from pathlib import Path

from ops_agent.answering import validate_answer
from ops_agent.config import AppConfig, LLMConfig, RetrievalConfig
from ops_agent.embedding import LocalHashEmbeddingClient
from ops_agent.errors import llm_unavailable_error
from ops_agent.indexing import KnowledgeIndexer
from ops_agent.llm import LLMError, MockLLMClient, create_llm_client, require_llm_available
from ops_agent.orchestrator import ChatOrchestrator
from ops_agent.prompts import SYSTEM_PROMPT
from ops_agent.query import rewrite_query
from ops_agent.retrieval import HybridRetriever
from ops_agent.sessions import FeedbackStatus, SessionStore


def write_doc(root: Path, name: str, body: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_query_rewriter_expands_colloquial_question() -> None:
    rewritten = rewrite_query("加密卡卡起来了，初始化失败")

    assert "加密卡" in rewritten
    assert "KmPermitServer" in rewritten


def test_retriever_deduplicates_same_source_path(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    write_doc(kb, "07-故障卡片/card.md", "# A\n\n加密卡启动失败 初始化错误\n\n## B\n\n加密卡启动失败 端口")
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


def test_system_prompt_prefers_plain_conversational_style_over_fixed_template() -> None:
    assert "自然一点" in SYSTEM_PROMPT
    assert "不要每次都硬分成固定几段" in SYSTEM_PROMPT
    assert "五段" not in SYSTEM_PROMPT


def test_orchestrator_polishes_template_like_model_output(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    write_doc(kb, "07-fault/card.md", "# 加密卡\n\n加密卡服务启动失败时先看进程和端口。")
    chunks = KnowledgeIndexer(kb).build_chunks()
    config = AppConfig(llm=LLMConfig(provider="mock", model="mock"))
    orchestrator = ChatOrchestrator(config, HybridRetriever(chunks), MockLLMClient())

    response = orchestrator.answer("加密卡起不来", "s1")

    assert "一、" not in response.answer
    assert "1." not in response.answer
    assert "结论：" not in response.answer


def test_orchestrator_uses_shorter_source_hint_and_natural_fallback(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    write_doc(kb, "07-fault/card.md", "# 加密卡\n\n加密卡服务启动失败时先看进程和端口。")
    chunks = KnowledgeIndexer(kb).build_chunks()
    config = AppConfig(llm=LLMConfig(provider="mock", model="mock"))
    orchestrator = ChatOrchestrator(config, HybridRetriever(chunks), MockLLMClient())

    response = orchestrator.answer("一个完全无关的问题", "s1")

    assert "可以先补这几项" in response.answer
    assert "1." not in response.answer
    assert "你可以先补这几项" in response.answer


def test_llm_unavailable_error_is_structured_for_ui() -> None:
    error = llm_unavailable_error().to_dict()

    assert error["code"] == "LLM_UNAVAILABLE"
    assert "无法生成排障回答" in error["message"]
    assert "API Key" in error["hint"]


class FailingLLMClient(MockLLMClient):
    def complete(self, messages):
        raise LLMError("network unavailable")


def test_runtime_rejects_mock_llm_provider() -> None:
    config = LLMConfig(provider="mock")

    try:
        create_llm_client(config, require_real=True)
    except LLMError as exc:
        assert "mock" in str(exc)
    else:
        raise AssertionError("mock provider should be rejected in runtime mode")


def test_runtime_requires_llm_health_check() -> None:
    try:
        require_llm_available(FailingLLMClient())
    except LLMError as exc:
        assert "LLM health check failed" in str(exc)
    else:
        raise AssertionError("unavailable LLM should fail health check")


def test_orchestrator_requires_llm_for_answer_generation(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    write_doc(kb, "07-fault/kmvue.md", "# KMVue Linux\n\nkmconvertservice missing runtime blocks startup.")
    chunks = KnowledgeIndexer(kb).build_chunks()
    config = AppConfig(llm=LLMConfig(provider="openai-compatible", api_key="test"))
    orchestrator = ChatOrchestrator(config, HybridRetriever(chunks), FailingLLMClient())

    try:
        orchestrator.answer("KMVue Linux runtime", session_id="s1")
    except LLMError as exc:
        assert "network unavailable" in str(exc)
    else:
        raise AssertionError("answer generation should fail when LLM is unavailable")
