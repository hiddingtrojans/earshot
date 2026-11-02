"""Local viewer server: static files with HTTP Range (video seeking) + catch-up API."""

from __future__ import annotations

import json
import mimetypes
import os
import re
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .calls import CallLog, ReplayMiss
from .spark import catch_up
from .timeline import Caption

WEB = Path(__file__).resolve().parent.parent / "web"


def make_handler(run: Path, replay: bool):
    doc = json.loads((run / "earshot.json").read_text())
    names = [p["name"] for p in doc["people"]]
    captions = [Caption(**{k: v for k, v in c.items()}) for c in doc["captions"]]
    calls = CallLog(run, replay=replay)

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(run), **kw)

        def log_message(self, fmt, *args):  # quieter
            pass

        def _json(self, payload, status=HTTPStatus.OK):
            body = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            url = urlparse(self.path)
            if url.path in ("/", "/index.html"):
                return self._file(WEB / "index.html")
            if url.path == "/api/catchup":
                q = parse_qs(url.query)
                t = float(q.get("t", ["0"])[0])
                person = q.get("person", [""])[0]
                person = None if person in ("", "all") else int(person)
                seconds = float(q.get("seconds", ["30"])[0])
                try:
                    res = catch_up(captions, names, t, seconds, calls, person=person)
                    return self._json({"t": t, "person": person, "source": "spark", **res})
                except (ReplayMiss, RuntimeError) as exc:
                    pre = [c for c in doc.get("catchups", []) if c["person"] == person and c["t"] <= t + 0.01]
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
                else:  # suffix range
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


def serve(run: Path, port: int = 8765, replay: bool | None = None) -> None:
    if replay is None:
        replay = os.environ.get("EARSHOT_REPLAY") == "1" or not os.environ.get("MODEL_API_KEY")
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(run, replay))
    mode = "replay (cached model responses)" if replay else "live"
    print(f"Earshot viewer: http://127.0.0.1:{port}/  [{mode}]  — Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
