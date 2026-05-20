# Web console (local API + React UI)

Related E2E: [Web console — jobs, mic, downloads](e2e-web-console.md)

## 🚦 Status

**ACCEPTED** — Local developer surface; not a multi-tenant product.

## 🧩 Context

`video-watcher` today is a **CLI** (`python -m vw`) with **file transcription**, **YouTube (`--yt`)**, **microphone (`--mic`)**, and **post-transcribe summary (`--summary`)**. Operators asked for a **browser UI** that exposes the same capabilities in **isolated sections**, without changing the core transcription engine.

**Domain language**

- **Job** — One asynchronous **file** or **YouTube** transcription (and optional summary) tracked by the API until exit.
- **Web mic** — Browser capture → **phrase audio** uploaded to the API; Whisper runs **in the API process** with a **cached model** (CLI mic remains server-side PortAudio + `vw/mic.py`).
- **Artifact** — Any output file under the job workspace (captions, summary markdown).

## 🎯 Scope

| Area | In scope |
|------|----------|
| Local FastAPI on `127.0.0.1` by default | Yes |
| Async jobs + log stream (SSE) for file / YouTube | Yes |
| Multipart file upload and YouTube URL field | Yes |
| Optional `--summary` / `--summary-model` on jobs | Yes |
| Browser mic: WAV (or browser default) phrase upload → JSON text | Yes |
| Auth / multi-user | No (localhost trust boundary) |
| Replacing CLI `vw/mic.py` for web users | No — parallel path |

## ✅ Decision

1. **Layout:** `web/api/` (FastAPI) and `web/ui/` (Vite + React + TypeScript). Vite **proxies** `/api` to the API in dev to avoid CORS.
2. **Jobs:** `POST /api/jobs` returns `job_id` immediately; worker runs `python -m vw` with `PYTHONPATH` set to the **repository root** (same contract as `./video-watcher`). **One concurrent subprocess job** to reduce GPU/RAM contention.
3. **Progress:** Subprocess **stderr** lines are appended to a ring buffer and replayed over **`GET /api/jobs/{id}/events`** as **SSE** (`data: …\n\n`).
4. **Downloads:** `GET /api/jobs/{id}/files/{name}` serves files under the job directory only (basename allow-list).
5. **Web mic:** `POST /api/mic/transcribe` accepts audio; server writes a temp file, runs Whisper with a **per-(model, device) cached model**; returns transcript text. **No** `--summary` on this route (matches CLI: summary not supported with mic).
6. **Observability:** `GET /api/health/live` for liveness.

## 🤔 Alternatives considered

1. **Blocking HTTP until transcription finishes** — Rejected: brittle timeouts and poor UX for long media.
2. **Browser-only Whisper** — Rejected: duplicates model/cache story and diverges from `vw`.
3. **Subprocess per mic phrase** — Rejected: reloads Whisper every phrase; unusable latency.

## ⚖️ Consequences

- **Positive:** Reuses `vw` for heavy jobs unchanged; UI can ship incrementally.
- **Trade-off:** API process holds Whisper weights for web mic; concurrent **subprocess** jobs may still compete for GPU with mic unless operators serialize usage.

## 🏗️ Implemented Design

### API (FastAPI)

- Package: `web/api/vw_web/`
- ASGI entry: `vw_web.main:app` (wraps `create_app()`).
- **Config:** `VIDEO_WATCHER_WEB_HOST` (default `127.0.0.1`), `VIDEO_WATCHER_WEB_PORT` (default `8765`), `VIDEO_WATCHER_WEB_JOBS_DIR` (default `<repo>/.video_watcher_web/jobs`), `VIDEO_WATCHER_PYTHON` (optional; else first ``.venv`` interpreter that passes ``import torch``, else first ``.venv/bin/python*``, else ``sys.executable``). Repo root is **discovered** by walking parents for ``vw/cli.py`` + ``video-watcher`` (override with ``VIDEO_WATCHER_REPO_ROOT``).

### Frontend (React)

- Sections: **File transcription**, **YouTube**, **Microphone (browser)**; shared **Job status** area for async jobs.
- Uses `fetch` + `EventSource` for SSE against proxied `/api`.

## 🧪 Test Coverage Snapshot

- Backend contract and state machine: `web/api/tests/` (pytest + httpx `AsyncClient`).
- Manual / future browser automation: see [e2e-web-console.md](e2e-web-console.md).
