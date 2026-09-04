"""Adapter presenting the relay corridor host to the HMASD base route.

Review Part IV §IV.8.1 decision 1 (adapter reading (c)) fixes the seam:

* the full HMASD stack runs, with ``n_z = K``;
* the low-level policy emits a **continuous ``K``-vector** each step and the
  host takes its ``argmax`` as the role (``role_decode = argmax``);
* the ADR-01 adapter emits ``RENEW`` for exactly ``i in S_t`` and ``KEEP``
  otherwise -- so ``S_t`` is an *input* to :meth:`RelayCorridorAdapter.step`,
  and this file does not depend on any ADR-01 phase that is still open;
* the learner receives the **shared mean reward** ``r_t``, and every per-agent
  service indicator is logged.

Shape contract, matching ``envs/pettingzoo/env_adapter.py``
(``ParallelToArrayAdapter``): with ``num_envs = 1`` the adapter returns
``observations [N, obs_dim]``, a scalar reward, ``terminated``/``truncated``
flags and an ``info`` dict carrying the global ``state``.  With ``num_envs > 1``
the same quantities keep the leading batch dimension.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional, Sequence, Tuple

import numpy as np

from envs.relay_corridor.config import RelayCorridorConfig
from envs.relay_corridor.host import RelayCorridorHost

__all__ = ["RelayCorridorAdapter"]


class RelayCorridorAdapter:
    """Array-shaped view of :class:`RelayCorridorHost` for the base route."""

    def __init__(
        self,
        config: RelayCorridorConfig,
        *,
        num_envs: int = 1,
        master_seed: int = 0,
        episode_ids: Optional[Sequence[int]] = None,
        squeeze_batch: Optional[bool] = None,
    ) -> None:
        self.config = config
        self.num_envs = int(num_envs)
        self.master_seed = int(master_seed)
        self._episode_ids = (
            list(range(self.num_envs)) if episode_ids is None else list(episode_ids)
        )
        if len(self._episode_ids) != self.num_envs:
            raise ValueError("episode_ids must have one entry per environment")
        self.squeeze_batch = (self.num_envs == 1) if squeeze_batch is None else bool(squeeze_batch)

        self.host = RelayCorridorHost(
            config,
            batch_size=self.num_envs,
            master_seed=self.master_seed,
            episode_ids=self._episode_ids,
        )

        self.n_agents = self.host.n_agents
        self.obs_dim = self.host.obs_dim
        self.state_dim = self.host.state_dim
        #: ADR 02 "Parameters": ``low_level_action_dim = K`` and ``n_z = K``.
        self.action_dim = config.low_level_action_dim
        self.n_z = config.n_z
        self.role_decode = config.role_decode

    # ------------------------------------------------------------------
    def episode_ids(self) -> Tuple[int, ...]:
        return tuple(int(x) for x in self._episode_ids)

    def advance_episode_ids(self, stride: Optional[int] = None) -> None:
        """Move every lane to its next episode id (ragged CRNs stay keyed)."""
        step = self.num_envs if stride is None else int(stride)
        self._episode_ids = [int(x) + step for x in self._episode_ids]

    # ------------------------------------------------------------------
    def reset(self, seed: Optional[int] = None) -> Tuple[np.ndarray, Dict[str, object]]:
        if seed is not None:
            self.master_seed = int(seed)
        self.host = RelayCorridorHost(
            self.config,
            batch_size=self.num_envs,
            master_seed=self.master_seed,
            episode_ids=self._episode_ids,
        )
        obs = self.host.observations()
        info = {
            "state": self._maybe_squeeze(self.host.global_state()),
            "state_info": self.host.info_snapshot(),
            "episode_ids": self.episode_ids(),
        }
        return self._maybe_squeeze(obs).astype(np.float32), info

    # ------------------------------------------------------------------
    def step(
        self,
        actions: np.ndarray,
        renew_mask: Optional[np.ndarray] = None,
        *,
        renew_indices: Optional[Iterable[int]] = None,
    ) -> Tuple[np.ndarray, object, object, object, Dict[str, object]]:
        """Take one corridor step from continuous low-level actions.

        ``actions`` are the low-level ``K``-vectors, shaped ``[N, K]`` (single
        environment) or ``[B, N, K]``; the host takes their ``argmax`` as the
        role.  ``renew_mask`` (or ``renew_indices``, the set ``S_t``) says which
        agents emit ``RENEW`` this step; everything else is ``KEEP``.

        Returns ``(observations, reward, terminated, truncated, info)`` where
        ``reward`` is the shared mean ``r_t`` delivered to the learner and
        ``info['service_indicators']`` carries every per-agent component.
        """
        actions = np.asarray(actions, dtype=np.float64)
        if actions.ndim == 2:
            actions = actions[None, ...]
        if actions.shape != (self.num_envs, self.n_agents, self.action_dim):
            raise ValueError(
                "actions must have shape "
                f"{(self.num_envs, self.n_agents, self.action_dim)}, got {actions.shape}"
            )
        roles = self.host.decode_roles(actions)

        mask = self._resolve_renew(renew_mask, renew_indices)
        obs, reward, terminated, info = self.host.step(roles, mask)

        step_info: Dict[str, object] = {
            "state": self._maybe_squeeze(self.host.global_state()),
            "state_info": self.host.info_snapshot(),
            "shared_reward": self._maybe_squeeze_scalar(reward),
            "service_indicators": self._maybe_squeeze(info["service_indicators"]),
            "per_agent_service_reward": self._maybe_squeeze(info["per_agent_service_reward"]),
            "roles": self._maybe_squeeze(info["roles"]),
            "renew_mask": self._maybe_squeeze(info["renew_mask"]),
            "lease_fresh": self._maybe_squeeze(info["lease_fresh"]),
            "role_correct": self._maybe_squeeze(info["role_correct"]),
            "segment_ages": self._maybe_squeeze(info["segment_ages"]),
            "change_flag": self._maybe_squeeze(info["change_flag"]),
            "cue": self._maybe_squeeze(info["cue"]),
            "dwell_age": self._maybe_squeeze(info["dwell_age"]),
            "probe_valid": self._maybe_squeeze(info["probe_valid"]),
            "coupling_field": self._maybe_squeeze(info["coupling_field"]),
            "t": info["t"],
        }
        truncated = terminated  # the corridor ends only by reaching H
        return (
            self._maybe_squeeze(obs).astype(np.float32),
            self._maybe_squeeze_scalar(reward),
            terminated,
            truncated,
            step_info,
        )

    # ------------------------------------------------------------------
    def _resolve_renew(
        self,
        renew_mask: Optional[np.ndarray],
        renew_indices: Optional[Iterable[int]],
    ) -> np.ndarray:
        if renew_mask is not None and renew_indices is not None:
            raise ValueError("pass renew_mask or renew_indices, not both")
        mask = np.zeros((self.num_envs, self.n_agents), dtype=bool)
        if renew_indices is not None:
            for index in renew_indices:
                mask[:, int(index)] = True
            return mask
        if renew_mask is None:
            return mask
        given = np.asarray(renew_mask).astype(bool)
        if given.ndim == 1:
            given = given[None, :]
        if given.shape != (self.num_envs, self.n_agents):
            raise ValueError(
                f"renew_mask must have shape {(self.num_envs, self.n_agents)}, got {given.shape}"
            )
        return given

    def _maybe_squeeze(self, array: np.ndarray) -> np.ndarray:
        array = np.asarray(array)
        if self.squeeze_batch and array.ndim >= 1 and array.shape[0] == 1:
            return array[0]
        return array

    def _maybe_squeeze_scalar(self, array: np.ndarray) -> object:
        array = np.asarray(array)
        if self.squeeze_batch and array.shape == (1,):
            return float(array[0])
        return array
