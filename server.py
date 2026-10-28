"""Stable entry point for Render, Docker and local MCP clients.

Keep this file small: tools and business logic live in ``pokemon_mcp``.
"""

from pokemon_mcp.app import MCP_TRANSPORT, mcp

if __name__ == "__main__":
    mcp.run(transport=MCP_TRANSPORT)
