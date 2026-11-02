"""Far-field voice-envelope correlation for visual-separation evaluation."""

from __future__ import annotations

import numpy as np
from scipy.ndimage import uniform_filter1d


def log_energy_envelope(audio: np.ndarray, sample_rate: int = 48_000) -> np.ndarray:
    frame = int(sample_rate * 0.050)
    hop = int(sample_rate * 0.025)
    if audio.size < frame:
        return np.array([])
    starts = range(0, audio.size - frame + 1, hop)
    rms = np.array([np.sqrt(np.mean(audio[start:start + frame] ** 2) + 1e-12) for start in starts])
    return uniform_filter1d(np.log10(rms), size=max(1, int(round(0.2 / 0.025))), mode="nearest")


def envelope_correlation(estimate: np.ndarray, reference: np.ndarray) -> float:
    left = log_energy_envelope(estimate)
    right = log_energy_envelope(reference)
    size = min(left.size, right.size)
    if size < 2:
        return 0.0
    left, right = left[:size], right[:size]
    noise_floor = float(np.percentile(right, 20))
    active = right > noise_floor
    if active.sum() < 2:
        return 0.0
    left, right = left[active] - left[active].mean(), right[active] - right[active].mean()
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    return float(np.dot(left, right) / denominator) if denominator else 0.0


def correct_voice_rate(matrix: list[list[float]]) -> float:
    if not matrix:
        return 0.0
    return round(sum(row[index] == max(row) for index, row in enumerate(matrix)) / len(matrix), 3)
