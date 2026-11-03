# Earshot running summary

## Owner actions needed, in order

1. **Listen to the array stems and the eight files in `review/ab_listen/`.** The agent verified browser audio requests and playback, but did not perceptually assess the audio and does not claim a listening check.
2. Keep **Lite** as the default demo. The optional `demo/ami_meeting_array` is explicitly experimental: its ES2008a overlap-recall gate failed. Do not present it as verified overlap recovery, real-time processing, or software running on glasses.
3. Review and publish the local history and demo. **The final instruction authorizes a fast-forward push after the secret scan.**
4. Check VTT in VLC, including a long cue. VLC is not installed here, so that playback remains unverified.
5. Record the real ≤2:59 video with the opening new-work disclosure and AMI credit. Explain that local Glimmer handles cached catch-ups and evidence checks on this computer. Preserve the T5 ruling and link in README. If SAM Audio appears, show: “SAM Audio includes a frozen Google T5-base text encoder (open source). Allowed by the organizers; disclosed in the README.”
6. Check the video logged out, read back every submission field, and link the exact X post.

## Parallel experiment and independent validation — 3 Nov

- **Product direction:** an accessible overlapping-conversation player with isolated listening, cited catch-ups, and evidence-checked questions/commitments. It is not presented as a proven winner or a successful separation claim. The default remains Lite; the array player is a separately labelled experiment.
- **Real evidence board:** local Glimmer supported three literal questions (`c006`, `c009`, `c011`) and rejected the proposed commitment (`c012`) as **insufficient** because “I'll look into it. If I can.” is conditional. Unsupported proposals stay inspectable with original caption IDs and verbatim evidence. No messages, tasks, or calendar events are created automatically.
- **Complete replay:** `demo/ami_meeting_array` is 47.71 MB with four isolated stems, delay-and-sum comparison audio, 35 local catch-ups, two threads, Spanish translation, and the board. The browser showed “Both talking”, loaded Speaker C's stem with successful range responses, played it to the end, rendered a cited precomputed catch-up, and exposed the rejected proposal. Replay did not alter the packaged `earshot.json` or `calls.jsonl` hashes.
- **Review fixes:** Droid ran read-only through the owner's configured GLM Coding Plan (`custom:GLM-5.3-[Z.AI-Coding-Plan]-0`). It identified experimental-claim, replay, and evidence-verification risks. The implementation now reports the real quality gate, warns that lip-sync is unverified, preserves replay evidence, validates packaged caption fields, serves precomputed catch-ups on cache misses, and withholds isolated audio for degenerate guides. The uncertain camera-motion lag is not applied as a correction.
- **Verification:** main suite **111 passed**. Fresh clone/base install at the demo-packaging commit **109 passed, 1 optional skipped**, plus strict offline catch-up/board/stem/hash smoke (`review/parallel_clean_clone.log`). A separate strict-replay check reproduced all **35 catch-up windows (27 nonempty), the board, both threads and Spanish translation exactly**, with unchanged provenance (`review/parallel_cached_calls_check.log`). Earlier failures in the clean-clone command came from forcing replay on tests that intentionally mock live calls; the standard offline suite and separate strict-replay check passed.
- **Independent data audit:** public ES2008b at 745 s has 217 truth words, all from Speaker C, and **zero overlapping words**. Its three-repeat overlap gate is **not evaluable**, not a pass or failure; automatic mapping found the correct single active label (`A → Speaker C`). Full metrics are in `review/ami_es2008b_array_8_summary.json`. The 635 s candidate has only two overlapping words and was not run. Before any model inference on a replacement, the inclusion rule was fixed at ≥2 active speakers and ≥20 overlapping truth words. The earliest eligible 75 s window is **150 s**, with 110 words, 44 overlapping words, and all four speakers active. Corpus camera metadata and actual first-frame face taps were checked. `tools/run_array_benches.py --meeting ES2008b --window 150 --subsets 8` runs the same fixed pipeline and three-repeat baselines; its result is recorded below. No synthetic meeting is robustness evidence.
- **Spend:** the first independent run brought estimated hosted spend to **$4.591059 of $20**. The eligible run is additional and is included in the final report. Local Glimmer inference costs $0. `review/SPEND_PARALLEL.md` is generated from uncached calls only.

## Claude review round 5 — microphone array and captions

- **Reference limitation:** the supplied `~/Downloads/array_exp.py` is missing and no copy exists at `docs/array_exp.py`. Its exact 4/4, 0.66 matrix is not claimed as reproduced. The independent implementation is committed and measured. If a direct reference comparison is required, save the real reference file at that path.
- **Array evaluation:** `array.wav` was generated at 16 kHz for both windows. `--separator array` uses runtime Lite/corrected guides, missing-label motion fallback, loaded Souden MVDR, Voice transcription, and a GCC-PHAT delay-and-sum baseline. It is classical numpy/scipy processing, not a new AI model.
- **745 s:** 8 channels reached 4/4 correct-voice rows (diagonal 0.6291, off-diagonal 0.0229), with right-person 0.844 and overlap recall 0.605. The better delay-and-sum baseline was 0.522, requiring 0.622, so it misses by 0.017. The 5- and 4-channel runs also have 4/4 envelope rows but fail right-person (0.658, 0.638) and overlap (0.396, 0.392).
- **635 s:** every subset scores 0.750 correct-voice and fails the quality gate. Right-person is 0.680, 0.584 and 0.434 for 8, 5 and 4 channels; overlap recall is 0.437, 0.418 and 0.478, against the raw baseline 0.486. Speaker C uses the fixed motion fallback at 0.56507652. Automatic and corrected mappings are identical with **0 taps**.
- **Decision:** **NO-GO on both windows.** Round 5 created no array demo. The subsequent Parallel work now packages `demo/ami_meeting_array` as a separately labelled experiment without reversing that quality decision; the default Lite demo/tagline is unchanged. There is no claim that Earshot runs on glasses. Full values, matrices, baseline scores, WER and timings are in `bench/RESULTS.md`, `review/array_745_summary.json`, and `review/array_635_summary.json`.
- **Sentence bubbles:** punctuation-aware chunks of at most 12 words have timing estimated from text length, visibly marked as estimated. Original caption and citation IDs are preserved, including translated segments. The real browser showed `estimated timing` and the exact motion marker at 7.28–8.08 s.
- **Lite motion markers:** “was also talking” is explicitly a motion estimate, not verified speech. Precision/recall is **0.0987/0.1888 on 745 s** and **0.0695/0.1181 on 635 s**, using fixed 0.5 s smoothing, `max(0.1, median + 3×MAD)` and 0.5 s minimum events. Weak results are disclosed.
- **SAM Audio conclusion:** it removes noise from speech in our sanity setup (+16.8751 dB), but no face or time-span prompt isolated a speaker from the others, on far-field or clean-mic audio. SAM Audio work is closed, and the optional noise-cleaning experiment was not run.
- **Verification:** main suite **94 passed**; final fresh clone/base install **93 passed, 1 optional Torch-dependent skipped**. `review/clean_clone_review5.log` has the result.
- **Spend:** **$4.115609 of $20.00**, including the preserved unintended $0.375 tracking run and all six array evaluations. `review/SPEND.md` has per-call accounting.

## Claude review round 4 — final SAM Audio checks

- **Integration sanity passed:** clean reference plus 0 dB white noise improved SI-SDR by **16.8751 dB** (mixture -0.0214 dB, target 16.8538 dB). Target RMS was 0.00701538 and residual RMS 0.00665512. Input and output were both 480,000 samples; the input, batch and processor rates were all 48,000 Hz. The initial harness device-placement error was fixed; production already moved batches correctly.
- All three variants on **clean mixed-down mic (AMI Mix-Headset)** scored **0.25 correct-voice rate**. Visual `keep` diagonal/off-diagonal means were 0.3232/0.3133; text-only spans were 0.3114/0.3096; video-plus-spans were 0.3102/0.3113. Only C's own row was correct in each matrix. All 12 stems and the mixture are in `review/ab_listen_cleanmic/`.
- On clean mixed-down mic (AMI Mix-Headset), separation call wall times were **83.535 s visual-only**, **31.539 s text-only spans**, and **370.815 s video-plus-spans**. No variant reached 3/4 correct rows.
- **No full 745 s or 635 s run, three-repeat clean-mic bench, or `demo/ami_meeting_cleanmic` was created.** The existing demo, tagline and production separator are unchanged. Separation work ends after this round.
- Main suite: **78 passed**. Fresh clone/base install: **77 passed, 1 optional Torch-dependent skipped**. See `review/clean_clone_review4.log`.
- New hosted spend was **$0.003752** for the clean-mic baseline transcription; all A/B separation was local with hosted endpoints disabled. Total estimated spend remains under the cap at **$3.290369 of $20.00**. See `GATE_REVIEW4.md` and `bench/RESULTS.md`.

## Claude review round 3 — span prompting negative result

- Ran the bounded local experiment with runtime-Lite mappings, other-label-subtracted solo spans, balanced enrollment, and explicit positive/negative anchors. `spans-text` used no video; `spans-video` added `keep` video at matching enrollment times. Mode and complete anchor plans were included in cache keys and tested.
- Both four-person A/B variants scored **0.25 correct-voice rate**, the same as round-2 visual-only `keep` on this window. Spans-text diagonal/off-diagonal means were 0.4141/0.4115; spans-video were 0.3757/0.3719. Only C's own row was correct in each matrix.
- Separation call wall time was **36.290 s for text** and **225.084 s for video**. All eight WAVs are committed in `review/ab_listen_spans/`.
- **No variant reached 3/4 correct rows. No full 745 s or 635 s runs, oracle benches, or new hosted transcription calls were made. New API spend is $0.** No oracle-mapped product result is claimed.
- Demo, tagline and production separator behavior are unchanged. The negative result and exact matrices are in `bench/RESULTS.md` and `GATE_REVIEW3.md`.
- Main suite: **76 passed**. Fresh clone/base install: **75 passed, 1 optional Torch-dependent skipped**, with no credentials or model downloads. See `review/clean_clone_review3.log`.

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
