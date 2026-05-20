"""Container-only runtime policy for the web console."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from vw_web.runtime_policy import (
    CONTAINER_REQUIRED_MSG,
    is_container_runtime,
    require_container_runtime,
    resolve_container_ready,
)


def test_is_container_runtime_true_when_env_set(monkeypatch) -> None:
    monkeypatch.setenv("VIDEO_WATCHER_RUNTIME", "container")
    assert is_container_runtime() is True


def test_is_container_runtime_false_by_default(monkeypatch) -> None:
    monkeypatch.delenv("VIDEO_WATCHER_RUNTIME", raising=False)
    assert is_container_runtime() is False


def test_require_container_runtime_raises_without_env(monkeypatch) -> None:
    monkeypatch.delenv("VIDEO_WATCHER_RUNTIME", raising=False)
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        require_container_runtime(container_runtime=False, fake_runner=False, torch_ok=True)
    assert exc.value.status_code == 503
    assert CONTAINER_REQUIRED_MSG in str(exc.value.detail)


def test_resolve_container_ready_requires_torch(monkeypatch) -> None:
    monkeypatch.setenv("VIDEO_WATCHER_RUNTIME", "container")
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        resolve_container_ready(container_runtime=True, fake_runner=False, torch_ok=False)
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_create_job_requires_container_runtime(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("VIDEO_WATCHER_WEB_FAKE_RUNNER", raising=False)
    monkeypatch.delenv("VIDEO_WATCHER_RUNTIME", raising=False)
    monkeypatch.setenv("VIDEO_WATCHER_WEB_JOBS_DIR", str(tmp_path))

    from vw_web.app import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("clip.wav", b"RIFF", "audio/wav")}
        data = {"job_type": "file", "model": "tiny", "formats": "txt"}
        r = await client.post("/api/jobs", data=data, files=files)
    assert r.status_code == 503, r.text
    assert "docker compose" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_meta_reports_container_runtime(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("VIDEO_WATCHER_RUNTIME", "container")
    monkeypatch.setenv("VIDEO_WATCHER_WEB_JOBS_DIR", str(tmp_path))
    monkeypatch.delenv("VIDEO_WATCHER_WEB_FAKE_RUNNER", raising=False)

    from vw_web.app import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/meta")
    assert r.status_code == 200
    body = r.json()
    assert body.get("container_runtime") is True
    assert body.get("docker_required") is False
