"""Process-held exclusive lease for one A/RECON or RUN-01 invocation.

The file is a durable owner record, while exclusion is provided by an OS lock.
The kernel therefore releases exclusion on normal exit and hard process death;
the file itself is deliberately retained as invocation history.
"""

from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import sys
from typing import BinaryIO


class ActiveGateError(RuntimeError):
    pass


_PROCESS_LIFETIME_LEASES: list["ActiveInvocationGate"] = []


def _process_creation_identity() -> str:
    pid = os.getpid()
    if sys.platform == "win32":
        from ctypes import wintypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.GetProcessTimes.argtypes = (
            wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
        )
        kernel32.GetProcessTimes.restype = wintypes.BOOL
        created = wintypes.FILETIME()
        exited = wintypes.FILETIME()
        kernel = wintypes.FILETIME()
        user = wintypes.FILETIME()
        if not kernel32.GetProcessTimes(
            kernel32.GetCurrentProcess(), ctypes.byref(created), ctypes.byref(exited),
            ctypes.byref(kernel), ctypes.byref(user),
        ):
            raise ActiveGateError("process creation identity cannot be observed")
        ticks = (int(created.dwHighDateTime) << 32) | int(created.dwLowDateTime)
        return f"{pid}:{ticks}"
    try:
        start_ticks = Path(f"/proc/{pid}/stat").read_text(encoding="ascii").split()[21]
    except (OSError, IndexError) as error:
        raise ActiveGateError("process creation identity cannot be observed") from error
    return f"{pid}:{start_ticks}"


class ActiveInvocationGate:
    def __init__(self, root: str | Path, *, mode: str) -> None:
        self.root = Path(root).resolve(strict=False)
        self.mode = mode
        self.path = self.root.with_name(f".{self.root.name}.active-invocation.json")
        self.pid = os.getpid()
        self.creation_identity = _process_creation_identity()
        self._stream: BinaryIO | None = None
        self._encoded = (json.dumps({
            "schema": "SCDMP_MF_RS_MK_B01_ACTIVE_INVOCATION_V2",
            "resolved_root": str(self.root),
            "mode": mode,
            "owner_pid": self.pid,
            "owner_process_creation_identity": self.creation_identity,
            "lease_kind": "OS_HELD_EXCLUSIVE_BYTE_RANGE",
        }, sort_keys=True, separators=(",", ":")) + "\n").encode()

    @property
    def owned(self) -> bool:
        return self._stream is not None

    def acquire(self) -> None:
        if self._stream is not None:
            raise ActiveGateError("invocation already owns the active gate")
        if (self.root / "published-result.json").is_file() or (self.root / "assessment.json").is_file():
            raise ActiveGateError("published coordinate cannot acquire an active gate")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        stream = self.path.open("a+b", buffering=0)
        try:
            if self.path.stat().st_size == 0:
                stream.write(b"\0")
                stream.flush()
                os.fsync(stream.fileno())
            stream.seek(0)
            if sys.platform == "win32":
                import msvcrt
                try:
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError as error:
                    raise ActiveGateError("another invocation already owns the active gate") from error
            else:
                import fcntl
                try:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError as error:
                    raise ActiveGateError("another invocation already owns the active gate") from error
            stream.seek(0)
            stream.truncate()
            stream.write(self._encoded)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            stream.close()
            raise
        self._stream = stream

    def assert_owner(self) -> None:
        if self._stream is None or self._stream.closed:
            raise ActiveGateError("invocation does not own an active gate")
        try:
            self._stream.seek(0)
            observed = self._stream.read()
        except OSError as error:
            raise ActiveGateError("active gate is unreadable") from error
        if observed != self._encoded:
            raise ActiveGateError("active gate ownership record changed")

    def binding(self) -> dict[str, object]:
        self.assert_owner()
        return {
            "resolved_root": str(self.root), "mode": self.mode,
            "owner_pid": self.pid,
            "owner_process_creation_identity": self.creation_identity,
            "gate_path": str(self.path),
            "lease_kind": "OS_HELD_EXCLUSIVE_BYTE_RANGE",
        }

    def retain_until_process_exit(self) -> None:
        """Keep the OS handle live after an irreversible publication commit."""
        self.assert_owner()
        if self not in _PROCESS_LIFETIME_LEASES:
            _PROCESS_LIFETIME_LEASES.append(self)

    def release(self) -> None:
        self.assert_owner()
        assert self._stream is not None
        stream = self._stream
        try:
            stream.seek(0)
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        finally:
            stream.close()
            self._stream = None


__all__ = ["ActiveGateError", "ActiveInvocationGate"]
