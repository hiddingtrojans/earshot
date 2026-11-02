from earshot.calls import response_metadata


def test_response_metadata_captures_id_usage_and_header_fallback():
    assert response_metadata({"id": "resp_123", "usage": {"input_tokens": 12}}) == {
        "request_id": "resp_123", "usage": {"input_tokens": 12},
    }
    assert response_metadata({}, {"X-Request-ID": "req_456"}) == {"request_id": "req_456"}
    assert response_metadata({"sessionId": "voyager/transcribe/ABC"}) == {
        "request_id": "voyager/transcribe/ABC",
    }
    assert response_metadata({}) == {}
