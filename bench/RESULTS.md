# Dinner Table Bench — AMI ES2008a results

Date: 2026-11-02. Hardware: Apple M5 Max, arm64. Source: public AMI Meeting Corpus ES2008a, 745.0–820.0 s, far-field `Array1-01`, four speakers, 234 manually timed words (53 overlapping). All numbers below come from `python -m earshot bench` on real cached runs.

Models: `sam-3.1` for person masks; `muse-voice-transcribe-1.0` for single-stream DIARIZATION and repeat transcription; `muse-spark-1.3` for the viewer's threads/catch-ups. Lite attribution is deterministic mouth motion, not another model.

## Results

Values are **mean [min, max] over 3 real Voice transcription repeats**. Repeats reuse the same SAM masks and vary only Voice with repeat-specific cache keys. WER and right-person are macro means over the four people; overlap recall is the macro mean of per-person recall against exact word-level overlap intervals.

| Mode | WER ↓ | Right person ↑ | Overlap-word recall ↑ | SI-SDR gain (dB) ↑ |
|---|---:|---:|---:|---:|
| Single-stream captions (oracle-mapped) | 0.231 [0.221, 0.237] | 0.919 [0.918, 0.921] | 0.495 [0.444, 0.540] | — |
| Earshot-Lite (optimal mouth-motion attribution) | 0.702 [0.691, 0.714] | 0.540 [0.537, 0.545] | 0.387 [0.369, 0.415] | — |
| Earshot (SAM Audio) | blocked by gated-weight approval | blocked | blocked | blocked |

The single-stream baseline is **oracle-mapped**: each anonymous Voice speaker is assigned to the real person whose truth it matches best. This is generous to the baseline and is not available to Earshot-Lite at runtime. The baseline and Lite use identical Voice responses within each repeat.

Lite does not separate audio and cannot recover words that the single-stream Voice response omits. Its measured right-person attribution and overlap recall are worse than the oracle-mapped baseline on this clip. The initial greedy assignment implementation also had a deterministic assignment bug; commit `82c0eee` replaced it with exact small-group assignment, and `607bfdd` added a compression-noise floor for static regions. The table uses the corrected code and was regenerated with `EARSHOT_REPLAY=1` from the same three cached Voice responses, adding no API spend.

SAM Audio was not run because Hugging Face returned `Access denied ... requires approval`. No claim is made that SAM Audio failed or succeeded on far-field audio, and no SAM Audio metric is inferred.

## Commands

```bash
python -m earshot analyze bench/ami_ES2008a/clip.mp4 \
  --tap "Speaker A@0.25,0.29" --tap "Speaker B@0.80,0.36" \
  --tap "Speaker C@0.31,0.78" --tap "Speaker D@0.71,0.78" \
  --out runs/ami_lite --separator lite

python -m earshot bench runs/ami_lite \
  --truth bench/ami_ES2008a/truth.json --repeat 3 \
  --out runs/ami_lite/bench_repeat3.json

EARSHOT_REPLAY=1 python -m earshot bench runs/ami_lite \
  --truth bench/ami_ES2008a/truth.json --repeat 3 \
  --out runs/ami_lite/bench_repeat3.json
```

Full scorer output and machine-readable per-person/per-repeat values are in `review/ami_lite_bench_repeat3_optimized.log` and `runs/ami_lite/bench_repeat3.json` in the working run folder.

## Negative control

The fifth tap is `Negative Control@0.12,0.70`, on the empty door area of Closeup3. The analysis command is:

```bash
python -m earshot analyze bench/ami_ES2008a/clip.mp4 \
  --tap "Speaker A@0.25,0.29" --tap "Speaker B@0.80,0.36" \
  --tap "Speaker C@0.31,0.78" --tap "Speaker D@0.71,0.78" \
  --tap "Negative Control@0.12,0.70" \
  --out runs/ami_negative --separator lite --no-spark
```

**Final result: 0 captions for Negative Control**, out of 11 captions assigned to the four real people. SAM returned a mask for the empty region on all 1,875 frames (mean area 0.053931 of the frame), so this checks attribution rather than mask presence.

The first implementation amplified the empty region's 0.0045-gray-level median compression motion and incorrectly gave it 4 captions. Commit `607bfdd` added a 0.1-gray-level normalization floor and a regression test. The final run used `EARSHOT_REPLAY=1`, reused the real masks and Voice response, and produced zero negative-control captions without new API spend.
