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


if __name__ == "__main__":
    test_verifier_registration_and_model_routing()
    print("HMASD_MODEL_ROUTING_OK")
