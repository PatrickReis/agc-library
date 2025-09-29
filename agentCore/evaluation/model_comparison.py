"""
Model comparison framework for evaluating different LLM providers
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd

from ..logger.logger import get_logger
from ..providers.llm_providers import get_llm, get_provider_info
from .prompt_evaluator import PromptEvaluator, EvalSummary

logger = get_logger("model_comparison")

@dataclass
class ModelResult:
    """Result for a single model"""
    provider: str
    model_info: Dict[str, Any]
    eval_summary: EvalSummary
    avg_latency_ms: float
    total_cost_estimate: float
    error_rate: float

@dataclass
class ComparisonResult:
    """Result of model comparison"""
    models: List[ModelResult]
    best_model: str
    best_score: float
    comparison_metrics: Dict[str, Any]
    timestamp: float

class ModelComparator:
    """
    Compare multiple LLM providers on the same tasks
    """

    def __init__(self,
                 providers: List[str],
                 cost_per_1k_tokens: Optional[Dict[str, float]] = None):
        """
        Initialize model comparator

        Args:
            providers: List of provider names to compare
            cost_per_1k_tokens: Cost estimates per provider (optional)
        """
        self.providers = providers
        self.cost_per_1k_tokens = cost_per_1k_tokens or self._default_costs()
        self.evaluators = {}

        # Initialize evaluators for each provider
        for provider in providers:
            try:
                self.evaluators[provider] = PromptEvaluator(llm_provider=provider)
                logger.info(f"✅ Initialized evaluator for {provider}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {provider}: {e}")

    def _default_costs(self) -> Dict[str, float]:
        """Default cost estimates per 1K tokens (approximate)"""
        return {
            "bedrock": 0.008,  # Claude-3 Sonnet
            "openai": 0.002,   # GPT-3.5-turbo
            "ollama": 0.0,     # Local models
            "gemini": 0.001    # Gemini Flash
        }

    def compare_on_dataset(self,
                          dataset: List[Dict[str, str]],
                          eval_type: str = "semantic_similarity",
                          include_latency: bool = True,
                          save_results: bool = True) -> ComparisonResult:
        """
        Compare all models on the same dataset

        Args:
            dataset: List of test cases
            eval_type: Evaluation method
            include_latency: Whether to measure response latency
            save_results: Whether to save detailed results

        Returns:
            ComparisonResult with model rankings
        """
        logger.info(f"🔥 Starting model comparison with {len(self.providers)} providers")

        model_results = []

        for provider in self.providers:
            if provider not in self.evaluators:
                logger.warning(f"Skipping {provider} - evaluator not available")
                continue

            logger.info(f"🧪 Evaluating {provider}...")

            start_time = time.time()

            # Run evaluation
            evaluator = self.evaluators[provider]
            eval_summary = evaluator.evaluate_dataset(
                dataset=dataset,
                eval_type=eval_type,
                save_results=save_results,
                output_path=f"comparison_{provider}_{int(time.time())}.json"
            )

            end_time = time.time()

            # Calculate metrics
            avg_latency = sum([r.latency_ms for r in evaluator.evaluate_single(
                prompt=sample["prompt"],
                expected=sample["expected"],
                eval_type=eval_type
            ) for sample in dataset[:5]]) / min(5, len(dataset))  # Sample first 5 for latency

            error_rate = eval_summary.failed_samples / eval_summary.total_samples

            # Estimate cost
            total_tokens = self._estimate_tokens(dataset)
            cost_estimate = (total_tokens / 1000) * self.cost_per_1k_tokens.get(provider, 0.0)

            # Get model info
            try:
                model_info = get_provider_info(provider)
            except:
                model_info = {"provider": provider}

            model_result = ModelResult(
                provider=provider,
                model_info=model_info,
                eval_summary=eval_summary,
                avg_latency_ms=avg_latency,
                total_cost_estimate=cost_estimate,
                error_rate=error_rate
            )

            model_results.append(model_result)

            logger.success(f"✅ {provider}: Score {eval_summary.avg_score:.3f}, "
                         f"Latency {avg_latency:.0f}ms, Errors {error_rate:.2%}")

        # Determine best model (highest score with reasonable latency)
        best_model = self._determine_best_model(model_results)

        # Calculate comparison metrics
        comparison_metrics = self._calculate_comparison_metrics(model_results)

        result = ComparisonResult(
            models=model_results,
            best_model=best_model,
            best_score=max([m.eval_summary.avg_score for m in model_results]) if model_results else 0.0,
            comparison_metrics=comparison_metrics,
            timestamp=time.time()
        )

        if save_results:
            self._save_comparison_results(result)

        self._print_comparison_summary(result)

        return result

    def _estimate_tokens(self, dataset: List[Dict[str, str]]) -> int:
        """Rough token estimation"""
        total_chars = sum(len(sample["prompt"]) + len(sample.get("expected", "")) for sample in dataset)
        return total_chars // 4  # Rough approximation: 4 chars per token

    def _determine_best_model(self, results: List[ModelResult]) -> str:
        """Determine best model based on score, latency, and cost"""
        if not results:
            return "none"

        # Weighted scoring: 70% accuracy, 20% latency, 10% cost
        scored_models = []

        max_score = max([r.eval_summary.avg_score for r in results])
        min_latency = min([r.avg_latency_ms for r in results if r.avg_latency_ms > 0]) or 1
        min_cost = min([r.total_cost_estimate for r in results]) or 0.001

        for result in results:
            # Normalize metrics (higher is better)
            score_norm = result.eval_summary.avg_score / max_score if max_score > 0 else 0
            latency_norm = min_latency / max(result.avg_latency_ms, 1)  # Invert for latency
            cost_norm = min_cost / max(result.total_cost_estimate, 0.001)  # Invert for cost

            # Weighted score
            combined_score = (score_norm * 0.7) + (latency_norm * 0.2) + (cost_norm * 0.1)

            scored_models.append((result.provider, combined_score))

        # Return best model
        best = max(scored_models, key=lambda x: x[1])
        return best[0]

    def _calculate_comparison_metrics(self, results: List[ModelResult]) -> Dict[str, Any]:
        """Calculate aggregate comparison metrics"""
        if not results:
            return {}

        scores = [r.eval_summary.avg_score for r in results]
        latencies = [r.avg_latency_ms for r in results]
        costs = [r.total_cost_estimate for r in results]

        return {
            "score_range": max(scores) - min(scores),
            "avg_score": sum(scores) / len(scores),
            "score_std": pd.Series(scores).std(),
            "latency_range_ms": max(latencies) - min(latencies),
            "avg_latency_ms": sum(latencies) / len(latencies),
            "total_cost_range": max(costs) - min(costs),
            "avg_cost": sum(costs) / len(costs),
            "providers_tested": len(results)
        }

    def _save_comparison_results(self, result: ComparisonResult):
        """Save comparison results to file"""
        timestamp = int(result.timestamp)
        output_path = f"model_comparison_{timestamp}.json"

        # Convert to serializable format
        output_data = {
            "comparison_summary": {
                "best_model": result.best_model,
                "best_score": result.best_score,
                "timestamp": result.timestamp,
                "metrics": result.comparison_metrics
            },
            "model_results": []
        }

        for model_result in result.models:
            model_data = asdict(model_result)
            # Convert EvalSummary to dict
            model_data["eval_summary"] = asdict(model_result.eval_summary)
            output_data["model_results"].append(model_data)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        # Create CSV summary
        csv_data = []
        for model_result in result.models:
            csv_data.append({
                "provider": model_result.provider,
                "avg_score": model_result.eval_summary.avg_score,
                "avg_latency_ms": model_result.avg_latency_ms,
                "cost_estimate": model_result.total_cost_estimate,
                "error_rate": model_result.error_rate,
                "total_samples": model_result.eval_summary.total_samples
            })

        csv_path = f"model_comparison_{timestamp}.csv"
        pd.DataFrame(csv_data).to_csv(csv_path, index=False)

        logger.info(f"Comparison results saved to {output_path} and {csv_path}")

    def _print_comparison_summary(self, result: ComparisonResult):
        """Print a nice comparison summary"""
        print("\n" + "="*60)
        print("🏆 MODEL COMPARISON RESULTS")
        print("="*60)

        # Sort models by score
        sorted_models = sorted(result.models, key=lambda x: x.eval_summary.avg_score, reverse=True)

        for i, model_result in enumerate(sorted_models):
            rank = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."

            print(f"{rank} {model_result.provider.upper()}")
            print(f"   Score: {model_result.eval_summary.avg_score:.3f}")
            print(f"   Latency: {model_result.avg_latency_ms:.0f}ms")
            print(f"   Cost: ${model_result.total_cost_estimate:.4f}")
            print(f"   Error Rate: {model_result.error_rate:.2%}")
            print()

        print(f"🎯 BEST OVERALL: {result.best_model.upper()}")
        print(f"📊 Score Range: {result.comparison_metrics.get('score_range', 0):.3f}")
        print(f"⚡ Avg Latency: {result.comparison_metrics.get('avg_latency_ms', 0):.0f}ms")
        print("="*60)

    def benchmark_specific_tasks(self,
                                task_datasets: Dict[str, List[Dict[str, str]]],
                                eval_type: str = "semantic_similarity") -> Dict[str, ComparisonResult]:
        """
        Benchmark models on specific task types

        Args:
            task_datasets: Dict mapping task name to dataset
            eval_type: Evaluation method

        Returns:
            Dict mapping task name to comparison results
        """
        logger.info(f"🎯 Running task-specific benchmarks for {len(task_datasets)} tasks")

        results = {}

        for task_name, dataset in task_datasets.items():
            logger.info(f"📝 Benchmarking task: {task_name}")

            result = self.compare_on_dataset(
                dataset=dataset,
                eval_type=eval_type,
                save_results=True
            )

            results[task_name] = result

            print(f"\n📊 Best for {task_name}: {result.best_model} (Score: {result.best_score:.3f})")

        return results

    def quick_comparison(self,
                        prompts: List[str],
                        expected_outputs: List[str]) -> ComparisonResult:
        """
        Quick comparison with simple prompt/expected pairs

        Args:
            prompts: List of prompts to test
            expected_outputs: List of expected outputs

        Returns:
            ComparisonResult
        """
        if len(prompts) != len(expected_outputs):
            raise ValueError("Prompts and expected outputs must have same length")

        dataset = [
            {"prompt": prompt, "expected": expected}
            for prompt, expected in zip(prompts, expected_outputs)
        ]

        return self.compare_on_dataset(dataset, save_results=True)