# 3-minute interview demonstration

## Thirty-second introduction

> I built a Python MCP server that connects an AI assistant to a real Pokémon data API. I then extended the original demonstration with testable, explainable algorithms for team suggestions and defensive type analysis. It runs remotely using Streamable HTTP and deploys with Docker on Render.

## Demonstration

1. **Show a live lookup.** Ask: "Use Pokémon MCP to tell me Greninja's types, abilities and base stats." Explain that ChatGPT invokes a tool, and the server fetches structured PokéAPI data.
2. **Show an example team.** Ask: "Use `suggest_example_team` to build a balanced example team around Greninja, and explain why each Pokémon was selected." Show the six roles and the type-overlap analysis.
3. **Show transparent limitations.** Ask: "Is this automatically legal in Gen 9 OU?" Answer no: the heuristic does not validate format-specific restrictions, sets, items or moves.
4. **Show engineering maturity.** Open `tests/`, `.github/workflows/ci.yml`, and `docs/ARCHITECTURE.md`. Demonstrate that core algorithm tests run offline.

## Demo without ChatGPT or internet

```bash
python -m scripts.demo
```

## Interview Q&A

**Why use MCP instead of just writing a chatbot?** MCP exposes structured tools in a protocol that compatible clients can discover and call. The Python service owns the data retrieval and algorithms; the assistant chooses when to use them.

**Why one MCP server instead of three?** Multiple tools can coexist in one server. Keeping them together reduces operational complexity for a small, coherent project.

**What was the hardest engineering tradeoff?** A basic type matcher is easy to mistake for a competitive optimizer. I deliberately label suggested teams as educational and separate explainable heuristics from unimplemented legality checking or simulations.

**How would you improve it?** Add battle-format restrictions, a Showdown validator, curated competitive sets, usage statistics and reproducible battle simulations.
