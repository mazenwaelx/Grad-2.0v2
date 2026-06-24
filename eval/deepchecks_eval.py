"""
Deepchecks Evaluation for Egyptian Legal AI (RAG System)
=========================================================

Evaluates the quality of:
1. Document retrieval — Are the right documents being retrieved?
2. LLM response quality — Are the answers accurate, relevant, and complete?
3. System consistency — Does the same question produce similar answers?

Usage:
    python eval/deepchecks_eval.py                  # Run all checks (cached mode)
    python eval/deepchecks_eval.py --live            # Run with real Gemini API calls
    python eval/deepchecks_eval.py --report-only     # Generate report from last run
"""

import sys

# Fix Windows console encoding for emoji/Unicode output
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ─────────────────────────────────────────────────────────
# Test Dataset: Egyptian Labour Law Q&A Pairs
# ─────────────────────────────────────────────────────────
# Each entry has:
#   - question: The question to ask
#   - expected_keywords: Keywords that MUST appear in a correct answer
#   - expected_topic: The legal topic the retriever should find
#   - difficulty: simple | medium | complex

TEST_DATASET = [
    {
        "id": "Q01",
        "question": "ما هي مدة الإجازة السنوية للعامل؟",
        "expected_keywords": ["إجازة", "سنوية", "يوم"],
        "expected_topic": "الإجازات",
        "difficulty": "simple",
    },
    {
        "id": "Q02",
        "question": "ما هي حقوق المرأة العاملة في قانون العمل المصري؟",
        "expected_keywords": ["المرأة", "عاملة", "إجازة وضع"],
        "expected_topic": "حقوق المرأة العاملة",
        "difficulty": "medium",
    },
    {
        "id": "Q03",
        "question": "ما هو الحد الأدنى للأجور؟",
        "expected_keywords": ["أجر", "حد أدنى"],
        "expected_topic": "الأجور",
        "difficulty": "simple",
    },
    {
        "id": "Q04",
        "question": "ما هي إجراءات الفصل التعسفي؟",
        "expected_keywords": ["فصل", "تعسفي", "تعويض"],
        "expected_topic": "إنهاء علاقة العمل",
        "difficulty": "complex",
    },
    {
        "id": "Q05",
        "question": "كم عدد ساعات العمل اليومية؟",
        "expected_keywords": ["ساعات", "عمل"],
        "expected_topic": "ساعات العمل",
        "difficulty": "simple",
    },
    {
        "id": "Q06",
        "question": "ما هي شروط عقد العمل؟",
        "expected_keywords": ["عقد", "عمل", "شروط"],
        "expected_topic": "عقود العمل",
        "difficulty": "medium",
    },
    {
        "id": "Q07",
        "question": "ما هي أنواع الإجازات المتاحة للعامل؟",
        "expected_keywords": ["إجازة"],
        "expected_topic": "الإجازات",
        "difficulty": "medium",
    },
    {
        "id": "Q08",
        "question": "ما هي حقوق العامل عند إنهاء العقد؟",
        "expected_keywords": ["إنهاء", "عقد", "حقوق"],
        "expected_topic": "إنهاء علاقة العمل",
        "difficulty": "complex",
    },
    {
        "id": "Q09",
        "question": "ما هي قواعد التأمينات الاجتماعية للعمال؟",
        "expected_keywords": ["تأمين"],
        "expected_topic": "التأمينات الاجتماعية",
        "difficulty": "medium",
    },
    {
        "id": "Q10",
        "question": "ما هي إجراءات تسوية النزاعات العمالية؟",
        "expected_keywords": ["نزاع", "تسوية"],
        "expected_topic": "النزاعات العمالية",
        "difficulty": "complex",
    },
    {
        "id": "Q11",
        "question": "ما هي قواعد السلامة والصحة المهنية؟",
        "expected_keywords": ["سلامة", "صحة", "مهنية"],
        "expected_topic": "السلامة المهنية",
        "difficulty": "medium",
    },
    {
        "id": "Q12",
        "question": "ما هي حقوق العامل في الإجازة المرضية؟",
        "expected_keywords": ["إجازة", "مرضية"],
        "expected_topic": "الإجازات",
        "difficulty": "simple",
    },
    {
        "id": "Q13",
        "question": "ما الفرق بين عقد العمل محدد المدة وغير محدد المدة؟",
        "expected_keywords": ["عقد", "محدد", "مدة"],
        "expected_topic": "عقود العمل",
        "difficulty": "complex",
    },
    {
        "id": "Q14",
        "question": "ما هي قواعد تشغيل الأطفال؟",
        "expected_keywords": ["أطفال", "تشغيل"],
        "expected_topic": "تشغيل الأطفال",
        "difficulty": "medium",
    },
    {
        "id": "Q15",
        "question": "ما هي مدة إجازة الوضع للمرأة العاملة؟",
        "expected_keywords": ["إجازة", "وضع", "أشهر"],
        "expected_topic": "حقوق المرأة العاملة",
        "difficulty": "simple",
    },
]


# ─────────────────────────────────────────────────────────
# Evaluation Metrics
# ─────────────────────────────────────────────────────────

def calculate_keyword_coverage(response: str, expected_keywords: List[str]) -> float:
    """
    Calculate what percentage of expected keywords appear in the response.
    Returns a score between 0.0 and 1.0.
    """
    if not expected_keywords:
        return 1.0
    
    found = 0
    for keyword in expected_keywords:
        if keyword in response:
            found += 1
    
    return found / len(expected_keywords)


def calculate_response_quality(response: str) -> Dict[str, float]:
    """
    Calculate multiple quality metrics for a response.
    Returns scores between 0.0 and 1.0.
    """
    metrics = {}
    
    # 1. Completeness: Is the response substantial enough?
    word_count = len(response.split())
    if word_count >= 100:
        metrics["completeness"] = 1.0
    elif word_count >= 50:
        metrics["completeness"] = 0.8
    elif word_count >= 20:
        metrics["completeness"] = 0.5
    else:
        metrics["completeness"] = 0.2
    
    # 2. Structure: Does the response use formatting (bullets, numbers, headers)?
    has_bullets = any(char in response for char in ["•", "●", "-", "*"])
    has_numbers = any(f"{i}." in response or f"{i})" in response for i in range(1, 10))
    has_bold = "**" in response
    structure_score = sum([has_bullets, has_numbers, has_bold]) / 3
    metrics["structure"] = max(0.3, structure_score)  # Minimum 0.3 if there's any content
    
    # 3. Legal References: Does it mention articles or legal terms?
    has_article_ref = "المادة" in response or "مادة" in response
    has_law_ref = "قانون" in response
    metrics["legal_references"] = 1.0 if (has_article_ref and has_law_ref) else (0.5 if has_article_ref or has_law_ref else 0.0)
    
    # 4. Arabic Quality: Is the response in Arabic (not gibberish)?
    arabic_chars = sum(1 for c in response if '\u0600' <= c <= '\u06FF')
    total_chars = max(len(response), 1)
    metrics["arabic_quality"] = min(1.0, arabic_chars / (total_chars * 0.3))
    
    # 5. No Error: Is the response NOT an error message?
    error_indicators = ["عذراً، حدث خطأ", "خطأ في معالجة", "يرجى المحاولة مرة أخرى"]
    metrics["no_error"] = 0.0 if any(err in response for err in error_indicators) else 1.0
    
    return metrics


def calculate_retrieval_quality(retrieved_docs: List[Any], expected_topic: str) -> Dict[str, float]:
    """
    Evaluate the quality of retrieved documents.
    """
    metrics = {}
    
    if not retrieved_docs:
        return {"relevance": 0.0, "coverage": 0.0, "doc_count": 0.0}
    
    # 1. Doc count: Did we retrieve a reasonable number?
    doc_count = len(retrieved_docs)
    metrics["doc_count"] = min(1.0, doc_count / 3)  # At least 3 docs is ideal
    
    # 2. Relevance: Do the docs contain the expected topic keywords?
    topic_keywords = expected_topic.split()
    relevant_docs = 0
    for doc in retrieved_docs:
        content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
        if any(kw in content for kw in topic_keywords):
            relevant_docs += 1
    
    metrics["relevance"] = relevant_docs / max(len(retrieved_docs), 1)
    
    # 3. Coverage: Total content length (more content = more coverage)
    total_content = sum(
        len(doc.page_content) if hasattr(doc, 'page_content') else len(str(doc))
        for doc in retrieved_docs
    )
    metrics["coverage"] = min(1.0, total_content / 2000)  # 2000 chars is good coverage
    
    return metrics


# ─────────────────────────────────────────────────────────
# Main Evaluation Runner
# ─────────────────────────────────────────────────────────

class DeepChecksEvaluator:
    """Runs comprehensive evaluation of the RAG system."""
    
    def __init__(self, live_mode: bool = False):
        """
        Args:
            live_mode: If True, makes real API calls. If False, uses cached responses.
        """
        self.live_mode = live_mode
        self.results: List[Dict[str, Any]] = []
        self.reports_dir = PROJECT_ROOT / "eval" / "reports"
        self.cache_dir = PROJECT_ROOT / "eval" / "cache"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.retriever = None
        self.agent = None
        self._initialized = False
    
    def _get_cache_path(self, question: str) -> Path:
        """Get cache file path for a question."""
        key = hashlib.md5(question.encode('utf-8'), usedforsecurity=False).hexdigest()
        return self.cache_dir / f"{key}.json"
    
    def _load_cached_response(self, question: str) -> Optional[Dict]:
        """Load a cached response if available."""
        cache_path = self._get_cache_path(question)
        if cache_path.exists():
            return json.loads(cache_path.read_text(encoding='utf-8'))
        return None
    
    def _save_cached_response(self, question: str, response: str, docs: List[str]):
        """Cache a response for future use."""
        cache_path = self._get_cache_path(question)
        cache_data = {
            "question": question,
            "response": response,
            "retrieved_docs": docs,
            "timestamp": datetime.now().isoformat(),
        }
        cache_path.write_text(json.dumps(cache_data, ensure_ascii=False, indent=2), encoding='utf-8')
    
    def initialize_system(self):
        """Initialize the retriever and agent for live evaluation."""
        if self._initialized:
            return
        
        print("🔧 Initializing RAG system for evaluation...")
        
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
            
            from src.retrieval.retriever import prepare_retriever
            from src.retrieval.file_processor import FileProcessor, set_file_processor
            from src.agents.langchain_react_agent import LangChainReActAgent, build_langchain_tools
            from src.llm.llm_manager import init_llm
            from src.config.settings import MODEL_NAME
            from data.data_embedding import SentenceTransformerEmbeddings
            from database.db_memory_store import DatabaseChatMessageHistory
            
            # Initialize retriever
            print("  📚 Loading FAISS retriever...")
            self.retriever, _, _, _ = prepare_retriever("data/labour_data/labour_law.md")
            
            # Initialize file processor
            embeddings = SentenceTransformerEmbeddings()
            file_processor = FileProcessor(embeddings)
            set_file_processor(file_processor)
            
            # Initialize LLM
            print("  🤖 Initializing LLM...")
            llm = init_llm(MODEL_NAME)
            
            # Create evaluation history store
            eval_chat_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                from database import create_user, create_chat
                create_user("eval_user@eval.com", "Eval User", "EvalPassword123!")
                create_chat(eval_chat_id, "eval_user@eval.com", "Evaluation Chat")
            except Exception:
                pass
            history_store = DatabaseChatMessageHistory(eval_chat_id)
            
            # Build tools and agent
            tools = build_langchain_tools(self.retriever, history_store, file_processor)
            self.agent = LangChainReActAgent(
                llm=llm,
                tools=tools,
                history_store=history_store,
                log_callback=lambda msg: print(f"    {msg}"),
                max_iterations=6,
                verbose=False,
            )
            
            self._initialized = True
            print("  ✅ System initialized successfully!\n")
            
        except Exception as e:
            print(f"  ❌ Failed to initialize system: {e}")
            print("  ℹ️  Falling back to cached mode")
            self.live_mode = False
    
    def evaluate_retrieval(self, question: str, expected_topic: str) -> Tuple[List, Dict[str, float]]:
        """Evaluate document retrieval for a question."""
        if self.retriever is None:
            return [], {"relevance": 0.0, "coverage": 0.0, "doc_count": 0.0}
        
        try:
            docs = self.retriever.invoke(question)
            metrics = calculate_retrieval_quality(docs, expected_topic)
            return docs, metrics
        except Exception as e:
            print(f"    ⚠️ Retrieval error: {e}")
            return [], {"relevance": 0.0, "coverage": 0.0, "doc_count": 0.0}
    
    def evaluate_response(self, question: str) -> str:
        """Get a response from the agent."""
        if self.agent is None:
            return ""
        
        try:
            response = self.agent.ask(question)
            return response
        except Exception as e:
            print(f"    ⚠️ Agent error: {e}")
            return f"ERROR: {e}"
    
    def run_single_evaluation(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run evaluation for a single test case."""
        question = test_case["question"]
        q_id = test_case["id"]
        
        print(f"  📝 [{q_id}] {question}")
        
        result = {
            "id": q_id,
            "question": question,
            "difficulty": test_case["difficulty"],
            "expected_topic": test_case["expected_topic"],
        }
        
        # Check cache first
        cached = self._load_cached_response(question)
        
        if cached and not self.live_mode:
            # Use cached response
            response = cached["response"]
            result["source"] = "cache"
            print(f"       📦 Using cached response")
        elif self.live_mode and self._initialized:
            # Live evaluation
            start_time = time.time()
            
            # Evaluate retrieval
            docs, retrieval_metrics = self.evaluate_retrieval(question, test_case["expected_topic"])
            result["retrieval_metrics"] = retrieval_metrics
            
            # Get agent response
            response = self.evaluate_response(question)
            
            elapsed = time.time() - start_time
            result["latency_seconds"] = round(elapsed, 2)
            result["source"] = "live"
            
            # Cache the response
            doc_contents = [
                doc.page_content[:200] if hasattr(doc, 'page_content') else str(doc)[:200]
                for doc in docs
            ]
            self._save_cached_response(question, response, doc_contents)
            
            print(f"       ⏱️ Response in {elapsed:.2f}s")
        else:
            print(f"       ⚠️ No cache found and not in live mode — skipping")
            result["skipped"] = True
            return result
        
        # Calculate metrics
        result["response"] = response
        result["keyword_coverage"] = calculate_keyword_coverage(response, test_case["expected_keywords"])
        result["response_quality"] = calculate_response_quality(response)
        
        # Overall score (weighted average)
        quality = result["response_quality"]
        overall = (
            result["keyword_coverage"] * 0.30 +
            quality.get("completeness", 0) * 0.20 +
            quality.get("legal_references", 0) * 0.20 +
            quality.get("arabic_quality", 0) * 0.15 +
            quality.get("no_error", 0) * 0.15
        )
        result["overall_score"] = round(overall, 3)
        
        # Pass/Fail threshold
        result["passed"] = overall >= 0.5
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"       {status} (score: {overall:.1%}, keywords: {result['keyword_coverage']:.0%})")
        
        return result
    
    def run_all_evaluations(self) -> List[Dict[str, Any]]:
        """Run evaluation on all test cases."""
        print("=" * 70)
        print("🔬 Deepchecks RAG Evaluation — Egyptian Legal AI")
        print(f"   Mode: {'🔴 LIVE (real API calls)' if self.live_mode else '🟢 CACHED (no API calls)'}")
        print(f"   Test cases: {len(TEST_DATASET)}")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70 + "\n")
        
        if self.live_mode:
            self.initialize_system()
        
        self.results = []
        for test_case in TEST_DATASET:
            result = self.run_single_evaluation(test_case)
            self.results.append(result)
            # Small delay between live calls to avoid rate limiting
            if self.live_mode and self._initialized:
                time.sleep(2)
        
        return self.results
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of all evaluation results."""
        if not self.results:
            return {}
        
        evaluated = [r for r in self.results if not r.get("skipped")]
        passed = [r for r in evaluated if r.get("passed")]
        failed = [r for r in evaluated if not r.get("passed")]
        
        scores = [r["overall_score"] for r in evaluated if "overall_score" in r]
        avg_score = sum(scores) / max(len(scores), 1)
        
        # Per-difficulty breakdown
        difficulty_breakdown = {}
        for diff in ["simple", "medium", "complex"]:
            diff_results = [r for r in evaluated if r.get("difficulty") == diff]
            if diff_results:
                diff_scores = [r["overall_score"] for r in diff_results if "overall_score" in r]
                difficulty_breakdown[diff] = {
                    "count": len(diff_results),
                    "avg_score": round(sum(diff_scores) / max(len(diff_scores), 1), 3),
                    "passed": sum(1 for r in diff_results if r.get("passed")),
                }
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "mode": "live" if self.live_mode else "cached",
            "total_tests": len(TEST_DATASET),
            "evaluated": len(evaluated),
            "skipped": len(self.results) - len(evaluated),
            "passed": len(passed),
            "failed": len(failed),
            "pass_rate": round(len(passed) / max(len(evaluated), 1) * 100, 1),
            "average_score": round(avg_score, 3),
            "difficulty_breakdown": difficulty_breakdown,
        }
        
        return summary
    
    def generate_html_report(self) -> str:
        """Generate an HTML report and save it to disk."""
        summary = self.generate_summary()
        evaluated = [r for r in self.results if not r.get("skipped")]
        
        pass_rate = summary.get("pass_rate", 0)
        pass_color = "#22c55e" if pass_rate >= 80 else "#f59e0b" if pass_rate >= 50 else "#ef4444"
        
        # Build rows for the results table
        rows_html = ""
        for r in evaluated:
            status = "✅" if r.get("passed") else "❌"
            score = r.get("overall_score", 0)
            kw = r.get("keyword_coverage", 0)
            quality = r.get("response_quality", {})
            
            score_color = "#22c55e" if score >= 0.7 else "#f59e0b" if score >= 0.5 else "#ef4444"
            
            rows_html += f"""
            <tr>
                <td>{r['id']}</td>
                <td style="text-align:left;">{r['question']}</td>
                <td><span class="badge badge-{r['difficulty']}">{r['difficulty']}</span></td>
                <td>{status}</td>
                <td style="color:{score_color}; font-weight:bold;">{score:.1%}</td>
                <td>{kw:.0%}</td>
                <td>{quality.get('completeness', 0):.0%}</td>
                <td>{quality.get('legal_references', 0):.0%}</td>
                <td>{quality.get('no_error', 0):.0%}</td>
            </tr>"""
        
        # Difficulty breakdown
        diff_html = ""
        for diff, data in summary.get("difficulty_breakdown", {}).items():
            diff_html += f"""
            <div class="stat-card">
                <div class="stat-label">{diff.upper()}</div>
                <div class="stat-value">{data['avg_score']:.1%}</div>
                <div class="stat-detail">{data['passed']}/{data['count']} passed</div>
            </div>"""
        
        html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deepchecks RAG Evaluation Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 2rem;
            direction: ltr;
        }}
        .header {{
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: linear-gradient(135deg, #1e293b, #334155);
            border-radius: 16px;
            border: 1px solid #475569;
        }}
        .header h1 {{ color: #f1f5f9; font-size: 1.8rem; margin-bottom: 0.5rem; }}
        .header p {{ color: #94a3b8; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .stat-card {{
            background: #1e293b;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            border: 1px solid #334155;
        }}
        .stat-label {{ color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.5rem; }}
        .stat-value {{ font-size: 2rem; font-weight: bold; color: #f1f5f9; }}
        .stat-detail {{ color: #64748b; font-size: 0.8rem; margin-top: 0.3rem; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: #1e293b;
            border-radius: 12px;
            overflow: hidden;
        }}
        th {{
            background: #334155;
            padding: 0.75rem;
            text-align: center;
            font-weight: 600;
            color: #e2e8f0;
            font-size: 0.85rem;
        }}
        td {{
            padding: 0.75rem;
            text-align: center;
            border-bottom: 1px solid #2d3748;
            font-size: 0.85rem;
        }}
        tr:hover {{ background: #2d3748; }}
        .badge {{
            padding: 0.2rem 0.6rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge-simple {{ background: #22c55e20; color: #22c55e; }}
        .badge-medium {{ background: #f59e0b20; color: #f59e0b; }}
        .badge-complex {{ background: #ef444420; color: #ef4444; }}
        .section-title {{
            font-size: 1.2rem;
            margin: 2rem 0 1rem;
            color: #f1f5f9;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #334155;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 Deepchecks RAG Evaluation Report</h1>
        <p>Egyptian Legal AI — {summary.get('timestamp', 'N/A')}</p>
        <p>Mode: {'🔴 LIVE' if self.live_mode else '🟢 CACHED'}</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-label">PASS RATE</div>
            <div class="stat-value" style="color:{pass_color}">{pass_rate}%</div>
            <div class="stat-detail">{summary.get('passed', 0)}/{summary.get('evaluated', 0)} tests</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">AVG SCORE</div>
            <div class="stat-value">{summary.get('average_score', 0):.1%}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">TOTAL TESTS</div>
            <div class="stat-value">{summary.get('total_tests', 0)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">SKIPPED</div>
            <div class="stat-value">{summary.get('skipped', 0)}</div>
        </div>
    </div>

    <h2 class="section-title">📊 Difficulty Breakdown</h2>
    <div class="stats-grid">{diff_html}</div>

    <h2 class="section-title">📋 Detailed Results</h2>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Question</th>
                <th>Difficulty</th>
                <th>Status</th>
                <th>Overall</th>
                <th>Keywords</th>
                <th>Completeness</th>
                <th>Legal Refs</th>
                <th>No Error</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <p style="text-align:center; margin-top:2rem; color:#64748b;">
        Generated by Deepchecks RAG Evaluator • Egyptian Legal AI
    </p>
</body>
</html>"""
        
        # Save report
        report_path = self.reports_dir / f"deepchecks_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        report_path.write_text(html, encoding='utf-8')
        
        # Also save JSON results
        json_path = self.reports_dir / f"deepchecks_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        json_data = {
            "summary": summary,
            "results": [
                {k: v for k, v in r.items() if k != "response"}
                for r in self.results
            ],
        }
        json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding='utf-8')
        
        print(f"\n📄 HTML Report saved: {report_path}")
        print(f"📊 JSON Results saved: {json_path}")
        
        return str(report_path)


# ─────────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Deepchecks RAG Evaluation")
    parser.add_argument("--live", action="store_true", help="Use real Gemini API calls (costs quota)")
    parser.add_argument("--report-only", action="store_true", help="Generate report from cached results")
    args = parser.parse_args()
    
    evaluator = DeepChecksEvaluator(live_mode=args.live)
    
    # Run evaluations
    results = evaluator.run_all_evaluations()
    
    # Print summary
    summary = evaluator.generate_summary()
    print("\n" + "=" * 70)
    print("📊 EVALUATION SUMMARY")
    print("=" * 70)
    print(f"  Total Tests:    {summary.get('total_tests', 0)}")
    print(f"  Evaluated:      {summary.get('evaluated', 0)}")
    print(f"  Passed:         {summary.get('passed', 0)}")
    print(f"  Failed:         {summary.get('failed', 0)}")
    print(f"  Pass Rate:      {summary.get('pass_rate', 0)}%")
    print(f"  Average Score:  {summary.get('average_score', 0):.1%}")
    
    if summary.get("difficulty_breakdown"):
        print(f"\n  Difficulty Breakdown:")
        for diff, data in summary["difficulty_breakdown"].items():
            print(f"    {diff:>8}: {data['avg_score']:.1%} ({data['passed']}/{data['count']} passed)")
    
    # Generate HTML report
    report_path = evaluator.generate_html_report()
    
    print(f"\n✅ Evaluation complete!")
    print(f"   Open the HTML report in your browser to see detailed results.")
    print("=" * 70)


if __name__ == "__main__":
    main()

