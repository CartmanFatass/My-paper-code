"""Read-only bridge to the exact legacy host and immutable tape primitives.

Only physical host/tape types and the already-defined common-future audit
equation are imported.  No historical execution, model, training, result, or
artifact route is reachable from this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol, Sequence

import numpy as np

from experiments.candidates.commitment_residual_triggered_options.host import (
    DecisionKind,
    DecisionRecord,
    HORIZON,
    Option,
    Regime,
    ScenarioTape,
    ServiceRelayHost,
    balanced_scenario_specs,
    build_scenario_tape,
    common_future_audit_rollout,
)

from .config import AUDIT_HORIZON, EVALUATION_REGIMES, OBSERVATION_DIM, counter_seed
from .contracts import Panel, PanelRow, PredictorExample, RowKey, Split, TapeRecord, canonical_array


class ForecastProvider(Protocol):
    def __call__(
        self, origin_history: np.ndarray, option: int, k: int, elapsed_horizon: int,
    ) -> tuple[np.ndarray, np.ndarray]: ...


@dataclass(frozen=True)
class CommonFutureAudit:
    action_values: np.ndarray
    legal_mask: np.ndarray
    branch_steps: tuple[int, ...]
    first_step_target_charges: tuple[float, ...]
    denominator: int


def canonical_tape(tape: ScenarioTape) -> TapeRecord:
    """Return complete immutable tape content for direct structural equality."""

    scalars = (
        tape.spec.episode_index, tape.spec.episode_seed, tape.spec.regime.value,
        tape.spec.event.value, tape.spec.event_onset, tape.spec.replanning_cost,
        int(tape.initial_hot_lane),
    )
    arrays = tuple(canonical_array(array) for array in (
        tape.initial_locations, tape.arrival_hot_coin, tape.arrival_cold_coin,
        tape.relay_capacity_coin, tape.option_uniform, tape.rate_control_uniform,
    ))
    return scalars + arrays


def _script_scores(host: ServiceRelayHost) -> tuple[dict[Option, float], ...]:
    """Arm-independent, deterministic behavior scores on deployable state only."""

    rows: list[dict[Option, float]] = []
    for observation in host.observations():
        vector = observation.vector()
        # Fixed printed-order score with small deployable-state terms.  It is a
        # collection script, not a learned gate and contains no arm packet.
        queue_skew = float(vector[25] - vector[26])
        rows.append({
            option: float(-0.07 * int(option) + 0.01 * observation.agent +
                          (0.02 * queue_skew if int(option) % 2 == 0 else -0.02 * queue_skew))
            for option in Option
        })
    return tuple(rows)


def scripted_decisions(host: ServiceRelayHost) -> tuple[DecisionRecord, ...]:
    """Provisional inherited behavior/continuation; not frozen for a result run."""
    scores = _script_scores(host)
    if not host.initialized:
        return host.select_initial(scores, training=False)
    zeros = tuple({option: 0.0 for option in Option} for _ in range(4))
    return host.resolve_reviews(scores, zeros, training=False)


def enumerate_common_future_g16(
    predecision_host: ServiceRelayHost,
    *,
    target_agent: int,
    aligned_decisions: Sequence[DecisionRecord],
    continuation: Callable[[ServiceRelayHost], tuple[DecisionRecord, ...]] = scripted_decisions,
) -> CommonFutureAudit:
    """Enumerate KEEP then seven printed options on one immutable future tape."""

    previous = Option(int(predecision_host.state.options[target_agent]))
    host_actions = predecision_host.audit_action_set(target_agent)
    values = np.full(8, np.nan, dtype=np.float64)
    legal = np.zeros(8, dtype=np.bool_)
    legal[0] = True
    branch_steps: list[int] = []
    charges: list[float] = []
    expected_actions: list[tuple[int, Option | None]] = [(0, None)]
    expected_actions.extend(
        (int(option) + 1, option) for option in Option
        if option != previous and option in host_actions
    )
    for printed_index, action in expected_actions:
        value, branch = common_future_audit_rollout(
            predecision_host,
            target_agent=target_agent,
            audit_action=action,
            aligned_decisions=aligned_decisions,
            continuation=continuation,
        )
        if len(branch.steps) != AUDIT_HORIZON:
            raise RuntimeError("common-future branch did not execute exactly sixteen steps")
        first_target = branch.steps[0].decisions[target_agent]
        expected_charge = 0.0 if action is None else 0.05 + predecision_host.tape.spec.replanning_cost
        if abs(first_target.charge - expected_charge) > 1e-12:
            raise RuntimeError("target action charge was not applied exactly on the branch boundary")
        if action is not None and first_target.selected_option != action:
            raise RuntimeError("common-future branch did not apply the requested target action")
        values[printed_index] = value
        legal[printed_index] = True
        branch_steps.append(len(branch.steps))
        charges.append(first_target.charge)
    if tuple(np.flatnonzero(legal)) != tuple(index for index, _ in expected_actions):
        raise RuntimeError("common-future action order drifted")
    return CommonFutureAudit(
        action_values=values,
        legal_mask=legal,
        branch_steps=tuple(branch_steps),
        first_step_target_charges=tuple(charges),
        denominator=max(1, predecision_host.tape.total_physical_arrivals()),
    )


def _valid_event_window(host: ServiceRelayHost) -> bool:
    time = host.state.primitive_time
    onset = host.tape.spec.event_onset
    # Exact inherited B1 audit-population window.  NONE scenarios retain their
    # prospectively assigned onset and obey the same window as event scenarios.
    return onset + 4 <= time <= onset + 20


def _protected_switch_boundary(host: ServiceRelayHost) -> bool:
    time = host.state.primitive_time
    # Exact inherited protection is on the decision boundary, not a stronger
    # constant-K-over-the-whole-suffix restriction.
    return time + AUDIT_HORIZON <= HORIZON and abs(time - 128) > 8


def materialize_common_history_row(
    tape: ScenarioTape,
    *,
    replicate: int,
    split: Split,
    forecast: ForecastProvider,
) -> PanelRow | None:
    """Collect the first eligible agent at the first eligible review in one episode."""

    host = ServiceRelayHost(tape)
    histories: list[list[np.ndarray]] = [[] for _ in range(4)]
    origins: dict[tuple[int, int, int], tuple[np.ndarray, int, int]] = {}
    while not host.done:
        observations = host.observations()
        for agent, observation in enumerate(observations):
            vector = observation.vector()
            if vector.shape != (OBSERVATION_DIM,):
                raise RuntimeError("legacy host deployable history width drifted from 42")
            histories[agent].append(vector.copy())

        if host.initialized:
            kinds = host.review_kinds()
            aligned_host = host.clone(retain_records=False)
            aligned = scripted_decisions(aligned_host)
            for agent, kind in enumerate(kinds):
                previous = Option(int(host.state.options[agent]))
                elapsed = host.state.primitive_time - int(host.state.anchor_times[agent])
                replacements = [
                    option for option in Option
                    if option != previous and host.legal_mask(agent)[int(option)]
                ]
                origin_key = (
                    agent, int(host.state.commitment_ids[agent]), int(host.state.anchor_times[agent])
                )
                eligible = (
                    kind is DecisionKind.DISCRETIONARY
                    and bool(replacements)
                    and elapsed in (4, 8, 12, 16)
                    and origin_key in origins
                    and _valid_event_window(host)
                    and _protected_switch_boundary(host)
                )
                if not eligible:
                    continue
                origin_history, origin_option, origin_k = origins[origin_key]
                mean, factor = forecast(origin_history, origin_option, origin_k, elapsed)
                audit = enumerate_common_future_g16(
                    host, target_agent=agent, aligned_decisions=aligned,
                )
                aligned_target = aligned[agent]
                logged_action = (
                    0 if aligned_target.selected_option == previous
                    else int(aligned_target.selected_option) + 1
                )
                return PanelRow(
                    key=RowKey(
                        replicate=replicate, split=split, regime=tape.spec.regime.value,
                        episode_index=tape.spec.episode_index,
                        primitive_time=host.state.primitive_time, agent=agent,
                    ),
                    cost=tape.spec.replanning_cost,
                    elapsed_horizon=elapsed,
                    history=np.stack(histories[agent]),
                    target=host.predictor_target(agent),
                    mean=mean,
                    cholesky=factor,
                    legal_mask=audit.legal_mask,
                    g16=audit.action_values,
                    logged_action=logged_action,
                    tape_record=canonical_tape(tape),
                )

        decisions = scripted_decisions(host)
        for agent in range(4):
            key = (agent, int(host.state.commitment_ids[agent]), int(host.state.anchor_times[agent]))
            if key not in origins:
                origins[key] = (
                    np.stack(histories[agent]).astype(np.float32),
                    int(host.state.options[agent]),
                    int(host.state.current_k),
                )
        host.advance(decisions)
    return None


def materialize_common_history_panel(
    tapes: Sequence[ScenarioTape],
    *,
    replicate: int,
    split: Split,
    forecast: ForecastProvider,
) -> Panel:
    """Bounded batched seam over pre-materialized immutable episode tapes."""

    rows = [
        row for tape in tapes
        if (row := materialize_common_history_row(
            tape, replicate=replicate, split=split, forecast=forecast,
        )) is not None
    ]
    rows.sort(key=lambda row: row.key.canonical)
    return Panel(split=split, rows=tuple(rows))


def materialize_predictor_examples(tapes: Sequence[ScenarioTape]) -> tuple[PredictorExample, ...]:
    """Collect provisional inherited-policy continuous-commitment examples."""

    examples: list[PredictorExample] = []
    for tape in tapes:
        host = ServiceRelayHost(tape)
        histories: list[list[np.ndarray]] = [[] for _ in range(4)]
        origins: dict[tuple[int, int, int], tuple[np.ndarray, int, int]] = {}
        while not host.done:
            for agent, observation in enumerate(host.observations()):
                histories[agent].append(observation.vector().copy())
            if host.initialized:
                for agent in range(4):
                    anchor_time = int(host.state.anchor_times[agent])
                    elapsed = host.state.primitive_time - anchor_time
                    key = (agent, int(host.state.commitment_ids[agent]), anchor_time)
                    if elapsed in (4, 8, 12, 16) and key in origins:
                        origin_history, option, k = origins[key]
                        examples.append(PredictorExample(
                            episode_index=tape.spec.episode_index,
                            commitment_time=anchor_time,
                            target_age=elapsed,
                            agent=agent,
                            option=option,
                            k=k,
                            origin_history=origin_history,
                            target=host.predictor_target(agent),
                        ))
            decisions = scripted_decisions(host)
            for agent in range(4):
                key = (agent, int(host.state.commitment_ids[agent]), int(host.state.anchor_times[agent]))
                if key not in origins:
                    origins[key] = (
                        np.stack(histories[agent]).astype(np.float32),
                        int(host.state.options[agent]), int(host.state.current_k),
                    )
            host.advance(decisions)
    examples.sort(key=lambda example: example.canonical_key)
    return tuple(examples)


def build_balanced_tapes(
    *,
    replicate: int,
    split: Split,
    regime: str,
    count: int,
    first_episode_index: int,
) -> tuple[ScenarioTape, ...]:
    """Pre-materialize a split-isolated tape batch from the registered namespace."""

    regime_value = Regime(regime)
    split_ordinal = tuple(Split).index(Split(split))
    regime_ordinal = tuple(Regime).index(regime_value)
    root_seed = counter_seed("panel_tape", replicate, split_ordinal, regime_ordinal) % (2**63)
    specs = balanced_scenario_specs(
        count=count, regime=regime_value, root_seed=root_seed,
        first_episode_index=first_episode_index,
    )
    return tuple(build_scenario_tape(spec) for spec in specs)


def evaluation_tape_batches(
    *, replicate: int, split: Split, count_per_regime: int, first_episode_index: int,
) -> dict[str, tuple[ScenarioTape, ...]]:
    batches: dict[str, tuple[ScenarioTape, ...]] = {}
    cursor = first_episode_index
    for regime in EVALUATION_REGIMES:
        batches[regime] = build_balanced_tapes(
            replicate=replicate, split=split, regime=regime,
            count=count_per_regime, first_episode_index=cursor,
        )
        cursor += count_per_regime
    return batches
