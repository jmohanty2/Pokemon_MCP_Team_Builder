# Validation

Run `python -m pytest -q`, `python -m ruff check pokemon_mcp server.py tests scripts`,
`python -m scripts.demo`, and `python -m pip check` after installing `.[dev]`.

Offline tests initialize an HTTP MCP session for each specialist, check its exact
three-tool registry, invoke a representative tool, and verify rejection of a tool
owned by another service. They also check the Strategist-to-Analyst typed-roster
handoff, service configuration, preserved tutorial outputs, all curated cores and
playstyles, type matchups/immunities, invalid inputs and mocked API failures.

For real process/protocol validation, start all three modules and run
`python -m scripts.check_services`. This discovers each registry and passes a team
between two independent MCP sessions. It needs no external API and does not prove
PokéAPI, ChatGPT or Render connectivity.

For live validation, call Data Expert `get_pokemon_info(name="pikachu")` and
Analyst `analyze_team(pokemon_names="charizard,garchomp")`. Require real stats/types;
service-error text is not a passing result. Check each deployed Render URL
separately. Tests do not prove competitive legality or winning performance.
