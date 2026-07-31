#!/usr/bin/env python3
"""Build one direction packet and gate a reusable ordered review batch."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


class PacketError(ValueError):
    pass


def _is_below(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _one(items: list[dict[str, Any]], key: str, value: str, label: str) -> dict[str, Any]:
    matches = [item for item in items if item.get(key) == value]
    if len(matches) != 1:
        raise PacketError(f"expected exactly one {label} {value!r}, found {len(matches)}")
    return matches[0]


def _ids(value: Any, label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise PacketError(f"{label} must be a list of nonempty strings")
    if len(set(value)) != len(value):
        raise PacketError(f"{label} contains duplicate identities")
    return value


def build_payload(record: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    if record.get("document_kind") != "independent_research_campaign_v3":
        raise PacketError("campaign document_kind is not independent_research_campaign_v3")
    intake = record.get("intake")
    campaign = record.get("campaign")
    if not isinstance(intake, dict) or intake.get("mode") != "algorithm_inspiration_campaign":
        raise PacketError("campaign mode is not algorithm_inspiration_campaign")
    if not isinstance(campaign, dict) or not campaign.get("campaign_id"):
        raise PacketError("campaign identity is missing")
    if not record.get("workflow_commit"):
        raise PacketError("workflow_commit is missing")

    portfolio = record.get("portfolio")
    packets = record.get("packets")
    opportunities = record.get("opportunities", [])
    if not isinstance(portfolio, list) or not isinstance(packets, list):
        raise PacketError("portfolio or packets is not a list")
    if not isinstance(opportunities, list):
        raise PacketError("opportunities is not a list")

    candidate = _one(portfolio, "candidate_id", candidate_id, "candidate")
    if candidate.get("status") != "validation_ready":
        raise PacketError("only a validation_ready candidate may enter direction audit")

    parent_ids = _ids(candidate.get("parent_candidate_ids"), "parent_candidate_ids")
    source_ids = _ids(candidate.get("source_result_packet_ids"), "source_result_packet_ids")
    lineage_ids: list[str] = []
    inspiration_id = candidate.get("inspiration_packet_id")
    if not isinstance(inspiration_id, str) or not inspiration_id:
        raise PacketError("inspiration_packet_id is missing")
    lineage_ids.append(inspiration_id)
    for field in ("revision_packet_ids", "principles_packet_ids", "critic_packet_ids"):
        lineage_ids.extend(_ids(candidate.get(field), field))
    if len(set(lineage_ids)) != len(lineage_ids):
        raise PacketError("candidate lineage contains duplicate packet identities")

    source_packets = [_one(packets, "packet_id", packet_id, "source packet") for packet_id in source_ids]
    if any(packet.get("packet_kind") != "SOURCE_RESULT_PACKET" for packet in source_packets):
        raise PacketError("source_result_packet_ids includes a non-source packet")
    lineage_packets = [_one(packets, "packet_id", packet_id, "lineage packet") for packet_id in lineage_ids]
    allowed_kinds = {
        "ALGORITHM_INSPIRATION_PACKET",
        "RL_PRINCIPLE_ANALYSIS_PACKET",
        "CRITIC_ASSESSMENT_PACKET",
    }
    if any(packet.get("packet_kind") not in allowed_kinds for packet in lineage_packets):
        raise PacketError("candidate lineage includes an unsupported packet kind")

    parents = [_one(portfolio, "candidate_id", parent_id, "parent candidate") for parent_id in parent_ids]
    selected_assignment_ids = {packet.get("assignment_id") for packet in lineage_packets}
    relevant_opportunities = []
    for opportunity in opportunities:
        opportunity_parents = set(_ids(opportunity.get("parent_candidate_ids"), "opportunity parent_candidate_ids"))
        planned = set(_ids(opportunity.get("planned_assignment_ids"), "planned_assignment_ids"))
        if opportunity_parents.intersection({candidate_id, *parent_ids}) or planned.intersection(selected_assignment_ids):
            relevant_opportunities.append(opportunity)

    return {
        "document_kind": "independent_research_direction_review_input_v1",
        "review_mode": "INDEPENDENT_RESEARCH_DIRECTION_AUDIT",
        "campaign_id": campaign["campaign_id"],
        "workflow_commit": record["workflow_commit"],
        "review_candidate_id": candidate_id,
        "scope": {
            "candidate_count": 1,
            "portfolio_comparison": "forbidden",
            "global_winner_selection": "forbidden",
            "code_compute_formal_effect": "none",
        },
        "campaign_boundary": {
            "direction_or_question": intake.get("direction_or_question"),
            "mission_link": intake.get("mission_link"),
            "authorized_source_boundary": intake.get("authorized_source_boundary"),
            "exclusions": intake.get("exclusions"),
        },
        "candidate": candidate,
        "parent_boundaries": parents,
        "source_result_packets": source_packets,
        "candidate_lineage_packets": lineage_packets,
        "candidate_relevant_opportunities": relevant_opportunities,
    }


def build_batch_payload(
    record: dict[str, Any], candidate_ids: list[str], question_contract_commit: str
) -> dict[str, Any]:
    ordered = _ids(candidate_ids, "ordered_candidate_ids")
    if not ordered:
        raise PacketError("ordered_candidate_ids must not be empty")
    if len(question_contract_commit) != 40 or any(
        character not in "0123456789abcdef" for character in question_contract_commit
    ):
        raise PacketError("question_contract_commit must be a lowercase 40-character Git identity")

    payloads = [build_payload(record, candidate_id) for candidate_id in ordered]
    campaign_id = payloads[0]["campaign_id"]
    campaign_workflow_commit = payloads[0]["workflow_commit"]
    if any(payload["campaign_id"] != campaign_id for payload in payloads):
        raise PacketError("batch candidates do not share one campaign identity")
    if any(payload["workflow_commit"] != campaign_workflow_commit for payload in payloads):
        raise PacketError("batch candidates do not share one campaign workflow identity")

    return {
        "document_kind": "independent_research_direction_review_batch_v1",
        "review_mode": "INDEPENDENT_RESEARCH_DIRECTION_AUDIT",
        "campaign_id": campaign_id,
        "campaign_workflow_commit": campaign_workflow_commit,
        "question_contract_commit": question_contract_commit,
        "ordered_candidate_ids": ordered,
        "candidate_count": len(ordered),
        "review_items": [
            {
                "index": index,
                "candidate_id": candidate_id,
                "directory": f"item_{index:03d}",
            }
            for index, candidate_id in enumerate(ordered, start=1)
        ],
        "policy": {
            "user_authorization_scope": "one_ordered_batch",
            "active_pro_turn_limit": 1,
            "candidates_per_pro_turn": 1,
            "reorder_or_skip": "forbidden",
            "portfolio_payload": "forbidden",
            "normal_direction_disposition_stops_batch": False,
            "transport_identity_format_or_archive_blocker_stops_batch": True,
            "formal_project_effect": "none",
        },
    }


def render_packet(payload: dict[str, Any], source_path: Path, source_sha256: str) -> bytes:
    manifest = {
        "source_campaign_path": source_path.as_posix(),
        "source_campaign_sha256": source_sha256,
        "campaign_id": payload["campaign_id"],
        "workflow_commit": payload["workflow_commit"],
        "review_candidate_id": payload["review_candidate_id"],
        "candidate_count": 1,
    }
    text = (
        "# Independent research single-direction review input\n\n"
        "## Identity manifest\n\n```json\n"
        + json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n```\n\n## Candidate-bounded campaign records\n\n```json\n"
        + json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n```\n"
    )
    return text.encode("utf-8")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _load_rendered(campaign_argument: str, candidate_id: str) -> tuple[dict[str, Any], Path, bytes]:
    repo = _repo_root()
    local_research = (repo / "local_research").resolve()
    pro_reviews = (local_research / "pro_reviews").resolve()
    campaign_path = Path(campaign_argument).resolve()
    if not _is_below(campaign_path, local_research) or _is_below(campaign_path, pro_reviews):
        raise PacketError("campaign must be under local_research and outside pro_reviews")
    source_bytes = campaign_path.read_bytes()
    try:
        record = json.loads(source_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PacketError(f"campaign is not valid UTF-8 JSON: {exc}") from exc
    payload = build_payload(record, candidate_id)
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    rendered = render_packet(payload, campaign_path.relative_to(repo), source_sha)
    return payload, campaign_path, rendered


def _load_campaign(campaign_argument: str) -> tuple[dict[str, Any], Path, bytes]:
    repo = _repo_root()
    local_research = (repo / "local_research").resolve()
    pro_reviews = (local_research / "pro_reviews").resolve()
    campaign_path = Path(campaign_argument).resolve()
    if not _is_below(campaign_path, local_research) or _is_below(campaign_path, pro_reviews):
        raise PacketError("campaign must be under local_research and outside pro_reviews")
    source_bytes = campaign_path.read_bytes()
    try:
        record = json.loads(source_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PacketError(f"campaign is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(record, dict):
        raise PacketError("campaign JSON root must be an object")
    return record, campaign_path, source_bytes


def _write_immutable(output_path: Path, content: bytes) -> None:
    if output_path.exists():
        raise PacketError("output already exists; review control artifacts are immutable")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(output_path.name + ".tmp")
    if temporary.exists():
        raise PacketError("temporary output already exists")
    temporary.write_bytes(content)
    os.replace(temporary, output_path)


def command_check(args: argparse.Namespace) -> int:
    payload, campaign_path, rendered = _load_rendered(args.campaign, args.candidate_id)
    receipt = {
        "status": "HMASD_DIRECTION_REVIEW_INPUT_CHECK_OK",
        "campaign_id": payload["campaign_id"],
        "workflow_commit": payload["workflow_commit"],
        "candidate_id": payload["review_candidate_id"],
        "source": str(campaign_path),
        "bytes": len(rendered),
        "sha256": hashlib.sha256(rendered).hexdigest(),
    }
    print(json.dumps(receipt, ensure_ascii=True, sort_keys=True))
    return 0


def command_build(args: argparse.Namespace) -> int:
    repo = _repo_root()
    pro_reviews = (repo / "local_research" / "pro_reviews").resolve()
    output_path = Path(args.output).resolve()
    if not _is_below(output_path, pro_reviews):
        raise PacketError("output must be under local_research/pro_reviews")
    payload, campaign_path, rendered = _load_rendered(args.campaign, args.candidate_id)
    if args.batch_manifest:
        manifest_path = Path(args.batch_manifest).resolve()
        if not _is_below(manifest_path, pro_reviews):
            raise PacketError("batch manifest must be under local_research/pro_reviews")
        manifest = _load_json_object(manifest_path, "batch manifest")
        next_item = batch_next_status(manifest, manifest_path.parent)
        if next_item.get("status") != "NEXT" or next_item.get("candidate_id") != args.candidate_id:
            raise PacketError("candidate is not the next ordered batch item")
        expected_output = manifest_path.parent / next_item["directory"] / "22_DIRECTION_INPUT.md"
        if output_path != expected_output:
            raise PacketError("batch direction output does not match the next item directory")
        expected_campaign = (repo / str(manifest.get("source_campaign_path"))).resolve()
        if campaign_path != expected_campaign:
            raise PacketError("batch direction campaign path does not match the manifest")
        campaign_bytes = campaign_path.read_bytes()
        if hashlib.sha256(campaign_bytes).hexdigest() != manifest.get("source_campaign_sha256"):
            raise PacketError("batch direction campaign bytes changed after manifest creation")
        if (
            payload["campaign_id"] != manifest.get("campaign_id")
            or payload["workflow_commit"] != manifest.get("campaign_workflow_commit")
        ):
            raise PacketError("batch direction campaign identity does not match the manifest")
    _write_immutable(output_path, rendered)
    receipt = {
        "status": "HMASD_DIRECTION_REVIEW_INPUT_OK",
        "campaign_id": payload["campaign_id"],
        "workflow_commit": payload["workflow_commit"],
        "candidate_id": payload["review_candidate_id"],
        "output": str(output_path),
        "bytes": len(rendered),
        "sha256": hashlib.sha256(rendered).hexdigest(),
    }
    print(json.dumps(receipt, ensure_ascii=True, sort_keys=True))
    return 0


def command_batch_plan(args: argparse.Namespace) -> int:
    repo = _repo_root()
    pro_reviews = (repo / "local_research" / "pro_reviews").resolve()
    output_path = Path(args.output).resolve()
    if not _is_below(output_path, pro_reviews):
        raise PacketError("batch manifest output must be under local_research/pro_reviews")
    record, campaign_path, source_bytes = _load_campaign(args.campaign)
    payload = build_batch_payload(record, args.candidate_id, args.question_contract_commit)
    payload["source_campaign_path"] = campaign_path.relative_to(repo).as_posix()
    payload["source_campaign_sha256"] = hashlib.sha256(source_bytes).hexdigest()
    rendered = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _write_immutable(output_path, rendered)
    receipt = {
        "status": "HMASD_DIRECTION_REVIEW_BATCH_PLAN_OK",
        "campaign_id": payload["campaign_id"],
        "campaign_workflow_commit": payload["campaign_workflow_commit"],
        "question_contract_commit": payload["question_contract_commit"],
        "candidate_count": payload["candidate_count"],
        "ordered_candidate_ids": payload["ordered_candidate_ids"],
        "output": str(output_path),
        "bytes": len(rendered),
        "sha256": hashlib.sha256(rendered).hexdigest(),
    }
    print(json.dumps(receipt, ensure_ascii=True, sort_keys=True))
    return 0


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PacketError(f"{label} is not readable UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise PacketError(f"{label} JSON root must be an object")
    return value


def batch_next_status(manifest: dict[str, Any], batch_root: Path) -> dict[str, Any]:
    if manifest.get("document_kind") != "independent_research_direction_review_batch_v1":
        raise PacketError("batch manifest document_kind is invalid")
    candidate_ids = _ids(manifest.get("ordered_candidate_ids"), "ordered_candidate_ids")
    if not candidate_ids or manifest.get("candidate_count") != len(candidate_ids):
        raise PacketError("batch manifest candidate count is invalid")
    items = manifest.get("review_items")
    if not isinstance(items, list) or len(items) != len(candidate_ids):
        raise PacketError("batch manifest review_items are invalid")
    expected_items = [
        {"index": index, "candidate_id": candidate_id, "directory": f"item_{index:03d}"}
        for index, candidate_id in enumerate(candidate_ids, start=1)
    ]
    if items != expected_items:
        raise PacketError("batch manifest review item order or identity is invalid")

    item_roots = [batch_root / item["directory"] for item in items]
    for offset, (item, item_root) in enumerate(zip(items, item_roots, strict=True)):
        packet_path = item_root / "60_DIRECTION_PACKET.md"
        handoff_path = item_root / "70_EXPLORER_HANDOFF.json"
        blocker_path = item_root / "90_TERMINAL_BLOCKER.json"
        later_exists = any(path.exists() for path in item_roots[offset + 1 :])
        if blocker_path.exists():
            blocker = _load_json_object(blocker_path, "terminal blocker")
            if blocker.get("candidate_id") != item["candidate_id"] or later_exists:
                raise PacketError("blocked batch item identity or later-item state is invalid")
            return {
                "status": "BLOCKED",
                "index": item["index"],
                "candidate_id": item["candidate_id"],
            }
        if handoff_path.exists() and not packet_path.exists():
            raise PacketError("Explorer handoff exists without the exact direction packet")
        if packet_path.exists() and handoff_path.exists():
            handoff = _load_json_object(handoff_path, "Explorer handoff receipt")
            packet_bytes = packet_path.read_bytes()
            if (
                handoff.get("candidate_id") != item["candidate_id"]
                or handoff.get("route_status") != "ROUTE_SENT"
                or handoff.get("packet_bytes") != len(packet_bytes)
                or handoff.get("packet_sha256") != hashlib.sha256(packet_bytes).hexdigest()
            ):
                raise PacketError("Explorer handoff receipt does not bind the exact direction packet")
            continue
        if item_root.exists():
            if later_exists:
                raise PacketError("a later batch item exists before the active item is terminal")
            return {
                "status": "ACTIVE",
                "index": item["index"],
                "candidate_id": item["candidate_id"],
            }
        if later_exists:
            raise PacketError("a later batch item exists before the next ordered item")
        return {
            "status": "NEXT",
            "index": item["index"],
            "candidate_id": item["candidate_id"],
            "directory": item["directory"],
        }
    return {"status": "COMPLETE", "candidate_count": len(candidate_ids)}


def command_batch_next(args: argparse.Namespace) -> int:
    repo = _repo_root()
    pro_reviews = (repo / "local_research" / "pro_reviews").resolve()
    manifest_path = Path(args.manifest).resolve()
    if not _is_below(manifest_path, pro_reviews):
        raise PacketError("batch manifest must be under local_research/pro_reviews")
    manifest = _load_json_object(manifest_path, "batch manifest")
    result = batch_next_status(manifest, manifest_path.parent)
    result["campaign_id"] = manifest.get("campaign_id")
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


def command_self_test(_: argparse.Namespace) -> int:
    source_packet = {"packet_id": "SRP-1", "assignment_id": "SRC-1", "packet_kind": "SOURCE_RESULT_PACKET", "status": "terminal"}
    inspiration = {"packet_id": "AIP-1", "assignment_id": "INN-1", "packet_kind": "ALGORITHM_INSPIRATION_PACKET", "status": "terminal"}
    principles = {"packet_id": "RLPA-1", "assignment_id": "PRI-1", "packet_kind": "RL_PRINCIPLE_ANALYSIS_PACKET", "status": "terminal"}
    critic = {"packet_id": "CAP-1", "assignment_id": "CRI-1", "packet_kind": "CRITIC_ASSESSMENT_PACKET", "status": "terminal"}
    record = {
        "document_kind": "independent_research_campaign_v3",
        "workflow_commit": "abc1234",
        "intake": {"mode": "algorithm_inspiration_campaign", "direction_or_question": "test", "mission_link": "test", "authorized_source_boundary": "fixture", "exclusions": []},
        "campaign": {"campaign_id": "TEST-CAMPAIGN"},
        "portfolio": [
            {"candidate_id": "PARENT", "status": "parked"},
            {"candidate_id": "CAND-1", "status": "validation_ready", "inspiration_packet_id": "AIP-1", "revision_packet_ids": [], "principles_packet_ids": ["RLPA-1"], "critic_packet_ids": ["CAP-1"], "source_result_packet_ids": ["SRP-1"], "parent_candidate_ids": ["PARENT"]},
            {"candidate_id": "CAND-2", "status": "validation_ready"},
        ],
        "packets": [source_packet, inspiration, principles, critic],
        "opportunities": [],
    }
    payload = build_payload(record, "CAND-1")
    assert payload["scope"]["candidate_count"] == 1
    assert payload["review_candidate_id"] == "CAND-1"
    assert len(payload["source_result_packets"]) == 1
    assert len(payload["candidate_lineage_packets"]) == 3
    broken = json.loads(json.dumps(record))
    broken["packets"] = broken["packets"][:-1]
    try:
        build_payload(broken, "CAND-1")
    except PacketError:
        pass
    else:
        raise AssertionError("missing lineage packet did not fail closed")
    try:
        build_payload(record, "CAND-2")
    except PacketError:
        pass
    else:
        raise AssertionError("incomplete second candidate did not fail closed")
    batch_record = json.loads(json.dumps(record))
    batch_record["portfolio"][2] = json.loads(json.dumps(batch_record["portfolio"][1]))
    batch_record["portfolio"][2]["candidate_id"] = "CAND-2"
    batch = build_batch_payload(batch_record, ["CAND-1", "CAND-2"], "1" * 40)
    assert batch["ordered_candidate_ids"] == ["CAND-1", "CAND-2"]
    try:
        build_batch_payload(batch_record, ["CAND-1", "CAND-1"], "1" * 40)
    except PacketError:
        pass
    else:
        raise AssertionError("duplicate batch candidate did not fail closed")
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        assert batch_next_status(batch, root)["candidate_id"] == "CAND-1"
        first = root / "item_001"
        first.mkdir()
        packet = b"packet-one\n"
        (first / "60_DIRECTION_PACKET.md").write_bytes(packet)
        (first / "70_EXPLORER_HANDOFF.json").write_text(
            json.dumps(
                {
                    "candidate_id": "CAND-1",
                    "route_status": "ROUTE_SENT",
                    "packet_bytes": len(packet),
                    "packet_sha256": hashlib.sha256(packet).hexdigest(),
                }
            ),
            encoding="utf-8",
        )
        assert batch_next_status(batch, root)["candidate_id"] == "CAND-2"
        second = root / "item_002"
        second.mkdir()
        (second / "90_TERMINAL_BLOCKER.json").write_text(
            json.dumps({"candidate_id": "CAND-2", "reason": "fixture"}),
            encoding="utf-8",
        )
        assert batch_next_status(batch, root)["status"] == "BLOCKED"
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / "item_002").mkdir()
        try:
            batch_next_status(batch, root)
        except PacketError:
            pass
        else:
            raise AssertionError("out-of-order batch item did not fail closed")
    print("HMASD_DIRECTION_REVIEW_BATCH_SELF_TEST_OK")
    print("HMASD_DIRECTION_REVIEW_PACKAGER_SELF_TEST_OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--campaign", required=True)
    build.add_argument("--candidate-id", required=True)
    build.add_argument("--output", required=True)
    build.add_argument("--batch-manifest")
    build.set_defaults(func=command_build)
    check = subparsers.add_parser("check")
    check.add_argument("--campaign", required=True)
    check.add_argument("--candidate-id", required=True)
    check.set_defaults(func=command_check)
    batch_plan = subparsers.add_parser("batch-plan")
    batch_plan.add_argument("--campaign", required=True)
    batch_plan.add_argument("--candidate-id", action="append", required=True)
    batch_plan.add_argument("--question-contract-commit", required=True)
    batch_plan.add_argument("--output", required=True)
    batch_plan.set_defaults(func=command_batch_plan)
    batch_next = subparsers.add_parser("batch-next")
    batch_next.add_argument("--manifest", required=True)
    batch_next.set_defaults(func=command_batch_next)
    self_test = subparsers.add_parser("self-test")
    self_test.set_defaults(func=command_self_test)
    args = parser.parse_args()
    try:
        return args.func(args)
    except PacketError as exc:
        print(f"HMASD_DIRECTION_REVIEW_INPUT_ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
