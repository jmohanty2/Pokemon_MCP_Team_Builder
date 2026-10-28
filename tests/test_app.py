"""Exercise actual HTTP MCP requests and preserve the tutorial tool contracts."""
import json

import httpx
import pytest

from pokemon_mcp import app
from pokemon_mcp.pokeapi import PokemonServiceUnavailable


@pytest.mark.asyncio
@pytest.mark.parametrize("service", ["data", "strategist", "analyst"])
async def test_http_health_discovery_and_tool_calls(service):
    server = app.create_server(service)
    asgi = server.streamable_http_app()
    async with server.session_manager.run():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=asgi), base_url="http://localhost"
        ) as client:
            health = await client.get("/health")
            assert health.status_code == 200
            assert health.json() == {"status": "ok", "service": service}
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
            expected = {
                "data": {"get_pokemon_info", "get_pokemon_moves", "list_popular_pokemon"},
                "strategist": {"list_team_candidates", "suggest_example_team", "create_tournament_squad"},
                "analyst": {"analyze_team", "analyze_team_types", "analyze_type_matchup"},
            }
            assert {tool["name"] for tool in tools["tools"]} == expected[service]
            calls = {
                "data": ("list_popular_pokemon", {}),
                "strategist": ("suggest_example_team", {"core": "greninja"}),
                "analyst": ("analyze_type_matchup", {
                    "attacking_type": "rock", "defending_types": ["fire", "flying"],
                }),
            }
            name, arguments = calls[service]
            result = await rpc("tools/call", {"name": name, "arguments": arguments})
            assert not result.get("isError")
            text = result["content"][0]["text"]
            if service == "data":
                assert len(text.splitlines()) == 6
            elif service == "strategist":
                assert len(json.loads(text)["team"]) == 6
            else:
                assert json.loads(text)["damage_multiplier"] == 4
            # A specialist must reject tools owned by another MCP server.
            foreign = "suggest_example_team" if service != "strategist" else "analyze_team"
            rejected = await rpc("tools/call", {"name": foreign, "arguments": {}})
            assert rejected["isError"]



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


def test_offline_handoff_from_strategist_to_analyst():
    proposed = json.loads(app.suggest_example_team("greninja"))
    analyzed = json.loads(app.analyze_team_types(proposed["team"]))
    assert analyzed["team_size"] == 6
    assert analyzed == proposed["analysis"]
    assert "Could not analyze" in app.analyze_team_types([])


def test_invalid_service_and_independent_configuration(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    with pytest.raises(ValueError):
        app.create_server("unknown")
    assert [app.create_server(s).settings.port for s in app.SERVICE_TOOLS] == [8000, 8001, 8002]
    monkeypatch.setenv("PORT", "9000")
    assert app.create_server("analyst").settings.port == 9000
