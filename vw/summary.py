"""Transcript summarization via llama.cpp (GGUF)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path

from vw.cache import llama_model_dir, setup_cache
from vw.constants import DEFAULT_SUMMARY_MODEL, SUMMARY_MODELS

HF_RESOLVE = "https://huggingface.co/{repo}/resolve/main/{filename}"

SYSTEM_PROMPT = """\
You summarize video/audio transcripts clearly and accurately.
Output markdown with:
1. A one-paragraph overview (2-4 sentences).
2. A "## Key points" heading followed by 5-10 bullet points.
Stay factual; do not invent details not present in the transcript.\
"""

USER_PROMPT_TEMPLATE = """\
Summarize the following transcript.

---
{transcript}
---\
"""

MERMAID_SYSTEM_PROMPT = """\
You analyze text and produce Mermaid diagrams for parts that benefit from visualization.

For each distinct process, workflow, relationship, hierarchy, decision tree, or \
interaction sequence in the text:
1. Give a short ### heading naming the block.
2. One line: which diagram type you chose and why (e.g. flowchart, sequenceDiagram).
3. A fenced ```mermaid code block with valid syntax only.

Pick the best diagram type per block:
- flowchart TD or LR — processes, pipelines, if/else, step order
- sequenceDiagram — messages or steps between actors over time
- erDiagram — entities, fields, relationships
- stateDiagram-v2 — states and transitions
- mindmap — hierarchical concepts
- journey — user/customer steps with stages (only if clearly described)
- gantt — only when explicit dates or durations exist in the text

Rules:
- Use only information from the provided text; do not invent steps or entities.
- Produce 1–4 diagrams; skip prose that does not map to a graph.
- Every diagram MUST be inside a ```mermaid fenced code block (required for rendering).
- Valid Mermaid only (no HTML, no prose inside code fences).
- All display strings MUST use double quotes: node labels, edge labels, participant \
names, state names, etc. (e.g. A["Transcribe audio"], B -->|"done"| C). Never use \
bare unquoted labels.
- Output markdown starting with ## Diagrams, then one ### section per diagram.\
"""

_MERMAID_LINE_RE = re.compile(
    r"^(flowchart|graph\s|sequenceDiagram|erDiagram|stateDiagram|mindmap|"
    r"journey|gantt|classDiagram|pie)\b",
    re.I,
)

MERMAID_USER_PROMPT_TEMPLATE = """\
Read the summary below. Find every block (or blocks) of content that can be \
represented as a graph—workflow, sequence, data model, state machine, hierarchy, etc.

There may be more than one diagram. Use the diagram type that fits each block best.

---
{summary}
---\
"""


def resolve_llama_cli() -> Path:
    """Locate llama-cli binary."""
    if env := os.environ.get("VIDEO_WATCHER_LLAMA_CLI"):
        path = Path(env).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return path.resolve()
        raise FileNotFoundError(
            f"VIDEO_WATCHER_LLAMA_CLI is set but not executable: {path}"
        )

    found = shutil.which("llama-cli")
    if found:
        return Path(found).resolve()

    candidates = [
        Path.home() / "llama-cpp-turboquant/build-rocm/bin/llama-cli",
        Path.home() / "llama-cpp-turboquant/build/bin/llama-cli",
        Path.home() / "llama.cpp/build/bin/llama-cli",
        Path.home() / "llama.cpp/build-rocm/bin/llama-cli",
    ]
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()

    raise FileNotFoundError(
        "llama-cli not found. Install llama.cpp and add llama-cli to PATH, or set "
        "VIDEO_WATCHER_LLAMA_CLI to the binary path."
    )


def model_spec(model_key: str) -> dict[str, str]:
    if model_key not in SUMMARY_MODELS:
        known = ", ".join(sorted(SUMMARY_MODELS))
        raise ValueError(f"Unknown summary model {model_key!r}. Known: {known}")
    return SUMMARY_MODELS[model_key]


def model_gguf_path(model_key: str) -> Path:
    spec = model_spec(model_key)
    return llama_model_dir() / spec["filename"]


def ensure_summary_model(model_key: str = DEFAULT_SUMMARY_MODEL) -> Path:
    """Download GGUF into cache if missing."""
    setup_cache()
    path = model_gguf_path(model_key)
    if path.is_file() and path.stat().st_size > 0:
        return path

    spec = model_spec(model_key)
    repo = spec["repo"]
    filename = spec["filename"]
    url = HF_RESOLVE.format(repo=repo, filename=filename)

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    print(f"Downloading {model_key} ({filename}) …", file=sys.stderr)
    print(f"  {url}", file=sys.stderr)
    print(f"  → {path}", file=sys.stderr)

    try:
        _download_file(url, tmp)
        tmp.rename(path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise

    print("Download complete.", file=sys.stderr)
    return path


def _download_file(url: str, dest: Path) -> None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "video-watcher/1.0"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        chunk_size = 1024 * 1024
        downloaded = 0
        with dest.open("wb") as out:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                out.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = 100.0 * downloaded / total
                    mb = downloaded / (1024 * 1024)
                    total_mb = total / (1024 * 1024)
                    print(
                        f"\r  {mb:.1f} / {total_mb:.1f} MiB ({pct:.0f}%)",
                        end="",
                        file=sys.stderr,
                    )
        if total > 0:
            print(file=sys.stderr)


def read_transcript(txt_path: Path) -> str:
    text = txt_path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        raise ValueError(f"Transcript is empty: {txt_path}")
    return text


def _fit_transcript(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    head = int(max_chars * 0.65)
    tail = max_chars - head - 80
    return (
        text[:head]
        + "\n\n[… middle truncated for context limit …]\n\n"
        + text[-tail:]
    )


def _llama_complete(
    *,
    system_prompt: str,
    user_prompt: str,
    model_key: str = DEFAULT_SUMMARY_MODEL,
    use_gpu: bool = False,
    ctx_size: int = 32768,
    n_predict: int = 2048,
    label: str = "Running",
) -> str:
    """Run llama-cli with system + user prompt file; return model text."""
    model_path = ensure_summary_model(model_key)
    spec = model_spec(model_key)
    llama_cli = resolve_llama_cli()

    cmd: list[str] = [
        str(llama_cli),
        "-m",
        str(model_path),
        "-sys",
        system_prompt,
        "-st",
        "--no-conversation",
        "--simple-io",
        "--reasoning",
        "off",
        "-n",
        str(n_predict),
        "-c",
        str(ctx_size),
        "--temp",
        "0.3",
    ]

    chat_template = spec.get("chat_template", "")
    if chat_template:
        cmd.extend(["--chat-template", chat_template])

    if use_gpu:
        cmd.extend(["-ngl", "999"])

    gpu_note = " GPU" if use_gpu else ""
    print(f"{label} with {model_key} ({llama_cli.name}{gpu_note}) …", file=sys.stderr)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".txt",
        delete=False,
    ) as tmp:
        tmp.write(user_prompt)
        prompt_path = Path(tmp.name)

    try:
        cmd.extend(["-f", str(prompt_path)])
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        except OSError as exc:
            raise RuntimeError(f"Failed to run {llama_cli}: {exc}") from exc
    finally:
        prompt_path.unlink(missing_ok=True)

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(
            f"llama-cli exited {proc.returncode}"
            + (f":\n{err}" if err else "")
        )

    text = _extract_generation(proc.stdout)
    if not text.strip():
        err = (proc.stderr or "").strip()
        raise RuntimeError(
            f"{label} produced no output" + (f":\n{err}" if err else "")
        )
    return text.strip() + "\n"


def summarize_text(
    transcript: str,
    *,
    model_key: str = DEFAULT_SUMMARY_MODEL,
    use_gpu: bool = False,
    ctx_size: int = 32768,
    max_transcript_chars: int = 24000,
) -> str:
    """Run llama.cpp on transcript text; return summary markdown."""
    body = _fit_transcript(transcript, max_transcript_chars)
    user_prompt = USER_PROMPT_TEMPLATE.format(transcript=body)
    return _llama_complete(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model_key=model_key,
        use_gpu=use_gpu,
        ctx_size=ctx_size,
        n_predict=2048,
        label="Summarizing",
    )


def mermaid_from_summary(
    summary: str,
    *,
    model_key: str = DEFAULT_SUMMARY_MODEL,
    use_gpu: bool = False,
    ctx_size: int = 32768,
) -> str:
    """Second pass: Mermaid diagrams for graph-worthy blocks in the summary."""
    user_prompt = MERMAID_USER_PROMPT_TEMPLATE.format(summary=summary)
    raw = _llama_complete(
        system_prompt=MERMAID_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model_key=model_key,
        use_gpu=use_gpu,
        ctx_size=ctx_size,
        n_predict=3072,
        label="Generating Mermaid diagrams",
    )
    return _normalize_mermaid_section(raw)


def _extract_generation(stdout: str) -> str:
    """Strip echoed prompt / chat framing from llama-cli stdout."""
    for marker in (
        "[ Prompt:",
        "common_memory_breakdown_print:",
        "Exiting...",
    ):
        if marker in stdout:
            stdout = stdout.split(marker, 1)[0]

    lines = stdout.splitlines()
    response_lines: list[str] = []
    in_response = False
    past_prompt = False

    for line in lines:
        if re.match(
            r"^(llama_|ggml_|build:|main:|sampler|system_info|model loaded|"
            r"available commands|using custom|modalities|model\s*:)",
            line,
            re.I,
        ):
            continue
        if re.match(r"^\s*/\w+", line):
            continue

        if line.startswith(">"):
            in_response = False
            response_lines = []
            continue
        if line.strip().endswith("(truncated)"):
            past_prompt = True
            continue
        if line.startswith(":"):
            in_response = True
            rest = line[1:].lstrip()
            if rest:
                response_lines.append(rest)
            continue
        if in_response:
            response_lines.append(line)
            continue
        if past_prompt or re.match(r"^#{1,3}\s", line):
            past_prompt = True
            if line.strip():
                response_lines.append(line)

    if response_lines:
        text = "\n".join(response_lines).strip()
        # Drop generic refusals from wrong chat-template runs.
        lower = text.lower()
        if lower.startswith("i am a large language model") or lower.startswith(
            "i'm ready to help"
        ):
            return ""
        return text

    return ""


def _wrap_bare_mermaid_blocks(text: str) -> str:
    """Wrap diagram lines in ```mermaid fences when the model omits them."""
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if _MERMAID_LINE_RE.match(line.strip()):
            if out and out[-1].strip():
                out.append("")
            out.append("```mermaid")
            while i < len(lines):
                current = lines[i]
                stripped = current.strip()
                if (
                    i > 0
                    and out[-1] != "```mermaid"
                    and stripped.startswith("###")
                ):
                    break
                if (
                    i > 0
                    and out[-1] != "```mermaid"
                    and re.match(r"^##\s+(?!Diagrams)", stripped)
                ):
                    break
                out.append(current)
                i += 1
            out.append("```")
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def _normalize_mermaid_section(text: str) -> str:
    """Ensure output has ## Diagrams and at least one ```mermaid block."""
    text = text.strip()
    if not text:
        return ""

    if "```mermaid" not in text:
        text = _wrap_bare_mermaid_blocks(text)

    has_mermaid = "```mermaid" in text or _MERMAID_LINE_RE.search(text)
    if not has_mermaid:
        return ""

    if "```mermaid" not in text:
        text = _wrap_bare_mermaid_blocks(text)

    if not re.search(r"^##\s+Diagrams\s*$", text, re.M):
        if text.startswith("###"):
            text = "## Diagrams\n\n" + text
        elif not text.startswith("## Diagrams"):
            text = "## Diagrams\n\n" + text

    if not text.endswith("\n"):
        text += "\n"
    return text + "\n"


def timestamped_summary_path(txt_path: Path, when: datetime | None = None) -> Path:
    """Build `{stem}.{YYYYMMDD-HHMMSS}.summary.md` next to the transcript."""
    moment = when or datetime.now()
    stamp = moment.strftime("%Y%m%d-%H%M%S")
    return txt_path.with_name(f"{txt_path.stem}.{stamp}.summary.md")


def summarize_transcript_file(
    txt_path: Path,
    output_path: Path | None = None,
    *,
    model_key: str = DEFAULT_SUMMARY_MODEL,
    use_gpu: bool = False,
    print_to_terminal: bool = True,
) -> Path:
    """Summarize a .txt transcript; write timestamped .summary.md beside it."""
    txt_path = txt_path.expanduser().resolve()
    transcript = read_transcript(txt_path)
    summary = summarize_text(
        transcript,
        model_key=model_key,
        use_gpu=use_gpu,
    )

    diagrams = mermaid_from_summary(
        summary,
        model_key=model_key,
        use_gpu=use_gpu,
    )

    if output_path is None:
        output_path = timestamped_summary_path(txt_path)
    else:
        output_path = output_path.expanduser().resolve()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = (
        f"# Summary\n\n"
        f"_Source: `{txt_path.name}` · model: `{model_key}` · created: {created}_\n\n"
    )
    content = header + summary
    if diagrams:
        content = content.rstrip() + "\n\n" + diagrams
    output_path.write_text(content, encoding="utf-8")

    if print_to_terminal:
        print(content, end="" if content.endswith("\n") else "\n")

    print(f"Summary saved: {output_path}", file=sys.stderr)
    return output_path
