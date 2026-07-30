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


def methodology() -> dict[str, object]:
    return {
        "scientific_object": {
            "stochastic_game": "partially observed stochastic game",
            "objective": "cooperative discounted return",
            "temporal_abstraction": "primitive and membership event clocks",
        },
        "information_contract": {
            "observations": "local observation plus authoritative membership mask",
            "authoritative_membership": "environment-owned",
            "symmetry_assumptions": "entity permutation equivariance",
        },
        "scope": {
            "target_population": "variable-team cooperative tasks",
            "source_boundary": "frozen evidence baseline",
            "partner_policy_population": "frozen and held-out partner profiles",
        },
        "membership_nonstationarity": {"sources": ["join", "leave"], "consequences": ["policy drift"]},
        "identity_ownership_map": {
            "persistent_entity": "environment identity",
            "slot": "ephemeral observation slot",
            "policy_identity": "shared actor",
            "role": "task role",
            "skill": "temporally extended action",
            "capability_type": "environment type",
            "recurrent_state_owner": "persistent entity",
        },
        "temporal_abstraction": {
            "clock_map": ["primitive", "membership", "credit"],
            "duration_distribution": "environment supplied",
            "termination_rule": "skill completion or interruption",
            "interruption_and_censoring": "recorded separately",
            "credit_rule": "duration-aware discounted return",
        },
        "policy_process": {
            "frozen": ["partner policies during discriminator"],
            "adapting": ["focal policy during training"],
            "jointly_trained": ["shared actor population"],
            "replaced": ["held-out partner swap"],
            "sampled": ["replicate-level partner profile"],
        },
        "solution_concept": "cooperative return under held-out cross-play",
        "strategic_dependence": {
            "identity_and_symmetry_claim": "equivariant under entity permutation",
            "unilateral_intervention": "partner-policy swap",
            "held_out_cross_play": "held-out partner profile",
        },
        "primary_estimand": "paired utility contrast under roster intervention",
        "sampling_hierarchy": {
            "top_level_independent_unit": "replicate",
            "lower_levels": ["roster stream", "episode"],
        },
        "identification_assumptions": ["paired exogenous roster stream"],
        "uncertainty_plan": {
            "method": "paired replicate interval",
            "independent_unit": "replicate",
        },
        "simplest_competing_explanation": "information-matched recurrent null",
        "intervention_regime": {"membership": "controlled"},
        "comparator_regime": {"capacity": "matched"},
        "equivalence_analysis": {"tests": ["identity permutation"]},
        "replacement_ledger": {
            "delete": ["slot-owned recurrent state"],
            "retain": ["shared actor"],
            "add": ["identity-keyed lifecycle state"],
        },
        "mathematical_defect": "slot reuse aliases replacement and rejoin",
        "predictions": {
            "intervention": "identity reset changes only replacement traces",
            "natural_execution": "survivor state remains continuous",
            "held_out_transport": "cross-play retains the separation",
        },
        "negative_controls": ["visibility-only mask change"],
        "resource_bounds": {"evidence_search": "O(HK)"},
        "complexity_bound": {
            "evidence_search": "O(HK)",
            "deployment": "O(Nk)",
        },
        "approximation_assumptions": ["bounded active neighborhood"],
        "smallest_claim": "identity ownership separates replacement from rejoin",
        "smallest_supported_propositions": ["state ownership is reconstructible"],
        "smallest_refuted_propositions": ["slot identity is sufficient"],
        "strongest_counterexample": "environment exposes no persistent identity",
        "smallest_discriminating_observation": "one join-leave-rejoin trace",
        "failure_boundaries": ["identity unavailable"],
        "provenance": {
            "baseline": "evidence-review-v1",
            "packet": "direction-1",
            "cross_pollination_edges": ["identity@v1 <- evidence-review-v1"],
        },
        "stop_condition": "Stop when no bounded observation can change the claim.",
    }


def direction_packet(
    *,
    packet_id: str = "direction-1",
    assignment_id: str = "innovator-1",
    cohort_id: str = "cohort-1",
    conjecture_key: str = "identity@v1",
    parents: list[str] | None = None,
    purpose: str = "develop",
    input_brief: str | None = None,
    exact_claim: str = "Persistent identity separates replacement from rejoin.",
) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "packet_kind": "RESEARCH_DIRECTION_PACKET",
        "status": "terminal",
        "campaign_id": "campaign-1",
        "cohort_id": cohort_id,
        "assignment_id": assignment_id,
        "family_id": "family-identity",
        "conjecture_key": conjecture_key,
        "parent_conjecture_keys": parents or [],
        "claim_id": f"claim-{conjecture_key}",
        "purpose": purpose,
        "core_mechanism": "identity-keyed lifecycle state",
        "exact_claim": exact_claim,
        "mission_link": "Variable team membership and skill lifetime",
        "evidence_baseline": "evidence-review-v1",
        "input_collaboration_brief_id": input_brief,
        "campaign_scope": {"research_question": "variable membership lifecycle"},
        "common_scientific_objects": {
            "game": "partially observed stochastic game",
            "membership_process": "join-leave-rejoin",
        },
        "semantic_trap_results": [
            {"trap": "visibility is not membership", "disposition": "pass"}
        ],
        "assumptions": ["authoritative identity is available"],
        "derivation_or_construction": "Factor lifecycle state by persistent entity identity.",
        "novelty_delta": "Separates identity continuity from slot continuity.",
        "evidence_dependencies": [
            {"evidence_id": "evidence-review-v1", "verification_state": "verified"}
        ],
        "methodology": methodology(),
        "concrete_outputs": [
            {
                "kind": "counterexample",
                "content": "Slot reuse aliases replacement and rejoin.",
            }
        ],
        "proposed_conjecture_patch": "Condition the claim on authoritative identity.",
        "unresolved_items": ["Whether all target environments expose identity."],
    }


def innovator_assignment(
    *,
    assignment_id: str = "innovator-1",
    cohort_id: str = "cohort-1",
    conjecture_key: str = "identity@v1",
    parents: list[str] | None = None,
    purpose: str = "develop",
    input_brief: str | None = None,
    exact_claim: str = "Persistent identity separates replacement from rejoin.",
) -> dict[str, object]:
    return {
        "assignment_id": assignment_id,
        "role": "innovator",
        "campaign_id": "campaign-1",
        "cohort_id": cohort_id,
        "family_id": "family-identity",
        "conjecture_key": conjecture_key,
        "parent_conjecture_keys": parents or [],
        "claim_id": f"claim-{conjecture_key}",
        "purpose": purpose,
        "favored_family_visibility": (
            "withheld" if cohort_id == "cohort-1" else "collaboration_brief_only"
        ),
        "core_mechanism": "identity-keyed lifecycle state",
        "exact_claim": exact_claim,
        "mission_link": "Variable team membership and skill lifetime",
        "evidence_baseline": "evidence-review-v1",
        "methodology_reference": "research-methodology.md",
        "input_collaboration_brief_id": input_brief,
        "campaign_scope": {"research_question": "variable membership lifecycle"},
        "common_scientific_objects": {
            "game": "partially observed stochastic game",
            "membership_process": "join-leave-rejoin",
        },
        "semantic_traps": ["visibility is not membership"],
    }


def correction() -> dict[str, str]:
    return {
        "correction_id": "correction-1",
        "target_record_id": "identity@v1",
        "target_field": "exact_claim",
        "kind": "scope_weakening",
        "exact_text": "Condition the claim on authoritative identity.",
        "basis": "No-identity counterexample.",
        "disposition_impact": "supported becomes weakened",
    }


def innovation_record() -> dict[str, object]:
    record: dict[str, object] = {
        "document_kind": "independent_research_campaign_v2",
        "intake": {
            "mode": "scientific_innovation",
            "question": "How should lifecycle state survive variable membership?",
            "mission_link": "Variable team membership and skill lifetime",
            "named_sources": ["evidence-review-v1"],
            "allowed_source_ids": ["MARL-0001", "MARL-0002"],
            "source_boundary": "Frozen evidence baseline plus named collaboration briefs",
            "evidence_baseline": "evidence-review-v1",
            "scope": {"research_question": "variable membership lifecycle"},
            "common_scientific_objects": {
                "game": "partially observed stochastic game",
                "membership_process": "join-leave-rejoin",
            },
            "exclusions": ["formal workflow", "compute", "implementation"],
            "completion_condition": "Return audited conjectures or exact residual gaps.",
            "semantic_traps": ["visibility is not membership"],
        },
        "campaign": {
            "campaign_id": "campaign-1",
            "user_authorization_id": "user-confirmed-campaign-v1",
            "max_cohorts": 3,
            "total_budgets": {"scout": 1, "innovator": 3, "critic": 2},
            "stop_conditions": [
                "no disposition-changing target",
                "role budget exhausted",
            ],
            "authorization_fingerprint": "",
        },
        "families": [
            {
                "family_id": "family-identity",
                "core_mechanism": "identity-keyed lifecycle state",
                "current_conjecture_key": "identity@v1",
                "strongest_support": "Membership churn requires ownership semantics.",
                "strongest_counterexample": "Environment exposes no persistent identity.",
                "current_gap": "Identity availability boundary.",
                "status": "live",
                "reopen_condition": "New identity invariant or exact correction.",
                "packet_ids": ["direction-1"],
                "critic_status": "weakened",
            }
        ],
        "conjectures": [
            {
                "conjecture_key": "identity@v1",
                "conjecture_id": "identity",
                "version": 1,
                "family_id": "family-identity",
                "parent_conjecture_keys": [],
                "exact_claim": "Persistent identity separates replacement from rejoin.",
                "source_packet_ids": ["direction-1"],
            }
        ],
        "cohorts": [
            {
                "cohort_id": "cohort-1",
                "campaign_id": "campaign-1",
                "index": 1,
                "input_collaboration_brief_id": None,
                "originating_admission": None,
                "originating_admission_fingerprint": None,
                "assignments": [innovator_assignment()],
                "packets": [direction_packet()],
                "terminal_failures": [],
                "critic_assignments": [
                    {
                        "critic_assignment_id": "critic-1",
                        "campaign_id": "campaign-1",
                        "cohort_id": "cohort-1",
                        "target_identity": "family-identity",
                        "conjecture_key": "identity@v1",
                        "claim_id": "claim-identity@v1",
                        "source_packet_ids": ["direction-1"],
                        "checklist": ["identity ownership"],
                        "methodology_reference": "research-methodology.md",
                    }
                ],
                "critic_packets": [
                    {
                        "critic_assignment_id": "critic-1",
                        "packet_kind": "CRITIC_ASSESSMENT_PACKET",
                        "status": "terminal",
                        "campaign_id": "campaign-1",
                        "cohort_id": "cohort-1",
                        "target_identity": "family-identity",
                        "conjecture_key": "identity@v1",
                        "claim_id": "claim-identity@v1",
                        "source_packet_ids": ["direction-1"],
                        "checklist_results": [
                            {"check": "identity ownership", "disposition": "weaken"}
                        ],
                        "strongest_counterexample": "No persistent identity.",
                        "alternate_explanation": "Capacity rather than lifecycle.",
                        "disposition": "weakened",
                        "smallest_discriminating_observation": "Identity permutation.",
                        "corrections": [correction()],
                    }
                ],
                "critic_failures": [],
                "family_dispositions": [
                    {"family_id": "family-identity", "status": "live"}
                ],
            }
        ],
        "collaboration_briefs": [
            {
                "brief_id": "brief-1",
                "after_cohort_id": "cohort-1",
                "source_packet_ids": ["direction-1"],
                "corrections": [correction()],
                "retained_lemmas": ["Identity ownership is a separate object."],
                "counterexamples": ["No persistent identity."],
                "gaps": ["Availability boundary."],
                "transfer_candidates": ["Identity permutation control."],
                "permitted_parent_conjecture_keys": ["identity@v1"],
            }
        ],
        "next_cohort_admission": {
            "prior_cohort_id": "cohort-1",
            "next_cohort_id": "cohort-2",
            "prior_terminal_assignment_ids": ["innovator-1"],
            "prior_terminal_packet_ids": ["direction-1"],
            "prior_correction_ids": ["correction-1"],
            "prior_family_dispositions": [
                {"family_id": "family-identity", "status": "live"}
            ],
            "input_collaboration_brief_id": "brief-1",
            "target_family_ids": ["family-identity"],
            "parent_conjecture_keys": ["identity@v1"],
            "purpose": "refine",
            "basis": "critic_correction",
            "novelty_statement": "Apply the exact identity-availability correction.",
            "expected_disposition_change": "Replace the broad claim with a scoped claim.",
            "planned_assignments": [
                {
                    "assignment_id": "innovator-2",
                    "role": "innovator",
                    "claim_id": "claim-identity@v2",
                    "semantic_traps": ["visibility is not membership"],
                    "family_id": "family-identity",
                    "conjecture_key": "identity@v2",
                    "parent_conjecture_keys": ["identity@v1"],
                    "purpose": "refine",
                    "core_mechanism": "identity-keyed lifecycle state",
                    "exact_claim": "Condition the claim on authoritative identity.",
                }
            ],
            "planned_critic_count": 0,
            "stop_condition": "Stop if the corrected claim remains non-identifiable.",
            "admission_fingerprint": "",
        },
        "synthesis": {
            "advisory_only": True,
            "automatic_formal_promotion": False,
            "completion_reason": "Bounded campaign synthesis.",
            "family_dispositions": [
                {"family_id": "family-identity", "status": "live"}
            ],
            "cohort_disposition_history": [
                {
                    "cohort_id": "cohort-1",
                    "family_dispositions": [
                        {"family_id": "family-identity", "status": "live"}
                    ],
                }
            ],
            "conjecture_version_map": ["identity@v1"],
            "collaboration_brief_ids": ["brief-1"],
            "critic_correction_propagation": [
                {
                    **correction(),
                    "outcome": "unresolved",
                    "resolution_reason": "No successor cohort has completed yet.",
                }
            ],
        },
    }
    record["campaign"]["authorization_fingerprint"] = gate.campaign_fingerprint(record)
    record["next_cohort_admission"]["admission_fingerprint"] = gate.next_cohort_fingerprint(record)
    return record


def two_cohort_record() -> dict[str, object]:
    record = innovation_record()
    admission = copy.deepcopy(record["next_cohort_admission"])
    corrected_claim = "Condition the claim on authoritative identity."
    record["conjectures"].append(
        {
            "conjecture_key": "identity@v2",
            "conjecture_id": "identity",
            "version": 2,
            "family_id": "family-identity",
            "parent_conjecture_keys": ["identity@v1"],
            "exact_claim": corrected_claim,
            "source_packet_ids": ["direction-2"],
        }
    )
    record["families"][0]["current_conjecture_key"] = "identity@v2"
    record["families"][0]["packet_ids"] = ["direction-1", "direction-2"]
    record["cohorts"].append(
        {
            "cohort_id": "cohort-2",
            "campaign_id": "campaign-1",
            "index": 2,
            "input_collaboration_brief_id": "brief-1",
            "originating_admission": admission,
            "originating_admission_fingerprint": admission["admission_fingerprint"],
            "assignments": [
                innovator_assignment(
                    assignment_id="innovator-2",
                    cohort_id="cohort-2",
                    conjecture_key="identity@v2",
                    parents=["identity@v1"],
                    purpose="refine",
                    input_brief="brief-1",
                    exact_claim=corrected_claim,
                )
            ],
            "packets": [
                direction_packet(
                    packet_id="direction-2",
                    assignment_id="innovator-2",
                    cohort_id="cohort-2",
                    conjecture_key="identity@v2",
                    parents=["identity@v1"],
                    purpose="refine",
                    input_brief="brief-1",
                    exact_claim=corrected_claim,
                )
            ],
            "terminal_failures": [],
            "critic_assignments": [],
            "critic_packets": [],
            "critic_failures": [],
            "family_dispositions": [
                {"family_id": "family-identity", "status": "live"}
            ],
        }
    )
    record["collaboration_briefs"].append(
        {
            "brief_id": "brief-2",
            "after_cohort_id": "cohort-2",
            "source_packet_ids": ["direction-2"],
            "corrections": [],
            "retained_lemmas": ["Scoped identity claim."],
            "counterexamples": ["Identity unavailable."],
            "gaps": ["External validity."],
            "transfer_candidates": ["Identity permutation control."],
            "permitted_parent_conjecture_keys": ["identity@v2"],
        }
    )
    record.pop("next_cohort_admission")
    record["synthesis"]["conjecture_version_map"] = ["identity@v1", "identity@v2"]
    record["synthesis"]["collaboration_brief_ids"] = ["brief-1", "brief-2"]
    record["synthesis"]["cohort_disposition_history"] = [
        {
            "cohort_id": "cohort-1",
            "family_dispositions": [
                {"family_id": "family-identity", "status": "live"}
            ],
        },
        {
            "cohort_id": "cohort-2",
            "family_dispositions": [
                {"family_id": "family-identity", "status": "live"}
            ],
        },
    ]
    record["synthesis"]["critic_correction_propagation"] = [
        {
            **correction(),
            "outcome": "applied",
            "successor_record_id": "identity@v2",
        }
    ]
    return record


def three_cohort_record() -> dict[str, object]:
    record = two_cohort_record()
    future_claim = "A future cohort introduces a distinct lifecycle conjecture."
    record["conjectures"].append(
        {
            "conjecture_key": "future@v1",
            "conjecture_id": "future",
            "version": 1,
            "family_id": "family-identity",
            "parent_conjecture_keys": [],
            "exact_claim": future_claim,
            "source_packet_ids": ["direction-3"],
        }
    )
    record["families"][0]["current_conjecture_key"] = "future@v1"
    record["families"][0]["packet_ids"].append("direction-3")
    admission = {
        "prior_cohort_id": "cohort-2",
        "next_cohort_id": "cohort-3",
        "prior_terminal_assignment_ids": ["innovator-2"],
        "prior_terminal_packet_ids": ["direction-2"],
        "prior_correction_ids": [],
        "prior_family_dispositions": [
            {"family_id": "family-identity", "status": "live"}
        ],
        "input_collaboration_brief_id": "brief-2",
        "target_family_ids": ["family-identity"],
        "parent_conjecture_keys": [],
        "purpose": "develop",
        "basis": "new_mechanism",
        "novelty_statement": "Introduce a separate bounded lifecycle mechanism.",
        "expected_disposition_change": "Add a distinct testable conjecture.",
        "planned_assignments": [
            {
                "assignment_id": "innovator-3",
                "role": "innovator",
                "claim_id": "claim-future@v1",
                "semantic_traps": ["visibility is not membership"],
                "family_id": "family-identity",
                "conjecture_key": "future@v1",
                "parent_conjecture_keys": [],
                "purpose": "develop",
                "core_mechanism": "identity-keyed lifecycle state",
                "exact_claim": future_claim,
            }
        ],
        "planned_critic_count": 0,
        "stop_condition": "Stop after the distinct mechanism is stated.",
        "admission_fingerprint": "",
    }
    admission["admission_fingerprint"] = gate._admission_fingerprint(record, admission)
    record["cohorts"].append(
        {
            "cohort_id": "cohort-3",
            "campaign_id": "campaign-1",
            "index": 3,
            "input_collaboration_brief_id": "brief-2",
            "originating_admission": admission,
            "originating_admission_fingerprint": admission["admission_fingerprint"],
            "assignments": [
                innovator_assignment(
                    assignment_id="innovator-3",
                    cohort_id="cohort-3",
                    conjecture_key="future@v1",
                    parents=[],
                    purpose="develop",
                    input_brief="brief-2",
                    exact_claim=future_claim,
                )
            ],
            "packets": [
                direction_packet(
                    packet_id="direction-3",
                    assignment_id="innovator-3",
                    cohort_id="cohort-3",
                    conjecture_key="future@v1",
                    parents=[],
                    purpose="develop",
                    input_brief="brief-2",
                    exact_claim=future_claim,
                )
            ],
            "terminal_failures": [],
            "critic_assignments": [],
            "critic_packets": [],
            "critic_failures": [],
            "family_dispositions": [
                {"family_id": "family-identity", "status": "live"}
            ],
        }
    )
    record["collaboration_briefs"].append(
        {
            "brief_id": "brief-3",
            "after_cohort_id": "cohort-3",
            "source_packet_ids": ["direction-3"],
            "corrections": [],
            "retained_lemmas": ["Distinct lifecycle mechanism."],
            "counterexamples": ["No persistent identity."],
            "gaps": ["Future mechanism boundary."],
            "transfer_candidates": ["Lifecycle control."],
            "permitted_parent_conjecture_keys": ["future@v1"],
        }
    )
    record["synthesis"]["conjecture_version_map"].append("future@v1")
    record["synthesis"]["collaboration_brief_ids"].append("brief-3")
    record["synthesis"]["cohort_disposition_history"].append(
        {
            "cohort_id": "cohort-3",
            "family_dispositions": [
                {"family_id": "family-identity", "status": "live"}
            ],
        }
    )
    return record


def evidence_packet(
    packet_id: str,
    assignment_id: str,
    source_id: str,
    axis: str,
) -> dict[str, object]:
    path = f"C:/MyLib/json/{source_id}.json"
    claim_id = f"claim-{axis}"
    return {
        "packet_id": packet_id,
        "packet_kind": "SCOUT_EVIDENCE_PACKET",
        "status": "terminal",
        "cohort_id": "evidence-cohort-1",
        "assignment_id": assignment_id,
        "claim_id": claim_id,
        "evidence_axis_id": axis,
        "input_collaboration_brief_id": None,
        "source_ids": [source_id],
        "semantic_trap_results": [
            {"trap": f"trap-{axis}", "disposition": "pass"}
        ],
        "search_terms": [axis],
        "candidates": [source_id],
        "exclusions": [],
        "coverage_limit": 1,
        "evidence_rows": [
            {
                "claim_id": claim_id,
                "claim": f"Evidence for {axis}.",
                "source_identity": source_id,
                "title": f"Paper {source_id}",
                "evidence_path": path,
                "evidence_type": "json",
                "locator": "p1/e1",
                "provenance": "structured-json",
                "claim_kind": "paper_claim",
                "verification_state": "verified",
                "confidence": 0.9,
            }
        ],
        "supporting_evidence": ["p1/e1"],
        "conflicting_evidence": [],
        "boundary_evidence": [],
        "testable_hypotheses": [],
        "unresolved_facts": [],
        "mechanism_primitives": [],
        "transfer_boundaries": [],
        "cross_source_questions": [],
    }


def evidence_assignment(
    assignment_id: str,
    source_id: str,
    axis: str,
) -> dict[str, object]:
    return {
        "assignment_id": assignment_id,
        "role": "scout",
        "cohort_id": "evidence-cohort-1",
        "claim_id": f"claim-{axis}",
        "evidence_axis_id": axis,
        "source_ids": [source_id],
        "source_bindings": [
            {
                "source_identity": source_id,
                "evidence_type": "json",
                "evidence_path": f"C:/MyLib/json/{source_id}.json",
            }
        ],
        "input_collaboration_brief_id": None,
        "semantic_traps": [f"trap-{axis}"],
    }


def evidence_record() -> dict[str, object]:
    return {
        "document_kind": "independent_research_campaign_v2",
        "intake": {
            "mode": "evidence_review",
            "question": "What do the named sources establish?",
            "mission_link": "Variable team membership and skill lifetime",
            "named_sources": ["MARL-0001", "MARL-0002"],
            "exclusions": ["formal workflow"],
            "completion_condition": "Return bounded evidence report.",
            "semantic_traps": ["membership semantics"],
        },
        "campaign": None,
        "families": [],
        "conjectures": [],
        "cohorts": [
            {
                "cohort_id": "evidence-cohort-1",
                "index": 1,
                "input_collaboration_brief_id": None,
                "originating_admission": None,
                "originating_admission_fingerprint": None,
                "assignments": [
                    evidence_assignment("scout-1", "MARL-0001", "dynamic"),
                    evidence_assignment("scout-2", "MARL-0002", "duration"),
                ],
                "packets": [
                    evidence_packet("packet-1", "scout-1", "MARL-0001", "dynamic"),
                    evidence_packet("packet-2", "scout-2", "MARL-0002", "duration"),
                ],
                "terminal_failures": [],
                "critic_assignments": [],
                "critic_packets": [],
                "critic_failures": [],
                "family_dispositions": [],
            }
        ],
        "collaboration_briefs": [],
        "synthesis": {
            "advisory_only": True,
            "automatic_formal_promotion": False,
            "completion_reason": "Evidence report complete.",
            "critic_correction_propagation": [],
        },
    }


@pytest.mark.parametrize("phase", ["intake", "merge", "next-cohort", "synthesis"])
def test_valid_innovation_campaign_passes_all_phases(phase: str) -> None:
    gate.validate_record(innovation_record(), phase)


@pytest.mark.parametrize("phase", ["intake", "merge", "synthesis"])
def test_valid_evidence_review_passes_bounded_phases(phase: str) -> None:
    gate.validate_record(evidence_record(), phase)


@pytest.mark.parametrize("phase", ["merge", "synthesis"])
def test_completed_second_cohort_is_bound_to_its_admission(phase: str) -> None:
    gate.validate_record(two_cohort_record(), phase)


def test_campaign_authorization_binds_frozen_total_budget() -> None:
    record = innovation_record()
    record["campaign"]["total_budgets"]["innovator"] = 4
    with pytest.raises(gate.GateError, match="authorization fingerprint"):
        gate.validate_record(record, "intake")


@pytest.mark.parametrize(
    "field",
    [
        "question",
        "mission_link",
        "named_sources",
        "allowed_source_ids",
        "source_boundary",
        "evidence_baseline",
        "scope",
        "common_scientific_objects",
        "exclusions",
        "completion_condition",
        "semantic_traps",
        "max_cohorts",
        "stop_conditions",
    ],
)
def test_campaign_authorization_binds_every_declared_boundary(field: str) -> None:
    record = innovation_record()
    if field == "max_cohorts":
        record["campaign"][field] += 1
    elif field == "stop_conditions":
        record["campaign"][field].append("new stop")
    elif field in {
        "named_sources",
        "allowed_source_ids",
        "exclusions",
        "semantic_traps",
    }:
        record["intake"][field].append("changed boundary")
    elif field in {"scope", "common_scientific_objects"}:
        record["intake"][field]["unconfirmed"] = "changed"
    else:
        record["intake"][field] += " changed"
    with pytest.raises(gate.GateError, match="authorization fingerprint"):
        gate.validate_record(record, "intake")


def test_innovation_requires_an_explicit_allowed_source_set() -> None:
    record = innovation_record()
    del record["intake"]["allowed_source_ids"]
    with pytest.raises(gate.GateError, match="intake.allowed_source_ids"):
        gate.validate_record(record, "intake")


def test_explicit_empty_allowed_source_set_has_its_own_authorization_identity() -> None:
    record = innovation_record()
    original = record["campaign"]["authorization_fingerprint"]
    record["intake"]["allowed_source_ids"] = []
    replacement = gate.campaign_fingerprint(record)
    assert replacement != original
    record["campaign"]["authorization_fingerprint"] = replacement
    gate.validate_record(record, "intake")


def test_first_cohort_rejects_peer_visibility() -> None:
    record = innovation_record()
    record["cohorts"][0]["assignments"][0]["favored_family_visibility"] = "collaboration_brief_only"
    with pytest.raises(gate.GateError, match="independence shielding"):
        gate.validate_record(record, "merge")


def test_innovator_assignment_is_bound_to_campaign_mission_and_baseline() -> None:
    record = innovation_record()
    record["cohorts"][0]["assignments"][0]["evidence_baseline"] = "other-baseline"
    with pytest.raises(gate.GateError, match="evidence baseline differs from intake"):
        gate.validate_record(record, "merge")


def test_first_cohort_cannot_seed_the_same_family_twice() -> None:
    record = innovation_record()
    duplicate = copy.deepcopy(record["cohorts"][0]["assignments"][0])
    duplicate["assignment_id"] = "innovator-duplicate"
    record["cohorts"][0]["assignments"].append(duplicate)
    with pytest.raises(gate.GateError, match="one family more than once"):
        gate.validate_record(record, "merge")


def test_merge_barrier_rejects_missing_terminal_packet() -> None:
    record = innovation_record()
    record["cohorts"][0]["packets"] = []
    record["families"][0]["packet_ids"] = []
    record["conjectures"][0]["source_packet_ids"] = []
    with pytest.raises(gate.GateError, match="merge barrier"):
        gate.validate_record(record, "merge")


def test_critic_merge_barrier_rejects_missing_terminal_result() -> None:
    record = innovation_record()
    record["cohorts"][0]["critic_packets"] = []
    with pytest.raises(gate.GateError, match="Critic merge barrier"):
        gate.validate_record(record, "merge")


def test_terminal_critic_failure_closes_barrier_and_consumes_budget() -> None:
    record = innovation_record()
    cohort = record["cohorts"][0]
    cohort["critic_packets"] = []
    cohort["critic_failures"] = [
        {
            "assignment_id": "critic-1",
            "failure_kind": "OPERATIONAL_FAILURE",
            "status": "terminal",
            "failure_signature": "critic-source-unreadable",
            "unchanged_retry_count": 1,
            "scientific_output": False,
        }
    ]
    record["families"][0]["critic_status"] = "operational_failure"
    record["collaboration_briefs"][0]["corrections"] = []
    record["next_cohort_admission"]["prior_correction_ids"] = []
    record["next_cohort_admission"]["basis"] = "new_invariant"
    record["next_cohort_admission"]["admission_fingerprint"] = gate.next_cohort_fingerprint(record)
    record["synthesis"]["critic_correction_propagation"] = []
    gate.validate_record(record, "merge")

    record["campaign"]["total_budgets"]["critic"] = 0
    record["campaign"]["authorization_fingerprint"] = gate.campaign_fingerprint(record)
    with pytest.raises(gate.GateError, match="critic budget exceeded"):
        gate.validate_record(record, "merge")


def test_critic_packet_must_cover_exact_assigned_checklist() -> None:
    record = innovation_record()
    record["cohorts"][0]["critic_packets"][0]["checklist_results"][0][
        "check"
    ] = "different check"
    with pytest.raises(gate.GateError, match="exact assigned checklist"):
        gate.validate_record(record, "merge")


def test_critic_packet_is_bound_to_campaign_identity() -> None:
    record = innovation_record()
    record["cohorts"][0]["critic_packets"][0]["campaign_id"] = "other-campaign"
    with pytest.raises(gate.GateError, match="Critic campaign identity mismatch"):
        gate.validate_record(record, "merge")


def test_correction_target_record_and_field_must_exist() -> None:
    record = innovation_record()
    record["cohorts"][0]["critic_packets"][0]["corrections"][0][
        "target_field"
    ] = "missing_field"
    with pytest.raises(gate.GateError, match="target field does not exist"):
        gate.validate_record(record, "merge")


def test_terminal_operational_failure_has_no_scientific_payload() -> None:
    record = evidence_record()
    cohort = record["cohorts"][0]
    cohort["packets"] = [cohort["packets"][0]]
    cohort["terminal_failures"] = [
        {
            "assignment_id": "scout-2",
            "failure_kind": "OPERATIONAL_FAILURE",
            "status": "terminal",
            "failure_signature": "source-unreadable",
            "unchanged_retry_count": 1,
            "scientific_output": False,
        }
    ]
    gate.validate_record(record, "merge")
    cohort["terminal_failures"][0]["claim"] = "unsupported scientific payload"
    with pytest.raises(gate.GateError, match="unsupported fields"):
        gate.validate_record(record, "merge")


def test_missing_methodology_field_is_rejected() -> None:
    record = innovation_record()
    del record["cohorts"][0]["packets"][0]["methodology"]["primary_estimand"]
    with pytest.raises(gate.GateError, match="methodology fields missing"):
        gate.validate_record(record, "merge")


def test_missing_nested_clock_contract_is_rejected() -> None:
    record = innovation_record()
    del record["cohorts"][0]["packets"][0]["methodology"]["temporal_abstraction"][
        "credit_rule"
    ]
    with pytest.raises(gate.GateError, match="temporal_abstraction fields missing"):
        gate.validate_record(record, "merge")


@pytest.mark.parametrize(
    ("section", "field"),
    [
        ("scope", "partner_policy_population"),
        ("provenance", "cross_pollination_edges"),
    ],
)
def test_missing_required_methodology_nested_contract_is_rejected(
    section: str,
    field: str,
) -> None:
    record = innovation_record()
    del record["cohorts"][0]["packets"][0]["methodology"][section][field]
    with pytest.raises(gate.GateError, match=rf"methodology\.{section} fields missing"):
        gate.validate_record(record, "merge")


def test_missing_methodology_stop_condition_is_rejected() -> None:
    record = innovation_record()
    del record["cohorts"][0]["packets"][0]["methodology"]["stop_condition"]
    with pytest.raises(gate.GateError, match="methodology fields missing"):
        gate.validate_record(record, "merge")


def test_blank_methodology_list_item_is_rejected() -> None:
    record = innovation_record()
    record["cohorts"][0]["packets"][0]["methodology"]["negative_controls"] = [""]
    with pytest.raises(gate.GateError, match=r"negative_controls\[0\]"):
        gate.validate_record(record, "merge")


def test_incomplete_module_replacement_ledger_is_rejected() -> None:
    record = innovation_record()
    del record["cohorts"][0]["packets"][0]["methodology"]["replacement_ledger"]["delete"]
    with pytest.raises(gate.GateError, match="replacement ledger"):
        gate.validate_record(record, "merge")


def test_next_cohort_requires_exact_latest_collaboration_brief() -> None:
    record = innovation_record()
    record["next_cohort_admission"]["input_collaboration_brief_id"] = "missing-brief"
    record["next_cohort_admission"]["admission_fingerprint"] = gate.next_cohort_fingerprint(record)
    with pytest.raises(gate.GateError, match="unknown collaboration brief"):
        gate.validate_record(record, "next-cohort")


def test_planned_scout_cannot_expand_the_campaign_source_set() -> None:
    record = innovation_record()
    record["next_cohort_admission"]["planned_assignments"] = [
        {
            "assignment_id": "scout-next",
            "role": "scout",
            "claim_id": "claim-next-evidence",
            "semantic_traps": ["visibility is not membership"],
            "evidence_axis_id": "identity-availability",
            "source_ids": ["MARL-9999"],
            "source_bindings": [
                {
                    "source_identity": "MARL-9999",
                    "evidence_type": "json",
                    "evidence_path": "C:/MyLib/json/MARL-9999.json",
                }
            ],
        }
    ]
    record["next_cohort_admission"]["admission_fingerprint"] = gate.next_cohort_fingerprint(record)
    with pytest.raises(gate.GateError, match="planned Scout expands"):
        gate.validate_record(record, "next-cohort")


def test_planned_innovator_must_belong_to_an_admission_target() -> None:
    record = innovation_record()
    planned = record["next_cohort_admission"]["planned_assignments"][0]
    planned["family_id"] = "unrelated-family"
    record["next_cohort_admission"]["admission_fingerprint"] = gate.next_cohort_fingerprint(record)
    with pytest.raises(gate.GateError, match="outside the admission targets"):
        gate.validate_record(record, "next-cohort")


def test_planned_prospective_conjecture_requires_a_canonical_next_version() -> None:
    record = innovation_record()
    planned = record["next_cohort_admission"]["planned_assignments"][0]
    planned["conjecture_key"] = "identity@v3"
    record["next_cohort_admission"]["admission_fingerprint"] = gate.next_cohort_fingerprint(record)
    with pytest.raises(gate.GateError, match="next canonical version"):
        gate.validate_record(record, "next-cohort")

    planned["conjecture_key"] = "not-a-versioned-conjecture"
    record["next_cohort_admission"]["admission_fingerprint"] = gate.next_cohort_fingerprint(record)
    with pytest.raises(gate.GateError, match="not a canonical conjecture key"):
        gate.validate_record(record, "next-cohort")


def test_planned_innovators_must_cover_every_admitted_parent() -> None:
    record = innovation_record()
    planned = record["next_cohort_admission"]["planned_assignments"][0]
    planned["parent_conjecture_keys"] = []
    record["next_cohort_admission"]["admission_fingerprint"] = gate.next_cohort_fingerprint(record)
    with pytest.raises(
        gate.GateError,
        match="omits its own immediate predecessor",
    ):
        gate.validate_record(record, "next-cohort")


def test_one_planned_innovator_cannot_carry_another_refinements_predecessor() -> None:
    families = {
        "family-a": {"core_mechanism": "mechanism-a"},
        "family-b": {"core_mechanism": "mechanism-b"},
    }
    conjectures = {
        "a@v1": {
            "conjecture_id": "a",
            "version": 1,
            "family_id": "family-a",
            "parent_conjecture_keys": [],
            "exact_claim": "claim-a-v1",
        },
        "b@v1": {
            "conjecture_id": "b",
            "version": 1,
            "family_id": "family-b",
            "parent_conjecture_keys": [],
            "exact_claim": "claim-b-v1",
        },
    }
    planned = gate._validate_planned_assignments(
        [
            {
                "assignment_id": "refine-a",
                "role": "innovator",
                "claim_id": "claim-a-v2",
                "semantic_traps": ["trap-a"],
                "family_id": "family-a",
                "conjecture_key": "a@v2",
                "parent_conjecture_keys": [],
                "purpose": "refine",
                "core_mechanism": "mechanism-a",
                "exact_claim": "claim-a-v2",
            },
            {
                "assignment_id": "refine-b",
                "role": "innovator",
                "claim_id": "claim-b-v2",
                "semantic_traps": ["trap-b"],
                "family_id": "family-b",
                "conjecture_key": "b@v2",
                "parent_conjecture_keys": ["a@v1", "b@v1"],
                "purpose": "refine",
                "core_mechanism": "mechanism-b",
                "exact_claim": "claim-b-v2",
            },
        ]
    )
    admission = {
        "target_family_ids": ["family-a", "family-b"],
        "parent_conjecture_keys": ["a@v1", "b@v1"],
        "purpose": "refine",
    }
    brief = {"permitted_parent_conjecture_keys": ["a@v1", "b@v1"]}
    with pytest.raises(
        gate.GateError,
        match="omits its own immediate predecessor",
    ):
        gate._validate_admission_plan_context(
            planned,
            {"allowed_source_ids": []},
            families,
            conjectures,
            admission,
            brief,
        )


def test_completed_cohort_rejects_admission_to_assignment_drift() -> None:
    record = two_cohort_record()
    admission = record["cohorts"][1]["originating_admission"]
    admission["planned_assignments"][0]["exact_claim"] = "Drifted claim."
    admission["admission_fingerprint"] = gate._admission_fingerprint(record, admission)
    record["cohorts"][1]["originating_admission_fingerprint"] = admission[
        "admission_fingerprint"
    ]
    with pytest.raises(gate.GateError, match="planned Innovator claim differs"):
        gate.validate_record(record, "merge")


def test_completed_cohort_rejects_a_skipped_conjecture_version() -> None:
    record = json.loads(
        json.dumps(two_cohort_record()).replace("identity@v2", "identity@v3")
    )
    record["conjectures"][1]["version"] = 3
    admission = record["cohorts"][1]["originating_admission"]
    admission["admission_fingerprint"] = gate._admission_fingerprint(record, admission)
    record["cohorts"][1]["originating_admission_fingerprint"] = admission[
        "admission_fingerprint"
    ]
    with pytest.raises(gate.GateError, match="next canonical version"):
        gate.validate_record(record, "merge")


def test_completed_cohort_cannot_use_a_parent_from_a_future_cohort() -> None:
    record = three_cohort_record()
    future_parent = "future@v1"
    record["conjectures"][1]["parent_conjecture_keys"].append(future_parent)
    cohort = record["cohorts"][1]
    cohort["assignments"][0]["parent_conjecture_keys"].append(future_parent)
    cohort["packets"][0]["parent_conjecture_keys"].append(future_parent)
    admission = cohort["originating_admission"]
    admission["parent_conjecture_keys"].append(future_parent)
    admission["planned_assignments"][0]["parent_conjecture_keys"].append(future_parent)
    record["collaboration_briefs"][0]["permitted_parent_conjecture_keys"].append(
        future_parent
    )
    admission["admission_fingerprint"] = gate._admission_fingerprint(record, admission)
    cohort["originating_admission_fingerprint"] = admission["admission_fingerprint"]
    with pytest.raises(gate.GateError, match="parent not visible before the cohort"):
        gate.validate_record(record, "merge")


def test_blocked_route_rejects_generic_evidence_gap_reopening() -> None:
    record = innovation_record()
    record["families"][0]["status"] = "blocked"
    record["cohorts"][0]["family_dispositions"][0]["status"] = "blocked"
    record["next_cohort_admission"]["prior_family_dispositions"][0]["status"] = "blocked"
    record["next_cohort_admission"]["basis"] = "evidence_gap"
    record["next_cohort_admission"]["admission_fingerprint"] = gate.next_cohort_fingerprint(record)
    with pytest.raises(gate.GateError, match="blocked route"):
        gate.validate_record(record, "next-cohort")


def test_combine_requires_two_parent_families() -> None:
    record = innovation_record()
    record["next_cohort_admission"]["purpose"] = "combine"
    record["next_cohort_admission"]["basis"] = "combination"
    record["next_cohort_admission"]["admission_fingerprint"] = gate.next_cohort_fingerprint(record)
    with pytest.raises(gate.GateError, match="at least two parent"):
        gate.validate_record(record, "next-cohort")


def test_next_cohort_fails_when_total_budget_is_exhausted() -> None:
    record = innovation_record()
    record["campaign"]["total_budgets"]["innovator"] = 1
    record["campaign"]["authorization_fingerprint"] = gate.campaign_fingerprint(record)
    record["next_cohort_admission"]["admission_fingerprint"] = gate.next_cohort_fingerprint(record)
    with pytest.raises(gate.GateError, match="exceeds innovator budget"):
        gate.validate_record(record, "next-cohort")


def test_per_cohort_user_confirmation_field_is_rejected() -> None:
    record = innovation_record()
    record["next_cohort_admission"]["user_confirmation"] = "confirm again"
    with pytest.raises(gate.GateError, match="per-cohort user confirmation"):
        gate.validate_record(record, "next-cohort")


def test_next_cohort_fingerprint_binds_planned_critic_count() -> None:
    record = innovation_record()
    record["next_cohort_admission"]["planned_critic_count"] = 1
    with pytest.raises(gate.GateError, match="fingerprint mismatch"):
        gate.validate_record(record, "next-cohort")


def test_synthesis_must_propagate_exact_critic_correction() -> None:
    record = innovation_record()
    record["synthesis"]["critic_correction_propagation"][0]["exact_text"] = "paraphrased"
    with pytest.raises(gate.GateError, match="changed correction"):
        gate.validate_record(record, "synthesis")


def test_applied_correction_must_reach_successor_field_exactly() -> None:
    record = two_cohort_record()
    drift = "Paraphrased successor claim."
    record["conjectures"][1]["exact_claim"] = drift
    record["cohorts"][1]["assignments"][0]["exact_claim"] = drift
    record["cohorts"][1]["packets"][0]["exact_claim"] = drift
    admission = record["cohorts"][1]["originating_admission"]
    admission["planned_assignments"][0]["exact_claim"] = drift
    admission["admission_fingerprint"] = gate._admission_fingerprint(record, admission)
    record["cohorts"][1]["originating_admission_fingerprint"] = admission[
        "admission_fingerprint"
    ]
    with pytest.raises(gate.GateError, match="exact text is absent"):
        gate.validate_record(record, "synthesis")


def test_applied_correction_requires_versioned_conjecture_lineage() -> None:
    record = innovation_record()
    family_correction = {
        **correction(),
        "target_record_id": "family-identity",
        "target_field": "core_mechanism",
        "exact_text": "identity-keyed lifecycle state",
    }
    record["cohorts"][0]["critic_packets"][0]["corrections"] = [family_correction]
    record["collaboration_briefs"][0]["corrections"] = [family_correction]
    record["synthesis"]["critic_correction_propagation"] = [
        {
            **family_correction,
            "outcome": "applied",
            "successor_record_id": "identity@v1",
        }
    ]
    with pytest.raises(gate.GateError, match="target must be a versioned conjecture"):
        gate.validate_record(record, "synthesis")


def test_synthesis_preserves_each_cohort_disposition_transition() -> None:
    record = two_cohort_record()
    record["cohorts"][0]["family_dispositions"][0]["status"] = "blocked"
    admission = record["cohorts"][1]["originating_admission"]
    admission["prior_family_dispositions"][0]["status"] = "blocked"
    admission["admission_fingerprint"] = gate._admission_fingerprint(record, admission)
    record["cohorts"][1]["originating_admission_fingerprint"] = admission[
        "admission_fingerprint"
    ]
    record["synthesis"]["cohort_disposition_history"][0]["family_dispositions"][0][
        "status"
    ] = "blocked"
    gate.validate_record(record, "synthesis")

    record["synthesis"]["cohort_disposition_history"][0]["family_dispositions"][0][
        "status"
    ] = "live"
    with pytest.raises(gate.GateError, match="changed a cohort disposition snapshot"):
        gate.validate_record(record, "synthesis")


def test_evidence_review_rejects_overlapping_scout_source_ownership() -> None:
    record = evidence_record()
    second = record["cohorts"][0]["assignments"][1]
    second["source_ids"] = ["MARL-0001"]
    second["source_bindings"] = [
        {
            "source_identity": "MARL-0001",
            "evidence_type": "json",
            "evidence_path": "C:/MyLib/json/MARL-0001.json",
        }
    ]
    with pytest.raises(gate.GateError, match="duplicate Scout source ownership"):
        gate.validate_record(record, "merge")


def test_scout_cannot_expand_frozen_source_set() -> None:
    record = evidence_record()
    assignment = record["cohorts"][0]["assignments"][0]
    assignment["source_ids"] = ["MARL-9999"]
    assignment["source_bindings"] = [
        {
            "source_identity": "MARL-9999",
            "evidence_type": "json",
            "evidence_path": "C:/MyLib/json/MARL-9999.json",
        }
    ]
    with pytest.raises(gate.GateError, match="frozen source set"):
        gate.validate_record(record, "merge")


def test_scout_packet_must_repeat_input_collaboration_brief_identity() -> None:
    record = evidence_record()
    record["cohorts"][0]["packets"][0]["input_collaboration_brief_id"] = "other-brief"
    with pytest.raises(gate.GateError, match="Scout packet collaboration brief"):
        gate.validate_record(record, "merge")


def test_evidence_review_cannot_create_collaboration_brief() -> None:
    record = evidence_record()
    record["collaboration_briefs"] = [
        {
            "brief_id": "unexpected-brief",
            "after_cohort_id": "evidence-cohort-1",
            "source_packet_ids": ["packet-1", "packet-2"],
            "corrections": [],
            "retained_lemmas": [],
            "counterexamples": [],
            "gaps": [],
            "transfer_candidates": [],
            "permitted_parent_conjecture_keys": [],
        }
    ]
    with pytest.raises(gate.GateError, match="must not create collaboration briefs"):
        gate.validate_record(record, "merge")


def test_conjecture_lineage_cycle_is_rejected() -> None:
    record = innovation_record()
    record["conjectures"][0]["parent_conjecture_keys"] = ["identity@v2"]
    record["conjectures"].append(
        {
            "conjecture_key": "identity@v2",
            "conjecture_id": "identity",
            "version": 2,
            "family_id": "family-identity",
            "parent_conjecture_keys": ["identity@v1"],
            "exact_claim": "Scoped identity preserves lifecycle state.",
            "source_packet_ids": [],
        }
    )
    with pytest.raises(gate.GateError, match="lineage contains a cycle"):
        gate.validate_record(record, "intake")


def test_old_wave_schema_is_rejected() -> None:
    record = innovation_record()
    record["document_kind"] = "independent_research_record_v1"
    with pytest.raises(gate.GateError, match="document_kind"):
        gate.validate_record(record, "intake")


def test_loader_is_confined_to_local_research(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    allowed = repo / "local_research" / "record.json"
    allowed.parent.mkdir(parents=True)
    allowed.write_text(json.dumps(evidence_record()), encoding="utf-8")
    assert gate.load_record(allowed, repo)["document_kind"] == gate.DOCUMENT_KIND

    outside = repo / "record.json"
    outside.write_text("{}", encoding="utf-8")
    with pytest.raises(gate.GateError, match="outside"):
        gate.load_record(outside, repo)
