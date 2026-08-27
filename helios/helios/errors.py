"""Canonical Helios error codes. Same meaning in CLI, API, and docs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HeliosError(Exception):
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


LICENSE_EXHAUSTED = HeliosError(
    code="LICENSE_EXHAUSTED",
    message=(
        "No farm seat for analog_sim or place_route. Wait or page ECS with "
        "the feature name and job ids. Burst will not create a seat."
    ),
    exit_code=32,
    http_status=429,
    retry_after=30,
)

QUOTA_EXCEEDED = HeliosError(
    code="QUOTA_EXCEEDED",
    message="Project or user concurrency cap reached. Ask the project owner.",
    exit_code=33,
    http_status=429,
    retry_after=15,
)

REGION_PIN = HeliosError(
    code="REGION_PIN",
    message="Pin or data class forbids this placement. Fix pin or pipeline.",
    exit_code=34,
    http_status=403,
)

NFS_STALE = HeliosError(
    code="NFS_STALE",
    message=(
        "Artifact volume handle is stale. Retry once after 30 seconds. "
        "Then page storage on-call with the job id only."
    ),
    exit_code=41,
    http_status=503,
)

NOT_FOUND = HeliosError(
    code="NOT_FOUND",
    message="Job not found.",
    exit_code=2,
    http_status=404,
)

VALIDATION = HeliosError(
    code="VALIDATION",
    message="Request failed validation.",
    exit_code=2,
    http_status=400,
)
