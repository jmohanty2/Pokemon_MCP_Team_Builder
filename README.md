# Pokémon MCP Team Builder — Three Specialist Servers

A Python student portfolio project exposing **three independent Model Context
Protocol servers**. ChatGPT (or another MCP host) coordinates data retrieval,
example team construction, and defensive type analysis by calling their tools.

| MCP server | Responsibility | Tools | Local port |
| --- | --- | --- | --- |
| Data Expert | Live PokéAPI stats, abilities, types and historical moves | `get_pokemon_info`, `get_pokemon_moves`, `list_popular_pokemon` | 8000 |
| Strategist | Deterministic six-member example teams and curated roles | `suggest_example_team`, `list_team_candidates`, `create_tournament_squad` | 8001 |
| Battle Analyst | Defensive weaknesses and type matchups | `analyze_team`, `analyze_team_types`, `analyze_type_matchup` | 8002 |

Each server has its own MCP identity, tool registry, process, `/mcp` endpoint,
and `/health` route. They share reusable Python modules in this repository.
There is no combined seven-tool endpoint. Servers do not call one another:
the MCP host passes results between them.

## Quick start

Python 3.11+ is required. No API keys are needed.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
```

Run each command in a separate terminal with the virtual environment activated:

```bash
python -m pokemon_mcp.data_server        # port 8000
python -m pokemon_mcp.strategist_server  # port 8001
python -m pokemon_mcp.analyst_server     # port 8002
```

Register all three URLs with your local MCP host:
`http://localhost:8000/mcp`, `http://localhost:8001/mcp`, and
`http://localhost:8002/mcp`. Cloud-hosted ChatGPT needs public HTTPS URLs instead.
Health responses identify the service, for example
`{"status":"ok","service":"analyst"}`.

Alternatively run `MCP_SERVICE=analyst python server.py`.
`MCP_SERVICE` accepts `data` (default), `strategist`, or `analyst`.
`HOST` and `PORT` override HTTP binding; `MCP_TRANSPORT=stdio` enables local
STDIO clients. With STDIO configure three client entries, each launching its
respective `python -m pokemon_mcp.<role>_server` command using the venv interpreter.

## Example coordination

Ask your MCP host: “Build an example team around Greninja and explain its weaknesses.”

1. Data Expert: call `get_pokemon_info(name="greninja")` for live reference data.
2. Strategist: call `suggest_example_team(core="greninja", playstyle="balanced")`.
3. Battle Analyst: pass the result's `team` array to `analyze_team_types(team=...)`.
4. Ask the Strategist for an alternative playstyle and compare the Analyst's reports.

The Strategist uses a documented curated roster, not arbitrary live candidates.
Its `team` array contains names, types and roles. The Analyst can accept that
array without further network calls, or resolve live typings from 1–6
comma-separated names via `analyze_team(pokemon_names="charizard,garchomp")`.
`analyze_type_matchup(attacking_type="rock", defending_types=["fire","flying"])`
returns a 4x multiplier.

For protocol-level checks against all three running services:

```bash
python -m scripts.check_services
```

For an offline algorithm demonstration without servers: `python -m scripts.demo`.

## Deploy three services on Render

Create a **new Blueprint** connected to this repository. `render.yaml` defines
`pokemon-mcp-data`, `pokemon-mcp-strategist`, and `pokemon-mcp-analyst`, all using
the same Dockerfile with different `MCP_SERVICE` values. Each service uses its own
container and port 8000 internally; their public hostnames differ. Free-service
availability and quotas depend on your Render account.

Check each public `/health`, then register each public HTTPS `/mcp` URL as a
separate MCP connection. Refresh tool discovery when changing services. This
project does not change the original `Pokemon_MCP_Server` repository or deployment.
For Docker locally, build `docker build -t pokemon-mcp .` and run three containers
with `-e MCP_SERVICE=<role>` and distinct host ports mapped to container port 8000.

## Scope and tradeoffs

This is an educational prototype, not a competitive optimizer or battle simulator.
Historical move discovery does not establish format-specific legality. Analysis
uses the standard modern 18-type chart, excluding abilities, items, moves, Tera,
EVs, speed benchmarks, and battle outcomes. Shared weaknesses affect at least three
members. Individual reports distinguish 0x, 0.25x, 0.5x, 1x, 2x and 4x matchups.

Three servers demonstrate independent deployment and host-mediated coordination,
but add three processes, connections and deployment lifecycles. They do not
inherently make suggestions stronger. No LLM, automatic cross-server orchestrator,
or claim of tournament legality is embedded in these services.

## Engineering and interview material

```bash
python -m pytest -q
python -m ruff check pokemon_mcp server.py tests scripts
python -m pip check
```

CI runs offline tests and lint. See [architecture](docs/ARCHITECTURE.md),
[validation](docs/TESTING.md), [interview demo](docs/DEMO.md), and
[roadmap](docs/ROADMAP.md).

The public services have no authentication; do not add private data or write
capabilities without appropriate access controls. PokéAPI requests use timeouts,
validated names, a fixed host and TLS verification.

## Attribution

Based on the 2MinutesPy Pokémon MCP tutorial. The original three demo tools remain
available across the specialist servers; their single-server connection layout
has changed. Pokémon data comes from [PokéAPI](https://pokeapi.co/).
This unofficial fan project is not affiliated with Nintendo, Game Freak or
The Pokémon Company.
