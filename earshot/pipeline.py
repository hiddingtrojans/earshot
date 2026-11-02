"""End-to-end analysis of one video into a run folder the viewer can play."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from .activity import overlap_windows, speech_segments
from .calls import CallLog
from .media import SEPARATION_SR, TRANSCRIBE_SR, prepare_analysis_video, probe, read_audio, resample, write_wav
from .spark import assign_threads, catch_up
from .timeline import build_captions
from .tracking import Tap, Tracks, track_people
from .transcribe import Turn, transcribe

COLORS = ["#E4572E", "#2E86AB", "#7BAE37", "#9B5DE5", "#F2A541", "#17BEBB"]


@dataclass
class Options:
    separator: str = "samaudio"      # "samaudio" | "lite"
    replay: bool = False
    text_features: Path | None = None   # None = repo default (assets/text_features.npz)
    allow_t5: bool = False
    prompt: str = ""
    spark: bool = True
    catchup_every: float = 10.0      # precompute catch-ups so replay mode has them
    catchup_seconds: float = 30.0
    max_edge: int = 960


def analyze(video: Path, taps: list[Tap], out: Path, opt: Options) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    calls = CallLog(out, replay=opt.replay)
    analysis = out / "analysis.mp4"
    if not analysis.exists():
        if opt.replay:
            raise FileNotFoundError(f"replay mode needs {analysis}")
        prepare_analysis_video(video, analysis, max_edge=opt.max_edge)
    info = probe(analysis)
    names = [t.name for t in taps]

    tracks_path = out / "tracks.json"
    tracks = None
    previous = out / "earshot.json"
    if tracks_path.exists() and previous.exists():
        prior = json.loads(previous.read_text())
        prior_taps = [person.get("tap") for person in prior.get("people", [])]
        expected_taps = [[tap.x, tap.y, tap.frame] for tap in taps]
        if prior_taps == expected_taps and prior.get("people", []) and names == [p["name"] for p in prior["people"]]:
            cached = Tracks.load(tracks_path)
            if (cached.width, cached.height, cached.frames) == (info.width, info.height, info.frames) \
                    and cached.fps == info.fps:
                tracks = cached
    if tracks is None:
        tracks = track_people(analysis, taps, info, calls)
        tracks.save(tracks_path)

    mixture = read_audio(analysis, SEPARATION_SR)
    mix24 = resample(mixture, SEPARATION_SR, TRANSCRIBE_SR)
    # Today's captions: one diarized stream for the whole table (also the bench baseline).
    baseline = transcribe(mix24, calls, purpose="diarize the raw mix (today's captions)")

    stems: list[str | None] = [None] * len(names)
    if opt.separator == "samaudio":
        from .separation import SamAudioSeparator

        from .separation import DEFAULT_TEXT_FEATURES

        # Default: precomputed text conditioning, so T5 never runs. --allow-t5 alone runs SAM Audio as released.
        features = None if (opt.allow_t5 and not opt.text_features) else (opt.text_features or DEFAULT_TEXT_FEATURES)
        sep = SamAudioSeparator(description=opt.prompt, text_features=features, allow_t5=opt.allow_t5)
        turns, activity = [], []
        for p, name in enumerate(names):
            iso = sep.separate(analysis, mixture, tracks, p, calls)
            stem = f"stems/{p}_{_slug(name)}.wav"
            write_wav(out / stem, iso, SEPARATION_SR)
            stems[p] = stem
            activity.append(speech_segments(resample(iso, SEPARATION_SR, 16_000), 16_000))
            turns.append(transcribe(resample(iso, SEPARATION_SR, TRANSCRIBE_SR), calls,
                                    purpose=f"transcribe {name}'s isolated voice"))
        separator_name = sep.name
    elif opt.separator == "lite":
        from .lite import attribute_turns, gray_frames, head_motion

        frames = gray_frames(analysis)
        motion = [head_motion(frames, tracks, p) for p in range(len(names))]
        mapping = attribute_turns(baseline, motion, info.fps)
        turns = [[Turn(str(p), t.start, t.end, t.text) for t in baseline if mapping.get(t.speaker) == p]
                 for p in range(len(names))]
        activity = [[(t.start, t.end) for t in person_turns] for person_turns in turns]
        separator_name = "none (Earshot-Lite: mouth-motion attribution)"
    else:
        raise ValueError(f"unknown separator {opt.separator!r}")

    captions = build_captions(names, turns, activity)
    threads = assign_threads(captions, calls) if opt.spark and captions else []
    catchups = []
    if opt.spark and captions and opt.catchup_every > 0:
        t = opt.catchup_every
        while t <= info.duration + 1e-6:
            for person in [None, *range(len(names))]:
                res = catch_up(captions, names, t, opt.catchup_seconds, calls, person=person)
                catchups.append({"t": round(t, 2), "person": person, **res})
            t += opt.catchup_every

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
        "threads": threads,
        "catchups": catchups,
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
