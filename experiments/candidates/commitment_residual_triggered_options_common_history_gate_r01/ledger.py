"""Exact primitive-team-step accounting for the prospective CRTO object."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import os
import platform
import time
from typing import Final, Mapping

from .config import MAX_PRIMITIVE_TEAM_STEPS, PEAK_RSS_BYTES, WALL_SECONDS


EPISODE_STEPS: Final = 256
REPLICATE_COUNT: Final = 8
EPISODES_PER_REPLICATE: Final = 1_088
BASE_PRIMITIVE_TEAM_STEPS: Final = (
    REPLICATE_COUNT * EPISODES_PER_REPLICATE * EPISODE_STEPS
)
COMMON_FUTURE_STEPS_PER_BRANCH: Final = 16
COMMON_FUTURE_STEP_HEADROOM: Final = MAX_PRIMITIVE_TEAM_STEPS - BASE_PRIMITIVE_TEAM_STEPS
MAX_COMMON_FUTURE_BRANCHES: Final = (
    COMMON_FUTURE_STEP_HEADROOM // COMMON_FUTURE_STEPS_PER_BRANCH
)

BASE_POPULATION_EPISODES: Final[Mapping[str, int]] = {
    "PREDICTOR_FIT": 256,
    "CALIBRATION": 64,
    "TRAIN": 512,
    "EVALUATION": 256,
}


class ResourceLimitExceeded(RuntimeError):
    """The frozen wall, RSS, thread, or primitive-step ceiling was crossed."""


def _peak_rss_bytes() -> int:
    if os.name == "nt":
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
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = (
            wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD,
        )
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        process = kernel32.GetCurrentProcess()
        if not psapi.GetProcessMemoryInfo(
            process, ctypes.byref(counters), counters.cb
        ):
            raise OSError(ctypes.get_last_error(), "Windows process RSS query failed")
        return int(counters.PeakWorkingSetSize)
    import resource

    observed = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return observed if platform.system() == "Darwin" else observed * 1024


def prospective_ledger_report(
    actual_common_future_branch_count: int | None = None,
) -> dict[str, object]:
    """Assess the exact ledger from a result-blind structural boundary scan."""

    if actual_common_future_branch_count is not None and (
        isinstance(actual_common_future_branch_count, bool)
        or not isinstance(actual_common_future_branch_count, int)
        or actual_common_future_branch_count < 0
    ):
        raise ValueError("actual common-future branch count must be a nonnegative integer")
    common_steps = (
        None
        if actual_common_future_branch_count is None
        else actual_common_future_branch_count * COMMON_FUTURE_STEPS_PER_BRANCH
    )
    total = None if common_steps is None else BASE_PRIMITIVE_TEAM_STEPS + common_steps
    exact = actual_common_future_branch_count is not None
    within_ceiling = exact and total is not None and total <= MAX_PRIMITIVE_TEAM_STEPS
    return {
        "formula": "8*1088*256 + 16*actual_common_future_branch_count",
        "charged_full_tape_episode_count": REPLICATE_COUNT * EPISODES_PER_REPLICATE,
        "charged_full_tape_primitive_team_steps": BASE_PRIMITIVE_TEAM_STEPS,
        "ceiling_accounting_law": (
            "charge every assigned base episode at the full 256-step horizon, then add every "
            "actually executed 16-step common-future branch"
        ),
        "common_future_steps_per_actual_branch": COMMON_FUTURE_STEPS_PER_BRANCH,
        "actual_common_future_branch_count": actual_common_future_branch_count,
        "actual_common_future_steps": common_steps,
        "actual_total_steps": total,
        "common_future_step_headroom": COMMON_FUTURE_STEP_HEADROOM,
        "maximum_common_future_branches_within_ceiling": MAX_COMMON_FUTURE_BRANCHES,
        "ceiling": MAX_PRIMITIVE_TEAM_STEPS,
        "pre_result_exact": exact,
        "within_ceiling": within_ceiling,
        "blocker": (
            "PRE_RESULT_EXACT_LEDGER_EXCEEDS_CEILING: the result-blind structural scan "
            f"requires {total} primitive team steps, above {MAX_PRIMITIVE_TEAM_STEPS}; "
            "do not launch and do not raise the ceiling"
        ) if exact and not within_ceiling else None if exact else (
            "PRE_RESULT_STRUCTURAL_SCAN_REQUIRED: run the result-blind scripted-history scan "
            "over the exact final manifests before creating a model, optimizer, or result root"
        ),
    }


@dataclass(frozen=True)
class LedgerSnapshot:
    charged_base_steps_by_population: Mapping[str, int]
    physically_executed_base_steps_by_population: Mapping[str, int]
    common_future_branches: int
    common_future_steps: int
    actual_total_steps: int
    ceiling: int
    wall_seconds: float
    peak_rss_bytes: int
    workers: int
    threads_per_worker: int


class PrimitiveTeamStepLedger:
    """Fail-before-work accounting for base episodes and each actual G16 branch."""

    def __init__(
        self, *, expected_common_future_branches: int,
        workers: int = 1, threads_per_worker: int = 1,
    ) -> None:
        if workers != 1 or threads_per_worker != 1:
            raise ResourceLimitExceeded("CRTO requires one worker and one thread")
        self._workers = workers
        self._threads = threads_per_worker
        if (
            isinstance(expected_common_future_branches, bool)
            or not isinstance(expected_common_future_branches, int)
            or expected_common_future_branches < 0
        ):
            raise ValueError("prospective expected branch count must be a nonnegative integer")
        expected_report = prospective_ledger_report(expected_common_future_branches)
        if expected_report["within_ceiling"] is not True:
            raise ResourceLimitExceeded(str(expected_report["blocker"]))
        self._expected_branches = expected_common_future_branches
        self._started = time.monotonic()
        self._peak = _peak_rss_bytes()
        self._base: dict[str, int] = defaultdict(int)
        self._physical_base: dict[str, int] = defaultdict(int)
        self._branches = 0
        self._check_limits()

    @property
    def actual_total_steps(self) -> int:
        return sum(self._base.values()) + self._branches * COMMON_FUTURE_STEPS_PER_BRANCH

    def _check_limits(self, *, proposed_additional_steps: int = 0) -> None:
        if self.actual_total_steps + proposed_additional_steps > MAX_PRIMITIVE_TEAM_STEPS:
            raise ResourceLimitExceeded("CRTO primitive-team-step ceiling would be exceeded")
        self._peak = max(self._peak, _peak_rss_bytes())
        if self._peak > PEAK_RSS_BYTES:
            raise ResourceLimitExceeded("CRTO 2-GiB peak RSS ceiling was exceeded")
        if time.monotonic() - self._started > WALL_SECONDS:
            raise ResourceLimitExceeded("CRTO 7,200-second wall ceiling was exceeded")

    def check_limits(self) -> None:
        """Public injected monitor callback for long optimizer loops."""

        self._check_limits()

    def charge_base_population(self, name: str, episode_count: int) -> None:
        """Charge one global eight-slot population once at its full 256-step horizon."""

        if name not in BASE_POPULATION_EPISODES:
            raise ValueError(f"unknown base population: {name}")
        if episode_count != BASE_POPULATION_EPISODES[name]:
            raise ValueError(f"{name} episode count drifted from the frozen population")
        if self._base[name]:
            raise ValueError(f"{name} base population was already recorded")
        steps = REPLICATE_COUNT * episode_count * EPISODE_STEPS
        self._check_limits(proposed_additional_steps=steps)
        self._base[name] = steps
        self._check_limits()

    def record_physically_executed_base_steps(self, name: str, executed_steps: int) -> None:
        if name not in BASE_POPULATION_EPISODES or not self._base[name]:
            raise ValueError("base population must be charged before physical execution is recorded")
        if isinstance(executed_steps, bool) or not isinstance(executed_steps, int) or executed_steps < 0:
            raise ValueError("physically executed base steps must be a nonnegative integer")
        proposed = self._physical_base[name] + executed_steps
        if proposed > self._base[name]:
            raise ResourceLimitExceeded("physical base execution exceeds the charged population")
        self._physical_base[name] = proposed
        self._check_limits()

    def require_common_future_headroom(self, branch_count: int) -> None:
        if isinstance(branch_count, bool) or not isinstance(branch_count, int) or branch_count <= 0:
            raise ValueError("common-future branch count must be a positive integer")
        self._check_limits(
            proposed_additional_steps=branch_count * COMMON_FUTURE_STEPS_PER_BRANCH
        )

    def record_common_future_branch(self, executed_steps: int) -> None:
        if executed_steps != COMMON_FUTURE_STEPS_PER_BRANCH:
            raise ValueError("every common-future branch must execute exactly 16 steps")
        self._check_limits(proposed_additional_steps=executed_steps)
        self._branches += 1
        self._check_limits()

    def snapshot(self) -> LedgerSnapshot:
        self._check_limits()
        return LedgerSnapshot(
            charged_base_steps_by_population=dict(self._base),
            physically_executed_base_steps_by_population=dict(self._physical_base),
            common_future_branches=self._branches,
            common_future_steps=self._branches * COMMON_FUTURE_STEPS_PER_BRANCH,
            actual_total_steps=self.actual_total_steps,
            ceiling=MAX_PRIMITIVE_TEAM_STEPS,
            wall_seconds=time.monotonic() - self._started,
            peak_rss_bytes=self._peak,
            workers=self._workers,
            threads_per_worker=self._threads,
        )

    def assert_complete(self) -> None:
        expected = {
            name: REPLICATE_COUNT * episodes * EPISODE_STEPS
            for name, episodes in BASE_POPULATION_EPISODES.items()
        }
        if dict(self._base) != expected:
            raise ResourceLimitExceeded("base primitive-team-step ledger is incomplete")
        if dict(self._physical_base) != expected:
            raise ResourceLimitExceeded(
                "physical base traversal is incomplete or was not recorded separately from charge"
            )
        if self._branches != self._expected_branches:
            raise ResourceLimitExceeded(
                "actual common-future branch count does not equal the prospective dry scan: "
                f"{self._branches}!={self._expected_branches}"
            )
        self._check_limits()


__all__ = [
    "BASE_PRIMITIVE_TEAM_STEPS",
    "COMMON_FUTURE_STEPS_PER_BRANCH",
    "PrimitiveTeamStepLedger",
    "ResourceLimitExceeded",
    "MAX_COMMON_FUTURE_BRANCHES",
    "prospective_ledger_report",
]
