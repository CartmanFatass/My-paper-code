"""FRRIE V2 external-action training orchestration interfaces.

The production entry point remains unreachable while the simultaneous-mean
inference contract is unresolved.  The functions here freeze the downstream
state/action seams so resolving that blocker cannot silently change replay,
recurrent-state, or paired-work semantics.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

import numpy as np

from .contracts.core import LEARNED_ARMS, UPDATES, ContractError
from .policy import LEGAL_ACTION_INDICES, FRRIEActorCritic, require_torch
from .training import RSCFEpisode, TRAIN_ROSTER_ORDER


HORIZON = 12
INFERENCE_BLOCKER = "SIMULTANEOUS_MEAN_INFERENCE_UNRESOLVED_AT_24_BLOCKS"


@dataclass(frozen=True, slots=True)
class ExternalObservation:
    observations: np.ndarray
    roles: np.ndarray
    legal_masks: np.ndarray
    slot: int
    terminal: bool


@dataclass(frozen=True, slots=True)
class ExternalStep:
    terminal: bool
    dw: int
    de: int
    waste: float
    terminal_return: float


@runtime_checkable
class ExternalActionEnvironment(Protocol):
    """Environment-only state boundary; policy and RNG remain external."""

    roster: int

    def reset(self, environment_tape: object) -> None: ...
    def observe(self) -> ExternalObservation: ...
    def step(self, actions: Sequence[int]) -> ExternalStep: ...
    def snapshot(self) -> bytes: ...
    def restore(self, snapshot: bytes) -> None: ...


@dataclass(frozen=True, slots=True)
class OriginCoordinate:
    role: int
    slot: int
    entity: int


@dataclass(frozen=True, slots=True)
class OriginReplayState:
    """Arm-independent environment origin plus arm-local recurrent state."""

    coordinate: OriginCoordinate
    environment_snapshot: bytes
    observations: np.ndarray
    roles: np.ndarray
    legal_masks: np.ndarray
    incoming_hidden: Any
    postdecision_hidden: Any
    current_actions: Any
    probabilities: Any
    selected_probabilities: Any


@dataclass(frozen=True, slots=True)
class PairedUpdatePlan:
    update: int
    roster_order: tuple[int, ...]
    tape_ids: tuple[str, ...]
    origin_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RSCFReplayAudit:
    alternative_suffixes_executed: int
    factual_suffixes_audited: int
    factual_trace_direct_equal: bool
    factual_audit_actor_steps: int
    new_rng_addresses: int
    preupdate_model_bit_equal: bool


@dataclass(frozen=True, slots=True)
class FactualDecisionRecord:
    environment_snapshot: bytes
    observations: np.ndarray
    roles: np.ndarray
    legal_masks: np.ndarray
    incoming_hidden: Any
    postdecision_hidden: Any
    probabilities: Any
    actions: Any
    step: ExternalStep
    poststep_environment_snapshot: bytes


def production_training_schedule(
    tape_ids: Sequence[Sequence[str]], origin_ids: Sequence[Sequence[str]],
) -> tuple[PairedUpdatePlan, ...]:
    """Bind exactly 512 paired updates in manifest episode order.

    The returned plans contain no arm field by design: both learned arms must
    consume the same plan object and retain separate model/optimizer state.
    """

    if len(tape_ids) != UPDATES or len(origin_ids) != UPDATES:
        raise ContractError("V2 production schedule requires exactly 512 updates")
    plans: list[PairedUpdatePlan] = []
    all_tapes: set[str] = set()
    all_origins: set[str] = set()
    for index, (tapes, origins) in enumerate(zip(tape_ids, origin_ids), start=1):
        if len(tapes) != 64 or len(origins) != 64:
            raise ContractError("each update requires 64 tape/origin identities")
        if any(not isinstance(value, str) or not value for value in (*tapes, *origins)):
            raise ContractError("tape and origin identities must be nonempty strings")
        if len(set(tapes)) != 64 or any(value in all_tapes for value in tapes):
            raise ContractError("each update/episode coordinate requires one unique tape identity")
        if len(set(origins)) != 64 or any(value in all_origins for value in origins):
            raise ContractError("each update/episode coordinate requires one unique origin identity")
        all_tapes.update(tapes)
        all_origins.update(origins)
        plans.append(PairedUpdatePlan(
            update=index,
            roster_order=TRAIN_ROSTER_ORDER,
            tape_ids=tuple(tapes),
            origin_ids=tuple(origins),
        ))
    return tuple(plans)


def assert_paired_initialization(models: Mapping[str, FRRIEActorCritic]) -> None:
    if set(models) != set(LEARNED_ARMS):
        raise ContractError("paired execution requires exactly both learned arms")
    left, right = (models[arm] for arm in LEARNED_ARMS)
    if left is right or left.parameter_bytes() != right.parameter_bytes():
        raise ContractError("paired models must be separate after byte-identical initialization")


def _validate_origins(origins: Sequence[OriginCoordinate], roster: int) -> None:
    if len(origins) != 3 or tuple(origin.role for origin in origins) != (0, 1, 2):
        raise ContractError("one W/E/R origin is required in role order")
    if any(
        type(origin.slot) is not int or not 0 <= origin.slot < HORIZON
        or type(origin.entity) is not int or not 0 <= origin.entity < roster
        for origin in origins
    ):
        raise ContractError("origin coordinates lie outside the episode")


def _as_torch_observation(frame: ExternalObservation) -> tuple[Any, Any]:
    import torch

    observations = torch.as_tensor(
        np.asarray(frame.observations, dtype=np.float32), dtype=torch.float32
    )
    roles = torch.as_tensor(np.asarray(frame.roles, dtype=np.int64), dtype=torch.int64)
    if observations.shape != (len(roles), 22):
        raise ContractError("external observation must have shape [roster,22]")
    masks = np.asarray(frame.legal_masks, dtype=np.bool_)
    expected_masks = np.zeros((len(roles), 6), dtype=np.bool_)
    for entity, role in enumerate(roles.tolist()):
        if role not in (0, 1, 2):
            raise ContractError("external observation contains an unknown public role")
        expected_masks[entity, list(LEGAL_ACTION_INDICES[role])] = True
    if not _direct_array_equal(masks, expected_masks):
        raise ContractError("external legal masks differ from the fixed role support")
    return observations, roles


def _terminal_return(step: ExternalStep) -> float:
    if not step.terminal or not np.isfinite(step.terminal_return):
        raise ContractError("closed-loop suffix did not produce a finite terminal return")
    return float(step.terminal_return)


def _direct_array_equal(left: np.ndarray, right: np.ndarray) -> bool:
    return left.dtype == right.dtype and left.shape == right.shape and left.tobytes() == right.tobytes()


def _direct_step_equal(left: ExternalStep, right: ExternalStep) -> bool:
    return (
        left.terminal == right.terminal
        and left.dw == right.dw
        and left.de == right.de
        and np.float32(left.waste).tobytes() == np.float32(right.waste).tobytes()
        and np.float32(left.terminal_return).tobytes()
        == np.float32(right.terminal_return).tobytes()
    )


def _audit_factual_suffix(
    *, model: FRRIEActorCritic, environment: ExternalActionEnvironment,
    origin: OriginReplayState, factual_trace: Sequence[FactualDecisionRecord],
    action_uniforms: np.ndarray,
) -> int:
    """Physically replay one factual-label suffix and compare every direct fact."""

    import torch

    environment.restore(origin.environment_snapshot)
    start = origin.coordinate.slot
    expected_origin = factual_trace[start]
    if (
        environment.snapshot() != expected_origin.environment_snapshot
        or origin.environment_snapshot != expected_origin.environment_snapshot
        or not _direct_array_equal(origin.observations, expected_origin.observations)
        or not _direct_array_equal(origin.roles, expected_origin.roles)
        or not _direct_array_equal(origin.legal_masks, expected_origin.legal_masks)
        or not torch.equal(origin.incoming_hidden, expected_origin.incoming_hidden)
        or not torch.equal(origin.postdecision_hidden, expected_origin.postdecision_hidden)
        or not torch.equal(origin.probabilities, expected_origin.probabilities)
        or not torch.equal(origin.current_actions, expected_origin.actions)
    ):
        raise ContractError("factual audit retained origin decision trace differs")
    # The origin clock is already post-GRU/post-distribution/post-action and
    # pretransition.  Step the retained joint action directly; recomputation
    # at this slot would add an unauthorized actor decision to the work ledger.
    step = environment.step(origin.current_actions.tolist())
    if not _direct_step_equal(step, expected_origin.step):
        raise ContractError("factual audit origin terminal primitives or FP32 J differ")
    if environment.snapshot() != expected_origin.poststep_environment_snapshot:
        raise ContractError("factual audit origin poststep state bytes differ")
    hidden = origin.postdecision_hidden.detach().clone()
    actor_steps = 0
    with torch.no_grad():
        for slot in range(start + 1, HORIZON):
            expected = factual_trace[slot]
            if environment.snapshot() != expected.environment_snapshot:
                raise ContractError("factual audit native predecision state bytes differ")
            frame = environment.observe()
            if (
                frame.slot != slot or frame.terminal
                or not _direct_array_equal(frame.observations, expected.observations)
                or not _direct_array_equal(frame.roles, expected.roles)
                or not _direct_array_equal(frame.legal_masks, expected.legal_masks)
            ):
                raise ContractError("factual audit observation/role/mask trace differs")
            observations, roles = _as_torch_observation(frame)
            if not torch.equal(hidden, expected.incoming_hidden):
                raise ContractError("factual audit incoming recurrent state differs")
            actor = model.actor_step(observations, roles, hidden)
            actor_steps += 1
            actions = model.actions_from_uniforms(
                actor.probabilities,
                torch.as_tensor(action_uniforms[slot], dtype=torch.float32),
            )
            if (
                not torch.equal(actor.hidden, expected.postdecision_hidden)
                or not torch.equal(actor.probabilities, expected.probabilities)
                or not torch.equal(actions, expected.actions)
            ):
                raise ContractError("factual audit hidden/probability/action trace differs")
            step = environment.step(actions.tolist())
            if not _direct_step_equal(step, expected.step):
                raise ContractError("factual audit terminal primitives or FP32 J differ")
            if environment.snapshot() != expected.poststep_environment_snapshot:
                raise ContractError("factual audit native poststep state bytes differ")
            hidden = actor.hidden
    return actor_steps


def _suffix_return(
    *, model: FRRIEActorCritic, environment: ExternalActionEnvironment,
    origin: OriginReplayState, focal_action: int, action_uniforms: np.ndarray,
) -> float:
    """Restore one origin and execute one immutable-model closed-loop suffix."""

    import torch

    environment.restore(origin.environment_snapshot)
    with torch.no_grad():
        actions = origin.current_actions.detach().clone()
        actions[origin.coordinate.entity] = int(focal_action)
        step = environment.step(actions.tolist())
        hidden = origin.postdecision_hidden.detach().clone()
        slot = origin.coordinate.slot + 1
        while not step.terminal:
            frame = environment.observe()
            observations, roles = _as_torch_observation(frame)
            actor = model.actor_step(observations, roles, hidden)
            uniforms = torch.as_tensor(action_uniforms[slot], dtype=torch.float32)
            actions = model.actions_from_uniforms(actor.probabilities, uniforms)
            hidden = actor.hidden
            step = environment.step(actions.tolist())
            slot += 1
            if slot > HORIZON:
                raise ContractError("external environment exceeded the 12-slot horizon")
    return _terminal_return(step)


def capture_rscf_episode(
    *, model: FRRIEActorCritic, environment: ExternalActionEnvironment,
    environment_tape: object, action_uniforms: np.ndarray,
    origins: Sequence[OriginCoordinate], audit_out: dict[str, Any] | None = None,
) -> RSCFEpisode:
    """Capture a factual episode and all legal focal-action suffix targets.

    Each origin is snapped after observation, GRU/distribution and factual
    action selection, but before the environment step.  The factual current
    teammate actions and common future tape are reused in every branch.
    """

    require_torch()
    import torch

    roster = environment.roster
    _validate_origins(origins, roster)
    uniforms = np.asarray(action_uniforms, dtype=np.float32)
    if uniforms.shape != (HORIZON, roster) or not np.isfinite(uniforms).all():
        raise ContractError("action tape must be finite FP32 [12,roster]")
    if np.any((uniforms < 0.0) | (uniforms >= 1.0)):
        raise ContractError("action tape uniforms must lie in [0,1)")

    environment.reset(environment_tape)
    hidden = model.initial_hidden(roster)
    probabilities_by_slot: list[Any] = []
    observations_by_slot: list[Any] = []
    factual_trace: list[FactualDecisionRecord] = []
    origin_by_role: dict[int, OriginReplayState] = {}
    terminal_step: ExternalStep | None = None
    factual_roles: Any | None = None

    for slot in range(HORIZON):
        frame = environment.observe()
        if frame.slot != slot or frame.terminal:
            raise ContractError("external observation slot/terminal contract drift")
        observations, roles = _as_torch_observation(frame)
        if factual_roles is None:
            factual_roles = roles.detach().clone()
        elif not torch.equal(factual_roles, roles):
            raise ContractError("public roles changed during the fixed-roster episode")
        incoming_hidden = hidden
        predecision_snapshot = environment.snapshot()
        actor = model.actor_step(observations, roles, incoming_hidden)
        actions = model.actions_from_uniforms(
            actor.probabilities, torch.as_tensor(uniforms[slot], dtype=torch.float32)
        )
        probabilities_by_slot.append(actor.probabilities)
        observations_by_slot.append(observations)
        for coordinate in origins:
            if coordinate.slot == slot:
                if int(roles[coordinate.entity].item()) != coordinate.role:
                    raise ContractError("origin entity does not have its declared public role")
                origin_by_role[coordinate.role] = OriginReplayState(
                    coordinate=coordinate,
                    environment_snapshot=predecision_snapshot,
                    observations=frame.observations.copy(),
                    roles=frame.roles.copy(),
                    legal_masks=frame.legal_masks.copy(),
                    incoming_hidden=incoming_hidden.detach().clone(),
                    postdecision_hidden=actor.hidden.detach().clone(),
                    current_actions=actions.detach().clone(),
                    probabilities=actor.probabilities.detach().clone(),
                    selected_probabilities=actor.probabilities[coordinate.entity],
                )
        hidden = actor.hidden
        terminal_step = environment.step(actions.tolist())
        poststep_snapshot = environment.snapshot()
        factual_trace.append(FactualDecisionRecord(
            environment_snapshot=predecision_snapshot,
            observations=frame.observations.copy(),
            roles=frame.roles.copy(),
            legal_masks=frame.legal_masks.copy(),
            incoming_hidden=incoming_hidden.detach().clone(),
            postdecision_hidden=actor.hidden.detach().clone(),
            probabilities=actor.probabilities.detach().clone(),
            actions=actions.detach().clone(),
            step=terminal_step,
            poststep_environment_snapshot=poststep_snapshot,
        ))
        if terminal_step.terminal != (slot == HORIZON - 1):
            raise ContractError("external environment terminal horizon drift")

    if set(origin_by_role) != {0, 1, 2} or terminal_step is None:
        raise ContractError("factual rollout did not capture all three origins")
    factual_return = _terminal_return(terminal_step)
    selected = torch.stack([
        origin_by_role[role].selected_probabilities for role in range(3)
    ])
    factual_actions = torch.stack([
        origin_by_role[role].current_actions[origin_by_role[role].coordinate.entity]
        for role in range(3)
    ]).to(torch.int64)
    legal = torch.zeros((3, 6), dtype=torch.bool)
    q_targets = torch.full((3, 6), torch.nan, dtype=torch.float32)
    immutable_model_bytes = model.parameter_bytes()
    alternative_suffixes_executed = 0
    factual_suffixes_audited = 0
    factual_trace_direct_equal = True
    factual_audit_actor_steps = 0
    for role in range(3):
        origin = origin_by_role[role]
        try:
            factual_audit_actor_steps += _audit_factual_suffix(
                model=model, environment=environment, origin=origin,
                factual_trace=factual_trace, action_uniforms=uniforms,
            )
        except ContractError:
            factual_trace_direct_equal = False
            raise
        factual_suffixes_audited += 1
    # Only after all three factual-label direct audits pass may the seven
    # nonfactual continuations consume environment/policy work.
    for role in range(3):
        origin = origin_by_role[role]
        factual_action = int(factual_actions[role].item())
        for action in LEGAL_ACTION_INDICES[role]:
            legal[role, action] = True
            if action == factual_action:
                # The factual Q is the cached J_base from this exact factual
                # trace.  Its identity binds the selected action, pre-step
                # origin snapshot/current teammate joint action, common tape
                # coordinate and terminal return without spending a redundant
                # environment or policy continuation.
                identity = (
                    bool(origin.environment_snapshot)
                    and int(origin.current_actions[origin.coordinate.entity].item())
                    == factual_action
                    and 0 <= origin.coordinate.slot < HORIZON
                    and np.isfinite(factual_return)
                )
                if not identity:
                    raise ContractError("cached factual Q identity contract is incomplete")
                q_targets[role, action] = factual_return
            else:
                q_targets[role, action] = _suffix_return(
                    model=model, environment=environment, origin=origin,
                    focal_action=action, action_uniforms=uniforms,
                )
                alternative_suffixes_executed += 1
    preupdate_model_bit_equal = model.parameter_bytes() == immutable_model_bytes
    if not preupdate_model_bit_equal:
        raise ContractError("counterfactual suffix mutated the pre-update model")
    audit = RSCFReplayAudit(
        alternative_suffixes_executed=alternative_suffixes_executed,
        factual_suffixes_audited=factual_suffixes_audited,
        factual_trace_direct_equal=factual_trace_direct_equal,
        factual_audit_actor_steps=factual_audit_actor_steps,
        new_rng_addresses=0,
        preupdate_model_bit_equal=preupdate_model_bit_equal,
    )
    if audit.alternative_suffixes_executed != 7 or audit.factual_suffixes_audited != 3:
        raise ContractError("RSCF replay did not execute the exact final suffix-audit work ledger")
    if audit_out is not None:
        if not isinstance(audit_out, dict) or audit_out:
            raise ContractError("RSCF audit output must be an empty mutable dictionary")
        audit_out.update({
            "alternative_suffixes_executed": audit.alternative_suffixes_executed,
            "factual_suffixes_audited": audit.factual_suffixes_audited,
            "factual_trace_direct_equal": audit.factual_trace_direct_equal,
            "factual_audit_actor_steps": audit.factual_audit_actor_steps,
            "new_rng_addresses": audit.new_rng_addresses,
            "preupdate_model_bit_equal": audit.preupdate_model_bit_equal,
        })

    factual_observations = torch.stack(observations_by_slot)
    if factual_roles is None:
        raise ContractError("factual rollout supplied no public roles")
    critic = model.critic_values(factual_observations, factual_roles)
    return RSCFEpisode(
        roster_size=roster,
        selected_probabilities=selected,
        q_targets=q_targets.detach(),
        legal_masks=legal,
        factual_actions=factual_actions,
        all_probabilities=torch.stack(probabilities_by_slot),
        critic_values=critic,
        terminal_return=torch.tensor(factual_return, dtype=torch.float32),
    )


class TestOnlyExternalEnvironment:
    """Deterministic explicit external-action adapter for bounded TEST_ONLY use."""

    __test__ = False
    TEST_ONLY = True
    production_admissible = False

    def __init__(self, roster: int) -> None:
        if roster not in (9, 15):
            raise ContractError("TEST_ONLY training roster must be 9 or 15")
        self.roster = roster
        counts = (roster // 3, roster // 3, roster - 2 * (roster // 3))
        self._roles = np.repeat(np.arange(3, dtype=np.int64), counts)
        self._slot = 0
        self._score = 0
        self._actions = 0
        self._previous_actions = np.full(roster, 255, dtype=np.int64)
        self._previous_success = np.zeros(roster, dtype=np.float32)

    def reset(self, environment_tape: object) -> None:
        del environment_tape
        self._slot = self._score = self._actions = 0
        self._previous_actions.fill(255)
        self._previous_success.fill(0.0)

    def observe(self) -> ExternalObservation:
        observations = np.zeros((self.roster, 22), dtype=np.float32)
        observations[np.arange(self.roster), self._roles] = 1.0
        observations[:, 3] = np.float32(min(self._slot, 11) / 11.0)
        observations[:, 4:7] = np.float32((self.roster // 3) / 7.0)
        for entity, action in enumerate(self._previous_actions):
            if 0 <= action < 6:
                observations[entity, 15 + action] = 1.0
        observations[:, 21] = self._previous_success
        legal_masks = np.zeros((self.roster, 6), dtype=np.bool_)
        for entity, role in enumerate(self._roles):
            legal_masks[entity, list(LEGAL_ACTION_INDICES[int(role)])] = True
        return ExternalObservation(
            observations, self._roles.copy(), legal_masks,
            self._slot, self._slot == HORIZON,
        )

    def step(self, actions: Sequence[int]) -> ExternalStep:
        if self._slot >= HORIZON or len(actions) != self.roster:
            raise ContractError("TEST_ONLY external step is outside its lane")
        for entity, action in enumerate(actions):
            if type(action) is not int or action not in LEGAL_ACTION_INDICES[int(self._roles[entity])]:
                raise ContractError("TEST_ONLY actor supplied an illegal external action")
        self._score += sum(int(action) for action in actions)
        self._actions += len(actions)
        self._previous_actions = np.asarray(actions, dtype=np.int64).copy()
        self._previous_success = np.asarray(
            [float(action != 5) for action in actions], dtype=np.float32
        )
        self._slot += 1
        terminal = self._slot == HORIZON
        dw = min(3, self._score % 4)
        de = min(3, (self._score // 4) % 4)
        waste = self._score / max(1, self._actions * 5)
        from .host import native_endpoint
        endpoint = native_endpoint(dw, de, waste)
        return ExternalStep(terminal, dw, de, waste, endpoint)

    def snapshot(self) -> bytes:
        return json.dumps(
            {
                "slot": self._slot, "score": self._score, "actions": self._actions,
                "previous_actions": self._previous_actions.tolist(),
                "previous_success": self._previous_success.tolist(),
            },
            sort_keys=True, separators=(",", ":"),
        ).encode("ascii")

    def restore(self, snapshot: bytes) -> None:
        try:
            state = json.loads(snapshot.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ContractError("TEST_ONLY snapshot is invalid") from exc
        if set(state) != {
            "slot", "score", "actions", "previous_actions", "previous_success",
        }:
            raise ContractError("TEST_ONLY snapshot fields differ")
        self._slot, self._score, self._actions = (
            int(state["slot"]), int(state["score"]), int(state["actions"])
        )
        self._previous_actions = np.asarray(state["previous_actions"], dtype=np.int64)
        self._previous_success = np.asarray(state["previous_success"], dtype=np.float32)


class PackageExternalActionEnvironment:
    """One logical lane backed by the package's batched native step ABI.

    Multiple instances may be grouped by a bounded worker around the same
    admitted adapter; every call here still crosses the native batch API.  No
    policy, action codec, RNG, or autonomous rollout is hidden in this bridge.
    """

    TEST_ONLY = False
    production_admissible = True

    def __init__(self, adapter: object, roster: int) -> None:
        from .native.native_abi import NativeStateV1
        from .native_adapter import admit_package_native_adapter

        if roster not in (6, 9, 15, 21):
            raise ContractError("native external environment roster is not registered")
        self._adapter = admit_package_native_adapter(adapter)
        self.roster = roster
        self._states = (NativeStateV1 * 1)()
        self._reset = False

    def reset(self, environment_tape: object) -> None:
        from .native.native_abi import ABI_VERSION, STATE_VERSION, ResetInputV1
        from .tapes import EpisodeTape, NativeEnvironmentTapePayload

        payload = (
            environment_tape.native_environment_payload()
            if isinstance(environment_tape, EpisodeTape) else environment_tape
        )
        if not isinstance(payload, NativeEnvironmentTapePayload) or payload.roster != self.roster:
            raise ContractError("native reset requires the directly bound episode tape payload")
        inputs = (ResetInputV1 * 1)()
        row = inputs[0]
        row.abi_version = ABI_VERSION
        row.state_version = STATE_VERSION
        row.roster = self.roster
        for basin in range(2):
            for ordinal in range(3):
                row.event_times[basin][ordinal] = int(payload.event_times[basin, ordinal])
        for slot in range(HORIZON):
            for sender in range(21):
                row.detection_uniforms[slot][sender] = float(payload.detection_uniforms[slot, sender])
                row.base_uniforms[slot][sender] = float(payload.base_uniforms[slot, sender])
                for receiver in range(21):
                    row.uplink_uniforms[slot][sender][receiver] = float(
                        payload.uplink_uniforms[slot, sender, receiver]
                    )
        self._adapter.reset_batch(self._states, inputs, batch_count=1)
        self._reset = True

    def observe(self) -> ExternalObservation:
        from .native.native_abi import ObservationOutputV1

        if not self._reset:
            raise ContractError("native environment must be reset before observation")
        outputs = (ObservationOutputV1 * 1)()
        self._adapter.observe_batch(self._states, outputs, batch_count=1)
        row = outputs[0]
        observations = np.asarray(
            [[float(row.observations[agent][field]) for field in range(22)]
             for agent in range(self.roster)], dtype=np.float32,
        )
        roles = np.asarray([int(row.roles[agent]) for agent in range(self.roster)], dtype=np.int64)
        legal_masks = np.asarray(
            [[bool(row.legal_masks[agent][action]) for action in range(6)]
             for agent in range(self.roster)], dtype=np.bool_,
        )
        return ExternalObservation(
            observations=observations, roles=roles, legal_masks=legal_masks,
            slot=int(row.slot),
            terminal=bool(row.terminal),
        )

    def step(self, actions: Sequence[int]) -> ExternalStep:
        from .host import native_endpoint
        from .native.native_abi import ABI_VERSION, StepInputV1, StepOutputV1

        if not self._reset or len(actions) != self.roster:
            raise ContractError("native external step requires one action per active entity")
        inputs = (StepInputV1 * 1)()
        inputs[0].abi_version = ABI_VERSION
        for entity, action in enumerate(actions):
            if type(action) is not int:
                raise ContractError("native external actions must be literal integers")
            inputs[0].actions[entity] = action
        outputs = (StepOutputV1 * 1)()
        self._adapter.step_batch(self._states, inputs, outputs, batch_count=1)
        metrics = outputs[0].metrics
        dw, de, waste = int(metrics.dw), int(metrics.de), float(metrics.waste)
        return ExternalStep(
            terminal=bool(outputs[0].terminal), dw=dw, de=de, waste=waste,
            terminal_return=native_endpoint(dw, de, waste),
        )

    def snapshot(self) -> bytes:
        if not self._reset:
            raise ContractError("native environment must be reset before snapshot")
        return self._adapter.snapshot_batch(self._states, batch_count=1)

    def restore(self, snapshot: bytes) -> None:
        self._adapter.restore_batch(self._states, snapshot, batch_count=1)
        self._reset = True


__all__ = [
    "ExternalObservation", "ExternalStep", "ExternalActionEnvironment",
    "OriginCoordinate", "OriginReplayState", "PairedUpdatePlan",
    "RSCFReplayAudit",
    "production_training_schedule", "assert_paired_initialization",
    "capture_rscf_episode", "TestOnlyExternalEnvironment",
    "PackageExternalActionEnvironment",
]
