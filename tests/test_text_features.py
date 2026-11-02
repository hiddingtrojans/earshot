from pathlib import Path

import pytest

from earshot.separation import DEFAULT_TEXT_FEATURES, SamAudioSeparator


def test_fails_closed_without_text_features():
    with pytest.raises(ValueError):
        SamAudioSeparator(text_features=None)
    SamAudioSeparator(text_features=None, allow_t5=True)  # explicit opt-in only


def test_shipped_features_cover_our_prompts():
    import numpy as np

    data = np.load(DEFAULT_TEXT_FEATURES)
    assert {"feat::", "feat::speech"} <= set(data.files)
    assert data["feat::"].shape == (1, 768) and data["feat::speech"].shape[1] == 768


def test_cached_encoder_matches_t5_output_shape():
    torch = pytest.importorskip("torch")
    from earshot.separation import cached_text_encoder_class

    enc = cached_text_encoder_class(Path(DEFAULT_TEXT_FEATURES))()
    feats, mask = enc(["", "speech"])
    assert feats.shape == (2, 2, 768) and mask.tolist() == [[True, False], [True, True]]
    assert feats.dtype == torch.float32
    with pytest.raises(KeyError):
        enc(["dog barking"])
    # stored T5 weights under its prefix are ignored rather than reported as unexpected
    missing, unexpected = [], []
    enc._load_from_state_dict({"model.encoder.weight": torch.zeros(1)}, "", {}, True, missing, unexpected, [])
    assert unexpected == []
