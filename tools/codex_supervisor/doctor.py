"""Read-only observer doctor. Does not launch App Server or migrate the semantic DB."""

from __future__ import annotations

from pathlib import Path

from .codex_binary import CodexBinaryError, read_codex_version, resolve_codex_binary
from .config import load_observer_config
from .db import SCHEMA_VERSION, connect


def collect_doctor(
    repo_root: Path,
    *,
    runtime_home: Path | None = None,
    codex_bin: str | None = None,
) -> dict[str, object]:
    config = load_observer_config(repo_root, runtime_home)
    binary = None
    version = None
    try:
        binary = resolve_codex_binary(codex_bin)
        version = read_codex_version(binary)
    except (CodexBinaryError, Exception) as exc:
        binary_error = type(exc).__name__
    else:
        binary_error = None
    schema_present = False
    if version:
        schema_dir = config.runtime_home / "schema"
        schema_present = schema_dir.is_dir() and any(schema_dir.rglob("capture-manifest.json"))
    observer_schema = None
    active_bindings = 0
    db_path = config.runtime_home / "state.sqlite3"
    if db_path.is_file():
        connection = connect(db_path)
        observer_schema = int(connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] or 0)
        try:
            active_bindings = int(
                connection.execute(
                    "SELECT COUNT(*) FROM managed_actor_bindings WHERE binding_state = 'ACTIVE'"
                ).fetchone()[0]
            )
        except Exception:
            active_bindings = 0
        connection.close()
    return {
        "status": "OK" if binary_error is None else "DEGRADED",
        "phase": 1,
        "observer_only": True,
        "automatic_turn_start_enabled": False,
        "automatic_wake_enabled": False,
        "mailbox_enabled": False,
        "managed_actor_binding_enabled": True,
        "managed_actor_hosting_enabled": True,
        "allowed_actor_kinds": ["OPERATIONAL_ROOT", "PORTFOLIO"],
        "active_binding_count": active_bindings,
        "codex_binary": str(binary) if binary else None,
        "codex_version": version,
        "binary_error": binary_error,
        "schema_capture_present": schema_present,
        "runtime_home_external": True,
        "runtime_home": str(config.runtime_home),
        "observer_schema_version": observer_schema or SCHEMA_VERSION,
        "semantic_ledger_mutation_enabled": False,
        "unexpected_server_request_policy": config.unexpected_server_request_policy,
    }
