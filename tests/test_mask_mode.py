import numpy as np
import pytest

from earshot.separation import apply_mask_mode


class Processor:
    def mask_videos(self, frames, masks):
        return [frames[0] * mask.eq(0) for mask in masks]


class Mask:
    def __init__(self, values):
        self.values = np.asarray(values, dtype=bool)

    def __invert__(self):
        return Mask(~self.values)

    def eq(self, value):
        return self.values == value


def test_keep_leaves_only_target_visible():
    frames = [np.ones((2, 2), dtype=np.uint8)]
    target = Mask([[True, False], [False, False]])
    kept = apply_mask_mode(Processor(), frames, [target], "keep")[0]
    removed = apply_mask_mode(Processor(), frames, [target], "remove")[0]
    assert kept.tolist() == [[1, 0], [0, 0]]
    assert removed.tolist() == [[0, 1], [1, 1]]
    with pytest.raises(ValueError, match="unknown mask mode"):
        apply_mask_mode(Processor(), frames, [target], "invalid")


def test_batched_people_cache_includes_mask_mode(tmp_path):
    from earshot.calls import CallLog
    from earshot.separation import SamAudioSeparator
    from earshot.tracking import Tracks

    calls = CallLog(tmp_path)
    tracks = Tracks(["A", "B"], 1, 1, 25.0, 1, [{}, {}])
    separator = SamAudioSeparator(mask_mode="keep")
    separator._separate_uncached = lambda *args: (
        {0: np.array([1.0]), 1: np.array([2.0])},
        {"0": 10, "1": 20}, "batched", [],
    )
    result = separator.separate_people(None, np.zeros(1), tracks, calls)
    assert result[0][0] == 1.0 and result[1][0] == 2.0
    separator.separate_people(None, np.zeros(1), tracks, calls)
    rows = [row for row in (tmp_path / "calls.jsonl").read_text().splitlines()]
    assert len(rows) == 2
    assert '"cache": "hit"' in rows[-1]
    assert '"batching": "batched"' in rows[-1]
