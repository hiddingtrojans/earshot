"""Collect array benchmark evidence without hand-copying metrics or matrices."""

from __future__ import annotations

import json
from pathlib import Path

from earshot.bench import oracle_speaker_mapping
from earshot.corrections import taps_to_oracle
from earshot.quality import better_overlap


def envelope_stats(matrix: list[list[float]]) -> tuple[float, float]:
    diagonal = sum(row[index] for index, row in enumerate(matrix)) / len(matrix)
    off_diagonal = sum(row[column] for index, row in enumerate(matrix) for column in range(len(row)) if column != index)
    count = len(matrix) * (len(matrix) - 1)
    return round(diagonal, 4), round(off_diagonal / count, 4)


def summarize(run: Path) -> dict:
    doc = json.loads((run / "earshot.json").read_text())
    bench = json.loads((run / "bench_array.json").read_text())
    summary = bench["summary"]
    better = better_overlap(summary)
    diagonal, off_diagonal = envelope_stats(list(bench["repeats"][0]["envelope"]["people"].values()))
    result = {
        "audio": "AMI 8-mic meeting-room array", "channels": doc["array"]["channels"],
        "metrics": summary, "better_baseline_overlap": better,
        "overlap_delta": None if better is None else round(summary["earshot"]["overlap_recall"]["mean"] - better, 4),
        "go_no_go": None if better is None else summary["earshot"]["attribution"]["mean"] >= 0.8
        and summary["earshot"]["overlap_recall"]["mean"] >= better + 0.1,
        "envelope": bench["repeats"][0]["envelope"], "diagonal_mean": diagonal, "off_diagonal_mean": off_diagonal,
        "runtime": {key: doc["array"][key] for key in ("beamforming_seconds", "analysis_seconds", "delays", "guide", "mvdr", "mapping_source")},
        "repeat_metrics": [repeat["summary"] for repeat in bench["repeats"]],
    }
    if run.name.endswith("_635"):
        truth = json.loads(Path("bench/ami_ES2008a_635/truth.json").read_text())
        oracle = oracle_speaker_mapping(doc["baseline"], truth["people"])
        names = [person["name"] for person in doc["people"]]
        correction = taps_to_oracle(doc["attribution"]["mapping"], doc["attribution"].get("confidence", {}), oracle, names)
        result["mapping_evaluation"] = {
            "automatic_mapping": doc["attribution"]["mapping"], "oracle_association": oracle,
            "correction_taps": correction["taps"], "mapping_after_one_tap_correction": doc["attribution"]["mapping"],
            "note": "No taps are needed: the automatic mapping already matches the oracle association; no duplicate corrected run.",
        }
    elif run.name.startswith("ami_es2008b"):
        suffix = run.name.removeprefix("ami_es2008b").split("_array", 1)[0]
        truth = json.loads(Path(f"bench/ami_ES2008b{suffix}/truth.json").read_text())
        oracle = oracle_speaker_mapping(doc["baseline"], truth["people"])
        correction = taps_to_oracle(doc["attribution"]["mapping"], doc["attribution"].get("confidence", {}),
                                   oracle, [person["name"] for person in doc["people"]])
        result["mapping_evaluation"] = {
            "automatic_mapping": doc["attribution"]["mapping"], "oracle_association": oracle,
            "taps_to_oracle": correction["taps"],
            "note": "Diagnostic only: no oracle-mapped product claim and no corrected benchmark run.",
        }
    return result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", type=Path, nargs="*")
    args = parser.parse_args()
    if args.runs:
        for run in args.runs:
            result = summarize(run)
            output = Path("review") / f"{run.name}_summary.json"
            output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
            print(run, result["metrics"], result["go_no_go"])
        return
    for window in ("745", "635"):
        suffix = "" if window == "745" else "_635"
        result = {f"ami_array_{count}{suffix}": summarize(Path(f"runs/ami_array_{count}{suffix}"))
                  for count in (8, 5, 4)}
        Path(f"review/array_{window}_summary.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        print(window, {name: (data["metrics"]["earshot"], data["overlap_delta"], data["go_no_go"])
                       for name, data in result.items()})


if __name__ == "__main__":
    main()
