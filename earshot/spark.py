"""Muse Spark (hosted): conversation threads and verified "What did I miss?".

Spark proposes; deterministic code checks. A catch-up sentence is shown only if
every caption it cites exists in the window, every person it names is among the
speakers of those captions (or named in them), and every number it contains
appears in the cited captions. Anything else is replaced by the cited captions,
verbatim. That follows the Agents 102 pattern: checks outside the model.
"""

from __future__ import annotations

import json
import re

from .calls import BASE_URL, CallLog, api_key
from .timeline import Caption, captions_in_window

SPARK_MODEL = "muse-spark-1.3"
MAX_SENTENCE_WORDS = 40

THREADS_SCHEMA = {
    "type": "object",
    "properties": {
        "threads": {"type": "array", "items": {
            "type": "object",
            "properties": {"thread": {"type": "integer"}, "topic": {"type": "string"}},
            "required": ["thread", "topic"], "additionalProperties": False}},
        "assignments": {"type": "array", "items": {
            "type": "object",
            "properties": {"id": {"type": "string"}, "thread": {"type": "integer"}},
            "required": ["id", "thread"], "additionalProperties": False}},
    },
    "required": ["threads", "assignments"], "additionalProperties": False,
}

CATCHUP_SCHEMA = {
    "type": "object",
    "properties": {"sentences": {"type": "array", "items": {
        "type": "object",
        "properties": {"text": {"type": "string"}, "cite": {"type": "array", "items": {"type": "string"}}},
        "required": ["text", "cite"], "additionalProperties": False}}},
    "required": ["sentences"], "additionalProperties": False,
}


def _respond(calls: CallLog, purpose: str, instructions: str, user: str, schema: dict, name: str,
             effort: str = "low", max_output_tokens: int = 6000) -> dict:
    def call():
        from openai import OpenAI

        with OpenAI(base_url=BASE_URL, api_key=api_key()) as api:
            resp = api.responses.create(
                model=SPARK_MODEL, instructions=instructions, input=user,
                text={"format": {"type": "json_schema", "name": name, "schema": schema, "strict": True}},
                reasoning={"effort": effort}, max_output_tokens=max_output_tokens,
            )
        if getattr(resp, "status", "completed") != "completed" or not resp.output_text:
            raise RuntimeError(f"Spark returned no final text (status={getattr(resp, 'status', None)}); "
                               "raise max_output_tokens: reasoning tokens count against it")
        usage = getattr(resp, "usage", None)
        return json.loads(resp.output_text), {
            "request_id": resp.id,
            "usage": usage.model_dump() if hasattr(usage, "model_dump") else None,
        }

    return calls.cached(model=SPARK_MODEL, purpose=purpose, where="hosted",
                        key_parts=(instructions, user, schema), fn=call)


def _glimmer_respond(calls: CallLog, purpose: str, instructions: str, user: str, schema: dict, name: str) -> dict:
    def call():
        import os

        from openai import OpenAI

        base_url = os.environ.get("EARSHOT_LOCAL_BASE_URL", "http://localhost:11434/v1")
        request = {
            "model": "muse-glimmer",
            "messages": [{"role": "system", "content": instructions}, {"role": "user", "content": user}],
            "max_tokens": 8000,
        }
        with OpenAI(base_url=base_url, api_key=os.environ.get("EARSHOT_LOCAL_API_KEY", "ollama")) as api:
            try:
                resp = api.chat.completions.create(**request, response_format={
                    "type": "json_schema", "json_schema": {"name": name, "schema": schema, "strict": True},
                })
            except Exception as error:
                if getattr(error, "status_code", None) not in (400, 422):
                    raise
                resp = api.chat.completions.create(**request, response_format={"type": "json_object"})
        content = resp.choices[0].message.content
        if not content:
            raise RuntimeError("Muse Glimmer returned no final JSON text")
        usage = getattr(resp, "usage", None)
        return json.loads(content), {
            "request_id": resp.id,
            "usage": usage.model_dump() if hasattr(usage, "model_dump") else None,
        }

    return calls.cached(model="muse-glimmer", purpose=purpose, where="local",
                        key_parts=(instructions, user, schema), fn=call)


def _caption_lines(captions: list[Caption]) -> str:
    return "\n".join(f"[{c.id}] {c.start:6.1f}s {c.name}: {c.text}" for c in captions)


# --------------------------------------------------------------------------- #
# Threads
# --------------------------------------------------------------------------- #
def assign_threads(captions: list[Caption], calls: CallLog) -> list[dict]:
    if not captions:
        return []
    instructions = (
        "You group a captioned group conversation into threads. People at a table often hold two "
        "conversations at once. Give each caption ID exactly one thread number (start at 1). Only start "
        "a new thread when people are clearly talking about something else at the same time or the topic "
        "changes. Topics are 2-5 plain words. Return every caption ID."
    )
    out = _respond(calls, "split conversation into threads", instructions, _caption_lines(captions),
                   THREADS_SCHEMA, "threads")
    return apply_threads(captions, out)


def apply_threads(captions: list[Caption], out: dict) -> list[dict]:
    """Validate Spark's thread assignment; repair gaps deterministically."""
    threads = {t["thread"]: t["topic"].strip() or f"Thread {t['thread']}" for t in out.get("threads", [])}
    given = {a["id"]: a["thread"] for a in out.get("assignments", []) if a.get("thread") in threads}
    if not threads or not given:
        threads, given = {1: "Conversation"}, {}
    previous = min(threads)
    for c in captions:  # unassigned or unknown -> same thread as the caption before it
        c.thread = given.get(c.id, previous)
        previous = c.thread
    used = sorted({c.thread for c in captions})
    return [{"thread": t, "topic": threads.get(t, f"Thread {t}")} for t in used]


# --------------------------------------------------------------------------- #
# What did I miss?
# --------------------------------------------------------------------------- #
def catch_up(captions: list[Caption], names: list[str], t_now: float, seconds: float,
             calls: CallLog, person: int | None = None, model: str = "spark") -> dict:
    t0 = max(0.0, t_now - seconds)
    window = [c for c in captions_in_window(captions, t0, t_now) if person is None or c.person == person]
    who = "the table" if person is None else names[person]
    if not window:
        return {"window": [t0, t_now], "who": who, "sentences": [], "note": "Nothing was said."}
    instructions = (
        "A deaf or hard-of-hearing person missed part of a group conversation. Write 1-3 short, plain "
        f"sentences catching them up on what {who} said. Use only the captions given. Name people as in "
        "the captions. Every sentence must cite the caption IDs it is based on, like c004."
    )
    if model == "glimmer":
        out = _glimmer_respond(calls, f"what did I miss: {who}", instructions, _caption_lines(window),
                               CATCHUP_SCHEMA, "catchup")
    elif model == "spark":
        out = _respond(calls, f"what did I miss: {who}", instructions, _caption_lines(window),
                       CATCHUP_SCHEMA, "catchup")
    else:
        raise ValueError(f"unknown catch-up model {model!r}")
    return {"window": [round(t0, 2), round(t_now, 2)], "who": who,
            "sentences": verify_catchup(out.get("sentences", []), window, names)}


def verify_catchup(sentences: list[dict], window: list[Caption], names: list[str]) -> list[dict]:
    by_id = {c.id: c for c in window}
    checked = []
    for s in sentences:
        text, cite = s.get("text", "").strip(), [c for c in s.get("cite", []) if isinstance(c, str)]
        problems = []
        cited = [by_id[c] for c in cite if c in by_id]
        if not cite or len(cited) != len(cite):
            problems.append("cites captions outside the window" if cite else "no citation")
        cited_text = " ".join(c.text for c in cited).lower()
        speakers = {c.name.lower() for c in cited}
        for n in names:
            if re.search(rf"\b{re.escape(n.lower())}\b", text.lower()) and n.lower() not in speakers \
                    and n.lower() not in cited_text:
                problems.append(f"names {n}, who isn't in the cited captions")
        number_text = re.sub(r"\bc\d+\b", "", text)
        for num in re.findall(r"\d+(?:[.,:]\d+)?", number_text):
            if num not in cited_text:
                problems.append(f"number {num} not in the cited captions")
        if len(text.split()) > MAX_SENTENCE_WORDS:
            problems.append("too long")
        if problems:
            if cited:
                checked.append({"text": " / ".join(f"{c.name}: “{c.text}”" for c in cited),
                                "cite": [c.id for c in cited], "status": "replaced", "problems": problems})
            continue
        checked.append({"text": text, "cite": cite, "status": "verified"})
    if not checked:  # nothing usable: show the last captions verbatim
        checked = [{"text": f"{c.name}: “{c.text}”", "cite": [c.id], "status": "verbatim"} for c in window[-3:]]
    return checked


def translate_captions(captions: list[Caption], target_lang: str, calls: CallLog) -> tuple[dict[str, str], str]:
    original = {caption.id: caption.text for caption in captions}
    if not original:
        return {}, "translated"
    schema = {
        "type": "object",
        "properties": {"items": {"type": "array", "items": {
            "type": "object",
            "properties": {"id": {"type": "string"}, "text": {"type": "string"}},
            "required": ["id", "text"], "additionalProperties": False}}},
        "required": ["items"], "additionalProperties": False,
    }
    instructions = (
        f"Translate every caption's spoken text into {target_lang}. Return every caption ID exactly once and no other IDs. "
        "Preserve meaning, names, numbers, and caption IDs. Do not include speaker labels or timestamps in the "
        "translated text; the viewer already shows them. Return only the translation items."
    )
    try:
        out = _respond(calls, f"translate captions to {target_lang}", instructions,
                       _caption_lines(captions), schema, "translation")
        items = out["items"]
        ids = [item["id"] for item in items]
        if len(ids) != len(original) or set(ids) != set(original) or len(set(ids)) != len(ids):
            raise ValueError("translation caption IDs do not match the originals")
        if any(not isinstance(item["text"], str) or not item["text"].strip() for item in items):
            raise ValueError("translation contains empty text")
        by_id = {caption.id: caption for caption in captions}
        if any(item["text"].lstrip().lower().startswith(f"{by_id[item['id']].name.lower()}:") for item in items):
            raise ValueError("translation repeats the viewer's speaker label")
        return {item["id"]: item["text"].strip() for item in items}, "translated"
    except (RuntimeError, ValueError, TypeError, KeyError):
        return original, "untranslated"
