import wave

import numpy as np

from earshot.array import (
    delay_and_sum,
    gcc_phat_delay,
    load_array,
    separate,
    shift_to_reference,
)
from earshot.bench import si_sdr


def test_gcc_phat_alignment_recovers_integer_delay():
    rng = np.random.default_rng(3)
    reference = rng.standard_normal(16_000).astype(np.float32)
    other = np.r_[np.zeros(5, dtype=np.float32), reference[:-5] * 0.8]
    delay = gcc_phat_delay(reference, other)
    assert delay == 5
    aligned = shift_to_reference(other, delay)
    assert np.corrcoef(reference[100:-100], aligned[100:-100])[0, 1] > 0.999
    _, delays = delay_and_sum(np.stack([reference, other], axis=1))
    assert delays[1] == 5


def test_load_array_selects_one_based_channel_subset(tmp_path):
    path = tmp_path / "array.wav"
    frames = np.arange(32 * 8, dtype="<i2").reshape(32, 8)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(8)
        output.setsampwidth(2)
        output.setframerate(16_000)
        output.writeframes(frames.tobytes())
    audio, rate = load_array(path, [1, 3, 5, 7])
    assert rate == 16_000
    assert audio.shape == (32, 4)
    np.testing.assert_allclose(audio[:, 0], frames[:, 0] / np.iinfo(frames.dtype).max)


def test_souden_separation_improves_target_si_sdr():
    rate = 16_000
    time = np.arange(rate * 2) / rate
    rng = np.random.default_rng(8)
    target = rng.standard_normal(rate * 2).astype(np.float32)
    target[time < 1] = 0
    first = target + 0.1 * rng.standard_normal(target.size)
    delayed = shift_to_reference(target, 4)
    second = 0.7 * delayed + 0.1 * rng.standard_normal(target.size)
    guide = np.arange(50) / 25 >= 1
    outputs, metadata = separate(np.stack([first, second], axis=1).astype(np.float32), [guide], 25)
    assert outputs[0].shape == target.shape
    assert si_sdr(outputs[0], target) > 5
    assert not metadata["0"]["degenerate_guide"]
    assert metadata["0"]["reference_channel"] == 1


def test_stft_roundtrip_preserves_samples_and_scale():
    from earshot.array import inverse_stft, stft_array

    audio = np.random.default_rng(11).standard_normal(16_000).astype(np.float32)
    _, _, spectrogram = stft_array(audio[:, None])
    reconstructed = inverse_stft(spectrogram[0], audio.size)
    assert np.linalg.norm(reconstructed - audio) / np.linalg.norm(audio) < 0.01
    assert si_sdr(reconstructed, audio) > 40


def test_degenerate_guide_returns_finite_reference_audio():
    audio = np.random.default_rng(2).standard_normal(16_000).astype(np.float32)
    outputs, metadata = separate(audio[:, None], [np.zeros(50, dtype=bool)], 25)
    assert outputs[0].shape == audio.shape
    assert np.isfinite(outputs[0]).all()
    assert metadata["0"]["degenerate_guide"]
