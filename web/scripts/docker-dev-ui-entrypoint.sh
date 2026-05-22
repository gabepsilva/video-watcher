#!/usr/bin/env sh
# Dev UI: sync bind-mounted package-lock into the node_modules volume, then Vite HMR.
set -eu

cd /app

lock_hash() {
  sha256sum package-lock.json 2>/dev/null | awk '{print $1}'
}

need_install() {
  if [ ! -d node_modules ] || [ ! -f node_modules/.package-lock.sha256 ]; then
    return 0
  fi
  want="$(lock_hash)"
  have="$(cat node_modules/.package-lock.sha256)"
  [ "$want" != "$have" ]
}

if need_install; then
  printf '%s\n' 'dev-ui: npm ci (package-lock changed or node_modules volume empty)…' >&2
  npm ci
  lock_hash > node_modules/.package-lock.sha256
fi

exec npm run dev -- --host 0.0.0.0 --port 5173
