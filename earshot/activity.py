"""Deterministic voice activity: frame energy with hysteresis. No models.

Used on each isolated voice track to decide when that person is speaking, which
drives the overlap flags and the bleed filter in `timeline.py`.
"""

from __future__ import annotations

import numpy as np

Segment = tuple[float, float]


def frame_energy_db(x: np.ndarray, sr: int, win: float = 0.025, hop: float = 0.010) -> tuple[np.ndarray, np.ndarray]:
    n_win, n_hop = int(win * sr), int(hop * sr)
    if x.size < n_win:
        return np.zeros(0), np.zeros(0)
    n = 1 + (x.size - n_win) // n_hop
    idx = np.arange(n_win)[None, :] + n_hop * np.arange(n)[:, None]
    frames = x[idx]
    rms = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1))
    times = (np.arange(n) * n_hop + n_win / 2) / sr
    return times, 20 * np.log10(rms + 1e-9)


def speech_segments(x: np.ndarray, sr: int, *, margin_db: float = 9.0, rel_db: float = -30.0,
                    abs_floor_db: float = -55.0, min_speech: float = 0.20, min_gap: float = 0.30,
                    hangover: float = 0.15) -> list[Segment]:
    times, db = frame_energy_db(x, sr)
    if db.size == 0:
        return []
    floor = float(np.percentile(db, 10))
    peak = float(np.percentile(db, 98))
    if peak < abs_floor_db or peak - floor < margin_db:
        return []  # nothing clearly above the noise floor: no speech
    on = max(floor + margin_db, peak + rel_db)
    off = on - 3.0
    hop = times[1] - times[0] if times.size > 1 else 0.01
    segs: list[list[float]] = []
    active, start = False, 0.0
    for t, v in zip(times, db):
        if not active and v >= on:
            active, start = True, t - hop / 2
        elif active and v < off:
            active = False
            segs.append([start, t + hangover])
    if active:
        segs.append([start, times[-1] + hop / 2])
    merged: list[list[float]] = []
    for s in segs:
        if merged and s[0] - merged[-1][1] < min_gap:
            merged[-1][1] = max(merged[-1][1], s[1])
        else:
            merged.append(s)
    return [(round(a, 3), round(b, 3)) for a, b in merged if b - a >= min_speech]


def active_fraction(segments: list[Segment], t0: float, t1: float) -> float:
    """Fraction of [t0, t1] covered by `segments`."""
    if t1 <= t0:
        return 0.0
    covered = sum(max(0.0, min(b, t1) - max(a, t0)) for a, b in segments)
    return min(1.0, covered / (t1 - t0))


def overlap_windows(per_person: list[list[Segment]]) -> list[Segment]:
    """Time windows where two or more people are active."""
    events = sorted([(a, 1) for segs in per_person for a, _ in segs] + [(b, -1) for segs in per_person for _, b in segs])
    out, depth, start = [], 0, 0.0
    for t, d in events:
        prev = depth
        depth += d
        if prev < 2 <= depth:
            start = t
        elif prev >= 2 > depth and t > start:
            out.append((round(start, 3), round(t, 3)))
    return out
