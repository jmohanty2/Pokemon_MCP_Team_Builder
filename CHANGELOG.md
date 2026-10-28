# Changelog

## 2.0.0 — Proposed portfolio upgrade

### Added

- Clean Python package layout with separated MCP transport, PokéAPI networking, team selection and defensive type analysis.
- New MCP tools: `get_pokemon_moves`, `list_team_candidates`, `suggest_example_team`, and `analyze_team`.
- Clear testable and explainable six-Pokémon example suggestions.
- Offline tests for type calculations, team construction and mocked HTTP requests.
- GitHub Actions test pipeline, ignore patterns, architecture notes and interview demonstration guide.

### Preserved

- Existing MCP tools: `get_pokemon_info`, `create_tournament_squad`, and `list_popular_pokemon`.
- Separate Render service configuration and stable `/mcp` and `/health` paths.

### Explicitly not implemented

- Competitive tier or moveset legality, EV and nature optimization, damage calculation, Pokémon Showdown export, and battle win-rate simulation.

### Repository status

Standalone project extracted from the Pokémon MCP portfolio upgrade.
