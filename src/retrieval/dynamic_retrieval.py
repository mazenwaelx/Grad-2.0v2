"""
Dynamic document retrieval based on question complexity
"""
import re
from typing import Dict, Any


class DynamicRetrieval:
    """Intelligently determine how many documents to retrieve based on question complexity"""
    
    def __init__(self):
        self.complexity_indicators = {
            # Simple questions (2-3 docs)
            'simple_patterns': [
                r'^ما هو\s+',  # What is...
                r'^ما هي\s+',  # What is...
                r'^كم\s+',     # How much/many...
                r'^متى\s+',    # When...
                r'^أين\s+',    # Where...
            ],
            
            # Complex questions (4-6 docs)
            'complex_indicators': [
                'مقارنة', 'فرق', 'اختلاف', 'بين',  # Comparison
                'إجراءات', 'خطوات', 'كيفية',      # Procedures
                'حالات', 'أنواع', 'أشكال',        # Multiple cases
                'استثناءات', 'شروط',             # Exceptions/conditions
                'تفصيل', 'بالتفصيل', 'اشرح',     # Detailed explanation
            ],
            
            # Multi-topic questions (5-6 docs)
            'multi_topic_indicators': [
                'و', 'أو', 'كذلك', 'أيضاً',      # Multiple topics
                'جميع', 'كل', 'كافة',            # All/comprehensive
            ]
        }
    
    def analyze_question_complexity(self, question: str) -> Dict[str, Any]:
        """Analyze question complexity and return recommended document count"""
        question_lower = question.lower().strip()
        
        # Initialize scores
        complexity_score = 0
        indicators_found = []
        
        # Check for simple patterns (reduces complexity)
        is_simple = any(re.match(pattern, question_lower) for pattern in self.complexity_indicators['simple_patterns'])
        if is_simple:
            complexity_score -= 2
            indicators_found.append("simple_pattern")
        
        # Check for complex indicators
        complex_count = sum(1 for indicator in self.complexity_indicators['complex_indicators'] 
                          if indicator in question_lower)
        complexity_score += complex_count * 1.5
        if complex_count > 0:
            indicators_found.extend([f"complex_{i}" for i in range(complex_count)])
        
        # Check for multi-topic indicators
        multi_topic_count = sum(1 for indicator in self.complexity_indicators['multi_topic_indicators'] 
                              if indicator in question_lower)
        complexity_score += multi_topic_count * 1
        if multi_topic_count > 0:
            indicators_found.extend([f"multi_topic_{i}" for i in range(multi_topic_count)])
        
        # Question length factor
        word_count = len(question.split())
        if word_count > 15:
            complexity_score += 1
            indicators_found.append("long_question")
        elif word_count < 5:
            complexity_score -= 1
            indicators_found.append("short_question")
        
        # Determine document count based on complexity score
        if complexity_score <= 0:
            doc_count = 2  # Very simple questions
            complexity_level = "simple"
        elif complexity_score <= 2:
            doc_count = 3  # Simple questions
            complexity_level = "simple"
        elif complexity_score <= 4:
            doc_count = 4  # Medium complexity
            complexity_level = "medium"
        elif complexity_score <= 6:
            doc_count = 5  # Complex questions
            complexity_level = "complex"
        else:
            doc_count = 6  # Very complex questions
            complexity_level = "very_complex"
        
        return {
            "complexity_score": complexity_score,
            "complexity_level": complexity_level,
            "recommended_docs": doc_count,
            "indicators_found": indicators_found,
            "word_count": word_count
        }
    
    def get_optimal_k(self, question: str) -> int:
        """Get optimal number of documents to retrieve for this question"""
        analysis = self.analyze_question_complexity(question)
        return analysis["recommended_docs"]


# Global instance
dynamic_retrieval = DynamicRetrieval()


def get_dynamic_k(question: str) -> int:
    """Get optimal document count for a question"""
    return dynamic_retrieval.get_optimal_k(question)


# Example usage and testing
if __name__ == "__main__":
    test_questions = [
        "ما هي ساعات العمل؟",  # Simple -> 2-3 docs
        "كم مدة الإجازة السنوية؟",  # Simple -> 2-3 docs
        "ما الفرق بين إجازة الأمومة وإجازة الوضع؟",  # Complex -> 4-5 docs
        "اشرح بالتفصيل إجراءات فصل العامل وما هي حقوقه في هذه الحالة؟",  # Very complex -> 6 docs
        "ما هي جميع أنواع الإجازات المتاحة للعامل وشروط كل منها؟",  # Multi-topic -> 5-6 docs
    ]
    
    for question in test_questions:
        analysis = dynamic_retrieval.analyze_question_complexity(question)
        print(f"\nQuestion: {question}")
        print(f"Complexity: {analysis['complexity_level']} (score: {analysis['complexity_score']})")
        print(f"Recommended docs: {analysis['recommended_docs']}")
        print(f"Indicators: {analysis['indicators_found']}")