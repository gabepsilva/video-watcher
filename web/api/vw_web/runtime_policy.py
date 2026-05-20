"""Web console runs only inside Docker Compose (in-container ``python -m vw``)."""

from __future__ import annotations

import os

from fastapi import HTTPException

CONTAINER_REQUIRED_MSG = (
    "This console runs only via Docker Compose. From the repository root run: docker compose up --build"
)


def is_container_runtime() -> bool:
    return os.environ.get("VIDEO_WATCHER_RUNTIME", "").strip().lower() == "container"


def require_container_runtime(
    *,
    container_runtime: bool,
    fake_runner: bool,
    torch_ok: bool,
) -> None:
    if fake_runner:
        return
    if not container_runtime:
        raise HTTPException(status_code=503, detail=CONTAINER_REQUIRED_MSG)
    if not torch_ok:
        raise HTTPException(
            status_code=503,
            detail="Whisper/PyTorch is not ready in the API container. Rebuild: docker compose build --no-cache api",
        )


def resolve_container_ready(
    *,
    container_runtime: bool,
    fake_runner: bool,
    torch_ok: bool,
) -> None:
    """Validate the API can run real transcription jobs (raises HTTP 503 otherwise)."""
    require_container_runtime(
        container_runtime=container_runtime,
        fake_runner=fake_runner,
        torch_ok=torch_ok,
    )
