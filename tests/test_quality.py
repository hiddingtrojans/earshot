import json

from earshot.quality import array_quality


def test_array_gate_uses_better_baseline_and_fixed_thresholds(tmp_path):
    result = {"repeat_count": 3, "summary": {
        "earshot": {"attribution": {"mean": 0.844}, "overlap_recall": {"mean": 0.605}},
        "baseline": {"overlap_recall": {"mean": 0.495}},
        "delay_sum": {"overlap_recall": {"mean": 0.522}},
    }}
    (tmp_path / "bench_array.json").write_text(json.dumps(result))
    quality = array_quality(tmp_path)
    assert quality["status"] == "experimental"
    assert quality["decision"] == "NO-GO on this window"
    assert quality["gate"]["required_at_least"] == 0.622
    assert "none is applied" in quality["media_sync"]


def test_array_gate_does_not_hide_a_measured_pass(tmp_path):
    result = {"repeat_count": 3, "summary": {
        "earshot": {"attribution": {"mean": 0.85}, "overlap_recall": {"mean": 0.70}},
        "baseline": {"overlap_recall": {"mean": 0.50}},
        "delay_sum": {"overlap_recall": {"mean": 0.52}},
    }}
    (tmp_path / "bench_array.json").write_text(json.dumps(result))
    assert array_quality(tmp_path)["decision"] == "GO on this window"
    assert array_quality(tmp_path)["status"] == "experimental"
