import json
import zipfile

import numpy as np

from tools.make_ami_clip import PEOPLE, best_lag, truth_from_annotations


def test_truth_uses_only_timed_non_punctuation_words(tmp_path):
    archive = tmp_path / "annotations.zip"
    with zipfile.ZipFile(archive, "w") as output:
        for _, agent, _, _ in PEOPLE:
            body = "<w starttime='745.10' endtime='745.30'>Okay</w>"
            if agent == "A":
                body += """
                    <w starttime='745.40' punc='true'>.</w>
                    <w starttime='745.50'>missing-end</w>
                    <w starttime='744.80' endtime='745.00'>before</w>
                    <w starttime='745.00' endtime='745.20'>inside</w>
                    <w starttime='819.90' endtime='820.10'>after</w>
                """
            output.writestr(f"words/ES2008a.{agent}.words.xml", f"<root>{body}</root>")
    first = json.dumps(truth_from_annotations(archive), ensure_ascii=False, indent=2) + "\n"
    second = json.dumps(truth_from_annotations(archive), ensure_ascii=False, indent=2) + "\n"
    assert first == second
    truth = json.loads(first)
    assert len(truth["words"]) == 5
    assert truth["words"][0] == {"person": "Speaker A", "start": 0.0, "end": 0.2, "text": "inside"}
    assert [word["text"] for word in truth["words"] if word["person"] == "Speaker A"] == ["inside", "Okay"]
    assert all(word["text"] not in {"before", "after", ".", "missing-end"} for word in truth["words"])


def test_sync_lag_and_camera_mapping():
    rng = np.random.default_rng(4)
    energy = rng.standard_normal(250)
    motion = np.zeros(250)
    motion[3:] = energy[:-3]
    lag, correlation = best_lag(energy, motion)
    assert lag == 0.12
    assert correlation > 0.99
    assert [camera for _, _, _, camera in PEOPLE] == ["Closeup4", "Closeup2", "Closeup3", "Closeup1"]
    assert [headset for _, _, headset, _ in PEOPLE] == ["Headset-0", "Headset-1", "Headset-2", "Headset-3"]
