"""MCP transport and tool registration; business logic lives in testable modules."""

from __future__ import annotations

import asyncio
import json
import os

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from .pokeapi import (
    PokemonLookupError, fetch_pokemon, list_known_moves, parse_team_names, summarize_pokemon,
)
from .team_builder import CANDIDATES, build_example_team
from .type_chart import analyze_types, type_multiplier

async def get_pokemon_info(name: str) -> str:
    """Retrieve live Pokémon types, base stats and abilities by name."""
    try:
        details = summarize_pokemon(await fetch_pokemon(name))
    except (PokemonLookupError, ValueError):
        return f"No data found for Pokémon: {name}"
    stats = ", ".join(f"{key}: {value}" for key, value in details["base_stats"].items())
    abilities = ", ".join(x["name"] for x in details["abilities"])
    return (
        f"Name: {details['name'].capitalize()}\n"
        f"Types: {', '.join(details['types'])}\n"
        f"Abilities: {abilities}\n"
        f"Stats: {stats}\n"
        f"Source: {details['source']}"
    )


async def get_pokemon_moves(name: str, limit: int = 30) -> str:
    """Get PokéAPI-recorded moves, NOT a format-specific legal moveset."""
    try:
        payload = list_known_moves(await fetch_pokemon(name), limit=limit)
        return json.dumps(payload, indent=2)
    except (PokemonLookupError, ValueError) as exc:
        return f"Could not retrieve moves: {exc}"


async def analyze_team(pokemon_names: str) -> str:
    """Analyze type weaknesses for 1–6 comma-separated Pokémon names.

    Example: "Greninja, Corviknight, Garchomp". Retrieves types from PokéAPI.
    Does not model items, abilities, format-specific rules or battle mechanics.
    """
    try:
        names = parse_team_names(pokemon_names)
        records = await asyncio.gather(*(fetch_pokemon(name) for name in names))
        team = [
            {"name": details["name"], "types": summarize_pokemon(details)["types"]}
            for details in records
        ]
        return json.dumps(analyze_types(team), indent=2)
    except (PokemonLookupError, ValueError, TypeError, KeyError) as exc:
        return f"Could not analyze team: {exc}"


def suggest_example_team(core: str = "greninja", playstyle: str = "balanced") -> str:
    """Suggest an educational six-Pokémon example using a role/type heuristic.

    Supports a named core from list_team_candidates and balanced, offense or
    defense playstyles. Not a legal or ranked competitive team generator.
    """
    try:
        return json.dumps(build_example_team(core=core, style=playstyle), indent=2)
    except ValueError as exc:
        return f"Cannot build example team: {exc}"


def list_team_candidates() -> str:
    """List curated Pokémon available for illustrative team suggestions."""
    return json.dumps([
        {"name": x.name, "types": list(x.types), "role": x.role}
        for x in CANDIDATES
    ], indent=2)


# Preserve the original demonstration tools and outputs for existing users.
_DEMO_SQUAD = ("charizard", "garchomp", "lucario", "dragonite", "metagross", "gardevoir")


async def create_tournament_squad() -> str:
    """Return the original tutorial's fixed demo roster (not an optimized team)."""
    found = []
    for name in _DEMO_SQUAD:
        try:
            data = await fetch_pokemon(name)
            found.append(data["name"].capitalize())
        except PokemonLookupError:
            continue
    if not found:
        return "PokéAPI is temporarily unavailable, so the squad could not be created."
    return "Tournament Squad:\n" + "\n".join(found)


def list_popular_pokemon() -> str:
    """List the six Pokémon from the original tutorial (fixed demonstration)."""
    return "\n".join(name.capitalize() for name in _DEMO_SQUAD)


def analyze_team_types(team: list[dict]) -> str:
    """Analyze a typed roster from the Strategist or Data Expert without network calls."""
    try:
        return json.dumps(analyze_types(team), indent=2)
    except (ValueError, TypeError, AttributeError) as exc:
        return f"Could not analyze team: {exc}"


def analyze_type_matchup(attacking_type: str, defending_types: list[str]) -> str:
    """Calculate one attacking type against one or two defending types, excluding abilities."""
    try:
        multiplier = type_multiplier(attacking_type, defending_types)
        return json.dumps({"attacking_type": attacking_type, "defending_types": defending_types,
                           "damage_multiplier": multiplier, "scope": "Type chart only"})
    except ValueError as exc:
        return f"Could not analyze matchup: {exc}"


SERVICE_TOOLS = {
    "data": (get_pokemon_info, get_pokemon_moves, list_popular_pokemon),
    "strategist": (list_team_candidates, suggest_example_team, create_tournament_squad),
    "analyst": (analyze_team, analyze_team_types, analyze_type_matchup),
}
SERVICE_NAMES = {
    "data": "Pokemon Data Expert",
    "strategist": "Pokemon Strategist",
    "analyst": "Pokemon Battle Analyst",
}
SERVICE_INSTRUCTIONS = {
    "data": "Retrieve live Pokémon stats, types, abilities and historical moves from PokéAPI. "
            "Move discovery does not validate competitive legality.",
    "strategist": "Build illustrative six-member teams from the curated candidate roster. "
                  "Pass the returned typed team to the Battle Analyst's analyze_team_types tool. "
                  "Suggestions do not validate competitive legality or battle outcomes.",
    "analyst": "Evaluate defensive weaknesses and type matchups. Accept typed teams from the "
               "Strategist with analyze_team_types or fetch live types with analyze_team. "
               "This is type analysis, not a battle simulator; abilities/items are excluded.",
}


def create_server(service: str, *, host: str | None = None, port: int | None = None) -> FastMCP:
    """Create an independent MCP server exposing only its specialist's tools."""
    if service not in SERVICE_TOOLS:
        raise ValueError("MCP_SERVICE must be data, strategist, or analyst")
    defaults = {"data": 8000, "strategist": 8001, "analyst": 8002}
    server = FastMCP(
        SERVICE_NAMES[service], instructions=SERVICE_INSTRUCTIONS[service],
        host=host or os.getenv("HOST", "0.0.0.0"),
        port=port if port is not None else int(os.getenv("PORT", str(defaults[service]))),
        streamable_http_path="/mcp",
    )

    @server.custom_route("/health", methods=["GET"])
    async def health_check(_: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "service": service})

    for tool in SERVICE_TOOLS[service]:
        server.tool()(tool)
    return server


def run_service(service: str) -> None:
    """Run a specialist over HTTP by default, or STDIO when configured."""
    create_server(service).run(transport=os.getenv("MCP_TRANSPORT", "streamable-http"))
