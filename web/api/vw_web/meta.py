"""Static metadata for the UI (mirrors ``vw.constants``)."""

from __future__ import annotations

from vw.constants import OUTPUT_EXTENSIONS, SUMMARY_MODELS, WHISPER_MODELS

# ISO 639-1 codes — UI datalist presets (free text still allowed).
POPULAR_LANGUAGES: tuple[str, ...] = ("en", "es", "fr", "de", "pt")

# Common ``-f`` values for the formats combobox.
FORMAT_PRESETS: tuple[str, ...] = (
    "all",
    "srt",
    "vtt",
    "txt",
    "srt,vtt,txt",
)


def meta_payload() -> dict:
    return {
        "whisper_models": list(WHISPER_MODELS),
        "summary_models": sorted(SUMMARY_MODELS.keys()),
        "output_formats": list(OUTPUT_EXTENSIONS),
        "popular_languages": list(POPULAR_LANGUAGES),
        "format_presets": list(FORMAT_PRESETS),
    }
