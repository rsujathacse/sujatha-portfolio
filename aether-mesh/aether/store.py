"""JSON file store under AETHER_HOME."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def home() -> Path:
    raw = os.environ.get("AETHER_HOME")
    if raw:
        return Path(raw)
    return Path.cwd() / ".aether"


def path(*parts: str) -> Path:
    dest = home().joinpath(*parts)
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


def read_json(name: str, default: Any) -> Any:
    file = path(name)
    if not file.exists():
        return default
    return json.loads(file.read_text(encoding="utf-8"))


def write_json(name: str, payload: Any) -> None:
    file = path(name)
    file.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(name: str, row: dict[str, Any]) -> None:
    file = path(name)
    with file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def read_jsonl(name: str) -> list[dict[str, Any]]:
    file = path(name)
    if not file.exists():
        return []
    rows = []
    for line in file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows
