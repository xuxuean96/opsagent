from __future__ import annotations

import re
from dataclasses import dataclass, field


RISK_TERMS = ("删除", "覆盖", "重装", "rm -rf", "关闭防火墙", "开放端口")
COMMAND_RE = re.compile(r"(^|\n)\s*(systemctl|ps\s|netstat|ss\s|tail\s|cat\s|grep\s|java\s|- ./|./|sh\s)", re.I)


@dataclass
class AnswerValidation:
    passed: bool
    issues: list[str] = field(default_factory=list)


def validate_answer(answer: str, has_sources: bool) -> AnswerValidation:
    issues: list[str] = []
    if has_sources and "来源" not in answer and "参考" not in answer:
        issues.append("命中知识库但没有说明来源")
    if any(term in answer for term in RISK_TERMS) and "风险" not in answer:
        issues.append("包含高危操作但没有风险提示")
    if COMMAND_RE.search(answer) and "```" not in answer:
        issues.append("包含命令但没有使用代码块")
    return AnswerValidation(passed=not issues, issues=issues)


def append_validation_notes(answer: str, validation: AnswerValidation) -> str:
    if validation.passed:
        return answer
    notes = "\n".join(f"- {issue}" for issue in validation.issues)
    return f"{answer.rstrip()}\n\n输出校验提示\n{notes}"
