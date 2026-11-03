"""Run the real array channel-subset analyses and three-repeat benches."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

TAPS = ["Speaker A@0.25,0.29", "Speaker B@0.80,0.36", "Speaker C@0.31,0.78", "Speaker D@0.71,0.78"]
CHANNELS = {8: list(range(1, 9)), 5: [1, 2, 3, 4, 5], 4: [1, 3, 5, 7]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window", choices=["745", "635"], required=True)
    args = parser.parse_args()
    source = Path("runs/ami_lite" if args.window == "745" else "runs/ami_lite_635")
    bench = Path("bench/ami_ES2008a" if args.window == "745" else "bench/ami_ES2008a_635")
    for count, channels in CHANNELS.items():
        name = f"ami_array_{count}" + ("" if args.window == "745" else "_635")
        run_dir = Path("runs") / name
        channel_arg = ",".join(str(channel) for channel in channels)
        print(f"ANALYZE {name}: channels {channel_arg}", flush=True)
        subprocess.run([
            sys.executable, "-m", "earshot", "analyze", str(source / "analysis.mp4"),
            *(item for tap in TAPS for item in ("--tap", tap)),
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
