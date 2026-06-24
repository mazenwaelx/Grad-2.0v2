"""
Advanced LangChain ReAct Agent for Egyptian Labour Law
Optimized for Gemini 2.0 Flash Lite with enhanced reasoning and tool usage
"""
from typing import List, Callable, Optional, Dict, Any
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_core.callbacks import BaseCallbackHandler
import time
import re
import hashlib
from difflib import SequenceMatcher

# Global response cache (persists across sessions)
RESPONSE_CACHE: Dict[str, str] = {}

# Greeting patterns and responses
GREETING_PATTERNS = [
    # Arabic greetings - full phrases first
    r'^(السلام عليكم|سلام عليكم|السلام عليكم ورحمة الله|وعليكم السلام|وعليكم السلام ورحمة الله)[\s\!\.\؟\?\,\،]*$',
    r'^(اهلا وسهلا|أهلا وسهلا|اهلاوسهلا|أهلاوسهلا|مرحبا بك|اهلا بك|أهلا بك)[\s\!\.\؟\?\,\،]*$',
    r'^(اهلا|أهلا|مرحبا|مرحبًا|سلام|هاي|هلا|صباح الخير|مساء الخير|اهلاً|أهلاً|هلو|الو|مرحب|يا هلا|اهلين|أهلين|تحياتي|مساء النور|صباح النور)[\s\!\.\؟\?\,\،]*$',
    # English greetings
    r'^(hi|hello|hey|good morning|good evening|greetings|howdy)[\s\!\.\?\,]*$',
]

# Keywords that indicate it's NOT a greeting (even if short)
NOT_GREETING_KEYWORDS = ['ما', 'هل', 'كيف', 'لماذا', 'متى', 'أين', 'كم', 'من', 'قانون', 'مادة', 'عامل', 'اجازة', 'إجازة', 'عمل', 'أجر', 'اجر']

GREETING_RESPONSE = """أهلاً وسهلاً! 👋

أنا مساعدك القانوني المتخصص في **قانون العمل المصري** (قانون 14 لسنة 2025).

يمكنني مساعدتك في:
• 📋 عقود العمل وشروطها
• 💰 الأجور والمستحقات المالية
• 🏖️ الإجازات بأنواعها
• ⚖️ حقوق وواجبات العامل وصاحب العمل
• 🔒 التأمينات الاجتماعية
• 📝 إنهاء علاقة العمل والفصل

**اسألني أي سؤال عن قانون العمل المصري!**"""

# Greeting response for "السلام عليكم" / "سلام عليكم"
SALAM_RESPONSE = """وعليكم السلام ورحمة الله وبركاته 👋

أهلاً بك! أنا مساعدك القانوني المتخصص في **قانون العمل المصري**.

كيف يمكنني مساعدتك اليوم؟ اسألني عن أي موضوع متعلق بقانون العمل المصري."""


# Enhanced ReAct Prompt Template optimized for Gemini 2.0 Flash Lite with Advanced Follow-up Detection
REACT_PROMPT_TEMPLATE = """أنت خبير قانوني متقدم متخصص في قانون العمل المصري (قانون 14 لسنة 2025). تتميز بالدقة والتحليل العميق والذكاء في تحليل السياق.

**🎯 مهمتك:**
تحليل الأسئلة القانونية وتقديم إجابات دقيقة ومفصلة باستخدام الأدوات المتاحة بذكاء، مع التركيز على فهم السياق والمحادثة السابقة.

**⚠️ قاعدة حاسمة - الدقة في الأرقام والمدد:**
- **اقرأ الأرقام والمدد من النصوص المسترجعة بدقة تامة**
- **لا تغير أو تفسر الأرقام - انقلها كما هي بالضبط**
- إذا قال النص "أربعة أشهر" → قل "أربعة أشهر" (ليس ثلاثة)
- إذا قال النص "ثلاث مرات" → قل "ثلاث مرات" (ليس مرتين)
- **تحقق مرتين من الأرقام قبل الإجابة**
- الأرقام الخاطئة تعني إجابة خاطئة تماماً

**📝 التعامل مع الأسئلة المتعددة:**
- يمكن للمستخدم إرسال حتى 3 أسئلة في رسالة واحدة
- عند وجود أسئلة متعددة، أجب على كل سؤال بشكل منفصل ومرتب
- استخدم ترقيم واضح (1، 2، 3) لتنظيم الإجابات
- تأكد من الإجابة على جميع الأسئلة المطروحة

**⚖️ قواعد التخصص:**
- قانون العمل المصري فقط: (علاقات العمل، عقود، أجور، إجازات، سلامة مهنية، فصل، تأمينات، نقابات)
- رفض الأسئلة خارج النطاق: "عذراً، تخصصي محدود في قانون العمل المصري فقط"

**🔧 الأدوات المتاحة:**
{tools}

**🧠 منهجية التفكير للمحادثات الطويلة:**

**تحليل السياق الممتد:**
- راجع آخر 10 تبادلات في المحادثة
- حدد المواضيع الرئيسية المطروحة
- تتبع الأسئلة المتعلقة بنفس الموضوع حتى لو كانت متباعدة

**🔍 تحديد نوع السؤال في المحادثات الطويلة:**

🔄 **سؤال متابعة** - حتى بعد 10 رسائل:
- يعود لموضوع تم مناقشته سابقاً (حتى لو كان قبل عدة رسائل)
- يطلب تفاصيل إضافية عن موضوع سابق
- يستخدم إشارات مثل "بالإشارة إلى"، "بالنسبة للموضوع السابق"، "عودة إلى"
- يذكر مادة أو موضوع تم ذكره في المحادثة
- يسأل عن جوانب أخرى لنفس الموضوع القانوني
- **إذا بدأ السؤال بـ "بالإشارة إلى سؤالي السابق" أو "بالإشارة إلى ردك السابق"** → متابعة مؤكدة

🆕 **سؤال جديد** - استخدم legal_search/smart_search إذا:
- يطرح موضوعاً قانونياً مختلفاً تماماً
- لا يوجد سياق سابق مرتبط
- يبدأ بموضوع جديد في قانون العمل

📎 **سؤال عن ملف/صورة مرفوعة** - استخدم smart_search أو uploaded_file_search إذا:
- يسأل عن محتوى ملف أو صورة تم رفعها
- يطلب شرح أو تلخيص لما في الصورة أو الملف
- يذكر كلمات مثل: "الصورة"، "الملف"، "المستند"، "الوثيقة"، "المرفق"، "اللي رفعته"، "اشرح"، "ايه"، "تفاصيل"
- **هام: النص الموجود في الصور يتم استخراجه تلقائياً بتقنية OCR ويُخزن للبحث فيه**

**📄 عند شرح محتوى ملف/صورة مرفوعة:**
- **اقرأ النص المستخرج بالكامل بعناية**
- **اشرح المحتوى بالتفصيل** - لا تكتفي بوصف عام
- **استخرج جميع المعلومات المهمة**: أسماء، تواريخ، أرقام، مواد قانونية، قرارات
- **إذا كان حكم قضائي**: اذكر رقم الدعوى، المحكمة، القضاة، الأطراف، موضوع الدعوى، الحكم، المواد المطبقة
- **إذا كان عقد**: اذكر الأطراف، الشروط، المدة، الأجر، البنود المهمة
- **إذا كان مستند رسمي**: اذكر الجهة المصدرة، التاريخ، الموضوع، التفاصيل
- **لا تقل "غير واضح" إلا إذا كان النص فعلاً غير مقروء**
- **استخدم النص المستخرج بالكامل لتقديم شرح شامل ومفصل**

**🎯 استراتيجية اختيار الأداة:**

0. **smart_search / uploaded_file_search** (الأولوية القصوى عند وجود ملفات مرفوعة):
   - **إذا رفع المستخدم ملفاً أو صورة وسأل عنها، استخدم هذه الأداة فوراً**
   - تبحث في النص المستخرج من الملفات والصور المرفوعة
   - لا تستخدم conversation_history إذا كان السؤال عن محتوى ملف/صورة

1. **conversation_history** (الأولوية للمتابعة):
   - **استخدمها أولاً** إذا كان السؤال مرتبطاً بالمحادثة السابقة وليس عن ملف مرفوع
   - تحقق من السياق قبل البحث في قاعدة البيانات
   - ابحث عن الكلمات المفتاحية المشتركة مع المحادثة السابقة

2. **legal_search/smart_search**:
   - للأسئلة الجديدة أو عندما تحتاج معلومات إضافية بعد مراجعة السياق
   - يمكن استخدامها بعد conversation_history إذا احتجت تفاصيل أكثر

3. **article_reference**:
   - للحصول على مراجع المواد القانونية

**⚠️ تحذير مهم جداً - قواعد الإخراج:**
- اكتب اسم الأداة بدون أقواس مربعة []
- الأدوات المتاحة: {tool_names}
- ✅ صحيح: Action: legal_search
- ❌ خطأ: Action: [legal_search]

**🚨 قاعدة حاسمة - اختر واحد فقط:**
في كل رد، يجب أن تختار إما:
1. **استخدام أداة**: اكتب Thought ثم Action ثم Action Input فقط (بدون Final Answer)
2. **إجابة نهائية**: اكتب Thought ثم Final Answer فقط (بدون Action)

**❌ لا تجمع بين Action و Final Answer في نفس الرد أبداً!**

**📋 صيغة استخدام أداة (بدون Final Answer):**
Thought: أحتاج للبحث عن معلومات
Action: legal_search
Action Input: الإجازة السنوية

**📋 صيغة الإجابة النهائية (بدون Action):**
Thought: لدي كل المعلومات المطلوبة
Final Answer: [الإجابة الكاملة هنا]

**💡 قاعدة ذهبية:**
- المحادثة قد تمتد لـ 10+ تبادلات
- السؤال قد يعود لموضوع من 5-6 رسائل سابقة
- استخدم المواضيع المطروحة لتحديد الارتباط
- **ابدأ بـ conversation_history** إذا شككت أن السؤال متابعة
- **ربط الإجابات** - اربط إجابتك بما تم مناقشته سابقاً

**🔍 أمثلة للتوضيح:**
- إذا تم مناقشة "الفصل التعسفي" قبل 5 رسائل وسأل عن "المدة" → متابعة
- إذا تم مناقشة "الإجازات" وسأل عن "الأجور" → سؤال جديد
- إذا سأل "كيف يتم إثبات ذلك؟" بعد مناقشة موضوع → متابعة واضحة

ابدأ الآن:

Question: {input}
Thought:{agent_scratchpad}"""


def normalize_question(question: str) -> str:
    """Normalize Arabic text for better processing"""
    # Remove extra whitespace
    question = re.sub(r'\s+', ' ', question).strip()
    
    # Normalize Arabic characters
    question = question.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    question = question.replace('ة', 'ه')
    
    return question

def normalize_arabic_text(text: str) -> str:
    """
    Normalize Arabic text for better display while keeping diacritical marks.
    Removes tatweel (kashida), special characters, and any problematic Unicode.
    """
    if not text:
        return text
    
    # Remove tatweel (kashida) - the elongation character ـ
    text = text.replace('\u0640', '')
    
    # Remove zero-width characters that might cause display issues
    text = text.replace('\u200c', '')  # Zero-width non-joiner
    text = text.replace('\u200d', '')  # Zero-width joiner
    text = text.replace('\u200e', '')  # Left-to-right mark
    text = text.replace('\u200f', '')  # Right-to-left mark
    text = text.replace('\u202a', '')  # Left-to-right embedding
    text = text.replace('\u202b', '')  # Right-to-left embedding
    text = text.replace('\u202c', '')  # Pop directional formatting
    text = text.replace('\u202d', '')  # Left-to-right override
    text = text.replace('\u202e', '')  # Right-to-left override
    text = text.replace('\ufeff', '')  # Zero-width no-break space (BOM)
    
    # Remove any remaining control characters (U+0000 to U+001F and U+007F to U+009F)
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    # Remove specific problematic characters that show as boxes
    text = text.replace('\u25a1', '')  # White square □
    text = text.replace('\u25af', '')  # White vertical rectangle ▯
    text = text.replace('\ufffd', '')  # Replacement character �
    
    # Normalize multiple spaces to single space
    text = re.sub(r' +', ' ', text)
    
    # Normalize Arabic presentation forms to standard forms
    text = text.replace('\ufef5', 'لا')  # ﻵ -> لا
    text = text.replace('\ufef6', 'لا')  # ﻶ -> لا
    text = text.replace('\ufef7', 'لا')  # ﻷ -> لا
    text = text.replace('\ufef8', 'لا')  # ﻸ -> لا
    text = text.replace('\ufef9', 'لأ')  # ﻹ -> لأ
    text = text.replace('\ufefa', 'لأ')  # ﻺ -> لأ
    text = text.replace('\ufefb', 'لإ')  # ﻻ -> لإ
    text = text.replace('\ufefc', 'لإ')  # ﻼ -> لإ
    
    # Remove any non-printable characters except Arabic, numbers, punctuation, and whitespace
    # Keep: Arabic (0600-06FF), Arabic Supplement (0750-077F), Arabic Extended (08A0-08FF)
    # Keep: Arabic Presentation Forms (FB50-FDFF, FE70-FEFF)
    # Keep: Basic Latin numbers and punctuation, spaces, newlines
    allowed_ranges = [
        (0x0020, 0x007E),  # Basic Latin (space to ~)
        (0x00A0, 0x00FF),  # Latin-1 Supplement
        (0x0600, 0x06FF),  # Arabic
        (0x0750, 0x077F),  # Arabic Supplement
        (0x08A0, 0x08FF),  # Arabic Extended-A
        (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
        (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
    ]
    
    def is_allowed_char(char):
        if char in '\n\r\t':
            return True
        code = ord(char)
        return any(start <= code <= end for start, end in allowed_ranges)
    
    text = ''.join(char for char in text if is_allowed_char(char))
    
    return text.strip()

def normalize_question(question: str) -> str:
    """Normalize question for cache lookup (remove extra spaces, normalize Arabic)"""
    text = question.strip().lower()
    # Normalize Arabic characters
    text = re.sub("[إأٱآا]", "ا", text)
    text = re.sub("ى", "ي", text)
    text = re.sub("ة", "ه", text)
    text = re.sub("ؤ", "ء", text)
    text = re.sub("ئ", "ء", text)
    # Remove diacritics
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text

def get_cache_key(question: str) -> str:
    """Generate a cache key from normalized question"""
    normalized = normalize_question(question)
    return hashlib.md5(normalized.encode('utf-8'), usedforsecurity=False).hexdigest()  # ✅ SECURE: marked as not for security

def fuzzy_match_greeting(text: str, known_greetings: List[str], threshold: float = 0.75) -> bool:
    """
    Fuzzy match text against known greetings to handle typos
    Uses similarity scoring - returns True if similarity >= threshold
    
    Args:
        text: Input text to check
        known_greetings: List of known greeting phrases
        threshold: Minimum similarity score (0-1) to consider a match
    
    Returns:
        True if text is similar enough to any known greeting
    """
    text_clean = text.strip().lower()
    
    # Remove common punctuation
    text_clean = re.sub(r'[!.,?،؟\s]+$', '', text_clean)
    
    for greeting in known_greetings:
        greeting_clean = greeting.strip().lower()
        
        # Calculate similarity ratio
        similarity = SequenceMatcher(None, text_clean, greeting_clean).ratio()
        
        if similarity >= threshold:
            return True
        
        # Also check if text is contained in greeting or vice versa (for partial matches)
        if len(text_clean) >= 3:  # Only for text with 3+ chars
            if text_clean in greeting_clean or greeting_clean in text_clean:
                # Additional check: must have at least 60% overlap
                overlap = min(len(text_clean), len(greeting_clean)) / max(len(text_clean), len(greeting_clean))
                if overlap >= 0.6:
                    return True
    
    return False

def is_greeting(text: str) -> bool:
    """Check if the text is a greeting - with typo tolerance via fuzzy matching"""
    text = text.strip()
    text_lower = text.lower()
    
    # Normalize Arabic text - remove extra spaces and normalize alef variations
    normalized = re.sub(r'\s+', ' ', text)  # Normalize spaces
    normalized_no_space = re.sub(r'\s+', '', text)  # Remove all spaces for comparison
    
    # Known greetings for fuzzy matching
    KNOWN_ARABIC_GREETINGS = [
        'أهلا', 'اهلا', 'مرحبا', 'مرحباً', 'هلا', 'اهلين', 'أهلين',
        'أهلا وسهلا', 'اهلا وسهلا', 'مرحبا بك', 'يا هلا',
        'السلام عليكم', 'سلام عليكم', 'سلام', 'صباح الخير', 'مساء الخير',
        'صباح النور', 'مساء النور', 'تحياتي', 'السلام', 'هلو', 'الو'
    ]
    
    KNOWN_ENGLISH_GREETINGS = [
        'hi', 'hello', 'hey', 'good morning', 'good evening', 
        'greetings', 'howdy', 'hi there', 'hello there'
    ]
    
    # If it contains question-related keywords, it's not a greeting
    # Use word boundaries to prevent false matches (e.g., "هل" shouldn't match in "اهلا")
    for keyword in NOT_GREETING_KEYWORDS:
        # Check if keyword appears as a separate word (with spaces or at boundaries)
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            return False
    
    # First: Try exact regex patterns (fast path)
    for pattern in GREETING_PATTERNS:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    
    # Second: Try fuzzy matching for typos (with high threshold for accuracy)
    # Use 0.75 threshold - allows ~25% character differences
    if fuzzy_match_greeting(text, KNOWN_ARABIC_GREETINGS, threshold=0.75):
        return True
    
    if fuzzy_match_greeting(text, KNOWN_ENGLISH_GREETINGS, threshold=0.75):
        return True
    
    # Third: Special patterns for common Arabic greeting typos
    # This catches more creative typos like احهلا, اهلاا, مرحببا
    typo_patterns = [
        r'^(ا|أ|إ|آ)+(ح|ه|خ|)*هلا+(ا|أ|)*$',  # أهلا variations with extra chars
        r'^مرح(ب|پ|ت)+(ا|و|)*$',                  # مرحبا with typing errors
        r'^(ه|ح|خ)لا+(و|)*$',                      # هلا variations
        r'^(س|ص)لام+(ع|)*$',                       # سلام variations
    ]
    
    for pattern in typo_patterns:
        if re.match(pattern, normalized, re.IGNORECASE):
            return True
    
    return False

def get_greeting_response(text: str) -> str:
    """Get appropriate greeting response based on the greeting type"""
    text = text.strip().lower()
    
    # Check for "السلام عليكم" / "سلام عليكم"
    if re.match(r'^(السلام عليكم|سلام عليكم)', text, re.IGNORECASE):
        return SALAM_RESPONSE
    
    # Default greeting response
    return GREETING_RESPONSE

def has_multiple_questions(text: str) -> bool:
    """Check if the text contains TOO MANY questions (more than 3)"""
    # Count question marks - allow up to 3 questions
    question_marks = text.count('?') + text.count('؟')
    if question_marks > 3:  # Changed from >= 3 to > 3 (allow 3, reject 4+)
        return True
    
    # Check for numbered lists with 4+ questions
    numbered_pattern = r'\d+[\.)\-]\s*\S+'
    numbered_items = re.findall(numbered_pattern, text)
    if len(numbered_items) > 3:  # Allow up to 3 numbered items
        return True
    
    # Check for multiple sentences ending with question marks - allow up to 3
    sentences = re.split(r'[.،,\n]', text)
    question_sentences = sum(1 for s in sentences if '?' in s or '؟' in s)
    if question_sentences > 3:  # Changed from >= 3 to > 3
        return True
    
    return False



MULTIPLE_QUESTIONS_RESPONSE = """⚠️ **يبدو أنك أرسلت أكثر من 3 أسئلة في رسالة واحدة.**

للحصول على إجابات دقيقة وشاملة، يرجى إرسال **حتى 3 أسئلة كحد أقصى في كل مرة**.

هذا يساعدني على:
• تقديم إجابة مفصلة لكل سؤال
• تجنب الأخطاء والتأخير
• توفير مراجع دقيقة للمواد القانونية

**يمكنك إرسال 1-3 أسئلة في رسالة واحدة، ثم إرسال الأسئلة الإضافية في رسالة منفصلة.**"""


class PerformanceCallback(BaseCallbackHandler):
    """Advanced callback for monitoring agent performance"""
    
    def __init__(self, log_callback: Callable[[str], None]):
        self.log_callback = log_callback
        self.start_time = None
        self.tool_calls = []
        self.step_count = 0
    
    def on_agent_action(self, action, **kwargs):
        self.step_count += 1
        self.tool_calls.append({
            'step': self.step_count,
            'tool': action.tool,
            'input': action.tool_input[:100] + "..." if len(str(action.tool_input)) > 100 else action.tool_input,
            'timestamp': time.time()
        })
        self.log_callback(f"🔧 Step {self.step_count}: Using {action.tool}")
    
    def on_agent_finish(self, finish, **kwargs):
        if self.start_time:
            duration = time.time() - self.start_time
            self.log_callback(f"✅ Agent completed in {duration:.2f}s with {self.step_count} steps")
            
            # Log tool usage summary
            tool_summary = {}
            for call in self.tool_calls:
                tool_summary[call['tool']] = tool_summary.get(call['tool'], 0) + 1
            
            if tool_summary:
                summary_str = ", ".join([f"{tool}({count})" for tool, count in tool_summary.items()])
                self.log_callback(f"📊 Tools used: {summary_str}")


class LangChainReActAgent:
    """
    Advanced LangChain ReAct Agent with enhanced reasoning and performance monitoring.
    Optimized for Gemini 1.5 Flash with intelligent tool usage and error handling.
    """

    @staticmethod
    def _detect_repetition(text: str, min_repeat_len: int = 20, max_repeats: int = 3) -> bool:
        """Detect if text contains excessive repetition (LLM degeneration).
        
        Checks if any substring of min_repeat_len+ chars repeats more than
        max_repeats times. This catches the common Gemini bug where it
        gets stuck repeating a phrase hundreds of times.
        """
        if not text or len(text) < min_repeat_len * 2:
            return False
        
        # Strategy 1: Check for repeated lines
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if len(lines) >= 5:
            from collections import Counter
            line_counts = Counter(lines)
            most_common_line, count = line_counts.most_common(1)[0]
            if count > max_repeats and len(most_common_line) >= min_repeat_len:
                return True
        
        # Strategy 2: Check for repeated bullet points
        bullets = re.findall(r'^\s*[\*\-•]\s*(.+)$', text, re.MULTILINE)
        if len(bullets) >= 5:
            from collections import Counter
            bullet_counts = Counter(bullets)
            most_common_bullet, count = bullet_counts.most_common(1)[0]
            if count > max_repeats:
                return True
        
        # Strategy 3: Check for repeated 5-word phrases (LLM looping/degeneration)
        words = text.split()
        if len(words) > 30:
            phrases = [" ".join(words[i:i+5]) for i in range(len(words) - 4)]
            from collections import Counter
            phrase_counts = Counter(phrases)
            most_common_phrase, count = phrase_counts.most_common(1)[0]
            if count >= 3:
                return True
        
        return False

    @staticmethod
    def _clean_repetitive_text(text: str) -> str:
        """Remove repeated lines/blocks and duplicate sentences from LLM output, keeping only unique content."""
        if not text:
            return text
        
        # 1. Clean at line level first
        lines = text.split('\n')
        seen_lines = set()
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            # Allow empty lines and short formatting lines
            if not stripped or len(stripped) < 10:
                cleaned_lines.append(line)
                continue
            
            if stripped in seen_lines:
                # Skip duplicate lines
                continue
            else:
                seen_lines.add(stripped)
                cleaned_lines.append(line)
        
        cleaned_text = '\n'.join(cleaned_lines).strip()
        
        # 2. Clean at sentence level within paragraphs
        paragraphs = cleaned_text.split('\n')
        cleaned_paragraphs = []
        
        for para in paragraphs:
            stripped_para = para.strip()
            if not stripped_para or len(stripped_para) < 20:
                cleaned_paragraphs.append(para)
                continue
            
            # Split by Arabic/English sentence boundaries, keeping delimiters
            sentences = re.split(r'([\.؟\?\!]\s+)', para)
            
            # Reconstruct sentences with their punctuation
            reconstructed_sentences = []
            i = 0
            while i < len(sentences):
                s = sentences[i].strip()
                punc = ""
                if i + 1 < len(sentences):
                    punc = sentences[i+1]
                
                if s:
                    reconstructed_sentences.append((s, punc))
                i += 2
            
            seen_sentences = set()
            unique_sentences = []
            for s, punc in reconstructed_sentences:
                # Normalize sentence for comparison (remove spaces/punctuation)
                norm = re.sub(r'[\s\.؟\?\!]+', '', s)
                if norm not in seen_sentences:
                    seen_sentences.add(norm)
                    unique_sentences.append(s + punc)
            
            cleaned_paragraphs.append("".join(unique_sentences))
            
        return '\n'.join(cleaned_paragraphs).strip()

    @staticmethod
    def _handle_parsing_error(error):
        """Extract answer from malformed LLM output.
        
        The LLM sometimes generates correct answers but forgets the
        'Final Answer:' prefix, causing a parsing error. This handler
        extracts the actual answer from the error string.
        """
        error_str = str(error)
        
        # 1. Extract raw LLM output from error string (if enclosed in backticks)
        raw = error_str
        if "Could not parse LLM output:" in error_str:
            try:
                raw = error_str.split("Could not parse LLM output: `", 1)[-1]
                if "For troubleshooting" in raw:
                    raw = raw.split("For troubleshooting")[0]
                raw = raw.rstrip("`").strip()
            except Exception:
                raw = error_str
                
        # 2. Check for "Final Answer" variations or Arabic equivalents in raw output
        # Pattern detects 'Final Answer', 'الإجابة النهائية', 'الجواب النهائي' (case-insensitive)
        # followed by optional punctuation/spaces/equals/dashes, and extracts everything after it.
        pattern = r'(?:Final\s*Answer|الإجابة\s*النهائية|الجواب\s*النهائي)[\s\:\-\—\=]*(.*)'
        match = re.search(pattern, raw, re.IGNORECASE | re.DOTALL)
        
        if match:
            answer = match.group(1).strip()
            if len(answer) > 50:
                answer = LangChainReActAgent._clean_repetitive_text(answer)
                return answer
                
        # 3. Fallback: if "Final Answer" was not found but the raw text is a substantial
        # response (not attempting to call a tool), return the cleaned raw content.
        if len(raw) > 100 and not raw.startswith("Action:"):
            cleaned_raw = LangChainReActAgent._clean_repetitive_text(raw)
            if len(cleaned_raw) > 50:
                print(f"[INFO] Recovered {len(cleaned_raw)} chars from unparsed LLM output (fallback)")
                return cleaned_raw
        
        return "عذراً، حدث خطأ في معالجة الإجابة. يرجى إعادة صياغة السؤال."

    def __init__(
        self,
        llm,
        tools: List[Tool],
        history_store,
        log_callback: Optional[Callable[[str], None]] = None,
        max_iterations: int = 10,  # Increased to give more iterations before timeout
        verbose: bool = True,
        enable_performance_monitoring: bool = True,
    ):
        """
        Initialize the Advanced LangChain ReAct Agent.
        
        Args:
            llm: LangChain LLM instance (optimized for Gemini 1.5 Flash)
            tools: List of LangChain Tool instances
            history_store: Chat history storage
            log_callback: Optional callback for logging
            max_iterations: Maximum iterations for the agent loop
            verbose: Whether to print verbose output
            enable_performance_monitoring: Enable advanced performance tracking
        """
        self.llm = llm
        self.tools = tools
        self.history_store = history_store
        self.log_callback = log_callback or (lambda msg: None)
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.enable_performance_monitoring = enable_performance_monitoring
        
        # Performance tracking
        self.performance_stats = {
            'total_questions': 0,
            'avg_response_time': 0,
            'tool_usage_stats': {},
            'error_count': 0
        }
        
        # Create the enhanced ReAct prompt
        self.prompt = PromptTemplate.from_template(REACT_PROMPT_TEMPLATE)
        
        # Create the ReAct agent using LangChain's official function
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt,
        )
        
        # Setup callbacks
        callbacks = []
        if self.enable_performance_monitoring:
            self.performance_callback = PerformanceCallback(self.log_callback)
            callbacks.append(self.performance_callback)
        
        # Create the enhanced AgentExecutor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=self.verbose,
            max_iterations=self.max_iterations,
            handle_parsing_errors=self._handle_parsing_error,
            return_intermediate_steps=True,
            callbacks=callbacks,
            max_execution_time=120,  # 2 minute timeout
        )
        
        self.log_callback("🚀 Advanced LangChain ReAct Agent initialized with Gemini 2.0 Flash Lite")

    def _get_conversation_context(self) -> str:
        """Get intelligent conversation history with extended context for long conversations (10+ exchanges)"""
        try:
            messages = self.history_store.messages
            if not messages or len(messages) == 0:
                return ""
            
            # Get last 20 messages (10 exchanges) for extended context
            recent = messages[-20:] if len(messages) >= 20 else messages
            
            # Extract key topics from recent conversation
            topics = set()
            legal_topics = {
                'فصل': 'الفصل التعسفي',
                'إجازة': 'الإجازات',
                'أجر': 'الأجور',
                'عقد': 'عقود العمل',
                'تأمين': 'التأمينات الاجتماعية',
                'سلامة': 'السلامة المهنية',
                'نقابة': 'النقابات العمالية',
                'تعويض': 'التعويضات',
                'دعوى': 'الدعاوى القضائية',
                'محكمة': 'الإجراءات القضائية'
            }
            
            context_parts = []
            for i, msg in enumerate(recent):
                if hasattr(msg, 'type'):
                    content = msg.content if isinstance(msg.content, str) else str(msg.content)
                    
                    # Extract topics from messages
                    for keyword, topic in legal_topics.items():
                        if keyword in content:
                            topics.add(topic)
                    
                    if msg.type == 'human':
                        context_parts.append(f"👤 المستخدم: {content}")
                    elif msg.type == 'ai':
                        # Smart truncation - keep key legal info
                        if len(content) > 400:
                            # Try to keep article numbers and key legal terms
                            if "المادة" in content:
                                # Keep first part with article info
                                content = content[:350] + "... [تم اختصار الإجابة]"
                            else:
                                content = content[:300] + "..."
                        context_parts.append(f"🤖 المساعد: {content}")
            
            if context_parts:
                # Add topic summary at the beginning
                context_header = "📚 سياق المحادثة السابقة (آخر 10 تبادلات):\n"
                if topics:
                    topics_str = "، ".join(sorted(topics))
                    context_header += f"🏷️ **المواضيع المطروحة**: {topics_str}\n\n"
                
                return context_header + "\n\n".join(context_parts) + "\n\n"
            return ""
        except Exception as e:
            print(f"[ERROR] Failed to get conversation context: {e}")
            return ""
    
    def _check_out_of_scope(self, question: str) -> Optional[str]:
        """
        Check if the question is completely out of scope (not related to Egyptian Labor Law).
        Returns a polite rejection response if out of scope, None otherwise.
        """
        question_lower = question.lower()
        
        # Keywords that indicate completely unrelated topics
        out_of_scope_keywords = [
            # Travel & Immigration
            'تأشيرة', 'فيزا', 'visa', 'سفر', 'جواز', 'passport', 'هجرة', 'immigration',
            # Finance & Markets (non-labor)
            'ذهب', 'gold', 'أسعار الذهب', 'دولار', 'بورصة', 'أسهم', 'عملات', 'بيتكوين', 'crypto',
            # Criminal Law
            'سرقة', 'قتل', 'مخدرات', 'جريمة', 'جنائي', 'سجن', 'حبس',
            # Real Estate (non-labor)
            'إيجار', 'عقار', 'شقة', 'أرض', 'بيع عقار', 'شراء منزل',
            # Medical/Health (non-labor context)
            'وصفة طبية', 'دواء', 'مستشفى', 'علاج مرض',
            # Education (non-labor)
            'مدرسة', 'جامعة', 'امتحان', 'شهادة دراسية',
            # Food & Recipes
            'طبخ', 'وصفة', 'recipe', 'أكل', 'مطعم',
            # Weather
            'طقس', 'weather', 'جو', 'درجة حرارة',
            # Sports & Entertainment
            'كرة قدم', 'مباراة', 'فيلم', 'مسلسل', 'أغنية',
            # Technology (non-labor)
            'تحميل', 'download', 'برنامج', 'تطبيق', 'هاتف', 'لابتوب',
            # Traffic & Driving
            'رخصة قيادة', 'مرور', 'سيارة', 'حادث سير',
            # Family Law (separate from labor)
            'زواج', 'طلاق', 'نفقة', 'حضانة', 'ميراث', 'إرث',
            # Religious
            'فتوى', 'حلال', 'حرام', 'صلاة', 'صيام',
        ]
        
        # Check if question contains out-of-scope keywords
        for keyword in out_of_scope_keywords:
            if keyword in question_lower:
                # Make sure it's not in a labor context
                labor_context_words = ['عمل', 'عامل', 'موظف', 'شركة', 'صاحب عمل', 'راتب', 'أجر', 'إجازة', 'عقد']
                has_labor_context = any(lc in question_lower for lc in labor_context_words)
                
                if not has_labor_context:
                    return """عذرًا، تخصصي محدود في **قانون العمل المصري** فقط.

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
        
        return None

    def ask(self, question: str) -> str:
        """
        Process a question using the ReAct agent.
        
        Args:
            question: User's question
            
        Returns:
            Agent's response
        """
        clean_question = question.strip()
        
        # 1. Check for greetings first (no API call needed) - BEFORE follow-up detection
        if is_greeting(clean_question):
            greeting_response = get_greeting_response(clean_question)
            self.log_callback("👋 Detected greeting - responding without API call")
            self.history_store.add_user_message(clean_question)
            self.history_store.add_ai_message(greeting_response)
            return greeting_response
        
        # 1.5. Check for completely out-of-scope questions (no API call needed)
        out_of_scope_response = self._check_out_of_scope(clean_question)
        if out_of_scope_response:
            self.log_callback("🚫 Detected out-of-scope question - responding without API call")
            self.history_store.add_user_message(clean_question)
            self.history_store.add_ai_message(out_of_scope_response)
            return out_of_scope_response
        
        # 2. Check for multiple questions (prevent quota issues)
        if has_multiple_questions(clean_question):
            self.log_callback("⚠️ Detected multiple questions - asking user to send one at a time")
            self.history_store.add_user_message(clean_question)
            self.history_store.add_ai_message(MULTIPLE_QUESTIONS_RESPONSE)
            return MULTIPLE_QUESTIONS_RESPONSE
        
        # 3. Detect file changes BEFORE cache check — so stale cached responses
        #    from old files don't get served when a new file is uploaded
        from src.retrieval.file_processor import get_file_processor
        file_processor = get_file_processor()
        current_files = file_processor.list_uploaded_files() if file_processor else []
        
        # Build a fingerprint of currently uploaded files (for cache key + rebuild check)
        current_file_hashes = sorted(f["hash"] for f in current_files) if current_files else []
        current_files_fingerprint = "|".join(current_file_hashes)
        
        # Check if tools need to be rebuilt (different file set)
        tools_need_rebuild = False
        if hasattr(self, '_last_files_fingerprint'):
            if current_files_fingerprint != self._last_files_fingerprint:
                tools_need_rebuild = True
                self.log_callback(f"🔄 Uploaded files changed, rebuilding tools...")
                # Clear response cache when files change to avoid stale answers
                RESPONSE_CACHE.clear()
                self.log_callback("🧹 Response cache cleared due to file change")
        else:
            self._last_files_fingerprint = current_files_fingerprint
        
        # 4. Check cache — key includes file fingerprint so same question
        #    about different files won't return stale cached answers
        cache_key = get_cache_key(clean_question + current_files_fingerprint)
        if cache_key in RESPONSE_CACHE:
            self.log_callback("📦 Found cached response - returning without API call")
            cached_response = RESPONSE_CACHE[cache_key]
            self.history_store.add_user_message(clean_question)
            self.history_store.add_ai_message(cached_response)
            return cached_response
        
        if tools_need_rebuild:
            # Rebuild tools with current file state
            from src.agents.langchain_react_agent import build_langchain_tools
            # Get retriever from the first tool (assuming it's still valid)
            retriever = None
            for tool in self.tools:
                if hasattr(tool.func, '__closure__') and tool.func.__closure__:
                    for cell in tool.func.__closure__:
                        if hasattr(cell.cell_contents, 'vectorstore'):
                            retriever = cell.cell_contents
                            break
                if retriever:
                    break
            
            if retriever:
                new_tools = build_langchain_tools(retriever, self.history_store, file_processor)
                self.tools = new_tools
                
                # Update the prompt template to reflect current available tools
                tool_names = [tool.name for tool in self.tools]
                updated_prompt = REACT_PROMPT_TEMPLATE.replace(
                    "[{tool_names}]", 
                    f"[{', '.join(tool_names)}]"
                )
                self.prompt = PromptTemplate.from_template(updated_prompt)
                
                # Rebuild agent with new tools
                self.agent = create_react_agent(
                    llm=self.llm,
                    tools=self.tools,
                    prompt=self.prompt,
                )
                
                # Rebuild agent executor with custom error handler
                callbacks = []
                if self.enable_performance_monitoring:
                    callbacks.append(self.performance_callback)

                self.agent_executor = AgentExecutor(
                    agent=self.agent,
                    tools=self.tools,
                    verbose=self.verbose,
                    max_iterations=self.max_iterations,
                    handle_parsing_errors=self._handle_parsing_error,
                    return_intermediate_steps=True,
                    callbacks=callbacks,
                    max_execution_time=180,
                )
                
                self.log_callback("✅ Tools and agent rebuilt successfully")
            
            self._last_files_fingerprint = current_files_fingerprint
        
        # 5. Get conversation context and let LangChain agent decide how to handle the question
        context = self._get_conversation_context()
        
        # Build the full input with context - let the agent decide if it's a follow-up
        if context:
            full_input = f"{context}السؤال الحالي: {clean_question}"
        else:
            full_input = clean_question
        
        self.log_callback("🤔 Processing question - letting LangChain agent decide the approach")
        
        self.log_callback(f"🤔 Processing question with ReAct agent...")
        
        try:
            # Invoke the agent executor with retry logic
            max_retries = 2
            retry_delay = 10  # Reduced from 60 to 10 seconds (Google's 429 is often temporary)
            
            for attempt in range(max_retries + 1):
                try:
                    result = self.agent_executor.invoke({"input": full_input})
                    
                    # Extract the final answer
                    response = result.get("output", "عذراً، لم أتمكن من معالجة السؤال.")
                    
                    # If the agent hit iteration limit, check intermediate steps
                    # for recovered answers from parsing errors
                    if "Agent stopped" in response or "iteration limit" in response:
                        steps = result.get("intermediate_steps", [])
                        recovered_answers = []
                        for action, observation in steps:
                            # Look for recovered content from _Exception handler
                            if (action.tool == "_Exception" 
                                and isinstance(observation, str) 
                                and len(observation) > 200
                                and "عذراً، حدث خطأ" not in observation):
                                # Clean repetitive content before considering it
                                cleaned = self._clean_repetitive_text(observation)
                                if len(cleaned) > 100 and not self._detect_repetition(cleaned):
                                    recovered_answers.append(cleaned)
                        
                        if recovered_answers:
                            # Use the longest recovered answer (most complete)
                            response = max(recovered_answers, key=len)
                            self.log_callback(f"✅ Recovered {len(response)} char answer from intermediate steps")
                    
                    # Final safety net: detect and clean any repetitive output
                    if self._detect_repetition(response):
                        self.log_callback("⚠️ Detected repetitive LLM output, cleaning...")
                        response = self._clean_repetitive_text(response)
                        if len(response) < 50:
                            response = "عذراً، حدث خطأ في إنشاء الإجابة (تكرار في المخرجات). يرجى إعادة صياغة السؤال."
                    
                    # Check if response is a valid short greeting (these are complete)
                    valid_short_greetings = [
                        "وعليكم السلام",
                        "وعليكم السلام ورحمة الله",
                        "وعليكم السلام ورحمة الله وبركاته",
                        "أهلاً",
                        "مرحباً",
                        "مرحبا"
                    ]
                    is_valid_short_greeting = any(greeting in response for greeting in valid_short_greetings)
                    
                    # Check if response is a valid out-of-scope rejection (these are complete)
                    valid_out_of_scope = [
                        "عذراً، تخصصي محدود في قانون العمل المصري فقط",
                        "تخصصي محدود في قانون العمل",
                        "خارج نطاق تخصصي",
                        "لا يقع ضمن تخصصي"
                    ]
                    is_valid_out_of_scope = any(phrase in response for phrase in valid_out_of_scope)
                    
                    # Check if response is complete (not cut off)
                    # Allow short but complete greetings and out-of-scope rejections
                    if not is_valid_short_greeting and not is_valid_out_of_scope and (len(response) < 50 or response.endswith("...")):
                        if attempt < max_retries:
                            self.log_callback(f"⚠️ Incomplete response detected, retrying in {retry_delay}s...")
                            time.sleep(retry_delay)
                            continue
                    
                    # Log intermediate steps if verbose
                    if self.verbose and "intermediate_steps" in result:
                        steps = result["intermediate_steps"]
                        self.log_callback(f"📝 Agent completed with {len(steps)} steps")
                        for i, (action, observation) in enumerate(steps):
                            self.log_callback(f"  Step {i+1}: {action.tool} -> {observation[:100]}...")
                    
                    # Save to history
                    self.history_store.add_user_message(clean_question)
                    self.history_store.add_ai_message(response)
                    
                    # Cache the response for future identical questions
                    RESPONSE_CACHE[cache_key] = response
                    self.log_callback(f"✅ Response generated and cached successfully")
                    
                    return response
                    
                except Exception as e:
                    if "429" in str(e) or "quota" in str(e).lower():
                        if attempt < max_retries:
                            self.log_callback(f"⏳ Quota exceeded, waiting {retry_delay}s before retry {attempt + 1}/{max_retries}...")
                            time.sleep(retry_delay)
                            continue
                        else:
                            # Final attempt failed, return quota message
                            quota_response = "عذراً، تم تجاوز حد الاستخدام المسموح للذكاء الاصطناعي. يرجى المحاولة مرة أخرى بعد دقيقة أو ترقية خطة الاستخدام."
                            self.history_store.add_user_message(clean_question)
                            self.history_store.add_ai_message(quota_response)
                            return quota_response
                    else:
                        # Non-quota error, re-raise
                        raise e
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.log_callback(f"❌ Error in ReAct agent: {e}")
            print(f"[ERROR] ReAct agent failed: {e}")
            print(error_details)
            
            # Check if it's a quota error
            if "429" in str(e) or "quota" in str(e).lower():
                error_response = "عذراً، تم تجاوز حد الاستخدام المسموح للذكاء الاصطناعي. يرجى المحاولة مرة أخرى بعد دقيقة أو ترقية خطة الاستخدام من Google AI Studio."
            else:
                error_response = "عذراً، حدث خطأ أثناء معالجة سؤالك. يرجى المحاولة مرة أخرى."
            
            # Save error to history
            self.history_store.add_user_message(clean_question)
            self.history_store.add_ai_message(error_response)
            
            return error_response


def build_langchain_tools(retriever, history_store, file_processor=None) -> List[Tool]:
    """
    Build LangChain Tool instances for the ReAct agent.
    
    Args:
        retriever: FAISS retriever
        history_store: Chat history store
        
    Returns:
        List of LangChain Tool instances
    """
    
    def _format_doc(doc, idx):
        """Format a document with metadata"""
        page = doc.metadata.get("page", "غير معروفة")
        article_number = doc.metadata.get("article_number", doc.metadata.get("article", "غير محددة"))
        book = doc.metadata.get("book", "")
        chapter = doc.metadata.get("chapter", "")
        source = doc.metadata.get("source", "قانون العمل 2025")
        snippet = doc.page_content.strip()
        
        # Normalize Arabic text for better display
        snippet = normalize_arabic_text(snippet)
        
        snippet = snippet[:600] + ("..." if len(snippet) > 600 else "")
        
        metadata_parts = [f"المقتطف {idx}"]
        metadata_parts.append(f"المادة: {article_number}")
        if book:
            metadata_parts.append(f"الكتاب: {book}")
        if chapter:
            metadata_parts.append(f"الباب: {chapter}")
        metadata_parts.append(f"المصدر: {source}")
        
        return f"{' — '.join(metadata_parts)}\n{snippet}"

    def expand_query_by_domain(query: str) -> List[str]:
        """Apply domain-specific query expansion rules for Egyptian Labor Law"""
        variants = [query]
        query_lower = query.lower()
        
        # 1. Unfair dismissal (فصل تعسفي -> إنهاء لسبب غير مشروع)
        if "تعسف" in query_lower:
            variants.append("إنهاء لسبب غير مشروع")
            variants.append("إنهاء لسبب غير مشروع تعويض")
            variants.append("أجر شهرين عن كل سنة")
            variants.append("المادة 165")
            
        # 2. Child labor minimum age (الحد الأدنى لسن -> يحظر تشغيل الأطفال)
        if "الحد الأدنى" in query_lower and "سن" in query_lower:
            variants.append("يحظر تشغيل الأطفال قبل")
            variants.append("سن خمس عشرة سنة أطفال")
            variants.append("المادة 64")
            
        # 3. Child labor maximum hours (الحد الأقصى لساعات -> ساعات عمل الطفل)
        if "الحد الأقصى" in query_lower and "ساعات" in query_lower:
            variants.append("يحظر تشغيل الطفل أكثر من ست ساعات")
            variants.append("ساعات عمل الطفل يوميا")
            variants.append("المادة 65")
            
        # 4. Maternity leave (إجازة وضع -> أربعة أشهر وضع)
        if "إجازة" in query_lower and ("وضع" in query_lower or "أمومة" in query_lower or "حامل" in query_lower):
            variants.append("أربعة أشهر وضع")
            variants.append("إجازة العاملة الحامل")
            variants.append("المادة 54")
            
        return list(dict.fromkeys(variants))

    def law_lookup(question: str) -> str:
        """Retrieve relevant documents for the question using dynamic retrieval with query expansion"""
        try:
            # Check if this is a compound question
            sub_queries = detect_compound_question(question)
            
            if len(sub_queries) > 1:
                # Use query expansion with domain knowledge for compound questions
                print(f"[INFO] Using query expansion with domain knowledge for compound question ({len(sub_queries)} parts)")
                
                all_docs = []
                seen_content = set()  # Avoid duplicates
                
                for sub_query in sub_queries:
                    print(f"[INFO] Processing sub-query: {sub_query}")
                    expanded_queries = expand_query_by_domain(sub_query)
                    
                    # Retrieve documents for all query variants
                    for query_variant in expanded_queries:
                        try:
                            # Retrieve 15 documents to account for duplicate chunks in vector store
                            temp_retriever = retriever.vectorstore.as_retriever(search_kwargs={"k": 15})
                            docs = temp_retriever.invoke(query_variant)
                            
                            # Add unique documents
                            for doc in docs:
                                content_hash = hash(doc.page_content[:200])  # Hash first 200 chars
                                if content_hash not in seen_content:
                                    seen_content.add(content_hash)
                                    all_docs.append(doc)
                        except Exception as e:
                            print(f"[ERROR] Failed to retrieve for variant '{query_variant[:50]}...': {e}")
                            continue
                    
                    print(f"[INFO] Retrieved {len(all_docs)} unique docs so far")
                
                if not all_docs:
                    return "لم يتم العثور على معلومات ذات صلة في قاعدة بيانات قانون العمل المصري."
                
                # Format results
                print(f"[SUCCESS] Total unique documents retrieved: {len(all_docs)}")
                
                results = []
                for idx, doc in enumerate(all_docs[:8], 1):  # Show up to 8 docs for compound questions
                    content = doc.page_content.strip()
                    
                    # Normalize Arabic text for better display
                    content = normalize_arabic_text(content)
                    
                    # Extract article number if available
                    article_match = re.search(r'المادة\s*(\d+)', content)
                    article_num = article_match.group(1) if article_match else None
                    
                    # Truncate long content
                    if len(content) > 600:
                        content = content[:600] + "..."
                    
                    # Format with article number if available
                    if article_num:
                        results.append(f"**المادة {article_num}:**\n{content}")
                    else:
                        results.append(f"**مقطع {idx}:**\n{content}")
                    
                    results.append("")  # Empty line between documents
                
                return "\n".join(results)
            
            # Single question - use regular dynamic retrieval with query expansion
            from src.retrieval.dynamic_retrieval import get_dynamic_k
            
            # Get optimal number of documents for this question
            optimal_k = get_dynamic_k(question)
            
            # Expand the single query
            expanded_queries = expand_query_by_domain(question)
            
            # Retrieve documents for all query variants
            all_docs = []
            seen_content = set()
            for q_var in expanded_queries:
                # Retrieve 15 documents to account for duplicate chunks in vector store
                temp_retriever = retriever.vectorstore.as_retriever(search_kwargs={"k": 15})
                try:
                    docs = temp_retriever.invoke(q_var)
                    all_docs.extend(docs)
                except Exception as e:
                    print(f"[WARNING] Failed to retrieve for variant '{q_var[:50]}...': {e}")
            
            if not all_docs:
                return "لم يتم العثور على مواد مرتبطة بالسؤال المطروح."
            
            # Deduplicate documents based on content
            unique_docs = []
            for doc in all_docs:
                # Normalize spaces/punctuation to identify identical text chunks
                norm_content = re.sub(r'[\s\.؟\?\!]+', '', doc.page_content[:200])
                if norm_content not in seen_content:
                    seen_content.add(norm_content)
                    unique_docs.append(doc)
                    if len(unique_docs) == optimal_k:
                        break
            
            print(f"[SUCCESS] law_lookup retrieved {len(all_docs)} docs, deduplicated to {len(unique_docs)} unique docs (dynamic optimal: {optimal_k})")
            return "\n\n".join(_format_doc(doc, idx + 1) for idx, doc in enumerate(unique_docs))
            
        except Exception as e:
            print(f"[ERROR] law_lookup failed: {e}")
            # Fallback to original retriever
            try:
                docs = retriever.invoke(question)
                if docs:
                    print(f"[FALLBACK] Using original retriever: {len(docs)} docs")
                    return "\n\n".join(_format_doc(doc, idx + 1) for idx, doc in enumerate(docs))
            except:
                pass
            return f"حدث خطأ أثناء البحث: {str(e)}"

    def article_reference(question: str) -> str:
        """Get article references for the question using dynamic retrieval"""
        try:
            # Import dynamic retrieval
            from src.retrieval.dynamic_retrieval import get_dynamic_k
            
            # Get optimal number of documents (but limit to 4 for references)
            optimal_k = min(get_dynamic_k(question), 4)  # References don't need as many docs
            
            # Retrieve 15 documents to account for duplicate chunks in vector store
            dynamic_retriever = retriever.vectorstore.as_retriever(search_kwargs={"k": 15})
            docs = dynamic_retriever.invoke(question)
            
            if not docs:
                return "لا توجد مراجع متاحة لهذا السؤال."
            
            # Deduplicate documents based on content
            unique_docs = []
            seen_content = set()
            for doc in docs:
                norm_content = re.sub(r'[\s\.؟\?\!]+', '', doc.page_content[:200])
                if norm_content not in seen_content:
                    seen_content.add(norm_content)
                    unique_docs.append(doc)
                    if len(unique_docs) == optimal_k:
                        break
            
            references = []
            for doc in unique_docs:
                article_number = doc.metadata.get("article_number", doc.metadata.get("article", "غير محددة"))
                book = doc.metadata.get("book", "")
                chapter = doc.metadata.get("chapter", "")
                source = doc.metadata.get("source", "قانون العمل 2025")
                
                ref_parts = [f"المادة {article_number}"]
                if book:
                    ref_parts.append(f"({book})")
                if chapter:
                    ref_parts.append(f"- {chapter}")
                ref_parts.append(f"- المصدر: {source}")
                
                references.append(" ".join(ref_parts))
            
            unique_refs = list(dict.fromkeys(references))[:8]
            return "\n".join(unique_refs)
        except Exception as e:
            print(f"[ERROR] article_reference failed: {e}")
            return f"حدث خطأ: {str(e)}"

    def memory_snapshot(query: str) -> str:
        """Get conversation history snapshot with extended context for long conversations (6 exchanges)"""
        try:
            messages = history_store.messages[-12:]  # Get last 12 messages (6 exchanges) for extended context
            if not messages:
                return "لا توجد محادثات سابقة للاطلاع عليها."
            
            # Extract key topics and themes from conversation
            legal_topics = {
                'فصل': 'الفصل التعسفي',
                'إجازة': 'الإجازات', 
                'أجر': 'الأجور',
                'عقد': 'عقود العمل',
                'تأمين': 'التأمينات الاجتماعية',
                'سلامة': 'السلامة المهنية',
                'نقابة': 'النقابات العمالية',
                'تعويض': 'التعويضات',
                'دعوى': 'الدعاوى القضائية',
                'محكمة': 'الإجراءات القضائية',
                'مدة': 'المدد الزمنية',
                'إجراء': 'الإجراءات القانونية'
            }
            
            topics_mentioned = set()
            articles_mentioned = set()
            lines = []
            rejection_phrases = [
                "عذراً، أنا متخصص في قانون العمل المصري فقط",
                "خارج نطاق تخصصي",
                "لا يمكنني مساعدتك"
            ]
            
            for i, msg in enumerate(messages):
                role = "المستخدم" if msg.type == "human" else "المساعد"
                text = msg.content.strip() if isinstance(msg.content, str) else str(msg.content)
                
                # Skip rejection messages
                if msg.type != "human" and any(phrase in text for phrase in rejection_phrases):
                    if i > 0 and messages[i-1].type == "human":
                        if lines and lines[-1].startswith("المستخدم:"):
                            lines.pop()
                    continue
                
                # Extract topics and articles from text
                for keyword, topic in legal_topics.items():
                    if keyword in text:
                        topics_mentioned.add(topic)
                
                # Extract article numbers
                article_matches = re.findall(r'المادة\s*(\d+)', text)
                for article in article_matches:
                    articles_mentioned.add(f"المادة {article}")
                
                # Format message with appropriate length
                if msg.type == "human":
                    if len(text) > 200:
                        text = text[:200] + "..."
                else:
                    # Keep more of AI responses for context (up to 800 chars)
                    if len(text) > 800:
                        # Try to keep important legal information
                        if "المادة" in text:
                            text = text[:750] + "... [تم اختصار الإجابة]"
                        else:
                            text = text[:600] + "..."
                
                lines.append(f"{role}: {text}")
            
            if not lines:
                return "لا توجد محادثات سابقة للاطلاع عليها."
            
            # Build enhanced context with topic summary
            context_parts = ["📚 **سياق المحادثة السابقة للإجابة على سؤال المتابعة:**\n"]
            
            if topics_mentioned:
                topics_str = "، ".join(sorted(topics_mentioned))
                context_parts.append(f"🏷️ **المواضيع المطروحة**: {topics_str}")
            
            if articles_mentioned:
                articles_str = "، ".join(sorted(articles_mentioned))
                context_parts.append(f"📋 **المواد المذكورة**: {articles_str}")
            
            if topics_mentioned or articles_mentioned:
                context_parts.append("")  # Empty line
            
            context_parts.append("💬 **تفاصيل المحادثة:**")
            context_parts.extend(lines)
            
            # Add guidance for follow-up
            context_parts.append(f"\n🎯 **إرشاد**: السؤال الحالي '{query}' يبدو مرتبطاً بالمحادثة السابقة. استخدم هذا السياق للإجابة.")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            print(f"[ERROR] memory_snapshot failed: {e}")
            return "لا توجد محادثات سابقة."

    def detect_compound_question(question: str) -> list:
        """
        Detect if question has multiple parts and split into sub-queries.
        Returns list of sub-queries, or [original_question] if not compound.
        Works even when agent reformulates questions without question words.
        """
        # Patterns that indicate compound questions
        compound_indicators = [
            r'،\s*و(?:ما|كم|هل|ماذا|أين|متى|كيف)',  # و + question word after comma
            r'\s+و(?:ما|كم|هل|ماذا|أين|متى|كيف)\s+',  # و + question word
            r'؟.*(?:و|كذلك|أيضاً|بالإضافة).*؟',  # Multiple question marks with connectors
            r'،\s*(?:ساعات|أيام|سن|عمر|مدة|فترة|حقوق|واجبات)',  # Comma + key legal terms (agent reformulation)
        ]
        
        # Check if it's a compound question
        is_compound = any(re.search(pattern, question) for pattern in compound_indicators)
        
        if not is_compound:
            return [question]
        
        # Try to split the question intelligently
        sub_queries = []
        
        # Split by question marks
        parts = re.split(r'[؟\?]', question)
        parts = [p.strip() for p in parts if p.strip()]
        
        if len(parts) >= 2:
            # We have multiple questions
            for part in parts:
                # Clean up connectors at the beginning
                part = re.sub(r'^(و|كذلك|أيضاً|بالإضافة إلى ذلك|كما)\s+', '', part)
                if len(part) > 10:  # Minimum length for a valid question
                    sub_queries.append(part + '؟')
        
        # If splitting by question marks didn't work, try splitting by "و" + question word
        if len(sub_queries) < 2:
            parts = re.split(r'،?\s*و(?=(?:ما|كم|هل|ماذا|أين|متى|كيف)\s)', question)
            if len(parts) >= 2:
                sub_queries = [p.strip() for p in parts if len(p.strip()) > 10]
        
        # If still no split, try splitting by comma + key legal terms (for agent reformulations)
        if len(sub_queries) < 2:
            # Pattern: "topic1، topic2" where topics are legal concepts
            parts = re.split(r'،\s*(?=(?:ساعات|أيام|سن|عمر|مدة|فترة|حقوق|واجبات|الحد))', question)
            if len(parts) >= 2:
                sub_queries = []
                for part in parts:
                    part = part.strip()
                    if len(part) > 10:
                        # Add context if missing
                        if not any(word in part for word in ['ما', 'كم', 'هل', 'الحد', 'تشغيل', 'عمل']):
                            # This is likely a fragment, try to add context
                            if 'ساعات' in part and 'عمل' not in part:
                                part = 'ساعات عمل ' + part
                        sub_queries.append(part)
                
                print(f"[INFO] Split by comma + legal terms: {sub_queries}")
        
        # Return original if we couldn't split properly
        if len(sub_queries) < 2:
            return [question]
        
        return sub_queries[:3]  # Maximum 3 sub-queries


    def smart_search(question: str) -> str:
        """Intelligently search in uploaded files first, then legal database if needed"""
        if not file_processor:
            # No file processor, go directly to legal search
            return law_lookup(question)
        
        uploaded_files = file_processor.list_uploaded_files()
        if not uploaded_files:
            # No uploaded files, go directly to legal search
            return law_lookup(question)
        
        # Check if this question is about the uploaded file using the file processor's logic
        file_hash = uploaded_files[0]["hash"]  # Assume single file for now
        is_about_file = file_processor.is_question_about_file(question, file_hash)
        
        if not is_about_file:
            # This is the first question NOT about the uploaded file
            # Remove all uploaded files permanently and switch to legal database
            print(f"[INFO] Question not about uploaded file - removing files and switching to legal database")
            
            # Remove all uploaded files
            removed_files = []
            for file_info in uploaded_files:
                filename = file_info["filename"]
                file_hash = file_info["hash"]
                if file_processor.remove_file(file_hash):
                    removed_files.append(filename)
            
            # Search in legal database
            legal_results = law_lookup(question)
            
            # Return response with notification about file removal
            if removed_files:
                file_list = "، ".join(removed_files)
                return f"""🔄 **تم التبديل إلى قاعدة بيانات قانون العمل المصري**

تم حذف الملف المرفوع ({file_list}) من الذاكرة لأن سؤالك لا يتعلق بمحتواه.

🔍 **الإجابة من قاعدة بيانات قانون العمل المصري:**

{legal_results}"""
            else:
                return f"🔍 **الإجابة من قاعدة بيانات قانون العمل المصري:**\n\n{legal_results}"
        
        # Question is about the file - search in uploaded files
        file_results = []
        found_in_files = False
        
        for file_info in uploaded_files:
            file_hash = file_info["hash"]
            filename = file_info["filename"]
            
            try:
                # Search in this file - retrieve MORE chunks for comprehensive content
                docs = file_processor.search_in_file(file_hash, question, k=5)  # Increased from 3 to 5
                
                if docs:
                    # Check if this is a meta-question about the file/image itself
                    # (e.g., "اشرح الصورة", "ملخص الملف") - skip word overlap check
                    meta_keywords = ['الصورة', 'صورة', 'الملف', 'المستند', 'الوثيقة', 'المرفق',
                                     'اشرح', 'لخص', 'ملخص', 'محتوى', 'رفعته', 'المرفوع', 'المرفوعة',
                                     'تفاصيل', 'ايه', 'كل', 'حاجه']
                    is_meta_question = any(kw in question for kw in meta_keywords)
                    
                    if is_meta_question:
                        # For meta-questions, use all FAISS results directly
                        relevant_docs = docs
                    else:
                        # For specific content questions, check word overlap
                        relevant_docs = []
                        for doc in docs:
                            question_words = set(question.lower().split())
                            doc_words = set(doc.page_content.lower().split())
                            
                            # Remove common Arabic stop words for better matching
                            stop_words = {'في', 'من', 'إلى', 'على', 'عن', 'مع', 'هذا', 'هذه', 'التي', 'الذي', 'ما', 'هل', 'كيف', 'متى', 'أين', 'لماذا'}
                            question_words = question_words - stop_words
                            
                            # Check for word overlap (at least 20% of question words should appear in document)
                            if len(question_words) > 0:
                                overlap = len(question_words.intersection(doc_words)) / len(question_words)
                                if overlap >= 0.2:  # Reduced threshold for file content
                                    relevant_docs.append(doc)
                    
                    if relevant_docs:
                        found_in_files = True
                        file_results.append(f"📄 **من الملف: {filename}**")
                        # For OCR files, show full content. For others, limit to 800 chars.
                        is_ocr = any(d.metadata.get("ocr", False) for d in relevant_docs)
                        for idx, doc in enumerate(relevant_docs[:4], 1):
                            content = doc.page_content.strip()
                            if not is_ocr and len(content) > 800:
                                content = content[:800] + "..."
                            
                            # Add metadata if available
                            metadata_parts = []
                            if doc.metadata.get("page"):
                                metadata_parts.append(f"الصفحة: {doc.metadata['page']}")
                            if doc.metadata.get("sheet"):
                                metadata_parts.append(f"الورقة: {doc.metadata['sheet']}")
                            
                            metadata_str = f" ({', '.join(metadata_parts)})" if metadata_parts else ""
                            file_results.append(f"المقطع {idx}{metadata_str}:\n{content}")
                        
                        file_results.append("")  # Empty line between files
            
            except Exception as e:
                print(f"[ERROR] Failed to search in file {filename}: {e}")
                continue
        
        # If we found relevant information in files, return it with source attribution
        if found_in_files:
            file_content = "\n".join(file_results)
            
            # Check if any of the documents were OCR-extracted (from images/scanned PDFs)
            has_ocr = any(
                doc.metadata.get("ocr", False) 
                for file_info in uploaded_files 
                for doc in file_processor.uploaded_files.get(file_info["hash"], {}).get("documents", [])
            )
            
            ocr_disclaimer = ""
            if has_ocr:
                ocr_disclaimer = "\n\n⚠️ **ملاحظة**: تم استخراج النص من الصورة تلقائياً باستخدام تقنية OCR. قد تحتوي على أخطاء في التواريخ أو الأرقام أو ترتيب المقاطع. يُرجى التحقق من المعلومات الحساسة يدوياً."
            
            return f"🔍 **هذه الإجابة مأخوذة من الملف الذي رفعته:**\n\n{file_content}{ocr_disclaimer}"
        
        # If no relevant information found in files, search the legal database
        print(f"[INFO] No relevant information found in uploaded files, searching legal database...")
        legal_results = law_lookup(question)
        
        return f"🔍 **لم أجد معلومات ذات صلة في الملف المرفوع، الإجابة من قاعدة بيانات قانون العمل المصري:**\n\n{legal_results}"

    def uploaded_file_search(question: str) -> str:
        """Search specifically in uploaded files (for explicit file queries)"""
        if not file_processor:
            return "لا توجد ملفات مرفوعة للبحث فيها."
        
        uploaded_files = file_processor.list_uploaded_files()
        if not uploaded_files:
            return "لا توجد ملفات مرفوعة للبحث فيها."
        
        results = []
        for file_info in uploaded_files:
            file_hash = file_info["hash"]
            filename = file_info["filename"]
            
            try:
                # Search in this file - retrieve MORE chunks for comprehensive content
                docs = file_processor.search_in_file(file_hash, question, k=5)  # Increased from 3 to 5
                
                if docs:
                    results.append(f"📄 **من الملف: {filename}**")
                    # For OCR files, show full content. For others, limit to 800 chars.
                    is_ocr = any(d.metadata.get("ocr", False) for d in docs)
                    for idx, doc in enumerate(docs, 1):
                        content = doc.page_content.strip()
                        if not is_ocr and len(content) > 800:
                            content = content[:800] + "..."
                        
                        # Add metadata if available
                        metadata_parts = []
                        if doc.metadata.get("page"):
                            metadata_parts.append(f"الصفحة: {doc.metadata['page']}")
                        if doc.metadata.get("sheet"):
                            metadata_parts.append(f"الورقة: {doc.metadata['sheet']}")
                        
                        metadata_str = f" ({', '.join(metadata_parts)})" if metadata_parts else ""
                        results.append(f"المقطع {idx}{metadata_str}:\n{content}")
                    
                    results.append("")  # Empty line between files
            
            except Exception as e:
                print(f"[ERROR] Failed to search in file {filename}: {e}")
                continue
        
        if results:
            result_text = "\n".join(results)
            
            # Check if any of the documents were OCR-extracted
            has_ocr = any(
                doc.metadata.get("ocr", False)
                for file_info in uploaded_files
                for doc in file_processor.uploaded_files.get(file_info["hash"], {}).get("documents", [])
            )
            
            ocr_disclaimer = ""
            if has_ocr:
                ocr_disclaimer = "\n\n⚠️ **ملاحظة**: تم استخراج النص من الصورة تلقائياً باستخدام تقنية OCR. قد تحتوي على أخطاء في التواريخ أو الأرقام أو ترتيب المقاطع. يُرجى التحقق من المعلومات الحساسة يدوياً."
            
            return result_text + ocr_disclaimer
        else:
            return "لم يتم العثور على معلومات ذات صلة في الملفات المرفوعة."

    # Create LangChain Tool instances
    tools = [
        Tool(
            name="conversation_history",
            func=memory_snapshot,
            description="""📚 **أداة المحادثة السابقة - استخدمها أولاً لأسئلة المتابعة**

**متى تستخدم هذه الأداة (أولوية عالية):**
✅ عندما يسأل المستخدم عن تفاصيل إضافية لموضوع تم مناقشته
✅ عندما يطلب توضيحاً أو شرحاً أعمق (كيف، متى، ما المدة، ما الإجراءات)
✅ عندما يسأل عن جوانب أخرى لنفس الموضوع القانوني
✅ عندما يستخدم كلمات مثل: "أيضاً"، "كذلك"، "وماذا عن"، "بالإضافة"
✅ عندما يشير السؤال ضمنياً لموضوع سابق (مثل: "المدة" بعد مناقشة إجراءات)

**ما تقدمه الأداة:**
- ملخص المواضيع المطروحة في المحادثة
- المواد القانونية المذكورة سابقاً
- تفاصيل المحادثة الكاملة للسياق

**مثال:** إذا تم مناقشة "الفصل التعسفي" وسأل عن "المدة لرفع الدعوى" → استخدم هذه الأداة أولاً""",
        ),
        Tool(
            name="article_reference",
            func=article_reference,
            description="اعرض قائمة مختصرة بأرقام المواد ذات الصلة من قانون العمل المصري. استخدم للأسئلة الجديدة أو بعد conversation_history إذا احتجت مراجع إضافية.",
        ),
    ]
    
    # Add smart search or regular legal search based on file processor availability
    if file_processor and file_processor.list_uploaded_files():
        # If files are uploaded, use smart search that checks files first
        tools.insert(1, Tool(
            name="smart_search",
            func=smart_search,
            description="""🧠 **البحث الذكي - الأداة الأساسية عند وجود ملفات مرفوعة**

هذه الأداة تبحث بذكاء في:
1. الملفات والصور المرفوعة أولاً (النص المستخرج من الصور بتقنية OCR)
2. قاعدة بيانات قانون العمل المصري (إذا لم تجد في الملفات)

**استخدم هذه الأداة فوراً عندما يسأل المستخدم عن صورة أو ملف رفعه!**
مثل: 'اشرح الصورة'، 'ما محتوى الملف'، 'لخص المستند'، 'ايه تفاصيلها'، 'اشرحلي كل حاجه'

⚠️ لا تستخدم legal_search أو conversation_history إذا كان السؤال عن ملف/صورة مرفوعة!

📋 **عند شرح محتوى ملف/صورة:**
- اقرأ النص المستخرج بالكامل بعناية
- اشرح المحتوى بالتفصيل الكامل - لا تكتفي بوصف عام
- استخرج جميع المعلومات: أسماء، تواريخ، أرقام، مواد قانونية، قرارات، بنود
- إذا كان حكم قضائي: اذكر رقم الدعوى، المحكمة، القضاة، الأطراف، موضوع الدعوى، الحكم، المواد المطبقة، التعويضات
- إذا كان عقد: اذكر الأطراف، الشروط، المدة، الأجر، جميع البنود المهمة
- استخدم النص المستخرج بالكامل لتقديم شرح شامل ومفصل""",
        ))
        
        # Add explicit file search for when user specifically asks about files
        tools.append(
            Tool(
                name="uploaded_file_search",
                func=uploaded_file_search,
                description="""📄 البحث المباشر في الملفات المرفوعة فقط.

استخدم هذه الأداة فقط عندما:
- يذكر المستخدم صراحة 'الملف' أو 'المستند' أو 'الوثيقة' أو 'الصورة'
- يطلب عرض محتوى الملف أو شرح الصورة
- يريد معلومات محددة من الملف المرفوع
- يسأل 'ايه تفاصيلها' أو 'اشرحلي كل حاجه' بعد رفع ملف

📋 **عند شرح المحتوى:**
- اقرأ النص المستخرج بالكامل بعناية
- قدم شرح مفصل وشامل - لا تكتفي بوصف عام
- استخرج جميع المعلومات المهمة من النص
- إذا كان حكم قضائي: اذكر كل التفاصيل (رقم الدعوى، المحكمة، القضاة، الأطراف، الموضوع، الحكم، المواد، التعويضات)
- إذا كان عقد: اذكر جميع البنود والشروط بالتفصيل

لا تستخدم هذه الأداة للأسئلة العامة - استخدم smart_search بدلاً منها.""",
            )
        )
    else:
        # No files uploaded, use regular legal search
        tools.insert(1, Tool(
            name="legal_search",
            func=law_lookup,
            description="""🔍 **البحث في قانون العمل المصري**

**متى تستخدم:**
- للأسئلة الجديدة التي تطرح موضوعاً قانونياً جديداً
- بعد استخدام conversation_history إذا احتجت معلومات إضافية
- عندما لا يوجد سياق سابق مرتبط بالسؤال

**لا تستخدم إذا:**
❌ السؤال مرتبط بمحادثة سابقة (استخدم conversation_history أولاً)
❌ السؤال يطلب توضيحاً لشيء تم ذكره (استخدم conversation_history)""",
        ))
    
    return tools
