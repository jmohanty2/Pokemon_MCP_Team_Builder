"""Exercise actual HTTP MCP requests and preserve the tutorial tool contracts."""
import json

import httpx
import pytest

from pokemon_mcp import app
from pokemon_mcp.pokeapi import PokemonServiceUnavailable


@pytest.mark.asyncio
async def test_http_health_discovery_and_tool_calls():
    asgi = app.mcp.streamable_http_app()
    async with app.mcp.session_manager.run():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=asgi), base_url="http://localhost"
        ) as client:
            health = await client.get("/health")
            assert health.status_code == 200
            assert health.json() == {"status": "ok"}
            headers = {"Accept": "application/json, text/event-stream"}

            async def rpc(method, params, request_id=1):
                response = await client.post("/mcp", headers=headers, json={
                    "jsonrpc": "2.0", "id": request_id, "method": method, "params": params,
                })
                assert response.status_code == 200, response.text
                if response.headers.get("mcp-session-id"):
                    headers["mcp-session-id"] = response.headers["mcp-session-id"]
                if response.headers["content-type"].startswith("text/event-stream"):
                    return json.loads(next(
                        line[6:] for line in response.text.splitlines()
                        if line.startswith("data: ")
                    ))["result"]
                return response.json()["result"]

            initialized = await rpc("initialize", {
                "protocolVersion": "2025-03-26", "capabilities": {},
                "clientInfo": {"name": "portfolio-test", "version": "1.0"},
            })
            headers["mcp-protocol-version"] = initialized["protocolVersion"]
            response = await client.post("/mcp", headers=headers, json={
                "jsonrpc": "2.0", "method": "notifications/initialized",
            })
            assert response.status_code == 202
            tools = await rpc("tools/list", {})
            assert {tool["name"] for tool in tools["tools"]} == {
                "get_pokemon_info", "create_tournament_squad", "list_popular_pokemon",
                "get_pokemon_moves", "list_team_candidates", "suggest_example_team",
                "analyze_team",
            }
            result = await rpc("tools/call", {
                "name": "list_popular_pokemon", "arguments": {},
            })
            assert result["content"][0]["text"].splitlines() == [
                "Charizard", "Garchomp", "Lucario", "Dragonite", "Metagross", "Gardevoir",
            ]
            result = await rpc("tools/call", {
                "name": "suggest_example_team", "arguments": {"core": "greninja"},
            })
            assert len(json.loads(result["content"][0]["text"])["team"]) == 6


@pytest.mark.asyncio
async def test_original_tools_and_live_analysis(monkeypatch):
    async def fetch(name):
        return {
            "name": name, "types": [{"slot": 1, "type": {"name": "electric"}}],
            "abilities": [{"ability": {"name": "static"}, "is_hidden": False}],
            "stats": [{"stat": {"name": "speed"}, "base_stat": 90}],
        }

    monkeypatch.setattr(app, "fetch_pokemon", fetch)
    assert await app.get_pokemon_info("pikachu") == (
        "Name: Pikachu\nTypes: electric\nAbilities: static\nStats: speed: 90\n"
        "Source: https://pokeapi.co/api/v2/pokemon/pikachu"
    )
    assert await app.create_tournament_squad() == (
        "Tournament Squad:\n" + app.list_popular_pokemon()
    )
    result = json.loads(await app.analyze_team("pikachu"))
    assert result["weakness_counts"] == {"ground": 1}
    assert "Could not analyze" in await app.analyze_team("pikachu,pikachu")

    async def unavailable(name):
        raise PokemonServiceUnavailable("offline")

    monkeypatch.setattr(app, "fetch_pokemon", unavailable)
    assert await app.get_pokemon_info("pikachu") == "No data found for Pokémon: pikachu"
    assert "could not be created" in await app.create_tournament_squad()
    assert "Could not retrieve moves" in await app.get_pokemon_moves("pikachu")
    assert "Could not analyze" in await app.analyze_team("pikachu")
