"""Artifact paths and URLs (spaces in filenames, path traversal)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from vw_web.artifacts import artifact_file, artifact_file_url, artifact_name_allowed


def test_artifact_name_allows_spaces_and_dots() -> None:
    name = "OpenClaw Skills Crash Course 2.20260522-000749.summary.md"
    assert artifact_name_allowed(name)
    assert "%20" in artifact_file_url("job1", name)


def test_artifact_name_rejects_path_traversal() -> None:
    assert not artifact_name_allowed("../etc/passwd")
    assert not artifact_name_allowed("foo/bar.txt")


def test_artifact_file_resolves_spaced_name(tmp_path: Path) -> None:
    work = tmp_path / "job"
    out = work / "out"
    out.mkdir(parents=True)
    fname = "My Video.summary.md"
    (out / fname).write_text("# hello", encoding="utf-8")
    path = artifact_file(work, fname)
    assert path.read_text(encoding="utf-8") == "# hello"


def test_artifact_file_rejects_traversal(tmp_path: Path) -> None:
    work = tmp_path / "job"
    (work / "out").mkdir(parents=True)
    with pytest.raises(HTTPException) as exc:
        artifact_file(work, "..")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_and_put_artifact_with_spaces_in_name(monkeypatch, tmp_path) -> None:
    import asyncio

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

        fname = "OpenClaw Skills Crash Course 2.20260522-000749.summary.md"
        out = tmp_path / job_id / "out"
        (out / fname).write_text("# original", encoding="utf-8")

        url_path = artifact_file_url(job_id, fname)
        detail = await client.get(f"/api/jobs/{job_id}")
        names = {a["name"]: a["url"] for a in detail.json()["artifacts"]}
        assert names[fname] == url_path

        get_r = await client.get(url_path)
        assert get_r.status_code == 200, get_r.text
        assert get_r.text == "# original"

        put_r = await client.put(
            url_path,
            content="# edited",
            headers={"content-type": "text/plain; charset=utf-8"},
        )
        assert put_r.status_code == 200, put_r.text
        assert (out / fname).read_text(encoding="utf-8") == "# edited"
