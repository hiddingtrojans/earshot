"""Earshot-Lite: attribute diarized turns to faces by mouth movement. No models.

Fallback when voice separation isn't available. Muse Voice Transcribe diarizes
the mixture into anonymous speakers; for each turn we measure motion in the top
part of each person's SAM 3.1 mask (their head) and give each anonymous speaker
to the person whose head moves most while that speaker talks. This keeps the
face-anchored captions without the manual voice-to-person matching step, but it
cannot recover words lost to overlapping speech.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

from .media import probe
from .tracking import Tracks
from .transcribe import Turn

GRAY_WIDTH = 320


def gray_frames(video: Path, width: int = GRAY_WIDTH) -> np.ndarray:
    info = probe(video)
    h = int(round(info.height * width / info.width / 2) * 2)
    raw = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(video),
         "-vf", f"scale={width}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, h, width)


def head_motion(frames: np.ndarray, tracks: Tracks, person: int, head_frac: float = 0.35) -> np.ndarray:
    """Mean absolute frame difference inside the person's head box, per frame."""
    n, h, w = frames.shape
    sx, sy = w / tracks.width, h / tracks.height
    motion = np.full(n, np.nan)
    for f in range(1, min(n, tracks.frames or n)):
        box = tracks.bbox(person, f)
        if box is None:
            continue
        x0, y0, x1, y1 = box
        y1 = y0 + max(1, int((y1 - y0) * head_frac))
        xa, xb = int(x0 * sx), max(int(x0 * sx) + 1, int(x1 * sx))
        ya, yb = int(y0 * sy), max(int(y0 * sy) + 1, int(y1 * sy))
        a = frames[f, ya:yb, xa:xb].astype(np.int16)
        b = frames[f - 1, ya:yb, xa:xb].astype(np.int16)
        if a.size:
            motion[f] = float(np.mean(np.abs(a - b)))
    return motion


def attribute_turns(turns: list[Turn], motion: list[np.ndarray], fps: float) -> dict[str, int]:
    """Map each anonymous speaker label to a person index."""
    people = len(motion)
    norm = []
    for m in motion:
        base = np.nanmedian(m) if np.isfinite(m).any() else 1.0
        norm.append(m / (base + 1e-6))
    score: dict[str, np.ndarray] = {}
    for t in turns:
        f0, f1 = int(t.start * fps), max(int(t.start * fps) + 1, int(t.end * fps))
        per_person = np.array([np.nanmean(n[f0:f1]) if np.isfinite(n[f0:f1]).any() else 0.0 for n in norm])
        score.setdefault(t.speaker, np.zeros(people))
        score[t.speaker] += np.nan_to_num(per_person) * (t.end - t.start)
    if not score:
        return {}
    speakers = sorted(score)
    if len(speakers) <= people and len(speakers) <= 8:
        from itertools import permutations

        best = max(permutations(range(people), len(speakers)),
                   key=lambda assignment: sum(score[speaker][person]
                                              for speaker, person in zip(speakers, assignment)))
        return dict(zip(speakers, best))
    mapping: dict[str, int] = {}
    pairs = sorted(((s[p], spk, p) for spk, s in score.items() for p in range(people)), reverse=True)
    used_people: set[int] = set()
    for _, spk, p in pairs:
        if spk in mapping or (p in used_people and len(used_people) < people):
            continue
        mapping[spk] = p
        used_people.add(p)
    return mapping
