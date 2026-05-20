"""Command-line interface."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from vw.cache import default_cache_root, setup_cache
from vw.constants import (
    DEFAULT_SUMMARY_MODEL,
    OUTPUT_EXTENSIONS,
    SUMMARY_MODELS,
    WHISPER_MODELS,
)
from vw.env_docs import local_env_epilog
from vw.media import format_media_list, is_supported_media


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="video-watcher",
        description="Transcribe audio/video to captions (SRT, VTT, TXT, …) via local Whisper.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=local_env_epilog(),
    )
    parser.add_argument(
        "media",
        nargs="*",
        help="audio or video file(s) to transcribe",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        metavar="DIR",
        help="write all outputs here (default: same directory as each input)",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=os.environ.get("WHISPER_MODEL", "base"),
        choices=WHISPER_MODELS,
        help="Whisper model size",
    )
    parser.add_argument(
        "-l",
        "--language",
        metavar="CODE",
        help="language code, e.g. en, es (default: auto-detect)",
    )
    parser.add_argument(
        "-f",
        "--formats",
        default="all",
        help="comma-separated output formats: srt,vtt,txt,json,tsv,all",
    )
    parser.add_argument(
        "--gpu",
        action="store_true",
        help="use GPU (AMD/NVIDIA via ROCm/CUDA)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="print transcribed text live instead of a progress bar",
    )
    parser.add_argument(
        "--mic",
        action="store_true",
        help="transcribe from the default microphone on pause (VAD; Ctrl+C to stop)",
    )
    parser.add_argument(
        "--list-inputs",
        action="store_true",
        help="print accepted input file types and exit",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="after transcription, summarize the .txt transcript with llama.cpp "
        f"(default model: {DEFAULT_SUMMARY_MODEL})",
    )
    parser.add_argument(
        "--summary-model",
        default=os.environ.get("VIDEO_WATCHER_SUMMARY_MODEL", DEFAULT_SUMMARY_MODEL),
        choices=tuple(SUMMARY_MODELS),
        metavar="MODEL",
        help="summary model key (default: %(default)s; more models later)",
    )
    return parser


def _status(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def resolve_output_dir(input_path: Path, output_dir: str | None) -> Path:
    if output_dir:
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        return out
    return input_path.resolve().parent


def main(argv: list[str] | None = None) -> int:
    setup_cache()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_inputs:
        print(format_media_list())
        return 0

    if args.mic:
        if args.summary:
            print("error: --summary is not supported with --mic", file=sys.stderr)
            return 1
        if args.media:
            print(
                "warning: ignoring media file(s) with --mic",
                file=sys.stderr,
            )
        if args.verbose:
            print(
                "warning: --verbose has no effect with --mic (text is always printed)",
                file=sys.stderr,
            )

        _status("Loading PyTorch and Whisper …")
        from vw.mic import default_mic_output_path, listen_microphone
        from vw.transcribe import resolve_device

        device = resolve_device(args.gpu)
        _status(f"Device: {device}  |  Model: {args.model}")

        out_path: Path | None = None
        if args.output_dir:
            out_dir = Path(args.output_dir).expanduser().resolve()
            out_path = default_mic_output_path(out_dir)

        try:
            listen_microphone(
                model_name=args.model,
                device=device,
                language=args.language,
                output_path=out_path,
            )
        except (ValueError, ImportError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"error: microphone: {exc}", file=sys.stderr)
            return 1

        if out_path is not None and out_path.is_file():
            print(f"Transcript: {out_path}", file=sys.stderr)
        return 0

    if not args.media:
        parser.print_help()
        print("\nerror: provide at least one media file, or use --mic.", file=sys.stderr)
        return 1

    paths = [Path(p).expanduser() for p in args.media]

    output_format = args.formats
    if args.summary and output_format != "all" and "txt" not in output_format.split(","):
        output_format = f"{output_format},txt" if output_format else "txt"

    for path in paths:
        if not path.is_file():
            print(f"error: not a file: {path}", file=sys.stderr)
            return 1
        if not is_supported_media(path):
            print(f"error: unsupported media: {path}", file=sys.stderr)
            print("Run: video-watcher --list-inputs", file=sys.stderr)
            return 1

    _status("Loading PyTorch and Whisper …")
    from vw.transcribe import list_output_files, resolve_device, transcribe_file

    device = resolve_device(args.gpu)
    _status(f"Device: {device}  |  Model: {args.model}")

    for path in paths:
        abs_path = path.resolve()
        out_dir = resolve_output_dir(abs_path, args.output_dir)
        stem = abs_path.stem

        if args.verbose:
            print(f"\nTranscribing: {abs_path}", file=sys.stderr)
            print(
                f"Model: {args.model} | Output: {out_dir} | GPU: {args.gpu}",
                file=sys.stderr,
            )

        _status(f"File: {abs_path.name}")

        try:
            transcribe_file(
                abs_path,
                model_name=args.model,
                output_dir=out_dir,
                output_format=output_format,
                language=args.language,
                device=device,
                verbose=args.verbose,
                release_gpu=args.summary and device == "cuda",
            )
        except Exception as exc:
            print(f"error: {abs_path}: {exc}", file=sys.stderr)
            return 1

        print("Done:", file=sys.stderr)
        for out_file in list_output_files(out_dir, stem):
            if out_file.is_file():
                print(f"  {out_file}", file=sys.stderr)

        if args.summary:
            from vw.summary import summarize_transcript_file

            txt_path = out_dir / f"{stem}.txt"
            if not txt_path.is_file():
                print(f"error: transcript missing: {txt_path}", file=sys.stderr)
                return 1
            try:
                summary_path = summarize_transcript_file(
                    txt_path,
                    model_key=args.summary_model,
                    use_gpu=args.gpu,
                )
            except FileNotFoundError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1
            except Exception as exc:
                print(f"error: summary failed: {exc}", file=sys.stderr)
                return 1
            # summarize_transcript_file prints markdown to stdout and path to stderr

    return 0


if __name__ == "__main__":
    sys.exit(main())
