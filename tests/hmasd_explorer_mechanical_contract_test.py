"""Proof-sized contracts for the Explorer Mechanical child boundary.

These checks parse the registered profile and verify that the capability
remains read-only, literal-fact organization only, and owned by the Explorer
alone.
"""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib


REPO = Path(__file__).resolve().parents[1]
PROFILE = REPO / ".codex" / "agents" / "hmasd-explorer-mechanical.toml"
ROLE = REPO / ".agents" / "roles" / "EXPLORER_MECHANICAL_OPERATOR.md"
SKILL = REPO / ".agents" / "skills" / "hmasd-explorer-mechanical" / "SKILL.md"
CONFIG = REPO / ".codex" / "config.toml"


def _require_producer_surfaces() -> None:
    missing = [str(path.relative_to(REPO)) for path in (PROFILE, ROLE, SKILL) if not path.is_file()]
    assert not missing, "Explorer Mechanical producer surfaces are missing: " + ", ".join(missing)


def _registered_profiles() -> list[tuple[Path, dict[str, object]]]:
    profiles: list[tuple[Path, dict[str, object]]] = []
    for path in sorted((REPO / ".codex" / "agents").glob("*.toml")):
        with path.open("rb") as stream:
            profiles.append((path, tomllib.load(stream)))
    return profiles


def test_explorer_mechanical_profile_is_registered_once_with_frozen_route() -> None:
    _require_producer_surfaces()
    registered = [
        (path, profile)
        for path, profile in _registered_profiles()
        if profile.get("name") == "hmasd-explorer-mechanical"
    ]
    assert len(registered) == 1
    profile_path, profile = registered[0]
    assert profile_path == PROFILE
    assert profile["model"] == "gpt-5.6-luna"
    assert profile["model_reasoning_effort"] == "low"
    assert profile["sandbox_mode"] == "read-only"
    assert profile["approval_policy"] == "never"

    instructions = " ".join(str(profile.get("developer_instructions", "")).split())
    for required in (
        ".agents/roles/EXPLORER_MECHANICAL_OPERATOR.md",
        ".agents/skills/hmasd-explorer-mechanical/SKILL.md",
        "fork_turns=none",
        "self-contained natural-language task model",
        "one conclusion-first native result",
        "Do not write files",
        "mutate Git",
        "run runtime or experiments",
        "interpret science",
        "spawn children",
    ):
        assert required in instructions

    config = CONFIG.read_text(encoding="utf-8")
    assert config.count('config_file = "./agents/hmasd-explorer-mechanical.toml"') == 1


def test_explorer_mechanical_role_and_skill_keep_literal_fact_boundary() -> None:
    _require_producer_surfaces()
    role = " ".join(ROLE.read_text(encoding="utf-8").split())
    skill = " ".join(SKILL.read_text(encoding="utf-8").split())

    for required in (
        "role=explorer_mechanical_operator",
        "callable_agent_type=hmasd-explorer-mechanical",
        "parent=independent_research_explorer",
        "write_authority=none",
        "git_authority=none",
        "scientific_authority=none",
        "technical_acceptance_authority=none",
        "runtime_authority=none",
        "child_authority=none",
        "cross_task_contact_authority=none",
        "state_scan_authority=none",
        "self-contained natural-language task model",
        "locate, preserve, compare, group and compactly present",
        "must not fill unknown, empty or unspecified values",
        "literal existence or inaccessibility",
        "does not judge locator validity",
        "schema, readability, readiness, receipts, activity counts, retry history",
        "Return one native terminal result only",
        "There is no mandatory output file, queue, monitor",
    ):
        assert required in role

    for required in (
        "Dispatch the registered `hmasd-explorer-mechanical` child",
        "fork_turns=none",
        "Prefer this child when heterogeneous record handling",
        "lowest-cost read-only observation first",
        "cannot decide locator validity, completeness, public accessibility or technical sufficiency",
        "If the first observation exposes one missing or disputed named fact",
        "one conclusion-first native result",
        "not a cheap scientific consultant, validator, dispatcher, writer",
    ):
        assert required in skill

    # Registration is a new Explorer-only lane, not a replacement for CPM or
    # any of the four Sol scientific consultants.
    names = {profile.get("name") for _, profile in _registered_profiles()}
    assert "hmasd-explorer-mechanical" in names
    assert "hmasd-cpm-mechanical" in names
    for scientific_name in (
        "hmasd-research-scout",
        "hmasd-research-innovator",
        "hmasd-research-critic",
        "hmasd-research-principles-analyst",
    ):
        assert scientific_name in names


if __name__ == "__main__":
    test_explorer_mechanical_profile_is_registered_once_with_frozen_route()
    test_explorer_mechanical_role_and_skill_keep_literal_fact_boundary()
    print("HMASD_EXPLORER_MECHANICAL_CONTRACT_OK")
