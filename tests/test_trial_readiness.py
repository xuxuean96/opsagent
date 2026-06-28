from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from ops_agent import app as app_module
from ops_agent.auth import hash_password
from ops_agent.app import app
from ops_agent.llm import LLMError, MockLLMClient


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

先检查 Java 运行环境、依赖 DLL 和授权服务。
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
                "auth:",
                "  enabled: true",
                "  username: admin",
                f"  password: {hash_password('admin')}",
                "  secret_key: test-secret",
                "  users:",
                "    - username: implementer1",
                f"      password: {hash_password('implementer1')}",
                "      role: implementer",
                "      enabled: true",
                "backup:",
                "  dir: data/backups",
                "  retention_count: 2",
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
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["csrf_token"]


def test_trial_entry_contains_session_constraints(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    with client:
        _login(client, "implementer1", "implementer1")
        response = client.get("/api/trial/entry")
        assert response.status_code == 200
        payload = response.json()
        assert payload["entry"]["requires_project_code_format"] == "拼音首字母大写缩写"
        assert "先创建会话" in payload["entry"]["chat_placeholder"]
        assert payload["entry"]["attachment_types"]
        assert payload["entry"]["feedback_options"] == ["resolved", "partial", "unresolved"]


def test_alert_center_records_backup_failure(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    with client:
        csrf = _login(client)
        bad_path = tmp_path / "missing" / "not-exists.zip"
        response = client.post(
            "/api/backup/verify",
            json={"archive_path": bad_path.as_posix()},
            headers={"x-csrf-token": csrf},
        )
        assert response.status_code == 400

        alerts = client.get("/api/alerts").json()["alerts"]
        assert any(item["code"] == "BACKUP_VERIFY_FAILED" for item in alerts)


def test_alert_center_records_llm_unavailable(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    with client:
        _login(client, "implementer1", "implementer1")
        session = client.post("/api/sessions", json={"project_code": "ZJDL", "implementer": "张三"}).json()["session"]

        def fail_answer(question: str, session_id: str):
            raise LLMError("network unavailable")

        monkeypatch.setattr(app_module.get_state(), "answer_with_task", fail_answer)
        response = client.post("/api/chat", json={"session_id": session["id"], "message": "DDB 启动失败"})
        assert response.status_code == 503

        client.post("/api/auth/logout")
        _login(client)
        alerts = client.get("/api/alerts").json()["alerts"]
        assert any(item["code"] == "LLM_UNAVAILABLE" for item in alerts)


def test_alert_center_records_job_failure(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    with client:
        csrf = _login(client)

        def fail_rebuild() -> int:
            raise RuntimeError("reindex failed")

        monkeypatch.setattr(app_module.get_state(), "rebuild_index", fail_rebuild)
        submit = client.post("/api/jobs/reindex", headers={"x-csrf-token": csrf})
        assert submit.status_code == 202
        job_id = submit.json()["job"]["id"]

        for _ in range(30):
            job = client.get(f"/api/jobs/{job_id}").json()["job"]
            if job["status"] == "failed":
                break
        assert job["status"] == "failed"

        alerts = client.get("/api/alerts").json()["alerts"]
        assert any(item["code"] == "JOB_FAILED" and item["source_id"] == job_id for item in alerts)
