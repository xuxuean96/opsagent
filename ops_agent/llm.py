from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod

from .config import LLMConfig


class LLMError(RuntimeError):
    pass


class BaseLLMClient(ABC):
    @abstractmethod
    def complete(self, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError


class MockLLMClient(BaseLLMClient):
    def complete(self, messages: list[dict[str, str]]) -> str:
        user = messages[-1]["content"] if messages else ""
        return (
            "根据知识库命中内容，建议按以下顺序排查：\n\n"
            "1. 先确认现象和运行环境。\n"
            "2. 再检查进程、端口、防火墙和配置。\n"
            "3. 如果涉及 KMVue Linux 报加密卡连接不上，先确认 kmconvertservice 能独立启动。\n\n"
            f"用户问题：{user[:200]}"
        )


class OpenAICompatibleClient(BaseLLMClient):
    def __init__(self, config: LLMConfig):
        self.config = config

    def complete(self, messages: list[dict[str, str]]) -> str:
        if not self.config.api_key:
            raise LLMError("LLM api_key is not configured")
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        data = None
        attempts = max(1, self.config.retries + 1)
        for attempt in range(attempts):
            try:
                with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                    data = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.URLError as exc:
                if attempt >= attempts - 1:
                    raise LLMError(str(exc)) from exc
                time.sleep(self.config.retry_backoff_seconds * (attempt + 1))
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Unexpected LLM response: {data}") from exc


def create_llm_client(config: LLMConfig, require_real: bool = False) -> BaseLLMClient:
    if require_real and config.provider == "mock":
        raise LLMError("mock LLM provider is not allowed. Configure llm.provider=openai-compatible.")
    if config.provider == "mock":
        return MockLLMClient()
    return OpenAICompatibleClient(config)


def require_llm_available(client: BaseLLMClient) -> None:
    try:
        client.complete(
            [
                {
                    "role": "system",
                    "content": "You are a health-check endpoint. Reply with OK only.",
                },
                {
                    "role": "user",
                    "content": "OK",
                },
            ]
        )
    except LLMError as exc:
        raise LLMError(f"LLM health check failed: {exc}") from exc
