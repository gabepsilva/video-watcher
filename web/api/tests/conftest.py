"""Pytest configuration for the web API tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Default: subprocess runner is stubbed out so the suite stays fast and offline.
os.environ.setdefault("VIDEO_WATCHER_WEB_FAKE_RUNNER", "1")

# Repo root (…/video-watcher) must be importable as ``vw`` for validation imports.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_API_ROOT = Path(__file__).resolve().parents[1]

for p in (_REPO_ROOT, _API_ROOT):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)
