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
