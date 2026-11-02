# GATE T3 — SAM Audio evaluated: NO-GO

Final outcome: full T3/T4 evaluation completed and failed both speed and quality thresholds. The earlier sections preserve the initial access blocker and its correction.

Date: 2026-11-02. No SAM Audio model call or local weight execution occurred. No task code commit was needed.

## Access checks and real output

```bash
hf auth whoami
# ✓ Logged in
#   user: hiddingpickles

HF_HOME="$PWD/.hf-home" hf download facebook/sam-audio-small-tv config.json --cache-dir "$PWD/.hf-cache"
# Error: Access denied. Model 'facebook/sam-audio-small-tv' requires approval.
```

The owner logged in after the first authentication check; the remaining blocker is repository approval, not authentication. No token was requested, printed, or stored in the repository. The cache directories are git-ignored.

The required rules thread was checked on 2026-11-02. At 06:06, Cerebral Valley posted the organizers' decision:

> Yes — SAM Audio is an open-source Meta model, so it counts as a Meta model however you run it, and the frozen T5-base encoder inside it is fine with no workaround or precomputation needed. Organizers have ruled that open-source non-Meta models can run alongside Meta's models as long as Meta's models do real work; disclose the T5 encoder in your README and demo. Closed third-party AI models are still not allowed.

Source: https://discord.com/channels/1557169028080869426/1564043204725182484/threads/1566631376868876419

This resolves the compliance question, but not gated-weight access. The run remains on the stricter implementation-pack path: precomputed `assets/text_features.npz`, no runtime T5, no `--allow-t5`, re-rankers disabled.

## Deterministic check

```bash
.venv/bin/pytest -q
# 29 passed
```

The shipped text features and fail-closed behavior are covered by `tests/test_text_features.py`. This does not substitute for running the real weights.

## Done when

- ✗ `runs/ami_samaudio/earshot.json` exists: weights cannot be downloaded.
- ✗ Stems are spot-checked by listening: no stems were produced.
- ✗ Spike `report.json` shows `forbidden_modules_imported: []`: the spike cannot construct the model without weights.
- ✗ Full-clip RTF/device and go/no-go metrics: not run; no numbers invented.
- ✓ Blocker recorded and independent work continues with `--separator lite`, as instructed.

## Review checklist self-check

- ✓ Existing deterministic tests are green; precomputed conditioning remains the default and `--allow-t5` is now allowed by the organizers.
- ✓ No dependency or request-format change was made to bypass access.
- ✓ No private media, credentials, non-Meta hosted model, or unapproved runtime fallback was used.
- ✗ Real-weight checks (three `None` overrides at runtime, forbidden-module report, RTF, listening, SI-SDR, and go/no-go) remain unverified.

## Owner action and next step

Owner: obtain Hugging Face approval for `facebook/sam-audio-small-tv` for `hiddingpickles`. After approval, run the spike and full SAM Audio analysis from the implementation pack, then add real T3/T4 rows.

Next: T4 single-stream and Earshot-Lite benchmark only. Additional Meta API spend for this gate: **$0.000000**; running total remains **$0.055881**.

## Addendum — T5 ruling and same-seed comparison

Commit `c6851f4` applied the organizers' 2 Nov 06:06 Madrid ruling (`docs/10_T5_RULING.md`). Precomputed conditioning remains the default, `--allow-t5` is allowed, and Lite is not a T5 fallback.

Access was rechecked after the ruling:

```text
✓ Logged in
  user: hiddingpickles
Error: Access denied. Model 'facebook/sam-audio-small-tv' requires approval.
```

The new check—two runs of the same 10 s with one seed, precomputed default versus `--allow-t5`, then SI-SDR between their outputs—**could not be run**. No comparison SI-SDR is reported and the default remains unchanged. It must run after weight approval; select `--allow-t5` as the default only if the measured value is below 30 dB.

## Final T3/T4 result — measured NO-GO

The earlier access failure was caused by overriding `HF_HOME`, not by the owner's approval. The correct check without that override succeeded:

```bash
hf auth whoami
# ✓ Logged in
#   user: hiddingpickles
hf download facebook/sam-audio-small-tv config.json --cache-dir "$PWD/.hf-cache"
# ✓ Downloaded
```

SAM Audio and the prescribed dependencies were installed. Compatibility fixes are in `5433653`, `4774a34`, and `2519186`; the reproducible spike seed is in `7d6f077`. Transformers is pinned to 4.56.2 and huggingface_hub to 0.36.2. Native SDPA works without xformers; FMHA is not used. The spike reports show `forbidden_modules_imported: []` for both conditioning modes.

### Conditioning comparison

The same 10 s, box, reference, device (MPS), and seed 0 were used for precomputed and `--allow-t5` runs. Their direct output SI-SDR was **80.775909 dB** (80.775926 dB in reverse), above the 30 dB threshold, so **precomputed remains the default**. Samples are not bit-identical (max difference 0.000030517578125), and this is not presented as byte equality. See `CONDITIONING.md`.

### Full run and quality

All four real stems exist under `runs/ami_samaudio/stems/`. Separation device was MPS for all four; no CPU fallback occurred. A first invocation forgot the interactive-shell key and stopped after Speaker A's separation. Resuming with `zsh -ic` reused that stem and completed without repeating its work.

| Person | Separation seconds (MPS) |
|---|---:|---:|
| Speaker A | 573.198 |
| Speaker B | 569.936 |
| Speaker C | 780.500 |
| Speaker D | 1029.191 |
| **Total** | **2495.825 (41.6 min)** |

Three real Voice repeats on those stems produced:

```text
                               Earshot         Single stream
Word error rate      0.916 [0.896, 0.935]       0.231 [0.221, 0.237]
Right person         0.464 [0.385, 0.555]       0.919 [0.918, 0.921]
Overlap words        0.117 [0.097, 0.146]       0.495 [0.444, 0.540]
SI-SDR gain dB -2.415 [-2.415, -2.415]
```

Per-person SI-SDR gain in the first repeat: A +1.28 dB, B -7.35 dB, C -3.15 dB, D -0.44 dB; macro mean -2.415 dB. Full logs are in `ami_samaudio_analyze_resume.log` and `ami_samaudio_bench_repeat3.log`.

### Go/no-go audit

- ✗ Full 75 s separation must take ≤15 min: **41.6 min**.
- ✗ Overlap recall must beat single-stream by ≥10 points: **0.117 vs 0.495**.
- ✗ Right-person must be ≥0.8: **0.464**.
- ✗ SI-SDR must improve: macro **-2.415 dB**.
- ✓ `runs/ami_samaudio/earshot.json` and all four stems exist; re-rankers/span predictor stayed off and forbidden imports were empty.
- ✗ Listening spot-check: not performed by this interface. The owner should audition the four stems; numerical quality failure is already sufficient for no-go, so no listening success is claimed.

**Decision: ship Lite as the main mode and keep the existing Lite demo. Do not use the failed SAM Audio run as the demo.** The failed run remains useful real evidence of the far-field limitation. Current hosted API spend including this evaluation is **$1.561797 of $20.00**.
