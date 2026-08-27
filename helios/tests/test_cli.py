from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from helios import errors, fabric, store
from helios.cli import main


@pytest.fixture(autouse=True)
def helios_home(tmp_path, monkeypatch):
    home = tmp_path / "helios-home"
    monkeypatch.setenv("HELIOS_HOME", str(home))
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


def test_whoami():
    code, out, _ = run(["whoami"])
    body = json.loads(out)
    assert code == 0
    assert body["endpoint"] == "farm"
    assert body["rev"] == "1.1"
    assert body["default_project"] == "demo"


def test_quickstart_submit_and_artifacts(tmp_path):
    code, out, _ = run(
        [
            "job",
            "submit",
            "--project",
            "demo",
            "--class",
            "sim",
            "--image",
            "sim-class:1.1",
            "--pin",
            "farm",
            "--input",
            "samples/smoke",
        ]
    )
    job = json.loads(out)
    assert code == 0
    assert job["state"] == "succeeded"
    assert job["placement"] == "farm"
    assert job["feature"] == "analog_sim"
    dest = tmp_path / "helios-out"
    code, _, _ = run(["job", "artifacts", job["job_id"], "--out", str(dest)])
    assert code == 0
    log = (dest / "smoke.log").read_text(encoding="utf-8")
    assert "placement=farm" in log
    assert "feature=analog_sim" in log
    assert "image=sim-class:1.1" in log


def test_region_pin_classified_burst():
    code, _, err = run(
        [
            "job",
            "submit",
            "--project",
            "analog-ip",
            "--class",
            "sim",
            "--image",
            "sim-class:1.1",
            "--pin",
            "burst",
            "--input",
            "samples/smoke",
        ]
    )
    body = json.loads(err)
    assert code == 34
    assert body["code"] == "REGION_PIN"


def test_fail_if_queued_after_drain():
    code, _, _ = run(["admin", "drain-licenses", "--feature", "analog_sim"])
    assert code == 0
    code, _, err = run(
        [
            "job",
            "submit",
            "--project",
            "demo",
            "--class",
            "sim",
            "--image",
            "sim-class:1.1",
            "--pin",
            "farm",
            "--input",
            "samples/smoke",
            "--fail-if-queued",
        ]
    )
    body = json.loads(err)
    assert code == 32
    assert body["code"] == "LICENSE_EXHAUSTED"


def test_quota_exceeded():
    state = store.load()
    state["projects"]["demo"]["quota"] = 1
    store.save(state)
    fabric.drain_licenses("analog_sim")
    fabric.submit_job(
        project="demo",
        job_class="sim",
        image="sim-class:1.1",
        pin="farm",
        input_path="samples/smoke",
    )
    with pytest.raises(errors.HeliosError) as exc:
        fabric.submit_job(
            project="demo",
            job_class="sim",
            image="sim-class:1.1",
            pin="farm",
            input_path="samples/smoke",
        )
    assert exc.value.code == "QUOTA_EXCEEDED"
    assert exc.value.exit_code == 33


def test_nfs_stale():
    job = fabric.submit_job(
        project="demo",
        job_class="sim",
        image="sim-class:1.1",
        pin="farm",
        input_path="samples/smoke",
    )
    fabric.inject_nfs_stale(job["job_id"])
    code, _, err = run(["job", "artifacts", job["job_id"], "--out", "out"])
    body = json.loads(err)
    assert code == 41
    assert body["code"] == "NFS_STALE"
