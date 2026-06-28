from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass, field
from typing import Any

from .config import AuthConfig, UserConfig


COOKIE_NAME = "ops_agent_token"
VALID_ROLES = {"admin", "reviewer", "implementer", "auditor"}


def hash_password(password: str, salt: bytes | None = None, iterations: int = 120_000) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return "pbkdf2$%d$%s$%s" % (
        iterations,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, stored: str) -> bool:
    if stored.startswith("pbkdf2$"):
        _, iterations, salt_b64, digest_b64 = stored.split("$", 3)
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(candidate, expected)
    return hmac.compare_digest(password, stored)


def create_token(data: dict[str, Any], secret_key: str) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    signature = hmac.new(secret_key.encode("utf-8"), payload, hashlib.sha256).digest()
    return f"{encoded}.{base64.urlsafe_b64encode(signature).decode('ascii').rstrip('=')}"


def verify_token(token: str, secret_key: str) -> dict[str, Any] | None:
    try:
        encoded, signature = token.split(".", 1)
        payload = base64.urlsafe_b64decode(_pad(encoded))
        expected = hmac.new(secret_key.encode("utf-8"), payload, hashlib.sha256).digest()
        expected_sig = base64.urlsafe_b64encode(expected).decode("ascii").rstrip("=")
        if not hmac.compare_digest(signature, expected_sig):
            return None
        data = json.loads(payload.decode("utf-8"))
        if data.get("exp") and int(data["exp"]) < int(time.time()):
            return None
        return data
    except Exception:
        return None


def _pad(value: str) -> str:
    return value + "=" * (-len(value) % 4)


@dataclass
class AuthSession:
    username: str
    role: str
    projects: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)


class AuthManager:
    def __init__(self, config: AuthConfig):
        self.config = config
        self.secret_key = config.secret_key or "ops-agent-dev-secret"
        self._users = self._build_users(config)

    @property
    def enabled(self) -> bool:
        return bool(self.config.enabled)

    def authenticate(self, username: str, password: str) -> AuthSession | None:
        if not self.enabled:
            return AuthSession(username="anonymous", role="admin")
        user = self._users.get(username)
        if user is None or not user.enabled or not user.password or not verify_password(password, user.password):
            return None
        return AuthSession(username=user.username, role=_normalize_role(user.role), projects=user.projects, components=user.components)

    def issue_token(self, session: AuthSession) -> str:
        now = int(time.time())
        payload = {
            "sub": session.username,
            "role": session.role,
            "projects": session.projects,
            "components": session.components,
            "iat": now,
            "exp": now + self.config.token_ttl_minutes * 60,
        }
        return create_token(payload, self.secret_key)

    def verify(self, token: str | None) -> AuthSession | None:
        if not self.enabled:
            return AuthSession(username="anonymous", role="admin")
        if not token:
            return None
        data = verify_token(token, self.secret_key)
        if not data:
            return None
        return AuthSession(
            username=str(data.get("sub", "")),
            role=_normalize_role(str(data.get("role", "implementer"))),
            projects=list(data.get("projects", [])),
            components=list(data.get("components", [])),
        )

    def list_users(self) -> list[UserConfig]:
        return sorted(self._users.values(), key=lambda user: user.username)

    def upsert_user(
        self,
        username: str,
        password: str | None = None,
        role: str | None = None,
        enabled: bool | None = None,
        projects: list[str] | None = None,
        components: list[str] | None = None,
    ) -> UserConfig:
        normalized = username.strip()
        if not normalized:
            raise ValueError("username cannot be empty")
        existing = self._users.get(normalized, UserConfig(username=normalized, role="implementer"))
        if password:
            existing.password = password
        if role:
            existing.role = _normalize_role(role)
        if enabled is not None:
            existing.enabled = bool(enabled)
        if projects is not None:
            existing.projects = projects
        if components is not None:
            existing.components = components
        self._users[normalized] = existing
        self._sync_config_users()
        return existing

    def reset_password(self, username: str, password: str) -> UserConfig:
        return self.upsert_user(username, password=password)

    def set_enabled(self, username: str, enabled: bool) -> UserConfig:
        return self.upsert_user(username, enabled=enabled)

    def _sync_config_users(self) -> None:
        self.config.users = self.list_users()
        if self.config.username in self._users:
            self.config.password = self._users[self.config.username].password

    @staticmethod
    def _build_users(config: AuthConfig) -> dict[str, UserConfig]:
        users = {user.username: user for user in config.users if user.username}
        if config.username and config.password and config.username not in users:
            users[config.username] = UserConfig(username=config.username, password=config.password, role="admin")
        return users


def _normalize_role(role: str) -> str:
    return role if role in VALID_ROLES else "implementer"
