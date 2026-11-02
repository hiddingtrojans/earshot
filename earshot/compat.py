"""Compatibility for SAM Audio's native-attention path on macOS."""

from __future__ import annotations

import sys
import types


def enable_native_attention() -> None:
    """Let SAM Audio use SDPA when xformers has no macOS wheel; keep FMHA explicit."""
    try:
        import xformers.ops  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    class AttentionBias:
        pass

    class MissingFMHA:
        @staticmethod
        def memory_efficient_attention(*args, **kwargs):
            raise RuntimeError("FMHA requires xformers; use SAM Audio's default attn_impl='sdpa'")

    operations = types.ModuleType("xformers.ops")
    operations.AttentionBias = AttentionBias
    operations.fmha = MissingFMHA
    package = types.ModuleType("xformers")
    package.ops = operations
    sys.modules.setdefault("xformers", package)
    sys.modules.setdefault("xformers.ops", operations)
