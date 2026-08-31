"""Result-blind prospective admission for the fresh CRTO common-history object."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Final, Iterable, Mapping, Sequence

from .config import (
    CPU_WORKERS, MAX_PRIMITIVE_TEAM_STEPS, OBJECT_ID, PEAK_RSS_BYTES, REPLICATES,
    RNG_NAMESPACE, WALL_SECONDS,
)
from .contracts import Split
from .host_bridge import (
    BoundaryScanRow, build_balanced_tapes, canonical_calibration_specs,
    evaluation_tape_batches, scan_common_history_boundary,
)
from .ledger import prospective_ledger_report


MINIMUM_AVAILABLE_BYTES: Final = 4 * 1024**3
THREADS_PER_WORKER: Final = 1
PACKAGE_ROOT: Final = Path(__file__).resolve().parent
REPOSITORY_ROOT: Final = PACKAGE_ROOT.parents[2]
RESOURCE_SCRIPT: Final = REPOSITORY_ROOT / "scripts" / "hmasd_resource_preflight.py"


@dataclass(frozen=True)
class PopulationBlock:
    split: str
    regime: str
    first_episode_index: int
    last_episode_index: int
    count: int
    construction: str


POPULATION_SCHEDULE: Final = (
    PopulationBlock("PREDICTOR_FIT", "K4", 0, 127, 128, "BALANCED_SHUFFLED"),
    PopulationBlock("PREDICTOR_FIT", "K8", 128, 255, 128, "BALANCED_SHUFFLED"),
    PopulationBlock("CALIBRATION", "K4", 256, 287, 32, "CALIBRATION_FORMULA"),
    PopulationBlock("CALIBRATION", "K8", 288, 319, 32, "CALIBRATION_FORMULA"),
    PopulationBlock("TRAIN", "K8", 320, 831, 512, "BALANCED_SHUFFLED"),
    PopulationBlock("EVALUATION", "K8", 832, 895, 64, "BALANCED_SHUFFLED"),
    PopulationBlock("EVALUATION", "K16", 896, 959, 64, "BALANCED_SHUFFLED"),
    PopulationBlock("EVALUATION", "K4_TO_16", 960, 1023, 64, "BALANCED_SHUFFLED"),
    PopulationBlock("EVALUATION", "K16_TO_4", 1024, 1087, 64, "BALANCED_SHUFFLED"),
)


def canonical_population_schedule() -> tuple[PopulationBlock, ...]:
    return POPULATION_SCHEDULE


def validate_population_schedule() -> tuple[str, ...]:
    issues: list[str] = []
    indices: list[int] = []
    for block in POPULATION_SCHEDULE:
        if block.last_episode_index - block.first_episode_index + 1 != block.count:
            issues.append(f"{block.split}/{block.regime} episode range/count mismatch")
        indices.extend(range(block.first_episode_index, block.last_episode_index + 1))
    if indices != list(range(1_088)):
        issues.append("population episode indices are not the exact disjoint 0..1087 schedule")
    for replicate in REPLICATES:
        for regime, first in (("K4", 256), ("K8", 288)):
            specs = canonical_calibration_specs(replicate=replicate, regime=regime)
            if tuple(spec.episode_index for spec in specs) != tuple(range(first, first + 32)):
                issues.append(f"slot {replicate} {regime} calibration index formula drifted")
            for offset, spec in enumerate(specs):
                cell, within_cell = divmod(offset, 4)
                from experiments.candidates.commitment_residual_triggered_options.host import FIXED_ONSETS
                if spec.event_onset != FIXED_ONSETS[(cell + within_cell) % 8]:
                    issues.append(f"slot {replicate} {regime} calibration onset formula drifted")
                    break
    return tuple(issues)


def validate_resource_receipt(receipt: Mapping[str, object]) -> tuple[str, ...]:
    issues: list[str] = []
    if receipt.get("schema_version") != 1:
        issues.append("shared resource receipt schema_version must equal 1")
    if receipt.get("minimum_available_bytes") != MINIMUM_AVAILABLE_BYTES:
        issues.append("shared resource receipt does not bind the exact 4-GiB floor")
    for field in ("available_physical_bytes", "effective_available_bytes"):
        value = receipt.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < MINIMUM_AVAILABLE_BYTES:
            issues.append(f"shared resource receipt {field} is absent or below 4 GiB")
    if receipt.get("physical_floor_pass") is not True:
        issues.append("shared resource receipt physical floor did not pass")
    if receipt.get("effective_floor_pass") is not True:
        issues.append("shared resource receipt effective floor did not pass")
    if receipt.get("passed") is not True:
        issues.append("shared resource receipt final admission did not pass")
    reasons = receipt.get("failure_reasons")
    if not isinstance(reasons, list) or reasons:
        issues.append("shared resource receipt contains missing or nonempty failure reasons")
    return tuple(issues)


def validate_run_resource_receipt(receipt: Mapping[str, object]) -> tuple[str, ...]:
    issues: list[str] = []
    expected = {
        "workers": 1,
        "threads_per_worker": 1,
        "minimum_available_bytes": MINIMUM_AVAILABLE_BYTES,
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            issues.append(f"shared assess-run receipt {field} must equal {value}")
    estimate = receipt.get("estimate")
    if not isinstance(estimate, Mapping):
        issues.append("shared assess-run receipt estimate is missing")
    else:
        try:
            wall = float(estimate.get("wall_seconds", -1))
            peak = float(estimate.get("peak_memory_gib", -1))
        except (TypeError, ValueError):
            wall = peak = -1.0
        if wall != 7_200.0:
            issues.append("shared assess-run wall estimate must equal 7,200 seconds")
        if peak != 2.0:
            issues.append("shared assess-run peak estimate must equal 2 GiB")
    if receipt.get("physical_floor_pass") is not True:
        issues.append("shared assess-run physical 4-GiB floor did not pass")
    if receipt.get("effective_floor_pass") is not True:
        issues.append("shared assess-run effective 4-GiB floor did not pass")
    if receipt.get("memory_floor_pass") is not True or receipt.get("memory_safe") is not True:
        issues.append("shared assess-run memory admission did not pass")
    return tuple(issues)


def load_resource_receipt(path: Path) -> Mapping[str, object]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"shared resource receipt is unreadable: {error}") from error
    if not isinstance(payload, Mapping):
        raise ValueError("shared resource receipt must be a JSON object")
    issues = validate_resource_receipt(payload)
    if issues:
        raise ValueError("; ".join(issues))
    return payload


def create_shared_resource_receipt(path: Path) -> Mapping[str, object]:
    """Run the repository-wide 4-GiB admission command into one fresh receipt."""

    target = Path(path).resolve()
    if target.exists():
        raise FileExistsError("resource receipt must be fresh for this invocation")
    target.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [sys.executable, str(RESOURCE_SCRIPT), "admit-memory", "--out", str(target)],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "shared 4-GiB resource admission failed: "
            + (completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}")
        )
    return load_resource_receipt(target)


def create_shared_run_assessment(path: Path, *, run_id: str) -> Mapping[str, object]:
    target = Path(path).resolve()
    if target.exists():
        raise FileExistsError("assess-run receipt must be fresh for this invocation")
    target.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            sys.executable, str(RESOURCE_SCRIPT), "assess-run",
            "--direction", "commitment_residual_triggered_options",
            "--run-id", run_id,
            "--workers", "1", "--threads-per-worker", "1",
            "--estimated-wall-seconds", "7200", "--estimated-peak-gib", "2",
            "--basis", "CRTO prospective frozen one-worker CPU envelope",
            "--out", str(target),
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "shared assess-run admission failed: "
            + (completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}")
        )
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"shared assess-run receipt is unreadable: {error}") from error
    if not isinstance(payload, Mapping):
        raise ValueError("shared assess-run receipt must be a JSON object")
    issues = validate_run_resource_receipt(payload)
    if issues:
        raise ValueError("; ".join(issues))
    return payload


def _scan_registered_histories() -> tuple[BoundaryScanRow, ...]:
    """Scan final manifests without a predictor, G16 rollout, packet, model, or optimizer."""

    rows: list[BoundaryScanRow] = []
    for replicate in REPLICATES:
        training = build_balanced_tapes(
            replicate=replicate, split=Split.TRAIN, regime="K8", count=512,
            first_episode_index=320,
        )
        rows.extend(
            scan_common_history_boundary(tape, replicate=replicate, split=Split.TRAIN)
            for tape in training
        )
        for tapes in evaluation_tape_batches(
            replicate=replicate, split=Split.EVALUATION, count_per_regime=64,
            first_episode_index=832,
        ).values():
            rows.extend(
                scan_common_history_boundary(tape, replicate=replicate, split=Split.EVALUATION)
                for tape in tapes
            )
    return tuple(rows)


def assess_structural_scan(rows: Sequence[BoundaryScanRow]) -> dict[str, object]:
    """Assess exact result-blind availability, cell support, and branch ledger facts."""

    issues: list[str] = []
    # The actual scanner is slot-major: one slot's TRAIN followed by its four
    # evaluation regimes. Rebuild that exact sequence rather than accepting a
    # set-equivalent permutation of the eight fixed outer slots.
    expected_keys_ordered = []
    for replicate in REPLICATES:
        expected_keys_ordered.extend(
            (replicate, "TRAIN", "K8", episode) for episode in range(320, 832)
        )
        for regime, first in (
            ("K8", 832), ("K16", 896), ("K4_TO_16", 960), ("K16_TO_4", 1024),
        ):
            expected_keys_ordered.extend(
                (replicate, "EVALUATION", regime, episode)
                for episode in range(first, first + 64)
            )
    actual_keys = [
        (row.replicate, row.split.value, row.regime, row.episode_index) for row in rows
    ]
    if actual_keys != expected_keys_ordered:
        issues.append(
            "structural scan must contain outer replicate ids exactly ordered 0..7 and every "
            "frozen TRAIN/EVALUATION episode in canonical order"
        )
    retained = tuple(row for row in rows if row.row_present)
    if any(
        row.primitive_time is None or row.agent is None or row.elapsed_horizon not in (4, 8, 12, 16)
        or row.legal_common_future_branches < 2
        for row in retained
    ):
        issues.append("retained structural row has an invalid boundary or legal branch count")
    availability: dict[str, int] = {}
    for replicate in REPLICATES:
        for regime in ("K8", "K16", "K4_TO_16", "K16_TO_4"):
            count = sum(
                row.row_present and row.replicate == replicate
                and row.split is Split.EVALUATION and row.regime == regime
                for row in rows
            )
            availability[f"{replicate}/{regime}"] = count
            if count < 48:
                issues.append(f"slot {replicate} evaluation {regime} retained {count}/64 (<48)")
    cell_counts = Counter(
        (row.replicate, row.derangement_cell)
        for row in retained if row.derangement_cell is not None
    )
    supported = {cell for cell, count in cell_counts.items() if count >= 8}
    supported_counts: dict[str, int] = {}
    for split in (Split.TRAIN, Split.EVALUATION):
        for replicate in REPLICATES:
            denominator = sum(
                row.replicate == replicate and row.split is split for row in retained
            )
            count = sum(
                row.replicate == replicate and row.split is split
                and (row.replicate, row.derangement_cell) in supported
                for row in retained
            )
            supported_counts[f"{replicate}/{split.value}"] = count
            if denominator == 0 or count < math.ceil(0.80 * denominator):
                issues.append(
                    f"slot {replicate} {split.value} supported-cell rows {count}/{denominator} (<80%)"
                )
    branch_count = sum(row.legal_common_future_branches for row in retained)
    ledger = prospective_ledger_report(branch_count)
    if ledger["within_ceiling"] is not True:
        issues.append(
            f"exact structural ledger {ledger['actual_total_steps']} exceeds ceiling "
            f"{MAX_PRIMITIVE_TEAM_STEPS}"
        )
    return {
        "passed": not issues,
        "issues": issues,
        "scanned_episode_count": len(rows),
        "retained_row_count": len(retained),
        "availability": availability,
        "derangement_cell_counts": {
            f"{cell[0]}/" + "/".join(map(str, cell[1])): count
            for cell, count in sorted(cell_counts.items())
        },
        "supported_fixed_denominator_counts": supported_counts,
        "ledger": ledger,
        "activity": {
            "tapes_materialized": len(rows),
            "scripted_history_transitions": sum(
                row.scripted_history_transitions for row in rows
            ),
            "predictor_forecasts": 0,
            "common_future_rollouts": 0,
            "models_constructed": 0,
            "optimizer_updates": 0,
            "checkpoints": 0,
            "result_roots": 0,
            "results": 0,
        },
    }


def _fresh_target_issues(output_root: Path, result_path: Path) -> tuple[str, ...]:
    output = Path(output_root).resolve()
    result = Path(result_path).resolve()
    issues: list[str] = []
    if output.exists():
        issues.append("scientific output root is not fresh")
    if result.exists():
        issues.append("scientific result path is not fresh")
    if output == result or output in result.parents:
        issues.append("scientific result path must be outside the output root")
    return tuple(issues)


def prospective_preflight(
    *,
    resource_receipt: Mapping[str, object],
    run_resource_receipt: Mapping[str, object] | None,
    output_root: Path,
    result_path: Path,
    structural_scan: Sequence[BoundaryScanRow] | None = None,
    scan_final_namespace: bool = False,
) -> dict[str, object]:
    """Run result-blind admission; production is ready only when every gate passes."""

    resource_issues = list(validate_resource_receipt(resource_receipt))
    run_resource_issues = (
        ["fresh shared assess-run receipt was not supplied"]
        if run_resource_receipt is None
        else list(validate_run_resource_receipt(run_resource_receipt))
    )
    schedule_issues = list(validate_population_schedule())
    target_issues = list(_fresh_target_issues(output_root, result_path))
    runtime_issues: list[str] = []
    if CPU_WORKERS != 1 or THREADS_PER_WORKER != 1:
        runtime_issues.append("runtime must use one worker and one thread")
    if PEAK_RSS_BYTES != 2 * 1024**3 or WALL_SECONDS != 7_200:
        runtime_issues.append("runtime must bind the exact 2-GiB RSS and 7,200-second ceilings")
    if structural_scan is None and scan_final_namespace:
        structural_scan = _scan_registered_histories()
    if structural_scan is None:
        scan_report = {
            "passed": False,
            "issues": ["exact final-namespace structural dry scan was not supplied"],
            "activity": {
                "tapes_materialized": 0, "scripted_history_transitions": 0,
                "predictor_forecasts": 0, "common_future_rollouts": 0,
                "models_constructed": 0, "optimizer_updates": 0, "checkpoints": 0,
                "result_roots": 0, "results": 0,
            },
        }
    else:
        scan_report = assess_structural_scan(structural_scan)
    gates = {
        "resource_4gib": {"passed": not resource_issues, "issues": resource_issues},
        "resource_run_envelope": {
            "passed": not run_resource_issues, "issues": run_resource_issues,
        },
        "exact_population_schedule": {"passed": not schedule_issues, "issues": schedule_issues},
        "fresh_scientific_targets": {"passed": not target_issues, "issues": target_issues},
        "runtime_envelope": {"passed": not runtime_issues, "issues": runtime_issues},
        "result_blind_structural_scan": {
            "passed": scan_report.get("passed") is True,
            "issues": list(scan_report.get("issues", [])),
        },
        "single_pass_production_pipeline": {
            "passed": False,
            "issues": [
                "ENGINEERING_SINGLE_PASS_RESIDUAL_CALIBRATION_PIPELINE_INCOMPLETE: the formal "
                "runner does not yet bind all-horizon calibration residuals and the first audit "
                "row to one full 256-step TRAIN/EVALUATION host traversal, nor the staged "
                "RAW-LONG competence stop to the analysis API; it also lacks the second fresh "
                "4-GiB/assess-run recheck immediately after the potentially long dry scan and "
                "before model/optimizer construction; remain before every model and optimizer"
            ],
        },
    }
    return {
        "format": "CRTO_COMMON_HISTORY_PROSPECTIVE_PREFLIGHT_V1",
        "object_id": OBJECT_ID,
        "rng_namespace": RNG_NAMESPACE,
        "replicates": list(REPLICATES),
        "population_schedule": [asdict(block) for block in POPULATION_SCHEDULE],
        "resource": dict(resource_receipt),
        "run_resource": None if run_resource_receipt is None else dict(run_resource_receipt),
        "resource_contract": {
            "workers": 1, "threads_per_worker": 1,
            "peak_rss_bytes": 2 * 1024**3, "wall_seconds": 7_200,
            "minimum_available_bytes": MINIMUM_AVAILABLE_BYTES,
        },
        "gates": gates,
        "structural_scan": scan_report,
        "ready_for_optimizer": all(gate["passed"] for gate in gates.values()),
        "activity": scan_report["activity"],
    }


def atomic_create_json(path: Path, payload: Mapping[str, object]) -> None:
    target = Path(path).resolve()
    if target.exists():
        raise FileExistsError(f"fresh receipt already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    temporary_name: str | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{target.name}.", suffix=".tmp", dir=target.parent,
        )
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.rename(temporary_name, target)
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


__all__ = [
    "BoundaryScanRow",
    "PopulationBlock",
    "assess_structural_scan",
    "atomic_create_json",
    "canonical_population_schedule",
    "create_shared_resource_receipt",
    "create_shared_run_assessment",
    "prospective_preflight",
    "validate_population_schedule",
    "validate_resource_receipt",
    "validate_run_resource_receipt",
]
