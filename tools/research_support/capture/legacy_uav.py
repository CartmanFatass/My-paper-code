"""Scene capture for the legacy mobile UAV relay environments.

The target route is ``ha_ctse_process.env_factory`` scenario ``base`` (aliases ``4`` /
``s4``), which constructs :class:`envs.pettingzoo.relay.forced_relay.UAVForcedRelayEnv`
behind :class:`envs.pettingzoo.env_adapter.ParallelToArrayAdapter`. It is the environment
with genuinely mobile ground UEs: ``user_movement_model`` drives a random walk or an RPGM
cluster process, so the UEs on screen move because the simulation moved them. Nothing here
invents motion, and the sibling ``routed_core`` environment is a different class that this
alias does not construct.

This capture needs **no edit to shared environment code**. The adapter already builds
``info["state_info"]`` on every reset and step, which is where positions, the association
matrix, the UAV-UAV and UAV-site adjacency and the reconstructed routing paths live. The
wrapper reads that already-produced mapping; the only direct attribute read is the cached
``sinr_matrix``, and it is read, never recomputed. No radio method is invoked to draw a
frame, because several of them consume RNG or update caches.

The environment has no traffic-demand model, so ``offered``/``delivered`` Mbps are
reported as ``NOT_APPLICABLE`` rather than as zeros, and the viewer shows association,
coverage and SINR instead of invented rates.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

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
    canonical_link_key,
    dumps,
)
from .profiles import CaptureGate, GateVerdict
from .transport import FrameSink, OverloadBreaker

LEGACY_RELAY_CAPABILITY = SceneCapability(
    has_uav_positions=True,
    has_uav_velocity=False,
    has_requested_action=True,
    has_skill_labels=False,
    has_energy=False,
    has_individual_ues=True,
    has_aggregate_demand=False,
    has_demand_rates=False,
    has_delivered_rates=False,
    has_sites=True,
    has_links=True,
    has_link_flows=False,
    has_link_capacity=True,
    has_resource_domains=False,
    has_candidate_paths=True,
    has_sinr=True,
    has_association=True,
    has_observation_view=False,
    has_roster_changes=False,
    has_altitude=True,
    has_interval_metrics=True,
    notes=(
        "ground markers are individual simulated UEs; they move because the environment's "
        "mobility model moved them",
        "this environment has no traffic-demand model: offered and delivered Mbps are not "
        "applicable and are never shown as zero",
        "a path capacity is the reconstructed route's bottleneck; it is not a measured "
        "delivered rate",
    ),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _as_array(value: Any, dtype: Any) -> np.ndarray | None:
    if value is None:
        return None
    array = np.asarray(value, dtype=dtype)
    return array


class LegacyRelayObserver:
    """Builds scenes from an adapter's already-produced ``state_info``.

    Unlike the service-restoration observer this one is driven from outside the
    environment: :class:`LegacyCaptureWrapper` calls it after ``reset``/``step`` returns.
    That keeps the legacy route free of any shared edit.
    """

    def __init__(
        self,
        *,
        gate: CaptureGate,
        sink: FrameSink,
        run_id: str,
        trace_id: str,
        route: str = "legacy-mobile-relay",
        lane_id: int = 0,
        scenario: str = "base",
        environment_id: str = "uav_forced_relay_env_v0",
        policy_kind: PolicyKind = PolicyKind.FIXED_ACTION,
        source_kind: SourceKind = SourceKind.RULE_CONTROLLER_ROLLOUT,
        policy_label: str = "unspecified",
        checkpoint_identity: str | None = None,
        trace_writer: Any | None = None,
        breaker: OverloadBreaker | None = None,
    ) -> None:
        self._gate = gate
        self._sink = sink
        self._run_id = run_id
        self._trace_id = trace_id
        self._route = route
        self._lane_id = int(lane_id)
        self._scenario = scenario
        self._environment_id = environment_id
        self._policy_kind = policy_kind
        self._source_kind = source_kind
        self._policy_label = policy_label
        self._checkpoint_identity = checkpoint_identity
        self._trace_writer = trace_writer
        self._breaker = breaker or OverloadBreaker()

        self._sequence = 0
        self._completed_steps = 0
        self._episode_index = -1
        self._lifetime = LifetimeRegistry()
        self._stream_state = StreamState.WAITING
        self._last_error: str | None = None
        self._emitted = 0
        self._skipped_oversized = 0
        self._gap_since_sequence: int | None = None
        # Disagreement counters between the environment's two backhaul criteria; see
        # :meth:`_topology`.
        self._route_edges_without_adjacency = 0
        self._adjacency_edges_without_route = 0

    # ----------------------------------------------------------------------------------

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
        self._stream_state = state
        self._publish_health()

    def begin_episode(self) -> None:
        self._episode_index += 1
        self._lifetime = LifetimeRegistry()

    # ----------------------------------------------------------------------------------

    def observe(
        self,
        *,
        raw_env: Any,
        state_info: Mapping[str, Any],
        frame_kind: FrameKind,
        requested_actions: np.ndarray | None = None,
        interval_metrics: Mapping[str, Measured] | None = None,
        events: Sequence[DecisionEvent] = (),
        force_first: bool = False,
    ) -> bool:
        """Gate, then build and emit one frame. Returns whether a frame was emitted.

        Every gate is evaluated before a single array is copied out of ``state_info``.
        """

        verdict = self._gate.admit(self._lane_id, self._completed_steps, force_first=force_first)
        if not verdict.admitted:
            if verdict is GateVerdict.CIRCUIT_OPEN:
                self._stream_state = StreamState.STALE
            if self._gap_since_sequence is None:
                self._gap_since_sequence = self._sequence
            return False
        started = time.perf_counter()
        frame = self._build_frame(
            raw_env=raw_env,
            state_info=state_info,
            frame_kind=frame_kind,
            requested_actions=requested_actions,
            interval_metrics=interval_metrics or {},
            events=events,
        )
        build_s = time.perf_counter() - started
        return self._emit(frame, build_s=build_s)

    # ----------------------------------------------------------------------------------

    def _build_frame(
        self,
        *,
        raw_env: Any,
        state_info: Mapping[str, Any],
        frame_kind: FrameKind,
        requested_actions: np.ndarray | None,
        interval_metrics: Mapping[str, Measured],
        events: Sequence[DecisionEvent],
    ) -> SceneFrame:
        uav_positions = _as_array(state_info.get("uav_positions"), np.float64)
        user_positions = _as_array(state_info.get("user_positions"), np.float64)
        bs_positions = _as_array(state_info.get("ground_bs_positions"), np.float64)
        if bs_positions is None:
            bs_positions = _as_array(getattr(raw_env, "ground_bs_positions", None), np.float64)
        connections = _as_array(state_info.get("connections"), bool)
        uav_links = _as_array(state_info.get("uav_connections"), bool)
        uav_bs_links = _as_array(state_info.get("uav_bs_connections"), bool)
        routing_paths = state_info.get("routing_paths") or {}
        # Already-computed cache; reading it invokes no radio method and consumes no RNG.
        sinr = _as_array(getattr(raw_env, "sinr_matrix", None), np.float64)
        min_sinr = float(getattr(raw_env, "min_sinr", float("nan")))
        area_size = float(state_info.get("area_size", getattr(raw_env, "area_size", 0.0)))
        current_step = int(state_info.get("current_step", 0))
        max_steps = int(state_info.get("max_steps", getattr(raw_env, "max_steps", 0)))

        n_uavs = 0 if uav_positions is None else int(uav_positions.shape[0])
        n_users = 0 if user_positions is None else int(user_positions.shape[0])
        n_bs = 0 if bs_positions is None else int(bs_positions.shape[0])
        self._lifetime.observe(EntityKind.UAV, range(n_uavs))
        self._lifetime.observe(EntityKind.INDIVIDUAL_UE, range(n_users))
        self._lifetime.observe(EntityKind.SITE, range(n_bs))

        routed = {int(k) for k in routing_paths}

        uavs = tuple(
            UavState(
                entity=self._lifetime.entity(EntityKind.UAV, index, label=f"uav_{index}"),
                position_m=tuple(float(v) for v in uav_positions[index][:3]),
                active=True,
                executed_velocity_mps=None,
                requested_velocity_mps=(
                    None
                    if requested_actions is None or index >= requested_actions.shape[0]
                    else tuple(float(v) for v in np.asarray(requested_actions[index]).reshape(-1)[:3])
                ),
                team_skill_id=None,
                individual_skill_id=None,
                skill_age_s=Measured.not_recorded("no skill layer on this route"),
                energy=Measured.not_applicable("this scenario has no battery model"),
            )
            for index in range(n_uavs)
        )

        ground = tuple(
            self._ue_state(index, user_positions, connections, sinr, routed)
            for index in range(n_users)
        )

        sites = tuple(
            SiteStateRecord(
                entity=self._lifetime.entity(EntityKind.SITE, index, label=f"ground_bs_{index}"),
                position_m=tuple(float(v) for v in bs_positions[index][:3]),
                radio_up=True,
                core_link_up=True,
                access_capacity_scale=Measured.not_recorded(
                    "this scenario models no site capacity scaling"
                ),
                backhaul_capacity_scale=Measured.not_recorded(
                    "this scenario models no site capacity scaling"
                ),
                observed=True,
                degraded=False,
            )
            for index in range(n_bs)
        )

        links, paths = self._topology(
            connections=connections,
            uav_links=uav_links,
            uav_bs_links=uav_bs_links,
            routing_paths=routing_paths,
            sinr=sinr,
        )
        metrics = dict(interval_metrics)
        # Surfaced as ordinary scene diagnostics so the disagreement between the two
        # backhaul criteria is visible in the UI and in a recorded trace.
        metrics["backhaul_route_edges_without_sinr_adjacency"] = Measured.ok(
            int(self._route_edges_without_adjacency), unit="count"
        )
        metrics["backhaul_sinr_adjacency_edges_without_route"] = Measured.ok(
            int(self._adjacency_edges_without_route), unit="count"
        )
        metrics["ues_associated"] = Measured.ok(
            0 if connections is None else int(np.count_nonzero(connections.any(axis=0))),
            unit="count",
        )
        metrics["uavs_with_route"] = Measured.ok(len(routed), unit="count")

        identity = SceneIdentity(
            run_id=self._run_id,
            trace_id=self._trace_id,
            episode_id=f"episode_{max(self._episode_index, 0)}",
            world_id=f"{self._scenario}/episode_{max(self._episode_index, 0)}",
            lane_id=self._lane_id,
            sequence=self._sequence,
        )
        # This route's clock is a decision-step index; there is no separate physics
        # subinterval, so geometry time and simulation time coincide.
        time_step = float(getattr(raw_env, "time_step", 1.0) or 1.0)
        sim_time = float(current_step) * time_step
        clock = SceneClock(
            simulation_time_s=sim_time,
            geometry_time_s=sim_time,
            decision_step=current_step,
            capture_wall_time_utc=_utc_now(),
            producer_monotonic_s=time.monotonic(),
            measurement_start_s=max(0.0, sim_time - time_step),
            measurement_end_s=sim_time,
            training_step=None,
            substep_index=None,
        )
        provenance = SceneProvenance(
            route=self._route,
            environment_id=self._environment_id,
            source_kind=self._source_kind,
            policy_kind=self._policy_kind,
            information_condition="legacy_relay_local_view",
            frame_kind=frame_kind,
            capture_resolution="one_frame_per_admitted_decision_step",
            dataset_hash=None,
            checkpoint_identity=self._checkpoint_identity,
            is_real_activity_data=False,
            measured_fields=(
                "positions, association matrix, UAV-UAV and UAV-site adjacency and the "
                "reconstructed routing paths are read from the adapter's state_info; SINR "
                "is read from the environment's cached matrix",
            ),
            derived_fields=(
                "link activity is derived here from the association matrix combined with "
                "whether the serving UAV holds a reconstructed route to a ground station",
            ),
            notes=(
                f"policy_label={self._policy_label}",
                f"scenario={self._scenario}",
                f"min_sinr_db={min_sinr}",
                f"max_steps={max_steps}",
            ),
        )
        bounds = (0.0, 0.0, area_size, area_size)
        return SceneFrame(
            identity=identity,
            clock=clock,
            provenance=provenance,
            geometry=SceneGeometry(bounds_m=bounds),
            capability=LEGACY_RELAY_CAPABILITY,
            uavs=uavs,
            ground_entities=ground,
            sites=sites,
            links=links,
            resource_domains=(),
            paths=paths,
            events=tuple(events),
            interval_metrics=metrics,
            observation_view=ObservationView(
                values={},
                masks={},
                ages_s={},
                field_provenance={},
                information_condition=(
                    "not reconstructed for this route; the per-agent local view is not "
                    "exposed through state_info and is therefore not shown"
                ),
            ),
            stream_health=self.stream_health(),
        )

    def _ue_state(
        self,
        index: int,
        user_positions: np.ndarray,
        connections: np.ndarray | None,
        sinr: np.ndarray | None,
        routed: set[int],
    ) -> GroundEntityState:
        entity = self._lifetime.entity(EntityKind.INDIVIDUAL_UE, index, label=f"ue_{index}")
        serving: int | None = None
        if connections is not None and index < connections.shape[1]:
            candidates = np.flatnonzero(connections[:, index])
            if candidates.size:
                serving = int(candidates[0])
        if serving is None:
            status = "unserved"
            associated_to = None
        elif serving in routed:
            status = "served"
            associated_to = self._lifetime.entity(EntityKind.UAV, serving).key
        else:
            # Associated to a UAV that has no reconstructed route to a ground station: a
            # visible access link with no backhaul is not a successful service path.
            status = "associated_no_backhaul"
            associated_to = self._lifetime.entity(EntityKind.UAV, serving).key
        if sinr is not None and serving is not None and serving < sinr.shape[0]:
            sinr_value = Measured.from_float(float(sinr[serving, index]), unit="dB")
        else:
            sinr_value = Measured.not_recorded("no serving UAV for this UE", unit="dB")
        return GroundEntityState(
            entity=entity,
            position_m=tuple(float(v) for v in user_positions[index][:3]),
            active=True,
            # No traffic model on this route: not applicable, never a measured zero.
            offered_mbps=Measured.not_applicable("environment models no traffic demand"),
            delivered_mbps=Measured.not_applicable("environment models no traffic demand"),
            observed=True,
            age_s=Measured.not_applicable("simulator-truth view is current"),
            service_status=status,
            associated_to=associated_to,
            sinr_db=sinr_value,
            represents_count=1,
        )

    def _topology(
        self,
        *,
        connections: np.ndarray | None,
        uav_links: np.ndarray | None,
        uav_bs_links: np.ndarray | None,
        routing_paths: Mapping[Any, Any],
        sinr: np.ndarray | None,
    ) -> tuple[tuple[LinkRecord, ...], tuple[PathRecord, ...]]:
        links: list[LinkRecord] = []
        routed = {int(k) for k in routing_paths}
        # This environment decides backhaul twice, by two different criteria, and they can
        # disagree:
        #
        #   * ``uav_connections`` / ``uav_bs_connections`` are boolean adjacency set from a
        #     SINR threshold;
        #   * ``routing_paths`` comes from ``_find_widest_path_to_ground_bs``, whose edge
        #     test is ``_get_link_capacity() > 0`` — a Shannon capacity from geometry that
        #     never consults those matrices.
        #
        # A route edge therefore exists that the adjacency matrix does not contain. Both
        # are reported, each labelled with the criterion that admitted it, and the
        # disagreement is counted rather than resolved here. Picking one criterion would
        # make the picture look self-consistent while hiding a real property of the model.
        carrying: set[tuple[str, int, str, int]] = set()
        for entry in routing_paths.values():
            path = entry[0] if isinstance(entry, tuple) else entry
            if not path:
                continue
            for first, second in zip(path[:-1], path[1:]):
                first_tag = self._PATH_NODE_KINDS[str(first[0])][1]
                second_tag = self._PATH_NODE_KINDS[str(second[0])][1]
                carrying.add((first_tag, int(first[1]), second_tag, int(second[1])))
        adjacency: set[tuple[str, int, str, int]] = set()
        if uav_links is not None:
            adjacency |= {("uav", int(a), "uav", int(b)) for a, b in zip(*np.nonzero(uav_links))}
        if uav_bs_links is not None:
            adjacency |= {
                ("uav", int(u), "bs", int(s)) for u, s in zip(*np.nonzero(uav_bs_links))
            }
        self._route_edges_without_adjacency = len(carrying - adjacency)
        self._adjacency_edges_without_route = len(adjacency - carrying)

        if connections is not None:
            for uav_index, ue_index in zip(*np.nonzero(connections)):
                source = self._lifetime.entity(EntityKind.UAV, int(uav_index))
                target = self._lifetime.entity(EntityKind.INDIVIDUAL_UE, int(ue_index))
                snr = (
                    Measured.from_float(float(sinr[uav_index, ue_index]), unit="dB")
                    if sinr is not None
                    else Measured.not_recorded("no cached SINR matrix", unit="dB")
                )
                links.append(
                    LinkRecord(
                        link_key=canonical_link_key(source, target, "uav_access"),
                        source=source,
                        target=target,
                        link_class="uav_access",
                        activity=(
                            LinkActivity.ACTIVE
                            if int(uav_index) in routed
                            else LinkActivity.AVAILABLE
                        ),
                        capacity_mbps=Measured.not_recorded(
                            "per-access-link capacity is not retained by this route"
                        ),
                        flow_mbps=Measured.not_applicable(
                            "environment models no traffic flow"
                        ),
                        utilization=Measured.not_applicable(
                            "environment models no traffic flow"
                        ),
                        snr_db=snr,
                        distance_m=Measured.not_recorded("not retained by this route"),
                    )
                )

        # Backhaul: the union of both criteria, each edge labelled with what admitted it.
        for edge in sorted(adjacency | carrying):
            source_tag, source_index, target_tag, target_index = edge
            source = self._lifetime.entity(EntityKind.UAV, source_index)
            if target_tag == "uav":
                target = self._lifetime.entity(EntityKind.UAV, target_index)
                link_class = "uav_uav_backhaul"
            else:
                target = self._lifetime.entity(EntityKind.SITE, target_index)
                link_class = "site_uav_backhaul"
            in_route = edge in carrying
            in_adjacency = edge in adjacency
            if in_route and in_adjacency:
                criterion = "sinr_adjacency_and_widest_path_route"
            elif in_route:
                criterion = "widest_path_route_only_not_in_sinr_adjacency"
            else:
                criterion = "sinr_adjacency_only_no_route_uses_it"
            links.append(
                LinkRecord(
                    link_key=canonical_link_key(source, target, link_class),
                    source=source,
                    target=target,
                    link_class=link_class,
                    activity=LinkActivity.ACTIVE if in_route else LinkActivity.AVAILABLE,
                    capacity_mbps=Measured.not_recorded(
                        f"per-link capacity is not retained; admitted by {criterion}"
                    ),
                    flow_mbps=Measured.not_applicable("environment models no traffic flow"),
                    utilization=Measured.not_applicable("environment models no traffic flow"),
                    snr_db=Measured.not_recorded("backhaul SINR is not cached per pair"),
                    distance_m=Measured.not_recorded("not retained by this route"),
                )
            )

        link_keys = {link.link_key for link in links}
        paths: list[PathRecord] = []
        for uav_index, entry in routing_paths.items():
            path, capacity = entry if isinstance(entry, tuple) else (entry, None)
            if not path:
                continue
            node_keys = tuple(self._node_key(kind, index) for kind, index in path)
            path_link_keys = tuple(
                key
                for key in (
                    self._edge_key(first, second) for first, second in zip(path[:-1], path[1:])
                )
                if key in link_keys
            )
            paths.append(
                PathRecord(
                    demand_entity=self._lifetime.entity(EntityKind.UAV, int(uav_index)).key,
                    node_keys=node_keys,
                    link_keys=path_link_keys,
                    backhaul_hops=max(0, len(path) - 2),
                    # The reconstructed route's bottleneck capacity, not a delivered rate.
                    flow_mbps=Measured.not_applicable(
                        "route capacity is a bottleneck, not a measured flow"
                    ),
                    selected=True,
                )
            )
            if capacity is not None:
                paths[-1] = PathRecord(
                    demand_entity=paths[-1].demand_entity,
                    node_keys=paths[-1].node_keys,
                    link_keys=paths[-1].link_keys,
                    backhaul_hops=paths[-1].backhaul_hops,
                    flow_mbps=Measured.not_applicable(
                        f"bottleneck_capacity={float(capacity):.6g}; a capacity, not a flow"
                    ),
                    selected=True,
                )
        return tuple(links), tuple(paths)

    #: Node tags the legacy routing reconstruction puts into a path tuple. The ground
    #: station is spelled ``ground_bs`` there; ``bs`` is accepted as a historical alias.
    _PATH_NODE_KINDS = {
        "uav": (EntityKind.UAV, "uav"),
        "ground_bs": (EntityKind.SITE, "bs"),
        "bs": (EntityKind.SITE, "bs"),
        "user": (EntityKind.INDIVIDUAL_UE, "user"),
    }

    def _node_key(self, kind: str, index: int) -> str:
        entity_kind, _tag = self._PATH_NODE_KINDS[str(kind)]
        return self._lifetime.entity(entity_kind, int(index)).key

    def _edge_key(self, first: Sequence[Any], second: Sequence[Any]) -> str:
        kinds = self._PATH_NODE_KINDS
        source_kind, source_tag = kinds[str(first[0])]
        target_kind, target_tag = kinds[str(second[0])]
        source = self._lifetime.entity(source_kind, int(first[1]))
        target = self._lifetime.entity(target_kind, int(second[1]))
        link_class = {
            ("uav", "uav"): "uav_uav_backhaul",
            ("uav", "bs"): "site_uav_backhaul",
            ("uav", "user"): "uav_access",
        }.get((source_tag, target_tag), "unknown")
        return canonical_link_key(source, target, link_class)

    # ----------------------------------------------------------------------------------

    def _emit(self, frame: SceneFrame, *, build_s: float = 0.0) -> bool:
        payload = frame.to_bytes()
        if self._gate.charge(len(payload)) is GateVerdict.FRAME_TOO_LARGE:
            self._skipped_oversized += 1
            self._last_error = (
                f"scene of {len(payload)} bytes exceeded max_frame_bytes="
                f"{self._gate.max_frame_bytes}; frame reported, not emitted"
            )
            if self._gap_since_sequence is None:
                self._gap_since_sequence = self._sequence
            return False
        started = time.perf_counter()
        display_active = getattr(self._sink, "active", True)
        delivered = self._sink.offer(payload)
        latency = (time.perf_counter() - started) + build_s
        written = False
        if self._trace_writer is not None:
            written = self._trace_writer.append(
                payload, sequence=self._sequence, time_s=frame.clock.simulation_time_s
            )
            if not written:
                self._last_error = self._trace_writer.error or "trace write refused"
        # The breaker watches the *display* channel only; see the service-restoration
        # observer for the same reasoning.
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
        return delivered

    def _publish_health(self) -> None:
        writer = getattr(self._sink, "write_health", None)
        if not callable(writer):
            return
        writer(
            dumps(
                {
                    "stream_health": self.stream_health().to_json(),
                    "gate": self._gate.counters.to_json(),
                    "sink": self._sink.stats.to_json(),
                    "emitted": self._emitted,
                    "sequence": self._sequence,
                    "capture_wall_time_utc": _utc_now(),
                }
            ).encode("utf-8")
        )

    def step_completed(self) -> None:
        self._completed_steps += 1


class LegacyCaptureWrapper:
    """Transparent wrapper that captures from an adapter without editing it.

    It forwards every attribute it does not define, so a runner that received a
    :class:`ParallelToArrayAdapter` keeps working unchanged. ``reset`` and ``step`` are
    intercepted only to read the ``state_info`` mapping the adapter had already built.

    The wrapper deliberately does not touch ``obs``, ``state``, rewards, termination flags
    or ``info`` contents: it reads and returns them untouched.
    """

    def __init__(self, adapter: Any, observer: LegacyRelayObserver) -> None:
        self._adapter = adapter
        self._observer = observer

    def __getattr__(self, name: str) -> Any:
        # Only reached for names this wrapper does not define.
        return getattr(self._adapter, name)

    @property
    def unwrapped_adapter(self) -> Any:
        return self._adapter

    @property
    def observer(self) -> LegacyRelayObserver:
        return self._observer

    def reset(self, *args: Any, **kwargs: Any) -> Any:
        result = self._adapter.reset(*args, **kwargs)
        self._observer.begin_episode()
        info = result[1] if isinstance(result, tuple) and len(result) > 1 else {}
        state_info = (info or {}).get("state_info") or {}
        if state_info:
            self._observer.observe(
                raw_env=self._adapter.env,
                state_info=state_info,
                frame_kind=FrameKind.INITIAL,
                force_first=True,
            )
        return result

    def step(self, actions: Any) -> Any:
        result = self._adapter.step(actions)
        info = result[4] if isinstance(result, tuple) and len(result) > 4 else {}
        state_info = (info or {}).get("state_info") or {}
        self._observer.step_completed()
        if state_info:
            terminated = bool(result[2]) if len(result) > 2 else False
            truncated = bool(result[3]) if len(result) > 3 else False
            reward = result[1] if len(result) > 1 else None
            metrics: dict[str, Measured] = {}
            if reward is not None:
                metrics["reward_total"] = Measured.from_float(
                    float(np.asarray(reward).reshape(-1)[0])
                    if np.asarray(reward).size
                    else None,
                    unit="native_reward",
                )
            metrics["terminated"] = Measured.ok(terminated)
            metrics["truncated"] = Measured.ok(truncated)
            self._observer.observe(
                raw_env=self._adapter.env,
                state_info=state_info,
                frame_kind=(
                    FrameKind.FINAL if (terminated or truncated) else FrameKind.TRANSITION
                ),
                requested_actions=_as_array(actions, np.float64),
                interval_metrics=metrics,
            )
        return result

    def close(self) -> Any:
        self._observer.finish()
        return self._adapter.close()
