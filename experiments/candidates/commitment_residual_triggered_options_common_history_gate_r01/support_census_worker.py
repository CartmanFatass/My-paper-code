"""Isolated launcher-side worker for the frozen support-only K8 census."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
from typing import Mapping, Sequence

from .config import (
    CPU_WORKERS,
    PEAK_RSS_BYTES,
    SUPPORT_CENSUS_CLAIM_CEILING,
    SUPPORT_CENSUS_COMMIT_CPU_HEADROOM_SECONDS,
    SUPPORT_CENSUS_COMMIT_IO_READ_HEADROOM_BYTES,
    SUPPORT_CENSUS_COMMIT_IO_WRITE_HEADROOM_BYTES,
    SUPPORT_CENSUS_COMMIT_RSS_HEADROOM_BYTES,
    SUPPORT_CENSUS_COMMIT_WALL_HEADROOM_SECONDS,
    SUPPORT_CENSUS_EPISODES_PER_SLOT,
    SUPPORT_CENSUS_FIRST_EPISODE,
    SUPPORT_CENSUS_LAUNCH_RUN_ID,
    SUPPORT_CENSUS_MAX_PRIMITIVE_TEAM_STEPS,
    SUPPORT_CENSUS_OBJECT_ID,
    SUPPORT_CENSUS_PERFORMANCE_DISPOSITION,
    SUPPORT_CENSUS_RNG_NAMESPACE,
    SUPPORT_CENSUS_SLOTS,
    WALL_SECONDS,
)
from .ledger import ResourceLimitExceeded, _peak_rss_bytes
from .preflight import create_shared_resource_receipt, create_shared_run_assessment
from .support_census import (
    COMMIT_HEADROOM,
    RUNTIME_MEASUREMENT_CUTOFF,
    commit_prepared_support_publication,
    discard_prepared_support_publication,
    materialize_support_observation,
    prepare_support_census_publication,
    registered_support_tapes,
    summarize_support_census,
    validate_support_full_replay,
)


WORKER_ENV = "HMASD_CRTO_SUPPORT_CENSUS_WORKER"
BASE_EPISODE_COUNT = len(SUPPORT_CENSUS_SLOTS) * SUPPORT_CENSUS_EPISODES_PER_SLOT
BASE_PRIMITIVE_TEAM_STEPS = BASE_EPISODE_COUNT * 256


def _validate_registration() -> None:
    if (
        SUPPORT_CENSUS_OBJECT_ID
        != "CRTO-K8-FIRST-BOUNDARY-SUPPORT-CENSUS-20260831-01"
        or SUPPORT_CENSUS_RNG_NAMESPACE != 2_026_083_192
        or SUPPORT_CENSUS_SLOTS != tuple(range(8))
        or SUPPORT_CENSUS_FIRST_EPISODE != 832
        or SUPPORT_CENSUS_EPISODES_PER_SLOT != 64
        or SUPPORT_CENSUS_CLAIM_CEILING
        != "FIXED_EIGHT_SLOT_K8_FIRST_BOUNDARY_SUPPORT_ONLY"
        or SUPPORT_CENSUS_PERFORMANCE_DISPOSITION != "PILOT_ONLY"
        or SUPPORT_CENSUS_MAX_PRIMITIVE_TEAM_STEPS != 393_216
        or CPU_WORKERS != 1
    ):
        raise PermissionError("support census registration or execution envelope drifted")


def _configure_import_safe_worker() -> None:
    if os.environ.get(WORKER_ENV) != SUPPORT_CENSUS_OBJECT_ID:
        raise PermissionError("support census requires its isolated fixed worker")
    for name in (
        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
    ):
        if os.environ.get(name) != "1":
            raise ResourceLimitExceeded("support census worker thread limits were not fixed at birth")
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise ResourceLimitExceeded("support census worker must make GPUs unavailable")


def _process_io_bytes() -> tuple[int, int]:
    """Return process read/write byte counters without an optional dependency."""

    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class IoCounters(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_ulonglong),
                ("WriteOperationCount", ctypes.c_ulonglong),
                ("OtherOperationCount", ctypes.c_ulonglong),
                ("ReadTransferCount", ctypes.c_ulonglong),
                ("WriteTransferCount", ctypes.c_ulonglong),
                ("OtherTransferCount", ctypes.c_ulonglong),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.GetProcessIoCounters.argtypes = (wintypes.HANDLE, ctypes.POINTER(IoCounters))
        kernel32.GetProcessIoCounters.restype = wintypes.BOOL
        counters = IoCounters()
        if not kernel32.GetProcessIoCounters(
            kernel32.GetCurrentProcess(), ctypes.byref(counters),
        ):
            raise OSError(ctypes.get_last_error(), "Windows process I/O query failed")
        return int(counters.ReadTransferCount), int(counters.WriteTransferCount)
    import resource

    usage = resource.getrusage(resource.RUSAGE_SELF)
    # POSIX exposes block counts rather than bytes.  Record a conservative 512-byte conversion.
    return int(usage.ru_inblock) * 512, int(usage.ru_oublock) * 512


class SupportCensusWorkLedger:
    """Prospective full-population charge plus measured bounded runtime facts."""

    def __init__(self) -> None:
        if 2 * BASE_PRIMITIVE_TEAM_STEPS > SUPPORT_CENSUS_MAX_PRIMITIVE_TEAM_STEPS:
            raise ResourceLimitExceeded("support census base population exceeds its work ceiling")
        self._started = time.monotonic()
        self._cpu_started = time.process_time()
        self._io_started = _process_io_bytes()
        self._peak = _peak_rss_bytes()
        self._materialization_base_episodes = 0
        self._materialization_transitions = 0
        self._materialization_branches = 0
        self._validation_base_episodes = 0
        self._validation_transitions = 0
        self._validation_branches = 0
        self._phase = "MATERIALIZATION"
        self.check_limits()

    @property
    def branches(self) -> int:
        return self._materialization_branches + self._validation_branches

    def check_limits(self) -> None:
        self._peak = max(self._peak, _peak_rss_bytes())
        if self._peak > PEAK_RSS_BYTES:
            raise ResourceLimitExceeded("support census exceeded the 2-GiB peak RSS ceiling")
        if time.monotonic() - self._started > WALL_SECONDS:
            raise ResourceLimitExceeded("support census exceeded the 7,200-second wall ceiling")

    def require_common_future_headroom(self, branch_count: int) -> None:
        if type(branch_count) is not int or not 1 <= branch_count <= 8:
            raise ValueError("support row requires one to eight printed common-future branches")
        proposed = (
            2 * BASE_PRIMITIVE_TEAM_STEPS + 16 * (self.branches + branch_count)
        )
        if proposed > SUPPORT_CENSUS_MAX_PRIMITIVE_TEAM_STEPS:
            raise ResourceLimitExceeded("support census common-future work would exceed its ceiling")
        self.check_limits()

    def record_common_future_branch(self, executed_steps: int) -> None:
        if executed_steps != 16:
            raise ValueError("support common-future branch must execute exactly 16 steps")
        if 2 * BASE_PRIMITIVE_TEAM_STEPS + 16 * (self.branches + 1) > (
            SUPPORT_CENSUS_MAX_PRIMITIVE_TEAM_STEPS
        ):
            raise ResourceLimitExceeded("support census common-future work exceeded its ceiling")
        if self._phase == "MATERIALIZATION":
            self._materialization_branches += 1
        elif self._phase == "VALIDATION":
            self._validation_branches += 1
        else:
            raise RuntimeError("support census ledger phase is closed")
        self.check_limits()

    def record_base_episode(self, scripted_history_transitions: int) -> None:
        if type(scripted_history_transitions) is not int or not 0 <= scripted_history_transitions <= 256:
            raise ValueError("support base traversal count is invalid")
        if self._phase != "MATERIALIZATION":
            raise RuntimeError("materialization base work was recorded in the wrong phase")
        if self._materialization_base_episodes >= BASE_EPISODE_COUNT:
            raise ResourceLimitExceeded("support census observed more than 512 assigned episodes")
        self._materialization_base_episodes += 1
        self._materialization_transitions += scripted_history_transitions
        self.check_limits()

    def begin_validation_replay(self) -> None:
        if self._phase != "MATERIALIZATION" or self._materialization_base_episodes != (
            BASE_EPISODE_COUNT
        ):
            raise ResourceLimitExceeded("validation replay began before complete materialization")
        self._phase = "VALIDATION"
        self.check_limits()

    def record_validation_base_episode(self, scripted_history_transitions: int) -> None:
        if self._phase != "VALIDATION":
            raise RuntimeError("validation base work was recorded outside replay")
        if type(scripted_history_transitions) is not int or not 0 <= scripted_history_transitions <= 256:
            raise ValueError("validation base traversal count is invalid")
        if self._validation_base_episodes >= BASE_EPISODE_COUNT:
            raise ResourceLimitExceeded("validation replay exceeded 512 assigned episodes")
        self._validation_base_episodes += 1
        self._validation_transitions += scripted_history_transitions
        self.check_limits()

    def finish_validation_replay(self) -> None:
        if (
            self._phase != "VALIDATION"
            or self._validation_base_episodes != BASE_EPISODE_COUNT
            or self._validation_branches != self._materialization_branches
        ):
            raise ResourceLimitExceeded("independent full validation replay is incomplete")
        self._phase = "CLOSED"
        self.check_limits()

    def runtime_record(
        self, *, scratch_high_water_bytes: int, durable_high_water_bytes: int,
    ) -> dict[str, object]:
        if (
            self._phase != "CLOSED"
            or self._materialization_base_episodes != BASE_EPISODE_COUNT
            or self._validation_base_episodes != BASE_EPISODE_COUNT
        ):
            raise ResourceLimitExceeded("support census materialization/replay is incomplete")
        self.check_limits()
        wall = time.monotonic() - self._started
        cpu = time.process_time() - self._cpu_started
        io_now = _process_io_bytes()
        materialization_common_steps = 16 * self._materialization_branches
        validation_common_steps = 16 * self._validation_branches
        return {
            "workers": 1,
            "threads_per_worker": 1,
            "base_episode_count": 2 * BASE_EPISODE_COUNT,
            "charged_base_primitive_team_steps": 2 * BASE_PRIMITIVE_TEAM_STEPS,
            "scripted_history_transitions": (
                self._materialization_transitions + self._validation_transitions
            ),
            "actual_common_future_branch_count": self.branches,
            "actual_common_future_steps": (
                materialization_common_steps + validation_common_steps
            ),
            "materialization_base_episode_count": BASE_EPISODE_COUNT,
            "materialization_charged_base_primitive_team_steps": BASE_PRIMITIVE_TEAM_STEPS,
            "materialization_scripted_history_transitions": self._materialization_transitions,
            "materialization_common_future_branch_count": self._materialization_branches,
            "materialization_common_future_steps": materialization_common_steps,
            "validation_base_episode_count": BASE_EPISODE_COUNT,
            "validation_charged_base_primitive_team_steps": BASE_PRIMITIVE_TEAM_STEPS,
            "validation_scripted_history_transitions": self._validation_transitions,
            "validation_common_future_branch_count": self._validation_branches,
            "validation_common_future_steps": validation_common_steps,
            "actual_total_charged_primitive_team_steps": (
                2 * BASE_PRIMITIVE_TEAM_STEPS
                + materialization_common_steps
                + validation_common_steps
            ),
            "primitive_team_step_ceiling": SUPPORT_CENSUS_MAX_PRIMITIVE_TEAM_STEPS,
            "wall_seconds": wall,
            "wall_ceiling_seconds": WALL_SECONDS,
            "peak_rss_bytes": self._peak,
            "peak_rss_ceiling_bytes": PEAK_RSS_BYTES,
            "cpu_seconds": cpu,
            "cpu_occupancy_fraction": cpu / max(wall, 1e-12),
            "scratch_high_water_bytes": int(scratch_high_water_bytes),
            "durable_high_water_bytes": int(durable_high_water_bytes),
            "io_read_bytes": max(0, io_now[0] - self._io_started[0]),
            "io_write_bytes": max(0, io_now[1] - self._io_started[1]),
            "measurement_cutoff": RUNTIME_MEASUREMENT_CUTOFF,
            "commit_tail_excluded": True,
            "commit_headroom": dict(COMMIT_HEADROOM),
            "final_candidate_staging_rehearsal_observed": {
                "wall_seconds": wall,
                "cpu_seconds": cpu,
                "peak_rss_bytes": self._peak,
                "io_read_bytes": max(0, io_now[0] - self._io_started[0]),
                "io_write_bytes": max(0, io_now[1] - self._io_started[1]),
            },
        }


def _validate_fresh_targets(*paths: Path) -> tuple[Path, ...]:
    resolved = tuple(Path(path).resolve() for path in paths)
    if len(set(resolved)) != len(resolved):
        raise ValueError("support census output, result, and resource paths must be distinct")
    output = resolved[0]
    if any(path.exists() for path in resolved):
        raise FileExistsError("support census requires fresh create-only paths")
    if any(output == path or output in path.parents for path in resolved[1:]):
        raise ValueError("support census public result and receipts must be outside output root")
    return resolved


def _encoded_size(payload: Mapping[str, object]) -> int:
    return len((json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8"))


def _precommit_runtime_bound(
    observed: Mapping[str, object], *, encoded_size: int, receipt_bytes: int,
) -> dict[str, object]:
    """Turn a complete staging rehearsal observation into a conservative final bound."""

    publication_bytes = 4 * encoded_size + 8 * 1024**2
    runtime = dict(observed)
    rehearsal = {
        field: observed[field]
        for field in (
            "wall_seconds", "cpu_seconds", "peak_rss_bytes",
            "io_read_bytes", "io_write_bytes",
        )
    }
    runtime.update({
        "wall_seconds": float(observed["wall_seconds"]) + 30.0,
        "cpu_seconds": float(observed["cpu_seconds"]) + 10.0,
        "peak_rss_bytes": int(observed["peak_rss_bytes"]),
        "io_read_bytes": int(observed["io_read_bytes"]) + publication_bytes,
        "io_write_bytes": int(observed["io_write_bytes"]) + publication_bytes,
        "scratch_high_water_bytes": publication_bytes,
        "durable_high_water_bytes": receipt_bytes + publication_bytes,
        "measurement_cutoff": RUNTIME_MEASUREMENT_CUTOFF,
        "commit_tail_excluded": True,
        "commit_headroom": dict(COMMIT_HEADROOM),
        "final_candidate_staging_rehearsal_observed": rehearsal,
    })
    runtime["cpu_occupancy_fraction"] = (
        float(runtime["cpu_seconds"]) / max(float(runtime["wall_seconds"]), 1e-12)
    )
    if (
        float(runtime["wall_seconds"])
        > WALL_SECONDS - SUPPORT_CENSUS_COMMIT_WALL_HEADROOM_SECONDS
        or float(runtime["cpu_seconds"])
        > WALL_SECONDS - SUPPORT_CENSUS_COMMIT_CPU_HEADROOM_SECONDS
        or int(runtime["peak_rss_bytes"])
        > PEAK_RSS_BYTES - SUPPORT_CENSUS_COMMIT_RSS_HEADROOM_BYTES
    ):
        raise ResourceLimitExceeded(
            "support census cannot reserve final staging and rename-only commit headroom"
        )
    return runtime


def _run_registered_support_census(
    *,
    output_root: Path,
    result_path: Path,
    resource_receipt_path: Path,
    run_resource_receipt_path: Path,
) -> Mapping[str, object]:
    _validate_registration()
    _configure_import_safe_worker()
    output, result, memory_path, assessment_path = _validate_fresh_targets(
        output_root, result_path, resource_receipt_path, run_resource_receipt_path,
    )

    # This fresh pair precedes the first support namespace address or tape.
    memory_receipt = create_shared_resource_receipt(memory_path)
    run_receipt = create_shared_run_assessment(
        assessment_path, run_id=SUPPORT_CENSUS_LAUNCH_RUN_ID,
    )
    ledger = SupportCensusWorkLedger()
    observations: list[dict[str, object]] = []
    for slot in SUPPORT_CENSUS_SLOTS:
        for tape in registered_support_tapes(slot):
            observation = materialize_support_observation(tape, slot=slot, ledger=ledger)
            ledger.record_base_episode(
                int(observation["boundary"]["scripted_history_transitions"])
            )
            observations.append(observation)
    independent_replay = validate_support_full_replay(observations, ledger=ledger)
    receipt_bytes = memory_path.stat().st_size + assessment_path.stat().st_size
    runtime = ledger.runtime_record(
        scratch_high_water_bytes=1_048_576,
        durable_high_water_bytes=receipt_bytes + 1_048_576,
    )
    payload = summarize_support_census(
        observations,
        independent_replay=independent_replay,
        resource_receipt=memory_receipt,
        run_resource_receipt=run_receipt,
        runtime=runtime,
    )
    observed = runtime
    for _ in range(8):
        rehearsal_runtime = _precommit_runtime_bound(
            observed,
            encoded_size=_encoded_size(payload),
            receipt_bytes=receipt_bytes,
        )
        rehearsal_candidate = summarize_support_census(
            observations,
            independent_replay=independent_replay,
            resource_receipt=memory_receipt,
            run_resource_receipt=run_receipt,
            runtime=rehearsal_runtime,
        )
        # This is a complete, non-visible rehearsal of the same final candidate
        # schema and dual-staging/fsync path.  Its exact cumulative terminal
        # wall/CPU/RSS/I/O observation is embedded in the next candidate.
        rehearsal = prepare_support_census_publication(
            output, result, rehearsal_candidate,
        )
        try:
            rehearsal_bytes = int(rehearsal["staged_bytes"])
            observed = ledger.runtime_record(
                scratch_high_water_bytes=max(
                    int(rehearsal_runtime["scratch_high_water_bytes"]),
                    rehearsal_bytes,
                ),
                durable_high_water_bytes=max(
                    int(rehearsal_runtime["durable_high_water_bytes"]),
                    receipt_bytes + rehearsal_bytes,
                ),
            )
        finally:
            discard_prepared_support_publication(rehearsal)

        bounded_runtime = _precommit_runtime_bound(
            observed,
            encoded_size=_encoded_size(rehearsal_candidate),
            receipt_bytes=receipt_bytes,
        )
        candidate = summarize_support_census(
            observations,
            independent_replay=independent_replay,
            resource_receipt=memory_receipt,
            run_resource_receipt=run_receipt,
            runtime=bounded_runtime,
        )
        prepared = prepare_support_census_publication(output, result, candidate)
        try:
            staged_bytes = int(prepared["staged_bytes"])
            terminal = ledger.runtime_record(
                scratch_high_water_bytes=max(
                    int(bounded_runtime["scratch_high_water_bytes"]), staged_bytes,
                ),
                durable_high_water_bytes=max(
                    int(bounded_runtime["durable_high_water_bytes"]),
                    receipt_bytes + staged_bytes,
                ),
            )
            covered_fields = (
                "wall_seconds", "cpu_seconds", "peak_rss_bytes",
                "io_read_bytes", "io_write_bytes",
            )
            covered = all(
                terminal[field] <= bounded_runtime[field] for field in covered_fields
            )
            io_headroom = (
                int(bounded_runtime["io_read_bytes"]) - int(terminal["io_read_bytes"])
                >= SUPPORT_CENSUS_COMMIT_IO_READ_HEADROOM_BYTES
                and int(bounded_runtime["io_write_bytes"])
                - int(terminal["io_write_bytes"])
                >= SUPPORT_CENSUS_COMMIT_IO_WRITE_HEADROOM_BYTES
            )
            if not covered or not io_headroom:
                observed = terminal
                payload = candidate
                discard_prepared_support_publication(prepared)
                continue
            if (
                float(terminal["wall_seconds"])
                > WALL_SECONDS - SUPPORT_CENSUS_COMMIT_WALL_HEADROOM_SECONDS
                or float(terminal["cpu_seconds"])
                > WALL_SECONDS - SUPPORT_CENSUS_COMMIT_CPU_HEADROOM_SECONDS
                or int(terminal["peak_rss_bytes"])
                > PEAK_RSS_BYTES - SUPPORT_CENSUS_COMMIT_RSS_HEADROOM_BYTES
            ):
                raise ResourceLimitExceeded(
                    "support census lacks its frozen rename-only commit headroom"
                )
        except BaseException:
            discard_prepared_support_publication(prepared)
            raise
        return commit_prepared_support_publication(prepared)
    raise RuntimeError("support census precommit resource accounting did not converge")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=SUPPORT_CENSUS_OBJECT_ID)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--resource-receipt", type=Path, required=True)
    parser.add_argument("--run-resource-receipt", type=Path, required=True)
    arguments = parser.parse_args(argv)
    _run_registered_support_census(
        output_root=arguments.output_root,
        result_path=arguments.result,
        resource_receipt_path=arguments.resource_receipt,
        run_resource_receipt_path=arguments.run_resource_receipt,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


__all__ = ["SupportCensusWorkLedger", "_run_registered_support_census", "main"]
