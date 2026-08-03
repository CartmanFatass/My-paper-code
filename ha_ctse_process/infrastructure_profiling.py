"""Optional non-scientific infrastructure timing for standalone runners."""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Callable


PROFILE_CATEGORIES = (
    "inference",
    "collector_env",
    "transition_ledger_pack",
    "update",
    "metrics",
    "checkpoint_eval",
)


class InfrastructureProfiler:
    """Accumulate one update's wall-clock phases and optionally append JSONL."""

    def __init__(
        self,
        log_dir: str | Path,
        interval: int,
        *,
        clock: Callable[[], float] = time.monotonic,
        cuda_synchronize: Callable[[], None] | None = None,
    ) -> None:
        if interval <= 0:
            raise ValueError("infrastructure profile interval must be positive")
        self._interval = int(interval)
        self._path = Path(log_dir) / "diagnostics" / "infrastructure_profile.jsonl"
        self._clock = clock
        self._cuda_synchronize = cuda_synchronize
        self._durations = {category: 0.0 for category in PROFILE_CATEGORIES}
        self._active_category: str | None = None
        self._started_at: float | None = None

    def start(self, category: str, *, torch_phase: bool = False) -> None:
        if category not in self._durations:
            raise ValueError(f"unknown infrastructure profile category: {category}")
        if self._active_category is not None:
            raise RuntimeError("infrastructure profile phases must not overlap")
        if torch_phase and self._cuda_synchronize is not None:
            self._cuda_synchronize()
        self._active_category = category
        self._started_at = self._clock()

    def stop(self, *, torch_phase: bool = False) -> None:
        if self._active_category is None or self._started_at is None:
            raise RuntimeError("infrastructure profile phase was not started")
        if torch_phase and self._cuda_synchronize is not None:
            self._cuda_synchronize()
        duration = self._clock() - self._started_at
        self._durations[self._active_category] += duration
        self._active_category = None
        self._started_at = None

    def finish_update(self, *, update: int, total_steps: int) -> None:
        if self._active_category is not None:
            raise RuntimeError("cannot emit an active infrastructure profile phase")
        if int(update) % self._interval == 0:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            row = {
                "schema_version": 1,
                "update": int(update),
                "total_steps": int(total_steps),
                "durations_seconds": dict(self._durations),
            }
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
        self._durations = {category: 0.0 for category in PROFILE_CATEGORIES}
