"""Docker/Render entry point: select data, strategist or analyst with MCP_SERVICE."""
import os

from pokemon_mcp.app import run_service

if __name__ == "__main__":
    run_service(os.getenv("MCP_SERVICE", "data"))
