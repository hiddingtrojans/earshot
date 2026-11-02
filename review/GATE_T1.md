# GATE T1 — live hosted-model smoke

Date: 2026-11-02. Device: Apple M5 Max, arm64; Python 3.12.13; FFmpeg 9.0.2.

## Commits

- `f1dabef` Add live smoke harness and response provenance
- `d38ae79` Record Voice session identifiers in call provenance
- T2 input dependency: `38e2c19`, `2984738`, `17eab2a`, `553e928`

## Commands and real output

Baseline and final deterministic checks:

```bash
.venv/bin/pytest -q
# .............................                                            [100%]
# 29 passed in 3.53s
```

The original T0 environment needed the already-declared optional `torch` package to unskip its shape test; after installing it in `.venv`, T0 showed `26 passed in 5.61s`. No project dependency was added.

AMI input:

```bash
caffeinate -i .venv/bin/python tools/make_ami_clip.py --out bench/ami_ES2008a
# Wrote 234 truth words to bench/ami_ES2008a/truth.json
# clip.mp4: 75.000000 s, 704x576, 25 fps, H.264, mono 48 kHz AAC
```

A full cached rerun produced byte-identical truth, SHA-256 `f46b45885eb0983827a624615e3ec70f60439393be3e9aacba1d5fafdec5b39a`. The midpoint rule in the pack yields 234 words, 53 overlapping; the pack's prose said 233, so the prose is inaccurate. `frame0.png` was inspected: A–D taps land on the correct faces in grid order Closeup4, Closeup2, Closeup3, Closeup1.

Live invocation (the key was available only through the interactive zsh; its value was never printed):

```bash
zsh -ic 'set -o pipefail; caffeinate -i .venv/bin/python tools/live_smoke.py bench/ami_ES2008a/clip.mp4 --tap "Speaker A@0.25,0.29" --tap "Speaker B@0.80,0.36" --tap "Speaker C@0.31,0.78" --tap "Speaker D@0.71,0.78" --out runs/live_smoke 2>&1 | tee review/live_smoke_run1.log'
```

Real output:

```text
Speaker A: coverage=252/252; mean mask area=0.0402
Speaker B: coverage=252/252; mean mask area=0.0200
Speaker C: coverage=252/252; mean mask area=0.0329
Speaker D: coverage=252/252; mean mask area=0.0544
Voice turns: 2 turns, 0.00–7.02 s and 7.02–9.58 s
Spark threads: [{"thread": 1, "topic": "programmed buttons layout"}]
Spark catch-up: 2 sentences, both status="verified"
```

Full transcript and JSON are in `live_smoke_run1.log` and `runs/live_smoke/smoke.json`. Relevant provenance from `runs/live_smoke/calls.jsonl`:

| Model | Cache | Latency | Request/session ID | Usage |
|---|---|---:|---|---|
| `sam-3.1` | miss | 49,071 ms | `resp_6ae8925d591514e600ce4f87` | 252 video frames |
| `muse-voice-transcribe-1.0` | miss | 5,630 ms | `voyager/transcribe/77CE4D092D29489CA620B1C50308BE1A` | 10.08 s server audio duration |
| `muse-spark-1.3` threads | miss | 3,656 ms | `resp_6ae892de0cd72a0a4b824a69` | 267 input, 439 output tokens |
| `muse-spark-1.3` catch-up | miss | 3,074 ms | `resp_6ae892e211cabaff792244d2` | 226 input, 587 output tokens |

Voice returned `sessionId`, not a Responses-style `id` or standard request header. The cached response supplied the real session ID above; `response_metadata` now recognizes that field. `../docs/02_ARCHITECTURE.md` was updated with this live shape.

Replay invocation:

```bash
zsh -ic 'set -o pipefail; EARSHOT_REPLAY=1 caffeinate -i .venv/bin/python tools/live_smoke.py bench/ami_ES2008a/clip.mp4 --tap "Speaker A@0.25,0.29" --tap "Speaker B@0.80,0.36" --tap "Speaker C@0.31,0.78" --tap "Speaker D@0.71,0.78" --out runs/live_smoke 2>&1 | tee review/live_smoke_run2.log'
```

Its final `Calls this run` line contains exactly four entries: SAM, Voice, Spark threads, Spark catch-up. Every entry has `"cache": "hit"` and the corresponding real request/session ID. No upload was needed because the outer SAM response was cached. Replay produced identical tracking, turns, threads, and verified catch-up.

## Done when

- ✓ Every person tracked on at least 90% of visible frames: 252/252 for each of A–D; all four are visible throughout this 10.08 s grid clip.
- ✓ Transcript has turns: two real DIARIZATION turns.
- ✓ Spark returns schema-valid JSON: one thread and two verified catch-up sentences.
- ✓ All model calls appear in `calls.jsonl` with real IDs; Voice uses its returned session ID.
- ✓ Second run is 100% cache hits (4/4), with `EARSHOT_REPLAY=1` preventing network fallback.

## Review checklist self-check

- ✓ `pytest -q` green; deterministic metadata and AMI parsing/lag code have tests.
- ✓ Small descriptive local commits; no push performed.
- ✓ `git log -p | grep -iE 'api[_-]?key|bearer '` showed only environment names, code placeholders, and `Bearer {api_key()}`; no secret value.
- ✓ No new project dependency and no non-Meta runtime model introduced.
- ✓ Every hosted model call goes through `CallLog.cached` with model, purpose, and hosted location.
- ✓ Only public AMI ES2008a media was used; speaker labels are Speaker A–D.
- ✓ SAM usage and Voice/Spark IDs are attached above; the API response-shape note is updated.

## Open problems and owner actions

1. Hugging Face authentication now succeeds, but `facebook/sam-audio-small-tv` still returns `Access denied ... requires approval`. Owner must obtain model approval before T3 can run.
2. Owner must push the local history to a new public GitHub repository after review; T0's public-repo criterion remains open.
3. T2's motion/energy sync estimator reported A −0.200 s (r=0.303), B −0.080 s (r=0.122), C +0.480 s (r=0.167), D +0.560 s (r=0.163). C/D exceed the warning threshold but correlations are weak; AMI sources share one timeline, so no unsupported shift was applied. Treat this heuristic as inconclusive, not measured clock drift.

Estimated spend through this gate: **$0.055881**, detailed in `SPEND.md`.
