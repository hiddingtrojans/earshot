# Dinner Table Bench — AMI ES2008a results

Date: 2026-11-02. Hardware: Apple M5 Max, arm64. Source: public AMI Meeting Corpus ES2008a, 745.0–820.0 s, far-field `Array1-01`, four speakers, 234 manually timed words (53 overlapping). All numbers below come from `python -m earshot bench` on real cached runs.

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

The single-stream baseline is **oracle-mapped**: each anonymous Voice speaker is assigned to the real person whose truth it matches best. This is generous to the baseline and unavailable to Lite at runtime. The primary SAM comparison uses its own three Voice repeats. Lite and Spark AV use their own previously reported cached repeats, so their baselines are not silently substituted for the primary run's baseline.

Lite does not separate audio and cannot recover words omitted by single-stream Voice. Its central 60% width, 30–60% mask-height mouth band, 0.5 s smoothing, z-scoring, Pearson correlation and `scipy.optimize.linear_sum_assignment` match the oracle baseline on its three 745 s repeats.

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

Stems: **0.500 correct-voice rate**. Mixture: **0.250**. A and C select their own headsets; B and D do not. SI-SDR remains in the JSON rather than the headline because the far-field mixture/close-talk-headset comparison is not meaningful here (mixture/Speaker A = -32.91 dB). `keep` SI-SDR gain is -0.008 dB; legacy `remove` gain is -2.415 dB.

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
