# CPU-only image (local Whisper, no API key). Mount videos at /data.
FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY install-cpu video-watcher ./
RUN chmod +x install-cpu video-watcher \
    && ./install-cpu

# Persist downloaded Whisper weights between runs (optional volume).
ENV XDG_CACHE_HOME=/cache

ENTRYPOINT ["./video-watcher"]
CMD ["--help"]
