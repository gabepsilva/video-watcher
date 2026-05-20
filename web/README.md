# `web/` — local console

- **`api/`** — FastAPI service (`vw_web`). Prefer repo root **`./video-watcher-web`** (uses `.venv` and sets `VIDEO_WATCHER_PYTHON`). See root `README.md`.
- **`ui/`** — Vite + React UI. Run `npm install` then `npm run dev`; `/api` is proxied to `127.0.0.1:8765`.
- **`docker-compose.yml`** + **`Dockerfile.api`** — API in Docker (`docker compose -f web/docker-compose.yml up --build` from repo root).

Internal design + QA matrix: `doc-internal/features/web-ui/`.
