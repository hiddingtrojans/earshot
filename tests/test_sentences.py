from earshot.timeline import Caption, sentence_segments


def test_sentence_timing_is_proportional_and_preserves_caption_id():
    caption = Caption("c042", 0, "Speaker A", 2, 10, "One two three four. Five six seven eight nine ten.")
    payload = caption.to_json()
    assert payload["id"] == "c042"
    assert [segment["caption_id"] for segment in payload["sentences"]] == ["c042", "c042"]
    first, second = payload["sentences"]
    assert first["start"] == 2 and first["end"] == 5.2
    assert second["start"] == 5.2 and second["end"] == 10
    assert first["estimated"] and second["estimated"]
    assert Caption.from_json(payload) == caption


def test_long_unpunctuated_turn_is_chunked_by_text_length():
    segments = sentence_segments(" ".join(f"w{index}" for index in range(26)), 0, 26, "c007")
    assert [len(segment["text"].split()) for segment in segments] == [12, 12, 2]
    assert [segment["caption_id"] for segment in segments] == ["c007", "c007", "c007"]
    assert segments[-1]["end"] == 26
