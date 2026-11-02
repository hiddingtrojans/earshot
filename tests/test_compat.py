import sys

import pytest

from earshot.compat import enable_native_attention


def test_native_attention_shim_only_stubs_missing_xformers(monkeypatch):
    monkeypatch.delitem(sys.modules, "xformers", raising=False)
    monkeypatch.delitem(sys.modules, "xformers.ops", raising=False)
    enable_native_attention()
    import xformers.ops

    assert xformers.ops.AttentionBias is not None
    with pytest.raises(RuntimeError, match="default attn_impl='sdpa'"):
        xformers.ops.fmha.memory_efficient_attention()
