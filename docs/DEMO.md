# Three-minute interview demo

1. Start all three specialist modules following the README. Show three `/health`
   identities and connect three MCP endpoints to the host.
2. Ask the Data Expert for Greninja's stats. Explain that this requires PokéAPI;
   do not claim success if an upstream error occurs.
3. Ask the Strategist for a balanced example around Greninja. Explain deterministic
   role selection from a curated roster, not metagame optimization.
4. Pass its `team` array to the Analyst's `analyze_team_types` tool. Discuss shared
   weaknesses and 4x vulnerabilities. Demonstrate a standalone rock attack against
   fire/flying via `analyze_type_matchup`.
5. Show `python -m scripts.check_services`, tests, CI, and architecture notes.

The host coordinates tools; no automatic host orchestration is bundled. The
protocol smoke script performs a deterministic handoff for reproducible validation.
For a network-free algorithm demo without servers use `python -m scripts.demo`.

**Why three MCPs?** Independent discovery, deployment and focused tool boundaries.
The cost is more processes, URLs and operational work. Shared libraries keep rules
consistent. One server would also be suitable for a small project.

**Are the teams tournament legal?** No legality validator or competitive evaluation
is implemented. Analysis covers standard type matchups only.
