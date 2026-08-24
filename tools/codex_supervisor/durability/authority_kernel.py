"""Closed-union authority plans and the final typed submission proof.

The types in this module deliberately contain only immutable scalar values,
bytes, enums, and tuples.  No caller-supplied executable, mapping, SQL, or
transition list can cross the submission boundary.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TypeAlias

from ..canary_contract import is_exact_canary_request
from .effects import (
    EffectError,
    EffectJournal,
    _canonical_request,
    require_exact_canary_submission_ownership,
    require_exact_open_effect_ownership,
    require_exact_prepared_wake_ownership,
)
from .models import AggregateKind, TransitionCause, TransitionRequest
from .transitions import TransitionKernel

AUTHORITY_PLAN_VERSION = 1
THREAD_MEMORY_ALLOWED_BINDING_STATES = frozenset(
    {"PREPARED", "THREAD_CREATED", "VERIFICATION_REQUIRED", "ACTIVE"}
)


class AuthorityLeaseError(EffectError):
    """Final authoritative scheduler-lease proof failed before write."""


class ResumeMode(str, Enum):
    ADOPTION = "ADOPTION"
    WAKE_RECOVERY = "WAKE_RECOVERY"


class CanaryPhase(str, Enum):
    THREAD_START = "THREAD_START"
    TURN_START = "TURN_START"


@dataclass(frozen=True)
class _OwnerPlan:
    effect_id: str
    owner_kind: str
    owner_id: str
    binding_id: str | None
    predecessor_effect_id: str | None
    method: str
    client_key: str
    request_bytes: bytes
    request_sha256: str
    request_byte_length: int
    sealed_at: str
    plan_version: int
    effect_version: int
    actor_context_id: str | None
    actor_kind: str | None
    semantic_scope_key: str | None
    direction_id: str | None
    binding_state: str | None
    binding_version: int | None
    thread_id: str | None
    checkpoint_id: str | None
    state_version: int | None
    epoch_id: str | None
    epoch_revision: int | None


@dataclass(frozen=True)
class ManagedTurnPlan(_OwnerPlan):
    intent_version: int
    intent_kind: str
    context_injection_id: str
    input_sha256: str


@dataclass(frozen=True)
class WakeBatchPlan(_OwnerPlan):
    batch_version: int
    lease_key: str
    lease_holder: str
    lease_generation: int
    context_injection_id: str
    input_sha256: str
    membership_ids: tuple[str, ...]


@dataclass(frozen=True)
class ThreadProvisionPlan(_OwnerPlan):
    pass


@dataclass(frozen=True)
class ThreadResumePlan(_OwnerPlan):
    mode: ResumeMode
    wake_batch_id: str | None
    context_injection_id: str | None
    lease_key: str | None
    lease_holder: str | None
    lease_generation: int | None


@dataclass(frozen=True)
class ThreadMemoryPlan(_OwnerPlan):
    pass


@dataclass(frozen=True)
class EphemeralCanaryPlan(_OwnerPlan):
    phase: CanaryPhase


OwnerPlan: TypeAlias = (
    ManagedTurnPlan
    | WakeBatchPlan
    | ThreadProvisionPlan
    | ThreadResumePlan
    | ThreadMemoryPlan
    | EphemeralCanaryPlan
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_bytes(request: object) -> bytes:
    if not isinstance(request, dict):
        raise EffectError("authority request must be a JSON object")
    return _canonical_request(request).encode("utf-8")


def _binding_fields(connection: sqlite3.Connection, binding_id: str | None) -> tuple[object, ...]:
    if binding_id is None:
        return (None,) * 12
    row = connection.execute(
        "SELECT * FROM managed_actor_bindings WHERE binding_id=?", (binding_id,)
    ).fetchone()
    if row is None:
        raise EffectError("authority plan binding is missing")
    state = str(row["binding_state"])
    if state == "ACTIVE":
        currentness = (
            row["verified_checkpoint_id"],
            row["verified_state_version"],
            row["verified_epoch_id"],
            row["verified_epoch_revision"],
        )
    else:
        currentness = (
            row["prepared_checkpoint_id"],
            row["prepared_state_version"],
            row["prepared_epoch_id"],
            row["prepared_epoch_revision"],
        )
    return (
        str(row["actor_context_id"]),
        str(row["actor_kind"]),
        str(row["semantic_scope_key"]),
        None if row["direction_id"] is None else str(row["direction_id"]),
        state,
        int(row["version"] or 0),
        None if row["thread_id"] is None else str(row["thread_id"]),
        None if currentness[0] is None else str(currentness[0]),
        None if currentness[1] is None else int(currentness[1]),
        None if currentness[2] is None else str(currentness[2]),
        None if currentness[3] is None else int(currentness[3]),
        int(row["prepared_context_trusted"] or 0),
    )


def _base(connection: sqlite3.Connection, effect_id: str) -> tuple[object, ...]:
    effect = EffectJournal(connection).get(effect_id)
    if effect.state != "PREPARED":
        raise EffectError("typed authority plans require a PREPARED effect")
    if (
        effect.plan_version != AUTHORITY_PLAN_VERSION
        or not effect.sealed_at
        or not effect.request_sha256
        or effect.request_byte_length is None
    ):
        raise EffectError("effect has no current durable authority seal")
    request_bytes = _canonical_bytes(dict(effect.request))
    if (
        len(request_bytes) != effect.request_byte_length
        or hashlib.sha256(request_bytes).hexdigest() != effect.request_sha256
    ):
        raise EffectError("durable effect request seal is inconsistent")
    binding = _binding_fields(connection, effect.binding_id)
    if effect.binding_id is not None and binding[-1] != 1:
        raise EffectError("authority plan binding has untrusted prepared provenance")
    return (
        effect.effect_id,
        effect.owner_kind,
        effect.owner_id,
        effect.binding_id,
        effect.predecessor_effect_id,
        effect.method,
        effect.client_key,
        request_bytes,
        effect.request_sha256,
        effect.request_byte_length,
        effect.sealed_at,
        effect.plan_version,
        effect.version,
        *binding[:-1],
    )


def _seal_existing(connection: sqlite3.Connection, effect_id: str) -> None:
    effect = EffectJournal(connection).get(effect_id)
    EffectJournal(connection).seal_effect(effect_id, request=effect.request)


def seal_managed_turn(
    connection: sqlite3.Connection, intent_id: str, input_text: str
) -> ManagedTurnPlan:
    if not connection.in_transaction:
        raise EffectError("managed-turn sealing requires an ambient transaction")
    intent = connection.execute(
        "SELECT * FROM managed_turn_intents WHERE turn_intent_id=?", (intent_id,)
    ).fetchone()
    if intent is None or str(intent["submission_state"]) != "PREPARED":
        raise EffectError("managed turn is not PREPARED")
    effect_id = str(intent["effect_id"] or "")
    request = {
        "threadId": str(intent["app_server_thread_id"]),
        "input": [{"type": "text", "text": input_text}],
        "approvalPolicy": "never",
        "clientUserMessageId": str(intent["client_user_message_id"]),
    }
    input_bytes = input_text.encode("utf-8")
    input_sha256 = hashlib.sha256(input_bytes).hexdigest()
    injections = connection.execute(
        """SELECT * FROM managed_context_injections
        WHERE turn_intent_id=? AND binding_id=? ORDER BY injection_id""",
        (intent_id, str(intent["binding_id"])),
    ).fetchall()
    if len(injections) > 1:
        raise EffectError("managed turn has ambiguous durable input provenance")
    if not injections:
        injection_id = f"inj_{uuid.uuid4().hex}"
        connection.execute(
            """INSERT INTO managed_context_injections(
                injection_id,turn_intent_id,binding_id,checkpoint_id,state_version,
                epoch_id,epoch_revision,canonical_refs_json,open_obligation_ids_json,
                mailbox_message_ids_json,input_byte_length,input_bytes,input_sha256,created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                injection_id,
                intent_id,
                str(intent["binding_id"]),
                intent["checkpoint_id"],
                intent["expected_state_version"],
                intent["expected_epoch_id"],
                intent["expected_epoch_revision"],
                "[]",
                "[]",
                "[]",
                len(input_bytes),
                input_bytes,
                input_sha256,
                _now(),
            ),
        )
    else:
        injection_id = str(injections[0]["injection_id"])
        if (
            bytes(injections[0]["input_bytes"] or b"") != input_bytes
            or str(injections[0]["input_sha256"] or "") != input_sha256
            or int(injections[0]["input_byte_length"] or 0) != len(input_bytes)
        ):
            raise EffectError("managed turn input differs from durable provenance")
    EffectJournal(connection).seal_effect(effect_id, request=request)
    base_items = list(_base(connection, effect_id))
    base_items[20:24] = [
        None if intent["checkpoint_id"] is None else str(intent["checkpoint_id"]),
        None
        if intent["expected_state_version"] is None
        else int(intent["expected_state_version"]),
        None if intent["expected_epoch_id"] is None else str(intent["expected_epoch_id"]),
        None
        if intent["expected_epoch_revision"] is None
        else int(intent["expected_epoch_revision"]),
    ]
    base = tuple(base_items)
    if base[1:4] != ("MANAGED_TURN", intent_id, str(intent["binding_id"])):
        raise EffectError("managed-turn effect ownership is not exact")
    return ManagedTurnPlan(
        *base,
        intent_version=int(intent["version"] or 0),
        intent_kind=str(intent["intent_kind"]),
        context_injection_id=injection_id,
        input_sha256=input_sha256,
    )


def seal_wake_batch(
    connection: sqlite3.Connection,
    wake_batch_id: str,
    lease_holder: str,
    lease_generation: int,
) -> WakeBatchPlan:
    if not connection.in_transaction:
        raise EffectError("wake sealing requires an ambient transaction")
    wake = require_exact_prepared_wake_ownership(connection, wake_batch_id)
    effect_id = str(wake["effect_id"])
    _seal_existing(connection, effect_id)
    wake = connection.execute(
        "SELECT * FROM wake_batches WHERE wake_batch_id=?", (wake_batch_id,)
    ).fetchone()
    assert wake is not None
    if (
        str(wake["lease_holder"] or "") != lease_holder
        or int(wake["lease_generation"] or -1) != lease_generation
        or not wake["context_injection_id"]
    ):
        raise EffectError("wake lease/context authority is not exact")
    injection = connection.execute(
        "SELECT * FROM managed_context_injections WHERE injection_id=?",
        (str(wake["context_injection_id"]),),
    ).fetchone()
    if injection is None or not injection["input_bytes"] or not injection["input_sha256"]:
        raise EffectError("wake exact durable envelope is missing")
    memberships = tuple(
        str(row["message_id"])
        for row in connection.execute(
            "SELECT message_id FROM wake_batch_messages WHERE wake_batch_id=? ORDER BY ordinal",
            (wake_batch_id,),
        ).fetchall()
    )
    base_items = list(_base(connection, effect_id))
    base_items[20:24] = [
        None if injection["checkpoint_id"] is None else str(injection["checkpoint_id"]),
        None if injection["state_version"] is None else int(injection["state_version"]),
        None if injection["epoch_id"] is None else str(injection["epoch_id"]),
        None if injection["epoch_revision"] is None else int(injection["epoch_revision"]),
    ]
    base = tuple(base_items)
    if base[1:4] != ("WAKE_BATCH", wake_batch_id, str(wake["binding_id"])):
        raise EffectError("wake effect ownership is not exact")
    return WakeBatchPlan(
        *base,
        batch_version=int(wake["version"] or 0),
        lease_key=f"wake:{wake['binding_id']}",
        lease_holder=lease_holder,
        lease_generation=lease_generation,
        context_injection_id=str(wake["context_injection_id"]),
        input_sha256=str(injection["input_sha256"]),
        membership_ids=memberships,
    )


def _seal_binding_owner(
    connection: sqlite3.Connection,
    effect_id: str,
    expected_kind: str,
) -> tuple[object, ...]:
    if not connection.in_transaction:
        raise EffectError("binding-owner sealing requires an ambient transaction")
    _seal_existing(connection, effect_id)
    base = _base(connection, effect_id)
    if base[1] != expected_kind or base[3] is None or base[2] != base[3]:
        raise EffectError("binding-owner effect ownership is not exact")
    return base


def seal_thread_provision(connection: sqlite3.Connection, effect_id: str) -> ThreadProvisionPlan:
    return ThreadProvisionPlan(*_seal_binding_owner(connection, effect_id, "THREAD_PROVISION"))


def seal_thread_memory(connection: sqlite3.Connection, effect_id: str) -> ThreadMemoryPlan:
    base = _seal_binding_owner(connection, effect_id, "THREAD_MEMORY")
    if base[17] not in THREAD_MEMORY_ALLOWED_BINDING_STATES:
        raise EffectError("thread-memory binding state is not allowed")
    return ThreadMemoryPlan(*base)


def seal_thread_resume(
    connection: sqlite3.Connection,
    effect_id: str,
    *,
    mode: ResumeMode,
    wake_batch_id: str | None = None,
) -> ThreadResumePlan:
    base = _seal_binding_owner(connection, effect_id, "THREAD_RESUME")
    context_id = None
    lease_key = None
    lease_holder = None
    lease_generation = None
    if mode is ResumeMode.ADOPTION:
        if wake_batch_id is not None:
            raise EffectError("adoption resume cannot name a wake batch")
        effect = EffectJournal(connection).get(effect_id)
        request = dict(effect.request)
        if set(request) != {"threadId"} or type(request.get("threadId")) is not str:
            raise EffectError("adoption resume request is not exact")
        base_items = list(base)
        base_items[19] = request["threadId"]
        base = tuple(base_items)
    else:
        if not wake_batch_id:
            raise EffectError("wake-recovery resume requires a wake batch")
        wake = connection.execute(
            "SELECT * FROM wake_batches WHERE wake_batch_id=?", (wake_batch_id,)
        ).fetchone()
        if (
            wake is None
            or str(wake["binding_id"]) != str(base[3])
            or str(wake["state"]) != "PREPARED"
            or not wake["context_injection_id"]
        ):
            raise EffectError("wake-recovery resume relation is not exact")
        context_id = str(wake["context_injection_id"])
        lease_key = f"wake:{wake['binding_id']}"
        lease_holder = None if wake["lease_holder"] is None else str(wake["lease_holder"])
        lease_generation = (
            None if wake["lease_generation"] is None else int(wake["lease_generation"])
        )
        if not lease_holder or lease_generation is None:
            raise EffectError("wake-recovery resume has no exact lease identity")
        context = connection.execute(
            "SELECT * FROM managed_context_injections WHERE injection_id=?",
            (context_id,),
        ).fetchone()
        if context is None:
            raise EffectError("wake-recovery resume context is missing")
        base_items = list(base)
        base_items[20:24] = [
            None if context["checkpoint_id"] is None else str(context["checkpoint_id"]),
            None if context["state_version"] is None else int(context["state_version"]),
            None if context["epoch_id"] is None else str(context["epoch_id"]),
            None if context["epoch_revision"] is None else int(context["epoch_revision"]),
        ]
        base = tuple(base_items)
    return ThreadResumePlan(
        *base,
        mode=mode,
        wake_batch_id=wake_batch_id,
        context_injection_id=context_id,
        lease_key=lease_key,
        lease_holder=lease_holder,
        lease_generation=lease_generation,
    )


def seal_ephemeral_canary(
    connection: sqlite3.Connection,
    effect_id: str,
    *,
    phase: CanaryPhase,
) -> EphemeralCanaryPlan:
    if not connection.in_transaction:
        raise EffectError("canary sealing requires an ambient transaction")
    _seal_existing(connection, effect_id)
    base = _base(connection, effect_id)
    expected_method = "thread/start" if phase is CanaryPhase.THREAD_START else "turn/start"
    if base[1] != "EPHEMERAL_CANARY" or base[3] is not None or base[5] != expected_method:
        raise EffectError("canary phase/effect ownership is not exact")
    return EphemeralCanaryPlan(*base, phase=phase)


def request_object(plan: OwnerPlan) -> dict[str, object]:
    parsed = json.loads(plan.request_bytes.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise EffectError("sealed request is not an object")
    return parsed


def semantic_guard(store: object, plan: OwnerPlan):
    if plan.actor_context_id is None:
        return nullcontext()
    bridge = getattr(store, "_semantic_bridge", None)
    if bridge is None:
        return nullcontext()
    if plan.state_version is None:
        raise EffectError("typed plan has no semantic state version")
    return bridge.currentness_guard(
        plan.actor_context_id,
        checkpoint_id=plan.checkpoint_id,
        state_version=plan.state_version,
        epoch_id=plan.epoch_id,
        epoch_revision=plan.epoch_revision,
    )


def apply_typed_preclaim(connection: sqlite3.Connection, plan: OwnerPlan) -> None:
    """Apply the closed set of owner operations before final reproof."""

    kernel = TransitionKernel(connection)
    if isinstance(plan, ManagedTurnPlan):
        kernel.apply(
            TransitionRequest(
                aggregate_kind=AggregateKind.MANAGED_TURN,
                aggregate_id=plan.owner_id,
                expected_state="PREPARED",
                expected_version=plan.intent_version,
                target_state="SUBMITTING",
                cause_kind=TransitionCause.APP_SERVER_EFFECT,
                cause_ref=plan.effect_id,
            )
        )
        return
    if isinstance(plan, WakeBatchPlan):
        kernel.apply(
            TransitionRequest(
                aggregate_kind=AggregateKind.WAKE_BATCH,
                aggregate_id=plan.owner_id,
                expected_state="PREPARED",
                expected_version=plan.batch_version,
                target_state="SUBMITTING",
                cause_kind=TransitionCause.APP_SERVER_EFFECT,
                cause_ref=plan.effect_id,
            )
        )
        connection.execute(
            """INSERT INTO wake_attempts(
                wake_attempt_id,wake_batch_id,attempt_number,request_id,
                outcome,error_json,created_at
            ) VALUES (?, ?, 1, NULL, 'SUBMITTING', NULL, ?)""",
            (f"watt_{uuid.uuid4().hex}", plan.owner_id, _now()),
        )
        return
    if isinstance(
        plan,
        (ThreadProvisionPlan, ThreadResumePlan, ThreadMemoryPlan, EphemeralCanaryPlan),
    ):
        return
    raise EffectError("authority plan union is not exhaustive")


def _require_request_shape(plan: OwnerPlan, request: dict[str, object]) -> None:
    keys = set(request)
    if isinstance(plan, (ManagedTurnPlan, WakeBatchPlan)):
        if keys != {"threadId", "input", "approvalPolicy", "clientUserMessageId"}:
            raise EffectError("turn/start request key set is not exact")
        item = request.get("input")
        if (
            type(request.get("threadId")) is not str
            or type(request.get("clientUserMessageId")) is not str
            or request.get("approvalPolicy") != "never"
            or type(item) is not list
            or len(item) != 1
            or type(item[0]) is not dict
            or set(item[0]) != {"type", "text"}
            or item[0].get("type") != "text"
            or type(item[0].get("text")) is not str
        ):
            raise EffectError("turn/start request JSON types are not exact")
        return
    if isinstance(plan, ThreadProvisionPlan):
        if (
            keys != {"cwd", "ephemeral", "approvalPolicy"}
            or type(request.get("cwd")) is not str
            or request.get("ephemeral") is not False
            or request.get("approvalPolicy") != "never"
        ):
            raise EffectError("thread provision request is not exact")
        return
    if isinstance(plan, ThreadResumePlan):
        if keys != {"threadId"} or type(request.get("threadId")) is not str:
            raise EffectError("thread resume request is not exact")
        return
    if isinstance(plan, ThreadMemoryPlan):
        if (
            keys != {"threadId", "mode"}
            or type(request.get("threadId")) is not str
            or request.get("mode") != "disabled"
        ):
            raise EffectError("thread memory request is not exact")
        return
    if isinstance(plan, EphemeralCanaryPlan):
        if not is_exact_canary_request(request, request):
            raise EffectError("canary request JSON types are not exact")
        return
    raise EffectError("authority plan request proof is not exhaustive")


def prove_prepared_rpc(plan: OwnerPlan, prepared: object) -> None:
    request = request_object(plan)
    _require_request_shape(plan, request)
    method = getattr(prepared, "method", None)
    params = getattr(prepared, "params", None)
    payload = getattr(prepared, "payload", None)
    if method != plan.method or not isinstance(params, dict) or not isinstance(payload, dict):
        raise EffectError("PreparedRpcRequest has an invalid native shape")
    if _canonical_bytes(params) != plan.request_bytes:
        raise EffectError("PreparedRpcRequest params differ from the durable seal")
    if set(payload) != {"id", "method", "params"} or type(payload.get("id")) is not int:
        raise EffectError("PreparedRpcRequest payload key/type set is not exact")
    if payload.get("method") != plan.method or payload.get("params") != params:
        raise EffectError("PreparedRpcRequest payload differs from params")


def _prove_binding(connection: sqlite3.Connection, plan: OwnerPlan) -> sqlite3.Row | None:
    if plan.binding_id is None:
        return None
    row = connection.execute(
        "SELECT * FROM managed_actor_bindings WHERE binding_id=?", (plan.binding_id,)
    ).fetchone()
    if row is None:
        raise EffectError("typed plan binding disappeared")
    expected_binding_thread = (
        None
        if isinstance(plan, ThreadResumePlan) and plan.mode is ResumeMode.ADOPTION
        else plan.thread_id
    )
    actual = (
        str(row["actor_context_id"]),
        str(row["actor_kind"]),
        str(row["semantic_scope_key"]),
        None if row["direction_id"] is None else str(row["direction_id"]),
        str(row["binding_state"]),
        int(row["version"] or 0),
        None if row["thread_id"] is None else str(row["thread_id"]),
    )
    expected = (
        plan.actor_context_id,
        plan.actor_kind,
        plan.semantic_scope_key,
        plan.direction_id,
        plan.binding_state,
        plan.binding_version,
        expected_binding_thread,
    )
    if actual != expected or int(row["prepared_context_trusted"] or 0) != 1:
        raise EffectError("typed plan binding identity/state/version changed")
    return row


def _prove_current_scheduler_lease(
    connection: sqlite3.Connection,
    *,
    binding_id: str | None,
    lease_key: str | None,
    lease_holder: str | None,
    lease_generation: int | None,
) -> None:
    if binding_id is None:
        raise AuthorityLeaseError("wake authority has no binding")
    expected_key = f"wake:{binding_id}"
    if (
        lease_key != expected_key
        or not lease_holder
        or lease_generation is None
    ):
        raise AuthorityLeaseError("wake authority lease identity is incomplete")
    row = connection.execute(
        "SELECT * FROM scheduler_leases WHERE lease_key=?", (expected_key,)
    ).fetchone()
    if row is None:
        raise AuthorityLeaseError("authoritative scheduler lease is missing")
    try:
        expires_at = datetime.fromisoformat(str(row["expires_at"]))
    except (TypeError, ValueError) as exc:
        raise AuthorityLeaseError("authoritative scheduler lease expiry is invalid") from exc
    if expires_at.tzinfo is None or expires_at.utcoffset() != timedelta(0):
        raise AuthorityLeaseError("authoritative scheduler lease expiry is not strict UTC")
    if (
        str(row["lease_key"]) != expected_key
        or str(row["holder_instance_id"]) != lease_holder
        or int(row["generation"]) != lease_generation
        or expires_at <= datetime.now(timezone.utc)
    ):
        raise AuthorityLeaseError("authoritative scheduler lease expired or transferred")


def final_authority_proof(
    connection: sqlite3.Connection, plan: OwnerPlan, *, run_id: str
) -> None:
    """Re-read every owner/request fact after typed operations, before claim."""

    if not connection.in_transaction:
        raise EffectError("final authority proof requires an ambient transaction")
    effect = EffectJournal(connection).get(plan.effect_id)
    request_bytes = _canonical_bytes(dict(effect.request))
    if (
        effect.state != "PREPARED"
        or effect.version != plan.effect_version
        or effect.owner_kind != plan.owner_kind
        or effect.owner_id != plan.owner_id
        or effect.binding_id != plan.binding_id
        or effect.predecessor_effect_id != plan.predecessor_effect_id
        or effect.method != plan.method
        or effect.client_key != plan.client_key
        or effect.plan_version != plan.plan_version
        or effect.sealed_at != plan.sealed_at
        or effect.request_sha256 != plan.request_sha256
        or effect.request_byte_length != plan.request_byte_length
        or request_bytes != plan.request_bytes
        or hashlib.sha256(request_bytes).hexdigest() != plan.request_sha256
    ):
        raise EffectError("durable authority seal changed before final claim")
    if not isinstance(plan, EphemeralCanaryPlan):
        require_exact_open_effect_ownership(
            connection,
            owner_kind=plan.owner_kind,
            owner_id=plan.owner_id,
            effect_id=plan.effect_id,
            binding_id=plan.binding_id,
            expected_states=("PREPARED",),
        )
    binding = _prove_binding(connection, plan)
    request = request_object(plan)
    _require_request_shape(plan, request)

    if isinstance(plan, ManagedTurnPlan):
        row = connection.execute(
            "SELECT * FROM managed_turn_intents WHERE turn_intent_id=?", (plan.owner_id,)
        ).fetchone()
        injection = connection.execute(
            "SELECT * FROM managed_context_injections WHERE injection_id=?",
            (plan.context_injection_id,),
        ).fetchone()
        input_text = request["input"][0]["text"]  # shape proved above
        input_bytes = input_text.encode("utf-8")
        allowed_binding_state = (
            "VERIFICATION_REQUIRED"
            if plan.intent_kind in {"BOOTSTRAP", "IDENTITY_VERIFICATION"}
            else "ACTIVE"
        )
        if (
            row is None
            or str(row["submission_state"]) != "SUBMITTING"
            or int(row["version"] or 0) != plan.intent_version + 1
            or str(row["effect_id"] or "") != plan.effect_id
            or str(row["intent_kind"]) != plan.intent_kind
            or str(row["binding_id"]) != plan.binding_id
            or str(row["app_server_thread_id"]) != request["threadId"]
            or str(row["client_user_message_id"]) != request["clientUserMessageId"]
            or injection is None
            or str(injection["turn_intent_id"]) != plan.owner_id
            or str(injection["binding_id"]) != plan.binding_id
            or bytes(injection["input_bytes"] or b"") != input_bytes
            or str(injection["input_sha256"] or "") != plan.input_sha256
            or hashlib.sha256(input_bytes).hexdigest() != plan.input_sha256
            or plan.binding_state != allowed_binding_state
            or row["checkpoint_id"] != plan.checkpoint_id
            or (
                None
                if row["expected_state_version"] is None
                else int(row["expected_state_version"])
            )
            != plan.state_version
            or row["expected_epoch_id"] != plan.epoch_id
            or (
                None
                if row["expected_epoch_revision"] is None
                else int(row["expected_epoch_revision"])
            )
            != plan.epoch_revision
            or str(injection["injection_id"]) != plan.context_injection_id
            or injection["checkpoint_id"] != plan.checkpoint_id
            or (
                None if injection["state_version"] is None else int(injection["state_version"])
            )
            != plan.state_version
            or injection["epoch_id"] != plan.epoch_id
            or (
                None
                if injection["epoch_revision"] is None
                else int(injection["epoch_revision"])
            )
            != plan.epoch_revision
        ):
            raise EffectError("managed-turn final owner/input proof failed")
        return

    if isinstance(plan, WakeBatchPlan):
        _prove_current_scheduler_lease(
            connection,
            binding_id=plan.binding_id,
            lease_key=plan.lease_key,
            lease_holder=plan.lease_holder,
            lease_generation=plan.lease_generation,
        )
        final_wake_authority_proof(connection, plan)
        return

    if isinstance(plan, ThreadProvisionPlan):
        if (
            binding is None
            or plan.binding_state != "PREPARED"
            or plan.client_key != f"thread/start:{plan.binding_id}"
            or request["cwd"] != binding["thread_cwd"]
        ):
            raise EffectError("thread-provision final owner proof failed")
        return
    if isinstance(plan, ThreadMemoryPlan):
        if (
            binding is None
            or plan.binding_state not in THREAD_MEMORY_ALLOWED_BINDING_STATES
            or request["threadId"] != binding["thread_id"]
            or plan.client_key != f"thread/memoryMode/set:{plan.thread_id}"
        ):
            raise EffectError("thread-memory final owner proof failed")
        return
    if isinstance(plan, ThreadResumePlan):
        if binding is None or request["threadId"] != plan.thread_id:
            raise EffectError("thread-resume final binding proof failed")
        if plan.mode is ResumeMode.ADOPTION:
            if (
                plan.binding_state != "PREPARED"
                or plan.wake_batch_id is not None
                or plan.lease_key is not None
                or plan.lease_holder is not None
                or plan.lease_generation is not None
                or plan.client_key != f"thread/resume:{plan.thread_id}"
            ):
                raise EffectError("adoption resume variant changed")
        else:
            _prove_current_scheduler_lease(
                connection,
                binding_id=plan.binding_id,
                lease_key=plan.lease_key,
                lease_holder=plan.lease_holder,
                lease_generation=plan.lease_generation,
            )
            wake = connection.execute(
                "SELECT * FROM wake_batches WHERE wake_batch_id=?", (plan.wake_batch_id,)
            ).fetchone()
            context = connection.execute(
                "SELECT * FROM managed_context_injections WHERE injection_id=?",
                (plan.context_injection_id,),
            ).fetchone()
            if (
                plan.binding_state != "ACTIVE"
                or plan.client_key
                != f"thread/resume:{plan.thread_id}:{plan.wake_batch_id}"
                or wake is None
                or str(wake["state"]) != "PREPARED"
                or str(wake["binding_id"]) != plan.binding_id
                or str(wake["context_injection_id"] or "") != plan.context_injection_id
                or context is None
                or str(context["binding_id"]) != plan.binding_id
                or str(context["turn_intent_id"]) != plan.wake_batch_id
            ):
                raise EffectError("wake-recovery resume variant changed")
        return
    if isinstance(plan, EphemeralCanaryPlan):
        require_exact_canary_submission_ownership(
            connection, effect, run_id=run_id, validate_contract=True
        )
        return
    raise EffectError("authority plan final proof is not exhaustive")


def final_wake_authority_proof(
    connection: sqlite3.Connection, plan: WakeBatchPlan
) -> None:
    """Wake-specific post-operation proof (aggregate is now SUBMITTING)."""

    row = connection.execute(
        "SELECT * FROM wake_batches WHERE wake_batch_id=?", (plan.owner_id,)
    ).fetchone()
    injection = connection.execute(
        "SELECT * FROM managed_context_injections WHERE injection_id=?",
        (plan.context_injection_id,),
    ).fetchone()
    memberships = tuple(
        str(item["message_id"])
        for item in connection.execute(
            "SELECT message_id FROM wake_batch_messages WHERE wake_batch_id=? ORDER BY ordinal",
            (plan.owner_id,),
        ).fetchall()
    )
    request = request_object(plan)
    input_bytes = request["input"][0]["text"].encode("utf-8")
    attempts = connection.execute(
        "SELECT attempt_number,outcome FROM wake_attempts WHERE wake_batch_id=?",
        (plan.owner_id,),
    ).fetchall()
    if (
        row is None
        or str(row["state"]) != "SUBMITTING"
        or int(row["version"] or 0) != plan.batch_version + 1
        or str(row["effect_id"] or "") != plan.effect_id
        or str(row["binding_id"]) != plan.binding_id
        or str(row["thread_id"]) != request["threadId"]
        or str(row["client_user_message_id"]) != request["clientUserMessageId"]
        or plan.client_key != f"hmasd-wake:{plan.owner_id}"
        or str(row["lease_holder"] or "") != plan.lease_holder
        or int(row["lease_generation"] or -1) != plan.lease_generation
        or str(row["context_injection_id"] or "") != plan.context_injection_id
        or injection is None
        or bytes(injection["input_bytes"] or b"") != input_bytes
        or str(injection["input_sha256"] or "") != plan.input_sha256
        or hashlib.sha256(input_bytes).hexdigest() != plan.input_sha256
        or plan.binding_state != "ACTIVE"
        or injection["checkpoint_id"] != plan.checkpoint_id
        or (
            None if injection["state_version"] is None else int(injection["state_version"])
        )
        != plan.state_version
        or injection["epoch_id"] != plan.epoch_id
        or (
            None
            if injection["epoch_revision"] is None
            else int(injection["epoch_revision"])
        )
        != plan.epoch_revision
        or memberships != plan.membership_ids
        or len(attempts) != 1
        or int(attempts[0]["attempt_number"]) != 1
        or str(attempts[0]["outcome"]) != "SUBMITTING"
    ):
        raise EffectError("wake final lease/context/membership proof failed")
    for message_id in memberships:
        message = connection.execute(
            """SELECT m.delivery_state,m.target_actor_context_id,b.actor_context_id
            FROM mailbox_messages m JOIN managed_actor_bindings b ON b.binding_id=?
            WHERE m.message_id=?""",
            (plan.binding_id, message_id),
        ).fetchone()
        if (
            message is None
            or str(message["delivery_state"]) != "BATCHED"
            or str(message["target_actor_context_id"]) != str(message["actor_context_id"])
        ):
            raise EffectError("wake message state/target proof failed")
        owners = connection.execute(
            """SELECT b.wake_batch_id
            FROM wake_batch_messages w JOIN wake_batches b
              ON b.wake_batch_id=w.wake_batch_id
            WHERE w.message_id=?
              AND b.state IN ('PREPARED','SUBMITTING','SUBMITTED',
                              'SUBMISSION_UNCERTAIN','ACTIVE')""",
            (message_id,),
        ).fetchall()
        if len(owners) != 1 or str(owners[0][0]) != plan.owner_id:
            raise EffectError("wake message has ambiguous open membership")
