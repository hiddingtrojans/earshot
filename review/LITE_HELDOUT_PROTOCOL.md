# Held-out test: array-input binding on an unseen meeting (ES2008c)

Written 2026-11-04 shortly before 18:55 CET, before downloading any ES2008c media or running any model on it. This is the follow-up named in `review/LITE_INPUT_PROTOCOL.md`.

## Meeting

AMI **ES2008c**: no Earshot code, threshold or decision has used it. It is the same four participants and room as ES2008a/b, so this tests a new **meeting**, not new people or acoustics. Corpus metadata (`corpusResources/meetings.xml`) gives the same headset-to-camera mapping as ES2008a/b (A: Headset-0/Closeup4, B: Headset-1/Closeup2, C: Headset-2/Closeup3, D: Headset-3/Closeup1).

## Window (rule fixed before looking at media)

The ES2008b inclusion rule, unchanged: the **earliest** 75 s window, with starts on a 5 s grid from 0 s, that has at least two active speakers and at least 20 overlapping truth words (word-level timing). It is chosen from the manual word annotations only.

## Pipeline (unchanged code paths)

1. `tools/make_ami_clip.py --meeting ES2008c --start <W> --array`, with taps placed by inspecting `frame0.png` and written before any model call.
2. `tools/run_array_benches.py --meeting ES2008c --window <W> --subsets 8`: SAM 3.1 tracks, three raw-mix and three delay-and-sum Voice Transcribe repeats (live, first time).
3. `EARSHOT_REPLAY=1 python -m tools.lite_input_probe`, with ES2008c added to its window list and no other change.

Binding parameters stay as in the input protocol: 30–60% mouth band, confidence threshold 0.15.

## Pass rule (frozen)

By mean over the three repeats, with the oracle computed on the same diarization:

1. Delay-and-sum binding right-person ≥ delay-and-sum oracle right-person − 0.05.
2. Taps to reach the delay-and-sum oracle ≤ 1 in at least 2 of 3 repeats.

Raw-mix binding is reported alongside for comparison but does not decide the result. Anything else is a FAIL, reported in the README.

## Window selected (annotations only, before any media download)

Earliest eligible start: **355 s** (251 truth words, 22 overlapping words). Only **Speaker B and Speaker D** speak in it, so binding has to place two voices among four tapped faces. That is a weaker test than four active speakers; it is kept because the rule was fixed in advance.

## Taps (set on `frame0.png` before any model call)

The ES2008b taps were tried first because the seats are the same. On ES2008c's first frame, Speaker D's landed on the background and Speaker A's on hair, so all four were moved onto faces by eye: `Speaker A@0.22,0.33`, `Speaker B@0.81,0.37`, `Speaker C@0.33,0.77`, `Speaker D@0.75,0.80` (`bench/ami_ES2008c_355/taps.txt`). The builder's headset/motion sync check gives lag −0.08 s and −0.12 s for B and D; A and C do not speak in this window, so their correlations are near zero, as expected.

## Result: FAIL

Live run 19:03–19:25 CET (`review/ami_es2008c_355_array_8.log`), then the frozen probe cache-only (`EARSHOT_REPLAY=1`, `review/lite_heldout_probe.log`, `review/lite_input_probe.json`). The probe reproduced all three earlier windows exactly. New live calls: 1 SAM 3.1 (1,875 frames, ≈ $0.38 list price) and 24 Voice Transcribe calls of 75 s (≈ $0.09).

Right-person, mean [min, max] over the same three repeats; the oracle is hand-matching on the same diarization.

| ES2008c 355 s | Binding | Oracle | Taps to oracle |
|---|---:|---:|---|
| Raw single mic | 0.225 [0.000, 0.441] | 0.384 | 1 / 0 / 2 |
| Delay-and-sum 8-mic | 0.284 [0.195, 0.448] | 0.439 | 1 / 0 / 1 |

- Rule 1 **fails**: 0.284 is 0.155 below the oracle, against an allowed 0.05.
- Rule 2 passes: at most one tap in all three repeats.

The exploratory "binding equals hand-matching with no taps on array input" result does **not** generalize to this meeting. Array input still beats the raw mic (0.284 against 0.225), and one correction tap reaches the hand-matched mapping in every delay-and-sum repeat. Only two people speak in this window and right-person is averaged over all four tapped people, and the two silent people score 0, so the maximum possible mean is 0.50. That is why absolute values are low for every mode, the oracle included; the comparison uses the same metric throughout.
