#!/usr/bin/env bash
# Dev API: reuse bind-mounted .venv + cache; install once if missing; uvicorn --reload.
set -euo pipefail

cd /repo
export PYTHONPATH=/repo
export VIDEO_WATCHER_RUNTIME=container
export VIDEO_WATCHER_REPO_ROOT=/repo
export VIDEO_WATCHER_WEB_HOST=0.0.0.0
export VIDEO_WATCHER_WEB_PORT=8765

mkdir -p .video_watcher_web/jobs

# Pip cache in-container (avoids host .cache permission mismatches during install).
export PIP_CACHE_DIR="${PIP_CACHE_DIR:-/tmp/pip-cache}"
mkdir -p "${PIP_CACHE_DIR}"

cache_root="${VIDEO_WATCHER_CACHE:-/cache}"
mkdir -p "${cache_root}"
if touch "${cache_root}/.write-test" 2>/dev/null; then
  rm -f "${cache_root}/.write-test"
  export VIDEO_WATCHER_CACHE="${cache_root}"
  export XDG_CACHE_HOME="${cache_root}"
else
  printf '%s\n' "dev-api: ${cache_root} not writable; using /tmp/vw-cache for Whisper models" >&2
  export VIDEO_WATCHER_CACHE=/tmp/vw-cache
  export XDG_CACHE_HOME=/tmp/vw-cache
  mkdir -p "${VIDEO_WATCHER_CACHE}"
fi

if [[ -d .venv ]] && [[ ! -w .venv ]]; then
  printf '%s\n' "dev-api: .venv exists but is not writable (often created as root in Docker)." >&2
  printf '%s\n' "  sudo chown -R \"$(id -u):$(id -g)\" .venv" >&2
  printf '%s\n' "  or: rm -rf .venv && run ./install-local or ./install-gpu on the host, then restart" >&2
  exit 1
fi

dev_gpu_mode() {
  [[ "${VIDEO_WATCHER_DEV_GPU:-0}" == 1 ]] || [[ -c /dev/kfd ]]
}

venv_python_usable() {
  [[ -x .venv/bin/python ]] && .venv/bin/python -c "import sys" >/dev/null 2>&1
}

venv_whisper_ok() {
  venv_python_usable && .venv/bin/python -m whisper --help >/dev/null 2>&1
}

venv_torch_cuda_ok() {
  venv_whisper_ok && .venv/bin/python -c "import torch; raise SystemExit(0 if torch.cuda.is_available() else 1)" 2>/dev/null
}

remove_venv_if_unusable() {
  if [[ -d .venv ]] && ! venv_python_usable; then
    printf '%s\n' "dev-api: removing .venv (built for a different Python/image)…" >&2
    rm -rf .venv
  fi
}

ensure_cpu_venv() {
  remove_venv_if_unusable
  if venv_whisper_ok && ! dev_gpu_mode; then
    return 0
  fi
  if dev_gpu_mode; then
    return 0
  fi
  printf '%s\n' "dev-api: installing Whisper (CPU) into /repo/.venv (first run only; may take several minutes)…" >&2
  ./install-local
}

ensure_gpu_venv() {
  remove_venv_if_unusable
  if venv_torch_cuda_ok; then
    return 0
  fi
  if [[ -d .venv ]] && venv_whisper_ok && ! venv_torch_cuda_ok; then
    printf '%s\n' "dev-api: removing CPU .venv (GPU dev needs ROCm PyTorch)…" >&2
    rm -rf .venv
  fi
  printf '%s\n' "dev-api: setting up GPU .venv (Whisper + API deps; first run may take a few minutes)…" >&2
  sys_py="/opt/venv/bin/python"
  if [[ ! -x "${sys_py}" ]]; then
    sys_py="${PYTHON_BIN:-python}"
    command -v "${sys_py}" >/dev/null 2>&1 || sys_py=python3
  fi
  if [[ ! -d .venv ]]; then
    "${sys_py}" -m venv --system-site-packages .venv
  fi
  # ROCm image keeps torch in /opt/venv; plain --system-site-packages does not include it.
  rocm_site="/opt/venv/lib/python3.10/site-packages"
  if [[ -d "${rocm_site}" ]]; then
    mkdir -p .venv/lib/python3.10/site-packages
    printf '%s\n' "${rocm_site}" > .venv/lib/python3.10/site-packages/_rocm.pth
  fi
  .venv/bin/pip install -q -U pip
  .venv/bin/pip install -q openai-whisper sounddevice yt-dlp youtube-transcript-api
  .venv/bin/pip install -q -r web/api/requirements.txt
  if ! .venv/bin/python -c "import torch; assert torch.cuda.is_available()"; then
    printf '%s\n' "dev-api: GPU not visible inside the container." >&2
    printf '%s\n' "  Use: docker compose -f docker-compose.dev.yml -f docker-compose.dev.gpu.yml up --build" >&2
    printf '%s\n' "  For RX 6000 (Navi 21), try: export HSA_OVERRIDE_GFX_VERSION=10.3.0" >&2
    exit 1
  fi
  .venv/bin/python -c "import torch; print('dev-api: GPU', torch.cuda.get_device_name(0), file=__import__('sys').stderr)"
}

if dev_gpu_mode; then
  ensure_gpu_venv
else
  ensure_cpu_venv
fi

if ! .venv/bin/python -c "import fastapi" >/dev/null 2>&1; then
  .venv/bin/pip install -q -r web/api/requirements.txt
fi

cd web/api
exec /repo/.venv/bin/python -m uvicorn vw_web.main:app \
  --host 0.0.0.0 \
  --port 8765 \
  --reload \
  --reload-dir /repo/web/api/vw_web \
  --reload-dir /repo/vw
