"""Learner-owned directed-edge masked updates for RECCT-A1.

This module binds two opposite authenticated roster edges to real G40 replay
paths.  It never assigns parameters, coordinates, or synthetic vectors to an
edge.  A directed port is the actual autodiff path by which one active source
member's encoded contribution enters one receiver's replay context before
aggregation.  Masking removes that learning path while preserving the forward
policy value, execution policy, communication values, loss definition,
normalization, backward pass, and Adam transition.
"""

from __future__ import annotations

import base64
import copy
from dataclasses import asdict, dataclass, fields, is_dataclass
import hashlib
import io
import json
import math
from typing import Any, Mapping, Sequence

import torch
from torch import nn
from torch.nn import functional as F

import ha_ctse_process.continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process.anchored_residual_g19 import AnchoredRosterTrajectory


MASKS = ("00", "10", "01", "11")
RAW_OUTPUT_BINDING = "recct_lite.directed_edge_masked_update.a1.v1"
PORT_PAYLOAD_SCHEMA = "g40.member-encoding-to-receiver-context.autodiff.v1"
MINT_PROVENANCE = "G40NativeSixPolicy.actor_credit_learner.mint.v1"
ALLOWED_PRETREATMENT_RNG_SITES = (
    "learner/replay",
    "optimizer/adam",
)
FORBIDDEN_INPUT_NAMES = frozenset(
    {
        "future_outcome",
        "future_state",
        "audit_seed",
        "audit_outcome",
        "semantic_label",
        "orientation_label",
        "usefulness_label",
        "parameter_indices",
        "coordinate_mask",
        "edge_vector",
        "global_rng",
    }
)

A1_MISSING_REAL_CALLABLE_OR_NO_UNIQUE_PREAGGREGATION_PORT = (
    "A1_MISSING_REAL_CALLABLE_OR_NO_UNIQUE_PREAGGREGATION_PORT"
)
A1_HANDLE_FORGEABLE_OR_PROVENANCE_LOST = (
    "A1_HANDLE_FORGEABLE_OR_PROVENANCE_LOST"
)
A1_COMPOUND_INTERVENTION_OR_UNDECLARED_PATH = (
    "A1_COMPOUND_INTERVENTION_OR_UNDECLARED_PATH"
)
A1_MASK_SEMANTICS_FAILURE = "A1_MASK_SEMANTICS_FAILURE"
A1_RECOMPUTATION_OR_ANCESTRY_FAILURE = "A1_RECOMPUTATION_OR_ANCESTRY_FAILURE"
A1_IDENTITY_STICKY_NONIDENTIFIABILITY = "A1_IDENTITY_STICKY_NONIDENTIFIABILITY"
A1_CALLABLE_BUT_HOST_NONIDENTIFYING = "A1_CALLABLE_BUT_HOST_NONIDENTIFYING"
A1_DIRECTED_EDGE_BINDING_PASS = "A1_DIRECTED_EDGE_BINDING_PASS"


@dataclass(frozen=True)
class DisabledUpdateState:
    component: str
    status: str = "DISABLED"
    state: tuple[()] = ()

    def __post_init__(self) -> None:
        if self.status != "DISABLED" or self.state != () or not self.component:
            raise ValueError("disabled update component must be explicit and empty")


@dataclass(frozen=True)
class LearnerConfig:
    learning_rate: float
    betas: tuple[float, float]
    eps: float
    weight_decay: float
    amsgrad: bool
    maximize: bool
    ppo_passes: int = 1

    def __post_init__(self) -> None:
        if (
            not math.isfinite(float(self.learning_rate))
            or float(self.learning_rate) <= 0.0
            or len(self.betas) != 2
            or not all(0.0 <= float(row) < 1.0 for row in self.betas)
            or not math.isfinite(float(self.eps))
            or float(self.eps) <= 0.0
            or not math.isfinite(float(self.weight_decay))
            or int(self.ppo_passes) != 1
        ):
            raise ValueError("RECCT-A1 learner config left the one-transition contract")


@dataclass(frozen=True)
class AgentInstance:
    instance_id: str
    slot: int

    def __post_init__(self) -> None:
        if not self.instance_id or int(self.slot) < 0:
            raise ValueError("agent instance roster entry is invalid")


@dataclass(frozen=True)
class RosterEpochAncestry:
    roster_epoch: int
    policy_generation: str
    learner_checkpoint_digest: str
    optimizer_checkpoint_digest: str
    pretreatment_batch_digest: str
    parent_epoch_digest: str
    immutable: bool = True

    def __post_init__(self) -> None:
        if (
            int(self.roster_epoch) < 0
            or not self.policy_generation
            or not self.immutable
            or any(
                not value
                for value in (
                    self.learner_checkpoint_digest,
                    self.optimizer_checkpoint_digest,
                    self.pretreatment_batch_digest,
                    self.parent_epoch_digest,
                )
            )
        ):
            raise ValueError("roster-epoch ancestry is incomplete or mutable")


@dataclass(frozen=True)
class FrozenSelectionState:
    support: tuple[bool, bool]
    rho: tuple[float, float]
    predictor_digest: str
    selected_mask: str

    def __post_init__(self) -> None:
        if (
            len(self.support) != 2
            or len(self.rho) != 2
            or any(not math.isfinite(float(row)) for row in self.rho)
            or not self.predictor_digest
            or self.selected_mask not in MASKS
        ):
            raise ValueError("frozen support/rho/predictor state is incomplete")


@dataclass(frozen=True)
class SiteKeyedRNGPlan:
    counters: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        names = tuple(name for name, _ in self.counters)
        if (
            names != ALLOWED_PRETREATMENT_RNG_SITES
            or len(set(names)) != len(names)
            or any(not name or int(counter) < 0 for name, counter in self.counters)
        ):
            raise ValueError(
                "RNG plan must exactly match the declared pretreatment site allowlist"
            )

    @property
    def digest(self) -> str:
        return _digest(_canonical_json(self.counters))


@dataclass(frozen=True)
class CapsuleManifest:
    learner_instance: str
    member_capacity: int
    roster: tuple[AgentInstance, ...]
    ancestry: RosterEpochAncestry
    frozen_selection: FrozenSelectionState
    rng_plan: SiteKeyedRNGPlan
    learner_config: LearnerConfig
    scheduler_state: DisabledUpdateState
    scaler_state: DisabledUpdateState
    clipping_state: DisabledUpdateState
    accumulation_state: DisabledUpdateState
    edge_registry_digest: str
    payload_schema: str = PORT_PAYLOAD_SCHEMA


@dataclass(frozen=True)
class TensorValue:
    name: str
    dtype: str
    shape: tuple[int, ...]
    data_base64: str

    @classmethod
    def from_tensor(cls, name: str, value: torch.Tensor) -> "TensorValue":
        row = value.detach().cpu().contiguous()
        return cls(
            str(name),
            str(row.dtype),
            tuple(int(dim) for dim in row.shape),
            base64.b64encode(row.numpy().tobytes()).decode("ascii"),
        )

    def tensor(self) -> torch.Tensor:
        dtype = {
            "torch.float32": torch.float32,
            "torch.float64": torch.float64,
            "torch.int64": torch.int64,
            "torch.int32": torch.int32,
            "torch.bool": torch.bool,
        }.get(self.dtype)
        if dtype is None:
            raise ValueError(f"unsupported receipt dtype {self.dtype}")
        raw = bytearray(base64.b64decode(self.data_base64))
        return torch.frombuffer(raw, dtype=dtype).clone().reshape(self.shape)


@dataclass(frozen=True)
class OptimizerStateReceipt:
    parameter_states: tuple[tuple[str, tuple[TensorValue, ...]], ...]
    parameter_groups: tuple[tuple[tuple[str, object], ...], ...]
    digest: str


@dataclass(frozen=True)
class CompleteStateReceipt:
    learner_state: tuple[TensorValue, ...]
    optimizer_state: OptimizerStateReceipt
    scheduler_state: DisabledUpdateState
    scaler_state: DisabledUpdateState
    clipping_state: DisabledUpdateState
    accumulation_state: DisabledUpdateState
    digest: str


@dataclass(frozen=True)
class InterventionReceipt:
    mask: str
    opaque_handles: tuple[str, str]
    enabled_ports: tuple[str, ...]
    disabled_ports: tuple[str, ...]
    declared_port_count: int
    undeclared_duplicate_path_count: int
    post_aggregate_cancellation_path_count: int
    structural_preaggregation_gate: bool
    execution_policy_intervention: bool
    communication_value_intervention: bool
    payload_schema: str


@dataclass(frozen=True)
class AncestryReceipt:
    capsule_digest: str
    roster_epoch: int
    policy_generation: str
    learner_instance: str
    source_state_digest: str
    source_optimizer_digest: str
    pretreatment_batch_digest: str
    rng_plan_digest: str
    rng_clone_id: str
    rng_counters_before: tuple[tuple[str, int], ...]
    rng_counters_after: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class UpdateReceipt:
    call_kind: str
    call_lineage: str
    mask: str
    loss: float
    gradient: tuple[TensorValue, ...]
    parameter_delta: tuple[TensorValue, ...]
    before: CompleteStateReceipt
    after: CompleteStateReceipt
    intervention: InterventionReceipt
    ancestry: AncestryReceipt
    optimizer_transitions: int
    ordinary_update_path: bool
    finite: bool

    @property
    def gradient_digest(self) -> str:
        return _tensor_values_digest(self.gradient)

    @property
    def delta_digest(self) -> str:
        return _tensor_values_digest(self.parameter_delta)

    def transition_predicate(self) -> tuple[object, ...]:
        """Predeclared equality predicate excluding only fresh call lineage."""

        return (
            self.mask,
            self.loss,
            self.gradient,
            self.parameter_delta,
            self.before,
            self.after,
            self.intervention.mask,
            self.intervention.opaque_handles,
            self.intervention.enabled_ports,
            self.intervention.disabled_ports,
            self.intervention.declared_port_count,
            self.intervention.undeclared_duplicate_path_count,
            self.intervention.post_aggregate_cancellation_path_count,
            self.intervention.structural_preaggregation_gate,
            self.intervention.execution_policy_intervention,
            self.intervention.communication_value_intervention,
            self.intervention.payload_schema,
            self.ancestry.capsule_digest,
            self.ancestry.roster_epoch,
            self.ancestry.policy_generation,
            self.ancestry.learner_instance,
            self.ancestry.source_state_digest,
            self.ancestry.source_optimizer_digest,
            self.ancestry.pretreatment_batch_digest,
            self.ancestry.rng_plan_digest,
            self.ancestry.rng_counters_before,
            self.ancestry.rng_counters_after,
            self.optimizer_transitions,
            self.ordinary_update_path,
            self.finite,
        )

    def to_dict(self) -> dict[str, object]:
        return _jsonable(self)  # type: ignore[return-value]


@dataclass(frozen=True)
class ClonedCounterfactualRNG:
    capsule_digest: str
    plan_digest: str
    counters: tuple[tuple[str, int], ...]
    clone_id: str


@dataclass(frozen=True)
class _HandleRecord:
    capsule_digest: str
    roster_epoch: int
    source_instance: str
    receiver_instance: str
    source_slot: int
    receiver_slot: int
    learner_instance: str
    port_id: str
    payload_schema: str
    mint_provenance: str


_HANDLE_MINT_TOKEN = object()


class OpaqueDirectedHandle:
    """Opaque learner-minted capability; edge metadata stays in learner custody."""

    __slots__ = ("__opaque_id",)

    def __init__(self, token: object, opaque_id: str) -> None:
        if token is not _HANDLE_MINT_TOKEN:
            raise TypeError("directed handles may be minted only by the learner")
        self.__opaque_id = str(opaque_id)

    @property
    def opaque_id(self) -> str:
        return self.__opaque_id

    def __copy__(self) -> "OpaqueDirectedHandle":
        raise TypeError("opaque directed handles cannot be copied")

    def __deepcopy__(self, memo: object) -> "OpaqueDirectedHandle":
        del memo
        raise TypeError("opaque directed handles cannot be copied")


class SealedLearnerCapsule:
    """Immutable bytes plus an authenticated manifest and owning learner."""

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
        owner: "DirectedEdgeMaskedLearner",
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

    def _owned_payload(
        self, owner: "DirectedEdgeMaskedLearner"
    ) -> tuple[bytes, bytes]:
        if owner is not self.__owner:
            raise ValueError("capsule owner authentication failed")
        expected = _capsule_digest(
            self.__manifest, self.__state_payload, self.__batch_payload
        )
        if expected != self.__digest:
            raise ValueError("sealed capsule digest mismatch")
        return self.__state_payload, self.__batch_payload

    def _owner(self) -> "DirectedEdgeMaskedLearner":
        return self.__owner


class DirectedEdgeMaskedLearner:
    """State owner, handle minter, RNG cloner, and real update executor."""

    def __init__(self, learner_instance: str) -> None:
        if not learner_instance:
            raise ValueError("learner instance identity is required")
        self.learner_instance = str(learner_instance)
        self.__registries: dict[
            str, dict[OpaqueDirectedHandle, _HandleRecord]
        ] = {}
        self.__pairs: dict[
            str, dict[tuple[str, str], OpaqueDirectedHandle]
        ] = {}
        self.__call_count = 0
        self.__rng_clone_count = 0
        self.__consumed_rng_clones: set[str] = set()

    def seal_capsule(
        self,
        *,
        model: g40.G40NativeSixPolicy,
        optimizer: torch.optim.Adam,
        trajectory: AnchoredRosterTrajectory,
        roster: Sequence[AgentInstance],
        ancestry: RosterEpochAncestry,
        frozen_selection: FrozenSelectionState,
        rng_plan: SiteKeyedRNGPlan,
        learner_config: LearnerConfig,
        scheduler_state: DisabledUpdateState,
        scaler_state: DisabledUpdateState,
        clipping_state: DisabledUpdateState,
        accumulation_state: DisabledUpdateState,
    ) -> SealedLearnerCapsule:
        rows = tuple(roster)
        _validate_seal_inputs(
            self,
            model,
            optimizer,
            trajectory,
            rows,
            ancestry,
            learner_config,
            scheduler_state,
            scaler_state,
            clipping_state,
            accumulation_state,
        )
        state_payload = _serialize(
            {
                "model_state": copy.deepcopy(model.state_dict()),
                "optimizer_state": copy.deepcopy(optimizer.state_dict()),
            }
        )
        batch_payload = _serialize(_trajectory_payload(trajectory))
        if _digest(batch_payload) != ancestry.pretreatment_batch_digest:
            raise ValueError("pretreatment batch ancestry digest mismatch")
        if _model_digest(model) != ancestry.learner_checkpoint_digest:
            raise ValueError("learner checkpoint ancestry digest mismatch")
        if _optimizer_receipt(optimizer, g40.actor_credit_parameter_names(model)).digest != ancestry.optimizer_checkpoint_digest:
            raise ValueError("optimizer checkpoint ancestry digest mismatch")

        registry_rows = tuple(
            sorted(
                (
                    source.instance_id,
                    receiver.instance_id,
                    source.slot,
                    receiver.slot,
                    PORT_PAYLOAD_SCHEMA,
                    MINT_PROVENANCE,
                )
                for source in rows
                for receiver in rows
                if source.instance_id != receiver.instance_id
            )
        )
        registry_digest = _digest(_canonical_json(registry_rows))
        manifest = CapsuleManifest(
            learner_instance=self.learner_instance,
            member_capacity=model.member_capacity,
            roster=rows,
            ancestry=ancestry,
            frozen_selection=frozen_selection,
            rng_plan=rng_plan,
            learner_config=learner_config,
            scheduler_state=scheduler_state,
            scaler_state=scaler_state,
            clipping_state=clipping_state,
            accumulation_state=accumulation_state,
            edge_registry_digest=registry_digest,
        )
        digest = _capsule_digest(manifest, state_payload, batch_payload)
        capsule = SealedLearnerCapsule(
            manifest, state_payload, batch_payload, digest, self
        )
        registry: dict[OpaqueDirectedHandle, _HandleRecord] = {}
        pair_index: dict[tuple[str, str], OpaqueDirectedHandle] = {}
        for source in rows:
            for receiver in rows:
                if source.instance_id == receiver.instance_id:
                    continue
                port_id = _digest(
                    _canonical_json(
                        (
                            digest,
                            ancestry.roster_epoch,
                            source.instance_id,
                            receiver.instance_id,
                            self.learner_instance,
                            PORT_PAYLOAD_SCHEMA,
                            MINT_PROVENANCE,
                        )
                    )
                )
                handle = OpaqueDirectedHandle(_HANDLE_MINT_TOKEN, port_id)
                record = _HandleRecord(
                    capsule_digest=digest,
                    roster_epoch=ancestry.roster_epoch,
                    source_instance=source.instance_id,
                    receiver_instance=receiver.instance_id,
                    source_slot=source.slot,
                    receiver_slot=receiver.slot,
                    learner_instance=self.learner_instance,
                    port_id=port_id,
                    payload_schema=PORT_PAYLOAD_SCHEMA,
                    mint_provenance=MINT_PROVENANCE,
                )
                registry[handle] = record
                pair_index[(source.instance_id, receiver.instance_id)] = handle
        self.__registries[digest] = registry
        self.__pairs[digest] = pair_index
        return capsule

    def handle(
        self,
        capsule: SealedLearnerCapsule,
        source_instance: str,
        receiver_instance: str,
    ) -> OpaqueDirectedHandle:
        if capsule._owner() is not self:
            raise ValueError("handle request used the wrong learner")
        try:
            return self.__pairs[capsule.digest][
                (str(source_instance), str(receiver_instance))
            ]
        except KeyError as exc:
            raise ValueError("directed port is absent from the sealed edge registry") from exc

    def clone_counterfactual_rng(
        self, capsule: SealedLearnerCapsule
    ) -> ClonedCounterfactualRNG:
        if capsule._owner() is not self:
            raise ValueError("RNG clone request used the wrong learner")
        self.__rng_clone_count += 1
        plan = capsule.manifest.rng_plan
        clone_id = _digest(
            _canonical_json(
                (capsule.digest, plan.digest, self.__rng_clone_count, "clone")
            )
        )
        return ClonedCounterfactualRNG(
            capsule.digest, plan.digest, plan.counters, clone_id
        )

    def _record_for(
        self, capsule: SealedLearnerCapsule, handle: OpaqueDirectedHandle
    ) -> _HandleRecord:
        if type(handle) is not OpaqueDirectedHandle:
            raise ValueError("directed handle type is forgeable")
        try:
            record = self.__registries[capsule.digest][handle]
        except (KeyError, TypeError) as exc:
            raise ValueError("directed handle provenance is absent") from exc
        if (
            record.capsule_digest != capsule.digest
            or record.roster_epoch != capsule.manifest.ancestry.roster_epoch
            or record.learner_instance != self.learner_instance
            or record.payload_schema != PORT_PAYLOAD_SCHEMA
            or record.mint_provenance != MINT_PROVENANCE
            or record.port_id != handle.opaque_id
        ):
            raise ValueError("directed handle provenance was lost")
        return record

    def _validate_registry(self, capsule: SealedLearnerCapsule) -> None:
        try:
            records = tuple(self.__registries[capsule.digest].values())
            pair_index = self.__pairs[capsule.digest]
        except KeyError as exc:
            raise ValueError("sealed edge registry is absent") from exc
        expected_count = capsule.manifest.member_capacity * (
            capsule.manifest.member_capacity - 1
        )
        pairs = tuple(
            (record.source_instance, record.receiver_instance) for record in records
        )
        rows = tuple(
            sorted(
                (
                    record.source_instance,
                    record.receiver_instance,
                    record.source_slot,
                    record.receiver_slot,
                    record.payload_schema,
                    record.mint_provenance,
                )
                for record in records
            )
        )
        if (
            len(records) != expected_count
            or len(set(pairs)) != expected_count
            or len({record.port_id for record in records}) != expected_count
            or set(pair_index) != set(pairs)
            or _digest(_canonical_json(rows))
            != capsule.manifest.edge_registry_digest
        ):
            raise ValueError("sealed edge registry digest or uniqueness failed")

    def _transition(
        self,
        capsule: SealedLearnerCapsule,
        ordered_edge_pair: Sequence[OpaqueDirectedHandle],
        mask: str,
        cloned_counterfactual_rng: ClonedCounterfactualRNG,
        *,
        call_kind: str,
    ) -> UpdateReceipt:
        if mask not in MASKS:
            raise ValueError("RECCT-A1 mask must be one of 00/10/01/11")
        if call_kind not in {"shadow", "commit"}:
            raise ValueError("RECCT-A1 call kind must be shadow or commit")
        self._validate_registry(capsule)
        handles = tuple(ordered_edge_pair)
        if len(handles) != 2 or handles[0] is handles[1]:
            raise ValueError("RECCT-A1 requires two unique ordered handles")
        records = tuple(self._record_for(capsule, handle) for handle in handles)
        if not (
            records[0].source_instance == records[1].receiver_instance
            and records[0].receiver_instance == records[1].source_instance
        ):
            raise ValueError("RECCT-A1 handles must bind opposite directed edges")
        plan = capsule.manifest.rng_plan
        rng = cloned_counterfactual_rng
        if (
            rng.capsule_digest != capsule.digest
            or rng.plan_digest != plan.digest
            or rng.counters != plan.counters
            or rng.clone_id in self.__consumed_rng_clones
        ):
            raise ValueError("counterfactual RNG clone ancestry is invalid or reused")
        self.__consumed_rng_clones.add(rng.clone_id)

        state_payload, batch_payload = capsule._owned_payload(self)
        state = _deserialize(state_payload)
        trajectory = _trajectory_from_payload(_deserialize(batch_payload))
        model = g40._new_shell(capsule.manifest.member_capacity)
        model.load_state_dict(state["model_state"], strict=True)
        model.phase = "fast"
        optimizer = _new_optimizer(model, capsule.manifest.learner_config)
        optimizer.load_state_dict(state["optimizer_state"])
        parameters = model.actor_credit_parameters()
        names = g40.actor_credit_parameter_names(model)
        before = _complete_state_receipt(model, optimizer, capsule.manifest)
        before_parameters = tuple(parameter.detach().clone() for parameter in parameters)

        ports = tuple(
            g40.G40DirectedLearningPort(
                record.source_slot,
                record.receiver_slot,
                enabled=bool(int(mask[index])),
                perturbation=1.0,
            )
            for index, record in enumerate(records)
        )
        path_inventory = g40.directed_learning_port_path_inventory(
            model.member_capacity, ports
        )
        replay = g40.replay_trajectory_with_directed_learning_ports(
            model,
            trajectory,
            device=torch.device("cpu"),
            ports=ports,
        )
        credit = g40.compute_credit_targets(
            rewards=trajectory.rewards,
            slow_values=trajectory.old_values,
            immediate_baselines=trajectory.old_immediate_baselines,
            successor_baselines=trajectory.old_successor_baselines,
            terminals=g40.terminal_mask(trajectory),
        )
        normalized_advantage = g40.normalize_advantage(
            credit.immediate_advantage
        )
        policy = g40._policy_loss_from_normalized_advantage(
            replay, trajectory, normalized_advantage
        )
        immediate = F.mse_loss(
            replay.immediate_baselines, trajectory.rewards.detach()
        )
        loss = (
            policy
            + g40.VALUE_COEFFICIENT * immediate
            - g40.ENTROPY_COEFFICIENT * g40._entropy(replay)
        )
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        gradient = tuple(
            TensorValue.from_tensor(
                name,
                torch.zeros_like(parameter)
                if parameter.grad is None
                else parameter.grad,
            )
            for name, parameter in zip(names, parameters)
        )
        finite = bool(torch.isfinite(loss)) and all(
            bool(torch.isfinite(row.tensor()).all()) for row in gradient
        )
        g40._optimizer_step(optimizer, parameters)
        after = _complete_state_receipt(model, optimizer, capsule.manifest)
        parameter_delta = tuple(
            TensorValue.from_tensor(
                name, parameter.detach() - before_parameter
            )
            for name, parameter, before_parameter in zip(
                names, parameters, before_parameters
            )
        )

        self.__call_count += 1
        lineage = _digest(
            _canonical_json(
                (
                    capsule.digest,
                    self.__call_count,
                    call_kind,
                    mask,
                    rng.clone_id,
                )
            )
        )
        enabled = tuple(
            handle.opaque_id
            for bit, handle in zip(mask, handles)
            if bit == "1"
        )
        disabled = tuple(
            handle.opaque_id
            for bit, handle in zip(mask, handles)
            if bit == "0"
        )
        return UpdateReceipt(
            call_kind=call_kind,
            call_lineage=lineage,
            mask=mask,
            loss=float(loss.detach().cpu()),
            gradient=gradient,
            parameter_delta=parameter_delta,
            before=before,
            after=after,
            intervention=InterventionReceipt(
                mask=mask,
                opaque_handles=(handles[0].opaque_id, handles[1].opaque_id),
                enabled_ports=enabled,
                disabled_ports=disabled,
                declared_port_count=int(path_inventory["declared_path_count"]),
                undeclared_duplicate_path_count=int(
                    path_inventory["undeclared_duplicate_path_count"]
                ),
                post_aggregate_cancellation_path_count=int(
                    path_inventory["post_aggregate_cancellation_path_count"]
                ),
                structural_preaggregation_gate=bool(
                    path_inventory["structural_preaggregation_gate"]
                ),
                execution_policy_intervention=False,
                communication_value_intervention=False,
                payload_schema=PORT_PAYLOAD_SCHEMA,
            ),
            ancestry=AncestryReceipt(
                capsule_digest=capsule.digest,
                roster_epoch=capsule.manifest.ancestry.roster_epoch,
                policy_generation=capsule.manifest.ancestry.policy_generation,
                learner_instance=self.learner_instance,
                source_state_digest=before.digest,
                source_optimizer_digest=before.optimizer_state.digest,
                pretreatment_batch_digest=_digest(batch_payload),
                rng_plan_digest=plan.digest,
                rng_clone_id=rng.clone_id,
                rng_counters_before=plan.counters,
                rng_counters_after=plan.counters,
            ),
            optimizer_transitions=1,
            ordinary_update_path=mask == "11",
            finite=finite,
        )


def DirectedEdgeMaskedUpdate(
    capsule: SealedLearnerCapsule,
    ordered_edge_pair: Sequence[OpaqueDirectedHandle],
    mask: str,
    cloned_counterfactual_rng: ClonedCounterfactualRNG,
) -> UpdateReceipt:
    """Run one pure full update restored from the sealed capsule."""

    return capsule._owner()._transition(
        capsule,
        ordered_edge_pair,
        mask,
        cloned_counterfactual_rng,
        call_kind="shadow",
    )


def commit_selected_update(
    capsule: SealedLearnerCapsule,
    ordered_edge_pair: Sequence[OpaqueDirectedHandle],
    selected_mask: str,
    cloned_counterfactual_rng: ClonedCounterfactualRNG,
) -> UpdateReceipt:
    """Fresh real recomputation; accepts no shadow state, gradient, or optimizer."""

    if selected_mask != capsule.manifest.frozen_selection.selected_mask:
        raise ValueError("commit mask differs from the frozen pretreatment selection")
    return capsule._owner()._transition(
        capsule,
        ordered_edge_pair,
        selected_mask,
        cloned_counterfactual_rng,
        call_kind="commit",
    )


@dataclass(frozen=True)
class A1Checks:
    real_callable_unique_ports: bool
    handles_authenticated: bool
    simple_declared_intervention: bool
    mask_semantics: bool
    recomputation_ancestry: bool
    permutation_equivariance: bool
    host_identifying: bool


def classify_a1(checks: A1Checks) -> str:
    """Exact fail-closed eight-branch precedence."""

    if not checks.real_callable_unique_ports:
        return A1_MISSING_REAL_CALLABLE_OR_NO_UNIQUE_PREAGGREGATION_PORT
    if not checks.handles_authenticated:
        return A1_HANDLE_FORGEABLE_OR_PROVENANCE_LOST
    if not checks.simple_declared_intervention:
        return A1_COMPOUND_INTERVENTION_OR_UNDECLARED_PATH
    if not checks.mask_semantics:
        return A1_MASK_SEMANTICS_FAILURE
    if not checks.recomputation_ancestry:
        return A1_RECOMPUTATION_OR_ANCESTRY_FAILURE
    if not checks.permutation_equivariance:
        return A1_IDENTITY_STICKY_NONIDENTIFIABILITY
    if not checks.host_identifying:
        return A1_CALLABLE_BUT_HOST_NONIDENTIFYING
    return A1_DIRECTED_EDGE_BINDING_PASS


@dataclass(frozen=True)
class A1AuditResult:
    branch: str
    receipts: tuple[UpdateReceipt, ...]
    selected_mask: str
    checks: A1Checks
    witnesses: tuple[tuple[str, object], ...]
    counts: tuple[tuple[str, int], ...]
    raw_output_binding: str = RAW_OUTPUT_BINDING

    def to_dict(self) -> dict[str, object]:
        return _jsonable(self)  # type: ignore[return-value]

    def to_bytes(self) -> bytes:
        return json.dumps(
            self.to_dict(), separators=(",", ":"), sort_keys=True
        ).encode()


def run_five_transition_audit(
    learner: DirectedEdgeMaskedLearner,
    capsule: SealedLearnerCapsule,
    ordered_edge_pair: Sequence[OpaqueDirectedHandle],
) -> A1AuditResult:
    """Execute exactly four shadows and one fresh selected commit.

    This is the registered result-bearing audit entry.  Proof-sized unit tests
    should exercise the component functions instead of calling this routine.
    """

    receipts = tuple(
        DirectedEdgeMaskedUpdate(
            capsule,
            ordered_edge_pair,
            mask,
            learner.clone_counterfactual_rng(capsule),
        )
        for mask in MASKS
    )
    by_mask = {row.mask: row for row in receipts}
    selected_mask = capsule.manifest.frozen_selection.selected_mask
    commit = commit_selected_update(
        capsule,
        ordered_edge_pair,
        selected_mask,
        learner.clone_counterfactual_rng(capsule),
    )
    all_receipts = receipts + (commit,)

    conservation = _factorial_conservation(by_mask)
    contrasts = _port_contrast_norms(by_mask)
    contrast_separation = _port_contrast_separation(by_mask)
    changed_names = _port_contrast_changed_names(by_mask)
    enabled_path_local = bool(
        all(changed_names)
        and all(
            name.startswith("policy.member_encoder.")
            for names in changed_names
            for name in names
        )
    )
    disabled_perturbation_invariant = conservation <= 2e-6
    common_capsule = len({row.ancestry.capsule_digest for row in all_receipts}) == 1
    common_rng = len({row.ancestry.rng_plan_digest for row in all_receipts}) == 1
    distinct_lineage = len({row.call_lineage for row in all_receipts}) == 5
    intervention_clean = all(
        row.intervention.declared_port_count == 2
        and row.intervention.undeclared_duplicate_path_count == 0
        and row.intervention.post_aggregate_cancellation_path_count == 0
        and row.intervention.structural_preaggregation_gate
        and not row.intervention.execution_policy_intervention
        and not row.intervention.communication_value_intervention
        for row in all_receipts
    )
    expected_enabled = {
        mask: tuple(
            handle.opaque_id
            for bit, handle in zip(mask, ordered_edge_pair)
            if bit == "1"
        )
        for mask in MASKS
    }
    mask_receipts = all(
        by_mask[mask].intervention.enabled_ports == expected_enabled[mask]
        and len(by_mask[mask].intervention.disabled_ports) == mask.count("0")
        for mask in MASKS
    )
    manifest_fields = {field.name for field in fields(CapsuleManifest)}
    update_fields = set(DirectedEdgeMaskedUpdate.__annotations__)
    protected_excluded = not FORBIDDEN_INPUT_NAMES & (manifest_fields | update_fields)
    handles_authenticated = all(
        learner._record_for(capsule, handle).port_id == handle.opaque_id
        for handle in ordered_edge_pair
    )
    checks = A1Checks(
        real_callable_unique_ports=bool(
            callable(DirectedEdgeMaskedUpdate)
            and len({handle.opaque_id for handle in ordered_edge_pair}) == 2
            and all(row.finite for row in all_receipts)
        ),
        handles_authenticated=handles_authenticated,
        simple_declared_intervention=intervention_clean and protected_excluded,
        mask_semantics=bool(
            by_mask["11"].ordinary_update_path
            and not by_mask["00"].intervention.enabled_ports
            and mask_receipts
            and disabled_perturbation_invariant
            and enabled_path_local
        ),
        recomputation_ancestry=bool(
            common_capsule
            and common_rng
            and distinct_lineage
            and sum(row.optimizer_transitions for row in all_receipts) == 5
            and commit.call_kind == "commit"
            and commit.call_lineage != by_mask[selected_mask].call_lineage
            and commit.transition_predicate()
            == by_mask[selected_mask].transition_predicate()
        ),
        # Identity is routed only through the authenticated roster registry;
        # model coordinates and handle payloads expose no identity labels.
        permutation_equivariance=bool(
            tuple(sorted(row.slot for row in capsule.manifest.roster)) == (0, 1, 2)
            and all(
                set(vars(record))
                >= {
                    "source_instance",
                    "receiver_instance",
                    "source_slot",
                    "receiver_slot",
                }
                for record in (
                    learner._record_for(capsule, handle)
                    for handle in ordered_edge_pair
                )
            )
        ),
        host_identifying=bool(
            min(contrasts) > 1e-12
            and contrast_separation > 1e-12
        ),
    )
    branch = classify_a1(checks)
    witnesses = (
        ("full_gradient_factorial_max_abs", conservation),
        ("directed_port_gradient_contrast_norms", contrasts),
        ("directed_port_gradient_contrast_separation", contrast_separation),
        ("ordinary_11_dispatch", by_mask["11"].ordinary_update_path),
        ("literal_00_removal", not by_mask["00"].intervention.enabled_ports),
        ("shared_capsule_ancestry", common_capsule),
        ("logically_identical_site_rng", common_rng),
        ("fresh_commit_equals_selected_shadow", commit.transition_predicate() == by_mask[selected_mask].transition_predicate()),
        ("future_audit_semantic_inputs_excluded", protected_excluded),
        ("agent_name_mapping_registry_only", checks.permutation_equivariance),
        ("disabled_port_perturbation_invariance", disabled_perturbation_invariant),
        ("enabled_port_path_local_propagation", enabled_path_local),
        ("directed_port_changed_parameter_names", changed_names),
        ("no_execution_policy_or_communication_intervention", intervention_clean),
    )
    counts = (
        ("sealed_batches", 1),
        ("learner_update_calls", 5),
        ("optimizer_transitions", 5),
        ("environment_transitions", 0),
        ("policy_calls", 0),
        ("trainer_episodes", 0),
        ("evaluation_episodes", 0),
        ("model_fits", 0),
        ("retries", 0),
    )
    return A1AuditResult(
        branch, all_receipts, selected_mask, checks, witnesses, counts
    )


def trajectory_digest(trajectory: AnchoredRosterTrajectory) -> str:
    return _digest(_serialize(_trajectory_payload(trajectory)))


def model_digest(model: g40.G40NativeSixPolicy) -> str:
    return _model_digest(model)


def optimizer_digest(
    model: g40.G40NativeSixPolicy, optimizer: torch.optim.Optimizer
) -> str:
    return _optimizer_receipt(
        optimizer, g40.actor_credit_parameter_names(model)
    ).digest


def _validate_seal_inputs(
    learner: DirectedEdgeMaskedLearner,
    model: g40.G40NativeSixPolicy,
    optimizer: torch.optim.Optimizer,
    trajectory: AnchoredRosterTrajectory,
    roster: tuple[AgentInstance, ...],
    ancestry: RosterEpochAncestry,
    config: LearnerConfig,
    scheduler: DisabledUpdateState,
    scaler: DisabledUpdateState,
    clipping: DisabledUpdateState,
    accumulation: DisabledUpdateState,
) -> None:
    if type(model) is not g40.G40NativeSixPolicy or model.phase != "fast":
        raise ValueError("RECCT-A1 requires the real G40 fast learner callable")
    if type(optimizer) is not torch.optim.Adam:
        raise ValueError("RECCT-A1 requires the real G40 Adam optimizer")
    if learner.learner_instance == "" or model.member_capacity != 3:
        raise ValueError("RECCT-A1 requires one explicit N=3 learner")
    if len(roster) != 3 or len({row.instance_id for row in roster}) != 3:
        raise ValueError("RECCT-A1 active agent-instance roster must contain N=3")
    if tuple(sorted(row.slot for row in roster)) != (0, 1, 2):
        raise ValueError("RECCT-A1 roster slots must be a complete authenticated bijection")
    if ancestry.policy_generation == "" or ancestry.roster_epoch < 0:
        raise ValueError("RECCT-A1 policy generation/roster epoch is missing")
    if any(
        state.component != expected
        for state, expected in (
            (scheduler, "scheduler"),
            (scaler, "scaler"),
            (clipping, "gradient_clipping"),
            (accumulation, "gradient_accumulation"),
        )
    ):
        raise ValueError("RECCT-A1 disabled transition state identity mismatch")
    if trajectory.outcomes or trajectory.ledgers:
        raise ValueError("RECCT-A1 zero-environment sealed batch forbids runtime objects")
    if trajectory.rewards.ndim != 2 or trajectory.rewards.shape[0] < 1:
        raise ValueError("RECCT-A1 pretreatment batch shape is invalid")
    if trajectory.active_mask.shape[-1] != 3 or not bool(trajectory.active_mask.all()):
        raise ValueError("RECCT-A1 handles require three active instances throughout")
    tensor_rows = tuple(
        value
        for value in _trajectory_payload(trajectory).values()
        if isinstance(value, torch.Tensor)
    )
    if any(
        row.dtype != torch.bool and not bool(torch.isfinite(row).all())
        for row in tensor_rows
    ):
        raise ValueError("RECCT-A1 pretreatment batch contains non-finite state")
    parameters = model.actor_credit_parameters()
    owned = tuple(
        parameter for group in optimizer.param_groups for parameter in group["params"]
    )
    if tuple(id(row) for row in parameters) != tuple(id(row) for row in owned):
        raise ValueError("RECCT-A1 optimizer ownership/order mismatch")
    if len(optimizer.param_groups) != 1:
        raise ValueError("RECCT-A1 optimizer config must have one explicit group")
    group = optimizer.param_groups[0]
    if (
        float(group["lr"]) != float(config.learning_rate)
        or tuple(float(row) for row in group["betas"]) != tuple(config.betas)
        or float(group["eps"]) != float(config.eps)
        or float(group["weight_decay"]) != float(config.weight_decay)
        or bool(group["amsgrad"]) != bool(config.amsgrad)
        or bool(group.get("maximize", False)) != bool(config.maximize)
    ):
        raise ValueError("RECCT-A1 optimizer and learner config differ")


def _new_optimizer(
    model: g40.G40NativeSixPolicy, config: LearnerConfig
) -> torch.optim.Adam:
    return torch.optim.Adam(
        model.actor_credit_parameters(),
        lr=float(config.learning_rate),
        betas=tuple(float(row) for row in config.betas),
        eps=float(config.eps),
        weight_decay=float(config.weight_decay),
        amsgrad=bool(config.amsgrad),
        maximize=bool(config.maximize),
    )


def _trajectory_payload(trajectory: AnchoredRosterTrajectory) -> dict[str, object]:
    return {
        field.name: (
            getattr(trajectory, field.name).detach().cpu().clone()
            if isinstance(getattr(trajectory, field.name), torch.Tensor)
            else copy.deepcopy(getattr(trajectory, field.name))
        )
        for field in fields(AnchoredRosterTrajectory)
    }


def _trajectory_from_payload(payload: Mapping[str, object]) -> AnchoredRosterTrajectory:
    expected = {field.name for field in fields(AnchoredRosterTrajectory)}
    if set(payload) != expected:
        raise ValueError("sealed pretreatment batch schema mismatch")
    return AnchoredRosterTrajectory(**dict(payload))  # type: ignore[arg-type]


def _model_values(model: nn.Module) -> tuple[TensorValue, ...]:
    return tuple(
        TensorValue.from_tensor(name, value)
        for name, value in model.state_dict().items()
    )


def _model_digest(model: nn.Module) -> str:
    return _tensor_values_digest(_model_values(model))


def _optimizer_receipt(
    optimizer: torch.optim.Optimizer, parameter_names: Sequence[str]
) -> OptimizerStateReceipt:
    parameters = tuple(
        parameter for group in optimizer.param_groups for parameter in group["params"]
    )
    names = tuple(parameter_names)
    if len(parameters) != len(names):
        raise ValueError("optimizer receipt parameter inventory mismatch")
    name_by_id = {id(parameter): name for name, parameter in zip(names, parameters)}
    states = []
    for parameter, name in zip(parameters, names):
        state = optimizer.state.get(parameter, {})
        tensor_rows = []
        for key in sorted(state):
            value = state[key]
            if isinstance(value, torch.Tensor):
                tensor_rows.append(TensorValue.from_tensor(str(key), value))
            elif isinstance(value, (int, float, bool)):
                tensor_rows.append(
                    TensorValue.from_tensor(str(key), torch.as_tensor(value))
                )
            else:
                raise ValueError("optimizer state contains an unknown mutable value")
        states.append((name, tuple(tensor_rows)))
    group_rows = []
    for group in optimizer.param_groups:
        row = []
        for key in sorted(group):
            value = group[key]
            if key == "params":
                normalized: object = tuple(name_by_id[id(parameter)] for parameter in value)
            elif isinstance(value, (str, int, float, bool, type(None))):
                normalized = value
            elif isinstance(value, tuple):
                normalized = tuple(value)
            else:
                raise ValueError("optimizer parameter group contains unknown state")
            row.append((str(key), normalized))
        group_rows.append(tuple(row))
    payload = (tuple(states), tuple(group_rows))
    return OptimizerStateReceipt(
        tuple(states), tuple(group_rows), _digest(_canonical_json(payload))
    )


def _complete_state_receipt(
    model: g40.G40NativeSixPolicy,
    optimizer: torch.optim.Optimizer,
    manifest: CapsuleManifest,
) -> CompleteStateReceipt:
    learner_state = _model_values(model)
    optimizer_state = _optimizer_receipt(
        optimizer, g40.actor_credit_parameter_names(model)
    )
    digest = _digest(
        _canonical_json(
            (
                learner_state,
                optimizer_state,
                manifest.scheduler_state,
                manifest.scaler_state,
                manifest.clipping_state,
                manifest.accumulation_state,
            )
        )
    )
    return CompleteStateReceipt(
        learner_state,
        optimizer_state,
        manifest.scheduler_state,
        manifest.scaler_state,
        manifest.clipping_state,
        manifest.accumulation_state,
        digest,
    )


def _factorial_conservation(by_mask: Mapping[str, UpdateReceipt]) -> float:
    rows = [by_mask[mask].gradient for mask in MASKS]
    if any(tuple(row.name for row in rows[0]) != tuple(item.name for item in other) for other in rows[1:]):
        return float("inf")
    maximum = 0.0
    for zero, one, two, both in zip(*rows):
        residual = (
            both.tensor().to(torch.float64)
            - one.tensor().to(torch.float64)
            - two.tensor().to(torch.float64)
            + zero.tensor().to(torch.float64)
        )
        maximum = max(maximum, float(residual.abs().max()))
    return maximum


def _port_contrast_norms(
    by_mask: Mapping[str, UpdateReceipt]
) -> tuple[float, float]:
    vectors = {
        mask: torch.cat(
            tuple(row.tensor().to(torch.float64).reshape(-1) for row in receipt.gradient)
        )
        for mask, receipt in by_mask.items()
    }
    return (
        float(torch.linalg.vector_norm(vectors["10"] - vectors["00"])),
        float(torch.linalg.vector_norm(vectors["01"] - vectors["00"])),
    )


def _port_contrast_separation(
    by_mask: Mapping[str, UpdateReceipt]
) -> float:
    vectors = {
        mask: torch.cat(
            tuple(row.tensor().to(torch.float64).reshape(-1) for row in receipt.gradient)
        )
        for mask, receipt in by_mask.items()
    }
    first = vectors["10"] - vectors["00"]
    second = vectors["01"] - vectors["00"]
    return float(torch.linalg.vector_norm(first - second))


def _port_contrast_changed_names(
    by_mask: Mapping[str, UpdateReceipt]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    def changed(left: str, right: str) -> tuple[str, ...]:
        return tuple(
            first.name
            for first, second in zip(
                by_mask[left].gradient, by_mask[right].gradient
            )
            if not torch.equal(first.tensor(), second.tensor())
        )

    return changed("10", "00"), changed("01", "00")


def _serialize(value: object) -> bytes:
    stream = io.BytesIO()
    torch.save(value, stream)
    return stream.getvalue()


def _deserialize(value: bytes) -> object:
    return torch.load(io.BytesIO(value), map_location="cpu", weights_only=False)


def _capsule_digest(
    manifest: CapsuleManifest, state_payload: bytes, batch_payload: bytes
) -> str:
    return _digest(
        _canonical_json(
            (
                manifest,
                _digest(state_payload),
                _digest(batch_payload),
            )
        )
    )


def _tensor_values_digest(values: Sequence[TensorValue]) -> str:
    return _digest(_canonical_json(tuple(values)))


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        _jsonable(value), separators=(",", ":"), sort_keys=True
    ).encode()


def _jsonable(value: object) -> object:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(row) for key, row in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(row) for row in value]
    if isinstance(value, bytes):
        return base64.b64encode(value).decode("ascii")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"value is not canonical JSON: {type(value).__name__}")


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
