"""First-application-valid paired REAL/SHAM flow for frozen r06."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import inspect
from typing import Final, Mapping

import numpy as np
import torch

from .production_backend import NativeBatch
from .production_recurrent_trainer import AddressedPolicySampler, BatchedRecurrentPolicy, RecurrentRolloutState


FORK_TICKS: Final = 100


class RealShamFlowError(RuntimeError):
    pass


class _RemappedSampler:
    def __init__(self, parent: AddressedPolicySampler, lanes: np.ndarray) -> None:
        self.parent = parent; self.lanes = np.asarray(lanes, dtype=np.int64)

    def normal(self, *, lane: int, tick: int, field: str) -> float:
        return self.parent.normal(lane=int(self.lanes[lane]), tick=tick, field=field)

    def bernoulli(self, *, lane: int, tick: int, field: str, probability: float) -> int:
        return self.parent.bernoulli(lane=int(self.lanes[lane]), tick=tick, field=field, probability=probability)


@dataclass(frozen=True)
class ForkTelemetry:
    source_lanes: tuple[int, ...]
    origin_tick: int
    real_service: np.ndarray
    sham_service: np.ndarray
    real_energy_delta: np.ndarray
    sham_energy_delta: np.ndarray
    real_hard_events: np.ndarray
    sham_hard_events: np.ndarray
    transaction_telemetry_sha256: str

    def validate(self) -> None:
        width = len(self.source_lanes)
        if not width or self.real_service.shape != (width, 100) or self.sham_service.shape != (width, 100):
            raise RealShamFlowError("REAL/SHAM service window differs")
        if self.real_energy_delta.shape != (width,) or self.sham_energy_delta.shape != (width,):
            raise RealShamFlowError("REAL/SHAM energy window differs")
        if self.real_hard_events.shape != (width, 100, 7) or self.sham_hard_events.shape != (width, 100, 7):
            raise RealShamFlowError("REAL/SHAM hard-event window differs")


def _fork_policy_state(parent: RecurrentRolloutState, lanes: np.ndarray, owner: np.ndarray, *, real: bool) -> RecurrentRolloutState:
    hidden = parent.hidden[lanes].clone()
    if real:
        for local, current_owner in enumerate(owner):
            old_owner = int(current_owner); standby = 1 - old_owner
            old_i, old_s = 2 * old_owner, 2 * old_owner + 1
            new_i, new_s = 2 * standby, 2 * standby + 1
            hidden[local, new_i] = hidden[local, new_s]
            hidden[local, old_s] = hidden[local, old_i]
    return RecurrentRolloutState(
        arm="STRUCTURED", hidden=hidden,
        actor_welford=parent.actor_welford, snapshot_welford=parent.snapshot_welford,
        critic_welford=parent.critic_welford,
        lane_episode_wave=parent.lane_episode_wave[lanes].copy(),
        lane_episode_tick=parent.lane_episode_tick[lanes].copy(),
        updates_completed=parent.updates_completed,
    )


class FirstApplicationValidRealShamRunner:
    """Detect once, clone before application, then run exactly 100 paired ticks."""

    def __init__(self, *, checkpoint_bytes: bytes, sampler: AddressedPolicySampler) -> None:
        if not bytes(checkpoint_bytes):
            raise RealShamFlowError("STRUCTURED sole checkpoint is required")
        self.checkpoint_bytes = bytes(checkpoint_bytes); self.sampler = sampler

    def detect(self, native: NativeBatch, step_rows: np.ndarray, already_forked: np.ndarray) -> np.ndarray:
        valid = native.first_application_valid(step_rows)
        prior = np.asarray(already_forked, dtype=bool)
        if valid.shape != prior.shape:
            raise RealShamFlowError("fork detector state differs")
        return valid & ~prior

    def run(
        self, *, native: NativeBatch, step_rows: np.ndarray,
        observation: Mapping[str, np.ndarray], policy_state: RecurrentRolloutState,
        already_forked: np.ndarray, origin_tick: int,
    ) -> ForkTelemetry | None:
        selected_mask = self.detect(native, step_rows, already_forked)
        if not bool(np.any(selected_mask)):
            return None
        lanes = np.flatnonzero(selected_mask)
        selected = native.select(selected_mask)
        real_native, sham_native, binding = selected.clone_real_sham_batches()
        owner = np.asarray(observation["owner"], dtype=np.int64)[lanes]
        real_state = _fork_policy_state(policy_state, lanes, owner, real=True)
        sham_state = _fork_policy_state(policy_state, lanes, owner, real=False)
        remapped = _RemappedSampler(self.sampler, lanes)
        real_policy = BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=self.checkpoint_bytes, state=real_state)
        sham_policy = BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=self.checkpoint_bytes, state=sham_state)
        real_observation = {name: np.asarray(value)[lanes].copy() for name, value in observation.items()}
        sham_observation = {name: np.asarray(value)[lanes].copy() for name, value in observation.items()}
        energy_origin = np.asarray(observation["total_energy"], dtype=np.float64)[lanes]
        hard_names = ("invalid_commit", "token_gap", "dual_owner", "dual_payload", "buffer_clear", "command_slew_breach", "separation_breach")
        hard_origin = {name: np.asarray(observation[name], dtype=np.int64)[lanes] for name in hard_names}
        captured: dict[str, list[np.ndarray]] = {f"{branch}_{name}": [] for branch in ("real", "sham") for name in (
            "service", "total_energy", "invalid_commit", "token_gap", "dual_owner",
            "dual_payload", "buffer_clear", "command_slew_breach", "separation_breach",
        )}
        for offset in range(FORK_TICKS):
            # Both branches share all future addressed physical rows.  Their
            # policy actions may diverge only through the frozen branch state.
            real_rows = real_policy.step_rows(real_observation, sampler=remapped, global_tick=origin_tick + offset, deterministic=True)
            sham_rows = sham_policy.step_rows(sham_observation, sampler=remapped, global_tick=origin_tick + offset, deterministic=True)
            real_observation = real_native.step(real_rows); sham_observation = sham_native.step(sham_rows)
            for branch, rows in (("real", real_observation), ("sham", sham_observation)):
                for name in ("service", "total_energy", "invalid_commit", "token_gap", "dual_owner", "dual_payload", "buffer_clear", "command_slew_breach", "separation_breach"):
                    captured[f"{branch}_{name}"].append(np.asarray(rows[name]).copy())
        stacked = {name: np.stack(values, axis=1) for name, values in captured.items()}
        result = ForkTelemetry(
            tuple(map(int, lanes)), origin_tick,
            stacked["real_service"].astype(np.int8), stacked["sham_service"].astype(np.int8),
            stacked["real_total_energy"][:, -1].astype(np.float64) - energy_origin,
            stacked["sham_total_energy"][:, -1].astype(np.float64) - energy_origin,
            np.stack([stacked[f"real_{name}"] > hard_origin[name][:, None] for name in hard_names], axis=2).astype(np.int8),
            np.stack([stacked[f"sham_{name}"] > hard_origin[name][:, None] for name in hard_names], axis=2).astype(np.int8),
            str(binding["transaction_telemetry_sha256"]),
        )
        result.validate(); return result


def flow_local_real_sham_self_audit() -> dict[str, object]:
    """Synthetic predicate-order audit only; no branch outcome is generated."""

    valid_flags = np.asarray([False, True, True, False, True], dtype=bool)
    already = np.asarray([False, False, True, False, False], dtype=bool)
    first = np.flatnonzero(valid_flags & ~already).tolist()
    source = inspect.getsource(FirstApplicationValidRealShamRunner)
    return {
        "schema": "DISH_RBHR_R06_E1_REAL_SHAM_FLOW_LOCAL_SELF_AUDIT_V1",
        "first_valid_only_fixture": first == [1, 4],
        "native_predicate_before_clone": source.index("self.detect") < source.index("clone_real_sham_batches"),
        "paired_window_ticks": FORK_TICKS,
        "real_and_sham_transaction_telemetry_required_identical": True,
        "future_physical_address_pairing": True,
        "fixture_only": True, "fork_activity": False, "partial_value": False,
        "question_relevant_output": False,
        "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
    }


__all__ = [
    "FirstApplicationValidRealShamRunner", "ForkTelemetry", "RealShamFlowError",
    "flow_local_real_sham_self_audit",
]
