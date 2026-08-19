"""Fail-safe around every managed App Server mutation."""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Mapping

from .client import AppServerClient, UnexpectedServerRequest
from .models import ProtocolIds, RpcShape
from .protocol import extract_protocol_ids
from .store import ObserverStore
from .transport import TransportClosed


class SessionGuardError(RuntimeError):
    """Raised when a guarded App Server session must stop."""


def _ensure_run(store: ObserverStore) -> str:
    row = store.connection.execute(
        "SELECT run_id FROM observer_runs ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    if row is not None:
        return str(row[0])
    return store.start_run(
        codex_binary="unknown",
        codex_version="unknown",
        client_name="hmasd-session-guard",
        process_id=None,
    )


def persist_server_request(store: ObserverStore, payload: Mapping[str, Any]) -> str:
    run_id = _ensure_run(store)
    ids = extract_protocol_ids(payload)
    request_id = str(ids.request_id or payload.get("id") or "")
    already = None
    if request_id:
        already = store.connection.execute(
            """SELECT 1 FROM raw_messages
            WHERE run_id = ? AND request_id = ?""",
            (run_id, request_id),
        ).fetchone()
    if already is None:
        store.record_raw_message(
            run_id=run_id,
            direction="stdout",
            transport_seq=int(
                store.connection.execute(
                    "SELECT COALESCE(MAX(transport_seq), 0) + 1 FROM raw_messages WHERE run_id = ? AND direction = 'stdout'",
                    (run_id,),
                ).fetchone()[0]
            ),
            rpc_shape=RpcShape.REQUEST,
            ids=ids if ids.method else ProtocolIds(request_id, str(payload.get("method") or ""), None, None, None),
            payload=payload,
        )
    return store.record_server_request(
        run_id=run_id,
        server_request_id=str(ids.request_id or payload.get("id") or ""),
        method=str(ids.method or payload.get("method") or ""),
        payload=payload,
        thread_id=ids.thread_id,
        turn_id=ids.turn_id,
    )


async def terminate_transport(client: AppServerClient) -> None:
    transport = getattr(client, "transport", None)
    if transport is not None and hasattr(transport, "stop"):
        await transport.stop()


def mark_related_incidents(store: ObserverStore, payload: Mapping[str, Any]) -> None:
    ids = extract_protocol_ids(payload)
    thread_id = ids.thread_id
    turn_id = ids.turn_id
    incident = '{"reason":"server_request"}'
    turn_sql = """UPDATE managed_turn_intents
        SET submission_state = 'INCIDENT', incident_json = ?
        WHERE submission_state IN ('SUBMITTING', 'SUBMITTED', 'SUBMISSION_UNCERTAIN', 'OBSERVED')"""
    turn_params: list[object] = [incident]
    batch_sql = """UPDATE wake_batches
        SET state = 'INCIDENT', incident_json = ?
        WHERE state IN ('SUBMITTING', 'SUBMITTED', 'SUBMISSION_UNCERTAIN', 'ACTIVE')"""
    batch_params: list[object] = [incident]
    if thread_id or turn_id:
        clauses = []
        batch_clauses = []
        if thread_id:
            clauses.append("app_server_thread_id = ?")
            batch_clauses.append("thread_id = ?")
            turn_params.append(thread_id)
            batch_params.append(thread_id)
        if turn_id:
            clauses.append("app_server_turn_id = ?")
            batch_clauses.append("app_server_turn_id = ?")
            turn_params.append(turn_id)
            batch_params.append(turn_id)
        turn_sql += " AND (" + " OR ".join(clauses) + ")"
        batch_sql += " AND (" + " OR ".join(batch_clauses) + ")"
    with store._lock, store.connection:
        store.connection.execute(turn_sql, turn_params)
        store.connection.execute(batch_sql, batch_params)
        store.connection.execute(
            """UPDATE mutation_intents
            SET state = 'INCIDENT', request_json = ?, updated_at = datetime('now')
            WHERE state IN ('SUBMITTING', 'SUBMISSION_UNCERTAIN', 'SUBMITTED', 'SUBMITTED_UNRECONCILED')""",
            (incident,),
        )


class ManagedAppServerSession:
    """Compatibility adapter around AppServerSessionOwner. Do not start a second watcher."""

    def __init__(self, owner: Any) -> None:
        self.owner = owner
        self.client = owner.client
        self.store = owner.store

    @property
    def terminated(self) -> bool:
        return bool(self.owner.terminated)

    @property
    def incident_payload(self) -> dict[str, Any] | None:
        return self.owner.incident_payload

    @property
    def _task(self) -> asyncio.Task[None] | None:
        return self.owner._task

    @classmethod
    def for_client(cls, client: AppServerClient, store: ObserverStore) -> ManagedAppServerSession:
        from .durability.session_owner import AppServerSessionOwner

        return cls(AppServerSessionOwner.for_client(client, store))

    @classmethod
    def active_watcher_count(cls) -> int:
        from .durability.session_owner import AppServerSessionOwner

        return AppServerSessionOwner.active_watcher_count()

    def start(self) -> None:
        self.owner.start()

    def close(self) -> None:
        self.owner._by_client.pop(id(self.client), None)
        if self.owner._task is not None and not self.owner._task.done():
            self.owner._task.cancel()

    async def request(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
        *,
        timeout: float | None = None,
    ) -> dict[str, object]:
        return await self.owner.request(method, params, timeout=timeout)


class SessionGuard:
    def __init__(
        self,
        client: AppServerClient,
        store: ObserverStore,
        *,
        on_incident: Callable[[Mapping[str, Any]], None] | None = None,
    ) -> None:
        from .durability.session_owner import AppServerSessionOwner

        self.client = client
        self.store = store
        self.on_incident = on_incident
        self.owner = AppServerSessionOwner.for_client(client, store)
        self.session = ManagedAppServerSession(self.owner)

    async def request(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
        *,
        timeout: float | None = None,
    ) -> dict[str, object]:
        try:
            return await self.owner.request(method, params, timeout=timeout)
        except UnexpectedServerRequest as exc:
            if self.on_incident is not None:
                self.on_incident(exc.payload)
            raise
        except asyncio.CancelledError as exc:
            raise TransportClosed("guarded request cancelled") from exc

    async def submit_effect(self, effect_id: str):
        try:
            return await self.owner.submit_effect(effect_id)
        except UnexpectedServerRequest as exc:
            if self.on_incident is not None:
                self.on_incident(exc.payload)
            raise
