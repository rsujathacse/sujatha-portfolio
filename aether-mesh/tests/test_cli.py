from __future__ import annotations

import json
from pathlib import Path

import pytest

from aether.cli import main

ROOT = Path(__file__).resolve().parents[1]
POL = ROOT / "samples" / "policies"
FLOWS = ROOT / "samples" / "flows" / "golden.jsonl"
TET = ROOT / "samples" / "tetragon"


@pytest.fixture(autouse=True)
def aether_home(tmp_path, monkeypatch):
    home = tmp_path / "aether-home"
    monkeypatch.setenv("AETHER_HOME", str(home))
    monkeypatch.setenv("AETHER_ALLOW_ANON", "1")
    monkeypatch.chdir(tmp_path)
    yield home


def run(argv: list[str]) -> tuple[int, str, str]:
    import io
    from contextlib import redirect_stderr, redirect_stdout

    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def _promote_baseline() -> None:
    run(["mesh", "bootstrap"])
    for name in (
        "frontend-to-checkout.yaml",
        "checkout-to-payments.yaml",
        "payments-to-inventory.yaml",
    ):
        code, out, err = run(
            ["policy", "shadow", "--file", str(POL / name), "--flows", str(FLOWS)]
        )
        assert code == 0, err or out
        bundle = json.loads(out)["bundle"]
        code, _, err = run(["policy", "promote", "--name", bundle])
        assert code == 0, err


def test_whoami():
    run(["mesh", "bootstrap"])
    code, out, _ = run(["whoami"])
    body = json.loads(out)
    assert code == 0
    assert body["endpoint"] == "clustermesh"
    assert body["rev"] == "1.0"
    assert "shadow" in body["dataplanes"]


def test_mesh_status_healthy():
    code, out, _ = run(["mesh", "bootstrap"])
    body = json.loads(out)
    assert code == 0
    assert body["healthy"] is True
    assert body["workloads"] == 6
    assert body["unique_cluster_ids"] is True


def test_shadow_promote_and_replay_golden():
    _promote_baseline()
    code, out, err = run(
        ["flow", "replay", "--file", str(FLOWS), "--dataplane", "enforce"]
    )
    assert code == 0, err
    body = json.loads(out)
    assert body["flows"] == 5
    assert body["forwarded"] == 3
    assert body["dropped"] == 2
    intents = []
    # Re-read observed verdicts vs intent
    for row in body["observed"]:
        if row["src"]["labels"]["app"] == "frontend" and row["dst"]["labels"]["app"] == "payments":
            assert row["verdict"] == "DROPPED"
            assert row["drop_reason"] == "POLICY_DENIED"
        if row["src"]["labels"]["app"] == "checkout":
            assert row["verdict"] == "FORWARDED"
            assert row["matched_policy"] == "checkout-to-payments"
        intents.append(row["verdict"])
    assert "FORWARDED" in intents


def test_overreach_fails_shadow():
    _promote_baseline()
    code, _, err = run(
        [
            "policy",
            "shadow",
            "--file",
            str(POL / "checkout-to-payments-overreach.yaml"),
            "--flows",
            str(FLOWS),
        ]
    )
    body = json.loads(err)
    assert code == 36
    assert body["code"] == "POLICY_SHADOW_FAILED"


def test_promote_without_shadow():
    run(["mesh", "bootstrap"])
    code, _, err = run(["policy", "promote", "--name", "ghost"])
    body = json.loads(err)
    assert code == 37
    assert body["code"] == "POLICY_NOT_QUALIFIED"


def test_identity_collision():
    run(["mesh", "bootstrap"])
    code, _, err = run(["admin", "inject-identity-collision"])
    body = json.loads(err)
    assert code == 35
    assert body["code"] == "IDENTITY_COLLISION"
    status = json.loads(run(["mesh", "status"])[1])
    assert status["healthy"] is False
    assert status["identity_collisions"]


def test_tetragon_exploit_window():
    run(["mesh", "bootstrap"])
    code, out, err = run(["tetragon", "apply", "--file", str(TET / "payments-enforcer.yaml")])
    assert code == 0, err
    code, out, err = run(["tetragon", "replay", "--file", str(TET / "exploit-window.jsonl")])
    assert code == 0, err
    body = json.loads(out)
    assert body["events"] == 5
    assert body["enforced"] == 3
    actions = {row["call"]: row["action"] for row in body["observed"] if row.get("enforced")}
    assert actions["process_exec"] == "Sigkill"
    assert "tcp_connect" in {row["call"] for row in body["observed"] if row.get("enforced")}
