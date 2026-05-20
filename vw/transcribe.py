"""Transcription orchestration."""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import torch
import whisper
from whisper.audio import load_audio
from whisper.utils import get_writer

from vw.cache import setup_cache, whisper_model_dir
from vw.constants import OUTPUT_EXTENSIONS
from vw.progress import nice_progress, print_file_header


def resolve_device(use_gpu: bool) -> str:
    if use_gpu and torch.cuda.is_available():
        return "cuda"
    if use_gpu:
        print("Warning: --gpu requested but no GPU visible; using CPU.", file=sys.stderr)
    return "cpu"


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
) -> dict:
    setup_cache()
    duration = audio_duration_seconds(path)

    if not verbose:
        print_file_header(path, model_name, device, duration)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
        if device == "cpu":
            warnings.filterwarnings(
                "ignore", message="Performing inference on CPU when CUDA is available"
            )
        model = whisper.load_model(
            model_name,
            device=device,
            download_root=str(whisper_model_dir()),
        )

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

    return result


def list_output_files(output_dir: Path, stem: str) -> list[Path]:
    return [output_dir / f"{stem}.{ext}" for ext in OUTPUT_EXTENSIONS]
