# GATE T6 — demo folder and key-free replay

Date: 2026-11-02. Best available real run: Earshot-Lite on public AMI ES2008a. SAM Audio remains blocked by gated-weight approval; no synthetic model response or stem was substituted.

## Commits

T5 setup flow:

- `a69e41a` Add tap-to-start live and replay setup
- `f9f8e8e` Fix browser tap coordinates and frame bounds

T6 packaging:

- `4ad4187` Add lightweight real-run demo packager
- `ed7e543` Add cached AMI meeting demo

## T5 browser evidence

Replay setup used four approximate pointer taps on the real AMI grid. Letterboxing was accounted for, all four taps snapped within the 5% limit, and `/viewer` loaded the saved captions immediately without rerunning analysis. Enter on the focused crosshair independently added Speaker A and enabled Analyze; focus styling is present.

Live setup used `runs/live_smoke/source.mp4`, a real 10.08 s AMI cut. The browser displayed actual steps in order: preparing, SAM tracking, group transcription, Lite attribution, caption building, Spark threads/catch-ups, then redirected to `/viewer` only after completion. Real calls include:

- SAM: 252 frames, 43,320 ms, `resp_6ae8a101171e7819bed34d57`.
- Voice: 4.8 s in the viewer's model table; real session ID is in `runs/ui_live/calls.jsonl`.
- Spark: threads plus table/Speaker A/Speaker B catch-ups; the resulting viewer shows two captions and the hosted-model table.

The first live attempt exposed an end-of-video frame bug (`252` for 252 frames). It was rejected before SAM segmentation. The fix clamps the UI to frame 251, prevents native playback toggles on tap, and validates frames before upload. A letterbox coordinate bug found in replay was also fixed and browser-retested. `tests/test_tracking_validation.py` proves an invalid frame fails before upload.

## Demo build

```bash
.venv/bin/pytest -q
# 43 passed in 5.36s

.venv/bin/python tools/make_demo.py runs/ami_lite demo/ami_meeting --attribution bench/ami_ES2008a/ATTRIBUTION.md
# wrote demo/ami_meeting (42.62 MB)
```

Folder contents:

- `analysis.mp4` (6.1 MiB), `tracks.json` (33 MiB), `earshot.json`, `calls.jsonl`;
- 35 JSON-only cached responses (1.6 MiB), no `sep_*.npy`;
- `ATTRIBUTION.md` with the AMI CC BY 4.0 notice.

The run is Lite and every person's `stem` is null. There are no isolated voices to convert or display. The packager's separate WAV-to-M4A test uses AAC 96 kbps and proves no WAV or NumPy cache is retained when stems do exist. No audio was invented for this demo.

## Clean-clone verification

A new local clone was created at `/Users/raulacedo/src/earshot/verify-clone`, followed by a fresh Python 3.12 venv and editable install with dev extras. It served the committed demo with the key removed and an unreachable Meta URL:

```bash
env -u MODEL_API_KEY EARSHOT_REPLAY=1 MODEL_API_BASE_URL=http://127.0.0.1:9 \
  .venv/bin/python -m earshot serve demo/ami_meeting --replay --port 8768
```

Real output:

```text
viewer HTTP 200
video range HTTP 206, bytes 1024
catch-up: source=spark (cache hit), sentences=2, statuses=[verified, verified]
```

The built-in browser then loaded this clean-clone URL and rendered the real AMI captions, both conversation threads, all four people, and the model-call table. `source=spark` means the cached Spark response was used; replay mode prohibited any network fallback and the configured Meta address could not have been reached.

## Done when

- ✓ Viewer audio is light where audio exists: packager converts stems to 96 kbps M4A. Not applicable to this Lite demo because no stems exist.
- ✓ `demo/ami_meeting/` contains the real analysis, tracks, viewer JSON, JSON caches, call provenance, and AMI attribution.
- ✓ Folder is 42.62 MB, below ~50 MB, so it is committed directly; no release fetch script is needed.
- ✓ A clean clone in another directory replays with no key and no network route to Meta, verified by HTTP and the browser.
- ✓ T5's full live flow really invokes `pipeline.analyze` in a background thread; replay snapping applies only in replay and immediately loads saved results.
- ✓ Plain progress steps, no fake percentage bar, and a working keyboard path with visible focus.

## Review checklist self-check

- ✓ 43 tests pass, including real HTTP job execution, snap boundaries, invalid-frame upload prevention, and demo packaging.
- ✓ Public AMI media only; attribution included; no secret or private media added.
- ✓ Every live model response used by the demo is cached and logged. Replay does not bypass `CallLog` or invent responses.
- ✓ Small commits; no push. No new dependency or non-Meta runtime model.
- ✓ No real-time claim: setup explicitly says recorded clips are processed in the background and replay loads saved results.

## Open problems and owner actions

1. Obtain SAM Audio approval to replace Lite with a real separated run if it passes T3/T4. Until then, solo isolated-audio playback/download is unavailable in the demo.
2. Push the local repository publicly after review.
3. Lite's measured right-person and overlap metrics remain worse than the oracle baseline; the README and demo must not imply separation succeeded.

T5's additional live calls brought estimated spend to **$0.967408 of $20.00**. T6 packaging and clean-clone replay added $0. See `SPEND.md`.
