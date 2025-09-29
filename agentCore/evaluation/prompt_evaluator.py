"""
Prompt evaluation framework using OpenAI/evals style approach
"""

import json
import time
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd

from ..logger.logger import get_logger
from ..providers.llm_providers import get_llm

logger = get_logger("prompt_evaluator")

@dataclass
class EvalResult:
    """Result of a single evaluation"""
    prompt: str
    expected: str
    actual: str
    score: float
    metrics: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: float
    latency_ms: float

@dataclass
class EvalSummary:
    """Summary of evaluation run"""
    total_samples: int
    avg_score: float
    scores: List[float]
    metrics: Dict[str, float]
    failed_samples: int
    total_time_ms: float

class PromptEvaluator:
    """
    Prompt evaluation system inspired by OpenAI/evals

    Supports multiple evaluation metrics:
    - Exact match
    - Semantic similarity
    - BLEU score
    - Custom evaluators
    """

    def __init__(self,
                 llm_provider: str = "bedrock",
                 eval_model: Optional[str] = None):
        """
        Initialize prompt evaluator

        Args:
            llm_provider: LLM provider to test
            eval_model: Model to use for evaluation (if different from test model)
        """
        self.llm_provider = llm_provider
        self.eval_model = eval_model
        self.llm = get_llm(llm_provider)

        # Evaluation model for semantic similarity
        if eval_model:
            self.eval_llm = get_llm(eval_model)
        else:
            self.eval_llm = self.llm

        self.evaluators = {
            "exact_match": self._exact_match,
            "semantic_similarity": self._semantic_similarity,
            "contains": self._contains_check,
            "length_check": self._length_check,
            "custom": None
        }

    def add_custom_evaluator(self, name: str, evaluator_func: Callable):
        """Add custom evaluation function"""
        self.evaluators[name] = evaluator_func

    def evaluate_single(self,
                       prompt: str,
                       expected: str,
                       eval_type: str = "semantic_similarity",
                       metadata: Optional[Dict] = None) -> EvalResult:
        """
        Evaluate a single prompt

        Args:
            prompt: The prompt to evaluate
            expected: Expected response
            eval_type: Type of evaluation to perform
            metadata: Additional metadata for the evaluation

        Returns:
            EvalResult with score and metrics
        """
        start_time = time.time()

        try:
            # Get model response
            if hasattr(self.llm, 'invoke'):
                actual = self.llm.invoke(prompt).content if hasattr(self.llm.invoke(prompt), 'content') else str(self.llm.invoke(prompt))
            else:
                actual = str(self.llm(prompt))

            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            # Evaluate response
            evaluator = self.evaluators.get(eval_type)
            if not evaluator:
                raise ValueError(f"Unknown evaluation type: {eval_type}")

            score, metrics = evaluator(actual, expected)

            return EvalResult(
                prompt=prompt,
                expected=expected,
                actual=actual,
                score=score,
                metrics=metrics,
                metadata=metadata or {},
                timestamp=time.time(),
                latency_ms=latency_ms
            )

        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            return EvalResult(
                prompt=prompt,
                expected=expected,
                actual=f"ERROR: {str(e)}",
                score=0.0,
                metrics={"error": str(e)},
                metadata=metadata or {},
                timestamp=time.time(),
                latency_ms=0.0
            )

    def evaluate_dataset(self,
                        dataset: List[Dict[str, str]],
                        eval_type: str = "semantic_similarity",
                        save_results: bool = True,
                        output_path: str = "eval_results.json") -> EvalSummary:
        """
        Evaluate a dataset of prompts

        Args:
            dataset: List of {"prompt": str, "expected": str, "metadata": dict}
            eval_type: Type of evaluation
            save_results: Whether to save results to file
            output_path: Path to save results

        Returns:
            EvalSummary with aggregate metrics
        """
        logger.info(f"Starting evaluation of {len(dataset)} samples with {eval_type}")

        results = []
        start_time = time.time()

        for i, sample in enumerate(dataset):
            logger.info(f"Evaluating sample {i+1}/{len(dataset)}")

            result = self.evaluate_single(
                prompt=sample["prompt"],
                expected=sample["expected"],
                eval_type=eval_type,
                metadata=sample.get("metadata", {})
            )
            results.append(result)

        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000

        # Calculate summary metrics
        scores = [r.score for r in results]
        failed_count = len([r for r in results if r.score == 0.0 and "error" in r.metrics])

        # Aggregate metrics
        all_metrics = {}
        for result in results:
            for key, value in result.metrics.items():
                if isinstance(value, (int, float)):
                    if key not in all_metrics:
                        all_metrics[key] = []
                    all_metrics[key].append(value)

        avg_metrics = {k: sum(v)/len(v) for k, v in all_metrics.items()}

        summary = EvalSummary(
            total_samples=len(dataset),
            avg_score=sum(scores) / len(scores) if scores else 0.0,
            scores=scores,
            metrics=avg_metrics,
            failed_samples=failed_count,
            total_time_ms=total_time_ms
        )

        # Save results
        if save_results:
            self._save_results(results, summary, output_path)

        logger.success(f"Evaluation completed. Average score: {summary.avg_score:.3f}")

        return summary

    def _exact_match(self, actual: str, expected: str) -> tuple[float, Dict]:
        """Exact string match evaluation"""
        match = actual.strip().lower() == expected.strip().lower()
        return float(match), {"exact_match": match}

    def _contains_check(self, actual: str, expected: str) -> tuple[float, Dict]:
        """Check if expected text is contained in actual"""
        contains = expected.lower() in actual.lower()
        return float(contains), {"contains": contains}

    def _length_check(self, actual: str, expected: str) -> tuple[float, Dict]:
        """Check response length compared to expected"""
        actual_len = len(actual.split())
        expected_len = len(expected.split())

        if expected_len == 0:
            return 1.0, {"length_ratio": 1.0}

        ratio = min(actual_len / expected_len, expected_len / actual_len)
        return ratio, {"length_ratio": ratio, "actual_length": actual_len, "expected_length": expected_len}

    def _semantic_similarity(self, actual: str, expected: str) -> tuple[float, Dict]:
        """Semantic similarity evaluation using LLM"""
        evaluation_prompt = f"""
        Please evaluate how similar these two responses are semantically on a scale of 0.0 to 1.0.

        Expected response: {expected}
        Actual response: {actual}

        Consider:
        - Semantic meaning and intent
        - Factual accuracy
        - Completeness of information

        Respond with only a number between 0.0 and 1.0, where:
        - 1.0 = Semantically identical
        - 0.8-0.9 = Very similar meaning
        - 0.6-0.7 = Similar meaning with minor differences
        - 0.4-0.5 = Somewhat similar
        - 0.0-0.3 = Very different or incorrect

        Score:"""

        try:
            if hasattr(self.eval_llm, 'invoke'):
                response = self.eval_llm.invoke(evaluation_prompt)
                score_text = response.content if hasattr(response, 'content') else str(response)
            else:
                score_text = str(self.eval_llm(evaluation_prompt))

            # Extract numerical score
            import re
            score_match = re.search(r'(\d+\.?\d*)', score_text.strip())
            if score_match:
                score = float(score_match.group(1))
                score = max(0.0, min(1.0, score))  # Clamp to [0,1]
            else:
                score = 0.0

            return score, {
                "semantic_similarity": score,
                "evaluator_response": score_text.strip()
            }

        except Exception as e:
            logger.warning(f"Semantic similarity evaluation failed: {e}")
            return 0.0, {"error": str(e)}

    def _save_results(self, results: List[EvalResult], summary: EvalSummary, output_path: str):
        """Save evaluation results to file"""
        output_data = {
            "summary": asdict(summary),
            "results": [asdict(result) for result in results],
            "evaluation_config": {
                "llm_provider": self.llm_provider,
                "eval_model": self.eval_model,
                "timestamp": time.time()
            }
        }

        # Save as JSON
        json_path = Path(output_path)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        # Also save as CSV for easy analysis
        csv_path = json_path.with_suffix('.csv')
        df_results = pd.DataFrame([asdict(result) for result in results])
        df_results.to_csv(csv_path, index=False)

        logger.info(f"Results saved to {json_path} and {csv_path}")

    def compare_prompts(self,
                       prompts: List[str],
                       test_cases: List[Dict[str, str]],
                       eval_type: str = "semantic_similarity") -> Dict[str, EvalSummary]:
        """
        Compare multiple prompts on the same test cases

        Args:
            prompts: List of prompt templates to compare
            test_cases: List of test cases with expected outputs
            eval_type: Evaluation method

        Returns:
            Dictionary mapping prompt index to evaluation summary
        """
        results = {}

        for i, prompt_template in enumerate(prompts):
            logger.info(f"Evaluating prompt {i+1}/{len(prompts)}")

            # Create dataset for this prompt
            dataset = []
            for test_case in test_cases:
                # Format prompt template with test case inputs
                try:
                    formatted_prompt = prompt_template.format(**test_case.get("inputs", {}))
                except KeyError as e:
                    logger.warning(f"Could not format prompt {i}: missing key {e}")
                    formatted_prompt = prompt_template

                dataset.append({
                    "prompt": formatted_prompt,
                    "expected": test_case["expected"],
                    "metadata": {"prompt_index": i, "test_case": test_case}
                })

            summary = self.evaluate_dataset(
                dataset=dataset,
                eval_type=eval_type,
                save_results=True,
                output_path=f"eval_results_prompt_{i}.json"
            )

            results[f"prompt_{i}"] = summary

        return results