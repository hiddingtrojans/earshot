import numpy as np

from earshot.motion import (
    events_from_mask,
    guide_activities,
    motion_activity,
    overlap_metrics,
    talked_over,
)
from earshot.timeline import Caption
from earshot.transcribe import Turn


def test_motion_threshold_and_minimum_event_are_fixed():
    motion = np.zeros(50)
    motion[12:25] = 1.0
    activity, threshold = motion_activity(motion, 25)
    assert threshold == 0.1
    events = events_from_mask(activity, 25)
    assert len(events) == 1 and events[0][1] - events[0][0] >= 0.5
    assert events_from_mask(np.r_[np.zeros(10, bool), np.ones(3, bool)], 25) == []
    assert not motion_activity(np.full(50, 0.01), 25)[0].any()


def test_missing_label_uses_motion_guide():
    motion = [np.zeros(25), np.zeros(25)]
    motion[1][4:10] = 1.0
    guides, metadata = guide_activities([[Turn("A", 0, 0.2, "a")], []], motion, 25, 25)
    assert guides[0].any()
    assert not guides[1][:5].any()
    assert guides[1][5:10].all()
    assert metadata["motion_fallback_people"] == [1]


def test_talked_over_marker_and_overlap_precision_recall(monkeypatch):
    motion = [np.zeros(50), np.zeros(50)]
    motion[1][12:25] = 1.0
    captions = [Caption("c001", 0, "A", 0, 2, "hello")]
    turns = [[Turn("A", 0, 2, "hello")], []]
    markers, _ = talked_over(captions, turns, motion, 25)
    assert markers["c001"][0]["person"] == 1
    assert markers["c001"][0]["end"] - markers["c001"][0]["start"] >= 0.5
    words = [
        {"person": "A", "start": 0, "end": 1, "text": "a"},
        {"person": "B", "start": 0.5, "end": 1.5, "text": "b"},
    ]
    motion_b = np.zeros(50)
    motion_b[12:38] = 1.0
    turns = [[Turn("A", 0, 1, "a")], [Turn("B", 0.5, 1.5, "b")]]
    monkeypatch.setattr("earshot.motion.motion_activity", lambda values, fps: (values.astype(bool), 0.1))
    result = overlap_metrics(turns, [motion_b.copy(), motion_b], words, ["A", "B"], 25)
    assert result["precision"] == 0.6667
    assert result["recall"] == 1.0
