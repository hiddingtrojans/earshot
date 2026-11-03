import json
import sys
import wave
from pathlib import Path

import numpy as np
import pytest

from earshot import cli, pipeline, spark
from earshot.array import shift_to_reference
from earshot.bench import score_document
from earshot.tracking import Tap

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import synthetic  # noqa: E402


def make_array(path: Path) -> None:
    rate = 16_000
    time = np.arange(20 * rate) / rate
    sources = []
    for person in range(2):
        audio = np.zeros(time.size, dtype=np.float32)
        for speaker, start, end, _ in synthetic.SCRIPT:
            if speaker == person:
                mask = (time >= start) & (time < end)
                audio[mask] = 0.25 * np.sin(2 * np.pi * (220 + person * 110) * time[mask])
        sources.append(audio)
    channels = []
    for channel in range(8):
        channels.append(sum(shift_to_reference(source, (channel + person) % 3) * (0.5 + 0.03 * channel)
                            for person, source in enumerate(sources)))
    with wave.open(str(path), "wb") as output:
        output.setnchannels(8)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes((np.clip(np.stack(channels, axis=1), -1, 1) * 32767).astype("<i2").tobytes())


def test_array_pipeline_builds_stems_and_delay_sum(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "track_people", lambda video, taps, info, calls: synthetic.fake_tracks([t.name for t in taps], info))
    monkeypatch.setattr(pipeline, "transcribe", synthetic.fake_transcribe)
    monkeypatch.setattr(spark, "_respond", synthetic.fake_respond)
    video = tmp_path / "in.mp4"
    synthetic.make_video(video)
    array = tmp_path / "array.wav"
    make_array(array)
    out = tmp_path / "run"
    doc_path = pipeline.analyze(video, [Tap("Ana", .30, .35), Tap("Raúl", .70, .35)], out,
                                pipeline.Options(separator="array", array_path=array))
    doc = json.loads(doc_path.read_text())
    assert doc["array"]["channels"] == list(range(1, 9))
    assert doc["array_baseline"]
    assert (out / doc["array"]["delay_sum"]).exists()
    assert all((out / person["stem"]).exists() for person in doc["people"])
    assert doc["captions"]


def test_delay_sum_baseline_is_scored_separately():
    turn = {"speaker": "0", "start": 0, "end": 1, "text": "the dog"}
    doc = {"separator": "array test", "people": [{"name": "Ana"}, {"name": "Raúl"}],
           "captions": [], "baseline": [turn], "array_baseline": [turn]}
    result = score_document(doc, Path("unused"), {"people": {"Ana": "the dog", "Raúl": ""}, "words": []}, Path("unused"))
    assert result["summary"]["delay_sum"]["attribution"] == 0.5
    assert result["people"]["Ana"]["delay_sum"]["attribution"] == 1.0
    assert result["delay_sum_oracle_mapping"] == {"0": "Ana"}


def test_cli_accepts_array_and_channel_subset(tmp_path, monkeypatch):
    captured = {}

    def fake_analyze(video, taps, out, options):
        captured["options"] = options
        out.mkdir(parents=True, exist_ok=True)
        (out / "earshot.json").write_text("{}")
        return out / "earshot.json"

    monkeypatch.setattr(pipeline, "analyze", fake_analyze)
    video = tmp_path / "in.mp4"
    video.write_bytes(b"not read")
    monkeypatch.setattr(sys, "argv", ["earshot", "analyze", str(video), "--tap", "Ana@.3,.35",
                                      "--out", str(tmp_path / "out"), "--separator", "array",
                                      "--array", "array.wav", "--array-channels", "1,3,5,7"])
    cli.main()
    assert captured["options"].separator == "array"
    assert captured["options"].array_path == Path("array.wav")
    assert captured["options"].array_channels == [1, 3, 5, 7]


def test_envelope_stats_use_row_indexes():
    from tools.summarize_array_results import envelope_stats

    assert envelope_stats([[0.9, 0.8, 0.1], [0.8, 0.9, 0.1]]) == (0.9, 0.9)
    assert envelope_stats([[0.9, 0.1], [0.8, 0.7]]) == (0.8, 0.45)
