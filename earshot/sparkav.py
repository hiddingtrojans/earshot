"""Unverified Muse Spark audiovisual overlap transcription experiment."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .calls import CallLog, api_key, content_key
from .media import ffmpeg
from .spark import SPARK_MODEL
from .tracking import Tap, _upload
from .transcribe import Turn

SEGMENTS_SCHEMA = {
    "type": "object",
    "properties": {"segments": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "person": {"type": "integer"},
            "start": {"type": "number"},
            "end": {"type": "number"},
            "text": {"type": "string"},
        },
        "required": ["person", "start", "end", "text"],
        "additionalProperties": False,
    }}},
    "required": ["segments"], "additionalProperties": False,
}


def transcribe_window(video: Path, taps: list[Tap], baseline: list[Turn], start: float, seconds: float,
                      calls: CallLog, repeat: int | None = None) -> list[list[Turn]]:
    names = [tap.name for tap in taps]
    clip = calls.calls_dir / f"av_{start:.1f}_{seconds:.1f}.mp4"
    if not clip.exists():
        ffmpeg("-ss", f"{start}", "-i", str(video), "-t", f"{seconds}", "-vf", "fps=25,setsar=1",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "96k", "-ac", "1", "-ar", "48000", str(clip))
    digest = hashlib.sha256(clip.read_bytes()).hexdigest()
    positions = [{"person": index, "name": tap.name, "tap": [tap.x, tap.y, tap.frame]}
                 for index, tap in enumerate(taps)]
    turns = [{"speaker": turn.speaker, "start": turn.start, "end": turn.end, "text": turn.text}
             for turn in baseline if turn.start < start + seconds and turn.end > start]
    instructions = (
        "Watch the video and LISTEN to its audio. Transcribe every spoken word in this 10-second window, "
        "especially simultaneous speech. The supplied diarization is a noisy hint, not an answer to copy. "
        "Bind voices only to the named people and normalized grid positions supplied; do not infer identity "
        "or anyone outside them. Return strict JSON segments with zero-based person index, rough start/end "
        "seconds relative to the full clip, and the exact words you hear. Do not invent confidence or verification."
    )
    user = json.dumps({"window": [start, start + seconds], "people": positions, "diarized_turns": turns})
    key_parts = (digest, instructions, user, SEGMENTS_SCHEMA)
    if repeat is not None:
        key_parts += (repeat,)

    def call():
        from openai import OpenAI

        from .calls import BASE_URL

        file_id = _upload(clip)
        with OpenAI(base_url=BASE_URL, api_key=api_key()) as api:
            resp = api.responses.create(
                model=SPARK_MODEL,
                instructions=instructions,
                input=[{"type": "message", "role": "user", "content": [
                    {"type": "input_text", "text": user}, {"type": "input_video", "file_id": file_id},
                ]}],
                text={"format": {"type": "json_schema", "name": "av_segments",
                                 "schema": SEGMENTS_SCHEMA, "strict": True}},
                reasoning={"effort": "low"}, max_output_tokens=6000,
            )
        if not resp.output_text:
            raise RuntimeError(f"Spark AV returned no JSON (status={getattr(resp, 'status', None)})")
        usage = getattr(resp, "usage", None)
        return json.loads(resp.output_text), {
            "request_id": resp.id, "usage": usage.model_dump() if hasattr(usage, "model_dump") else None,
        }

    result = calls.cached(model=SPARK_MODEL, purpose=f"unverified AV overlap transcription {start:.1f}",
                          where="hosted", key_parts=key_parts, fn=call)
    output = [[] for _ in names]
    for segment in result.get("segments", []):
        person, text = segment.get("person"), (segment.get("text") or "").strip()
        if not isinstance(person, int) or not 0 <= person < len(names) or not text:
            continue
        start_s = max(start, min(start + seconds, float(segment["start"])))
        end_s = max(start_s + 0.01, min(start + seconds, float(segment["end"])))
        output[person].append(Turn(str(person), start_s, end_s, text))
    return output


def transcribe_windows(video: Path, taps: list[Tap], baseline: list[Turn], duration: float,
                       calls: CallLog, repeat: int | None = None) -> tuple[list[list[Turn]], list[list[tuple[float, float]]]]:
    turns = [[] for _ in taps]
    for start in range(0, int(duration + 0.999), 10):
        window = transcribe_window(video, taps, baseline, float(start), min(10.0, duration - start), calls, repeat)
        for person, segments in enumerate(window):
            turns[person].extend(segments)
    for person in range(len(turns)):
        turns[person].sort(key=lambda turn: turn.start)
    activity = [[(turn.start, turn.end) for turn in person_turns] for person_turns in turns]
    return turns, activity
