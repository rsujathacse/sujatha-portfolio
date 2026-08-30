#!/usr/bin/env python3
"""Render terminal screenshots from live Aether Mesh CLI/API output."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
OUT_DIR = REPO / "static" / "img" / "aether-mesh"
SAMPLES = ROOT / "samples"
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    paths = FONT_CANDIDATES
    if bold:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            *FONT_CANDIDATES,
        ]
    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def run_cmd(argv: list[str], env: dict[str, str], cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(argv, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def wrap_prompt(command: str, stdout: str, stderr: str, code: int) -> str:
    lines = [f"$ {command}"]
    body = (stdout or "") + (stderr or "")
    if body and not body.endswith("\n"):
        body += "\n"
    lines.append(body.rstrip("\n"))
    if code != 0:
        lines.append(f"[exit {code}]")
    return "\n".join(part for part in lines if part is not None)


def render_terminal(title: str, text: str, dest: Path, max_lines: int = 28) -> None:
    mono = font(16)
    mono_b = font(16, bold=True)
    pad_x, pad_y = 28, 18
    title_h = 44
    lines = text.split("\n")
    if len(lines) > max_lines:
        lines = lines[:max_lines] + ["…"]
    line_h = 22
    width = min(1400, max(960, max(int(mono.getlength(line)) for line in lines + [title]) + pad_x * 2))
    height = title_h + pad_y * 2 + line_h * max(len(lines), 4) + 12
    img = Image.new("RGB", (width, height), "#0d1117")
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width, title_h], fill="#161b22")
    for i, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        draw.ellipse([14 + i * 18, 14, 26 + i * 18, 26], fill=color)
    draw.text((90, 12), title, fill="#8b949e", font=mono_b)

    y = title_h + pad_y
    for line in lines:
        clipped = line if int(mono.getlength(line)) < width - pad_x * 2 else line[:120] + "…"
        if clipped.startswith("$ "):
            draw.text((pad_x, y), "$", fill="#3fb950", font=mono_b)
            draw.text((pad_x + 18, y), clipped[2:], fill="#e6edf3", font=mono)
        elif clipped.startswith("[exit"):
            draw.text((pad_x, y), clipped, fill="#f85149", font=mono_b)
        elif any(k in clipped for k in ("IDENTITY_COLLISION", "POLICY_SHADOW_FAILED", "POLICY_NOT_QUALIFIED")):
            draw.text((pad_x, y), clipped, fill="#ffa657", font=mono)
        elif any(k in clipped for k in ("qualified", "FORWARDED", "healthy", "promoted", "Sigkill")):
            draw.text((pad_x, y), clipped, fill="#7ee787", font=mono)
        else:
            draw.text((pad_x, y), clipped, fill="#c9d1d9", font=mono)
        y += line_h
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, "PNG")


def draw_architecture(dest: Path) -> None:
    img = Image.new("RGB", (1480, 860), "#0b1220")
    draw = ImageDraw.Draw(img)
    title_f = font(30, bold=True)
    body = font(18)
    small = font(16)
    draw.text((48, 24), "Aether Mesh  ·  self-qualifying ClusterMesh analog  ·  rev 1.0", fill="#e6edf3", font=title_f)
    draw.text(
        (48, 70),
        "Cilium identity + Hubble flows + L7 policy  →  shadow dataplane  →  enforce  |  Tetragon runtime",
        fill="#8b949e",
        font=body,
    )

    def box(xy, fill, outline, heading, lines, heading_color="#ffffff"):
        x1, y1, x2, y2 = xy
        draw.rounded_rectangle(xy, radius=16, fill=fill, outline=outline, width=2)
        draw.text((x1 + 18, y1 + 14), heading, fill=heading_color, font=font(18, bold=True))
        ty = y1 + 48
        for line in lines:
            draw.text((x1 + 18, ty), line, fill="#dbe4f0", font=small)
            ty += 22

    box((48, 120, 470, 340), "#122033", "#3d8bfd", "prod-us  cluster-id 1",
        ["frontend  identity hash(1, shop, app)", "checkout  L7 GET /api/cart", "WireGuard  kube-proxy replacement"], "#79c0ff")
    box((500, 120, 930, 340), "#1a1630", "#a371f7", "prod-eu  cluster-id 2",
        ["payments  PCI tier", "ingress only from checkout@us", "Tetragon TracingPolicy"], "#d2a8ff")
    box((960, 120, 1432, 340), "#1b2420", "#3fb950", "prod-ap  cluster-id 3",
        ["inventory  data tier", "frontend-ap replica (untrusted)", "Collision if id reused as 1"], "#7ee787")
    box((48, 380, 720, 640), "#1a2030", "#58a6ff", "Shadow dataplane (self-qualify)",
        ["Replay golden Hubble JSONL", "Unexpected deny → exit 36", "Promote only if qualified", "Hypershield dual-dataplane analog"], "#79c0ff")
    box((760, 380, 1432, 640), "#241a1a", "#f85149", "Enforce + Tetragon",
        ["Default deny  L3/L7 NetworkPolicy", "Sigkill /bin/sh in payments", "Deny webapp file_open /etc/shadow", "IDENTITY_COLLISION blocks promote"], "#ffa198")
    draw.text(
        (48, 680),
        "Not Cisco Hypershield. Open control-plane analog for Isovalent-domain documentation: identity, policy, runtime, docs-as-code.",
        fill="#8b949e",
        font=body,
    )
    draw.text(
        (48, 760),
        "Docs: Hugo/Markdown tutorials  ·  Sphinx/reST reference  ·  Git revision train  ·  aether CLI / HTTP API",
        fill="#79c0ff",
        font=small,
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, "JPEG", quality=92)
    hero = REPO / "static" / "img" / "aether-mesh-self-qualifying-zero-trust.jpg"
    shutil.copyfile(dest, hero)
    thumb = Image.new("RGB", (1200, 630), "#0b1220")
    thumb.paste(img.resize((1200, 698), Image.Resampling.LANCZOS), (0, -40))
    thumb.save(OUT_DIR / "thumbnail.png", "PNG")


def _summarize_json(text: str, keys: tuple[str, ...]) -> str:
    try:
        body = json.loads(text)
    except json.JSONDecodeError:
        return text
    if not isinstance(body, dict):
        return text
    slim = {k: body[k] for k in keys if k in body}
    return json.dumps(slim, indent=2, sort_keys=True) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="aether-docs-"))
    home = work / ".aether"
    env = os.environ.copy()
    env["PATH"] = str(Path.home() / ".local" / "bin") + os.pathsep + env.get("PATH", "")
    env["AETHER_HOME"] = str(home)
    env["AETHER_TOKEN"] = "slice-token"
    env["AETHER_ALLOW_ANON"] = "1"
    aether = shutil.which("aether", path=env["PATH"]) or str(Path.home() / ".local" / "bin" / "aether")

    def capture(filename: str, title: str, argv: list[str], display: str, slim: tuple[str, ...] | None = None) -> tuple[int, str, str]:
        code, out, err = run_cmd(argv, env, work)
        shown = out
        if slim and out.strip().startswith("{"):
            shown = _summarize_json(out, slim)
        text = wrap_prompt(display, shown, err, code)
        render_terminal(title, text, OUT_DIR / filename)
        return code, out, err

    capture("01-whoami.png", "aether whoami", [aether, "whoami"], "aether whoami",
            ("identity", "endpoint", "rev", "default_mesh", "dataplanes"))
    capture("02-mesh-bootstrap.png", "aether mesh bootstrap", [aether, "mesh", "bootstrap"], "aether mesh bootstrap",
            ("mesh", "healthy", "workloads", "encryption", "kube_proxy_replacement", "unique_cluster_ids", "kvstore"))
    capture("03-identity-list.png", "aether identity list", [aether, "identity", "list"], "aether identity list")
    # Trim identity screenshot: rewrite from parsed list
    code, out, _ = run_cmd([aether, "identity", "list"], env, work)
    identities = json.loads(out)["identities"]
    slim_ids = {
        "identities": [
            {"id": r["id"], "cluster": r["cluster"], "cluster_id": r["cluster_id"], "app": r["app"], "collision": r["collision"]}
            for r in identities
        ]
    }
    render_terminal(
        "aether identity list",
        wrap_prompt("aether identity list", json.dumps(slim_ids, indent=2), "", 0),
        OUT_DIR / "03-identity-list.png",
    )

    for yaml_name in (
        "frontend-to-checkout.yaml",
        "checkout-to-payments.yaml",
        "payments-to-inventory.yaml",
    ):
        path = SAMPLES / "policies" / yaml_name
        code, out, err = run_cmd(
            [aether, "policy", "shadow", "--file", str(path), "--flows", str(SAMPLES / "flows" / "golden.jsonl")],
            env,
            work,
        )
        assert code == 0, err or out
        bundle = json.loads(out)["bundle"]
        run_cmd([aether, "policy", "promote", "--name", bundle], env, work)

    code, out, err = run_cmd(
        [aether, "policy", "shadow", "--file", str(SAMPLES / "policies" / "frontend-to-checkout.yaml"),
         "--flows", str(SAMPLES / "flows" / "golden.jsonl")],
        env, work,
    )
    report = json.loads(out)
    slim = {
        "bundle": report["bundle"],
        "mode": report["mode"],
        "qualified": report["qualified"],
        "slo": report["slo"],
        "unexpected_denies": report["unexpected_denies"],
    }
    render_terminal(
        "aether policy shadow (qualified)",
        wrap_prompt(
            "aether policy shadow --file samples/policies/frontend-to-checkout.yaml --flows samples/flows/golden.jsonl",
            json.dumps(slim, indent=2),
            "",
            0,
        ),
        OUT_DIR / "04-policy-shadow.png",
    )
    capture(
        "05-policy-promote.png",
        "aether policy promote",
        [aether, "policy", "promote", "--name", "frontend-to-checkout"],
        "aether policy promote --name frontend-to-checkout",
        ("bundle", "dataplane", "promoted", "enforce_policies"),
    )
    code, out, err = run_cmd(
        [aether, "flow", "replay", "--file", str(SAMPLES / "flows" / "golden.jsonl"), "--dataplane", "enforce"],
        env, work,
    )
    replay = json.loads(out)
    observed = [
        {
            "src": f"{r['src']['cluster']}/{r['src']['labels']['app']}",
            "dst": f"{r['dst']['cluster']}/{r['dst']['labels']['app']}",
            "verdict": r["verdict"],
            "drop_reason": r.get("drop_reason"),
            "matched_policy": r.get("matched_policy"),
        }
        for r in replay["observed"]
    ]
    slim_replay = {
        "dataplane": replay["dataplane"],
        "flows": replay["flows"],
        "forwarded": replay["forwarded"],
        "dropped": replay["dropped"],
        "observed": observed,
    }
    render_terminal(
        "aether flow replay (enforce)",
        wrap_prompt(
            "aether flow replay --file samples/flows/golden.jsonl --dataplane enforce",
            json.dumps(slim_replay, indent=2),
            "",
            0,
        ),
        OUT_DIR / "06-flow-replay.png",
        max_lines=36,
    )

    code, out, err = run_cmd(
        [
            aether,
            "policy",
            "shadow",
            "--file",
            str(SAMPLES / "policies" / "checkout-to-payments-overreach.yaml"),
            "--flows",
            str(SAMPLES / "flows" / "golden.jsonl"),
        ],
        env,
        work,
    )
    render_terminal(
        "POLICY_SHADOW_FAILED  (overreach L7 path)",
        wrap_prompt(
            "aether policy shadow --file samples/policies/checkout-to-payments-overreach.yaml --flows samples/flows/golden.jsonl",
            out,
            err,
            code,
        ),
        OUT_DIR / "07-shadow-failed.png",
    )

    capture(
        "08-tetragon-apply.png",
        "aether tetragon apply",
        [aether, "tetragon", "apply", "--file", str(SAMPLES / "tetragon" / "payments-enforcer.yaml")],
        "aether tetragon apply --file samples/tetragon/payments-enforcer.yaml",
        ("name", "kind"),
    )
    code, out, err = run_cmd(
        [aether, "tetragon", "replay", "--file", str(SAMPLES / "tetragon" / "exploit-window.jsonl")],
        env, work,
    )
    tet = json.loads(out)
    slim_tet = {
        "events": tet["events"],
        "enforced": tet["enforced"],
        "observed": [
            {"call": r["call"], "binary": r["binary"], "action": r["action"], "enforced": r["enforced"]}
            for r in tet["observed"]
        ],
    }
    render_terminal(
        "aether tetragon replay (exploit window)",
        wrap_prompt(
            "aether tetragon replay --file samples/tetragon/exploit-window.jsonl",
            json.dumps(slim_tet, indent=2),
            "",
            0,
        ),
        OUT_DIR / "09-tetragon-exploit.png",
        max_lines=32,
    )

    code, out, err = run_cmd([aether, "admin", "inject-identity-collision"], env, work)
    render_terminal(
        "IDENTITY_COLLISION  (duplicate cluster-id)",
        wrap_prompt("aether admin inject-identity-collision", out, err, code),
        OUT_DIR / "10-identity-collision.png",
    )

    from aether.api import AetherHandler

    os.environ["AETHER_HOME"] = str(work / ".aether-api")
    os.environ["AETHER_TOKEN"] = "slice-token"
    os.environ.pop("AETHER_ALLOW_ANON", None)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), AetherHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]
    subprocess.run(
        ["curl", "-sS", "-X", "POST", f"http://127.0.0.1:{port}/v1/mesh/bootstrap",
         "-H", "Authorization: Bearer slice-token", "-H", "Content-Type: application/json", "-d", "{}"],
        capture_output=True, text=True,
    )
    proc = subprocess.run(
        ["curl", "-sS", "-D", "-", "-o", "-", f"http://127.0.0.1:{port}/v1/mesh",
         "-H", "Authorization: Bearer slice-token"],
        capture_output=True, text=True,
    )
    api_out = proc.stdout or ""
    try:
        header, _, body = api_out.partition("\r\n\r\n")
        parsed = json.loads(body) if body.strip().startswith("{") else {}
        body_slim = json.dumps(
            {k: parsed[k] for k in ("mesh", "healthy", "workloads", "encryption", "rev") if k in parsed},
            indent=2,
        )
        api_shown = header.split("\n")[0] + "\n" + body_slim + "\n"
    except json.JSONDecodeError:
        api_shown = api_out
    render_terminal(
        "GET /v1/mesh",
        wrap_prompt(
            f"python3 -m aether.api\n$ curl -sS http://127.0.0.1:{port}/v1/mesh -H 'Authorization: Bearer slice-token'",
            api_shown,
            "",
            proc.returncode,
        ),
        OUT_DIR / "11-api-mesh.png",
    )
    httpd.shutdown()

    draw_architecture(OUT_DIR / "architecture.jpg")
    print(f"Wrote screenshots to {OUT_DIR}")
    shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
