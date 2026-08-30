"""Sphinx / reST reference for Aether Mesh (Read the Docs)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow autodoc of the control plane if we add it later.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

project = "Aether Mesh"
copyright = "2026, Sujatha R"
author = "Sujatha R"
release = "1.0"
extensions: list[str] = []
templates_path: list[str] = []
exclude_patterns: list[str] = ["_build"]
html_theme = "sphinx_rtd_theme"
html_title = "Aether Mesh reference"
html_short_title = "Aether Mesh"
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 3,
    "style_external_links": True,
}

# On Read the Docs, html_baseurl is injected. Local builds stay relative.
html_context = {
    "display_github": True,
    "github_user": "rsujathacse",
    "github_repo": "sujatha-portfolio",
    "github_version": "main",
    "conf_py_path": "/aether-mesh/docs/sphinx/",
}

if os.environ.get("READTHEDOCS") == "True":
    html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "")
