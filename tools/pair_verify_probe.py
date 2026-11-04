"""Muse Spark picks which of two face strips is talking, in both orders (review/FACE_VERIFY_PROTOCOL.md, 2c)."""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from itertools import combinations, permutations
from pathlib import Path

from PIL import Image

from earshot.calls import BASE_URL, CallLog, api_key
from earshot.spark import SPARK_MODEL

from tools.face_verify_probe import face_clip, frame_strip
from tools.spark_verify_probe import build_cases, report

GAP = 24
SCHEMA = {
    "type": "object",
    "properties": {"talking": {"type": "string", "enum": ["left", "right", "unclear"]}},
    "required": ["talking"], "additionalProperties": False,
}
INSTRUCTIONS = (
    "The image has two panels separated by a white bar. Each panel shows 8 consecutive frames of one person's face, "
    "about 0.3 s apart, left to right then top to bottom. Exactly one of the two people may be talking. "
    "Compare how much the lips and jaw change across frames in each panel. "
    'Answer "left" or "right" for the person who is talking, or "unclear" if you cannot tell. Do not guess.'
)
USER = "Which person is talking, left or right?"


def pair_image(left: Path, right: Path, out: Path) -> Path:
    if out.exists():
        return out
    a, b = Image.open(left), Image.open(right)
    canvas = Image.new("RGB", (a.width + GAP + b.width, max(a.height, b.height)), "white")
    canvas.paste(a, (0, 0))
    canvas.paste(b, (a.width + GAP, 0))
    canvas.save(out, quality=90)
    return out


def ask_pair(calls: CallLog, image: Path) -> str:
    data = image.read_bytes()
    digest = hashlib.sha256(data).hexdigest()

    def call():
        from openai import OpenAI

        url = "data:image/jpeg;base64," + base64.b64encode(data).decode()
        with OpenAI(base_url=BASE_URL, api_key=api_key()) as api:
            resp = api.responses.create(
                model=SPARK_MODEL, instructions=INSTRUCTIONS,
                input=[{"type": "message", "role": "user", "content": [
                    {"type": "input_text", "text": USER}, {"type": "input_image", "image_url": url}]}],
                text={"format": {"type": "json_schema", "name": "pair_talking", "schema": SCHEMA, "strict": True}},
                reasoning={"effort": "low"}, max_output_tokens=4000,
            )
        if not resp.output_text:
            raise RuntimeError(f"Spark returned no JSON (status={getattr(resp, 'status', None)})")
        usage = getattr(resp, "usage", None)
        return json.loads(resp.output_text), {
            "request_id": resp.id, "usage": usage.model_dump() if hasattr(usage, "model_dump") else None}

    result = calls.cached(model=SPARK_MODEL, purpose="verify a flagged binding: which of two faces is talking",
                          where="hosted", key_parts=(digest, INSTRUCTIONS, USER, SCHEMA), fn=call)
    return result.get("talking", "unclear")


def clip_vote(people: int, answers: dict[tuple[int, int], str]) -> str:
    """A pair is decided only when both orders name the same face; a clip votes for a face that wins all its pairs."""
    wins = {p: 0 for p in range(people)}
    for i, j in combinations(range(people), 2):
        first = {"left": i, "right": j}.get(answers[(i, j)])
        second = {"left": j, "right": i}.get(answers[(j, i)])
        if first is not None and first == second:
            wins[first] += 1
    winners = [p for p, n in wins.items() if n == people - 1]
    return str(winners[0] + 1) if winners else "unclear"


def main() -> None:
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else ""
    suffix = "_" + only.split()[0].lower() if only else ""
    cases, jobs = build_cases("--live" in sys.argv, only)
    images = {}
    for case, label, calls, video, start, seconds, taps, size in jobs:
        folder = case["run"] / "calls" / "face_clips"
        strips = [frame_strip(face_clip(video, start, seconds, tap, size, folder / f"{start:.2f}_{seconds:.2f}_p{p}.mp4"))
                  for p, tap in enumerate(taps)]
        for i, j in permutations(range(len(taps)), 2):
            out = folder / f"{start:.2f}_{seconds:.2f}_pair{i}{j}.jpg"
            if out not in images:
                images[out] = (calls, pair_image(strips[i], strips[j], out))
    with ThreadPoolExecutor(max_workers=8) as pool:
        answers = dict(zip(images, pool.map(lambda item: ask_pair(*item), images.values())))
    log = []
    for case, label, calls, video, start, seconds, taps, size in jobs:
        folder = case["run"] / "calls" / "face_clips"
        pairs = {(i, j): answers[folder / f"{start:.2f}_{seconds:.2f}_pair{i}{j}.jpg"]
                 for i, j in permutations(range(len(taps)), 2)}
        case["answers"].setdefault(label, []).append(clip_vote(len(taps), pairs))
        log.append({"window": case["window"], "source": case["source"], "repeat": case["repeat"], "label": label,
                    "start": round(start, 2), "pairs": {f"{i}{j}": a for (i, j), a in pairs.items()}})
    report(cases, len(images), Path(f"review/pair_verify_probe{suffix}.json"))
    Path(f"review/pair_verify_answers{suffix}.json").write_text(json.dumps(log, indent=2) + "\n")


if __name__ == "__main__":
    main()
