import numpy as np
import pytest

from earshot.envelope import correct_voice_rate, envelope_correlation, log_energy_envelope


def test_envelope_correlation_identifies_matching_voice():
    time = np.arange(48_000 * 2) / 48_000
    voice = (0.2 + 0.8 * (np.sin(2 * np.pi * 3 * time) > 0)) * np.sin(2 * np.pi * 220 * time)
    other = np.zeros_like(voice)
    assert envelope_correlation(voice, voice) > 0.99
    assert envelope_correlation(voice, other) == 0.0
    assert log_energy_envelope(voice).size == 79


def test_correlation_uses_mixture_activity_gate(monkeypatch):
    monkeypatch.setattr("earshot.envelope.log_energy_envelope", lambda audio: audio)
    estimate = np.array([0.0, 1.0, 2.0, 3.0])
    reference = np.array([0.0, 1.0, 4.0, 9.0])
    mixture = np.array([3.0, 0.0, 2.0, 1.0])
    expected = np.corrcoef([0.0, 2.0, 3.0], [0.0, 4.0, 9.0])[0, 1]
    assert envelope_correlation(estimate, reference, mixture) == pytest.approx(expected)
    assert envelope_correlation(estimate, reference) != pytest.approx(expected)


def test_correct_voice_rate_is_diagonal_fraction():
    matrix = [[0.9, 0.8, 0.1, 0.2], [0.8, 0.9, 0.1, 0.2], [0.1, 0.2, 0.8, 0.95], [0.1, 0.2, 0.3, 0.4]]
    assert correct_voice_rate(matrix) == 0.75
