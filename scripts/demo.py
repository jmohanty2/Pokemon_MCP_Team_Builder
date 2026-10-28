"""Run the offline demo without a PokéAPI call or MCP client.

Usage: python -m scripts.demo
"""

import json

from pokemon_mcp.team_builder import build_example_team


def main() -> None:
    print("Pokémon MCP | Interview demo (educational example)\n")
    result = build_example_team("greninja", "balanced")
    print("Core:", result["core"].title())
    print("Team:")
    for number, member in enumerate(result["team"], start=1):
        print(f"  {number}. {member['name'].title()} — {member['role']}")
    print("\nShared weaknesses:")
    print(json.dumps(result["analysis"]["shared_weaknesses"], indent=2))
    print("\nDisclaimer:", result["limitations"])


if __name__ == "__main__":
    main()
