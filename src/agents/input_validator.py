"""
Input validation for the ReAct agent.

- Multiple-question detection
- Out-of-scope question detection
"""
from __future__ import annotations

import re
from typing import Optional


# ── Multiple questions ─────────────────────────────────────────────

MULTIPLE_QUESTIONS_RESPONSE = """\
⚠️ **يبدو أنك أرسلت أكثر من 3 أسئلة في رسالة واحدة.**

للحصول على إجابات دقيقة وشاملة، يرجى إرسال **حتى 3 أسئلة كحد أقصى في كل مرة**.

هذا يساعدني على:
• تقديم إجابة مفصلة لكل سؤال
• تجنب الأخطاء والتأخير
• توفير مراجع دقيقة للمواد القانونية

**يمكنك إرسال 1-3 أسئلة في رسالة واحدة، ثم إرسال الأسئلة الإضافية في رسالة منفصلة.**"""

_MAX_QUESTIONS = 3


def has_multiple_questions(text: str) -> bool:
    """Return *True* if *text* contains more than 3 questions."""
    question_marks = text.count("?") + text.count("؟")
    if question_marks > _MAX_QUESTIONS:
        return True

    numbered_items = re.findall(r"\d+[\.)\-]\s*\S+", text)
    if len(numbered_items) > _MAX_QUESTIONS:
        return True

    sentences = re.split(r"[.،,\n]", text)
    question_sentences = sum(1 for s in sentences if "?" in s or "؟" in s)
    if question_sentences > _MAX_QUESTIONS:
        return True

    return False


# ── Out-of-scope detection ─────────────────────────────────────────

_OUT_OF_SCOPE_RESPONSE = """\
عذرًا، تخصصي محدود في **قانون العمل المصري** فقط.

لا يمكنني الإجابة على أسئلة خارج نطاق قانون العمل.

يمكنني مساعدتك في:
• 📋 عقود العمل وشروطها
• 💰 الأجور والمرتبات
• 🏖️ الإجازات بأنواعها
• ⚖️ حقوق العمال وواجباتهم
• 🚫 الفصل التعسفي والتعويضات
• 👩‍💼 حقوق المرأة العاملة
• ⏰ ساعات العمل والراحة

هل لديك سؤال عن قانون العمل المصري؟"""

# Keywords that indicate completely unrelated topics
_OUT_OF_SCOPE_KEYWORDS = [
    # Travel & Immigration
    "تأشيرة", "فيزا", "visa", "سفر", "جواز", "passport", "هجرة", "immigration",
    # Finance & Markets (non-labor)
    "ذهب", "gold", "أسعار الذهب", "دولار", "بورصة", "أسهم", "عملات", "بيتكوين", "crypto",
    # Criminal Law
    "سرقة", "قتل", "مخدرات", "جريمة", "جنائي", "سجن", "حبس",
    # Real Estate (non-labor)
    "إيجار شقة", "عقار", "شقة للبيع", "بيع عقار", "شراء منزل",
    # Medical / Health (non-labor context)
    "وصفة طبية", "دواء", "مستشفى", "علاج مرض",
    # Education (non-labor)
    "مدرسة", "جامعة",
    # Food & Recipes
    "طبخ", "وصفة طعام", "recipe", "مطعم",
    # Weather
    "طقس", "weather", "حالة الجو", "درجة حرارة",
    # Sports & Entertainment
    "كرة قدم", "مباراة", "فيلم", "مسلسل", "أغنية",
    # Technology (non-labor)
    "تحميل", "download", "برنامج", "تطبيق", "هاتف", "لابتوب",
    # Traffic & Driving
    "رخصة قيادة", "مرور", "سيارة", "حادث سير",
    # Family Law (separate from labor)
    "زواج", "طلاق", "نفقة", "حضانة", "ميراث", "إرث",
    # Religious
    "فتوى", "حلال", "حرام", "صلاة", "صيام",
]

# Labour-context words that override an out-of-scope keyword
_LABOUR_CONTEXT_WORDS = [
    "عمل", "عامل", "موظف", "شركة", "صاحب عمل",
    "راتب", "أجر", "أجور", "إجازة", "عقد",
    "حد أدنى", "مرتب", "مكافأة", "تعويض",
    "فصل", "تقاعد", "نقابة", "قانون العمل",
    "سلامة مهنية", "تأمينات", "منشأة",
    "تشغيل", "عمالة", "وظيفة",
]


class ScopeValidator:
    """Determines whether a question is within the labour-law scope."""

    def check(self, question: str) -> Optional[str]:
        """Return a polite rejection string if *question* is out of scope,
        or *None* if it is within scope.
        """
        question_lower = question.lower()

        for keyword in _OUT_OF_SCOPE_KEYWORDS:
            if keyword in question_lower:
                if not any(lc in question_lower for lc in _LABOUR_CONTEXT_WORDS):
                    return _OUT_OF_SCOPE_RESPONSE

        return None
