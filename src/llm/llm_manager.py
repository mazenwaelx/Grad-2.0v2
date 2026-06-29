"""
LLM initialization and management — Factory pattern.

``LLMFactory`` centralises LLM creation and fallback logic so that
adding a new model variant requires only editing the ``_FALLBACK_MODELS``
list.
"""
from __future__ import annotations

import os
import time
from typing import List, Optional

from langchain_google_genai import ChatGoogleGenerativeAI


class LLMCreationError(Exception):
    """Raised when all model variants fail to initialise."""


class LLMFactory:
    """Factory for creating LangChain LLM instances.

    Tries the requested model first, then falls back through a
    list of known-good alternatives.
    """

    _FALLBACK_MODELS: List[str] = [
        "models/gemini-2.5-flash",
        "models/gemini-2.0-flash-001",
        "models/gemini-flash-latest",
    ]

    _DEFAULT_CONFIG = {
        "temperature": 0.1,
        "max_tokens": 4096,
        "top_p": 0.95,
        "top_k": 40,
        "convert_system_message_to_human": True,
        "max_retries": 5,
    }

    _RATE_LIMIT_WAIT = 2  # seconds to wait between model attempts on 429

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        if not self._api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

    def create(self, model_name: str) -> ChatGoogleGenerativeAI:
        """Create and return a working LLM instance.

        Tries *model_name* first, then each fallback in order.

        Raises:
            LLMCreationError: If every variant fails.
        """
        candidates = self._build_candidate_list(model_name)

        for idx, variant in enumerate(candidates):
            llm = self._try_variant(variant, idx, len(candidates))
            if llm is not None:
                return llm

        raise LLMCreationError(
            "All model variants failed. "
            "Please check your API key and model availability."
        )

    # ── Private helpers ────────────────────────────────────────────
    def _build_candidate_list(self, model_name: str) -> List[str]:
        """Return a deduplicated ordered list of model names to try."""
        seen = set()
        candidates: List[str] = []
        for name in [model_name] + self._FALLBACK_MODELS:
            if name not in seen:
                seen.add(name)
                candidates.append(name)
        return candidates

    def _try_variant(
        self, model_name: str, index: int, total: int
    ) -> Optional[ChatGoogleGenerativeAI]:
        """Attempt to create and smoke-test a single model variant."""
        try:
            print(f"[DEBUG] Trying model: {model_name}")
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=self._api_key,
                **self._DEFAULT_CONFIG,
            )

            # Smoke-test the model
            llm.invoke("Test")
            print(f"[SUCCESS] Model {model_name} works!")
            return llm

        except Exception as e:
            error_str = str(e)
            print(f"[ERROR] Model {model_name} failed: {error_str[:100]}...")

            if self._is_rate_limit_error(error_str) and index < total - 1:
                print(
                    f"[INFO] Rate limited, waiting {self._RATE_LIMIT_WAIT}s "
                    f"before trying next model..."
                )
                time.sleep(self._RATE_LIMIT_WAIT)

            return None

    @staticmethod
    def _is_rate_limit_error(error_str: str) -> bool:
        """Check if an error string indicates a rate limit / quota issue."""
        lower = error_str.lower()
        return "429" in error_str or "quota" in lower or "resource" in lower


# ── Backward-compatible module-level function ──────────────────────
def init_llm(model_name: str) -> ChatGoogleGenerativeAI:
    """Initialise an LLM with the specified model (backward-compatible wrapper).

    Raises ``LLMCreationError`` (subclass of ``Exception``) if all
    model variants fail.
    """
    factory = LLMFactory()
    return factory.create(model_name)
