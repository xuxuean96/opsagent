from pathlib import Path

from ops_agent.sessions import FeedbackStatus, SessionStore


def test_resolved_session_can_generate_candidate_draft(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "sessions.jsonl", tmp_path / "uploads", tmp_path / "drafts")
    session = store.create_session("ZJDL", "张三", component="DDB")
    store.record_feedback(session.id, FeedbackStatus.RESOLVED)

    draft_path = store.generate_candidate_from_session(session.id, "DDB 生成 XML 失败", "检查 update.xml 路径。")

    draft = Path(draft_path)
    assert draft.exists()
    assert "status: draft" in draft.read_text(encoding="utf-8")
    assert "DDB 生成 XML 失败" in draft.read_text(encoding="utf-8")


def test_unresolved_session_cannot_generate_candidate_draft(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "sessions.jsonl", tmp_path / "uploads", tmp_path / "drafts")
    session = store.create_session("ZJDL", "张三")

    try:
        store.generate_candidate_from_session(session.id, "问题", "答案")
    except ValueError as exc:
        assert "已解决会话" in str(exc)
    else:
        raise AssertionError("unresolved session should not create knowledge draft")


def test_publish_draft_marks_active_and_copies_to_target(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "sessions.jsonl", tmp_path / "uploads", tmp_path / "drafts")
    draft = tmp_path / "drafts" / "case.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text("---\nstatus: draft\n---\n# case", encoding="utf-8")

    published = store.publish_draft(draft, tmp_path / "kb" / "07-故障卡片")

    text = Path(published).read_text(encoding="utf-8")
    assert "status: active" in text


def test_review_analytics_groups_project_and_component(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "sessions.jsonl", tmp_path / "uploads", tmp_path / "drafts")
    first = store.create_session("ZJDL", "张三", component="DDB")
    second = store.create_session("ZJDL", "李四", component="KMVue")
    store.record_feedback(first.id, FeedbackStatus.RESOLVED)
    store.request_admin(second.id, "未解决")

    analytics = store.review_analytics(task_records=[{"status": "failed"}, {"answer": "输出校验提示"}])

    assert analytics["by_project"]["ZJDL"] == 2
    assert analytics["by_component"]["DDB"] == 1
    assert analytics["admin_cases"] == 1
    assert analytics["failed_tasks"] == 1
