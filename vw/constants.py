"""Shared constants."""

from __future__ import annotations

MEDIA_EXTENSIONS: frozenset[str] = frozenset(
    {
        "mp4",
        "mkv",
        "webm",
        "mov",
        "avi",
        "m4v",
        "flv",
        "ts",
        "m2ts",
        "mp3",
        "wav",
        "flac",
        "ogg",
        "opus",
        "m4a",
        "aac",
        "wma",
    }
)

OUTPUT_EXTENSIONS: tuple[str, ...] = ("srt", "vtt", "txt", "json", "tsv")

WHISPER_MODELS: tuple[str, ...] = ("tiny", "base", "small", "medium", "large")

# llama.cpp summary models (GGUF). More keys can be added later.
DEFAULT_SUMMARY_MODEL = "gemma-4-e4b"

SUMMARY_MODELS: dict[str, dict[str, str]] = {
    "gemma-4-e4b": {
        "repo": "ggml-org/gemma-4-E4B-it-GGUF",
        "filename": "gemma-4-E4B-it-Q4_K_M.gguf",
        # Use the chat template embedded in the GGUF (Gemma 4 needs this).
        "chat_template": "",
        "label": "Gemma 4 E4B Instruct (Q4_K_M)",
    },
}
