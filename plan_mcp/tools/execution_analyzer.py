"""Execution result analysis tool using Gemini AI."""


from ..api.gemini_client import GeminiClient
from ..models import ExecutionAnalysis
from ..prompts.system_prompts import EXECUTION_ANALYZER_PROMPT
from ..utils.logger import logger


class ExecutionAnalyzer:
    """Tool for analyzing code execution results using Gemini."""

    def __init__(self, gemini_client: GeminiClient | None = None):
        """Initialize the execution analyzer.

        Args:
            gemini_client: Optional Gemini client instance
        """
        self.client = gemini_client or GeminiClient()

    async def analyze_execution(
        self,
        code: str,
        execution_output: str,
        expected_behavior: str | None = None,
        error_messages: list[str] | None = None,
        language: str = "python",
        previous_attempts: list[str] | None = None,
    ) -> ExecutionAnalysis:
        """Analyze code execution results and provide guidance.

        Args:
            code: The code that was executed
            execution_output: Output from the execution
            expected_behavior: What the code should do
            error_messages: Any error messages
            language: Programming language
            previous_attempts: Previous attempts if this is a retry

        Returns:
            Execution analysis results
        """
        logger.info(f"Analyzing execution results for {language} code")

        # Build the prompt
        prompt_parts = [
            f"Code ({language}):",
            f"```{language}",
            code,
            "```",
            "",
            "Execution Output:",
            "```",
            execution_output,
            "```",
        ]

        if expected_behavior:
            prompt_parts.insert(0, f"Expected Behavior: {expected_behavior}\n")

        if error_messages:
            prompt_parts.append("\nError Messages:")
            prompt_parts.extend(f"- {error}" for error in error_messages)

        if previous_attempts:
            prompt_parts.append("\nPrevious Attempts:")
            for i, attempt in enumerate(previous_attempts, 1):
                prompt_parts.append(f"\nAttempt {i}:\n{attempt}")

        prompt_parts.append("\nPlease analyze the execution results and provide guidance.")

        prompt = "\n".join(prompt_parts)

        try:
            # Generate the analysis
            analysis = await self.client.generate_json(
                prompt=prompt,
                response_model=ExecutionAnalysis,
                system_prompt=EXECUTION_ANALYZER_PROMPT,
                temperature=0.7,
            )

            logger.info(
                f"Execution analysis completed: {'Success' if analysis.success else 'Failed'}, "
                f"{len(analysis.issues)} issues, {len(analysis.suggested_fixes)} fixes suggested"
            )
            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze execution: {str(e)}")
            raise

    async def debug_error(
        self,
        code: str,
        error_message: str,
        stack_trace: str | None = None,
        language: str = "python",
        context: str | None = None,
    ) -> ExecutionAnalysis:
        """Debug a specific error.

        Args:
            code: The code that caused the error
            error_message: The error message
            stack_trace: Optional stack trace
            language: Programming language
            context: Additional context

        Returns:
            Debug analysis with fixes
        """
        logger.info(f"Debugging {language} error: {error_message[:100]}...")

        prompt_parts = [
            f"Debug this {language} error:",
            "",
            "Code:",
            f"```{language}",
            code,
            "```",
            "",
            "Error Message:",
            error_message,
        ]

        if stack_trace:
            prompt_parts.extend(["", "Stack Trace:", stack_trace])

        if context:
            prompt_parts.extend(["", f"Context: {context}"])

        prompt_parts.extend(
            ["", "Please provide a detailed analysis of the error and specific fixes."]
        )

        prompt = "\n".join(prompt_parts)

        try:
            analysis = await self.client.generate_json(
                prompt=prompt,
                response_model=ExecutionAnalysis,
                system_prompt=EXECUTION_ANALYZER_PROMPT,
                temperature=0.7,
            )

            logger.info(f"Debug analysis completed with {len(analysis.suggested_fixes)} fixes")
            return analysis

        except Exception as e:
            logger.error(f"Failed to debug error: {str(e)}")
            raise
