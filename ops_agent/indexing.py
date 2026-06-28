from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

from .models import DocumentChunk
from .embedding import BaseEmbeddingClient


FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)
HEADING = re.compile(r"^(#{1,3})\s+(.+)$", re.M)


class KnowledgeIndexer:
    def __init__(self, root: str | Path, chunk_size: int = 1200, chunk_overlap: int = 180):
        self.root = Path(root)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def build_chunks(self) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        for path in sorted(self.root.rglob("*.md")):
            text = path.read_text(encoding="utf-8", errors="ignore")
            metadata, body = self._extract_metadata(text)
            title = self._extract_title(body) or path.stem
            rel_path = path.relative_to(self.root).as_posix()
            for index, chunk_text in enumerate(self._split_text(body)):
                chunk_id = hashlib.sha1(f"{rel_path}:{index}:{chunk_text[:80]}".encode("utf-8")).hexdigest()
                chunks.append(
                    DocumentChunk(
                        id=chunk_id,
                        text=chunk_text.strip(),
                        source_path=rel_path,
                        title=title,
                        metadata=metadata.copy(),
                    )
                )
        return chunks

    def save(self, chunks: list[DocumentChunk], index_path: str | Path) -> None:
        path = Path(index_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [chunk.__dict__ for chunk in chunks]
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def attach_embeddings(
        self,
        chunks: list[DocumentChunk],
        embedder: BaseEmbeddingClient,
        batch_size: int = 64,
    ) -> None:
        pending = [chunk for chunk in chunks if not chunk.embedding]
        for start in range(0, len(pending), batch_size):
            batch = pending[start : start + batch_size]
            texts = [self._embedding_text(chunk) for chunk in batch]
            vectors = embedder.embed_texts(texts)
            for chunk, vector in zip(batch, vectors):
                chunk.embedding = vector

    @staticmethod
    def load(index_path: str | Path) -> list[DocumentChunk]:
        path = Path(index_path)
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [DocumentChunk(**item) for item in payload]

    def _extract_metadata(self, text: str) -> tuple[dict[str, Any], str]:
        match = FRONT_MATTER.match(text)
        if not match:
            return {}, text
        try:
            metadata = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            metadata = {}
        return metadata, text[match.end() :]

    @staticmethod
    def _extract_title(text: str) -> str | None:
        match = HEADING.search(text)
        return match.group(2).strip() if match else None

    @staticmethod
    def _embedding_text(chunk: DocumentChunk) -> str:
        metadata = " ".join(str(value) for value in chunk.metadata.values())
        return f"{chunk.title}\n{metadata}\n{chunk.source_path}\n{chunk.text}"

    def _split_text(self, text: str) -> list[str]:
        sections = self._split_by_headings(text)
        chunks: list[str] = []
        for section in sections:
            if len(section) <= self.chunk_size:
                chunks.append(section)
                continue
            start = 0
            while start < len(section):
                end = min(start + self.chunk_size, len(section))
                chunks.append(section[start:end])
                if end >= len(section):
                    break
                start = max(0, end - self.chunk_overlap)
        return [chunk for chunk in chunks if chunk.strip()]

    @staticmethod
    def _split_by_headings(text: str) -> list[str]:
        matches = list(HEADING.finditer(text))
        if not matches:
            return [text]
        sections: list[str] = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            sections.append(text[start:end])
        return sections
