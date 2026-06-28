import base64
from pathlib import Path

from fastapi.testclient import TestClient

from ops_agent import app as app_module
from ops_agent.auth import hash_password
from ops_agent.app import app
from ops_agent.llm import MockLLMClient


def _write_config(root: Path) -> None:
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "knowledge-base" / "07-故障卡片").mkdir(parents=True, exist_ok=True)
    (root / "knowledge-base" / "11-测试集").mkdir(parents=True, exist_ok=True)
    (root / "knowledge-base" / "13-待审核").mkdir(parents=True, exist_ok=True)
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "knowledge-base" / "07-故障卡片" / "card.md").write_text(
        """---
type: runbook
component: DDB
scenario: 启动失败
priority: P2
tags: [DDB, 启动失败]
status: active
---

# DDB 启动失败

检查 Java 环境、运行时依赖和授权服务。
""",
        encoding="utf-8",
    )
    (root / "knowledge-base" / "11-测试集" / "cases.md").write_text(
        "- question: DDB 启动失败怎么办\n- expected_sources: [card.md]\n- expected_keywords: [Java]\n",
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
                "session:",
                "  store_path: data/sessions.jsonl",
                "  upload_dir: data/uploads",
                "  draft_dir: knowledge-base/13-待审核",
                "  max_upload_bytes: 20",
                "auth:",
                "  enabled: true",
                "  username: admin",
                f"  password: {hash_password('admin')}",
                "  secret_key: test-secret",
                "  users:",
                "    - username: auditor",
                f"      password: {hash_password('auditor')}",
                "      role: auditor",
                "backup:",
                "  dir: data/backups",
                "  retention_count: 3",
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


def _client(tmp_path: Path, monkeypatch) -> TestClient:
    monkeypatch.chdir(tmp_path)
    _write_config(tmp_path)
    app_module.state = None
    monkeypatch.setattr(app_module, "create_llm_client", lambda config, require_real=False: MockLLMClient())
    monkeypatch.setattr(app_module, "require_llm_available", lambda client: None)
    return TestClient(app, raise_server_exceptions=False)


def _login(client: TestClient, username: str = "admin", password: str = "admin") -> str:
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return login.json()["csrf_token"]


def test_login_session_and_backup_flow(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    with client:
        csrf = _login(client)
        config = client.get("/api/config")
        assert config.status_code == 200

        backup = client.post("/api/backup/create", json={}, headers={"x-csrf-token": csrf})
        assert backup.status_code == 200
        assert backup.json()["path"].endswith(".zip")

        verify = client.post("/api/backup/verify", json={"archive_path": backup.json()["path"]}, headers={"x-csrf-token": csrf})
        assert verify.status_code == 200
        assert verify.json()["ok"] is True


def test_project_access_control_rejects_blocked_project(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    with client:
        csrf = _login(client)
        payload = client.post(
            "/api/config",
            json={"auth": {"allowed_projects": ["ZJDL"]}},
            headers={"x-csrf-token": csrf},
        )
        assert payload.status_code == 200
        denied = client.post("/api/sessions", json={"project_code": "ABCD", "implementer": "张三"})
        assert denied.status_code == 403


def test_admin_mutation_requires_csrf(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    with client:
        _login(client)
        response = client.post("/api/reindex")
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "CSRF_REQUIRED"


def test_auditor_role_is_read_only(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    with client:
        _login(client, "auditor", "auditor")
        assert client.get("/api/audit").status_code == 200
        denied = client.post("/api/reindex", headers={"x-csrf-token": "bad"})
        assert denied.status_code == 403


def test_upload_rejects_oversized_attachment(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    with client:
        _login(client)
        session = client.post("/api/sessions", json={"project_code": "ZJDL", "implementer": "张三"}).json()["session"]
        content = base64.b64encode(b"x" * 21).decode("ascii")
        response = client.post(
            f"/api/sessions/{session['id']}/attachments",
            json={"filename": "ddb.log", "content_type": "text/plain", "content_base64": content},
        )
        assert response.status_code == 400
        assert "大小限制" in response.json()["detail"]


def test_storage_check_and_alerts_are_available(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    with client:
        _login(client)
        storage = client.get("/api/storage/check")
        alerts = client.get("/api/alerts")
        assert storage.status_code == 200
        assert storage.json()["vector_store"]["ok"] is True
        assert alerts.status_code == 200
        assert isinstance(alerts.json()["alerts"], list)


def test_knowledge_draft_requires_approval_before_publish(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    with client:
        csrf = _login(client)
        draft = tmp_path / "knowledge-base" / "13-待审核" / "draft.md"
        draft.write_text(
            """---
type: runbook
component: DDB
scenario: 新故障
priority: P2
tags: [DDB, 新故障]
status: draft
review_status: pending
---

# 新故障

这是一个经过人工整理的 DDB 故障处理步骤，包含判断依据和验证方式。
""",
            encoding="utf-8",
        )
        blocked = client.post(
            "/api/knowledge/publish",
            json={"draft_path": draft.as_posix(), "target_dir": "knowledge-base/07-故障卡片"},
            headers={"x-csrf-token": csrf},
        )
        assert blocked.status_code == 400

        approved = client.post("/api/knowledge/drafts/approve", json={"draft_path": draft.as_posix()}, headers={"x-csrf-token": csrf})
        assert approved.status_code == 200

        published = client.post(
            "/api/knowledge/publish",
            json={"draft_path": draft.as_posix(), "target_dir": "knowledge-base/07-故障卡片"},
            headers={"x-csrf-token": csrf},
        )
        assert published.status_code == 200
        assert Path(published.json()["path"]).exists()
        assert client.get("/api/evaluation/history").json()["history"]
