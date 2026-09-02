"""Vectorized NumPy relay corridor host (batch dimension first).

Pure NumPy: no torch, no native code, no imports from ``experiments/candidates``.

Step order (fixed by review Part V.2 note 1 and asserted directly by
``tests/relay_corridor_host_test.py`` test 8)::

    the event is realised in the transition into state t,
    the change flag is visible at t,
    the cue at t still shows the old latent (y_{r,t} = theta_{r,t-1}),
    RENEW at t is one zero-service step,
    service resumes at t + 1.

See :meth:`RelayCorridorHost.step` for the per-call ordering that realises it.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from envs.relay_corridor.config import RelayCorridorConfig
from envs.relay_corridor.rng import (
    STREAM_ENTITY,
    STREAM_REGION_EVENT,
    stream_generator,
)

__all__ = [
    "KEEP",
    "RENEW",
    "RelayCorridorHost",
    "obs_layout",
    "state_layout",
]

#: ``e_i`` values.  The ADR-01 adapter emits ``RENEW`` for exactly ``i in S_t``.
KEEP = 0
RENEW = 1


def obs_layout(config: RelayCorridorConfig) -> Dict[str, slice]:
    """Named index blocks of one agent observation vector.

    ``probe_theta``, ``probe_valid`` and ``coupling`` are the reserved fields:
    they are held at exactly zero while ``c_probe = 0`` and
    ``e5_coupling_enabled = False``, and they exist so that enabling either
    later does not change the state layout.
    """
    k = int(config.n_roles)
    r = int(config.n_regions)
    z = int(config.n_zones)
    cursor = 0

    def take(width: int) -> slice:
        nonlocal cursor
        block = slice(cursor, cursor + width)
        cursor += width
        return block

    layout = {
        "time": take(1),
        "lease_fresh": take(1),
        "segment_age": take(1),
        "held_role": take(k),
        "region": take(r),
        "zone": take(z),
        "change_flag": take(1),
        "dwell_age": take(1),
        "cue": take(k),
        "probe_theta": take(k),
        "probe_valid": take(1),
        "coupling": take(1),
    }
    layout["__total__"] = slice(0, cursor)
    return layout


def state_layout(config: RelayCorridorConfig) -> Dict[str, slice]:
    """Named index blocks of the global state vector."""
    k = int(config.n_roles)
    r = int(config.n_regions)
    z = int(config.n_zones)
    n = int(config.n_agents)
    cursor = 0

    def take(width: int) -> slice:
        nonlocal cursor
        block = slice(cursor, cursor + width)
        cursor += width
        return block

    layout = {"time": take(1)}
    region_block = 2 + k + k + 1 + 1  # flag, age, cue, probe theta, probe valid, coupling
    layout["regions"] = take(r * region_block)
    layout["region_block_width"] = region_block  # type: ignore[assignment]
    agent_block = 2 + k + r + z  # fresh, segment age, held role, region, zone
    layout["agents"] = take(n * agent_block)
    layout["agent_block_width"] = agent_block  # type: ignore[assignment]
    layout["__total__"] = slice(0, cursor)
    return layout


class RelayCorridorHost:
    """Two regions, ``Z`` zones, ``N`` agents pinned to region and zone.

    Region ``r`` carries a latent ``theta_r in {0..K-1}``; zone ``q`` requires
    role ``(q + theta_r) mod K``.  An event redraws ``theta_r`` uniformly among
    the ``K - 1`` other values, increments the regional epoch, and invalidates
    every regional lease.  Before costs::

        r_t = (Delta / N) * sum_i 1[ e_i = KEEP, lease_i fresh,
                                     a_i = (q_i + theta_{r_i}) mod K ]

    All arrays carry the batch dimension first.  Every batch lane is an
    independent episode identified by an *episode id*; the RNG streams are keyed
    by ``(master seed, episode, entity id)`` and ``(master seed, episode, region
    id)``, so a lane's tape does not depend on its batch position.
    """

    def __init__(
        self,
        config: RelayCorridorConfig,
        *,
        batch_size: int = 1,
        master_seed: int = 0,
        episode_ids: Optional[Sequence[int]] = None,
    ) -> None:
        self.config = config
        self.master_seed = int(master_seed)
        if episode_ids is None:
            episode_ids = list(range(int(batch_size)))
        self.episode_ids = np.asarray(list(episode_ids), dtype=np.int64)
        if self.episode_ids.ndim != 1 or self.episode_ids.size == 0:
            raise ValueError("episode_ids must be a non-empty 1-D sequence")
        self.batch_size = int(self.episode_ids.size)

        self.n_agents = int(config.n_agents)
        self.n_roles = int(config.n_roles)
        self.n_zones = int(config.n_zones)
        self.n_regions = int(config.n_regions)
        self.horizon = int(config.horizon)

        self.region_of_agent = config.region_of_agent
        self.zone_of_agent = config.zone_of_agent
        self.region_of_zone = config.region_of_zone

        self._laws = config.region_laws()
        max_age = self.horizon  # ages never exceed t <= H - 1 inside an episode
        self._hazard = np.stack(
            [law.hazard_table(max_age) for law in self._laws], axis=0
        )  # [R, H + 1]

        self.obs_slices = obs_layout(config)
        self.state_slices = state_layout(config)
        self.obs_dim = self.obs_slices["__total__"].stop
        self.state_dim = self.state_slices["__total__"].stop

        self._tapes: Dict[str, np.ndarray] = {}
        self.reset()

    # ------------------------------------------------------------------
    # tapes
    # ------------------------------------------------------------------
    def _build_tapes(self) -> None:
        """Draw every episode's tape from its own keyed stream.

        Region stream draw order is fixed: ``theta0``, then the ``H`` event
        uniforms, then the ``H`` switch-target uniforms.  Entity stream draw
        order is fixed: one initial held-role uniform.  Because each key owns a
        generator, the tapes are independent of batch order (invariant 2).
        """
        b, r, n, h = self.batch_size, self.n_regions, self.n_agents, self.horizon
        theta0 = np.empty((b, r), dtype=np.float64)
        event_u = np.empty((b, r, h), dtype=np.float64)
        switch_u = np.empty((b, r, h), dtype=np.float64)
        role0 = np.empty((b, n), dtype=np.float64)

        for lane, episode in enumerate(self.episode_ids):
            for region in range(r):
                gen = stream_generator(
                    self.master_seed, int(episode), STREAM_REGION_EVENT, region
                )
                theta0[lane, region] = gen.random()
                event_u[lane, region] = gen.random(h)
                switch_u[lane, region] = gen.random(h)
            for agent in range(n):
                gen = stream_generator(
                    self.master_seed, int(episode), STREAM_ENTITY, agent
                )
                role0[lane, agent] = gen.random()

        self._tapes = {
            "theta0": theta0,
            "event_u": event_u,
            "switch_u": switch_u,
            "role0": role0,
        }

    def stream_tapes(self) -> Dict[str, np.ndarray]:
        """Read-only view of the keyed tapes (used by the invariant-2 test)."""
        return {name: tape.copy() for name, tape in self._tapes.items()}

    # ------------------------------------------------------------------
    # episode lifecycle
    # ------------------------------------------------------------------
    def reset(self) -> Tuple[np.ndarray, Dict[str, object]]:
        """Reset every lane to ``t = 0`` and install the initial lease.

        The initial lease is installed *before scoring*, so ``t = 0`` costs no
        renewal outage.  The cue at reset is degenerate: there is no
        ``theta_{r,-1}``, so ``y_{r,0} = theta_{r,0}``; this is the reading that
        keeps ``J_greedy = J_sw`` exactly at ``K = 2`` (see the report).
        """
        self._build_tapes()
        b, r, n = self.batch_size, self.n_regions, self.n_agents

        self.t = 0
        self.done = False
        self.theta = np.floor(self._tapes["theta0"] * self.n_roles).astype(np.int64)
        np.clip(self.theta, 0, self.n_roles - 1, out=self.theta)
        self.epoch = np.zeros((b, r), dtype=np.int64)
        self.change_flag = np.zeros((b, r), dtype=np.int64)
        self.cue = self.theta.copy()
        self.dwell_age = np.zeros((b, r), dtype=np.int64)

        self.lease_epoch = np.zeros((b, n), dtype=np.int64)
        self.segment_age = np.zeros((b, n), dtype=np.int64)
        self.held_role = np.floor(self._tapes["role0"] * self.n_roles).astype(np.int64)
        np.clip(self.held_role, 0, self.n_roles - 1, out=self.held_role)

        # Reserved fields: exactly zero while c_probe = 0 and coupling is off.
        self.probe_theta = np.zeros((b, r, self.n_roles), dtype=np.float64)
        self.probe_valid = np.zeros((b, r), dtype=np.float64)
        self.coupling_field = np.zeros((b, r), dtype=np.float64)

        self.event_log: List[np.ndarray] = []
        return self.observations(), self.info_snapshot()

    # ------------------------------------------------------------------
    # derived quantities
    # ------------------------------------------------------------------
    @property
    def lease_fresh(self) -> np.ndarray:
        """A lease is fresh while its stamped epoch is still the region's epoch."""
        return self.lease_epoch == self.epoch[:, self.region_of_agent]

    def target_roles(self) -> np.ndarray:
        """``a*(q_i, theta_{r_i}) = (q_i + theta_{r_i}) mod K`` per agent, ``[B, N]``."""
        theta_of_agent = self.theta[:, self.region_of_agent]
        return (self.zone_of_agent[None, :] + theta_of_agent) % self.n_roles

    def decode_roles(self, continuous_actions: np.ndarray) -> np.ndarray:
        """``role_decode = argmax`` over the low-level ``K``-vector."""
        actions = np.asarray(continuous_actions)
        if actions.shape[-1] != self.n_roles:
            raise ValueError(
                f"low-level action must be a {self.n_roles}-vector, got {actions.shape}"
            )
        return np.argmax(actions, axis=-1).astype(np.int64)

    # ------------------------------------------------------------------
    # step
    # ------------------------------------------------------------------
    def step(
        self,
        roles: np.ndarray,
        renew_mask: Optional[np.ndarray] = None,
        *,
        build_obs: bool = True,
    ) -> Tuple[Optional[np.ndarray], np.ndarray, bool, Dict[str, object]]:
        """Score the action at ``t`` and then realise the transition into ``t + 1``.

        Review Part V.2 note 1 fixes the order, realised here as:

        1. **Score at t.**  ``serve_i = (e_i = KEEP) and lease_i fresh and
           a_i = a*(q_i, theta_{r_i})``; ``r_t = (Delta / N) * sum_i serve_i``.
           A ``RENEW`` at ``t`` therefore contributes exactly zero: it is one
           zero-service step.
        2. **Apply RENEW at t.**  The renewing agent's lease is stamped with the
           region's *current* epoch, its held role becomes the role it emitted
           this step, and its segment age restarts at zero.
        3. **Transition into t + 1.**  One event is drawn per region from the
           keyed tape against the dwell hazard at the current age.  On an event
           ``theta_r`` is redrawn uniformly among the ``K - 1`` other values, the
           regional epoch increments (invalidating every regional lease), the
           dwell age restarts, and the change flag is raised **at t + 1**.  The
           cue is written *before* the latent moves, so ``y_{r,t+1} =
           theta_{r,t}`` still shows the old latent; service resumes at ``t + 2``.

        There are ``H`` scored steps (``t = 0 .. H - 1``) and therefore ``H - 1``
        transitions: the final call scores ``t = H - 1`` and draws no event.

        ``build_obs=False`` skips assembling the observation array and returns
        ``None`` in its place.  It isolates the mechanics cost the speed note
        describes (two event updates, indexed target-role gathers, freshness and
        renew masks, one Boolean reduction over ``[batch, N]``, cue and age
        updates) from the cost of laying out observation vectors.
        """
        if self.done:
            raise RuntimeError("episode is finished; call reset()")

        b, n = self.batch_size, self.n_agents
        roles = np.asarray(roles, dtype=np.int64)
        if roles.shape != (b, n):
            raise ValueError(f"roles must have shape {(b, n)}, got {roles.shape}")
        if np.any(roles < 0) or np.any(roles >= self.n_roles):
            raise ValueError("roles must lie in [0, K)")

        if renew_mask is None:
            renew = np.zeros((b, n), dtype=bool)
        else:
            renew = np.asarray(renew_mask).astype(bool)
            if renew.shape != (b, n):
                raise ValueError(f"renew_mask must have shape {(b, n)}, got {renew.shape}")

        # 1. score at t
        fresh = self.lease_fresh
        correct = roles == self.target_roles()
        service = (~renew) & fresh & correct
        reward = (self.config.delta / float(n)) * service.sum(axis=1).astype(np.float64)

        step_index = self.t
        info = {
            "t": step_index,
            "roles": roles.copy(),
            "renew_mask": renew.copy(),
            "service_indicators": service.copy(),
            "per_agent_service_reward": (self.config.delta / float(n)) * service.astype(np.float64),
            "lease_fresh": fresh.copy(),
            "role_correct": correct.copy(),
            "shared_reward": reward.copy(),
            "segment_ages": self.segment_age.copy(),
            "change_flag": self.change_flag.copy(),
            "cue": self.cue.copy(),
            "dwell_age": self.dwell_age.copy(),
            "coupling_field": self.coupling_field.copy(),
            "probe_valid": self.probe_valid.copy(),
        }

        # 2. apply RENEW at t (stamps the current regional epoch)
        if renew.any():
            agent_epoch = self.epoch[:, self.region_of_agent]
            self.lease_epoch = np.where(renew, agent_epoch, self.lease_epoch)
            self.held_role = np.where(renew, roles, self.held_role)
            self.segment_age = np.where(renew, 0, self.segment_age)

        # 3. transition into t + 1 (skipped after the last scored step)
        if step_index + 1 < self.horizon:
            hazard = self._hazard[np.arange(self.n_regions), np.minimum(self.dwell_age, self.horizon)]
            event = self._tapes["event_u"][:, :, step_index] < hazard
            self.cue = self.theta.copy()  # y_{r,t+1} = theta_{r,t}
            if event.any():
                offset = np.floor(
                    self._tapes["switch_u"][:, :, step_index] * (self.n_roles - 1)
                ).astype(np.int64)
                np.clip(offset, 0, max(self.n_roles - 2, 0), out=offset)
                new_theta = (self.theta + 1 + offset) % self.n_roles
                self.theta = np.where(event, new_theta, self.theta)
                self.epoch = self.epoch + event.astype(np.int64)
            self.change_flag = event.astype(np.int64)
            self.dwell_age = np.where(event, 0, self.dwell_age + 1)
            self.segment_age = self.segment_age + 1
            self.event_log.append(event.copy())
            self.t = step_index + 1
            terminated = False
        else:
            terminated = True
            self.done = True

        info["event_realised_into_next"] = (
            self.event_log[-1].copy() if self.event_log and not terminated
            else np.zeros((b, self.n_regions), dtype=bool)
        )
        obs = self.observations() if build_obs else None
        return obs, reward, terminated, info

    # ------------------------------------------------------------------
    # public state
    # ------------------------------------------------------------------
    def observations(self) -> np.ndarray:
        """Per-agent observation array ``[B, N, obs_dim]`` built from public state."""
        b, n = self.batch_size, self.n_agents
        k, r, z = self.n_roles, self.n_regions, self.n_zones
        obs = np.zeros((b, n, self.obs_dim), dtype=np.float64)
        sl = self.obs_slices

        obs[:, :, sl["time"]] = self.t / float(self.horizon)
        obs[:, :, sl["lease_fresh"]] = self.lease_fresh.astype(np.float64)[:, :, None]
        obs[:, :, sl["segment_age"]] = (self.segment_age / float(self.horizon))[:, :, None]
        obs[:, :, sl["held_role"]] = _one_hot(self.held_role, k)
        obs[:, :, sl["region"]] = _one_hot(
            np.broadcast_to(self.region_of_agent, (b, n)), r
        )
        obs[:, :, sl["zone"]] = _one_hot(np.broadcast_to(self.zone_of_agent, (b, n)), z)

        agent_region = self.region_of_agent
        obs[:, :, sl["change_flag"]] = self.change_flag[:, agent_region].astype(np.float64)[:, :, None]
        obs[:, :, sl["dwell_age"]] = (
            self.dwell_age[:, agent_region] / float(self.horizon)
        )[:, :, None]
        obs[:, :, sl["cue"]] = _one_hot(self.cue[:, agent_region], k)
        obs[:, :, sl["probe_theta"]] = self.probe_theta[:, agent_region, :]
        obs[:, :, sl["probe_valid"]] = self.probe_valid[:, agent_region][:, :, None]
        obs[:, :, sl["coupling"]] = self.coupling_field[:, agent_region][:, :, None]
        return obs

    def global_state(self) -> np.ndarray:
        """Global state array ``[B, state_dim]``."""
        b = self.batch_size
        k, r, z, n = self.n_roles, self.n_regions, self.n_zones, self.n_agents
        state = np.zeros((b, self.state_dim), dtype=np.float64)
        sl = self.state_slices
        state[:, sl["time"]] = self.t / float(self.horizon)

        region_block = np.concatenate(
            [
                self.change_flag.astype(np.float64)[:, :, None],
                (self.dwell_age / float(self.horizon))[:, :, None],
                _one_hot(self.cue, k),
                self.probe_theta,
                self.probe_valid[:, :, None],
                self.coupling_field[:, :, None],
            ],
            axis=2,
        )
        state[:, sl["regions"]] = region_block.reshape(b, -1)

        agent_block = np.concatenate(
            [
                self.lease_fresh.astype(np.float64)[:, :, None],
                (self.segment_age / float(self.horizon))[:, :, None],
                _one_hot(self.held_role, k),
                _one_hot(np.broadcast_to(self.region_of_agent, (b, n)), r),
                _one_hot(np.broadcast_to(self.zone_of_agent, (b, n)), z),
            ],
            axis=2,
        )
        state[:, sl["agents"]] = agent_block.reshape(b, -1)
        return state

    def public_state_records(self, lane: int = 0) -> Dict[str, List[Dict[str, object]]]:
        """The ragged, unpadded public state of one lane (invariant 1).

        Records are emitted at the live cardinality with no padding row, no
        padding column, and no sentinel value: ``len(agents) == N`` exactly.
        Raggedness is a *family* boundary property; ``rho = 0`` keeps the
        cardinality fixed inside an E2-E4 object, but the boundary never pads.
        """
        regions = [
            {
                "region_id": int(region),
                "change_flag": int(self.change_flag[lane, region]),
                "dwell_age": int(self.dwell_age[lane, region]),
                "cue": int(self.cue[lane, region]),
                "probe_theta": self.probe_theta[lane, region].copy(),
                "probe_valid": float(self.probe_valid[lane, region]),
                "coupling": float(self.coupling_field[lane, region]),
            }
            for region in range(self.n_regions)
        ]
        zones = [
            {"zone_id": int(zone), "region_id": int(self.region_of_zone[zone])}
            for zone in range(self.n_zones)
        ]
        fresh = self.lease_fresh
        agents = [
            {
                "agent_id": int(agent),
                "region_id": int(self.region_of_agent[agent]),
                "zone_id": int(self.zone_of_agent[agent]),
                "held_role": int(self.held_role[lane, agent]),
                "lease_fresh": bool(fresh[lane, agent]),
                "segment_age": int(self.segment_age[lane, agent]),
            }
            for agent in range(self.n_agents)
        ]
        return {"regions": regions, "zones": zones, "agents": agents}

    @property
    def record_padding(self) -> bool:
        """The host boundary never pads its records."""
        return False

    def info_snapshot(self) -> Dict[str, object]:
        return {
            "state": self.global_state(),
            "t": self.t,
            "change_flag": self.change_flag.copy(),
            "cue": self.cue.copy(),
            "dwell_age": self.dwell_age.copy(),
            "lease_fresh": self.lease_fresh.copy(),
            "segment_ages": self.segment_age.copy(),
            "held_role": self.held_role.copy(),
            "probe_valid": self.probe_valid.copy(),
            "coupling_field": self.coupling_field.copy(),
            "private": {"theta": self.theta.copy(), "epoch": self.epoch.copy()},
        }

    # ------------------------------------------------------------------
    # oracle access (host-private; exact references only)
    # ------------------------------------------------------------------
    def private_theta(self) -> np.ndarray:
        """Current latent, host-private: exposed only to the exact oracles."""
        return self.theta.copy()

    def dwell_lengths(self, lane: int, region: int) -> np.ndarray:
        """Completed dwell lengths observed on one lane and region.

        The first dwell starts at reset (a *full* dwell, no residual-life
        phase), so the ``j``-th completed dwell ends at the ``j``-th event.
        """
        if not self.event_log:
            return np.zeros(0, dtype=np.int64)
        events = np.stack(self.event_log, axis=0)[:, lane, region]  # transition into t+1
        times = np.flatnonzero(events) + 1  # event realised into step index t + 1
        if times.size == 0:
            return np.zeros(0, dtype=np.int64)
        return np.diff(np.concatenate(([0], times)))


def _one_hot(index: np.ndarray, width: int) -> np.ndarray:
    index = np.asarray(index, dtype=np.int64)
    out = np.zeros(index.shape + (int(width),), dtype=np.float64)
    np.put_along_axis(out, index[..., None], 1.0, axis=-1)
    return out
