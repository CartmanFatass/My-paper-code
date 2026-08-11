"""Proof-sized contracts for the Explorer Mechanical child boundary.

These checks parse the registered profile and verify that the capability
remains read-only and literal-fact organization only when invoked by Root or
the Explorer.
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


def _normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


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
        "fork_turns=1",
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
    role = _normalized(ROLE)
    skill = _normalized(SKILL)

    for required in (
        "role=explorer_mechanical_operator",
        "callable_agent_type=hmasd-explorer-mechanical",
        "parent=root|independent_research_explorer",
        "assignment_identity=assignment_scoped_native_task",
        "user_contact_authority=none",
        "write_authority=none",
        "git_authority=none",
        "scientific_authority=none",
        "technical_acceptance_authority=none",
        "runtime_authority=none",
        "child_authority=none",
        "cross_owner_contact_authority=none",
        "cross_branch_transport=none",
        "default_fork_turns=1",
        "output_contract=conclusion_first_return_to_invoker",
        "Root or Independent Research Explorer may invoke this leaf",
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
        "fork_turns=1",
        "returns once to its invoker",
        "Root relays the organized facts",
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


def test_explorer_mechanical_assignment_intake_is_native_or_parent_file_backed() -> None:
    """Cover assignment intake by normalized structural fragments."""

    _require_producer_surfaces()
    role = _normalized(ROLE)
    skill = _normalized(SKILL)

    role_structures = (
        (
            "native payload",
            (
                "When no assignment-file locator is supplied",
                "native assignment payload is authoritative",
                "do not search for, reconstruct or infer an assignment file",
            ),
        ),
        (
            "parent file-backed assignment",
            (
                "parent supplies its exact path, hash and authority",
                "hash as a locator/integrity fact only",
                "never as admission or acceptance",
            ),
        ),
        (
            "closed missing meaning",
            (
                "required task meaning is absent",
                "fail closed to the invoker",
                "not use `rg` or other discovery",
            ),
        ),
        (
            "bounded rg",
            ("use `rg` only for explicitly named Markdown or JSON fields and evidence locators",),
        ),
        (
            "immediate references",
            (
                "mandatory Role and Explorer Mechanical Skill references",
                "distinct from assignment-file reconstruction",
            ),
        ),
    )
    for label, fragments in role_structures:
        assert all(fragment in role for fragment in fragments), f"Role structure missing: {label}"

    skill_structures = (
        (
            "native payload",
            (
                "When no assignment-file locator is supplied",
                "that payload is the exact assignment",
                "must not search for, reconstruct or infer an assignment file",
            ),
        ),
        (
            "invoker file-backed assignment",
            (
                "invoker must supply its exact path, hash and authority",
                "supplied hash is a locator/integrity fact",
                "not an admission or acceptance decision",
            ),
        ),
        (
            "closed missing meaning",
            (
                "required assignment meaning is missing",
                "fail closed to the invoker",
                "instead of using `rg` or discovery",
            ),
        ),
        (
            "bounded rg",
            ("`rg` only for explicitly named Markdown or JSON fields and evidence locators",),
        ),
        (
            "immediate references",
            (
                "Role and this Skill are mandatory immediate references",
                "distinct from assignment-file reconstruction",
            ),
        ),
    )
    for label, fragments in skill_structures:
        assert all(fragment in skill for fragment in fragments), f"Skill structure missing: {label}"

    # Named evidence inputs remain valid; assignment-file discovery does not.
    assert "assignment-named local file" not in role
    assert "assignment-named local file" not in skill


if __name__ == "__main__":
    test_explorer_mechanical_profile_is_registered_once_with_frozen_route()
    test_explorer_mechanical_role_and_skill_keep_literal_fact_boundary()
    test_explorer_mechanical_assignment_intake_is_native_or_parent_file_backed()
    print("HMASD_EXPLORER_MECHANICAL_CONTRACT_OK")
