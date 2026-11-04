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

MEETING = "ES2008a"
MIRROR = f"https://groups.inf.ed.ac.uk/ami/AMICorpusMirror/amicorpus/{MEETING}"
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
DEFAULT_TAPS = ["Speaker A@0.25,0.29", "Speaker B@0.80,0.36", "Speaker C@0.31,0.78", "Speaker D@0.71,0.78"]
TAPS = " ".join(f'--tap "{tap}"' for tap in DEFAULT_TAPS) + "\n"
ATTRIBUTION = """# AMI Meeting Corpus attribution

Contains material from the AMI Meeting Corpus (meeting {meeting}), © University of Edinburgh and AMI Consortium, licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Carletta, J. et al. (2005). The AMI Meeting Corpus: A Pre-Announcement. MLMI 2005, LNCS 3869.

Edited: four close-up cameras arranged in a 2×2 grid, cut to {start:g}–{end:g} seconds, audio from the far-field microphone Array1-01. `clip_cleanmic.mp4` instead uses Mix-Headset. Speaker labels A–D follow AMI's meeting metadata; no participant identity codes are used. Tap coordinates are supplied separately in taps.txt after inspecting frame0.png.
"""


def download(url: str, destination: Path) -> None:
    import time
    import urllib.error

    if destination.exists() and destination.stat().st_size:
        print(f"Cached {destination.name}", flush=True)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "Earshot-AMI-builder/1.0"})
    for attempt in range(5):
        try:
            print(f"Downloading {url}", flush=True)
            with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as output:
                shutil.copyfileobj(response, output, length=1024 * 1024)
            partial.replace(destination)
            return
        except (urllib.error.URLError, TimeoutError) as error:
            if attempt == 4:
                raise
            delay = 2 ** attempt
            print(f"Download failed ({error}); retrying in {delay}s", flush=True)
            time.sleep(delay)


def truth_from_annotations(archive: Path) -> dict:
    words = []
    with zipfile.ZipFile(archive) as annotations:
        members = {Path(name).name: name for name in annotations.namelist()}
        for person, agent, _, _ in PEOPLE:
            filename = f"{MEETING}.{agent}.words.xml"
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
        "source": f"AMI Meeting Corpus {MEETING}, CC BY 4.0",
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
        command += ["-i", str(cache / "video" / f"{MEETING}.{camera}.avi")]
    command += ["-i", str(cache / "audio" / f"{MEETING}.{mixture}.wav")]
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
            "-i", str(cache / "audio" / f"{MEETING}.{headset}.wav"),
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
        energy = energy_envelope(cache / "audio" / f"{MEETING}.{headset}.wav")
        motion = motion_envelope(cache / "video" / f"{MEETING}.{camera}.avi")
        lag, correlation = best_lag(energy, motion)
        row = {"person": person, "lag_seconds": round(lag, 3), "correlation": round(correlation, 4)}
        rows.append(row)
        print(f"Sync {person}: lag={lag:+.3f}s correlation={correlation:.3f}", flush=True)
        if abs(lag) > 0.2:
            print(f"WARNING: {person} sync lag exceeds 0.2 s", flush=True)
    (output / "sync.json").write_text(json.dumps(rows, indent=2) + "\n")


def make_array(output: Path, cache: Path) -> None:
    import wave

    destination = output / "array.wav"
    if destination.exists() and destination.stat().st_size:
        print(f"Cached {destination}", flush=True)
        return
    channels = []
    for channel in range(1, 9):
        path = cache / "audio" / f"{MEETING}.Array1-{channel:02d}.wav"
        download(f"{MIRROR}/audio/{MEETING}.Array1-{channel:02d}.wav", path)
        with wave.open(str(path), "rb") as source:
            if source.getnchannels() != 1 or source.getsampwidth() != 2 or source.getframerate() != 16_000:
                raise ValueError(f"Expected 16 kHz mono PCM16: {path}")
            channels.append(np.frombuffer(source.readframes(source.getnframes()), dtype="<i2"))
    first = int(round(START * 16_000))
    count = int(round(DURATION * 16_000))
    if min(channel.size for channel in channels) < first + count:
        raise ValueError("Array source is shorter than the requested window")
    frames = np.stack([channel[first:first + count] for channel in channels], axis=1)
    output.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(".part")
    with wave.open(str(partial), "wb") as target:
        target.setnchannels(8)
        target.setsampwidth(2)
        target.setframerate(16_000)
        target.writeframes(frames.astype("<i2").tobytes())
    partial.replace(destination)
    print(f"Wrote {frames.shape[0]} frames x 8 channels at 16 kHz to {destination}", flush=True)


def build(output: Path, cache: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    output.mkdir(parents=True, exist_ok=True)
    archive = cache / "ami_public_manual_1.6.2.zip"
    download(ANNOTATIONS, archive)
    sources = [("video", camera) for _, _, _, camera in PEOPLE]
    sources += [("audio", headset) for _, _, headset, _ in PEOPLE]
    sources += [("audio", mixture) for mixture in ("Array1-01", "Mix-Headset")]

    def fetch(source):
        kind, name = source
        suffix = "avi" if kind == "video" else "wav"
        download(f"{MIRROR}/{kind}/{MEETING}.{name}.{suffix}", cache / kind / f"{MEETING}.{name}.{suffix}")

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(fetch, sources))
    make_grid(cache, output / "clip.mp4", "Array1-01")
    make_grid(cache, output / "clip_cleanmic.mp4", "Mix-Headset")
    cut_references(cache, output)
    truth = json.dumps(truth_from_annotations(archive), ensure_ascii=False, indent=2) + "\n"
    (output / "truth.json").write_text(truth)
    (output / "taps.txt").write_text(TAPS)
    (output / "ATTRIBUTION.md").write_text(ATTRIBUTION.format(meeting=MEETING, start=START, end=START + DURATION))
    if not (output / "frame0.png").exists():
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(output / "clip.mp4"),
            "-frames:v", "1", str(output / "frame0.png"))
    check_sync(cache, output)
    print(f"Wrote {len(json.loads(truth)['words'])} truth words to {output / 'truth.json'}", flush=True)


def main() -> None:
    global START, MEETING, MIRROR, TAPS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--meeting", choices=["ES2008a", "ES2008b", "ES2008c"], default=MEETING)
    parser.add_argument("--cache", type=Path, help="source cache (default: bench/.ami_cache/<meeting>)")
    parser.add_argument("--start", type=float, default=START, help="window start in seconds (default: 745)")
    parser.add_argument("--tap", action="append", help="Name@x,y on the verified first frame; repeatable")
    parser.add_argument("--array", action="store_true", help="download all eight microphones and write array.wav")
    args = parser.parse_args()
    START, MEETING = args.start, args.meeting
    MIRROR = f"https://groups.inf.ed.ac.uk/ami/AMICorpusMirror/amicorpus/{MEETING}"
    TAPS = " ".join(f'--tap "{tap}"' for tap in args.tap or DEFAULT_TAPS) + "\n"
    cache = args.cache or Path("bench/.ami_cache") / MEETING
    if args.array:
        make_array(args.out, cache)
    else:
        build(args.out, cache)


if __name__ == "__main__":
    main()
