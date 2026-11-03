"""End-to-end pipeline run on a SYNTHETIC clip with fake model clients."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import synthetic  # noqa: E402

from earshot import pipeline, separation, spark  # noqa: E402
from earshot.tracking import Tap  # noqa: E402


@pytest.fixture()
def fakes(monkeypatch):
    monkeypatch.setattr(pipeline, "track_people", lambda video, taps, info, calls: synthetic.fake_tracks([t.name for t in taps], info))
    monkeypatch.setattr(pipeline, "transcribe", synthetic.fake_transcribe)
    monkeypatch.setattr(separation, "SamAudioSeparator", synthetic.FakeSeparator)
    monkeypatch.setattr(spark, "_respond", synthetic.fake_respond)
    monkeypatch.setattr(pipeline, "build_board", lambda captions, names, calls, model: {
        "items": [], "review": [], "verification_model": "muse-glimmer", "where": "local",
        "actions": "Review only: no automatic actions.", "counts": {"supported": 0, "not_accepted": 0},
    })


def run(tmp_path, separator):
    video = tmp_path / "in.mp4"
    synthetic.make_video(video)
    out = tmp_path / f"run_{separator}"
    taps = [Tap("Ana", 0.30, 0.35), Tap("Raúl", 0.70, 0.35)]
    pipeline.analyze(video, taps, out, pipeline.Options(separator=separator, catchup_every=10))
    return json.loads((out / "earshot.json").read_text()), out


def test_samaudio_path_recovers_overlapping_lines(tmp_path, fakes):
    doc, out = run(tmp_path, "samaudio")
    texts = {(c["name"], c["text"]) for c in doc["captions"]}
    assert ("Raúl", "I booked Casa Lola for eight") in texts  # spoken over Ana
    assert len(doc["captions"]) == len(synthetic.SCRIPT)
    assert any(c["overlap"] for c in doc["captions"])
    assert doc["overlaps"], "overlap windows should be detected from the isolated tracks"
    assert {t["topic"] for t in doc["threads"]} == {"Friday dinner", "The dog and the shoe"}
    assert all((out / p["stem"]).exists() for p in doc["people"])
    assert doc["people"][0]["anchors"] and doc["catchups"]
    assert len(doc["baseline"]) < len(synthetic.SCRIPT)  # single stream merges overlaps
    assert (out / "index.html").exists()


def test_lite_path_runs_without_separation(tmp_path, fakes):
    doc, _ = run(tmp_path, "lite")
    assert doc["separator"].startswith("none")
    assert doc["captions"] and all(p["stem"] is None for p in doc["people"])


def test_same_run_reuses_saved_tracks(tmp_path, fakes, monkeypatch):
    video = tmp_path / "in.mp4"
    synthetic.make_video(video)
    out = tmp_path / "run_lite"
    taps = [Tap("Ana", 0.30, 0.35), Tap("Raúl", 0.70, 0.35)]
    options = pipeline.Options(separator="lite", catchup_every=10)
    pipeline.analyze(video, taps, out, options)

    def unexpected_tracking(*args):
        raise AssertionError("same taps should load the saved tracks")

    monkeypatch.setattr(pipeline, "track_people", unexpected_tracking)
    doc = pipeline.analyze(video, taps, out, options)
    assert json.loads(doc.read_text())["captions"]
    doc.unlink()
    doc = pipeline.analyze(video, taps, out, options)
    assert json.loads(doc.read_text())["captions"]
