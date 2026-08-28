"""Contracts for the role-local scientific capability control surface."""

from __future__ import annotations

from pathlib import Path

from scripts import hmasd_control_release


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return " ".join((ROOT / relative).read_text(encoding="utf-8").lower().split())


def test_protocol_keeps_role_local_instruments_outside_v3_transport() -> None:
    protocol = _read("docs/project/WORKFLOW_PROTOCOL.md")

    for required in (
        "role-local instrument request/result v1",
        "不是新的 envelope kind",
        "configs/scientific-capabilities-v1.toml",
        "observed | failed | unavailable",
        "hmasd_instrument_observation_v1.schema.json",
        "docs/research/candidates/<direction_id>/evidence/<evidence_id>.json",
        "temp/directions/<direction_id>/{exp,test}/instruments/<evidence_id>/",
        "validate-evidence --path",
        "sidecar candidate",
        "content_sha256",
        "完全相同的 bytes",
        "不得用 `pass`",
        "manager 是唯一 durable writer",
        "能力不可用",
        "不得安装",
    ):
        assert required in protocol

    assert "普通检索、静态数学验证和分析 probe" in protocol
    assert "result-bearing command" in protocol


def test_root_summary_names_instrument_sidecar_writer_boundary() -> None:
    agents = _read("AGENTS.md")

    assert "instrument evidence sidecar" in agents
    assert "leaf 只返回 typed observation" in agents
    assert "em/cm 校验并写 sidecar" in agents


def test_em_and_cm_select_only_explicit_active_capabilities_and_freeze_effects() -> None:
    for prompt in (".codex/prompts/hmasd-em.md", ".codex/prompts/hmasd-cm.md"):
        text = _read(prompt)
        for required in (
            "classify the evidence question",
            "smallest sufficient active capability",
            "configs/scientific-capabilities-v1.toml",
            "freeze the objective",
            "judgment criteria",
            "effect",
            "explicitly invoke",
            "validate-evidence",
            "report unavailable",
            "do not install",
        ):
            assert required in text

    cm = _read(".codex/prompts/hmasd-cm.md")
    assert "result-bearing command" in cm
    assert "experiment operator" in cm


def test_portfolio_and_clerk_do_not_become_instrument_managers() -> None:
    portfolio = _read(".codex/prompts/hmasd-portfolio.md")
    clerk = _read(".codex/prompts/hmasd-workflow-clerk.md")

    assert "only evidence summaries that can change an investment judgment" in portfolio
    assert "does not invoke capabilities or operate tools" in portfolio
    assert "must not read the capability catalog" in clerk
    assert "must not interpret instrument evidence" in clerk
    assert "must not change routing from a tool observation" in clerk


def test_control_release_includes_contract_but_excludes_evolving_tool_surface() -> None:
    included = {
        ".gitattributes",
        "docs/SCIENTIFIC_CAPABILITY_LAYER_REQUIREMENTS.md",
        "scripts/hmasd_science_capabilities.py",
        "scripts/schemas/hmasd_instrument_evidence_v1.schema.json",
        "scripts/schemas/hmasd_instrument_observation_v1.schema.json",
        "tests/hmasd_science_capabilities_test.py",
        "tests/hmasd_scientific_control_plane_test.py",
        "tests/codex_config_contract_test.py",
        "tests/fixtures/hmasd_science/critical_thinking_field_slot/temp/directions/field_slot_coordination/test/instruments/critical-thinking-field-slot-r01/observation.json",
    }
    excluded = {
        "configs/scientific-capabilities-v1.toml",
        "configs/scientific-capability-sources-v1.json",
        "environments/hmasd-science-tools/manifest.json",
        ".agents/skills/hmasd-scientific-critical-thinking/SKILL.md",
    }

    assert hmasd_control_release.PROTOCOL_EPOCH == 3
    assert all(hmasd_control_release.is_control_path(path) for path in included)
    assert not any(hmasd_control_release.is_control_path(path) for path in excluded)


def test_hash_bound_science_fixture_has_an_lf_checkout_contract() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")

    assert "/tests/fixtures/hmasd_science/** text eol=lf" in attributes


def test_transport_and_state_contracts_do_not_gain_instrument_fields() -> None:
    envelope = _read("scripts/hmasd_session_envelope.py")
    research_schema = _read("scripts/schemas/hmasd_research_state.schema.json")
    engineering_schema = _read("scripts/schemas/hmasd_engineering_state.schema.json")

    for forbidden in ("instrument_request", "instrument_result", "capability_id"):
        assert forbidden not in envelope
        assert forbidden not in research_schema
        assert forbidden not in engineering_schema
