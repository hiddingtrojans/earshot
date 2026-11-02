# GATE — Claude review round 2

Date: 2026-11-02. Local commits only; no push.

**Owner listening task first:** listen to all eight `review/ab_listen/{A,B,C,D}_{keep,remove}.wav` files and compare them with `review/ab_listen/mixture.wav`. The agent computed metrics but did not listen to the stems and does not claim a listening check.

## Commits

- `6bd2eda` Add keep and remove visual mask modes
- `7e08673` Add far-field voice-envelope correlation metric
- `5ce1ec6` Fix batched mask digest syntax
- `67f92db` Add low-confidence tap corrections and A/B evidence
- `440d6ea` Add correct-voice rate and A/B matrices
- `b51802e` Allow explicit CPU fallback for SAM Audio
- `3c47dff` Include tap corrections in replay demo packages
- `d57712e` Report taps needed for oracle mappings
- `42f48eb` Preserve correction history during replay
- `148a8f8` Adopt keep mask semantics consistently
- `dc4bb3b` Gate envelope correlation by mixture activity
- `404f443` Avoid batched MPS separation stalls
- `0123b29` Log separation window timings
- `05a7ece` Resume interrupted runs from saved tracks
- `b22be6c` Fix correction controls and replay rendering
- `75411c9` Use cached local Glimmer in replay demo
- `a9e10c6` Make correct-voice rate the headline audio metric
- `5bc181b` Test correct-voice bench output
- `8c5b22e` Document cached Glimmer demo
- `e6df939` Record primary quality no-go and Lite tagline
- `4673114` Use run-specific SI-SDR caveat
- `88294db` Record held-out SAM Audio results and spend

## 1. Visual mask semantics and eight-output A/B

`processor.mask_videos` computes `v * m.eq(0)`. Earshot's `keep` mode inverts the target mask first, leaving only the tapped person visible. `remove` passes the target mask, blacking out that person. `keep` is the library, pipeline, CLI and spike default; `remove` remains selectable. The mode, people, masks, audio and conditioning parameters are all in the separation cache key. A unit test with frames of ones verifies that `keep` is nonzero only inside the target mask.

The A/B used the 0–10 s window, which has 14 overlapping truth words, the most of the nine separation windows. All eight calls used seed 0 and real SAM Audio on MPS. No output was selected by listening.

```bash
for mode in keep remove; do
  for spec in 'A 0 0 0.5 0.5' 'B 0.5 0 1 0.5' 'C 0 0.5 0.5 1' 'D 0.5 0.5 1 1'; do
    set -- $spec
    person=$1
    box="$2 $3 $4 $5"
    env HF_HUB_CACHE="$PWD/.hf-cache/hub" caffeinate -i \
      .venv/bin/python spike/earshot_spike.py run \
      --video bench/ami_ES2008a/clip.mp4 --box $box \
      --ref "bench/ami_ES2008a/ref_${person}.wav" --seconds 10 --seed 0 \
      --mask-mode "$mode" --out "spike/out/ab_${person}_${mode}"
  done
done
```

Envelope protocol: log energy in 50 ms frames, 25 ms hop, 200 ms smoothing, Pearson correlation on frames above the mixture's 20th-percentile log-energy noise floor. Rows are the intended speaker and columns are headset references A/B/C/D. This is implemented in `earshot/envelope.py`; the A/B matrices below are from `review/envelope_ab.json`, not estimated values.

**Keep:**

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| A | 0.3512 | -0.1337 | 0.9071 | 0.5337 |
| B | 0.3526 | -0.1328 | 0.9071 | 0.5341 |
| C | 0.3515 | -0.1322 | 0.9071 | 0.5343 |
| D | 0.3538 | -0.1328 | 0.9067 | 0.5334 |
| Mixture | 0.3927 | -0.1761 | 0.8535 | 0.4093 |

**Remove:**

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| A | 0.3528 | -0.1325 | 0.9069 | 0.5334 |
| B | 0.3520 | -0.1323 | 0.9070 | 0.5333 |
| C | 0.3525 | -0.1325 | 0.9070 | 0.5334 |
| D | 0.3512 | -0.1329 | 0.9070 | 0.5334 |
| Mixture | 0.3927 | -0.1761 | 0.8535 | 0.4093 |

| Mode | Correct-voice rate | Diagonal mean | Off-diagonal mean |
|---|---:|---:|---:|
| Keep | 0.25 | 0.4147 | 0.4152 |
| Remove | 0.25 | 0.4152 | 0.4149 |

Neither mode is diagonal-dominant. Each keep/remove waveform pair has Pearson correlation between 0.999955 and 0.999986. The mixture's best match is C; treating the same mixture as all four people's baseline gives a correct-voice rate of 0.25. **`keep` is retained for Meta's target-visible semantics, not claimed as an A/B winner.** Raw spike output is in `review/ab_spikes.log`; both modes report no forbidden imported modules.

## 2. Envelope metric replaces the SI-SDR headline

`python -m earshot bench` now prints correct-voice rate for stems and mixture. Its JSON retains per-person SI-SDR, gain, complete envelope rows, the mixture baseline and the gating rule. Correct-voice rate is the fraction of rows whose strongest headset correlation is the intended person. SI-SDR is no longer the headline because these are far-field mixtures compared with close-talk headsets. The 10 s A/B mixture/Speaker A comparison is -32.91 dB; the full-run values are -24.77 dB on 745 s and -51.11 dB on 635 s. The JSON note uses the measured value for each run rather than hard-coding the A/B value.

The old full `remove` stems were rescored without model calls for comparison, not confused with the new `keep` run: their correct-voice rate is **0.25**, with mixture **0.25**. Their matrix is in `runs/ami_samaudio/bench_envelope.json`.

A test verifies the exact frames selected by the mixture gate, plus positive self-correlation, silence handling and the diagonal-fraction calculation. An earlier activity-gate implementation was corrected and all matrices recomputed from saved WAVs; no additional separation or hosted calls were needed.

## 3. Separation execution and honest timings

Batching all four people in one processor/model call is implemented, with per-person fallback on exceptions. `gc.collect()` runs after every window and `torch.mps.empty_cache()` on MPS. Device selection is explicit with `--device auto|mps|cpu`. Per-window wall times are logged.

Real execution findings:

- Four-person MPS batching did not finish a window after more than 25 minutes. `review/separation_sample.txt` captured the Metal command-buffer wait and garbage-collection stack.
- The CPU four-person batch did not finish a window after more than 20 minutes. `review/separation_cpu_sample.txt` captured active model work. This incomplete trial is not a quality result.
- The full evaluation therefore uses **one person at a time on MPS**. The static loaded-model object graph is frozen before per-window collection. The real batching/fallback code remains available on other devices.
- A resume attempt spent about nine minutes reparsing cached SAM masks because an interrupted run lacked `earshot.json`. The new `tracks_request.json` sidecar records names and taps so the verified saved masks can be reused safely. This setup time is not presented as separation latency.

The completed primary separation used `per-person (MPS batch stall avoided)` and recorded no exceptions. The single cached call's wall time was **773.889 s (12 min 53.9 s)**, including model loading and preparation. Model-inference and logged per-window wall timings are:

| Person | Model inference (s) | Window wall time including processing/cleanup (s) |
|---|---:|---:|
| Speaker A | 161.775 | 165.1 |
| Speaker B | 179.909 | 183.2 |
| Speaker C | 200.073 | 203.5 |
| Speaker D | 193.504 | 196.1 |
| **Total** | **735.261** | **747.9** |

The 26.0 s difference between total call wall time and summed window time is one-time setup/loading and finalization. These are real timings, not a controlled speed comparison with the earlier 41.6-minute run, which used different separation code and mask behavior. **Speed is not a failure criterion.**

The full command is:

```bash
env HF_HUB_CACHE="$PWD/.hf-cache/hub" caffeinate -i \
  .venv/bin/python -u -m earshot analyze bench/ami_ES2008a/clip.mp4 \
  --tap "Speaker A@0.25,0.29" --tap "Speaker B@0.80,0.36" \
  --tap "Speaker C@0.31,0.78" --tap "Speaker D@0.71,0.78" \
  --out runs/ami_samaudio_keep --separator samaudio --device mps --no-spark
```

## 4. Full `keep` benchmark and quality-only decision

Three real Voice repeats scored the completed 745 s `keep` run. Values are mean [min, max].

| Mode | WER ↓ | Right person ↑ | Overlap-word recall ↑ | Correct voice ↑ |
|---|---:|---:|---:|---:|
| SAM Audio `keep` | 0.967 [0.749, 1.227] | 0.386 [0.301, 0.546] | 0.098 [0.037, 0.141] | 0.500 [0.500, 0.500] |
| Same-run single stream, oracle-mapped | 0.239 [0.231, 0.246] | 0.913 [0.906, 0.918] | 0.480 [0.463, 0.513] | 0.250 mixture |

**Decision: NO-GO on quality.** Right-person is below 0.80 in every repeat. Overlap recall must be at least 0.580 against the mean baseline +0.10, but is 0.098, a 0.382-point shortfall; every repeat fails its paired baseline comparison too. WER is reported as 0.967 and is not a pass/fail condition. SI-SDR gain remains in the JSON at -0.008 dB with the far-field note, not as a headline. The 773.889 s separation time is documented but **is not a reason for rejection**.

Full-run envelope matrix, identical across transcription repeats:

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| Speaker A | **0.2121** | 0.0995 | 0.0464 | 0.1532 |
| Speaker B | 0.1808 | **0.1884** | 0.0167 | 0.1316 |
| Speaker C | 0.2109 | 0.0998 | 0.0427 | **0.1573** |
| Speaker D | 0.1402 | **0.2091** | 0.0480 | 0.1349 |
| Mixture | **0.3887** | 0.0834 | 0.0950 | 0.2559 |

Bold cells are each row's strongest match. A and C select their own headsets; B and D do not, giving correct-voice rate 0.500. The mixture's strongest match is A, so the four-person mixture baseline rate is 0.250.

```bash
caffeinate -i .venv/bin/python -m earshot bench runs/ami_samaudio_keep \
  --truth bench/ami_ES2008a/truth.json --repeat 3 \
  --out runs/ami_samaudio_keep/bench_review2.json
```

The 635 s held-out analysis started before 23:00 Madrid with the same mask semantics and per-person MPS execution. It reuses verified masks and all four baseline Voice responses, but performs new isolated-voice transcriptions.

The 635 s analysis and three-repeat benchmark both completed before 23:00 Madrid. These are new results, not the earlier Lite numbers on the same window.

| Mode | WER ↓ | Right person ↑ | Overlap-word recall ↑ | Correct voice ↑ |
|---|---:|---:|---:|---:|
| SAM Audio `keep` (635 s) | 2.731 [1.097, 3.825] | 0.382 [0.296, 0.537] | 0.185 [0.158, 0.230] | 0.250 |
| Same-run single stream, oracle-mapped | 0.384 [0.377, 0.395] | 0.693 [0.689, 0.697] | 0.486 [0.424, 0.524] | 0.250 mixture |

**Held-out decision: NO-GO on quality too.** Right-person is below 0.80 in every repeat. Overlap recall is below the mean baseline +0.10 threshold of 0.586, and every paired repeat fails. SI-SDR gain is -5.19 dB; the measured mixture/Speaker A value is -51.11 dB. The JSON now derives this note from each run rather than using the 10 s A/B value.

| Stem \ headset | A | B | C | D |
|---|---:|---:|---:|---:|
| Speaker A | 0.4208 | 0.1495 | **0.4300** | -0.1635 |
| Speaker B | 0.3426 | 0.1441 | **0.5587** | 0.0420 |
| Speaker C | 0.3801 | 0.0880 | **0.5102** | 0.0059 |
| Speaker D | 0.3436 | 0.1410 | **0.5589** | 0.0439 |
| Mixture | 0.3413 | 0.1183 | **0.6501** | 0.1514 |

All four stems best match C; only C's own row is correct, giving 0.250 correct-voice rate. The full separation call took **772.703 s**:

| Person | Model inference (s) | Window wall time (s) |
|---|---:|---:|
| Speaker A | 158.669 | 161.5 |
| Speaker B | 188.832 | 191.9 |
| Speaker C | 178.132 | 180.7 |
| Speaker D | 210.156 | 213.1 |
| **Total** | **735.789** | **747.2** |

```bash
env HF_HUB_CACHE="$PWD/.hf-cache/hub" caffeinate -i \
  .venv/bin/python -u -m earshot analyze bench/ami_ES2008a_635/clip.mp4 \
  --tap "Speaker A@0.25,0.29" --tap "Speaker B@0.80,0.36" \
  --tap "Speaker C@0.31,0.78" --tap "Speaker D@0.71,0.78" \
  --out runs/ami_samaudio_keep_635 --separator samaudio --device mps --no-spark
caffeinate -i .venv/bin/python -m earshot bench runs/ami_samaudio_keep_635 \
  --truth bench/ami_ES2008a_635/truth.json --repeat 3 \
  --out runs/ami_samaudio_keep_635/bench_review2.json
```

Logs: `review/ami_samaudio_keep_635_analyze.log` and `review/ami_samaudio_keep_635_bench_review2.log`. Machine-readable scores: `runs/ami_samaudio_keep_635/bench_review2.json`. Replaying these scores after the run-specific SI-SDR note fix reproduced the same metrics without hosted calls.

The decision rule is fixed in advance: overlap-word recall must be at least single-stream +0.10 and right-person at least 0.80. WER is reported. Speed alone does not fail the run. A 635 s held-out run is conditional on finishing before 23:00 Madrid.

## 5. Lite protocol and one-tap corrections

The protocol statement is unchanged and explicit: the 60–90% band won on 635 s and scored 0.537 on 745 s, so it is rejected. The reviewer-fixed 30–60% mouth band, central 60% width, 0.5 s smoothing, z-scoring, Pearson correlation and Hungarian assignment were not selected using test-window results.

| Window | Lite WER | Right person | Overlap recall | Oracle right person |
|---|---:|---:|---:|---:|
| 635 s development | 2.571 [0.395, 3.719] | 0.547 [0.473, 0.693] | 0.553 [0.424, 0.624] | 0.693 [0.689, 0.697] |
| 745 s primary | 0.231 [0.221, 0.237] | 0.919 [0.918, 0.921] | 0.495 [0.444, 0.540] | 0.919 [0.918, 0.921] |

The confidence margin is best-minus-second-best correlation, threshold **0.15 fixed in advance**. Taps needed to reach the oracle mapping were **0 / 0 / 0 on 745 s** and **1 / 1 / 0 on 635 s**, in repeat order. The tuning JSON now contains every repeat's mapping, rather than incorrectly attaching one mapping to different metric results.

Corrections move captions/activity immediately, update only the confirmed diarized label, and save to `corrections.json`. Replay applies history without duplicating it or moving activity twice. A browser test on the public demo moved Speaker B's 0:07 caption to Speaker C, saved one correction, retained the other low-confidence prompt and did not duplicate threads. The temporary edit was restored afterward. Synthetic server tests cover a second correction and replay order.

## 6. Demo and provenance

SAM Audio failed the primary quality gate, so **the existing Lite demo is retained**. No SAM Audio stem or unsupported “Both talking” moment is presented as a successful recovery. The tagline is now **“Every voice at the table, captioned under the right face.”** in `README.md`, `web/index.html`, and `pyproject.toml`. The viewer also says `Voice attribution` rather than `Voices separated by` for Lite.

The packaged Lite run has `"catchup_model": "glimmer"`, 35 cached catch-ups, 47 verified summary sentences and three verbatim fallback sentences. `calls.jsonl` has 15 Glimmer cache-miss rows and 12 replay-hit rows, all `"where": "local"`; replay checks added the hit rows. The rendered model table says **On this computer**. A real request returned source `glimmer` and three verified sentences with no API key and unreachable hosted/local endpoints.

```bash
.venv/bin/python -m earshot analyze bench/ami_ES2008a/clip.mp4 \
  --tap "Speaker A@0.25,0.29" --tap "Speaker B@0.80,0.36" \
  --tap "Speaker C@0.31,0.78" --tap "Speaker D@0.71,0.78" \
  --out runs/ami_lite --separator lite --catchup-model glimmer --translate es
.venv/bin/python tools/make_demo.py runs/ami_lite demo/ami_meeting \
  --attribution bench/ami_ES2008a/ATTRIBUTION.md
```

## 7. Tests and fresh-clone verification

- Main suite: **70 passed** with `pytest -q`.
- Final fresh local clone, fresh base virtual environment, editable `.[dev]` install: **69 passed, 1 skipped**; the skip is the optional Torch-dependent compatibility test. Offline VTT/SRT export also passed.
- `tests/test_sparkav.py` generates its video with `tools/synthetic.py`; it does not require the AMI clip.
- An optional Node syntax test catches malformed viewer JavaScript. No Node package or runtime dependency was added.
- The first clean-clone attempt incorrectly applied `EARSHOT_REPLAY=1` to fake-client unit tests, producing four cache-miss failures. The standard suite without that override passed, followed by a separate offline replay test. Both outputs are retained in `review/clean_clone_review2.log`.
- A fresh-clone replay request with no key and unreachable model endpoints returned the cached Glimmer catch-up successfully.

## 8. Evidence locations

- A/B audio and matrices: `review/ab_listen/`, `review/envelope_ab.json`, `review/ab_spikes.log`.
- Full separation and bench logs: `review/ami_samaudio_keep_mps_analyze.log`, `review/ami_samaudio_keep_bench_review2.log`.
- Machine-readable full scores: `runs/ami_samaudio_keep/bench_review2.json` (ignored run output).
- Held-out logs and scores: `review/ami_samaudio_keep_635_analyze.log`, `review/ami_samaudio_keep_635_bench_review2.log`, `runs/ami_samaudio_keep_635/bench_review2.json`.
- Public results: `bench/RESULTS.md` and `README.md`.
- Clean-clone test/replay: `review/clean_clone_review2.log`.
- Local Glimmer run: `review/glimmer_demo_analyze.log` and `demo/ami_meeting/calls.jsonl`.
- MPS/CPU unsuccessful batch diagnostics: `review/separation_sample.txt`, `review/separation_cpu_sample.txt`.

## 9. Spend cap

Final estimated hosted spend is **$3.286617 of $20.00**, generated from the real run logs in `review/SPEND.md`. This includes the previously omitted 635 s development run and both new full evaluations. Local Glimmer, SAM Audio and cache hits add $0. Spark AV remains within its separate $3 experiment cap at $0.330758. No credential value is included in logs or commits.
