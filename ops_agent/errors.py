from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApiError:
    code: str
    message: str
    hint: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "hint": self.hint,
        }


def llm_unavailable_error() -> ApiError:
    return ApiError(
        code="LLM_UNAVAILABLE",
        message="LLM 当前不可用，无法生成排障回答。",
        hint="请检查模型地址、API Key、模型名称、网络连通性和服务商额度后重试。",
    )
