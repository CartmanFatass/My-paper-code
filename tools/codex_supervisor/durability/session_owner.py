"""One process-lifetime App Server session owner."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Mapping

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
    ) -> EffectSubmissionResult:
        from ..client import UnexpectedServerRequest

        if self.terminated:
            raise UnexpectedServerRequest(self.incident_payload or {})
        record = self.journal.get(effect_id)
        if record.state != EffectState.PREPARED.value:
            raise SessionOwnerError(
                f"effect {effect_id} is {record.state}; WRITE_STARTED or later is never automatically submitted again"
            )
        async with self._lock:
            return await self._submit_locked(record, extra_transitions, extra_hooks)

    async def _submit_locked(
        self,
        record: EffectRecord,
        extra_transitions: list[Any] | None = None,
        extra_hooks: list[Any] | None = None,
    ) -> EffectSubmissionResult:
        from ..client import UnexpectedServerRequest

        self._open_effect_ids.add(record.effect_id)
        prepared = self.client.prepare_request(record.method, record.request)
        try:
            self.store.record_effect_write_start(
                effect_id=record.effect_id,
                run_id=self._ensure_run(),
                method=record.method,
                payload=dict(prepared.payload),
                params=dict(prepared.params),
                request_class=prepared.request_class.value,
                extra_transitions=extra_transitions,
                extra_hooks=extra_hooks,
            )
        except Exception:
            discard = getattr(self.client, "discard_prepared", None)
            if callable(discard):
                discard(prepared)
            self._open_effect_ids.discard(record.effect_id)
            raise
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
