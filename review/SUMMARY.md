# Earshot running summary

Final update after the full SAM Audio go/no-go on 2026-11-02. Evidence: `GATE_T1.md`, `GATE_T3.md`, `GATE_T4.md`, `GATE_T6.md`, `GATE_T12.md`, and `CONDITIONING.md`. **Engineering implementation and freeze verification are complete. No remote push has been performed.**

## Done

- **T0:** bundle unpacked at `~/src/earshot`; original history confirmed at 8 commits; baseline `pytest -q` reached 26 passed after installing the existing optional `torch` extra in the venv.
- **T2:** deterministic AMI builder implemented and committed. Real ES2008a 75 s grid, both audio mixtures, four references, taps, attribution, frame, and sync log generated. Re-run truth bytes are identical. Official annotations produce 234 words under the specified filter, 53 overlapping; all four taps were visually checked on `frame0.png`.
- **T1:** real SAM 3.1, Voice Transcribe, and Spark smoke passed. All four people have masks on 252/252 frames, Voice returned two turns, Spark returned valid threads and two verified catch-up sentences. Replay returned 4/4 cache hits with no network fallback.
- **T3:** real precomputed and local-T5 spikes matched at 80.776 dB, so precomputed remains the default. All four stems were produced on MPS, but SAM Audio failed speed and quality: 41.6 minutes, right-person 0.464, overlap recall 0.117, SI-SDR gain -2.415 dB. **NO-GO; Lite remains the demo.**
- **T4:** three real Voice repeats scored against exact word-level truth; README and `bench/RESULTS.md` contain matching measured values for Lite, single-stream, and SAM Audio. Exact assignment and a compression-noise floor fixed the Lite implementation. Final negative control: 0 captions for the empty tap.
- **T5:** pointer and keyboard tap-to-start, real background analysis with plain progress, and bounded replay snapping all passed in the browser, including a real 10 s live run.
- **T6:** real AMI demo committed. A fresh clone rendered it with no API key and an unreachable Meta URL; HTTP viewer/range/catch-up checks passed.
- **T7:** real cached Spanish for all 10 captions, strict ID/label validation, visible untranslated fallback, and original-on-hover/focus all passed in the browser.
- **T8/T9:** offline VTT/SRT export and downloads implemented. Native browser `<track>` showed a coloured, positioned short cue; stem download was fixture-verified. Lite correctly reports no isolated audio.
- **T10:** real local Muse Glimmer ran three cited catch-ups with local provenance and viewer label “On this computer.” Verifier fixed caption-ID numeric handling; replay was all cache hits.
- **T11:** README includes a real demo screenshot, exact results, models/locations, organizer ruling, Lite limitations, replay/setup/export commands, responsible use, and attribution.
- **T12:** **55 tests passed after SAM Audio compatibility work**; base editable install succeeded in a clean venv; final clean-clone replay, exports, banned-runtime scan, and history secret scan passed. Final demo size is **42.65 MB**.

See `ami_lite_bench_repeat3_optimized.log`, `ami_samaudio_bench_repeat3.log`, `glimmer_analyze.log`, and `SPEND.md` for real outputs and usage.

## Blocked / not submission-ready

- **T3 / SAM Audio:** **evaluated NO-GO**, not blocked by credentials. All four stems exist, but separation took 41.6 minutes and failed every quality threshold. The failed run is not the demo. Listening spot-check remains unverified and is not claimed.
- **Public repository:** does not exist yet because this run was explicitly local-only.
- **VLC:** not installed, so VLC colour playback is unverified. A long 22-second VTT cue also rendered poorly in the browser; the README records this limitation.
- **Video and submission:** owner must record/check the ≤2:59 video, publish the repo, complete/read back the form, and link the X post.

## Exact owner actions needed, in order

1. Keep Lite as the main mode and demo. Do not wait for SAM Audio approval—it is already working. Only revisit SAM Audio if you want to fund optimization; its measured full-clip speed and quality failed.
2. Review and push all local history and the demo to a new public GitHub repository.
3. Check VTT in VLC, including a long cue; adjust player-specific layout if needed.
4. Record the real ≤2:59 video with the opening new-work disclosure and AMI credit. Do not claim live processing, SAM Audio separation, or simultaneous-caption recovery from this Lite demo. Explain local Glimmer if using it for the open-weight bonus. Preserve the organizer's T5 ruling quoted in README: https://discord.com/channels/1557169028080869426/1564043204725182484/threads/1566631376868876419 — and if SAM Audio appears, include the on-screen line "SAM Audio includes a frozen Google T5-base text encoder (open source). Allowed by the organizers; disclosed in the README."
5. Check the video logged out, read back every submission field, and link the exact X post.

## Current benchmark

Mean [min, max] over 3 real Voice repeats; exact values are in `bench/RESULTS.md` and README.

| Mode | WER ↓ | Right person ↑ | Overlap-word recall ↑ | SI-SDR gain ↑ |
|---|---:|---:|---:|---:|
| Single-stream captions (oracle-mapped) | 0.231 [0.221, 0.237] | 0.919 [0.918, 0.921] | 0.495 [0.444, 0.540] | — |
| Earshot-Lite | 0.702 [0.691, 0.714] | 0.540 [0.537, 0.545] | 0.387 [0.369, 0.415] | — |
| Earshot (SAM Audio) | 0.916 [0.896, 0.935] | 0.464 [0.385, 0.555] | 0.117 [0.097, 0.146] | -2.415 [-2.415, -2.415] |

Lite underperforms the generous oracle-mapped baseline and must not be presented as a measured separation success. SAM Audio is worse on speed and quality and is also a no-go. Negative control: **0 empty-tap captions**. T2 sync heuristic remains inconclusive for C/D due weak correlations; no timeline correction was made.

## Estimated spend

**$1.561797 of $20.00.** See `SPEND.md` for per-call usage and arithmetic. Replay and local Glimmer added no hosted spend after the accepted Spanish call.

## Next

T12 and the SAM Audio go/no-go are complete. Only the owner/external actions above remain. Resume implementation only for requested optimization or review changes.
