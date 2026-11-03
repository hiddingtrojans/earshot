import json

from earshot.calls import CallLog, content_key, response_metadata


def test_replay_reads_cache_without_mutating_provenance(tmp_path):
    key = content_key("model", "test")
    (tmp_path / "calls").mkdir()
    (tmp_path / "calls" / f"{key}.json").write_text(json.dumps({
        "meta": {"model": "model", "where": "local"}, "result": {"answer": 1},
    }))
    (tmp_path / "calls.jsonl").write_text("original log\n")
    calls = CallLog(tmp_path, replay=True)
    result = calls.cached(model="model", purpose="test", where="local", key_parts=(),
                          fn=lambda: (_ for _ in ()).throw(AssertionError("network call")))
    assert result == {"answer": 1}
    assert (tmp_path / "calls.jsonl").read_text() == "original log\n"


def test_response_metadata_captures_id_usage_and_header_fallback():
    assert response_metadata({"id": "resp_123", "usage": {"input_tokens": 12}}) == {
        "request_id": "resp_123", "usage": {"input_tokens": 12},
    }
    assert response_metadata({}, {"X-Request-ID": "req_456"}) == {"request_id": "req_456"}
    assert response_metadata({"sessionId": "voyager/transcribe/ABC"}) == {
        "request_id": "voyager/transcribe/ABC",
    }
    assert response_metadata({}) == {}
