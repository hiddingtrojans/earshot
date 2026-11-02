from earshot.calls import CallLog
from earshot.spark import translate_captions
from earshot.timeline import Caption


def captions():
    return [Caption("c001", 0, "Speaker A", 0, 1, "Hello"),
            Caption("c002", 1, "Speaker B", 1, 2, "Good question")]


def test_translation_validates_all_ids_once(monkeypatch, tmp_path):
    def fake(calls, purpose, instructions, user, schema, name):
        return {"items": [{"id": "c002", "text": "Buena pregunta"}, {"id": "c001", "text": "Hola"}]}

    monkeypatch.setattr("earshot.spark._respond", fake)
    translated, status = translate_captions(captions(), "es", CallLog(tmp_path))
    assert status == "translated"
    assert translated == {"c001": "Hola", "c002": "Buena pregunta"}


def test_translation_id_mismatch_falls_back_visibly(monkeypatch, tmp_path):
    monkeypatch.setattr("earshot.spark._respond", lambda *args: {"items": [
        {"id": "c001", "text": "Hola"}, {"id": "c001", "text": "Duplicado"},
    ]})
    translated, status = translate_captions(captions(), "es", CallLog(tmp_path))
    assert status == "untranslated"
    assert translated == {"c001": "Hello", "c002": "Good question"}


def test_translation_failure_keeps_originals(monkeypatch, tmp_path):
    def fail(*args):
        raise RuntimeError("cache miss")

    monkeypatch.setattr("earshot.spark._respond", fail)
    translated, status = translate_captions(captions(), "es", CallLog(tmp_path))
    assert status == "untranslated"
    assert translated["c002"] == "Good question"
