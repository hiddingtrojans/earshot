# GATE T12 — engineering freeze checks

Date: 2026-11-02. Device: Apple M5 Max, 36 GiB RAM, arm64; Python 3.12.13. The implementation run stops here with known owner-only publication/submission steps and the already-recorded SAM Audio weight blocker.

## Commits after GATE_T6

- `38a591f` Add offline subtitle and voice downloads
- `3e02d3f` Constrain subtitle cue width for wrapping
- `3cfc6dd` Add cached bilingual caption bubbles
- `c419541` Keep speaker labels out of translated caption text
- `1b26cf3` Preserve focus for interactive translated bubbles
- `dcb92d6` Cache Spanish AMI demo and usage report
- `2200bce` Document delivered demo and attribution
- `40353df` Add cached local Muse Glimmer catch-ups
- `315d2a6` Ignore caption IDs in catch-up number checks
- `6028602` Document verified local Glimmer catch-ups

Earlier evidence is in `GATE_T1.md`, `GATE_T3.md`, `GATE_T4.md`, and `GATE_T6.md`.

## Freeze commands and real output

```bash
.venv/bin/pytest -q
# ......................................................                   [100%]
# 54 passed in 6.03s
```

A new clone at `/Users/raulacedo/src/earshot/verify-freeze` received a fresh Python 3.12 venv and base (non-dev) install:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e /Users/raulacedo/src/earshot/verify-freeze
# Successfully installed ... earshot-0.1.0 ...
```

The banned-runtime scan over `earshot`, `web`, and `tools` for `whisper|pyannote|silero|tesseract|easyocr|paddleocr|spacy|presidio|sentence_transformers|laion_clap|elevenlabs|openai.audio|gemini|anthropic` returned no matches. The full-history scan for `api[_-]?key|bearer ` returned only environment names, `export MODEL_API_KEY=...`, and code such as `Bearer {api_key()}` / `EARSHOT_LOCAL_API_KEY`; no credential value was present. The temporary history patch was removed.

Final spend recomputation:

```bash
.venv/bin/python tools/spend_report.py runs/live_smoke runs/ami_lite runs/ami_negative runs/ui_live --out review/SPEND.md
# calls=55 estimated_spend=$0.977157 cap=$20.00
```

Local Glimmer calls are included as $0 rows. All hosted usage comes from real cache misses and response usage.

## Final clean-clone replay

The new clone served the committed 42.65 MB demo with no key and no reachable Meta endpoint:

```bash
env -u MODEL_API_KEY EARSHOT_REPLAY=1 MODEL_API_BASE_URL=http://127.0.0.1:9 \
  .venv/bin/python -m earshot serve demo/ami_meeting --replay --port 8775
```

Real results:

```text
viewer HTTP 200
video range HTTP 206, bytes 1024
catch-up: source=spark, statuses=[verified, verified]
VTT: starts WEBVTT=True, contains ::cue(.spk0)=True
export: wrote freeze.vtt (2,334 bytes), freeze.srt (1,598 bytes)
```

The built-in browser rendered the real AMI captions, threads, download controls, Lite audio notice, and the `Original / Español` picker from this exact clean clone. No Meta request could have occurred: replay was enforced and the base URL was unreachable.

## T7–T10 evidence

### Spanish bubbles (T7)

Accepted real call: `resp_6ae8a85d91d8763104c449ac`, 5,892 ms, 492 uncached input + 1,023 output tokens, cache key `5d2c03de00ae6332e2a81e4a`. All 10 caption IDs returned exactly once with no speaker-label duplication. A prior response that inserted labels was rejected and regenerated with a clearer prompt; both real calls remain in provenance and spend.

The browser displayed Spanish text and original English on focus. Active bubble nodes now persist across animation frames and accept pointer/keyboard interaction. A forced untranslated fixture displayed `Español (untranslated)`, the warning `Translation unavailable; showing the original text`, and original captions. Unit tests cover valid IDs, duplicates/mismatches, empty/failure fallback, and label rejection.

### Subtitle and audio exports (T8/T9)

`python -m earshot export runs/ami_lite --vtt runs/ami_lite/captions.vtt --srt runs/ami_lite/captions.srt` produced real exports. FFprobe identified `webvtt` and all 10 cue timings. A native browser `<track>` showed the orange Speaker A cue “Good question.” at its head-derived position. The VTT has per-speaker classes/colours, clamped line/position settings, 45% width, and separate overlapping cues; SRT keeps plain text and `[Speaker N]` labels.

The offline viewer exposes both downloads. A synthetic fixture (not demo evidence) showed `Download Speaker A's voice` beside `Hear only` and returned HTTP 206 for its M4A range. The real Lite demo explicitly says isolated audio is unavailable instead of showing a false download.

**Unverified:** VLC is not installed on this Mac. Long 22-second VTT cues also rendered poorly in the browser; short cues and colour/position work. The README records both limitations instead of claiming universal player compatibility.

### Local Muse Glimmer (T10)

`ollama pull muse-glimmer` completed (18 GB installed) after resuming a tool-timeout interruption. The real 10-second AMI regeneration used cached SAM/Voice/Spark calls and three local Glimmer calls:

| Who | Request | Latency | Completion tokens | Result after deterministic verification |
|---|---|---:|---:|---|
| Table | `chatcmpl-991` | 57,779 ms | 9 | Empty model answer → verbatim captions |
| Speaker A | `chatcmpl-318` | 83,752 ms | 103 | Valid c002 sentence verified; c009/c014/c016 outside-window citations rejected |
| Speaker B | `chatcmpl-973` | 40,286 ms | 76 | Two verified sentences |

Glimmer included caption IDs in sentence text, exposing a verifier bug that treated `c002` as an unsupported number. Commit `315d2a6` excludes caption IDs only from numeric checks; unsupported numbers and out-of-window citations still fail. Replay then produced verified A/B sentences and cache hits for all three Glimmer calls. The browser's model table says **On this computer**, and `/api/catchup?t=10&person=0&seconds=30` returned `source=glimmer`, `status=verified`. No temperature was forced; max tokens is 8,000; JSON schema has JSON-mode fallback; all local calls use `CallLog.cached`.

## Checklist audit

- ✓ Tests and deterministic coverage green; small local commits; no push.
- ✓ Base editable install works in a clean venv; final clean-clone replay works with no key/network.
- ✓ No banned runtime dependency, private media, secret, invented metric, or bypassed model cache found.
- ✓ T1/T2/T4/T5/T6/T7/T9/T10 implementation checks have real evidence in this and earlier gates.
- ✓ README has models/locations, organizer ruling, CLAP-off/no-T5 notes, Lite limitation, prior art, AMI attribution, responsible use, results, and a real screenshot.
- ✗ **T0 public repository:** owner must create/push it; this run was explicitly local-only.
- ✗ **T3 real SAM Audio weights:** still blocked by Hugging Face approval; no SAM Audio result is claimed.
- ✗ **T8 VLC:** not installed, so VLC colour playback and long-cue layout remain unverified.
- ✗ **Video/public submission:** owner must record the ≤2:59 video, play it logged out, push the public repo, complete/read back the submission form, and link the X post. These are not implemented by this engineering run.

The implementation-specific T12 checks are complete. The ✗ items are explicit owner/external blockers, not hidden passes.

## Exact owner actions, in order

1. If separation is still wanted before feature freeze, obtain `facebook/sam-audio-small-tv` approval and rerun T3/T4. Otherwise keep the honest Lite demo and its limitations.
2. Review and push all local history and the demo to a new public repository.
3. Check VTT in VLC, including a long cue; adjust player-specific layout if needed.
4. Record the real ≤2:59 product video. Do not claim live processing, SAM Audio separation, or simultaneous-caption recovery from this Lite demo. Show real model calls, AMI attribution, and the opening new-work disclosure; explain Glimmer locally if using it for the bonus.
5. Submit by the organizer deadline: check video logged out, read back every form field, and link the exact X post.

Final estimated Meta API spend: **$0.977157 of $20.00**. Replay and local Glimmer added no hosted spend after the accepted Spanish call.
