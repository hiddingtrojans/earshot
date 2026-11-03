"""End-to-end analysis of one video into a run folder the viewer can play."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .activity import overlap_windows, speech_segments
from .board import build_board, check_board_items
from .calls import CallLog
from .media import SEPARATION_SR, TRANSCRIBE_SR, prepare_analysis_video, probe, read_audio, resample, write_wav
from .spark import assign_threads, catch_up
from .timeline import build_captions, sentence_segments
from .tracking import Tap, Tracks, track_people
from .transcribe import Turn, transcribe

COLORS = ["#E4572E", "#2E86AB", "#7BAE37", "#9B5DE5", "#F2A541", "#17BEBB"]


@dataclass
class Options:
    separator: str = "samaudio"      # "samaudio" | "lite"
    replay: bool = False
    text_features: Path | None = None   # None = repo default (assets/text_features.npz)
    mask_mode: str = "keep"
    device: str = "auto"
    allow_t5: bool = False
    prompt: str = ""
    spark: bool = True
    catchup_every: float = 10.0      # precompute catch-ups so replay mode has them
    catchup_seconds: float = 30.0
    catchup_model: str = "spark"
    max_edge: int = 960
    translate: list[str] | None = None
    progress: Callable[[str], None] | None = None
    array_path: Path | None = None
    array_channels: list[int] | None = None


def analyze(video: Path, taps: list[Tap], out: Path, opt: Options) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    report = opt.progress or (lambda step: None)
    report("Preparing the recorded clip")
    calls = CallLog(out, replay=opt.replay)
    analysis = out / "analysis.mp4"
    if not analysis.exists():
        if opt.replay:
            raise FileNotFoundError(f"replay mode needs {analysis}")
        prepare_analysis_video(video, analysis, max_edge=opt.max_edge)
    info = probe(analysis)
    names = [t.name for t in taps]

    tracks_path = out / "tracks.json"
    tracks_request = out / "tracks_request.json"
    tracks = None
    previous = out / "earshot.json"
    expected_taps = [[tap.x, tap.y, tap.frame] for tap in taps]
    cached_taps = None
    if previous.exists():
        prior = json.loads(previous.read_text())
        if names == [p["name"] for p in prior.get("people", [])]:
            cached_taps = [person.get("tap") for person in prior.get("people", [])]
    elif tracks_request.exists():
        request = json.loads(tracks_request.read_text())
        if request.get("names") == names:
            cached_taps = request.get("taps")
    if tracks_path.exists() and cached_taps == expected_taps:
        cached = Tracks.load(tracks_path)
        if (cached.width, cached.height, cached.frames) == (info.width, info.height, info.frames) \
                and cached.fps == info.fps:
            tracks = cached
    if tracks is None:
        report("Tracking people with SAM 3.1")
        tracks = track_people(analysis, taps, info, calls)
        tracks.save(tracks_path)
        tracks_request.write_text(json.dumps({"names": names, "taps": expected_taps}) + "\n")
    else:
        report("Loading cached person tracks")

    mixture = read_audio(analysis, SEPARATION_SR)
    mix24 = resample(mixture, SEPARATION_SR, TRANSCRIBE_SR)
    # Today's captions: one diarized stream for the whole table (also the bench baseline).
    report("Transcribing the group with Muse Voice Transcribe")
    baseline = transcribe(mix24, calls, purpose="diarize the raw mix (today's captions)")

    stems: list[str | None] = [None] * len(names)
    array_metadata = None
    array_baseline = []
    motion_markers, motion_thresholds, motion_protocol = {}, {}, None
    if opt.separator == "array":
        import time

        from .array import delay_and_sum, load_array, separate
        from .corrections import apply_saved_corrections
        from .lite import attribute_with_confidence, gray_frames, head_motion
        from .motion import guide_activities

        if opt.array_path is None:
            raise ValueError("--array PATH is required with --separator array")
        report("Matching diarized voices to faces for the array guide")
        frames = gray_frames(analysis)
        motion = [head_motion(frames, tracks, person) for person in range(len(names))]
        mapping, confidence = attribute_with_confidence(baseline, motion, info.fps)
        corrections_path = out / "corrections.json"
        if corrections_path.exists():
            corrected = {
                "people": [{"name": tap.name, "tap": [tap.x, tap.y, tap.frame]} for tap in taps],
                "captions": [], "activity": [],
                "attribution": {"mapping": mapping, "confidence": confidence},
                "corrections": json.loads(corrections_path.read_text()),
            }
            apply_saved_corrections(corrected)
            mapping, confidence = corrected["attribution"]["mapping"], corrected["attribution"]["confidence"]
        turns = [[Turn(str(person), turn.start, turn.end, turn.text) for turn in baseline
                  if mapping.get(turn.speaker) == person] for person in range(len(names))]
        guides, guide_metadata = guide_activities(turns, motion, info.fps, info.frames)
        audio, _ = load_array(opt.array_path, opt.array_channels)
        report("Separating voices with classical MVDR beamforming")
        started = time.perf_counter()
        separated, mvdr_metadata = separate(audio, guides, info.fps)
        beamforming_seconds = time.perf_counter() - started
        turns, activity = [], []
        for person, name in enumerate(names):
            audio24 = resample(separated[person], 16_000, TRANSCRIBE_SR)
            stem = f"stems/{person}_{_slug(name)}.wav"
            write_wav(out / stem, audio24, TRANSCRIBE_SR)
            stems[person] = stem
            activity.append(speech_segments(audio24, TRANSCRIBE_SR))
            report(f"Transcribing {name}'s voice with Muse Voice Transcribe")
            turns.append(transcribe(audio24, calls, purpose=f"transcribe {name}'s isolated voice"))
        report("Building the GCC-PHAT delay-and-sum baseline")
        all_channels, _ = load_array(opt.array_path)
        delay_sum, delays = delay_and_sum(all_channels)
        delay24 = resample(delay_sum, 16_000, TRANSCRIBE_SR)
        write_wav(out / "array_delay_sum.wav", delay24, TRANSCRIBE_SR)
        delay_turns = transcribe(delay24, calls, purpose="diarize GCC-PHAT delay-and-sum 8-mic baseline")
        array_baseline = [{"speaker": turn.speaker, "start": turn.start, "end": turn.end, "text": turn.text}
                          for turn in delay_turns]
        channels = opt.array_channels or list(range(1, 9))
        separator_name = f"AMI 8-mic meeting-room array MVDR (classical; channels {channels})"
        array_metadata = {
            "source": "AMI 8-mic meeting-room array", "array_path": str(opt.array_path),
            "channels": channels, "source_sample_rate": 16_000, "sample_rate": TRANSCRIBE_SR,
            "delay_sum": "array_delay_sum.wav", "delays": delays,
            "beamforming_seconds": round(beamforming_seconds, 3),
            "analysis_seconds": round(time.perf_counter() - started, 3),
            "guide": guide_metadata, "mvdr": mvdr_metadata, "mapping_source": "runtime-lite",
        }
    elif opt.separator == "samaudio":
        from .separation import SamAudioSeparator

        from .separation import DEFAULT_TEXT_FEATURES

        # Precomputed text conditioning is the default; --allow-t5 runs the permitted local T5 encoder.
        features = None if (opt.allow_t5 and not opt.text_features) else (opt.text_features or DEFAULT_TEXT_FEATURES)
        sep = SamAudioSeparator(description=opt.prompt, text_features=features, allow_t5=opt.allow_t5,
                                mask_mode=opt.mask_mode, device=opt.device)
        report("Separating the tapped voices with SAM Audio")
        if hasattr(sep, "separate_people"):
            separated = sep.separate_people(analysis, mixture, tracks, calls)
        else:
            separated = {person: sep.separate(analysis, mixture, tracks, person, calls)
                         for person in range(len(names))}
        turns, activity = [], []
        for p, name in enumerate(names):
            iso = separated[p]
            stem = f"stems/{p}_{_slug(name)}.wav"
            write_wav(out / stem, iso, SEPARATION_SR)
            stems[p] = stem
            activity.append(speech_segments(resample(iso, SEPARATION_SR, 16_000), 16_000))
            report(f"Transcribing {name}'s voice with Muse Voice Transcribe")
            turns.append(transcribe(resample(iso, SEPARATION_SR, TRANSCRIBE_SR), calls,
                                    purpose=f"transcribe {name}'s isolated voice"))
        separator_name = sep.name
    elif opt.separator == "lite":
        from .lite import attribute_with_confidence, gray_frames, head_motion

        report("Matching voices to faces with Earshot-Lite")
        frames = gray_frames(analysis)
        motion = [head_motion(frames, tracks, p) for p in range(len(names))]
        mapping, confidence = attribute_with_confidence(baseline, motion, info.fps)
        turns = [[Turn(str(p), t.start, t.end, t.text) for t in baseline if mapping.get(t.speaker) == p]
                 for p in range(len(names))]
        activity = [[(t.start, t.end) for t in person_turns] for person_turns in turns]
        separator_name = "none (Earshot-Lite: mouth-motion attribution)"
    elif opt.separator == "spark-av":
        from .sparkav import transcribe_windows

        report("Transcribing overlapping speech with unverified Muse Spark AV")
        turns, activity = transcribe_windows(analysis, taps, baseline, info.duration, calls)
        separator_name = "Muse Spark AV (unverified audiovisual transcription)"
    else:
        raise ValueError(f"unknown separator {opt.separator!r}")

    report("Building per-person captions")
    captions = build_captions(names, turns, activity)
    if opt.separator == "lite":
        from .motion import (
            MIN_EVENT_SECONDS,
            MOTION_MAD_MULTIPLIER,
            MOTION_NOISE_FLOOR,
            MOTION_SMOOTH_SECONDS,
            talked_over,
        )

        motion_markers, motion_thresholds = talked_over(captions, turns, motion, info.fps)
        motion_protocol = {
            "noise_floor": MOTION_NOISE_FLOOR, "mad_multiplier": MOTION_MAD_MULTIPLIER,
            "smooth_seconds": MOTION_SMOOTH_SECONDS, "min_event_seconds": MIN_EVENT_SECONDS,
        }
    if opt.spark and captions:
        report("Grouping conversations with Muse Spark")
    threads = assign_threads(captions, calls) if opt.spark and captions else []
    board = check_board_items([], captions, names)
    if opt.spark and captions:
        report("Checking questions and commitments against their cited captions")
        board = build_board(captions, names, calls, model=opt.catchup_model)
    catchups = []
    if opt.spark and captions and opt.catchup_every > 0:
        report(f"Preparing cited catch-ups with {'Muse Glimmer' if opt.catchup_model == 'glimmer' else 'Muse Spark'}")
        t = opt.catchup_every
        while t <= info.duration + 1e-6:
            for person in [None, *range(len(names))]:
                res = catch_up(captions, names, t, opt.catchup_seconds, calls, person=person,
                               model=opt.catchup_model)
                catchups.append({"t": round(t, 2), "person": person, **res})
            t += opt.catchup_every

    from .quality import array_quality
    from .spark import translate_captions

    translations, translation_status, translation_segments = {}, {}, {}
    for language in opt.translate or []:
        report(f"Translating captions to {language} with Muse Spark")
        translations[language], translation_status[language] = translate_captions(captions, language, calls)
        translation_segments[language] = {
            caption.id: sentence_segments(translations[language][caption.id], caption.start, caption.end, caption.id)
            for caption in captions if caption.id in translations[language]
        }

    doc = {
        "video": "analysis.mp4",
        "info": {"width": info.width, "height": info.height, "fps": info.fps, "duration": info.duration},
        "separator": separator_name,
        "people": [{"name": n, "color": COLORS[p % len(COLORS)], "stem": stems[p],
                    "anchors": tracks.anchors(p), "tap": [taps[p].x, taps[p].y, taps[p].frame]}
                   for p, n in enumerate(names)],
        "captions": [c.to_json() for c in captions],
        "baseline": [{"speaker": t.speaker, "start": t.start, "end": t.end, "text": t.text} for t in baseline],
        "activity": activity,
        "overlaps": overlap_windows(activity),
        "attribution": {"mapping": mapping if opt.separator in ("lite", "array") else {},
                        "confidence": confidence if opt.separator in ("lite", "array") else {}},
        "threads": threads,
        "catchups": catchups,
        "catchup_model": opt.catchup_model,
        "board": board,
        "translations": translations,
        "translation_status": translation_status,
        "translation_segments": translation_segments,
        "talked_over": motion_markers,
        "motion_thresholds": motion_thresholds,
        "motion_protocol": motion_protocol,
        "array": array_metadata,
        "array_baseline": array_baseline,
        "quality": array_quality(out) if opt.separator == "array" else None,
    }
    (out / "earshot.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    _install_viewer(out)
    return out / "earshot.json"


def _slug(name: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in name.lower()).strip("_") or "person"


def _install_viewer(out: Path) -> None:
    src = Path(__file__).resolve().parent.parent / "web" / "index.html"
    if src.exists():
        shutil.copyfile(src, out / "index.html")


def load_tracks(run: Path) -> Tracks:
    return Tracks.load(run / "tracks.json")
