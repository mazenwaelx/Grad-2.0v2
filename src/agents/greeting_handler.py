"""
Greeting detection and response generation.

Handles Arabic and English greetings with typo tolerance
via fuzzy matching (SequenceMatcher).
"""
from __future__ import annotations

import re
from typing import List

from difflib import SequenceMatcher

# ── Greeting patterns (regex) ──────────────────────────────────────
GREETING_PATTERNS = [
    r'^(السلام عليكم|سلام عليكم|السلام عليكم ورحمة الله|وعليكم السلام|وعليكم السلام ورحمة الله)[\s\!\.\؟\?\,\،]*$',
    r'^(اهلا وسهلا|أهلا وسهلا|اهلاوسهلا|أهلاوسهلا|مرحبا بك|اهلا بك|أهلا بك)[\s\!\.\؟\?\,\،]*$',
    r'^(اهلا|أهلا|مرحبا|مرحبًا|سلام|هاي|هلا|صباح الخير|مساء الخير|اهلاً|أهلاً|هلو|الو|مرحب|يا هلا|اهلين|أهلين|تحياتي|مساء النور|صباح النور)[\s\!\.\؟\?\,\،]*$',
    r'^(hi|hello|hey|good morning|good evening|greetings|howdy)[\s\!\.\?\,]*$',
]

# Keywords that disqualify text from being treated as a greeting
_NOT_GREETING_KEYWORDS = [
    'ما', 'هل', 'كيف', 'لماذا', 'متى', 'أين', 'كم', 'من',
    'قانون', 'مادة', 'عامل', 'اجازة', 'إجازة', 'عمل', 'أجر', 'اجر',
]

# Known greeting phrases for fuzzy matching
_ARABIC_GREETINGS = [
    'أهلا', 'اهلا', 'مرحبا', 'مرحباً', 'هلا', 'اهلين', 'أهلين',
    'أهلا وسهلا', 'اهلا وسهلا', 'مرحبا بك', 'يا هلا',
    'السلام عليكم', 'سلام عليكم', 'سلام', 'صباح الخير', 'مساء الخير',
    'صباح النور', 'مساء النور', 'تحياتي', 'السلام', 'هلو', 'الو',
]

_ENGLISH_GREETINGS = [
    'hi', 'hello', 'hey', 'good morning', 'good evening',
    'greetings', 'howdy', 'hi there', 'hello there',
]

# Typo-tolerant patterns for creative Arabic typos
_TYPO_PATTERNS = [
    r'^(ا|أ|إ|آ)+(ح|ه|خ|)*هلا+(ا|أ|)*$',
    r'^مرح(ب|پ|ت)+(ا|و|)*$',
    r'^(ه|ح|خ)لا+(و|)*$',
    r'^(س|ص)لام+(ع|)*$',
]

# ── Canned responses ───────────────────────────────────────────────

GREETING_RESPONSE = """\
أهلاً وسهلاً! 👋

أنا مساعدك القانوني المتخصص في **قانون العمل المصري** (قانون 14 لسنة 2025).

يمكنني مساعدتك في:
• 📋 عقود العمل وشروطها
• 💰 الأجور والمستحقات المالية
• 🏖️ الإجازات بأنواعها
• ⚖️ حقوق وواجبات العامل وصاحب العمل
• 🔒 التأمينات الاجتماعية
• 📝 إنهاء علاقة العمل والفصل

**اسألني أي سؤال عن قانون العمل المصري!**"""

SALAM_RESPONSE = """\
وعليكم السلام ورحمة الله وبركاته 👋

أهلاً بك! أنا مساعدك القانوني المتخصص في **قانون العمل المصري**.

كيف يمكنني مساعدتك اليوم؟ اسألني عن أي موضوع متعلق بقانون العمل المصري."""


# ── Public API ─────────────────────────────────────────────────────

def is_greeting(text: str) -> bool:
    """Return *True* if *text* is a greeting (with typo tolerance)."""
    text = text.strip()
    text_lower = text.lower()
    normalized = re.sub(r'\s+', ' ', text)

    # Disqualify if it contains question-related keywords
    for kw in _NOT_GREETING_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            return False

    # 1. Exact regex match (fast path)
    for pattern in GREETING_PATTERNS:
        if re.match(pattern, text, re.IGNORECASE):
            return True

    # 2. Fuzzy match against known greetings
    if _fuzzy_match(text, _ARABIC_GREETINGS, threshold=0.75):
        return True
    if _fuzzy_match(text, _ENGLISH_GREETINGS, threshold=0.75):
        return True

    # 3. Typo patterns
    for pattern in _TYPO_PATTERNS:
        if re.match(pattern, normalized, re.IGNORECASE):
            return True

    return False


def get_greeting_response(text: str) -> str:
    """Return the appropriate greeting response."""
    if re.match(r'^(السلام عليكم|سلام عليكم)', text.strip(), re.IGNORECASE):
        return SALAM_RESPONSE
    return GREETING_RESPONSE


# ── Private helpers ────────────────────────────────────────────────

def _fuzzy_match(text: str, known: List[str], threshold: float = 0.75) -> bool:
    """Return *True* if *text* is similar enough to any known phrase."""
    text_clean = re.sub(r'[!.,?،؟\s]+$', '', text.strip().lower())

    for phrase in known:
        phrase_clean = phrase.strip().lower()
        similarity = SequenceMatcher(None, text_clean, phrase_clean).ratio()
        if similarity >= threshold:
            return True

        # Partial containment check
        if len(text_clean) >= 3:
            if text_clean in phrase_clean or phrase_clean in text_clean:
                overlap = min(len(text_clean), len(phrase_clean)) / max(len(text_clean), len(phrase_clean))
                if overlap >= 0.6:
                    return True

    return False
