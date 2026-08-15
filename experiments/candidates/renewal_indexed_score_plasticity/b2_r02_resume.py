"""Atomic, resumable, result-blind frontier for RISP-B2 revision 02."""

from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

from b2_r02_experiment import (
    ALGORITHM_SEEDS,
    RESULT_SCHEMA,
    SCIENCE_REVISION,
    analyze_complete,
    atomic_write_json,
    run_seed,
    structural_certificate,
)


FRONTIER_SCHEMA = "RISP-B2-R02-RESUME-20260814-02"
DEFAULT_FRONTIER_NAME = "RISP_B2_R02_RESUME_20260814_02"
DEFAULT_RESULT_NAME = "RISP_B2_R02_20260814_02.json"


class SliceExpired(RuntimeError):
    pass


def _peak_rss_bytes() -> int | None:
    try:
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        get_current_process = kernel32.GetCurrentProcess
        get_current_process.argtypes = ()
        get_current_process.restype = wintypes.HANDLE
        get_process_memory_info = psapi.GetProcessMemoryInfo
        get_process_memory_info.argtypes = (wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD)
        get_process_memory_info.restype = wintypes.BOOL
        handle = get_current_process()
        if not get_process_memory_info(handle, ctypes.byref(counters), counters.cb):
            return None
        return int(counters.PeakWorkingSetSize)
    except Exception:
        return None


@dataclass
class Frontier:
    root: Path
    result: Path
    slice_wall_seconds: float
    rss_limit_bytes: int
    started: float

    @property
    def units(self) -> Path:
        return self.root / "seed_units"

    @property
    def receipts(self) -> Path:
        return self.root / "slice_receipts"

    def elapsed(self) -> float:
        return time.monotonic() - self.started

    def assert_resources(self) -> None:
        rss = _peak_rss_bytes()
        if rss is not None and rss >= self.rss_limit_bytes:
            raise RuntimeError(f"process RSS {rss} exceeds lease limit {self.rss_limit_bytes}")

    def seed_path(self, seed: int) -> Path:
        return self.units / f"seed_{seed:02d}.json"

    def committed_seeds(self) -> tuple[int, ...]:
        present: list[int] = []
        for seed in ALGORITHM_SEEDS:
            path = self.seed_path(seed)
            if path.exists():
                with path.open("r", encoding="utf-8") as handle:
                    packet = json.load(handle)
                if packet.get("science_revision") != SCIENCE_REVISION or packet.get("algorithm_seed") != seed or packet.get("registered") is not True:
                    raise RuntimeError(f"invalid committed seed packet {path}")
                present.append(seed)
        return tuple(present)


def _initialize(frontier: Frontier) -> None:
    frontier.root.mkdir(parents=True, exist_ok=True)
    frontier.units.mkdir(parents=True, exist_ok=True)
    frontier.receipts.mkdir(parents=True, exist_ok=True)
    manifest = frontier.root / "manifest.json"
    expected = {
        "schema": FRONTIER_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "algorithm_seeds": list(ALGORITHM_SEEDS),
        "result": str(frontier.result.resolve()),
        "production_threads": 1,
        "partial_scientific_values_exposed": False,
    }
    if manifest.exists():
        with manifest.open("r", encoding="utf-8") as handle:
            found = json.load(handle)
        if found != expected:
            raise RuntimeError("frontier manifest mismatch")
    else:
        atomic_write_json(manifest, expected)


def _next_receipt(frontier: Frontier) -> Path:
    index = 0
    while (frontier.receipts / f"slice_{index:04d}.json").exists():
        index += 1
    return frontier.receipts / f"slice_{index:04d}.json"


@contextmanager
def _exclusive_frontier(root: Path):
    """Hold an OS-released one-process lock for the frontier lifetime."""
    import msvcrt

    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / "PRODUCTION.lock"
    with lock_path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            raise RuntimeError(f"frontier already has an active production process: {root}") from error
        try:
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def _finalize(frontier: Frontier) -> dict[str, Any]:
    packets: list[dict[str, Any]] = []
    for seed in ALGORITHM_SEEDS:
        with frontier.seed_path(seed).open("r", encoding="utf-8") as handle:
            packets.append(json.load(handle))
    analysis = analyze_complete(packets)
    if analysis.get("schema") != RESULT_SCHEMA or analysis.get("complete_panel") is not True:
        raise RuntimeError("complete analyzer did not return a complete result")
    ledger: dict[str, int] = {}
    for packet in packets:
        for kind, count in packet["sampler_audit"]["calls"].items():
            ledger[kind] = ledger.get(kind, 0) + int(count)
    expected = {"INIT_MODEL": 960, "INIT_TARGET": 323584, "ACTION": 11304960, "OUTCOME": 11304960, "ALT": 11304960, "TWIN": 602112}
    if ledger != expected:
        raise RuntimeError(f"complete ledger mismatch: {ledger} != {expected}")
    retained = {
        **analysis,
        "structural_certificate": structural_certificate(),
        "ledger": ledger,
        "seed_unit_paths": [str(frontier.seed_path(seed).resolve()) for seed in ALGORITHM_SEEDS],
        "peak_rss_bytes": _peak_rss_bytes(),
        "partial_scientific_values_exposed": False,
    }
    atomic_write_json(frontier.result, retained)
    atomic_write_json(frontier.root / "FINAL_COMPLETE.commit.json", {"schema": FRONTIER_SCHEMA, "science_revision": SCIENCE_REVISION, "result": str(frontier.result.resolve()), "complete_panel": True})
    return retained


def _run_slice_locked(root: Path, result: Path, slice_wall_seconds: float, rss_limit_bytes: int) -> dict[str, Any]:
    if slice_wall_seconds <= 0:
        raise ValueError("slice wall seconds must be positive")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    frontier = Frontier(root.resolve(), result.resolve(), slice_wall_seconds, rss_limit_bytes, time.monotonic())
    _initialize(frontier)
    certificate = structural_certificate()
    if not certificate["passed"]:
        raise RuntimeError("structural certificate failed")
    before = frontier.committed_seeds()
    if frontier.result.exists():
        with frontier.result.open("r", encoding="utf-8") as handle:
            complete = json.load(handle)
        if complete.get("complete_panel") is not True or complete.get("science_revision") != SCIENCE_REVISION:
            raise RuntimeError("retained result is not the exact complete object")
        status = "COMPLETE"
    else:
        durations = []
        for seed in ALGORITHM_SEEDS:
            if seed in before:
                continue
            frontier.assert_resources()
            remaining = slice_wall_seconds - frontier.elapsed()
            reserve = max(120.0, (max(durations) * 1.25 if durations else 0.0) + 60.0)
            if durations and remaining <= reserve:
                break
            seed_started = time.monotonic()
            def progress_guard() -> None:
                frontier.assert_resources()
                if frontier.elapsed() + 120.0 >= slice_wall_seconds:
                    raise SliceExpired("slice finalization reserve reached")

            try:
                packet = run_seed(seed, progress_guard=progress_guard)
            except SliceExpired:
                break
            frontier.assert_resources()
            atomic_write_json(frontier.seed_path(seed), packet)
            durations.append(time.monotonic() - seed_started)
            if frontier.elapsed() + 120.0 >= slice_wall_seconds:
                break
        committed = frontier.committed_seeds()
        if committed == ALGORITHM_SEEDS:
            _finalize(frontier)
            status = "COMPLETE"
        else:
            status = "PARTIAL"
    after = frontier.committed_seeds()
    receipt_path = _next_receipt(frontier)
    receipt = {
        "schema": FRONTIER_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "status": status,
        "committed_seed_count_before": len(before),
        "committed_seed_count_after": len(after),
        "elapsed_seconds": frontier.elapsed(),
        "peak_rss_bytes": _peak_rss_bytes(),
        "partial_scientific_values_exposed": False,
        "result": str(frontier.result),
    }
    atomic_write_json(receipt_path, receipt)
    return {"schema": FRONTIER_SCHEMA, "status": status, "receipt": str(receipt_path.resolve()), "result": str(frontier.result.resolve()), "partial_scientific_values_exposed": False}


def run_slice(root: Path, result: Path, slice_wall_seconds: float, rss_limit_bytes: int) -> dict[str, Any]:
    root = root.resolve()
    with _exclusive_frontier(root):
        return _run_slice_locked(root, result, slice_wall_seconds, rss_limit_bytes)


def default_paths(module_path: Path) -> tuple[Path, Path]:
    return module_path.parent / DEFAULT_FRONTIER_NAME, module_path.parent / DEFAULT_RESULT_NAME
