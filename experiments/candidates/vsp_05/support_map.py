"""Frozen candidate-independent VSP-05 support map on the real event runtime.

The probe changes only candidate-local clean-process dynamics and receipt
geometry.  It executes the supplied executor and variable-roster lifecycle
core without a learner, optimizer, veto, search, or adaptive cell selection.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from experiments.candidates.vsp_05.real_toy_semantic_veto import (
    CANDIDATE_ID,
    DET_ARM,
    proposed_successor,
)
from experiments.candidates.vsp_05.semantic_veto_policy import ReceiptClassification
from ha_ctse_process.collectors import SyncEnvCollector
from ha_ctse_process.dynamic_roster_clean_process_testbed import (
    CleanProcessDynamicRosterEnv,
    CleanProcessDynamicRosterEventEnv,
    make_clean_process_dynamic_roster_ledger,
)
from ha_ctse_process.dynamic_roster_supplied_executor import (
    ORACLE_ARM,
    SuppliedExecutorVectorRuntime,
    SuppliedSkillExecutor,
    make_model_owner,
)
from ha_ctse_process.dynamic_roster_testbed import (
    ACTION_COUNT,
    HORIZON,
)
from ha_ctse_process.dynamic_roster_clean_process_testbed import PROCESS_ACTION_FORCE
from ha_ctse_process.variable_roster_event import (
    JOIN,
    REJOIN,
    TEMPORARY_LEAVE,
    TERMINAL_LEAVE,
    VariableRosterEventCore,
)
from ha_ctse_process.variable_roster_event_types import MembershipTransaction


TREATMENT_ID = "VSP05-B0-SUPPORT-MAP"
FULL_TASK_SEEDS = (68101, 68102, 68103)
SMOKE_TASK_SEEDS = (68101,)
FULL_EPISODES_PER_SEED_CELL = 24
SMOKE_EPISODES_PER_SEED_CELL = 1
EPISODE_NAMESPACE_BASE = 20_000_000
CELL_NAMESPACE_STRIDE = 100_000
SEED_NAMESPACE_STRIDE = 1_000
OPPORTUNITY_CATEGORIES = (JOIN, REJOIN, "SURVIVOR")
PROPOSED_SKILLS = (0, 1, 2)
MEMBERSHIP_KINDS = (JOIN, TEMPORARY_LEAVE, TERMINAL_LEAVE, REJOIN)


@dataclass(frozen=True)
class SupportCell:
    name: str
    damping: float
    drive: float
    step: float
    hard_position: float
    truth_position: float
    hard_velocity: float
    truth_velocity: float

    def __post_init__(self) -> None:
        values = (
            self.damping,
            self.drive,
            self.step,
            self.hard_position,
            self.truth_position,
            self.hard_velocity,
            self.truth_velocity,
        )
        if not all(np.isfinite(float(value)) for value in values):
            raise ValueError("support-map cell values must be finite")
        if not float(self.truth_position) > float(self.hard_position) > 0.0:
            raise ValueError("position thresholds require truth > hard > 0")
        if not 0.0 < float(self.truth_velocity) < float(self.hard_velocity):
            raise ValueError("velocity thresholds require 0 < truth < hard")

    def dynamics(self) -> tuple[float, float, float]:
        return (float(self.damping), float(self.drive), float(self.step))

    def geometry(self) -> tuple[float, float, float, float]:
        return (
            float(self.hard_position),
            float(self.truth_position),
            float(self.hard_velocity),
            float(self.truth_velocity),
        )


REFERENCE_DYNAMICS = (0.75, 0.25, 0.125)
REFERENCE_GEOMETRY = (0.125, 0.25, 0.25, 0.0625)
CELLS = (
    SupportCell("REFERENCE", *REFERENCE_DYNAMICS, *REFERENCE_GEOMETRY),
    SupportCell(
        "THRESHOLD_MID",
        *REFERENCE_DYNAMICS,
        0.125,
        0.1875,
        0.25,
        0.125,
    ),
    SupportCell(
        "THRESHOLD_NEAR_GATE",
        *REFERENCE_DYNAMICS,
        0.125,
        0.15625,
        0.25,
        0.1875,
    ),
    SupportCell("DRIVE_HIGH", 0.75, 0.375, 0.125, *REFERENCE_GEOMETRY),
    SupportCell("STEP_HIGH", 0.75, 0.25, 0.1875, *REFERENCE_GEOMETRY),
    SupportCell("DRIVE_STEP_HIGH", 0.75, 0.375, 0.1875, *REFERENCE_GEOMETRY),
)


@dataclass(frozen=True)
class SupportMapConfig:
    name: str
    task_seeds: tuple[int, ...]
    episodes_per_seed_cell: int
    horizon: int = HORIZON

    def __post_init__(self) -> None:
        if not self.task_seeds or len(set(self.task_seeds)) != len(self.task_seeds):
            raise ValueError("support-map task seeds must be nonempty and distinct")
        if self.episodes_per_seed_cell <= 0 or self.horizon != HORIZON:
            raise ValueError("support-map episodes must be positive at the real horizon")

    def counts(self) -> dict[str, int]:
        episodes = len(CELLS) * len(self.task_seeds) * self.episodes_per_seed_cell
        return {
            "cells": len(CELLS),
            "task_seeds": len(self.task_seeds),
            "episodes": episodes,
            "environment_transitions": episodes * self.horizon,
        }


FULL_CONFIG = SupportMapConfig(
    "full", FULL_TASK_SEEDS, FULL_EPISODES_PER_SEED_CELL
)
SMOKE_CONFIG = SupportMapConfig(
    "smoke", SMOKE_TASK_SEEDS, SMOKE_EPISODES_PER_SEED_CELL
)


def episode_id(cell_index: int, seed_index: int, episode_index: int) -> int:
    cell_value = int(cell_index)
    seed_value = int(seed_index)
    episode_value = int(episode_index)
    if not 0 <= cell_value < len(CELLS):
        raise ValueError("cell index lies outside the frozen table")
    if not 0 <= seed_value < len(FULL_TASK_SEEDS):
        raise ValueError("seed index lies outside the frozen full seed block")
    if not 0 <= episode_value < FULL_EPISODES_PER_SEED_CELL:
        raise ValueError("episode index lies outside the frozen full cap")
    return (
        EPISODE_NAMESPACE_BASE
        + cell_value * CELL_NAMESPACE_STRIDE
        + seed_value * SEED_NAMESPACE_STRIDE
        + episode_value
    )


def build_episode_roster(config: SupportMapConfig) -> tuple[dict[str, int | str], ...]:
    """Freeze the complete cell/seed/episode roster before runtime results exist."""

    seed_indices = {seed: FULL_TASK_SEEDS.index(seed) for seed in config.task_seeds}
    return tuple(
        {
            "cell": cell.name,
            "cell_index": cell_index,
            "task_seed": int(seed),
            "seed_index": seed_indices[seed],
            "episode_index": episode_index,
            "episode_id": episode_id(cell_index, seed_indices[seed], episode_index),
        }
        for cell_index, cell in enumerate(CELLS)
        for seed in config.task_seeds
        for episode_index in range(config.episodes_per_seed_cell)
    )


def classify_support_receipt(
    cell: SupportCell,
    proposed_skill: int,
    position: float,
    velocity: float,
) -> ReceiptClassification:
    """Apply one cell's symmetric inclusive gate and stricter truth geometry."""

    proposed = int(proposed_skill)
    if isinstance(proposed_skill, (bool, np.bool_)) or proposed not in PROPOSED_SKILLS:
        raise ValueError("proposed skill must lie in {0,1,2}")
    position_value = float(position)
    velocity_value = float(velocity)
    if not np.isfinite(position_value) or not np.isfinite(velocity_value):
        raise ValueError("receipt state must be finite")
    if proposed == 0:
        gate = position_value <= -cell.hard_position
        truth = position_value <= -cell.truth_position
    elif proposed == 2:
        gate = position_value >= cell.hard_position
        truth = position_value >= cell.truth_position
    else:
        gate = abs(velocity_value) <= cell.hard_velocity
        truth = abs(velocity_value) <= cell.truth_velocity
    return ReceiptClassification(
        gate=bool(gate),
        truth=bool(truth),
        label=(0 if truth else 1) if gate else None,
    )


class CellCleanProcessDynamicRosterEnv(CleanProcessDynamicRosterEnv):
    """Clean process with only the requested velocity/position update changed."""

    def __init__(self, ledger, *, cell: SupportCell):
        super().__init__(ledger)
        self.support_cell = cell

    def _advance_process(self, key: int, action: int) -> None:
        if int(action) < 0 or int(action) >= ACTION_COUNT:
            raise ValueError("clean-process action lies outside primitive support")
        position, velocity = self.process_states[int(key)]
        velocity = (
            self.support_cell.damping * float(velocity)
            + self.support_cell.drive * float(PROCESS_ACTION_FORCE[int(action)])
        )
        position = float(
            np.clip(position + self.support_cell.step * velocity, -1.0, 1.0)
        )
        self.process_states[int(key)] = np.asarray(
            (position, velocity), dtype=np.float64
        )


class CellCleanProcessDynamicRosterEventEnv(CleanProcessDynamicRosterEventEnv):
    """Real clean-process adapter rebound to one frozen support-map cell."""

    def __init__(self, *, task_master_seed: int, cell: SupportCell):
        super().__init__(task_master_seed=task_master_seed)
        self.support_cell = cell

    def reset_event_runtime(self, episode_id_value: int):
        self.episode_id = int(episode_id_value)
        self.environment = CellCleanProcessDynamicRosterEnv(
            make_clean_process_dynamic_roster_ledger(
                self.episode_id, master_seed=self.task_master_seed
            ),
            cell=self.support_cell,
        )
        return self.environment.event_transaction()


def _empty_bucket() -> dict[str, Any]:
    return {
        "frontier_opportunities": 0,
        "different_successor_opportunities": 0,
        "gated": 0,
        "strict_truth": 0,
        "alias": 0,
        "unresolved": 0,
        "gated_position_min": None,
        "gated_position_max": None,
        "gated_velocity_min": None,
        "gated_velocity_max": None,
        "active_skills": set(),
        "proposed_skills": set(),
        "event_ranks": set(),
    }


def _update_range(bucket: dict[str, Any], prefix: str, value: float) -> None:
    low_key = f"{prefix}_min"
    high_key = f"{prefix}_max"
    bucket[low_key] = value if bucket[low_key] is None else min(bucket[low_key], value)
    bucket[high_key] = value if bucket[high_key] is None else max(bucket[high_key], value)


def _category(transaction: MembershipTransaction, key: str) -> str:
    delta_kind = next(
        (
            delta.kind
            for delta in transaction.atomic_membership_delta
            if delta.lifecycle_key == key
        ),
        None,
    )
    if delta_kind in (JOIN, REJOIN):
        return str(delta_kind)
    return "SURVIVOR"


class SupportMapVectorRuntime(SuppliedExecutorVectorRuntime):
    """Candidate-local counting adapter over the real supplied-executor runtime."""

    @classmethod
    def create_cell(
        cls,
        *,
        cell: SupportCell,
        episode_ids: Sequence[int],
        task_seed: int,
    ) -> "SupportMapVectorRuntime":
        ids = tuple(int(value) for value in episode_ids)
        runtime = cls.create(
            arm=ORACLE_ARM,
            model_owner=make_model_owner("cpu"),
            episode_ids=ids,
            task_seed=int(task_seed),
            deterministic_high=True,
        )
        # Rebind the real adapter before the first transition.  The already
        # constructed cores retain the exact registered executor/runtime path.
        runtime.collector.close()
        runtime.collector = SyncEnvCollector(
            [
                CellCleanProcessDynamicRosterEventEnv(
                    task_master_seed=int(task_seed), cell=cell
                )
                for _ in ids
            ]
        )
        runtime.current_transactions = list(
            runtime.collector.reset_event_runtime(ids)
        )
        runtime._bind_current_state()
        runtime.support_cell = cell
        runtime.per_environment_buckets = [
            {
                (proposed, category): _empty_bucket()
                for proposed in PROPOSED_SKILLS
                for category in OPPORTUNITY_CATEGORIES
            }
            for _ in ids
        ]
        runtime.per_environment_membership = [Counter() for _ in ids]
        runtime.per_environment_event_ranks = [Counter() for _ in ids]
        runtime.proposal_policy_calls = 0
        runtime.environment_transition_calls = 0
        runtime.supplied_executor_calls = 0
        runtime.lifecycle_transaction_calls = 0
        if not isinstance(runtime.executor, SuppliedSkillExecutor):
            raise RuntimeError("support map lost the supplied executor")
        if not all(
            isinstance(adapter, CellCleanProcessDynamicRosterEventEnv)
            for adapter in runtime.collector.envs
        ) or not all(
            isinstance(core, VariableRosterEventCore) for core in runtime.cores
        ):
            raise RuntimeError("support map lost the real environment/core path")
        return runtime

    def _oracle_teacher_actions(
        self,
        env_index: int,
        transaction: MembershipTransaction,
    ) -> dict[str, int] | None:
        membership = self.per_environment_membership[env_index]
        for delta in transaction.atomic_membership_delta:
            membership[str(delta.kind)] += 1
        frontier = transaction.post_membership_pre_policy_snapshot.frontier
        if not frontier:
            return None
        core = self.cores[env_index]
        adapter = self.collector.envs[env_index]
        process_states = adapter.process_state_mapping(frontier)
        self.oracle_constructive_calls += 1
        selected: dict[str, int] = {}
        ranks = self.per_environment_event_ranks[env_index]
        buckets = self.per_environment_buckets[env_index]
        for key in frontier:
            self.proposal_policy_calls += 1
            ranks[str(key)] += 1
            event_rank = int(ranks[str(key)])
            record = core.records.get(key)
            incumbent = None if record is None else record.active_skill
            position, velocity = np.asarray(
                process_states[key], dtype=np.float64
            ).tolist()
            proposed = proposed_successor(
                position=position,
                velocity=velocity,
                current_skill=None if incumbent is None else int(incumbent),
            )
            category = _category(transaction, key)
            bucket = buckets[(int(proposed), category)]
            bucket["frontier_opportunities"] += 1
            bucket["proposed_skills"].add(int(proposed))
            bucket["event_ranks"].add(event_rank)
            if incumbent is None:
                if category != JOIN or int(proposed) != 2:
                    raise RuntimeError("genuine joins must start at skill 2")
                selected[key] = int(proposed)
                continue
            current = int(incumbent)
            bucket["active_skills"].add(current)
            if int(proposed) == current:
                selected[key] = current
                continue
            bucket["different_successor_opportunities"] += 1
            receipt = classify_support_receipt(
                self.support_cell, int(proposed), position, velocity
            )
            if receipt.gate:
                bucket["gated"] += 1
                bucket["strict_truth" if receipt.truth else "alias"] += 1
                _update_range(bucket, "gated_position", float(position))
                _update_range(bucket, "gated_velocity", float(velocity))
                selected[key] = int(proposed)
            else:
                bucket["unresolved"] += 1
                selected[key] = current
        return selected

    def advance_one(self) -> None:
        super().advance_one()
        completed = len(self.episode_ids)
        self.environment_transition_calls += completed
        self.supplied_executor_calls += completed
        self.lifecycle_transaction_calls += completed


def _merge_bucket(target: dict[str, Any], source: Mapping[str, Any]) -> None:
    for key in (
        "frontier_opportunities",
        "different_successor_opportunities",
        "gated",
        "strict_truth",
        "alias",
        "unresolved",
    ):
        target[key] += int(source[key])
    for prefix in ("gated_position", "gated_velocity"):
        if source[f"{prefix}_min"] is not None:
            _update_range(target, prefix, float(source[f"{prefix}_min"]))
            _update_range(target, prefix, float(source[f"{prefix}_max"]))
    target["active_skills"].update(source["active_skills"])
    target["proposed_skills"].update(source["proposed_skills"])
    target["event_ranks"].update(source["event_ranks"])


def _bucket_payload(
    bucket: Mapping[str, Any],
    *,
    cell: str,
    task_seed: int,
    proposed_skill: int,
    category: str,
) -> dict[str, Any]:
    truth = int(bucket["strict_truth"])
    alias = int(bucket["alias"])
    gated = int(bucket["gated"])
    event_ranks = sorted(int(value) for value in bucket["event_ranks"])
    return {
        "cell": str(cell),
        "task_seed": int(task_seed),
        "proposed_skill": int(proposed_skill),
        "opportunity_lifecycle": str(category),
        "frontier_opportunities": int(bucket["frontier_opportunities"]),
        "different_successor_opportunities": int(
            bucket["different_successor_opportunities"]
        ),
        "gated": gated,
        "strict_truth": truth,
        "alias": alias,
        "unresolved": int(bucket["unresolved"]),
        "class_ratio": {
            "strict_truth": truth,
            "alias": alias,
            "alias_fraction_of_gated": None if gated == 0 else alias / gated,
        },
        "gated_position_range": [
            bucket["gated_position_min"],
            bucket["gated_position_max"],
        ],
        "gated_velocity_range": [
            bucket["gated_velocity_min"],
            bucket["gated_velocity_max"],
        ],
        "active_skill_coverage": sorted(int(v) for v in bucket["active_skills"]),
        "proposed_skill_coverage": sorted(
            int(v) for v in bucket["proposed_skills"]
        ),
        "event_rank_coverage": {
            "minimum": None if not event_ranks else event_ranks[0],
            "maximum": None if not event_ranks else event_ranks[-1],
            "distinct_count": len(event_ranks),
        },
    }


def _support_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    totals = Counter()
    for row in rows:
        for key in (
            "frontier_opportunities",
            "different_successor_opportunities",
            "gated",
            "strict_truth",
            "alias",
            "unresolved",
        ):
            totals[key] += int(row[key])
    return {
        **{key: int(totals[key]) for key in sorted(totals)},
        "two_sided_observed": bool(totals["strict_truth"] and totals["alias"]),
    }


def run_support_map(
    config: SupportMapConfig,
    *,
    code_revision: str,
) -> dict[str, Any]:
    """Execute every frozen cell once over the predeclared real-runtime roster."""

    roster = build_episode_roster(config)
    declared = config.counts()
    aggregate_rows: list[dict[str, Any]] = []
    membership_by_cell_seed: dict[tuple[str, int], Counter[str]] = {}
    call_counts = Counter()
    episode_returns: dict[tuple[str, int], list[float]] = {}
    lifecycle_checks: list[bool] = []

    for cell in CELLS:
        for task_seed in config.task_seeds:
            ids = tuple(
                int(row["episode_id"])
                for row in roster
                if row["cell"] == cell.name and row["task_seed"] == task_seed
            )
            runtime = SupportMapVectorRuntime.create_cell(
                cell=cell, episode_ids=ids, task_seed=task_seed
            )
            try:
                runtime.advance()
                merged = {
                    (proposed, category): _empty_bucket()
                    for proposed in PROPOSED_SKILLS
                    for category in OPPORTUNITY_CATEGORIES
                }
                for environment_buckets in runtime.per_environment_buckets:
                    for key, bucket in environment_buckets.items():
                        _merge_bucket(merged[key], bucket)
                for proposed in PROPOSED_SKILLS:
                    for category in OPPORTUNITY_CATEGORIES:
                        aggregate_rows.append(
                            _bucket_payload(
                                merged[(proposed, category)],
                                cell=cell.name,
                                task_seed=task_seed,
                                proposed_skill=proposed,
                                category=category,
                            )
                        )
                membership_by_cell_seed[(cell.name, task_seed)] = sum(
                    runtime.per_environment_membership, Counter()
                )
                episode_returns[(cell.name, task_seed)] = [
                    float(sum(values)) for values in runtime.reward_trace
                ]
                call_counts["proposal_policy"] += runtime.proposal_policy_calls
                call_counts["environment_transition"] += (
                    runtime.environment_transition_calls
                )
                call_counts["supplied_executor"] += runtime.supplied_executor_calls
                call_counts["variable_roster_event_core_transaction"] += (
                    runtime.lifecycle_transaction_calls
                )
                lifecycle_checks.extend(
                    bool(value)
                    for key, value in runtime.lifecycle_audit.items()
                    if key != "frozen_absent_high"
                )
            finally:
                runtime.close()

    actual = {
        "cells": len({str(row["cell"]) for row in roster}),
        "task_seeds": len({int(row["task_seed"]) for row in roster}),
        "episodes": len(roster),
        "environment_transitions": int(call_counts["environment_transition"]),
    }
    if actual != declared:
        raise RuntimeError(f"support-map counts differ: {actual} != {declared}")
    if call_counts["supplied_executor"] != declared["environment_transitions"]:
        raise RuntimeError("supplied-executor call count drifted")
    if (
        call_counts["variable_roster_event_core_transaction"]
        != declared["environment_transitions"]
    ):
        raise RuntimeError("lifecycle transaction count drifted")
    if not lifecycle_checks or not all(lifecycle_checks):
        raise RuntimeError("real lifecycle invariant audit failed")

    cell_summaries = []
    for cell in CELLS:
        rows = [row for row in aggregate_rows if row["cell"] == cell.name]
        returns = [
            value
            for seed in config.task_seeds
            for value in episode_returns[(cell.name, seed)]
        ]
        cell_summaries.append(
            {
                "cell": cell.name,
                **_support_summary(rows),
                "episodes": len(returns),
                "episode_return_mean": sum(returns) / len(returns),
            }
        )
    seed_summaries = [
        {
            "task_seed": int(seed),
            **_support_summary(
                [row for row in aggregate_rows if row["task_seed"] == seed]
            ),
        }
        for seed in config.task_seeds
    ]
    membership_rows = [
        {
            "cell": cell.name,
            "task_seed": int(seed),
            "counts": {
                kind: int(membership_by_cell_seed[(cell.name, seed)][kind])
                for kind in MEMBERSHIP_KINDS
            },
        }
        for cell in CELLS
        for seed in config.task_seeds
    ]
    config_payload = asdict(config)
    config_payload["task_seeds"] = list(config.task_seeds)
    return {
        "schema_version": 1,
        "stage": "experiment",
        "evidence_level": "A",
        "formal": False,
        "candidate_id": CANDIDATE_ID,
        "treatment_id": TREATMENT_ID,
        "arm": DET_ARM,
        "config_name": config.name,
        "code_revision": str(code_revision),
        "execution_command": (
            "python scripts/run_vsp05_b0_support_map.py "
            f"--config {config.name} --code-revision {code_revision} "
            "--output <explicit-output>"
        ),
        "environment_binding": {
            "environment": (
                "experiments.candidates.vsp_05.support_map."
                "CellCleanProcessDynamicRosterEventEnv"
            ),
            "inherited_real_environment": (
                "ha_ctse_process.dynamic_roster_clean_process_testbed."
                "CleanProcessDynamicRosterEventEnv"
            ),
            "event_core": (
                "ha_ctse_process.variable_roster_event.VariableRosterEventCore"
            ),
            "vector_runtime": (
                "ha_ctse_process.dynamic_roster_supplied_executor."
                "SuppliedExecutorVectorRuntime"
            ),
            "executor": (
                "ha_ctse_process.dynamic_roster_supplied_executor."
                "SuppliedSkillExecutor"
            ),
            "horizon": HORIZON,
        },
        "scientific_disposition": None,
        "c_treatment_licensed": False,
        "all_cells_reported": [row["cell"] for row in cell_summaries]
        == [cell.name for cell in CELLS],
        "claim_boundary": (
            "candidate-independent descriptive support only; no cell selection, "
            "prevalence claim, learner comparison, promotion, retirement, "
            "generalization, utility, or scientific acceptance"
        ),
        "configuration": {
            **config_payload,
            "cells": [
                {
                    "name": cell.name,
                    "dynamics": list(cell.dynamics()),
                    "geometry": list(cell.geometry()),
                }
                for cell in CELLS
            ],
            "episode_namespace": {
                "base": EPISODE_NAMESPACE_BASE,
                "cell_stride": CELL_NAMESPACE_STRIDE,
                "seed_stride": SEED_NAMESPACE_STRIDE,
                "encoding": "base + cell_index*cell_stride + seed_index*seed_stride + episode_index",
                "disjoint_from_b1_zero_based_namespace": True,
            },
            "proposal_rule": (
                "exact B1 proposed_successor(position, velocity, current_skill)"
            ),
            "cell_roster_frozen_before_results": True,
            "K_search": 0,
            "hypothetical_transitions": 0,
        },
        "episode_roster": list(roster),
        "declared_counts": declared,
        "actual_counts": actual,
        "call_counts": {
            "environment_transition": int(call_counts["environment_transition"]),
            "proposal_policy": int(call_counts["proposal_policy"]),
            "supplied_executor": int(call_counts["supplied_executor"]),
            "variable_roster_event_core_transaction": int(
                call_counts["variable_roster_event_core_transaction"]
            ),
            "learner": 0,
            "trainer": 0,
            "optimizer_update": 0,
        },
        "real_calls": {
            "environment": call_counts["environment_transition"] > 0,
            "proposal_policy": call_counts["proposal_policy"] > 0,
            "supplied_executor": call_counts["supplied_executor"] > 0,
            "variable_roster_event_core": (
                call_counts["variable_roster_event_core_transaction"] > 0
            ),
            "learner": False,
            "trainer": False,
        },
        "aggregate_rows": aggregate_rows,
        "cell_summaries": cell_summaries,
        "seed_summaries": seed_summaries,
        "membership_event_coverage": membership_rows,
        "two_sided_observed": {
            "descriptive_only": True,
            "by_cell": {
                row["cell"]: bool(row["two_sided_observed"])
                for row in cell_summaries
            },
        },
        "exclusions": {
            "learner_training": True,
            "learned_veto": True,
            "reject_threshold_tuning": True,
            "adaptive_cell_search": True,
            "cell_selection": True,
            "b1_learner_comparison": True,
            "c_treatment": True,
            "external_pro": True,
            "queued_eociv_b5_decision_change": True,
        },
        "updates": 0,
        "trainer_calls": 0,
        "learner_calls": 0,
        "K_search": 0,
        "hypothetical_transitions": 0,
    }


def write_result(path: str | Path, result: Mapping[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(dict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", choices=("smoke", "full"), required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--code-revision", default="WORKTREE")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    config = SMOKE_CONFIG if args.config == "smoke" else FULL_CONFIG
    result = run_support_map(config, code_revision=args.code_revision)
    write_result(args.output, result)
    print(
        json.dumps(
            {"output": str(Path(args.output)), "actual_counts": result["actual_counts"]},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
