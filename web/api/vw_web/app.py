"""FastAPI application for the local web console."""

from __future__ import annotations

import asyncio
import json
import re
import secrets
import shutil
import tempfile
from contextlib import asynccontextmanager
from functools import partial
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from vw.constants import OUTPUT_EXTENSIONS, SUMMARY_MODELS, WHISPER_MODELS
from vw.yt import is_youtube_url

from vw_web.config import Settings, load_settings, runtime_meta
from vw_web.job_store import JobStore, SSE_END
from vw_web.meta import meta_payload
from vw_web.mic_transcribe import transcribe_audio_file
from vw_web.models import JobKind, JobState
from vw_web.artifacts import (
    EDITABLE_EXTENSIONS,
    MAX_EDIT_BYTES,
    artifact_file,
    artifact_file_url,
    is_editable,
    job_input_file,
    serve_media_file,
    source_media_payload,
)
from vw_web.runner import runner_for_job
from vw_web.runtime_policy import require_container_runtime, resolve_container_ready


def _safe_filename(name: str | None) -> str:
    if not name:
        return "upload.bin"
    base = Path(name).name
    if base in (".", "..") or not base:
        return "upload.bin"
    return base


def _validate_formats(formats: str) -> str:
    fm = formats.strip() or "all"
    if fm == "all":
        return fm
    parts = [p.strip().lower() for p in fm.split(",") if p.strip()]
    if not parts:
        raise HTTPException(status_code=422, detail="invalid formats")
    for p in parts:
        if p not in OUTPUT_EXTENSIONS:
            raise HTTPException(status_code=422, detail=f"unknown format: {p}")
    return fm


def _validate_model(model: str) -> None:
    if model not in WHISPER_MODELS:
        raise HTTPException(status_code=422, detail=f"unknown model: {model}")


def _validate_summary_model(summary_model: str) -> None:
    if summary_model not in SUMMARY_MODELS:
        raise HTTPException(status_code=422, detail=f"unknown summary model: {summary_model}")


class JobSummary(BaseModel):
    id: str
    kind: str
    state: str
    created_at: str
    exit_code: int | None = None
    error: str | None = None


class SourceMedia(BaseModel):
    name: str
    url: str


class JobArtifact(BaseModel):
    name: str
    url: str
    editable: bool = False


class JobDetail(BaseModel):
    id: str
    kind: str
    state: str
    created_at: str
    exit_code: int | None = None
    error: str | None = None
    source_media: SourceMedia | None = None
    artifacts: list[JobArtifact] = Field(default_factory=list)


def _artifacts_for_job(job_id: str, work_dir: Path) -> list[JobArtifact]:
    """List downloadable files under ``out/`` (promote Docker ``--yt`` outputs from job root)."""
    out_dir = work_dir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in work_dir.iterdir():
        if p.is_file() and p.parent == work_dir:
            dest = out_dir / p.name
            if not dest.is_file():
                try:
                    shutil.copy2(p, dest)
                except OSError:
                    pass
    items: list[JobArtifact] = []
    if not out_dir.is_dir():
        return items
    for p in sorted(out_dir.iterdir()):
        if p.is_file():
            items.append(
                JobArtifact(
                    name=p.name,
                    url=artifact_file_url(job_id, p.name),
                    editable=is_editable(p.name),
                )
            )
    return items


async def _execute_job(app: FastAPI, job_id: str) -> None:
    store: JobStore = app.state.job_store
    settings: Settings = app.state.settings
    lock: asyncio.Lock = app.state.job_lock

    job = store.get(job_id)
    if job is None:
        return

    meta_path = job.work_dir / "job.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    out_dir = job.work_dir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    kind = meta["kind"]
    input_path = Path(meta["input_path"]) if meta.get("input_path") else None
    youtube_url = meta.get("youtube_url")

    def log_line(msg: str) -> None:
        store.publish_log(job_id, msg)

    runner = runner_for_job(settings)
    work = partial(
        runner.run,
        job_id=job_id,
        settings=settings,
        output_dir=out_dir,
        input_path=input_path,
        youtube_url=youtube_url,
        model=meta["model"],
        language=meta.get("language"),
        formats=meta["formats"],
        gpu=bool(meta.get("gpu")),
        verbose=bool(meta.get("verbose")),
        summary=bool(meta.get("summary")),
        summary_model=meta["summary_model"],
        log_line=log_line,
    )

    async with lock:
        store.publish_state(job_id, JobState.RUNNING)
        try:
            code = int(await asyncio.to_thread(work))
            job.exit_code = code
            if code == 0:
                store.publish_state(job_id, JobState.SUCCEEDED)
            else:
                job.error = f"vw exited with code {code}"
                store.publish_state(job_id, JobState.FAILED)
        except Exception as exc:  # noqa: BLE001 — surface worker failures to the job record
            job.exit_code = 1
            job.error = str(exc)
            store.publish_log(job_id, f"error: {exc}")
            store.publish_state(job_id, JobState.FAILED)
        finally:
            store.publish_done(job_id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    store: JobStore = app.state.job_store
    store.attach_loop(asyncio.get_running_loop())
    yield


def create_app() -> FastAPI:
    settings = load_settings()

    app = FastAPI(title="video-watcher web API", lifespan=lifespan)
    app.state.settings = settings
    app.state.job_store = JobStore()
    app.state.job_lock = asyncio.Lock()
    app.state.api_meta_static: dict[str, Any] = meta_payload()

    @app.get("/api/meta")
    async def meta(request: Request) -> dict[str, Any]:
        settings: Settings = request.app.state.settings
        # Re-check Docker on each request (fast); GPU uses startup probe + host devices.
        return {
            **request.app.state.api_meta_static,
            **runtime_meta(settings),
        }

    @app.get("/api/health/live")
    async def health_live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/jobs", response_model=list[JobSummary])
    async def list_jobs(request: Request) -> list[JobSummary]:
        store: JobStore = request.app.state.job_store
        out: list[JobSummary] = []
        for j in store.list_recent(50):
            out.append(
                JobSummary(
                    id=j.id,
                    kind=j.kind,
                    state=j.state.value,
                    created_at=j.created_at.isoformat(),
                    exit_code=j.exit_code,
                    error=j.error,
                )
            )
        return out

    @app.get("/api/jobs/{job_id}", response_model=JobDetail)
    async def get_job(job_id: str, request: Request) -> JobDetail:
        store: JobStore = request.app.state.job_store
        job = store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="unknown job")
        artifacts = _artifacts_for_job(job.id, job.work_dir)
        src = source_media_payload(job.id, job.work_dir)
        return JobDetail(
            id=job.id,
            kind=job.kind,
            state=job.state.value,
            created_at=job.created_at.isoformat(),
            exit_code=job.exit_code,
            error=job.error,
            source_media=SourceMedia(**src) if src else None,
            artifacts=artifacts,
        )

    @app.get("/api/jobs/{job_id}/events")
    async def job_events(job_id: str, request: Request) -> StreamingResponse:
        store: JobStore = request.app.state.job_store
        job = store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="unknown job")

        q = store.subscribe(job_id)

        async def gen():
            try:
                snap = store.get(job_id)
                if snap is None:
                    return
                for line in list(snap.log_lines):
                    yield f"data: {json.dumps({'kind': 'log', 'line': line})}\n\n"
                latest = store.get(job_id)
                if latest is not None and latest.state in (JobState.SUCCEEDED, JobState.FAILED):
                    yield f"data: {json.dumps({'kind': 'done'})}\n\n"
                    return
                while True:
                    item = await q.get()
                    if item is SSE_END:
                        yield f"data: {json.dumps({'kind': 'done'})}\n\n"
                        break
                    yield f"data: {json.dumps(item)}\n\n"
            finally:
                store.unsubscribe(job_id, q)

        return StreamingResponse(gen(), media_type="text/event-stream")

    @app.get("/api/jobs/{job_id}/files/{name}")
    async def download_file(
        job_id: str,
        name: str,
        request: Request,
        download: bool = False,
    ) -> FileResponse:
        store: JobStore = request.app.state.job_store
        job = store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="unknown job")
        path = artifact_file(job.work_dir, name)
        return serve_media_file(path, as_download=download)

    @app.put("/api/jobs/{job_id}/files/{name}")
    async def update_artifact_file(job_id: str, name: str, request: Request) -> dict[str, str]:
        if not is_editable(name):
            raise HTTPException(
                status_code=422,
                detail=f"file is not editable (allowed: {', '.join(sorted(EDITABLE_EXTENSIONS))})",
            )
        store: JobStore = request.app.state.job_store
        job = store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="unknown job")
        raw = await request.body()
        if len(raw) > MAX_EDIT_BYTES:
            raise HTTPException(status_code=413, detail=f"body exceeds {MAX_EDIT_BYTES} bytes")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=422, detail="body must be UTF-8 text") from exc
        path = artifact_file(job.work_dir, name)
        path.write_text(text, encoding="utf-8")
        return {"name": name, "status": "saved"}

    @app.get("/api/jobs/{job_id}/input")
    async def download_input_file(
        job_id: str,
        request: Request,
        download: bool = False,
    ) -> FileResponse:
        store: JobStore = request.app.state.job_store
        job = store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="unknown job")
        path = job_input_file(job.work_dir)
        if path is None:
            raise HTTPException(status_code=404, detail="no input media for this job")
        return serve_media_file(path, as_download=download)

    @app.post("/api/jobs", status_code=202)
    async def create_job(
        request: Request,
        background: BackgroundTasks,
        job_type: str = Form(..., description="file or youtube"),
        model: str = Form("base"),
        formats: str = Form("all"),
        language: str | None = Form(None),
        gpu: bool = Form(False),
        verbose: bool = Form(False),
        summary: bool = Form(False),
        summary_model: str = Form("gemma-4-e4b"),
        youtube_url: str | None = Form(None),
        file: UploadFile | None = File(None),
    ) -> dict[str, str]:
        store: JobStore = request.app.state.job_store
        settings: Settings = request.app.state.settings
        body = {**request.app.state.api_meta_static, **runtime_meta(settings)}
        resolve_container_ready(
            container_runtime=settings.container_runtime,
            fake_runner=settings.fake_runner,
            torch_ok=settings.torch_import_ok,
        )
        if gpu and not body.get("gpu_available"):
            raise HTTPException(
                status_code=422,
                detail="GPU is not available in this container (rebuild with a GPU image or use CPU)",
            )

        jt = job_type.strip().lower()
        if jt not in ("file", "youtube"):
            raise HTTPException(status_code=422, detail="job_type must be file or youtube")

        _validate_model(model)
        fm = _validate_formats(formats)
        if summary:
            _validate_summary_model(summary_model)

        if jt == "file":
            if file is None:
                raise HTTPException(status_code=422, detail="file is required for job_type=file")
            if not file.filename:
                raise HTTPException(status_code=422, detail="file requires a filename")
            kind: JobKind = "file"
            yt: str | None = None
            if youtube_url:
                raise HTTPException(status_code=422, detail="youtube_url must be empty for file jobs")
        else:
            if not youtube_url or not youtube_url.strip():
                raise HTTPException(status_code=422, detail="youtube_url is required for job_type=youtube")
            yt = youtube_url.strip()
            if not is_youtube_url(yt):
                raise HTTPException(status_code=422, detail="not a recognized YouTube URL")
            if file is not None:
                raise HTTPException(status_code=422, detail="file must be omitted for youtube jobs")
            kind = "youtube"

        work_root = settings.jobs_dir.resolve()
        record = store.create_job(kind=kind, jobs_dir=work_root)
        job_id = record.id
        work_dir = record.work_dir

        input_path: str | None = None
        if jt == "file":
            assert file is not None
            safe = _safe_filename(file.filename)
            dest = work_dir / safe
            dest.write_bytes(await file.read())
            input_path = str(dest)

        lng = (language or "").strip() or None
        meta: dict[str, Any] = {
            "kind": kind,
            "model": model,
            "formats": fm,
            "language": lng,
            "gpu": gpu,
            "verbose": verbose,
            "summary": summary,
            "summary_model": summary_model,
            "input_path": input_path,
            "youtube_url": yt,
        }
        (work_dir / "job.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

        background.add_task(_execute_job, request.app, job_id)
        return {"job_id": job_id}

    @app.post("/api/mic/transcribe")
    async def mic_transcribe(
        request: Request,
        audio: UploadFile = File(...),
        model: str = Form("base"),
        language: str | None = Form(None),
        gpu: bool = Form(False),
    ) -> dict[str, Any]:
        _validate_model(model)
        settings: Settings = request.app.state.settings
        body = {**request.app.state.api_meta_static, **runtime_meta(settings)}
        require_container_runtime(
            container_runtime=settings.container_runtime,
            fake_runner=settings.fake_runner,
            torch_ok=settings.torch_import_ok,
        )
        if gpu and not body.get("gpu_available"):
            raise HTTPException(
                status_code=422,
                detail="GPU is not available in this container (rebuild with a GPU image or use CPU)",
            )
        suffix = Path(_safe_filename(audio.filename)).suffix or ".webm"
        work = Path(tempfile.mkdtemp(prefix="vw-mic-"))
        tmp = work / f"phrase{suffix}"
        tmp.write_bytes(await audio.read())
        try:
            try:
                return await transcribe_audio_file(
                    tmp,
                    settings=settings,
                    model=model,
                    language=language.strip() if language else None,
                    gpu=gpu,
                )
            except RuntimeError as exc:
                raise HTTPException(status_code=500, detail=str(exc)) from exc
        finally:
            shutil.rmtree(work, ignore_errors=True)

    return app
