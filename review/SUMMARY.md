# Earshot running summary

## Owner actions needed, in order

1. **Listen to all eight files in `review/ab_listen/` and compare them with `mixture.wav`.** Specifically compare `{A,B,C,D}_{keep,remove}.wav`. The agent computed metrics but did not listen to the stems and does not claim a listening check.
2. Keep **Lite** as the main mode and demo. The full SAM Audio `keep` run failed the quality gate; do not present it as overlap recovery or isolated listening.
3. Review and publish the local history and demo. **No push was performed in this run.**
4. Check VTT in VLC, including a long cue. VLC is not installed here, so that playback remains unverified.
5. Record the real ≤2:59 video with the opening new-work disclosure and AMI credit. Do not claim live processing, SAM Audio separation, or simultaneous-caption recovery from this Lite demo. Explain that local Glimmer handles cached catch-ups on this computer. Preserve the T5 ruling and link in README. If SAM Audio appears, show: “SAM Audio includes a frozen Google T5-base text encoder (open source). Allowed by the organizers; disclosed in the README.”
6. Check the video logged out, read back every submission field, and link the exact X post.

## Claude review round 2 — outcome

- **Mask semantics:** `keep` leaves the target visible; `remove` blacks out the target. The mode is in every separation cache key and a unit test checks the pixels. All eight real A/B WAVs are committed. Neither mode was diagonal-dominant; both scored 0.25 correct-voice rate on the 10 s A/B. Keep/remove waveform pairs correlate at 0.999955–0.999986. **`keep` is the semantic default, not an A/B winner.**
- **Primary quality decision:** SAM Audio `keep` is **NO-GO** on the 745 s clip. Right-person 0.386 is below 0.80; overlap recall 0.098 is below the same-run baseline +0.10 threshold of 0.580. WER is 0.967. This is not a speed-only rejection.
- **Timing:** per-person MPS separation took **773.889 s including loading**. Window wall totals were A 165.1 s, B 183.2 s, C 203.5 s and D 196.1 s; model inference totals were 161.775, 179.909, 200.073 and 193.504 s. Four-person MPS/CPU batching stalled and was not used for the completed run. Per-window cleanup is real and timed.
- **Audio metric:** correct-voice rate replaces the SI-SDR headline. Primary stems score **0.500**, mixture **0.250**. SI-SDR remains in JSON with the far-field caveat; primary `keep` gain is -0.008 dB. The full matrix is in `bench/RESULTS.md` and `GATE_REVIEW2.md`.
- **Held-out check:** the 635 s SAM Audio `keep` run also finished before 23:00 Madrid and is **NO-GO**: WER 2.731 [1.097, 3.825], right-person 0.382 [0.296, 0.537], overlap recall 0.185 [0.158, 0.230], correct-voice 0.250. Single-stream overlap recall is 0.486. Separation took 772.703 s; speed is not the rejection reason. The full matrix and timings are in `bench/RESULTS.md` and `GATE_REVIEW2.md`.
- **Lite:** the 30–60% band was fixed by the reviewer before results. The 60–90% band won on 635 s but scored 0.537 on 745 s and is rejected. Both windows are reported below; no test-window tuning is claimed.
- **Corrections:** threshold 0.15 fixed in advance. Taps to oracle: **0 / 0 / 0 on 745 s**, **1 / 1 / 0 on 635 s**. One-tap corrections move captions immediately, preserve other labels' confidence, save history, and replay without duplicate activity. Browser and synthetic tests passed.
- **Demo/tagline:** retained the real Lite demo. Tagline is **“Every voice at the table, captioned under the right face.”** in README, viewer and package metadata. Lite is described as voice attribution, not audio separation.
- **Local Glimmer:** the packaged demo has `"catchup_model": "glimmer"`, 35 cached catch-ups, 15 local inference calls and additional replay hits. The rendered model table says **On this computer**. A key-free request with unreachable endpoints returned three verified sentences. Demo size is **42.67 MB**.
- **Tests:** main suite **70 passed**. Final fresh clone/base install: **69 passed, 1 optional Torch-dependent skipped**, with offline VTT/SRT export and Glimmer replay passing. `test_sparkav.py` uses synthetic media; no AMI clip is needed in a clean clone.

## Current benchmark

Mean [min, max] over three real Voice repeats. The primary SAM comparison uses its own repeats; Lite and Spark AV retain their previously reported cached repeats. Exact evidence and per-window timing are in `bench/RESULTS.md` and `review/GATE_REVIEW2.md`.

| Mode | WER ↓ | Right person ↑ | Overlap-word recall ↑ | Correct voice ↑ |
|---|---:|---:|---:|---:|
| Single stream (oracle; primary SAM repeats) | 0.239 [0.231, 0.246] | 0.913 [0.906, 0.918] | 0.480 [0.463, 0.513] | — |
| Earshot-Lite (745 s) | 0.231 [0.221, 0.237] | 0.919 [0.918, 0.921] | 0.495 [0.444, 0.540] | — |
| Lite development check (635 s) | 2.571 [0.395, 3.719] | 0.547 [0.473, 0.693] | 0.553 [0.424, 0.624] | — |
| SAM Audio `keep` (745 s) | 0.967 [0.749, 1.227] | 0.386 [0.301, 0.546] | 0.098 [0.037, 0.141] | 0.500 |
| SAM Audio `keep` (635 s held-out) | 2.731 [1.097, 3.825] | 0.382 [0.296, 0.537] | 0.185 [0.158, 0.230] | 0.250 |
| SAM Audio legacy `remove` (745 s) | 0.916 [0.896, 0.935] | 0.464 [0.385, 0.555] | 0.117 [0.097, 0.146] | 0.250 |
| Spark AV experiment (unverified) | 0.852 [0.776, 0.897] | 0.496 [0.455, 0.529] | 0.254 [0.244, 0.262] | — |

Spark AV failed every adoption gate and is not a viewer mode. The negative control produced **0 empty-tap captions**. T2's sync heuristic remains inconclusive for C/D; no timeline correction was made.

## Earlier gates, still applicable

- **T0:** bundle at `~/src/earshot`; original app had 8 commits; baseline reached 26 passed after installing the existing optional Torch extra.
- **T1/T2:** real SAM 3.1, Voice and Spark smoke passed. Deterministic public ES2008a clips, truth, references, taps and attribution were generated; primary has 234 words and 53 overlapping words.
- **T3 conditioning:** precomputed versus local T5 measured 80.776 dB, so precomputed `assets/text_features.npz` remains the default. The organizers explicitly allow `--allow-t5`; the ruling is quoted in README and `docs/10_T5_RULING.md`.
- **T4:** reviewed Lite correlation and negative control are recorded above. Spark AV is a documented negative experiment.
- **T5–T9:** tap-to-start, replay snapping, real cached demo, Spanish validation, offline VTT/SRT and exports passed their earlier checks. Long WebVTT cues can render poorly in some players; VLC remains unverified.
- **T10:** local Glimmer is now included in the full 75 s demo, with local provenance and citation verification.
- **T11/T12:** README documents real results, limitations, model locations, replay/setup/export, responsible use and attribution. Earlier clean-clone, banned-runtime and history secret scans passed; the final review-2 clean clone is recorded in `review/clean_clone_review2.log`.

Earlier evidence: `GATE_T1.md`, `GATE_T3.md`, `GATE_T4.md`, `GATE_T6.md`, `GATE_T12.md`, `CONDITIONING.md`, and `GATE_REVIEW1.md`.

## Estimated spend

**$3.286617 of $20.00**, from 261 real cache-miss/local entries used by the pricing report. Cache hits and local inference cost $0. This includes both new full SAM Audio evaluations and the previously omitted 635 s development run. See `SPEND.md` for per-call usage and arithmetic.

Spark AV used 33 uncached AV calls and **$0.330758**, within its 2-hour/$3 experiment cap. Local Glimmer and cached responses add $0. `SPEND.md` now includes the 635 s development run omitted from the earlier report, as well as the new full evaluations.

## Evidence and remaining external work

See `GATE_REVIEW2.md`, `bench/RESULTS.md`, `ami_samaudio_keep_mps_analyze.log`, `ami_samaudio_keep_bench_review2.log`, `ami_samaudio_keep_635_analyze.log`, `ami_samaudio_keep_635_bench_review2.log`, `clean_clone_review2.log`, and `SPEND.md`.

Engineering implementation and the requested reviews are local and committed. Owner listening, VLC playback, publication, video and submission remain external/owner tasks; no unverified listening or publication is claimed.
