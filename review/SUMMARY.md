# Earshot running summary

Updated after GATE_T1 on 2026-11-02.

## Done

- **T0:** bundle unpacked at `~/src/earshot`; original history confirmed at 8 commits; baseline `pytest -q` reached 26 passed after installing the existing optional `torch` extra in the venv.
- **T2:** deterministic AMI builder implemented and committed. Real ES2008a 75 s grid, both audio mixtures, four references, taps, attribution, frame, and sync log generated. Re-run truth bytes are identical. Official annotations produce 234 words under the specified filter, 53 overlapping; all four taps were visually checked on `frame0.png`.
- **T1:** real SAM 3.1, Voice Transcribe, and Spark smoke passed. All four people have masks on 252/252 frames, Voice returned two turns, Spark returned valid threads and two verified catch-up sentences. Replay returned 4/4 cache hits with no network fallback.
- Current deterministic suite: **29 passed**. No remote push has been performed.

See `GATE_T1.md`, `live_smoke_run1.log`, and `live_smoke_run2.log` for evidence.

## Blocked

- **T3 / SAM Audio:** `hf auth whoami` succeeds as `hiddingpickles`, but downloading `facebook/sam-audio-small-tv` returns `Access denied. Model ... requires approval.` T3 cannot run until the owner receives gated-model approval. The Lite path will proceed.
- The public GitHub repository required by T0 does not yet exist because this run is explicitly local-only.

## Exact owner actions needed, in order

1. In Hugging Face, obtain approval for `facebook/sam-audio-small-tv` for `hiddingpickles`; then rerun T3 with the existing precomputed text features. No token is needed in the report.
2. After reviewing the local history, push it to a new public GitHub repository with all commits included.
3. Before submission, retain the organizer's 2 Nov 06:06 Discord ruling in the README/demo: SAM Audio counts as a Meta model and its internal T5 is allowed with disclosure. The implementation nevertheless keeps the runbook's stricter precomputed-features/no-T5 path. Thread: https://discord.com/channels/1557169028080869426/1564043204725182484/threads/1566631376868876419

## Current benchmark

T4 has not run; there are no benchmark metrics yet.

| Mode | WER ↓ | Right person ↑ | Overlap-word recall ↑ | SI-SDR gain ↑ |
|---|---:|---:|---:|---:|
| Single-stream captions (oracle-mapped) | pending | pending | pending | — |
| Earshot-Lite | pending | pending | pending | — |
| Earshot (SAM Audio) | blocked by model approval | blocked by model approval | blocked by model approval | blocked by model approval |

T2 sync heuristic warning: C +0.480 s and D +0.560 s, with weak correlations 0.167 and 0.163. No timeline correction was made because the estimator is inconclusive and AMI signals share one timeline.

## Estimated spend

**$0.055881 of $20.00.** See `SPEND.md` for per-call usage and arithmetic. Replay added $0.

## Next

Write the T3 blocked gate, implement word-level truth and repeat support, then run the three-repeat single-stream/Lite benchmark on the real AMI clip. Keep SAM Audio rows blocked unless model approval arrives.
