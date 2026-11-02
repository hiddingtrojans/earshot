# GATE — Claude review round 1

Date: 2026-11-02. All work was local; no push. Tests: **59 passed** before the result commit.

## Commits

- `570f40b` Add selectable AMI benchmark window start
- `a7add9d` Map voices to faces by mouth activity correlation
- `1adc763` Add unverified Spark audiovisual overlap mode
- `57d9979` Log Lite and oracle mappings in bench output
- `438d29f` Stop AV windows at the clip boundary
- `0a07757` Add AMI 635s development truth and attribution
- `68aaf81` Report reviewed Lite mapping and Spark AV result

## 1. Lite voice-to-face correction

Implementation: central 60% width, 30–60% mask-height mouth band; per-label activity at video frame rate; 0.5 s smoothing; z-scored motion/activity; Pearson correlation; `scipy.optimize.linear_sum_assignment`; best-correlated assignment for extra labels. SciPy was added as a declared dependency for the Hungarian assignment, not for any model.

Synthetic tests cover activity-aligned person 2 beating higher overall motion, exact mouth-band geometry, optimal assignment, and static-region behavior. The full suite is 59 tests.

### Real before/after values

| Window | Metric | Before | After | Oracle baseline after |
|---|---|---:|---:|---:|
| 635 s development | WER | 0.396 | 2.571 [0.395, 3.719] | 0.384 [0.377, 0.395] |
| 635 s development | Right person | 0.686 | 0.547 [0.473, 0.693] | 0.693 [0.689, 0.697] |
| 635 s development | Overlap recall | 0.424 | 0.553 [0.424, 0.624] | 0.486 [0.424, 0.524] |
| 745 s primary | WER | 0.702 | 0.231 [0.221, 0.237] | 0.231 [0.221, 0.237] |
| 745 s primary | Right person | 0.540 | 0.919 [0.918, 0.921] | 0.919 [0.918, 0.921] |
| 745 s primary | Overlap recall | 0.387 | 0.495 [0.444, 0.540] | 0.495 [0.444, 0.540] |

The primary target, right-person within 0.05 of baseline, is met exactly. The development window did not meet that target: one label is misassigned in two repeats, producing high WER. This is reported rather than hidden.

A 60–90% lower-mask alternative matched the 635 s baseline (0.384 / 0.693 / 0.486) but scored 0.537 right-person on 745 s and is **not used**. The requested 30–60% mouth band remains. No parameter was selected from the 745 s test results.

### Mapping evidence

Commands:

```bash
python tools/make_ami_clip.py --start 635 --out bench/ami_ES2008a_635
python -m earshot analyze bench/ami_ES2008a_635/clip.mp4 \
  --tap "Speaker A@0.25,0.29" --tap "Speaker B@0.80,0.36" \
  --tap "Speaker C@0.31,0.78" --tap "Speaker D@0.71,0.78" \
  --out runs/ami_lite_635 --separator lite --no-spark
python -m earshot bench runs/ami_lite_635 \
  --truth bench/ami_ES2008a_635/truth.json --repeat 3 --out runs/ami_lite_635/bench_review1.json

EARSHOT_REPLAY=1 python -m earshot analyze bench/ami_ES2008a/clip.mp4 \
  --tap "Speaker A@0.25,0.29" --tap "Speaker B@0.80,0.36" \
  --tap "Speaker C@0.31,0.78" --tap "Speaker D@0.71,0.78" \
  --out runs/ami_lite --separator lite --no-spark
EARSHOT_REPLAY=1 python -m earshot bench runs/ami_lite \
  --truth bench/ami_ES2008a/truth.json --repeat 3 --out runs/ami_lite/bench_review1.json
```

All three 745 s repeats map labels `{A:3, B:1, C:0, D:2}` to people `{C:0, A:3, D:2, B:1}`, exactly the oracle association. The fields `lite_mapping` and `oracle_mapping` are stored side by side in each bench JSON. The 635 s mappings differ by repeat and are included unchanged in `runs/ami_lite_635/bench_review1.json`.

Logs: `ami_lite_635_before_bench.log`, `ami_lite_635_review1.log`, `ami_lite_745_review1.log`, `lite_tuning_635.log`, `lite_tuning_635.json`, and `lite_tuning_635_bands.json`.

## 2. T5 ruling verification

Confirmed already applied, with no behavior change:

- README has the T5-base row (Google, open source, Apache-2.0), precomputed output or local `--allow-t5`, plus the exact organizer ruling and 2 Nov 06:06 Madrid link.
- `earshot/cli.py` says local T5 is allowed with the precomputed default.
- `earshot/separation.py` describes the precomputed default and allowed local T5 error/help path.
- `spike/earshot_spike.py` contains the updated ruling and setup notes.
- `assets/README.md` says the ruling allows T5 and keeps precomputed outputs as default.
- `docs/10_T5_RULING.md` is committed. Precomputed remains selected after the measured 80.776 dB comparison.

## 3. Spark AV bounded experiment

### Protocol

Eight 10-second windows of the public 75 s AMI clip were sent as `input_video` with audio, the corresponding Voice DIARIZATION turns, and normalized name/grid positions. `muse-spark-1.3` returned strict JSON per-person rough start/end/text. All hosted calls used `CallLog.cached`; outputs were never labelled verified. A first-window probe produced spoken text with plausible timing, so no audio-only fallback was needed.

```bash
python -m earshot analyze bench/ami_ES2008a/clip.mp4 \
  --tap "Speaker A@0.25,0.29" --tap "Speaker B@0.80,0.36" \
  --tap "Speaker C@0.31,0.78" --tap "Speaker D@0.71,0.78" \
  --out runs/spark_ami --separator spark-av --no-spark
python -m earshot bench runs/spark_ami \
  --truth bench/ami_ES2008a/truth.json --repeat 3 --out runs/spark_ami/bench_review1.json
```

A loop initially attempted an invalid 80–85 s window on the 75 s clip. `438d29f` fixed it and added a boundary regression test; completed windows replayed from cache.

### Result: negative, not enabled in the viewer

| Repeat metric | Spark AV | Single stream |
|---|---:|---:|
| WER | 0.852 [0.776, 0.897] | 0.231 [0.221, 0.237] |
| Right person | 0.496 [0.455, 0.529] | 0.919 [0.918, 0.921] |
| Overlap recall | 0.254 [0.244, 0.262] | 0.495 [0.444, 0.540] |

It fails all adoption gates: WER is worse, overlap recall does not improve by 10 points, and right-person is below 0.8. **Spark AV stays a documented negative experiment and is not shown in the viewer or demo.** Scorer output is in `spark_ami_bench.log`.

Usage: 33 uncached AV calls, estimated **$0.330758**, and approximately 36 minutes elapsed including earlier implementation checks. This is within the 2-hour/$3 experiment cap. Overall logged spend is **$2.377451 of $20.00**; this conservative total includes copied run histories in `SPEND.md`.

## Review checklist

- ✓ Small local commits; tests green; no push.
- ✓ Development/test windows and real before/after values recorded.
- ✓ Synthetic activity-vs-motion regression tests added.
- ✓ Lite and oracle mappings logged.
- ✓ T5 ruling text verified in every requested location.
- ✓ Spark AV bounded, cached, real JSON, unverified, and rejected by measured gates.
- ✓ Public `bench/RESULTS.md` and README contain every result, including the negative ones.
