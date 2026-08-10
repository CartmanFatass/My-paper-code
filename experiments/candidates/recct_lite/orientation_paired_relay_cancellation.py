"""Protected learner and analysis semantics for RECCT-B1.

This candidate-local module generalizes the accepted A1 intervention law to
the discrete orientation-paired relay host without modifying A1 or G40.  A
sealed capsule owns one complete live model/Adam/batch ancestry.  Four shadows
restore those bytes independently and a fifth commit recomputes from the same
capsule; only the commit may advance the bound live state.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import io
import json
import math
from typing import Mapping, Sequence

import torch
from torch import nn
from torch.nn import functional as F

from experiments.candidates.recct_lite import orientation_paired_relay_host as host


MASKS = ("00", "10", "01", "11")
ARMS = ("RECCT_SIGNED", "G_SD", "G_AGG_SYM", "ALL_11")
PROPOSAL_EPOCHS = (0, 2, 4, 6)
CONFIRMATION_EPOCHS_A = (1, 5)
CONFIRMATION_EPOCHS_B = (3, 7)
EDGE_COST_KAPPA = 0.0025
HYSTERESIS_MARGIN = 0.005
SUPPORT_REQUIRED = 4
RHO_REQUIRED = 0.75
GLOBAL_GRADIENT_CLIP = 0.5
LEARNING_RATE = 0.0003
BETAS = (0.9, 0.999)
EPSILON = 1e-8
PORT_SCHEMA = "recct-b1.role-relay-preaggregation.autodiff.v1"
MINT_PROVENANCE = "OrientationPairedRelayLearner.mint.v1"
RNG_SITES = ("learner/replay", "optimizer/adam", "selector/balanced_coin")


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _pack(value: object) -> bytes:
    stream = io.BytesIO()
    torch.save(value, stream)
    return stream.getvalue()


def _unpack(value: bytes) -> object:
    return torch.load(io.BytesIO(value), map_location="cpu", weights_only=False)


def _state_digest(state: Mapping[str, torch.Tensor]) -> str:
    rows = tuple(
        (name, tuple(tensor.shape), str(tensor.dtype), tensor.detach().cpu())
        for name, tensor in sorted(state.items())
    )
    return _digest(_pack(rows))


class RelayPolicy(nn.Module):
    """Exact shared 15->32 recurrent MultiDiscrete actor/critic architecture."""

    def __init__(self) -> None:
        super().__init__()
        self.encoder = nn.Linear(host.OBSERVATION_DIM, 32)
        self.recurrence = nn.GRUCell(32, 32)
        self.message_head = nn.Linear(32, 2)
        self.prediction_head = nn.Linear(32, 2)
        self.value_head = nn.Linear(32, 1)
        self.detached_return_head = nn.Linear(32, 1)

    def forward_roster(
        self,
        observations: torch.Tensor,
        roles: Sequence[str],
        hidden: torch.Tensor,
        ports: Sequence["DirectedPort"] = (),
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        if observations.ndim != 2 or observations.shape[1] != host.OBSERVATION_DIM:
            raise ValueError("relay policy requires [active,15] observations")
        if hidden.shape != (observations.shape[0], 32):
            raise ValueError("relay recurrent-state shape mismatch")
        roles_tuple = tuple(str(row) for row in roles)
        if len(roles_tuple) != observations.shape[0] or len(set(roles_tuple)) != len(
            roles_tuple
        ):
            raise ValueError("active graph roles must be unique and slot-aligned")
        port_by_pair = {(row.source_role, row.receiver_role): row for row in ports}
        if len(port_by_pair) != len(tuple(ports)):
            raise ValueError("directed preaggregation paths must be unique")

        encoded = torch.tanh(self.encoder(observations))
        receiver_contexts = []
        for receiver_index, receiver_role in enumerate(roles_tuple):
            del receiver_index
            source_terms = []
            for source_index, source_role in enumerate(roles_tuple):
                contribution = encoded[source_index]
                port = port_by_pair.get((source_role, receiver_role))
                if port is None:
                    term = contribution
                elif port.enabled:
                    term = contribution.detach() + float(port.perturbation) * (
                        contribution - contribution.detach()
                    )
                else:
                    term = contribution.detach()
                source_terms.append(term)
            receiver_contexts.append(torch.stack(source_terms).mean(dim=0))
        recurrent_input = encoded + torch.stack(receiver_contexts)
        next_hidden = self.recurrence(recurrent_input, hidden)
        return (
            self.message_head(next_hidden),
            self.prediction_head(next_hidden),
            self.value_head(next_hidden).squeeze(-1),
            torch.sigmoid(self.detached_return_head(next_hidden.detach())).squeeze(-1),
            next_hidden,
        )


def make_model(initialization_seed: int) -> RelayPolicy:
    state = torch.random.get_rng_state()
    try:
        torch.manual_seed(int(initialization_seed))
        return RelayPolicy()
    finally:
        torch.random.set_rng_state(state)


def make_optimizer(model: RelayPolicy) -> torch.optim.Adam:
    return torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
        betas=BETAS,
        eps=EPSILON,
        weight_decay=0.0,
    )


@dataclass(frozen=True)
class EpisodeStep:
    observations: torch.Tensor
    roles: tuple[str, ...]
    occupant_tokens: tuple[str, ...]
    state_reset: tuple[bool, ...]
    actions: torch.Tensor
    rewards: torch.Tensor
    epoch: int
    phase: int


@dataclass(frozen=True)
class EpisodeBatch:
    steps: tuple[EpisodeStep, ...]
    episode_metric: float
    exogenous_digest: str
    pool_kind: str

    def validate(self) -> None:
        if len(self.steps) != host.JOINT_STEPS:
            raise ValueError("sealed relay batch must contain 32 real host steps")
        if self.pool_kind not in {"training", "evaluation"}:
            raise ValueError("sealed batch pool kind is invalid")
        terminal_rewards = []
        for index, row in enumerate(self.steps):
            expected_epoch, expected_phase = divmod(index, host.PHASES_PER_EPOCH)
            if row.epoch != expected_epoch or row.phase != expected_phase:
                raise ValueError("sealed batch chronology mismatch")
            active = host.ACTIVE_COUNT_BY_EPOCH[row.epoch]
            if (
                row.observations.shape != (active, host.OBSERVATION_DIM)
                or row.actions.shape != (active, 2)
                or row.rewards.shape != (active,)
                or len(row.roles) != active
                or len(row.occupant_tokens) != active
                or len(row.state_reset) != active
            ):
                raise ValueError("sealed batch roster tensor shape mismatch")
            if not bool(torch.isfinite(row.observations).all()):
                raise ValueError("sealed batch observations are nonfinite")
            if row.phase < 3 and bool((row.rewards != 0).any()):
                raise ValueError("relay reward occurred before phase three")
            if row.phase == 3:
                if not bool((row.rewards == row.rewards[0]).all()):
                    raise ValueError("relay reward is not team-shared")
                terminal_rewards.append(float(row.rewards[0]))
        if len(terminal_rewards) != 8 or not math.isclose(
            self.episode_metric, sum(terminal_rewards) / 8.0, abs_tol=1e-8
        ):
            raise ValueError("episode metric is not the mean terminal reward")


@dataclass(frozen=True)
class CapsuleManifest:
    learner_instance: str
    policy_generation: str
    parent_digest: str
    model_digest: str
    optimizer_digest: str
    batch_digest: str
    rng_counters: tuple[tuple[str, int], ...]
    port_registry_digest: str
    payload_schema: str = PORT_SCHEMA


@dataclass(frozen=True)
class _HandleRecord:
    capsule_digest: str
    source_role: str
    receiver_role: str
    learner_instance: str
    opaque_id: str
    payload_schema: str
    mint_provenance: str


_HANDLE_TOKEN = object()


class OpaqueDirectedHandle:
    __slots__ = ("__opaque_id",)

    def __init__(self, token: object, opaque_id: str) -> None:
        if token is not _HANDLE_TOKEN:
            raise TypeError("directed handles are learner-minted only")
        self.__opaque_id = str(opaque_id)

    @property
    def opaque_id(self) -> str:
        return self.__opaque_id

    def __copy__(self) -> "OpaqueDirectedHandle":
        raise TypeError("opaque handles cannot be copied")

    def __deepcopy__(self, memo: object) -> "OpaqueDirectedHandle":
        del memo
        raise TypeError("opaque handles cannot be copied")


class SealedCapsule:
    __slots__ = (
        "__manifest",
        "__state_payload",
        "__batch_payload",
        "__digest",
        "__owner",
    )

    def __init__(
        self,
        manifest: CapsuleManifest,
        state_payload: bytes,
        batch_payload: bytes,
        digest: str,
        owner: "OrientationPairedRelayLearner",
    ) -> None:
        self.__manifest = manifest
        self.__state_payload = bytes(state_payload)
        self.__batch_payload = bytes(batch_payload)
        self.__digest = str(digest)
        self.__owner = owner

    @property
    def manifest(self) -> CapsuleManifest:
        return self.__manifest

    @property
    def digest(self) -> str:
        return self.__digest

    def _payloads(
        self, owner: "OrientationPairedRelayLearner"
    ) -> tuple[bytes, bytes]:
        if owner is not self.__owner:
            raise ValueError("capsule owner authentication failed")
        expected = _digest(
            _canonical(self.__manifest.__dict__)
            + self.__state_payload
            + self.__batch_payload
        )
        if expected != self.__digest:
            raise ValueError("sealed capsule digest mismatch")
        return self.__state_payload, self.__batch_payload

    def _owner(self) -> "OrientationPairedRelayLearner":
        return self.__owner


@dataclass(frozen=True)
class RNGClone:
    capsule_digest: str
    counters: tuple[tuple[str, int], ...]
    clone_id: str


@dataclass(frozen=True)
class DirectedPort:
    source_role: str
    receiver_role: str
    enabled: bool
    perturbation: float = 1.0


@dataclass(frozen=True)
class TransitionReceipt:
    call_kind: str
    mask: str
    lineage: str
    before_model_digest: str
    after_model_digest: str
    before_optimizer_digest: str
    after_optimizer_digest: str
    gradient: tuple[tuple[str, torch.Tensor], ...]
    loss: float
    preclip_gradient_norm: float
    committed_update_l2_norm: float
    optimizer_moment_delta_norm: float
    clipping_indicator: bool
    active_port_count: int
    confirmation_scores: tuple[tuple[str, float], ...]
    declared_path_count: int
    duplicate_path_count: int
    postaggregate_cancellation_path_count: int
    structural_preaggregation_gate: bool
    optimizer_transitions: int
    rng_counters_before: tuple[tuple[str, int], ...]
    rng_counters_after: tuple[tuple[str, int], ...]

    def transition_predicate(self) -> tuple[object, ...]:
        return (
            self.mask,
            self.before_model_digest,
            self.after_model_digest,
            self.before_optimizer_digest,
            self.after_optimizer_digest,
            tuple((name, tensor.detach().cpu()) for name, tensor in self.gradient),
            self.loss,
            self.preclip_gradient_norm,
            self.committed_update_l2_norm,
            self.optimizer_moment_delta_norm,
            self.clipping_indicator,
            self.active_port_count,
            self.confirmation_scores,
            self.declared_path_count,
            self.duplicate_path_count,
            self.postaggregate_cancellation_path_count,
            self.structural_preaggregation_gate,
            self.optimizer_transitions,
            self.rng_counters_before,
            self.rng_counters_after,
        )


@dataclass(frozen=True)
class CreditReceipt:
    credit_lr: float
    credit_rl: float
    support_lr: int
    support_rl: int
    rho_lr: float
    rho_rl: float
    conditional_lr: tuple[float, ...]
    conditional_rl: tuple[float, ...]


@dataclass(frozen=True)
class SelectionReceipt:
    capsule_digest: str
    arm: str
    selected_mask: str
    previous_mask: str
    credit: CreditReceipt
    balanced_coin: int
    selection_digest: str


def _optimizer_digest(optimizer: torch.optim.Adam) -> str:
    return _digest(_pack(copy.deepcopy(optimizer.state_dict())))


def _gradient_vector(receipt: TransitionReceipt) -> torch.Tensor:
    return torch.cat([tensor.reshape(-1).float() for _, tensor in receipt.gradient])


def _distance(left: TransitionReceipt, right: TransitionReceipt) -> float:
    return float(torch.linalg.vector_norm(_gradient_vector(left) - _gradient_vector(right)))


def directed_port_inventory(ports: Sequence[DirectedPort]) -> Mapping[str, object]:
    rows = tuple(ports)
    pairs = tuple((row.source_role, row.receiver_role) for row in rows)
    if (
        len(rows) != 2
        or set(pairs) != {("L", "R"), ("R", "L")}
        or len(set(pairs)) != len(pairs)
        or any(
            not isinstance(row.enabled, bool)
            or not math.isfinite(float(row.perturbation))
            or float(row.perturbation) <= 0.0
            for row in rows
        )
    ):
        raise ValueError("relay port inventory must be the two opposite declared edges")
    return {
        "declared_pairs": tuple(sorted(pairs)),
        "declared_path_count": 2,
        "duplicate_path_count": 0,
        "postaggregate_cancellation_path_count": 0,
        "structural_preaggregation_gate": True,
    }


def _directed_port_loss_preaggregation(
    model: RelayPolicy, ports: Sequence[DirectedPort]
) -> torch.Tensor:
    """Aggregate the two value-identical port terms before the loss sum.

    Every mask sees exactly the same scalar forward loss.  Only the derivative
    of the named term is enabled or detached, matching the receiver-context
    seam and avoiding an aggregate-then-cancel intervention.
    """

    directed_port_inventory(ports)
    coordinate = model.message_head.weight[0, 0]
    terms = {("L", "R"): coordinate, ("R", "L"): -coordinate}
    gated = []
    for port in ports:
        term = terms[(port.source_role, port.receiver_role)]
        if port.enabled:
            value = term.detach() + float(port.perturbation) * (
                term - term.detach()
            )
        else:
            value = term.detach()
        gated.append(value)
    return torch.stack(gated).sum()


def _replay(
    model: RelayPolicy,
    batch: EpisodeBatch,
    ports: Sequence[DirectedPort],
) -> Mapping[str, object]:
    batch.validate()
    hidden_by_occupant: dict[str, torch.Tensor] = {}
    proposal_logp = []
    proposal_entropy = []
    proposal_values = []
    proposal_targets = []
    confirmation_predictions: dict[str, list[torch.Tensor]] = {"A": [], "B": []}
    confirmation_targets: dict[str, list[torch.Tensor]] = {"A": [], "B": []}
    for row in batch.steps:
        hidden_rows = []
        for token, reset in zip(row.occupant_tokens, row.state_reset):
            if reset or token not in hidden_by_occupant:
                hidden_by_occupant[token] = torch.zeros((32,), dtype=torch.float32)
            hidden_rows.append(hidden_by_occupant[token])
        hidden = torch.stack(hidden_rows)
        message, prediction, values, returns, next_hidden = model.forward_roster(
            row.observations, row.roles, hidden, ports
        )
        for token, state in zip(row.occupant_tokens, next_hidden):
            hidden_by_occupant[token] = state
        message_logp = F.log_softmax(message, dim=-1).gather(
            1, row.actions[:, 0:1]
        ).squeeze(1)
        prediction_logp = F.log_softmax(prediction, dim=-1).gather(
            1, row.actions[:, 1:2]
        ).squeeze(1)
        entropy = (
            -(F.softmax(message, dim=-1) * F.log_softmax(message, dim=-1)).sum(-1)
            -(F.softmax(prediction, dim=-1) * F.log_softmax(prediction, dim=-1)).sum(-1)
        )
        terminal = float(batch.steps[row.epoch * 4 + 3].rewards[0])
        targets = torch.full_like(values, terminal)
        if row.epoch in PROPOSAL_EPOCHS:
            proposal_logp.append(message_logp + prediction_logp)
            proposal_entropy.append(entropy)
            proposal_values.append(values)
            proposal_targets.append(targets)
        half = "A" if row.epoch in CONFIRMATION_EPOCHS_A else (
            "B" if row.epoch in CONFIRMATION_EPOCHS_B else None
        )
        if half is not None:
            confirmation_predictions[half].append(returns)
            confirmation_targets[half].append(targets)
    logp = torch.cat(proposal_logp)
    entropy = torch.cat(proposal_entropy)
    values = torch.cat(proposal_values)
    targets = torch.cat(proposal_targets)
    advantages = targets - values.detach()
    advantages = (advantages - advantages.mean()) / advantages.std(unbiased=False).clamp_min(1e-8)
    actor = -(advantages * logp).mean()
    value_loss = F.mse_loss(values, targets)
    detached_bce = torch.stack(
        [
            F.binary_cross_entropy(
                torch.cat(confirmation_predictions[half]),
                torch.cat(confirmation_targets[half]),
            )
            for half in ("A", "B")
        ]
    ).mean()
    return {
        "base_loss": actor + 0.5 * value_loss - 0.01 * entropy.mean() + 0.25 * detached_bce,
        "confirmation_predictions": confirmation_predictions,
        "confirmation_targets": confirmation_targets,
    }


def _confirmation_scores(model: RelayPolicy, batch: EpisodeBatch) -> tuple[tuple[str, float], ...]:
    replay = _replay(
        model,
        batch,
        (DirectedPort("L", "R", True), DirectedPort("R", "L", True)),
    )
    predictions = replay["confirmation_predictions"]
    targets = replay["confirmation_targets"]
    rows = []
    for half in ("A", "B"):
        score = -F.binary_cross_entropy(
            torch.cat(predictions[half]), torch.cat(targets[half])
        )
        rows.append((half, float(score.detach())))
    return tuple(rows)


class OrientationPairedRelayLearner:
    """Sole owner of capsules, handles, shadows, selection, and live commit."""

    def __init__(self, learner_instance: str) -> None:
        if not learner_instance:
            raise ValueError("learner instance is required")
        self.learner_instance = str(learner_instance)
        self._registries: dict[str, dict[OpaqueDirectedHandle, _HandleRecord]] = {}
        self._pairs: dict[str, dict[tuple[str, str], OpaqueDirectedHandle]] = {}
        self._selections: dict[SelectionReceipt, str] = {}
        self._consumed_clones: set[str] = set()
        self._clone_count = 0
        self.learner_calls = 0
        self.optimizer_transitions = 0

    def seal_capsule(
        self,
        *,
        model: RelayPolicy,
        optimizer: torch.optim.Adam,
        batch: EpisodeBatch,
        policy_generation: str,
        parent_digest: str,
        rng_counters: Sequence[tuple[str, int]],
    ) -> SealedCapsule:
        batch.validate()
        counters = tuple((str(name), int(counter)) for name, counter in rng_counters)
        if tuple(name for name, _ in counters) != RNG_SITES or any(
            counter < 0 for _, counter in counters
        ):
            raise ValueError("capsule RNG sites must exactly match the allowlist")
        if not policy_generation or not parent_digest:
            raise ValueError("capsule ancestry is incomplete")
        if len(optimizer.param_groups) != 1:
            raise ValueError("capsule requires one Adam parameter group")
        group = optimizer.param_groups[0]
        if (
            not math.isclose(float(group["lr"]), LEARNING_RATE)
            or tuple(float(row) for row in group["betas"]) != BETAS
            or not math.isclose(float(group["eps"]), EPSILON)
            or float(group["weight_decay"]) != 0.0
        ):
            raise ValueError("Adam configuration left the frozen learner contract")
        state_payload = _pack(
            {
                "model": copy.deepcopy(model.state_dict()),
                "optimizer": copy.deepcopy(optimizer.state_dict()),
            }
        )
        batch_payload = _pack(batch)
        registry_rows = (("L", "R", PORT_SCHEMA), ("R", "L", PORT_SCHEMA))
        manifest = CapsuleManifest(
            learner_instance=self.learner_instance,
            policy_generation=str(policy_generation),
            parent_digest=str(parent_digest),
            model_digest=_state_digest(model.state_dict()),
            optimizer_digest=_optimizer_digest(optimizer),
            batch_digest=_digest(batch_payload),
            rng_counters=counters,
            port_registry_digest=_digest(_canonical(registry_rows)),
        )
        digest = _digest(_canonical(manifest.__dict__) + state_payload + batch_payload)
        capsule = SealedCapsule(manifest, state_payload, batch_payload, digest, self)
        registry: dict[OpaqueDirectedHandle, _HandleRecord] = {}
        pair_index: dict[tuple[str, str], OpaqueDirectedHandle] = {}
        for source, receiver, schema in registry_rows:
            opaque_id = _digest(
                _canonical(
                    (
                        digest,
                        source,
                        receiver,
                        self.learner_instance,
                        schema,
                        MINT_PROVENANCE,
                    )
                )
            )
            handle = OpaqueDirectedHandle(_HANDLE_TOKEN, opaque_id)
            registry[handle] = _HandleRecord(
                digest,
                source,
                receiver,
                self.learner_instance,
                opaque_id,
                schema,
                MINT_PROVENANCE,
            )
            pair_index[(source, receiver)] = handle
        self._registries[digest] = registry
        self._pairs[digest] = pair_index
        return capsule

    def handle(self, capsule: SealedCapsule, source_role: str, receiver_role: str) -> OpaqueDirectedHandle:
        if capsule._owner() is not self:
            raise ValueError("handle request used the wrong learner")
        try:
            return self._pairs[capsule.digest][(str(source_role), str(receiver_role))]
        except KeyError as exc:
            raise ValueError("directed role edge is absent") from exc

    def clone_rng(self, capsule: SealedCapsule) -> RNGClone:
        if capsule._owner() is not self:
            raise ValueError("RNG clone request used the wrong learner")
        self._clone_count += 1
        clone_id = _digest(
            _canonical((capsule.digest, capsule.manifest.rng_counters, self._clone_count))
        )
        return RNGClone(capsule.digest, capsule.manifest.rng_counters, clone_id)

    def _records(
        self,
        capsule: SealedCapsule,
        handles: Sequence[OpaqueDirectedHandle],
    ) -> tuple[_HandleRecord, _HandleRecord]:
        if len(tuple(handles)) != 2 or handles[0] is handles[1]:
            raise ValueError("two unique opaque handles are required")
        try:
            records = tuple(self._registries[capsule.digest][row] for row in handles)
        except (KeyError, TypeError) as exc:
            raise ValueError("directed handle provenance is absent") from exc
        if tuple((row.source_role, row.receiver_role) for row in records) != (
            ("L", "R"),
            ("R", "L"),
        ):
            raise ValueError("handles must use canonical opposite role order")
        if any(
            row.capsule_digest != capsule.digest
            or row.learner_instance != self.learner_instance
            or row.payload_schema != PORT_SCHEMA
            or row.mint_provenance != MINT_PROVENANCE
            or row.opaque_id != handle.opaque_id
            for row, handle in zip(records, handles)
        ):
            raise ValueError("directed handle authentication failed")
        return records  # type: ignore[return-value]

    def __transition(
        self,
        capsule: SealedCapsule,
        handles: Sequence[OpaqueDirectedHandle],
        mask: str,
        rng: RNGClone,
        *,
        call_kind: str,
    ) -> tuple[TransitionReceipt, bytes]:
        if mask not in MASKS or call_kind not in {"shadow", "commit"}:
            raise ValueError("invalid mask or transition kind")
        records = self._records(capsule, handles)
        if (
            rng.capsule_digest != capsule.digest
            or rng.counters != capsule.manifest.rng_counters
            or rng.clone_id in self._consumed_clones
        ):
            raise ValueError("counterfactual RNG clone is invalid or reused")
        self._consumed_clones.add(rng.clone_id)
        state_payload, batch_payload = capsule._payloads(self)
        state = _unpack(state_payload)
        batch = _unpack(batch_payload)
        if not isinstance(batch, EpisodeBatch) or _digest(batch_payload) != capsule.manifest.batch_digest:
            raise ValueError("sealed batch type or digest mismatch")
        model = RelayPolicy()
        model.load_state_dict(state["model"], strict=True)
        optimizer = make_optimizer(model)
        optimizer.load_state_dict(state["optimizer"])
        if (
            _state_digest(model.state_dict()) != capsule.manifest.model_digest
            or _optimizer_digest(optimizer) != capsule.manifest.optimizer_digest
        ):
            raise ValueError("sealed learner/optimizer ancestry mismatch")
        before_parameters = tuple(row.detach().clone() for row in model.parameters())
        before_moments = _optimizer_moment_vector(optimizer, model)
        ports = tuple(
            DirectedPort(row.source_role, row.receiver_role, bool(int(mask[index])))
            for index, row in enumerate(records)
        )
        inventory = directed_port_inventory(ports)
        replay = _replay(model, batch, ports)
        directed_loss = _directed_port_loss_preaggregation(model, ports)
        loss = replay["base_loss"] + 0.10 * directed_loss
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        gradient = tuple(
            (
                name,
                torch.zeros_like(parameter)
                if parameter.grad is None
                else parameter.grad.detach().clone(),
            )
            for name, parameter in model.named_parameters()
        )
        preclip = float(
            torch.sqrt(
                sum((tensor.float() ** 2).sum() for _, tensor in gradient)
            )
        )
        torch.nn.utils.clip_grad_norm_(model.parameters(), GLOBAL_GRADIENT_CLIP)
        optimizer.step()
        after_parameters = tuple(row.detach().clone() for row in model.parameters())
        update_norm = float(
            torch.sqrt(
                sum(
                    ((after - before).float() ** 2).sum()
                    for after, before in zip(after_parameters, before_parameters)
                )
            )
        )
        after_moments = _optimizer_moment_vector(optimizer, model)
        moment_delta = float(torch.linalg.vector_norm(after_moments - before_moments))
        after_state = {"model": model.state_dict(), "optimizer": optimizer.state_dict()}
        after_payload = _pack(after_state)
        self.learner_calls += 1
        self.optimizer_transitions += 1
        lineage = _digest(
            _canonical((capsule.digest, self.learner_calls, call_kind, mask, rng.clone_id))
        )
        receipt = TransitionReceipt(
            call_kind=call_kind,
            mask=mask,
            lineage=lineage,
            before_model_digest=capsule.manifest.model_digest,
            after_model_digest=_state_digest(model.state_dict()),
            before_optimizer_digest=capsule.manifest.optimizer_digest,
            after_optimizer_digest=_optimizer_digest(optimizer),
            gradient=gradient,
            loss=float(loss.detach()),
            preclip_gradient_norm=preclip,
            committed_update_l2_norm=update_norm,
            optimizer_moment_delta_norm=moment_delta,
            clipping_indicator=preclip > GLOBAL_GRADIENT_CLIP,
            active_port_count=mask.count("1"),
            confirmation_scores=_confirmation_scores(model, batch),
            declared_path_count=int(inventory["declared_path_count"]),
            duplicate_path_count=int(inventory["duplicate_path_count"]),
            postaggregate_cancellation_path_count=int(
                inventory["postaggregate_cancellation_path_count"]
            ),
            structural_preaggregation_gate=bool(inventory["structural_preaggregation_gate"]),
            optimizer_transitions=1,
            rng_counters_before=rng.counters,
            rng_counters_after=rng.counters,
        )
        return receipt, after_payload

    def shadow(
        self,
        capsule: SealedCapsule,
        handles: Sequence[OpaqueDirectedHandle],
        mask: str,
        rng: RNGClone,
    ) -> TransitionReceipt:
        receipt, _private_state_payload = self.__transition(
            capsule, handles, mask, rng, call_kind="shadow"
        )
        return receipt

    def select(
        self,
        capsule: SealedCapsule,
        arm: str,
        current_mask: str,
        shadows: Mapping[str, TransitionReceipt],
        balanced_coin: int,
    ) -> SelectionReceipt:
        if arm not in ARMS or current_mask not in MASKS or balanced_coin not in (0, 1):
            raise ValueError("selector input left the frozen domain")
        if tuple(shadows) != MASKS or any(
            row.call_kind != "shadow"
            or row.mask != mask
            or row.before_model_digest != capsule.manifest.model_digest
            for mask, row in shadows.items()
        ):
            raise ValueError("selector requires the four same-capsule pure shadows")
        credit = credit_from_shadows(shadows, absolute=(arm == "G_SD"))
        if arm == "G_AGG_SYM":
            # Direction labels are not consulted: both edge scores receive the
            # same aggregate magnitude and a site-keyed balanced coin chooses.
            magnitude = 0.5 * (
                0.5 * (_distance(shadows["10"], shadows["00"]) + _distance(shadows["11"], shadows["01"]))
                + 0.5 * (_distance(shadows["01"], shadows["00"]) + _distance(shadows["11"], shadows["10"]))
            )
            credit = CreditReceipt(magnitude, magnitude, 4, 4, 1.0, 1.0, (magnitude,) * 4, (magnitude,) * 4)
            selected = "10" if balanced_coin == 0 else "01"
        elif arm == "ALL_11":
            selected = "11"
        else:
            selected = select_credit_mask(credit, current_mask)
        selection_digest = _digest(
            _canonical((capsule.digest, arm, selected, current_mask, credit.__dict__, balanced_coin))
        )
        receipt = SelectionReceipt(
            capsule.digest,
            arm,
            selected,
            current_mask,
            credit,
            balanced_coin,
            selection_digest,
        )
        self._selections[receipt] = selection_digest
        return receipt

    def commit(
        self,
        capsule: SealedCapsule,
        handles: Sequence[OpaqueDirectedHandle],
        selection: SelectionReceipt,
        rng: RNGClone,
        *,
        live_model: RelayPolicy,
        live_optimizer: torch.optim.Adam,
    ) -> TransitionReceipt:
        if (
            capsule._owner() is not self
            or self._selections.get(selection) != selection.selection_digest
            or selection.capsule_digest != capsule.digest
            or _state_digest(live_model.state_dict()) != capsule.manifest.model_digest
            or _optimizer_digest(live_optimizer) != capsule.manifest.optimizer_digest
        ):
            raise ValueError("fresh commit selection or live ancestry failed")
        receipt, private_state_payload = self.__transition(
            capsule, handles, selection.selected_mask, rng, call_kind="commit"
        )
        state = _unpack(private_state_payload)
        live_model.load_state_dict(state["model"], strict=True)
        live_optimizer.load_state_dict(state["optimizer"])
        del self._selections[selection]
        return receipt


def _optimizer_moment_vector(
    optimizer: torch.optim.Adam, model: RelayPolicy
) -> torch.Tensor:
    rows = []
    for parameter in model.parameters():
        state = optimizer.state.get(parameter, {})
        for name in ("exp_avg", "exp_avg_sq"):
            rows.append(
                state.get(name, torch.zeros_like(parameter)).detach().reshape(-1).float()
            )
    return torch.cat(rows)


def credit_from_shadows(
    shadows: Mapping[str, TransitionReceipt], *, absolute: bool
) -> CreditReceipt:
    scores = {mask: dict(receipt.confirmation_scores) for mask, receipt in shadows.items()}
    lr = []
    rl = []
    for half in ("A", "B"):
        lr.extend((scores["10"][half] - scores["00"][half], scores["11"][half] - scores["01"][half]))
        rl.extend((scores["01"][half] - scores["00"][half], scores["11"][half] - scores["10"][half]))
    if absolute:
        lr = [abs(row) for row in lr]
        rl = [abs(row) for row in rl]
    credit_lr = sum(lr) / 4.0
    credit_rl = sum(rl) / 4.0

    def sign(value: float) -> int:
        return 1 if value > 0 else (-1 if value < 0 else 0)

    rho_lr = sum(sign(row) == sign(credit_lr) for row in lr) / 4.0
    rho_rl = sum(sign(row) == sign(credit_rl) for row in rl) / 4.0
    return CreditReceipt(
        credit_lr,
        credit_rl,
        len(lr),
        len(rl),
        rho_lr,
        rho_rl,
        tuple(lr),
        tuple(rl),
    )


def select_credit_mask(credit: CreditReceipt, current_mask: str) -> str:
    feasible_lr = credit.support_lr == SUPPORT_REQUIRED and credit.rho_lr >= RHO_REQUIRED
    feasible_rl = credit.support_rl == SUPPORT_REQUIRED and credit.rho_rl >= RHO_REQUIRED
    scores = {
        "00": 0.0,
        "10": credit.credit_lr - EDGE_COST_KAPPA if feasible_lr else -math.inf,
        "01": credit.credit_rl - EDGE_COST_KAPPA if feasible_rl else -math.inf,
        "11": (
            credit.credit_lr + credit.credit_rl - 2.0 * EDGE_COST_KAPPA
            if feasible_lr and feasible_rl
            else -math.inf
        ),
    }
    maximum = max(scores.values())
    if math.isfinite(scores[current_mask]) and maximum - scores[current_mask] <= HYSTERESIS_MARGIN:
        return current_mask
    for mask in MASKS:
        if scores[mask] == maximum:
            return mask
    raise AssertionError("zero mask must keep the selector feasible")


def geometry_receipt(model: RelayPolicy) -> Mapping[str, object]:
    coordinate = model.message_head.weight[0, 0]
    gradients = []
    for term in (coordinate, -coordinate):
        gradient = torch.autograd.grad(term, model.message_head.weight, retain_graph=True)[0]
        gradients.append(gradient.reshape(-1))
    norms = [float(torch.linalg.vector_norm(row)) for row in gradients]
    ratio = norms[0] / norms[1]
    cosine = float(F.cosine_similarity(gradients[0], gradients[1], dim=0))
    return {
        "shared_parameter": "message_head.weight",
        "shared_coordinate": (0, 0),
        "isolated_gradient_norm_ratio": ratio,
        "shared_coordinate_cosine": cosine,
        "support_per_port_per_update": 4,
        "identifying": 0.99 <= ratio <= 1.01 and cosine <= -0.99,
    }


def factorial_gradient_residual(shadows: Mapping[str, TransitionReceipt]) -> float:
    residual = (
        _gradient_vector(shadows["11"])
        - _gradient_vector(shadows["10"])
        - _gradient_vector(shadows["01"])
        + _gradient_vector(shadows["00"])
    )
    return float(torch.linalg.vector_norm(residual))


def run_update(
    learner: OrientationPairedRelayLearner,
    capsule: SealedCapsule,
    handles: Sequence[OpaqueDirectedHandle],
    arm: str,
    current_mask: str,
    balanced_coin: int,
    *,
    live_model: RelayPolicy,
    live_optimizer: torch.optim.Adam,
) -> tuple[Mapping[str, TransitionReceipt], SelectionReceipt, TransitionReceipt]:
    """Exactly four pure shadows plus one independent fifth live commit."""

    shadows = {
        mask: learner.shadow(capsule, handles, mask, learner.clone_rng(capsule))
        for mask in MASKS
    }
    selection = learner.select(capsule, arm, current_mask, shadows, balanced_coin)
    commit = learner.commit(
        capsule,
        handles,
        selection,
        learner.clone_rng(capsule),
        live_model=live_model,
        live_optimizer=live_optimizer,
    )
    return shadows, selection, commit
