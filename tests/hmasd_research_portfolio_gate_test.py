from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO
    / ".agents"
    / "skills"
    / "hmasd-independent-research-exploration"
    / "scripts"
    / "research_portfolio_gate.py"
)
SPEC = importlib.util.spec_from_file_location("research_portfolio_gate", SCRIPT)
assert SPEC and SPEC.loader
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def _assignment(
    assignment_id: str,
    role: str,
    phase: str,
    *,
    source_ids: list[str] | None = None,
    opportunity_id: str | None = None,
) -> dict[str, object]:
    return {
        "assignment_id": assignment_id,
        "role": role,
        "phase": phase,
        "cycle_id": "cycle-1",
        "status": "terminal",
        "source_ids": source_ids or [],
        "opportunity_id": opportunity_id,
    }


def _packet(
    packet_id: str,
    assignment_id: str,
    packet_kind: str,
    *,
    source_ids: list[str] | None = None,
    candidate_ids: list[str] | None = None,
    principles_packet_ids: list[str] | None = None,
) -> dict[str, object]:
    packet: dict[str, object] = {
        "packet_id": packet_id,
        "assignment_id": assignment_id,
        "packet_kind": packet_kind,
        "status": "terminal",
    }
    if source_ids is not None:
        packet["source_ids"] = source_ids
    if candidate_ids is not None:
        packet["candidate_ids"] = candidate_ids
    if principles_packet_ids is not None:
        packet["principles_packet_ids"] = principles_packet_ids
    return packet


def inspiration_record(source_count: int = 6) -> dict[str, object]:
    source_assignments = [
        _assignment(f"scout-{index}", "scout", "source_absorption", source_ids=[f"paper-{index}"])
        for index in range(source_count)
    ]
    source_packets = [
        _packet(
            f"source-packet-{index}",
            f"scout-{index}",
            "SOURCE_RESULT_PACKET",
            source_ids=[f"paper-{index}"],
        )
        for index in range(source_count)
    ]
    assignments = [
        *source_assignments,
        _assignment("innovator-1", "innovator", "innovation"),
        _assignment("innovator-2", "innovator", "innovation"),
        _assignment("principles-1", "principles_analyst", "principles_review"),
        _assignment("principles-2", "principles_analyst", "principles_review"),
        _assignment("critic-1", "critic", "adversarial_review"),
        _assignment("critic-2", "critic", "adversarial_review"),
    ]
    packets = [
        *source_packets,
        _packet("idea-1", "innovator-1", "ALGORITHM_INSPIRATION_PACKET", candidate_ids=["candidate-1"]),
        _packet("idea-2", "innovator-2", "ALGORITHM_INSPIRATION_PACKET", candidate_ids=["candidate-2"]),
        _packet(
            "principles-packet-1",
            "principles-1",
            "RL_PRINCIPLE_ANALYSIS_PACKET",
            candidate_ids=["candidate-1"],
        ),
        _packet(
            "principles-packet-2",
            "principles-2",
            "RL_PRINCIPLE_ANALYSIS_PACKET",
            candidate_ids=["candidate-2"],
        ),
        _packet(
            "critic-packet-1",
            "critic-1",
            "CRITIC_ASSESSMENT_PACKET",
            candidate_ids=["candidate-1"],
            principles_packet_ids=["principles-packet-1"],
        ),
        _packet(
            "critic-packet-2",
            "critic-2",
            "CRITIC_ASSESSMENT_PACKET",
            candidate_ids=["candidate-2"],
            principles_packet_ids=["principles-packet-2"],
        ),
    ]
    manifest = [
        {
            "source_id": f"paper-{index}",
            "immutable_identity": f"MARL-{index:04d}@pdf-sha",
            "inclusion_reason": "Relevant source result for variable membership.",
            "owner_assignment_id": f"scout-{index}",
        }
        for index in range(source_count)
    ]
    criteria = {name: True for name in gate.CONVERGENCE_CRITERIA}
    return {
        "document_kind": "independent_research_campaign_v3",
        "intake": {
            "mode": "algorithm_inspiration_campaign",
            "direction_or_question": "How should a shared policy learn with variable agent population?",
            "mission_link": "General MARL under membership churn.",
            "authorized_source_boundary": "Validated MyLib snapshot and named PDFs.",
            "completion_meaning": "Multi-direction portfolio converged inside the source boundary.",
            "exclusions": ["formal workflow", "code", "compute"],
        },
        "campaign": {
            "campaign_id": "variable-agents-campaign",
            "user_authorization_id": "user-confirmed",
            "assignment_policy": "exact_work_roster",
            "runtime_concurrency": "available_native_capacity",
            "resource_policy": "explicit_work_rosters_plus_recorded_convergence",
            "optional_total_assignment_ceiling": None,
        },
        "corpus": {"version": 1, "manifest": manifest, "deltas": []},
        "assignments": assignments,
        "packets": packets,
        "cycles": [
            {
                "cycle_id": "cycle-1",
                "index": 1,
                "stages": [
                    {
                        "stage": "source_absorption",
                        "assignment_ids": [f"scout-{index}" for index in range(source_count)],
                        "complete": True,
                    },
                    {
                        "stage": "innovation",
                        "assignment_ids": ["innovator-1", "innovator-2"],
                        "complete": True,
                    },
                    {
                        "stage": "principles_review",
                        "assignment_ids": ["principles-1", "principles-2"],
                        "complete": True,
                    },
                    {
                        "stage": "adversarial_review",
                        "assignment_ids": ["critic-1", "critic-2"],
                        "complete": True,
                    },
                    {"stage": "portfolio_update", "assignment_ids": [], "complete": True},
                ],
            }
        ],
        "portfolio": [
            {
                "candidate_id": "candidate-1",
                "status": "retained",
                "target_problem": "Membership-conditioned exploration.",
                "mechanism": "Uncertainty-conditioned active-set belief.",
                "learning_driver": "Directed uncertainty reduction.",
                "source_result_packet_ids": ["source-packet-0"],
                "parent_candidate_ids": [],
                "principles_packet_ids": ["principles-packet-1"],
                "critic_packet_ids": ["critic-packet-1"],
                "recommended": True,
            },
            {
                "candidate_id": "candidate-2",
                "status": "retained",
                "target_problem": "Survivor-state continuity.",
                "mechanism": "Entity-owned recurrent state.",
                "learning_driver": "Credit continuity across membership events.",
                "source_result_packet_ids": ["source-packet-1"],
                "parent_candidate_ids": [],
                "principles_packet_ids": ["principles-packet-2"],
                "critic_packet_ids": ["critic-packet-2"],
                "recommended": True,
            },
        ],
        "opportunities": [
            {
                "opportunity_id": "op-new",
                "kind": "new_mechanism",
                "status": "completed",
                "source_ids": ["paper-0"],
                "parent_candidate_ids": [],
                "material_delta": "Adds membership uncertainty as an exploration object.",
                "expected_portfolio_effect": "Creates candidate-1.",
                "required_role": "innovator",
                "completion_condition": "Mechanism candidate returned.",
                "planned_assignment_ids": [],
            },
            {
                "opportunity_id": "op-transfer",
                "kind": "transfer",
                "status": "completed",
                "source_ids": ["paper-1"],
                "parent_candidate_ids": ["candidate-1"],
                "material_delta": "Transfers uncertainty control to active-set renewal.",
                "expected_portfolio_effect": "Refines candidate-1.",
                "required_role": "innovator",
                "completion_condition": "Transfer assumptions recorded.",
                "planned_assignment_ids": [],
                "source_context": "Partner uncertainty.",
                "target_context": "Membership uncertainty.",
                "changed_assumptions": ["Fixed partner roster becomes stochastic membership."],
            },
            {
                "opportunity_id": "op-combine",
                "kind": "combination",
                "status": "completed",
                "source_ids": [],
                "parent_candidate_ids": ["candidate-1", "candidate-2"],
                "material_delta": "Connects exploration belief and survivor memory.",
                "expected_portfolio_effect": "Adds a combined candidate edge.",
                "required_role": "innovator",
                "completion_condition": "Interaction claim recorded.",
                "planned_assignment_ids": [],
                "new_interaction": "Belief updates gate entity-state renewal.",
            },
            {
                "opportunity_id": "op-correction",
                "kind": "important_correction",
                "status": "parked",
                "source_ids": [],
                "parent_candidate_ids": ["candidate-1"],
                "material_delta": "Separates passive entropy from directed exploration.",
                "expected_portfolio_effect": "Weakens an exploration claim.",
                "required_role": "principles_analyst",
                "completion_condition": "Correction has a reactivation condition.",
                "planned_assignment_ids": [],
            },
            {
                "opportunity_id": "op-split",
                "kind": "subdirection_split",
                "status": "completed",
                "source_ids": [],
                "parent_candidate_ids": ["candidate-2"],
                "material_delta": "Separates replacement from rejoin.",
                "expected_portfolio_effect": "Creates two subdirections.",
                "required_role": "innovator",
                "completion_condition": "Distinct predictions recorded.",
                "planned_assignment_ids": [],
                "distinct_assumption_driver_or_prediction": "Rejoin preserves entity state; replacement does not.",
            },
            {
                "opportunity_id": "op-cross",
                "kind": "cross_direction_inspiration",
                "status": "completed",
                "source_ids": ["paper-2"],
                "parent_candidate_ids": ["candidate-1", "candidate-2"],
                "material_delta": "Uses temporal renewal to connect belief and memory.",
                "expected_portfolio_effect": "Adds a cross-direction edge.",
                "required_role": "innovator",
                "completion_condition": "Cross-direction transformation recorded.",
                "planned_assignment_ids": [],
            },
        ],
        "convergence": {
            "status": "CONVERGED",
            "criteria": criteria,
            "basis": [
                "All corpus assignments are terminal.",
                "All retained candidates have principles and adversarial review.",
                "All six opportunity classes are closed.",
            ],
        },
    }


@pytest.mark.parametrize("phase", ["intake", "absorption", "cycle", "convergence"])
def test_inspiration_campaign_passes_all_phases(phase: str) -> None:
    result = gate.validate_record(inspiration_record(), phase)
    assert result["mode"] == "algorithm_inspiration_campaign"


def test_first_absorption_roster_is_not_capped_at_four() -> None:
    result = gate.validate_record(inspiration_record(source_count=9), "absorption")
    assert result["sources"] == 9


def test_fixed_parallel_limit_is_rejected() -> None:
    record = inspiration_record()
    record["campaign"]["scout_parallel_limit"] = 4
    with pytest.raises(gate.GateError, match="retired key"):
        gate.validate_record(record, "intake")


def test_missing_source_result_fails_absorption() -> None:
    record = inspiration_record()
    record["packets"] = [packet for packet in record["packets"] if packet["packet_id"] != "source-packet-0"]
    with pytest.raises(gate.GateError, match="has no packet"):
        gate.validate_record(record, "absorption")


def test_phase_order_requires_principles_before_criticism() -> None:
    record = inspiration_record()
    stages = record["cycles"][0]["stages"]
    stages[2], stages[3] = stages[3], stages[2]
    with pytest.raises(gate.GateError, match="phase order"):
        gate.validate_record(record, "cycle")


def test_critic_requires_candidate_principles_packet() -> None:
    record = inspiration_record()
    record["packets"][-2]["principles_packet_ids"] = ["principles-packet-2"]
    with pytest.raises(gate.GateError, match="lacks principles prerequisite"):
        gate.validate_record(record, "cycle")


def test_combination_requires_multiple_parents() -> None:
    record = inspiration_record()
    record["opportunities"][2]["parent_candidate_ids"] = ["candidate-1"]
    with pytest.raises(gate.GateError, match="needs two parents"):
        gate.validate_record(record, "cycle")


def test_transfer_requires_source_and_target_context() -> None:
    record = inspiration_record()
    del record["opportunities"][1]["target_context"]
    with pytest.raises(gate.GateError, match="target_context"):
        gate.validate_record(record, "cycle")


def test_split_requires_one_parent_and_distinct_basis() -> None:
    record = inspiration_record()
    record["opportunities"][4]["parent_candidate_ids"] = []
    with pytest.raises(gate.GateError, match="needs one parent"):
        gate.validate_record(record, "cycle")


def test_convergence_rejects_a_planned_opportunity() -> None:
    record = inspiration_record()
    record["opportunities"][0]["status"] = "planned"
    record["opportunities"][0]["planned_assignment_ids"] = ["innovator-1"]
    record["assignments"][-6]["opportunity_id"] = "op-new"
    with pytest.raises(gate.GateError, match="planned opportunity"):
        gate.validate_record(record, "convergence")


def test_resource_boundary_is_not_convergence() -> None:
    record = inspiration_record()
    record["convergence"]["status"] = "PARTIAL_CAMPAIGN_RESOURCE_BOUND"
    record["convergence"]["criteria"]["no_transfer_opportunity"] = False
    record["convergence"]["resource_boundary"] = "Authorized assignment ceiling exhausted."
    gate.validate_record(record, "convergence")


def test_unique_winner_field_is_rejected() -> None:
    record = inspiration_record()
    record["portfolio"][0]["unique_winner"] = True
    with pytest.raises(gate.GateError, match="retired key"):
        gate.validate_record(record, "intake")


def test_recommended_candidate_needs_adversarial_review() -> None:
    record = inspiration_record()
    record["portfolio"][0]["critic_packet_ids"] = []
    with pytest.raises(gate.GateError, match="lacks adversarial review"):
        gate.validate_record(record, "cycle")


def test_candidate_validation_loads_strict_methodology_only_when_mature() -> None:
    record = inspiration_record()
    record["intake"]["mode"] = "candidate_validation"
    record["validation_candidate"] = {
        "candidate_id": "candidate-1",
        "precise_defect": "Slot identity aliases replacement and rejoin.",
        "mechanism": "Entity-owned recurrent state.",
        "algorithm_delta": "Replace slot ownership with entity ownership.",
        "strongest_simple_explanation": "Ordinary masked recurrence.",
        "separating_prediction": "Rejoin preserves state while replacement resets.",
        "methodology_reference": "research-methodology.md",
    }
    result = gate.validate_record(record, "cycle")
    assert result["mode"] == "candidate_validation"


def test_candidate_validation_rejects_missing_separating_prediction() -> None:
    record = inspiration_record()
    record["intake"]["mode"] = "candidate_validation"
    record["validation_candidate"] = {
        "candidate_id": "candidate-1",
        "precise_defect": "Slot identity aliases replacement and rejoin.",
        "mechanism": "Entity-owned recurrent state.",
        "algorithm_delta": "Replace slot ownership with entity ownership.",
        "strongest_simple_explanation": "Ordinary masked recurrence.",
        "methodology_reference": "research-methodology.md",
    }
    with pytest.raises(gate.GateError, match="separating_prediction"):
        gate.validate_record(record, "cycle")


def test_load_record_rejects_path_outside_local_research(tmp_path: Path) -> None:
    path = tmp_path / "record.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(gate.GateError, match="outside"):
        gate.load_record(path, REPO)
