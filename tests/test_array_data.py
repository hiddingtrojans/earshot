import io
import urllib.error
import wave
from pathlib import Path

import numpy as np

from tools import make_ami_clip


def test_array_download_retries_403(tmp_path, monkeypatch):
    calls = []

    def response(url, timeout):
        calls.append(url)
        if len(calls) == 1:
            raise urllib.error.HTTPError(url, 403, "Forbidden", None, None)
        return io.BytesIO(b"public audio")

    monkeypatch.setattr("urllib.request.urlopen", response)
    monkeypatch.setattr("time.sleep", lambda seconds: None)
    make_ami_clip.download("https://example.invalid/audio", tmp_path / "array.wav")
    assert len(calls) == 2
    assert (tmp_path / "array.wav").read_bytes() == b"public audio"


def test_make_array_writes_eight_channels_at_16khz(tmp_path, monkeypatch):
    monkeypatch.setattr(make_ami_clip, "START", 0)
    monkeypatch.setattr(make_ami_clip, "DURATION", 0.01)
    for channel in range(1, 9):
        path = tmp_path / "cache" / "audio" / f"ES2008a.Array1-{channel:02d}.wav"
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(16_000)
            output.writeframes(np.full(160, channel, dtype="<i2").tobytes())
    make_ami_clip.make_array(tmp_path / "out", tmp_path / "cache")
    with wave.open(str(tmp_path / "out" / "array.wav"), "rb") as source:
        assert source.getnchannels() == 8
        assert source.getframerate() == 16_000
        frames = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2").reshape(-1, 8)
    assert frames.shape == (160, 8)
    assert frames[0].tolist() == list(range(1, 9))


def test_second_meeting_uses_its_own_source_and_taps(tmp_path, monkeypatch):
    captured = {}

    def fake_build(output, cache):
        captured.update(output=output, cache=cache, mirror=make_ami_clip.MIRROR,
                        meeting=make_ami_clip.MEETING, taps=make_ami_clip.TAPS)

    monkeypatch.setattr(make_ami_clip, "build", fake_build)
    for name in ("MEETING", "MIRROR", "TAPS", "START"):
        monkeypatch.setattr(make_ami_clip, name, getattr(make_ami_clip, name))
    monkeypatch.setattr("sys.argv", ["make_ami_clip", "--meeting", "ES2008b", "--out", str(tmp_path / "clip"),
                                    "--tap", "Speaker A@0.1,0.2"])
    make_ami_clip.main()
    assert captured["mirror"].endswith("/ES2008b")
    assert captured["cache"] == Path("bench/.ami_cache/ES2008b")
    assert captured["meeting"] == "ES2008b"
    assert captured["taps"] == '--tap "Speaker A@0.1,0.2"\n'


def test_independent_bench_reads_verified_taps(tmp_path):
    from tools.run_array_benches import read_taps

    path = tmp_path / "taps.txt"
    path.write_text('--tap "Speaker A@0.7,0.3" --tap "Speaker C@0.2,0.8"\n')
    assert read_taps(path) == ["Speaker A@0.7,0.3", "Speaker C@0.2,0.8"]
