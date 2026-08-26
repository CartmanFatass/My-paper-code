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
    from scripts import hmasd_platform, hmasd_work_packet
except ImportError:
    import hmasd_platform
    import hmasd_work_packet


PROTOCOL_MARKER = "hmasd.work-packet.dispatch.v2"
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
_BOOTSTRAP_SKILLS = {
    "Portfolio": "hmasd-portfolio-task",
    "EM": "hmasd-em-task",
    "CM": "hmasd-cm-task",
}
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
    return (executable, "app-server")


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

    def create_thread(self, *, cwd: str, target_identity: str) -> dict[str, Any]:
        if _IDENTITY.fullmatch(target_identity) is None:
            raise ValueError("target identity is invalid")
        initialized = self._ensure_initialized()
        if initialized["status"] != "OK":
            return initialized
        runtime = self._target_runtime(target_identity)
        params: dict[str, Any] = {
            "approvalPolicy": "never",
            "cwd": cwd,
            "sandbox": "danger-full-access",
        }
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
            return {
                "status": "UNKNOWN",
                "reason": "THREAD_CREATED_NAME_UNKNOWN",
                "thread_id": thread_id,
                "name_result": named,
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
    def _history_has_text(value: Any, exact_text: str) -> bool:
        if isinstance(value, Mapping):
            if value.get("type") == "text" and value.get("text") == exact_text:
                return True
            return any(AppServerClient._history_has_text(item, exact_text) for item in value.values())
        if isinstance(value, list):
            return any(AppServerClient._history_has_text(item, exact_text) for item in value)
        return False

    @staticmethod
    def _history_has_protocol(value: Any) -> bool:
        if isinstance(value, Mapping):
            if value.get("type") == "text" and isinstance(value.get("text"), str):
                return f'"protocol": "{PROTOCOL_MARKER}"' in value["text"]
            return any(AppServerClient._history_has_protocol(item) for item in value.values())
        if isinstance(value, list):
            return any(AppServerClient._history_has_protocol(item) for item in value)
        return False

    @staticmethod
    def _protocol_documents(value: Any, work_id: str) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        if isinstance(value, Mapping):
            text = value.get("text")
            if value.get("type") == "text" and isinstance(text, str):
                try:
                    document = json.loads(text)
                except json.JSONDecodeError:
                    document = None
                if (
                    isinstance(document, Mapping)
                    and document.get("protocol") == PROTOCOL_MARKER
                    and document.get("work_id") == work_id
                ):
                    found.append(dict(document))
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
            values: list[str] = []

            def visit(value: Any) -> None:
                if isinstance(value, Mapping):
                    text = value.get("text")
                    if value.get("type") == "text" and isinstance(text, str):
                        try:
                            document = json.loads(text)
                        except json.JSONDecodeError:
                            document = None
                        if (
                            isinstance(document, Mapping)
                            and document.get("protocol") == PROTOCOL_MARKER
                            and isinstance(document.get("work_id"), str)
                            and _SHA256.fullmatch(document["work_id"]) is not None
                        ):
                            values.append(document["work_id"])
                    for item in value.values():
                        visit(item)
                elif isinstance(value, list):
                    for item in value:
                        visit(item)

            visit(turn.get("items", []))
            if values:
                return values[-1]
        return None

    @staticmethod
    def _target_runtime(target_identity: str) -> dict[str, str] | None:
        if target_identity == "Portfolio" or target_identity.startswith("EM-"):
            return {"model": "gpt-5.6-sol", "effort": "max"}
        if target_identity.startswith("CM-"):
            return {"model": "gpt-5.6-sol", "effort": "high"}
        return None

    @staticmethod
    def _bootstrap_input(target_identity: str, repo: Path) -> dict[str, str] | None:
        if target_identity == "Portfolio":
            kind = "Portfolio"
        elif target_identity.startswith("EM-"):
            kind = "EM"
        elif target_identity.startswith("CM-"):
            kind = "CM"
        else:
            return None
        name = _BOOTSTRAP_SKILLS[kind]
        path = (repo.resolve() / ".agents" / "skills" / name / "SKILL.md").as_posix()
        return {"type": "skill", "name": name, "path": path}

    def send(
        self,
        thread_id: str,
        work_id: str,
        packet_locator: str,
        target_identity: str,
        *,
        repo: Path | None = None,
        max_attempts: int = 3,
        root_override_reason: str | None = None,
    ) -> dict[str, Any]:
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        read = self._read_thread_full(thread_id)
        if read["status"] != "OK":
            return read
        history = read["thread"].get("turns", [])
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
            skill = self._bootstrap_input(target_identity, repo or Path.cwd())
            if skill is not None:
                inputs.append({"type": "text", "text": f"${skill['name']}"})
                inputs.append(skill)
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
        return {
            "status": "COMPLETED" if status == "completed" else "TERMINAL",
            "thread_id": thread_id,
            "turn_id": turn.get("id"),
            "turn_status": status,
        }

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
        if target == "Workflow-Clerk":
            return {
                "status": "PROTOCOL_DEFECT",
                "reason": "ORDINARY_PACKET_CANNOT_TARGET_CLERK",
                "work_id": work_id,
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
        repo = Path(cwd).absolute()
        with self._dispatch_lock(repo):
            listed = self._list_all_threads(cwd=cwd)
            if listed.get("status") != "OK":
                return listed
            rows = [
                row
                for row in listed["threads"]
                if self._same_cwd(row.get("cwd"), cwd)
            ]
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
            resolution = plan.get("task_resolution", {})
            known_thread_ids = {
                value
                for value in (
                    resolution.get("thread_id") if isinstance(resolution, Mapping) else None,
                    plan.get("thread_id"),
                )
                if isinstance(value, str) and value
            }
            known_thread_ids.update(exact_thread_ids)
            task_resolution = hmasd_work_packet.resolve_target_task(
                str(target), self._task_rows(observed_tasks)
            )
            if task_resolution.get("status") == "REUSE":
                cached_thread_id = task_resolution.get("thread_id")
                if isinstance(cached_thread_id, str) and cached_thread_id:
                    known_thread_ids.add(cached_thread_id)
            elif task_resolution.get("status") == "TASK_IDENTITY_CONFLICT":
                return {
                    "status": "TASK_IDENTITY_CONFLICT",
                    "target_identity": target,
                    "reason": task_resolution.get("reason"),
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
                    if not exact:
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
                created = self.create_thread(cwd=cwd, target_identity=target)
                if created["status"] != "CREATED":
                    return created
                thread_id = created["thread_id"]
            elif thread_full is None:
                thread_full = self._read_thread_full(thread_id)
                if thread_full.get("status") != "OK":
                    return thread_full
            if thread_full is not None and self._terminal_attempt_needs_return_observation(
                thread_full["thread"], work_id, packet_locator, target
            ):
                try:
                    return_plan = hmasd_work_packet.reconcile_once(
                        repo=repo,
                        work_id=work_id,
                        observed_tasks=self._task_rows(observed_tasks),
                    )["plan"]
                except (hmasd_work_packet.InvalidPacket, hmasd_work_packet.PacketConflict):
                    return {
                        "status": "PROTOCOL_DEFECT",
                        "reason": "RETURN_WITNESS_INVALID",
                        "work_id": work_id,
                        "thread_id": thread_id,
                    }
                return_resolution = return_plan.get("task_resolution", {})
                if return_resolution.get("status") == "RETURN_WITNESS":
                    return {
                        "status": "NO_EFFECT",
                        "reason": "RETURN_WITNESS_PRESENT",
                        "work_id": work_id,
                        "thread_id": thread_id,
                    }
                if return_plan.get("verb") not in _DISPATCH_VERBS:
                    return {
                        "status": "PROTOCOL_DEFECT",
                        "reason": "RETURN_WITNESS_INVALID",
                        "work_id": work_id,
                        "thread_id": thread_id,
                    }
            sent = self.send(
                thread_id,
                work_id,
                packet_locator,
                target,
                repo=repo,
                root_override_reason=root_override_reason,
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
            return self.wait(
                thread_id,
                sent["turn_id"],
                timeout=wait_timeout,
                resume=delivery_status == "ALREADY_DELIVERED",
                observe_active=delivery_status == "ALREADY_DELIVERED",
            )
        return sent

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
    send.add_argument("--repo", default=".")
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
                    repo=Path(args.repo),
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
