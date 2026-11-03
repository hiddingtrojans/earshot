import numpy as np

from earshot.bench import align, oracle_baseline_text, overlap_word_indexes, person_scores, si_sdr, wer


def test_alignment_and_wer():
    assert wer("the cat sat", "the cat sat") == 0
    assert wer("the sat", "the cat sat") == 1 / 3
    edits, matches, matched = align(["a", "x", "c"], ["a", "b", "c"])
    assert (edits, matches, matched) == (1, 2, [0, 2])


def test_person_scores_attribution_and_overlap_recall():
    s = person_scores("hello there friend extra", "hello there my friend", {2, 3})
    assert s["attribution"] == 0.75           # "extra" isn't hers
    assert s["overlap_recall"] == 0.5         # "my" missed, "friend" recovered


def test_overlap_word_indexes():
    turns = [{"person": "A", "start": 0, "end": 4, "text": "one two three four"},
             {"person": "B", "start": 2, "end": 5, "text": "five six"}]
    assert overlap_word_indexes(turns, "A") == {2, 3}


def test_oracle_baseline_mapping():
    base = [{"speaker": "1", "start": 0, "end": 1, "text": "did you book"},
            {"speaker": "0", "start": 1, "end": 2, "text": "the dog ate it"}]
    out = oracle_baseline_text(base, {"Ana": "did you book the table", "Raúl": "the dog ate my shoe"})
    assert out == {"Ana": "did you book", "Raúl": "the dog ate it"}


def test_oracle_mapping_is_one_to_one_and_drops_unmatched_speakers():
    baseline = [
        {"speaker": "A", "start": 0, "end": 1, "text": "alpha beta"},
        {"speaker": "B", "start": 1, "end": 2, "text": "alpha gamma"},
        {"speaker": "C", "start": 2, "end": 3, "text": "unrelated"},
    ]
    truth = {"Ana": "alpha beta", "Raúl": "gamma"}
    assert oracle_baseline_text(baseline, truth) == {"Ana": "alpha beta", "Raúl": "alpha gamma"}


def test_si_sdr():
    rng = np.random.default_rng(0)
    ref = rng.standard_normal(16000)
    assert si_sdr(ref, ref) > 100
    assert abs(si_sdr(ref + 0.1 * rng.standard_normal(16000), ref) - 20) < 1
