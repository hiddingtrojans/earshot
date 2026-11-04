"""Do low-confidence flags catch the wrong bindings? Cache-only; see review/FLAG_COVERAGE.md."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from earshot.bench import oracle_speaker_mapping
from earshot.calls import CallLog
from earshot.lite import CONFIDENCE_THRESHOLD, attribute_with_confidence, gray_frames, head_motion
from earshot.media import SEPARATION_SR, TRANSCRIBE_SR, read_audio, resample
from earshot.tracking import Tracks
from earshot.transcribe import transcribe

from tools.lite_input_probe import REPEATS, WINDOWS


def main() -> None:
    if os.environ.get("EARSHOT_REPLAY") != "1":
        sys.exit("run with EARSHOT_REPLAY=1 so no new model calls are made")
    rows = []
    for window, (run_dir, truth_dir) in WINDOWS.items():
        run = Path(run_dir)
        doc = json.loads((run / "earshot.json").read_text())
        truth = json.loads((Path(truth_dir) / "truth.json").read_text())
        names = [person["name"] for person in doc["people"]]
        calls = CallLog(run)
        tracks = Tracks.load(run / "tracks.json")
        frames = gray_frames(run / doc["video"])
        motion = [head_motion(frames, tracks, person) for person in range(len(names))]
        sources = {
            "raw": (resample(read_audio(run / doc["video"], SEPARATION_SR), SEPARATION_SR, TRANSCRIBE_SR),
                    "bench repeat {i}: diarize the raw mix"),
            "delay_sum": (read_audio(run / doc["array"]["delay_sum"], TRANSCRIBE_SR),
                          "bench repeat {i}: diarize GCC-PHAT delay-and-sum 8-mic baseline"),
        }
        for source, (audio, purpose) in sources.items():
            for i in range(REPEATS):
                turns = transcribe(audio, calls, purpose=purpose.format(i=i), repeat=i)
                mapping, confidence = attribute_with_confidence(turns, motion, doc["info"]["fps"])
                oracle = oracle_speaker_mapping(
                    [{"speaker": t.speaker, "start": t.start, "end": t.end, "text": t.text} for t in turns], truth["people"])
                for label, person in mapping.items():
                    if label not in oracle:
                        continue
                    rows.append({"window": window, "source": source, "repeat": i, "label": label,
                                 "bound": names[person], "oracle": oracle[label],
                                 "correct": names[person] == oracle[label],
                                 "confidence": round(confidence[label], 4),
                                 "flagged": confidence[label] < CONFIDENCE_THRESHOLD})
    summary = {}
    for source in ("raw", "delay_sum"):
        subset = [r for r in rows if r["source"] == source]
        wrong = [r for r in subset if not r["correct"]]
        summary[source] = {"bindings": len(subset), "wrong": len(wrong),
                           "wrong_flagged": sum(r["flagged"] for r in wrong),
                           "right_flagged": sum(r["flagged"] for r in subset if r["correct"])}
    Path("review/flag_coverage.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    for r in rows:
        if not r["correct"]:
            print("WRONG", r)


if __name__ == "__main__":
    main()
