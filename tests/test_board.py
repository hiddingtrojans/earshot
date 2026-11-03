import json
from types import SimpleNamespace

from earshot.board import build_board, check_board_items
from earshot.calls import CallLog
from earshot.timeline import Caption


CAPTIONS = [
    Caption("c001", 1, "Speaker B", 0, 2, "Could we include video recorder functions?"),
    Caption("c002", 0, "Speaker A", 2, 4, "I'll look into it. If I can."),
    Caption("c003", 1, "Speaker B", 4, 6, "Or should we just stick to television buttons?"),
]
NAMES = ["Speaker A", "Speaker B"]


def candidate(**changes):
    item = {"kind": "commitment", "text": "Speaker A will look into including video recorder functions.",
            "owner": "Speaker A", "action": "look into including video recorder functions",
            "due": None, "cite": ["c001", "c002"]}
    item.update(changes)
    return item


def verdict(index=0, status="supported"):
    return {"index": index, "status": status, "reason": "Speaker A explicitly offers to investigate."}


def test_rejects_bad_citation_owner_due_and_number_with_verbatim_fallback():
    invalid = [
        candidate(cite=["c999"]),
        candidate(owner="Speaker D"),
        candidate(due="Friday"),
        candidate(text="Speaker A will deliver 3 remotes."),
    ]
    board = check_board_items(invalid, CAPTIONS, NAMES, [verdict(index) for index in range(4)])
    assert board["items"] == []
    assert len(board["review"]) == 4
    assert "citation" in board["review"][0]["evidence_check"]
    assert "owner" in board["review"][1]["evidence_check"]
    assert "due date" in board["review"][2]["evidence_check"]
    assert "number 3" in board["review"][3]["evidence_check"]
    assert board["review"][3]["fallback"] == {
        "text": "Speaker B: “Could we include video recorder functions?” / Speaker A: “I'll look into it. If I can.”",
        "cite": ["c001", "c002"],
    }


def test_verifier_cannot_turn_a_request_into_a_commitment():
    proposal = candidate(text="Speaker B will include video recorder functions.", owner="Speaker B",
                         action="include video recorder functions", cite=["c001"])
    board = check_board_items([proposal], CAPTIONS, NAMES, [verdict(status="contradicted")])
    assert not board["items"]
    assert board["review"][0]["status"] == "contradicted"
    assert "no messages" in board["actions"]


def test_missing_or_duplicate_verdict_needs_human_review():
    board = check_board_items([candidate()], CAPTIONS, NAMES, [])
    assert board["review"][0]["status"] == "needs_human"
    assert not board["items"]


def test_glimmer_proposals_and_verification_replay_without_credentials(monkeypatch, tmp_path):
    requests = []

    class Completions:
        def create(self, **kwargs):
            requests.append(kwargs)
            name = kwargs["response_format"]["json_schema"]["name"]
            if name == "meeting_board":
                content = json.dumps({"items": [candidate()]})
            else:
                content = json.dumps({"verdicts": [verdict()]})
            return SimpleNamespace(id=f"local-{len(requests)}",
                                   choices=[SimpleNamespace(message=SimpleNamespace(content=content))], usage=None)

    class Client:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=Completions())

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    monkeypatch.setattr("openai.OpenAI", Client)
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    monkeypatch.setenv("EARSHOT_LOCAL_BASE_URL", "http://127.0.0.1:1/v1")
    board = build_board(CAPTIONS, NAMES, CallLog(tmp_path))
    assert len(requests) == 2
    assert board["items"][0]["status"] == "supported"
    assert board["items"][0]["cite"] == ["c001", "c002"]
    assert board["items"][0]["id"] == "board-01"
    assert all(entry["where"] == "local" for entry in
               (json.loads(line) for line in (tmp_path / "calls.jsonl").read_text().splitlines()))

    before_replay = (tmp_path / "calls.jsonl").read_text()
    replayed = build_board(CAPTIONS, NAMES, CallLog(tmp_path, replay=True))
    assert replayed == board
    assert len(requests) == 2
    assert (tmp_path / "calls.jsonl").read_text() == before_replay


def test_empty_conversation_has_no_invented_actions(tmp_path):
    board = build_board([], NAMES, CallLog(tmp_path))
    assert board["items"] == [] and board["review"] == []
    assert "no messages" in board["actions"]


def test_literal_questions_and_acceptance_still_need_glimmer_verification(monkeypatch, tmp_path):
    def respond(calls, purpose, instructions, user, schema, name):
        if name == "meeting_board":
            return {"items": []}
        candidates = __import__("earshot.board", fromlist=["_literal_candidates"])._literal_candidates(CAPTIONS)
        return {"verdicts": [verdict(index) for index in range(len(candidates))]}

    monkeypatch.setattr("earshot.board._glimmer_respond", respond)
    board = build_board(CAPTIONS, NAMES, CallLog(tmp_path))
    assert board["proposal_source"] == "literal transcript"
    assert [item["kind"] for item in board["items"]] == ["question", "commitment", "question"]
    assert board["items"][1]["owner"] == "Speaker A"
    assert board["items"][1]["action"] == "look into it"
    assert board["items"][1]["cite"] == ["c001", "c002"]
    assert "I'll look into it" in board["items"][1]["text"]


def test_literal_acceptance_preserves_the_full_conditional_quote():
    from earshot.board import _literal_candidates

    caption = Caption("c012", 0, "Speaker A", 65, 73, "that's a good question. I'll look into it. If I can.")
    item = _literal_candidates([caption])[0]
    assert "If I can." in item["text"]
    assert item["text"].endswith("If I can.”")


def test_owner_and_due_need_word_boundaries_and_commitment_needs_speaker():
    captions = [Caption("c100", 0, "Speaker A", 0, 1, "Actually, Speaker B will check maybe.")]
    items = [candidate(owner="Al", action="check", cite=["c100"]),
             candidate(owner="Speaker B", action="check", cite=["c100"]),
             candidate(due="may", cite=["c100"])]
    board = check_board_items(items, captions, NAMES, [verdict(index) for index in range(3)])
    assert not board["items"]
    assert "not in the cited captions" in board["review"][0]["evidence_check"]
    assert "not an evidenced speaker" in board["review"][1]["evidence_check"]
    assert "due date" in board["review"][2]["evidence_check"]
