"""ClusterMesh identity plane, Hubble-style flows, and mesh health."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from aether import REV, errors, store

def _wl(cluster: str, pod: str, app: str, tier: str, ip: str) -> dict[str, Any]:
    return {
        "cluster": cluster,
        "namespace": "shop",
        "pod": pod,
        "ip": ip,
        "labels": {"app": app, "tier": tier, "k8s:io.kubernetes.pod.namespace": "shop"},
    }


DEFAULT_CLUSTERS = [
    {
        "name": "prod-us",
        "id": 1,
        "cidr": "10.1.0.0/16",
        "region": "us-west",
        "kvstore": "ready",
    },
    {
        "name": "prod-eu",
        "id": 2,
        "cidr": "10.2.0.0/16",
        "region": "eu-central",
        "kvstore": "ready",
    },
    {
        "name": "prod-ap",
        "id": 3,
        "cidr": "10.3.0.0/16",
        "region": "ap-south",
        "kvstore": "ready",
    },
]

DEFAULT_WORKLOADS = [
    _wl("prod-us", "frontend-0", "frontend", "edge", "10.1.1.10"),
    _wl("prod-us", "checkout-0", "checkout", "svc", "10.1.2.20"),
    _wl("prod-eu", "payments-0", "payments", "pci", "10.2.3.30"),
    _wl("prod-ap", "inventory-0", "inventory", "data", "10.3.4.40"),
    _wl("prod-ap", "frontend-ap-0", "frontend", "edge", "10.3.1.11"),
    _wl("prod-eu", "debug-0", "debug", "ops", "10.2.9.9"),
]


def require_identity() -> None:
    token = __import__("os").environ.get("AETHER_TOKEN", "slice-token")
    allow_anon = __import__("os").environ.get("AETHER_ALLOW_ANON", "1")
    if allow_anon == "1":
        return
    if not token:
        raise errors.UNAUTHORIZED


def whoami() -> dict[str, Any]:
    require_identity()
    return {
        "identity": "platform-sre",
        "endpoint": "clustermesh",
        "rev": REV,
        "default_mesh": "shop-prod",
        "dataplanes": ["shadow", "enforce"],
    }


def bootstrap() -> dict[str, Any]:
    mesh = {
        "name": "shop-prod",
        "encryption": "wireguard",
        "kube_proxy_replacement": True,
        "default_deny": True,
        "clusters": [dict(c) for c in DEFAULT_CLUSTERS],
        "workloads": [dict(w) for w in DEFAULT_WORKLOADS],
    }
    store.write_json("mesh.json", mesh)
    store.write_json("policies.json", {"enforce": [], "shadow": []})
    store.write_json("qualifications.json", {})
    store.write_json("tetragon.json", {"policies": []})
    store.path("flows.jsonl").write_text("", encoding="utf-8")
    store.path("events.jsonl").write_text("", encoding="utf-8")
    return status()


def _mesh() -> dict[str, Any]:
    mesh = store.read_json("mesh.json", None)
    if mesh is None:
        return bootstrap()
    return store.read_json("mesh.json", {})


def cluster_by_name(name: str) -> dict[str, Any]:
    for cluster in _mesh()["clusters"]:
        if cluster["name"] == name:
            return cluster
    raise errors.AetherError(
        code="NOT_FOUND",
        message=f"Cluster {name!r} is not in the mesh.",
        exit_code=2,
        http_status=404,
    )


def numeric_identity(cluster_name: str, namespace: str, labels: dict[str, str]) -> int:
    cluster = cluster_by_name(cluster_name)
    app = labels.get("app", "")
    key = f"{cluster['id']}:{namespace}:app={app}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return 10000 + (int(digest[:8], 16) % 50000)


def identity_index() -> list[dict[str, Any]]:
    mesh = _mesh()
    rows = []
    seen: dict[int, dict[str, Any]] = {}
    collisions = []
    for workload in mesh["workloads"]:
        ident = numeric_identity(
            workload["cluster"], workload["namespace"], workload["labels"]
        )
        row = {
            "id": ident,
            "cluster": workload["cluster"],
            "cluster_id": cluster_by_name(workload["cluster"])["id"],
            "namespace": workload["namespace"],
            "pod": workload["pod"],
            "app": workload["labels"]["app"],
            "ip": workload["ip"],
            "labels": workload["labels"],
        }
        if ident in seen and seen[ident]["cluster"] != workload["cluster"]:
            row["collision"] = True
            collisions.append({"id": ident, "left": seen[ident], "right": row})
            seen[ident]["collision"] = True
        else:
            row["collision"] = False
            seen[ident] = row
        rows.append(row)
    return rows


def collision_report() -> list[dict[str, Any]]:
    hits = [row for row in identity_index() if row.get("collision")]
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in hits:
        grouped.setdefault(row["id"], []).append(row)
    return [{"id": ident, "endpoints": eps} for ident, eps in grouped.items()]


def status() -> dict[str, Any]:
    mesh = _mesh()
    ids = [c["id"] for c in mesh["clusters"]]
    unique = len(ids) == len(set(ids))
    kv = all(c.get("kvstore") == "ready" for c in mesh["clusters"])
    collisions = collision_report()
    healthy = unique and kv and not collisions
    return {
        "mesh": mesh["name"],
        "rev": REV,
        "encryption": mesh["encryption"],
        "kube_proxy_replacement": mesh["kube_proxy_replacement"],
        "default_deny": mesh["default_deny"],
        "clusters": mesh["clusters"],
        "workloads": len(mesh["workloads"]),
        "unique_cluster_ids": unique,
        "kvstore": "ready" if kv else "degraded",
        "identity_collisions": collisions,
        "healthy": healthy,
        "dataplane": {
            "shadow": "active",
            "enforce": "active",
        },
    }


def inject_identity_collision() -> dict[str, Any]:
    mesh = _mesh()
    for cluster in mesh["clusters"]:
        if cluster["name"] == "prod-ap":
            cluster["id"] = 1
    store.write_json("mesh.json", mesh)
    report = collision_report()
    if not report:
        raise errors.mesh_unhealthy("Collision injector did not produce a colliding identity.")
    raise errors.identity_collision()


def resolve_endpoint(cluster: str, app: str) -> dict[str, Any]:
    for workload in _mesh()["workloads"]:
        if workload["cluster"] == cluster and workload["labels"]["app"] == app:
            ident = numeric_identity(
                workload["cluster"], workload["namespace"], workload["labels"]
            )
            return {**workload, "id": ident}
    raise errors.AetherError(
        code="NOT_FOUND",
        message=f"No endpoint app={app} in cluster {cluster}.",
        exit_code=2,
        http_status=404,
    )


def annotate_flow(flow: dict[str, Any]) -> dict[str, Any]:
    src = flow["src"]
    dst = flow["dst"]
    annotated = json.loads(json.dumps(flow))
    annotated["src"]["id"] = numeric_identity(src["cluster"], src["namespace"], src["labels"])
    annotated["dst"]["id"] = numeric_identity(dst["cluster"], dst["namespace"], dst["labels"])
    collisions = {item["id"] for item in collision_report()}
    if annotated["src"]["id"] in collisions or annotated["dst"]["id"] in collisions:
        annotated["verdict"] = "DROPPED"
        annotated["drop_reason"] = "IDENTITY_COLLISION"
    return annotated
