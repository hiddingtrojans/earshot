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


def test_correction_endpoint_applies_and_replays(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    document = cached_doc()
    document["captions"] = [{"person": 0, "name": "Speaker A", "start": 0, "end": 1, "text": "hello"}]
    document["activity"] = [[(0.0, 1.0)], []]
    document["attribution"] = {"mapping": {"A": 0}, "confidence": {"A": 0.1}}
    (run / "earshot.json").write_text(json.dumps(document))
    with running_server(make_handler(run, False)) as base:
        request = urllib.request.Request(base + "/api/correct", data=json.dumps({
            "person": 0, "x": 0.79, "y": 0.37, "frame": 0,
        }).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=2) as response:
            corrected = json.loads(response.read())
    assert corrected["doc"]["captions"][0]["person"] == 1
    assert json.loads((run / "corrections.json").read_text())[0]["to"] == 1
    with running_server(make_handler(run, True)) as base:
        with urllib.request.urlopen(base + "/earshot.json", timeout=2) as response:
            replayed = json.loads(response.read())
    assert replayed["captions"][0]["person"] == 1
    with running_server(make_handler(run, True)) as base:
        request = urllib.request.Request(base + "/api/correct", data=json.dumps({
            "person": 1, "x": 0.26, "y": 0.28, "frame": 0,
        }).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=2) as response:
            corrected_again = json.loads(response.read())
    assert corrected_again["doc"]["captions"][0]["person"] == 0
    assert len(corrected_again["doc"]["corrections"]) == 2
    assert corrected_again["doc"]["corrections"][0]["to"] == 1
    assert corrected_again["doc"]["corrections"][1]["to"] == 0


def test_replay_corrections_preserve_packaged_evidence(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    document = cached_doc()
    document["captions"] = [{"person": 0, "name": "Speaker A", "start": 0, "end": 1, "text": "hello"}]
    document["activity"] = [[(0.0, 1.0)], []]
    document["attribution"] = {"mapping": {"A": 0}, "confidence": {"A": 0.1}}
    original = json.dumps(document)
    (run / "earshot.json").write_text(original)
    with running_server(make_handler(run, True)) as base:
        request = urllib.request.Request(base + "/api/correct", data=json.dumps({
            "person": 0, "x": 0.79, "y": 0.37, "frame": 0,
        }).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=2) as response:
            assert json.loads(response.read())["doc"]["captions"][0]["person"] == 1
        with urllib.request.urlopen(base + "/earshot.json", timeout=2) as response:
            assert json.loads(response.read())["captions"][0]["person"] == 1
    assert (run / "earshot.json").read_text() == original
    assert not (run / "corrections.json").exists()
    assert (run / ".replay-corrections.json").exists()


def test_demo_server_defaults_to_replay_with_api_key_present(tmp_path, monkeypatch):
    captured = {}

    class Server:
        def serve_forever(self):
            return None

    monkeypatch.setattr("earshot.server.make_handler",
                        lambda run, replay, *args: captured.update(replay=replay))
    monkeypatch.setattr("earshot.server.ThreadingHTTPServer", lambda address, handler: Server())
    monkeypatch.setenv("MODEL_API_KEY", "test-placeholder")
    monkeypatch.delenv("EARSHOT_REPLAY", raising=False)
    from earshot.server import serve
    serve(tmp_path / "demo" / "example")
    assert captured["replay"] is True


def test_catchup_accepts_packaged_sentence_fields(tmp_path, monkeypatch):
    from earshot.timeline import Caption

    run = tmp_path / "run"
    run.mkdir()
    captured = {}
    caption = Caption("c001", 0, "Speaker A", 0, 1, "A packaged caption.")
    (run / "earshot.json").write_text(json.dumps({
        "people": [{"name": "Speaker A"}], "captions": [caption.to_json()],
        "catchups": [], "catchup_model": "glimmer",
    }))

    def fake_catchup(captions, names, t, seconds, calls, person, model):
        captured.update(captions=captions, model=model)
        return {"window": [0, 1], "who": names[0], "sentences": []}

    monkeypatch.setattr("earshot.server.catch_up", fake_catchup)
    with running_server(make_handler(run, True)) as base:
        with urllib.request.urlopen(base + "/api/catchup?t=1&person=0", timeout=2) as response:
            assert response.status == 200
            assert json.loads(response.read())["source"] == "glimmer"
    assert captured["captions"] == [caption]
    assert captured["model"] == "glimmer"


def test_replay_miss_uses_precomputed_catchup_from_packaged_document(tmp_path, monkeypatch):
    from earshot.calls import ReplayMiss

    run = tmp_path / "run"
    run.mkdir()
    (run / "earshot.json").write_text(json.dumps({
        "people": [], "captions": [], "catchup_model": "glimmer",
        "catchups": [{"t": 40, "person": None, "sentences": [{"text": "Cached answer", "cite": ["c001"]}]}],
    }))

    def miss(*args, **kwargs):
        raise ReplayMiss("no response for this different time window")

    monkeypatch.setattr("earshot.server.catch_up", miss)
    with running_server(make_handler(run, True)) as base:
        with urllib.request.urlopen(base + "/api/catchup?t=45.58&person=all", timeout=2) as response:
            result = json.loads(response.read())
    assert response.status == 200
    assert result["source"] == "precomputed"
    assert result["sentences"][0]["text"] == "Cached answer"
