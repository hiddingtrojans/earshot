# assets

`text_features.npz` — SAM Audio's text conditioning for Earshot's two fixed prompts (`""` and `"speech"`), precomputed once with `tools/precompute_text_features.py` from the `t5-base` encoder that SAM Audio's config names. It was made offline during development. With it, Earshot never loads or runs T5 at runtime; `CachedTextEncoder` in `earshot/separation.py` looks these tensors up instead.

Status: the organizers ruled on 2 Nov 2026 at 06:06 Madrid that SAM Audio and its frozen T5-base encoder are allowed with disclosure. These precomputed outputs remain the default; `--allow-t5` is also allowed and runs T5-base locally. Lite is not a T5 fallback; it is used only if SAM Audio fails the T3 go/no-go. See `docs/10_T5_RULING.md`.
