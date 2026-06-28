from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocumentChunk:
    id: str
    text: str
    source_path: str
    title: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None


@dataclass
class RetrievalResult:
    chunk: DocumentChunk
    score: float
    matched_terms: list[str] = field(default_factory=list)
    keyword_score: float = 0.0
    vector_score: float = 0.0


@dataclass
class SourceRef:
    title: str
    path: str
    score: float
    snippet: str


@dataclass
class ChatResponse:
    answer: str
    session_id: str
    sources: list[SourceRef]
    used_fallback: bool = False
