# Contributing to Plan-MCP

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/bee4come/plan-mcp.git
cd plan-mcp
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev]"
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

## Code Quality

Before submitting changes, ensure code quality:

```bash
# Format code
black plan_mcp/

# Lint code
ruff check plan_mcp/

# Type checking
mypy plan_mcp/

# Run tests
pytest
```

## Release Process

### For Maintainers

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with new features/fixes
3. Create and push a git tag:
```bash
git tag v1.0.1
git push origin v1.0.1
```

This will automatically trigger the PyPI release via GitHub Actions.

### Testing Releases

To test releases before publishing:

1. Build the package locally:
```bash
python -m build
```

2. Test installation:
```bash
pip install dist/plan_mcp-*.whl
```

3. Test functionality:
```bash
plan-mcp --help
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all tests pass
5. Submit a pull request

## Issue Reporting

When reporting issues, please include:
- Python version
- Operating system
- Error messages/logs
- Steps to reproduce