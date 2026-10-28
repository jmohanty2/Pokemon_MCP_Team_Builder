"""Deterministic Pokémon type-effectiveness calculations.

Values model the standard 18-type matchup chart, not temporary game mechanics.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable

# For every attacking type: defending types it deals 2x, 0.5x, or 0x to.
ATTACK_CHART: dict[str, dict[str, frozenset[str]]] = {
    "normal": {"strong": frozenset(), "resisted": frozenset({"rock", "steel"}), "immune": frozenset({"ghost"})},
    "fire": {"strong": frozenset({"grass", "ice", "bug", "steel"}), "resisted": frozenset({"fire", "water", "rock", "dragon"}), "immune": frozenset()},
    "water": {"strong": frozenset({"fire", "ground", "rock"}), "resisted": frozenset({"water", "grass", "dragon"}), "immune": frozenset()},
    "electric": {"strong": frozenset({"water", "flying"}), "resisted": frozenset({"electric", "grass", "dragon"}), "immune": frozenset({"ground"})},
    "grass": {"strong": frozenset({"water", "ground", "rock"}), "resisted": frozenset({"fire", "grass", "poison", "flying", "bug", "dragon", "steel"}), "immune": frozenset()},
    "ice": {"strong": frozenset({"grass", "ground", "flying", "dragon"}), "resisted": frozenset({"fire", "water", "ice", "steel"}), "immune": frozenset()},
    "fighting": {"strong": frozenset({"normal", "ice", "rock", "dark", "steel"}), "resisted": frozenset({"poison", "flying", "psychic", "bug", "fairy"}), "immune": frozenset({"ghost"})},
    "poison": {"strong": frozenset({"grass", "fairy"}), "resisted": frozenset({"poison", "ground", "rock", "ghost"}), "immune": frozenset({"steel"})},
    "ground": {"strong": frozenset({"fire", "electric", "poison", "rock", "steel"}), "resisted": frozenset({"grass", "bug"}), "immune": frozenset({"flying"})},
    "flying": {"strong": frozenset({"grass", "fighting", "bug"}), "resisted": frozenset({"electric", "rock", "steel"}), "immune": frozenset()},
    "psychic": {"strong": frozenset({"fighting", "poison"}), "resisted": frozenset({"psychic", "steel"}), "immune": frozenset({"dark"})},
    "bug": {"strong": frozenset({"grass", "psychic", "dark"}), "resisted": frozenset({"fire", "fighting", "poison", "flying", "ghost", "steel", "fairy"}), "immune": frozenset()},
    "rock": {"strong": frozenset({"fire", "ice", "flying", "bug"}), "resisted": frozenset({"fighting", "ground", "steel"}), "immune": frozenset()},
    "ghost": {"strong": frozenset({"psychic", "ghost"}), "resisted": frozenset({"dark"}), "immune": frozenset({"normal"})},
    "dragon": {"strong": frozenset({"dragon"}), "resisted": frozenset({"steel"}), "immune": frozenset({"fairy"})},
    "dark": {"strong": frozenset({"psychic", "ghost"}), "resisted": frozenset({"fighting", "dark", "fairy"}), "immune": frozenset()},
    "steel": {"strong": frozenset({"ice", "rock", "fairy"}), "resisted": frozenset({"fire", "water", "electric", "steel"}), "immune": frozenset()},
    "fairy": {"strong": frozenset({"fighting", "dragon", "dark"}), "resisted": frozenset({"fire", "poison", "steel"}), "immune": frozenset()},
}

TYPES = frozenset(ATTACK_CHART)


def type_multiplier(attacking_type: str, defending_types: Iterable[str]) -> float:
    """Compute 0, 0.25, 0.5, 1, 2, or 4 for one move's typing.

    Does not account for abilities, weather, held items, Terastallization, etc.
    """
    attack = attacking_type.strip().lower()
    if attack not in TYPES:
        raise ValueError(f"Unknown attacking type: {attacking_type}")
    defenders = [t.strip().lower() for t in defending_types]
    if not 1 <= len(defenders) <= 2 or len(set(defenders)) != len(defenders):
        raise ValueError("Provide one or two different defending types")
    if any(t not in TYPES for t in defenders):
        raise ValueError("Unknown defending type")
    match = ATTACK_CHART[attack]
    multiplier = 1.0
    for defender in defenders:
        if defender in match["immune"]:
            return 0.0
        if defender in match["strong"]:
            multiplier *= 2
        elif defender in match["resisted"]:
            multiplier *= 0.5
    return multiplier


def analyze_types(team: list[dict]) -> dict:
    """Summarize defensive type coverage for an explicitly supplied team.

    Team members must have a name and one or two types. Role fields optional.
    """
    if not 1 <= len(team) <= 6:
        raise ValueError("A team must contain between 1 and 6 Pokémon")
    seen = set()
    for member in team:
        if not isinstance(member, dict) or not isinstance(member.get("name"), str):
            raise ValueError("Each team entry needs a name")
        name = member["name"].strip().lower()
        if not name or name in seen:
            raise ValueError("Each Pokémon needs a unique nonempty name")
        seen.add(name)
        if not isinstance(member.get("types"), list):
            raise ValueError("Each Pokémon needs a types list")

    weaknesses = Counter()
    resistances = Counter()
    members = []
    for pokemon in team:
        types = pokemon["types"]
        chart = {t: type_multiplier(t, types) for t in sorted(TYPES)}
        weaknesses.update({attack: 1 for attack, value in chart.items() if value > 1})
        resistances.update({attack: 1 for attack, value in chart.items() if value < 1})
        members.append({
            "name": pokemon["name"], "types": types, "role": pokemon.get("role"),
            "damage_multipliers": chart,
            "weak_to": [t for t, value in chart.items() if value > 1],
            "resists_or_immune": [t for t, value in chart.items() if value < 1],
        })
    return {
        "team_size": len(team),
        "members": members,
        "shared_weaknesses": [
            {"type": t, "count": count}
            for t, count in sorted(weaknesses.items(), key=lambda x: (-x[1], x[0]))
            if count >= 3
        ],
        "weakness_counts": dict(sorted(weaknesses.items())),
        "resistance_or_immunity_counts": dict(sorted(resistances.items())),
        "scope": "Type matchups only; abilities, items, moves, Tera and format legality not evaluated.",
    }
