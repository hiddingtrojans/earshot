# Dinner Table Bench — AMI ES2008a results

Date: 2026-11-02. Hardware: Apple M5 Max, arm64. Source: public AMI Meeting Corpus ES2008a, 745.0–820.0 s, far-field `Array1-01`, four speakers, 234 manually timed words (53 overlapping). All numbers below come from `python -m earshot bench` on real cached runs.

Models: `sam-3.1` for person masks; `muse-voice-transcribe-1.0` for single-stream DIARIZATION and repeat transcription; `muse-spark-1.3` for the viewer's threads/catch-ups. Lite attribution is deterministic mouth motion, not another model.

## Results

Values are **mean [min, max] over 3 real Voice transcription repeats**. Repeats reuse the same SAM masks and vary only Voice with repeat-specific cache keys. WER and right-person are macro means over the four people; overlap recall is the macro mean of per-person recall against exact word-level overlap intervals.

| Mode | WER ↓ | Right person ↑ | Overlap-word recall ↑ | SI-SDR gain (dB) ↑ |
|---|---:|---:|---:|---:|
| Single-stream captions (oracle-mapped) | 0.231 [0.221, 0.237] | 0.919 [0.918, 0.921] | 0.495 [0.444, 0.540] | — |
| Earshot-Lite (mouth-band activity correlation) | 0.231 [0.221, 0.237] | 0.919 [0.918, 0.921] | 0.495 [0.444, 0.540] | — |
| Earshot (SAM Audio) | 0.916 [0.896, 0.935] | 0.464 [0.385, 0.555] | 0.117 [0.097, 0.146] | -2.415 [-2.415, -2.415] |
| Spark AV experiment (unverified) | 0.852 [0.776, 0.897] | 0.496 [0.455, 0.529] | 0.254 [0.244, 0.262] | — |

The single-stream baseline is **oracle-mapped**: each anonymous Voice speaker is assigned to the real person whose truth it matches best. This is generous to the baseline and is not available to Earshot-Lite at runtime. The baseline and Lite use identical Voice responses within each repeat.

Lite does not separate audio and cannot recover words that the single-stream Voice response omits. The reviewed implementation measures a central 60% width, 30–60% mask-height mouth band, smooths activity and motion over 0.5 s, z-scores both, and maximizes total Pearson correlation with `scipy.optimize.linear_sum_assignment`. On 745 s it matches the generous oracle baseline on all three repeats.

**SAM Audio is a measured no-go on this clip.** All four real stems were produced on MPS, but separation took 2,495.8 seconds (41.6 minutes), exceeding the 15-minute limit. Right-person 0.464 is below 0.8, overlap recall 0.117 does not beat the baseline by 10 points, and SI-SDR gain is -2.415 dB. Lite therefore remains the main mode and demo. The failed run is evidence, not demo media. Per-person SI-SDR in the first repeat was A +1.28 dB, B -7.35 dB, C -3.15 dB, D -0.44 dB (isolated minus mixture); their macro mean is -2.415 dB.

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

SAM Audio analysis and its three-repeat scorer used:

```bash
python -m earshot analyze bench/ami_ES2008a/clip.mp4 \
  --tap "Speaker A@0.25,0.29" --tap "Speaker B@0.80,0.36" \
  --tap "Speaker C@0.31,0.78" --tap "Speaker D@0.71,0.78" \
  --out runs/ami_samaudio --separator samaudio --translate es

python -m earshot bench runs/ami_samaudio \
  --truth bench/ami_ES2008a/truth.json --repeat 3 \
  --out runs/ami_samaudio/bench_repeat3.json
```

Full scorer output and machine-readable per-person/per-repeat values are in `review/ami_lite_bench_repeat3_optimized.log` and `runs/ami_lite/bench_repeat3.json` in the working run folder. SAM Audio's output is in `review/ami_samaudio_bench_repeat3.log` and `runs/ami_samaudio/bench_repeat3.json`.

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
