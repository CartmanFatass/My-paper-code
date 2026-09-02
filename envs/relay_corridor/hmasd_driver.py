"""Run the full HMASD stack on the relay corridor host.

This is the integration seam review Part VII §VII.4 asks for: neither the D2
line (`config_1.py`, `hmasd/*`) nor the host line (`envs/relay_corridor/*`)
could make it alone.  ADR 02 "Decision" fixes the reading implemented here:

* the full HMASD stack runs with ``n_z = K``; ``n_Z`` stays as configured and
  the team code remains present and inert;
* the low-level policy emits a **continuous ``K``-vector** each step and the
  host takes its ``argmax`` as the role (``role_decode = argmax``);
* the adapter emits ``RENEW`` for exactly ``i in S_t`` and ``KEEP`` otherwise;
* the learner receives the **shared mean reward**, and the per-agent service
  indicators are logged (here: into the per-rollout summary).

``S_t`` per mode:

* ``d2``: the D2 sampled mask of that step, ``step_data['d2_sampled_mask']``
  (shape ``[num_envs, n_agents]``).
* ``off``: all-True exactly at the ``off`` boundaries — ``env_steps % k == 0``,
  which includes the first step of every episode after a reset — and all-False
  otherwise.  So ``RENEW`` is emitted exactly when the segment opens in both
  modes, and D0 (``c = c_Z = inf``, ``k_max = k_Z = k``) reproduces the ``off``
  renew pattern step for step.

The rollout loop mirrors the batched base-route loop of
``train_multiproc_config_1.py`` (and the small driver in
``tests/flexible_skill_duration_d2_test.py``): ``agent.step`` -> env step with
terminal-state storage semantics -> ``store_transition_batch`` -> per-env reset
bookkeeping -> ``agent.update`` at the rollout boundary.  Nothing under
``hmasd/`` is imported for anything but the agent itself, and nothing under
``hmasd/`` was changed to make this work.

Resource preflight (``scripts/hmasd_resource_preflight.py admit-memory``) is the
caller's responsibility: it must pass immediately before a run that builds
models, and this module deliberately makes no admission decision of its own.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import torch

from config_1 import Config
from envs.relay_corridor.adapter import RelayCorridorAdapter
from envs.relay_corridor.config import RelayCorridorConfig
from hmasd.agent import HMASDAgent

__all__ = [
    "build_corridor_learner_config",
    "RelayCorridorHMASDDriver",
]


def build_corridor_learner_config(
    corridor: RelayCorridorConfig,
    adapter: RelayCorridorAdapter,
    *,
    mode: str = "off",
    num_envs: int = 2,
    rollout_length: Optional[int] = None,
    k: Optional[int] = None,
    seed: int = 0,
    overrides: Optional[Dict[str, object]] = None,
) -> Config:
    """Build the learner configuration from the host, per ADR 02 "Parameters".

    ``obs_dim``, ``state_dim``, ``n_agents`` come from the adapter;
    ``action_dim = n_z = K`` and ``episode_length = H`` come from the corridor
    configuration.  ``n_Z`` is *not* derived from the host: the team code stays
    at whatever the learner configuration carries (ADR 02: "the team code
    remains present", E5 coupling off).
    """
    if mode not in ("off", "d2"):
        raise ValueError(f"mode must be 'off' or 'd2', got {mode!r}")

    horizon = int(corridor.horizon)
    rollout_length = horizon if rollout_length is None else int(rollout_length)
    k = horizon if k is None else int(k)

    class _CorridorConfig(Config):
        pass

    config = _CorridorConfig()
    config.seed = int(seed)
    config.num_envs = int(num_envs)
    config.episode_length = horizon
    config.max_steps = horizon
    config.rollout_length = rollout_length
    config.k = int(k)
    # ADR 02 "Parameters": n_z = K, low_level_action_dim = K, role_decode = argmax.
    config.n_z = int(corridor.n_z)
    config.action_dim = int(corridor.low_level_action_dim)
    config.action_space_type = "continuous"
    config.action_bound = 1.0
    config.policy_interruption_mode = mode
    for name, value in (overrides or {}).items():
        setattr(config, name, value)
    config.update_env_dims(
        state_dim=int(adapter.state_dim),
        obs_dim=int(adapter.obs_dim),
        n_agents=int(adapter.n_agents),
    )
    return config


class RelayCorridorHMASDDriver:
    """One HMASD agent, one batched corridor adapter, one rollout loop."""

    def __init__(
        self,
        corridor: RelayCorridorConfig,
        *,
        mode: str = "off",
        num_envs: int = 2,
        rollout_length: Optional[int] = None,
        k: Optional[int] = None,
        master_seed: int = 0,
        seed: int = 20260902,
        log_dir: Optional[str] = None,
        device: Optional[torch.device] = None,
        config_overrides: Optional[Dict[str, object]] = None,
    ) -> None:
        if mode not in ("off", "d2"):
            raise ValueError(f"mode must be 'off' or 'd2', got {mode!r}")
        torch.set_num_threads(1)
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)

        self.corridor = corridor
        self.mode = mode
        self.num_envs = int(num_envs)
        # Distinct episode ids per lane keep the keyed corridor streams distinct
        # (host invariant 2); `advance_episode_ids` moves every lane on by
        # `num_envs` at each rollout, so no episode id is ever reused.
        self.adapter = RelayCorridorAdapter(
            corridor,
            num_envs=self.num_envs,
            master_seed=int(master_seed),
            episode_ids=list(range(self.num_envs)),
            squeeze_batch=False,
        )
        self.config = build_corridor_learner_config(
            corridor,
            self.adapter,
            mode=mode,
            num_envs=self.num_envs,
            rollout_length=rollout_length,
            k=k,
            seed=seed,
            overrides=config_overrides,
        )
        self.rollout_length = int(self.config.rollout_length)
        self.n_agents = int(self.config.n_agents)
        self.device = torch.device("cpu") if device is None else device
        log_dir = Path(log_dir) if log_dir is not None else Path("temp/relay_corridor_hmasd/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        self.agent = HMASDAgent(self.config, log_dir=str(log_dir), device=self.device)

        observations, info = self.adapter.reset()
        self.observations = np.asarray(observations, dtype=np.float32)
        self.states = np.asarray(info["state"], dtype=np.float64)
        self.env_steps = np.zeros(self.num_envs, dtype=int)
        self.dones_tracker = np.zeros(self.num_envs, dtype=bool)
        self.rollouts_run = 0

    # ------------------------------------------------------------------
    def off_boundary_mask(self) -> np.ndarray:
        """The ``off`` renew rule at the current step, broadcast over agents.

        ``env_steps % k == 0`` is the boundary rule the base route uses in
        ``off``; ``env_steps`` is reset to zero after a done, so the first step
        of every episode is a boundary too.  ``dones_tracker`` is kept in the
        expression because the base route's ``skill_changed`` carries it.
        """
        boundary = ((self.env_steps % int(self.config.k)) == 0) | self.dones_tracker
        return np.repeat(boundary[:, None], self.n_agents, axis=1)

    # ------------------------------------------------------------------
    def run_rollout(self, *, update: bool = True) -> Dict[str, object]:
        """Collect one rollout, optionally update, and return its summary."""
        steps = self.rollout_length
        renew_masks = np.zeros((steps, self.num_envs, self.n_agents), dtype=bool)
        sampled_masks = np.zeros((steps, self.num_envs, self.n_agents), dtype=bool)
        boundary_masks = np.zeros((steps, self.num_envs, self.n_agents), dtype=bool)
        service = np.zeros((steps, self.num_envs, self.n_agents), dtype=bool)
        rewards_log = np.zeros((steps, self.num_envs), dtype=np.float64)
        roles_log = np.zeros((steps, self.num_envs, self.n_agents), dtype=np.int64)
        dones_log = np.zeros((steps, self.num_envs), dtype=bool)

        for t in range(steps):
            actions, _infos, step_data = self.agent.step(
                self.states,
                self.observations,
                self.env_steps,
                self.dones_tracker,
                deterministic=False,
                return_step_data=True,
                build_infos=False,
            )
            actions = np.asarray(actions)
            if actions.shape != (self.num_envs, self.n_agents, int(self.config.action_dim)):
                raise ValueError(
                    "the low-level policy did not emit a continuous "
                    f"{self.config.action_dim}-vector per agent: got {actions.shape}"
                )

            boundary = self.off_boundary_mask()
            boundary_masks[t] = boundary
            if self.mode == "d2":
                sampled = np.asarray(step_data["d2_sampled_mask"], dtype=bool)
                sampled_masks[t] = sampled
                renew = sampled
            else:
                renew = boundary
            renew_masks[t] = renew

            next_observations, reward, terminated, _truncated, info = self.adapter.step(
                actions, renew_mask=renew
            )
            next_observations = np.asarray(next_observations, dtype=np.float32)
            next_states = np.asarray(info["state"], dtype=np.float64)
            # The learner receives the shared mean reward (ADR 02 "Decision").
            rewards = np.asarray(info["shared_reward"], dtype=np.float64).reshape(self.num_envs)
            dones = np.full(self.num_envs, bool(terminated), dtype=bool)

            service[t] = np.asarray(info["service_indicators"], dtype=bool)
            roles_log[t] = np.asarray(info["roles"], dtype=np.int64)
            rewards_log[t] = rewards
            dones_log[t] = dones

            self.agent.store_transition_batch(
                states=self.states,
                next_states=next_states.copy(),
                observations=self.observations,
                next_observations=next_observations.copy(),
                actions=actions,
                rewards=rewards,
                dones=dones,
                infos_batch=None,
                rollout_step_idx=t,
                step_data=step_data,
            )

            # Per-env reset bookkeeping, exactly as the base-route collector does:
            # the stored transition keeps the terminal next state, while the next
            # policy input takes the reset observations.  The corridor host is one
            # batched object, so every lane terminates together at t = H - 1.
            policy_next_observations = next_observations.copy()
            if bool(terminated):
                self.adapter.advance_episode_ids()
                reset_observations, _reset_info = self.adapter.reset()
                policy_next_observations = np.asarray(reset_observations, dtype=np.float32)
                for env_idx in range(self.num_envs):
                    self.dones_tracker[env_idx] = True
                    self.env_steps[env_idx] = 0
                    self.agent.reset_env_state(env_idx)
            else:
                self.env_steps += 1
            self.states = next_states
            self.observations = policy_next_observations
            self.dones_tracker = dones.copy()

        stored_reward_env = np.asarray(
            self.agent.rollout_buffer.reward_env[:steps], dtype=np.float64
        ).copy()

        updated = False
        if update:
            last_values = np.zeros((self.num_envs, self.n_agents), dtype=np.float32)
            self.agent.update(
                steps_in_buffer=steps,
                last_values=last_values,
                dones=self.dones_tracker.copy(),
                last_state=self.states.copy(),
                last_observations=self.observations.copy(),
            )
            # `update` flushes the open D2 segments, so the metrics are complete
            # here and `clear_buffers` (below) resets them: snapshot in between.
            d2_metrics = self.agent.get_d2_metrics()
            # Mirrors train_multiproc_config_1.py: buffers are cleared after each
            # update, otherwise the next rollout's stores go backwards in time.
            self.agent.clear_buffers()
            updated = True
        else:
            if self.mode == "d2":
                self.agent._d2_flush_open_segments(steps)
            d2_metrics = self.agent.get_d2_metrics()

        self.rollouts_run += 1
        summary = {
            "rollout_index": self.rollouts_run - 1,
            "mode": self.mode,
            "steps": steps,
            "num_envs": self.num_envs,
            "n_agents": self.n_agents,
            "action_dim": int(self.config.action_dim),
            "n_z": int(self.config.n_z),
            "n_Z": int(self.config.n_Z),
            "updated": updated,
            "renew_masks": renew_masks,
            "sampled_masks": sampled_masks if self.mode == "d2" else None,
            "off_boundary_masks": boundary_masks,
            "service_indicators": service,
            "roles": roles_log,
            "rewards": rewards_log,
            "dones": dones_log,
            "stored_reward_env": stored_reward_env,
            # Per-rollout aggregates (ADR 02 "Metrics to log").
            "mean_shared_reward": float(rewards_log.mean()),
            "service_rate_per_agent": service.mean(axis=(0, 1)).astype(np.float64),
            "renew_rate_per_agent": renew_masks.mean(axis=(0, 1)).astype(np.float64),
            "renew_fraction": float(renew_masks.mean()),
            "episode_ids": self.adapter.episode_ids(),
        }
        if self.mode == "d2":
            summary["d2_metrics"] = d2_metrics
        return summary

    # ------------------------------------------------------------------
    def run(self, num_rollouts: int = 1, *, update: bool = True) -> List[Dict[str, object]]:
        return [self.run_rollout(update=update) for _ in range(int(num_rollouts))]
