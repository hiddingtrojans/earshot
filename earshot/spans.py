"""Experimental SAM Audio span prompting from runtime diarization and Lite attribution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .bench import oracle_speaker_mapping
from .calls import CallLog, content_key
from .corrections import apply_saved_corrections
from .media import SEPARATION_SR
from .separation import (
    DEFAULT_TEXT_FEATURES,
    SamAudioSeparator,
    apply_mask_mode,
    crossfade_windows,
    overlap_add,
)
from .tracking import Tracks
from .transcribe import Turn

Span = tuple[float, float]
Anchor = tuple[str, float, float]
SILENCE_S = 0.25
MIN_SPAN_S = 0.5


def union_spans(spans: list[Span]) -> list[Span]:
    out: list[Span] = []
    for start, end in sorted(spans):
        if end <= start:
            continue
        if out and start <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], end))
        else:
            out.append((start, end))
    return out


def subtract_spans(own: list[Span], others: list[Span], minimum: float = MIN_SPAN_S) -> list[Span]:
    pieces = []
    for start, end in own:
        remaining = [(start, end)]
        for block_start, block_end in others:
            next_remaining = []
            for left, right in remaining:
                if block_end <= left or block_start >= right:
                    next_remaining.append((left, right))
                    continue
                if block_start > left:
                    next_remaining.append((left, min(right, block_start)))
                if block_end < right:
                    next_remaining.append((max(left, block_end), right))
            remaining = next_remaining
        pieces.extend(remaining)
    return [(start, end) for start, end in sorted(pieces) if end - start >= minimum]


def solo_spans(turns: list[Turn], mapping: dict[str, int], people: int, duration: float) -> list[list[Span]]:
    labels = {turn.speaker for turn in turns}
    if labels != set(mapping):
        raise ValueError(f"Attribution must cover every diarized label: {sorted(labels)} versus {sorted(mapping)}")
    out: list[list[Span]] = [[] for _ in range(people)]
    for label in sorted(labels):
        own = union_spans([(max(0.0, turn.start), min(duration, turn.end))
                           for turn in turns if turn.speaker == label])
        others = union_spans([(max(0.0, turn.start), min(duration, turn.end))
                              for turn in turns if turn.speaker != label])
        person = mapping[label]
        out[person] = union_spans(out[person] + subtract_spans(own, others))
    return out


def select_enrollment(spans: list[Span], budget_s: float) -> list[Span]:
    selected = []
    remaining = budget_s
    for start, end in sorted(spans, key=lambda span: (-(span[1] - span[0]), span[0])):
        if remaining <= 0:
            break
        length = min(end - start, remaining)
        if length > 0:
            selected.append((start, start + length))
            remaining -= length
    return selected


def _source_audio(mixture: np.ndarray, sources: list[dict], sr: int) -> np.ndarray:
    pieces = [mixture[int(round(source["start"] * sr)):int(round(source["end"] * sr))]
              for source in sources]
    return np.concatenate(pieces) if pieces else mixture[:0]


def build_window_plan(mixture: np.ndarray, solo: list[list[Span]], person: int,
                      start: int, end: int, sr: int = SEPARATION_SR) -> dict:
    target_sources = [{"person": person, "sign": "+", "start": a, "end": b}
                      for a, b in select_enrollment(solo[person], 4.0)]
    other_sources = []
    others = [index for index in range(len(solo)) if index != person]
    for other in others:
        budget = 4.0 / len(others)
        other_sources.extend({"person": other, "sign": "-", "start": a, "end": b}
                             for a, b in select_enrollment(solo[other], budget))
    target_audio = _source_audio(mixture, target_sources, sr)
    other_audio = _source_audio(mixture, other_sources, sr)
    silence = int(round(SILENCE_S * sr))
    offset = target_audio.size + silence + other_audio.size + silence
    anchors: list[Anchor] = []
    if target_audio.size:
        anchors.append(("+", 0.0, target_audio.size / sr))
    cursor = target_audio.size + silence
    for other in others:
        sources = [source for source in other_sources if source["person"] == other]
        size = _source_audio(mixture, sources, sr).size
        if size:
            anchors.append(("-", cursor / sr, (cursor + size) / sr))
        cursor += size
    window_start, window_end = start / sr, end / sr
    for owner, sign in [(person, "+")] + [(other, "-") for other in others]:
        for a, b in solo[owner]:
            left, right = max(a, window_start), min(b, window_end)
            if right - left < MIN_SPAN_S:
                continue
            anchors.append((sign, (offset / sr) + left - window_start,
                            (offset / sr) + right - window_start))
    anchors.sort(key=lambda anchor: (anchor[1], anchor[2], anchor[0]))
    return {
        "person": person, "window": [window_start, window_end],
        "sources": target_sources + other_sources, "anchors": anchors,
        "offset_samples": offset,
    }


def window_audio(mixture: np.ndarray, plan: dict, sr: int = SEPARATION_SR) -> np.ndarray:
    target = _source_audio(mixture, [s for s in plan["sources"] if s["sign"] == "+"], sr)
    others = _source_audio(mixture, [s for s in plan["sources"] if s["sign"] == "-"], sr)
    silence = np.zeros(int(round(SILENCE_S * sr)), dtype=mixture.dtype)
    start, end = [int(round(value * sr)) for value in plan["window"]]
    audio = np.concatenate([target, silence, others, silence, mixture[start:end]])
    assert audio.size == plan["offset_samples"] + end - start
    return audio


def build_plans(mixture: np.ndarray, turns: list[Turn], mapping: dict[str, int], people: int,
                window_s: float = 10.0, overlap_s: float = 1.0,
                sr: int = SEPARATION_SR) -> tuple[dict[int, dict[int, dict]], list[list[Span]]]:
    solo = solo_spans(turns, mapping, people, mixture.size / sr)
    windows = crossfade_windows(mixture.size, int(window_s * sr), int(overlap_s * sr))
    plans = {person: {start: build_window_plan(mixture, solo, person, start, end, sr)
                      for start, end in windows} for person in range(people)}
    return plans, solo


def runtime_attribution(run: Path, mapping_kind: str = "auto", truth_path: Path | None = None):
    from .lite import attribute_with_confidence, gray_frames, head_motion

    doc = json.loads((run / "earshot.json").read_text())
    turns = [Turn(str(item["speaker"]), item["start"], item["end"], item["text"]) for item in doc["baseline"]]
    names = [person["name"] for person in doc["people"]]
    if mapping_kind == "oracle":
        if truth_path is None:
            raise ValueError("oracle evaluation needs the truth file")
        truth = json.loads(truth_path.read_text())
        oracle = oracle_speaker_mapping(doc["baseline"], truth["people"])
        indexes = {name: index for index, name in enumerate(names)}
        mapping = {label: indexes[name] for label, name in oracle.items()}
        confidence = {}
    elif mapping_kind == "auto":
        tracks = Tracks.load(run / "tracks.json")
        frames = gray_frames(run / doc["video"])
        motion = [head_motion(frames, tracks, person) for person in range(len(names))]
        mapping, confidence = attribute_with_confidence(turns, motion, tracks.fps)
    else:
        raise ValueError(f"unknown mapping kind {mapping_kind!r}")
    corrections_path = run / "corrections.json"
    if corrections_path.exists():
        corrected = {
            "people": doc["people"], "captions": [], "activity": [],
            "attribution": {"mapping": mapping, "confidence": confidence},
            "corrections": json.loads(corrections_path.read_text()),
        }
        apply_saved_corrections(corrected)
        mapping = corrected["attribution"]["mapping"]
        confidence = corrected["attribution"]["confidence"]
    return turns, mapping, confidence, names


@dataclass
class SpanAudioSeparator(SamAudioSeparator):
    turns: list[Turn] = field(default_factory=list)
    mapping: dict[str, int] = field(default_factory=dict)
    span_mode: str = "spans-text"
    mapping_source: str = "runtime-lite"
    clip_seconds: float | None = None
    description: str = "speech"

    name = "SAM Audio span-prompting experiment (local)"

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.span_mode not in ("spans-text", "spans-video"):
            raise ValueError(f"unknown span mode {self.span_mode!r}")
        if self.description != "speech":
            raise ValueError("span experiments use the precomputed 'speech' description")
        self._plans = None
        self._video_prefixes = {}

    def separate_people(self, video: Path, mixture: np.ndarray, tracks: Tracks, calls: CallLog,
                        people: list[int] | None = None) -> dict[int, np.ndarray]:
        people = list(range(len(tracks.names))) if people is None else people
        self._plans, self._solo = build_plans(mixture, self.turns, self.mapping, len(tracks.names),
                                              self.window_s, self.overlap_s)
        mask_digest = hashlib.sha256(b"".join(
            tracks.regions[person][f][4] for person in people for f in sorted(tracks.regions[person])
        )).hexdigest()
        signature = {
            "span_mode": self.span_mode,
            "mapping": self.mapping,
            "plans": {str(person): [self._plans[person][start] for start in sorted(self._plans[person])]
                      for person in people},
        }
        key = (content_key(mixture.tobytes()), mask_digest, self.description, self.window_s,
               self.overlap_s, self.work_width, self.seed, self.mask_mode, self.span_mode,
               bool(self.text_features), tuple(people), self.clip_seconds, content_key(signature))
        out_holder: dict[int, np.ndarray] = {}

        def run():
            audio, timings, batching, errors = self._separate_uncached(video, mixture, tracks, people)
            if self.clip_seconds is not None:
                audio = {person: samples[:int(self.clip_seconds * SEPARATION_SR)]
                         for person, samples in audio.items()}
            stems = {}
            for person, samples in audio.items():
                name = f"sep_{content_key(*key, person)}.npy"
                np.save(calls.calls_dir / name, samples)
                stems[str(person)] = name
            out_holder.update(audio)
            return {"stems": stems, "timings_ms": timings, "batching": batching, "errors": errors}, {
                "device": self.device, "timings_ms": timings, "batching": batching,
                "span_mode": self.span_mode, "mapping_source": self.mapping_source,
                "anchor_digest": content_key(signature),
            }

        result = calls.cached(model=self.model_id, purpose=f"isolate tapped voices with {self.span_mode}",
                              where="local", key_parts=key, fn=run)
        return {person: out_holder.get(person, np.load(calls.calls_dir / result["stems"][str(person)]))
                for person in people}

    def _window_inputs(self, video: Path, tracks: Tracks, mixture: np.ndarray, frames, masks,
                       person: int, start: int):
        import torch
        import torch.nn.functional as F
        from torchcodec.decoders import VideoDecoder

        plan = self._plans[person][start]
        audio = torch.from_numpy(window_audio(mixture, plan)).unsqueeze(0)
        if self.span_mode == "spans-text":
            return audio, None, plan["anchors"], plan["offset_samples"]
        if person not in self._video_prefixes:
            height, width = frames.shape[2], frames.shape[3]
            decoder = VideoDecoder(str(video), dimension_order="NCHW")
            parts = []
            current_sign = None
            for source in plan["sources"]:
                if source["sign"] == "-" and current_sign != "-":
                    parts.append(torch.zeros(int(round(SILENCE_S * tracks.fps)), 3, height, width,
                                             dtype=torch.uint8))
                current_sign = source["sign"]
                owner = source["person"]
                f0 = int(round(source["start"] * tracks.fps))
                f1 = max(f0 + 1, int(round(source["end"] * tracks.fps)))
                source_frames = decoder.get_frames_in_range(f0, f1).data
                source_frames = F.interpolate(source_frames.float(), size=(height, width), mode="bilinear",
                                              antialias=True).round().clamp(0, 255).to(torch.uint8)
                source_masks = torch.from_numpy(tracks.masks(owner, f0, f1)[:, None].astype(np.float32))
                source_masks = F.interpolate(source_masks, size=(height, width), mode="nearest").bool()
                parts.append(apply_mask_mode(self._processor, [source_frames], [source_masks], "keep")[0])
            parts.append(torch.zeros(int(round(SILENCE_S * tracks.fps)), 3, height, width, dtype=torch.uint8))
            self._video_prefixes[person] = torch.cat(parts)
        masked = apply_mask_mode(self._processor, [frames], masks, "keep")[0]
        return audio, torch.cat([self._video_prefixes[person], masked]), plan["anchors"], plan["offset_samples"]

    def _separate_uncached(self, video: Path, mixture: np.ndarray, tracks: Tracks, people: list[int]):
        import gc
        import time

        import torch
        import torch.nn.functional as F
        from torchcodec.decoders import VideoDecoder

        self._load()
        torch.manual_seed(self.seed)
        if self.device == "mps" and len(people) > 1:
            audio, timings, errors = {}, {}, []
            for person in people:
                one_audio, one_timings, _, one_errors = self._separate_uncached(video, mixture, tracks, [person])
                audio.update(one_audio)
                timings.update(one_timings)
                errors.extend(one_errors)
            return audio, timings, "per-person (MPS batch stall avoided)", errors
        sr, fps = SEPARATION_SR, tracks.fps
        decoder = VideoDecoder(str(video), dimension_order="NCHW")
        n_frames = min(len(decoder), tracks.frames or len(decoder))
        windows = crossfade_windows(mixture.size, int(self.window_s * sr), int(self.overlap_s * sr))
        if self.clip_seconds is not None:
            windows = [(0, min(mixture.size, int(self.clip_seconds * sr)))]
        chunks = {person: [] for person in people}
        timings = {str(person): 0.0 for person in people}
        batching, errors = "batched", []
        for start, end in windows:
            f0 = int(start / sr * fps)
            f1 = max(f0 + 1, min(n_frames, int(np.ceil(end / sr * fps))))
            frames = decoder.get_frames_in_range(f0, f1).data
            height = int(round(frames.shape[2] * self.work_width / frames.shape[3] / 2) * 2)
            frames = F.interpolate(frames.float(), size=(height, self.work_width), mode="bilinear",
                                   antialias=True).round().clamp(0, 255).to(torch.uint8)
            masks = [torch.from_numpy(tracks.masks(person, f0, f1)[:, None].astype(np.float32))
                     for person in people]
            masks = [F.interpolate(mask, size=(height, self.work_width), mode="nearest").bool() for mask in masks]
            inputs = [self._window_inputs(video, tracks, mixture, frames, [masks[index]], person, start)
                      for index, person in enumerate(people)]
            window_started = time.perf_counter()
            try:
                audios, videos, anchors, offsets = zip(*inputs)
                batch = self._processor(audios=list(audios), descriptions=[self.description] * len(people),
                                        anchors=list(anchors),
                                        masked_videos=None if videos[0] is None else list(videos)).to(self.device)
                started = time.perf_counter()
                with torch.inference_mode():
                    result = self._model.separate(batch, predict_spans=False, reranking_candidates=1)
                elapsed = time.perf_counter() - started
                for index, person in enumerate(people):
                    timings[str(person)] += elapsed / len(people)
                    offset = offsets[index]
                    size = end - start
                    target = result.target[index].detach().float().cpu().numpy().reshape(-1)[offset:offset + size]
                    if target.size < size:
                        target = np.pad(target, (0, size - target.size))
                    chunks[person].append((start, target))
            except Exception as error:
                if len(people) == 1:
                    raise
                batching = "fallback"
                errors.append(f"{type(error).__name__}: {error}"[:300])
                for index, person in enumerate(people):
                    audio, masked, anchors, offset = inputs[index]
                    batch = self._processor(audios=[audio], descriptions=[self.description],
                                            anchors=[anchors],
                                            masked_videos=None if masked is None else [masked]).to(self.device)
                    started = time.perf_counter()
                    with torch.inference_mode():
                        result = self._model.separate(batch, predict_spans=False, reranking_candidates=1)
                    timings[str(person)] += time.perf_counter() - started
                    size = end - start
                    target = result.target[0].detach().float().cpu().numpy().reshape(-1)[offset:offset + size]
                    if target.size < size:
                        target = np.pad(target, (0, size - target.size))
                    chunks[person].append((start, target))
            gc.collect()
            if self.device == "mps":
                torch.mps.empty_cache()
            print(f"{self.span_mode} device={self.device} people={people} window {start/sr:.0f}-{end/sr:.0f}s "
                  f"total={time.perf_counter() - window_started:.1f}s", flush=True)
        audio = {person: overlap_add(chunks[person], mixture.size, int(self.overlap_s * sr))
                 for person in people}
        timings = {person: round(milliseconds * 1000) for person, milliseconds in timings.items()}
        return audio, timings, batching, errors


def plan_document(separator: SpanAudioSeparator) -> dict:
    return {
        "span_mode": separator.span_mode, "mapping": separator.mapping,
        "mapping_source": separator.mapping_source,
        "solo_spans": {str(person): spans for person, spans in enumerate(separator._solo)},
        "plans": {str(person): [separator._plans[person][start]
                                for start in sorted(separator._plans[person])]
                  for person in separator._plans},
    }
