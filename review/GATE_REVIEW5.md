# GATE — Claude review round 5: microphone array and caption presentation

Date: 2026-11-03. SAM Audio separation experiments are closed. Small local commits, tests green. The final instruction explicitly authorizes one fast-forward push after the secret scan.

## Reference availability and data

**The supplied reference script is missing.** `/Users/raulacedo/Downloads/array_exp.py` does not exist. Searches of Downloads, Desktop, Documents, `src`, `/tmp`, and likely agent-work folders found no copy. It has therefore **not been copied to `docs/array_exp.py`**, and its exact reported matrix is not claimed as reproduced. Saving the real file there later would enable that separate check.

The independent implementation's initial 0–10 s probe scored correct-voice **0.50**, diagonal mean **0.6703**, off-diagonal mean **0.2023**. That was not used for the go/no-go decision. The integrated full-clip matrix is reported separately below; it differs because all 75 s of guide/covariance data are used and the full reference window is scored.

`tools/make_ami_clip.py --array` downloads `ES2008a.Array1-01` through `Array1-08` from the AMI mirror and writes eight-channel, 16 kHz `array.wav` for 745–820 s and 635–710 s. Existing download code retries HTTP 403 and other URL errors; a test proves a 403 retry and the eight-channel output shape. Media remains ignored under `bench/` and `runs/`.

```bash
python tools/make_ami_clip.py --array --out bench/ami_ES2008a
python tools/make_ami_clip.py --array --start 635 --out bench/ami_ES2008a_635
```

Implementation commits: `5161912` (data), `6320816` (fixed motion guide), `8894b38` (MVDR), `b379dac` (pipeline and baselines), `596bd58` (sentence/motion presentation), `16a6994` (batch runner and probe), `7fd3dc1` (array evaluation and NO-GO). Tests: **94 passed**.

## Array implementation

`earshot/array.py` uses only numpy/scipy: STFT 512/hop 128, per-person solo-target covariance from runtime guide activity, covariance from frames where that person is inactive, diagonal loading `1e-3*trace/D`, loaded Souden solve, SNR-selected input reference channel, and inverse Hann overlap-add reconstruction. Stems are resampled from 16 kHz to 24 kHz for Voice Transcribe and the usual timeline. The source, the loaded solve, and reference selection were tested on synthetic targets and then real AMI data. The supplied reference file was not available for a line-by-line comparison.

The guide recomputes Lite mouth-band/Hungarian mapping from cached diarization and applies `corrections.json` if present. Missing mapped turns use fixed-threshold mouth motion: 0.5 s smoothing, `max(0.1, median + 3×MAD)`, 0.5 s minimum events. On 635 s, Speaker C has no mapped turns and uses this fallback with threshold **0.56507652**. The automatic mapping is `{A:1, B:3, C:0}`; it already matches the oracle association, so **0 correction taps** are needed and the corrected mapping is identical. No duplicate “corrected” run or oracle product result is claimed.

`--separator array --array PATH` supports all eight channels and 1-based subsets. `array_delay_sum.wav` is an independently scored GCC-PHAT-aligned delay-and-sum baseline using all eight channels. `array_baseline` is kept separate from the existing Array1-01 single-stream baseline. The scorer prints and records both baselines.

## 745 s results — **AMI 8-mic meeting-room array**

Values are mean [min, max] over three real Voice repeats. Better baseline overlap is the larger of Array1-01 and GCC-PHAT delay-and-sum. The gate is right-person >= 0.80 and overlap recall >= better baseline +0.10.

| Channels | WER ↓ | Right person ↑ | Overlap recall ↑ | Better baseline +0.10 | Correct-voice rate | Diagonal mean | Off-diagonal mean | Beamforming (s) | Analysis (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 (1–8) | 0.282 [0.240, 0.322] | 0.844 [0.835, 0.850] | 0.605 [0.555, 0.662] | 0.522 + 0.10 = 0.622 | 1.000 | 0.6291 | 0.0229 | 1.835 | 64.294 |
| 5 (1–5) | 0.845 [0.715, 1.078] | 0.658 [0.570, 0.709] | 0.396 [0.349, 0.440] | 0.527 + 0.10 = 0.627 | 1.000 | 0.5772 | 0.0664 | 0.948 | 66.270 |
| 4 (1,3,5,7) | 0.740 [0.505, 1.127] | 0.638 [0.515, 0.708] | 0.392 [0.331, 0.470] | 0.502 + 0.10 = 0.602 | 1.000 | 0.5842 | 0.0502 | 0.676 | 67.298 |

**745 s NO-GO for every subset.** Eight channels passes right-person but misses the overlap margin by **0.017**. Five and four channels fail both right-person and the overlap margin. Array1-01 overlap recall is 0.495, 0.495 and 0.495 respectively; delay-and-sum is the better baseline at 0.522, 0.527 and 0.502. Exact repeat values and run metadata are in `review/array_745_summary.json` and `review/array_745.log`.

Eight-channel correct-voice matrix, rows intended speakers and columns headset references A/B/C/D:

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| Speaker A | **0.7629** | -0.0276 | -0.1870 | 0.1365 |
| Speaker B | 0.1444 | **0.4798** | 0.0878 | 0.1424 |
| Speaker C | -0.1037 | 0.0814 | **0.8092** | 0.0421 |
| Speaker D | 0.0475 | -0.0353 | -0.0536 | **0.4644** |
| Mixture | **0.3887** | 0.0834 | 0.0950 | 0.2559 |

All four rows win their own headset, but that does not satisfy the transcription gate. Five- and four-channel matrices also have correct-voice rate 1.000, with the diagonal/off-diagonal means above. Their full matrices are in `review/array_745_summary.json`.

## 635 s results — **AMI 8-mic meeting-room array**

Values are mean [min, max] over three real Voice repeats. The better baseline is Array1-01 single stream in every subset; its overlap recall is 0.486, so the threshold is 0.586.

| Channels | WER ↓ | Right person ↑ | Overlap recall ↑ | Better baseline +0.10 | Correct-voice rate | Diagonal mean | Off-diagonal mean | Beamforming (s) | Analysis (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 (1–8) | 0.403 [0.376, 0.451] | 0.680 [0.623, 0.714] | 0.437 [0.428, 0.442] | 0.486 + 0.10 = 0.586 | 0.750 | 0.5599 | 0.1129 | 1.907 | 58.664 |
| 5 (1–5) | 1.498 [0.418, 3.122] | 0.584 [0.429, 0.672] | 0.418 [0.378, 0.448] | 0.486 + 0.10 = 0.586 | 0.750 | 0.5571 | 0.1421 | 0.897 | 62.282 |
| 4 (1,3,5,7) | 4.482 [3.452, 5.327] | 0.434 [0.378, 0.516] | 0.478 [0.398, 0.522] | 0.486 + 0.10 = 0.586 | 0.750 | 0.5545 | 0.1387 | 0.662 | 60.660 |

**635 s NO-GO for every subset.** All three fail right-person and the overlap margin. Overlap deltas are -0.049, -0.068 and -0.008 respectively. The 8-channel delay-and-sum baseline is 0.449, 0.406 and 0.449; raw Array1-01 remains the better baseline at 0.486.

The automatic mapping is `{A:1, B:3, C:0}` and the mapping after one-tap correction is identical, with **0 taps**. The oracle association is `{C:Speaker A, A:Speaker B, B:Speaker D}`, used only to check how many correction taps were needed, not as a runtime product claim. Speaker C uses the fixed motion fallback at threshold 0.56507652. `review/array_635_summary.json` records the mapping, all repeat metrics, matrices and runtime metadata.

## Caption presentation, either way

Sentence-sized bubbles split punctuation-aware text into chunks of at most 12 words and estimate timing from text length. Original caption IDs and citation IDs are unchanged; nested `sentences` and `translation_segments` carry the same original ID. The viewer labels **estimated timing** and uses unique DOM segment IDs internally. Real browser checks showed that label, and the exact motion marker at 7.28–8.08 s.

Lite “was also talking” labels are **motion estimates**, not verified speech. Fixed protocol: 0.5 s smoothing, `max(0.1, median + 3×MAD)`, 0.5 s minimum events. Actual frame-level precision/recall against AMI truth:

| Window | Precision | Recall |
|---|---:|---:|
| 745 s single-mic Array1-01 | 0.0987 | 0.1888 |
| 635 s single-mic Array1-01 | 0.0695 | 0.1181 |

These weak results are disclosed. They are not evidence of recovered overlap words. See `review/motion_overlap.json` and `tools/bench_motion_overlap.py` for per-person values and exact thresholds.

## SAM Audio conclusion

SAM Audio removed noise from speech in the controlled reference/noise sanity setup (**+16.8751 dB SI-SDR**), but no face or time-span prompt isolated one speaker from the others, on far-field or clean-mic audio. Separation work on SAM Audio is closed.

## Conditional demo decision

**NO-GO on both windows. No array demo is built and Lite remains the default demo and single-mic mode.** `demo/ami_meeting_array` was not created, and the talking-at-once tagline is not restored. The enriched Lite demo keeps sentence estimates and motion labels; no new default or overlap-recovery claim is made. No claim is made that Earshot runs on glasses.

## Verification and evidence

- Main tests: **94 passed**, including synthetic MVDR separation, delay estimation, subset selection, loaded covariance solve, STFT round-trip amplitude, and summary statistics.
- Final fresh clone/base install: **93 passed, 1 optional Torch-dependent skipped**, with no credentials or model downloads. Log: `review/clean_clone_review5.log`.
- Browser checks showed `estimated timing` and `Speaker A was also talking (motion estimate)` at the real 7.28–8.08 s marker. Temporary seek/error hooks used for that check were removed.
- `tools/run_array_benches.py` ran all 8/5/4-channel analyses and three-repeat benches on both windows.
- `review/array_745_summary.json`, `review/array_635_summary.json`, `review/motion_overlap.json`, `review/array_probe.log`, and the ignored `runs/*/bench_array.json` preserve the actual outputs.

Estimated hosted spend is **$4.115609 of the $20 cap**, from `review/SPEND.md`. This includes the preserved unintended fresh tracking run (a $0.375 SAM 3.1 charge), all six array analyses and baseline/delay-sum transcriptions, and the earlier clean-mic baseline. Local MVDR work and cached responses add no further charge. The optional SAM Audio noise-cleaning experiment was not run: the array is NO-GO and the original reference reproduction is unresolved. No credential value was printed or committed.
