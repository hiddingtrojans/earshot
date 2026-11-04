"""Compare automatic binding on raw-mix vs delay-and-sum diarization (review/LITE_INPUT_PROTOCOL.md)."""

from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from pathlib import Path

from earshot.activity import overlap_windows
from earshot.bench import _spread, score_document
from earshot.calls import CallLog
from earshot.corrections import taps_to_oracle
from earshot.lite import attribute_with_confidence, gray_frames, head_motion
from earshot.media import SEPARATION_SR, TRANSCRIBE_SR, read_audio, resample
from earshot.timeline import build_captions
from earshot.tracking import Tracks
from earshot.transcribe import Turn, transcribe

WINDOWS = {
    "ES2008a 745 s": ("runs/ami_array_8", "bench/ami_ES2008a"),
    "ES2008a 635 s": ("runs/ami_array_8_635", "bench/ami_ES2008a_635"),
    "ES2008b 150 s": ("runs/ami_es2008b_150_array_8", "bench/ami_ES2008b_150"),
    "ES2008c 355 s (held out)": ("runs/ami_es2008c_355_array_8", "bench/ami_ES2008c_355"),
}
REPEATS = 3


def bind_and_score(doc: dict, run: Path, truth: dict, truth_dir: Path, baseline: list[Turn], motion) -> dict:
    mapping, confidence = attribute_with_confidence(baseline, motion, doc["info"]["fps"])
    return score_mapping(doc, run, truth, truth_dir, baseline, mapping, confidence)


def score_mapping(doc: dict, run: Path, truth: dict, truth_dir: Path, baseline: list[Turn],
                  mapping: dict, confidence: dict) -> dict:
    names = [person["name"] for person in doc["people"]]
    turns = [[Turn(str(person), t.start, t.end, t.text) for t in baseline if mapping.get(t.speaker) == person]
             for person in range(len(names))]
    activity = [[(t.start, t.end) for t in person_turns] for person_turns in turns]
    scored_doc = deepcopy(doc)
    scored_doc.pop("array_baseline", None)
    for person in scored_doc["people"]:
        person.pop("stem", None)
    scored_doc["baseline"] = [{"speaker": t.speaker, "start": t.start, "end": t.end, "text": t.text} for t in baseline]
    scored_doc["captions"] = [c.to_json() for c in build_captions(names, turns, activity)]
    scored_doc["activity"] = activity
    scored_doc["overlaps"] = overlap_windows(activity)
    scored = score_document(scored_doc, run, {k: v for k, v in truth.items() if k != "reference_tracks"}, truth_dir)
    return {"binding": scored["summary"]["earshot"]["attribution"],
            "oracle": scored["summary"]["baseline"]["attribution"],
            "labels": len({t.speaker for t in baseline}),
            "taps": taps_to_oracle(mapping, confidence, scored["oracle_mapping"], names)["taps"]}


def main() -> None:
    if os.environ.get("EARSHOT_REPLAY") != "1":
        sys.exit("run with EARSHOT_REPLAY=1 so no new model calls are made")
    report = {}
    for window, (run_dir, truth_dir) in WINDOWS.items():
        run, truth_dir = Path(run_dir), Path(truth_dir)
        doc = json.loads((run / "earshot.json").read_text())
        truth = json.loads((truth_dir / "truth.json").read_text())
        calls = CallLog(run)
        tracks = Tracks.load(run / "tracks.json")
        frames = gray_frames(run / doc["video"])
        motion = [head_motion(frames, tracks, person) for person in range(len(doc["people"]))]
        mix24 = resample(read_audio(run / doc["video"], SEPARATION_SR), SEPARATION_SR, TRANSCRIBE_SR)
        delay = read_audio(run / doc["array"]["delay_sum"], TRANSCRIBE_SR)
        rows = {"raw": [], "delay_sum": []}
        for index in range(REPEATS):
            raw = transcribe(mix24, calls, purpose=f"bench repeat {index}: diarize the raw mix", repeat=index)
            ds = transcribe(delay, calls, repeat=index,
                            purpose=f"bench repeat {index}: diarize GCC-PHAT delay-and-sum 8-mic baseline")
            rows["raw"].append(bind_and_score(doc, run, truth, truth_dir, raw, motion))
            rows["delay_sum"].append(bind_and_score(doc, run, truth, truth_dir, ds, motion))
        report[window] = {
            source: {"binding": _spread([r["binding"] for r in reps]), "oracle": _spread([r["oracle"] for r in reps]),
                     "taps": [r["taps"] for r in reps], "labels": [r["labels"] for r in reps]}
            for source, reps in rows.items()
        }
        print(window, json.dumps(report[window]), flush=True)
    Path("review/lite_input_probe.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
