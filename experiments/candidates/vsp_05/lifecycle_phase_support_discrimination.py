"""VSP05-A2 fixed lifecycle-phase support discrimination.

The treatment changes only the two deterministic temporary leaves from
physical time 20 to time 19.  It reuses A1's real supplied-executor runtime,
post-membership/pre-policy trace boundary, proposal, receipt classifier and
complete semantic mask.  No learner, optimizer, search or hypothetical
environment transition exists in this module.
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

import numpy as np

from experiments.candidates.vsp_05.support_map import (
    CELLS,
    CellCleanProcessDynamicRosterEnv,
    FULL_TASK_SEEDS,
    MEMBERSHIP_KINDS,
    OPPORTUNITY_CATEGORIES,
    PROPOSED_SKILLS,
    SupportCell,
    _category,
    build_episode_roster,
    classify_support_receipt,
    make_clean_process_dynamic_roster_ledger,
)
from experiments.candidates.vsp_05.truth_reachability_decomposition import (
    CAPTURE_BOUNDARY,
    MASK_FIELDS,
    NEAR_MISS_DOMAIN,
    SKILLS,
    TRUTH_SET_DOMAIN,
    TruthReachabilityVectorRuntime,
    _complete_tables,
    _deep_equal,
)
from experiments.candidates.vsp_05.real_toy_semantic_veto import (
    CANDIDATE_ID,
    DET_ARM,
)
from ha_ctse_process.collectors import SyncEnvCollector
from ha_ctse_process.dynamic_roster_clean_process_testbed import (
    CleanProcessDynamicRosterEventEnv,
)
from ha_ctse_process.dynamic_roster_testbed import (
    ACTIVE,
    HORIZON,
    IDLE,
    NOT_JOINED,
    TEMPORARILY_ABSENT,
    TERMINAL,
    MembershipChange,
)
from ha_ctse_process.variable_roster_event import (
    ACTIVE as CORE_ACTIVE,
    JOIN,
    REJOIN,
    TEMPORARY_LEAVE,
    TEMPORARILY_ABSENT as CORE_TEMPORARILY_ABSENT,
    TERMINAL_LEAVE,
    VariableRosterEventCore,
)


TREATMENT_ID = "VSP05-A2-LIFECYCLE-PHASE-SUPPORT-DISCRIMINATION"
SCHEMA_VERSION = 1
CONTROL_RESULT_COMMIT = "9f3c57f809a0c0ee11868e025adbeea762832a46"
CONTROL_SOURCE_COMMIT = "1a09bccf9bd64c756865531bc55a871afa286dd3"
CONTROL_RAW_SHA256 = (
    "d4ba7e00ae65c4f0cfd6f84b37c300e9e580868c42bd3c3f02eff20b0b3a3f2e"
)
CONTROL_TREATMENT_ID = "VSP05-A1-TRUTH-REACHABILITY-DECOMPOSITION"
CONTROL_RAW_RELATIVE_PATH = Path(
    "logs/vsp05_a1_truth_reachability_1a09bccf_r1/raw_result.json"
)

CONTROL_LEAVE_TIME = 20
TREATMENT_LEAVE_TIME = 19
REJOIN_TIME = 40
KNOWN_CELL = "STEP_HIGH"
KNOWN_TASK_SEED = 68102
KNOWN_EPISODE_ID = 20401022
KNOWN_LIFECYCLE_KEY = "1"

TERMINAL_LABELS = (
    "CLEAN_TWO_SIDED_SUPPORT_OPENS",
    "PROPOSAL_ALIGNMENT_REMAINS",
    "CLOSED_LOOP_PATTERN_SURVIVES_THIS_PHASE_SHIFT",
    "NONSEPARATING_SHIFT",
    "AMBIGUOUS_OR_ONE_SIDED",
)


@dataclass(frozen=True)
class A2Config:
    name: str
    cells: tuple[SupportCell, ...]
    task_seeds: tuple[int, ...]
    episodes_per_seed_cell: int
    steps: int

    def __post_init__(self) -> None:
        if not self.cells or len(set(self.cells)) != len(self.cells):
            raise ValueError("A2 cells must be nonempty and distinct")
        if any(cell not in CELLS for cell in self.cells):
            raise ValueError("A2 cell lies outside the frozen six-cell table")
        if not self.task_seeds or len(set(self.task_seeds)) != len(self.task_seeds):
            raise ValueError("A2 task seeds must be nonempty and distinct")
        if any(seed not in FULL_TASK_SEEDS for seed in self.task_seeds):
            raise ValueError("A2 seed lies outside the frozen three-seed block")
        if self.episodes_per_seed_cell <= 0 or self.episodes_per_seed_cell > 24:
            raise ValueError("A2 episode count lies outside the frozen cap")
        if not REJOIN_TIME < self.steps <= HORIZON:
            raise ValueError("A2 capture must include the time-40 rejoin")

    def counts(self) -> dict[str, int]:
        episodes = (
            len(self.cells) * len(self.task_seeds) * self.episodes_per_seed_cell
        )
        return {
            "cells": len(self.cells),
            "task_seeds": len(self.task_seeds),
            "episodes": episodes,
            "environment_transitions": episodes * self.steps,
        }


FULL_CONFIG = A2Config("full", CELLS, FULL_TASK_SEEDS, 24, HORIZON)
SMOKE_CONFIG = A2Config("smoke", (CELLS[0],), (FULL_TASK_SEEDS[0],), 1, 41)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_accepted_control(path: str | Path) -> dict[str, Any]:
    """Load and bind the exact accepted A1 full control, failing closed."""

    source = Path(path).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"accepted A1 control is absent: {source}")
    actual_sha = _sha256(source)
    if actual_sha != CONTROL_RAW_SHA256:
        raise ValueError(
            f"accepted A1 raw SHA mismatch: {actual_sha} != {CONTROL_RAW_SHA256}"
        )
    payload = json.loads(source.read_text(encoding="utf-8"))
    required = {
        "candidate_id": CANDIDATE_ID,
        "treatment_id": CONTROL_TREATMENT_ID,
        "code_revision": CONTROL_SOURCE_COMMIT,
        "config_name": "full",
        "capture_boundary": CAPTURE_BOUNDARY,
    }
    for name, expected in required.items():
        if payload.get(name) != expected:
            raise ValueError(f"accepted A1 control {name} identity drifted")
    if payload.get("actual_counts") != {
        "cells": 6,
        "task_seeds": 3,
        "episodes": 432,
        "environment_transitions": 34_560,
    }:
        raise ValueError("accepted A1 control activity counts drifted")
    if int(payload.get("K_search", -1)) != 0 or int(
        payload.get("hypothetical_transitions", -1)
    ) != 0:
        raise ValueError("accepted A1 control is not the frozen nonintervening trace")
    payload["_bound_path"] = str(source)
    payload["_bound_sha256"] = actual_sha
    return payload


def _config_identity(config: A2Config) -> str:
    payload = {
        "treatment_id": TREATMENT_ID,
        "candidate_id": CANDIDATE_ID,
        "control_raw_sha256": CONTROL_RAW_SHA256,
        "control_leave_time": CONTROL_LEAVE_TIME,
        "treatment_leave_time": TREATMENT_LEAVE_TIME,
        "rejoin_time": REJOIN_TIME,
        "cells": [cell.name for cell in config.cells],
        "task_seeds": list(config.task_seeds),
        "episodes_per_seed_cell": config.episodes_per_seed_cell,
        "steps": config.steps,
        "episode_namespace_unchanged": True,
        "proposal_classifier_executor_core_unchanged": True,
        "K_search": 0,
        "hypothetical_environment_transitions": 0,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _frozen_identity(
    config: A2Config, *, code_revision: str, run_id: str
) -> dict[str, str]:
    revision = str(code_revision).strip()
    identifier = str(run_id).strip()
    if not revision or not identifier:
        raise ValueError("A2 source revision and run identity must be frozen")
    if config is FULL_CONFIG and not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("full A2 requires an exact 40-hex source revision")
    if config is FULL_CONFIG and revision in (CONTROL_RESULT_COMMIT, CONTROL_SOURCE_COMMIT):
        raise ValueError("full A2 source identity must name the treatment implementation")
    return {
        "source_revision": revision,
        "configuration_sha256": _config_identity(config),
        "run_id": identifier,
    }


class LifecyclePhaseCellEnv(CellCleanProcessDynamicRosterEnv):
    """Cell environment whose only delta is the temporary-leave phase."""

    def _apply_membership(self) -> MembershipChange:
        joined: tuple[int, ...] = ()
        temporarily_left: tuple[int, ...] = ()
        rejoined: tuple[int, ...] = ()
        terminally_left: tuple[int, ...] = ()

        if self.time == 0:
            joined = (0, 1, 2, 3)
            for key in joined:
                state = self.lifecycles[key]
                if state.status != NOT_JOINED:
                    raise RuntimeError("initial join attempted to reuse a lifecycle")
                state.status = ACTIVE
                state.previous_action = IDLE
                state.active_steps = 0
        elif self.time == TREATMENT_LEAVE_TIME:
            temporarily_left = self.ledger.temporary_leave
            for key in temporarily_left:
                state = self.lifecycles[key]
                if state.status != ACTIVE:
                    raise RuntimeError("A2 temporary leave selected an inactive lifecycle")
                state.status = TEMPORARILY_ABSENT
                state.short_streak = 0
                state.contributed_current_wave = False
                if self.persistent_owner == key:
                    self.persistent_owner = None
        elif self.time == REJOIN_TIME:
            rejoined = self.ledger.temporary_leave
            joined = (4, 5)
            if set(rejoined) & set(joined):
                raise RuntimeError("A2 rejoin and genuine join collided")
            for key in rejoined:
                state = self.lifecycles[key]
                if state.status != TEMPORARILY_ABSENT:
                    raise RuntimeError("A2 rejoin selected a non-absent lifecycle")
                state.status = ACTIVE
                state.membership_epoch += 1
            for key in joined:
                state = self.lifecycles[key]
                if state.status != NOT_JOINED:
                    raise RuntimeError("A2 genuine join attempted to reuse a lifecycle")
                state.status = ACTIVE
                state.previous_action = IDLE
                state.active_steps = 0
        elif self.time == 60:
            terminally_left = self.ledger.terminal_leave
            for key in terminally_left:
                state = self.lifecycles[key]
                if state.status != ACTIVE:
                    raise RuntimeError("A2 terminal leave selected an inactive lifecycle")
                state.status = TERMINAL
                state.short_streak = 0
                state.contributed_current_wave = False
                if self.persistent_owner == key:
                    self.persistent_owner = None

        change = MembershipChange(
            joined=joined,
            temporarily_left=temporarily_left,
            rejoined=rejoined,
            terminally_left=terminally_left,
        )
        for key in change.joined:
            self.process_states[int(key)] = np.zeros(2, dtype=np.float64)
        return change


class LifecyclePhaseEventEnv(CleanProcessDynamicRosterEventEnv):
    """Real event adapter constructing only the A2 phase-shift environment."""

    def __init__(self, *, task_master_seed: int, cell: SupportCell):
        super().__init__(task_master_seed=task_master_seed)
        self.support_cell = cell

    def reset_event_runtime(self, episode_id: int):
        self.episode_id = int(episode_id)
        self.environment = LifecyclePhaseCellEnv(
            make_clean_process_dynamic_roster_ledger(
                self.episode_id, master_seed=self.task_master_seed
            ),
            cell=self.support_cell,
        )
        return self.environment.event_transaction()


class LifecyclePhaseVectorRuntime(TruthReachabilityVectorRuntime):
    """A1 observer rebound to the A2 schedule with lineage audits."""

    @classmethod
    def create_cell(
        cls,
        *,
        cell: SupportCell,
        episode_ids: Sequence[int],
        task_seed: int,
    ) -> "LifecyclePhaseVectorRuntime":
        runtime = super().create_cell(
            cell=cell, episode_ids=episode_ids, task_seed=task_seed
        )
        runtime.collector.close()
        runtime.collector = SyncEnvCollector(
            [
                LifecyclePhaseEventEnv(task_master_seed=int(task_seed), cell=cell)
                for _ in runtime.episode_ids
            ]
        )
        runtime.current_transactions = list(
            runtime.collector.reset_event_runtime(runtime.episode_ids)
        )
        runtime._bind_current_state()
        runtime.phase_lineage_audits = [dict() for _ in runtime.episode_ids]
        if not all(
            isinstance(adapter, LifecyclePhaseEventEnv)
            for adapter in runtime.collector.envs
        ) or not all(isinstance(core, VariableRosterEventCore) for core in runtime.cores):
            raise RuntimeError("A2 lost the real candidate environment/core path")
        return runtime

    def _capture_preframe(self, env_index: int, observed_core: Any) -> None:
        super()._capture_preframe(env_index, observed_core)
        environment = self.collector.envs[env_index].environment
        if environment is None:
            raise RuntimeError("A2 lineage audit lost its real environment")
        core = self.cores[env_index]
        transaction = core.pending_membership_transaction
        # pending_membership_transaction is the raw structural transaction; the
        # A1 context consumed above carries the bound transaction.  The current
        # time and committed records are the authoritative audit boundary.
        time = int(self.step_index)
        treated = tuple(str(value) for value in environment.ledger.temporary_leave)
        audit = self.phase_lineage_audits[env_index]
        if time == TREATMENT_LEAVE_TIME:
            deltas = tuple(
                delta
                for delta in transaction.atomic_membership_delta
                if delta.kind == TEMPORARY_LEAVE
            )
            if tuple(sorted(delta.lifecycle_key for delta in deltas)) != tuple(
                sorted(treated)
            ) or len(transaction.atomic_membership_delta) != len(treated):
                raise RuntimeError("A2 time-19 leave transaction drifted or collided")
            audit["leave"] = {
                key: {
                    "position_velocity": environment.process_states[int(key)].tolist(),
                    "incumbent": (
                        None if core.records[key].active_skill is None else int(core.records[key].active_skill)
                    ),
                    "record_status": str(core.records[key].status),
                    "environment_status": str(environment.lifecycles[int(key)].status),
                    "active_steps": int(environment.lifecycles[int(key)].active_steps),
                    "primitive_actions_before_leave": sum(
                        key in actions for actions in self.primitive_action_trace[env_index]
                    ),
                }
                for key in treated
            }
            if any(
                row["incumbent"] is None
                or row["record_status"] != CORE_TEMPORARILY_ABSENT
                or row["environment_status"] != TEMPORARILY_ABSENT
                or row["active_steps"] != TREATMENT_LEAVE_TIME
                or row["primitive_actions_before_leave"] != TREATMENT_LEAVE_TIME
                for row in audit["leave"].values()
            ):
                raise RuntimeError(
                    "A2 time-19 treated lineage was not active/incumbent-bearing: "
                    + repr(audit["leave"])
                )
        elif time == REJOIN_TIME:
            delta_kinds = [(delta.kind, delta.lifecycle_key) for delta in transaction.atomic_membership_delta]
            expected = [(REJOIN, key) for key in treated] + [(JOIN, "4"), (JOIN, "5")]
            if sorted(delta_kinds) != sorted(expected) or len(delta_kinds) != 4:
                raise RuntimeError("A2 time-40 membership delta drifted or collided")
            if "leave" not in audit:
                raise RuntimeError("A2 rejoin has no bound leave lineage")
            rejoin_rows = {
                str(row["lifecycle_key"]): row
                for row in self.real_frontier_rows[env_index]
                if int(row["environment_step"]) == REJOIN_TIME
                and str(row["lifecycle_key"]) in treated
            }
            if set(rejoin_rows) != set(treated):
                raise RuntimeError("A2 did not retain every treated time-40 frontier")
            audit["rejoin"] = {}
            for key in treated:
                leave = audit["leave"][key]
                state = environment.process_states[int(key)].tolist()
                incumbent = core.records[key].active_skill
                audit["rejoin"][key] = {
                    "position_velocity": state,
                    "incumbent": None if incumbent is None else int(incumbent),
                    "record_status": str(core.records[key].status),
                    "environment_status": str(environment.lifecycles[int(key)].status),
                    "active_steps": int(environment.lifecycles[int(key)].active_steps),
                    "state_unchanged_while_absent": state == leave["position_velocity"],
                    "incumbent_not_reset": incumbent == leave["incumbent"],
                    "skipped_primitives_relative_to_control": 1,
                    "absent_transition_times": list(range(TREATMENT_LEAVE_TIME, REJOIN_TIME)),
                }
                row = audit["rejoin"][key]
                if not (
                    row["record_status"] == CORE_ACTIVE
                    and row["environment_status"] == ACTIVE
                    and row["active_steps"] == TREATMENT_LEAVE_TIME
                    and row["state_unchanged_while_absent"]
                    and row["incumbent_not_reset"]
                ):
                    raise RuntimeError("A2 state/incumbent continuity failed at rejoin")


def _roster(config: A2Config) -> tuple[dict[str, int | str], ...]:
    from experiments.candidates.vsp_05.support_map import SupportMapConfig

    base = build_episode_roster(
        SupportMapConfig(
            config.name,
            config.task_seeds,
            config.episodes_per_seed_cell,
        )
    )
    allowed = {cell.name for cell in config.cells}
    return tuple(row for row in base if str(row["cell"]) in allowed)


def _schedule_rows(config: A2Config) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in _roster(config):
        ledger = make_clean_process_dynamic_roster_ledger(
            int(item["episode_id"]), master_seed=int(item["task_seed"])
        )
        treated = tuple(int(key) for key in ledger.temporary_leave)
        if len(treated) != 2 or len(set(treated)) != 2:
            raise RuntimeError("A2 ledger did not select two unique temporary leaves")
        for key in treated:
            rows.append(
                {
                    "cell": str(item["cell"]),
                    "task_seed": int(item["task_seed"]),
                    "episode_index": int(item["episode_index"]),
                    "episode_id": int(item["episode_id"]),
                    "lifecycle_key": str(key),
                    "control_leave_time": CONTROL_LEAVE_TIME,
                    "treatment_leave_time": TREATMENT_LEAVE_TIME,
                    "control_rejoin_time": REJOIN_TIME,
                    "treatment_rejoin_time": REJOIN_TIME,
                    "leave_shift": -1,
                    "other_membership_delta": False,
                    "event_collision": False,
                }
            )
    identities = {
        (row["cell"], row["task_seed"], row["episode_id"], row["lifecycle_key"])
        for row in rows
    }
    if len(identities) != len(rows):
        raise RuntimeError("A2 schedule contains a duplicate lifecycle identity")
    return rows


def run_treatment_probe(
    config: A2Config,
    *,
    control_path: str | Path,
    code_revision: str,
    run_id: str,
    equivalence_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run one registered treatment arm (full or proof-sized smoke)."""

    if config not in (FULL_CONFIG, SMOKE_CONFIG):
        raise ValueError("A2 accepts only its registered full or smoke configuration")
    control = load_accepted_control(control_path)
    identity = _frozen_identity(config, code_revision=code_revision, run_id=run_id)
    if config is FULL_CONFIG:
        _validate_equivalence_receipt(equivalence_receipt)
    roster = _roster(config)
    schedule_rows = _schedule_rows(config)
    expected_lifecycle_rows = 2 * len(roster)
    if len(schedule_rows) != expected_lifecycle_rows:
        raise RuntimeError("A2 schedule coverage drifted from two leaves per episode")

    real_rows: list[dict[str, Any]] = []
    lineage_audits: list[dict[str, Any]] = []
    membership_rows: list[dict[str, Any]] = []
    counts = Counter()
    lifecycle_checks: list[bool] = []
    for cell in config.cells:
        for task_seed in config.task_seeds:
            ids = tuple(
                int(row["episode_id"])
                for row in roster
                if row["cell"] == cell.name and row["task_seed"] == task_seed
            )
            runtime = LifecyclePhaseVectorRuntime.create_cell(
                cell=cell, episode_ids=ids, task_seed=task_seed
            )
            try:
                runtime.advance(config.steps)
                real_rows.extend(
                    row
                    for environment_rows in runtime.real_frontier_rows
                    for row in environment_rows
                )
                for episode_id, audit in zip(runtime.episode_ids, runtime.phase_lineage_audits):
                    if set(audit) != {"leave", "rejoin"}:
                        raise RuntimeError("A2 lineage audit did not reach leave and rejoin")
                    lineage_audits.append(
                        {
                            "cell": cell.name,
                            "task_seed": int(task_seed),
                            "episode_id": int(episode_id),
                            **audit,
                        }
                    )
                membership = sum(runtime.per_environment_membership, Counter())
                membership_rows.append(
                    {
                        "cell": cell.name,
                        "task_seed": int(task_seed),
                        "counts": {kind: int(membership[kind]) for kind in MEMBERSHIP_KINDS},
                    }
                )
                counts["proposal_policy"] += runtime.proposal_policy_calls
                counts["environment_transition"] += runtime.environment_transition_calls
                counts["supplied_executor"] += runtime.supplied_executor_calls
                counts["variable_roster_event_core_transaction"] += runtime.lifecycle_transaction_calls
                counts["trace_hook"] += runtime.trace_hook_calls
                lifecycle_checks.extend(
                    bool(value)
                    for key, value in runtime.lifecycle_audit.items()
                    if key != "frozen_absent_high"
                )
                if any(value is not None for value in runtime._pending_trace_context):
                    raise RuntimeError("A2 terminal runtime retained trace context")
            finally:
                runtime.close()

    declared = config.counts()
    if counts["environment_transition"] != declared["environment_transitions"]:
        raise RuntimeError("A2 environment transition count drifted")
    if counts["supplied_executor"] != declared["environment_transitions"]:
        raise RuntimeError("A2 supplied-executor count drifted")
    if counts["variable_roster_event_core_transaction"] != declared["environment_transitions"]:
        raise RuntimeError("A2 lifecycle transaction count drifted")
    if counts["proposal_policy"] != len(real_rows):
        raise RuntimeError("A2 proposal count differs from retained real frontier rows")
    if not lifecycle_checks or not all(lifecycle_checks):
        raise RuntimeError("A2 real lifecycle invariant audit failed")

    actual = {
        "cells": len(config.cells),
        "task_seeds": len(config.task_seeds),
        "episodes": len(roster),
        "environment_transitions": int(counts["environment_transition"]),
    }
    if actual != declared:
        raise RuntimeError(f"A2 actual counts differ: {actual} != {declared}")
    if config is FULL_CONFIG and len(schedule_rows) != 864:
        raise RuntimeError("full A2 did not compile exactly 864 leave shifts")

    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "VSP05_A2_TREATMENT_RAW",
        "stage": "experiment" if config is FULL_CONFIG else "technical_validation",
        "evidence_level": "A" if config is FULL_CONFIG else "TECHNICAL_ONLY",
        "scientific_terminal_admitted": False,
        "formal": False,
        "candidate_id": CANDIDATE_ID,
        "treatment_id": TREATMENT_ID,
        "arm": DET_ARM,
        "config_name": config.name,
        "frozen_identity": identity,
        "control_binding": {
            "path": control["_bound_path"],
            "sha256": control["_bound_sha256"],
            "public_result_commit": CONTROL_RESULT_COMMIT,
            "source_commit": CONTROL_SOURCE_COMMIT,
            "reuse_mode": "IMMUTABLE_ACCEPTED_A1_FULL_CONTROL",
        },
        "technical_equivalence_receipt": (
            None if equivalence_receipt is None else deepcopy(dict(equivalence_receipt))
        ),
        "scientific_delta": {
            "control_leave_time": CONTROL_LEAVE_TIME,
            "treatment_leave_time": TREATMENT_LEAVE_TIME,
            "rejoin_time": REJOIN_TIME,
            "changed_fields": ["temporary_leave_physical_time"],
            "K_search": 0,
            "hypothetical_environment_transitions": 0,
        },
        "capture_boundary": CAPTURE_BOUNDARY,
        "configuration": {
            **asdict(config),
            "cells": [cell.name for cell in config.cells],
            "task_seeds": list(config.task_seeds),
            "horizon": HORIZON,
            "episode_namespace_unchanged": True,
        },
        "declared_counts": declared,
        "actual_counts": actual,
        "call_counts": {
            "environment_transition": int(counts["environment_transition"]),
            "proposal_policy": int(counts["proposal_policy"]),
            "supplied_executor": int(counts["supplied_executor"]),
            "variable_roster_event_core_transaction": int(
                counts["variable_roster_event_core_transaction"]
            ),
            "trace_hook": int(counts["trace_hook"]),
            "learner": 0,
            "trainer": 0,
            "optimizer_update": 0,
            "hypothetical_environment_transition": 0,
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
        "schedule_delta_rows": schedule_rows,
        "membership_event_coverage": membership_rows,
        "lineage_runtime_audits": lineage_audits,
        "real_frontier_rows": real_rows,
        "predicate_tables": _complete_tables(real_rows),
        "updates": 0,
        "learner_calls": 0,
        "trainer_calls": 0,
        "K_search": 0,
        "hypothetical_transitions": 0,
    }


def _index_control_rows(control: Mapping[str, Any]) -> dict[tuple[Any, ...], dict[str, Any]]:
    result: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in control["real_frontier_rows"]:
        key = (
            str(row["cell"]),
            int(row["task_seed"]),
            int(row["episode_id"]),
            int(row["environment_step"]),
            str(row["lifecycle_key"]),
        )
        if key in result:
            raise RuntimeError("accepted A1 control frontier key is not unique")
        result[key] = row
    return result


def _expected_configuration(config: A2Config) -> dict[str, Any]:
    return {
        "name": config.name,
        "cells": [cell.name for cell in config.cells],
        "task_seeds": list(config.task_seeds),
        "episodes_per_seed_cell": config.episodes_per_seed_cell,
        "steps": config.steps,
        "horizon": HORIZON,
        "episode_namespace_unchanged": True,
    }


def _config_from_raw(raw: Mapping[str, Any]) -> A2Config:
    name = raw.get("config_name")
    if name == "full":
        return FULL_CONFIG
    if name == "smoke":
        return SMOKE_CONFIG
    raise ValueError("A2 raw config name is not registered")


def _validate_equivalence_receipt(
    receipt: Mapping[str, Any] | None,
) -> None:
    if receipt is None:
        raise ValueError("full A2 requires the separate 82-transition equivalence receipt")
    required = {
        "artifact_kind": "VSP05_A2_EQUIVALENCE_SMOKE",
        "technical_only": True,
        "control_raw_sha256": CONTROL_RAW_SHA256,
        "cell": CELLS[0].name,
        "task_seed": FULL_TASK_SEEDS[0],
        "episode_id": int(_roster(SMOKE_CONFIG)[0]["episode_id"]),
        "control_environment_transitions": 41,
        "treatment_environment_transitions": 41,
        "total_environment_transitions": 82,
        "cap": 82,
        "hypothetical_environment_transitions": 0,
        "learner_calls": 0,
        "trainer_calls": 0,
        "optimizer_updates": 0,
    }
    for name, expected in required.items():
        if receipt.get(name) != expected:
            raise ValueError(f"A2 equivalence receipt {name} drifted")
    checks = receipt.get("checks")
    if not isinstance(checks, Mapping) or not checks or not all(
        value is True for value in checks.values()
    ):
        raise ValueError("A2 equivalence receipt checks are absent or failed")
    if receipt.get("all_checks_passed") is not True:
        raise ValueError("A2 equivalence receipt is not terminally successful")


def _validate_lineage_coverage(
    raw: Mapping[str, Any], config: A2Config
) -> None:
    schedule = list(raw.get("schedule_delta_rows", ()))
    expected_schedule = _schedule_rows(config)
    if schedule != expected_schedule:
        raise ValueError("A2 schedule rows drifted from the exact registered roster")
    expected_by_episode: dict[tuple[str, int, int], set[str]] = {}
    for row in expected_schedule:
        episode = (str(row["cell"]), int(row["task_seed"]), int(row["episode_id"]))
        expected_by_episode.setdefault(episode, set()).add(str(row["lifecycle_key"]))
    audits = list(raw.get("lineage_runtime_audits", ()))
    if len(audits) != len(expected_by_episode):
        raise ValueError("A2 lineage audit episode coverage drifted")
    seen: set[tuple[str, int, int]] = set()
    for audit in audits:
        episode = (
            str(audit.get("cell")),
            int(audit.get("task_seed", -1)),
            int(audit.get("episode_id", -1)),
        )
        if episode not in expected_by_episode or episode in seen:
            raise ValueError("A2 lineage audit namespace is missing or duplicated")
        seen.add(episode)
        treated = expected_by_episode[episode]
        leave = audit.get("leave")
        rejoin = audit.get("rejoin")
        if not isinstance(leave, Mapping) or not isinstance(rejoin, Mapping):
            raise ValueError("A2 lineage leave/rejoin receipts are absent")
        if set(leave) != treated or set(rejoin) != treated:
            raise ValueError("A2 lineage treated-key coverage drifted")
        for key in treated:
            left = leave[key]
            returned = rejoin[key]
            if not (
                left.get("incumbent") is not None
                and left.get("record_status") == CORE_TEMPORARILY_ABSENT
                and left.get("environment_status") == TEMPORARILY_ABSENT
                and int(left.get("active_steps", -1)) == TREATMENT_LEAVE_TIME
                and int(left.get("primitive_actions_before_leave", -1))
                == TREATMENT_LEAVE_TIME
                and returned.get("record_status") == CORE_ACTIVE
                and returned.get("environment_status") == ACTIVE
                and int(returned.get("active_steps", -1)) == TREATMENT_LEAVE_TIME
                and returned.get("state_unchanged_while_absent") is True
                and returned.get("incumbent_not_reset") is True
                and int(returned.get("skipped_primitives_relative_to_control", -1)) == 1
                and returned.get("absent_transition_times")
                == list(range(TREATMENT_LEAVE_TIME, REJOIN_TIME))
                and returned.get("position_velocity") == left.get("position_velocity")
                and returned.get("incumbent") == left.get("incumbent")
            ):
                raise ValueError("A2 lineage continuity receipt is incomplete or inconsistent")
    if seen != set(expected_by_episode):
        raise ValueError("A2 lineage audit roster is incomplete")


def _validate_exact_raw_contract(
    raw: Mapping[str, Any], config: A2Config
) -> None:
    if raw.get("configuration") != _expected_configuration(config):
        raise ValueError("A2 raw configuration is not the exact registered configuration")
    expected_counts = config.counts()
    if raw.get("declared_counts") != expected_counts or raw.get("actual_counts") != expected_counts:
        raise ValueError("A2 declared/actual activity counts drifted")
    expected_roster = list(_roster(config))
    if raw.get("episode_roster") != expected_roster:
        raise ValueError("A2 episode roster or namespace drifted")
    _validate_lineage_coverage(raw, config)

    counts = raw.get("call_counts")
    if not isinstance(counts, Mapping):
        raise ValueError("A2 call-count receipt is absent")
    transitions = expected_counts["environment_transitions"]
    for name in (
        "environment_transition",
        "supplied_executor",
        "variable_roster_event_core_transaction",
        "trace_hook",
    ):
        if int(counts.get(name, -1)) != transitions:
            raise ValueError(f"A2 {name} count drifted from the registered activity")
    for name in (
        "learner",
        "trainer",
        "optimizer_update",
        "hypothetical_environment_transition",
    ):
        if int(counts.get(name, -1)) != 0:
            raise ValueError(f"A2 protected zero count drifted: {name}")
    rows = raw.get("real_frontier_rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("A2 retained real frontier rows are absent")
    if int(counts.get("proposal_policy", -1)) != len(rows):
        raise ValueError("A2 raw proposal/frontier count drifted")
    if any(
        set(row.get("complete_mask", ())) != set(MASK_FIELDS)
        or set(row.get("all_skill_classification", ())) != {"0", "1", "2"}
        for row in rows
    ):
        raise ValueError("A2 real frontier rows lost the complete all-skill mask")
    if raw.get("predicate_tables") != _complete_tables(rows):
        raise ValueError("A2 zero-retaining predicate tables drifted from real rows")

    expected_groups = len(config.cells) * len(config.task_seeds)
    membership = raw.get("membership_event_coverage")
    if not isinstance(membership, list) or len(membership) != expected_groups:
        raise ValueError("A2 membership coverage groups drifted")
    episodes = config.episodes_per_seed_cell
    expected_membership = {
        JOIN: 6 * episodes,
        TEMPORARY_LEAVE: 2 * episodes,
        TERMINAL_LEAVE: (2 * episodes if config.steps > 60 else 0),
        REJOIN: 2 * episodes,
    }
    expected_group_ids = {
        (cell.name, seed) for cell in config.cells for seed in config.task_seeds
    }
    actual_group_ids = {
        (str(row.get("cell")), int(row.get("task_seed", -1))) for row in membership
    }
    if actual_group_ids != expected_group_ids or any(
        row.get("counts") != expected_membership for row in membership
    ):
        raise ValueError("A2 membership event coverage drifted")


_RAW_ADMISSION_MARKER = object()


@dataclass(frozen=True)
class _ValidatedRawAdmission:
    marker: object
    config: A2Config
    run_id: str


def _validate_raw(
    raw: Mapping[str, Any], control: Mapping[str, Any]
) -> _ValidatedRawAdmission:
    if raw.get("artifact_kind") != "VSP05_A2_TREATMENT_RAW":
        raise ValueError("A2 input is not a treatment raw artifact")
    if raw.get("candidate_id") != CANDIDATE_ID or raw.get("treatment_id") != TREATMENT_ID:
        raise ValueError("A2 raw identity drifted")
    binding = raw.get("control_binding", {})
    if not isinstance(binding, Mapping) or not (
        binding.get("sha256") == CONTROL_RAW_SHA256
        and binding.get("public_result_commit") == CONTROL_RESULT_COMMIT
        and binding.get("source_commit") == CONTROL_SOURCE_COMMIT
        and binding.get("reuse_mode") == "IMMUTABLE_ACCEPTED_A1_FULL_CONTROL"
        and str(binding.get("path", "")).strip()
    ):
        raise ValueError("A2 raw is not bound to the accepted A1 control SHA")
    if control.get("_bound_sha256") != CONTROL_RAW_SHA256:
        raise ValueError("A2 analyzer control binding drifted")
    if int(raw.get("K_search", -1)) != 0 or int(raw.get("hypothetical_transitions", -1)) != 0:
        raise ValueError("A2 search/hypothetical cap drifted")
    config = _config_from_raw(raw)
    expected_stage = "experiment" if config is FULL_CONFIG else "technical_validation"
    expected_level = "A" if config is FULL_CONFIG else "TECHNICAL_ONLY"
    if (
        raw.get("stage") != expected_stage
        or raw.get("evidence_level") != expected_level
        or raw.get("scientific_terminal_admitted") is not False
    ):
        raise ValueError("A2 raw scientific/technical admission metadata drifted")
    _validate_exact_raw_contract(raw, config)
    identity = raw.get("frozen_identity")
    if not isinstance(identity, Mapping) or set(identity) != {
        "source_revision",
        "configuration_sha256",
        "run_id",
    }:
        raise ValueError("A2 frozen source/configuration/run identity is absent")
    if identity.get("configuration_sha256") != _config_identity(config):
        raise ValueError("A2 frozen configuration SHA drifted")
    if not str(identity.get("run_id", "")).strip():
        raise ValueError("A2 frozen run identity is empty")
    if config is FULL_CONFIG:
        revision = str(identity.get("source_revision", ""))
        if not re.fullmatch(r"[0-9a-f]{40}", revision) or revision in (
            CONTROL_RESULT_COMMIT,
            CONTROL_SOURCE_COMMIT,
        ):
            raise ValueError("full A2 source revision identity drifted")
        _validate_equivalence_receipt(raw.get("technical_equivalence_receipt"))
    return _ValidatedRawAdmission(
        marker=_RAW_ADMISSION_MARKER,
        config=config,
        run_id=str(identity["run_id"]),
    )


_FULL_ADMISSION_MARKER = object()


@dataclass(frozen=True)
class _FullTerminalAdmission:
    marker: object
    run_id: str
    paired_rejoins: int
    suppressed_t19_frontiers: int
    known_lineage_verified: bool


def _make_full_terminal_admission(
    raw: Mapping[str, Any],
    *,
    raw_admission: _ValidatedRawAdmission,
    paired_rejoins: Sequence[Mapping[str, Any]],
    suppressed: Sequence[Mapping[str, Any]],
    known: Sequence[Mapping[str, Any]],
    control_equal_through_t18: bool,
) -> _FullTerminalAdmission:
    if not isinstance(raw_admission, _ValidatedRawAdmission) or not (
        raw_admission.marker is _RAW_ADMISSION_MARKER
        and raw_admission.config is FULL_CONFIG
        and raw_admission.run_id == str(raw["frozen_identity"]["run_id"])
    ):
        raise ValueError("scientific terminal admission requires exact FULL_CONFIG")
    if len(paired_rejoins) != 864:
        raise ValueError("scientific terminal admission requires 864 paired t40 rows")
    if len(suppressed) != 88:
        raise ValueError("scientific terminal admission requires the measured 88 t19 frontiers")
    known_ok = len(known) == 1 and bool(
        known[0]["different_successor"]
        and known[0]["proposal_gate"]
        and not known[0]["proposal_strict_truth"]
        and known[0]["suppression_changes_time40_incumbent"]
    )
    if not known_ok:
        raise ValueError("scientific terminal admission requires the known t19 lineage")
    if not control_equal_through_t18:
        raise ValueError("scientific terminal admission requires exact matching through t18")
    _validate_equivalence_receipt(raw.get("technical_equivalence_receipt"))
    return _FullTerminalAdmission(
        marker=_FULL_ADMISSION_MARKER,
        run_id=str(raw["frozen_identity"]["run_id"]),
        paired_rejoins=len(paired_rejoins),
        suppressed_t19_frontiers=len(suppressed),
        known_lineage_verified=True,
    )


def classify_terminal_label(
    rows: Sequence[Mapping[str, Any]],
    paired_rejoins: Sequence[Mapping[str, Any]],
    mismatch_lineages: set[tuple[str, int, int, str]],
    *,
    admission: _FullTerminalAdmission,
) -> str:
    """Apply exactly the five pre-registered labels, failing closed."""

    if not isinstance(admission, _FullTerminalAdmission) or not (
        admission.marker is _FULL_ADMISSION_MARKER
        and admission.paired_rejoins == 864
        and admission.suppressed_t19_frontiers == 88
        and admission.known_lineage_verified
        and admission.run_id
    ):
        raise ValueError("five-label classification requires exact full admission")

    eligible = [row for row in rows if row["complete_mask"]["eligible_strict_truth"]]
    aliases = [
        row for row in rows
        if row["complete_mask"]["incumbent_present"]
        and row["complete_mask"]["different_successor"]
        and row["complete_mask"]["actual_proposal_gate"]
        and not row["complete_mask"]["truth_actual_proposal"]
    ]
    nonincumbent = [row for row in rows if row["complete_mask"]["truth_non_incumbent_skill"]]
    actual_truth = [row for row in rows if row["complete_mask"]["truth_actual_proposal"]]
    clean_eligible = [
        row for row in eligible
        if (
            str(row["cell"]),
            int(row["task_seed"]),
            int(row["episode_id"]),
            str(row["lifecycle_key"]),
        ) not in mismatch_lineages
    ]
    paired_separation = any(
        pair["state_delta"]["position"] != 0.0
        or pair["state_delta"]["velocity"] != 0.0
        or not pair["incumbent_lineage_match"]
        or pair["control"]["proposal"] != pair["treatment"]["proposal"]
        or pair["control"]["complete_mask"] != pair["treatment"]["complete_mask"]
        for pair in paired_rejoins
    )
    incumbent_truth_rows = [
        row for row in rows
        if row["incumbent_skill"] is not None
        and row["complete_mask"]["truth_any_skill"]
    ]
    incumbent_only = bool(incumbent_truth_rows) and all(
        row["truth_skill_set"] == [int(row["incumbent_skill"])]
        for row in incumbent_truth_rows
    )

    if eligible and aliases and clean_eligible:
        return TERMINAL_LABELS[0]
    if nonincumbent and not actual_truth:
        return TERMINAL_LABELS[1]
    if paired_separation and incumbent_only and not actual_truth:
        return TERMINAL_LABELS[2]
    if not paired_separation:
        return TERMINAL_LABELS[3]
    return TERMINAL_LABELS[4]


def analyze_treatment(
    raw: Mapping[str, Any], control: Mapping[str, Any]
) -> dict[str, Any]:
    """Pair A2 to accepted A1, audit lineage, and apply the frozen map."""

    raw_admission = _validate_raw(raw, control)
    config = raw_admission.config
    control_index = _index_control_rows(control)
    treatment_rows = list(raw["real_frontier_rows"])
    treatment_index = {
        (
            str(row["cell"]), int(row["task_seed"]), int(row["episode_id"]),
            int(row["environment_step"]), str(row["lifecycle_key"]),
        ): row
        for row in treatment_rows
    }
    if len(treatment_index) != len(treatment_rows):
        raise RuntimeError("A2 treatment frontier key is not unique")

    config_name = config.name
    schedule_rows = list(raw["schedule_delta_rows"])
    pairs: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = []
    mismatch_lineages: set[tuple[str, int, int, str]] = set()
    for schedule in schedule_rows:
        lineage = (
            str(schedule["cell"]), int(schedule["task_seed"]),
            int(schedule["episode_id"]), str(schedule["lifecycle_key"]),
        )
        control_rejoin = control_index.get((*lineage[:3], REJOIN_TIME, lineage[3]))
        treatment_rejoin = treatment_index.get((*lineage[:3], REJOIN_TIME, lineage[3]))
        if control_rejoin is None or treatment_rejoin is None:
            raise RuntimeError("A2 paired rejoin coverage is incomplete")
        if control_rejoin["incumbent_skill"] is None:
            raise RuntimeError(
                "accepted A1 control does not prove a persisted treated incumbent"
            )
        control_t19 = control_index.get((*lineage[:3], TREATMENT_LEAVE_TIME, lineage[3]))
        incumbent_changing = bool(
            control_t19 is not None
            and control_t19["complete_mask"]["different_successor"]
            and control_t19["complete_mask"]["actual_proposal_gate"]
        )
        incumbent_match = control_rejoin["incumbent_skill"] == treatment_rejoin["incumbent_skill"]
        if incumbent_changing and not incumbent_match:
            mismatch_lineages.add(lineage)
        pair = {
            "cell": lineage[0],
            "task_seed": lineage[1],
            "episode_id": lineage[2],
            "lifecycle_key": lineage[3],
            "control": {
                "position": control_rejoin["position"],
                "velocity": control_rejoin["velocity"],
                "incumbent": control_rejoin["incumbent_skill"],
                "proposal": control_rejoin["actual_proposal"],
                "truth_skill_set": control_rejoin["truth_skill_set"],
                "complete_mask": control_rejoin["complete_mask"],
            },
            "treatment": {
                "position": treatment_rejoin["position"],
                "velocity": treatment_rejoin["velocity"],
                "incumbent": treatment_rejoin["incumbent_skill"],
                "proposal": treatment_rejoin["actual_proposal"],
                "truth_skill_set": treatment_rejoin["truth_skill_set"],
                "complete_mask": treatment_rejoin["complete_mask"],
            },
            "state_delta": {
                "position": float(treatment_rejoin["position"] - control_rejoin["position"]),
                "velocity": float(treatment_rejoin["velocity"] - control_rejoin["velocity"]),
            },
            "incumbent_lineage_match": incumbent_match,
            "control_t19_frontier_present": control_t19 is not None,
            "suppressed_incumbent_changing_t19_decision": incumbent_changing,
            "incumbent_mismatch_due_to_suppression": bool(incumbent_changing and not incumbent_match),
        }
        pairs.append(pair)
        if control_t19 is not None:
            suppressed.append(
                {
                    "cell": lineage[0],
                    "task_seed": lineage[1],
                    "episode_id": lineage[2],
                    "lifecycle_key": lineage[3],
                    "control_real_frontier_id": control_t19["real_frontier_id"],
                    "position": control_t19["position"],
                    "velocity": control_t19["velocity"],
                    "incumbent": control_t19["incumbent_skill"],
                    "proposal": control_t19["actual_proposal"],
                    "different_successor": control_t19["different_successor"],
                    "proposal_gate": control_t19["actual_proposal_gate"],
                    "proposal_strict_truth": control_t19["actual_proposal_strict_truth"],
                    "truth_skill_set": control_t19["truth_skill_set"],
                    "complete_mask": control_t19["complete_mask"],
                    "treatment_t19_proposal_suppressed": True,
                    "treatment_control_t40_incumbent_match": incumbent_match,
                    "suppression_changes_time40_incumbent": bool(incumbent_changing and not incumbent_match),
                }
            )

    if len(pairs) != len(schedule_rows):
        raise RuntimeError("A2 paired rejoin table is not exact")
    if config_name == "full" and len(pairs) != 864:
        raise RuntimeError("full A2 paired rejoin table must contain exactly 864 rows")
    if config_name == "full" and len(suppressed) != 88:
        raise RuntimeError("full A2 suppressed proposal count drifted from accepted A1's 88")

    known = [
        row for row in suppressed
        if row["cell"] == KNOWN_CELL
        and row["task_seed"] == KNOWN_TASK_SEED
        and row["episode_id"] == KNOWN_EPISODE_ID
        and row["lifecycle_key"] == KNOWN_LIFECYCLE_KEY
    ]
    if config_name == "full":
        if len(known) != 1 or not (
            known[0]["different_successor"]
            and known[0]["proposal_gate"]
            and not known[0]["proposal_strict_truth"]
            and known[0]["suppression_changes_time40_incumbent"]
        ):
            raise RuntimeError("known STEP_HIGH/68102/20401022/key1 lineage audit failed")

    # Historical equality is checked on every retained frontier through t18.
    treatment_pre = [row for row in treatment_rows if int(row["environment_step"]) <= 18]
    pre_mismatches: list[str] = []
    comparison_fields = (
        "event_rank", "lifecycle_category", "incumbent_skill", "position", "velocity",
        "actual_proposal", "all_skill_classification", "truth_skill_set", "complete_mask",
    )
    for row in treatment_pre:
        key = (
            str(row["cell"]), int(row["task_seed"]), int(row["episode_id"]),
            int(row["environment_step"]), str(row["lifecycle_key"]),
        )
        other = control_index.get(key)
        if other is None or any(not _deep_equal(row[field], other[field]) for field in comparison_fields):
            pre_mismatches.append(str(row["real_frontier_id"]))
    control_pre_keys = {
        key for key in control_index
        if key[0] in {str(row["cell"]) for row in raw["episode_roster"]}
        and key[1] in {int(row["task_seed"]) for row in raw["episode_roster"]}
        and key[2] in {int(row["episode_id"]) for row in raw["episode_roster"]}
        and key[3] <= 18
    }
    treatment_pre_keys = {
        (
            str(row["cell"]), int(row["task_seed"]), int(row["episode_id"]),
            int(row["environment_step"]), str(row["lifecycle_key"]),
        ) for row in treatment_pre
    }
    if treatment_pre_keys != control_pre_keys:
        pre_mismatches.append("FRONTIER_KEY_SET_DRIFT")
    if pre_mismatches:
        raise RuntimeError("A2 treatment differs from accepted control through t18")

    schedule_receipt = {
        "leave_shift_rows": len(schedule_rows),
        "control_leave_time": CONTROL_LEAVE_TIME,
        "treatment_leave_time": TREATMENT_LEAVE_TIME,
        "unchanged_rejoin_rows": len(schedule_rows),
        "rejoin_time": REJOIN_TIME,
        "other_membership_deltas": sum(
            bool(row["other_membership_delta"]) for row in schedule_rows
        ),
        "event_collisions": sum(bool(row["event_collision"]) for row in schedule_rows),
    }
    matching_receipt = {
        "control_equal_through_t18": True,
        "compared_frontier_rows_through_t18": len(treatment_pre),
        "all_control_treated_lineages_active_and_incumbent_bearing_at_t19": True,
        "control_t19_proof": (
            "initial lifecycle remained active before the registered control "
            "leave at t20, and its accepted t40 rejoin retained a non-null "
            "incumbent across the absence"
        ),
        "exogenous_ledger_identity_preserved": True,
        "episode_namespace_identity_preserved": True,
        "causal_separation_begins_at_t19": True,
    }
    lineage_receipt = {
        "primitive_skips": len(schedule_rows),
        "suppressed_control_t19_proposals": len(suppressed),
        "paired_t40_rejoins": len(pairs),
        "incumbent_mismatch_due_to_suppression": len(mismatch_lineages),
        "known_lineage": known[0] if known else None,
        "all_treatment_state_frozen_while_absent": all(
            item["state_unchanged_while_absent"]
            for audit in raw["lineage_runtime_audits"]
            for item in audit["rejoin"].values()
        ),
        "all_treatment_incumbents_preserved_at_rejoin": all(
            item["incumbent_not_reset"]
            for audit in raw["lineage_runtime_audits"]
            for item in audit["rejoin"].values()
        ),
    }

    if config is SMOKE_CONFIG:
        return {
            "schema_version": SCHEMA_VERSION,
            "artifact_kind": "VSP05_A2_TECHNICAL_SMOKE_ANALYSIS",
            "stage": "technical_validation",
            "evidence_level": "TECHNICAL_ONLY",
            "formal": False,
            "candidate_id": CANDIDATE_ID,
            "treatment_id": TREATMENT_ID,
            "config_name": config.name,
            "scientific_terminal_admitted": False,
            "technical_control_binding_verified": True,
            "frozen_identity": deepcopy(raw["frozen_identity"]),
            "actual_counts": deepcopy(raw["actual_counts"]),
            "call_counts": deepcopy(raw["call_counts"]),
            "schedule_delta_receipt": schedule_receipt,
            "technical_matching_receipt": matching_receipt,
            "technical_lineage_receipt": lineage_receipt,
            "paired_t40_rejoin_rows": pairs,
            "predicate_tables": deepcopy(raw["predicate_tables"]),
            "claim_boundary": (
                "proof-sized technical smoke only; no A-level result, terminal "
                "label, historical-control reuse decision, or route disposition"
            ),
        }

    eligible = [row for row in treatment_rows if row["complete_mask"]["eligible_strict_truth"]]
    aliases = [
        row for row in treatment_rows
        if row["complete_mask"]["incumbent_present"]
        and row["complete_mask"]["different_successor"]
        and row["complete_mask"]["actual_proposal_gate"]
        and not row["complete_mask"]["truth_actual_proposal"]
    ]
    nonincumbent = [row for row in treatment_rows if row["complete_mask"]["truth_non_incumbent_skill"]]
    actual_truth = [row for row in treatment_rows if row["complete_mask"]["truth_actual_proposal"]]
    clean_eligible = [
        row for row in eligible
        if (str(row["cell"]), int(row["task_seed"]), int(row["episode_id"]), str(row["lifecycle_key"]))
        not in mismatch_lineages
    ]
    admission = _make_full_terminal_admission(
        raw,
        raw_admission=raw_admission,
        paired_rejoins=pairs,
        suppressed=suppressed,
        known=known,
        control_equal_through_t18=True,
    )
    label = classify_terminal_label(
        treatment_rows,
        pairs,
        mismatch_lineages,
        admission=admission,
    )

    clean_open = label == "CLEAN_TWO_SIDED_SUPPORT_OPENS"
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "VSP05_A2_ANALYZED_RESULT",
        "stage": "experiment",
        "evidence_level": "A",
        "formal": False,
        "scientific_terminal_admitted": True,
        "candidate_id": CANDIDATE_ID,
        "treatment_id": TREATMENT_ID,
        "terminal_label": label,
        "historical_control_reuse_passed": True,
        "clean_two_sided_real_support_opened": clean_open,
        "toy_route_must_park": not clean_open,
        "config_name": config_name,
        "frozen_identity": deepcopy(raw["frozen_identity"]),
        "control_binding": deepcopy(raw["control_binding"]),
        "scientific_delta": deepcopy(raw["scientific_delta"]),
        "declared_counts": deepcopy(raw["declared_counts"]),
        "actual_counts": deepcopy(raw["actual_counts"]),
        "call_counts": deepcopy(raw["call_counts"]),
        "technical_equivalence_receipt": deepcopy(raw["technical_equivalence_receipt"]),
        "schedule_delta_receipt": schedule_receipt,
        "matching_receipt": matching_receipt,
        "lineage_receipt": lineage_receipt,
        "outcome_counts": {
            "eligible_strict_truth": len(eligible),
            "clean_eligible_strict_truth": len(clean_eligible),
            "ambiguous_mismatch_lineage_eligible_strict_truth": len(eligible) - len(clean_eligible),
            "gated_alias_different_successor": len(aliases),
            "truth_non_incumbent_skill": len(nonincumbent),
            "truth_actual_proposal": len(actual_truth),
            "paired_rejoin_separation": sum(
                pair["state_delta"]["position"] != 0.0
                or pair["state_delta"]["velocity"] != 0.0
                or not pair["incumbent_lineage_match"]
                or pair["control"]["proposal"] != pair["treatment"]["proposal"]
                or pair["control"]["complete_mask"] != pair["treatment"]["complete_mask"]
                for pair in pairs
            ),
        },
        "predicate_tables": deepcopy(raw["predicate_tables"]),
        "schedule_delta_rows": schedule_rows,
        "suppressed_t19_control_frontiers": suppressed,
        "paired_t40_rejoin_rows": pairs,
        "lineage_runtime_audits": deepcopy(raw["lineage_runtime_audits"]),
        "real_frontier_rows": treatment_rows,
        "decision_boundary": (
            "Only CLEAN_TWO_SIDED_SUPPORT_OPENS keeps support feasibility open; "
            "all other labels park this exact toy learner route."
        ),
        "claim_boundary": (
            "finite fixed A2 phase intervention only; no prevalence, learner value, "
            "utility, return, generalization, superiority, C authorization, global "
            "impossibility or direction retirement"
        ),
        "scientific_disposition": None,
        "c_treatment_licensed": False,
        "updates": 0,
        "learner_calls": 0,
        "trainer_calls": 0,
        "K_search": 0,
        "hypothetical_transitions": 0,
    }


def evaluate_treatment(raw: Mapping[str, Any], control: Mapping[str, Any]) -> dict[str, Any]:
    analyzed = analyze_treatment(raw, control)
    if analyzed["artifact_kind"] == "VSP05_A2_TECHNICAL_SMOKE_ANALYSIS":
        return {
            "schema_version": SCHEMA_VERSION,
            "artifact_kind": "VSP05_A2_TECHNICAL_SMOKE_EVALUATION_RECEIPT",
            "stage": "technical_validation",
            "evidence_level": "TECHNICAL_ONLY",
            "candidate_id": CANDIDATE_ID,
            "treatment_id": TREATMENT_ID,
            "config_name": "smoke",
            "scientific_terminal_admitted": False,
            "technical_control_binding_verified": True,
            "frozen_identity": analyzed["frozen_identity"],
            "schedule_delta_receipt": analyzed["schedule_delta_receipt"],
            "technical_matching_receipt": analyzed["technical_matching_receipt"],
            "technical_lineage_receipt": analyzed["technical_lineage_receipt"],
            "actual_counts": analyzed["actual_counts"],
            "call_counts": analyzed["call_counts"],
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "VSP05_A2_EVALUATION_RECEIPT",
        "stage": "experiment",
        "evidence_level": "A",
        "scientific_terminal_admitted": True,
        "candidate_id": CANDIDATE_ID,
        "treatment_id": TREATMENT_ID,
        "config_name": analyzed["config_name"],
        "frozen_identity": analyzed["frozen_identity"],
        "terminal_label": analyzed["terminal_label"],
        "historical_control_reuse_passed": True,
        "clean_two_sided_real_support_opened": analyzed["clean_two_sided_real_support_opened"],
        "toy_route_must_park": analyzed["toy_route_must_park"],
        "schedule_delta_receipt": analyzed["schedule_delta_receipt"],
        "matching_receipt": analyzed["matching_receipt"],
        "lineage_receipt": analyzed["lineage_receipt"],
        "outcome_counts": analyzed["outcome_counts"],
        "actual_counts": analyzed["actual_counts"],
        "call_counts": analyzed["call_counts"],
    }


def run_equivalence_smoke(*, control_path: str | Path) -> dict[str, Any]:
    """One control/treatment pair through t40, exactly 82 real transitions."""

    load_accepted_control(control_path)
    cell = CELLS[0]
    task_seed = FULL_TASK_SEEDS[0]
    episode_id = int(_roster(SMOKE_CONFIG)[0]["episode_id"])
    control = TruthReachabilityVectorRuntime.create_cell(
        cell=cell, episode_ids=(episode_id,), task_seed=task_seed
    )
    treatment = LifecyclePhaseVectorRuntime.create_cell(
        cell=cell, episode_ids=(episode_id,), task_seed=task_seed
    )
    try:
        control.advance(19)
        treatment.advance(19)
        pre_checks = {
            "decision_trace_equal_through_t18": _deep_equal(control.decision_trace, treatment.decision_trace),
            "primitive_trace_equal_through_t18": _deep_equal(control.primitive_action_trace, treatment.primitive_action_trace),
            "reward_trace_equal_through_t18": _deep_equal(control.reward_trace, treatment.reward_trace),
            "frontier_rows_equal_through_t18": _deep_equal(control.real_frontier_rows, treatment.real_frontier_rows),
            "environment_ledgers_equal": _deep_equal(
                asdict(control.collector.envs[0].environment.ledger),
                asdict(treatment.collector.envs[0].environment.ledger),
            ),
        }
        treated = tuple(str(value) for value in treatment.collector.envs[0].environment.ledger.temporary_leave)
        control_t19 = {
            key: {
                "active": control.cores[0].records[key].status == CORE_ACTIVE,
                "incumbent_present": control.cores[0].records[key].active_skill is not None,
                "state": control.collector.envs[0].environment.process_states[int(key)].tolist(),
            }
            for key in treated
        }
        control.advance_one()
        treatment.advance_one()
        t19_checks = {
            "control_treated_keys_active_and_incumbent_bearing": all(
                row["active"] and row["incumbent_present"] for row in control_t19.values()
            ),
            "treatment_omits_exactly_two_primitive_actions": (
                set(control.primitive_action_trace[0][19]) - set(treatment.primitive_action_trace[0][19])
                == set(treated)
            ),
            "unchanged_key_actions_equal_at_t19": all(
                treatment.primitive_action_trace[0][19][key] == action
                for key, action in control.primitive_action_trace[0][19].items()
                if key not in treated
            ),
        }
        control.advance(20)
        treatment.advance(20)
        control.advance_one()
        treatment.advance_one()
        audit = treatment.phase_lineage_audits[0]
        rejoin_checks = {
            "leave_and_rejoin_audited": set(audit) == {"leave", "rejoin"},
            "state_did_not_advance_while_absent": all(
                row["state_unchanged_while_absent"] for row in audit["rejoin"].values()
            ),
            "incumbent_not_reset_at_rejoin": all(
                row["incumbent_not_reset"] for row in audit["rejoin"].values()
            ),
            "exactly_one_relative_primitive_skip_each": all(
                row["skipped_primitives_relative_to_control"] == 1
                for row in audit["rejoin"].values()
            ),
            "absence_window_is_t19_through_t39": all(
                row["absent_transition_times"] == list(range(19, 40))
                for row in audit["rejoin"].values()
            ),
        }
        checks = {**pre_checks, **t19_checks, **rejoin_checks}
        return {
            "schema_version": SCHEMA_VERSION,
            "artifact_kind": "VSP05_A2_EQUIVALENCE_SMOKE",
            "stage": "technical_validation",
            "evidence_level": "TECHNICAL_ONLY",
            "technical_only": True,
            "scientific_terminal_admitted": False,
            "control_raw_sha256": CONTROL_RAW_SHA256,
            "cell": cell.name,
            "task_seed": task_seed,
            "episode_id": episode_id,
            "control_environment_transitions": 41,
            "treatment_environment_transitions": 41,
            "total_environment_transitions": 82,
            "cap": 82,
            "all_checks_passed": all(checks.values()),
            "checks": checks,
            "treated_lifecycle_keys": list(treated),
            "control_t19": control_t19,
            "treatment_lineage_audit": audit,
            "hypothetical_environment_transitions": 0,
            "learner_calls": 0,
            "trainer_calls": 0,
            "optimizer_updates": 0,
        }
    finally:
        control.close()
        treatment.close()


def write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("train", "probe", "evaluate", "analyze", "equivalence-smoke"), required=True)
    parser.add_argument("--config", choices=("smoke", "full"))
    parser.add_argument("--control", required=True)
    parser.add_argument("--input")
    parser.add_argument("--output")
    parser.add_argument("--code-revision")
    parser.add_argument("--run-id")
    parser.add_argument("--equivalence-receipt")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.phase == "equivalence-smoke":
        result = run_equivalence_smoke(control_path=args.control)
    elif args.phase in ("train", "probe"):
        if args.config is None:
            raise ValueError("A2 probe/train acquisition requires explicit --config")
        if not args.output:
            raise ValueError("A2 probe/train phase requires --output")
        config = SMOKE_CONFIG if args.config == "smoke" else FULL_CONFIG
        if config is FULL_CONFIG and (
            args.code_revision is None
            or args.run_id is None
            or args.equivalence_receipt is None
        ):
            raise ValueError(
                "full A2 acquisition requires explicit --code-revision, --run-id, "
                "and --equivalence-receipt"
            )
        equivalence = (
            None
            if args.equivalence_receipt is None
            else json.loads(Path(args.equivalence_receipt).read_text(encoding="utf-8"))
        )
        result = run_treatment_probe(
            config,
            control_path=args.control,
            code_revision=args.code_revision or "WORKTREE",
            run_id=args.run_id or "VSP05_A2_SMOKE",
            equivalence_receipt=equivalence,
        )
    else:
        if not args.input or not args.output:
            raise ValueError("A2 evaluate/analyze phase requires --input and --output")
        raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
        control = load_accepted_control(args.control)
        result = (
            evaluate_treatment(raw, control)
            if args.phase == "evaluate"
            else analyze_treatment(raw, control)
        )
    if args.output:
        write_json(args.output, result)
    summary = {
        "phase": args.phase,
        "output": args.output,
        "artifact_kind": result["artifact_kind"],
        "actual_counts": result.get("actual_counts"),
        "all_checks_passed": result.get("all_checks_passed"),
    }
    if "terminal_label" in result:
        summary["terminal_label"] = result["terminal_label"]
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
