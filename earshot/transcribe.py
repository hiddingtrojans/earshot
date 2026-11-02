"""Muse Voice Transcribe (hosted) — file endpoint with diarization.

Request format follows Meta's cookbook (07_sam/03_headlocked_speech_bubble_captions/
scripts/transcribe.py): multipart `request` JSON + `audio` WAV, mono 16-bit 24 kHz.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass

import numpy as np

from .calls import BASE_URL, CallLog, api_key, content_key
from .media import TRANSCRIBE_SR, wav_bytes

VOICE_MODEL = "muse-voice-transcribe-1.0"
MAX_SECONDS = 600  # file endpoint limit: 10 minutes


@dataclass(frozen=True)
class Turn:
    speaker: str
    start: float
    end: float
    text: str


def _post_transcribe(audio_wav: bytes, mode: str) -> tuple[dict, dict]:
    from .calls import response_metadata

    request = {"mode": mode, "model": VOICE_MODEL, "audioEncoding": "WAV"}
    boundary = f"----earshot-{uuid.uuid4().hex}"
    body = b"".join([
        f'--{boundary}\r\nContent-Disposition: form-data; name="request"\r\n'
        f"Content-Type: application/json\r\n\r\n".encode(),
        json.dumps(request).encode(), b"\r\n",
        f'--{boundary}\r\nContent-Disposition: form-data; name="audio"; filename="audio.wav"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n".encode(),
        audio_wav, b"\r\n", f"--{boundary}--\r\n".encode(),
    ])
    req = urllib.request.Request(
        f"{BASE_URL}/asr/transcribe", data=body, method="POST",
        headers={"Authorization": f"Bearer {api_key()}",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read())
            return result, response_metadata(result, resp.headers)
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Muse Voice returned HTTP {err.code}: {detail}") from err


def transcribe(audio_24k: np.ndarray, calls: CallLog, purpose: str, mode: str = "DIARIZATION",
               repeat: int | None = None) -> list[Turn]:
    """Transcribe a mono 24 kHz signal, optionally with a repeat-specific cache key."""
    if audio_24k.size / TRANSCRIBE_SR > MAX_SECONDS:
        raise ValueError("audio longer than the 10-minute file limit; split it first")
    wav = wav_bytes(audio_24k, TRANSCRIBE_SR)
    key = content_key(wav)

    def call():
        result, response_meta = _post_transcribe(wav, mode)
        return result, {"audio_seconds": round(audio_24k.size / TRANSCRIBE_SR, 2), **response_meta}

    key_parts = (key, mode) if repeat is None else (key, mode, repeat)
    result = calls.cached(model=VOICE_MODEL, purpose=purpose, where="hosted", key_parts=key_parts, fn=call)
    return turns_from_response(result)


def turns_from_response(result: dict) -> list[Turn]:
    turns = []
    for t in result.get("turns", []):
        text = (t.get("transcript") or "").strip()
        if not text:
            continue
        turns.append(Turn(str(t.get("speaker", "0")), t["startMs"] / 1000, t["endMs"] / 1000, text))
    return sorted(turns, key=lambda t: t.start)
