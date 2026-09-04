"""Frozen two-slot RAW-LONG development-feasibility transaction."""

from __future__ import annotations

from dataclasses import dataclass, field
import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Callable, Mapping, Sequence

import numpy as np

from .config import (
    BUDGETS,
    CPU_WORKERS,
    EVALUATION_EPISODES_PER_REGIME,
    PILOT_OBJECT_ID,
    PILOT_RNG_NAMESPACE,
    PILOT_SLOTS,
    PEAK_RSS_BYTES,
    MATERIAL_ADVANTAGE_THRESHOLD,
    MATERIAL_STRATA,
    MAX_PRIMITIVE_TEAM_STEPS,
    MINIMUM_K8_ROWS_PER_MATERIAL_STRATUM,
    NUMERIC_TOLERANCE,
    PILOT_LAUNCH_RUN_ID,
    RAW_LONG_MAX_MEAN_REGRET,
    RNG_NAMESPACE,
    WALL_SECONDS,
)
from .contracts import Budget, PanelRow, Representation, Split
from .host_bridge import (
    BoundaryScanRow,
    build_balanced_tapes,
    materialize_episode_observables,
    materialize_predictor_examples,
    scan_common_history_boundary,
)
from .ledger import ResourceLimitExceeded, _peak_rss_bytes
from .preflight import (
    atomic_create_json,
    create_shared_resource_receipt,
    create_shared_run_assessment,
    validate_resource_receipt,
    validate_run_resource_receipt,
)

PILOT_BASE_EPISODES_PER_SLOT = 256 + 512 + 64
PILOT_BASE_PRIMITIVE_TEAM_STEPS = (
    len(PILOT_SLOTS) * PILOT_BASE_EPISODES_PER_SLOT * 256
)
PILOT_BASE_EPISODE_COUNT = len(PILOT_SLOTS) * PILOT_BASE_EPISODES_PER_SLOT


@dataclass(frozen=True)
class PilotConfig:
    """Non-selectable registration for the development-only RAW pilot."""

    object_id: str = field(default=PILOT_OBJECT_ID, init=False)
    rng_namespace: int = field(default=PILOT_RNG_NAMESPACE, init=False)
    slots: tuple[int, ...] = field(default=PILOT_SLOTS, init=False)
    launch_run_id: str = field(default=PILOT_LAUNCH_RUN_ID, init=False)
    representation: str = field(default="RAW", init=False)
    checkpoint: str = field(default="LONG", init=False)
    updates: int = field(default=BUDGETS["LONG"], init=False)
    evaluation_regimes: tuple[str, ...] = field(default=("K8",), init=False)
    evaluation_episodes_per_slot: int = field(
        default=EVALUATION_EPISODES_PER_REGIME, init=False,
    )
    claim_ceiling: str = field(
        default="TWO_SLOT_RAW_LONG_DEVELOPMENT_FEASIBILITY_ONLY", init=False,
    )
    feasibility_only: bool = field(default=True, init=False)

    def validate(self) -> None:
        if (
            self.object_id != PILOT_OBJECT_ID
            or self.rng_namespace != PILOT_RNG_NAMESPACE
            or self.rng_namespace == RNG_NAMESPACE
            or self.slots != (0, 1)
            or self.launch_run_id != PILOT_LAUNCH_RUN_ID
        ):
            raise ValueError("pilot object registration or RNG namespace drifted")
        if (
            self.representation != "RAW"
            or self.checkpoint != "LONG"
            or self.updates != 2_048
            or self.evaluation_regimes != ("K8",)
            or self.evaluation_episodes_per_slot != 64
        ):
            raise ValueError("pilot RAW-LONG development law drifted")
        if (
            self.claim_ceiling != "TWO_SLOT_RAW_LONG_DEVELOPMENT_FEASIBILITY_ONLY"
            or self.feasibility_only is not True
        ):
            raise ValueError("pilot claim ceiling drifted")


PILOT_CONFIG = PilotConfig()
PILOT_CONFIG.validate()


def assess_pilot_structural_scan(
    rows: Sequence[BoundaryScanRow],
) -> dict[str, object]:
    """Validate the exact result-blind two-slot K8 TRAIN/EVALUATION scan."""

    issues: list[str] = []
    expected_keys: list[tuple[int, str, str, int]] = []
    for slot in PILOT_SLOTS:
        expected_keys.extend((slot, "TRAIN", "K8", episode) for episode in range(320, 832))
        expected_keys.extend(
            (slot, "EVALUATION", "K8", episode) for episode in range(832, 896)
        )
    actual_keys = [
        (row.replicate, row.split.value, row.regime, row.episode_index) for row in rows
    ]
    if actual_keys != expected_keys:
        issues.append(
            "pilot structural scan must use canonical slot-major order over slots 0,1 and "
            "only the frozen K8 TRAIN/EVALUATION episodes"
        )
    retained = tuple(row for row in rows if row.row_present)
    if any(
        row.primitive_time is None
        or row.agent is None
        or row.elapsed_horizon not in (4, 8, 12, 16)
        or row.legal_common_future_branches < 2
        for row in retained
    ):
        issues.append("pilot retained row has an invalid boundary or branch count")
    availability: dict[str, int] = {}
    support_failures: list[str] = []
    for slot in PILOT_SLOTS:
        count = sum(
            row.row_present
            and row.replicate == slot
            and row.split is Split.EVALUATION
            and row.regime == "K8"
            for row in rows
        )
        availability[f"{slot}/K8"] = count
        if count < 48:
            support_failures.append(f"pilot slot {slot} K8 retained {count}/64 (<48)")
    cell_counts = Counter(
        (row.replicate, row.derangement_cell)
        for row in retained if row.derangement_cell is not None
    )
    supported = {cell for cell, count in cell_counts.items() if count >= 8}
    supported_counts: dict[str, dict[str, int]] = {}
    for slot in PILOT_SLOTS:
        for split in (Split.TRAIN, Split.EVALUATION):
            denominator = sum(
                row.replicate == slot and row.split is split for row in retained
            )
            count = sum(
                row.replicate == slot
                and row.split is split
                and (row.replicate, row.derangement_cell) in supported
                for row in retained
            )
            supported_counts[f"{slot}/{split.value}"] = {
                "supported": count,
                "retained_denominator": denominator,
            }
            if denominator == 0 or count < math.ceil(0.80 * denominator):
                support_failures.append(
                    f"pilot slot {slot} {split.value} supported-cell rows "
                    f"{count}/{denominator} (<80%)"
                )
    branches = sum(row.legal_common_future_branches for row in retained)
    common_future_steps = 16 * branches
    total_steps = PILOT_BASE_PRIMITIVE_TEAM_STEPS + common_future_steps
    within_ceiling = total_steps <= MAX_PRIMITIVE_TEAM_STEPS
    if not within_ceiling:
        issues.append(
            f"pilot exact work {total_steps} exceeds ceiling {MAX_PRIMITIVE_TEAM_STEPS}"
        )
    return {
        "passed": not issues,
        "issues": issues,
        "support_passed": not support_failures,
        "support_failures": support_failures,
        "scanned_episode_count": len(rows),
        "retained_row_count": len(retained),
        "availability": availability,
        "supported_fixed_denominator_counts": supported_counts,
        "supported_cells": [
            {
                "slot": slot,
                "split": cell[0],
                "regime": cell[1],
                "elapsed_horizon": cell[2],
                "cost": cell[3],
                "row_count": cell_counts[(slot, cell)],
            }
            for slot, cell in sorted(supported)
        ],
        "expected_common_future_branch_count": branches,
        "work": {
            "formula": (
                "2*(256+512+64)*256 + 16*actual_common_future_branch_count"
            ),
            "base_episode_count": len(PILOT_SLOTS) * PILOT_BASE_EPISODES_PER_SLOT,
            "base_primitive_team_steps": PILOT_BASE_PRIMITIVE_TEAM_STEPS,
            "actual_common_future_branch_count": branches,
            "actual_common_future_steps": common_future_steps,
            "actual_total_steps": total_steps,
            "ceiling": MAX_PRIMITIVE_TEAM_STEPS,
            "within_ceiling": within_ceiling,
        },
        "activity": {
            "tapes_materialized": len(rows),
            "scripted_history_transitions": sum(
                row.scripted_history_transitions for row in rows
            ),
            "predictor_forecasts": 0,
            "common_future_rollouts": 0,
            "models_constructed": 0,
            "optimizer_updates": 0,
            "true_residual_training": 0,
            "deranged_training": 0,
            "final_namespace_reads": 0,
            "result_roots": 0,
            "results": 0,
        },
    }


def assess_pilot_competence(
    summaries: tuple[EvaluationSummary, ...],
) -> dict[str, object]:
    """Apply the frozen support and 0.01 gate to the four pilot cells."""

    from .evaluation import EvaluationSummary

    support_failures: list[str] = []
    numeric_failures: list[str] = []
    if len(summaries) != len(PILOT_SLOTS):
        support_failures.append("pilot requires exactly slots 0 and 1")
    else:
        for expected_slot, summary in zip(PILOT_SLOTS, summaries):
            if not isinstance(summary, EvaluationSummary):
                support_failures.append(f"slot {expected_slot} summary is not typed evidence")
                continue
            if summary.replicate != expected_slot:
                support_failures.append(
                    f"outer slot {expected_slot} is bound to replicate {summary.replicate}"
                )
            if (
                summary.representation is not Representation.RAW
                or summary.budget is not Budget.LONG
            ):
                support_failures.append(f"slot {expected_slot} is not RAW-LONG")
            if summary.row_count_by_regime.get("K8", 0) < 48:
                support_failures.append(f"slot {expected_slot} has fewer than 48 K8 rows")
            counts = summary.material_stratum_count_by_regime.get("K8", {})
            raw_means = summary.mean_regret_by_regime_and_material_stratum.get("K8", {})
            script_means = (
                summary.logged_scripted_mean_regret_by_regime_and_material_stratum.get("K8", {})
            )
            for stratum in MATERIAL_STRATA:
                count = counts.get(stratum)
                raw = raw_means.get(stratum)
                script = script_means.get(stratum)
                if count is None or count < MINIMUM_K8_ROWS_PER_MATERIAL_STRATUM:
                    support_failures.append(
                        f"slot {expected_slot} K8/{stratum} has fewer than "
                        f"{MINIMUM_K8_ROWS_PER_MATERIAL_STRATUM} rows"
                    )
                if raw is None or not np.isfinite(raw) or raw < 0.0:
                    support_failures.append(
                        f"slot {expected_slot} K8/{stratum} RAW regret is invalid"
                    )
                elif raw > RAW_LONG_MAX_MEAN_REGRET + NUMERIC_TOLERANCE:
                    numeric_failures.append(
                        f"slot {expected_slot} K8/{stratum} RAW mean regret exceeds "
                        f"{RAW_LONG_MAX_MEAN_REGRET:.12f}"
                    )
                if script is None or not np.isfinite(script) or script < 0.0:
                    support_failures.append(
                        f"slot {expected_slot} K8/{stratum} scripted regret is invalid"
                    )

    common = {
        "claim_ceiling": PILOT_CONFIG.claim_ceiling,
        "feasibility_only": True,
    }
    if support_failures:
        return {
            **common,
            "status": "NONIDENTIFYING",
            "disposition": "NONIDENTIFYING_PILOT_K8_SUPPORT",
            "failures": support_failures,
            "cells": [],
        }

    cells: list[dict[str, object]] = []
    for slot, summary in zip(PILOT_SLOTS, summaries):
        counts = summary.material_stratum_count_by_regime["K8"]
        raw_means = summary.mean_regret_by_regime_and_material_stratum["K8"]
        script_means = summary.logged_scripted_mean_regret_by_regime_and_material_stratum["K8"]
        for stratum in MATERIAL_STRATA:
            raw = float(raw_means[stratum])
            script = float(script_means[stratum])
            cells.append({
                "slot": slot,
                "stratum": stratum,
                "row_count": int(counts[stratum]),
                "raw_mean_regret": raw,
                "script_mean_regret": script,
                "raw_minus_script": raw - script,
                "ceiling": RAW_LONG_MAX_MEAN_REGRET,
            })
    if numeric_failures:
        return {
            **common,
            "status": "FAIL",
            "disposition": "PILOT_RAW_LONG_INCOMPETENT",
            "failures": numeric_failures,
            "cells": cells,
        }
    return {
        **common,
        "status": "PASS",
        "disposition": "PILOT_FEASIBLE",
        "failures": [],
        "cells": cells,
    }


def route_pilot_execution_evidence(
    completed_summaries: tuple[EvaluationSummary, ...],
    support_failures: Sequence[str],
) -> tuple[tuple[EvaluationSummary, ...], dict[str, object]]:
    """Suppress every partial question-relevant summary on any support failure."""

    if support_failures:
        return (), {
            "status": "NONIDENTIFYING",
            "disposition": "NONIDENTIFYING_PILOT_K8_SUPPORT",
            "failures": list(support_failures),
            "cells": [],
            "claim_ceiling": PILOT_CONFIG.claim_ceiling,
            "feasibility_only": True,
        }
    return completed_summaries, assess_pilot_competence(completed_summaries)


class PilotWorkLedger:
    """Exact two-slot work and runtime monitor for the RAW-only pilot."""

    def __init__(self, *, expected_common_future_branches: int) -> None:
        if (
            isinstance(expected_common_future_branches, bool)
            or not isinstance(expected_common_future_branches, int)
            or expected_common_future_branches < 0
        ):
            raise ValueError("pilot expected branch count must be a nonnegative integer")
        planned = PILOT_BASE_PRIMITIVE_TEAM_STEPS + 16 * expected_common_future_branches
        if planned > MAX_PRIMITIVE_TEAM_STEPS:
            raise ResourceLimitExceeded("pilot prospective work exceeds the frozen ceiling")
        self._expected_branches = expected_common_future_branches
        self._base_episodes = 0
        self._branches = 0
        self._started = time.monotonic()
        self._peak = _peak_rss_bytes()
        self.check_limits()

    @property
    def actual_total_steps(self) -> int:
        return 256 * self._base_episodes + 16 * self._branches

    def check_limits(self) -> None:
        self._peak = max(self._peak, _peak_rss_bytes())
        if self._peak > PEAK_RSS_BYTES:
            raise ResourceLimitExceeded("pilot crossed the 2-GiB peak RSS ceiling")
        if time.monotonic() - self._started > WALL_SECONDS:
            raise ResourceLimitExceeded("pilot crossed the 7,200-second wall ceiling")
        if self.actual_total_steps > MAX_PRIMITIVE_TEAM_STEPS:
            raise ResourceLimitExceeded("pilot crossed the primitive-team-step ceiling")

    def record_base_episodes(self, episode_count: int) -> None:
        if isinstance(episode_count, bool) or not isinstance(episode_count, int) or episode_count < 0:
            raise ValueError("pilot base episode count must be a nonnegative integer")
        if self._base_episodes + episode_count > PILOT_BASE_EPISODE_COUNT:
            raise ResourceLimitExceeded("pilot executed more base episodes than assigned")
        self._base_episodes += episode_count
        self.check_limits()

    def require_common_future_headroom(self, branch_count: int) -> None:
        if isinstance(branch_count, bool) or not isinstance(branch_count, int) or branch_count <= 0:
            raise ValueError("pilot G16 branch count must be positive")
        if self.actual_total_steps + 16 * branch_count > MAX_PRIMITIVE_TEAM_STEPS:
            raise ResourceLimitExceeded("pilot lacks prospective G16 work headroom")
        self.check_limits()

    def record_common_future_branch(self, executed_steps: int) -> None:
        if executed_steps != 16:
            raise ValueError("every pilot common-future branch must execute exactly 16 steps")
        self._branches += 1
        if self._branches > self._expected_branches:
            raise ResourceLimitExceeded("pilot exceeded its result-blind branch count")
        self.check_limits()

    def assert_complete(self) -> None:
        if self._base_episodes != PILOT_BASE_EPISODE_COUNT:
            raise ResourceLimitExceeded("pilot base-tape traversal is incomplete")
        if self._branches != self._expected_branches:
            raise ResourceLimitExceeded("pilot G16 count disagrees with the result-blind scan")
        self.check_limits()

    def receipt(self, *, require_exact_branches: bool = True) -> dict[str, object]:
        if self._base_episodes != PILOT_BASE_EPISODE_COUNT:
            raise ResourceLimitExceeded("pilot base-tape traversal is incomplete")
        if require_exact_branches:
            self.assert_complete()
        else:
            self.check_limits()
        return {
            "formula": "2*(256+512+64)*256 + 16*actual_common_future_branch_count",
            "base_episode_count": self._base_episodes,
            "base_primitive_team_steps": 256 * self._base_episodes,
            "actual_common_future_branch_count": self._branches,
            "actual_common_future_steps": 16 * self._branches,
            "expected_common_future_branch_count": self._expected_branches,
            "branch_count_matches_scan": self._branches == self._expected_branches,
            "actual_total_steps": self.actual_total_steps,
            "ceiling": MAX_PRIMITIVE_TEAM_STEPS,
            "within_ceiling": True,
            "workers": 1,
            "threads_per_worker": 1,
            "wall_seconds": time.monotonic() - self._started,
            "peak_rss_bytes": self._peak,
        }


def _pilot_tapes(slot: int, split: Split, count: int, first: int) -> tuple[object, ...]:
    return build_balanced_tapes(
        replicate=slot,
        split=split,
        regime="K8",
        count=count,
        first_episode_index=first,
        rng_namespace=PILOT_CONFIG.rng_namespace,
    )


def scan_pilot_histories() -> tuple[BoundaryScanRow, ...]:
    """Scan only the independent pilot namespace without constructing Torch models."""

    rows: list[BoundaryScanRow] = []
    for slot in PILOT_SLOTS:
        for tape in _pilot_tapes(slot, Split.TRAIN, 512, 320):
            rows.append(scan_common_history_boundary(tape, replicate=slot, split=Split.TRAIN))
        for tape in _pilot_tapes(slot, Split.EVALUATION, 64, 832):
            rows.append(
                scan_common_history_boundary(tape, replicate=slot, split=Split.EVALUATION)
            )
    return tuple(rows)


def _configure_one_worker_one_thread() -> None:
    if CPU_WORKERS != 1:
        raise ResourceLimitExceeded("pilot registration requires exactly one worker")
    thread_variables = (
        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
    )
    if any(os.environ.get(variable) != "1" for variable in thread_variables):
        raise ResourceLimitExceeded(
            "pilot worker was not born with every BLAS/OpenMP thread limit equal to one"
        )
    import torch

    if os.environ.get("CUDA_VISIBLE_DEVICES") != "" or torch.cuda.is_available():
        raise ResourceLimitExceeded("pilot worker must make every GPU unavailable")
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        if torch.get_num_interop_threads() != 1:
            raise ResourceLimitExceeded("pilot could not bind one Torch interop thread")
    if torch.get_num_threads() != 1 or torch.get_num_interop_threads() != 1:
        raise ResourceLimitExceeded("pilot Torch runtime is not one-worker/one-thread")


def _raw_dataset(rows: tuple[object, ...]) -> object:
    from .packets import PacketDataset, raw_packet

    typed_rows = tuple(rows)
    return PacketDataset(
        tuple(row.key.text for row in typed_rows),
        np.stack([raw_packet(row.target, row.mean, row.cholesky) for row in typed_rows]),
    )


def _supported_cell_keys(scan: Mapping[str, object]) -> frozenset[tuple[object, ...]]:
    cells = scan.get("supported_cells")
    if not isinstance(cells, list):
        raise ValueError("pilot scan lacks supported-cell bindings")
    result: set[tuple[object, ...]] = set()
    for cell in cells:
        if not isinstance(cell, Mapping):
            raise ValueError("pilot supported-cell entry is malformed")
        result.add((
            cell.get("slot"), cell.get("split"), cell.get("regime"),
            cell.get("elapsed_horizon"), cell.get("cost"),
        ))
    return frozenset(result)


def retain_pilot_supported_rows(
    rows: Sequence[PanelRow],
    supported_cells: frozenset[tuple[object, ...]],
) -> tuple[PanelRow, ...]:
    """Exclude every row outside the prospectively supported slot/cell set."""

    return tuple(
        row for row in rows
        if (row.key.replicate, *row.derangement_cell) in supported_cells
    )


def _actual_support_failures(
    slot: int,
    retained_rows: Sequence[PanelRow],
    supported_rows: Sequence[PanelRow],
    split: Split,
) -> list[str]:
    denominator = len(retained_rows)
    count = len(supported_rows)
    failures: list[str] = []
    if denominator == 0 or count < math.ceil(0.80 * denominator):
        failures.append(
            f"pilot slot {slot} {split.value} actual supported-cell rows "
            f"{count}/{denominator} (<80%)"
        )
    if split is Split.EVALUATION and denominator < 48:
        failures.append(f"pilot slot {slot} actual K8 retained {denominator}/64 (<48)")
    return failures


def pilot_material_stratum_support(
    slot: int,
    evaluation_rows: Sequence[PanelRow],
) -> tuple[tuple[int, int], list[str]]:
    """Check both G16-defined material tails before any RAW gate exists."""

    counts = {stratum: 0 for stratum in MATERIAL_STRATA}
    failures: list[str] = []
    for row in evaluation_rows:
        legal_replacements = row.g16[1:][row.legal_mask[1:]]
        if legal_replacements.size == 0:
            failures.append(f"pilot slot {slot} K8 row lacks a legal replacement")
            continue
        advantage = float(np.max(legal_replacements) - row.g16[0])
        if advantage <= -MATERIAL_ADVANTAGE_THRESHOLD:
            counts[MATERIAL_STRATA[0]] += 1
        elif advantage >= MATERIAL_ADVANTAGE_THRESHOLD:
            counts[MATERIAL_STRATA[1]] += 1
    for stratum in MATERIAL_STRATA:
        if counts[stratum] < MINIMUM_K8_ROWS_PER_MATERIAL_STRATUM:
            failures.append(
                f"pilot slot {slot} K8/{stratum} has {counts[stratum]} rows "
                f"(<{MINIMUM_K8_ROWS_PER_MATERIAL_STRATUM}) before RAW"
            )
    return tuple(counts[stratum] for stratum in MATERIAL_STRATA), failures


def pilot_material_stratum_support_failures(
    slot: int,
    evaluation_rows: Sequence[PanelRow],
) -> list[str]:
    """Compatibility view over the durable material-support counter."""

    return pilot_material_stratum_support(slot, evaluation_rows)[1]


@dataclass(frozen=True)
class PilotSlotMaterialization:
    slot: int
    training_rows: tuple[PanelRow, ...]
    evaluation_rows: tuple[PanelRow, ...]
    material_support_counts: tuple[int, int] = (0, 0)


def _materialize_slot(
    slot: int,
    ledger: PilotWorkLedger,
    supported_cells: frozenset[tuple[object, ...]],
) -> tuple[PilotSlotMaterialization, tuple[str, ...]]:
    from .training import fit_fresh_predictor

    predictor_tapes = (
        build_balanced_tapes(
            replicate=slot, split=Split.PREDICTOR_FIT, regime="K4", count=128,
            first_episode_index=0, rng_namespace=PILOT_CONFIG.rng_namespace,
        )
        + build_balanced_tapes(
            replicate=slot, split=Split.PREDICTOR_FIT, regime="K8", count=128,
            first_episode_index=128, rng_namespace=PILOT_CONFIG.rng_namespace,
        )
    )
    examples = materialize_predictor_examples(predictor_tapes)
    ledger.record_base_episodes(256)
    predictor, _audit = fit_fresh_predictor(
        examples,
        replicate=slot,
        rng_namespace=PILOT_CONFIG.rng_namespace,
        resource_monitor=ledger.check_limits,
    )

    training_rows = []
    for tape in _pilot_tapes(slot, Split.TRAIN, 512, 320):
        observables = materialize_episode_observables(
            tape,
            replicate=slot,
            split=Split.TRAIN,
            forecast=predictor.packet_forecast,
            collect_common_history=True,
            ledger=ledger,
        )
        ledger.record_base_episodes(1)
        if observables.common_history_row is not None:
            training_rows.append(observables.common_history_row)

    evaluation_rows = []
    for tape in _pilot_tapes(slot, Split.EVALUATION, 64, 832):
        observables = materialize_episode_observables(
            tape,
            replicate=slot,
            split=Split.EVALUATION,
            forecast=predictor.packet_forecast,
            collect_common_history=True,
            ledger=ledger,
        )
        ledger.record_base_episodes(1)
        if observables.common_history_row is not None:
            evaluation_rows.append(observables.common_history_row)
    retained_train = tuple(sorted(training_rows, key=lambda row: row.key.canonical))
    retained_evaluation = tuple(sorted(evaluation_rows, key=lambda row: row.key.canonical))
    train_tuple = retain_pilot_supported_rows(retained_train, supported_cells)
    evaluation_tuple = retain_pilot_supported_rows(retained_evaluation, supported_cells)
    material_counts, material_failures = pilot_material_stratum_support(
        slot, evaluation_tuple,
    )
    support_failures = (
        _actual_support_failures(slot, retained_train, train_tuple, Split.TRAIN)
        + _actual_support_failures(
            slot, retained_evaluation, evaluation_tuple, Split.EVALUATION,
        )
        + material_failures
    )
    return PilotSlotMaterialization(
        slot=slot,
        training_rows=train_tuple,
        evaluation_rows=evaluation_tuple,
        material_support_counts=material_counts,
    ), tuple(support_failures)


def _train_evaluate_slot(
    state: PilotSlotMaterialization,
    ledger: PilotWorkLedger,
) -> EvaluationSummary:
    from .evaluation import evaluate_checkpoint
    from .training import canonical_example_order, train_one_path

    order = canonical_example_order(
        len(state.training_rows),
        replicate=state.slot,
        updates=PILOT_CONFIG.updates,
        rng_namespace=PILOT_CONFIG.rng_namespace,
    )
    trained = train_one_path(
        state.training_rows,
        _raw_dataset(state.training_rows),
        replicate=state.slot,
        representation=Representation.RAW,
        order=order,
        short_updates=BUDGETS["SHORT"],
        long_updates=PILOT_CONFIG.updates,
        resource_monitor=ledger.check_limits,
        rng_namespace=PILOT_CONFIG.rng_namespace,
        capture_short=False,
    )
    if set(trained.checkpoints) != {Budget.LONG} or set(trained.audits) != {Budget.LONG}:
        raise RuntimeError("pilot must retain only the frozen LONG checkpoint")
    return evaluate_checkpoint(
        trained.checkpoints[Budget.LONG],
        state.evaluation_rows,
        _raw_dataset(state.evaluation_rows),
        representation=Representation.RAW,
        budget=Budget.LONG,
        target_regimes=("K8",),
    )


def execute_pilot_slots_two_phase(
    ledger: PilotWorkLedger,
    supported_cells: frozenset[tuple[object, ...]],
) -> tuple[tuple[EvaluationSummary, ...], tuple[str, ...], tuple[dict[str, object], ...]]:
    """Materialize/support-check both slots before constructing any RAW gate."""

    states: list[PilotSlotMaterialization] = []
    failures: list[str] = []
    for slot in PILOT_SLOTS:
        state, slot_failures = _materialize_slot(slot, ledger, supported_cells)
        states.append(state)
        failures.extend(slot_failures)
    count_records = tuple(
        {
            "slot": state.slot,
            "stratum": stratum,
            "observed": True,
            "row_count": state.material_support_counts[index],
        }
        for state in states
        for index, stratum in enumerate(MATERIAL_STRATA)
    )
    if failures:
        return (), tuple(failures), count_records
    return tuple(_train_evaluate_slot(state, ledger) for state in states), (), count_records


def _summary_record(summary: EvaluationSummary) -> dict[str, object]:
    return {
        "slot": summary.replicate,
        "representation": summary.representation.value,
        "checkpoint": summary.budget.value,
        "regime_mean_regret": dict(summary.regime_mean_regret),
        "row_count_by_regime": dict(summary.row_count_by_regime),
        "material_stratum_count_by_regime": {
            regime: dict(values)
            for regime, values in summary.material_stratum_count_by_regime.items()
        },
        "mean_regret_by_regime_and_material_stratum": {
            regime: dict(values)
            for regime, values in summary.mean_regret_by_regime_and_material_stratum.items()
        },
        "logged_scripted_mean_regret_by_regime_and_material_stratum": {
            regime: dict(values)
            for regime, values
            in summary.logged_scripted_mean_regret_by_regime_and_material_stratum.items()
        },
    }


def _validate_fresh_targets(
    output_root: Path,
    result_path: Path,
    resource_receipt_path: Path,
    launch_resource_receipt_path: Path,
    launch_run_resource_receipt_path: Path,
) -> None:
    paths = tuple(Path(path).resolve() for path in (
        output_root, result_path, resource_receipt_path,
        launch_resource_receipt_path, launch_run_resource_receipt_path,
    ))
    if len(set(paths)) != 5:
        raise ValueError("pilot roots, result, and resource receipts must be distinct")
    if any(path.exists() for path in paths):
        raise FileExistsError("pilot requires fresh create-only targets and receipts")
    output = paths[0]
    if any(output == path or output in path.parents for path in paths[1:]):
        raise ValueError("pilot result and resource receipts must be outside the output root")


def validate_pilot_result(payload: Mapping[str, object]) -> None:
    """Recompute the fixed pilot identity and non-activity claims before publication."""

    if (
        payload.get("format") != "CRTO_RAW_ONLY_DEVELOPMENT_PILOT_V1"
        or payload.get("object_id") != PILOT_CONFIG.object_id
        or payload.get("rng_namespace") != PILOT_CONFIG.rng_namespace
        or payload.get("slots") != [0, 1]
        or payload.get("claim_ceiling") != PILOT_CONFIG.claim_ceiling
        or payload.get("feasibility_only") is not True
        or payload.get("final_namespace") != RNG_NAMESPACE
        or payload.get("final_namespace_untouched") is not True
    ):
        raise ValueError("pilot serialized registration or claim ceiling drifted")
    representations = payload.get("representations")
    if (
        not isinstance(representations, Mapping)
        or representations.get("registered") != ["RAW"]
        or any(value not in ([], ["RAW"]) for value in (
            representations.get("trained"), representations.get("evaluated"),
        ))
    ):
        raise ValueError("pilot serialized a non-RAW representation")
    if payload.get("registered_checkpoint") != "LONG" or payload.get("checkpoints") not in (
        [], ["LONG"],
    ):
        raise ValueError("pilot serialized a selectable or non-LONG checkpoint")
    activity = payload.get("activity")
    if not isinstance(activity, Mapping) or any(
        activity.get(field) != 0
        for field in (
            "true_residual_training", "true_residual_evaluation",
            "deranged_training", "deranged_evaluation", "short_checkpoint_exposed",
            "final_namespace_reads", "final_artifact_reads",
        )
    ):
        raise ValueError("pilot non-RAW, SHORT, or final-namespace activity is nonzero")
    competence = payload.get("competence")
    if not isinstance(competence, Mapping):
        raise ValueError("pilot competence receipt is missing")
    disposition = competence.get("disposition")
    if disposition not in {
        "PILOT_FEASIBLE", "NONIDENTIFYING_PILOT_K8_SUPPORT",
        "PILOT_RAW_LONG_INCOMPETENT",
    }:
        raise ValueError("pilot disposition is outside the frozen three-way law")
    failures = competence.get("failures")
    expected_status = {
        "PILOT_FEASIBLE": "PASS",
        "PILOT_RAW_LONG_INCOMPETENT": "FAIL",
        "NONIDENTIFYING_PILOT_K8_SUPPORT": "NONIDENTIFYING",
    }[str(disposition)]
    if competence.get("status") != expected_status or not isinstance(failures, list):
        raise ValueError("pilot disposition, status, or failure list disagrees")
    if disposition == "PILOT_FEASIBLE" and failures:
        raise ValueError("PILOT_FEASIBLE must have an empty failure list")
    if disposition != "PILOT_FEASIBLE" and not failures:
        raise ValueError("non-PASS pilot disposition requires at least one failure")
    summaries = payload.get("summaries")
    if not isinstance(summaries, list):
        raise ValueError("pilot top-level summaries must be a list")
    material_support = payload.get("material_support_counts")
    expected_material_identities = [
        (slot, stratum) for slot in PILOT_SLOTS for stratum in MATERIAL_STRATA
    ]
    if not isinstance(material_support, list) or [
        (row.get("slot"), row.get("stratum"))
        for row in material_support if isinstance(row, Mapping)
    ] != expected_material_identities:
        raise ValueError("pilot must retain the exact four material-support count identities")
    durable_material_counts: dict[tuple[int, str], int | None] = {}
    durable_material_observed: dict[tuple[int, str], bool] = {}
    for row in material_support:
        assert isinstance(row, Mapping)
        observed = row.get("observed")
        count = row.get("row_count")
        if observed is True:
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                raise ValueError("observed pilot material count must be a nonnegative integer")
        elif observed is False:
            if count is not None:
                raise ValueError("unobserved pilot material count must be null")
        else:
            raise ValueError("pilot material-support observed flag must be boolean")
        key = (int(row["slot"]), str(row["stratum"]))
        durable_material_counts[key] = count
        durable_material_observed[key] = observed
    if (
        any(count is not None and count < MINIMUM_K8_ROWS_PER_MATERIAL_STRATUM
            for count in durable_material_counts.values())
        and disposition != "NONIDENTIFYING_PILOT_K8_SUPPORT"
    ):
        raise ValueError("sub-eight material support requires NONIDENTIFYING disposition")
    cells = competence.get("cells")
    if disposition == "NONIDENTIFYING_PILOT_K8_SUPPORT":
        if (
            cells != []
            or summaries != []
            or representations.get("trained") != []
            or representations.get("evaluated") != []
            or payload.get("checkpoints") != []
            or activity.get("raw_gate_models") != 0
            or activity.get("raw_gate_optimizer_updates") != 0
        ):
            raise ValueError("support-invalid pilot cannot serialize RAW outcomes or activity")
    elif not isinstance(cells, list) or [
        (cell.get("slot"), cell.get("stratum")) for cell in cells if isinstance(cell, Mapping)
    ] != [
        (0, "KEEP_MATERIAL"), (0, "REPLAN_MATERIAL"),
        (1, "KEEP_MATERIAL"), (1, "REPLAN_MATERIAL"),
    ]:
        raise ValueError("pilot must bind the exact four slot-by-stratum cells")
    if disposition in {"PILOT_FEASIBLE", "PILOT_RAW_LONG_INCOMPETENT"}:
        assert isinstance(cells, list)
        if (
            representations.get("trained") != ["RAW"]
            or representations.get("evaluated") != ["RAW"]
            or payload.get("checkpoints") != ["LONG"]
            or activity.get("predictor_models") != 2
            or activity.get("raw_gate_models") != 2
            or activity.get("raw_gate_optimizer_updates") != 2 * PILOT_CONFIG.updates
        ):
            raise ValueError("completed pilot actual RAW/LONG activity is inconsistent")
        if len(summaries) != 2:
            raise ValueError("completed pilot requires exactly two slot summaries")
        expected_cells: list[tuple[int, str, int, float, float]] = []
        for expected_slot, summary in zip(PILOT_SLOTS, summaries):
            if not isinstance(summary, Mapping) or (
                summary.get("slot") != expected_slot
                or summary.get("representation") != "RAW"
                or summary.get("checkpoint") != "LONG"
            ):
                raise ValueError("pilot summaries must be exact slot-ordered RAW/LONG records")
            row_counts = summary.get("row_count_by_regime")
            regime_means = summary.get("regime_mean_regret")
            counts_by_regime = summary.get("material_stratum_count_by_regime")
            raw_by_regime = summary.get("mean_regret_by_regime_and_material_stratum")
            script_by_regime = summary.get(
                "logged_scripted_mean_regret_by_regime_and_material_stratum"
            )
            if (
                not isinstance(row_counts, Mapping)
                or set(row_counts) != {"K8"}
                or not 48 <= int(row_counts.get("K8", 0)) <= 64
                or not isinstance(regime_means, Mapping)
                or set(regime_means) != {"K8"}
                or not np.isfinite(float(regime_means.get("K8", np.nan)))
                or float(regime_means.get("K8", -1.0)) < 0.0
                or not isinstance(counts_by_regime, Mapping)
                or set(counts_by_regime) != {"K8"}
                or not isinstance(raw_by_regime, Mapping)
                or set(raw_by_regime) != {"K8"}
                or not isinstance(script_by_regime, Mapping)
                or set(script_by_regime) != {"K8"}
            ):
                raise ValueError("pilot summary lacks frozen K8 support mappings")
            counts = counts_by_regime.get("K8")
            raw_means = raw_by_regime.get("K8")
            script_means = script_by_regime.get("K8")
            if not all(isinstance(value, Mapping) for value in (counts, raw_means, script_means)):
                raise ValueError("pilot summary lacks K8 material-stratum mappings")
            if any(set(value) != set(MATERIAL_STRATA) for value in (
                counts, raw_means, script_means,
            )):
                raise ValueError("pilot summary material mappings must contain exact K8 strata")
            if sum(int(counts[stratum]) for stratum in MATERIAL_STRATA) > int(
                row_counts["K8"]
            ):
                raise ValueError("pilot material counts exceed the retained K8 row count")
            for stratum in MATERIAL_STRATA:
                try:
                    row_count = int(counts[stratum])
                    raw_mean = float(raw_means[stratum])
                    script_mean = float(script_means[stratum])
                except (KeyError, TypeError, ValueError) as error:
                    raise ValueError("pilot summary material cell is incomplete") from error
                if (
                    row_count < MINIMUM_K8_ROWS_PER_MATERIAL_STRATUM
                    or not np.isfinite(raw_mean)
                    or not np.isfinite(script_mean)
                    or raw_mean < 0.0
                    or script_mean < 0.0
                ):
                    raise ValueError("pilot summary material cell is invalid")
                expected_cells.append((
                    expected_slot, stratum, row_count, raw_mean, script_mean,
                ))
        for cell, expected in zip(cells, expected_cells):
            assert isinstance(cell, Mapping)
            slot, stratum, row_count, raw, script = expected
            if (
                cell.get("slot") != slot
                or cell.get("stratum") != stratum
                or cell.get("row_count") != row_count
                or abs(float(cell.get("raw_mean_regret", np.nan)) - raw) > NUMERIC_TOLERANCE
                or abs(float(cell.get("script_mean_regret", np.nan)) - script)
                > NUMERIC_TOLERANCE
            ):
                raise ValueError("pilot summaries and competence cells disagree")
            if durable_material_counts[(slot, stratum)] != row_count:
                raise ValueError("pilot durable material support disagrees with summaries")
        raw_values: list[float] = []
        for cell in cells:
            assert isinstance(cell, Mapping)
            try:
                raw = float(cell["raw_mean_regret"])
                script = float(cell["script_mean_regret"])
                difference = float(cell["raw_minus_script"])
                ceiling = float(cell["ceiling"])
                row_count = int(cell["row_count"])
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError("pilot competence cell is incomplete") from error
            if (
                not np.isfinite(raw)
                or not np.isfinite(script)
                or raw < 0.0
                or script < 0.0
                or row_count < MINIMUM_K8_ROWS_PER_MATERIAL_STRATUM
                or ceiling != RAW_LONG_MAX_MEAN_REGRET
                or abs(difference - (raw - script)) > NUMERIC_TOLERANCE
            ):
                raise ValueError("pilot competence cell failed independent recomputation")
            raw_values.append(raw)
        any_incompetent = any(
            value > RAW_LONG_MAX_MEAN_REGRET + NUMERIC_TOLERANCE
            for value in raw_values
        )
        if disposition == "PILOT_FEASIBLE" and any_incompetent:
            raise ValueError("PILOT_FEASIBLE contains a RAW regret above 0.01")
        if disposition == "PILOT_RAW_LONG_INCOMPETENT" and not any_incompetent:
            raise ValueError("PILOT_RAW_LONG_INCOMPETENT lacks a RAW regret above 0.01")
    structural = payload.get("structural_scan")
    work = payload.get("work")
    prospective = work.get("prospective") if isinstance(work, Mapping) else None
    actual = work.get("actual") if isinstance(work, Mapping) else None
    if (
        not isinstance(structural, Mapping)
        or structural.get("passed") is not True
        or not isinstance(work, Mapping)
        or work.get("within_ceiling") is not True
        or work.get("formula")
        != "2*(256+512+64)*256 + 16*actual_common_future_branch_count"
        or not isinstance(prospective, Mapping)
        or prospective.get("actual_common_future_branch_count")
        != structural.get("expected_common_future_branch_count")
        or not isinstance(actual, Mapping)
        or actual.get("within_ceiling") is not True
    ):
        raise ValueError("pilot structural scan and exact work receipt disagree")
    availability = structural.get("availability")
    if not isinstance(availability, Mapping) or any(
        count is not None and count > int(availability.get(f"{slot}/K8", -1))
        for slot, stratum in expected_material_identities
        for count in (durable_material_counts[(slot, stratum)],)
    ):
        raise ValueError("pilot material-support count exceeds retained EVALUATION rows")
    if disposition == "NONIDENTIFYING_PILOT_K8_SUPPORT" and structural.get(
        "support_passed"
    ) is False:
        if actual.get("execution_started") is not False:
            raise ValueError("scan-support-invalid pilot must not enter scientific execution")
    elif actual.get("execution_started") is not True:
        raise ValueError("support-admitted pilot lacks an actual execution receipt")
    if actual.get("execution_started") is True:
        if actual.get("base_episode_count") != PILOT_BASE_EPISODE_COUNT:
            raise ValueError("executed pilot base episode count is incomplete")
        if (
            actual.get("actual_common_future_branch_count")
            != prospective.get("actual_common_future_branch_count")
            or actual.get("branch_count_matches_scan") is not True
        ):
            raise ValueError("completed pilot branch work disagrees with prospective scan")
    if actual.get("execution_started") is False and (
        representations.get("trained") != []
        or representations.get("evaluated") != []
        or payload.get("checkpoints") != []
        or any(durable_material_observed.values())
    ):
        raise ValueError("unexecuted support branch claims actual support or RAW/LONG activity")
    if actual.get("execution_started") is True and not all(
        durable_material_observed.values()
    ):
        raise ValueError("executed pilot must observe all four material-support counts")
    expected_predictors = 2 if actual.get("execution_started") is True else 0
    if activity.get("predictor_models") != expected_predictors:
        raise ValueError("pilot predictor activity disagrees with execution state")
    resource = payload.get("resource")
    if not isinstance(resource, Mapping):
        raise ValueError("pilot resource receipt is missing")
    if set(resource) != {
        "prescan_memory", "launch_memory", "launch_assess_run",
    }:
        raise ValueError("pilot must bind the pre-scan memory and post-scan launch pair")
    prescan_memory = resource.get("prescan_memory")
    launch_memory = resource.get("launch_memory")
    launch_assessment = resource.get("launch_assess_run")
    if (
        not isinstance(prescan_memory, Mapping)
        or validate_resource_receipt(prescan_memory)
        or not isinstance(launch_memory, Mapping)
        or validate_resource_receipt(launch_memory)
        or not isinstance(launch_assessment, Mapping)
        or validate_run_resource_receipt(launch_assessment)
    ):
        raise ValueError("pilot resource or one-worker/one-thread admission is invalid")


def publish_pilot_result_create_only(
    stage_root: Path,
    output_root: Path,
    result_path: Path,
    payload: Mapping[str, object],
    *,
    limit_check: Callable[[], None] | None = None,
) -> None:
    """Publish the staged root and external result or expose neither target."""

    stage = Path(stage_root).resolve()
    output = Path(output_root).resolve()
    result = Path(result_path).resolve()
    if not stage.is_dir() or output.exists() or result.exists():
        raise FileExistsError("pilot dual-target publication requires fresh public targets")
    if stage.parent != output.parent:
        raise ValueError("pilot stage root must be a sibling of the public output root")
    result.parent.mkdir(parents=True, exist_ok=True)
    result_stage_dir = Path(tempfile.mkdtemp(
        prefix=f".{result.name}.pilot-stage-", dir=result.parent,
    ))
    staged_result = result_stage_dir / "result.json"
    moved_output = False
    monitor = limit_check or (lambda: None)
    try:
        monitor()
        atomic_create_json(staged_result, payload)
        monitor()
        if output.exists() or result.exists():
            raise FileExistsError("pilot public target appeared during create-only publication")
        monitor()
        os.rename(stage, output)
        moved_output = True
        try:
            monitor()
            os.rename(staged_result, result)
        except BaseException:
            os.rename(output, stage)
            moved_output = False
            raise
    finally:
        if staged_result.exists():
            staged_result.unlink()
        if result_stage_dir.exists():
            result_stage_dir.rmdir()
        if moved_output and not result.exists():
            # Defensive rollback if an unexpected exception occurred after the first rename.
            os.rename(output, stage)


def _run_raw_only_pilot_worker(
    *,
    output_root: Path,
    result_path: Path,
    resource_receipt_path: Path,
    launch_resource_receipt_path: Path,
    launch_run_resource_receipt_path: Path,
) -> Mapping[str, object]:
    """Execute inside the isolated, pre-thread-limited pilot worker."""

    PILOT_CONFIG.validate()
    if os.environ.get("HMASD_CRTO_PILOT_WORKER") != PILOT_CONFIG.object_id:
        raise PermissionError("pilot scientific work requires the isolated launcher worker")
    output = Path(output_root).resolve()
    result = Path(result_path).resolve()
    memory_path = Path(resource_receipt_path).resolve()
    launch_memory_path = Path(launch_resource_receipt_path).resolve()
    launch_assess_path = Path(launch_run_resource_receipt_path).resolve()
    _validate_fresh_targets(
        output, result, memory_path, launch_memory_path, launch_assess_path,
    )

    # The first fresh memory receipt precedes every pilot address, RNG stream, or tape.
    prescan_memory = create_shared_resource_receipt(memory_path)
    scan = assess_pilot_structural_scan(scan_pilot_histories())
    if scan["passed"] is not True:
        raise PermissionError("pilot result-blind structural scan failed: " + "; ".join(scan["issues"]))

    # The second fresh pair occurs after scan and immediately before runtime/model admission.
    launch_memory = create_shared_resource_receipt(launch_memory_path)
    launch_run_resource = create_shared_run_assessment(
        launch_assess_path, run_id=PILOT_CONFIG.launch_run_id,
    )
    _configure_one_worker_one_thread()

    output.parent.mkdir(parents=True, exist_ok=True)
    result.parent.mkdir(parents=True, exist_ok=True)
    stage_root = Path(tempfile.mkdtemp(prefix=f".{output.name}.pilot-stage-", dir=output.parent))
    try:
        expected_branches = int(scan["expected_common_future_branch_count"])
        ledger = PilotWorkLedger(expected_common_future_branches=expected_branches)
        summaries: tuple[EvaluationSummary, ...] = ()
        completed_summaries: tuple[EvaluationSummary, ...] = ()
        material_support_counts: tuple[dict[str, object], ...] = ()
        execution_failures: list[str] = []
        actual_work: dict[str, object]
        if scan["support_passed"] is True:
            supported_cells = _supported_cell_keys(scan)
            completed_summaries, slot_failures, material_support_counts = (
                execute_pilot_slots_two_phase(
                ledger, supported_cells,
                )
            )
            execution_failures.extend(slot_failures)
            summaries, competence = route_pilot_execution_evidence(
                completed_summaries, execution_failures,
            )
            actual_work = ledger.receipt(require_exact_branches=True)
            actual_work["execution_started"] = True
        else:
            material_support_counts = tuple(
                {"slot": slot, "stratum": stratum, "observed": False, "row_count": None}
                for slot in PILOT_SLOTS for stratum in MATERIAL_STRATA
            )
            competence = {
                "status": "NONIDENTIFYING",
                "disposition": "NONIDENTIFYING_PILOT_K8_SUPPORT",
                "failures": list(scan["support_failures"]),
                "cells": [],
                "claim_ceiling": PILOT_CONFIG.claim_ceiling,
                "feasibility_only": True,
            }
            actual_work = {
                "execution_started": False,
                "base_episode_count": 0,
                "base_primitive_team_steps": 0,
                "actual_common_future_branch_count": 0,
                "actual_common_future_steps": 0,
                "actual_total_steps": 0,
                "within_ceiling": True,
            }
        work = {
        "formula": "2*(256+512+64)*256 + 16*actual_common_future_branch_count",
        "prospective": dict(scan["work"]),
        "actual": actual_work,
        "within_ceiling": actual_work["within_ceiling"] is True,
    }
        actual_raw = ["RAW"] if completed_summaries else []
        actual_checkpoints = ["LONG"] if completed_summaries else []
        payload = {
        "format": "CRTO_RAW_ONLY_DEVELOPMENT_PILOT_V1",
        "object_id": PILOT_CONFIG.object_id,
        "rng_namespace": PILOT_CONFIG.rng_namespace,
        "slots": list(PILOT_CONFIG.slots),
        "claim_ceiling": PILOT_CONFIG.claim_ceiling,
        "feasibility_only": True,
        "final_namespace": RNG_NAMESPACE,
        "final_namespace_untouched": True,
        "representations": {
            "registered": ["RAW"],
            "trained": actual_raw,
            "evaluated": actual_raw,
        },
        "registered_checkpoint": "LONG",
        "checkpoints": actual_checkpoints,
        "competence": competence,
        "material_support_counts": list(material_support_counts),
        "summaries": [_summary_record(summary) for summary in summaries],
        "structural_scan": scan,
        "resource": {
            "prescan_memory": dict(prescan_memory),
            "launch_memory": dict(launch_memory),
            "launch_assess_run": dict(launch_run_resource),
        },
        "work": work,
        "activity": {
            "predictor_models": 0 if scan["support_passed"] is not True else 2,
            "raw_gate_models": len(completed_summaries),
            "raw_gate_optimizer_updates": len(completed_summaries) * PILOT_CONFIG.updates,
            "true_residual_training": 0,
            "true_residual_evaluation": 0,
            "deranged_training": 0,
            "deranged_evaluation": 0,
            "short_checkpoint_exposed": 0,
            "final_namespace_reads": 0,
            "final_artifact_reads": 0,
        },
        }
        validate_pilot_result(payload)
        ledger.check_limits()
        atomic_create_json(stage_root / "pilot_receipt.json", payload)
        ledger.check_limits()
        publish_pilot_result_create_only(
            stage_root, output, result, payload, limit_check=ledger.check_limits,
        )
        stage_root = None
        return payload
    finally:
        if stage_root is not None and stage_root.exists():
            shutil.rmtree(stage_root)


def run_raw_only_pilot(
    *,
    output_root: Path,
    result_path: Path,
    resource_receipt_path: Path,
    launch_resource_receipt_path: Path,
    launch_run_resource_receipt_path: Path,
) -> Mapping[str, object]:
    """Launch exactly one fresh worker with all thread pools fixed before import."""

    output = Path(output_root).resolve()
    result = Path(result_path).resolve()
    memory_path = Path(resource_receipt_path).resolve()
    launch_memory_path = Path(launch_resource_receipt_path).resolve()
    launch_assess_path = Path(launch_run_resource_receipt_path).resolve()
    _validate_fresh_targets(
        output, result, memory_path, launch_memory_path, launch_assess_path,
    )
    environment = dict(os.environ)
    for variable in (
        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
    ):
        environment[variable] = "1"
    environment["CUDA_VISIBLE_DEVICES"] = ""
    environment["HMASD_CRTO_PILOT_WORKER"] = PILOT_CONFIG.object_id
    completed = subprocess.run(
        [
            sys.executable, "-m",
            "experiments.candidates."
            "commitment_residual_triggered_options_common_history_gate_r01.pilot",
            "--worker",
            "--output-root", str(output),
            "--result", str(result),
            "--resource-receipt", str(memory_path),
            "--launch-resource-receipt", str(launch_memory_path),
            "--launch-run-resource-receipt", str(launch_assess_path),
        ],
        cwd=Path(__file__).resolve().parents[3],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "isolated CRTO pilot worker failed: "
            + (completed.stderr.strip() or completed.stdout.strip() or str(completed.returncode))
        )
    try:
        payload = json.loads(result.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("pilot worker did not publish a readable result") from error
    if not isinstance(payload, Mapping):
        raise RuntimeError("pilot worker result must be a JSON object")
    validate_pilot_result(payload)
    return payload


def _worker_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--worker", action="store_true", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--resource-receipt", type=Path, required=True)
    parser.add_argument("--launch-resource-receipt", type=Path, required=True)
    parser.add_argument("--launch-run-resource-receipt", type=Path, required=True)
    arguments = parser.parse_args(argv)
    _run_raw_only_pilot_worker(
        output_root=arguments.output_root,
        result_path=arguments.result,
        resource_receipt_path=arguments.resource_receipt,
        launch_resource_receipt_path=arguments.launch_resource_receipt,
        launch_run_resource_receipt_path=arguments.launch_run_resource_receipt,
    )
    return 0


__all__ = [
    "PILOT_CONFIG",
    "PilotConfig",
    "assess_pilot_competence",
    "assess_pilot_structural_scan",
    "run_raw_only_pilot",
    "retain_pilot_supported_rows",
    "publish_pilot_result_create_only",
    "route_pilot_execution_evidence",
    "execute_pilot_slots_two_phase",
    "pilot_material_stratum_support_failures",
    "scan_pilot_histories",
    "validate_pilot_result",
]


if __name__ == "__main__":  # pragma: no cover - isolated scientific worker
    raise SystemExit(_worker_main())
