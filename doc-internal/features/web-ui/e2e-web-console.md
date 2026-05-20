# Web console — jobs, mic, downloads

Related ADR: [Web console (local API + React UI)](adr-web-console.md)

## Purpose

Validate the **local web console** end-to-end: **async jobs** (file + YouTube), **SSE logs**, **artifact downloads**, and **browser → API** microphone phrases.

## Preconditions

- Repository root: run `./install-local` (or equivalent) so `python -m vw` works.
- From `web/api/`: install deps (`pip install -r requirements.txt` in the project venv or a dedicated venv).
- API: `PYTHONPATH=../..` and `uvicorn vw_web.main:app` with cwd `web/api` (see root `README.md`).
- UI: `npm install` && `npm run dev` in `web/ui/` (Vite proxies `/api`).

## Test matrix

| ID | Step | Action | Expected | Coverage |
|----|------|--------|----------|----------|
| TC-WEB-001 | File job | Upload short media, model `tiny` | Job `succeeded`; artifacts listed; download returns bytes | Manual / backlog |
| TC-WEB-002 | YouTube | Submit a public URL | Completes or fails with stderr visible in SSE | Manual (network) |
| TC-WEB-003 | SSE | Open `EventSource` on `/api/jobs/{id}/events` | `log` events mirror subprocess stderr | Automated (`web/api/tests/test_jobs.py`) |
| TC-WEB-004 | Web mic | Record in UI → `POST /api/mic/transcribe` | JSON `text` for audible speech | Manual |
| TC-WEB-005 | Summary | File job with `summary=true` (requires `llama-cli`) | `.summary.md` artifact or clear job `error` | Manual |
| TC-WEB-006 | Meta | `GET /api/meta` | Lists `whisper_models`, `summary_models`, `output_formats` | Automated (`web/api/tests/test_meta.py`) |
| TC-WEB-007 | Health | `GET /api/health/live` | `{"status":"ok"}` | Automated (`web/api/tests/test_health.py`) |

**Automation caveat:** `VIDEO_WATCHER_WEB_FAKE_RUNNER=1` (default in `web/api/tests/conftest.py`) stubs subprocess `vw` for speed; it does **not** validate real Whisper runs or GPU paths.

## Spec reference

- `web/api/tests/test_health.py`
- `web/api/tests/test_meta.py`
- `web/api/tests/test_jobs.py`

## Run only this suite

```bash
cd /path/to/video-watcher/web/api
PYTHONPATH="../../:." ../../.venv/bin/python -m pytest -q
```
