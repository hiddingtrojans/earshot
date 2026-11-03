"""Run the real array channel-subset analyses and three-repeat benches."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

TAPS = ["Speaker A@0.25,0.29", "Speaker B@0.80,0.36", "Speaker C@0.31,0.78", "Speaker D@0.71,0.78"]
CHANNELS = {8: list(range(1, 9)), 5: [1, 2, 3, 4, 5], 4: [1, 3, 5, 7]}


def read_taps(path: Path) -> list[str]:
    tokens = shlex.split(path.read_text())
    taps = [tokens[index + 1] for index, token in enumerate(tokens[:-1]) if token == "--tap"]
    if not taps:
        raise ValueError(f"No --tap entries in {path}")
    return taps


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window", type=int, required=True, help="window start in seconds (e.g. 745 or 150)")
    parser.add_argument("--meeting", choices=["ES2008a", "ES2008b"], default="ES2008a")
    parser.add_argument("--subsets", default="8,5,4", help="microphone counts to evaluate (default: 8,5,4)")
    args = parser.parse_args()
    suffix = "" if args.window == 745 else f"_{args.window}"
    bench = Path(f"bench/ami_{args.meeting}{suffix}")
    original = args.meeting == "ES2008a" and args.window in (745, 635)
    source = Path("runs/ami_lite" + suffix) / "analysis.mp4" if original else bench / "clip.mp4"
    taps = TAPS if original else read_taps(bench / "taps.txt")
    counts = [int(count) for count in args.subsets.split(",")]
    if any(count not in CHANNELS for count in counts):
        parser.error("--subsets may contain only 8, 5 and 4")
    for count in counts:
        channels = CHANNELS[count]
        name = f"ami_array_{count}{suffix}" if original else f"ami_{args.meeting.lower()}{suffix}_array_{count}"
        run_dir = Path("runs") / name
        channel_arg = ",".join(str(channel) for channel in channels)
        print(f"ANALYZE {name}: channels {channel_arg}", flush=True)
        subprocess.run([
            sys.executable, "-m", "earshot", "analyze", str(source),
            *(item for tap in taps for item in ("--tap", tap)),
            "--out", str(run_dir), "--separator", "array", "--array", str(bench / "array.wav"),
            "--array-channels", channel_arg, "--no-spark",
        ], check=True)
        print(f"BENCH {name}: three repeats", flush=True)
        subprocess.run([
            sys.executable, "-m", "earshot", "bench", str(run_dir), "--truth", str(bench / "truth.json"),
            "--repeat", "3", "--out", str(run_dir / "bench_array.json"),
        ], check=True)


if __name__ == "__main__":
    main()
