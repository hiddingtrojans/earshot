"""Run one real hosted-model smoke test on a short public video clip."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from earshot.calls import CallLog
from earshot.lite import attribute_turns, gray_frames, head_motion
from earshot.media import SEPARATION_SR, TRANSCRIBE_SR, ffmpeg, prepare_analysis_video, probe, read_audio, resample
from earshot.spark import assign_threads, catch_up
from earshot.timeline import build_captions
from earshot.tracking import Tap, track_people
from earshot.transcribe import Turn, transcribe


def smoke(video: Path, taps: list[Tap], out: Path, seconds: float) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    short = out / "source.mp4"
    analysis = out / "analysis.mp4"
    if not analysis.exists():
        ffmpeg("-i", str(video), "-t", str(seconds), "-c", "copy", str(short))
        prepare_analysis_video(short, analysis)
    info = probe(analysis)
    calls = CallLog(out)
    before = sum(1 for _ in calls.log_path.open()) if calls.log_path.exists() else 0

    tracks = track_people(analysis, taps, info, calls)
    tracks.save(out / "tracks.json")
    tracking = []
    for person, tap in enumerate(taps):
        present, area = 0, 0.0
        for frame in range(info.frames):
            mask = tracks.mask(person, frame)
            visible = bool(mask.any())
            present += int(visible)
            area += float(mask.mean()) if visible else 0.0
        tracking.append({
            "person": tap.name,
            "frame_coverage": round(present / info.frames, 4),
            "mean_mask_area_fraction": round(area / present, 4) if present else 0.0,
        })
        print(f"{tap.name}: coverage={present}/{info.frames}; mean mask area={tracking[-1]['mean_mask_area_fraction']:.4f}")

    mixture = read_audio(analysis, SEPARATION_SR)
    baseline = transcribe(resample(mixture, SEPARATION_SR, TRANSCRIBE_SR), calls,
                          purpose="diarize the raw mix (today's captions)")
    print("Voice turns:", json.dumps([asdict(turn) for turn in baseline], ensure_ascii=False))

    frames = gray_frames(analysis)
    motion = [head_motion(frames, tracks, person) for person in range(len(taps))]
    mapping = attribute_turns(baseline, motion, info.fps)
    turns = [[Turn(str(person), turn.start, turn.end, turn.text) for turn in baseline
              if mapping.get(turn.speaker) == person] for person in range(len(taps))]
    activity = [[(turn.start, turn.end) for turn in person_turns] for person_turns in turns]
    captions = build_captions([tap.name for tap in taps], turns, activity)
    threads = assign_threads(captions, calls)
    catchup = catch_up(captions, [tap.name for tap in taps], info.duration, info.duration, calls)
    print("Spark threads:", json.dumps(threads, ensure_ascii=False))
    print("Spark catch-up:", json.dumps(catchup, ensure_ascii=False))

    lines = calls.log_path.read_text().splitlines()[before:]
    new_calls = [json.loads(line) for line in lines]
    summary = {
        "video": str(video),
        "seconds": info.duration,
        "tracking": tracking,
        "turns": [asdict(turn) for turn in baseline],
        "captions": [caption.to_json() for caption in captions],
        "threads": threads,
        "catchup": catchup,
        "calls": [{
            "model": call.get("model"), "purpose": call.get("purpose"),
            "cache": call.get("cache"), "request_id": call.get("request_id"),
        } for call in new_calls],
    }
    (out / "smoke.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print("Calls this run:", json.dumps(summary["calls"], ensure_ascii=False))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--tap", action="append", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=10.0)
    args = parser.parse_args()
    smoke(args.video, [Tap.parse(tap) for tap in args.tap], args.out, args.seconds)


if __name__ == "__main__":
    main()
