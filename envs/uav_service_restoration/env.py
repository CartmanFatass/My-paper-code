"""``uav_service_restoration_v0``: a PettingZoo ParallelEnv.

Question posed by this environment: after a terrestrial site fails, or spatiotemporal load
pressure arises, how much undelivered traffic can UAV position decisions - which cost
travel time - remove, under access, backhaul and shared-capacity constraints?

What is simulated, and what is not
----------------------------------
* Spatial/temporal variation in communication activity comes from the configured demand
  source.  It is real aggregated activity only when that source says so
  (``metadata().is_real_activity_data``).
* Offered traffic is a **demand proxy** mapped from activity.  It is not measured Mbps,
  not a population count and not individual traffic.
* Terrestrial sites, capacities and failures are this configuration's scenario.  They are
  not an operator's real topology and not recorded outages.
* Propagation and resource allocation are parameterized simulations
  (:mod:`envs.uav_service_restoration.radio`,
  :mod:`envs.uav_service_restoration.scheduler`).
* UAV motion is finite-speed kinematics with a ``motion_effort`` proxy.  There is no
  validated flight control, no endurance model and no field deployment claim.

Time semantics
--------------
One decision interval holds the action.  The interval is partitioned at event boundaries
and source-demand boundaries, then subdivided into physics substeps of at most
``physics_dt_s``.  Within each substep the active exogenous state is applied, motion
advances, and service is evaluated by the fixed scheduler at the substep's quadrature
point (midpoint by default).  A UAV is never teleported to its end-of-interval position
before its service is computed.

Lifecycle
---------
Demand service is a **continuing** task by default: the end of the external evaluation
window sets ``truncated=True`` for every agent, and ``terminated`` stays ``False``.
``semantics='finite_horizon'`` is available and then sets ``terminated=True`` instead;
that is a different task definition, declared in configuration, not a flag flipped to
suit a trainer.

Reward
------
``r = -(integral of unmet demand) / (D_ref * dt_ref) - motion_weight * (integral of
motion effort) / dt_ref``, identical for every UAV.  References are fixed by
configuration and never adapt per episode.  There is no reward for holding a formation,
switching a skill, taking a role, or approaching a chosen hotspot.  The same team reward
is returned for each agent and is **not** divided by the UAV count.
"""

from __future__ import annotations

import contextlib

import copy
from typing import Any, Sequence

import numpy as np
from gymnasium.spaces import Box
from pettingzoo.utils.env import ParallelEnv

from . import dynamics as dyn
from . import network as net
from . import scheduler as sched
from .config import EnvConfig
from .demand import build_demand_source
from .events import EventSchedule, sample_schedule
from .metrics import EpisodeAccumulator, SubintervalRecord
from .observations import (
    DemandPointLayout,
    ObservationBuilder,
    TelemetryStore,
    sensed_demand_mask,
)
from .types import DemandFrame, EpisodeDescriptor, SiteState, TelemetryRecord

#: Explicit allowlist of keys the environment puts into the per-agent ``info`` mapping.
#: Everything here is an aggregate of an already completed interval.  Privileged
#: diagnostics are reachable only through :meth:`UAVServiceRestorationEnv.
#: get_privileged_diagnostics`, which no training path reads.
TRAINING_INFO_FIELDS = ("scenario", "agent_index", "reward_info")

REWARD_INFO_FIELDS = (
    "unmet_mbit_interval",
    "delivered_mbit_interval",
    "offered_mbit_interval",
    "motion_effort_integral_s",
    "service_term",
    "motion_term",
    "reward_total",
    "reference_scale_mbps",
    "reference_dt_s",
)

_RNG_STREAM_NAMES = ("episode", "layout", "events", "observation_noise", "channel")


@contextlib.contextmanager
def _readonly(*arrays: np.ndarray):
    """Make arrays temporarily read-only while a diagnostic observer holds them.

    The capture seam hands the observer live arrays that this module reads back afterwards -
    one of them becomes the simulation's own position state. The observer is contractually
    required to copy anything it retains; this turns a violation of that contract into an
    immediate ``ValueError`` instead of a silently altered reward. Only the armed branch pays
    for it, and the original flags are restored even if the observer raises.
    """

    previous = [array.flags.writeable for array in arrays]
    for array in arrays:
        array.flags.writeable = False
    try:
        yield
    finally:
        for array, was_writeable in zip(arrays, previous):
            array.flags.writeable = was_writeable


class UAVServiceRestorationEnv(ParallelEnv):
    """Cooperative multi-UAV access-and-backhaul service restoration."""

    metadata = {
        "name": "uav_service_restoration_v0",
        "is_parallelizable": True,
        "render_modes": [],
    }

    def __init__(
        self,
        config: EnvConfig,
        *,
        demand_source: Any | None = None,
        dataset_root: str | None = None,
        render_mode: str | None = None,
        seed: int | None = None,
    ) -> None:
        super().__init__()
        config.validate()
        self._config = config
        self.render_mode = render_mode
        self._base_seed = int(config.seed if seed is None else seed)
        self._episode_index = -1

        origin = (float(config.region.min_xy_m[0]), float(config.region.min_xy_m[1]))
        self._source = (
            demand_source
            if demand_source is not None
            else build_demand_source(
                config.source, dataset_root=dataset_root, origin_m=origin
            )
        )
        self._source_metadata = self._source.metadata()
        self._interval_ms = int(round(float(self._source_metadata.interval_duration_s) * 1000.0))

        self._layout = DemandPointLayout.build(
            self._source.cell_positions_m(),
            int(config.source.max_demand_points),
            config.observations.on_entity_limit_exceeded,
        )
        self._demand_positions_m = net.demand_positions_from_xy(self._layout.positions_m, 0.0)
        self._builder = ObservationBuilder(config, self._layout)

        self.possible_agents = [f"uav_{index}" for index in range(int(config.n_uavs))]
        self.agents: list[str] = []
        self._agent_index = {agent: index for index, agent in enumerate(self.possible_agents)}

        obs_space = Box(
            low=-np.inf,
            high=np.inf,
            shape=(self._builder.obs_dim,),
            dtype=np.float32,
        )
        act_space = Box(low=-1.0, high=1.0, shape=(dyn.ACTION_DIM,), dtype=np.float32)
        # The Parallel API requires the identical space object per agent across calls.
        self._observation_spaces = {agent: obs_space for agent in self.possible_agents}
        self._action_spaces = {agent: act_space for agent in self.possible_agents}
        self.state_space = Box(
            low=-np.inf, high=np.inf, shape=(self._builder.state_dim,), dtype=np.float32
        )

        self._site_positions_m = np.asarray(
            [site.position_m for site in config.network.sites], dtype=np.float64
        )
        access_model = config.network.radio_models["site_access"]
        self._site_registration_radius_m = float(
            config.network.site_access_radius_m
            if config.network.site_access_radius_m is not None
            else access_model.max_range_m
        )

        self._store = TelemetryStore(
            n_uavs=int(config.n_uavs),
            n_sites=len(config.network.sites),
            n_demand_slots=self._layout.n_slots,
        )

        # Attributes legacy diagnostics look for by name; harmless and read-only.
        self.n_uavs = int(config.n_uavs)
        self.area_size = float(
            max(
                config.region.max_xy_m[0] - config.region.min_xy_m[0],
                config.region.max_xy_m[1] - config.region.min_xy_m[1],
            )
        )
        self.max_steps = int(config.n_decision_steps)
        self.time_step = float(config.episode.decision_dt_s)
        self.max_speed = float(config.dynamics.max_speed_mps)
        self.height_range = tuple(float(value) for value in config.dynamics.altitude_range_m)

        # Optional human-diagnostic capture observer.  ``None`` is the only state any
        # training or evaluation path ever sets, and on that path the seams below cost one
        # attribute load and one ``is not None`` test per decision step and per substep.
        # See :meth:`set_capture_observer`.
        self._capture_observer: Any | None = None

        self._reset_episode_state()

    # ----------------------------------------------------------------------------------
    # Spaces and dimensions
    # ----------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------
    # Optional diagnostic capture seam
    # ----------------------------------------------------------------------------------

    def set_capture_observer(self, observer: Any | None) -> None:
        """Attach or detach a human-diagnostic observer.  Default and only training state
        is ``None``.

        The observer is a duck-typed object supplied by the explicit visualization layer.
        This environment imports no renderer, server or browser library, and the observer
        never influences dynamics: it receives values that were *already computed* for the
        simulation and may only read them.

        Required protocol - every one of these is called unconditionally, with no
        ``hasattr`` guard, so an observer missing any of them raises::

            observer.begin_decision(env, decision_step, time_s) -> None
            observer.armed -> bool
            observer.on_service_evaluated(**kwargs) -> None      # only when ``armed``
            observer.on_decision_complete(**kwargs) -> None
            observer.on_episode_reset(env, time_s) -> None

        ``decision_step`` is the index of the interval being computed, and it is the same
        value at all three of ``begin_decision``, ``on_service_evaluated`` and
        ``on_decision_complete``.  ``on_service_evaluated`` receives both
        ``window_start_s`` (the start of the measurement window) and ``geometry_time_s``
        (the quadrature point the handed-over positions actually hold at); under the default
        midpoint rule these differ by half a substep and must not be conflated.

        ``begin_decision`` is where the observer decides, once per decision interval,
        whether this interval is eligible at all.  ``armed`` is then a plain attribute
        read, so an ineligible interval performs no substep work beyond that read.  The
        observer must copy anything it retains: the arrays it is handed belong to the
        caller and the later substeps of the same interval will reuse or replace them.

        Setting an observer must not change any scientific quantity.  A capture that
        raises is the caller's defect and is not absorbed here, so a broken observer is
        visible instead of silently corrupting a diagnostic stream.  An observer that is
        optional to the operator - a live preview - is expected to absorb its own errors
        before they reach this seam; ``ServiceRestorationObserver`` does exactly that.

        While a callback runs, the numpy arrays handed to it are made read-only, so an
        observer that writes into one fails immediately rather than altering a reward.
        The observer must still copy anything it keeps past the call: the arrays belong to
        the caller and later substeps reuse or replace them.
        """

        self._capture_observer = observer

    @property
    def capture_observer(self) -> Any | None:
        return self._capture_observer

    def capture_capabilities(self) -> dict[str, Any]:
        """What a scene captured from this environment can truthfully contain."""

        return {
            "environment_id": self._config.environment_id,
            "preset_name": self._config.preset_name,
            "entity_kind_ground": "aggregate_demand_point",
            "individual_ues": False,
            "aggregate_demand": True,
            "demand_rates": True,
            "delivered_rates": True,
            "links": True,
            "link_flows": True,
            "link_capacity": True,
            "resource_domains": True,
            "candidate_paths": True,
            "sinr": True,
            "skill_labels": False,
            "energy": False,
            "roster_changes": False,
            "observation_view": True,
            "quadrature": self._config.episode.quadrature,
            "physics_dt_s": float(self._config.episode.physics_dt_s),
            "decision_dt_s": float(self._config.episode.decision_dt_s),
            "notes": [
                "ground entities are aggregated demand proxies for source grid cells, "
                "not individual people or tracked devices",
                "service is evaluated at the substep quadrature point; the displayed "
                "geometry belongs to that point, not to the interval end position",
            ],
        }

    def observation_space(self, agent: str) -> Box:
        return self._observation_spaces[agent]

    def action_space(self, agent: str) -> Box:
        return self._action_spaces[agent]

    def get_obs_dim(self) -> int:
        return int(self._builder.obs_dim)

    def get_state_dim(self) -> int:
        return int(self._builder.state_dim)

    def schema(self) -> dict[str, Any]:
        """Observation/action/state/reward/termination contract, for the delivery report."""

        config = self._config
        return {
            "environment_id": config.environment_id,
            "preset_name": config.preset_name,
            "n_agents": int(config.n_uavs),
            "action_space": {
                "shape": [dyn.ACTION_DIM],
                "low": -1.0,
                "high": 1.0,
                "dtype": "float32",
                "meaning": "normalised 3-D velocity request, vector-norm speed limited",
            },
            "observation_space": {
                "shape": [self._builder.obs_dim],
                "dtype": "float32",
                "bounds": "unbounded Box; features are normalised but not hard clipped",
            },
            "state": {"shape": [self._builder.state_dim], "dtype": "float32"},
            "reward": {
                "definition": (
                    "-(integral of unmet demand in Mbit)/(reference_scale_mbps * "
                    "reference_dt_s) - motion_weight * (integral of motion effort in s)/"
                    "reference_dt_s"
                ),
                "reference_scale_mbps": float(config.reward.reference_scale_mbps),
                "reference_dt_s": float(config.reward.reference_dt_s),
                "motion_weight": float(config.reward.motion_weight),
                "team_reward": "identical scalar per agent; never divided by n_uavs",
            },
            "termination": {
                "semantics": config.episode.semantics,
                "terminated": (
                    "always False in 'continuing'; True at the horizon in "
                    "'finite_horizon'"
                ),
                "truncated": (
                    "True for every agent at the end of the external window in "
                    "'continuing'"
                ),
                "final_observation": "the real terminal observation is returned",
            },
            "information_condition": self._builder.schema(),
            "demand_source": {
                "kind": self._source_metadata.kind,
                "is_real_activity_data": bool(self._source_metadata.is_real_activity_data),
                "dataset_hash": self._source_metadata.dataset_hash,
                "demand_scale_mbps": self._source_metadata.demand_scale_mbps,
                "activity_reference_scale": self._source_metadata.activity_reference_scale,
            },
            "info_allowlist": list(TRAINING_INFO_FIELDS),
            "reward_info_fields": list(REWARD_INFO_FIELDS),
        }

    # ----------------------------------------------------------------------------------
    # Episode state
    # ----------------------------------------------------------------------------------

    def _reset_episode_state(self) -> None:
        n = int(self._config.n_uavs)
        self._positions_m = np.zeros((n, 3), dtype=np.float64)
        self._velocities_mps = np.zeros((n, 3), dtype=np.float64)
        self._time_s = 0.0
        self._step_index = 0
        self._schedule = EventSchedule(events=(), n_sites=len(self._config.network.sites))
        self._episode: EpisodeDescriptor | None = None
        self._accumulator = EpisodeAccumulator(
            n_demand_points=self._layout.n_slots, n_uavs=n
        )
        self._alert_time_s: float | None = None
        self._alert_raised = False
        self._rngs: dict[str, np.random.Generator] = {}
        self._last_result_status = "none"
        self._store.clear()

    def _spawn_rngs(self, base_seed: int, episode_index: int) -> None:
        """Independent RNG streams; the global NumPy state is never touched."""

        sequence = np.random.SeedSequence([int(base_seed), int(episode_index)])
        children = sequence.spawn(len(_RNG_STREAM_NAMES))
        self._rngs = {
            name: np.random.default_rng(child)
            for name, child in zip(_RNG_STREAM_NAMES, children)
        }

    # ----------------------------------------------------------------------------------
    # Time and demand plumbing
    # ----------------------------------------------------------------------------------

    def _utc_ms_at(self, time_s: float) -> int:
        assert self._episode is not None
        return int(self._episode.start_utc_ms + int(round(float(time_s) * 1000.0)))

    def _demand_boundaries_within(self, start_s: float, end_s: float) -> tuple[float, ...]:
        """Source-interval boundaries strictly inside ``(start_s, end_s)``, in seconds."""

        assert self._episode is not None
        interval_ms = self._interval_ms
        base = int(self._episode.start_utc_ms)
        first_ms = int(np.ceil((base + start_s * 1000.0) / interval_ms)) * interval_ms
        found: list[float] = []
        cursor = first_ms
        while True:
            offset = (cursor - base) / 1000.0
            if offset >= end_s - 1e-12:
                break
            if offset > start_s + 1e-12:
                found.append(float(offset))
            cursor += interval_ms
        return tuple(found)

    def _demand_frame_at(self, time_s: float) -> DemandFrame:
        assert self._episode is not None
        return self._source.read_interval(self._episode, self._utc_ms_at(time_s))

    def _slot_demand(
        self, frame: DemandFrame, time_s: float
    ) -> tuple[np.ndarray, np.ndarray]:
        """Aggregate a source frame onto demand slots and apply any synthetic overlay.

        An overlay is a *constructed* load envelope, recorded as
        ``event_source='synthetic_overlay'``.  It is never described as a real gathering.
        """

        demand = self._layout.aggregate_demand(frame.demand_mbps)
        observed = self._layout.aggregate_mask(frame.observed_mask)
        overlay = self._config.source.event_overlay
        if overlay is not None and float(overlay.start_s) <= float(time_s) < float(overlay.end_s):
            indices = np.asarray(overlay.cell_indices, dtype=np.int64)
            valid = indices[(indices >= 0) & (indices < demand.shape[0])]
            demand = demand.copy()
            demand[valid] *= float(overlay.peak_gain)
        return demand, observed

    def _site_states_at(self, time_s: float) -> tuple[SiteState, ...]:
        return self._schedule.site_states(float(time_s))

    # ----------------------------------------------------------------------------------
    # Service evaluation
    # ----------------------------------------------------------------------------------

    def _evaluate_service(
        self,
        positions_m: np.ndarray,
        site_states: Sequence[SiteState],
        demand_mbps: np.ndarray,
    ) -> Any:
        snapshot = net.build_snapshot(
            self._config.network,
            site_states,
            positions_m,
            self._demand_positions_m,
            demand_mbps,
        )
        result = sched.solve_or_raise(snapshot, self._config.scheduler)
        self._last_result_status = result.status.value
        return snapshot, result

    # ----------------------------------------------------------------------------------
    # Reset
    # ----------------------------------------------------------------------------------

    def reset(
        self, seed: int | None = None, options: dict | None = None
    ) -> tuple[dict[str, np.ndarray], dict[str, dict]]:
        config = self._config
        if seed is not None:
            self._base_seed = int(seed)
            self._episode_index = 0
        else:
            self._episode_index += 1
        self._reset_episode_state()
        self._spawn_rngs(self._base_seed, self._episode_index)

        split = str((options or {}).get("split", config.source.split))
        history_intervals = int((options or {}).get("history_intervals", 1))
        self._episode = self._source.sample_episode(
            split,
            self._rngs["episode"],
            duration_s=float(config.episode.duration_s),
            history_intervals=history_intervals,
        )

        self._schedule = sample_schedule(
            config.events,
            config.network.sites,
            self._rngs["events"],
            episode_duration_s=float(config.episode.duration_s),
        )

        if config.deployment.mode == "reactive_launch":
            start_positions = np.asarray(config.deployment.standby_positions_m, dtype=np.float64)
            loss = self._schedule.first_capability_loss_time_s()
            self._alert_time_s = (
                None if loss is None else float(loss) + float(config.deployment.alert_delay_s)
            )
        else:
            start_positions = np.asarray(config.deployment.positions_m, dtype=np.float64)
            self._alert_time_s = None
        self._positions_m = start_positions.reshape(-1, 3).copy()
        self._velocities_mps = np.zeros_like(self._positions_m)
        if not dyn.valid_initial_positions(self._positions_m, config.dynamics, config.region):
            raise ValueError("configured initial UAV positions are outside the flight box")
        self._alert_raised = self._alert_time_s is not None and self._alert_time_s <= 0.0

        self._accumulator = EpisodeAccumulator(
            n_demand_points=self._layout.n_slots,
            n_uavs=int(config.n_uavs),
            affected_mask=None,
        )
        self._seed_history_telemetry(history_intervals)

        self.agents = list(self.possible_agents)
        observations = self._observations()
        infos = {
            agent: {
                "scenario": config.preset_name,
                "agent_index": self._agent_index[agent],
                "reward_info": {},
            }
            for agent in self.agents
        }
        observer = self._capture_observer
        if observer is not None:
            observer.on_episode_reset(env=self, time_s=float(self._time_s))
        return observations, infos

    def _seed_history_telemetry(self, history_intervals: int) -> None:
        """Ingest the terrestrial network's own pre-episode service records.

        These are measurements of intervals that *precede* the episode window, produced
        with no UAVs present and the pre-episode site capability.  They give the first
        observation legitimate history without revealing any part of the episode's own
        first window.
        """

        assert self._episode is not None
        if history_intervals <= 0:
            return
        interval_ms = self._interval_ms
        for step_back in range(history_intervals, 0, -1):
            timestamp = int(self._episode.start_utc_ms - step_back * interval_ms)
            if timestamp < int(self._episode.history_start_utc_ms):
                continue
            frame = self._source.read_interval(self._episode, timestamp)
            demand = self._layout.aggregate_demand(frame.demand_mbps)
            observed_source = self._layout.aggregate_mask(frame.observed_mask)
            site_states = self._site_states_at(0.0)
            no_uavs = np.zeros((0, 3), dtype=np.float64)
            snapshot = net.build_snapshot(
                self._config.network, site_states, no_uavs, self._demand_positions_m, demand
            )
            result = sched.solve_or_raise(snapshot, self._config.scheduler)
            sensed = sensed_demand_mask(
                self._demand_positions_m,
                no_uavs,
                self._site_positions_m,
                site_states,
                float(self._config.observations.sensing_radius_m),
                self._site_registration_radius_m,
            )
            interval_end_s = -float(step_back - 1) * (interval_ms / 1000.0)
            self._store.submit(
                TelemetryRecord(
                    interval_start_s=interval_end_s - interval_ms / 1000.0,
                    interval_end_s=interval_end_s,
                    release_time_s=interval_end_s
                    + float(self._config.observations.telemetry_delay_s),
                    uav_positions_m=self._positions_m.copy(),
                    uav_velocities_mps=self._velocities_mps.copy(),
                    site_state_vectors=np.stack([state.as_vector() for state in site_states]),
                    site_state_observed=np.ones(len(site_states), dtype=bool),
                    demand_offered_mbps=demand,
                    demand_delivered_mbps=result.delivered_mbps_per_demand,
                    demand_observed=sensed & observed_source,
                )
            )
        self._store.release_due(0.0)

    # ----------------------------------------------------------------------------------
    # Step
    # ----------------------------------------------------------------------------------

    def step(
        self, actions: dict[str, np.ndarray]
    ) -> tuple[
        dict[str, np.ndarray],
        dict[str, float],
        dict[str, bool],
        dict[str, bool],
        dict[str, dict],
    ]:
        if not self.agents:
            raise RuntimeError(
                "step() called after every agent finished; call reset() first. The "
                "environment never performs an implicit second reset inside a decision "
                "interval."
            )
        config = self._config
        missing = [agent for agent in self.agents if agent not in actions]
        if missing:
            raise ValueError(f"step() is missing actions for active agents: {missing}")
        unexpected = sorted(set(actions) - set(self.possible_agents))
        if unexpected:
            raise ValueError(f"step() received actions for unknown agents: {unexpected}")

        stacked = np.stack(
            [np.asarray(actions[agent], dtype=np.float64).reshape(-1) for agent in self.possible_agents]
        )
        if stacked.shape != (int(config.n_uavs), dyn.ACTION_DIM):
            raise ValueError(
                f"action array has shape {stacked.shape}; expected "
                f"{(int(config.n_uavs), dyn.ACTION_DIM)}"
            )
        requested = dyn.requested_velocity_mps(stacked, config.dynamics)

        t0 = float(self._time_s)
        t1 = t0 + float(config.episode.decision_dt_s)

        held = self._is_held_at_standby(t0)
        if held:
            requested = np.zeros_like(requested)

        segment_edges = sorted(
            {t0, t1}
            | set(self._schedule.boundaries_within(t0, t1))
            | set(self._demand_boundaries_within(t0, t1))
        )

        # Optional diagnostic capture.  One attribute load; when nothing is attached the
        # remaining seams in this method are a single ``is not None`` test each.
        observer = self._capture_observer
        # Captured before ``_step_index`` advances, and reused by every seam in this method.
        # Reading the attribute again after the increment made ``on_decision_complete``
        # report k+1 for the same interval the other two seams reported as k.
        decision_index = self._step_index
        if observer is not None:
            observer.begin_decision(self, decision_step=decision_index, time_s=t0)
        substep_index = 0

        interval_offered = np.zeros(self._layout.n_slots, dtype=np.float64)
        interval_delivered = np.zeros(self._layout.n_slots, dtype=np.float64)
        interval_sensed = np.zeros(self._layout.n_slots, dtype=bool)
        interval_source_observed = np.ones(self._layout.n_slots, dtype=bool)
        unmet_mbit = 0.0
        delivered_mbit = 0.0
        offered_mbit = 0.0
        motion_integral_s = 0.0

        for left, right in zip(segment_edges[:-1], segment_edges[1:]):
            span = float(right) - float(left)
            if span <= 0.0:
                continue
            n_sub = max(1, int(np.ceil(span / float(config.episode.physics_dt_s) - 1e-9)))
            h = span / n_sub
            for index in range(n_sub):
                sub_start = float(left) + index * h
                site_states = self._site_states_at(sub_start)
                frame = self._demand_frame_at(sub_start)
                demand, source_observed = self._slot_demand(frame, sub_start)

                start_position = self._positions_m.copy()
                mid_position, _, _ = dyn.advance(
                    start_position, requested, h / 2.0, config.dynamics, config.region
                )
                end_position, _, _ = dyn.advance(
                    mid_position, requested, h / 2.0, config.dynamics, config.region
                )
                evaluation_position = (
                    mid_position if config.episode.quadrature == "midpoint" else start_position
                )
                # The quadrature rule decides WHICH geometry the solve used, so it also
                # decides the time that geometry holds at. Only this method knows the rule,
                # so the offset is computed here rather than guessed by the consumer.
                geometry_offset_s = (
                    0.5 * h if config.episode.quadrature == "midpoint" else 0.0
                )

                snapshot, result = self._evaluate_service(
                    evaluation_position, site_states, demand
                )
                delivered = result.delivered_mbps_per_demand
                # Truthful capture seam: hand over the solve that actually happened,
                # paired with the geometry and measurement time it was computed at.  The
                # scheduler is never asked to solve again on the viewer's behalf, and an
                # unarmed interval never reaches this call's body.
                if observer is not None:
                    if observer.armed:
                        # Read-only for the duration of the call: the env reads all of these
                        # back after it returns, and `end_position` becomes the live
                        # `_positions_m`. A mutating observer now fails loudly here instead
                        # of silently changing a reward or the trajectory.
                        with _readonly(
                            evaluation_position, end_position, requested, demand, source_observed
                        ):
                            observer.on_service_evaluated(
                                env=self,
                                window_start_s=sub_start,
                                geometry_time_s=sub_start + geometry_offset_s,
                                duration_s=h,
                                substep_index=substep_index,
                                decision_step=decision_index,
                                positions_m=evaluation_position,
                                end_positions_m=end_position,
                                requested_velocity_mps=requested,
                                site_states=site_states,
                                demand_mbps=demand,
                                source_observed=source_observed,
                                snapshot=snapshot,
                                result=result,
                            )
                    substep_index += 1
                link_utilization = {
                    int(link.link_id): float(
                        result.link_flow_mbps[int(link.link_id)]
                        / max(link.capacity_mbps, 1e-12)
                    )
                    for link in snapshot.links
                    if int(link.link_id) in result.link_flow_mbps
                }

                step_distance = np.linalg.norm(end_position - start_position, axis=1)
                realised_velocity = (end_position - start_position) / h
                effort = dyn.motion_effort(realised_velocity, config.dynamics)

                sensed = sensed_demand_mask(
                    self._demand_positions_m,
                    evaluation_position,
                    self._site_positions_m,
                    site_states,
                    float(config.observations.sensing_radius_m),
                    self._site_registration_radius_m,
                )

                self._accumulator.add(
                    SubintervalRecord(
                        start_s=sub_start,
                        duration_s=h,
                        offered_mbps=demand,
                        delivered_mbps=delivered,
                        domain_utilization=result.domain_utilization,
                        gateway_utilization=result.gateway_utilization,
                        link_utilization=link_utilization,
                        max_constraint_residual=result.max_constraint_residual,
                        motion_effort=effort,
                        distance_m=step_distance,
                        active_path_signature=tuple(
                            int(i)
                            for i in np.flatnonzero(result.path_flows_mbps > 1e-9).tolist()
                        ),
                        min_separation_m=dyn.min_pairwise_separation_m(evaluation_position),
                    )
                )

                interval_offered += demand * h
                interval_delivered += delivered * h
                interval_sensed |= sensed
                interval_source_observed &= source_observed
                unmet = float(np.maximum(demand - delivered, 0.0).sum())
                unmet_mbit += unmet * h
                delivered_mbit += float(delivered.sum()) * h
                offered_mbit += float(demand.sum()) * h
                motion_integral_s += effort * h

                self._positions_m = end_position
                self._velocities_mps = realised_velocity

        self._time_s = t1
        self._step_index += 1
        if self._alert_time_s is not None and t1 >= self._alert_time_s - 1e-9:
            self._alert_raised = True

        # Telemetry describes only the interval that just finished.
        duration = max(t1 - t0, 1e-12)
        site_states_end = self._site_states_at(t1 - 1e-9)
        self._store.submit(
            TelemetryRecord(
                interval_start_s=t0,
                interval_end_s=t1,
                release_time_s=t1 + float(config.observations.telemetry_delay_s),
                uav_positions_m=self._positions_m.copy(),
                uav_velocities_mps=self._velocities_mps.copy(),
                site_state_vectors=np.stack([state.as_vector() for state in site_states_end]),
                site_state_observed=np.ones(len(site_states_end), dtype=bool),
                demand_offered_mbps=interval_offered / duration,
                demand_delivered_mbps=interval_delivered / duration,
                demand_observed=interval_sensed & interval_source_observed,
            )
        )
        self._store.release_due(t1)

        service_term = -unmet_mbit / (
            float(config.reward.reference_scale_mbps) * float(config.reward.reference_dt_s)
        )
        motion_term = -float(config.reward.motion_weight) * motion_integral_s / float(
            config.reward.reference_dt_s
        )
        reward = float(service_term + motion_term)

        finished = self._step_index >= int(config.n_decision_steps)
        terminated_flag = bool(finished and config.episode.semantics == "finite_horizon")
        truncated_flag = bool(finished and config.episode.semantics == "continuing")

        observations = self._observations()
        rewards = {agent: reward for agent in self.agents}
        terminations = {agent: terminated_flag for agent in self.agents}
        truncations = {agent: truncated_flag for agent in self.agents}
        reward_info = {
            "unmet_mbit_interval": float(unmet_mbit),
            "delivered_mbit_interval": float(delivered_mbit),
            "offered_mbit_interval": float(offered_mbit),
            "motion_effort_integral_s": float(motion_integral_s),
            "service_term": float(service_term),
            "motion_term": float(motion_term),
            "reward_total": reward,
            "reference_scale_mbps": float(config.reward.reference_scale_mbps),
            "reference_dt_s": float(config.reward.reference_dt_s),
        }
        infos = {
            agent: {
                "scenario": config.preset_name,
                "agent_index": self._agent_index[agent],
                "reward_info": dict(reward_info),
            }
            for agent in self.agents
        }
        # Final diagnostic seam of the interval.  It runs before ``self.agents`` is
        # emptied and before any caller can reset, so a terminal frame describes the
        # episode that just ended rather than the next one's initial state.
        if observer is not None:
            observer.on_decision_complete(
                env=self,
                decision_step=decision_index,
                interval_start_s=t0,
                interval_end_s=t1,
                reward_info=reward_info,
                terminated=terminated_flag,
                truncated=truncated_flag,
                finished=finished,
                n_substeps=substep_index,
            )
        if finished:
            # The real terminal observation above is what is returned; the agent list is
            # emptied only afterwards, and no implicit reset happens here.
            self.agents = []
        return observations, rewards, terminations, truncations, infos

    def _is_held_at_standby(self, time_s: float) -> bool:
        config = self._config
        if config.deployment.mode != "reactive_launch":
            return False
        if self._alert_time_s is None:
            return True
        release = float(self._alert_time_s) + float(config.deployment.launch_delay_s)
        return float(time_s) < release - 1e-9

    # ----------------------------------------------------------------------------------
    # Observations and state
    # ----------------------------------------------------------------------------------

    def _ideal_offered(self) -> np.ndarray | None:
        if self._config.observations.mode != "ideal_full_current_demand":
            return None
        frame = self._demand_frame_at(self._time_s)
        demand, _ = self._slot_demand(frame, float(self._time_s))
        return demand

    def _observations(self) -> dict[str, np.ndarray]:
        progress = (
            float(self._step_index) / float(max(self._config.n_decision_steps, 1))
            if self._config.observations.include_episode_progress
            else 0.0
        )
        ideal = self._ideal_offered()
        held = self._is_held_at_standby(self._time_s)
        timestamp = self._utc_ms_at(self._time_s)
        return {
            agent: self._builder.build_observation(
                uav_index=self._agent_index[agent],
                own_position_m=self._positions_m[self._agent_index[agent]],
                own_velocity_mps=self._velocities_mps[self._agent_index[agent]],
                store=self._store,
                now_s=float(self._time_s),
                timestamp_utc_ms=timestamp,
                progress=progress,
                alert_raised=self._alert_raised,
                held_at_standby=held,
                ideal_offered_mbps=ideal,
            )
            for agent in self.agents
        }

    def state(self) -> np.ndarray:
        progress = (
            float(self._step_index) / float(max(self._config.n_decision_steps, 1))
            if self._config.observations.include_episode_progress
            else 0.0
        )
        return self._builder.build_state(
            store=self._store,
            now_s=float(self._time_s),
            timestamp_utc_ms=self._utc_ms_at(self._time_s),
            progress=progress,
            alert_raised=self._alert_raised,
            held_at_standby=self._is_held_at_standby(self._time_s),
            ideal_offered_mbps=self._ideal_offered(),
        )

    def _get_state(self) -> np.ndarray:
        return self.state()

    def get_current_state(self) -> dict[str, Any]:
        """Compact diagnostic state for plotting and for the adapter's ``state_info``.

        Contains only permitted centralized information, because this mapping reaches the
        training path through the shared adapter.  Future demand, the event schedule and
        internal solver state are not here; see
        :meth:`get_privileged_diagnostics` for those.
        """

        ttl = float(self._config.observations.telemetry_ttl_s)
        demand_age = float(self._time_s) - self._store.demand_time_s
        demand_valid = (
            np.isfinite(self._store.demand_time_s)
            & (demand_age >= -1e-9)
            & (demand_age <= ttl + 1e-9)
        )
        site_age = float(self._time_s) - self._store.site_time_s
        site_valid = (
            np.isfinite(self._store.site_time_s)
            & (site_age >= -1e-9)
            & (site_age <= ttl + 1e-9)
        )
        return {
            "uav_positions": self._positions_m.copy(),
            "site_positions": self._site_positions_m.copy(),
            "demand_point_positions": self._layout.positions_m.copy(),
            "telemetry_demand_offered_mbps": self._store.demand_offered_mbps.copy(),
            "telemetry_demand_delivered_mbps": self._store.demand_delivered_mbps.copy(),
            # Observed means "reported and not yet stale": the TTL applies here exactly as
            # it does in the observation masks, so a controller sees the same staleness a
            # policy does.
            "telemetry_demand_observed": demand_valid,
            "telemetry_demand_age_s": np.where(demand_valid, demand_age, np.inf),
            "telemetry_site_capability": self._store.site_vectors.copy(),
            "telemetry_site_observed": site_valid,
            "site_registration_radius_m": float(self._site_registration_radius_m),
            "current_step": int(self._step_index),
            "max_steps": int(self._config.n_decision_steps),
            "area_size": float(self.area_size),
            "alert_raised": bool(self._alert_raised),
            "physical_time_s": float(self._time_s),
        }

    # ----------------------------------------------------------------------------------
    # Privileged diagnostics (evaluator only)
    # ----------------------------------------------------------------------------------

    def get_privileged_diagnostics(self) -> dict[str, Any]:
        """Evaluator-only view.  Never reachable from observations, state or ``info``."""

        return {
            "episode_id": None if self._episode is None else self._episode.episode_id,
            "split": None if self._episode is None else self._episode.split,
            "dataset_hash": None if self._episode is None else self._episode.dataset_hash,
            "exogenous_events": self._schedule.summary(),
            "alert_time_s": self._alert_time_s,
            "episode_summary": self._accumulator.summary(),
            "scheduler_status": self._last_result_status,
            "source_metadata": {
                "kind": self._source_metadata.kind,
                "is_real_activity_data": bool(self._source_metadata.is_real_activity_data),
                "demand_scale_mbps": self._source_metadata.demand_scale_mbps,
                "activity_reference_scale": self._source_metadata.activity_reference_scale,
            },
            "calibration_summary": self._config.calibration_summary(),
        }

    def episode_summary(self) -> dict[str, Any]:
        return self._accumulator.summary()

    # ----------------------------------------------------------------------------------
    # Snapshots
    # ----------------------------------------------------------------------------------

    def get_probe_snapshot(self) -> dict[str, Any]:
        """Full runtime snapshot referencing - never copying - the source dataset."""

        return {
            "schema": "uav_service_restoration_v0.snapshot.1",
            "positions_m": self._positions_m.copy(),
            "velocities_mps": self._velocities_mps.copy(),
            "time_s": float(self._time_s),
            "step_index": int(self._step_index),
            "agents": list(self.agents),
            "alert_raised": bool(self._alert_raised),
            "alert_time_s": self._alert_time_s,
            "episode": self._episode,
            "schedule": self._schedule,
            "telemetry": self._store.snapshot(),
            "accumulator": copy.deepcopy(self._accumulator),
            "rng_states": {
                name: generator.bit_generator.state
                for name, generator in self._rngs.items()
            },
            "base_seed": int(self._base_seed),
            "episode_index": int(self._episode_index),
            "dataset_hash": self._source_metadata.dataset_hash,
        }

    def set_probe_snapshot(self, snapshot: dict[str, Any]) -> None:
        if snapshot.get("schema") != "uav_service_restoration_v0.snapshot.1":
            raise ValueError("snapshot schema mismatch")
        if snapshot.get("dataset_hash") != self._source_metadata.dataset_hash:
            raise ValueError(
                "snapshot references a different dataset content hash; a same-named file "
                "from another version is not silently accepted"
            )
        self._positions_m = np.array(snapshot["positions_m"], dtype=np.float64)
        self._velocities_mps = np.array(snapshot["velocities_mps"], dtype=np.float64)
        self._time_s = float(snapshot["time_s"])
        self._step_index = int(snapshot["step_index"])
        self.agents = list(snapshot["agents"])
        self._alert_raised = bool(snapshot["alert_raised"])
        self._alert_time_s = snapshot["alert_time_s"]
        self._episode = snapshot["episode"]
        self._schedule = snapshot["schedule"]
        self._store.restore(snapshot["telemetry"])
        self._accumulator = copy.deepcopy(snapshot["accumulator"])
        self._base_seed = int(snapshot["base_seed"])
        self._episode_index = int(snapshot["episode_index"])
        self._rngs = {}
        for name, state in snapshot["rng_states"].items():
            generator = np.random.default_rng()
            generator.bit_generator.state = state
            self._rngs[name] = generator

    # ----------------------------------------------------------------------------------
    # Misc
    # ----------------------------------------------------------------------------------

    @property
    def config(self) -> EnvConfig:
        return self._config

    @property
    def demand_source(self) -> Any:
        return self._source

    @property
    def demand_layout(self) -> DemandPointLayout:
        return self._layout

    @property
    def event_schedule(self) -> EventSchedule:
        return self._schedule

    @property
    def episode_descriptor(self) -> EpisodeDescriptor | None:
        """Episode identity.  Evaluator-side only: never an observation feature."""

        return self._episode

    @property
    def accumulator(self) -> EpisodeAccumulator:
        """Raw metric accumulator of the episode in progress or just finished."""

        return self._accumulator

    @property
    def uav_positions_m(self) -> np.ndarray:
        return self._positions_m.copy()

    @property
    def physical_time_s(self) -> float:
        return float(self._time_s)

    def render(self) -> None:
        """No renderer in v0; reads must never advance time or RNG state."""

        return None

    def close(self) -> None:
        return None
