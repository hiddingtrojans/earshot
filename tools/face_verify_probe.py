"""Muse Spark judges one face at a time whether that person is talking (review/FACE_VERIFY_PROTOCOL.md)."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from earshot.calls import BASE_URL, CallLog, api_key
from earshot.spark import SPARK_MODEL
from earshot.tracking import _upload

from tools.spark_verify_probe import build_cases, report

CROP_WIDTH, CROP_HEIGHT = 0.35, 0.45
SCHEMA = {
    "type": "object",
    "properties": {"talking": {"type": "string", "enum": ["yes", "no", "unclear"]}},
    "required": ["talking"], "additionalProperties": False,
}
INSTRUCTIONS = (
    "This muted video clip shows one person's face. Watch their lips and jaw. "
    'Answer "yes" if this person is talking for most of the clip, "no" if they are not talking, '
    'or "unclear" if you cannot tell. Do not guess.'
)
USER = "Is this person talking in this muted clip?"


def face_clip(video: Path, start: float, seconds: float, tap: tuple[float, float],
              size: tuple[int, int], out: Path) -> Path:
    if out.exists():
        return out
    width, height = size
    crop_w, crop_h = int(width * CROP_WIDTH) // 2 * 2, int(height * CROP_HEIGHT) // 2 * 2
    x = int(min(max(tap[0] * width - crop_w / 2, 0), width - crop_w))
    y = int(min(max(tap[1] * height - crop_h / 2, 0), height - crop_h))
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{start:.3f}", "-i", str(video),
         "-t", f"{seconds:.3f}", "-an", "-vf", f"fps=25,crop={crop_w}:{crop_h}:{x}:{y},scale=iw*2:ih*2",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", str(out)],
        check=True)
    return out


def ask_face(calls: CallLog, clip: Path) -> str:
    digest = hashlib.sha256(clip.read_bytes()).hexdigest()

    def call():
        from openai import OpenAI

        file_id = _upload(clip)
        with OpenAI(base_url=BASE_URL, api_key=api_key()) as api:
            resp = api.responses.create(
                model=SPARK_MODEL, instructions=INSTRUCTIONS,
                input=[{"type": "message", "role": "user", "content": [
                    {"type": "input_text", "text": USER}, {"type": "input_video", "file_id": file_id}]}],
                text={"format": {"type": "json_schema", "name": "face_talking", "schema": SCHEMA, "strict": True}},
                reasoning={"effort": "low"}, max_output_tokens=4000,
            )
        if not resp.output_text:
            raise RuntimeError(f"Spark returned no JSON (status={getattr(resp, 'status', None)})")
        usage = getattr(resp, "usage", None)
        return json.loads(resp.output_text), {
            "request_id": resp.id, "usage": usage.model_dump() if hasattr(usage, "model_dump") else None}

    result = calls.cached(model=SPARK_MODEL, purpose="verify a flagged binding: is this one face talking",
                          where="hosted", key_parts=(digest, INSTRUCTIONS, USER, SCHEMA), fn=call)
    return result.get("talking", "unclear")


def clip_vote(face_answers: list[str]) -> str:
    """A clip votes for a person only when exactly one face is talking."""
    talking = [index for index, answer in enumerate(face_answers) if answer == "yes"]
    return str(talking[0] + 1) if len(talking) == 1 else "unclear"


def main() -> None:
    cases, jobs = build_cases("--live" in sys.argv)
    crops = {}
    for case, label, calls, video, start, seconds, taps, size in jobs:
        for person, tap in enumerate(taps):
            clip = case["run"] / "calls" / "face_clips" / f"{start:.2f}_{seconds:.2f}_p{person}.mp4"
            if clip not in crops:
                crops[clip] = (calls, face_clip(video, start, seconds, tap, size, clip))
    with ThreadPoolExecutor(max_workers=8) as pool:
        answers = dict(zip(crops, pool.map(lambda item: ask_face(*item), crops.values())))
    face_log = []
    for case, label, calls, video, start, seconds, taps, size in jobs:
        per_face = [answers[case["run"] / "calls" / "face_clips" / f"{start:.2f}_{seconds:.2f}_p{person}.mp4"]
                    for person in range(len(taps))]
        case["answers"].setdefault(label, []).append(clip_vote(per_face))
        face_log.append({"window": case["window"], "source": case["source"], "repeat": case["repeat"],
                         "label": label, "start": round(start, 2), "faces": per_face})
    report(cases, len(crops), Path("review/face_verify_probe.json"))
    Path("review/face_verify_answers.json").write_text(json.dumps(face_log, indent=2) + "\n")


if __name__ == "__main__":
    main()
