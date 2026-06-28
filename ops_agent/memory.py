from __future__ import annotations

from collections import defaultdict, deque


class ConversationMemory:
    def __init__(self, max_messages: int = 12):
        self.max_messages = max_messages
        self._messages: dict[str, deque[dict[str, str]]] = defaultdict(lambda: deque(maxlen=max_messages))

    def add(self, session_id: str, role: str, content: str) -> None:
        self._messages[session_id].append({"role": role, "content": content})

    def get(self, session_id: str) -> list[dict[str, str]]:
        return list(self._messages[session_id])

