"""Host capabilities exposed to the UI (GPU, Docker)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def docker_available() -> bool:
    """True when ``docker`` or ``podman`` can talk to a daemon."""
    for cmd in ("docker", "podman"):
        if not shutil.which(cmd):
            continue
        for subcmd in ("info", "version"):
            try:
                proc = subprocess.run(
                    [cmd, subcmd],
                    capture_output=True,
                    timeout=15,
                )
                if proc.returncode == 0:
                    return True
            except (OSError, subprocess.TimeoutExpired):
                continue
    return False


def host_gpu_devices() -> bool:
    """
    True when the host likely has a GPU usable by ``video-watcher-docker``
    (NVIDIA or AMD ROCm), without importing PyTorch.
    """
    if shutil.which("nvidia-smi"):
        try:
            proc = subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                timeout=10,
            )
            if proc.returncode == 0:
                return True
        except (OSError, subprocess.TimeoutExpired):
            pass
    # AMD ROCm (same devices video-watcher-docker checks)
    if Path("/dev/kfd").is_char_device() and Path("/dev/dri").exists():
        return True
    return False


def torch_cuda_available(python_executable: Path, *, timeout_s: float = 90.0) -> bool:
    """True when the job interpreter reports ``torch.cuda.is_available()``."""
    try:
        proc = subprocess.run(
            [
                str(python_executable),
                "-c",
                "import torch; raise SystemExit(0 if torch.cuda.is_available() else 1)",
            ],
            capture_output=True,
            timeout=timeout_s,
        )
        return proc.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def gpu_available_for_ui(
    python_executable: Path,
    *,
    torch_import_ok: bool,
    docker_ok: bool | None = None,
) -> bool:
    """
    Whether the UI should offer **GPU** for jobs.

    Native path: PyTorch sees CUDA/ROCm. Docker path: daemon up and host has GPU
    devices (container image selection is handled by ``video-watcher-docker``).
    """
    if docker_ok is None:
        docker_ok = docker_available()
    if torch_import_ok and torch_cuda_available(python_executable):
        return True
    if docker_ok and host_gpu_devices():
        return True
    return False
