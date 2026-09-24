"""Fixed B08 configuration, initialization identity, and F-only evaluation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch

from hmasd.agent import HMASDAgent
from ..b01.native import NativeSpec, _rng_state, active_config, make_config, seed_everything
from ..b04.evaluation import TRACE_FIELDS
from ..b06.feedback import PRODUCTION_LAYOUT
from ..b06.native import _normalizer_snapshot
from ..b07.native import evaluate_panel
from .metrics import aggregate_opportunity_summaries, recovery_opportunity_summary


OBJECT_ID = "UAV-SERVICE-FEEDBACK-TRAINING-B08"
TRAINING_SEED = 915031
DEVELOPMENT_SEEDS = tuple(range(941001, 941009))
FINAL_SEEDS = tuple(range(942001, 942033))
ARMS = ("N", "A")
TRAINING_FEEDBACK = {"N": False, "A": True}
EVALUATION_MODE = "F"


class OrdinaryBoundaryRepairRequired(RuntimeError):
    """The fixed batch cannot start until the ordinary learner boundary is resolved."""


@dataclass(frozen=True)
class B08Spec(NativeSpec):
    seed: int = TRAINING_SEED
    lanes: int = 2
    rollouts: int = 30
    rollout_length: int = 3000
    episode_length: int = 3000
    eval_seeds: tuple[int, ...] = DEVELOPMENT_SEEDS
    final_seeds: tuple[int, ...] = FINAL_SEEDS
    eval_rollouts: tuple[int, ...] = ()
    fact_seeds: tuple[int, ...] = ()


def production_spec(seed: int) -> B08Spec:
    if int(seed) != TRAINING_SEED:
        raise ValueError("unplanned B08 training seed")
    return B08Spec()


def make_b08_config(spec: B08Spec):
    config = make_config(spec)
    expected = {
        "seed": TRAINING_SEED,
        "num_envs": 2,
        "rollout_length": 3000,
        "episode_length": 3000,
        "max_steps": 3000,
        "total_timesteps": 180000,
        "n_agents": 8,
        "k": 10,
    }
    mismatches = {
        key: {"expected": value, "actual": getattr(config, key, None)}
        for key, value in expected.items()
        if getattr(config, key, None) != value
    }
    if mismatches:
        raise ValueError(f"B08 fixed native configuration mismatch: {mismatches}")
    if config.lambda_return != 2.0 or config.lambda_e != 1.0:
        raise ValueError("B08 native reward coefficients changed")
    if config.use_obsnorm or config.use_statenorm:
        raise ValueError("B08 expected the unchanged disabled observation/state normalizers")
    return config


def fixed_config_record(spec: B08Spec, config) -> dict[str, Any]:
    """Compact, explicit record of the matched N/A training rights."""

    return {
        "object_id": OBJECT_ID,
        "spec": asdict(spec),
        "active": json.loads(json.dumps(active_config(config)), parse_constant=str),
        "arm_order": list(ARMS),
        "training_action_paths": {
            "N": "native actor proposal -> original adapter/environment",
            "A": "native actor proposal -> unchanged B06 feedback -> original adapter/environment",
        },
        "evaluation_action_path": "unchanged B06 feedback for common initial and both endpoints",
        "training_feedback": TRAINING_FEEDBACK,
        "training_return_coefficient": 2.0,
        "extra_training_cost_coefficient": 0.0,
        "training_transitions_per_arm": spec.transitions,
        "joint_update_phases_per_arm": spec.rollouts,
        "transitions_per_phase": spec.lanes * spec.rollout_length,
        "lane_initial_seeds": [spec.seed + lane for lane in range(spec.lanes)],
        "development_seeds": list(spec.eval_seeds),
        "final_seeds": list(spec.final_seeds),
        "common_initial_evaluation_episodes": len(spec.eval_seeds) + len(spec.final_seeds),
        "feedback_layout": asdict(PRODUCTION_LAYOUT),
    }


def _hash_value(digest: "hashlib._Hash", name: str, value: Any) -> None:
    digest.update(name.encode("utf-8"))
    if torch.is_tensor(value):
        array = value.detach().cpu().contiguous().numpy()
        digest.update(b"tensor")
        digest.update(str(array.dtype).encode("ascii"))
        digest.update(np.asarray(array.shape, dtype=np.int64).tobytes())
        digest.update(array.tobytes())
        return
    if isinstance(value, np.ndarray):
        array = np.ascontiguousarray(value)
        digest.update(b"array")
        digest.update(str(array.dtype).encode("ascii"))
        digest.update(np.asarray(array.shape, dtype=np.int64).tobytes())
        digest.update(array.tobytes())
        return
    digest.update(json.dumps(value, sort_keys=True, default=str).encode("utf-8"))


def initialization_identity(agent: HMASDAgent) -> dict[str, Any]:
    """Hash parameters, registered buffers, normalizers, and evaluation mode state."""

    modules = {
        "skill_coordinator": agent.skill_coordinator,
        "skill_discoverer": agent.skill_discoverer,
        "team_discriminator": agent.team_discriminator,
        "individual_discriminator": agent.individual_discriminator,
    }
    component_digests: dict[str, str] = {}
    aggregate = hashlib.sha256()
    for module_name, module in sorted(modules.items()):
        digest = hashlib.sha256()
        digest.update(str(bool(module.training)).encode("ascii"))
        for key, value in sorted(module.state_dict().items()):
            _hash_value(digest, key, value)
        component_digests[module_name] = digest.hexdigest()
        aggregate.update(module_name.encode("utf-8"))
        aggregate.update(digest.digest())
    normalizers = _normalizer_snapshot(agent)
    normalizer_digest = hashlib.sha256()
    for name, state in sorted(normalizers.items()):
        if state is None:
            _hash_value(normalizer_digest, name, None)
        else:
            for field, value in sorted(state.items()):
                _hash_value(normalizer_digest, f"{name}.{field}", value)
    component_digests["normalizers"] = normalizer_digest.hexdigest()
    aggregate.update(b"normalizers")
    aggregate.update(normalizer_digest.digest())
    sampler_state = (
        agent.rollout_buffer.get_sampler_rng_state()
        if hasattr(agent, "rollout_buffer")
        else None
    )
    evaluation_state = {
        "agent_training": bool(agent.training),
        "module_training": {
            name: bool(module.training) for name, module in sorted(modules.items())
        },
        "torch_default_dtype": str(torch.get_default_dtype()),
        "rollout_sampler_state": sampler_state,
    }
    evaluation_digest = hashlib.sha256(
        json.dumps(evaluation_state, sort_keys=True).encode("utf-8")
    ).hexdigest()
    component_digests["evaluation_state"] = evaluation_digest
    aggregate.update(b"evaluation_state")
    aggregate.update(bytes.fromhex(evaluation_digest))
    rng = _rng_state()
    rng_digest = hashlib.sha256()
    _hash_value(rng_digest, "python", rng["python"])
    numpy_state = rng["numpy"]
    _hash_value(rng_digest, "numpy.algorithm", numpy_state[0])
    _hash_value(rng_digest, "numpy.state", numpy_state[1])
    _hash_value(rng_digest, "numpy.position", numpy_state[2])
    _hash_value(rng_digest, "numpy.has_gaussian", numpy_state[3])
    _hash_value(rng_digest, "numpy.cached_gaussian", numpy_state[4])
    _hash_value(rng_digest, "torch", rng["torch"])
    for index, cuda_state in enumerate(rng["cuda"] or ()):
        _hash_value(rng_digest, f"cuda.{index}", cuda_state)
    component_digests["rng_state"] = rng_digest.hexdigest()
    aggregate.update(b"rng_state")
    aggregate.update(rng_digest.digest())
    return {
        "sha256": aggregate.hexdigest(),
        "components": component_digests,
        "evaluation_state": evaluation_state,
    }


def new_initialized_agent(
    config,
    *,
    device: torch.device,
    log_dir: Path,
    seed: int = TRAINING_SEED,
) -> tuple[HMASDAgent, dict[str, Any]]:
    seed_everything(int(seed), device)
    agent = HMASDAgent(config, log_dir=str(log_dir), device=device)
    return agent, initialization_identity(agent)


def assert_common_initialization(
    left: dict[str, Any], right: dict[str, Any]
) -> None:
    if left != right:
        differences = {
            key: {"first": left.get(key), "second": right.get(key)}
            for key in set(left) | set(right)
            if left.get(key) != right.get(key)
        }
        raise RuntimeError(f"B08 arm initialization identity mismatch: {differences}")


def _episode_diagnostics(arrays: dict[str, np.ndarray], episode_index: int):
    prefix = f"episode_{episode_index}_"
    keys = (
        "mode_before",
        "mode",
        "entry",
        "exit",
        "charger_input_wh",
        "signed_stored_energy_delta_wh",
    )
    return {key: arrays[prefix + key] for key in keys}


def evaluate_feedback_panel(
    agent: HMASDAgent,
    config,
    seeds: Iterable[int],
    device: torch.device,
    *,
    trace_path: Path,
    log_dir: Path,
    policy_seed: int = TRAINING_SEED,
    progress=None,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    """Run one deterministic F panel and add the fixed opportunity description."""

    seeds = tuple(int(seed) for seed in seeds)
    if not seeds:
        raise ValueError("B08 evaluation panel is empty")
    before = initialization_identity(agent)
    result, arrays = evaluate_panel(
        agent,
        config,
        seeds,
        device,
        policy_seed=int(policy_seed),
        mode=EVALUATION_MODE,
        log_dir=Path(log_dir),
        trace_path=Path(trace_path),
        progress=progress,
    )
    after = initialization_identity(agent)
    if before != after:
        raise RuntimeError("B08 evaluation mutated the training agent state")
    time_step_seconds = float(config.time_step)
    opportunities = []
    if len(result["worlds"]) != len(seeds):
        raise RuntimeError("B08 evaluation world count mismatch")
    for index, world in enumerate(result["worlds"]):
        if int(world["seed"]) != seeds[index]:
            raise RuntimeError("B08 evaluation world ordering mismatch")
        metrics = arrays[f"episode_{index}_metrics"]
        throughput_sum = float(
            metrics[
                :, TRACE_FIELDS.index("delivered_end_to_end_throughput_mbps")
            ].sum()
        )
        world["actual_delivered_megabits"] = throughput_sum * time_step_seconds
        world["actual_delivered_megabytes"] = (
            world["actual_delivered_megabits"] / 8.0
        )
        opportunity = recovery_opportunity_summary(
            _episode_diagnostics(arrays, index),
            metrics,
            time_step_seconds=time_step_seconds,
        )
        world["recovery_opportunity"] = opportunity
        opportunities.append(opportunity)
    for field in ("actual_delivered_megabits", "actual_delivered_megabytes"):
        values = np.asarray(
            [world[field] for world in result["worlds"]], dtype=np.float64
        )
        result["aggregate"].update(
            {
                f"mean_{field}": float(values.mean()),
                f"median_{field}": float(np.median(values)),
                f"min_{field}": float(values.min()),
                f"max_{field}": float(values.max()),
                f"total_{field}": float(values.sum()),
            }
        )
    result.update(
        evaluation_mode=EVALUATION_MODE,
        policy_seed=int(policy_seed),
        learner_state_sha256_before_after=before["sha256"],
        full_state_immutable=True,
        recovery_opportunity_aggregate=aggregate_opportunity_summaries(opportunities),
    )
    return result, arrays


ENDPOINT_FIELDS = (
    "raw_native_J",
    "native_J_per_actual_step",
    "actual_length",
    "cumulative_qos",
    "qos_per_actual_step",
    "planned_window_qos",
    "cumulative_throughput_mbps",
    "throughput_mbps_per_actual_step",
    "planned_window_throughput_mbps",
    "actual_delivered_megabits",
    "actual_delivered_megabytes",
    "return_constraint_cost_sum",
    "return_constraint_cost_raw_sum",
    "episode_minimum_battery_ratio",
    "episode_minimum_return_margin",
    "maximum_service_free_interval_steps",
    "total_consumed_wh",
    "total_charger_input_wh",
    "total_signed_stored_energy_delta_wh",
)


def _world_effects(new: dict[str, Any], old: dict[str, Any]) -> dict[str, float]:
    return {field: float(new[field] - old[field]) for field in ENDPOINT_FIELDS}


def endpoint_comparison(
    initial: dict[str, Any],
    n_final: dict[str, Any],
    a_final: dict[str, Any],
) -> dict[str, Any]:
    """World-aligned A-N and each-arm-minus-common-initial endpoint effects."""

    panels = {"initial": initial, "N": n_final, "A": a_final}
    world_lists = {name: panel["worlds"] for name, panel in panels.items()}
    seed_lists = {
        name: [int(row["seed"]) for row in rows]
        for name, rows in world_lists.items()
    }
    if not (seed_lists["initial"] == seed_lists["N"] == seed_lists["A"]):
        raise RuntimeError(f"B08 endpoint seeds are not aligned: {seed_lists}")
    rows = []
    for initial_row, n_row, a_row in zip(
        world_lists["initial"], world_lists["N"], world_lists["A"], strict=True
    ):
        rows.append(
            {
                "seed": int(initial_row["seed"]),
                "effects_A_minus_N": _world_effects(a_row, n_row),
                "effects_N_minus_initial": _world_effects(n_row, initial_row),
                "effects_A_minus_initial": _world_effects(a_row, initial_row),
                "initial_recovery_opportunity": initial_row["recovery_opportunity"],
                "N_recovery_opportunity": n_row["recovery_opportunity"],
                "A_recovery_opportunity": a_row["recovery_opportunity"],
            }
        )
    aggregate: dict[str, Any] = {}
    for comparison in (
        "effects_A_minus_N",
        "effects_N_minus_initial",
        "effects_A_minus_initial",
    ):
        aggregate[comparison] = {}
        for field in ENDPOINT_FIELDS:
            values = np.asarray([row[comparison][field] for row in rows], dtype=np.float64)
            aggregate[comparison][field] = {
                "mean": float(values.mean()),
                "median": float(np.median(values)),
                "min": float(values.min()),
                "max": float(values.max()),
            }
    return {"worlds": rows, "aggregate": aggregate}


def unresolved_boundary_evidence(agent: HMASDAgent, dones: np.ndarray) -> dict[str, Any]:
    """Expose the exact ordinary-path state that blocks safe mid-episode clearing."""

    live = [int(index) for index in np.flatnonzero(~np.asarray(dones, dtype=bool))]
    pending = {
        str(index): {
            "time_step": int(agent.env_pending_high_level[index]["time_step"]),
            "fields": sorted(agent.env_pending_high_level[index]),
            "timer": int(agent.env_timers.get(index, -1)),
            "accumulated_reward": float(agent.env_reward_sums.get(index, 0.0)),
        }
        for index in live
        if index in agent.env_pending_high_level
    }
    return {
        "live_lanes": live,
        "live_lanes_with_pending_high_level_sample": pending,
        # Even a just-completed skill in a live episode retains recurrent
        # history: ordinary clear_buffers erases its timer and the next step
        # reinitializes skills/GRUs. No-pending is therefore insufficient.
        "supported_safe_clear": not live,
    }


def run_native(**_kwargs):
    """Fail before scientific effects until the DM supplies the core boundary resolution."""

    raise OrdinaryBoundaryRepairRequired(
        "B08 ordinary HMASD training is blocked on the recorded mid-skill rollout-boundary "
        "contract; no scientific fit was started"
    )
