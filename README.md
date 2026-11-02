# Earshot

**Every voice at the table, captioned, even when people talk at once.**

Deaf and hard-of-hearing people have a name for being left out of group conversations: *dinner table syndrome*. One of its main causes is people talking over each other. Today's live captions turn a table into one stream of text: overlapping speech merges or disappears, and you can't tell who said what.

Earshot takes a video of the table and:

1. **tracks each person you tap** with SAM 3.1;
2. **pulls each person's voice out of the mix** with SAM Audio, using that person's masks as the visual prompt, so two people talking at once become two clean tracks;
3. **captions each voice separately** with Muse Voice Transcribe, and shows the captions as bubbles above each person's head, two at once when they overlap;
4. **splits side conversations into threads** and answers **"What did I miss?"** with Muse Spark. Every summary sentence must cite the captions it comes from and pass deterministic checks, or it's replaced by the captions themselves.

> Built during the Meta Global AI Developer Hackathon (26 Oct – 4 Nov 2026). Everything in this repository was written during the event. Meta's cookbook recipe `07_sam/03_headlocked_speech_bubble_captions` already shows speech-bubble captions from diarization plus SAM 3.1, with voices matched to people by hand. Earshot's contribution is the case that recipe can't handle: separating **overlapping** speech, and binding each voice to a face with **no manual matching**. Earshot reuses no code from that recipe; it follows the cookbook's API request formats.

## Meta models used

| Model | Where it runs | What it does in Earshot | Code |
|---|---|---|---|
| `sam-3.1` | Meta Model API | Tracks each tapped person through the video (point prompts → per-frame masks) | `earshot/tracking.py` |
| SAM Audio (`facebook/sam-audio-small-tv`) | This computer | Isolates each person's voice, with their SAM 3.1 masks as the visual prompt | `earshot/separation.py` |
| `muse-voice-transcribe-1.0` | Meta Model API | Transcribes each isolated voice; also diarizes the raw mix as the single-stream baseline | `earshot/transcribe.py` |
| `muse-spark-1.3` | Meta Model API | Groups captions into conversation threads; writes cited "What did I miss?" summaries | `earshot/spark.py` |

Everything else is deterministic code: voice activity (frame energy with hysteresis), the caption timeline and bleed filter, citation checks, metrics, and FFmpeg for media. No other model runs at runtime.

### Rules notes (Meta-only runtime models)

- SAM Audio's released config builds optional **re-rankers**, including **CLAP**, which isn't a Meta model. Earshot turns them off with config overrides (`text_ranker=None, visual_ranker=None, span_predictor=None`) and installs SAM Audio without them (`--no-deps`).
- SAM Audio conditions on text through a frozen **T5-base** encoder (Google) inside the model, on every call. We've asked the organizers whether that's acceptable inside a Meta open model. For a fixed prompt that encoder's output is a constant, so `--text-features text_features.npz` (made once with `tools/precompute_text_features.py`) replaces it with a lookup. In that mode T5 is never loaded or run at runtime. We use it only as the organizers advise.
- **Earshot-Lite** (`--separator lite`) needs no SAM Audio at all. It gives each diarized speaker to the face whose head moves while they talk (measured inside the SAM 3.1 masks). It keeps face-anchored captions without manual matching, but can't recover overlapping words.

## Run it

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
brew install ffmpeg            # or your platform's ffmpeg
export MODEL_API_KEY=...       # Meta Model API key
```

**Replay the included demo without any keys** (all model responses are cached in the run folder):

```bash
python -m earshot serve demo/dinner --replay
# open http://127.0.0.1:8765/
```

**Analyze your own video.** Tap each person with `Name@x,y`, where x,y are fractions of the frame on frame 0 (a point on their face):

```bash
python -m earshot analyze table.mp4 --tap "Ana@0.31,0.40" --tap "Raúl@0.68,0.38" --out runs/table
python -m earshot serve runs/table
```

Use `--separator lite` to run without SAM Audio.

### Install SAM Audio (Apple Silicon)

```bash
pip install torch torchaudio torchvision torchcodec "transformers>=4.54" einops torchdiffeq \
    huggingface_hub safetensors timm ftfy regex sentencepiece
pip install "git+https://github.com/facebookresearch/dacvae.git"
# --no-deps: perception_models lists decord and xformers (no macOS arm64 wheels, not needed here)
pip install --no-deps "git+https://github.com/facebookresearch/perception_models@unpin-deps"
# --no-deps: skips laion-clap and imagebind, which only the disabled re-rankers use
pip install --no-deps "git+https://github.com/facebookresearch/sam-audio.git"
hf auth login                  # access to facebook/sam-audio-small-tv is gated on Hugging Face
```

`spike/earshot_spike.py` checks that SAM Audio runs on your machine, times it, and scores the separation on a clip with known ground truth.

## Dinner Table Bench

`python -m earshot bench RUN --truth truth.json` scores a run against what each person actually said:

- **word error rate** per person;
- **right person**: the share of caption words that belong to that person;
- **overlap words**: the share of words spoken while someone else was talking that make it into that person's captions;
- **SI-SDR** of each isolated voice, when clean reference tracks exist.

The baseline is the same table as one diarized stream (what single-stream captions give you). Each anonymous speaker is mapped to the person it matches best, so the baseline is shown at its best. See `earshot/bench.py` for the truth file format. Composed clips (each person recorded separately, then mixed with `spike/earshot_spike.py compose`) give exact references.

## How it's built

```
earshot/
  tracking.py     SAM 3.1 object prompts from taps, stream parsing with meta_sam_parser, masks, head anchors
  separation.py   SAM Audio windowed separation (10 s windows, 1 s crossfade); Earshot-Lite passthrough
  transcribe.py   Muse Voice Transcribe file endpoint
  activity.py     deterministic voice activity and overlap windows
  timeline.py     per-person captions, bleed filter, overlap flags
  lite.py         mouth-motion attribution (no separation)
  spark.py        threads + verified catch-up (citations, names and numbers checked in code)
  calls.py        model-call cache, replay mode and provenance log (shown in the viewer)
  bench.py        Dinner Table Bench metrics
  server.py       local viewer server (Range requests for video seeking, catch-up API)
web/index.html    the viewer
tests/            unit tests and a synthetic end-to-end run with fake model clients
```

## Limitations

- Earshot analyzes recorded clips; it is not live yet.
- Separation degrades when voices are very similar or when a speaker's face isn't visible.
- Use it only with people who know they're being recorded. Earshot does no face recognition: people are the ones you tap, with the names you type.

## Licence

MIT, see `LICENSE`. Model licences: SAM 3.1 and SAM Audio are under the SAM License. `meta_sam_parser` is under the SAM License. Muse models are used through the Meta Model API under its terms.
