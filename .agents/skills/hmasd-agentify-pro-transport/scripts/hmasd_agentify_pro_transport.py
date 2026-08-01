#!/usr/bin/env python3
"""Mechanical HMASD adapter for Agentify's strict Pro review transport."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


SCHEMA_VERSION = 1
MAX_TIMEOUT_MS = 45 * 60 * 1000
SEND_CONFIRM_TIMEOUT_SECONDS = 60.0
LEDGER_POLL_SECONDS = 1.0
GENERATION_REPORT_SECONDS = 5 * 60.0
AGENTIFY_REQUIRED_COMMIT = "6ed991f95d954415b0e9b8898b84c000067ebe00"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
KEY_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
OWNER_KEYS = {
    "code_project_manager": {
        "hmasd-formal-pro",
        "hmasd-uav-formal-pro",
        "hmasd-explorer-validation-pro",
    },
    "independent_research_review_operator": {
        "hmasd-independent-research-pro",
    },
}
REQUEST_FIELDS = {
    "schema_version",
    "transport_backend",
    "transport_owner",
    "stable_key",
    "provider",
    "model",
    "conversation_url",
    "conversation_id",
    "idempotency_key",
    "assignment_identity",
    "backend_selection_path",
    "prompt_path",
    "timeout_ms",
}
BACKEND_SELECTION_FIELDS = {
    "schema_version",
    "assignment_identity",
    "transport_backend",
    "operation_key",
}


class TransportError(RuntimeError):
    pass


def _fail(code: str) -> None:
    raise TransportError(code)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _required_text(value: Any, field: str, *, maximum: int = 4096) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum:
        _fail(f"invalid_{field}")
    return value


def _required_nonempty_text_preserve(value: Any, field: str, *, maximum: int) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        _fail(f"invalid_{field}")
    return value


def _required_int(value: Any, field: str, *, minimum: int = 0, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        _fail(f"invalid_{field}")
    if maximum is not None and value > maximum:
        _fail(f"invalid_{field}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TransportError(f"unreadable_json:{path}") from exc
    if not isinstance(value, dict):
        _fail("json_root_not_object")
    return value


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def _require_within(path: Path, roots: list[Path], field: str) -> Path:
    if not path.is_absolute():
        _fail(f"{field}_not_absolute")
    resolved = path.resolve(strict=False)
    if not any(_is_within(resolved, root) for root in roots):
        _fail(f"{field}_outside_owner_scope")
    return resolved


def _owner_roots(repo_root: Path, owner: str, kind: str) -> list[Path]:
    if owner == "code_project_manager":
        return [repo_root / ("logs" if kind == "runtime" else "docs/external-review")]
    if owner == "independent_research_review_operator":
        return [repo_root / "local_research/pro_reviews"]
    _fail("invalid_transport_owner")


def validate_request(raw: dict[str, Any], *, repo_root: Path) -> dict[str, Any]:
    if set(raw) != REQUEST_FIELDS:
        _fail("request_field_set_mismatch")
    if raw.get("schema_version") != SCHEMA_VERSION:
        _fail("invalid_schema_version")
    if raw.get("transport_backend") != "agentify":
        _fail("invalid_transport_backend")
    owner = _required_text(raw.get("transport_owner"), "transport_owner", maximum=128)
    if owner not in OWNER_KEYS:
        _fail("invalid_transport_owner")
    stable_key = _required_text(raw.get("stable_key"), "stable_key", maximum=128)
    if not KEY_RE.fullmatch(stable_key) or stable_key not in OWNER_KEYS[owner]:
        _fail("stable_key_owner_mismatch")
    if raw.get("provider") != "chatgpt":
        _fail("invalid_provider")
    model = _required_text(raw.get("model"), "model", maximum=128)
    conversation_url = _required_text(raw.get("conversation_url"), "conversation_url", maximum=2048)
    conversation_id = _required_text(raw.get("conversation_id"), "conversation_id", maximum=256)
    parsed = urlparse(conversation_url)
    if parsed.scheme != "https" or parsed.netloc != "chatgpt.com" or parsed.query or parsed.fragment:
        _fail("invalid_conversation_url")
    if parsed.path != f"/c/{conversation_id}":
        _fail("conversation_identity_mismatch")
    idempotency_key = _required_text(raw.get("idempotency_key"), "idempotency_key", maximum=128)
    if not KEY_RE.fullmatch(idempotency_key):
        _fail("invalid_idempotency_key")
    assignment_identity = _required_text(raw.get("assignment_identity"), "assignment_identity", maximum=1024)
    backend_selection_path = _require_within(
        Path(_required_text(raw.get("backend_selection_path"), "backend_selection_path", maximum=32768)),
        _owner_roots(repo_root, owner, "runtime"),
        "backend_selection_path",
    )
    if backend_selection_path.name != "TRANSPORT_BACKEND.json" or not backend_selection_path.is_file():
        _fail("backend_selection_missing")
    backend_selection = _load_json(backend_selection_path)
    if set(backend_selection) != BACKEND_SELECTION_FIELDS:
        _fail("backend_selection_field_set_mismatch")
    if (
        backend_selection.get("schema_version") != SCHEMA_VERSION
        or backend_selection.get("assignment_identity") != assignment_identity
        or backend_selection.get("transport_backend") != "agentify"
        or backend_selection.get("operation_key") != idempotency_key
    ):
        _fail("backend_selection_mismatch")
    timeout_ms = _required_int(raw.get("timeout_ms"), "timeout_ms", minimum=3000, maximum=MAX_TIMEOUT_MS)
    prompt_path = _require_within(
        Path(_required_text(raw.get("prompt_path"), "prompt_path", maximum=32768)),
        _owner_roots(repo_root, owner, "archive"),
        "prompt_path",
    )
    if not prompt_path.is_file():
        _fail("prompt_path_missing")
    try:
        prompt_bytes = prompt_path.read_bytes()
        prompt = prompt_bytes.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise TransportError("prompt_not_exact_utf8") from exc
    if not prompt:
        _fail("prompt_empty")
    if assignment_identity not in prompt:
        _fail("assignment_identity_not_in_prompt")
    return {
        "schema_version": SCHEMA_VERSION,
        "transport_backend": "agentify",
        "transport_owner": owner,
        "stable_key": stable_key,
        "provider": "chatgpt",
        "model": model,
        "conversation_url": conversation_url,
        "conversation_id": conversation_id,
        "idempotency_key": idempotency_key,
        "assignment_identity": assignment_identity,
        "backend_selection_path": str(backend_selection_path),
        "prompt_path": str(prompt_path),
        "timeout_ms": timeout_ms,
        "prompt": prompt,
    }


def agentify_body(request: dict[str, Any], *, verify_existing: bool) -> dict[str, Any]:
    return {
        "stableKey": request["stable_key"],
        "provider": request["provider"],
        "model": request["model"],
        "conversationUrl": request["conversation_url"],
        "conversationId": request["conversation_id"],
        "idempotencyKey": request["idempotency_key"],
        "prompt": request["prompt"],
        "timeoutMs": request["timeout_ms"],
        "verifyExisting": bool(verify_existing),
    }


def _http_json(url: str, *, token: str | None = None, body: dict[str, Any] | None = None, timeout_seconds: float = 10.0) -> dict[str, Any]:
    payload = None if body is None else json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    headers = {"accept": "application/json"}
    if token is not None:
        headers["authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["content-type"] = "application/json; charset=utf-8"
    request = Request(url, data=payload, headers=headers, method="POST" if payload is not None else "GET")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        raise TransportError(f"agentify_http_{exc.code}:{detail}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise TransportError("agentify_unreachable") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise TransportError("agentify_invalid_json") from exc
    if not isinstance(value, dict):
        _fail("agentify_json_root_not_object")
    return value


def _require_preexisting_review_tab(
    base: str,
    token: str,
    request: dict[str, Any],
    *,
    require_send_ready: bool = True,
) -> str:
    """Prove exact tab identity; new sends additionally require a ready prompt."""
    inventory = _http_json(f"{base}/tabs", token=token, timeout_seconds=10.0)
    tabs = inventory.get("tabs")
    if inventory.get("ok") is not True or not isinstance(tabs, list):
        _fail("agentify_preexisting_tab_inventory_invalid")
    matches = [
        tab
        for tab in tabs
        if isinstance(tab, dict) and tab.get("key") == request["stable_key"]
    ]
    if not matches:
        _fail("agentify_preexisting_tab_missing")
    if len(matches) != 1:
        _fail("agentify_preexisting_tab_ambiguous")
    tab = matches[0]
    tab_id = _required_text(tab.get("id"), "agentify_preexisting_tab_id", maximum=512)
    if tab.get("vendorId") != request["provider"] or tab.get("url") != request["conversation_url"]:
        _fail("agentify_preexisting_tab_identity_mismatch")

    status = _http_json(
        f"{base}/status?{urlencode({'tabId': tab_id})}",
        token=token,
        timeout_seconds=10.0,
    )
    status_tabs = status.get("tabs")
    if (
        status.get("ok") is not True
        or status.get("tabId") != tab_id
        or (require_send_ready and status.get("blocked") is not False)
        or not isinstance(status_tabs, list)
    ):
        _fail("agentify_preexisting_tab_status_invalid")
    status_matches = [
        row
        for row in status_tabs
        if isinstance(row, dict) and row.get("key") == request["stable_key"]
    ]
    if (
        len(status_matches) != 1
        or status_matches[0].get("id") != tab_id
        or status_matches[0].get("vendorId") != request["provider"]
        or status_matches[0].get("url") != request["conversation_url"]
    ):
        _fail("agentify_preexisting_tab_status_identity_mismatch")
    if require_send_ready and status.get("promptVisible") is not True:
        _fail("agentify_preexisting_tab_prompt_unavailable")
    runtime = status.get("runtime")
    active_queries = runtime.get("activeQueries") if isinstance(runtime, dict) else None
    if not isinstance(active_queries, list):
        _fail("agentify_preexisting_tab_runtime_invalid")
    if require_send_ready and (
        status.get("activeQuery") is not None
        or any(
            not isinstance(active, dict)
            or active.get("tabId") == tab_id
            or active.get("scope") == f"key:{request['stable_key']}"
            for active in active_queries
        )
    ):
        _fail("agentify_preexisting_tab_busy")
    return tab_id


def _agentify_session(
    request: dict[str, Any], state_dir: Path, *, require_send_ready: bool = True
) -> tuple[str, str, str]:
    if not state_dir.is_absolute():
        _fail("agentify_state_dir_not_absolute")
    state_dir = state_dir.resolve(strict=False)
    state = _load_json(state_dir / "state.json")
    port = _required_int(state.get("port"), "agentify_port", minimum=1, maximum=65535)
    server_id = _required_text(state.get("serverId"), "agentify_server_id", maximum=256)
    if state.get("sourceCommit") != AGENTIFY_REQUIRED_COMMIT or state.get("sourceDirty") is not False:
        _fail("agentify_state_source_identity_mismatch")
    try:
        token = (state_dir / "token.txt").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise TransportError("agentify_token_unreadable") from exc
    _required_text(token, "agentify_token", maximum=4096)
    base = f"http://127.0.0.1:{port}"
    health = _http_json(f"{base}/health", timeout_seconds=10.0)
    if (
        health.get("ok") is not True
        or health.get("serverId") != server_id
        or health.get("sourceCommit") != AGENTIFY_REQUIRED_COMMIT
        or health.get("sourceDirty") is not False
    ):
        _fail("agentify_server_identity_mismatch")
    tab_id = _require_preexisting_review_tab(
        base, token, request, require_send_ready=require_send_ready
    )
    return base, token, tab_id


def call_agentify(request: dict[str, Any], *, state_dir: Path, verify_existing: bool) -> dict[str, Any]:
    base, token, _ = _agentify_session(
        request, state_dir, require_send_ready=not verify_existing
    )
    timeout_seconds = request["timeout_ms"] / 1000.0 + 30.0
    result = _http_json(
        f"{base}/review-query",
        token=token,
        body=agentify_body(request, verify_existing=verify_existing),
        timeout_seconds=timeout_seconds,
    )
    if result.get("ok") is not True or not isinstance(result.get("receipt"), dict):
        _fail("agentify_receipt_missing")
    return result["receipt"]

def _ledger_operation(state_dir: Path, operation_key: str) -> dict[str, Any]:
    if not state_dir.is_absolute():
        _fail("agentify_state_dir_not_absolute")
    ledger_path = state_dir.resolve(strict=False) / "review-transport.json"
    if not ledger_path.exists():
        return {}
    ledger = _load_json(ledger_path)
    operations = ledger.get("operations")
    operation = operations.get(operation_key) if isinstance(operations, dict) else None
    return operation if isinstance(operation, dict) else {}


def _send_confirmation_predicates(
    operation: dict[str, Any], request: dict[str, Any], tab_id: str
) -> dict[str, bool]:
    submitted_at = operation.get("submittedAt")
    return {
        "sendCount": operation.get("sendCount") == 1,
        "sendActionCount": operation.get("sendActionCount") == 1,
        "userMessageId": isinstance(operation.get("userMessageId"), str)
        and bool(operation.get("userMessageId")),
        "submittedAt": isinstance(submitted_at, int)
        and not isinstance(submitted_at, bool)
        and submitted_at > 0,
        "stableKey": operation.get("stableKey") == request["stable_key"],
        "provider": operation.get("provider") == request["provider"],
        "conversationUrl": operation.get("conversationUrl")
        == request["conversation_url"],
        "conversationId": operation.get("conversationId")
        == request["conversation_id"],
        "tabId": operation.get("tabId") == tab_id,
    }


def _user_message_present(operation: dict[str, Any]) -> bool:
    user_message_id = operation.get("userMessageId")
    return isinstance(user_message_id, str) and bool(user_message_id)


def _fail_post_send(
    code: str,
    *,
    operation: dict[str, Any],
    request: dict[str, Any],
    tab_id: str,
    **facts: Any,
) -> None:
    _emit_lifecycle(
        "POST_SEND_BLOCKED",
        predicates=_send_confirmation_predicates(operation, request, tab_id),
        operation_status=operation.get("status"),
        **facts,
    )
    _fail(code)


def _emit_lifecycle(phase: str, **facts: Any) -> None:
    print(
        "HMASD_AGENTIFY_LIFECYCLE "
        + json.dumps({"phase": phase, **facts}, ensure_ascii=True, sort_keys=True),
        flush=True,
    )


def validate_receipt(receipt: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    exact = {
        "stableKey": request["stable_key"],
        "provider": request["provider"],
        "model": request["model"],
        "conversationUrl": request["conversation_url"],
        "conversationId": request["conversation_id"],
        "idempotencyKey": request["idempotency_key"],
        "timeoutMs": request["timeout_ms"],
        "status": "COMPLETE",
        "terminalState": "NATURAL_COMPLETION_VERIFIED",
        "sendCount": 1,
        "sendActionCount": 1,
    }
    for field, expected in exact.items():
        if receipt.get(field) != expected:
            _fail(f"receipt_{field}_mismatch")
    _required_text(receipt.get("operationId"), "receipt_operation_id", maximum=256)
    fingerprint = _required_text(receipt.get("requestFingerprint"), "receipt_request_fingerprint", maximum=64)
    if not SHA256_RE.fullmatch(fingerprint):
        _fail("receipt_request_fingerprint_invalid")
    user_message_id = _required_text(receipt.get("userMessageId"), "receipt_user_message_id", maximum=512)
    assistant_message_id = _required_text(receipt.get("assistantMessageId"), "receipt_assistant_message_id", maximum=512)
    if user_message_id == assistant_message_id:
        _fail("receipt_message_identity_collision")
    response_text = _required_nonempty_text_preserve(
        receipt.get("responseText"), "receipt_response_text", maximum=2_000_000
    )
    response_sha256 = _required_text(receipt.get("responseSha256"), "receipt_response_sha256", maximum=64)
    if not SHA256_RE.fullmatch(response_sha256) or _sha256(response_text.encode("utf-8")) != response_sha256:
        _fail("receipt_response_hash_mismatch")
    created_at = _required_int(receipt.get("createdAt"), "receipt_created_at", minimum=1)
    prepared_at = _required_int(receipt.get("preparedAt"), "receipt_prepared_at", minimum=created_at)
    submitted_at = _required_int(receipt.get("submittedAt"), "receipt_submitted_at", minimum=prepared_at)
    completed_at = _required_int(receipt.get("completedAt"), "receipt_completed_at", minimum=submitted_at)
    deadline_at = _required_int(receipt.get("deadlineAt"), "receipt_deadline_at", minimum=completed_at)
    if deadline_at - created_at != request["timeout_ms"]:
        _fail("receipt_deadline_mismatch")
    snapshots = receipt.get("snapshots")
    if not isinstance(snapshots, list) or len(snapshots) != 2:
        _fail("receipt_snapshot_count_mismatch")
    observations: list[int] = []
    for snapshot in snapshots:
        if not isinstance(snapshot, dict):
            _fail("receipt_snapshot_invalid")
        if snapshot.get("assistantMessageId") != assistant_message_id or snapshot.get("textSha256") != response_sha256:
            _fail("receipt_snapshot_identity_mismatch")
        observations.append(_required_int(snapshot.get("observedAt"), "receipt_snapshot_time", minimum=1))
    if observations[0] < submitted_at or observations[1] > completed_at:
        _fail("receipt_snapshot_outside_response_interval")
    if observations[1] - observations[0] < 3000:
        _fail("receipt_snapshot_stability_too_short")
    controls = receipt.get("controls")
    if not isinstance(controls, dict):
        _fail("receipt_controls_invalid")
    for prohibited in ("stop", "continue", "retry"):
        if controls.get(prohibited) is not False:
            _fail(f"receipt_control_{prohibited}_active")
    if not isinstance(controls.get("answerNow"), bool):
        _fail("receipt_control_answer_now_invalid")
    if receipt.get("clickedControls") != []:
        _fail("receipt_prohibited_control_activated")
    return receipt


def _atomic_write_new(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            if path.read_bytes() == data:
                return
        except OSError as exc:
            raise TransportError("existing_output_unreadable") from exc
        _fail("output_exists_with_different_bytes")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _validated_inputs(request_path: Path, receipt_path: Path | None = None) -> tuple[dict[str, Any], dict[str, Any] | None, Path]:
    repo_root = _repo_root()
    raw_request = _load_json(request_path)
    request = validate_request(raw_request, repo_root=repo_root)
    runtime_roots = _owner_roots(repo_root, request["transport_owner"], "runtime")
    _require_within(request_path, runtime_roots, "request_path")
    receipt = None
    if receipt_path is not None:
        _require_within(receipt_path, runtime_roots, "receipt_path")
        receipt = _load_json(receipt_path)
    return request, receipt, repo_root


def _receipt_bytes(receipt: dict[str, Any]) -> bytes:
    return (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def command_provision_direction(args: argparse.Namespace) -> None:
    repo_root = _repo_root()
    assignment_identity = _required_text(
        args.assignment_identity, "assignment_identity", maximum=1024
    )
    if not assignment_identity.startswith("IR_DIRECTION_REVIEW:"):
        _fail("direction_provision_identity_invalid")
    source_path = _require_within(
        args.prompt_source,
        [repo_root / "local_research"],
        "prompt_source",
    )
    review_root = (repo_root / "local_research" / "pro_reviews").resolve(strict=False)
    if _is_within(source_path, review_root):
        _fail("prompt_source_inside_review_archive")
    if not source_path.is_file():
        _fail("prompt_source_missing")
    prompt_path = _require_within(
        args.prompt_path,
        [review_root],
        "prompt_path",
    )
    try:
        relative_prompt = prompt_path.relative_to(review_root)
    except ValueError:
        _fail("direction_prompt_outside_review_archive")
    if len(relative_prompt.parts) != 2 or prompt_path.name != "20_PRO_OPEN_QUESTION.md":
        _fail("direction_prompt_item_depth_invalid")
    try:
        prompt_bytes = source_path.read_bytes()
        prompt = prompt_bytes.decode("utf-8")
    except OSError as exc:
        raise TransportError("prompt_source_unreadable") from exc
    except UnicodeError as exc:
        raise TransportError("prompt_source_not_exact_utf8") from exc
    if not prompt or assignment_identity not in prompt:
        _fail("prompt_source_identity_mismatch")
    _atomic_write_new(prompt_path, prompt_bytes)
    print(
        "HMASD_DIRECTION_REVIEW_ITEM_PROVISIONED "
        f"assignment_identity={assignment_identity} prompt={prompt_path}"
    )


def command_prepare(args: argparse.Namespace) -> None:
    repo_root = _repo_root()
    owner = _required_text(args.owner, "transport_owner", maximum=128)
    if owner not in OWNER_KEYS:
        _fail("invalid_transport_owner")
    stable_key = _required_text(args.stable_key, "stable_key", maximum=128)
    if not KEY_RE.fullmatch(stable_key) or stable_key not in OWNER_KEYS[owner]:
        _fail("stable_key_owner_mismatch")
    assignment_identity = _required_text(
        args.assignment_identity, "assignment_identity", maximum=1024
    )
    operation_key = _required_text(args.operation_key, "operation_key", maximum=128)
    if not KEY_RE.fullmatch(operation_key):
        _fail("invalid_operation_key")
    model = _required_text(args.model, "model", maximum=128)
    conversation_url = _required_text(args.conversation_url, "conversation_url", maximum=2048)
    conversation_id = _required_text(args.conversation_id, "conversation_id", maximum=256)
    parsed = urlparse(conversation_url)
    if (
        parsed.scheme != "https"
        or parsed.netloc != "chatgpt.com"
        or parsed.query
        or parsed.fragment
        or parsed.path != f"/c/{conversation_id}"
    ):
        _fail("conversation_identity_mismatch")
    timeout_ms = _required_int(
        args.timeout_ms, "timeout_ms", minimum=3000, maximum=MAX_TIMEOUT_MS
    )
    prompt_path = _require_within(
        args.prompt_path,
        _owner_roots(repo_root, owner, "archive"),
        "prompt_path",
    )
    if not prompt_path.is_file():
        _fail("prompt_path_missing")
    try:
        prompt_bytes = prompt_path.read_bytes()
        prompt = prompt_bytes.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise TransportError("prompt_not_exact_utf8") from exc
    if not prompt:
        _fail("prompt_empty")
    if assignment_identity not in prompt:
        _fail("assignment_identity_not_in_prompt")
    selection_path = _require_within(
        args.selection,
        _owner_roots(repo_root, owner, "runtime"),
        "backend_selection_path",
    )
    if selection_path.name != "TRANSPORT_BACKEND.json":
        _fail("backend_selection_filename_mismatch")
    selection = {
        "schema_version": SCHEMA_VERSION,
        "assignment_identity": assignment_identity,
        "transport_backend": "agentify",
        "operation_key": operation_key,
    }
    request_path = _require_within(
        args.request,
        _owner_roots(repo_root, owner, "runtime"),
        "request_path",
    )
    request = {
        "schema_version": SCHEMA_VERSION,
        "transport_backend": "agentify",
        "transport_owner": owner,
        "stable_key": stable_key,
        "provider": "chatgpt",
        "model": model,
        "conversation_url": conversation_url,
        "conversation_id": conversation_id,
        "idempotency_key": operation_key,
        "assignment_identity": assignment_identity,
        "backend_selection_path": str(selection_path),
        "prompt_path": str(prompt_path),
        "timeout_ms": timeout_ms,
    }
    selection_bytes = (
        json.dumps(selection, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    request_bytes = (
        json.dumps(request, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    _atomic_write_new(selection_path, selection_bytes)
    validate_request(request, repo_root=repo_root)
    _atomic_write_new(request_path, request_bytes)
    print(
        "HMASD_AGENTIFY_REQUEST_PREPARED "
        f"assignment_identity={assignment_identity} operation_key={operation_key} "
        f"selection={selection_path} request={request_path}"
    )
    _emit_lifecycle("PREPARED", operation_key=operation_key)


def command_submit_worker(args: argparse.Namespace) -> None:
    request, _, repo_root = _validated_inputs(args.request)
    receipt_path = _require_within(
        args.receipt,
        _owner_roots(repo_root, request["transport_owner"], "runtime"),
        "receipt_path",
    )
    receipt = call_agentify(request, state_dir=args.state_dir, verify_existing=args.verify_existing)
    validate_receipt(receipt, request)
    _atomic_write_new(receipt_path, _receipt_bytes(receipt))
    print(
        "HMASD_AGENTIFY_TRANSPORT_COMPLETE "
        f"operation_id={receipt['operationId']} receipt={receipt_path}"
    )


def _spawn_submit_worker(args: argparse.Namespace, verify_existing: bool) -> subprocess.Popen[str]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "_submit-worker",
        "--request",
        str(args.request),
        "--receipt",
        str(args.receipt),
        "--state-dir",
        str(args.state_dir),
    ]
    if verify_existing:
        command.append("--verify-existing")
    return subprocess.Popen(
        command,
        cwd=str(_repo_root()),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _terminate_owned_worker(worker: subprocess.Popen[str]) -> None:
    worker.terminate()
    try:
        worker.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        worker.kill()
        worker.wait(timeout=5.0)


def _complete_from_existing(
    request: dict[str, Any], state_dir: Path, receipt_path: Path
) -> dict[str, Any]:
    receipt = call_agentify(request, state_dir=state_dir, verify_existing=True)
    validate_receipt(receipt, request)
    _atomic_write_new(receipt_path, _receipt_bytes(receipt))
    return receipt


def command_submit(args: argparse.Namespace) -> None:
    request, _, repo_root = _validated_inputs(args.request)
    receipt_path = _require_within(
        args.receipt,
        _owner_roots(repo_root, request["transport_owner"], "runtime"),
        "receipt_path",
    )
    operation = _ledger_operation(args.state_dir, request["idempotency_key"])
    existing = _user_message_present(operation)
    if args.verify_existing:
        print(f"HMASD_AGENTIFY_EXISTING_USER_MESSAGE present={str(existing).lower()}")
        if not existing:
            return
    started = time.monotonic()
    overall_deadline = started + request["timeout_ms"] / 1000.0 + 30.0
    if existing:
        try:
            _, _, tab_id = _agentify_session(
                request, args.state_dir, require_send_ready=False
            )
        except TransportError as exc:
            _emit_lifecycle("POST_SEND_BLOCKED", live_tab_error=str(exc))
            raise TransportError("post_send_blocked_live_tab_identity") from exc
        predicates = _send_confirmation_predicates(operation, request, tab_id)
        if not all(predicates.values()):
            _fail_post_send(
                "post_send_blocked_ledger_identity_unconfirmed",
                operation=operation,
                request=request,
                tab_id=tab_id,
            )
        _emit_lifecycle("MESSAGE_CONFIRMED", predicates=predicates)
        _emit_lifecycle("GENERATING", operation_status=operation.get("status"))
        next_generation_report = started + GENERATION_REPORT_SECONDS
        while time.monotonic() <= overall_deadline:
            operation = _ledger_operation(args.state_dir, request["idempotency_key"])
            status = operation.get("status")
            if status == "COMPLETE":
                receipt = _complete_from_existing(request, args.state_dir, receipt_path)
                _emit_lifecycle("STABLE_COMPLETE", operation_id=receipt["operationId"])
                print(
                    "HMASD_AGENTIFY_TRANSPORT_COMPLETE "
                    f"operation_id={receipt['operationId']} receipt={receipt_path}"
                )
                return
            if status in {"BLOCKED", "ERROR"}:
                break
            now = time.monotonic()
            if now >= next_generation_report:
                _emit_lifecycle("GENERATING", operation_status=status)
                next_generation_report = now + GENERATION_REPORT_SECONDS
            time.sleep(LEDGER_POLL_SECONDS)
        _emit_lifecycle(
            "POST_SEND_BLOCKED",
            predicates=_send_confirmation_predicates(operation, request, tab_id),
            operation_status=operation.get("status"),
        )
        _fail("post_send_blocked_existing_operation_incomplete")

    _, _, tab_id = _agentify_session(request, args.state_dir)
    _emit_lifecycle("TAB_READY", tab_id=tab_id)
    worker = _spawn_submit_worker(args, False)
    _emit_lifecycle("DISPATCH_STARTED", worker_pid=worker.pid)
    dispatch_started = time.monotonic()
    confirmation_deadline = dispatch_started + SEND_CONFIRM_TIMEOUT_SECONDS
    confirmed = False
    next_generation_report = dispatch_started + GENERATION_REPORT_SECONDS

    while worker.poll() is None:
        operation = _ledger_operation(args.state_dir, request["idempotency_key"])
        predicates = _send_confirmation_predicates(operation, request, tab_id)
        now = time.monotonic()
        if _user_message_present(operation) and not all(predicates.values()):
            _fail_post_send(
                "post_send_blocked_partial_message_identity",
                operation=operation,
                request=request,
                tab_id=tab_id,
            )
        if all(predicates.values()) and not confirmed:
            confirmed = True
            _emit_lifecycle("MESSAGE_CONFIRMED", predicates=predicates)
            _emit_lifecycle("GENERATING", operation_status=operation.get("status"))
            next_generation_report = now + GENERATION_REPORT_SECONDS
        if not confirmed and now >= confirmation_deadline:
            operation = _ledger_operation(args.state_dir, request["idempotency_key"])
            predicates = _send_confirmation_predicates(operation, request, tab_id)
            if _user_message_present(operation) and not all(predicates.values()):
                _fail_post_send(
                    "post_send_blocked_partial_message_identity",
                    operation=operation,
                    request=request,
                    tab_id=tab_id,
                )
            if not all(predicates.values()):
                _terminate_owned_worker(worker)
                operation = _ledger_operation(
                    args.state_dir, request["idempotency_key"]
                )
                predicates = _send_confirmation_predicates(operation, request, tab_id)
                if _user_message_present(operation) and not all(predicates.values()):
                    _fail_post_send(
                        "post_send_blocked_partial_message_identity",
                        operation=operation,
                        request=request,
                        tab_id=tab_id,
                    )
                if not all(predicates.values()):
                    _emit_lifecycle("PRE_SEND_BLOCKED", predicates=predicates)
                    _fail("pre_send_blocked_unconfirmed_user_message")
            confirmed = True
            _emit_lifecycle("MESSAGE_CONFIRMED", predicates=predicates)
            _emit_lifecycle("GENERATING", operation_status=operation.get("status"))
        if confirmed and now >= next_generation_report:
            _emit_lifecycle("GENERATING", operation_status=operation.get("status"))
            next_generation_report = now + GENERATION_REPORT_SECONDS
        time.sleep(LEDGER_POLL_SECONDS)

    _, worker_stderr = worker.communicate()
    operation = _ledger_operation(args.state_dir, request["idempotency_key"])
    predicates = _send_confirmation_predicates(operation, request, tab_id)
    if _user_message_present(operation) and not all(predicates.values()):
        _fail_post_send(
            "post_send_blocked_partial_message_identity",
            operation=operation,
            request=request,
            tab_id=tab_id,
            worker_returncode=worker.returncode,
        )
    if all(predicates.values()) and not confirmed:
        confirmed = True
        _emit_lifecycle("MESSAGE_CONFIRMED", predicates=predicates)

    receipt = None
    if worker.returncode == 0:
        receipt = _load_json(receipt_path)
        validate_receipt(receipt, request)
    while not confirmed and time.monotonic() < confirmation_deadline:
        operation = _ledger_operation(args.state_dir, request["idempotency_key"])
        predicates = _send_confirmation_predicates(operation, request, tab_id)
        if _user_message_present(operation) and not all(predicates.values()):
            _fail_post_send(
                "post_send_blocked_partial_message_identity",
                operation=operation,
                request=request,
                tab_id=tab_id,
                worker_returncode=worker.returncode,
            )
        if all(predicates.values()):
            confirmed = True
            _emit_lifecycle("MESSAGE_CONFIRMED", predicates=predicates)
            break
        time.sleep(LEDGER_POLL_SECONDS)

    if not confirmed:
        operation = _ledger_operation(args.state_dir, request["idempotency_key"])
        predicates = _send_confirmation_predicates(operation, request, tab_id)
        if _user_message_present(operation) or receipt is not None:
            _fail_post_send(
                "post_send_blocked_ledger_identity_unconfirmed",
                operation=operation,
                request=request,
                tab_id=tab_id,
                worker_returncode=worker.returncode,
                receipt_send_evidence=receipt is not None,
            )
        _emit_lifecycle(
            "PRE_SEND_BLOCKED",
            predicates=predicates,
            worker_returncode=worker.returncode,
        )
        _fail("pre_send_blocked_submit_worker_failed")

    if worker.returncode == 0:
        assert receipt is not None
        _emit_lifecycle("STABLE_COMPLETE", operation_id=receipt["operationId"])
        print(
            "HMASD_AGENTIFY_TRANSPORT_COMPLETE "
            f"operation_id={receipt['operationId']} receipt={receipt_path}"
        )
        return

    while time.monotonic() <= overall_deadline:
        operation = _ledger_operation(args.state_dir, request["idempotency_key"])
        status = operation.get("status")
        if status == "COMPLETE":
            receipt = _complete_from_existing(request, args.state_dir, receipt_path)
            _emit_lifecycle("STABLE_COMPLETE", operation_id=receipt["operationId"])
            print(
                "HMASD_AGENTIFY_TRANSPORT_COMPLETE "
                f"operation_id={receipt['operationId']} receipt={receipt_path}"
            )
            return
        if status in {"BLOCKED", "ERROR"}:
            break
        if time.monotonic() >= next_generation_report:
            _emit_lifecycle("GENERATING", operation_status=status)
            next_generation_report = time.monotonic() + GENERATION_REPORT_SECONDS
        time.sleep(LEDGER_POLL_SECONDS)
    _emit_lifecycle(
        "POST_SEND_BLOCKED",
        predicates=_send_confirmation_predicates(operation, request, tab_id),
        operation_status=operation.get("status"),
        worker_returncode=worker.returncode,
        worker_error=worker_stderr.strip()[:512],
    )
    _fail("post_send_blocked_submit_worker_failed")


def command_verify(args: argparse.Namespace) -> None:
    request, receipt, _ = _validated_inputs(args.request, args.receipt)
    assert receipt is not None
    validate_receipt(receipt, request)
    print(
        "HMASD_AGENTIFY_RECEIPT_OK "
        f"operation_id={receipt['operationId']} receipt={args.receipt.resolve()}"
    )


def command_archive(args: argparse.Namespace) -> None:
    request, receipt, repo_root = _validated_inputs(args.request, args.receipt)
    assert receipt is not None
    validate_receipt(receipt, request)
    raw_output = _require_within(
        args.raw_output,
        _owner_roots(repo_root, request["transport_owner"], "archive"),
        "raw_output",
    )
    raw_bytes = receipt["responseText"].encode("utf-8")
    _atomic_write_new(raw_output, raw_bytes)
    try:
        archived_bytes = raw_output.read_bytes()
    except OSError as exc:
        raise TransportError("raw_archive_reread_failed") from exc
    if archived_bytes != raw_bytes:
        _fail("raw_archive_byte_mismatch")
    print(
        "HMASD_AGENTIFY_RAW_ARCHIVED "
        f"operation_id={receipt['operationId']} path={raw_output}"
    )
    _emit_lifecycle("ARCHIVED", operation_id=receipt["operationId"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    provision = subparsers.add_parser("provision-direction")
    provision.add_argument("--assignment-identity", required=True)
    provision.add_argument("--prompt-source", type=Path, required=True)
    provision.add_argument("--prompt-path", type=Path, required=True)
    provision.set_defaults(handler=command_provision_direction)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--owner", required=True)
    prepare.add_argument("--stable-key", required=True)
    prepare.add_argument("--model", required=True)
    prepare.add_argument("--conversation-url", required=True)
    prepare.add_argument("--conversation-id", required=True)
    prepare.add_argument("--assignment-identity", required=True)
    prepare.add_argument("--operation-key", required=True)
    prepare.add_argument("--prompt-path", type=Path, required=True)
    prepare.add_argument("--timeout-ms", type=int, default=MAX_TIMEOUT_MS)
    prepare.add_argument("--selection", type=Path, required=True)
    prepare.add_argument("--request", type=Path, required=True)
    prepare.set_defaults(handler=command_prepare)
    for name in ("submit", "_submit-worker", "verify", "archive"):
        command = subparsers.add_parser(name)
        command.add_argument("--request", type=Path, required=True)
        command.add_argument("--receipt", type=Path, required=True)
        if name in {"submit", "_submit-worker"}:
            command.add_argument(
                "--state-dir",
                type=Path,
                default=Path(os.environ.get("AGENTIFY_DESKTOP_STATE_DIR", Path.home() / ".agentify-desktop")),
            )
            command.add_argument("--verify-existing", action="store_true")
            command.set_defaults(
                handler=command_submit if name == "submit" else command_submit_worker
            )
        elif name == "verify":
            command.set_defaults(handler=command_verify)
        else:
            command.add_argument("--raw-output", type=Path, required=True)
            command.set_defaults(handler=command_archive)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        args.handler(args)
        return 0
    except TransportError as exc:
        print(f"HMASD_AGENTIFY_TRANSPORT_ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
