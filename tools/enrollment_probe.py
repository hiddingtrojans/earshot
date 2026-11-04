"""Measure the ceiling of short solo-speech enrollment, with oracle spans for diagnosis only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from earshot.array import inverse_stft, load_array, souden_mvdr, stft_array
from earshot.envelope import correct_voice_rate, envelope_correlation
from earshot.media import read_audio, resample


def solo_spans(words: list[dict], person: str, fps: int = 100) -> list[tuple[float, float]]:
    last = max(word["end"] for word in words)
    own = np.zeros(int(np.ceil(last * fps)) + 1, dtype=bool)
    others = np.zeros_like(own)
    for word in words:
        start, end = int(np.floor(word["start"] * fps)), int(np.ceil(word["end"] * fps))
        (own if word["person"] == person else others)[start:end] = True
    mask = own & ~others
    edges = np.flatnonzero(np.diff(np.r_[False, mask, False]))
    return [(start / fps, end / fps) for start, end in zip(edges[::2], edges[1::2]) if end - start >= 0.5]


def enrollment(words: list[dict], person: str, seconds: float = 4.0) -> list[tuple[float, float]]:
    chosen, total = [], 0.0
    for start, end in sorted(solo_spans(words, person), key=lambda span: span[1] - span[0], reverse=True):
        if total >= seconds:
            break
        duration = min(end - start, seconds - total)
        chosen.append((start, start + duration))
        total += duration
    return chosen


def probe(run: Path, truth_dir: Path, output: Path, seconds: float = 4.0) -> dict:
    doc = json.loads((run / "earshot.json").read_text())
    truth = json.loads((truth_dir / "truth.json").read_text())
    audio, _ = load_array(truth_dir / "array.wav")
    _, times, spectrogram = stft_array(audio)
    mixture = resample(audio[:, 0], 16_000, 48_000)
    rows, spans = [], {}
    for person in doc["people"]:
        selected = enrollment(truth["words"], person["name"], seconds=seconds)
        spans[person["name"]] = selected
        if not selected:
            rows.append([0.0] * len(doc["people"]))
            continue
        guide = np.zeros(times.size, dtype=bool)
        for start, end in selected:
            guide |= (times >= start) & (times < end)
        separated, _ = souden_mvdr(spectrogram, guide)
        estimate = resample(inverse_stft(separated, audio.shape[0]), 16_000, 48_000)
        rows.append([round(envelope_correlation(
            estimate, read_audio(truth_dir / truth["reference_tracks"][other["name"]], 48_000), mixture), 4)
            for other in doc["people"]])
    diagonal = float(np.mean([row[index] for index, row in enumerate(rows)]))
    off_diagonal = float(np.mean([row[column] for index, row in enumerate(rows)
                                 for column in range(len(row)) if column != index]))
    result = {
        "protocol": f"ORACLE ENROLLMENT CEILING, not a runtime or product result. Truth chooses up to {seconds:g} s of solo speech per person.",
        "enrollment_seconds_cap": seconds,
        "run": str(run), "truth": str(truth_dir), "enrollment_spans": spans,
        "matrix": rows, "correct_voice": correct_voice_rate(rows),
        "diagonal_mean": round(diagonal, 4), "off_diagonal_mean": round(off_diagonal, 4),
    }
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--truth", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=4.0)
    args = parser.parse_args()
    print(json.dumps(probe(args.run, args.truth, args.out, seconds=args.seconds), indent=2))


if __name__ == "__main__":
    main()
