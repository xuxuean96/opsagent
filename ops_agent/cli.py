from __future__ import annotations

import argparse
import sys

from .config import AppConfig
from .embedding import EmbeddingError, LocalHashEmbeddingClient, create_embedding_client
from .governance import KnowledgeGovernance
from .indexing import KnowledgeIndexer
from .vector_store import create_vector_store


def build_index() -> None:
    config = AppConfig.load()
    indexer = KnowledgeIndexer(
        config.knowledge_base_path,
        chunk_size=config.retrieval.chunk_size,
        chunk_overlap=config.retrieval.chunk_overlap,
    )
    chunks = indexer.build_chunks()
    embedder = create_embedding_client(config.embedding)
    try:
        indexer.attach_embeddings(chunks, embedder)
    except EmbeddingError as exc:
        print(f"embedding failed, fallback to local vectors: {exc}")
        indexer.attach_embeddings(chunks, LocalHashEmbeddingClient())
    indexer.save(chunks, config.index_path)
    vector_store = create_vector_store(config.vector_store)
    vector_store.rebuild(chunks)
    print(f"indexed {len(chunks)} chunks -> {config.index_path}, {config.vector_store.path}")


def govern_knowledge_base(report_path: str | None = None, strict: bool = False) -> None:
    config = AppConfig.load()
    governance = KnowledgeGovernance(config.knowledge_base_path)
    report = governance.inspect()
    if report_path:
        governance.write_report(report_path)
        print(f"governance report -> {report_path}")
    print(
        "knowledge governance: "
        f"files={report.file_count}, score={report.score}, "
        f"errors={report.error_count}, warnings={report.warning_count}, info={report.info_count}"
    )
    if strict and report.error_count:
        sys.exit(2)


def run_evaluation() -> None:
    from .evaluation import EvaluationRunner
    from .llm import create_llm_client
    from .retrieval import HybridRetriever

    config = AppConfig.load()
    chunks = KnowledgeIndexer.load(config.index_path)
    llm = create_llm_client(config.llm, require_real=True)
    report = EvaluationRunner(config, HybridRetriever(chunks), llm).write_reports()
    print(
        "evaluation: "
        f"cases={report.case_count}, "
        f"source_hit_rate={report.source_hit_rate:.2%}, "
        f"keyword_hit_rate={report.keyword_hit_rate:.2%}, "
        f"fallback_rate={report.fallback_rate:.2%}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="ops-agent")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("index")
    govern = sub.add_parser("govern")
    govern.add_argument("--report", help="write a markdown governance report")
    govern.add_argument("--strict", action="store_true", help="exit non-zero when errors exist")
    sub.add_parser("eval")
    args = parser.parse_args()
    if args.command == "index":
        build_index()
    elif args.command == "govern":
        govern_knowledge_base(report_path=args.report, strict=args.strict)
    elif args.command == "eval":
        run_evaluation()


if __name__ == "__main__":
    main()
