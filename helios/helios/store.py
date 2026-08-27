"""JSON file state for the local Helios slice."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

REV = "1.1"

DEFAULT_STATE: dict[str, Any] = {
    "rev": REV,
    "scheduler": {"status": "healthy"},
    "identity": {
        "user": "designer@farm.helios",
        "default_project": "demo",
        "endpoint": "farm",
        "rev": REV,
    },
    "projects": {
        "demo": {"data_class": "internal", "quota": 4},
        "analog-ip": {"data_class": "classified", "quota": 2},
    },
    "licenses": {
        "analog_sim": {"total": 2, "in_use": 0, "drained": False},
        "place_route": {"total": 1, "in_use": 0, "drained": False},
    },
    "jobs": {},
}


def home_dir() -> Path:
    override = os.environ.get("HELIOS_HOME")
    if override:
        return Path(override)
    return Path.cwd() / ".helios"


def state_path() -> Path:
    return home_dir() / "state.json"


def artifacts_root() -> Path:
    return home_dir() / "artifacts"


def load() -> dict[str, Any]:
    path = state_path()
    if not path.exists():
        save(DEFAULT_STATE)
        return json.loads(json.dumps(DEFAULT_STATE))
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return data


def save(state: dict[str, Any]) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    tmp.replace(path)
