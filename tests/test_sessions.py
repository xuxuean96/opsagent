import base64
from pathlib import Path

from ops_agent.sessions import (
    AdminStatus,
    FeedbackStatus,
    SessionStore,
    validate_project_code,
)


def test_project_code_must_be_pinyin_initials() -> None:
    assert validate_project_code("ZJDL") == "ZJDL"
    assert validate_project_code("zjdl") == "ZJDL"

    for value in ("浙江电力", "ZJDL01", "ZJ-DL", ""):
        try:
            validate_project_code(value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid project code accepted: {value}")


def test_session_store_tracks_feedback_and_pending_sessions(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "sessions.jsonl", tmp_path / "uploads", tmp_path / "drafts")

    session = store.create_session("ZJDL", "张三", component="DDB")
    store.record_feedback(session.id, FeedbackStatus.RESOLVED, "已解决")
    loaded = store.get_session(session.id)

    assert loaded is not None
    assert loaded.project_code == "ZJDL"
    assert loaded.feedback_status == FeedbackStatus.RESOLVED
    assert store.pending_feedback_sessions() == []


def test_upload_text_attachment_extracts_content(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "sessions.jsonl", tmp_path / "uploads", tmp_path / "drafts")
    session = store.create_session("ZJDL", "张三")
    content = base64.b64encode("DDB error: create xml failed".encode("utf-8")).decode("ascii")

    attachment = store.add_attachment(session.id, "ddb.log", "text/plain", content)

    assert attachment.extracted_text == "DDB error: create xml failed"
    assert Path(attachment.path).exists()


def test_admin_intervention_can_create_knowledge_draft(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "sessions.jsonl", tmp_path / "uploads", tmp_path / "drafts")
    session = store.create_session("ZJDL", "张三", component="KMVue")
    case = store.request_admin(session.id, "知识库多轮无法解决")
    store.resolve_admin_case(
        case.id,
        root_cause="kmconvertservice 缺少运行时",
        solution="补齐运行库后重启服务",
        create_draft=True,
    )

    loaded = store.get_admin_case(case.id)
    drafts = list((tmp_path / "drafts").glob("*.md"))

    assert loaded is not None
    assert loaded.status == AdminStatus.RESOLVED
    assert drafts
    assert "kmconvertservice 缺少运行时" in drafts[0].read_text(encoding="utf-8")
