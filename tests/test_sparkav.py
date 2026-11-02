import json
from types import SimpleNamespace

from earshot.calls import CallLog
from earshot.sparkav import transcribe_window, transcribe_windows
from earshot.tracking import Tap
from earshot.transcribe import Turn


def test_spark_av_parses_json_and_reuses_cache(monkeypatch, tmp_path):
    monkeypatch.setattr("earshot.sparkav._upload", lambda video: "file-av-test")
    monkeypatch.setattr("earshot.sparkav.api_key", lambda: "test-key")
    payload = {"segments": [
        {"person": 1, "start": 0.05, "end": 0.15, "text": " overlapping words "},
        {"person": 9, "start": 0.0, "end": 0.1, "text": "ignored"},
    ]}
    calls_seen = []

    class Responses:
        def create(self, **kwargs):
            calls_seen.append(kwargs)
            return SimpleNamespace(output_text=json.dumps(payload), id="resp_av", usage=None)

    class Client:
        def __init__(self, **kwargs):
            self.responses = Responses()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    monkeypatch.setattr("openai.OpenAI", Client)
    calls = CallLog(tmp_path)
    taps = [Tap("Speaker A", 0.25, 0.29), Tap("Speaker B", 0.8, 0.36)]
    baseline = [Turn("A", 0.0, 0.2, "hint")]
    video = __import__("pathlib").Path("bench/ami_ES2008a/clip.mp4")
    turns = transcribe_window(video, taps, baseline, 0.0, 0.2, calls)
    assert len(turns) == 2 and turns[1][0].text == "overlapping words"
    assert turns[1][0].start == 0.05 and turns[1][0].end == 0.15
    assert calls_seen[0]["input"][0]["content"][1]["type"] == "input_video"
    transcribe_window(video, taps, baseline, 0.0, 0.2, calls)
    assert len(calls_seen) == 1
    assert json.loads(calls.log_path.read_text().splitlines()[-1])["cache"] == "hit"


def test_spark_windows_stop_at_clip_end(monkeypatch, tmp_path):
    calls = CallLog(tmp_path)
    seen = []

    def fake(video, taps, baseline, start, seconds, calls, repeat=None):
        seen.append((start, seconds))
        return [[] for _ in taps]

    monkeypatch.setattr("earshot.sparkav.transcribe_window", fake)
    taps = [Tap("Speaker A", 0.25, 0.29)]
    _, activity = transcribe_windows(None, taps, [], 75.0, calls)
    assert seen[-1] == (70.0, 5.0)
    assert len(seen) == 8
    assert all(seconds > 0 for _, seconds in seen)
    assert activity == [[]]
