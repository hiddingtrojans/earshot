# GATE T4 — real AMI single-stream and Lite benchmark

Date: 2026-11-02. Device: Apple M5 Max, arm64. All metrics come from real `python -m earshot bench` calls on public AMI ES2008a.

## Commits

- `d8d26c2` Add word-level truth and cached benchmark repeats
- `7621c56` Calculate API spend from cached usage
- `82c0eee` Optimize Lite speaker-to-face assignment
- `090d1e8` Reuse saved tracks for identical run taps
- `607bfdd` Suppress static-region motion in Lite attribution
- `b5e0ca1` Add real AMI Lite benchmark results

## Commands and real output

```bash
.venv/bin/pytest -q
# 37 passed in 4.63s
```

Main analysis:

```bash
zsh -ic 'caffeinate -i .venv/bin/python -m earshot analyze bench/ami_ES2008a/clip.mp4 --tap "Speaker A@0.25,0.29" --tap "Speaker B@0.80,0.36" --tap "Speaker C@0.31,0.78" --tap "Speaker D@0.71,0.78" --out runs/ami_lite --separator lite'
# wrote runs/ami_lite/earshot.json
# wall time: 969.944 s (including pure-Python SAM mask decoding and Spark catch-ups)
```

SAM processed 1,875 frames in 304,539 ms, request `resp_6ae8961a3a63bfff59064d73`. Every person has a mask on 1,875/1,875 frames. Frame-0 boxes: A `(100,121,279,288)`, B `(504,165,635,288)`, C `(137,410,312,576)`, D `(379,403,603,576)`.

Three repeats:

```bash
zsh -ic 'caffeinate -i .venv/bin/python -m earshot bench runs/ami_lite --truth bench/ami_ES2008a/truth.json --repeat 3 --out runs/ami_lite/bench_repeat3.json'
```

| Repeat | Voice request/session ID | Latency | Audio |
|---|---|---:|---:|
| 0 | `voyager/transcribe/D38DE279F31C4D3F95DC1321C6A5D26C` | 15,924 ms | 75.0 s sent; server duration used for spend |
| 1 | `voyager/transcribe/4A8ADEE3136140F299A75EB04A92E5AE` | 15,211 ms | 75.0 s sent |
| 2 | `voyager/transcribe/EE13F677B0B3462DB2845AB3FA3FDCA2` | 16,210 ms | 75.0 s sent |

Final replay after exact assignment and static-noise fixes:

```bash
zsh -ic 'EARSHOT_REPLAY=1 caffeinate -i .venv/bin/python -m earshot bench runs/ami_lite --truth bench/ami_ES2008a/truth.json --repeat 3 --out runs/ami_lite/bench_repeat3.json'
#                                Earshot         Single stream
# Word error rate      0.702 [0.691, 0.714]       0.231 [0.221, 0.237]
# Right person         0.540 [0.537, 0.545]       0.919 [0.918, 0.921]
# Overlap words        0.387 [0.369, 0.415]       0.495 [0.444, 0.540]
# wrote runs/ami_lite/bench_repeat3.json
```

The final replay used cached Voice for all three repeats. No SAM call is made by the repeat scorer. Full console output is in `ami_lite_bench_repeat3_optimized.log`; machine-readable per-person values are in the ignored run folder's `bench_repeat3.json`.

Negative control:

```bash
zsh -ic 'caffeinate -i .venv/bin/python -m earshot analyze bench/ami_ES2008a/clip.mp4 --tap "Speaker A@0.25,0.29" --tap "Speaker B@0.80,0.36" --tap "Speaker C@0.31,0.78" --tap "Speaker D@0.71,0.78" --tap "Negative Control@0.12,0.70" --out runs/ami_negative --separator lite --no-spark'
# wall time: 1,188.398 s
# SAM: 1,875 frames, 399,855 ms, resp_6ae896e4d53fa9036cbc49cf
# Voice: 16,016 ms, voyager/transcribe/D2297074DFEB438F9083825CC814D246
```

The empty mask exists on all 1,875 frames. Initially it received 4 captions because its 0.0045-gray-level median motion was normalized into a large score. After the 0.1-gray-level floor in `607bfdd`, replay produced:

```text
captions_by_person: Speaker D=2, Speaker C=2, Speaker A=4, Speaker B=3
negative_captions: []
```

This is a final pass: **0 negative-control captions out of 11 total**. See `bench/RESULTS.md` for the recorded failure and fix.

## Done when

- ✓ Word-level truth uses exact `<w>` intervals and intersecting another person's word defines overlap; turn-based truth remains supported. Tests cover boundaries, punctuation, exact overlap, and deterministic bytes.
- ✓ `--repeat N` adds the repeat index to Voice `key_parts`; N=3 real calls have independent cache entries and IDs. Mean [min, max] is reported.
- ✓ Single-stream and Lite ran 3× on the same far-field mixture. SAM Audio rows remain explicitly blocked because T3 did not run; optional clean-mic condition was not run.
- ✓ `bench/RESULTS.md` exists with real values, spread, commands, date, model IDs, and hardware. README's table is copied exactly from it.
- ✓ Baseline is labelled oracle-mapped and generous.
- ✓ Final negative control produces zero captions.
- ✓ No SAM Audio/SI-SDR number appears without a real SAM Audio run.

## Review checklist self-check

- ✓ `pytest -q` green (37 tests); deterministic parsing, assignment, noise-floor, cache-key, aggregation, spend, and same-run reuse paths have tests.
- ✓ Small commits; no push and no secrets. Every hosted call uses `CallLog.cached` and only public AMI media is used.
- ✓ No new runtime model or project dependency. Spend tooling fails closed on unknown hosted models.
- ✓ README numbers match `RESULTS.md`; final negative control is reported rather than hidden.
- ✓ Corrected viewer regenerated from cached tracks/Voice; its 50 catch-up sentences all have `verified` status.

## Open problems and owner actions

1. Lite remains worse than the generous baseline: right-person 0.540 vs 0.919 and overlap recall 0.387 vs 0.495. It does not separate speech. Do not present it as recovering SAM Audio-quality overlap.
2. Owner must obtain SAM Audio weight approval before separation and the T3 go/no-go can be evaluated.
3. Full-clip mask decoding is slow pure-Python work. Same-run track reuse avoids repeating it, but a fresh 75 s analysis is not instant and must not be marketed as live/real-time.
4. T2 sync heuristic remains inconclusive for C/D due weak correlations; no timeline shift was invented.

Spend across T1 smoke, full Lite, optimized Spark regeneration, three repeats, and negative control: **$0.906028 of $20.00**, generated from real call logs in `SPEND.md`. Replay checks added $0.

## Addendum — SAM Audio rows measured after approval

All four real SAM Audio stems were produced and scored with three Voice repeats. `bench/RESULTS.md` and README now include this real row:

| Mode | WER ↓ | Right person ↑ | Overlap recall ↑ | SI-SDR gain (dB) ↑ |
|---|---:|---:|---:|---:|
| Earshot (SAM Audio) | 0.916 [0.896, 0.935] | 0.464 [0.385, 0.555] | 0.117 [0.097, 0.146] | -2.415 [-2.415, -2.415] |

The go/no-go failed on every threshold: 41.6 minutes of separation, right-person below 0.8, overlap recall below baseline +10 points, and negative SI-SDR gain. Per-person first-repeat gains were A +1.28 dB, B -7.35 dB, C -3.15 dB, D -0.44 dB. Lite remains the main mode and demo. See `ami_samaudio_bench_repeat3.log` for real scorer output and `GATE_T3.md` for the complete audit. Hosted spend including this evaluation is **$1.561797**.
