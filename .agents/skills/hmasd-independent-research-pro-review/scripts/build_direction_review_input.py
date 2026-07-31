#!/usr/bin/env python3
"""Build one mechanically bounded independent-research direction review packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
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
    if output_path.exists():
        raise PacketError("output already exists; review inputs are immutable")
    payload, _, rendered = _load_rendered(args.campaign, args.candidate_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(output_path.name + ".tmp")
    if temporary.exists():
        raise PacketError("temporary output already exists")
    temporary.write_bytes(rendered)
    os.replace(temporary, output_path)
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
    print("HMASD_DIRECTION_REVIEW_PACKAGER_SELF_TEST_OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--campaign", required=True)
    build.add_argument("--candidate-id", required=True)
    build.add_argument("--output", required=True)
    build.set_defaults(func=command_build)
    check = subparsers.add_parser("check")
    check.add_argument("--campaign", required=True)
    check.add_argument("--candidate-id", required=True)
    check.set_defaults(func=command_check)
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
