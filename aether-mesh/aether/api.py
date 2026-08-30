"""Local Aether Mesh HTTP API. Start with: python -m aether.api"""

from __future__ import annotations

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from aether import REV, errors, mesh, policy, tetragon

SHADOW_RE = re.compile(r"^/v1/policies/shadow$")
PROMOTE_RE = re.compile(r"^/v1/policies/([^/]+)/promote$")
REPLAY_RE = re.compile(r"^/v1/flows/replay$")
TETRAGON_RE = re.compile(r"^/v1/tetragon/events$")


def _token_ok(handler: BaseHTTPRequestHandler) -> bool:
    expected = os.environ.get("AETHER_TOKEN", "slice-token")
    header = handler.headers.get("Authorization", "")
    if header == f"Bearer {expected}":
        return True
    if os.environ.get("AETHER_ALLOW_ANON") == "1":
        return True
    return False


class AetherHandler(BaseHTTPRequestHandler):
    server_version = "AetherAPI/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys_stderr = __import__("sys").stderr
        sys_stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _error(self, exc: errors.AetherError) -> None:
        self._send(exc.http_status, exc.to_dict())

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            raise errors.AetherError(
                code="VALIDATION",
                message="Body must be JSON.",
                exit_code=2,
                http_status=400,
            ) from exc
        if not isinstance(data, dict):
            raise errors.AetherError(
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
                self._send(200, {"status": "ok", "rev": REV})
                return
            if path == "/v1/mesh":
                self._send(200, mesh.status())
                return
            if path == "/v1/identities":
                self._send(200, {"identities": mesh.identity_index()})
                return
            if path == "/v1/policies":
                self._send(200, policy.list_policies())
                return
            if path == "/v1/tetragon/events":
                self._send(200, {"events": tetragon.list_events()})
                return
            self._send(404, {"code": "NOT_FOUND", "message": "No such route."})
        except errors.AetherError as exc:
            self._error(exc)

    def do_POST(self) -> None:  # noqa: N802
        if not _token_ok(self):
            self._send(401, {"code": "UNAUTHORIZED", "message": "Bearer token required."})
            return
        path = urlparse(self.path).path
        try:
            body = self._read_json()
            if path == "/v1/mesh/bootstrap":
                self._send(200, mesh.bootstrap())
                return
            if path == "/v1/policies/shadow":
                doc = body.get("policy") or {}
                flows = body.get("flows") or []
                self._send(200, policy.shadow(doc, flows))
                return
            match = PROMOTE_RE.match(path)
            if match:
                self._send(200, policy.promote(match.group(1)))
                return
            if path == "/v1/flows/replay":
                self._send(200, policy.replay(body.get("flows") or [], body.get("dataplane", "enforce")))
                return
            if path == "/v1/tetragon/policies":
                self._send(200, tetragon.apply_policy(body.get("policy") or body))
                return
            if path == "/v1/tetragon/events":
                self._send(200, tetragon.replay_events(body.get("events") or []))
                return
            if path == "/v1/admin/inject-identity-collision":
                mesh.inject_identity_collision()
                return
            self._send(404, {"code": "NOT_FOUND", "message": "No such route."})
        except errors.AetherError as exc:
            self._error(exc)


def main() -> None:
    host = os.environ.get("AETHER_API_HOST", "127.0.0.1")
    port = int(os.environ.get("AETHER_API_PORT", "8787"))
    httpd = ThreadingHTTPServer((host, port), AetherHandler)
    print(f"Aether API {REV} on http://{host}:{port}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
