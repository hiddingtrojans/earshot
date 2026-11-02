"""Earshot-Lite: attribute diarized turns to faces by mouth movement. No models.

Muse Voice Transcribe diarizes the mixture into anonymous speakers. For each
label, an activity signal is correlated with mouth-band motion over the clip.
One-to-one assignment maximizes total correlation; it does not reward people for
moving more overall. This binds voices to faces without manual matching, but it
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


def head_motion(frames: np.ndarray, tracks: Tracks, person: int,
                mouth_band: tuple[float, float] = (0.30, 0.60), center_frac: float = 0.60) -> np.ndarray:
    """Mean absolute frame difference in a central mouth band, per frame."""
    n, h, w = frames.shape
    sx, sy = w / tracks.width, h / tracks.height
    motion = np.full(n, np.nan)
    for f in range(1, min(n, tracks.frames or n)):
        box = tracks.bbox(person, f)
        if box is None:
            continue
        x0, y0, x1, y1 = box
        height, width = y1 - y0, x1 - x0
        ya = int((y0 + height * mouth_band[0]) * sy)
        yb = max(ya + 1, int((y0 + height * mouth_band[1]) * sy))
        centre = (x0 + width / 2) * sx
        half = width * center_frac * sx / 2
        xa, xb = max(0, int(centre - half)), min(w, max(int(centre - half) + 1, int(centre + half)))
        a = frames[f, ya:yb, xa:xb].astype(np.int16)
        b = frames[f - 1, ya:yb, xa:xb].astype(np.int16)
        if a.size:
            motion[f] = float(np.mean(np.abs(a - b)))
    return motion


def _smooth(values: np.ndarray, frames: int) -> np.ndarray:
    from scipy.ndimage import uniform_filter1d

    values = np.nan_to_num(np.asarray(values, dtype=float), nan=0.0)
    return uniform_filter1d(values, size=frames, mode="nearest")


def _zscore(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    deviation = float(values.std())
    return (values - values.mean()) / deviation if deviation > 1e-12 else np.zeros_like(values)


def _activity(turns: list[Turn], speaker: str, frames: int, fps: float) -> np.ndarray:
    out = np.zeros(frames)
    for turn in turns:
        if turn.speaker != speaker:
            continue
        start = max(0, int(round(turn.start * fps)))
        end = min(frames, max(start + 1, int(round(turn.end * fps))))
        out[start:end] = 1.0
    return out


def _correlation(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    return float(np.dot(left, right) / denominator) if denominator else 0.0


def attribute_turns(turns: list[Turn], motion: list[np.ndarray], fps: float,
                    smooth_seconds: float = 0.5) -> dict[str, int]:
    """Map diarized labels to people by smoothed activity/mouth-motion correlation."""
    from scipy.optimize import linear_sum_assignment

    people = len(motion)
    window = max(1, int(round(fps * smooth_seconds)))
    smoothed = []
    for values in motion:
        if not np.isfinite(values).any() or float(np.nanmedian(np.abs(values))) < 0.1:
            smoothed.append(np.zeros_like(values, dtype=float))
        else:
            smoothed.append(_zscore(_smooth(values, window)))
    speakers = sorted({turn.speaker for turn in turns})
    candidates = []
    for speaker in speakers:
        raw_activity = _activity(turns, speaker, len(motion[0]), fps)
        activity = _smooth(raw_activity, window)
        if activity.std() <= 1e-12:
            score = np.array([float(values.std()) for values in smoothed])
        else:
            activity = _zscore(activity)
            score = np.array([_correlation(activity, values) for values in smoothed])
        if score.size and float(score.max()) != 0:
            candidates.append((speaker, score))
    mapping: dict[str, int] = {}
    if not candidates:
        return {speaker: index % people for index, speaker in enumerate(speakers)} if people else mapping
    labels = [speaker for speaker, _ in candidates]
    matrix = np.stack([score for _, score in candidates])
    rows, columns = linear_sum_assignment(-matrix)
    for row, column in zip(rows, columns):
        mapping[labels[row]] = int(column)
    for row, label in enumerate(labels):
        if label not in mapping:
            mapping[label] = int(np.argmax(matrix[row]))
    return mapping
