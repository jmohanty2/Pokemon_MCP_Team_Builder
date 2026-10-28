import httpx
import pytest

from pokemon_mcp.pokeapi import (
    PokemonNotFound,
    fetch_pokemon,
    list_known_moves,
    normalize_name,
    parse_team_names,
    summarize_pokemon,
)


@pytest.mark.asyncio
async def test_fetch_and_summarize_without_network():
    record = {
        "name": "greninja", "id": 658,
        "types": [{"slot": 2, "type": {"name": "dark"}},
                  {"slot": 1, "type": {"name": "water"}}],
        "abilities": [{"ability": {"name": "torrent"}, "is_hidden": False}],
        "stats": [{"stat": {"name": "speed"}, "base_stat": 122}],
        "moves": [{"move": {"name": "ice-beam"}}, {"move": {"name": "dark-pulse"}}],
    }

    def handler(request):
        assert str(request.url).endswith("/pokemon/greninja")
        return httpx.Response(200, json=record)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        data = await fetch_pokemon("  Greninja ", client)
    summary = summarize_pokemon(data)
    assert summary["types"] == ["water", "dark"]
    assert summary["base_stats"]["speed"] == 122
    assert list_known_moves(data, limit=1)["truncated"]


@pytest.mark.asyncio
async def test_not_found():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(404))
    ) as client:
        with pytest.raises(PokemonNotFound):
            await fetch_pokemon("nope", client)


def test_safe_name_validation():
    assert normalize_name("Mr Mime") == "mr-mime"
    with pytest.raises(ValueError):
        normalize_name("../../etc/passwd")


def test_parse_team_names():
    assert parse_team_names("Greninja, Corviknight") == ["greninja", "corviknight"]
    with pytest.raises(ValueError):
        parse_team_names("Greninja, Greninja")
    with pytest.raises(ValueError):
        parse_team_names("Greninja, Charizard, Pikachu, Garchomp, Lucario, Dragonite, Mewtwo")


@pytest.mark.asyncio
@pytest.mark.parametrize("response", [
    httpx.Response(500), httpx.Response(200, text="not json"),
    httpx.Response(200, json={"name": "pikachu"}),
    httpx.Response(200, json=[]),
    httpx.Response(302, headers={"Location": "https://example.com"}),
])
async def test_service_errors_and_malformed_responses(response):
    from pokemon_mcp.pokeapi import PokemonServiceUnavailable

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: response)
    ) as client:
        with pytest.raises(PokemonServiceUnavailable):
            await fetch_pokemon("pikachu", client)


@pytest.mark.asyncio
async def test_timeout_is_service_error():
    from pokemon_mcp.pokeapi import PokemonServiceUnavailable

    def timeout(request):
        raise httpx.ReadTimeout("timeout", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(timeout)) as client:
        with pytest.raises(PokemonServiceUnavailable):
            await fetch_pokemon("pikachu", client)


@pytest.mark.parametrize("limit", [0, 101, -1])
def test_move_limit_validation(limit):
    with pytest.raises(ValueError, match="limit"):
        list_known_moves({"name": "pikachu"}, limit)
