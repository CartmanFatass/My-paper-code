"""Fail-open SHADOW hook entrypoint for the semantic MVP.

The SHADOW handler is deliberately observational.  It records a small,
sanitized diagnostic and always returns a neutral continuation response; it
does not inspect transcripts, change workflow state, block a tool, or inject
context into the model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

# Keep imports explicit so this module remains usable with the repository's
# package layout and does not introduce an SDK/App Server dependency.
from .constants import SHADOW_MODE, STATE_DIR_ENV
from .db import DEFAULT_STATE_PATH
from .store import SemanticStore


SUPPORTED_EVENTS = frozenset(
    {"SessionStart", "SubagentStart", "SubagentStop", "Stop", "PreToolUse"}
)
EVENT_KINDS = {
    "SessionStart": "SESSION_STARTED",
    "SubagentStart": "SUBAGENT_STARTED",
    "SubagentStop": "SUBAGENT_STOPPED",
    "Stop": "STOP_OBSERVED",
    "PreToolUse": "PRE_TOOL_USE_OBSERVED",
}
MAX_PREVIEW_BYTES = 2048


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def state_dir_from_environment() -> Path:
    """Resolve state relative to this repository unless an absolute path is given."""
    configured = os.environ.get(STATE_DIR_ENV)
    if configured:
        path = Path(configured)
        return path if path.is_absolute() else _repo_root() / path
    return _repo_root() / DEFAULT_STATE_PATH.parent


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return repr(value)


def _canonical_json(value: Any) -> str:
    return json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _diagnostic_payload(payload: Mapping[str, object], event: str) -> dict[str, object]:
    """Return bounded metadata; never copy arbitrary hook input to diagnostics."""
    tool_input = payload.get("tool_input")
    tool_input_json = _canonical_json(tool_input) if tool_input is not None else ""
    selected = {
        "hook_event_name": event,
        "session_id": str(payload.get("session_id") or ""),
        "turn_id": str(payload.get("turn_id") or ""),
        "tool_name": str(payload.get("tool_name") or ""),
        "tool_use_id": str(payload.get("tool_use_id") or ""),
        "tool_input_sha256": hashlib.sha256(tool_input_json.encode("utf-8")).hexdigest()
        if tool_input is not None
        else None,
    }
    preview = _canonical_json(selected)
    # The preview consists only of selected metadata and is bounded by bytes.
    selected["payload_preview"] = preview.encode("utf-8")[:MAX_PREVIEW_BYTES].decode(
        "utf-8", errors="ignore"
    )
    return selected


def _append_audit(state_dir: Path, kind: str, payload: Mapping[str, object]) -> None:
    """Append one JSON diagnostic, swallowing all I/O failures (fail open)."""
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        record = {"event": kind, **_json_safe(payload)}
        with (state_dir / "audit.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    except Exception:
        return


def _neutral_response() -> dict[str, object]:
    return {"continue": True}


def handle_hook(
    payload: Mapping[str, object], mode: str, store: SemanticStore | None
) -> dict[str, object] | None:
    """Observe one hook invocation and return a behavior-neutral response."""
    event = str(payload.get("hook_event_name") or payload.get("event") or "") if isinstance(payload, Mapping) else ""
    kind = EVENT_KINDS.get(event, "UNKNOWN_HOOK_EVENT")
    diagnostic = _diagnostic_payload(payload if isinstance(payload, Mapping) else {}, event)
    diagnostic["mode"] = mode
    if store is not None:
        try:
            store.append_event(
                None,
                kind,
                diagnostic.get("session_id") or None,
                diagnostic,
                f"HOOK:{uuid.uuid4().hex}",
            )
        except Exception:
            # A broken local store must never turn an observational hook into
            # a behavioral gate.
            pass
        try:
            _append_audit(store.path.parent, kind, diagnostic)
        except Exception:
            pass
    return _neutral_response()


def _parse_stdin() -> Mapping[str, object] | None:
    try:
        text = sys.stdin.read()
        value = json.loads(text)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, Mapping) else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SHADOW semantic MVP hook")
    parser.add_argument("--mode", default=SHADOW_MODE)
    args = parser.parse_args(argv)
    payload = _parse_stdin()
    if payload is None:
        _append_audit(state_dir_from_environment(), "MALFORMED_HOOK_INPUT", {})
        return 0

    state_dir = state_dir_from_environment()
    store: SemanticStore | None = None
    try:
        store = SemanticStore(state_dir / "state.sqlite3").initialize()
        response = handle_hook(payload, args.mode, store)
    except Exception as exc:
        _append_audit(
            state_dir,
            "HOOK_FAIL_OPEN",
            {"exception_class": type(exc).__name__},
        )
        response = _neutral_response()
    finally:
        if store is not None:
            try:
                store.close()
            except Exception:
                pass
    if response is not None:
        sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised by subprocess tests
    raise SystemExit(main())
