"""Calculate estimated hosted-model spend from real Earshot call logs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CAP_USD = 20.0
PRICES = {
    "sam_frames_per_1000": 0.20,
    "voice_per_hour": 0.18,
    "spark_input_per_million": 1.25,
    "spark_cached_input_per_million": 0.15,
    "spark_output_per_million": 4.25,
}


def price_call(row: dict, cached_response: dict) -> tuple[str, float]:
    if row.get("where") == "local" or row.get("cache") != "miss":
        return "local/cached", 0.0
    model = row.get("model")
    if model == "files":
        return "file upload", 0.0
    if model == "sam-3.1":
        frames = (row.get("usage") or {}).get("video_frames_processed")
        if frames is None:
            raise ValueError(f"SAM call {row.get('key')} has no video_frames_processed usage")
        return f"{frames} video frames", frames / 1000 * PRICES["sam_frames_per_1000"]
    if model == "muse-voice-transcribe-1.0":
        milliseconds = cached_response.get("audioDurationMs")
        seconds = milliseconds / 1000 if milliseconds is not None else row.get("audio_seconds")
        if seconds is None:
            raise ValueError(f"Voice call {row.get('key')} has no audio duration")
        return f"{seconds:.3f} audio seconds", seconds / 3600 * PRICES["voice_per_hour"]
    if model == "muse-spark-1.3":
        usage = row.get("usage") or {}
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        if input_tokens is None or output_tokens is None:
            raise ValueError(f"Spark call {row.get('key')} has no token usage")
        cached = (usage.get("input_tokens_details") or {}).get("cached_tokens") or 0
        uncached = input_tokens - cached
        cost = (uncached * PRICES["spark_input_per_million"]
                + cached * PRICES["spark_cached_input_per_million"]
                + output_tokens * PRICES["spark_output_per_million"]) / 1_000_000
        return f"{uncached} uncached + {cached} cached input; {output_tokens} output tokens", cost
    raise ValueError(f"No list-price rule for hosted model {model!r}")


def collect(runs: list[Path]) -> list[dict]:
    entries = []
    for run in runs:
        log = run / "calls.jsonl"
        if not log.exists():
            continue
        for line in log.read_text().splitlines():
            row = json.loads(line)
            cache_path = run / "calls" / f"{row['key']}.json"
            cached = json.loads(cache_path.read_text()) if cache_path.exists() else {}
            usage, cost = price_call(row, cached.get("result") or {})
            if row.get("cache") == "miss":
                entries.append({"run": str(run), "model": row["model"], "purpose": row["purpose"],
                                "usage": usage, "cost": cost})
    return entries


def markdown(entries: list[dict]) -> str:
    total = sum(entry["cost"] for entry in entries)
    lines = [
        "# Estimated Meta API spend", "",
        f"Run cap: **${CAP_USD:.2f}**. **Running total: ${total:.6f}.**", "",
        "Generated from `cache=miss` rows in the supplied run folders. Cache hits and local models add $0. "
        "Prices: SAM $0.20/1,000 processed video frames; Voice $0.18/audio hour; Spark $1.25/1M uncached "
        "input, $0.15/1M cached input, and $4.25/1M output tokens. Unknown hosted models are an error, not a zero.", "",
        "| Run | Model | Purpose | Actual usage | Estimated USD |", "|---|---|---|---|---:|",
    ]
    lines += [f"| {entry['run']} | `{entry['model']}` | {entry['purpose']} | {entry['usage']} | "
              f"${entry['cost']:.6f} |" for entry in entries]
    lines += ["", f"Total before rounding: ${total:.12f}. Stop new live calls before the cap is reached.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", type=Path, nargs="+")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    entries = collect(args.runs)
    report = markdown(entries)
    if args.out:
        args.out.write_text(report)
    print(f"calls={len(entries)} estimated_spend=${sum(entry['cost'] for entry in entries):.6f} cap=${CAP_USD:.2f}")


if __name__ == "__main__":
    main()
