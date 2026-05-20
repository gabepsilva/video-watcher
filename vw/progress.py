"""Readable tqdm progress for Whisper transcription and model downloads."""

from __future__ import annotations

import contextlib
from typing import Iterator
from unittest.mock import patch

import tqdm
from whisper.audio import HOP_LENGTH, SAMPLE_RATE

FRAMES_TO_SECONDS = HOP_LENGTH / SAMPLE_RATE


def _format_duration(seconds: float) -> str:
    seconds = max(0.0, seconds)
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:d}:{secs:02d}"


class TranscribeProgressBar(tqdm.tqdm):
    """Whisper frame updates shown as audio timeline (seconds)."""

    def __init__(self, *, total_frames: int, label: str = "", **kwargs):
        kwargs.pop("unit", None)
        kwargs.pop("total", None)
        duration = total_frames * FRAMES_TO_SECONDS
        desc = (label[:44] + "…") if len(label) > 45 else label
        super().__init__(
            total=duration if duration > 0 else None,
            unit="s",
            desc=desc,
            bar_format="{desc}: {percentage:3.0f}%|{bar:24}| {n:.0f}/{total:.0f}s [{elapsed}<{remaining}]",
            dynamic_ncols=True,
            **kwargs,
        )
        self._frame_scale = FRAMES_TO_SECONDS

    def update(self, n: float = 1) -> bool | None:
        return super().update(n * self._frame_scale)


class DownloadProgressBar(tqdm.tqdm):
    """Model download progress."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("unit", "B")
        kwargs.setdefault("unit_scale", True)
        kwargs.setdefault("unit_divisor", 1024)
        super().__init__(
            *args,
            desc="Model",
            bar_format="{desc}: {percentage:3.0f}%|{bar:20}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
            dynamic_ncols=True,
            **kwargs,
        )


def _tqdm_factory(label: str):
    def constructor(*args, **kwargs):
        if kwargs.get("disable"):
            return tqdm.tqdm(*args, **kwargs)

        unit = kwargs.get("unit")
        if unit == "frames":
            total_frames = int(kwargs.pop("total", 0) or 0)
            kwargs.pop("unit", None)
            return TranscribeProgressBar(total_frames=total_frames, label=label, **kwargs)

        if unit == "iB" or kwargs.get("unit_scale"):
            return DownloadProgressBar(*args, **kwargs)

        return tqdm.tqdm(*args, **kwargs)

    return constructor


@contextlib.contextmanager
def nice_progress(label: str) -> Iterator[None]:
    """Patch Whisper's tqdm usage for human-friendly bars."""
    factory = _tqdm_factory(label)
    with contextlib.ExitStack() as stack:
        stack.enter_context(patch("whisper.transcribe.tqdm.tqdm", factory))
        stack.enter_context(patch("whisper.tqdm", factory))
        yield


def print_file_header(path, model: str, device: str, duration_sec: float) -> None:
    from pathlib import Path

    name = Path(path).name
    print(f"\n▸ {name}", flush=True)
    print(
        f"  model={model}  device={device}  duration≈{_format_duration(duration_sec)}",
        flush=True,
    )
