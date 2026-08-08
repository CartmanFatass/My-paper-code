"""Focused contracts for the remaining native child Roles and Profiles."""

from __future__ import annotations

import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]

CHILDREN = (
    (
        "code_scout",
        ROOT / ".agents/roles/CODE_SCOUT.md",
        ROOT / ".codex/agents/hmasd-code-scout.toml",
        "gpt-5.6-luna",
        "medium",
        "read-only",
        None,
        "reopen one named immediate interface once",
    ),
    (
        "reviewer",
        ROOT / ".agents/roles/REVIEWER.md",
        ROOT / ".codex/agents/hmasd-reviewer.toml",
        "gpt-5.6-sol",
        "xhigh",
        "read-only",
        None,
        "reread one indispensable changed artifact or immediate interface once",
    ),
    (
        "research_scout",
        ROOT / ".agents/roles/RESEARCH_SCOUT.md",
        ROOT / ".codex/agents/hmasd-research-scout.toml",
        "gpt-5.6-sol",
        "high",
        "read-only",
        "SOURCE_RESULT_PACKET",
        "one JSON or PDF fidelity recheck at that disputed locator",
    ),
    (
        "research_principles_analyst",
        ROOT / ".agents/roles/RESEARCH_PRINCIPLES_ANALYST.md",
        ROOT / ".codex/agents/hmasd-research-principles-analyst.toml",
        "gpt-5.6-sol",
        "max",
        "read-only",
        "RL_PRINCIPLE_ANALYSIS_PACKET",
        "reread one supplied candidate or source fact at the disputed information, credit or temporal boundary",
    ),
    (
        "research_critic",
        ROOT / ".agents/roles/RESEARCH_CRITIC.md",
        ROOT / ".codex/agents/hmasd-research-critic.toml",
        "gpt-5.6-sol",
        "max",
        "read-only",
        "CRITIC_ASSESSMENT_PACKET",
        "recheck one named source or principles packet at that disputed claim boundary",
    ),
    (
        "research_innovator",
        ROOT / ".agents/roles/RESEARCH_INNOVATOR.md",
        ROOT / ".codex/agents/hmasd-research-innovator.toml",
        "gpt-5.6-sol",
        "max",
        "read-only",
        "ALGORITHM_INSPIRATION_PACKET",
        "reread one frozen input or named parent packet once at the disputed assumption",
    ),
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return " ".join(text.split()).lower()


def _bare_result(fragment: str) -> bool:
    return bool(
        re.match(
            r"^\s*(?:`?[A-Z][A-Z_]+_PACKET`?|COMPLETE)(?:\b|\s|$)",
            fragment,
        )
    )


def test_each_role_is_a_semantic_task_model_with_conclusion_first_return() -> None:
    common = (
        "self-contained natural-language task model",
        "factual anchors after meaning",
        "never define task meaning or completion",
        "not a schema or admission gate",
        "concise natural-language conclusion",
        "direct consequence",
        "residual uncertainty",
        "never substitutes for the conclusion",
        "label, status or field list alone is not a complete result",
    )
    for name, role_path, _profile_path, _model, _effort, _sandbox, packet, _recovery in CHILDREN:
        role = _normalized(_text(role_path))
        for required in common:
            assert required in role, f"{name} Role lacks {required!r}"
        assert "owned" in role and "outcome" in role
        assert "factual" in role and "tail" in role
        assert any(
            phrase in role
            for phrase in (
                "do not loop",
                "do not start a second",
                "do not repeat the recheck",
                "do not reread a packet set",
                "do not broaden the evidence set",
                "do not broaden the roster",
            )
        )
        assert any(
            phrase in role
            for phrase in (
                "if ambiguity remains",
                "if the conflict remains",
                "if fidelity remains",
                "if the fact remains",
                "if the issue remains",
            )
        )
        if packet is not None:
            marker = packet.lower()
            assert marker in role
            assert "conclusion-first result then appends" in role
        else:
            assert "evidence map as the factual tail" in role or "evidence tail" in role


def test_recovery_observation_is_one_tailored_non_looping_read() -> None:
    for name, role_path, _profile_path, _model, _effort, _sandbox, _packet, recovery in CHILDREN:
        role = _normalized(_text(role_path))
        assert recovery.lower() in role, f"{name} lacks its tailored recovery"
        assert "one bounded recovery" in role
        assert "if" in role and "remains" in role
        assert "do not" in role
        assert not any(
            anchor in role
            for anchor in ("workflow_assignment_id", "owned_paths", "wdm_session_workspace")
        )


def test_bare_packet_fixture_cannot_stand_in_for_conclusion() -> None:
    assert _bare_result("SOURCE_RESULT_PACKET status=COMPLETE")
    assert _bare_result("COMPLETE")
    assert not _bare_result(
        "The source-evidence outcome is complete because the locator check passed; residual uncertainty is none."
    )


def test_profiles_keep_exact_settings_and_thin_role_pointer() -> None:
    for name, role_path, profile_path, model, effort, sandbox, _packet, _recovery in CHILDREN:
        with profile_path.open("rb") as stream:
            profile = tomllib.load(stream)
        assert profile["name"] == f"hmasd-{name.replace('_', '-')}", name
        assert profile["model"] == model
        assert profile["model_reasoning_effort"] == effort
        assert profile["sandbox_mode"] == sandbox

        instructions = _normalized(profile["developer_instructions"])
        role_pointer = str(role_path.relative_to(ROOT)).replace("\\", "/").lower()
        for required in (
            "fork_turns=none",
            "forked context is background only",
            "self-contained natural-language task model",
            "exact assignment",
            role_pointer,
            "role charter owns",
            "thin",
            "do not duplicate",
        ):
            assert required in instructions, f"{profile_path} lacks {required!r}"

        # Scientific/reviewer procedure belongs only in the Role charter.
        for forbidden in (
            "source_result_packet",
            "algorithm_inspiration_packet",
            "rl_principle_analysis_packet",
            "critic_assessment_packet",
            "reopen one",
            "reread one",
            "recheck one",
            "return exactly one",
            "metadata v2",
            "structured json",
            "pdf verification",
        ):
            assert forbidden not in instructions, f"{profile_path} duplicates {forbidden!r}"
