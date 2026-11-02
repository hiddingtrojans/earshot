"""Voice separation: one isolated track per tapped person.

`SamAudioSeparator` runs Meta's SAM Audio locally with the person's SAM 3.1 masks
as its visual prompt. Compliance choices, from reading SAM Audio's source:

* re-rankers (CLAP + judge, ImageBind) and the span predictor are switched off
  through config overrides, so they are never built (CLAP is not a Meta model);
* SAM Audio conditions on text through a frozen Google T5-base encoder. The
  default uses precomputed encoder outputs for our fixed prompts instead of
  loading T5. The organizers allow `--allow-t5`, which runs T5-base locally.

`MixtureSeparator` is Earshot-Lite: no separation; attribution happens in
`lite.py` from mouth movement instead.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .calls import CallLog, content_key
from .media import SEPARATION_SR
from .tracking import Tracks

DEFAULT_MODEL = os.environ.get("EARSHOT_SAM_AUDIO", "facebook/sam-audio-small-tv")
DEFAULT_TEXT_FEATURES = Path(__file__).resolve().parent.parent / "assets" / "text_features.npz"


def crossfade_windows(total: int, window: int, overlap: int) -> list[tuple[int, int]]:
    if total <= window:
        return [(0, total)]
    step = window - overlap
    starts = list(range(0, max(1, total - overlap), step))
    out = [(s, min(total, s + window)) for s in starts]
    if out[-1][1] < total:
        out.append((max(0, total - window), total))
    return out


def overlap_add(chunks: list[tuple[int, np.ndarray]], total: int, overlap: int) -> np.ndarray:
    """Linear crossfade of overlapping chunks into one signal."""
    out = np.zeros(total, dtype=np.float64)
    weight = np.zeros(total, dtype=np.float64)
    for i, (start, chunk) in enumerate(chunks):
        n = chunk.size
        w = np.ones(n)
        ramp = min(overlap, n // 2)
        if i > 0 and ramp:
            w[:ramp] = np.linspace(1e-3, 1.0, ramp)
        if i < len(chunks) - 1 and ramp:
            w[-ramp:] = np.linspace(1.0, 1e-3, ramp)
        out[start:start + n] += chunk * w
        weight[start:start + n] += w
    return (out / np.maximum(weight, 1e-6)).astype(np.float32)


class MixtureSeparator:
    """Earshot-Lite: every person gets the mixture; attribution is done by lite.py."""

    name = "none (Earshot-Lite)"

    def separate(self, video: Path, mixture: np.ndarray, tracks: Tracks, person: int, calls: CallLog) -> np.ndarray:
        return mixture


@dataclass
class SamAudioSeparator:
    model_id: str = DEFAULT_MODEL
    device: str = "auto"
    description: str = ""          # "" = visual prompt only; e.g. "speech" to combine
    window_s: float = 10.0
    overlap_s: float = 1.0
    work_width: int = 640
    text_features: Path | None = DEFAULT_TEXT_FEATURES
    allow_t5: bool = False         # precomputed output by default; true runs T5-base locally
    seed: int = 0

    name = "SAM Audio (local)"

    def __post_init__(self) -> None:
        self._model = self._processor = None
        if self.text_features is None and not self.allow_t5:
            raise ValueError(
                "Choose SAM Audio text conditioning: pass precomputed text_features "
                "(the default), or set allow_t5=True to run frozen T5-base locally (allowed by organizers).")

    # ---------- model ----------
    def _load(self):
        if self._model is not None:
            return
        os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
        import torch

        if self.text_features is not None:
            _install_cached_text_encoder(Path(self.text_features))
        from sam_audio import SAMAudio, SAMAudioProcessor

        if self.device == "auto":
            self.device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
        model = SAMAudio.from_pretrained(self.model_id, text_ranker=None, visual_ranker=None, span_predictor=None)
        self._model = model.eval().to(self.device)
        self._processor = SAMAudioProcessor.from_pretrained(self.model_id)

    # ---------- separation ----------
    def separate(self, video: Path, mixture: np.ndarray, tracks: Tracks, person: int, calls: CallLog) -> np.ndarray:
        mask_digest = hashlib.sha256(
            b"".join(tracks.regions[person][f][4] for f in sorted(tracks.regions[person]))
        ).hexdigest()
        key = (content_key(mixture.tobytes()), mask_digest, self.description, self.window_s,
               self.overlap_s, self.work_width, self.seed, bool(self.text_features))
        out_holder: dict = {}

        def run():
            audio = self._separate_uncached(video, mixture, tracks, person)
            name = f"sep_{content_key(*key)}.npy"
            np.save(calls.calls_dir / name, audio)
            out_holder["audio"] = audio
            return {"npy": name, "device": self.device}, {"device": self.device, "person": tracks.names[person]}

        res = calls.cached(model=self.model_id, purpose=f"isolate {tracks.names[person]}'s voice",
                           where="local", key_parts=key, fn=run)
        return out_holder.get("audio", np.load(calls.calls_dir / res["npy"]))

    def _separate_uncached(self, video: Path, mixture: np.ndarray, tracks: Tracks, person: int) -> np.ndarray:
        import torch
        import torch.nn.functional as F
        from torchcodec.decoders import VideoDecoder

        self._load()
        torch.manual_seed(self.seed)
        sr, fps = SEPARATION_SR, tracks.fps
        decoder = VideoDecoder(str(video), dimension_order="NCHW")
        n_frames = min(len(decoder), tracks.frames or len(decoder))
        windows = crossfade_windows(mixture.size, int(self.window_s * sr), int(self.overlap_s * sr))
        chunks = []
        for s0, s1 in windows:
            f0 = int(s0 / sr * fps)
            f1 = max(f0 + 1, min(n_frames, int(np.ceil(s1 / sr * fps))))
            masks = tracks.masks(person, f0, f1)
            if not masks.any():  # person not visible: nothing to isolate here
                chunks.append((s0, np.zeros(s1 - s0, dtype=np.float32)))
                continue
            frames = decoder.get_frames_in_range(f0, f1).data  # (n, 3, H, W) uint8
            h = int(round(frames.shape[2] * self.work_width / frames.shape[3] / 2) * 2)
            frames = F.interpolate(frames.float(), size=(h, self.work_width), mode="bilinear",
                                   antialias=True).round().clamp(0, 255).to(torch.uint8)
            m = torch.from_numpy(masks[:, None].astype(np.float32))
            m = F.interpolate(m, size=(h, self.work_width), mode="nearest").bool()
            audio = torch.from_numpy(mixture[s0:s1]).unsqueeze(0)
            batch = self._processor(
                audios=[audio], descriptions=[self.description],
                masked_videos=self._processor.mask_videos([frames], [m]),
            ).to(self.device)
            with torch.inference_mode():
                result = self._model.separate(batch, predict_spans=False, reranking_candidates=1)
            target = result.target[0].detach().float().cpu().numpy().reshape(-1)[: s1 - s0]
            if target.size < s1 - s0:
                target = np.pad(target, (0, s1 - s0 - target.size))
            chunks.append((s0, target))
        return overlap_add(chunks, mixture.size, int(self.overlap_s * sr))


# --------------------------------------------------------------------------- #
# Optional: precomputed text conditioning (no T5 at runtime)
# --------------------------------------------------------------------------- #
def _install_cached_text_encoder(path: Path) -> None:
    """Replace SAM Audio's T5 text encoder with a lookup of precomputed outputs."""
    import sam_audio.model.model as sam_model

    sam_model.T5TextEncoder = cached_text_encoder_class(path)


def cached_text_encoder_class(path: Path):
    import torch

    data = np.load(path, allow_pickle=False)
    table = {str(k): data[k] for k in data.files}

    class CachedTextEncoder(torch.nn.Module):
        def __init__(self, cfg=None):
            super().__init__()
            self.register_buffer("_device_probe", torch.zeros(1), persistent=False)

        def _load_from_state_dict(self, state_dict, prefix, *args, **kwargs):
            return  # no T5 weights here; ignore any stored under this prefix

        def forward(self, texts: list[str]):
            missing = [t for t in texts if f"feat::{t}" not in table]
            if missing:
                raise KeyError(f"no precomputed text features for {missing}; run tools/precompute_text_features.py")
            feats = [torch.from_numpy(table[f"feat::{t}"]) for t in texts]
            length = max(f.shape[0] for f in feats)
            dim = feats[0].shape[1]
            out = torch.zeros(len(texts), length, dim)
            mask = torch.zeros(len(texts), length, dtype=torch.bool)
            for i, f in enumerate(feats):
                out[i, : f.shape[0]] = f
                mask[i, : f.shape[0]] = True
            dev = self._device_probe.device
            return out.to(dev), mask.to(dev)

    return CachedTextEncoder
