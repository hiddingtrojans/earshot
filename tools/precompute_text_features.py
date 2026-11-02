#!/usr/bin/env python3
"""ONE-TIME, OFFLINE, DEV-ONLY: precompute SAM Audio's text conditioning.

SAM Audio encodes its text prompt with a frozen Google T5-base encoder on every
call. Earshot only ever uses a few fixed prompts, so their encoder outputs are
constants. This script computes them once and writes `text_features.npz`;
`earshot --text-features text_features.npz` then never loads or runs T5.

Use this only if the organizers confirm it's acceptable (see README, "Rules").
"""

import argparse

import numpy as np


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="text_features.npz")
    p.add_argument("--prompt", action="append", default=None, help='repeatable; default: "" and "speech"')
    p.add_argument("--encoder", default="t5-base", help="must match SAM Audio's config text_encoder.name")
    a = p.parse_args()
    prompts = a.prompt if a.prompt is not None else ["", "speech"]

    import torch
    import transformers

    tok = transformers.AutoTokenizer.from_pretrained(a.encoder)
    enc = transformers.T5EncoderModel.from_pretrained(a.encoder).eval()
    out = {}
    with torch.inference_mode():
        for text in prompts:
            ids = tok([text], truncation=True, max_length=512, padding="longest", return_tensors="pt")
            hidden = enc(input_ids=ids["input_ids"], attention_mask=ids["attention_mask"],
                         output_hidden_states=True)["last_hidden_state"][0]
            keep = ids["attention_mask"][0].bool()
            out[f"feat::{text}"] = hidden[keep].numpy().astype(np.float32)
    np.savez(a.out, **out)
    print(f"wrote {a.out}: " + ", ".join(f"{k!r}{v.shape}" for k, v in out.items()))


if __name__ == "__main__":
    main()
