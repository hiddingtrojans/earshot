"""Local setup/viewer server: background analysis, replay snapping, media ranges, catch-up and exports."""

from __future__ import annotations

import json
import math
import mimetypes
import os
import re
import threading
import uuid
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .calls import CallLog, ReplayMiss
from .media import probe
from .spark import catch_up
from .timeline import Caption
from .tracking import Tap

WEB = Path(__file__).resolve().parent.parent / "web"


def snap_taps(taps: list[Tap], doc: dict) -> list[Tap]:
    cached = doc.get("people", [])
    if len(taps) != len(cached):
        raise ValueError(f"Replay needs exactly {len(cached)} taps for this cached run")
    remaining = set(range(len(cached)))
    snapped = []
    for tap in taps:
        candidates = []
        for index in remaining:
            person = cached[index]
            x, y, frame = person["tap"]
            distance = math.hypot(tap.x - x, tap.y - y)
            candidates.append((distance, index, x, y, frame))
        distance, index, x, y, frame = min(candidates)
        if distance > 0.05:
            raise ValueError(f"{tap.name} is more than 5% away from every unused cached person")
        remaining.remove(index)
        snapped.append(Tap(cached[index]["name"], x, y, int(frame)))
    return snapped


def make_handler(run: Path, replay: bool, setup_video: Path | None = None, separator: str = "lite"):
    doc_path = run / "earshot.json"
    doc = json.loads(doc_path.read_text()) if doc_path.exists() else {}
    calls = CallLog(run, replay=replay)
    jobs = {}
    jobs_lock = threading.Lock()

    def update_job(job_id: str, step: str | None = None, **changes) -> None:
        with jobs_lock:
            job = jobs[job_id]
            if step:
                job["steps"].append(step)
                job["step"] = step
            job.update(changes)

    def run_analysis(job_id: str, taps: list[Tap], selected_separator: str) -> None:
        from .pipeline import Options, analyze

        try:
            analyze(setup_video, taps, run, Options(
                separator=selected_separator, replay=False,
                progress=lambda step: update_job(job_id, step),
            ))
        except Exception as error:
            update_job(job_id, status="error", error=str(error)[:500])
        else:
            update_job(job_id, status="done", url="/viewer")

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(run), **kw)

        def log_message(self, fmt, *args):
            pass

        def _json(self, payload, status=HTTPStatus.OK):
            body = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _text(self, text: str, content_type: str):
            body = text.encode()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            url = urlparse(self.path)
            if url.path in ("/", "/index.html"):
                return self._file(WEB / ("setup.html" if setup_video else "index.html"))
            if url.path == "/viewer":
                return self._file(WEB / "index.html")
            if url.path in ("/api/subtitles.vtt", "/api/subtitles.srt"):
                from .export import srt, vtt

                current = json.loads(doc_path.read_text())
                if url.path.endswith(".vtt"):
                    return self._text(vtt(current), "text/vtt; charset=utf-8")
                return self._text(srt(current), "application/x-subrip; charset=utf-8")
            if url.path == "/api/setup/info" and setup_video:
                info = probe(setup_video)
                return self._json({"width": info.width, "height": info.height, "fps": info.fps, "frames": info.frames,
                                   "duration": info.duration, "replay": replay, "separator": separator})
            if url.path == "/api/setup/video" and setup_video:
                return self._file(setup_video)
            if url.path == "/api/analyze/status" and setup_video:
                job_id = parse_qs(url.query).get("job", [""])[0]
                with jobs_lock:
                    if job_id not in jobs:
                        return self._json({"error": "Unknown analysis job"}, HTTPStatus.NOT_FOUND)
                    job = jobs[job_id]
                    snapshot = {**job, "steps": list(job["steps"])}
                return self._json(snapshot)
            if url.path == "/api/catchup":
                q = parse_qs(url.query)
                t = float(q.get("t", ["0"])[0])
                person = q.get("person", [""])[0]
                person = None if person in ("", "all") else int(person)
                seconds = float(q.get("seconds", ["30"])[0])
                try:
                    current = json.loads(doc_path.read_text())
                    names = [p["name"] for p in current["people"]]
                    captions = [Caption(**c) for c in current["captions"]]
                    res = catch_up(captions, names, t, seconds, calls, person=person)
                    return self._json({"t": t, "person": person, "source": "spark", **res})
                except (ReplayMiss, RuntimeError, FileNotFoundError) as exc:
                    current = json.loads(doc_path.read_text()) if doc_path.exists() else {}
                    pre = [c for c in current.get("catchups", []) if c["person"] == person and c["t"] <= t + 0.01]
                    if pre:
                        best = max(pre, key=lambda c: c["t"])
                        return self._json({**best, "source": "precomputed", "note": str(exc)[:200]})
                    return self._json({"error": str(exc)[:300]}, HTTPStatus.SERVICE_UNAVAILABLE)
            path = (run / url.path.lstrip("/")).resolve()
            if run.resolve() not in path.parents and path != run.resolve():
                return self.send_error(HTTPStatus.FORBIDDEN)
            if path.is_file():
                return self._file(path)
            return self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self):  # noqa: N802
            url = urlparse(self.path)
            if url.path != "/api/analyze" or not setup_video:
                return self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 1_000_000:
                    raise ValueError("Request body is empty or too large")
                payload = json.loads(self.rfile.read(length))
                raw_taps = payload["taps"]
                if not isinstance(raw_taps, list) or not 1 <= len(raw_taps) <= 8:
                    raise ValueError("Add between 1 and 8 people")
                taps = []
                for index, item in enumerate(raw_taps):
                    name = str(item.get("name") or f"Speaker {chr(65 + index)}").strip()
                    x, y, frame = float(item["x"]), float(item["y"]), int(item.get("frame", 0))
                    if not name or not math.isfinite(x) or not math.isfinite(y) \
                            or not 0 <= x <= 1 or not 0 <= y <= 1 or frame < 0:
                        raise ValueError("Each tap needs a name, coordinates between 0 and 1, and a valid frame")
                    taps.append(Tap(name, x, y, frame))
            except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
                return self._json({"error": str(error)[:300]}, HTTPStatus.BAD_REQUEST)

            if replay:
                try:
                    snapped = snap_taps(taps, doc)
                except ValueError as error:
                    return self._json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return self._json({"done": True, "url": "/viewer", "taps": [
                    {"name": tap.name, "x": tap.x, "y": tap.y, "frame": tap.frame} for tap in snapped
                ]})

            selected_separator = payload.get("separator", separator)
            if selected_separator not in ("lite", "samaudio"):
                return self._json({"error": "Unknown separator"}, HTTPStatus.BAD_REQUEST)
            job_id = uuid.uuid4().hex
            with jobs_lock:
                jobs[job_id] = {"status": "running", "steps": [], "step": "Starting analysis"}
            thread = threading.Thread(target=run_analysis, args=(job_id, taps, selected_separator), daemon=True)
            thread.start()
            return self._json({"job": job_id, "status": "running"}, HTTPStatus.ACCEPTED)

        def _file(self, path: Path):
            size = path.stat().st_size
            ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            rng = self.headers.get("Range")
            start, end = 0, size - 1
            m = re.match(r"bytes=(\d*)-(\d*)", rng or "")
            if m:
                if m.group(1):
                    start = int(m.group(1))
                    end = int(m.group(2)) if m.group(2) else size - 1
                else:
                    start = max(0, size - int(m.group(2)))
                end = min(end, size - 1)
                self.send_response(HTTPStatus.PARTIAL_CONTENT)
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            else:
                self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            with path.open("rb") as f:
                f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk = f.read(min(1 << 16, remaining))
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                    except (BrokenPipeError, ConnectionResetError):
                        return
                    remaining -= len(chunk)

    return Handler


def serve(run: Path, port: int = 8765, replay: bool | None = None,
          setup: Path | None = None, separator: str = "lite") -> None:
    if replay is None:
        replay = os.environ.get("EARSHOT_REPLAY") == "1" or not os.environ.get("MODEL_API_KEY")
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(run, replay, setup, separator))
    mode = "replay (cached model responses)" if replay else "live"
    print(f"Earshot viewer: http://127.0.0.1:{port}/  [{mode}]  — Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
