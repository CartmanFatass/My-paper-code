"""Collect frozen natural-policy behavior windows for the R26-G1a screen."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ha_ctse_process.r26_g1_dataset import (  # noqa: E402
    G1WindowBatch,
    build_prior_context,
    window_summary,
    write_g1_window_shard,
)


@dataclass
class PendingWindow:
    agent_id: int
    label: int
    duration_idx: int
    previous_skill: int
    previous_age: int
    team_code: int
    assignment_obs: np.ndarray
    omega: np.ndarray
    teammate_roster: np.ndarray
    pre_action: np.ndarray
    pre_effect: np.ndarray
    pre_valid: bool
    actions: list[np.ndarray]
    observations: list[np.ndarray]


@dataclass
class PendingR28Window:
    agent_id: int
    label: int
    duration_idx: int
    episode_step_start: int
    expected_length: int
    phi0: np.ndarray
    pre_actions: np.ndarray
    pre_valid: bool
    actions: list[np.ndarray]


@dataclass(frozen=True)
class CollectorStats:
    resets: int
    completed_windows: int
    discarded_incomplete: int
    renewal_events: int


_RUNTIME_ATTRIBUTES = (
    "active_skills",
    "active_duration_indices",
    "duration_remaining",
    "skill_age",
    "has_active_skill",
    "active_team_codes",
    "episode_steps",
    "episode_ids",
    "team_intent_remaining",
    "team_intent_age",
    "low_actor_hxs",
    "low_critic_hxs",
    "_last_low_context",
    "segments",
    "situation_debouncer",
    "per_agent_situation_debouncer",
    "situation_hazard_guard",
    "_last_situation_state",
    "_last_agent_situation_state",
    "_team_transition_open",
    "_team_transition_closed",
    "_team_transition_env_steps",
    "_team_intent_boundary_count",
    "_team_intent_boundary_trunc_fracs",
    "_team_intent_boundary_trunc_by_duration",
    "_team_intent_dwell_checks",
    "_team_intent_age_check_samples",
    "_situation_diag_events",
    "_agent_situation_diag_events",
    "_situation_hazard_forced_renewals",
    "_situation_hazard_events",
)


@contextmanager
def preserve_agent_runtime(agent: Any) -> Iterator[None]:
    """Restore mutable rollout state after collection from a reused agent."""

    missing = object()
    originals: dict[str, Any] = {}
    for name in _RUNTIME_ATTRIBUTES:
        value = getattr(agent, name, missing)
        if value is not missing:
            originals[name] = value
    working = copy.deepcopy(originals)
    for name, value in working.items():
        setattr(agent, name, value)
    try:
        yield
    finally:
        for name, value in originals.items():
            setattr(agent, name, value)


def require_cuda_device(device: str) -> torch.device:
    requested = str(device).strip().lower()
    if requested != "cuda" and not requested.startswith("cuda:"):
        raise ValueError("real R26-G1a collection requires --device cuda")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested for R26-G1a collection but is unavailable")
    return torch.device(requested)


def _state_from_info(info: Any, previous: Any = None) -> np.ndarray | None:
    mapping = info if isinstance(info, dict) else {}
    state = mapping.get("next_state", mapping.get("state", previous))
    if state is None:
        return None
    return np.asarray(state, dtype=np.float32).reshape(-1)


def _copy_vector(value: Any, *, dtype=np.float32) -> np.ndarray:
    if value is None:
        return np.zeros(0, dtype=dtype)
    return np.asarray(value, dtype=dtype).reshape(-1).copy()


def _pre_window_summary(
    action_history: list[np.ndarray],
    observation_history: list[np.ndarray],
    *,
    skill_interval: int,
    action_dim: int,
    observation_dim: int,
) -> tuple[np.ndarray, np.ndarray, bool]:
    valid = (
        len(action_history) >= int(skill_interval)
        and len(observation_history) >= int(skill_interval) + 1
    )
    if not valid:
        return (
            np.zeros(action_dim * 4, dtype=np.float32),
            np.zeros(observation_dim * 4, dtype=np.float32),
            False,
        )
    return (
        window_summary(action_history[-skill_interval:], action_dim),
        window_summary(observation_history[-(skill_interval + 1) :], observation_dim),
        True,
    )


def _pending_from_segment(
    agent: Any,
    segment: Any,
    *,
    agent_id: int,
    assignment_obs: np.ndarray,
    pre_action: np.ndarray,
    pre_effect: np.ndarray,
    pre_valid: bool,
) -> PendingWindow:
    roster = getattr(segment, "roster_active_skills_start", None)
    if roster is None:
        roster = np.asarray(agent.active_skills[0], dtype=np.int64)
    omega = getattr(segment, "omega_start", None)
    return PendingWindow(
        agent_id=int(agent_id),
        label=int(segment.skill),
        duration_idx=int(segment.duration_idx),
        previous_skill=int(getattr(segment, "prev_skill", 0)),
        previous_age=int(getattr(segment, "skill_age_prev", 0)),
        team_code=int(getattr(segment, "team_code", agent.active_team_codes[0])),
        assignment_obs=_copy_vector(assignment_obs),
        omega=_copy_vector(omega),
        teammate_roster=_copy_vector(roster, dtype=np.int64),
        pre_action=_copy_vector(pre_action),
        pre_effect=_copy_vector(pre_effect),
        pre_valid=bool(pre_valid),
        actions=[],
        observations=[_copy_vector(assignment_obs)],
    )


def pending_prior_context(agent: Any, pending: PendingWindow) -> np.ndarray:
    return build_prior_context(
        focal_agent=int(pending.agent_id),
        n_agents=int(agent.n_agents),
        duration_idx=int(pending.duration_idx),
        n_durations=len(agent.duration_candidates),
        previous_skill=int(pending.previous_skill),
        n_skills=int(agent.n_skills),
        previous_age=int(pending.previous_age),
        team_code=int(pending.team_code),
        num_team_codes=int(agent.num_team_codes),
        teammate_roster=pending.teammate_roster,
        assignment_obs=pending.assignment_obs,
        omega=pending.omega,
        pre_action=pending.pre_action,
        pre_effect=pending.pre_effect,
        pre_valid=pending.pre_valid,
    )


def _empty_batch(
    *, action_summary_dim: int, effect_summary_dim: int, prior_context_dim: int
) -> G1WindowBatch:
    return G1WindowBatch(
        label=np.zeros(0, dtype=np.int64),
        post_action=np.zeros((0, action_summary_dim), dtype=np.float32),
        post_effect=np.zeros((0, effect_summary_dim), dtype=np.float32),
        pre_action=np.zeros((0, action_summary_dim), dtype=np.float32),
        pre_effect=np.zeros((0, effect_summary_dim), dtype=np.float32),
        pre_valid=np.zeros(0, dtype=np.float32),
        prior_context=np.zeros((0, prior_context_dim), dtype=np.float32),
        reset_id=np.zeros(0, dtype=np.int64),
        reset_seed=np.zeros(0, dtype=np.int64),
        episode_id=np.zeros(0, dtype=np.int64),
        env_id=np.zeros(0, dtype=np.int64),
        agent_id=np.zeros(0, dtype=np.int64),
        duration_idx=np.zeros(0, dtype=np.int64),
        segment_length=np.zeros(0, dtype=np.int64),
        checkpoint_id=np.zeros(0, dtype=np.str_),
        checkpoint_update=np.zeros(0, dtype=np.int64),
    )


def _rows_to_batch(
    rows: list[dict[str, Any]],
    *,
    action_summary_dim: int,
    effect_summary_dim: int,
    prior_context_dim: int,
) -> G1WindowBatch:
    if not rows:
        return _empty_batch(
            action_summary_dim=action_summary_dim,
            effect_summary_dim=effect_summary_dim,
            prior_context_dim=prior_context_dim,
        )
    return G1WindowBatch(
        label=np.asarray([row["label"] for row in rows], dtype=np.int64),
        post_action=np.asarray([row["post_action"] for row in rows], dtype=np.float32),
        post_effect=np.asarray([row["post_effect"] for row in rows], dtype=np.float32),
        pre_action=np.asarray([row["pre_action"] for row in rows], dtype=np.float32),
        pre_effect=np.asarray([row["pre_effect"] for row in rows], dtype=np.float32),
        pre_valid=np.asarray([row["pre_valid"] for row in rows], dtype=np.float32),
        prior_context=np.asarray([row["prior_context"] for row in rows], dtype=np.float32),
        reset_id=np.asarray([row["reset_id"] for row in rows], dtype=np.int64),
        reset_seed=np.asarray([row["reset_seed"] for row in rows], dtype=np.int64),
        episode_id=np.asarray([row["episode_id"] for row in rows], dtype=np.int64),
        env_id=np.asarray([row["env_id"] for row in rows], dtype=np.int64),
        agent_id=np.asarray([row["agent_id"] for row in rows], dtype=np.int64),
        duration_idx=np.asarray([row["duration_idx"] for row in rows], dtype=np.int64),
        segment_length=np.asarray([row["segment_length"] for row in rows], dtype=np.int64),
        checkpoint_id=np.asarray([row["checkpoint_id"] for row in rows], dtype=np.str_),
        checkpoint_update=np.asarray(
            [row["checkpoint_update"] for row in rows], dtype=np.int64
        ),
    )


def collect_reset(
    env: Any,
    agent: Any,
    *,
    reset_id: int,
    reset_seed: int,
    episode_id: int,
    skill_interval: int,
    episode_max_steps: int,
    checkpoint_id: str,
    checkpoint_update: int,
    r28_phi0: torch.nn.Module | None = None,
    r28_sidecar_rows: list[dict[str, Any]] | None = None,
    r28_stats: dict[str, int] | None = None,
) -> tuple[G1WindowBatch, CollectorStats]:
    """Collect one reset without retaining any mutation of agent rollout state."""

    interval = int(skill_interval)
    if interval <= 0:
        raise ValueError("skill_interval must be positive")
    if int(episode_max_steps) <= 0:
        raise ValueError("episode_max_steps must be positive")
    r28_enabled = r28_phi0 is not None or r28_sidecar_rows is not None
    if (r28_phi0 is None) != (r28_sidecar_rows is None):
        raise ValueError("R28 sidecar requires both frozen phi0 and an output row list")
    if r28_enabled:
        if interval != 10:
            raise ValueError("R28 sidecar requires skill_interval=10")
        if int(agent.n_agents) != 6 or int(agent.n_skills) != 4:
            raise ValueError("R28 sidecar requires six agents and four skills")
        if tuple(int(item) for item in agent.duration_candidates) != (1, 2, 3, 4):
            raise ValueError("R28 sidecar requires duration candidates (1,2,3,4)")

    completed_rows: list[dict[str, Any]] = []
    discarded = 0
    renewals = 0
    prior_context_dim = 0

    with preserve_agent_runtime(agent):
        obs, info = env.reset(seed=int(reset_seed))
        obs = np.asarray(obs, dtype=np.float32)
        if obs.ndim < 2 or int(obs.shape[0]) != int(agent.n_agents):
            raise ValueError("environment observation must have one row per agent")
        state = _state_from_info(info)
        agent.reset_env_state(0)
        if hasattr(agent.segments, "active"):
            agent.segments.active[0] = [None for _ in range(int(agent.n_agents))]

        observation_dim = int(np.asarray(obs[0]).reshape(-1).size)
        action_dim = 0
        pending: dict[int, PendingWindow] = {}
        r28_pending: dict[int, PendingR28Window] = {}
        action_history: list[list[np.ndarray]] = [
            [] for _ in range(int(agent.n_agents))
        ]
        deterministic_action_history: list[list[np.ndarray]] = [
            [] for _ in range(int(agent.n_agents))
        ]
        observation_history: list[list[np.ndarray]] = [
            [_copy_vector(obs[agent_id])] for agent_id in range(int(agent.n_agents))
        ]

        for step in range(int(episode_max_steps)):
            previous_segments = list(agent.segments.active[0])
            with torch.no_grad():
                agent.maybe_assign_skills(
                    obs,
                    state=state,
                    step=int(step),
                    k=interval,
                    env_id=0,
                    deterministic=False,
                )
            current_segments = list(agent.segments.active[0])
            changed = [
                agent_id
                for agent_id, (before, after) in enumerate(
                    zip(previous_segments, current_segments)
                )
                if after is not None and after is not before
            ]
            for agent_id in changed:
                renewals += 1
                if r28_phi0 is not None and r28_sidecar_rows is not None:
                    previous_r28 = r28_pending.pop(agent_id, None)
                    if previous_r28 is not None:
                        if len(previous_r28.actions) == int(previous_r28.expected_length):
                            r28_sidecar_rows.append(
                                {
                                    "label": int(previous_r28.label),
                                    "duration_idx": int(previous_r28.duration_idx),
                                    "agent_id": int(previous_r28.agent_id),
                                    "episode_step_start": int(
                                        previous_r28.episode_step_start
                                    ),
                                    "phi0": previous_r28.phi0.copy(),
                                    "pre_actions": previous_r28.pre_actions.copy(),
                                    "post_actions": np.asarray(
                                        previous_r28.actions[-interval:],
                                        dtype=np.float32,
                                    ),
                                    "pre_valid": bool(previous_r28.pre_valid),
                                    "reset_id": int(reset_id),
                                    "reset_seed": int(reset_seed),
                                    "episode_id": int(episode_id),
                                    "checkpoint_id": str(checkpoint_id),
                                    "checkpoint_update": int(checkpoint_update),
                                }
                            )
                            if r28_stats is not None:
                                r28_stats["completed"] = r28_stats.get("completed", 0) + 1
                        elif r28_stats is not None:
                            r28_stats["discarded"] = r28_stats.get("discarded", 0) + 1
                if agent_id in pending:
                    discarded += 1
                summary_action_dim = max(action_dim, 1)
                pre_action, pre_effect, pre_valid = _pre_window_summary(
                    action_history[agent_id],
                    observation_history[agent_id],
                    skill_interval=interval,
                    action_dim=summary_action_dim,
                    observation_dim=observation_dim,
                )
                segment = current_segments[agent_id]
                assignment_obs = getattr(segment, "high_obs", obs[agent_id])
                if r28_phi0 is not None and r28_sidecar_rows is not None:
                    pre_rows = deterministic_action_history[agent_id][-interval:]
                    r28_pre_valid = len(pre_rows) == interval
                    pre_deterministic = (
                        np.asarray(pre_rows, dtype=np.float32)
                        if r28_pre_valid
                        else np.zeros((interval, 4), dtype=np.float32)
                    )
                    with torch.no_grad():
                        phi0 = (
                            r28_phi0(
                                torch.as_tensor(
                                    np.asarray(assignment_obs, dtype=np.float32).reshape(1, -1),
                                    dtype=torch.float32,
                                    device=next(r28_phi0.parameters()).device,
                                )
                            )
                            .detach()
                            .cpu()
                            .numpy()
                            .reshape(-1)
                        )
                    if phi0.shape != (256,) or not np.isfinite(phi0).all():
                        raise RuntimeError("R28 sidecar frozen phi0 context is invalid")
                    duration_idx = int(segment.duration_idx)
                    expected_length = int(agent.duration_candidates[duration_idx]) * interval
                    if expected_length not in (10, 20, 30, 40):
                        raise RuntimeError("R28 sidecar natural duration drifted")
                    r28_pending[agent_id] = PendingR28Window(
                        agent_id=int(agent_id),
                        label=int(segment.skill),
                        duration_idx=duration_idx,
                        episode_step_start=int(step),
                        expected_length=expected_length,
                        phi0=phi0.astype(np.float32),
                        pre_actions=pre_deterministic,
                        pre_valid=bool(r28_pre_valid),
                        actions=[],
                    )
                opened = _pending_from_segment(
                    agent,
                    segment,
                    agent_id=agent_id,
                    assignment_obs=assignment_obs,
                    pre_action=pre_action,
                    pre_effect=pre_effect,
                    pre_valid=pre_valid,
                )
                pending[agent_id] = opened
                prior_context_dim = max(
                    prior_context_dim, int(pending_prior_context(agent, opened).size)
                )

            with torch.no_grad():
                if r28_phi0 is not None:
                    actions, _logp, _values, low_context = agent.act_low(
                        obs,
                        env_id=0,
                        deterministic=False,
                        state=state,
                        return_context=True,
                        capture_deterministic_action=True,
                    )
                    deterministic_actions = np.asarray(
                        low_context["deterministic_actions"], dtype=np.float32
                    )
                    if deterministic_actions.shape != (int(agent.n_agents), 4):
                        raise RuntimeError(
                            "R28 sidecar deterministic actions must have shape (6,4)"
                        )
                    if not np.isfinite(deterministic_actions).all():
                        raise RuntimeError("R28 sidecar deterministic actions are non-finite")
                else:
                    actions, _logp, _values = agent.act_low(
                        obs,
                        env_id=0,
                        deterministic=False,
                        state=state,
                    )
                    deterministic_actions = None
            actions = np.asarray(actions)
            if int(actions.shape[0]) != int(agent.n_agents):
                raise ValueError("agent actions must have one row per agent")
            if action_dim <= 0:
                action_dim = int(np.asarray(actions[0]).reshape(-1).size)
                for window in pending.values():
                    if not window.pre_valid:
                        window.pre_action = np.zeros(action_dim * 4, dtype=np.float32)

            next_obs, _reward, terminated, truncated, next_info = env.step(actions)
            next_obs = np.asarray(next_obs, dtype=np.float32)
            for agent_id in range(int(agent.n_agents)):
                action_row = _copy_vector(actions[agent_id])
                observation_row = _copy_vector(next_obs[agent_id])
                action_history[agent_id].append(action_row)
                observation_history[agent_id].append(observation_row)
                if deterministic_actions is not None:
                    deterministic_row = _copy_vector(deterministic_actions[agent_id])
                    deterministic_action_history[agent_id].append(deterministic_row)
                    if len(deterministic_action_history[agent_id]) > interval:
                        del deterministic_action_history[agent_id][:-interval]
                    r28_window = r28_pending.get(agent_id)
                    if r28_window is not None:
                        r28_window.actions.append(deterministic_row)
                        if len(r28_window.actions) > int(r28_window.expected_length):
                            raise RuntimeError("R28 sidecar window exceeded its natural duration")
                if len(action_history[agent_id]) > interval:
                    del action_history[agent_id][:-interval]
                if len(observation_history[agent_id]) > interval + 1:
                    del observation_history[agent_id][: -(interval + 1)]

            for agent_id, window in list(pending.items()):
                window.actions.append(_copy_vector(actions[agent_id]))
                window.observations.append(_copy_vector(next_obs[agent_id]))
                if len(window.actions) == interval:
                    context = pending_prior_context(agent, window)
                    prior_context_dim = int(context.size)
                    completed_rows.append(
                        {
                            "label": int(window.label),
                            "post_action": window_summary(window.actions, action_dim),
                            "post_effect": window_summary(
                                window.observations, observation_dim
                            ),
                            "pre_action": window.pre_action,
                            "pre_effect": window.pre_effect,
                            "pre_valid": float(window.pre_valid),
                            "prior_context": context,
                            "reset_id": int(reset_id),
                            "reset_seed": int(reset_seed),
                            "episode_id": int(episode_id),
                            "env_id": 0,
                            "agent_id": int(window.agent_id),
                            "duration_idx": int(window.duration_idx),
                            "segment_length": interval,
                            "checkpoint_id": str(checkpoint_id),
                            "checkpoint_update": int(checkpoint_update),
                        }
                    )
                    del pending[agent_id]
                elif len(window.actions) > interval:
                    raise RuntimeError("pending window exceeded skill_interval")

            obs = next_obs
            state = _state_from_info(next_info, previous=state)
            if hasattr(agent, "record_environment_step"):
                agent.record_environment_step(0)
            if bool(terminated or truncated):
                break

        discarded += len(pending)
        if r28_stats is not None:
            r28_stats["discarded"] = r28_stats.get("discarded", 0) + len(r28_pending)

    action_dim = max(int(action_dim), 1)
    batch = _rows_to_batch(
        completed_rows,
        action_summary_dim=action_dim * 4,
        effect_summary_dim=observation_dim * 4,
        prior_context_dim=prior_context_dim,
    )
    return batch, CollectorStats(
        resets=1,
        completed_windows=len(completed_rows),
        discarded_incomplete=int(discarded),
        renewal_events=int(renewals),
    )


def snapshot_policy_parameters(agent: Any) -> dict[str, torch.Tensor]:
    snapshot: dict[str, torch.Tensor] = {}
    seen_modules: set[int] = set()
    for attribute, value in sorted(vars(agent).items()):
        if not isinstance(value, torch.nn.Module) or id(value) in seen_modules:
            continue
        seen_modules.add(id(value))
        for name, parameter in sorted(value.named_parameters()):
            snapshot[f"{attribute}.{name}"] = parameter.detach().cpu().clone()
    return snapshot


def policy_parameters_equal(
    left: dict[str, torch.Tensor], right: dict[str, torch.Tensor]
) -> bool:
    return left.keys() == right.keys() and all(
        torch.equal(left[name], right[name]) for name in left
    )


def write_r28_sidecar_shard(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write deterministic-action evidence without altering the R26 batch."""

    path.parent.mkdir(parents=True, exist_ok=True)
    count = len(rows)
    payload = {
        "schema": np.asarray("r28-g1-natural-sidecar-v1"),
        "label": np.asarray([row["label"] for row in rows], dtype=np.int64),
        "duration_idx": np.asarray(
            [row["duration_idx"] for row in rows], dtype=np.int64
        ),
        "agent_id": np.asarray([row["agent_id"] for row in rows], dtype=np.int64),
        "episode_step_start": np.asarray(
            [row["episode_step_start"] for row in rows], dtype=np.int64
        ),
        "phi0": np.asarray(
            [row["phi0"] for row in rows], dtype=np.float32
        ).reshape(count, 256),
        "pre_actions": np.asarray(
            [row["pre_actions"] for row in rows], dtype=np.float32
        ).reshape(count, 10, 4),
        "post_actions": np.asarray(
            [row["post_actions"] for row in rows], dtype=np.float32
        ).reshape(count, 10, 4),
        "pre_valid": np.asarray(
            [row["pre_valid"] for row in rows], dtype=np.bool_
        ),
        "reset_id": np.asarray([row["reset_id"] for row in rows], dtype=np.int64),
        "reset_seed": np.asarray(
            [row["reset_seed"] for row in rows], dtype=np.int64
        ),
        "episode_id": np.asarray(
            [row["episode_id"] for row in rows], dtype=np.int64
        ),
        "env_id": np.zeros(count, dtype=np.int64),
        "checkpoint_id": np.asarray(
            [row["checkpoint_id"] for row in rows], dtype=np.str_
        ),
        "checkpoint_update": np.asarray(
            [row["checkpoint_update"] for row in rows], dtype=np.int64
        ),
    }
    np.savez_compressed(path, **payload)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return str(value)


def _set_eval_mode(agent: Any) -> None:
    seen: set[int] = set()
    for value in vars(agent).values():
        if id(value) in seen:
            continue
        seen.add(id(value))
        if isinstance(value, torch.nn.Module):
            value.eval()


def _configure_agent(args: argparse.Namespace):
    from ha_ctse_process import train as train_mod

    config = train_mod.load_config(args.config, args.preset or None)
    config.scenario = train_mod.normalize_scenario(args.scenario)
    metadata = train_mod.load_checkpoint_metadata(args.checkpoint)
    train_mod.apply_checkpoint_structure(config, args, metadata)
    if int(args.n_agents) > 0 and metadata.get("n_agents") is None:
        config.n_agents = int(args.n_agents)
        config.n_uavs = int(args.n_agents)
        config.max_observed_uavs = max(
            int(args.n_agents),
            int(getattr(config, "max_observed_uavs", args.n_agents)),
        )
    env = train_mod.create_env(
        config, config.scenario, int(args.seed), rank=0, scale_mode="eval"
    )
    _obs, info = env.reset(seed=int(args.seed))
    state = _state_from_info(info)
    state_dim = None if state is None else int(state.size)
    agent = train_mod.create_agent(
        config, args, env, num_envs=1, state_dim=state_dim
    )
    _total_steps, loaded_update = train_mod.load_checkpoint(
        args.checkpoint, agent, load_optimizers=False
    )
    _set_eval_mode(agent)
    return config, metadata, env, agent, int(loaded_update)


def run_collection(args: argparse.Namespace) -> dict[str, Any]:
    require_cuda_device(args.device)
    checkpoint = Path(args.checkpoint)
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    if checkpoint.stat().st_size <= 0:
        raise ValueError(f"checkpoint is empty: {checkpoint}")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    np.random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))
    torch.cuda.manual_seed_all(int(args.seed))

    _config, metadata, env, agent, loaded_update = _configure_agent(args)
    r28_phi0 = None
    r28_stats: dict[str, int] = {"completed": 0, "discarded": 0}
    if bool(getattr(args, "r28_sidecar", False)):
        expected_metadata = {
            "total_steps": 1_160_000,
            "update_idx": 52,
            "n_agents": 6,
            "n_skills": 4,
            "action_space_type": "continuous",
            "action_dim": 4,
            "use_recurrent_low_level": True,
            "low_level_architecture": "strict_hmasd_mappo",
            "skill_interval": 10,
        }
        for name, expected in expected_metadata.items():
            if metadata.get(name) != expected:
                raise ValueError(
                    f"--r28_sidecar checkpoint {name}={metadata.get(name)!r}, "
                    f"expected {expected!r}"
                )
        if tuple(int(item) for item in metadata.get("duration_candidates") or ()) != (
            1,
            2,
            3,
            4,
        ):
            raise ValueError("--r28_sidecar checkpoint duration candidates drifted")
        if bool(metadata.get("low_actor_condition_on_team_code")):
            raise ValueError("--r28_sidecar low actor must remain blind to team code")
        continuation = metadata.get("r28_g1")
        if not isinstance(continuation, dict):
            raise ValueError("--r28_sidecar requires an R28-G1 continuation checkpoint")
        if continuation.get("arm") not in {"probe_only", "sham_reward", "real_reward"}:
            raise ValueError("--r28_sidecar checkpoint arm identity is invalid")
        if (
            int(continuation.get("source_total_steps", -1)) != 1_000_000
            or int(continuation.get("source_update_idx", -1)) != 32
            or continuation.get("source_checkpoint_id") != "arm0_final"
            or continuation.get("has_frozen_actor_base") is not True
        ):
            raise ValueError("--r28_sidecar checkpoint source identity drifted")
        if Path(str(continuation.get("scorer_path") or "")).name != "r28_g0_scorer_final.pt":
            raise ValueError("--r28_sidecar checkpoint scorer identity drifted")
        if int(loaded_update) != 52:
            raise ValueError("--r28_sidecar loaded checkpoint update is not 52")
        if args.checkpoint_update is not None and int(args.checkpoint_update) != 52:
            raise ValueError("--r28_sidecar cannot relabel the checkpoint update")
        if int(args.skill_interval) != 10:
            raise ValueError("--r28_sidecar requires --skill_interval 10")
        if int(agent.n_agents) != 6 or int(agent.n_skills) != 4 or int(agent.action_dim) != 4:
            raise ValueError("--r28_sidecar live agent shape drifted")
        try:
            checkpoint_payload = torch.load(
                checkpoint, map_location="cpu", weights_only=True
            )
        except TypeError:
            checkpoint_payload = torch.load(checkpoint, map_location="cpu")
        r28_state = checkpoint_payload.get("r28_g1")
        if not isinstance(r28_state, dict) or not isinstance(
            r28_state.get("frozen_actor_base"), dict
        ):
            raise ValueError("--r28_sidecar requires a G1 checkpoint with frozen actor_base")
        if not hasattr(agent.low, "actor_base"):
            raise TypeError("--r28_sidecar requires the strict recurrent low actor")
        r28_phi0 = copy.deepcopy(agent.low.actor_base).to(torch.device(args.device))
        r28_phi0.load_state_dict(r28_state["frozen_actor_base"], strict=True)
        r28_phi0.eval()
        for parameter in r28_phi0.parameters():
            parameter.requires_grad_(False)
    checkpoint_id = str(args.checkpoint_id or checkpoint.stem)
    checkpoint_update = (
        int(args.checkpoint_update)
        if args.checkpoint_update is not None
        else int(metadata.get("update_idx") or loaded_update)
    )
    parameters_before = snapshot_policy_parameters(agent)
    totals = CollectorStats(0, 0, 0, 0)
    feature_dimensions: dict[str, int] = {}
    reset_seeds: list[int] = []
    try:
        for reset_id in range(int(args.n_resets)):
            reset_seed = int(args.seed) + int(reset_id)
            reset_seeds.append(reset_seed)
            sidecar_rows: list[dict[str, Any]] = []
            batch, stats = collect_reset(
                env,
                agent,
                reset_id=reset_id,
                reset_seed=reset_seed,
                episode_id=reset_id,
                skill_interval=int(args.skill_interval),
                episode_max_steps=int(args.episode_max_steps),
                checkpoint_id=checkpoint_id,
                checkpoint_update=checkpoint_update,
                r28_phi0=r28_phi0,
                r28_sidecar_rows=sidecar_rows if r28_phi0 is not None else None,
                r28_stats=r28_stats if r28_phi0 is not None else None,
            )
            write_g1_window_shard(output_dir / f"reset_{reset_id:04d}.npz", batch)
            if r28_phi0 is not None:
                write_r28_sidecar_shard(
                    output_dir / "r28_sidecar" / f"reset_{reset_id:04d}.npz",
                    sidecar_rows,
                )
            totals = CollectorStats(
                resets=totals.resets + stats.resets,
                completed_windows=totals.completed_windows + stats.completed_windows,
                discarded_incomplete=(
                    totals.discarded_incomplete + stats.discarded_incomplete
                ),
                renewal_events=totals.renewal_events + stats.renewal_events,
            )
            feature_dimensions = {
                "post_action": int(batch.post_action.shape[1]),
                "post_effect": int(batch.post_effect.shape[1]),
                "pre_action": int(batch.pre_action.shape[1]),
                "pre_effect": int(batch.pre_effect.shape[1]),
                "prior_context": int(batch.prior_context.shape[1]),
            }
    finally:
        env.close()

    parameters_unchanged = policy_parameters_equal(
        parameters_before, snapshot_policy_parameters(agent)
    )
    underpowered = totals.completed_windows == 0
    manifest: dict[str, Any] = {
        "status": "UNDERPOWERED" if underpowered else "OK",
        "underpowered_reason": (
            "no complete post-assignment windows were observed"
            if underpowered
            else None
        ),
        "checkpoint": str(checkpoint),
        "checkpoint_id": checkpoint_id,
        "checkpoint_update": checkpoint_update,
        "checkpoint_nonempty": checkpoint.stat().st_size > 0,
        "checkpoint_metadata": _jsonable(metadata),
        "base_seed": int(args.seed),
        "reset_seeds": reset_seeds,
        "skill_interval": int(args.skill_interval),
        "episode_max_steps": int(args.episode_max_steps),
        "stats": asdict(totals),
        "feature_dimensions": feature_dimensions,
        "policy_parameters_unchanged": parameters_unchanged,
        "device": str(args.device),
        "r28_sidecar": {
            "enabled": r28_phi0 is not None,
            "schema": "r28-g1-natural-sidecar-v1" if r28_phi0 is not None else None,
            "directory": str(output_dir / "r28_sidecar") if r28_phi0 is not None else None,
            **r28_stats,
        },
    }
    (output_dir / "collector_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if not parameters_unchanged:
        raise RuntimeError("policy parameters changed during frozen collection")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect frozen R26-G1a natural-policy behavior windows."
    )
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--config", default="ha_ctse_process.config")
    parser.add_argument("--scenario", default="energy")
    parser.add_argument("--preset", default="S7-S1")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--n_agents", type=int, default=6)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--skill_interval", type=int, default=10)
    parser.add_argument("--n_resets", type=int, default=64)
    parser.add_argument("--episode_max_steps", type=int, default=500)
    parser.add_argument("--checkpoint_id", default="")
    parser.add_argument("--checkpoint_update", type=int, default=None)
    parser.add_argument("--r28_sidecar", action="store_true")
    return parser.parse_args()


def main() -> None:
    manifest = run_collection(parse_args())
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
