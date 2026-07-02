"""
Legal Accuracy Validator - Validates AI answers against expert ground truth

This module validates AI-generated legal answers by comparing them against
expert-verified ground truth answers from Egyptian Labour Law.

Usage:
    from eval.legal_accuracy_validator import validate_ai_answer
    
    result = validate_ai_answer("ما هي مدة الإجازة السنوية؟", ai_response)
    print(f"Legally Accurate: {result['legally_accurate']}")
    print(f"Accuracy Score: {result['accuracy_score']:.1%}")
"""

import json
import re
import difflib
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class LegalAccuracyValidator:
    """Validates AI answers against expert-verified ground truth."""
    
    def __init__(self, ground_truth_path: str = None):
        """
        Initialize the validator with ground truth data.
        
        Args:
            ground_truth_path: Path to ground truth JSON file.
                              Defaults to eval/ground_truth_legal_qa.json
        """
        if ground_truth_path is None:
            ground_truth_path = Path(__file__).parent / "ground_truth_legal_qa.json"
        
        self.ground_truth = self._load_ground_truth(ground_truth_path)
        self.total_evaluations = 0
        self.passed_evaluations = 0
    
    def _load_ground_truth(self, path: str | Path) -> List[Dict]:
        """Load expert-verified Q&A pairs."""
        gt_path = Path(path)
        if not gt_path.exists():
            raise FileNotFoundError(
                f"Ground truth file not found: {path}\n"
                f"Please create it at: {gt_path}"
            )
        return json.loads(gt_path.read_text(encoding='utf-8'))
    
    def validate_answer(self, question: str, ai_answer: str) -> Dict:
        """
        Validate AI answer against ground truth.
        
        Args:
            question: The question asked
            ai_answer: The AI-generated answer
        
        Returns:
            Dict containing:
                - legally_accurate: bool (True if score >= 85%)
                - accuracy_score: float (0.0 to 1.0)
                - checks: dict of individual check results
                - explanation: str describing the results
                - missing_facts: list of missing key facts
                - wrong_info: list of incorrect information found
        """
        self.total_evaluations += 1
        
        # Find matching ground truth
        gt = self._find_ground_truth(question)
        if not gt:
            return {
                'legally_accurate': None,
                'accuracy_score': 0.0,
                'explanation': '⚠️ لا يوجد ground truth متاح لهذا السؤال',
                'gt_id': None,
                'question': question
            }
        
        results = {
            'question': question,
            'gt_id': gt['id'],
            'legally_accurate': True,
            'accuracy_score': 0.0,
            'checks': {},
            'missing_facts': [],
            'wrong_info': []
        }
        
        # Check 1: Key Facts Coverage (40%)
        facts_score, missing_facts = self._check_key_facts(ai_answer, gt['key_facts'])
        results['checks']['key_facts'] = {
            'score': facts_score,
            'missing': missing_facts,
            'weight': 0.40,
            'description': 'تغطية الحقائق الأساسية'
        }
        results['missing_facts'] = missing_facts
        
        # Check 2: Article Reference Accuracy (25%)
        article_score, article_details = self._check_article_reference(
            ai_answer, gt['article_reference']
        )
        results['checks']['article_accuracy'] = {
            'score': article_score,
            'details': article_details,
            'weight': 0.25,
            'description': 'دقة الإشارة للمواد'
        }
        
        # Check 3: Wrong Answer Detection (25%)
        wrong_score, wrong_found = self._check_wrong_answers(
            ai_answer, gt['wrong_answers']
        )
        results['checks']['no_wrong_info'] = {
            'score': wrong_score,
            'wrong_info_found': wrong_found,
            'weight': 0.25,
            'description': 'عدم وجود معلومات خاطئة'
        }
        results['wrong_info'] = wrong_found
        
        # Check 4: Semantic Similarity (10%)
        similarity_score = self._semantic_similarity(
            ai_answer, gt['correct_answer']
        )
        results['checks']['semantic_similarity'] = {
            'score': similarity_score,
            'weight': 0.10,
            'description': 'التشابه الدلالي مع الإجابة الصحيحة'
        }
        
        # Calculate overall accuracy
        total_score = 0.0
        for check_name, check_data in results['checks'].items():
            total_score += check_data['score'] * check_data['weight']
        
        results['accuracy_score'] = round(total_score, 3)
        results['legally_accurate'] = total_score >= 0.85  # 85% threshold
        
        if results['legally_accurate']:
            self.passed_evaluations += 1
        
        # Generate explanation
        results['explanation'] = self._generate_explanation(results, total_score)
        
        return results
    
    def _find_ground_truth(self, question: str) -> Optional[Dict]:
        """Find matching ground truth entry for a question."""
        question_lower = question.lower().strip()
        
        # Exact match first
        for gt in self.ground_truth:
            if gt['question'].lower().strip() == question_lower:
                return gt
        
        # Fuzzy match if exact not found (similarity > 85%)
        best_match = None
        best_score = 0.0
        
        for gt in self.ground_truth:
            similarity = difflib.SequenceMatcher(
                None, question_lower, gt['question'].lower()
            ).ratio()
            if similarity > best_score:
                best_score = similarity
                best_match = gt
        
        if best_score > 0.85:
            return best_match
        
        return None
    
    # ── Arabic ↔ digit equivalence maps ─────────────────────────────
    _ARABIC_TO_DIGIT = {
        'واحد': '1', 'واحدة': '1',
        'اثنين': '2', 'اثنان': '2', 'اثنتين': '2',
        'ثلاث': '3', 'ثلاثة': '3',
        'أربع': '4', 'أربعة': '4',
        'خمس': '5', 'خمسة': '5',
        'ست': '6', 'ستة': '6',
        'سبع': '7', 'سبعة': '7',
        'ثمان': '8', 'ثماني': '8', 'ثمانية': '8',
        'تسع': '9', 'تسعة': '9',
        'عشر': '10', 'عشرة': '10',
        'أحد عشر': '11', 'إحدى عشرة': '11',
        'اثنا عشر': '12', 'اثنتا عشرة': '12', 'اثني عشر': '12', 'اثنى عشر': '12',
        'خمس عشرة': '15', 'خمسة عشر': '15',
        'عشرين': '20', 'عشرون': '20',
        'واحد وعشرين': '21', 'واحد وعشرون': '21',
        'أربع وعشرين': '24', 'أربع وعشرون': '24',
        'ثلاثين': '30', 'ثلاثون': '30',
        'خمس وثلاثين': '35', 'خمسة وثلاثون': '35',
        'خمس وأربعين': '45', 'خمسة وأربعون': '45', 'خمسة وأربعين': '45',
        'ثمان وأربعين': '48', 'ثماني وأربعين': '48', 'ثمانية وأربعين': '48', 'ثمانية وأربعون': '48',
        'خمسون': '50', 'خمسين': '50',
        'سبعين': '70', 'سبعون': '70',
        'تسعين': '90', 'تسعون': '90',
        'مائة': '100', 'مئة': '100',
        'مائة وعشرين': '120', 'مائة وعشرون': '120',
    }

    # Build reverse map: digit -> list of Arabic word forms
    _DIGIT_TO_ARABIC = {}
    for _ar, _dig in _ARABIC_TO_DIGIT.items():
        _DIGIT_TO_ARABIC.setdefault(_dig, []).append(_ar)

    def _normalize_text_with_numbers(self, text: str) -> str:
        """Expand text with digit equivalents for Arabic number words and vice versa.
        
        This allows matching '48 ساعة' against 'ثمان وأربعين ساعة' and similar.
        """
        expanded = text.lower()
        
        # Add digit equivalents for Arabic words found in text
        for arabic_word, digit in self._ARABIC_TO_DIGIT.items():
            if arabic_word in expanded:
                expanded += f' {digit} '
        
        # Add Arabic word equivalents for digits found in text
        for digit_match in re.findall(r'\d+', text):
            if digit_match in self._DIGIT_TO_ARABIC:
                for ar_word in self._DIGIT_TO_ARABIC[digit_match]:
                    expanded += f' {ar_word} '
        
        return expanded

    def _check_key_facts(self, answer: str, key_facts: List[str]) -> Tuple[float, List[str]]:
        """
        Check if all key legal facts are present in the answer.
        
        Returns:
            (score, missing_facts) where score is 0.0-1.0
        """
        # Normalize answer with number equivalents for better matching
        answer_normalized = self._normalize_text_with_numbers(answer)
        missing = []
        found = 0
        
        for fact in key_facts:
            # Extract key numbers and terms from original fact
            key_terms = self._extract_key_terms(fact)
            
            # Check if most key terms are present (at least 40%)
            terms_found = 0
            for term in key_terms:
                term_lower = term.lower()
                # Check if term or its normalized equivalent exists
                if term_lower in answer_normalized:
                    terms_found += 1
                else:
                    # Check if digit equivalent exists
                    term_digit = self._ARABIC_TO_DIGIT.get(term_lower)
                    if term_digit and term_digit in answer_normalized:
                        terms_found += 1
                        
            if terms_found >= len(key_terms) * 0.4:
                found += 1
            else:
                missing.append(fact)
        
        score = found / max(len(key_facts), 1)
        return score, missing
    
    def _extract_key_terms(self, fact: str) -> List[str]:
        """Extract important terms from a fact (numbers, key words)."""
        # Extract numbers (e.g., "21", "30", "10")
        numbers = re.findall(r'\d+', fact)
        
        # Also extract Arabic number words and convert them
        for ar_num, digit in self._ARABIC_TO_DIGIT.items():
            if ar_num in fact:
                numbers.append(digit)
        
        # Remove duplicates from numbers
        numbers = list(set(numbers))
        
        # Extract important Arabic words (ignore common words)
        common_words = {
            'في', 'من', 'إلى', 'على', 'عن', 'مع', 'هذا', 'هذه', 'التي', 'الذي',
            'ما', 'هل', 'كيف', 'متى', 'أين', 'لماذا', 'كم', 'أي', 'كل', 'بعض',
            'قد', 'لقد', 'كان', 'كانت', 'يكون', 'تكون', 'أن', 'إن', 'بعد', 'حسب',
            'أو', 'لا', 'عن', 'وفقا', 'وفقاً', 'ذلك',
        }
        
        words = [w for w in fact.split() if len(w) > 2 and w not in common_words]
        
        # Return numbers + top important words
        return numbers + words[:4]
    
    def _check_article_reference(self, answer: str, correct_article: str) -> Tuple[float, str]:
        """
        Check if the correct article is cited.
        
        Returns:
            (score, explanation)
        """
        # Extract all article numbers from correct reference (e.g., "المادة 36 أو 89" -> ["36", "89"])
        correct_nums = re.findall(r'\d+', correct_article)
        if not correct_nums:
            return 0.5, "⚠️ لا يمكن تحديد رقم المادة الصحيح"
        
        # Find all article references in answer (المادة X) - more flexible patterns
        article_refs = re.findall(r'[Mm]ادة\s*(\d+)', answer)
        article_refs += re.findall(r'المادة\s*(\d+)', answer)
        article_refs += re.findall(r'م\s*(\d+)', answer)  # Abbreviated form
        article_refs += re.findall(r'رقم\s*(\d+)', answer)  # Article number X
        
        # Remove duplicates
        article_refs = list(set(article_refs))
        
        if not article_refs:
            return 0.0, "❌ لم يتم ذكر أي مادة قانونية"
        
        # Check if ANY of the correct articles were cited
        matching_articles = [num for num in correct_nums if num in article_refs]
        
        if matching_articles:
            if len(matching_articles) == len(correct_nums):
                return 1.0, f"✅ تم ذكر جميع المواد الصحيحة: {matching_articles}"
            else:
                return 1.0, f"✅ تم ذكر المادة {matching_articles[0]} (من المواد الصحيحة: {correct_nums})"
        else:
            return 0.0, f"❌ مواد خاطئة: {article_refs}، الصحيح: {correct_nums}"
    
    def _check_wrong_answers(self, answer: str, wrong_answers: List[str]) -> Tuple[float, List[str]]:
        """
        Check if answer contains any known wrong information.
        
        Returns:
            (score, wrong_info_found)
        """
        answer_lower = answer.lower()
        wrong_found = []
        
        for wrong in wrong_answers:
            key_terms = self._extract_key_terms(wrong)
            
            # If most key terms are found, check if it's presented as the ONLY answer
            # (not as an exception or special case)
            terms_found = sum(1 for term in key_terms if term.lower() in answer_lower)
            if terms_found >= len(key_terms) * 0.7:  # 70% of terms
                # Check if it's presented as exception/special case (which is OK)
                exception_indicators = [
                    'استثناء', 'حالة خاصة', 'بعض', 'بالنسبة', 'أو', 'في حالة',
                    'متقطعة', 'خاصة', 'يحددها', 'ما عدا', 'باستثناء'
                ]
                
                # If exception indicators are present, it's probably OK
                has_exception_context = any(ind in answer_lower for ind in exception_indicators)
                
                if not has_exception_context:
                    wrong_found.append(wrong)
        
        if wrong_found:
            return 0.0, wrong_found
        return 1.0, []
    
    def _semantic_similarity(self, answer1: str, answer2: str) -> float:
        """
        Calculate semantic similarity between two texts.
        
        Uses word overlap (Jaccard similarity).
        """
        # Tokenize and clean
        words1 = set(re.findall(r'\w+', answer1.lower()))
        words2 = set(re.findall(r'\w+', answer2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        # Remove very common words
        common_words = {
            'في', 'من', 'إلى', 'على', 'عن', 'مع', 'هذا', 'هذه', 'التي', 'الذي',
            'ما', 'هل', 'كيف', 'متى', 'أين', 'لماذا', 'كم', 'أي', 'كل', 'بعض',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'
        }
        
        words1 = words1 - common_words
        words2 = words2 - common_words
        
        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _generate_explanation(self, results: Dict, total_score: float) -> str:
        """Generate human-readable explanation of the results."""
        if results['legally_accurate']:
            return f"✅ **إجابة دقيقة قانونياً** (النتيجة: {total_score:.1%})"
        
        issues = []
        checks = results['checks']
        
        # Key facts issues
        if checks['key_facts']['score'] < 0.8:
            missing_count = len(results['missing_facts'])
            issues.append(f"• ناقص {missing_count} من الحقائق الأساسية")
        
        # Article issues
        if checks['article_accuracy']['score'] < 1.0:
            issues.append(f"• {checks['article_accuracy']['details']}")
        
        # Wrong info issues
        if checks['no_wrong_info']['score'] < 1.0:
            wrong_count = len(results['wrong_info'])
            issues.append(f"• يحتوي على {wrong_count} معلومة خاطئة")
        
        issues_text = '\n'.join(issues) if issues else 'مشاكل في الدقة'
        
        return f"❌ **إجابة غير دقيقة قانونياً** (النتيجة: {total_score:.1%})\n\n**المشاكل:**\n{issues_text}"
    
    def get_statistics(self) -> Dict:
        """Get overall validation statistics."""
        if self.total_evaluations == 0:
            return {
                'total_evaluations': 0,
                'passed': 0,
                'failed': 0,
                'pass_rate': 0.0
            }
        
        return {
            'total_evaluations': self.total_evaluations,
            'passed': self.passed_evaluations,
            'failed': self.total_evaluations - self.passed_evaluations,
            'pass_rate': round(self.passed_evaluations / self.total_evaluations * 100, 1)
        }
    
    def validate_batch(self, qa_pairs: List[Tuple[str, str]]) -> List[Dict]:
        """
        Validate multiple Q&A pairs at once.
        
        Args:
            qa_pairs: List of (question, answer) tuples
        
        Returns:
            List of validation results
        """
        results = []
        for question, answer in qa_pairs:
            result = self.validate_answer(question, answer)
            results.append(result)
        return results


def validate_ai_answer(question: str, answer: str) -> Dict:
    """
    Main function to validate an AI answer for legal accuracy.
    
    Args:
        question: The legal question asked
        answer: The AI-generated answer
    
    Returns:
        Dict with validation results including:
            - legally_accurate: bool
            - accuracy_score: float (0.0-1.0)
            - explanation: str
            - checks: detailed check results
            - missing_facts: list
            - wrong_info: list
    
    Example:
        >>> result = validate_ai_answer(
        ...     "ما هي مدة الإجازة السنوية؟",
        ...     "الإجازة السنوية 21 يوماً حسب المادة 124"
        ... )
        >>> print(result['legally_accurate'])
        True
        >>> print(result['accuracy_score'])
        0.92
    """
    validator = LegalAccuracyValidator()
    return validator.validate_answer(question, answer)


# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("🔍 اختبار نظام التحقق من الدقة القانونية")
    print("=" * 70)
    print()
    
    # Test cases
    test_question = "ما هي مدة الإجازة السنوية للعامل؟"
    
    # Good answer
    good_answer = """
    مدة الإجازة السنوية للعامل حسب المادة 124 من قانون العمل المصري:
    - 15 يوماً في السنة الأولى
    - 21 يوماً اعتباراً من السنة الثانية
    - 30 يوماً لمن أمضى 10 سنوات كاملة أو تجاوزت سنه 50 عاماً
    - 45 يوماً للأشخاص ذوي الإعاقة والأقزام
    """
    
    # Bad answer
    bad_answer = """
    الإجازة السنوية حسب المادة 10 هي 10 أيام فقط للجميع
    ويمكن التنازل عنها مقابل المال.
    """
    
    # Partial answer (missing some facts)
    partial_answer = """
    الإجازة السنوية للعامل حسب المادة 124 هي 21 يوماً سنوياً.
    """
    
    validator = LegalAccuracyValidator()
    
    # Test 1: Good answer
    print("📝 **اختبار 1: إجابة جيدة**")
    print(f"السؤال: {test_question}")
    result1 = validator.validate_answer(test_question, good_answer)
    print(f"النتيجة: {result1['accuracy_score']:.1%}")
    print(f"دقيقة قانونياً: {result1['legally_accurate']}")
    print(f"الشرح: {result1['explanation']}")
    print()
    
    # Test 2: Bad answer
    print("📝 **اختبار 2: إجابة خاطئة**")
    print(f"السؤال: {test_question}")
    result2 = validator.validate_answer(test_question, bad_answer)
    print(f"النتيجة: {result2['accuracy_score']:.1%}")
    print(f"دقيقة قانونياً: {result2['legally_accurate']}")
    print(f"الشرح: {result2['explanation']}")
    if result2['missing_facts']:
        print(f"حقائق ناقصة: {result2['missing_facts']}")
    if result2['wrong_info']:
        print(f"معلومات خاطئة: {result2['wrong_info']}")
    print()
    
    # Test 3: Partial answer
    print("📝 **اختبار 3: إجابة جزئية**")
    print(f"السؤال: {test_question}")
    result3 = validator.validate_answer(test_question, partial_answer)
    print(f"النتيجة: {result3['accuracy_score']:.1%}")
    print(f"دقيقة قانونياً: {result3['legally_accurate']}")
    print(f"الشرح: {result3['explanation']}")
    if result3['missing_facts']:
        print(f"حقائق ناقصة ({len(result3['missing_facts'])}): {result3['missing_facts']}")
    print()
    
    # Statistics
    stats = validator.get_statistics()
    print("=" * 70)
    print("📊 **الإحصائيات**")
    print(f"إجمالي التقييمات: {stats['total_evaluations']}")
    print(f"نجح: {stats['passed']}")
    print(f"فشل: {stats['failed']}")
    print(f"معدل النجاح: {stats['pass_rate']}%")
    print("=" * 70)
