"""Stdio MCP server implementation for Plan-MCP."""

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
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
    ]


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


async def main() -> None:
    """Main entry point for the stdio server."""
    global gemini_client, project_planner, code_reviewer, execution_analyzer
    
    logger.info("Starting Plan-MCP stdio server")
    
    # 验证配置
    try:
        config = get_config()
        config.validate_config()
    except ValueError as e:
        logger.error(f"配置错误: {e}")
        logger.error("请确保您已经设置了 GEMINI_API_KEY 环境变量，或在项目根目录创建了 .env 文件。")
        return
    
    # Initialize tools
    try:
        gemini_client = GeminiClient()
        project_planner = ProjectPlanner(gemini_client)
        code_reviewer = CodeReviewer(gemini_client)
        execution_analyzer = ExecutionAnalyzer(gemini_client)
        logger.info("Plan-MCP tools initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize tools: {e}")
        return

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
