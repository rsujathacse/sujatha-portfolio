"""Canonical Aether Mesh error codes. Same meaning in CLI, API, and docs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AetherError(Exception):
    code: str
    message: str
    exit_code: int
    http_status: int
    retry_after: int | None = None

    def to_dict(self) -> dict:
        body = {"code": self.code, "message": self.message}
        if self.retry_after is not None:
            body["retry_after"] = self.retry_after
        return body


def identity_collision() -> AetherError:
    return AetherError(
        code="IDENTITY_COLLISION",
        message=(
            "Two clusters share a cluster-id. Numeric security identities collide "
            "and ClusterMesh policy is unsafe. Restore unique cluster-ids before "
            "promoting policy."
        ),
        exit_code=35,
        http_status=409,
    )


def shadow_failed(detail: str) -> AetherError:
    return AetherError(
        code="POLICY_SHADOW_FAILED",
        message=(
            "Shadow dataplane rejected the bundle against golden Hubble flows. "
            + detail
        ),
        exit_code=36,
        http_status=409,
    )


def not_qualified(name: str) -> AetherError:
    return AetherError(
        code="POLICY_NOT_QUALIFIED",
        message=(
            f"Bundle {name!r} has no passing shadow qualification. "
            "Run `aether policy shadow` and promote only a qualified bundle."
        ),
        exit_code=37,
        http_status=409,
    )


def mesh_unhealthy(detail: str) -> AetherError:
    return AetherError(
        code="CLUSTERMESH_KVSTORE",
        message="ClusterMesh control plane is not ready. " + detail,
        exit_code=38,
        http_status=503,
        retry_after=15,
    )


NOT_FOUND = AetherError(
    code="NOT_FOUND",
    message="Object not found.",
    exit_code=2,
    http_status=404,
)

VALIDATION = AetherError(
    code="VALIDATION",
    message="Request failed validation.",
    exit_code=2,
    http_status=400,
)

UNAUTHORIZED = AetherError(
    code="UNAUTHORIZED",
    message="Bearer token required.",
    exit_code=3,
    http_status=401,
)
