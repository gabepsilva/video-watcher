"""Health endpoint contract."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from vw_web.app import create_app


@pytest.mark.asyncio
async def test_health_live_ok(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("VIDEO_WATCHER_WEB_FAKE_RUNNER", "1")
    monkeypatch.setenv("VIDEO_WATCHER_WEB_JOBS_DIR", str(tmp_path))
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/health/live")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
