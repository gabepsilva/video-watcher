"""Job workspace paths for downloads, source media, and editable outputs."""

from __future__ import annotations

import json
import mimetypes
from pathlib import Path
from urllib.parse import quote

from fastapi import HTTPException
from starlette.responses import FileResponse

EDITABLE_EXTENSIONS: frozenset[str] = frozenset(
    {"txt", "md", "markdown", "srt", "vtt", "json", "tsv", "csv", "log", "yml", "yaml"}
)

VIDEO_EXTENSIONS: frozenset[str] = frozenset(
    {"mp4", "mkv", "webm", "mov", "avi", "m4v", "flv", "ts", "m2ts"}
)

AUDIO_EXTENSIONS: frozenset[str] = frozenset({"mp3", "wav", "flac", "ogg", "opus", "m4a", "aac", "wma"})

MAX_EDIT_BYTES = 5 * 1024 * 1024

# Explicit types help browsers pick a decoder for <video>/<audio> (guess_type is often wrong).
_MEDIA_TYPES: dict[str, str] = {
    ".mp4": "video/mp4",
    ".m4v": "video/mp4",
    ".webm": "video/webm",
    ".mkv": "video/x-matroska",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".aac": "audio/aac",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".opus": "audio/ogg",
    ".flac": "audio/flac",
}


def media_type_for(path: Path) -> str:
    explicit = _MEDIA_TYPES.get(path.suffix.lower())
    if explicit:
        return explicit
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def serve_media_file(path: Path, *, as_download: bool = False) -> FileResponse:
    """
    Stream a job file for browser playback or download.

    Default is ``inline`` so HTML5 ``<video>`` / ``<audio>`` can play the URL.
    Starlette's ``FileResponse`` defaults to ``attachment``, which breaks embedding.
    """
    disposition = "attachment" if as_download else "inline"
    return FileResponse(
        path,
        media_type=media_type_for(path),
        filename=path.name,
        content_disposition_type=disposition,
    )


def extension_of(name: str) -> str:
    if "." not in name:
        return ""
    return name.rsplit(".", 1)[-1].lower()


def is_editable(name: str) -> bool:
    return extension_of(name) in EDITABLE_EXTENSIONS


def is_video(name: str) -> bool:
    return extension_of(name) in VIDEO_EXTENSIONS


def is_audio(name: str) -> bool:
    return extension_of(name) in AUDIO_EXTENSIONS


def artifact_name_allowed(name: str) -> bool:
    """Reject path traversal; allow spaces and punctuation in real media filenames."""
    if not name or name in {".", ".."}:
        return False
    if "\0" in name or "/" in name or "\\" in name:
        return False
    return True


def artifact_file_url(job_id: str, name: str) -> str:
    """URL path for GET/PUT artifact (percent-encoded basename)."""
    return f"/api/jobs/{job_id}/files/{quote(name, safe='')}"


def artifact_file(job_work_dir: Path, name: str) -> Path:
    if not artifact_name_allowed(name):
        raise HTTPException(status_code=404, detail="invalid artifact name")
    out_dir = (job_work_dir / "out").resolve()
    candidate = (out_dir / name).resolve()
    try:
        candidate.relative_to(out_dir)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="not found") from exc
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="not found")
    return candidate


def job_input_file(job_work_dir: Path) -> Path | None:
    meta_path = job_work_dir / "job.json"
    if not meta_path.is_file():
        return None
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    raw = meta.get("input_path")
    if not raw:
        return None
    path = Path(raw).resolve()
    root = job_work_dir.resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    if not path.is_file():
        return None
    return path


def source_media_payload(job_id: str, job_work_dir: Path) -> dict[str, str] | None:
    path = job_input_file(job_work_dir)
    if path is None:
        return None
    return {"name": path.name, "url": f"/api/jobs/{job_id}/input"}
