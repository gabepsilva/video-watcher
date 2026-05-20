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
        help="media file(s) to transcribe, or YouTube URL(s) with --yt",
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
        "--summarize",
        action="store_true",
        help="after transcription, summarize the .txt transcript with llama.cpp "
        f"(default model: {DEFAULT_SUMMARY_MODEL}; --summarize is an alias)",
    )
    parser.add_argument(
        "--yt",
        action="store_true",
        help="treat inputs as YouTube URLs: fetch captions (yt-dlp, then "
        "youtube-transcript-api), or download audio and run Whisper if none",
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


def resolve_youtube_output_dir(output_dir: str | None) -> Path:
    """Default output directory for --yt when no media file path exists."""
    if output_dir:
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        return out
    return Path.cwd().resolve()


def main(argv: list[str] | None = None) -> int:
    setup_cache()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_inputs:
        print(format_media_list())
        return 0

    if args.mic:
        if args.yt:
            print("error: --yt is not supported with --mic", file=sys.stderr)
            return 1
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

    if args.yt:
        from tempfile import TemporaryDirectory

        from vw.transcribe import list_output_files, release_whisper_gpu, resolve_device, transcribe_file
        from vw.yt import (
            fetch_youtube_segments,
            is_youtube_url,
            try_ytdlp_audio_file,
            write_caption_outputs,
        )

        if not args.media:
            parser.print_help()
            print(
                "\nerror: with --yt, provide at least one YouTube URL.",
                file=sys.stderr,
            )
            return 1

        urls = [str(p).strip() for p in args.media]
        for u in urls:
            if not is_youtube_url(u):
                print(
                    f"error: --yt expects YouTube URLs; not recognized: {u}",
                    file=sys.stderr,
                )
                return 1

        output_format = args.formats
        if (
            args.summary
            and output_format != "all"
            and "txt" not in output_format.split(",")
        ):
            output_format = f"{output_format},txt" if output_format else "txt"

        whisper_loaded = False

        def ensure_whisper_loaded() -> str:
            nonlocal whisper_loaded
            if not whisper_loaded:
                _status("Loading PyTorch and Whisper …")
                whisper_loaded = True
            return resolve_device(args.gpu)

        for url in urls:
            out_dir = resolve_youtube_output_dir(args.output_dir)
            try:
                video_id, segments, source = fetch_youtube_segments(
                    url,
                    cli_language=args.language,
                    status=_status,
                )
            except ValueError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1

            if segments:
                _status(f"Using captions ({source}) for {video_id} …")
                write_caption_outputs(
                    segments,
                    video_id=video_id,
                    output_dir=out_dir,
                    output_format=output_format,
                    language=args.language,
                )
            else:
                device = ensure_whisper_loaded()
                _status(f"No captions for {video_id}; downloading audio (yt-dlp) …")
                with TemporaryDirectory(prefix="vw-yt-audio-") as tmp:
                    work = Path(tmp)
                    audio_path = try_ytdlp_audio_file(url, video_id, work)
                    if audio_path is None:
                        print(
                            "error: could not download subtitles or audio. "
                            "Install yt-dlp in the same environment: "
                            "pip install yt-dlp",
                            file=sys.stderr,
                        )
                        return 1
                    _status(f"Transcribing audio with Whisper ({args.model}) …")
                    try:
                        transcribe_file(
                            audio_path,
                            model_name=args.model,
                            output_dir=out_dir,
                            output_format=output_format,
                            language=args.language,
                            device=device,
                            verbose=args.verbose,
                            release_gpu=args.summary and device == "cuda",
                        )
                    except Exception as exc:
                        print(f"error: {video_id}: {exc}", file=sys.stderr)
                        return 1

            _status("Done:")
            for out_file in list_output_files(out_dir, video_id):
                if out_file.is_file():
                    print(f"  {out_file}", file=sys.stderr)

            if args.summary:
                from vw.summary import summarize_transcript_file

                txt_path = out_dir / f"{video_id}.txt"
                if not txt_path.is_file():
                    print(f"error: transcript missing: {txt_path}", file=sys.stderr)
                    return 1
                if whisper_loaded and resolve_device(args.gpu) == "cuda":
                    release_whisper_gpu(None)
                try:
                    summarize_transcript_file(
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
