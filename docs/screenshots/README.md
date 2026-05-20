# README screenshots

PNG captures for the main README live in **`web-ui/`**.

## Regenerate

With the web API and Vite UI running on localhost:

```bash
# Terminal 1
docker compose up --build

# Terminal 2
cd web/ui && npm run dev
```

Then from the repo root:

```bash
npx -p playwright@1.60.0 node docs/screenshots/capture-web-ui.mjs
```

Requires a one-time browser install: `npx playwright install chromium`.

Optional: `VW_UI_URL=http://127.0.0.1:5173` if the dev server uses another host or port.
