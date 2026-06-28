import base64
from pathlib import Path

from ops_agent.answering import validate_answer
from ops_agent.config import AppConfig, LLMConfig
from ops_agent.indexing import KnowledgeIndexer
from ops_agent.llm import MockLLMClient
from ops_agent.orchestrator import ChatOrchestrator
from ops_agent.query import rewrite_query
from ops_agent.retrieval import HybridRetriever
from ops_agent.sessions import FeedbackStatus, SessionStore


def write_doc(root: Path, name: str, body: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_query_rewriter_expands_colloquial_question() -> None:
    rewritten = rewrite_query("卡起不来，初始化失败")

    assert "加密卡" in rewritten
    assert "KmPermitServer" in rewritten


def test_retriever_deduplicates_same_source_path(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    write_doc(kb, "07-故障卡片/card.md", "# A\n\n加密卡 启动失败 初始化错误\n\n## B\n\n加密卡 启动失败 端口")
    chunks = KnowledgeIndexer(kb, chunk_size=20, chunk_overlap=0).build_chunks()

    results = HybridRetriever(chunks).search("加密卡 启动失败", top_k=5)

    paths = [item.chunk.source_path for item in results]
    assert len(paths) == len(set(paths))


def test_attachment_context_is_injected_into_answer_flow(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    write_doc(kb, "07-故障卡片/ddb.md", "# DDB\n\nDDB error failed create xml.")
    chunks = KnowledgeIndexer(kb).build_chunks()
    config = AppConfig(llm=LLMConfig(provider="mock", model="mock"))
    orchestrator = ChatOrchestrator(config, HybridRetriever(chunks), MockLLMClient())

    response = orchestrator.answer("这个日志怎么处理", "s1", attachment_context="DDB error failed create xml")

    assert response.sources
    assert "DDB error failed create xml" in response.answer


def test_answer_validator_flags_missing_sections_and_risky_operation() -> None:
    validation = validate_answer("建议删除配置后重启", has_sources=True)

    assert not validation.passed
    assert any("高危操作" in issue for issue in validation.issues)
    assert any("来源" in issue for issue in validation.issues)


def test_feedback_summary_counts_statuses(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "sessions.jsonl", tmp_path / "uploads", tmp_path / "drafts")
    first = store.create_session("ZJDL", "张三")
    second = store.create_session("HNDL", "李四")
    store.record_feedback(first.id, FeedbackStatus.RESOLVED)
    store.request_admin(second.id, "未解决")

    summary = store.feedback_summary()

    assert summary["resolved"] == 1
    assert summary["pending_feedback"] == 1
    assert summary["admin_requested"] == 1
