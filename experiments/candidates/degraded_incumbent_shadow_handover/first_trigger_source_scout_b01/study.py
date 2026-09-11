"""One production learner seed and the frozen sixteen-row B01 fork panel."""

from __future__ import annotations

from io import BytesIO
import hashlib
import math
import time
from typing import Mapping

import numpy as np
import torch

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_backend import (
    B01PreparedBatch, NativeBatch,
    decode_promotion_source_receipt,
    native_batch_from_rows,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_evaluator import (
    prepare_b01_application,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_population import (
    EvaluationCoordinate,
    address,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_recurrent_trainer import (
    AddressedPolicySampler,
    BatchedRecurrentPolicy,
    MasterAddressedTrainResetFactory,
    NativePersistentTrainingFlow,
    RecurrentRolloutState,
    build_master_addressed_initial_state,
)


OBJECT = "DISH-FIRST-TRIGGER-SOURCE-SCOUT-B01"
BRANCHES = ("RETAIN", "TRANSFER_COPY", "TRANSFER_SHADOW")
HARD_EVENTS = (
    "invalid_commit", "token_gap", "dual_owner", "dual_payload", "buffer_clear",
    "command_slew_breach", "separation_breach",
)


class _DeterministicSampler:
    def normal(self, *, lane: int, tick: int, field: str) -> float:
        return 0.0

    def bernoulli(self, *, lane: int, tick: int, field: str, probability: float) -> int:
        return int(probability >= 0.5)


def seed_master(seed: int) -> bytes:
    if seed not in (11, 29, 47):
        raise ValueError("B01 seed differs")
    return hashlib.sha256(f"{OBJECT}/seed/{seed}".encode("ascii")).digest()


def panel() -> tuple[EvaluationCoordinate, ...]:
    return tuple(
        EvaluationCoordinate(0, package, schedule, f"SPEED_{speed}", slot)
        for package in ("TARGET_VISUAL_MASK", "TERRAIN_RELAY_MASK")
        for schedule in ("K8", "K4_TO_K12")
        for speed in (4, 8)
        for slot in (0, 3)
    )


def _reset_row(master: bytes, coordinate: EvaluationCoordinate) -> Mapping[str, object]:
    phase_address = address(
        purpose="K_SCHEDULE", block=0, split=coordinate.split,
        regime=coordinate.regime, schedule=coordinate.schedule,
        evaluation_slot=None, field="PHASE_OFFSET", draw_index=0,
    )
    digest = hashlib.sha256(master + b"\0" + phase_address.encode("ascii")).digest()
    uniform = ((int.from_bytes(digest[:8], "big") >> 11) + 0.5) / 2**53
    fixture_key = int.from_bytes(hashlib.sha256(
        master + b"\0" + coordinate.canonical_key().encode("ascii")
    ).digest()[:8], "big")
    return {
        "fixture_key": fixture_key, "master": master.hex(), "test_mode": 0,
        "package": ("TARGET_VISUAL_MASK", "TERRAIN_RELAY_MASK").index(coordinate.regime),
        "reflection": coordinate.reflection, "initial_owner": coordinate.initial_owner,
        "qa_owner": coordinate.qa_owner, "k_initial": coordinate.k_pair[0],
        "k_new": coordinate.k_pair[1], "switch_tick": coordinate.switch_tick,
        "tau_d_tick": coordinate.tau_d_tick,
        "phase": coordinate.phase(int(coordinate.k_pair[0] * uniform)),
        "route_speed": coordinate.route_speed,
        "turn_magnitude_deg": coordinate.turn_magnitude_deg, "turn_sign": coordinate.turn_sign,
        "initial_ux": coordinate.initial_ux, "initial_uy": coordinate.initial_uy,
        "block": 0, "split": 1,
        "schedule": ("K4", "K8", "K12", "K4_TO_K12", "K12_TO_K4").index(coordinate.schedule),
        "evaluation_slot": coordinate.evaluation_slot, "lane": -1, "cycle": -1,
        "arm_substream": 0, "degradation_flag": 0, "mask_enabled": 1,
        "fork_branch": 0, "episode": -1,
    }


def _parameter_exposure(
    initial: bytes, final: bytes, optimizer_steps: int,
) -> Mapping[str, float | int]:
    first = torch.load(BytesIO(initial), map_location="cpu", weights_only=False)["model"]
    last = torch.load(BytesIO(final), map_location="cpu", weights_only=False)["model"]
    initial_norm_sq = 0.0; final_norm_sq = 0.0; displacement_sq = 0.0; maximum = 0.0
    for name in first:
        before = first[name].to(torch.float64); after = last[name].to(torch.float64)
        before_norm = float(torch.linalg.vector_norm(before))
        displacement = float(torch.linalg.vector_norm(after - before))
        initial_norm_sq += before_norm * before_norm
        final_norm_sq += float(torch.sum(after * after))
        displacement_sq += displacement * displacement
        maximum = max(maximum, displacement / max(before_norm, 1e-300))
    initial_norm = math.sqrt(initial_norm_sq); final_norm = math.sqrt(final_norm_sq)
    return {
        "relative_l2_displacement": math.sqrt(displacement_sq) / initial_norm,
        "maximum_per_tensor_displacement_ratio": maximum,
        "initial_norm": initial_norm, "final_norm": final_norm,
        "optimizer_steps": optimizer_steps,
    }


def _check_deadline(deadline: float, boundary: str) -> None:
    if time.perf_counter() >= deadline:
        raise RuntimeError(f"incomplete: 1800s deadline reached at {boundary}")


def _branch_metrics(
    *, native: NativeBatch, observation: Mapping[str, np.ndarray], hidden: np.ndarray,
    prepared: B01PreparedBatch, checkpoint: bytes, sampler: AddressedPolicySampler,
    start_tick: int, deadline: float,
) -> Mapping[str, object]:
    state = RecurrentRolloutState.fresh("STRUCTURED", width=1)
    state.hidden = torch.from_numpy(hidden.astype(np.float32, copy=True))
    policy = BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=checkpoint, state=state)
    services: list[int] = []; energy_start = float(observation["total_energy"][0])
    hard = {name: 0 for name in HARD_EVENTS}
    previous_hard = {name: int(observation[name][0]) for name in HARD_EVENTS}
    for offset in range(100):
        _check_deadline(deadline, "branch-tick")
        if offset == 0:
            current = observation
        else:
            prepared, current, _ = prepare_b01_application(native=native, policy=policy)
        rows = policy.step_rows(
            current, sampler=sampler, global_tick=start_tick + offset,
            deterministic=True, recurrent_prepared=True,
        )
        owner_before = np.asarray(current["owner"], dtype=np.int64)
        after = native.complete_b01_tick(prepared, rows)
        policy.apply_native_promotion(owner_before=owner_before, step_rows=rows, observation_after=after)
        services.append(int(after["service"][0]))
        for name in HARD_EVENTS:
            current = int(after[name][0]); hard[name] += int(current > previous_hard[name])
            previous_hard[name] = current
    windows = [sum(services[index:index + 20]) for index in range(81)]
    delay = next((index + 1 for index in range(9, 100) if all(services[index - 9:index + 1])), 100)
    return {
        "recovery_return_100": sum(services), "worst_20_tick_service": min(windows),
        "recovery_delay_10": delay,
        "energy_change": float(after["total_energy"][0]) - energy_start,
        "hard_event_ticks": hard,
    }


def _evaluate_row(
    *, master: bytes, coordinate: EvaluationCoordinate, checkpoint: bytes,
    deadline: float,
) -> Mapping[str, object]:
    native = native_batch_from_rows((_reset_row(master, coordinate),))
    state = RecurrentRolloutState.fresh("STRUCTURED", width=1)
    policy = BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=checkpoint, state=state)
    sampler = _DeterministicSampler()
    for tick in range(1_200):
        _check_deadline(deadline, "panel-prefix")
        prepared, observation, hidden = prepare_b01_application(native=native, policy=policy)
        if bool(prepared.origin_valid[0]):
            if 1_200 - int(observation["tick"][0]) < 100:
                raise RuntimeError("incomplete: fewer than 100 native ticks remain after trigger")
            branches, branch_observations, metadata = native.clone_b01_prepared_batches(prepared, hidden)
            values = {
                name: _branch_metrics(
                    native=branches[name], observation=branch_observations[name],
                    hidden=metadata["branch_hidden"][name],
                    prepared=metadata["branch_prepared"][name], checkpoint=checkpoint,
                    sampler=sampler, start_tick=tick, deadline=deadline,
                )
                for name in BRANCHES
            }
            return {
                "coordinate": coordinate.canonical_key(), "package": coordinate.regime,
                "schedule": coordinate.schedule, "speed": coordinate.route_speed,
                "slot": coordinate.within_speed_slot, "triggered": True,
                "first_trigger_tick": tick,
                "owner_before": int(observation["owner"][0]),
                "owner_after": {
                    name: int(branch_observations[name]["owner"][0]) for name in BRANCHES
                },
                "receipts": {
                    name: decode_promotion_source_receipt(metadata["raw_receipts"][name][0])
                    for name in BRANCHES
                },
                "branches": values,
            }
        rows = policy.step_rows(
            observation, sampler=sampler, global_tick=tick,
            deterministic=True, recurrent_prepared=True,
        )
        owner_before = np.asarray(observation["owner"], dtype=np.int64)
        after = native.complete_b01_tick(prepared, rows)
        policy.apply_native_promotion(owner_before=owner_before, step_rows=rows, observation_after=after)
    return {
        "coordinate": coordinate.canonical_key(), "package": coordinate.regime,
        "schedule": coordinate.schedule, "speed": coordinate.route_speed,
        "slot": coordinate.within_speed_slot, "triggered": False,
    }


def _seed_estimands(rows: list[Mapping[str, object]]) -> Mapping[str, object]:
    triggered = [row for row in rows if bool(row["triggered"])]
    packages = {str(row["package"]) for row in triggered}
    if not triggered:
        return {
            "usable_trigger_support": False, "shadow_nonharm": True,
            "delta_shadow": 0.0, "delta_shadow_worst20": 0.0, "delta_copy": 0.0,
        }
    def mean_difference(left: str, right: str, metric: str) -> float:
        return float(np.mean([
            float(row["branches"][left][metric]) - float(row["branches"][right][metric])
            for row in triggered
        ]))
    shadow_hard = sum(sum(row["branches"]["TRANSFER_SHADOW"]["hard_event_ticks"].values()) for row in triggered)
    copy_hard = sum(sum(row["branches"]["TRANSFER_COPY"]["hard_event_ticks"].values()) for row in triggered)
    shadow_energy = np.mean([row["branches"]["TRANSFER_SHADOW"]["energy_change"] for row in triggered])
    copy_energy = np.mean([row["branches"]["TRANSFER_COPY"]["energy_change"] for row in triggered])
    return {
        "usable_trigger_support": len(triggered) >= 4 and len(packages) == 2,
        "shadow_nonharm": bool(shadow_hard <= copy_hard and shadow_energy <= 1.05 * copy_energy),
        "delta_shadow": mean_difference("TRANSFER_SHADOW", "TRANSFER_COPY", "recovery_return_100"),
        "delta_shadow_worst20": mean_difference("TRANSFER_SHADOW", "TRANSFER_COPY", "worst_20_tick_service"),
        "delta_shadow_delay": mean_difference("TRANSFER_SHADOW", "TRANSFER_COPY", "recovery_delay_10"),
        "delta_copy": mean_difference("TRANSFER_COPY", "RETAIN", "recovery_return_100"),
    }


def run_seed(seed: int, *, launch_sha: str) -> tuple[Mapping[str, object], bytes]:
    torch.set_num_threads(1); started = time.perf_counter(); deadline = started + 1_800.0
    master = seed_master(seed)
    initial_checkpoint = build_master_addressed_initial_state(master=master, block=0, arm="STRUCTURED")
    state = RecurrentRolloutState.fresh("STRUCTURED")
    factory = MasterAddressedTrainResetFactory(master=master, block=0, arm="STRUCTURED")
    native = native_batch_from_rows(factory.rows(state.lane_episode_wave))
    flow = NativePersistentTrainingFlow(
        native=native, arm="STRUCTURED", master=master, block=0,
        checkpoint_bytes=initial_checkpoint, state=state,
    )
    optimizer_steps = 0
    for _ in range(64):
        _check_deadline(deadline, "update-start")
        fragments = flow.collect_update(native.observe())
        update = flow.apply_update(fragments)
        if int(update["optimizer_steps"]) != 32:
            raise RuntimeError("incomplete: optimizer-step count differs")
        optimizer_steps += int(update["optimizer_steps"])
        if not bool(update["losses_finite"]) or not bool(update["gradient_norms_finite"]):
            raise RuntimeError("nonfinite learner state")
        retained = torch.load(
            BytesIO(flow.trainer.checkpoint_bytes), map_location="cpu", weights_only=False,
        )
        learner_tensors = list(retained["model"].values())
        for optimizer_state in retained["optimizer"]["state"].values():
            learner_tensors.extend(
                value for value in optimizer_state.values()
                if isinstance(value, torch.Tensor)
            )
        if any(not bool(torch.isfinite(value).all()) for value in learner_tensors):
            raise RuntimeError("nonfinite learner state")
        _check_deadline(deadline, "update-complete")
    checkpoint = bytes(flow.trainer.checkpoint_bytes)
    rows = []
    for coordinate in panel():
        _check_deadline(deadline, "panel-row")
        rows.append(_evaluate_row(
            master=master, coordinate=coordinate, checkpoint=checkpoint, deadline=deadline,
        ))
    estimands = _seed_estimands(rows)
    _check_deadline(deadline, "estimands-complete")
    exposure = _parameter_exposure(initial_checkpoint, checkpoint, optimizer_steps)
    if optimizer_steps != 2_048 or not all(
        math.isfinite(float(exposure[name]))
        for name in (
            "relative_l2_displacement", "maximum_per_tensor_displacement_ratio",
            "initial_norm", "final_norm",
        )
    ) or float(exposure["relative_l2_displacement"]) <= 0.0:
        raise RuntimeError("incomplete: learner exposure differs")
    _check_deadline(deadline, "exposure-complete")
    summary = {
        "seed": seed, "launch_sha": launch_sha,
        "training_transitions": 262_144, "learner_updates": 64,
        "optimizer_steps": optimizer_steps, "evaluation_prefix_ticks": sum(
            int(row.get("first_trigger_tick", 1_200)) for row in rows
        ),
        "branch_consequence_ticks": 300 * sum(bool(row["triggered"]) for row in rows),
        "trigger_count": sum(bool(row["triggered"]) for row in rows),
        "panel_rows": rows, "estimands": estimands,
        "exposure": exposure,
    }
    completed = time.perf_counter()
    if completed >= deadline:
        raise RuntimeError("incomplete: 1800s deadline reached at publication-boundary")
    summary["wall_seconds"] = completed - started
    return summary, checkpoint


__all__ = ["BRANCHES", "OBJECT", "panel", "run_seed", "seed_master"]
