"""
File relevance analysis — determines whether a user question
is about an uploaded file vs. the legal database.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Any, List


_EXPLICIT_FILE_KEYWORDS = [
    "الملف", "المستند", "الوثيقة", "المرفق", "الملف المرفوع",
    "في الملف", "من الملف", "حسب الملف", "وفقا للملف",
    "المحتوى", "النص", "البيانات", "المعلومات المرفقة",
    "الصورة", "صورة", "اشرح الصورة", "الصوره", "اشرح لي الصورة",
    "اللي رفعته", "رفعته", "المرفوعة", "المرفوع",
    "محتوى الصورة", "في الصورة", "من الصورة",
]

_STRONG_LEGAL = [
    "قانون العمل المصري", "حسب القانون", "وفقا للقانون",
    "القانون المصري", "النظام", "التشريع",
]

_WEAK_LEGAL = ["المادة", "حقوق العامل", "واجبات العامل", "العواقب القانونية"]

_CONTRACT_TERMS = ["طرف", "عقد", "اتفاقية", "شروط", "بنود"]
_WORKPLACE_TERMS = ["بيئة عمل", "مكان العمل", "السلامة المهنية", "وسائل السلامة", "صاحب العمل"]
_PROCEDURE_TERMS = ["كيف يتم", "كيفية", "إجراءات", "خطوات"]

_STOP_WORDS = {
    "في", "من", "إلى", "على", "عن", "مع", "هذا", "هذه", "التي", "الذي",
    "ما", "هل", "كيف", "متى", "أين", "لماذا", "كم", "أي", "كل", "بعض",
    "قد", "لقد", "كان", "كانت", "يكون", "تكون", "أن", "إن", "لكن",
    "أو", "أم", "بل", "لا", "لن", "لم", "غير", "سوى", "إلا",
}


class FileRelevanceAnalyzer:
    """Determine whether a user question is about an uploaded file."""

    def calculate_relevance(self, question: str, file_info: Dict[str, Any]) -> float:
        q = question.lower()

        for kw in _EXPLICIT_FILE_KEYWORDS:
            if kw in q:
                return 1.0

        basename = Path(file_info["filename"]).stem.lower()
        if len(basename) > 3 and basename in q:
            return 0.9

        try:
            docs = file_info.get("documents", [])[:5]
            file_words = set(" ".join(d.page_content.lower() for d in docs).split())
            q_words = {w for w in set(q.split()) - _STOP_WORDS if len(w) > 2}
            if not q_words:
                return 0.1

            overlap = len(q_words & file_words) / len(q_words)
            arabic_names = re.findall(r"[أ-ي]{3,}(?:\s+[أ-ي]{3,})*",
                                      " ".join(d.page_content.lower() for d in docs))
            entity_overlap = sum(1 for n in set(arabic_names) if n in q)

            contract = {"عقد", "اتفاقية", "شروط", "بنود", "راتب", "أجر", "مكافأة",
                        "مدة", "موظف", "عامل", "شركة", "طرف", "التزامات", "مسؤوليات", "ساعات"}
            legal = {"مادة", "فقرة", "قانون", "نظام", "حقوق", "واجبات", "تشريع",
                     "إجازة", "تأمين", "تعويض", "فصل", "استقالة"}

            score = (overlap * 0.5
                     + min(entity_overlap * 0.3, 0.6)
                     + min(len(q_words & contract) * 0.2, 0.4)
                     - min(len(q_words & legal) * 0.1, 0.3))
            score = max(0.0, min(score, 1.0))

            if len(q_words & {"قانون", "حقوق", "واجبات", "مادة", "نظام", "تشريع"}) >= 2:
                score *= 0.3

            return score
        except Exception:
            return 0.1

    def is_question_about_file(self, question: str, file_info: Dict[str, Any]) -> bool:
        q = question.lower()

        for kw in _EXPLICIT_FILE_KEYWORDS:
            if kw in q:
                return True

        docs = file_info.get("documents", [])
        is_ocr = any(d.metadata.get("ocr", False) for d in docs) if docs else False
        if is_ocr:
            if not any(ind in q for ind in _STRONG_LEGAL[:4]):
                return True

        strong = sum(1 for ind in _STRONG_LEGAL if ind in q)
        weak = sum(1 for ind in _WEAK_LEGAL if ind in q)

        if strong >= 2 or (strong >= 1 and weak >= 2):
            return False
        if re.search(r"المادة\s*\d+", q):
            return False

        relevance = self.calculate_relevance(question, file_info)

        has_contract = any(t in q for t in _CONTRACT_TERMS)
        has_workplace = any(t in q for t in _WORKPLACE_TERMS)
        has_procedure = any(t in q for t in _PROCEDURE_TERMS)
        total_legal = strong + weak

        if (total_legal >= 2 and not has_contract and not has_workplace) or has_procedure:
            return relevance >= 0.6
        if has_contract or has_workplace:
            return relevance >= 0.15
        if total_legal >= 1:
            return relevance >= 0.45
        return relevance >= 0.35
