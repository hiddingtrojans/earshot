from earshot.export import anchor_at, srt, timestamp, vtt


def sample_doc():
    return {
        "people": [
            {"name": "Speaker A", "color": "#E4572E", "anchors": [[0, 0.2, 0.3], [1, 0.4, 0.5]]},
            {"name": "Speaker B", "color": "#2E86AB", "anchors": [[0, 0.8, 0.2]]},
        ],
        "captions": [
            {"id": "c001", "person": 0, "start": 0.5, "end": 2.0, "text": "one & <two>"},
            {"id": "c002", "person": 1, "start": 0.5, "end": 1.5, "text": "simultaneous"},
        ],
    }


def test_vtt_positions_colours_overlap_and_escaping():
    output = vtt(sample_doc())
    assert output.startswith("WEBVTT\n\nSTYLE\n::cue(.spk0) { color: #E4572E; }")
    assert "::cue(.spk1) { color: #2E86AB; }" in output
    assert output.count("00:00:00.500 -->") == 2
    assert "00:00:00.500 --> 00:00:02.000 line:40% position:30% align:middle size:45%" in output
    assert "<c.spk0><v Speaker A>one &amp; &lt;two&gt;</v></c>" in output
    assert "<c.spk1><v Speaker B>simultaneous</v></c>" in output


def test_srt_labels_and_timing():
    output = srt(sample_doc())
    assert output.startswith("1\n00:00:00,500 --> 00:00:02,000\n[Speaker A] one & <two>")
    assert "2\n00:00:00,500 --> 00:00:01,500\n[Speaker B] simultaneous" in output
    assert timestamp(75) == "00:01:15.000"
    assert timestamp(75, True) == "00:01:15,000"


def test_anchor_falls_back_when_person_is_not_visible():
    doc = sample_doc()
    x, y = anchor_at(doc, 0, 0.5)
    assert abs(x - 0.3) < 1e-12 and y == 0.4
    assert anchor_at(doc, 0, 10) == (0.25, 0.35)


def test_exports_use_selected_translation_and_fall_back_to_original():
    doc = sample_doc()
    doc["translations"] = {"es": {"c001": "uno y dos"}}
    assert "<c.spk0><v Speaker A>uno y dos</v></c>" in vtt(doc, "es")
    assert "<c.spk1><v Speaker B>simultaneous</v></c>" in vtt(doc, "es")
    assert "[Speaker A] uno y dos" in srt(doc, "es")
    assert "[Speaker A] one & <two>" in srt(doc)


def test_exports_use_translated_segments():
    doc = sample_doc()
    doc["captions"][0].update({"caption_id": "c001", "segment": 1})
    doc["translation_segments"] = {"es": {"c001": [{"text": "primero"}, {"text": "segundo"}]}}
    assert "[Speaker A] segundo" in srt(doc, "es")
