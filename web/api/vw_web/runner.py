"""Run `python -m vw` as a subprocess (same contract as ./video-watcher)."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from vw_web.config import Settings


def _formats_for_cli(formats: str, *, summary: bool) -> str:
    """Mirror ``vw/cli.py``: summary needs a ``.txt`` transcript."""
    output_format = formats.strip() or "all"
    if summary and output_format != "all" and "txt" not in output_format.split(","):
        return f"{output_format},txt" if output_format else "txt"
    return output_format


class VwJobRunner(Protocol):
    def run(
        self,
        *,
        job_id: str,
        settings: Settings,
        output_dir: Path,
        input_path: Path | None,
        youtube_url: str | None,
        model: str,
        language: str | None,
        formats: str,
        gpu: bool,
        verbose: bool,
        summary: bool,
        summary_model: str,
        log_line: Callable[[str], None],
    ) -> int:
        """Return process exit code."""


class FakeVwJobRunner:
    """Fast, deterministic runner for API tests (no Whisper)."""

    def run(
        self,
        *,
        job_id: str,
        settings: Settings,
        output_dir: Path,
        input_path: Path | None,
        youtube_url: str | None,
        model: str,
        language: str | None,
        formats: str,
        gpu: bool,
        verbose: bool,
        summary: bool,
        summary_model: str,
        log_line: Callable[[str], None],
    ) -> int:
        _ = (
            job_id,
            settings,
            model,
            language,
            formats,
            gpu,
            verbose,
            summary,
            summary_model,
            youtube_url,
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        stem = input_path.stem if input_path else "fake"
        log_line("video-watcher (fake runner): starting …")
        (output_dir / f"{stem}.txt").write_text("fake transcript\n", encoding="utf-8")
        (output_dir / f"{stem}.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nfake\n", encoding="utf-8")
        log_line("Done:")
        log_line(f"  {output_dir / f'{stem}.txt'}")
        return 0


class SubprocessVwJobRunner:
    """Invokes the real `vw` CLI in a subprocess."""

    def run(
        self,
        *,
        job_id: str,
        settings: Settings,
        output_dir: Path,
        input_path: Path | None,
        youtube_url: str | None,
        model: str,
        language: str | None,
        formats: str,
        gpu: bool,
        verbose: bool,
        summary: bool,
        summary_model: str,
        log_line: Callable[[str], None],
    ) -> int:
        _ = job_id
        log_line(f"video-watcher (web): subprocess {settings.python_executable}")
        cli_formats = _formats_for_cli(formats, summary=summary)
        cmd: list[str] = [
            str(settings.python_executable),
            "-m",
            "vw",
            "-m",
            model,
            "-f",
            cli_formats,
            "-o",
            str(output_dir),
        ]
        if gpu:
            cmd.append("--gpu")
        if verbose:
            cmd.append("--verbose")
        if language:
            cmd.extend(["-l", language])
        if summary:
            cmd.append("--summary")
            cmd.extend(["--summary-model", summary_model])
        if youtube_url:
            cmd.append("--yt")
            cmd.append(youtube_url)
        else:
            if input_path is None:
                raise ValueError("file job requires input_path")
            cmd.append(str(input_path))

        env = os.environ.copy()
        env["PYTHONPATH"] = str(settings.repo_root)
        env["PYTHONUNBUFFERED"] = "1"

        proc = subprocess.Popen(
            cmd,
            cwd=str(settings.repo_root),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert proc.stderr is not None
        for line in proc.stderr:
            log_line(line.rstrip("\n"))
        return int(proc.wait())


class DockerVwJobRunner:
    """Runs ``./video-watcher-docker`` with container paths under ``/data``."""

    def run(
        self,
        *,
        job_id: str,
        settings: Settings,
        output_dir: Path,
        input_path: Path | None,
        youtube_url: str | None,
        model: str,
        language: str | None,
        formats: str,
        gpu: bool,
        verbose: bool,
        summary: bool,
        summary_model: str,
        log_line: Callable[[str], None],
    ) -> int:
        _ = job_id
        script = settings.repo_root / "video-watcher-docker"
        if not script.is_file():
            raise FileNotFoundError(f"video-watcher-docker not found: {script}")

        output_dir.mkdir(parents=True, exist_ok=True)
        cli_formats = _formats_for_cli(formats, summary=summary)

        cmd: list[str] = [str(script), "-m", model, "-f", cli_formats, "-o", "/data/out"]
        if gpu:
            cmd.append("--gpu")
        if verbose:
            cmd.append("--verbose")
        if language:
            cmd.extend(["-l", language])
        if summary:
            cmd.append("--summary")
            cmd.extend(["--summary-model", summary_model])
        if youtube_url:
            cmd.append("--yt")
            cmd.append(youtube_url)
        else:
            if input_path is None:
                raise ValueError("file job requires input_path")
            cmd.append(str(input_path.resolve()))

        log_line(f"video-watcher (web): docker {script.name}")
        log_line(f"  output (container): /data/out → {output_dir}")

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        proc = subprocess.Popen(
            cmd,
            cwd=str(settings.repo_root),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert proc.stderr is not None
        for line in proc.stderr:
            log_line(line.rstrip("\n"))
        return int(proc.wait())


def runner_for_job(
    settings: Settings,
    *,
    use_docker: bool,
) -> VwJobRunner:
    if settings.fake_runner:
        return FakeVwJobRunner()
    if use_docker:
        return DockerVwJobRunner()
    return SubprocessVwJobRunner()
