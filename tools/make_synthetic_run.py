#!/usr/bin/env python3
"""Build a SYNTHETIC run folder (fake model outputs) for viewer development.

    python tools/make_synthetic_run.py runs/synthetic
    python -m earshot serve runs/synthetic --replay
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import synthetic  # noqa: E402

from earshot import pipeline, separation, spark  # noqa: E402
from earshot.tracking import Tap  # noqa: E402


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "runs/synthetic")
    out.mkdir(parents=True, exist_ok=True)
    video = out / "source.mp4"
    synthetic.make_video(video)
    pipeline.track_people = lambda v, taps, info, calls: synthetic.fake_tracks([t.name for t in taps], info)
    pipeline.transcribe = synthetic.fake_transcribe
    separation.SamAudioSeparator = synthetic.FakeSeparator
    spark._respond = synthetic.fake_respond
    pipeline.analyze(video, [Tap("Ana", 0.30, 0.35), Tap("Raúl", 0.70, 0.35)], out,
                     pipeline.Options(separator="samaudio", catchup_every=5))
    synthetic.write_fake_calls(out)
    print(f"SYNTHETIC run written to {out}")


if __name__ == "__main__":
    main()
