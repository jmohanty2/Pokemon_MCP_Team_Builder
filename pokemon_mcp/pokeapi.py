"""Async PokéAPI adapter with explicit errors and safe input validation."""

from __future__ import annotations

import re

import httpx

POKEAPI_BASE = "https://pokeapi.co/api/v2"
_NAME = re.compile(r"^[a-z0-9-]{1,80}$")


class PokemonLookupError(Exception):
    """Base class for expected PokéAPI lookup failures."""


class PokemonNotFound(PokemonLookupError):
    """PokéAPI returned no matching Pokémon."""


class PokemonServiceUnavailable(PokemonLookupError):
    """PokéAPI could not be reached or returned an unexpected response."""


def normalize_name(name: str) -> str:
    if not isinstance(name, str):
        raise ValueError("Pokémon name must be a string")
    normalized = name.strip().lower().replace(" ", "-")
    if not _NAME.fullmatch(normalized):
        raise ValueError("Pokémon name must be 1–80 letters, numbers or hyphens")
    return normalized


def parse_team_names(names: str) -> list[str]:
    """Parse a comma-separated team of up to six names."""
    if not isinstance(names, str):
        raise ValueError("Please provide Pokémon names separated by commas")
    members = [normalize_name(value) for value in names.split(",")]
    if not 1 <= len(members) <= 6 or len(set(members)) != len(members):
        raise ValueError("Provide 1–6 different Pokémon names, separated by commas")
    return members


async def fetch_pokemon(name: str, client: httpx.AsyncClient | None = None) -> dict:
    """Retrieve the PokéAPI Pokémon record, reusing a supplied client in tests."""
    slug = normalize_name(name)
    if client is None:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as owned:
            return await fetch_pokemon(slug, owned)
    try:
        response = await client.get(f"{POKEAPI_BASE}/pokemon/{slug}")
        if response.status_code == 404:
            raise PokemonNotFound(slug)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or "name" not in data:
            raise PokemonServiceUnavailable("Unexpected response from PokéAPI")
        # Validate the fields consumed by tools at the external service boundary.
        try:
            summarize_pokemon(data)
            list_known_moves(data)
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise PokemonServiceUnavailable("Unexpected response from PokéAPI") from exc
        return data
    except PokemonLookupError:
        raise
    except (httpx.HTTPError, ValueError) as exc:
        raise PokemonServiceUnavailable("PokéAPI is currently unavailable") from exc


def summarize_pokemon(data: dict) -> dict:
    """Convert raw PokéAPI payload into a small stable record."""
    return {
        "name": data["name"],
        "id": data.get("id"),
        "types": [x["type"]["name"] for x in sorted(data["types"], key=lambda x: x["slot"])],
        "abilities": [
            {"name": x["ability"]["name"], "hidden": x["is_hidden"]}
            for x in data["abilities"]
        ],
        "base_stats": {x["stat"]["name"]: x["base_stat"] for x in data["stats"]},
        "source": f"{POKEAPI_BASE}/pokemon/{data['name']}",
    }


def list_known_moves(data: dict, limit: int = 30) -> dict:
    """List recorded learnable moves; format legality is not implied."""
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    moves = sorted({row["move"]["name"] for row in data.get("moves", [])})
    return {
        "pokemon": data["name"],
        "move_count": len(moves),
        "moves": moves[:limit],
        "truncated": len(moves) > limit,
        "source": f"{POKEAPI_BASE}/pokemon/{data['name']}",
        "warning": "Historical move availability is NOT the same as legality in a specific competitive format.",
    }
