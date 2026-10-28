"""Independent strategist MCP server entry point."""
from .app import run_service

if __name__ == "__main__":
    run_service("strategist")
