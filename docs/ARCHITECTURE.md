# Architecture and engineering decisions

## System overview

The MCP client (for example ChatGPT) discovers tools exposed over Streamable HTTP. Tool handlers run inside `pokemon_mcp/app.py` and call independent application modules. Data lookups are read-only HTTP calls to public PokéAPI.

```text
MCP client
    |
    v
server.py -> pokemon_mcp/app.py (tool definitions, /mcp and /health)
                 |                 |                    |
                 v                 v                    v
          pokeapi.py         team_builder.py        type_chart.py
                 |                 |                    ^
                 v                 +--------------------+
              PokéAPI              shared deterministic logic
```

## Why a single MCP server?

One server is enough: separate tools handle retrieval, generation and analysis. Splitting these into three independently deployed servers adds hosting, discovery and authentication overhead without improving team quality. Components can be separated later if there are real scaling or ownership reasons.

## Design decisions

1. **Keep the public entry point stable.** `server.py`, the `/mcp` path, `/health` remain stable. The standalone project uses its own Render service name.
2. **Separate I/O and logic.** `pokeapi.py` handles HTTP and validation. Type matchup code has no network dependency.
3. **Make algorithm limitations obvious.** The builder selects from a curated roster, not live usage data or official legality rules.
4. **Return machine-readable structures when helpful.** Suggestions, moves and team analysis return JSON strings suitable for an MCP client.
5. **Simple user inputs.** Team analysis accepts comma-separated Pokémon names and resolves typings itself.
6. **Design for testability.** `httpx.MockTransport` verifies API handling without relying on third-party uptime.

## Team builder algorithm

Start with a requested core Pokémon and select candidates to cover six useful roles. For each available candidate, evaluate overlapping weaknesses, whether the candidate resists existing vulnerabilities, and duplicated typing. Select the best-scoring candidate for each unfilled role. The result is reproducible; it is not a trained model or a claim about statistical competitive strength.

The algorithm currently ignores move and item compatibility, matchups against a metagame sample, speed benchmarks, dynamic battle state, and legal format restrictions. Improving those areas is in the roadmap.

## Security and reliability

- The API adapter validates Pokémon names and uses an explicit request timeout.
- Connections do not follow redirects, and external calls go to a fixed PokéAPI host.
- The server never requires or stores user secrets.
- The public endpoint is unauthenticated. Restrict access if sensitive capabilities are added.
- A health route supports platform readiness checks.
- Unit tests use canned HTTP responses rather than requiring internet access.

## Key modules

| Path | Purpose |
| --- | --- |
| `server.py` | Local and production entry point |
| `pokemon_mcp/app.py` | MCP tool registration and HTTP health route |
| `pokemon_mcp/pokeapi.py` | Input validation and PokéAPI service calls |
| `pokemon_mcp/type_chart.py` | Static type-effectiveness and team coverage analysis |
| `pokemon_mcp/team_builder.py` | Explainable, deterministic example team assembly |
| `tests/` | Offline unit tests |
| `.github/workflows/ci.yml` | Continuous integration for tests and lint |
