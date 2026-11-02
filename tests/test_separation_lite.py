import numpy as np

from earshot.lite import attribute_turns, head_motion
from earshot.tracking import Tracks
from earshot.separation import crossfade_windows, overlap_add
from earshot.transcribe import Turn


def test_windows_cover_signal():
    w = crossfade_windows(25, 10, 2)
    assert w[0] == (0, 10) and w[-1][1] == 25
    covered = np.zeros(25, bool)
    for a, b in w:
        covered[a:b] = True
    assert covered.all()
    assert crossfade_windows(5, 10, 2) == [(0, 5)]


def test_overlap_add_reconstructs_constant():
    total, win, ov = 1000, 300, 50
    chunks = [(a, np.ones(b - a, np.float32)) for a, b in crossfade_windows(total, win, ov)]
    out = overlap_add(chunks, total, ov)
    assert np.allclose(out, 1.0, atol=1e-5)


def test_lite_attribution_by_head_motion():
    fps = 10.0
    n = 100
    # person 0's head moves during 0-5 s, person 1's during 5-10 s
    m0 = np.r_[np.full(50, 5.0), np.full(50, 1.0)]
    m1 = np.r_[np.full(50, 1.0), np.full(50, 5.0)]
    turns = [Turn("A", 0.5, 4.5, "hi"), Turn("B", 5.5, 9.5, "hello"), Turn("A", 1.0, 2.0, "again")]
    mapping = attribute_turns(turns, [m0, m1], fps)
    assert mapping == {"A": 0, "B": 1}
    assert n == m0.size


def test_lite_attribution_uses_optimal_not_greedy_assignment():
    turns = [Turn("A", 0.0, 1.0, "first"), Turn("B", 1.0, 2.0, "second")]
    person0 = np.array([5.0, 4.0, 1.0, 1.0, 1.0])
    person1 = np.array([4.0, 1.0, 1.0, 1.0, 1.0])
    assert attribute_turns(turns, [person0, person1], 1.0) == {"A": 1, "B": 0}


def test_lite_attribution_does_not_amplify_static_region_noise():
    turns = [Turn("speech", 0.0, 2.0, "words")]
    face = np.array([2.0, 2.0, 1.0, 1.0, 1.0])
    empty = np.full(5, 0.0045)
    assert attribute_turns(turns, [face, empty], 1.0) == {"speech": 0}


def test_activity_match_beats_larger_overall_motion():
    turns = [Turn("speaker2", 2.0, 6.0, "words")]
    overall = np.full(100, 100.0)
    other = np.full(100, 1.0)
    aligned = np.r_[np.full(20, 1.0), np.full(40, 100.0), np.full(40, 1.0)]
    assert attribute_turns(turns, [overall, other, aligned], 10.0) == {"speaker2": 2}


def test_head_motion_uses_central_mouth_band():
    packed = np.packbits(np.ones(100 * 200, dtype=np.uint8)).tobytes()
    tracks = Tracks(["Speaker A"], 100, 300, 25.0, 2, [{1: (10, 100, 100, 200, packed)}])
    frames = np.zeros((2, 300, 100), dtype=np.uint8)
    frames[0, 100:130, 30:90] = 50
    frames[1, 100:130, 30:90] = 100
    frames[0, 160:220, 30:90] = 10
    frames[1, 160:220, 30:90] = 20
    assert head_motion(frames, tracks, 0)[1] == 10.0
