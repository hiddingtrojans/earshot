from earshot.spark import apply_threads, verify_catchup
from earshot.timeline import Caption

NAMES = ["Ana", "Raúl", "Marta"]


def caps():
    return [
        Caption("c001", 0, "Ana", 0.0, 2.0, "Did anyone book the table for Friday?"),
        Caption("c002", 1, "Raúl", 1.0, 3.0, "I booked it for 8 at Casa Lola"),
        Caption("c003", 2, "Marta", 1.5, 3.5, "the dog ate my shoe again"),
    ]


def test_verified_sentence_passes():
    out = verify_catchup([{"text": "Raúl booked Casa Lola for 8.", "cite": ["c002"]}], caps(), NAMES)
    assert out == [{"text": "Raúl booked Casa Lola for 8.", "cite": ["c002"], "status": "verified"}]


def test_wrong_number_is_replaced_by_verbatim_caption():
    out = verify_catchup([{"text": "Raúl booked it for 9.", "cite": ["c002"]}], caps(), NAMES)
    assert out[0]["status"] == "replaced"
    assert out[0]["text"] == "Raúl: “I booked it for 8 at Casa Lola”"


def test_name_not_in_cited_captions_is_rejected():
    out = verify_catchup([{"text": "Marta booked the table.", "cite": ["c002"]}], caps(), NAMES)
    assert out[0]["status"] == "replaced"


def test_citation_outside_window_and_empty_fallback():
    out = verify_catchup([{"text": "Something.", "cite": ["c999"]}], caps(), NAMES)
    assert [s["status"] for s in out] == ["verbatim"] * 3


def test_threads_validated_and_repaired():
    c = caps()
    threads = apply_threads(c, {"threads": [{"thread": 1, "topic": "Friday dinner"}, {"thread": 2, "topic": "the dog"}],
                                "assignments": [{"id": "c001", "thread": 1}, {"id": "c003", "thread": 2},
                                                {"id": "c002", "thread": 7}]})
    assert [x.thread for x in c] == [1, 1, 2]  # unknown thread 7 -> previous caption's thread
    assert threads == [{"thread": 1, "topic": "Friday dinner"}, {"thread": 2, "topic": "the dog"}]
    c = caps()
    assert apply_threads(c, {"threads": [], "assignments": []}) == [{"thread": 1, "topic": "Conversation"}]
