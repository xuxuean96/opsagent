from __future__ import annotations

import json
import re
import shutil
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from .config import AppConfig
from .llm import BaseLLMClient, LLMError
from .models import RetrievalResult
from .orchestrator import ChatOrchestrator
from .retrieval import HybridRetriever


FIELD_RE = re.compile(r"^-\s*(question|expected_sources|expected_keywords):\s*(.+)$", re.M)


@dataclass
class EvaluationCase:
    question: str
    expected_sources: list[str] = field(default_factory=list)
    expected_keywords: list[str] = field(default_factory=list)


@dataclass
class EvaluationCaseResult:
    question: str
    source_hit: bool
    keyword_hit: bool
    used_fallback: bool
    elapsed_ms: int
    sources: list[str]
    error: str | None = None


@dataclass
class EvaluationReport:
    case_count: int
    source_hit_rate: float
    keyword_hit_rate: float
    fallback_rate: float
    average_elapsed_ms: int
    results: list[EvaluationCaseResult]

    def to_dict(self) -> dict:
        return {
            "case_count": self.case_count,
            "source_hit_rate": self.source_hit_rate,
            "keyword_hit_rate": self.keyword_hit_rate,
            "fallback_rate": self.fallback_rate,
            "average_elapsed_ms": self.average_elapsed_ms,
            "results": [asdict(result) for result in self.results],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        lines = [
            "# 效果评测报告",
            "",
            f"- 用例数：{self.case_count}",
            f"- 来源命中率：{self.source_hit_rate:.2%}",
            f"- 关键词命中率：{self.keyword_hit_rate:.2%}",
            f"- 兜底率：{self.fallback_rate:.2%}",
            f"- 平均耗时：{self.average_elapsed_ms} ms",
            "",
            "## 明细",
            "",
        ]
        for result in self.results:
            lines.append(
                f"- `{result.question}` 来源命中={result.source_hit} "
                f"关键词命中={result.keyword_hit} 兜底={result.used_fallback} "
                f"耗时={result.elapsed_ms}ms 来源={', '.join(result.sources)}"
            )
            if result.error:
                lines.append(f"  - 错误：{result.error}")
        return "\n".join(lines)


class EvaluationRunner:
    def __init__(self, config: AppConfig, retriever: HybridRetriever, llm: BaseLLMClient):
        self.config = config
        self.retriever = retriever
        self.llm = llm

    def run(self) -> EvaluationReport:
        cases = load_cases(self.config.evaluation.testset_path)
        orchestrator = ChatOrchestrator(self.config, self.retriever, self.llm)
        results: list[EvaluationCaseResult] = []
        for case in cases:
            started = time.perf_counter()
            retrieval_results = self.retriever.search(case.question, top_k=self.config.retrieval.top_k)
            source_paths = [item.chunk.source_path for item in retrieval_results]
            try:
                response = orchestrator.answer(case.question, session_id="evaluation")
                answer = response.answer
                used_fallback = response.used_fallback
                error = None
            except LLMError as exc:
                answer = ""
                used_fallback = False
                error = str(exc)
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            results.append(
                EvaluationCaseResult(
                    question=case.question,
                    source_hit=_source_hit(case.expected_sources, retrieval_results),
                    keyword_hit=_keyword_hit(case.expected_keywords, answer, retrieval_results),
                    used_fallback=used_fallback,
                    elapsed_ms=elapsed_ms,
                    sources=source_paths,
                    error=error,
                )
            )
        return _build_report(results)

    def write_reports(self) -> EvaluationReport:
        report = self.run()
        json_path = Path(self.config.evaluation.report_json_path)
        md_path = Path(self.config.evaluation.report_md_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(report.to_json(), encoding="utf-8")
        md_path.write_text(report.to_markdown(), encoding="utf-8")
        history_dir = Path(self.config.evaluation.history_dir)
        history_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.copyfile(json_path, history_dir / f"eval-{stamp}.json")
        return report


def load_cases(root: str | Path) -> list[EvaluationCase]:
    path = Path(root)
    files = [path] if path.is_file() else sorted(path.rglob("*.md"))
    cases: list[EvaluationCase] = []
    for file in files:
        text = file.read_text(encoding="utf-8", errors="ignore")
        fields = dict((name, value.strip()) for name, value in FIELD_RE.findall(text))
        if "question" not in fields:
            continue
        cases.append(
            EvaluationCase(
                question=fields["question"],
                expected_sources=_parse_list(fields.get("expected_sources", "")),
                expected_keywords=_parse_list(fields.get("expected_keywords", "")),
            )
        )
    return cases


def list_evaluation_history(history_dir: str | Path, limit: int = 20) -> list[dict]:
    root = Path(history_dir)
    if not root.exists():
        return []
    history = []
    for path in sorted(root.glob("eval-*.json"), reverse=True)[:limit]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        history.append({"path": path.as_posix(), "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(), **data})
    return history


def _parse_list(value: str) -> list[str]:
    cleaned = value.strip()
    if cleaned.startswith("[") and cleaned.endswith("]"):
        cleaned = cleaned[1:-1]
    return [item.strip().strip("'\"") for item in cleaned.split(",") if item.strip()]


def _source_hit(expected_sources: list[str], results: list[RetrievalResult]) -> bool:
    if not expected_sources:
        return True
    paths = [item.chunk.source_path for item in results]
    return any(expected in path for expected in expected_sources for path in paths)


def _keyword_hit(expected_keywords: list[str], answer: str, results: list[RetrievalResult]) -> bool:
    if not expected_keywords:
        return True
    haystack = answer + "\n" + "\n".join(item.chunk.text for item in results)
    return all(keyword in haystack for keyword in expected_keywords)


def _build_report(results: list[EvaluationCaseResult]) -> EvaluationReport:
    count = len(results)
    if count == 0:
        return EvaluationReport(0, 0.0, 0.0, 0.0, 0, [])
    return EvaluationReport(
        case_count=count,
        source_hit_rate=sum(1 for result in results if result.source_hit) / count,
        keyword_hit_rate=sum(1 for result in results if result.keyword_hit) / count,
        fallback_rate=sum(1 for result in results if result.used_fallback) / count,
        average_elapsed_ms=int(sum(result.elapsed_ms for result in results) / count),
        results=results,
    )
