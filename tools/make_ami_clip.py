"""Build Earshot's public AMI ES2008a benchmark clip and word-level truth."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np

from earshot.media import read_audio

MIRROR = "https://groups.inf.ed.ac.uk/ami/AMICorpusMirror/amicorpus/ES2008a"
ANNOTATIONS = "https://groups.inf.ed.ac.uk/ami/AMICorpusAnnotations/ami_public_manual_1.6.2.zip"
START = 745.0
DURATION = 75.0
FPS = 25
SAMPLE_RATE = 48_000
PEOPLE = (
    ("Speaker A", "A", "Headset-0", "Closeup4"),
    ("Speaker B", "B", "Headset-1", "Closeup2"),
    ("Speaker C", "C", "Headset-2", "Closeup3"),
    ("Speaker D", "D", "Headset-3", "Closeup1"),
)
TAPS = (
    "--tap \"Speaker A@0.25,0.29\" --tap \"Speaker B@0.80,0.36\" "
    "--tap \"Speaker C@0.31,0.78\" --tap \"Speaker D@0.71,0.78\"\n"
)
ATTRIBUTION = """# AMI Meeting Corpus attribution

Contains material from the AMI Meeting Corpus (meeting ES2008a), © University of Edinburgh and AMI Consortium, licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Carletta, J. et al. (2005). The AMI Meeting Corpus: A Pre-Announcement. MLMI 2005, LNCS 3869.

Edited: four close-up cameras arranged in a 2×2 grid, cut to 12:25–13:40, audio from the far-field microphone Array1-01. `clip_cleanmic.mp4` instead uses Mix-Headset. Speaker labels A–D follow AMI's meeting metadata; no participant identity codes are used.
"""


def download(url: str, destination: Path) -> None:
    if destination.exists() and destination.stat().st_size:
        print(f"Cached {destination.name}", flush=True)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "Earshot-AMI-builder/1.0"})
    print(f"Downloading {url}", flush=True)
    with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as output:
        shutil.copyfileobj(response, output, length=1024 * 1024)
    partial.replace(destination)


def truth_from_annotations(archive: Path) -> dict:
    words = []
    with zipfile.ZipFile(archive) as annotations:
        members = {Path(name).name: name for name in annotations.namelist()}
        for person, agent, _, _ in PEOPLE:
            filename = f"ES2008a.{agent}.words.xml"
            if filename not in members:
                raise ValueError(f"Missing {filename} in {archive}")
            root = ET.fromstring(annotations.read(members[filename]))
            for element in root.iter():
                if element.tag.rsplit("}", 1)[-1] != "w":
                    continue
                if element.get("punc", "").lower() == "true":
                    continue
                start_attr, end_attr = element.get("starttime"), element.get("endtime")
                text = (element.text or "").strip()
                if start_attr is None or end_attr is None or not text:
                    continue
                start, end = float(start_attr), float(end_attr)
                if not START <= (start + end) / 2 < START + DURATION:
                    continue
                words.append({
                    "person": person,
                    "start": round(start - START, 3),
                    "end": round(end - START, 3),
                    "text": text,
                })
    words.sort(key=lambda word: (word["start"], word["end"], word["person"]))
    return {
        "source": "AMI Meeting Corpus ES2008a, CC BY 4.0",
        "window": [START, START + DURATION],
        "mixture": "Array1-01",
        "people": {
            person: " ".join(word["text"] for word in words if word["person"] == person)
            for person, _, _, _ in PEOPLE
        },
        "words": words,
        "reference_tracks": {
            person: f"ref_{agent}.wav" for person, agent, _, _ in PEOPLE
        },
    }


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def make_grid(cache: Path, output: Path, mixture: str) -> None:
    if output.exists():
        print(f"Cached {output}", flush=True)
        return
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    for _, _, _, camera in PEOPLE:
        command += ["-i", str(cache / "video" / f"ES2008a.{camera}.avi")]
    command += ["-i", str(cache / "audio" / f"ES2008a.{mixture}.wav")]
    video_filters = ";".join(
        f"[{index}:v]fps={FPS},setsar=1[v{index}]" for index in range(4)
    )
    command += [
        "-ss", str(START), "-t", str(DURATION),
        "-filter_complex_threads", "1",
        "-filter_complex",
        video_filters + ";[v0][v1][v2][v3]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[grid];"
        "[4:a]aresample=48000[audio]",
        "-map", "[grid]", "-map", "[audio]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-g", str(FPS), "-c:a", "aac", "-b:a", "160k", "-ac", "1", "-ar", str(SAMPLE_RATE),
        "-movflags", "+faststart", "-shortest", str(output),
    ]
    run(*command)


def cut_references(cache: Path, output: Path) -> None:
    for person, _, headset, _ in PEOPLE:
        destination = output / f"ref_{person[-1]}.wav"
        if destination.exists():
            continue
        run(
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(cache / "audio" / f"ES2008a.{headset}.wav"),
            "-ss", str(START), "-t", str(DURATION), "-vn", "-ac", "1",
            "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(destination),
        )


def motion_envelope(video: Path) -> np.ndarray:
    width, height = 88, 72
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(video),
        "-ss", str(START), "-t", str(DURATION), "-an", "-vf", f"fps={FPS},scale={width}:{height}",
        "-f", "rawvideo", "-pix_fmt", "gray", "-",
    ]
    raw = subprocess.run(command, check=True, capture_output=True).stdout
    frames = np.frombuffer(raw, dtype=np.uint8)
    frames = frames[: frames.size // (width * height) * width * height]
    frames = frames.reshape(-1, height, width).astype(np.float32)
    lower_centre = frames[:, height // 2 :, width // 4 : 3 * width // 4]
    return np.mean(np.abs(np.diff(lower_centre, axis=0)), axis=(1, 2))


def energy_envelope(audio: Path) -> np.ndarray:
    rate = 16_000
    samples = read_audio(audio, sr=rate, start=START, seconds=DURATION)
    frame_size = rate // FPS
    samples = samples[: samples.size // frame_size * frame_size]
    frames = samples.reshape(-1, frame_size)
    return np.sqrt(np.mean(frames * frames, axis=1))


def best_lag(energy: np.ndarray, motion: np.ndarray, max_lag_seconds: float = 1.0) -> tuple[float, float]:
    size = min(energy.size, motion.size)
    energy, motion = energy[:size], motion[:size]
    best = (0, -1.0)
    for lag in range(-int(max_lag_seconds * FPS), int(max_lag_seconds * FPS) + 1):
        if lag < 0:
            left, right = energy[-lag:], motion[:lag]
        elif lag > 0:
            left, right = energy[:-lag], motion[lag:]
        else:
            left, right = energy, motion
        left = left - np.mean(left)
        right = right - np.mean(right)
        denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
        correlation = float(np.dot(left, right) / denominator) if denominator else 0.0
        if correlation > best[1]:
            best = (lag, correlation)
    return best[0] / FPS, best[1]


def check_sync(cache: Path, output: Path) -> None:
    rows = []
    for person, _, headset, camera in PEOPLE:
        energy = energy_envelope(cache / "audio" / f"ES2008a.{headset}.wav")
        motion = motion_envelope(cache / "video" / f"ES2008a.{camera}.avi")
        lag, correlation = best_lag(energy, motion)
        row = {"person": person, "lag_seconds": round(lag, 3), "correlation": round(correlation, 4)}
        rows.append(row)
        print(f"Sync {person}: lag={lag:+.3f}s correlation={correlation:.3f}", flush=True)
        if abs(lag) > 0.2:
            print(f"WARNING: {person} sync lag exceeds 0.2 s", flush=True)
    (output / "sync.json").write_text(json.dumps(rows, indent=2) + "\n")


def build(output: Path, cache: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    archive = cache / "ami_public_manual_1.6.2.zip"
    download(ANNOTATIONS, archive)
    for _, _, headset, camera in PEOPLE:
        download(f"{MIRROR}/video/ES2008a.{camera}.avi", cache / "video" / f"ES2008a.{camera}.avi")
        download(f"{MIRROR}/audio/ES2008a.{headset}.wav", cache / "audio" / f"ES2008a.{headset}.wav")
    for mixture in ("Array1-01", "Mix-Headset"):
        download(f"{MIRROR}/audio/ES2008a.{mixture}.wav", cache / "audio" / f"ES2008a.{mixture}.wav")

    make_grid(cache, output / "clip.mp4", "Array1-01")
    make_grid(cache, output / "clip_cleanmic.mp4", "Mix-Headset")
    cut_references(cache, output)
    truth = json.dumps(truth_from_annotations(archive), ensure_ascii=False, indent=2) + "\n"
    (output / "truth.json").write_text(truth)
    (output / "taps.txt").write_text(TAPS)
    (output / "ATTRIBUTION.md").write_text(ATTRIBUTION)
    if not (output / "frame0.png").exists():
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(output / "clip.mp4"),
            "-frames:v", "1", str(output / "frame0.png"))
    check_sync(cache, output)
    print(f"Wrote {len(json.loads(truth)['words'])} truth words to {output / 'truth.json'}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path("bench/.ami_cache/ES2008a"))
    args = parser.parse_args()
    build(args.out, args.cache)


if __name__ == "__main__":
    main()
