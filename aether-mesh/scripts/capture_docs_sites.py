#!/usr/bin/env python3
"""Serve Hugo + Sphinx HTML and screenshot with Chrome (real pages)."""

from __future__ import annotations

import http.server
import os
import shutil
import socketserver
import subprocess
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
HUGO_PUBLIC = ROOT / "docs" / "hugo" / "public"
SPHINX_HTML = ROOT / "docs" / "sphinx" / "_build" / "html"
OUT = REPO / "static" / "img" / "aether-mesh"
CHROME = os.environ.get("CHROME", "/usr/bin/google-chrome")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        pass


def serve(directory: Path, port: int) -> socketserver.TCPServer:
    handler = lambda *a, **k: QuietHandler(*a, directory=str(directory), **k)
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", port), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def screenshot(url: str, dest: Path, width: int = 1440, height: int = 900) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".chrome.png")
    cmd = [
        CHROME,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--hide-scrollbars",
        f"--window-size={width},{height}",
        "--force-device-scale-factor=1",
        f"--screenshot={tmp}",
        "--virtual-time-budget=4000",
        url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not tmp.exists():
        raise SystemExit(f"chrome failed for {url}: {proc.stderr or proc.stdout}")
    shutil.move(str(tmp), str(dest))
    print(f"wrote {dest} from {url}")


def main() -> int:
    docroot = Path("/tmp/aether-docs-root")
    if docroot.exists():
        shutil.rmtree(docroot)
    (docroot / "aether-mesh").mkdir(parents=True)
    shutil.copytree(HUGO_PUBLIC, docroot / "aether-mesh", dirs_exist_ok=True)

    hugo_httpd = serve(docroot, 1313)
    sphinx_httpd = serve(SPHINX_HTML, 8001)
    try:
        screenshot("http://127.0.0.1:1313/aether-mesh/", OUT / "hugo-home.png", 1440, 900)
        screenshot(
            "http://127.0.0.1:1313/aether-mesh/tutorials/qualify-policy/",
            OUT / "hugo-qualify-policy.png",
            1440,
            1000,
        )
        screenshot(
            "http://127.0.0.1:1313/aether-mesh/tutorials/identity-collision/",
            OUT / "hugo-identity-collision.png",
            1440,
            1000,
        )
        screenshot("http://127.0.0.1:8001/index.html", OUT / "rtd-sphinx-home.png", 1440, 900)
        screenshot("http://127.0.0.1:8001/errors.html", OUT / "rtd-sphinx-errors.png", 1440, 900)
        screenshot("http://127.0.0.1:8001/policy.html", OUT / "rtd-sphinx-policy.png", 1440, 900)
        screenshot("http://127.0.0.1:8001/cli.html", OUT / "rtd-sphinx-cli.png", 1440, 900)
    finally:
        hugo_httpd.shutdown()
        sphinx_httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
