from __future__ import annotations

import hashlib
import json
import math
import re
import urllib.error
import urllib.request
from abc import ABC, abstractmethod

from .config import EmbeddingConfig


TOKEN_RE = re.compile(r"[A-Za-z0-9_\-.]+|[\u4e00-\u9fff]+")


class EmbeddingError(RuntimeError):
    pass


class BaseEmbeddingClient(ABC):
    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


class LocalHashEmbeddingClient(BaseEmbeddingClient):
    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in _tokens(text):
            digest = hashlib.sha1(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        return normalize(vector)


class OpenAICompatibleEmbeddingClient(BaseEmbeddingClient):
    def __init__(self, config: EmbeddingConfig, timeout_seconds: int = 60):
        self.config = config
        self.timeout_seconds = timeout_seconds

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self.config.api_key:
            raise EmbeddingError("embedding api_key is not configured")
        url = self.config.base_url.rstrip("/") + "/embeddings"
        payload = {"model": self.config.model, "input": texts}
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise EmbeddingError(str(exc)) from exc
        try:
            items = sorted(data["data"], key=lambda item: item["index"])
            return [normalize([float(value) for value in item["embedding"]]) for item in items]
        except (KeyError, TypeError, ValueError) as exc:
            raise EmbeddingError(f"Unexpected embedding response: {data}") from exc


def create_embedding_client(config: EmbeddingConfig) -> BaseEmbeddingClient:
    if config.provider == "openai-compatible":
        return OpenAICompatibleEmbeddingClient(config)
    return LocalHashEmbeddingClient()


def cosine_similarity(left: list[float] | None, right: list[float] | None) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))


def normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _tokens(text: str) -> list[str]:
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
