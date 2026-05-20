"""Browser phrase audio → transcript via in-container ``python -m vw``."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from vw_web.config import Settings
from vw_web.runner import SubprocessVwJobRunner


async def transcribe_audio_file(
    path: Path,
    *,
    settings: Settings,
    model: str,
    language: str | None,
    gpu: bool,
) -> dict[str, Any]:
    """Transcribe one uploaded clip inside the API container."""
    loop = asyncio.get_running_loop()
    if settings.fake_runner:
        return {"text": "fake mic phrase", "language": language or "en"}
    return await loop.run_in_executor(
        None,
        lambda: _transcribe_subprocess_sync(
            path,
            settings=settings,
            model=model,
            language=language,
            gpu=gpu,
        ),
    )


def _transcribe_subprocess_sync(
    path: Path,
    *,
    settings: Settings,
    model: str,
    language: str | None,
    gpu: bool,
) -> dict[str, Any]:
    out_dir = path.parent / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    logs: list[str] = []

    def log_line(msg: str) -> None:
        logs.append(msg)

    runner = SubprocessVwJobRunner()
    code = runner.run(
        job_id="mic",
        settings=settings,
        output_dir=out_dir,
        input_path=path,
        youtube_url=None,
        model=model,
        language=language,
        formats="txt",
        gpu=gpu,
        verbose=False,
        summary=False,
        summary_model="gemma-4-e4b",
        log_line=log_line,
    )
    if code != 0:
        tail = "\n".join(logs[-20:])
        raise RuntimeError(f"Mic transcribe failed (exit {code})\n{tail}")

    txt_path = out_dir / f"{path.stem}.txt"
    if not txt_path.is_file():
        raise RuntimeError(f"expected transcript missing: {txt_path}")

    text = txt_path.read_text(encoding="utf-8").strip()
    return {"text": text, "language": language}
