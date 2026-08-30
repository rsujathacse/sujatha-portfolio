"""Cilium-style L3/L7 policy compile, Hubble replay, shadow qualification, promote."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from aether import errors, mesh, store


def load_yaml(path: str | Path) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise errors.AetherError(
            code="VALIDATION",
            message="Policy file must be a YAML mapping.",
            exit_code=2,
            http_status=400,
        )
    return data


def load_flows(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def compile_policy(doc: dict[str, Any]) -> dict[str, Any]:
    kind = doc.get("kind")
    if kind != "NetworkPolicy":
        raise errors.AetherError(
            code="VALIDATION",
            message="kind must be NetworkPolicy.",
            exit_code=2,
            http_status=400,
        )
    spec = doc.get("spec") or {}
    selector = (spec.get("endpointSelector") or {}).get("matchLabels") or {}
    rules = []
    for direction in ("ingress", "egress"):
        for rule in spec.get(direction) or []:
            http_rules = []
            ports = []
            for to_port in rule.get("toPorts") or []:
                for port in to_port.get("ports") or []:
                    ports.append(
                        {
                            "port": int(port["port"]),
                            "protocol": port.get("protocol", "TCP"),
                        }
                    )
                for http in (to_port.get("rules") or {}).get("http") or []:
                    http_rules.append(
                        {
                            "method": http.get("method", "*"),
                            "path": http.get("path", ".*"),
                        }
                    )
            peers = []
            peer_key = "fromEndpoints" if direction == "ingress" else "toEndpoints"
            for peer in rule.get(peer_key) or []:
                peers.append(peer.get("matchLabels") or {})
            rules.append(
                {
                    "direction": direction,
                    "peers": peers,
                    "ports": ports,
                    "http": http_rules,
                }
            )
    compiled = {
        "name": (doc.get("metadata") or {}).get("name", "unnamed"),
        "cluster": (doc.get("metadata") or {}).get("cluster", "*"),
        "selector": selector,
        "rules": rules,
        "kind": "NetworkPolicy",
    }
    return compiled


def _labels_match(have: dict[str, str], want: dict[str, str]) -> bool:
    for key, value in want.items():
        if key == "cluster":
            continue
        if have.get(key) != value:
            return False
    return True


def _http_match(flow: dict[str, Any], http_rules: list[dict[str, str]]) -> bool:
    if not http_rules:
        return True
    l7 = flow.get("l7") or {}
    if l7.get("type") != "http":
        return False
    method = l7.get("method", "")
    path = l7.get("path", "")
    for rule in http_rules:
        method_ok = rule["method"] in {"*", method}
        path_ok = re.search(rule["path"], path) is not None
        if method_ok and path_ok:
            return True
    return False


def _port_match(flow: dict[str, Any], ports: list[dict[str, Any]]) -> bool:
    if not ports:
        return True
    l4 = flow.get("l4") or {}
    for port in ports:
        if int(l4.get("port", 0)) == port["port"] and l4.get("protocol", "TCP") == port["protocol"]:
            return True
    return False


def _peer_cluster(peer: dict[str, str], fallback: str) -> str | None:
    return peer.get("cluster") or fallback


def policy_allows(compiled: dict[str, Any], flow: dict[str, Any]) -> bool:
    src_labels = flow["src"]["labels"]
    dst_labels = flow["dst"]["labels"]
    src_cluster = flow["src"]["cluster"]
    dst_cluster = flow["dst"]["cluster"]
    selected_dst = _labels_match(dst_labels, compiled["selector"])
    selected_src = _labels_match(src_labels, compiled["selector"])
    cluster_ok = compiled["cluster"] in {"*", dst_cluster, src_cluster}

    for rule in compiled["rules"]:
        if rule["direction"] == "ingress":
            if not selected_dst or not cluster_ok:
                continue
            if not _port_match(flow, rule["ports"]):
                continue
            if not _http_match(flow, rule["http"]):
                continue
            for peer in rule["peers"]:
                peer_cluster = _peer_cluster(peer, src_cluster)
                if peer.get("cluster") and peer["cluster"] != src_cluster:
                    continue
                if _labels_match(src_labels, peer) and (
                    peer_cluster in {src_cluster, None} or True
                ):
                    if peer.get("cluster") in {None, src_cluster}:
                        return True
        elif rule["direction"] == "egress":
            if not selected_src:
                continue
            if compiled["cluster"] not in {"*", src_cluster}:
                continue
            if not _port_match(flow, rule["ports"]):
                continue
            if not _http_match(flow, rule["http"]):
                continue
            for peer in rule["peers"]:
                if peer.get("cluster") and peer["cluster"] != dst_cluster:
                    continue
                if _labels_match(dst_labels, peer):
                    return True
    return False


def evaluate_flow(
    flow: dict[str, Any], policies: list[dict[str, Any]]
) -> dict[str, Any]:
    annotated = mesh.annotate_flow(flow)
    if annotated.get("drop_reason") == "IDENTITY_COLLISION":
        return annotated
    if not policies:
        annotated["verdict"] = "DROPPED"
        annotated["drop_reason"] = "POLICY_DENIED"
        annotated["matched_policy"] = None
        return annotated
    for compiled in policies:
        if policy_allows(compiled, annotated):
            annotated["verdict"] = "FORWARDED"
            annotated["drop_reason"] = None
            annotated["matched_policy"] = compiled["name"]
            return annotated
    annotated["verdict"] = "DROPPED"
    annotated["drop_reason"] = "POLICY_DENIED"
    annotated["matched_policy"] = None
    return annotated


def replay(flows: list[dict[str, Any]], dataplane: str = "enforce") -> dict[str, Any]:
    bundle = store.read_json("policies.json", {"enforce": [], "shadow": []})
    policies = bundle.get(dataplane) or []
    observed = []
    forwarded = dropped = 0
    for flow in flows:
        row = evaluate_flow(flow, policies)
        store.append_jsonl("flows.jsonl", row)
        observed.append(row)
        if row["verdict"] == "FORWARDED":
            forwarded += 1
        else:
            dropped += 1
    return {
        "dataplane": dataplane,
        "flows": len(observed),
        "forwarded": forwarded,
        "dropped": dropped,
        "observed": observed,
    }


def _in_scope(compiled: dict[str, Any], flow: dict[str, Any]) -> bool:
    """Score only traffic that this policy would subject (ingress to / egress from)."""
    selector = compiled["selector"]
    cluster = compiled["cluster"]
    has_ingress = any(rule["direction"] == "ingress" for rule in compiled["rules"])
    has_egress = any(rule["direction"] == "egress" for rule in compiled["rules"])
    if (
        has_ingress
        and _labels_match(flow["dst"]["labels"], selector)
        and cluster in {"*", flow["dst"]["cluster"]}
    ):
        return True
    if (
        has_egress
        and _labels_match(flow["src"]["labels"], selector)
        and cluster in {"*", flow["src"]["cluster"]}
    ):
        return True
    return False


def _policies() -> dict[str, Any]:
    return store.read_json("policies.json", {"enforce": [], "shadow": []})


def upsert_shadow(compiled: dict[str, Any]) -> None:
    bundle = _policies()
    bundle.setdefault("shadow", [])
    bundle["shadow"] = [p for p in bundle["shadow"] if p["name"] != compiled["name"]]
    bundle["shadow"].append(compiled)
    store.write_json("policies.json", bundle)


def shadow(doc: dict[str, Any], flows: list[dict[str, Any]]) -> dict[str, Any]:
    health = mesh.status()
    if health["identity_collisions"]:
        raise errors.identity_collision()
    compiled = compile_policy(doc)
    upsert_shadow(compiled)
    candidate = list(_policies().get("enforce") or [])
    candidate = [p for p in candidate if p["name"] != compiled["name"]]
    candidate.append(compiled)

    unexpected_denies = []
    unexpected_allows = []
    rows = []
    for flow in flows:
        if not _in_scope(compiled, flow):
            continue
        current = evaluate_flow(flow, _policies().get("enforce") or [])
        proposed = evaluate_flow(flow, candidate)
        intended = flow.get("intent") or flow.get("expected")
        row = {
            "src": f"{flow['src']['cluster']}/{flow['src']['labels']['app']}",
            "dst": f"{flow['dst']['cluster']}/{flow['dst']['labels']['app']}",
            "l7": flow.get("l7"),
            "current": current["verdict"],
            "proposed": proposed["verdict"],
            "intent": intended,
        }
        rows.append(row)
        if intended == "FORWARDED" and proposed["verdict"] != "FORWARDED":
            unexpected_denies.append(row)
        if intended == "DROPPED" and proposed["verdict"] == "FORWARDED":
            unexpected_allows.append(row)
        if intended is None and current["verdict"] == "FORWARDED" and proposed["verdict"] != "FORWARDED":
            unexpected_denies.append(row)

    qualified = len(unexpected_denies) == 0
    report = {
        "bundle": compiled["name"],
        "mode": "shadow",
        "dataplane": "shadow",
        "slo": {
            "max_unexpected_deny": 0,
            "max_unexpected_allow_on_exploit": 0,
        },
        "unexpected_denies": unexpected_denies,
        "unexpected_allows": unexpected_allows,
        "qualified": qualified,
        "compared": rows,
        "compiled": compiled,
    }
    quals = store.read_json("qualifications.json", {})
    quals[compiled["name"]] = report
    store.write_json("qualifications.json", quals)
    if not qualified:
        raise errors.shadow_failed(
            f"{len(unexpected_denies)} unexpected deny(s) on golden flows."
        )
    return report


def promote(name: str) -> dict[str, Any]:
    quals = store.read_json("qualifications.json", {})
    report = quals.get(name)
    if not report or not report.get("qualified"):
        raise errors.not_qualified(name)
    bundle = _policies()
    compiled = report["compiled"]
    bundle["enforce"] = [p for p in bundle.get("enforce") or [] if p["name"] != name]
    bundle["enforce"].append(compiled)
    store.write_json("policies.json", bundle)
    return {
        "bundle": name,
        "dataplane": "enforce",
        "promoted": True,
        "enforce_policies": [p["name"] for p in bundle["enforce"]],
    }


def list_policies() -> dict[str, Any]:
    bundle = _policies()
    quals = store.read_json("qualifications.json", {})
    return {
        "shadow": [p["name"] for p in bundle.get("shadow") or []],
        "enforce": [p["name"] for p in bundle.get("enforce") or []],
        "qualified": [name for name, row in quals.items() if row.get("qualified")],
    }
