# Per-face Spark verifier, and a second held-out meeting (ES2008d)

Written 2026-11-04 shortly before 19:50 CET, before any per-face verifier call and before downloading or annotating-by-window anything from ES2008d. Committed before both.

## Why a new design

`review/SPARK_VERIFY_PROTOCOL.md` failed: shown the whole numbered 2×2 grid, Spark mostly said "unclear" and otherwise always named the same grid position. This design removes the position choice: Spark sees **one face at a time** and answers whether that person is talking.

## Per-face verifier (`tools/face_verify_probe.py`)

- Same flagged labels (confidence < 0.15), same clip spans as the grid verifier: up to 3 of the label's non-overlapping turns ≥ 1.5 s, at most 2.5 s each, muted. Only runtime information chooses them.
- For each clip and each tapped person: a crop centred on that person's tap (35% of frame width × 45% of frame height, clamped to the frame), upscaled 2×. One `muse-spark-1.3` call per crop, low reasoning, strict enum `"yes"` / `"no"` / `"unclear"`: is this person talking?
- A clip **votes** for a person only if exactly one crop is `"yes"`. A label is confirmed or moved only if at least 2 clips vote for the same person, under the same collision rule as before; otherwise it stays flagged for a human.

## Part 1: exploratory, on the four seen windows

PASS only if, on delay-and-sum input: at least 1 of the 2 wrong bindings is fixed, no correct binding is broken, and at least half of the flagged labels are resolved. Raw single-mic results are reported but do not decide.

## Part 2: held out, ES2008d

- Same participants and room; corpus metadata gives the same headset/camera mapping as ES2008a–c (checked 18:5x from `meetings.xml`).
- **Window rule, fixed now:** the earliest 75 s window on a 5 s grid from 0 s with at least **three** active speakers and at least 20 overlapping truth words, chosen from annotations only. (The ES2008c rule allowed two speakers; three is required here, decided before seeing ES2008d.)
- Taps set on `frame0.png` before any model call, then the same pipeline as ES2008c.
- **2a, array-input binding (re-test of the ES2008c FAIL):** delay-and-sum binding right-person ≥ oracle − 0.05, and ≤ 1 tap in at least 2 of 3 repeats.
- **2b, per-face verifier:** on delay-and-sum input, no correct binding broken and at least half of the flagged labels resolved. If nothing is flagged, 2b is not evaluable.

Every result, pass or fail, goes in the README.
