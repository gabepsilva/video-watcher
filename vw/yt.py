"""YouTube URLs: captions via yt-dlp, transcript API fallback, then Whisper on audio."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from collections.abc import Callable
from pathlib import Path
from urllib.parse import parse_qs, urlparse


def extract_video_id(url: str) -> str | None:
    """Return 11-character YouTube video id or None."""
    u = url.strip()
    parsed = urlparse(u)
    host = (parsed.netloc or "").lower()
    if "youtu.be" in host:
        seg = (parsed.path or "").strip("/").split("/")[0]
        return seg if len(seg) == 11 and re.match(r"^[A-Za-z0-9_-]{11}$", seg) else None
    if "youtube.com" in host or "youtube-nocookie.com" in host:
        if parsed.path == "/watch":
            v = parse_qs(parsed.query).get("v", [""])[0]
            if len(v) == 11 and re.match(r"^[A-Za-z0-9_-]{11}$", v):
                return v
        m = re.match(r"^/embed/([A-Za-z0-9_-]{11})", parsed.path or "")
        if m:
            return m.group(1)
        m = re.match(r"^/shorts/([A-Za-z0-9_-]{11})", parsed.path or "")
        if m:
            return m.group(1)
    return None


def is_youtube_url(text: str) -> bool:
    return extract_video_id(text) is not None


def ytdlp_command() -> list[str]:
    exe = shutil.which("yt-dlp")
    if exe:
        return [exe]
    return [sys.executable, "-m", "yt_dlp"]


def _srt_timestamp_to_seconds(ts: str) -> float:
    ts = ts.strip().replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(ts)


def parse_srt(content: str) -> list[dict]:
    """Parse SRT into segments: {start, end, text} (seconds)."""
    content = content.replace("\r\n", "\n").strip()
    if not content:
        return []
    blocks = re.split(r"\n\s*\n+", content)
    segments: list[dict] = []
    for block in blocks:
        lines = block.split("\n")
        if not lines:
            continue
        i = 0
        if lines[0].strip().isdigit():
            i = 1
        if i >= len(lines) or "-->" not in lines[i]:
            continue
        left, _, right = lines[i].partition("-->")
        try:
            start = _srt_timestamp_to_seconds(left)
            end = _srt_timestamp_to_seconds(right)
        except ValueError:
            continue
        text = "\n".join(lines[i + 1 :]).strip()
        if text:
            segments.append({"start": start, "end": end, "text": text})
    return segments


def _pick_srt_file(work_dir: Path, video_id: str, preferred_lang: str) -> Path | None:
    exact = work_dir / f"{video_id}.{preferred_lang}.srt"
    if exact.is_file():
        return exact
    candidates = sorted(work_dir.glob(f"{video_id}*.srt"))
    return candidates[0] if candidates else None


def try_ytdlp_subtitles(url: str, video_id: str, work_dir: Path, sub_lang: str) -> list[dict] | None:
    """Download subtitles with yt-dlp; return segments or None."""
    cmd = ytdlp_command() + [
        "--no-warnings",
        "--skip-download",
        "--write-sub",
        "--write-auto-sub",
        "--sub-langs",
        sub_lang,
        "--convert-subs",
        "srt",
        "-o",
        str(work_dir / "%(id)s"),
        url,
    ]
    try:
        r = subprocess.run(
            cmd,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=600,
        )
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return None
    srt_path = _pick_srt_file(work_dir, video_id, sub_lang)
    if srt_path is None or not srt_path.is_file():
        return None
    try:
        segments = parse_srt(srt_path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return None
    return segments if segments else None


def try_transcript_api(video_id: str, languages: tuple[str, ...]) -> list[dict] | None:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None
    api = YouTubeTranscriptApi()
    try:
        ft = api.fetch(video_id, languages=languages)
    except Exception:
        return None
    segments: list[dict] = []
    for snip in ft:
        start = float(snip.start)
        dur = float(snip.duration)
        text = (snip.text or "").strip()
        if text:
            segments.append({"start": start, "end": start + dur, "text": text})
    return segments if segments else None


def try_ytdlp_audio_file(url: str, video_id: str, work_dir: Path) -> Path | None:
    out_tmpl = str(work_dir / f"{video_id}.%(ext)s")
    cmd = ytdlp_command() + [
        "--no-warnings",
        "-f",
        "bestaudio/best",
        "--no-playlist",
        "-o",
        out_tmpl,
        url,
    ]
    try:
        r = subprocess.run(
            cmd,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=3600,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    for p in work_dir.iterdir():
        if p.is_file() and p.stem == video_id and p.suffix.lower() in (
            ".webm",
            ".m4a",
            ".opus",
            ".mp3",
            ".ogg",
            ".wav",
        ):
            return p
    return None


def _language_priority(cli_language: str | None) -> tuple[str, ...]:
    if not cli_language:
        return ("en",)
    c = cli_language.strip().lower()
    if c == "en":
        return ("en",)
    return (c, "en")


def _sub_lang_for_ytdlp(cli_language: str | None) -> str:
    """Single yt-dlp --sub-langs token (avoids requesting many translations → 429)."""
    if not cli_language:
        return "en"
    return cli_language.strip().lower()


def _status_stderr(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def fetch_youtube_segments(
    url: str,
    *,
    cli_language: str | None,
    status: Callable[[str], None] | None = None,
) -> tuple[str, list[dict], str]:
    """
    Return (video_id, segments, source) where source is ytdlp|transcript_api|none.
    segments empty if none — caller may try Whisper on audio.
    """
    emit = status or _status_stderr
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"not a recognized YouTube URL: {url}")

    langs = _language_priority(cli_language)
    sub_lang = _sub_lang_for_ytdlp(cli_language)

    with tempfile.TemporaryDirectory(prefix="vw-yt-") as tmp:
        work = Path(tmp)
        emit(f"YouTube {video_id}: trying yt-dlp subtitles ({sub_lang}) …")
        segs = try_ytdlp_subtitles(url, video_id, work, sub_lang)
        if segs:
            return video_id, segs, "ytdlp"

        emit("yt-dlp subtitles unavailable; trying youtube-transcript-api …")
        segs = try_transcript_api(video_id, langs)
        if segs:
            return video_id, segs, "transcript_api"

    return video_id, [], "none"


def _normalize_cue_text(text: str) -> str:
    """Single-line cue text safe for TSV / JSON; keeps words readable."""
    t = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    t = unicodedata.normalize("NFKC", t)
    t = " ".join(t.split())
    return t.strip()


def _dedupe_consecutive_identical(segments: list[dict]) -> list[dict]:
    """Merge back-to-back cues with the same normalized text (belt-and-suspenders)."""
    out: list[dict] = []
    for s in segments:
        t = _normalize_cue_text(s.get("text") or "")
        if not t:
            continue
        try:
            start = float(s["start"])
            end = float(s["end"])
        except (TypeError, ValueError):
            continue
        if end < start:
            end = start
        if out and _normalize_cue_text(out[-1]["text"]) == t:
            out[-1]["end"] = max(float(out[-1]["end"]), end)
            continue
        out.append({"start": start, "end": end, "text": t})
    return out


def _rolling_caption_merge(segments: list[dict]) -> list[dict]:
    """
    YouTube auto-captions often emit duplicate lines and rolling prefixes
    ("hello" → "hello world" → "hello world today") as many tiny cues.
    Merge those so TXT / writers are readable and TSV rows stay one line.
    """
    out: list[dict] = []
    for s in segments:
        t = _normalize_cue_text(s.get("text") or "")
        if not t:
            continue
        try:
            start = float(s["start"])
            end = float(s["end"])
        except (TypeError, ValueError):
            continue
        if end < start:
            end = start
        if not out:
            out.append({"start": start, "end": end, "text": t})
            continue
        prev = out[-1]
        pt = prev["text"]
        if t == pt:
            prev["end"] = max(prev["end"], end)
            continue
        if t.startswith(pt) and len(t) > len(pt):
            extra = t[len(pt) :]
            if extra.startswith(
                (" ", ",", ".", "!", "?", ":", ";", "'", '"', "(", "-", "…", "\n")
            ) or pt.endswith((" ", "-", "…", ".", ",", "!", "?", ":")):
                prev["text"] = t
                prev["end"] = max(prev["end"], end)
                continue
        out.append({"start": start, "end": end, "text": t})
    return out


def segments_to_whisper_result(segments: list[dict], language: str | None) -> dict:
    cleaned: list[dict] = []
    for s in segments:
        txt = _normalize_cue_text(s.get("text") or "")
        if not txt:
            continue
        cleaned.append(
            {
                "start": float(s["start"]),
                "end": float(s["end"]),
                "text": txt,
            }
        )
    return {
        "text": " ".join(s["text"] for s in cleaned),
        "segments": [
            {
                "id": i,
                "start": s["start"],
                "end": s["end"],
                "text": s["text"],
            }
            for i, s in enumerate(cleaned)
        ],
        "language": (language or "en").lower(),
    }


def write_caption_outputs(
    segments: list[dict],
    *,
    video_id: str,
    output_dir: Path,
    output_format: str,
    language: str | None,
) -> None:
    from vw.transcribe import write_whisper_result

    merged = _dedupe_consecutive_identical(_rolling_caption_merge(segments))
    result = segments_to_whisper_result(merged, language)
    dummy_media = output_dir / f"{video_id}.mp4"
    write_whisper_result(result, output_format, output_dir, dummy_media)
