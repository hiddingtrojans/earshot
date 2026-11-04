"""Calibrate anchored spatial residuals on the development window only."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from earshot.anchored import anchored_residual
from earshot.array import load_array, stft_array
from earshot.motion import turns_mask
from earshot.transcribe import Turn


def calibrate(run: Path, truth_dir: Path, output: Path, return_residual: bool = False,
              mapping_override: dict | None = None, **parameters) -> dict:
    started = time.perf_counter()
    doc = json.loads((run / "earshot.json").read_text())
    audio, _ = load_array(truth_dir / "array.wav")
    frequencies, times, spectrogram = stft_array(audio)
    fps = doc["info"]["fps"]
    frames = int(round(doc["info"]["duration"] * fps))
    mapping = mapping_override or doc["attribution"]["mapping"]
    turns = [[Turn(str(person), turn["start"], turn["end"], turn["text"])
              for turn in doc["baseline"] if mapping.get(turn["speaker"]) == person]
             for person in range(len(doc["people"]))]
    activities = [turns_mask(person_turns, frames, fps) for person_turns in turns]
    indexes = np.minimum((times * fps).astype(int), frames - 1)
    fallback = doc["array"]["guide"]["motion_fallback_people"]
    guides = []
    for person, person_turns in enumerate(turns):
        others = np.any([mask for index, mask in enumerate(activities) if index != person], axis=0)
        guides.append((activities[person] & ~others)[indexes] if person_turns else np.zeros(times.size, dtype=bool))
    residual, metadata = anchored_residual(spectrogram, frequencies, guides, fallback, **parameters)
    result = {"run": str(run), "truth": str(truth_dir), "fallback_people": fallback,
              "method": metadata, "seconds": round(time.perf_counter() - started, 3)}
    if return_residual:
        result["residual"] = residual
        result["times"] = times
    serializable = {key: value for key, value in result.items() if key not in ("residual", "times")}
    output.write_text(json.dumps(serializable, indent=2, allow_nan=True) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=Path("runs/ami_array_8_635"))
    parser.add_argument("--truth", type=Path, default=Path("bench/ami_ES2008a_635"))
    parser.add_argument("--out", type=Path, default=Path("review/anchored_635_calibration.json"))
    args = parser.parse_args()
    print(json.dumps(calibrate(args.run, args.truth, args.out), indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
