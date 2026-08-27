from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer

import pytest

from helios.api import HeliosHandler
from helios import fabric


@pytest.fixture
def api_server(tmp_path, monkeypatch):
    monkeypatch.setenv("HELIOS_HOME", str(tmp_path / "helios-home"))
    monkeypatch.setenv("HELIOS_TOKEN", "slice-token")
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), HeliosHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address[:2]
    yield f"http://{host}:{port}"
    httpd.shutdown()


def _req(url: str, method: str = "GET", body: dict | None = None, token: str = "slice-token"):
    import urllib.request
    import urllib.error

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


def test_api_submit_and_get(api_server):
    status, job = _req(
        f"{api_server}/v1/jobs",
        method="POST",
        body={
            "project": "demo",
            "class": "sim",
            "image": "sim-class:1.1",
            "pin": "farm",
            "input": "samples/smoke",
        },
    )
    assert status == 201
    assert job["state"] == "succeeded"
    assert job["feature"] == "analog_sim"
    status, got = _req(f"{api_server}/v1/jobs/{job['job_id']}")
    assert status == 200
    assert got["job_id"] == job["job_id"]
    status, manifest = _req(f"{api_server}/v1/jobs/{job['job_id']}/artifacts")
    assert status == 200
    assert "smoke.log" in manifest["files"]


def test_api_region_pin(api_server):
    status, body = _req(
        f"{api_server}/v1/jobs",
        method="POST",
        body={
            "project": "analog-ip",
            "class": "sim",
            "image": "sim-class:1.1",
            "pin": "burst",
            "input": "samples/smoke",
        },
    )
    assert status == 403
    assert body["code"] == "REGION_PIN"


def test_api_license_exhausted(api_server):
    fabric.drain_licenses("analog_sim")
    status, body = _req(
        f"{api_server}/v1/jobs",
        method="POST",
        body={
            "project": "demo",
            "class": "sim",
            "image": "sim-class:1.1",
            "pin": "farm",
            "input": "samples/smoke",
            "fail_if_queued": True,
        },
    )
    assert status == 429
    assert body["code"] == "LICENSE_EXHAUSTED"
    assert "retry_after" in body
