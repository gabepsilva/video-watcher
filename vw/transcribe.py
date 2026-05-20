"""Transcription orchestration."""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import torch
import whisper
from whisper.audio import load_audio
from whisper.utils import get_writer

from vw.cache import setup_cache, whisper_checkpoint_path, whisper_model_dir
from vw.constants import OUTPUT_EXTENSIONS
from vw.progress import (
    nice_progress,
    print_file_header,
    whisper_model_load_progress,
)

# Approximate download sizes (first run only).
_WHISPER_DOWNLOAD_SIZE: dict[str, str] = {
    "tiny": "72 MB",
    "base": "140 MB",
    "small": "460 MB",
    "medium": "1.4 GB",
    "large": "2.9 GB",
    "turbo": "1.5 GB",
}


def _status(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def _announce_whisper_model(model_name: str) -> None:
    cache_dir = whisper_model_dir()
    checkpoint = whisper_checkpoint_path(model_name)
    if checkpoint.is_file() and checkpoint.stat().st_size > 0:
        _status(f"Loading Whisper model “{model_name}” from {cache_dir} …")
        return
    size = _WHISPER_DOWNLOAD_SIZE.get(model_name, "")
    size_hint = f" ({size})" if size else ""
    _status(
        f"Downloading Whisper model “{model_name}”{size_hint} to {cache_dir} "
        "(first run only) …"
    )


def resolve_device(use_gpu: bool) -> str:
    if use_gpu and torch.cuda.is_available():
        return "cuda"
    if use_gpu:
        print("Warning: --gpu requested but no GPU visible; using CPU.", file=sys.stderr)
    return "cpu"


def release_whisper_gpu(model=None) -> None:
    """Free Whisper weights on GPU before another GPU consumer (e.g. llama-cli)."""
    import gc

    if model is not None:
        del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def load_whisper_model(model_name: str, device: str):
    """Load Whisper model (downloads on first use)."""
    setup_cache()
    _announce_whisper_model(model_name)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
        if device == "cpu":
            warnings.filterwarnings(
                "ignore", message="Performing inference on CPU when CUDA is available"
            )
        with whisper_model_load_progress(model_name):
            return whisper.load_model(
                model_name,
                device=device,
                download_root=str(whisper_model_dir()),
            )


def audio_duration_seconds(path: Path) -> float:
    audio = load_audio(str(path))
    return len(audio) / 16000.0


def transcribe_file(
    path: Path,
    *,
    model_name: str,
    output_dir: Path,
    output_format: str,
    language: str | None,
    device: str,
    verbose: bool,
    release_gpu: bool = False,
) -> dict:
    _status(f"Decoding audio ({path.name}) …")
    setup_cache()
    duration = audio_duration_seconds(path)

    if not verbose:
        print_file_header(path, model_name, device, duration)

    model = load_whisper_model(model_name, device)

    transcribe_kwargs: dict = {
        "temperature": 0,
        "verbose": verbose,
    }
    if language:
        transcribe_kwargs["language"] = language

    if verbose:
        result = whisper.transcribe(model, str(path), **transcribe_kwargs)
    else:
        with nice_progress(path.stem):
            result = whisper.transcribe(model, str(path), **transcribe_kwargs)

    writer = get_writer(output_format, str(output_dir))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        writer(result, str(path))

    if release_gpu:
        _status("Releasing Whisper from GPU …")
        release_whisper_gpu(model)

    return result


def list_output_files(output_dir: Path, stem: str) -> list[Path]:
    return [output_dir / f"{stem}.{ext}" for ext in OUTPUT_EXTENSIONS]
