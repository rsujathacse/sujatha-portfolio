from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from aether.api import AetherHandler
from aether import mesh, policy

ROOT = Path(__file__).resolve().parents[1]
POL = ROOT / "samples" / "policies"
FLOWS = ROOT / "samples" / "flows" / "golden.jsonl"


@pytest.fixture
def api_server(tmp_path, monkeypatch):
    monkeypatch.setenv("AETHER_HOME", str(tmp_path / "aether-home"))
    monkeypatch.setenv("AETHER_TOKEN", "slice-token")
    monkeypatch.delenv("AETHER_ALLOW_ANON", raising=False)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), AetherHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address[:2]
    mesh.bootstrap()
    yield f"http://{host}:{port}"
    httpd.shutdown()


def _req(url: str, method: str = "GET", body: dict | None = None, token: str = "slice-token"):
    import urllib.error
    import urllib.request

    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode())


def test_health_and_mesh(api_server):
    status, body = _req(f"{api_server}/v1/healthz")
    assert status == 200
    assert body["rev"] == "1.0"
    status, mesh_body = _req(f"{api_server}/v1/mesh")
    assert status == 200
    assert mesh_body["healthy"] is True


def test_api_shadow_promote(api_server):
    doc = policy.load_yaml(POL / "frontend-to-checkout.yaml")
    flows = policy.load_flows(FLOWS)
    status, report = _req(
        f"{api_server}/v1/policies/shadow",
        method="POST",
        body={"policy": doc, "flows": flows},
    )
    assert status == 200, report
    assert report["qualified"] is True
    status, promoted = _req(
        f"{api_server}/v1/policies/frontend-to-checkout/promote",
        method="POST",
        body={},
    )
    assert status == 200
    assert promoted["promoted"] is True


def test_api_unauthorized(api_server):
    status, body = _req(f"{api_server}/v1/mesh", token="wrong")
    assert status == 401
    assert body["code"] == "UNAUTHORIZED"
