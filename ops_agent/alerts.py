from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass
class AlertRecord:
    id: str
    code: str
    severity: str
    message: str
    source: str
    source_id: str | None
    status: str
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = field(default_factory=dict)


class AlertCenter:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(
        self,
        code: str,
        severity: str,
        message: str,
        source: str,
        source_id: str | None = None,
        status: str = "open",
        metadata: dict[str, Any] | None = None,
    ) -> AlertRecord:
        existing = self.find_open(code=code, source=source, source_id=source_id)
        now = _now()
        if existing is not None:
            existing.severity = severity
            existing.message = message
            existing.status = status
            existing.updated_at = now
            if metadata:
                existing.metadata.update(metadata)
            self._append(existing)
            return existing
        record = AlertRecord(
            id=str(uuid4()),
            code=code,
            severity=severity,
            message=message,
            source=source,
            source_id=source_id,
            status=status,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )
        self._append(record)
        return record

    def resolve(self, code: str, source: str, source_id: str | None = None, metadata: dict[str, Any] | None = None) -> AlertRecord | None:
        existing = self.find_open(code=code, source=source, source_id=source_id)
        if existing is None:
            return None
        existing.status = "resolved"
        existing.updated_at = _now()
        if metadata:
            existing.metadata.update(metadata)
        self._append(existing)
        return existing

    def find_open(self, code: str, source: str, source_id: str | None = None) -> AlertRecord | None:
        for item in self.list(limit=10000, include_resolved=False):
            if item.code == code and item.source == source and item.source_id == source_id:
                return item
        return None

    def list(self, limit: int = 100, include_resolved: bool = False) -> list[AlertRecord]:
        if not self.path.exists():
            return []
        latest: dict[str, AlertRecord] = {}
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            latest[payload["id"]] = AlertRecord(**payload)
        items = sorted(latest.values(), key=lambda item: item.updated_at, reverse=True)
        if not include_resolved:
            items = [item for item in items if item.status != "resolved"]
        return items[:limit]

    def _append(self, record: AlertRecord) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
