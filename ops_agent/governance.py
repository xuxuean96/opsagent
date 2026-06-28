from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)
HEADING = re.compile(r"^#\s+(.+)$", re.M)
WHITESPACE = re.compile(r"\s+")

REQUIRED_METADATA = ("type", "component", "scenario", "priority", "tags", "status")
VALID_TYPES = {"runbook", "faq", "reference", "strategy", "testcase", "standard", "overview"}
VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}
VALID_STATUSES = {"active", "draft", "deprecated"}
MIN_CONTENT_CHARS = 40
MIN_DUPLICATE_CHARS = 20

DIRECTORY_TYPE_HINTS = {
    "01-概览": "overview",
    "02-安装部署": "reference",
    "03-调用方式": "reference",
    "04-报错排查": "runbook",
    "05-日志与证据": "reference",
    "06-FAQ": "faq",
    "07-故障卡片": "runbook",
    "08-问答样例": "faq",
    "09-反问策略": "strategy",
    "10-原文拆分": "reference",
    "11-测试集": "testcase",
    "12-规范": "standard",
    "13-待审核": "runbook",
    "99-附录": "reference",
}


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class GovernanceIssue:
    severity: Severity
    code: str
    path: str
    message: str


@dataclass
class GovernanceReport:
    root: str
    file_count: int
    issues: list[GovernanceIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == Severity.INFO)

    @property
    def score(self) -> int:
        if self.file_count == 0:
            return 0
        penalty = self.error_count * 10 + self.warning_count * 3 + self.info_count
        return max(0, min(100, 100 - penalty))

    def to_markdown(self) -> str:
        lines = [
            "# 知识库治理报告",
            "",
            f"- 知识库路径：`{self.root}`",
            f"- 文档数量：{self.file_count}",
            f"- 质量分：{self.score}",
            f"- 错误：{self.error_count}",
            f"- 警告：{self.warning_count}",
            f"- 提示：{self.info_count}",
            "",
        ]
        if not self.issues:
            lines.append("未发现治理问题。")
            return "\n".join(lines)
        lines.extend(["## 问题清单", ""])
        for issue in sorted(self.issues, key=lambda item: (item.severity.value, item.path, item.code)):
            lines.append(f"- **{issue.severity.value}** `{issue.code}` `{issue.path}`：{issue.message}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "file_count": self.file_count,
            "score": self.score,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "issues": [
                {
                    "severity": issue.severity.value,
                    "code": issue.code,
                    "path": issue.path,
                    "message": issue.message,
                }
                for issue in self.issues
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class KnowledgeGovernance:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def inspect(self) -> GovernanceReport:
        issues: list[GovernanceIssue] = []
        fingerprints: dict[str, list[str]] = defaultdict(list)
        files = sorted(self.root.rglob("*.md"))
        for path in files:
            rel_path = path.relative_to(self.root).as_posix()
            text = path.read_text(encoding="utf-8", errors="ignore")
            metadata, body, metadata_present = self._extract_metadata(text)
            issues.extend(self._inspect_file(rel_path, metadata, body, metadata_present))
            fingerprint = self._fingerprint(body)
            if fingerprint:
                fingerprints[fingerprint].append(rel_path)

        for paths in fingerprints.values():
            if len(paths) < 2:
                continue
            joined = ", ".join(paths)
            for path in paths:
                issues.append(GovernanceIssue(Severity.WARNING, "DUPLICATE_CONTENT", path, f"文档内容与其他文件高度重复：{joined}"))
        return GovernanceReport(root=self.root.as_posix(), file_count=len(files), issues=issues)

    def inspect_file(self, file_path: str | Path) -> GovernanceReport:
        path = Path(file_path)
        text = path.read_text(encoding="utf-8", errors="ignore")
        metadata, body, metadata_present = self._extract_metadata(text)
        issues = self._inspect_file(path.name, metadata, body, metadata_present)
        return GovernanceReport(root=path.parent.as_posix(), file_count=1, issues=issues)

    def write_report(self, output_path: str | Path) -> GovernanceReport:
        report = self.inspect()
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report.to_json() if path.suffix.lower() == ".json" else report.to_markdown(), encoding="utf-8")
        return report

    def _inspect_file(self, rel_path: str, metadata: dict[str, Any], body: str, metadata_present: bool) -> list[GovernanceIssue]:
        issues: list[GovernanceIssue] = []
        if not metadata_present:
            issues.append(GovernanceIssue(Severity.WARNING, "MISSING_FRONT_MATTER", rel_path, "缺少 YAML front matter。"))
        for key in REQUIRED_METADATA:
            if key not in metadata:
                issues.append(GovernanceIssue(Severity.WARNING, "MISSING_METADATA", rel_path, f"缺少元数据字段 `{key}`。"))
        doc_type = metadata.get("type")
        if doc_type and doc_type not in VALID_TYPES:
            issues.append(GovernanceIssue(Severity.ERROR, "INVALID_TYPE", rel_path, f"`type` 不在允许范围：{doc_type}。"))
        priority = metadata.get("priority")
        if priority and priority not in VALID_PRIORITIES:
            issues.append(GovernanceIssue(Severity.ERROR, "INVALID_PRIORITY", rel_path, f"`priority` 不在允许范围：{priority}。"))
        status = metadata.get("status")
        if status and status not in VALID_STATUSES:
            issues.append(GovernanceIssue(Severity.ERROR, "INVALID_STATUS", rel_path, f"`status` 不在允许范围：{status}。"))
        tags = metadata.get("tags")
        if "tags" in metadata and not self._valid_tags(tags):
            issues.append(GovernanceIssue(Severity.ERROR, "INVALID_TAGS", rel_path, "`tags` 必须是非空列表。"))
        expected_type = self._expected_type(rel_path)
        if expected_type and doc_type and doc_type != expected_type:
            issues.append(GovernanceIssue(Severity.WARNING, "DIRECTORY_TYPE_MISMATCH", rel_path, f"目录建议 type 为 `{expected_type}`，当前为 `{doc_type}`。"))
        if not HEADING.search(body):
            issues.append(GovernanceIssue(Severity.WARNING, "MISSING_H1", rel_path, "正文缺少一级标题。"))
        if len(body.strip()) < MIN_CONTENT_CHARS:
            issues.append(GovernanceIssue(Severity.WARNING, "CONTENT_TOO_SHORT", rel_path, "正文过短，检索价值较低。"))
        if status == "deprecated":
            issues.append(GovernanceIssue(Severity.INFO, "DEPRECATED_DOCUMENT", rel_path, "文档已标记废弃，检索时应降低权重。"))
        return issues

    @staticmethod
    def _extract_metadata(text: str) -> tuple[dict[str, Any], str, bool]:
        match = FRONT_MATTER.match(text)
        if not match:
            return {}, text, False
        try:
            metadata = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            return {}, text[match.end() :], True
        return metadata, text[match.end() :], True

    @staticmethod
    def _fingerprint(text: str) -> str | None:
        normalized = WHITESPACE.sub("", text).strip().lower()
        if len(normalized) < MIN_DUPLICATE_CHARS:
            return None
        return hashlib.sha1(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _valid_tags(tags: Any) -> bool:
        return isinstance(tags, list) and bool(tags) and all(isinstance(tag, str) and tag.strip() for tag in tags)

    @staticmethod
    def _expected_type(rel_path: str) -> str | None:
        for prefix, doc_type in DIRECTORY_TYPE_HINTS.items():
            if rel_path.startswith(prefix):
                return doc_type
        return None
