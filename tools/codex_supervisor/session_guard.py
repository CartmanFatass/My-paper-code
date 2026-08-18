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
        ids=ids if ids.method else ProtocolIds(str(payload.get("id") or ""), str(payload.get("method") or ""), None, None, None),
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


class SessionGuard:
    def __init__(
        self,
        client: AppServerClient,
        store: ObserverStore,
        *,
        on_incident: Callable[[Mapping[str, Any]], None] | None = None,
    ) -> None:
        self.client = client
        self.store = store
        self.on_incident = on_incident

    async def request(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
        *,
        timeout: float | None = None,
    ) -> dict[str, object]:
        watch = asyncio.create_task(self.client.server_requests.get())
        send = asyncio.create_task(self.client.request(method, params, timeout=timeout))
        done, pending = await asyncio.wait({watch, send}, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        if watch in done and not watch.cancelled():
            payload = watch.result()
            persist_server_request(self.store, payload)
            if self.on_incident is not None:
                self.on_incident(payload)
            await terminate_transport(self.client)
            raise UnexpectedServerRequest(payload)
        try:
            return send.result()
        except asyncio.CancelledError as exc:
            raise TransportClosed("guarded request cancelled") from exc
