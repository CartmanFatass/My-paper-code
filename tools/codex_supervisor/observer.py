"""Read-only observer service plus one explicit ephemeral canary."""

from __future__ import annotations

import asyncio
import inspect
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Mapping

from .canary_contract import (
    CANARY_TEXT,
    canonical_canary_scratch,
    canonical_canary_thread_start_request,
    canonical_canary_turn_start_request,
)
from .client import (
    MUTATING_NO_RETRY_METHODS,
    MUTATING_OWNER_MESSAGE,
    AppServerClient,
    UnexpectedServerRequest,
    request_class_for,
)
from .codex_binary import read_codex_version
from .models import (
    CanaryResult,
    EndKind,
    NormalizedEvent,
    ObserverConfig,
    ObserverRunResult,
    ProtocolIds,
    RpcShape,
)
from .normalizer import apply_normalized_event, normalize_message, thread_snapshot_fields
from .protocol import classify_rpc_message, decode_jsonl_line, encode_jsonl, extract_protocol_ids
from .runtime_profiles import RuntimeProfile
from .session_guard import ManagedAppServerSession
from .store import ObserverStore
from .transport import AppServerTransport, TransportClosed, TransportMessage

if TYPE_CHECKING:
    from .host_control import HostControlChannel

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ObserverService:
    def __init__(
        self,
        config: ObserverConfig,
        *,
        binary: Path,
        store: ObserverStore,
        process_cwd: Path | None = None,
        outbound_hook: Callable[[dict[str, Any]], None] | None = None,
        extra_env: Mapping[str, str] | None = None,
        stdin_close_timeout: float = 5.0,
        terminate_timeout: float = 5.0,
    ) -> None:
        self.config = config
        self.binary = Path(binary)
        self.store = store
        self.process_cwd = Path(process_cwd or config.runtime_home)
        self.outbound_hook = outbound_hook
        self.extra_env = dict(extra_env or {})
        self.stdin_close_timeout = stdin_close_timeout
        self.terminate_timeout = terminate_timeout
        self.run_id: str | None = None
        self.transport: AppServerTransport | None = None
        self.client: AppServerClient | None = None
        self._stdin_seq = 0
        self._local_seq = 0
        self._version = ""
        self._end_kind = EndKind.NORMAL.value
        self._stopped = False
        self.session: ManagedAppServerSession | None = None

    async def start(self) -> None:
        self.store.recover_incomplete_runs()
        self._version = read_codex_version(self.binary)
        self.run_id = self.store.start_run(
            codex_binary=str(self.binary),
            codex_version=self._version,
            client_name=self.config.client_name,
            process_id=None,
        )
        stderr_path = self.store.raw_dir(self.run_id) / "stderr.log"
        self.transport = AppServerTransport(
            self.binary,
            self.config,
            self.process_cwd,
            stderr_path,
            stdin_close_timeout=self.stdin_close_timeout,
            terminate_timeout=self.terminate_timeout,
            extra_env=self.extra_env,
        )
        await self.transport.start()
        with self.store.connection:
            self.store.connection.execute(
                "UPDATE observer_runs SET process_id = ? WHERE run_id = ?",
                (self.transport.process_id, self.run_id),
            )
        self.client = AppServerClient(
            self.transport,
            self.config,
            on_inbound=self._on_inbound,
        )
        original_send = self.transport.send
        original_send_bytes = self.transport.send_bytes

        async def recorded_send(message: dict[str, Any]) -> bytes:
            return await self._record_and_send(original_send_bytes, message)

        async def exact_mutation_send(exact_jsonl: bytes) -> bytes:
            message = decode_jsonl_line(exact_jsonl, self.config.max_jsonl_line_bytes)
            if self.outbound_hook is not None:
                self.outbound_hook(message)
            return await original_send_bytes(exact_jsonl)

        self.transport.send = recorded_send  # type: ignore[method-assign]
        self.transport.send_bytes = exact_mutation_send  # type: ignore[method-assign]
        self.client.start_reader()
        self.session = ManagedAppServerSession.for_client(self.client, self.store)
        self.record_local_event("APP_SERVER_PROCESS_STARTED_OBSERVED", {"pid": self.transport.process_id})

    async def _record_and_send(self, original_send: Any, message: dict[str, Any]) -> bytes:
        assert self.run_id is not None
        encoded = encode_jsonl(message)
        self._stdin_seq += 1
        self.store.append_raw_file(self.run_id, "stdin.jsonl", encoded)
        already = self.store.connection.execute(
            "SELECT 1 FROM rpc_requests WHERE run_id = ? AND client_request_id = ?",
            (self.run_id, str(message.get("id") or "")),
        ).fetchone()
        if already is not None:
            if self.outbound_hook is not None:
                self.outbound_hook(message)
            return await original_send(message)
        self.store.record_raw_message(
            run_id=self.run_id,
            direction="stdin",
            transport_seq=self._stdin_seq,
            rpc_shape=classify_rpc_message(message),
            ids=extract_protocol_ids(message),
            payload=message,
        )
        if self.outbound_hook is not None:
            self.outbound_hook(message)
        if message.get("method") and message.get("id") is not None:
            self.store.record_request_sent(
                run_id=self.run_id,
                client_request_id=str(message["id"]),
                method=str(message["method"]),
                request_class=request_class_for(str(message["method"])).value,
                params=message.get("params") if isinstance(message.get("params"), dict) else {},
                attempt_count=1,
            )
        return await original_send(encoded)

    def record_local_event(self, kind: str, params: dict[str, Any]) -> int:
        assert self.run_id is not None
        self._local_seq += 1
        seq = self.store.record_raw_message(
            run_id=self.run_id,
            direction="local",
            transport_seq=self._local_seq,
            rpc_shape=RpcShape.NOTIFICATION,
            ids=ProtocolIds(None, kind, params.get("thread_id"), None, None),
            payload={"method": kind, "params": params},
        )
        event = NormalizedEvent(kind, seq, self.run_id, params.get("thread_id"), None, None, None, params, _now())
        return apply_normalized_event(self.store, event)

    def _apply_thread_objects(self, payload: Mapping[str, Any], raw_seq: int, observed_at: str) -> None:
        result = payload.get("result") if isinstance(payload.get("result"), Mapping) else None
        if not isinstance(result, Mapping):
            return
        threads: list[Mapping[str, Any]] = []
        if isinstance(result.get("thread"), Mapping):
            threads.append(result["thread"])
        data = result.get("data")
        if isinstance(data, list):
            threads.extend(item for item in data if isinstance(item, Mapping) and item.get("id"))
        for thread in threads:
            thread_id = thread.get("id")
            if not thread_id:
                continue
            fields = thread_snapshot_fields(thread)
            self.store.upsert_thread_snapshot(
                thread_id=str(thread_id),
                status_type=fields.get("status_type"),
                preview_present=fields.get("preview_present"),
                preview_byte_length=fields.get("preview_byte_length"),
                ephemeral=fields.get("ephemeral"),
                path=fields.get("path"),
                last_event_seq=raw_seq,
                observed_at=observed_at,
            )

    def _on_inbound(self, message: TransportMessage) -> None:
        assert self.run_id is not None
        encoded = encode_jsonl(dict(message.payload))
        self.store.append_raw_file(self.run_id, "stdout.jsonl", encoded)
        ids = extract_protocol_ids(message.payload)
        seq = self.store.record_raw_message(
            run_id=self.run_id,
            direction="stdout",
            transport_seq=message.transport_seq,
            rpc_shape=classify_rpc_message(message.payload),
            ids=ids,
            payload=message.payload,
            observed_at=message.observed_at,
        )
        if ids.request_id and classify_rpc_message(message.payload) is RpcShape.RESPONSE:
            error = message.payload.get("error") if isinstance(message.payload.get("error"), Mapping) else None
            self.store.record_request_completed(
                run_id=self.run_id,
                client_request_id=str(ids.request_id),
                outcome="ERROR" if error is not None else "OK",
                response=message.payload,
                error_code=error.get("code") if isinstance(error, Mapping) else None,
            )
        event = normalize_message(message.payload, seq, self.run_id, message.observed_at)
        if event is not None:
            apply_normalized_event(self.store, event)
        self._apply_thread_objects(message.payload, seq, message.observed_at)

    def _raise_if_incident(self) -> None:
        if self.session is not None and self.session.terminated:
            raise UnexpectedServerRequest(self.session.incident_payload or {})

    async def _drain_incident(self) -> None:
        await asyncio.sleep(0)
        self._raise_if_incident()

    async def _session_request(
        self,
        method: str,
        params: dict[str, object] | None = None,
    ) -> dict[str, object]:
        assert self.client is not None
        if method in MUTATING_NO_RETRY_METHODS:
            raise RuntimeError(MUTATING_OWNER_MESSAGE)
        from .durability.session_owner import AppServerSessionOwner

        owner = AppServerSessionOwner.for_client(self.client, self.store)
        response = dict(await owner.request_read(method, params))
        await self._drain_incident()
        return response

    async def _start_canary_thread(self, canary_id: str) -> dict[str, object]:
        assert self.client is not None
        from .durability.outbox import MutationSpec, OperationState
        from .durability.session_owner import AppServerSessionOwner

        owner = AppServerSessionOwner.for_client(self.client, self.store)
        operation = owner.enqueue_mutation(
            MutationSpec(
                dedupe_key=f"canary-thread:{canary_id}",
                protocol_session_id=owner.protocol_session_id,
                run_id=owner.protocol_session_id,
                method="thread/start",
                params=canonical_canary_thread_start_request(self.store.runtime_home, canary_id),
                target=f"canary:{canary_id}",
            )
        )
        submitted = await owner.submit(operation.operation_id)
        if submitted.state is not OperationState.DONE or submitted.outcome != "OK":
            if owner.terminated:
                raise UnexpectedServerRequest(owner.incident_payload or {})
            raise RuntimeError("canary thread/start was not observed")
        await self._drain_incident()
        response = dict(submitted.response or {})
        response["_hmasd_operation_id"] = operation.operation_id
        return response

    async def _start_canary_turn(self, canary_id: str, thread_id: str) -> dict[str, object]:
        assert self.client is not None
        from .durability.outbox import MutationSpec, OperationState
        from .durability.session_owner import AppServerSessionOwner

        owner = AppServerSessionOwner.for_client(self.client, self.store)
        operation = owner.enqueue_mutation(
            MutationSpec(
                dedupe_key=f"canary-turn:{canary_id}",
                protocol_session_id=owner.protocol_session_id,
                run_id=owner.protocol_session_id,
                method="turn/start",
                params=canonical_canary_turn_start_request(thread_id),
                target=f"canary:{canary_id}",
                thread_id=thread_id,
            )
        )
        submitted = await owner.submit(operation.operation_id)
        if submitted.state is not OperationState.DONE or submitted.outcome != "OK":
            if owner.terminated:
                raise UnexpectedServerRequest(owner.incident_payload or {})
            raise RuntimeError("canary turn/start was not observed")
        await self._drain_incident()
        response = dict(submitted.response or {})
        response["_hmasd_operation_id"] = operation.operation_id
        return response

    async def _list_threads(self) -> list[dict[str, object]]:
        threads: list[dict[str, object]] = []
        cursor: object = None
        while True:
            params: dict[str, object] = {}
            if cursor:
                params["cursor"] = cursor
            response = await self._session_request("thread/list", params)
            result = response.get("result") if isinstance(response.get("result"), Mapping) else {}
            data = result.get("data") if isinstance(result, Mapping) else None
            if isinstance(data, list):
                threads.extend(item for item in data if isinstance(item, dict))
            next_cursor = result.get("nextCursor") if isinstance(result, Mapping) else None
            if not next_cursor:
                return threads
            cursor = next_cursor

    async def _read_thread(self, thread_id: str, include_turns: bool = False) -> dict[str, object]:
        params: dict[str, object] = {"threadId": thread_id}
        if include_turns:
            params["includeTurns"] = True
        response = await self._session_request("thread/read", params)
        result = response.get("result")
        return dict(result) if isinstance(result, Mapping) else {}

    async def initialize(self) -> None:
        assert self.client is not None and self.run_id is not None
        await self.client.initialize()
        await self._drain_incident()
        self.store.mark_initialized(self.run_id)
        self.record_local_event("APP_SERVER_INITIALIZED_OBSERVED", {})

    async def reconcile_threads(self) -> dict[str, object]:
        assert self.client is not None and self.run_id is not None
        self._raise_if_incident()
        rec_id = self.store.start_reconciliation(self.run_id)
        self.record_local_event("RECONCILIATION_STARTED_OBSERVED", {})
        try:
            threads = await self._list_threads()
            for thread in threads:
                thread_id = thread.get("id")
                if not thread_id:
                    continue
                await self._read_thread(str(thread_id), include_turns=False)
            self.store.complete_reconciliation(rec_id, thread_count=len(threads), outcome="OK")
            self.record_local_event("RECONCILIATION_COMPLETED_OBSERVED", {"thread_count": len(threads)})
            return {"thread_count": len(threads), "outcome": "OK"}
        except UnexpectedServerRequest:
            self.store.complete_reconciliation(
                rec_id, thread_count=0, outcome="ERROR", error={"type": "UnexpectedServerRequest"}
            )
            raise
        except Exception as exc:
            if self.session is not None and self.session.terminated:
                self.store.complete_reconciliation(
                    rec_id, thread_count=0, outcome="ERROR", error={"type": "UnexpectedServerRequest"}
                )
                raise UnexpectedServerRequest(self.session.incident_payload or {}) from exc
            self.store.complete_reconciliation(
                rec_id, thread_count=0, outcome="ERROR", error={"type": type(exc).__name__}
            )
            raise

    async def _watch_server_requests(self) -> None:
        assert self.client is not None
        session = self.session or ManagedAppServerSession.for_client(self.client, self.store)
        self.session = session
        await session._incident.wait()
        raise UnexpectedServerRequest(session.incident_payload or {})

    async def _await_reader_quarantine(self) -> None:
        assert self.client is not None and self.session is not None
        await self.client.reader_terminal.wait()
        await self.session._incident.wait()

    async def serve(
        self,
        duration_seconds: float | None = None,
        ready_hook: Callable[[dict[str, object]], Awaitable[None] | None] | None = None,
        *,
        control: HostControlChannel | None = None,
        profile: RuntimeProfile = RuntimeProfile.OBSERVER,
    ) -> ObserverRunResult:
        from .durability.session_owner import SessionOwnerError

        watcher: asyncio.Task[None] | None = None
        command_task: asyncio.Task[None] | None = None
        stop_waiter: asyncio.Task[bool] | None = None
        host_stop_event = asyncio.Event()
        try:
            # Startup is part of the lifecycle guarded by this cleanup block.
            # ``start`` may have created a run and an App Server transport
            # before a later startup step fails.
            await self.start()
            await self.initialize()
            watcher = asyncio.create_task(self._watch_server_requests())
            await asyncio.sleep(0)
            session_available = True
            if watcher.done():
                exc = watcher.exception()
                if isinstance(exc, UnexpectedServerRequest):
                    session_available = False
                    watcher = None
                elif exc is not None:
                    raise exc
                else:
                    raise RuntimeError("server-request watcher stopped before readiness")
            if session_available:
                try:
                    reconciliation = await asyncio.wait_for(
                        self.reconcile_threads(),
                        timeout=self.config.first_reconciliation_timeout_seconds,
                    )
                except TransportClosed:
                    await self._await_reader_quarantine()
                    reconciliation = {"thread_count": 0, "outcome": "SESSION_UNAVAILABLE"}
                    session_available = False
                    watcher = None
                except (UnexpectedServerRequest, SessionOwnerError):
                    reconciliation = {"thread_count": 0, "outcome": "SESSION_UNAVAILABLE"}
                    session_available = False
                    watcher = None
                if watcher is not None and watcher.done():
                    exc = watcher.exception()
                    if isinstance(exc, UnexpectedServerRequest):
                        reconciliation = {"thread_count": 0, "outcome": "SESSION_UNAVAILABLE"}
                        session_available = False
                        watcher = None
                    elif exc is not None:
                        raise exc
            else:
                reconciliation = {"thread_count": 0, "outcome": "SESSION_UNAVAILABLE"}
            if ready_hook is not None:
                assert self.run_id is not None and self.transport is not None
                ready_result = ready_hook(
                    {
                        "run_id": self.run_id,
                        # READY identifies the long-lived Python supervisor
                        # host.  The distinct App Server child PID remains in
                        # observer_runs and APP_SERVER_PROCESS_* facts.
                        "process_id": os.getpid(),
                        "initialized_at": _now(),
                        "watcher_active": watcher is not None and not watcher.done(),
                        "first_reconciliation_completed": reconciliation["outcome"] == "OK",
                        "thread_count": int(reconciliation["thread_count"]),
                    }
                )
                if inspect.isawaitable(ready_result):
                    await ready_result
            if control is not None:
                command_task = asyncio.create_task(
                    control.serve(
                        profile=profile,
                        service=self,
                        stop_event=host_stop_event,
                    )
                )
                stop_waiter = asyncio.create_task(host_stop_event.wait())
            deadline = None if duration_seconds is None else asyncio.get_running_loop().time() + duration_seconds
            while True:
                if host_stop_event.is_set():
                    return await self.stop(EndKind.NORMAL.value)
                if deadline is not None and asyncio.get_running_loop().time() >= deadline:
                    return await self.stop(EndKind.NORMAL.value)
                timeout = self.config.reconcile_interval_seconds
                if deadline is not None:
                    timeout = min(timeout, max(0.05, deadline - asyncio.get_running_loop().time()))
                waited: set[asyncio.Task[Any]] = set()
                if watcher is not None:
                    waited.add(watcher)
                if command_task is not None:
                    waited.add(command_task)
                if stop_waiter is not None:
                    waited.add(stop_waiter)
                if waited:
                    done, _pending = await asyncio.wait(waited, timeout=timeout)
                else:
                    await asyncio.sleep(timeout)
                    done = set()
                if watcher is not None and watcher in done:
                    exc = watcher.exception()
                    if isinstance(exc, UnexpectedServerRequest):
                        # Quarantine only the failed protocol session. Host
                        # control/status remains available in bounded degraded mode.
                        watcher = None
                        continue
                    if exc:
                        raise exc
                if stop_waiter is not None and stop_waiter in done:
                    return await self.stop(EndKind.NORMAL.value)
                if command_task is not None and command_task in done:
                    exc = command_task.exception()
                    if exc is not None:
                        raise exc
                    if not host_stop_event.is_set():
                        raise RuntimeError("host control loop stopped unexpectedly")
                    return await self.stop(EndKind.NORMAL.value)
                if self.session is None or not self.session.terminated:
                    try:
                        await self.reconcile_threads()
                    except TransportClosed:
                        await self._await_reader_quarantine()
                        watcher = None
        except UnexpectedServerRequest as exc:
            return await self._terminate_unexpected(exc)
        except TransportClosed:
            if self.session is not None and self.session.terminated:
                return await self._terminate_unexpected(
                    UnexpectedServerRequest(self.session.incident_payload or {})
                )
            return await self.stop(EndKind.TRANSPORT_EOF.value)
        except Exception:
            if not self._stopped:
                await self.stop(EndKind.PROTOCOL_INCIDENT.value)
            raise
        finally:
            host_stop_event.set()
            tasks = tuple(
                task
                for task in (watcher, command_task, stop_waiter)
                if task is not None and not task.done()
            )
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def run_snapshot(self) -> dict[str, object] | ObserverRunResult:
        await self.start()
        try:
            await self.initialize()
            await self._drain_incident()
            result = await self.reconcile_threads()
            await self._drain_incident()
            await self.stop(EndKind.NORMAL.value)
            return result
        except UnexpectedServerRequest as exc:
            return await self._terminate_unexpected(exc)
        except Exception:
            if not self._stopped:
                await self.stop(EndKind.PROTOCOL_INCIDENT.value)
            raise

    async def _terminate_unexpected(self, exc: UnexpectedServerRequest) -> ObserverRunResult:
        assert self.run_id is not None
        ids = extract_protocol_ids(exc.payload)
        request_id = str(ids.request_id or "")
        already = None
        if request_id:
            already = self.store.connection.execute(
                "SELECT 1 FROM server_requests WHERE server_request_id = ?",
                (request_id,),
            ).fetchone()
        if already is None:
            self.store.record_server_request(
                run_id=self.run_id,
                server_request_id=request_id,
                method=str(ids.method or ""),
                payload=exc.payload,
                thread_id=ids.thread_id,
                turn_id=ids.turn_id,
            )
        return await self.stop(EndKind.UNEXPECTED_SERVER_REQUEST.value)

    async def stop(self, end_kind: str) -> ObserverRunResult:
        if self._stopped:
            count = self.store.connection.execute("SELECT COUNT(*) FROM thread_snapshots").fetchone()[0]
            return ObserverRunResult(
                run_id=self.run_id or "",
                end_kind=self._end_kind,
                exit_code=None if self.transport is None else self.transport._process.returncode if self.transport._process else None,
                initialized=True,
                thread_count=int(count),
            )
        self._stopped = True
        await asyncio.sleep(0)
        self._end_kind = end_kind
        if self.session is not None:
            self.session.close()
        exit_code = None
        if self.transport is not None:
            await self.transport.stop()
            if self.transport._process is not None:
                exit_code = self.transport._process.returncode
        if self.run_id is not None:
            self.record_local_event("APP_SERVER_PROCESS_EXITED_OBSERVED", {"end_kind": end_kind})
            if end_kind == EndKind.TRANSPORT_EOF.value:
                self.record_local_event("TRANSPORT_EOF_OBSERVED", {})
            self.store.end_run(self.run_id, end_kind, exit_code)
        count = self.store.connection.execute("SELECT COUNT(*) FROM thread_snapshots").fetchone()[0]
        return ObserverRunResult(
            run_id=self.run_id or "",
            end_kind=end_kind,
            exit_code=exit_code,
            initialized=True,
            thread_count=int(count),
        )

    async def run_ephemeral_canary(self, timeout_seconds: float = 300) -> CanaryResult:
        canary_id = f"canary_{uuid.uuid4().hex}"
        scratch = canonical_canary_scratch(self.store.runtime_home, canary_id)
        scratch.mkdir(parents=True, exist_ok=True)
        outbound: list[str] = []
        previous_hook = self.outbound_hook

        def _hook(message: dict[str, Any]) -> None:
            outbound.append(str(message.get("method") or ""))
            if previous_hook is not None:
                previous_hook(message)

        self.outbound_hook = _hook
        await self.start()
        assert self.run_id is not None and self.client is not None
        self.record_local_event("CANARY_STARTED_OBSERVED", {"canary_id": canary_id})
        try:
            await self.initialize()
            watcher = asyncio.create_task(self._watch_server_requests())
            await asyncio.sleep(0)
            if watcher.done():
                exc = watcher.exception()
                if isinstance(exc, UnexpectedServerRequest):
                    await self._terminate_unexpected(exc)
                    self.record_local_event("CANARY_INCIDENT_OBSERVED", {"reason": "server_request"})
                    return CanaryResult(canary_id, self.run_id, None, None, "incident", incident="server_request")
            start = await self._start_canary_thread(canary_id)
            start.pop("_hmasd_operation_id", None)
            if watcher.done():
                exc = watcher.exception()
                if isinstance(exc, UnexpectedServerRequest):
                    await self._terminate_unexpected(exc)
                    self.record_local_event("CANARY_INCIDENT_OBSERVED", {"reason": "server_request"})
                    return CanaryResult(canary_id, self.run_id, None, None, "incident", incident="server_request")
            result = start.get("result") if isinstance(start.get("result"), dict) else {}
            thread = result.get("thread") if isinstance(result.get("thread"), dict) else {}
            thread_id = str(thread.get("id") or "")
            if not thread.get("ephemeral"):
                self.record_local_event("CANARY_INCIDENT_OBSERVED", {"reason": "not_ephemeral"})
                await self.stop(EndKind.PROTOCOL_INCIDENT.value)
                return CanaryResult(canary_id, self.run_id, thread_id, None, "incident", incident="not_ephemeral")
            turn = await self._start_canary_turn(canary_id, thread_id)
            turn.pop("_hmasd_operation_id", None)
            if outbound.count("thread/start") != 1 or outbound.count("turn/start") != 1:
                raise RuntimeError("mutating canary requests must be sent exactly once")
            turn_id = extract_protocol_ids(turn).turn_id
            inner = turn.get("result") if isinstance(turn.get("result"), dict) else {}
            if isinstance(inner.get("turn"), dict):
                turn_id = turn_id or str(inner["turn"].get("id") or "") or None
            status, text = await self._await_turn_completed(timeout_seconds, watcher)
            if status != "completed" or text != CANARY_TEXT:
                self.record_local_event("CANARY_INCIDENT_OBSERVED", {"status": status})
                await self.stop(EndKind.PROTOCOL_INCIDENT.value)
                return CanaryResult(
                    canary_id, self.run_id, thread_id, turn_id, "incident", final_text=text, incident=status or "mismatch"
                )
            self.record_local_event("CANARY_COMPLETED_OBSERVED", {"thread_id": thread_id})
            await self.stop(EndKind.NORMAL.value)
            return CanaryResult(canary_id, self.run_id, thread_id, turn_id, "ok", final_text=text)
        except UnexpectedServerRequest as exc:
            await self._terminate_unexpected(exc)
            self.record_local_event("CANARY_INCIDENT_OBSERVED", {"reason": "server_request"})
            return CanaryResult(canary_id, self.run_id, None, None, "incident", incident="server_request")
        except asyncio.TimeoutError:
            self.record_local_event("CANARY_INCIDENT_OBSERVED", {"reason": "timeout"})
            await self.stop(EndKind.PROTOCOL_INCIDENT.value)
            return CanaryResult(canary_id, self.run_id, None, None, "incident", incident="timeout")
        finally:
            if scratch.exists():
                shutil.rmtree(scratch, ignore_errors=True)

    async def _await_turn_completed(
        self,
        timeout_seconds: float,
        watcher: asyncio.Task[None],
    ) -> tuple[str, str]:
        assert self.client is not None
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        pieces: list[str] = []
        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise asyncio.TimeoutError()
            if watcher.done():
                exc = watcher.exception()
                if isinstance(exc, UnexpectedServerRequest):
                    raise exc
                if exc:
                    raise exc
            try:
                notification = await asyncio.wait_for(self.client.notifications.get(), timeout=min(0.2, remaining))
            except asyncio.TimeoutError:
                continue
            method = str(notification.get("method") or "")
            params = notification.get("params") if isinstance(notification.get("params"), dict) else {}
            if method.endswith("/delta"):
                delta = params.get("delta")
                if isinstance(delta, str):
                    pieces.append(delta)
            if method == "turn/completed":
                turn = params.get("turn") if isinstance(params.get("turn"), dict) else params
                status = str(turn.get("status") or "")
                return status, "".join(pieces).strip()
