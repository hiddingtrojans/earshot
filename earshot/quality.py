"""Keep experimental listening claims tied to the actual benchmark artifact."""

from __future__ import annotations

import json
from pathlib import Path


def array_quality(run: Path) -> dict:
    quality = {
        "status": "experimental",
        "decision": "not yet evaluated",
        "overlap_recovery": "Experimental isolated listening, not verified overlap recovery.",
        "media_sync": "Camera-motion/audio lag estimates are not a verified lip-sync correction; none is applied.",
    }
    path = run / "bench_array.json"
    if not path.exists():
        return quality
    result = json.loads(path.read_text())
    summary = result.get("summary", {})
    try:
        recall = summary["earshot"]["overlap_recall"]["mean"]
        attribution = summary["earshot"]["attribution"]["mean"]
        threshold = max(summary[baseline]["overlap_recall"]["mean"]
                        for baseline in ("baseline", "delay_sum")) + 0.10
    except (KeyError, TypeError):
        return quality
    passed = attribution >= 0.80 and recall >= threshold
    quality.update({
        "decision": "GO on this window" if passed else "NO-GO on this window",
        "gate": {"overlap_recall": recall, "required_at_least": round(threshold, 3),
                 "right_person": attribution, "right_person_required_at_least": 0.80},
        "summary": summary,
        "repeat_count": result.get("repeat_count", 1),
        "benchmark_source": "AMI 8-mic meeting-room array; see bench/RESULTS.md",
    })
    return quality
