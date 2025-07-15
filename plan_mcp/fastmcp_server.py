#!/usr/bin/env python3
"""FastMCP-based server implementation for Plan-MCP."""

import os
from pathlib import Path
from typing import List, Optional

from mcp.server.fastmcp import FastMCP

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


@mcp.resource("file://{path}")
def read_file_or_directory(path: str) -> str:
    """Read file system resources."""
    try:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if file_path.is_file():
            # Read single file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"File: {path}\n\n{content}"
        
        elif file_path.is_dir():
            return _read_directory_content(path)
        
        else:
            raise ValueError(f"Path is neither file nor directory: {path}")
    
    except Exception as e:
        raise ValueError(f"Error reading {path}: {str(e)}")


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