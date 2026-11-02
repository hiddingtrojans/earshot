# GATE — Claude review round 4: final SAM Audio checks

Date: 2026-11-02. Maximum three hours, then stop separation work. Local commits only; no push.

Implementation and evidence commits: `34bfb97` (integration sanity), `9646725` (clean-mic setup), and `ac8f32f` (negative clean-mic A/B).

## 1. Integration sanity: clean reference plus white noise

Commit `34bfb97` adds `tools/sam_audio_sanity.py` and a deterministic 0 dB SNR test. The source is the first 10 s of `bench/ami_ES2008a/ref_A.wav`, mixed with white noise scaled to the reference RMS. This is a clean-reference comparison, not a room-acoustics evaluation.

| Measurement | Result |
|---|---:|
| Measured SNR | 0.00000056 dB |
| Mixture SI-SDR vs reference | -0.0214 dB |
| SAM Audio target SI-SDR vs reference | 16.8538 dB |
| **Improvement** | **16.8751 dB** |
| Required improvement | >= 10 dB |
| Input sample rate | 48,000 Hz |
| `processor.audio_sampling_rate` | 48,000 Hz |
| `batch.audio_sampling_rate` | 48,000 Hz |
| Input samples | 480,000 |
| Output samples | 480,000 |
| Anchors | None |
| Masked video | None |
| Target RMS | 0.00701538 (-43.079 dBFS) |
| Residual RMS | 0.00665512 (-43.537 dBFS) |
| Residual SI-SDR vs reference | -38.1742 dB |
| Model load | 7.810 s |
| Processor call | 0.002 s |
| Separation call | 3.522 s |

The test used description `speech`, no video, no anchors, precomputed text conditioning, no re-rankers and `predict_spans=False`. **The >=10 dB expectation passes.** The input and output lengths match exactly and the processor receives 48 kHz audio. Target and residual WAVs are in ignored `runs/sanity_sam/`; the public measurements are in `review/sanity_result.json` and `review/sanity_sam.log`.

The first harness attempt omitted `.to(device)` on the processor batch and failed because the audio was on CPU while the model was on MPS. The harness was corrected and rerun. Production separator paths already moved the batch correctly, so no production integration bug or repeat of the old visual A/B was needed.

## 2. Clean-mic A/B

**Audio condition for every number in this section: clean mixed-down mic (AMI Mix-Headset).** The source is T2's `bench/ami_ES2008a/clip_cleanmic.mp4`, first 10 s, with the same four headset references and envelope protocol as earlier rounds. The clip has 704×576 frames at 25 fps and 1,875 frames, matching the saved masks' geometry and timing. The same four-person grid is used for visual prompts.

`keep` repeats round 2's visual-only target-visible masks. `spans-text` repeats round 3's text-only anchors; `spans-video` repeats its matching-time `keep` enrollment video. Span enrollment uses the full 75 s recording, with output trimmed to the first 10 s. Voice diarization and Lite attribution are recomputed on this audio, with corrections applied if present. No oracle mapping is used.

The clean mixed-down mic (AMI Mix-Headset) Voice response contains 13 turns across four labels. Runtime Lite mapping is `{A:3, B:1, C:0, D:2}`; no correction file exists. Its confidence margins are A 0.318298, B 0.115284, C 0.453705 and D 0.025425. No oracle mapping is used.

```bash
python -m earshot analyze runs/ami_cleanmic/analysis.mp4 \
  --tap "Speaker A@0.25,0.29" --tap "Speaker B@0.80,0.36" \
  --tap "Speaker C@0.31,0.78" --tap "Speaker D@0.71,0.78" \
  --out runs/ami_cleanmic --separator lite --no-spark

env -u MODEL_API_KEY MODEL_API_BASE_URL=http://127.0.0.1:1 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_CACHE="$PWD/.hf-cache/hub" \
  caffeinate -i .venv/bin/python -u tools/clean_mic_ab.py --device mps
```

Correct-voice-rate matrices and timings:

**Visual-only `keep` — clean mixed-down mic (AMI Mix-Headset):**

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| A | 0.2804 | 0.0397 | 0.7946 | 0.1514 |
| B | 0.2606 | 0.0561 | 0.7646 | 0.1713 |
| C | 0.2802 | 0.0415 | 0.7937 | 0.1523 |
| D | 0.2702 | 0.0505 | 0.7832 | 0.1627 |
| Mixture | 0.2400 | 0.1557 | 0.4442 | 0.4520 |

Correct-voice rate **0.25**; diagonal/off-diagonal means **0.3232/0.3133**.

**Text-only spans — clean mixed-down mic (AMI Mix-Headset):**

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| A | 0.2896 | -0.0248 | 0.8225 | 0.1532 |
| B | 0.2800 | -0.0180 | 0.8203 | 0.1487 |
| C | 0.2981 | -0.0260 | 0.8234 | 0.1488 |
| D | 0.2983 | -0.0260 | 0.8219 | 0.1506 |
| Mixture | 0.2400 | 0.1557 | 0.4442 | 0.4520 |

Correct-voice rate **0.25**; diagonal/off-diagonal means **0.3114/0.3096**.

**Video plus spans — clean mixed-down mic (AMI Mix-Headset):**

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| A | 0.2885 | -0.0221 | 0.8228 | 0.1519 |
| B | 0.2868 | -0.0209 | 0.8243 | 0.1526 |
| C | 0.3008 | -0.0239 | 0.8236 | 0.1456 |
| D | 0.2988 | -0.0247 | 0.8221 | 0.1498 |
| Mixture | 0.2400 | 0.1557 | 0.4442 | 0.4520 |

Correct-voice rate **0.25**; diagonal/off-diagonal means **0.3102/0.3113**.

All three variants have only C's row correct. The mixture's correct-voice rate is also 0.25, with D its strongest match. None reaches the 3/4 continuation threshold.

**Timings — clean mixed-down mic (AMI Mix-Headset):**

| Variant | Model time A/B/C/D (s) | Model time total (s) | Separation call wall (s) |
|---|---|---:|---:|
| Visual-only `keep` | 18.192 / 16.929 / 17.831 / 18.481 | 71.433 | 83.535 |
| Text-only spans | 5.757 / 5.463 / 5.429 / 5.990 | 22.639 | 31.539 |
| Video plus spans | 83.100 / 101.242 / 87.842 / 79.628 | 351.812 | 370.815 |

Video-plus-span window wall times were 84.7, 102.2, 88.6 and 81.4 s (356.9 s total). Call wall includes loading and the four-person call. All calls used `per-person (MPS batch stall avoided)` with no reported fallback exceptions. Anchor digests were `27518e5730737a68e5c0988a` for text and `b7e1b3597154aa436ceb8fe9` for video.

All stems and the mixture are saved in `review/ab_listen_cleanmic/`.

## 3. Conditional full evaluation

**Not run: every clean-mic variant scored 0.25, below the required 0.75.** Therefore no full 745 s clean-mic analysis, single-stream or Lite three-repeat bench, 635 s run, or new isolated-voice transcription was performed. No WER, right-person or overlap-recall result is claimed for clean mixed-down mic (AMI Mix-Headset). The full evaluation was conditional on 3/4 correct rows and that condition was not met.

Only a variant reaching at least 3/4 correct rows proceeds to the full 745 s clean-mic clip. The comparison includes single-stream and Lite on the same audio, three Voice repeats, then 635 s if time allows. Every resulting number will be labelled **clean mixed-down mic (AMI Mix-Headset)**. The quality gate remains overlap-word recall >= same-run single-stream +0.10 and right-person >= 0.80. WER and real timings are reported; speed alone is not a rejection criterion.

## 4. Conditional demo

**No clean-mic demo was built.** No variant passed the 3/4 threshold, so `demo/ami_meeting_cleanmic` was not created and no “Both talking” claim was added. The existing `demo/ami_meeting`, tagline, viewer and production separator are unchanged. Separation work ends after this round.

## Verification and evidence

- Main suite: **78 passed**, including a direct clean-mic CLI smoke test.
- Fresh clone/base install: **77 passed, 1 optional Torch-dependent skipped**, with no credentials or model downloads. Log: `review/clean_clone_review4.log`.
- Sanity measurements: `review/sanity_result.json` and `review/sanity_sam.log`.
- Clean-mic matrices: `review/cleanmic_ab_results.json` and `runs/cleanmic_ab/results.json`; raw output: `review/cleanmic_ab.log`.
- Clean-mic WAVs: `review/ab_listen_cleanmic/` (12 stems plus mixture).
- Final separation work ends after this round regardless of outcome. No push will be performed.

The clean-mic baseline transcription added **$0.003752**. All A/B separation was local with hosted endpoints and model downloads disabled, and no full-run transcription was needed. Total estimated hosted spend is **$3.290369 of the $20 cap**, recorded in `review/SPEND.md`. No credential value was printed or committed.
