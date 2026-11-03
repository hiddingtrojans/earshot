"""Classical microphone-array beamforming and alignment with numpy/scipy only."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import stft

ARRAY_SR = 16_000
FFT_SIZE = 512
HOP_SIZE = 128
DIAGONAL_LOAD = 1e-3
MAX_GCC_LAG = 64


def load_array(path: Path, channels: list[int] | None = None) -> tuple[np.ndarray, int]:
    rate, audio = wavfile.read(path)
    if rate != ARRAY_SR or audio.ndim != 2 or audio.shape[1] != 8:
        raise ValueError(f"Expected eight-channel 16 kHz audio: {path}")
    channels = list(range(1, 9)) if channels is None else channels
    if not channels or len(set(channels)) != len(channels) or any(channel < 1 or channel > 8 for channel in channels):
        raise ValueError("Array channels must be unique 1-based indexes from 1 to 8")
    if np.issubdtype(audio.dtype, np.integer):
        audio = audio.astype(np.float32) / np.iinfo(audio.dtype).max
    return np.asarray(audio[:, [channel - 1 for channel in channels]], dtype=np.float32), rate


def gcc_phat_delay(reference: np.ndarray, other: np.ndarray, max_lag: int = MAX_GCC_LAG) -> int:
    size = 1 << int(np.ceil(np.log2(max(2, reference.size + other.size))))
    spectrum = np.fft.rfft(other, size) * np.conj(np.fft.rfft(reference, size))
    spectrum /= np.maximum(np.abs(spectrum), 1e-12)
    correlation = np.fft.irfft(spectrum, size)
    lags = np.arange(-max_lag, max_lag + 1)
    return int(lags[np.argmax(correlation[lags % size])])


def shift_to_reference(signal: np.ndarray, delay: int) -> np.ndarray:
    out = np.zeros_like(signal)
    if delay > 0:
        out[:-delay] = signal[delay:]
    elif delay < 0:
        out[-delay:] = signal[:delay]
    else:
        out[:] = signal
    return out


def delay_and_sum(audio: np.ndarray) -> tuple[np.ndarray, list[int]]:
    delays = [gcc_phat_delay(audio[:, 0], audio[:, channel]) for channel in range(audio.shape[1])]
    aligned = [shift_to_reference(audio[:, channel], delay) for channel, delay in enumerate(delays)]
    return np.mean(aligned, axis=0).astype(np.float32), delays


def stft_array(audio: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    frequencies, times, transformed = stft(
        audio.T, fs=ARRAY_SR, window="hann", nperseg=FFT_SIZE,
        noverlap=FFT_SIZE - HOP_SIZE, nfft=FFT_SIZE, boundary="zeros", padded=True,
    )
    return frequencies, times, transformed


def covariance(spectrogram: np.ndarray) -> np.ndarray:
    if spectrogram.shape[2] == 0:
        return np.zeros((spectrogram.shape[0], spectrogram.shape[0], spectrogram.shape[1]), dtype=np.complex128)
    return np.einsum("dft,eft->def", spectrogram, spectrogram.conj()) / spectrogram.shape[2]


def souden_mvdr(spectrogram: np.ndarray, target_mask: np.ndarray) -> tuple[np.ndarray, dict]:
    channels, frequencies, _ = spectrogram.shape
    if target_mask.sum() < 2 or (~target_mask).sum() < 2:
        reference = int(np.argmax(np.var(spectrogram, axis=2).mean(axis=1)))
        return spectrogram[reference], {"degenerate_guide": True, "reference_channel": reference + 1}
    target = covariance(spectrogram[:, :, target_mask])
    noise = covariance(spectrogram[:, :, ~target_mask])
    loading = DIAGONAL_LOAD * np.trace(noise, axis1=0, axis2=1) / channels
    loaded = noise + loading[None, None, :] * np.eye(channels)[:, :, None]
    target_f = np.moveaxis(target, -1, 0)
    weights = np.linalg.solve(np.moveaxis(loaded, -1, 0), target_f)
    normalization = np.trace(weights, axis1=1, axis2=2)
    active = np.abs(normalization) > 1e-9 * max(1e-300, float(np.max(np.abs(normalization))))
    weights = weights / np.where(active, normalization, 1.0)[:, None, None]
    weights *= active[:, None, None]
    target_power = np.real(np.diagonal(target, axis1=0, axis2=1)).sum(axis=0)
    noise_power = np.real(np.diagonal(noise, axis1=0, axis2=1)).sum(axis=0)
    global_snr = target_power / np.maximum(noise_power, 1e-12)
    reference = int(np.argmax(global_snr))
    output = np.einsum("fd,dft->ft", weights[:, :, reference].conj(), spectrogram)
    return output, {
        "degenerate_guide": False,
        "reference_channel": reference + 1,
        "selected_snr": float(global_snr[reference]),
    }


def inverse_stft(spectrogram: np.ndarray, total_samples: int) -> np.ndarray:
    frames = np.fft.irfft(spectrogram, n=FFT_SIZE, axis=0)
    window = np.hanning(FFT_SIZE)
    audio = np.zeros(total_samples, dtype=np.float64)
    weights = np.zeros(total_samples, dtype=np.float64)
    for index, frame in enumerate(frames.T):
        start = index * HOP_SIZE - FFT_SIZE // 2
        end = start + FFT_SIZE
        left, right = max(0, start), min(total_samples, end)
        if right <= left:
            continue
        offset = left - start
        audio[left:right] += frame[offset:offset + right - left] * window[offset:offset + right - left]
        weights[left:right] += window[offset:offset + right - left] ** 2
    active = weights > 1e-8
    audio[active] /= weights[active]
    return (audio * window.sum()).astype(np.float32)


def separate(audio: np.ndarray, guides: list[np.ndarray], guide_fps: float) -> tuple[dict[int, np.ndarray], dict]:
    _, times, spectrogram = stft_array(audio)
    outputs, metadata = {}, {}
    for person, guide in enumerate(guides):
        indexes = np.minimum((times * guide_fps).astype(int), guide.size - 1)
        output, person_metadata = souden_mvdr(spectrogram, guide[indexes])
        outputs[person] = inverse_stft(output, audio.shape[0])
        metadata[str(person)] = person_metadata
    return outputs, metadata
