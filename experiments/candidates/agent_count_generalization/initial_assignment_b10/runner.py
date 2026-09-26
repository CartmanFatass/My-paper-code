"""Evaluate ordinary H6 deployment against replay of each lane's opening assignment."""
from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import traceback
from types import MethodType
from typing import Any, Callable, Mapping

import numpy as np
import torch

from experiments.candidates.agent_count_generalization.action_law_b02.probe import (
    _normalizer_record,
    _rng_digest,
    restore_checkpoint,
)
from experiments.candidates.agent_count_generalization.action_law_b03.runner import runtime_state_digest
from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import DIRECTION
from experiments.candidates.agent_count_generalization.fixed_count_b09 import runner as b09
from experiments.candidates.agent_count_generalization.initial_policy_b08 import runner as b08
from experiments.candidates.agent_count_generalization.models import build_agent
from experiments.candidates.agent_count_generalization.runner import (
    COMPONENTS,
    digest_agent,
    finite,
    jsonable,
    native_components,
    optimizer_counts,
    preserve_rng,
    seed_rng,
    write_json,
)


OBJECT_ID = "s1_initial_assignment_b10"
TAG = OBJECT_ID
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
MODES = ("ordinary", "initial_replay")
POLICY_STAGE = 45
WORLD_PANEL_STAGE = 45
PRIOR_TRAINING_TEAM_STEPS = 360_000
H6_ASSET = b09.ASSETS[0]
SET_REFERENCE = b08.ASSETS[1]
EvalSpec = b08.EvalSpec
DEFAULT_SPEC = b08.DEFAULT_SPEC


@dataclass
class LoadedInputs:
    h6: b09.LoadedAsset
    set_summary: dict[str, Any]
    set_summary_identity: dict[str, Any]
    set_panels: dict[int, dict[str, Any]]
    set_panel_identities: dict[int, dict[str, Any]]


def file_sha256(path: Path) -> str:
    return b08.file_sha256(path)


def _world_seed(n: int) -> int:
    return b08._world_seed(n)


def _array_sha_bytes(value: np.ndarray) -> np.ndarray:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(repr(array.shape).encode("ascii"))
    digest.update(array.tobytes())
    return np.frombuffer(digest.digest(), dtype=np.uint8).copy()


def _lane_digests(value: np.ndarray) -> np.ndarray:
    return np.stack([_array_sha_bytes(row) for row in np.asarray(value)], axis=0)


def _actor_lane_digests(value: np.ndarray | None, lanes: int) -> np.ndarray:
    if value is None:
        empty = _array_sha_bytes(np.asarray([], dtype=np.float32))
        return np.repeat(empty[None, :], lanes, axis=0)
    return _lane_digests(np.asarray(value)[:lanes])


def _copy_log_probability_record(value: Any) -> dict[str, Any]:
    row = copy.deepcopy(value) if isinstance(value, dict) else {}
    return {
        "semantics": "native coordinator proposal only",
        "team_log_probability": row.get("team_log_prob"),
        "individual_log_probabilities": row.get("agent_log_probs"),
        "proposal_state_value": row.get("state_value"),
        "proposal_agent_values": row.get("agent_values"),
        "execution_assignment_scoring": "not applicable/uncomputed",
        "eligible_for_training_storage": False,
    }


class AssignmentAdapter:
    """Observe native proposals and optionally replay copied opening execution labels."""

    def __init__(
        self, agent: Any, mode: str,
        on_selection_return: Callable[[int, int, int, int], None] | None = None,
    ):
        if mode not in MODES:
            raise ValueError(f"unknown B10 mode {mode}")
        self.agent = agent
        self.mode = mode
        self.on_selection_return = on_selection_return
        self.original = agent._batched_assign_skills
        self.coordinator_original = agent.skill_coordinator.assign_and_value_batch
        self.opening_team: dict[int, int] = {}
        self.opening_individual: dict[int, np.ndarray] = {}
        self.previous_proposal_team: dict[int, int] = {}
        self.previous_proposal_individual: dict[int, np.ndarray] = {}
        self.previous_execution_team: dict[int, int] = {}
        self.previous_execution_individual: dict[int, np.ndarray] = {}
        self.pending_reset: set[int] = set()
        self.events: list[dict[str, Any]] = []
        self.last_step_events: list[dict[str, Any]] = []
        self.selection_forwards = 0
        self.per_lane_selections = 0
        self.opening_lane_selections = 0
        self.later_lane_selections = 0
        self._closed = False
        self._selection_context: tuple[int, int, int] | None = None

        def coordinator_wrapped(
            _coordinator: Any, states: torch.Tensor, observations: torch.Tensor,
            deterministic: bool = False,
        ):
            result = self.coordinator_original(
                states, observations, deterministic=deterministic,
            )
            if self._selection_context is None:
                raise ValueError("B10 observed coordinator selection outside assignment boundary")
            expected, opening, later = self._selection_context
            actual = int(states.shape[0])
            self.selection_forwards += 1
            self.per_lane_selections += actual
            if self.on_selection_return is not None:
                self.on_selection_return(1, actual, 0, 0)
            if actual != expected:
                raise ValueError("B10 coordinator input count differs from opportunity mask")
            self.opening_lane_selections += opening
            self.later_lane_selections += later
            if self.on_selection_return is not None:
                self.on_selection_return(0, 0, opening, later)
            return result

        def wrapped(
            _agent: Any, states_batch: np.ndarray, observations_batch: np.ndarray,
            env_steps_batch: np.ndarray, dones_batch: np.ndarray, deterministic: bool = False,
        ):
            return self._assign(
                states_batch, observations_batch, env_steps_batch, dones_batch,
                deterministic=deterministic,
            )

        agent._batched_assign_skills = MethodType(wrapped, agent)
        agent.skill_coordinator.assign_and_value_batch = MethodType(
            coordinator_wrapped, agent.skill_coordinator,
        )

    def mark_reset(self, lane: int) -> None:
        lane = int(lane)
        self.opening_team.pop(lane, None)
        self.opening_individual.pop(lane, None)
        self.previous_proposal_team.pop(lane, None)
        self.previous_proposal_individual.pop(lane, None)
        self.previous_execution_team.pop(lane, None)
        self.previous_execution_individual.pop(lane, None)
        self.pending_reset.add(lane)

    def _assign(
        self, states_batch: np.ndarray, observations_batch: np.ndarray,
        env_steps_batch: np.ndarray, dones_batch: np.ndarray, deterministic: bool,
    ):
        steps = np.asarray(env_steps_batch, dtype=np.int64)
        dones = np.asarray(dones_batch, dtype=bool)
        invalid = np.asarray([
            self.agent.env_team_skills.get(i, -1) == -1
            or np.any(self.agent.env_agent_skills.get(
                i, np.full(self.agent.config.n_agents, -1, dtype=np.int64)
            ) == -1)
            for i in range(len(steps))
        ], dtype=bool)
        opportunity = (steps % int(self.agent.config.k) == 0) | dones | invalid
        lanes = np.where(opportunity)[0]
        opening_count = sum(int(lane) in self.pending_reset for lane in lanes)
        self._selection_context = (len(lanes), opening_count, len(lanes) - opening_count)
        try:
            proposals = self.original(
                states_batch, observations_batch, env_steps_batch, dones_batch,
                deterministic=deterministic,
            )
        finally:
            self._selection_context = None
        proposed_team, proposed_individual, proposal_logs = proposals
        execution_team = proposed_team if self.mode == "ordinary" else proposed_team.copy()
        execution_individual = (
            proposed_individual if self.mode == "ordinary" else proposed_individual.copy()
        )
        execution_logs = proposal_logs if self.mode == "ordinary" else [
            copy.deepcopy(value) for value in proposal_logs
        ]
        self.last_step_events = []
        for lane in np.where(opportunity)[0]:
            lane = int(lane)
            is_opening = lane in self.pending_reset
            if is_opening:
                self.opening_team[lane] = int(proposed_team[lane])
                self.opening_individual[lane] = np.asarray(
                    proposed_individual[lane], dtype=np.int64
                ).copy()
                self.pending_reset.remove(lane)
            if lane not in self.opening_team or lane not in self.opening_individual:
                raise ValueError(f"B10 lane {lane} proposal preceded true opening cache")
            if self.mode == "initial_replay":
                execution_team[lane] = self.opening_team[lane]
                execution_individual[lane] = self.opening_individual[lane]
            previous_proposal_individual = self.previous_proposal_individual.get(lane)
            previous_execution_individual = self.previous_execution_individual.get(lane)
            event = {
                "lane": lane,
                "step": int(steps[lane]),
                "opportunity_index": sum(1 for row in self.events if row["lane"] == lane),
                "actual_episode_opening": is_opening,
                "proposal_team": int(proposed_team[lane]),
                "proposal_individual": np.asarray(proposed_individual[lane], dtype=np.int64).tolist(),
                "execution_team": int(execution_team[lane]),
                "execution_individual": np.asarray(execution_individual[lane], dtype=np.int64).tolist(),
                "opening_team": int(self.opening_team[lane]),
                "opening_individual": self.opening_individual[lane].tolist(),
                "proposal_team_changed_from_opening": (
                    int(proposed_team[lane]) != self.opening_team[lane]
                ),
                "proposal_individual_changes_from_opening": int(np.sum(
                    np.asarray(proposed_individual[lane]) != self.opening_individual[lane]
                )),
                "proposal_team_changed_from_previous_opportunity": bool(
                    lane in self.previous_proposal_team
                    and int(proposed_team[lane]) != self.previous_proposal_team[lane]
                ),
                "proposal_individual_changes_from_previous_opportunity": (
                    0 if previous_proposal_individual is None else int(np.sum(
                        np.asarray(proposed_individual[lane]) != previous_proposal_individual
                    ))
                ),
                "execution_team_changed_from_opening": (
                    int(execution_team[lane]) != self.opening_team[lane]
                ),
                "execution_individual_changes_from_opening": int(np.sum(
                    np.asarray(execution_individual[lane]) != self.opening_individual[lane]
                )),
                "execution_team_changed_from_previous_opportunity": bool(
                    lane in self.previous_execution_team
                    and int(execution_team[lane]) != self.previous_execution_team[lane]
                ),
                "execution_individual_changes_from_previous_opportunity": (
                    0 if previous_execution_individual is None else int(np.sum(
                        np.asarray(execution_individual[lane]) != previous_execution_individual
                    ))
                ),
                "proposal_metadata": _copy_log_probability_record(proposal_logs[lane]),
            }
            self.previous_proposal_team[lane] = int(proposed_team[lane])
            self.previous_proposal_individual[lane] = np.asarray(
                proposed_individual[lane], dtype=np.int64,
            ).copy()
            self.previous_execution_team[lane] = int(execution_team[lane])
            self.previous_execution_individual[lane] = np.asarray(
                execution_individual[lane], dtype=np.int64,
            ).copy()
            self.events.append(event)
            self.last_step_events.append(event)
        if self.mode == "initial_replay":
            for lane in range(len(steps)):
                if lane not in self.opening_team:
                    raise ValueError(f"B10 lane {lane} has no copied opening labels")
                execution_team[lane] = self.opening_team[lane]
                execution_individual[lane] = self.opening_individual[lane]
                metadata = _copy_log_probability_record(proposal_logs[lane])
                metadata["proposal_only"] = True
                execution_logs[lane] = metadata
                self.agent.env_team_skills[lane] = int(execution_team[lane])
                self.agent.env_agent_skills[lane] = np.asarray(
                    execution_individual[lane], dtype=np.int64
                ).copy()
                self.agent.env_log_probs[lane] = copy.deepcopy(metadata)
        return execution_team, execution_individual, execution_logs

    def evidence(self) -> dict[str, Any]:
        change_counts = {
            key: int(sum(
                int(row[key]) for row in self.events
            ))
            for key in (
                "proposal_team_changed_from_opening",
                "proposal_individual_changes_from_opening",
                "proposal_team_changed_from_previous_opportunity",
                "proposal_individual_changes_from_previous_opportunity",
                "execution_team_changed_from_opening",
                "execution_individual_changes_from_opening",
                "execution_team_changed_from_previous_opportunity",
                "execution_individual_changes_from_previous_opportunity",
            )
        }
        return {
            "mode": self.mode,
            "selection_forwards": self.selection_forwards,
            "per_lane_selections": self.per_lane_selections,
            "opening_lane_selections": self.opening_lane_selections,
            "later_lane_selections": self.later_lane_selections,
            "opening_labels_are_copies": True,
            "proposal_metadata_semantics": "proposal only; never replay-label likelihood",
            "execution_assignment_scoring": "not applicable/uncomputed",
            "separate_team_and_individual_change_counts": change_counts,
            "events": self.events,
        }

    def close(self) -> None:
        if not self._closed:
            self.agent._batched_assign_skills = self.original
            self.agent.skill_coordinator.assign_and_value_batch = self.coordinator_original
            self._closed = True


def _reset_lanes_counted(
    envs: list[Any], agent: Any, adapter: AssignmentAdapter, n: int,
    progress: Callable[..., None] | None,
) -> tuple[np.ndarray, np.ndarray]:
    pairs = []
    for lane, env in enumerate(envs):
        agent.reset_env_state(lane)
        pair = env.reset()
        pairs.append(pair)
        adapter.mark_reset(lane)
        if progress is not None:
            progress(0, 0, n, 0, 1, 0, 0, 0, 0, 0)
    return (
        np.stack([info["state"] for observation, info in pairs]),
        np.stack([observation for observation, info in pairs]),
    )


def _trace_path(out: Path, mode: str, n: int) -> Path:
    return out / f"trace_{mode}_policy45_world45_n{n}.npz"


def _write_trace(path: Path, arrays: Mapping[str, np.ndarray]) -> dict[str, Any]:
    metadata = {}
    checked = {}
    for name, value in arrays.items():
        array = np.asarray(value)
        if array.dtype == object:
            raise ValueError(f"B10 trace {name} has object dtype")
        if np.issubdtype(array.dtype, np.floating) and not np.isfinite(array).all():
            raise ValueError(f"B10 trace {name} is nonfinite")
        checked[name] = array
        metadata[name] = {"shape": list(array.shape), "dtype": str(array.dtype)}
    partial = path.with_suffix(".npz.partial")
    with partial.open("wb") as stream:
        np.savez(stream, **checked)
    partial.replace(path)
    return {
        "path": str(path), "native_relative_path": path.name,
        "sha256": file_sha256(path), "bytes": path.stat().st_size,
        "format": "NumPy npz with allow_pickle=False", "arrays": metadata,
    }


def _load_trace(identity: Mapping[str, Any]) -> dict[str, np.ndarray]:
    path = Path(identity["path"])
    if file_sha256(path) != identity["sha256"] or path.stat().st_size != identity["bytes"]:
        raise ValueError("B10 trace identity changed")
    with np.load(path, allow_pickle=False) as loaded:
        result = {name: loaded[name].copy() for name in loaded.files}
    for name, record in identity["arrays"].items():
        value = result.get(name)
        if value is None or list(value.shape) != record["shape"] or str(value.dtype) != record["dtype"]:
            raise ValueError(f"B10 trace schema mismatch for {name}")
    return result


def _historical_identity(row: dict[str, Any], historical: dict[str, Any]) -> dict[str, Any]:
    fields = {"J": (row["J"], historical["J"]),
              "scalar_returns": (row["scalar_returns"], historical["scalar_returns"])}
    for component in COMPONENTS:
        fields[f"component_means.{component}"] = (
            row["component_means"][component], historical["component_means"][component]
        )
    result = {}
    for name, (observed, expected) in fields.items():
        left, right = np.asarray(observed), np.asarray(expected)
        exact = left.shape == right.shape and np.array_equal(left, right)
        result[name] = {
            "exact": bool(exact),
            "max_abs_difference": (
                float(np.abs(left.astype(np.float64) - right.astype(np.float64)).max(initial=0.0))
                if left.shape == right.shape else None
            ),
        }
    result["all_exact"] = all(row["exact"] for row in result.values())
    return result


def load_inputs(
    h6_checkpoint: Path, *, h6_asset: b09.AssetSpec = H6_ASSET,
    set_reference: b08.AssetSpec = SET_REFERENCE,
    summary_root: Path = REPOSITORY_ROOT / "runs" / DIRECTION,
    committed_sources: bool = True, eval_spec: EvalSpec = DEFAULT_SPEC,
    restore_log_root: Path | None = None,
    construction_progress: Callable[[str, int], None] | None = None,
) -> LoadedInputs:
    def count(name: str, amount: int = 1) -> None:
        if construction_progress is not None:
            construction_progress(name, amount)

    count("input_validation_attempts")
    source = b09._source_asset(h6_asset)
    summary, summary_identity, panels, panel_ids, fit = b08._validate_summary_and_final_panels(
        source, summary_root=summary_root, committed=committed_sources, eval_spec=eval_spec,
    )
    checkpoint = Path(h6_checkpoint)
    if not checkpoint.is_file() or checkpoint.stat().st_size != h6_asset.checkpoint_bytes:
        raise ValueError("B10 H6 final checkpoint byte-size mismatch")
    if file_sha256(checkpoint) != h6_asset.checkpoint_sha256:
        raise ValueError("B10 H6 final checkpoint SHA-256 mismatch")
    count("checkpoint_deserialization_attempts")
    payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
    count("checkpoint_deserialization_completions")
    b09._validate_payload(h6_asset, payload, fit)
    h6 = b09.LoadedAsset(
        h6_asset, checkpoint, summary, summary_identity, panels, panel_ids, payload, fit,
    )
    log_root = Path(restore_log_root or checkpoint.parent / "b10_restore_validation_logs")
    for n in eval_spec.test_ns:
        count("validation_environment_batch_construction_attempts")
        envs = make_envs(eval_spec.eval_lanes, _world_seed(n), n, eval_spec.horizon)
        count("validation_environment_batch_construction_completions")
        count("validation_environment_instances_constructed", len(envs))
        target = None
        try:
            config = b09._make_eval_config(h6, envs, n)
            count("validation_agent_construction_attempts")
            target = build_agent(config, str(log_root / "h6" / f"n{n}"))
            count("validation_agent_construction_completions")
            restore_checkpoint(target, payload)
            if digest_agent(target) != h6_asset.final_digest:
                raise ValueError(f"B10 restored final digest mismatch for H6 N={n}")
        finally:
            for env in envs:
                env.close()
            del target
    count("input_validation_completions")
    if h6.spec.arm != "H6" or set_reference.arm != "SET":
        raise ValueError("B10 requires one H6 model and SET reference arrays only")
    count("input_validation_attempts")
    set_summary, set_identity, set_panels, set_panel_ids, set_fit = (
        b08._validate_summary_and_final_panels(
            set_reference, summary_root=summary_root, committed=committed_sources,
            eval_spec=eval_spec,
        )
    )
    count("input_validation_completions")
    if set_fit != h6.fit_spec:
        raise ValueError("B10 H6 and SET reference evaluation specs differ")
    return LoadedInputs(h6, set_summary, set_identity, set_panels, set_panel_ids)


def _new_trace_arrays(spec: EvalSpec, n: int) -> dict[str, np.ndarray]:
    shape = (spec.horizon, spec.eval_lanes)
    return {
        "raw_actions": np.zeros((*shape, n, 3), dtype=np.float32),
        "clipped_actions": np.zeros((*shape, n, 3), dtype=np.float32),
        "state_sha256": np.zeros((*shape, 32), dtype=np.uint8),
        "observation_sha256": np.zeros((*shape, 32), dtype=np.uint8),
        "actor_state_before_sha256": np.zeros((*shape, 32), dtype=np.uint8),
        "actor_state_after_sha256": np.zeros((*shape, 32), dtype=np.uint8),
        "execution_team": np.full(shape, -1, dtype=np.int16),
        "execution_individual": np.full((*shape, n), -1, dtype=np.int16),
        "proposal_team": np.full(shape, -1, dtype=np.int16),
        "proposal_individual": np.full((*shape, n), -1, dtype=np.int16),
        "opportunity": np.zeros(shape, dtype=bool),
    }


def evaluate_panel(
    record: b09.LoadedAsset, mode: str, n: int, out: Path, eval_spec: EvalSpec,
    progress: Callable[..., None] | None = None,
    construction_progress: Callable[[str, int], None] | None = None,
) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError(f"unknown B10 mode {mode}")
    world_seed = _world_seed(n)
    rng_before = _rng_digest()
    row: dict[str, Any]
    control_mismatch = False
    with preserve_rng():
        seed_rng(world_seed + 51)
        if construction_progress is not None:
            construction_progress("panel_environment_batch_construction_attempts", 1)
        envs = make_envs(eval_spec.eval_lanes, world_seed, n, eval_spec.horizon)
        if construction_progress is not None:
            construction_progress("panel_environment_batch_construction_completions", 1)
            construction_progress("panel_environment_instances_constructed", len(envs))
        target, adapter, hooks = None, None, []
        try:
            config = b09._make_eval_config(record, envs, n)
            if construction_progress is not None:
                construction_progress("panel_agent_construction_attempts", 1)
            target = build_agent(config, str(out / "evaluation_logs" / f"{mode}_n{n}"))
            if construction_progress is not None:
                construction_progress("panel_agent_construction_completions", 1)
            restore_checkpoint(target, record.payload)
            calls, hooks = optimizer_counts(target)
            model_before = digest_agent(target)
            if model_before != record.spec.final_digest:
                raise ValueError("B10 restored final digest mismatch")
            norms_before = _normalizer_record(target)
            runtime_before = runtime_state_digest(target)

            def selection_return(
                forwards: int, lanes: int, opening: int, later: int,
            ) -> None:
                if progress is not None:
                    progress(0, 0, n, 0, 0, forwards, lanes, opening, later, 0)

            adapter = AssignmentAdapter(target, mode, selection_return)
            states, observations = _reset_lanes_counted(envs, target, adapter, n, progress)
            initial = [{
                "world_seed": world_seed + lane,
                "state_sha256": b08._array_digest(states[lane]),
                "observation_sha256": b08._array_digest(observations[lane]),
            } for lane in range(eval_spec.eval_lanes)]
            steps = np.zeros(eval_spec.eval_lanes, dtype=np.int64)
            dones = np.zeros(eval_spec.eval_lanes, dtype=bool)
            returns = np.zeros(eval_spec.eval_lanes, dtype=np.float64)
            components = {name: np.zeros(eval_spec.eval_lanes, dtype=np.float64) for name in COMPONENTS}
            trace = _new_trace_arrays(eval_spec, n)
            action_min, action_max = float("inf"), float("-inf")
            mapping_unchanged = True
            diagnostics_rng_unchanged = True
            with torch.no_grad():
                for t in range(eval_spec.horizon):
                    state_before = states.copy()
                    observation_before = observations.copy()
                    actor_before = (
                        None if target.actor_hidden_np is None
                        else np.asarray(target.actor_hidden_np[:eval_spec.eval_lanes]).copy()
                    )
                    actions, _, data = target.step(
                        states, observations, steps, dones, deterministic=True,
                        return_step_data=True, build_infos=False,
                    )
                    if progress is not None:
                        progress(0, 0, n, 1, 0, 0, 0, 0, 0, 0)
                    finite((actions, data), "B10 deterministic policy output")
                    if actions.shape != (eval_spec.eval_lanes, n, 3) or actions.dtype != np.float32:
                        raise ValueError("B10 action shape/dtype mismatch")
                    if not np.array_equal(states, state_before) or not np.array_equal(
                        observations, observation_before
                    ):
                        raise ValueError("B10 policy call mutated supplied environment inputs")
                    execution_team = np.asarray(data["team_skills"], dtype=np.int64)
                    execution_individual = np.asarray(data["agent_skills"], dtype=np.int64)
                    for lane in range(eval_spec.eval_lanes):
                        if target.env_team_skills[lane] != execution_team[lane] or not np.array_equal(
                            target.env_agent_skills[lane], execution_individual[lane]
                        ):
                            raise ValueError("B10 returned/internal execution labels differ")
                    trace["raw_actions"][t] = actions
                    trace["state_sha256"][t] = _lane_digests(state_before)
                    trace["observation_sha256"][t] = _lane_digests(observation_before)
                    trace["actor_state_before_sha256"][t] = _actor_lane_digests(
                        actor_before, eval_spec.eval_lanes,
                    )
                    trace["actor_state_after_sha256"][t] = _actor_lane_digests(
                        target.actor_hidden_np, eval_spec.eval_lanes,
                    )
                    trace["execution_team"][t] = execution_team
                    trace["execution_individual"][t] = execution_individual
                    for event in adapter.last_step_events:
                        lane = event["lane"]
                        trace["opportunity"][t, lane] = True
                        trace["proposal_team"][t, lane] = event["proposal_team"]
                        trace["proposal_individual"][t, lane] = event["proposal_individual"]
                    diagnostic_rng = _rng_digest()
                    before = actions.copy()
                    executed = np.clip(actions, -1.0, 1.0)
                    trace["clipped_actions"][t] = executed
                    mapping_unchanged &= np.array_equal(before, actions)
                    diagnostics_rng_unchanged &= diagnostic_rng == _rng_digest()
                    action_min = min(action_min, float(executed.min()))
                    action_max = max(action_max, float(executed.max()))
                    next_states, next_observations = [], []
                    for lane, env in enumerate(envs):
                        obs, reward, terminated, truncated, info = env.step(executed[lane])
                        done = bool(terminated or truncated)
                        if progress is not None:
                            progress(1, int(done), n, 0, 0, 0, 0, 0, 0, 0)
                        parts = native_components(info, reward, n)
                        returns[lane] += reward
                        for name in COMPONENTS:
                            components[name][lane] += parts[name]
                        next_states.append(info["next_state"])
                        next_observations.append(obs)
                        dones[lane] = done
                    states, observations = np.stack(next_states), np.stack(next_observations)
                    steps += 1
                    if dones.any() and (t != eval_spec.horizon - 1 or not dones.all()):
                        raise ValueError("unexpected B10 terminal boundary")
            if not dones.all():
                raise ValueError("B10 evaluation missed fixed terminal boundary")
            means = {name: value / eval_spec.horizon for name, value in components.items()}
            j = n * returns / eval_spec.horizon
            native = .7 * means["coverage_reward"] + .3 * means["quality_reward"] - means["energy_penalty"]
            if not np.allclose(j, means["total_reward"], atol=1e-7, rtol=1e-6) or not np.allclose(
                j, native, atol=1e-7, rtol=1e-6
            ):
                raise ValueError("B10 native J/component identity failed")
            model_after = digest_agent(target)
            norms_after = _normalizer_record(target)
            runtime_after = runtime_state_digest(target)
            if any(calls.values()) or model_after != model_before or norms_after != norms_before:
                raise ValueError("B10 evaluation changed weights/normalizers or optimized")
            if not mapping_unchanged or not diagnostics_rng_unchanged or action_min < -1.0 or action_max > 1.0:
                raise ValueError("B10 deterministic clip/diagnostic contract failed")
            trace_identity = _write_trace(_trace_path(out, mode, n), trace)
            if progress is not None:
                progress(0, 0, n, 0, 0, 0, 0, 0, 0, 1)
            row = {
                "status": "complete", "mode": mode, "asset_key": "h6", "arm": "H6",
                "seed": record.spec.seed, "policy_stage": POLICY_STAGE,
                "prior_training_team_steps": PRIOR_TRAINING_TEAM_STEPS,
                "world_panel_stage": WORLD_PANEL_STAGE, "test_n": n,
                "world_seeds": list(range(world_seed, world_seed + eval_spec.eval_lanes)),
                "runtime_seed": world_seed + 51,
                "steps": eval_spec.eval_lanes * eval_spec.horizon,
                "episodes": eval_spec.eval_lanes, "actual_policy_step_calls": eval_spec.horizon,
                "J": j.tolist(), "scalar_returns": returns.tolist(),
                "component_means": jsonable(means), "initial_world_digests": initial,
                "optimizer_calls": calls.copy(), "frozen_weights_and_normalizers": True,
                "parameter_normalizer_digest_before": model_before,
                "parameter_normalizer_digest_after": model_after,
                "restored_digest_matches_original_final": model_before == record.spec.final_digest,
                "normalizers_before": norms_before, "normalizers_after": norms_after,
                "runtime_digest_before": runtime_before, "runtime_digest_after": runtime_after,
                "runtime_evolved": runtime_before != runtime_after,
                "executed_action_bounds": {"minimum": action_min, "maximum": action_max},
                "policy_outputs_unchanged_by_mapping": mapping_unchanged,
                "diagnostics_rng_unchanged": diagnostics_rng_unchanged,
                "assignment": adapter.evidence(), "trace": trace_identity,
                "shadow_forwards": 0, "training_storage_calls": 0,
                "config": b08._config_record(config),
            }
            if mode == "ordinary":
                row["historical_ordinary_identity"] = _historical_identity(
                    row, record.final_panels[n]
                )
                control_mismatch = not row["historical_ordinary_identity"]["all_exact"]
        finally:
            if adapter is not None:
                adapter.close()
            for hook in hooks:
                hook.remove()
            for env in envs:
                env.close()
            del target
    rng_after = _rng_digest()
    if rng_after != rng_before:
        raise ValueError("B10 evaluation changed global RNG state")
    row["global_rng_isolation"] = {
        "digest_before": rng_before, "digest_after": rng_after, "preserved": True,
    }
    if control_mismatch:
        row.update(
            status="failed",
            failure="ValueError: B10 ordinary arrays differ from historical B07",
        )
        write_json(out / f"panel_{mode}_policy45_world45_n{n}.json", row)
        raise ValueError("B10 ordinary arrays differ from historical B07")
    return row


def _first_index(mask: np.ndarray) -> int | None:
    indices = np.where(mask)[0]
    return int(indices[0]) if len(indices) else None


def compare_mode_traces(
    ordinary_identity: Mapping[str, Any], replay_identity: Mapping[str, Any], n: int,
) -> dict[str, Any]:
    ordinary = _load_trace(ordinary_identity)
    replay = _load_trace(replay_identity)
    if set(ordinary) != set(replay):
        raise ValueError("B10 mode traces have different schemas")
    if any(ordinary[name].shape != replay[name].shape for name in ordinary):
        raise ValueError("B10 mode trace shapes differ")
    horizon, lanes = ordinary["execution_team"].shape
    prefix = min(10, horizon)
    prefix_fields = (
        "raw_actions", "clipped_actions", "state_sha256", "observation_sha256",
        "actor_state_before_sha256", "actor_state_after_sha256",
        "execution_team", "execution_individual",
    )
    prefix_checks = {
        name: bool(np.array_equal(ordinary[name][:prefix], replay[name][:prefix]))
        for name in prefix_fields
    }
    if not all(prefix_checks.values()):
        raise ValueError("B10 first-ten ordinary/replay prefix mismatch")
    expected_opportunities = np.zeros((horizon, lanes), dtype=bool)
    expected_opportunities[::10] = True
    cadence = {
        "ordinary_exact_k10": bool(np.array_equal(ordinary["opportunity"], expected_opportunities)),
        "replay_exact_k10": bool(np.array_equal(replay["opportunity"], expected_opportunities)),
    }
    if not all(cadence.values()):
        raise ValueError("B10 selection opportunity cadence mismatch")
    worlds = []
    for lane in range(lanes):
        team_diff = ordinary["execution_team"][:, lane] != replay["execution_team"][:, lane]
        individual_diff = np.any(
            ordinary["execution_individual"][:, lane] != replay["execution_individual"][:, lane],
            axis=-1,
        )
        raw_diff = np.any(
            ordinary["raw_actions"][:, lane] != replay["raw_actions"][:, lane], axis=(-2, -1)
        )
        clipped_diff = np.any(
            ordinary["clipped_actions"][:, lane] != replay["clipped_actions"][:, lane],
            axis=(-2, -1),
        )
        state_diff = np.any(
            ordinary["state_sha256"][:, lane] != replay["state_sha256"][:, lane], axis=-1
        )
        observation_diff = np.any(
            ordinary["observation_sha256"][:, lane] != replay["observation_sha256"][:, lane],
            axis=-1,
        )
        actor_before_diff = np.any(
            ordinary["actor_state_before_sha256"][:, lane]
            != replay["actor_state_before_sha256"][:, lane], axis=-1,
        )
        actor_after_diff = np.any(
            ordinary["actor_state_after_sha256"][:, lane]
            != replay["actor_state_after_sha256"][:, lane], axis=-1,
        )
        first_individual = _first_index(individual_diff)
        first_raw = _first_index(raw_diff)
        first_clipped = _first_index(clipped_diff)
        first_state = _first_index(state_diff)
        first_observation = _first_index(observation_diff)
        if first_raw is not None and (first_individual is None or first_raw < first_individual):
            raise ValueError("B10 raw action diverged before individual execution condition")
        if first_clipped is not None and (first_raw is None or first_clipped < first_raw):
            raise ValueError("B10 clipped action diverged before raw action")
        if first_state is not None and (first_clipped is None or first_state <= first_clipped):
            raise ValueError("B10 physical state diverged before a prior executed-action difference")
        if first_observation is not None and (
            first_clipped is None or first_observation <= first_clipped
        ):
            raise ValueError("B10 observation diverged before a prior executed-action difference")
        worlds.append({
            "world_seed": _world_seed(n) + lane,
            "first_execution_team_label_difference": _first_index(team_diff),
            "first_execution_individual_label_difference": first_individual,
            "first_raw_action_difference": first_raw,
            "first_clipped_action_difference": first_clipped,
            "first_state_history_difference": first_state,
            "first_observation_history_difference": first_observation,
            "first_actor_state_before_difference": _first_index(actor_before_diff),
            "first_actor_state_after_difference": _first_index(actor_after_diff),
            "raw_difference_absorbed_by_clipping": (
                first_raw is not None and (first_clipped is None or first_clipped > first_raw)
            ),
        })
    return {
        "test_n": n, "prefix_length": prefix,
        "first_ten_common_prefix": prefix_checks,
        "selection_cadence": cadence, "worlds": worlds,
        "comparison_scope": "separate realized histories after first divergence; not same-input effects",
    }


def _quantity_reading(ordinary: Any, replay: Any, set_reference: Any) -> dict[str, Any]:
    o, r, s = [np.asarray(value, dtype=np.float64) for value in (
        ordinary, replay, set_reference,
    )]
    if len({value.shape for value in (o, r, s)}) != 1 or not all(
        np.isfinite(value).all() for value in (o, r, s)
    ):
        raise ValueError("B10 reading shape/nonfinite mismatch")
    loss = r - o
    gap_o, gap_r = o - s, r - s
    residual = gap_r - (gap_o + loss)
    return {
        "absolute": {
            "O_per_world": o.tolist(), "O_mean": float(o.mean()),
            "R_per_world": r.tolist(), "R_mean": float(r.mean()),
            "SET_reference_per_world": s.tolist(), "SET_reference_mean": float(s.mean()),
        },
        "replay_effect": {"L_R_minus_O_per_world": loss.tolist(), "L_mean": float(loss.mean())},
        "descriptive_h6_minus_set_gap": {
            "G_O_per_world": gap_o.tolist(), "G_O_mean": float(gap_o.mean()),
            "G_R_per_world": gap_r.tolist(), "G_R_mean": float(gap_r.mean()),
            "G_O_plus_L_per_world": (gap_o + loss).tolist(),
            "identity_residual_per_world": residual.tolist(),
            "identity_max_abs_residual": float(np.abs(residual).max(initial=0.0)),
        },
    }


def compute_readings(
    panels: list[dict[str, Any]], inputs: LoadedInputs, test_ns: tuple[int, ...],
) -> dict[str, Any]:
    rows = {(row["mode"], row["test_n"]): row for row in panels}
    by_n = {}
    for n in test_ns:
        ordinary, replay = rows[("ordinary", n)], rows[("initial_replay", n)]
        reference = inputs.set_panels[n]
        worlds = ordinary["world_seeds"]
        if replay["world_seeds"] != worlds or reference["world_seeds"] != worlds:
            raise ValueError(f"B10 source join worlds differ at N={n}")
        quantities = {
            "J": _quantity_reading(ordinary["J"], replay["J"], reference["J"]),
            "scalar_returns": _quantity_reading(
                ordinary["scalar_returns"], replay["scalar_returns"], reference["scalar_returns"]
            ),
        }
        for component in COMPONENTS:
            quantities[component] = _quantity_reading(
                ordinary["component_means"][component],
                replay["component_means"][component],
                reference["component_means"][component],
            )
        coverage = quantities["coverage_reward"]
        coverage["served_users_per_step"] = {
            section: {
                key: (
                    (50 * np.asarray(value, dtype=np.float64)).tolist()
                    if isinstance(value, list) else 50 * value
                )
                for key, value in coverage[section].items()
            }
            for section in ("absolute", "replay_effect", "descriptive_h6_minus_set_gap")
        }
        by_n[str(n)] = {"test_n": n, "world_seeds": worlds, "quantities": quantities}
    unseen = {}
    if 4 in test_ns and 8 in test_ns:
        for quantity in ("J", "scalar_returns", *COMPONENTS):
            unseen[quantity] = {}
            for section in ("absolute", "replay_effect", "descriptive_h6_minus_set_gap"):
                for key, value in by_n["4"]["quantities"][quantity][section].items():
                    if key.endswith("_mean"):
                        unseen[quantity][key] = float(np.mean([
                            value, by_n["8"]["quantities"][quantity][section][key]
                        ]))
            if quantity == "coverage_reward":
                unseen[quantity]["served_users_per_step"] = {
                    key: 50 * value for key, value in unseen[quantity].items()
                }
    return {
        "reading_order": ["absolute O", "absolute R", "L=R-O", "descriptive gaps"],
        "by_test_n": by_n, "U_equal_weight_N4_N8": unseen,
        "n6_is_a_treatment": by_n.get("6"),
        "positive_energy_penalty_change_is_adverse": True,
        "scope": "opening-assignment deployment rule; no general necessity or compute-saving claim",
    }


def _source_paths() -> tuple[Path, ...]:
    return (
        Path(__file__).resolve(),
        REPOSITORY_ROOT / "scripts/run_agent_count_initial_assignment_b10.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/fixed_count_b09/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/initial_policy_b08/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/action_law_b02/probe.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/action_law_b03/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/configuration.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/models.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/adapter.py",
        REPOSITORY_ROOT / "hmasd/agent.py",
    )


def _source_hashes() -> dict[str, str]:
    return {path.relative_to(REPOSITORY_ROOT).as_posix(): file_sha256(path) for path in _source_paths()}


def _input_identities(inputs: LoadedInputs) -> dict[str, Any]:
    h6 = b09._input_identities([inputs.h6])["h6"]
    set_summary = Path(inputs.set_summary_identity["path"])
    set_panels = {
        str(n): {"path": row["path"], "bytes": Path(row["path"]).stat().st_size,
                 "sha256": file_sha256(Path(row["path"]))}
        for n, row in inputs.set_panel_identities.items()
    }
    return {
        "h6_model_and_original_arrays": h6,
        "set_reference_only": {
            "model_loaded_or_executed": False,
            "summary": {"path": str(set_summary), "bytes": set_summary.stat().st_size,
                        "sha256": file_sha256(set_summary)},
            "panels": set_panels,
        },
    }


def _expected_counts(spec: EvalSpec) -> dict[str, int]:
    panels = len(MODES) * len(spec.test_ns)
    team_steps = panels * spec.eval_lanes * spec.horizon
    selection_per_panel = (spec.horizon + 9) // 10
    selections = panels * selection_per_panel
    return {
        "fits": 0, "training_team_steps": 0, "stored_training_steps": 0,
        "optimizer_calls": 0, "panels": panels,
        "evaluation_team_steps": team_steps,
        "evaluation_uav_steps": len(MODES) * spec.eval_lanes * spec.horizon * sum(spec.test_ns),
        "evaluation_episodes": panels * spec.eval_lanes,
        "evaluation_resets": panels * spec.eval_lanes,
        "actual_batched_policy_step_calls": panels * spec.horizon,
        "coordinator_selection_forwards": selections,
        "per_lane_coordinator_selections": selections * spec.eval_lanes,
        "opening_lane_selections": panels * spec.eval_lanes,
        "later_lane_selections": (selections - panels) * spec.eval_lanes,
        "trace_files": panels, "shadow_forwards": 0,
        "set_model_loads": 0, "training_storage_calls": 0,
    }


def run_study(
    out: Path, launch_sha: str, admission: dict[str, Any], h6_checkpoint: Path,
    *, h6_asset: b09.AssetSpec = H6_ASSET, set_reference: b08.AssetSpec = SET_REFERENCE,
    eval_spec: EvalSpec = DEFAULT_SPEC,
    summary_root: Path = REPOSITORY_ROOT / "runs" / DIRECTION,
    committed_sources: bool = True, command_start: float | None = None,
    evaluate_fn: Callable[..., dict[str, Any]] = evaluate_panel,
) -> int:
    out = Path(out)
    if out.name != TAG:
        raise ValueError(f"B10 output basename must be {TAG}")
    if (out / "summary.json").exists():
        raise ValueError("existing B10 summary; reconcile original attempt")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    command_start = started if command_start is None else command_start
    expected = _expected_counts(eval_spec)
    summary: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "tag": TAG, "direction": DIRECTION,
        "launch_sha": launch_sha, "admission": admission, "status": "validating_assets",
        "zero_fit": True, "failure": None, "spec": jsonable(vars(eval_spec)),
        "policy_stage": POLICY_STAGE, "world_panel_stage": WORLD_PANEL_STAGE,
        "prior_training_team_steps": PRIOR_TRAINING_TEAM_STEPS,
        "modes": list(MODES), "assets": {}, "panels": [], "mode_comparisons": {},
        "readings": None, "counts": {key: 0 for key in expected},
        "construction_counts": {
            key: 0 for key in (
                "input_validation_attempts", "input_validation_completions",
                "checkpoint_deserialization_attempts", "checkpoint_deserialization_completions",
                "validation_environment_batch_construction_attempts",
                "validation_environment_batch_construction_completions",
                "validation_environment_instances_constructed",
                "validation_agent_construction_attempts",
                "validation_agent_construction_completions",
                "panel_environment_batch_construction_attempts",
                "panel_environment_batch_construction_completions",
                "panel_environment_instances_constructed",
                "panel_agent_construction_attempts", "panel_agent_construction_completions",
            )
        },
        "expected_counts": expected, "source_hashes_before": _source_hashes(),
        "runtime": {"python": sys.version, "torch": torch.__version__, "numpy": np.__version__,
                    "device": "cpu", "dtype": "float32", "torch_threads": eval_spec.torch_threads},
    }

    def publish(boundary: str) -> None:
        summary["last_boundary"] = boundary
        summary["command_wall_seconds"] = time.perf_counter() - command_start
        summary["run_study_wall_seconds"] = time.perf_counter() - started
        write_json(out / "summary.json", summary)

    inputs: LoadedInputs | None = None
    active: dict[str, Any] | None = None
    active_filename: str | None = None
    publish("admitted")
    try:
        torch.set_num_threads(eval_spec.torch_threads)

        def construction_progress(name: str, amount: int = 1) -> None:
            if name not in summary["construction_counts"]:
                raise ValueError(f"unknown B10 construction counter {name}")
            summary["construction_counts"][name] += amount

        write_json(out / "config.json", {
            "launch_sha": launch_sha, "object_id": OBJECT_ID, "tag": TAG,
            "spec": jsonable(vars(eval_spec)), "modes": list(MODES),
            "h6_asset": jsonable(vars(h6_asset)), "set_reference": jsonable(vars(set_reference)),
        })
        inputs = load_inputs(
            h6_checkpoint, h6_asset=h6_asset, set_reference=set_reference,
            summary_root=summary_root, committed_sources=committed_sources,
            eval_spec=eval_spec, restore_log_root=out / "restore_validation_logs",
            construction_progress=construction_progress,
        )
        summary["assets"] = {
            "h6": {"model_loaded": True, "checkpoint45": str(inputs.h6.checkpoint),
                   "summary": inputs.h6.summary_identity,
                   "original_panels": inputs.h6.final_panel_identities},
            "set_reference": {"model_loaded_or_executed": False,
                              "summary": inputs.set_summary_identity,
                              "panels": inputs.set_panel_identities},
        }
        summary["input_identities_before"] = _input_identities(inputs)
        publish("H6 final45 model and H6/SET reference arrays validated")

        def progress(
            steps: int, episodes: int, n: int, policy_calls: int, resets: int,
            selection_forwards: int, lane_selections: int, opening: int, later: int,
            traces: int,
        ) -> None:
            summary["counts"]["evaluation_team_steps"] += steps
            summary["counts"]["evaluation_uav_steps"] += steps * n
            summary["counts"]["evaluation_episodes"] += episodes
            summary["counts"]["evaluation_resets"] += resets
            summary["counts"]["actual_batched_policy_step_calls"] += policy_calls
            summary["counts"]["coordinator_selection_forwards"] += selection_forwards
            summary["counts"]["per_lane_coordinator_selections"] += lane_selections
            summary["counts"]["opening_lane_selections"] += opening
            summary["counts"]["later_lane_selections"] += later
            summary["counts"]["trace_files"] += traces

        for mode in MODES:
            for n in eval_spec.test_ns:
                active_filename = f"panel_{mode}_policy45_world45_n{n}.json"
                active = {
                    "status": "running", "mode": mode, "asset_key": "h6", "arm": "H6",
                    "seed": inputs.h6.spec.seed, "policy_stage": POLICY_STAGE,
                    "prior_training_team_steps": PRIOR_TRAINING_TEAM_STEPS,
                    "world_panel_stage": WORLD_PANEL_STAGE, "test_n": n,
                    "world_seeds": list(range(_world_seed(n), _world_seed(n) + eval_spec.eval_lanes)),
                }
                summary["panels"].append(active)
                write_json(out / active_filename, active)
                publish(f"{mode} H6 final45 N={n} starting")
                evaluated = evaluate_fn(
                    inputs.h6, mode, n, out, eval_spec, progress, construction_progress,
                )
                active.clear()
                active.update(evaluated)
                summary["counts"]["panels"] += 1
                write_json(out / active_filename, active)
                publish(f"{mode} H6 final45 N={n} complete")
                active = None
                active_filename = None
        grouped = {(row["mode"], row["test_n"]): row for row in summary["panels"]}
        for n in eval_spec.test_ns:
            ordinary = grouped[("ordinary", n)]
            replay = grouped[("initial_replay", n)]
            if ordinary["initial_world_digests"] != replay["initial_world_digests"]:
                raise ValueError(f"B10 initial environment mismatch at N={n}")
            if ordinary["runtime_digest_before"] != replay["runtime_digest_before"]:
                raise ValueError(f"B10 initial policy runtime mismatch at N={n}")
            if ordinary["runtime_seed"] != replay["runtime_seed"] or (
                ordinary["global_rng_isolation"]["digest_before"]
                != replay["global_rng_isolation"]["digest_before"]
            ):
                raise ValueError(f"B10 initial seed/RNG mismatch at N={n}")
            summary["mode_comparisons"][str(n)] = compare_mode_traces(
                ordinary["trace"], replay["trace"], n
            )
        summary["readings"] = compute_readings(summary["panels"], inputs, eval_spec.test_ns)
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = summary["source_hashes_before"] == summary["source_hashes_after"]
        summary["input_identities_after"] = _input_identities(inputs)
        summary["input_identities_unchanged"] = summary["input_identities_before"] == summary["input_identities_after"]
        if not summary["source_hashes_unchanged"] or not summary["input_identities_unchanged"]:
            raise ValueError("B10 source/checkpoint inputs changed during evaluation")
        if summary["counts"] != expected:
            raise ValueError(f"B10 exposure mismatch: {summary['counts']} != {expected}")
        summary["status"] = "complete"
        return_code = 0
    except Exception as exc:
        if active is not None and active.get("status") == "running":
            if active_filename is not None and (out / active_filename).is_file():
                retained = json.loads((out / active_filename).read_text(encoding="utf-8"))
                if isinstance(retained, dict) and retained.get("J") is not None:
                    active.clear()
                    active.update(retained)
            active.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
            if active_filename is not None:
                write_json(out / active_filename, active)
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = summary["source_hashes_before"] == summary["source_hashes_after"]
        if inputs is not None:
            summary["input_identities_after"] = _input_identities(inputs)
            summary["input_identities_unchanged"] = (
                summary.get("input_identities_before") == summary["input_identities_after"]
            )
        (out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        return_code = 1
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary["resources"] = {
            "command_wall_seconds": time.perf_counter() - command_start,
            "run_study_wall_seconds": time.perf_counter() - started,
            "cpu_user_seconds": usage.ru_utime, "cpu_system_seconds": usage.ru_stime,
            "peak_rss_kib": usage.ru_maxrss,
            "rss_scope": "scientific process Linux RUSAGE_SELF",
            "resources_unmeasured": ["peak_scratch_bytes"],
        }
        publish(summary["status"])
    return return_code
