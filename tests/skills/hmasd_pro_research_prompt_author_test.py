from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agents" / "skills" / "hmasd-pro-research-prompt-author" / "scripts" / "render_packet.py"
SKILL = ROOT / ".agents" / "skills" / "hmasd-pro-research-prompt-author" / "SKILL.md"


def _renderer():
    spec = importlib.util.spec_from_file_location("hmasd_prompt_author_renderer", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _request() -> dict[str, object]:
    return {
        "caller_role": "em",
        "workflow_node": "em_convergence",
        "request_id": "req-companion-01",
        "source_thread_id": "11111111-1111-1111-1111-111111111111",
        "direction_id": "demo_direction",
        "repository": "C:/repo",
        "repository_url": "https://github.com/example/repo",
        "commit_or_ref": "0123456789abcdef0123456789abcdef01234567",
        "scientific_question": "Does the bounded intervention change the stated endpoint?",
        "deliverable": "A conclusion-first evidence assessment.",
        "claim_ceiling": "Descriptive finite-panel claim only.",
        "reference_files": [
            {
                "path": "docs/research/candidates/demo_direction/DIRECTION.md",
                "purpose": "direction definition",
                "provenance": "registered direction authority",
            }
        ],
    }


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    direction = tmp_path / "docs" / "research" / "candidates" / "demo_direction"
    portfolio = tmp_path / "docs" / "research" / "portfolio"
    direction.mkdir(parents=True)
    portfolio.mkdir(parents=True)
    (direction / "DIRECTION.md").write_text("# Demo\n", encoding="utf-8")
    second = tmp_path / "docs" / "research" / "candidates" / "second_direction"
    second.mkdir(parents=True)
    (second / "DIRECTION.md").write_text("# Second\n", encoding="utf-8")
    (portfolio / "PORTFOLIO.md").write_text(
        "| demo_direction | ACTIVE |\n| second_direction | PARKED |\n",
        encoding="utf-8",
    )
    return tmp_path


def _render(renderer, request: dict[str, object], project_root: Path, out_dir: Path) -> dict:
    packet = renderer.validate(request, project_root)
    renderer.render(packet, out_dir)
    return json.loads((out_dir / "HANDOFF.json").read_text(encoding="utf-8"))


def test_omitted_companion_prompt_uses_the_fixed_default(project_root: Path, tmp_path: Path) -> None:
    renderer = _renderer()
    packet = renderer.validate(_request(), project_root)

    assert packet["companion_prompt"] == (
        "Execute the attached PROMPT_BODY.md exactly. "
        "It contains the complete read-only evidence manifest. "
        "Return this node's final decision or the exact blocker."
    )
    out_dir = tmp_path / "default"
    handoff = _render(renderer, _request(), project_root, out_dir)
    assert handoff["transport_request"]["companion_prompt"] == packet["companion_prompt"]
    assert "companion_prompt" not in handoff
    assert packet["companion_prompt"].encode() not in (out_dir / "PROMPT_BODY.md").read_bytes()
    assert not (out_dir / "REFERENCE_FILES.md").exists()
    assert handoff["transport_request"]["prompt_path"] == "PROMPT_BODY.md"
    assert "reference_paths" not in handoff["transport_request"]
    assert handoff["transport_request"]["source_mode"] == "single_body_attachment"
    body = (out_dir / "PROMPT_BODY.md").read_text(encoding="utf-8")
    assert "GITHUB_EVIDENCE_MANIFEST" in body
    assert "docs/research/candidates/demo_direction/DIRECTION.md" in body
    assert "purpose: direction definition" in body


def test_default_companion_is_provider_facing_and_excludes_author_workflow_terms(
    project_root: Path
) -> None:
    renderer = _renderer()
    companion = renderer.validate(_request(), project_root)["companion_prompt"]

    assert "PROMPT_BODY.md" in companion
    assert "REFERENCE_FILES.md" not in companion
    assert "final decision" in companion
    assert "exact blocker" in companion
    assert not any(
        term in companion.lower()
        for term in (
            "author",
            "send_message_to_thread",
            "codex",
            "transport",
            "browser",
            "dispatch",
            "conversation-binding",
            "routing",
            "cleanup",
            "workflow",
        )
    )


def test_provider_context_reset_is_routing_only_and_default_reuse_is_unchanged(
    project_root: Path, tmp_path: Path
) -> None:
    renderer = _renderer()
    evidence = {
        "previous_request_id": "req-companion-00",
        "decision_outcome": "DECISION_NOT_FORMED",
        "repository_paths_read": 0,
        "provider_context_contamination_acknowledged": True,
        "acknowledged_prompt_defect": "obsolete provider-visible author dispatch instruction",
    }
    default_dir = tmp_path / "default"
    reset_dir = tmp_path / "reset"
    default_handoff = _render(renderer, _request(), project_root, default_dir)
    reset_handoff = _render(
        renderer,
        {
            **_request(),
            "reset_invalid_provider_context": True,
            "provider_context_reset_evidence": evidence,
        },
        project_root,
        reset_dir,
    )

    assert default_handoff["reset_invalid_provider_context"] is False
    assert default_handoff["transport_request"]["reset_invalid_provider_context"] is False
    assert default_handoff["conversation_reuse_required"] is True
    assert reset_handoff["reset_invalid_provider_context"] is True
    assert reset_handoff["transport_request"]["reset_invalid_provider_context"] is True
    assert reset_handoff["provider_context_reset_evidence"] == evidence
    assert reset_handoff["transport_request"]["provider_context_reset_evidence"] == evidence
    assert (default_dir / "PROMPT_BODY.md").read_bytes() == (reset_dir / "PROMPT_BODY.md").read_bytes()
    companion = reset_handoff["transport_request"]["companion_prompt"]
    for text in (
        (reset_dir / "PROMPT_BODY.md").read_text(encoding="utf-8"),
        companion,
    ):
        assert "reset_invalid_provider_context" not in text
        assert "provider_context_reset_evidence" not in text


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"reset_invalid_provider_context": "true"}, "reset_invalid_provider_context"),
        ({"reset_invalid_provider_context": True}, "provider_context_reset_evidence"),
        (
            {
                "reset_invalid_provider_context": True,
                "provider_context_reset_evidence": {
                    "previous_request_id": "prior",
                    "decision_outcome": "DECISION_FORMED",
                    "repository_paths_read": 0,
                    "provider_context_contamination_acknowledged": True,
                    "acknowledged_prompt_defect": "bad companion",
                },
            },
            "provider_context_reset_evidence.decision_outcome",
        ),
        (
            {
                "reset_invalid_provider_context": True,
                "provider_context_reset_evidence": {
                    "previous_request_id": "prior",
                    "decision_outcome": "BLOCKED",
                    "repository_paths_read": 1,
                    "provider_context_contamination_acknowledged": True,
                    "acknowledged_prompt_defect": "bad companion",
                },
            },
            "provider_context_reset_evidence.repository_paths_read",
        ),
    ],
)
def test_invalid_provider_context_reset_metadata_is_rejected(
    project_root: Path, changes: dict[str, object], field: str
) -> None:
    renderer = _renderer()

    with pytest.raises(renderer.PacketInputError) as exc_info:
        renderer.validate({**_request(), **changes}, project_root)

    assert exc_info.value.field == field


def test_reset_caller_cannot_supply_a_replacement_conversation_id(project_root: Path) -> None:
    renderer = _renderer()
    with pytest.raises(renderer.PacketInputError, match="conversation_id"):
        renderer.validate(
            {
                **_request(),
                "conversation_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "reset_invalid_provider_context": True,
                "provider_context_reset_evidence": {
                    "previous_request_id": "prior",
                    "decision_outcome": "BLOCKED",
                    "repository_paths_read": 0,
                    "provider_context_contamination_acknowledged": True,
                    "acknowledged_prompt_defect": "bad companion",
                },
            },
            project_root,
        )


def test_non_empty_companion_prompt_is_preserved_byte_for_byte(project_root: Path) -> None:
    renderer = _renderer()
    override = "  Execute this exact companion.\r\nKeep the newline and trailing spaces.  \n"

    packet = renderer.validate({**_request(), "companion_prompt": override}, project_root)

    assert packet["companion_prompt"] == override


@pytest.mark.parametrize("value", ["", "   ", "\r\n\t"])
def test_empty_or_whitespace_only_companion_prompt_is_rejected(
    project_root: Path, value: str
) -> None:
    renderer = _renderer()

    with pytest.raises(ValueError, match="companion_prompt"):
        renderer.validate({**_request(), "companion_prompt": value}, project_root)


def test_companion_override_changes_only_handoff_companion_content(
    project_root: Path, tmp_path: Path
) -> None:
    renderer = _renderer()
    packet_dir = tmp_path / "packet"
    override = "Use this caller-supplied companion verbatim.\n"

    default_handoff = _render(renderer, _request(), project_root, packet_dir)
    default_body = (packet_dir / "PROMPT_BODY.md").read_bytes()
    override_handoff = _render(
        renderer, {**_request(), "companion_prompt": override}, project_root, packet_dir
    )

    override_body = (packet_dir / "PROMPT_BODY.md").read_bytes()
    assert default_body == override_body
    assert default_handoff["transport_request"]["companion_prompt"].encode() not in default_body
    assert override.encode() not in override_body
    assert default_handoff["transport_request"]["companion_prompt"] != override_handoff["transport_request"]["companion_prompt"]
    assert override_handoff["transport_request"]["companion_prompt"] == override
    default_without_companion = dict(default_handoff)
    override_without_companion = dict(override_handoff)
    default_without_companion["transport_request"] = dict(default_handoff["transport_request"])
    override_without_companion["transport_request"] = dict(override_handoff["transport_request"])
    default_without_companion["transport_request"].pop("companion_prompt")
    override_without_companion["transport_request"].pop("companion_prompt")
    assert default_without_companion == override_without_companion


def test_author_remains_authoring_only_and_operator_gets_companion_contract(
    project_root: Path, tmp_path: Path
) -> None:
    renderer = _renderer()
    handoff = _render(renderer, _request(), project_root, tmp_path / "packet")
    skill_text = SKILL.read_text(encoding="utf-8")

    assert handoff["pro_send_from_caller"] is False
    assert "companion_prompt" in handoff["transport_request"]
    assert "supply the companion_prompt verbatim" in skill_text
    assert "provider-visible scientific UI text only" in skill_text
    assert "Those instructions belong only in the author-to-Transport `HANDOFF.json`" in skill_text
    assert "all\nrouting and execution workflow remains in `HANDOFF.json`" in skill_text
    assert "sole provider attachment" in skill_text
    assert "must not declare or upload a reference attachment" in skill_text


def test_handoff_creates_one_transport_operator_on_demand(
    project_root: Path, tmp_path: Path
) -> None:
    renderer = _renderer()
    out_dir = tmp_path / "packet"
    handoff = _render(renderer, _request(), project_root, out_dir)
    handoff_path = str((out_dir / "HANDOFF.json").resolve())

    assert handoff["packet_version"] == 2
    assert handoff["dispatch_mode"] == "CREATE_ON_DEMAND"
    assert handoff["dispatch_state"] == "PENDING_CREATE"
    assert handoff["dispatch_required"] is True
    assert handoff["dispatch_once"] is True
    assert handoff["operator_thread_id"] is None
    assert handoff["operator_thread_url"] is None
    assert handoff["return_receipt_thread_id"] == handoff["source_thread_id"]
    assert "Wait for the creator's execution message" in handoff["operator_bootstrap_prompt"]
    for legacy_field in (
        "transport_operator_thread",
        "transport_operator_thread_id",
        "dispatch_target_thread_id",
        "dispatch_target_thread_url",
    ):
        assert legacy_field not in handoff
    assert handoff["pro_send_from_caller"] is False
    assert handoff["workflow_node"] == "em_convergence"
    assert handoff["direction_ids"] == ["demo_direction"]
    assert handoff["conversation_binding_key"] == "em:demo_direction:convergence"
    assert handoff["conversation_reuse_required"] is True
    assert handoff["decision_authority"] == "pro_final"
    assert handoff["dispatch_handoff_path"] == handoff_path
    assert handoff["dispatch_prompt"] == f"Execute the handoff packet at {handoff_path} exactly once."
    assert "Call create_thread exactly once" in handoff["dispatch_instruction"]
    assert "dynamic threadId" in handoff["dispatch_instruction"]
    assert f"prompt=Execute the handoff packet at {handoff_path} exactly once." in handoff["dispatch_instruction"]


def test_each_handoff_records_its_own_operator_without_changing_provider_binding(
    project_root: Path, tmp_path: Path
) -> None:
    renderer = _renderer()
    first_dir = tmp_path / "operator-a"
    second_dir = tmp_path / "operator-b"
    first = _render(renderer, _request(), project_root, first_dir)
    second = _render(
        renderer,
        {**_request(), "request_id": "req-companion-02"},
        project_root,
        second_dir,
    )
    first_body = (first_dir / "PROMPT_BODY.md").read_bytes()
    second_body = (second_dir / "PROMPT_BODY.md").read_bytes()

    first = renderer.record_operator_thread_id(
        first_dir / "HANDOFF.json",
        "22222222-2222-2222-2222-222222222222",
    )
    second = renderer.record_operator_thread_id(
        second_dir / "HANDOFF.json",
        "33333333-3333-3333-3333-333333333333",
    )

    assert first["operator_thread_id"] != second["operator_thread_id"]
    assert first["conversation_binding_key"] == second["conversation_binding_key"]
    assert first["transport_request"]["operator_thread_id"] == first["operator_thread_id"]
    assert second["transport_request"]["operator_thread_id"] == second["operator_thread_id"]
    assert first["return_receipt_thread_id"] == first["source_thread_id"]
    assert second["return_receipt_thread_id"] == second["source_thread_id"]
    assert (first_dir / "PROMPT_BODY.md").read_bytes() == first_body
    assert (second_dir / "PROMPT_BODY.md").read_bytes() == second_body

    renderer.record_operator_thread_id(
        first_dir / "HANDOFF.json",
        first["operator_thread_id"],
    )
    with pytest.raises(renderer.PacketInputError, match="different operator_thread_id"):
        renderer.record_operator_thread_id(
            first_dir / "HANDOFF.json",
            "44444444-4444-4444-4444-444444444444",
        )


def test_operator_recording_rejects_a_mismatched_nested_creator_route(
    project_root: Path, tmp_path: Path
) -> None:
    renderer = _renderer()
    out_dir = tmp_path / "mismatched-source"
    _render(renderer, _request(), project_root, out_dir)
    handoff_path = out_dir / "HANDOFF.json"
    handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
    handoff["transport_request"]["source_thread_id"] = "55555555-5555-5555-5555-555555555555"
    handoff_path.write_text(json.dumps(handoff), encoding="utf-8")

    with pytest.raises(renderer.PacketInputError, match="must equal top-level source_thread_id"):
        renderer.record_operator_thread_id(
            handoff_path,
            "22222222-2222-2222-2222-222222222222",
        )


@pytest.mark.parametrize(
    ("caller_role", "workflow_node", "source_thread_id"),
    [
        ("em", "em_innovator", "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA"),
        ("em", "em_convergence", "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        ("portfolio", "portfolio_decision", "ABCDEFAB-CDEF-ABCD-EFAB-CDEFABCDEFAB"),
    ],
)
def test_source_thread_id_is_exactly_propagated_for_every_decision_node(
    project_root: Path,
    tmp_path: Path,
    caller_role: str,
    workflow_node: str,
    source_thread_id: str,
) -> None:
    renderer = _renderer()
    request = {
        **_request(),
        "caller_role": caller_role,
        "workflow_node": workflow_node,
        "source_thread_id": source_thread_id,
    }
    if caller_role == "portfolio":
        request["direction_ids"] = ["demo_direction", "second_direction"]
        request.pop("direction_id")

    out_dir = tmp_path / workflow_node
    handoff = _render(renderer, request, project_root, out_dir)

    assert handoff["source_thread_id"] == source_thread_id
    assert handoff["transport_request"]["source_thread_id"] == source_thread_id
    assert handoff["return_receipt_thread_id"] == source_thread_id
    assert handoff["transport_request"]["return_receipt_thread_id"] == source_thread_id
    assert handoff["transport_request"]["creator_thread_id"] == source_thread_id
    assert handoff["transport_request"]["return_route"] == "CREATOR_SESSION"
    assert not handoff.get("fallback_enabled", False)
    assert not handoff["transport_request"].get("fallback_enabled", False)
    assert source_thread_id not in (out_dir / "PROMPT_BODY.md").read_text(encoding="utf-8")


def test_source_thread_id_changes_only_handoff_routing_content(
    project_root: Path, tmp_path: Path
) -> None:
    renderer = _renderer()
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first = _render(
        renderer,
        {**_request(), "source_thread_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"},
        project_root,
        first_dir,
    )
    second = _render(
        renderer,
        {**_request(), "source_thread_id": "ABCDEFAB-CDEF-ABCD-EFAB-CDEFABCDEFAB"},
        project_root,
        second_dir,
    )

    assert (first_dir / "PROMPT_BODY.md").read_bytes() == (second_dir / "PROMPT_BODY.md").read_bytes()
    assert first["source_thread_id"] != second["source_thread_id"]
    assert first["transport_request"]["source_thread_id"] != second["transport_request"]["source_thread_id"]


@pytest.mark.parametrize("value", [None, "", "  \t"])
def test_missing_or_blank_source_thread_id_is_a_consolidated_input_gap(
    project_root: Path, value: object
) -> None:
    renderer = _renderer()

    with pytest.raises(renderer.PacketInputError) as exc_info:
        renderer.validate({**_request(), "source_thread_id": value}, project_root)

    assert exc_info.value.kind == "missing_input"
    assert exc_info.value.missing_fields == ["source_thread_id"]


def test_author_skill_closes_the_dispatch_sequence_and_keeps_pro_transport_separate(
    project_root: Path, tmp_path: Path
) -> None:
    renderer = _renderer()
    handoff = _render(renderer, _request(), project_root, tmp_path / "packet")
    skill_text = SKILL.read_text(encoding="utf-8")

    assert "Validate the caller input" in skill_text
    assert "Render exactly the two files" in skill_text
    assert "`create_thread` exactly once" in skill_text
    assert "`send_message_to_thread` exactly once" in skill_text
    assert "authoring task is not complete until" in skill_text
    assert "task exclusively owns Pro/browser send" in skill_text
    assert "Complete validated input proceeds directly without a confirmation prompt" in skill_text
    assert "Connector availability and GitHub retrieval are Transport/Pro checks" in skill_text
    assert "must not become an author-side blocker" in skill_text
    assert all(
        term in skill_text
        for term in (
            "model and connector checks",
            "conversation binding",
            "waiting",
            "archive",
            "cleanup",
        )
    )
    assert ("does not call " + "the transport operator") not in skill_text
    assert ("does not send" + ", open a browser") not in skill_text
    assert ("send_from_" + "author") not in skill_text
    assert handoff["dispatch_mode"] == "CREATE_ON_DEMAND"
    assert handoff["operator_thread_id"] is None


def test_missing_required_input_returns_one_consolidated_caller_question_without_rendering(
    project_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    renderer = _renderer()
    request = _request()
    request.pop("scientific_question")
    request.pop("claim_ceiling")
    request.pop("source_thread_id")
    request["reference_files"] = []
    request_path = tmp_path / "request.json"
    out_dir = tmp_path / "packet"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "render_packet.py",
            str(request_path),
            "--out-dir",
            str(out_dir),
            "--project-root",
            str(project_root),
        ],
    )

    assert renderer.main() == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is False
    assert payload["error"]["kind"] == "missing_input"
    assert payload["error"]["missing_fields"] == [
        "source_thread_id",
        "scientific_question",
        "claim_ceiling",
        "reference_files",
    ]
    assert payload["error"]["question"].count("?") == 1
    assert not out_dir.exists()


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("caller_role", "operator", "caller_role"),
        ("source_thread_id", "not-a-codex-task", "source_thread_id"),
        ("direction_id", "../escape", "direction_id"),
        ("repository_url", 42, "repository_url"),
        ("reference_files", "not-a-list", "reference_files"),
    ],
)
def test_malformed_caller_input_is_rejected(
    project_root: Path, field: str, value: object, error: str
) -> None:
    renderer = _renderer()

    with pytest.raises(renderer.PacketInputError, match=error) as exc_info:
        renderer.validate({**_request(), field: value}, project_root)
    assert exc_info.value.kind == "malformed_input"
    assert exc_info.value.field == error


def test_dispatch_contract_has_no_digest_identity_or_authentication_gate(
    project_root: Path, tmp_path: Path
) -> None:
    renderer = _renderer()
    handoff = _render(renderer, _request(), project_root, tmp_path / "packet")
    serialized = json.dumps(handoff, ensure_ascii=False).lower()

    assert ("send_from_" + "author") not in serialized
    assert not any(token in serialized for token in ("sha256", "digest", "identity", "authentication"))


def test_em_innovator_and_convergence_use_distinct_persistent_bindings(
    project_root: Path, tmp_path: Path
) -> None:
    renderer = _renderer()
    convergence = _render(renderer, _request(), project_root, tmp_path / "convergence")
    innovator = _render(
        renderer,
        {**_request(), "request_id": "req-innovator-01", "workflow_node": "em_innovator"},
        project_root,
        tmp_path / "innovator",
    )

    assert convergence["conversation_binding_key"] == "em:demo_direction:convergence"
    assert innovator["conversation_binding_key"] == "em:demo_direction:innovator"
    assert convergence["conversation_binding_key"] != innovator["conversation_binding_key"]
    body = (tmp_path / "innovator" / "PROMPT_BODY.md").read_text(encoding="utf-8")
    assert "REQUEST_CLASS=SCIENTIFIC_INNOVATION" in body
    assert "DECISION_AUTHORITY=PRO_FINAL" in body
    assert "final decision for this workflow node" in body


def test_portfolio_uses_one_cross_direction_binding_and_final_decision_authority(
    project_root: Path, tmp_path: Path
) -> None:
    renderer = _renderer()
    request = {
        **_request(),
        "caller_role": "portfolio",
        "workflow_node": "portfolio_decision",
        "request_id": "portfolio-round-01",
        "direction_ids": ["demo_direction", "second_direction"],
    }
    request.pop("direction_id")
    handoff = _render(renderer, request, project_root, tmp_path / "portfolio")

    assert handoff["direction_id"] == "portfolio"
    assert handoff["direction_ids"] == ["demo_direction", "second_direction"]
    assert handoff["conversation_binding_key"] == "portfolio:cross_direction"
    assert handoff["decision_authority"] == "pro_final"
    assert handoff["transport_request"]["conversation_binding_key"] == "portfolio:cross_direction"
    body = (tmp_path / "portfolio" / "PROMPT_BODY.md").read_text(encoding="utf-8")
    assert "REQUEST_CLASS=PORTFOLIO_DECISION" in body
    assert "DIRECTION_SCOPE=demo_direction,second_direction" in body
    assert "priority, capacity, lifecycle, fusion, separation" in body


@pytest.mark.parametrize(
    ("caller_role", "workflow_node"),
    [
        ("portfolio", "em_innovator"),
        ("portfolio", "em_convergence"),
        ("em", "portfolio_decision"),
    ],
)
def test_caller_and_workflow_node_must_match(
    project_root: Path, caller_role: str, workflow_node: str
) -> None:
    renderer = _renderer()
    request = {**_request(), "caller_role": caller_role, "workflow_node": workflow_node}
    if caller_role == "portfolio":
        request["direction_ids"] = ["demo_direction"]
        request.pop("direction_id")

    with pytest.raises(renderer.PacketInputError, match="requires caller_role"):
        renderer.validate(request, project_root)
