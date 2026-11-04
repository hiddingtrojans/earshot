# Automatic binding on an independent meeting (ES2008b 150 s)

Written 2026-11-04 ~18:50 CET, before running Lite on this window or scoring it.

## Question

Does automatic voice-to-face binding (Earshot-Lite, fixed 30–60% mouth band, confidence threshold 0.15) hold up on a meeting that was never used to tune it? Until now it has been scored only on ES2008a (745 s primary, 635 s development).

## Setup

- Clip, taps, SAM 3.1 tracks and the three raw-mix diarization repeats come unchanged from `runs/ami_es2008b_150_array_8` (copied, not re-run). No parameter changes.
- `python -m earshot analyze bench/ami_ES2008b_150/clip.mp4 --tap ... --out runs/ami_es2008b_150_lite --separator lite --no-spark`
- `EARSHOT_REPLAY=1 python -m earshot bench runs/ami_es2008b_150_lite --truth bench/ami_ES2008b_150/truth.json --repeat 3 --out runs/ami_es2008b_150_lite/bench_repeat3.json`

## Already known before this run (disclosed)

The array run on this window already computed a Lite mapping on the primary diarization: Voice Transcribe found only three speaker labels for four people, and label B had confidence 0.061, below the 0.15 flag threshold. The README reports that the array run's automatic mapping needed two corrections. Lite caption metrics on this window have **not** been computed.

## Pass rule (frozen)

Both, on the same three repeats:

1. **Uncorrected right-person ≥ hand-matched (oracle) right-person − 0.05**, by mean.
2. **Taps to reach the oracle mapping ≤ 1 in at least 2 of 3 repeats**, and every mismatched label is one the confidence flag marks as low-confidence.

Otherwise the result is a FAIL and is reported as such in the README. Three labels for four people is a property of the input, not a reason to exclude the window.

## Result: FAIL

Run 2026-11-04 ~19:05 CET. Every model response came from the cache (`EARSHOT_REPLAY=1`); no new calls. Raw output: `review/lite_es2008b_150_bench.log`, `review/lite_es2008b_150_bench.json`.

| Mode (same 3 repeats) | WER ↓ | Right person ↑ | Overlap-word recall ↑ |
|---|---:|---:|---:|
| Matched by hand (oracle) | 0.781 [0.629, 0.911] | 0.549 [0.372, 0.807] | 0.131 [0.065, 0.167] |
| Earshot automatic binding | 0.839 [0.761, 0.893] | 0.348 [0.207, 0.475] | 0.096 [0.040, 0.192] |

- Rule 1 fails: 0.348 is 0.201 below the oracle, against an allowed 0.05.
- Rule 2 fails: 2 / 2 / 2 taps to reach the oracle mapping. In repeat 1, label B was mapped to the wrong person with confidence 0.256 and was **not** flagged; only C was flagged. The confidence flag therefore does not catch every error.
- Diarization was poor on this window even for the oracle (WER 0.78; three labels in two repeats for four people), so automatic binding started from weak input. That explains part of the gap but is not grounds for exclusion under this protocol.

No parameter was changed after seeing this result.
