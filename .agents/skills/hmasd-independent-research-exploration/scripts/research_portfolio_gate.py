#!/usr/bin/env python3
"""Mechanical gate for HMASD independent advisory research records."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


MODES = {"evidence_review", "algorithm_inspiration_campaign", "candidate_validation"}
PHASES = ("intake", "absorption", "cycle", "convergence")
STAGE_ORDER = (
    "source_absorption",
    "innovation",
    "principles_review",
    "adversarial_review",
    "portfolio_update",
)
STAGE_ROLE = {
    "source_absorption": "scout",
    "innovation": "innovator",
    "principles_review": "principles_analyst",
    "adversarial_review": "critic",
}
PACKET_KIND = {
    "scout": "SOURCE_RESULT_PACKET",
    "innovator": "ALGORITHM_INSPIRATION_PACKET",
    "principles_analyst": "RL_PRINCIPLE_ANALYSIS_PACKET",
    "critic": "CRITIC_ASSESSMENT_PACKET",
}
OPPORTUNITY_KINDS = {
    "new_mechanism",
    "transfer",
    "combination",
    "important_correction",
    "subdirection_split",
    "cross_direction_inspiration",
}
CANDIDATE_STATUSES = {"retained", "parked", "validation_ready", "rejected"}
CONVERGENCE_CRITERIA = {
    "corpus_absorbed",
    "retained_principles_complete",
    "recommended_criticism_complete",
    "actionable_corrections_closed",
    "no_new_mechanism_opportunity",
    "no_transfer_opportunity",
    "no_combination_opportunity",
    "no_important_correction_opportunity",
    "no_subdirection_split_opportunity",
    "no_cross_direction_inspiration_opportunity",
}
RETIRED_KEYS = {
    "max_cohorts",
    "scout_parallel_limit",
    "innovator_parallel_limit",
    "critic_parallel_limit",
    "principles_analyst_parallel_limit",
    "unique_winner",
}


class GateError(ValueError):
    pass


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
    _require(isinstance(value, str) and bool(value.strip()), f"{name} must be nonempty text")
    return value.strip()


def _text_list(value: Any, name: str, *, nonempty: bool = True) -> list[str]:
    items = _list(value, name)
    if nonempty:
        _require(bool(items), f"{name} must not be empty")
    result = [_text(item, f"{name}[{index}]") for index, item in enumerate(items)]
    _require(len(result) == len(set(result)), f"{name} contains duplicates")
    return result


def _integer(value: Any, name: str, minimum: int = 0) -> int:
    _require(isinstance(value, int) and not isinstance(value, bool), f"{name} must be an integer")
    _require(value >= minimum, f"{name} must be >= {minimum}")
    return value


def _unique(items: list[Any], key: str, name: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(items):
        item = _mapping(raw, f"{name}[{index}]")
        identity = _text(item.get(key), f"{name}[{index}].{key}")
        _require(identity not in result, f"duplicate {name} identity: {identity}")
        result[identity] = item
    return result


def _forbid_retired_keys(value: Any, path: str = "record") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _require(key not in RETIRED_KEYS, f"{path} contains retired key: {key}")
            _forbid_retired_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _forbid_retired_keys(child, f"{path}[{index}]")


def _validate_intake(record: dict[str, Any]) -> str:
    _require(record.get("document_kind") == "independent_research_campaign_v3", "wrong document_kind")
    _forbid_retired_keys(record)
    intake = _mapping(record.get("intake"), "intake")
    mode = _text(intake.get("mode"), "intake.mode")
    _require(mode in MODES, f"unsupported mode: {mode}")
    for field in ("direction_or_question", "mission_link", "authorized_source_boundary", "completion_meaning"):
        _text(intake.get(field), f"intake.{field}")
    _text_list(intake.get("exclusions"), "intake.exclusions")
    campaign = _mapping(record.get("campaign"), "campaign")
    for field in ("campaign_id", "user_authorization_id"):
        _text(campaign.get(field), f"campaign.{field}")
    _require(campaign.get("assignment_policy") == "exact_work_roster", "wrong assignment_policy")
    _require(
        campaign.get("runtime_concurrency") == "available_native_capacity",
        "wrong runtime_concurrency",
    )
    _require(
        campaign.get("resource_policy") == "explicit_work_rosters_plus_recorded_convergence",
        "wrong resource_policy",
    )
    ceiling = campaign.get("optional_total_assignment_ceiling")
    _require(
        ceiling is None or (isinstance(ceiling, int) and not isinstance(ceiling, bool) and ceiling > 0),
        "optional_total_assignment_ceiling must be null or positive",
    )
    return mode


def _validate_assignments_and_packets(
    record: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    assignments = _unique(_list(record.get("assignments"), "assignments"), "assignment_id", "assignments")
    packets = _unique(_list(record.get("packets"), "packets"), "packet_id", "packets")
    packet_by_assignment: dict[str, dict[str, Any]] = {}
    for packet_id, packet in packets.items():
        assignment_id = _text(packet.get("assignment_id"), f"packet {packet_id}.assignment_id")
        _require(assignment_id in assignments, f"packet {packet_id} has unknown assignment")
        _require(assignment_id not in packet_by_assignment, f"assignment {assignment_id} has multiple packets")
        _require(packet.get("status") == "terminal", f"packet {packet_id} is not terminal")
        packet_by_assignment[assignment_id] = packet

    for assignment_id, assignment in assignments.items():
        role = _text(assignment.get("role"), f"assignment {assignment_id}.role")
        _require(role in PACKET_KIND, f"assignment {assignment_id} has unsupported role")
        status = _text(assignment.get("status"), f"assignment {assignment_id}.status")
        _require(status in {"terminal", "operational_failure"}, f"assignment {assignment_id} has bad status")
        if status == "terminal":
            _require(assignment_id in packet_by_assignment, f"terminal assignment {assignment_id} has no packet")
            _require(
                packet_by_assignment[assignment_id].get("packet_kind") == PACKET_KIND[role],
                f"assignment {assignment_id} has wrong packet kind",
            )
        else:
            _require(assignment_id not in packet_by_assignment, f"failed assignment {assignment_id} has a packet")
            _require(assignment.get("scientific_output") is False, f"failed assignment {assignment_id} has output")
            _text(assignment.get("failure_signature"), f"assignment {assignment_id}.failure_signature")
    return assignments, packets


def _validate_corpus(
    record: dict[str, Any],
    assignments: dict[str, dict[str, Any]],
    packets: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    corpus = _mapping(record.get("corpus"), "corpus")
    _integer(corpus.get("version"), "corpus.version", 1)
    manifest = _unique(_list(corpus.get("manifest"), "corpus.manifest"), "source_id", "corpus.manifest")
    _require(bool(manifest), "corpus manifest must not be empty")
    for source_id, source in manifest.items():
        _text(source.get("immutable_identity"), f"source {source_id}.immutable_identity")
        _text(source.get("inclusion_reason"), f"source {source_id}.inclusion_reason")
        owner = _text(source.get("owner_assignment_id"), f"source {source_id}.owner_assignment_id")
        _require(owner in assignments, f"source {source_id} has unknown owner")
        assignment = assignments[owner]
        _require(assignment.get("role") == "scout", f"source {source_id} owner is not a Scout")
        _require(assignment.get("phase") == "source_absorption", f"source {source_id} owner has wrong phase")
        source_ids = _text_list(assignment.get("source_ids"), f"assignment {owner}.source_ids")
        _require(source_id in source_ids, f"source {source_id} is absent from owner assignment")
        if assignment.get("status") == "terminal":
            packet_id = next(pid for pid, packet in packets.items() if packet.get("assignment_id") == owner)
            packet_sources = _text_list(packets[packet_id].get("source_ids"), f"packet {packet_id}.source_ids")
            _require(source_id in packet_sources, f"packet {packet_id} omits source {source_id}")

    previous = 1
    for index, raw in enumerate(_list(corpus.get("deltas"), "corpus.deltas")):
        delta = _mapping(raw, f"corpus.deltas[{index}]")
        version = _integer(delta.get("version"), f"corpus.deltas[{index}].version", 2)
        _require(version > previous, "corpus delta versions must increase")
        previous = version
        _text(delta.get("reason"), f"corpus.deltas[{index}].reason")
        _text_list(delta.get("added_source_ids"), f"corpus.deltas[{index}].added_source_ids")
        _require(delta.get("inside_authorized_source_boundary") is True, "corpus delta expands source boundary")
    return manifest


def _validate_cycles(
    record: dict[str, Any],
    assignments: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    cycles = _list(record.get("cycles"), "cycles")
    _require(bool(cycles), "algorithm inspiration requires a cycle")
    seen: set[str] = set()
    previous_index = 0
    output: list[dict[str, Any]] = []
    for cycle_pos, raw in enumerate(cycles):
        cycle = _mapping(raw, f"cycles[{cycle_pos}]")
        cycle_id = _text(cycle.get("cycle_id"), f"cycles[{cycle_pos}].cycle_id")
        _require(cycle_id not in seen, f"duplicate cycle: {cycle_id}")
        seen.add(cycle_id)
        index = _integer(cycle.get("index"), f"cycle {cycle_id}.index", 1)
        _require(index > previous_index, "cycle indexes must increase")
        previous_index = index
        stages = _list(cycle.get("stages"), f"cycle {cycle_id}.stages")
        names = [_text(_mapping(stage, "stage").get("stage"), "stage.name") for stage in stages]
        _require(len(names) == len(set(names)), f"cycle {cycle_id} repeats a stage")
        _require(all(name in STAGE_ORDER for name in names), f"cycle {cycle_id} has unknown stage")
        positions = [STAGE_ORDER.index(name) for name in names]
        _require(positions == sorted(positions), f"cycle {cycle_id} violates phase order")
        if index == 1:
            _require(tuple(names) == STAGE_ORDER, "first cycle must contain all ordered stages")
        else:
            _require(names and names[-1] == "portfolio_update", "later cycle must end in portfolio_update")
            for required in ("innovation", "principles_review", "adversarial_review"):
                _require(required in names, f"later cycle lacks {required}")
        for raw_stage in stages:
            stage = _mapping(raw_stage, f"cycle {cycle_id}.stage")
            name = _text(stage.get("stage"), f"cycle {cycle_id}.stage.name")
            _require(stage.get("complete") is True, f"cycle {cycle_id} stage {name} is incomplete")
            assignment_ids = _text_list(
                stage.get("assignment_ids"),
                f"cycle {cycle_id}.{name}.assignment_ids",
                nonempty=name != "portfolio_update",
            )
            for assignment_id in assignment_ids:
                _require(assignment_id in assignments, f"cycle {cycle_id} references unknown assignment")
                assignment = assignments[assignment_id]
                _require(assignment.get("cycle_id") == cycle_id, f"assignment {assignment_id} has wrong cycle")
                _require(assignment.get("phase") == name, f"assignment {assignment_id} has wrong phase")
                if name in STAGE_ROLE:
                    _require(assignment.get("role") == STAGE_ROLE[name], f"assignment {assignment_id} has wrong role")
        output.append(cycle)
    return output


def _validate_portfolio(
    record: dict[str, Any],
    packets: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    portfolio = _unique(_list(record.get("portfolio"), "portfolio"), "candidate_id", "portfolio")
    for candidate_id, candidate in portfolio.items():
        _require(candidate.get("status") in CANDIDATE_STATUSES, f"candidate {candidate_id} has bad status")
        for field in ("target_problem", "mechanism", "learning_driver"):
            _text(candidate.get(field), f"candidate {candidate_id}.{field}")
        source_packets = _text_list(candidate.get("source_result_packet_ids"), f"candidate {candidate_id}.sources")
        for packet_id in source_packets:
            _require(packet_id in packets, f"candidate {candidate_id} has unknown source packet")
            _require(packets[packet_id].get("packet_kind") == "SOURCE_RESULT_PACKET", "wrong source packet kind")
        parents = _text_list(candidate.get("parent_candidate_ids"), f"candidate {candidate_id}.parents", nonempty=False)
        for parent in parents:
            _require(parent in portfolio, f"candidate {candidate_id} has unknown parent")
        principles = _text_list(
            candidate.get("principles_packet_ids"),
            f"candidate {candidate_id}.principles",
            nonempty=False,
        )
        critics = _text_list(candidate.get("critic_packet_ids"), f"candidate {candidate_id}.critics", nonempty=False)
        for packet_id in principles:
            _require(
                packet_id in packets and packets[packet_id].get("packet_kind") == "RL_PRINCIPLE_ANALYSIS_PACKET",
                f"candidate {candidate_id} has invalid principles packet",
            )
            _require(
                candidate_id in _text_list(packets[packet_id].get("candidate_ids"), f"packet {packet_id}.candidates"),
                f"principles packet {packet_id} omits candidate",
            )
        for packet_id in critics:
            _require(
                packet_id in packets and packets[packet_id].get("packet_kind") == "CRITIC_ASSESSMENT_PACKET",
                f"candidate {candidate_id} has invalid critic packet",
            )
            prerequisite = _text_list(
                packets[packet_id].get("principles_packet_ids"),
                f"packet {packet_id}.principles",
            )
            _require(set(prerequisite).issubset(set(principles)), f"critic {packet_id} lacks principles prerequisite")
        if candidate.get("recommended") is True:
            _require(bool(principles), f"recommended candidate {candidate_id} lacks principles review")
            _require(bool(critics), f"recommended candidate {candidate_id} lacks adversarial review")
    return portfolio


def _validate_opportunities(
    record: dict[str, Any],
    portfolio: dict[str, dict[str, Any]],
    manifest: dict[str, dict[str, Any]],
    assignments: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    opportunities = _unique(_list(record.get("opportunities"), "opportunities"), "opportunity_id", "opportunities")
    for opportunity_id, item in opportunities.items():
        kind = _text(item.get("kind"), f"opportunity {opportunity_id}.kind")
        _require(kind in OPPORTUNITY_KINDS, f"opportunity {opportunity_id} has unsupported kind")
        _require(item.get("status") in {"planned", "completed", "parked"}, f"opportunity {opportunity_id} has bad status")
        for field in ("material_delta", "expected_portfolio_effect", "required_role", "completion_condition"):
            _text(item.get(field), f"opportunity {opportunity_id}.{field}")
        parents = _text_list(item.get("parent_candidate_ids"), f"opportunity {opportunity_id}.parents", nonempty=False)
        sources = _text_list(item.get("source_ids"), f"opportunity {opportunity_id}.sources", nonempty=False)
        for parent in parents:
            _require(parent in portfolio, f"opportunity {opportunity_id} has unknown parent")
        for source in sources:
            _require(source in manifest, f"opportunity {opportunity_id} has unknown source")
        if kind == "transfer":
            _text(item.get("source_context"), f"opportunity {opportunity_id}.source_context")
            _text(item.get("target_context"), f"opportunity {opportunity_id}.target_context")
            _text_list(item.get("changed_assumptions"), f"opportunity {opportunity_id}.changed_assumptions")
        elif kind == "combination":
            _require(len(parents) >= 2, f"combination {opportunity_id} needs two parents")
            _text(item.get("new_interaction"), f"opportunity {opportunity_id}.new_interaction")
        elif kind == "subdirection_split":
            _require(len(parents) == 1, f"split {opportunity_id} needs one parent")
            _text(
                item.get("distinct_assumption_driver_or_prediction"),
                f"opportunity {opportunity_id}.distinct_assumption_driver_or_prediction",
            )
        planned = _text_list(
            item.get("planned_assignment_ids"),
            f"opportunity {opportunity_id}.planned_assignments",
            nonempty=item.get("status") == "planned",
        )
        for assignment_id in planned:
            _require(assignment_id in assignments, f"opportunity {opportunity_id} has unknown assignment")
            _require(assignments[assignment_id].get("opportunity_id") == opportunity_id, "assignment/opportunity mismatch")
    return opportunities


def _validate_candidate_validation(record: dict[str, Any]) -> None:
    candidate = _mapping(record.get("validation_candidate"), "validation_candidate")
    for field in (
        "candidate_id",
        "precise_defect",
        "mechanism",
        "algorithm_delta",
        "strongest_simple_explanation",
        "separating_prediction",
    ):
        _text(candidate.get(field), f"validation_candidate.{field}")
    _require(
        candidate.get("methodology_reference") == "research-methodology.md",
        "candidate validation requires research-methodology.md",
    )


def _validate_convergence(
    record: dict[str, Any],
    portfolio: dict[str, dict[str, Any]],
    opportunities: dict[str, dict[str, Any]],
) -> None:
    convergence = _mapping(record.get("convergence"), "convergence")
    status = _text(convergence.get("status"), "convergence.status")
    _require(
        status in {"ACTIVE", "CONVERGED", "PARTIAL_CAMPAIGN_RESOURCE_BOUND", "EXTERNAL_BOUNDARY"},
        "unsupported convergence status",
    )
    criteria = _mapping(convergence.get("criteria"), "convergence.criteria")
    _require(set(criteria) == CONVERGENCE_CRITERIA, "convergence criteria set is incomplete")
    _require(all(isinstance(value, bool) for value in criteria.values()), "convergence criteria must be booleans")
    _text_list(convergence.get("basis"), "convergence.basis")
    if status == "CONVERGED":
        _require(all(criteria.values()), "CONVERGED requires every criterion")
        _require(all(item.get("status") in {"completed", "parked"} for item in opportunities.values()), "planned opportunity remains")
        for candidate_id, candidate in portfolio.items():
            if candidate.get("status") in {"retained", "validation_ready"}:
                _require(bool(candidate.get("principles_packet_ids")), f"candidate {candidate_id} lacks principles review")
            if candidate.get("recommended") is True:
                _require(bool(candidate.get("critic_packet_ids")), f"candidate {candidate_id} lacks adversarial review")
    elif status == "PARTIAL_CAMPAIGN_RESOURCE_BOUND":
        _text(convergence.get("resource_boundary"), "convergence.resource_boundary")
    elif status == "EXTERNAL_BOUNDARY":
        _text(convergence.get("external_boundary"), "convergence.external_boundary")


def validate_record(record: dict[str, Any], phase: str) -> dict[str, Any]:
    _require(phase in PHASES, f"unsupported phase: {phase}")
    mode = _validate_intake(record)
    if phase == "intake":
        return {"mode": mode}

    assignments, packets = _validate_assignments_and_packets(record)
    if mode == "candidate_validation":
        _validate_candidate_validation(record)
        return {"mode": mode, "assignments": len(assignments), "packets": len(packets)}

    manifest = _validate_corpus(record, assignments, packets)
    if mode == "evidence_review":
        return {"mode": mode, "sources": len(manifest), "assignments": len(assignments), "packets": len(packets)}

    cycles = _validate_cycles(record, assignments)
    if phase == "absorption":
        _require(
            _mapping(cycles[0]["stages"][0], "first stage").get("stage") == "source_absorption",
            "first campaign stage is not source_absorption",
        )
        return {"mode": mode, "sources": len(manifest), "assignments": len(assignments)}

    portfolio = _validate_portfolio(record, packets)
    opportunities = _validate_opportunities(record, portfolio, manifest, assignments)
    if phase == "convergence":
        _validate_convergence(record, portfolio, opportunities)
    return {
        "mode": mode,
        "sources": len(manifest),
        "cycles": len(cycles),
        "assignments": len(assignments),
        "packets": len(packets),
        "candidates": len(portfolio),
        "opportunities": len(opportunities),
    }


def _inside(path: Path, root: Path) -> bool:
    try:
        return os.path.commonpath((os.path.normcase(str(path)), os.path.normcase(str(root)))) == os.path.normcase(str(root))
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
    check.add_argument("--phase", choices=PHASES, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        record = load_record(args.record, _repo_root())
        detail = validate_record(record, args.phase)
    except GateError as exc:
        print(json.dumps({"status": "RESEARCH_PORTFOLIO_GATE_ERROR", "phase": getattr(args, "phase", None), "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"status": "RESEARCH_PORTFOLIO_GATE_OK", "phase": args.phase, **detail}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
