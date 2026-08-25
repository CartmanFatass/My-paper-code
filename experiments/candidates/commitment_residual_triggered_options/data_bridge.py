"""Concrete host-to-tensor bridge for CRTO-B1 v4.

This module owns only data movement: deterministic panel manifests, the exact
scripted predictor policy, conversion to predictor/probe examples, and complete
on-policy recurrent training episodes.  Physical semantics remain in
``host.py`` and all learned/predictor equations remain in their owner modules.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import IntEnum
from math import log
from typing import Mapping, Sequence

import numpy as np
import torch

from .config import AGENT_COUNT, ALGORITHM_SEEDS, HORIZON
from .host import (
    DecisionKind as HostDecisionKind,
    EventClass,
    Option,
    Regime,
    ScenarioSpec,
    ScenarioTape,
    ServiceRelayHost,
    build_scenario_tape,
    onset_schedule,
)
from .models import (
    ArmKind,
    DecisionKind as ModelDecisionKind,
    RecurrentOptionActorCritic,
    decision_action_index,
)
from .predictor import (
    CalibrationTable,
    CommitmentAnchor,
    FORECAST_HORIZONS,
    ForecastExample,
    FrozenPredictor,
    PredecisionTarget,
    eligible_forecast_examples,
    forecast_examples,
    make_packets,
)
from .training import ProbeExample, RecurrentEpisode


PANEL_SEED_NAMESPACE = 2_026_081_203
OBSERVATION_DIM = 42
CENTRALIZED_STATE_DIM = 54


class PanelOrdinal(IntEnum):
    """Stable, persisted phase coordinates for all data-bearing panels."""

    SCRIPTED_PREDICTOR = 0
    LEARNED_TRAINING = 1


@dataclass(frozen=True)
class PanelEpisodeIdentity:
    algorithm_seed: int
    panel_ordinal: int
    episode_index: int
    episode_seed: int
    split: str
    regime: str
    event: str
    event_onset: int
    replanning_cost: float

    @property
    def seed_sequence_coordinates(self) -> tuple[int, int, int, int]:
        return (
            PANEL_SEED_NAMESPACE,
            self.algorithm_seed,
            self.panel_ordinal,
            self.episode_index,
        )

    def persisted(self) -> dict[str, object]:
        payload = asdict(self)
        payload["seed_sequence_coordinates"] = list(self.seed_sequence_coordinates)
        return payload

    def scenario_spec(self) -> ScenarioSpec:
        return ScenarioSpec(
            episode_index=self.episode_index,
            episode_seed=self.episode_seed,
            regime=Regime(self.regime),
            event=EventClass(self.event),
            event_onset=self.event_onset,
            replanning_cost=self.replanning_cost,
        )


@dataclass(frozen=True)
class ScriptedPredictorPanel:
    identities: tuple[PanelEpisodeIdentity, ...]
    predictor_fit: tuple[ForecastExample, ...]
    calibration: tuple[ForecastExample, ...]
    development: tuple[ForecastExample, ...]
    steps: int
    observation_dim: int = OBSERVATION_DIM
    centralized_state_dim: int = CENTRALIZED_STATE_DIM

    def persisted_identities(self) -> tuple[dict[str, object], ...]:
        return tuple(identity.persisted() for identity in self.identities)


@dataclass(frozen=True)
class ProbeSplits:
    predictor_fit: tuple[ProbeExample, ...]
    calibration: tuple[ProbeExample, ...]
    development: tuple[ProbeExample, ...]


@dataclass(frozen=True)
class _OnlineAnchor:
    commitment_time: int
    commitment_token: tuple[int, int, int]
    option: int
    k: int
    origin_hidden: torch.Tensor


@dataclass(frozen=True)
class CollectedLearnedEpisode:
    identity: PanelEpisodeIdentity
    tape: ScenarioTape
    trajectory: RecurrentEpisode
    normalized_score: float
    failure: bool


@dataclass(frozen=True)
class PairedTrainingBatch:
    update_index: int
    identities: tuple[PanelEpisodeIdentity, ...]
    crto: tuple[CollectedLearnedEpisode, ...]
    full_history_aux_term: tuple[CollectedLearnedEpisode, ...]
    steps: int

    def as_training_mapping(self) -> dict[str, object]:
        return {
            "CRTO": tuple(row.trajectory for row in self.crto),
            "FULL-HISTORY-AUX-TERM": tuple(
                row.trajectory for row in self.full_history_aux_term
            ),
            "steps": self.steps,
            "panel_identities": tuple(row.persisted() for row in self.identities),
        }


def _episode_seed(algorithm_seed: int, panel: PanelOrdinal, episode_index: int) -> int:
    sequence = np.random.SeedSequence((
        PANEL_SEED_NAMESPACE, int(algorithm_seed), int(panel), int(episode_index),
    ))
    words = sequence.generate_state(2, dtype=np.uint32)
    return int(words[0]) | (int(words[1]) << 32)


def _manifest_rows(panel: PanelOrdinal) -> list[tuple[str, Regime, EventClass, int, float]]:
    if panel is PanelOrdinal.SCRIPTED_PREDICTOR:
        repeats, splits = 2, ("predictor_fit",) * 8 + ("calibration",) * 4 + (
            "development",
        ) * 4
    elif panel is PanelOrdinal.LEARNED_TRAINING:
        repeats, splits = 8, ("training",) * 64
    else:
        raise ValueError("unknown CRTO panel ordinal")

    rows: list[tuple[str, Regime, EventClass, int, float]] = []
    for regime in (Regime.K4, Regime.K8):
        onsets = onset_schedule(regime)
        for event in EventClass:
            for cost in (0.25, 4.0):
                cell_size = repeats * len(onsets)
                if len(splits) != cell_size:
                    raise RuntimeError("panel split law does not match its crossed cell")
                for within_cell in range(cell_size):
                    rows.append((
                        splits[within_cell], regime, event,
                        onsets[within_cell % len(onsets)], cost,
                    ))
    expected = 256 if panel is PanelOrdinal.SCRIPTED_PREDICTOR else 1_024
    if len(rows) != expected:
        raise RuntimeError("constructed panel has the wrong registered episode count")
    return rows


def panel_manifest(
    algorithm_seed: int, panel: PanelOrdinal,
) -> tuple[PanelEpisodeIdentity, ...]:
    """Build a deterministic balanced manifest and expose every seed identity."""

    if (
        isinstance(algorithm_seed, bool)
        or not isinstance(algorithm_seed, (int, np.integer))
        or int(algorithm_seed) not in ALGORITHM_SEEDS
    ):
        raise ValueError("panel manifest requires a registered CRTO algorithm seed")
    algorithm_seed = int(algorithm_seed)
    panel = PanelOrdinal(panel)
    rows = _manifest_rows(panel)
    order = np.random.Generator(np.random.PCG64(np.random.SeedSequence((
        PANEL_SEED_NAMESPACE, int(algorithm_seed), int(panel),
    )))).permutation(len(rows))
    identities: list[PanelEpisodeIdentity] = []
    for episode_index, source_index in enumerate(order):
        split, regime, event, onset, cost = rows[int(source_index)]
        identities.append(PanelEpisodeIdentity(
            algorithm_seed=int(algorithm_seed), panel_ordinal=int(panel),
            episode_index=episode_index,
            episode_seed=_episode_seed(algorithm_seed, panel, episode_index),
            split=split, regime=regime.value, event=event.value,
            event_onset=onset, replanning_cost=cost,
        ))
    return tuple(identities)


def _commitment_token(host: ServiceRelayHost, agent: int) -> tuple[int, int, int]:
    return (
        host.tape.spec.episode_index,
        agent,
        int(host.state.commitment_ids[agent]),
    )


def _history_tensor(history: Sequence[np.ndarray]) -> torch.Tensor:
    tensor = torch.as_tensor(np.stack(history), dtype=torch.float32).clone()
    if tensor.ndim != 2 or tensor.shape[1] != OBSERVATION_DIM:
        raise RuntimeError("host deployable history violated the 44-coordinate boundary")
    return tensor


def _anchor_records(
    host: ServiceRelayHost,
    histories: Sequence[Sequence[np.ndarray]],
    decisions: Sequence[object],
) -> list[CommitmentAnchor]:
    anchors: list[CommitmentAnchor] = []
    for agent, decision in enumerate(decisions):
        if not bool(getattr(decision, "reanchored")):
            continue
        anchors.append(CommitmentAnchor(
            episode_index=host.tape.spec.episode_index,
            commitment_time=host.state.primitive_time,
            environment_slot=agent,
            commitment_token=_commitment_token(host, agent),
            option=int(host.state.options[agent]),
            k=host.tape.k_at(host.state.primitive_time),
            origin_history=_history_tensor(histories[agent]),
        ))
    return anchors


def _zero_scores() -> tuple[dict[Option, float], ...]:
    return tuple({option: 0.0 for option in Option} for _ in range(AGENT_COUNT))


def _script_review_scores(host: ServiceRelayHost) -> tuple[
    tuple[dict[Option, float], ...], tuple[dict[Option, float], ...]
]:
    q_rows = _zero_scores()
    b_rows: list[dict[Option, float]] = []
    cost = host.tape.spec.replanning_cost
    for agent, kind in enumerate(host.review_kinds()):
        current = Option(int(host.state.options[agent]))
        residual = {option: 0.0 for option in Option}
        if kind is HostDecisionKind.DISCRETIONARY:
            replacements = [
                option for option, allowed in zip(Option, host.legal_mask(agent))
                if allowed and option is not current
            ]
            if replacements:
                # KEEP has mass .75 and replacements share mass .25 exactly.
                relative = log(1.0 / (3.0 * len(replacements)))
                for option in replacements:
                    residual[option] = cost + 0.05 + relative
        elif kind is HostDecisionKind.FORCED_RENEWAL:
            # Cancel the changed-option cost, leaving every legal option equal.
            for option in Option:
                if option is not current:
                    residual[option] = cost
        b_rows.append(residual)
    return q_rows, tuple(b_rows)


def _collect_scripted_episode(
    identity: PanelEpisodeIdentity,
) -> tuple[list[CommitmentAnchor], list[PredecisionTarget], int]:
    host = ServiceRelayHost(build_scenario_tape(identity.scenario_spec()))
    histories: list[list[np.ndarray]] = [[] for _ in range(AGENT_COUNT)]
    anchors: list[CommitmentAnchor] = []
    targets: list[PredecisionTarget] = []

    while not host.done:
        observations = host.observations()
        for agent, observation in enumerate(observations):
            histories[agent].append(observation.vector())
        if host.initialized:
            for agent in range(AGENT_COUNT):
                targets.append(PredecisionTarget(
                    episode_index=identity.episode_index,
                    primitive_time=host.state.primitive_time,
                    environment_slot=agent,
                    predecision_commitment_token=_commitment_token(host, agent),
                    target=torch.as_tensor(host.predictor_target(agent), dtype=torch.float32),
                ))
            q_rows, b_rows = _script_review_scores(host)
            decisions = host.resolve_reviews(q_rows, b_rows, training=True)
        else:
            decisions = host.select_initial(_zero_scores(), training=True)
        anchors.extend(_anchor_records(host, histories, decisions))
        host.advance(decisions)
    host.finish()
    return anchors, targets, HORIZON


def collect_scripted_predictor_panel(algorithm_seed: int) -> ScriptedPredictorPanel:
    """Collect all 256 complete scripted episodes and their frozen splits."""

    identities = panel_manifest(algorithm_seed, PanelOrdinal.SCRIPTED_PREDICTOR)
    split_rows: dict[str, list[ForecastExample]] = {
        "predictor_fit": [], "calibration": [], "development": [],
    }
    steps = 0
    for identity in identities:
        anchors, targets, episode_steps = _collect_scripted_episode(identity)
        split_rows[identity.split].extend(eligible_forecast_examples(anchors, targets))
        steps += episode_steps
    if steps != 256 * HORIZON:
        raise RuntimeError("scripted predictor panel did not complete its exact ledger row")
    return ScriptedPredictorPanel(
        identities=identities,
        predictor_fit=tuple(sorted(split_rows["predictor_fit"], key=lambda row: row.canonical_key)),
        calibration=tuple(sorted(split_rows["calibration"], key=lambda row: row.canonical_key)),
        development=tuple(sorted(split_rows["development"], key=lambda row: row.canonical_key)),
        steps=steps,
    )


def _probe_examples(
    predictor: FrozenPredictor,
    calibration: CalibrationTable,
    examples: Sequence[ForecastExample],
) -> tuple[ProbeExample, ...]:
    ordered = sorted(examples, key=lambda row: row.canonical_key)
    target, mean, factor = forecast_examples(predictor, ordered)
    packets = make_packets(target, mean, factor, calibration)
    return tuple(
        ProbeExample(
            episode_index=row.episode_index,
            commitment_time=row.commitment_time,
            target_age=row.target_age,
            environment_slot=row.environment_slot,
            raw_packet=packets.raw[index].detach().cpu().clone(),
            explicit_coordinates=packets.explicit[index, :24].detach().cpu().clone(),
        )
        for index, row in enumerate(ordered)
    )


def materialize_probe_splits(
    predictor: FrozenPredictor,
    calibration: CalibrationTable,
    panel: ScriptedPredictorPanel,
) -> ProbeSplits:
    """Create probe rows after, and only from, the common fitted predictor."""

    return ProbeSplits(
        predictor_fit=_probe_examples(predictor, calibration, panel.predictor_fit),
        calibration=_probe_examples(predictor, calibration, panel.calibration),
        development=_probe_examples(predictor, calibration, panel.development),
    )


def _centralized_preselection_vector(host: ServiceRelayHost) -> np.ndarray:
    """Physical reset state with the not-yet-selected option block set to zero."""

    state = host.state
    vector = np.concatenate((
        state.queues.astype(np.float32) / 64.0,
        state.buffers.astype(np.float32) / 64.0,
        np.eye(3, dtype=np.float32)[state.locations].reshape(-1),
        state.energies.astype(np.float32) / 32.0,
        np.zeros(AGENT_COUNT * len(Option), dtype=np.float32),
        state.option_ages.astype(np.float32) / 16.0,
        np.asarray((state.current_k / 16.0, 0.0), dtype=np.float32),
    ))
    if vector.shape != (CENTRALIZED_STATE_DIM,):
        raise RuntimeError("reset centralized state violated its fixed width")
    return vector


def _online_packets(
    host: ServiceRelayHost,
    predictor: FrozenPredictor,
    calibration: CalibrationTable,
    anchors: Sequence[_OnlineAnchor | None],
) -> tuple[torch.Tensor, torch.Tensor]:
    explicit = torch.zeros((AGENT_COUNT, 52), dtype=torch.float32)
    raw = torch.zeros((AGENT_COUNT, 52), dtype=torch.float32)
    for agent, anchor in enumerate(anchors):
        if anchor is None:
            continue
        horizon = host.state.primitive_time - anchor.commitment_time
        if horizon not in FORECAST_HORIZONS:
            continue
        if anchor.commitment_token != _commitment_token(host, agent):
            continue
        with torch.no_grad():
            distribution = predictor.forecast_from_hidden(
                anchor.origin_hidden.unsqueeze(0),
                torch.tensor((anchor.option,), dtype=torch.int64),
                torch.tensor((anchor.k,), dtype=torch.int64),
                (horizon,),
            )
            target = torch.as_tensor(host.predictor_target(agent), dtype=torch.float32).unsqueeze(0)
            bundle = make_packets(
                target, distribution.mean[:, 0], distribution.cholesky[:, 0], calibration
            )
        explicit[agent] = bundle.explicit[0]
        raw[agent] = bundle.raw[0]
    return explicit, raw


def _model_kind(kind: HostDecisionKind) -> ModelDecisionKind:
    return {
        HostDecisionKind.NONE: ModelDecisionKind.NONE,
        HostDecisionKind.INITIAL: ModelDecisionKind.INITIAL,
        HostDecisionKind.DISCRETIONARY: ModelDecisionKind.DISCRETIONARY,
        HostDecisionKind.FORCED_RENEWAL: ModelDecisionKind.FORCED_RENEWAL,
    }[kind]


def collect_learned_episode(
    identity: PanelEpisodeIdentity,
    tape: ScenarioTape,
    model: RecurrentOptionActorCritic,
    predictor: FrozenPredictor,
    calibration: CalibrationTable,
) -> CollectedLearnedEpisode:
    """Collect one complete old-policy trajectory on one immutable tape."""

    if identity.panel_ordinal != int(PanelOrdinal.LEARNED_TRAINING):
        raise ValueError("learned collection requires a training-panel identity")
    if model.algorithm_seed != identity.algorithm_seed or predictor.algorithm_seed != identity.algorithm_seed:
        raise ValueError("identity, learned arm, and predictor algorithm seeds must agree")
    if tape.spec != identity.scenario_spec():
        raise ValueError("supplied tape does not match its persisted panel identity")
    if model.observation_dim != OBSERVATION_DIM or model.centralized_state_dim != CENTRALIZED_STATE_DIM:
        raise ValueError("learned model dimensions do not match the concrete host vectors")

    host = ServiceRelayHost(tape)
    anchors: list[_OnlineAnchor | None] = [None] * AGENT_COUNT
    hidden = model.initial_hidden(AGENT_COUNT)
    predictor_hidden = torch.zeros((1, AGENT_COUNT, 64), dtype=torch.float32)
    records: dict[str, list[torch.Tensor]] = {
        key: [] for key in (
            "observations", "centralized", "packets", "current", "legal", "kinds",
            "selected", "costs", "charges", "rewards", "dones", "log_probs", "values",
        )
    }
    model.eval()
    predictor.eval()

    while not host.done:
        time = host.state.primitive_time
        observations = host.observations()
        observation_tensor = torch.as_tensor(
            np.stack([row.vector() for row in observations]), dtype=torch.float32
        )
        with torch.no_grad():
            _encoded, predictor_hidden = predictor.observation_encoder(
                observation_tensor.unsqueeze(1), predictor_hidden
            )
        centralized = torch.as_tensor(
            _centralized_preselection_vector(host)
            if not host.initialized else host.centralized_state_vector(),
            dtype=torch.float32,
        )
        explicit_packet, raw_packet = _online_packets(host, predictor, calibration, anchors)
        adapter_packet = explicit_packet if model.arm is ArmKind.CRTO else raw_packet
        with torch.no_grad():
            actor = model.forward_step(observation_tensor, hidden, centralized, adapter_packet)
        hidden = actor.hidden.detach()
        q_rows = tuple(
            {option: float(actor.q[agent, int(option)]) for option in Option}
            for agent in range(AGENT_COUNT)
        )
        b_rows = tuple(
            {option: float(actor.residual_contribution[agent, int(option)]) for option in Option}
            for agent in range(AGENT_COUNT)
        )

        if not host.initialized:
            decisions = host.select_initial(q_rows, training=True)
        else:
            kinds_before = host.review_kinds()
            switch = tape.k_at(time) != host.state.current_k
            for agent, kind in enumerate(kinds_before):
                if kind is not HostDecisionKind.NONE and not switch:
                    anchor = anchors[agent]
                    if anchor is None or time - anchor.commitment_time not in FORECAST_HORIZONS:
                        raise RuntimeError("legal learned review lacks its eligible anchor forecast")
            decisions = host.resolve_reviews(q_rows, b_rows, training=True)

        joint_log_probability = actor.value.new_zeros(())
        for agent, decision in enumerate(decisions):
            kind = _model_kind(decision.kind)
            if kind is ModelDecisionKind.NONE:
                continue
            q = actor.q[agent:agent + 1]
            residual = actor.residual_contribution[agent:agent + 1]
            if decision.switch_time:
                residual = torch.zeros_like(residual)
            legal = torch.tensor((host.legal_mask(agent),), dtype=torch.bool)
            current_value = int(
                decision.selected_option if decision.previous_option is None
                else decision.previous_option
            )
            current = torch.tensor((current_value,), dtype=torch.int64)
            cost = torch.tensor((tape.spec.replanning_cost,), dtype=torch.float32)
            if kind is ModelDecisionKind.INITIAL:
                logits = model.initial_logits(q, legal)
            elif kind is ModelDecisionKind.DISCRETIONARY:
                logits = model.discretionary_logits(q, residual, current, legal, cost)
            else:
                logits = model.forced_renewal_logits(q, residual, current, legal, cost)
            action = torch.tensor((decision_action_index(
                kind, int(decision.selected_option), current_value,
            ),), dtype=torch.int64)
            selected_log_probability, _entropy = model.log_probability_and_entropy(logits, action)
            joint_log_probability = joint_log_probability + selected_log_probability[0]

        current_options = torch.tensor([
            int(row.selected_option if row.previous_option is None else row.previous_option)
            for row in decisions
        ], dtype=torch.int64)
        selected_options = torch.tensor(
            [int(row.selected_option) for row in decisions], dtype=torch.int64
        )
        decision_kinds = torch.tensor(
            [int(_model_kind(row.kind)) for row in decisions], dtype=torch.int64
        )
        legal_masks = torch.tensor(
            [host.legal_mask(agent) for agent in range(AGENT_COUNT)], dtype=torch.bool
        )
        charges = torch.tensor([row.charge for row in decisions], dtype=torch.float32)
        for agent, decision in enumerate(decisions):
            if decision.reanchored:
                anchors[agent] = _OnlineAnchor(
                    commitment_time=time,
                    commitment_token=_commitment_token(host, agent),
                    option=int(host.state.options[agent]),
                    k=tape.k_at(time),
                    origin_hidden=predictor_hidden[0, agent].detach().clone(),
                )

        step_record = host.advance(decisions)
        records["observations"].append(observation_tensor)
        records["centralized"].append(centralized)
        records["packets"].append(adapter_packet.detach().clone())
        records["current"].append(current_options)
        records["legal"].append(legal_masks)
        records["kinds"].append(decision_kinds)
        records["selected"].append(selected_options)
        records["costs"].append(torch.full((AGENT_COUNT,), tape.spec.replanning_cost))
        records["charges"].append(charges)
        records["rewards"].append(torch.tensor(step_record.reward, dtype=torch.float32))
        records["dones"].append(torch.tensor(host.done, dtype=torch.bool))
        records["log_probs"].append(joint_log_probability.detach())
        records["values"].append(actor.value.detach())

    episode_record = host.finish()
    trajectory = RecurrentEpisode(
        episode_index=identity.episode_index,
        deployable_observations=torch.stack(records["observations"]),
        centralized_states=torch.stack(records["centralized"]),
        adapter_packets=torch.stack(records["packets"]),
        current_options=torch.stack(records["current"]),
        legal_masks=torch.stack(records["legal"]),
        decision_kinds=torch.stack(records["kinds"]),
        selected_options=torch.stack(records["selected"]),
        replanning_costs=torch.stack(records["costs"]),
        own_immediate_charges=torch.stack(records["charges"]),
        rewards=torch.stack(records["rewards"]),
        dones=torch.stack(records["dones"]),
        old_joint_log_probabilities=torch.stack(records["log_probs"]),
        old_values=torch.stack(records["values"]),
    )
    trajectory.validate(model)
    return CollectedLearnedEpisode(
        identity=identity, tape=tape, trajectory=trajectory,
        normalized_score=episode_record.normalized_score, failure=episode_record.failure,
    )


def collect_paired_training_batch(
    algorithm_seed: int,
    update_index: int,
    models: Mapping[str, RecurrentOptionActorCritic],
    predictor: FrozenPredictor,
    calibration: CalibrationTable,
) -> PairedTrainingBatch:
    """Collect 32 CRTO and 32 FULL trajectories on byte-identical tapes."""

    if not 0 <= update_index < 32:
        raise ValueError("training update index must be in [0,32)")
    try:
        crto_model = models["CRTO"]
        full_model = models["FULL-HISTORY-AUX-TERM"]
    except KeyError as error:
        raise ValueError("paired collection requires both registered learned arms") from error
    if crto_model.arm is not ArmKind.CRTO or full_model.arm is not ArmKind.FULL_HISTORY_AUX_TERM:
        raise ValueError("learned models have incorrect paired arm identities")
    manifest = panel_manifest(algorithm_seed, PanelOrdinal.LEARNED_TRAINING)
    identities = manifest[update_index * 32:(update_index + 1) * 32]
    crto_rows: list[CollectedLearnedEpisode] = []
    full_rows: list[CollectedLearnedEpisode] = []
    for identity in identities:
        tape = build_scenario_tape(identity.scenario_spec())
        crto_rows.append(collect_learned_episode(
            identity, tape, crto_model, predictor, calibration
        ))
        full_rows.append(collect_learned_episode(
            identity, tape, full_model, predictor, calibration
        ))
    return PairedTrainingBatch(
        update_index=update_index,
        identities=identities,
        crto=tuple(crto_rows),
        full_history_aux_term=tuple(full_rows),
        steps=2 * len(identities) * HORIZON,
    )


__all__ = [
    "CENTRALIZED_STATE_DIM", "CollectedLearnedEpisode", "OBSERVATION_DIM",
    "PANEL_SEED_NAMESPACE", "PairedTrainingBatch", "PanelEpisodeIdentity",
    "PanelOrdinal", "ProbeSplits", "ScriptedPredictorPanel",
    "collect_learned_episode", "collect_paired_training_batch",
    "collect_scripted_predictor_panel", "materialize_probe_splits", "panel_manifest",
]
