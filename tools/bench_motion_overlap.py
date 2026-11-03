"""Measure fixed-threshold Lite motion overlap markers and enrich cached run JSON."""

from __future__ import annotations

import argparse
import json
from dataclasses import fields
from pathlib import Path

from earshot.lite import gray_frames, head_motion
from earshot.motion import (
    MIN_EVENT_SECONDS,
    MOTION_MAD_MULTIPLIER,
    MOTION_NOISE_FLOOR,
    MOTION_SMOOTH_SECONDS,
    overlap_metrics,
    talked_over,
)
from earshot.spans import runtime_attribution
from earshot.timeline import Caption, sentence_segments
from earshot.tracking import Tracks
from earshot.transcribe import Turn

PROTOCOL = {
    "noise_floor": MOTION_NOISE_FLOOR, "mad_multiplier": MOTION_MAD_MULTIPLIER,
    "smooth_seconds": MOTION_SMOOTH_SECONDS, "min_event_seconds": MIN_EVENT_SECONDS,
}


def enrich(run: Path, truth_path: Path, write: bool = False) -> dict:
    truth = json.loads(truth_path.read_text())
    doc = json.loads((run / "earshot.json").read_text())
    for caption in doc["captions"]:
        caption["sentences"] = sentence_segments(caption["text"], caption["start"], caption["end"], caption["id"])
    doc["translation_segments"] = {
        language: {caption["id"]: sentence_segments(translations[caption["id"]], caption["start"], caption["end"], caption["id"])
                   for caption in doc["captions"] if caption["id"] in translations}
        for language, translations in doc.get("translations", {}).items()
    }
    turns, mapping, confidence, names = runtime_attribution(run)
    tracks = Tracks.load(run / "tracks.json")
    frames = gray_frames(run / doc["video"])
    motion = [head_motion(frames, tracks, person) for person in range(len(names))]
    people_turns = [[Turn(str(person), turn.start, turn.end, turn.text) for turn in turns
                     if mapping[turn.speaker] == person] for person in range(len(names))]
    fields_by_name = {field.name for field in fields(Caption)}
    captions = [Caption(**{key: value for key, value in caption.items() if key in fields_by_name})
                for caption in doc["captions"]]
    markers, thresholds = talked_over(captions, people_turns, motion, tracks.fps)
    metrics = overlap_metrics(people_turns, motion, truth["words"], names, tracks.fps)
    if write:
        doc["attribution"] = {"mapping": mapping, "confidence": confidence}
        doc["talked_over"] = markers
        doc["motion_thresholds"] = thresholds
        doc["motion_protocol"] = PROTOCOL
        (run / "earshot.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    return {
        "run": str(run), "audio": "Array1-01 single-mic", "mapping": mapping,
        "confidence": confidence, "motion_protocol": PROTOCOL,
        "motion_thresholds": thresholds, "metrics": metrics, "written": write,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--truth", type=Path, action="append", required=True)
    parser.add_argument("--out", type=Path, default=Path("review/motion_overlap.json"))
    parser.add_argument("--write", action="store_true", help="write enriched JSON to each run")
    args = parser.parse_args()
    if len(args.run) != len(args.truth):
        parser.error("each --run needs a corresponding --truth")
    result = {"windows": [enrich(run, truth, args.write) for run, truth in zip(args.run, args.truth)]}
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    for window in result["windows"]:
        print(window["run"], window["audio"], window["metrics"], "thresholds", window["motion_thresholds"])


if __name__ == "__main__":
    main()
