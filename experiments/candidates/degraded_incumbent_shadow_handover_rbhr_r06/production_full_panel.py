"""Atomic lease-bound orchestration for the indivisible R06 full panel.

This module contains no authority or identity at import time.  It owns the
complete stage inventory, resource guards, same-identity slice resume and
result firewall.  Scientific tensors and values remain private to the data
plane until the complete result is sealed.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Mapping, Protocol, Sequence

from .production_backend import open_production_batch
from .production_contract import COMPONENT, R06ContractError, complete_inventory
from .production_inference import accept_complete_result, run_production_inference
from .production_lifecycle import open_production_lifecycle, resume_full_panel
from .production_training import PersistentTrainer
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.production_preactivity import (
    process_io_bytes, process_memory_bytes,
)


STAGE_TOTALS = {
    "POPULATION": 11_520,
    "TRAINING": 120 * 1_024,
    "EVALUATION": 115_200,
    "FORK": 6_912,
    "INFERENCE": 1,
}
STAGE_ORDER = tuple(STAGE_TOTALS)
GIB = 1024 ** 3


class FullPanelError(RuntimeError):
    pass


class ProductionDataPlane(Protocol):
    def population_unit(self, index: int) -> bytes: ...
    def training_unit(self, index: int) -> bytes: ...
    def evaluation_unit(self, index: int) -> bytes: ...
    def fork_unit(self, index: int) -> bytes: ...
    def inference_unit(self) -> Mapping[str, object]: ...
    def complete_result(self) -> Mapping[str, object]: ...
    def preferred_batch(self, stage: str, start: int, remaining: int) -> int: ...
    def execute_units(self, stage: str, start: int, count: int) -> Sequence[bytes]: ...


@dataclass(frozen=True)
class ResourceCeilings:
    workers: int = 8
    cpu_cores: int = 8
    gpu: int = 0
    ordinary_cpu_hours: float = 320.0
    ordinary_wall_hours: float = 65.0
    hard_cpu_hours: float = 560.0
    hard_wall_hours: float = 110.0
    rss_gib: float = 40.0
    scratch_gib: float = 120.0
    durable_gib: float = 16.0
    io_gib: float = 400.0


@dataclass
class PanelFrontier:
    identity_sha256: str
    lease_chain_sha256: str
    stage: str = "POPULATION"
    stage_index: int = 0
    completed_units: int = 0
    cpu_seconds: float = 0.0
    wall_seconds: float = 0.0
    io_bytes: int = 0
    slice_generation: int = 0
    component_chain_sha256: str = "0" * 64
    terminal: str | None = None

    def validate(self) -> None:
        if self.stage not in (*STAGE_ORDER, "COMPLETE"):
            raise FullPanelError("frontier stage differs")
        if self.stage != "COMPLETE" and not 0 <= self.stage_index <= STAGE_TOTALS[self.stage]:
            raise FullPanelError("frontier stage index differs")
        if self.completed_units < 0 or self.slice_generation < 0:
            raise FullPanelError("frontier counter differs")


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def _atomic_replace(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    with temporary.open("xb") as stream:
        stream.write(_canonical(value)); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def _directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


class FullPanelExecutor:
    """One identity, one coordinate and one atomic complete-panel frontier."""

    def __init__(self, *, authority: object, data_plane: ProductionDataPlane, run_root: Path) -> None:
        require = getattr(authority, "require_active", None)
        if not callable(require):
            raise FullPanelError("exact Root lease authority is required")
        require()
        if getattr(authority, "component", None) != COMPONENT:
            raise FullPanelError("lease component differs")
        if int(getattr(authority, "workers", 0)) > 8 or int(getattr(authority, "cpu_cores", 0)) > 8 or int(getattr(authority, "gpu", -1)) != 0:
            raise FullPanelError("lease compute shape differs")
        self.authority = authority
        self.data_plane = data_plane
        self.run_root = run_root.resolve()
        self.ceilings = ResourceCeilings()
        self.frontier_path = self.run_root / "sealed_frontier.json"
        self.result_path = self.run_root / "complete_result.json"
        self._io_observed = process_io_bytes(os.getpid())

    def load_or_create_frontier(self) -> PanelFrontier:
        identity = str(getattr(self.authority, "identity_sha256", ""))
        lease_chain = str(getattr(self.authority, "lease_chain_sha256", ""))
        if len(identity) != 64 or len(lease_chain) != 64:
            raise FullPanelError("lease identity binding differs")
        if self.frontier_path.exists():
            value = json.loads(self.frontier_path.read_text(encoding="utf-8"))
            frontier = PanelFrontier(**value)
            if frontier.identity_sha256 != identity:
                raise FullPanelError("replacement identity is forbidden")
            frontier.lease_chain_sha256 = lease_chain
            frontier.slice_generation += 1
            frontier.validate()
            return frontier
        frontier = PanelFrontier(identity_sha256=identity, lease_chain_sha256=lease_chain)
        _atomic_replace(self.frontier_path, asdict(frontier))
        return frontier

    def _guard(self, frontier: PanelFrontier) -> str | None:
        scratch_root = Path(getattr(self.data_plane, "scratch_root", self.run_root))
        durable_root = Path(getattr(self.data_plane, "durable_root", self.run_root))
        scratch = _directory_bytes(scratch_root) / GIB if scratch_root.exists() else 0.0
        durable = _directory_bytes(durable_root) / GIB if durable_root.exists() else 0.0
        rss = float(process_memory_bytes(os.getpid())["current"]) / GIB
        values = {
            "HARD_CPU": frontier.cpu_seconds / 3600.0 > self.ceilings.hard_cpu_hours,
            "HARD_WALL": frontier.wall_seconds / 3600.0 > self.ceilings.hard_wall_hours,
            "HARD_RSS": rss > self.ceilings.rss_gib,
            "HARD_SCRATCH": scratch > self.ceilings.scratch_gib,
            "HARD_DURABLE": durable > self.ceilings.durable_gib,
            "HARD_IO": frontier.io_bytes / GIB > self.ceilings.io_gib,
        }
        return next((name for name, tripped in values.items() if tripped), None)

    @staticmethod
    def _chain(previous: str, payload: bytes) -> str:
        return hashlib.sha256(bytes.fromhex(previous) + payload).hexdigest()

    def _execute_unit(self, frontier: PanelFrontier) -> bytes:
        index = frontier.stage_index
        if frontier.stage == "POPULATION": return bytes(self.data_plane.population_unit(index))
        if frontier.stage == "TRAINING": return bytes(self.data_plane.training_unit(index))
        if frontier.stage == "EVALUATION": return bytes(self.data_plane.evaluation_unit(index))
        if frontier.stage == "FORK": return bytes(self.data_plane.fork_unit(index))
        if frontier.stage == "INFERENCE": return _canonical(self.data_plane.inference_unit())
        raise FullPanelError("complete frontier has no executable unit")

    def _execute_batch(self, frontier: PanelFrontier, count: int) -> tuple[bytes, ...]:
        execute = getattr(self.data_plane, "execute_units", None)
        if callable(execute):
            rows = tuple(bytes(row) for row in execute(frontier.stage, frontier.stage_index, count))
            if len(rows) != count or any(not row for row in rows):
                raise FullPanelError("native batch receipt inventory differs")
            return rows
        if count != 1:
            raise FullPanelError("scalar compatibility data plane cannot execute a batch")
        return (self._execute_unit(frontier),)

    def run_slice(self, *, max_units: int) -> dict[str, object]:
        if bool(getattr(self.data_plane, "supports_parallel_scheduler", False)):
            from .production_scheduler import ParallelPanelScheduler
            scheduler = ParallelPanelScheduler(
                authority=self.authority, data_plane=self.data_plane,
                journal_root=self.run_root / "scheduler_journal",
            )
            return dict(scheduler.run_slice(executor=self, max_units=max_units))
        if max_units <= 0:
            raise FullPanelError("slice unit budget must be positive")
        frontier = self.load_or_create_frontier(); started_wall = time.perf_counter(); started_cpu = time.process_time()
        started_io = process_io_bytes(os.getpid())
        units = 0
        while frontier.stage != "COMPLETE" and units < max_units:
            reason = self._guard(frontier)
            if reason:
                frontier.terminal = reason; break
            remaining_stage = STAGE_TOTALS[frontier.stage] - frontier.stage_index
            remaining_slice = max_units - units
            preferred = getattr(self.data_plane, "preferred_batch", None)
            requested = int(preferred(frontier.stage, frontier.stage_index, min(remaining_stage, remaining_slice))) if callable(preferred) else 1
            count = min(requested, remaining_stage, remaining_slice)
            if count <= 0:
                raise FullPanelError("production batch width differs")
            # A batch is failure-atomic: no frontier byte is replaced until the
            # data plane returns the exact complete receipt inventory.
            payloads = self._execute_batch(frontier, count)
            chain = frontier.component_chain_sha256
            for payload in payloads:
                chain = self._chain(chain, payload)
            frontier.component_chain_sha256 = chain
            frontier.stage_index += count; frontier.completed_units += count; units += count
            if frontier.stage_index == STAGE_TOTALS[frontier.stage]:
                position = STAGE_ORDER.index(frontier.stage) + 1
                frontier.stage = STAGE_ORDER[position] if position < len(STAGE_ORDER) else "COMPLETE"
                frontier.stage_index = 0
            frontier.cpu_seconds += time.process_time() - started_cpu
            frontier.wall_seconds += time.perf_counter() - started_wall
            current_io = process_io_bytes(os.getpid())
            frontier.io_bytes += max(0, int(current_io["read_bytes"] - started_io["read_bytes"]))
            frontier.io_bytes += max(0, int(current_io["write_bytes"] - started_io["write_bytes"]))
            _atomic_replace(self.frontier_path, asdict(frontier))
            started_cpu = time.process_time(); started_wall = time.perf_counter(); started_io = current_io
        return self.finish_slice(frontier)

    def commit_parallel_stage(
        self, frontier: PanelFrontier, *, digests: Sequence[str],
        cpu_seconds: float, wall_seconds: float,
    ) -> None:
        """Atomically advance one complete parallel stage in ordered task order."""

        if frontier.stage == "COMPLETE" or frontier.stage_index != 0 or not digests:
            raise FullPanelError("parallel stage commit frontier differs")
        stage = frontier.stage; chain = frontier.component_chain_sha256
        for digest in digests:
            if len(digest) != 64:
                raise FullPanelError("parallel task digest differs")
            chain = self._chain(chain, bytes.fromhex(digest))
        current_io = process_io_bytes(os.getpid())
        frontier.io_bytes += max(0, int(current_io["read_bytes"] - self._io_observed["read_bytes"]))
        frontier.io_bytes += max(0, int(current_io["write_bytes"] - self._io_observed["write_bytes"]))
        self._io_observed = current_io
        frontier.component_chain_sha256 = chain
        frontier.completed_units += STAGE_TOTALS[stage]
        frontier.cpu_seconds += float(cpu_seconds); frontier.wall_seconds += float(wall_seconds)
        position = STAGE_ORDER.index(stage) + 1
        frontier.stage = STAGE_ORDER[position] if position < len(STAGE_ORDER) else "COMPLETE"
        frontier.stage_index = 0
        _atomic_replace(self.frontier_path, asdict(frontier))

    def finish_slice(self, frontier: PanelFrontier) -> dict[str, object]:
        if frontier.stage == "COMPLETE" and frontier.terminal is None:
            payload = dict(self.data_plane.complete_result())
            payload.update({
                "schema": "DISH_RBHR_R06_COMPLETE_RESULT_V1", "complete": True,
                "identity_sha256": frontier.identity_sha256, "population_count": 11_520,
                "training_jobs": 120, "evaluation_episodes": 115_200,
                "estimands": 6_990, "resamples": 99_999,
            })
            result = accept_complete_result(self.result_path, payload)
            return {"status": "COMPLETE", "result": result, "frontier": asdict(frontier)}
        return {"status": "HARD_GUARD" if frontier.terminal else "SLICE_COMPLETE", "frontier": asdict(frontier), "partial_values_exposed": False}


def production_surface_manifest() -> dict[str, object]:
    inventory = complete_inventory()
    return {
        "schema": "DISH_RBHR_R06_PRODUCTION_SURFACE_MANIFEST_V1",
        "stages": dict(STAGE_TOTALS), "total_units": sum(STAGE_TOTALS.values()),
        "inventory": inventory, "workers_max": 8, "gpu": 0,
        "same_identity_successor_slice": True, "complete_result_firewall": True,
        "partial_values_exposed": False,
    }


__all__ = [
    "FullPanelError", "FullPanelExecutor", "PanelFrontier", "ProductionDataPlane",
    "ResourceCeilings", "STAGE_TOTALS", "production_surface_manifest",
]
