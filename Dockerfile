# CPU-only image (local Whisper, no API key). Mount videos at /data.
FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY install-local video-watcher ./
RUN chmod +x install-local video-watcher \
    && ./install-local \
    && chmod -R a+rX /app

# Persist downloaded Whisper weights (bind-mount ~/.video_watcher → /cache).
ENV XDG_CACHE_HOME=/cache

ENTRYPOINT ["./video-watcher"]
CMD ["--help"]
