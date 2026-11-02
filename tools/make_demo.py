"""Package a real Earshot run as a lightweight, key-free replay demo."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from earshot.media import ffmpeg


def build_demo(source: Path, destination: Path, attribution: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "calls").mkdir(exist_ok=True)
    for name in ("analysis.mp4", "tracks.json", "calls.jsonl"):
        shutil.copy2(source / name, destination / name)
    for cached in (source / "calls").glob("*.json"):
        shutil.copy2(cached, destination / "calls" / cached.name)
    shutil.copy2(attribution, destination / "ATTRIBUTION.md")

    doc = json.loads((source / "earshot.json").read_text())
    for person in doc["people"]:
        stem = person.get("stem")
        if not stem:
            continue
        target = Path(stem).with_suffix(".m4a")
        (destination / target.parent).mkdir(parents=True, exist_ok=True)
        ffmpeg("-i", str(source / stem), "-c:a", "aac", "-b:a", "96k", str(destination / target))
        person["stem"] = target.as_posix()
    (destination / "earshot.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--attribution", type=Path, required=True)
    args = parser.parse_args()
    build_demo(args.source, args.destination, args.attribution)
    size = sum(path.stat().st_size for path in args.destination.rglob("*") if path.is_file())
    print(f"wrote {args.destination} ({size / 1_000_000:.2f} MB)")


if __name__ == "__main__":
    main()
