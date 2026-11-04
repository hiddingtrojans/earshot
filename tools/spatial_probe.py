"""Evaluate spatial clustering on a development AMI window without using truth for guidance."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

from earshot.array import gcc_phat_delay, inverse_stft, load_array, souden_mvdr, stft_array
from earshot.envelope import correct_voice_rate, envelope_correlation
from earshot.media import read_audio, resample
from earshot.motion import turns_mask
from earshot.spatial import align_clusters, cluster_profiles, spatial_delay, spatial_profiles
from earshot.transcribe import Turn


def probe(run: Path, truth_dir: Path, output: Path, seed: int = 42) -> dict:
    started = time.perf_counter()
    doc = json.loads((run / "earshot.json").read_text())
    truth = json.loads((truth_dir / "truth.json").read_text())
    audio, _ = load_array(truth_dir / "array.wav")
    frequencies, times, spectrogram = stft_array(audio)
    fps = doc["info"]["fps"]
    frames = int(round(doc["info"]["duration"] * fps))
    mapping = doc["attribution"]["mapping"]
    turns = [[Turn(str(person), turn["start"], turn["end"], turn["text"])
              for turn in doc["baseline"] if mapping.get(turn["speaker"]) == person]
             for person in range(len(doc["people"]))]
    activities = [turns_mask(person_turns, frames, fps) for person_turns in turns]
    indexes = np.minimum((times * fps).astype(int), frames - 1)
    known = []
    for person, person_turns in enumerate(turns):
        if not person_turns:
            continue
        others = np.any([mask for index, mask in enumerate(activities) if index != person], axis=0)
        guide = (activities[person] & ~others)[indexes]
        if guide.sum() < 2:
            continue
        estimated, _ = spatial_delay(spectrogram, frequencies, guide)
        reference = read_audio(truth_dir / truth["reference_tracks"][f"Speaker {chr(65 + person)}"], 16_000)
        base = gcc_phat_delay(reference, audio[:, 0])
        actual = [gcc_phat_delay(reference, audio[:, channel]) - base for channel in range(1, 8)]
        known.append({"person": person, "estimated_relative_delays": estimated.tolist(),
                      "headset_relative_delays_diagnostic_only": actual})

    profiles, energy = spatial_profiles(spectrogram, frequencies)
    assignments, cluster_metadata = cluster_profiles(profiles, energy, len(doc["people"]), seed=seed)
    known_people = [person for person, person_turns in enumerate(turns) if person_turns]
    overlap_scores = np.array([[np.count_nonzero((assignments == cluster) & activities[person][indexes]) /
                                max(1, np.count_nonzero(assignments == cluster)) for person in known_people]
                               for cluster in range(len(doc["people"]))])
    cluster_rows, person_columns = linear_sum_assignment(-overlap_scores)
    runtime_mapping = {int(cluster): known_people[person] for cluster, person in zip(cluster_rows, person_columns)}
    remaining_clusters = [cluster for cluster in range(len(doc["people"])) if cluster not in runtime_mapping]
    missing_people = [person for person in range(len(doc["people"])) if person not in known_people]
    runtime_mapping.update({cluster: person for cluster, person in zip(remaining_clusters, missing_people)})
    cluster_metadata["runtime_assignment"] = runtime_mapping
    cluster_metadata["diarization_overlap_scores"] = overlap_scores.tolist()
    references = [read_audio(truth_dir / truth["reference_tracks"][person["name"]], 48_000)
                  for person in doc["people"]]
    mixture = resample(audio[:, 0], 16_000, 48_000)
    matrix, cluster_audio = [], {}
    for cluster in range(len(doc["people"])):
        guide = assignments == cluster
        if guide.sum() < 2:
            matrix.append([0.0] * len(references))
            continue
        separated, metadata = souden_mvdr(spectrogram, guide)
        audio48 = resample(inverse_stft(separated, audio.shape[0]), 16_000, 48_000)
        cluster_audio[cluster] = audio48
        matrix.append([round(envelope_correlation(audio48, reference, mixture), 4) for reference in references])
    aligned, diagnostic_mapping = align_clusters(matrix)
    diagonal = float(np.mean([aligned[index][index] for index in range(len(aligned))]))
    off_diagonal = float(np.mean([aligned[row][column] for row in range(len(aligned))
                                 for column in range(len(aligned)) if row != column]))
    result = {
        "run": str(run), "truth": str(truth_dir), "protocol": "development-only spatial probe; headsets used for scoring only",
        "cluster_method": cluster_metadata, "known_spatial_delays": known,
        "matrix_clusters_by_headset": matrix, "diagnostic_assignment": diagnostic_mapping,
        "aligned_matrix_diagnostic_only": aligned, "correct_voice_diagnostic_only": correct_voice_rate(aligned),
        "diagonal_mean_diagnostic_only": round(diagonal, 4), "off_diagonal_mean": round(off_diagonal, 4),
        "seconds": round(time.perf_counter() - started, 3),
    }
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=Path("runs/ami_array_8_635"))
    parser.add_argument("--truth", type=Path, default=Path("bench/ami_ES2008a_635"))
    parser.add_argument("--out", type=Path, default=Path("review/spatial_635_probe.json"))
    args = parser.parse_args()
    print(json.dumps(probe(args.run, args.truth, args.out), indent=2))


if __name__ == "__main__":
    main()
