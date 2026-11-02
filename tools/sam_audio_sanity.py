"""Sanity-check local SAM Audio on a known reference plus 0 dB white noise."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from earshot.bench import si_sdr
from earshot.media import SEPARATION_SR, read_audio, write_wav
from earshot.separation import SamAudioSeparator


def mix_white_noise(reference: np.ndarray, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(reference.size).astype(np.float32)
    reference_rms = float(np.sqrt(np.mean(reference ** 2)))
    noise *= reference_rms / float(np.sqrt(np.mean(noise ** 2)))
    return (reference + noise).astype(np.float32), noise


def rms(audio: np.ndarray) -> float:
    return float(np.sqrt(np.mean(audio ** 2)))


def db(value: float) -> float:
    return 20 * np.log10(max(value, 1e-12))


def run(reference_path: Path, out: Path, report: Path, device: str, seconds: float, seed: int) -> dict:
    reference = read_audio(reference_path, SEPARATION_SR, seconds=seconds)
    mixture, noise = mix_white_noise(reference, seed)
    out.mkdir(parents=True, exist_ok=True)
    write_wav(out / "mixture.wav", mixture, SEPARATION_SR)
    write_wav(out / "noise.wav", noise, SEPARATION_SR)
    separator = SamAudioSeparator(description="speech", device=device)
    started = time.perf_counter()
    separator._load()
    load_seconds = time.perf_counter() - started
    import torch

    torch.manual_seed(seed)
    started = time.perf_counter()
    batch = separator._processor(audios=[torch.from_numpy(mixture).unsqueeze(0)], descriptions=["speech"]).to(separator.device)
    processor_seconds = time.perf_counter() - started
    started = time.perf_counter()
    with torch.inference_mode():
        result = separator._model.separate(batch, predict_spans=False, reranking_candidates=1)
    separation_seconds = time.perf_counter() - started
    target = result.target[0].detach().float().cpu().numpy().reshape(-1)
    residual = result.residual[0].detach().float().cpu().numpy().reshape(-1)
    write_wav(out / "target.wav", target, SEPARATION_SR)
    write_wav(out / "residual.wav", residual, SEPARATION_SR)
    baseline = si_sdr(mixture, reference)
    target_score = si_sdr(target, reference)
    result_data = {
        "reference": str(reference_path), "seconds": seconds, "seed": seed,
        "snr_db": db(rms(reference)) - db(rms(noise)),
        "input_sample_rate": SEPARATION_SR,
        "processor_audio_sampling_rate": separator._processor.audio_sampling_rate,
        "batch_audio_sampling_rate": batch.audio_sampling_rate,
        "sample_rate_matches": batch.audio_sampling_rate == SEPARATION_SR == separator._processor.audio_sampling_rate,
        "input_samples": int(batch.wav_sizes[0].item()),
        "output_samples": int(target.size),
        "output_length_matches": target.size == mixture.size,
        "anchors": batch.anchors, "masked_video": batch.masked_video,
        "mixture_si_sdr_db": round(baseline, 4), "target_si_sdr_db": round(target_score, 4),
        "improvement_db": round(target_score - baseline, 4),
        "expected_improvement_db": 10.0, "passes_10db": target_score - baseline >= 10.0,
        "target_rms": rms(target), "target_rms_dbfs": db(rms(target)),
        "residual_rms": rms(residual), "residual_rms_dbfs": db(rms(residual)),
        "residual_si_sdr_db": round(si_sdr(residual, reference), 4),
        "input_rms": rms(mixture), "reference_rms": rms(reference), "noise_rms": rms(noise),
        "load_seconds": round(load_seconds, 3), "processor_seconds": round(processor_seconds, 3),
        "separation_seconds": round(separation_seconds, 3),
        "output": str(out),
    }
    report.write_text(json.dumps(result_data, indent=2) + "\n")
    print(json.dumps(result_data, indent=2))
    return result_data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=Path("bench/ami_ES2008a/ref_A.wav"))
    parser.add_argument("--out", type=Path, default=Path("runs/sanity_sam"))
    parser.add_argument("--report", type=Path, default=Path("review/sanity_result.json"))
    parser.add_argument("--device", default="mps")
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    run(args.reference, args.out, args.report, args.device, args.seconds, args.seed)


if __name__ == "__main__":
    main()
