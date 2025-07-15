"""Project planning tool using Gemini AI."""

from typing import List, Optional

from ..api.gemini_client import GeminiClient
from ..models import ProjectPlan
from ..prompts.system_prompts import PROJECT_PLANNER_PROMPT
from ..utils.logger import logger


class ProjectPlanner:
    """Tool for generating project plans using Gemini."""
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """Initialize the project planner.
        
        Args:
            gemini_client: Optional Gemini client instance
        """
        self.client = gemini_client or GeminiClient()
    
    async def create_plan(
        self,
        description: str,
        requirements: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
        tech_stack: Optional[List[str]] = None,
    ) -> ProjectPlan:
        """Create a project plan based on the provided information.
        
        Args:
            description: Project description
            requirements: List of specific requirements
            constraints: List of constraints or limitations
            tech_stack: Preferred technology stack
            
        Returns:
            Generated project plan
        """
        logger.info("Creating project plan")
        
        # Build the prompt
        prompt_parts = [f"Project Description: {description}"]
        
        if requirements:
            prompt_parts.append(f"Requirements:\n" + "\n".join(f"- {req}" for req in requirements))
        
        if constraints:
            prompt_parts.append(f"Constraints:\n" + "\n".join(f"- {con}" for con in constraints))
        
        if tech_stack:
            prompt_parts.append(f"Technology Stack: {', '.join(tech_stack)}")
        
        prompt_parts.append("\nPlease create a comprehensive project plan with phases, tasks, and estimates.")
        
        prompt = "\n\n".join(prompt_parts)
        
        try:
            # Generate the plan
            plan = await self.client.generate_json(
                prompt=prompt,
                response_model=ProjectPlan,
                system_prompt=PROJECT_PLANNER_PROMPT,
                temperature=0.7,
            )
            
            logger.info(f"Created project plan with {len(plan.phases)} phases")
            return plan
            
        except Exception as e:
            logger.error(f"Failed to create project plan: {str(e)}")
            raise
    
    async def refine_plan(
        self,
        current_plan: ProjectPlan,
        feedback: str,
        additional_context: Optional[str] = None,
    ) -> ProjectPlan:
        """Refine an existing project plan based on feedback.
        
        Args:
            current_plan: The current project plan
            feedback: Feedback on what to change
            additional_context: Any additional context
            
        Returns:
            Refined project plan
        """
        logger.info("Refining project plan based on feedback")
        
        prompt = f"""Current Project Plan:
{current_plan.model_dump_json(indent=2)}

Feedback:
{feedback}

{f"Additional Context: {additional_context}" if additional_context else ""}

Please refine the project plan based on the feedback while maintaining its overall structure and quality."""
        
        try:
            refined_plan = await self.client.generate_json(
                prompt=prompt,
                response_model=ProjectPlan,
                system_prompt=PROJECT_PLANNER_PROMPT,
                temperature=0.7,
            )
            
            logger.info("Successfully refined project plan")
            return refined_plan
            
        except Exception as e:
            logger.error(f"Failed to refine project plan: {str(e)}")
            raise