from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path

from .config import VectorStoreConfig
from .embedding import cosine_similarity
from .models import DocumentChunk, RetrievalResult


class BaseVectorStore(ABC):
    @abstractmethod
    def rebuild(self, chunks: list[DocumentChunk]) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_chunks(self) -> list[DocumentChunk]:
        raise NotImplementedError

    @abstractmethod
    def search(self, query_vector: list[float], top_k: int = 6) -> list[RetrievalResult]:
        raise NotImplementedError


class SqliteVectorStore(BaseVectorStore):
    def __init__(self, config: VectorStoreConfig):
        self.config = config
        self.path = Path(config.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def rebuild(self, chunks: list[DocumentChunk]) -> None:
        with self._connect() as conn:
            conn.execute("delete from chunks where collection = ?", (self.config.collection,))
            conn.executemany(
                """
                insert into chunks (collection, id, source_path, title, text, metadata, embedding)
                values (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        self.config.collection,
                        chunk.id,
                        chunk.source_path,
                        chunk.title,
                        chunk.text,
                        json.dumps(chunk.metadata, ensure_ascii=False),
                        json.dumps(chunk.embedding or [], ensure_ascii=False),
                    )
                    for chunk in chunks
                ],
            )

    def load_chunks(self) -> list[DocumentChunk]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                select id, source_path, title, text, metadata, embedding
                from chunks
                where collection = ?
                order by rowid
                """,
                (self.config.collection,),
            ).fetchall()
        return [
            DocumentChunk(
                id=row[0],
                source_path=row[1],
                title=row[2],
                text=row[3],
                metadata=json.loads(row[4] or "{}"),
                embedding=json.loads(row[5] or "[]"),
            )
            for row in rows
        ]

    def search(self, query_vector: list[float], top_k: int = 6) -> list[RetrievalResult]:
        results: list[RetrievalResult] = []
        for chunk in self.load_chunks():
            vector_score = max(0.0, cosine_similarity(query_vector, chunk.embedding))
            if vector_score <= 0:
                continue
            results.append(
                RetrievalResult(
                    chunk=chunk,
                    score=vector_score,
                    vector_score=vector_score,
                )
            )
        return sorted(results, key=lambda item: item.score, reverse=True)[:top_k]

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                create table if not exists chunks (
                    collection text not null,
                    id text not null,
                    source_path text not null,
                    title text not null,
                    text text not null,
                    metadata text not null,
                    embedding text not null,
                    primary key (collection, id)
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)


def create_vector_store(config: VectorStoreConfig) -> BaseVectorStore:
    if config.provider != "sqlite":
        raise ValueError(f"Unsupported vector store provider: {config.provider}")
    return SqliteVectorStore(config)
