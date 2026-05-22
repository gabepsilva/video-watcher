"""Dev Compose stack: slim images, bind mounts, live reload."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_dev_compose_and_dockerfiles_exist() -> None:
    assert (ROOT / "docker-compose.dev.yml").is_file()
    assert (ROOT / "web/Dockerfile.api.dev").is_file()
    assert (ROOT / "web/Dockerfile.ui.dev").is_file()
    assert (ROOT / "web/scripts/docker-dev-api-entrypoint.sh").is_file()


def test_dev_api_entrypoint_uses_reload() -> None:
    text = (ROOT / "web/scripts/docker-dev-api-entrypoint.sh").read_text(encoding="utf-8")
    assert "--reload" in text
    assert "install-local" in text
    assert "/repo/.venv" in text or ".venv/bin/python" in text


def test_dev_gpu_compose_overlay_exists() -> None:
    assert (ROOT / "docker-compose.dev.gpu.yml").is_file()
    text = (ROOT / "docker-compose.dev.gpu.yml").read_text(encoding="utf-8")
    assert "Dockerfile.api.dev.rocm" in text
    assert "/dev/kfd" in text
    assert "VIDEO_WATCHER_DEV_GPU" in text


def test_dev_entrypoint_supports_gpu_venv() -> None:
    text = (ROOT / "web/scripts/docker-dev-api-entrypoint.sh").read_text(encoding="utf-8")
    assert "ensure_gpu_venv" in text
    assert "system-site-packages" in text


def test_dev_compose_bind_mounts_repo_and_cache() -> None:
    text = (ROOT / "docker-compose.dev.yml").read_text(encoding="utf-8")
    assert ".:/repo" in text
    assert ".video_watcher_web/jobs" in text
    assert "Dockerfile.api.dev" in text
    assert "Dockerfile.ui.dev" in text
    assert "vw-ui-node-modules" in text
    assert "service_healthy" in text
    assert '${UID:-1000}:${GID:-1000}' in text or "${UID" in text
