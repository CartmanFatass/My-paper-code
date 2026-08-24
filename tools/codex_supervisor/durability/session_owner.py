"""One process-lifetime App Server session owner."""

from __future__ import annotations

import asyncio
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any, Callable, ContextManager, Mapping

from ..client import (
    COMPATIBLE_REQUEST_METHODS,
    MUTATING_NO_RETRY_METHODS,
    MUTATING_OWNER_MESSAGE,
    AppServerClient,
    RetryRequired,
)
from ..protocol import extract_protocol_ids
from ..store import ObserverStore
from ..transport import TransportClosed
from .effects import EffectError, EffectJournal, EffectRecord
from .models import EffectState, SUBMISSION_RESULT_STATES


@dataclass(frozen=True)
class EffectSubmissionResult:
    effect_id: str
    state: str
    response: Mapping[str, object] | None = None
    incident: Mapping[str, object] | None = None


class SessionOwnerError(RuntimeError):
    """Raised when the session owner cannot submit or read."""


class AppServerSessionOwner:
    """One client, one watcher, one mutating submit path."""

    _by_client: dict[int, AppServerSessionOwner] = {}

    def __init__(self, client: AppServerClient, store: ObserverStore) -> None:
        self.client = client
        self.store = store
        self.journal = EffectJournal(store.connection)
        self.terminated = False
        self.incident_payload: dict[str, Any] | None = None
        self._incident = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()
        self._open_effect_ids: set[str] = set()

    @classmethod
    def for_client(cls, client: AppServerClient, store: ObserverStore) -> AppServerSessionOwner:
        existing = cls._by_client.get(id(client))
        if existing is not None and existing._task is not None and not existing._task.done():
            return existing
        owner = cls(client, store)
        owner.start()
        cls._by_client[id(client)] = owner
        return owner

    @classmethod
    def active_watcher_count(cls) -> int:
        return sum(1 for item in cls._by_client.values() if item._task is not None and not item._task.done())

    def start(self) -> None:
        start_reader = getattr(self.client, "start_reader", None)
        if callable(start_reader):
            start_reader()
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._watch())

    async def close(self) -> None:
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
        self._by_client.pop(id(self.client), None)

    def _ensure_run(self) -> str:
        row = self.store.connection.execute(
            "SELECT run_id FROM observer_runs ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        if row is not None:
            return str(row[0])
        return self.store.start_run(
            codex_binary="unknown",
            codex_version="unknown",
            client_name="hmasd-session-owner",
            process_id=None,
        )

    async def _watch(self) -> None:
        from ..session_guard import persist_server_request, terminate_transport

        try:
            queue = getattr(self.client, "server_requests", None)
            if queue is None:
                return
            payload = await queue.get()
        except Exception:
            self.terminated = True
            self._incident.set()
            return
        try:
            persist_server_request(self.store, payload)
            self._mark_open_effects_incident(payload)
        except Exception:
            self._mark_open_effects_incident(payload)
        self.incident_payload = dict(payload)
        self.terminated = True
        self._incident.set()
        await terminate_transport(self.client)

    def _mark_open_effects_incident(self, payload: Mapping[str, Any]) -> None:
        from ..session_guard import mark_related_incidents

        mark_related_incidents(self.store, payload)
        evidence = str(payload.get("id") or "server_request")
        incident = {"reason": "server_request", "server_request_id": evidence}
        for effect_id in list(self._open_effect_ids):
            try:
                record = self.journal.get(effect_id)
            except EffectError:
                continue
            if record.state in {
                EffectState.PREPARED.value,
                EffectState.EFFECT_CONFIRMED.value,
                EffectState.CANCELLED_BEFORE_WRITE.value,
                EffectState.INCIDENT.value,
                EffectState.OPERATOR_RESOLVED.value,
            }:
                continue
            try:
                self.journal.mark_incident(effect_id, evidence_ref=f"server_request:{evidence}", incident=incident)
            except EffectError:
                continue

    async def request_read(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
        *,
        timeout: float | None = None,
    ) -> Mapping[str, object]:
        if method not in COMPATIBLE_REQUEST_METHODS:
            raise SessionOwnerError(f"read path does not allow {method}")
        if self.terminated:
            from ..client import UnexpectedServerRequest

            raise UnexpectedServerRequest(self.incident_payload or {})
        send = asyncio.create_task(self.client.request(method, dict(params or {}), timeout=timeout))
        incident = asyncio.create_task(self._incident.wait())
        done, pending = await asyncio.wait({send, incident}, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            if task is incident:
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
        if send in done:
            await asyncio.sleep(0)
            if self.terminated or self._incident.is_set():
                from ..client import UnexpectedServerRequest

                raise UnexpectedServerRequest(self.incident_payload or {})
            try:
                return send.result()
            except Exception:
                if self.terminated or self._incident.is_set():
                    from ..client import UnexpectedServerRequest

                    raise UnexpectedServerRequest(self.incident_payload or {})
                raise
        send.cancel()
        try:
            await send
        except (asyncio.CancelledError, Exception):
            pass
        from ..client import UnexpectedServerRequest

        raise UnexpectedServerRequest(self.incident_payload or {})

    def classify_submission(self, result: EffectSubmissionResult) -> str:
        if result.state == EffectState.RESPONSE_OBSERVED.value:
            return "observed"
        if result.state == EffectState.SUBMISSION_UNCERTAIN.value:
            return "uncertain"
        if result.state == EffectState.INCIDENT.value:
            return "incident"
        raise SessionOwnerError(f"unexpected effect submission state {result.state}")

    def release_open_effect(self, effect_id: str) -> None:
        self._open_effect_ids.discard(effect_id)

    async def submit_effect(
        self,
        effect_id: str,
        extra_transitions: list[Any] | None = None,
        extra_hooks: list[Any] | None = None,
        request_override: Mapping[str, object] | None = None,
        pre_write_guard: Callable[[], ContextManager[object]] | None = None,
    ) -> EffectSubmissionResult:
        from ..client import UnexpectedServerRequest

        if self.terminated:
            raise UnexpectedServerRequest(self.incident_payload or {})
        from .transaction import DurabilityTransaction

        with self.store._lock, DurabilityTransaction(self.store.connection):
            record = self.journal.get(effect_id)
            if record.state != EffectState.PREPARED.value:
                raise SessionOwnerError(
                    f"effect {effect_id} is {record.state}; WRITE_STARTED or later is never automatically submitted again"
                )
            self._require_owner_submittable(record)
        async with self._lock:
            return await self._submit_locked(
                record,
                extra_transitions,
                extra_hooks,
                request_override,
                pre_write_guard,
            )

    def _require_owner_submittable(
        self, record, *, run_id: str | None = None
    ) -> None:
        from .effects import (
            require_exact_canary_submission_ownership,
            require_exact_open_effect_ownership,
        )

        # One canary owner intentionally performs thread/start followed by
        # turn/start.  Its already RESPONSE_OBSERVED first effect is historical
        # evidence, not another submittable write.  All states that could still
        # write, be retried, or require no-resend containment remain globally
        # enumerated for the final proof.
        if record.owner_kind == "EPHEMERAL_CANARY":
            try:
                require_exact_canary_submission_ownership(
                    self.store.connection,
                    record,
                    run_id=run_id,
                    validate_contract=run_id is not None,
                )
            except EffectError as exc:
                raise SessionOwnerError(
                    "canary predecessor ownership is not exact; cannot submit"
                ) from exc
            return
        try:
            require_exact_open_effect_ownership(
                self.store.connection,
                owner_kind=record.owner_kind,
                owner_id=record.owner_id,
                effect_id=record.effect_id,
                binding_id=record.binding_id,
                expected_states=(EffectState.PREPARED.value,),
            )
        except EffectError as exc:
            raise SessionOwnerError(
                "effect owner PREPARED ownership is not exact; cannot submit"
            ) from exc
        if record.owner_kind == "MANAGED_TURN":
            row = self.store.connection.execute(
                "SELECT submission_state FROM managed_turn_intents WHERE turn_intent_id = ?",
                (record.owner_id,),
            ).fetchone()
            if row is None:
                raise SessionOwnerError("linked managed turn is missing; cannot submit")
            if str(row[0]) != "PREPARED":
                raise SessionOwnerError("linked managed turn is not PREPARED; cannot submit")
            return
        if record.owner_kind == "WAKE_BATCH":
            from .effects import (
                require_exact_prepared_wake_ownership,
                require_exact_wake_ownership,
            )

            try:
                proof = (
                    require_exact_prepared_wake_ownership
                    if run_id is not None
                    else require_exact_wake_ownership
                )
                proof(
                    self.store.connection, record.owner_id,
                    effect_id=record.effect_id, binding_id=record.binding_id,
                )
            except EffectError as exc:
                raise SessionOwnerError(
                    "linked wake is missing or ownership is not exact; cannot submit"
                ) from exc
            return
        if record.owner_kind in {"THREAD_PROVISION", "THREAD_RESUME", "THREAD_MEMORY"}:
            if record.owner_kind == "THREAD_RESUME":
                from .effects import require_exact_open_effect_ownership

                try:
                    require_exact_open_effect_ownership(
                        self.store.connection,
                        owner_kind="THREAD_RESUME",
                        owner_id=record.owner_id,
                        effect_id=record.effect_id,
                        binding_id=record.binding_id,
                        expected_states=(EffectState.PREPARED.value,),
                    )
                except EffectError as exc:
                    raise SessionOwnerError(
                        "linked resume effect ownership is not exact; cannot submit"
                    ) from exc
            binding_id = record.binding_id or record.owner_id
            row = self.store.connection.execute(
                """SELECT binding_state, prepared_context_trusted
                FROM managed_actor_bindings WHERE binding_id = ?""",
                (binding_id,),
            ).fetchone()
            if row is None:
                raise SessionOwnerError("linked binding is missing; cannot submit")
            if int(row["prepared_context_trusted"] or 0) != 1:
                raise SessionOwnerError("linked binding has no trusted prepared-context provenance")
            allowed = {"PREPARED"} if record.owner_kind == "THREAD_PROVISION" else {
                "PREPARED",
                "THREAD_CREATED",
                "VERIFICATION_REQUIRED",
                "ACTIVE",
            }
            if str(row[0]) not in allowed:
                raise SessionOwnerError("linked binding cannot submit this effect")
            return
        raise SessionOwnerError(f"effect owner {record.owner_kind} cannot be submitted")

    async def _submit_locked(
        self,
        record: EffectRecord,
        extra_transitions: list[Any] | None = None,
        extra_hooks: list[Any] | None = None,
        request_override: Mapping[str, object] | None = None,
        pre_write_guard: Callable[[], ContextManager[object]] | None = None,
    ) -> EffectSubmissionResult:
        from ..client import UnexpectedServerRequest

        self._open_effect_ids.add(record.effect_id)
        request = dict(request_override) if request_override is not None else dict(record.request)
        prepared = None
        try:
            prepared = self.client.prepare_request(record.method, request)
            run_id = self._ensure_run()
            guard = pre_write_guard() if pre_write_guard is not None else nullcontext()
            with guard:
                self.store.record_effect_write_start(
                    effect_id=record.effect_id,
                    run_id=run_id,
                    method=record.method,
                    payload=dict(prepared.payload),
                    params=dict(prepared.params),
                    request_class=prepared.request_class.value,
                    extra_transitions=extra_transitions,
                    extra_hooks=extra_hooks,
                    request_override=request_override,
                    final_owner_guard=lambda _connection: self._require_owner_submittable(
                        record, run_id=run_id
                    ),
                )
        except asyncio.CancelledError:
            try:
                still_prepared = (
                    self.journal.get(record.effect_id).state == EffectState.PREPARED.value
                )
            except EffectError:
                still_prepared = False
            if still_prepared:
                if prepared is not None:
                    discard = getattr(self.client, "discard_prepared", None)
                    if callable(discard):
                        discard(prepared)
                self._open_effect_ids.discard(record.effect_id)
            raise
        except Exception:
            if prepared is not None:
                discard = getattr(self.client, "discard_prepared", None)
                if callable(discard):
                    discard(prepared)
            self._open_effect_ids.discard(record.effect_id)
            raise
        assert prepared is not None
        await self.client.send_prepared(prepared)
        send = asyncio.create_task(self.client.await_prepared(prepared))
        incident = asyncio.create_task(self._incident.wait())
        done, pending = await asyncio.wait({send, incident}, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            if task is incident:
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
        if send not in done:
            send.cancel()
            try:
                await send
            except (asyncio.CancelledError, Exception):
                pass
            self._mark_open_effects_incident(self.incident_payload or {"reason": "server_request"})
            raise UnexpectedServerRequest(self.incident_payload or {})
        await asyncio.sleep(0)
        if self.terminated or self._incident.is_set():
            self._mark_open_effects_incident(self.incident_payload or {"reason": "server_request"})
            raise UnexpectedServerRequest(self.incident_payload or {})
        try:
            response = send.result()
        except RetryRequired:
            self.journal.mark_uncertain(record.effect_id, reason="overload")
            raise
        except (TimeoutError, asyncio.TimeoutError, TransportClosed):
            updated = self.journal.mark_uncertain(record.effect_id, reason="timeout")
            return EffectSubmissionResult(record.effect_id, updated.state, None, {"reason": "timeout"})
        except Exception:
            if self.terminated or self._incident.is_set():
                self._mark_open_effects_incident(self.incident_payload or {"reason": "server_request"})
                raise UnexpectedServerRequest(self.incident_payload or {})
            self.journal.mark_uncertain(record.effect_id, reason="transport")
            raise
        current = self.journal.get(record.effect_id)
        if current.state == EffectState.INCIDENT.value:
            raise UnexpectedServerRequest(self.incident_payload or {})
        ids = extract_protocol_ids(response)
        inner = response.get("result") if isinstance(response.get("result"), Mapping) else {}
        thread = inner.get("thread") if isinstance(inner, Mapping) and isinstance(inner.get("thread"), Mapping) else {}
        turn = inner.get("turn") if isinstance(inner, Mapping) and isinstance(inner.get("turn"), Mapping) else {}
        observed = self.journal.observe_response(
            record.effect_id,
            response=response,
            thread_id=ids.thread_id or (str(thread.get("id")) if thread else None),
            turn_id=ids.turn_id or (str(turn.get("id")) if turn else None),
        )
        await asyncio.sleep(0)
        if self.terminated or self._incident.is_set():
            self._mark_open_effects_incident(self.incident_payload or {"reason": "server_request"})
            raise UnexpectedServerRequest(self.incident_payload or {})
        if observed.state not in SUBMISSION_RESULT_STATES:
            raise SessionOwnerError(f"unexpected effect submission state {observed.state}")
        return EffectSubmissionResult(record.effect_id, observed.state, response, None)

    async def request(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
        *,
        timeout: float | None = None,
    ) -> dict[str, object]:
        if method in MUTATING_NO_RETRY_METHODS:
            raise SessionOwnerError(MUTATING_OWNER_MESSAGE)
        result = await self.request_read(method, params, timeout=timeout)
        return dict(result)
