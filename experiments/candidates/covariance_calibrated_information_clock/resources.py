"""Hard wall-clock and process-RSS enforcement for the production lifecycle."""

from __future__ import annotations

import ctypes
import os
import sys
import threading
import time
from dataclasses import dataclass


class ResourceBudgetExceeded(RuntimeError):
    pass


def process_rss_bytes() -> int:
    if sys.platform == "win32":
        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.argtypes = ()
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        psapi.GetProcessMemoryInfo.argtypes = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong)
        psapi.GetProcessMemoryInfo.restype = ctypes.c_int
        handle = kernel32.GetCurrentProcess()
        if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            raise OSError("GetProcessMemoryInfo failed")
        return int(counters.PeakWorkingSetSize)
    import resource

    maximum = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(maximum if sys.platform == "darwin" else maximum * 1024)


@dataclass
class ResourceMonitor:
    wall_seconds_ceiling: float = 5400.0
    rss_bytes_ceiling: int = 4 * 1024**3

    def __post_init__(self) -> None:
        self.started = time.monotonic()
        self.peak_rss_bytes = 0
        self._lock = threading.Lock()
        self._violation: str | None = None

    def check(self) -> None:
        elapsed = time.monotonic() - self.started
        rss = process_rss_bytes()
        with self._lock:
            self.peak_rss_bytes = max(self.peak_rss_bytes, rss)
            if elapsed > self.wall_seconds_ceiling:
                self._violation = f"wall ceiling exceeded: {elapsed:.6f}s > {self.wall_seconds_ceiling}s"
            elif rss > self.rss_bytes_ceiling:
                self._violation = f"RSS ceiling exceeded: {rss} > {self.rss_bytes_ceiling} bytes"
            violation = self._violation
        if violation is not None:
            raise ResourceBudgetExceeded(violation)

    def record(self) -> dict:
        self.check()
        return {
            "elapsed_seconds": time.monotonic() - self.started,
            "peak_process_rss_bytes": self.peak_rss_bytes,
            "wall_seconds_ceiling": self.wall_seconds_ceiling,
            "rss_bytes_ceiling": self.rss_bytes_ceiling,
            "within_ceiling": self._violation is None,
        }
