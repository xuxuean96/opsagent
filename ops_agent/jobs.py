from __future__ import annotations

import json
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class JobRecord:
    id: str
    kind: str
    status: JobStatus
    created_at: str
    updated_at: str
    result: dict[str, Any] | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class JobStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def create(self, kind: str, metadata: dict[str, Any] | None = None) -> JobRecord:
        now = _now()
        job = JobRecord(id=str(uuid4()), kind=kind, status=JobStatus.QUEUED, created_at=now, updated_at=now, metadata=metadata or {})
        self._append(job)
        return job

    def update(
        self,
        job_id: str,
        status: JobStatus,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> JobRecord:
        job = self.get(job_id)
        if job is None:
            raise KeyError(f"Job not found: {job_id}")
        job.status = status
        job.updated_at = _now()
        if result is not None:
            job.result = result
        if error is not None:
            job.error = error
        self._append(job)
        return job

    def get(self, job_id: str) -> JobRecord | None:
        for job in reversed(self.list(limit=10000)):
            if job.id == job_id:
                return job
        return None

    def list(self, limit: int = 50) -> list[JobRecord]:
        if not self.path.exists():
            return []
        latest: dict[str, JobRecord] = {}
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            payload["status"] = JobStatus(payload["status"])
            latest[payload["id"]] = JobRecord(**payload)
        return sorted(latest.values(), key=lambda job: job.updated_at, reverse=True)[:limit]

    def _append(self, job: JobRecord) -> None:
        payload = asdict(job)
        payload["status"] = job.status.value
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


class JobManager:
    def __init__(self, store: JobStore, max_workers: int = 2, on_job_update: Callable[[JobRecord], None] | None = None):
        self.store = store
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="ops-agent-job")
        self._futures: dict[str, Future] = {}
        self.on_job_update = on_job_update

    def submit(self, kind: str, func: Callable[..., Any], *args: Any, metadata: dict[str, Any] | None = None, **kwargs: Any) -> JobRecord:
        job = self.store.create(kind, metadata=metadata)
        self._notify(job)

        def runner() -> None:
            try:
                running = self.store.update(job.id, JobStatus.RUNNING)
                self._notify(running)
                result = func(*args, **kwargs)
                payload = result if isinstance(result, dict) else {"value": result}
                completed = self.store.update(job.id, JobStatus.COMPLETED, result=payload)
                self._notify(completed)
            except Exception as exc:
                failed = self.store.update(job.id, JobStatus.FAILED, error=str(exc))
                self._notify(failed)

        self._futures[job.id] = self.executor.submit(runner)
        return self.store.get(job.id) or job

    def list(self, limit: int = 50) -> list[JobRecord]:
        return self.store.list(limit=limit)

    def get(self, job_id: str) -> JobRecord | None:
        return self.store.get(job_id)

    def _notify(self, job: JobRecord) -> None:
        if self.on_job_update is not None:
            self.on_job_update(job)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
