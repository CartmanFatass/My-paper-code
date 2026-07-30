from __future__ import annotations

import copy
import importlib.util
import json
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


def intake(mode: str) -> dict[str, object]:
    result: dict[str, object] = {
        "mode": mode,
        "question": "What does the bounded task establish?",
        "mission_link": "Variable team membership and skill lifetime",
        "named_sources": ["frozen-source-a", "frozen-source-b"],
        "exclusions": ["formal workflow", "compute"],
        "completion_condition": "Return audited result or exact gap",
        "semantic_traps": ["visibility is not membership", "duration is not termination"],
    }
    if mode == "scientific_innovation":
        result["evidence_baseline"] = "evidence-review-2026-07-30"
    return result


def evidence_record() -> dict[str, object]:
    return {
        "document_kind": "independent_research_record_v1",
        "intake": intake("evidence_review"),
        "families": [],
        "wave": {
            "wave_id": "evidence-wave-1",
            "cross_pollination_started": False,
            "assignments": [
                {
                    "assignment_id": "scout-a",
                    "claim_id": "claim-a",
                    "evidence_axis_id": "dynamic-team",
                    "source_ids": ["MARL-0001"],
                    "source_bindings": [
                        {
                            "source_identity": "MARL-0001",
                            "evidence_type": "json",
                            "evidence_path": "C:/MyLib/json/MARL-0001.json",
                        }
                    ],
                    "semantic_traps": ["episode count is not within-episode churn"],
                },
                {
                    "assignment_id": "scout-b",
                    "claim_id": "claim-b",
                    "evidence_axis_id": "skill-lifetime",
                    "source_ids": ["MARL-0002"],
                    "source_bindings": [
                        {
                            "source_identity": "MARL-0002",
                            "evidence_type": "pdf",
                            "evidence_path": "C:/MyLib/pdf/MARL-0002.pdf",
                        }
                    ],
                    "semantic_traps": ["adaptive duration is not learned termination"],
                },
            ],
            "packets": [
                {
                    "packet_id": "packet-a",
                    "packet_kind": "SCOUT_EVIDENCE_PACKET",
                    "assignment_id": "scout-a",
                    "claim_id": "claim-a",
                    "evidence_axis_id": "dynamic-team",
                    "status": "terminal",
                    "source_ids": ["MARL-0001"],
                    "semantic_trap_results": [
                        {
                            "trap": "episode count is not within-episode churn",
                            "disposition": "unresolved",
                        }
                    ],
                    "evidence_rows": [
                        {
                            "claim_id": "claim-a",
                            "claim": "Within-episode churn is distinct from episode-level count variation.",
                            "source_identity": "MARL-0001",
                            "title": "Dynamic Team Example",
                            "evidence_path": "C:/MyLib/json/MARL-0001.json",
                            "evidence_type": "json",
                            "locator": "p3/e17",
                            "provenance": "structured-json",
                            "claim_kind": "paper_claim",
                            "confidence": 0.8,
                        }
                    ],
                },
                {
                    "packet_id": "packet-b",
                    "packet_kind": "SCOUT_EVIDENCE_PACKET",
                    "assignment_id": "scout-b",
                    "claim_id": "claim-b",
                    "evidence_axis_id": "skill-lifetime",
                    "status": "terminal",
                    "source_ids": ["MARL-0002"],
                    "semantic_trap_results": [
                        {
                            "trap": "adaptive duration is not learned termination",
                            "disposition": "pass",
                        }
                    ],
                    "evidence_rows": [
                        {
                            "claim_id": "claim-b",
                            "claim": "Adaptive duration is not learned termination.",
                            "source_identity": "MARL-0002",
                            "title": "Skill Lifetime Example",
                            "evidence_path": "C:/MyLib/pdf/MARL-0002.pdf",
                            "evidence_type": "pdf",
                            "locator": "pdf-p5",
                            "provenance": "hash-bound-pdf",
                            "claim_kind": "paper_limitation",
                            "confidence": 0.9,
                        }
                    ],
                },
            ],
        },
        "critic_packets": [],
    }


def direction_packet(
    packet_id: str,
    assignment_id: str,
    family_id: str,
    claim_id: str,
    exact_claim: str,
    mechanism: str,
    trap: str,
) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "packet_kind": "RESEARCH_DIRECTION_PACKET",
        "assignment_id": assignment_id,
        "family_id": family_id,
        "claim_id": claim_id,
        "core_mechanism": mechanism,
        "exact_claim": exact_claim,
        "mission_link": "Variable team membership and skill lifetime",
        "evidence_baseline": "evidence-review-2026-07-30",
        "status": "terminal",
        "semantic_trap_results": [{"trap": trap, "disposition": "pass"}],
        "assumptions": ["identity is persistent"],
        "derivation_or_construction": "Define a membership-keyed state transition.",
        "novelty_delta": "Separates authoritative membership from visibility.",
        "evidence_dependencies": ["evidence-review-2026-07-30"],
        "strongest_internal_counterexample": "Slot reuse without persistent identity.",
        "alternate_explanations": ["benefit comes from capacity rather than lifecycle"],
        "failure_boundaries": ["identity unavailable"],
        "missing_lemma_or_interface": "Need an identity-preservation interface.",
        "falsifiable_predictions": ["state checksum survives a visibility-only change"],
        "minimal_discriminator": "One join-leave-rejoin trace without optimization.",
        "concrete_outputs": [
            {
                "kind": "counterexample",
                "content": "Visibility masking alone aliases inactive and occluded agents.",
            }
        ],
    }


def innovation_record() -> dict[str, object]:
    record = {
        "document_kind": "independent_research_record_v1",
        "intake": intake("scientific_innovation"),
        "families": [
            {
                "family_id": "family-identity",
                "core_mechanism": "identity-keyed lifecycle state",
                "exact_claim": "Identity separates replacement from rejoin.",
                "evidence_baseline": "evidence-review-2026-07-30",
                "strongest_support": "CAMA exposes active-set churn.",
                "strongest_counterexample": "Slots may lack persistent identity.",
                "current_gap": "No authoritative identity interface.",
                "status": "blocked",
                "reopen_condition": "A new identity mechanism or invariant.",
                "innovator_packet_ids": ["direction-a"],
                "critic_status": "contradicted",
            },
            {
                "family_id": "family-duration",
                "core_mechanism": "learned asynchronous duration gate",
                "exact_claim": "A differentiable gate can induce asynchronous renewal.",
                "evidence_baseline": "evidence-review-2026-07-30",
                "strongest_support": "Duration selection and async credit exist separately.",
                "strongest_counterexample": "A hidden synchronized clock may dominate.",
                "current_gap": "No joint implementation evidence.",
                "status": "live",
                "reopen_condition": "A parameter-flow construction.",
                "innovator_packet_ids": ["direction-b"],
                "critic_status": "not_selected",
            },
        ],
        "wave": {
            "wave_id": "innovation-wave-1",
            "cross_pollination_started": True,
            "assignments": [
                {
                    "assignment_id": "innovator-a",
                    "family_id": "family-identity",
                    "claim_id": "claim-identity",
                    "core_mechanism": "identity-keyed lifecycle state",
                    "exact_claim": "Identity separates replacement from rejoin.",
                    "mission_link": "Variable team membership and skill lifetime",
                    "evidence_baseline": "evidence-review-2026-07-30",
                    "purpose": "develop",
                    "favored_family_visibility": "withheld",
                    "semantic_traps": ["visibility is not membership"],
                },
                {
                    "assignment_id": "innovator-b",
                    "family_id": "family-duration",
                    "claim_id": "claim-duration",
                    "core_mechanism": "learned asynchronous duration gate",
                    "exact_claim": "A differentiable gate can induce asynchronous renewal.",
                    "mission_link": "Variable team membership and skill lifetime",
                    "evidence_baseline": "evidence-review-2026-07-30",
                    "purpose": "challenge",
                    "favored_family_visibility": "named_for_challenge",
                    "semantic_traps": ["duration choice is not learned termination"],
                },
            ],
            "packets": [
                direction_packet(
                    "direction-a",
                    "innovator-a",
                    "family-identity",
                    "claim-identity",
                    "Identity separates replacement from rejoin.",
                    "identity-keyed lifecycle state",
                    "visibility is not membership",
                ),
                direction_packet(
                    "direction-b",
                    "innovator-b",
                    "family-duration",
                    "claim-duration",
                    "A differentiable gate can induce asynchronous renewal.",
                    "learned asynchronous duration gate",
                    "duration choice is not learned termination",
                ),
            ],
        },
        "critic_packets": [
            {
                "critic_assignment_id": "critic-identity",
                "packet_kind": "CRITIC_ASSESSMENT_PACKET",
                "status": "terminal",
                "claim_id": "claim-identity",
                "target_identity": "family-identity",
                "source_packet_ids": ["direction-a"],
                "disposition": "contradicted",
                "correction": "The claim requires an authoritative persistent identity.",
                "checklist_results": ["slot reuse counterexample survives"],
            }
        ],
        "additional_wave_admission": {
            "prior_wave_id": "innovation-wave-1",
            "next_wave_id": "innovation-wave-2",
            "prior_terminal_assignment_ids": ["innovator-a", "innovator-b"],
            "prior_terminal_packet_ids": ["direction-a", "direction-b"],
            "target_family_id": "family-identity",
            "basis": "new_mechanism",
            "novelty_statement": "Add an explicit identity issuance and retirement protocol.",
            "expected_disposition_change": "blocked to live or contradicted",
            "innovator_budget": 2,
            "critic_budget": 1,
            "stop_condition": "One identity trace and one destructive counterexample.",
            "user_confirmation": "User confirmed innovation-wave-2.",
            "admission_fingerprint": "pending",
            "user_confirmation_fingerprint": "pending",
        },
        "synthesis": {
            "automatic_formal_promotion": False,
            "claims": [
                {
                    "claim_id": "claim-identity",
                    "critic_assignment_id": "critic-identity",
                    "disposition": "contradicted",
                    "correction": "The claim requires an authoritative persistent identity.",
                }
            ],
        },
    }
    fingerprint = gate._additional_wave_fingerprint(record["additional_wave_admission"])
    record["additional_wave_admission"]["admission_fingerprint"] = fingerprint
    record["additional_wave_admission"]["user_confirmation_fingerprint"] = fingerprint
    return record


def test_evidence_review_uses_disjoint_sources_and_crosses_merge() -> None:
    result = gate.validate_record(evidence_record(), "merge")
    assert result == {
        "mode": "evidence_review",
        "families": 0,
        "packets": 2,
        "terminal_failures": 0,
        "critics": 0,
    }

    duplicate = evidence_record()
    duplicate["wave"]["assignments"][1]["source_ids"] = ["MARL-0001"]
    with pytest.raises(gate.GateError, match="duplicate evidence source ownership"):
        gate.validate_record(duplicate, "merge")


def test_innovation_requires_favored_family_independence_shielding() -> None:
    record = innovation_record()
    record["wave"]["assignments"][0]["favored_family_visibility"] = "named_for_challenge"
    with pytest.raises(gate.GateError, match="independence shielding"):
        gate.validate_record(record, "merge")


def test_merge_barrier_blocks_early_cross_pollination() -> None:
    record = innovation_record()
    record["wave"]["packets"].pop()
    with pytest.raises(gate.GateError, match="cross-pollination started before"):
        gate.validate_record(record, "merge")


def test_terminal_operational_failure_closes_barrier_without_scientific_output() -> None:
    record = innovation_record()
    record["wave"]["packets"].pop()
    record["families"][1]["innovator_packet_ids"] = []
    record["wave"]["terminal_failures"] = [
        {
            "assignment_id": "innovator-b",
            "failure_kind": "OPERATIONAL_FAILURE",
            "status": "terminal",
            "failure_signature": "tool-route-unavailable",
            "unchanged_retry_count": 1,
            "scientific_output": False,
        }
    ]
    result = gate.validate_record(record, "merge")
    assert result["packets"] == 1
    assert result["terminal_failures"] == 1

    disguised_science = copy.deepcopy(record)
    disguised_science["wave"]["terminal_failures"][0]["scientific_claim"] = "contradicted"
    with pytest.raises(gate.GateError, match="unsupported fields"):
        gate.validate_record(disguised_science, "merge")

    stale_registration = copy.deepcopy(record)
    stale_registration["families"][1]["innovator_packet_ids"] = ["direction-b"]
    with pytest.raises(gate.GateError, match="registration differs"):
        gate.validate_record(stale_registration, "merge")


def test_malformed_evidence_packet_without_locator_is_rejected() -> None:
    record = evidence_record()
    del record["wave"]["packets"][0]["evidence_rows"][0]["locator"]
    with pytest.raises(gate.GateError, match="evidence row.locator"):
        gate.validate_record(record, "merge")

    wrong_source = evidence_record()
    wrong_source["wave"]["packets"][0]["evidence_rows"][0]["source_identity"] = "MARL-9999"
    with pytest.raises(gate.GateError, match="outside the packet source set"):
        gate.validate_record(wrong_source, "merge")

    relative_path = evidence_record()
    relative_path["wave"]["packets"][0]["evidence_rows"][0]["evidence_path"] = "MARL-0001.json"
    with pytest.raises(gate.GateError, match="path must be absolute"):
        gate.validate_record(relative_path, "merge")

    wrong_bound_path = evidence_record()
    wrong_bound_path["wave"]["packets"][0]["evidence_rows"][0]["evidence_path"] = (
        "C:/MyLib/json/MARL-9999.json"
    )
    with pytest.raises(gate.GateError, match="assigned source binding"):
        gate.validate_record(wrong_bound_path, "merge")


def test_direction_packet_is_bound_to_intake_mission_and_evidence_baseline() -> None:
    mission_drift = innovation_record()
    mission_drift["wave"]["assignments"][0]["mission_link"] = "Unrelated objective"
    with pytest.raises(gate.GateError, match="mission link differs from intake"):
        gate.validate_record(mission_drift, "merge")

    baseline_drift = innovation_record()
    baseline_drift["wave"]["packets"][0]["evidence_baseline"] = "unregistered-baseline"
    with pytest.raises(gate.GateError, match="evidence baseline changed"):
        gate.validate_record(baseline_drift, "merge")

    family_drift = innovation_record()
    family_drift["families"][0]["evidence_baseline"] = "unregistered-baseline"
    with pytest.raises(gate.GateError, match="approach-family evidence baseline differs"):
        gate.validate_record(family_drift, "merge")

    claim_drift = innovation_record()
    claim_drift["wave"]["assignments"][0]["exact_claim"] = "A different claim"
    with pytest.raises(gate.GateError, match="exact claim differs"):
        gate.validate_record(claim_drift, "merge")


def test_critic_packet_is_terminal_and_bound_to_its_source_target() -> None:
    wrong_target = innovation_record()
    wrong_target["critic_packets"][0]["target_identity"] = "family-duration"
    with pytest.raises(gate.GateError, match="target identity differs"):
        gate.validate_record(wrong_target, "merge")

    working = innovation_record()
    working["critic_packets"][0]["status"] = "working"
    with pytest.raises(gate.GateError, match="status must be terminal"):
        gate.validate_record(working, "merge")

    disagreement = innovation_record()
    disagreement["critic_packets"].append(
        {
            "critic_assignment_id": "critic-identity-2",
            "packet_kind": "CRITIC_ASSESSMENT_PACKET",
            "status": "terminal",
            "claim_id": "claim-identity",
            "target_identity": "family-identity",
            "source_packet_ids": ["direction-a"],
            "disposition": "weakened",
            "correction": "The claim may hold only with stable identity issuance.",
            "checklist_results": ["replacement ambiguity remains"],
        }
    )
    disagreement["families"][0]["critic_status"] = "conflicting"
    assert gate.validate_record(disagreement, "merge")["critics"] == 2

    invented_status = innovation_record()
    invented_status["families"][1]["critic_status"] = "unresolved"
    with pytest.raises(gate.GateError, match="actual Critic packet set"):
        gate.validate_record(invented_status, "merge")


def test_direction_packet_requires_a_concrete_research_output() -> None:
    record = innovation_record()
    record["wave"]["packets"][0]["concrete_outputs"] = []
    with pytest.raises(gate.GateError, match="no concrete output"):
        gate.validate_record(record, "merge")

    unregistered = innovation_record()
    unregistered["families"][0]["innovator_packet_ids"] = []
    with pytest.raises(gate.GateError, match="not registered to its approach family"):
        gate.validate_record(unregistered, "merge")


def test_blocked_route_reopening_requires_new_mechanism_and_user_confirmation() -> None:
    record = innovation_record()
    result = gate.validate_record(record, "additional-wave")
    assert result["mode"] == "scientific_innovation"

    generic = innovation_record()
    generic["additional_wave_admission"]["basis"] = "underexplored_family"
    with pytest.raises(gate.GateError, match="blocked family lacks"):
        gate.validate_record(generic, "additional-wave")

    unconfirmed = innovation_record()
    unconfirmed["additional_wave_admission"]["user_confirmation"] = ""
    with pytest.raises(gate.GateError, match="user_confirmation"):
        gate.validate_record(unconfirmed, "additional-wave")

    stale_confirmation = innovation_record()
    stale_confirmation["additional_wave_admission"]["stop_condition"] = "A changed stop condition."
    with pytest.raises(gate.GateError, match="admission fingerprint mismatch"):
        gate.validate_record(stale_confirmation, "additional-wave")

    missing_terminal_identity = innovation_record()
    missing_terminal_identity["additional_wave_admission"]["prior_terminal_packet_ids"].pop()
    with pytest.raises(gate.GateError, match="prior terminal packet set mismatch"):
        gate.validate_record(missing_terminal_identity, "additional-wave")


def test_exact_critic_correction_must_propagate_to_synthesis() -> None:
    accepted = gate.validate_record(innovation_record(), "synthesis")
    assert accepted["critics"] == 1

    drifted = innovation_record()
    drifted["synthesis"]["claims"][0]["correction"] = "A softened paraphrase."
    with pytest.raises(gate.GateError, match="changes exact Critic correction"):
        gate.validate_record(drifted, "synthesis")


def test_record_loader_is_confined_to_local_research(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    local = repo / "local_research"
    local.mkdir(parents=True)
    inside = local / "record.json"
    inside.write_text(json.dumps(evidence_record()), encoding="utf-8")
    assert gate.load_record(inside, repo)["document_kind"] == "independent_research_record_v1"

    outside = repo / "outside.json"
    outside.write_text(json.dumps(evidence_record()), encoding="utf-8")
    with pytest.raises(gate.GateError, match="outside the registered local_research"):
        gate.load_record(outside, repo)
