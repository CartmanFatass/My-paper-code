"""App Server effect journal. WRITE_STARTED means possible submission."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from ..canary_contract import (
    canonical_canary_thread_start_request,
    canonical_canary_turn_start_request,
    is_exact_canary_request,
    is_exact_json_value,
    require_canonical_canary_id,
)
from .models import AggregateKind, EffectOwnerKind, EffectState, TransitionCause, TransitionRequest
from .transaction import DurabilityTransaction
from .transitions import TransitionError, TransitionKernel


class EffectError(RuntimeError):
    """Raised when an App Server effect cannot be prepared or advanced."""


@dataclass(frozen=True)
class EffectRecord:
    effect_id: str
    owner_kind: str
    owner_id: str
    binding_id: str | None
    predecessor_effect_id: str | None
    method: str
    client_key: str
    request: Mapping[str, object]
    state: str
    version: int
    run_id: str | None = None
    client_request_id: str | None = None
    request_row_id: str | None = None
    raw_request_seq: int | None = None
    thread_id: str | None = None
    turn_id: str | None = None
    response_json: str | None = None
    incident_json: str | None = None
    prepared_at: str = ""
    write_started_at: str | None = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return f"eff_{uuid.uuid4().hex}"


def _canonical_request(request: Mapping[str, object]) -> str:
    if not is_exact_json_value(request, request):
        raise EffectError("effect request contains a non-JSON or non-finite value")
    return json.dumps(dict(request), sort_keys=True, separators=(",", ":"))


def _record(row: Mapping[str, Any] | sqlite3.Row) -> EffectRecord:
    data = dict(row)
    raw_seq = data.get("raw_request_seq")
    payload = data.get("request_json") or "{}"
    parsed = json.loads(str(payload))
    return EffectRecord(
        effect_id=str(data["effect_id"]),
        owner_kind=str(data["owner_kind"]),
        owner_id=str(data["owner_id"]),
        binding_id=None if data["binding_id"] is None else str(data["binding_id"]),
        predecessor_effect_id=(
            None
            if data.get("predecessor_effect_id") is None
            else str(data["predecessor_effect_id"])
        ),
        method=str(data["method"]),
        client_key=str(data["client_key"]),
        request=dict(parsed) if isinstance(parsed, Mapping) else {},
        state=str(data["state"]),
        version=int(data["version"] or 0),
        run_id=None if data["run_id"] is None else str(data["run_id"]),
        client_request_id=None if data["client_request_id"] is None else str(data["client_request_id"]),
        request_row_id=None if data["request_row_id"] is None else str(data["request_row_id"]),
        raw_request_seq=None if raw_seq is None else int(raw_seq),
        thread_id=None if data["thread_id"] is None else str(data["thread_id"]),
        turn_id=None if data["turn_id"] is None else str(data["turn_id"]),
        response_json=None if data["response_json"] is None else str(data["response_json"]),
        incident_json=None if data["incident_json"] is None else str(data["incident_json"]),
        prepared_at=str(data["prepared_at"] or ""),
        write_started_at=None if data["write_started_at"] is None else str(data["write_started_at"]),
    )


class EffectJournal:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.kernel = TransitionKernel(connection)

    def _tx(self):
        if self.connection.in_transaction:
            return nullcontext()
        return DurabilityTransaction(self.connection)

    def get(self, effect_id: str) -> EffectRecord:
        row = self.connection.execute(
            "SELECT * FROM app_server_effects WHERE effect_id = ?",
            (effect_id,),
        ).fetchone()
        if row is None:
            raise EffectError(f"unknown effect: {effect_id}")
        return _record(row)

    def get_by_key(self, method: str, client_key: str) -> EffectRecord | None:
        row = self.connection.execute(
            "SELECT * FROM app_server_effects WHERE method = ? AND client_key = ?",
            (method, client_key),
        ).fetchone()
        return None if row is None else _record(row)

    def prepare_effect(
        self,
        *,
        owner_kind: str,
        owner_id: str,
        binding_id: str | None,
        method: str,
        client_key: str,
        request: Mapping[str, object],
        predecessor_effect_id: str | None = None,
    ) -> EffectRecord:
        EffectOwnerKind(owner_kind)
        request_json = _canonical_request(request)
        existing = self.get_by_key(method, client_key)
        if existing is not None:
            same = (
                existing.owner_kind == owner_kind
                and existing.owner_id == owner_id
                and existing.binding_id == binding_id
                and existing.predecessor_effect_id == predecessor_effect_id
                and existing.method == method
                and existing.client_key == client_key
                and _canonical_request(existing.request) == request_json
            )
            if not same:
                raise EffectError(f"effect key conflict for {method} {client_key}")
            if existing.state != EffectState.PREPARED.value:
                raise EffectError(
                    f"{method} {client_key} already {existing.state}; cannot prepare again"
                )
            return existing
        effect_id = _new_id()
        now = _now()
        with self._tx():
            self.connection.execute(
                """INSERT INTO app_server_effects(
                    effect_id, owner_kind, owner_id, binding_id, predecessor_effect_id,
                    method, client_key,
                    request_json, state, version, prepared_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)""",
                (
                    effect_id,
                    owner_kind,
                    owner_id,
                    binding_id,
                    predecessor_effect_id,
                    method,
                    client_key,
                    request_json,
                    EffectState.PREPARED.value,
                    now,
                ),
            )
        return self.get(effect_id)

    def claim_write(
        self,
        effect_id: str,
        *,
        run_id: str,
        client_request_id: str,
        request_row_id: str,
        raw_request_seq: int,
        transport_seq: int | None = None,
    ) -> EffectRecord:
        current = self.get(effect_id)
        if current.state != EffectState.PREPARED.value:
            raise EffectError(f"only PREPARED can claim write; {effect_id} is {current.state}")
        fields: dict[str, object] = {
            "run_id": run_id,
            "client_request_id": client_request_id,
            "request_row_id": request_row_id,
            "raw_request_seq": raw_request_seq,
            "write_started_at": _now(),
        }
        if transport_seq is not None:
            fields["transport_seq"] = transport_seq
        with self._tx():
            try:
                self.kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.APP_SERVER_EFFECT,
                        aggregate_id=effect_id,
                        expected_state=EffectState.PREPARED.value,
                        expected_version=current.version,
                        target_state=EffectState.WRITE_STARTED.value,
                        cause_kind=TransitionCause.APP_SERVER_EFFECT,
                        cause_ref=client_request_id,
                        evidence_ref=request_row_id,
                        field_updates=fields,
                    )
                )
            except TransitionError as exc:
                raise EffectError(str(exc)) from exc
        return self.get(effect_id)

    def observe_response(
        self,
        effect_id: str,
        *,
        response: Mapping[str, object],
        thread_id: str | None = None,
        turn_id: str | None = None,
    ) -> EffectRecord:
        current = self.get(effect_id)
        with self._tx():
            try:
                self.kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.APP_SERVER_EFFECT,
                        aggregate_id=effect_id,
                        expected_state=current.state,
                        expected_version=current.version,
                        target_state=EffectState.RESPONSE_OBSERVED.value,
                        cause_kind=TransitionCause.APP_SERVER_RESPONSE,
                        cause_ref=current.client_request_id or effect_id,
                        field_updates={
                            "response_json": json.dumps(dict(response), sort_keys=True),
                            "response_observed_at": _now(),
                            "thread_id": thread_id,
                            "turn_id": turn_id,
                        },
                    )
                )
            except TransitionError as exc:
                raise EffectError(str(exc)) from exc
        return self.get(effect_id)

    def mark_uncertain(self, effect_id: str, *, reason: str) -> EffectRecord:
        current = self.get(effect_id)
        with self._tx():
            try:
                self.kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.APP_SERVER_EFFECT,
                        aggregate_id=effect_id,
                        expected_state=current.state,
                        expected_version=current.version,
                        target_state=EffectState.SUBMISSION_UNCERTAIN.value,
                        cause_kind=TransitionCause.RECONCILIATION,
                        cause_ref=reason,
                        field_updates={"incident_json": json.dumps({"reason": reason})},
                    )
                )
            except TransitionError as exc:
                raise EffectError(str(exc)) from exc
        return self.get(effect_id)

    def confirm_effect(self, effect_id: str, *, evidence_ref: str) -> EffectRecord:
        if not evidence_ref:
            raise EffectError("confirmation requires evidence_ref")
        current = self.get(effect_id)
        if current.state == EffectState.EFFECT_CONFIRMED.value:
            return current
        with self._tx():
            try:
                if current.state == EffectState.WRITE_STARTED.value:
                    self.kernel.apply(
                        TransitionRequest(
                            aggregate_kind=AggregateKind.APP_SERVER_EFFECT,
                            aggregate_id=effect_id,
                            expected_state=EffectState.WRITE_STARTED.value,
                            expected_version=current.version,
                            target_state=EffectState.SUBMISSION_UNCERTAIN.value,
                            cause_kind=TransitionCause.RECONCILIATION,
                            cause_ref=evidence_ref,
                            evidence_ref=evidence_ref,
                        )
                    )
                    current = self.get(effect_id)
                self.kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.APP_SERVER_EFFECT,
                        aggregate_id=effect_id,
                        expected_state=current.state,
                        expected_version=current.version,
                        target_state=EffectState.EFFECT_CONFIRMED.value,
                        cause_kind=TransitionCause.RECONCILIATION,
                        cause_ref=evidence_ref,
                        evidence_ref=evidence_ref,
                        field_updates={"confirmed_at": _now(), "reconciled_at": _now()},
                    )
                )
            except TransitionError as exc:
                raise EffectError(str(exc)) from exc
        return self.get(effect_id)

    def mark_incident(
        self,
        effect_id: str,
        *,
        evidence_ref: str,
        incident: Mapping[str, object],
    ) -> EffectRecord:
        current = self.get(effect_id)
        with self._tx():
            try:
                self.kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.APP_SERVER_EFFECT,
                        aggregate_id=effect_id,
                        expected_state=current.state,
                        expected_version=current.version,
                        target_state=EffectState.INCIDENT.value,
                        cause_kind=TransitionCause.SERVER_REQUEST_INCIDENT,
                        cause_ref=evidence_ref,
                        evidence_ref=evidence_ref,
                        field_updates={
                            "incident_json": json.dumps(dict(incident), sort_keys=True),
                        },
                    )
                )
            except TransitionError as exc:
                raise EffectError(str(exc)) from exc
        return self.get(effect_id)

    def cancel_before_write(self, effect_id: str, *, cause_ref: str) -> EffectRecord:
        current = self.get(effect_id)
        with self._tx():
            try:
                self.kernel.apply(
                    TransitionRequest(
                        aggregate_kind=AggregateKind.APP_SERVER_EFFECT,
                        aggregate_id=effect_id,
                        expected_state=current.state,
                        expected_version=current.version,
                        target_state=EffectState.CANCELLED_BEFORE_WRITE.value,
                        cause_kind=TransitionCause.PRE_WRITE_CANCEL,
                        cause_ref=cause_ref,
                    )
                )
            except TransitionError as exc:
                raise EffectError(str(exc)) from exc
        return self.get(effect_id)

    def cancel_prepared_if_present(self, effect_id: str | None, *, cause_ref: str) -> None:
        if not effect_id:
            return
        try:
            current = self.get(effect_id)
        except EffectError:
            return
        if current.state != EffectState.PREPARED.value:
            return
        self.cancel_before_write(effect_id, cause_ref=cause_ref)

    def has_possible_submission(self, effect_id: str) -> bool:
        current = self.get(effect_id)
        return current.state != EffectState.PREPARED.value or current.raw_request_seq is not None


def cancel_prepared_wake(
    connection: sqlite3.Connection,
    wake_batch_id: str,
    *,
    cause_ref: str,
    message_target: str = "ELIGIBLE",
    message_targets: Mapping[str, str] | None = None,
    message_field_updates: Mapping[str, Mapping[str, object]] | None = None,
    batch_cause_kind: TransitionCause = TransitionCause.PRE_WRITE_CANCEL,
    message_cause_kind: TransitionCause = TransitionCause.PRE_WRITE_CANCEL,
) -> dict[str, object]:
    """Cancel one exactly-owned PREPARED wake atomically.

    The base operation is intentionally strict because restart and source
    reconciliation both reach it.  The complete batch/effect/message ownership
    graph is proved before the first transition.  Missing, crossed, duplicate,
    foreign-binding, or multiply-owned rows therefore leave every aggregate
    unchanged.
    """
    from .models import AggregateKind, TransitionCause, TransitionRequest
    from .transaction import DurabilityTransaction
    from .transitions import TransitionError, TransitionKernel

    journal = EffectJournal(connection)
    kernel = TransitionKernel(connection)
    owns = not connection.in_transaction
    if owns:
        connection.execute("BEGIN IMMEDIATE")
    try:
        ownership = require_exact_prepared_wake_ownership(connection, wake_batch_id)
        batch = connection.execute(
            "SELECT * FROM wake_batches WHERE wake_batch_id = ?",
            (wake_batch_id,),
        ).fetchone()
        assert batch is not None
        rows = connection.execute(
            """SELECT m.message_id, m.delivery_state, m.delivery_version, b.ordinal
            FROM mailbox_messages m
            JOIN wake_batch_messages b ON b.message_id = m.message_id
            WHERE b.wake_batch_id = ?
            ORDER BY b.ordinal, m.message_id""",
            (wake_batch_id,),
        ).fetchall()
        message_ids = [str(row["message_id"]) for row in rows]
        if (
            not rows
            or [int(row["ordinal"]) for row in rows] != list(range(len(rows)))
            or any(str(row["delivery_state"]) != "BATCHED" for row in rows)
        ):
            raise EffectError("prepared wake message ownership is not exact")
        for message_id in message_ids:
            owners = connection.execute(
                """SELECT b.wake_batch_id
                FROM wake_batch_messages m
                JOIN wake_batches b ON b.wake_batch_id = m.wake_batch_id
                WHERE m.message_id = ?
                  AND b.state IN ('PREPARED','SUBMITTING','SUBMITTED',
                                  'SUBMISSION_UNCERTAIN','ACTIVE')""",
                (message_id,),
            ).fetchall()
            if len(owners) != 1 or str(owners[0][0]) != wake_batch_id:
                raise EffectError("prepared wake message has ambiguous open ownership")
        if message_targets is not None and set(message_targets) != set(message_ids):
            raise EffectError("prepared wake message target map is not exact")
        if message_field_updates is not None and not set(message_field_updates).issubset(
            message_ids
        ):
            raise EffectError("prepared wake message update map is not exact")

        kernel.apply(
            TransitionRequest(
                aggregate_kind=AggregateKind.WAKE_BATCH,
                aggregate_id=wake_batch_id,
                expected_state="PREPARED",
                expected_version=int(batch["version"] or 0),
                target_state="CANCELLED",
                cause_kind=batch_cause_kind,
                cause_ref=cause_ref,
            )
        )
        for row in rows:
            message_id = str(row["message_id"])
            target = (
                str(message_targets[message_id])
                if message_targets is not None
                else message_target
            )
            kernel.apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.MAILBOX_DELIVERY,
                    aggregate_id=message_id,
                    expected_state="BATCHED",
                    expected_version=int(row["delivery_version"] or 0),
                    target_state=target,
                    cause_kind=message_cause_kind,
                    cause_ref=cause_ref,
                    field_updates=dict((message_field_updates or {}).get(message_id, {})),
                )
            )
        journal.cancel_before_write(str(ownership["effect_id"]), cause_ref=cause_ref)
        if owns:
            connection.commit()
    except Exception:
        if owns:
            connection.rollback()
        raise
    row = connection.execute(
        "SELECT * FROM wake_batches WHERE wake_batch_id = ?",
        (wake_batch_id,),
    ).fetchone()
    return dict(row)


_OPEN_EFFECT_STATES = (
    "PREPARED",
    "WRITE_STARTED",
    "RESPONSE_OBSERVED",
    "SUBMISSION_UNCERTAIN",
    "INCIDENT",
)

_BINDING_EFFECT_OWNER_KINDS = (
    "THREAD_PROVISION",
    "THREAD_RESUME",
    "THREAD_MEMORY",
)


def require_exact_binding_containment_ownership(
    connection: sqlite3.Connection,
    *,
    binding_id: str,
    effect_id: str | None = None,
    owner_kind: str | None = None,
    owner_id: str | None = None,
    expected_states: tuple[str, ...] = (EffectState.PREPARED.value,),
) -> dict[str, object] | None:
    """Prove the complete open-effect set affected by binding containment.

    With no expected effect, containment is legitimate only when the binding
    has no open effect.  With an expected effect, that effect must be the sole
    open relation touching the binding, and its owner tuple is enumerated
    globally so a same-owner foreign-binding row cannot be hidden by a binding
    filter.
    """

    if not connection.in_transaction:
        raise EffectError("binding containment proof requires an ambient transaction")
    expected = None
    if effect_id is not None:
        expected = connection.execute(
            "SELECT * FROM app_server_effects WHERE effect_id = ?",
            (effect_id,),
        ).fetchone()
        if expected is None:
            raise EffectError("binding containment effect is missing")
        resolved_owner_kind = str(expected["owner_kind"])
        resolved_owner_id = str(expected["owner_id"])
        if owner_kind is not None and resolved_owner_kind != owner_kind:
            raise EffectError("binding containment owner kind changed")
        if owner_id is not None and resolved_owner_id != owner_id:
            raise EffectError("binding containment owner id changed")
        owner_kind = resolved_owner_kind
        owner_id = resolved_owner_id

    open_placeholders = ",".join("?" for _ in _OPEN_EFFECT_STATES)
    binding_kind_placeholders = ",".join("?" for _ in _BINDING_EFFECT_OWNER_KINDS)
    predicates = [
        "binding_id = ?",
        f"(owner_id = ? AND owner_kind IN ({binding_kind_placeholders}))",
    ]
    params: list[object] = [
        *_OPEN_EFFECT_STATES,
        binding_id,
        binding_id,
        *_BINDING_EFFECT_OWNER_KINDS,
    ]
    if owner_kind is not None and owner_id is not None:
        predicates.append("(owner_kind = ? AND owner_id = ?)")
        params.extend((owner_kind, owner_id))
    rows = connection.execute(
        f"""SELECT * FROM app_server_effects
        WHERE state IN ({open_placeholders})
          AND ({' OR '.join(predicates)})
        ORDER BY owner_kind, owner_id, effect_id""",
        params,
    ).fetchall()
    if effect_id is None:
        if rows:
            raise EffectError("binding containment has an unowned open effect")
        return None
    if len(rows) != 1 or str(rows[0]["effect_id"]) != effect_id:
        raise EffectError("binding containment has missing or ambiguous open ownership")
    assert owner_kind is not None and owner_id is not None
    return require_exact_open_effect_ownership(
        connection,
        owner_kind=owner_kind,
        owner_id=owner_id,
        effect_id=effect_id,
        binding_id=binding_id,
        expected_states=expected_states,
    )


def require_exact_open_effect_ownership(
    connection: sqlite3.Connection,
    *,
    owner_kind: str,
    owner_id: str,
    effect_id: str,
    binding_id: str | None,
    expected_states: tuple[str, ...] | None = None,
    enumerated_states: tuple[str, ...] | None = None,
) -> dict[str, object]:
    """Prove one globally unique open effect for an exact owner tuple.

    Open effects are deliberately enumerated by ``(owner_kind, owner_id)``
    before any binding or effect-id relation is inspected.  A foreign-binding
    effect owned by the same aggregate is therefore ambiguity, including when
    it has already crossed WRITE_STARTED, and no caller may submit, cancel, or
    requeue through that ambiguity.
    """

    if not connection.in_transaction:
        raise EffectError("exact effect ownership proof requires an ambient transaction")
    states = _OPEN_EFFECT_STATES if enumerated_states is None else enumerated_states
    if not states:
        raise EffectError("exact effect ownership proof requires enumerated states")
    placeholders = ",".join("?" for _ in states)
    rows = connection.execute(
        f"""SELECT * FROM app_server_effects
        WHERE owner_kind = ? AND owner_id = ?
          AND state IN ({placeholders})
        ORDER BY effect_id""",
        (owner_kind, owner_id, *states),
    ).fetchall()
    if len(rows) != 1:
        raise EffectError("effect owner has missing or ambiguous open ownership")
    row = rows[0]
    actual_binding_id = None if row["binding_id"] is None else str(row["binding_id"])
    if (
        str(row["owner_kind"]) != owner_kind
        or str(row["owner_id"]) != owner_id
        or str(row["effect_id"]) != effect_id
        or actual_binding_id != binding_id
    ):
        raise EffectError("open effect does not match the exact requested ownership tuple")
    if expected_states is not None and str(row["state"]) not in expected_states:
        raise EffectError("open effect is not in the required ownership state")
    return dict(row)


def require_exact_wake_ownership(
    connection: sqlite3.Connection,
    wake_batch_id: str,
    *,
    effect_id: str | None = None,
    binding_id: str | None = None,
) -> dict[str, object]:
    """Prove the one exact open wake/effect relation in an ambient txn.

    This deliberately treats a missing, crossed, foreign, or duplicate open
    effect as ambiguity.  Callers must not submit or cancel on ambiguity.
    """

    if not connection.in_transaction:
        raise EffectError("exact wake ownership proof requires an ambient transaction")
    batch = connection.execute(
        "SELECT * FROM wake_batches WHERE wake_batch_id = ?",
        (wake_batch_id,),
    ).fetchone()
    if batch is None:
        raise EffectError("wake batch is missing")
    actual_effect_id = "" if batch["effect_id"] is None else str(batch["effect_id"])
    actual_binding_id = str(batch["binding_id"])
    effect = require_exact_open_effect_ownership(
        connection,
        owner_kind="WAKE_BATCH",
        owner_id=wake_batch_id,
        effect_id=actual_effect_id,
        binding_id=actual_binding_id,
    )
    if effect_id is not None and actual_effect_id != effect_id:
        raise EffectError("wake batch effect relation changed")
    if binding_id is not None and actual_binding_id != binding_id:
        raise EffectError("wake batch binding relation changed")
    row = dict(batch)
    row.update(
        {
            "effect_owner_kind": effect["owner_kind"],
            "effect_owner_id": effect["owner_id"],
            "effect_binding_id": effect["binding_id"],
            "effect_state": effect["state"],
            "effect_method": effect["method"],
            "effect_client_key": effect["client_key"],
            "effect_request_json": effect["request_json"],
        }
    )
    return row


def require_exact_prepared_wake_ownership(
    connection: sqlite3.Connection,
    wake_batch_id: str,
    *,
    effect_id: str | None = None,
    binding_id: str | None = None,
) -> dict[str, object]:
    """Prove the one exact PREPARED wake/effect relation in an ambient txn."""

    row = require_exact_wake_ownership(
        connection,
        wake_batch_id,
        effect_id=effect_id,
        binding_id=binding_id,
    )
    if str(row["state"]) != "PREPARED" or str(row["effect_state"]) != "PREPARED":
        raise EffectError("wake batch/effect ownership is not PREPARED")
    binding = connection.execute(
        """SELECT actor_context_id, thread_id
        FROM managed_actor_bindings WHERE binding_id = ?""",
        (str(row["binding_id"]),),
    ).fetchone()
    if binding is None or str(binding["thread_id"] or "") != str(row["thread_id"]):
        raise EffectError("prepared wake binding/thread ownership is not exact")
    expected_client_key = f"hmasd-wake:{wake_batch_id}"
    try:
        request = json.loads(str(row["effect_request_json"]))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise EffectError("prepared wake request is not exact") from exc
    request_keys = set(request)
    if (
        str(row["client_user_message_id"]) != expected_client_key
        or str(row["effect_owner_kind"]) != "WAKE_BATCH"
        or str(row["effect_owner_id"]) != wake_batch_id
        or str(row["effect_binding_id"] or "") != str(row["binding_id"])
        or str(row["effect_method"]) != "turn/start"
        or str(row["effect_client_key"]) != expected_client_key
        or request.get("clientUserMessageId") != expected_client_key
        or str(request.get("threadId") or "") != str(row["thread_id"])
        or not request_keys.issubset(
            {"clientUserMessageId", "threadId", "input", "approvalPolicy"}
        )
        or (
            "approvalPolicy" in request and request.get("approvalPolicy") != "never"
        )
        or (
            "input" in request
            and (
                not isinstance(request.get("input"), list)
                or len(request["input"]) != 1
                or not isinstance(request["input"][0], Mapping)
                or request["input"][0].get("type") != "text"
                or not isinstance(request["input"][0].get("text"), str)
            )
        )
    ):
        raise EffectError("prepared wake effect/request ownership is not exact")

    memberships = connection.execute(
        """SELECT w.message_id, w.ordinal, m.target_actor_context_id
        FROM wake_batch_messages w
        LEFT JOIN mailbox_messages m ON m.message_id = w.message_id
        WHERE w.wake_batch_id = ?
        ORDER BY w.ordinal, w.message_id""",
        (wake_batch_id,),
    ).fetchall()
    if (
        not memberships
        or [int(item["ordinal"]) for item in memberships]
        != list(range(len(memberships)))
        or any(
            item["target_actor_context_id"] is None
            or str(item["target_actor_context_id"])
            != str(binding["actor_context_id"])
            for item in memberships
        )
    ):
        raise EffectError("prepared wake message target/membership is not exact")
    for item in memberships:
        owners = connection.execute(
            """SELECT b.wake_batch_id
            FROM wake_batch_messages w
            JOIN wake_batches b ON b.wake_batch_id = w.wake_batch_id
            WHERE w.message_id = ?
              AND b.state IN ('PREPARED','SUBMITTING','SUBMITTED',
                              'SUBMISSION_UNCERTAIN','ACTIVE')
            ORDER BY b.wake_batch_id""",
            (str(item["message_id"]),),
        ).fetchall()
        if len(owners) != 1 or str(owners[0][0]) != wake_batch_id:
            raise EffectError("prepared wake message membership is not sole")
    if "input" in request:
        injections = connection.execute(
            """SELECT binding_id, mailbox_message_ids_json, input_byte_length
            FROM managed_context_injections WHERE turn_intent_id = ?
            ORDER BY injection_id""",
            (wake_batch_id,),
        ).fetchall()
        if (
            len(injections) != 1
            or str(injections[0]["binding_id"]) != str(row["binding_id"])
        ):
            raise EffectError("prepared wake durable context relation is not exact")
        try:
            injected_messages = json.loads(
                str(injections[0]["mailbox_message_ids_json"])
            )
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise EffectError("prepared wake durable message relation is not exact") from exc
        membership_ids = [str(item["message_id"]) for item in memberships]
        if injected_messages != membership_ids:
            raise EffectError("prepared wake durable message relation is not exact")
        input_text = str(request["input"][0]["text"])
        if len(input_text.encode("utf-8")) != int(injections[0]["input_byte_length"]):
            raise EffectError("prepared wake input relation is not exact")
    return row


def require_exact_canary_submission_ownership(
    connection: sqlite3.Connection,
    record: EffectRecord,
    *,
    run_id: str | None = None,
    validate_contract: bool = True,
) -> None:
    """Prove the one allowed thread/start -> turn/start canary chain.

    RESPONSE_OBSERVED is not ignored wholesale.  The only accepted historical
    row is the explicit predecessor named by the PREPARED turn/start effect.
    Every other row in the complete open set is ambiguity.
    """

    if not connection.in_transaction:
        raise EffectError("canary ownership proof requires an ambient transaction")
    rows = connection.execute(
        """SELECT * FROM app_server_effects
        WHERE owner_kind = 'EPHEMERAL_CANARY' AND owner_id = ?
          AND state IN ('PREPARED','WRITE_STARTED','RESPONSE_OBSERVED',
                        'SUBMISSION_UNCERTAIN','INCIDENT')
        ORDER BY effect_id""",
        (record.owner_id,),
    ).fetchall()
    current = [row for row in rows if str(row["effect_id"]) == record.effect_id]
    if len(current) != 1 or str(current[0]["state"]) != EffectState.PREPARED.value:
        raise EffectError("canary current effect ownership is not exactly PREPARED")
    row = current[0]
    if row["binding_id"] is not None:
        raise EffectError("canary effect must not have a managed binding")
    try:
        require_canonical_canary_id(record.owner_id)
    except ValueError as exc:
        raise EffectError("canary owner id is not canonical") from exc
    if (
        str(row["owner_kind"]) != "EPHEMERAL_CANARY"
        or str(row["owner_id"]) != record.owner_id
        or str(row["effect_id"]) != record.effect_id
        or str(row["method"]) != record.method
    ):
        raise EffectError("canary current effect relation is not exact")

    runtime_home: str | None = None
    if validate_contract:
        if run_id is None:
            raise EffectError("canary contract proof requires a run id")
        run_rows = connection.execute(
            "SELECT runtime_home FROM observer_runs WHERE run_id = ?", (run_id,)
        ).fetchall()
        if len(run_rows) != 1 or not str(run_rows[0]["runtime_home"] or ""):
            raise EffectError("canary runtime provenance is not exact")
        runtime_home = str(run_rows[0]["runtime_home"])

    predecessor_id = row["predecessor_effect_id"]
    if record.method == "thread/start":
        if predecessor_id is not None or len(rows) != 1:
            raise EffectError("canary thread/start has an unexpected predecessor or peer")
        if not validate_contract:
            return
        if str(row["client_key"]) != f"canary:thread/start:{record.owner_id}":
            raise EffectError("canary thread/start key is not canonical")
        try:
            request = json.loads(str(row["request_json"]))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise EffectError("canary thread/start request is not exact") from exc
        assert runtime_home is not None
        try:
            expected_request = canonical_canary_thread_start_request(
                runtime_home, record.owner_id
            )
        except ValueError as exc:
            raise EffectError("canary thread/start request is not canonical") from exc
        if not is_exact_canary_request(request, expected_request):
            raise EffectError("canary thread/start request is not exact")
        return

    if record.method != "turn/start" or predecessor_id is None or len(rows) != 2:
        raise EffectError("canary turn/start predecessor relation is missing or ambiguous")
    predecessors = [row for row in rows if str(row["effect_id"]) == str(predecessor_id)]
    if len(predecessors) != 1:
        raise EffectError("canary predecessor is missing or ambiguous")
    if not validate_contract:
        return
    predecessor = predecessors[0]
    try:
        current_request = json.loads(str(row["request_json"]))
        predecessor_request = json.loads(str(predecessor["request_json"]))
        predecessor_response = json.loads(str(predecessor["response_json"] or "{}"))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise EffectError("canary predecessor evidence is not parseable") from exc
    response_result = predecessor_response.get("result")
    response_thread = (
        response_result.get("thread") if isinstance(response_result, Mapping) else None
    )
    predecessor_thread_id = predecessor["thread_id"]
    response_thread_id = (
        response_thread.get("id") if isinstance(response_thread, Mapping) else None
    )
    if (
        type(predecessor_thread_id) is not str
        or not predecessor_thread_id
        or type(response_thread_id) is not str
        or not response_thread_id
    ):
        raise EffectError("canary predecessor thread identity is not a native string")
    assert runtime_home is not None
    try:
        expected_predecessor_request = canonical_canary_thread_start_request(
            runtime_home, record.owner_id
        )
        expected_current_request = canonical_canary_turn_start_request(
            predecessor_thread_id
        )
    except ValueError as exc:
        raise EffectError("canary request relation is not canonical") from exc
    if (
        str(row["client_key"]) != f"canary:turn/start:{record.owner_id}"
        or predecessor["binding_id"] is not None
        or predecessor["predecessor_effect_id"] is not None
        or str(predecessor["state"]) != EffectState.RESPONSE_OBSERVED.value
        or str(predecessor["method"]) != "thread/start"
        or str(predecessor["client_key"])
        != f"canary:thread/start:{record.owner_id}"
        or not is_exact_canary_request(
            predecessor_request, expected_predecessor_request
        )
        or not is_exact_canary_request(current_request, expected_current_request)
        or not isinstance(response_thread, Mapping)
        or response_thread.get("ephemeral") is not True
        or response_thread_id != predecessor_thread_id
        or (run_id is not None and str(predecessor["run_id"] or "") != run_id)
    ):
        raise EffectError("canary predecessor method/request/run relation is not exact")


def cancel_exact_prepared_wake(
    connection: sqlite3.Connection,
    wake_batch_id: str,
    *,
    effect_id: str,
    binding_id: str,
    cause_ref: str,
) -> dict[str, object]:
    """Cancel/requeue only after exact joined PREPARED ownership is proven."""

    require_exact_prepared_wake_ownership(
        connection,
        wake_batch_id,
        effect_id=effect_id,
        binding_id=binding_id,
    )
    return cancel_prepared_wake(connection, wake_batch_id, cause_ref=cause_ref)


def cancel_exact_prepared_resume_and_wake(
    connection: sqlite3.Connection,
    wake_batch_id: str,
    *,
    resume_effect_id: str,
    binding_id: str,
    actor_context_id: str,
    actor_kind: str,
    semantic_scope_key: str,
    direction_id: str | None,
    thread_id: str,
    checkpoint_id: str | None,
    state_version: int,
    epoch_id: str | None,
    epoch_revision: int | None,
    cause_ref: str,
) -> dict[str, object]:
    """Atomically contain one cancelled, exactly PREPARED recovery resume.

    Every ownership and payload relation is proven before either the resume
    effect or wake delivery is changed.  Any missing, crossed, duplicate, or
    post-write relation raises and leaves the ambient transaction unchanged.
    """

    if not connection.in_transaction:
        raise EffectError("cancelled resume containment requires an ambient transaction")

    resume = require_exact_open_effect_ownership(
        connection,
        owner_kind="THREAD_RESUME",
        owner_id=binding_id,
        effect_id=resume_effect_id,
        binding_id=binding_id,
        expected_states=(EffectState.PREPARED.value,),
    )
    binding = connection.execute(
        """SELECT actor_context_id, actor_kind, semantic_scope_key, direction_id,
                  thread_id, binding_state, prepared_context_trusted
        FROM managed_actor_bindings WHERE binding_id = ?""",
        (binding_id,),
    ).fetchone()
    if binding is None or (
        str(binding["actor_context_id"]) != actor_context_id
        or str(binding["actor_kind"]) != actor_kind
        or str(binding["semantic_scope_key"]) != semantic_scope_key
        or binding["direction_id"] != direction_id
        or str(binding["thread_id"] or "") != thread_id
        or str(binding["binding_state"]) != "ACTIVE"
        or int(binding["prepared_context_trusted"] or 0) != 1
    ):
        raise EffectError("cancelled resume binding ownership is not exact")

    expected_resume_key = f"thread/resume:{thread_id}:{wake_batch_id}"
    try:
        resume_request = json.loads(str(resume["request_json"]))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise EffectError("cancelled resume request is not exact") from exc
    if (
        str(resume["owner_kind"]) != "THREAD_RESUME"
        or str(resume["owner_id"]) != binding_id
        or str(resume["binding_id"] or "") != binding_id
        or str(resume["method"]) != "thread/resume"
        or str(resume["client_key"]) != expected_resume_key
        or str(resume["state"]) != EffectState.PREPARED.value
        or resume_request != {"threadId": thread_id}
    ):
        raise EffectError("cancelled resume effect ownership is not exactly PREPARED")
    wake = require_exact_prepared_wake_ownership(
        connection,
        wake_batch_id,
        binding_id=binding_id,
    )
    wake_effect_id = str(wake["effect_id"] or "")
    wake_client_id = str(wake["client_user_message_id"])
    try:
        wake_request = json.loads(str(wake["effect_request_json"]))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise EffectError("cancelled wake request is not exact") from exc
    if (
        str(wake["thread_id"]) != thread_id
        or str(wake["effect_owner_kind"]) != "WAKE_BATCH"
        or str(wake["effect_method"]) != "turn/start"
        or str(wake["effect_client_key"]) != wake_client_id
        or wake_request
        != {"clientUserMessageId": wake_client_id, "threadId": thread_id}
    ):
        raise EffectError("cancelled wake batch ownership is not exact")
    open_batches = connection.execute(
        """SELECT wake_batch_id FROM wake_batches
        WHERE binding_id = ?
          AND state IN ('PREPARED','SUBMITTING','SUBMITTED','SUBMISSION_UNCERTAIN','ACTIVE')""",
        (binding_id,),
    ).fetchall()
    if len(open_batches) != 1 or str(open_batches[0][0]) != wake_batch_id:
        raise EffectError("cancelled wake has ambiguous open batch ownership")

    injections = connection.execute(
        """SELECT binding_id, checkpoint_id, state_version, epoch_id,
                  epoch_revision, mailbox_message_ids_json
        FROM managed_context_injections WHERE turn_intent_id = ?
        ORDER BY created_at, injection_id""",
        (wake_batch_id,),
    ).fetchall()
    if len(injections) != 1:
        raise EffectError("cancelled wake context ownership is missing or ambiguous")
    injection = injections[0]
    actual_context = (
        injection["checkpoint_id"],
        int(injection["state_version"] or 0),
        injection["epoch_id"],
        None
        if injection["epoch_revision"] is None
        else int(injection["epoch_revision"]),
    )
    expected_context = (checkpoint_id, state_version, epoch_id, epoch_revision)
    if str(injection["binding_id"]) != binding_id or actual_context != expected_context:
        raise EffectError("cancelled wake context tuple is not exact")

    messages = connection.execute(
        """SELECT m.message_id, m.target_actor_context_id, m.delivery_state,
                  b.ordinal
        FROM wake_batch_messages b
        JOIN mailbox_messages m ON m.message_id = b.message_id
        WHERE b.wake_batch_id = ? ORDER BY b.ordinal, b.message_id""",
        (wake_batch_id,),
    ).fetchall()
    message_ids = [str(row["message_id"]) for row in messages]
    try:
        injected_message_ids = json.loads(str(injection["mailbox_message_ids_json"]))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise EffectError("cancelled wake message context is not exact") from exc
    if (
        not message_ids
        or injected_message_ids != message_ids
        or [int(row["ordinal"]) for row in messages] != list(range(len(messages)))
        or any(
            str(row["target_actor_context_id"]) != actor_context_id
            or str(row["delivery_state"]) != "BATCHED"
            for row in messages
        )
    ):
        raise EffectError("cancelled wake message ownership is not exact")
    for message_id in message_ids:
        owners = connection.execute(
            """SELECT b.wake_batch_id
            FROM wake_batch_messages m
            JOIN wake_batches b ON b.wake_batch_id = m.wake_batch_id
            WHERE m.message_id = ?
              AND b.state IN ('PREPARED','SUBMITTING','SUBMITTED','SUBMISSION_UNCERTAIN','ACTIVE')""",
            (message_id,),
        ).fetchall()
        if len(owners) != 1 or str(owners[0][0]) != wake_batch_id:
            raise EffectError("cancelled wake message has ambiguous open ownership")

    journal = EffectJournal(connection)
    journal.cancel_before_write(resume_effect_id, cause_ref=cause_ref)
    result = cancel_exact_prepared_wake(
        connection,
        wake_batch_id,
        effect_id=wake_effect_id,
        binding_id=binding_id,
        cause_ref=cause_ref,
    )
    result["resume_effect_id"] = resume_effect_id
    return result


def cancel_prepared_turn(connection: sqlite3.Connection, turn_intent_id: str, effect_id: str, *, cause_ref: str) -> None:
    from .models import AggregateKind, TransitionCause, TransitionRequest
    from .transitions import TransitionKernel

    journal = EffectJournal(connection)
    kernel = TransitionKernel(connection)
    with journal._tx():
        row = connection.execute(
            "SELECT submission_state, version FROM managed_turn_intents WHERE turn_intent_id = ?",
            (turn_intent_id,),
        ).fetchone()
        if row is not None and str(row["submission_state"]) == "PREPARED":
            kernel.apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.MANAGED_TURN,
                    aggregate_id=turn_intent_id,
                    expected_state="PREPARED",
                    expected_version=int(row["version"] or 0),
                    target_state="CANCELLED",
                    cause_kind=TransitionCause.PRE_WRITE_CANCEL,
                    cause_ref=cause_ref,
                )
            )
        journal.cancel_prepared_if_present(effect_id, cause_ref=cause_ref)


TURN_OBSERVED_DISPOSITIONS = frozenset({"TURN_OBSERVED_ACTIVE", "TURN_OBSERVED_COMPLETED"})


def effect_is_completion_ready(connection: sqlite3.Connection, effect_id: str) -> bool:
    """True when completion may treat the linked effect as evidence-confirmed."""
    row = connection.execute(
        "SELECT state FROM app_server_effects WHERE effect_id = ?",
        (effect_id,),
    ).fetchone()
    if row is None:
        return False
    state = str(row[0])
    if state == EffectState.EFFECT_CONFIRMED.value:
        return True
    if state != EffectState.OPERATOR_RESOLVED.value:
        return False
    resolution = connection.execute(
        """SELECT disposition FROM operator_resolutions
        WHERE aggregate_kind = ? AND aggregate_id = ?
        ORDER BY created_at DESC LIMIT 1""",
        (AggregateKind.APP_SERVER_EFFECT.value, effect_id),
    ).fetchone()
    return resolution is not None and str(resolution[0]) in TURN_OBSERVED_DISPOSITIONS
