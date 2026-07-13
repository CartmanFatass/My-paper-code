"""Frozen R27-G2 forced-label trajectory/effect evidence collection.

The collector is deliberately separate from the training collector.  It loads
frozen R25 checkpoints, replays exact natural-prefix actions into a fresh
environment for every branch, suppresses all high-level renewal after the
branch point, and records one typed shard per independent reset group.
"""

from __future__ import annotations

import json
import random
from collections.abc import Mapping
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np
import torch

from ha_ctse_process.low_actor_capacity_audit import forward_actor_snapshot
from ha_ctse_process.r27_g2_runtime import (
    CanonicalEntry,
    R27G2ContractError,
    assert_runtime_matches_snapshot,
    assert_runtime_snapshots_equal,
    capture_environment_state,
    capture_environment_rng_state,
    capture_global_rng_state,
    capture_module_state,
    capture_runtime_snapshot,
    capture_structured_evidence,
    capture_value_norm_state,
    environment_states_equal,
    global_rng_states_equal,
    module_states_equal,
    restore_runtime_snapshot,
    rng_states_equal,
    runtime_snapshot_differences,
    typed_evidence_equal,
    value_norm_states_equal,
)


N_AGENTS = 6
N_SKILLS = 4
ACTION_DIM = 4
BRANCH_STEPS = 50
BRANCH_COUNT = 55
DIAGNOSTIC_SLOT_COUNT = 60
PARITY_TOLERANCE = 1e-6
INACTIVE_TOLERANCE = 1e-8


@dataclass(frozen=True)
class BranchSpec:
    kind: str
    focal_agent: int
    target_skill: int
    natural_skill: int
    inactive_film: bool = False

    def executed_skill(self, step_index: int) -> int:
        if self.kind == "reference":
            return self.natural_skill
        if self.kind == "pulse" and int(step_index) >= 10:
            return self.natural_skill
        return self.target_skill

    @property
    def is_identity_branch(self) -> bool:
        return bool(
            self.kind == "reference"
            or (self.kind == "hold" and self.target_skill == self.natural_skill)
            or self.kind == "inactive"
        )


def prefix_steps_for_reset(reset_id: int) -> int:
    reset_id = int(reset_id)
    if not 0 <= reset_id < 64:
        raise ValueError("R27-G2 reset_id must be in 0..63")
    return (50, 150, 250)[reset_id % 3]


def prefix_policy_seed_for_reset(reset_id: int) -> int:
    return 27100 + int(reset_id)


def build_branch_specs(natural_roster: np.ndarray) -> tuple[BranchSpec, ...]:
    roster = np.asarray(natural_roster, dtype=np.int64).reshape(-1)
    if roster.shape != (N_AGENTS,) or np.any(roster < 0) or np.any(roster >= N_SKILLS):
        raise ValueError("R27-G2 natural roster must contain six labels in 0..3")
    specs: list[BranchSpec] = [
        BranchSpec("reference", -1, -1, -1, False)
    ]
    for agent_id in range(N_AGENTS):
        natural = int(roster[agent_id])
        for target in range(N_SKILLS):
            specs.append(BranchSpec("hold", agent_id, target, natural, False))
    for agent_id in range(N_AGENTS):
        natural = int(roster[agent_id])
        for target in range(N_SKILLS):
            if target != natural:
                specs.append(BranchSpec("pulse", agent_id, target, natural, False))
    for agent_id in range(N_AGENTS):
        natural = int(roster[agent_id])
        for offset in (1, 2):
            specs.append(
                BranchSpec(
                    "inactive",
                    agent_id,
                    (natural + offset) % N_SKILLS,
                    natural,
                    True,
                )
            )
    if len(specs) != BRANCH_COUNT:
        raise AssertionError("R27-G2 branch construction did not yield 55 branches")
    return tuple(specs)


def build_diagnostic_slots(
    branches: Iterable[BranchSpec],
) -> tuple[np.ndarray, np.ndarray]:
    branch_ids: list[int] = []
    agent_ids: list[int] = []
    for branch_id, branch in enumerate(branches):
        agents = range(N_AGENTS) if branch.kind == "reference" else (branch.focal_agent,)
        for agent_id in agents:
            branch_ids.append(int(branch_id))
            agent_ids.append(int(agent_id))
    if len(branch_ids) != DIAGNOSTIC_SLOT_COUNT:
        raise AssertionError("R27-G2 diagnostic slot construction did not yield 60 slots")
    return np.asarray(branch_ids, dtype=np.int64), np.asarray(agent_ids, dtype=np.int64)


def _state_from_info(info: Any) -> np.ndarray:
    mapping = info if isinstance(info, dict) else {}
    state = mapping.get("next_state", mapping.get("state"))
    if state is None:
        raise R27G2ContractError("R27-G2 environment did not expose global state")
    value = np.asarray(state)
    if value.dtype != np.float32:
        value = value.astype(np.float32)
    value = value.reshape(-1)
    if not np.isfinite(value).all():
        raise R27G2ContractError("R27-G2 environment state contains non-finite values")
    return value


def _require_observation(obs: Any, *, obs_dim: int | None = None) -> np.ndarray:
    value = np.asarray(obs)
    if value.dtype != np.float32:
        value = value.astype(np.float32)
    if value.ndim != 2 or value.shape[0] != N_AGENTS:
        raise R27G2ContractError("R27-G2 observation must have six agent rows")
    if obs_dim is not None and value.shape[1] != int(obs_dim):
        raise R27G2ContractError("R27-G2 observation dimension changed within reset")
    if not np.isfinite(value).all():
        raise R27G2ContractError("R27-G2 observation contains non-finite values")
    return value


def _assert_finite_evidence(value: Any, label: str, seen: set[int] | None = None) -> None:
    """Reject non-finite numeric leaves in rewards and nested info metrics."""

    visited = set() if seen is None else seen
    if value is None or isinstance(value, (str, bytes, bool, int, np.integer)):
        return
    if isinstance(value, (float, np.floating)):
        if not np.isfinite(float(value)):
            raise R27G2ContractError(f"R27-G2 non-finite metric: {label}")
        return
    if isinstance(value, torch.Tensor):
        if value.is_floating_point() and not bool(torch.isfinite(value).all()):
            raise R27G2ContractError(f"R27-G2 non-finite tensor metric: {label}")
        return
    if isinstance(value, np.ndarray):
        if np.issubdtype(value.dtype, np.number) and not np.isfinite(value).all():
            raise R27G2ContractError(f"R27-G2 non-finite array metric: {label}")
        return
    if isinstance(value, Mapping):
        object_id = id(value)
        if object_id in visited:
            return
        visited.add(object_id)
        for key, item in value.items():
            _assert_finite_evidence(item, f"{label}.{key}", visited)
        return
    if isinstance(value, (list, tuple)):
        object_id = id(value)
        if object_id in visited:
            return
        visited.add(object_id)
        for index, item in enumerate(value):
            _assert_finite_evidence(item, f"{label}[{index}]", visited)


def _failure_arrays(info: Any) -> tuple[np.ndarray, ...]:
    if not isinstance(info, Mapping):
        return ()
    arrays: list[np.ndarray] = []
    for container in (info, info.get("state_info")):
        if not isinstance(container, Mapping):
            continue
        for key in ("uav_failed", "energy_failure_mask", "agent_failed"):
            if key in container:
                arrays.append(np.asarray(container[key], dtype=np.bool_).reshape(-1))
    return tuple(arrays)


def _focal_failed(info: Any, focal_agent: int) -> bool:
    for values in _failure_arrays(info):
        if focal_agent < 0 and bool(values.any()):
            return True
        if values.size > focal_agent >= 0 and bool(values[focal_agent]):
            return True
    return False


def validate_agent_source_contract(agent: Any) -> None:
    checks = {
        "n_agents": int(getattr(agent, "n_agents", -1)) == N_AGENTS,
        "n_skills": int(getattr(agent, "n_skills", -1)) == N_SKILLS,
        "action_dim": int(getattr(agent, "action_dim", -1)) == ACTION_DIM,
        "num_envs": int(getattr(agent, "num_envs", -1)) == 1,
        "continuous_action": getattr(agent, "action_space_type", None)
        == "continuous",
        "recurrent_low": bool(getattr(agent, "use_recurrent_low_level", False)),
        "strict_low_class": type(getattr(agent, "low", None)).__name__
        == "StrictHMASDMAPPOLowLevelPolicy",
        "actor_team_conditioning_off": getattr(
            getattr(agent, "low", None), "actor_team_film", None
        )
        is None,
        "tanh_gaussian": type(
            getattr(getattr(getattr(agent, "low", None), "actor_act", None), "action_out", None)
        ).__name__
        == "TanhDiagGaussian",
        "duration_candidates": tuple(
            int(value) for value in getattr(agent, "duration_candidates", ())
        )
        == (1, 2, 3, 4),
        "team_intent_k": int(getattr(agent, "team_intent_k", -1)) == 8,
        "cuda_device": torch.device(getattr(agent, "device", "cpu")).type == "cuda",
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise R27G2ContractError(
            f"R27-G2 registered R25 source contract failed: {failed}"
        )


@dataclass
class R27G2ResetArtifact:
    reset_id: np.ndarray
    reset_seed: np.ndarray
    prefix_policy_seed: np.ndarray
    prefix_steps: np.ndarray
    prefix_action: np.ndarray
    prefix_pre_tanh_mean: np.ndarray
    prefix_log_standard_deviation: np.ndarray
    prefix_skill: np.ndarray
    prefix_duration_index: np.ndarray
    calibration_action: np.ndarray
    calibration_observation: np.ndarray
    branch_kind: np.ndarray
    branch_focal_agent: np.ndarray
    branch_target_skill: np.ndarray
    branch_natural_skill: np.ndarray
    branch_inactive_film: np.ndarray
    branch_completed: np.ndarray
    reference_act_low_parity_abs_error: np.ndarray
    runtime_restored_equal: np.ndarray
    replay_global_rng_equal: np.ndarray
    replay_info_equal: np.ndarray
    replay_environment_equal: np.ndarray
    replay_environment_rng_equal: np.ndarray
    step_valid: np.ndarray
    local_observation: np.ndarray
    global_state: np.ndarray
    joint_action: np.ndarray
    live_pre_tanh_mean: np.ndarray
    live_log_standard_deviation: np.ndarray
    live_log_probability: np.ndarray
    live_value: np.ndarray
    executed_focal_skill: np.ndarray
    diagnostic_branch_id: np.ndarray
    diagnostic_agent_id: np.ndarray
    diagnostic_active_mean: np.ndarray
    diagnostic_active_logstd: np.ndarray
    diagnostic_active_action: np.ndarray
    diagnostic_active_new_hidden: np.ndarray
    diagnostic_inactive_mean: np.ndarray
    diagnostic_inactive_logstd: np.ndarray
    diagnostic_inactive_action: np.ndarray
    diagnostic_inactive_new_hidden: np.ndarray
    live_diagnostic_abs_error: np.ndarray
    frozen_runtime_unchanged: np.ndarray
    environment_rng_equal_reference: np.ndarray
    identity_actor_equal: np.ndarray
    identity_critic_equal: np.ndarray
    identity_info_equal: np.ndarray
    identity_environment_equal: np.ndarray
    module_state_equal: np.ndarray
    value_norm_state_equal: np.ndarray
    global_rng_unchanged: np.ndarray
    branchpoint_focal_failure: np.ndarray
    terminated: np.ndarray
    truncated: np.ndarray
    focal_failure: np.ndarray

    @classmethod
    def allocate(
        cls,
        *,
        reset_id: int,
        prefix_steps: int,
        obs_dim: int,
        hidden_dim: int,
        state_dim: int,
        branches: tuple[BranchSpec, ...],
    ) -> "R27G2ResetArtifact":
        diagnostic_branch_id, diagnostic_agent_id = build_diagnostic_slots(branches)
        b, t, a, k, d, h = (
            BRANCH_COUNT,
            BRANCH_STEPS,
            N_AGENTS,
            N_SKILLS,
            ACTION_DIM,
            int(hidden_dim),
        )
        zeros = np.zeros
        return cls(
            reset_id=np.asarray(int(reset_id), dtype=np.int64),
            reset_seed=np.asarray(int(reset_id) + 1, dtype=np.int64),
            prefix_policy_seed=np.asarray(
                prefix_policy_seed_for_reset(reset_id), dtype=np.int64
            ),
            prefix_steps=np.asarray(int(prefix_steps), dtype=np.int64),
            prefix_action=zeros((prefix_steps, a, d), dtype=np.float32),
            prefix_pre_tanh_mean=zeros((prefix_steps, a, d), dtype=np.float32),
            prefix_log_standard_deviation=zeros(
                (prefix_steps, a, d), dtype=np.float32
            ),
            prefix_skill=zeros((prefix_steps, a), dtype=np.int64),
            prefix_duration_index=zeros((prefix_steps, a), dtype=np.int64),
            calibration_action=zeros((50, a, d), dtype=np.float32),
            calibration_observation=zeros((50, a, obs_dim), dtype=np.float32),
            branch_kind=np.asarray([item.kind for item in branches], dtype="<U12"),
            branch_focal_agent=np.asarray(
                [item.focal_agent for item in branches], dtype=np.int64
            ),
            branch_target_skill=np.asarray(
                [item.target_skill for item in branches], dtype=np.int64
            ),
            branch_natural_skill=np.asarray(
                [item.natural_skill for item in branches], dtype=np.int64
            ),
            branch_inactive_film=np.asarray(
                [item.inactive_film for item in branches], dtype=np.bool_
            ),
            branch_completed=zeros(b, dtype=np.bool_),
            reference_act_low_parity_abs_error=zeros((t, 5), dtype=np.float32),
            runtime_restored_equal=zeros(b, dtype=np.bool_),
            replay_global_rng_equal=zeros(b, dtype=np.bool_),
            replay_info_equal=zeros(b, dtype=np.bool_),
            replay_environment_equal=zeros(b, dtype=np.bool_),
            replay_environment_rng_equal=zeros(b, dtype=np.bool_),
            step_valid=zeros((b, t), dtype=np.bool_),
            local_observation=zeros((b, t + 1, a, obs_dim), dtype=np.float32),
            global_state=zeros(
                (b, t + 1, int(state_dim)), dtype=np.float32
            ),
            joint_action=zeros((b, t, a, d), dtype=np.float32),
            live_pre_tanh_mean=zeros((b, t, a, d), dtype=np.float32),
            live_log_standard_deviation=zeros((b, t, a, d), dtype=np.float32),
            live_log_probability=zeros((b, t, a), dtype=np.float32),
            live_value=zeros((b, t, a), dtype=np.float32),
            executed_focal_skill=np.full((b, t), -1, dtype=np.int64),
            diagnostic_branch_id=diagnostic_branch_id,
            diagnostic_agent_id=diagnostic_agent_id,
            diagnostic_active_mean=zeros((DIAGNOSTIC_SLOT_COUNT, t, k, d), dtype=np.float32),
            diagnostic_active_logstd=zeros((DIAGNOSTIC_SLOT_COUNT, t, k, d), dtype=np.float32),
            diagnostic_active_action=zeros((DIAGNOSTIC_SLOT_COUNT, t, k, d), dtype=np.float32),
            diagnostic_active_new_hidden=zeros(
                (DIAGNOSTIC_SLOT_COUNT, t, k, h), dtype=np.float32
            ),
            diagnostic_inactive_mean=zeros((DIAGNOSTIC_SLOT_COUNT, t, k, d), dtype=np.float32),
            diagnostic_inactive_logstd=zeros((DIAGNOSTIC_SLOT_COUNT, t, k, d), dtype=np.float32),
            diagnostic_inactive_action=zeros((DIAGNOSTIC_SLOT_COUNT, t, k, d), dtype=np.float32),
            diagnostic_inactive_new_hidden=zeros(
                (DIAGNOSTIC_SLOT_COUNT, t, k, h), dtype=np.float32
            ),
            live_diagnostic_abs_error=zeros(
                (DIAGNOSTIC_SLOT_COUNT, t, 3), dtype=np.float32
            ),
            frozen_runtime_unchanged=zeros((b, t), dtype=np.bool_),
            environment_rng_equal_reference=zeros((b, t + 1), dtype=np.bool_),
            identity_actor_equal=zeros((b, t), dtype=np.bool_),
            identity_critic_equal=zeros((b, t), dtype=np.bool_),
            identity_info_equal=zeros((b, t + 1), dtype=np.bool_),
            identity_environment_equal=zeros((b, t + 1), dtype=np.bool_),
            module_state_equal=np.asarray(False, dtype=np.bool_),
            value_norm_state_equal=np.asarray(False, dtype=np.bool_),
            global_rng_unchanged=zeros((b, t), dtype=np.bool_),
            branchpoint_focal_failure=zeros(b, dtype=np.bool_),
            terminated=zeros((b, t), dtype=np.bool_),
            truncated=zeros((b, t), dtype=np.bool_),
            focal_failure=zeros((b, t), dtype=np.bool_),
        )

    def validate(self) -> None:
        if int(self.reset_seed) != int(self.reset_id) + 1:
            raise R27G2ContractError("R27-G2 reset seed does not equal reset_id + 1")
        if int(self.prefix_policy_seed) != prefix_policy_seed_for_reset(int(self.reset_id)):
            raise R27G2ContractError("R27-G2 prefix policy seed mismatch")
        if int(self.prefix_steps) != prefix_steps_for_reset(int(self.reset_id)):
            raise R27G2ContractError("R27-G2 prefix length mismatch")
        if self.branch_kind.shape != (BRANCH_COUNT,):
            raise R27G2ContractError("R27-G2 artifact does not contain 55 branches")
        counts = {
            kind: int(np.sum(self.branch_kind == kind))
            for kind in ("reference", "hold", "pulse", "inactive")
        }
        if counts != {"reference": 1, "hold": 24, "pulse": 18, "inactive": 12}:
            raise R27G2ContractError(f"R27-G2 branch matrix mismatch: {counts}")
        if self.diagnostic_branch_id.shape != (DIAGNOSTIC_SLOT_COUNT,) or self.diagnostic_agent_id.shape != (
            DIAGNOSTIC_SLOT_COUNT,
        ):
            raise R27G2ContractError("R27-G2 diagnostic slot matrix mismatch")
        prefix = int(self.prefix_steps)
        obs_dim = int(self.calibration_observation.shape[-1])
        hidden_dim = int(self.diagnostic_active_new_hidden.shape[-1])
        state_dim = int(self.global_state.shape[-1])
        expected_shapes = {
            "prefix_action": (prefix, N_AGENTS, ACTION_DIM),
            "prefix_pre_tanh_mean": (prefix, N_AGENTS, ACTION_DIM),
            "prefix_log_standard_deviation": (prefix, N_AGENTS, ACTION_DIM),
            "prefix_skill": (prefix, N_AGENTS),
            "prefix_duration_index": (prefix, N_AGENTS),
            "branch_focal_agent": (BRANCH_COUNT,),
            "branch_target_skill": (BRANCH_COUNT,),
            "branch_natural_skill": (BRANCH_COUNT,),
            "branch_inactive_film": (BRANCH_COUNT,),
            "branch_completed": (BRANCH_COUNT,),
            "reference_act_low_parity_abs_error": (BRANCH_STEPS, 5),
            "runtime_restored_equal": (BRANCH_COUNT,),
            "replay_global_rng_equal": (BRANCH_COUNT,),
            "replay_info_equal": (BRANCH_COUNT,),
            "replay_environment_equal": (BRANCH_COUNT,),
            "replay_environment_rng_equal": (BRANCH_COUNT,),
            "step_valid": (BRANCH_COUNT, BRANCH_STEPS),
            "local_observation": (
                BRANCH_COUNT,
                BRANCH_STEPS + 1,
                N_AGENTS,
                obs_dim,
            ),
            "global_state": (
                BRANCH_COUNT,
                BRANCH_STEPS + 1,
                state_dim,
            ),
            "joint_action": (
                BRANCH_COUNT,
                BRANCH_STEPS,
                N_AGENTS,
                ACTION_DIM,
            ),
            "live_pre_tanh_mean": (
                BRANCH_COUNT,
                BRANCH_STEPS,
                N_AGENTS,
                ACTION_DIM,
            ),
            "live_log_standard_deviation": (
                BRANCH_COUNT,
                BRANCH_STEPS,
                N_AGENTS,
                ACTION_DIM,
            ),
            "live_log_probability": (
                BRANCH_COUNT,
                BRANCH_STEPS,
                N_AGENTS,
            ),
            "live_value": (BRANCH_COUNT, BRANCH_STEPS, N_AGENTS),
            "executed_focal_skill": (BRANCH_COUNT, BRANCH_STEPS),
            "diagnostic_active_mean": (
                DIAGNOSTIC_SLOT_COUNT,
                BRANCH_STEPS,
                N_SKILLS,
                ACTION_DIM,
            ),
            "diagnostic_active_logstd": (
                DIAGNOSTIC_SLOT_COUNT,
                BRANCH_STEPS,
                N_SKILLS,
                ACTION_DIM,
            ),
            "diagnostic_active_action": (
                DIAGNOSTIC_SLOT_COUNT,
                BRANCH_STEPS,
                N_SKILLS,
                ACTION_DIM,
            ),
            "diagnostic_active_new_hidden": (
                DIAGNOSTIC_SLOT_COUNT,
                BRANCH_STEPS,
                N_SKILLS,
                hidden_dim,
            ),
            "diagnostic_inactive_mean": (
                DIAGNOSTIC_SLOT_COUNT,
                BRANCH_STEPS,
                N_SKILLS,
                ACTION_DIM,
            ),
            "diagnostic_inactive_logstd": (
                DIAGNOSTIC_SLOT_COUNT,
                BRANCH_STEPS,
                N_SKILLS,
                ACTION_DIM,
            ),
            "diagnostic_inactive_action": (
                DIAGNOSTIC_SLOT_COUNT,
                BRANCH_STEPS,
                N_SKILLS,
                ACTION_DIM,
            ),
            "diagnostic_inactive_new_hidden": (
                DIAGNOSTIC_SLOT_COUNT,
                BRANCH_STEPS,
                N_SKILLS,
                hidden_dim,
            ),
            "live_diagnostic_abs_error": (
                DIAGNOSTIC_SLOT_COUNT,
                BRANCH_STEPS,
                3,
            ),
            "frozen_runtime_unchanged": (BRANCH_COUNT, BRANCH_STEPS),
            "environment_rng_equal_reference": (
                BRANCH_COUNT,
                BRANCH_STEPS + 1,
            ),
            "identity_actor_equal": (BRANCH_COUNT, BRANCH_STEPS),
            "identity_critic_equal": (BRANCH_COUNT, BRANCH_STEPS),
            "identity_info_equal": (
                BRANCH_COUNT,
                BRANCH_STEPS + 1,
            ),
            "identity_environment_equal": (
                BRANCH_COUNT,
                BRANCH_STEPS + 1,
            ),
            "module_state_equal": (),
            "value_norm_state_equal": (),
            "global_rng_unchanged": (BRANCH_COUNT, BRANCH_STEPS),
            "branchpoint_focal_failure": (BRANCH_COUNT,),
            "terminated": (BRANCH_COUNT, BRANCH_STEPS),
            "truncated": (BRANCH_COUNT, BRANCH_STEPS),
            "focal_failure": (BRANCH_COUNT, BRANCH_STEPS),
        }
        for name, expected_shape in expected_shapes.items():
            if np.asarray(getattr(self, name)).shape != expected_shape:
                raise R27G2ContractError(
                    f"R27-G2 field shape mismatch {name}: "
                    f"expected={expected_shape} actual={np.asarray(getattr(self, name)).shape}"
                )
        if self.calibration_action.shape != (50, N_AGENTS, ACTION_DIM):
            raise R27G2ContractError("R27-G2 action calibration shape mismatch")
        if self.calibration_observation.shape[:2] != (50, N_AGENTS):
            raise R27G2ContractError("R27-G2 observation calibration shape mismatch")
        for item in fields(self):
            value = np.asarray(getattr(self, item.name))
            if value.dtype == object:
                raise R27G2ContractError(f"R27-G2 object array is forbidden: {item.name}")
            if np.issubdtype(value.dtype, np.floating) and not np.isfinite(value).all():
                raise R27G2ContractError(f"R27-G2 non-finite artifact field: {item.name}")
        if not np.isfinite(self.calibration_action).all() or not np.isfinite(
            self.calibration_observation
        ).all():
            raise R27G2ContractError("R27-G2 calibration contains non-finite rows")
        expected_branches = build_branch_specs(self.prefix_skill[-1])
        expected_kind = np.asarray([item.kind for item in expected_branches])
        expected_focal = np.asarray([item.focal_agent for item in expected_branches])
        expected_target = np.asarray([item.target_skill for item in expected_branches])
        expected_natural = np.asarray([item.natural_skill for item in expected_branches])
        expected_inactive = np.asarray([item.inactive_film for item in expected_branches])
        for name, actual, expected in (
            ("branch_kind", self.branch_kind, expected_kind),
            ("branch_focal_agent", self.branch_focal_agent, expected_focal),
            ("branch_target_skill", self.branch_target_skill, expected_target),
            ("branch_natural_skill", self.branch_natural_skill, expected_natural),
            ("branch_inactive_film", self.branch_inactive_film, expected_inactive),
        ):
            if not np.array_equal(actual, expected):
                raise R27G2ContractError(f"R27-G2 frozen branch ordering mismatch: {name}")
        expected_diag_branch, expected_diag_agent = build_diagnostic_slots(
            expected_branches
        )
        if not np.array_equal(
            self.diagnostic_branch_id, expected_diag_branch
        ) or not np.array_equal(self.diagnostic_agent_id, expected_diag_agent):
            raise R27G2ContractError("R27-G2 diagnostic slot ordering mismatch")
        expected_executed = np.full(
            (BRANCH_COUNT, BRANCH_STEPS), -1, dtype=np.int64
        )
        for branch_id, branch in enumerate(expected_branches):
            hook_focal = 0 if branch.kind == "reference" else branch.focal_agent
            for step in range(BRANCH_STEPS):
                expected_executed[branch_id, step] = (
                    int(self.prefix_skill[-1, hook_focal])
                    if branch.kind == "reference"
                    else branch.executed_skill(step)
                )
        if not np.array_equal(
            self.executed_focal_skill[self.step_valid],
            expected_executed[self.step_valid],
        ):
            raise R27G2ContractError("R27-G2 executed focal-label schedule mismatch")
        if not np.array_equal(
            self.calibration_action,
            np.tanh(self.prefix_pre_tanh_mean[-50:]).astype(np.float32),
        ):
            raise R27G2ContractError("R27-G2 action calibration is not tanh(prefix mean)")
        if np.any(self.branch_completed & ~np.all(self.step_valid, axis=1)):
            raise R27G2ContractError("R27-G2 completed branch has missing steps")
        if np.any(
            (self.terminated | self.truncated | self.focal_failure)
            & ~self.step_valid
        ):
            raise R27G2ContractError(
                "R27-G2 boundary/failure event exists outside valid evidence steps"
            )
        if self.branch_completed[0] and float(
            self.reference_act_low_parity_abs_error.max()
        ) > PARITY_TOLERANCE:
            raise R27G2ContractError("R27-G2 source act_low parity evidence failed")
        completed = self.branch_completed.astype(np.bool_)
        if np.any(completed & ~self.runtime_restored_equal):
            raise R27G2ContractError(
                "R27-G2 completed branch has a restored-runtime mismatch"
            )
        if np.any(completed & ~self.replay_global_rng_equal):
            raise R27G2ContractError(
                "R27-G2 completed branch has a replay-global-RNG mismatch"
            )
        if np.any(
            completed
            & ~(
                self.replay_info_equal
                & self.replay_environment_equal
                & self.replay_environment_rng_equal
            )
        ):
            raise R27G2ContractError(
                "R27-G2 completed branch has a fresh-replay state mismatch"
            )
        if np.any(
            completed & ~np.all(self.global_rng_unchanged, axis=1)
        ):
            raise R27G2ContractError(
                "R27-G2 completed branch contains a global-RNG preservation failure"
            )
        if np.any(self.step_valid) and not bool(
            self.module_state_equal & self.value_norm_state_equal
        ):
            raise R27G2ContractError(
                "R27-G2 reset changed frozen module inference state"
            )
        if np.any(completed & ~np.all(self.frozen_runtime_unchanged, axis=1)):
            raise R27G2ContractError(
                "R27-G2 completed branch changed frozen non-neural runtime"
            )
        if bool(np.all(completed)):
            matched_mask = np.isin(self.branch_kind, ("hold", "pulse"))
            if not bool(
                np.all(self.environment_rng_equal_reference[matched_mask, :41])
            ):
                raise R27G2ContractError(
                    "R27-G2 matched environment RNG differs through H40"
                )
            identity_mask = (
                (self.branch_kind == "reference")
                | (
                    (self.branch_kind == "hold")
                    & (self.branch_target_skill == self.branch_natural_skill)
                )
                | (self.branch_kind == "inactive")
            )
            identity_checks = (
                ("actor", self.identity_actor_equal[identity_mask]),
                ("critic", self.identity_critic_equal[identity_mask]),
                ("info", self.identity_info_equal[identity_mask]),
                ("environment", self.identity_environment_equal[identity_mask]),
            )
            for label, evidence in identity_checks:
                if not bool(np.all(evidence)):
                    raise R27G2ContractError(
                        f"R27-G2 completed identity branch differs: {label}"
                    )

    def write(self, path: str | Path) -> Path:
        self.validate()
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            target,
            **{item.name: np.asarray(getattr(self, item.name)) for item in fields(self)},
        )
        return target

    @classmethod
    def read(cls, path: str | Path) -> "R27G2ResetArtifact":
        with np.load(Path(path), allow_pickle=False) as payload:
            expected = {item.name for item in fields(cls)}
            if set(payload.files) != expected:
                missing = sorted(expected - set(payload.files))
                extra = sorted(set(payload.files) - expected)
                raise R27G2ContractError(
                    f"R27-G2 shard field mismatch missing={missing} extra={extra}"
                )
            artifact = cls(**{name: payload[name].copy() for name in expected})
        artifact.validate()
        return artifact


def _diagnostic_forward(
    actor: Any,
    observation: np.ndarray,
    hidden: np.ndarray,
    *,
    inactive_film: bool,
) -> dict[str, np.ndarray]:
    obs_batch = np.repeat(np.asarray(observation, dtype=np.float32)[None, :], N_SKILLS, axis=0)
    hidden_batch = np.repeat(np.asarray(hidden, dtype=np.float32)[None, :], N_SKILLS, axis=0)
    result = forward_actor_snapshot(
        actor,
        torch.as_tensor(obs_batch, dtype=torch.float32, device=actor.device),
        torch.arange(N_SKILLS, dtype=torch.long, device=actor.device),
        torch.as_tensor(hidden_batch, dtype=torch.float32, device=actor.device),
        inactive_film=bool(inactive_film),
    )
    output = {
        "mean": result.action_mean.cpu().numpy().astype(np.float32),
        "logstd": result.action_logstd.cpu().numpy().astype(np.float32),
        "action": result.deterministic_action.cpu().numpy().astype(np.float32),
        "new_hidden": result.new_hidden.cpu().numpy().astype(np.float32),
    }
    if any(not np.isfinite(value).all() for value in output.values()):
        raise R27G2ContractError("R27-G2 diagnostic forward contains non-finite values")
    return output


def _assert_exact_array(label: str, actual: np.ndarray, expected: np.ndarray) -> None:
    if np.asarray(actual).dtype != np.asarray(expected).dtype or not np.array_equal(
        actual, expected
    ):
        raise R27G2ContractError(f"R27-G2 exact parity failed: {label}")


def _array_tuple_equal(
    left: tuple[np.ndarray, ...], right: tuple[np.ndarray, ...]
) -> bool:
    if len(left) != len(right):
        return False
    return all(
        np.asarray(left_value).dtype == np.asarray(right_value).dtype
        and np.array_equal(left_value, right_value)
        for left_value, right_value in zip(left, right)
    )


def _array_tuple_sequence_equal(
    left: list[tuple[np.ndarray, ...]], right: list[tuple[np.ndarray, ...]]
) -> np.ndarray:
    if len(left) != len(right):
        return np.zeros(max(len(left), len(right)), dtype=np.bool_)
    return np.asarray(
        [_array_tuple_equal(a, b) for a, b in zip(left, right)], dtype=np.bool_
    )


def _write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


@dataclass(frozen=True)
class ResetCollectionResult:
    artifact: R27G2ResetArtifact
    manifest: dict[str, Any]


def collect_reset_evidence(
    *,
    env_factory: Callable[[], Any],
    agent: Any,
    reset_id: int,
    checkpoint_id: str,
    checkpoint_update: int,
    checkpoint_path: str | Path,
) -> ResetCollectionResult:
    """Collect the exact 55-branch Stage-1 matrix for one reset group."""

    reset_id = int(reset_id)
    validate_agent_source_contract(agent)
    checkpoint_path = Path(checkpoint_path)
    if not checkpoint_path.is_file():
        raise R27G2ContractError(
            f"R27-G2 checkpoint path is not a regular file: {checkpoint_path}"
        )
    module_state_snapshot = capture_module_state(agent)
    value_norm_state_snapshot = capture_value_norm_state(agent)
    prefix_steps = prefix_steps_for_reset(reset_id)
    reset_seed = reset_id + 1
    policy_seed = prefix_policy_seed_for_reset(reset_id)
    prefix_env = env_factory()
    invalid_reasons: list[str] = []
    excluded_reason: str | None = None
    try:
        obs, info = prefix_env.reset(seed=reset_seed)
        _assert_finite_evidence(info, "prefix.reset.info")
        obs = _require_observation(obs)
        state = _state_from_info(info)
        agent.reset_env_state(0)
        if hasattr(agent.segments, "active"):
            agent.segments.active[0] = [None for _ in range(N_AGENTS)]
        random.seed(policy_seed)
        np.random.seed(policy_seed)
        torch.manual_seed(policy_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(policy_seed)

        prefix_actions: list[np.ndarray] = []
        prefix_means: list[np.ndarray] = []
        prefix_logstds: list[np.ndarray] = []
        prefix_skills: list[np.ndarray] = []
        prefix_durations: list[np.ndarray] = []
        prefix_observations: list[np.ndarray] = []
        for step in range(prefix_steps):
            prefix_observations.append(obs.copy())
            with torch.no_grad():
                agent.maybe_assign_skills(
                    obs,
                    state=state,
                    step=step,
                    k=10,
                    env_id=0,
                    deterministic=False,
                )
            preview = forward_actor_snapshot(
                agent.low,
                torch.as_tensor(obs, dtype=torch.float32, device=agent.device),
                torch.as_tensor(
                    agent.active_skills[0], dtype=torch.long, device=agent.device
                ),
                torch.as_tensor(
                    agent.low_actor_hxs[0], dtype=torch.float32, device=agent.device
                ),
                inactive_film=False,
            )
            actions, _logp, _values = agent.act_low(
                obs, env_id=0, deterministic=False, state=state
            )
            actions = np.asarray(actions)
            if actions.dtype != np.float32 or actions.shape != (
                N_AGENTS,
                ACTION_DIM,
            ):
                raise R27G2ContractError("R27-G2 prefix action shape/dtype mismatch")
            np.testing.assert_allclose(
                preview.new_hidden.cpu().numpy(),
                agent.low_actor_hxs[0],
                atol=PARITY_TOLERANCE,
                rtol=PARITY_TOLERANCE,
            )
            prefix_actions.append(actions.copy())
            prefix_means.append(preview.action_mean.cpu().numpy().astype(np.float32))
            prefix_logstds.append(preview.action_logstd.cpu().numpy().astype(np.float32))
            prefix_skills.append(np.asarray(agent.active_skills[0], dtype=np.int64).copy())
            prefix_durations.append(
                np.asarray(agent.active_duration_indices[0], dtype=np.int64).copy()
            )
            next_obs, reward, terminated, truncated, next_info = prefix_env.step(
                actions
            )
            _assert_finite_evidence(reward, f"prefix.step[{step}].reward")
            _assert_finite_evidence(next_info, f"prefix.step[{step}].info")
            if bool(terminated or truncated):
                raise R27G2ContractError(
                    "R27-G2 prefix ended before the registered branch point"
                )
            obs = _require_observation(next_obs, obs_dim=obs.shape[1])
            state = _state_from_info(next_info)
            info = next_info

        canonical_obs = obs.copy()
        canonical_state = state.copy()
        canonical_info = capture_structured_evidence(info)
        canonical_environment = capture_environment_state(prefix_env)
        canonical_environment_rng = capture_environment_rng_state(prefix_env)
        canonical_global_rng = capture_global_rng_state()
        canonical_runtime = capture_runtime_snapshot(agent)
        frozen_runtime_keys = tuple(
            name
            for name in canonical_runtime
            if name
            not in {"low_actor_hxs", "low_critic_hxs", "_last_low_context"}
        )
        canonical_frozen_runtime = {
            name: canonical_runtime[name] for name in frozen_runtime_keys
        }
        natural_roster = np.asarray(agent.active_skills[0], dtype=np.int64).copy()
        branches = build_branch_specs(natural_roster)
        artifact = R27G2ResetArtifact.allocate(
            reset_id=reset_id,
            prefix_steps=prefix_steps,
            obs_dim=int(obs.shape[1]),
            hidden_dim=int(agent.low_actor_hxs.shape[-1]),
            state_dim=int(state.size),
            branches=branches,
        )
        artifact.prefix_action[:] = np.stack(prefix_actions)
        artifact.prefix_pre_tanh_mean[:] = np.stack(prefix_means)
        artifact.prefix_log_standard_deviation[:] = np.stack(prefix_logstds)
        artifact.prefix_skill[:] = np.stack(prefix_skills)
        artifact.prefix_duration_index[:] = np.stack(prefix_durations)
        artifact.calibration_action[:] = np.tanh(
            np.asarray(prefix_means[-50:], dtype=np.float32)
        )
        artifact.calibration_observation[:] = np.asarray(
            prefix_observations[-50:], dtype=np.float32
        )
    finally:
        prefix_env.close()

    diagnostic_slots = {
        (int(branch_id), int(agent_id)): slot
        for slot, (branch_id, agent_id) in enumerate(
            zip(artifact.diagnostic_branch_id, artifact.diagnostic_agent_id)
        )
    }
    reference_environment_rng: list[Any] | None = None
    identity_actor_evidence: dict[int, list[tuple[np.ndarray, ...]]] = {}
    identity_critic_evidence: dict[int, list[tuple[np.ndarray, ...]]] = {}
    identity_info_evidence: dict[int, list[tuple[CanonicalEntry, ...]]] = {}
    identity_environment_evidence: dict[int, list[Any]] = {}
    try:
        for branch_id, branch in enumerate(branches):
            if not global_rng_states_equal(
                capture_global_rng_state(), canonical_global_rng
            ):
                raise R27G2ContractError(
                    "R27-G2 global RNG changed before fresh replay"
                )
            env = env_factory()
            try:
                replay_obs, replay_info = env.reset(seed=reset_seed)
                _assert_finite_evidence(
                    replay_info, f"branch[{branch_id}].reset.info"
                )
                replay_obs = _require_observation(replay_obs, obs_dim=canonical_obs.shape[1])
                replay_state = _state_from_info(replay_info)
                for replay_step, replay_action in enumerate(artifact.prefix_action):
                    replay_obs, replay_reward, replay_terminated, replay_truncated, replay_info = env.step(
                        replay_action
                    )
                    _assert_finite_evidence(
                        replay_reward,
                        f"branch[{branch_id}].replay[{replay_step}].reward",
                    )
                    _assert_finite_evidence(
                        replay_info,
                        f"branch[{branch_id}].replay[{replay_step}].info",
                    )
                    if bool(replay_terminated or replay_truncated):
                        raise R27G2ContractError(
                            "R27-G2 fresh replay ended before the branch point"
                        )
                    replay_obs = _require_observation(
                        replay_obs, obs_dim=canonical_obs.shape[1]
                    )
                    replay_state = _state_from_info(replay_info)
                _assert_exact_array("replay observation", replay_obs, canonical_obs)
                _assert_exact_array("replay state", replay_state, canonical_state)
                artifact.replay_info_equal[branch_id] = bool(
                    capture_structured_evidence(replay_info) == canonical_info
                )
                if not artifact.replay_info_equal[branch_id]:
                    raise R27G2ContractError("R27-G2 replay info parity failed")
                artifact.replay_environment_equal[branch_id] = bool(
                    environment_states_equal(
                        capture_environment_state(env), canonical_environment
                    )
                )
                if not artifact.replay_environment_equal[branch_id]:
                    raise R27G2ContractError("R27-G2 replay environment state mismatch")
                branchpoint_environment_rng = capture_environment_rng_state(env)
                artifact.replay_environment_rng_equal[branch_id] = bool(
                    rng_states_equal(
                        branchpoint_environment_rng, canonical_environment_rng
                    )
                )
                if not artifact.replay_environment_rng_equal[branch_id]:
                    raise R27G2ContractError("R27-G2 replay environment RNG mismatch")
                replay_global_rng = capture_global_rng_state()
                artifact.replay_global_rng_equal[branch_id] = bool(
                    global_rng_states_equal(replay_global_rng, canonical_global_rng)
                )
                if not artifact.replay_global_rng_equal[branch_id]:
                    raise R27G2ContractError(
                        "R27-G2 fresh replay consumed global RNG state"
                    )

                restore_runtime_snapshot(agent, canonical_runtime)
                restored_runtime = capture_runtime_snapshot(agent)
                artifact.runtime_restored_equal[branch_id] = bool(
                    not runtime_snapshot_differences(
                        restored_runtime, canonical_runtime
                    )
                )
                if not artifact.runtime_restored_equal[branch_id]:
                    raise R27G2ContractError(
                        "R27-G2 restored runtime mismatch before branch"
                    )
                artifact.local_observation[branch_id, 0] = replay_obs
                artifact.global_state[branch_id, 0] = replay_state
                branch_environment_rng = [branchpoint_environment_rng]
                if reference_environment_rng is None:
                    artifact.environment_rng_equal_reference[branch_id, 0] = True
                else:
                    artifact.environment_rng_equal_reference[branch_id, 0] = bool(
                        rng_states_equal(
                            branchpoint_environment_rng,
                            reference_environment_rng[0],
                        )
                    )
                if branch.is_identity_branch:
                    identity_actor_evidence[branch_id] = []
                    identity_critic_evidence[branch_id] = []
                    identity_info_evidence[branch_id] = [
                        capture_structured_evidence(replay_info)
                    ]
                    identity_environment_evidence[branch_id] = [
                        capture_environment_state(env)
                    ]

                artifact.branchpoint_focal_failure[branch_id] = _focal_failed(
                    replay_info, branch.focal_agent
                )
                if artifact.branchpoint_focal_failure[branch_id]:
                    excluded_reason = (
                        f"branch={branch_id} branchpoint "
                        "terminated=False truncated=False focal_failure=True"
                    )
                    break

                for step in range(BRANCH_STEPS):
                    global_rng_before = capture_global_rng_state()
                    diagnostic_agents = (
                        range(N_AGENTS)
                        if branch.kind == "reference"
                        else (branch.focal_agent,)
                    )
                    for diagnostic_agent in diagnostic_agents:
                        slot = diagnostic_slots[(branch_id, int(diagnostic_agent))]
                        active = _diagnostic_forward(
                            agent.low,
                            replay_obs[diagnostic_agent],
                            agent.low_actor_hxs[0, diagnostic_agent],
                            inactive_film=False,
                        )
                        inactive = _diagnostic_forward(
                            agent.low,
                            replay_obs[diagnostic_agent],
                            agent.low_actor_hxs[0, diagnostic_agent],
                            inactive_film=True,
                        )
                        artifact.diagnostic_active_mean[slot, step] = active["mean"]
                        artifact.diagnostic_active_logstd[slot, step] = active["logstd"]
                        artifact.diagnostic_active_action[slot, step] = active["action"]
                        artifact.diagnostic_active_new_hidden[slot, step] = active[
                            "new_hidden"
                        ]
                        artifact.diagnostic_inactive_mean[slot, step] = inactive["mean"]
                        artifact.diagnostic_inactive_logstd[slot, step] = inactive[
                            "logstd"
                        ]
                        artifact.diagnostic_inactive_action[slot, step] = inactive[
                            "action"
                        ]
                        artifact.diagnostic_inactive_new_hidden[slot, step] = inactive[
                            "new_hidden"
                        ]
                        for diagnostic_name, diagnostic_value in inactive.items():
                            spread = np.max(
                                np.abs(
                                    diagnostic_value
                                    - diagnostic_value[0:1]
                                )
                            )
                            if float(spread) > INACTIVE_TOLERANCE:
                                raise R27G2ContractError(
                                    "R27-G2 inactive diagnostic label leakage "
                                    f"field={diagnostic_name} spread={float(spread)}"
                                )
                    hook_focal = 0 if branch.kind == "reference" else branch.focal_agent
                    focal_skill = (
                        None
                        if branch.kind == "reference"
                        else branch.executed_skill(step)
                    )
                    pre_audit_runtime = (
                        capture_runtime_snapshot(agent)
                        if branch.kind == "reference"
                        else None
                    )
                    live = agent.r27_g2_audit_step(
                        replay_obs,
                        env_id=0,
                        state=replay_state,
                        focal_agent=hook_focal,
                        focal_skill=focal_skill,
                        focal_inactive_film=branch.inactive_film,
                    )
                    _assert_finite_evidence(
                        live, f"branch[{branch_id}].step[{step}].live"
                    )
                    visible_skills = np.asarray(live["visible_skills"], dtype=np.int64)
                    expected_visible = natural_roster.copy()
                    if branch.kind != "reference":
                        expected_visible[branch.focal_agent] = branch.executed_skill(step)
                    if not np.array_equal(visible_skills, expected_visible):
                        raise R27G2ContractError(
                            "R27-G2 actor-visible roster is not the exact focal-only schedule"
                        )
                    if int(live["focal_skill"]) != int(expected_visible[hook_focal]):
                        raise R27G2ContractError(
                            "R27-G2 executed focal label does not match frozen schedule"
                        )
                    if (
                        np.asarray(live["deterministic_action"]).dtype != np.float32
                        or np.asarray(live["deterministic_action"]).shape
                        != (N_AGENTS, ACTION_DIM)
                    ):
                        raise R27G2ContractError(
                            "R27-G2 live action shape/dtype mismatch"
                        )
                    if branch.kind == "reference":
                        post_audit_runtime = capture_runtime_snapshot(agent)
                        restore_runtime_snapshot(agent, pre_audit_runtime)
                        source_action, source_logp, source_value = agent.act_low(
                            replay_obs,
                            env_id=0,
                            deterministic=True,
                            state=replay_state,
                        )
                        post_source_runtime = capture_runtime_snapshot(agent)
                        parity_errors = np.asarray(
                            [
                                np.max(np.abs(source_action - live["deterministic_action"])),
                                np.max(np.abs(source_logp - live["log_probability"])),
                                np.max(np.abs(source_value - live["value"])),
                                np.max(
                                    np.abs(
                                        agent.low_actor_hxs[0]
                                        - live["new_actor_hxs"]
                                    )
                                ),
                                np.max(
                                    np.abs(
                                        agent.low_critic_hxs[0]
                                        - live["new_critic_hxs"]
                                    )
                                ),
                            ],
                            dtype=np.float32,
                        )
                        artifact.reference_act_low_parity_abs_error[step] = parity_errors
                        if float(parity_errors.max()) > PARITY_TOLERANCE:
                            raise R27G2ContractError(
                                "R27-G2 registered act_low parity tolerance exceeded"
                            )
                        assert_runtime_snapshots_equal(
                            post_source_runtime, post_audit_runtime
                        )
                        restore_runtime_snapshot(agent, post_audit_runtime)
                        assert_runtime_matches_snapshot(agent, post_audit_runtime)
                    artifact.frozen_runtime_unchanged[branch_id, step] = bool(
                        typed_evidence_equal(
                            {
                                name: getattr(agent, name)
                                for name in frozen_runtime_keys
                            },
                            canonical_frozen_runtime,
                        )
                    )
                    if not artifact.frozen_runtime_unchanged[branch_id, step]:
                        raise R27G2ContractError(
                            "R27-G2 audit step mutated roster, clocks, or non-neural runtime"
                        )
                    artifact.live_pre_tanh_mean[branch_id, step] = live[
                        "pre_tanh_mean"
                    ]
                    artifact.live_log_standard_deviation[branch_id, step] = live[
                        "log_standard_deviation"
                    ]
                    artifact.live_log_probability[branch_id, step] = live[
                        "log_probability"
                    ]
                    artifact.live_value[branch_id, step] = live["value"]
                    artifact.joint_action[branch_id, step] = live[
                        "deterministic_action"
                    ]
                    artifact.executed_focal_skill[branch_id, step] = int(
                        live["focal_skill"]
                    )
                    if branch.is_identity_branch:
                        identity_actor_evidence[branch_id].append(
                            tuple(
                                np.asarray(value).copy()
                                for value in (
                                    live["pre_tanh_mean"],
                                    live["log_standard_deviation"],
                                    live["deterministic_action"],
                                    live["log_probability"],
                                    live["new_actor_hxs"],
                                )
                            )
                        )
                        identity_critic_evidence[branch_id].append(
                            tuple(
                                np.asarray(value).copy()
                                for value in (
                                    live["value"],
                                    live["new_critic_hxs"],
                                )
                            )
                        )

                    for diagnostic_agent in diagnostic_agents:
                        slot = diagnostic_slots[(branch_id, int(diagnostic_agent))]
                        executed_label = int(live["visible_skills"][diagnostic_agent])
                        source = (
                            "inactive" if branch.inactive_film else "active"
                        )
                        diagnostic_mean = getattr(
                            artifact, f"diagnostic_{source}_mean"
                        )[slot, step, executed_label]
                        diagnostic_logstd = getattr(
                            artifact, f"diagnostic_{source}_logstd"
                        )[slot, step, executed_label]
                        diagnostic_hidden = getattr(
                            artifact, f"diagnostic_{source}_new_hidden"
                        )[slot, step, executed_label]
                        errors = np.asarray(
                            [
                                np.max(
                                    np.abs(
                                        live["pre_tanh_mean"][diagnostic_agent]
                                        - diagnostic_mean
                                    )
                                ),
                                np.max(
                                    np.abs(
                                        live["log_standard_deviation"][diagnostic_agent]
                                        - diagnostic_logstd
                                    )
                                ),
                                np.max(
                                    np.abs(
                                        live["new_actor_hxs"][diagnostic_agent]
                                        - diagnostic_hidden
                                    )
                                ),
                            ],
                            dtype=np.float32,
                        )
                        artifact.live_diagnostic_abs_error[slot, step] = errors
                        if float(errors.max()) > PARITY_TOLERANCE:
                            raise R27G2ContractError(
                                "R27-G2 live/diagnostic parity tolerance exceeded"
                            )

                    next_obs, reward, terminated, truncated, next_info = env.step(
                        live["deterministic_action"]
                    )
                    _assert_finite_evidence(
                        reward, f"branch[{branch_id}].step[{step}].reward"
                    )
                    _assert_finite_evidence(
                        next_info, f"branch[{branch_id}].step[{step}].info"
                    )
                    next_obs = _require_observation(
                        next_obs, obs_dim=canonical_obs.shape[1]
                    )
                    next_state = _state_from_info(next_info)
                    global_rng_after = capture_global_rng_state()
                    artifact.global_rng_unchanged[branch_id, step] = global_rng_states_equal(
                        global_rng_before, global_rng_after
                    )
                    if not artifact.global_rng_unchanged[branch_id, step]:
                        raise R27G2ContractError(
                            "R27-G2 deterministic branch consumed global RNG state"
                        )

                    artifact.step_valid[branch_id, step] = True
                    artifact.terminated[branch_id, step] = bool(terminated)
                    artifact.truncated[branch_id, step] = bool(truncated)
                    artifact.focal_failure[branch_id, step] = _focal_failed(
                        next_info, branch.focal_agent
                    )
                    artifact.local_observation[branch_id, step + 1] = next_obs
                    artifact.global_state[branch_id, step + 1] = next_state
                    current_environment_rng = capture_environment_rng_state(env)
                    branch_environment_rng.append(current_environment_rng)
                    if reference_environment_rng is None:
                        artifact.environment_rng_equal_reference[
                            branch_id, step + 1
                        ] = True
                    else:
                        artifact.environment_rng_equal_reference[
                            branch_id, step + 1
                        ] = bool(
                            rng_states_equal(
                                current_environment_rng,
                                reference_environment_rng[step + 1],
                            )
                        )
                    if branch.is_identity_branch:
                        identity_info_evidence[branch_id].append(
                            capture_structured_evidence(next_info)
                        )
                        identity_environment_evidence[branch_id].append(
                            capture_environment_state(env)
                        )
                    if bool(terminated or truncated) or artifact.focal_failure[
                        branch_id, step
                    ]:
                        excluded_reason = (
                            f"branch={branch_id} step={step + 1} "
                            f"terminated={bool(terminated)} truncated={bool(truncated)} "
                            f"focal_failure={bool(artifact.focal_failure[branch_id, step])}"
                        )
                        break
                    replay_obs, replay_state, replay_info = (
                        next_obs,
                        next_state,
                        next_info,
                    )
                artifact.branch_completed[branch_id] = bool(
                    np.all(artifact.step_valid[branch_id])
                )
                if excluded_reason is not None:
                    break
                if reference_environment_rng is None:
                    reference_environment_rng = branch_environment_rng
                elif branch.kind in {"hold", "pulse"}:
                    if not np.all(
                        artifact.environment_rng_equal_reference[branch_id, :41]
                    ):
                        raise R27G2ContractError(
                            "R27-G2 matched environment RNG diverged through H40"
                        )
            finally:
                env.close()

        if excluded_reason is None:
            reference_id = 0
            artifact.identity_actor_equal[reference_id] = True
            artifact.identity_critic_equal[reference_id] = True
            artifact.identity_info_equal[reference_id] = True
            artifact.identity_environment_equal[reference_id] = True
            for agent_id in range(N_AGENTS):
                natural = int(natural_roster[agent_id])
                hold_id = next(
                    index
                    for index, item in enumerate(branches)
                    if item.kind == "hold"
                    and item.focal_agent == agent_id
                    and item.target_skill == natural
                )
                for field_name in (
                    "local_observation",
                    "global_state",
                    "joint_action",
                    "live_pre_tanh_mean",
                    "live_log_standard_deviation",
                    "live_log_probability",
                ):
                    _assert_exact_array(
                        f"same-label {field_name} agent={agent_id}",
                        getattr(artifact, field_name)[hold_id],
                        getattr(artifact, field_name)[reference_id],
                    )
                artifact.identity_actor_equal[hold_id] = _array_tuple_sequence_equal(
                    identity_actor_evidence[hold_id],
                    identity_actor_evidence[reference_id],
                )
                artifact.identity_critic_equal[
                    hold_id
                ] = _array_tuple_sequence_equal(
                    identity_critic_evidence[hold_id],
                    identity_critic_evidence[reference_id],
                )
                artifact.identity_info_equal[hold_id] = np.asarray(
                    [
                        left == right
                        for left, right in zip(
                            identity_info_evidence[hold_id],
                            identity_info_evidence[reference_id],
                        )
                    ],
                    dtype=np.bool_,
                )
                artifact.identity_environment_equal[hold_id] = np.asarray(
                    [
                        environment_states_equal(left, right)
                        for left, right in zip(
                            identity_environment_evidence[hold_id],
                            identity_environment_evidence[reference_id],
                        )
                    ],
                    dtype=np.bool_,
                )
                for evidence_name, evidence in (
                    ("actor", artifact.identity_actor_equal[hold_id]),
                    ("critic", artifact.identity_critic_equal[hold_id]),
                    ("info", artifact.identity_info_equal[hold_id]),
                    (
                        "environment",
                        artifact.identity_environment_equal[hold_id],
                    ),
                ):
                    if not bool(np.all(evidence)):
                        first = int(np.flatnonzero(~evidence)[0])
                        raise R27G2ContractError(
                            "R27-G2 exact parity failed: "
                            f"same-label {evidence_name} agent={agent_id} step={first}"
                        )
                reference_slot = diagnostic_slots[(reference_id, agent_id)]
                hold_slot = diagnostic_slots[(hold_id, agent_id)]
                for field_name in (
                    "diagnostic_active_mean",
                    "diagnostic_active_logstd",
                    "diagnostic_active_action",
                    "diagnostic_active_new_hidden",
                    "diagnostic_inactive_mean",
                    "diagnostic_inactive_logstd",
                    "diagnostic_inactive_action",
                    "diagnostic_inactive_new_hidden",
                    "live_diagnostic_abs_error",
                ):
                    _assert_exact_array(
                        f"same-label {field_name} agent={agent_id}",
                        getattr(artifact, field_name)[hold_slot],
                        getattr(artifact, field_name)[reference_slot],
                    )
                inactive_ids = [
                    index
                    for index, item in enumerate(branches)
                    if item.kind == "inactive" and item.focal_agent == agent_id
                ]
                if len(inactive_ids) != 2:
                    raise AssertionError("R27-G2 inactive pair construction failed")
                for field_name in (
                    "local_observation",
                    "global_state",
                    "joint_action",
                    "live_pre_tanh_mean",
                    "live_log_standard_deviation",
                    "live_log_probability",
                ):
                    _assert_exact_array(
                        f"inactive identity {field_name} agent={agent_id}",
                        getattr(artifact, field_name)[inactive_ids[0]],
                        getattr(artifact, field_name)[inactive_ids[1]],
                    )
                first_inactive, second_inactive = inactive_ids
                actor_equal = _array_tuple_sequence_equal(
                    identity_actor_evidence[first_inactive],
                    identity_actor_evidence[second_inactive],
                )
                critic_equal = _array_tuple_sequence_equal(
                    identity_critic_evidence[first_inactive],
                    identity_critic_evidence[second_inactive],
                )
                info_equal = np.asarray(
                    [
                        left == right
                        for left, right in zip(
                            identity_info_evidence[first_inactive],
                            identity_info_evidence[second_inactive],
                        )
                    ],
                    dtype=np.bool_,
                )
                environment_equal = np.asarray(
                    [
                        environment_states_equal(left, right)
                        for left, right in zip(
                            identity_environment_evidence[first_inactive],
                            identity_environment_evidence[second_inactive],
                        )
                    ],
                    dtype=np.bool_,
                )
                for field_name, values in (
                    ("identity_actor_equal", actor_equal),
                    ("identity_critic_equal", critic_equal),
                    ("identity_info_equal", info_equal),
                    ("identity_environment_equal", environment_equal),
                ):
                    getattr(artifact, field_name)[first_inactive] = values
                    getattr(artifact, field_name)[second_inactive] = values
                    if not bool(np.all(values)):
                        first = int(np.flatnonzero(~values)[0])
                        raise R27G2ContractError(
                            "R27-G2 exact parity failed: inactive identity "
                            f"{field_name} agent={agent_id} step={first}"
                        )
                first_inactive_slot = diagnostic_slots[
                    (inactive_ids[0], agent_id)
                ]
                second_inactive_slot = diagnostic_slots[
                    (inactive_ids[1], agent_id)
                ]
                for field_name in (
                    "diagnostic_active_mean",
                    "diagnostic_active_logstd",
                    "diagnostic_active_action",
                    "diagnostic_active_new_hidden",
                    "diagnostic_inactive_mean",
                    "diagnostic_inactive_logstd",
                    "diagnostic_inactive_action",
                    "diagnostic_inactive_new_hidden",
                    "live_diagnostic_abs_error",
                ):
                    _assert_exact_array(
                        f"inactive identity {field_name} agent={agent_id}",
                        getattr(artifact, field_name)[first_inactive_slot],
                        getattr(artifact, field_name)[second_inactive_slot],
                    )
    except Exception as error:
        if isinstance(error, R27G2ContractError):
            invalid_reasons.append(str(error))
        else:
            invalid_reasons.append(f"{type(error).__name__}: {error}")

    try:
        artifact.module_state_equal[...] = bool(
            module_states_equal(capture_module_state(agent), module_state_snapshot)
        )
        artifact.value_norm_state_equal[...] = bool(
            value_norm_states_equal(
                capture_value_norm_state(agent), value_norm_state_snapshot
            )
        )
    except Exception as error:
        if isinstance(error, R27G2ContractError):
            invalid_reasons.append(str(error))
        else:
            invalid_reasons.append(f"{type(error).__name__}: {error}")
    if not bool(artifact.module_state_equal):
        invalid_reasons.append("R27-G2 module state changed during reset")
    if not bool(artifact.value_norm_state_equal):
        invalid_reasons.append("R27-G2 ValueNorm state changed during reset")

    status = "INVALID" if invalid_reasons else (
        "EXCLUDED" if excluded_reason is not None else "OK"
    )
    artifact.validate()
    manifest: dict[str, Any] = {
        "experiment_id": "EXP-20260712-r27-g2-forced-z-trajectory-effect",
        "status": status,
        "invalid_reasons": invalid_reasons,
        "excluded_reason": excluded_reason,
        "reset_id": reset_id,
        "reset_seed": reset_seed,
        "prefix_policy_seed": policy_seed,
        "prefix_steps": prefix_steps,
        "checkpoint_id": str(checkpoint_id),
        "checkpoint_update": int(checkpoint_update),
        "checkpoint_path": str(checkpoint_path),
        "module_state_equal": bool(artifact.module_state_equal),
        "value_norm_state_equal": bool(artifact.value_norm_state_equal),
        "calibration_complete": True,
        "branch_count": BRANCH_COUNT,
        "branch_steps": BRANCH_STEPS,
        "diagnostic_slot_count": DIAGNOSTIC_SLOT_COUNT,
        "artifact_schema": "r27-g2-reset-v2",
        "artifact_fields": [item.name for item in fields(R27G2ResetArtifact)],
        "observation_dim": int(artifact.local_observation.shape[-1]),
        "state_dim": int(artifact.global_state.shape[-1]),
        "hidden_dim": int(artifact.diagnostic_active_new_hidden.shape[-1]),
        "reference_act_low_parity_complete": bool(
            np.all(artifact.step_valid[0])
        ),
        "reference_act_low_parity_max_abs_error": float(
            artifact.reference_act_low_parity_abs_error.max()
        ),
        "environment_steps": int(prefix_steps + BRANCH_COUNT * (prefix_steps + BRANCH_STEPS)),
        "calibration_rows": int(50 * N_AGENTS),
        "parity_tolerance": PARITY_TOLERANCE,
        "inactive_tolerance": INACTIVE_TOLERANCE,
    }
    return ResetCollectionResult(artifact=artifact, manifest=manifest)


def write_reset_collection(
    result: ResetCollectionResult, output_dir: str | Path
) -> tuple[Path, Path]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    reset_id = int(result.artifact.reset_id)
    shard = result.artifact.write(root / f"reset_{reset_id:04d}.npz")
    manifest = dict(result.manifest)
    manifest["artifact"] = shard.name
    manifest_path = root / "reset_manifest.json"
    _write_manifest(manifest_path, manifest)
    return shard, manifest_path
