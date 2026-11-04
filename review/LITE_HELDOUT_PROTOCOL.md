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
