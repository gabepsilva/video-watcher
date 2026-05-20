"""Input media validation."""

from __future__ import annotations

import subprocess
from pathlib import Path

from vw.constants import MEDIA_EXTENSIONS


def extension(path: Path) -> str | None:
    suffix = path.suffix.lower().lstrip(".")
    return suffix or None


def mime_type(path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["file", "-b", "--mime-type", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def is_supported_media(path: Path) -> bool:
    if not path.is_file():
        return False
    ext = extension(path)
    if ext and ext in MEDIA_EXTENSIONS:
        return True
    mime = mime_type(path)
    return mime is not None and (mime.startswith("audio/") or mime.startswith("video/"))


def format_media_list() -> str:
    video = "mp4 mkv webm mov avi m4v flv ts m2ts"
    audio = "mp3 wav flac ogg opus m4a aac wma"
    return (
        "Accepted input files (decoded by ffmpeg):\n\n"
        f"  Video:  {video}\n"
        f"  Audio:  {audio}\n\n"
        "Other files recognized as audio/* or video/* (via file(1)) are also accepted.\n"
        "Anything ffmpeg can decode will work even if not listed above."
    )
