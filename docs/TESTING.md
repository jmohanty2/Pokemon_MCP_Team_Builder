# Validation guide

Install development dependencies with `python -m pip install -e '.[dev]'`, then run:

```bash
python -m pytest -q
python -m ruff check pokemon_mcp server.py tests scripts
python -m scripts.demo
python -m pip check
```

The 32 offline cases cover team construction across all candidate cores and three
playstyles, representative single/dual type matchups, fourfold weaknesses,
immunities, shared weaknesses, input validation, HTTP failures/timeouts,
malformed API responses, and preserved tutorial outputs. An in-process HTTP MCP
test initializes a session, discovers all seven tools, and calls both an original
tool and the new team builder. No account, secret, external API or LLM is needed.

The static chart describes modern standard type matchups. Results explicitly
exclude abilities and items (for example, Rotom's Levitate immunity is not modeled).
The curated roster supplies illustrative roles; those roles do not certify a legal
moveset. Shared weaknesses mean three or more members are weak to an attacking type.
Each member also reports all 18 damage multipliers to distinguish 2x from 4x.

For a manual live check, start `python server.py`. Verify `/health` returns
`{"status":"ok"}`, then use an MCP client at `/mcp` to call
`get_pokemon_info(name="pikachu")` and `analyze_team(pokemon_names="charizard,garchomp")`.
Require real stats/types in the responses; an unavailable-service message is not
a successful live check. The test suite mocks API access and does not establish
PokéAPI availability, Render health, ChatGPT connectivity or competitive strength.

Build the production container with `docker build -t pokemon-mcp .`, then run
`docker run --rm -p 8000:8000 pokemon-mcp` and repeat the health/MCP checks.
In managed proxy environments, package downloads may need the configured proxy
CA mounted during the build; preserve TLS verification. A local image check does
not deploy or validate the existing Render service.
