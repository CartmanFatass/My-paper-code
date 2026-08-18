"""JSONL stdio transport for one owned `codex app-server` child process."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .models import ObserverConfig, TransportMessage
from .protocol import ProtocolError, ProtocolLineTooLarge, decode_jsonl_line, encode_jsonl


class TransportClosed(RuntimeError):
    """Raised when the App Server process stdout ends or the transport stops."""


def process_exec_argv(binary: Path) -> list[str]:
    """Return argv that CreateProcess can start.

    Official launch is `<codex> app-server`. On Windows a `.cmd`/`.bat` shim
    cannot be the CreateProcess image, so prefix `COMSPEC /d /s /c`.
    """

    resolved = Path(binary)
    if os.name == "nt" and resolved.suffix.lower() in {".cmd", ".bat"}:
        comspec = os.environ.get("COMSPEC") or "cmd.exe"
        return [comspec, "/d", "/s", "/c", str(resolved)]
    return [str(resolved)]


async def _windows_kill_tree(pid: int, *, force: bool) -> None:
    system_root = os.environ.get("SystemRoot") or r"C:\Windows"
    taskkill = str(Path(system_root) / "System32" / "taskkill.exe")
    argv = [taskkill, "/PID", str(pid), "/T"]
    if force:
        argv.append("/F")
    killer = await asyncio.create_subprocess_exec(
        *argv,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await killer.wait()


class AppServerTransport:
    def __init__(
        self,
        binary: Path,
        config: ObserverConfig,
        process_cwd: Path,
        stderr_path: Path,
        *,
        stdin_close_timeout: float = 5.0,
        terminate_timeout: float = 5.0,
        extra_env: Mapping[str, str] | None = None,
    ) -> None:
        self.binary = Path(binary)
        self.config = config
        self.process_cwd = Path(process_cwd)
        self.stderr_path = Path(stderr_path)
        self.stdin_close_timeout = stdin_close_timeout
        self.terminate_timeout = terminate_timeout
        self.extra_env = dict(extra_env or {})
        self._process: asyncio.subprocess.Process | None = None
        self._send_lock = asyncio.Lock()
        self._seq = 0
        self._closed = False
        self._stderr_task: asyncio.Task[None] | None = None
        self.end_action = "open"

    @property
    def process_id(self) -> int | None:
        return None if self._process is None else self._process.pid

    async def start(self) -> None:
        if self._process is not None:
            raise RuntimeError("transport already started")
        self.stderr_path.parent.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.update(self.extra_env)
        argv = process_exec_argv(self.binary)
        self._process = await asyncio.create_subprocess_exec(
            *argv,
            "app-server",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=self.config.max_jsonl_line_bytes + 1,
            cwd=str(self.process_cwd),
            env=env,
        )
        self._stderr_task = asyncio.create_task(self._drain_stderr())

    async def send(self, message: dict[str, Any]) -> bytes:
        if self._closed or self._process is None or self._process.stdin is None:
            raise TransportClosed("transport is not started")
        payload = encode_jsonl(message)
        async with self._send_lock:
            if self._closed or self._process.stdin.is_closing():
                raise TransportClosed("transport stdin is closed")
            self._process.stdin.write(payload)
            await self._process.stdin.drain()
        return payload

    async def recv(self) -> TransportMessage:
        if self._closed or self._process is None or self._process.stdout is None:
            raise TransportClosed("transport is not started")
        try:
            line = await self._process.stdout.readline()
        except ValueError as exc:
            self._closed = True
            self.end_action = "line_too_large"
            raise ProtocolLineTooLarge(str(exc)) from exc
        if not line:
            self._closed = True
            self.end_action = "eof"
            raise TransportClosed("stdout EOF")
        try:
            decoded = decode_jsonl_line(line, self.config.max_jsonl_line_bytes)
        except ProtocolLineTooLarge:
            self._closed = True
            self.end_action = "line_too_large"
            raise
        except ProtocolError:
            self._closed = True
            self.end_action = "malformed"
            raise
        self._seq += 1
        return TransportMessage(
            transport_seq=self._seq,
            payload=decoded,
            observed_at=datetime.now(timezone.utc).isoformat(),
        )

    async def _drain_stderr(self) -> None:
        if self._process is None or self._process.stderr is None:
            return
        with self.stderr_path.open("ab") as handle:
            while True:
                chunk = await self._process.stderr.read(4096)
                if not chunk:
                    return
                handle.write(chunk)
                handle.flush()

    async def _close_stderr_task(self) -> None:
        if self._stderr_task is None:
            return
        task = self._stderr_task
        self._stderr_task = None
        if task.done():
            return
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass

    async def _signal_stop(self, process: asyncio.subprocess.Process, *, force: bool) -> None:
        if process.returncode is not None:
            return
        if os.name == "nt" and process.pid is not None:
            await _windows_kill_tree(process.pid, force=force)
            return
        if force:
            process.kill()
        else:
            process.terminate()

    async def stop(self) -> str:
        if self._process is None:
            self._closed = True
            return self.end_action
        process = self._process
        self._closed = True
        if process.stdin is not None and not process.stdin.is_closing():
            process.stdin.close()
            try:
                await process.stdin.wait_closed()
            except Exception:
                pass
        try:
            await asyncio.wait_for(process.wait(), timeout=self.stdin_close_timeout)
            if self.end_action == "open":
                self.end_action = "stdin_closed"
            await self._close_stderr_task()
            return self.end_action
        except asyncio.TimeoutError:
            await self._signal_stop(process, force=False)
        try:
            await asyncio.wait_for(process.wait(), timeout=self.terminate_timeout)
            if self.end_action == "open":
                self.end_action = "terminated"
            await self._close_stderr_task()
            return self.end_action
        except asyncio.TimeoutError:
            await self._signal_stop(process, force=True)
            await process.wait()
            if self.end_action == "open":
                self.end_action = "killed"
            await self._close_stderr_task()
            return self.end_action
