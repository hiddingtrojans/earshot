# Earshot running summary

Updated after GATE_T4 on 2026-11-02. Evidence: `GATE_T1.md`, `GATE_T3.md`, and `GATE_T4.md`.

## Done

- **T0:** bundle unpacked at `~/src/earshot`; original history confirmed at 8 commits; baseline `pytest -q` reached 26 passed after installing the existing optional `torch` extra in the venv.
- **T2:** deterministic AMI builder implemented and committed. Real ES2008a 75 s grid, both audio mixtures, four references, taps, attribution, frame, and sync log generated. Re-run truth bytes are identical. Official annotations produce 234 words under the specified filter, 53 overlapping; all four taps were visually checked on `frame0.png`.
- **T1:** real SAM 3.1, Voice Transcribe, and Spark smoke passed. All four people have masks on 252/252 frames, Voice returned two turns, Spark returned valid threads and two verified catch-up sentences. Replay returned 4/4 cache hits with no network fallback.
- **T4:** three real Voice repeats scored against exact word-level truth; README and `bench/RESULTS.md` contain matching measured values. Exact assignment and a compression-noise floor fixed the Lite implementation. Final negative control: 0 captions for the empty tap. Current suite: **37 passed**. No remote push has been performed.

See `ami_lite_bench_repeat3_optimized.log` for the final scorer output and `SPEND.md` for actual call usage.

## Blocked

- **T3 / SAM Audio:** `hf auth whoami` succeeds as `hiddingpickles`, but downloading `facebook/sam-audio-small-tv` returns `Access denied. Model ... requires approval.` T3 cannot run until the owner receives gated-model approval. The Lite path will proceed.
- The public GitHub repository required by T0 does not yet exist because this run is explicitly local-only.

## Exact owner actions needed, in order

1. In Hugging Face, obtain approval for `facebook/sam-audio-small-tv` for `hiddingpickles`; then rerun T3 with the existing precomputed text features. No token is needed in the report.
2. After reviewing the local history, push it to a new public GitHub repository with all commits included.
3. Before submission, retain the organizer's 2 Nov 06:06 Discord ruling in the README/demo: SAM Audio counts as a Meta model and its internal T5 is allowed with disclosure. The implementation nevertheless keeps the runbook's stricter precomputed-features/no-T5 path. Thread: https://discord.com/channels/1557169028080869426/1564043204725182484/threads/1566631376868876419

## Current benchmark

Mean [min, max] over 3 real Voice repeats; exact values are in `bench/RESULTS.md` and README.

| Mode | WER ↓ | Right person ↑ | Overlap-word recall ↑ | SI-SDR gain ↑ |
|---|---:|---:|---:|---:|
| Single-stream captions (oracle-mapped) | 0.231 [0.221, 0.237] | 0.919 [0.918, 0.921] | 0.495 [0.444, 0.540] | — |
| Earshot-Lite | 0.702 [0.691, 0.714] | 0.540 [0.537, 0.545] | 0.387 [0.369, 0.415] | — |
| Earshot (SAM Audio) | blocked by model approval | blocked | blocked | blocked |

Lite underperforms the generous oracle-mapped baseline and must not be presented as a measured separation success. Negative control: **0 empty-tap captions**. T2 sync heuristic remains inconclusive for C/D due weak correlations; no timeline correction was made.

## Estimated spend

**$0.906028 of $20.00.** See `SPEND.md` for per-call usage and arithmetic. Replay checks added $0.

## Next

T4 gate is committed (`a190c18`). Build T5 tap-to-start with live background analysis and documented instant cached replay; then produce the T6 demo folder. Keep SAM Audio rows blocked unless model approval arrives.
