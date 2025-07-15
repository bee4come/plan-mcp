"""Plan-MCP: AI-powered project planning and code review MCP server."""
from importlib import metadata

try:
    __version__ = metadata.version(__name__)
except metadata.PackageNotFoundError:
    # 如果包未安装，则进行回退
    __version__ = "0.0.0"
