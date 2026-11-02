import json
from types import SimpleNamespace

from earshot.calls import CallLog
from earshot.spark import CATCHUP_SCHEMA, _glimmer_respond, catch_up
from earshot.timeline import Caption


def test_glimmer_json_mode_fallback_and_local_cache(monkeypatch, tmp_path):
    requests = []

    class UnsupportedSchema(Exception):
        status_code = 400

    class Completions:
        def create(self, **kwargs):
            requests.append(kwargs)
            if kwargs["response_format"]["type"] == "json_schema":
                raise UnsupportedSchema()
            return SimpleNamespace(
                id="chatcmpl-local-1",
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"sentences": []}'))],
                usage=None,
            )

    class Client:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=Completions())

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    monkeypatch.setattr("openai.OpenAI", Client)
    calls = CallLog(tmp_path)
    result = _glimmer_respond(calls, "test local catch-up", "instructions", "captions", CATCHUP_SCHEMA, "catchup")
    assert result == {"sentences": []}
    assert len(requests) == 2
    assert requests[0]["model"] == "muse-glimmer"
    assert requests[0]["max_tokens"] == 8000
    assert "temperature" not in requests[0]
    assert requests[1]["response_format"] == {"type": "json_object"}
    row = json.loads(calls.log_path.read_text())
    assert row["model"] == "muse-glimmer" and row["where"] == "local"
    assert row["request_id"] == "chatcmpl-local-1"

    _glimmer_respond(calls, "test local catch-up", "instructions", "captions", CATCHUP_SCHEMA, "catchup")
    assert len(requests) == 2
    assert json.loads(calls.log_path.read_text().splitlines()[-1])["cache"] == "hit"


def test_glimmer_uses_the_same_catchup_verifier(monkeypatch, tmp_path):
    monkeypatch.setattr("earshot.spark._glimmer_respond", lambda *args: {
        "sentences": [{"text": "Speaker A needs 99 remotes.", "cite": ["c001"]}],
    })
    caption = Caption("c001", 0, "Speaker A", 0, 2, "We need two remotes")
    result = catch_up([caption], ["Speaker A"], 2, 30, CallLog(tmp_path), model="glimmer")
    assert result["sentences"][0]["status"] == "replaced"
    assert "number 99 not in the cited captions" in result["sentences"][0]["problems"]
