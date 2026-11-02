from earshot.corrections import apply_correction, apply_saved_corrections, nearest_person, taps_to_oracle


def doc():
    return {
        "people": [{"name": "Speaker A", "tap": [0.25, 0.29, 0]}, {"name": "Speaker B", "tap": [0.8, 0.36, 0]}],
        "captions": [{"id": "c001", "person": 0, "name": "Speaker A", "text": "hello"}],
        "activity": [[(0.0, 1.0)], [(1.0, 2.0)]],
        "attribution": {"mapping": {"A": 0}, "confidence": {"A": 0.1}},
    }


def test_correction_moves_captions_and_is_replayable():
    document = doc()
    distance, target = nearest_person(document, 0.81, 0.35, exclude=0)
    assert target == 1 and distance < 0.05
    correction = apply_correction(document, 0, target, 0.81, 0.35, 0)
    assert correction["to"] == 1
    assert document["captions"][0]["person"] == 1
    assert document["captions"][0]["name"] == "Speaker B"
    assert document["activity"] == [[], [(1.0, 2.0), (0.0, 1.0)]]
    assert document["attribution"]["confidence"]["A"] == 1.0
    apply_saved_corrections(document)
    apply_saved_corrections(document)
    assert document["corrections"] == [correction]
    assert document["captions"][0]["person"] == 1
    assert document["activity"] == [[], [(1.0, 2.0), (0.0, 1.0)]]


def test_taps_to_oracle_counts_mismatches_and_low_confidence():
    oracle = {"A": "Speaker A", "B": "Speaker B"}
    result = taps_to_oracle({"A": 1, "B": 1}, {"A": 0.1, "B": 0.9}, oracle, ["Speaker A", "Speaker B"])
    assert result == {"taps": 1, "low_confidence": ["A"]}
