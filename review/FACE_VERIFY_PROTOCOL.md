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

## ES2008d window selected (annotations only, before any media download)

Earliest eligible start: **120 s** (248 truth words, 28 overlapping words, all four speakers active).

## Amendment before the evaluation run (≈19:58 CET)

Smoke test only, on one known solo span of Speaker A in ES2008a (16.7 s, 2.5 s; not part of any scored case):

- **Per-face muted video** (the design above): A `unclear`, B `unclear`, C `unclear`, D `no`. Spark apparently samples too few frames from a 2.5 s clip to see lip motion.
- **Per-face 8-frame strip image** (the same crop, 8 frames ≈ 0.3 s apart tiled 4×2, sent as one `input_image`): A `yes`, B `unclear`, C `unclear`, D `no`, which is a correct vote for A.

The evaluation therefore uses the **strip image** instead of video. Everything else (flagged labels only, clip spans, enum answers, exactly-one-yes clip vote, 2-of-3 label rule, collision rule, both pass rules) is unchanged. No scored case has been run with either variant.

## Part 1 result: FAIL

Run 2026-11-04 20:03 CET (`python -m tools.face_verify_probe --live`; `review/face_verify_probe.json`, `review/face_verify_answers.json`, `review/face_verify_probe.log`). 296 per-face strip calls for 74 clips (≈ 830 input tokens each; roughly $0.35 at list price).

| Input | Flagged | Resolved | Fixed | Broken |
|---|---:|---:|---:|---:|
| Raw single mic | 19 | 1 | 0 | 0 |
| Delay-and-sum 8-mic | 18 | 1 | 0 | 0 |

- Spark said `yes` to 156 of 296 face strips, usually for two or three faces in the same clip, so only 17 of 74 clips cast a vote.
- When exactly one face was `yes`, it was the right person in **5 of 17** clips, no better than choosing at random among four people.
- Delay-and-sum rules: 0 of 2 errors fixed (needed ≥ 1), 0 broken, 1 of 18 flags resolved (needed ≥ 9). FAIL. The 2-of-3 rule again kept the noise from breaking any binding.

## ES2008d taps (set 20:07 CET on `frame0.png`, before any model call on ES2008d)

`Speaker A@0.22,0.33`, `Speaker B@0.79,0.37`, `Speaker C@0.31,0.81`, `Speaker D@0.75,0.86`. The builder's default taps put C and D on foreheads; all four moved onto the face centre after a visual check of the overlay.

## 2c: pairwise verifier (pre-registered 20:15 CET, before any pairwise call)

Part 1 failed because Spark said `yes` to two or three faces per clip; the grid probe failed on a fixed position bias. `tools/pair_verify_probe.py` forces a choice and cancels position:

- Same flagged labels, clip spans and 8-frame face strips as Part 1.
- For each clip, every ordered pair of faces (12 for four people): the two strips side by side, `muse-spark-1.3`, low reasoning, enum `"left"` / `"right"` / `"unclear"`.
- A pair is decided only if **both orders** name the same face. A clip votes for a face only if it wins **all** of its pairs. Label rule (2 of 3 clips) and collision rule unchanged.
- **Exploratory, on the four seen windows**: same pass rule as Part 1 (delay-and-sum: ≥ 1 of 2 errors fixed, none broken, ≥ half of flags resolved). Reported either way.
- **Deciding, ES2008d only**: same as 2b (delay-and-sum: no correct binding broken, ≥ half of flags resolved). Run once, regardless of the exploratory result.
- Tooling change committed with this section: `--only <window prefix>` restricts the verifiers to one window and writes `review/*_<meeting>.json`, so ES2008d results stay separate and the Part 1 files are not overwritten.

## 2c exploratory result (seen windows): FAIL

Run 2026-11-04 ≈20:30 CET (`python -m tools.pair_verify_probe --live --only '!ES2008d'`; `review/pair_verify_probe_not_es2008d.{json,log}`, `review/pair_verify_answers_not_es2008d.json`). 768 pair images for 64 clips (12 ordered pairs each), one `muse-spark-1.3` call each. A smoke test on the solo-A span voted A before the run. The only code change after the 2c commit was an exclusion filter (`--only '!ES2008d'`), because the ES2008d run did not exist yet.

| Input | Flagged | Resolved | Fixed | Broken |
|---|---:|---:|---:|---:|
| Raw single mic | 19 | 3 | 1 | 0 |
| Delay-and-sum 8-mic | 18 | 1 | 1 | 0 |

- Both orders agreed on 260 of 384 face pairs; a left/right bias remains (362 `left` vs 325 `right`).
- A clip voted in 34 of 74 cases and was right **19 of 34** (56%, chance 25%). Part 1 managed 5 of 17. Better than chance, still too unreliable for 2 of 3 clips to agree.
- Delay-and-sum: 1 of 2 errors fixed (rule met), 0 broken (met), 1 of 18 flags resolved (needed ≥ 9). **FAIL.** No binding was broken on either input.

## Part 2 results on ES2008d (held out)

Bench: `python tools/run_array_benches.py --meeting ES2008d --window 120 --subsets 8` (`review/ami_es2008d_120_array_8.log`). Verifiers: `--live --only ES2008d` (`review/{face,pair}_verify_probe_es2008d.{json,log}`).

Earshot-Lite binding is far below the oracle on this window (delay-and-sum 0.197 vs oracle 0.616; raw 0.089 vs 0.664), and two wrong delay-and-sum bindings were **confident**, so they were never shown to a verifier.

| Rule (delay-and-sum) | Flagged | Resolved | Fixed | Broken | Result |
|---|---:|---:|---:|---:|---|
| 2b per-face | 6 | 0 | 0 | 0 | **FAIL** (all 8 clip votes `unclear`) |
| 2c pairwise | 6 | 1 | 1 | 0 | **FAIL** (needed ≥ 3 resolved) |

The pairwise clip votes that were cast were right 6 of 6 on delay-and-sum input (3 of 5 on raw), which motivated 2d (`review/IS1009A_PROTOCOL.md`).
