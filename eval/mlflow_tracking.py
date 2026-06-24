"""
MLflow Experiment Tracking for Egyptian Legal AI
=================================================

Tracks and compares evaluation runs across different model configurations.
Logs metrics, parameters, and artifacts to the MLflow tracking server.

Usage:
    python eval/mlflow_tracking.py                    # Run evaluation + log to MLflow
    python eval/mlflow_tracking.py --ui               # Launch MLflow dashboard
    python eval/mlflow_tracking.py --compare           # Compare last N runs
    
Dashboard:
    After running, launch the dashboard:
        mlflow ui --backend-store-uri eval/mlruns
    Then open http://localhost:5000 in your browser.
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
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import mlflow
from mlflow.tracking import MlflowClient

# Configure MLflow to store runs locally using SQLite (MLflow 3.x requirement)
MLRUNS_DIR = PROJECT_ROOT / "eval" / "mlruns"
MLRUNS_DIR.mkdir(parents=True, exist_ok=True)
MLFLOW_DB = PROJECT_ROOT / "eval" / "mlflow.db"
TRACKING_URI = f"sqlite:///{MLFLOW_DB.as_posix()}"
mlflow.set_tracking_uri(TRACKING_URI)

# Experiment name
EXPERIMENT_NAME = "Egyptian-Legal-AI-Evaluation"


def get_or_create_experiment() -> str:
    """Get or create the MLflow experiment."""
    experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        experiment_id = mlflow.create_experiment(
            EXPERIMENT_NAME,
            tags={"project": "Egyptian Legal AI", "type": "RAG evaluation"},
        )
    else:
        experiment_id = experiment.experiment_id
    return experiment_id


class MLflowTracker:
    """
    Tracks RAG evaluation experiments using MLflow.
    
    Logs:
    - Model parameters (model name, temperature, top_k, etc.)
    - Quality metrics (accuracy, keyword coverage, completeness, etc.)
    - Performance metrics (latency, token usage)
    - Artifacts (evaluation reports, Q&A pairs)
    """
    
    def __init__(self):
        self.experiment_id = get_or_create_experiment()
        self.run = None
    
    def start_run(self, run_name: Optional[str] = None, tags: Optional[Dict] = None):
        """Start a new MLflow run."""
        if run_name is None:
            run_name = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.run = mlflow.start_run(
            experiment_id=self.experiment_id,
            run_name=run_name,
            tags=tags or {},
        )
        return self.run
    
    def log_model_config(self, config: Dict[str, Any]):
        """Log model configuration parameters."""
        params = {
            "model_name": config.get("model_name", "unknown"),
            "temperature": config.get("temperature", 0.1),
            "max_tokens": config.get("max_tokens", 4096),
            "top_p": config.get("top_p", 0.95),
            "top_k_documents": config.get("top_k_documents", 6),
            "chunk_size": config.get("chunk_size", 2000),
            "chunk_overlap": config.get("chunk_overlap", 200),
            "embedding_model": config.get("embedding_model", "BAAI/bge-m3"),
            "max_iterations": config.get("max_iterations", 6),
        }
        mlflow.log_params(params)
    
    def log_evaluation_results(self, results: List[Dict[str, Any]]):
        """Log evaluation results as metrics."""
        evaluated = [r for r in results if not r.get("skipped")]
        
        if not evaluated:
            return
        
        # Overall metrics
        scores = [r["overall_score"] for r in evaluated if "overall_score" in r]
        passed = sum(1 for r in evaluated if r.get("passed"))
        
        mlflow.log_metrics({
            "total_tests": len(results),
            "evaluated": len(evaluated),
            "passed": passed,
            "failed": len(evaluated) - passed,
            "pass_rate": round(passed / max(len(evaluated), 1) * 100, 1),
            "avg_overall_score": round(sum(scores) / max(len(scores), 1), 4),
            "min_score": round(min(scores) if scores else 0, 4),
            "max_score": round(max(scores) if scores else 0, 4),
        })
        
        # Per-metric averages
        metric_names = ["completeness", "structure", "legal_references", "arabic_quality", "no_error"]
        for metric_name in metric_names:
            values = [
                r.get("response_quality", {}).get(metric_name, 0)
                for r in evaluated
                if "response_quality" in r
            ]
            if values:
                mlflow.log_metric(f"avg_{metric_name}", round(sum(values) / len(values), 4))
        
        # Keyword coverage
        kw_values = [r.get("keyword_coverage", 0) for r in evaluated]
        if kw_values:
            mlflow.log_metric("avg_keyword_coverage", round(sum(kw_values) / len(kw_values), 4))
        
        # Latency metrics (if available)
        latencies = [r.get("latency_seconds", 0) for r in evaluated if r.get("latency_seconds")]
        if latencies:
            mlflow.log_metrics({
                "avg_latency_seconds": round(sum(latencies) / len(latencies), 2),
                "max_latency_seconds": round(max(latencies), 2),
                "min_latency_seconds": round(min(latencies), 2),
            })
        
        # Per-difficulty metrics
        for difficulty in ["simple", "medium", "complex"]:
            diff_results = [r for r in evaluated if r.get("difficulty") == difficulty]
            if diff_results:
                diff_scores = [r["overall_score"] for r in diff_results if "overall_score" in r]
                diff_passed = sum(1 for r in diff_results if r.get("passed"))
                mlflow.log_metrics({
                    f"{difficulty}_avg_score": round(sum(diff_scores) / max(len(diff_scores), 1), 4),
                    f"{difficulty}_pass_rate": round(diff_passed / max(len(diff_results), 1) * 100, 1),
                })
        
        # Per-question scores (logged as individual metrics for tracking over time)
        for r in evaluated:
            if "overall_score" in r:
                mlflow.log_metric(f"q_{r['id']}_score", r["overall_score"])
    
    def log_qa_artifact(self, results: List[Dict[str, Any]]):
        """Log Q&A pairs as an artifact for review."""
        artifact_dir = PROJECT_ROOT / "eval" / "artifacts"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a readable Q&A summary
        qa_lines = []
        for r in results:
            if r.get("skipped"):
                continue
            status = "✅ PASS" if r.get("passed") else "❌ FAIL"
            qa_lines.append(f"{'='*60}")
            qa_lines.append(f"[{r['id']}] {status} (Score: {r.get('overall_score', 0):.1%})")
            qa_lines.append(f"Question: {r['question']}")
            qa_lines.append(f"Topic: {r.get('expected_topic', 'N/A')}")
            qa_lines.append(f"Difficulty: {r.get('difficulty', 'N/A')}")
            qa_lines.append(f"Keyword Coverage: {r.get('keyword_coverage', 0):.0%}")
            if r.get("response"):
                # Truncate long responses
                resp = r["response"][:500] + ("..." if len(r["response"]) > 500 else "")
                qa_lines.append(f"Response:\n{resp}")
            qa_lines.append("")
        
        qa_path = artifact_dir / f"qa_pairs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        qa_path.write_text("\n".join(qa_lines), encoding='utf-8')
        
        mlflow.log_artifact(str(qa_path))
    
    def log_report_artifact(self, report_path: str):
        """Log the HTML report as an artifact."""
        if Path(report_path).exists():
            mlflow.log_artifact(report_path)
    
    def end_run(self):
        """End the current MLflow run."""
        if self.run:
            mlflow.end_run()
            self.run = None


def run_tracked_evaluation(live_mode: bool = False):
    """Run the full evaluation with MLflow tracking."""
    from eval.deepchecks_eval import DeepChecksEvaluator
    
    # Initialize tracker
    tracker = MLflowTracker()
    
    # Load model config from settings
    try:
        from src.config.settings import MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_DOCUMENTS
        model_config = {
            "model_name": MODEL_NAME,
            "temperature": 0.1,
            "max_tokens": 4096,
            "top_p": 0.95,
            "top_k_documents": TOP_K_DOCUMENTS,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "embedding_model": "BAAI/bge-m3",
            "max_iterations": 6,
        }
    except ImportError:
        model_config = {
            "model_name": "unknown",
            "temperature": 0.1,
            "max_tokens": 4096,
        }
    
    # Start MLflow run
    run_tags = {
        "mode": "live" if live_mode else "cached",
        "project": "Egyptian Legal AI",
        "evaluator": "deepchecks",
    }
    tracker.start_run(
        run_name=f"{'live' if live_mode else 'cached'}_{datetime.now().strftime('%H%M%S')}",
        tags=run_tags,
    )
    
    print("\n" + "=" * 70)
    print("📊 MLflow Tracked Evaluation")
    print(f"   Experiment: {EXPERIMENT_NAME}")
    print(f"   Tracking URI: {mlflow.get_tracking_uri()}")
    print("=" * 70 + "\n")
    
    try:
        # Log model configuration
        tracker.log_model_config(model_config)
        
        # Run Deepchecks evaluation
        evaluator = DeepChecksEvaluator(live_mode=live_mode)
        results = evaluator.run_all_evaluations()
        
        # Log results to MLflow
        tracker.log_evaluation_results(results)
        
        # Log artifacts
        tracker.log_qa_artifact(results)
        
        # Generate and log HTML report
        report_path = evaluator.generate_html_report()
        tracker.log_report_artifact(report_path)
        
        # Print summary
        summary = evaluator.generate_summary()
        print("\n" + "=" * 70)
        print("📊 MLflow TRACKING COMPLETE")
        print("=" * 70)
        print(f"  Run ID: {tracker.run.info.run_id}")
        print(f"  Pass Rate: {summary.get('pass_rate', 0)}%")
        print(f"  Avg Score: {summary.get('average_score', 0):.1%}")
        print(f"\n  🌐 To view the dashboard, run:")
        print(f"     mlflow ui --backend-store-uri \"{TRACKING_URI}\"")
        print(f"     Then open http://localhost:5000")
        print("=" * 70)
        
    finally:
        tracker.end_run()


def compare_runs(n_runs: int = 5):
    """Compare the last N evaluation runs."""
    client = MlflowClient(tracking_uri=TRACKING_URI)
    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    
    if experiment is None:
        print("❌ No experiment found. Run an evaluation first.")
        return
    
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["start_time DESC"],
        max_results=n_runs,
    )
    
    if not runs:
        print("❌ No runs found. Run an evaluation first.")
        return
    
    print("\n" + "=" * 90)
    print(f"📊 Last {len(runs)} Evaluation Runs Comparison")
    print("=" * 90)
    
    # Header
    print(f"{'Run Name':<25} {'Date':<20} {'Pass Rate':<12} {'Avg Score':<12} {'Mode':<8}")
    print("-" * 90)
    
    for run in runs:
        name = run.info.run_name or "unnamed"
        date = datetime.fromtimestamp(run.info.start_time / 1000).strftime("%Y-%m-%d %H:%M")
        pass_rate = run.data.metrics.get("pass_rate", 0)
        avg_score = run.data.metrics.get("avg_overall_score", 0)
        mode = run.data.tags.get("mode", "unknown")
        
        print(f"{name:<25} {date:<20} {pass_rate:<12.1f}% {avg_score:<12.1%} {mode:<8}")
    
    print("=" * 90)
    print(f"\n🌐 For detailed comparison, run: mlflow ui --backend-store-uri \"{TRACKING_URI}\"")


def launch_ui():
    """Launch the MLflow UI dashboard."""
    import subprocess
    print(f"🌐 Launching MLflow UI...")
    print(f"   Tracking URI: {TRACKING_URI}")
    print(f"   Open http://localhost:5000 in your browser")
    print(f"   Press Ctrl+C to stop\n")
    
    subprocess.run(
        [sys.executable, "-m", "mlflow", "ui", 
         "--backend-store-uri", TRACKING_URI,
         "--host", "127.0.0.1",
         "--port", "5000"],
        cwd=str(PROJECT_ROOT),
    )


# ─────────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="MLflow Experiment Tracking for Egyptian Legal AI")
    parser.add_argument("--live", action="store_true", help="Use real Gemini API calls")
    parser.add_argument("--ui", action="store_true", help="Launch MLflow dashboard")
    parser.add_argument("--compare", action="store_true", help="Compare last N runs")
    parser.add_argument("--n-runs", type=int, default=5, help="Number of runs to compare")
    args = parser.parse_args()
    
    if args.ui:
        launch_ui()
    elif args.compare:
        compare_runs(args.n_runs)
    else:
        run_tracked_evaluation(live_mode=args.live)


if __name__ == "__main__":
    main()
