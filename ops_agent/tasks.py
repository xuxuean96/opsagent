from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from uuid import uuid4


class TaskStatus(str, Enum):
    CREATED = "created"
    RETRIEVING = "retrieving"
    PLANNING = "planning"
    ANSWERING = "answering"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentTask:
    id: str
    session_id: str
    question: str
    status: TaskStatus
    created_at: str
    updated_at: str
    answer: str | None = None
    error: str | None = None
    sources: list[dict] = field(default_factory=list)


class TaskStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def create(self, session_id: str, question: str) -> AgentTask:
        now = _now()
        task = AgentTask(
            id=str(uuid4()),
            session_id=session_id,
            question=question,
            status=TaskStatus.CREATED,
            created_at=now,
            updated_at=now,
        )
        self._append(task)
        return task

    def update(
        self,
        task_id: str,
        status: TaskStatus,
        answer: str | None = None,
        error: str | None = None,
        sources: list[dict] | None = None,
    ) -> AgentTask:
        task = self.get(task_id)
        if task is None:
            raise KeyError(f"Task not found: {task_id}")
        task.status = status
        task.updated_at = _now()
        if answer is not None:
            task.answer = answer
        if error is not None:
            task.error = error
        if sources is not None:
            task.sources = sources
        self._append(task)
        return task

    def get(self, task_id: str) -> AgentTask | None:
        for task in reversed(self.list(limit=10000)):
            if task.id == task_id:
                return task
        return None

    def list(self, limit: int = 50) -> list[AgentTask]:
        if not self.path.exists():
            return []
        latest: dict[str, AgentTask] = {}
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            payload["status"] = TaskStatus(payload["status"])
            latest[payload["id"]] = AgentTask(**payload)
        tasks = sorted(latest.values(), key=lambda task: task.updated_at, reverse=True)
        return tasks[:limit]

    def _append(self, task: AgentTask) -> None:
        payload = asdict(task)
        payload["status"] = task.status.value
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
