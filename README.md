# Plan-MCP

A Model Context Protocol (MCP) server that leverages Google Gemini AI for intelligent project planning and code review.

## 🌟 Overview

Plan-MCP acts as an AI-powered project architect that bridges Gemini's planning capabilities with Claude's coding abilities:

- **Gemini as Architect**: Analyzes requirements, creates project plans, reviews code quality
- **Claude as Developer**: Implements code based on Gemini's guidance
- **Continuous Feedback Loop**: Gemini reviews execution results and provides iterative improvements

## 🚀 Features

### 1. Project Planning (`plan_project`)
- Break down complex requirements into structured phases and tasks
- Generate detailed project plans with priorities and dependencies
- Estimate effort and identify potential risks
- Support for technical constraints and preferred tech stacks

### 2. Code Review (`review_code`)
- Comprehensive code quality analysis
- Security vulnerability detection
- Performance optimization suggestions
- Best practices and design pattern recommendations
- Language-agnostic support

### 3. Execution Analysis (`analyze_execution`)
- Debug runtime errors with root cause analysis
- Provide specific code fixes with explanations
- Evaluate if execution meets expected behavior
- Guide iterative development with next steps

## 📋 Prerequisites

- Python 3.11 or higher
- Google Gemini API key
- Claude Code (for MCP integration)

## 🛠️ Installation

### Quick Start with uvx (Recommended)

```bash
# Install and run directly with uvx
uvx plan-mcp

# Or add to Claude Code
claude mcp add plan-mcp -- uvx plan-mcp
```

### Traditional pip Installation

```bash
# Install from PyPI
pip install plan-mcp

# Run the server
plan-mcp
```

## 🔧 Configuration

### Set up your Gemini API key

```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```

Or create a `.env` file:
```
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-pro
LOG_LEVEL=INFO
```

### Claude Code Integration

#### 🚀 Quick Integration (Recommended)

Run directly from GitHub using `uv` without local installation:

```bash
# Team/project configuration (recommended)
claude mcp add -s project plan-mcp uv tool run --from git+https://github.com/bee4come/plan-mcp.git plan-mcp
```

This creates a `.mcp.json` file in your project root. For secure API key management, edit the file:

```json
{
  "mcpServers": {
    "plan-mcp": {
      "command": "uv",
      "args": [
        "tool",
        "run",
        "--from",
        "git+https://github.com/bee4come/plan-mcp.git",
        "plan-mcp"
      ],
      "env": {
        "GEMINI_API_KEY": "${GEMINI_API_KEY}"
      }
    }
  }
}
```

#### Alternative Configuration Options

**Personal global configuration:**
```bash
claude mcp add -s user plan-mcp uv tool run -e GEMINI_API_KEY=your_api_key --from git+https://github.com/bee4come/plan-mcp.git plan-mcp
```

**Local testing configuration:**
```bash
claude mcp add plan-mcp uv tool run -e GEMINI_API_KEY=your_api_key --from git+https://github.com/bee4come/plan-mcp.git plan-mcp
```

#### Managing MCP Services

```bash
# List all services
claude mcp list

# Get service details
claude mcp get plan-mcp

# Check status in Claude Code
# Type /mcp command to view connection status
```

## 💻 Usage

Once configured, you can use these tools in Claude Code:

### 1. Create a project plan
```
Use the plan_project tool to create a plan for building a REST API for task management with user authentication
```

### 2. Review code
```
Use the review_code tool to review this Python function for security and performance issues: [paste code]
```

### 3. Analyze execution errors
```
Use the analyze_execution tool to help me debug this error: [paste code and error]
```

## 🏗️ Architecture

```
plan-mcp/
├── plan_mcp/
│   ├── api/              # Gemini API integration
│   ├── tools/            # MCP tools (planner, reviewer, analyzer)
│   ├── prompts/          # System prompts for Gemini
│   ├── utils/            # Utilities (logging, etc.)
│   ├── config.py         # Configuration management
│   ├── models.py         # Pydantic data models
│   └── server.py         # MCP server implementation
└── README.md
```

## 🤝 Workflow Example

1. **Human → Claude**: "Help me build a web scraper"
2. **Claude → Plan-MCP**: Requests project plan
3. **Plan-MCP → Gemini**: Analyzes requirements
4. **Gemini → Plan-MCP**: Returns structured plan
5. **Plan-MCP → Claude**: Delivers plan
6. **Claude**: Implements first task
7. **Claude → Plan-MCP**: Submits code for review
8. **Plan-MCP → Gemini**: Reviews code
9. **Gemini → Plan-MCP**: Provides feedback
10. **Plan-MCP → Claude**: Delivers improvements
11. **Cycle continues...**

## 📚 API Reference

### Tools

#### `plan_project`
- **Description**: Create a comprehensive project plan
- **Parameters**:
  - `description` (required): Project description
  - `requirements`: List of specific requirements
  - `constraints`: Project constraints
  - `tech_stack`: Preferred technologies

#### `review_code`
- **Description**: Review code for quality and issues
- **Parameters**:
  - `code` (required): Code to review
  - `language` (required): Programming language
  - `context`: Additional context
  - `focus_areas`: Specific areas to focus on

#### `analyze_execution`
- **Description**: Analyze execution results and debug errors
- **Parameters**:
  - `code` (required): Code that was executed
  - `execution_output` (required): Output or error messages
  - `expected_behavior`: What the code should do
  - `error_messages`: Specific error messages
  - `language`: Programming language (default: python)

## 🧪 Development

### Set up development environment

```bash
# Clone the repository
git clone https://github.com/bee4come/plan-mcp.git
cd plan-mcp

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

### Code quality

```bash
# Format code
black plan_mcp/

# Lint code
ruff check plan_mcp/

# Type checking
mypy plan_mcp/
```

## 🐛 Troubleshooting

### Common Issues

1. **"GEMINI_API_KEY not found"**
   - Ensure your API key is set in environment variables: `export GEMINI_API_KEY="your_key_here"`
   - Or create a `.env` file in your working directory with `GEMINI_API_KEY=your_key_here`
   - Get your API key from: https://makersuite.google.com/app/apikey

2. **Connection errors**
   - Verify your internet connection
   - Check if the Gemini API is accessible
   - Ensure your API key has proper permissions

3. **MCP connection issues**
   - Restart Claude Code after configuration
   - Check that the server starts without errors
   - Look at Claude Code logs for errors

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Google Gemini for powerful AI capabilities
- Anthropic for Claude and the MCP protocol
- The open-source community for inspiration