"""FFmpeg helpers. Plain signal processing only: no model-based filters."""

from __future__ import annotations

import json
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

SEPARATION_SR = 48_000  # SAM Audio
TRANSCRIBE_SR = 24_000  # Muse Voice Transcribe file endpoint accepts 16 or 24 kHz


def ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


@dataclass(frozen=True)
class VideoInfo:
    width: int
    height: int
    fps: float
    frames: int
    duration: float


def probe(path: Path) -> VideoInfo:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
         "-show_entries", "stream=width,height,avg_frame_rate,nb_read_frames:format=duration",
         "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout
    data = json.loads(out)
    stream = data["streams"][0]
    num, _, den = stream["avg_frame_rate"].partition("/")
    fps = float(num) / float(den or 1)
    return VideoInfo(
        width=int(stream["width"]), height=int(stream["height"]), fps=fps,
        frames=int(stream.get("nb_read_frames") or 0),
        duration=float(data["format"]["duration"]),
    )


def prepare_analysis_video(src: Path, dst: Path, max_edge: int = 960, fps: float | None = None) -> VideoInfo:
    """Constant-frame-rate H.264 copy with the longest edge capped, mono 48 kHz audio.

    Every later step (SAM 3.1 frame indexes, SAM Audio frames, UI playback) uses
    this one file, so frame indexes line up everywhere.
    """
    scale = f"scale='if(gt(iw,ih),min({max_edge},iw),-2)':'if(gt(iw,ih),-2,min({max_edge},ih))'"
    filters = [scale, "setsar=1"]
    if fps:
        filters.append(f"fps={fps}")
    ffmpeg(
        "-i", str(src), "-vf", ",".join(filters), "-fps_mode", "cfr",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-g", "25", "-c:a", "aac", "-b:a", "160k", "-ac", "1", "-ar", str(SEPARATION_SR),
        "-movflags", "+faststart", str(dst),
    )
    return probe(dst)


def read_audio(path: Path, sr: int = SEPARATION_SR, start: float | None = None,
               seconds: float | None = None) -> np.ndarray:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
    if start is not None:
        cmd += ["-ss", f"{start}"]
    if seconds is not None:
        cmd += ["-t", f"{seconds}"]
    cmd += ["-i", str(path), "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def write_wav(path: Path, audio: np.ndarray, sr: int) -> None:
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 1.0:
        audio = audio / peak
    pcm = (np.clip(audio, -1.0, 1.0) * 32767.0).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def resample(audio: np.ndarray, src_sr: int, dst_sr: int) -> np.ndarray:
    """Deterministic resampling through ffmpeg's swresample."""
    if src_sr == dst_sr:
        return audio.astype(np.float32)
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "f32le", "-ar", str(src_sr),
         "-ac", "1", "-i", "-", "-ar", str(dst_sr), "-f", "f32le", "-"],
        input=np.asarray(audio, dtype=np.float32).tobytes(), check=True, capture_output=True,
    )
    return np.frombuffer(proc.stdout, dtype=np.float32).copy()


def wav_bytes(audio: np.ndarray, sr: int) -> bytes:
    """16-bit mono WAV in memory (what the Voice Transcribe file endpoint takes)."""
    import io

    buf = io.BytesIO()
    pcm = (np.clip(np.asarray(audio, dtype=np.float32), -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()
