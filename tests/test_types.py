import pytest

from pokemon_mcp.type_chart import analyze_types, type_multiplier


def test_dual_type_and_immunity():
    assert type_multiplier("electric", ["water", "flying"]) == 4.0
    assert type_multiplier("ground", ["flying", "steel"]) == 0.0
    assert type_multiplier("fire", ["water", "dragon"]) == 0.25


def test_validation():
    with pytest.raises(ValueError):
        type_multiplier("unknown", ["water"])
    with pytest.raises(ValueError):
        type_multiplier("fire", ["fire", "fire"])


def test_shared_weaknesses_and_duplicates():
    team = [
        {"name": "Charizard", "types": ["fire", "flying"]},
        {"name": "Corviknight", "types": ["flying", "steel"]},
        {"name": "Gyarados", "types": ["water", "flying"]},
    ]
    result = analyze_types(team)
    assert {row["type"] for row in result["shared_weaknesses"]} == {"electric"}
    with pytest.raises(ValueError):
        analyze_types([team[0], team[0]])


@pytest.mark.parametrize("attack,defenders,expected", [
    ("rock", ["fire", "flying"], 4),
    ("ice", ["dragon", "ground"], 4),
    ("electric", ["ground", "flying"], 0),
    ("dragon", ["fairy"], 0),
    ("poison", ["steel", "fairy"], 0),
    ("fire", ["water", "grass"], 1),
    ("fighting", ["bug", "poison"], 0.25),
])
def test_known_matchups(attack, defenders, expected):
    assert type_multiplier(attack, defenders) == expected


def test_analysis_preserves_fourfold_weakness_and_immunity():
    result = analyze_types([{"name": "Charizard", "types": ["fire", "flying"]}])
    multipliers = result["members"][0]["damage_multipliers"]
    assert len(multipliers) == 18
    assert multipliers["rock"] == 4
    assert multipliers["ground"] == 0
