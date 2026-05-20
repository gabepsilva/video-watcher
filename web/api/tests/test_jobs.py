"""Async job lifecycle (fake runner; no Whisper)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_create_file_job_succeeds_with_fake_runner(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("VIDEO_WATCHER_WEB_FAKE_RUNNER", "1")
    monkeypatch.setenv("VIDEO_WATCHER_WEB_JOBS_DIR", str(tmp_path))

    from vw_web.app import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("clip.wav", b"RIFF", "audio/wav")}
        data = {
            "job_type": "file",
            "model": "tiny",
            "formats": "txt",
            "gpu": "false",
            "verbose": "false",
            "summary": "false",
            "summary_model": "gemma-4-e4b",
        }
        r = await client.post("/api/jobs", data=data, files=files)
        assert r.status_code == 202, r.text
        job_id = r.json()["job_id"]

        for _ in range(50):
            jr = await client.get(f"/api/jobs/{job_id}")
            if jr.json()["state"] in ("succeeded", "failed"):
                break
            await asyncio.sleep(0.05)
        body = jr.json()
        assert body["state"] == "succeeded"
        assert body["exit_code"] == 0
        names = {a["name"] for a in body["artifacts"]}
        assert "clip.txt" in names


@pytest.mark.asyncio
async def test_create_job_rejects_missing_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("VIDEO_WATCHER_WEB_FAKE_RUNNER", "1")
    monkeypatch.setenv("VIDEO_WATCHER_WEB_JOBS_DIR", str(tmp_path))

    from vw_web.app import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = {"job_type": "file", "model": "tiny"}
        r = await client.post("/api/jobs", data=data)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_youtube_job_requires_valid_url(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("VIDEO_WATCHER_WEB_FAKE_RUNNER", "1")
    monkeypatch.setenv("VIDEO_WATCHER_WEB_JOBS_DIR", str(tmp_path))

    from vw_web.app import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = {"job_type": "youtube", "model": "tiny", "youtube_url": "https://example.com/"}
        r = await client.post("/api/jobs", data=data)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_sse_replays_logs(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("VIDEO_WATCHER_WEB_FAKE_RUNNER", "1")
    monkeypatch.setenv("VIDEO_WATCHER_WEB_JOBS_DIR", str(tmp_path))

    from vw_web.app import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=30) as client:
        files = {"file": ("clip.wav", b"RIFF", "audio/wav")}
        data = {"job_type": "file", "model": "tiny", "formats": "txt"}
        r = await client.post("/api/jobs", data=data, files=files)
        job_id = r.json()["job_id"]

        buf = ""
        async with client.stream("GET", f"/api/jobs/{job_id}/events") as stream:
            async for chunk in stream.aiter_text():
                buf += chunk
                if '"kind": "done"' in buf:
                    break

        assert "fake runner" in buf


@pytest.mark.asyncio
async def test_put_artifact_updates_txt(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("VIDEO_WATCHER_WEB_FAKE_RUNNER", "1")
    monkeypatch.setenv("VIDEO_WATCHER_WEB_JOBS_DIR", str(tmp_path))

    from vw_web.app import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("clip.wav", b"RIFF", "audio/wav")}
        data = {"job_type": "file", "model": "tiny", "formats": "txt"}
        r = await client.post("/api/jobs", data=data, files=files)
        job_id = r.json()["job_id"]

        for _ in range(50):
            jr = await client.get(f"/api/jobs/{job_id}")
            if jr.json()["state"] in ("succeeded", "failed"):
                break
            await asyncio.sleep(0.05)
        assert jr.json()["state"] == "succeeded"

        put = await client.put(
            f"/api/jobs/{job_id}/files/clip.txt",
            content="edited caption line",
            headers={"content-type": "text/plain; charset=utf-8"},
        )
        assert put.status_code == 200, put.text

        dl = await client.get(f"/api/jobs/{job_id}/files/clip.txt")
        assert dl.text == "edited caption line"


@pytest.mark.asyncio
async def test_file_job_exposes_source_media_and_input_download(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("VIDEO_WATCHER_WEB_FAKE_RUNNER", "1")
    monkeypatch.setenv("VIDEO_WATCHER_WEB_JOBS_DIR", str(tmp_path))

    from vw_web.app import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("clip.wav", b"RIFF-WAVE", "audio/wav")}
        data = {"job_type": "file", "model": "tiny", "formats": "txt"}
        r = await client.post("/api/jobs", data=data, files=files)
        job_id = r.json()["job_id"]

        body = (await client.get(f"/api/jobs/{job_id}")).json()
        assert body["source_media"] == {"name": "clip.wav", "url": f"/api/jobs/{job_id}/input"}

        inp = await client.get(f"/api/jobs/{job_id}/input")
        assert inp.status_code == 200
        assert inp.content.startswith(b"RIFF")
        assert "inline" in inp.headers.get("content-disposition", "")
        assert inp.headers.get("content-type", "").startswith("audio/")

        dl = await client.get(f"/api/jobs/{job_id}/input", params={"download": True})
        assert dl.status_code == 200
        assert "attachment" in dl.headers.get("content-disposition", "")


