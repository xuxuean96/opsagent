from __future__ import annotations

from .answering import append_validation_notes, validate_answer
from .config import AppConfig
from .llm import BaseLLMClient
from .logger import JsonlLogger
from .memory import ConversationMemory
from .models import ChatResponse, SourceRef
from .prompts import FALLBACK_ANSWER, SYSTEM_PROMPT
from .query import rewrite_query
from .retrieval import HybridRetriever


class ChatOrchestrator:
    def __init__(
        self,
        config: AppConfig,
        retriever: HybridRetriever,
        llm: BaseLLMClient,
        memory: ConversationMemory | None = None,
        logger: JsonlLogger | None = None,
    ):
        self.config = config
        self.retriever = retriever
        self.llm = llm
        self.memory = memory or ConversationMemory()
        self.logger = logger

    def answer(self, question: str, session_id: str, attachment_context: str = "") -> ChatResponse:
        rewritten_query = rewrite_query(question, attachment_context=attachment_context)
        results = self.retriever.search(rewritten_query, top_k=self.config.retrieval.top_k)
        results = [item for item in results if item.score >= self.config.retrieval.min_score]
        if not results:
            response = ChatResponse(answer=FALLBACK_ANSWER, session_id=session_id, sources=[], used_fallback=True)
            self._log(session_id, question, rewritten_query, response)
            return response

        context = self._build_context(results)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.memory.get(session_id))
        attachment_block = f"\n\n附件/日志内容：\n{attachment_context}" if attachment_context else ""
        messages.append(
            {
                "role": "user",
                "content": (
                    f"用户问题：{question}\n\n"
                    f"检索改写：{rewritten_query}\n\n"
                    f"知识库片段：\n{context}"
                    f"{attachment_block}\n\n"
                    "直接用自然一点的说法回答，先给结论，再给必要步骤。"
                    "如果有命令，放到代码块里；如果有风险，直接说明。"
                    "最后只保留一句很短的来源提示，别套固定小标题。"
                ),
            }
        )
        answer = self.llm.complete(messages)

        sources = [
            SourceRef(
                title=item.chunk.title,
                path=item.chunk.source_path,
                score=round(item.score, 3),
                snippet=item.chunk.text[:240].replace("\n", " "),
            )
            for item in results
        ]
        answer = self._polish_answer(answer)
        answer = append_validation_notes(answer, validate_answer(answer, has_sources=bool(sources)))
        response = ChatResponse(answer=answer, session_id=session_id, sources=sources)
        self.memory.add(session_id, "user", question)
        self.memory.add(session_id, "assistant", answer)
        self._log(session_id, question, rewritten_query, response)
        return response

    @staticmethod
    def _build_context(results) -> str:
        lines = []
        for i, item in enumerate(results, start=1):
            lines.append(f"[{i}] {item.chunk.title} ({item.chunk.source_path}, score={item.score:.2f})\n{item.chunk.text}")
        return "\n\n".join(lines)

    @staticmethod
    def _polish_answer(answer: str) -> str:
        lines = []
        for line in answer.splitlines():
            stripped = line.strip()
            if not stripped:
                lines.append("")
                continue
            if stripped.startswith(("一、", "二、", "三、", "四、", "五、", "六、", "七、", "八、", "九、")):
                lines.append(stripped.split("、", 1)[1].strip())
                continue
            if stripped.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
                lines.append(stripped[2:].strip())
                continue
            if stripped in {"结论：", "步骤：", "来源：", "参考："}:
                continue
            lines.append(line)
        cleaned = "\n".join(lines).strip()
        cleaned = cleaned.replace("【来源】", "来源：")
        cleaned = cleaned.replace("来源:\n", "来源：")
        return cleaned

    def _log(self, session_id: str, question: str, rewritten_query: str, response: ChatResponse) -> None:
        if not self.logger:
            return
        self.logger.write(
            {
                "session_id": session_id,
                "question": question,
                "rewritten_query": rewritten_query,
                "answer": response.answer,
                "sources": [source.__dict__ for source in response.sources],
                "used_fallback": response.used_fallback,
            }
        )
