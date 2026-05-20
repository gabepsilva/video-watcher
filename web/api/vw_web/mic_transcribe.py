"""Whisper inference for browser-uploaded phrase audio (cached model per process)."""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from typing import Any

_model_lock = threading.Lock()
_cache: dict[tuple[str, str], Any] = {}


async def transcribe_audio_file(
    path: Path,
    *,
    model: str,
    language: str | None,
    gpu: bool,
) -> dict[str, Any]:
    """Run Whisper on a local media file (wav/webm/…) and return text + detected language."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        lambda: _transcribe_sync(path, model=model, language=language, gpu=gpu),
    )


def _transcribe_sync(path: Path, *, model: str, language: str | None, gpu: bool) -> dict[str, Any]:
    import whisper

    from vw.transcribe import load_whisper_model, resolve_device

    device = resolve_device(gpu)
    key = (model, device)
    with _model_lock:
        wmodel = _cache.get(key)
        if wmodel is None:
            wmodel = load_whisper_model(model, device)
            _cache[key] = wmodel
        kwargs: dict[str, Any] = {"temperature": 0, "verbose": False}
        if language:
            kwargs["language"] = language
        result = whisper.transcribe(wmodel, str(path), **kwargs)

    text = (result.get("text") or "").strip()
    return {"text": text, "language": result.get("language")}
