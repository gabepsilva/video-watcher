"""Environment variable documentation for --help output."""

from __future__ import annotations

LOCAL_ENV_VARS: tuple[tuple[str, str], ...] = (
    ("WHISPER_MODEL", "Default Whisper model if -m is omitted (e.g. base, small)."),
    (
        "VIDEO_WATCHER_CACHE",
        "Directory for model weights and caches (default: ~/.video_watcher).",
    ),
    (
        "VIDEO_WATCHER_PYTHON",
        "Python executable to use (video-watcher launcher only).",
    ),
    ("XDG_CACHE_HOME", "Set automatically from VIDEO_WATCHER_CACHE when vw runs."),
    (
        "VIDEO_WATCHER_LLAMA_CLI",
        "Path to llama-cli for --summary (default: search PATH and common build dirs).",
    ),
    (
        "VIDEO_WATCHER_SUMMARY_MODEL",
        "Default summary model key for --summary (default: gemma-4-e4b).",
    ),
)

DOCKER_ENV_VARS: tuple[tuple[str, str], ...] = (
    ("VIDEO_WATCHER_CACHE", "Host cache dir mounted at /cache (default: ~/.video_watcher)."),
    (
        "VIDEO_WATCHER_DATA",
        "Default host folder mounted as /data (default: ~/Downloads).",
    ),
    ("CONTAINER_RUNTIME", "Container CLI: docker (default) or podman."),
    (
        "HSA_OVERRIDE_GFX_VERSION",
        "AMD GPU workaround, e.g. 10.3.0 for RX 6000 / Navi 21 (local and Docker).",
    ),
)


def format_env_section(
    title: str,
    variables: tuple[tuple[str, str], ...],
) -> str:
    lines = [title, ""]
    width = max(len(name) for name, _ in variables)
    for name, description in variables:
        lines.append(f"  {name:<{width}}  {description}")
    return "\n".join(lines)


def local_env_epilog() -> str:
    return format_env_section("Environment variables:", LOCAL_ENV_VARS)


def docker_env_epilog() -> str:
    return format_env_section("Environment variables:", DOCKER_ENV_VARS)
