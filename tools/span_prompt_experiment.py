"""Run the bounded, local SAM Audio span-prompting experiment."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from copy import deepcopy
from pathlib import Path

import numpy as np

from earshot.activity import overlap_windows, speech_segments
from earshot.calls import CallLog
from earshot.envelope import correct_voice_rate, envelope_correlation
from earshot.media import SEPARATION_SR, TRANSCRIBE_SR, read_audio, resample, write_wav
from earshot.spans import SpanAudioSeparator, plan_document, runtime_attribution
from earshot.timeline import build_captions
from earshot.tracking import Tracks


def separator_for(run: Path, variant: str, device: str, mapping_kind: str = "auto",
                  truth: Path | None = None, clip_seconds: float | None = None):
    turns, mapping, confidence, names = runtime_attribution(run, mapping_kind, truth)
    separator = SpanAudioSeparator(
        turns=turns, mapping=mapping, span_mode=variant, device=device,
        mapping_source="oracle-evaluation-only" if mapping_kind == "oracle" else "runtime-lite",
        clip_seconds=clip_seconds,
    )
    return separator, mapping, confidence, names


def matrix(stems: list[np.ndarray], references: list[np.ndarray], mixture: np.ndarray) -> dict:
    rows = [[round(envelope_correlation(stem, reference, mixture), 4) for reference in references]
            for stem in stems]
    baseline = [round(envelope_correlation(mixture, reference, mixture), 4) for reference in references]
    diagonal = round(sum(row[index] for index, row in enumerate(rows)) / len(rows), 4)
    off_diagonal = round(sum(row[j] for i, row in enumerate(rows) for j in range(len(row)) if i != j)
                         / (len(rows) * (len(rows) - 1)), 4)
    return {
        "matrix": rows, "mixture_baseline": baseline,
        "correct_voice_rate": correct_voice_rate(rows),
        "mixture_correct_voice_rate": correct_voice_rate([baseline] * len(rows)),
        "diagonal_mean": diagonal, "off_diagonal_mean": off_diagonal,
    }


def local_timing(run: Path) -> dict:
    rows = [json.loads(line) for line in (run / "calls.jsonl").read_text().splitlines() if line.strip()]
    local = [row for row in rows if row.get("model") == "facebook/sam-audio-small-tv"]
    if not local:
        return {}
    row = local[-1]
    return {key: row.get(key) for key in ("cache", "latency_ms", "device", "batching", "timings_ms",
                                          "span_mode", "mapping_source", "anchor_digest", "key")}


def ab(args) -> dict:
    source = args.run
    tracks = Tracks.load(source / "tracks.json")
    mixture = read_audio(source / "analysis.mp4")
    references = [read_audio(Path(f"bench/ami_ES2008a/ref_{person}.wav"), seconds=args.seconds)
                  for person in "ABCD"]
    sample_count = int(args.seconds * SEPARATION_SR)
    mixture_window = mixture[:sample_count]
    args.wav_dir.mkdir(parents=True, exist_ok=True)
    write_wav(args.wav_dir / "mixture.wav", mixture_window, SEPARATION_SR)
    result = {
        "window_seconds": args.seconds,
        "gate": "Mixture log energy above its 20th percentile; 50 ms frames, 25 ms hop, 200 ms smoothing",
        "round2_visual_keep": json.loads(Path("review/envelope_ab.json").read_text())["keep"],
        "variants": {},
    }
    for variant in args.variants:
        run = args.out / variant
        run.mkdir(parents=True, exist_ok=True)
        separator, mapping, confidence, names = separator_for(source, variant, args.device,
                                                              clip_seconds=args.seconds)
        print(f"{variant}: runtime Lite mapping {mapping}", flush=True)
        started = __import__("time").perf_counter()
        stems = separator.separate_people(source / "analysis.mp4", mixture, tracks, CallLog(run))
        elapsed = __import__("time").perf_counter() - started
        audio = [stems[person] for person in range(4)]
        assert all(samples.size == sample_count for samples in audio)
        for person, samples in zip("ABCD", audio):
            write_wav(args.wav_dir / f"{person}_{variant}.wav", samples, SEPARATION_SR)
        scores = matrix(audio, references, mixture_window)
        (run / "span_plans.json").write_text(json.dumps(plan_document(separator), indent=2) + "\n")
        scores.update({
            "mapping": mapping, "confidence": confidence,
            "first_window_plans": {str(person): separator._plans[person][0] for person in range(4)},
            "timing": {**local_timing(run), "total_seconds_including_mapping": round(elapsed, 3)},
            "wav_dir": str(args.wav_dir),
        })
        result["variants"][variant] = scores
        print(variant, json.dumps({key: scores[key] for key in
                                   ("correct_voice_rate", "matrix", "timing")}, indent=2), flush=True)
        (args.out / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.out / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def full(args) -> dict:
    if args.transcribe and not os.environ.get("MODEL_API_KEY"):
        raise RuntimeError("Full transcription needs MODEL_API_KEY inside the interactive shell; local A/B does not")
    source = args.run
    tracks = Tracks.load(source / "tracks.json")
    mixture = read_audio(source / "analysis.mp4")
    separator, mapping, confidence, names = separator_for(source, args.variant, args.device,
                                                          args.mapping, args.truth)
    print(f"{args.variant} {args.mapping}: mapping {mapping}", flush=True)
    args.out.mkdir(parents=True, exist_ok=True)
    for name in ("analysis.mp4", "tracks.json"):
        if not (args.out / name).exists():
            shutil.copy2(source / name, args.out / name)
    (args.out / "calls").mkdir(exist_ok=True)
    baseline_keys = set()
    for line in (source / "calls.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("model") == "muse-voice-transcribe-1.0" and "diarize the raw mix" in row.get("purpose", ""):
            baseline_keys.add(row["key"])
    for key in baseline_keys:
        cached = source / "calls" / f"{key}.json"
        if cached.exists() and not (args.out / "calls" / cached.name).exists():
            shutil.copy2(cached, args.out / "calls" / cached.name)
    started = __import__("time").perf_counter()
    separated = separator.separate_people(source / "analysis.mp4", mixture, tracks, CallLog(args.out))
    elapsed = __import__("time").perf_counter() - started
    (args.out / "span_plans.json").write_text(json.dumps(plan_document(separator), indent=2) + "\n")
    original = json.loads((source / "earshot.json").read_text())
    people = deepcopy(original["people"])
    turns, activity = [], []
    from earshot.transcribe import transcribe

    for person, name in enumerate(names):
        audio = separated[person]
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        stem = f"stems/{person}_{slug}.wav"
        write_wav(args.out / stem, audio, SEPARATION_SR)
        people[person]["stem"] = stem
        activity.append(speech_segments(resample(audio, SEPARATION_SR, 16_000), 16_000))
        turns.append(transcribe(resample(audio, SEPARATION_SR, TRANSCRIBE_SR), CallLog(args.out),
                                purpose=f"transcribe {name}'s isolated voice") if args.transcribe else [])
    captions = build_captions(names, turns, activity) if args.transcribe else []
    doc = {
        "video": "analysis.mp4", "info": original["info"],
        "separator": f"SAM Audio {args.variant} ({args.mapping}; experiment)",
        "people": people, "captions": [caption.to_json() for caption in captions],
        "baseline": original["baseline"], "activity": activity,
        "overlaps": overlap_windows(activity),
        "attribution": {"mapping": mapping, "confidence": confidence,
                        "mapping_source": separator.mapping_source},
        "threads": [], "catchups": [], "catchup_model": "spark",
        "translations": {}, "translation_status": {},
    }
    if args.transcribe:
        (args.out / "earshot.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    metadata = {
        "mapping": mapping, "confidence": confidence, "mapping_source": separator.mapping_source,
        "variant": args.variant, "seconds": round(elapsed, 3), "timing": local_timing(args.out),
        "transcribed": args.transcribe,
    }
    (args.out / "span_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    if (source / "corrections.json").exists():
        (args.out / "corrections.json").write_text((source / "corrections.json").read_text())
    print(json.dumps(metadata, indent=2), flush=True)
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    a = sub.add_parser("ab", help="run both variants on the round-2 10 s window")
    a.add_argument("--run", type=Path, default=Path("runs/ami_lite"))
    a.add_argument("--out", type=Path, default=Path("runs/span_ab"))
    a.add_argument("--wav-dir", type=Path, default=Path("review/ab_listen_spans"))
    a.add_argument("--seconds", type=float, default=10.0)
    a.add_argument("--device", default="mps")
    a.add_argument("--variants", nargs="+", default=["spans-text", "spans-video"])
    a.set_defaults(func=ab)
    f = sub.add_parser("full", help="run a qualifying variant on a complete cached clip")
    f.add_argument("--run", type=Path, required=True)
    f.add_argument("--truth", type=Path, required=True)
    f.add_argument("--out", type=Path, required=True)
    f.add_argument("--variant", choices=["spans-text", "spans-video"], required=True)
    f.add_argument("--mapping", choices=["auto", "oracle"], default="auto")
    f.add_argument("--device", default="mps")
    f.add_argument("--transcribe", action="store_true", help="permit hosted Voice calls for new stems")
    f.set_defaults(func=full)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
