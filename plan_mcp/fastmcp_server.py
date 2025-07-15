#!/usr/bin/env python3
"""FastMCP-based server implementation for Plan-MCP."""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.prompts import base
from mcp.types import SamplingMessage, TextContent

from .api.gemini_client import GeminiClient
from .config import get_config
from .tools.code_reviewer import CodeReviewer
from .tools.execution_analyzer import ExecutionAnalyzer
from .tools.project_planner import ProjectPlanner
from .utils.logger import logger

# Create the FastMCP server
mcp = FastMCP("plan-mcp", version="1.0.0")

# Global variables for tools (initialized on first use)
gemini_client = None
project_planner = None
code_reviewer = None
execution_analyzer = None


def _ensure_tools_initialized():
    """Ensure tools are initialized."""
    global gemini_client, project_planner, code_reviewer, execution_analyzer
    
    if gemini_client is None:
        try:
            config = get_config()
            config.validate_config()
            
            gemini_client = GeminiClient()
            project_planner = ProjectPlanner(gemini_client)
            code_reviewer = CodeReviewer(gemini_client)
            execution_analyzer = ExecutionAnalyzer(gemini_client)
        except Exception as e:
            logger.error(f"Failed to initialize tools: {e}")
            raise


@mcp.tool()
def plan_project(
    description: str,
    requirements: Optional[List[str]] = None,
    constraints: Optional[List[str]] = None,
    tech_stack: Optional[List[str]] = None,
) -> dict:
    """Create a comprehensive project plan based on requirements."""
    _ensure_tools_initialized()
    
    import asyncio
    
    async def _plan():
        return await project_planner.create_plan(
            description=description,
            requirements=requirements,
            constraints=constraints,
            tech_stack=tech_stack,
        )
    
    plan = asyncio.run(_plan())
    return plan.model_dump()


@mcp.tool()
def review_code(
    code: str,
    language: str,
    context: Optional[str] = None,
    focus_areas: Optional[List[str]] = None,
) -> dict:
    """Review code for quality, security, and best practices."""
    _ensure_tools_initialized()
    
    import asyncio
    
    async def _review():
        return await code_reviewer.review_code(
            code=code,
            language=language,
            context=context,
            focus_areas=focus_areas,
        )
    
    review = asyncio.run(_review())
    return review.model_dump()


@mcp.tool()
def analyze_execution(
    code: str,
    execution_output: str,
    expected_behavior: Optional[str] = None,
    error_messages: Optional[List[str]] = None,
    language: str = "python",
) -> dict:
    """Analyze code execution results and provide debugging guidance."""
    _ensure_tools_initialized()
    
    import asyncio
    
    async def _analyze():
        return await execution_analyzer.analyze_execution(
            code=code,
            execution_output=execution_output,
            expected_behavior=expected_behavior,
            error_messages=error_messages,
            language=language,
        )
    
    analysis = asyncio.run(_analyze())
    return analysis.model_dump()


@mcp.tool()
def review_directory(
    directory_path: str,
    focus_areas: Optional[List[str]] = None,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> dict:
    """Review an entire directory/project for code quality, security, and best practices."""
    _ensure_tools_initialized()
    
    import asyncio
    
    async def _review_dir():
        # Read directory content
        directory_content = _read_directory_content(directory_path)
        
        # Use the code reviewer with the directory content
        review = await code_reviewer.review_code(
            code=directory_content,
            language="mixed",  # Multi-language project
            context=f"Full directory review of {directory_path}",
            focus_areas=focus_areas,
        )
        
        # Add directory-specific metadata
        result = review.model_dump()
        result["review_type"] = "directory_review"
        result["directory_path"] = directory_path
        result["include_patterns"] = include_patterns or ["*"]
        result["exclude_patterns"] = exclude_patterns or []
        
        return result
    
    return asyncio.run(_review_dir())


# ============================================================================
# PROMPTS - Predefined prompt templates
# ============================================================================

@mcp.prompt(title="Code Review Template")
def code_review_prompt(
    code: str, 
    language: str = "python", 
    focus_areas: str = "security, performance, maintainability"
) -> str:
    """Generate a structured code review prompt."""
    return f"""Please review this {language} code with focus on {focus_areas}.

Code to Review:
```{language}
{code}
```

Please provide:
1. Overall assessment
2. Security issues (if any)
3. Performance concerns
4. Code quality improvements
5. Best practices recommendations
6. Specific line-by-line feedback for critical issues

Format your response with clear sections and actionable recommendations."""


@mcp.prompt(title="Project Planning Template")
def project_planning_prompt(
    description: str,
    tech_stack: str = "",
    constraints: str = ""
) -> list[base.Message]:
    """Generate a project planning conversation starter."""
    messages = [
        base.UserMessage(f"I need help planning a project: {description}"),
    ]
    
    if tech_stack:
        messages.append(base.UserMessage(f"Preferred tech stack: {tech_stack}"))
    
    if constraints:
        messages.append(base.UserMessage(f"Constraints: {constraints}"))
    
    messages.append(
        base.AssistantMessage(
            "I'll help you create a comprehensive project plan. Let me break this down into phases with specific tasks, timelines, and deliverables. Would you like me to focus on any particular aspect first (architecture, timeline, team structure, or risk management)?"
        )
    )
    
    return messages


@mcp.prompt(title="Debug Assistant")
def debug_assistant_prompt(
    error_message: str,
    code_snippet: str = "",
    expected_behavior: str = ""
) -> str:
    """Generate a debugging assistance prompt."""
    prompt = f"""Help me debug this issue:

Error: {error_message}
"""
    
    if code_snippet:
        prompt += f"""
Code:
```
{code_snippet}
```
"""
    
    if expected_behavior:
        prompt += f"""
Expected Behavior: {expected_behavior}
"""
    
    prompt += """
Please provide:
1. Likely causes of this error
2. Step-by-step debugging approach
3. Specific fixes with code examples
4. Prevention strategies for similar issues
"""
    
    return prompt


@mcp.prompt(title="Architecture Review")
def architecture_review_prompt(
    system_description: str,
    requirements: str = "",
    scale: str = "medium"
) -> str:
    """Generate an architecture review prompt."""
    return f"""Please review this system architecture:

System: {system_description}

Requirements: {requirements if requirements else 'Standard web application requirements'}

Scale: {scale} scale application

Please analyze:
1. Architectural patterns and their appropriateness
2. Scalability considerations
3. Security architecture
4. Data flow and storage design
5. Technology choices and alternatives
6. Potential bottlenecks
7. Deployment and infrastructure recommendations

Provide specific recommendations for improvements."""


# ============================================================================
# SAMPLING - LLM text generation capabilities  
# ============================================================================

@mcp.tool()
async def generate_documentation(
    code: str,
    ctx: Context,
    doc_type: str = "api",
    style: str = "comprehensive"
) -> str:
    """Generate documentation using LLM sampling."""
    prompt = f"""Generate {style} {doc_type} documentation for this code:

```
{code}
```

Please include:
- Clear descriptions
- Parameter details
- Return value explanations
- Usage examples
- Error handling information
"""
    
    result = await ctx.session.create_message(
        messages=[
            SamplingMessage(
                role="user",
                content=TextContent(type="text", text=prompt),
            )
        ],
        max_tokens=1000,
    )
    
    if result.content.type == "text":
        return result.content.text
    return str(result.content)


@mcp.tool()
async def generate_tests(
    code: str,
    ctx: Context,
    test_framework: str = "pytest",
    coverage_type: str = "unit"
) -> str:
    """Generate test cases using LLM sampling."""
    prompt = f"""Generate {coverage_type} tests using {test_framework} for this code:

```
{code}
```

Please include:
- Positive test cases
- Negative test cases  
- Edge cases
- Proper assertions
- Test data setup/teardown
- Clear test names and docstrings
"""
    
    result = await ctx.session.create_message(
        messages=[
            SamplingMessage(
                role="user", 
                content=TextContent(type="text", text=prompt),
            )
        ],
        max_tokens=1500,
    )
    
    if result.content.type == "text":
        return result.content.text
    return str(result.content)


# ============================================================================
# ELICITATION - Interactive user input collection
# ============================================================================

class ProjectRequirements(BaseModel):
    """Schema for collecting project requirements."""
    
    confirm_tech_stack: bool = Field(description="Confirm the suggested technology stack?")
    additional_features: str = Field(
        default="",
        description="Any additional features you'd like to include?"
    )
    timeline_preference: str = Field(
        default="normal",
        description="Timeline preference: fast, normal, or thorough"
    )
    team_size: int = Field(
        default=1,
        description="Expected team size"
    )


class CodeReviewPreferences(BaseModel):
    """Schema for collecting code review preferences."""
    
    include_suggestions: bool = Field(description="Include improvement suggestions?")
    focus_on_security: bool = Field(description="Focus heavily on security issues?")
    check_performance: bool = Field(description="Include performance analysis?")
    style_guide: str = Field(
        default="pep8",
        description="Preferred style guide (pep8, google, airbnb, etc.)"
    )


@mcp.tool()
async def interactive_project_planning(
    description: str,
    ctx: Context
) -> str:
    """Interactive project planning with user elicitation."""
    # First, provide initial analysis
    initial_response = f"Based on your project description: '{description}', I'll help create a detailed plan."
    
    # Ask for additional requirements
    result = await ctx.elicit(
        message="I need some additional information to create the best plan for you:",
        schema=ProjectRequirements,
    )
    
    if result.action == "accept" and result.data:
        prefs = result.data
        
        # Now create a customized plan based on preferences
        _ensure_tools_initialized()
        
        import asyncio
        
        async def _create_plan():
            additional_requirements = []
            if prefs.additional_features:
                additional_requirements.append(prefs.additional_features)
            
            return await project_planner.create_plan(
                description=description + f" (Timeline: {prefs.timeline_preference}, Team size: {prefs.team_size})",
                requirements=additional_requirements,
                tech_stack=["Confirmed by user"] if prefs.confirm_tech_stack else None,
            )
        
        plan = asyncio.run(_create_plan())
        plan_dict = plan.model_dump()
        
        return f"✅ Customized project plan created:\n\n{plan_dict}"
    
    return "❌ Project planning cancelled by user."


@mcp.tool()
async def interactive_code_review(
    code: str,
    language: str,
    ctx: Context
) -> str:
    """Interactive code review with user preferences."""
    # Ask for review preferences
    result = await ctx.elicit(
        message="What aspects of the code review are most important to you?",
        schema=CodeReviewPreferences,
    )
    
    if result.action == "accept" and result.data:
        prefs = result.data
        
        # Build focus areas based on preferences
        focus_areas = []
        if prefs.include_suggestions:
            focus_areas.append("improvement suggestions")
        if prefs.focus_on_security:
            focus_areas.append("security")
        if prefs.check_performance:
            focus_areas.append("performance")
        focus_areas.append(f"{prefs.style_guide} style compliance")
        
        # Perform customized review
        _ensure_tools_initialized()
        
        import asyncio
        
        async def _review():
            return await code_reviewer.review_code(
                code=code,
                language=language,
                context=f"Interactive review with focus on: {', '.join(focus_areas)}",
                focus_areas=focus_areas,
            )
        
        review = asyncio.run(_review())
        review_dict = review.model_dump()
        
        return f"✅ Customized code review completed:\n\n{review_dict}"
    
    return "❌ Code review cancelled by user."


# ============================================================================
# ROOTS - File system navigation roots
# ============================================================================

@mcp.tool()
def list_workspace_roots() -> List[str]:
    """List available workspace root directories."""
    common_roots = [
        str(Path.home()),
        str(Path.home() / "Documents"),
        str(Path.home() / "Projects"),
        str(Path.home() / "Development"),
        str(Path.cwd()),
        "/tmp",
        "/var/tmp"
    ]
    
    # Filter to only existing directories
    existing_roots = [root for root in common_roots if Path(root).exists()]
    
    return existing_roots


@mcp.tool()
def suggest_project_roots(project_type: str = "web") -> List[str]:
    """Suggest appropriate root directories for different project types."""
    base_paths = [
        str(Path.home() / "Projects"),
        str(Path.home() / "Development"),
        str(Path.home() / "Code"),
        str(Path.cwd())
    ]
    
    suggested_roots = []
    for base in base_paths:
        if Path(base).exists():
            # Add project-type-specific suggestions
            if project_type == "web":
                suggested_roots.extend([
                    str(Path(base) / "web-projects"),
                    str(Path(base) / "frontend"),
                    str(Path(base) / "backend")
                ])
            elif project_type == "mobile":
                suggested_roots.extend([
                    str(Path(base) / "mobile-apps"),
                    str(Path(base) / "ios"),
                    str(Path(base) / "android")
                ])
            elif project_type == "data":
                suggested_roots.extend([
                    str(Path(base) / "data-science"),
                    str(Path(base) / "analytics"),
                    str(Path(base) / "ml-projects")
                ])
            else:
                suggested_roots.append(str(Path(base) / project_type))
    
    # Add the base paths themselves
    suggested_roots.extend([p for p in base_paths if Path(p).exists()])
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(suggested_roots))


@mcp.resource("file://{filepath}")
def read_file_resource(filepath: str) -> str:
    """Read a single file resource."""
    try:
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        if file_path.is_file():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"File: {filepath}\n\n{content}"
        else:
            raise ValueError(f"Path is not a file: {filepath}")
    
    except Exception as e:
        raise ValueError(f"Error reading {filepath}: {str(e)}")


@mcp.resource("dir://{dirpath}")
def read_directory_resource(dirpath: str) -> str:
    """Read a directory resource with all code files."""
    try:
        dir_path = Path(dirpath)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dirpath}")
        
        if dir_path.is_dir():
            return _read_directory_content(dirpath)
        else:
            raise ValueError(f"Path is not a directory: {dirpath}")
    
    except Exception as e:
        raise ValueError(f"Error reading directory {dirpath}: {str(e)}")


@mcp.resource("workspace://current")
def get_current_workspace() -> str:
    """Get information about the current workspace."""
    cwd = Path.cwd()
    return f"""Current Workspace: {cwd}

Available in this workspace:
- Use file://{{filepath}} to read individual files
- Use dir://{{dirpath}} to read entire directories
- Use list_workspace_roots tool to find common project directories

Current directory contents:
{chr(10).join(f"  {item.name}{'/' if item.is_dir() else ''}" for item in cwd.iterdir() if not item.name.startswith('.'))}
"""


def _read_directory_content(directory_path: str) -> str:
    """Read directory structure and code files."""
    path = Path(directory_path)
    code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt'}
    
    result = f"Directory: {directory_path}\n\n"
    
    # Add directory structure
    result += "Directory Structure:\n"
    for root, dirs, files in os.walk(path):
        # Skip hidden directories and common ignore patterns
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'node_modules', '__pycache__', 'venv', 'env'}]
        
        level = root.replace(str(path), '').count(os.sep)
        indent = '  ' * level
        result += f"{indent}{os.path.basename(root)}/\n"
        
        sub_indent = '  ' * (level + 1)
        for file in files:
            if not file.startswith('.'):
                result += f"{sub_indent}{file}\n"
    
    result += "\n" + "="*50 + "\n\n"
    
    # Add code files content
    result += "Code Files Content:\n\n"
    
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'node_modules', '__pycache__', 'venv', 'env'}]
        
        for file in files:
            file_path_obj = Path(root) / file
            if file_path_obj.suffix.lower() in code_extensions:
                try:
                    with open(file_path_obj, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    
                    relative_path = file_path_obj.relative_to(path)
                    result += f"--- {relative_path} ---\n"
                    result += file_content
                    result += "\n\n"
                except (UnicodeDecodeError, PermissionError):
                    result += f"--- {relative_path} ---\n"
                    result += "(Binary file or permission denied)\n\n"
    
    return result


if __name__ == "__main__":
    # Setup environment
    script_dir = Path(__file__).parent.parent.resolve()
    env_file = script_dir / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value
    
    # Run the server
    mcp.run()