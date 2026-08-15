#!/usr/bin/env python3
"""Create one canonical HMASD transport archive from a COMPLETE strict ledger row.

This utility is intentionally offline: it reads no browser state and performs no
provider action.  It is for the manual's ledger-only restoration procedure when
an assigned result archive is missing or stale.  It never overwrites an archive.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


class RestoreError(ValueError):
    """The proposed ledger-only restoration is not authoritative enough."""


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _nonempty_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise RestoreError(f"missing_or_empty:{name}")
    return value


def _require_complete_operation(operation: dict[str, Any]) -> None:
    required_equals = {
        "status": "COMPLETE",
        "terminalState": "NATURAL_COMPLETION_VERIFIED",
        "sendCount": 1,
        "sendActionCount": 1,
        "clickCount": 1,
    }
    for field, expected in required_equals.items():
        if operation.get(field) != expected:
            raise RestoreError(f"strict_invariant_failed:{field}")
    for field in (
        "operationId", "provider", "model", "stableKey", "promptSha256",
        "conversationUrl", "conversationId", "userMessageId",
        "assistantMessageId", "responseText", "responseSha256",
    ):
        _nonempty_string(operation.get(field), field)
    response = operation["responseText"]
    if _sha256_text(response) != operation["responseSha256"]:
        raise RestoreError("response_sha256_mismatch")
    causal = operation.get("causalSendReceipt")
    if not isinstance(causal, dict) or causal.get("ok") is not True or causal.get("persisted") is not True:
        raise RestoreError("causal_send_receipt_invalid")
    for field in ("operationId", "sendActionCount", "clickCount", "sourceSha256", "canonicalPromptSha256"):
        if causal.get(field) != operation.get(field if field not in {"sourceSha256", "canonicalPromptSha256"} else "promptSha256"):
            raise RestoreError(f"causal_send_receipt_mismatch:{field}")
    snapshots = operation.get("snapshots")
    if not isinstance(snapshots, list) or len(snapshots) < 2:
        raise RestoreError("stable_snapshots_missing")
    for snapshot in snapshots:
        if not isinstance(snapshot, dict) or snapshot.get("assistantMessageId") != operation["assistantMessageId"] or snapshot.get("textSha256") != operation["responseSha256"]:
            raise RestoreError("stable_snapshot_mismatch")
    controls = operation.get("controls")
    if not isinstance(controls, dict) or any(controls.get(key) is not False for key in ("stop", "continue", "retry", "answerNow")):
        raise RestoreError("active_or_unknown_response_control")


def canonical_receipt(operation: dict[str, Any]) -> dict[str, Any]:
    """Copy ledger-backed receipt facts without inventing a tab-close outcome."""
    fields = (
        "operationId", "status", "terminalState", "provider", "model", "stableKey",
        "idempotencyKey", "conversationUrl", "conversationId", "promptSha256",
        "sendCount", "sendActionCount", "clickCount", "userMessageId",
        "assistantMessageId", "responseSha256", "responseText", "snapshots",
        "controls", "clickedControls", "completedAt", "causalSendReceipt",
        "submissionIdentity", "renderedDisplay", "renderedIdentity",
        "observedCommitmentClass", "observedTurnEvidence",
    )
    return {field: operation[field] for field in fields if field in operation}


def restore(*, state_path: Path, batch_path: Path, idempotency_key: str, results_path: Path) -> dict[str, Any]:
    if results_path.exists():
        raise RestoreError("results_path_already_exists")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    operations = state.get("operations")
    if not isinstance(operations, dict) or not isinstance(operations.get(idempotency_key), dict):
        raise RestoreError("strict_operation_not_found")
    operation = operations[idempotency_key]
    _require_complete_operation(operation)
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    provider = batch.get("provider")
    question_paths = batch.get("question_paths")
    if provider != operation["provider"] or not isinstance(question_paths, list) or len(question_paths) != 1:
        raise RestoreError("batch_operation_binding_invalid")
    question_path = Path(question_paths[0])
    question_sha256 = _sha256_file(question_path)
    if question_sha256 != operation["promptSha256"]:
        raise RestoreError("question_sha256_mismatch")
    receipt = canonical_receipt(operation)
    result = {
        "schema_version": 1,
        "provider": provider,
        "status": "COMPLETE",
        "rows": [{
            "question_path": str(question_path).replace("\\", "/"),
            "question_sha256": question_sha256,
            "status": "COMPLETE",
            "response": operation["responseText"],
            "conversation_url": operation["conversationUrl"],
            "conversation_id": operation["conversationId"],
            "model_evidence": operation["model"],
            "promptSha256": operation["promptSha256"],
            "receipt": receipt,
            "prompt_sent": True,
            "response_received": True,
            "error": "",
        }],
        "tab_cleanup": {
            "tab_id": operation.get("tabId"),
            "generation_inactive": True,
            "closed": None,
            "error": "unknown: ledger-only restoration has no authoritative tab-close outcome",
        },
    }
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with results_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-path", type=Path, required=True)
    parser.add_argument("--batch-path", type=Path, required=True)
    parser.add_argument("--idempotency-key", required=True)
    parser.add_argument("--results-path", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = restore(
            state_path=args.state_path,
            batch_path=args.batch_path,
            idempotency_key=args.idempotency_key,
            results_path=args.results_path,
        )
    except (OSError, json.JSONDecodeError, RestoreError) as error:
        print(f"LEDGER_RESTORE_REJECTED:{error}")
        return 2
    row = result["rows"][0]
    print(f"LEDGER_RESTORE_COMPLETE:{row['receipt']['operationId']}:{row['receipt']['responseSha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
