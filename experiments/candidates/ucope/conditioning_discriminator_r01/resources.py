"""Outcome-blind process-tree, filesystem, and I/O telemetry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import threading
import time
from typing import Any
import ctypes


def directory_bytes(path: str | Path) -> int:
    root = Path(path)
    if not root.exists(): return 0
    if root.is_symlink(): raise ValueError("resource root may not be a symlink")
    total = 0
    for item in root.rglob("*"):
        if item.is_symlink(): raise ValueError("resource tree may not contain symlinks")
        if item.is_file(): total += item.stat().st_size
    return total


def _tree_sample() -> dict[str, int]:
    try:
        import psutil
    except ImportError:
        if os.name == "nt":
            return _windows_tree_sample()
        return _portable_self_sample()
    root = psutil.Process(os.getpid()); processes = [root, *root.children(recursive=True)]
    rss = threads = read_bytes = write_bytes = 0; live = 0; cpu = 0.0
    for process in processes:
        try:
            rss += process.memory_info().rss; threads += process.num_threads(); io = process.io_counters()
            read_bytes += io.read_bytes; write_bytes += io.write_bytes; times = process.cpu_times(); cpu += times.user + times.system; live += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return {"rss_bytes": rss, "threads": threads, "processes": live, "io_read_bytes": read_bytes, "io_write_bytes": write_bytes, "cpu_milliseconds": int(cpu * 1000)}


def _windows_tree_sample() -> dict[str, int]:
    """Observe this process and descendants through Win32, without helpers."""
    from ctypes import wintypes
    class Entry(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("pid", wintypes.DWORD), ("heap", ctypes.c_size_t), ("module", wintypes.DWORD), ("threads", wintypes.DWORD), ("parent", wintypes.DWORD), ("priority", ctypes.c_long), ("flags", wintypes.DWORD), ("exe", wintypes.WCHAR * 260)]
    class Memory(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD), ("peak_ws", ctypes.c_size_t), ("working_set", ctypes.c_size_t), ("qpp", ctypes.c_size_t), ("qp", ctypes.c_size_t), ("qnpp", ctypes.c_size_t), ("qnp", ctypes.c_size_t), ("pagefile", ctypes.c_size_t), ("peak_pagefile", ctypes.c_size_t)]
    class Io(ctypes.Structure):
        _fields_ = [("read_ops", ctypes.c_ulonglong), ("write_ops", ctypes.c_ulonglong), ("other_ops", ctypes.c_ulonglong), ("read_bytes", ctypes.c_ulonglong), ("write_bytes", ctypes.c_ulonglong), ("other_bytes", ctypes.c_ulonglong)]
    kernel, psapi = ctypes.WinDLL("kernel32", use_last_error=True), ctypes.WinDLL("psapi", use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]; kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]; kernel.Process32FirstW.restype = wintypes.BOOL
    kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]; kernel.Process32NextW.restype = wintypes.BOOL
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]; kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]; kernel.CloseHandle.restype = wintypes.BOOL
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Memory), wintypes.DWORD]; psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    kernel.GetProcessIoCounters.argtypes = [wintypes.HANDLE, ctypes.POINTER(Io)]; kernel.GetProcessIoCounters.restype = wintypes.BOOL
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME)]; kernel.GetProcessTimes.restype = wintypes.BOOL
    snapshot = kernel.CreateToolhelp32Snapshot(0x2, 0)
    if snapshot == ctypes.c_void_p(-1).value: raise RuntimeError("process-tree snapshot failed")
    entries = []
    try:
        item = Entry(); item.dwSize = ctypes.sizeof(item); present = kernel.Process32FirstW(snapshot, ctypes.byref(item))
        while present:
            entries.append((int(item.pid), int(item.parent), int(item.threads))); item.dwSize = ctypes.sizeof(item); present = kernel.Process32NextW(snapshot, ctypes.byref(item))
    finally: kernel.CloseHandle(snapshot)
    descendants = {os.getpid()}
    while True:
        expanded = descendants | {pid for pid, parent, _ in entries if parent in descendants}
        if expanded == descendants: break
        descendants = expanded
    thread_map = {pid: threads for pid, _, threads in entries}; rss = read = write = cpu_ms = live = threads = 0
    for pid in sorted(descendants):
        handle = kernel.GetCurrentProcess() if pid == os.getpid() else kernel.OpenProcess(0x1000 | 0x10, False, pid)
        if not handle: continue
        try:
            memory, io = Memory(), Io(); memory.cb = ctypes.sizeof(memory)
            creation, exit_time, kernel_time, user_time = wintypes.FILETIME(), wintypes.FILETIME(), wintypes.FILETIME(), wintypes.FILETIME()
            if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(memory), memory.cb): continue
            if not kernel.GetProcessIoCounters(handle, ctypes.byref(io)): continue
            if not kernel.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_time), ctypes.byref(kernel_time), ctypes.byref(user_time)): continue
            filetime = lambda value: (int(value.dwHighDateTime) << 32) | int(value.dwLowDateTime)
            rss += int(memory.working_set); read += int(io.read_bytes); write += int(io.write_bytes); cpu_ms += int((filetime(kernel_time) + filetime(user_time)) / 10_000); threads += thread_map.get(pid, 0); live += 1
        finally:
            if pid != os.getpid(): kernel.CloseHandle(handle)
    return {"rss_bytes": rss, "threads": threads, "processes": live, "io_read_bytes": read, "io_write_bytes": write, "cpu_milliseconds": cpu_ms}


def _portable_self_sample() -> dict[str, int]:  # pragma: no cover - Windows production host
    import resource
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {"rss_bytes": int(usage.ru_maxrss * 1024), "threads": threading.active_count(), "processes": 1, "io_read_bytes": int(usage.ru_inblock * 512), "io_write_bytes": int(usage.ru_oublock * 512), "cpu_milliseconds": int((usage.ru_utime + usage.ru_stime) * 1000)}


class ResourceMonitor:
    def __init__(self, scratch: str | Path, durable: str | Path, interval: float = 0.05):
        self.scratch, self.durable, self.interval = Path(scratch), Path(durable), interval
        self._stop = threading.Event(); self._thread = None; self._samples = []

    def start(self) -> "ResourceMonitor":
        if self._thread is not None: raise RuntimeError("monitor already started")
        self._wall = time.perf_counter(); self._baseline = _tree_sample()
        def loop():
            while not self._stop.wait(self.interval): self._capture()
        self._capture(); self._thread = threading.Thread(target=loop, name="ucope-resource-monitor", daemon=True); self._thread.start(); return self

    def _capture(self):
        row = _tree_sample(); row["scratch_bytes"] = directory_bytes(self.scratch); row["durable_bytes"] = directory_bytes(self.durable); self._samples.append(row)

    def finish(self) -> dict[str, Any]:
        if self._thread is None: raise RuntimeError("monitor not started")
        self._stop.set(); self._thread.join(); self._capture(); end = _tree_sample()
        wall_seconds = time.perf_counter() - self._wall
        cpu_seconds = max(0, end["cpu_milliseconds"] - self._baseline["cpu_milliseconds"]) / 1000
        logical_cpus = os.cpu_count() or 1
        cpu_core_equivalents = cpu_seconds / wall_seconds if wall_seconds > 0 else 0.0
        io_read = max(0, end["io_read_bytes"] - self._baseline["io_read_bytes"])
        io_write = max(0, end["io_write_bytes"] - self._baseline["io_write_bytes"])
        return {
            "wall_seconds": wall_seconds,
            "process_tree_peak_rss_bytes": max(row["rss_bytes"] for row in self._samples),
            "process_count_peak": max(row["processes"] for row in self._samples),
            "thread_count_peak": max(row["threads"] for row in self._samples),
            "scratch_high_water_bytes": max(row["scratch_bytes"] for row in self._samples),
            "durable_high_water_bytes": max(row["durable_bytes"] for row in self._samples),
            "io_read_bytes": io_read, "io_write_bytes": io_write,
            "aggregate_io_bytes": io_read + io_write,
            "cpu_seconds": cpu_seconds, "cpu_core_equivalents": cpu_core_equivalents,
            "logical_cpu_count": logical_cpus, "host_cpu_occupancy": cpu_core_equivalents / logical_cpus,
            "samples": len(self._samples), "root_process_count": 1,
            "child_process_count_peak": max(0, max(row["processes"] for row in self._samples) - 1),
        }
