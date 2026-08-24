"""Availability-first owner for one serial App Server mutation lane."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Mapping

from ..client import (
    COMPATIBLE_REQUEST_METHODS,
    MUTATING_NO_RETRY_METHODS,
    MUTATING_OWNER_MESSAGE,
    AppServerClient,
    AppServerRpcError,
)
from ..store import ObserverStore
from ..transport import TransportClosed
from ..protocol import extract_protocol_ids
from .outbox import AppServerOutbox, ClaimRejected, MutationSpec, OperationRecord, OperationState


@dataclass(frozen=True)
class MutationSubmissionResult:
    operation_id: str
    state: OperationState
    outcome: str | None
    response: Mapping[str, object] | None = None
    error: str | None = None


class SessionOwnerError(RuntimeError):
    """A single protocol session is unavailable or a mutation is not admissible."""


class AppServerSessionOwner:
    """One protocol session, one watcher, one serial async mutation sender."""

    _by_client: dict[int, "AppServerSessionOwner"] = {}

    def __init__(self, client: AppServerClient, store: ObserverStore) -> None:
        self.client = client
        self.store = store
        self.outbox = AppServerOutbox(store.connection)
        self.protocol_session_id = self._ensure_run()
        self.outbox.recover_stale_sessions(self.protocol_session_id)
        self.terminated = False
        self.incident_payload: dict[str, Any] | None = None
        self._incident = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._mutation_lane = asyncio.Lock()

    @classmethod
    def for_client(cls, client: AppServerClient, store: ObserverStore) -> "AppServerSessionOwner":
        existing = cls._by_client.get(id(client))
        if existing is not None and not existing.terminated:
            existing.start()
            return existing
        owner = cls(client, store)
        owner.start()
        cls._by_client[id(client)] = owner
        return owner

    @classmethod
    def active_watcher_count(cls) -> int:
        return sum(
            1
            for owner in cls._by_client.values()
            if owner._task is not None and not owner._task.done()
        )

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

    def start(self) -> None:
        self.client.start_reader()
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

    async def _watch(self) -> None:
        """Quarantine this session only; host/control lifecycle remains outside."""
        request_wait = asyncio.create_task(self.client.server_requests.get())
        terminal_wait = asyncio.create_task(self.client.reader_terminal.wait())
        try:
            done, pending = await asyncio.wait(
                {request_wait, terminal_wait}, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            if request_wait in done:
                payload = request_wait.result()
                reader_terminal = False
            else:
                terminal = self.client.reader_terminal_exception
                payload = {
                    "reason": "reader_terminal",
                    "error_type": type(terminal).__name__ if terminal is not None else "unknown",
                    "error": str(terminal or "reader stopped"),
                }
                reader_terminal = True
        except asyncio.CancelledError:
            for task in (request_wait, terminal_wait):
                if not task.done():
                    task.cancel()
            await asyncio.gather(request_wait, terminal_wait, return_exceptions=True)
            return
        except Exception as exc:
            payload = {"reason": type(exc).__name__}
            reader_terminal = True
        self.incident_payload = dict(payload)
        if not reader_terminal:
            ids = extract_protocol_ids(payload)
            try:
                row_id = self.store.record_server_request(
                    run_id=self.protocol_session_id,
                    server_request_id=str(ids.request_id or "server-request"),
                    method=str(ids.method or ""),
                    payload=payload,
                    thread_id=ids.thread_id,
                    turn_id=ids.turn_id,
                )
                with self.store._lock, self.store.connection:
                    self.store.connection.execute(
                        """UPDATE server_requests
                        SET handling = 'SESSION_QUARANTINE', process_terminated_at = NULL
                        WHERE server_request_row_id = ?""",
                        (row_id,),
                    )
            except Exception:
                pass
        self.terminated = True
        self._incident.set()
        self.outbox.mark_session_sending_unknown(
            self.protocol_session_id, error="protocol session quarantined"
        )
        try:
            await self.client.transport.stop()
        except Exception:
            pass

    def enqueue_mutation(self, spec: MutationSpec) -> OperationRecord:
        if self.terminated:
            raise SessionOwnerError("SESSION_UNAVAILABLE")
        if spec.protocol_session_id != self.protocol_session_id:
            raise SessionOwnerError("mutation belongs to a different protocol session")
        if spec.run_id != self.protocol_session_id:
            raise SessionOwnerError("mutation run/session identity mismatch")
        if spec.method not in MUTATING_NO_RETRY_METHODS:
            raise SessionOwnerError(f"method is not a V1 mutation: {spec.method}")
        return self.outbox.enqueue(spec)

    async def submit(self, operation_id: str) -> MutationSubmissionResult:
        if self.terminated:
            raise SessionOwnerError("SESSION_UNAVAILABLE")
        async with self._mutation_lane:
            if self.terminated:
                raise SessionOwnerError("SESSION_UNAVAILABLE")
            claim = self.outbox.claim(
                operation_id,
                protocol_session_id=self.protocol_session_id,
                target="",
                thread_id=None,
                enforce_target=False,
            )
            try:
                frozen = self.client.activate_frozen(
                    claim.rpc_request_id, claim.method, claim.wire_bytes
                )
            except Exception as exc:
                done = self.outbox.complete(
                    claim, outcome="LOCAL_REJECTED", error=type(exc).__name__
                )
                return MutationSubmissionResult(
                    operation_id, done.state, done.outcome, error=done.error
                )
            try:
                await self.client.transport.send_bytes(claim.wire_bytes)
                response = await self.client.await_frozen(frozen)
            except AppServerRpcError as exc:
                response = dict(exc.payload)
                done = self.outbox.complete(
                    claim,
                    outcome="PROVIDER_REJECTED",
                    response_raw_ref=f"run:{self.protocol_session_id}:response:{claim.rpc_request_id}",
                    error=str(exc),
                )
                return MutationSubmissionResult(
                    operation_id, done.state, done.outcome, response, done.error
                )
            except BaseException as exc:
                self.client.discard_frozen(frozen)
                try:
                    unknown = self.outbox.mark_unknown(claim, error=type(exc).__name__)
                except ClaimRejected:
                    unknown = self.outbox.get(operation_id)
                    if unknown.state is not OperationState.UNKNOWN:
                        raise
                if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                    raise
                return MutationSubmissionResult(
                    operation_id, unknown.state, unknown.outcome, error=unknown.error
                )
            try:
                done = self.outbox.complete(
                    claim,
                    outcome="OK",
                    response_raw_ref=f"run:{self.protocol_session_id}:response:{claim.rpc_request_id}",
                )
            except ClaimRejected:
                contained = self.outbox.get(operation_id)
                if contained.state is not OperationState.UNKNOWN:
                    raise
                return MutationSubmissionResult(
                    operation_id, contained.state, contained.outcome, error=contained.error
                )
            return MutationSubmissionResult(
                operation_id, done.state, done.outcome, response=response
            )

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
            raise SessionOwnerError("SESSION_UNAVAILABLE")
        return await self.client.request(method, dict(params or {}), timeout=timeout)

    async def request(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
        *,
        timeout: float | None = None,
    ) -> dict[str, object]:
        if method in MUTATING_NO_RETRY_METHODS:
            raise SessionOwnerError(MUTATING_OWNER_MESSAGE)
        return dict(await self.request_read(method, params, timeout=timeout))
