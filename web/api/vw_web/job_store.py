"""Job registry + log fan-out for SSE (thread-safe publish from worker threads)."""

from __future__ import annotations

import asyncio
import threading
import uuid
from pathlib import Path
from typing import Any

from vw_web.models import JobKind, JobRecord, JobState


_SENTINEL = object()
SSE_END = _SENTINEL


class JobStore:
    """Process-local job store (dev / localhost)."""

    def __init__(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = threading.Lock()
        self._loop = loop
        self._queues: dict[str, list[asyncio.Queue[Any]]] = {}

    def attach_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def create_job(self, *, kind: JobKind, jobs_dir: Path) -> JobRecord:
        jobs_dir.mkdir(parents=True, exist_ok=True)
        job_id = uuid.uuid4().hex
        work_dir = (jobs_dir / job_id).resolve()
        work_dir.mkdir(parents=False)
        record = JobRecord(id=job_id, kind=kind, state=JobState.QUEUED, work_dir=work_dir)
        with self._lock:
            self._jobs[job_id] = record
            self._queues[job_id] = []
        return record

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list_recent(self, limit: int = 20) -> list[JobRecord]:
        with self._lock:
            items = list(self._jobs.values())
        items.sort(key=lambda j: j.created_at, reverse=True)
        return items[:limit]

    def subscribe(self, job_id: str) -> asyncio.Queue[Any]:
        q: asyncio.Queue[Any] = asyncio.Queue(maxsize=500)
        with self._lock:
            if job_id not in self._queues:
                self._queues[job_id] = []
            self._queues[job_id].append(q)
        return q

    def unsubscribe(self, job_id: str, q: asyncio.Queue[Any]) -> None:
        with self._lock:
            qs = self._queues.get(job_id)
            if not qs:
                return
            try:
                qs.remove(q)
            except ValueError:
                return

    def publish_log(self, job_id: str, line: str) -> None:
        job = self.get(job_id)
        if job is None:
            return
        with self._lock:
            job.log_lines.append(line)
            queues = list(self._queues.get(job_id, ()))

        loop = self._loop
        if loop is None:
            return
        for q in queues:
            # Bind `q` per iteration; default-arg binds `line` at define-time.
            def _put(
                target: asyncio.Queue[Any] = q,
                payload: str = line,
            ) -> None:
                try:
                    target.put_nowait({"kind": "log", "line": payload})
                except asyncio.QueueFull:
                    pass

            loop.call_soon_threadsafe(_put)

    def publish_state(self, job_id: str, state: JobState) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            job.state = state
        self._fanout(job_id, {"kind": "state", "state": state.value})

    def publish_done(self, job_id: str) -> None:
        with self._lock:
            qs = list(self._queues.get(job_id, ()))
        loop = self._loop
        if loop is None:
            return
        for q in qs:

            def _end(target: asyncio.Queue[Any] = q) -> None:
                try:
                    target.put_nowait(_SENTINEL)
                except asyncio.QueueFull:
                    pass

            loop.call_soon_threadsafe(_end)

    def _fanout(self, job_id: str, payload: dict[str, Any]) -> None:
        with self._lock:
            queues = list(self._queues.get(job_id, ()))
        loop = self._loop
        if loop is None:
            return
        for q in queues:

            def _put(
                target: asyncio.Queue[Any] = q,
                body: dict[str, Any] = payload,
            ) -> None:
                try:
                    target.put_nowait(body)
                except asyncio.QueueFull:
                    pass

            loop.call_soon_threadsafe(_put)
