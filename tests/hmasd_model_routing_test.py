"""Structural checks for the registered execution-readiness verifier route."""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VERIFIER_PROFILE = REPOSITORY_ROOT / ".codex" / "agents" / "hmasd-verifier.toml"
VERIFIER_ROLE = REPOSITORY_ROOT / ".agents" / "roles" / "VERIFIER.md"
MECHANICAL_PROFILE = REPOSITORY_ROOT / ".codex" / "agents" / "hmasd-cpm-mechanical.toml"
MECHANICAL_ROLE = REPOSITORY_ROOT / ".agents" / "roles" / "CPM_MECHANICAL_OPERATOR.md"
EXPLORER_MECHANICAL_PROFILE = (
    REPOSITORY_ROOT / ".codex" / "agents" / "hmasd-explorer-mechanical.toml"
)
EXPLORER_MECHANICAL_ROLE = (
    REPOSITORY_ROOT / ".agents" / "roles" / "EXPLORER_MECHANICAL_OPERATOR.md"
)
IMPLEMENTER_PROFILES = {
    "hmasd-implementer": (
        REPOSITORY_ROOT / ".codex" / "agents" / "hmasd-implementer.toml",
        "gpt-5.6-sol",
        "high",
    ),
    "hmasd-implementer-terra": (
        REPOSITORY_ROOT / ".codex" / "agents" / "hmasd-implementer-terra.toml",
        "gpt-5.6-terra",
        "high",
    ),
}
IMPLEMENTER_ROLE = REPOSITORY_ROOT / ".agents" / "roles" / "IMPLEMENTER.md"


def test_verifier_registration_and_model_routing() -> None:
    profiles = []
    for profile_path in sorted((REPOSITORY_ROOT / ".codex" / "agents").glob("*.toml")):
        with profile_path.open("rb") as stream:
            profiles.append((profile_path, tomllib.load(stream)))

    registered = [
        (profile_path, profile)
        for profile_path, profile in profiles
        if profile.get("name") == "hmasd-verifier"
    ]
    assert len(registered) == 1, "verifier must have exactly one registered profile"

    profile_path, profile = registered[0]
    assert profile_path == VERIFIER_PROFILE
    assert profile["model"] == "gpt-5.6-luna"
    assert profile["model_reasoning_effort"] == "high"
    instructions = profile.get("developer_instructions", "")
    assert ".agents/roles/VERIFIER.md" in instructions

    assert VERIFIER_ROLE.is_file()
    role_text = VERIFIER_ROLE.read_text(encoding="utf-8")
    assert "role=verifier" in role_text


def test_cpm_mechanical_registration_and_model_routing() -> None:
    profiles = []
    for profile_path in sorted((REPOSITORY_ROOT / ".codex" / "agents").glob("*.toml")):
        with profile_path.open("rb") as stream:
            profiles.append((profile_path, tomllib.load(stream)))

    registered = [
        (profile_path, profile)
        for profile_path, profile in profiles
        if profile.get("name") == "hmasd-cpm-mechanical"
    ]
    assert len(registered) == 1, "CPM mechanical child must have exactly one registered profile"

    profile_path, profile = registered[0]
    assert profile_path == MECHANICAL_PROFILE
    assert profile["model"] == "gpt-5.6-luna"
    assert profile["model_reasoning_effort"] == "low"
    instructions = profile.get("developer_instructions", "")
    assert "CPM_MECHANICAL_TASK_ASSIGNMENT" in instructions
    assert "fork_turns=none" in instructions
    assert MECHANICAL_ROLE.is_file()
    role_text = MECHANICAL_ROLE.read_text(encoding="utf-8")
    assert "role=cpm_mechanical_operator" in role_text


def test_explorer_mechanical_registration_and_model_routing() -> None:
    assert EXPLORER_MECHANICAL_PROFILE.is_file()

    profiles = []
    for profile_path in sorted((REPOSITORY_ROOT / ".codex" / "agents").glob("*.toml")):
        with profile_path.open("rb") as stream:
            profiles.append((profile_path, tomllib.load(stream)))

    registered = [
        (profile_path, profile)
        for profile_path, profile in profiles
        if profile.get("name") == "hmasd-explorer-mechanical"
    ]
    assert len(registered) == 1, "Explorer mechanical child must have exactly one registered profile"
    profile_path, profile = registered[0]
    assert profile_path == EXPLORER_MECHANICAL_PROFILE
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
    ):
        assert required in instructions

    assert EXPLORER_MECHANICAL_ROLE.is_file()
    role_text = EXPLORER_MECHANICAL_ROLE.read_text(encoding="utf-8")
    for required in (
        "role=explorer_mechanical_operator",
        "callable_agent_type=hmasd-explorer-mechanical",
        "parent=independent_research_explorer",
        "write_authority=none",
        "scientific_authority=none",
        "technical_acceptance_authority=none",
        "runtime_authority=none",
    ):
        assert required in role_text


def test_implementer_registration_and_model_routing() -> None:
    profiles = []
    for profile_path in sorted((REPOSITORY_ROOT / ".codex" / "agents").glob("*.toml")):
        with profile_path.open("rb") as stream:
            profiles.append((profile_path, tomllib.load(stream)))

    for name, (expected_path, expected_model, expected_effort) in IMPLEMENTER_PROFILES.items():
        registered = [
            (profile_path, profile)
            for profile_path, profile in profiles
            if profile.get("name") == name
        ]
        assert len(registered) == 1, f"{name} must have exactly one registered profile"
        profile_path, profile = registered[0]
        assert profile_path == expected_path
        assert profile["model"] == expected_model
        assert profile["model_reasoning_effort"] == expected_effort
        instructions = profile.get("developer_instructions", "")
        assert ".agents/roles/IMPLEMENTER.md" in instructions
        assert "exact assignment" in instructions
        assert "registered child of Code Project Manager" in instructions
        assert "Do not mutate Git" in instructions
        for duplicated in (
            "purpose, observed behavior or failure",
            "necessary consequential scope",
            "Every result must begin with a concise natural-language conclusion",
            "scripts/hmasd_workspace_ticket.py",
            "absolute `apply_patch` targets",
            "core.longpaths=true",
            "Return status, changed files, checks",
        ):
            assert duplicated not in instructions

    role_text = IMPLEMENTER_ROLE.read_text(encoding="utf-8")
    role_text_normalized = " ".join(role_text.split())
    for required in (
        "Every result must begin with a concise natural-language conclusion",
        "what outcome was achieved or remains unresolved",
        "direct consumer or cross-module consequence checked",
        "residual uncertainty",
        "A mechanical status or changed-path list alone is not a complete result",
        "necessary consequential scope",
        "model strength adds no authority and never substitutes for a complete assignment",
        "rigid schema or admission gate",
    ):
        assert required in role_text_normalized

    terra_text = IMPLEMENTER_PROFILES["hmasd-implementer-terra"][0].read_text(encoding="utf-8")
    terra_text_normalized = " ".join(terra_text.split())
    assert "material or outcome-changing" in terra_text_normalized
    assert "reversible internal organization" in terra_text_normalized
    assert "You do not choose scientific semantics, architecture direction" not in terra_text
    sol_text = IMPLEMENTER_PROFILES["hmasd-implementer"][0].read_text(encoding="utf-8")
    assert "protected Sol route" in sol_text
    assert "assignment-specified semantics" in sol_text


if __name__ == "__main__":
    test_verifier_registration_and_model_routing()
    test_cpm_mechanical_registration_and_model_routing()
    test_explorer_mechanical_registration_and_model_routing()
    test_implementer_registration_and_model_routing()
    print("HMASD_MODEL_ROUTING_OK")
