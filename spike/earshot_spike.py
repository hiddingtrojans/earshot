#!/usr/bin/env python3
"""Earshot go/no-go spike: can SAM Audio pull one visible speaker out of a mix
on this Mac, how fast, and how well?

Subcommands
-----------
compose   Build a test clip WITH ground truth from two separate recordings
          (e.g. you, filmed twice in two seats). Puts them side by side and
          mixes their audio, keeping each clean track as a reference.

run       Cut a short window from a video, mask one speaker with a box, run
          SAM Audio visual prompting, a text-only baseline ("speech") and an
          optional silent-region control. Times everything and, if you pass a
          reference track, scores separation quality (SI-SDR).

Typical morning
---------------
  # 1. Ground-truth clip from two takes (left seat, right seat), ~20 s each
  python earshot_spike.py compose --left take_left.mp4 --right take_right.mp4 --out spike/

  # 2. Isolate the left person (box = left half), score against the clean track
  python earshot_spike.py run --video spike/mix.mp4 --box 0 0 0.5 1 \
      --ref spike/ref_left.wav --seconds 10 --out spike/run_left

  # 3. Same for the right person
  python earshot_spike.py run --video spike/mix.mp4 --box 0.5 0 1 1 \
      --ref spike/ref_right.wav --seconds 10 --out spike/run_right

  # 4. A real clip with two people talking over each other (no reference)
  python earshot_spike.py run --video kitchen.mp4 --box 0.05 0.1 0.45 0.95 \
      --control-box 0.8 0 1 0.3 --start 12 --seconds 10 --out spike/real

  Then LISTEN to target_visual.wav vs mixture.wav. The numbers help; your ears decide.

GO if: the target voice is clearly the dominant one, the other voice is clearly
quieter, and the visual run takes at most ~3x the clip length (rtf <= 3).

Setup (macOS, Apple Silicon)
----------------------------
  brew install ffmpeg      # torchcodec needs FFmpeg's shared libraries
                           # (if torchcodec can't load it: brew install ffmpeg@7)
  uv venv -p 3.11 .venv && source .venv/bin/activate
  uv pip install torch torchaudio torchvision torchcodec "transformers>=4.54" \
      einops torchdiffeq numpy huggingface_hub safetensors timm ftfy regex \
      sentencepiece pydub
  uv pip install "git+https://github.com/facebookresearch/dacvae.git"
  # --no-deps: perception_models' requirements pull decord and xformers, which
  # have no macOS arm64 wheels and aren't needed for SAM Audio inference.
  uv pip install --no-deps "git+https://github.com/facebookresearch/perception_models@unpin-deps"
  # --no-deps: skips laion-clap (a non-Meta model, only used by an optional
  # re-ranker) and imagebind. This script disables the re-rankers and checks
  # that neither was imported.
  uv pip install --no-deps "git+https://github.com/facebookresearch/sam-audio.git"
  hf auth login            # after access to facebook/sam-audio-small-tv is granted

Compliance notes (hackathon rule: every runtime model must be a Meta model)
---------------------------------------------------------------------------
* Re-rankers (CLAP + judge for text, ImageBind for visual) and the span
  predictor are switched off via config overrides, so they are never built.
* SAM Audio's own text conditioning runs Google's T5-base encoder on every
  call (sam_audio/model/text_encoder.py), even for visual prompts. That is an
  open question for the organizers; the report flags it.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import time
import wave
from pathlib import Path

import numpy as np

SR = 48_000  # SAM Audio works at 48 kHz
WORK_WIDTH = 640  # frames are downscaled before masking to keep memory sane
WORK_FPS = 25


# --------------------------------------------------------------------------- #
# ffmpeg helpers (plain signal processing, no models)
# --------------------------------------------------------------------------- #
def ffmpeg(*args: str) -> None:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args]
    subprocess.run(cmd, check=True)


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return float(out)


def has_audio(path: Path) -> bool:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a",
         "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return bool(out)


def read_audio(path: Path, start: float | None = None, seconds: float | None = None) -> np.ndarray:
    """Decode any audio/video file to mono float32 at 48 kHz via ffmpeg."""
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
    if start is not None:
        cmd += ["-ss", f"{start}"]
    if seconds is not None:
        cmd += ["-t", f"{seconds}"]
    cmd += ["-i", str(path), "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def write_wav(path: Path, audio: np.ndarray, sr: int = SR) -> None:
    """16-bit PCM mono WAV with the standard library (no extra deps)."""
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 1.0:  # avoid clipping; level differences are reported separately
        audio = audio / peak
    pcm = (np.clip(audio, -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def to_transcribe_wav(src: Path, dst: Path) -> None:
    """Mono 16-bit 16 kHz copy, the format Muse Voice Transcribe's file endpoint takes."""
    ffmpeg("-i", str(src), "-ac", "1", "-ar", "16000", "-sample_fmt", "s16", str(dst))


# --------------------------------------------------------------------------- #
# Metrics (deterministic)
# --------------------------------------------------------------------------- #
def rms_db(x: np.ndarray) -> float:
    if x.size == 0:
        return float("-inf")
    return 20.0 * math.log10(float(np.sqrt(np.mean(np.square(x)))) + 1e-9)


def si_sdr(est: np.ndarray, ref: np.ndarray) -> float:
    """Scale-invariant SDR in dB (higher is better)."""
    n = min(est.size, ref.size)
    est = est[:n] - est[:n].mean()
    ref = ref[:n] - ref[:n].mean()
    alpha = float(np.dot(est, ref)) / (float(np.dot(ref, ref)) + 1e-12)
    target = alpha * ref
    noise = est - target
    return 10.0 * math.log10((float(np.dot(target, target)) + 1e-12) / (float(np.dot(noise, noise)) + 1e-12))


# --------------------------------------------------------------------------- #
# compose
# --------------------------------------------------------------------------- #
def cmd_compose(a: argparse.Namespace) -> None:
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    left, right = Path(a.left), Path(a.right)
    for p in (left, right):
        if not has_audio(p):
            sys.exit(f"{p} has no audio track")
    dur = min(probe_duration(left), probe_duration(right))
    if a.seconds:
        dur = min(dur, a.seconds)
    mix = out / "mix.mp4"
    # Side by side at equal height; audio = plain sum (no normalisation) so the
    # references stay exact components of the mixture.
    ffmpeg(
        "-t", f"{dur}", "-i", str(left), "-t", f"{dur}", "-i", str(right),
        "-filter_complex",
        f"[0:v]scale=-2:{a.height},fps={WORK_FPS},setsar=1[l];"
        f"[1:v]scale=-2:{a.height},fps={WORK_FPS},setsar=1[r];"
        "[l][r]hstack=inputs=2[v];"
        f"[0:a]aresample={SR},pan=mono|c0=c0[a0];[1:a]aresample={SR},pan=mono|c0=c0[a1];"
        "[a0][a1]amix=inputs=2:duration=shortest:normalize=0[a]",
        "-map", "[v]", "-map", "[a]", "-t", f"{dur}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "pcm_s16le", "-ar", str(SR), str(mix.with_suffix(".mov")),
    )
    # Keep a lossless-audio .mov master, plus an .mp4 copy for players.
    ffmpeg("-i", str(mix.with_suffix(".mov")), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(mix))
    ref_l, ref_r = read_audio(left, 0, dur), read_audio(right, 0, dur)
    write_wav(out / "ref_left.wav", ref_l)
    write_wav(out / "ref_right.wav", ref_r)
    mixture = read_audio(mix.with_suffix(".mov"))
    meta = {
        "mix": str(mix), "mix_master": str(mix.with_suffix(".mov")), "duration_s": round(dur, 3),
        "left_box": [0, 0, 0.5, 1], "right_box": [0.5, 0, 1, 1],
        "rms_db": {"left": round(rms_db(ref_l), 1), "right": round(rms_db(ref_r), 1),
                   "mixture": round(rms_db(mixture), 1)},
        "baseline_si_sdr_db": {"mixture_vs_left": round(si_sdr(mixture, ref_l), 2),
                               "mixture_vs_right": round(si_sdr(mixture, ref_r), 2)},
    }
    (out / "compose.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    print(f"\nNext: python {Path(__file__).name} run --video {mix.with_suffix('.mov')} "
          f"--box 0 0 0.5 1 --ref {out / 'ref_left.wav'} --out {out / 'run_left'}")


# --------------------------------------------------------------------------- #
# run
# --------------------------------------------------------------------------- #
def cut_clip(src: Path, dst: Path, start: float, seconds: float) -> None:
    """Short working clip: downscaled, fixed fps, mono 48 kHz PCM audio."""
    ffmpeg(
        "-ss", f"{start}", "-t", f"{seconds}", "-i", str(src),
        "-vf", f"scale={WORK_WIDTH}:-2,fps={WORK_FPS},setsar=1",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", str(dst),
    )


def box_mask(n: int, h: int, w: int, box: list[float]):
    import torch

    x0, y0, x1, y1 = box
    m = torch.zeros((n, 1, h, w), dtype=torch.bool)
    m[:, :, int(round(y0 * h)):int(round(y1 * h)), int(round(x0 * w)):int(round(x1 * w))] = True
    return m


def pick_device(name: str) -> str:
    import torch

    if name != "auto":
        return name
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def as_numpy(t) -> np.ndarray:
    import torch

    if isinstance(t, (list, tuple)):
        t = t[0]
    if isinstance(t, torch.Tensor):
        return t.detach().float().cpu().numpy().reshape(-1)
    return np.asarray(t, dtype=np.float32).reshape(-1)


def cmd_run(a: argparse.Namespace) -> None:
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    clip = out / "clip.mov"
    cut_clip(Path(a.video), clip, a.start, a.seconds)
    mixture = read_audio(clip)
    clip_s = mixture.size / SR
    write_wav(out / "mixture.wav", mixture)

    ref = None
    if a.ref:
        # References from `compose` start at t=0 of the mix, so cut the same window.
        ref = read_audio(Path(a.ref), a.start, a.seconds)

    report: dict = {
        "clip": str(clip), "clip_seconds": round(clip_s, 2), "box": a.box,
        "control_box": a.control_box, "model": a.model,
        "python": sys.version.split()[0], "platform": platform.platform(),
        "runs": {},
    }

    if a.dry_run:
        # Plumbing check without the model: pretend the mixture is the output.
        runs = {"visual": mixture, "text_only": mixture}
        if a.control_box:
            runs["control"] = mixture
        for name, est in runs.items():
            write_wav(out / f"target_{name}.wav", est)
            entry = {"seconds": 0.0, "rtf": 0.0, "target_rms_db": round(rms_db(est), 1)}
            if ref is not None:
                entry["si_sdr_db"] = round(si_sdr(est, ref), 2)
            report["runs"][name] = entry
        report["dry_run"] = True
        finish(out, report, ref, mixture)
        return

    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    import torch
    from torchcodec.decoders import VideoDecoder

    from sam_audio import SAMAudio, SAMAudioProcessor

    device = pick_device(a.device)
    report["torch"] = torch.__version__
    report["device_requested"] = device

    t0 = time.perf_counter()
    # Config overrides: never build the CLAP/judge/ImageBind re-rankers or the
    # span predictor. Only the separation model itself is loaded.
    model = SAMAudio.from_pretrained(a.model, text_ranker=None, visual_ranker=None, span_predictor=None)
    processor = SAMAudioProcessor.from_pretrained(a.model)
    model = model.eval().to(device)
    report["load_seconds"] = round(time.perf_counter() - t0, 1)

    frames = VideoDecoder(str(clip), dimension_order="NCHW")[:]
    n, _, h, w = frames.shape
    report["frames"] = [int(n), int(h), int(w)]

    def separate(name: str, description: str, box: list[float] | None) -> None:
        nonlocal device
        kwargs = {"audios": [str(clip)], "descriptions": [description]}
        if box is not None:
            kwargs["masked_videos"] = processor.mask_videos([frames], [box_mask(n, h, w, box)])
        entry: dict = {"description": description, "box": box}
        attempts = [device] + (["cpu"] if device != "cpu" else [])
        for attempt in attempts:
            try:
                batch = processor(**kwargs).to(attempt)
                if attempt != device:
                    model.to(attempt)
                if attempt == "mps":
                    torch.mps.synchronize()
                t = time.perf_counter()
                with torch.inference_mode():
                    result = model.separate(batch, predict_spans=False, reranking_candidates=1)
                if attempt == "mps":
                    torch.mps.synchronize()
                entry["seconds"] = round(time.perf_counter() - t, 2)
                entry["device"] = attempt
                break
            except Exception as exc:  # MPS op gaps -> retry on CPU, but record it
                entry.setdefault("errors", []).append(f"{attempt}: {type(exc).__name__}: {exc}"[:500])
                if attempt == "cpu":
                    report["runs"][name] = entry
                    print(f"[{name}] failed on CPU too: {exc}")
                    return
                device = "cpu"
        target, residual = as_numpy(result.target), as_numpy(result.residual)
        sr = int(processor.audio_sampling_rate)
        write_wav(out / f"target_{name}.wav", target, sr)
        write_wav(out / f"residual_{name}.wav", residual, sr)
        to_transcribe_wav(out / f"target_{name}.wav", out / f"target_{name}_16k.wav")
        entry.update({
            "rtf": round(entry["seconds"] / max(clip_s, 1e-6), 2),
            "target_rms_db": round(rms_db(target), 1),
            "residual_rms_db": round(rms_db(residual), 1),
        })
        if ref is not None:
            entry["si_sdr_db"] = round(si_sdr(target, ref), 2)
        report["runs"][name] = entry
        print(f"[{name}] {entry}")

    separate("visual", a.text, a.box)          # the Earshot path
    separate("text_only", "speech", None)       # can't choose a person: baseline
    if a.control_box:
        separate("control", a.text, a.control_box)  # nobody there: should be quiet

    report["device_used"] = device
    finish(out, report, ref, mixture)


def finish(out: Path, report: dict, ref, mixture: np.ndarray) -> None:
    report["mixture_rms_db"] = round(rms_db(mixture), 1)
    if ref is not None:
        report["baseline_mixture_si_sdr_db"] = round(si_sdr(mixture, ref), 2)
        vis = report["runs"].get("visual", {}).get("si_sdr_db")
        if vis is not None:
            report["si_sdr_improvement_db"] = round(vis - report["baseline_mixture_si_sdr_db"], 2)

    # Compliance self-check: none of these should ever be imported.
    forbidden = ("laion_clap", "imagebind", "whisper", "speechbrain", "pyannote", "silero")
    report["forbidden_modules_imported"] = sorted(
        m for m in sys.modules if m.split(".")[0] in forbidden
    )
    report["open_rule_question"] = (
        "SAM Audio runs Google's T5-base text encoder internally on every call "
        "(sam_audio/model/text_encoder.py). Ask organizers whether that is acceptable "
        "inside a Meta open model."
    )
    vis = report["runs"].get("visual", {})
    rtf = vis.get("rtf")
    report["verdict_hint"] = (
        "dry run (no model)" if report.get("dry_run")
        else "speed OK, now listen" if rtf is not None and rtf <= 3
        else "too slow for comfort (rtf > 3): try sam-audio-small-tv, shorter windows, or CPU vs MPS"
        if rtf is not None else "visual run failed, see errors"
    )
    (out / "report.json").write_text(json.dumps(report, indent=2))
    print("\n" + json.dumps(report, indent=2))
    print(f"\nListen: {out / 'mixture.wav'}  vs  {out / 'target_visual.wav'}")


# --------------------------------------------------------------------------- #
def main() -> None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        sys.exit("ffmpeg/ffprobe not found (brew install ffmpeg)")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compose", help="side-by-side test clip with ground-truth tracks")
    c.add_argument("--left", required=True)
    c.add_argument("--right", required=True)
    c.add_argument("--out", default="spike")
    c.add_argument("--seconds", type=float, default=0, help="cap duration (0 = shortest input)")
    c.add_argument("--height", type=int, default=720)
    c.set_defaults(func=cmd_compose)

    r = sub.add_parser("run", help="isolate the speaker inside --box")
    r.add_argument("--video", required=True)
    r.add_argument("--box", type=float, nargs=4, required=True, metavar=("X0", "Y0", "X1", "Y1"),
                   help="speaker box as fractions of width/height, e.g. 0 0 0.5 1")
    r.add_argument("--control-box", type=float, nargs=4, metavar=("X0", "Y0", "X1", "Y1"),
                   help="optional box over a region with nobody speaking")
    r.add_argument("--ref", help="clean reference track for this speaker (from compose)")
    r.add_argument("--start", type=float, default=0.0)
    r.add_argument("--seconds", type=float, default=10.0)
    r.add_argument("--text", default="", help='optional text prompt alongside the box, e.g. "male speech"')
    r.add_argument("--model", default="facebook/sam-audio-small-tv")
    r.add_argument("--device", default="auto", choices=["auto", "mps", "cpu", "cuda"])
    r.add_argument("--out", default="spike/run")
    r.add_argument("--dry-run", action="store_true", help="test the plumbing without loading the model")
    r.set_defaults(func=cmd_run)

    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
