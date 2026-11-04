# Different cast, different room: AMI IS1009a

Written 2026-11-04 ≈20:35 CET, before choosing a window, before downloading any IS1009a media, and before any model call on it. Committed before all three.

## Why

ES2008a–d share four people and one Edinburgh room. Every threshold in Earshot-Lite (mouth band, confidence 0.15) was tuned or inspected on ES2008a. IS1009a was recorded at Idiap with four different people, different cameras and a different microphone array. It is the first test of whether anything transfers.

## Setup

- Camera/headset mapping from `corpusResources/meetings.xml` in the AMI public annotations 1.6.2: A = Headset-0 / Closeup1, B = Headset-1 / Closeup2, C = Headset-2 / Closeup3, D = Headset-3 / Closeup4.
- `tools/make_ami_clip.py` reads this mapping from `meetings.xml` for any meeting instead of the hard-coded ES2008 table (ES2008a–d mapping unchanged, checked against the table).
- **Window rule (same as ES2008d):** the earliest 75 s window on a 5 s grid from 0 s with at least three active speakers and at least 20 overlapping truth words, from annotations only. A word overlaps if its span intersects a word of another person.
- Taps set on `frame0.png` before any model call and committed.
- Same pipeline: three diarization repeats on raw single-mic and GCC-PHAT delay-and-sum 8-mic input.

## Pass rules (frozen, same as ES2008d)

- **2a, binding:** delay-and-sum right-person ≥ oracle − 0.05, and ≤ 1 tap to oracle in at least 2 of 3 repeats. Raw reported too.
- **2b, per-face verifier** and **2c, pairwise verifier:** on delay-and-sum input, no correct binding broken and at least half of the flagged labels resolved. Not evaluable if nothing is flagged.

Every result, pass or fail, goes in the README.

## Window selected (annotations only, before any media download)

Earliest eligible start: **250 s** (153 truth words, 34 overlapping, speakers A, B, D active; C silent in this window and scores 0 attribution by construction, as everywhere else). The metadata mapping reproduces the hard-coded ES2008a–d table exactly.

## Taps and sync (set ≈20:50 CET, before any model call on IS1009a)

`Speaker A@0.33,0.31`, `Speaker B@0.65,0.36`, `Speaker C@0.29,0.89`, `Speaker D@0.79,0.79`, on face centres after a visual overlay check.

The builder's headset-energy vs lower-face-motion sync check warns for all four (lags 0.72–1.0 s, correlation 0.09–0.44). The same check is as noisy on ES2008 (lags up to ±1.0 s, correlations down to −0.07), so it is not treated as evidence of misalignment; nothing is shifted. Recorded in `bench/ami_IS1009a_250/sync.json`.

## 2d: Spark pairwise vote binds every label (pre-registered ≈21:05 CET, before the IS1009a bench finished and before any IS1009a binding or verifier output was seen)

Motivation: on ES2008d delay-and-sum the pairwise clip votes were right 6 of 6 (3 of 5 on raw; first written as "7 of 7", a miscount, corrected 21:10 with no change to the rule), while Earshot-Lite was confidently wrong on 2 labels the verifier never looked at. 2d applies the pairwise verifier (`tools/pair_verify_probe.py`, unchanged prompt, strips and clip rule) to **every** diarized label, not only flagged ones. A label moves when 2 of its clips vote for the same face (collision rule unchanged); otherwise the Earshot-Lite binding stays.

- Exploratory on the seen windows (ES2008a–d), delay-and-sum and raw, reported either way.
- **Deciding, IS1009a delay-and-sum:** PASS only if mean right-person after 2d ≥ Earshot-Lite mean + 0.05 on the same three repeats, **and** 2d is not worse than Lite on any repeat. Raw reported.

## 2a result: PASS

Bench `python tools/run_array_benches.py --meeting IS1009a --window 250 --subsets 8` (`review/ami_is1009a_250_array_8.log`), then the cache-only probe (`review/lite_heldout_probe_2.log`; earlier rows reproduced exactly).

| Input | Binding | Oracle | Taps to oracle |
|---|---:|---:|---|
| Delay-and-sum 8-mic | 0.424 | 0.424 | 0, 1, 0 |
| Raw single mic | 0.674 | 0.683 | 1, 0, 0 |

Delay-and-sum binding ≥ oracle − 0.05 and ≤ 1 tap in 3 of 3 repeats: **PASS**. On a new cast, room, cameras and array, automatic binding matches the oracle mapping on the same diarization; one tap at most. The ceiling here is diarization (oracle 0.42 on delay-and-sum vs 0.68 on raw), not binding.

## 2e: more clips per label (pre-registered ≈21:25 CET, while the IS1009a verifier runs were in progress and before any of their output was read)

Exploratory 2d on the seen windows (`review/pair_verify_probe_not_is1009a_all.{json,log}`): cast pairwise clip votes were right 41 of 54 on delay-and-sum and 38 of 53 on raw, yet 2d changed nothing beyond 2c, because most labels have only one solo turn ≥ 1.5 s and never reach 2 agreeing clips.

2e = 2d with: solo turns ≥ **1.0 s** (was 1.5), up to **5** clips per label (was 3), clips still ≤ 2.5 s from each turn's middle. A label moves to a face only if that face has **≥ 2 votes and strictly more than any other face**; otherwise the Earshot-Lite binding stays. Collision rule unchanged.

- Exploratory on ES2008a–d, reported either way.
- **Deciding, IS1009a delay-and-sum:** same rule as 2d (mean right-person ≥ Lite + 0.05 on the same repeats, and not worse on any repeat). Raw reported.
