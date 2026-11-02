# SAM Audio conditioning comparison

Date: 2026-11-02. Device: Apple M5 Max (MPS). Model: `facebook/sam-audio-small-tv`. Seed: **0** for both runs. Input: the same 10 s of public AMI ES2008a, box `[0.0, 0.0, 0.5, 0.5]`, reference `ref_A.wav`, and text prompt `""`.

## Commands

```bash
python spike/earshot_spike.py run --video bench/ami_ES2008a/clip.mp4 \
  --box 0 0 0.5 0.5 --ref bench/ami_ES2008a/ref_A.wav \
  --seconds 10 --seed 0 --out spike/out/ami_precomputed

python spike/earshot_spike.py run --video bench/ami_ES2008a/clip.mp4 \
  --box 0 0 0.5 0.5 --ref bench/ami_ES2008a/ref_A.wav \
  --seconds 10 --seed 0 --allow-t5 --out spike/out/ami_allow_t5
```

Both commands used `HF_HUB_CACHE="$PWD/.hf-cache/hub"` so credentials stayed in the default store while caches remained in the project.

## Real reports

| Condition | Load (s) | Visual inference (s) | RTF | Visual SI-SDR vs headset (dB) | Mixture baseline (dB) | Improvement (dB) | Forbidden imports |
|---|---:|---:|---:|---:|---:|---:|---|
| Precomputed `assets/text_features.npz` | 374.1 | 20.47 | 2.05 | -32.13 | -32.91 | +0.78 | `[]` |
| Local T5 with `--allow-t5` | 45.2 | 21.01 | 2.10 | -32.13 | -32.91 | +0.78 | `[]` |

Load time includes the initial model download in the first run. MPS was used for both; no CPU fallback was needed.

Direct comparison of the two `target_visual.wav` files:

- `samples_equal`: false (maximum absolute difference `0.000030517578125`).
- SI-SDR, precomputed output against local-T5 output: **80.775909 dB**.
- SI-SDR in the reverse direction: **80.775926 dB**.
- The files are therefore not claimed to be bit-identical; the measured equivalence is far above the required threshold.

## Decision

**80.776 dB > 30 dB**, so **precomputed conditioning remains the default**. `--allow-t5` is allowed but is not selected as the default. This is a threshold decision, not a compliance restriction. Full logs are in `sam_audio_precomputed.log` and `sam_audio_allow_t5.log`.
