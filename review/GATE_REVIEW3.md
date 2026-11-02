# GATE — Claude review round 3: SAM Audio span prompting

Date: 2026-11-02. Bounded experiment, maximum three hours. Local commits only; no push.

## Implementation and protocol

Commits: `9e0ceb8` (span experiment), `4ab320e` (matrix aggregation and regression test), and `a75b6d7` (negative A/B evidence). Tests: **76 passed** before the real A/B run.

`earshot/spans.py` is an experiment-only separator; the existing production separator and demo were not changed. It loads SAM Audio locally with `predict_spans=False`, `reranking_candidates=1`, and no re-rankers or learned span predictor. The description is `speech`, using the existing precomputed text features. The span predictor remains off; **explicit anchors are processor conditioning**, not output from another model.

For each clip:

1. Reuse cached Voice DIARIZATION turns, recompute Lite's mouth-band/Hungarian mapping at runtime, then apply `corrections.json` when present. Neither source run has corrections. The primary runtime mapping is `{A:3, B:1, C:0, D:2}`.
2. For each diarized label, subtract every other label's time coverage from its turns and retain solo spans of at least 0.5 s.
3. Per person, select up to 4 s of target solo audio, longest spans first, from the entire clip. Select up to 4 s of other people's solo audio, with an equal budget per other person. Concatenate target enrollment + 0.25 s silence + other enrollment + 0.25 s silence + the current 10 s window.
4. `+` anchors cover target enrollment and target solo spans within the window; `-` anchors cover each other person's enrollment and solo spans within the window. All anchor times are relative to the concatenated input. Output is trimmed from `offset_samples` to the window length, excluding enrollment.
5. `spans-text` supplies no video. `spans-video` supplies target-visible `keep` masks for the current window and for the matching enrollment times, including the other people used for negative enrollment. Silence has black frames.
6. The cache key contains the variant, mapping, mask digest, complete source spans, anchors, offsets and evaluation-window limit. Tests show distinct keys for text/video and changed mappings.

Synthetic tests cover label subtraction, 0.5 s filtering, longest-first selection, balanced budgets, anchor timing, audio concatenation/trimming, corrections, full-clip enrollment with a short output window, and mode-and-anchor cache invalidation. A separate matrix regression test covers diagonal and off-diagonal aggregation.

## A/B setup

The evaluation window is the round-2 overlap-heavy **0–10 s** interval (14 overlapping truth words), while enrollment is selected from the full 75 s recording. All four people are evaluated with both variants, seed 0 on MPS. The eight output WAVs and `mixture.wav` are saved in `review/ab_listen_spans/`.

```bash
env -u MODEL_API_KEY MODEL_API_BASE_URL=http://127.0.0.1:1 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_CACHE="$PWD/.hf-cache/hub" \
  caffeinate -i .venv/bin/python -u tools/span_prompt_experiment.py ab --device mps
```

Hosted endpoints and Hugging Face downloads are disabled. The local A/B makes **no API calls**. The first run produced the four text stems and then stopped on a matrix-indexing error; a regression test fixed the helper, and the cached stems were reused on rerun.

Envelope protocol is identical to round 2: log energy in 50 ms frames, 25 ms hop, 200 ms smoothing, Pearson correlation on frames above the mixture's 20th-percentile log-energy floor. Rows are intended speakers and columns are headset references A/B/C/D. Correct-voice rate is the fraction whose own headset is the row maximum. A variant needs **at least 3/4 correct rows** to proceed to full runs.

Round-2 visual-only reference on this same window:

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| A | 0.3512 | -0.1337 | 0.9071 | 0.5337 |
| B | 0.3526 | -0.1328 | 0.9071 | 0.5341 |
| C | 0.3515 | -0.1322 | 0.9071 | 0.5343 |
| D | 0.3538 | -0.1328 | 0.9067 | 0.5334 |
| Mixture | 0.3927 | -0.1761 | 0.8535 | 0.4093 |

Round-2 visual-only correct-voice rate: **0.25**; diagonal mean **0.4147**, off-diagonal mean **0.4152**.

## A/B results and timings

**Spans-text:**

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| A | 0.3370 | -0.1127 | 0.8771 | 0.5496 |
| B | 0.3392 | -0.1071 | 0.8788 | 0.5428 |
| C | 0.3350 | -0.1212 | 0.8746 | 0.5522 |
| D | 0.3368 | -0.1164 | 0.8769 | 0.5519 |
| Mixture | 0.3929 | -0.1761 | 0.8536 | 0.4089 |

**Spans-video:**

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| A | 0.3920 | -0.1728 | 0.8589 | 0.4125 |
| B | 0.3931 | -0.1673 | 0.8604 | 0.4094 |
| C | 0.3904 | -0.1731 | 0.8599 | 0.4140 |
| D | 0.3911 | -0.1786 | 0.8573 | 0.4181 |
| Mixture | 0.3929 | -0.1761 | 0.8536 | 0.4089 |

| Variant | Correct-voice rate | Diagonal mean | Off-diagonal mean | Result |
|---|---:|---:|---:|---|
| Spans-text | 0.25 | 0.4141 | 0.4115 | Does not qualify |
| Spans-video | 0.25 | 0.3757 | 0.3719 | Does not qualify |
| Round-2 visual-only `keep` | 0.25 | 0.4147 | 0.4152 | Reference |

Only C's row is correct in each variant. Text/video waveform-pair Pearson correlations are 0.882940–0.883456; no listening evaluation is claimed. The final cached rerun produced the same matrices and all nine WAVs (eight stems plus mixture).

Timings below come from the original cache-miss calls, not the fast cache-hit replays. Model time is per-person inference; call wall includes model loading and the full four-person call.

| Variant | Person | Model inference (s) | Window wall (s) |
|---|---|---:|---:|
| Text | A | 7.208 | 7.4 |
| Text | B | 5.800 | 5.9 |
| Text | C | 5.811 | 5.9 |
| Text | D | 5.806 | 5.9 |
| **Text total** | | **24.625** | **25.1** |
| Video | A | 52.724 | 54.1 |
| Video | B | 46.263 | 47.0 |
| Video | C | 51.450 | 52.2 |
| Video | D | 57.157 | 57.9 |
| **Video total** | | **207.594** | **211.2** |

Text separation call wall: **36.290 s**. Video separation call wall: **225.084 s**. Text anchor digest: `194ed521aae26b00b38f4753`; video anchor digest: `9286c401db9d9bc894c9c6dd`. Both used `per-person (MPS batch stall avoided)` and had no reported fallback exceptions.

## Full evaluation, only if a variant reaches 3/4

**Not run: neither variant reached 3/4 correct-voice rows.** Both scored 0.25. Therefore no full 745 s or 635 s analysis, automatic or oracle three-repeat bench, or new hosted Voice transcription was performed. No WER, right-person, overlap-recall, or oracle-mapped result is claimed.

For qualifying variants, the planned full-run commands are:

```bash
python tools/span_prompt_experiment.py full \
  --run runs/ami_lite --truth bench/ami_ES2008a/truth.json \
  --variant VARIANT --mapping auto --out runs/ami_VARIANT_auto --transcribe
python -m earshot bench runs/ami_VARIANT_auto \
  --truth bench/ami_ES2008a/truth.json --repeat 3 \
  --out runs/ami_VARIANT_auto/bench_review3.json
```

The 635 s run substitutes `runs/ami_lite_635`, `bench/ami_ES2008a_635/truth.json`, and a distinct output directory. A separately labelled oracle run substitutes `--mapping oracle`. **Oracle mappings are for error analysis only and are never a product claim.** The full benchmark also requires new hosted Voice transcriptions for the new stems; that stage is not part of the no-spend local A/B and will be reported with actual usage if reached.

The quality gate is overlap-word recall >= same-run single-stream +0.10 and right-person >= 0.80. WER is reported. Speed is not a rejection criterion.

## Demo decision

**No changes to the demo, tagline, viewer, or production separator.** Neither variant met the 3/4 threshold, so no demo was rebuilt, no “Both talking” moment was added, and the talking-at-once tagline was not restored. Oracle evaluation was not run and is not used for any product claim. A diff confirmed no changes to `demo/ami_meeting`, `README.md`, `web/index.html`, or `pyproject.toml`; only the experiment, tests, and negative-result documentation changed.

## Verification and evidence

- Main tests: **76 passed**.
- Fresh clone/base install: **75 passed, 1 optional Torch-dependent skipped**, with no credentials and Hugging Face offline. Log: `review/clean_clone_review3.log`.
- A/B WAVs: `review/ab_listen_spans/`.
- Machine-readable matrices, plans and timings: `review/span_ab_results.json`; raw output: `review/span_ab.log` and `runs/span_ab/results.json`.
- Anchor plans: `runs/span_ab/spans-text/span_plans.json` and `runs/span_ab/spans-video/span_plans.json`.
- Final public result and running summary: `bench/RESULTS.md` and `review/SUMMARY.md`.

**New API spend: $0.** Hosted endpoints were disabled for the local A/B, model files were used from the local Hugging Face cache, and no full-run transcription was needed. The previous report's total remains **$3.286617 of the $20 cap**. No credential value was printed or committed, and no push was performed.
