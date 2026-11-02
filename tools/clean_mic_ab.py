"""Compare visual-only and span-prompted SAM Audio on clean mixed-down mic audio."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from earshot.calls import CallLog
from earshot.media import SEPARATION_SR, read_audio, write_wav
from earshot.separation import SamAudioSeparator
from earshot.spans import plan_document
from earshot.tracking import Tracks
from span_prompt_experiment import local_timing, matrix, separator_for

LABEL = "clean mixed-down mic (AMI Mix-Headset)"


def run(source: Path, out: Path, wav_dir: Path, device: str, seconds: float) -> dict:
    tracks = Tracks.load(source / "tracks.json")
    mixture = read_audio(source / "analysis.mp4")
    sample_count = int(seconds * SEPARATION_SR)
    window = mixture[:sample_count]
    references = [read_audio(Path(f"bench/ami_ES2008a/ref_{person}.wav"), seconds=seconds)
                  for person in "ABCD"]
    wav_dir.mkdir(parents=True, exist_ok=True)
    write_wav(wav_dir / "mixture.wav", window, SEPARATION_SR)
    result = {
        "audio_source": LABEL, "window_seconds": seconds,
        "gate": "50 ms frames, 25 ms hop, 200 ms smoothing; mixture above its 20th-percentile log-energy floor",
        "variants": {},
    }
    variants = [("keep", None), ("spans-text", None), ("spans-video", None)]
    for variant, _ in variants:
        run = out / variant
        run.mkdir(parents=True, exist_ok=True)
        if variant == "keep":
            separator = SamAudioSeparator(description="", mask_mode="keep", device=device)
            mapping, confidence = None, None
        else:
            separator, mapping, confidence, _ = separator_for(source, variant, device, clip_seconds=seconds)
            print(variant, "runtime Lite mapping", mapping, flush=True)
        stems_by_person = separator.separate_people(source / "analysis.mp4",
                                                   window if variant == "keep" else mixture,
                                                   tracks, CallLog(run))
        audio = [stems_by_person[person] for person in range(4)]
        assert all(samples.size == sample_count for samples in audio)
        for person, samples in zip("ABCD", audio):
            write_wav(wav_dir / f"{person}_{variant}.wav", samples, SEPARATION_SR)
        scores = matrix(audio, references, window)
        scores["timing"] = local_timing(run)
        scores["mapping"] = mapping
        scores["confidence"] = confidence
        if variant != "keep":
            (run / "span_plans.json").write_text(json.dumps(plan_document(separator), indent=2) + "\n")
        result["variants"][variant] = scores
        print(variant, "correct-voice rate", scores["correct_voice_rate"],
              "matrix", scores["matrix"], "timing", scores["timing"], flush=True)
        (out / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("runs/ami_cleanmic"))
    parser.add_argument("--out", type=Path, default=Path("runs/cleanmic_ab"))
    parser.add_argument("--wav-dir", type=Path, default=Path("review/ab_listen_cleanmic"))
    parser.add_argument("--device", default="mps")
    parser.add_argument("--seconds", type=float, default=10.0)
    args = parser.parse_args()
    result = run(args.source, args.out, args.wav_dir, args.device, args.seconds)
    print(json.dumps({variant: data["correct_voice_rate"] for variant, data in result["variants"].items()}, indent=2))


if __name__ == "__main__":
    main()
