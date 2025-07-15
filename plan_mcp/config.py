"""Configuration management for Plan-MCP."""

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()


class Config(BaseModel):
    """Application configuration."""

    # Gemini API settings
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-1.5-pro"))

    # Logging
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # MCP Server settings
    server_name: str = Field(default_factory=lambda: os.getenv("MCP_SERVER_NAME", "plan-mcp"))
    server_version: str = Field(default_factory=lambda: os.getenv("MCP_SERVER_VERSION", "1.0.0"))

    # Optional settings
    max_retries: int = Field(default=3)
    timeout: int = Field(default=60)  # seconds

    def validate_config(self) -> None:
        """Validate that required configuration is present."""
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")


# Global config instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config
