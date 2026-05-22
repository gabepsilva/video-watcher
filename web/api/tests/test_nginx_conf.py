"""Regression: UI nginx must allow large POST bodies for job file uploads."""

from __future__ import annotations

import re
from pathlib import Path

NGINX_CONF = Path(__file__).resolve().parents[2] / "nginx.conf"


def test_nginx_api_location_allows_large_uploads() -> None:
    text = NGINX_CONF.read_text(encoding="utf-8")
    api_block = re.search(r"location\s+/api/\s*\{([^}]+)\}", text, re.DOTALL)
    assert api_block is not None, "missing location /api/ block"
    body = api_block.group(1)
    match = re.search(r"client_max_body_size\s+(\S+)\s*;", body)
    assert match is not None, "client_max_body_size must be set in /api/ (nginx default is 1m)"
    value = match.group(1)
    if value == "0":
        return
    assert value[-1] in "kmgKMG", f"unexpected client_max_body_size unit: {value!r}"
    num = float(value[:-1])
    assert num >= 512, f"client_max_body_size too small for media uploads: {value}"
