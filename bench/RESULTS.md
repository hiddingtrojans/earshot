# Dinner Table Bench — public AMI results

Date: 2026-11-02–03. Hardware: Apple M5 Max, arm64. Source: public AMI Meeting Corpus ES2008a, 745.0–820.0 s, far-field `Array1-01`, four speakers, 234 manually timed words (53 overlapping). All numbers below come from `python -m earshot bench` on real cached runs.

Models: `sam-3.1` for person masks; `muse-voice-transcribe-1.0` for single-stream DIARIZATION and repeat transcription; `muse-spark-1.3` for threads, optional hosted catch-ups and translation; `muse-glimmer` for cached local catch-ups in the demo. Lite attribution is deterministic mouth motion, not another model.

## Results

Values are **mean [min, max] over 3 real Voice transcription repeats**. Repeats reuse the same SAM masks and separated audio, and vary Voice with repeat-specific cache keys. WER and right-person are macro means over four people; overlap recall is the macro mean of per-person recall against exact word-level overlap intervals. Correct-voice rate is the fraction of envelope-correlation rows whose best headset match is the intended person.

| Mode | WER ↓ | Right person ↑ | Overlap-word recall ↑ | Correct voice ↑ |
|---|---:|---:|---:|---:|
| Single stream (oracle; primary SAM repeats) | 0.239 [0.231, 0.246] | 0.913 [0.906, 0.918] | 0.480 [0.463, 0.513] | — |
| Earshot-Lite (745 s mouth-band correlation) | 0.231 [0.221, 0.237] | 0.919 [0.918, 0.921] | 0.495 [0.444, 0.540] | — |
| SAM Audio `keep` (745 s) | 0.967 [0.749, 1.227] | 0.386 [0.301, 0.546] | 0.098 [0.037, 0.141] | 0.500 |
| SAM Audio legacy `remove` (745 s) | 0.916 [0.896, 0.935] | 0.464 [0.385, 0.555] | 0.117 [0.097, 0.146] | 0.250 |
| Spark AV experiment (unverified) | 0.852 [0.776, 0.897] | 0.496 [0.455, 0.529] | 0.254 [0.244, 0.262] | — |

The single-stream baseline is **oracle-mapped** with one-to-one maximum word-overlap assignment; unmatched voices are excluded. This is generous to the baseline and unavailable to Lite at runtime. The primary SAM comparison uses its own three Voice repeats. Lite and Spark AV use their own previously reported cached repeats, so their baselines are not silently substituted for the primary run's baseline.

Lite does not separate audio and cannot recover words omitted by single-stream Voice. Its central 60% width, 30–60% mask-height mouth band, 0.5 s smoothing, z-scoring, Pearson correlation and `scipy.optimize.linear_sum_assignment` match the oracle baseline on its three 745 s repeats.

## Independent public-meeting evaluation and scoring audit — 3 Nov

The independent data source is **ES2008b, AMI 8-mic meeting-room array**, CC BY 4.0. Camera assignments came from corpus metadata and taps were inspected on each actual first frame. No synthetic meeting is used as robustness evidence.

The initial 745 s window contains 217 words, all from Speaker C, and **zero overlapping truth words**. Its overlap gate is **not evaluable** (`go_no_go: null`), not a pass or failure. Its automatic mapping is the correct single active association (`A → Speaker C`). The 635 s candidate has only two overlapping words and was not run. Before inference on a replacement, an inclusion rule was fixed: at least two active speakers and at least 20 overlapping truth words in the same 75 s window. The earliest eligible start was **150 s**, with 110 truth words, 44 overlapping words, and all four speakers. Command: `python tools/run_array_benches.py --meeting ES2008b --window 150 --subsets 8`.

| Meeting / start | WER ↓ | Right person ↑ | Overlap recall ↑ | Better baseline +0.10 | Correct voice | Beamforming (s) | Analysis section (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| ES2008b / 150 s | 0.891 [0.871, 0.901] | 0.337 [0.227, 0.490] | 0.126 [0.106, 0.147] | 0.131 + 0.10 = 0.231 | 0.250 | 1.731 | 52.604 |

**NO-GO on the independent meeting.** It misses the overlap margin by 0.105 and right-person by 0.463. Raw single-stream overlap recall is 0.131 [0.065, 0.167]; delay-and-sum is 0.023. Beamforming and analysis-section times exclude tracking, mask parsing and transcription; the full analysis-and-three-repeat task took 1235.167 s wall time. Diarization found three labels. Speaker B used the fixed motion fallback at threshold 1.77380952. Automatic mapping was `{A:2, B:0, C:3}`; the diagnostic oracle association was `{A:Speaker C, B:Speaker B, C:Speaker A}`, so two corrections would be needed. No corrected or oracle-mapped result is presented as a product claim.

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| Speaker A | 0.1934 | 0.0697 | **0.4601** | 0.3481 |
| Speaker B | 0.1237 | 0.1057 | **0.3911** | 0.1508 |
| Speaker C | 0.0417 | 0.1036 | **0.8287** | 0.1412 |
| Speaker D | **0.3346** | 0.0688 | 0.2785 | 0.2453 |
| Mixture | 0.2228 | 0.1071 | **0.5274** | 0.2922 |

Only Speaker C's row selects its own headset. Diagonal/off-diagonal means are 0.3433/0.2093; correct-voice is 0.250 for stems and mixture. Full repeats, mapping diagnostics and timing are in `review/ami_es2008b_150_array_8_summary.json`; raw output is in `review/parallel_es2008b_150_bench.log` and `review/ami_es2008b_150_array_8_oracle_recheck.log`. The Parallel experiment is not a validated robust separation result.

**Oracle integrity:** review found that greedy assignment could map two diarized voices to one person and dump unmatched voices onto the first person. All array baselines now use one-to-one maximum word-overlap assignment (`scipy.optimize.linear_sum_assignment`), with unmatched voices excluded. Every array benchmark was recomputed cache-only. ES2008b and the 4/5-channel ES2008a summaries are unchanged. ES2008a 745 s delay-and-sum WER changed from 0.235 to 0.234; ES2008a 635 s delay-and-sum WER changed from 0.399 to 0.441. Recall, thresholds and every GO/NO-GO decision are unchanged. Before/after evidence is in `review/oracle_mapping_recheck.json` and the two `ami_array_8*_oracle_recheck.log` files.

## Review round 5: microphone array evaluation

All numbers in this section are **AMI 8-mic meeting-room array**. The optional `--separator array` implementation is classical numpy/scipy MVDR, not SAM Audio. Runtime guide attribution is Lite with saved corrections; Speaker C uses the fixed motion fallback on 635 s at threshold 0.56507652. The delay-and-sum baseline uses GCC-PHAT alignment across all eight channels.

| Window / channels | WER ↓ | Right person ↑ | Overlap recall ↑ | Better baseline +0.10 | Correct voice | Beamforming (s) | Analysis (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 745 s / 8 | 0.282 [0.240, 0.322] | 0.844 [0.835, 0.850] | 0.605 [0.555, 0.662] | 0.522 + 0.10 = 0.622 | 1.000 | 1.835 | 64.294 |
| 745 s / 5 | 0.845 [0.715, 1.078] | 0.658 [0.570, 0.709] | 0.396 [0.349, 0.440] | 0.527 + 0.10 = 0.627 | 1.000 | 0.948 | 66.270 |
| 745 s / 4 (1,3,5,7) | 0.740 [0.505, 1.127] | 0.638 [0.515, 0.708] | 0.392 [0.331, 0.470] | 0.502 + 0.10 = 0.602 | 1.000 | 0.676 | 67.298 |
| 635 s / 8 | 0.403 [0.376, 0.451] | 0.680 [0.623, 0.714] | 0.437 [0.428, 0.442] | 0.486 + 0.10 = 0.586 | 0.750 | 1.907 | 58.664 |
| 635 s / 5 | 1.498 [0.418, 3.122] | 0.584 [0.429, 0.672] | 0.418 [0.378, 0.448] | 0.486 + 0.10 = 0.586 | 0.750 | 0.897 | 62.282 |
| 635 s / 4 (1,3,5,7) | 4.482 [3.452, 5.327] | 0.434 [0.378, 0.516] | 0.478 [0.398, 0.522] | 0.486 + 0.10 = 0.586 | 0.750 | 0.662 | 60.660 |

**NO-GO on both windows.** On 745 s, 8 channels misses the overlap margin by 0.017 despite right-person 0.844; 5 and 4 channels fail both gates. On 635 s, all subsets fail both gates. Array1-01 overlap recall is 0.495/0.495/0.495/0.486, and delay-and-sum is the better 745 s baseline at 0.522/0.527/0.502. On 635 s, Array1-01 is the better baseline at 0.486. The 635 s automatic and one-tap-corrected mappings are identical with **0 taps**; no oracle mapping is used as a product claim.

Eight-channel 745 s correct-voice matrix, diagonal mean 0.6291 and off-diagonal mean 0.0229:

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| Speaker A | **0.7629** | -0.0276 | -0.1870 | 0.1365 |
| Speaker B | 0.1444 | **0.4798** | 0.0878 | 0.1424 |
| Speaker C | -0.1037 | 0.0814 | **0.8092** | 0.0421 |
| Speaker D | 0.0475 | -0.0353 | -0.0536 | **0.4644** |
| Mixture | **0.3887** | 0.0834 | 0.0950 | 0.2559 |

Other 745 s subsets also have correct-voice rate 1.000 (5 channels 0.5772/0.0664 and 4 channels 0.5842/0.0502 diagonal/off-diagonal means). On 635 s, the correct-voice rate is 0.750 for all subsets; diagonal/off-diagonal means are 0.5599/0.1129, 0.5571/0.1421 and 0.5545/0.1387. Full repeat values are in `review/array_745_summary.json` and `review/array_635_summary.json`; raw commands and scores are in `review/array_745.log` and `review/array_635.log`.

**Demo decision:** round 5 built no array demo and did not restore the overlap-recovery tagline. On 3 Nov, `demo/ami_meeting_array` was added as a separately labelled Parallel experiment with its real gate and sync limitations visible. Lite remains the default demo and single-mic mode; the quality decision is unchanged. No claim is made that Earshot runs on glasses. The reference file `~/Downloads/array_exp.py` was missing, so no copy is committed at `docs/array_exp.py` and its exact matrix is not claimed as reproduced. The optional SAM Audio noise-cleaning experiment was not run, both because the array is NO-GO and because that direct reference reproduction is unresolved.

## Review round 5: sentence timing and Lite motion estimates

Sentence bubbles preserve original caption IDs and divide text into punctuation-aware chunks of at most 12 words. Their start/end times are **estimated from text length**, and the viewer labels that estimate. Translated segments use the same original caption IDs. `Caption.to_json` emits nested `sentences` without changing the original caption or citation schema.

Lite's motion-based “was also talking” markers use the fixed protocol chosen before evaluation: 0.5 s smoothing, threshold `max(0.1, median + 3×MAD)`, and 0.5 s minimum events. The displayed label is a **motion estimate**, not verified speech. Precision/recall are frame-level measurements at 40 ms against exact AMI word overlaps:

| Window | Precision | Recall | True-positive frames | Predicted frames | Truth frames |
|---|---:|---:|---:|---:|---:|
| 745 s single-mic Array1-01 | 0.0987 | 0.1888 | 54 | 547 | 286 |
| 635 s single-mic Array1-01 | 0.0695 | 0.1181 | 34 | 489 | 288 |

These are weak motion estimates, not evidence of recovered overlap words. Exact per-person values and thresholds are in `review/motion_overlap.json`; generation and scoring use `tools/bench_motion_overlap.py`.

## Review round 2: full `keep` decision and timing

**SAM Audio `keep` is a measured NO-GO on quality, not speed.** Right-person 0.386 is below 0.80 in every repeat. Overlap recall 0.098 must be at least the same-run baseline mean +0.10 = **0.580**, so it falls short by 0.382; every repeat also fails its paired comparison. WER is 0.967 and is reported rather than used as a gate. Lite remains the demo; the failed run is evidence, not demo media.

The real per-person MPS run used the semantic `keep` mask, precomputed text conditioning, no re-rankers/span predictor, and no Spark. Total separation call wall time was **773.889 s (12 min 53.9 s)**, including loading. No speed-only failure was applied. Per-person timings:

| Person | Model inference (s) | Window wall time including processing/cleanup (s) |
|---|---:|---:|
| A | 161.775 | 165.1 |
| B | 179.909 | 183.2 |
| C | 200.073 | 203.5 |
| D | 193.504 | 196.1 |
| **Total** | **735.261** | **747.9** |

Four-person batching and per-person exception fallback are implemented. Actual four-person MPS batching stalled for over 25 minutes, and a CPU batch did not complete a window after over 20 minutes; neither is a quality benchmark. The completed evaluation therefore uses one person at a time on MPS, freezes the loaded static object graph, and runs `gc.collect()` plus `torch.mps.empty_cache()` after every window. Real per-window timings are in `review/ami_samaudio_keep_mps_analyze.log`.

### Full-run envelope matrix

Protocol: 50 ms frames, 25 ms hop, log energy, 200 ms smoothing, Pearson correlation on frames above the mixture's 20th-percentile log-energy noise floor. Rows are intended people; columns are headset references A/B/C/D. Bold cells are each row's maximum.

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| Speaker A | **0.2121** | 0.0995 | 0.0464 | 0.1532 |
| Speaker B | 0.1808 | **0.1884** | 0.0167 | 0.1316 |
| Speaker C | 0.2109 | 0.0998 | 0.0427 | **0.1573** |
| Speaker D | 0.1402 | **0.2091** | 0.0480 | 0.1349 |
| Mixture | **0.3887** | 0.0834 | 0.0950 | 0.2559 |

Stems: **0.500 correct-voice rate**. Mixture: **0.250**. A and C select their own headsets; B and D do not. SI-SDR remains in the JSON rather than the headline because far-field mixture/close-talk-headset comparisons are not meaningful here. The 10 s A/B mixture/Speaker A value is -32.91 dB; the full primary value is -24.77 dB. `keep` SI-SDR gain is -0.008 dB; legacy `remove` gain is -2.415 dB.

## Review round 2: 635 s held-out SAM Audio check

The same `keep` semantics and per-person MPS code were run on the 635–710 s window before 23:00 Madrid. This is distinct from the Lite development-window result above. Three repeats produced:

| Mode | WER ↓ | Right person ↑ | Overlap-word recall ↑ | Correct voice ↑ |
|---|---:|---:|---:|---:|
| SAM Audio `keep` (635 s) | 2.731 [1.097, 3.825] | 0.382 [0.296, 0.537] | 0.185 [0.158, 0.230] | 0.250 |
| Same-run single stream, oracle-mapped | 0.384 [0.377, 0.395] | 0.693 [0.689, 0.697] | 0.486 [0.424, 0.524] | 0.250 mixture |

**Held-out NO-GO on quality too.** Right-person is below 0.80 in every repeat. Overlap recall is below the mean baseline +0.10 threshold of 0.586; every paired repeat also fails. WER is reported, not used as a gate. SI-SDR gain is -5.19 dB and the measured mixture/Speaker A value is -51.11 dB, retained only as secondary JSON evidence.

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| Speaker A | 0.4208 | 0.1495 | **0.4300** | -0.1635 |
| Speaker B | 0.3426 | 0.1441 | **0.5587** | 0.0420 |
| Speaker C | 0.3801 | 0.0880 | **0.5102** | 0.0059 |
| Speaker D | 0.3436 | 0.1410 | **0.5589** | 0.0439 |
| Mixture | 0.3413 | 0.1183 | **0.6501** | 0.1514 |

Every stem best matches C; only C's own row is correct, for **0.250 correct-voice rate**. Separation wall time was **772.703 s**. Per-person model/window-wall times were A 158.669/161.5 s, B 188.832/191.9 s, C 178.132/180.7 s and D 210.156/213.1 s. Totals: model **735.789 s**, windows **747.2 s**. Speed is not a rejection criterion.

```bash
zsh -ic 'env HF_HUB_CACHE="$PWD/.hf-cache/hub" caffeinate -i \
  .venv/bin/python -u -m earshot analyze bench/ami_ES2008a_635/clip.mp4 \
  --tap "Speaker A@0.25,0.29" --tap "Speaker B@0.80,0.36" \
  --tap "Speaker C@0.31,0.78" --tap "Speaker D@0.71,0.78" \
  --out runs/ami_samaudio_keep_635 --separator samaudio \
  --device mps --mask-mode keep --no-spark'
zsh -ic 'caffeinate -i .venv/bin/python -m earshot bench runs/ami_samaudio_keep_635 \
  --truth bench/ami_ES2008a_635/truth.json --repeat 3 \
  --out runs/ami_samaudio_keep_635/bench_review2.json'
```

The verified masks and all four baseline Voice responses were reused from `runs/ami_lite_635`; only isolated-voice transcription required new hosted calls. Logs are `review/ami_samaudio_keep_635_analyze.log` and `review/ami_samaudio_keep_635_bench_review2.log`; JSON is `runs/ami_samaudio_keep_635/bench_review2.json`.

## Review round 2: visual-mask A/B

`processor.mask_videos` computes `v * m.eq(0)`. `keep` inverts the target mask first and leaves the target visible; `remove` passes the target mask and blacks it out. Both modes are cached separately. The unit test uses frames of ones and proves nonzero pixels remain only inside the `keep` mask.

The eight real MPS runs used the 0–10 s window (14 overlapping truth words, the most of the separation windows), four grid cells, both modes, and seed 0. WAVs are committed in `review/ab_listen/` for the owner to compare with `mixture.wav`. **No agent listening check is claimed.**

**Keep:**

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| A | 0.3512 | -0.1337 | 0.9071 | 0.5337 |
| B | 0.3526 | -0.1328 | 0.9071 | 0.5341 |
| C | 0.3515 | -0.1322 | 0.9071 | 0.5343 |
| D | 0.3538 | -0.1328 | 0.9067 | 0.5334 |
| Mixture | 0.3927 | -0.1761 | 0.8535 | 0.4093 |

**Remove:**

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| A | 0.3528 | -0.1325 | 0.9069 | 0.5334 |
| B | 0.3520 | -0.1323 | 0.9070 | 0.5333 |
| C | 0.3525 | -0.1325 | 0.9070 | 0.5334 |
| D | 0.3512 | -0.1329 | 0.9070 | 0.5334 |
| Mixture | 0.3927 | -0.1761 | 0.8535 | 0.4093 |

| Mode | Correct-voice rate | Diagonal mean | Off-diagonal mean |
|---|---:|---:|---:|
| Keep | 0.25 | 0.4147 | 0.4152 |
| Remove | 0.25 | 0.4152 | 0.4149 |

**Neither mode is diagonal-dominant.** Keep/remove waveform-pair Pearson correlations are 0.999955–0.999986. `keep` is therefore the default because it follows Meta's target-visible evaluation semantics, **not because it won the A/B**. Exact values and the mixture gating rule are in `review/envelope_ab.json`; raw model output is in `review/ab_spikes.log`.

## Review round 3: span prompting negative result

A bounded local experiment tested explicit SAM Audio anchors on the same 0–10 s window. Runtime Lite mapped cached Voice labels with `{A:3, B:1, C:0, D:2}`; there was no correction file. Solo spans were other-label-subtracted and at least 0.5 s. Enrollment was up to 4 s target speech + 0.25 s silence + up to 4 s evenly budgeted other speech + 0.25 s silence + the window. `spans-text` used anchors and `speech` text only; `spans-video` added target-visible `keep` video at matching enrollment times. Output was trimmed to the window. Mode, source spans and complete anchor plans were in the cache key.

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

| Variant | Correct-voice rate | Diagonal mean | Off-diagonal mean | Model time total (s) | Separation call wall (s) |
|---|---:|---:|---:|---:|---:|
| Spans-text | 0.25 | 0.4141 | 0.4115 | 24.625 | 36.290 |
| Spans-video | 0.25 | 0.3757 | 0.3719 | 207.594 | 225.084 |
| Round-2 visual-only `keep` | 0.25 | 0.4147 | 0.4152 | — | — |

Only C's row selected its own headset in each variant. **Neither variant reached the required 3/4 correct rows, so no full 745 s/635 s runs, automatic/oracle three-repeat benches, or hosted transcription calls were made.** No WER/right-person/overlap-recall result is claimed. Demo, tagline, and production separator behavior are unchanged. This was a local-only experiment with **$0 new API spend**.

Per-person model inference seconds: text A 7.208, B 5.800, C 5.811, D 5.806; video A 52.724, B 46.263, C 51.450, D 57.157. Video window wall times were 54.1, 47.0, 52.2 and 57.9 s. All eight WAVs are in `review/ab_listen_spans/`; exact matrices, anchors, cache digests and timings are in `review/span_ab_results.json`. Per-variant anchor plans are `runs/span_ab/spans-text/span_plans.json` and `runs/span_ab/spans-video/span_plans.json`; raw output is `review/span_ab.log`. See `review/GATE_REVIEW3.md` for the protocol.

## Review round 4: clean mixed-down mic (AMI Mix-Headset) negative result

The final integration sanity test used a clean reference plus 0 dB white noise. SAM Audio improved SI-SDR by **16.8751 dB** (mixture -0.0214 dB, target 16.8538 dB), with target RMS 0.00701538 and residual RMS 0.00665512. Input, batch and processor rates were all 48,000 Hz; input and output both contained 480,000 samples. A harness-only device-placement error was fixed; production already moved batches to the selected device. **No production integration bug was found.**

The clean-mic A/B used T2's `clip_cleanmic.mp4`, first 10 s, four headset references and the same envelope protocol. Runtime Voice diarization returned 13 turns; Lite mapped `{A:3, B:1, C:0, D:2}` without corrections or an oracle. Every number below is **clean mixed-down mic (AMI Mix-Headset)**.

**Visual-only `keep` — clean mixed-down mic (AMI Mix-Headset):**

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| A | 0.2804 | 0.0397 | 0.7946 | 0.1514 |
| B | 0.2606 | 0.0561 | 0.7646 | 0.1713 |
| C | 0.2802 | 0.0415 | 0.7937 | 0.1523 |
| D | 0.2702 | 0.0505 | 0.7832 | 0.1627 |
| Mixture | 0.2400 | 0.1557 | 0.4442 | 0.4520 |

**Text-only spans — clean mixed-down mic (AMI Mix-Headset):**

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| A | 0.2896 | -0.0248 | 0.8225 | 0.1532 |
| B | 0.2800 | -0.0180 | 0.8203 | 0.1487 |
| C | 0.2981 | -0.0260 | 0.8234 | 0.1488 |
| D | 0.2983 | -0.0260 | 0.8219 | 0.1506 |
| Mixture | 0.2400 | 0.1557 | 0.4442 | 0.4520 |

**Video plus spans — clean mixed-down mic (AMI Mix-Headset):**

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| A | 0.2885 | -0.0221 | 0.8228 | 0.1519 |
| B | 0.2868 | -0.0209 | 0.8243 | 0.1526 |
| C | 0.3008 | -0.0239 | 0.8236 | 0.1456 |
| D | 0.2988 | -0.0247 | 0.8221 | 0.1498 |
| Mixture | 0.2400 | 0.1557 | 0.4442 | 0.4520 |

| Variant — clean mixed-down mic (AMI Mix-Headset) | Correct-voice rate | Diagonal mean | Off-diagonal mean | Model time total (s) | Separation call wall (s) |
|---|---:|---:|---:|---:|---:|
| Visual-only `keep` | 0.25 | 0.3232 | 0.3133 | 71.433 | 83.535 |
| Text-only spans | 0.25 | 0.3114 | 0.3096 | 22.639 | 31.539 |
| Video plus spans | 0.25 | 0.3102 | 0.3113 | 351.812 | 370.815 |

Only C's own row was correct in each variant. **No variant reached 3/4 correct rows. No full 745 s/635 s run, three-repeat clean-mic bench, or `demo/ami_meeting_cleanmic` was created.** No full-run WER, right-person or overlap-recall result is claimed. Existing demo, tagline and production separator behavior are unchanged, and separation work ends here.

All 12 stems and the mixture are in `review/ab_listen_cleanmic/`; measurements are in `review/cleanmic_ab_results.json` and `review/cleanmic_ab.log`. The clean-mic baseline transcription added **$0.003752**; A/B inference itself used no hosted calls. See `review/GATE_REVIEW4.md` for the full protocol and per-person timings.

## Review round 1: Spark AV negative result

The bounded experiment sent each 10-second AMI window as `input_video` with audio, the corresponding Voice DIARIZATION turns, and normalized name/grid positions. Strict JSON returned rough per-person segments. All calls used `muse-spark-1.3` through `CallLog.cached`; outputs are **unverified** and are not presented as ground truth or a verified summary.

Three repeats measured WER **0.852 [0.776, 0.897]**, right-person **0.496 [0.455, 0.529]**, and overlap recall **0.254 [0.244, 0.262]**. These fail every adoption threshold: overlap recall below baseline +10 points, WER worse than baseline, and right-person below 0.8. The model did return spoken words with plausible timing, so an audio-only fallback was not needed. **Spark AV is not enabled in the viewer or demo; it is a documented negative result.**

Experiment usage: 33 uncached AV calls, estimated **$0.330758**, within the 2-hour/$3 experiment cap. Scorer output is in `review/spark_ami_bench.log`; machine-readable values are in `runs/spark_ami/bench_review1.json`.

## Review round 1: Lite before/after

The 635 s window was used for development sweeps; 745 s was evaluated separately. Before is the original top-of-mask/total-motion implementation. After is the reviewed mouth-band correlation implementation.

| Window | Lite before WER / right / overlap | Lite after WER / right / overlap | Oracle baseline after WER / right / overlap |
|---|---|---|---|
| 635 s development | 0.396 / 0.686 / 0.424 | 2.571 [0.395, 3.719] / 0.547 [0.473, 0.693] / 0.553 [0.424, 0.624] | 0.384 / 0.693 / 0.486 |
| 745 s primary | 0.702 / 0.540 / 0.387 | 0.231 [0.221, 0.237] / 0.919 [0.918, 0.921] / 0.495 [0.444, 0.540] | 0.231 / 0.919 / 0.495 |

A development-only 60–90% lower-mask band matched the 635 s baseline (0.384 / 0.693 / 0.486) but failed on 745 s (right-person 0.537). It is **not used**. The actual 30–60% mouth band is retained on the primary benchmark and was not selected from its test-window results. Mappings are recorded beside oracle mappings in each repeat's bench JSON.

**One-tap correction:** confidence is best-minus-second-best correlation, with threshold **0.15 fixed in advance**. Taps needed to reach the oracle mapping were **0 / 0 / 0 on 745 s** and **1 / 1 / 0 on 635 s** (three repeats in order). Low-confidence corrections are exposed as “Not Speaker?” buttons and saved to `corrections.json` for replay.

## Commands

```bash
python -m earshot analyze bench/ami_ES2008a/clip.mp4 \
  --tap "Speaker A@0.25,0.29" --tap "Speaker B@0.80,0.36" \
  --tap "Speaker C@0.31,0.78" --tap "Speaker D@0.71,0.78" \
  --out runs/ami_lite --separator lite

python -m earshot bench runs/ami_lite \
  --truth bench/ami_ES2008a/truth.json --repeat 3 \
  --out runs/ami_lite/bench_repeat3.json

EARSHOT_REPLAY=1 python -m earshot bench runs/ami_lite \
  --truth bench/ami_ES2008a/truth.json --repeat 3 \
  --out runs/ami_lite/bench_repeat3.json
```

Primary SAM Audio `keep` analysis and its three-repeat scorer used (the interactive shell supplies the hosted credential without printing it):

```bash
zsh -ic 'env HF_HUB_CACHE="$PWD/.hf-cache/hub" caffeinate -i \
  .venv/bin/python -u -m earshot analyze bench/ami_ES2008a/clip.mp4 \
  --tap "Speaker A@0.25,0.29" --tap "Speaker B@0.80,0.36" \
  --tap "Speaker C@0.31,0.78" --tap "Speaker D@0.71,0.78" \
  --out runs/ami_samaudio_keep --separator samaudio \
  --device mps --mask-mode keep --no-spark'

zsh -ic 'caffeinate -i .venv/bin/python -m earshot bench runs/ami_samaudio_keep \
  --truth bench/ami_ES2008a/truth.json --repeat 3 \
  --out runs/ami_samaudio_keep/bench_review2.json'
```

Full scorer output and machine-readable per-person/per-repeat values are in `review/ami_lite_bench_repeat3_optimized.log` and `runs/ami_lite/bench_repeat3.json`. Primary SAM Audio output is in `review/ami_samaudio_keep_mps_analyze.log`, `review/ami_samaudio_keep_bench_review2.log`, and `runs/ami_samaudio_keep/bench_review2.json`. Legacy `remove` values remain in `runs/ami_samaudio/bench_repeat3.json`; its envelope matrix is `runs/ami_samaudio/bench_envelope.json`.

## Negative control

The fifth tap is `Negative Control@0.12,0.70`, on the empty door area of Closeup3. The analysis command is:

```bash
python -m earshot analyze bench/ami_ES2008a/clip.mp4 \
  --tap "Speaker A@0.25,0.29" --tap "Speaker B@0.80,0.36" \
  --tap "Speaker C@0.31,0.78" --tap "Speaker D@0.71,0.78" \
  --tap "Negative Control@0.12,0.70" \
  --out runs/ami_negative --separator lite --no-spark
```

**Final result: 0 captions for Negative Control**, out of 11 captions assigned to the four real people. SAM returned a mask for the empty region on all 1,875 frames (mean area 0.053931 of the frame), so this checks attribution rather than mask presence.

The first implementation amplified the empty region's 0.0045-gray-level median compression motion and incorrectly gave it 4 captions. Commit `607bfdd` added a 0.1-gray-level normalization floor and a regression test. The final run used `EARSHOT_REPLAY=1`, reused the real masks and Voice response, and produced zero negative-control captions without new API spend.
