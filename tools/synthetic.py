"""SYNTHETIC test fixture — not real model output.

Builds a 20-second video with two stand-in "people" (coloured shapes) and two
tone "voices" that overlap, plus fake model clients. Used by the integration
test and by `make_synthetic_run.py` to develop the viewer without API keys.
Never present this run as a demo of the models.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

SR = 48_000
DUR = 20.0
W, H, FPS = 960, 540, 25

# (person, start, end, text) — two conversations, with overlaps
SCRIPT = [
    (0, 0.5, 3.0, "Did anyone book a table for Friday"),
    (1, 2.4, 5.2, "I booked Casa Lola for eight"),
    (0, 5.6, 8.0, "Great, is Marta coming too"),
    (1, 7.4, 10.5, "The dog ate my shoe again this morning"),
    (0, 9.8, 12.8, "Wait, which shoe, the new ones"),
    (1, 12.2, 15.5, "Yes the blue ones from Saturday"),
    (0, 16.0, 19.0, "Okay so Friday at eight then"),
]
NAMES = ["Ana", "Raúl"]
FREQS = [220.0, 330.0]
CENTERS = [(0.30, 0.55), (0.70, 0.55)]


def sources() -> list[np.ndarray]:
    t = np.arange(int(DUR * SR)) / SR
    out = []
    for p in range(2):
        x = np.zeros_like(t)
        for q, a, b, _ in SCRIPT:
            if q == p:
                m = (t >= a) & (t < b)
                x[m] = 0.25 * np.sin(2 * np.pi * FREQS[p] * t[m]) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t[m]))
        out.append(x.astype(np.float32))
    return out


def make_video(path: Path) -> None:
    mix = sum(sources())
    raw = path.with_suffix(".f32")
    raw.write_bytes(mix.astype(np.float32).tobytes())
    boxes = []
    for (cx, cy), color in zip(CENTERS, ["0xE4572E", "0x2E86AB"]):
        x, y = int(cx * W - 90), int(cy * H - 60)
        boxes.append(f"drawbox=x={x}:y={y}:w=180:h=260:color={color}@1:t=fill")
        boxes.append(f"drawbox=x={x + 50}:y={y - 90}:w=80:h=80:color={color}@1:t=fill")
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", f"color=c=0x3A4A5A:s={W}x{H}:r={FPS}:d={DUR}",
        "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(raw),
        "-vf", ",".join(boxes), "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest", str(path),
    ], check=True)
    raw.unlink()


def fake_tracks(names, info):
    from earshot.tracking import Tracks

    regions = []
    for cx, cy in CENTERS[: len(names)]:
        x0, y0 = int(cx * info.width - 90), int(cy * info.height - 150)
        w, h = 180, 350
        packed = np.packbits(np.ones(w * h, dtype=np.uint8)).tobytes()
        regions.append({f: (x0, y0, w, h, packed) for f in range(info.frames)})
    return Tracks(list(names), info.width, info.height, info.fps, info.frames, regions)


class FakeSeparator:
    name = "SYNTHETIC fake separator"

    def __init__(self, **kw):
        self._src = sources()

    def separate(self, video, mixture, tracks, person, calls):
        s = self._src[person]
        return np.pad(s, (0, max(0, mixture.size - s.size)))[: mixture.size]


def fake_transcribe(audio, calls, purpose, mode="DIARIZATION"):
    from earshot.transcribe import Turn

    if purpose.startswith("diarize"):
        # A single stream: overlapping lines get merged and attributed to one speaker.
        turns, cur = [], None
        for p, a, b, text in SCRIPT:
            if cur and a < cur[2]:
                cur = (cur[0], cur[1], max(cur[2], b), cur[3] + " " + " ".join(text.split()[:2]) + "…")
            else:
                if cur:
                    turns.append(cur)
                cur = (str(p), a, b, text)
        turns.append(cur)
        return [Turn(s, a, b, t) for s, a, b, t in turns]
    person = next(i for i, n in enumerate(NAMES) if n in purpose)
    return [Turn("0", a, b, t) for p, a, b, t in SCRIPT if p == person]


def fake_respond(calls, purpose, instructions, user, schema, name, **kw):
    ids = [line.split("]")[0].strip("[") for line in user.splitlines() if line.startswith("[")]
    if name == "threads":
        def thread(line):
            return 2 if any(w in line for w in ("dog", "shoe", "blue")) else 1
        lines = user.splitlines()
        return {"threads": [{"thread": 1, "topic": "Friday dinner"}, {"thread": 2, "topic": "The dog and the shoe"}],
                "assignments": [{"id": i, "thread": thread(lines[k])} for k, i in enumerate(ids)]}
    last = user.splitlines()[-1]
    who = last.split("s ", 1)[1].split(":", 1)[0].strip()
    text = last.split(":", 1)[1].strip()
    return {"sentences": [{"text": f"{who} said: {text}.", "cite": [ids[-1]]}]}


def write_fake_calls(run: Path) -> None:
    rows = [
        {"model": "sam-3.1", "purpose": "track tapped people", "where": "hosted", "latency_ms": 0},
        {"model": "muse-voice-transcribe-1.0", "purpose": "diarize the raw mix (today's captions)", "where": "hosted", "latency_ms": 0},
        {"model": "facebook/sam-audio-small-tv", "purpose": "isolate Ana's voice", "where": "local", "latency_ms": 0},
        {"model": "facebook/sam-audio-small-tv", "purpose": "isolate Raúl's voice", "where": "local", "latency_ms": 0},
        {"model": "muse-voice-transcribe-1.0", "purpose": "transcribe Ana's isolated voice", "where": "hosted", "latency_ms": 0},
        {"model": "muse-spark-1.3", "purpose": "split conversation into threads", "where": "hosted", "latency_ms": 0},
    ]
    (run / "calls.jsonl").write_text("".join(json.dumps({**r, "synthetic": True}) + "\n" for r in rows))
