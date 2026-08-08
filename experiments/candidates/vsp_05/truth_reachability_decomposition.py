"""Nonintervening VSP05-A1 frontier truth-reachability decomposition.

The candidate-local adapter observes the real supplied-executor lifecycle at
the existing post-membership/pre-policy hook.  It never writes core state and
never advances a hypothetical environment.  Every real frontier row retains
the complete simultaneous predicate mask and every static incumbent row is
explicitly marked as nonreachable bookkeeping.
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from itertools import combinations, product
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from experiments.candidates.vsp_05.real_toy_semantic_veto import (
    CANDIDATE_ID,
    DET_ARM,
    proposed_successor,
)
from experiments.candidates.vsp_05.support_map import (
    CELL_NAMESPACE_STRIDE,
    CELLS,
    EPISODE_NAMESPACE_BASE,
    FULL_CONFIG as B0_FULL_CONFIG,
    FULL_TASK_SEEDS,
    MEMBERSHIP_KINDS,
    OPPORTUNITY_CATEGORIES,
    PROPOSED_SKILLS,
    SEED_NAMESPACE_STRIDE,
    SMOKE_CONFIG as B0_SMOKE_CONFIG,
    SupportCell,
    SupportMapConfig,
    SupportMapVectorRuntime,
    _category,
    _update_range,
    build_episode_roster,
    classify_support_receipt,
)
from ha_ctse_process.dynamic_roster_testbed import HORIZON
from ha_ctse_process.variable_roster_event import JOIN, MembershipTransaction


TREATMENT_ID = "VSP05-A1-TRUTH-REACHABILITY-DECOMPOSITION"
SCHEMA_VERSION = 1
FULL_CONFIG = B0_FULL_CONFIG
SMOKE_CONFIG = B0_SMOKE_CONFIG
CAPTURE_BOUNDARY = "POST_MEMBERSHIP_PRE_POLICY"
SKILLS = (0, 1, 2)

MASK_FIELDS = (
    "frontier_present",
    "incumbent_present",
    "different_successor",
    "actual_proposal_gate",
    "truth_any_skill",
    "truth_non_incumbent_skill",
    "truth_actual_proposal",
    "eligible_strict_truth",
)

# Gate is retained in MASK_FIELDS, but omitted here deliberately.  Strict truth
# for the actual skill implies its gate, so a failed truth predicate already
# explains a failed gate and the gate must not become a second blocker.
SEMANTIC_MISSING_FIELDS = (
    "frontier_present",
    "incumbent_present",
    "different_successor",
    "truth_any_skill",
    "truth_non_incumbent_skill",
    "truth_actual_proposal",
)


def _mask_code(mask: Mapping[str, bool]) -> int:
    if set(mask) != set(MASK_FIELDS):
        raise ValueError("complete mask fields drifted")
    return sum((1 << index) for index, name in enumerate(MASK_FIELDS) if mask[name])


def semantic_missing_predicates(mask: Mapping[str, bool]) -> tuple[str, ...]:
    """Return all simultaneous semantic failures without predicate ordering."""

    if set(mask) != set(MASK_FIELDS):
        raise ValueError("semantic decomposition requires the complete mask")
    if bool(mask["truth_actual_proposal"]) and not bool(
        mask["actual_proposal_gate"]
    ):
        raise ValueError("strict truth must imply the actual-proposal hard gate")
    missing = tuple(name for name in SEMANTIC_MISSING_FIELDS if not bool(mask[name]))
    expected_eligible = not missing
    if bool(mask["eligible_strict_truth"]) != expected_eligible:
        raise ValueError("eligible strict-truth conjunction drifted from its mask")
    return missing


def semantic_near_miss_class(mask: Mapping[str, bool]) -> str:
    missing = semantic_missing_predicates(mask)
    if not missing:
        return "ELIGIBLE_STRICT_TRUTH"
    return "MISSING:" + "|".join(missing)


def _near_miss_domain() -> tuple[str, ...]:
    values = ["ELIGIBLE_STRICT_TRUTH"]
    for count in range(1, len(SEMANTIC_MISSING_FIELDS) + 1):
        values.extend(
            "MISSING:" + "|".join(fields)
            for fields in combinations(SEMANTIC_MISSING_FIELDS, count)
        )
    return tuple(values)


NEAR_MISS_DOMAIN = _near_miss_domain()


def _truth_set_label(skills: Sequence[int]) -> str:
    normalized = tuple(sorted(int(value) for value in skills))
    if any(value not in SKILLS for value in normalized) or len(normalized) != len(
        set(normalized)
    ):
        raise ValueError("truth-skill set lies outside the frozen skill support")
    return "NONE" if not normalized else "|".join(str(value) for value in normalized)


TRUTH_SET_DOMAIN = tuple(
    _truth_set_label(values)
    for count in range(len(SKILLS) + 1)
    for values in combinations(SKILLS, count)
)


def _episode_index_from_id(
    episode_id: int, *, cell: SupportCell, task_seed: int
) -> int:
    cell_index = CELLS.index(cell)
    seed_index = FULL_TASK_SEEDS.index(int(task_seed))
    value = (
        int(episode_id)
        - EPISODE_NAMESPACE_BASE
        - cell_index * CELL_NAMESPACE_STRIDE
        - seed_index * SEED_NAMESPACE_STRIDE
    )
    if not 0 <= value < B0_FULL_CONFIG.episodes_per_seed_cell:
        raise RuntimeError("A1 episode ID left the frozen B0 namespace")
    return int(value)


def _static_row(
    real_row: Mapping[str, Any], *, cell: SupportCell, hypothetical_incumbent: int
) -> dict[str, Any]:
    incumbent = int(hypothetical_incumbent)
    position = float(real_row["position"])
    velocity = float(real_row["velocity"])
    proposal = proposed_successor(
        position=position, velocity=velocity, current_skill=incumbent
    )
    receipt = classify_support_receipt(cell, proposal, position, velocity)
    return {
        "source_real_frontier_id": str(real_row["real_frontier_id"]),
        "cell": str(real_row["cell"]),
        "task_seed": int(real_row["task_seed"]),
        "episode_id": int(real_row["episode_id"]),
        "environment_step": int(real_row["environment_step"]),
        "lifecycle_key": str(real_row["lifecycle_key"]),
        "event_rank": int(real_row["event_rank"]),
        "position": position,
        "velocity": velocity,
        "hypothetical_incumbent_skill": incumbent,
        "hypothetical_proposal": int(proposal),
        "different_successor": bool(int(proposal) != incumbent),
        "proposal_gate": bool(receipt.gate),
        "proposal_strict_truth": bool(receipt.truth),
        "eligible_if_incumbent": bool(
            int(proposal) != incumbent and bool(receipt.truth)
        ),
        "classification_kind": "STATIC_HYPOTHETICAL_INCUMBENT_COMPATIBILITY",
        "static": True,
        "reachable_evidence": False,
        "hypothetical_environment_transitions": 0,
    }


class TruthReachabilityVectorRuntime(SupportMapVectorRuntime):
    """Read-only A1 capture adapter at the committed pre-policy boundary."""

    @classmethod
    def create_cell(
        cls,
        *,
        cell: SupportCell,
        episode_ids: Sequence[int],
        task_seed: int,
    ) -> "TruthReachabilityVectorRuntime":
        runtime = super().create_cell(
            cell=cell, episode_ids=episode_ids, task_seed=task_seed
        )
        runtime.trace_task_seed = int(task_seed)
        runtime.real_frontier_rows = [[] for _ in runtime.episode_ids]
        runtime.static_compatibility_rows = [[] for _ in runtime.episode_ids]
        runtime._pending_trace_context = [None for _ in runtime.episode_ids]
        runtime.trace_hook_calls = 0
        runtime.static_classification_calls = 0
        for env_index, core in enumerate(runtime.cores):
            core.install_preframe_intervention(
                lambda observed_core, index=env_index: runtime._capture_preframe(
                    index, observed_core
                )
            )
        return runtime

    def _oracle_teacher_actions(
        self,
        env_index: int,
        transaction: MembershipTransaction,
    ) -> dict[str, int] | None:
        if self._pending_trace_context[env_index] is not None:
            raise RuntimeError("A1 trace context was not consumed exactly once")
        membership = self.per_environment_membership[env_index]
        for delta in transaction.atomic_membership_delta:
            membership[str(delta.kind)] += 1
        frontier = tuple(
            str(key)
            for key in transaction.post_membership_pre_policy_snapshot.frontier
        )
        if not frontier:
            self._pending_trace_context[env_index] = {
                "transaction": transaction,
                "event_ranks": {},
                "actual_proposals": {},
                "semantic_incumbents": {},
            }
            return None
        core = self.cores[env_index]
        adapter = self.collector.envs[env_index]
        process_states = adapter.process_state_mapping(frontier)
        self.oracle_constructive_calls += 1
        selected: dict[str, int] = {}
        ranks = self.per_environment_event_ranks[env_index]
        buckets = self.per_environment_buckets[env_index]
        actual_proposals: dict[str, int] = {}
        semantic_incumbents: dict[str, int | None] = {}
        for key in frontier:
            self.proposal_policy_calls += 1
            ranks[key] += 1
            event_rank = int(ranks[key])
            record = core.records.get(key)
            incumbent = None if record is None else record.active_skill
            position, velocity = np.asarray(
                process_states[key], dtype=np.float64
            ).tolist()
            proposal = proposed_successor(
                position=position,
                velocity=velocity,
                current_skill=None if incumbent is None else int(incumbent),
            )
            category = _category(transaction, key)
            bucket = buckets[(int(proposal), category)]
            bucket["frontier_opportunities"] += 1
            bucket["proposed_skills"].add(int(proposal))
            bucket["event_ranks"].add(event_rank)
            actual_proposals[key] = int(proposal)
            semantic_incumbents[key] = None if incumbent is None else int(incumbent)
            if incumbent is None:
                if category != JOIN or int(proposal) != 2:
                    raise RuntimeError("genuine joins must start at skill 2")
                selected[key] = int(proposal)
                continue
            current = int(incumbent)
            bucket["active_skills"].add(current)
            if int(proposal) == current:
                selected[key] = current
                continue
            bucket["different_successor_opportunities"] += 1
            receipt = classify_support_receipt(
                self.support_cell, int(proposal), position, velocity
            )
            if receipt.gate:
                bucket["gated"] += 1
                bucket["strict_truth" if receipt.truth else "alias"] += 1
                _update_range(bucket, "gated_position", float(position))
                _update_range(bucket, "gated_velocity", float(velocity))
                selected[key] = int(proposal)
            else:
                bucket["unresolved"] += 1
                selected[key] = current
        self._pending_trace_context[env_index] = {
            "transaction": transaction,
            "event_ranks": {key: int(ranks[key]) for key in frontier},
            "actual_proposals": actual_proposals,
            "semantic_incumbents": semantic_incumbents,
        }
        return selected

    def _capture_preframe(self, env_index: int, observed_core: Any) -> None:
        context = self._pending_trace_context[env_index]
        if context is None:
            raise RuntimeError("A1 hook ran without its bound transaction")
        self._pending_trace_context[env_index] = None
        core = self.cores[env_index]
        if observed_core is not core:
            raise RuntimeError("A1 hook observed the wrong lifecycle core")
        transaction = context["transaction"]
        post = transaction.post_membership_pre_policy_snapshot
        frontier = tuple(str(key) for key in post.frontier)
        adapter = self.collector.envs[env_index]
        environment = adapter.environment
        if environment is None:
            raise RuntimeError("A1 hook lost the real clean-process environment")
        if int(environment.time) != int(self.step_index):
            raise RuntimeError("A1 capture occurred after primitive process stepping")
        if int(core.physical_time) != int(self.step_index):
            raise RuntimeError("A1 capture core time left the pre-policy boundary")
        if len(self.reward_trace[env_index]) != int(self.step_index):
            raise RuntimeError("A1 capture observed a completed current transition")
        if int(post.physical_time) != int(self.step_index):
            raise RuntimeError("A1 bound transaction time drifted")

        self.trace_hook_calls += 1
        if not frontier:
            return
        process_states = adapter.process_state_mapping(frontier)
        event_ranks = dict(context["event_ranks"])
        episode_value = int(self.episode_ids[env_index])
        episode_index = _episode_index_from_id(
            episode_value, cell=self.support_cell, task_seed=self.trace_task_seed
        )
        real_sink = self.real_frontier_rows[env_index]
        static_sink = self.static_compatibility_rows[env_index]

        for key in frontier:
            record = core.records.get(key)
            if record is None:
                raise RuntimeError("A1 capture occurred before membership commit")
            category = _category(transaction, key)
            if category not in OPPORTUNITY_CATEGORIES:
                raise RuntimeError("A1 lifecycle category left the frozen support")
            if category == JOIN:
                if not bool(record.is_genuine_join) or record.active_skill is not None:
                    raise RuntimeError("A1 join was not observed at its committed boundary")
                incumbent: int | None = None
            else:
                if record.active_skill is None:
                    raise RuntimeError("A1 incumbent-bearing frontier lost its skill")
                incumbent = int(record.active_skill)
            if incumbent != context["semantic_incumbents"][key]:
                raise RuntimeError("A1 membership commit changed proposal incumbent meaning")
            position, velocity = np.asarray(
                process_states[key], dtype=np.float64
            ).tolist()
            actual_proposal = int(context["actual_proposals"][key])
            classifications = {
                skill: classify_support_receipt(
                    self.support_cell, skill, position, velocity
                )
                for skill in SKILLS
            }
            actual_receipt = classifications[int(actual_proposal)]
            truth_skills = tuple(
                skill for skill in SKILLS if classifications[skill].truth
            )
            incumbent_present = incumbent is not None
            different_successor = bool(
                incumbent_present and int(actual_proposal) != int(incumbent)
            )
            truth_non_incumbent = bool(
                incumbent_present
                and any(skill != int(incumbent) for skill in truth_skills)
            )
            mask = {
                "frontier_present": True,
                "incumbent_present": incumbent_present,
                "different_successor": different_successor,
                "actual_proposal_gate": bool(actual_receipt.gate),
                "truth_any_skill": bool(truth_skills),
                "truth_non_incumbent_skill": truth_non_incumbent,
                "truth_actual_proposal": bool(actual_receipt.truth),
                "eligible_strict_truth": bool(
                    incumbent_present
                    and different_successor
                    and actual_receipt.gate
                    and bool(truth_skills)
                    and truth_non_incumbent
                    and actual_receipt.truth
                ),
            }
            missing = semantic_missing_predicates(mask)
            event_rank = int(event_ranks[key])
            if event_rank <= 0 or event_rank != int(
                self.per_environment_event_ranks[env_index][key]
            ):
                raise RuntimeError("A1 event rank was incremented or rebound twice")
            real_frontier_id = (
                f"{self.support_cell.name}:{self.trace_task_seed}:{episode_value}:"
                f"{self.step_index}:{key}:{event_rank}"
            )
            row = {
                "real_frontier_id": real_frontier_id,
                "capture_boundary": CAPTURE_BOUNDARY,
                "cell": self.support_cell.name,
                "task_seed": self.trace_task_seed,
                "episode_index": episode_index,
                "episode_id": episode_value,
                "environment_step": int(self.step_index),
                "physical_time": int(post.physical_time),
                "completed_primitive_transitions_at_capture": len(
                    self.reward_trace[env_index]
                ),
                "lifecycle_key": key,
                "event_rank": event_rank,
                "lifecycle_category": category,
                "committed_record_present": True,
                "incumbent_present": incumbent_present,
                "incumbent_skill": incumbent,
                "position": float(position),
                "velocity": float(velocity),
                "actual_proposal": int(actual_proposal),
                "different_successor": different_successor,
                "actual_proposal_gate": bool(actual_receipt.gate),
                "actual_proposal_strict_truth": bool(actual_receipt.truth),
                "all_skill_classification": {
                    str(skill): {
                        "gate": bool(classifications[skill].gate),
                        "strict_truth": bool(classifications[skill].truth),
                    }
                    for skill in SKILLS
                },
                "truth_skill_set": list(truth_skills),
                "truth_skill_set_label": _truth_set_label(truth_skills),
                "complete_mask": mask,
                "mask_code": _mask_code(mask),
                "missing_predicates": list(missing),
                "semantic_near_miss_class": semantic_near_miss_class(mask),
                "real_reachable_evidence": True,
            }
            real_sink.append(row)
            for hypothetical_incumbent in SKILLS:
                static_sink.append(
                    _static_row(
                        row,
                        cell=self.support_cell,
                        hypothetical_incumbent=hypothetical_incumbent,
                    )
                )
                self.static_classification_calls += 1

    def close(self) -> None:
        for core in self.cores:
            core.install_preframe_intervention(None)
        super().close()


def _row_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {
        "real_frontier_rows": len(rows),
        "eligible_strict_truth": sum(
            bool(row["complete_mask"]["eligible_strict_truth"]) for row in rows
        ),
        "truth_any_skill": sum(
            bool(row["complete_mask"]["truth_any_skill"]) for row in rows
        ),
        "truth_non_incumbent_skill": sum(
            bool(row["complete_mask"]["truth_non_incumbent_skill"])
            for row in rows
        ),
        "truth_actual_proposal": sum(
            bool(row["complete_mask"]["truth_actual_proposal"]) for row in rows
        ),
        "gated_alias_different_successor": sum(
            bool(row["complete_mask"]["incumbent_present"])
            and bool(row["complete_mask"]["different_successor"])
            and bool(row["complete_mask"]["actual_proposal_gate"])
            and not bool(row["complete_mask"]["truth_actual_proposal"])
            for row in rows
        ),
    }


def _marginal_table(
    rows: Sequence[Mapping[str, Any]],
    *,
    fields: Sequence[str],
    domain: Sequence[tuple[Any, ...]],
) -> list[dict[str, Any]]:
    table: list[dict[str, Any]] = []
    for values in domain:
        subset = [
            row
            for row in rows
            if all(row[field] == value for field, value in zip(fields, values))
        ]
        table.append(
            {
                **{field: value for field, value in zip(fields, values)},
                **_row_metrics(subset),
            }
        )
    return table


def _complete_tables(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_mask = Counter(int(row["mask_code"]) for row in rows)
    mask_histogram = [
        {
            "mask_code": code,
            "mask_bits": format(code, "08b"),
            "count": int(by_mask[code]),
        }
        for code in range(1 << len(MASK_FIELDS))
    ]
    by_near_miss = Counter(str(row["semantic_near_miss_class"]) for row in rows)
    near_miss = [
        {"semantic_near_miss_class": label, "count": int(by_near_miss[label])}
        for label in NEAR_MISS_DOMAIN
    ]
    return {
        "mask_field_bit_order": list(MASK_FIELDS),
        "complete_mask_histogram": mask_histogram,
        "by_cell": _marginal_table(
            rows,
            fields=("cell",),
            domain=tuple((cell.name,) for cell in CELLS),
        ),
        "by_seed": _marginal_table(
            rows,
            fields=("task_seed",),
            domain=tuple((seed,) for seed in FULL_TASK_SEEDS),
        ),
        "by_cell_seed": _marginal_table(
            rows,
            fields=("cell", "task_seed"),
            domain=tuple(
                (cell.name, seed) for cell in CELLS for seed in FULL_TASK_SEEDS
            ),
        ),
        "by_lifecycle_category": _marginal_table(
            rows,
            fields=("lifecycle_category",),
            domain=tuple((value,) for value in OPPORTUNITY_CATEGORIES),
        ),
        "by_incumbent": _marginal_table(
            rows,
            fields=("incumbent_skill",),
            domain=((None,), (0,), (1,), (2,)),
        ),
        "by_actual_proposal": _marginal_table(
            rows,
            fields=("actual_proposal",),
            domain=tuple((value,) for value in SKILLS),
        ),
        "by_truth_skill_set": _marginal_table(
            rows,
            fields=("truth_skill_set_label",),
            domain=tuple((value,) for value in TRUTH_SET_DOMAIN),
        ),
        "by_semantic_near_miss": near_miss,
    }


def _static_tables(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    joint = Counter(
        (
            int(row["hypothetical_incumbent_skill"]),
            int(row["hypothetical_proposal"]),
            bool(row["proposal_strict_truth"]),
            bool(row["eligible_if_incumbent"]),
        )
        for row in rows
    )
    return {
        "classification_kind": "STATIC_HYPOTHETICAL_INCUMBENT_COMPATIBILITY",
        "reachable_evidence": False,
        "hypothetical_environment_transitions": 0,
        "joint_zero_filled": [
            {
                "hypothetical_incumbent_skill": incumbent,
                "hypothetical_proposal": proposal,
                "proposal_strict_truth": truth,
                "eligible_if_incumbent": eligible,
                "count": int(joint[(incumbent, proposal, truth, eligible)]),
            }
            for incumbent, proposal, truth, eligible in product(
                SKILLS, SKILLS, (False, True), (False, True)
            )
        ],
    }


def _decision_branch(
    real_rows: Sequence[Mapping[str, Any]],
    static_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    eligible = [
        row for row in real_rows if row["complete_mask"]["eligible_strict_truth"]
    ]
    aliases = [
        row
        for row in real_rows
        if row["complete_mask"]["incumbent_present"]
        and row["complete_mask"]["different_successor"]
        and row["complete_mask"]["actual_proposal_gate"]
        and not row["complete_mask"]["truth_actual_proposal"]
    ]
    proposal_misses = [
        row
        for row in real_rows
        if row["complete_mask"]["incumbent_present"]
        and row["complete_mask"]["truth_non_incumbent_skill"]
        and not row["complete_mask"]["truth_actual_proposal"]
    ]
    incumbent_only = [
        row
        for row in real_rows
        if row["incumbent_skill"] is not None
        and row["truth_skill_set"] == [int(row["incumbent_skill"])]
    ]
    any_truth = [row for row in real_rows if row["complete_mask"]["truth_any_skill"]]
    static_eligible = [row for row in static_rows if row["eligible_if_incumbent"]]

    if eligible and aliases:
        branch = 1
        label = "OBSERVED_ELIGIBLE_STRICT_TRUTH_AND_ALIAS_SUPPORT"
    elif proposal_misses:
        branch = 2
        label = "OBSERVED_NON_INCUMBENT_TRUTH_ACTUAL_PROPOSAL_MISS"
    elif incumbent_only and len(incumbent_only) == len(any_truth):
        branch = 3
        label = "OBSERVED_TRUTH_ONLY_FOR_INCUMBENT"
    elif not any_truth:
        branch = 4
        label = "NO_SKILL_STRICT_TRUE_IN_FIXED_REAL_TRACE_CAP"
    elif static_eligible and not eligible:
        branch = 5
        label = "COMPATIBILITY_ONLY_UNDER_STATIC_HYPOTHETICAL_INCUMBENTS"
    else:
        # This is a finite descriptive fallback, not a new scientific branch.
        # It fails closed so CPM sees an unhandled mask population.
        raise RuntimeError("A1 observed masks do not map to a frozen decision branch")
    return {
        "branch": branch,
        "label": label,
        "finite_evidence_only": True,
        "counts": {
            "eligible_strict_truth": len(eligible),
            "gated_alias_different_successor": len(aliases),
            "non_incumbent_truth_actual_proposal_miss": len(proposal_misses),
            "truth_only_for_incumbent": len(incumbent_only),
            "truth_any_skill": len(any_truth),
            "static_hypothetical_eligible": len(static_eligible),
        },
    }


def run_truth_reachability_decomposition(
    config: SupportMapConfig,
    *,
    code_revision: str,
) -> dict[str, Any]:
    """Run one fixed nonintervening trace roster and analyze all frontier rows."""

    if config not in (SMOKE_CONFIG, FULL_CONFIG):
        raise ValueError("A1 accepts only the registered smoke/full configurations")
    roster = build_episode_roster(config)
    declared = config.counts()
    real_rows: list[dict[str, Any]] = []
    static_rows: list[dict[str, Any]] = []
    membership_rows: list[dict[str, Any]] = []
    call_counts = Counter()
    lifecycle_checks: list[bool] = []

    for cell in CELLS:
        for task_seed in config.task_seeds:
            ids = tuple(
                int(row["episode_id"])
                for row in roster
                if row["cell"] == cell.name and row["task_seed"] == task_seed
            )
            runtime = TruthReachabilityVectorRuntime.create_cell(
                cell=cell, episode_ids=ids, task_seed=task_seed
            )
            try:
                runtime.advance()
                real_rows.extend(
                    row for environment_rows in runtime.real_frontier_rows for row in environment_rows
                )
                static_rows.extend(
                    row
                    for environment_rows in runtime.static_compatibility_rows
                    for row in environment_rows
                )
                membership = sum(runtime.per_environment_membership, Counter())
                membership_rows.append(
                    {
                        "cell": cell.name,
                        "task_seed": int(task_seed),
                        "counts": {
                            kind: int(membership[kind]) for kind in MEMBERSHIP_KINDS
                        },
                    }
                )
                call_counts["proposal_policy"] += runtime.proposal_policy_calls
                call_counts["environment_transition"] += (
                    runtime.environment_transition_calls
                )
                call_counts["supplied_executor"] += runtime.supplied_executor_calls
                call_counts["variable_roster_event_core_transaction"] += (
                    runtime.lifecycle_transaction_calls
                )
                call_counts["trace_hook"] += runtime.trace_hook_calls
                call_counts["static_classification"] += (
                    runtime.static_classification_calls
                )
                lifecycle_checks.extend(
                    bool(value)
                    for key, value in runtime.lifecycle_audit.items()
                    if key != "frozen_absent_high"
                )
                if any(value is not None for value in runtime._pending_trace_context):
                    raise RuntimeError("A1 terminal runtime retained trace context")
            finally:
                runtime.close()

    real_ids = [str(row["real_frontier_id"]) for row in real_rows]
    if len(real_ids) != len(set(real_ids)):
        raise RuntimeError("A1 real frontier identity is not unique")
    if len(static_rows) != len(real_rows) * len(SKILLS):
        raise RuntimeError("A1 static compatibility coverage drifted")
    if call_counts["proposal_policy"] != len(real_rows):
        raise RuntimeError("A1 proposal count differs from real frontier rows")
    for name in (
        "environment_transition",
        "supplied_executor",
        "variable_roster_event_core_transaction",
    ):
        if call_counts[name] != declared["environment_transitions"]:
            raise RuntimeError(f"A1 {name} count drifted from the registered cap")
    if not lifecycle_checks or not all(lifecycle_checks):
        raise RuntimeError("A1 real lifecycle invariant audit failed")

    actual = {
        "cells": len(CELLS),
        "task_seeds": len(config.task_seeds),
        "episodes": len(roster),
        "environment_transitions": int(call_counts["environment_transition"]),
    }
    if actual != declared:
        raise RuntimeError(f"A1 actual counts differ: {actual} != {declared}")
    config_payload = asdict(config)
    config_payload["task_seeds"] = list(config.task_seeds)
    tables = _complete_tables(real_rows)
    static_tables = _static_tables(static_rows)
    branch = _decision_branch(real_rows, static_rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": "experiment",
        "evidence_level": "A",
        "formal": False,
        "candidate_id": CANDIDATE_ID,
        "treatment_id": TREATMENT_ID,
        "arm": DET_ARM,
        "config_name": config.name,
        "code_revision": str(code_revision),
        "evidence_source": "SINGLE_NEW_NONINTERVENING_A1_TRACE_PASS",
        "capture_boundary": CAPTURE_BOUNDARY,
        "execution_command": (
            "python scripts/run_vsp05_a1_truth_reachability_decomposition.py "
            f"--config {config.name} --code-revision {code_revision} "
            "--output <explicit-output>"
        ),
        "environment_binding": {
            "environment": (
                "experiments.candidates.vsp_05.support_map."
                "CellCleanProcessDynamicRosterEventEnv"
            ),
            "event_core": "ha_ctse_process.variable_roster_event.VariableRosterEventCore",
            "hook": "VariableRosterEventCore.install_preframe_intervention",
            "hook_effect": "read_only_candidate_local_observation",
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
                "unchanged_from_b0": True,
            },
            "proposal_rule": "unchanged proposed_successor",
            "K_search": 0,
            "hypothetical_environment_transitions": 0,
        },
        "declared_counts": declared,
        "actual_counts": actual,
        "call_counts": {
            "environment_transition": int(call_counts["environment_transition"]),
            "proposal_policy": int(call_counts["proposal_policy"]),
            "supplied_executor": int(call_counts["supplied_executor"]),
            "variable_roster_event_core_transaction": int(
                call_counts["variable_roster_event_core_transaction"]
            ),
            "trace_hook": int(call_counts["trace_hook"]),
            "static_classification": int(call_counts["static_classification"]),
            "hypothetical_environment_transition": 0,
            "learner": 0,
            "trainer": 0,
            "optimizer_update": 0,
        },
        "real_calls": {
            "environment": True,
            "proposal_policy": bool(real_rows),
            "supplied_executor": True,
            "variable_roster_event_core": True,
            "learner": False,
            "trainer": False,
            "optimizer": False,
            "hypothetical_environment": False,
        },
        "episode_roster": list(roster),
        "membership_event_coverage": membership_rows,
        "real_frontier_rows": real_rows,
        "static_hypothetical_incumbent_rows": static_rows,
        "predicate_tables": tables,
        "static_compatibility_table": static_tables,
        "decision_map": branch,
        "claim_boundary": (
            "finite fixed-cap candidate-local reachability decomposition only; "
            "no prevalence, learner value, utility, generalization, promotion, "
            "retirement, global impossibility, sibling or portfolio claim"
        ),
        "scientific_disposition": None,
        "c_treatment_licensed": False,
        "updates": 0,
        "trainer_calls": 0,
        "learner_calls": 0,
        "K_search": 0,
        "hypothetical_transitions": 0,
    }


def _deep_equal(left: Any, right: Any) -> bool:
    if isinstance(left, np.ndarray) or isinstance(right, np.ndarray):
        return bool(np.array_equal(np.asarray(left), np.asarray(right)))
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return set(left) == set(right) and all(
            _deep_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        return len(left) == len(right) and all(
            _deep_equal(a, b) for a, b in zip(left, right)
        )
    return bool(left == right)


def run_differential_nonintervention_smoke(*, steps: int = 12) -> dict[str, Any]:
    """Compare one bounded A1 trace against the unchanged B0 runtime."""

    count = int(steps)
    if count <= 0 or count > HORIZON:
        raise ValueError("differential smoke steps lie outside the real horizon")
    cell = CELLS[0]
    task_seed = FULL_TASK_SEEDS[0]
    episode_value = int(build_episode_roster(SMOKE_CONFIG)[0]["episode_id"])
    baseline = SupportMapVectorRuntime.create_cell(
        cell=cell, episode_ids=(episode_value,), task_seed=task_seed
    )
    observed = TruthReachabilityVectorRuntime.create_cell(
        cell=cell, episode_ids=(episode_value,), task_seed=task_seed
    )
    try:
        baseline.advance(count)
        observed.advance(count)
        checks = {
            "primitive_action_trace_equal": _deep_equal(
                baseline.primitive_action_trace, observed.primitive_action_trace
            ),
            "reward_trace_equal": _deep_equal(
                baseline.reward_trace, observed.reward_trace
            ),
            "decision_trace_equal": _deep_equal(
                baseline.decision_trace, observed.decision_trace
            ),
            "membership_evidence_equal": _deep_equal(
                baseline.per_environment_membership,
                observed.per_environment_membership,
            ),
            "lifecycle_audit_equal": _deep_equal(
                baseline.lifecycle_audit, observed.lifecycle_audit
            ),
            "transition_counts_equal": (
                baseline.environment_transition_calls
                == observed.environment_transition_calls
                == count
            ),
            "proposal_counts_equal": (
                baseline.proposal_policy_calls == observed.proposal_policy_calls
            ),
        }
        return {
            "cell": cell.name,
            "task_seed": task_seed,
            "episode_id": episode_value,
            "steps": count,
            "all_equal": all(checks.values()),
            "checks": checks,
            "observed_real_frontier_rows": sum(
                len(values) for values in observed.real_frontier_rows
            ),
            "observed_static_rows": sum(
                len(values) for values in observed.static_compatibility_rows
            ),
            "hypothetical_environment_transitions": 0,
        }
    finally:
        baseline.close()
        observed.close()


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
    result = run_truth_reachability_decomposition(
        config, code_revision=args.code_revision
    )
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
