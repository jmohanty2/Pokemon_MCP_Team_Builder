import pytest

from pokemon_mcp.team_builder import CANDIDATES, build_example_team


def test_build_team_is_unique_and_repeatable():
    result = build_example_team("greninja")
    assert len(result["team"]) == 6
    assert result["team"][0]["name"] == "greninja"
    assert len({member["name"] for member in result["team"]}) == 6
    assert result == build_example_team("greninja")
    assert len({member["role"] for member in result["team"]}) == 6


def test_all_core_candidates_supported():
    for candidate in CANDIDATES:
        result = build_example_team(candidate.name, "offense")
        assert result["team"][0]["name"] == candidate.name
        assert len(result["team"]) == 6


def test_invalid_core_and_style():
    with pytest.raises(ValueError):
        build_example_team("not-a-pokemon")
    with pytest.raises(ValueError):
        build_example_team("greninja", "ultra")


@pytest.mark.parametrize("style", ["balanced", "offense", "defense"])
def test_every_core_covers_six_roles_for_each_style(style):
    for candidate in CANDIDATES:
        result = build_example_team(candidate.name, style)
        assert len({member["name"] for member in result["team"]}) == 6
        assert len({member["role"] for member in result["team"]}) == 6
        assert result["analysis"]["team_size"] == 6
