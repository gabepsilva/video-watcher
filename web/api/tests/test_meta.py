"""Contract for ``GET /api/meta``."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from vw_web.app import create_app


@pytest.mark.asyncio
async def test_meta_lists_models(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("VIDEO_WATCHER_WEB_FAKE_RUNNER", "1")
    monkeypatch.setenv("VIDEO_WATCHER_WEB_JOBS_DIR", str(tmp_path))
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/meta")
    assert r.status_code == 200
    body = r.json()
    assert "tiny" in body["whisper_models"]
    assert "gemma-4-e4b" in body["summary_models"]
    assert "srt" in body["output_formats"]
    assert "subprocess_python" in body
    assert "subprocess_torch_import_ok" in body
    assert "repo_root" in body
    assert "gpu_available" in body
    assert "docker_available" in body
    assert "popular_languages" in body
    assert "format_presets" in body
    assert "en" in body["popular_languages"]
