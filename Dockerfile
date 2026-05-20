# CPU-only image (local Whisper, no API key). Mount videos at /data.
FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg git cmake build-essential libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/ggml-org/llama.cpp /tmp/llama.cpp \
    && cmake -S /tmp/llama.cpp -B /tmp/llama-build \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_SHARED_LIBS=ON \
        -DGGML_NATIVE=OFF \
    && cmake --build /tmp/llama-build -j"$(nproc)" --target llama-cli \
    && install -d /opt/llama \
    && cp -a /tmp/llama-build/bin/llama-cli /tmp/llama-build/bin/*.so* /opt/llama/ 2>/dev/null || true \
    && install -m755 /tmp/llama-build/bin/llama-cli /opt/llama/ \
    && rm -rf /tmp/llama.cpp /tmp/llama-build

WORKDIR /app

COPY install-local video-watcher ./
COPY vw ./vw/
RUN chmod +x install-local video-watcher \
    && ./install-local \
    && /app/.venv/bin/python -c "import sounddevice, whisper" \
    && chmod -R a+rX /app

ENV PYTHONPATH=/app
ENV VIDEO_WATCHER_CACHE=/cache
ENV XDG_CACHE_HOME=/cache
ENV PATH=/app/.venv/bin:/opt/llama:${PATH}
ENV LD_LIBRARY_PATH=/opt/llama:${LD_LIBRARY_PATH:-}
ENV VIDEO_WATCHER_LLAMA_CLI=/opt/llama/llama-cli

ENTRYPOINT ["python", "-m", "vw"]
CMD ["--help"]
