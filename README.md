# video-watcher

Local video captions (SRT, VTT, TXT) via [OpenAI Whisper](https://github.com/openai/whisper). No API key.

## Layout

```
video-watcher/
  Downloads/      → symlink to ~/Downloads
  video-watcher   # main command
  install-cpu     # CPU setup
  setup-rocm      # AMD GPU setup
  .venv/          # Python env (created by install scripts)
```

## Quick start (CPU)

```bash
cd ~/Downloads/video-watcher
./install-cpu
./video-watcher Downloads/"OpenClaw Intro.mp4"
```

## AMD GPU (ROCm)

```bash
./setup-rocm
./video-watcher --gpu -m small Downloads/your-video.mp4
```

Reinstall ROCm stack: `./setup-rocm --force`

If GPU is not detected on RX 6800 / Navi 21:

```bash
export HSA_OVERRIDE_GFX_VERSION=10.3.0
./setup-rocm --force
```

## Options

| Flag | Meaning |
|------|---------|
| `-m small` | Better accuracy, slower |
| `-l en` | Force English |
| `--gpu` | Use GPU (after `setup-rocm`) |
| `-o ./out` | Output folder for caption files |

## Convenience symlink

From anywhere:

```bash
~/Downloads/vw Downloads/foo.mp4
```

(`vw` → `video-watcher/video-watcher`)

## Docker

Build once:

```bash
docker build -t video-watcher .
```

Transcribe a file (mount your video folder as `/data`):

```bash
docker run --rm \
  -v "$HOME/Downloads:/data" \
  -v video-watcher-cache:/cache \
  video-watcher /data/your-video.mp4
```

With options:

```bash
docker run --rm \
  -v "$HOME/Downloads:/data" \
  -v video-watcher-cache:/cache \
  video-watcher -m small -l en -o /data/out /data/talk.mp4
```

The named volume `video-watcher-cache` keeps Whisper model weights so later runs start faster. Caption files are written next to each input unless you pass `-o`.

For NVIDIA GPU in Docker, use the host’s [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) and a CUDA-based image; this repo’s default image is CPU-only.
