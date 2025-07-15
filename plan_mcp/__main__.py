#!/usr/bin/env python3
"""Main entry point for plan-mcp package."""

import os
import sys
from pathlib import Path

def main():
    """Main entry point for the plan-mcp CLI."""
    # Setup environment - load .env if available
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
    
    try:
        # Import FastMCP server
        from .fastmcp_server import mcp
        mcp.run()
    except KeyboardInterrupt:
        sys.stderr.write("Server interrupted\n")
    except Exception as e:
        sys.stderr.write(f"Server failed to start: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
