"""Result-blind, one-process, atomic/resumable RISP-B3/R03 frontier."""

from __future__ import annotations

import hashlib
import json
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import torch

from b3_r03_experiment import (
    ALGORITHM_SEEDS,
    ARCHITECTURES,
    CELL_FAMILIES,
    COORDINATE_ROOT,
    COORDINATE_SCHEMA,
    EVALUATION_SCHEMA,
    RESULT_SCHEMA,
    SCIENCE_CARD_SHA256,
    SCIENCE_REVISION,
    TRAINING_SCHEMA,
    analyze_complete,
    atomic_write_json,
    expected_complete_ledger,
    run_evaluation_unit,
    run_training_unit,
    structural_certificate,
)


FRONTIER_SCHEMA = "RISP-B3-TRG-R03-RESUME-20260815-03"
DEFAULT_FRONTIER_NAME = "RISP_B3_R03_RESUME_20260815_03"
DEFAULT_RESULT_ROOT_NAME = "RISP_B3_R03_RESULTS_20260815_03"
DEFAULT_RESULT_NAME = "RISP_B3_R03_20260815_03.json"


class SliceExpired(RuntimeError):
    pass


def _peak_rss_bytes() -> int | None:
    try:
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
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
        if not get_process_memory_info(get_current_process(), ctypes.byref(counters), counters.cb):
            return None
        return int(counters.PeakWorkingSetSize)
    except Exception:
        return None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _unit_id_training(seed: int, architecture: str) -> str:
    return f"train__seed_{seed:02d}__{architecture}"


def _unit_id_evaluation(seed: int, cell: str, schedule: int) -> str:
    safe_cell = cell.replace("|", "__")
    return f"eval__seed_{seed:02d}__{safe_cell}__schedule_{schedule}"


def unit_plan() -> tuple[tuple[str, int, str, int | None], ...]:
    result: list[tuple[str, int, str, int | None]] = []
    for seed in ALGORITHM_SEEDS:
        for architecture in ARCHITECTURES:
            result.append(("TRAIN", seed, architecture, None))
        for cell in CELL_FAMILIES:
            for schedule in range(5):
                result.append(("EVAL", seed, cell, schedule))
    return tuple(result)


@dataclass
class Frontier:
    root: Path
    result_root: Path
    result: Path
    certificate: Path
    slice_wall_seconds: float
    rss_limit_bytes: int
    started: float

    @property
    def training_root(self) -> Path:
        return self.root / "training_units"

    @property
    def evaluation_root(self) -> Path:
        return self.root / "evaluation_units"

    @property
    def receipts(self) -> Path:
        return self.root / "slice_receipts"

    def elapsed(self) -> float:
        return time.monotonic() - self.started

    def assert_resources(self) -> None:
        peak = _peak_rss_bytes()
        if peak is not None and peak >= self.rss_limit_bytes:
            raise RuntimeError(f"process peak RSS {peak} exceeds limit {self.rss_limit_bytes}")

    def paths(self, item: tuple[str, int, str, int | None]) -> tuple[Path, Path]:
        phase, seed, name, schedule = item
        unit_id = _unit_id_training(seed, name) if phase == "TRAIN" else _unit_id_evaluation(seed, name, int(schedule))
        root = self.training_root if phase == "TRAIN" else self.evaluation_root
        return root / f"{unit_id}.json", root / f"{unit_id}.commit.json"

    def committed(self, item: tuple[str, int, str, int | None]) -> bool:
        packet_path, commit_path = self.paths(item)
        if not packet_path.exists() and not commit_path.exists():
            return False
        if not packet_path.exists() or not commit_path.exists():
            raise RuntimeError(f"torn atomic unit {packet_path}")
        with commit_path.open("r", encoding="utf-8") as handle:
            commit = json.load(handle)
        phase, seed, name, schedule = item
        expected_schema = TRAINING_SCHEMA if phase == "TRAIN" else EVALUATION_SCHEMA
        with packet_path.open("r", encoding="utf-8") as handle:
            packet = json.load(handle)
        if commit.get("sha256") != _sha256(packet_path) or packet.get("schema") != expected_schema or packet.get("science_revision") != SCIENCE_REVISION or packet.get("registered") is not True or packet.get("algorithm_seed") != seed:
            raise RuntimeError(f"invalid atomic unit {packet_path}")
        if phase == "TRAIN" and packet.get("architecture") != name:
            raise RuntimeError(f"training identity mismatch {packet_path}")
        if phase == "EVAL" and (packet.get("cell") != name or packet.get("schedule_id") != schedule):
            raise RuntimeError(f"evaluation identity mismatch {packet_path}")
        return True


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _certificate_hash(path: Path) -> str:
    if not path.exists():
        raise RuntimeError(f"missing preactivity certificate {path}")
    certificate = _load_json(path)
    if certificate.get("science_revision") != SCIENCE_REVISION or certificate.get("science_card_sha256") != SCIENCE_CARD_SHA256 or certificate.get("coordinate_schema") != COORDINATE_SCHEMA or certificate.get("coordinate_root") != COORDINATE_ROOT or certificate.get("technical_acceptance") is not True:
        raise RuntimeError("preactivity certificate binding mismatch")
    return _sha256(path)


def _initialize(frontier: Frontier) -> None:
    frontier.root.mkdir(parents=True, exist_ok=True)
    frontier.result_root.mkdir(parents=True, exist_ok=True)
    frontier.training_root.mkdir(parents=True, exist_ok=True)
    frontier.evaluation_root.mkdir(parents=True, exist_ok=True)
    frontier.receipts.mkdir(parents=True, exist_ok=True)
    manifest_path = frontier.root / "manifest.json"
    expected = {
        "schema": FRONTIER_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "science_card_sha256": SCIENCE_CARD_SHA256,
        "coordinate_schema": COORDINATE_SCHEMA,
        "coordinate_root": COORDINATE_ROOT,
        "algorithm_seeds": list(ALGORITHM_SEEDS),
        "cell_families": list(CELL_FAMILIES),
        "schedules": list(range(5)),
        "unit_count": len(unit_plan()),
        "result": str(frontier.result.resolve()),
        "preactivity_certificate": str(frontier.certificate.resolve()),
        "preactivity_certificate_sha256": _certificate_hash(frontier.certificate),
        "production_threads": 1,
        "partial_scientific_values_exposed": False,
    }
    if manifest_path.exists():
        if _load_json(manifest_path) != expected:
            raise RuntimeError("frontier manifest mismatch")
    else:
        atomic_write_json(manifest_path, expected)


def _write_unit(frontier: Frontier, item: tuple[str, int, str, int | None], packet: dict[str, Any]) -> None:
    packet_path, commit_path = frontier.paths(item)
    atomic_write_json(packet_path, packet)
    atomic_write_json(commit_path, {"schema": FRONTIER_SCHEMA, "science_revision": SCIENCE_REVISION, "unit": packet_path.stem, "sha256": _sha256(packet_path)})


def _checkpoint_states(frontier: Frontier, seed: int) -> dict[str, dict[str, Any]]:
    states: dict[str, dict[str, Any]] = {}
    for architecture in ARCHITECTURES:
        item = ("TRAIN", seed, architecture, None)
        if not frontier.committed(item):
            raise RuntimeError(f"evaluation reached before checkpoint {seed} {architecture}")
        packet_path, _ = frontier.paths(item)
        states[architecture] = _load_json(packet_path)["final_state"]
    return states


def _next_receipt(frontier: Frontier) -> Path:
    index = 0
    while (frontier.receipts / f"slice_{index:04d}.json").exists():
        index += 1
    return frontier.receipts / f"slice_{index:04d}.json"


@contextmanager
def _exclusive_frontier(root: Path):
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
            raise RuntimeError(f"frontier already active: {root}") from error
        try:
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def _aggregate_ledger(training: list[dict[str, Any]], evaluation: list[dict[str, Any]]) -> dict[str, int]:
    result: dict[str, int] = {}
    # Initialization coordinates are paired and reused between the two arms;
    # count each seed's 60 unique identities once.
    for seed in ALGORITHM_SEEDS:
        first = next(unit for unit in training if unit["algorithm_seed"] == seed and unit["architecture"] == ARCHITECTURES[0])
        result["INIT_MODEL"] = result.get("INIT_MODEL", 0) + first["sampler_audit"]["calls"]["INIT_MODEL"]
    for unit in training:
        for kind, count in unit["sampler_audit"]["calls"].items():
            if kind != "INIT_MODEL":
                result[kind] = result.get(kind, 0) + int(count)
    for unit in evaluation:
        for kind, count in unit["sampler_audit"]["calls"].items():
            result[kind] = result.get(kind, 0) + int(count)
    return dict(sorted(result.items()))


def _finalize(frontier: Frontier) -> None:
    training: list[dict[str, Any]] = []
    evaluation: list[dict[str, Any]] = []
    for item in unit_plan():
        if not frontier.committed(item):
            raise RuntimeError("finalization reached incomplete frontier")
        packet_path, _ = frontier.paths(item)
        packet = _load_json(packet_path)
        (training if item[0] == "TRAIN" else evaluation).append(packet)
    analysis = analyze_complete(training, evaluation)
    if analysis.get("schema") != RESULT_SCHEMA or analysis.get("complete_panel") is not True:
        raise RuntimeError("analyzer did not produce exact complete panel")
    ledger = _aggregate_ledger(training, evaluation)
    if ledger != expected_complete_ledger():
        raise RuntimeError(f"complete ledger mismatch: {ledger} != {expected_complete_ledger()}")
    retained = {
        **analysis,
        "structural_certificate": structural_certificate(),
        "coordinate_schema": COORDINATE_SCHEMA,
        "coordinate_root": COORDINATE_ROOT,
        "ledger": ledger,
        "training_unit_paths": [str(frontier.paths(item)[0].resolve()) for item in unit_plan() if item[0] == "TRAIN"],
        "evaluation_unit_paths": [str(frontier.paths(item)[0].resolve()) for item in unit_plan() if item[0] == "EVAL"],
        "peak_rss_bytes": _peak_rss_bytes(),
        "partial_scientific_values_exposed": False,
    }
    atomic_write_json(frontier.result, retained)
    atomic_write_json(frontier.root / "FINAL_COMPLETE.commit.json", {"schema": FRONTIER_SCHEMA, "science_revision": SCIENCE_REVISION, "result": str(frontier.result.resolve()), "result_sha256": _sha256(frontier.result), "complete_panel": True})


def _run_one(frontier: Frontier, item: tuple[str, int, str, int | None], guard: Callable[[], None]) -> None:
    phase, seed, name, schedule = item
    if phase == "TRAIN":
        packet = run_training_unit(seed, name, progress_guard=guard)
    else:
        packet = run_evaluation_unit(seed, name, int(schedule), _checkpoint_states(frontier, seed), progress_guard=guard)
    frontier.assert_resources()
    _write_unit(frontier, item, packet)


def _run_slice_locked(frontier: Frontier) -> dict[str, Any]:
    if frontier.slice_wall_seconds <= 0:
        raise ValueError("slice wall seconds must be positive")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    _initialize(frontier)
    if not structural_certificate()["passed"]:
        raise RuntimeError("structural certificate failed")
    plan = unit_plan()
    before = sum(frontier.committed(item) for item in plan)
    if frontier.result.exists():
        complete = _load_json(frontier.result)
        if complete.get("complete_panel") is not True or complete.get("science_revision") != SCIENCE_REVISION:
            raise RuntimeError("retained result mismatch")
        status = "COMPLETE"
    else:
        durations: list[float] = []
        for item in plan:
            if frontier.committed(item):
                continue
            reserve = max(300.0, (max(durations) * 1.35 if durations else 0.0) + 120.0)
            if durations and frontier.slice_wall_seconds - frontier.elapsed() <= reserve:
                break
            started = time.monotonic()

            def guard() -> None:
                frontier.assert_resources()
                if frontier.elapsed() + 300.0 >= frontier.slice_wall_seconds:
                    raise SliceExpired("slice reserve reached before atomic commit")

            try:
                _run_one(frontier, item, guard)
            except SliceExpired:
                break
            durations.append(time.monotonic() - started)
            if frontier.elapsed() + 300.0 >= frontier.slice_wall_seconds:
                break
        after_now = sum(frontier.committed(item) for item in plan)
        if after_now == len(plan):
            _finalize(frontier)
            status = "COMPLETE"
        else:
            status = "PARTIAL"
    after = sum(frontier.committed(item) for item in plan)
    receipt_path = _next_receipt(frontier)
    atomic_write_json(receipt_path, {
        "schema": FRONTIER_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "status": status,
        "committed_atomic_units_before": before,
        "committed_atomic_units_after": after,
        "registered_atomic_units": len(plan),
        "elapsed_seconds": frontier.elapsed(),
        "peak_rss_bytes": _peak_rss_bytes(),
        "result": str(frontier.result.resolve()),
        "partial_scientific_values_exposed": False,
    })
    return {"schema": FRONTIER_SCHEMA, "status": status, "receipt": str(receipt_path.resolve()), "result": str(frontier.result.resolve()), "partial_scientific_values_exposed": False}


def run_slice(frontier_root: Path, result_root: Path, certificate: Path, slice_wall_seconds: float, rss_limit_bytes: int) -> dict[str, Any]:
    frontier_root = frontier_root.resolve()
    result_root = result_root.resolve()
    result = result_root / DEFAULT_RESULT_NAME
    with _exclusive_frontier(frontier_root):
        frontier = Frontier(frontier_root, result_root, result, certificate.resolve(), slice_wall_seconds, rss_limit_bytes, time.monotonic())
        return _run_slice_locked(frontier)


def default_paths(module_path: Path) -> tuple[Path, Path, Path]:
    parent = module_path.parent
    return parent / DEFAULT_FRONTIER_NAME, parent / DEFAULT_RESULT_ROOT_NAME, parent / "RISP_B3_R03_PREACTIVITY_CERTIFICATE_20260815_03.json"
