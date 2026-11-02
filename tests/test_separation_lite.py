import numpy as np

from earshot.lite import attribute_turns
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
