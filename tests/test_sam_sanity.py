import numpy as np

from tools.sam_audio_sanity import db, mix_white_noise, rms


def test_white_noise_mix_is_zero_db_and_deterministic():
    reference = np.sin(np.arange(48_000) * 0.1).astype(np.float32)
    first, noise = mix_white_noise(reference, seed=7)
    second, _ = mix_white_noise(reference, seed=7)
    assert np.array_equal(first, second)
    assert db(rms(reference)) - db(rms(noise)) == np.float32(0.0)
    assert first.shape == reference.shape
