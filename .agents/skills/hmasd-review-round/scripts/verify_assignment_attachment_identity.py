from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPOSITORY = "CartmanFatass/My-paper-code"
BRANCH = "aggressive"
INSTRUCTION = (
    "Ignore earlier rounds and refs. Read only this question and its listed "
    "evidence from stage_commit."
)


class IdentityError(RuntimeError):
    pass


def _require_single_line(name: str, value: str) -> None:
    if not value or "\n" in value or "\r" in value:
        raise IdentityError(f"{name} must be one nonempty line")


def _assignment_fence(round_name: str, stage_commit: str, question: str) -> bytes:
    _require_single_line("round", round_name)
    _require_single_line("question", question)
    if len(stage_commit) != 40 or any(
        c not in "0123456789abcdef" for c in stage_commit
    ):
        raise IdentityError(
            "stage_commit must be exactly 40 lowercase hexadecimal characters"
        )
    return "\n".join(
        (
            "CURRENT_REVIEW_ASSIGNMENT",
            f"repository={REPOSITORY}",
            f"branch={BRANCH}",
            f"round={round_name}",
            f"stage_commit={stage_commit}",
            f"question={question}",
            f"instruction={INSTRUCTION}",
        )
    ).encode("utf-8")


def _read_required(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise IdentityError(f"cannot read {label}: {exc}") from exc


def _read_observed(path: Path) -> tuple[str, bytes | None]:
    try:
        return "readable_text", path.read_bytes()
    except OSError:
        return "unreadable", None


def _canonical_identity(
    *,
    conversation_id: str,
    user_turn_id: str,
    attachment_id: str,
    payload: bytes,
    round_name: str,
    stage_commit: str,
    question: str,
) -> str:
    return "\n".join(
        (
            "ATTACHMENT_BACKED_REVIEW_ASSIGNMENT",
            f"conversation_id={conversation_id}",
            f"user_turn_id={user_turn_id}",
            f"attachment_id={attachment_id}",
            f"payload_bytes={len(payload)}",
            f"payload_sha256={hashlib.sha256(payload).hexdigest()}",
            f"repository={REPOSITORY}",
            f"branch={BRANCH}",
            f"round={round_name}",
            f"stage_commit={stage_commit}",
            f"question={question}",
            f"instruction={INSTRUCTION}",
        )
    )


def _base_result(status: str, source: str, reason: str) -> dict[str, Any]:
    return {
        "status": status,
        "identity_source": source,
        "reason": reason,
    }


def _verify_metadata(
    metadata_path: Path,
    *,
    expected: bytes,
    conversation_id: str,
    user_turn_id: str,
) -> tuple[str, str, dict[str, Any] | None]:
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "IDENTITY_UNREADABLE", "provider_native_metadata", None
    required = {
        "metadata_source": "provider_native_attachment_payload",
        "provider_native": True,
        "conversation_id": conversation_id,
        "user_turn_id": user_turn_id,
        "payload_bytes": len(expected),
        "payload_sha256": hashlib.sha256(expected).hexdigest(),
    }
    attachment_id = metadata.get("attachment_id")
    if not isinstance(attachment_id, str) or not attachment_id:
        return "IDENTITY_UNREADABLE", "provider_native_metadata", None
    for key, value in required.items():
        if key not in metadata:
            return "IDENTITY_UNREADABLE", "provider_native_metadata", None
        if metadata[key] != value:
            return "IDENTITY_MISMATCH", "provider_native_metadata", None
    return "ATTACHMENT_IDENTITY_VERIFIED", "provider_native_metadata", metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-payload", required=True, type=Path)
    observed = parser.add_mutually_exclusive_group(required=True)
    observed.add_argument("--observed-attachment", type=Path)
    observed.add_argument("--provider-metadata", type=Path)
    parser.add_argument("--conversation-id", required=True)
    parser.add_argument("--user-turn-id", required=True)
    parser.add_argument("--attachment-id", default="")
    parser.add_argument("--round", required=True, dest="round_name")
    parser.add_argument("--stage-commit", required=True)
    parser.add_argument("--question", required=True)
    args = parser.parse_args()

    try:
        _require_single_line("conversation_id", args.conversation_id)
        _require_single_line("user_turn_id", args.user_turn_id)
        expected = _read_required(args.expected_payload, "expected payload")
        fence = _assignment_fence(args.round_name, args.stage_commit, args.question)
        crlf_fence = fence.replace(b"\n", b"\r\n")
        if expected.count(fence) + expected.count(crlf_fence) != 1:
            result = _base_result(
                "IDENTITY_MISMATCH",
                "expected_payload",
                "expected payload must contain exactly one complete rendered Assignment fence",
            )
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
            return 3

        attachment_id = args.attachment_id
        source = "readable_text"
        if args.observed_attachment is not None:
            source, observed_bytes = _read_observed(args.observed_attachment)
            if observed_bytes is None:
                result = _base_result(
                    "IDENTITY_UNREADABLE", source, "attachment payload is not readable"
                )
                print(json.dumps(result, ensure_ascii=False, sort_keys=True))
                return 2
            if not attachment_id:
                result = _base_result(
                    "IDENTITY_UNREADABLE",
                    source,
                    "attachment_id is required to bind the readable payload to one user turn",
                )
                print(json.dumps(result, ensure_ascii=False, sort_keys=True))
                return 2
            _require_single_line("attachment_id", attachment_id)
            if observed_bytes != expected:
                result = _base_result(
                    "IDENTITY_MISMATCH",
                    source,
                    "attachment payload is not byte-exact expected payload",
                )
                print(json.dumps(result, ensure_ascii=False, sort_keys=True))
                return 3
        else:
            status, source, metadata = _verify_metadata(
                args.provider_metadata,
                expected=expected,
                conversation_id=args.conversation_id,
                user_turn_id=args.user_turn_id,
            )
            if status != "ATTACHMENT_IDENTITY_VERIFIED" or metadata is None:
                result = _base_result(
                    status,
                    source,
                    "provider-native metadata is incomplete or does not match the "
                    "expected payload",
                )
                print(json.dumps(result, ensure_ascii=False, sort_keys=True))
                return 2 if status == "IDENTITY_UNREADABLE" else 3
            attachment_id = str(metadata["attachment_id"])
            _require_single_line("attachment_id", attachment_id)

        identity = _canonical_identity(
            conversation_id=args.conversation_id,
            user_turn_id=args.user_turn_id,
            attachment_id=attachment_id,
            payload=expected,
            round_name=args.round_name,
            stage_commit=args.stage_commit,
            question=args.question,
        )
        result = {
            "status": "ATTACHMENT_IDENTITY_VERIFIED",
            "identity_source": source,
            "conversation_id": args.conversation_id,
            "user_turn_id": args.user_turn_id,
            "attachment_id": attachment_id,
            "payload_bytes": len(expected),
            "payload_sha256": hashlib.sha256(expected).hexdigest(),
            "round": args.round_name,
            "stage_commit": args.stage_commit,
            "question": args.question,
            "sentinel_fence_identity": identity,
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except IdentityError as exc:
        print(f"ATTACHMENT_IDENTITY_ERROR {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
