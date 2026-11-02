import json

import pytest

from tools.spend_report import collect, price_call


def test_prices_real_usage_and_ignores_cache_hits(tmp_path):
    run = tmp_path / "run"
    (run / "calls").mkdir(parents=True)
    rows = [
        {"model": "sam-3.1", "purpose": "track", "where": "hosted", "cache": "miss", "key": "sam",
         "usage": {"video_frames_processed": 250}},
        {"model": "muse-voice-transcribe-1.0", "purpose": "voice", "where": "hosted", "cache": "miss",
         "key": "voice", "audio_seconds": 10.0},
        {"model": "muse-spark-1.3", "purpose": "spark", "where": "hosted", "cache": "miss", "key": "spark",
         "usage": {"input_tokens": 1000, "input_tokens_details": {"cached_tokens": 200}, "output_tokens": 500}},
        {"model": "sam-3.1", "purpose": "cached", "where": "hosted", "cache": "hit", "key": "sam"},
    ]
    (run / "calls.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    (run / "calls" / "voice.json").write_text(json.dumps({"result": {"audioDurationMs": 10080}}))
    entries = collect([run])
    assert [entry["cost"] for entry in entries] == pytest.approx([0.05, 0.000504, 0.003155])
    assert len(entries) == 3


def test_unknown_hosted_model_fails_closed():
    with pytest.raises(ValueError, match="No list-price rule"):
        price_call({"model": "unknown", "where": "hosted", "cache": "miss"}, {})
