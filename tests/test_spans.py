import json

import numpy as np
import pytest

from earshot.calls import CallLog
from earshot.spans import (
    SpanAudioSeparator,
    build_window_plan,
    runtime_attribution,
    select_enrollment,
    solo_spans,
    window_audio,
)
from earshot.tracking import Tracks
from earshot.transcribe import Turn


def test_solo_spans_subtract_other_labels_and_drop_short_fragments():
    turns = [Turn("A", 0, 3, "a"), Turn("A", 4, 4.4, "short"),
             Turn("A", 10, 12, "later"), Turn("B", 1, 2, "b"), Turn("B", 5, 8, "solo")]
    assert solo_spans(turns, {"A": 0, "B": 1}, 2, 12) == [
        [(0, 1), (2, 3), (10, 12)], [(5, 8)],
    ]
    with pytest.raises(ValueError, match="cover every diarized label"):
        solo_spans(turns, {"A": 0}, 2, 12)


def test_enrollment_and_window_anchors_match_audio_and_trim_offset():
    sr = 100
    mixture = np.arange(30 * sr, dtype=np.float32)
    solo = [[(0, 2), (10, 14), (20, 22)], [(1, 5), (30, 34)], [(6, 8)]]
    plan = build_window_plan(mixture, solo, 0, 0, 10 * sr, sr)
    assert [source["start"] for source in plan["sources"]] == [10, 1, 6]
    assert plan["offset_samples"] == 850
    assert plan["anchors"] == [
        ("+", 0.0, 4.0), ("-", 4.25, 6.25), ("-", 6.25, 8.25),
        ("+", 8.5, 10.5), ("-", 9.5, 13.5), ("-", 14.5, 16.5),
    ]
    audio = window_audio(mixture, plan, sr)
    assert audio.size == 1850
    assert np.array_equal(audio[:400], mixture[1000:1400])
    assert np.array_equal(audio[-1000:], mixture[:1000])
    assert select_enrollment([(0, 1), (5, 9), (20, 21)], 5) == [(5, 9), (0, 1)]


def test_span_cache_key_contains_mode_and_anchor_plan(tmp_path, monkeypatch):
    monkeypatch.delenv("EARSHOT_REPLAY", raising=False)
    tracks = Tracks(["A", "B"], 1, 1, 25.0, 1, [{}, {}])
    mixture = np.zeros(480_000, dtype=np.float32)
    turns = [Turn("A", 0, 4, "a"), Turn("B", 5, 9, "b")]

    def fake(video, audio, tracks, people):
        return ({person: np.zeros(audio.size, dtype=np.float32) for person in people},
                {str(person): 1 for person in people}, "test", [])

    keys = []
    for index, (mode, mapping) in enumerate([
        ("spans-text", {"A": 0, "B": 1}),
        ("spans-video", {"A": 0, "B": 1}),
        ("spans-text", {"A": 1, "B": 0}),
    ]):
        run = tmp_path / str(index)
        separator = SpanAudioSeparator(turns=turns, mapping=mapping, span_mode=mode)
        separator._separate_uncached = fake
        separator.separate_people(None, mixture, tracks, CallLog(run))
        rows = [json.loads(line) for line in (run / "calls.jsonl").read_text().splitlines()]
        keys.append(rows[-1]["key"])
        assert rows[-1]["anchor_digest"]
    assert len(set(keys)) == 3


def test_clip_seconds_trims_output_but_not_enrollment(tmp_path, monkeypatch):
    monkeypatch.delenv("EARSHOT_REPLAY", raising=False)
    tracks = Tracks(["A", "B"], 1, 1, 25.0, 1, [{}, {}])
    mixture = np.zeros(20 * 48_000, dtype=np.float32)
    turns = [Turn("A", 0, 4, "a"), Turn("B", 15, 19, "b")]
    separator = SpanAudioSeparator(turns=turns, mapping={"A": 0, "B": 1}, clip_seconds=5)

    def fake(video, audio, tracks, people):
        return ({person: np.zeros(audio.size, dtype=np.float32) for person in people},
                {str(person): 1 for person in people}, "test", [])

    separator._separate_uncached = fake
    stems = separator.separate_people(None, mixture, tracks, CallLog(tmp_path))
    assert all(samples.size == 5 * 48_000 for samples in stems.values())
    sources = separator._plans[0][0]["sources"]
    assert any(source["person"] == 1 and source["start"] == 15 for source in sources)


def test_runtime_attribution_applies_saved_corrections(tmp_path, monkeypatch):
    doc = {
        "video": "analysis.mp4",
        "people": [{"name": "Speaker A", "tap": [0.25, 0.29, 0]},
                   {"name": "Speaker B", "tap": [0.8, 0.36, 0]}],
        "baseline": [{"speaker": "A", "start": 0, "end": 1, "text": "hello"}],
    }
    (tmp_path / "earshot.json").write_text(json.dumps(doc))
    Tracks(["Speaker A", "Speaker B"], 1, 1, 25.0, 1, [{}, {}]).save(tmp_path / "tracks.json")
    (tmp_path / "corrections.json").write_text(json.dumps([
        {"from": 0, "to": 1, "tap": [0.8, 0.36, 0]},
    ]))
    monkeypatch.setattr("earshot.lite.gray_frames", lambda video: np.zeros((1, 1, 1), dtype=np.uint8))
    monkeypatch.setattr("earshot.lite.head_motion", lambda frames, tracks, person: np.zeros(1))
    monkeypatch.setattr("earshot.lite.attribute_with_confidence",
                        lambda turns, motion, fps: ({"A": 0}, {"A": 0.1}))
    _, mapping, confidence, _ = runtime_attribution(tmp_path)
    assert mapping == {"A": 1}
    assert confidence == {"A": 1.0}
