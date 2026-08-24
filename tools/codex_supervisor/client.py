"""App Server JSONL client: handshake, correlation, and bounded read retry."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Mapping

from .models import ObserverConfig, RequestClass, RpcShape
from .protocol import classify_rpc_message, decode_jsonl_line, encode_jsonl
from .transport import AppServerTransport, TransportClosed, TransportMessage

# Method strings present in both official app-server docs and the host
# ClientRequest.json from `codex-cli 0.147.0`. Unknown methods default to
# MUTATING_NO_RETRY.
READ_IDEMPOTENT_METHODS = frozenset({"thread/list", "thread/read", "thread/loaded/list"})
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
        "thread/memoryMode/set",
    }
)
OVERLOAD_CODE = -32001
CLIENT_NOTIFICATION_METHODS = frozenset({"initialized"})
COMPATIBLE_REQUEST_METHODS = frozenset(
    {
        "initialize",
        "thread/list",
        "thread/read",
        "thread/loaded/list",
    }
)
MUTATING_OWNER_MESSAGE = "mutating requests require AppServerSessionOwner.submit_effect"


@dataclass(frozen=True)
class PreparedRpcRequest:
    request_id: str
    method: str
    params: Mapping[str, object]
    payload: Mapping[str, object]
    request_class: RequestClass
    future: asyncio.Future[dict[str, object]]


@dataclass(frozen=True)
class FrozenRpcRequest:
    request_id: int
    method: str
    wire_bytes: bytes
    future: asyncio.Future[dict[str, object]]


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
        # Durable mutation ids are positive. Ephemeral handshake/read ids use a
        # disjoint negative range and can therefore never collide after restart.
        self._next_id = -1
        self._initialize_complete = False
        self._reader: asyncio.Task[None] | None = None
        self._sleep = sleep or asyncio.sleep
        self._jitter = jitter or (lambda: random.random() * 0.05)
        self._on_inbound = on_inbound
        self.notifications: asyncio.Queue[dict[str, object]] = asyncio.Queue()
        self.server_requests: asyncio.Queue[dict[str, object]] = asyncio.Queue()
        self.reader_terminal = asyncio.Event()
        self.reader_terminal_exception: BaseException | None = None

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
            self.reader_terminal_exception = exc
            self._fail_pending(exc)
            self.reader_terminal.set()
        except Exception as exc:
            self.reader_terminal_exception = exc
            self._fail_pending(exc)
            self.reader_terminal.set()

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
                # A bounded read may time out before its late response arrives.
                # The response is still captured by the observer; it must not
                # take down the session or another mutation lane.
                return
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

    def prepare_request(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
    ) -> PreparedRpcRequest:
        self.start_reader()
        if method != "initialize" and not self._initialize_complete:
            raise HandshakeError("initialize/initialized must complete before other requests")
        request_id = str(self._next_id)
        self._next_id -= 1
        payload = {"id": int(request_id), "method": method, "params": dict(params or {})}
        future: asyncio.Future[dict[str, object]] = asyncio.get_running_loop().create_future()
        self._pending[request_id] = future
        return PreparedRpcRequest(
            request_id=request_id,
            method=method,
            params=dict(params or {}),
            payload=payload,
            request_class=request_class_for(method),
            future=future,
        )

    def discard_prepared(self, prepared: PreparedRpcRequest) -> None:
        future = self._pending.pop(prepared.request_id, None)
        if future is not None and not future.done():
            future.cancel()

    async def send_prepared(self, prepared: PreparedRpcRequest) -> None:
        actual = dict(prepared.payload)
        expected = {
            "id": int(prepared.request_id),
            "method": prepared.method,
            "params": dict(prepared.params),
        }
        actual_method = actual.get("method")
        actual_class = request_class_for(str(actual_method or ""))
        expected_class = request_class_for(prepared.method)
        if (
            actual_class is RequestClass.MUTATING_NO_RETRY
            or expected_class is RequestClass.MUTATING_NO_RETRY
            or prepared.request_class is not expected_class
        ):
            self.discard_prepared(prepared)
            raise RuntimeError(MUTATING_OWNER_MESSAGE)
        if actual != expected:
            self.discard_prepared(prepared)
            raise RuntimeError("prepared request changed before send")
        await self.transport.send(actual)

    @staticmethod
    def freeze_request(
        request_id: int, method: str, params: Mapping[str, object] | None = None
    ) -> bytes:
        if request_id <= 0:
            raise ValueError("durable mutation request id must be positive")
        return encode_jsonl(
            {"id": request_id, "method": method, "params": dict(params or {})}
        )

    def activate_frozen(
        self, request_id: int, method: str, wire_bytes: bytes
    ) -> FrozenRpcRequest:
        self.start_reader()
        if not self._initialize_complete:
            raise HandshakeError("initialize/initialized must complete before mutations")
        decoded = decode_jsonl_line(wire_bytes, self.config.max_jsonl_line_bytes)
        if decoded.get("id") != request_id or decoded.get("method") != method:
            raise ValueError("frozen request identity does not match its wire bytes")
        key = str(request_id)
        if key in self._pending:
            raise RuntimeError(f"request id is already active: {request_id}")
        future: asyncio.Future[dict[str, object]] = asyncio.get_running_loop().create_future()
        self._pending[key] = future
        return FrozenRpcRequest(request_id, method, bytes(wire_bytes), future)

    def discard_frozen(self, frozen: FrozenRpcRequest) -> None:
        future = self._pending.pop(str(frozen.request_id), None)
        if future is not None and not future.done():
            future.cancel()

    async def await_frozen(
        self, frozen: FrozenRpcRequest, *, timeout: float | None = None
    ) -> dict[str, object]:
        try:
            response = await asyncio.wait_for(
                frozen.future, timeout=timeout or self.config.request_timeout_seconds
            )
        except BaseException:
            self._pending.pop(str(frozen.request_id), None)
            raise
        if "error" not in response:
            return response
        error = response.get("error") if isinstance(response.get("error"), Mapping) else {}
        code = error.get("code") if isinstance(error, Mapping) else None
        message = str(error.get("message") if isinstance(error, Mapping) else "rpc error")
        raise AppServerRpcError(int(code) if isinstance(code, int) else None, message, response)

    async def await_prepared(
        self,
        prepared: PreparedRpcRequest,
        *,
        timeout: float | None = None,
    ) -> dict[str, object]:
        try:
            response = await asyncio.wait_for(
                prepared.future, timeout=timeout or self.config.request_timeout_seconds
            )
        except Exception:
            self._pending.pop(prepared.request_id, None)
            raise
        if "error" not in response:
            return response
        error = response.get("error") if isinstance(response.get("error"), Mapping) else {}
        code = error.get("code") if isinstance(error, Mapping) else None
        message = str(error.get("message") if isinstance(error, Mapping) else "rpc error")
        rpc_error = AppServerRpcError(int(code) if isinstance(code, int) else None, message, response)
        if isinstance(code, int) and code == OVERLOAD_CODE and prepared.request_class is not RequestClass.READ_IDEMPOTENT:
            raise RetryRequired(code, message, response)
        raise rpc_error

    async def request(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
        *,
        timeout: float | None = None,
    ) -> dict[str, object]:
        if method in MUTATING_NO_RETRY_METHODS:
            raise RuntimeError(MUTATING_OWNER_MESSAGE)
        klass = request_class_for(method)
        attempt = 1
        while True:
            prepared = self.prepare_request(method, params)
            await self.send_prepared(prepared)
            try:
                return await self.await_prepared(prepared, timeout=timeout)
            except AppServerRpcError as rpc_error:
                code = rpc_error.code
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
                raise

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

    async def list_loaded_threads(self) -> list[str]:
        loaded: list[str] = []
        cursor: object = None
        while True:
            params: dict[str, object] = {}
            if cursor:
                params["cursor"] = cursor
            response = await self.request("thread/loaded/list", params)
            result = response.get("result") if isinstance(response.get("result"), Mapping) else {}
            data = result.get("data") if isinstance(result, Mapping) else None
            if isinstance(data, list):
                loaded.extend(str(item) for item in data)
            next_cursor = result.get("nextCursor") if isinstance(result, Mapping) else None
            if not next_cursor:
                return loaded
            cursor = next_cursor
