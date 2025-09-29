"""
Step-by-step reasoning implementation
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

from ..logger.logger import get_logger

logger = get_logger("step_by_step")

class StepType(Enum):
    """Types of reasoning steps"""
    UNDERSTANDING = "understanding"
    ANALYSIS = "analysis"
    CALCULATION = "calculation"
    SYNTHESIS = "synthesis"
    VERIFICATION = "verification"

@dataclass
class ReasoningStep:
    """Single reasoning step"""
    step_id: str
    step_type: StepType
    description: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    reasoning: str
    success: bool
    confidence: float

@dataclass
class StepByStepResult:
    """Result of step-by-step reasoning"""
    problem: str
    steps: List[ReasoningStep]
    final_result: Any
    success: bool
    total_confidence: float

class StepByStepReasoner:
    """
    Implements structured step-by-step reasoning
    """

    def __init__(self, llm):
        """
        Initialize step-by-step reasoner

        Args:
            llm: Language model to use
        """
        self.llm = llm
        self.step_templates = self._load_step_templates()

    def reason(self, problem: str, problem_type: str = "general") -> StepByStepResult:
        """
        Perform step-by-step reasoning

        Args:
            problem: Problem to solve
            problem_type: Type of problem (general, math, logic, etc.)

        Returns:
            StepByStepResult with detailed steps
        """
        logger.info(f"🔢 Starting step-by-step reasoning for {problem_type} problem")

        steps = []
        current_data = {"problem": problem, "problem_type": problem_type}

        try:
            # Step 1: Understanding
            understanding_step = self._execute_understanding_step(problem, current_data)
            steps.append(understanding_step)
            current_data.update(understanding_step.output_data)

            # Step 2: Analysis
            analysis_step = self._execute_analysis_step(problem, current_data)
            steps.append(analysis_step)
            current_data.update(analysis_step.output_data)

            # Step 3: Solution Steps (varies by problem type)
            solution_steps = self._execute_solution_steps(problem, problem_type, current_data)
            steps.extend(solution_steps)

            # Update current data with solution results
            for step in solution_steps:
                current_data.update(step.output_data)

            # Step 4: Verification
            verification_step = self._execute_verification_step(problem, current_data)
            steps.append(verification_step)

            # Determine final result
            final_result = current_data.get("final_answer", "Unable to determine result")
            success = all(step.success for step in steps)
            total_confidence = self._calculate_total_confidence(steps)

            result = StepByStepResult(
                problem=problem,
                steps=steps,
                final_result=final_result,
                success=success,
                total_confidence=total_confidence
            )

            logger.success(f"✅ Step-by-step reasoning completed with {len(steps)} steps")
            return result

        except Exception as e:
            logger.error(f"Step-by-step reasoning failed: {e}")
            return StepByStepResult(
                problem=problem,
                steps=steps,
                final_result=f"Error: {str(e)}",
                success=False,
                total_confidence=0.0
            )

    def _execute_understanding_step(self, problem: str, data: Dict) -> ReasoningStep:
        """Execute understanding step"""
        prompt = f"""
        Analyze this problem to understand what is being asked:

        Problem: {problem}

        Please provide:
        1. What is the main question being asked?
        2. What type of problem is this?
        3. What information is given?
        4. What information is needed to solve it?

        Understanding:"""

        response = self._call_llm(prompt)

        # Parse understanding
        understanding = self._parse_understanding_response(response)

        return ReasoningStep(
            step_id="understanding",
            step_type=StepType.UNDERSTANDING,
            description="Understanding the problem",
            input_data={"problem": problem},
            output_data=understanding,
            reasoning=response,
            success=bool(understanding.get("main_question")),
            confidence=0.9
        )

    def _execute_analysis_step(self, problem: str, data: Dict) -> ReasoningStep:
        """Execute analysis step"""
        main_question = data.get("main_question", problem)
        problem_type = data.get("problem_type", "unknown")

        prompt = f"""
        Analyze the approach needed to solve this problem:

        Problem: {problem}
        Main Question: {main_question}
        Problem Type: {problem_type}

        Please provide:
        1. What approach or method should be used?
        2. What are the key steps needed?
        3. Are there any potential challenges?
        4. What order should the steps be performed?

        Analysis:"""

        response = self._call_llm(prompt)

        # Parse analysis
        analysis = self._parse_analysis_response(response)

        return ReasoningStep(
            step_id="analysis",
            step_type=StepType.ANALYSIS,
            description="Analyzing solution approach",
            input_data={"main_question": main_question, "problem_type": problem_type},
            output_data=analysis,
            reasoning=response,
            success=bool(analysis.get("approach")),
            confidence=0.8
        )

    def _execute_solution_steps(self, problem: str, problem_type: str, data: Dict) -> List[ReasoningStep]:
        """Execute solution-specific steps"""
        approach = data.get("approach", "general")
        key_steps = data.get("key_steps", [])

        solution_steps = []

        # Generate solution steps based on problem type
        if problem_type == "math":
            solution_steps = self._solve_math_problem(problem, data)
        elif problem_type == "logic":
            solution_steps = self._solve_logic_problem(problem, data)
        else:
            solution_steps = self._solve_general_problem(problem, data)

        return solution_steps

    def _solve_math_problem(self, problem: str, data: Dict) -> List[ReasoningStep]:
        """Solve mathematical problems"""
        steps = []

        # Step: Identify mathematical operations
        prompt = f"""
        Identify the mathematical operations needed for this problem:

        Problem: {problem}
        Context: {data}

        Please:
        1. List the mathematical operations needed
        2. Identify the order of operations
        3. Perform the calculations step by step

        Mathematical Solution:"""

        response = self._call_llm(prompt)

        step = ReasoningStep(
            step_id="math_calculation",
            step_type=StepType.CALCULATION,
            description="Performing mathematical calculations",
            input_data=data,
            output_data={"calculation_result": response},
            reasoning=response,
            success=True,
            confidence=0.9
        )
        steps.append(step)

        # Extract final answer
        final_answer = self._extract_math_answer(response)
        if final_answer:
            step.output_data["final_answer"] = final_answer

        return steps

    def _solve_logic_problem(self, problem: str, data: Dict) -> List[ReasoningStep]:
        """Solve logical reasoning problems"""
        steps = []

        # Step: Logical analysis
        prompt = f"""
        Apply logical reasoning to solve this problem:

        Problem: {problem}
        Context: {data}

        Please:
        1. Identify the logical relationships
        2. Apply logical rules step by step
        3. Draw conclusions

        Logical Solution:"""

        response = self._call_llm(prompt)

        step = ReasoningStep(
            step_id="logical_reasoning",
            step_type=StepType.ANALYSIS,
            description="Applying logical reasoning",
            input_data=data,
            output_data={"logical_result": response},
            reasoning=response,
            success=True,
            confidence=0.8
        )
        steps.append(step)

        # Extract conclusion
        conclusion = self._extract_logical_conclusion(response)
        if conclusion:
            step.output_data["final_answer"] = conclusion

        return steps

    def _solve_general_problem(self, problem: str, data: Dict) -> List[ReasoningStep]:
        """Solve general problems"""
        steps = []

        # Step: Solution synthesis
        prompt = f"""
        Synthesize a solution for this problem:

        Problem: {problem}
        Analysis: {data.get('approach', 'General approach')}
        Key Steps: {data.get('key_steps', [])}

        Please provide a step-by-step solution:

        Solution:"""

        response = self._call_llm(prompt)

        step = ReasoningStep(
            step_id="solution_synthesis",
            step_type=StepType.SYNTHESIS,
            description="Synthesizing solution",
            input_data=data,
            output_data={"solution": response},
            reasoning=response,
            success=True,
            confidence=0.7
        )
        steps.append(step)

        # Extract final answer
        final_answer = self._extract_general_answer(response)
        if final_answer:
            step.output_data["final_answer"] = final_answer

        return steps

    def _execute_verification_step(self, problem: str, data: Dict) -> ReasoningStep:
        """Execute verification step"""
        final_answer = data.get("final_answer", "No answer found")

        prompt = f"""
        Verify this solution:

        Original Problem: {problem}
        Solution: {final_answer}

        Please:
        1. Check if the solution answers the original question
        2. Verify the logic and calculations
        3. Identify any potential errors
        4. Confirm if the solution is reasonable

        Verification:"""

        response = self._call_llm(prompt)

        # Parse verification
        verification_result = "correct" in response.lower() and "error" not in response.lower()

        return ReasoningStep(
            step_id="verification",
            step_type=StepType.VERIFICATION,
            description="Verifying solution",
            input_data={"final_answer": final_answer},
            output_data={"verification_result": verification_result, "verification_notes": response},
            reasoning=response,
            success=verification_result,
            confidence=0.8 if verification_result else 0.4
        )

    def _call_llm(self, prompt: str) -> str:
        """Call the language model"""
        try:
            if hasattr(self.llm, 'invoke'):
                response = self.llm.invoke(prompt)
                return response.content if hasattr(response, 'content') else str(response)
            else:
                return str(self.llm(prompt))
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return f"Error: {str(e)}"

    def _parse_understanding_response(self, response: str) -> Dict[str, Any]:
        """Parse understanding response"""
        understanding = {}

        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('1.') or 'main question' in line.lower():
                understanding["main_question"] = line.split(':', 1)[-1].strip()
            elif line.startswith('2.') or 'type of problem' in line.lower():
                understanding["problem_type"] = line.split(':', 1)[-1].strip()
            elif line.startswith('3.') or 'information given' in line.lower():
                understanding["given_info"] = line.split(':', 1)[-1].strip()
            elif line.startswith('4.') or 'information needed' in line.lower():
                understanding["needed_info"] = line.split(':', 1)[-1].strip()

        return understanding

    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse analysis response"""
        analysis = {}

        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('1.') or 'approach' in line.lower() or 'method' in line.lower():
                analysis["approach"] = line.split(':', 1)[-1].strip()
            elif line.startswith('2.') or 'key steps' in line.lower():
                analysis["key_steps"] = line.split(':', 1)[-1].strip()
            elif line.startswith('3.') or 'challenges' in line.lower():
                analysis["challenges"] = line.split(':', 1)[-1].strip()
            elif line.startswith('4.') or 'order' in line.lower():
                analysis["step_order"] = line.split(':', 1)[-1].strip()

        return analysis

    def _extract_math_answer(self, response: str) -> Optional[str]:
        """Extract mathematical answer from response"""
        import re

        # Look for numerical answers
        number_pattern = r'(?:answer|result|equals?)\s*:?\s*([+-]?\d+(?:\.\d+)?)'
        match = re.search(number_pattern, response, re.IGNORECASE)

        if match:
            return match.group(1)

        # Look for final line with number
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        for line in reversed(lines):
            number_match = re.search(r'([+-]?\d+(?:\.\d+)?)', line)
            if number_match:
                return number_match.group(1)

        return None

    def _extract_logical_conclusion(self, response: str) -> Optional[str]:
        """Extract logical conclusion from response"""
        lines = [line.strip() for line in response.split('\n') if line.strip()]

        # Look for conclusion indicators
        for line in lines:
            if any(indicator in line.lower() for indicator in ['conclusion:', 'therefore', 'thus', 'answer:']):
                return line.split(':', 1)[-1].strip() if ':' in line else line

        # Return last non-empty line as fallback
        return lines[-1] if lines else None

    def _extract_general_answer(self, response: str) -> Optional[str]:
        """Extract general answer from response"""
        lines = [line.strip() for line in response.split('\n') if line.strip()]

        # Look for answer indicators
        for line in lines:
            if any(indicator in line.lower() for indicator in ['answer:', 'solution:', 'result:']):
                return line.split(':', 1)[-1].strip() if ':' in line else line

        # Return last paragraph as fallback
        paragraphs = response.split('\n\n')
        return paragraphs[-1].strip() if paragraphs else None

    def _calculate_total_confidence(self, steps: List[ReasoningStep]) -> float:
        """Calculate total confidence from all steps"""
        if not steps:
            return 0.0

        confidences = [step.confidence for step in steps if step.success]
        if not confidences:
            return 0.0

        # Use weighted average (verification step has higher weight)
        total_weight = 0
        weighted_sum = 0

        for step in steps:
            if step.success:
                weight = 2.0 if step.step_type == StepType.VERIFICATION else 1.0
                weighted_sum += step.confidence * weight
                total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _load_step_templates(self) -> Dict[str, str]:
        """Load step templates for different problem types"""
        return {
            "math": "Mathematical problem solving template",
            "logic": "Logical reasoning template",
            "general": "General problem solving template"
        }

    def explain_solution(self, result: StepByStepResult) -> str:
        """
        Generate human-readable explanation of the solution

        Args:
            result: Step-by-step reasoning result

        Returns:
            Human-readable explanation
        """
        explanation_parts = [
            f"Problem: {result.problem}",
            "",
            "Solution Process:",
            ""
        ]

        for i, step in enumerate(result.steps, 1):
            icon = "✅" if step.success else "❌"
            explanation_parts.append(f"{icon} Step {i}: {step.description}")
            explanation_parts.append(f"   📝 {step.reasoning[:200]}...")
            explanation_parts.append(f"   🎯 Confidence: {step.confidence:.0%}")
            explanation_parts.append("")

        explanation_parts.extend([
            f"🏁 Final Result: {result.final_result}",
            f"✅ Success: {'Yes' if result.success else 'No'}",
            f"📊 Overall Confidence: {result.total_confidence:.0%}"
        ])

        return "\n".join(explanation_parts)