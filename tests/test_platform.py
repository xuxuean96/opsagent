from pathlib import Path

from ops_agent.config import AppConfig, EvaluationConfig, LLMConfig, VectorStoreConfig
from ops_agent.evaluation import EvaluationRunner
from ops_agent.indexing import KnowledgeIndexer
from ops_agent.llm import MockLLMClient
from ops_agent.retrieval import HybridRetriever
from ops_agent.tasks import TaskStatus, TaskStore
from ops_agent.vector_store import SqliteVectorStore


def write_doc(root: Path, name: str, body: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_sqlite_vector_store_round_trips_chunks(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    db_path = tmp_path / "vectors.sqlite3"
    write_doc(kb, "07-故障卡片/kmvue.md", "# KMVue\n\nkmconvertservice runtime missing.")
    chunks = KnowledgeIndexer(kb).build_chunks()
    chunks[0].embedding = [1.0, 0.0, 0.0]

    store = SqliteVectorStore(VectorStoreConfig(path=str(db_path)))
    store.rebuild(chunks)
    results = store.search([1.0, 0.0, 0.0], top_k=1)

    assert results
    assert results[0].chunk.source_path.endswith("kmvue.md")
    assert results[0].vector_score == 1.0


def test_task_store_records_status_transitions(tmp_path: Path) -> None:
    store = TaskStore(tmp_path / "tasks.jsonl")

    task = store.create("session-1", "KMVue 启动失败")
    store.update(task.id, TaskStatus.RETRIEVING)
    store.update(task.id, TaskStatus.COMPLETED, answer="done")
    loaded = store.get(task.id)

    assert loaded is not None
    assert loaded.status == TaskStatus.COMPLETED
    assert loaded.answer == "done"
    assert store.list(limit=1)[0].id == task.id


def test_evaluation_runner_reports_retrieval_metrics(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    write_doc(kb, "07-故障卡片/kmvue.md", "# KMVue\n\nkmconvertservice runtime missing.")
    write_doc(
        kb,
        "11-测试集/eval.md",
        """# 评测集

## 用例 1

- question: KMVue runtime missing
- expected_sources: [kmvue.md]
- expected_keywords: [kmconvertservice]
""",
    )
    chunks = KnowledgeIndexer(kb).build_chunks()
    config = AppConfig(
        knowledge_base_path=str(kb),
        llm=LLMConfig(provider="mock", model="mock"),
        evaluation=EvaluationConfig(testset_path=str(kb / "11-测试集")),
    )
    runner = EvaluationRunner(config, HybridRetriever(chunks), MockLLMClient())

    report = runner.run()

    assert report.case_count == 1
    assert report.source_hit_rate == 1.0
    assert report.keyword_hit_rate == 1.0
