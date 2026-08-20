from __future__ import annotations

import sys
from pathlib import Path

from tests.codex_supervisor import fake_app_server
from tools.codex_supervisor.models import ObserverConfig, RpcShape
from tools.codex_supervisor.normalizer import apply_normalized_event, normalize_message
from tools.codex_supervisor.protocol import extract_protocol_ids
from tools.codex_supervisor.store import ObserverStore


def insert_submittable_owner_for_effect(connection, effect) -> None:
    """Test helper: give a prepared effect a matching owner aggregate row."""
    if effect.owner_kind == "MANAGED_TURN":
        connection.execute(
            """INSERT INTO managed_turn_intents (
                turn_intent_id, binding_id, intent_kind, client_user_message_id,
                input_ref, submission_state, app_server_thread_id, prepared_at, version, effect_id
            ) VALUES (?, ?, 'MANUAL_OPERATOR', ?, 'ref', 'PREPARED', 'thr1', 't', 0, ?)""",
            (effect.owner_id, effect.binding_id or "bind1", effect.client_key, effect.effect_id),
        )
    elif effect.owner_kind == "WAKE_BATCH":
        connection.execute(
            """INSERT INTO wake_batches (
                wake_batch_id, binding_id, thread_id, state, client_user_message_id,
                prepared_at, version, effect_id
            ) VALUES (?, ?, 'thr1', 'PREPARED', ?, 't', 0, ?)""",
            (effect.owner_id, effect.binding_id or "bind1", effect.client_key, effect.effect_id),
        )
    elif effect.owner_kind in {"THREAD_PROVISION", "THREAD_RESUME", "THREAD_MEMORY"}:
        binding_id = effect.binding_id or effect.owner_id
        existing = connection.execute(
            "SELECT 1 FROM managed_actor_bindings WHERE binding_id = ?",
            (binding_id,),
        ).fetchone()
        if existing is None:
            state = "PREPARED" if effect.owner_kind == "THREAD_PROVISION" else "ACTIVE"
            connection.execute(
                """INSERT INTO managed_actor_bindings (
                    binding_id, actor_context_id, actor_kind, semantic_scope_key,
                    thread_origin, history_trust, binding_state, memory_policy_state,
                    repo_root, thread_cwd, created_by_operator, created_at
                ) VALUES (?, ?, 'OPERATIONAL_ROOT', 'scope', 'NEW', 'FRESH', ?, 'UNVERIFIED', '.', '.', 'op', 't')""",
                (binding_id, f"act-{binding_id}", state),
            )
    connection.commit()


def claim_wake_write_start_for_tests(
    batches,
    wake_batch_id: str,
    *,
    lease_holder: object = None,
    lease_generation: object = None,
) -> dict[str, object]:
    """Fixture-only mid-flight wake. Production code must use submit_effect."""
    import uuid
    from datetime import datetime, timezone

    from tools.codex_supervisor.durability.effects import EffectJournal
    from tools.codex_supervisor.durability.models import AggregateKind, TransitionCause, TransitionRequest
    from tools.codex_supervisor.durability.transaction import DurabilityTransaction
    from tools.codex_supervisor.durability.transitions import TransitionError, TransitionKernel
    from tools.codex_supervisor.mailbox_models import WakeAttemptOutcome, WakeBatchState
    from tools.codex_supervisor.wake_batches import WakeBatchError

    now = datetime.now(timezone.utc).isoformat()
    with batches.store._lock:
        with DurabilityTransaction(batches.store.connection):
            current = batches.store.connection.execute(
                """SELECT state, version, lease_holder, lease_generation, effect_id
                FROM wake_batches WHERE wake_batch_id = ?""",
                (wake_batch_id,),
            ).fetchone()
            if (
                current is None
                or str(current["state"]) != WakeBatchState.PREPARED.value
                or current["lease_holder"] != lease_holder
                or current["lease_generation"] != lease_generation
            ):
                raise WakeBatchError("wake batch is not PREPARED for this lease")
            try:
                TransitionKernel(batches.store.connection).apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.WAKE_BATCH,
                        aggregate_id=wake_batch_id,
                        expected_state=WakeBatchState.PREPARED.value,
                        expected_version=int(current["version"] or 0),
                        target_state=WakeBatchState.SUBMITTING.value,
                        cause_kind=TransitionCause.APP_SERVER_EFFECT,
                        cause_ref="test-wake-claim",
                    )
                )
            except TransitionError as exc:
                raise WakeBatchError("wake batch is not PREPARED for this lease") from exc
            effect_id = None if current["effect_id"] is None else str(current["effect_id"])
            if effect_id:
                EffectJournal(batches.store.connection).claim_write(
                    effect_id,
                    run_id="fixture",
                    client_request_id="fixture",
                    request_row_id="fixture",
                    raw_request_seq=1,
                )
            batches.store.connection.execute(
                """INSERT INTO wake_attempts (
                    wake_attempt_id, wake_batch_id, attempt_number, request_id,
                    outcome, error_json, created_at
                ) VALUES (?, ?, 1, NULL, ?, NULL, ?)""",
                (
                    f"watt_{uuid.uuid4().hex}",
                    wake_batch_id,
                    WakeAttemptOutcome.SUBMITTING.value,
                    now,
                ),
            )
    row = batches.get(wake_batch_id)
    assert row is not None
    return row


def rewind_command_validation(connection, command_id: str, state: str) -> None:
    """Test-only crash reconstruction. Production code cannot rewind APPLIED."""
    from tools.codex_supervisor.db import _install_transition_guards

    connection.execute("DROP TRIGGER IF EXISTS durability_managed_actor_commands_validation_state_guard")
    connection.execute(
        """UPDATE managed_actor_commands
        SET validation_state = ?, applied_at = NULL, version = version + 1
        WHERE command_id = ?""",
        (state, command_id),
    )
    _install_transition_guards(connection)
    connection.commit()


def insert_legacy_mutation_intent(
    connection,
    *,
    method: str,
    client_key: str,
    state: str = "SUBMITTING",
    binding_id: str | None = None,
    intent_id: str | None = None,
) -> str:
    import uuid
    from datetime import datetime, timezone

    intent_id = intent_id or f"mut_{uuid.uuid4().hex}"
    now = datetime.now(timezone.utc).isoformat()
    connection.execute(
        """INSERT INTO mutation_intents (
            intent_id, method, binding_id, client_key, state, request_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, '{}', ?, ?)""",
        (intent_id, method, binding_id, client_key, state, now, now),
    )
    connection.commit()
    return intent_id


def make_observer_config(tmp_path: Path, **overrides: object) -> ObserverConfig:
    values: dict[str, object] = {
        "schema_version": 1,
        "client_name": "hmasd-codex-app-server-observer",
        "client_title": "HMASD Codex App Server Observer",
        "client_version": "0.1.0",
        "experimental_api": False,
        "initialize_timeout_seconds": 15.0,
        "request_timeout_seconds": 30.0,
        "reconcile_interval_seconds": 60.0,
        "max_jsonl_line_bytes": 1_048_576,
        "read_retry_attempts": 5,
        "read_retry_base_seconds": 0.25,
        "unexpected_server_request_policy": "terminate",
        "runtime_home": tmp_path / "runtime",
    }
    values.update(overrides)
    return ObserverConfig(**values)  # type: ignore[arg-type]


def write_fake_codex(tmp_path: Path) -> Path:
    script = Path(fake_app_server.__file__).resolve()
    if sys.platform == "win32":
        binary = tmp_path / "codex.cmd"
        binary.write_text(
            f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n',
            encoding="utf-8",
        )
    else:
        binary = tmp_path / "codex"
        binary.write_text(
            f"#!/usr/bin/env bash\nexec '{sys.executable}' '{script}' \"$@\"\n",
            encoding="utf-8",
        )
        binary.chmod(0o755)
    return binary


def drive_turn_intent(connection, turn_intent_id: str, target: str, **fields: object) -> None:
    """Walk legal managed-turn edges so tests do not jump the kernel graph."""
    paths = {
        "SUBMITTING": ("SUBMITTING",),
        "SUBMITTED": ("SUBMITTING", "SUBMITTED"),
        "SUBMISSION_UNCERTAIN": ("SUBMITTING", "SUBMISSION_UNCERTAIN"),
        "OBSERVED": ("SUBMITTING", "SUBMITTED", "OBSERVED"),
        "COMPLETED": ("SUBMITTING", "SUBMITTED", "OBSERVED", "COMPLETED"),
        "INCIDENT": ("INCIDENT",),
        "CANCELLED": ("CANCELLED",),
    }
    current = str(
        connection.execute(
            "SELECT submission_state FROM managed_turn_intents WHERE turn_intent_id = ?",
            (turn_intent_id,),
        ).fetchone()[0]
    )
    assignments = ", ".join(f"{key} = ?" for key in fields)
    for state in paths[target]:
        if current == target:
            return
        extra_sql = f", {assignments}" if assignments and state == target else ""
        values: list[object] = [state]
        if extra_sql:
            values.extend(fields.values())
        values.append(turn_intent_id)
        connection.execute(
            f"""UPDATE managed_turn_intents
            SET submission_state = ?, version = version + 1{extra_sql}
            WHERE turn_intent_id = ?""",
            values,
        )
        current = state
    connection.commit()


def drive_wake_batch(batches, wake_id: str, target: str, **fields: object) -> None:
    """Walk legal wake-batch edges so tests do not jump the kernel graph."""
    paths = {
        "SUBMITTING": ("SUBMITTING",),
        "SUBMITTED": ("SUBMITTING", "SUBMITTED"),
        "ACTIVE": ("SUBMITTING", "SUBMITTED", "ACTIVE"),
        "COMPLETED": ("SUBMITTING", "SUBMITTED", "ACTIVE", "COMPLETED"),
        "INCIDENT": ("INCIDENT",),
        "CANCELLED": ("CANCELLED",),
    }
    current = str(batches.get(wake_id)["state"])
    for state in paths[target]:
        if current == target:
            return
        extra = fields if state == target else {}
        batches.set_state(wake_id, state=state, expected_state=current, **extra)
        current = state


def _ensure_run(store: ObserverStore) -> str:
    row = store.connection.execute("SELECT run_id FROM observer_runs ORDER BY started_at DESC LIMIT 1").fetchone()
    if row is not None:
        return str(row[0])
    return store.start_run(codex_binary="c", codex_version="v", client_name="n", process_id=1)


def record_completed_agent_item(
    store: ObserverStore,
    *,
    thread_id: str,
    turn_id: str,
    text: str,
    item_id: str = "itm_final",
    item_type: str = "agentMessage",
) -> int:
    run_id = _ensure_run(store)
    next_seq = int(
        store.connection.execute(
            "SELECT COALESCE(MAX(transport_seq), 0) + 1 FROM raw_messages WHERE run_id = ?",
            (run_id,),
        ).fetchone()[0]
    )
    item_payload = {
        "method": "item/completed",
        "params": {
            "threadId": thread_id,
            "turnId": turn_id,
            "item": {"id": item_id, "type": item_type, "text": text},
        },
    }
    raw_seq = store.record_raw_message(
        run_id=run_id,
        direction="stdout",
        transport_seq=next_seq,
        rpc_shape=RpcShape.NOTIFICATION,
        ids=extract_protocol_ids(item_payload),
        payload=item_payload,
    )
    event = normalize_message(item_payload, raw_seq, run_id, "t-item")
    assert event is not None
    apply_normalized_event(store, event)
    turn_payload = {
        "method": "turn/completed",
        "params": {"threadId": thread_id, "turn": {"id": turn_id, "status": "completed"}},
    }
    turn_raw = store.record_raw_message(
        run_id=run_id,
        direction="stdout",
        transport_seq=next_seq + 1,
        rpc_shape=RpcShape.NOTIFICATION,
        ids=extract_protocol_ids(turn_payload),
        payload=turn_payload,
    )
    turn_event = normalize_message(turn_payload, turn_raw, run_id, "t-turn")
    assert turn_event is not None
    apply_normalized_event(store, turn_event)
    return raw_seq


def ingest_recorded_command(gateway, store: ObserverStore, *, thread_id: str, turn_id: str, text: str, item_id: str | None = None) -> dict:
    seq = record_completed_agent_item(
        store,
        thread_id=thread_id,
        turn_id=turn_id,
        text=text,
        item_id=item_id or f"itm_{turn_id}",
    )
    return gateway.ingest_final_item(raw_message_seq=seq)
