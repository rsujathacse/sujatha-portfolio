"""Scheduler, pin policy, farm licenses, and artifact volume for Helios 1.1."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from helios import errors, store

CLASS_FEATURE = {"sim": "analog_sim", "pnr": "place_route"}
CLASS_IMAGE_FAMILY = {"sim": "sim-class", "pnr": "pnr-class"}
ALLOWED_PINS = {"farm", "burst"}
ACTIVE_STATES = {"queued", "running"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _job_id() -> str:
    return "hel-" + uuid.uuid4().hex[:10]


def whoami() -> dict[str, Any]:
    state = store.load()
    identity = dict(state["identity"])
    identity["user"] = os.environ.get("HELIOS_USER", identity["user"])
    return identity


def require_identity() -> dict[str, Any]:
    identity = whoami()
    if not identity.get("user"):
        raise errors.VALIDATION
    return identity


def admin_status(verbose: bool = False) -> dict[str, Any]:
    state = store.load()
    jobs = state.get("jobs", {})
    by_state: dict[str, int] = {}
    for job in jobs.values():
        by_state[job["state"]] = by_state.get(job["state"], 0) + 1
    queue_depth = sum(1 for job in jobs.values() if job["state"] == "queued")
    body: dict[str, Any] = {
        "scheduler": state["scheduler"]["status"],
        "rev": state.get("rev", store.REV),
        "queue_depth": queue_depth,
        "endpoint": "farm",
    }
    if verbose:
        body["jobs_by_state"] = by_state
        body["projects"] = {
            name: {"data_class": meta["data_class"], "quota": meta["quota"]}
            for name, meta in state["projects"].items()
        }
        body["storage"] = {
            "farm_volume": "ok",
            "probe": "farm-bastion",
            "note": "Do not probe artifact storage from a burst node.",
        }
    return body


def admin_licenses() -> dict[str, Any]:
    state = store.load()
    features = {}
    for name, pool in state["licenses"].items():
        in_use = pool["total"] if pool.get("drained") else pool.get("in_use", 0)
        features[name] = {"total": pool["total"], "in_use": in_use}
    return {"features": features, "note": "Burst compute cannot mint farm features."}


def drain_licenses(feature: str) -> dict[str, Any]:
    state = store.load()
    if feature not in state["licenses"]:
        err = errors.HeliosError(
            code="VALIDATION",
            message=f"Unknown feature {feature}. Use analog_sim or place_route.",
            exit_code=2,
            http_status=400,
        )
        raise err
    state["licenses"][feature]["drained"] = True
    state["licenses"][feature]["in_use"] = state["licenses"][feature]["total"]
    store.save(state)
    return {"feature": feature, "drained": True, **admin_licenses()}


def inject_nfs_stale(job_id: str) -> dict[str, Any]:
    state = store.load()
    job = state["jobs"].get(job_id)
    if not job:
        raise errors.NOT_FOUND
    job["nfs_stale"] = True
    store.save(state)
    return {"job_id": job_id, "nfs_stale": True}


def _project(state: dict[str, Any], slug: str) -> dict[str, Any]:
    project = state["projects"].get(slug)
    if not project:
        raise errors.HeliosError(
            code="VALIDATION",
            message=f"Unknown project {slug}. Use demo or analog-ip.",
            exit_code=2,
            http_status=400,
        )
    return project


def _validate_submit(
    project: str, job_class: str, image: str, pin: str, input_path: str
) -> str:
    if job_class not in CLASS_FEATURE:
        raise errors.HeliosError(
            code="VALIDATION",
            message="class must be sim or pnr.",
            exit_code=2,
            http_status=400,
        )
    if pin not in ALLOWED_PINS:
        raise errors.HeliosError(
            code="VALIDATION",
            message="pin must be farm or burst.",
            exit_code=2,
            http_status=400,
        )
    family = CLASS_IMAGE_FAMILY[job_class]
    if not image.startswith(family):
        raise errors.HeliosError(
            code="VALIDATION",
            message=f"image {image} is not allow-listed for class {job_class}.",
            exit_code=2,
            http_status=400,
        )
    if not input_path:
        raise errors.HeliosError(
            code="VALIDATION",
            message="input path is required.",
            exit_code=2,
            http_status=400,
        )
    return CLASS_FEATURE[job_class]


def _seat_available(pool: dict[str, Any]) -> bool:
    if pool.get("drained"):
        return False
    return pool.get("in_use", 0) < pool["total"]


def _active_count(state: dict[str, Any], project: str) -> int:
    return sum(
        1
        for job in state["jobs"].values()
        if job["project"] == project and job["state"] in ACTIVE_STATES
    )


def _write_artifact(job: dict[str, Any]) -> str:
    job_dir = store.artifacts_root() / job["job_id"]
    job_dir.mkdir(parents=True, exist_ok=True)
    log_path = job_dir / "smoke.log"
    log_path.write_text(
        (
            f"Helios artifact log rev={job['rev']}\n"
            f"job_id={job['job_id']}\n"
            f"placement={job['placement']}\n"
            f"feature={job['feature']}\n"
            f"image={job['image']}\n"
            f"input={job['input']}\n"
            f"project={job['project']}\n"
        ),
        encoding="utf-8",
    )
    job["artifacts"] = ["smoke.log"]
    return str(log_path)


def submit_job(
    *,
    project: str,
    job_class: str,
    image: str,
    pin: str,
    input_path: str,
    fail_if_queued: bool = False,
) -> dict[str, Any]:
    require_identity()
    state = store.load()
    project_meta = _project(state, project)
    feature = _validate_submit(project, job_class, image, pin, input_path)

    if pin == "burst" and project_meta["data_class"] == "classified":
        raise errors.REGION_PIN

    if _active_count(state, project) >= project_meta["quota"]:
        raise errors.QUOTA_EXCEEDED

    pool = state["licenses"][feature]
    job_id = _job_id()
    job: dict[str, Any] = {
        "job_id": job_id,
        "project": project,
        "class": job_class,
        "image": image,
        "pin": pin,
        "placement": pin,
        "input": input_path,
        "feature": feature,
        "rev": state.get("rev", store.REV),
        "created_at": _now(),
        "nfs_stale": False,
        "reason": None,
        "state": "queued",
    }

    if not _seat_available(pool):
        if fail_if_queued:
            raise errors.LICENSE_EXHAUSTED
        job["state"] = "queued"
        job["reason"] = "LICENSE_EXHAUSTED"
        state["jobs"][job_id] = job
        store.save(state)
        return dict(job)

    pool["in_use"] = pool.get("in_use", 0) + 1
    job["state"] = "running"
    job["reason"] = None
    _write_artifact(job)
    pool["in_use"] = max(0, pool["in_use"] - 1)
    job["state"] = "succeeded"
    job["finished_at"] = _now()
    state["jobs"][job_id] = job
    store.save(state)
    return dict(job)


def get_job(job_id: str) -> dict[str, Any]:
    state = store.load()
    job = state["jobs"].get(job_id)
    if not job:
        raise errors.NOT_FOUND
    return dict(job)


def wait_job(job_id: str) -> dict[str, Any]:
    """Promote a license-wait job if a seat exists; otherwise return current state."""
    state = store.load()
    job = state["jobs"].get(job_id)
    if not job:
        raise errors.NOT_FOUND
    if job["state"] in {"succeeded", "failed"}:
        return dict(job)
    pool = state["licenses"][job["feature"]]
    if job["state"] == "queued" and job.get("reason") == "LICENSE_EXHAUSTED":
        if _seat_available(pool):
            pool["in_use"] = pool.get("in_use", 0) + 1
            job["state"] = "running"
            job["reason"] = None
            _write_artifact(job)
            pool["in_use"] = max(0, pool["in_use"] - 1)
            job["state"] = "succeeded"
            job["finished_at"] = _now()
            store.save(state)
    return dict(job)


def job_artifacts(job_id: str, out_dir: str | None = None) -> dict[str, Any]:
    state = store.load()
    job = state["jobs"].get(job_id)
    if not job:
        raise errors.NOT_FOUND
    if job.get("nfs_stale"):
        raise errors.NFS_STALE
    if job["state"] != "succeeded":
        raise errors.HeliosError(
            code="VALIDATION",
            message="Use artifacts only after a terminal success.",
            exit_code=2,
            http_status=409,
        )
    src_dir = store.artifacts_root() / job_id
    written: list[str] = []
    if out_dir:
        dest = Path(out_dir)
        dest.mkdir(parents=True, exist_ok=True)
        for name in job.get("artifacts", []):
            src = src_dir / name
            target = dest / name
            target.write_bytes(src.read_bytes())
            written.append(str(target))
    manifest = {
        "job_id": job_id,
        "files": job.get("artifacts", []),
        "written": written,
        "volume": "farm",
    }
    return manifest
