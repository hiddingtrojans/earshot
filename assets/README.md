# assets

`text_features.npz` — SAM Audio's text conditioning for Earshot's two fixed prompts (`""` and `"speech"`), precomputed once with `tools/precompute_text_features.py` from the `t5-base` encoder that SAM Audio's config names. It was made offline during development. With it, Earshot never loads or runs T5 at runtime; `CachedTextEncoder` in `earshot/separation.py` looks these tensors up instead.

Status: we asked the organizers in Discord #questions (2 Nov) whether shipping these constants is acceptable. Their bot said T5 running at runtime would not meet the rule and passed the constants question to the organizers. If they say no, run `--separator lite` (no SAM Audio).
