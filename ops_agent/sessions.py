from __future__ import annotations

import base64
import binascii
import json
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from uuid import uuid4


PROJECT_CODE_RE = re.compile(r"^[A-Z]{2,12}$")


class FeedbackStatus(str, Enum):
    PENDING = "pending_feedback"
    RESOLVED = "resolved"
    PARTIAL = "partial"
    UNRESOLVED = "unresolved"


class AdminStatus(str, Enum):
    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


@dataclass
class Attachment:
    id: str
    session_id: str
    filename: str
    content_type: str
    path: str
    extracted_text: str
    created_at: str


@dataclass
class SupportSession:
    id: str
    project_code: str
    implementer: str
    component: str | None
    feedback_status: FeedbackStatus
    feedback_note: str | None
    admin_requested: bool
    created_at: str
    updated_at: str
    attachments: list[Attachment] = field(default_factory=list)


@dataclass
class AdminCase:
    id: str
    session_id: str
    reason: str
    status: AdminStatus
    root_cause: str | None
    solution: str | None
    draft_path: str | None
    created_at: str
    updated_at: str


def validate_project_code(value: str) -> str:
    code = value.strip().upper()
    if not PROJECT_CODE_RE.fullmatch(code):
        raise ValueError("项目名称只能填写拼音首字母缩写，格式为 2-12 位大写英文字母。")
    return code


class SessionStore:
    def __init__(
        self,
        path: str | Path,
        upload_dir: str | Path,
        draft_dir: str | Path,
        max_upload_bytes: int = 5 * 1024 * 1024,
        allowed_content_types: list[str] | None = None,
        allowed_extensions: list[str] | None = None,
    ):
        self.path = Path(path)
        self.upload_dir = Path(upload_dir)
        self.draft_dir = Path(draft_dir)
        self.max_upload_bytes = max_upload_bytes
        self.allowed_content_types = set(allowed_content_types or [])
        self.allowed_extensions = {item.lower() for item in (allowed_extensions or [])}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.draft_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self, project_code: str, implementer: str, component: str | None = None) -> SupportSession:
        now = _now()
        session = SupportSession(
            id=str(uuid4()),
            project_code=validate_project_code(project_code),
            implementer=implementer.strip(),
            component=component.strip() if component else None,
            feedback_status=FeedbackStatus.PENDING,
            feedback_note=None,
            admin_requested=False,
            created_at=now,
            updated_at=now,
        )
        if not session.implementer:
            raise ValueError("实施人员不能为空。")
        self._append({"type": "session", "payload": _session_to_dict(session)})
        return session

    def get_session(self, session_id: str) -> SupportSession | None:
        return self._sessions().get(session_id)

    def list_sessions(self, limit: int = 100) -> list[SupportSession]:
        return sorted(self._sessions().values(), key=lambda item: item.updated_at, reverse=True)[:limit]

    def pending_feedback_sessions(self) -> list[SupportSession]:
        return [session for session in self.list_sessions(limit=10000) if session.feedback_status == FeedbackStatus.PENDING]

    def attachment_context(self, session_id: str, max_chars: int = 4000) -> str:
        session = self.get_session(session_id)
        if session is None:
            return ""
        blocks = [
            f"附件：{item.filename}\n{item.extracted_text.strip()}"
            for item in session.attachments
            if item.extracted_text.strip()
        ]
        return "\n\n".join(blocks)[:max_chars]

    def record_feedback(self, session_id: str, status: FeedbackStatus, note: str | None = None) -> SupportSession:
        session = self._require_session(session_id)
        session.feedback_status = status
        session.feedback_note = note
        session.updated_at = _now()
        self._append({"type": "session", "payload": _session_to_dict(session)})
        return session

    def add_attachment(self, session_id: str, filename: str, content_type: str, content_base64: str) -> Attachment:
        session = self._require_session(session_id)
        raw = _decode_upload(content_base64)
        self._validate_upload(filename, content_type, len(raw))
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", filename).strip("_") or "upload.bin"
        path = self.upload_dir / session_id / f"{uuid4()}-{safe_name}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        attachment = Attachment(
            id=str(uuid4()),
            session_id=session_id,
            filename=filename,
            content_type=content_type,
            path=path.as_posix(),
            extracted_text=_extract_text(path, raw, filename, content_type),
            created_at=_now(),
        )
        session.attachments.append(attachment)
        session.updated_at = _now()
        self._append({"type": "session", "payload": _session_to_dict(session)})
        return attachment

    def request_admin(self, session_id: str, reason: str) -> AdminCase:
        session = self._require_session(session_id)
        now = _now()
        case = AdminCase(
            id=str(uuid4()),
            session_id=session_id,
            reason=reason.strip() or "当前会话多轮排查后仍无法解决，需要管理员介入。",
            status=AdminStatus.REQUESTED,
            root_cause=None,
            solution=None,
            draft_path=None,
            created_at=now,
            updated_at=now,
        )
        session.admin_requested = True
        session.updated_at = now
        self._append({"type": "session", "payload": _session_to_dict(session)})
        self._append({"type": "admin_case", "payload": _admin_case_to_dict(case)})
        return case

    def get_admin_case(self, case_id: str) -> AdminCase | None:
        return self._admin_cases().get(case_id)

    def list_admin_cases(self, limit: int = 100) -> list[AdminCase]:
        return sorted(self._admin_cases().values(), key=lambda item: item.updated_at, reverse=True)[:limit]

    def resolve_admin_case(self, case_id: str, root_cause: str, solution: str, create_draft: bool = True) -> AdminCase:
        case = self._require_admin_case(case_id)
        case.status = AdminStatus.RESOLVED
        case.root_cause = root_cause.strip()
        case.solution = solution.strip()
        case.updated_at = _now()
        if create_draft:
            case.draft_path = self._write_knowledge_draft(case)
        self._append({"type": "admin_case", "payload": _admin_case_to_dict(case)})
        return case

    def generate_candidate_from_session(self, session_id: str, question: str, answer: str) -> str:
        session = self._require_session(session_id)
        if session.feedback_status != FeedbackStatus.RESOLVED:
            raise ValueError("只有已解决会话可以自动生成候选知识草稿。")
        path = self.draft_dir / f"{session.project_code}-{session.id[:8]}-已解决会话草稿.md"
        body = f"""---
type: runbook
component: {session.component or "待补充"}
scenario: 已解决会话沉淀
priority: P2
tags: [{session.component or "待补充"}, 已解决会话, {session.project_code}]
status: draft
review_status: pending
---

# 已解决会话沉淀：{session.project_code}

## 会话信息

- 项目缩写：{session.project_code}
- 实施人员：{session.implementer}
- 会话 ID：{session.id}

## 用户问题

{question}

## 当前答案

{answer}

## 附件摘要

{self.attachment_context(session.id, max_chars=2000) or "无附件。"}

## 审核清单

1. 删除客户敏感信息。
2. 补齐适用组件、场景、判断依据、处理步骤和验证方式。
3. 执行知识库治理检查。
4. 审核通过后发布到正式知识库。
"""
        path.write_text(body, encoding="utf-8")
        return path.as_posix()

    def publish_draft(self, draft_path: str | Path, target_dir: str | Path) -> str:
        source = Path(draft_path)
        if not source.exists():
            raise FileNotFoundError(f"Draft not found: {draft_path}")
        target = Path(target_dir)
        target.mkdir(parents=True, exist_ok=True)
        content = source.read_text(encoding="utf-8").replace("status: draft", "status: active", 1)
        content = content.replace("review_status: approved", "review_status: published", 1)
        destination = target / source.name
        destination.write_text(content, encoding="utf-8")
        return destination.as_posix()

    def feedback_summary(self) -> dict[str, int]:
        summary = {status.value: 0 for status in FeedbackStatus}
        summary["admin_requested"] = 0
        for session in self.list_sessions(limit=10000):
            summary[session.feedback_status.value] += 1
            if session.admin_requested:
                summary["admin_requested"] += 1
        return summary

    def review_analytics(self, task_records: list[dict] | None = None) -> dict:
        sessions = self.list_sessions(limit=10000)
        by_project: dict[str, int] = {}
        by_component: dict[str, int] = {}
        for session in sessions:
            by_project[session.project_code] = by_project.get(session.project_code, 0) + 1
            component = session.component or "未填写"
            by_component[component] = by_component.get(component, 0) + 1
        failed_tasks = 0
        source_misses: dict[str, int] = {}
        for task in task_records or []:
            if task.get("status") == "failed":
                failed_tasks += 1
            if task.get("answer") and "输出校验提示" in task["answer"]:
                source_misses["answer_validation_warning"] = source_misses.get("answer_validation_warning", 0) + 1
        return {
            "sessions": len(sessions),
            "feedback": self.feedback_summary(),
            "by_project": dict(sorted(by_project.items(), key=lambda item: item[1], reverse=True)[:10]),
            "by_component": dict(sorted(by_component.items(), key=lambda item: item[1], reverse=True)[:10]),
            "admin_cases": len(self.list_admin_cases(limit=10000)),
            "failed_tasks": failed_tasks,
            "signals": source_misses,
        }

    def _validate_upload(self, filename: str, content_type: str, size: int) -> None:
        if size > self.max_upload_bytes:
            raise ValueError(f"附件超过大小限制：最大 {self.max_upload_bytes} 字节。")
        suffix = Path(filename).suffix.lower()
        normalized_type = (content_type or "application/octet-stream").split(";")[0].strip().lower()
        type_allowed = not self.allowed_content_types or normalized_type in self.allowed_content_types
        ext_allowed = not self.allowed_extensions or suffix in self.allowed_extensions
        if not type_allowed and not ext_allowed:
            raise ValueError("附件类型不在允许范围内。")

    def _write_knowledge_draft(self, case: AdminCase) -> str:
        session = self._require_session(case.session_id)
        path = self.draft_dir / f"{session.project_code}-{case.id[:8]}-管理员沉淀.md"
        body = f"""---
type: runbook
component: {session.component or "待补充"}
scenario: 管理员介入沉淀
priority: P2
tags: [{session.component or "待补充"}, 管理员介入, {session.project_code}]
status: draft
review_status: pending
---

# 管理员介入沉淀：{session.project_code}

## 会话信息

- 项目缩写：{session.project_code}
- 实施人员：{session.implementer}
- 会话 ID：{session.id}

## 问题原因

{case.root_cause}

## 解决方案

{case.solution}

## 后续审核

1. 补充适用组件和场景。
2. 补充判断依据、处理步骤和验证方式。
3. 执行知识库治理检查。
4. 审核通过后将 `status` 改为 `active`。
"""
        path.write_text(body, encoding="utf-8")
        return path.as_posix()

    def _require_session(self, session_id: str) -> SupportSession:
        session = self.get_session(session_id)
        if session is None:
            raise KeyError(f"Session not found: {session_id}")
        return session

    def _require_admin_case(self, case_id: str) -> AdminCase:
        case = self.get_admin_case(case_id)
        if case is None:
            raise KeyError(f"Admin case not found: {case_id}")
        return case

    def _sessions(self) -> dict[str, SupportSession]:
        sessions: dict[str, SupportSession] = {}
        for record in self._records():
            if record.get("type") == "session":
                session = _session_from_dict(record["payload"])
                sessions[session.id] = session
        return sessions

    def _admin_cases(self) -> dict[str, AdminCase]:
        cases: dict[str, AdminCase] = {}
        for record in self._records():
            if record.get("type") == "admin_case":
                case = _admin_case_from_dict(record["payload"])
                cases[case.id] = case
        return cases

    def _records(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def _append(self, record: dict) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _decode_upload(content_base64: str) -> bytes:
    try:
        return base64.b64decode(content_base64, validate=True)
    except binascii.Error as exc:
        raise ValueError("附件内容不是有效的 base64。") from exc


def _extract_text(path: Path, raw: bytes, filename: str, content_type: str) -> str:
    lower = filename.lower()
    if content_type.startswith("text/") or lower.endswith((".txt", ".log", ".xml", ".json", ".ini", ".conf")):
        return raw.decode("utf-8", errors="ignore")
    if content_type.startswith("image/") or lower.endswith((".png", ".jpg", ".jpeg", ".bmp")):
        text = _ocr_image(path)
        return text or "图片已上传，但当前环境没有可用 OCR 引擎或未识别到文字。"
    return "附件已上传。当前类型不支持自动文本提取，请管理员下载查看。"


def _ocr_image(path: Path) -> str:
    try:
        import pytesseract
        from PIL import Image
    except Exception:
        return ""
    try:
        return pytesseract.image_to_string(Image.open(path), lang="chi_sim+eng").strip()
    except Exception:
        return ""


def _session_to_dict(session: SupportSession) -> dict:
    payload = asdict(session)
    payload["feedback_status"] = session.feedback_status.value
    payload["attachments"] = [asdict(item) for item in session.attachments]
    return payload


def _session_from_dict(payload: dict) -> SupportSession:
    data = payload.copy()
    data["feedback_status"] = FeedbackStatus(data["feedback_status"])
    data["attachments"] = [Attachment(**item) for item in data.get("attachments", [])]
    return SupportSession(**data)


def _admin_case_to_dict(case: AdminCase) -> dict:
    payload = asdict(case)
    payload["status"] = case.status.value
    return payload


def _admin_case_from_dict(payload: dict) -> AdminCase:
    data = payload.copy()
    data["status"] = AdminStatus(data["status"])
    return AdminCase(**data)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
