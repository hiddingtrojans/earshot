"""Development-only anchored-guide sweep and go/no-go checks."""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from earshot.array import inverse_stft, load_array, souden_mvdr, stft_array
from earshot.envelope import correct_voice_rate, envelope_correlation
from earshot.lite import gray_frames, head_motion
from earshot.media import read_audio, resample
from earshot.motion import guide_activities, interval_mask, turns_mask
from earshot.tracking import Tracks
from earshot.transcribe import Turn
from tools.anchored_probe import calibrate


def guide_scores(predicted: np.ndarray, words: list[dict], name: str, fps: float, frames: int) -> dict:
    own = interval_mask([(word["start"], word["end"]) for word in words if word["person"] == name], frames, fps)
    others = interval_mask([(word["start"], word["end"]) for word in words if word["person"] != name], frames, fps)
    truth = own & ~others
    if not truth.any():
        return {"precision": None, "recall": None, "f1": None,
                "predicted_frames": int(predicted.sum()), "truth_solo_frames": 0}
    true_positive = int(np.count_nonzero(predicted & truth))
    precision = true_positive / max(1, int(predicted.sum()))
    recall = true_positive / max(1, int(truth.sum()))
    return {"precision": round(precision, 4), "recall": round(recall, 4),
            "f1": round(2 * precision * recall / max(1e-12, precision + recall), 4),
            "predicted_frames": int(predicted.sum()), "truth_solo_frames": int(truth.sum())}


def envelope_matrix(run: Path, truth_dir: Path, audio: np.ndarray, spectrogram: np.ndarray,
                    fallback: int, guide: np.ndarray | None) -> list[list[float]]:
    doc = json.loads((run / "earshot.json").read_text())
    truth = json.loads((truth_dir / "truth.json").read_text())
    mixture = resample(audio[:, 0], 16_000, 48_000)
    matrix = []
    for person, person_doc in enumerate(doc["people"]):
        if person == fallback and guide is not None:
            separated, _ = souden_mvdr(spectrogram, guide)
            estimate = resample(inverse_stft(separated, audio.shape[0]), 16_000, 48_000)
        else:
            estimate = read_audio(run / person_doc["stem"], 48_000)
        matrix.append([round(envelope_correlation(
            estimate, read_audio(truth_dir / truth["reference_tracks"][person["name"]], 48_000), mixture), 4)
            for person in doc["people"]])
    return matrix


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=Path("runs/ami_array_8_635"))
    parser.add_argument("--truth", type=Path, default=Path("bench/ami_ES2008a_635"))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--diagnostic-oracle-mapping", action="store_true")
    args = parser.parse_args()
    started = time.perf_counter()
    run, truth_dir = args.run, args.truth
    output_path = args.out or Path(f"review/anchored_{run.name}_sweep.json")
    doc = json.loads((run / "earshot.json").read_text())
    truth = json.loads((truth_dir / "truth.json").read_text())
    fps = doc["info"]["fps"]
    frames = int(round(doc["info"]["duration"] * fps))
    fallback = doc["array"]["guide"]["motion_fallback_people"][0]
    name = doc["people"][fallback]["name"]
    tracks = Tracks.load(run / "tracks.json")
    gray = gray_frames(run / "analysis.mp4")
    motion = [head_motion(gray, tracks, person) for person in range(len(doc["people"]))]
    if args.diagnostic_oracle_mapping:
        from earshot.bench import oracle_speaker_mapping

        mapping = oracle_speaker_mapping(doc["baseline"], truth["people"])
    else:
        mapping = doc["attribution"]["mapping"]
    turns = [[Turn(str(person), turn["start"], turn["end"], turn["text"])
              for turn in doc["baseline"] if mapping.get(turn["speaker"]) == person]
             for person in range(len(doc["people"]))]
    guides, _ = guide_activities(turns, motion, fps, frames)
    baseline = guide_scores(guides[fallback], truth["words"], name, fps, frames)
    if baseline["f1"] is None:
        result = {"decision": "not evaluable: no solo target speech", "baseline_guide": baseline,
                  "protocol": "development-only; no parameter selection on an empty target"}
        output_path.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return
    activities = [turns_mask(person_turns, frames, fps) for person_turns in turns]
    others = np.any([mask for person, mask in enumerate(activities) if person != fallback], axis=0)
    audio, _ = load_array(truth_dir / "array.wav")
    frequencies, times, spectrogram = stft_array(audio)
    indexes = np.minimum((times * fps).astype(int), frames - 1)
    results = []
    for confidence in (3.0, 5.0):
        for triangle_fraction in (0.25, 0.5):
            for residual_z in (1.5, 2.0):
                parameters = {"confidence_min": confidence, "triangle_min_fraction": triangle_fraction,
                              "residual_z_min": residual_z}
                result = calibrate(run, truth_dir, Path("review/.anchored_tmp.json"), True,
                                   mapping_override=mapping, **parameters)
                raw = result["residual"][0] & ~others[indexes]
                video = np.zeros(frames, dtype=bool)
                video[indexes] = raw
                metrics = guide_scores(video, truth["words"], name, fps, frames)
                accepted = bool(result["method"]["accepted"]) and int(raw.sum()) >= 10
                record = {"parameters": parameters, "calibration": result["method"]["calibration"],
                          "residual_frames": result["method"]["residual_frames"],
                          "effective_frames": int(raw.sum()), "accepted": accepted, "guide": metrics}
                if accepted:
                    candidate = envelope_matrix(run, truth_dir, audio, spectrogram, fallback, raw)
                    baseline_matrix = envelope_matrix(run, truth_dir, audio, spectrogram, fallback, None)
                    record["envelope"] = matrix_report(candidate)
                    record["baseline_envelope"] = matrix_report(baseline_matrix)
                results.append(record)
                print(parameters, 'accepted', accepted, 'calibration', record['calibration'],
                      'guide', metrics, flush=True)
    baseline_f1_gate = max(0.01, 2 * baseline["f1"])
    passing = [record for record in results if record["accepted"] and
               record["guide"]["f1"] >= baseline_f1_gate and record["guide"]["precision"] >= 0.5]
    passing.sort(key=lambda record: record["guide"]["f1"], reverse=True)
    output = {"protocol": "development-only; truth used for scoring, not guide construction",
              "mapping_source": "diagnostic oracle (development only)" if args.diagnostic_oracle_mapping else "runtime-lite",
              "fallback_person": name, "baseline_guide": baseline,
              "f1_gate": {"minimum": round(baseline_f1_gate, 4), "minimum_precision": 0.5},
              "configurations": results, "selected": passing[0] if passing else None,
              "decision": "advance" if passing else "no-go", "seconds": round(time.perf_counter() - started, 3)}
    output_path.write_text(json.dumps(output, indent=2) + "\n")
    Path("review/.anchored_tmp.json").unlink(missing_ok=True)
    print(json.dumps({"baseline": baseline, "passing_configurations": len(passing),
                      "selected": output["selected"], "decision": output["decision"]}, indent=2))


def matrix_report(matrix: list[list[float]]) -> dict:
    diagonal = float(np.mean([row[index] for index, row in enumerate(matrix)]))
    off_diagonal = float(np.mean([row[column] for index, row in enumerate(matrix)
                                 for column in range(len(row)) if column != index]))
    return {"matrix": matrix, "correct_voice": correct_voice_rate(matrix),
            "diagonal_mean": round(diagonal, 4), "off_diagonal_mean": round(off_diagonal, 4)}


if __name__ == "__main__":
    main()
