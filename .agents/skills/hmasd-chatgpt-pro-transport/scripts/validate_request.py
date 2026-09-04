#!/usr/bin/env python3
"""Validate an inbound direction/prompt transport request without sending it."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from transport_contract import (  # noqa: E402
    packet_artifacts,
    validate_provider_context_reset_evidence,
    validate_parent_thread_id,
    validate_source_thread_id,
)


WORKFLOW_NODES = {"em_innovator", "em_convergence", "portfolio_decision", "legacy"}


def _error(message: str) -> int:
    print(json.dumps({"valid": False, "error": message}, ensure_ascii=False))
    return 2


def _portfolio_has_direction(portfolio: Path, direction_id: str) -> bool:
    if not portfolio.is_file():
        return False
    pattern = re.compile(rf"^\|\s*{re.escape(direction_id)}\s*\|")
    return any(pattern.search(line) for line in portfolio.read_text(encoding="utf-8").splitlines())


def validate(request: dict, project_root: Path) -> dict:
    forbidden_route_fields = sorted(
        field
        for field in (
            "fallback_enabled",
            "fallback_thread_id",
            "fallback_thread_url",
            "fallback_destination_thread_id",
            "primary_destination_thread_id",
        )
        if field in request
    )
    if forbidden_route_fields:
        raise ValueError(
            "legacy fallback routing fields are not accepted: "
            + ", ".join(forbidden_route_fields)
        )
    request_id = request.get("request_id")
    direction_id = request.get("direction_id")
    if not isinstance(request_id, str) or not request_id.strip():
        raise ValueError("request_id must be a non-empty string")
    if not isinstance(direction_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", direction_id):
        raise ValueError("direction_id must use letters, digits, underscore, or hyphen")

    portfolio_path = project_root / "docs" / "research" / "portfolio" / "PORTFOLIO.md"
    workflow_node = request.get("workflow_node", "legacy")
    if workflow_node not in WORKFLOW_NODES:
        raise ValueError("workflow_node must be em_innovator, em_convergence, portfolio_decision, or legacy")
    direction_ids_value = request.get("direction_ids", [direction_id])
    if not isinstance(direction_ids_value, list) or not direction_ids_value:
        raise ValueError("direction_ids must be a non-empty list")
    direction_ids: list[str] = []
    for value in direction_ids_value:
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
            raise ValueError("every direction_ids entry must be a registered direction token")
        if value in direction_ids:
            raise ValueError(f"duplicate direction_id in scope: {value}")
        direction_ids.append(value)
        direction_path = project_root / "docs" / "research" / "candidates" / value / "DIRECTION.md"
        if not direction_path.is_file() or not _portfolio_has_direction(portfolio_path, value):
            raise ValueError(f"unknown or unregistered direction_id: {value}")

    if workflow_node == "portfolio_decision":
        if direction_id != "portfolio":
            raise ValueError("portfolio_decision requires direction_id=portfolio")
        expected_binding_key = "portfolio:cross_direction"
    elif workflow_node in {"em_innovator", "em_convergence"}:
        if direction_ids != [direction_id]:
            raise ValueError("an EM decision node requires exactly its direction_id in direction_ids")
        suffix = "innovator" if workflow_node == "em_innovator" else "convergence"
        expected_binding_key = f"em:{direction_id}:{suffix}"
    else:
        if direction_ids != [direction_id]:
            raise ValueError("legacy transport accepts exactly one direction")
        expected_binding_key = f"legacy:{direction_id}"

    conversation_binding_key = request.get("conversation_binding_key", expected_binding_key)
    if conversation_binding_key != expected_binding_key:
        raise ValueError(
            f"conversation_binding_key must be {expected_binding_key} for {workflow_node}"
        )
    requested_conversation_id = request.get("requested_conversation_id")
    if requested_conversation_id is not None and (
        not isinstance(requested_conversation_id, str)
        or not re.fullmatch(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            requested_conversation_id,
        )
    ):
        raise ValueError("requested_conversation_id must be a UUID when supplied")
    declared_source_mode = request.get("source_mode")
    if declared_source_mode is not None and declared_source_mode not in {
        "single_body_attachment",
        "paste",
        "upload",
    }:
        raise ValueError("source_mode must be single_body_attachment, paste, or upload when supplied")
    reset_invalid_provider_context = request.get("reset_invalid_provider_context", False)
    if not isinstance(reset_invalid_provider_context, bool):
        raise ValueError("reset_invalid_provider_context must be a boolean when supplied")
    reset_evidence_value = request.get("provider_context_reset_evidence")
    if reset_invalid_provider_context:
        if requested_conversation_id is not None:
            raise ValueError("requested_conversation_id must be absent for a provider-context reset")
        provider_context_reset_evidence = validate_provider_context_reset_evidence(reset_evidence_value)
    else:
        if reset_evidence_value is not None:
            raise ValueError("provider_context_reset_evidence requires reset_invalid_provider_context=true")
        provider_context_reset_evidence = None
    decision_authority = request.get("decision_authority")
    if workflow_node != "legacy" and decision_authority != "pro_final":
        raise ValueError("decision_authority must be pro_final for a Pro decision node")

    prompt = request.get("prompt")
    prompt_path_value = request.get("prompt_path")
    if (prompt is None) == (prompt_path_value is None):
        raise ValueError("provide exactly one of prompt or prompt_path")

    source_mode = "paste"
    prompt_path = None
    if prompt is not None:
        if not isinstance(prompt, str) or not prompt:
            raise ValueError("prompt must be a non-empty string")
        prompt_bytes = prompt.encode("utf-8")
    else:
        source_mode = "upload"
        if not isinstance(prompt_path_value, str) or not Path(prompt_path_value).is_absolute():
            raise ValueError("prompt_path must be an absolute path")
        prompt_path = Path(prompt_path_value)
        if not prompt_path.is_file():
            raise ValueError(f"prompt_path is not a file: {prompt_path}")
        prompt_bytes = prompt_path.read_bytes()
        if not prompt_bytes:
            raise ValueError("prompt_path is empty")

    if declared_source_mode == "single_body_attachment":
        if source_mode != "upload" or prompt_path is None or prompt_path.name != "PROMPT_BODY.md":
            raise ValueError("single_body_attachment requires exactly the sole PROMPT_BODY.md upload")
        if "reference_paths" in request or "reference_file" in request:
            raise ValueError("single_body_attachment must not declare reference_paths or reference_file")

    companion_prompt = request.get("companion_prompt")
    if companion_prompt is not None and (not isinstance(companion_prompt, str) or not companion_prompt):
        raise ValueError("companion_prompt must be a non-empty string when supplied")

    reference_paths_value = request.get("reference_paths", [])
    if reference_paths_value is None:
        reference_paths_value = []
    if not isinstance(reference_paths_value, list):
        raise ValueError("reference_paths must be a list")
    reference_files = []
    seen_references = set()
    for raw_reference in reference_paths_value:
        if not isinstance(raw_reference, str) or not Path(raw_reference).is_absolute():
            raise ValueError("every reference_path must be an absolute path")
        reference_path = Path(raw_reference)
        if not reference_path.is_file():
            raise ValueError(f"reference_path is not a file: {reference_path}")
        resolved_reference = reference_path.resolve()
        if resolved_reference in seen_references:
            raise ValueError(f"duplicate reference_path: {resolved_reference}")
        seen_references.add(resolved_reference)
        reference_bytes = resolved_reference.read_bytes()
        if not reference_bytes:
            raise ValueError(f"reference_path is empty: {resolved_reference}")
        reference_files.append(
            {
                "path": str(resolved_reference),
                "filename": resolved_reference.name,
                "bytes": len(reference_bytes),
                "sha256": hashlib.sha256(reference_bytes).hexdigest(),
            }
        )

    canonical_handoff = workflow_node != "legacy" or declared_source_mode == "single_body_attachment"
    source_thread_id = request.get("source_thread_id")
    if source_thread_id is None:
        if canonical_handoff:
            raise ValueError("canonical handoff requires source_thread_id")
    else:
        source_thread_id = validate_source_thread_id(source_thread_id)
    creator_thread_id = request.get("creator_thread_id", source_thread_id)
    if creator_thread_id is not None:
        creator_thread_id = validate_source_thread_id(creator_thread_id)
        if creator_thread_id != source_thread_id:
            raise ValueError("creator_thread_id must equal source_thread_id")
    parent_thread_id = request.get("parent_thread_id")
    if parent_thread_id is None:
        if canonical_handoff:
            raise ValueError("canonical handoff requires parent_thread_id")
    else:
        parent_thread_id = validate_parent_thread_id(parent_thread_id)
    return_receipt_thread_id = request.get("return_receipt_thread_id", parent_thread_id)
    if return_receipt_thread_id is not None:
        return_receipt_thread_id = validate_parent_thread_id(return_receipt_thread_id)
        if return_receipt_thread_id != parent_thread_id:
            raise ValueError("return_receipt_thread_id must equal parent_thread_id")
    return_route = request.get("return_route", "PARENT_SESSION" if parent_thread_id else None)
    if return_route not in {None, "PARENT_SESSION"}:
        raise ValueError("return_route must be PARENT_SESSION when supplied")
    operator_thread_id = request.get("operator_thread_id")
    if operator_thread_id is not None:
        operator_thread_id = validate_source_thread_id(operator_thread_id)
    if canonical_handoff and operator_thread_id is None:
        raise ValueError("canonical handoff requires operator_thread_id after create_thread")

    packet = packet_artifacts(
        request_id,
        direction_id,
        [item["filename"] for item in reference_files],
    )

    return {
        "valid": True,
        "request_id": request_id,
        "direction_id": direction_id,
        "direction_ids": direction_ids,
        "workflow_node": workflow_node,
        "conversation_binding_key": conversation_binding_key,
        "requested_conversation_id": requested_conversation_id,
        "conversation_reuse_required": bool(request.get("conversation_reuse_required", workflow_node != "legacy")),
        "reset_invalid_provider_context": reset_invalid_provider_context,
        "provider_context_reset_evidence": provider_context_reset_evidence,
        "decision_authority": decision_authority,
        "direction_path": str(
            (project_root / "docs" / "research" / "candidates" / direction_ids[0] / "DIRECTION.md").resolve()
        ),
        "direction_paths": [
            str((project_root / "docs" / "research" / "candidates" / value / "DIRECTION.md").resolve())
            for value in direction_ids
        ],
        "source_mode": declared_source_mode or source_mode,
        "transport_input_mode": source_mode,
        "prompt_path": str(prompt_path.resolve()) if prompt_path else None,
        "prompt_bytes": len(prompt_bytes),
        "prompt_sha256": hashlib.sha256(prompt_bytes).hexdigest(),
        "companion_prompt": companion_prompt,
        "companion_prompt_sha256": hashlib.sha256(companion_prompt.encode("utf-8")).hexdigest() if companion_prompt is not None else None,
        "source_thread_id": source_thread_id,
        "creator_thread_id": creator_thread_id,
        "parent_thread_id": parent_thread_id,
        "operator_thread_id": operator_thread_id,
        "return_route": return_route,
        "return_receipt_thread_id": return_receipt_thread_id,
        "return_receipt_ready": bool(parent_thread_id),
        "reference_files": reference_files,
        "packet": packet,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("request_json", type=Path)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[4])
    args = parser.parse_args()
    try:
        request = json.loads(args.request_json.read_text(encoding="utf-8"))
        if not isinstance(request, dict):
            return _error("request JSON must be an object")
        print(json.dumps(validate(request, args.project_root.resolve()), ensure_ascii=False, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return _error(str(exc))


if __name__ == "__main__":
    sys.exit(main())
