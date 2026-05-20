"""Twelve-factor style settings for the web API."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


def discover_repo_root() -> Path:
    """
    Find the video-watcher repository root (directory that contains ``vw/cli.py``).

    Walks parents from ``vw_web/config.py``. If that fails (e.g. editable install
    with ``vw_web`` outside the repo tree), fall back to the ``vw`` package path
    from ``import vw`` so ``.venv`` resolution still matches the real checkout.
    """
    here = Path(__file__).resolve()
    for d in (here, *here.parents):
        if (d / "vw" / "cli.py").is_file():
            return d
    try:
        import vw as vw_pkg  # noqa: PLC0415 — deliberate late import for path discovery

        pkg_dir = Path(vw_pkg.__file__).resolve().parent
        if (pkg_dir / "cli.py").is_file():
            return pkg_dir.parent
    except Exception:
        pass
    return here.parents[3]


def _default_repo_root() -> Path:
    return discover_repo_root()


def _default_jobs_dir(repo_root: Path) -> Path:
    raw = os.environ.get("VIDEO_WATCHER_WEB_JOBS_DIR")
    if raw:
        return Path(raw).expanduser().resolve()
    return (repo_root / ".video_watcher_web" / "jobs").resolve()


def _venv_bin_pythons(repo_root: Path) -> list[Path]:
    """Prefer ``python``, then ``python3``, then ``python3.x`` under ``.venv/bin``."""
    bin_dir = repo_root / ".venv" / "bin"
    if not bin_dir.is_dir():
        return []
    out: list[Path] = []
    for name in ("python", "python3"):
        p = bin_dir / name
        if p.is_file():
            out.append(p)
    extras = sorted(
        (bin_dir / p.name)
        for p in bin_dir.glob("python3.*")
        if p.is_file() and p.name not in {"python3", "python3-config"}
    )
    for p in extras:
        if p not in out:
            out.append(p)
    return out


def python_imports_torch(py: Path, *, timeout_s: float = 45.0) -> bool:
    """Return True if ``py -c 'import torch'`` succeeds (used at startup / settings)."""
    try:
        proc = subprocess.run(
            [str(py), "-c", "import torch"],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        return proc.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def resolve_vw_python(repo_root: Path) -> tuple[Path, bool]:
    """
    Pick the interpreter for ``python -m vw`` jobs and whether it can ``import torch``.

    **Do not** ``Path.resolve()`` interpreter paths: venv ``python`` is often a
    symlink to the base binary; resolving breaks ``site-packages`` / PyTorch.
    """
    override = os.environ.get("VIDEO_WATCHER_PYTHON")
    if override:
        p = Path(override).expanduser()
        return p, python_imports_torch(p)

    candidates = _venv_bin_pythons(repo_root)
    fake = os.environ.get("VIDEO_WATCHER_WEB_FAKE_RUNNER", "").lower() in (
        "1",
        "true",
        "yes",
    )
    if fake:
        if candidates:
            return candidates[0], True
        return Path(sys.executable), True

    for py in candidates:
        if python_imports_torch(py):
            return py, True
    if candidates:
        p = candidates[0]
        return p, python_imports_torch(p)
    p = Path(sys.executable)
    return p, python_imports_torch(p)


@dataclass(frozen=True, slots=True)
class Settings:
    repo_root: Path
    jobs_dir: Path
    python_executable: Path
    host: str
    port: int
    fake_runner: bool
    torch_import_ok: bool
    gpu_cuda_ok: bool


def runtime_meta(settings: Settings, *, refresh_docker: bool = True) -> dict[str, str | bool]:
    """Extra fields for ``GET /api/meta`` (operator diagnostics)."""
    from vw_web.capabilities import docker_available, host_gpu_devices

    if settings.fake_runner:
        docker_ok = False
        gpu_ok = False
        host_gpu = False
    else:
        docker_ok = docker_available() if refresh_docker else False
        host_gpu = host_gpu_devices()
        gpu_ok = (settings.torch_import_ok and settings.gpu_cuda_ok) or (
            docker_ok and host_gpu
        )

    return {
        "repo_root": str(settings.repo_root),
        "subprocess_python": str(settings.python_executable),
        "subprocess_torch_import_ok": settings.torch_import_ok,
        "gpu_available": gpu_ok,
        "gpu_cuda_native": settings.gpu_cuda_ok,
        "host_gpu_devices": host_gpu,
        "docker_available": docker_ok,
        "docker_script": str(settings.repo_root / "video-watcher-docker"),
    }


def load_settings() -> Settings:
    repo_root = Path(
        os.environ.get("VIDEO_WATCHER_REPO_ROOT", str(_default_repo_root()))
    ).expanduser().resolve()
    jobs_dir = _default_jobs_dir(repo_root)
    jobs_dir.mkdir(parents=True, exist_ok=True)
    host = os.environ.get("VIDEO_WATCHER_WEB_HOST", "127.0.0.1")
    port = int(os.environ.get("VIDEO_WATCHER_WEB_PORT", "8765"))
    fake_runner = os.environ.get("VIDEO_WATCHER_WEB_FAKE_RUNNER", "").lower() in (
        "1",
        "true",
        "yes",
    )
    py_exec, torch_ok = resolve_vw_python(repo_root)
    from vw_web.capabilities import torch_cuda_available

    gpu_cuda = False
    if torch_ok and not fake_runner:
        gpu_cuda = torch_cuda_available(py_exec)
    return Settings(
        repo_root=repo_root,
        jobs_dir=jobs_dir,
        python_executable=py_exec,
        host=host,
        port=port,
        fake_runner=fake_runner,
        torch_import_ok=torch_ok,
        gpu_cuda_ok=gpu_cuda,
    )
