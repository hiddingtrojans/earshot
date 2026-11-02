import importlib

import numpy as np

from earshot.bench import _repeat_summary, overlap_word_indexes_from_words
from earshot.calls import CallLog


def test_word_level_overlap_uses_exact_word_intervals():
    words = [
        {"person": "Speaker A", "start": 0.0, "end": 1.0, "text": "one"},
        {"person": "Speaker A", "start": 1.0, "end": 2.0, "text": "two"},
        {"person": "Speaker A", "start": 2.0, "end": 3.0, "text": "three"},
        {"person": "Speaker B", "start": 1.5, "end": 2.5, "text": "other"},
    ]
    assert overlap_word_indexes_from_words(words, "Speaker A") == {1, 2}
    assert overlap_word_indexes_from_words(words, "Speaker B") == {0}


def test_voice_repeats_have_independent_cache_entries(monkeypatch, tmp_path):
    transcribe_module = importlib.import_module("earshot.transcribe")
    calls = CallLog(tmp_path)
    invocations = []

    def fake_post(wav, mode):
        invocations.append((wav, mode))
        return {"turns": []}, {"sessionId": f"session-{len(invocations)}"}

    monkeypatch.setattr(transcribe_module, "_post_transcribe", fake_post)
    audio = np.zeros(240, dtype=np.float32)
    for repeat in (None, None, 0, 1, 0):
        transcribe_module.transcribe(audio, calls, purpose="repeat test", repeat=repeat)
    assert len(invocations) == 3
    rows = [line for line in calls.log_path.read_text().splitlines()]
    assert len(rows) == 5


def test_repeat_summary_reports_mean_and_min_max():
    repeats = [{"summary": {
        "earshot": {"wer": value, "attribution": 0.8, "overlap_recall": 0.5},
        "baseline": {"wer": 1.0, "attribution": 0.7, "overlap_recall": 0.4},
    }} for value in (0.4, 0.6, 0.8)]
    summary = _repeat_summary(repeats)
    assert summary["earshot"]["wer"] == {"mean": 0.6, "min": 0.4, "max": 0.8}
    assert summary["baseline"]["attribution"] == {"mean": 0.7, "min": 0.7, "max": 0.7}
