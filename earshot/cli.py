"""Command line: `python -m earshot analyze|serve|bench`."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(prog="earshot", description="Every voice at the table, captioned.")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyze", help="analyze a video into a run folder")
    a.add_argument("video", type=Path)
    a.add_argument("--tap", action="append", required=True,
                   help='person to follow: "Name@x,y" (fractions of width/height on frame 0), '
                        'or "Name@x,y#frame"; repeat per person')
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--separator", choices=["samaudio", "lite"], default="samaudio")
    a.add_argument("--prompt", default="", help='SAM Audio text prompt alongside the visual one, e.g. "speech"')
    a.add_argument("--text-features", type=Path,
                   help="precomputed SAM Audio text features (default: assets/text_features.npz; no T5 at runtime)")
    a.add_argument("--allow-t5", action="store_true",
                   help="let SAM Audio run its own T5 text encoder (only if organizers allow it)")
    a.add_argument("--no-spark", action="store_true")
    a.add_argument("--catchup-every", type=float, default=10.0)
    a.add_argument("--replay", action="store_true", help="use cached model responses only (no API key)")

    s = sub.add_parser("serve", help="open the viewer for a run folder")
    s.add_argument("run", type=Path, nargs="?", help="run folder (defaults to demo in replay or runs/<video> in setup)")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--replay", action="store_true")
    s.add_argument("--setup", type=Path, help="show the tap-to-start screen for this recorded video")
    s.add_argument("--separator", choices=["samaudio", "lite"], default="lite")

    b = sub.add_parser("bench", help="score runs against ground truth (Dinner Table Bench)")
    b.add_argument("run", type=Path)
    b.add_argument("--truth", type=Path, required=True, help="truth JSON (see bench/README.md)")
    b.add_argument("--out", type=Path)
    b.add_argument("--repeat", type=int,
                   help="re-run Voice transcription N times with repeat-specific cache keys")

    e = sub.add_parser("export", help="export per-person subtitles")
    e.add_argument("run", type=Path)
    e.add_argument("--vtt", type=Path)
    e.add_argument("--srt", type=Path)

    args = p.parse_args()
    if getattr(args, "replay", False):
        os.environ["EARSHOT_REPLAY"] = "1"

    if args.cmd == "analyze":
        from .pipeline import Options, analyze
        from .tracking import Tap

        doc = analyze(args.video, [Tap.parse(t) for t in args.tap], args.out, Options(
            separator=args.separator, replay=args.replay, text_features=args.text_features,
            allow_t5=args.allow_t5, prompt=args.prompt, spark=not args.no_spark, catchup_every=args.catchup_every))
        print(f"wrote {doc}\nview it: python -m earshot serve {args.out}")
    elif args.cmd == "serve":
        from .server import serve

        if not args.run and not args.setup:
            s.error("provide a run folder or --setup VIDEO")
        run = args.run
        if run is None:
            replay_demo = Path("demo/ami_meeting")
            run = replay_demo if args.replay and replay_demo.exists() else Path("runs") / args.setup.stem
        serve(run, args.port, replay=True if args.replay else None, setup=args.setup, separator=args.separator)
    elif args.cmd == "bench":
        from .bench import run_bench

        run_bench(args.run, args.truth, args.out, repeat=args.repeat)
    elif args.cmd == "export":
        from .export import export

        if not args.vtt and not args.srt:
            e.error("provide --vtt and/or --srt")
        export(args.run, args.vtt, args.srt)


if __name__ == "__main__":
    main()
