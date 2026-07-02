"""
Run Legal Accuracy Test - Test AI answers against ground truth

This script evaluates the legal accuracy of AI-generated answers by:
1. Loading ground truth Q&A pairs
2. Asking the AI each question
3. Validating answers against ground truth
4. Generating a detailed report

Usage:
    python eval/run_legal_accuracy_test.py
    python eval/run_legal_accuracy_test.py --limit 5  # Test first 5 questions only
"""

import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Load environment variables FIRST (before any imports that might use them)
from dotenv import load_dotenv
load_dotenv(override=True)

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eval.legal_accuracy_validator import LegalAccuracyValidator

# Try to import AI agent
try:
    from src.agents.langchain_react_agent import LangChainReActAgent
    from src.retrieval.retriever import prepare_retriever
    from src.llm.llm_manager import init_llm
    from src.config.settings import MODEL_NAME
    from data.data_embedding import SentenceTransformerEmbeddings
    from src.retrieval.file_processor import FileProcessor, set_file_processor
    from database.db_memory_store import DatabaseChatMessageHistory
    from database import init_database
    AI_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Warning: Could not import AI components: {e}")
    print("   Running in TEST MODE with mock answers\n")
    AI_AVAILABLE = False


class LegalAccuracyTester:
    """Test AI legal accuracy against ground truth."""
    
    def __init__(self, use_ai: bool = True):
        """Initialize the tester."""
        self.validator = LegalAccuracyValidator()
        self.agent = None
        self.use_ai = use_ai and AI_AVAILABLE
        
        if self.use_ai:
            self._initialize_ai()
    
    def _initialize_ai(self):
        """Initialize the AI agent."""
        print("🔧 جاري تهيئة النظام...")
        
        try:
            # Initialize database
            init_database()
            
            # Initialize retriever
            print("  📚 تحميل قاعدة البيانات القانونية...")
            retriever, _, _, _ = prepare_retriever("data/labour_data/labour_law.md")
            
            # Initialize file processor
            embeddings = SentenceTransformerEmbeddings()
            file_processor = FileProcessor(embeddings)
            set_file_processor(file_processor)
            
            # Initialize LLM
            print("  🤖 تهيئة نموذج الذكاء الاصطناعي...")
            llm = init_llm(MODEL_NAME)
            
            # Create test chat
            test_chat_id = f"legal_accuracy_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            history_store = DatabaseChatMessageHistory(test_chat_id)
            
            # Build agent
            self.agent = LangChainReActAgent(
                llm=llm,
                retriever=retriever,
                history_store=history_store,
                file_processor=None,
                chat_id=test_chat_id,
                log_callback=lambda msg: None,
                max_iterations=6,
                verbose=False,
            )
            
            print("  ✅ النظام جاهز!\n")
            
        except Exception as e:
            print(f"  ❌ فشل في تهيئة النظام: {e}")
            print("  ⚠️ سيتم استخدام إجابات وهمية للاختبار\n")
            self.use_ai = False
    
    def get_ai_answer(self, question: str) -> str:
        """Get answer from AI or return mock answer."""
        if self.use_ai and self.agent:
            try:
                return self.agent.ask(question)
            except Exception as e:
                print(f"    ⚠️ خطأ في الحصول على إجابة من AI: {e}")
                return "[فشل الحصول على الإجابة]"
        else:
            # Mock answer for testing
            return f"إجابة وهمية للسؤال: {question}"
    
    def run_tests(self, limit: int = None) -> Dict:
        """
        Run legal accuracy tests.
        
        Args:
            limit: Maximum number of questions to test (None = all)
        
        Returns:
            Dict with test results and statistics
        """
        ground_truth = self.validator.ground_truth
        
        if limit:
            ground_truth = ground_truth[:limit]
        
        print("=" * 70)
        print(f"🔬 اختبار الدقة القانونية - نظام Estasheer")
        print(f"   عدد الأسئلة: {len(ground_truth)}")
        print(f"   الوضع: {'🔴 مباشر مع AI' if self.use_ai else '🟢 اختبار وهمي'}")
        print(f"   الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()
        
        results = []
        
        for i, gt in enumerate(ground_truth, 1):
            print(f"📝 [{i}/{len(ground_truth)}] {gt['id']}: {gt['question']}")
            print(f"   الصعوبة: {gt['difficulty']}")
            
            # Get AI answer
            start_time = time.time()
            ai_answer = self.get_ai_answer(gt['question'])
            elapsed = time.time() - start_time
            
            print(f"   ⏱️ وقت الاستجابة: {elapsed:.2f} ثانية")
            
            # Validate answer
            validation = self.validator.validate_answer(gt['question'], ai_answer)
            validation['ai_answer'] = ai_answer
            validation['response_time'] = round(elapsed, 2)
            validation['difficulty'] = gt['difficulty']
            
            results.append(validation)
            
            # Print result
            status = "✅ دقيقة" if validation['legally_accurate'] else "❌ غير دقيقة"
            print(f"   {status} (النتيجة: {validation['accuracy_score']:.1%})")
            
            if not validation['legally_accurate']:
                if validation['missing_facts']:
                    print(f"   ⚠️ حقائق ناقصة: {len(validation['missing_facts'])}")
                if validation['wrong_info']:
                    print(f"   ⚠️ معلومات خاطئة: {len(validation['wrong_info'])}")
            
            print()
            
            # Small delay between requests to avoid rate limiting
            if self.use_ai and i < len(ground_truth):
                time.sleep(1)
        
        # Calculate statistics
        stats = self._calculate_statistics(results)
        
        return {
            'results': results,
            'statistics': stats,
            'timestamp': datetime.now().isoformat(),
            'mode': 'live' if self.use_ai else 'mock',
            'total_questions': len(ground_truth)
        }
    
    def _calculate_statistics(self, results: List[Dict]) -> Dict:
        """Calculate overall statistics."""
        total = len(results)
        passed = sum(1 for r in results if r.get('legally_accurate'))
        failed = total - passed
        
        scores = [r['accuracy_score'] for r in results]
        avg_score = sum(scores) / max(total, 1)
        
        # Per-difficulty breakdown
        difficulty_stats = {}
        for diff in ['simple', 'medium', 'complex']:
            diff_results = [r for r in results if r.get('difficulty') == diff]
            if diff_results:
                diff_scores = [r['accuracy_score'] for r in diff_results]
                difficulty_stats[diff] = {
                    'total': len(diff_results),
                    'passed': sum(1 for r in diff_results if r['legally_accurate']),
                    'avg_score': round(sum(diff_scores) / len(diff_scores), 3)
                }
        
        # Response times
        response_times = [r.get('response_time', 0) for r in results]
        
        return {
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': round(passed / max(total, 1) * 100, 1),
            'average_score': round(avg_score, 3),
            'difficulty_breakdown': difficulty_stats,
            'avg_response_time': round(sum(response_times) / max(len(response_times), 1), 2)
        }
    
    def print_summary(self, test_data: Dict):
        """Print test summary."""
        stats = test_data['statistics']
        
        print("=" * 70)
        print("📊 **ملخص النتائج**")
        print("=" * 70)
        print(f"إجمالي الأسئلة:        {stats['total_tests']}")
        print(f"إجابات دقيقة:          {stats['passed']} ✅")
        print(f"إجابات غير دقيقة:      {stats['failed']} ❌")
        print(f"معدل الدقة:             {stats['pass_rate']}%")
        print(f"متوسط النتيجة:         {stats['average_score']:.1%}")
        print(f"متوسط وقت الاستجابة:   {stats['avg_response_time']} ثانية")
        print()
        
        if stats['difficulty_breakdown']:
            print("**حسب مستوى الصعوبة:**")
            for diff, data in stats['difficulty_breakdown'].items():
                print(f"  {diff:>8}: {data['avg_score']:.1%} ({data['passed']}/{data['total']} دقيقة)")
        
        print("=" * 70)
        
        # Interpretation
        if stats['pass_rate'] >= 85:
            print("🎉 **نتيجة ممتازة!** النظام يقدم إجابات دقيقة قانونياً")
        elif stats['pass_rate'] >= 70:
            print("✅ **نتيجة جيدة** النظام موثوق في معظم الحالات")
        elif stats['pass_rate'] >= 50:
            print("⚠️ **نتيجة متوسطة** يحتاج النظام لتحسينات")
        else:
            print("❌ **نتيجة ضعيفة** النظام يحتاج لتطوير كبير")
        
        print("=" * 70)
    
    def save_report(self, test_data: Dict, filename: str = None):
        """Save test report to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"legal_accuracy_report_{timestamp}.json"
        
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        report_path = reports_dir / filename
        
        # Remove full AI answers to keep file size manageable
        compact_results = []
        for r in test_data['results']:
            compact = {k: v for k, v in r.items() if k != 'ai_answer'}
            compact['ai_answer_preview'] = r['ai_answer'][:200] + "..." if len(r['ai_answer']) > 200 else r['ai_answer']
            compact_results.append(compact)
        
        report_data = {
            **test_data,
            'results': compact_results
        }
        
        report_path.write_text(
            json.dumps(report_data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        
        print(f"\n📄 تم حفظ التقرير: {report_path}")
        return report_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="اختبار الدقة القانونية لنظام Estasheer AI"
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='عدد الأسئلة للاختبار (افتراضي: كل الأسئلة)'
    )
    parser.add_argument(
        '--no-ai',
        action='store_true',
        help='استخدام إجابات وهمية بدلاً من AI الفعلي'
    )
    
    args = parser.parse_args()
    
    # Run tests
    tester = LegalAccuracyTester(use_ai=not args.no_ai)
    test_data = tester.run_tests(limit=args.limit)
    
    # Print summary
    tester.print_summary(test_data)
    
    # Save report
    tester.save_report(test_data)
    
    print("\n✅ تم الانتهاء من الاختبار!")


if __name__ == "__main__":
    main()
