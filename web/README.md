# `web/` — browser console (Docker Compose only)

From the **repository root**:

```bash
docker compose up --build
```

Open **http://127.0.0.1:8080**.

| Path | Role |
|------|------|
| `api/` | FastAPI (`vw_web`) — runs in the `api` service |
| `ui/` | Vite + React — built into the `ui` service (nginx) |
| `Dockerfile.api` | API image (Whisper + uvicorn) |
| `Dockerfile.ui` | UI image (npm build + nginx) |
| `nginx.conf` | Proxies `/api` → `http://api:8765` |

Host `./video-watcher-web` and `npm run dev` are **deprecated** for normal use.

Internal design: `doc-internal/features/web-ui/`.
