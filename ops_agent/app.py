from __future__ import annotations

import json
import os
import time
from collections import defaultdict, deque
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .alerts import AlertCenter
from .auth import AuthManager, AuthSession, COOKIE_NAME, hash_password
from .config import AppConfig
from .embedding import EmbeddingError, LocalHashEmbeddingClient, create_embedding_client
from .errors import llm_unavailable_error
from .evaluation import EvaluationRunner, list_evaluation_history
from .governance import KnowledgeGovernance
from .indexing import KnowledgeIndexer
from .jobs import JobManager, JobStatus, JobStore
from .llm import LLMError, create_llm_client, require_llm_available
from .logger import JsonlLogger
from .maintenance import create_backup, list_backups, prune_backups, restore_backup, sqlite_integrity_check, verify_backup
from .memory import ConversationMemory
from .orchestrator import ChatOrchestrator
from .retrieval import HybridRetriever
from .sessions import FeedbackStatus, SessionStore
from .tasks import TaskStatus, TaskStore
from .vector_store import create_vector_store


class ChatRequest(BaseModel):
    message: str
    session_id: str


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateSessionRequest(BaseModel):
    project_code: str
    implementer: str
    component: str | None = None


class FeedbackRequest(BaseModel):
    status: str
    note: str | None = None


class AttachmentRequest(BaseModel):
    filename: str
    content_type: str
    content_base64: str


class AdminRequest(BaseModel):
    reason: str


class ResolveAdminRequest(BaseModel):
    root_cause: str
    solution: str
    create_draft: bool = True


class CandidateDraftRequest(BaseModel):
    question: str
    answer: str


class PublishDraftRequest(BaseModel):
    draft_path: str
    target_dir: str = "knowledge-base/07-故障卡片"


class ReviewDraftRequest(BaseModel):
    draft_path: str
    note: str | None = None


class BackupRequest(BaseModel):
    backup_dir: str | None = None


class RestoreRequest(BaseModel):
    archive_path: str


class UserUpsertRequest(BaseModel):
    username: str
    password: str | None = None
    role: str | None = None
    enabled: bool | None = None
    projects: list[str] | None = None
    components: list[str] | None = None


class UserPatchRequest(BaseModel):
    password: str | None = None
    role: str | None = None
    enabled: bool | None = None
    projects: list[str] | None = None
    components: list[str] | None = None


class AppState:
    def __init__(self) -> None:
        self.config = AppConfig.load()
        if self.config.auth.enabled and not (self.config.auth.password or self.config.auth.users):
            raise RuntimeError("auth.password/users or OPS_AGENT_ADMIN_PASSWORD must be configured")
        self.auth = AuthManager(self.config.auth)
        self.memory = ConversationMemory()
        self.logger = JsonlLogger(
            self.config.logging.path,
            max_bytes=self.config.logging.max_bytes,
            backup_count=self.config.logging.backup_count,
        )
        self.task_store = TaskStore(self.config.task.store_path)
        self.session_store = SessionStore(
            self.config.session.store_path,
            self.config.session.upload_dir,
            self.config.session.draft_dir,
            max_upload_bytes=self.config.session.max_upload_bytes,
            allowed_content_types=self.config.session.allowed_content_types,
            allowed_extensions=self.config.session.allowed_extensions,
        )
        self.vector_store = create_vector_store(self.config.vector_store)
        self.embedder = create_embedding_client(self.config.embedding)
        self.chunks = self._load_or_build_index()
        self._ensure_embeddings()
        self.retriever = HybridRetriever(self.chunks, embedder=self.embedder)
        self.llm = create_llm_client(self.config.llm, require_real=True)
        self._llm_health_check()
        self.orchestrator = ChatOrchestrator(self.config, self.retriever, self.llm, memory=self.memory, logger=self.logger)
        self.rate_counters: dict[str, deque[float]] = defaultdict(deque)
        self.metrics: dict[str, int] = defaultdict(int)
        self._csrf_secret = self.config.auth.secret_key or "ops-agent-csrf-secret"
        self.alert_center = AlertCenter("data/alerts.jsonl")
        self.job_store = JobStore(self.config.task.job_store_path)
        self.job_manager = JobManager(self.job_store, on_job_update=self.on_job_update)

    def _llm_health_check(self) -> None:
        require_llm_available(self.llm)

    def _load_or_build_index(self):
        vector_chunks = self.vector_store.load_chunks()
        if vector_chunks:
            return vector_chunks
        chunks = KnowledgeIndexer.load(self.config.index_path)
        if chunks:
            return chunks
        indexer = KnowledgeIndexer(
            self.config.knowledge_base_path,
            chunk_size=self.config.retrieval.chunk_size,
            chunk_overlap=self.config.retrieval.chunk_overlap,
        )
        chunks = indexer.build_chunks()
        self._attach_embeddings(indexer, chunks)
        indexer.save(chunks, self.config.index_path)
        self.vector_store.rebuild(chunks)
        return chunks

    def _ensure_embeddings(self) -> None:
        if self.chunks and all(chunk.embedding for chunk in self.chunks):
            return
        indexer = KnowledgeIndexer(
            self.config.knowledge_base_path,
            chunk_size=self.config.retrieval.chunk_size,
            chunk_overlap=self.config.retrieval.chunk_overlap,
        )
        self._attach_embeddings(indexer, self.chunks)
        indexer.save(self.chunks, self.config.index_path)
        self.vector_store.rebuild(self.chunks)

    def _attach_embeddings(self, indexer: KnowledgeIndexer, chunks) -> None:
        try:
            indexer.attach_embeddings(chunks, self.embedder)
        except EmbeddingError:
            self.embedder = LocalHashEmbeddingClient()
            indexer.attach_embeddings(chunks, self.embedder)

    def rebuild_index(self) -> int:
        indexer = KnowledgeIndexer(
            self.config.knowledge_base_path,
            chunk_size=self.config.retrieval.chunk_size,
            chunk_overlap=self.config.retrieval.chunk_overlap,
        )
        self.chunks = indexer.build_chunks()
        self._attach_embeddings(indexer, self.chunks)
        indexer.save(self.chunks, self.config.index_path)
        self.vector_store.rebuild(self.chunks)
        self.retriever = HybridRetriever(self.chunks, embedder=self.embedder)
        self.orchestrator = ChatOrchestrator(self.config, self.retriever, self.llm, memory=self.memory, logger=self.logger)
        return len(self.chunks)

    def answer_with_task(self, question: str, session_id: str):
        task = self.task_store.create(session_id, question)
        try:
            self.task_store.update(task.id, TaskStatus.RETRIEVING)
            self.task_store.update(task.id, TaskStatus.ANSWERING)
            attachment_context = self.session_store.attachment_context(session_id)
            response = self.orchestrator.answer(question, session_id=session_id, attachment_context=attachment_context)
            self.task_store.update(
                task.id,
                TaskStatus.COMPLETED,
                answer=response.answer,
                sources=[source.__dict__ for source in response.sources],
            )
            self.alert_center.resolve("LLM_UNAVAILABLE", source="chat")
            self.metrics["chat_count"] += 1
            self.audit("chat", session_id=session_id, task_id=task.id, status="ok")
            return task.id, response
        except Exception as exc:
            self.task_store.update(task.id, TaskStatus.FAILED, error=str(exc))
            self.metrics["chat_failed"] += 1
            if isinstance(exc, LLMError):
                self.emit_alert(
                    code="LLM_UNAVAILABLE",
                    severity="critical",
                    message="LLM 当前不可用，无法生成排障回答。",
                    source="chat",
                    error=str(exc),
                    session_id=session_id,
                    task_id=task.id,
                )
            self.audit("chat", session_id=session_id, task_id=task.id, status="failed", error=str(exc))
            raise

    def run_evaluation(self):
        return EvaluationRunner(self.config, self.retriever, self.llm).write_reports()

    def rate_limit_ok(self, key: str) -> bool:
        if not self.config.rate_limit.enabled:
            return True
        now = time.time()
        window = self.rate_counters[key]
        cutoff = now - 60
        while window and window[0] < cutoff:
            window.popleft()
        if len(window) >= self.config.rate_limit.requests_per_minute + self.config.rate_limit.burst:
            return False
        window.append(now)
        return True

    def make_csrf(self, username: str) -> str:
        import hashlib
        import hmac

        return hmac.new(self._csrf_secret.encode("utf-8"), username.encode("utf-8"), hashlib.sha256).hexdigest()

    def verify_csrf(self, username: str, token: str | None) -> bool:
        import hmac

        if not self.config.auth.csrf_enabled:
            return True
        return bool(token and hmac.compare_digest(self.make_csrf(username), token))

    def audit(self, action: str, **fields: Any) -> None:
        self.logger.write({"type": "audit", "action": action, "at": datetime.now(timezone.utc).isoformat(), **fields})
        self.metrics[f"audit_{action}"] += 1

    def emit_alert(
        self,
        code: str,
        severity: str,
        message: str,
        source: str,
        source_id: str | None = None,
        **metadata: Any,
    ) -> None:
        self.alert_center.emit(
            code=code,
            severity=severity,
            message=message,
            source=source,
            source_id=source_id,
            metadata=metadata or None,
        )
        self.metrics[f"alert_{code.lower()}"] += 1

    def on_job_update(self, job) -> None:
        if job.status == JobStatus.FAILED:
            self.emit_alert(
                code="JOB_FAILED",
                severity="warning",
                message=f"后台作业执行失败：{job.kind}",
                source="job",
                source_id=job.id,
                kind=job.kind,
                error=job.error,
            )
        elif job.status == JobStatus.COMPLETED:
            self.alert_center.resolve("JOB_FAILED", source="job", source_id=job.id, metadata={"kind": job.kind})


state: AppState | None = None
app = FastAPI(title="Ops Agent", version="0.6.0")
web_dir = Path(__file__).resolve().parents[1] / "web"
app.mount("/static", StaticFiles(directory=web_dir), name="static")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; connect-src 'self'"
    return response


def get_state() -> AppState:
    global state
    if state is None:
        state = AppState()
    return state


@app.on_event("startup")
def _startup() -> None:
    get_state()


def _client_key(request: Request, user: AuthSession | None = None) -> str:
    return f"user:{user.username}" if user else (request.client.host if request.client else "anonymous")


def _guard_rate_limit(request: Request, user: AuthSession | None = None) -> None:
    if not get_state().rate_limit_ok(_client_key(request, user)):
        raise HTTPException(status_code=429, detail={"code": "RATE_LIMITED", "message": "请求过于频繁", "hint": "请稍后重试。"})


def get_current_user(request: Request) -> AuthSession:
    current_state = get_state()
    token = request.cookies.get(COOKIE_NAME)
    auth = current_state.auth.verify(token)
    if auth is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_REQUIRED", "message": "请先登录", "hint": "登录后再重试。"},
        )
    return auth


def require_roles(*roles: str):
    def _dependency(user: AuthSession = Depends(get_current_user)) -> AuthSession:
        if user.role == "admin" or user.role in roles:
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "无权限访问", "hint": "请使用具备权限的账号。"},
        )

    return _dependency


def _require_csrf(request: Request, user: AuthSession) -> None:
    if not get_state().verify_csrf(user.username, request.headers.get("x-csrf-token")):
        raise HTTPException(status_code=403, detail={"code": "CSRF_REQUIRED", "message": "缺少 CSRF 校验", "hint": "请重新登录后重试。"})


def _safe_config_payload() -> dict:
    data = get_state().config.to_safe_dict()
    data["auth"]["enabled"] = get_state().config.auth.enabled
    return data


def _session_payload(session):
    payload = session.__dict__.copy()
    payload["feedback_status"] = session.feedback_status.value
    payload["attachments"] = [attachment.__dict__ for attachment in session.attachments]
    return payload


def _admin_case_payload(case):
    payload = case.__dict__.copy()
    payload["status"] = case.status.value
    return payload


def _user_payload(user) -> dict:
    payload = user.__dict__.copy()
    payload["password"] = "***" if payload.get("password") else None
    return payload


def _job_payload(job) -> dict:
    payload = job.__dict__.copy()
    payload["status"] = job.status.value
    return payload


def _alert_payload(alert) -> dict:
    return alert.__dict__.copy()


def _read_audit_logs(limit: int = 100) -> list[dict]:
    path = Path(get_state().config.logging.path)
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("type") == "audit":
            records.append(item)
    return list(reversed(records))[:limit]


def _list_drafts() -> list[dict]:
    draft_dir = Path(get_state().config.session.draft_dir)
    draft_dir.mkdir(parents=True, exist_ok=True)
    drafts = []
    for path in sorted(draft_dir.glob("*.md"), reverse=True):
        text = path.read_text(encoding="utf-8", errors="ignore")
        drafts.append(
            {
                "path": path.as_posix(),
                "status": _front_matter_value(text, "review_status") or "pending",
                "title": _first_heading(text),
                "modified_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            }
        )
    return drafts


def _front_matter_value(text: str, key: str) -> str | None:
    for line in text.splitlines()[:30]:
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    return None


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "未命名草稿"


def _set_review_status(path: str, status_value: str, reviewer: str, note: str | None = None) -> str:
    draft = Path(path)
    if not draft.exists():
        raise FileNotFoundError(path)
    text = draft.read_text(encoding="utf-8")
    lines = text.splitlines()
    replaced = False
    for idx, line in enumerate(lines):
        if line.startswith("review_status:"):
            lines[idx] = f"review_status: {status_value}"
            replaced = True
            break
    if not replaced and lines and lines[0] == "---":
        lines.insert(1, f"review_status: {status_value}")
    stamp = datetime.now(timezone.utc).isoformat()
    lines.append(f"\n<!-- review: {status_value}; reviewer={reviewer}; at={stamp}; note={note or ''} -->")
    draft.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return draft.as_posix()


def _alerts() -> list[dict]:
    current_state = get_state()
    alerts = [_alert_payload(item) for item in current_state.alert_center.list(limit=200)]
    if len(current_state.chunks) == 0:
        alerts.append({"severity": "critical", "code": "NO_KNOWLEDGE_CHUNKS", "message": "知识库索引为空。", "source": "system", "source_id": None, "status": "open"})
    pending = current_state.session_store.feedback_summary().get("pending_feedback", 0)
    if pending:
        alerts.append({"severity": "warning", "code": "PENDING_FEEDBACK", "message": f"存在 {pending} 个会话未反馈是否解决。", "source": "session", "source_id": None, "status": "open"})
    failed = sum(1 for task in current_state.task_store.list(limit=10000) if task.status == TaskStatus.FAILED)
    if failed:
        alerts.append({"severity": "warning", "code": "FAILED_TASKS", "message": f"存在 {failed} 个失败任务需要复盘。", "source": "task", "source_id": None, "status": "open"})
    backups = list_backups(current_state.config.backup.dir)
    if not backups:
        alerts.append({"severity": "warning", "code": "NO_BACKUP", "message": "当前未发现备份文件。", "source": "backup", "source_id": None, "status": "open"})
    else:
        modified_at = datetime.fromisoformat(backups[0]["modified_at"])
        age_hours = (datetime.now(timezone.utc) - modified_at).total_seconds() / 3600
        if age_hours > current_state.config.backup.warn_if_older_hours:
            alerts.append(
                {
                    "severity": "warning",
                    "code": "BACKUP_TOO_OLD",
                    "message": f"最近备份已超过 {current_state.config.backup.warn_if_older_hours} 小时。",
                    "source": "backup",
                    "source_id": backups[0]["path"],
                    "status": "open",
                }
            )
    return alerts


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/ready")
def ready():
    current_state = get_state()
    return {"ok": True, "llm": bool(current_state.llm), "chunks": len(current_state.chunks)}


@app.get("/")
def index():
    return FileResponse(web_dir / "index.html")


@app.get("/api/trial/entry")
def trial_entry(request: Request, user: AuthSession = Depends(require_roles("admin", "implementer", "reviewer", "auditor"))):
    _guard_rate_limit(request, user)
    return {
        "entry": {
            "requires_project_code_format": "拼音首字母大写缩写",
            "chat_placeholder": "先创建会话，再描述组件、环境、报错和已做过的检查。",
            "attachment_types": list(get_state().config.session.allowed_extensions),
            "feedback_options": ["resolved", "partial", "unresolved"],
            "admin_intervention_available": user.role in {"admin", "implementer", "reviewer"},
            "admin_views_alerts": user.role in {"admin", "reviewer", "auditor"},
        }
    }


@app.post("/api/auth/login")
def login(request: Request, payload: LoginRequest, response: Response):
    current_state = get_state()
    _guard_rate_limit(request)
    session = current_state.auth.authenticate(payload.username, payload.password)
    if session is None:
        current_state.audit("login_failed", username=payload.username)
        raise HTTPException(status_code=401, detail={"code": "AUTH_FAILED", "message": "用户名或密码错误", "hint": "请联系管理员确认账号。"})
    token = current_state.auth.issue_token(session)
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=os.getenv("OPS_AGENT_COOKIE_SECURE", "0") == "1",
        samesite="lax",
        max_age=current_state.config.auth.token_ttl_minutes * 60,
    )
    response.headers["X-CSRF-Token"] = current_state.make_csrf(session.username)
    current_state.audit("login", username=session.username, role=session.role)
    return {"ok": True, "user": asdict(session), "csrf_token": current_state.make_csrf(session.username)}


@app.post("/api/auth/logout")
def logout(request: Request, response: Response, user: AuthSession = Depends(get_current_user)):
    _guard_rate_limit(request, user)
    response.delete_cookie(COOKIE_NAME)
    get_state().audit("logout", username=user.username)
    return {"ok": True}


@app.get("/api/auth/me")
def me(request: Request, user: AuthSession = Depends(get_current_user)):
    _guard_rate_limit(request, user)
    return {"user": asdict(user), "csrf_token": get_state().make_csrf(user.username)}


@app.get("/api/config")
def config(request: Request, user: AuthSession = Depends(get_current_user)):
    _guard_rate_limit(request, user)
    return {"config": _safe_config_payload(), "chunks": len(get_state().chunks), "csrf_token": get_state().make_csrf(user.username)}


@app.post("/api/config")
def update_config(request: Request, payload: dict, user: AuthSession = Depends(require_roles("admin"))):
    current_state = get_state()
    _guard_rate_limit(request, user)
    _require_csrf(request, user)
    raw = current_state.config.to_persisted_dict()
    for section in ("llm", "embedding", "retrieval", "vector_store", "evaluation", "task", "session", "auth", "rate_limit", "backup", "logging"):
        if section in payload and isinstance(payload[section], dict):
            raw.setdefault(section, {}).update(payload[section])
    if "auth" in payload and isinstance(payload["auth"], dict) and payload["auth"].get("password"):
        raw["auth"]["password"] = hash_password(payload["auth"]["password"])
    for key in ("knowledge_base_path", "index_path", "log_path"):
        if key in payload:
            raw[key] = payload[key]
    Path("config").mkdir(parents=True, exist_ok=True)
    Path("config/app.yaml").write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")
    current_state.config = AppConfig.load()
    current_state.auth = AuthManager(current_state.config.auth)
    current_state.logger = JsonlLogger(current_state.config.logging.path, max_bytes=current_state.config.logging.max_bytes, backup_count=current_state.config.logging.backup_count)
    current_state.audit("config_updated", username=user.username)
    return {"ok": True, "message": "配置已保存，重启服务后会完全生效。"}


@app.post("/api/config/test-llm")
def test_llm_config(request: Request, payload: dict | None = None, user: AuthSession = Depends(require_roles("admin"))):
    _guard_rate_limit(request, user)
    _require_csrf(request, user)
    config_obj = AppConfig.load()
    if payload:
        raw = config_obj.to_persisted_dict()
        if "llm" in payload and isinstance(payload["llm"], dict):
            raw["llm"].update(payload["llm"])
        temp_path = Path("data/.config-test.yaml")
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")
        config_obj = AppConfig.load(temp_path)
        temp_path.unlink(missing_ok=True)
    try:
        llm = create_llm_client(config_obj.llm, require_real=True)
        require_llm_available(llm)
    except LLMError as exc:
        get_state().emit_alert("LLM_UNAVAILABLE", "critical", "LLM 连通性测试失败。", "llm_test", error=str(exc))
        raise HTTPException(status_code=503, detail=llm_unavailable_error().to_dict()) from exc
    get_state().alert_center.resolve("LLM_UNAVAILABLE", source="llm_test")
    get_state().audit("llm_test", username=user.username)
    return {"ok": True}


@app.get("/metrics")
def metrics(user: AuthSession = Depends(require_roles("admin", "auditor"))):
    return {"counters": dict(get_state().metrics), "alerts": _alerts()}


@app.get("/api/audit")
def audit_logs(request: Request, limit: int = 100, user: AuthSession = Depends(require_roles("admin", "auditor"))):
    _guard_rate_limit(request, user)
    return {"logs": _read_audit_logs(limit)}


@app.get("/api/alerts")
def alerts(request: Request, user: AuthSession = Depends(require_roles("admin", "reviewer", "auditor"))):
    _guard_rate_limit(request, user)
    return {"alerts": _alerts()}


@app.get("/api/users")
def list_users(request: Request, user: AuthSession = Depends(require_roles("admin"))):
    _guard_rate_limit(request, user)
    return {"users": [_user_payload(item) for item in get_state().auth.list_users()]}


@app.post("/api/users")
def create_user(request: Request, payload: UserUpsertRequest, user: AuthSession = Depends(require_roles("admin"))):
    current_state = get_state()
    _guard_rate_limit(request, user)
    _require_csrf(request, user)
    try:
        record = current_state.auth.upsert_user(
            payload.username,
            password=hash_password(payload.password) if payload.password else None,
            role=payload.role,
            enabled=payload.enabled,
            projects=payload.projects,
            components=payload.components,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    Path("config").mkdir(parents=True, exist_ok=True)
    Path("config/app.yaml").write_text(yaml.safe_dump(current_state.config.to_persisted_dict(), allow_unicode=True, sort_keys=False), encoding="utf-8")
    current_state.audit("user_create", username=user.username, target=record.username, role=record.role)
    return {"user": _user_payload(record)}


@app.patch("/api/users/{username}")
def update_user(request: Request, username: str, payload: UserPatchRequest, user: AuthSession = Depends(require_roles("admin"))):
    current_state = get_state()
    _guard_rate_limit(request, user)
    _require_csrf(request, user)
    try:
        record = current_state.auth.upsert_user(
            username,
            password=hash_password(payload.password) if payload.password else None,
            role=payload.role,
            enabled=payload.enabled,
            projects=payload.projects,
            components=payload.components,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    Path("config").mkdir(parents=True, exist_ok=True)
    Path("config/app.yaml").write_text(yaml.safe_dump(current_state.config.to_persisted_dict(), allow_unicode=True, sort_keys=False), encoding="utf-8")
    current_state.audit("user_update", username=user.username, target=record.username, role=record.role, enabled=record.enabled)
    return {"user": _user_payload(record)}


@app.post("/api/users/{username}/reset-password")
def reset_user_password(request: Request, username: str, payload: dict, user: AuthSession = Depends(require_roles("admin"))):
    current_state = get_state()
    _guard_rate_limit(request, user)
    _require_csrf(request, user)
    password = str(payload.get("password", "")).strip()
    if not password:
        raise HTTPException(status_code=400, detail="password is required")
    record = current_state.auth.reset_password(username, hash_password(password))
    Path("config").mkdir(parents=True, exist_ok=True)
    Path("config/app.yaml").write_text(yaml.safe_dump(current_state.config.to_persisted_dict(), allow_unicode=True, sort_keys=False), encoding="utf-8")
    current_state.audit("user_reset_password", username=user.username, target=record.username)
    return {"user": _user_payload(record)}


@app.get("/api/jobs")
def list_jobs(request: Request, limit: int = 50, user: AuthSession = Depends(require_roles("admin", "reviewer", "auditor"))):
    _guard_rate_limit(request, user)
    return {"jobs": [_job_payload(job) for job in get_state().job_manager.list(limit=limit)]}


@app.get("/api/jobs/{job_id}")
def get_job(request: Request, job_id: str, user: AuthSession = Depends(require_roles("admin", "reviewer", "auditor"))):
    _guard_rate_limit(request, user)
    job = get_state().job_manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return {"job": _job_payload(job)}


@app.post("/api/jobs/reindex", status_code=202)
def submit_reindex_job(request: Request, user: AuthSession = Depends(require_roles("admin", "reviewer"))):
    _guard_rate_limit(request, user)
    _require_csrf(request, user)
    job = get_state().job_manager.submit("reindex", lambda: {"chunks": get_state().rebuild_index()})
    get_state().audit("job_submit", username=user.username, kind="reindex", job_id=job.id)
    return {"job": _job_payload(job)}


@app.post("/api/jobs/governance", status_code=202)
def submit_governance_job(request: Request, user: AuthSession = Depends(require_roles("admin", "reviewer", "auditor"))):
    _guard_rate_limit(request, user)
    _require_csrf(request, user)
    job = get_state().job_manager.submit(
        "governance",
        lambda: KnowledgeGovernance(get_state().config.knowledge_base_path).write_report("data/governance-report.json").to_dict(),
    )
    get_state().audit("job_submit", username=user.username, kind="governance", job_id=job.id)
    return {"job": _job_payload(job)}


@app.post("/api/jobs/evaluation", status_code=202)
def submit_evaluation_job(request: Request, user: AuthSession = Depends(require_roles("admin", "reviewer"))):
    _guard_rate_limit(request, user)
    _require_csrf(request, user)
    job = get_state().job_manager.submit("evaluation", lambda: get_state().run_evaluation().to_dict())
    get_state().audit("job_submit", username=user.username, kind="evaluation", job_id=job.id)
    return {"job": _job_payload(job)}


@app.get("/api/backup")
def backups(request: Request, user: AuthSession = Depends(require_roles("admin", "auditor"))):
    _guard_rate_limit(request, user)
    return {"backups": list_backups(get_state().config.backup.dir)}


@app.post("/api/backup/create")
def create_backup_endpoint(request: Request, payload: BackupRequest | None = None, user: AuthSession = Depends(require_roles("admin"))):
    _guard_rate_limit(request, user)
    _require_csrf(request, user)
    current_state = get_state()
    path = create_backup(Path.cwd(), payload.backup_dir if payload and payload.backup_dir else current_state.config.backup.dir)
    removed = prune_backups(current_state.config.backup.dir, current_state.config.backup.retention_count)
    current_state.alert_center.resolve("BACKUP_VERIFY_FAILED", source="backup")
    current_state.audit("backup_create", username=user.username, path=path)
    return {"path": path, "removed": removed}


@app.post("/api/backup/verify")
def verify_backup_endpoint(request: Request, payload: RestoreRequest, user: AuthSession = Depends(require_roles("admin", "auditor"))):
    _guard_rate_limit(request, user)
    _require_csrf(request, user)
    try:
        result = verify_backup(payload.archive_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        get_state().emit_alert("BACKUP_VERIFY_FAILED", "warning", "备份校验失败。", "backup", archive=payload.archive_path, error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    get_state().alert_center.resolve("BACKUP_VERIFY_FAILED", source="backup")
    return result


@app.post("/api/backup/restore")
def restore_backup_endpoint(request: Request, payload: RestoreRequest, user: AuthSession = Depends(require_roles("admin"))):
    _guard_rate_limit(request, user)
    _require_csrf(request, user)
    try:
        extracted = restore_backup(payload.archive_path, Path.cwd())
    except (FileNotFoundError, ValueError, OSError) as exc:
        get_state().emit_alert("BACKUP_RESTORE_FAILED", "warning", "备份恢复失败。", "backup", archive=payload.archive_path, error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    get_state().alert_center.resolve("BACKUP_RESTORE_FAILED", source="backup")
    get_state().audit("backup_restore", username=user.username, archive=payload.archive_path)
    return {"ok": True, "restored": extracted}


@app.get("/api/storage/check")
def storage_check(request: Request, user: AuthSession = Depends(require_roles("admin", "auditor"))):
    _guard_rate_limit(request, user)
    return {"vector_store": sqlite_integrity_check(get_state().config.vector_store.path)}


@app.post("/api/reindex")
def reindex(request: Request, user: AuthSession = Depends(require_roles("admin", "reviewer"))):
    _guard_rate_limit(request, user)
    _require_csrf(request, user)
    count = get_state().rebuild_index()
    get_state().audit("reindex", username=user.username, chunks=count)
    return {"ok": True, "chunks": count}


@app.post("/api/governance/run")
def run_governance(request: Request, user: AuthSession = Depends(require_roles("admin", "reviewer", "auditor"))):
    _guard_rate_limit(request, user)
    _require_csrf(request, user)
    governance = KnowledgeGovernance(get_state().config.knowledge_base_path)
    report = governance.write_report("data/governance-report.json")
    Path("data/governance-report.md").write_text(report.to_markdown(), encoding="utf-8")
    get_state().audit("governance_run", username=user.username, score=report.score)
    return report.to_dict()


@app.post("/api/evaluation/run")
def run_evaluation(request: Request, user: AuthSession = Depends(require_roles("admin", "reviewer"))):
    _guard_rate_limit(request, user)
    _require_csrf(request, user)
    report = get_state().run_evaluation()
    get_state().audit("evaluation_run", username=user.username, cases=report.case_count)
    return report.to_dict()


@app.get("/api/evaluation/history")
def evaluation_history(request: Request, user: AuthSession = Depends(require_roles("admin", "reviewer", "auditor"))):
    _guard_rate_limit(request, user)
    return {"history": list_evaluation_history(get_state().config.evaluation.history_dir)}


@app.post("/api/sessions")
def create_session(request: Request, payload: CreateSessionRequest, user: AuthSession = Depends(require_roles("admin", "implementer", "reviewer"))):
    current_state = get_state()
    _guard_rate_limit(request, user)
    project = payload.project_code.strip().upper()
    component = payload.component.strip() if payload.component else None
    allowed_projects = user.projects or current_state.config.auth.allowed_projects
    allowed_components = user.components or current_state.config.auth.allowed_components
    if allowed_projects and project not in allowed_projects:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "项目不在允许范围内", "hint": "请联系管理员放行该项目。"})
    if allowed_components and component and component not in allowed_components:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "组件不在允许范围内", "hint": "请联系管理员放行该组件。"})
    try:
        session = current_state.session_store.create_session(project, payload.implementer, component)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    current_state.audit("session_create", username=user.username, session_id=session.id, project=session.project_code)
    return {"session": _session_payload(session)}


@app.get("/api/sessions")
def list_sessions(request: Request, limit: int = 100, pending_feedback: bool = False, user: AuthSession = Depends(require_roles("admin", "reviewer", "implementer", "auditor"))):
    _guard_rate_limit(request, user)
    sessions = get_state().session_store.pending_feedback_sessions() if pending_feedback else get_state().session_store.list_sessions(limit=limit)
    return {"sessions": [_session_payload(session) for session in sessions[:limit]]}


@app.get("/api/sessions/analytics")
def session_analytics(request: Request, user: AuthSession = Depends(require_roles("admin", "reviewer", "implementer", "auditor"))):
    _guard_rate_limit(request, user)
    return get_state().session_store.feedback_summary()


@app.get("/api/review/analytics")
def review_analytics(request: Request, user: AuthSession = Depends(require_roles("admin", "reviewer", "auditor"))):
    _guard_rate_limit(request, user)
    tasks = []
    for task in get_state().task_store.list(limit=10000):
        payload = task.__dict__.copy()
        payload["status"] = task.status.value
        tasks.append(payload)
    return get_state().session_store.review_analytics(tasks)


@app.get("/api/sessions/{session_id}")
def get_session(request: Request, session_id: str, user: AuthSession = Depends(get_current_user)):
    _guard_rate_limit(request, user)
    session = get_state().session_store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"session": _session_payload(session)}


@app.post("/api/sessions/{session_id}/feedback")
def record_feedback(request: Request, session_id: str, payload: FeedbackRequest, user: AuthSession = Depends(require_roles("admin", "implementer", "reviewer"))):
    _guard_rate_limit(request, user)
    try:
        session = get_state().session_store.record_feedback(session_id, FeedbackStatus(payload.status), payload.note)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    get_state().audit("feedback", username=user.username, session_id=session.id, status=payload.status)
    return {"session": _session_payload(session)}


@app.post("/api/sessions/{session_id}/attachments")
def add_attachment(request: Request, session_id: str, payload: AttachmentRequest, user: AuthSession = Depends(require_roles("admin", "implementer", "reviewer"))):
    _guard_rate_limit(request, user)
    try:
        attachment = get_state().session_store.add_attachment(session_id, payload.filename, payload.content_type, payload.content_base64)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    get_state().audit("attachment_upload", username=user.username, session_id=session_id, filename=payload.filename)
    return {"attachment": attachment.__dict__}


@app.post("/api/sessions/{session_id}/admin-request")
def request_admin(request: Request, session_id: str, payload: AdminRequest, user: AuthSession = Depends(require_roles("admin", "implementer", "reviewer"))):
    _guard_rate_limit(request, user)
    try:
        case = get_state().session_store.request_admin(session_id, payload.reason)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    get_state().audit("admin_request", username=user.username, case_id=case.id)
    return {"case": _admin_case_payload(case)}


@app.post("/api/sessions/{session_id}/candidate-draft")
def create_candidate_draft(request: Request, session_id: str, payload: CandidateDraftRequest, user: AuthSession = Depends(require_roles("admin", "implementer", "reviewer"))):
    _guard_rate_limit(request, user)
    try:
        draft_path = get_state().session_store.generate_candidate_from_session(session_id, payload.question, payload.answer)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    get_state().audit("candidate_draft", username=user.username, session_id=session_id, draft_path=draft_path)
    return {"draft_path": draft_path}


@app.get("/api/admin/cases")
def list_admin_cases(request: Request, limit: int = 100, user: AuthSession = Depends(require_roles("admin", "reviewer", "auditor"))):
    _guard_rate_limit(request, user)
    return {"cases": [_admin_case_payload(case) for case in get_state().session_store.list_admin_cases(limit=limit)]}


@app.post("/api/admin/cases/{case_id}/resolve")
def resolve_admin_case(request: Request, case_id: str, payload: ResolveAdminRequest, user: AuthSession = Depends(require_roles("admin", "reviewer"))):
    _guard_rate_limit(request, user)
    _require_csrf(request, user)
    try:
        case = get_state().session_store.resolve_admin_case(case_id, payload.root_cause, payload.solution, create_draft=payload.create_draft)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    get_state().audit("admin_case_resolve", username=user.username, case_id=case_id, draft_path=case.draft_path)
    return {"case": _admin_case_payload(case)}


@app.get("/api/knowledge/drafts")
def list_knowledge_drafts(request: Request, user: AuthSession = Depends(require_roles("admin", "reviewer", "auditor"))):
    _guard_rate_limit(request, user)
    return {"drafts": _list_drafts()}


@app.post("/api/knowledge/drafts/approve")
def approve_draft(request: Request, payload: ReviewDraftRequest, user: AuthSession = Depends(require_roles("admin", "reviewer"))):
    _guard_rate_limit(request, user)
    _require_csrf(request, user)
    try:
        report = KnowledgeGovernance(get_state().config.knowledge_base_path).inspect_file(payload.draft_path)
        if report.error_count:
            raise HTTPException(status_code=400, detail={"message": "草稿存在治理错误，不能批准。", "issues": report.to_dict()["issues"]})
        path = _set_review_status(payload.draft_path, "approved", user.username, payload.note)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    get_state().audit("draft_approve", username=user.username, path=path)
    return {"path": path, "governance": report.to_dict()}


@app.post("/api/knowledge/drafts/reject")
def reject_draft(request: Request, payload: ReviewDraftRequest, user: AuthSession = Depends(require_roles("admin", "reviewer"))):
    _guard_rate_limit(request, user)
    _require_csrf(request, user)
    try:
        path = _set_review_status(payload.draft_path, "rejected", user.username, payload.note)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    get_state().audit("draft_reject", username=user.username, path=path)
    return {"path": path}


@app.post("/api/knowledge/publish")
def publish_knowledge(request: Request, payload: PublishDraftRequest, user: AuthSession = Depends(require_roles("admin", "reviewer"))):
    _guard_rate_limit(request, user)
    _require_csrf(request, user)
    draft_path = Path(payload.draft_path)
    draft_text = draft_path.read_text(encoding="utf-8", errors="ignore") if draft_path.exists() else ""
    if _front_matter_value(draft_text, "review_status") != "approved":
        raise HTTPException(status_code=400, detail="草稿未审核通过，不能发布。")
    governance = KnowledgeGovernance(get_state().config.knowledge_base_path).inspect_file(payload.draft_path)
    if governance.score < get_state().config.evaluation.minimum_publish_score:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "草稿治理评分未达到发布阈值。",
                "score": governance.score,
                "threshold": get_state().config.evaluation.minimum_publish_score,
                "issues": governance.to_dict()["issues"],
            },
        )
    try:
        path = get_state().session_store.publish_draft(payload.draft_path, payload.target_dir)
        count = get_state().rebuild_index()
        eval_report = get_state().run_evaluation()
    except (FileNotFoundError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    get_state().audit("publish_knowledge", username=user.username, path=path, chunks=count)
    return {"path": path, "chunks": count, "evaluation": eval_report.to_dict()}


@app.get("/api/tasks")
def list_tasks(request: Request, limit: int = 50, user: AuthSession = Depends(get_current_user)):
    _guard_rate_limit(request, user)
    tasks = []
    for task in get_state().task_store.list(limit=limit):
        payload = task.__dict__.copy()
        payload["status"] = task.status.value
        tasks.append(payload)
    return {"tasks": tasks}


@app.post("/api/chat")
def chat(request: Request, payload: ChatRequest, user: AuthSession = Depends(require_roles("admin", "implementer", "reviewer"))):
    _guard_rate_limit(request, user)
    current_state = get_state()
    session = current_state.session_store.get_session(payload.session_id)
    if session is None:
        raise HTTPException(status_code=400, detail="请先创建会话并填写项目缩写和实施姓名。")
    try:
        task_id, response = current_state.answer_with_task(payload.message, session_id=payload.session_id)
    except LLMError as exc:
        current_state.emit_alert(
            code="LLM_UNAVAILABLE",
            severity="critical",
            message="LLM 当前不可用，无法生成排障回答。",
            source="chat",
            error=str(exc),
            session_id=payload.session_id,
        )
        raise HTTPException(status_code=503, detail=llm_unavailable_error().to_dict()) from exc
    return {
        "task_id": task_id,
        "session_id": response.session_id,
        "answer": response.answer,
        "sources": [source.__dict__ for source in response.sources],
        "used_fallback": response.used_fallback,
        "csrf_token": current_state.make_csrf(user.username),
    }
