"""Scene capture for ``uav_service_restoration_v0``.

The environment evaluates service at substep quadrature points and exposes the
``NetworkSnapshot`` and ``SchedulerResult`` that each solve produced. This module turns
one of those solves into a :class:`~tools.research_support.records.SceneFrame`, and does
so only for an interval the gate already admitted.

What it deliberately does not do:

* It never calls ``_evaluate_service`` again, never rebuilds the graph, never recomputes
  SINR and never asks the scheduler to solve on the viewer's behalf. Every number in a
  frame is a value the simulation had already produced for its own purposes.
* It never caches a solve on an unarmed interval. Exactly one substep per admitted
  decision interval is converted, and the rest of that interval's solves are untouched.
* It never fills a policy-visible field from privileged truth. The ``observation_view``
  section is read from the environment's own policy-facing telemetry store, and an
  unknown entry stays unknown.

Geometry and time are kept paired: a midpoint solve is reported with the midpoint
position and the midpoint measurement window, never presented as an exact solve at the
interval-end position the UAV will reach next.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from ..records import (
    DecisionEvent,
    EntityId,
    EntityKind,
    FrameKind,
    GroundEntityState,
    LifetimeRegistry,
    LinkActivity,
    LinkRecord,
    Measured,
    ObservationView,
    PathRecord,
    PolicyKind,
    ResourceDomainRecord,
    SceneCapability,
    SceneClock,
    SceneFrame,
    SceneGeometry,
    SceneIdentity,
    SceneProvenance,
    SiteStateRecord,
    SourceKind,
    StreamHealth,
    StreamState,
    UavState,
    Validity,
    canonical_link_key,
)
from .profiles import CaptureGate, GateVerdict
from .transport import FrameSink, OverloadBreaker

#: Numerical floor below which a solved flow is treated as "no traffic on this link".
#: The scheduler's own feasibility tolerance is 1e-7 by default, so 1e-9 keeps a link
#: that genuinely carries a trickle distinguishable from one that carries nothing.
_FLOW_EPSILON = 1e-9

_NODE_KIND_TO_ENTITY = {
    "core": EntityKind.CORE,
    "site": EntityKind.SITE,
    "uav": EntityKind.UAV,
    "demand": EntityKind.AGGREGATE_DEMAND_POINT,
}

SERVICE_RESTORATION_CAPABILITY = SceneCapability(
    has_uav_positions=True,
    has_uav_velocity=True,
    has_requested_action=True,
    has_skill_labels=False,
    has_energy=False,
    has_individual_ues=False,
    has_aggregate_demand=True,
    has_demand_rates=True,
    has_delivered_rates=True,
    has_sites=True,
    has_links=True,
    has_link_flows=True,
    has_link_capacity=True,
    has_resource_domains=True,
    has_candidate_paths=True,
    has_sinr=True,
    has_association=False,
    has_observation_view=True,
    has_roster_changes=False,
    has_altitude=True,
    has_interval_metrics=True,
    notes=(
        "ground markers are aggregated demand proxies for source grid cells; they are "
        "not people, subscribers or tracked devices",
        "there is no learned skill in this environment; a rule controller has no skill "
        "sequence and none is invented",
        "link geometry and flows belong to the substep quadrature point named by "
        "geometry_time_s, not to the interval-end UAV position",
    ),
)


def _entity_for_node(node: Any, lifetime: LifetimeRegistry) -> EntityId:
    kind = _NODE_KIND_TO_ENTITY[str(getattr(node.kind, "value", node.kind))]
    return lifetime.entity(kind, int(node.index))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class ServiceRestorationObserver:
    """Capture observer attached to :class:`UAVServiceRestorationEnv`.

    Lifecycle per decision interval::

        begin_decision()          -> one gate decision, no copying
        [armed] on_service_evaluated()  -> convert exactly one already-produced solve
        on_decision_complete()    -> attach interval totals and emit one frame

    Nothing is retained between intervals except the small pending-scene reference, which
    is cleared as soon as the frame is emitted.
    """

    def __init__(
        self,
        *,
        gate: CaptureGate,
        sink: FrameSink,
        run_id: str,
        trace_id: str,
        route: str = "service-restoration",
        lane_id: int = 0,
        policy_kind: PolicyKind = PolicyKind.RULE_CONTROLLER,
        source_kind: SourceKind = SourceKind.RULE_CONTROLLER_ROLLOUT,
        policy_label: str = "unspecified",
        checkpoint_identity: str | None = None,
        trace_writer: Any | None = None,
        breaker: OverloadBreaker | None = None,
        capture_substeps: bool = False,
    ) -> None:
        self._gate = gate
        self._sink = sink
        self._run_id = run_id
        self._trace_id = trace_id
        self._route = route
        self._lane_id = int(lane_id)
        self._policy_kind = policy_kind
        self._source_kind = source_kind
        self._policy_label = policy_label
        self._checkpoint_identity = checkpoint_identity
        self._trace_writer = trace_writer
        self._breaker = breaker or OverloadBreaker()
        self._capture_substeps = bool(capture_substeps)

        self.armed = False
        self._sequence = 0
        self._completed_steps = 0
        self._pending: dict[str, Any] | None = None
        self._lifetime = LifetimeRegistry()
        self._episode_key = "episode_unset"
        self._world_key = "world_unset"
        self._stream_state = StreamState.WAITING
        self._last_error: str | None = None
        self._emitted = 0
        self._skipped_oversized = 0
        self._capture_errors = 0
        self._gap_since_sequence: int | None = None

    # ----------------------------------------------------------------------------------
    # Properties
    # ----------------------------------------------------------------------------------

    @property
    def last_error(self) -> str | None:
        """The most recent capture failure, or ``None``. Also carried in stream health."""

        return self._last_error

    @property
    def capture_errors(self) -> int:
        return self._capture_errors

    @property
    def emitted(self) -> int:
        return self._emitted

    @property
    def sequence(self) -> int:
        return self._sequence

    def stream_health(self) -> StreamHealth:
        counters = self._gate.counters
        stats = self._sink.stats
        return StreamHealth(
            state=self._stream_state,
            dropped_display_frames=stats.dropped_full + stats.dropped_error,
            missing_sequences=counters.attempts - counters.admitted,
            refused_by_gate=(
                counters.refused_step_gate
                + counters.refused_wall_gate
                + counters.refused_no_viewer
                + counters.refused_lane
                + counters.refused_session_expired
                + counters.refused_circuit_open
            ),
            refused_by_byte_budget=counters.refused_byte_budget + self._skipped_oversized,
            trace_status="recording" if self._trace_writer is not None else "not_recorded",
            producer_status="running",
            last_error=self._last_error or stats.last_error,
        )

    def finish(self, *, state: StreamState = StreamState.ENDED) -> None:
        """Mark the stream terminal and publish a final health record."""

        self._stream_state = state
        self._publish_health()

    # ----------------------------------------------------------------------------------
    # Environment callbacks
    # ----------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------
    # Environment seams
    #
    # Each public seam delegates to its ``_impl`` through ``_absorb``. Under a live preview
    # a defect here is a display defect: it disarms the capture, records the reason and
    # opens the circuit, but it must never end a scientific run that was not started for
    # its benefit. Under an explicitly requested recording the recording IS the
    # deliverable, so the error surfaces instead of producing a quietly incomplete trace.
    # ----------------------------------------------------------------------------------

    #: How long the circuit stays open after a capture defect, in seconds.
    ERROR_COOLDOWN_S = 30.0

    @property
    def absorbs_errors(self) -> bool:
        return bool(getattr(self._gate, "is_optional_display", False))

    def _absorb(self, where: str, action: Callable[[], None]) -> None:
        try:
            action()
        except Exception as error:
            if not self.absorbs_errors:
                raise
            self.armed = False
            self._pending = None
            self._capture_errors += 1
            self._last_error = f"{where}: {type(error).__name__}: {error}"
            self._stream_state = StreamState.ERROR
            self._gate.open_circuit(self.ERROR_COOLDOWN_S)

    def on_episode_reset(self, *, env: Any, time_s: float) -> None:
        self._absorb(
            "on_episode_reset",
            lambda: self._on_episode_reset_impl(env=env, time_s=time_s),
        )

    def begin_decision(self, env: Any, *, decision_step: int, time_s: float) -> None:
        self._absorb(
            "begin_decision",
            lambda: self._begin_decision_impl(env, decision_step=decision_step, time_s=time_s),
        )

    def on_service_evaluated(self, **kwargs: Any) -> None:
        self._absorb(
            "on_service_evaluated", lambda: self._on_service_evaluated_impl(**kwargs)
        )

    def on_decision_complete(self, **kwargs: Any) -> None:
        self._absorb(
            "on_decision_complete", lambda: self._on_decision_complete_impl(**kwargs)
        )

    def _on_episode_reset_impl(self, *, env: Any, time_s: float) -> None:
        """Attempt one initial frame with legitimate initial masks.

        The first explicitly armed sample may initialise the view; it still respects the
        byte budget, and a later reset competes for the same rate allowance as any other
        attempt rather than bypassing it.
        """

        episode = getattr(env, "episode_descriptor", None)
        self._episode_key = getattr(episode, "episode_id", None) or "episode_unknown"
        self._world_key = self._world_identity(env, episode)
        self._lifetime = LifetimeRegistry()
        verdict = self._gate.admit(
            self._lane_id, self._completed_steps, force_first=self._sequence == 0
        )
        if not verdict.admitted:
            self._note_gap()
            return
        # An initial frame has no solve behind it: report geometry and policy view only,
        # with every service quantity explicitly not yet measured.
        frame = self._build_frame(
            env=env,
            frame_kind=FrameKind.INITIAL,
            geometry_time_s=float(time_s),
            simulation_time_s=float(time_s),
            decision_step=int(getattr(env, "_step_index", 0)),
            substep_index=None,
            measurement_start_s=None,
            measurement_end_s=None,
            positions_m=np.asarray(env.uav_positions_m, dtype=np.float64),
            requested_velocity_mps=None,
            snapshot=None,
            result=None,
            demand_mbps=None,
            source_observed=None,
            site_states=None,
            interval_metrics={},
        )
        self._emit(frame)

    def _begin_decision_impl(self, env: Any, *, decision_step: int, time_s: float) -> None:
        """One gate decision per decision interval. No array is touched here."""

        del env, time_s
        self._pending = None
        verdict = self._gate.admit(self._lane_id, self._completed_steps)
        self.armed = verdict.admitted
        if not self.armed:
            if verdict is GateVerdict.CIRCUIT_OPEN:
                self._stream_state = StreamState.STALE
            self._note_gap()
        self._current_step = int(decision_step)

    def _on_service_evaluated_impl(
        self,
        *,
        env: Any,
        window_start_s: float,
        geometry_time_s: float,
        duration_s: float,
        substep_index: int,
        decision_step: int,
        positions_m: np.ndarray,
        end_positions_m: np.ndarray,
        requested_velocity_mps: np.ndarray,
        site_states: Sequence[Any],
        demand_mbps: np.ndarray,
        source_observed: np.ndarray,
        snapshot: Any,
        result: Any,
    ) -> None:
        """Convert exactly one already-produced solve.

        By default ``armed`` is cleared after the first conversion of an armed interval, so
        the remaining substeps of that interval do no work at all and the frame carries the
        FIRST substep.

        ``capture_substeps`` keeps the flag set, so each substep overwrites the pending
        conversion and the frame ends up carrying the LAST substep instead. It does not
        produce one frame per substep and never did: a frame carries the interval totals,
        which do not exist until the interval has finished. It costs one conversion per
        substep, so it is available only to an explicit recording session.
        """

        del end_positions_m
        if self._pending is not None and not self._capture_substeps:
            return
        started = time.perf_counter()
        self._pending = {
            # Two distinct times, never conflated: the measurement window opens at
            # `window_start_s`, while the handed-over positions hold at the quadrature point
            # `geometry_time_s`. Under the default midpoint rule they differ by half a
            # substep, and stamping the geometry with the window start mislabelled every
            # UAV position by up to max_speed * h / 2.
            "window_start_s": float(window_start_s),
            "geometry_time_s": float(geometry_time_s),
            "duration_s": float(duration_s),
            "substep_index": int(substep_index),
            "decision_step": int(decision_step),
            # Owned copies: the caller reuses these arrays on the next substep.
            "positions_m": np.array(positions_m, dtype=np.float64, copy=True),
            "requested_velocity_mps": np.array(
                requested_velocity_mps, dtype=np.float64, copy=True
            ),
            "demand_mbps": np.array(demand_mbps, dtype=np.float64, copy=True),
            "source_observed": np.array(source_observed, dtype=bool, copy=True),
            "site_states": tuple(state.copy() for state in site_states),
            "snapshot": snapshot,
            "result": result,
            "env": env,
            "build_s": time.perf_counter() - started,
        }
        if not self._capture_substeps:
            self.armed = False

    def _on_decision_complete_impl(
        self,
        *,
        env: Any,
        decision_step: int,
        interval_start_s: float,
        interval_end_s: float,
        reward_info: Mapping[str, Any],
        terminated: bool,
        truncated: bool,
        finished: bool,
        n_substeps: int,
    ) -> None:
        """Attach the completed interval's totals and emit the frame."""

        self._completed_steps += 1
        pending = self._pending
        self._pending = None
        self.armed = False
        if pending is None:
            return
        del n_substeps
        interval_metrics = {
            name: Measured.from_float(
                value,
                unit=_REWARD_INFO_UNITS.get(name),
                source="reward_info",
                missing_reason="absent_in_reward_info",
            )
            for name, value in reward_info.items()
        }
        interval_metrics["interval_start_s"] = Measured.ok(float(interval_start_s), unit="s")
        interval_metrics["interval_end_s"] = Measured.ok(float(interval_end_s), unit="s")
        interval_metrics["terminated"] = Measured.ok(bool(terminated))
        interval_metrics["truncated"] = Measured.ok(bool(truncated))

        frame = self._build_frame(
            env=env,
            frame_kind=FrameKind.FINAL if finished else FrameKind.TRANSITION,
            geometry_time_s=pending["geometry_time_s"],
            simulation_time_s=float(interval_end_s),
            decision_step=int(decision_step),
            substep_index=pending["substep_index"],
            measurement_start_s=pending["window_start_s"],
            measurement_end_s=pending["window_start_s"] + pending["duration_s"],
            positions_m=pending["positions_m"],
            requested_velocity_mps=pending["requested_velocity_mps"],
            snapshot=pending["snapshot"],
            result=pending["result"],
            demand_mbps=pending["demand_mbps"],
            source_observed=pending["source_observed"],
            site_states=pending["site_states"],
            interval_metrics=interval_metrics,
        )
        self._emit(frame, build_s=pending["build_s"])

    # ----------------------------------------------------------------------------------
    # Frame construction
    # ----------------------------------------------------------------------------------

    def _build_frame(
        self,
        *,
        env: Any,
        frame_kind: FrameKind,
        geometry_time_s: float,
        simulation_time_s: float,
        decision_step: int,
        substep_index: int | None,
        measurement_start_s: float | None,
        measurement_end_s: float | None,
        positions_m: np.ndarray,
        requested_velocity_mps: np.ndarray | None,
        snapshot: Any,
        result: Any,
        demand_mbps: np.ndarray | None,
        source_observed: np.ndarray | None,
        site_states: Sequence[Any] | None,
        interval_metrics: Mapping[str, Measured],
    ) -> SceneFrame:
        config = env.config
        n_uavs = int(positions_m.shape[0])
        self._lifetime.observe(EntityKind.UAV, range(n_uavs))

        uavs = tuple(
            UavState(
                entity=self._lifetime.entity(EntityKind.UAV, index, label=f"uav_{index}"),
                position_m=tuple(float(v) for v in positions_m[index]),
                active=True,
                executed_velocity_mps=None,
                requested_velocity_mps=(
                    None
                    if requested_velocity_mps is None
                    else tuple(float(v) for v in requested_velocity_mps[index])
                ),
                team_skill_id=None,
                individual_skill_id=None,
                skill_age_s=Measured.not_applicable("environment has no skill layer"),
                energy=Measured.not_applicable("environment has no endurance model"),
            )
            for index in range(n_uavs)
        )

        ground = self._ground_entities(env, demand_mbps, source_observed, result)
        sites = self._sites(env, site_states)
        links, domains, paths = self._network(snapshot, result, geometry_time_s)
        events = self._events(env, simulation_time_s)
        observation_view = self._observation_view(env)

        bounds = (
            float(config.region.min_xy_m[0]),
            float(config.region.min_xy_m[1]),
            float(config.region.max_xy_m[0]),
            float(config.region.max_xy_m[1]),
        )
        diagnostics = env.get_privileged_diagnostics()
        source_meta = diagnostics.get("source_metadata") or {}

        identity = SceneIdentity(
            run_id=self._run_id,
            trace_id=self._trace_id,
            episode_id=self._episode_key,
            world_id=self._world_key,
            lane_id=self._lane_id,
            sequence=self._sequence,
        )
        clock = SceneClock(
            simulation_time_s=float(simulation_time_s),
            geometry_time_s=float(geometry_time_s),
            decision_step=int(decision_step),
            capture_wall_time_utc=_utc_now(),
            producer_monotonic_s=time.monotonic(),
            measurement_start_s=measurement_start_s,
            measurement_end_s=measurement_end_s,
            training_step=None,
            substep_index=substep_index,
        )
        provenance = SceneProvenance(
            route=self._route,
            environment_id=str(config.environment_id),
            source_kind=self._source_kind,
            policy_kind=self._policy_kind,
            information_condition=str(config.observations.mode),
            frame_kind=frame_kind,
            capture_resolution=(
                # One frame per admitted decision interval either way: the interval totals
                # this frame carries only exist once the interval has finished, so a
                # per-substep frame could not be assembled. The flag chooses WHICH substep's
                # geometry and solve the frame holds, and the label says so rather than
                # claiming a resolution that is not produced.
                "first_substep_of_an_admitted_decision_interval"
                if not self._capture_substeps
                else "last_substep_of_an_admitted_decision_interval"
            ),
            dataset_hash=diagnostics.get("dataset_hash"),
            checkpoint_identity=self._checkpoint_identity,
            is_real_activity_data=bool(source_meta.get("is_real_activity_data", False)),
            measured_fields=(
                "link flows, link capacities, resource-domain utilization and delivered "
                "rates come from the scheduler solve that the simulation performed at "
                "geometry_time_s",
            ),
            derived_fields=(
                "link utilization is flow divided by isolated link capacity, computed "
                "here from two recorded values",
            ),
            notes=(f"policy_label={self._policy_label}",),
        )
        return SceneFrame(
            identity=identity,
            clock=clock,
            provenance=provenance,
            geometry=SceneGeometry(bounds_m=bounds),
            capability=SERVICE_RESTORATION_CAPABILITY,
            uavs=uavs,
            ground_entities=ground,
            sites=sites,
            links=links,
            resource_domains=domains,
            paths=paths,
            events=events,
            interval_metrics=dict(interval_metrics),
            observation_view=observation_view,
            stream_health=self.stream_health(),
        )

    def _ground_entities(
        self,
        env: Any,
        demand_mbps: np.ndarray | None,
        source_observed: np.ndarray | None,
        result: Any,
    ) -> tuple[GroundEntityState, ...]:
        positions = np.asarray(env.demand_layout.positions_m, dtype=np.float64)
        n_points = int(positions.shape[0])
        self._lifetime.observe(EntityKind.AGGREGATE_DEMAND_POINT, range(n_points))
        delivered = (
            None
            if result is None
            else np.asarray(result.delivered_mbps_per_demand, dtype=np.float64)
        )
        out: list[GroundEntityState] = []
        for index in range(n_points):
            observed = True if source_observed is None else bool(source_observed[index])
            if demand_mbps is None:
                offered = Measured.not_recorded("no solve captured for this frame", unit="Mbps")
            elif not observed:
                # The source has no record for this cell: unknown demand, never a
                # measured zero and never an empty region.
                offered = Measured.unknown("source_interval_not_observed", unit="Mbps")
            else:
                offered = Measured.from_float(float(demand_mbps[index]), unit="Mbps")
            if delivered is None:
                served = Measured.not_recorded("no solve captured for this frame", unit="Mbps")
            else:
                served = Measured.from_float(float(delivered[index]), unit="Mbps")
            status = self._service_status(offered, served)
            out.append(
                GroundEntityState(
                    entity=self._lifetime.entity(
                        EntityKind.AGGREGATE_DEMAND_POINT, index, label=f"cell_{index}"
                    ),
                    position_m=(float(positions[index][0]), float(positions[index][1]), 0.0),
                    active=True,
                    offered_mbps=offered,
                    delivered_mbps=served,
                    observed=observed,
                    age_s=Measured.not_applicable("simulator-truth view is current"),
                    service_status=status,
                    associated_to=None,
                    sinr_db=Measured.not_recorded("per-cell SINR is not retained by the solve"),
                    # One marker stands for one source grid cell's aggregated activity.
                    represents_count=1,
                )
            )
        return tuple(out)

    @staticmethod
    def _service_status(offered: Measured, delivered: Measured) -> str:
        if offered.validity is not Validity.OK:
            return "unknown_demand"
        if delivered.validity is not Validity.OK:
            return "unknown_service"
        if float(offered.value) <= 0.0:
            return "zero_demand"
        ratio = float(delivered.value) / float(offered.value)
        if ratio >= 0.999:
            return "served"
        if ratio <= 1e-9:
            return "unserved"
        return "partially_served"

    def _sites(self, env: Any, site_states: Sequence[Any] | None) -> tuple[SiteStateRecord, ...]:
        positions = np.asarray(env._site_positions_m, dtype=np.float64)
        n_sites = int(positions.shape[0])
        self._lifetime.observe(EntityKind.SITE, range(n_sites))
        config_sites = list(env.config.network.sites)
        out: list[SiteStateRecord] = []
        for index in range(n_sites):
            state = None if site_states is None else site_states[index]
            label = (
                str(getattr(config_sites[index], "site_id", f"site_{index}"))
                if index < len(config_sites)
                else f"site_{index}"
            )
            if state is None:
                out.append(
                    SiteStateRecord(
                        entity=self._lifetime.entity(EntityKind.SITE, index, label=label),
                        position_m=tuple(float(v) for v in positions[index]),
                        radio_up=None,
                        core_link_up=None,
                        access_capacity_scale=Measured.not_recorded("no solve captured"),
                        backhaul_capacity_scale=Measured.not_recorded("no solve captured"),
                        observed=True,
                    )
                )
                continue
            access = float(state.access_capacity_scale)
            backhaul = float(state.backhaul_capacity_scale)
            out.append(
                SiteStateRecord(
                    entity=self._lifetime.entity(EntityKind.SITE, index, label=label),
                    position_m=tuple(float(v) for v in positions[index]),
                    radio_up=bool(state.radio_up),
                    core_link_up=bool(state.core_link_up),
                    access_capacity_scale=Measured.ok(access, unit="ratio"),
                    backhaul_capacity_scale=Measured.ok(backhaul, unit="ratio"),
                    observed=True,
                    age_s=Measured.not_applicable("simulator-truth view is current"),
                    degraded=bool(
                        not state.radio_up
                        or not state.core_link_up
                        or access < 1.0
                        or backhaul < 1.0
                    ),
                )
            )
        return tuple(out)

    def _network(
        self, snapshot: Any, result: Any, geometry_time_s: float
    ) -> tuple[
        tuple[LinkRecord, ...], tuple[ResourceDomainRecord, ...], tuple[PathRecord, ...]
    ]:
        if snapshot is None or result is None:
            return (), (), ()
        del geometry_time_s
        domain_of_link: dict[int, str] = {}
        for domain in snapshot.resource_domains:
            for link_id in domain.link_ids:
                domain_of_link[int(link_id)] = str(domain.domain_id)

        link_keys: dict[int, str] = {}
        links: list[LinkRecord] = []
        for link in snapshot.links:
            local_id = int(link.link_id)
            source = _entity_for_node(link.source, self._lifetime)
            target = _entity_for_node(link.target, self._lifetime)
            link_class = str(getattr(link.link_class, "value", link.link_class))
            domain_id = domain_of_link.get(local_id)
            key = canonical_link_key(source, target, link_class, resource_domain=domain_id)
            link_keys[local_id] = key
            capacity = float(link.capacity_mbps)
            flow_value = result.link_flow_mbps.get(local_id)
            if flow_value is None:
                flow = Measured.not_recorded("link carried no variable in this solve", unit="Mbps")
                utilization = Measured.not_recorded("no flow recorded for this link")
                activity = LinkActivity.AVAILABLE
            else:
                flow = Measured.from_float(float(flow_value), unit="Mbps")
                if capacity > 0.0 and flow.validity is Validity.OK:
                    utilization = Measured.ok(float(flow.value) / capacity, unit="ratio")
                else:
                    utilization = Measured.invalid(
                        "zero_or_unknown_isolated_capacity", unit="ratio"
                    )
                activity = (
                    LinkActivity.ACTIVE
                    if flow.validity is Validity.OK and float(flow.value) > _FLOW_EPSILON
                    else LinkActivity.AVAILABLE
                )
            links.append(
                LinkRecord(
                    link_key=key,
                    source=source,
                    target=target,
                    link_class=link_class,
                    activity=activity,
                    capacity_mbps=Measured.from_float(capacity, unit="Mbps"),
                    flow_mbps=flow,
                    utilization=utilization,
                    resource_domain=domain_id,
                    # A wired core link has no radio SNR; the model stores an infinity
                    # there, which is "not applicable" rather than a failed measurement.
                    snr_db=(
                        Measured.not_applicable("wired link has no radio SNR", unit="dB")
                        if link_class == "wired_core"
                        else Measured.from_float(float(link.snr_db), unit="dB")
                    ),
                    distance_m=Measured.from_float(float(link.distance_m), unit="m"),
                    producer_local_id=local_id,
                )
            )

        domains = tuple(
            ResourceDomainRecord(
                domain_id=str(domain.domain_id),
                description=str(domain.description),
                link_keys=tuple(
                    link_keys[int(i)] for i in domain.link_ids if int(i) in link_keys
                ),
                utilization=Measured.from_float(
                    result.domain_utilization.get(str(domain.domain_id)), unit="ratio"
                ),
            )
            for domain in snapshot.resource_domains
        )

        path_flows = np.asarray(result.path_flows_mbps, dtype=np.float64)
        paths: list[PathRecord] = []
        for index, path in enumerate(snapshot.paths):
            flow = (
                Measured.from_float(float(path_flows[index]), unit="Mbps")
                if index < path_flows.shape[0]
                else Measured.not_recorded("path index beyond solved flow vector", unit="Mbps")
            )
            selected = flow.validity is Validity.OK and float(flow.value) > _FLOW_EPSILON
            demand_entity = self._lifetime.entity(
                EntityKind.AGGREGATE_DEMAND_POINT, int(path.demand_index)
            )
            node_keys = tuple(
                self._lifetime.entity(_NODE_KIND_TO_ENTITY[str(kind)], int(idx)).key
                for kind, idx in path.node_keys
            )
            paths.append(
                PathRecord(
                    demand_entity=demand_entity.key,
                    node_keys=node_keys,
                    link_keys=tuple(
                        link_keys[int(i)] for i in path.link_ids if int(i) in link_keys
                    ),
                    backhaul_hops=int(path.backhaul_hops),
                    flow_mbps=flow,
                    selected=selected,
                )
            )
        return tuple(links), domains, tuple(paths)

    def _events(self, env: Any, simulation_time_s: float) -> tuple[DecisionEvent, ...]:
        """Exogenous events that have already occurred.

        Only events whose start time has passed are reported. A future unannounced fault
        schedule is privileged simulator knowledge and must not appear in a live timeline;
        a completed trace may expose the retrospective schedule, marked as such, and that
        is a decision for the replay layer rather than for live capture.
        """

        diagnostics = env.get_privileged_diagnostics()
        summary = diagnostics.get("exogenous_events") or ()
        out: list[DecisionEvent] = []
        for item in summary:
            if not isinstance(item, Mapping):
                continue
            start = item.get("start_s")
            if start is None or float(start) > float(simulation_time_s) + 1e-9:
                continue
            site_index = item.get("site_index")
            out.append(
                DecisionEvent(
                    time_s=float(start),
                    event_type=str(item.get("event_type", "unknown")),
                    description=(
                        f"{item.get('event_type', 'event')} on site index {site_index}"
                    ),
                    entity=(
                        None
                        if site_index is None
                        else self._lifetime.entity(EntityKind.SITE, int(site_index)).key
                    ),
                    availability="recorded",
                )
            )
            end = item.get("end_s")
            if end is not None and float(end) <= float(simulation_time_s) + 1e-9:
                out.append(
                    DecisionEvent(
                        time_s=float(end),
                        event_type="repair",
                        description=(
                            "configured capability restoration; exogenous, not caused by "
                            "the UAVs"
                        ),
                        entity=(
                            None
                            if site_index is None
                            else self._lifetime.entity(EntityKind.SITE, int(site_index)).key
                        ),
                        availability="recorded",
                    )
                )
        alert = diagnostics.get("alert_time_s")
        if alert is not None and float(alert) <= float(simulation_time_s) + 1e-9:
            out.append(
                DecisionEvent(
                    time_s=float(alert),
                    event_type="alarm",
                    description="operator alert raised",
                    availability="recorded",
                )
            )
        return tuple(sorted(out, key=lambda e: e.time_s))

    def _observation_view(self, env: Any) -> ObservationView:
        """Read the environment's own policy-facing telemetry, never privileged truth."""

        state = env.get_current_state()
        demand_observed = np.asarray(state["telemetry_demand_observed"], dtype=bool)
        site_observed = np.asarray(state["telemetry_site_observed"], dtype=bool)
        ages = np.asarray(state["telemetry_demand_age_s"], dtype=np.float64)
        offered = np.asarray(state["telemetry_demand_offered_mbps"], dtype=np.float64)
        delivered = np.asarray(state["telemetry_demand_delivered_mbps"], dtype=np.float64)
        return ObservationView(
            values={
                # A value is reported only where the policy-facing mask says it is both
                # reported and not yet stale; elsewhere it stays null.
                "demand_offered_mbps": [
                    float(v) if seen else None for v, seen in zip(offered, demand_observed)
                ],
                "demand_delivered_mbps": [
                    float(v) if seen else None for v, seen in zip(delivered, demand_observed)
                ],
                "alert_raised": bool(state["alert_raised"]),
                "current_step": int(state["current_step"]),
            },
            masks={
                "demand_observed": [bool(v) for v in demand_observed],
                "site_observed": [bool(v) for v in site_observed],
            },
            ages_s={
                "demand_age_s": [
                    float(a) if np.isfinite(a) else None for a in ages
                ],
            },
            field_provenance={
                "demand_offered_mbps": "policy_facing_telemetry_store",
                "demand_delivered_mbps": "policy_facing_telemetry_store",
                "demand_observed": "policy_facing_ttl_and_sensing_mask",
                "site_observed": "policy_facing_ttl_mask",
            },
            information_condition=str(env.config.observations.mode),
        )

    # ----------------------------------------------------------------------------------
    # Emission
    # ----------------------------------------------------------------------------------

    def _world_identity(self, env: Any, episode: Any) -> str:
        """Exogenous-world identity: dataset, window and event realization together.

        Two runs sharing an integer seed do not share a world unless these agree, so the
        comparison layer can refuse pairing rather than assume it.
        """

        config = env.config
        dataset = getattr(episode, "dataset_hash", None) or "dataset_unknown"
        start = getattr(episode, "start_utc_ms", None)
        end = getattr(episode, "end_utc_ms", None)
        region = getattr(episode, "region_id", None) or str(config.source.region_id)
        events = env.event_schedule.summary()
        event_key = "|".join(
            f"{item.get('event_type')}@{item.get('site_index')}:{item.get('start_s')}-"
            f"{item.get('end_s')}"
            for item in events
            if isinstance(item, Mapping)
        )
        return f"{dataset}/{region}/{start}-{end}/{config.preset_name}/{event_key or 'no_events'}"

    def _note_gap(self) -> None:
        if self._gap_since_sequence is None:
            self._gap_since_sequence = self._sequence

    def _emit(self, frame: SceneFrame, *, build_s: float = 0.0) -> None:
        payload = frame.to_bytes()
        charge = self._gate.charge(len(payload))
        if charge is GateVerdict.FRAME_TOO_LARGE:
            # An oversized scene is reported, never silently trimmed of unserved cells.
            self._skipped_oversized += 1
            self._last_error = (
                f"scene of {len(payload)} bytes exceeded max_frame_bytes="
                f"{self._gate.max_frame_bytes}; frame reported, not emitted"
            )
            self._note_gap()
            return
        started = time.perf_counter()
        display_active = getattr(self._sink, "active", True)
        delivered = self._sink.offer(payload)
        latency = (time.perf_counter() - started) + build_s
        written = False
        if self._trace_writer is not None:
            written = self._trace_writer.append(
                payload,
                sequence=self._sequence,
                time_s=frame.clock.simulation_time_s,
            )
            if not written:
                self._last_error = self._trace_writer.error or "trace write refused"
        # The breaker watches the *display* channel. A recording session with no viewer has
        # no display channel at all, and its refusals are not transport failures.
        if display_active:
            message = self._breaker.record(ok=delivered, latency_s=latency)
            if message is not None:
                self._gate.open_circuit(self._breaker.cooldown_s)
                self._last_error = message
        if delivered or written:
            self._stream_state = StreamState.LIVE
            self._emitted += 1
        self._sequence += 1
        if self._gap_since_sequence is not None and self._trace_writer is not None:
            self._trace_writer.note_gap(
                after_sequence=self._gap_since_sequence,
                reason="refused_by_preview_gate",
                count=max(0, self._sequence - self._gap_since_sequence - 1),
            )
        self._gap_since_sequence = None
        self._publish_health()

    def _publish_health(self) -> None:
        writer = getattr(self._sink, "write_health", None)
        if not callable(writer):
            return
        from ..records import dumps

        payload = {
            "stream_health": self.stream_health().to_json(),
            "gate": self._gate.counters.to_json(),
            "sink": self._sink.stats.to_json(),
            "emitted": self._emitted,
            "sequence": self._sequence,
            "capture_wall_time_utc": _utc_now(),
        }
        writer(dumps(payload).encode("utf-8"))


_REWARD_INFO_UNITS = {
    "unmet_mbit_interval": "Mbit",
    "delivered_mbit_interval": "Mbit",
    "offered_mbit_interval": "Mbit",
    "motion_effort_integral_s": "s",
    "service_term": "reward",
    "motion_term": "reward",
    "reward_total": "reward",
    "reference_scale_mbps": "Mbps",
    "reference_dt_s": "s",
}
