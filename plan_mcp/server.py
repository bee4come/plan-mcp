"""Stdio MCP server implementation for Plan-MCP."""

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
    Resource,
)

from .api.gemini_client import GeminiClient
from .config import get_config
from .tools.code_reviewer import CodeReviewer
from .tools.execution_analyzer import ExecutionAnalyzer
from .tools.project_planner import ProjectPlanner
from .utils.logger import logger

# Create server instance
server = Server("plan-mcp")

# Global variables for tools (will be initialized in main)
gemini_client = None
project_planner = None
code_reviewer = None
execution_analyzer = None


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="plan_project",
            description="Create a comprehensive project plan based on requirements",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Project description"},
                    "requirements": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of project requirements",
                    },
                    "constraints": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Project constraints or limitations",
                    },
                    "tech_stack": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Preferred technology stack",
                    },
                },
                "required": ["description"],
            },
        ),
        Tool(
            name="review_code",
            description="Review code for quality, security, and best practices",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to review"},
                    "language": {"type": "string", "description": "Programming language"},
                    "context": {"type": "string", "description": "Context about the code"},
                    "focus_areas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific areas to focus on",
                    },
                },
                "required": ["code", "language"],
            },
        ),
        Tool(
            name="analyze_execution",
            description="Analyze code execution results and provide debugging guidance",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code that was executed"},
                    "execution_output": {"type": "string", "description": "Output from execution"},
                    "expected_behavior": {"type": "string", "description": "Expected behavior"},
                    "error_messages": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Error messages if any",
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language",
                        "default": "python",
                    },
                },
                "required": ["code", "execution_output"],
            },
        ),
        Tool(
            name="review_directory",
            description="Review an entire directory/project for code quality, security, and best practices",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory_path": {"type": "string", "description": "Path to the directory to review"},
                    "focus_areas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific areas to focus on (e.g., security, performance, style)",
                    },
                    "include_patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "File patterns to include (e.g., ['*.py', '*.js'])",
                    },
                    "exclude_patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "File patterns to exclude (e.g., ['test_*', '*.md'])",
                    },
                },
                "required": ["directory_path"],
            },
        ),
    ]


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available file system resources."""
    return [
        Resource(
            uri="file://",
            name="File System Access",
            description="Access to local file system for code analysis",
            mimeType="text/plain",
        )
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read file system resources."""
    if not uri.startswith("file://"):
        raise ValueError("Only file:// URIs are supported")
    
    # Remove file:// prefix and decode
    file_path = uri[7:]  # Remove "file://"
    
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if path.is_file():
            # Read single file
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"File: {file_path}\n\n{content}"
        
        elif path.is_dir():
            # Read directory structure and code files
            code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt'}
            
            result = f"Directory: {file_path}\n\n"
            
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
        
        else:
            raise ValueError(f"Path is neither file nor directory: {file_path}")
    
    except Exception as e:
        raise ValueError(f"Error reading {file_path}: {str(e)}")


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        logger.info(f"Calling tool: {name}")

        if name == "plan_project":
            result = await handle_plan_project(arguments)
        elif name == "review_code":
            result = await handle_review_code(arguments)
        elif name == "analyze_execution":
            result = await handle_analyze_execution(arguments)
        elif name == "review_directory":
            result = await handle_review_directory(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        # Format the result as JSON
        result_json = json.dumps(result, indent=2, ensure_ascii=False)

        return [TextContent(type="text", text=result_json)]

    except Exception as e:
        logger.error(f"Error calling tool {name}: {str(e)}")
        error_result = {
            "error": f"Tool execution failed: {str(e)}",
            "tool": name,
            "arguments": arguments,
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def handle_plan_project(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle project planning requests."""
    logger.info("Handling project planning request")

    plan = await project_planner.create_plan(
        description=arguments["description"],
        requirements=arguments.get("requirements"),
        constraints=arguments.get("constraints"),
        tech_stack=arguments.get("tech_stack"),
    )

    return plan.model_dump()


async def handle_review_code(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle code review requests."""
    logger.info("Handling code review request")

    review = await code_reviewer.review_code(
        code=arguments["code"],
        language=arguments["language"],
        context=arguments.get("context"),
        focus_areas=arguments.get("focus_areas"),
    )

    return review.model_dump()


async def handle_analyze_execution(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle execution analysis requests."""
    logger.info("Handling execution analysis request")

    analysis = await execution_analyzer.analyze_execution(
        code=arguments["code"],
        execution_output=arguments["execution_output"],
        expected_behavior=arguments.get("expected_behavior"),
        error_messages=arguments.get("error_messages"),
        language=arguments.get("language", "python"),
    )

    return analysis.model_dump()


async def handle_review_directory(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle directory review requests."""
    logger.info("Handling directory review request")
    
    directory_path = arguments["directory_path"]
    focus_areas = arguments.get("focus_areas", [])
    include_patterns = arguments.get("include_patterns", ["*"])
    exclude_patterns = arguments.get("exclude_patterns", [])
    
    try:
        # Read directory content using the resource function
        uri = f"file://{directory_path}"
        directory_content = await read_resource(uri)
        
        # Create a comprehensive review
        review_prompt = f"""
Please review this entire codebase for code quality, security, and best practices.

Directory: {directory_path}

Focus Areas: {', '.join(focus_areas) if focus_areas else 'General code review'}

Directory Content:
{directory_content}

Please provide a comprehensive review including:
1. Overall code quality assessment
2. Security issues and vulnerabilities
3. Performance concerns
4. Best practices violations
5. Architectural recommendations
6. Specific file-by-file feedback for critical issues
7. Priority-based action items

Format your response as a structured analysis with clear sections and actionable recommendations.
"""
        
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
        result["include_patterns"] = include_patterns
        result["exclude_patterns"] = exclude_patterns
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to review directory {directory_path}: {str(e)}")
        return {
            "error": f"Directory review failed: {str(e)}",
            "directory_path": directory_path,
            "review_type": "directory_review"
        }


async def main() -> None:
    """Main entry point for the stdio server."""
    global gemini_client, project_planner, code_reviewer, execution_analyzer
    
    # 验证配置
    try:
        config = get_config()
        config.validate_config()
    except ValueError as e:
        # Exit silently for MCP - don't log to stderr during connection
        return
    
    # Initialize tools
    try:
        gemini_client = GeminiClient()
        project_planner = ProjectPlanner(gemini_client)
        code_reviewer = CodeReviewer(gemini_client)
        execution_analyzer = ExecutionAnalyzer(gemini_client)
    except Exception as e:
        # Exit silently for MCP
        return

    # Start the MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, 
            write_stream, 
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
