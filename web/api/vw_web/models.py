"""In-memory job records (localhost dev; lost on process restart)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Literal


class JobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


JobKind = Literal["file", "youtube"]


@dataclass
class JobRecord:
    id: str
    kind: JobKind
    state: JobState
    work_dir: Path
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    exit_code: int | None = None
    error: str | None = None
    log_lines: list[str] = field(default_factory=list)
    subscribers: list = field(default_factory=list, repr=False)
