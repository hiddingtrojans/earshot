from types import SimpleNamespace

import pytest

from earshot.calls import CallLog
from earshot.tracking import Tap, track_people


def test_out_of_range_tap_fails_before_video_upload(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"not uploaded")
    info = SimpleNamespace(frames=252, width=704, height=576, fps=25.0)
    calls = CallLog(tmp_path / "run")
    with pytest.raises(ValueError, match="between 0 and 251"):
        track_people(video, [Tap("Speaker A", 0.25, 0.29, 252)], info, calls)
    assert not calls.log_path.exists()
