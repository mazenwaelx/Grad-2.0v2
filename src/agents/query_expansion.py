"""
Query expansion and compound-question detection for Arabic legal queries.
"""
from __future__ import annotations

import re
from typing import List


def expand_query(query: str) -> List[str]:
    """Domain-specific query expansion for Egyptian Labour Law."""
    variants = [query]
    q = query.lower()

    if "تعسف" in q:
        variants.extend(["إنهاء لسبب غير مشروع", "إنهاء لسبب غير مشروع تعويض",
                          "أجر شهرين عن كل سنة", "المادة 165"])
    if "الحد الأدنى" in q and "سن" in q:
        variants.extend(["يحظر تشغيل الأطفال قبل", "سن خمس عشرة سنة أطفال", "المادة 64"])
    if "الحد الأقصى" in q and "ساعات" in q:
        variants.extend(["يحظر تشغيل الطفل أكثر من ست ساعات", "ساعات عمل الطفل يوميا", "المادة 65"])
    if "إجازة" in q and any(w in q for w in ("وضع", "أمومة", "حامل")):
        variants.extend(["أربعة أشهر وضع", "إجازة العاملة الحامل", "المادة 54"])

    return list(dict.fromkeys(variants))


def detect_compound_question(question: str) -> List[str]:
    """Split a compound question into sub-queries (max 3)."""
    indicators = [
        r'،\s*و(?:ما|كم|هل|ماذا|أين|متى|كيف)',
        r'\s+و(?:ما|كم|هل|ماذا|أين|متى|كيف)\s+',
        r'؟.*(?:و|كذلك|أيضاً|بالإضافة).*؟',
        r'،\s*(?:ساعات|أيام|سن|عمر|مدة|فترة|حقوق|واجبات)',
    ]
    if not any(re.search(p, question) for p in indicators):
        return [question]

    subs: List[str] = []

    # By question marks
    parts = [p.strip() for p in re.split(r'[؟\?]', question) if p.strip()]
    if len(parts) >= 2:
        for p in parts:
            p = re.sub(r'^(و|كذلك|أيضاً|بالإضافة إلى ذلك|كما)\s+', '', p)
            if len(p) > 10:
                subs.append(p + '؟')

    # By "و" + question word
    if len(subs) < 2:
        parts = re.split(r'،?\s*و(?=(?:ما|كم|هل|ماذا|أين|متى|كيف)\s)', question)
        if len(parts) >= 2:
            subs = [p.strip() for p in parts if len(p.strip()) > 10]

    # By comma + legal terms
    if len(subs) < 2:
        parts = re.split(r'،\s*(?=(?:ساعات|أيام|سن|عمر|مدة|فترة|حقوق|واجبات|الحد))', question)
        if len(parts) >= 2:
            subs = [p.strip() for p in parts if len(p.strip()) > 10]

    return subs[:3] if len(subs) >= 2 else [question]
