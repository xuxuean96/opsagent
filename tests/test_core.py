from pathlib import Path

from ops_agent.config import AppConfig, LLMConfig, RetrievalConfig
from ops_agent.indexing import KnowledgeIndexer
from ops_agent.retrieval import HybridRetriever
from ops_agent.orchestrator import ChatOrchestrator
from ops_agent.llm import LLMError, MockLLMClient, create_llm_client, require_llm_available
from ops_agent.embedding import LocalHashEmbeddingClient
from ops_agent.errors import llm_unavailable_error


def write_doc(root: Path, name: str, body: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_indexer_splits_markdown_with_metadata(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    write_doc(
        kb,
        "07-故障卡片/加密卡-启动失败.md",
        "---\ntype: runbook\ncomponent: 加密卡\ntags: [加密卡, 启动失败]\n---\n# 加密卡启动失败\n\n先查 KmPermitServer 进程和端口。",
    )

    chunks = KnowledgeIndexer(kb).build_chunks()

    assert len(chunks) == 1
    assert chunks[0].metadata["component"] == "加密卡"
    assert "KmPermitServer" in chunks[0].text
    assert chunks[0].source_path.endswith("加密卡-启动失败.md")


def test_hybrid_retriever_prioritizes_fault_cards(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    write_doc(kb, "10-原文拆分/raw.md", "# 原文\n\n加密卡 启动失败 初始化错误 原始说明")
    write_doc(
        kb,
        "07-故障卡片/card.md",
        "---\ntype: runbook\ncomponent: 加密卡\ntags: [加密卡, 启动失败]\n---\n# 卡片\n\n加密卡 启动失败 初始化错误 先查运行环境。",
    )
    chunks = KnowledgeIndexer(kb).build_chunks()

    results = HybridRetriever(chunks).search("Linux 下加密卡服务启动失败，报初始化错误", top_k=2)

    assert results
    assert "07-故障卡片" in results[0].chunk.source_path


def test_orchestrator_uses_fallback_when_no_retrieval(tmp_path: Path) -> None:
    config = AppConfig(
        llm=LLMConfig(provider="mock", model="mock"),
        retrieval=RetrievalConfig(min_score=999),
    )
    orchestrator = ChatOrchestrator(config, HybridRetriever([]), MockLLMClient())

    response = orchestrator.answer("完全无关的问题", session_id="s1")

    assert "当前知识库没有命中明确方案" in response.answer
    assert response.sources == []


def test_orchestrator_returns_answer_with_sources(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    write_doc(
        kb,
        "07-故障卡片/kmvue.md",
        "---\ntype: runbook\ncomponent: KMVue\ntags: [KMVue, kmconvertservice]\n---\n# KMVue Linux\n\nKMVue 报加密卡连接不上时，先查 kmconvertservice 运行环境。",
    )
    chunks = KnowledgeIndexer(kb).build_chunks()
    config = AppConfig(llm=LLMConfig(provider="mock", model="mock"))
    orchestrator = ChatOrchestrator(config, HybridRetriever(chunks), MockLLMClient())

    response = orchestrator.answer("KMVue Linux 报加密卡连接不上", session_id="s1")

    assert "kmconvertservice" in response.answer
    assert response.sources
    assert response.sources[0].path.endswith("kmvue.md")


def test_indexer_can_persist_local_vectors(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    index_path = tmp_path / "index.json"
    write_doc(kb, "07-fault/card.md", "# KMVue Linux\n\nkmconvertservice missing runtime blocks startup.")

    indexer = KnowledgeIndexer(kb)
    chunks = indexer.build_chunks()
    indexer.attach_embeddings(chunks, LocalHashEmbeddingClient(dimensions=32))
    indexer.save(chunks, index_path)
    loaded = KnowledgeIndexer.load(index_path)

    assert loaded[0].embedding
    assert len(loaded[0].embedding) == 32


def test_hybrid_retriever_uses_vector_signal_when_terms_do_not_overlap(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    write_doc(kb, "07-fault/kmvue.md", "# KMVue Linux\n\nkmconvertservice missing runtime blocks startup.")
    chunks = KnowledgeIndexer(kb).build_chunks()
    embedder = LocalHashEmbeddingClient(dimensions=32)
    KnowledgeIndexer(kb).attach_embeddings(chunks, embedder)

    retriever = HybridRetriever(chunks, embedder=embedder)
    results = retriever.search("kmconvertservice runtime", top_k=1)

    assert results
    assert results[0].chunk.source_path.endswith("kmvue.md")
    assert results[0].vector_score > 0


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


def test_llm_unavailable_error_is_structured_for_ui() -> None:
    error = llm_unavailable_error().to_dict()

    assert error["code"] == "LLM_UNAVAILABLE"
    assert "无法生成排障回答" in error["message"]
    assert "API Key" in error["hint"]
