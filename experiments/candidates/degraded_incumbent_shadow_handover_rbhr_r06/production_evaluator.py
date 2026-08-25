"""Checkpoint-loaded five-arm, mask-on/off evaluation flow for r06."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import inspect
from typing import Final, Iterable, Mapping, Protocol

import numpy as np

from .production_backend import NativeBatch, native_batch_from_rows
from .production_contract import ARMS, COMPONENT, MASK_VIEWS, TICKS_PER_EPISODE
from .production_population import EvaluationCoordinate, address, complete_evaluation_coordinates
from .production_recurrent_trainer import AddressedPolicySampler, BatchedRecurrentPolicy, RecurrentRolloutState


EVALUATION_BATCH_WIDTH: Final = 32


class EvaluationFlowError(RuntimeError):
    pass


@dataclass(frozen=True, order=True)
class EvaluationItem:
    coordinate: EvaluationCoordinate
    mask_view: str
    arm: str

    def validate(self) -> None:
        if self.mask_view not in MASK_VIEWS or self.arm not in ARMS:
            raise EvaluationFlowError("evaluation arm or mask view differs")

    def canonical_key(self) -> str:
        self.validate()
        return f"{self.coordinate.canonical_key()}/{self.mask_view}/{self.arm}"


def complete_evaluation_plan() -> tuple[EvaluationItem, ...]:
    rows = tuple(
        EvaluationItem(coordinate, mask_view, arm)
        for coordinate in complete_evaluation_coordinates()
        for mask_view in MASK_VIEWS
        for arm in ARMS
    )
    if len(rows) != 115_200 or len({row.canonical_key() for row in rows}) != 115_200:
        raise EvaluationFlowError("complete evaluation plan differs")
    return rows


class EvaluationBatchFactory(Protocol):
    def open_batch(self, items: tuple[EvaluationItem, ...]) -> tuple[NativeBatch, Mapping[str, np.ndarray]]: ...


class EvaluationForkObserver(Protocol):
    def observe(
        self, *, tick: int, native: NativeBatch, step_rows: np.ndarray,
        observation: Mapping[str, np.ndarray], policy_state: RecurrentRolloutState,
    ) -> None: ...
    def complete(self) -> tuple[Mapping[str, object], ...]: ...


class MasterAddressedEvaluationBatchFactory:
    """Lease-bound deterministic evaluation reset rows with paired mask views."""

    def __init__(self, *, authority: object, master: bytes) -> None:
        require = getattr(authority, "require_active", None)
        if not callable(require):
            raise EvaluationFlowError("evaluation factory requires Root lease authority")
        require()
        if getattr(authority, "component", None) != COMPONENT:
            raise EvaluationFlowError("evaluation lease component differs")
        self.master = bytes(master)
        if len(self.master) != 32:
            raise EvaluationFlowError("evaluation master must be exactly 256 bits")

    def _phase(self, coordinate: EvaluationCoordinate) -> int:
        value = address(
            purpose="K_SCHEDULE", block=coordinate.block, split=coordinate.split,
            regime=coordinate.regime, schedule=coordinate.schedule,
            evaluation_slot=None, field="PHASE_OFFSET", draw_index=0,
        )
        digest = hashlib.sha256(self.master + b"\0" + value.encode("ascii")).digest()
        uniform = ((int.from_bytes(digest[:8], "big") >> 11) + 0.5) / 2**53
        return coordinate.phase(int(coordinate.k_pair[0] * uniform))

    def _row(self, item: EvaluationItem) -> Mapping[str, object]:
        item.validate(); coordinate = item.coordinate
        fixture_key = int.from_bytes(hashlib.sha256(
            self.master + b"\0" + item.canonical_key().encode("ascii")
        ).digest()[:8], "big")
        return {
            "fixture_key": fixture_key, "master": self.master.hex(), "test_mode": 0,
            "package": ("TARGET_VISUAL_MASK", "TERRAIN_RELAY_MASK").index(coordinate.regime),
            "reflection": coordinate.reflection, "initial_owner": coordinate.initial_owner,
            "qa_owner": coordinate.qa_owner, "k_initial": coordinate.k_pair[0],
            "k_new": coordinate.k_pair[1], "switch_tick": coordinate.switch_tick,
            "tau_d_tick": coordinate.tau_d_tick, "phase": self._phase(coordinate),
            "route_speed": coordinate.route_speed, "turn_magnitude_deg": coordinate.turn_magnitude_deg,
            "turn_sign": coordinate.turn_sign, "initial_ux": coordinate.initial_ux,
            "initial_uy": coordinate.initial_uy, "block": coordinate.block,
            "split": 1 if coordinate.split == "CLAIM" else 2,
            "schedule": ("K4", "K8", "K12", "K4_TO_K12", "K12_TO_K4").index(coordinate.schedule),
            "evaluation_slot": coordinate.evaluation_slot, "lane": -1, "cycle": -1,
            "arm_substream": 0, "degradation_flag": 0,
            "mask_enabled": int(item.mask_view == "DEGRADED"),
            "fork_branch": 0, "episode": -1,
        }

    def open_batch(self, items: tuple[EvaluationItem, ...]) -> tuple[NativeBatch, Mapping[str, np.ndarray]]:
        if len(items) != EVALUATION_BATCH_WIDTH:
            raise EvaluationFlowError("evaluation reset batch must contain exactly 32 items")
        batch = native_batch_from_rows(tuple(self._row(item) for item in items))
        return batch, batch.observe()


@dataclass(frozen=True)
class EvaluationTelemetry:
    item_keys: tuple[str, ...]
    service: np.ndarray
    energy: np.ndarray
    hard_events: np.ndarray
    application_reason: np.ndarray
    cas_applied: np.ndarray
    owner: np.ndarray
    protocol_wire_hash: np.ndarray
    fork_receipts: tuple[Mapping[str, object], ...] = ()

    def validate(self) -> None:
        width = len(self.item_keys)
        if self.service.shape != (width, 1_200) or self.energy.shape != (width, 1_200):
            raise EvaluationFlowError("evaluation telemetry tick shape differs")
        if self.hard_events.shape != (width, 1_200, 7):
            raise EvaluationFlowError("evaluation hard-event telemetry differs")
        for value in (self.application_reason, self.cas_applied, self.owner, self.protocol_wire_hash):
            if value.shape != (width, 1_200):
                raise EvaluationFlowError("evaluation protocol telemetry differs")


class CheckpointLoadedFiveArmEvaluator:
    """Run complete native episodes with deterministic checkpoint actions."""

    def __init__(
        self, *, checkpoints: Mapping[tuple[int, str], bytes], batch_factory: EvaluationBatchFactory,
        deterministic_sampler: AddressedPolicySampler,
        fork_observer: EvaluationForkObserver | None = None,
    ) -> None:
        expected = {(block, arm) for block in range(24) for arm in ARMS}
        if set(checkpoints) != expected or any(not bytes(value) for value in checkpoints.values()):
            raise EvaluationFlowError("120 block-arm sole checkpoints are required")
        self.checkpoints = {key: bytes(value) for key, value in checkpoints.items()}
        self.batch_factory = batch_factory; self.deterministic_sampler = deterministic_sampler
        self.fork_observer = fork_observer

    def run_batch(self, items: tuple[EvaluationItem, ...]) -> EvaluationTelemetry:
        if len(items) != EVALUATION_BATCH_WIDTH:
            raise EvaluationFlowError("evaluation batch width differs")
        arm = items[0].arm
        block = items[0].coordinate.block
        if any(item.arm != arm or item.coordinate.block != block for item in items):
            raise EvaluationFlowError("one evaluation batch must bind one block-arm checkpoint")
        native, observation = self.batch_factory.open_batch(items)
        if native.width != len(items):
            raise EvaluationFlowError("evaluation native width differs")
        # Policy execution is batched across tapes.  NativeBatch owns all host
        # transitions; Python owns only the frozen batched PyTorch forward.
        state = RecurrentRolloutState.fresh(arm)
        policy = BatchedRecurrentPolicy(arm=arm, checkpoint_bytes=self.checkpoints[(block, arm)], state=state)
        captured: dict[str, list[np.ndarray]] = {name: [] for name in (
            "service", "total_energy", "invalid_commit", "token_gap", "dual_owner",
            "dual_payload", "buffer_clear", "command_slew_breach", "separation_breach",
            "application_reason", "cas_applied", "owner", "protocol_wire_hash",
        )}
        for tick in range(TICKS_PER_EPISODE):
            step_rows = policy.step_rows(observation, sampler=self.deterministic_sampler, global_tick=tick, deterministic=True)
            if self.fork_observer is not None:
                self.fork_observer.observe(
                    tick=tick, native=native, step_rows=step_rows,
                    observation=observation, policy_state=policy.state,
                )
            owner_before = np.asarray(observation["owner"], dtype=np.int64)
            observation = native.step(step_rows)
            policy.apply_native_promotion(
                owner_before=owner_before, step_rows=step_rows, observation_after=observation,
            )
            for name in captured:
                captured[name].append(np.asarray(observation[name]).copy())
        stacked = {name: np.stack(values, axis=1) for name, values in captured.items()}
        hard = np.stack([stacked[name] > 0 for name in (
            "invalid_commit", "token_gap", "dual_owner", "dual_payload", "buffer_clear",
            "command_slew_breach", "separation_breach",
        )], axis=2).astype(np.int8)
        result = EvaluationTelemetry(
            tuple(item.canonical_key() for item in items), stacked["service"].astype(np.int8),
            stacked["total_energy"].astype(np.float64), hard,
            stacked["application_reason"].astype(np.int16), stacked["cas_applied"].astype(np.int8),
            stacked["owner"].astype(np.int8), stacked["protocol_wire_hash"].astype(np.uint64),
            () if self.fork_observer is None else self.fork_observer.complete(),
        )
        result.validate(); return result

    def iter_complete_batches(self) -> Iterable[tuple[EvaluationItem, ...]]:
        plan = complete_evaluation_plan()
        # Group by arm so every batch has exactly one loaded checkpoint.
        for block in range(24):
            for arm in ARMS:
                arm_rows = tuple(row for row in plan if row.coordinate.block == block and row.arm == arm)
                for start in range(0, len(arm_rows), EVALUATION_BATCH_WIDTH):
                    yield arm_rows[start:start + EVALUATION_BATCH_WIDTH]


def flow_local_evaluator_self_audit() -> dict[str, object]:
    plan = complete_evaluation_plan()
    encoded = ("\n".join(row.canonical_key() for row in plan) + "\n").encode("ascii")
    source = inspect.getsource(CheckpointLoadedFiveArmEvaluator)
    return {
        "schema": "DISH_RBHR_R06_E1_FIVE_ARM_EVALUATOR_FLOW_LOCAL_SELF_AUDIT_V1",
        "evaluation_items": len(plan), "base_tapes": len(plan) // (len(MASK_VIEWS) * len(ARMS)),
        "arms": list(ARMS), "mask_views": list(MASK_VIEWS),
        "ticks_per_episode": TICKS_PER_EPISODE, "batch_width_max": EVALUATION_BATCH_WIDTH,
        "plan_unique": len({row.canonical_key() for row in plan}) == len(plan),
        "checkpoint_loaded": "checkpoints" in source and "BatchedRecurrentPolicy" in source,
        "block_arm_checkpoints": 120,
        "native_first": "NativeBatch" in inspect.getsource(EvaluationBatchFactory),
        "plan_sha256": hashlib.sha256(encoded).hexdigest(),
        "model_instantiated": False, "evaluation_activity": False,
        "evaluation_output": False, "question_relevant_output": False,
    }


__all__ = [
    "CheckpointLoadedFiveArmEvaluator", "EvaluationBatchFactory", "MasterAddressedEvaluationBatchFactory", "EvaluationFlowError",
    "EvaluationForkObserver", "EvaluationItem", "EvaluationTelemetry", "complete_evaluation_plan",
    "flow_local_evaluator_self_audit",
]
