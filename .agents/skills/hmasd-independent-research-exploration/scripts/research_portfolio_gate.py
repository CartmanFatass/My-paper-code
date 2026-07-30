"""Mechanical gate for HMASD independent-research campaign records.

The gate validates structure, identity, lineage, accounting and ordering. It
never judges novelty, correctness, causal validity or project authority, and it
never writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


DOCUMENT_KIND = "independent_research_campaign_v2"
MODES = {"evidence_review", "scientific_innovation"}
ROLES = {"scout", "innovator"}
PURPOSES = {"develop", "refine", "combine", "challenge"}
FAMILY_STATUSES = {"live", "blocked", "parked", "contradicted"}
CRITIC_DISPOSITIONS = {"supported", "weakened", "contradicted", "unresolved"}
CRITIC_STATUSES = CRITIC_DISPOSITIONS | {
    "conflicting",
    "not_selected",
    "operational_failure",
    "partial_operational_failure",
}
CONCRETE_OUTPUTS = {
    "lemma",
    "construction",
    "equation",
    "counterexample",
    "falsifiable_prediction",
}
ADMISSION_BASES = {
    "new_mechanism",
    "new_invariant",
    "new_construction",
    "critic_correction",
    "combination",
    "refinement",
    "evidence_gap",
}
BLOCKED_REOPEN_BASES = {
    "new_mechanism",
    "new_invariant",
    "new_construction",
    "critic_correction",
}
METHODOLOGY_FIELDS = {
    "scientific_object",
    "information_contract",
    "scope",
    "membership_nonstationarity",
    "identity_ownership_map",
    "temporal_abstraction",
    "policy_process",
    "solution_concept",
    "strategic_dependence",
    "primary_estimand",
    "sampling_hierarchy",
    "identification_assumptions",
    "uncertainty_plan",
    "simplest_competing_explanation",
    "intervention_regime",
    "comparator_regime",
    "equivalence_analysis",
    "replacement_ledger",
    "mathematical_defect",
    "predictions",
    "negative_controls",
    "resource_bounds",
    "complexity_bound",
    "approximation_assumptions",
    "smallest_claim",
    "smallest_supported_propositions",
    "smallest_refuted_propositions",
    "strongest_counterexample",
    "smallest_discriminating_observation",
    "failure_boundaries",
    "provenance",
    "stop_condition",
}
METHODOLOGY_NESTED_FIELDS = {
    "scientific_object": {"stochastic_game", "objective", "temporal_abstraction"},
    "information_contract": {
        "observations",
        "authoritative_membership",
        "symmetry_assumptions",
    },
    "scope": {"target_population", "source_boundary", "partner_policy_population"},
    "membership_nonstationarity": {"sources", "consequences"},
    "identity_ownership_map": {
        "persistent_entity",
        "slot",
        "policy_identity",
        "role",
        "skill",
        "capability_type",
        "recurrent_state_owner",
    },
    "temporal_abstraction": {
        "clock_map",
        "duration_distribution",
        "termination_rule",
        "interruption_and_censoring",
        "credit_rule",
    },
    "policy_process": {"frozen", "adapting", "jointly_trained", "replaced", "sampled"},
    "strategic_dependence": {
        "identity_and_symmetry_claim",
        "unilateral_intervention",
        "held_out_cross_play",
    },
    "sampling_hierarchy": {"top_level_independent_unit", "lower_levels"},
    "uncertainty_plan": {"method", "independent_unit"},
    "equivalence_analysis": {"tests"},
    "resource_bounds": {"evidence_search"},
    "complexity_bound": {"evidence_search", "deployment"},
    "provenance": {"baseline", "packet", "cross_pollination_edges"},
}


class GateError(ValueError):
    """A fail-closed mechanical contract error."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GateError(message)


def _mapping(value: Any, name: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{name} must be an object")
    return value


def _list(value: Any, name: str) -> list[Any]:
    _require(isinstance(value, list), f"{name} must be a list")
    return value


def _text(value: Any, name: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{name} is required")
    return value.strip()


def _text_list(value: Any, name: str, *, nonempty: bool = True) -> list[str]:
    items = _list(value, name)
    if nonempty:
        _require(bool(items), f"{name} must not be empty")
    output = [_text(item, f"{name} item") for item in items]
    _require(len(output) == len(set(output)), f"{name} contains duplicates")
    return output


def _integer(value: Any, name: str, minimum: int, maximum: int | None = None) -> int:
    _require(isinstance(value, int) and not isinstance(value, bool), f"{name} must be an integer")
    _require(value >= minimum, f"{name} is below its minimum")
    if maximum is not None:
        _require(value <= maximum, f"{name} exceeds its maximum")
    return value


def _unique(items: list[dict[str, Any]], key: str, name: str) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for item in items:
        identity = _text(item.get(key), f"{name}.{key}")
        _require(identity not in output, f"duplicate {name}.{key}: {identity}")
        output[identity] = item
    return output


def _present(value: Any, name: str) -> None:
    if isinstance(value, str):
        _text(value, name)
        return
    if isinstance(value, list):
        _require(bool(value), f"{name} must not be empty")
        for index, item in enumerate(value):
            _present(item, f"{name}[{index}]")
        return
    if isinstance(value, dict):
        _require(bool(value), f"{name} must not be empty")
        if "status" in value:
            status = _text(value.get("status"), f"{name}.status")
            _require(status in {"unknown", "not_applicable"}, f"{name}.status is invalid")
            _text(value.get("reason"), f"{name}.reason")
            if status == "unknown":
                _text(value.get("resolution_condition"), f"{name}.resolution_condition")
        else:
            for key, item in value.items():
                _present(item, f"{name}.{key}")
        return
    _require(value is not None, f"{name} is required")


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _conjecture_identity(value: Any, name: str) -> tuple[str, int]:
    key = _text(value, name)
    conjecture_id, separator, version_text = key.rpartition("@v")
    _require(
        bool(separator)
        and bool(conjecture_id)
        and version_text.isdigit()
        and int(version_text) >= 1
        and version_text == str(int(version_text)),
        f"{name} is not a canonical conjecture key",
    )
    return conjecture_id, int(version_text)


def _validate_intake(record: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    _require(record.get("document_kind") == DOCUMENT_KIND, f"document_kind must be {DOCUMENT_KIND}")
    intake = _mapping(record.get("intake"), "intake")
    mode = _text(intake.get("mode"), "intake.mode")
    _require(mode in MODES, f"unsupported intake.mode: {mode}")
    for field in ("question", "mission_link", "completion_condition"):
        _text(intake.get(field), f"intake.{field}")
    _text_list(intake.get("named_sources"), "intake.named_sources")
    _text_list(intake.get("exclusions"), "intake.exclusions", nonempty=False)
    _text_list(intake.get("semantic_traps"), "intake.semantic_traps")
    if mode == "scientific_innovation":
        _text(intake.get("evidence_baseline"), "intake.evidence_baseline")
        _text(intake.get("source_boundary"), "intake.source_boundary")
        _present(intake.get("scope"), "intake.scope")
        _present(
            intake.get("common_scientific_objects"),
            "intake.common_scientific_objects",
        )
        _text_list(
            intake.get("allowed_source_ids"),
            "intake.allowed_source_ids",
            nonempty=False,
        )
    return mode, intake


def campaign_fingerprint(record: dict[str, Any]) -> str:
    intake = _mapping(record.get("intake"), "intake")
    campaign = _mapping(record.get("campaign"), "campaign")
    budgets = _mapping(campaign.get("total_budgets"), "campaign.total_budgets")
    payload = {
        "campaign_id": _text(campaign.get("campaign_id"), "campaign.campaign_id"),
        "user_authorization_id": _text(
            campaign.get("user_authorization_id"),
            "campaign.user_authorization_id",
        ),
        "question": _text(intake.get("question"), "intake.question"),
        "mission_link": _text(intake.get("mission_link"), "intake.mission_link"),
        "named_sources": sorted(_text_list(intake.get("named_sources"), "intake.named_sources")),
        "allowed_source_ids": sorted(
            _text_list(
                intake.get("allowed_source_ids"),
                "intake.allowed_source_ids",
                nonempty=False,
            )
        ),
        "source_boundary": _text(intake.get("source_boundary"), "intake.source_boundary"),
        "evidence_baseline": _text(intake.get("evidence_baseline"), "intake.evidence_baseline"),
        "scope": intake.get("scope"),
        "common_scientific_objects": intake.get("common_scientific_objects"),
        "exclusions": sorted(
            _text_list(
                intake.get("exclusions"),
                "intake.exclusions",
                nonempty=False,
            )
        ),
        "completion_condition": _text(
            intake.get("completion_condition"),
            "intake.completion_condition",
        ),
        "semantic_traps": sorted(
            _text_list(intake.get("semantic_traps"), "intake.semantic_traps")
        ),
        "max_cohorts": _integer(campaign.get("max_cohorts"), "campaign.max_cohorts", 1),
        "total_budgets": {
            role: _integer(budgets.get(role), f"campaign.total_budgets.{role}", 0)
            for role in ("scout", "innovator", "critic")
        },
        "stop_conditions": sorted(
            _text_list(campaign.get("stop_conditions"), "campaign.stop_conditions")
        ),
    }
    return _canonical_hash(payload)


def _validate_campaign(record: dict[str, Any], mode: str) -> dict[str, Any] | None:
    campaign_value = record.get("campaign")
    if mode == "evidence_review":
        _require(campaign_value is None, "evidence_review must not create an innovation campaign")
        return None
    campaign = _mapping(campaign_value, "campaign")
    _text(campaign.get("campaign_id"), "campaign.campaign_id")
    _text(campaign.get("user_authorization_id"), "campaign.user_authorization_id")
    _integer(campaign.get("max_cohorts"), "campaign.max_cohorts", 1)
    budgets = _mapping(campaign.get("total_budgets"), "campaign.total_budgets")
    _integer(budgets.get("scout"), "campaign.total_budgets.scout", 0)
    _integer(budgets.get("innovator"), "campaign.total_budgets.innovator", 1)
    _integer(budgets.get("critic"), "campaign.total_budgets.critic", 0)
    _text_list(campaign.get("stop_conditions"), "campaign.stop_conditions")
    _require(
        campaign.get("authorization_fingerprint") == campaign_fingerprint(record),
        "campaign authorization fingerprint mismatch",
    )
    return campaign


def _validate_registry(
    record: dict[str, Any],
    mode: str,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    families_raw = [_mapping(item, "families item") for item in _list(record.get("families", []), "families")]
    conjectures_raw = [
        _mapping(item, "conjectures item")
        for item in _list(record.get("conjectures", []), "conjectures")
    ]
    if mode == "evidence_review":
        _require(not families_raw and not conjectures_raw, "evidence_review has no conjecture portfolio")
        return {}, {}

    _require(bool(families_raw), "scientific_innovation requires approach families")
    _require(bool(conjectures_raw), "scientific_innovation requires versioned conjectures")
    families = _unique(families_raw, "family_id", "family")
    conjectures = _unique(conjectures_raw, "conjecture_key", "conjecture")
    mechanisms: set[str] = set()

    for family_id, family in families.items():
        mechanism = _text(family.get("core_mechanism"), f"family {family_id}.core_mechanism")
        normalized = " ".join(mechanism.lower().split())
        _require(normalized not in mechanisms, "approach families duplicate a core mechanism")
        mechanisms.add(normalized)
        for field in (
            "current_conjecture_key",
            "strongest_support",
            "strongest_counterexample",
            "current_gap",
            "reopen_condition",
        ):
            _text(family.get(field), f"family {family_id}.{field}")
        status = _text(family.get("status"), f"family {family_id}.status")
        _require(status in FAMILY_STATUSES, f"invalid family status: {status}")
        critic_status = _text(family.get("critic_status"), f"family {family_id}.critic_status")
        _require(critic_status in CRITIC_STATUSES, f"invalid family critic_status: {critic_status}")
        _text_list(family.get("packet_ids", []), f"family {family_id}.packet_ids", nonempty=False)

    for key, conjecture in conjectures.items():
        conjecture_id = _text(conjecture.get("conjecture_id"), f"conjecture {key}.conjecture_id")
        version = _integer(conjecture.get("version"), f"conjecture {key}.version", 1)
        _require(key == f"{conjecture_id}@v{version}", f"conjecture key is not canonical: {key}")
        family_id = _text(conjecture.get("family_id"), f"conjecture {key}.family_id")
        _require(family_id in families, f"conjecture names unknown family: {family_id}")
        _text(conjecture.get("exact_claim"), f"conjecture {key}.exact_claim")
        parents = _text_list(
            conjecture.get("parent_conjecture_keys", []),
            f"conjecture {key}.parent_conjecture_keys",
            nonempty=False,
        )
        _require(key not in parents, "a conjecture cannot parent itself")
        _text_list(
            conjecture.get("source_packet_ids", []),
            f"conjecture {key}.source_packet_ids",
            nonempty=False,
        )
    for key, conjecture in conjectures.items():
        for parent in conjecture["parent_conjecture_keys"]:
            _require(parent in conjectures, f"conjecture {key} names unknown parent: {parent}")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(key: str) -> None:
        _require(key not in visiting, f"conjecture lineage contains a cycle at {key}")
        if key in visited:
            return
        visiting.add(key)
        for parent in conjectures[key]["parent_conjecture_keys"]:
            visit(parent)
        visiting.remove(key)
        visited.add(key)

    for key in conjectures:
        visit(key)
    for family_id, family in families.items():
        current = family["current_conjecture_key"]
        _require(current in conjectures, f"family {family_id} names unknown current conjecture")
        _require(
            conjectures[current]["family_id"] == family_id,
            f"family {family_id} current conjecture belongs to another family",
        )
    return families, conjectures


def _validate_traps(assignment: dict[str, Any], packet: dict[str, Any]) -> None:
    expected = set(_text_list(assignment.get("semantic_traps"), "assignment.semantic_traps"))
    results = [
        _mapping(item, "packet.semantic_trap_results item")
        for item in _list(packet.get("semantic_trap_results"), "packet.semantic_trap_results")
    ]
    observed: set[str] = set()
    for result in results:
        trap = _text(result.get("trap"), "semantic trap result.trap")
        disposition = _text(result.get("disposition"), "semantic trap result.disposition")
        _require(disposition in {"pass", "fail", "unresolved"}, "invalid semantic-trap disposition")
        _require(trap not in observed, f"duplicate semantic-trap result: {trap}")
        observed.add(trap)
    _require(observed == expected, "packet does not cover the exact assignment semantic traps")


def _validate_source_bindings(assignment: dict[str, Any]) -> set[tuple[str, str, str]]:
    sources = set(_text_list(assignment.get("source_ids"), "assignment.source_ids"))
    bindings = [
        _mapping(item, "assignment.source_bindings item")
        for item in _list(assignment.get("source_bindings"), "assignment.source_bindings")
    ]
    _require(bool(bindings), "assignment.source_bindings must not be empty")
    tuples: set[tuple[str, str, str]] = set()
    bound: set[str] = set()
    for binding in bindings:
        source = _text(binding.get("source_identity"), "source binding.source_identity")
        kind = _text(binding.get("evidence_type"), "source binding.evidence_type")
        path = _text(binding.get("evidence_path"), "source binding.evidence_path")
        _require(source in sources, "source binding names an unassigned source")
        _require(kind in {"json", "pdf"}, "source binding type must be json or pdf")
        _require(Path(path).is_absolute(), "source binding path must be absolute")
        item = (source, kind, path)
        _require(item not in tuples, "duplicate source binding")
        tuples.add(item)
        bound.add(source)
    _require(bound == sources, "source bindings do not cover assigned sources")
    return tuples


def _validate_evidence_packet(assignment: dict[str, Any], packet: dict[str, Any]) -> None:
    _require(packet.get("packet_kind") == "SCOUT_EVIDENCE_PACKET", "wrong evidence packet kind")
    _require(packet.get("evidence_axis_id") == assignment.get("evidence_axis_id"), "evidence-axis identity mismatch")
    _require(
        packet.get("input_collaboration_brief_id")
        == assignment.get("input_collaboration_brief_id"),
        "Scout packet collaboration brief identity mismatch",
    )
    assigned_sources = set(_text_list(assignment.get("source_ids"), "assignment.source_ids"))
    packet_sources = set(_text_list(packet.get("source_ids"), "packet.source_ids"))
    _require(packet_sources <= assigned_sources, "evidence packet expands source ownership")
    bindings = _validate_source_bindings(assignment)
    for field in (
        "search_terms",
        "candidates",
        "exclusions",
        "supporting_evidence",
        "conflicting_evidence",
        "boundary_evidence",
        "testable_hypotheses",
        "unresolved_facts",
        "mechanism_primitives",
        "transfer_boundaries",
        "cross_source_questions",
    ):
        _list(packet.get(field), f"evidence packet.{field}")
    _integer(packet.get("coverage_limit"), "evidence packet.coverage_limit", 1)
    rows = [_mapping(item, "evidence_rows item") for item in _list(packet.get("evidence_rows"), "evidence_rows")]
    _require(bool(rows), "evidence packet has no evidence rows")
    for row in rows:
        for field in (
            "claim_id",
            "claim",
            "source_identity",
            "title",
            "evidence_path",
            "evidence_type",
            "locator",
            "provenance",
            "claim_kind",
            "verification_state",
        ):
            _text(row.get(field), f"evidence row.{field}")
        _require(row["claim_id"] == assignment["claim_id"], "evidence row claim identity mismatch")
        _require(row["source_identity"] in packet_sources, "evidence row source is outside packet sources")
        _require(
            (row["source_identity"], row["evidence_type"], row["evidence_path"]) in bindings,
            "evidence row does not match an assigned source binding",
        )
        confidence = row.get("confidence")
        _require(
            isinstance(confidence, (int, float))
            and not isinstance(confidence, bool)
            and 0 <= confidence <= 1,
            "invalid evidence confidence",
        )


def _validate_methodology(packet: dict[str, Any]) -> None:
    methodology = _mapping(packet.get("methodology"), "direction packet.methodology")
    missing = METHODOLOGY_FIELDS - set(methodology)
    _require(not missing, f"direction packet methodology fields missing: {sorted(missing)}")
    for field in METHODOLOGY_FIELDS:
        _present(methodology[field], f"direction packet.methodology.{field}")
    for field, required in METHODOLOGY_NESTED_FIELDS.items():
        value = methodology[field]
        if isinstance(value, dict) and value.get("status") in {"unknown", "not_applicable"}:
            continue
        nested = _mapping(value, f"methodology.{field}")
        missing_nested = required - set(nested)
        _require(
            not missing_nested,
            f"methodology.{field} fields missing: {sorted(missing_nested)}",
        )
    ledger = _mapping(methodology["replacement_ledger"], "methodology.replacement_ledger")
    _require(set(ledger) == {"delete", "retain", "add"}, "replacement ledger must contain delete, retain and add")
    for field in ("delete", "retain", "add"):
        value = ledger[field]
        if isinstance(value, list):
            _require(bool(value), f"replacement_ledger.{field} must not be empty")
        else:
            _present(value, f"replacement_ledger.{field}")
    predictions = _mapping(methodology["predictions"], "methodology.predictions")
    _require(
        {"intervention", "natural_execution", "held_out_transport"} <= set(predictions),
        "predictions must separate intervention, natural execution and held-out transport",
    )
    for field in ("intervention", "natural_execution", "held_out_transport"):
        _present(predictions[field], f"methodology.predictions.{field}")


def _validate_direction_packet(
    assignment: dict[str, Any],
    packet: dict[str, Any],
    conjectures: dict[str, dict[str, Any]],
) -> None:
    _require(packet.get("packet_kind") == "RESEARCH_DIRECTION_PACKET", "wrong direction packet kind")
    for field in (
        "family_id",
        "conjecture_key",
        "claim_id",
        "purpose",
        "core_mechanism",
        "exact_claim",
        "mission_link",
        "evidence_baseline",
        "input_collaboration_brief_id",
        "campaign_scope",
        "common_scientific_objects",
    ):
        _require(packet.get(field) == assignment.get(field), f"direction packet changed {field}")
    _require(
        packet.get("parent_conjecture_keys") == assignment.get("parent_conjecture_keys"),
        "direction packet changed parent conjecture identities",
    )
    conjecture = conjectures[assignment["conjecture_key"]]
    _require(packet["exact_claim"] == conjecture["exact_claim"], "direction packet differs from conjecture claim")
    for field in (
        "derivation_or_construction",
        "novelty_delta",
        "proposed_conjecture_patch",
    ):
        _text(packet.get(field), f"direction packet.{field}")
    for field in ("assumptions", "evidence_dependencies"):
        _present(packet.get(field), f"direction packet.{field}")
    _list(packet.get("unresolved_items"), "direction packet.unresolved_items")
    _validate_methodology(packet)
    outputs = [
        _mapping(item, "concrete_outputs item")
        for item in _list(packet.get("concrete_outputs"), "direction packet.concrete_outputs")
    ]
    _require(bool(outputs), "direction packet has no concrete output")
    for output in outputs:
        kind = _text(output.get("kind"), "concrete output.kind")
        _require(kind in CONCRETE_OUTPUTS, f"invalid concrete output kind: {kind}")
        _text(output.get("content"), "concrete output.content")


def _validate_failure(failure: dict[str, Any], assignment_ids: set[str], packet_assignments: set[str]) -> None:
    _require(
        set(failure)
        == {
            "assignment_id",
            "failure_kind",
            "status",
            "failure_signature",
            "unchanged_retry_count",
            "scientific_output",
        },
        "terminal operational failure has unsupported fields",
    )
    assignment_id = _text(failure.get("assignment_id"), "terminal failure.assignment_id")
    _require(assignment_id in assignment_ids, "terminal failure names an unknown assignment")
    _require(assignment_id not in packet_assignments, "assignment has both packet and terminal failure")
    _require(failure.get("failure_kind") == "OPERATIONAL_FAILURE", "failure kind must be OPERATIONAL_FAILURE")
    _require(failure.get("status") == "terminal", "operational failure status must be terminal")
    _text(failure.get("failure_signature"), "terminal failure.failure_signature")
    _integer(failure.get("unchanged_retry_count"), "terminal failure.unchanged_retry_count", 0, 1)
    _require(failure.get("scientific_output") is False, "operational failure must have scientific_output=false")


def _validate_critic(
    critic: dict[str, Any],
    assignment: dict[str, Any],
    mode: str,
    cohort: dict[str, Any],
    packet_by_id: dict[str, dict[str, Any]],
    families: dict[str, dict[str, Any]],
    conjectures: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    _require(critic.get("packet_kind") == "CRITIC_ASSESSMENT_PACKET", "wrong Critic packet kind")
    _require(critic.get("status") == "terminal", "Critic packet status must be terminal")
    _require(
        critic.get("critic_assignment_id") == assignment.get("critic_assignment_id"),
        "Critic assignment identity mismatch",
    )
    _require(critic.get("cohort_id") == cohort["cohort_id"], "Critic cohort identity mismatch")
    for field in ("target_identity", "claim_id", "source_packet_ids"):
        _require(critic.get(field) == assignment.get(field), f"Critic changed assigned {field}")
    if mode == "scientific_innovation":
        _require(
            critic.get("campaign_id") == assignment.get("campaign_id"),
            "Critic campaign identity mismatch",
        )
        _require(
            critic.get("conjecture_key") == assignment.get("conjecture_key"),
            "Critic conjecture identity mismatch",
        )
    source_ids = _text_list(critic.get("source_packet_ids"), "critic.source_packet_ids")
    _require(set(source_ids) <= set(packet_by_id), "Critic names an unknown source packet")
    target = _text(critic.get("target_identity"), "critic.target_identity")
    claim_id = _text(critic.get("claim_id"), "critic.claim_id")
    sources = [packet_by_id[item] for item in source_ids]
    _require(all(packet["claim_id"] == claim_id for packet in sources), "Critic claim differs from source packets")
    if mode == "evidence_review":
        _require(all(packet["evidence_axis_id"] == target for packet in sources), "Critic evidence target mismatch")
    else:
        _require(target in families, "Critic names an unknown family")
        conjecture_key = _text(critic.get("conjecture_key"), "critic.conjecture_key")
        _require(conjecture_key in conjectures, "Critic names an unknown conjecture")
        _require(all(packet["family_id"] == target for packet in sources), "Critic family target mismatch")
        _require(all(packet["conjecture_key"] == conjecture_key for packet in sources), "Critic conjecture target mismatch")
    disposition = _text(critic.get("disposition"), "critic.disposition")
    _require(disposition in CRITIC_DISPOSITIONS, "invalid Critic disposition")
    results = [
        _mapping(item, "critic.checklist_results item")
        for item in _list(critic.get("checklist_results"), "critic.checklist_results")
    ]
    observed_checks: set[str] = set()
    for result in results:
        check = _text(result.get("check"), "critic checklist result.check")
        _text(result.get("disposition"), "critic checklist result.disposition")
        _require(check not in observed_checks, f"duplicate Critic checklist result: {check}")
        observed_checks.add(check)
    _require(
        observed_checks == set(assignment["checklist"]),
        "Critic packet does not cover its exact assigned checklist",
    )
    _text(critic.get("strongest_counterexample"), "critic.strongest_counterexample")
    _text(critic.get("alternate_explanation"), "critic.alternate_explanation")
    _text(critic.get("smallest_discriminating_observation"), "critic.smallest_discriminating_observation")
    corrections = [
        _mapping(item, "critic.corrections item")
        for item in _list(critic.get("corrections", []), "critic.corrections")
    ]
    _unique(corrections, "correction_id", "correction")
    for correction in corrections:
        for field in (
            "target_record_id",
            "target_field",
            "kind",
            "exact_text",
            "basis",
            "disposition_impact",
        ):
            _text(correction.get(field), f"correction.{field}")
        target_id = correction["target_record_id"]
        if target_id in conjectures:
            target_record = conjectures[target_id]
        elif target_id in families:
            target_record = families[target_id]
        elif target_id in packet_by_id:
            target_record = packet_by_id[target_id]
        else:
            raise GateError(f"correction names unknown target record: {target_id}")
        _require(
            correction["target_field"] in target_record,
            f"correction target field does not exist: {target_id}.{correction['target_field']}",
        )
    return corrections


def _validate_collaboration_briefs(
    record: dict[str, Any],
    cohort_by_id: dict[str, dict[str, Any]],
    cohort_packet_ids: dict[str, set[str]],
    cohort_correction_ids: dict[str, set[str]],
    correction_by_id: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    briefs = [
        _mapping(item, "collaboration_briefs item")
        for item in _list(record.get("collaboration_briefs", []), "collaboration_briefs")
    ]
    by_id = _unique(briefs, "brief_id", "collaboration brief")
    for brief_id, brief in by_id.items():
        after = _text(brief.get("after_cohort_id"), f"brief {brief_id}.after_cohort_id")
        _require(after in cohort_by_id, f"brief {brief_id} names unknown cohort")
        source_ids = set(_text_list(brief.get("source_packet_ids"), f"brief {brief_id}.source_packet_ids", nonempty=False))
        corrections = [
            _mapping(item, f"brief {brief_id}.corrections item")
            for item in _list(brief.get("corrections", []), f"brief {brief_id}.corrections")
        ]
        brief_corrections = _unique(corrections, "correction_id", "brief correction")
        correction_ids = set(brief_corrections)
        _require(source_ids == cohort_packet_ids[after], "collaboration brief packet identity set mismatch")
        _require(correction_ids == cohort_correction_ids[after], "collaboration brief correction identity set mismatch")
        for correction_id, correction in brief_corrections.items():
            _require(
                correction == correction_by_id[correction_id],
                f"collaboration brief changed correction: {correction_id}",
            )
        for field in ("retained_lemmas", "counterexamples", "gaps", "transfer_candidates"):
            _list(brief.get(field), f"brief {brief_id}.{field}")
        _text_list(
            brief.get("permitted_parent_conjecture_keys", []),
            f"brief {brief_id}.permitted_parent_conjecture_keys",
            nonempty=False,
        )
    return by_id


def _validate_cohorts(
    record: dict[str, Any],
    mode: str,
    intake: dict[str, Any],
    campaign: dict[str, Any] | None,
    families: dict[str, dict[str, Any]],
    conjectures: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    cohorts = [_mapping(item, "cohorts item") for item in _list(record.get("cohorts"), "cohorts")]
    _require(bool(cohorts), "at least one cohort is required")
    if mode == "evidence_review":
        _require(len(cohorts) == 1, "evidence_review has exactly one bounded cohort")
    if campaign is not None:
        _require(len(cohorts) <= campaign["max_cohorts"], "cohort count exceeds campaign maximum")

    indices = [_integer(cohort.get("index"), "cohort.index", 1) for cohort in cohorts]
    _require(indices == list(range(1, len(cohorts) + 1)), "cohort indices must be contiguous and ordered")
    cohort_by_id = _unique(cohorts, "cohort_id", "cohort")
    packet_by_id: dict[str, dict[str, Any]] = {}
    correction_by_id: dict[str, dict[str, Any]] = {}
    cohort_packet_ids: dict[str, set[str]] = {}
    cohort_correction_ids: dict[str, set[str]] = {}
    cohort_dispositions: dict[str, dict[str, dict[str, Any]]] = {}
    assignment_use = {"scout": 0, "innovator": 0, "critic": 0}

    for cohort in cohorts:
        cohort_id = cohort["cohort_id"]
        source_owner: dict[str, str] = {}
        family_owner: set[str] = set()
        conjecture_owner: set[str] = set()
        if campaign is not None:
            _require(cohort.get("campaign_id") == campaign["campaign_id"], "cohort campaign identity mismatch")
        input_brief = cohort.get("input_collaboration_brief_id")
        if cohort["index"] == 1:
            _require(input_brief is None, "first cohort must not read a collaboration brief")
        else:
            _text(input_brief, f"cohort {cohort_id}.input_collaboration_brief_id")

        assignments = [
            _mapping(item, f"cohort {cohort_id}.assignments item")
            for item in _list(cohort.get("assignments"), f"cohort {cohort_id}.assignments")
        ]
        _require(1 <= len(assignments) <= 4, "a cohort requires 1..4 Scout or Innovator assignments")
        assignments_by_id = _unique(assignments, "assignment_id", "assignment")
        for assignment_id, assignment in assignments_by_id.items():
            role = _text(assignment.get("role"), f"assignment {assignment_id}.role")
            _require(role in ROLES, f"invalid assignment role: {role}")
            if mode == "evidence_review":
                _require(role == "scout", "evidence_review uses Scouts only")
            if mode == "scientific_innovation" and cohort["index"] == 1:
                _require(role == "innovator", "first innovation cohort uses independently shielded Innovators")
            assignment_use[role] += 1
            _require(assignment.get("cohort_id") == cohort_id, "assignment cohort identity mismatch")
            if campaign is not None:
                _require(assignment.get("campaign_id") == campaign["campaign_id"], "assignment campaign identity mismatch")
                _require(
                    assignment.get("campaign_scope") == intake["scope"],
                    "assignment campaign scope differs from intake",
                )
                _require(
                    assignment.get("common_scientific_objects")
                    == intake["common_scientific_objects"],
                    "assignment scientific objects differ from intake",
                )
            _text(assignment.get("claim_id"), f"assignment {assignment_id}.claim_id")
            _text_list(assignment.get("semantic_traps"), f"assignment {assignment_id}.semantic_traps")
            _require(
                assignment.get("input_collaboration_brief_id") == input_brief,
                "assignment collaboration brief differs from cohort",
            )
            if role == "scout":
                _text(assignment.get("evidence_axis_id"), f"assignment {assignment_id}.evidence_axis_id")
                assignment_sources = _text_list(
                    assignment.get("source_ids"),
                    f"assignment {assignment_id}.source_ids",
                )
                allowed_sources = set(
                    intake["allowed_source_ids"]
                    if mode == "scientific_innovation"
                    else intake["named_sources"]
                )
                _require(
                    set(assignment_sources) <= allowed_sources,
                    "Scout assignment expands the frozen source set",
                )
                for source in assignment_sources:
                    _require(source not in source_owner, f"duplicate Scout source ownership: {source}")
                    source_owner[source] = assignment_id
                _validate_source_bindings(assignment)
            else:
                family_id = _text(assignment.get("family_id"), f"assignment {assignment_id}.family_id")
                conjecture_key = _text(
                    assignment.get("conjecture_key"),
                    f"assignment {assignment_id}.conjecture_key",
                )
                _require(family_id in families, "Innovator assignment names unknown family")
                _require(conjecture_key in conjectures, "Innovator assignment names unknown conjecture")
                _require(family_id not in family_owner, "cohort assigns one family more than once")
                _require(
                    conjecture_key not in conjecture_owner,
                    "cohort assigns one conjecture more than once",
                )
                family_owner.add(family_id)
                conjecture_owner.add(conjecture_key)
                _require(conjectures[conjecture_key]["family_id"] == family_id, "assignment family/conjecture mismatch")
                parents = _text_list(
                    assignment.get("parent_conjecture_keys", []),
                    f"assignment {assignment_id}.parent_conjecture_keys",
                    nonempty=False,
                )
                _require(parents == conjectures[conjecture_key]["parent_conjecture_keys"], "assignment lineage mismatch")
                purpose = _text(assignment.get("purpose"), f"assignment {assignment_id}.purpose")
                _require(purpose in PURPOSES, f"invalid assignment purpose: {purpose}")
                if cohort["index"] == 1:
                    _require(purpose in {"develop", "challenge"}, "first cohort cannot refine or combine")
                    expected = "named_for_challenge" if purpose == "challenge" else "withheld"
                    _require(
                        assignment.get("favored_family_visibility") == expected,
                        "first-cohort independence shielding failed",
                    )
                else:
                    _require(
                        assignment.get("favored_family_visibility") == "collaboration_brief_only",
                        "later cohort may receive only its named collaboration brief",
                    )
                if purpose == "combine":
                    _require(len(parents) >= 2, "combine requires at least two parent conjectures")
                    parent_families = {conjectures[parent]["family_id"] for parent in parents}
                    _require(len(parent_families) >= 2, "combine requires parents from at least two families")
                for field in ("core_mechanism", "exact_claim", "mission_link", "evidence_baseline"):
                    _text(assignment.get(field), f"assignment {assignment_id}.{field}")
                _require(
                    assignment["core_mechanism"] == families[family_id]["core_mechanism"],
                    "assignment mechanism differs from family",
                )
                _require(
                    assignment["exact_claim"] == conjectures[conjecture_key]["exact_claim"],
                    "assignment claim differs from conjecture",
                )
                _require(
                    assignment["mission_link"] == intake["mission_link"],
                    "Innovator mission link differs from intake",
                )
                _require(
                    assignment["evidence_baseline"] == intake["evidence_baseline"],
                    "Innovator evidence baseline differs from intake",
                )
                _require(assignment.get("methodology_reference") == "research-methodology.md", "methodology reference missing")

        packets = [
            _mapping(item, f"cohort {cohort_id}.packets item")
            for item in _list(cohort.get("packets"), f"cohort {cohort_id}.packets")
        ]
        packet_assignments: set[str] = set()
        local_packet_by_id: dict[str, dict[str, Any]] = {}
        for packet in packets:
            packet_id = _text(packet.get("packet_id"), "packet.packet_id")
            _require(packet_id not in packet_by_id, f"duplicate packet.packet_id: {packet_id}")
            assignment_id = _text(packet.get("assignment_id"), "packet.assignment_id")
            _require(assignment_id in assignments_by_id, "packet names unknown assignment")
            _require(assignment_id not in packet_assignments, "assignment returned multiple packets")
            packet_assignments.add(assignment_id)
            _require(packet.get("status") == "terminal", "packet status must be terminal")
            _require(packet.get("cohort_id") == cohort_id, "packet cohort identity mismatch")
            if campaign is not None:
                _require(packet.get("campaign_id") == campaign["campaign_id"], "packet campaign identity mismatch")
                _require(
                    packet.get("campaign_scope") == assignments_by_id[assignment_id]["campaign_scope"],
                    "packet campaign scope differs from assignment",
                )
                _require(
                    packet.get("common_scientific_objects")
                    == assignments_by_id[assignment_id]["common_scientific_objects"],
                    "packet scientific objects differ from assignment",
                )
            _require(packet.get("claim_id") == assignments_by_id[assignment_id]["claim_id"], "packet claim identity mismatch")
            _validate_traps(assignments_by_id[assignment_id], packet)
            if assignments_by_id[assignment_id]["role"] == "scout":
                _validate_evidence_packet(assignments_by_id[assignment_id], packet)
            else:
                _validate_direction_packet(assignments_by_id[assignment_id], packet, conjectures)
            packet_by_id[packet_id] = packet
            local_packet_by_id[packet_id] = packet

        failures = [
            _mapping(item, f"cohort {cohort_id}.terminal_failures item")
            for item in _list(cohort.get("terminal_failures", []), f"cohort {cohort_id}.terminal_failures")
        ]
        failure_by_assignment = _unique(failures, "assignment_id", "terminal operational failure")
        for failure in failures:
            _validate_failure(failure, set(assignments_by_id), packet_assignments)
        terminal = packet_assignments | set(failure_by_assignment)
        _require(terminal == set(assignments_by_id), "cohort merge barrier is incomplete")

        critic_assignments = [
            _mapping(item, f"cohort {cohort_id}.critic_assignments item")
            for item in _list(
                cohort.get("critic_assignments", []),
                f"cohort {cohort_id}.critic_assignments",
            )
        ]
        _require(len(critic_assignments) <= 2, "a cohort permits at most two Critic assignments")
        critic_assignment_by_id = _unique(
            critic_assignments,
            "critic_assignment_id",
            "Critic assignment",
        )
        for critic_assignment_id, critic_assignment in critic_assignment_by_id.items():
            _require(
                critic_assignment.get("cohort_id") == cohort_id,
                "Critic assignment cohort identity mismatch",
            )
            if campaign is not None:
                _require(
                    critic_assignment.get("campaign_id") == campaign["campaign_id"],
                    "Critic assignment campaign identity mismatch",
                )
                _require(
                    critic_assignment.get("methodology_reference")
                    == "research-methodology.md",
                    "innovation Critic methodology reference missing",
                )
            source_ids = _text_list(
                critic_assignment.get("source_packet_ids"),
                f"Critic assignment {critic_assignment_id}.source_packet_ids",
            )
            _require(
                set(source_ids) <= set(local_packet_by_id),
                "Critic assignment names an unknown source packet",
            )
            target_identity = _text(
                critic_assignment.get("target_identity"),
                "Critic assignment.target_identity",
            )
            claim_id = _text(critic_assignment.get("claim_id"), "Critic assignment.claim_id")
            assigned_source_packets = [local_packet_by_id[item] for item in source_ids]
            _require(
                all(packet["claim_id"] == claim_id for packet in assigned_source_packets),
                "Critic assignment claim differs from source packets",
            )
            _text_list(critic_assignment.get("checklist"), "Critic assignment.checklist")
            if mode == "scientific_innovation":
                conjecture_key = _text(
                    critic_assignment.get("conjecture_key"),
                    "Critic assignment.conjecture_key",
                )
                _require(conjecture_key in conjectures, "Critic assignment names unknown conjecture")
                _require(target_identity in families, "Critic assignment names unknown family")
                _require(
                    all(
                        packet["family_id"] == target_identity
                        and packet["conjecture_key"] == conjecture_key
                        for packet in assigned_source_packets
                    ),
                    "Critic assignment target differs from source packets",
                )
            else:
                _require(
                    all(
                        packet["evidence_axis_id"] == target_identity
                        for packet in assigned_source_packets
                    ),
                    "Critic assignment evidence target differs from source packets",
                )

        critics = [
            _mapping(item, f"cohort {cohort_id}.critic_packets item")
            for item in _list(cohort.get("critic_packets", []), f"cohort {cohort_id}.critic_packets")
        ]
        _require(len(critics) <= 2, "a cohort permits at most two Critic packets")
        critic_packet_by_assignment = _unique(critics, "critic_assignment_id", "critic packet")
        critic_failures = [
            _mapping(item, f"cohort {cohort_id}.critic_failures item")
            for item in _list(
                cohort.get("critic_failures", []),
                f"cohort {cohort_id}.critic_failures",
            )
        ]
        critic_failure_by_assignment = _unique(
            critic_failures,
            "assignment_id",
            "terminal Critic operational failure",
        )
        for failure in critic_failures:
            _validate_failure(
                failure,
                set(critic_assignment_by_id),
                set(critic_packet_by_assignment),
            )
        _require(
            set(critic_packet_by_assignment) | set(critic_failure_by_assignment)
            == set(critic_assignment_by_id),
            "Critic merge barrier is incomplete",
        )
        assignment_use["critic"] += len(critic_assignments)
        local_correction_ids: set[str] = set()
        for critic in critics:
            critic_assignment = critic_assignment_by_id[critic["critic_assignment_id"]]
            corrections = _validate_critic(
                critic,
                critic_assignment,
                mode,
                cohort,
                local_packet_by_id,
                families,
                conjectures,
            )
            for correction in corrections:
                correction_id = correction["correction_id"]
                _require(correction_id not in correction_by_id, f"duplicate correction_id: {correction_id}")
                correction_by_id[correction_id] = correction
                local_correction_ids.add(correction_id)
        cohort_packet_ids[cohort_id] = set(local_packet_by_id)
        cohort_correction_ids[cohort_id] = local_correction_ids
        if mode == "scientific_innovation":
            disposition_rows = [
                _mapping(item, f"cohort {cohort_id}.family_dispositions item")
                for item in _list(
                    cohort.get("family_dispositions"),
                    f"cohort {cohort_id}.family_dispositions",
                )
            ]
            disposition_by_family = _unique(
                disposition_rows,
                "family_id",
                "cohort family disposition",
            )
            _require(
                set(disposition_by_family) == set(families),
                "cohort family disposition set mismatch",
            )
            for family_id, disposition in disposition_by_family.items():
                _require(
                    set(disposition) == {"family_id", "status"},
                    "cohort family disposition has unsupported fields",
                )
                _require(
                    disposition.get("status") in FAMILY_STATUSES,
                    f"invalid cohort family disposition: {family_id}",
                )
            cohort_dispositions[cohort_id] = disposition_by_family
        else:
            _require(
                not cohort.get("family_dispositions", []),
                "evidence_review has no family dispositions",
            )

    if campaign is not None:
        budgets = campaign["total_budgets"]
        for role, used in assignment_use.items():
            _require(used <= budgets[role], f"campaign {role} budget exceeded")

    briefs = _validate_collaboration_briefs(
        record,
        cohort_by_id,
        cohort_packet_ids,
        cohort_correction_ids,
        correction_by_id,
    )
    if mode == "evidence_review":
        _require(not briefs, "evidence_review must not create collaboration briefs")
    ordered = sorted(cohorts, key=lambda item: item["index"])
    for position, cohort in enumerate(ordered):
        if position == 0:
            _require(
                cohort.get("originating_admission") is None
                and cohort.get("originating_admission_fingerprint") is None,
                "first cohort must not have an originating admission",
            )
            continue
        brief_id = cohort["input_collaboration_brief_id"]
        _require(brief_id in briefs, "later cohort names unknown collaboration brief")
        prior = ordered[position - 1]
        _require(briefs[brief_id]["after_cohort_id"] == prior["cohort_id"], "later cohort brief is not from prior merge")
        permitted = set(briefs[brief_id]["permitted_parent_conjecture_keys"])
        admission = _mapping(
            cohort.get("originating_admission"),
            f"cohort {cohort['cohort_id']}.originating_admission",
        )
        _require(
            not any("confirmation" in key.lower() for key in admission),
            "per-cohort user confirmation fields are forbidden",
        )
        expected_admission_fingerprint = _admission_fingerprint(record, admission)
        _require(
            cohort.get("originating_admission_fingerprint")
            == expected_admission_fingerprint
            == admission.get("admission_fingerprint"),
            "completed cohort admission fingerprint mismatch",
        )
        _require(
            admission.get("prior_cohort_id") == prior["cohort_id"]
            and admission.get("next_cohort_id") == cohort["cohort_id"],
            "completed cohort admission transition identity mismatch",
        )
        _require(
            admission.get("input_collaboration_brief_id") == brief_id,
            "completed cohort admission brief mismatch",
        )
        _require(
            set(admission["prior_terminal_assignment_ids"])
            == {item["assignment_id"] for item in prior["assignments"]},
            "completed cohort admission prior assignment set mismatch",
        )
        _require(
            set(admission["prior_terminal_packet_ids"])
            == cohort_packet_ids[prior["cohort_id"]],
            "completed cohort admission prior packet set mismatch",
        )
        _require(
            set(admission["prior_correction_ids"])
            == cohort_correction_ids[prior["cohort_id"]],
            "completed cohort admission prior correction set mismatch",
        )
        admitted_dispositions = _unique(
            [
                _mapping(item, "originating admission disposition item")
                for item in admission["prior_family_dispositions"]
            ],
            "family_id",
            "originating admission disposition",
        )
        _require(
            admitted_dispositions == cohort_dispositions[prior["cohort_id"]],
            "completed cohort admission prior disposition snapshot mismatch",
        )
        planned = sorted(
            _validate_planned_assignments(admission.get("planned_assignments")),
            key=lambda item: item["assignment_id"],
        )
        prior_packet_ids: set[str] = set()
        for earlier in ordered[:position]:
            prior_packet_ids.update(cohort_packet_ids[earlier["cohort_id"]])
        prior_conjectures = {
            key: conjecture
            for key, conjecture in conjectures.items()
            if not conjecture["source_packet_ids"]
            or set(conjecture["source_packet_ids"]) <= prior_packet_ids
        }
        _validate_admission_plan_context(
            planned,
            intake,
            families,
            conjectures,
            admission,
            briefs[brief_id],
            prior_conjectures,
        )
        actual_plans = sorted(
            [_assignment_plan(item) for item in cohort["assignments"]],
            key=lambda item: item["assignment_id"],
        )
        _require(planned == actual_plans, "completed cohort differs from admitted assignment semantics")
        _require(
            len(cohort.get("critic_assignments", []))
            <= admission.get("planned_critic_count"),
            "completed cohort exceeds its admitted Critic count",
        )
        targets = set(admission["target_family_ids"])
        _require(targets <= set(families), "completed cohort admission names unknown family")
        basis = admission["basis"]
        _require(basis in ADMISSION_BASES, "completed cohort admission basis is invalid")
        if any(admitted_dispositions[item]["status"] == "blocked" for item in targets):
            _require(
                basis in BLOCKED_REOPEN_BASES,
                "completed cohort reopened a blocked route without new content",
            )
        for assignment in cohort["assignments"]:
            if assignment["role"] == "innovator":
                _require(
                    set(assignment["parent_conjecture_keys"]) <= permitted,
                    "later Innovator uses a parent not permitted by its collaboration brief",
                )

    if mode == "scientific_innovation":
        _require(
            {
                family_id: families[family_id]["status"]
                for family_id in families
            }
            == {
                family_id: item["status"]
                for family_id, item in cohort_dispositions[ordered[-1]["cohort_id"]].items()
            },
            "current family status differs from the latest cohort disposition snapshot",
        )
        actual_family_packets: dict[str, set[str]] = {family_id: set() for family_id in families}
        actual_conjecture_packets: dict[str, set[str]] = {key: set() for key in conjectures}
        dispositions: dict[str, set[str]] = {}
        critic_selected: dict[str, int] = {}
        critic_failed: dict[str, int] = {}
        for packet_id, packet in packet_by_id.items():
            if packet["packet_kind"] == "RESEARCH_DIRECTION_PACKET":
                actual_family_packets[packet["family_id"]].add(packet_id)
                actual_conjecture_packets[packet["conjecture_key"]].add(packet_id)
        for cohort in cohorts:
            critic_assignment_targets = {
                item["critic_assignment_id"]: item["target_identity"]
                for item in cohort.get("critic_assignments", [])
            }
            for target in critic_assignment_targets.values():
                critic_selected[target] = critic_selected.get(target, 0) + 1
            for critic in cohort.get("critic_packets", []):
                dispositions.setdefault(critic["target_identity"], set()).add(critic["disposition"])
            for failure in cohort.get("critic_failures", []):
                target = critic_assignment_targets[failure["assignment_id"]]
                critic_failed[target] = critic_failed.get(target, 0) + 1
        for family_id, family in families.items():
            _require(set(family["packet_ids"]) == actual_family_packets[family_id], "family packet registration mismatch")
            values = dispositions.get(family_id, set())
            selected = critic_selected.get(family_id, 0)
            failed = critic_failed.get(family_id, 0)
            if selected == 0:
                expected = "not_selected"
            elif failed == selected:
                expected = "operational_failure"
            elif failed:
                expected = "partial_operational_failure"
            else:
                expected = next(iter(values)) if len(values) == 1 else "conflicting"
            _require(family["critic_status"] == expected, "family critic_status differs from Critic packets")
        for key, conjecture in conjectures.items():
            _require(
                set(conjecture["source_packet_ids"]) == actual_conjecture_packets[key],
                "conjecture source packet registration mismatch",
            )

    return {
        "cohorts": cohorts,
        "cohort_by_id": cohort_by_id,
        "packet_by_id": packet_by_id,
        "correction_by_id": correction_by_id,
        "cohort_packet_ids": cohort_packet_ids,
        "cohort_correction_ids": cohort_correction_ids,
        "cohort_dispositions": cohort_dispositions,
        "briefs": briefs,
        "role_use": assignment_use,
    }


def _assignment_plan(assignment: dict[str, Any]) -> dict[str, Any]:
    common = {
        "assignment_id": assignment.get("assignment_id"),
        "role": assignment.get("role"),
        "claim_id": assignment.get("claim_id"),
        "semantic_traps": assignment.get("semantic_traps"),
    }
    if assignment.get("role") == "scout":
        return {
            **common,
            "evidence_axis_id": assignment.get("evidence_axis_id"),
            "source_ids": assignment.get("source_ids"),
            "source_bindings": assignment.get("source_bindings"),
        }
    return {
        **common,
        "family_id": assignment.get("family_id"),
        "conjecture_key": assignment.get("conjecture_key"),
        "parent_conjecture_keys": assignment.get("parent_conjecture_keys"),
        "purpose": assignment.get("purpose"),
        "core_mechanism": assignment.get("core_mechanism"),
        "exact_claim": assignment.get("exact_claim"),
    }


def _validate_planned_assignments(value: Any) -> list[dict[str, Any]]:
    planned = [
        _mapping(item, "planned_assignments item")
        for item in _list(value, "planned_assignments")
    ]
    _require(1 <= len(planned) <= 4, "next cohort requires 1..4 planned assignments")
    _unique(planned, "assignment_id", "planned assignment")
    for item in planned:
        role = _text(item.get("role"), "planned assignment.role")
        _require(role in ROLES, "invalid planned assignment role")
        _text(item.get("claim_id"), "planned assignment.claim_id")
        _text_list(item.get("semantic_traps"), "planned assignment.semantic_traps")
        common = {"assignment_id", "role", "claim_id", "semantic_traps"}
        if role == "scout":
            expected = common | {"evidence_axis_id", "source_ids", "source_bindings"}
            _text(item.get("evidence_axis_id"), "planned Scout.evidence_axis_id")
            _text_list(item.get("source_ids"), "planned Scout.source_ids")
            _list(item.get("source_bindings"), "planned Scout.source_bindings")
        else:
            expected = common | {
                "family_id",
                "conjecture_key",
                "parent_conjecture_keys",
                "purpose",
                "core_mechanism",
                "exact_claim",
            }
            for field in (
                "family_id",
                "conjecture_key",
                "purpose",
                "core_mechanism",
                "exact_claim",
            ):
                _text(item.get(field), f"planned Innovator.{field}")
            _text_list(
                item.get("parent_conjecture_keys", []),
                "planned Innovator.parent_conjecture_keys",
                nonempty=False,
            )
        _require(set(item) == expected, "planned assignment has missing or unsupported semantic fields")
    return planned


def _validate_admission_plan_context(
    planned: list[dict[str, Any]],
    intake: dict[str, Any],
    families: dict[str, dict[str, Any]],
    conjectures: dict[str, dict[str, Any]],
    admission: dict[str, Any],
    brief: dict[str, Any],
    prior_conjectures: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Bind a not-yet-dispatched cohort plan to its frozen campaign context."""

    targets = set(
        _text_list(admission.get("target_family_ids"), "admission.target_family_ids")
    )
    admitted_parents = set(
        _text_list(
            admission.get("parent_conjecture_keys"),
            "admission.parent_conjecture_keys",
            nonempty=False,
        )
    )
    permitted_parents = set(
        _text_list(
            brief.get("permitted_parent_conjecture_keys", []),
            "collaboration brief.permitted_parent_conjecture_keys",
            nonempty=False,
        )
    )
    parent_registry = conjectures if prior_conjectures is None else prior_conjectures
    _require(
        admitted_parents <= set(parent_registry),
        "admission names a parent not visible before the cohort",
    )
    admission_purpose = _text(admission.get("purpose"), "admission.purpose")
    allowed_sources = set(
        _text_list(
            intake.get("allowed_source_ids"),
            "intake.allowed_source_ids",
            nonempty=False,
        )
    )
    scout_source_owner: dict[str, str] = {}
    planned_innovator_parents: set[str] = set()
    planned_family_owner: set[str] = set()
    planned_conjecture_owner: set[str] = set()

    for item in planned:
        assignment_id = _text(item.get("assignment_id"), "planned assignment.assignment_id")
        if item["role"] == "scout":
            sources = set(
                _text_list(item.get("source_ids"), f"planned Scout {assignment_id}.source_ids")
            )
            _require(
                sources <= allowed_sources,
                "planned Scout expands the frozen source set",
            )
            _validate_source_bindings(item)
            for source in sources:
                _require(
                    source not in scout_source_owner,
                    f"duplicate planned Scout source ownership: {source}",
                )
                scout_source_owner[source] = assignment_id
            continue

        purpose = _text(item.get("purpose"), f"planned Innovator {assignment_id}.purpose")
        _require(
            purpose == admission_purpose,
            "planned Innovator purpose differs from admission",
        )
        family_id = _text(item.get("family_id"), f"planned Innovator {assignment_id}.family_id")
        conjecture_key = _text(
            item.get("conjecture_key"),
            f"planned Innovator {assignment_id}.conjecture_key",
        )
        _require(
            family_id not in planned_family_owner,
            "planned cohort assigns one family more than once",
        )
        _require(
            conjecture_key not in planned_conjecture_owner,
            "planned cohort assigns one conjecture more than once",
        )
        planned_family_owner.add(family_id)
        planned_conjecture_owner.add(conjecture_key)
        parents = set(
            _text_list(
                item.get("parent_conjecture_keys", []),
                f"planned Innovator {assignment_id}.parent_conjecture_keys",
                nonempty=False,
            )
        )
        planned_innovator_parents.update(parents)
        _require(
            parents <= admitted_parents,
            "planned Innovator parent is outside the admission",
        )
        _require(
            parents <= permitted_parents,
            "planned Innovator parent is not permitted by the collaboration brief",
        )
        if purpose == "combine":
            _require(len(parents) >= 2, "planned combine requires at least two parents")
            _require(
                len({parent_registry[parent]["family_id"] for parent in parents}) >= 2,
                "planned combine requires parents from at least two families",
            )
            _require(
                {parent_registry[parent]["family_id"] for parent in parents} <= targets,
                "planned combine uses a parent family outside its targets",
            )
        else:
            _require(
                family_id in targets,
                "planned Innovator family is outside the admission targets",
            )
            _require(family_id in families, "planned Innovator names an unknown family")

        if family_id in families:
            _require(
                item["core_mechanism"] == families[family_id]["core_mechanism"],
                "planned Innovator mechanism differs from its family",
            )
        conjecture_id, version = _conjecture_identity(
            conjecture_key,
            f"planned Innovator {assignment_id}.conjecture_key",
        )
        if conjecture_key in conjectures:
            conjecture = conjectures[conjecture_key]
            _require(
                conjecture["family_id"] == family_id,
                "planned Innovator family/conjecture mismatch",
            )
            _require(
                set(conjecture["parent_conjecture_keys"]) == parents,
                "planned Innovator lineage differs from its conjecture",
            )
            _require(
                conjecture["exact_claim"] == item["exact_claim"],
                "planned Innovator claim differs from its conjecture",
            )
        version_registry = conjectures if prior_conjectures is None else prior_conjectures
        prior_versions = sorted(
            item["version"]
            for key, item in version_registry.items()
            if key != conjecture_key and item["conjecture_id"] == conjecture_id
        )
        expected_version = prior_versions[-1] + 1 if prior_versions else 1
        _require(
            version == expected_version,
            "planned prospective conjecture does not use the next canonical version",
        )
        if purpose == "refine":
            _require(
                bool(prior_versions),
                "planned refinement cannot introduce an unrelated conjecture identity",
            )
            _require(
                f"{conjecture_id}@v{version - 1}" in parents,
                "planned refinement omits its own immediate predecessor",
            )
            _require(
                all(parent_registry[parent]["family_id"] == family_id for parent in parents),
                "planned refinement crosses family lineage",
            )

    _require(
        planned_innovator_parents == admitted_parents,
        "planned Innovator parents do not exactly cover the admission parent set",
    )


def _admission_fingerprint(record: dict[str, Any], admission: dict[str, Any]) -> str:
    planned = _validate_planned_assignments(admission.get("planned_assignments"))
    payload = {
        "campaign_authorization_fingerprint": _text(
            record["campaign"].get("authorization_fingerprint"),
            "campaign.authorization_fingerprint",
        ),
        "prior_cohort_id": _text(admission.get("prior_cohort_id"), "admission.prior_cohort_id"),
        "next_cohort_id": _text(admission.get("next_cohort_id"), "admission.next_cohort_id"),
        "prior_terminal_assignment_ids": sorted(
            _text_list(admission.get("prior_terminal_assignment_ids"), "admission.prior_terminal_assignment_ids")
        ),
        "prior_terminal_packet_ids": sorted(
            _text_list(
                admission.get("prior_terminal_packet_ids"),
                "admission.prior_terminal_packet_ids",
                nonempty=False,
            )
        ),
        "prior_correction_ids": sorted(
            _text_list(
                admission.get("prior_correction_ids"),
                "admission.prior_correction_ids",
                nonempty=False,
            )
        ),
        "prior_family_dispositions": sorted(
            [
                {
                    "family_id": _text(item.get("family_id"), "prior disposition.family_id"),
                    "status": _text(item.get("status"), "prior disposition.status"),
                }
                for item in [
                    _mapping(value, "prior_family_dispositions item")
                    for value in _list(
                        admission.get("prior_family_dispositions"),
                        "prior_family_dispositions",
                    )
                ]
            ],
            key=lambda item: item["family_id"],
        ),
        "input_collaboration_brief_id": _text(
            admission.get("input_collaboration_brief_id"),
            "admission.input_collaboration_brief_id",
        ),
        "target_family_ids": sorted(
            _text_list(admission.get("target_family_ids"), "admission.target_family_ids")
        ),
        "parent_conjecture_keys": sorted(
            _text_list(
                admission.get("parent_conjecture_keys"),
                "admission.parent_conjecture_keys",
                nonempty=False,
            )
        ),
        "purpose": _text(admission.get("purpose"), "admission.purpose"),
        "basis": _text(admission.get("basis"), "admission.basis"),
        "novelty_statement": _text(admission.get("novelty_statement"), "admission.novelty_statement"),
        "expected_disposition_change": _text(
            admission.get("expected_disposition_change"),
            "admission.expected_disposition_change",
        ),
        "planned_assignments": sorted(planned, key=lambda item: item["assignment_id"]),
        "planned_critic_count": _integer(
            admission.get("planned_critic_count"),
            "admission.planned_critic_count",
            0,
            2,
        ),
        "stop_condition": _text(admission.get("stop_condition"), "admission.stop_condition"),
    }
    return _canonical_hash(payload)


def next_cohort_fingerprint(record: dict[str, Any]) -> str:
    admission = _mapping(record.get("next_cohort_admission"), "next_cohort_admission")
    return _admission_fingerprint(record, admission)


def _validate_next_cohort(
    record: dict[str, Any],
    intake: dict[str, Any],
    campaign: dict[str, Any] | None,
    families: dict[str, dict[str, Any]],
    conjectures: dict[str, dict[str, Any]],
    state: dict[str, Any],
) -> None:
    _require(campaign is not None, "evidence_review has no next cohort")
    admission = _mapping(record.get("next_cohort_admission"), "next_cohort_admission")
    _require(
        not any("confirmation" in key.lower() for key in admission),
        "per-cohort user confirmation fields are forbidden",
    )
    cohorts = state["cohorts"]
    latest = cohorts[-1]
    _require(len(cohorts) < campaign["max_cohorts"], "campaign maximum cohort count is exhausted")
    _require(admission.get("prior_cohort_id") == latest["cohort_id"], "admission names wrong prior cohort")
    next_id = _text(admission.get("next_cohort_id"), "admission.next_cohort_id")
    _require(next_id not in state["cohort_by_id"], "next cohort identity already exists")
    terminal_assignments = {item["assignment_id"] for item in latest["assignments"]}
    _require(
        set(_text_list(admission.get("prior_terminal_assignment_ids"), "admission.prior_terminal_assignment_ids"))
        == terminal_assignments,
        "admission terminal assignment identity set mismatch",
    )
    _require(
        set(
            _text_list(
                admission.get("prior_terminal_packet_ids"),
                "admission.prior_terminal_packet_ids",
                nonempty=False,
            )
        )
        == state["cohort_packet_ids"][latest["cohort_id"]],
        "admission terminal packet identity set mismatch",
    )
    _require(
        set(
            _text_list(
                admission.get("prior_correction_ids"),
                "admission.prior_correction_ids",
                nonempty=False,
            )
        )
        == state["cohort_correction_ids"][latest["cohort_id"]],
        "admission correction identity set mismatch",
    )
    prior_dispositions = [
        _mapping(item, "admission.prior_family_dispositions item")
        for item in _list(
            admission.get("prior_family_dispositions"),
            "admission.prior_family_dispositions",
        )
    ]
    prior_by_family = _unique(prior_dispositions, "family_id", "prior family disposition")
    latest_dispositions = {
        item["family_id"]: item
        for item in latest["family_dispositions"]
    }
    _require(
        prior_by_family == latest_dispositions,
        "admission prior family disposition snapshot mismatch",
    )
    brief_id = _text(admission.get("input_collaboration_brief_id"), "admission.input_collaboration_brief_id")
    _require(brief_id in state["briefs"], "next cohort names unknown collaboration brief")
    _require(state["briefs"][brief_id]["after_cohort_id"] == latest["cohort_id"], "next cohort brief is stale")

    targets = _text_list(admission.get("target_family_ids"), "admission.target_family_ids")
    _require(set(targets) <= set(families), "next cohort names unknown target family")
    parents = _text_list(
        admission.get("parent_conjecture_keys"),
        "admission.parent_conjecture_keys",
        nonempty=False,
    )
    _require(set(parents) <= set(conjectures), "next cohort names unknown parent conjecture")
    _require(
        set(parents) <= set(state["briefs"][brief_id]["permitted_parent_conjecture_keys"]),
        "next cohort parent is not permitted by collaboration brief",
    )
    purpose = _text(admission.get("purpose"), "admission.purpose")
    basis = _text(admission.get("basis"), "admission.basis")
    _require(purpose in PURPOSES, "invalid next-cohort purpose")
    _require(basis in ADMISSION_BASES, "invalid next-cohort basis")
    if any(prior_by_family[family_id]["status"] == "blocked" for family_id in targets):
        _require(basis in BLOCKED_REOPEN_BASES, "blocked route lacks a new mechanism, invariant, construction or correction")
    if basis == "critic_correction":
        _require(bool(state["cohort_correction_ids"][latest["cohort_id"]]), "critic-correction admission has no exact correction")
    if purpose == "combine":
        _require(len(parents) >= 2, "combined route requires at least two parent conjectures")
        _require(
            len({conjectures[parent]["family_id"] for parent in parents}) >= 2,
            "combined route requires parents from at least two families",
        )
    _text(admission.get("novelty_statement"), "admission.novelty_statement")
    _text(admission.get("expected_disposition_change"), "admission.expected_disposition_change")
    _text(admission.get("stop_condition"), "admission.stop_condition")

    planned = _validate_planned_assignments(admission.get("planned_assignments"))
    _validate_admission_plan_context(
        planned,
        intake,
        families,
        conjectures,
        admission,
        state["briefs"][brief_id],
    )
    planned_use = {"scout": 0, "innovator": 0}
    for item in planned:
        role = _text(item.get("role"), "planned assignment.role")
        _require(role in ROLES, "invalid planned assignment role")
        planned_use[role] += 1
    budgets = campaign["total_budgets"]
    for role in ("scout", "innovator"):
        _require(state["role_use"][role] + planned_use[role] <= budgets[role], f"next cohort exceeds {role} budget")
    planned_critics = _integer(admission.get("planned_critic_count"), "admission.planned_critic_count", 0, 2)
    _require(state["role_use"]["critic"] + planned_critics <= budgets["critic"], "next cohort exceeds critic budget")
    _require(admission.get("admission_fingerprint") == next_cohort_fingerprint(record), "next-cohort fingerprint mismatch")


def _validate_synthesis(
    record: dict[str, Any],
    mode: str,
    families: dict[str, dict[str, Any]],
    conjectures: dict[str, dict[str, Any]],
    state: dict[str, Any],
) -> None:
    synthesis = _mapping(record.get("synthesis"), "synthesis")
    _require(synthesis.get("advisory_only") is True, "synthesis must remain advisory")
    _require(synthesis.get("automatic_formal_promotion") is False, "synthesis must not promote itself")
    _text(synthesis.get("completion_reason"), "synthesis.completion_reason")
    propagated = [
        _mapping(item, "synthesis.critic_correction_propagation item")
        for item in _list(
            synthesis.get("critic_correction_propagation"),
            "synthesis.critic_correction_propagation",
        )
    ]
    by_correction = _unique(propagated, "correction_id", "propagated correction")
    _require(set(by_correction) == set(state["correction_by_id"]), "synthesis correction identity set mismatch")
    for correction_id, source in state["correction_by_id"].items():
        target = by_correction[correction_id]
        for field in (
            "target_record_id",
            "target_field",
            "kind",
            "exact_text",
            "basis",
            "disposition_impact",
        ):
            _require(target.get(field) == source.get(field), f"synthesis changed correction {correction_id}.{field}")
        outcome = _text(target.get("outcome"), f"correction propagation {correction_id}.outcome")
        _require(
            outcome in {"applied", "unresolved", "conflicting"},
            f"invalid correction propagation outcome: {outcome}",
        )
        if outcome == "applied":
            successor_id = _text(
                target.get("successor_record_id"),
                f"correction propagation {correction_id}.successor_record_id",
            )
            _require(
                successor_id != source["target_record_id"],
                "applied correction must create or target a successor record",
            )
            _require(
                source["target_record_id"] in conjectures,
                "applied correction target must be a versioned conjecture",
            )
            _require(
                successor_id in conjectures,
                "applied correction successor must be a versioned conjecture",
            )
            successor = conjectures[successor_id]
            field = source["target_field"]
            _require(field in successor, "applied correction successor lacks target field")
            _require(
                successor[field] == source["exact_text"],
                "applied correction exact text is absent from successor field",
            )
            _require(
                source["target_record_id"] in successor["parent_conjecture_keys"],
                "corrected conjecture does not preserve target as a parent",
            )
        else:
            _text(
                target.get("resolution_reason"),
                f"correction propagation {correction_id}.resolution_reason",
            )
    if mode == "evidence_review":
        return
    history = [
        _mapping(item, "synthesis.cohort_disposition_history item")
        for item in _list(
            synthesis.get("cohort_disposition_history"),
            "synthesis.cohort_disposition_history",
        )
    ]
    _require(
        len(history) == len(state["cohorts"]),
        "synthesis cohort disposition history length mismatch",
    )
    for row, cohort in zip(history, state["cohorts"]):
        _require(
            set(row) == {"cohort_id", "family_dispositions"},
            "synthesis cohort disposition history has unsupported fields",
        )
        cohort_id = cohort["cohort_id"]
        _require(row.get("cohort_id") == cohort_id, "synthesis cohort disposition history order mismatch")
        row_dispositions = _unique(
            [
                _mapping(item, "synthesis historical family disposition item")
                for item in _list(
                    row.get("family_dispositions"),
                    "synthesis historical family dispositions",
                )
            ],
            "family_id",
            "synthesis historical family disposition",
        )
        _require(
            row_dispositions == state["cohort_dispositions"][cohort_id],
            "synthesis changed a cohort disposition snapshot",
        )
    dispositions = [
        _mapping(item, "synthesis.family_dispositions item")
        for item in _list(synthesis.get("family_dispositions"), "synthesis.family_dispositions")
    ]
    by_family = _unique(dispositions, "family_id", "family disposition")
    _require(set(by_family) == set(families), "synthesis family set mismatch")
    for family_id, item in by_family.items():
        _require(item.get("status") == families[family_id]["status"], "synthesis changes family disposition")
    _require(
        set(_text_list(synthesis.get("conjecture_version_map"), "synthesis.conjecture_version_map"))
        == set(conjectures),
        "synthesis conjecture version map mismatch",
    )
    _require(
        set(
            _text_list(
                synthesis.get("collaboration_brief_ids"),
                "synthesis.collaboration_brief_ids",
                nonempty=False,
            )
        )
        == set(state["briefs"]),
        "synthesis collaboration brief set mismatch",
    )


def validate_record(record: dict[str, Any], phase: str) -> dict[str, Any]:
    mode, _ = _validate_intake(record)
    campaign = _validate_campaign(record, mode)
    families, conjectures = _validate_registry(record, mode)
    if phase == "intake":
        return {
            "mode": mode,
            "families": len(families),
            "conjectures": len(conjectures),
        }
    state = _validate_cohorts(record, mode, record["intake"], campaign, families, conjectures)
    if phase == "next-cohort":
        _validate_next_cohort(record, record["intake"], campaign, families, conjectures, state)
    elif phase == "synthesis":
        _validate_synthesis(record, mode, families, conjectures, state)
    elif phase != "merge":
        raise GateError(f"unsupported phase: {phase}")
    return {
        "mode": mode,
        "families": len(families),
        "conjectures": len(conjectures),
        "cohorts": len(state["cohorts"]),
        "packets": len(state["packet_by_id"]),
        "corrections": len(state["correction_by_id"]),
        "scouts_used": state["role_use"]["scout"],
        "innovators_used": state["role_use"]["innovator"],
        "critics_used": state["role_use"]["critic"],
    }


def _inside(path: Path, root: Path) -> bool:
    try:
        return os.path.commonpath(
            (os.path.normcase(str(path)), os.path.normcase(str(root)))
        ) == os.path.normcase(str(root))
    except ValueError:
        return False


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def load_record(path: Path, repo: Path) -> dict[str, Any]:
    root = (repo.resolve(strict=False) / "local_research").resolve(strict=False)
    resolved = path.resolve(strict=False)
    _require(_inside(resolved, root), "record path is outside the registered local_research root")
    _require(resolved.is_file(), "record path is not a file")
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read campaign record: {exc}") from exc
    return _mapping(payload, "record")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check")
    check.add_argument("--record", type=Path, required=True)
    check.add_argument(
        "--phase",
        choices=("intake", "merge", "next-cohort", "synthesis"),
        required=True,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        record = load_record(args.record, _repo_root())
        detail = validate_record(record, args.phase)
    except GateError as exc:
        print(
            json.dumps(
                {
                    "status": "RESEARCH_PORTFOLIO_GATE_ERROR",
                    "phase": getattr(args, "phase", None),
                    "error": str(exc),
                },
                sort_keys=True,
            )
        )
        return 2
    print(
        json.dumps(
            {
                "status": "RESEARCH_PORTFOLIO_GATE_OK",
                "phase": args.phase,
                **detail,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
