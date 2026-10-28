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
from .type_chart import analyze_types

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "streamable-http")

mcp = FastMCP(
    "Pokemon MCP Server",
    instructions=(
        "Use these read-only tools for Pokémon data and *illustrative* team suggestions. "
        "The team builder is a heuristic demonstration and does NOT validate "
        "competitive legality, movesets, battle outcomes, or tournament viability."
    ),
    host=HOST,
    port=PORT,
    streamable_http_path="/mcp",
)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


@mcp.tool()
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


@mcp.tool()
async def get_pokemon_moves(name: str, limit: int = 30) -> str:
    """Get PokéAPI-recorded moves, NOT a format-specific legal moveset."""
    try:
        payload = list_known_moves(await fetch_pokemon(name), limit=limit)
        return json.dumps(payload, indent=2)
    except (PokemonLookupError, ValueError) as exc:
        return f"Could not retrieve moves: {exc}"


@mcp.tool()
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


@mcp.tool()
def suggest_example_team(core: str = "greninja", playstyle: str = "balanced") -> str:
    """Suggest an educational six-Pokémon example using a role/type heuristic.

    Supports a named core from list_team_candidates and balanced, offense or
    defense playstyles. Not a legal or ranked competitive team generator.
    """
    try:
        return json.dumps(build_example_team(core=core, style=playstyle), indent=2)
    except ValueError as exc:
        return f"Cannot build example team: {exc}"


@mcp.tool()
def list_team_candidates() -> str:
    """List curated Pokémon available for illustrative team suggestions."""
    return json.dumps([
        {"name": x.name, "types": list(x.types), "role": x.role}
        for x in CANDIDATES
    ], indent=2)


# Preserve the original demonstration tools and outputs for existing users.
_DEMO_SQUAD = ("charizard", "garchomp", "lucario", "dragonite", "metagross", "gardevoir")


@mcp.tool()
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


@mcp.tool()
def list_popular_pokemon() -> str:
    """List the six Pokémon from the original tutorial (fixed demonstration)."""
    return "\n".join(name.capitalize() for name in _DEMO_SQUAD)
