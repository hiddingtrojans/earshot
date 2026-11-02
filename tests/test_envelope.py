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


def test_bench_reports_envelope_matrix_and_correct_voice_headline(tmp_path, capsys):
    import json

    from earshot.bench import run_bench
    from earshot.media import write_wav

    time = np.arange(96_000) / 48_000
    first = (0.2 + 0.8 * (np.sin(2 * np.pi * 3 * time) > 0)) * np.sin(2 * np.pi * 220 * time)
    second = (0.2 + 0.8 * (np.sin(2 * np.pi * 7 * time) > 0)) * np.sin(2 * np.pi * 330 * time)
    for name, audio in (("a.wav", first), ("b.wav", second), ("mix.wav", first + second)):
        write_wav(tmp_path / name, audio.astype(np.float32), 48_000)
    doc = {"video": "mix.wav", "separator": "SAM Audio", "baseline": [], "captions": [],
           "people": [{"name": "A", "stem": "a.wav"}, {"name": "B", "stem": "b.wav"}]}
    (tmp_path / "earshot.json").write_text(json.dumps(doc))
    truth = {"people": {"A": "alpha", "B": "beta"}, "words": [],
             "reference_tracks": {"A": "a.wav", "B": "b.wav"}}
    (tmp_path / "truth.json").write_text(json.dumps(truth))

    result = run_bench(tmp_path, tmp_path / "truth.json")
    output = capsys.readouterr().out
    assert result["summary"]["correct_voice_rate"] == 1.0
    assert len(result["envelope"]["people"]) == 2
    assert result["envelope"]["si_sdr_note"].startswith("Mixture–A headset SI-SDR is ")
    assert "for this run" in result["envelope"]["si_sdr_note"]
    assert "Correct voice" in output and "Mixture correct voice" in output
    assert "SI-SDR gain" not in output
