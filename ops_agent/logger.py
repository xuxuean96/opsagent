from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class JsonlLogger:
    def __init__(self, path: str, max_bytes: int = 5 * 1024 * 1024, backup_count: int = 5):
        self.path = Path(path)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: dict[str, Any]) -> None:
        event = {"ts": datetime.now(timezone.utc).isoformat(), **event}
        self._rotate_if_needed()
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")

    def _rotate_if_needed(self) -> None:
        if not self.path.exists() or self.path.stat().st_size < self.max_bytes:
            return
        oldest = self.path.with_suffix(self.path.suffix + f".{self.backup_count}")
        if oldest.exists():
            oldest.unlink()
        for idx in range(self.backup_count - 1, 0, -1):
            src = self.path.with_suffix(self.path.suffix + f".{idx}")
            dst = self.path.with_suffix(self.path.suffix + f".{idx + 1}")
            if src.exists():
                src.rename(dst)
        self.path.rename(self.path.with_suffix(self.path.suffix + ".1"))
