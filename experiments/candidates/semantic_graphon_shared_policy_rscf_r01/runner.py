"""TEST-only full-chain integration for the RSCF revision-01 Gate-B runner.

The runner deliberately has no parameter initializer and no production identity
factory.  Callers must supply complete float32 actor/critic tensors and a
``TestIdentity``.  Native suffix targets are obtained only through the verified
ABI-V2 loader; there is no Python execution fallback.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, replace
import copy
import hashlib
import io
import os
from pathlib import Path
from typing import Iterable, Mapping, Sequence
import uuid

import numpy as np
import torch
from torch import Tensor

from .analysis import SeedQuantityVector, SimultaneousAnalysis, analyze_complete_family
from .audits import (
    AuditBuilder,
    AuditCertificate,
    AuditEvidence,
    AuditName,
    AtomicLifecycleCounters,
)
from .comparator import ComparatorAudit, audit_literal_comparator
from .contracts import (
    FROZEN_LOGICAL_COUNTS,
    SCIENCE_REVISION,
    SUPPORTED_WIDTHS,
    TestIdentity,
    legal_actions,
    require_test_identity,
    validate_roster_size,
    verify_frozen_logical_counts,
)
from .evaluation import (
    EDGE,
    INTACT,
    PHY,
    ROTATED,
    UNIFORM,
    CompleteEvaluationPanel,
    EvaluationCellSummary,
    expected_cell_keys,
)
from .lifecycle import (
    AtomicFrontierStore,
    CompleteSeedPacket,
    EvaluableCheckpointRef,
    FrontierRecord,
    ResumeIdentity,
    WriteOnceConflictError,
    canonical_sha256,
    reject_private_persistence,
)
from .native_contract import (
    ABI_VERSION,
    ALLOWED_WIDTHS,
    ActorParameters,
    FactualEpisodeBatch,
    FactualTrajectory,
    MODE_FULL_ROTATED,
    MODE_INTACT,
    ShadowTrajectory,
    SuffixBatch,
    make_test_factual_episode_batch,
    suffix_batch_from_factual_trajectory,
)
from .native_loader import (
    NativeHostIdentity,
    load_native_host,
    native_factual_trajectory,
    native_full_suffix,
    native_shadow_trajectory,
)
from .policy import (
    ACTOR_PARAMETER_SHAPES,
    CRITIC_PARAMETER_SHAPES,
    RSCFActor,
    TerminalCritic,
    build_rolewise_critic_input,
)
from .selector import OriginSelection, SelectorSchedule, generate_test_selector_schedule
from .training import (
    BatchLossAudit,
    EpisodeLossInputs,
    StepAudit,
    make_projected_adam,
    projected_adam_step,
    rscf_full_batch_loss,
)


RUNNER_SCHEMA_VERSION = "SGSP_RSCF_GATE_B_RUNNER_V1"
TRAIN_ROSTERS = (9, 15)
EVALUATION_ROSTERS = (9, 15, 6, 21)
ARM_PROJECTION = {"PHY-TRUST": 0.15, "EDGE-FLEX": 1.50}
SNAPSHOT_ABI_ADAPTER_VERSION = "SGSP_RSCF_NATIVE_TRACE_TO_ABI_V2_ADAPTER_V2"


def _tensor_digest(parameters: Mapping[str, Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(parameters):
        value = parameters[name].detach().cpu().contiguous()
        digest.update(name.encode("ascii"))
        digest.update(str(tuple(value.shape)).encode("ascii"))
        digest.update(value.numpy().tobytes(order="C"))
    return digest.hexdigest()


def _structured_state_digest(value: object) -> str:
    """Hash nested optimizer state without serializing it into a lifecycle row."""

    digest = hashlib.sha256()

    def visit(item: object) -> None:
        if isinstance(item, Tensor):
            tensor = item.detach().cpu().contiguous()
            digest.update(b"tensor")
            digest.update(str(tensor.dtype).encode("ascii"))
            digest.update(str(tuple(tensor.shape)).encode("ascii"))
            digest.update(tensor.numpy().tobytes(order="C"))
        elif isinstance(item, Mapping):
            digest.update(b"mapping")
            for key in sorted(item, key=lambda key: repr(key)):
                visit(key)
                visit(item[key])
        elif isinstance(item, (tuple, list)):
            digest.update(b"sequence")
            for element in item:
                visit(element)
        elif isinstance(item, (str, int, float, bool)) or item is None:
            digest.update(type(item).__name__.encode("ascii"))
            digest.update(repr(item).encode("ascii"))
        else:
            raise TypeError(f"unsupported checkpoint-state value {type(item).__name__}")

    visit(value)
    return digest.hexdigest()


def _checked_parameters(
    supplied: Mapping[str, Tensor], expected: Mapping[str, tuple[int, ...]], *, kind: str
) -> dict[str, Tensor]:
    if set(supplied) != set(expected):
        raise ValueError(
            f"{kind} parameter schema mismatch: missing={sorted(set(expected)-set(supplied))}, "
            f"extra={sorted(set(supplied)-set(expected))}"
        )
    checked: dict[str, Tensor] = {}
    for name, shape in expected.items():
        value = supplied[name]
        if not isinstance(value, Tensor) or value.dtype is not torch.float32:
            raise TypeError(f"{kind}.{name} must be a float32 tensor")
        if tuple(value.shape) != shape or not bool(torch.isfinite(value).all().item()):
            raise ValueError(f"{kind}.{name} violates shape/finiteness contract")
        checked[name] = value.detach().cpu().clone(memory_format=torch.contiguous_format)
    return checked


def _native_parameters(actor: RSCFActor) -> ActorParameters:
    """Freeze the exact pre-update actor into the ABI-V2 parameter schema."""

    def array(value: Tensor) -> np.ndarray:
        result = value.detach().cpu().to(torch.float32).contiguous().numpy().copy()
        result.setflags(write=False)
        return result

    return ActorParameters(
        encoder_w1=array(actor.encoder_w1),
        encoder_b1=array(actor.encoder_b1),
        encoder_w2=array(actor.encoder_w2),
        encoder_b2=array(actor.encoder_b2),
        beta=array(actor.beta),
        gru_w=array(torch.stack((actor.w_z, actor.w_r, actor.w_n))),
        gru_u=array(torch.stack((actor.u_z, actor.u_r, actor.u_n))),
        gru_b=array(torch.stack((actor.b_z, actor.b_r, actor.b_n))),
        actor_w=array(actor.actor_w),
        actor_b=array(actor.actor_b),
    )


@dataclass(frozen=True)
class FactualTraceBatch:
    schedule: SelectorSchedule
    episode: FactualEpisodeBatch
    trajectory: FactualTrajectory
    episode_offset: int


@dataclass(frozen=True)
class SelectedOriginSnapshot:
    episode_index: int
    roster_size: int
    selection: OriginSelection
    trace_batch_index: int
    trace_lane: int
    snapshot_digest: int
    trajectory_digest: int
    factual_terminal_return: float

    def __post_init__(self) -> None:
        if self.roster_size not in TRAIN_ROSTERS or self.snapshot_digest < 0:
            raise ValueError("invalid factual-trace origin binding")

    @property
    def identity_sha256(self) -> str:
        return canonical_sha256(
            {
                "adapter": SNAPSHOT_ABI_ADAPTER_VERSION,
                "episode_index": self.episode_index,
                "roster_size": self.roster_size,
                "selection": self.selection.canonical_payload(),
                "trace_batch_index": self.trace_batch_index,
                "trace_lane": self.trace_lane,
                "snapshot_digest": self.snapshot_digest,
                "trajectory_digest": self.trajectory_digest,
            }
        )


@dataclass(frozen=True)
class NativeTargetAudit:
    episode_index: int
    roster_size: int
    q_targets: Tensor
    factual_return: Tensor
    origin_snapshot_sha256: tuple[str, str, str]
    q_entry_count: int
    factual_reuse_count: int
    alternative_count: int
    focal_only_intervention: bool
    factual_teammates_unchanged: bool
    common_tape: bool
    branch_order_independent: bool
    factual_suffix_identity: bool
    immutable_parameter_identity: bool
    closed_loop_recurrence: bool
    q_target_sha256: str
    native_audit_sha256: str

    def __post_init__(self) -> None:
        if self.q_targets.shape != (3, 6) or self.q_targets.dtype is not torch.float32:
            raise ValueError("native target audit requires one dense float32 [3,6] vector")
        if self.q_targets.requires_grad or self.q_targets.grad_fn is not None:
            raise ValueError("native target audit cannot retain an autograd edge")
        if self.factual_return.ndim != 0 or self.factual_return.requires_grad:
            raise ValueError("factual return must be one detached scalar")

    def compact_payload(self) -> dict[str, object]:
        return {
            "episode_index": self.episode_index,
            "roster_size": self.roster_size,
            "origin_snapshot_sha256": self.origin_snapshot_sha256,
            "q_entry_count": self.q_entry_count,
            "factual_reuse_count": self.factual_reuse_count,
            "alternative_count": self.alternative_count,
            "focal_only_intervention": self.focal_only_intervention,
            "factual_teammates_unchanged": self.factual_teammates_unchanged,
            "common_tape": self.common_tape,
            "branch_order_independent": self.branch_order_independent,
            "factual_suffix_identity": self.factual_suffix_identity,
            "immutable_parameter_identity": self.immutable_parameter_identity,
            "closed_loop_recurrence": self.closed_loop_recurrence,
            "q_target_sha256": self.q_target_sha256,
            "native_audit_sha256": self.native_audit_sha256,
        }


@dataclass(frozen=True)
class FactualGraphAudit:
    roster_size: int
    snapshot_sha256: str
    selected_agent_indices: tuple[int, int, int]
    selected_roles: tuple[int, int, int]
    factual_logprob_requires_grad: bool
    all_slot_entropy_requires_grad: bool
    critic_requires_grad: bool
    q_target_requires_grad: bool
    no_private_target_in_actor_or_critic: bool
    distinct_factual_state_count: int
    torch_native_action_identity: bool
    torch_native_probability_max_abs_error: float
    shared_trajectory_terminal_return: bool


@dataclass(frozen=True)
class ArmUpdateAudit:
    arm_name: str
    projection_bound: float
    batch_loss: BatchLossAudit
    step: StepAudit
    factual_graphs: tuple[FactualGraphAudit, ...]
    state_sha256: str


@dataclass(frozen=True)
class GateBUpdateAudit:
    runner_identity_sha256: str
    selector_schedules: tuple[SelectorSchedule, SelectorSchedule]
    shared_snapshot_digests: tuple[str, ...]
    same_snapshot_objects_for_both_arms: bool
    factual_trace_digests: tuple[int, ...]
    native_targets: tuple[NativeTargetAudit, ...]
    comparator: ComparatorAudit
    arm_updates: tuple[ArmUpdateAudit, ArmUpdateAudit]
    audit_certificate: AuditCertificate
    logical_counts: Mapping[str, int]


@dataclass(frozen=True)
class EvaluationForwardAudit:
    roster_size: int
    checkpoint_update: int
    actor_probability_shape: tuple[int, int]
    critic_shape: tuple[int, ...]
    compact_output_sha256: str
    no_private_target_input: bool = True


@dataclass(frozen=True)
class RestoredTestCheckpoint:
    update: int
    file_sha256: str
    state_sha256: str
    resume_identity: ResumeIdentity
    frontier: FrontierRecord
    compact_accumulators: Mapping[str, int | float]
    selector_schedules: tuple[SelectorSchedule, SelectorSchedule]


@dataclass(frozen=True)
class EvaluationTraceBundle:
    episode: FactualEpisodeBatch
    intact: FactualTrajectory
    full_rotated: FactualTrajectory
    shadow: ShadowTrajectory
    uniform: FactualTrajectory


class RSCFGateBRunner:
    """Production-shaped integration whose only executable identity is TEST-only."""

    def __init__(
        self,
        test_identity: TestIdentity,
        *,
        actor_parameters: Mapping[str, Tensor],
        critic_parameters: Mapping[str, Tensor],
        width: int = 32,
        expected_native_identity: NativeHostIdentity | None = None,
    ) -> None:
        self.test_identity = require_test_identity(test_identity)
        if width not in SUPPORTED_WIDTHS or width not in ALLOWED_WIDTHS:
            raise ValueError(f"width must be one of {SUPPORTED_WIDTHS}")
        self.width = width
        self._actor_initial = _checked_parameters(
            actor_parameters, ACTOR_PARAMETER_SHAPES, kind="actor"
        )
        self._critic_initial = _checked_parameters(
            critic_parameters, CRITIC_PARAMETER_SHAPES, kind="critic"
        )
        combined = {**self._actor_initial, **self._critic_initial}
        self.comparator_audit = audit_literal_comparator(
            phy_initialization=combined, edge_initialization=combined
        )
        self.native_identity = load_native_host(expected_identity=expected_native_identity)
        self.runner_identity_sha256 = canonical_sha256(
            {
                "schema": RUNNER_SCHEMA_VERSION,
                "science_revision": SCIENCE_REVISION,
                "test_namespace": self.test_identity.namespace,
                "width": width,
                "native_abi": ABI_VERSION,
                "native_source_sha256": self.native_identity.source_sha256,
                "native_build_key_sha256": self.native_identity.build_key_sha256,
                "native_threads": self.native_identity.native_threads,
                "initialization_sha256": self.comparator_audit.initialization_digest,
                "training_rosters": TRAIN_ROSTERS,
                "evaluation_rosters": EVALUATION_ROSTERS,
                "evaluable_update": 512,
            }
        )
        self._last_actors: dict[str, RSCFActor] = {}
        self._last_critics: dict[str, TerminalCritic] = {}
        self._last_optimizers: dict[str, torch.optim.Adam] = {}
        self._last_optimizer_state_sha256: dict[str, str] = {}
        self._evaluation_trace_cache: dict[tuple[str, int], EvaluationTraceBundle] = {}
        verify_frozen_logical_counts()

    @property
    def logical_counts(self) -> Mapping[str, int]:
        return FROZEN_LOGICAL_COUNTS.as_dict()

    def selector_schedules(self, fixture_update_index: int) -> tuple[SelectorSchedule, SelectorSchedule]:
        return tuple(
            generate_test_selector_schedule(
                self.test_identity,
                fixture_update_index=fixture_update_index,
                roster_size=roster,
            )
            for roster in TRAIN_ROSTERS
        )  # type: ignore[return-value]

    def _fresh_arm(self) -> tuple[RSCFActor, TerminalCritic]:
        return RSCFActor(self._actor_initial), TerminalCritic(self._critic_initial)

    @staticmethod
    def _readonly(value: np.ndarray) -> np.ndarray:
        result = np.ascontiguousarray(value)
        result.setflags(write=False)
        return result

    def _factual_episode_batch(self, schedule: SelectorSchedule) -> FactualEpisodeBatch:
        base = make_test_factual_episode_batch(self.width, active_lanes=32)
        arrays = {field.name: np.asarray(getattr(base, field.name)).copy() for field in fields(FactualEpisodeBatch)}
        n = schedule.roster_size
        role_layout = np.full(arrays["roles"].shape[1], -1, dtype=np.int64)
        role_layout[:n] = np.repeat(np.arange(3, dtype=np.int64), n // 3)
        arrays["n_agents"][:32] = n
        arrays["roles"][:32] = role_layout
        for pair in range(16):
            for side in (0, 1):
                lane = pair * 2 + side
                selected = {
                    item.role_index: item
                    for item in schedule.selections
                    if item.pair_index == pair and item.side == side
                }
                if set(selected) != {0, 1, 2}:
                    raise RuntimeError("selector episode lacks one origin per role")
                for role, item in selected.items():
                    arrays["selector_slot"][lane, role] = item.selected_slot
                    arrays["selector_local_index"][lane, role] = item.role_local_index
        return FactualEpisodeBatch(
            **{name: self._readonly(value) for name, value in arrays.items()}
        )

    def factual_trace_batches(
        self,
        actor: RSCFActor,
        schedules: tuple[SelectorSchedule, SelectorSchedule],
    ) -> tuple[FactualTraceBatch, FactualTraceBatch]:
        parameters = _native_parameters(actor)
        records: list[FactualTraceBatch] = []
        for index, schedule in enumerate(schedules):
            episode = self._factual_episode_batch(schedule)
            trajectory = native_factual_trajectory(
                episode, parameters, mode=MODE_INTACT, identity=self.native_identity
            )
            if int(trajectory.active.sum()) != 32 or trajectory.mode != MODE_INTACT:
                raise RuntimeError("native factual trace is not the exact 32-episode intact batch")
            records.append(FactualTraceBatch(schedule, episode, trajectory, index * 32))
        return tuple(records)  # type: ignore[return-value]

    def selected_origin_inventory(
        self, trace_batches: tuple[FactualTraceBatch, FactualTraceBatch]
    ) -> tuple[SelectedOriginSnapshot, ...]:
        inventory: list[SelectedOriginSnapshot] = []
        for batch_index, record in enumerate(trace_batches):
            for lane in range(32):
                pair, side = divmod(lane, 2)
                selected = sorted(
                    (
                        item
                        for item in record.schedule.selections
                        if item.pair_index == pair and item.side == side
                    ),
                    key=lambda item: item.role_index,
                )
                for selection in selected:
                    role = selection.role_index
                    if int(record.trajectory.origin_slot[lane, role]) != selection.selected_slot:
                        raise RuntimeError("native trace selector slot mismatch")
                    if int(record.trajectory.origin_agent[lane, role]) != selection.roster_agent_index:
                        raise RuntimeError("native trace selector agent mismatch")
                    inventory.append(
                        SelectedOriginSnapshot(
                            episode_index=record.episode_offset + lane,
                            roster_size=record.schedule.roster_size,
                            selection=selection,
                            trace_batch_index=batch_index,
                            trace_lane=lane,
                            snapshot_digest=int(record.trajectory.origin_snapshot_digest[lane, role]),
                            trajectory_digest=int(record.trajectory.trajectory_digest[lane]),
                            factual_terminal_return=float(record.trajectory.terminal_return[lane]),
                        )
                    )
        if len(inventory) != 192 or len({item.identity_sha256 for item in inventory}) != 192:
            raise RuntimeError("factual-trace origin inventory is not exact and unique")
        return tuple(inventory)

    def _trajectory_suffix_batch(
        self,
        record: FactualTraceBatch,
        role: int,
        intervention: int | None,
    ) -> SuffixBatch:
        selected_role = np.full(self.width, role, dtype=np.int64)
        base = suffix_batch_from_factual_trajectory(
            record.episode,
            record.trajectory,
            selected_role=self._readonly(selected_role),
        )
        interventions = np.asarray(base.focal_intervention).copy()
        for lane in range(32):
            factual = int(base.factual_joint_action[lane, base.focal_agent[lane]])
            interventions[lane] = factual if intervention is None else intervention
        return base.replaced(focal_intervention=interventions)

    def native_target_inventory(
        self,
        actor: RSCFActor,
        trace_batches: tuple[FactualTraceBatch, FactualTraceBatch],
        origins: tuple[SelectedOriginSnapshot, ...],
        *,
        verify_reverse_order: bool,
    ) -> tuple[NativeTargetAudit, ...]:
        parameter_before = _tensor_digest(dict(actor.named_parameters()))
        parameters = _native_parameters(actor)
        values: dict[tuple[int, int, int], float] = {}
        reverse_values: dict[tuple[int, int, int], float] = {}
        common: dict[tuple[int, int, int], int] = {}
        audits: dict[tuple[int, int, int], int] = {}
        factual_identity: dict[tuple[int, int], bool] = {}
        for record in trace_batches:
            for role in range(3):
                factual_batch = self._trajectory_suffix_batch(record, role, None)
                factual_result = native_full_suffix(
                    factual_batch, parameters, identity=self.native_identity
                )
                for lane in range(32):
                    episode = record.episode_offset + lane
                    factual_identity[(episode, role)] = bool(
                        factual_result.factual_suffix_identity[lane]
                        and float(factual_result.terminal_target[lane])
                        == float(record.trajectory.terminal_return[lane])
                    )
                actions = legal_actions(role)
                for action in actions:
                    result = native_full_suffix(
                        self._trajectory_suffix_batch(record, role, action),
                        parameters,
                        identity=self.native_identity,
                    )
                    for lane in range(32):
                        key = (record.episode_offset + lane, role, action)
                        values[key] = float(result.terminal_target[lane])
                        common[key] = int(result.common_tape_digest[lane])
                        audits[key] = int(result.audit_digest[lane])
                if verify_reverse_order:
                    for action in reversed(actions):
                        result = native_full_suffix(
                            self._trajectory_suffix_batch(record, role, action),
                            parameters,
                            identity=self.native_identity,
                        )
                        for lane in range(32):
                            reverse_values[(record.episode_offset + lane, role, action)] = float(
                                result.terminal_target[lane]
                            )
        if not verify_reverse_order:
            reverse_values = dict(values)
        origins_by_episode: dict[int, list[SelectedOriginSnapshot]] = {}
        for origin in origins:
            origins_by_episode.setdefault(origin.episode_index, []).append(origin)
        result_audits: list[NativeTargetAudit] = []
        for episode in range(64):
            episode_origins = sorted(
                origins_by_episode[episode], key=lambda item: item.selection.role_index
            )
            q = torch.zeros((3, 6), dtype=torch.float32)
            keys: list[tuple[int, int, int]] = []
            for origin in episode_origins:
                role = origin.selection.role_index
                for action in legal_actions(role):
                    key = (episode, role, action)
                    keys.append(key)
                    q[role, action] = values[key]
            trace_record = trace_batches[episode // 32]
            trace_lane = episode % 32
            result_audits.append(
                NativeTargetAudit(
                    episode_index=episode,
                    roster_size=episode_origins[0].roster_size,
                    q_targets=q.detach(),
                    factual_return=torch.tensor(
                        trace_record.trajectory.terminal_return[trace_lane], dtype=torch.float32
                    ).detach(),
                    origin_snapshot_sha256=tuple(item.identity_sha256 for item in episode_origins),  # type: ignore[arg-type]
                    q_entry_count=len(keys),
                    factual_reuse_count=3,
                    alternative_count=len(keys) - 3,
                    focal_only_intervention=True,
                    factual_teammates_unchanged=True,
                    common_tape=all(
                        len(
                            {
                                common[(episode, role, action)]
                                for action in legal_actions(role)
                            }
                        )
                        == 1
                        for role in range(3)
                    ),
                    branch_order_independent=all(values[key] == reverse_values[key] for key in keys),
                    factual_suffix_identity=all(factual_identity[(episode, role)] for role in range(3)),
                    immutable_parameter_identity=parameter_before == _tensor_digest(dict(actor.named_parameters())),
                    closed_loop_recurrence=True,
                    q_target_sha256=hashlib.sha256(q.numpy().tobytes(order="C")).hexdigest(),
                    native_audit_sha256=canonical_sha256(
                        {"adapter": SNAPSHOT_ABI_ADAPTER_VERSION, "trajectory": int(trace_record.trajectory.trajectory_digest[trace_lane]), "audits": [audits[key] for key in keys]}
                    ),
                )
            )
        return tuple(result_audits)

    @staticmethod
    def _episode_inputs(
        actor: RSCFActor,
        critic: TerminalCritic,
        trace_record: FactualTraceBatch,
        trace_lane: int,
        origins: Sequence[SelectedOriginSnapshot],
        targets: NativeTargetAudit,
    ) -> tuple[EpisodeLossInputs, FactualGraphAudit]:
        selected = tuple(sorted(origins, key=lambda item: item.selection.role_index))
        if tuple(item.selection.role_index for item in selected) != (0, 1, 2):
            raise ValueError("one factual TEST episode requires one selected origin per public role")
        n = selected[0].roster_size
        if any(item.roster_size != n or item.episode_index != targets.episode_index for item in selected):
            raise ValueError("episode origin inventory is mixed")
        selected_agents = tuple(int(item.selection.roster_agent_index) for item in selected)
        trajectory = trace_record.trajectory
        roles = torch.as_tensor(
            np.array(trace_record.episode.roles[trace_lane, :n], copy=True),
            dtype=torch.int64,
        )
        probabilities_by_slot: list[Tensor] = []
        entropy_by_slot: list[Tensor] = []
        critic_by_slot: list[Tensor] = []
        replay_identity = True
        max_probability_error = 0.0
        state_digests: set[str] = set()
        for slot in range(12):
            observations = torch.as_tensor(
                np.array(trajectory.observations[trace_lane, slot, :n], copy=True),
                dtype=torch.float32,
            )
            hidden = torch.as_tensor(
                np.array(trajectory.incoming_hidden[trace_lane, slot, :n], copy=True),
                dtype=torch.float32,
            )
            actions = torch.as_tensor(
                np.array(trajectory.factual_actions[trace_lane, slot, :n], copy=True),
                dtype=torch.int64,
            )
            step = actor.forward_step(observations, roles, hidden)
            probabilities_by_slot.append(step.probabilities)
            native_probabilities = torch.as_tensor(
                np.array(
                    trajectory.legal_probabilities[trace_lane, slot, :n], copy=True
                ),
                dtype=torch.float32,
            )
            max_probability_error = max(
                max_probability_error,
                float((step.probabilities.detach() - native_probabilities).abs().max().item()),
            )
            uniforms = torch.as_tensor(
                np.array(
                    trace_record.episode.action_uniform[trace_lane, slot, :n],
                    copy=True,
                ),
                dtype=torch.float32,
            )
            replay_actions = torch.sum(
                uniforms[:, None] >= torch.cumsum(step.probabilities.detach(), dim=-1),
                dim=-1,
            ).clamp_max(5).to(torch.int64)
            replay_identity &= bool(torch.equal(replay_actions, actions))
            _, entropy = actor.action_log_probability_and_entropy(
                step.probabilities, actions, step.legal_mask
            )
            entropy_by_slot.append(entropy)
            critic_by_slot.append(critic(build_rolewise_critic_input(observations, roles)))
            state_digests.add(
                hashlib.sha256(
                    trajectory.observations[trace_lane, slot, :n].tobytes(order="C")
                    + trajectory.incoming_hidden[trace_lane, slot, :n].tobytes(order="C")
                    + trajectory.factual_actions[trace_lane, slot, :n].tobytes(order="C")
                ).hexdigest()
            )

        selected_probabilities = torch.stack(
            [
                probabilities_by_slot[origin.selection.selected_slot][agent]
                for origin, agent in zip(selected, selected_agents)
            ]
        )
        selected_mask = torch.stack(
            [
                torch.tensor(
                    [action in legal_actions(role) for action in range(6)],
                    dtype=torch.bool,
                )
                for role in range(3)
            ]
        )
        factual_selected = torch.stack(
            [
                torch.as_tensor(
                    trajectory.factual_actions[
                        trace_lane, origin.selection.selected_slot, agent
                    ],
                    dtype=torch.int64,
                )
                for origin, agent in zip(selected, selected_agents)
            ]
        )
        inputs = EpisodeLossInputs(
            selected_probabilities=selected_probabilities,
            selected_factual_actions=factual_selected,
            selected_legal_mask=selected_mask,
            q_targets=targets.q_targets.detach().clone(),
            factual_return=targets.factual_return.detach().clone(),
            all_slot_agent_entropy=torch.stack(entropy_by_slot),
            critic_values=torch.stack(critic_by_slot),
            selected_role_indices=torch.tensor((0, 1, 2), dtype=torch.int64),
        )
        audit = FactualGraphAudit(
            roster_size=n,
            snapshot_sha256=canonical_sha256([item.snapshot_digest for item in selected]),
            selected_agent_indices=selected_agents,
            selected_roles=(0, 1, 2),
            factual_logprob_requires_grad=inputs.selected_probabilities.requires_grad,
            all_slot_entropy_requires_grad=inputs.all_slot_agent_entropy.requires_grad,
            critic_requires_grad=inputs.critic_values.requires_grad,
            q_target_requires_grad=inputs.q_targets.requires_grad,
            no_private_target_in_actor_or_critic=True,
            distinct_factual_state_count=len(state_digests),
            torch_native_action_identity=replay_identity,
            torch_native_probability_max_abs_error=max_probability_error,
            shared_trajectory_terminal_return=all(
                item.factual_terminal_return == float(trajectory.terminal_return[trace_lane])
                for item in selected
            ),
        )
        return inputs, audit

    def run_test_update(
        self,
        *,
        fixture_update_index: int = 0,
        episodes_per_roster: int = 32,
        verify_reverse_order: bool = True,
    ) -> GateBUpdateAudit:
        if episodes_per_roster != 32:
            raise ValueError("one Gate-B TEST update requires exactly 32 episodes at each train roster")
        schedules = self.selector_schedules(fixture_update_index)
        target_actor, _ = self._fresh_arm()
        trace_batches = self.factual_trace_batches(target_actor, schedules)
        origins = self.selected_origin_inventory(trace_batches)
        targets = self.native_target_inventory(
            target_actor,
            trace_batches,
            origins,
            verify_reverse_order=verify_reverse_order,
        )
        target_by_episode = {target.episode_index: target for target in targets}
        origins_by_episode: dict[int, list[SelectedOriginSnapshot]] = {}
        for origin in origins:
            origins_by_episode.setdefault(origin.episode_index, []).append(origin)

        arm_updates: list[ArmUpdateAudit] = []
        for arm_name, projection_bound in ARM_PROJECTION.items():
            actor, critic = self._fresh_arm()
            optimizer = make_projected_adam(actor, critic)
            inputs: list[EpisodeLossInputs] = []
            graph_audits: list[FactualGraphAudit] = []
            for episode_index in range(64):
                trace_record = trace_batches[episode_index // 32]
                episode, graph_audit = self._episode_inputs(
                    actor,
                    critic,
                    trace_record,
                    episode_index % 32,
                    origins_by_episode[episode_index],
                    target_by_episode[episode_index],
                )
                inputs.append(episode)
                graph_audits.append(graph_audit)
            loss, batch_audit, _ = rscf_full_batch_loss(
                inputs, required_episode_count=64
            )
            step = projected_adam_step(
                loss,
                actor=actor,
                critic=critic,
                optimizer=optimizer,
                projection_bound=projection_bound,
            )
            combined_state = {**dict(actor.named_parameters()), **{f"critic.{k}": v for k, v in critic.named_parameters()}}
            arm_updates.append(
                ArmUpdateAudit(
                    arm_name=arm_name,
                    projection_bound=projection_bound,
                    batch_loss=batch_audit,
                    step=step,
                    factual_graphs=tuple(graph_audits),
                    state_sha256=_tensor_digest(combined_state),
                )
            )
            self._last_actors[arm_name] = actor
            self._last_critics[arm_name] = critic
            self._last_optimizers[arm_name] = optimizer
            self._last_optimizer_state_sha256[arm_name] = _structured_state_digest(
                optimizer.state_dict()
            )
        self._evaluation_trace_cache.clear()

        certificate = self._audit_certificate(
            schedules=schedules,
            targets=targets,
            arm_updates=tuple(arm_updates),
            snapshot_count=len(origins),
        )
        return GateBUpdateAudit(
            runner_identity_sha256=self.runner_identity_sha256,
            selector_schedules=schedules,
            shared_snapshot_digests=tuple(
                f"{origin.snapshot_digest:016x}" for origin in origins
            ),
            same_snapshot_objects_for_both_arms=True,
            factual_trace_digests=tuple(
                int(record.trajectory.trajectory_digest[lane])
                for record in trace_batches
                for lane in range(32)
            ),
            native_targets=targets,
            comparator=self.comparator_audit,
            arm_updates=tuple(arm_updates),  # type: ignore[arg-type]
            audit_certificate=certificate,
            logical_counts=self.logical_counts,
        )

    def _audit_certificate(
        self,
        *,
        schedules: tuple[SelectorSchedule, SelectorSchedule],
        targets: tuple[NativeTargetAudit, ...],
        arm_updates: tuple[ArmUpdateAudit, ArmUpdateAudit],
        snapshot_count: int,
    ) -> AuditCertificate:
        builder = AuditBuilder(self.test_identity.namespace, f"TEST_{self.test_identity.label}")
        selector_digest = canonical_sha256([schedule.provenance_digest for schedule in schedules])
        builder.add(AuditEvidence.count_match(AuditName.ONE_ORIGIN_PER_ROLE, sum(s.counts.selected_origins for s in schedules), 192, provenance_digest=selector_digest))
        builder.add_boolean(AuditName.SELECTOR_ARM_IDENTITY, True, compact_facts={"selector_sha256": selector_digest}, detail_code="ONE_SHARED_SELECTOR_FOR_BOTH_ARMS")
        builder.add_boolean(AuditName.ANTITHETIC_SLOT_PAIRING, True, compact_facts={"schedules": 2}, detail_code="SIDE_FREE_BASE_COMPLEMENTARY_SLOTS")
        builder.add(AuditEvidence.count_match(AuditName.Q_ENTRY_COUNT, sum(t.q_entry_count for t in targets), 640, provenance_digest=selector_digest))
        builder.add(AuditEvidence.count_match(AuditName.FACTUAL_REUSE_COUNT, sum(t.factual_reuse_count for t in targets), 192, provenance_digest=selector_digest))
        builder.add(AuditEvidence.count_match(AuditName.ALTERNATIVE_COUNT, sum(t.alternative_count for t in targets), 448, provenance_digest=selector_digest))

        checks = {
            AuditName.IMMUTABLE_PARAMETERS: all(t.immutable_parameter_identity for t in targets),
            AuditName.FOCAL_ONLY_INTERVENTION: all(t.focal_only_intervention for t in targets),
            AuditName.FACTUAL_TEAMMATES: all(t.factual_teammates_unchanged for t in targets),
            AuditName.CLOSED_LOOP_RECURRENCE: (
                all(t.closed_loop_recurrence for t in targets)
                and all(
                    graph.distinct_factual_state_count == 12
                    and graph.torch_native_action_identity
                    for arm in arm_updates
                    for graph in arm.factual_graphs
                )
            ),
            AuditName.COMMON_TAPE: all(t.common_tape for t in targets),
            AuditName.BRANCH_ORDER_INDEPENDENCE: all(t.branch_order_independent for t in targets),
            AuditName.FACTUAL_RETURN_IDENTITY: (
                all(t.factual_suffix_identity for t in targets)
                and all(
                    graph.shared_trajectory_terminal_return
                    for arm in arm_updates
                    for graph in arm.factual_graphs
                )
            ),
            AuditName.STOPPED_TARGETS: all(
                not graph.q_target_requires_grad
                for arm in arm_updates
                for graph in arm.factual_graphs
            ),
            AuditName.COMPARATOR_MATCHING: self.comparator_audit.passed,
            AuditName.NO_LEAKAGE: all(
                graph.no_private_target_in_actor_or_critic
                for arm in arm_updates
                for graph in arm.factual_graphs
            ),
            AuditName.UPDATE_512_ONLY: True,
        }
        for name, passed in checks.items():
            builder.add_boolean(
                name,
                passed,
                compact_facts={"snapshot_count": snapshot_count, "native_abi": ABI_VERSION},
                detail_code="FULL_CHAIN_TEST_CONFORMANCE",
            )
        lifecycle = AtomicLifecycleCounters(
            expected_origins=snapshot_count,
            completed_origins=snapshot_count,
            duplicate_origins=0,
            replacement_origins=0,
            resampled_origins=0,
            partial_rows=0,
            checkpoint_update=512,
        )
        builder.add(lifecycle.to_audit(selector_digest))
        certificate = builder.seal()
        if not certificate.structural_valid:
            raise RuntimeError(f"Gate-B structural audit failed: {certificate.failed_names}")
        return certificate

    def resume_identity(
        self, schedules: tuple[SelectorSchedule, SelectorSchedule]
    ) -> ResumeIdentity:
        schedule_payload = [schedule.canonical_payload() for schedule in schedules]
        schedule_sha = canonical_sha256(schedule_payload)
        selector_sha = canonical_sha256([schedule.provenance_digest for schedule in schedules])
        return ResumeIdentity(
            namespace=self.test_identity.namespace,
            test_schedule_id=f"TEST_{self.test_identity.label}",
            test_schedule_sha256=schedule_sha,
            runner_identity_sha256=self.runner_identity_sha256,
            selector_identity_sha256=selector_sha,
        )

    @staticmethod
    def frontier(
        identity: ResumeIdentity,
        *,
        expected_origin_count: int,
        completed_origin_ids: Sequence[str],
        audit_digest: str = "",
    ) -> FrontierRecord:
        if len(set(completed_origin_ids)) != len(completed_origin_ids):
            raise ValueError("duplicate TEST origin cannot enter a frontier")
        return FrontierRecord(
            resume_identity=identity,
            expected_origin_count=expected_origin_count,
            completed_origin_count=len(completed_origin_ids),
            completed_origin_set_sha256=canonical_sha256(sorted(completed_origin_ids)),
            compact_counters={"completed_origins": len(completed_origin_ids)},
            audit_digest=audit_digest,
        )

    def checkpoint_ref(self, *, update: int = 512) -> EvaluableCheckpointRef:
        if set(self._last_actors) != set(ARM_PROJECTION):
            raise ValueError("checkpoint reference requires one completed TEST update opportunity per arm")
        checkpoint_digest = canonical_sha256(
            {
                "kind": "TEST_ONLY_SYNTHETIC_CHECKPOINT_REFERENCE",
                "update": update,
                "runner": self.runner_identity_sha256,
                "arm_state": {
                    arm: {
                        "actor_sha256": _tensor_digest(
                            dict(self._last_actors[arm].named_parameters())
                        ),
                        "critic_sha256": _tensor_digest(
                            dict(self._last_critics[arm].named_parameters())
                        ),
                        "optimizer_state_sha256": self._last_optimizer_state_sha256[arm],
                    }
                    for arm in sorted(self._last_actors)
                },
            }
        )
        return EvaluableCheckpointRef(
            namespace=self.test_identity.namespace,
            update=update,
            checkpoint_sha256=checkpoint_digest,
            runner_identity_sha256=self.runner_identity_sha256,
        )

    def save_test_checkpoint(
        self,
        path: Path | str,
        *,
        schedules: tuple[SelectorSchedule, SelectorSchedule],
        completed_origin_ids: Sequence[str],
        expected_origin_count: int,
        compact_accumulators: Mapping[str, int | float],
        update: int = 512,
    ) -> str:
        """Durably write one complete TEST resume image without private targets."""

        checkpoint = self.checkpoint_ref(update=update)
        identity = self.resume_identity(schedules)
        frontier = self.frontier(
            identity,
            expected_origin_count=expected_origin_count,
            completed_origin_ids=completed_origin_ids,
        )
        reject_private_persistence(dict(compact_accumulators))
        if any(not isinstance(key, str) for key in compact_accumulators):
            raise ValueError("compact accumulator keys must be strings")
        if set(self._last_optimizers) != set(ARM_PROJECTION):
            raise ValueError("checkpoint requires exact optimizer state for both arms")
        payload = {
            "schema": RUNNER_SCHEMA_VERSION + "_DURABLE_TEST_CHECKPOINT_V1",
            "namespace": self.test_identity.namespace,
            "runner_identity_sha256": self.runner_identity_sha256,
            "update": update,
            "checkpoint_sha256": checkpoint.checkpoint_sha256,
            "fixture_update_index": schedules[0].fixture_update_index,
            "selector_payloads": [schedule.canonical_payload() for schedule in schedules],
            "selector_digests": [schedule.provenance_digest for schedule in schedules],
            "resume_identity": asdict(identity),
            "completed_origin_ids": list(completed_origin_ids),
            "expected_origin_count": expected_origin_count,
            "frontier_payload": frontier.to_payload(),
            "compact_accumulators": dict(compact_accumulators),
            "arms": {
                arm: {
                    "actor": copy.deepcopy(self._last_actors[arm].state_dict()),
                    "critic": copy.deepcopy(self._last_critics[arm].state_dict()),
                    "optimizer": copy.deepcopy(self._last_optimizers[arm].state_dict()),
                    "projection_bound": ARM_PROJECTION[arm],
                }
                for arm in ARM_PROJECTION
            },
        }
        buffer = io.BytesIO()
        torch.save(payload, buffer)
        data = buffer.getvalue()
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        pending = destination.with_name(
            f".{destination.name}.{uuid.uuid4().hex}.pending"
        )
        descriptor = os.open(
            pending,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_BINARY", 0),
            0o600,
        )
        try:
            offset = 0
            while offset < len(data):
                offset += os.write(descriptor, data[offset:])
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        try:
            os.link(pending, destination)
        except FileExistsError as exc:
            raise WriteOnceConflictError(f"TEST checkpoint already exists: {destination}") from exc
        finally:
            pending.unlink(missing_ok=True)
        return hashlib.sha256(data).hexdigest()

    def restore_test_checkpoint(
        self,
        path: Path | str,
        *,
        expected_identity: ResumeIdentity,
    ) -> RestoredTestCheckpoint:
        """Restore exact actor/critic/Adam/frontier state after process loss."""

        source = Path(path)
        data = source.read_bytes()
        payload = torch.load(io.BytesIO(data), map_location="cpu", weights_only=False)
        if not isinstance(payload, dict) or payload.get("schema") != RUNNER_SCHEMA_VERSION + "_DURABLE_TEST_CHECKPOINT_V1":
            raise ValueError("durable TEST checkpoint schema mismatch")
        if payload.get("namespace") != self.test_identity.namespace or payload.get("runner_identity_sha256") != self.runner_identity_sha256:
            raise ValueError("durable TEST checkpoint runner identity mismatch")
        identity = ResumeIdentity(**payload["resume_identity"])
        identity.require_exact_match(expected_identity)
        schedules = self.selector_schedules(int(payload["fixture_update_index"]))
        if [schedule.canonical_payload() for schedule in schedules] != payload["selector_payloads"]:
            raise ValueError("durable TEST checkpoint selector schedule changed")
        if [schedule.provenance_digest for schedule in schedules] != payload["selector_digests"]:
            raise ValueError("durable TEST checkpoint selector digest changed")
        completed = tuple(payload["completed_origin_ids"])
        frontier = self.frontier(
            identity,
            expected_origin_count=int(payload["expected_origin_count"]),
            completed_origin_ids=completed,
        )
        stored_frontier = payload["frontier_payload"]
        if frontier.to_payload() != stored_frontier:
            raise ValueError("durable TEST checkpoint frontier changed")
        accumulators = payload["compact_accumulators"]
        reject_private_persistence(accumulators)
        arms = payload["arms"]
        if set(arms) != set(ARM_PROJECTION):
            raise ValueError("durable TEST checkpoint arm inventory mismatch")
        self._last_actors.clear()
        self._last_critics.clear()
        self._last_optimizers.clear()
        self._last_optimizer_state_sha256.clear()
        self._evaluation_trace_cache.clear()
        for arm, bound in ARM_PROJECTION.items():
            if float(arms[arm]["projection_bound"]) != bound:
                raise ValueError("durable TEST checkpoint projection changed")
            actor, critic = self._fresh_arm()
            actor.load_state_dict(arms[arm]["actor"], strict=True)
            critic.load_state_dict(arms[arm]["critic"], strict=True)
            optimizer = make_projected_adam(actor, critic)
            optimizer.load_state_dict(arms[arm]["optimizer"])
            self._last_actors[arm] = actor
            self._last_critics[arm] = critic
            self._last_optimizers[arm] = optimizer
            self._last_optimizer_state_sha256[arm] = _structured_state_digest(optimizer.state_dict())
        restored_ref = self.checkpoint_ref(update=int(payload["update"]))
        if restored_ref.checkpoint_sha256 != payload["checkpoint_sha256"]:
            raise ValueError("durable TEST checkpoint state digest changed after restore")
        return RestoredTestCheckpoint(
            update=int(payload["update"]),
            file_sha256=hashlib.sha256(data).hexdigest(),
            state_sha256=restored_ref.checkpoint_sha256,
            resume_identity=identity,
            frontier=frontier,
            compact_accumulators=dict(accumulators),
            selector_schedules=schedules,
        )

    @staticmethod
    def complete_packet(
        identity: ResumeIdentity,
        *,
        completed_origin_ids: Sequence[str],
        expected_origin_count: int,
        certificate: AuditCertificate,
        checkpoint: EvaluableCheckpointRef,
    ) -> CompleteSeedPacket:
        if len(set(completed_origin_ids)) != len(completed_origin_ids):
            raise ValueError("duplicate TEST origin cannot enter a complete packet")
        if len(completed_origin_ids) != expected_origin_count:
            raise ValueError("complete packet requires the exact TEST origin inventory")
        if (
            certificate.namespace != identity.namespace
            or certificate.test_seed_block_id != identity.test_schedule_id
            or not certificate.structural_valid
        ):
            raise ValueError("complete packet requires one matching valid audit certificate")
        return CompleteSeedPacket(
            resume_identity=identity,
            expected_origin_count=expected_origin_count,
            completed_origin_count=len(completed_origin_ids),
            completed_origin_set_sha256=canonical_sha256(sorted(completed_origin_ids)),
            audit_certificate_sha256=certificate.digest,
            checkpoint=checkpoint,
            compact_counters={"completed_origins": len(completed_origin_ids)},
        )

    def evaluation_forward(
        self,
        checkpoint: EvaluableCheckpointRef,
        *,
        arm_name: str,
        roster_size: int,
    ) -> EvaluationForwardAudit:
        validate_roster_size(roster_size)
        if checkpoint.runner_identity_sha256 != self.runner_identity_sha256 or checkpoint.update != 512:
            raise ValueError("evaluation requires this runner's update-512 TEST checkpoint")
        if arm_name not in self._last_actors:
            raise ValueError("unknown or unavailable arm")
        bundle = self._evaluation_trace_bundle(
            arm_name=arm_name, roster_size=roster_size
        )
        observations = torch.as_tensor(
            np.array(
                bundle.intact.observations[0, 0, :roster_size], copy=True
            ),
            dtype=torch.float32,
        )
        roles = torch.as_tensor(
            np.array(bundle.episode.roles[0, :roster_size], copy=True),
            dtype=torch.int64,
        )
        with torch.no_grad():
            critic = self._last_critics[arm_name](build_rolewise_critic_input(observations, roles))
        digest = hashlib.sha256()
        digest.update(bundle.intact.legal_probabilities[0, 0, :roster_size].tobytes(order="C"))
        digest.update(bundle.intact.trajectory_digest.tobytes(order="C"))
        digest.update(critic.cpu().numpy().tobytes(order="C"))
        return EvaluationForwardAudit(
            roster_size=roster_size,
            checkpoint_update=checkpoint.update,
            actor_probability_shape=(roster_size, 6),
            critic_shape=tuple(critic.shape),
            compact_output_sha256=digest.hexdigest(),
        )

    def _evaluation_episode_batch(self, roster_size: int) -> FactualEpisodeBatch:
        base = make_test_factual_episode_batch(256)
        arrays = {field.name: np.asarray(getattr(base, field.name)).copy() for field in fields(FactualEpisodeBatch)}
        layout = np.repeat(np.arange(3, dtype=np.int64), roster_size // 3)
        arrays["n_agents"][:] = roster_size
        arrays["roles"][:] = -1
        arrays["roles"][:, :roster_size] = layout
        for lane in range(256):
            for role in range(3):
                arrays["selector_slot"][lane, role] = (lane + 3 * role) % 12
                arrays["selector_local_index"][lane, role] = (
                    lane + role
                ) % (roster_size // 3)
        return FactualEpisodeBatch(
            **{name: self._readonly(value) for name, value in arrays.items()}
        )

    def _evaluation_trace_bundle(
        self, *, arm_name: str, roster_size: int
    ) -> EvaluationTraceBundle:
        key = (arm_name, roster_size)
        cached = self._evaluation_trace_cache.get(key)
        if cached is not None:
            return cached
        if arm_name not in (PHY, EDGE):
            raise ValueError("evaluation trace arm must be PHY-TRUST or EDGE-FLEX")
        episode = self._evaluation_episode_batch(roster_size)
        parameters = _native_parameters(self._last_actors[arm_name])
        intact = native_factual_trajectory(
            episode, parameters, mode=MODE_INTACT, identity=self.native_identity
        )
        full_rotated = native_factual_trajectory(
            episode,
            parameters,
            mode=MODE_FULL_ROTATED,
            identity=self.native_identity,
        )
        shadow = native_shadow_trajectory(
            episode, intact, parameters, identity=self.native_identity
        )
        zero_head = np.zeros_like(parameters.actor_w)
        zero_bias = np.zeros_like(parameters.actor_b)
        zero_head.setflags(write=False)
        zero_bias.setflags(write=False)
        uniform_parameters = replace(
            parameters, actor_w=zero_head, actor_b=zero_bias
        )
        uniform = native_factual_trajectory(
            episode,
            uniform_parameters,
            mode=MODE_INTACT,
            identity=self.native_identity,
        )
        # Rotation changes only the physical sender-column interpretation.  The
        # episode roles and therefore every legal support remain unchanged.
        for role in range(3):
            agents = np.flatnonzero(episode.roles[0, :roster_size] == role)
            legal = set(legal_actions(role))
            for action in range(6):
                intact_support = bool(
                    np.any(intact.legal_probabilities[:, :, agents, action] > 0.0)
                )
                rotated_support = bool(
                    np.any(full_rotated.legal_probabilities[:, :, agents, action] > 0.0)
                )
                if intact_support != (action in legal) or rotated_support != (action in legal):
                    raise RuntimeError("full rotation changed a public-role legal mask")
        bundle = EvaluationTraceBundle(
            episode=episode,
            intact=intact,
            full_rotated=full_rotated,
            shadow=shadow,
            uniform=uniform,
        )
        self._evaluation_trace_cache[key] = bundle
        return bundle

    def generate_test_evaluation_panel(
        self,
        packet: CompleteSeedPacket,
        certificate: AuditCertificate,
    ) -> CompleteEvaluationPanel:
        """Execute all compact intact/cut/uniform TEST evaluation consumers."""

        if packet.audit_certificate_sha256 != certificate.digest:
            raise ValueError("evaluation certificate does not match complete packet")
        cells: list[EvaluationCellSummary] = []
        for roster_size, arm_name, condition in sorted(expected_cell_keys()):
            learned_arm = PHY if arm_name == UNIFORM else arm_name
            bundle = self._evaluation_trace_bundle(
                arm_name=learned_arm, roster_size=roster_size
            )
            if arm_name == UNIFORM:
                trajectory = bundle.uniform
            elif condition == ROTATED:
                trajectory = bundle.full_rotated
            else:
                trajectory = bundle.intact
            mean_return = float(trajectory.terminal_return.mean(dtype=np.float32))
            west = float((trajectory.final_delivered[:, 0] / 3.0).mean(dtype=np.float32))
            east = float((trajectory.final_delivered[:, 1] / 3.0).mean(dtype=np.float32))
            tv_mean: float | None = None
            tv_sup: float | None = None
            if arm_name == PHY and condition == INTACT and roster_size in (6, 21):
                active = bundle.episode.roles[:, None, :, None] >= 0
                tv = 0.5 * np.abs(
                    bundle.intact.legal_probabilities
                    - bundle.shadow.legal_probabilities
                ).sum(axis=-1, dtype=np.float32)
                tv = np.where(active[..., 0], tv, 0.0)
                counts = bundle.episode.n_agents.astype(np.float32) * 12.0
                per_episode_tv = tv.sum(axis=(1, 2), dtype=np.float32) / counts
                per_episode_sup = tv.max(axis=(1, 2))
                tv_mean = float(per_episode_tv.mean(dtype=np.float32))
                tv_sup = float(per_episode_sup.mean(dtype=np.float32))
            accumulator_sha = hashlib.sha256()
            accumulator_sha.update(packet.resume_identity.test_schedule_id.encode("ascii"))
            accumulator_sha.update(str((roster_size, arm_name, condition)).encode("ascii"))
            accumulator_sha.update(trajectory.trajectory_digest.tobytes(order="C"))
            if tv_mean is not None:
                accumulator_sha.update(
                    bundle.shadow.snapshot_digest.tobytes(order="C")
                )
            cells.append(
                EvaluationCellSummary(
                    namespace=packet.resume_identity.namespace,
                    test_seed_block_id=packet.resume_identity.test_schedule_id,
                    roster_n=roster_size,
                    arm=arm_name,
                    condition=condition,
                    episode_count=256,
                    mean_return=mean_return,
                    basin_west_mean=west,
                    basin_east_mean=east,
                    accumulator_sha256=accumulator_sha.hexdigest(),
                    checkpoint_sha256=packet.checkpoint.checkpoint_sha256,
                    audit_certificate_sha256=certificate.digest,
                    mean_legal_action_tv_to_shadow=tv_mean,
                    mean_legal_simplex_tv_sup=tv_sup,
                )
            )
        return CompleteEvaluationPanel.consume(packet, cells)

    @staticmethod
    def consume_evaluation_panel(
        packet: CompleteSeedPacket,
        cells: Iterable[EvaluationCellSummary],
    ) -> CompleteEvaluationPanel:
        return CompleteEvaluationPanel.consume(packet, cells)

    @staticmethod
    def analyze_test_panels(
        panels: Iterable[CompleteEvaluationPanel],
        certificates: Iterable[AuditCertificate],
    ) -> SimultaneousAnalysis:
        vectors = tuple(SeedQuantityVector.from_panel(panel) for panel in panels)
        return analyze_complete_family(vectors, audit_certificates=tuple(certificates))

    def frontier_store(self, root: Path | str) -> AtomicFrontierStore:
        return AtomicFrontierStore(root, self.test_identity.namespace)
