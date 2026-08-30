"""UNIX-style Aether Mesh CLI. Exit codes match the failure catalog."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from aether import errors, mesh, policy, tetragon


def _print_json(payload: Any, stream=None) -> None:
    if stream is None:
        stream = sys.stdout
    json.dump(payload, stream, indent=2, sort_keys=True)
    stream.write("\n")


def _fail(exc: errors.AetherError) -> int:
    _print_json(exc.to_dict(), stream=sys.stderr)
    return exc.exit_code


def cmd_whoami(_args: argparse.Namespace) -> int:
    mesh.require_identity()
    _print_json(mesh.whoami())
    return 0


def cmd_mesh_bootstrap(_args: argparse.Namespace) -> int:
    _print_json(mesh.bootstrap())
    return 0


def cmd_mesh_status(_args: argparse.Namespace) -> int:
    _print_json(mesh.status())
    return 0


def cmd_identity_list(_args: argparse.Namespace) -> int:
    _print_json({"identities": mesh.identity_index()})
    return 0


def cmd_flow_replay(args: argparse.Namespace) -> int:
    try:
        flows = policy.load_flows(args.file)
        _print_json(policy.replay(flows, dataplane=args.dataplane))
    except errors.AetherError as exc:
        return _fail(exc)
    return 0


def cmd_policy_compile(args: argparse.Namespace) -> int:
    try:
        doc = policy.load_yaml(args.file)
        _print_json(policy.compile_policy(doc))
    except errors.AetherError as exc:
        return _fail(exc)
    return 0


def cmd_policy_shadow(args: argparse.Namespace) -> int:
    try:
        doc = policy.load_yaml(args.file)
        flows = policy.load_flows(args.flows)
        _print_json(policy.shadow(doc, flows))
    except errors.AetherError as exc:
        return _fail(exc)
    return 0


def cmd_policy_promote(args: argparse.Namespace) -> int:
    try:
        _print_json(policy.promote(args.name))
    except errors.AetherError as exc:
        return _fail(exc)
    return 0


def cmd_policy_list(_args: argparse.Namespace) -> int:
    _print_json(policy.list_policies())
    return 0


def cmd_tetragon_apply(args: argparse.Namespace) -> int:
    try:
        doc = tetragon.load_yaml(args.file)
        _print_json(tetragon.apply_policy(doc))
    except errors.AetherError as exc:
        return _fail(exc)
    return 0


def cmd_tetragon_replay(args: argparse.Namespace) -> int:
    try:
        events = tetragon.load_events(args.file)
        _print_json(tetragon.replay_events(events))
    except errors.AetherError as exc:
        return _fail(exc)
    return 0


def cmd_tetragon_events(_args: argparse.Namespace) -> int:
    _print_json({"events": tetragon.list_events()})
    return 0


def cmd_inject_collision(_args: argparse.Namespace) -> int:
    try:
        mesh.inject_identity_collision()
    except errors.AetherError as exc:
        return _fail(exc)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aether", description="Aether Mesh control plane")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("whoami").set_defaults(func=cmd_whoami)

    mesh_p = sub.add_parser("mesh")
    mesh_sub = mesh_p.add_subparsers(dest="mesh_cmd", required=True)
    mesh_sub.add_parser("bootstrap").set_defaults(func=cmd_mesh_bootstrap)
    mesh_sub.add_parser("status").set_defaults(func=cmd_mesh_status)

    ident = sub.add_parser("identity")
    ident_sub = ident.add_subparsers(dest="identity_cmd", required=True)
    ident_sub.add_parser("list").set_defaults(func=cmd_identity_list)

    flow = sub.add_parser("flow")
    flow_sub = flow.add_subparsers(dest="flow_cmd", required=True)
    replay = flow_sub.add_parser("replay")
    replay.add_argument("--file", required=True)
    replay.add_argument("--dataplane", default="enforce", choices=("enforce", "shadow"))
    replay.set_defaults(func=cmd_flow_replay)

    pol = sub.add_parser("policy")
    pol_sub = pol.add_subparsers(dest="policy_cmd", required=True)
    compile_p = pol_sub.add_parser("compile")
    compile_p.add_argument("--file", required=True)
    compile_p.set_defaults(func=cmd_policy_compile)
    shadow_p = pol_sub.add_parser("shadow")
    shadow_p.add_argument("--file", required=True)
    shadow_p.add_argument("--flows", required=True)
    shadow_p.set_defaults(func=cmd_policy_shadow)
    promote_p = pol_sub.add_parser("promote")
    promote_p.add_argument("--name", required=True)
    promote_p.set_defaults(func=cmd_policy_promote)
    pol_sub.add_parser("list").set_defaults(func=cmd_policy_list)

    tet = sub.add_parser("tetragon")
    tet_sub = tet.add_subparsers(dest="tetragon_cmd", required=True)
    apply_p = tet_sub.add_parser("apply")
    apply_p.add_argument("--file", required=True)
    apply_p.set_defaults(func=cmd_tetragon_apply)
    treplay = tet_sub.add_parser("replay")
    treplay.add_argument("--file", required=True)
    treplay.set_defaults(func=cmd_tetragon_replay)
    tet_sub.add_parser("events").set_defaults(func=cmd_tetragon_events)

    admin = sub.add_parser("admin")
    admin_sub = admin.add_subparsers(dest="admin_cmd", required=True)
    admin_sub.add_parser("inject-identity-collision").set_defaults(func=cmd_inject_collision)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
