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
