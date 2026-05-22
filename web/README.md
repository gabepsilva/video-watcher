# `web/` — browser console (Docker Compose)

From the **repository root**:

**Dev** (live reload, bind-mounted repo / `.venv` / cache / jobs — fast iteration):

```bash
./video-watcher-web-dev          # CPU
./video-watcher-web-dev --gpu    # AMD ROCm (/dev/kfd + /dev/dri)
# Open http://127.0.0.1:5173
```

**Prod** (static UI + nginx, full Whisper image):

```bash
docker compose up --build
# Open http://127.0.0.1:8080
```

| Path | Role |
|------|------|
| `api/` | FastAPI (`vw_web`) — runs in the `api` service |
| `ui/` | Vite + React |
| `Dockerfile.api.dev` / `Dockerfile.ui.dev` | Slim dev images (`docker-compose.dev.yml`) |
| `Dockerfile.api` / `Dockerfile.ui` | Production images (`docker-compose.yml`) |
| `nginx.conf` | Prod UI: proxies `/api` → `http://api:8765` (`client_max_body_size 0`) |
| `scripts/docker-dev-api-entrypoint.sh` | Dev API: ensure `.venv`, `uvicorn --reload` |

Host `./video-watcher-web` is **deprecated** for normal use.

Internal design: `doc-internal/features/web-ui/`.
