"""External observer store and raw transport logs. No deletion API."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .db import connect, initialize_database
from .models import EndKind, NormalizedEvent, ProtocolIds, RpcShape
from .protocol import canonical_json

ALLOWED_END_KINDS = {member.value for member in EndKind}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


class ObserverStore:
    def __init__(self, runtime_home: Path) -> None:
        self.runtime_home = Path(runtime_home)
        self.runtime_home.mkdir(parents=True, exist_ok=True)
        self.path = self.runtime_home / "state.sqlite3"
        self.connection = connect(self.path)
        self._lock = threading.RLock()
        initialize_database(self.connection)

    def close(self) -> None:
        with self._lock:
            self.connection.close()

    def start_run(
        self,
        *,
        codex_binary: str,
        codex_version: str,
        client_name: str,
        process_id: int | None,
    ) -> str:
        run_id = _new_id("run")
        now = _now()
        with self._lock, self.connection:
            self.connection.execute(
                """INSERT INTO observer_runs (
                    run_id, codex_binary, codex_version, client_name, process_id,
                    started_at, initialized_at, ended_at, exit_code, end_kind, runtime_home
                ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, ?)""",
                (
                    run_id,
                    codex_binary,
                    codex_version,
                    client_name,
                    process_id,
                    now,
                    str(self.runtime_home),
                ),
            )
        raw_dir = self.raw_dir(run_id)
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "stdin.jsonl").touch()
        (raw_dir / "stdout.jsonl").touch()
        (raw_dir / "stderr.log").touch()
        return run_id

    def raw_dir(self, run_id: str) -> Path:
        return self.runtime_home / "raw" / run_id

    def append_raw_file(self, run_id: str, name: str, data: bytes) -> None:
        path = self.raw_dir(run_id) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab") as handle:
            handle.write(data)

    def mark_initialized(self, run_id: str) -> None:
        with self._lock, self.connection:
            self.connection.execute(
                "UPDATE observer_runs SET initialized_at = ? WHERE run_id = ?",
                (_now(), run_id),
            )

    def end_run(self, run_id: str, end_kind: str, exit_code: int | None = None) -> None:
        if end_kind not in ALLOWED_END_KINDS:
            raise ValueError(f"unknown end_kind: {end_kind}")
        with self._lock, self.connection:
            self.connection.execute(
                """UPDATE observer_runs
                SET ended_at = ?, end_kind = ?, exit_code = ?
                WHERE run_id = ? AND ended_at IS NULL""",
                (_now(), end_kind, exit_code, run_id),
            )

    def recover_incomplete_runs(self) -> list[str]:
        now = _now()
        with self._lock, self.connection:
            rows = self.connection.execute(
                "SELECT run_id FROM observer_runs WHERE ended_at IS NULL"
            ).fetchall()
            recovered = []
            for row in rows:
                self.connection.execute(
                    """UPDATE observer_runs
                    SET ended_at = ?, end_kind = ?, exit_code = NULL
                    WHERE run_id = ? AND ended_at IS NULL""",
                    (now, EndKind.PROCESS_EXIT.value, row[0]),
                )
                recovered.append(str(row[0]))
            return recovered

    def record_raw_message(
        self,
        *,
        run_id: str,
        direction: str,
        transport_seq: int,
        rpc_shape: RpcShape | str,
        ids: ProtocolIds,
        payload: Mapping[str, Any],
        observed_at: str | None = None,
    ) -> int:
        shape = rpc_shape.value if isinstance(rpc_shape, RpcShape) else str(rpc_shape)
        encoded = canonical_json(dict(payload))
        with self._lock, self.connection:
            cursor = self.connection.execute(
                """INSERT INTO raw_messages (
                    run_id, direction, transport_seq, rpc_shape, request_id, method,
                    thread_id, turn_id, item_id, canonical_json, observed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    direction,
                    transport_seq,
                    shape,
                    ids.request_id,
                    ids.method,
                    ids.thread_id,
                    ids.turn_id,
                    ids.item_id,
                    encoded,
                    observed_at or _now(),
                ),
            )
            return int(cursor.lastrowid)

    def record_effect_write_start(
        self,
        *,
        effect_id: str,
        run_id: str,
        method: str,
        payload: Mapping[str, Any],
        params: Mapping[str, Any],
        request_class: str,
        extra_transitions: list[Any] | None = None,
        extra_hooks: list[Any] | None = None,
        request_override: Mapping[str, Any] | None = None,
        final_owner_guard: Callable[[object], None] | None = None,
    ) -> dict[str, Any]:
        from .durability.effects import EffectJournal, _canonical_request
        from .durability.transaction import DurabilityError, DurabilityTransaction
        from .durability.transitions import TransitionKernel
        from .protocol import extract_protocol_ids

        ids = extract_protocol_ids(payload)
        client_request_id = str(payload.get("id") or ids.request_id or "")
        request_row_id = _new_id("req")
        encoded = canonical_json(dict(payload))
        params_json = canonical_json(dict(params))
        now = _now()
        with self._lock:
            if self.connection.in_transaction:
                raise DurabilityError("write-start requires transaction ownership")
            with DurabilityTransaction(self.connection):
                # An override is the request that will actually cross the
                # transport boundary.  Install it transactionally before the
                # final ownership/contract proof so that proof cannot validate
                # a different, originally prepared request.  Any failed proof
                # rolls this update back with the whole write-start attempt.
                if request_override is not None:
                    updated = self.connection.execute(
                        """UPDATE app_server_effects SET request_json = ?
                        WHERE effect_id = ? AND state = 'PREPARED'""",
                        (_canonical_request(request_override), effect_id),
                    )
                    if updated.rowcount != 1:
                        raise DurabilityError("request override requires a PREPARED effect")
                # This is the final supervisor-side submission boundary.  It
                # must run after BEGIN IMMEDIATE and before *any* effect,
                # aggregate, request, or raw-transport write so an ownership
                # change between the caller's preflight and this transaction
                # cannot cross WRITE_STARTED.
                if final_owner_guard is not None:
                    final_owner_guard(self.connection)
                next_seq = int(
                    self.connection.execute(
                        """SELECT COALESCE(MAX(transport_seq), 0) + 1
                        FROM raw_messages WHERE run_id = ? AND direction = 'stdin'""",
                        (run_id,),
                    ).fetchone()[0]
                )
                if extra_hooks:
                    for hook in extra_hooks:
                        hook(self.connection)
                if extra_transitions:
                    kernel = TransitionKernel(self.connection)
                    for request in extra_transitions:
                        kernel.apply(request)
                cursor = self.connection.execute(
                    """INSERT INTO raw_messages (
                        run_id, direction, transport_seq, rpc_shape, request_id, method,
                        thread_id, turn_id, item_id, canonical_json, observed_at, effect_id
                    ) VALUES (?, 'stdin', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        run_id,
                        next_seq,
                        RpcShape.REQUEST.value,
                        client_request_id,
                        method,
                        ids.thread_id,
                        ids.turn_id,
                        ids.item_id,
                        encoded,
                        now,
                        effect_id,
                    ),
                )
                raw_seq = int(cursor.lastrowid)
                journal = EffectJournal(self.connection)
                journal.claim_write(
                    effect_id,
                    run_id=run_id,
                    client_request_id=client_request_id,
                    request_row_id=request_row_id,
                    raw_request_seq=raw_seq,
                    transport_seq=next_seq,
                )
                self.connection.execute(
                    """INSERT INTO rpc_requests (
                        request_row_id, run_id, client_request_id, method, request_class,
                        params_json, attempt_count, sent_at, completed_at, outcome,
                        error_code, response_json, effect_id
                    ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, NULL, NULL, NULL, NULL, ?)""",
                    (
                        request_row_id,
                        run_id,
                        client_request_id,
                        method,
                        request_class,
                        params_json,
                        now,
                        effect_id,
                    ),
                )
        return {
            "raw_request_seq": raw_seq,
            "raw_message_seq": raw_seq,
            "transport_seq": next_seq,
            "request_row_id": request_row_id,
            "client_request_id": client_request_id,
        }

    def record_request_sent(
        self,
        *,
        run_id: str,
        client_request_id: str,
        method: str,
        request_class: str,
        params: Mapping[str, Any],
        attempt_count: int,
    ) -> str:
        row_id = _new_id("req")
        with self._lock, self.connection:
            self.connection.execute(
                """INSERT INTO rpc_requests (
                    request_row_id, run_id, client_request_id, method, request_class,
                    params_json, attempt_count, sent_at, completed_at, outcome,
                    error_code, response_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL)""",
                (
                    row_id,
                    run_id,
                    client_request_id,
                    method,
                    request_class,
                    canonical_json(dict(params)),
                    attempt_count,
                    _now(),
                ),
            )
        return row_id

    def record_request_completed(
        self,
        *,
        run_id: str,
        client_request_id: str,
        outcome: str,
        response: Mapping[str, Any] | None = None,
        error_code: int | None = None,
    ) -> None:
        with self._lock, self.connection:
            self.connection.execute(
                """UPDATE rpc_requests
                SET completed_at = ?, outcome = ?, error_code = ?, response_json = ?
                WHERE run_id = ? AND client_request_id = ?""",
                (
                    _now(),
                    outcome,
                    error_code,
                    canonical_json(dict(response)) if response is not None else None,
                    run_id,
                    client_request_id,
                ),
            )

    def apply_normalized_event(self, event: NormalizedEvent) -> int:
        if event.event_kind in {"BLOCKED", "FAILED", "SUCCESS", "RETIRED", "PAUSED", "PARKED", "RELEASED"}:
            raise ValueError(f"forbidden normalized event kind: {event.event_kind}")
        with self._lock, self.connection:
            cursor = self.connection.execute(
                """INSERT INTO normalized_events (
                    run_id, raw_message_seq, event_kind, thread_id, turn_id, item_id,
                    mechanical_status, payload_json, observed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    event.run_id,
                    event.raw_message_seq,
                    event.event_kind,
                    event.thread_id,
                    event.turn_id,
                    event.item_id,
                    event.mechanical_status,
                    canonical_json(event.payload),
                    event.observed_at,
                ),
            )
            seq = int(cursor.lastrowid)
            self._apply_snapshots(event, seq)
            return seq

    def _apply_snapshots(self, event: NormalizedEvent, event_seq: int) -> None:
        now = event.observed_at
        if event.thread_id:
            existing = self.connection.execute(
                "SELECT first_observed_at FROM thread_snapshots WHERE thread_id = ?",
                (event.thread_id,),
            ).fetchone()
            first = existing[0] if existing else now
            self.connection.execute(
                """INSERT INTO thread_snapshots (
                    thread_id, status_type, preview, ephemeral, path, last_event_seq,
                    first_observed_at, updated_at, preview_present, preview_byte_length
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(thread_id) DO UPDATE SET
                    status_type=excluded.status_type,
                    preview=NULL,
                    ephemeral=COALESCE(excluded.ephemeral, thread_snapshots.ephemeral),
                    path=COALESCE(excluded.path, thread_snapshots.path),
                    last_event_seq=excluded.last_event_seq,
                    updated_at=excluded.updated_at,
                    preview_present=COALESCE(excluded.preview_present, thread_snapshots.preview_present),
                    preview_byte_length=COALESCE(excluded.preview_byte_length, thread_snapshots.preview_byte_length)""",
                (
                    event.thread_id,
                    event.payload.get("status_type") or event.payload.get("status"),
                    None,
                    event.payload.get("ephemeral"),
                    event.payload.get("path"),
                    event_seq,
                    first,
                    now,
                    event.payload.get("preview_present"),
                    event.payload.get("preview_byte_length"),
                ),
            )
        if event.turn_id:
            started = now if event.event_kind == "TURN_STARTED_OBSERVED" else None
            completed = now if event.event_kind == "TURN_COMPLETED_OBSERVED" else None
            self.connection.execute(
                """INSERT INTO turn_snapshots (
                    turn_id, thread_id, status, error_json, started_at, completed_at,
                    last_event_seq, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(turn_id) DO UPDATE SET
                    thread_id=excluded.thread_id,
                    status=COALESCE(excluded.status, turn_snapshots.status),
                    error_json=COALESCE(excluded.error_json, turn_snapshots.error_json),
                    started_at=COALESCE(turn_snapshots.started_at, excluded.started_at),
                    completed_at=COALESCE(excluded.completed_at, turn_snapshots.completed_at),
                    last_event_seq=excluded.last_event_seq,
                    updated_at=excluded.updated_at""",
                (
                    event.turn_id,
                    event.thread_id or "",
                    event.mechanical_status,
                    json.dumps(event.payload.get("error")) if event.payload.get("error") else None,
                    started,
                    completed,
                    event_seq,
                    now,
                ),
            )
        if event.item_id:
            lifecycle = "COMPLETED" if event.event_kind == "ITEM_COMPLETED_OBSERVED" else "STARTED"
            self.connection.execute(
                """INSERT INTO item_snapshots (
                    item_id, thread_id, turn_id, item_type, lifecycle,
                    safe_metadata_json, last_event_seq, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET
                    thread_id=COALESCE(excluded.thread_id, item_snapshots.thread_id),
                    turn_id=COALESCE(excluded.turn_id, item_snapshots.turn_id),
                    item_type=COALESCE(excluded.item_type, item_snapshots.item_type),
                    lifecycle=excluded.lifecycle,
                    safe_metadata_json=excluded.safe_metadata_json,
                    last_event_seq=excluded.last_event_seq,
                    updated_at=excluded.updated_at""",
                (
                    event.item_id,
                    event.thread_id,
                    event.turn_id,
                    event.payload.get("item_type"),
                    lifecycle,
                    canonical_json({k: v for k, v in event.payload.items() if k != "text"}),
                    event_seq,
                    now,
                ),
            )

    def record_server_request(
        self,
        *,
        run_id: str,
        server_request_id: str,
        method: str,
        payload: Mapping[str, Any],
        thread_id: str | None,
        turn_id: str | None,
    ) -> str:
        row_id = _new_id("sreq")
        now = _now()
        with self._lock, self.connection:
            self.connection.execute(
                """INSERT INTO server_requests (
                    server_request_row_id, run_id, server_request_id, method, thread_id,
                    turn_id, request_json, handling, observed_at, process_terminated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'TERMINATE', ?, ?)""",
                (
                    row_id,
                    run_id,
                    server_request_id,
                    method,
                    thread_id,
                    turn_id,
                    canonical_json(dict(payload)),
                    now,
                    now,
                ),
            )
        return row_id

    def start_reconciliation(self, run_id: str) -> str:
        rec_id = _new_id("recon")
        with self._lock, self.connection:
            self.connection.execute(
                """INSERT INTO reconciliation_runs (
                    reconciliation_id, run_id, started_at, completed_at, thread_count,
                    outcome, error_json
                ) VALUES (?, ?, ?, NULL, NULL, NULL, NULL)""",
                (rec_id, run_id, _now()),
            )
        return rec_id

    def complete_reconciliation(
        self,
        reconciliation_id: str,
        *,
        thread_count: int,
        outcome: str,
        error: Mapping[str, Any] | None = None,
    ) -> None:
        with self._lock, self.connection:
            self.connection.execute(
                """UPDATE reconciliation_runs
                SET completed_at = ?, thread_count = ?, outcome = ?, error_json = ?
                WHERE reconciliation_id = ?""",
                (
                    _now(),
                    thread_count,
                    outcome,
                    canonical_json(dict(error)) if error else None,
                    reconciliation_id,
                ),
            )

    def upsert_thread_snapshot(
        self,
        *,
        thread_id: str,
        status_type: object = None,
        preview: object = None,
        ephemeral: object = None,
        path: object = None,
        last_event_seq: int | None = None,
        observed_at: str | None = None,
        preview_present: object = None,
        preview_byte_length: object = None,
    ) -> None:
        now = observed_at or _now()
        present = preview_present
        length = preview_byte_length
        if present is None and preview is not None:
            present = True
            length = len(str(preview).encode("utf-8"))
        with self._lock, self.connection:
            existing = self.connection.execute(
                "SELECT first_observed_at FROM thread_snapshots WHERE thread_id = ?",
                (thread_id,),
            ).fetchone()
            first = existing[0] if existing else now
            self.connection.execute(
                """INSERT INTO thread_snapshots (
                    thread_id, status_type, preview, ephemeral, path, last_event_seq,
                    first_observed_at, updated_at, preview_present, preview_byte_length
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(thread_id) DO UPDATE SET
                    status_type=COALESCE(excluded.status_type, thread_snapshots.status_type),
                    preview=NULL,
                    ephemeral=COALESCE(excluded.ephemeral, thread_snapshots.ephemeral),
                    path=COALESCE(excluded.path, thread_snapshots.path),
                    last_event_seq=COALESCE(excluded.last_event_seq, thread_snapshots.last_event_seq),
                    updated_at=excluded.updated_at,
                    preview_present=COALESCE(excluded.preview_present, thread_snapshots.preview_present),
                    preview_byte_length=COALESCE(excluded.preview_byte_length, thread_snapshots.preview_byte_length)""",
                (
                    thread_id,
                    None if status_type is None else str(status_type),
                    None,
                    ephemeral,
                    None if path is None else str(path),
                    last_event_seq,
                    first,
                    now,
                    present,
                    length,
                ),
            )

    def latest_thread_snapshot(self, thread_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self.connection.execute(
                "SELECT * FROM thread_snapshots WHERE thread_id = ?",
                (thread_id,),
            ).fetchone()
            return dict(row) if row is not None else None

    def get_command_receipt(self, command_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self.connection.execute(
                "SELECT * FROM managed_command_receipts WHERE command_id = ?",
                (command_id,),
            ).fetchone()
            return dict(row) if row is not None else None

    def record_command_receipt(
        self,
        *,
        command_id: str,
        effect_kind: str,
        result: Mapping[str, Any],
        semantic_ref: str | None = None,
    ) -> str:
        existing = self.get_command_receipt(command_id)
        if existing is not None:
            return str(existing["receipt_id"])
        receipt_id = _new_id("rcpt")
        with self._lock, self.connection:
            self.connection.execute(
                """INSERT INTO managed_command_receipts (
                    receipt_id, command_id, effect_kind, semantic_ref, result_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    receipt_id,
                    command_id,
                    effect_kind,
                    semantic_ref,
                    canonical_json(dict(result)),
                    _now(),
                ),
            )
        return receipt_id

    def events_for_thread(self, thread_id: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.connection.execute(
                """SELECT * FROM normalized_events
                WHERE thread_id = ?
                ORDER BY event_seq""",
                (thread_id,),
            ).fetchall()
            return [dict(row) for row in rows]
