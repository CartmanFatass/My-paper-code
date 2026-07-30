"""Mechanical gate for HMASD independent-research records.

The gate checks structure, identity and ordering only. It does not judge
scientific novelty, correctness or project authority, and it never writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


MODES = {"evidence_review", "scientific_innovation"}
FAMILY_STATUSES = {"live", "blocked", "parked", "contradicted"}
CRITIC_DISPOSITIONS = {"supported", "weakened", "contradicted", "unresolved"}
CRITIC_STATUSES = CRITIC_DISPOSITIONS | {"conflicting", "not_selected"}
CONCRETE_OUTPUTS = {
    "lemma",
    "construction",
    "equation",
    "counterexample",
    "falsifiable_prediction",
}
REOPEN_BASES = {"new_mechanism", "new_invariant", "new_construction"}


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


def _unique(items: list[dict[str, Any]], key: str, name: str) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for item in items:
        identity = _text(item.get(key), f"{name}.{key}")
        _require(identity not in output, f"duplicate {name}.{key}: {identity}")
        output[identity] = item
    return output


def _validate_intake(record: dict[str, Any]) -> str:
    _require(
        record.get("document_kind") == "independent_research_record_v1",
        "document_kind must be independent_research_record_v1",
    )
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
    return mode


def _validate_families(record: dict[str, Any], mode: str) -> dict[str, dict[str, Any]]:
    raw = record.get("families", [])
    families = [_mapping(item, "families item") for item in _list(raw, "families")]
    if mode == "evidence_review":
        _require(not families, "evidence_review must not create an approach-family registry")
        return {}
    _require(bool(families), "scientific_innovation requires approach families")
    by_id = _unique(families, "family_id", "family")
    mechanisms: set[str] = set()
    for family_id, family in by_id.items():
        mechanism = _text(family.get("core_mechanism"), f"family {family_id}.core_mechanism")
        normalized = " ".join(mechanism.lower().split())
        _require(normalized not in mechanisms, "approach families duplicate a core mechanism")
        mechanisms.add(normalized)
        for field in (
            "exact_claim",
            "evidence_baseline",
            "strongest_support",
            "strongest_counterexample",
            "current_gap",
            "reopen_condition",
        ):
            _text(family.get(field), f"family {family_id}.{field}")
        critic_status = _text(family.get("critic_status"), f"family {family_id}.critic_status")
        _require(critic_status in CRITIC_STATUSES, f"invalid family critic_status: {critic_status}")
        _require(
            family["evidence_baseline"] == record["intake"]["evidence_baseline"],
            "approach-family evidence baseline differs from intake",
        )
        status = _text(family.get("status"), f"family {family_id}.status")
        _require(status in FAMILY_STATUSES, f"invalid family status: {status}")
        _text_list(
            family.get("innovator_packet_ids", []),
            f"family {family_id}.innovator_packet_ids",
            nonempty=False,
        )
    return by_id


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


def _validate_evidence_packet(assignment: dict[str, Any], packet: dict[str, Any]) -> None:
    _require(packet.get("packet_kind") == "SCOUT_EVIDENCE_PACKET", "wrong evidence packet kind")
    axis = _text(assignment.get("evidence_axis_id"), "assignment.evidence_axis_id")
    _require(packet.get("evidence_axis_id") == axis, "evidence-axis identity mismatch")
    assigned_sources = set(_text_list(assignment.get("source_ids"), "assignment.source_ids"))
    packet_sources = set(_text_list(packet.get("source_ids"), "packet.source_ids"))
    _require(packet_sources <= assigned_sources, "evidence packet expands its source ownership")
    allowed_bindings = {
        (
            str(binding["source_identity"]),
            str(binding["evidence_type"]),
            str(binding["evidence_path"]),
        )
        for binding in assignment["source_bindings"]
    }
    rows = [
        _mapping(item, "evidence_rows item")
        for item in _list(packet.get("evidence_rows"), "packet.evidence_rows")
    ]
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
        ):
            _text(row.get(field), f"evidence row.{field}")
        _require(row["claim_id"] == assignment["claim_id"], "evidence row claim identity mismatch")
        _require(row["source_identity"] in packet_sources, "evidence row source is outside the packet source set")
        _require(row["evidence_type"] in {"json", "pdf"}, "evidence row type must be json or pdf")
        _require(Path(row["evidence_path"]).is_absolute(), "evidence row path must be absolute")
        _require(
            (row["source_identity"], row["evidence_type"], row["evidence_path"])
            in allowed_bindings,
            "evidence row does not match an assigned source binding",
        )
        confidence = row.get("confidence")
        _require(
            isinstance(confidence, (int, float))
            and not isinstance(confidence, bool)
            and 0 <= confidence <= 1,
            "invalid evidence confidence",
        )


def _validate_direction_packet(assignment: dict[str, Any], packet: dict[str, Any]) -> None:
    _require(packet.get("packet_kind") == "RESEARCH_DIRECTION_PACKET", "wrong direction packet kind")
    family_id = _text(assignment.get("family_id"), "assignment.family_id")
    _require(packet.get("family_id") == family_id, "approach-family identity mismatch")
    _require(packet.get("core_mechanism") == assignment.get("core_mechanism"), "core mechanism changed in packet")
    _require(packet.get("exact_claim") == assignment.get("exact_claim"), "exact claim changed in packet")
    _require(packet.get("mission_link") == assignment.get("mission_link"), "mission link changed in packet")
    _require(
        packet.get("evidence_baseline") == assignment.get("evidence_baseline"),
        "evidence baseline changed in packet",
    )
    for field in (
        "derivation_or_construction",
        "novelty_delta",
        "strongest_internal_counterexample",
        "missing_lemma_or_interface",
        "minimal_discriminator",
    ):
        _text(packet.get(field), f"direction packet.{field}")
    for field in (
        "assumptions",
        "evidence_dependencies",
        "alternate_explanations",
        "failure_boundaries",
        "falsifiable_predictions",
    ):
        _text_list(packet.get(field), f"direction packet.{field}")
    _require(
        assignment["evidence_baseline"] in packet["evidence_dependencies"],
        "direction packet does not depend on its frozen evidence baseline",
    )
    outputs = [
        _mapping(item, "concrete_outputs item")
        for item in _list(packet.get("concrete_outputs"), "direction packet.concrete_outputs")
    ]
    _require(bool(outputs), "direction packet has no concrete output")
    for output in outputs:
        kind = _text(output.get("kind"), "concrete output.kind")
        _require(kind in CONCRETE_OUTPUTS, f"invalid concrete output kind: {kind}")
        _text(output.get("content"), "concrete output.content")


def _validate_wave(
    record: dict[str, Any],
    mode: str,
    families: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], int, set[str]]:
    wave = _mapping(record.get("wave"), "wave")
    _text(wave.get("wave_id"), "wave.wave_id")
    assignments = [
        _mapping(item, "wave.assignments item")
        for item in _list(wave.get("assignments"), "wave.assignments")
    ]
    _require(1 <= len(assignments) <= 4, "a wave requires 1..4 assignments")
    by_assignment = _unique(assignments, "assignment_id", "assignment")
    source_owners: dict[str, str] = {}
    family_owners: set[str] = set()
    mechanisms: set[str] = set()
    for assignment_id, assignment in by_assignment.items():
        _text(assignment.get("claim_id"), f"assignment {assignment_id}.claim_id")
        _text_list(assignment.get("semantic_traps"), f"assignment {assignment_id}.semantic_traps")
        if mode == "evidence_review":
            _text(assignment.get("evidence_axis_id"), f"assignment {assignment_id}.evidence_axis_id")
            assignment_sources = _text_list(
                assignment.get("source_ids"),
                f"assignment {assignment_id}.source_ids",
            )
            for source in assignment_sources:
                _require(source not in source_owners, f"duplicate evidence source ownership: {source}")
                source_owners[source] = assignment_id
            bindings = [
                _mapping(item, f"assignment {assignment_id}.source_bindings item")
                for item in _list(
                    assignment.get("source_bindings"),
                    f"assignment {assignment_id}.source_bindings",
                )
            ]
            _require(bool(bindings), f"assignment {assignment_id}.source_bindings must not be empty")
            bound_sources: set[str] = set()
            binding_tuples: set[tuple[str, str, str]] = set()
            for binding in bindings:
                source_identity = _text(
                    binding.get("source_identity"),
                    f"assignment {assignment_id}.source binding.source_identity",
                )
                evidence_type = _text(
                    binding.get("evidence_type"),
                    f"assignment {assignment_id}.source binding.evidence_type",
                )
                evidence_path = _text(
                    binding.get("evidence_path"),
                    f"assignment {assignment_id}.source binding.evidence_path",
                )
                _require(source_identity in assignment_sources, "source binding names an unassigned source")
                _require(evidence_type in {"json", "pdf"}, "source binding type must be json or pdf")
                _require(Path(evidence_path).is_absolute(), "source binding path must be absolute")
                binding_tuple = (source_identity, evidence_type, evidence_path)
                _require(binding_tuple not in binding_tuples, "duplicate source binding")
                binding_tuples.add(binding_tuple)
                bound_sources.add(source_identity)
            _require(bound_sources == set(assignment_sources), "source bindings do not cover assigned sources")
        else:
            family_id = _text(assignment.get("family_id"), f"assignment {assignment_id}.family_id")
            _require(family_id in families, f"assignment names unknown family: {family_id}")
            _require(family_id not in family_owners, f"duplicate approach-family assignment: {family_id}")
            family_owners.add(family_id)
            mechanism = _text(assignment.get("core_mechanism"), f"assignment {assignment_id}.core_mechanism")
            _require(mechanism == families[family_id]["core_mechanism"], "assignment mechanism differs from registry")
            normalized = " ".join(mechanism.lower().split())
            _require(normalized not in mechanisms, "innovation assignments duplicate a mechanism")
            mechanisms.add(normalized)
            _text(assignment.get("exact_claim"), f"assignment {assignment_id}.exact_claim")
            _require(
                assignment["exact_claim"] == families[family_id]["exact_claim"],
                "innovation assignment exact claim differs from its approach family",
            )
            intake = _mapping(record.get("intake"), "intake")
            mission_link = _text(assignment.get("mission_link"), f"assignment {assignment_id}.mission_link")
            _require(mission_link == intake["mission_link"], "innovation assignment mission link differs from intake")
            evidence_baseline = _text(
                assignment.get("evidence_baseline"),
                f"assignment {assignment_id}.evidence_baseline",
            )
            _require(
                evidence_baseline == intake["evidence_baseline"],
                "innovation assignment evidence baseline differs from intake",
            )
            purpose = _text(assignment.get("purpose"), f"assignment {assignment_id}.purpose")
            visibility = _text(
                assignment.get("favored_family_visibility"),
                f"assignment {assignment_id}.favored_family_visibility",
            )
            _require(purpose in {"develop", "challenge"}, "invalid innovation assignment purpose")
            expected_visibility = "named_for_challenge" if purpose == "challenge" else "withheld"
            _require(visibility == expected_visibility, "favored-family independence shielding failed")

    packets = [
        _mapping(item, "wave.packets item")
        for item in _list(wave.get("packets"), "wave.packets")
    ]
    by_packet_id = _unique(packets, "packet_id", "packet")
    by_packet_assignment: dict[str, dict[str, Any]] = {}
    for packet in packets:
        assignment_id = _text(packet.get("assignment_id"), "packet.assignment_id")
        _require(
            assignment_id not in by_packet_assignment,
            f"duplicate packet assignment_id: {assignment_id}",
        )
        by_packet_assignment[assignment_id] = packet

    terminal_failures = [
        _mapping(item, "wave.terminal_failures item")
        for item in _list(wave.get("terminal_failures", []), "wave.terminal_failures")
    ]
    by_failure_assignment = _unique(
        terminal_failures,
        "assignment_id",
        "terminal operational failure",
    )
    for assignment_id, failure in by_failure_assignment.items():
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
        _require(assignment_id in by_assignment, "terminal failure names an unknown assignment")
        _require(
            assignment_id not in by_packet_assignment,
            "an assignment cannot have both a packet and a terminal failure",
        )
        _text(failure.get("failure_signature"), "terminal operational failure.failure_signature")
        _require(
            failure.get("failure_kind") == "OPERATIONAL_FAILURE",
            "terminal operational failure kind must be OPERATIONAL_FAILURE",
        )
        _require(
            failure.get("status") == "terminal",
            "terminal operational failure status must be terminal",
        )
        retry_count = failure.get("unchanged_retry_count")
        _require(
            isinstance(retry_count, int) and not isinstance(retry_count, bool) and 0 <= retry_count <= 1,
            "terminal operational failure unchanged_retry_count must be 0 or 1",
        )
        _require(
            failure.get("scientific_output") is False,
            "terminal operational failure must declare scientific_output=false",
        )

    terminal_assignments = set(by_packet_assignment) | set(by_failure_assignment)
    complete = terminal_assignments == set(by_assignment) and all(
        packet.get("status") == "terminal" for packet in packets
    )
    if wave.get("cross_pollination_started") is True:
        _require(complete, "cross-pollination started before the merge barrier")
    _require(complete, "merge barrier is incomplete")
    for assignment_id, packet in by_packet_assignment.items():
        assignment = by_assignment[assignment_id]
        _require(packet.get("claim_id") == assignment.get("claim_id"), "claim identity mismatch")
        _validate_traps(assignment, packet)
        if mode == "evidence_review":
            _validate_evidence_packet(assignment, packet)
        else:
            _validate_direction_packet(assignment, packet)
            family_id = str(assignment["family_id"])
            registered_packets = set(families[family_id]["innovator_packet_ids"])
            _require(
                packet["packet_id"] in registered_packets,
                "direction packet is not registered to its approach family",
            )
    if mode == "scientific_innovation":
        actual_by_family: dict[str, set[str]] = {family_id: set() for family_id in families}
        for assignment_id, packet in by_packet_assignment.items():
            actual_by_family[str(by_assignment[assignment_id]["family_id"])].add(str(packet["packet_id"]))
        for family_id, family in families.items():
            registered = set(family["innovator_packet_ids"])
            _require(
                registered == actual_by_family[family_id],
                "approach-family packet registration differs from returned packet set",
            )
    return by_packet_id, packets, len(terminal_failures), terminal_assignments


def _validate_critics(
    record: dict[str, Any],
    mode: str,
    families: dict[str, dict[str, Any]],
    packet_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    critics = [
        _mapping(item, "critic_packets item")
        for item in _list(record.get("critic_packets", []), "critic_packets")
    ]
    _require(len(critics) <= 2, "at most two Critic packets are allowed")
    _unique(critics, "critic_assignment_id", "critic packet")
    dispositions_by_target: dict[str, set[str]] = {}
    for critic in critics:
        _require(
            critic.get("packet_kind") == "CRITIC_ASSESSMENT_PACKET",
            "wrong Critic packet kind",
        )
        _require(critic.get("status") == "terminal", "Critic packet status must be terminal")
        claim_id = _text(critic.get("claim_id"), "critic packet.claim_id")
        target_identity = _text(critic.get("target_identity"), "critic packet.target_identity")
        source_ids = _text_list(critic.get("source_packet_ids"), "critic packet.source_packet_ids")
        _require(set(source_ids) <= set(packet_by_id), "Critic packet names an unknown source packet")
        source_packets = [packet_by_id[source_id] for source_id in source_ids]
        _require(
            all(packet["claim_id"] == claim_id for packet in source_packets),
            "Critic claim identity differs from its source packets",
        )
        target_field = "evidence_axis_id" if mode == "evidence_review" else "family_id"
        _require(
            all(packet[target_field] == target_identity for packet in source_packets),
            "Critic target identity differs from its source packets",
        )
        disposition = _text(critic.get("disposition"), "critic packet.disposition")
        _require(disposition in CRITIC_DISPOSITIONS, "invalid Critic disposition")
        if mode == "scientific_innovation":
            _require(target_identity in families, "Critic targets an unknown approach family")
            dispositions_by_target.setdefault(target_identity, set()).add(disposition)
        _text(critic.get("correction"), "critic packet.correction")
        _text_list(critic.get("checklist_results"), "critic packet.checklist_results")
    if mode == "scientific_innovation":
        for family_id, family in families.items():
            dispositions = dispositions_by_target.get(family_id, set())
            if not dispositions:
                expected = "not_selected"
            else:
                expected = next(iter(dispositions)) if len(dispositions) == 1 else "conflicting"
            _require(
                family["critic_status"] == expected,
                "approach-family critic_status differs from actual Critic packet set",
            )
    return critics


def _additional_wave_fingerprint(admission: dict[str, Any]) -> str:
    payload = {
        "prior_wave_id": _text(admission.get("prior_wave_id"), "additional_wave_admission.prior_wave_id"),
        "next_wave_id": _text(admission.get("next_wave_id"), "additional_wave_admission.next_wave_id"),
        "prior_terminal_assignment_ids": sorted(
            _text_list(
                admission.get("prior_terminal_assignment_ids"),
                "additional_wave_admission.prior_terminal_assignment_ids",
            )
        ),
        "prior_terminal_packet_ids": sorted(
            _text_list(
                admission.get("prior_terminal_packet_ids"),
                "additional_wave_admission.prior_terminal_packet_ids",
                nonempty=False,
            )
        ),
        "target_family_id": _text(
            admission.get("target_family_id"),
            "additional_wave_admission.target_family_id",
        ),
        "basis": _text(admission.get("basis"), "additional_wave_admission.basis"),
        "novelty_statement": _text(
            admission.get("novelty_statement"),
            "additional_wave_admission.novelty_statement",
        ),
        "expected_disposition_change": _text(
            admission.get("expected_disposition_change"),
            "additional_wave_admission.expected_disposition_change",
        ),
        "innovator_budget": admission.get("innovator_budget"),
        "critic_budget": admission.get("critic_budget"),
        "stop_condition": _text(
            admission.get("stop_condition"),
            "additional_wave_admission.stop_condition",
        ),
    }
    canonical = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_additional_wave(
    record: dict[str, Any],
    mode: str,
    families: dict[str, dict[str, Any]],
    terminal_assignment_ids: set[str],
    terminal_packet_ids: set[str],
) -> None:
    _require(mode == "scientific_innovation", "evidence_review has no additional wave")
    admission = _mapping(record.get("additional_wave_admission"), "additional_wave_admission")
    wave = _mapping(record.get("wave"), "wave")
    prior_wave_id = _text(admission.get("prior_wave_id"), "additional_wave_admission.prior_wave_id")
    next_wave_id = _text(admission.get("next_wave_id"), "additional_wave_admission.next_wave_id")
    _require(prior_wave_id == wave["wave_id"], "additional wave names the wrong prior wave")
    _require(next_wave_id != prior_wave_id, "additional wave must have a new wave identity")
    recorded_assignment_ids = set(
        _text_list(
            admission.get("prior_terminal_assignment_ids"),
            "additional_wave_admission.prior_terminal_assignment_ids",
        )
    )
    recorded_packet_ids = set(
        _text_list(
            admission.get("prior_terminal_packet_ids"),
            "additional_wave_admission.prior_terminal_packet_ids",
            nonempty=False,
        )
    )
    _require(
        recorded_assignment_ids == terminal_assignment_ids,
        "additional wave prior terminal assignment set mismatch",
    )
    _require(
        recorded_packet_ids == terminal_packet_ids,
        "additional wave prior terminal packet set mismatch",
    )
    family_id = _text(admission.get("target_family_id"), "additional_wave_admission.target_family_id")
    _require(family_id in families, "additional wave names an unknown family")
    basis = _text(admission.get("basis"), "additional_wave_admission.basis")
    _require(basis in REOPEN_BASES | {"underexplored_family"}, "invalid additional-wave basis")
    if families[family_id]["status"] == "blocked":
        _require(basis in REOPEN_BASES, "blocked family lacks a new mechanism, invariant or construction")
    _text(admission.get("novelty_statement"), "additional_wave_admission.novelty_statement")
    _text(
        admission.get("expected_disposition_change"),
        "additional_wave_admission.expected_disposition_change",
    )
    innovator_budget = admission.get("innovator_budget")
    critic_budget = admission.get("critic_budget")
    _require(
        isinstance(innovator_budget, int)
        and not isinstance(innovator_budget, bool)
        and 1 <= innovator_budget <= 4,
        "invalid Innovator budget",
    )
    _require(
        isinstance(critic_budget, int)
        and not isinstance(critic_budget, bool)
        and 0 <= critic_budget <= 2,
        "invalid Critic budget",
    )
    _text(admission.get("stop_condition"), "additional_wave_admission.stop_condition")
    _text(admission.get("user_confirmation"), "additional_wave_admission.user_confirmation")
    expected_fingerprint = _additional_wave_fingerprint(admission)
    _require(
        admission.get("admission_fingerprint") == expected_fingerprint,
        "additional-wave admission fingerprint mismatch",
    )
    _require(
        admission.get("user_confirmation_fingerprint") == expected_fingerprint,
        "user confirmation is not bound to the exact additional wave",
    )


def _validate_synthesis(record: dict[str, Any], mode: str, critics: list[dict[str, Any]]) -> None:
    synthesis = _mapping(record.get("synthesis"), "synthesis")
    claims = [
        _mapping(item, "synthesis.claims item")
        for item in _list(synthesis.get("claims"), "synthesis.claims")
    ]
    for critic in critics:
        matches = [
            claim
            for claim in claims
            if claim.get("claim_id") == critic["claim_id"]
            and claim.get("critic_assignment_id") == critic["critic_assignment_id"]
        ]
        _require(len(matches) == 1, "synthesis omits an exact Critic correction identity")
        claim = matches[0]
        _require(claim.get("disposition") == critic["disposition"], "synthesis changes a Critic disposition")
        _require(claim.get("correction") == critic["correction"], "synthesis changes exact Critic correction text")
    if mode == "scientific_innovation":
        _require(
            synthesis.get("automatic_formal_promotion") is False,
            "scientific innovation synthesis must not promote itself",
        )


def validate_record(record: dict[str, Any], phase: str) -> dict[str, Any]:
    mode = _validate_intake(record)
    families = _validate_families(record, mode)
    if phase == "intake":
        return {"mode": mode, "families": len(families)}
    packet_by_id, packets, terminal_failures, terminal_assignment_ids = _validate_wave(
        record,
        mode,
        families,
    )
    critics = _validate_critics(record, mode, families, packet_by_id)
    if phase == "additional-wave":
        _validate_additional_wave(
            record,
            mode,
            families,
            terminal_assignment_ids,
            set(packet_by_id),
        )
    elif phase == "synthesis":
        _validate_synthesis(record, mode, critics)
    elif phase != "merge":
        raise GateError(f"unsupported phase: {phase}")
    return {
        "mode": mode,
        "families": len(families),
        "packets": len(packets),
        "terminal_failures": terminal_failures,
        "critics": len(critics),
    }


def _inside(path: Path, root: Path) -> bool:
    try:
        return os.path.commonpath((os.path.normcase(str(path)), os.path.normcase(str(root)))) == os.path.normcase(str(root))
    except ValueError:
        return False


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def load_record(path: Path, repo: Path) -> dict[str, Any]:
    resolved_repo = repo.resolve(strict=False)
    root = (resolved_repo / "local_research").resolve(strict=False)
    resolved = path.resolve(strict=False)
    _require(_inside(resolved, root), "record path is outside the registered local_research root")
    _require(resolved.is_file(), "record path is not a file")
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read portfolio record: {exc}") from exc
    return _mapping(payload, "record")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check")
    check.add_argument("--record", type=Path, required=True)
    check.add_argument(
        "--phase",
        choices=("intake", "merge", "additional-wave", "synthesis"),
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
