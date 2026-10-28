"""Check three running MCP processes and perform an offline typed-team handoff."""
import argparse
import asyncio
import json
from contextlib import AsyncExitStack

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main(base_port: int = 8000) -> None:
    expected = {
        "data": {"get_pokemon_info", "get_pokemon_moves", "list_popular_pokemon"},
        "strategist": {"suggest_example_team", "list_team_candidates", "create_tournament_squad"},
        "analyst": {"analyze_team", "analyze_team_types", "analyze_type_matchup"},
    }
    sessions = {}
    async with AsyncExitStack() as stack:
        for port, (service, tools) in enumerate(expected.items(), start=base_port):
            client = await stack.enter_async_context(httpx.AsyncClient(trust_env=False))
            response = await client.get(f"http://127.0.0.1:{port}/health")
            response.raise_for_status()
            assert response.json() == {"status": "ok", "service": service}
            read, write, _ = await stack.enter_async_context(streamable_http_client(
                f"http://127.0.0.1:{port}/mcp", http_client=client,
            ))
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            assert {tool.name for tool in (await session.list_tools()).tools} == tools
            sessions[service] = session
            print(f"{service}: health, initialization and exact tool registry passed")
        original = await sessions["data"].call_tool("list_popular_pokemon", {})
        assert not original.isError and "Charizard" in original.content[0].text
        result = await sessions["strategist"].call_tool("suggest_example_team", {"core": "greninja"})
        assert not result.isError
        proposed = json.loads(result.content[0].text)
        result = await sessions["analyst"].call_tool("analyze_team_types", {"team": proposed["team"]})
        assert not result.isError
        assert json.loads(result.content[0].text) == proposed["analysis"]
        print("Independent Strategist → Analyst MCP handoff passed for six Pokémon")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-port", type=int, default=8000)
    asyncio.run(main(parser.parse_args().base_port))
