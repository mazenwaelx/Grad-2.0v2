"""
Text utilities for the ReAct agent.

- Arabic text normalisation
- Question normalisation and cache-key generation
- Repetition detection and cleaning
"""
from __future__ import annotations

import re
import hashlib
from collections import Counter
from typing import List


# ── Arabic normalisation ───────────────────────────────────────────

# Presentation-form → standard mappings
_PRESENTATION_MAP = {
    "\ufef5": "لا", "\ufef6": "لا", "\ufef7": "لا", "\ufef8": "لا",
    "\ufef9": "لأ", "\ufefa": "لأ", "\ufefb": "لإ", "\ufefc": "لإ",
}

# Zero-width and directional characters to strip
_INVISIBLE_CHARS = frozenset([
    "\u200c", "\u200d", "\u200e", "\u200f",
    "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",
    "\ufeff",
])

# Problematic display characters
_BOX_CHARS = frozenset(["\u25a1", "\u25af", "\ufffd"])

# Allowed Unicode ranges for final filtering
_ALLOWED_RANGES = [
    (0x0020, 0x007E),
    (0x00A0, 0x00FF),
    (0x0600, 0x06FF),
    (0x0750, 0x077F),
    (0x08A0, 0x08FF),
    (0xFB50, 0xFDFF),
    (0xFE70, 0xFEFF),
]


def normalize_arabic_text(text: str) -> str:
    """Normalise Arabic text for display.

    Removes tatweel, invisible characters, presentation forms, and
    non-printable characters while keeping Arabic, Latin, numbers,
    punctuation, and whitespace.
    """
    if not text:
        return text

    # Remove tatweel (kashida)
    text = text.replace("\u0640", "")

    # Remove invisible / directional characters
    for ch in _INVISIBLE_CHARS:
        text = text.replace(ch, "")

    # Remove box / replacement characters
    for ch in _BOX_CHARS:
        text = text.replace(ch, "")

    # Remove control characters (keep \n, \r, \t)
    text = "".join(c for c in text if ord(c) >= 32 or c in "\n\r\t")

    # Normalise multiple spaces
    text = re.sub(r" +", " ", text)

    # Presentation forms → standard
    for old, new in _PRESENTATION_MAP.items():
        text = text.replace(old, new)

    # Final filter: keep only allowed characters
    def _allowed(ch: str) -> bool:
        if ch in "\n\r\t":
            return True
        code = ord(ch)
        return any(lo <= code <= hi for lo, hi in _ALLOWED_RANGES)

    text = "".join(c for c in text if _allowed(c))
    return text.strip()


# ── Question normalisation and caching ─────────────────────────────

def normalize_question(question: str) -> str:
    """Normalise a question for cache lookup.

    Lowercases, normalises Arabic letter variants, removes diacritics,
    and collapses whitespace.
    """
    text = question.strip().lower()
    text = re.sub("[إأٱآا]", "ا", text)
    text = re.sub("ى", "ي", text)
    text = re.sub("ة", "ه", text)
    text = re.sub("ؤ", "ء", text)
    text = re.sub("ئ", "ء", text)
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def get_cache_key(question: str) -> str:
    """Generate a cache key from a normalised question."""
    normalized = normalize_question(question)
    return hashlib.md5(normalized.encode("utf-8"), usedforsecurity=False).hexdigest()


# ── Repetition detection / cleaning ────────────────────────────────

def detect_repetition(
    text: str,
    min_repeat_len: int = 20,
    max_repeats: int = 3,
) -> bool:
    """Return *True* if *text* shows excessive repetition (LLM degeneration)."""
    if not text or len(text) < min_repeat_len * 2:
        return False

    # Strategy 1: repeated lines
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if len(lines) >= 5:
        most_common_line, count = Counter(lines).most_common(1)[0]
        if count > max_repeats and len(most_common_line) >= min_repeat_len:
            return True

    # Strategy 2: repeated bullet points
    bullets = re.findall(r"^\s*[\*\-•]\s*(.+)$", text, re.MULTILINE)
    if len(bullets) >= 5:
        _, count = Counter(bullets).most_common(1)[0]
        if count > max_repeats:
            return True

    # Strategy 3: repeated 5-word phrases
    words = text.split()
    if len(words) > 30:
        phrases = [" ".join(words[i : i + 5]) for i in range(len(words) - 4)]
        _, count = Counter(phrases).most_common(1)[0]
        if count >= 3:
            return True

    return False


def clean_repetitive_text(text: str) -> str:
    """Remove repeated lines / blocks and duplicate sentences."""
    if not text:
        return text

    # 1. Deduplicate lines
    seen_lines: set = set()
    cleaned_lines: List[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or len(stripped) < 10:
            cleaned_lines.append(line)
            continue
        if stripped in seen_lines:
            continue
        seen_lines.add(stripped)
        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines).strip()

    # 2. Deduplicate sentences within paragraphs
    paragraphs: List[str] = []
    for para in cleaned.split("\n"):
        stripped_para = para.strip()
        if not stripped_para or len(stripped_para) < 20:
            paragraphs.append(para)
            continue

        sentences = re.split(r"([\.؟\?\!]\s+)", para)
        reconstructed = []
        i = 0
        while i < len(sentences):
            s = sentences[i].strip()
            punc = sentences[i + 1] if i + 1 < len(sentences) else ""
            if s:
                reconstructed.append((s, punc))
            i += 2

        seen_sentences: set = set()
        unique = []
        for s, punc in reconstructed:
            norm = re.sub(r"[\s\.؟\?\!]+", "", s)
            if norm not in seen_sentences:
                seen_sentences.add(norm)
                unique.append(s + punc)

        paragraphs.append("".join(unique))

    return "\n".join(paragraphs).strip()
