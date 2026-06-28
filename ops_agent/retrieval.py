from __future__ import annotations

import math
import re
from collections import Counter

from .embedding import BaseEmbeddingClient, cosine_similarity
from .models import DocumentChunk, RetrievalResult


TOKEN_RE = re.compile(r"[A-Za-z0-9_\-.]+|[\u4e00-\u9fff]+")

PRIORITY_BOOSTS = [
    ("07-故障卡片", 1.8),
    ("04-报错排查", 1.35),
    ("08-问答样例", 1.2),
    ("09-反问策略", 1.15),
    ("02-安装部署", 1.1),
    ("10-原文拆分", 0.85),
    ("11-测试集", 0.35),
    ("12-规范", 0.45),
    ("13-待审核", 0.5),
]


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in TOKEN_RE.findall(text):
        token = raw.lower()
        if re.fullmatch(r"[\u4e00-\u9fff]+", token):
            tokens.append(token)
            for size in (2, 3, 4):
                tokens.extend(token[i : i + size] for i in range(0, max(0, len(token) - size + 1)))
        else:
            tokens.append(token)
    return tokens


class HybridRetriever:
    def __init__(self, chunks: list[DocumentChunk], embedder: BaseEmbeddingClient | None = None):
        self.chunks = chunks
        self.embedder = embedder
        self.doc_terms = [Counter(tokenize(self._search_text(chunk))) for chunk in chunks]
        self.df: Counter[str] = Counter()
        for terms in self.doc_terms:
            self.df.update(terms.keys())

    def search(self, query: str, top_k: int = 6) -> list[RetrievalResult]:
        query_terms = Counter(tokenize(query))
        if not self.chunks:
            return []
        query_vector = self.embedder.embed_query(query) if self.embedder else None
        candidates: list[RetrievalResult] = []
        total_docs = len(self.chunks)
        for chunk, terms in zip(self.chunks, self.doc_terms):
            keyword_score = 0.0
            matched: list[str] = []
            if query_terms:
                for term, qtf in query_terms.items():
                    tf = terms.get(term, 0)
                    if not tf:
                        continue
                    idf = math.log((1 + total_docs) / (1 + self.df[term])) + 1
                    keyword_score += (1 + math.log(tf)) * idf * qtf
                    matched.append(term)
            vector_score = max(0.0, cosine_similarity(query_vector, chunk.embedding))
            score = self._apply_path_boost(chunk.source_path, keyword_score + vector_score)
            if score <= 0:
                continue
            candidates.append(
                RetrievalResult(
                    chunk=chunk,
                    score=score,
                    matched_terms=matched,
                    keyword_score=keyword_score,
                    vector_score=vector_score,
                )
            )
        return self._dedupe_and_rank(candidates, top_k=top_k)

    @staticmethod
    def _search_text(chunk: DocumentChunk) -> str:
        metadata = " ".join(str(v) for v in chunk.metadata.values())
        return f"{chunk.title}\n{metadata}\n{chunk.source_path}\n{chunk.text}"

    @staticmethod
    def _apply_path_boost(path: str, score: float) -> float:
        for marker, boost in PRIORITY_BOOSTS:
            if marker in path:
                return score * boost
        return score

    @staticmethod
    def _dedupe_and_rank(candidates: list[RetrievalResult], top_k: int) -> list[RetrievalResult]:
        best_by_path: dict[str, RetrievalResult] = {}
        for item in sorted(candidates, key=lambda result: result.score, reverse=True):
            current = best_by_path.get(item.chunk.source_path)
            if current is None or item.score > current.score:
                best_by_path[item.chunk.source_path] = item
        return sorted(best_by_path.values(), key=lambda result: result.score, reverse=True)[:top_k]
