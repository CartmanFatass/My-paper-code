#!/usr/bin/env python3
"""Read-only builder/checker for the Explorer toy-project candidate packet.

Canonical contract: document_kind=explorer_project_candidate_packet_v1.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any


DOCUMENT_KIND = "explorer_project_candidate_packet_v1"
EVIDENCE_TIER = "nonformal_toy"
REVIEW_MODE = "EXPLORER_TOY_DESIGN_ASSERTION_AUDIT"
COMPLETION = "OPS_IDENTITY_INTAKE_ONLY"
WORKFLOW_ID = "EXPLORER-TOY-VALIDATION-2026-07-31-P1"
ORDERED_CANDIDATE_IDS = (
    "CAND-VAP-FOLR-CORE",
    "CAND-VSP-02",
    "CAND-VSP-05",
)
AUTHORITY_FIELDS = (
    "scientific_authority",
    "code_authority",
    "compute_authority",
    "project_state_effect",
)
FORBIDDEN_DIRECT_AUTHORITY_FIELDS = {
    "code_project_manager_authority",
    "cpm_authority",
    "compute_authority",
    "scientific_authority",
    "project_state_authority",
    "current_work_authority",
}


class PacketError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PacketError(message)


def _text(value: Any, field: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{field} must be nonempty text")
    _require(value == value.strip(), f"{field} must not contain leading or trailing whitespace")
    return value


def _mapping(value: Any, field: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{field} must be an object")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], field: str) -> None:
    _require(set(value) == expected, f"{field} fields are not the canonical v1 set")


def _integer(value: Any, field: str) -> int:
    _require(isinstance(value, int) and not isinstance(value, bool), f"{field} must be an integer")
    return value


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _is_reparse(path: Path) -> bool:
    try:
        attributes = path.stat().st_file_attributes
    except (AttributeError, FileNotFoundError, OSError):
        attributes = 0
    # FILE_ATTRIBUTE_REPARSE_POINT, including junctions on Windows.
    return bool(attributes & 0x400)


def _safe_file(repo: Path, raw: Any, field: str, *, packet_path: bool = False) -> tuple[str, Path]:
    relative = _text(raw, field).replace("\\", "/")
    raw_parts = relative.split("/")
    _require(all(part not in {"", ".", ".."} for part in raw_parts), f"{field} contains path traversal or noncanonical segments")
    pure = PurePosixPath(relative)
    _require(not pure.is_absolute(), f"{field} must be repository-relative")
    _require(".." not in pure.parts and "." not in pure.parts, f"{field} contains path traversal")
    _require(pure.parts and pure.parts[0] == "local_research", f"{field} must be under local_research")
    _require("pro_reviews" not in pure.parts, f"{field} may not use local_research/pro_reviews")
    candidate = repo.joinpath(*pure.parts)
    local_root = (repo / "local_research").resolve(strict=True)
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise PacketError(f"{field} artifact is missing: {relative}") from exc
    try:
        resolved.relative_to(local_root)
    except ValueError as exc:
        raise PacketError(f"{field} escapes local_research: {relative}") from exc
    current = repo
    for part in pure.parts:
        current = current / part
        _require(not current.is_symlink() and not _is_reparse(current), f"{field} uses symlink/reparse path")
    _require(resolved.is_file() and not resolved.is_symlink(), f"{field} must reference a regular file")
    return "/".join(pure.parts), resolved


def _artifact(repo: Path, raw: Any, field: str) -> str:
    relative, path = _safe_file(repo, raw, field)
    path.read_bytes()
    return relative


def _artifact_from_path(repo: Path, raw: Any, field: str) -> str:
    relative, path = _safe_file(repo, raw, field)
    path.read_bytes()
    return relative


def _validate(packet: Any, repo: Path, *, packet_path: Path | None = None) -> dict[str, Any]:
    root = _mapping(packet, "packet")
    for field in FORBIDDEN_DIRECT_AUTHORITY_FIELDS:
        _require(field not in root, f"direct authority field is forbidden: {field}")
    _exact_keys(
        root,
        {
            "document_kind",
            "packet_version",
            "workflow_id",
            "user_authorization_reference",
            "evidence_tier",
            "origin_campaign",
            "cohort",
            "candidate",
            "review_request",
            "authority",
            "completion",
        },
        "packet",
    )
    _require(root.get("document_kind") == DOCUMENT_KIND, "wrong document_kind")
    _require(_integer(root.get("packet_version"), "packet_version") == 1, "wrong packet_version")
    workflow_id = _text(root.get("workflow_id"), "workflow_id")
    _require(workflow_id == WORKFLOW_ID, "wrong workflow_id")
    _text(root.get("user_authorization_reference"), "user_authorization_reference")
    _require(root.get("evidence_tier") == EVIDENCE_TIER, "evidence_tier must be nonformal_toy")

    campaign = _mapping(root.get("origin_campaign"), "origin_campaign")
    _exact_keys(campaign, {"campaign_id", "campaign_workflow_commit", "artifact"}, "origin_campaign")
    campaign_id = _text(campaign.get("campaign_id"), "origin_campaign.campaign_id")
    _text(campaign.get("campaign_workflow_commit"), "origin_campaign.campaign_workflow_commit")
    campaign_artifact = _artifact(repo, campaign.get("artifact"), "origin_campaign.artifact")

    cohort = _mapping(root.get("cohort"), "cohort")
    _exact_keys(cohort, {"ordered_candidate_ids", "current_index"}, "cohort")
    ordered = cohort.get("ordered_candidate_ids")
    _require(isinstance(ordered, list) and bool(ordered), "cohort.ordered_candidate_ids must be a nonempty list")
    ordered_ids = [_text(item, f"cohort.ordered_candidate_ids[{i}]") for i, item in enumerate(ordered)]
    _require(len(ordered_ids) == len(set(ordered_ids)), "cohort has duplicate candidates")
    _require(tuple(ordered_ids) == ORDERED_CANDIDATE_IDS, "cohort is not the frozen P1 queue")
    current_index = _integer(cohort.get("current_index"), "cohort.current_index")
    _require(0 <= current_index < len(ordered_ids), "cohort.current_index is out of range")

    candidate = _mapping(root.get("candidate"), "candidate")
    _exact_keys(candidate, {"id", "artifact"}, "candidate")
    candidate_id = _text(candidate.get("id"), "candidate.id")
    _require(candidate_id == ordered_ids[current_index], "candidate.id does not match ordered queue")
    candidate_artifact = _artifact(repo, candidate.get("artifact"), "candidate.artifact")

    review = _mapping(root.get("review_request"), "review_request")
    _exact_keys(review, {"mode", "candidate_count", "cross_direction_competition", "combined_toy"}, "review_request")
    _require(review.get("mode") == REVIEW_MODE, "review_request.mode must be EXPLORER_TOY_DESIGN_ASSERTION_AUDIT")
    _require(
        _integer(review.get("candidate_count"), "review_request.candidate_count") == 1,
        "review_request.candidate_count must be 1",
    )
    _require(review.get("cross_direction_competition") is False, "cross-direction Pro selection is forbidden")
    _require(review.get("combined_toy") is False, "combined toy package is forbidden")

    authority = _mapping(root.get("authority"), "authority")
    _exact_keys(authority, set(AUTHORITY_FIELDS), "authority")
    for field in AUTHORITY_FIELDS:
        _require(authority.get(field) == "none", f"authority.{field} must be none")
    _require(root.get("completion") == COMPLETION, "wrong completion marker")
    if packet_path is not None:
        _safe_file(repo, packet_path.relative_to(repo).as_posix(), "packet path")

    normalized = dict(root)
    normalized["origin_campaign"] = dict(campaign, artifact=campaign_artifact)
    normalized["cohort"] = dict(cohort, ordered_candidate_ids=ordered_ids, current_index=current_index)
    normalized["candidate"] = dict(candidate, id=candidate_id, artifact=candidate_artifact)
    normalized["authority"] = {field: "none" for field in AUTHORITY_FIELDS}
    normalized["document_kind"] = DOCUMENT_KIND
    normalized["packet_version"] = 1
    normalized["evidence_tier"] = EVIDENCE_TIER
    normalized["completion"] = COMPLETION
    return normalized


def _repo(path: str) -> Path:
    repo = Path(path).resolve(strict=True)
    _require(repo.is_dir(), "repo must be a directory")
    _require((repo / "local_research").is_dir(), "repo is missing local_research")
    return repo


def command_build(args: argparse.Namespace) -> int:
    repo = _repo(args.repo)
    packet = {
        "document_kind": DOCUMENT_KIND,
        "packet_version": 1,
        "workflow_id": args.workflow_id,
        "user_authorization_reference": args.user_authorization_reference,
        "evidence_tier": EVIDENCE_TIER,
        "origin_campaign": {
            "campaign_id": args.campaign_id,
            "campaign_workflow_commit": args.campaign_workflow_commit,
            "artifact": _artifact_from_path(repo, args.campaign_path, "origin_campaign.artifact"),
        },
        "cohort": {"ordered_candidate_ids": args.ordered_candidate, "current_index": args.current_index},
        "candidate": {
            "id": args.candidate_id,
            "artifact": _artifact_from_path(repo, args.candidate_path, "candidate.artifact"),
        },
        "review_request": {"mode": REVIEW_MODE, "candidate_count": 1, "cross_direction_competition": False, "combined_toy": False},
        "authority": {field: "none" for field in AUTHORITY_FIELDS},
        "completion": COMPLETION,
    }
    print(_canonical_json(_validate(packet, repo)), end="")
    return 0


def command_check(args: argparse.Namespace) -> int:
    repo = _repo(args.repo)
    packet_path = Path(args.packet)
    if not packet_path.is_absolute():
        packet_path = Path.cwd() / packet_path
    try:
        relative_packet = packet_path.relative_to(repo).as_posix()
    except ValueError as exc:
        raise PacketError("packet path must be under local_research") from exc
    _, checked_packet_path = _safe_file(repo, relative_packet, "packet path")
    try:
        raw = json.loads(checked_packet_path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PacketError(f"unable to read packet JSON: {exc}") from exc
    normalized = _validate(raw, repo)
    print(_canonical_json({"status": "EXPLORER_PROJECT_PACKET_OK", "packet": normalized}), end="")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--repo", required=True)
    build.add_argument("--workflow-id", required=True)
    build.add_argument("--user-authorization-reference", required=True)
    build.add_argument("--campaign-id", required=True)
    build.add_argument("--campaign-workflow-commit", required=True)
    build.add_argument("--campaign-path", required=True)
    build.add_argument("--candidate-id", required=True)
    build.add_argument("--candidate-path", required=True)
    build.add_argument("--current-index", required=True, type=int)
    build.add_argument("--ordered-candidate", action="append", required=True)
    build.set_defaults(func=command_build)
    check = sub.add_parser("check")
    check.add_argument("--repo", required=True)
    check.add_argument("--packet", required=True)
    check.set_defaults(func=command_check)
    args = parser.parse_args()
    try:
        return args.func(args)
    except (PacketError, OSError) as exc:
        print(f"EXPLORER_PROJECT_PACKET_ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
