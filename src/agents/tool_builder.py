"""
LangChain tool construction for the ReAct agent.

``ToolBuilder`` assembles the tool list. Individual tool methods
handle retrieval, history, and file search.
"""
from __future__ import annotations

import re
from typing import List, Dict

from langchain.tools import Tool

from src.agents.text_utils import normalize_arabic_text
from src.agents.query_expansion import expand_query, detect_compound_question
from src.agents.tool_descriptions import (
    CONVERSATION_HISTORY_DESC,
    UPLOADED_FILE_SEARCH_DESC, LEGAL_SEARCH_DESC,
)


class ToolBuilder:
    """Build LangChain Tool instances for the ReAct agent."""

    def __init__(self, retriever, history_store, file_processor=None, chat_id: str = None) -> None:
        self._retriever = retriever
        self._history = history_store
        self._fp = file_processor
        self._chat_id = chat_id

    def build(self) -> List[Tool]:
        tools = [
            Tool(name="conversation_history", func=self.memory_snapshot, description=CONVERSATION_HISTORY_DESC),
            Tool(name="article_reference", func=self.article_reference,
                 description="اعرض قائمة مختصرة بأرقام المواد ذات الصلة من قانون العمل المصري."),
        ]
        tools.insert(1, Tool(name="legal_search", func=self.law_lookup, description=LEGAL_SEARCH_DESC))
        if self._fp and self._fp.list_uploaded_files(self._chat_id):
            tools.append(Tool(name="uploaded_file_search", func=self.uploaded_file_search, description=UPLOADED_FILE_SEARCH_DESC))
        return tools

    # ── Tool: law_lookup ───────────────────────────────────────────

    def law_lookup(self, question: str) -> str:
        try:
            subs = detect_compound_question(question)
            if len(subs) > 1:
                return self._compound_lookup(question, subs)
            return self._single_lookup(question)
        except Exception as e:
            return self._fallback_lookup(question, e)

    def _single_lookup(self, question: str) -> str:
        from src.retrieval.dynamic_retrieval import get_dynamic_k
        optimal_k = get_dynamic_k(question)
        all_docs = []
        for v in expand_query(question):
            try:
                all_docs.extend(self._retriever.vectorstore.as_retriever(search_kwargs={"k": 15}).invoke(v))
            except Exception:
                pass
        if not all_docs:
            return "لم يتم العثور على مواد مرتبطة بالسؤال المطروح."
        unique = self._dedup(all_docs, optimal_k)
        return "\n\n".join(self._fmt(d, i + 1) for i, d in enumerate(unique))

    def _compound_lookup(self, question: str, subs: List[str]) -> str:
        all_docs, seen = [], set()
        for sq in subs:
            for v in expand_query(sq):
                try:
                    for d in self._retriever.vectorstore.as_retriever(search_kwargs={"k": 15}).invoke(v):
                        h = hash(d.page_content[:200])
                        if h not in seen:
                            seen.add(h)
                            all_docs.append(d)
                except Exception:
                    pass
        if not all_docs:
            return "لم يتم العثور على معلومات ذات صلة."
        parts = []
        for i, d in enumerate(all_docs[:8], 1):
            c = normalize_arabic_text(d.page_content.strip())[:600]
            m = re.search(r'المادة\s*(\d+)', c)
            parts.append(f"**{'المادة ' + m.group(1) if m else f'مقطع {i}'}:**\n{c}\n")
        return "\n".join(parts)

    def _fallback_lookup(self, question: str, err: Exception) -> str:
        try:
            docs = self._retriever.invoke(question)
            if docs:
                return "\n\n".join(self._fmt(d, i + 1) for i, d in enumerate(docs))
        except Exception:
            pass
        return f"حدث خطأ أثناء البحث: {err}"

    # ── Tool: article_reference ────────────────────────────────────

    def article_reference(self, question: str) -> str:
        try:
            from src.retrieval.dynamic_retrieval import get_dynamic_k
            k = min(get_dynamic_k(question), 4)
            docs = self._retriever.vectorstore.as_retriever(search_kwargs={"k": 15}).invoke(question)
            if not docs:
                return "لا توجد مراجع متاحة."
            refs = []
            for d in self._dedup(docs, k):
                art = d.metadata.get("article_number", d.metadata.get("article", "غير محددة"))
                parts = [f"المادة {art}"]
                if d.metadata.get("book"):
                    parts.append(f"({d.metadata['book']})")
                refs.append(" ".join(parts))
            return "\n".join(list(dict.fromkeys(refs))[:8])
        except Exception as e:
            return f"حدث خطأ: {e}"

    # ── Tool: memory_snapshot ──────────────────────────────────────

    def memory_snapshot(self, query: str) -> str:
        try:
            msgs = self._history.messages[-12:]
            if not msgs:
                return "لا توجد محادثات سابقة."
            topics_map = {'فصل': 'الفصل التعسفي', 'إجازة': 'الإجازات', 'أجر': 'الأجور',
                          'عقد': 'عقود العمل', 'تأمين': 'التأمينات', 'سلامة': 'السلامة المهنية'}
            topics, articles, lines = set(), set(), []
            reject = ["عذراً، أنا متخصص في قانون العمل المصري فقط", "خارج نطاق تخصصي"]

            for i, m in enumerate(msgs):
                text = m.content.strip() if isinstance(m.content, str) else str(m.content)
                if m.type != "human" and any(p in text for p in reject):
                    if lines and lines[-1].startswith("المستخدم:"):
                        lines.pop()
                    continue
                for kw, t in topics_map.items():
                    if kw in text:
                        topics.add(t)
                for a in re.findall(r'المادة\s*(\d+)', text):
                    articles.add(f"المادة {a}")
                role = "المستخدم" if m.type == "human" else "المساعد"
                limit = 200 if m.type == "human" else 800
                lines.append(f"{role}: {text[:limit]}{'...' if len(text) > limit else ''}")

            if not lines:
                return "لا توجد محادثات سابقة."
            parts = ["📚 **سياق المحادثة:**\n"]
            if topics:
                parts.append(f"🏷️ **المواضيع**: {'، '.join(sorted(topics))}")
            if articles:
                parts.append(f"📋 **المواد**: {'، '.join(sorted(articles))}")
            parts.append("\n💬 **المحادثة:**")
            parts.extend(lines)
            return "\n".join(parts)
        except Exception:
            return "لا توجد محادثات سابقة."


    # ── Tool: uploaded_file_search ─────────────────────────────────

    def uploaded_file_search(self, question: str) -> str:
        if not self._fp:
            return "لا توجد ملفات مرفوعة."
        files = self._fp.list_uploaded_files(self._chat_id)
        if not files:
            return "لا توجد ملفات مرفوعة."
        text, found = self._search_files(question, files)
        return text if found else "لم يتم العثور على معلومات ذات صلة في الملفات."

    # ── Shared helpers ─────────────────────────────────────────────

    def _search_files(self, question: str, files: List[Dict]) -> tuple:
        results, found = [], False
        for fi in files:
            try:
                docs = self._fp.search_in_file(fi["hash"], question, k=5)
                if not docs:
                    continue
                found = True
                results.append(f"📄 **{fi['filename']}**")
                for idx, d in enumerate(docs[:4], 1):
                    c = d.page_content.strip()
                    meta = []
                    if d.metadata.get("page"):
                        meta.append(f"ص{d.metadata['page']}")
                    ms = f" ({', '.join(meta)})" if meta else ""
                    results.append(f"المقطع {idx}{ms}:\n{c[:800]}")
            except Exception:
                continue
        return "\n".join(results), found

    def _fmt(self, doc, idx: int) -> str:
        art = doc.metadata.get("article_number", doc.metadata.get("article", "غير محددة"))
        src = doc.metadata.get("source", "قانون العمل 2025")
        snippet = normalize_arabic_text(doc.page_content.strip())[:600]
        return f"المقتطف {idx} — المادة: {art} — المصدر: {src}\n{snippet}"

    @staticmethod
    def _dedup(docs, limit: int):
        seen, out = set(), []
        for d in docs:
            n = re.sub(r'[\s\.؟\?\!]+', '', d.page_content[:200])
            if n not in seen:
                seen.add(n)
                out.append(d)
                if len(out) == limit:
                    break
        return out


def build_langchain_tools(retriever, history_store, file_processor=None, chat_id: str = None) -> List[Tool]:
    """Backward-compatible wrapper."""
    return ToolBuilder(retriever, history_store, file_processor, chat_id).build()
