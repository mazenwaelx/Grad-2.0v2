"""
Dynamic document retrieval based on question complexity.

Analyses Arabic questions to determine how many documents to
retrieve — simple questions get fewer, complex ones get more.
"""
from __future__ import annotations

import re
from typing import Dict, Any, List


# ── Complexity indicator catalogue ─────────────────────────────────

# Simple question patterns (reduce complexity score)
_SIMPLE_PATTERNS: List[str] = [
    r"^ما هو\s+",
    r"^ما هي\s+",
    r"^كم\s+",
    r"^متى\s+",
    r"^أين\s+",
]

# Complex question indicators (increase complexity score)
_COMPLEX_INDICATORS: List[str] = [
    "مقارنة", "فرق", "اختلاف", "بين",
    "إجراءات", "خطوات", "كيفية",
    "حالات", "أنواع", "أشكال",
    "استثناءات", "شروط",
    "تفصيل", "بالتفصيل", "اشرح",
]

# Multi-topic indicators (moderate increase)
_MULTI_TOPIC_INDICATORS: List[str] = [
    "و", "أو", "كذلك", "أيضاً",
    "جميع", "كل", "كافة",
]


class DynamicRetrieval:
    """Determine how many documents to retrieve based on question complexity."""

    # ── Scoring weights ────────────────────────────────────────────
    _COMPLEX_WEIGHT = 1.5
    _MULTI_TOPIC_WEIGHT = 1.0
    _LONG_QUESTION_THRESHOLD = 15  # words
    _SHORT_QUESTION_THRESHOLD = 5

    # ── Score → document-count mapping ─────────────────────────────
    _SCORE_TIERS = [
        (0, 2, "simple"),
        (2, 3, "simple"),
        (4, 4, "medium"),
        (6, 5, "complex"),
    ]
    _MAX_DOCS = 6
    _MAX_LEVEL = "very_complex"

    def analyze_question_complexity(self, question: str) -> Dict[str, Any]:
        """Analyse question complexity and recommend a document count."""
        question_lower = question.lower().strip()
        score = 0.0
        indicators: List[str] = []

        # Simple-pattern check
        if any(re.match(p, question_lower) for p in _SIMPLE_PATTERNS):
            score -= 2
            indicators.append("simple_pattern")

        # Complex indicators
        complex_count = sum(1 for ind in _COMPLEX_INDICATORS if ind in question_lower)
        score += complex_count * self._COMPLEX_WEIGHT
        indicators.extend(f"complex_{i}" for i in range(complex_count))

        # Multi-topic indicators
        multi_count = sum(1 for ind in _MULTI_TOPIC_INDICATORS if ind in question_lower)
        score += multi_count * self._MULTI_TOPIC_WEIGHT
        indicators.extend(f"multi_topic_{i}" for i in range(multi_count))

        # Question length
        word_count = len(question.split())
        if word_count > self._LONG_QUESTION_THRESHOLD:
            score += 1
            indicators.append("long_question")
        elif word_count < self._SHORT_QUESTION_THRESHOLD:
            score -= 1
            indicators.append("short_question")

        doc_count, level = self._score_to_recommendation(score)

        return {
            "complexity_score": score,
            "complexity_level": level,
            "recommended_docs": doc_count,
            "indicators_found": indicators,
            "word_count": word_count,
        }

    def get_optimal_k(self, question: str) -> int:
        """Return the optimal number of documents to retrieve."""
        return self.analyze_question_complexity(question)["recommended_docs"]

    # ── Private helpers ────────────────────────────────────────────
    def _score_to_recommendation(self, score: float):
        """Map a complexity score to (doc_count, level_name)."""
        for threshold, docs, level in self._SCORE_TIERS:
            if score <= threshold:
                return docs, level
        return self._MAX_DOCS, self._MAX_LEVEL


# ── Module-level convenience ───────────────────────────────────────
_instance = DynamicRetrieval()


def get_dynamic_k(question: str) -> int:
    """Return the optimal document count for a question."""
    return _instance.get_optimal_k(question)