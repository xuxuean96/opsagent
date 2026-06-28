from __future__ import annotations

import re
from dataclasses import dataclass, field


REQUIRED_SECTIONS = ("判断结论", "优先检查", "处理步骤", "需要补充的信息", "来源")
RISK_TERMS = ("删除", "覆盖", "重装", "rm -rf", "格式化", "关闭防火墙", "开放端口")
COMMAND_RE = re.compile(r"(^|\n)\s*(systemctl|ps\s|netstat|ss\s|tail\s|cat\s|grep\s|java\s|- ./|./|sh\s)", re.I)


@dataclass
class AnswerValidation:
    passed: bool
    issues: list[str] = field(default_factory=list)


def validate_answer(answer: str, has_sources: bool) -> AnswerValidation:
    issues: list[str] = []
    for section in REQUIRED_SECTIONS:
        if section not in answer:
            issues.append(f"缺少回答段落：{section}")
    if has_sources and "来源" not in answer:
        issues.append("命中知识库但回答没有来源段落")
    if any(term in answer for term in RISK_TERMS) and "风险" not in answer:
        issues.append("包含高危操作但缺少风险提示")
    if COMMAND_RE.search(answer) and "```" not in answer:
        issues.append("包含命令但没有使用代码块")
    return AnswerValidation(passed=not issues, issues=issues)


def append_validation_notes(answer: str, validation: AnswerValidation) -> str:
    if validation.passed:
        return answer
    notes = "\n".join(f"- {issue}" for issue in validation.issues)
    return f"{answer.rstrip()}\n\n## 输出校验提示\n{notes}"
