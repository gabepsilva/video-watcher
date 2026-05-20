"""Model and runtime cache paths."""

from __future__ import annotations

import os
from pathlib import Path


def default_cache_root() -> Path:
    return Path(os.environ.get("VIDEO_WATCHER_CACHE", Path.home() / ".video_watcher"))


def setup_cache() -> Path:
    """Ensure cache root exists and point Whisper/PyTorch caches at it."""
    root = default_cache_root()
    root.mkdir(parents=True, exist_ok=True)
    os.environ["XDG_CACHE_HOME"] = str(root)
    return root


def whisper_model_dir() -> Path:
    return setup_cache() / "whisper"


def whisper_checkpoint_path(model_name: str) -> Path:
    """Path where openai-whisper stores a named model checkpoint."""
    from whisper import _MODELS

    if model_name not in _MODELS:
        raise ValueError(f"Unknown Whisper model: {model_name!r}")
    url = _MODELS[model_name]
    return whisper_model_dir() / Path(url).name


def llama_model_dir() -> Path:
    return setup_cache() / "llama"
