import json
import threading
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from http.server import ThreadingHTTPServer

import pytest

from earshot import pipeline
from earshot.server import make_handler, snap_taps
from earshot.tracking import Tap


def cached_doc():
    return {"people": [
        {"name": "Speaker A", "tap": [0.25, 0.29, 0]},
        {"name": "Speaker B", "tap": [0.80, 0.36, 3]},
    ], "captions": [], "catchups": []}


def test_replay_snapping_is_bounded_and_uses_cached_people():
    snapped = snap_taps([Tap("first", 0.26, 0.28), Tap("second", 0.79, 0.37)], cached_doc())
    assert snapped == [Tap("Speaker A", 0.25, 0.29, 0), Tap("Speaker B", 0.80, 0.36, 3)]
    with pytest.raises(ValueError, match="more than 5%"):
        snap_taps([Tap("first", 0.40, 0.28), Tap("second", 0.79, 0.37)], cached_doc())
    with pytest.raises(ValueError, match="exactly 2"):
        snap_taps([Tap("first", 0.26, 0.28)], cached_doc())


@contextmanager
def running_server(handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def post(base, payload):
    request = urllib.request.Request(base + "/api/analyze", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=2) as response:
        return response.status, json.loads(response.read())


def test_live_post_runs_pipeline_in_background(tmp_path, monkeypatch):
    run, video = tmp_path / "run", tmp_path / "video.mp4"
    video.write_bytes(b"not read by the fake")
    captured = {}

    def fake_analyze(source, taps, out, options):
        captured["taps"] = taps
        captured["options"] = options
        options.progress("Testing the real progress callback")
        (out / "earshot.json").write_text(json.dumps(cached_doc()))
        return out / "earshot.json"

    monkeypatch.setattr(pipeline, "analyze", fake_analyze)
    with running_server(make_handler(run, False, video)) as base:
        status, result = post(base, {"taps": [{"name": "Speaker A", "x": 0.3, "y": 0.4, "frame": 2}],
                                     "separator": "lite"})
        assert status == 202
        for _ in range(50):
            with urllib.request.urlopen(base + f"/api/analyze/status?job={result['job']}", timeout=2) as response:
                job = json.loads(response.read())
            if job["status"] == "done":
                break
            time.sleep(0.02)
        assert job["status"] == "done"
        assert job["steps"] == ["Testing the real progress callback"]
    assert captured["taps"] == [Tap("Speaker A", 0.3, 0.4, 2)]
    assert captured["options"].separator == "lite"
    assert captured["options"].replay is False


def test_replay_post_returns_cached_run_without_calling_pipeline(tmp_path, monkeypatch):
    run, video = tmp_path / "run", tmp_path / "video.mp4"
    run.mkdir()
    video.write_bytes(b"not read")
    (run / "earshot.json").write_text(json.dumps(cached_doc()))

    def unexpected(*args):
        raise AssertionError("replay must not invoke the pipeline")

    monkeypatch.setattr(pipeline, "analyze", unexpected)
    with running_server(make_handler(run, True, video)) as base:
        _, result = post(base, {"taps": [{"name": "custom", "x": 0.26, "y": 0.28, "frame": 0},
                                               {"name": "other", "x": 0.79, "y": 0.37, "frame": 0}]})
        assert result["done"] is True
        assert [tap["name"] for tap in result["taps"]] == ["Speaker A", "Speaker B"]
        with pytest.raises(urllib.error.HTTPError) as error:
            post(base, {"taps": [{"name": "custom", "x": 0.5, "y": 0.5, "frame": 0},
                                       {"name": "other", "x": 0.79, "y": 0.37, "frame": 0}]})
        assert error.value.code == 400


def test_subtitle_endpoints_work_offline(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    doc = {
        "people": [{"name": "Speaker A", "color": "#E4572E", "anchors": [[0, 0.25, 0.3]]}],
        "captions": [{"person": 0, "start": 0.0, "end": 1.0, "text": "cached words"}],
        "catchups": [],
    }
    (run / "earshot.json").write_text(json.dumps(doc))
    with running_server(make_handler(run, True)) as base:
        with urllib.request.urlopen(base + "/api/subtitles.vtt", timeout=2) as response:
            assert response.headers["Content-Type"] == "text/vtt; charset=utf-8"
            vtt = response.read().decode()
        with urllib.request.urlopen(base + "/api/subtitles.srt", timeout=2) as response:
            srt = response.read().decode()
    assert "::cue(.spk0) { color: #E4572E; }" in vtt
    assert "cached words" in vtt
    assert "[Speaker A] cached words" in srt
