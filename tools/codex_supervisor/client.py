"""App Server JSONL client: handshake, correlation, and bounded read retry."""

from __future__ import annotations

import asyncio
import random
from typing import Any, Awaitable, Callable, Mapping

from .models import ObserverConfig, RequestClass, RpcShape
from .protocol import classify_rpc_message
from .transport import AppServerTransport, TransportClosed, TransportMessage

# Method strings present in both official app-server docs and the host
# ClientRequest.json from `codex-cli 0.147.0`. Unknown methods default to
# MUTATING_NO_RETRY.
READ_IDEMPOTENT_METHODS = frozenset({"thread/list", "thread/read"})
MUTATING_NO_RETRY_METHODS = frozenset(
    {
        "thread/start",
        "thread/resume",
        "thread/fork",
        "turn/start",
        "turn/steer",
        "turn/interrupt",
        "thread/compact/start",
        "review/start",
    }
)
OVERLOAD_CODE = -32001
CLIENT_NOTIFICATION_METHODS = frozenset({"initialized"})


class AppServerRpcError(RuntimeError):
    def __init__(self, code: int | None, message: str, payload: Mapping[str, Any]):
        super().__init__(message)
        self.code = code
        self.payload = dict(payload)


class RetryRequired(AppServerRpcError):
    """Raised when a mutating request receives a retryable overload."""


class UnexpectedServerRequest(RuntimeError):
    def __init__(self, message: Mapping[str, Any]):
        super().__init__("unexpected server-initiated request")
        self.payload = dict(message)


class HandshakeError(RuntimeError):
    """Raised when a request is sent before initialize/initialized complete."""


def request_class_for(method: str) -> RequestClass:
    if method == "initialize":
        return RequestClass.HANDSHAKE
    if method in READ_IDEMPOTENT_METHODS:
        return RequestClass.READ_IDEMPOTENT
    return RequestClass.MUTATING_NO_RETRY


class AppServerClient:
    def __init__(
        self,
        transport: AppServerTransport,
        config: ObserverConfig,
        *,
        sleep: Callable[[float], Awaitable[None]] | None = None,
        jitter: Callable[[], float] | None = None,
        on_inbound: Callable[[TransportMessage], None] | None = None,
    ) -> None:
        self.transport = transport
        self.config = config
        self._pending: dict[str, asyncio.Future[dict[str, object]]] = {}
        self._next_id = 1
        self._initialize_complete = False
        self._reader: asyncio.Task[None] | None = None
        self._sleep = sleep or asyncio.sleep
        self._jitter = jitter or (lambda: random.random() * 0.05)
        self._on_inbound = on_inbound
        self.notifications: asyncio.Queue[dict[str, object]] = asyncio.Queue()
        self.server_requests: asyncio.Queue[dict[str, object]] = asyncio.Queue()

    def start_reader(self) -> None:
        if self._reader is None:
            self._reader = asyncio.create_task(self._read_loop())

    async def _read_loop(self) -> None:
        try:
            while True:
                message = await self.transport.recv()
                if self._on_inbound is not None:
                    self._on_inbound(message)
                await self._route(dict(message.payload))
        except TransportClosed as exc:
            self._fail_pending(exc)
        except Exception as exc:
            self._fail_pending(exc)

    def _fail_pending(self, exc: BaseException) -> None:
        for future in list(self._pending.values()):
            if not future.done():
                future.set_exception(exc)
        self._pending.clear()

    async def _route(self, payload: dict[str, object]) -> None:
        shape = classify_rpc_message(payload)
        if shape is RpcShape.RESPONSE:
            request_id = str(payload.get("id"))
            future = self._pending.pop(request_id, None)
            if future is None:
                raise RuntimeError(f"unknown response id: {request_id}")
            if not future.done():
                future.set_result(payload)
            return
        if shape is RpcShape.REQUEST:
            await self.server_requests.put(payload)
            return
        if shape is RpcShape.NOTIFICATION:
            await self.notifications.put(payload)
            return
        raise RuntimeError("invalid inbound RPC object")

    async def initialize(self) -> dict[str, object]:
        self.start_reader()
        params = {
            "clientInfo": {
                "name": self.config.client_name,
                "title": self.config.client_title,
                "version": self.config.client_version,
            },
            "capabilities": {"experimentalApi": bool(self.config.experimental_api)},
        }
        response = await self.request(
            "initialize",
            params,
            timeout=self.config.initialize_timeout_seconds,
        )
        await self.notify("initialized", {})
        self._initialize_complete = True
        return response

    async def notify(self, method: str, params: Mapping[str, object] | None = None) -> None:
        if method not in CLIENT_NOTIFICATION_METHODS:
            raise HandshakeError(f"client notification not in local schema: {method}")
        await self.transport.send({"method": method, "params": dict(params or {})})

    async def request(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
        *,
        timeout: float | None = None,
    ) -> dict[str, object]:
        self.start_reader()
        if method != "initialize" and not self._initialize_complete:
            raise HandshakeError("initialize/initialized must complete before other requests")
        klass = request_class_for(method)
        attempt = 1
        while True:
            request_id = str(self._next_id)
            self._next_id += 1
            payload = {"id": int(request_id), "method": method, "params": dict(params or {})}
            future: asyncio.Future[dict[str, object]] = asyncio.get_running_loop().create_future()
            self._pending[request_id] = future
            await self.transport.send(payload)
            try:
                response = await asyncio.wait_for(
                    future, timeout=timeout or self.config.request_timeout_seconds
                )
            except Exception:
                self._pending.pop(request_id, None)
                raise
            if "error" in response:
                error = response.get("error") if isinstance(response.get("error"), Mapping) else {}
                code = error.get("code") if isinstance(error, Mapping) else None
                message = str(error.get("message") if isinstance(error, Mapping) else "rpc error")
                rpc_error = AppServerRpcError(int(code) if isinstance(code, int) else None, message, response)
                if (
                    isinstance(code, int)
                    and code == OVERLOAD_CODE
                    and klass is RequestClass.READ_IDEMPOTENT
                    and attempt < self.config.read_retry_attempts
                ):
                    delay = self.config.read_retry_base_seconds * (2 ** (attempt - 1)) + self._jitter()
                    await self._sleep(delay)
                    attempt += 1
                    continue
                if isinstance(code, int) and code == OVERLOAD_CODE and klass is not RequestClass.READ_IDEMPOTENT:
                    raise RetryRequired(code, message, response)
                raise rpc_error
            return response

    async def list_threads(self) -> list[dict[str, object]]:
        threads: list[dict[str, object]] = []
        cursor: object = None
        while True:
            params: dict[str, object] = {}
            if cursor:
                params["cursor"] = cursor
            response = await self.request("thread/list", params)
            result = response.get("result") if isinstance(response.get("result"), Mapping) else {}
            data = result.get("data") if isinstance(result, Mapping) else None
            if isinstance(data, list):
                threads.extend(item for item in data if isinstance(item, dict))
            next_cursor = result.get("nextCursor") if isinstance(result, Mapping) else None
            if not next_cursor:
                return threads
            cursor = next_cursor

    async def read_thread(self, thread_id: str, include_turns: bool = False) -> dict[str, object]:
        params: dict[str, object] = {"threadId": thread_id}
        if include_turns:
            params["includeTurns"] = True
        response = await self.request("thread/read", params)
        result = response.get("result")
        return dict(result) if isinstance(result, Mapping) else {}
