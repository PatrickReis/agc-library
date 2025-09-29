"""
Chain of Thought reasoning implementation
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re

from ..logger.logger import get_logger

logger = get_logger("chain_of_thought")

@dataclass
class ThoughtStep:
    """Single step in chain of thought"""
    step_number: int
    thought: str
    reasoning: str
    confidence: float

@dataclass
class ChainOfThoughtResult:
    """Result of chain of thought reasoning"""
    question: str
    steps: List[ThoughtStep]
    final_answer: str
    overall_confidence: float
    reasoning_trace: str

class ChainOfThoughtReasoner:
    """
    Implements Chain of Thought reasoning for complex problems
    """

    def __init__(self, llm, max_steps: int = 5):
        """
        Initialize CoT reasoner

        Args:
            llm: Language model to use
            max_steps: Maximum reasoning steps
        """
        self.llm = llm
        self.max_steps = max_steps

    def reason(self, question: str, context: Optional[str] = None) -> ChainOfThoughtResult:
        """
        Perform chain of thought reasoning

        Args:
            question: Question to reason about
            context: Optional context information

        Returns:
            ChainOfThoughtResult with reasoning steps
        """
        logger.info(f"🤔 Starting chain of thought reasoning for: {question[:50]}...")

        prompt = self._build_cot_prompt(question, context)

        try:
            # Get LLM response
            if hasattr(self.llm, 'invoke'):
                response = self.llm.invoke(prompt)
                response_text = response.content if hasattr(response, 'content') else str(response)
            else:
                response_text = str(self.llm(prompt))

            # Parse the response
            steps = self._parse_reasoning_steps(response_text)
            final_answer = self._extract_final_answer(response_text)
            overall_confidence = self._calculate_overall_confidence(steps)

            result = ChainOfThoughtResult(
                question=question,
                steps=steps,
                final_answer=final_answer,
                overall_confidence=overall_confidence,
                reasoning_trace=response_text
            )

            logger.success(f"✅ CoT reasoning completed with {len(steps)} steps")
            return result

        except Exception as e:
            logger.error(f"CoT reasoning failed: {e}")
            return ChainOfThoughtResult(
                question=question,
                steps=[],
                final_answer=f"Error: {str(e)}",
                overall_confidence=0.0,
                reasoning_trace=""
            )

    def _build_cot_prompt(self, question: str, context: Optional[str] = None) -> str:
        """Build chain of thought prompt"""
        prompt_parts = [
            "Let's work through this step-by-step using chain of thought reasoning.",
            "For each step, I'll explain my thinking process clearly.",
            "",
        ]

        if context:
            prompt_parts.extend([
                "Context:",
                context,
                ""
            ])

        prompt_parts.extend([
            f"Question: {question}",
            "",
            "Let me think through this step by step:",
            "",
            "Step 1: [First, I need to understand what the question is asking]",
            "Reasoning: [Explain the key aspects of the problem]",
            "Confidence: [Rate confidence 0-1]",
            "",
            "Step 2: [Next, I'll identify the relevant information]",
            "Reasoning: [Explain what information is needed]",
            "Confidence: [Rate confidence 0-1]",
            "",
            "Step 3: [Now I'll work through the logic]",
            "Reasoning: [Show the logical steps]",
            "Confidence: [Rate confidence 0-1]",
            "",
            "Continue with additional steps as needed...",
            "",
            "Final Answer: [Provide the final answer based on the reasoning above]"
        ])

        return "\n".join(prompt_parts)

    def _parse_reasoning_steps(self, response: str) -> List[ThoughtStep]:
        """Parse reasoning steps from LLM response"""
        steps = []

        # Find step patterns
        step_pattern = r'Step\s+(\d+):\s*(.*?)(?=Step\s+\d+:|Final Answer:|$)'
        step_matches = re.findall(step_pattern, response, re.DOTALL | re.IGNORECASE)

        for step_num_str, step_content in step_matches:
            try:
                step_num = int(step_num_str)

                # Extract thought and reasoning
                lines = [line.strip() for line in step_content.strip().split('\n') if line.strip()]

                thought = lines[0] if lines else ""
                reasoning = ""
                confidence = 0.5  # Default confidence

                # Look for reasoning and confidence
                for line in lines[1:]:
                    if line.lower().startswith('reasoning:'):
                        reasoning = line[10:].strip()
                    elif line.lower().startswith('confidence:'):
                        conf_text = line[11:].strip()
                        # Extract confidence score
                        conf_match = re.search(r'(\d*\.?\d+)', conf_text)
                        if conf_match:
                            confidence = float(conf_match.group(1))
                            if confidence > 1:
                                confidence = confidence / 100  # Convert percentage

                step = ThoughtStep(
                    step_number=step_num,
                    thought=thought,
                    reasoning=reasoning,
                    confidence=confidence
                )
                steps.append(step)

            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse step {step_num_str}: {e}")

        return steps

    def _extract_final_answer(self, response: str) -> str:
        """Extract final answer from response"""
        # Look for final answer pattern
        final_pattern = r'Final Answer:\s*(.*?)(?:\n\n|$)'
        match = re.search(final_pattern, response, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()

        # Fallback: take last line if no explicit final answer
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        return lines[-1] if lines else "Unable to determine final answer"

    def _calculate_overall_confidence(self, steps: List[ThoughtStep]) -> float:
        """Calculate overall confidence from step confidences"""
        if not steps:
            return 0.0

        confidences = [step.confidence for step in steps if step.confidence > 0]
        if not confidences:
            return 0.5

        # Use geometric mean for overall confidence
        import math
        product = 1.0
        for conf in confidences:
            product *= conf

        return product ** (1.0 / len(confidences))

    def reason_with_verification(self, question: str, context: Optional[str] = None) -> ChainOfThoughtResult:
        """
        Reason with self-verification step

        Args:
            question: Question to reason about
            context: Optional context

        Returns:
            Verified reasoning result
        """
        # First pass: initial reasoning
        initial_result = self.reason(question, context)

        # Verification prompt
        verification_prompt = f"""
        Please verify the following reasoning for correctness:

        Question: {question}

        Reasoning Steps:
        {self._format_steps_for_verification(initial_result.steps)}

        Final Answer: {initial_result.final_answer}

        Is this reasoning correct? If not, what are the issues?
        Please provide a corrected answer if needed.

        Verification:"""

        try:
            if hasattr(self.llm, 'invoke'):
                verification_response = self.llm.invoke(verification_prompt)
                verification_text = verification_response.content if hasattr(verification_response, 'content') else str(verification_response)
            else:
                verification_text = str(self.llm(verification_prompt))

            # If verification suggests corrections, update the result
            if "incorrect" in verification_text.lower() or "error" in verification_text.lower():
                logger.info("🔍 Verification found issues, updating reasoning")

                # Add verification step
                verification_step = ThoughtStep(
                    step_number=len(initial_result.steps) + 1,
                    thought="Verification and correction",
                    reasoning=verification_text,
                    confidence=0.8
                )
                initial_result.steps.append(verification_step)

                # Update final answer if verification provides one
                if "corrected answer:" in verification_text.lower():
                    corrected_answer = verification_text.split("corrected answer:")[-1].strip()
                    initial_result.final_answer = corrected_answer

        except Exception as e:
            logger.warning(f"Verification step failed: {e}")

        return initial_result

    def _format_steps_for_verification(self, steps: List[ThoughtStep]) -> str:
        """Format steps for verification prompt"""
        formatted = []
        for step in steps:
            formatted.append(f"Step {step.step_number}: {step.thought}")
            if step.reasoning:
                formatted.append(f"Reasoning: {step.reasoning}")
            formatted.append(f"Confidence: {step.confidence:.2f}")
            formatted.append("")

        return "\n".join(formatted)

    def explain_reasoning(self, result: ChainOfThoughtResult) -> str:
        """
        Generate human-readable explanation of reasoning

        Args:
            result: CoT reasoning result

        Returns:
            Human-readable explanation
        """
        explanation_parts = [
            f"Question: {result.question}",
            "",
            "My reasoning process:",
            ""
        ]

        for step in result.steps:
            explanation_parts.append(f"📍 Step {step.step_number}: {step.thought}")
            if step.reasoning:
                explanation_parts.append(f"   💭 Reasoning: {step.reasoning}")
            explanation_parts.append(f"   🎯 Confidence: {step.confidence:.0%}")
            explanation_parts.append("")

        explanation_parts.extend([
            f"🏁 Final Answer: {result.final_answer}",
            f"📊 Overall Confidence: {result.overall_confidence:.0%}"
        ])

        return "\n".join(explanation_parts)