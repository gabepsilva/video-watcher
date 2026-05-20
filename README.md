# video-watcher

Local captions (SRT, VTT, TXT) for audio and video via [OpenAI Whisper](https://github.com/openai/whisper). No API key.

**Input formats:** anything **ffmpeg** can decode. List known extensions:

```bash
./video-watcher --list-inputs
```

| Video | Audio |
|-------|-------|
| mp4, mkv, webm, mov, avi, m4v, flv, ts, m2ts | mp3, wav, flac, ogg, opus, m4a, aac, wma |

Other `audio/*` or `video/*` files (by MIME type) are accepted too.

## How it works

`video-watcher` runs [OpenAI Whisper](https://github.com/openai/whisper) on your file. **ffmpeg** decodes the audio; **Whisper** transcribes it. There is no intermediate MP3 on disk — audio stays in memory.

```mermaid
flowchart LR
  MP4[Your media file]
  FF[ffmpeg subprocess]
  PCM[Raw audio in memory<br/>16 kHz mono PCM]
  MEL[Log-mel spectrogram]
  W[Whisper neural network]
  OUT[SRT / VTT / TXT / JSON]

  MP4 --> FF --> PCM --> MEL --> W --> OUT
```

1. **ffmpeg** reads the media file (video or audio), extracts the audio track, and streams **mono 16 kHz PCM** to Python via a pipe (not a temp file).
2. Whisper converts that waveform into a **log-mel spectrogram** — the representation the model was trained on.
3. The **Whisper model** processes the spectrogram in ~30 second chunks and predicts text (optionally forced to a language with `-l`).
4. Caption files are written next to the input (or under `-o`).

`video-watcher` only adds CLI conveniences (model, language, output dir, GPU). `video-watcher-docker` runs the same pipeline inside a container that bundles ffmpeg, PyTorch, and Whisper.

## Scripts

| Script | Path | Purpose |
|--------|------|---------|
| **video-watcher-docker** | Docker | Check deps, build image, transcribe (auto GPU) |
| **install-local** | Local | Install CPU Whisper into `.venv` |
| **install-gpu** | Local | Install AMD ROCm PyTorch + Whisper into `.venv` |
| **setup-rocm** | Local | Alias for `install-gpu` (back-compat) |
| **video-watcher** | Local | Transcribe videos (after install) |

```
video-watcher/
  vw/                     # Python package (CLI, progress bar, transcribe)
  video-watcher-docker    # Docker: check → build → run
  install-local           # Local CPU setup
  install-gpu             # Local AMD GPU setup
  video-watcher           # Launcher → python -m vw
  .venv/                  # Created by install-* scripts
```

## Docker (recommended)

```bash
./video-watcher-docker                              # check + build image
./video-watcher-docker ~/Downloads/your-video.mp4   # transcribe
./video-watcher-docker -m turbo -l en ~/Downloads/talk.mp4
./video-watcher-docker --check                      # dependency report only
./video-watcher-docker --cpu ~/Downloads/foo.mp4     # force CPU image
```

Auto-detects **CPU**, **NVIDIA**, or **AMD ROCm** and picks the matching image. Runs entirely in the container and exits on failure (no host fallback). The ROCm image builds **HIP `llama-cli`** so `--gpu --summary` uses the GPU for Whisper and Gemma (rebuild with `--rebuild` after upgrading).

### Microphone in Docker (experimental)

```bash
./video-watcher-docker --mic -m tiny -l en          # print chunks (Ctrl+C to stop)
./video-watcher-docker --mic -m tiny -o ~/Downloads # also append to ~/Downloads/mic-*.txt
./video-watcher-docker --mic -m small -l en         # GPU image used when available
```

`video-watcher-docker` checks the host for **ALSA** (`/dev/snd`) and **PulseAudio/PipeWire** (`$XDG_RUNTIME_DIR/pulse/native`), passes them into the container, and **rebuilds the image automatically** if `sounddevice` is missing. Images include `libportaudio2` and `sounddevice` (install via the venv’s `python -m pip` on GPU images).

Mic records at the device’s native sample rate (often 48 kHz) and resamples to 16 kHz for Whisper — required for many USB mics in Docker. Same lag tips as native: `tiny`/`base`, shorter `--mic-chunk`. Manual rebuild after upgrading: `./video-watcher-docker --rebuild`.

## Local (native)

```bash
./install-local
./video-watcher ~/Downloads/your-video.mp4
```

### Microphone (experimental)

```bash
./video-watcher --mic -m tiny -l en          # print chunks to the terminal
./video-watcher --mic -m tiny -o ./out       # also append to ./out/mic-*.txt
# Ctrl+C to stop
```

Uses **sounddevice** (installed by `install-local` / `install-gpu`) and the system **PortAudio** library (`sudo apt install libportaudio2` on Ubuntu). Records at the mic’s native sample rate and resamples to 16 kHz for Whisper. Expect a few seconds of lag per chunk; `tiny` or `base` on `--gpu` feels best.

### AMD GPU (local)

```bash
./install-gpu
./video-watcher --gpu -m small ~/Downloads/your-video.mp4
# higher quality, still fast on GPU:
./video-watcher --gpu -m turbo -l en ~/Downloads/your-video.mp4
```

Reinstall ROCm stack: `./install-gpu --force`

If GPU is not detected on RX 6800 / Navi 21:

```bash
export HSA_OVERRIDE_GFX_VERSION=10.3.0
./install-gpu --force
```

## Options (`video-watcher` / `video-watcher-docker`)

| Flag | Meaning |
|------|---------|
| `-m MODEL` | Whisper model: `tiny`, `base`, `small`, `medium`, `large`, `turbo` (default: `base`, or `WHISPER_MODEL`) |
| `-l en` | Force language (default: auto-detect) |
| `-f srt,vtt,…` | Output formats: `srt`, `vtt`, `txt`, `json`, `tsv`, or `all` (default) |
| `--gpu` | Use GPU (local: after `install-gpu`; docker: automatic when available) |
| `--verbose` | Print live transcript text instead of the progress bar |
| `--mic` | Transcribe from the default microphone in chunks (experimental; Ctrl+C to stop) |
| `--mic-chunk SEC` | Seconds of audio per mic chunk (default: 5; range 1–30). Use `-m tiny` for lower latency |
| `-o ./out` | Output folder for caption files (with `--mic`, writes `mic-YYYYMMDD-HHMMSS.txt`) |
| `--list-inputs` | Print supported media extensions and exit |
| `--summary` | After transcribe: summarize `.txt` with llama.cpp + Mermaid diagrams |
| `--summary-model` | Summary model key (default: `gemma-4-e4b`; more models later) |

Docker-only: `--cpu` (force CPU image), `--check` (dependency report). `--mic` works in Docker with host audio passthrough (see above). No native fallback for file runs — use `./video-watcher` on the host if you prefer.

### Whisper models

| Model | Size (approx.) | Use when |
|-------|----------------|----------|
| `tiny` | 72 MB | Fastest drafts |
| `base` | 140 MB | Default; quick runs |
| `small` | 460 MB | Good daily balance with `--gpu` |
| `medium` | 1.4 GB | Higher accuracy, slower |
| `large` | 2.9 GB | Best quality (`large-v3`) |
| `turbo` | 1.5 GB | Near-`large` quality, much faster (`large-v3-turbo`) |

Weights download on first use into `~/.video_watcher/whisper/` with a progress bar. The CLI prints status before audio decode, model load, and download so long first runs are not silent.

Run `video-watcher --help` for environment variables (also listed below).

## Convenience symlink

From anywhere:

```bash
~/Downloads/vw ~/Downloads/foo.mp4
```

(`vw` → `video-watcher/video-watcher` for local, or point at `video-watcher-docker` for Docker)

## Docker images (manual)

`./video-watcher-docker` handles this automatically.

| Image | Dockerfile | GPU |
|-------|------------|-----|
| `video-watcher:cpu` | `Dockerfile` | — |
| `video-watcher:nvidia` | `Dockerfile.nvidia` | NVIDIA + [Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) |
| `video-watcher:rocm` | `Dockerfile.rocm` | AMD `/dev/kfd` + `/dev/dri` |

### Run as your user

Containers start as **your UID/GID** (`--user $(id -u):$(id -g)` on Docker, `--userns=keep-id` on Podman), so caption files on mounted folders are owned by you, not root.

Whisper models are cached on the host at `~/.video_watcher/whisper` (set `VIDEO_WATCHER_CACHE` to use a different folder). The directory is created automatically on first run.

## Summarize transcript (`--summary`)

After transcription, optionally summarize the `.txt` output with **llama.cpp** (default model: **Gemma 4 E4B** GGUF).

**Requires:** `llama-cli` on `PATH`, or set `VIDEO_WATCHER_LLAMA_CLI` to your build (e.g. `~/llama.cpp/build/bin/llama-cli`).

```bash
./video-watcher -m small -l en --summary ~/Downloads/talk.mp4
# → talk.txt + talk.20260519-153045.summary.md (timestamp avoids overwrite)
# Summary markdown is printed to the terminal and saved to the file.
# A second pass adds Mermaid diagrams (flowchart, sequence, ER, etc.) for graph-worthy blocks.
```

The GGUF is downloaded once to `~/.video_watcher/llama/` (~5 GB for Gemma 4 E4B Q4). Use `--gpu` so both Whisper and the summarizer can use the GPU. More summary models will be added later (`--summary-model`).

## Environment variables

| Variable | Applies to | Meaning |
|----------|------------|---------|
| `WHISPER_MODEL` | local | Default `-m` if omitted (e.g. `small`, `turbo`) |
| `VIDEO_WATCHER_CACHE` | local, Docker | Model cache root (default: `~/.video_watcher`) |
| `VIDEO_WATCHER_PYTHON` | launcher | Python binary for `video-watcher` script |
| `VIDEO_WATCHER_LLAMA_CLI` | local | Path to `llama-cli` for `--summary` |
| `VIDEO_WATCHER_SUMMARY_MODEL` | local | Default `--summary-model` |
| `VIDEO_WATCHER_DATA` | Docker | Host folder mounted as `/data` (default: `~/Downloads`) |
| `CONTAINER_RUNTIME` | Docker | `docker` (default) or `podman` |
| `HSA_OVERRIDE_GFX_VERSION` | local, Docker | AMD workaround (e.g. `10.3.0` for RX 6000 / Navi 21) |

## Features

### Transcription

- **Local Whisper** — no API key or cloud; ffmpeg pipes mono 16 kHz PCM into Whisper (no temp audio file)
- **`vw` Python package** — `video-watcher` launches `python -m vw`; logic in `vw/` (CLI, transcribe, progress, cache)
- **Multiple caption formats** — SRT, VTT, TXT, JSON, TSV (`-f` or `all`)
- **Audio and video inputs** — mp4, mkv, mp3, wav, ogg, flac, and more; `--list-inputs` for the full set
- **Whisper models** — `tiny`, `base`, `small`, `medium`, `large` (`large-v3`), and **`turbo`** (`large-v3-turbo`); language forcing with `-l`
- **Startup status** — messages before PyTorch loads, audio decode, and model download (first run shows size + progress bar)
- **Progress bar** — time-based bar with ETA during transcription; `--verbose` for live transcript text instead
- **Batch-friendly** — transcribe several files in one command
- **Live microphone** (`--mic`) — chunked live transcription to the terminal; optional `mic-YYYYMMDD-HHMMSS.txt` under `-o` (native and Docker)

### Summarization (`--summary`)

- **llama.cpp + GGUF** — local summarization with **Gemma 4 E4B** (default); no Ollama/vLLM required
- **Two-pass output** — (1) markdown summary with overview + key points, (2) **Mermaid diagrams** for graph-worthy blocks (flowchart, sequence, ER, state, mindmap, etc.; multiple diagrams when needed)
- **Timestamped files** — `name.YYYYMMDD-HHMMSS.summary.md` so reruns never overwrite prior summaries
- **Terminal + file** — full markdown printed to stdout and saved beside the transcript
- **Extensible models** — `--summary-model` registry in `vw/constants.py` (more models later)
- **GGUF cache** — weights under `~/.video_watcher/llama/` (~5 GB on first run)
- **`VIDEO_WATCHER_LLAMA_CLI`** — point at your `llama-cli` build if it is not on `PATH`

### Runtime & deployment

- **Docker or native** — `video-watcher-docker` (check → build → run) or `video-watcher` + `install-local` / `install-gpu`
- **Three Docker images** — `video-watcher:cpu`, `video-watcher:nvidia`, `video-watcher:rocm` (auto-selected)
- **GPU auto-detection (Docker)** — CPU, NVIDIA, or AMD ROCm image + device passthrough; `--cpu` to force CPU image
- **AMD ROCm (local)** — `install-gpu` for RX / Radeon on Linux (`HSA_OVERRIDE_GFX_VERSION` for Navi 21)
- **Runs as your user (Docker)** — captions and cache owned by you, not root
- **Unified model cache** — `~/.video_watcher/` for Whisper (`whisper/`) and summary GGUF (`llama/`); override with `VIDEO_WATCHER_CACHE`
- **Dependency checks** — `video-watcher-docker --check`
- **Container-only Docker runs** — no host `.venv` fallback; ROCm image includes HIP `llama-cli` for `--summary --gpu`
- **Podman-compatible** — `CONTAINER_RUNTIME=podman`
- **Help + env docs** — `video-watcher --help` lists environment variables via `vw/env_docs.py`
- **Docker mic** — `--mic` with ALSA/Pulse passthrough; auto-rebuild when the image lacks `sounddevice`; CPU image bundles `llama-cli` for `--summary`

## Changelog

### Unreleased (staged + working tree)

- **`--mic` live transcription** — new `vw/mic.py`; CLI flag `--mic` / `--mic-chunk`; works natively and in Docker
- **Docker mic** — host audio passthrough (`/dev/snd`, Pulse/PipeWire socket), `ensure_mic_image` auto-rebuild, `-o` rewritten to `/data` mount
- **Mic sample-rate handling** — record at device native rate, resample to 16 kHz (fixes USB mics and Docker ALSA)
- **Docker images** — `libportaudio2` + `sounddevice` in all images; CPU image adds `llama-cli`, `.venv` on `PATH`; GPU images use `python -m pip` with import check at build
- **`install-local` / `install-gpu`** — install `sounddevice`; PortAudio hint on Ubuntu
- **`setup-rocm`** — alias script for `install-gpu`
- **README** — Whisper model table, env var table, Docker/local mic sections, expanded features list
- **Docker wrapper** — partial mic wiring in staged changes; full passthrough + auto-rebuild in working tree

### `6e0f2ff` — Add turbo Whisper model and early startup status messages (on `main`)

- **`-m turbo`** — maps to Whisper `large-v3-turbo` (near-`large` quality, faster)
- **Startup status** — stderr messages before PyTorch loads, audio decode, and model download (with progress bar on first download)
- **Model cache** — download progress via `vw/cache.py`; transcribe status in `vw/transcribe.py`
