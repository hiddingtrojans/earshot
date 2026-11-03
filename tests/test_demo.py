import json
import shutil
import subprocess
import wave
from pathlib import Path

import pytest

import numpy as np

from tools.make_demo import build_demo


def test_demo_copies_json_cache_and_converts_stems(tmp_path):
    source = tmp_path / "source"
    (source / "calls").mkdir(parents=True)
    (source / "stems").mkdir()
    (source / "analysis.mp4").write_bytes(b"public test video")
    (source / "tracks.json").write_text("{}")
    (source / "calls.jsonl").write_text("{}\n")
    (source / "calls" / "response.json").write_text("{}")
    (source / "calls" / "sep_private.npy").write_bytes(b"not copied")
    (source / "corrections.json").write_text('[{"from": 0, "to": 1, "tap": [0.8, 0.36, 0]}]')
    attribution = tmp_path / "ATTRIBUTION.md"
    attribution.write_text("AMI test attribution")
    pcm = (np.sin(np.arange(4800) * 0.1) * 1000).astype("<i2")
    with wave.open(str(source / "stems" / "voice.wav"), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(48000)
        output.writeframes(pcm.tobytes())
    doc = {"video": "analysis.mp4", "people": [{"name": "Speaker A", "stem": "stems/voice.wav"}],
           "array": {"delay_sum": "array_delay_sum.wav"}}
    (source / "array_delay_sum.wav").write_bytes(b"public test audio")
    (source / "earshot.json").write_text(json.dumps(doc))

    destination = tmp_path / "demo"
    build_demo(source, destination, attribution)
    assert (destination / "stems" / "voice.m4a").stat().st_size > 0
    assert not (destination / "stems" / "voice.wav").exists()
    assert not (destination / "calls" / "sep_private.npy").exists()
    assert json.loads((destination / "earshot.json").read_text())["people"][0]["stem"] == "stems/voice.m4a"
    assert (destination / "ATTRIBUTION.md").read_text() == "AMI test attribution"
    assert (destination / "corrections.json").exists()
    assert (destination / "array_delay_sum.wav").read_bytes() == b"public test audio"


def test_demo_lite_has_no_invented_stems(tmp_path):
    source = tmp_path / "source"
    (source / "calls").mkdir(parents=True)
    (source / "analysis.mp4").write_bytes(b"public test video")
    (source / "tracks.json").write_text("{}")
    (source / "calls.jsonl").write_text("")
    (source / "earshot.json").write_text(json.dumps({"people": [{"name": "Speaker A", "stem": None}]}))
    attribution = tmp_path / "ATTRIBUTION.md"
    attribution.write_text("AMI")
    destination = tmp_path / "demo"
    build_demo(source, destination, attribution)
    assert json.loads((destination / "earshot.json").read_text())["people"][0]["stem"] is None
    assert not (destination / "stems").exists()


@pytest.mark.skipif(shutil.which("node") is None, reason="optional JavaScript syntax check needs Node.js")
def test_viewer_javascript_syntax():
    html = (Path(__file__).parent.parent / "web" / "index.html").read_text()
    script = html.split("<script>", 1)[1].split("</script>", 1)[0]
    subprocess.run(["node", "--check"], input=script, text=True, check=True, capture_output=True)
