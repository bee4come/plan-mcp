#!/usr/bin/env python3
"""Test script to verify MCP server works."""

import os
import sys
import asyncio
import json
from pathlib import Path

# Set environment variable for testing
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value

# Add the project to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_mcp_server():
    """Test the MCP server directly."""
    try:
        print("🚀 Testing MCP Server...")
        
        # Import and initialize
        from plan_mcp.server import server
        from plan_mcp.config import get_config
        from plan_mcp.api.gemini_client import GeminiClient
        from plan_mcp.tools.project_planner import ProjectPlanner
        from plan_mcp.tools.code_reviewer import CodeReviewer
        from plan_mcp.tools.execution_analyzer import ExecutionAnalyzer
        
        # Verify configuration
        config = get_config()
        config.validate_config()
        print("✅ Configuration validated")
        
        # Initialize tools
        gemini_client = GeminiClient()
        project_planner = ProjectPlanner(gemini_client)
        code_reviewer = CodeReviewer(gemini_client)
        execution_analyzer = ExecutionAnalyzer(gemini_client)
        print("✅ Tools initialized")
        
        # Update global variables
        import plan_mcp.server as server_module
        server_module.gemini_client = gemini_client
        server_module.project_planner = project_planner
        server_module.code_reviewer = code_reviewer
        server_module.execution_analyzer = execution_analyzer
        
        # Test list_tools
        tools = await server_module.list_tools()
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Test a simple tool call
        test_args = {
            "description": "Create a simple Python web application",
            "requirements": ["FastAPI", "SQLite database"],
            "tech_stack": ["Python", "FastAPI", "SQLite"]
        }
        
        print("\n🧪 Testing project planning tool...")
        result = await server_module.handle_plan_project(test_args)
        print("✅ Project planning tool works!")
        print(f"Generated plan with {len(result.get('phases', []))} phases")
        
        print("\n🎉 All tests passed! MCP server is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1)