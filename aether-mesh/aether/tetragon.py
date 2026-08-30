"""Tetragon-style tracing policies and runtime enforcement."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from aether import errors, store


def load_yaml(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise errors.AetherError(
            code="VALIDATION",
            message="TracingPolicy must be a YAML mapping.",
            exit_code=2,
            http_status=400,
        )
    return data


def compile_tracing(doc: dict[str, Any]) -> dict[str, Any]:
    if doc.get("kind") != "TracingPolicy":
        raise errors.AetherError(
            code="VALIDATION",
            message="kind must be TracingPolicy.",
            exit_code=2,
            http_status=400,
        )
    spec = doc.get("spec") or {}
    probes = []
    for probe in spec.get("kprobes") or []:
        selectors = []
        for selector in probe.get("selectors") or []:
            binaries = []
            for match in selector.get("matchBinaries") or []:
                binaries.extend(match.get("values") or [])
            namespaces = []
            for match in selector.get("matchNamespaces") or []:
                namespaces.extend(match.get("values") or [])
            apps = []
            for match in selector.get("matchLabels") or []:
                if "app" in (match if isinstance(match, dict) else {}):
                    apps.append(match["app"])
            labels = selector.get("matchPodLabels") or {}
            actions = [a.get("action") for a in selector.get("matchActions") or []]
            selectors.append(
                {
                    "binaries": binaries,
                    "namespaces": namespaces,
                    "pod_labels": labels,
                    "actions": actions or ["Observe"],
                }
            )
        probes.append({"call": probe.get("call"), "selectors": selectors})
    return {
        "name": (doc.get("metadata") or {}).get("name", "unnamed"),
        "kprobes": probes,
        "kind": "TracingPolicy",
    }


def apply_policy(doc: dict[str, Any]) -> dict[str, Any]:
    compiled = compile_tracing(doc)
    state = store.read_json("tetragon.json", {"policies": []})
    state["policies"] = [p for p in state["policies"] if p["name"] != compiled["name"]]
    state["policies"].append(compiled)
    store.write_json("tetragon.json", state)
    return compiled


def _selector_hit(event: dict[str, Any], selector: dict[str, Any]) -> bool:
    binary = event.get("binary") or event.get("process", {}).get("binary")
    labels = event.get("pod_labels") or {}
    namespace = event.get("namespace", "shop")
    if selector["binaries"] and binary not in selector["binaries"]:
        return False
    if selector["namespaces"] and namespace not in selector["namespaces"]:
        return False
    for key, value in (selector.get("pod_labels") or {}).items():
        if labels.get(key) != value:
            return False
    return True


def evaluate_event(event: dict[str, Any]) -> dict[str, Any]:
    state = store.read_json("tetragon.json", {"policies": []})
    result = dict(event)
    result["action"] = "Observe"
    result["matched_policy"] = None
    for policy in state.get("policies") or []:
        for probe in policy["kprobes"]:
            call = event.get("call") or event.get("syscall")
            if probe["call"] and call != probe["call"]:
                continue
            for selector in probe["selectors"]:
                if _selector_hit(event, selector):
                    action = selector["actions"][0]
                    result["action"] = action
                    result["matched_policy"] = policy["name"]
                    result["enforced"] = action in {"Sigkill", "Deny", "Override"}
                    store.append_jsonl("events.jsonl", result)
                    return result
    result["enforced"] = False
    store.append_jsonl("events.jsonl", result)
    return result


def load_events(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def replay_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    observed = [evaluate_event(event) for event in events]
    killed = [row for row in observed if row.get("enforced")]
    return {
        "events": len(observed),
        "enforced": len(killed),
        "observed": observed,
    }


def list_events() -> list[dict[str, Any]]:
    return store.read_jsonl("events.jsonl")
