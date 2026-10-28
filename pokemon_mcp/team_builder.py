"""Explainable demonstration team suggestions with deterministic role coverage.

These suggestions deliberately are NOT presented as competitively validated sets.
The candidate catalog is a teaching/demo dataset and will evolve with the project.
"""

from __future__ import annotations

from dataclasses import dataclass

from .type_chart import TYPES, type_multiplier, analyze_types


@dataclass(frozen=True)
class Candidate:
    name: str
    types: tuple[str, ...]
    role: str


# Curated *examples*, not a representation of a current format's legal metagame.
CANDIDATES: tuple[Candidate, ...] = (
    Candidate("greninja", ("water", "dark"), "special attacker"),
    Candidate("charizard", ("fire", "flying"), "special attacker"),
    Candidate("garchomp", ("dragon", "ground"), "physical attacker"),
    Candidate("lucario", ("fighting", "steel"), "physical attacker"),
    Candidate("dragonite", ("dragon", "flying"), "late-game cleaner"),
    Candidate("metagross", ("steel", "psychic"), "physical attacker"),
    Candidate("gardevoir", ("psychic", "fairy"), "special attacker"),
    Candidate("great-tusk", ("ground", "fighting"), "hazard control"),
    Candidate("corviknight", ("flying", "steel"), "defensive pivot"),
    Candidate("gholdengo", ("steel", "ghost"), "special attacker"),
    Candidate("dragapult", ("dragon", "ghost"), "speed control"),
    Candidate("kingambit", ("dark", "steel"), "late-game cleaner"),
    Candidate("rillaboom", ("grass",), "physical attacker"),
    Candidate("clodsire", ("poison", "ground"), "defensive pivot"),
    Candidate("rotom-wash", ("electric", "water"), "defensive pivot"),
    Candidate("meowscarada", ("grass", "dark"), "speed control"),
    Candidate("clefable", ("fairy",), "defensive pivot"),
    Candidate("skarmory", ("steel", "flying"), "hazard control"),
    Candidate("volcarona", ("bug", "fire"), "special attacker"),
)
CATALOG = {item.name: item for item in CANDIDATES}
ROLE_ORDER = (
    "hazard control", "defensive pivot", "physical attacker", "special attacker",
    "speed control", "late-game cleaner",
)


def _cost(candidate: Candidate, team: list[Candidate]) -> float:
    """Penalize overlapping weaknesses and reward defensive answers."""
    cost = 0.0
    for attack_type in sorted(TYPES):
        existing = [type_multiplier(attack_type, member.types) for member in team]
        multiplier = type_multiplier(attack_type, candidate.types)
        weak_count = sum(m > 1 for m in existing)
        if multiplier > 1:
            cost += weak_count * 2 + (1 if multiplier == 4 else 0)
        if weak_count and multiplier < 1:
            cost -= min(weak_count, 2) * 0.75
    # Encourage different type combinations as a modest tiebreaker.
    cost += sum(0.5 for member in team if set(member.types) == set(candidate.types))
    return cost


def build_example_team(core: str = "greninja", style: str = "balanced") -> dict:
    """Build a six-member *example* team from a fixed, openly documented pool.

    This is deterministic and local: no external calls, no claims of legal sets.
    """
    key = core.strip().lower().replace(" ", "-")
    if key not in CATALOG:
        raise ValueError(
            "That Pokémon is not yet in the demo candidate pool. "
            "Use a name from list_team_candidates or extend the catalog."
        )
    style_key = style.strip().lower()
    styles = {
        "balanced": ROLE_ORDER,
        "offense": ("speed control", "physical attacker", "special attacker", "late-game cleaner", "hazard control", "defensive pivot"),
        "defense": ("defensive pivot", "hazard control", "late-game cleaner", "special attacker", "physical attacker", "speed control"),
    }
    if style_key not in styles:
        raise ValueError("Playstyle must be balanced, offense, or defense")
    team = [CATALOG[key]]
    for role in styles[style_key]:
        if len(team) == 6:
            break
        if any(member.role == role for member in team):
            continue
        choices = [item for item in CANDIDATES if item not in team and item.role == role]
        if not choices:
            continue
        team.append(min(choices, key=lambda item: (_cost(item, team), item.name)))
    if len(team) < 6:
        remaining = [item for item in CANDIDATES if item not in team]
        for item in sorted(remaining, key=lambda item: (_cost(item, team), item.name)):
            if len(team) == 6:
                break
            team.append(item)
    roster = [{"name": m.name, "types": list(m.types), "role": m.role} for m in team]
    return {
        "core": key,
        "style": style_key,
        "team": roster,
        "analysis": analyze_types(roster),
        "method": "Greedy role coverage with type-weakness heuristic and a curated candidate pool",
        "limitations": (
            "Educational team suggestion only: no tier eligibility, move legality, "
            "items, abilities, EVs, speed tiers, usage statistics or battle simulations validated. "
            "Do not present as tournament-ready without external verification."
        ),
    }
