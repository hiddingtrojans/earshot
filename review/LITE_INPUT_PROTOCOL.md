# Does cleaner input audio fix automatic binding?

Written 2026-11-04 shortly before 18:45 CET, before running the comparison. The protocol and its result were committed together, so the order is stated here, not proven by git history.

## Hypothesis

Binding failed on ES2008b mainly because the raw far-field diarization was poor (WER 0.78; three labels for four people). Diarizing the classical GCC-PHAT delay-and-sum 8-mic signal instead may give binding better input, with no threshold or code change to binding itself.

## Method (`tools/lite_input_probe.py`)

For each window (ES2008a 745 s, ES2008a 635 s, ES2008b 150 s), use the existing array run's cached SAM 3.1 tracks and its three cached Voice Transcribe repeats of (a) the raw `Array1-01` mix and (b) the delay-and-sum signal. On each repeat and input, run the unchanged `attribute_with_confidence` (30–60% mouth band, threshold 0.15), build captions with the unchanged timeline, and score them with `score_document`. The hand-matched oracle is computed on the **same** diarization. Replay mode only: a cache miss is an error, not a new call.

## Status of evidence

All three windows have been seen before, so this is **exploratory, not a held-out test**. A pass would justify a labelled array-input option and a future held-out test, not a general robustness claim.

## Pass rule (frozen)

Adopt as a labelled option only if all of these hold, by mean over the three repeats:

1. Delay-and-sum binding right-person ≥ raw binding right-person − 0.02 on both ES2008a windows (no meaningful regression).
2. On ES2008b, delay-and-sum binding right-person ≥ raw binding + 0.10.
3. On ES2008b, taps to reach the delay-and-sum oracle ≤ 1 in at least 2 of 3 repeats.

Otherwise: FAIL, reported in the README.

## Result: PASS (exploratory)

Run 2026-11-04 18:45 CET with `EARSHOT_REPLAY=1`; no new model calls. Output: `review/lite_input_probe.json`, `review/lite_input_probe.log`. Consistency check: the raw-mix rows reproduce the earlier bench results exactly (0.919; 0.547/0.693; 0.348/0.549).

Right-person, mean [min, max] over the same three repeats; the oracle is hand-matching on the same diarization.

| Window | Raw: binding | Raw: oracle | Raw taps | Delay-and-sum: binding | Delay-and-sum: oracle | Delay-and-sum taps |
|---|---:|---:|---|---:|---:|---|
| ES2008a 745 s | 0.919 [0.918, 0.921] | 0.919 | 0/0/0 | 0.913 [0.898, 0.925] | 0.914 | 0/0/0 |
| ES2008a 635 s | 0.547 [0.473, 0.693] | 0.693 | 1/1/0 | 0.690 [0.671, 0.712] | 0.690 | 0/0/0 |
| ES2008b 150 s | 0.348 [0.207, 0.475] | 0.549 | 2/2/2 | 0.512 [0.488, 0.549] | 0.512 | 0/0/0 |

- Rule 1 holds: −0.006 on 745 s (allowed −0.02) and +0.143 on 635 s.
- Rule 2 holds: +0.164 on ES2008b (required +0.10).
- Rule 3 holds: 0 taps in 3 of 3 ES2008b repeats.

On delay-and-sum input, binding equalled hand-matching in 9 of 9 repeats. What it cannot fix is transcription quality: on ES2008b even hand-matching reaches only 0.512–0.549. This applies only to recordings from a synchronized multi-mic array, and all three windows had been seen before, so the next step is a held-out meeting.
