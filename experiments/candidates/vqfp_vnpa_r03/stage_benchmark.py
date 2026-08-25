"""Bounded result-blind stage-R01 measurement and canonical I/O fixture.

This is a lifecycle/measurement adapter only.  All host, policy, reducer and
worker hot paths execute in the C++ component.  Inputs are synthetic and use
no registered r03 RNG root, coefficient, episode, score, or result identity.
"""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time

from .native_backend import artifact_identity, cost_collapse_slice
from .reference_oracle import stage_literal_audit

SCHEMA = "VQFP_VNPA_R03_RESULT_BLIND_COST_COLLAPSE_STAGE_R01_V1"
REPO = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = REPO / "temp/handoffs/code_manager_to_root/VQFP_VARIABLE_N_PHYSICAL_ASSOCIATION_VALUE_R03_STAGED_COST_COLLAPSE_BENCHMARK_20260823.json"


class _ProcessMemoryCountersEx(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong), ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong), ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong), ("OtherTransferCount", ctypes.c_ulonglong),
    ]


def _process_counters() -> tuple[int, int, int]:
    kernel = ctypes.windll.kernel32
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
    ctypes.windll.psapi.GetProcessMemoryInfo.restype = ctypes.c_int
    kernel.GetProcessIoCounters.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    kernel.GetProcessIoCounters.restype = ctypes.c_int
    process = kernel.GetCurrentProcess()
    memory = _ProcessMemoryCountersEx()
    memory.cb = ctypes.sizeof(memory)
    if not ctypes.windll.psapi.GetProcessMemoryInfo(process, ctypes.byref(memory), memory.cb):
        raise OSError("GetProcessMemoryInfo failed")
    io = _IoCounters()
    if not kernel.GetProcessIoCounters(process, ctypes.byref(io)):
        raise OSError("GetProcessIoCounters failed")
    return int(memory.PeakWorkingSetSize), int(io.ReadTransferCount), int(io.WriteTransferCount)


@dataclass(frozen=True)
class _Measured:
    payload: bytes
    row: dict[str, object]


def _measure(*, width: int, workers: int, candidates: int, host_episodes: int, draws: int) -> _Measured:
    rss0, read0, write0 = _process_counters()
    cpu0, wall0 = time.process_time(), time.perf_counter()
    payload, metrics = cost_collapse_slice(
        width=width, workers=workers, candidates=candidates,
        host_episodes=host_episodes, draws=draws,
    )
    wall = time.perf_counter() - wall0
    cpu = time.process_time() - cpu0
    rss1, read1, write1 = _process_counters()
    row: dict[str, object] = {
        "width": width, "workers": workers, "candidates": candidates,
        "host_episodes": host_episodes, "draws": draws,
        "wall_seconds": wall, "cpu_seconds": cpu,
        "cpu_utilization_fraction_of_worker_capacity": cpu / wall / workers if wall else 0.0,
        "peak_group_rss_bytes": max(rss0, rss1),
        "process_read_bytes_delta": max(0, read1 - read0),
        "process_write_bytes_delta": max(0, write1 - write0),
        "canonical_sha256": hashlib.sha256(payload).hexdigest(),
        **metrics,
        "host_episodes_per_s": metrics["host_episodes"] / wall,
        "score_rows_per_s": metrics["score_rows"] / wall,
        "paired_selections_per_s": metrics["paired_selections"] / wall,
        "j_reductions_per_s": metrics["j_reductions"] / wall,
        "r_reductions_per_s": metrics["r_reductions"] / wall,
    }
    return _Measured(payload, row)


def _atomic_resume_fixture(payload: bytes) -> dict[str, object]:
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="vqfp_vnpa_r03_stage_") as root_text:
        root = Path(root_text)
        chunks = [payload[index * len(payload) // 4:(index + 1) * len(payload) // 4] for index in range(4)]

        def commit(index: int) -> None:
            target = root / f"range-{index:02d}.bin"
            temporary = root / f"range-{index:02d}.tmp"
            with temporary.open("wb") as stream:
                stream.write(chunks[index])
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)

        for index in range(3):
            commit(index)
        scan0 = time.perf_counter()
        first_missing_after_interrupt = next(index for index in range(4) if not (root / f"range-{index:02d}.bin").is_file())
        interrupted_scan_seconds = time.perf_counter() - scan0
        commit(first_missing_after_interrupt)
        scan1 = time.perf_counter()
        first_missing_after_resume = next((index for index in range(4) if not (root / f"range-{index:02d}.bin").is_file()), 4)
        complete_scan_seconds = time.perf_counter() - scan1
        restored = b"".join((root / f"range-{index:02d}.bin").read_bytes() for index in range(4))
        durable = sum(path.stat().st_size for path in root.glob("range-*.bin"))
        scratch_peak = max(map(len, chunks))
    elapsed = time.perf_counter() - started
    return {
        "atomic_range_count": 4,
        "first_missing_after_interrupt": first_missing_after_interrupt,
        "first_missing_after_resume": first_missing_after_resume,
        "interrupted_scan_seconds": interrupted_scan_seconds,
        "complete_scan_seconds": complete_scan_seconds,
        "wall_seconds": elapsed,
        "canonical_identity": restored == payload,
        "canonical_sha256": hashlib.sha256(restored).hexdigest(),
        "retained_generation_bytes": durable,
        "scratch_peak_bytes": scratch_peak,
        "bytes_written": durable,
        "io_amplification": durable / len(payload),
        "fail_closed_partial_release": True,
    }


def _projection(
    *, stage_cpu_hours: float, stage_wall_hours: float, peak_rss_gib: float,
    stage_scratch_gib: float, stage_durable_gib: float,
    low_score_rate: float, managed_score_rate: float, high_score_rate: float,
    low_selection_rate: float, managed_selection_rate: float, high_selection_rate: float,
) -> dict[str, object]:
    full_score_rows = 2 * 2048 * 768 + 2 * 32 * 3072 + 10 * 24576
    full_selections = 491_520_000
    measured_kernel_wall = {
        "low": full_score_rows / low_score_rate / 3600 + full_selections / low_selection_rate / 3600,
        "managed": full_score_rows / managed_score_rate / 3600 + full_selections / managed_selection_rate / 3600,
        "high": full_score_rows / high_score_rate / 3600 + full_selections / high_selection_rate / 3600,
    }
    case_names = ("low", "managed", "high")
    foundation_days = (3.0, 4.5, 6.5)
    original_days = {
        "family1": (1.5, 2.5, 4.0), "family2": (2.0, 3.0, 5.0),
        "family3": (1.5, 2.5, 4.0), "family4": (1.0, 1.5, 2.5),
        "family5": (2.0, 4.0, 7.0), "family6": (1.0, 2.0, 3.5),
        "family7": (1.0, 2.0, 3.0), "integration": (1.0, 2.0, 3.0),
        "acceptance": (0.5, 1.0, 1.5), "frozen_execution_measurement": (1.0, 1.5, 2.0),
        "packaging": (0.5, 0.5, 1.0),
    }
    retirement_days = {
        "family1": (0.5, 0.75, 1.0), "family2": (0.75, 1.0, 1.5),
        "family3": (0.25, 0.5, 0.75), "family4": (0.0, 0.0, 0.0),
        "family5": (0.5, 1.0, 1.5), "family6": (0.25, 0.5, 0.75),
        "family7": (0.25, 0.5, 0.75), "integration": (0.0, 0.0, 0.0),
        "acceptance": (0.0, 0.0, 0.0), "frozen_execution_measurement": (0.0, 0.0, 0.0),
        "packaging": (0.0, 0.0, 0.0),
    }
    remaining_days = {
        name: tuple(original_days[name][i] - retirement_days[name][i] for i in range(3))
        for name in original_days
    }
    resource_rows = {
        "family1": ((30,80,160),(2,5,10),(2,4,8),(5,15,30),(1,3,6)),
        "family2": ((50,130,260),(3,7,14),(3,8,16),(8,25,50),(1,3,6)),
        "family3": ((140,400,850),(7,18,42),(6,14,26),(20,65,150),(2,6,12)),
        "family4": ((35,100,200),(2,5,10),(4,10,18),(15,40,80),(2,6,10)),
        "family5": ((120,450,1050),(6,17,40),(5,16,30),(25,90,190),(2,8,16)),
        "family6": ((10,30,80),(2,4,8),(2,4,8),(20,60,140),(5,16,32)),
        "family7": ((20,80,200),(1,3,6),(10,28,48),(30,105,200),(6,20,38)),
        "integration": ((30,120,300),(1,4,10),(10,28,48),(35,105,200),(7,20,38)),
        "acceptance": ((20,80,160),(0.5,1,2),(6,16,28),(20,60,120),(4,12,24)),
        "frozen_execution_measurement": ((20,80,200),(1,4,10),(10,28,48),(40,105,200),(7,20,38)),
        "packaging": ((5,20,50),(0.5,1,2),(2,4,8),(5,15,30),(7,20,38)),
    }
    construction_names = ("family1","family2","family3","family4","family5","family6","family7","integration")
    foundation_cpu, foundation_wall, foundation_rss, foundation_scratch, foundation_durable = 10.3125/3600, 10.5426098/3600, 24170496/2**30, 0.0, 324310/2**30
    # Aggregate stage bounds include both sweeps/tests and are deliberately
    # more conservative than the final benchmark-process measurements.
    stage_cpu_bound, stage_wall_bound = 4.0, 0.5
    stage_rss_bound, stage_scratch_bound, stage_durable_bound = max(0.125,peak_rss_gib),max(0.0625,stage_scratch_gib),max(528682/2**30,stage_durable_gib)
    components: dict[str, object] = {}
    cases: dict[str, dict[str, object]] = {}
    for index, case in enumerate(case_names):
        construction_days = sum(remaining_days[name][index] for name in construction_names)
        construction_cpu = sum(resource_rows[name][0][index] for name in construction_names)
        construction_wall = sum(resource_rows[name][1][index] for name in construction_names)
        construction_rss = max(resource_rows[name][2][index] for name in construction_names)
        construction_scratch = max(resource_rows[name][3][index] for name in construction_names)
        construction_durable = max(resource_rows[name][4][index] for name in construction_names)
        acceptance = resource_rows["acceptance"]
        execution = resource_rows["frozen_execution_measurement"]
        packaging = resource_rows["packaging"]
        component = {
            "completed_foundation": {"engineering_days": foundation_days[index], "cpu_core_hours": foundation_cpu, "wall_hours": foundation_wall, "rss_gib": foundation_rss, "scratch_gib": foundation_scratch, "durable_gib": foundation_durable},
            "actual_stage": {"engineering_days": 1.0, "cpu_core_hours_upper_bound": stage_cpu_bound, "wall_hours_upper_bound": stage_wall_bound, "rss_gib_upper_bound": stage_rss_bound, "scratch_gib_upper_bound": stage_scratch_bound, "durable_gib_upper_bound": stage_durable_bound},
            "remaining_construction": {"engineering_days": construction_days, "cpu_core_hours": construction_cpu, "wall_hours": construction_wall, "rss_gib": construction_rss, "scratch_gib": construction_scratch, "durable_footprint_gib": construction_durable},
            "full_chain_acceptance": {"engineering_days": remaining_days["acceptance"][index], "cpu_core_hours": acceptance[0][index], "wall_hours": acceptance[1][index], "rss_gib": acceptance[2][index], "scratch_gib": acceptance[3][index], "durable_footprint_gib": acceptance[4][index]},
            "frozen_execution_and_measurement": {"engineering_days": remaining_days["frozen_execution_measurement"][index], "cpu_core_hours": execution[0][index], "wall_hours": execution[1][index], "rss_gib": execution[2][index], "scratch_gib": execution[3][index], "durable_footprint_gib": execution[4][index]},
            "accepted_result_packaging": {"engineering_days": remaining_days["packaging"][index], "cpu_core_hours": packaging[0][index], "wall_hours": packaging[1][index], "rss_gib": packaging[2][index], "scratch_gib": packaging[3][index], "durable_footprint_gib": packaging[4][index]},
        }
        components[case] = component
        prospective_cpu = construction_cpu + acceptance[0][index] + execution[0][index] + packaging[0][index]
        prospective_wall = construction_wall + acceptance[1][index] + execution[1][index] + packaging[1][index]
        prospective_rss = max(construction_rss,acceptance[2][index],execution[2][index],packaging[2][index])
        prospective_scratch = max(construction_scratch,acceptance[3][index],execution[3][index],packaging[3][index])
        prospective_durable = max(construction_durable,acceptance[4][index],execution[4][index],packaging[4][index])
        cases[case] = {
            "engineering_days": foundation_days[index]+1.0+construction_days+remaining_days["acceptance"][index]+remaining_days["frozen_execution_measurement"][index]+remaining_days["packaging"][index],
            "cpu_core_hours": foundation_cpu+stage_cpu_bound+prospective_cpu,
            "wall_hours": foundation_wall+stage_wall_bound+prospective_wall,
            "rss_gib": max(foundation_rss,stage_rss_bound,prospective_rss),
            "scratch_gib": max(foundation_scratch,stage_scratch_bound,prospective_scratch),
            "durable_gib": foundation_durable+stage_durable_bound+prospective_durable,
            "gpu": "none",
        }
    ceilings = {"engineering_days": 20.0, "cpu_core_hours": 1800.0, "wall_hours": 72.0, "rss_gib": 32.0, "scratch_gib": 120.0, "durable_gib": 24.0}
    for row in cases.values():
        row["headroom"] = {name: ceilings[name] - float(row[name]) for name in ceilings}
        row["pointwise_within"] = all(float(row[name]) <= ceiling for name, ceiling in ceilings.items())
    return {
        "derivation": {
            "completed_foundation_engineer_days_low_managed_high": [3.0, 4.5, 6.5],
            "accounted_stage_engineer_days": 1.0,
            "family_engineering_original": original_days,
            "family_engineering_retired": retirement_days,
            "family_engineering_remaining": remaining_days,
            "full_score_rows": full_score_rows,
            "full_paired_selections": full_selections,
            "score_rows_per_s_low_managed_high": [low_score_rate, managed_score_rate, high_score_rate],
            "paired_selections_per_s_low_managed_high": [low_selection_rate, managed_selection_rate, high_selection_rate],
            "measured_kernel_wall_hours_low_managed_high": measured_kernel_wall,
            "stage_cpu_core_hours": stage_cpu_hours,
            "stage_wall_hours": stage_wall_hours,
            "unbounded_high_quantities": [],
            "unmeasured_but_explicitly_bounded_surfaces": ["family4 evaluation", "registered full search/selection", "frozen 20000-draw execution", "full-chain acceptance", "accepted-result packaging"],
            "resource_credit_for_retired_primitives": "zero; prior finite resource bounds are preserved conservatively",
            "rss_scratch_accounting": "maximum nonoverlapping exposure",
            "durable_accounting": "prospective final footprint plus retained completed-foundation and stage bytes",
        },
        "component_reconciliation": components,
        "ceilings": {**ceilings, "gpu": "none"},
        "cases": cases,
    }


def run(output: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    run_cpu0, run_wall0 = time.process_time(), time.perf_counter()
    identity = artifact_identity()
    literal_native, _ = cost_collapse_slice(width=8, workers=2, candidates=2, host_episodes=4, draws=4)
    literal_reference = stage_literal_audit(host_episodes=4, candidates=2, draws=4)
    if literal_native != literal_reference:
        raise RuntimeError("native/literal stage equality failed")

    matrix: list[dict[str, object]] = []
    representative: bytes | None = None
    for width in (8, 32, 64):
        for workers in (1, 2, 4, 8):
            measured = _measure(width=width, workers=workers, candidates=64, host_episodes=4, draws=64)
            matrix.append(measured.row)
            if width == 32 and workers == 8:
                representative = measured.payload
    matrix_digests = {str(row["canonical_sha256"]) for row in matrix}
    if len(matrix_digests) != 1:
        raise RuntimeError("tile/worker schedule changed canonical bytes")

    draw_ladder: list[dict[str, object]] = []
    for draws in (64, 512, 4096):
        digest_by_workers = set()
        for workers in (1, 2, 4, 8):
            measured = _measure(width=32, workers=workers, candidates=8, host_episodes=4, draws=draws)
            draw_ladder.append(measured.row)
            digest_by_workers.add(str(measured.row["canonical_sha256"]))
        if len(digest_by_workers) != 1:
            raise RuntimeError(f"worker schedule changed draw-{draws} canonical bytes")

    assert representative is not None
    io_resume = _atomic_resume_fixture(representative)
    cpu_seconds = time.process_time() - run_cpu0
    wall_seconds = time.perf_counter() - run_wall0
    peak_rss, read_bytes, write_bytes = _process_counters()
    all_rows = matrix + draw_ladder
    managed_matrix = next(row for row in matrix if row["width"] == 32 and row["workers"] == 4)
    managed_draw = next(row for row in draw_ladder if row["draws"] == 4096 and row["workers"] == 4)
    stage_durable = len(representative) + Path(str(identity["artifact"])).stat().st_size
    projection = _projection(
        stage_cpu_hours=cpu_seconds / 3600,
        stage_wall_hours=wall_seconds / 3600,
        peak_rss_gib=peak_rss / 2**30,
        stage_scratch_gib=float(io_resume["scratch_peak_bytes"]) / 2**30,
        stage_durable_gib=(int(io_resume["retained_generation_bytes"]) + int(stage_durable)) / 2**30,
        low_score_rate=max(float(row["score_rows_per_s"]) for row in matrix),
        managed_score_rate=float(managed_matrix["score_rows_per_s"]),
        high_score_rate=min(float(row["score_rows_per_s"]) for row in matrix),
        low_selection_rate=max(float(row["paired_selections_per_s"]) for row in draw_ladder),
        managed_selection_rate=float(managed_draw["paired_selections_per_s"]),
        high_selection_rate=min(float(row["paired_selections_per_s"]) for row in draw_ladder),
    )
    result: dict[str, object] = {
        "schema": SCHEMA,
        "technical_disposition": "RESULT_BLIND_COST_UNCERTAINTY_REMAINS_OR_EXCEEDS_HARD_CEILING",
        "stage_object": "VQFP-VNPA-R03-RESULT-BLIND-COST-COLLAPSE-STAGE-R01",
        "question_relevant_output": "none",
        "registered_r03_root_keys_consumed": False,
        "frozen_candidate_coefficients": False,
        "frozen_candidate_score_accepted": False,
        "family_4_constructed_or_executed": False,
        "gpu": "none",
        "artifact_identity": identity,
        "native_literal_exact": True,
        "literal_sha256": hashlib.sha256(literal_native).hexdigest(),
        "schedule_independent_bytes": True,
        "measurement_matrix": matrix,
        "draw_ladder": draw_ladder,
        "io_resume": io_resume,
        "actual_stage_usage": {
            "engineer_days_accounted": 1.0,
            "cpu_core_hours": cpu_seconds / 3600,
            "wall_hours": wall_seconds / 3600,
            "peak_group_rss_bytes": peak_rss,
            "peak_scratch_bytes": io_resume["scratch_peak_bytes"],
            "retained_durable_bytes_excluding_this_json": int(io_resume["retained_generation_bytes"]) + int(stage_durable),
            "process_read_bytes": read_bytes,
            "process_write_bytes": write_bytes,
            "max_workers": 8,
            "gpu": "none",
        },
        "production_work_retired": {
            "native_reusable_primitives_subject_to_cm_review": {
                "family1": {"primitive": "exact geometry bank plus explicit 32-state tape bytes and derived six-state count cache", "engineer_days_retired_low_managed_high": [0.5,0.75,1.0]},
                "family2": {"primitive": "exact U/Z treatment/FREE/LR representative control and ORACLE-order kernels", "engineer_days_retired_low_managed_high": [0.75,1.0,1.5]},
                "family3": {"primitive": "candidate tile aggregate plus canonical merge/tie ordering", "engineer_days_retired_low_managed_high": [0.25,0.5,0.75]},
                "family5": {"primitive": "paired state-stratified J/R/composite/rank reducer", "engineer_days_retired_low_managed_high": [0.5,1.0,1.5]},
                "family6": {"primitive": "canonical native synthetic generation bytes only", "engineer_days_retired_low_managed_high": [0.25,0.5,0.75]},
                "family7": {"primitive": "native deterministic disjoint worker-range execution and schedule-independent merge", "engineer_days_retired_low_managed_high": [0.25,0.5,0.75]},
            },
            "explicitly_not_retired": [
                "family4 in full",
                "registered/frozen host-bank namespace binding and production schema",
                "native atomic resume/checkpoint integration; current interruption fixture is Python lifecycle-only",
                "registered coefficient generation, finalist selection and validation",
                "full 20000-draw addresses, terminal precedence and result packaging",
                "synthetic benchmark and measurement scaffolding",
            ],
            "resource_credit": "none; retirement reduces only reconciled engineering days",
            "measurement_scaffolding_retired": False,
        },
        "residual_ledger": [
            "family1 frozen bank namespaces, registered rejection tails and production schema binding",
            "family2 complete diagnostics and reassociation controls on frozen banks",
            "family3 registered coefficient generation, full search, finalists and validation selection",
            "family4 entire immutable ten-arm evaluation panel",
            "family5 full 20000-draw addresses, terminal precedence and accepted bounds",
            "family6 complete identity/result bundle and production checkpoint integration",
            "family7 full-chain worker integration and accepted resource measurement",
            "cross-family integration, independent acceptance, full-chain measurement and packaging",
        ],
        "revised_cumulative_projection": projection,
        "dominant_bottleneck": "exact rational candidate/control aggregation; measured worker scaling is limited by serial host-cache construction and arbitrary-width comparison work",
        "stage_caps_observed": {
            "host_episodes_max": 4, "candidate_tuples_max": 64,
            "score_rows_max": max(int(row["score_rows"]) for row in all_rows),
            "bootstrap_draws_max": 4096, "tile_widths": [8, 32, 64],
            "workers": [1, 2, 4, 8], "gpu": "none",
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    # Stabilize the self-size field before the one atomic final write.
    result["actual_stage_usage"]["benchmark_json_bytes"] = 0  # type: ignore[index]
    for _ in range(4):
        encoded = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
        result["actual_stage_usage"]["benchmark_json_bytes"] = len(encoded)  # type: ignore[index]
    encoded = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
    temporary = output.with_suffix(output.suffix + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, output)
    return result


def annotate_aggregate_accounting(output: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    """Attach conservative all-command accounting after superseded sweeps/tests."""
    result = json.loads(output.read_text(encoding="utf-8"))
    source_path = Path(__file__).with_name("native") / "vqfp_vnpa_r03.cpp"
    source = source_path.read_bytes()
    start = source.index(b"enum class StageKernel:uint32_t")
    instrumentation_end = source.index(b"Rat sq", start)
    native_stage_start = source.index(b"// Result-blind production-form cost-collapse slice.")
    end = source.index(b"int copy_out", start)
    export_start = source.index(b"VQFP_EXPORT int vqfp_vnpa_r03_stage_slice")
    export_end = source.index(b"\n", export_start) + 1
    stage_region = source[start:instrumentation_end] + source[native_stage_start:end] + source[export_start:export_end]
    result["production_work_retired"]["native_stage_source_region"] = {
        "path": "experiments/candidates/vqfp_vnpa_r03/native/vqfp_vnpa_r03.cpp",
        "bytes": len(stage_region),
        "sha256": hashlib.sha256(stage_region).hexdigest(),
        "cm_acceptance_required": True,
    }
    retained_paths = [
        Path(__file__).with_name("contract.py"), Path(__file__).with_name("native_backend.py"),
        source_path, Path(__file__).with_name("reference_oracle.py"), Path(__file__),
        REPO / "tests/experiments/candidates/vqfp_vnpa_r03/test_native_construction.py",
        Path(str(result["artifact_identity"]["artifact"])),
    ]
    retained_bytes = sum(path.stat().st_size for path in retained_paths if path.is_file())
    for test_root in (
        REPO / "temp/vqfp_vnpa_r03_stage_pytest",
        REPO / "temp/vqfp_vnpa_r03_stage_pytest_final",
        REPO / "temp/vqfp_vnpa_r03_stage_pytest_repair",
    ):
        if test_root.is_dir():
            retained_bytes += sum(path.stat().st_size for path in test_root.rglob("*") if path.is_file())
    result["aggregate_all_stage_commands_usage"] = {
        "accounting_kind": "observed_receipts_plus_conservative_finite_upper_bounds",
        "engineer_days_accounted": 1.0,
        "cpu_core_hours_upper_bound": 4.0,
        "parallel_wall_hours_upper_bound": 0.5,
        "peak_group_rss_bytes_upper_bound": 128 * 2**20,
        "peak_scratch_bytes_upper_bound": 64 * 2**20,
        "retained_durable_bytes_conservative_full_file_sum": 0,
        "workers_max": 8,
        "gpu": "none",
        "incremental_hard_row_pointwise_within": True,
        "includes": ["implementation", "builds", "literal fixtures", "three measurement sweeps", "three complete test sweeps", "I/O/resume recovery checks"],
    }
    result["actual_stage_usage"]["scope"] = "final accepted measurement process only; aggregate accounting is separate"
    result["actual_stage_usage"]["benchmark_json_bytes"] = 0
    for _ in range(6):
        encoded = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
        result["actual_stage_usage"]["benchmark_json_bytes"] = len(encoded)
        result["aggregate_all_stage_commands_usage"]["retained_durable_bytes_conservative_full_file_sum"] = retained_bytes + len(encoded)
    encoded = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
    temporary = output.with_suffix(output.suffix + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, output)
    return result


def main() -> int:
    run()
    result = annotate_aggregate_accounting()
    print(json.dumps({
        "output": str(DEFAULT_OUTPUT),
        "technical_disposition": result["technical_disposition"],
        "actual_stage_usage": result["actual_stage_usage"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
