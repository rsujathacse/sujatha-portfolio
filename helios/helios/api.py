"""Local Helios HTTP API. Start with: python -m helios.api"""

from __future__ import annotations

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from helios import errors, fabric

JOBS_RE = re.compile(r"^/v1/jobs$")
JOB_RE = re.compile(r"^/v1/jobs/([^/]+)$")
ART_RE = re.compile(r"^/v1/jobs/([^/]+)/artifacts$")


def _token_ok(handler: BaseHTTPRequestHandler) -> bool:
    expected = os.environ.get("HELIOS_TOKEN", "slice-token")
    header = handler.headers.get("Authorization", "")
    if header == f"Bearer {expected}":
        return True
    # Local slice also accepts an unset token when HELIOS_ALLOW_ANON=1
    if os.environ.get("HELIOS_ALLOW_ANON") == "1":
        return True
    return False


class HeliosHandler(BaseHTTPRequestHandler):
    server_version = "HeliosAPI/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys_stderr = __import__("sys").stderr
        sys_stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, status: int, body: dict[str, Any], retry_after: int | None = None) -> None:
        payload = json.dumps(body, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        if retry_after is not None:
            self.send_header("Retry-After", str(retry_after))
        self.end_headers()
        self.wfile.write(payload)

    def _error(self, exc: errors.HeliosError) -> None:
        self._send(exc.http_status, exc.to_dict(), retry_after=exc.retry_after)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            raise errors.HeliosError(
                code="VALIDATION",
                message="Body must be JSON.",
                exit_code=2,
                http_status=400,
            ) from exc
        if not isinstance(data, dict):
            raise errors.HeliosError(
                code="VALIDATION",
                message="Body must be a JSON object.",
                exit_code=2,
                http_status=400,
            )
        return data

    def do_GET(self) -> None:  # noqa: N802
        if not _token_ok(self):
            self._send(401, {"code": "UNAUTHORIZED", "message": "Bearer token required."})
            return
        path = urlparse(self.path).path
        try:
            if path in {"/healthz", "/v1/healthz"}:
                self._send(200, {"status": "ok", "rev": "1.1"})
                return
            match = JOB_RE.match(path)
            if match:
                self._send(200, fabric.get_job(match.group(1)))
                return
            match = ART_RE.match(path)
            if match:
                self._send(200, fabric.job_artifacts(match.group(1)))
                return
            self._send(404, {"code": "NOT_FOUND", "message": "No such path."})
        except errors.HeliosError as exc:
            self._error(exc)

    def do_POST(self) -> None:  # noqa: N802
        if not _token_ok(self):
            self._send(401, {"code": "UNAUTHORIZED", "message": "Bearer token required."})
            return
        path = urlparse(self.path).path
        try:
            if JOBS_RE.match(path):
                body = self._read_json()
                job = fabric.submit_job(
                    project=str(body.get("project", "")),
                    job_class=str(body.get("class", "")),
                    image=str(body.get("image", "")),
                    pin=str(body.get("pin", "")),
                    input_path=str(body.get("input", "")),
                    fail_if_queued=bool(body.get("fail_if_queued", False)),
                )
                self._send(201, job)
                return
            self._send(404, {"code": "NOT_FOUND", "message": "No such path."})
        except errors.HeliosError as exc:
            self._error(exc)


def main() -> None:
    host = os.environ.get("HELIOS_API_HOST", "127.0.0.1")
    port = int(os.environ.get("HELIOS_API_PORT", "8080"))
    httpd = ThreadingHTTPServer((host, port), HeliosHandler)
    print(f"Helios API 1.1 listening on http://{host}:{port}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
