"""UNIX-style Helios CLI. Exit codes match the failure catalog."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from helios import __version__, errors, fabric


def _print_json(payload: Any, stream=None) -> None:
    if stream is None:
        stream = sys.stdout
    json.dump(payload, stream, indent=2, sort_keys=True)
    stream.write("\n")


def _fail(exc: errors.HeliosError) -> int:
    _print_json(exc.to_dict(), stream=sys.stderr)
    return exc.exit_code


def cmd_whoami(_args: argparse.Namespace) -> int:
    fabric.require_identity()
    _print_json(fabric.whoami())
    return 0


def cmd_job_submit(args: argparse.Namespace) -> int:
    try:
        job = fabric.submit_job(
            project=args.project,
            job_class=args.job_class,
            image=args.image,
            pin=args.pin,
            input_path=args.input,
            fail_if_queued=args.fail_if_queued,
        )
    except errors.HeliosError as exc:
        return _fail(exc)
    _print_json(job)
    return 0


def cmd_job_get(args: argparse.Namespace) -> int:
    try:
        _print_json(fabric.get_job(args.job_id))
    except errors.HeliosError as exc:
        return _fail(exc)
    return 0


def cmd_job_wait(args: argparse.Namespace) -> int:
    try:
        _print_json(fabric.wait_job(args.job_id))
    except errors.HeliosError as exc:
        return _fail(exc)
    return 0


def cmd_job_artifacts(args: argparse.Namespace) -> int:
    try:
        _print_json(fabric.job_artifacts(args.job_id, args.out))
    except errors.HeliosError as exc:
        return _fail(exc)
    return 0


def cmd_admin_status(args: argparse.Namespace) -> int:
    _print_json(fabric.admin_status(verbose=args.verbose))
    return 0


def cmd_admin_licenses(_args: argparse.Namespace) -> int:
    _print_json(fabric.admin_licenses())
    return 0


def cmd_admin_drain(args: argparse.Namespace) -> int:
    try:
        _print_json(fabric.drain_licenses(args.feature))
    except errors.HeliosError as exc:
        return _fail(exc)
    return 0


def cmd_admin_nfs(args: argparse.Namespace) -> int:
    try:
        _print_json(fabric.inject_nfs_stale(args.job_id))
    except errors.HeliosError as exc:
        return _fail(exc)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="helios",
        description="Helios hybrid EDA job fabric CLI (rev 1.1).",
    )
    parser.add_argument("--version", action="version", version=f"helios {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    whoami = sub.add_parser("whoami", help="Show identity, default project, endpoint, rev.")
    whoami.set_defaults(func=cmd_whoami)

    job = sub.add_parser("job", help="Submit, inspect, wait, and fetch jobs.")
    job_sub = job.add_subparsers(dest="job_command", required=True)

    submit = job_sub.add_parser("submit", help="Submit a sim or pnr job.")
    submit.add_argument("--project", required=True)
    submit.add_argument("--class", dest="job_class", required=True, choices=["sim", "pnr"])
    submit.add_argument("--image", required=True)
    submit.add_argument("--pin", required=True, choices=["farm", "burst"])
    submit.add_argument("--input", required=True)
    submit.add_argument(
        "--fail-if-queued",
        action="store_true",
        help="Exit 32 if the feature pool is empty.",
    )
    submit.set_defaults(func=cmd_job_submit)

    get_p = job_sub.add_parser("get", help="Get job status and placement.")
    get_p.add_argument("job_id")
    get_p.set_defaults(func=cmd_job_get)

    wait_p = job_sub.add_parser("wait", help="Wait until the job is terminal when a seat exists.")
    wait_p.add_argument("job_id")
    wait_p.set_defaults(func=cmd_job_wait)

    art = job_sub.add_parser("artifacts", help="Fetch artifacts from the farm volume.")
    art.add_argument("job_id")
    art.add_argument("--out", required=True)
    art.set_defaults(func=cmd_job_artifacts)

    admin = sub.add_parser("admin", help="Farm health, licenses, and slice injectors.")
    admin_sub = admin.add_subparsers(dest="admin_command", required=True)

    status = admin_sub.add_parser("status", help="Scheduler status and queue depth.")
    status.add_argument("--verbose", action="store_true")
    status.set_defaults(func=cmd_admin_status)

    licenses = admin_sub.add_parser("licenses", help="Farm feature in_use versus total.")
    licenses.set_defaults(func=cmd_admin_licenses)

    drain = admin_sub.add_parser(
        "drain-licenses",
        help="Slice only: drain a farm feature so writers can validate LICENSE_EXHAUSTED.",
    )
    drain.add_argument("--feature", required=True)
    drain.set_defaults(func=cmd_admin_drain)

    nfs = admin_sub.add_parser(
        "inject-nfs-stale",
        help="Slice only: mark a job so artifact fetch returns NFS_STALE (exit 41).",
    )
    nfs.add_argument("job_id")
    nfs.set_defaults(func=cmd_admin_nfs)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
