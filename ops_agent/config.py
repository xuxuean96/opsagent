from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def env_value(value: str | None) -> str | None:
    if not value:
        return value
    if value.startswith("${") and value.endswith("}"):
        return os.getenv(value[2:-1])
    return value


@dataclass
class LLMConfig:
    provider: str = "openai-compatible"
    base_url: str = "https://api.openai.com/v1"
    api_key: str | None = None
    model: str = "gpt-4.1-mini"
    temperature: float = 0.2
    timeout_seconds: int = 60
    retries: int = 2
    retry_backoff_seconds: float = 0.8


@dataclass
class EmbeddingConfig:
    provider: str = "local"
    base_url: str = "https://api.openai.com/v1"
    api_key: str | None = None
    model: str = "text-embedding-3-small"


@dataclass
class RetrievalConfig:
    top_k: int = 6
    min_score: float = 0.05
    chunk_size: int = 1200
    chunk_overlap: int = 180


@dataclass
class VectorStoreConfig:
    provider: str = "sqlite"
    path: str = "data/vector_store.sqlite3"
    collection: str = "ops_knowledge"


@dataclass
class EvaluationConfig:
    testset_path: str = "knowledge-base/11-测试集"
    report_json_path: str = "data/eval-report.json"
    report_md_path: str = "data/eval-report.md"
    history_dir: str = "data/evaluations"
    minimum_source_hit_rate: float = 0.6
    minimum_keyword_hit_rate: float = 0.6
    minimum_publish_score: int = 80


@dataclass
class TaskConfig:
    store_path: str = "data/tasks.jsonl"
    job_store_path: str = "data/jobs.jsonl"


@dataclass
class SessionConfig:
    store_path: str = "data/sessions.jsonl"
    upload_dir: str = "data/uploads"
    draft_dir: str = "knowledge-base/13-待审核"
    max_upload_bytes: int = 5 * 1024 * 1024
    allowed_content_types: list[str] = field(
        default_factory=lambda: [
            "text/plain",
            "application/json",
            "application/xml",
            "text/xml",
            "image/png",
            "image/jpeg",
            "image/bmp",
        ]
    )
    allowed_extensions: list[str] = field(
        default_factory=lambda: [".txt", ".log", ".xml", ".json", ".ini", ".conf", ".png", ".jpg", ".jpeg", ".bmp"]
    )


@dataclass
class UserConfig:
    username: str
    password: str | None = None
    role: str = "implementer"
    enabled: bool = True
    projects: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)


@dataclass
class AuthConfig:
    enabled: bool = True
    username: str = "admin"
    password: str | None = None
    secret_key: str | None = None
    token_ttl_minutes: int = 720
    allowed_projects: list[str] = field(default_factory=list)
    allowed_components: list[str] = field(default_factory=list)
    csrf_enabled: bool = True
    trusted_origins: list[str] = field(default_factory=list)
    users: list[UserConfig] = field(default_factory=list)


@dataclass
class RateLimitConfig:
    enabled: bool = True
    requests_per_minute: int = 120
    burst: int = 30


@dataclass
class BackupConfig:
    dir: str = "data/backups"
    retention_count: int = 10
    warn_if_older_hours: int = 24


@dataclass
class LoggingConfig:
    path: str = "data/chat_logs.jsonl"
    max_bytes: int = 5 * 1024 * 1024
    backup_count: int = 5


@dataclass
class AppConfig:
    knowledge_base_path: str = "knowledge-base"
    index_path: str = "data/index.json"
    log_path: str = "data/chat_logs.jsonl"
    llm: LLMConfig = field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    task: TaskConfig = field(default_factory=TaskConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    backup: BackupConfig = field(default_factory=BackupConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def load(cls, path: str | Path = "config/app.yaml") -> "AppConfig":
        config_path = Path(path)
        if not config_path.exists():
            return cls()
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        return cls(
            knowledge_base_path=raw.get("knowledge_base_path", "knowledge-base"),
            index_path=raw.get("index_path", "data/index.json"),
            log_path=raw.get("log_path", "data/chat_logs.jsonl"),
            llm=_load_dataclass(LLMConfig, raw.get("llm", {}), env_keys={"api_key"}),
            embedding=_load_dataclass(EmbeddingConfig, raw.get("embedding", {}), env_keys={"api_key"}),
            retrieval=_load_dataclass(RetrievalConfig, raw.get("retrieval", {})),
            vector_store=_load_dataclass(VectorStoreConfig, raw.get("vector_store", {})),
            evaluation=_load_dataclass(EvaluationConfig, raw.get("evaluation", {})),
            task=_load_dataclass(TaskConfig, raw.get("task", {})),
            session=_load_dataclass(SessionConfig, raw.get("session", {})),
            auth=_load_auth(raw.get("auth", {})),
            rate_limit=_load_dataclass(RateLimitConfig, raw.get("rate_limit", {})),
            backup=_load_dataclass(BackupConfig, raw.get("backup", {})),
            logging=_load_dataclass(LoggingConfig, raw.get("logging", {"path": raw.get("log_path", "data/chat_logs.jsonl")})),
        )

    def save(self, path: str | Path = "config/app.yaml") -> None:
        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(yaml.safe_dump(self.to_persisted_dict(), allow_unicode=True, sort_keys=False), encoding="utf-8")

    def to_persisted_dict(self) -> dict[str, Any]:
        return {
            "knowledge_base_path": self.knowledge_base_path,
            "index_path": self.index_path,
            "log_path": self.log_path,
            "llm": self.llm.__dict__.copy(),
            "embedding": self.embedding.__dict__.copy(),
            "retrieval": self.retrieval.__dict__.copy(),
            "vector_store": self.vector_store.__dict__.copy(),
            "evaluation": self.evaluation.__dict__.copy(),
            "task": self.task.__dict__.copy(),
            "session": self.session.__dict__.copy(),
            "auth": {**self.auth.__dict__, "users": [user.__dict__.copy() for user in self.auth.users]},
            "rate_limit": self.rate_limit.__dict__.copy(),
            "backup": self.backup.__dict__.copy(),
            "logging": self.logging.__dict__.copy(),
        }

    def to_safe_dict(self) -> dict[str, Any]:
        data = self.to_persisted_dict()
        data["llm"]["api_key"] = "***" if self.llm.api_key else None
        data["embedding"]["api_key"] = "***" if self.embedding.api_key else None
        data["auth"]["password"] = "***" if self.auth.password else None
        data["auth"]["secret_key"] = "***" if self.auth.secret_key else None
        for user in data["auth"].get("users", []):
            user["password"] = "***" if user.get("password") else None
        return data


def _load_dataclass(cls, raw: dict[str, Any], env_keys: set[str] | None = None):
    env_keys = env_keys or set()
    values: dict[str, Any] = {}
    for field_obj in cls.__dataclass_fields__.values():  # type: ignore[attr-defined]
        if field_obj.name not in raw:
            continue
        value = raw[field_obj.name]
        if field_obj.name in env_keys:
            value = env_value(value)
        values[field_obj.name] = value
    return cls(**values)


def _load_auth(raw: dict[str, Any]) -> AuthConfig:
    users = []
    for item in raw.get("users", []) or []:
        users.append(
            UserConfig(
                username=str(item.get("username", "")).strip(),
                password=env_value(item.get("password")),
                role=str(item.get("role", "implementer")).strip() or "implementer",
                enabled=bool(item.get("enabled", True)),
                projects=list(item.get("projects", [])),
                components=list(item.get("components", [])),
            )
        )
    return AuthConfig(
        enabled=bool(raw.get("enabled", True)),
        username=raw.get("username", "admin"),
        password=env_value(raw.get("password")),
        secret_key=env_value(raw.get("secret_key")),
        token_ttl_minutes=int(raw.get("token_ttl_minutes", 720)),
        allowed_projects=list(raw.get("allowed_projects", [])),
        allowed_components=list(raw.get("allowed_components", [])),
        csrf_enabled=bool(raw.get("csrf_enabled", True)),
        trusted_origins=list(raw.get("trusted_origins", [])),
        users=users,
    )
