#!/usr/bin/env python3
"""Render terminal screenshots from live Helios CLI/API output."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
OUT_DIR = REPO / "static" / "img" / "helios"
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
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
    proc = subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
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


def render_terminal(title: str, text: str, dest: Path) -> None:
    mono = font(18)
    mono_b = font(18, bold=True)
    pad_x, pad_y = 28, 22
    title_h = 44
    lines = text.split("\n")
    line_h = 26
    width = max(920, max(int(mono.getlength(line)) for line in lines + [title]) + pad_x * 2)
    height = title_h + pad_y * 2 + line_h * max(len(lines), 4) + 12
    img = Image.new("RGB", (width, height), "#0d1117")
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width, title_h], fill="#161b22")
    for i, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        draw.ellipse([14 + i * 18, 14, 26 + i * 18, 26], fill=color)
    draw.text((90, 12), title, fill="#8b949e", font=mono_b)

    y = title_h + pad_y
    for line in lines:
        if line.startswith("$ "):
            draw.text((pad_x, y), "$", fill="#3fb950", font=mono_b)
            draw.text((pad_x + 18, y), line[2:], fill="#e6edf3", font=mono)
        elif line.startswith("[exit"):
            draw.text((pad_x, y), line, fill="#f85149", font=mono_b)
        elif '"code"' in line or "LICENSE_EXHAUSTED" in line or "REGION_PIN" in line or "NFS_STALE" in line:
            draw.text((pad_x, y), line, fill="#ffa657", font=mono)
        elif any(key in line for key in ("succeeded", "farm", "analog_sim", "healthy")):
            draw.text((pad_x, y), line, fill="#7ee787", font=mono)
        else:
            draw.text((pad_x, y), line, fill="#c9d1d9", font=mono)
        y += line_h
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, "PNG")


def draw_architecture(dest: Path) -> None:
    img = Image.new("RGB", (1400, 820), "#0b1220")
    draw = ImageDraw.Draw(img)
    title_f = font(32, bold=True)
    body = font(18)
    small = font(16)
    draw.text((48, 28), "Helios hybrid EDA job fabric  ·  rev 1.1", fill="#e6edf3", font=title_f)
    draw.text(
        (48, 78),
        "Linux CLI  →  scheduler + pin policy  →  farm licenses  →  on-prem farm or burst compute",
        fill="#8b949e",
        font=body,
    )

    def box(xy, fill, outline, heading, lines, heading_color="#ffffff"):
        x1, y1, x2, y2 = xy
        draw.rounded_rectangle(xy, radius=16, fill=fill, outline=outline, width=2)
        draw.text((x1 + 20, y1 + 16), heading, fill=heading_color, font=font(20, bold=True))
        ty = y1 + 52
        for line in lines:
            draw.text((x1 + 20, ty), line, fill="#dbe4f0", font=small)
            ty += 24

    box(
        (48, 140, 380, 360),
        "#122033",
        "#3d8bfd",
        "helios CLI / API",
        ["helios whoami", "helios job submit|get|wait", "helios job artifacts", "python -m helios.api"],
        "#79c0ff",
    )
    box(
        (430, 140, 820, 360),
        "#1a1630",
        "#a371f7",
        "Scheduler",
        ["class: sim → analog_sim", "class: pnr → place_route", "quota per project", "pin farm | burst"],
        "#d2a8ff",
    )
    box(
        (870, 140, 1352, 360),
        "#1b2420",
        "#3fb950",
        "Farm license daemon",
        ["analog_sim seats", "place_route seats", "Burst cannot mint features", "LICENSE_EXHAUSTED → wait / 32"],
        "#7ee787",
    )
    box(
        (48, 420, 680, 680),
        "#1a2030",
        "#58a6ff",
        "On-prem farm  (classified OK)",
        [
            "project analog-ip  data-class=classified",
            "sim-class:1.1  and  pnr-class:1.1 images",
            "artifacts on farm volume  (smoke.log)",
            "NFS_STALE → retry once, then storage on-call",
        ],
        "#79c0ff",
    )
    box(
        (720, 420, 1352, 680),
        "#241a1a",
        "#f85149",
        "Burst compute  (internal only)",
        [
            "project demo  data-class=internal",
            "REGION_PIN (exit 34 / HTTP 403) if classified",
            "Still checks out a farm license seat",
            "Do not probe NFS from a burst node",
        ],
        "#ffa198",
    )
    draw.text(
        (48, 720),
        "Trust boundary: classified netlists and analog IP stay on the farm. Tokens stay out of Jira and Confluence.",
        fill="#8b949e",
        font=body,
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, "JPEG", quality=92)
    hero = REPO / "static" / "img" / "helios-hybrid-eda-job-fabric.jpg"
    shutil.copyfile(dest, hero)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="helios-docs-"))
    home = work / ".helios"
    samples = work / "samples" / "smoke"
    samples.mkdir(parents=True)
    shutil.copytree(ROOT / "samples" / "smoke", samples, dirs_exist_ok=True)
    env = os.environ.copy()
    env["PATH"] = str(Path.home() / ".local" / "bin") + os.pathsep + env.get("PATH", "")
    env["HELIOS_HOME"] = str(home)
    env["HELIOS_TOKEN"] = "slice-token"
    env["HELIOS_ALLOW_ANON"] = "0"
    helios = shutil.which("helios", path=env["PATH"]) or str(Path.home() / ".local" / "bin" / "helios")

    shots: list[tuple[str, str, list[str]]] = []

    def capture(filename: str, title: str, argv: list[str], display: str | None = None) -> tuple[int, str, str]:
        code, out, err = run_cmd(argv, env, work)
        text = wrap_prompt(display or " ".join(argv), out, err, code)
        render_terminal(title, text, OUT_DIR / filename)
        shots.append((filename, title, argv))
        return code, out, err

    capture("01-whoami.png", "helios whoami", [helios, "whoami"], "helios whoami")

    code, out, _ = capture(
        "02-job-submit.png",
        "helios job submit (demo / farm)",
        [
            helios,
            "job",
            "submit",
            "--project",
            "demo",
            "--class",
            "sim",
            "--image",
            "sim-class:1.1",
            "--pin",
            "farm",
            "--input",
            "samples/smoke",
        ],
        "helios job submit --project demo --class sim --image sim-class:1.1 --pin farm --input samples/smoke",
    )
    assert code == 0, out
    job_id = json.loads(out)["job_id"]

    capture(
        "03-job-wait.png",
        "helios job wait",
        [helios, "job", "wait", job_id],
        f"helios job wait {job_id}",
    )
    capture(
        "04-job-get.png",
        "helios job get",
        [helios, "job", "get", job_id],
        f"helios job get {job_id}",
    )
    capture(
        "05-job-artifacts.png",
        "helios job artifacts",
        [helios, "job", "artifacts", job_id, "--out", "./helios-out"],
        f"helios job artifacts {job_id} --out ./helios-out",
    )
    log_text = (work / "helios-out" / "smoke.log").read_text(encoding="utf-8")
    render_terminal(
        "./helios-out/smoke.log",
        wrap_prompt("cat ./helios-out/smoke.log", log_text, "", 0),
        OUT_DIR / "06-smoke-log.png",
    )

    capture(
        "07-admin-status.png",
        "helios admin status --verbose",
        [helios, "admin", "status", "--verbose"],
        "helios admin status --verbose",
    )
    capture(
        "08-admin-licenses.png",
        "helios admin licenses",
        [helios, "admin", "licenses"],
        "helios admin licenses",
    )
    capture(
        "09-region-pin.png",
        "REGION_PIN  (classified + burst)",
        [
            helios,
            "job",
            "submit",
            "--project",
            "analog-ip",
            "--class",
            "sim",
            "--image",
            "sim-class:1.1",
            "--pin",
            "burst",
            "--input",
            "samples/smoke",
        ],
        "helios job submit --project analog-ip --class sim --image sim-class:1.1 --pin burst --input samples/smoke",
    )
    capture(
        "10-drain-licenses.png",
        "helios admin drain-licenses",
        [helios, "admin", "drain-licenses", "--feature", "analog_sim"],
        "helios admin drain-licenses --feature analog_sim",
    )
    capture(
        "11-fail-if-queued.png",
        "LICENSE_EXHAUSTED  (--fail-if-queued)",
        [
            helios,
            "job",
            "submit",
            "--project",
            "demo",
            "--class",
            "sim",
            "--image",
            "sim-class:1.1",
            "--pin",
            "farm",
            "--input",
            "samples/smoke",
            "--fail-if-queued",
        ],
        "helios job submit --project demo --class sim --image sim-class:1.1 --pin farm --input samples/smoke --fail-if-queued",
    )

    # Fresh home for NFS path so licenses are available again.
    home2 = work / ".helios-nfs"
    env2 = env.copy()
    env2["HELIOS_HOME"] = str(home2)
    code, out, _ = run_cmd(
        [
            helios,
            "job",
            "submit",
            "--project",
            "demo",
            "--class",
            "sim",
            "--image",
            "sim-class:1.1",
            "--pin",
            "farm",
            "--input",
            "samples/smoke",
        ],
        env2,
        work,
    )
    nfs_id = json.loads(out)["job_id"]
    run_cmd([helios, "admin", "inject-nfs-stale", nfs_id], env2, work)
    code, out, err = run_cmd(
        [helios, "job", "artifacts", nfs_id, "--out", str(work / "stale-out")],
        env2,
        work,
    )
    text = wrap_prompt(
        f"helios admin inject-nfs-stale {nfs_id}\n$ helios job artifacts {nfs_id} --out ./helios-out",
        out,
        err,
        code,
    )
    render_terminal("NFS_STALE  (exit 41)", text, OUT_DIR / "12-nfs-stale.png")

    # API screenshot via urllib against in-process server would be nicer;
    # start the API on an ephemeral port.
    import threading
    from http.server import ThreadingHTTPServer
    from helios.api import HeliosHandler

    os.environ["HELIOS_HOME"] = str(work / ".helios-api")
    os.environ["HELIOS_TOKEN"] = "slice-token"
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), HeliosHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]
    curl = [
        "curl",
        "-sS",
        "-D",
        "-",
        "-o",
        "-",
        "-X",
        "POST",
        f"http://127.0.0.1:{port}/v1/jobs",
        "-H",
        "Authorization: Bearer slice-token",
        "-H",
        "Content-Type: application/json",
        "-d",
        '{"project":"demo","class":"sim","image":"sim-class:1.1","pin":"farm","input":"samples/smoke"}',
    ]
    proc = subprocess.run(curl, cwd=work, env=env, text=True, capture_output=True)
    api_out = (proc.stdout or "") + (proc.stderr or "")
    display = (
        "python -m helios.api\n"
        f"$ curl -sS -X POST http://127.0.0.1:{port}/v1/jobs \\\n"
        "    -H 'Authorization: Bearer slice-token' \\\n"
        "    -H 'Content-Type: application/json' \\\n"
        "    -d '{\"project\":\"demo\",\"class\":\"sim\",\"image\":\"sim-class:1.1\",\"pin\":\"farm\",\"input\":\"samples/smoke\"}'"
    )
    render_terminal("POST /v1/jobs", wrap_prompt(display, api_out, "", proc.returncode), OUT_DIR / "13-api-submit.png")
    httpd.shutdown()

    draw_architecture(OUT_DIR / "architecture.jpg")
    print(f"Wrote screenshots to {OUT_DIR}")
    shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
