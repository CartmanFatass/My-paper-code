"""Direct multi-lane bridge to the accepted package C++ batch ABI."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Sequence, TypeVar

import numpy as np

from ..host import native_endpoint
from ..native.native_abi import (
    ABI_VERSION, STATE_VERSION, NativeStateV1, ObservationOutputV1,
    ResetInputV1, StepInputV1, StepOutputV1,
)
from ..native_adapter import admit_package_native_adapter
from .constants import HORIZON, WORKER_EQUIVALENCE_COUNTS
from .contract import B01ContractError


@dataclass(frozen=True, slots=True)
class BatchObservation:
    observations: np.ndarray
    roles: np.ndarray
    legal_masks: np.ndarray
    slots: tuple[int, ...]
    terminals: tuple[bool, ...]


@dataclass(frozen=True, slots=True)
class NativePrimitives:
    dw: int
    de: int
    waste: float
    duplicate: int
    expired: int
    collision: int
    empty_radio: int
    radio_actions: int
    waste_actions: int
    successful_deliveries: int


@dataclass(frozen=True, slots=True)
class BatchStep:
    terminals: tuple[bool, ...]
    returns: tuple[float, ...]
    primitives: tuple[NativePrimitives, ...]
    previous_success: np.ndarray


_LEDGER_TOKEN = object()


@dataclass(frozen=True, slots=True, init=False)
class BatchWorkLedger:
    lanes: int
    native_reset_calls: int
    native_observe_calls: int
    native_step_calls: int
    environment_slots: int

    def __init__(
        self, token: object, *, lanes: int, native_reset_calls: int,
        native_observe_calls: int, native_step_calls: int, environment_slots: int,
    ) -> None:
        if token is not _LEDGER_TOKEN:
            raise B01ContractError("native work ledger must come directly from B01 environment")
        object.__setattr__(self, "lanes", lanes)
        object.__setattr__(self, "native_reset_calls", native_reset_calls)
        object.__setattr__(self, "native_observe_calls", native_observe_calls)
        object.__setattr__(self, "native_step_calls", native_step_calls)
        object.__setattr__(self, "environment_slots", environment_slots)


class B01NativeBatchEnvironment:
    """Homogeneous-roster native lanes; every operation crosses batch_count>0."""

    production_admissible = True
    TEST_ONLY = False

    def __init__(self, adapter: object, *, roster: int, lanes: int) -> None:
        if roster not in (6, 9, 15, 21):
            raise B01ContractError("B01 native batch roster is invalid")
        self._adapter = admit_package_native_adapter(adapter)
        if type(lanes) is not int or not 1 <= lanes <= self._adapter.contract.native_width:
            raise B01ContractError("B01 lanes must lie within native_width")
        self.roster = roster
        self.lanes = lanes
        self._states = (NativeStateV1 * lanes)()
        self._reset = False
        self._reset_calls = self._observe_calls = self._step_calls = self._slots = 0

    def reset(self, tapes: Sequence[object]) -> None:
        if len(tapes) != self.lanes:
            raise B01ContractError("B01 batch reset requires one tape per lane")
        inputs = (ResetInputV1 * self.lanes)()
        for lane, tape in enumerate(tapes):
            if not hasattr(tape, "native_environment_payload"):
                raise B01ContractError("B01 batch tape lacks a native payload")
            payload = tape.native_environment_payload()
            if payload.roster != self.roster:
                raise B01ContractError("B01 batch requires a homogeneous roster")
            row = inputs[lane]
            row.abi_version = ABI_VERSION
            row.state_version = STATE_VERSION
            row.roster = self.roster
            for basin in range(2):
                for ordinal in range(3):
                    row.event_times[basin][ordinal] = int(payload.event_times[basin, ordinal])
            for slot in range(HORIZON):
                for sender in range(21):
                    row.detection_uniforms[slot][sender] = float(
                        payload.detection_uniforms[slot, sender]
                    )
                    row.base_uniforms[slot][sender] = float(payload.base_uniforms[slot, sender])
                    for receiver in range(21):
                        row.uplink_uniforms[slot][sender][receiver] = float(
                            payload.uplink_uniforms[slot, sender, receiver]
                        )
        self._adapter.reset_batch(self._states, inputs, batch_count=self.lanes)
        self._reset = True
        self._reset_calls += 1

    def observe(self) -> BatchObservation:
        if not self._reset:
            raise B01ContractError("B01 batch must be reset before observation")
        outputs = (ObservationOutputV1 * self.lanes)()
        self._adapter.observe_batch(self._states, outputs, batch_count=self.lanes)
        observations = np.empty((self.lanes, self.roster, 22), dtype=np.float32)
        roles = np.empty((self.lanes, self.roster), dtype=np.int64)
        masks = np.empty((self.lanes, self.roster, 6), dtype=np.bool_)
        slots: list[int] = []
        terminals: list[bool] = []
        for lane, row in enumerate(outputs):
            slots.append(int(row.slot))
            terminals.append(bool(row.terminal))
            for entity in range(self.roster):
                roles[lane, entity] = int(row.roles[entity])
                for field in range(22):
                    observations[lane, entity, field] = float(row.observations[entity][field])
                for action in range(6):
                    masks[lane, entity, action] = bool(row.legal_masks[entity][action])
        self._observe_calls += 1
        return BatchObservation(observations, roles, masks, tuple(slots), tuple(terminals))

    def step(self, actions: np.ndarray | Sequence[Sequence[int]]) -> BatchStep:
        if not self._reset:
            raise B01ContractError("B01 batch must be reset before step")
        values = np.asarray(actions)
        if values.shape != (self.lanes, self.roster) or values.dtype.kind not in "iu":
            raise B01ContractError("B01 batch actions must be integer [lanes,roster]")
        inputs = (StepInputV1 * self.lanes)()
        outputs = (StepOutputV1 * self.lanes)()
        for lane in range(self.lanes):
            inputs[lane].abi_version = ABI_VERSION
            for entity in range(self.roster):
                action = int(values[lane, entity])
                if not 0 <= action < 6:
                    raise B01ContractError("B01 batch action is outside [0,5]")
                inputs[lane].actions[entity] = action
        self._adapter.step_batch(self._states, inputs, outputs, batch_count=self.lanes)
        terminals: list[bool] = []
        returns: list[float] = []
        primitives: list[NativePrimitives] = []
        successes = np.empty((self.lanes, self.roster), dtype=np.bool_)
        for lane, row in enumerate(outputs):
            metrics = row.metrics
            terminals.append(bool(row.terminal))
            returns.append(native_endpoint(int(metrics.dw), int(metrics.de), float(metrics.waste)))
            primitives.append(NativePrimitives(
                dw=int(metrics.dw), de=int(metrics.de), waste=float(metrics.waste),
                duplicate=int(metrics.duplicate_arrivals),
                expired=int(metrics.expired_arrivals), collision=int(metrics.collision_loss),
                empty_radio=int(metrics.empty_actions), radio_actions=int(metrics.radio_actions),
                waste_actions=int(metrics.waste_actions),
                successful_deliveries=int(metrics.new_timely_deliveries),
            ))
            for entity in range(self.roster):
                # Direct post-step POD fact, including the terminal transition.
                successes[lane, entity] = bool(self._states[lane].previous_success[entity])
        self._step_calls += 1
        self._slots += self.lanes
        return BatchStep(tuple(terminals), tuple(returns), tuple(primitives), successes)

    def snapshot(self) -> bytes:
        if not self._reset:
            raise B01ContractError("B01 batch must be reset before snapshot")
        return self._adapter.snapshot_batch(self._states, batch_count=self.lanes)

    def restore(self, snapshot: bytes) -> None:
        self._adapter.restore_batch(self._states, snapshot, batch_count=self.lanes)
        self._reset = True

    def work_ledger(self) -> BatchWorkLedger:
        return BatchWorkLedger(
            _LEDGER_TOKEN, lanes=self.lanes, native_reset_calls=self._reset_calls,
            native_observe_calls=self._observe_calls, native_step_calls=self._step_calls,
            environment_slots=self._slots,
        )


T = TypeVar("T")
R = TypeVar("R")


def bounded_worker_map(
    function: Callable[[T], R], tasks: Sequence[T], *, workers: int,
) -> tuple[R, ...]:
    """Stable-index bounded worker topology used by B01 orchestration.

    Worker count may change scheduling only.  Returned order is always task
    order, which makes 1/2/4-worker equivalence directly testable.
    """

    if workers not in WORKER_EQUIVALENCE_COUNTS:
        raise B01ContractError("B01 worker count must be one of 1, 2, or 4")
    if workers == 1:
        return tuple(function(task) for task in tasks)
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="frrie-b01") as pool:
        return tuple(pool.map(function, tasks))


def performance_readiness(evidence: Any) -> str:
    """Validate direct telemetry/equivalence evidence; no caller booleans."""

    fields = {
        "schema", "disposition", "blocker", "measured_at",
        "end_to_end_wall_seconds", "scientific_slots", "slots_per_second",
        "cpu_seconds", "cpu_occupancy_fraction", "process_tree_peak_rss_bytes",
        "scratch_peak_bytes", "durable_peak_bytes", "read_bytes", "write_bytes",
        "worker_peak", "scalar_batch_equivalence", "worker_equivalence",
    }
    if not isinstance(evidence, dict) or set(evidence) != fields:
        raise B01ContractError("performance evidence fields differ")
    disposition = evidence["disposition"]
    if disposition == "REPAIR_REQUIRED":
        if not isinstance(evidence["blocker"], str) or not evidence["blocker"]:
            raise B01ContractError("REPAIR_REQUIRED requires an exact blocker")
        return disposition
    if disposition != "PERFORMANCE_READY" or evidence["blocker"] is not None:
        raise B01ContractError("unknown performance disposition")
    # READY cannot be synthesized from summary booleans.  The current B01
    # runner does not yet emit direct scalar/batch rows, 1/2/4-worker rows,
    # and sampled process-tree telemetry in one evidence object.
    raise B01ContractError(
        "PERFORMANCE_READY direct row-level runner evidence is not implemented"
    )
