"""Code review tool using Gemini AI."""

from typing import List, Optional

from ..api.gemini_client import GeminiClient
from ..models import CodeReview
from ..prompts.system_prompts import CODE_REVIEWER_PROMPT
from ..utils.logger import logger


class CodeReviewer:
    """Tool for reviewing code using Gemini."""
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """Initialize the code reviewer.
        
        Args:
            gemini_client: Optional Gemini client instance
        """
        self.client = gemini_client or GeminiClient()
    
    async def review_code(
        self,
        code: str,
        language: str,
        context: Optional[str] = None,
        focus_areas: Optional[List[str]] = None,
        previous_feedback: Optional[str] = None,
    ) -> CodeReview:
        """Review code and provide feedback.
        
        Args:
            code: The code to review
            language: Programming language
            context: Optional context about the code
            focus_areas: Specific areas to focus on
            previous_feedback: Previous review feedback if this is a revision
            
        Returns:
            Code review results
        """
        logger.info(f"Reviewing {language} code ({len(code)} characters)")
        
        # Build the prompt
        prompt_parts = [
            f"Please review the following {language} code:",
            f"```{language}",
            code,
            "```"
        ]
        
        if context:
            prompt_parts.insert(1, f"Context: {context}")
        
        if focus_areas:
            prompt_parts.append(f"\nFocus Areas:\n" + "\n".join(f"- {area}" for area in focus_areas))
        
        if previous_feedback:
            prompt_parts.append(f"\nThis is a revision. Previous feedback:\n{previous_feedback}")
        
        prompt = "\n".join(prompt_parts)
        
        try:
            # Generate the review
            review = await self.client.generate_json(
                prompt=prompt,
                response_model=CodeReview,
                system_prompt=CODE_REVIEWER_PROMPT,
                temperature=0.7,
            )
            
            logger.info(
                f"Code review completed: {review.overall_quality}, "
                f"{len(review.issues)} issues, {len(review.suggestions)} suggestions"
            )
            return review
            
        except Exception as e:
            logger.error(f"Failed to review code: {str(e)}")
            raise
    
    async def compare_implementations(
        self,
        code1: str,
        code2: str,
        language: str,
        comparison_criteria: Optional[List[str]] = None,
    ) -> str:
        """Compare two code implementations.
        
        Args:
            code1: First implementation
            code2: Second implementation  
            language: Programming language
            comparison_criteria: Specific criteria to compare
            
        Returns:
            Comparison analysis
        """
        logger.info(f"Comparing two {language} implementations")
        
        prompt = f"""Compare these two {language} implementations:

Implementation 1:
```{language}
{code1}
```

Implementation 2:
```{language}
{code2}
```

{f"Comparison Criteria: {', '.join(comparison_criteria)}" if comparison_criteria else ""}

Please provide a detailed comparison covering:
1. Functionality differences
2. Performance implications
3. Code quality and readability
4. Best practices adherence
5. Recommendation on which to use and why"""
        
        try:
            comparison = await self.client.generate_content(
                prompt=prompt,
                system_prompt=CODE_REVIEWER_PROMPT,
                temperature=0.7,
            )
            
            logger.info("Code comparison completed")
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare implementations: {str(e)}")
            raise