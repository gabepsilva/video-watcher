"""Live microphone transcription (experimental)."""

from __future__ import annotations

import contextlib
import io
import sys
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import whisper
from whisper.audio import SAMPLE_RATE

from vw.transcribe import _status, load_whisper_model

# Skip near-silent chunks (typical speech peaks are ~0.05–0.5).
_SILENCE_PEAK = 0.001


def _input_sample_rate(sd) -> int:
    try:
        info = sd.query_devices(kind="input")
        return int(info["default_samplerate"])
    except Exception:
        return SAMPLE_RATE


def _resample(audio: np.ndarray, orig_sr: int, target_sr: int = SAMPLE_RATE) -> np.ndarray:
    if orig_sr == target_sr or len(audio) == 0:
        return audio.astype(np.float32, copy=False)
    duration = len(audio) / orig_sr
    target_len = int(round(duration * target_sr))
    if target_len <= 0:
        return np.array([], dtype=np.float32)
    x_old = np.linspace(0.0, duration, num=len(audio), endpoint=False)
    x_new = np.linspace(0.0, duration, num=target_len, endpoint=False)
    return np.interp(x_new, x_old, audio).astype(np.float32)


def listen_microphone(
    *,
    model_name: str,
    device: str,
    language: str | None,
    chunk_seconds: float,
    output_path: Path | None,
) -> None:
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise ImportError(
            "Microphone mode requires sounddevice. Install with:\n"
            f"  {sys.executable} -m pip install sounddevice"
        ) from exc

    if not 1.0 <= chunk_seconds <= 30.0:
        raise ValueError("--mic-chunk must be between 1 and 30 seconds")

    input_sr = _input_sample_rate(sd)
    _status(
        f"Microphone mode — {chunk_seconds:g}s chunks "
        f"(record {input_sr} Hz → Whisper {SAMPLE_RATE} Hz, Ctrl+C to stop)"
    )
    try:
        device_name = sd.query_devices(kind="input")["name"]
        _status(f"Input device: {device_name}")
    except Exception:
        pass

    model = load_whisper_model(model_name, device)

    transcribe_kwargs: dict = {
        "temperature": 0,
        "verbose": False,
        "condition_on_previous_text": False,
    }
    if language:
        transcribe_kwargs["language"] = language

    chunk_frames = int(chunk_seconds * input_sr)
    outfile = None
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        outfile = output_path.open("a", encoding="utf-8")
        _status(f"Appending transcript to {output_path}")

    print("Listening…", file=sys.stderr, flush=True)

    try:
        while True:
            block = sd.rec(
                chunk_frames,
                samplerate=input_sr,
                channels=1,
                dtype=np.float32,
            )
            sd.wait()
            audio = _resample(block.flatten(), input_sr)
            if float(np.abs(audio).max()) < _SILENCE_PEAK:
                continue

            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
                warnings.filterwarnings(
                    "ignore", message="Performing inference on CPU when CUDA is available"
                )
                # Whisper/tqdm writes progress bars to stderr; keep mic output clean.
                with contextlib.redirect_stderr(io.StringIO()):
                    result = whisper.transcribe(model, audio, **transcribe_kwargs)

            text = result.get("text", "").strip()
            if not text:
                continue

            print(text, flush=True)
            if outfile is not None:
                outfile.write(text + "\n")
                outfile.flush()
    except KeyboardInterrupt:
        _status("\nStopped.")
    finally:
        if outfile is not None:
            outfile.close()


def default_mic_output_path(output_dir: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return output_dir / f"mic-{stamp}.txt"
