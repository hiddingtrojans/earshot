# GATE T3 — SAM Audio blocked by gated-weight approval

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

- ✓ Existing deterministic tests are green and the no-T5/precomputed-conditioning code remains in place.
- ✓ No dependency or request-format change was made to bypass access.
- ✓ No private media, credentials, non-Meta hosted model, or unapproved runtime fallback was used.
- ✗ Real-weight checks (three `None` overrides at runtime, forbidden-module report, RTF, listening, SI-SDR, and go/no-go) remain unverified.

## Owner action and next step

Owner: obtain Hugging Face approval for `facebook/sam-audio-small-tv` for `hiddingpickles`. After approval, run the spike and full SAM Audio analysis from the implementation pack, then add real T3/T4 rows.

Next: T4 single-stream and Earshot-Lite benchmark only. Additional Meta API spend for this gate: **$0.000000**; running total remains **$0.055881**.
