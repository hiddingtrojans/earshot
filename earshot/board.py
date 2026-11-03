"""Evidence-checked questions and commitments; never dispatch actions automatically."""

from __future__ import annotations

import json
import re

from .calls import CallLog
from .spark import _caption_lines, _glimmer_respond, _respond
from .timeline import Caption

BOARD_SCHEMA = {
    "type": "object",
    "properties": {"items": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "kind": {"type": "string", "enum": ["question", "commitment"]},
            "text": {"type": "string"},
            "owner": {"type": ["string", "null"]},
            "action": {"type": ["string", "null"]},
            "due": {"type": ["string", "null"]},
            "cite": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        },
        "required": ["kind", "text", "owner", "action", "due", "cite"],
        "additionalProperties": False,
    }}},
    "required": ["items"], "additionalProperties": False,
}

VERDICTS_SCHEMA = {
    "type": "object",
    "properties": {"verdicts": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "index": {"type": "integer"},
            "status": {"type": "string", "enum": ["supported", "contradicted", "insufficient", "needs_human"]},
            "reason": {"type": "string"},
        },
        "required": ["index", "status", "reason"], "additionalProperties": False,
    }}},
    "required": ["verdicts"], "additionalProperties": False,
}

PROPOSE_INSTRUCTIONS = """You help a deaf or hard-of-hearing person follow a captioned meeting.
Extract at most eight genuinely unresolved questions and explicitly accepted commitments from the captions.
A question is not a commitment. A commitment needs an explicitly spoken acceptance by its owner; never turn
a request, suggestion, or possibility into an assigned task. Do not invent owners, actions, dates, numbers,
or decisions. Leave owner/action/due null when not stated. Use only exact caption IDs in cite. Keep text
short and plain. Return no item when the evidence is ambiguous; this is a review aid, not a task dispatcher."""

VERIFY_INSTRUCTIONS = """Check proposed meeting questions and commitments against only their cited captions.
For each candidate index, decide whether its specific claim is supported, contradicted, insufficient, or
needs_human. A commitment must have an explicit acceptance by the proposed owner; requests and unanswered
questions are not commitments. Open questions may be paraphrased but must remain unresolved in the evidence.
Do not use prior knowledge or fill in missing owners, actions, dates, or numbers. Return one verdict per index,
with a short concrete reason. You are reviewing evidence, not approving or performing an action."""


def _string(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _evidence_problems(item: dict, by_id: dict[str, Caption], names: list[str]) -> tuple[list[str], list[Caption]]:
    problems = []
    if item.get("kind") not in ("question", "commitment"):
        problems.append("unknown item kind")
    if not _string(item.get("text")):
        problems.append("empty text")
    raw_citations = item.get("cite")
    citations = raw_citations if isinstance(raw_citations, list) else []
    if not citations or any(not isinstance(citation, str) for citation in citations):
        problems.append("missing or invalid citation")
        return problems, []
    cited = [by_id[citation] for citation in citations if citation in by_id]
    if len(cited) != len(citations) or len(set(citations)) != len(citations):
        problems.append("citation is missing, duplicated, or outside this conversation")
    evidence = " ".join(caption.text for caption in cited).lower()
    speakers = {caption.name.lower() for caption in cited}
    owner = _string(item.get("owner"))
    if owner and owner.lower() not in speakers and owner.lower() not in evidence:
        problems.append(f"owner {owner!r} is not in the cited captions")
    if any(owner.lower() == name.lower() for name in names) and owner.lower() not in speakers \
            and owner.lower() not in evidence:
        problems.append("owner is not a speaker or person named in the evidence")
    action = _string(item.get("action"))
    due = _string(item.get("due"))
    if item.get("kind") == "commitment" and (not owner or not action):
        problems.append("a commitment needs an explicitly evidenced owner and action")
    if due and due.lower() not in evidence:
        problems.append("due date or time is not stated verbatim in the cited captions")
    details = " ".join((_string(item.get("text")), action, due))
    for number in re.findall(r"\d+(?:[.,:]\d+)?", re.sub(r"\bc\d+\b", "", details.lower())):
        if number not in evidence:
            problems.append(f"number {number} is not in the cited captions")
    return problems, cited


def _fallback(cited: list[Caption]) -> dict:
    return {"text": " / ".join(f"{caption.name}: “{caption.text}”" for caption in cited),
            "cite": [caption.id for caption in cited]}


def check_board_items(candidates: list[dict], captions: list[Caption], names: list[str],
                      verdicts: list[dict] | None = None) -> dict:
    """Apply deterministic gates first, then require an individual local verifier verdict."""
    by_id = {caption.id: caption for caption in captions}
    supplied = {v.get("index"): v for v in verdicts or [] if isinstance(v, dict) and isinstance(v.get("index"), int)}
    items, review = [], []
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            review.append({"kind": "question", "text": "Invalid model item", "status": "rejected",
                           "reason": "candidate is not an object", "cite": []})
            continue
        item = {key: candidate.get(key) for key in ("kind", "text", "owner", "action", "due", "cite")}
        problems, cited = _evidence_problems(item, by_id, names)
        verdict = supplied.get(index, {})
        verdict_status = verdict.get("status")
        if problems:
            status, reason = "rejected", "; ".join(problems)
        elif verdict_status != "supported":
            status = verdict_status if verdict_status in ("contradicted", "insufficient", "needs_human") else "needs_human"
            reason = _string(verdict.get("reason")) or "the independent verifier did not support this item"
        else:
            status, reason = "supported", _string(verdict.get("reason")) or "claim and citations checked"
        item.update({"id": f"board-{index + 1:02d}", "status": status, "evidence_check": reason,
                     "verifier": "muse-glimmer (local)" if not problems else "deterministic evidence rules"})
        if status == "supported":
            items.append(item)
        else:
            item["fallback"] = _fallback(cited)
            review.append(item)
    return {"items": items, "review": review, "verification_model": "muse-glimmer", "where": "local",
            "actions": "Review only: no messages, tasks, or calendar events are created automatically.",
            "counts": {"supported": len(items), "not_accepted": len(review)}}


def build_board(captions: list[Caption], names: list[str], calls: CallLog, model: str = "glimmer") -> dict:
    if not captions:
        return check_board_items([], [], names)
    respond = _glimmer_respond if model == "glimmer" else _respond if model == "spark" else None
    if respond is None:
        raise ValueError(f"unknown board model {model!r}")
    proposed = respond(calls, "extract evidence-linked questions and commitments", PROPOSE_INSTRUCTIONS,
                       _caption_lines(captions), BOARD_SCHEMA, "meeting_board")
    candidates = proposed.get("items", [])
    if not isinstance(candidates, list) or len(candidates) > 8:
        raise ValueError("board proposals must be a list of at most eight items")
    if not candidates:
        return check_board_items([], captions, names)
    cited_ids = {citation for item in candidates if isinstance(item, dict)
                 for citation in item.get("cite", []) if isinstance(citation, str)}
    evidence = [caption for caption in captions if caption.id in cited_ids]
    review_input = "Cited captions (the only evidence):\n" + _caption_lines(evidence) + \
        "\n\nCandidates, indexed from zero:\n" + json.dumps(candidates, ensure_ascii=False)
    checked = _glimmer_respond(calls, "verify evidence for questions and commitments", VERIFY_INSTRUCTIONS,
                               review_input, VERDICTS_SCHEMA, "meeting_board_verdicts")
    verdicts = checked.get("verdicts", [])
    if not isinstance(verdicts, list):
        verdicts = []
    return check_board_items(candidates, captions, names, verdicts)
