"""
LangChain ReAct Agent for Egyptian Labour Law.

This module contains only the ``LangChainReActAgent`` class and
``PerformanceCallback``. All helper logic has been extracted into:

  - ``src.agents.greeting_handler``  — greeting detection / response
  - ``src.agents.input_validator``   — multiple-question & scope checks
  - ``src.agents.text_utils``        — Arabic normalisation, caching, repetition
  - ``src.agents.tool_builder``      — tool construction (``ToolBuilder``)
  - ``src.agents.prompt_templates``  — ``REACT_PROMPT_TEMPLATE``
"""
from __future__ import annotations

import re
import time
from collections import OrderedDict
from typing import Callable, List, Optional

from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain_core.callbacks import BaseCallbackHandler

# Extracted modules
from src.agents.greeting_handler import is_greeting, get_greeting_response
from src.agents.input_validator import has_multiple_questions, MULTIPLE_QUESTIONS_RESPONSE, ScopeValidator
from src.agents.text_utils import (
    normalize_question,
    get_cache_key,
    detect_repetition,
    clean_repetitive_text,
)
from src.agents.tool_builder import ToolBuilder, build_langchain_tools
from src.agents.prompt_templates import REACT_PROMPT_TEMPLATE


# ── Response cache ─────────────────────────────────────────────────
_CACHE_SIZE = 100


class _LRUCache(OrderedDict):
    """Simple LRU cache with a max size."""

    def __init__(self, maxsize: int = _CACHE_SIZE):
        super().__init__()
        self._maxsize = maxsize

    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        if len(self) > self._maxsize:
            oldest = next(iter(self))
            del self[oldest]


RESPONSE_CACHE = _LRUCache(_CACHE_SIZE)


# ── Performance monitoring ─────────────────────────────────────────
class PerformanceCallback(BaseCallbackHandler):
    """Tracks agent execution steps for diagnostics."""

    def __init__(self):
        self.step_count = 0
        self.start_time: Optional[float] = None
        self.tool_calls: List[dict] = []

    def on_agent_action(self, action, **kwargs):
        self.step_count += 1
        self.tool_calls.append({
            "tool": action.tool,
            "input_preview": str(action.tool_input)[:100],
            "step": self.step_count,
        })

    def on_agent_finish(self, finish, **kwargs):
        pass

    def reset(self):
        self.step_count = 0
        self.start_time = time.time()
        self.tool_calls = []


# ── Main agent class ───────────────────────────────────────────────
class LangChainReActAgent:
    """LangChain ReAct agent for Egyptian Labour Law questions.

    Lifecycle:
      1. ``__init__``  — build tools, prompt, agent, executor
      2. ``ask()``     — validate → cache → build context → invoke → post-process
    """

    # ── Valid short replies that should NOT trigger "incomplete" retry ──
    _VALID_SHORT_GREETINGS = [
        "وعليكم السلام", "وعليكم السلام ورحمة الله",
        "وعليكم السلام ورحمة الله وبركاته",
        "أهلاً", "مرحباً", "مرحبا",
    ]
    _VALID_OUT_OF_SCOPE = [
        "عذراً، تخصصي محدود في قانون العمل المصري فقط",
        "تخصصي محدود في قانون العمل",
        "خارج نطاق تخصصي", "لا يقع ضمن تخصصي",
    ]

    def __init__(
        self,
        llm,
        retriever,
        history_store,
        file_processor=None,
        chat_id: str = None,
        log_callback: Optional[Callable] = None,
        verbose: bool = False,
        max_iterations: int = 5,
        enable_performance_monitoring: bool = True,
    ) -> None:
        self.llm = llm
        self.retriever = retriever
        self.history_store = history_store
        self.file_processor = file_processor
        self.chat_id = chat_id
        self.log_callback = log_callback or (lambda msg: print(f"[LOG] {msg}"))
        self.verbose = verbose
        self.max_iterations = max_iterations
        self.enable_performance_monitoring = enable_performance_monitoring

        # Validators
        self._scope_validator = ScopeValidator()

        # Performance
        self.performance_callback = PerformanceCallback()

        # Build tools & agent
        self.tools = build_langchain_tools(retriever, history_store, file_processor, chat_id)
        self._build_agent()

    # ── Core public method ─────────────────────────────────────────
    def ask(self, question: str) -> str:
        """Process a user question and return the agent's response."""
        clean = question.strip()

        # 1. Greeting (no API call)
        if is_greeting(clean):
            return self._reply_shortcut("👋 Detected greeting", clean, get_greeting_response(clean))

        # 2. Out-of-scope (no API call)
        out_of_scope = self._scope_validator.check(clean)
        if out_of_scope:
            return self._reply_shortcut("🚫 Detected out-of-scope question", clean, out_of_scope)

        # 3. Multiple questions guard
        if has_multiple_questions(clean):
            return self._reply_shortcut("⚠️ Detected multiple questions", clean, MULTIPLE_QUESTIONS_RESPONSE)

        # 4. File-change detection & tool rebuild
        fingerprint = self._current_files_fingerprint()
        self._maybe_rebuild_tools(fingerprint)

        # 5. Cache check
        cache_key = get_cache_key(clean + fingerprint)
        if cache_key in RESPONSE_CACHE:
            self.log_callback("📦 Found cached response - returning without API call")
            cached = RESPONSE_CACHE[cache_key]
            self.history_store.add_user_message(clean)
            self.history_store.add_ai_message(cached)
            return cached

        # 6. Build conversation context
        context = self._get_conversation_context()
        full_input = f"{context}السؤال الحالي: {clean}" if context else clean

        if self.file_processor and self.file_processor.list_uploaded_files(self.chat_id):
            full_input += "\n\n[ملاحظة: قام المستخدم برفع ملفات/صور. إذا كان السؤال عن الملف المرفوع مثل 'اشرح'، يجب استخدام أداة uploaded_file_search لفحص الملفات المرفوعة أولاً وليس history]"


        self.log_callback("🤔 Processing question with ReAct agent...")

        # 7. Invoke agent with retry logic
        return self._invoke_with_retry(clean, full_input, cache_key)

    # ── Agent construction ─────────────────────────────────────────
    def _build_agent(self) -> None:
        """(Re)build the LangChain agent and executor."""
        tool_names = [t.name for t in self.tools]
        updated_prompt = REACT_PROMPT_TEMPLATE.replace(
            "[{tool_names}]", f"[{', '.join(tool_names)}]"
        )
        self.prompt = PromptTemplate.from_template(updated_prompt)

        self.agent = create_react_agent(llm=self.llm, tools=self.tools, prompt=self.prompt)

        callbacks = []
        if self.enable_performance_monitoring:
            callbacks.append(self.performance_callback)

        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=self.verbose,
            max_iterations=self.max_iterations,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
            callbacks=callbacks,
            max_execution_time=180,
            early_stopping_method="generate",
        )

    # ── Retry wrapper ──────────────────────────────────────────────
    _MAX_RETRIES = 2
    _RETRY_DELAY = 10

    def _invoke_with_retry(self, clean_question: str, full_input: str, cache_key: str) -> str:
        """Invoke the agent executor with retry logic."""
        try:
            for attempt in range(self._MAX_RETRIES + 1):
                try:
                    result = self.agent_executor.invoke({"input": full_input})
                    response = result.get("output", "عذراً، لم أتمكن من معالجة السؤال.")

                    # Try to recover from iteration-limit hits
                    response = self._try_recover(response, result)

                    # Clean repetitive output
                    response = self._clean_if_repetitive(response)

                    # Check for completeness
                    if self._is_incomplete(response) and attempt < self._MAX_RETRIES:
                        self.log_callback(f"⚠️ Incomplete response detected, retrying in {self._RETRY_DELAY}s...")
                        time.sleep(self._RETRY_DELAY)
                        continue

                    # Log steps
                    if self.verbose and "intermediate_steps" in result:
                        steps = result["intermediate_steps"]
                        self.log_callback(f"📝 Agent completed with {len(steps)} steps")
                        for i, (action, observation) in enumerate(steps):
                            self.log_callback(f"  Step {i+1}: {action.tool} -> {observation[:100]}...")

                    # Persist & cache
                    self.history_store.add_user_message(clean_question)
                    self.history_store.add_ai_message(response)
                    RESPONSE_CACHE[cache_key] = response
                    self.log_callback("✅ Response generated and cached successfully")
                    return response

                except Exception as e:
                    if self._is_quota_error(e):
                        if attempt < self._MAX_RETRIES:
                            self.log_callback(f"⏳ Quota exceeded, waiting {self._RETRY_DELAY}s before retry {attempt + 1}/{self._MAX_RETRIES}...")
                            time.sleep(self._RETRY_DELAY)
                            continue
                        return self._quota_response(clean_question)
                    raise

        except Exception as e:
            return self._error_response(clean_question, e)

    # ── Conversation context ───────────────────────────────────────
    def _get_conversation_context(self) -> str:
        """Build conversation context from recent messages."""
        messages = self.history_store.messages[-6:]
        if not messages:
            return ""

        lines = []
        for msg in messages:
            role = "المستخدم" if msg.type == "human" else "المساعد"
            text = msg.content.strip() if isinstance(msg.content, str) else str(msg.content)
            if len(text) > 300:
                text = text[:300] + "..."
            lines.append(f"{role}: {text}")

        return "المحادثة السابقة:\n" + "\n".join(lines) + "\n\n"

    # ── File fingerprinting & tool rebuild ─────────────────────────
    def _current_files_fingerprint(self) -> str:
        from src.retrieval.file_processor import get_file_processor

        fp = get_file_processor()
        if not fp:
            return ""
        current_files = fp.list_uploaded_files(self.chat_id)
        if not current_files:
            return ""
        return "|".join(sorted(f["hash"] for f in current_files))

    def _maybe_rebuild_tools(self, fingerprint: str) -> None:
        """Rebuild tools if uploaded files have changed."""
        if not hasattr(self, "_last_files_fingerprint"):
            self._last_files_fingerprint = fingerprint
            return

        if fingerprint == self._last_files_fingerprint:
            return

        self.log_callback("🔄 Uploaded files changed, rebuilding tools...")
        RESPONSE_CACHE.clear()
        self.log_callback("🧹 Response cache cleared due to file change")

        from src.retrieval.file_processor import get_file_processor

        fp = get_file_processor()
        new_tools = build_langchain_tools(self.retriever, self.history_store, fp)
        self.tools = new_tools
        self._build_agent()
        self.log_callback("✅ Tools and agent rebuilt successfully")
        self._last_files_fingerprint = fingerprint

    # ── Response helpers ───────────────────────────────────────────
    def _reply_shortcut(self, log_msg: str, question: str, response: str) -> str:
        """Log, persist, and return a pre-computed response."""
        self.log_callback(f"{log_msg} - responding without API call")
        self.history_store.add_user_message(question)
        self.history_store.add_ai_message(response)
        return response

    def _try_recover(self, response: str, result: dict) -> str:
        """Try to recover an answer from intermediate steps when the agent hit the iteration limit."""
        if "Agent stopped" not in response and "iteration limit" not in response:
            return response

        steps = result.get("intermediate_steps", [])
        recovered = []
        for action, observation in steps:
            if (action.tool == "_Exception"
                    and isinstance(observation, str)
                    and len(observation) > 200
                    and "عذراً، حدث خطأ" not in observation):
                cleaned = clean_repetitive_text(observation)
                if len(cleaned) > 100 and not detect_repetition(cleaned):
                    recovered.append(cleaned)

        if recovered:
            best = max(recovered, key=len)
            self.log_callback(f"✅ Recovered {len(best)} char answer from intermediate steps")
            return best

        return response

    def _clean_if_repetitive(self, response: str) -> str:
        if detect_repetition(response):
            self.log_callback("⚠️ Detected repetitive LLM output, cleaning...")
            response = clean_repetitive_text(response)
            if len(response) < 50:
                return "عذراً، حدث خطأ في إنشاء الإجابة (تكرار في المخرجات). يرجى إعادة صياغة السؤال."
        return response

    def _is_incomplete(self, response: str) -> bool:
        """Check if a response looks truncated."""
        if any(g in response for g in self._VALID_SHORT_GREETINGS):
            return False
        if any(p in response for p in self._VALID_OUT_OF_SCOPE):
            return False
        return len(response) < 50 or response.endswith("...")

    def _quota_response(self, question: str) -> str:
        msg = "عذراً، تم تجاوز حد الاستخدام المسموح للذكاء الاصطناعي. يرجى المحاولة مرة أخرى بعد دقيقة أو ترقية خطة الاستخدام."
        self.history_store.add_user_message(question)
        self.history_store.add_ai_message(msg)
        return msg

    def _error_response(self, question: str, error: Exception) -> str:
        import traceback
        self.log_callback(f"❌ Error in ReAct agent: {error}")
        print(f"[ERROR] ReAct agent failed: {error}")
        traceback.print_exc()

        if self._is_quota_error(error):
            msg = "عذراً، تم تجاوز حد الاستخدام المسموح للذكاء الاصطناعي. يرجى المحاولة مرة أخرى بعد دقيقة أو ترقية خطة الاستخدام من Google AI Studio."
        else:
            msg = "عذراً، حدث خطأ أثناء معالجة سؤالك. يرجى المحاولة مرة أخرى."

        self.history_store.add_user_message(question)
        self.history_store.add_ai_message(msg)
        return msg

    @staticmethod
    def _is_quota_error(e: Exception) -> bool:
        s = str(e)
        return "429" in s or "quota" in s.lower()

    @staticmethod
    def _handle_parsing_error(error) -> str:
        """Custom error handler for agent output-parsing failures."""
        error_str = str(error)

        # Try to extract a Final Answer from malformed output
        final_match = re.search(
            r'Final Answer\s*:?\s*(.*?)(?=\n(?:Thought|Action|Question)|$)',
            error_str,
            re.DOTALL,
        )
        if final_match:
            answer = final_match.group(1).strip()
            if answer and len(answer) > 20:
                return answer

        # Check if the "error" actually contains a substantial answer
        for marker in ["Action:", "Action Input:", "Thought:"]:
            idx = error_str.find(marker)
            if idx != -1:
                candidate = error_str[:idx].strip()
                candidate = re.sub(r"^.*?(?:Could not parse|Invalid Format|Parse Error).*?\n", "", candidate)
                candidate = candidate.strip()
                if len(candidate) > 100 and not candidate.startswith("Error"):
                    return candidate

        return (
            "عذراً، حدث خطأ في معالجة الرد. يرجى إعادة صياغة السؤال.\n\n"
            "💡 **نصيحة:** حاول أن تسأل سؤالاً واحداً محدداً في كل مرة."
        )
