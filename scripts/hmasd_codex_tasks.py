#!/usr/bin/env python3
"""Small native Codex App Server adapter for HMASD Work Packet delivery.

The adapter is deliberately transport-only.  It owns no queue, receipt,
lifecycle, or durable task state; callers record independently observed native
facts through the existing HMASD state contracts.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import platform
import queue
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
from typing import Any, Mapping, Protocol, Sequence

try:
    from scripts import hmasd_platform, hmasd_state, hmasd_work_packet
except ImportError:
    import hmasd_platform
    import hmasd_state
    import hmasd_work_packet


PROTOCOL_MARKER = "hmasd.work-packet.dispatch.v2"
OPERATOR_ASSIGNMENT_MARKER = "hmasd.experiment-operator.assignment.v1"
_OPERATOR_ROLE = "hmasd-experiment-operator"
_CONFORMANCE_RESPONSE = '{"status":"HMASD_NATIVE_ADAPTER_CONFORMANCE_OK"}'
_CONFORMANCE_PROMPT = (
    "HMASD native adapter conformance probe. Do not call tools. "
    "Return exactly this JSON object and no other text: " + _CONFORMANCE_RESPONSE
)
_CONFORMANCE_SCHEMA = {
    "additionalProperties": False,
    "properties": {
        "status": {
            "const": "HMASD_NATIVE_ADAPTER_CONFORMANCE_OK",
            "type": "string",
        }
    },
    "required": ["status"],
    "type": "object",
}
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_IDENTITY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}\Z")
_DISPATCH_VERBS = {"CREATE_TASK_INTENT", "DISPATCH_EXISTING"}
_RETIRED_RECOVERY_IDENTITY = "hmasd-workflow-recovery-manager"
_CAPACITY_ERRORS = {
    "usageLimitExceeded",
    "sessionBudgetExceeded",
    "serverOverloaded",
}
_PARTICIPANT_SLICE_INSTRUCTION = (
    "Complete only the exact Work Packet slice above. First reuse any existing exact "
    "return; otherwise read the packet, complete its bounded assignment, publish its "
    "typed result, and return that immutable witness."
)
_SOURCE_KINDS = [
    "cli",
    "vscode",
    "exec",
    "appServer",
    "subAgent",
    "subAgentReview",
    "subAgentCompact",
    "subAgentThreadSpawn",
    "subAgentOther",
    "unknown",
]
_SAFE_THREAD_FIELDS = (
    "id",
    "sessionId",
    "name",
    "parentThreadId",
    "forkedFromId",
    "source",
    "threadSource",
    "status",
    "cwd",
    "modelProvider",
    "createdAt",
    "updatedAt",
    "recencyAt",
    "ephemeral",
    "agentNickname",
    "agentRole",
    "canAcceptDirectInput",
    "instructionSources",
)
_EOF = object()


class Transport(Protocol):
    def write_line(self, data: bytes) -> None: ...

    def read_line(self, timeout: float) -> bytes | None: ...

    def close(self) -> None: ...


def default_server_command() -> tuple[str, ...]:
    """Resolve a CreateProcess-compatible launcher without using a shell."""

    executable: str | None = None
    if sys.platform == "win32":
        machine = platform.machine().lower()
        target = "aarch64-pc-windows-msvc" if machine in {"arm64", "aarch64"} else "x86_64-pc-windows-msvc"
        package = "codex-win32-arm64" if target.startswith("aarch64") else "codex-win32-x64"
        package_roots: list[Path] = []
        managed_root = os.environ.get("CODEX_MANAGED_PACKAGE_ROOT")
        if managed_root:
            package_roots.append(Path(managed_root))
        npm_launcher = shutil.which("codex.cmd")
        if npm_launcher:
            package_roots.append(
                Path(npm_launcher).resolve().parent / "node_modules" / "@openai" / "codex"
            )
        for root in package_roots:
            candidates = (
                root / "node_modules" / "@openai" / package / "vendor" / target / "bin" / "codex.exe",
                root / "vendor" / target / "bin" / "codex.exe",
            )
            executable_path = next((item for item in candidates if item.is_file()), None)
            if executable_path is not None:
                executable = str(executable_path)
                break
    if executable is None:
        executable = shutil.which("codex.exe" if sys.platform == "win32" else "codex")
    if executable is None:
        executable = "codex.exe" if sys.platform == "win32" else "codex"
    return (executable, "-c", "project_doc_max_bytes=0", "app-server")


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _wire_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _relative_posix_path(value: str) -> str:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value:
        raise ValueError("packet locator must be a repository-relative POSIX path")
    parts = value.split("/")
    if re.match(r"^[A-Za-z]:", value) or any(
        part in {"", ".", ".."} or ":" in part for part in parts
    ):
        raise ValueError("packet locator must be a repository-relative POSIX path")
    return value


def dispatch_envelope_bytes(
    work_id: str,
    packet_locator: str,
    target_identity: str,
    *,
    attempt: int = 1,
    mode: str | None = None,
    root_override_reason: str | None = None,
) -> bytes:
    """Return the byte-stable, exact Work Packet dispatch input."""

    if not isinstance(work_id, str) or _SHA256.fullmatch(work_id) is None:
        raise ValueError("work_id must be a lowercase SHA256")
    if not isinstance(target_identity, str) or _IDENTITY.fullmatch(target_identity) is None:
        raise ValueError("target identity is invalid")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
        raise ValueError("attempt must be a positive integer")
    expected_mode = "DISPATCH" if attempt == 1 else "RESUME"
    selected_mode = expected_mode if mode is None else mode
    if selected_mode != expected_mode:
        raise ValueError(f"attempt {attempt} requires mode {expected_mode}")
    envelope: dict[str, Any] = {
        "protocol": PROTOCOL_MARKER,
        "work_id": work_id,
        "packet_locator": _relative_posix_path(packet_locator),
        "target_identity": target_identity,
        "attempt": attempt,
        "mode": selected_mode,
    }
    if root_override_reason is not None:
        if not isinstance(root_override_reason, str) or not root_override_reason.strip():
            raise ValueError("root override reason must be non-empty")
        envelope["root_override_reason"] = root_override_reason
    return _canonical_bytes(envelope)


class JsonlProcessTransport:
    """Persistent stdio JSONL subprocess with a bounded, portable reader."""

    def __init__(self, command: Sequence[str] | None = None) -> None:
        command = default_server_command() if command is None else command
        if not command:
            raise ValueError("app-server command must not be empty")
        self.process = subprocess.Popen(
            list(command),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._lines: queue.Queue[bytes | object] = queue.Queue()
        self._stderr: list[bytes] = []
        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._stderr_reader = threading.Thread(target=self._read_stderr, daemon=True)
        self._reader.start()
        self._stderr_reader.start()
        self._closed = False

    def _read_stdout(self) -> None:
        assert self.process.stdout is not None
        while True:
            line = self.process.stdout.readline()
            if not line:
                self._lines.put(_EOF)
                return
            self._lines.put(line)

    def _read_stderr(self) -> None:
        assert self.process.stderr is not None
        while True:
            line = self.process.stderr.readline()
            if not line:
                return
            self._stderr.append(line)
            if len(self._stderr) > 32:
                del self._stderr[0]

    def write_line(self, data: bytes) -> None:
        if self._closed or self.process.stdin is None:
            raise BrokenPipeError("app-server transport is closed")
        self.process.stdin.write(data)
        self.process.stdin.flush()

    def read_line(self, timeout: float) -> bytes | None:
        try:
            value = self._lines.get(timeout=max(0.0, timeout))
        except queue.Empty as exc:
            raise TimeoutError("app-server response timed out") from exc
        if value is _EOF:
            return None
        assert isinstance(value, bytes)
        return value

    @property
    def stderr_tail(self) -> str:
        return b"".join(self._stderr).decode("utf-8", errors="replace")

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self.process.stdin is not None:
            try:
                self.process.stdin.close()
            except OSError:
                pass
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2.0)


class AppServerClient:
    """One-process native client with lazy initialization and no durable state."""

    def __init__(
        self,
        command: Sequence[str] | None = None,
        *,
        transport: Transport | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._command = default_server_command() if command is None else tuple(command)
        self._transport = transport
        self.timeout = timeout
        self._next_id = 1
        self._initialized = False
        self._notifications: list[dict[str, Any]] = []
        self._pending_responses: dict[int, dict[str, Any]] = {}

    def __enter__(self) -> "AppServerClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._transport is not None:
            self._transport.close()

    def _peer(self) -> Transport:
        if self._transport is None:
            self._transport = JsonlProcessTransport(self._command)
        return self._transport

    @staticmethod
    def _failure(kind: str, *, after_send: bool, detail: str | None = None) -> dict[str, Any]:
        if after_send:
            result: dict[str, Any] = {
                "status": "UNKNOWN",
                "reason": f"{kind}_AFTER_SEND",
            }
        else:
            result = {"status": kind}
        if detail:
            result["detail"] = detail
        return result

    @staticmethod
    def _safe_jsonrpc_error(error: Any) -> dict[str, Any]:
        """Keep a stable machine diagnostic without reflecting server payloads."""
        code = (
            error.get("code")
            if isinstance(error, Mapping)
            and isinstance(error.get("code"), int)
            and not isinstance(error.get("code"), bool)
            else "UNSPECIFIED"
        )
        return {
            "error_code": code,
            "error_message": "server error details withheld",
        }

    def _read(self, deadline: float, *, after_send: bool) -> dict[str, Any]:
        try:
            line = self._peer().read_line(max(0.0, deadline - time.monotonic()))
        except TimeoutError:
            return self._failure("TIMEOUT", after_send=after_send)
        if line is None:
            return self._failure("EOF", after_send=after_send)
        try:
            value = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return self._failure("INVALID_JSON", after_send=after_send, detail=str(exc))
        if not isinstance(value, dict):
            return self._failure(
                "INVALID_JSON", after_send=after_send, detail="message is not an object"
            )
        return {"status": "MESSAGE", "message": value}

    def _request(
        self, method: str, params: Mapping[str, Any], *, after_send: bool = False
    ) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        try:
            self._peer().write_line(
                _wire_bytes({"id": request_id, "method": method, "params": dict(params)})
            )
        except (BrokenPipeError, OSError) as exc:
            return self._failure("EOF", after_send=after_send, detail=str(exc))

        deadline = time.monotonic() + self.timeout
        while True:
            if request_id in self._pending_responses:
                message = self._pending_responses.pop(request_id)
            else:
                read = self._read(deadline, after_send=after_send)
                if read["status"] != "MESSAGE":
                    return read
                message = read["message"]
            message_id = message.get("id")
            if "method" in message and message_id is not None:
                if after_send:
                    return {
                        "status": "UNKNOWN",
                        "reason": "SERVER_REQUEST_AFTER_SEND",
                    }
                return {
                    "status": "INTERVENTION_REQUIRED",
                    "reason": "SERVER_REQUEST",
                }
            if "method" in message:
                self._notifications.append(message)
                continue
            if message_id != request_id:
                if isinstance(message_id, int):
                    self._pending_responses[message_id] = message
                continue
            if "error" in message:
                diagnostic = self._safe_jsonrpc_error(message["error"])
                if after_send:
                    return {
                        "status": "UNKNOWN",
                        "reason": "ERROR_AFTER_SEND",
                        **diagnostic,
                    }
                return {"status": "ERROR", **diagnostic}
            if "result" not in message:
                return self._failure(
                    "INVALID_JSON", after_send=after_send, detail="response has no result"
                )
            return {"status": "OK", "result": message["result"]}

    def _ensure_initialized(self) -> dict[str, Any]:
        if self._initialized:
            return {"status": "OK"}
        initialized = self._request(
            "initialize",
            {
                "clientInfo": {"name": "hmasd-native-adapter", "version": "1"},
                "capabilities": {"experimentalApi": True},
            },
        )
        if initialized["status"] != "OK":
            return initialized
        try:
            self._peer().write_line(_wire_bytes({"method": "initialized", "params": {}}))
        except (BrokenPipeError, OSError) as exc:
            return {"status": "EOF", "detail": str(exc)}
        self._initialized = True
        return {"status": "OK", "server": initialized["result"]}

    def probe(self) -> dict[str, Any]:
        initialized = self._ensure_initialized()
        if initialized["status"] != "OK":
            return initialized
        return {"status": "OK", "server": initialized.get("server")}

    def list_threads(
        self, *, cwd: str | None = None, cursor: str | None = None
    ) -> dict[str, Any]:
        initialized = self._ensure_initialized()
        if initialized["status"] != "OK":
            return initialized
        params: dict[str, Any] = {"limit": 100, "sourceKinds": _SOURCE_KINDS}
        if cwd is not None:
            params["cwd"] = cwd
        if cursor is not None:
            params["cursor"] = cursor
        response = self._request("thread/list", params)
        if response["status"] != "OK":
            return response
        result = response["result"]
        return {
            "status": "OK",
            "threads": [
                self._safe_thread_fact(thread) for thread in result.get("data", [])
            ],
            "next_cursor": result.get("nextCursor"),
        }

    def _list_all_threads(self, *, cwd: str) -> dict[str, Any]:
        threads: list[dict[str, Any]] = []
        cursor: str | None = None
        seen_cursors: set[str] = set()
        while True:
            page = self.list_threads(cwd=cwd, cursor=cursor)
            if page.get("status") != "OK":
                return page
            threads.extend(page["threads"])
            next_cursor = page.get("next_cursor")
            if next_cursor is None:
                return {"status": "OK", "threads": threads}
            if not isinstance(next_cursor, str) or not next_cursor or next_cursor in seen_cursors:
                return {"status": "TASK_LIST_PAGINATION_DEFECT"}
            seen_cursors.add(next_cursor)
            cursor = next_cursor

    @staticmethod
    def _safe_thread_fact(thread: Any, *, include_turns: bool = False) -> dict[str, Any]:
        if not isinstance(thread, Mapping):
            return {}
        safe = {field: thread[field] for field in _SAFE_THREAD_FIELDS if field in thread}
        if include_turns:
            safe["turns"] = [
                {field: turn[field] for field in ("id", "status") if field in turn}
                for turn in thread.get("turns", [])
                if isinstance(turn, Mapping)
            ]
        return safe

    def _read_thread_full(self, thread_id: str) -> dict[str, Any]:
        initialized = self._ensure_initialized()
        if initialized["status"] != "OK":
            return initialized
        response = self._request(
            "thread/read", {"threadId": thread_id, "includeTurns": True}
        )
        if response["status"] != "OK":
            return response
        return {"status": "OK", "thread": response["result"].get("thread", {})}

    def read_thread(self, thread_id: str) -> dict[str, Any]:
        full = self._read_thread_full(thread_id)
        if full["status"] != "OK":
            return full
        return {
            "status": "OK",
            "thread": self._safe_thread_fact(full["thread"], include_turns=True),
        }

    def create_thread(
        self,
        *,
        cwd: str,
        target_identity: str,
        generation: int | None = None,
    ) -> dict[str, Any]:
        if _IDENTITY.fullmatch(target_identity) is None:
            raise ValueError("target identity is invalid")
        if generation is not None and (
            not isinstance(generation, int)
            or isinstance(generation, bool)
            or generation < 1
        ):
            raise ValueError("generation must be a positive integer")
        initialized = self._ensure_initialized()
        if initialized["status"] != "OK":
            return initialized
        runtime = self._target_runtime(target_identity)
        params: dict[str, Any] = {
            "approvalPolicy": "never",
            "cwd": cwd,
            "sandbox": "danger-full-access",
        }
        if generation is not None:
            manager = self._canonical_manager(target_identity, generation)
            if manager is None:
                raise ValueError("target identity is not a canonical manager")
            params["threadSource"] = manager["thread_source"]
        if runtime is not None:
            params.update(
                {
                    "model": runtime["model"],
                    "config": {"model_reasoning_effort": runtime["effort"]},
                }
            )
        response = self._request(
            "thread/start",
            params,
            after_send=True,
        )
        if response["status"] != "OK":
            return response
        thread_id = response["result"].get("thread", {}).get("id")
        if not isinstance(thread_id, str) or not thread_id:
            return {"status": "UNKNOWN", "reason": "MISSING_CREATED_THREAD_ID"}
        named = self._request(
            "thread/name/set",
            {"threadId": thread_id, "name": target_identity},
            after_send=True,
        )
        if named["status"] != "OK":
            observed = self._read_thread_full(thread_id)
            observed_name = (
                observed.get("thread", {}).get("name")
                if observed.get("status") == "OK"
                else None
            )
            if observed.get("status") == "OK" and observed_name != target_identity:
                if observed_name not in {None, ""}:
                    return {
                        "status": "TASK_IDENTITY_CONFLICT",
                        "target_identity": target_identity,
                        "thread_id": thread_id,
                        "observed_name": observed_name,
                    }
                return {
                    "status": "UNKNOWN",
                    "reason": "THREAD_CREATED_NAME_UNKNOWN",
                    "target_identity": target_identity,
                    "thread_id": thread_id,
                    "observed_name": observed_name,
                    "observed_status": observed.get("thread", {}).get("status"),
                    "name_result": named,
                }
            if observed.get("status") != "OK":
                return {
                    "status": "UNKNOWN",
                    "reason": "THREAD_CREATED_NAME_UNKNOWN",
                    "target_identity": target_identity,
                    "thread_id": thread_id,
                    "observed_name": None,
                    "name_result": named,
                    "observation_status": observed.get("status"),
                }
        native = response["result"]
        return {
            "status": "CREATED",
            "thread_id": thread_id,
            "session_id": thread_id,
            "instruction_sources": native.get("instructionSources", []),
            "cwd": native.get("cwd"),
            "model": native.get("model"),
            "model_provider": native.get("modelProvider"),
            "approval_policy": native.get("approvalPolicy"),
            "sandbox": native.get("sandbox"),
        }

    def fork_thread(self, thread_id: str, *, ephemeral: bool = True) -> dict[str, Any]:
        initialized = self._ensure_initialized()
        if initialized["status"] != "OK":
            return initialized
        params: dict[str, Any] = {
            "approvalPolicy": "never",
            "ephemeral": ephemeral,
            "sandbox": "danger-full-access",
            "threadId": thread_id,
        }
        if ephemeral:
            params["excludeTurns"] = True
        response = self._request("thread/fork", params, after_send=True)
        if response["status"] != "OK":
            return response
        new_id = response["result"].get("thread", {}).get("id")
        if not isinstance(new_id, str) or not new_id:
            return {"status": "UNKNOWN", "reason": "MISSING_FORK_THREAD_ID"}
        return {"status": "FORKED", "thread_id": new_id, "ephemeral": ephemeral}

    @staticmethod
    def _strict_text_documents(
        text: str, *, include_composite_suffix: bool
    ) -> list[dict[str, Any]]:
        try:
            document = json.loads(text)
        except json.JSONDecodeError:
            document = None
        if isinstance(document, Mapping):
            return [dict(document)]
        if text.count(_PARTICIPANT_SLICE_INSTRUCTION) != 1:
            return []
        prefix_text, suffix_text = text.split(_PARTICIPANT_SLICE_INSTRUCTION)
        try:
            prefix = json.loads(prefix_text)
        except json.JSONDecodeError:
            return []
        if not isinstance(prefix, Mapping) or prefix.get("protocol") != PROTOCOL_MARKER:
            return []
        if not include_composite_suffix:
            return [dict(prefix)]
        try:
            suffix = json.loads(suffix_text)
        except json.JSONDecodeError:
            return []
        if not isinstance(suffix, Mapping):
            return []
        return [dict(prefix), dict(suffix)]

    @staticmethod
    def _protocol_documents(
        value: Any, work_id: str | None
    ) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        if isinstance(value, Mapping):
            text = value.get("text")
            if value.get("type") in {"text", "input_text"} and isinstance(text, str):
                for document in AppServerClient._strict_text_documents(
                    text, include_composite_suffix=False
                ):
                    observed_work_id = document.get("work_id")
                    if (
                        document.get("protocol") == PROTOCOL_MARKER
                        and (
                            observed_work_id == work_id
                            if work_id is not None
                            else isinstance(observed_work_id, str)
                            and _SHA256.fullmatch(observed_work_id) is not None
                        )
                    ):
                        found.append(document)
            for item in value.values():
                found.extend(AppServerClient._protocol_documents(item, work_id))
        elif isinstance(value, list):
            for item in value:
                found.extend(AppServerClient._protocol_documents(item, work_id))
        return found

    @classmethod
    def _attempt_records(cls, turns: Any, work_id: str) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        if not isinstance(turns, list):
            return records
        for turn in turns:
            if not isinstance(turn, Mapping):
                continue
            for envelope in cls._protocol_documents(turn.get("items", []), work_id):
                records.append(
                    {
                        "attempt": envelope.get("attempt"),
                        "mode": envelope.get("mode"),
                        "packet_locator": envelope.get("packet_locator"),
                        "target_identity": envelope.get("target_identity"),
                        "root_override_reason": envelope.get("root_override_reason"),
                        "turn_id": turn.get("id"),
                        "turn_status": turn.get("status"),
                    }
                )
        return records

    @classmethod
    def _latest_protocol_work_id(cls, turns: Any) -> str | None:
        if not isinstance(turns, list):
            return None
        for turn in reversed(turns):
            if not isinstance(turn, Mapping):
                continue
            documents = cls._protocol_documents(turn.get("items", []), None)
            if documents:
                return str(documents[-1]["work_id"])
        return None

    @staticmethod
    def _target_runtime(target_identity: str) -> dict[str, str] | None:
        manager = AppServerClient._canonical_manager(target_identity)
        if manager is not None and manager["kind"] in {"portfolio", "em"}:
            return {"model": "gpt-5.6-sol", "effort": "max"}
        if manager is not None and manager["kind"] == "cm":
            return {"model": "gpt-5.6-sol", "effort": "high"}
        return None

    @staticmethod
    def _canonical_manager(
        identity: Any, generation: int | None = None
    ) -> dict[str, Any] | None:
        if identity == "Portfolio":
            kind, direction_id = "portfolio", None
        elif isinstance(identity, str):
            matched = re.fullmatch(
                r"(EM|CM)-([a-z0-9][a-z0-9_-]{1,63})", identity
            )
            if matched is None:
                return None
            kind, direction_id = matched.group(1).lower(), matched.group(2)
        else:
            return None
        if generation is not None and (
            not isinstance(generation, int)
            or isinstance(generation, bool)
            or generation < 1
        ):
            return None
        return {
            "logical_identity": identity,
            "kind": kind,
            "direction_id": direction_id,
            "thread_source": (
                None
                if generation is None
                else f"hmasd-manager:{identity}:g{generation}"
            ),
        }

    def send(
        self,
        thread_id: str,
        work_id: str,
        packet_locator: str,
        target_identity: str,
        *,
        max_attempts: int = 3,
        root_override_reason: str | None = None,
        expected_cwd: str | None = None,
        expected_thread_source: str | None = None,
        require_thread_source: bool = False,
        participant_contract: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        read = self._read_thread_full(thread_id)
        if read["status"] != "OK":
            return read
        thread = read["thread"]
        observed_thread_source = thread.get("threadSource")
        thread_source_changed = (
            isinstance(observed_thread_source, str)
            and observed_thread_source.startswith("hmasd-manager:")
            and expected_thread_source is None
        ) or (
            expected_thread_source is not None
            and (
                observed_thread_source != expected_thread_source
                if require_thread_source
                else (
                    isinstance(observed_thread_source, str)
                    and observed_thread_source.startswith("hmasd-manager:")
                    and observed_thread_source != expected_thread_source
                )
            )
        )
        if expected_cwd is not None and (
            thread.get("id") != thread_id
            or thread.get("name") != target_identity
            or not self._same_cwd(thread.get("cwd"), expected_cwd)
            or thread_source_changed
        ):
            return {
                "status": "TASK_IDENTITY_CONFLICT",
                "reason": "FINAL_THREAD_IDENTITY_CHANGED",
                "target_identity": target_identity,
                "thread_id": thread_id,
                "observed_thread_id": thread.get("id"),
                "observed_name": thread.get("name"),
                "observed_cwd": thread.get("cwd"),
                "observed_thread_source": observed_thread_source,
            }
        history = thread.get("turns", [])
        records = self._attempt_records(history, work_id)
        invariant_conflict = any(
            record.get("packet_locator") != packet_locator
            or record.get("target_identity") != target_identity
            or not isinstance(record.get("attempt"), int)
            or record.get("mode")
            != ("DISPATCH" if record.get("attempt") == 1 else "RESUME")
            for record in records
        )
        attempts = [record.get("attempt") for record in records]
        if invariant_conflict or len(set(attempts)) != len(attempts):
            return {
                "status": "DELIVERY_CONFLICT",
                "thread_id": thread_id,
                "work_id": work_id,
            }
        ordered = sorted(records, key=lambda item: item["attempt"])
        if ordered and [item["attempt"] for item in ordered] != list(
            range(1, len(ordered) + 1)
        ):
            return {
                "status": "DELIVERY_CONFLICT",
                "thread_id": thread_id,
                "work_id": work_id,
            }
        latest = ordered[-1] if ordered else None
        if latest is not None and latest.get("turn_status") == "inProgress":
            return {
                "status": "ALREADY_DELIVERED",
                "thread_id": thread_id,
                "work_id": work_id,
                "attempt": latest["attempt"],
                "turn_id": latest.get("turn_id"),
                "turn_status": latest.get("turn_status"),
            }
        terminal_statuses = {"completed", "failed", "interrupted"}
        if latest is not None and latest.get("turn_status") not in terminal_statuses:
            return {
                "status": "DELIVERY_STATE_UNKNOWN",
                "thread_id": thread_id,
                "work_id": work_id,
                "attempt": latest["attempt"],
                "turn_id": latest.get("turn_id"),
                "turn_status": latest.get("turn_status"),
            }
        attempt = 1 if latest is None else latest["attempt"] + 1
        if attempt > max_attempts:
            return {
                "status": "RETURN_WITNESS_MISSING_AFTER_ATTEMPTS",
                "thread_id": thread_id,
                "work_id": work_id,
                "attempt_statuses": [
                    {
                        "attempt": item["attempt"],
                        "turn_id": item.get("turn_id"),
                        "turn_status": item.get("turn_status"),
                    }
                    for item in ordered
                ],
                "resume_condition": {
                    "latest_turn_terminal": True,
                    "return_witness": "ABSENT",
                    "next_attempt": attempt,
                    "max_attempts": max_attempts,
                    "attempt_below_max": False,
                },
            }
        mode = "DISPATCH" if attempt == 1 else "RESUME"
        envelope = dispatch_envelope_bytes(
            work_id,
            packet_locator,
            target_identity,
            attempt=attempt,
            mode=mode,
            root_override_reason=root_override_reason,
        ).decode("utf-8")
        resumed = self._request(
            "thread/resume",
            {
                "threadId": thread_id,
                "approvalPolicy": "never",
                "sandbox": "danger-full-access",
            },
        )
        if resumed["status"] != "OK":
            return resumed
        inputs: list[dict[str, Any]] = [{"type": "text", "text": envelope}]
        if attempt == 1:
            inputs.append({"type": "text", "text": _PARTICIPANT_SLICE_INSTRUCTION})
        if participant_contract is not None:
            inputs.append(
                {
                    "type": "text",
                    "text": json.dumps(
                        participant_contract,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                }
            )
        turn_params: dict[str, Any] = {
            "threadId": thread_id,
            "input": inputs,
            "approvalPolicy": "never",
            "sandboxPolicy": {"type": "dangerFullAccess"},
        }
        runtime = self._target_runtime(target_identity)
        if runtime is not None:
            turn_params["effort"] = runtime["effort"]
        response = self._request(
            "turn/start",
            turn_params,
            after_send=True,
        )
        if response["status"] != "OK":
            if response.get("status") == "UNKNOWN":
                observed = self._read_thread_full(thread_id)
                if observed.get("status") == "OK":
                    observed_records = self._attempt_records(
                        observed["thread"].get("turns", []), work_id
                    )
                    exact = next(
                        (
                            record
                            for record in observed_records
                            if record.get("attempt") == attempt
                            and record.get("packet_locator") == packet_locator
                            and record.get("target_identity") == target_identity
                        ),
                        None,
                    )
                    if exact is not None:
                        return {
                            "status": "DELIVERY_OBSERVED_AFTER_UNKNOWN",
                            "reason": response.get("reason", "UNKNOWN_AFTER_SEND"),
                            "thread_id": thread_id,
                            "turn_id": exact.get("turn_id"),
                            "turn_status": exact.get("turn_status"),
                            "work_id": work_id,
                            "attempt": attempt,
                        }
            return response
        turn_id = response["result"].get("turn", {}).get("id")
        if not isinstance(turn_id, str) or not turn_id:
            return {"status": "UNKNOWN", "reason": "MISSING_TURN_ID_AFTER_SEND"}
        return {
            "status": "DELIVERED",
            "attempt": attempt,
            "mode": mode,
            "thread_id": thread_id,
            "turn_id": turn_id,
            "work_id": work_id,
        }

    @staticmethod
    def _terminal_fact(thread_id: str, turn: Mapping[str, Any]) -> dict[str, Any]:
        status = turn.get("status")
        fact = {
            "status": "COMPLETED" if status == "completed" else "TERMINAL",
            "thread_id": thread_id,
            "turn_id": turn.get("id"),
            "turn_status": status,
        }
        error = turn.get("error")
        capacity_error = (
            error.get("codexErrorInfo") if isinstance(error, Mapping) else None
        )
        if status == "failed" and capacity_error in _CAPACITY_ERRORS:
            fact["capacity_error"] = capacity_error
        return fact

    def observe(self, thread_id: str, turn_id: str | None = None) -> dict[str, Any]:
        read = self.read_thread(thread_id)
        if read["status"] != "OK":
            return read
        turns = read["thread"].get("turns", [])
        selected = None
        for turn in turns:
            if isinstance(turn, Mapping) and (turn_id is None or turn.get("id") == turn_id):
                selected = turn
        if selected is None:
            return {"status": "NOT_OBSERVED", "thread_id": thread_id, "turn_id": turn_id}
        if selected.get("status") in {"completed", "failed", "interrupted"}:
            return self._terminal_fact(thread_id, selected)
        return {
            "status": "IN_FLIGHT",
            "thread_id": thread_id,
            "turn_id": selected.get("id"),
            "turn_status": selected.get("status"),
        }

    def wait(
        self,
        thread_id: str,
        turn_id: str,
        *,
        timeout: float | None,
        resume_sandbox: str = "danger-full-access",
        resume: bool = True,
        observe_active: bool = True,
    ) -> dict[str, Any]:
        if observe_active:
            observed = self.observe(thread_id, turn_id)
            if observed["status"] in {"COMPLETED", "TERMINAL"}:
                return observed
        if resume:
            resumed = self._request(
                "thread/resume",
                {
                    "threadId": thread_id,
                    "approvalPolicy": "never",
                    "sandbox": resume_sandbox,
                },
            )
            if resumed["status"] != "OK":
                return resumed
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            for index, notification in enumerate(self._notifications):
                params = notification.get("params", {})
                turn = params.get("turn", {}) if isinstance(params, Mapping) else {}
                if (
                    notification.get("method") == "turn/completed"
                    and params.get("threadId") in {None, thread_id}
                    and turn.get("id") == turn_id
                ):
                    del self._notifications[index]
                    return self._terminal_fact(thread_id, turn)
            if deadline is not None and time.monotonic() >= deadline:
                return {"status": "WAIT_TIMEOUT", "thread_id": thread_id, "turn_id": turn_id}
            read_deadline = (
                time.monotonic() + self.timeout if deadline is None else deadline
            )
            read = self._read(read_deadline, after_send=False)
            if read["status"] != "MESSAGE":
                if read["status"] == "TIMEOUT":
                    if not observe_active:
                        if deadline is None:
                            continue
                        return {
                            "status": "WAIT_TIMEOUT",
                            "thread_id": thread_id,
                            "turn_id": turn_id,
                        }
                    final = self.observe(thread_id, turn_id)
                    if final["status"] in {"COMPLETED", "TERMINAL"}:
                        return final
                    if deadline is None:
                        continue
                    return {
                        "status": "WAIT_TIMEOUT",
                        "thread_id": thread_id,
                        "turn_id": turn_id,
                    }
                return read
            message = read["message"]
            if "method" in message and message.get("id") is not None:
                return {"status": "INTERVENTION_REQUIRED", "reason": "SERVER_REQUEST"}
            if "method" in message:
                self._notifications.append(message)
            elif isinstance(message.get("id"), int):
                self._pending_responses[message["id"]] = message

    @staticmethod
    def _same_cwd(left: Any, right: str) -> bool:
        if not isinstance(left, str):
            return False
        return os.path.normcase(os.path.abspath(left)) == os.path.normcase(
            os.path.abspath(right)
        )

    @staticmethod
    def _task_rows(observed_tasks: Any) -> list[Mapping[str, Any]]:
        rows = observed_tasks.get("tasks", []) if isinstance(observed_tasks, Mapping) else observed_tasks
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            raise ValueError("observed_tasks must contain a task sequence")
        return [row for row in rows if isinstance(row, Mapping)]

    @classmethod
    def _active_task_rows(cls, observed_tasks: Any) -> list[Mapping[str, Any]]:
        return [
            row
            for row in cls._task_rows(observed_tasks)
            if str(row.get("lifecycle", row.get("status", ""))).upper()
            in {"ACTIVE", "RUNNING"}
        ]

    @staticmethod
    def _native_lifecycle(status: Any) -> str | None:
        state = (
            str(status.get("type", "")).replace("-", "").lower()
            if isinstance(status, Mapping)
            else str(status).replace("-", "").lower()
        )
        if state in {"active", "running", "inprogress"}:
            return "ACTIVE"
        if state == "idle":
            return "PARKED"
        if state in {"completed", "failed", "interrupted"}:
            return "COMPLETED"
        return None

    @classmethod
    def _native_task_snapshot(
        cls,
        rows: Sequence[Mapping[str, Any]],
        prior_tasks: Sequence[Mapping[str, Any]],
        *,
        include_unlisted: bool = True,
    ) -> list[dict[str, Any]]:
        prior_by_thread = {
            str(task.get("thread_id", task.get("session_id"))): dict(task)
            for task in prior_tasks
            if isinstance(task.get("thread_id", task.get("session_id")), str)
        }
        snapshot_by_thread = dict(prior_by_thread) if include_unlisted else {}
        for row in rows:
            thread_id = row.get("id")
            if not isinstance(thread_id, str) or not thread_id:
                continue
            task = dict(prior_by_thread.get(thread_id, {}))
            identity = row.get("name")
            if isinstance(identity, str) and identity:
                task["logical_identity"] = identity
            elif not isinstance(task.get("logical_identity"), str):
                continue
            identity = str(task["logical_identity"])
            task["thread_id"] = thread_id
            lifecycle = cls._native_lifecycle(row.get("status"))
            prior_lifecycle = task.get("lifecycle")
            if lifecycle is not None:
                if (
                    isinstance(prior_lifecycle, str)
                    and prior_lifecycle != lifecycle
                    and prior_lifecycle != "CREATED"
                ):
                    task["lifecycle"] = "CONFLICT"
                else:
                    task["lifecycle"] = lifecycle
            manager = cls._canonical_manager(identity)
            if manager is not None:
                task.setdefault("kind", manager["kind"])
                if manager["direction_id"] is not None:
                    task.setdefault("direction_id", manager["direction_id"])
                thread_source = row.get("threadSource")
                source_match = (
                    re.fullmatch(
                        rf"hmasd-manager:{re.escape(identity)}:g([1-9][0-9]*)",
                        thread_source,
                    )
                    if isinstance(thread_source, str)
                    else None
                )
                if source_match is not None:
                    native_generation = int(source_match.group(1))
                    projected_generation = task.get("generation")
                    if projected_generation is not None and (
                        not isinstance(projected_generation, int)
                        or isinstance(projected_generation, bool)
                        or projected_generation != native_generation
                    ):
                        task.pop("generation", None)
                        task["generation_conflict"] = {
                            "logical_identity": identity,
                            "thread_id": thread_id,
                            "projected_generation": projected_generation,
                            "native_generation": native_generation,
                            "thread_source": thread_source,
                        }
                        task["lifecycle"] = "CONFLICT"
                    else:
                        task["generation"] = native_generation
            snapshot_by_thread[thread_id] = task
        return [snapshot_by_thread[key] for key in sorted(snapshot_by_thread)]

    @staticmethod
    def _generation_conflicts(
        tasks: Sequence[Mapping[str, Any]],
        *,
        target_identity: str,
    ) -> list[dict[str, Any]]:
        return [
            dict(task["generation_conflict"])
            for task in tasks
            if isinstance(task.get("generation_conflict"), Mapping)
            and task["generation_conflict"].get("logical_identity")
            == target_identity
        ]

    def _read_known_identity(
        self,
        thread_id: str,
        *,
        target_identity: str,
        cwd: str,
    ) -> dict[str, Any]:
        full = self._read_thread_full(thread_id)
        if full.get("status") != "OK":
            return full
        thread = full.get("thread", {})
        observed_name = thread.get("name") if isinstance(thread, Mapping) else None
        if (
            not isinstance(thread, Mapping)
            or thread.get("id") != thread_id
            or observed_name != target_identity
            or not self._same_cwd(thread.get("cwd"), cwd)
        ):
            return {
                "status": "TASK_IDENTITY_CONFLICT",
                "target_identity": target_identity,
                "thread_id": thread_id,
                "observed_name": observed_name,
            }
        return full

    @staticmethod
    def _native_thread_activity(thread: Any) -> str:
        """Return whether native state still makes a runtime peer live.

        Runtime task rows are durable intent/projection facts, so an old ACTIVE
        row alone cannot keep a completed native thread in the dispatch set.
        A native active thread or an in-progress native turn is sufficient.
        """
        if not isinstance(thread, Mapping):
            return "UNKNOWN"
        turns = thread.get("turns", [])
        if isinstance(turns, list) and any(
            isinstance(turn, Mapping)
            and str(turn.get("status", "")).replace("-", "").lower()
            == "inprogress"
            for turn in turns
        ):
            return "ACTIVE"
        status = thread.get("status")
        state = str(status.get("type", "")).replace("-", "").lower() if isinstance(status, Mapping) else ""
        if state in {"active", "running", "inprogress"}:
            return "ACTIVE"
        if state in {"idle", "completed", "failed", "interrupted", "terminal"}:
            return "INACTIVE"
        return "UNKNOWN"

    @contextmanager
    def _dispatch_lock(self, repo: Path):
        lock_path = repo / ".codex" / "runtime" / "work" / "locks" / "native-dispatch.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+b") as stream:
            with hmasd_platform.exclusive_file_lock(stream.fileno()):
                yield

    def _peer_work_ids(
        self,
        observed_tasks: Any,
        explicit: Sequence[str],
        *,
        current_thread_id: str | None,
    ) -> tuple[list[str], list[str]]:
        work_ids = list(explicit)
        unknown_threads: list[str] = []
        if observed_tasks is not None:
            for row in self._active_task_rows(observed_tasks):
                peer_thread = row.get("thread_id", row.get("session_id"))
                if not isinstance(peer_thread, str) or not peer_thread:
                    unknown_threads.append("MISSING_THREAD_ID")
                    continue
                if peer_thread == current_thread_id:
                    continue
                full = self._read_thread_full(peer_thread)
                if full.get("status") != "OK":
                    unknown_threads.append(peer_thread)
                    continue
                activity = self._native_thread_activity(full.get("thread"))
                if activity == "INACTIVE":
                    continue
                if activity == "UNKNOWN":
                    unknown_threads.append(peer_thread)
                    continue
                work_id = self._latest_protocol_work_id(full["thread"].get("turns", []))
                if work_id is not None:
                    work_ids.append(work_id)
                else:
                    unknown_threads.append(peer_thread)
        return sorted(set(work_ids)), sorted(set(unknown_threads))

    @classmethod
    def _terminal_attempt_needs_return_observation(
        cls,
        thread: Mapping[str, Any],
        work_id: str,
        packet_locator: str,
        target_identity: str,
    ) -> bool:
        records = cls._attempt_records(thread.get("turns", []), work_id)
        if not records:
            return False
        if any(
            record.get("packet_locator") != packet_locator
            or record.get("target_identity") != target_identity
            or not isinstance(record.get("attempt"), int)
            or isinstance(record.get("attempt"), bool)
            or record.get("mode")
            != ("DISPATCH" if record.get("attempt") == 1 else "RESUME")
            for record in records
        ):
            return False
        attempts = [record["attempt"] for record in records]
        if len(set(attempts)) != len(attempts):
            return False
        ordered = sorted(records, key=lambda item: item["attempt"])
        if [item["attempt"] for item in ordered] != list(range(1, len(ordered) + 1)):
            return False
        latest = ordered[-1]
        return (
            latest.get("turn_status") in {"completed", "failed", "interrupted"}
        )

    @classmethod
    def _history_recovery_binding(
        cls,
        *,
        work_id: str,
        canonical_locator: str,
        cwd: str,
        full_native_rows: Sequence[Mapping[str, Any]],
        raw_projected_tasks: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any] | None:
        conflict = {"status": "TASK_IDENTITY_CONFLICT",
                    "reason": "HISTORY_RECOVERY_BINDING_CONFLICT", "work_id": work_id}
        candidates = [(row, manager, records) for row in full_native_rows
                      if cls._same_cwd(row.get("cwd"), cwd)
                      and cls._native_lifecycle(row.get("status")) == "COMPLETED"
                      and (manager := cls._canonical_manager(row.get("name"))) is not None
                      and (records := cls._attempt_records(row.get("turns", []), work_id))]
        if not candidates:
            return None
        if len(candidates) != 1:
            return conflict
        row, manager, records = candidates[0]
        target = row.get("name")
        thread_id = row.get("id")
        source = row.get("threadSource")
        source_match = (re.fullmatch(
            rf"hmasd-manager:{re.escape(str(target))}:g([1-9][0-9]*)", source
        ) if isinstance(source, str) else None)
        if (not isinstance(thread_id, str) or not thread_id or source_match is None
                or not cls._terminal_attempt_needs_return_observation(
                    row, work_id, canonical_locator, str(target))):
            return conflict
        generation = int(source_match.group(1))
        ordered = sorted(records, key=lambda item: item["attempt"])
        cached = [task for task in raw_projected_tasks
                  if task.get("thread_id") == thread_id]
        expected = (target, manager["kind"], manager["direction_id"], generation)
        if (len(cached) > 1 or cached and (
                tuple(cached[0].get(key) for key in
                      ("logical_identity", "kind", "direction_id", "generation")) != expected
                or cached[0].get("lifecycle") == "RETIRED"
                or isinstance(cached[0].get("generation_conflict"), Mapping))):
            return conflict
        return {"work_id": work_id, "packet_locator": canonical_locator,
            "target_identity": target, "thread_id": thread_id,
            "generation": generation, "thread_source": source,
            "attempt_count": len(ordered),
            "attempt_statuses": [{"attempt": item["attempt"],
                "turn_id": item.get("turn_id"), "turn_status": item.get("turn_status")}
                for item in ordered]}

    @staticmethod
    def _validated_return_fact(
        *,
        repo: Path,
        work_id: str,
        observed_tasks: Sequence[Mapping[str, Any]],
        thread_id: str,
        terminal: Mapping[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        try:
            return_plan = hmasd_work_packet.reconcile_once(
                repo=repo,
                work_id=work_id,
                observed_tasks=observed_tasks,
            )["plan"]
        except (hmasd_work_packet.InvalidPacket, hmasd_work_packet.PacketConflict):
            return {
                "status": "PROTOCOL_DEFECT",
                "reason": "RETURN_WITNESS_INVALID",
                "work_id": work_id,
                "thread_id": thread_id,
            }
        if return_plan.get("verb") == "OBSERVE_EFFECT_ONLY":
            try:
                witness = hmasd_work_packet.read_return(repo=repo, work_id=work_id)
            except (hmasd_work_packet.InvalidPacket, hmasd_work_packet.PacketConflict):
                witness = None
            result: dict[str, Any] = {
                "status": "NO_EFFECT",
                "verb": "OBSERVE_EFFECT_ONLY",
                "work_id": work_id,
                "thread_id": thread_id,
                "unknown_effect_refs": return_plan.get("unknown_effect_refs", []),
            }
            if witness is not None:
                result["return_witness"] = witness
            if terminal is not None:
                result.update(
                    {
                        "turn_id": terminal.get("turn_id"),
                        "turn_status": terminal.get("turn_status"),
                    }
                )
            return result
        return_resolution = return_plan.get("task_resolution", {})
        if return_resolution.get("status") != "RETURN_WITNESS":
            if return_plan.get("verb") in _DISPATCH_VERBS:
                return None
            return {
                "status": "PROTOCOL_DEFECT",
                "reason": "RETURN_WITNESS_INVALID",
                "work_id": work_id,
                "thread_id": thread_id,
            }
        try:
            witness = hmasd_work_packet.read_return(repo=repo, work_id=work_id)
        except (hmasd_work_packet.InvalidPacket, hmasd_work_packet.PacketConflict):
            witness = None
        if witness is None:
            return {
                "status": "PROTOCOL_DEFECT",
                "reason": "RETURN_WITNESS_INVALID",
                "work_id": work_id,
                "thread_id": thread_id,
            }
        result = {
            "status": witness["agent_result"]["status"],
            "reason": "RETURN_WITNESS_PRESENT",
            "work_id": work_id,
            "thread_id": thread_id,
            "return_witness": witness,
        }
        if terminal is not None:
            result.update(
                {
                    "turn_id": terminal.get("turn_id"),
                    "turn_status": terminal.get("turn_status"),
                }
            )
        return result

    @staticmethod
    def _override_allows_compare(compare: Mapping[str, Any]) -> bool:
        if compare.get("outcome") != "CONFLICT":
            return False
        reasons = [
            reason
            for pair in compare.get("pairs", [])
            if isinstance(pair, Mapping)
            for reason in pair.get("reasons", [])
            if isinstance(reason, Mapping)
        ]
        return bool(reasons) and all(
            reason.get("type") == "OWNED_PATH_OVERLAP" for reason in reasons
        ) and not compare.get("packet_conflicts")

    @staticmethod
    def _cm_operator_assignment(
        *, repo: Path, work_id: str, packet_locator: str, target_identity: str
    ) -> dict[str, Any] | None:
        """Freeze one existing run manifest into the CM's leaf assignment."""

        if not target_identity.startswith("CM-"):
            return None
        relative = _relative_posix_path(packet_locator)
        packet_path = (repo / Path(*relative.split("/"))).resolve()
        try:
            packet_path.relative_to(repo.resolve())
            packet_document = json.loads(packet_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError(f"CM packet is unreadable: {exc}") from exc
        packet = hmasd_work_packet.validate_packet(packet_document, repo=repo)
        if packet.get("work_id") != work_id or packet.get("target_identity") != target_identity:
            raise ValueError("CM packet identity does not match the closed plan")
        run_effects = [
            effect
            for effect in packet.get("effect_refs", [])
            if isinstance(effect, Mapping)
            and effect.get("kind") == "run_manifest"
            and effect.get("operation") == "EXECUTE"
        ]
        if not run_effects:
            return None
        if len(run_effects) != 1:
            raise ValueError("CM assignment must bind exactly one executable run manifest")
        manifest_locator = _relative_posix_path(str(run_effects[0].get("path", "")))
        manifest_path = (repo / Path(*manifest_locator.split("/"))).resolve()
        try:
            manifest_path.relative_to(repo.resolve())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError(f"run manifest is unreadable: {exc}") from exc
        run_id = manifest.get("run_id")
        assignment_id = manifest.get("assignment_id")
        command = manifest.get("command")
        run_cwd = manifest.get("cwd")
        run_owner = f"Operator-{run_id}"
        if (
            not isinstance(run_id, str)
            or _IDENTITY.fullmatch(run_id) is None
            or not isinstance(assignment_id, str)
            or not assignment_id
            or not isinstance(command, list)
            or not command
            or not all(isinstance(part, str) for part in command)
            or not isinstance(run_cwd, str)
            or not Path(run_cwd).is_absolute()
            or manifest.get("writer") != run_owner
            or manifest.get("operator_identity") != run_owner
            or manifest.get("status")
            not in {"PREPARED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED", "UNKNOWN"}
        ):
            raise ValueError("run manifest does not freeze a valid Operator assignment")
        run_script = Path(__file__).with_name("hmasd_run.py").resolve()
        task_suffix = re.sub(r"[^a-z0-9]+", "_", run_id.lower()).strip("_")
        task_digest = hmasd_state.sha256_bytes(run_id.encode("utf-8"))[:10]
        outputs = manifest.get("outputs", {})
        try:
            stdout_ref = (manifest_path.parent / outputs["stdout"]).relative_to(repo).as_posix()
            stderr_ref = (manifest_path.parent / outputs["stderr"]).relative_to(repo).as_posix()
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("run manifest output refs are invalid") from exc
        assignment = {
            "assignment_id": assignment_id,
            "command": command,
            "cwd": run_cwd,
            "execute_argv": [
                sys.executable,
                str(run_script),
                "execute",
                "--manifest",
                str(manifest_path),
            ],
            "logical_identity": _OPERATOR_ROLE,
            "agent_role": _OPERATOR_ROLE,
            "manifest": manifest_locator,
            "output_root": str(manifest_path.parent),
            "parent_identity": target_identity,
            "protocol": OPERATOR_ASSIGNMENT_MARKER,
            "run_id": run_id,
            "run_owner": run_owner,
            "result_contract": {
                "artifact_refs": [stdout_ref, stderr_ref],
                "assignment_id": assignment_id, "generation": 1,
                "logical_identity": _OPERATOR_ROLE,
                "role": _OPERATOR_ROLE, "run_id": run_id,
                "schema_path": "scripts/schemas/hmasd_agent_result.schema.json",
                "state_refs": [manifest_locator],
                "verification_refs": [manifest_locator, stdout_ref, stderr_ref],
                "work_id": work_id,
            },
            "task_name": f"native_ll_{task_suffix}_{task_digest}",
        }
        marker = manifest.get("parameters", {}).get("expected_stdout_marker")
        assignment.update({"expected_stdout_marker": marker} if isinstance(marker, str) and marker else {})
        return assignment

    @staticmethod
    def _json_documents(value: Any) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        if isinstance(value, Mapping):
            text_value = value.get("text")
            if (
                value.get("type") in {"text", "input_text", "output_text"}
                and isinstance(text_value, str)
            ):
                found.extend(
                    AppServerClient._strict_text_documents(
                        text_value, include_composite_suffix=True
                    )
                )
            for item in value.values():
                found.extend(AppServerClient._json_documents(item))
        elif isinstance(value, list):
            for item in value:
                found.extend(AppServerClient._json_documents(item))
        return found

    def _observe_operator_child(
        self,
        rows: Sequence[Mapping[str, Any]],
        *,
        parent_thread_id: str,
        assignment: Mapping[str, Any],
    ) -> dict[str, Any]:
        def stopped(status: str, reason: str, thread_id: str | None = None) -> dict[str, Any]:
            result = {"status": status, "reason": reason}
            if thread_id is not None:
                result["thread_id"] = thread_id
            return result

        candidate_ids: list[str] = []
        exact: list[dict[str, Any]] = []
        for row in rows:
            if (
                row.get("parentThreadId") != parent_thread_id
                or row.get("agentRole") != _OPERATOR_ROLE
            ):
                continue
            thread_id = row.get("id")
            if not isinstance(thread_id, str) or not thread_id:
                return stopped("UNKNOWN", "OPERATOR_CHILD_ID_UNKNOWN")
            if thread_id not in candidate_ids:
                candidate_ids.append(thread_id)

        parent_read = self._read_thread_full(parent_thread_id)
        if parent_read.get("status") != "OK":
            return stopped("UNKNOWN", "OPERATOR_PARENT_READ_UNKNOWN", parent_thread_id)
        parent = parent_read["thread"]
        if parent.get("id") != parent_thread_id:
            return stopped(
                "TASK_IDENTITY_CONFLICT", "OPERATOR_PARENT_IDENTITY_CHANGED",
                parent_thread_id,
            )
        turns = parent.get("turns")
        if not isinstance(turns, list):
            return stopped("UNKNOWN", "OPERATOR_PARENT_HISTORY_UNKNOWN", parent_thread_id)
        for turn in turns:
            if not isinstance(turn, Mapping) or "items" not in turn:
                return stopped("UNKNOWN", "OPERATOR_PARENT_ACTIVITY_INVALID", parent_thread_id)
            items = turn["items"]
            if not isinstance(items, list):
                return stopped("UNKNOWN", "OPERATOR_PARENT_ACTIVITY_INVALID", parent_thread_id)
            for item in items:
                if not isinstance(item, Mapping) or (
                    item.get("type") != "subAgentActivity"
                    or item.get("kind") != "started"
                ):
                    continue
                child_id = item.get("agentThreadId")
                agent_path = item.get("agentPath")
                if (
                    not isinstance(child_id, str) or not child_id
                    or not isinstance(agent_path, str) or not agent_path
                ):
                    return stopped("UNKNOWN", "OPERATOR_PARENT_ACTIVITY_INVALID", parent_thread_id)
                if child_id not in candidate_ids:
                    candidate_ids.append(child_id)

        for thread_id in candidate_ids:
            read = self._read_thread_full(thread_id)
            if read.get("status") != "OK":
                return stopped("UNKNOWN", "OPERATOR_CHILD_READ_UNKNOWN", thread_id)
            thread = read["thread"]
            if (
                thread.get("id") != thread_id
                or thread.get("parentThreadId") != parent_thread_id
            ):
                return stopped(
                    "TASK_IDENTITY_CONFLICT", "OPERATOR_CHILD_IDENTITY_CHANGED", thread_id
                )
            if thread.get("agentRole") != _OPERATOR_ROLE:
                continue
            documents = [
                document
                for document in self._json_documents(thread.get("turns", []))
                if document.get("protocol") == OPERATOR_ASSIGNMENT_MARKER
                and document.get("agent_role") == _OPERATOR_ROLE
            ]
            if not documents:
                return stopped("UNKNOWN", "OPERATOR_CHILD_RUN_BINDING_UNKNOWN", thread_id)
            run_ids = {document.get("run_id") for document in documents}
            if assignment["run_id"] in run_ids:
                exact.append(thread)
        if len(exact) > 1:
            return {
                "status": "TASK_IDENTITY_CONFLICT",
                "reason": "MULTIPLE_OPERATOR_CHILDREN_FOR_RUN",
                "thread_ids": sorted(str(thread["id"]) for thread in exact),
            }
        if not exact:
            return {"status": "CREATE_EXACT"}
        return {
            "status": "RESUME_EXACT",
            "thread_id": exact[0]["id"],
            "thread": exact[0],
            "assignment": next(
                document
                for document in self._json_documents(exact[0].get("turns", []))
                if document.get("protocol") == OPERATOR_ASSIGNMENT_MARKER
                and document.get("agent_role") == _OPERATOR_ROLE
                and document.get("run_id") == assignment["run_id"]
            ),
        }

    @staticmethod
    def _operator_evidence_error(reason: str) -> dict[str, Any]:
        return {"status": "OPERATOR_EVIDENCE_INVALID", "reason": reason}

    @classmethod
    def _validate_operator_evidence(
        cls,
        *,
        repo: Path,
        observation: Mapping[str, Any],
        assignment: Mapping[str, Any],
    ) -> dict[str, Any]:
        thread = observation["thread"]
        turns = thread.get("turns")
        if not isinstance(turns, list) or not turns or turns[-1].get("status") != "completed":
            return cls._operator_evidence_error("OPERATOR_CHILD_NOT_TERMINAL")
        frozen = observation["assignment"]
        bound = ("assignment_id", "agent_role", "command", "cwd", "logical_identity",
                 "manifest", "output_root", "parent_identity", "protocol", "result_contract",
                 "run_id", "run_owner")
        if any(frozen.get(key) != assignment.get(key) for key in bound):
            return cls._operator_evidence_error("OPERATOR_ASSIGNMENT_CHANGED")
        results = [document for document in cls._json_documents(turns[-1].get("items", []))
                   if document.get("schema_version") == 1 and "payload" in document]
        if not results:
            return cls._operator_evidence_error("OPERATOR_RESULT_MISSING")
        if len(results) > 1:
            return cls._operator_evidence_error("OPERATOR_RESULT_AMBIGUOUS")
        result = results[0]
        if result.get("role") != _OPERATOR_ROLE or result.get("logical_identity") != _OPERATOR_ROLE:
            return cls._operator_evidence_error("OPERATOR_RESULT_IDENTITY_MISMATCH")
        try:
            hmasd_state.validate_document("agent_result", result)
        except hmasd_state.StateError:
            return cls._operator_evidence_error("OPERATOR_RESULT_SCHEMA_INVALID")
        payload = result["payload"]
        if (
            result.get("assignment_id") != assignment["assignment_id"]
            or result.get("generation") != assignment["result_contract"]["generation"]
            or result.get("status") != "COMPLETED"
            or payload.get("run_id") != assignment["run_id"]
            or payload.get("terminal_status") != "SUCCEEDED"
            or payload.get("exit_code") != 0
        ):
            return cls._operator_evidence_error("OPERATOR_RESULT_BINDING_MISMATCH")
        manifest_ref = payload.get("manifest_ref")
        if not isinstance(manifest_ref, Mapping) or manifest_ref.get("path") != assignment["manifest"]:
            return cls._operator_evidence_error("OPERATOR_MANIFEST_REF_MISMATCH")
        refs = [*result.get("state_refs", []), *result.get("artifact_refs", [])]
        for reference in refs:
            if not isinstance(reference, Mapping) or set(reference) != {"path", "sha256"}:
                return cls._operator_evidence_error("OPERATOR_RESULT_REF_INVALID")
            path = repo / Path(*_relative_posix_path(str(reference["path"])).split("/"))
            try:
                if not path.is_file() or hmasd_state.sha256_file(path) != reference["sha256"]:
                    return cls._operator_evidence_error("OPERATOR_RESULT_REF_STALE")
            except OSError:
                return cls._operator_evidence_error("OPERATOR_RESULT_REF_STALE")
        manifest_path = repo / Path(*str(assignment["manifest"]).split("/"))
        if manifest_ref not in refs or hmasd_state.sha256_file(manifest_path) != manifest_ref["sha256"]:
            return cls._operator_evidence_error("OPERATOR_MANIFEST_REF_STALE")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls._operator_evidence_error("OPERATOR_MANIFEST_INVALID")
        process = manifest.get("process", {})
        frozen_manifest = (manifest.get("writer"), manifest.get("operator_identity"),
                           manifest.get("run_id"), manifest.get("assignment_id"),
                           manifest.get("command"), manifest.get("cwd"), str(manifest_path.parent))
        expected_manifest = (assignment["run_owner"], assignment["run_owner"],
                             assignment["run_id"], assignment["assignment_id"],
                             assignment["command"], assignment["cwd"], assignment["output_root"])
        if (frozen_manifest != expected_manifest or manifest.get("status") != "SUCCEEDED"
                or process.get("exit_code") != 0 or process.get("group_quiescent") is not True):
            return cls._operator_evidence_error("OPERATOR_MANIFEST_TERMINAL_MISMATCH")
        stdout_path = manifest_path.parent / str(manifest.get("outputs", {}).get("stdout", ""))
        stdout_rel = stdout_path.relative_to(repo).as_posix()
        if not any(reference.get("path") == stdout_rel for reference in result["artifact_refs"]):
            return cls._operator_evidence_error("OPERATOR_STDOUT_REF_MISSING")
        marker = assignment.get("expected_stdout_marker")
        if isinstance(marker, str) and stdout_path.read_text(encoding="utf-8").count(marker) != 1:
            return cls._operator_evidence_error("OPERATOR_STDOUT_MARKER_MISMATCH")
        stderr_path = manifest_path.parent / str(manifest.get("outputs", {}).get("stderr", ""))
        by_path = {reference["path"]: reference for reference in refs}
        expected_refs = [manifest_ref, by_path.get(stdout_rel), by_path.get(stderr_path.relative_to(repo).as_posix())]
        if any(reference is None for reference in expected_refs):
            return cls._operator_evidence_error("OPERATOR_REQUIRED_REF_MISSING")
        return {"status": "VALID", "thread_id": observation["thread_id"], "refs": expected_refs}

    @classmethod
    def _completed_operator_return(
        cls,
        *,
        repo: Path,
        return_fact: Mapping[str, Any],
        observation: Mapping[str, Any] | None,
        assignment: Mapping[str, Any],
    ) -> dict[str, Any]:
        if observation is None or observation.get("status") != "RESUME_EXACT":
            return {
                "status": "TASK_IDENTITY_CONFLICT",
                "reason": "OPERATOR_CHILD_NOT_OBSERVED",
            }
        evidence = cls._validate_operator_evidence(
            repo=repo, observation=observation, assignment=assignment
        )
        if evidence.get("status") != "VALID":
            return evidence
        result = return_fact["return_witness"]["agent_result"]
        manifest_ref, stdout_ref, stderr_ref = evidence["refs"]
        if (result.get("state_refs") != [manifest_ref]
                or result.get("artifact_refs") != [stdout_ref, stderr_ref]
                or result.get("payload", {}).get("verification_refs")
                != [manifest_ref, stdout_ref, stderr_ref]):
            return cls._operator_evidence_error("CM_OPERATOR_REFS_MISMATCH")
        return {
            **return_fact,
            "operator_child": {
                "thread_id": observation["thread_id"],
                "run_id": assignment["run_id"],
            },
        }

    def execute_plan(
        self,
        plan: Mapping[str, Any],
        *,
        packet_locator: str | None = None,
        cwd: str | None = None,
        wait_timeout: float | None = None,
        wait_for_terminal: bool = False,
        observed_tasks: Any = None,
        peer_work_ids: Sequence[str] = (),
        root_override_reason: str | None = None,
    ) -> dict[str, Any]:
        verb = plan.get("verb")
        if verb not in _DISPATCH_VERBS:
            return {"status": "NO_EFFECT", "verb": verb}
        work_id = plan.get("work_id")
        target = plan.get("target_identity") or plan.get("requested_target_identity")
        resolution = plan.get("task_resolution")
        if target == "Workflow-Clerk":
            return {
                "status": "PROTOCOL_DEFECT",
                "reason": "ORDINARY_PACKET_CANNOT_TARGET_CLERK",
                "work_id": work_id,
            }
        if target == _RETIRED_RECOVERY_IDENTITY or (
            isinstance(resolution, Mapping)
            and resolution.get("logical_identity") == _RETIRED_RECOVERY_IDENTITY
        ):
            return {
                "status": "PROTOCOL_DEFECT",
                "reason": "RETIRED_RUNTIME_ROLE",
                "work_id": work_id,
                "target_identity": _RETIRED_RECOVERY_IDENTITY,
            }
        if not isinstance(packet_locator, str):
            raise ValueError("dispatch plan requires packet_locator")
        if not isinstance(cwd, str):
            raise ValueError("dispatch plan requires cwd")
        if observed_tasks is None:
            return {
                "status": "PROTOCOL_DEFECT",
                "reason": "OBSERVED_TASK_SNAPSHOT_REQUIRED",
                "work_id": work_id,
            }
        if root_override_reason is not None and (
            not isinstance(root_override_reason, str) or not root_override_reason.strip()
        ):
            raise ValueError("root override reason must be non-empty")
        expected_resolution_status = (
            "CREATE_TASK" if verb == "CREATE_TASK_INTENT" else "REUSE"
        )
        required_resolution_fields = {
            "status",
            "logical_identity",
            "kind",
            "generation",
            *(
                {"direction_id"}
                if expected_resolution_status == "CREATE_TASK"
                else {"lifecycle", "thread_id"}
            ),
        }
        missing_resolution_fields = sorted(
            field
            for field in required_resolution_fields
            if not isinstance(resolution, Mapping) or field not in resolution
        )
        if missing_resolution_fields:
            return {
                "status": "PROTOCOL_DEFECT",
                "reason": "INCOMPLETE_TASK_RESOLUTION",
                "work_id": work_id,
                "missing_fields": missing_resolution_fields,
            }
        generation = resolution.get("generation")
        target_text = str(target)
        target_manager = self._canonical_manager(target_text)
        expected_kind = (
            resolution.get("kind")
            if target_manager is None
            else target_manager["kind"]
        )
        expected_direction = (
            None if target_manager is None else target_manager["direction_id"]
        )
        thread_locator_valid = (
            expected_resolution_status != "REUSE"
            or (
                isinstance(resolution.get("thread_id"), str)
                and bool(resolution["thread_id"].strip())
            )
        )
        if (
            resolution.get("status") != expected_resolution_status
            or resolution.get("logical_identity") != target
            or resolution.get("kind") != expected_kind
            or not isinstance(generation, int)
            or isinstance(generation, bool)
            or generation < 1
            or not thread_locator_valid
            or (
                expected_resolution_status == "CREATE_TASK"
                and target_manager is None
            )
            or (
                expected_resolution_status == "CREATE_TASK"
                and resolution.get("direction_id") != expected_direction
            )
            or (
                expected_resolution_status == "REUSE"
                and resolution.get("lifecycle")
                not in {"CREATED", "ACTIVE", "PARKED"}
            )
        ):
            return {
                "status": "PROTOCOL_DEFECT",
                "reason": "INVALID_TASK_RESOLUTION",
                "work_id": work_id,
            }
        closed_manager = self._canonical_manager(target_text, generation)
        if expected_resolution_status == "CREATE_TASK" and closed_manager is None:
            return {
                "status": "PROTOCOL_DEFECT",
                "reason": "INVALID_TASK_RESOLUTION",
                "work_id": work_id,
            }
        closed_thread_source = (
            None if closed_manager is None else str(closed_manager["thread_source"])
        )
        repo = Path(cwd).absolute()
        try:
            operator_assignment = self._cm_operator_assignment(
                repo=repo,
                work_id=str(work_id),
                packet_locator=packet_locator,
                target_identity=str(target),
            )
        except (ValueError, hmasd_work_packet.WorkPacketError) as exc:
            return {
                "status": "PROTOCOL_DEFECT",
                "reason": "INVALID_CM_OPERATOR_ASSIGNMENT",
                "work_id": work_id,
                "detail": str(exc),
            }
        with self._dispatch_lock(repo):
            listed = self._list_all_threads(cwd=cwd)
            if listed.get("status") != "OK":
                return listed
            rows = [
                row
                for row in listed["threads"]
                if self._same_cwd(row.get("cwd"), cwd)
            ]
            full_completed_rows: list[Mapping[str, Any]] = []
            for row in rows:
                if (
                    self._native_lifecycle(row.get("status")) != "COMPLETED"
                    or row.get("name") != target
                    or self._canonical_manager(row.get("name")) is None
                    or (
                        expected_resolution_status == "REUSE"
                        and row.get("id") != resolution.get("thread_id")
                    )
                ):
                    continue
                fresh = self._read_thread_full(str(row.get("id", "")))
                if fresh.get("status") != "OK":
                    return fresh
                full_completed_rows.append(fresh["thread"])
            recovery_observation = self._history_recovery_binding(
                work_id=str(work_id),
                canonical_locator=packet_locator,
                cwd=cwd,
                full_native_rows=full_completed_rows,
                raw_projected_tasks=self._task_rows(observed_tasks),
            )
            if isinstance(recovery_observation, Mapping) and "status" in recovery_observation:
                return dict(recovery_observation)
            if recovery_observation is not None:
                rows = [({**row, "status": {"type": "idle"}}
                         if row.get("id") == recovery_observation["thread_id"] else row)
                        for row in rows]
            initial_task_rows = self._native_task_snapshot(
                rows, self._task_rows(observed_tasks)
            )
            generation_conflicts = self._generation_conflicts(
                initial_task_rows, target_identity=str(target)
            )
            if generation_conflicts:
                return {
                    "status": "TASK_IDENTITY_CONFLICT",
                    "reason": "PROJECTED_NATIVE_GENERATION_CONFLICT",
                    "conflicts": generation_conflicts,
                }
            exact = [row for row in rows if row.get("name") == target]
            exact_thread_ids: list[str] = []
            for row in exact:
                listed_thread_id = row.get("id")
                if (
                    not isinstance(listed_thread_id, str)
                    or not listed_thread_id.strip()
                ):
                    return {
                        "status": "TASK_IDENTITY_CONFLICT",
                        "target_identity": target,
                        "reason": "LISTED_TARGET_THREAD_ID_INVALID",
                    }
                exact_thread_ids.append(listed_thread_id)
            if len(exact_thread_ids) > 1:
                return {
                    "status": "TASK_IDENTITY_CONFLICT",
                    "target_identity": target,
                    "thread_ids": sorted(exact_thread_ids),
                }
            thread_id: str | None = None
            thread_full: dict[str, Any] | None = None
            needs_create = False
            tagged_thread: Mapping[str, Any] | None = None
            tagged_generation = (
                resolution.get("generation")
                if isinstance(resolution, Mapping)
                and resolution.get("status") in {"CREATE_TASK", "REUSE"}
                else None
            )
            if (
                closed_thread_source is not None
                and isinstance(tagged_generation, int)
                and not isinstance(tagged_generation, bool)
                and tagged_generation >= 1
            ):
                expected_source = closed_thread_source
                tagged = [
                    row for row in rows if row.get("threadSource") == expected_source
                ]
                if len(tagged) > 1:
                    return {
                        "status": "TASK_IDENTITY_CONFLICT",
                        "target_identity": target,
                        "reason": "MULTIPLE_TARGET_TAGGED_NATIVE_TASKS",
                        "thread_ids": sorted(
                            str(row.get("id")) for row in tagged
                        ),
                    }
                if tagged:
                    tagged_thread = tagged[0]
                    tagged_thread_id = tagged_thread.get("id")
                    tagged_lifecycle = self._native_lifecycle(
                        tagged_thread.get("status")
                    )
                    if (
                        not isinstance(tagged_thread_id, str)
                        or not tagged_thread_id
                        or tagged_lifecycle is None
                    ):
                        return {
                            "status": "TASK_IDENTITY_CONFLICT",
                            "target_identity": target,
                            "reason": "TARGET_TAGGED_NATIVE_TASK_INVALID",
                        }
                    initial_task_rows = [
                        row
                        for row in initial_task_rows
                        if row.get("thread_id") != tagged_thread_id
                    ]
                    initial_task_rows.append(
                        {
                            "logical_identity": str(target),
                            "kind": resolution.get("kind"),
                            "direction_id": (
                                resolution.get("direction_id")
                                if closed_manager is None
                                else closed_manager["direction_id"]
                            ),
                            "generation": tagged_generation,
                            "lifecycle": tagged_lifecycle,
                            "thread_id": tagged_thread_id,
                        }
                    )
            reconcile_seed_tasks = list(initial_task_rows)
            known_thread_ids = {
                value
                for value in (
                    resolution.get("thread_id") if isinstance(resolution, Mapping) else None,
                    plan.get("thread_id"),
                )
                if isinstance(value, str) and value
            }
            known_thread_ids.update(exact_thread_ids)
            if tagged_thread is not None:
                known_thread_ids.add(str(tagged_thread["id"]))
            fresh_resolution = hmasd_work_packet.resolve_target_task(
                str(target), initial_task_rows
            )
            fresh_status = fresh_resolution.get("status")
            status_matches_plan = fresh_status == resolution["status"]
            tagged_create_recovery = (
                resolution["status"] == "CREATE_TASK"
                and tagged_thread is not None
                and fresh_status == "REUSE"
            )
            if not status_matches_plan and not tagged_create_recovery:
                return {
                    "status": "TASK_IDENTITY_CONFLICT",
                    "target_identity": target,
                    "reason": "PLAN_BOUND_TASK_STATUS_MISMATCH",
                    "expected_status": resolution["status"],
                    "observed_status": fresh_status,
                }
            if (
                fresh_resolution.get("status") in {"CREATE_TASK", "REUSE"}
            ):
                fresh_thread_id = fresh_resolution.get("thread_id")
                fresh_row = next(
                    (
                        row
                        for row in initial_task_rows
                        if row.get("thread_id") == fresh_thread_id
                    ),
                    {},
                )
                expected_binding = {
                    "logical_identity": str(target),
                    "kind": resolution.get("kind"),
                    "direction_id": resolution.get("direction_id"),
                    "generation": resolution.get("generation"),
                    "thread_id": resolution.get("thread_id"),
                }
                observed_binding = {
                    "logical_identity": fresh_resolution.get("logical_identity"),
                    "kind": fresh_resolution.get("kind"),
                    "direction_id": fresh_resolution.get(
                        "direction_id", fresh_row.get("direction_id")
                    ),
                    "generation": fresh_resolution.get("generation"),
                    "thread_id": fresh_resolution.get("thread_id"),
                }
                if closed_manager is not None:
                    expected_binding["kind"] = closed_manager["kind"]
                    expected_binding["direction_id"] = closed_manager["direction_id"]
                    manager_fields = {"kind", "direction_id"}
                else:
                    manager_fields = set()
                bound_fields = {"logical_identity", *manager_fields}
                bound_fields.update(
                    field
                    for field in (
                        "kind",
                        "direction_id",
                        "generation",
                        "thread_id",
                    )
                    if field in resolution
                )
                expected_fact = {
                    field: expected_binding[field]
                    for field in expected_binding
                    if field in bound_fields
                }
                observed_fact = {
                    field: observed_binding[field]
                    for field in observed_binding
                    if field in bound_fields
                }
                if expected_fact != observed_fact:
                    return {
                        "status": "TASK_IDENTITY_CONFLICT",
                        "target_identity": target,
                        "reason": "PLAN_BOUND_TASK_MISMATCH",
                        "expected": expected_fact,
                        "observed": observed_fact,
                    }
            if len(known_thread_ids) > 1:
                return {
                    "status": "TASK_IDENTITY_CONFLICT",
                    "target_identity": target,
                    "thread_ids": sorted(known_thread_ids),
                }
            if verb == "CREATE_TASK_INTENT":
                if known_thread_ids:
                    thread_id = next(iter(known_thread_ids))
                    if tagged_thread is not None and not exact:
                        thread_full = self._read_thread_full(thread_id)
                        observed_thread = thread_full.get("thread", {})
                        observed_name = (
                            observed_thread.get("name")
                            if isinstance(observed_thread, Mapping)
                            else None
                        )
                        expected_source = closed_thread_source
                        if (
                            thread_full.get("status") != "OK"
                            or observed_thread.get("threadSource") != expected_source
                            or not self._same_cwd(observed_thread.get("cwd"), cwd)
                        ):
                            return {
                                "status": "TASK_IDENTITY_CONFLICT",
                                "target_identity": target,
                                "thread_id": thread_id,
                                "reason": "TARGET_TAGGED_NATIVE_TASK_CHANGED",
                            }
                        if observed_name in {None, ""}:
                            return {
                                "status": "UNKNOWN",
                                "reason": "THREAD_CREATED_NAME_UNKNOWN",
                                "target_identity": target,
                                "thread_id": thread_id,
                                "observed_name": observed_name,
                                "observed_status": observed_thread.get("status"),
                            }
                        if observed_name != target:
                            return {
                                "status": "TASK_IDENTITY_CONFLICT",
                                "target_identity": target,
                                "thread_id": thread_id,
                                "observed_name": observed_name,
                            }
                    elif not exact:
                        thread_full = self._read_known_identity(
                            thread_id, target_identity=str(target), cwd=cwd
                        )
                        if thread_full.get("status") != "OK":
                            return thread_full
                else:
                    needs_create = True
            else:
                thread_id = resolution.get("thread_id") or plan.get("thread_id")
                if not isinstance(thread_id, str) or not thread_id:
                    raise ValueError("DISPATCH_EXISTING requires an observed thread_id")
                row = next((item for item in rows if item.get("id") == thread_id), None)
                if row is None:
                    thread_full = self._read_known_identity(
                        thread_id, target_identity=str(target), cwd=cwd
                    )
                    if thread_full.get("status") != "OK":
                        return thread_full
                elif row.get("name") != target:
                    return {
                        "status": "TASK_IDENTITY_CONFLICT",
                        "target_identity": target,
                        "thread_id": thread_id,
                        "observed_name": None if row is None else row.get("name"),
                    }
                else:
                    full = self._read_thread_full(thread_id)
                    observed_name = (
                        full.get("thread", {}).get("name")
                        if full.get("status") == "OK"
                        else None
                    )
                    if full.get("status") != "OK" or observed_name != target:
                        return {
                            "status": "TASK_IDENTITY_CONFLICT",
                            "target_identity": target,
                            "thread_id": thread_id,
                            "observed_name": observed_name,
                        }
                    thread_full = full
            peers, unknown_threads = self._peer_work_ids(
                observed_tasks,
                peer_work_ids,
                current_thread_id=thread_id,
            )
            warning = root_override_reason is not None
            if unknown_threads and root_override_reason is None:
                return {
                    "status": "ACTIVE_PEER_OBSERVATION_UNKNOWN",
                    "thread_ids": unknown_threads,
                }
            compare = None
            peer_candidates = [item for item in peers if item != work_id]
            if peer_candidates:
                try:
                    compare = hmasd_work_packet.compare_work_ids(
                        repo, [work_id, *peer_candidates]
                    )
                except hmasd_work_packet.WorkPacketError:
                    return {
                        "status": "PROTOCOL_DEFECT",
                        "reason": "PACKET_COMPARATOR_DEFECT",
                        "work_id": work_id,
                    }
                if compare.get("outcome") != "DISJOINT" and not (
                    root_override_reason is not None
                    and self._override_allows_compare(compare)
                ):
                    return {
                        "status": "WORK_OVERLAP_CONFLICT",
                        "compare_outcome": compare.get("outcome", "UNKNOWN"),
                        "work_ids": compare.get("work_ids", [work_id, *peer_candidates]),
                    }
                warning = warning or (
                    root_override_reason is not None
                    and compare.get("outcome") != "DISJOINT"
                )
            if needs_create:
                created = self.create_thread(
                    cwd=cwd,
                    target_identity=target,
                    generation=resolution["generation"],
                )
                if created["status"] != "CREATED":
                    return created
                thread_id = created["thread_id"]
                reconcile_seed_tasks.append(
                    {
                        "logical_identity": resolution["logical_identity"],
                        "kind": resolution.get("kind"),
                        "direction_id": resolution.get("direction_id"),
                        "generation": resolution["generation"],
                        "thread_id": thread_id,
                    }
                )
            elif thread_full is None:
                thread_full = self._read_thread_full(thread_id)
                if thread_full.get("status") != "OK":
                    return thread_full
            operator_contract = operator_assignment
            operator_observation: dict[str, Any] | None = None
            if operator_assignment is not None:
                operator_observation = self._observe_operator_child(
                    rows,
                    parent_thread_id=str(thread_id),
                    assignment=operator_assignment,
                )
                action = operator_observation.get("status")
                if action not in {"CREATE_EXACT", "RESUME_EXACT"}:
                    return operator_observation
                operator_contract = {**operator_assignment, "action": action}
                if action == "RESUME_EXACT":
                    operator_contract["observed_child_thread_id"] = operator_observation[
                        "thread_id"
                    ]
            if thread_full is not None and self._terminal_attempt_needs_return_observation(
                thread_full["thread"], work_id, packet_locator, target
            ):
                reconcile_rows = list(rows)
                if all(row.get("id") != thread_id for row in reconcile_rows):
                    reconcile_rows.append(thread_full["thread"])
                reconcile_task_rows = self._native_task_snapshot(
                    reconcile_rows,
                    self._task_rows(observed_tasks),
                    include_unlisted=False,
                )
                return_fact = self._validated_return_fact(
                    repo=repo,
                    work_id=work_id,
                    observed_tasks=reconcile_task_rows,
                    thread_id=thread_id,
                )
                if return_fact is not None:
                    if operator_assignment is None:
                        return return_fact
                    return self._completed_operator_return(
                        repo=repo,
                        return_fact=return_fact,
                        observation=operator_observation,
                        assignment=operator_assignment,
                    )
            sent = self.send(
                thread_id,
                work_id,
                packet_locator,
                target,
                root_override_reason=root_override_reason,
                expected_cwd=cwd,
                expected_thread_source=closed_thread_source,
                require_thread_source=(
                    closed_thread_source is not None
                    and (needs_create or tagged_thread is not None)
                ),
                participant_contract=operator_contract,
            )
            if warning:
                sent = {**sent, "warning": "ROOT_OVERRIDE_ACTIVE"}
        delivery_status = sent.get("status")
        if (
            (wait_for_terminal or wait_timeout is not None)
            and delivery_status
            in {"DELIVERED", "DELIVERY_OBSERVED_AFTER_UNKNOWN", "ALREADY_DELIVERED"}
            and isinstance(sent.get("turn_id"), str)
        ):
            terminal = self.wait(
                thread_id,
                sent["turn_id"],
                timeout=wait_timeout,
                resume=delivery_status == "ALREADY_DELIVERED",
                observe_active=delivery_status == "ALREADY_DELIVERED",
            )
            if terminal.get("status") not in {"COMPLETED", "TERMINAL"}:
                return terminal
            if terminal.get("capacity_error") in _CAPACITY_ERRORS:
                return {
                    "status": "CAPACITY_PAUSE",
                    "work_id": work_id,
                    "thread_id": terminal.get("thread_id"),
                    "turn_id": terminal.get("turn_id"),
                    "turn_status": terminal.get("turn_status"),
                    "capacity_error": terminal["capacity_error"],
                }
            fresh = self._list_all_threads(cwd=cwd)
            if fresh.get("status") != "OK":
                return fresh
            fresh_rows = [
                row
                for row in fresh["threads"]
                if self._same_cwd(row.get("cwd"), cwd)
            ]
            current = next(
                (row for row in fresh_rows if row.get("id") == thread_id), None
            )
            if current is not None and current.get("name") != target:
                return {
                    "status": "TASK_IDENTITY_CONFLICT",
                    "target_identity": target,
                    "thread_id": thread_id,
                    "observed_name": current.get("name"),
                    "observed_status": current.get("status"),
                }
            if current is None:
                full = self._read_known_identity(
                    thread_id, target_identity=str(target), cwd=cwd
                )
                if full.get("status") != "OK":
                    return full
                fresh_rows.append(full["thread"])
            fresh_task_rows = self._native_task_snapshot(
                fresh_rows,
                reconcile_seed_tasks,
                include_unlisted=False,
            )
            return_fact = self._validated_return_fact(
                repo=repo,
                work_id=work_id,
                observed_tasks=fresh_task_rows,
                thread_id=thread_id,
                terminal=terminal,
            )
            if return_fact is not None:
                if operator_assignment is None:
                    return return_fact
                child = self._observe_operator_child(
                    fresh_rows,
                    parent_thread_id=str(thread_id),
                    assignment=operator_assignment,
                )
                if child.get("status") != "RESUME_EXACT":
                    return child
                return self._completed_operator_return(
                    repo=repo,
                    return_fact=return_fact,
                    observation=child,
                    assignment=operator_assignment,
                )
            return {
                "status": "RETURN_WITNESS_MISSING",
                "reason": "NATIVE_TURN_TERMINAL_WITHOUT_RETURN_WITNESS",
                "recoverable": True,
                "work_id": work_id,
                "thread_id": thread_id,
                "turn_id": terminal.get("turn_id"),
                "turn_status": terminal.get("turn_status"),
            }
        return sent

    def run_chain(
        self,
        *,
        start_work_id: str,
        cwd: str,
        max_transitions: int = 16,
        peer_work_ids: Sequence[str] = (),
        root_override_reason: str | None = None,
    ) -> dict[str, Any]:
        """Boundedly compose validated one-work-id operations in memory.

        Durable workflow facts remain the ready packets, immutable returns,
        native task history, and Effect observations.  This method retains only
        an ordered trace and the current explicit work identity for this call.
        """

        if _SHA256.fullmatch(start_work_id) is None:
            raise ValueError("start_work_id must be a lowercase SHA256")
        if not isinstance(cwd, str) or not cwd:
            raise ValueError("run-chain requires cwd")
        if (
            not isinstance(max_transitions, int)
            or isinstance(max_transitions, bool)
            or max_transitions < 0
        ):
            raise ValueError("max_transitions must be a non-negative integer")
        repo = Path(cwd).absolute()
        current_tasks: list[dict[str, Any]] = []
        current_work_id = start_work_id
        transition_count = 0
        events: list[dict[str, Any]] = []
        current_override_reason = root_override_reason
        recovery_binding: dict[str, Any] | None = None

        def stopped(reason: str, **fact: Any) -> dict[str, Any]:
            return {
                "status": "STOPPED",
                "start_work_id": start_work_id,
                "transition_count": transition_count,
                "events": events,
                "stop": {
                    "reason": reason,
                    "work_id": current_work_id,
                    **fact,
                },
            }

        def observation_stop(observation: Mapping[str, Any]) -> dict[str, Any]:
            if observation.get("status") == "TASK_IDENTITY_CONFLICT":
                return stopped("TYPED_CONFLICT", conflict=dict(observation))
            return stopped("NATIVE_OBSERVATION_STOP", observation=dict(observation))

        def refresh_tasks(work_id: str) -> list[dict[str, Any]] | dict[str, Any]:
            nonlocal recovery_binding
            try:
                projected_tasks = hmasd_work_packet.load_observed_tasks(
                    None, repo=repo
                )
            except hmasd_work_packet.WorkPacketError as exc:
                return {
                    "status": "RUNTIME_TASK_PROJECTION_INVALID",
                    "conflict": {"type": type(exc).__name__, "detail": str(exc)},
                }
            listed = self._list_all_threads(cwd=cwd)
            if listed.get("status") != "OK":
                return listed
            rows: list[Mapping[str, Any]] = []
            full_rows: list[Mapping[str, Any]] = []
            for listed_row in listed["threads"]:
                thread_id = listed_row.get("id")
                if not isinstance(thread_id, str) or not thread_id:
                    return {
                        "status": "TASK_LIST_IDENTITY_DEFECT",
                        "reason": "LISTED_THREAD_ID_INVALID",
                    }
                read = self._read_thread_full(thread_id)
                if read.get("status") != "OK":
                    return read
                thread = read.get("thread")
                if not isinstance(thread, Mapping) or thread.get("id") != thread_id:
                    return {
                        "status": "TASK_IDENTITY_CONFLICT",
                        "reason": "FRESH_THREAD_READ_INVALID",
                        "thread_id": thread_id,
                    }
                full_rows.append(thread)
                if self._same_cwd(thread.get("cwd"), cwd):
                    rows.append(thread)
            locator = f".codex/runtime/work/ready/{work_id}/packet.json"
            try:
                witness = hmasd_work_packet.read_return(repo=repo, work_id=work_id)
            except (hmasd_work_packet.InvalidPacket, hmasd_work_packet.PacketConflict):
                return {"status": "TASK_IDENTITY_CONFLICT", "reason": "RETURN_WITNESS_INVALID"}
            recovery_binding = None
            if witness is None:
                observed = self._history_recovery_binding(
                    work_id=work_id,
                    canonical_locator=locator,
                    cwd=cwd,
                    full_native_rows=full_rows,
                    raw_projected_tasks=projected_tasks,
                )
                if isinstance(observed, Mapping) and "status" in observed:
                    return dict(observed)
                recovery_binding = observed
            if recovery_binding is not None:
                rows = [({**row, "status": {"type": "idle"}}
                         if row.get("id") == recovery_binding["thread_id"] else row)
                        for row in rows]
            return self._native_task_snapshot(
                rows, projected_tasks, include_unlisted=False
            )

        initial_snapshot = refresh_tasks(current_work_id)
        if isinstance(initial_snapshot, Mapping):
            return observation_stop(initial_snapshot)
        current_tasks = initial_snapshot

        while True:
            try:
                plan = hmasd_work_packet.reconcile_once(
                    repo=repo,
                    work_id=current_work_id,
                    observed_tasks=current_tasks,
                )["plan"]
            except (hmasd_work_packet.InvalidPacket, hmasd_work_packet.PacketConflict) as exc:
                return stopped(
                    "TYPED_CONFLICT",
                    conflict={"type": type(exc).__name__, "detail": str(exc)},
                )
            plan_target = (
                plan.get("target_identity")
                or plan.get("requested_target_identity")
                or plan.get("task_resolution", {}).get("logical_identity")
            )
            generation_conflicts = (
                self._generation_conflicts(
                    current_tasks, target_identity=plan_target
                )
                if isinstance(plan_target, str)
                else []
            )
            if generation_conflicts:
                return stopped(
                    "TYPED_CONFLICT",
                    conflict={
                        "status": "TASK_IDENTITY_CONFLICT",
                        "reason": "PROJECTED_NATIVE_GENERATION_CONFLICT",
                        "conflicts": generation_conflicts,
                    },
                )
            events.append(
                {"kind": "PLAN", "work_id": current_work_id, "plan": plan}
            )
            verb = plan.get("verb")

            if recovery_binding is not None and verb in _DISPATCH_VERBS:
                resolution = plan.get("task_resolution", {})
                if (
                    resolution.get("status") != "REUSE"
                    or resolution.get("logical_identity") != recovery_binding["target_identity"]
                    or resolution.get("thread_id") != recovery_binding["thread_id"]
                    or resolution.get("generation") != recovery_binding["generation"]
                ):
                    return stopped(
                        "TYPED_CONFLICT",
                        conflict={"status": "TASK_IDENTITY_CONFLICT", "reason": "HISTORY_RECOVERY_PLAN_MISMATCH"},
                    )

            if verb == "NOOP_TERMINAL":
                try:
                    witness = hmasd_work_packet.read_return(
                        repo=repo, work_id=current_work_id
                    )
                except (hmasd_work_packet.InvalidPacket, hmasd_work_packet.PacketConflict) as exc:
                    return stopped(
                        "TYPED_CONFLICT",
                        conflict={"type": type(exc).__name__, "detail": str(exc)},
                    )
                receiver = witness.get("receiver", {}) if witness is not None else {}
                target_identity = receiver.get("logical_identity")
                try:
                    assignment = self._cm_operator_assignment(
                        repo=repo,
                        work_id=current_work_id,
                        packet_locator=(
                            f".codex/runtime/work/ready/{current_work_id}/packet.json"
                        ),
                        target_identity=str(target_identity),
                    )
                except (ValueError, hmasd_work_packet.WorkPacketError) as exc:
                    return stopped(
                        "TYPED_CONFLICT",
                        conflict={"type": "INVALID_CM_OPERATOR_ASSIGNMENT", "detail": str(exc)},
                    )
                if assignment is not None:
                    parent = next(
                        (
                            task.get("thread_id")
                            for task in current_tasks
                            if task.get("logical_identity") == target_identity
                        ),
                        None,
                    )
                    listed = self._list_all_threads(cwd=cwd)
                    if not isinstance(parent, str) or listed.get("status") != "OK":
                        return stopped("NATIVE_OBSERVATION_STOP")
                    child = self._observe_operator_child(
                        listed["threads"],
                        parent_thread_id=parent,
                        assignment=assignment,
                    )
                    if child.get("status") != "RESUME_EXACT":
                        return stopped("EXECUTE_PLAN_STOP", result=child)
                    completed = self._completed_operator_return(
                        repo=repo,
                        return_fact={"return_witness": witness},
                        observation=child,
                        assignment=assignment,
                    )
                    if "return_witness" not in completed:
                        return stopped("EXECUTE_PLAN_STOP", result=completed)
                return stopped("TERMINAL_NO_NEXT", return_witness=witness)

            if verb == "CONFLICT":
                return stopped("TYPED_CONFLICT", conflict=plan)

            if verb == "OBSERVE_EFFECT_ONLY":
                return stopped(
                    "UNKNOWN_COMMITMENT",
                    unknown_effect_refs=plan.get("unknown_effect_refs", []),
                )

            if verb == "PUBLISH_PACKET_INTENT":
                try:
                    witness = hmasd_work_packet.read_return(
                        repo=repo, work_id=current_work_id
                    )
                except (hmasd_work_packet.InvalidPacket, hmasd_work_packet.PacketConflict) as exc:
                    return stopped(
                        "TYPED_CONFLICT",
                        conflict={"type": type(exc).__name__, "detail": str(exc)},
                    )
                if witness is None:
                    return stopped(
                        "TYPED_CONFLICT",
                        conflict={"type": "MISSING_RETURN_WITNESS"},
                    )
                next_action = witness["agent_result"]["next_action"]
                next_work_id = plan.get("next_work_id")
                if next_action.get("kind") != "REQUEST_CM_ENGINEERING":
                    return stopped(
                        "DOMAIN_DECISION_REQUIRED",
                        next_action=next_action,
                        return_witness=witness,
                    )
                if (
                    not isinstance(next_work_id, str)
                    or next_action.get("input_refs") != [next_work_id]
                    or witness.get("next_packet_draft") != plan.get("packet")
                ):
                    return stopped(
                        "TYPED_CONFLICT",
                        conflict={"type": "FOLLOW_ON_BINDING_MISMATCH"},
                    )
                if transition_count >= max_transitions:
                    return stopped(
                        "MAX_TRANSITIONS",
                        max_transitions=max_transitions,
                        next_work_id=next_work_id,
                    )
                try:
                    published = hmasd_work_packet.publish_packet(
                        plan["packet"], repo=repo
                    )
                except (hmasd_work_packet.InvalidPacket, hmasd_work_packet.PacketConflict) as exc:
                    return stopped(
                        "TYPED_CONFLICT",
                        conflict={"type": type(exc).__name__, "detail": str(exc)},
                    )
                events.append(
                    {
                        "kind": "PACKET_PUBLISH",
                        "work_id": current_work_id,
                        "next_work_id": next_work_id,
                        "published": published["published"],
                    }
                )
                transition_count += 1
                current_work_id = next_work_id
                current_override_reason = None
                refreshed = refresh_tasks(current_work_id)
                if isinstance(refreshed, Mapping):
                    return observation_stop(refreshed)
                current_tasks = refreshed
                continue

            if verb in _DISPATCH_VERBS:
                result = self.execute_plan(
                    plan,
                    packet_locator=(
                        f".codex/runtime/work/ready/{current_work_id}/packet.json"
                    ),
                    cwd=cwd,
                    wait_for_terminal=True,
                    observed_tasks=current_tasks,
                    peer_work_ids=peer_work_ids,
                    root_override_reason=current_override_reason,
                )
                events.append(
                    {
                        "kind": "EXECUTE_PLAN",
                        "work_id": current_work_id,
                        "result": result,
                    }
                )
                if result.get("status") == "UNKNOWN":
                    return stopped("UNKNOWN_COMMITMENT", result=result)
                if result.get("status") == "CAPACITY_PAUSE":
                    manager = self._canonical_manager(
                        str(plan.get("target_identity", ""))
                    )
                    direction_id = (
                        None if manager is None else manager["direction_id"]
                    )
                    scope = "direction" if direction_id is not None else "project"
                    error = result["capacity_error"]
                    thread_id = result.get("thread_id")
                    turn_id = result.get("turn_id")
                    return stopped(
                        "CAPACITY_PAUSE",
                        failure_scope=scope,
                        failure_ref=f"native_turn:{thread_id}:{turn_id}:{error}",
                        evidence={
                            "thread_id": thread_id,
                            "turn_id": turn_id,
                            "turn_status": result.get("turn_status"),
                            "codex_error_info": error,
                        },
                    )
                if result.get("status") == "RETURN_WITNESS_MISSING_AFTER_ATTEMPTS":
                    resolution = plan.get("task_resolution", {})
                    direction_id = (
                        resolution.get("direction_id")
                        if isinstance(resolution, Mapping)
                        else None
                    )
                    manager = self._canonical_manager(
                        str(plan.get("target_identity", ""))
                    )
                    if direction_id is None and manager is not None:
                        direction_id = manager["direction_id"]
                    failure_scope = (
                        "direction" if isinstance(direction_id, str) else "project"
                    )
                    failure_ref = (
                        direction_id
                        if isinstance(direction_id, str)
                        else current_work_id
                    )
                    return stopped(
                        "RECOVERY_EXHAUSTED",
                        failure_scope=failure_scope,
                        failure_ref=failure_ref,
                        evidence={
                            "target_identity": plan.get("target_identity"),
                            "thread_id": result.get("thread_id"),
                            "packet_locator": (
                                f".codex/runtime/work/ready/{current_work_id}/packet.json"
                            ),
                            "max_attempts": result.get(
                                "resume_condition", {}
                            ).get("max_attempts"),
                            "attempt_statuses": result.get("attempt_statuses", []),
                        },
                    )
                if (
                    result.get("status") == "RETURN_WITNESS_MISSING"
                    and result.get("recoverable") is True
                ):
                    refreshed = refresh_tasks(current_work_id)
                    if isinstance(refreshed, Mapping):
                        return observation_stop(refreshed)
                    current_tasks = refreshed
                    continue
                if "return_witness" not in result:
                    return stopped("EXECUTE_PLAN_STOP", result=result)
                refreshed = refresh_tasks(current_work_id)
                if isinstance(refreshed, Mapping):
                    return observation_stop(refreshed)
                current_tasks = refreshed
                continue

            return stopped("PLAN_STOP", plan=plan)

    @staticmethod
    def _conformance_failure(
        reason: str,
        source_thread_id: str,
        *,
        thread_id: str | None = None,
        turn_id: str | None = None,
        error_code: int | str | None = None,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "status": "CONFORMANCE_FAILED",
            "reason": reason,
            "source_thread_id": source_thread_id,
        }
        if thread_id is not None:
            result.update({"thread_id": thread_id, "ephemeral": True})
        if turn_id is not None:
            result["turn_id"] = turn_id
        if error_code is not None:
            result["error_code"] = error_code
        if error_message is not None:
            result["error_message"] = error_message
        return result

    @staticmethod
    def _conformance_transport_reason(result: Mapping[str, Any]) -> str:
        error_code = result.get("error_code")
        if isinstance(error_code, (int, str)) and not isinstance(error_code, bool):
            return f"SERVER_ERROR_{error_code}"
        return str(result.get("reason", result.get("status", "TRANSPORT_FAILED")))

    def _wait_for_conformance_completion(
        self, thread_id: str, turn_id: str, *, timeout: float
    ) -> dict[str, Any]:
        """Observe an ephemeral conformance turn without reading or resuming it."""
        deadline = time.monotonic() + timeout
        while True:
            for index, notification in enumerate(self._notifications):
                params = notification.get("params")
                turn = params.get("turn") if isinstance(params, Mapping) else None
                if (
                    notification.get("method") == "turn/completed"
                    and isinstance(params, Mapping)
                    and params.get("threadId") == thread_id
                    and isinstance(turn, Mapping)
                    and turn.get("id") == turn_id
                ):
                    del self._notifications[index]
                    return {"status": "COMPLETED_NOTIFICATION", "turn": turn}
            if time.monotonic() >= deadline:
                return {"status": "WAIT_TIMEOUT", "thread_id": thread_id, "turn_id": turn_id}
            read = self._read(deadline, after_send=False)
            if read["status"] != "MESSAGE":
                if read["status"] == "TIMEOUT":
                    return {
                        "status": "WAIT_TIMEOUT",
                        "thread_id": thread_id,
                        "turn_id": turn_id,
                    }
                return read
            message = read["message"]
            if "method" in message and message.get("id") is not None:
                return {
                    "status": "INTERVENTION_REQUIRED",
                    "reason": "SERVER_REQUEST",
                }
            if "method" in message:
                self._notifications.append(message)
                continue
            message_id = message.get("id")
            if isinstance(message_id, int):
                self._pending_responses[message_id] = message
                continue
            return {"status": "INVALID_JSON", "detail": "notification has no method"}

    def conformance(self, source_thread_id: str, *, wait_timeout: float) -> dict[str, Any]:
        """Run one ephemeral, read-only native transport conformance turn."""

        initialized = self._ensure_initialized()
        if initialized["status"] != "OK":
            return self._conformance_failure(initialized["status"], source_thread_id)
        forked = self._request(
            "thread/fork",
            {
                "approvalPolicy": "never",
                "ephemeral": True,
                "excludeTurns": True,
                "sandbox": "read-only",
                "threadId": source_thread_id,
            },
            after_send=True,
        )
        if forked["status"] != "OK":
            return self._conformance_failure(
                self._conformance_transport_reason(forked),
                source_thread_id,
                error_code=forked.get("error_code"),
                error_message=forked.get("error_message"),
            )
        thread_id = forked["result"].get("thread", {}).get("id")
        if not isinstance(thread_id, str) or not thread_id:
            return self._conformance_failure("MISSING_FORK_THREAD_ID", source_thread_id)
        started = self._request(
            "turn/start",
            {
                "approvalPolicy": "never",
                "effort": "low",
                "input": [{"type": "text", "text": _CONFORMANCE_PROMPT}],
                "model": "gpt-5.6-luna",
                "outputSchema": _CONFORMANCE_SCHEMA,
                "sandboxPolicy": {"networkAccess": False, "type": "readOnly"},
                "threadId": thread_id,
            },
            after_send=True,
        )
        if started["status"] != "OK":
            return self._conformance_failure(
                self._conformance_transport_reason(started),
                source_thread_id,
                thread_id=thread_id,
                error_code=started.get("error_code"),
                error_message=started.get("error_message"),
            )
        turn_id = started["result"].get("turn", {}).get("id")
        if not isinstance(turn_id, str) or not turn_id:
            return self._conformance_failure(
                "MISSING_TURN_ID_AFTER_SEND", source_thread_id, thread_id=thread_id
            )
        terminal = self._wait_for_conformance_completion(
            thread_id, turn_id, timeout=wait_timeout
        )
        if terminal.get("status") != "COMPLETED_NOTIFICATION":
            return self._conformance_failure(
                self._conformance_transport_reason(terminal),
                source_thread_id,
                thread_id=thread_id,
                turn_id=turn_id,
                error_code=terminal.get("error_code"),
                error_message=terminal.get("error_message"),
            )
        turn = terminal["turn"]
        if turn.get("status") != "completed":
            return self._conformance_failure(
                "TERMINAL_TURN_NOT_RECONSTRUCTED",
                source_thread_id,
                thread_id=thread_id,
                turn_id=turn_id,
            )
        items = turn.get("items")
        if not isinstance(items, list):
            return self._conformance_failure(
                "TERMINAL_TURN_ITEMS_MISSING",
                source_thread_id,
                thread_id=thread_id,
                turn_id=turn_id,
            )
        if any(
            not isinstance(item, Mapping)
            or item.get("type") not in {"userMessage", "agentMessage"}
            for item in items
        ):
            return self._conformance_failure(
                "UNEXPECTED_TURN_ITEM",
                source_thread_id,
                thread_id=thread_id,
                turn_id=turn_id,
            )
        messages = [
            item.get("text")
            for item in items
            if isinstance(item, Mapping) and item.get("type") == "agentMessage"
        ]
        if messages != [_CONFORMANCE_RESPONSE]:
            return self._conformance_failure(
                "FINAL_RESPONSE_MISMATCH",
                source_thread_id,
                thread_id=thread_id,
                turn_id=turn_id,
            )
        return {
            "status": "CONFORMANCE_OK",
            "source_thread_id": source_thread_id,
            "thread_id": thread_id,
            "turn_id": turn_id,
            "turn_status": "completed",
            "ephemeral": True,
            "response_verified": True,
        }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument(
        "--server-command",
        default=None,
        help="App Server command, parsed without a shell",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    probe = commands.add_parser("probe")
    probe.set_defaults(action="probe")
    listing = commands.add_parser("list")
    listing.add_argument("--cwd")
    read = commands.add_parser("read")
    read.add_argument("--thread-id", required=True)
    create = commands.add_parser("create")
    create.add_argument("--cwd", required=True)
    create.add_argument("--target-identity", required=True)
    send = commands.add_parser("send")
    send.add_argument("--thread-id", required=True)
    send.add_argument("--work-id", required=True)
    send.add_argument("--packet-locator", required=True)
    send.add_argument("--target-identity", required=True)
    wait = commands.add_parser("wait")
    wait.add_argument("--thread-id", required=True)
    wait.add_argument("--turn-id", required=True)
    wait.add_argument("--wait-timeout", type=float, required=True)
    observe = commands.add_parser("observe")
    observe.add_argument("--thread-id", required=True)
    observe.add_argument("--turn-id")
    execute = commands.add_parser("execute-plan")
    execute.add_argument("--plan", required=True)
    execute.add_argument("--packet-locator")
    execute.add_argument("--cwd")
    execute.add_argument("--observed-tasks")
    execute.add_argument("--peer-work-id", action="append", default=[])
    execute.add_argument("--root-override-reason")
    chain = commands.add_parser("run-chain")
    chain.add_argument("--work-id", required=True)
    chain.add_argument("--cwd", required=True)
    chain.add_argument("--peer-work-id", action="append", default=[])
    chain.add_argument("--root-override-reason")
    chain.add_argument("--max-transitions", type=int, default=16)
    conformance = commands.add_parser("conformance")
    conformance.add_argument("--source-thread-id", required=True)
    conformance.add_argument("--wait-timeout", type=float, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    command = (
        default_server_command()
        if args.server_command is None
        else tuple(shlex.split(args.server_command, posix=False))
    )
    try:
        with AppServerClient(command, timeout=args.timeout) as client:
            if args.command == "probe":
                result = client.probe()
            elif args.command == "list":
                result = client.list_threads(cwd=args.cwd)
            elif args.command == "read":
                result = client.read_thread(args.thread_id)
            elif args.command == "create":
                result = client.create_thread(
                    cwd=args.cwd, target_identity=args.target_identity
                )
            elif args.command == "send":
                result = client.send(
                    args.thread_id,
                    args.work_id,
                    args.packet_locator,
                    args.target_identity,
                )
                delivery_status = result.get("status")
                if (
                    delivery_status
                    in {"DELIVERED", "DELIVERY_OBSERVED_AFTER_UNKNOWN", "ALREADY_DELIVERED"}
                    and isinstance(result.get("turn_id"), str)
                ):
                    result = client.wait(
                        result["thread_id"],
                        result["turn_id"],
                        timeout=None,
                        resume=delivery_status == "ALREADY_DELIVERED",
                        observe_active=delivery_status == "ALREADY_DELIVERED",
                    )
            elif args.command == "wait":
                result = client.wait(
                    args.thread_id, args.turn_id, timeout=args.wait_timeout
                )
            elif args.command == "observe":
                result = client.observe(args.thread_id, args.turn_id)
            elif args.command == "conformance":
                result = client.conformance(
                    args.source_thread_id, wait_timeout=args.wait_timeout
                )
            elif args.command == "run-chain":
                result = client.run_chain(
                    start_work_id=args.work_id,
                    cwd=args.cwd,
                    peer_work_ids=args.peer_work_id,
                    root_override_reason=args.root_override_reason,
                    max_transitions=args.max_transitions,
                )
            else:
                plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
                observed_tasks = (
                    None
                    if args.observed_tasks is None
                    else json.loads(Path(args.observed_tasks).read_text(encoding="utf-8"))
                )
                result = client.execute_plan(
                    plan,
                    packet_locator=args.packet_locator,
                    cwd=args.cwd,
                    wait_timeout=None,
                    wait_for_terminal=True,
                    observed_tasks=observed_tasks,
                    peer_work_ids=args.peer_work_id,
                    root_override_reason=args.root_override_reason,
                )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"status": "CLIENT_ERROR", "detail": str(exc)}
    sys.stdout.buffer.write(_canonical_bytes(result))
    return 0 if result.get("status") not in {"CLIENT_ERROR", "ERROR"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
