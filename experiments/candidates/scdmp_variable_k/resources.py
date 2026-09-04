from __future__ import annotations

import ctypes
import os
import time
from ctypes import wintypes
from dataclasses import dataclass, field

from .config import REGISTERED_RESOURCES


class ResourceLimitExceeded(RuntimeError):
    pass


def _resident_bytes() -> int:
    if os.name == "nt":
        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t),
            ]
        counters = Counters()
        counters.cb = ctypes.sizeof(Counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.argtypes = ()
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = (
            wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD,
        )
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        process = kernel32.GetCurrentProcess()
        ok = psapi.GetProcessMemoryInfo(
            process, ctypes.byref(counters), counters.cb,
        )
        if not ok:
            error = ctypes.get_last_error()
            raise ctypes.WinError(error)
        return int(counters.PeakWorkingSetSize)
    import resource
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if value > 10_000_000 else value * 1024


@dataclass
class ResourceMonitor:
    started: float = field(default_factory=time.perf_counter)
    peak_rss_bytes: int = 0
    checks: int = 0

    def check(self) -> None:
        elapsed = time.perf_counter() - self.started
        rss = _resident_bytes()
        self.checks += 1
        self.peak_rss_bytes = max(self.peak_rss_bytes, rss)
        if elapsed > REGISTERED_RESOURCES.wall_limit_seconds:
            raise ResourceLimitExceeded(
                f"wall limit exceeded: {elapsed:.3f}s > {REGISTERED_RESOURCES.wall_limit_seconds}s"
            )
        if rss > REGISTERED_RESOURCES.rss_limit_bytes:
            raise ResourceLimitExceeded(
                f"RSS limit exceeded: {rss} > {REGISTERED_RESOURCES.rss_limit_bytes}"
            )

    def facts(self) -> dict[str, object]:
        self.check()
        return self.snapshot()

    def snapshot(self) -> dict[str, object]:
        return {
            "wall_seconds": float(time.perf_counter() - self.started),
            "peak_rss_bytes_process_lifetime": self.peak_rss_bytes,
            "resource_check_count": self.checks,
            "cpu_workers": 1,
            "gpu_visible": False,
            "wall_limit_seconds": REGISTERED_RESOURCES.wall_limit_seconds,
            "rss_limit_bytes": REGISTERED_RESOURCES.rss_limit_bytes,
        }
