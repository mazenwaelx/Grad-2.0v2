"""
Comprehensive Test Runner for Egyptian Legal AI
================================================

Runs all test suites:
- Unit Tests
- Integration Tests
- Mock Tests
- System Tests
- Functional Tests
- Security Tests
- Usability Tests
- Playwright E2E Tests
- Deepchecks RAG Evaluation
- MLflow Tracking

Usage:
    python eval/run_all_tests.py                 # Run all tests
    python eval/run_all_tests.py --quick         # Skip slow tests (Playwright, Deepchecks)
    python eval/run_all_tests.py --generate-report  # Generate comprehensive PDF report
"""

import sys
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

import os
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def print_banner():
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " 🔬 Egyptian Legal AI - Comprehensive Test Suite ".center(68) + "║")
    print("╠" + "═" * 68 + "╣")
    print("║" + f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ".center(68) + "║")
    print("╚" + "═" * 68 + "╝\n")


def run_test_suite(name, module_name, quick_mode=False):
    """Run a test suite and return success status"""
    print(f"\n{'='*70}")
    print(f"Running: {name}")
    print(f"{'='*70}")
    
    try:
        # Special handling for different test modules
        if module_name == "playwright_tests":
            # Playwright has a different structure - call run_tests directly
            module = __import__(f"eval.{module_name}", fromlist=[module_name])
            exit_code = module.run_tests(headed=False, save_screenshots=False)
            return exit_code == 0, name
        elif module_name == "deepchecks_eval":
            # Deepchecks uses DeepChecksEvaluator
            module = __import__(f"eval.{module_name}", fromlist=[module_name])
            evaluator = module.DeepChecksEvaluator(live_mode=False)
            evaluator.run_all_evaluations()
            summary = evaluator.generate_summary()
            evaluator.generate_html_report()
            return summary.get('pass_rate', 0) >= 90, name
        else:
            # Standard test suite classes
            class_name_map = {
                "unit_tests": "UnitTestSuite",
                "integration_tests": "IntegrationTestSuite",
                "mock_tests": "MockTestSuite",
                "functional_tests": "FunctionalTestSuite",
                "system_tests": "SystemTestSuite",
                "security_tests": "SecurityTestSuite",
                "usability_tests": "UsabilityTestSuite",
            }
            
            module = __import__(f"eval.{module_name}", fromlist=[module_name])
            suite_class = getattr(module, class_name_map.get(module_name, f"{module_name.title().replace('_', '')}Suite"))
            suite = suite_class()
            success = suite.run_all()
            return success, name
    except Exception as e:
        print(f"❌ Failed to run {name}: {e}")
        import traceback
        traceback.print_exc()
        return False, name


def main():
    parser = argparse.ArgumentParser(
        description="Run comprehensive test suite for Egyptian Legal AI"
    )
    parser.add_argument("--quick", action="store_true", help="Skip slow tests")
    parser.add_argument("--generate-report", action="store_true", help="Generate PDF report after tests")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    parser.add_argument("--e2e-only", action="store_true", help="Run only E2E tests")
    
    args = parser.parse_args()
    
    print_banner()
    
    start_time = time.time()
    results = {}
    
    # Define test suites
    if args.unit_only:
        suites = [
            ("Unit Tests", "unit_tests", False),
        ]
    elif args.integration_only:
        suites = [
            ("Integration Tests", "integration_tests", False),
        ]
    elif args.e2e_only:
        suites = [
            ("Playwright E2E Tests", "playwright_tests", True),
            ("Deepchecks RAG Evaluation", "deepchecks_eval", True),
        ]
    else:
        suites = [
            ("Unit Tests", "unit_tests", False),
            ("Mock Tests", "mock_tests", False),
            ("Integration Tests", "integration_tests", False),
            ("Functional Tests", "functional_tests", False),
            ("Security Tests", "security_tests", False),
            ("Usability Tests", "usability_tests", False),
            ("System Tests", "system_tests", False),
        ]
        
        # Add slow tests if not in quick mode
        if not args.quick:
            suites.extend([
                ("Playwright E2E Tests", "playwright_tests", True),
                ("Deepchecks RAG Evaluation", "deepchecks_eval", True),
            ])
    
    # Run all test suites
    for name, module, is_slow in suites:
        if args.quick and is_slow:
            print(f"\n⏩ Skipping {name} (quick mode)")
            results[name] = "SKIPPED"
            continue
        
        success, test_name = run_test_suite(name, module, args.quick)
        results[name] = "✅ PASSED" if success else "❌ FAILED"
    
    # Print final summary
    elapsed = time.time() - start_time
    
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " 📊 FINAL TEST SUMMARY ".center(68) + "║")
    print("╠" + "═" * 68 + "╣")
    
    for test_name, status in results.items():
        line = f"  {test_name:<45} {status}"
        print("║" + line.ljust(68) + "║")
    
    print("╠" + "═" * 68 + "╣")
    
    total = len([r for r in results.values() if r != "SKIPPED"])
    passed = len([r for r in results.values() if r == "✅ PASSED"])
    failed = len([r for r in results.values() if r == "❌ FAILED"])
    skipped = len([r for r in results.values() if r == "SKIPPED"])
    
    print("║" + f"  Total Test Suites: {total:<46}  ║")
    print("║" + f"  Passed: {passed:<54}  ║")
    print("║" + f"  Failed: {failed:<54}  ║")
    print("║" + f"  Skipped: {skipped:<53}  ║")
    print("║" + f"  Success Rate: {(passed/max(total,1))*100:.1f}%{' '*45}  ║")
    print("║" + f"  Total Time: {elapsed:.1f}s{' '*50}  ║")
    print("╚" + "═" * 68 + "╝\n")
    
    # Generate report if requested
    if args.generate_report:
        print("\n📄 Generating comprehensive PDF report...")
        try:
            from eval.generate_report import build_report
            build_report()
            print("✅ Report generated successfully!")
        except Exception as e:
            print(f"❌ Failed to generate report: {e}")
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
