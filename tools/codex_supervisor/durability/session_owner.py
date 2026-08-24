"""One process-lifetime App Server session owner and typed send authority."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from typing import Any, Mapping

from ..client import (
    COMPATIBLE_REQUEST_METHODS,
    MUTATING_NO_RETRY_METHODS,
    MUTATING_OWNER_MESSAGE,
    AppServerClient,
    CommittedClaimCapability,
    PreparedRpcRequest,
    RetryRequired,
)
from ..protocol import extract_protocol_ids
from ..store import ObserverStore
from ..transport import TransportClosed
from .authority_kernel import (
    EphemeralCanaryPlan,
    ManagedTurnPlan,
    OwnerPlan,
    ThreadMemoryPlan,
    ThreadProvisionPlan,
    ThreadResumePlan,
    WakeBatchPlan,
    apply_typed_preclaim,
    final_authority_proof,
    prove_prepared_rpc,
    request_object,
    semantic_guard,
)
from .effects import EffectError, EffectJournal
from .models import EffectState, SUBMISSION_RESULT_STATES
from .transaction import DurabilityTransaction


@dataclass(frozen=True)
class EffectSubmissionResult:
    effect_id: str
    state: str
    response: Mapping[str, object] | None = None
    incident: Mapping[str, object] | None = None


@dataclass(frozen=True)
class SendPermit:
    """Immutable single-use proof that the exact prepared RPC was claimed."""

    effect_id: str
    prepared: PreparedRpcRequest
    capability: CommittedClaimCapability | None = None
    fallback_token: str | None = None


class SessionOwnerError(RuntimeError):
    """Raised when the session owner cannot submit or read."""


class AppServerSessionOwner:
    """One client, one watcher, and one closed-union mutation kernel."""

    _by_client: dict[int, "AppServerSessionOwner"] = {}

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
        self._send_permits: set[str] = set()

    @classmethod
    def for_client(cls, client: AppServerClient, store: ObserverStore) -> "AppServerSessionOwner":
        existing = cls._by_client.get(id(client))
        if existing is not None and existing._task is not None and not existing._task.done():
            return existing
        owner = cls(client, store)
        owner.start()
        cls._by_client[id(client)] = owner
        return owner

    @classmethod
    def active_watcher_count(cls) -> int:
        return sum(
            1
            for item in cls._by_client.values()
            if item._task is not None and not item._task.done()
        )

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
                self.journal.mark_incident(
                    effect_id,
                    evidence_ref=f"server_request:{evidence}",
                    incident=incident,
                )
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

    async def submit_managed_turn(self, plan: ManagedTurnPlan) -> EffectSubmissionResult:
        return await self._submit_plan(plan)

    async def submit_wake_batch(self, plan: WakeBatchPlan) -> EffectSubmissionResult:
        return await self._submit_plan(plan)

    async def submit_thread_provision(
        self, plan: ThreadProvisionPlan
    ) -> EffectSubmissionResult:
        return await self._submit_plan(plan)

    async def submit_thread_resume(self, plan: ThreadResumePlan) -> EffectSubmissionResult:
        return await self._submit_plan(plan)

    async def submit_thread_memory(self, plan: ThreadMemoryPlan) -> EffectSubmissionResult:
        return await self._submit_plan(plan)

    async def submit_ephemeral_canary(
        self, plan: EphemeralCanaryPlan
    ) -> EffectSubmissionResult:
        return await self._submit_plan(plan)

    async def _submit_plan(self, plan: OwnerPlan) -> EffectSubmissionResult:
        from ..client import UnexpectedServerRequest

        if self.terminated:
            raise UnexpectedServerRequest(self.incident_payload or {})
        with self.store._lock, DurabilityTransaction(self.store.connection):
            current = self.journal.get(plan.effect_id)
            if current.state != EffectState.PREPARED.value:
                raise SessionOwnerError(
                    f"effect {plan.effect_id} is {current.state}; crossed effects are never submitted again"
                )
        async with self._lock:
            return await self._submit_locked(plan)

    def _before_final_authority_proof(self, plan: OwnerPlan) -> None:
        """Result-blind test seam before the mandatory final reproof."""

    def _authorize_and_claim(
        self,
        plan: OwnerPlan,
        prepared: PreparedRpcRequest,
        run_id: str,
    ) -> SendPermit:
        prove_prepared_rpc(plan, prepared)
        guard = semantic_guard(self.store, plan)
        try:
            with guard:
                with self.store._lock, DurabilityTransaction(self.store.connection):
                    apply_typed_preclaim(self.store.connection, plan)
                    self._before_final_authority_proof(plan)
                    final_authority_proof(self.store.connection, plan, run_id=run_id)
                    # From here through commit there is no caller code and no
                    # owner/aggregate mutation, only raw/RPC/effect claim writes.
                    self.store._record_authorized_effect_claim(
                        effect_id=plan.effect_id,
                        run_id=run_id,
                        method=plan.method,
                        payload=dict(prepared.payload),
                        params=dict(prepared.params),
                        request_class=prepared.request_class.value,
                    )
        except BaseException:
            crossed = False
            try:
                crossed = self.journal.get(plan.effect_id).state != EffectState.PREPARED.value
            except BaseException:
                crossed = True
            if crossed:
                try:
                    current = self.journal.get(plan.effect_id)
                    if current.state == EffectState.WRITE_STARTED.value:
                        self.journal.mark_uncertain(
                            plan.effect_id, reason="outer_semantic_commit_failed"
                        )
                except BaseException:
                    pass
            raise
        issuer = getattr(self.client, "_issue_committed_claim", None)
        if callable(issuer):
            capability = issuer(prepared, effect_id=plan.effect_id)
            return SendPermit(
                effect_id=plan.effect_id,
                prepared=prepared,
                capability=capability,
            )
        # Test doubles do not own a real transport boundary.  Keep their
        # legacy local permit registry so cleanup assertions remain explicit.
        token = f"permit_{uuid.uuid4().hex}"
        self._send_permits.add(token)
        return SendPermit(
            effect_id=plan.effect_id,
            prepared=prepared,
            fallback_token=token,
        )

    async def _consume_send_permit(self, permit: SendPermit) -> None:
        if permit.capability is not None:
            await self.client.send_prepared(permit.prepared, permit.capability)
            return
        token = permit.fallback_token
        if token is None or token not in self._send_permits:
            raise SessionOwnerError("send permit is unknown or already consumed")
        self._send_permits.remove(token)
        await self.client.send_prepared(permit.prepared)

    async def _submit_locked(self, plan: OwnerPlan) -> EffectSubmissionResult:
        from ..client import UnexpectedServerRequest

        self._open_effect_ids.add(plan.effect_id)
        prepared: PreparedRpcRequest | None = None
        permit: SendPermit | None = None
        try:
            prepared = self.client.prepare_request(plan.method, request_object(plan))
            permit = self._authorize_and_claim(plan, prepared, self._ensure_run())
        except BaseException:
            crossed = False
            try:
                crossed = self.journal.get(plan.effect_id).state != EffectState.PREPARED.value
            except BaseException:
                crossed = True
            if prepared is not None:
                self.client.discard_prepared(prepared)
            if not crossed:
                self._open_effect_ids.discard(plan.effect_id)
            raise
        assert prepared is not None and permit is not None
        try:
            await self._consume_send_permit(permit)
        except BaseException:
            try:
                current = self.journal.get(plan.effect_id)
                if current.state == EffectState.WRITE_STARTED.value:
                    self.journal.mark_uncertain(plan.effect_id, reason="send_failed")
            except BaseException:
                pass
            raise
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
            self._mark_open_effects_incident(
                self.incident_payload or {"reason": "server_request"}
            )
            raise UnexpectedServerRequest(self.incident_payload or {})
        await asyncio.sleep(0)
        if self.terminated or self._incident.is_set():
            self._mark_open_effects_incident(
                self.incident_payload or {"reason": "server_request"}
            )
            raise UnexpectedServerRequest(self.incident_payload or {})
        try:
            response = send.result()
        except RetryRequired:
            self.journal.mark_uncertain(plan.effect_id, reason="overload")
            raise
        except (TimeoutError, asyncio.TimeoutError, TransportClosed):
            updated = self.journal.mark_uncertain(plan.effect_id, reason="timeout")
            return EffectSubmissionResult(
                plan.effect_id, updated.state, None, {"reason": "timeout"}
            )
        except Exception:
            if self.terminated or self._incident.is_set():
                self._mark_open_effects_incident(
                    self.incident_payload or {"reason": "server_request"}
                )
                raise UnexpectedServerRequest(self.incident_payload or {})
            self.journal.mark_uncertain(plan.effect_id, reason="transport")
            raise
        current = self.journal.get(plan.effect_id)
        if current.state == EffectState.INCIDENT.value:
            raise UnexpectedServerRequest(self.incident_payload or {})
        ids = extract_protocol_ids(response)
        inner = response.get("result") if isinstance(response.get("result"), Mapping) else {}
        thread = (
            inner.get("thread")
            if isinstance(inner, Mapping) and isinstance(inner.get("thread"), Mapping)
            else {}
        )
        turn = (
            inner.get("turn")
            if isinstance(inner, Mapping) and isinstance(inner.get("turn"), Mapping)
            else {}
        )
        observed = self.journal.observe_response(
            plan.effect_id,
            response=response,
            thread_id=ids.thread_id or (str(thread.get("id")) if thread else None),
            turn_id=ids.turn_id or (str(turn.get("id")) if turn else None),
        )
        await asyncio.sleep(0)
        if self.terminated or self._incident.is_set():
            self._mark_open_effects_incident(
                self.incident_payload or {"reason": "server_request"}
            )
            raise UnexpectedServerRequest(self.incident_payload or {})
        if observed.state not in SUBMISSION_RESULT_STATES:
            raise SessionOwnerError(f"unexpected effect submission state {observed.state}")
        return EffectSubmissionResult(plan.effect_id, observed.state, response, None)

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
