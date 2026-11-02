"""Model-call cache, replay and provenance log.

Every hosted or local model call goes through `CallLog.cached(...)`:

* live mode: the call runs, its response is stored under `<run>/calls/<key>.json`
  together with model, purpose, latency and request ID;
* replay mode (`EARSHOT_REPLAY=1` or `--replay`): nothing is called, the stored
  response is returned, so judges can run the whole demo without API keys.

The UI shows `calls.jsonl` as the model-call strip.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


class ReplayMiss(RuntimeError):
    pass


def content_key(*parts: Any) -> str:
    h = hashlib.sha256()
    for part in parts:
        if isinstance(part, (bytes, bytearray)):
            h.update(bytes(part))
        else:
            h.update(json.dumps(part, sort_keys=True, default=str).encode())
        h.update(b"\x00")
    return h.hexdigest()[:24]


def response_metadata(response: dict, headers: Any = None) -> dict:
    meta = {}
    request_id = response.get("id") or response.get("request_id")
    if headers is not None:
        normalized = {str(key).lower(): value for key, value in headers.items()}
        request_id = request_id or normalized.get("x-request-id") or normalized.get("request-id")
    if request_id:
        meta["request_id"] = str(request_id)
    if response.get("usage") is not None:
        meta["usage"] = response["usage"]
    return meta


@dataclass
class CallLog:
    run_dir: Path
    replay: bool = field(default_factory=lambda: os.environ.get("EARSHOT_REPLAY") == "1")

    def __post_init__(self) -> None:
        self.calls_dir = self.run_dir / "calls"
        self.calls_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.run_dir / "calls.jsonl"

    def cached(self, *, model: str, purpose: str, where: str, key_parts: tuple,
               fn: Callable[[], tuple[Any, dict]]) -> Any:
        """Run `fn` (returning (result_json, meta)) unless a cached result exists."""
        key = content_key(model, purpose, *key_parts)
        path = self.calls_dir / f"{key}.json"
        if path.exists():
            stored = json.loads(path.read_text())
            self._log({**stored["meta"], "cache": "hit", "key": key})
            return stored["result"]
        if self.replay:
            raise ReplayMiss(f"replay mode: no cached response for {purpose} ({model}), key {key}")
        t0 = time.perf_counter()
        result, meta = fn()
        meta = {
            "model": model, "purpose": purpose, "where": where,
            "latency_ms": round((time.perf_counter() - t0) * 1000), "time": time.time(), **meta,
        }
        path.write_text(json.dumps({"meta": meta, "result": result}, default=str))
        self._log({**meta, "cache": "miss", "key": key})
        return result

    def _log(self, entry: dict) -> None:
        with self.log_path.open("a") as f:
            f.write(json.dumps(entry, default=str) + "\n")


def api_key() -> str:
    key = os.environ.get("MODEL_API_KEY")
    if not key:
        raise RuntimeError("Set MODEL_API_KEY (or run with --replay to use cached model responses).")
    return key


BASE_URL = os.environ.get("MODEL_API_BASE_URL", "https://api.meta.ai/v1")
