#!/usr/bin/env python3
"""MCP server launcher that follows protocol specifications."""

import os
import sys
from pathlib import Path

def setup_environment():
    """Set up the environment for the MCP server."""
    # Get script directory
    script_dir = Path(__file__).parent.resolve()
    
    # Add to Python path
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    
    # Load environment variables from .env if it exists
    env_file = script_dir / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value

def main():
    """Main entry point."""
    setup_environment()
    
    try:
        # Import and run FastMCP server
        from plan_mcp.fastmcp_server import mcp
        mcp.run()
    except KeyboardInterrupt:
        sys.stderr.write("Server interrupted\n")
    except Exception as e:
        sys.stderr.write(f"Server error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()