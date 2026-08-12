"""Concrete frozen-checkpoint evaluation bridge for CRTO-B1 v4.

The bridge owns episode-panel construction, locked recurrent policy execution,
development hazard rows, scored/donor boundary capture, complete-rollout cuts,
one-packet deranged replays, and bounded sixteen-step audits.  It deliberately
returns raw seed-local records; cross-seed pooling remains in :mod:`analysis`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Callable, Mapping, Sequence

import numpy as np
import torch

from .config import AGENT_COUNT, ALGORITHM_SEEDS, HORIZON, OPTIONS, REGIMES
from .controls import (
    BoundaryRecord, HazardCellKey, HazardControlFit, RateCount,
    audit_advantage_and_regret, build_derangement_plan, fit_rate_matched_hazard,
    evaluation_rate_balance, hazard_target_support, termination_mass,
)
from .analysis import (
    AuditState, BalanceRow, CalibrationObservation, EpisodeOutcome, ShadowScore,
    adverse_residual_trend, audit_mechanism_diagnostics, build_result_packet,
    calibration_diagnostic, donor_balance_feature_vectors,
    donor_recipient_balance_diagnostic, mechanism_estimand, primary_estimands,
    registered_package_and_mechanism_decisions, resource_conformance,
    retirement_decision_from_analysis_outputs, shortcut_shadow_diagnostic, validity_decisions,
)
from .host import (
    CueState, DecisionKind, DecisionRecord, Option,
    Regime, ScenarioSpec, ServiceRelayHost, balanced_scenario_specs,
    build_scenario_tape, common_future_audit_rollout,
)
from .models import RecurrentOptionActorCritic
from .predictor import CalibrationTable, FrozenPredictor, PacketBundle, make_packets


PANEL_ROOT_NAMESPACE = 2_026_081_203
PANEL_ORDINALS = {
    "hazard": 0,
    "scored": 1,
    "cuts": 2,
    "donor": 3,
}
HAZARD_SWITCH_FEATURE_ENCODING_ID = "CRTO-B1-v4-FULL-ONEHOT-REGIME-DIRECTION-PHASE"
REGIME_ENUM = {
    "K8": Regime.K8, "K16": Regime.K16,
    "K4_TO_16": Regime.K4_TO_16, "K16_TO_4": Regime.K16_TO_4,
}
CUT_METHODS = ("Q-ONLY-CRTO", "RATE-MATCHED-HAZARD-CRTO", "FORCED-RENEWAL-ONLY")


def panel_root(algorithm_seed: int, panel_ordinal: int) -> int:
    """Stable root containing only the frozen namespace, seed, and panel ordinal."""

    if algorithm_seed < 0 or panel_ordinal < 0:
        raise ValueError("algorithm seed and panel ordinal must be nonnegative")
    # SeedSequence avoids decimal concatenation collisions while exposing an
    # integer accepted by the host's deterministic manifest constructor.
    state = np.random.SeedSequence(
        [PANEL_ROOT_NAMESPACE, int(algorithm_seed), int(panel_ordinal)]
    ).generate_state(2, dtype=np.uint32)
    return int(state[0]) | (int(state[1]) << 32)


def _episode_seed(algorithm_seed: int, panel_ordinal: int, episode_index: int) -> int:
    state = np.random.SeedSequence([
        PANEL_ROOT_NAMESPACE, int(algorithm_seed), int(panel_ordinal), int(episode_index),
    ]).generate_state(2, dtype=np.uint32)
    return int(state[0]) | (int(state[1]) << 32)


def panel_specs(
    algorithm_seed: int, panel: str, regime: str, count: int,
) -> tuple[ScenarioSpec, ...]:
    """Build one disjoint deterministic panel; episode index is explicit in each row."""

    if panel not in PANEL_ORDINALS or regime not in REGIME_ENUM:
        raise ValueError("unknown CRTO evaluation panel or regime")
    ordinal = PANEL_ORDINALS[panel]
    root = panel_root(algorithm_seed, ordinal)
    # Index ranges are panel-disjoint and stable independently of root hashing.
    first = ordinal * 10_000 + REGIMES.index(regime) * 1_000
    specs = balanced_scenario_specs(
        count=count, regime=REGIME_ENUM[regime], root_seed=root,
        first_episode_index=first,
    )
    # Make the required four-coordinate seed law literal at the tape boundary.
    return tuple(ScenarioSpec(
        episode_index=spec.episode_index,
        episode_seed=_episode_seed(algorithm_seed, ordinal, spec.episode_index),
        regime=spec.regime, event=spec.event, event_onset=spec.event_onset,
        replanning_cost=spec.replanning_cost,
    ) for spec in specs)


@dataclass(frozen=True)
class BoundarySnapshot:
    record: BoundaryRecord
    host: ServiceRelayHost
    target_agent: int
    aligned_decisions: tuple[DecisionRecord, ...]
    aligned_action: str
    residual_tensor: np.ndarray
    cholesky: np.ndarray
    joint_option_counts: tuple[int, ...]
    location_counts: tuple[int, ...]
    prefix_reward_sum: float


@dataclass(frozen=True)
class EpisodeRaw:
    method: str
    scenario_id: str
    scenario: ScenarioSpec
    normalized_score: float
    failure: bool
    delivery_fraction: float
    total_overflow: int
    total_energy_spent: float
    renewal_count: int
    replan_count: int
    simultaneous_trigger_count: int
    option_collisions: int
    total_decision_charge: float
    legal_discretionary_reviews: int
    changed_option_terminations: int
    boundary: BoundarySnapshot | None
    calibration_rows: tuple[dict[str, object], ...]
    hazard_rows: tuple[tuple[np.ndarray, int, HazardCellKey], ...]
    evaluation_cell_keys: tuple[HazardCellKey, ...]


def _compact_episode(
    host: ServiceRelayHost, *, method: str, reviews: int, terms: int,
    boundary: BoundarySnapshot | None = None,
    calibration_rows: Sequence[dict[str, object]] = (),
    hazard_rows: Sequence[tuple[np.ndarray, int, HazardCellKey]] = (),
    evaluation_cell_keys: Sequence[HazardCellKey] = (),
    prefix_reward_sum: float = 0.0,
) -> EpisodeRaw:
    """Detach every analysis scalar while discarding primitive-step objects."""

    if not host.done or host.state.total_arrivals != host.tape.total_physical_arrivals():
        raise RuntimeError("compact episode requires one complete registered trajectory")
    # Aggregate rewards before dropping the step records. This avoids retaining
    # or reading the host's private running-sum implementation detail.
    reward_sum = float(prefix_reward_sum + sum(step.reward for step in host.steps))
    denominator = max(1, host.state.total_arrivals)
    delivery_fraction = host.state.total_delivered / denominator
    return EpisodeRaw(
        method, str(host.tape.spec.episode_index), host.tape.spec,
        reward_sum / denominator,
        delivery_fraction < 0.80 or host.state.total_overflow > 0,
        delivery_fraction, host.state.total_overflow, host.state.total_energy_spent,
        host.state.renewal_count, host.state.replan_count,
        host.state.simultaneous_trigger_count, host.state.option_collisions,
        host.state.total_renewal_replan_cost, reviews, terms, boundary,
        tuple(calibration_rows), tuple(hazard_rows), tuple(evaluation_cell_keys),
    )


class LockedPolicy:
    """Stateful locked recurrent evaluator with the common frozen predictor."""

    def __init__(
        self, model: RecurrentOptionActorCritic, predictor: FrozenPredictor,
        calibration: CalibrationTable,
    ) -> None:
        self.model = model
        self.predictor = predictor
        self.calibration = calibration
        self.hidden = model.initial_hidden(AGENT_COUNT)
        self.histories: list[list[torch.Tensor]] = [[] for _ in range(AGENT_COUNT)]
        self.anchor_history: list[torch.Tensor | None] = [None] * AGENT_COUNT
        self.anchor_option = np.full(AGENT_COUNT, -1, dtype=np.int64)
        self.anchor_k = np.zeros(AGENT_COUNT, dtype=np.int64)
        self.anchor_time = np.full(AGENT_COUNT, -1, dtype=np.int64)

    def clone(self) -> "LockedPolicy":
        result = object.__new__(LockedPolicy)
        result.model, result.predictor, result.calibration = self.model, self.predictor, self.calibration
        result.hidden = self.hidden.detach().clone()
        result.histories = [[value.detach().clone() for value in row] for row in self.histories]
        result.anchor_history = [None if value is None else value.detach().clone() for value in self.anchor_history]
        result.anchor_option = self.anchor_option.copy()
        result.anchor_k = self.anchor_k.copy()
        result.anchor_time = self.anchor_time.copy()
        return result

    def _forecast_packets(self, host: ServiceRelayHost) -> tuple[PacketBundle, ...]:
        bundles: list[PacketBundle] = []
        for agent in range(AGENT_COUNT):
            elapsed = host.state.primitive_time - int(self.anchor_time[agent])
            history = self.anchor_history[agent]
            if history is None or elapsed not in (4, 8, 12, 16):
                zero = torch.zeros(8)
                eye = torch.eye(8)
                bundles.append(make_packets(zero, zero, eye, self.calibration))
                continue
            with torch.no_grad():
                lengths = torch.tensor([history.shape[0]], dtype=torch.int64)
                dist = self.predictor(
                    history.unsqueeze(0), lengths,
                    torch.tensor([self.anchor_option[agent]]),
                    torch.tensor([self.anchor_k[agent]]), (elapsed,),
                )
                target = torch.as_tensor(host.predictor_target(agent), dtype=torch.float32).unsqueeze(0)
                bundles.append(make_packets(target, dist.mean[:, 0], dist.cholesky[:, 0], self.calibration))
        return tuple(bundles)

    def predecision(
        self, host: ServiceRelayHost, *, packet_override: Mapping[int, torch.Tensor] | None = None,
    ) -> tuple[object, tuple[PacketBundle, ...]]:
        observations = torch.stack([torch.as_tensor(row.vector()) for row in host.observations()])
        for agent, value in enumerate(observations):
            self.histories[agent].append(value.detach().clone())
        packets = self._forecast_packets(host) if host.initialized else tuple(
            make_packets(torch.zeros(1, 8), torch.zeros(1, 8), torch.eye(8).unsqueeze(0), self.calibration)
            for _ in range(AGENT_COUNT)
        )
        selected = []
        for agent, bundle in enumerate(packets):
            packet = bundle.explicit if self.model.arm.value == "CRTO" else bundle.raw
            if packet_override and agent in packet_override:
                packet = packet_override[agent]
            selected.append(packet.reshape(52))
        centralized = torch.as_tensor(host.centralized_state_vector() if host.initialized else np.zeros(self.model.centralized_state_dim), dtype=torch.float32)
        with torch.no_grad():
            step = self.model.forward_step(observations, self.hidden, centralized, torch.stack(selected))
        self.hidden = step.hidden.detach()
        return step, packets

    def decisions(
        self, host: ServiceRelayHost, *, disable_residual: bool = False,
        forced_renewal_only: bool = False, packet_override: Mapping[int, torch.Tensor] | None = None,
        hazard: HazardControlFit | None = None,
    ) -> tuple[tuple[DecisionRecord, ...], tuple[PacketBundle, ...]]:
        step, packets = self.predecision(host, packet_override=packet_override)
        q = [{Option(i): float(step.q[a, i]) for i in range(7)} for a in range(AGENT_COUNT)]
        b = [{Option(i): float(step.residual_contribution[a, i]) for i in range(7)} for a in range(AGENT_COUNT)]
        if not host.initialized:
            decisions = host.select_initial(q, training=False)
        elif hazard is None:
            decisions = host.resolve_reviews(q, b, training=False, disable_residual=disable_residual,
                                             forced_renewal_only=forced_renewal_only)
        else:
            decisions = _resolve_hazard(host, q, b, hazard)
        for row in decisions:
            if row.reanchored:
                self.anchor_history[row.agent] = torch.stack(self.histories[row.agent])
                self.anchor_option[row.agent] = int(row.selected_option)
                self.anchor_k[row.agent] = host.tape.k_at(host.state.primitive_time)
                self.anchor_time[row.agent] = host.state.primitive_time
        return decisions, packets


def _hazard_feature(host: ServiceRelayHost, agent: int) -> tuple[np.ndarray, HazardCellKey]:
    observation = host.observations()[agent]
    regime = host.tape.spec.regime.value
    current_k, age = host.tape.k_at(host.state.primitive_time), observation.absolute_age
    if HAZARD_SWITCH_FEATURE_ENCODING_ID != "CRTO-B1-v4-FULL-ONEHOT-REGIME-DIRECTION-PHASE":
        raise RuntimeError("evaluation bridge is not bound to the authoritative v4 hazard encoding")
    regime_order = ("K8", "K16", "K4_TO_16", "K16_TO_4")
    direction_order = ("NO_SWITCH", "FOUR_TO_SIXTEEN", "SIXTEEN_TO_FOUR")
    phase_order = (
        "FIXED", "PRE_9PLUS", "PRE_1_TO_8", "AT_SWITCH",
        "POST_1_TO_8", "POST_9PLUS", "FAR_POST",
    )
    if regime in ("K8", "K16"):
        direction, phase = "NO_SWITCH", "FIXED"
    else:
        direction = "FOUR_TO_SIXTEEN" if regime == "K4_TO_16" else "SIXTEEN_TO_FOUR"
        delta = host.state.primitive_time - 128
        if delta <= -9:
            phase = "PRE_9PLUS"
        elif delta <= -1:
            phase = "PRE_1_TO_8"
        elif delta == 0:
            phase = "AT_SWITCH"
        elif delta <= 8:
            phase = "POST_1_TO_8"
        elif delta <= 64:
            phase = "POST_9PLUS"
        else:
            phase = "FAR_POST"
    feature = np.asarray((
        1.0, *[float(int(observation.current_option) == option) for option in range(7)],
        current_k / 16.0, age / 16.0, age / current_k,
        host.tape.spec.replanning_cost / 4.0,
        *map(float, observation.legal_mask),
        *[float(observation.visible_cue is cue) for cue in (CueState.NONE, CueState.L, CueState.R)],
        *[float(regime == value) for value in regime_order],
        *[float(direction == value) for value in direction_order],
        *[float(phase == value) for value in phase_order],
    ), dtype=np.float64)
    if feature.shape != (36,):
        raise RuntimeError("v4 hazard feature must contain intercept plus exactly 35 slopes")
    return feature, HazardCellKey(regime, current_k, age, host.tape.spec.replanning_cost)


def _resolve_hazard(
    host: ServiceRelayHost, q: Sequence[Mapping[Option, float]],
    b: Sequence[Mapping[Option, float]], fit: HazardControlFit,
) -> tuple[DecisionRecord, ...]:
    """Resolve the residual-free stochastic hazard while preserving replacement scores."""

    kinds = host.review_kinds()
    terminate: dict[int, bool] = {}
    for agent, kind in enumerate(kinds):
        if kind is DecisionKind.DISCRETIONARY:
            x, key = _hazard_feature(host, agent)
            terminate[agent] = bool(fit.sampled_terminations(
                x.reshape(1, -1), (key,), (host.tape.rate_control_uniform[host.state.primitive_time, agent],)
            )[0])
    # Resolve the no-discretionary-termination base tuple on a clone, amend all
    # sampled hazard fires simultaneously, then ask the ordinary host API to
    # validate/apply that complete tuple. This includes the v4 t=128 action-
    # then-reanchor law and never routes a switch through the audit interface.
    baseline = host.clone()
    base_host = baseline.clone()
    amended = list(base_host.resolve_reviews(q, b, training=False, forced_renewal_only=True))
    switch = baseline.tape.k_at(baseline.state.primitive_time) != baseline.state.current_k
    for agent, fires in terminate.items():
        if not fires:
            continue
        current = Option(int(baseline.state.options[agent]))
        legal = [Option(i) for i, ok in enumerate(baseline.legal_mask(agent)) if ok and i != int(current)]
        if legal:
            selected = max(
                legal,
                key=lambda option: (
                    q[agent][option] + (0.0 if switch else b[agent][option]),
                    -int(option),
                ),
            )
            amended[agent] = DecisionRecord(
                agent, DecisionKind.DISCRETIONARY, current, selected, True,
                0.05 + host.tape.spec.replanning_cost,
                int(baseline.state.option_ages[agent]), 0, switch, True,
            )
    return host.apply_external_decisions(tuple(amended))


def _boundary_eligible(host: ServiceRelayHost) -> int | None:
    time, onset = host.state.primitive_time, host.tape.spec.event_onset
    if not onset + 4 <= time <= onset + 20 or abs(time - 128) <= 8:
        return None
    for agent, kind in enumerate(host.review_kinds()):
        if kind is DecisionKind.DISCRETIONARY and len(host.audit_action_set(agent)) > 1:
            return agent
    return None


def _boundary_snapshot(
    *, seed: int, panel: str, host: ServiceRelayHost, target: int,
    packets: tuple[PacketBundle, ...], decisions: tuple[DecisionRecord, ...],
) -> BoundarySnapshot:
    spec, observation = host.tape.spec, host.observations()[target]
    phase = (host.state.primitive_time - spec.event_onset) // 4
    record_id = f"{seed}:{spec.regime.value}:{panel}:{spec.episode_index}:{target}"
    record = BoundaryRecord(
        record_id, seed, spec.regime.value, panel, spec.episode_index, target,
        observation.current_option.label, host.tape.k_at(host.state.primitive_time),
        observation.absolute_age, tuple(map(int, observation.legal_mask)), spec.event.value,
        phase, observation.visible_cue.value, spec.replanning_cost,
    )
    packet = packets[target]
    lower = np.zeros((8, 8), dtype=np.float64)
    lower[np.tril_indices(8)] = packet.raw.reshape(52)[16:].numpy()
    return BoundarySnapshot(
        record, host.clone(retain_records=False), target, decisions,
        "KEEP" if not decisions[target].changed else decisions[target].selected_option.label,
        np.stack([bundle.explicit.reshape(52).numpy() for bundle in packets]),
        lower,
        tuple(int(np.count_nonzero(host.state.options == option)) for option in range(7)),
        tuple(int(np.count_nonzero(host.state.locations == location)) for location in range(3)),
        float(sum(step.reward for step in host.steps)),
    )


def _assert_same_predecision(
    reconstructed: ServiceRelayHost, saved: ServiceRelayHost, *, context: str,
) -> None:
    if reconstructed.tape.spec != saved.tape.spec:
        raise RuntimeError(f"{context} scenario identity diverged")
    left, right = reconstructed.state, saved.state
    scalar_fields = (
        "primitive_time", "current_k", "total_arrivals", "total_delivered",
        "total_overflow", "total_energy_spent", "total_renewal_replan_cost",
        "renewal_count", "replan_count", "simultaneous_trigger_count", "option_collisions",
    )
    if any(getattr(left, name) != getattr(right, name) for name in scalar_fields):
        raise RuntimeError(f"{context} aggregate predecision state diverged")
    array_fields = (
        "queues", "buffers", "locations", "energies", "options", "option_ages",
        "commitment_ids", "anchor_times", "anchor_commitment_ids",
    )
    if any(not np.array_equal(getattr(left, name), getattr(right, name)) for name in array_fields):
        raise RuntimeError(f"{context} physical/commitment predecision state diverged")
    if left.delivery_history != right.delivery_history:
        raise RuntimeError(f"{context} delivery-history state diverged")


def run_episode(
    *, seed: int, method: str, spec: ScenarioSpec, model: RecurrentOptionActorCritic,
    predictor: FrozenPredictor, calibration: CalibrationTable,
    panel: str, hazard: HazardControlFit | None = None,
) -> EpisodeRaw:
    """Run one complete locked episode and preserve its first registered boundary."""

    host, policy = ServiceRelayHost(build_scenario_tape(spec)), LockedPolicy(model, predictor, calibration)
    boundary = None
    reviews = terms = 0
    calibration_rows: list[dict[str, object]] = []
    hazard_rows: list[tuple[np.ndarray, int, HazardCellKey]] = []
    evaluation_cell_keys: list[HazardCellKey] = []
    while not host.done:
        target = _boundary_eligible(host) if host.initialized and boundary is None else None
        predecision = host.clone() if target is not None else None
        pending_hazard: list[tuple[int, np.ndarray, HazardCellKey]] = []
        if (panel == "hazard" or method == "RATE-MATCHED-HAZARD-CRTO") and host.initialized:
            for agent, kind in enumerate(host.review_kinds()):
                if kind is DecisionKind.DISCRETIONARY:
                    feature, key = _hazard_feature(host, agent)
                    pending_hazard.append((agent, feature, key))
        elapsed_before = tuple(
            host.state.primitive_time - int(policy.anchor_time[agent]) for agent in range(AGENT_COUNT)
        )
        decisions, packets = policy.decisions(
            host, disable_residual=method == "Q-ONLY-CRTO",
            forced_renewal_only=method == "FORCED-RENEWAL-ONLY",
            hazard=hazard if method == "RATE-MATCHED-HAZARD-CRTO" else None,
        )
        reviews += sum(row.kind is DecisionKind.DISCRETIONARY for row in decisions)
        terms += sum(row.kind is DecisionKind.DISCRETIONARY and row.changed for row in decisions)
        decisions_by_agent = {row.agent: row for row in decisions}
        for agent, feature, key in pending_hazard:
            decision = decisions_by_agent[agent]
            if decision.kind is not DecisionKind.DISCRETIONARY:
                raise RuntimeError("hazard row lost its legal discretionary decision")
            if panel == "hazard":
                hazard_rows.append((feature, int(decision.changed), key))
            else:
                evaluation_cell_keys.append(key)
        if target is not None and panel in ("scored", "donor"):
            assert predecision is not None
            boundary = _boundary_snapshot(seed=seed, panel=panel, host=predecision, target=target,
                                          packets=packets, decisions=decisions)
        for agent, bundle in enumerate(packets):
            elapsed = elapsed_before[agent]
            if panel == "scored" and method == "CRTO" and elapsed in (4, 8, 12, 16):
                residual = bundle.whitened.reshape(8).numpy()
                calibration_rows.append({
                    "seed": seed, "regime": spec.regime.value,
                    "episode_index": spec.episode_index, "environment_slot": agent,
                    "horizon": elapsed, "whitened": residual.tolist(),
                    "pit": calibration.cdf(bundle.whitened).reshape(8).numpy().tolist(),
                })
        host.advance(decisions)
    return _compact_episode(
        host, method=method, reviews=reviews, terms=terms, boundary=boundary,
        calibration_rows=calibration_rows, hazard_rows=hazard_rows,
        evaluation_cell_keys=evaluation_cell_keys,
    )


def hazard_development(
    *, seed: int, model: RecurrentOptionActorCritic, predictor: FrozenPredictor,
    calibration: CalibrationTable,
) -> dict[str, object]:
    features, labels, keys, episodes = [], [], [], []
    for regime in REGIMES:
        for spec in panel_specs(seed, "hazard", regime, 64):
            raw = run_episode(seed=seed, method="CRTO", spec=spec, model=model,
                              predictor=predictor, calibration=calibration, panel="hazard")
            episodes.append(raw)
            for feature, label, key in raw.hazard_rows:
                features.append(feature); labels.append(label); keys.append(key)
    fit = fit_rate_matched_hazard(np.asarray(features), np.asarray(labels), keys,
                                  continuous_columns=(8, 9, 10, 11))
    return {"steps": 4 * 64 * HORIZON, "fit": fit, "feature_rows": np.asarray(features),
            "labels": np.asarray(labels), "cell_keys": tuple(keys), "episodes": tuple(episodes)}


def scored_evaluation(
    *, seed: int, models: Mapping[str, RecurrentOptionActorCritic], predictor: FrozenPredictor,
    calibration: CalibrationTable, hazard: Mapping[str, object],
) -> dict[str, object]:
    rows = []
    for regime in REGIMES:
        specs = panel_specs(seed, "scored", regime, 64)
        for method in ("CRTO", "FULL-HISTORY-AUX-TERM"):
            rows.extend(run_episode(seed=seed, method=method, spec=spec, model=models[method],
                                    predictor=predictor, calibration=calibration, panel="scored")
                        for spec in specs)
    return {"steps": 2 * 4 * 64 * HORIZON, "episodes": tuple(rows)}


def complete_rollout_cuts(
    *, seed: int, model: RecurrentOptionActorCritic, predictor: FrozenPredictor,
    calibration: CalibrationTable, hazard: Mapping[str, object],
) -> dict[str, object]:
    fit = hazard["fit"]
    if not isinstance(fit, HazardControlFit):
        raise TypeError("hazard phase lacks its frozen HazardControlFit")
    rows = []
    evaluation_cell_keys: list[HazardCellKey] = []
    for regime in REGIMES:
        specs = panel_specs(seed, "scored", regime, 64)  # exact tapes shared with main methods
        for method in CUT_METHODS:
            method_rows = tuple(
                run_episode(seed=seed, method=method, spec=spec, model=model,
                            predictor=predictor, calibration=calibration, panel="scored", hazard=fit)
                for spec in specs
            )
            rows.extend(method_rows)
            if method == "RATE-MATCHED-HAZARD-CRTO":
                evaluation_cell_keys.extend(
                    key for row in method_rows for key in row.evaluation_cell_keys
                )
    return {"steps": 3 * 4 * 64 * HORIZON, "episodes": tuple(rows),
            "evaluation_cell_keys": tuple(evaluation_cell_keys)}


def donor_panel(
    *, seed: int, model: RecurrentOptionActorCritic, predictor: FrozenPredictor,
    calibration: CalibrationTable,
) -> dict[str, object]:
    rows = tuple(run_episode(seed=seed, method="CRTO", spec=spec, model=model,
                             predictor=predictor, calibration=calibration, panel="donor")
                 for regime in REGIMES for spec in panel_specs(seed, "donor", regime, 256))
    return {"steps": 4 * 256 * HORIZON, "episodes": rows}


def deranged_replays(
    *, seed: int, model: RecurrentOptionActorCritic, predictor: FrozenPredictor,
    calibration: CalibrationTable, scored: Mapping[str, object], donor: Mapping[str, object],
    persist_plan: Callable[[Mapping[str, object]], Mapping[str, object]],
) -> dict[str, object]:
    snapshots = {
        row.boundary.record.record_id: row.boundary
        for row in (*scored["episodes"], *donor["episodes"])
        if isinstance(row, EpisodeRaw) and row.method == "CRTO" and row.boundary is not None
    }
    plan = build_derangement_plan([snapshot.record for snapshot in snapshots.values()])
    if not callable(persist_plan):
        raise TypeError("deranged replay requires a durable plan-persistence callback")
    plan_payload = {
        "seed": seed,
        "panel_namespace": PANEL_ROOT_NAMESPACE,
        "encoding_revision": "CRTO-B1-SCIENCE-20260812-04",
        "plan": asdict(plan),
    }
    persistence_receipt = persist_plan(plan_payload)
    if not isinstance(persistence_receipt, Mapping) or not bool(persistence_receipt.get("durable", False)):
        raise RuntimeError("derangement plan was not durably persisted before branch execution")
    rows = []
    assignments = []
    deranged_actions: dict[str, str] = {}
    for assignment in plan.assignments:
        if assignment.seed != seed or assignment.recipient_panel != "scored" or not assignment.supported:
            continue
        recipient, donor_snapshot = snapshots[assignment.recipient_record_id], snapshots[assignment.donor_record_id]
        host, policy = recipient.host.clone(), LockedPolicy(model, predictor, calibration)
        # Replay to the boundary reconstructs the checkpoint's recurrent state; the
        # saved simulator remains the branch start and receives only the donor row.
        replay = ServiceRelayHost(build_scenario_tape(host.tape.spec))
        while replay.state.primitive_time < host.state.primitive_time:
            decisions, _ = policy.decisions(replay); replay.advance(decisions)
        _assert_same_predecision(replay, host, context="derangement replay")
        override = torch.as_tensor(donor_snapshot.residual_tensor[donor_snapshot.target_agent], dtype=torch.float32)
        first_boundary_decision = True
        while not host.done:
            decisions, _ = policy.decisions(
                host,
                packet_override={recipient.target_agent: override} if first_boundary_decision else None,
            )
            if first_boundary_decision:
                selected = decisions[recipient.target_agent]
                deranged_actions[recipient.record.record_id] = (
                    "KEEP" if not selected.changed else selected.selected_option.label
                )
            first_boundary_decision = False
            host.advance(decisions)
        rows.append(_compact_episode(
            host, method="DERANGED-RESIDUAL-CRTO", reviews=0, terms=0,
            prefix_reward_sum=recipient.prefix_reward_sum,
        ))
        assignments.append(asdict(assignment))
    # Unsupported scored recipients still consume their registered complete
    # replay with aligned packet; this preserves the immutable category ledger.
    supported_ids = {item["recipient_record_id"] for item in assignments}
    for row in scored["episodes"]:
        record_id = row.boundary.record.record_id if isinstance(row, EpisodeRaw) and row.boundary else None
        if isinstance(row, EpisodeRaw) and row.method == "CRTO" and record_id not in supported_ids:
            rows.append(run_episode(seed=seed, method="DERANGED-RESIDUAL-CRTO",
                                    spec=row.scenario, model=model, predictor=predictor,
                                    calibration=calibration, panel="scored"))
    return {"steps": 4 * 64 * HORIZON, "plan": plan, "assignments": tuple(assignments),
            "plan_persistence_receipt": dict(persistence_receipt),
            "deranged_actions": deranged_actions, "episodes": tuple(rows)}


def _bind_shadow_anchors(
    policy: LockedPolicy, host: ServiceRelayHost, decisions: Sequence[DecisionRecord],
) -> None:
    """Apply CRTO's resolved anchor events to a non-acting shadow backbone."""

    for row in decisions:
        if row.reanchored:
            policy.anchor_history[row.agent] = torch.stack(policy.histories[row.agent])
            policy.anchor_option[row.agent] = int(row.selected_option)
            policy.anchor_k[row.agent] = host.tape.k_at(host.state.primitive_time)
            policy.anchor_time[row.agent] = host.state.primitive_time


def _validate_audit_boundary(boundary: BoundarySnapshot) -> None:
    host, record = boundary.host, boundary.record
    time = host.state.primitive_time
    if host.done or time + 16 > HORIZON:
        raise ValueError("audit boundary must admit exactly sixteen future primitive steps")
    if boundary.target_agent != record.target_agent_slot or not 0 <= boundary.target_agent < AGENT_COUNT:
        raise ValueError("audit boundary target slot is inconsistent")
    if len(boundary.aligned_decisions) != AGENT_COUNT:
        raise ValueError("audit boundary must preserve four simultaneous aligned decisions")
    if host.review_kinds()[boundary.target_agent] is not DecisionKind.DISCRETIONARY:
        raise ValueError("audit target is not at a legal discretionary review")
    if len(host.audit_action_set(boundary.target_agent)) < 2:
        raise ValueError("audit target lacks a different legal replacement")
    onset = host.tape.spec.event_onset
    if not onset + 4 <= time <= onset + 20 or abs(time - 128) <= 8:
        raise ValueError("audit boundary is outside its frozen event window")
    if boundary.residual_tensor.shape != (AGENT_COUNT, 52) or boundary.cholesky.shape != (8, 8):
        raise ValueError("audit boundary packet tensor or Cholesky shape drifted")
    if len(boundary.joint_option_counts) != 7 or sum(boundary.joint_option_counts) != AGENT_COUNT:
        raise ValueError("audit boundary joint-option counts are malformed")
    if len(boundary.location_counts) != 3 or sum(boundary.location_counts) != AGENT_COUNT:
        raise ValueError("audit boundary location counts are malformed")
    if (
        record.regime != host.tape.spec.regime.value
        or record.episode_index != host.tape.spec.episode_index
        or record.current_k != host.tape.k_at(time)
        or record.age != int(host.state.option_ages[boundary.target_agent])
        or record.current_option != Option(int(host.state.options[boundary.target_agent])).label
    ):
        raise ValueError("audit boundary record does not describe its cloned predecision host")


def _shadow_termination_masses(
    boundary: BoundarySnapshot,
    models: Mapping[str, RecurrentOptionActorCritic],
    predictor: FrozenPredictor,
    calibration: CalibrationTable,
) -> tuple[float, float]:
    """Score both checkpoints on one identical aligned-CRTO history.

    Only the acting replay advances the simulator.  Each shadow consumes the
    same deployable predecision observations and CRTO-resolved current-option
    sequence, maintains its own recurrent state, and uses its own adapter packet.
    """

    _validate_audit_boundary(boundary)
    if set(models) != {"CRTO", "FULL-HISTORY-AUX-TERM"}:
        raise ValueError("shortcut shadow scoring requires both frozen learned checkpoints")
    crto_model, full_model = models["CRTO"], models["FULL-HISTORY-AUX-TERM"]
    replay = ServiceRelayHost(build_scenario_tape(boundary.host.tape.spec))
    acting = LockedPolicy(crto_model, predictor, calibration)
    shadows = {
        "CRTO": LockedPolicy(crto_model, predictor, calibration),
        "FULL-HISTORY-AUX-TERM": LockedPolicy(full_model, predictor, calibration),
    }
    target_time = boundary.host.state.primitive_time
    while replay.state.primitive_time < target_time:
        for shadow in shadows.values():
            shadow.predecision(replay)
        decisions, _ = acting.decisions(replay)
        for shadow in shadows.values():
            _bind_shadow_anchors(shadow, replay, decisions)
        replay.advance(decisions)
    if replay.state.primitive_time != target_time:
        raise RuntimeError("shadow replay did not reach the registered audit boundary")
    _assert_same_predecision(replay, boundary.host, context="shadow replay")

    target = boundary.target_agent
    current = int(replay.state.options[target])
    legal_replacements = tuple(
        int(option) for option in replay.audit_action_set(target) if option is not None
    )
    if not legal_replacements:
        raise RuntimeError("audit shadow boundary has no legal replacement")
    masses: dict[str, float] = {}
    for method, shadow in shadows.items():
        step, _ = shadow.predecision(replay)
        relative = tuple(
            float(step.q[target, option] - step.q[target, current]
                  - (0.05 + replay.tape.spec.replanning_cost)
                  + step.residual_contribution[target, option])
            for option in legal_replacements
        )
        masses[method] = termination_mass(relative)
    return masses["CRTO"], masses["FULL-HISTORY-AUX-TERM"]


def audit_enumeration(
    *, seed: int, models: Mapping[str, RecurrentOptionActorCritic], predictor: FrozenPredictor,
    calibration: CalibrationTable, scored: Mapping[str, object], deranged: Mapping[str, object],
) -> dict[str, object]:
    if set(models) != {"CRTO", "FULL-HISTORY-AUX-TERM"}:
        raise ValueError("audit enumeration requires both frozen learned checkpoints")
    model = models["CRTO"]
    deranged_action = dict(deranged["deranged_actions"])
    states, steps = [], 0
    for row in scored["episodes"]:
        if not isinstance(row, EpisodeRaw) or row.method != "CRTO" or row.boundary is None:
            continue
        boundary = row.boundary
        _validate_audit_boundary(boundary)
        policy = LockedPolicy(model, predictor, calibration)
        replay = ServiceRelayHost(build_scenario_tape(boundary.host.tape.spec))
        while replay.state.primitive_time < boundary.host.state.primitive_time:
            decisions, _ = policy.decisions(replay); replay.advance(decisions)
        # Consume the boundary observation exactly once so every cloned audit
        # continuation starts with the same aligned recurrent history.
        policy.predecision(replay)
        action_returns = {}
        for action in boundary.host.audit_action_set(boundary.target_agent):
            continuation_policy = policy.clone()
            first_continuation = True
            def continuation(branch: ServiceRelayHost, local=continuation_policy) -> tuple[DecisionRecord, ...]:
                nonlocal first_continuation
                if first_continuation:
                    # The enumerated first action was applied by the host. Bind
                    # any resulting new commitments to the already-consumed
                    # boundary history before advancing the frozen policy.
                    for agent in range(AGENT_COUNT):
                        anchor_time = int(branch.state.anchor_times[agent])
                        if anchor_time != int(local.anchor_time[agent]):
                            local.anchor_history[agent] = torch.stack(local.histories[agent])
                            local.anchor_option[agent] = int(branch.state.options[agent])
                            local.anchor_k[agent] = branch.tape.k_at(anchor_time)
                            local.anchor_time[agent] = anchor_time
                    first_continuation = False
                return local.decisions(branch)[0]
            value, _ = common_future_audit_rollout(
                boundary.host, target_agent=boundary.target_agent, audit_action=action,
                aligned_decisions=boundary.aligned_decisions, continuation=continuation,
            )
            label = "KEEP" if action is None else action.label
            action_returns[label] = value; steps += 16
        d_action = deranged_action.get(boundary.record.record_id) or boundary.aligned_action
        derangement_supported = boundary.record.record_id in deranged_action
        diagnostic = audit_advantage_and_regret(
            action_returns, aligned_action=boundary.aligned_action, deranged_action=d_action,
            printed_option_order=OPTIONS,
        )
        p_term_crto, p_term_full = _shadow_termination_masses(
            boundary, models, predictor, calibration,
        )
        states.append({"record_id": boundary.record.record_id, "boundary": asdict(boundary.record),
                       "action_returns": action_returns,
                       "derangement_supported": derangement_supported,
                       "p_term_crto": p_term_crto, "p_term_full": p_term_full,
                       **diagnostic})
    return {"steps": steps, "states": tuple(states)}


class EvaluationBridge:
    """Seed-bound concrete API consumed by the execution coordinator."""

    def __init__(self, *, seed: int, config: object) -> None:
        self.seed = int(seed)
        self.config = config
        if self.seed not in tuple(getattr(config, "algorithm_seeds", ())):
            raise ValueError("evaluation bridge seed is outside the supplied registered configuration")

    @property
    def interface_status(self) -> dict[str, object]:
        return {
            "hazard_switch_feature_encoding_id": HAZARD_SWITCH_FEATURE_ENCODING_ID,
            "hazard_available": True,
            "missing_authoritative_input": None,
        }

    def hazard_development(self, **kwargs: object) -> dict[str, object]:
        return hazard_development(seed=self.seed, **kwargs)  # type: ignore[arg-type]

    def scored_evaluation(self, **kwargs: object) -> dict[str, object]:
        return scored_evaluation(seed=self.seed, **kwargs)  # type: ignore[arg-type]

    def complete_rollout_cuts(self, **kwargs: object) -> dict[str, object]:
        return complete_rollout_cuts(seed=self.seed, **kwargs)  # type: ignore[arg-type]

    def donor_panel(self, **kwargs: object) -> dict[str, object]:
        return donor_panel(seed=self.seed, **kwargs)  # type: ignore[arg-type]

    def deranged_replays(self, **kwargs: object) -> dict[str, object]:
        return deranged_replays(seed=self.seed, **kwargs)  # type: ignore[arg-type]

    def audit_enumeration(self, **kwargs: object) -> dict[str, object]:
        return audit_enumeration(seed=self.seed, **kwargs)  # type: ignore[arg-type]

    @staticmethod
    def raw_seed_records(
        *, hazard: Mapping[str, object], scored: Mapping[str, object],
        cuts: Mapping[str, object], donor: Mapping[str, object],
        deranged: Mapping[str, object], audit: Mapping[str, object],
    ) -> dict[str, object]:
        """Return the lossless seed-local inputs for the later pooled finalizer."""

        return {
            "hazard_feature_rows": hazard["feature_rows"], "hazard_labels": hazard["labels"],
            "hazard_cell_keys": hazard["cell_keys"], "hazard_fit": hazard["fit"],
            "hazard_evaluation_cell_keys": cuts["evaluation_cell_keys"],
            "scored_episodes": scored["episodes"], "cut_episodes": cuts["episodes"],
            "donor_episodes": donor["episodes"], "derangement_plan": deranged["plan"],
            "deranged_episodes": deranged["episodes"], "audit_states": audit["states"],
        }


def _as_mapping(value: object, *, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return value


def _as_episode_rows(value: object, *, name: str) -> tuple[EpisodeRaw, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be an episode sequence")
    rows = tuple(value)
    if any(not isinstance(row, EpisodeRaw) for row in rows):
        raise ValueError(f"{name} contains a non-EpisodeRaw value")
    return rows  # type: ignore[return-value]


def _episode_outcome(seed: int, row: EpisodeRaw) -> EpisodeOutcome:
    return EpisodeOutcome(
        row.method, seed, row.scenario.regime.value, row.scenario_id,
        float(row.normalized_score), float(row.failure),
    )


def _lower_triangle(vector: np.ndarray) -> np.ndarray:
    source = np.asarray(vector, dtype=np.float64)
    if source.shape == (8, 8):
        if np.any(np.triu(source, 1) != 0.0):
            raise ValueError("boundary Cholesky matrix is not lower triangular")
        return source.copy()
    values = source.reshape(-1)
    if values.size != 36:
        raise ValueError("boundary raw packet must retain all 36 Cholesky coordinates")
    result = np.zeros((8, 8), dtype=np.float64)
    result[np.tril_indices(8)] = values
    return result


def _balance_features(snapshot: BoundarySnapshot) -> tuple[tuple[float, ...], tuple[float, ...]]:
    packet = np.asarray(snapshot.residual_tensor[snapshot.target_agent], dtype=np.float64).reshape(52)
    record = snapshot.record
    return donor_balance_feature_vectors(
        residual_r=packet[:8], residual_p=packet[8:16], residual_a=packet[16:24],
        cholesky=_lower_triangle(snapshot.cholesky),
        joint_option_counts=snapshot.joint_option_counts,
        location_counts=snapshot.location_counts,
        current_option=record.current_option, current_k=record.current_k, age=record.age,
        legal_mask_bits=record.legal_mask_bits, event_class=record.event_class,
        phase=record.phase, visible_cue=record.visible_cue, cost=record.cost,
        regime=record.regime,
    )


def _descriptive_episode_metrics(
    by_seed: Mapping[int, tuple[EpisodeRaw, ...]],
) -> dict[str, object]:
    grouped: dict[tuple[str, str], list[EpisodeRaw]] = {}
    for rows in by_seed.values():
        for row in rows:
            grouped.setdefault((row.method, row.scenario.regime.value), []).append(row)
    result: dict[str, object] = {}
    for (method, regime), episodes in sorted(grouped.items()):
        key = f"{method}|{regime}"
        result[key] = {
            "episodes": len(episodes),
            "mean_normalized_return": float(np.mean([row.normalized_score for row in episodes])),
            "failure_rate": float(np.mean([row.failure for row in episodes])),
            "delivery_fraction": float(np.mean([row.delivery_fraction for row in episodes])),
            "mean_overflow": float(np.mean([row.total_overflow for row in episodes])),
            "mean_energy": float(np.mean([row.total_energy_spent for row in episodes])),
            "mean_renewals": float(np.mean([row.renewal_count for row in episodes])),
            "mean_replans": float(np.mean([row.replan_count for row in episodes])),
            "mean_renewal_replan_cost": float(np.mean([row.total_decision_charge for row in episodes])),
            "mean_simultaneous_triggers": float(np.mean([row.simultaneous_trigger_count for row in episodes])),
            "mean_option_collisions": float(np.mean([row.option_collisions for row in episodes])),
        }
    return result


def finalize(
    per_seed_raw: Mapping[int, Mapping[str, object]], resources: Mapping[str, object],
) -> Mapping[str, object]:
    """Pool the eight raw seed panels into the frozen CRTO analysis packet.

    A scientific gate may fail while its section remains complete.  In contrast,
    absent raw inputs, unbuilt shadow scores, or missing evaluation-cell support
    evidence force ``required_sections_complete`` false.
    """

    expected = tuple(int(seed) for seed in ALGORITHM_SEEDS)
    if tuple(sorted(per_seed_raw)) != expected:
        raise ValueError("CRTO finalization requires exactly the registered eight integer seeds")
    if not isinstance(resources, Mapping):
        raise TypeError("resources must be a completed ledger mapping")

    anomalies: list[str] = []
    completeness: dict[str, bool] = {}
    scored_by_seed: dict[int, tuple[EpisodeRaw, ...]] = {}
    cuts_by_seed: dict[int, tuple[EpisodeRaw, ...]] = {}
    donor_by_seed: dict[int, tuple[EpisodeRaw, ...]] = {}
    deranged_by_seed: dict[int, tuple[EpisodeRaw, ...]] = {}
    audit_raw_by_seed: dict[int, tuple[Mapping[str, object], ...]] = {}
    hazard_by_seed: dict[int, Mapping[str, object]] = {}
    deranged_actions: dict[str, str] = {}
    probe_by_seed: dict[int, Mapping[str, float]] = {}
    source_anomalies: list[str] = []

    for seed in expected:
        row = _as_mapping(per_seed_raw[seed], name=f"seed {seed}")
        if row.get("seed") != seed:
            raise ValueError(f"seed identity mismatch for {seed}")
        try:
            predictor = _as_mapping(row["predictor"], name=f"seed {seed} predictor")
            probe = _as_mapping(predictor["probe"], name=f"seed {seed} probe")
            probe_by_seed[seed] = {"normalized_mse": float(probe["normalized_mse"]),
                                   "sign_accuracy": float(probe["sign_accuracy"])}
            hazard_by_seed[seed] = _as_mapping(row["hazard_development"], name=f"seed {seed} hazard")
            scored = _as_mapping(row["scored_evaluation"], name=f"seed {seed} scored")
            mechanism = _as_mapping(row["mechanism_cuts"], name=f"seed {seed} mechanisms")
            cuts = _as_mapping(mechanism["complete_rollout"], name=f"seed {seed} cuts")
            deranged = _as_mapping(mechanism["deranged"], name=f"seed {seed} deranged")
            donor = _as_mapping(row["donor_only"], name=f"seed {seed} donor")
            audit = _as_mapping(row["audit"], name=f"seed {seed} audit")
            scored_by_seed[seed] = _as_episode_rows(scored["episodes"], name=f"seed {seed} scored episodes")
            cuts_by_seed[seed] = _as_episode_rows(cuts["episodes"], name=f"seed {seed} cut episodes")
            donor_by_seed[seed] = _as_episode_rows(donor["episodes"], name=f"seed {seed} donor episodes")
            deranged_by_seed[seed] = _as_episode_rows(deranged["episodes"], name=f"seed {seed} deranged episodes")
            action_map = deranged.get("deranged_actions", {})
            if not isinstance(action_map, Mapping):
                raise ValueError("deranged_actions must be a mapping")
            deranged_actions.update({str(key): str(value) for key, value in action_map.items()})
            states = audit["states"]
            if not isinstance(states, Sequence) or isinstance(states, (str, bytes)):
                raise ValueError("audit states must be a sequence")
            audit_raw_by_seed[seed] = tuple(_as_mapping(state, name="audit state") for state in states)
            raw_anomalies = row.get("anomalies", ())
            if isinstance(raw_anomalies, Sequence) and not isinstance(raw_anomalies, (str, bytes)):
                source_anomalies.extend(str(item) for item in raw_anomalies)
        except (KeyError, TypeError, ValueError) as error:
            anomalies.append(f"seed {seed} raw extraction: {error}")
    completeness["all_seed_raw_sections"] = len(scored_by_seed) == len(expected)

    main_outcomes = [_episode_outcome(seed, row) for seed, rows in scored_by_seed.items() for row in rows]
    cut_outcomes = [_episode_outcome(seed, row) for seed, rows in cuts_by_seed.items() for row in rows]
    deranged_outcomes = [_episode_outcome(seed, row) for seed, rows in deranged_by_seed.items() for row in rows]

    try:
        primary = primary_estimands(main_outcomes)
        completeness["primary_estimands"] = True
    except (KeyError, TypeError, ValueError) as error:
        primary = {"built": False, "reason": str(error)}
        completeness["primary_estimands"] = False
        anomalies.append(f"primary analysis: {error}")

    # Rebuild the single canonical cross-seed partition from raw snapshots.
    snapshots: dict[str, BoundarySnapshot] = {}
    for rows in (*scored_by_seed.values(), *donor_by_seed.values()):
        for row in rows:
            if row.method == "CRTO" and row.boundary is not None:
                snapshots[row.boundary.record.record_id] = row.boundary
    try:
        pooled_plan = build_derangement_plan([snapshot.record for snapshot in snapshots.values()])
        completeness["derangement_partition"] = True
    except (TypeError, ValueError) as error:
        pooled_plan = None
        completeness["derangement_partition"] = False
        anomalies.append(f"derangement partition: {error}")

    supported_scenarios: set[tuple[int, str, str]] = set()
    balance_rows: list[BalanceRow] = []
    if pooled_plan is not None:
        for assignment in pooled_plan.assignments:
            if not assignment.supported or assignment.recipient_panel != "scored":
                continue
            recipient = snapshots.get(assignment.recipient_record_id)
            donor = snapshots.get(assignment.donor_record_id)
            if recipient is None or donor is None:
                anomalies.append(f"derangement assignment lacks snapshot {assignment.recipient_record_id}")
                continue
            supported_scenarios.add((assignment.seed, recipient.record.regime, str(recipient.record.episode_index)))
            try:
                recipient_cont, recipient_frozen = _balance_features(recipient)
                donor_cont, donor_frozen = _balance_features(donor)
                pair = assignment.recipient_record_id
                balance_rows.extend((
                    BalanceRow(pair, assignment.seed, recipient.record.regime, 0,
                               recipient_cont, recipient_frozen),
                    BalanceRow(pair, assignment.seed, recipient.record.regime, 1,
                               donor_cont, donor_frozen),
                ))
            except (TypeError, ValueError) as error:
                anomalies.append(f"balance feature {assignment.recipient_record_id}: {error}")
    try:
        donor_balance = donor_recipient_balance_diagnostic(balance_rows)
        # An empty supported population is a complete support result, not a
        # missing engineering section, once the full partition was consumed.
        completeness["donor_balance"] = pooled_plan is not None
    except (TypeError, ValueError) as error:
        donor_balance = {"available": False, "pass": False, "failure_reasons": [str(error)]}
        completeness["donor_balance"] = False
        anomalies.append(f"donor balance: {error}")

    align_outcomes = [
        row for row in main_outcomes + deranged_outcomes
        if row.method in ("CRTO", "DERANGED-RESIDUAL-CRTO")
        and (row.seed, row.regime, row.scenario_id) in supported_scenarios
    ]
    mechanisms: dict[str, object] = {}
    mechanism_specs = (
        ("Delta_align", align_outcomes, "CRTO", "DERANGED-RESIDUAL-CRTO", 0.01),
        ("Delta_Q", main_outcomes + cut_outcomes, "CRTO", "Q-ONLY-CRTO", 0.005),
        ("Delta_rate", main_outcomes + cut_outcomes, "CRTO", "RATE-MATCHED-HAZARD-CRTO", 0.0),
    )
    for label, rows, left, right, margin in mechanism_specs:
        if label == "Delta_align" and pooled_plan is not None:
            paired_cells = {
                (row.seed, row.regime)
                for row in rows
                if row.method == "CRTO" and any(
                    other.method == "DERANGED-RESIDUAL-CRTO"
                    and (other.seed, other.regime, other.scenario_id)
                    == (row.seed, row.regime, row.scenario_id)
                    for other in rows
                )
            }
            required_cells = {
                (seed, regime) for seed in expected for regime in REGIMES[1:]
            }
            if not required_cells.issubset(paired_cells):
                mechanisms[label] = {
                    "label": label, "available": False, "pass": False,
                    "reason": "frozen exact strata do not support every seed/target-regime cell",
                    "supported_seed_regime_cells": sorted(paired_cells),
                }
                completeness[label] = True
                continue
        try:
            mechanisms[label] = mechanism_estimand(
                rows, left=left, right=right, label=label, margin=margin,
            )
            completeness[label] = True
        except (KeyError, TypeError, ValueError) as error:
            mechanisms[label] = {"built": False, "reason": str(error), "pass": False}
            completeness[label] = False
            anomalies.append(f"{label}: {error}")

    calibration_rows: list[CalibrationObservation] = []
    for seed, rows in scored_by_seed.items():
        for row in rows:
            if row.method != "CRTO":
                continue
            for item in row.calibration_rows:
                calibration_rows.append(CalibrationObservation(
                    seed, row.scenario.regime.value, int(item["horizon"]),
                    tuple(float(value) for value in item["whitened"]),
                    tuple(float(value) for value in item["pit"]),
                ))
    try:
        calibration_report = calibration_diagnostic(calibration_rows)
        observed_calibration_regimes = {row.regime for row in calibration_rows}
        completeness["calibration"] = all(
            len(scored_by_seed.get(seed, ())) == 2 * 4 * 64 for seed in expected
        )
    except (TypeError, ValueError) as error:
        calibration_report = {"available": False, "pass": False, "failure_reasons": [str(error)]}
        completeness["calibration"] = False
        anomalies.append(f"calibration: {error}")

    audit_states: list[AuditState] = []
    shadow_rows: list[ShadowScore] = []
    shadow_fields_present = True
    for seed, raw_states in audit_raw_by_seed.items():
        for item in raw_states:
            boundary = _as_mapping(item.get("boundary"), name="audit boundary")
            record_id = str(item.get("record_id"))
            snapshot = snapshots.get(record_id)
            s_adv = float(np.mean(snapshot.residual_tensor[snapshot.target_agent, 16:24])) if snapshot else math.nan
            if snapshot is None:
                anomalies.append(f"audit state lacks scored boundary snapshot {record_id}")
                continue
            aligned_action = snapshot.aligned_action
            deranged_action = deranged_actions.get(record_id, aligned_action)
            audit_states.append(AuditState(
                seed, str(boundary["regime"]), int(boundary["episode_index"]),
                str(boundary["event_class"]), float(boundary["cost"]), s_adv,
                float(item["A16_replan"]), aligned_action, deranged_action,
                float(item["aligned_regret16"]), float(item["deranged_regret16"]),
                bool(item.get("derangement_supported", False)),
            ))
            if "p_term_crto" in item and "p_term_full" in item:
                shadow_rows.append(ShadowScore(
                    seed, str(boundary["regime"]), str(boundary["event_class"]),
                    float(boundary["cost"]), float(item["A16_replan"]),
                    float(item["p_term_crto"]), float(item["p_term_full"]),
                ))
            else:
                shadow_fields_present = False
    try:
        audit_report = audit_mechanism_diagnostics(audit_states)
        trend_report = adverse_residual_trend(audit_states)
        complete_audit_population = all(
            "states" in _as_mapping(per_seed_raw[seed].get("audit"), name=f"seed {seed} audit")
            for seed in expected
        )
        completeness["causal_audit"] = complete_audit_population
        completeness["adverse_trend"] = complete_audit_population
    except (KeyError, TypeError, ValueError) as error:
        audit_report = {"available": False, "pass": False, "failure_reasons": [str(error)]}
        trend_report = {"available": False, "pass": False, "failure_reasons": [str(error)]}
        completeness["causal_audit"] = completeness["adverse_trend"] = False
        anomalies.append(f"causal audit: {error}")
    try:
        shortcut_report = shortcut_shadow_diagnostic(shadow_rows)
        completeness["shortcut_shadow_scores"] = shadow_fields_present
    except (TypeError, ValueError) as error:
        shortcut_report = {"available": False, "pass": False, "failure_reasons": [str(error)]}
        completeness["shortcut_shadow_scores"] = False
        anomalies.append(f"shortcut shadows: {error}")

    rate_rows: list[RateCount] = []
    for seed in expected:
        for row in (*scored_by_seed.get(seed, ()), *cuts_by_seed.get(seed, ())):
            if row.method not in ("CRTO", "RATE-MATCHED-HAZARD-CRTO"):
                continue
            spec = row.scenario
            rate_rows.append(RateCount(
                row.method, seed, spec.regime.value, spec.event.value, spec.replanning_cost,
                1, row.legal_discretionary_reviews, row.changed_option_terminations,
            ))
    try:
        rate_report = evaluation_rate_balance(rate_rows)
        completeness["evaluation_rate_balance"] = all(
            sum(
                row.method == method and row.scenario.regime.value == regime
                for row in (*scored_by_seed.get(seed, ()), *cuts_by_seed.get(seed, ()))
            ) == 64
            for seed in expected
            for method in ("CRTO", "RATE-MATCHED-HAZARD-CRTO")
            for regime in REGIMES
        )
    except (TypeError, ValueError) as error:
        rate_report = {"available": False, "pass": False, "failure_reasons": [str(error)]}
        completeness["evaluation_rate_balance"] = False
        anomalies.append(f"evaluation rate balance: {error}")

    hazard_converged = all(
        isinstance(section.get("fit"), HazardControlFit) and section["fit"].base.converged
        for section in hazard_by_seed.values()
    ) and len(hazard_by_seed) == 8
    hazard_support_sections: dict[str, object] = {}
    hazard_support_evidence = True
    for seed, section in hazard_by_seed.items():
        fit = section.get("fit")
        cut_section = per_seed_raw[seed].get("mechanism_cuts")
        complete_cut = cut_section.get("complete_rollout") if isinstance(cut_section, Mapping) else None
        encountered = complete_cut.get("evaluation_cell_keys") if isinstance(complete_cut, Mapping) else None
        if isinstance(fit, HazardControlFit) and isinstance(encountered, Sequence):
            hazard_support_sections[str(seed)] = hazard_target_support(fit, encountered)  # type: ignore[arg-type]
        else:
            hazard_support_evidence = False
    hazard_support_pass = hazard_support_evidence and all(
        bool(section.get("available", False))
        for section in hazard_support_sections.values() if isinstance(section, Mapping)
    ) and len(hazard_support_sections) == 8
    completeness["hazard_evaluation_support"] = hazard_support_evidence and len(hazard_support_sections) == 8
    completeness["hazard_switch_feature_encoding"] = (
        HAZARD_SWITCH_FEATURE_ENCODING_ID
        == "CRTO-B1-v4-FULL-ONEHOT-REGIME-DIRECTION-PHASE"
    )
    delta_rate_available = (
        hazard_converged and hazard_support_pass and bool(rate_report.get("pass", False))
    )
    delta_rate_rows = main_outcomes + cut_outcomes
    try:
        mechanisms["Delta_rate"] = mechanism_estimand(
            delta_rate_rows, left="CRTO", right="RATE-MATCHED-HAZARD-CRTO",
            label="Delta_rate", margin=0.0, available=delta_rate_available,
        )
        mechanisms["Delta_rate"]["availability_prerequisites"] = {
            "hazard_fit_converged": hazard_converged,
            "all_encountered_target_cells_supported": hazard_support_pass,
            "scored_evaluation_rate_balance": bool(rate_report.get("pass", False)),
        }
        if not delta_rate_available:
            mechanisms["Delta_rate"]["unavailable_reason"] = (
                "hazard convergence, target-cell support, and scored rate balance must all pass"
            )
        completeness["Delta_rate"] = True
    except (KeyError, TypeError, ValueError) as error:
        mechanisms["Delta_rate"] = {"built": False, "available": False, "pass": False,
                                    "reason": str(error)}
        completeness["Delta_rate"] = False
        anomalies.append(f"Delta_rate availability binding: {error}")

    action_counts: dict[str, dict[str, int]] = {
        regime: {"legal_reviews": 0, "keep": 0, "changed_option": 0} for regime in REGIMES[1:]
    }
    audit_counts: dict[int, dict[str, int]] = {seed: {regime: 0 for regime in REGIMES[1:]} for seed in expected}
    for seed, rows in scored_by_seed.items():
        for row in rows:
            regime = row.scenario.regime.value
            if row.method == "CRTO" and regime in action_counts:
                action_counts[regime]["legal_reviews"] += row.legal_discretionary_reviews
                action_counts[regime]["changed_option"] += row.changed_option_terminations
                action_counts[regime]["keep"] += row.legal_discretionary_reviews - row.changed_option_terminations
                audit_counts[seed][regime] += int(row.boundary is not None)
    conformance = {
        "all_eight_seeds": len(scored_by_seed) == 8,
        "all_frozen_evaluation_cells": all(
            sum(row.method == method and row.scenario.regime.value == regime for row in scored_by_seed.get(seed, ())) == 64
            for seed in expected for method in ("CRTO", "FULL-HISTORY-AUX-TERM") for regime in REGIMES
        ),
        "finite_returns": all(
            math.isfinite(row.normalized_score)
            for groups in (scored_by_seed, cuts_by_seed, deranged_by_seed) for rows in groups.values() for row in rows
        ),
        "identical_scenario_counts": all(
            {row.scenario_id for row in scored_by_seed.get(seed, ()) if row.method == "CRTO" and row.scenario.regime.value == regime}
            == {row.scenario_id for row in scored_by_seed.get(seed, ()) if row.method == "FULL-HISTORY-AUX-TERM" and row.scenario.regime.value == regime}
            for seed in expected for regime in REGIMES
        ),
        "exact_action_cost_parity": all(
            len({row.scenario for row in scored_by_seed.get(seed, ()) if row.scenario_id == scenario}) == 1
            for seed in expected for scenario in {row.scenario_id for row in scored_by_seed.get(seed, ())}
        ),
        "no_test_leakage": all(
            isinstance(per_seed_raw[seed].get("panel_identities"), Mapping)
            and per_seed_raw[seed]["panel_identities"].get("namespace") == PANEL_ROOT_NAMESPACE  # type: ignore[index,union-attr]
            for seed in expected
        ),
    }
    completeness["conformance"] = all(key in conformance for key in (
        "all_eight_seeds", "all_frozen_evaluation_cells", "finite_returns",
        "identical_scenario_counts", "exact_action_cost_parity", "no_test_leakage",
    ))
    if pooled_plan is None:
        validity = {"whole_algorithm_valid": False, "residual_mechanism_valid": False,
                    "mechanism_failure_reasons": ["canonical derangement plan unavailable"]}
    else:
        validity = validity_decisions(
            conformance=conformance, probe_by_seed=probe_by_seed,
            target_action_counts=action_counts, audit_boundary_counts=audit_counts,
            derangement=pooled_plan, hazard_fit_converged=hazard_converged,
            hazard_target_support_pass=hazard_support_pass, rate_balance=rate_report,
            balance_diagnostic=donor_balance, calibration=calibration_report, audit=audit_report,
        )

    decisions = registered_package_and_mechanism_decisions(
        primary=primary, validity=validity,
        delta_align=_as_mapping(mechanisms["Delta_align"], name="Delta_align"),
        delta_q=_as_mapping(mechanisms["Delta_Q"], name="Delta_Q"),
        delta_rate=_as_mapping(mechanisms["Delta_rate"], name="Delta_rate"),
        audit=audit_report, trend=trend_report, shortcut=shortcut_report,
    )
    mechanisms.update({"audit": audit_report, "trend": trend_report,
                       "shortcut": shortcut_report, "decisions": decisions})
    all_retirement_gates = bool(
        validity.get("whole_algorithm_valid", False)
        and validity.get("residual_mechanism_valid", False)
        and audit_report.get("decision_disagreement", {}).get("pass", False)
        and audit_report.get("headroom_pass", False)
        and trend_report.get("pass", False)
        and shortcut_report.get("pass", False)
        and mechanisms.get("Delta_align", {}).get("available", False)
        and mechanisms.get("Delta_Q", {}).get("available", False)
        and mechanisms.get("Delta_rate", {}).get("available", False)
    )
    retirement = retirement_decision_from_analysis_outputs(
        validity_and_all_mechanism_gates_pass=all_retirement_gates,
        primary=primary,
        delta_align=_as_mapping(mechanisms["Delta_align"], name="Delta_align retirement"),
        delta_q=_as_mapping(mechanisms["Delta_Q"], name="Delta_Q retirement"),
        delta_rate=_as_mapping(mechanisms["Delta_rate"], name="Delta_rate retirement"),
        audit=audit_report,
    )
    mechanisms["retirement"] = retirement

    try:
        resource_report = resource_conformance(
            _as_mapping(resources.get("actual_completed_steps"), name="actual_completed_steps"),  # type: ignore[arg-type]
            wall_seconds=float(resources["wall_seconds"]), peak_rss_bytes=int(resources["peak_rss_bytes"]),
            gpu_used=bool(resources.get("gpu_enabled", False)), cpu_count=int(resources.get("cpu_workers", 0)),
        )
        completeness["resources"] = True
    except (KeyError, TypeError, ValueError) as error:
        resource_report = {"pass": False, "failure_reasons": [str(error)]}
        completeness["resources"] = False
        anomalies.append(f"resources: {error}")

    descriptive = _descriptive_episode_metrics({
        seed: (*scored_by_seed.get(seed, ()), *cuts_by_seed.get(seed, ()), *deranged_by_seed.get(seed, ()))
        for seed in expected
    })
    completeness["descriptive_metrics"] = completeness.get("all_seed_raw_sections", False)
    activity_counts = {
        "target_action_counts": action_counts, "audit_boundary_counts": audit_counts,
        "probe_by_seed": probe_by_seed, "hazard_support_by_seed": hazard_support_sections,
    }
    donor_diagnostics = {
        "canonical_plan": asdict(pooled_plan) if pooled_plan is not None else None,
        "balance": donor_balance,
    }
    causal_audit = {"audit": audit_report, "trend": trend_report, "shortcut": shortcut_report}
    anomalies.extend(source_anomalies)
    required_complete = all(completeness.values())
    packet = build_result_packet(
        question_relevant_output_exists=required_complete,
        primary=primary, mechanisms=mechanisms, validity=validity,
        activity_counts=activity_counts, calibration=calibration_report,
        donor_diagnostics=donor_diagnostics, causal_audit=causal_audit,
        rate_diagnostics={"balance": rate_report, "hazard_support": hazard_support_sections},
        descriptive_metrics=descriptive, resources=resource_report, anomalies=anomalies,
    )
    packet["required_sections_complete"] = required_complete
    packet["section_completeness"] = completeness
    packet["missing_required_sections"] = [name for name, built in completeness.items() if not built]
    packet["question_relevant_output_exists"] = required_complete
    return {
        "result_packet": packet,
        "primary": primary, "mechanisms": mechanisms, "validity": validity,
        "retirement": retirement,
        "calibration": calibration_report, "donor_diagnostics": donor_diagnostics,
        "causal_audit": causal_audit, "rate_diagnostics": rate_report,
        "resources": resource_report, "section_completeness": completeness,
    }


def build_evaluation_bridge(
    *, seed: int, config: object, panel_namespace: int | None = None,
) -> EvaluationBridge:
    """Construct the concrete seed-bound bridge; no panel is generated eagerly."""

    if panel_namespace is not None and panel_namespace != PANEL_ROOT_NAMESPACE:
        raise ValueError("CRTO evaluation panel namespace must remain 2026081203")
    return EvaluationBridge(seed=seed, config=config)


__all__ = [
    "BoundarySnapshot", "CUT_METHODS", "EpisodeRaw", "EvaluationBridge", "LockedPolicy", "PANEL_ORDINALS",
    "HAZARD_SWITCH_FEATURE_ENCODING_ID", "PANEL_ROOT_NAMESPACE", "audit_enumeration", "complete_rollout_cuts", "deranged_replays",
    "build_evaluation_bridge", "donor_panel", "finalize", "hazard_development", "panel_root", "panel_specs", "run_episode",
    "scored_evaluation",
]
