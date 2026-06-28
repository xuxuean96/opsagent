from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient

from ops_agent import app as app_module
from ops_agent.auth import hash_password
from ops_agent.app import app
from ops_agent.llm import MockLLMClient


def write_production_config(root: Path) -> None:
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "knowledge-base" / "07-故障卡片").mkdir(parents=True, exist_ok=True)
    (root / "knowledge-base" / "13-待审核").mkdir(parents=True, exist_ok=True)
    (root / "knowledge-base" / "11-测试集").mkdir(parents=True, exist_ok=True)
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "knowledge-base" / "07-故障卡片" / "good.md").write_text(
        """---
type: runbook
component: DDB
scenario: 启动失败
priority: P2
tags: [DDB, 启动失败]
status: active
---

# DDB 启动失败

检查 Java 环境、运行时依赖、授权服务和日志路径。
""",
        encoding="utf-8",
    )
    (root / "knowledge-base" / "13-待审核" / "draft.md").write_text(
        """---
type: runbook
priority: P2
status: draft
review_status: approved
---

这里是一个缺少组件、场景、标签和标题的草稿。
""",
        encoding="utf-8",
    )
    (root / "config" / "app.yaml").write_text(
        "\n".join(
            [
                "knowledge_base_path: knowledge-base",
                "index_path: data/index.json",
                "log_path: data/chat_logs.jsonl",
                "llm:",
                "  provider: mock",
                "  model: mock",
                "embedding:",
                "  provider: local",
                "vector_store:",
                "  provider: sqlite",
                "  path: data/vector_store.sqlite3",
                "retrieval:",
                "  top_k: 2",
                "  min_score: 0.0",
                "evaluation:",
                "  testset_path: knowledge-base/11-测试集",
                "  history_dir: data/evaluations",
                "  minimum_publish_score: 95",
                "session:",
                "  store_path: data/sessions.jsonl",
                "  upload_dir: data/uploads",
                "  draft_dir: knowledge-base/13-待审核",
                "auth:",
                "  enabled: true",
                "  username: admin",
                f"  password: {hash_password('admin')}",
                "  secret_key: test-secret",
                "  users:",
                "    - username: reviewer1",
                f"      password: {hash_password('reviewer1')}",
                "      role: reviewer",
                "      enabled: true",
                "backup:",
                "  dir: data/backups",
                "logging:",
                "  path: data/chat_logs.jsonl",
                "  max_bytes: 1048576",
                "  backup_count: 2",
                "rate_limit:",
                "  enabled: false",
            ]
        ),
        encoding="utf-8",
    )


def make_client(tmp_path: Path, monkeypatch) -> TestClient:
    monkeypatch.chdir(tmp_path)
    write_production_config(tmp_path)
    app_module.state = None
    monkeypatch.setattr(app_module, "create_llm_client", lambda config, require_real=False: MockLLMClient())
    monkeypatch.setattr(app_module, "require_llm_available", lambda client: None)
    return TestClient(app, raise_server_exceptions=False)


def login(client: TestClient, username: str = "admin", password: str = "admin") -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["csrf_token"]


def test_admin_can_manage_users_and_disable_login(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)
    with client:
        csrf = login(client)
        create = client.post(
            "/api/users",
            json={"username": "ops1", "password": "ops1", "role": "reviewer", "enabled": True},
            headers={"x-csrf-token": csrf},
        )
        assert create.status_code == 200
        assert any(user["username"] == "ops1" for user in client.get("/api/users").json()["users"])

        assert client.post("/api/auth/logout").status_code == 200
        assert client.post("/api/auth/login", json={"username": "ops1", "password": "ops1"}).status_code == 200

        csrf = login(client)
        disable = client.patch("/api/users/ops1", json={"enabled": False}, headers={"x-csrf-token": csrf})
        assert disable.status_code == 200

        client.post("/api/auth/logout")
        login_disabled = client.post("/api/auth/login", json={"username": "ops1", "password": "ops1"})
        assert login_disabled.status_code == 401


def test_publish_blocks_when_governance_score_is_below_threshold(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)
    with client:
        csrf = login(client)
        blocked = client.post(
            "/api/knowledge/publish",
            json={"draft_path": "knowledge-base/13-待审核/draft.md", "target_dir": "knowledge-base/07-故障卡片"},
            headers={"x-csrf-token": csrf},
        )
        assert blocked.status_code == 400
        detail = blocked.json()["detail"]
        assert detail["message"] == "草稿治理评分未达到发布阈值。"
        assert detail["threshold"] == 95
        assert detail["score"] < 95


def test_background_job_lifecycle_records_completion(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)
    with client:
        csrf = login(client)
        response = client.post("/api/jobs/reindex", headers={"x-csrf-token": csrf})
        assert response.status_code == 202
        job_id = response.json()["job"]["id"]

        for _ in range(30):
            job = client.get(f"/api/jobs/{job_id}").json()["job"]
            if job["status"] == "completed":
                break
            time.sleep(0.1)

        assert job["status"] == "completed"
        assert client.get("/api/jobs").json()["jobs"]
