"""Focused source contract for the registered WDM workflow children."""

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
        "auditor",
        ROOT / ".agents/roles/WORKFLOW_AUDITOR.md",
        ROOT / ".codex/agents/hmasd-workflow-auditor.toml",
        "WORKFLOW_IMPACT_PACKET",
    ),
    (
        "implementer",
        ROOT / ".agents/roles/WORKFLOW_IMPLEMENTER.md",
        ROOT / ".codex/agents/hmasd-workflow-implementer.toml",
        "WORKFLOW_CHANGE_PACKET",
    ),
    (
        "reviewer",
        ROOT / ".agents/roles/WORKFLOW_REVIEWER.md",
        ROOT / ".codex/agents/hmasd-workflow-reviewer.toml",
        "WORKFLOW_REVIEW_PACKET",
    ),
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return " ".join(text.split()).lower()


def _bare_packet_or_terminal(fragment: str) -> bool:
    """A realistic transport fragment that cannot stand in for a conclusion."""

    return bool(
        re.match(
            r"^\s*(?:`?WORKFLOW_[A-Z_]+_PACKET`?|COMPLETE)(?:\b|\s|$)",
            fragment,
            re.IGNORECASE,
        )
    )


def test_each_role_uses_a_semantic_task_model_and_conclusion_first_result() -> None:
    for _name, role_path, _profile_path, packet_name in CHILDREN:
        role = _normalized(_text(role_path))
        for required in (
            "self-contained natural-language task model",
            "workflow_assignment_id",
            "owned_paths",
            "factual authority and scope anchors",
            "never define task meaning",
            "never define task meaning or completion",
            "concise natural-language conclusion",
            "owned outcome",
            "complete or unresolved",
            "direct consequence",
            "residual uncertainty",
            "compact factual",
            packet_name.lower(),
            "never substitutes for the conclusion",
        ):
            assert required in role, f"{role_path} lacks {required!r}"

        # Packet names remain factual tails only; these forms would let a bare
        # transport token masquerade as the child’s semantic result.
        assert "return the packet only" not in role
        assert not re.search(
            r"return\s+(?:one\s+)?(?:exactly\s+one\s+)?`?workflow_[a-z_]+_packet`?",
            role,
        )


def test_bounded_recovery_is_tailored_without_a_second_state_machine() -> None:
    auditor = _normalized(_text(CHILDREN[0][1]))
    implementer = _normalized(_text(CHILDREN[1][1]))
    reviewer = _normalized(_text(CHILDREN[2][1]))

    for required in (
        "at most one alternate read-only observation",
        "re-read of an assignment-named direct interface",
        "may not add scope, design, edit or accept",
    ):
        assert required in auditor

    for required in (
        "focused local check",
        "inspect the local postcondition",
        "at most one reversible correction/re-run",
        "within these same owned paths",
        "may not change the frozen plan or add paths",
    ):
        assert required in implementer

    for required in (
        "integrated diff and assigned evidence conflict",
        "at most one bounded re-read",
        "read-only reproduction",
        "may not start a second review round",
        "reviewer-of-reviewer",
    ):
        assert required in reviewer


def test_children_are_leaves_and_return_to_the_wdm_parent() -> None:
    role = _normalized(_text(CHILDREN[1][1]))
    for child_role, _ in ((CHILDREN[0][1], "auditor"), (CHILDREN[1][1], "implementer"), (CHILDREN[2][1], "reviewer")):
        text = _normalized(_text(child_role))
        assert "agent_tree_level=2" in text
        assert "parent=workflow_design_manager" in text
        for required in ("spawn_authority=none", "user_contact_authority=none", "cross_branch_transport=none"):
            assert required in text
        assert "return" in text and "parent" in text
        assert "resolved_ticket_worktree_path" not in text
        assert "scripts/hmasd_workspace_ticket.py" not in text
    assert "git" in role
    implementer = _normalized(_text(CHILDREN[1][1]))
    assert "never invoke" in implementer
    assert "helper" in implementer
    assert "git lifecycle" in implementer


def test_implementer_slice_evidence_and_reviewer_advice_cannot_accept() -> None:
    implementer = _normalized(_text(CHILDREN[1][1]))
    reviewer = _normalized(_text(CHILDREN[2][1]))
    for required in (
        "owned",
        "slice",
        "candidate-ready evidence",
        "fork_turns=none",
    ):
        assert required in implementer, required
    for required in (
        "read-only",
        "advisory",
        "acceptance_authority=none",
        "cannot accept",
    ):
        assert required in reviewer, required


def test_profiles_are_thin_and_keep_forked_history_independent() -> None:
    expected = {
        "auditor": ("gpt-5.6-luna", "high", "read-only"),
        "implementer": ("gpt-5.6-luna", "xhigh", "workspace-write"),
        "reviewer": ("gpt-5.6-luna", "max", "read-only"),
    }
    for name, role_path, profile_path, _packet_name in CHILDREN:
        with profile_path.open("rb") as stream:
            profile = tomllib.load(stream)
        assert profile["name"] == f"hmasd-workflow-{name}"
        model, effort, sandbox = expected[name]
        assert profile["model"] == model
        assert profile["model_reasoning_effort"] == effort
        assert profile["sandbox_mode"] == sandbox
        assert profile["approval_policy"] == "never"

        instructions = _normalized(profile["developer_instructions"])
        role_pointer = str(role_path.relative_to(ROOT)).replace("\\", "/").lower()
        for required in (
            "fork_turns=none",
            "forked context is background only",
            "self-contained natural-language task model",
            "workflow design manager is the parent",
            "sole workflow design, routing and acceptance owner",
            role_pointer,
            "root router",
            "exact assignment",
            "this registered profile",
            "do not duplicate those procedures",
        ):
            assert required in instructions, f"{profile_path} lacks {required!r}"

        # Procedure details stay in the role charter instead of becoming a
        # second profile protocol or fixed packet admission rule.
        for forbidden in (
            "return exactly one",
            "return one workflow_",
            "for impact_map,",
            "a finding is actionable only when",
            "reversible correction/re-run",
            "bounded re-read",
        ):
            assert forbidden not in instructions
        assert "workflow_impact_packet" not in instructions
        assert "workflow_change_packet" not in instructions
        assert "workflow_review_packet" not in instructions


def test_contract_rejects_bare_packet_or_complete_fragments_without_fixed_headings() -> None:
    assert _bare_packet_or_terminal("WORKFLOW_CHANGE_PACKET status=COMPLETE")
    assert _bare_packet_or_terminal("`WORKFLOW_REVIEW_PACKET` COMPLETE")
    assert _bare_packet_or_terminal("COMPLETE")
    assert not _bare_packet_or_terminal(
        "The owned workflow slice is complete because the direct consequence check passed; residual uncertainty is none."
    )
    for _name, role_path, _profile_path, _packet_name in CHILDREN:
        role = _normalized(_text(role_path))
        assert "packet name or terminal token never substitutes for the conclusion" in role
