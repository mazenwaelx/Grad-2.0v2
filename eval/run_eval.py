"""
Unified Evaluation Runner for Egyptian Legal AI
=================================================

Single entry point to run all evaluation tools:
- Deepchecks: RAG quality evaluation
- MLflow: Experiment tracking
- Playwright: E2E browser automation tests

Usage:
    python eval/run_eval.py --all              # Run everything
    python eval/run_eval.py --deepchecks       # Only Deepchecks
    python eval/run_eval.py --mlflow           # Only MLflow tracking
    python eval/run_eval.py --playwright       # Only Playwright E2E tests
    python eval/run_eval.py --live             # Use real API calls (adds to any mode)
    python eval/run_eval.py --headed           # Show browser (Playwright only)
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
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def print_banner():
    """Print a nice banner."""
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     🔬 Egyptian Legal AI — Evaluation Suite                 ║")
    print("║     Deepchecks • MLflow • Playwright                       ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║     Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<48} ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()


def run_deepchecks(live: bool = False):
    """Run Deepchecks RAG evaluation."""
    print("\n" + "━" * 60)
    print("🔬 Running Deepchecks RAG Evaluation...")
    print("━" * 60 + "\n")
    
    try:
        from eval.deepchecks_eval import DeepChecksEvaluator
        
        evaluator = DeepChecksEvaluator(live_mode=live)
        results = evaluator.run_all_evaluations()
        
        summary = evaluator.generate_summary()
        report_path = evaluator.generate_html_report()
        
        print(f"\n  📊 Pass Rate: {summary.get('pass_rate', 0)}%")
        print(f"  📊 Avg Score: {summary.get('average_score', 0):.1%}")
        print(f"  📄 Report: {report_path}")
        
        return True, summary
        
    except Exception as e:
        print(f"\n  ❌ Deepchecks evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


def run_mlflow(live: bool = False):
    """Run MLflow tracked evaluation."""
    print("\n" + "━" * 60)
    print("📊 Running MLflow Tracked Evaluation...")
    print("━" * 60 + "\n")
    
    try:
        from eval.mlflow_tracking import run_tracked_evaluation
        
        run_tracked_evaluation(live_mode=live)
        
        print(f"\n  🌐 Dashboard: mlflow ui --backend-store-uri eval/mlruns")
        print(f"     Open http://localhost:5000")
        
        return True
        
    except Exception as e:
        print(f"\n  ❌ MLflow tracking failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_playwright(headed: bool = False, screenshots: bool = True):
    """Run Playwright E2E tests."""
    print("\n" + "━" * 60)
    print("🎭 Running Playwright E2E Tests...")
    print("━" * 60 + "\n")
    
    try:
        from eval.playwright_tests import run_tests
        
        exit_code = run_tests(
            headed=headed,
            save_screenshots=screenshots,
        )
        
        return exit_code == 0
        
    except Exception as e:
        print(f"\n  ❌ Playwright tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Unified Evaluation Runner for Egyptian Legal AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python eval/run_eval.py --all                Run all evaluations
  python eval/run_eval.py --deepchecks         Run only Deepchecks
  python eval/run_eval.py --mlflow --live      Run MLflow with real API calls
  python eval/run_eval.py --playwright --headed Run Playwright with visible browser
        """,
    )
    
    parser.add_argument("--all", action="store_true", help="Run all evaluations")
    parser.add_argument("--deepchecks", action="store_true", help="Run Deepchecks evaluation")
    parser.add_argument("--mlflow", action="store_true", help="Run MLflow tracked evaluation")
    parser.add_argument("--playwright", action="store_true", help="Run Playwright E2E tests")
    parser.add_argument("--live", action="store_true", help="Use real Gemini API calls (costs quota)")
    parser.add_argument("--headed", action="store_true", help="Run Playwright with visible browser")
    parser.add_argument("--no-screenshots", action="store_true", help="Disable Playwright screenshots")
    
    args = parser.parse_args()
    
    # Default to --all if nothing specified
    if not any([args.all, args.deepchecks, args.mlflow, args.playwright]):
        args.all = True
    
    print_banner()
    
    results = {}
    
    # ── Deepchecks ──
    if args.all or args.deepchecks:
        success, summary = run_deepchecks(live=args.live)
        results["deepchecks"] = "✅ PASSED" if success else "❌ FAILED"
    
    # ── MLflow ──
    if args.all or args.mlflow:
        success = run_mlflow(live=args.live)
        results["mlflow"] = "✅ PASSED" if success else "❌ FAILED"
    
    # ── Playwright ──
    if args.all or args.playwright:
        success = run_playwright(
            headed=args.headed,
            screenshots=not args.no_screenshots,
        )
        results["playwright"] = "✅ PASSED" if success else "❌ FAILED"
    
    # ── Final Summary ──
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + "  📋 FINAL EVALUATION SUMMARY".ljust(58) + "║")
    print("╠" + "═" * 58 + "╣")
    for tool, status in results.items():
        line = f"  {tool:<20} {status}"
        print("║" + line.ljust(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()


if __name__ == "__main__":
    main()
