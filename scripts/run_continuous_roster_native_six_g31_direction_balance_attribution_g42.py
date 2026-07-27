"""Train, evaluate, and analyze the frozen G42 direction attribution."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import time
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_direction_balance_attribution_g42 as source,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_slow_critic_reduction_g41 as g41,
)
from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import runtime_capacity_continuous_roster_g32 as g32
from scripts import run_continuous_roster_native_six_coordinate_training_g39 as g39_runner
from scripts import run_continuous_roster_native_six_credit_reduction_g40 as g40_runner
from scripts import run_continuous_roster_reactive_reduction_g35 as g35_runner
from scripts import run_continuous_roster_six_coordinate_cs_g38 as g38_runner


SCHEMA_VERSION = 1
ALGORITHM_ID = source.ALGORITHM_ID
AUTHORIZATION_TOKEN = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_"
    "FORMAL_AUTHORIZATION_V1"
)
ALIGNMENT_AUDIT_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_"
    "CODE_SCIENCE_ALIGNMENT_AUDIT_SOURCE_6B"
)
ALIGNED_IMPLEMENTATION_COMMIT = "6b8ea82d8fdbc76c14a414ff2b042a126f945dfb"
ALIGNMENT_STAGE_COMMIT = "309858dca06af66f13857f94773bcef37527d821"
ACCEPTED_ANCHOR_ROOT_RELATIVE = Path(
    "logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_"
    "20260727_97a8b23_r1"
)

INVALID_BRANCH = (
    "INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42"
)
SOURCE_FAILURE_BRANCH = "SOURCE_OR_REFERENCE_ACCESS_FAILURE_G42"
NO_DB_SUFFICIENT_BRANCH = "SCALE_MATCHED_NO_DIRECTION_BALANCE_SUFFICIENT_G42"
DB_ADVANTAGE_BRANCH = "DIRECTION_BALANCE_FINITE_BUDGET_ADVANTAGE_G42"
UNDERPOWERED_BRANCH = "MIXED_UNDERPOWERED_DIRECTION_BALANCE_ATTRIBUTION_G42"
NONFORMAL_BRANCH = (
    "NONFORMAL_CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_"
    "ATTRIBUTION_G42_EXERCISE_COMPLETE"
)
NON_EXECUTABLE_BRANCH = "NON_EXECUTABLE_EVIDENCE_DESIGN"

FINAL_FIXED_DET = "FINAL_FIXED_DET"
FINAL_FIXED_STOCH = "FINAL_FIXED_STOCH"
FINAL_RANDOM_DET = "FINAL_RANDOM_DET"
FINAL_RANDOM_STOCH = "FINAL_RANDOM_STOCH"
MODEL_CELLS = (
    FINAL_FIXED_DET,
    FINAL_FIXED_STOCH,
    FINAL_RANDOM_DET,
    FINAL_RANDOM_STOCH,
)

UTILITY_FLOOR = 0.90
EVENT_FLOOR = 0.85
SEGMENT_FLOOR = 0.85
PROCESS_MARGIN = -0.05
STOCHASTIC_FLOOR = 0.80
MINIMUM_REPLICATE_FLOOR = 0.85
DIRECTION_MARGIN = 0.05
NONFORMAL_WALL_CLOCK_CAP_SECONDS = 1_200.0
FORMAL_WALL_CLOCK_CAP_SECONDS = 28_800.0

FORMAL_REPLICATES = 3
FORMAL_BRANCH_UPDATES = 100
FORMAL_NUM_ENVS = 8
FORMAL_PPO_PASSES = 2
FORMAL_EVAL_EPISODES = 48
FORMAL_BOOTSTRAP_REPETITIONS = 10_000

EXERCISE_REPLICATES = 1
EXERCISE_BRANCH_UPDATES = 10
EXERCISE_NUM_ENVS = 8
EXERCISE_PPO_PASSES = 2
EXERCISE_EVAL_EPISODES = 6
EXERCISE_BOOTSTRAP_REPETITIONS = 250

SEED_BASES = {
    "branch_ledger": 10_421_000,
    "branch_action": 10_422_000,
    "branch_gradient_probe": 10_423_000,
    "evaluation_base_ledger": 10_424_000,
    "evaluation_process": 10_425_000,
    "evaluation_action": 10_426_000,
}
BOOTSTRAP_SEED = 10_427_042
NONFORMAL_SEED_OFFSET = 900_000

configure_runtime = g39_runner.configure_runtime
_runtime_identity = g39_runner._runtime_identity
_write_json = g39_runner._write_json
_read_json = g39_runner._read_json
_artifact_digest = g39_runner._artifact_digest
_state_digest = g39_runner._state_digest


def _native_backend_identity() -> dict[str, object]:
    module = g40.toy_cpp.load_continuous_roster_toy_cpp_backend()
    return {
        "kind": "ContinuousRosterToyBatch_CPU_CPP",
        "required": True,
        "python_fallback": False,
        "module": str(module.__name__),
        "build_identity": g40.toy_cpp._build_identity(),
    }


def seed_block(replicate: int, *, formal: bool) -> dict[str, int]:
    if isinstance(replicate, bool) or not isinstance(replicate, int):
        raise TypeError("G42 replicate must be an integer")
    limit = FORMAL_REPLICATES if formal else EXERCISE_REPLICATES
    if not 0 <= replicate < limit:
        raise ValueError("G42 replicate outside registered execution support")
    offset = replicate + (0 if formal else NONFORMAL_SEED_OFFSET)
    return {name: base + offset for name, base in SEED_BASES.items()}


def bootstrap_seed(*, formal: bool) -> int:
    return BOOTSTRAP_SEED + (0 if formal else NONFORMAL_SEED_OFFSET)


def _counts(*, formal: bool) -> dict[str, int]:
    if formal:
        return {
            "replicates": FORMAL_REPLICATES,
            "branch_updates_per_arm": FORMAL_BRANCH_UPDATES,
            "num_envs": FORMAL_NUM_ENVS,
            "ppo_passes": FORMAL_PPO_PASSES,
            "evaluation_episodes_per_cell": FORMAL_EVAL_EPISODES,
            "bootstrap_resamples": FORMAL_BOOTSTRAP_REPETITIONS,
        }
    return {
        "replicates": EXERCISE_REPLICATES,
        "branch_updates_per_arm": EXERCISE_BRANCH_UPDATES,
        "num_envs": EXERCISE_NUM_ENVS,
        "ppo_passes": EXERCISE_PPO_PASSES,
        "evaluation_episodes_per_cell": EXERCISE_EVAL_EPISODES,
        "bootstrap_resamples": EXERCISE_BOOTSTRAP_REPETITIONS,
    }


def _configuration(*, formal: bool) -> dict[str, object]:
    counts = _counts(formal=formal)
    replicates = int(counts["replicates"])
    updates = int(counts["branch_updates_per_arm"])
    envs = int(counts["num_envs"])
    passes = int(counts["ppo_passes"])
    episodes = int(counts["evaluation_episodes_per_cell"])
    cells_per_replicate = len(source.ARMS) * len(g34.CAPACITIES) * len(MODEL_CELLS)
    training = replicates * len(source.ARMS) * updates * envs * g32.HORIZON
    evaluation = replicates * cells_per_replicate * episodes * g32.HORIZON
    return {
        **counts,
        "arms": list(source.ARMS),
        "accepted_anchor_replicates": (
            list(source.ACCEPTED_G40_ANCHOR_REPLICATES) if formal else [0]
        ),
        "common_anchor_training": "none_read_only_accepted_G40_anchors",
        "accepted_common_anchor_updates": g41.ACCEPTED_G40_COMPLETED_ANCHOR_UPDATES,
        "accepted_common_anchor_optimizer_steps": g41.ACCEPTED_G40_ANCHOR_OPTIMIZER_STEPS,
        "accepted_g40_source_commit": g41.ACCEPTED_G40_SOURCE_COMMIT,
        "accepted_g41_source_commit": source.ACCEPTED_G41_SOURCE_COMMIT,
        "aligned_g42_implementation_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "training_capacity": g32.TRAIN_CAPACITY,
        "evaluation_capacities": list(g34.CAPACITIES),
        "horizon": g32.HORIZON,
        "stored_training_observation_dim": 6,
        "actor_width": g40.g39.HIDDEN_DIM,
        "learning_rate": g40.LEARNING_RATE,
        "optimizer": "Adam(beta1=0.9,beta2=0.999,eps=1e-8,weight_decay=0)",
        "gradient_clipping": "none",
        "minibatches": "none",
        "actor_head_optimizer": "native_six_actor|log_std|shared_two_output_baseline",
        "standalone_slow_critic": "absent",
        "optimizer_steps_per_ppo_pass_per_arm": 1,
        "checkpoint_selection": "final_only",
        "episode_exclusions": "none",
        "cells_per_arm_capacity": len(MODEL_CELLS),
        "cells_per_replicate": cells_per_replicate,
        "total_cells": replicates * cells_per_replicate,
        "training_transitions": training,
        "evaluation_transitions": evaluation,
        "total_real_transitions": training + evaluation,
        "optimizer_steps": replicates * len(source.ARMS) * updates * passes,
        "evaluation_optimizer_steps": 0,
        "branch_update_order": list(source.ARMS),
        "paired_collection_before_update": True,
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "environment_python_fallback": False,
        "intrinsic_K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "per_episode_complexity": "O(H)",
    }


def source_controls() -> dict[str, object]:
    return {
        "source_id": source.SOURCE_ID,
        "parent_source_id": g41.SOURCE_ID,
        "accepted_g40_manifest": g41.ACCEPTED_G40_MANIFEST,
        "accepted_g40_source_commit": g41.ACCEPTED_G40_SOURCE_COMMIT,
        "accepted_common_anchor_updates": g41.ACCEPTED_G40_COMPLETED_ANCHOR_UPDATES,
        "accepted_common_anchor_optimizer_steps": g41.ACCEPTED_G40_ANCHOR_OPTIMIZER_STEPS,
        "accepted_g41_source_commit": source.ACCEPTED_G41_SOURCE_COMMIT,
        "aligned_g42_implementation_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "training_source": "G32 capacity-8 fixed paired source",
        "evaluation_source": "G34 fixed/random capacities 6|8|12",
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "environment_backend_python_fallback": False,
        "horizon": g32.HORIZON,
        "training_capacity": g32.TRAIN_CAPACITY,
        "evaluation_capacities": list(g34.CAPACITIES),
        "arms": list(source.ARMS),
        "seed_bases": dict(SEED_BASES),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "nonformal_seed_offset": NONFORMAL_SEED_OFFSET,
        "intrinsic_K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "per_episode_complexity": "O(H)",
    }


def _expected_anchor_root() -> Path:
    return (PROJECT_ROOT / ACCEPTED_ANCHOR_ROOT_RELATIVE).resolve()


def _bind_anchor_root(root: Path | None) -> Path:
    if root is None:
        raise ValueError("G42 execution requires the accepted G40 anchor root")
    resolved = Path(root).resolve()
    if resolved != _expected_anchor_root():
        raise ValueError("G42 accepted anchor root is not the immutable registered root")
    return resolved


def _validate_anchor_manifest(root: Path) -> dict[str, str]:
    manifest_path = root / "train_manifest.json"
    manifest = _read_json(manifest_path)
    configuration = manifest.get("configuration")
    rows = manifest.get("replicate_results")
    if (
        manifest.get("schema_version") != g41.ACCEPTED_G40_SCHEMA_VERSION
        or manifest.get("algorithm") != g40.ALGORITHM_ID
        or manifest.get("source_id") != g40.SOURCE_ID
        or manifest.get("source_commit") != g41.ACCEPTED_G40_SOURCE_COMMIT
        or manifest.get("formal") is not True
        or manifest.get("authorization_token") != g41.ACCEPTED_G40_AUTHORIZATION_TOKEN
        or manifest.get("status") != "COMPLETE"
        or not isinstance(configuration, Mapping)
        or any(configuration.get(name) != value for name, value in g41.ACCEPTED_G40_CONFIGURATION_FIELDS)
        or not isinstance(rows, list)
        or len(rows) != len(source.ACCEPTED_G40_ANCHOR_REPLICATES)
    ):
        raise ValueError("G42 accepted G40 authority manifest identity mismatch")
    checkpoint_digests: dict[str, str] = {}
    for replicate in source.ACCEPTED_G40_ANCHOR_REPLICATES:
        authority = g41.accepted_g40_anchor_authority(replicate)
        try:
            row = rows[replicate]
            anchor = row["common_anchor"]
            relative = Path(str(anchor["checkpoint"]))
            expected_name = Path(authority.checkpoint_reference).name
            if (
                row["replicate"] != replicate
                or anchor["state_digest"] != authority.complete_state_digest
                or anchor["optimizer_steps"] != g41.ACCEPTED_G40_ANCHOR_OPTIMIZER_STEPS
                or relative.name != expected_name
            ):
                raise ValueError("G42 accepted G40 anchor row mismatch")
            checkpoint_path = root / "checkpoints" / expected_name
            checkpoint_digests[str(replicate)] = _artifact_digest(checkpoint_path)
        except (KeyError, OSError, TypeError, ValueError) as error:
            raise ValueError(f"G42 accepted anchor {replicate} invalid: {error}") from error
    return {
        "manifest": _artifact_digest(manifest_path),
        **{f"checkpoint_{key}": value for key, value in checkpoint_digests.items()},
    }


def _load_accepted_anchor(root: Path, replicate: int) -> g40.G40NativeSixPolicy:
    authority = g41.accepted_g40_anchor_authority(replicate)
    path = root / "checkpoints" / Path(authority.checkpoint_reference).name
    payload = torch.load(path, map_location="cpu", weights_only=False)
    return g41.load_accepted_g40_anchor_checkpoint(
        payload, accepted_anchor_replicate=replicate
    )


def _balanced_assignments(
    categories: Sequence[object], *, replicate: int, capacity: int,
    process_seed: int, stream: int, count: int,
) -> tuple[object, ...]:
    if len(categories) != 3 or count not in (6, 48) or count % 3:
        raise ValueError("G42 evaluation balance requires 3 categories and 6 or 48 rows")
    order = sorted(
        range(count),
        key=lambda episode: (
            int(g40.g35._process_rng(process_seed, capacity, episode, stream).integers(0, 2**63)),
            episode,
        ),
    )
    assigned: list[object | None] = [None] * count
    width = count // 3
    for category_index, category in enumerate(categories):
        for episode in order[category_index * width : (category_index + 1) * width]:
            assigned[episode] = category
    if any(row is None for row in assigned):
        raise RuntimeError("G42 balanced assignment did not close")
    return tuple(assigned)  # type: ignore[return-value]


def _source_inventory(
    *, replicate: int, capacity: int, episode_count: int, formal: bool
) -> tuple[tuple[g34.RandomProcessLedger, ...], dict[str, object]]:
    if capacity not in g34.CAPACITIES or episode_count not in (6, 48):
        raise ValueError("G42 evaluation source request is outside frozen support")
    seeds = seed_block(replicate, formal=formal)
    times = g40.g35._time_assignments(
        capacity=capacity, process_seed=seeds["evaluation_process"]
    )[:episode_count]
    orders = _balanced_assignments(
        g34.EVENT_ORDERS,
        replicate=replicate,
        capacity=capacity,
        process_seed=seeds["evaluation_process"],
        stream=1,
        count=episode_count,
    )
    if capacity == 6:
        profiles: Sequence[object] = (g32.SMALL_CAPACITY_6,) * episode_count
    elif capacity == 12:
        profiles = (g32.LARGE_CAPACITY_12,) * episode_count
    else:
        profiles = _balanced_assignments(
            g32.TRAIN_PROFILES,
            replicate=replicate,
            capacity=capacity,
            process_seed=seeds["evaluation_process"],
            stream=2,
            count=episode_count,
        )
    processes: list[g34.RandomProcessLedger] = []
    for local_episode in range(episode_count):
        base = g32.make_ledger(
            g34.episode_address(capacity, local_episode),
            master_seed=seeds["evaluation_base_ledger"],
            profile=profiles[local_episode],  # type: ignore[arg-type]
        )
        expected, trajectory = g34._expected_roster_schedule(
            base, times[local_episode], orders[local_episode]  # type: ignore[arg-type]
        )
        row = g34.RandomProcessLedger(
            base=base,
            local_episode_id=local_episode,
            event_times=times[local_episode],
            event_order=orders[local_episode],  # type: ignore[arg-type]
            expected_roster_sizes=expected,
            count_trajectory=trajectory,
        )
        row.validate()
        processes.append(row)
    if len({row.signature for row in processes}) != episode_count:
        raise ValueError("G42 process signatures are not unique")
    inventory = {
        "replicate": replicate,
        "capacity": capacity,
        "seeds": seeds,
        "order_counts": {
            "LRJT": sum(tuple(row.event_order) == tuple(g34.EVENT_ORDERS[0]) for row in processes),
            "LJRT": sum(tuple(row.event_order) == tuple(g34.EVENT_ORDERS[1]) for row in processes),
            "JLRT": sum(tuple(row.event_order) == tuple(g34.EVENT_ORDERS[2]) for row in processes),
        },
        "profile_counts": {
            profile.name: sum(row.profile.name == profile.name for row in processes)
            for profile in g32.TRAIN_PROFILES
        } if capacity == 8 else None,
        "processes": [
            {
                "local_episode_id": row.local_episode_id,
                "episode_id": row.episode_id,
                "profile": row.profile.name,
                "event_times": list(row.event_times),
                "event_order": list(row.event_order),
                "count_trajectory": list(row.count_trajectory),
                "random_expected_roster_sizes": list(row.expected_roster_sizes),
                "fixed_expected_roster_sizes": list(row.base.expected_roster_sizes),
                "signature": repr(row.signature),
            }
            for row in processes
        ],
    }
    expected_per_category = episode_count // 3
    if set(inventory["order_counts"].values()) != {expected_per_category}:  # type: ignore[union-attr]
        raise RuntimeError("G42 event-order inventory is not exactly balanced")
    if capacity == 8 and set(inventory["profile_counts"].values()) != {expected_per_category}:  # type: ignore[union-attr]
        raise RuntimeError("G42 capacity-8 profile inventory is not exactly balanced")
    return tuple(processes), inventory


def _optimizer_step_values(
    optimizer: torch.optim.Optimizer,
    model: g41.G41NoSlowProjection,
) -> tuple[float, ...]:
    return tuple(
        source._optimizer_step_value(optimizer, parameter)
        for parameter in model.actor_credit_parameters()
    )


def _continuation_audit(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    *,
    update_index: int,
) -> dict[str, object]:
    if isinstance(update_index, bool) or not isinstance(update_index, int) or update_index < 0:
        raise ValueError("G42 update index must be a nonnegative integer")
    if update_index == 0:
        return source.branch_boundary_audit(models, optimizers)
    inventory_valid = tuple(models) == source.ARMS and tuple(optimizers) == source.ARMS
    expected_steps = float(update_index * source.PPO_PASSES)
    authorities = [
        model.accepted_g40_anchor_authority for model in models.values()
    ] if inventory_valid else []
    authority_valid = bool(
        authorities
        and all(
            authority == authorities[0]
            and authority == g41.accepted_g40_anchor_authority(authority.replicate)
            for authority in authorities
        )
    )
    no_slow = bool(inventory_valid and all(not hasattr(model, "slow_critic") for model in models.values()))
    phases_valid = bool(inventory_valid and all(model.phase == "credit_branch" for model in models.values()))
    optimizer_inventory = bool(
        inventory_valid
        and all(
            isinstance(optimizers[arm], torch.optim.Adam)
            and source._optimizer_owns_actor_head(optimizers[arm], models[arm])
            for arm in source.ARMS
        )
    )
    step_state_valid = bool(
        optimizer_inventory
        and all(
            values
            and all(value == expected_steps for value in values)
            for values in (
                _optimizer_step_values(optimizers[arm], models[arm])
                for arm in source.ARMS
            )
        )
    )
    optimizer_storage_separate = bool(
        inventory_valid
        and id(optimizers[source.DB_ARM].state)
        != id(optimizers[source.NO_DB_ARM].state)
    )
    passed = bool(
        inventory_valid
        and authority_valid
        and no_slow
        and phases_valid
        and optimizer_inventory
        and step_state_valid
        and optimizer_storage_separate
    )
    authority_identity = (
        g41.accepted_g40_anchor_identity(authorities[0].replicate)
        if authority_valid
        else None
    )
    return {
        "passed": passed,
        "continuation": True,
        "update_index": update_index,
        "inventory_valid": inventory_valid,
        "accepted_g41_source_commit": source.ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g40_anchor_authority": authority_identity,
        "authority_valid": authority_valid,
        "standalone_slow_absent": no_slow,
        "branch_phases_valid": phases_valid,
        "optimizer_parameter_order_equal": optimizer_inventory,
        "optimizer_expected_step_before": expected_steps,
        "optimizer_step_state_valid": step_state_valid,
        "optimizer_states_separate": optimizer_storage_separate,
    }


def _paired_source_audit(
    trajectories: Mapping[str, g40.AnchoredRosterTrajectory],
    *,
    update_index: int,
    ledger_seed: int,
    action_seed: int,
) -> dict[str, object]:
    if tuple(trajectories) != source.ARMS:
        return {"passed": False, "inventory_valid": False}
    left, right = (trajectories[arm] for arm in source.ARMS)
    def ledger_key(ledger: g32.CapacityRosterLedger) -> tuple[object, ...]:
        return (
            ledger.episode_id,
            ledger.profile,
            ledger.initial_keys,
            ledger.temporarily_absent,
            ledger.fresh_join,
            ledger.terminal_leave,
            ledger.capabilities.tobytes(),
            ledger.load.tobytes(),
            ledger.target_mix.tobytes(),
            ledger.presentation_priority.tobytes(),
            ledger.expected_roster_sizes,
        )

    ledgers_equal = tuple(ledger_key(ledger) for ledger in left.ledgers) == tuple(
        ledger_key(ledger) for ledger in right.ledgers
    )
    source_tensors_equal = all(
        torch.equal(getattr(left, name), getattr(right, name))
        for name in ("observations", "active_mask", "critic_states")
    )
    lifecycle_equal = tuple(outcome.roster_sizes for outcome in left.outcomes) == tuple(
        outcome.roster_sizes for outcome in right.outcomes
    )
    initial_exact = (
        g40.branch_trajectory_match(left, right)
        if update_index == 0
        else None
    )
    return {
        "passed": bool(
            ledgers_equal
            and source_tensors_equal
            and lifecycle_equal
            and (initial_exact is None or initial_exact["passed"] is True)
        ),
        "inventory_valid": True,
        "ledger_signatures_equal": ledgers_equal,
        "source_observation_mask_critic_tensors_equal": source_tensors_equal,
        "roster_lifecycle_equal": lifecycle_equal,
        "initial_complete_trajectory_equal": initial_exact,
        "ledger_seed": ledger_seed,
        "action_seed": action_seed,
        "member_owned_action_stream_seed_equal": True,
    }


def _collect_trajectory(
    model: g41.G41NoSlowProjection,
    *,
    episode_ids: Sequence[int],
    ledger_seed: int,
    action_seed: int,
) -> g40.AnchoredRosterTrajectory:
    """Collect the accepted no-slow policy through the required C++ toy batch."""

    ids = tuple(int(value) for value in episode_ids)
    profiles = tuple(g32.TRAIN_PROFILES)
    if len(ids) != 8 or model.member_capacity != g32.TRAIN_CAPACITY:
        raise ValueError("G42 branch collection requires exactly 8 capacity-8 episodes")
    ledgers = tuple(
        g32.make_ledger(
            episode,
            master_seed=int(ledger_seed),
            profile=profiles[episode % len(profiles)],
        )
        for episode in ids
    )
    envs = tuple(g32.RuntimeCapacityRosterEnv(row) for row in ledgers)
    env_batch = g40.toy_cpp.ContinuousRosterToyBatch(envs)
    noise = g32.make_action_noise(
        ids, action_seed=int(action_seed), member_capacity=g32.TRAIN_CAPACITY
    )
    hidden = torch.zeros((len(ids), g32.TRAIN_CAPACITY, model.hidden_dim))
    shapes = {
        "observations": (g32.HORIZON, len(ids), g32.TRAIN_CAPACITY, 6),
        "active_mask": (g32.HORIZON, len(ids), g32.TRAIN_CAPACITY),
        "critic_states": (g32.HORIZON, len(ids), g32.CRITIC_STATE_DIM),
        "actions": (g32.HORIZON, len(ids), g32.TRAIN_CAPACITY, g32.ACTION_DIM),
        "pre_tanh_actions": (g32.HORIZON, len(ids), g32.TRAIN_CAPACITY, g32.ACTION_DIM),
        "old_log_probs": (g32.HORIZON, len(ids), g32.TRAIN_CAPACITY),
        "old_values": (g32.HORIZON, len(ids)),
        "rewards": (g32.HORIZON, len(ids)),
        "hidden_before": (g32.HORIZON, len(ids), g32.TRAIN_CAPACITY, model.hidden_dim),
        "hidden_after": (g32.HORIZON, len(ids), g32.TRAIN_CAPACITY, model.hidden_dim),
        "prefix_action_sums": (g32.HORIZON, len(ids), g32.TRAIN_CAPACITY, g32.ACTION_DIM),
        "terminal_hidden_reset_mask": (g32.HORIZON, len(ids), g32.TRAIN_CAPACITY),
    }
    rows = {
        name: torch.empty(
            shape,
            dtype=(
                torch.bool
                if name in ("active_mask", "terminal_hidden_reset_mask")
                else torch.float32
            ),
        )
        for name, shape in shapes.items()
    }
    model.eval()
    with torch.no_grad():
        for step in range(g32.HORIZON):
            views = env_batch.observe_six()
            terminal_reset = torch.zeros(
                (len(ids), g32.TRAIN_CAPACITY), dtype=torch.bool
            )
            for batch_index, view in enumerate(views):
                if view.membership_change.terminally_left:
                    terminal_reset[
                        batch_index,
                        list(view.membership_change.terminally_left),
                    ] = True
            g32._delete_terminal_hidden(hidden, views)
            observations = torch.as_tensor(
                np.stack([row.observations for row in views])
            )
            active = torch.as_tensor(np.stack([row.active_mask for row in views]))
            critic = torch.as_tensor(np.stack([row.critic_state for row in views]))
            before = hidden.clone()
            output = g41.retained_actor_step(
                model,
                observations=observations,
                active_mask=active,
                critic_state=critic,
                hidden=hidden,
                sampling_noise=torch.as_tensor(noise[step]),
            )
            action_rows = np.ascontiguousarray(
                output.actions.detach().cpu().numpy(), dtype=np.float32
            )
            rewards = np.asarray(
                env_batch.advance(views, action_rows), dtype=np.float32
            )
            values = {
                "observations": observations,
                "active_mask": active,
                "critic_states": critic,
                "actions": output.actions,
                "pre_tanh_actions": output.pre_tanh_actions,
                "old_log_probs": output.token_log_probs,
                "old_values": torch.zeros(len(ids), dtype=torch.float32),
                "rewards": torch.as_tensor(rewards),
                "hidden_before": before,
                "hidden_after": output.next_hidden,
                "prefix_action_sums": output.prefix_action_sums,
                "terminal_hidden_reset_mask": terminal_reset,
            }
            for name, value in values.items():
                rows[name][step].copy_(value.detach().cpu())
            hidden = output.next_hidden
        immediate, successor = model.baseline_values(rows["critic_states"])
    return g40.AnchoredRosterTrajectory(
        **rows,
        old_immediate_baselines=immediate.detach().cpu(),
        old_successor_baselines=successor.detach().cpu(),
        outcomes=tuple(env.outcome() for env in envs),
        ledgers=ledgers,
    )


def _apply_matched_update(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, g40.AnchoredRosterTrajectory],
    *,
    update_index: int,
    ledger_seed: int,
    action_seed: int,
) -> dict[str, object]:
    """Repeat the accepted one-batch kernel with persistent arm-owned Adam state."""

    boundary = _continuation_audit(models, optimizers, update_index=update_index)
    if boundary.get("passed") is not True:
        raise ValueError("G42 branch/continuation gate failed before optimizer step")
    if tuple(trajectories) != source.ARMS or any(
        trajectory.rewards.numel() != source.MAX_CONFORMANCE_TRANSITIONS
        for trajectory in trajectories.values()
    ):
        raise ValueError("G42 update requires two paired 8x48 real trajectories")
    paired_source = _paired_source_audit(
        trajectories,
        update_index=update_index,
        ledger_seed=ledger_seed,
        action_seed=action_seed,
    )
    if paired_source["passed"] is not True:
        raise ValueError("G42 paired source/RNG gate failed before optimizer step")

    db_model = models[source.DB_ARM]
    no_db_model = models[source.NO_DB_ARM]
    db_optimizer = optimizers[source.DB_ARM]
    no_db_optimizer = optimizers[source.NO_DB_ARM]
    credits = {
        arm: g41.compute_g31_credit_without_slow(
            rewards=trajectory.rewards,
            immediate_baselines=trajectory.old_immediate_baselines,
            successor_baselines=trajectory.old_successor_baselines,
            terminals=g40.terminal_mask(trajectory),
        )
        for arm, trajectory in trajectories.items()
    }
    normalized = {
        arm: g41._normalized_g31_advantages(credit)
        for arm, credit in credits.items()
    }
    steps_before = {
        arm: _optimizer_step_values(optimizers[arm], models[arm])
        for arm in source.ARMS
    }
    rng_before = torch.random.get_rng_state().clone()
    pass_records: list[dict[str, object]] = []
    for pass_index in range(source.PPO_PASSES):
        db_trajectory = trajectories[source.DB_ARM]
        no_db_trajectory = trajectories[source.NO_DB_ARM]
        db_replay = g41.retained_replay(db_model, db_trajectory)
        no_db_replay = g41.retained_replay(no_db_model, no_db_trajectory)
        db_probe = source._channel_gradient_probe(
            db_model,
            db_replay,
            db_trajectory,
            credits[source.DB_ARM],
            normalized[source.DB_ARM],
        )
        _, db_preview_gradients = g40._actor_objective_gradients(
            g40.G31_ARM,
            db_model,
            db_replay,
            db_trajectory,
            normalized[source.DB_ARM],
        )
        registered_norm = g40._norm_rows(db_preview_gradients)
        no_db_plan = source._prepare_raw_sum_pass(
            no_db_model,
            no_db_replay,
            no_db_trajectory,
            credits[source.NO_DB_ARM],
            normalized[source.NO_DB_ARM],
            registered_gradient_norm=registered_norm,
        )
        direction_comparison = source.direction_unit_distance_record(
            db_preview_gradients,
            no_db_plan.composition.raw_sum_gradients,
            registered_gradient_norm=registered_norm,
        )
        db_metrics = g41._retained_actor_head_pass(
            db_model,
            db_optimizer,
            db_replay,
            db_trajectory,
            credits[source.DB_ARM],
            normalized[source.DB_ARM],
        )
        no_db_metrics = source._apply_raw_sum_pass(
            no_db_model, no_db_optimizer, no_db_plan
        )
        pass_records.append(
            {
                "pass_index": pass_index,
                "db_policy_loss": db_metrics[0],
                "no_db_policy_loss": no_db_metrics[0],
                "db_immediate_baseline_loss": db_metrics[1],
                "no_db_immediate_baseline_loss": no_db_metrics[1],
                "db_successor_baseline_loss": db_metrics[2],
                "no_db_successor_baseline_loss": no_db_metrics[2],
                "db_registered_gradient_norm": registered_norm,
                "gradient_evidence": {
                    source.DB_ARM: db_probe.gradient_evidence,
                    source.NO_DB_ARM: no_db_plan.gradient_evidence,
                },
                "direction_comparison": direction_comparison,
                "no_db_composition": source.raw_sum_composition_record(
                    no_db_plan.composition
                ),
            }
        )
    rng_unchanged = torch.equal(rng_before, torch.random.get_rng_state())
    steps_after = {
        arm: _optimizer_step_values(optimizers[arm], models[arm])
        for arm in source.ARMS
    }
    exposure_valid = all(
        before
        and len(before) == len(steps_after[arm])
        and all(after == prior + source.PPO_PASSES for prior, after in zip(before, steps_after[arm]))
        for arm, before in steps_before.items()
    )
    passed = bool(
        rng_unchanged
        and exposure_valid
        and paired_source["passed"] is True
        and source.raw_sum_null_dependency_audit()["passed"] is True
        and all(
            all(
                source.validate_registered_gradient_evidence(
                    record["gradient_evidence"][arm]  # type: ignore[index]
                )
                for arm in source.ARMS
            )
            and record["direction_comparison"]["passed"] is True  # type: ignore[index]
            for record in pass_records
        )
    )
    authority = models[source.DB_ARM].accepted_g40_anchor_authority
    record: dict[str, object] = {
        "algorithm_id": source.ALGORITHM_ID,
        "accepted_g41_source_commit": source.ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g40_anchor_registry": [
            g41.accepted_g40_anchor_identity(replicate)
            for replicate in source.ACCEPTED_G40_ANCHOR_REPLICATES
        ],
        "arms": list(source.ARMS),
        "accepted_g40_anchor_replicate": authority.replicate,
        "update_index": update_index,
        "branch_boundary": boundary,
        "paired_source_audit": paired_source,
        "paired_collection_before_update": True,
        "branch_update_order": list(source.ARMS),
        "advantage_normalization_count": 2,
        "advantage_recomputed_between_passes": False,
        "actor_head_optimizer_steps_before": {
            arm: min(values) for arm, values in steps_before.items()
        },
        "actor_head_optimizer_steps": {
            arm: min(values) for arm, values in steps_after.items()
        },
        "actor_head_optimizer_step_delta": source.PPO_PASSES,
        "baseline_update_rule_equal": True,
        "baseline_optimizer_exposure_equal": (
            min(steps_after[source.DB_ARM]) == min(steps_after[source.NO_DB_ARM])
        ),
        "torch_rng_unchanged": rng_unchanged,
        "raw_sum_null_dependency_audit": source.raw_sum_null_dependency_audit(),
        "pass_records": pass_records,
        "real_transitions": len(source.ARMS) * source.MAX_CONFORMANCE_TRANSITIONS,
        "K_search": 0,
        "hypothetical_transitions": 0,
        "treatment_separation_observed": any(
            row["direction_comparison"]["strict_separation_observed"] is True  # type: ignore[index]
            for row in pass_records
        ),
        "passed": passed,
    }
    if not passed or not source._update_gradient_evidence_valid(record):
        raise RuntimeError("G42 repeated update evidence failed validation")
    return record


def _checkpoint_reference(replicate: int, arm: str) -> str:
    if arm not in source.ARMS:
        raise ValueError("G42 checkpoint arm is not registered")
    safe_arm = arm.lower()
    return f"checkpoints/replicate_{replicate}_{safe_arm}_final.pt"


def _save_checkpoint(
    path: Path,
    *,
    source_commit: str,
    aligned_source_commit: str,
    formal: bool,
    replicate: int,
    arm: str,
    configuration: Mapping[str, object],
    seeds: Mapping[str, int],
    model: g41.G41NoSlowProjection,
    final_update_record: Mapping[str, object],
    conclusion_evidence: Mapping[str, object],
) -> dict[str, object]:
    certificate = source.build_final_checkpoint(
        arm,
        model,
        final_update_record,
        conclusion_evidence,
        formal=formal,
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "source_commit": source_commit,
        "aligned_source_commit": aligned_source_commit,
        "formal": formal,
        "replicate": replicate,
        "arm": arm,
        "kind": "final_only",
        "configuration": dict(configuration),
        "seeds": dict(seeds),
        "accepted_g40_anchor_authority": g41.accepted_g40_anchor_identity(replicate),
        "accepted_g41_source_commit": source.ACCEPTED_G41_SOURCE_COMMIT,
        "completed_branch_updates": int(configuration["branch_updates_per_arm"]),
        "actor_head_optimizer_steps": (
            int(configuration["branch_updates_per_arm"])
            * int(configuration["ppo_passes"])
        ),
        "conclusion_evidence": dict(conclusion_evidence),
        "source_final_checkpoint_certificate": certificate,
        "model_state": certificate["model_state"],
        "model_state_digest": certificate["model_state_digest"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, path)
    return payload


def _finite_seconds(value: object, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not np.isfinite(float(value))
        or float(value) < 0.0
    ):
        raise ValueError(f"G42 {name} timing invalid")
    return float(value)


def _preflight_digests(root: Path) -> dict[str, str]:
    return {
        "training": _artifact_digest(root / "train_manifest.json"),
        "evaluation": _artifact_digest(root / "evaluation_manifest.json"),
        "analysis": _artifact_digest(root / "analysis_result.json"),
    }


def _validate_formal_preflight(
    preflight_root: Path | None,
    *,
    source_commit: str,
    alignment_disposition: str | None,
    aligned_source_commit: str | None,
    alignment_stage_commit: str | None,
    accepted_anchor_root: Path,
) -> dict[str, str]:
    if preflight_root is None:
        raise ValueError("formal G42 execution requires a bounded preflight root")
    if (
        alignment_disposition != "ALIGNED"
        or aligned_source_commit != ALIGNED_IMPLEMENTATION_COMMIT
        or alignment_stage_commit != ALIGNMENT_STAGE_COMMIT
    ):
        raise ValueError("formal G42 execution requires the registered ALIGNED source")
    root = Path(preflight_root).resolve()
    training = _read_json(root / "train_manifest.json")
    evaluation = _read_json(root / "evaluation_manifest.json")
    analysis = _read_json(root / "analysis_result.json")
    errors = _evaluation_errors(root, training, evaluation)
    if errors:
        raise ValueError("G42 formal preflight artifacts invalid: " + " | ".join(errors))
    train_seconds = _finite_seconds(training.get("stage_wall_time_seconds"), "preflight train")
    eval_seconds = _finite_seconds(evaluation.get("stage_wall_time_seconds"), "preflight evaluate")
    analyze_seconds = _finite_seconds(analysis.get("stage_wall_time_seconds"), "preflight analyze")
    projection = 1.25 * (
        30.0 * train_seconds + 24.0 * eval_seconds + 40.0 * analyze_seconds
    )
    if (
        training.get("formal") is not False
        or evaluation.get("formal") is not False
        or analysis.get("formal") is not False
        or training.get("source_commit") != source_commit
        or evaluation.get("source_commit") != source_commit
        or analysis.get("source_commit") != source_commit
        or training.get("aligned_source_commit") != ALIGNED_IMPLEMENTATION_COMMIT
        or evaluation.get("aligned_source_commit") != ALIGNED_IMPLEMENTATION_COMMIT
        or analysis.get("aligned_source_commit") != ALIGNED_IMPLEMENTATION_COMMIT
        or training.get("accepted_anchor_root") != str(accepted_anchor_root)
        or training.get("configuration") != _configuration(formal=False)
        or evaluation.get("configuration") != _configuration(formal=False)
        or analysis.get("algorithm") != ALGORITHM_ID
        or analysis.get("source_id") != source.SOURCE_ID
        or analysis.get("branch") != NONFORMAL_BRANCH
        or analysis.get("operational_valid") is not True
        or analysis.get("operational_errors") != []
        or analysis.get("training_manifest_digest")
        != _artifact_digest(root / "train_manifest.json")
        or analysis.get("evaluation_manifest_digest")
        != _artifact_digest(root / "evaluation_manifest.json")
        or not np.isclose(
            float(analysis.get("formal_projection_seconds", np.nan)),
            projection,
            rtol=0.0,
            atol=1e-9,
        )
        or analysis.get("formal_projection_executable") is not True
        or train_seconds + eval_seconds + analyze_seconds
        > NONFORMAL_WALL_CLOCK_CAP_SECONDS
        or projection > FORMAL_WALL_CLOCK_CAP_SECONDS
    ):
        raise ValueError("G42 formal preflight is not executable for the aligned source")
    return _preflight_digests(root)


def _train_replicate(
    *,
    formal: bool,
    replicate: int,
    configuration: Mapping[str, object],
    accepted_anchor_root: Path,
) -> dict[str, Any]:
    seeds = seed_block(replicate, formal=formal)
    configure_runtime(seeds["branch_gradient_probe"])
    anchor = _load_accepted_anchor(accepted_anchor_root, replicate)
    anchor_digest = g41._state_digest(anchor.state_dict())
    models = source.project_g42_arms(
        anchor, accepted_anchor_replicate=replicate
    )
    for model in models.values():
        model.begin_credit_branch_phase()
    initial_actor = {
        arm: g40.state_bytes(model.policy) for arm, model in models.items()
    }
    initial_baseline = {
        arm: g40.state_bytes(model.credit_baselines)
        for arm, model in models.items()
    }
    optimizers = {
        arm: g41.make_actor_head_optimizer(model)
        for arm, model in models.items()
    }
    boundary = source.branch_boundary_audit(models, optimizers)
    if boundary["passed"] is not True:
        raise RuntimeError("G42 branch boundary failed before the first update")
    records: list[dict[str, object]] = []
    lifecycle = {arm: True for arm in source.ARMS}
    for update_index in range(int(configuration["branch_updates_per_arm"])):
        first = update_index * int(configuration["num_envs"])
        episode_ids = tuple(
            range(first, first + int(configuration["num_envs"]))
        )
        ledger_seed = (
            seeds["branch_gradient_probe"]
            if update_index == 0
            else seeds["branch_ledger"]
        )
        action_seed = (
            seeds["branch_gradient_probe"]
            if update_index == 0
            else seeds["branch_action"]
        )
        trajectories = {
            arm: _collect_trajectory(
                model,
                episode_ids=episode_ids,
                ledger_seed=ledger_seed,
                action_seed=action_seed,
            )
            for arm, model in models.items()
        }
        for arm, trajectory in trajectories.items():
            lifecycle[arm] &= g40_runner._lifecycle_valid(trajectory)
        if not all(lifecycle.values()):
            raise RuntimeError("G42 lifecycle failed before an optimizer step")
        records.append(
            _apply_matched_update(
                models,
                optimizers,
                trajectories,
                update_index=update_index,
                ledger_seed=ledger_seed,
                action_seed=action_seed,
            )
        )
    expected_steps = (
        int(configuration["branch_updates_per_arm"])
        * int(configuration["ppo_passes"])
    )
    actor_departure = {
        arm: g40.state_bytes(model.policy) != initial_actor[arm]
        for arm, model in models.items()
    }
    baseline_departure = {
        arm: g40.state_bytes(model.credit_baselines) != initial_baseline[arm]
        for arm, model in models.items()
    }
    exposure = {
        arm: min(_optimizer_step_values(optimizers[arm], models[arm]))
        for arm in source.ARMS
    }
    if (
        not all(actor_departure.values())
        or not all(baseline_departure.values())
        or any(value != float(expected_steps) for value in exposure.values())
    ):
        raise RuntimeError("G42 final treatment liveness/exposure gate failed")
    return {
        "replicate": replicate,
        "seeds": seeds,
        "accepted_anchor": g41.accepted_g40_anchor_identity(replicate),
        "accepted_anchor_state_digest": anchor_digest,
        "branch_boundary_audit": boundary,
        "paired_collection_before_update": True,
        "branch_update_order": list(source.ARMS),
        "lifecycle_contract_valid": lifecycle,
        "actor_parameter_departure": actor_departure,
        "shared_baseline_parameter_departure": baseline_departure,
        "actor_head_optimizer_steps": exposure,
        "update_records": records,
        "models": models,
    }


def train(
    *,
    run_root: Path,
    source_commit: str,
    formal: bool,
    authorization_token: str | None,
    accepted_anchor_root: Path | None,
    preflight_root: Path | None = None,
    alignment_disposition: str | None = None,
    aligned_source_commit: str | None = None,
    alignment_stage_commit: str | None = None,
) -> dict[str, Any]:
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("G42 training requires an integrated source commit")
    anchor_root = _bind_anchor_root(accepted_anchor_root)
    resolved_run_root = Path(run_root).resolve()
    if resolved_run_root == anchor_root or anchor_root in resolved_run_root.parents:
        raise ValueError("G42 run root cannot write inside the read-only anchor root")
    preflight_digests: dict[str, str] | None = None
    if formal:
        if authorization_token != AUTHORIZATION_TOKEN:
            raise ValueError("G42 formal authorization token mismatch")
        preflight_digests = _validate_formal_preflight(
            preflight_root,
            source_commit=source_commit,
            alignment_disposition=alignment_disposition,
            aligned_source_commit=aligned_source_commit,
            alignment_stage_commit=alignment_stage_commit,
            accepted_anchor_root=anchor_root,
        )
    elif any(
        value is not None
        for value in (
            authorization_token,
            preflight_root,
            alignment_disposition,
            aligned_source_commit,
            alignment_stage_commit,
        )
    ):
        raise ValueError("G42 nonformal training cannot carry formal authority")
    started = time.perf_counter()
    configuration = _configuration(formal=formal)
    configure_runtime(bootstrap_seed(formal=formal))
    native_backend = _native_backend_identity()
    anchor_digests = _validate_anchor_manifest(anchor_root)
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "checkpoints").mkdir(exist_ok=True)
    internal_rows = [
        _train_replicate(
            formal=formal,
            replicate=replicate,
            configuration=configuration,
            accepted_anchor_root=anchor_root,
        )
        for replicate in range(int(configuration["replicates"]))
    ]
    update_records = [
        record
        for row in internal_rows
        for record in row["update_records"]
    ]
    conclusion_evidence = source.build_conclusion_evidence(
        update_records, formal=formal
    )
    if not source.validate_conclusion_evidence(conclusion_evidence):
        raise RuntimeError("G42 directional treatment did not activate in every replicate")
    rows: list[dict[str, Any]] = []
    for internal in internal_rows:
        replicate = int(internal["replicate"])
        models = internal.pop("models")
        arms: dict[str, dict[str, object]] = {}
        for arm in source.ARMS:
            reference = _checkpoint_reference(replicate, arm)
            payload = _save_checkpoint(
                run_root / reference,
                source_commit=source_commit,
                aligned_source_commit=ALIGNED_IMPLEMENTATION_COMMIT,
                formal=formal,
                replicate=replicate,
                arm=arm,
                configuration=configuration,
                seeds=internal["seeds"],
                model=models[arm],
                final_update_record=internal["update_records"][-1],
                conclusion_evidence=conclusion_evidence,
            )
            arms[arm] = {
                "final_checkpoint": reference,
                "final_checkpoint_file_digest": _artifact_digest(run_root / reference),
                "final_state_digest": payload["model_state_digest"],
                "completed_branch_updates": int(configuration["branch_updates_per_arm"]),
                "actor_head_optimizer_steps": payload["actor_head_optimizer_steps"],
                "actor_parameter_departure": internal["actor_parameter_departure"][arm],
                "shared_baseline_parameter_departure": internal["shared_baseline_parameter_departure"][arm],
            }
        internal["arms"] = arms
        rows.append(internal)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "train",
        "status": "COMPLETE",
        "formal": formal,
        "source_commit": source_commit,
        "authorization_token": authorization_token,
        "alignment_audit_id": ALIGNMENT_AUDIT_ID if formal else None,
        "alignment_disposition": alignment_disposition,
        "aligned_source_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "alignment_stage_commit": alignment_stage_commit,
        "preflight_root": (
            str(Path(preflight_root).resolve()) if preflight_root is not None else None
        ),
        "preflight_artifact_digests": preflight_digests,
        "accepted_anchor_root": str(anchor_root),
        "accepted_anchor_root_mode": "read_only_input_no_writes",
        "accepted_anchor_artifact_digests": anchor_digests,
        "runtime": _runtime_identity(),
        "native_backend": native_backend,
        "configuration": configuration,
        "source_controls": source_controls(),
        "conclusion_evidence": conclusion_evidence,
        "stage_wall_time_seconds": time.perf_counter() - started,
        "replicate_results": rows,
    }
    _write_json(run_root / "train_manifest.json", manifest)
    return manifest


def _cell_contract(name: str) -> dict[str, object]:
    contracts = {
        FINAL_FIXED_DET: {"process": "fixed", "deterministic": True},
        FINAL_FIXED_STOCH: {"process": "fixed", "deterministic": False},
        FINAL_RANDOM_DET: {"process": "random", "deterministic": True},
        FINAL_RANDOM_STOCH: {"process": "random", "deterministic": False},
    }
    if name not in contracts:
        raise ValueError("G42 unknown evaluation cell")
    return {"checkpoint": "final", **contracts[name]}


def _load_checkpoint_payload(
    path: Path,
    *,
    training: Mapping[str, Any],
    replicate: int,
    arm: str,
) -> Mapping[str, Any]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    configuration = training["configuration"]
    seeds = seed_block(replicate, formal=bool(training["formal"]))
    expected = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "source_commit": training["source_commit"],
        "aligned_source_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "formal": bool(training["formal"]),
        "replicate": replicate,
        "arm": arm,
        "kind": "final_only",
        "configuration": configuration,
        "seeds": seeds,
        "accepted_g40_anchor_authority": g41.accepted_g40_anchor_identity(replicate),
        "accepted_g41_source_commit": source.ACCEPTED_G41_SOURCE_COMMIT,
        "completed_branch_updates": int(configuration["branch_updates_per_arm"]),
        "actor_head_optimizer_steps": (
            int(configuration["branch_updates_per_arm"])
            * int(configuration["ppo_passes"])
        ),
        "conclusion_evidence": training["conclusion_evidence"],
    }
    expected_keys = {
        *expected,
        "source_final_checkpoint_certificate",
        "model_state",
        "model_state_digest",
    }
    if (
        not isinstance(payload, Mapping)
        or set(payload) != expected_keys
        or any(payload.get(name) != value for name, value in expected.items())
    ):
        raise ValueError("G42 final checkpoint identity mismatch")
    state = payload.get("model_state")
    digest = payload.get("model_state_digest")
    if (
        not isinstance(state, Mapping)
        or not all(isinstance(name, str) and isinstance(value, torch.Tensor) for name, value in state.items())
        or not isinstance(digest, str)
        or g41._state_digest(state) != digest
        or any("slow_critic" in name for name in state)
    ):
        raise ValueError("G42 final checkpoint state mismatch")
    certificate = payload.get("source_final_checkpoint_certificate")
    certificate_diagnostics = (
        certificate.get("diagnostics") if isinstance(certificate, Mapping) else None
    )
    if (
        not isinstance(certificate, Mapping)
        or certificate.get("model_state_digest") != digest
        or certificate.get("arm") != arm
        or certificate.get("formal") is not bool(training["formal"])
        or certificate.get("standalone_slow_present") is not False
        or certificate.get("actor_head_optimizer_steps") != source.PPO_PASSES
        or not isinstance(certificate_diagnostics, Mapping)
        or certificate_diagnostics.get("treatment_separation")
        != training["conclusion_evidence"]
    ):
        raise ValueError("G42 accepted-source checkpoint certificate mismatch")
    return payload


def _load_final_model(
    *,
    run_root: Path,
    training: Mapping[str, Any],
    replicate: int,
    capacity: int,
    arm: str,
) -> g41.G41NoSlowProjection:
    reference = training["replicate_results"][replicate]["arms"][arm]["final_checkpoint"]
    payload = _load_checkpoint_payload(
        run_root / reference,
        training=training,
        replicate=replicate,
        arm=arm,
    )
    anchor_root = _bind_anchor_root(Path(str(training["accepted_anchor_root"])))
    anchor = _load_accepted_anchor(anchor_root, replicate)
    if capacity != g32.TRAIN_CAPACITY:
        authority = g41.accepted_g40_anchor_authority(replicate)
        resized = g40.make_model(
            capacity, initialization_seed=authority.anchor_model_seed
        )
        resized.load_state_dict(anchor.state_dict(), strict=True)
        anchor = resized
    models = source.project_g42_arms(
        anchor, accepted_anchor_replicate=replicate
    )
    for model in models.values():
        model.begin_credit_branch_phase()
    model = models[arm]
    model.load_state_dict(payload["model_state"], strict=True)
    if g41._state_digest(model.state_dict()) != payload["model_state_digest"]:
        raise ValueError("G42 deployed final state digest mismatch")
    return model


def _expected_final_checkpoint_files(
    rows: Sequence[object],
) -> set[str]:
    expected_files: set[str] = set()
    for replicate, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError("G42 final checkpoint inventory mismatch")
        arms = row.get("arms")
        if not isinstance(arms, Mapping) or set(arms) != set(source.ARMS):
            raise ValueError("G42 final checkpoint inventory mismatch")
        for arm in source.ARMS:
            arm_row = arms.get(arm)
            if not isinstance(arm_row, Mapping):
                raise ValueError("G42 final checkpoint inventory mismatch")
            reference = arm_row.get("final_checkpoint")
            if reference != _checkpoint_reference(replicate, arm):
                raise ValueError("G42 final checkpoint inventory mismatch")
            expected_files.add(Path(reference).name)
    if len(expected_files) != len(rows) * len(source.ARMS):
        raise ValueError("G42 final checkpoint inventory mismatch")
    return expected_files


def _training_errors(
    run_root: Path, training: Mapping[str, Any]
) -> list[str]:
    errors: list[str] = []
    formal = bool(training.get("formal"))
    configuration = _configuration(formal=formal)
    if (
        training.get("schema_version") != SCHEMA_VERSION
        or training.get("algorithm") != ALGORITHM_ID
        or training.get("source_id") != source.SOURCE_ID
        or training.get("stage") != "train"
        or training.get("status") != "COMPLETE"
        or training.get("configuration") != configuration
        or training.get("source_controls") != source_controls()
        or training.get("aligned_source_commit") != ALIGNED_IMPLEMENTATION_COMMIT
        or re.fullmatch(r"[0-9a-f]{40}", str(training.get("source_commit"))) is None
    ):
        return ["G42 training identity mismatch"]
    backend = training.get("native_backend")
    if (
        not isinstance(backend, Mapping)
        or backend.get("kind") != "ContinuousRosterToyBatch_CPU_CPP"
        or backend.get("required") is not True
        or backend.get("python_fallback") is not False
    ):
        errors.append("G42 native backend binding mismatch")
    try:
        anchor_root = _bind_anchor_root(Path(str(training["accepted_anchor_root"])))
        if training.get("accepted_anchor_root_mode") != "read_only_input_no_writes":
            raise ValueError("G42 accepted anchor mode mismatch")
        if _validate_anchor_manifest(anchor_root) != training.get(
            "accepted_anchor_artifact_digests"
        ):
            raise ValueError("G42 accepted anchor digest binding mismatch")
    except (KeyError, OSError, TypeError, ValueError) as error:
        errors.append(str(error))
        anchor_root = _expected_anchor_root()
    if formal:
        if (
            training.get("authorization_token") != AUTHORIZATION_TOKEN
            or training.get("alignment_audit_id") != ALIGNMENT_AUDIT_ID
            or training.get("alignment_disposition") != "ALIGNED"
            or training.get("alignment_stage_commit") != ALIGNMENT_STAGE_COMMIT
            or not isinstance(training.get("preflight_artifact_digests"), dict)
        ):
            errors.append("G42 formal authority binding mismatch")
        else:
            try:
                serialized = training.get("preflight_root")
                if not isinstance(serialized, str) or not Path(serialized).is_absolute():
                    raise ValueError("G42 formal preflight root mismatch")
                live = _validate_formal_preflight(
                    Path(serialized),
                    source_commit=str(training["source_commit"]),
                    alignment_disposition=str(training["alignment_disposition"]),
                    aligned_source_commit=str(training["aligned_source_commit"]),
                    alignment_stage_commit=str(training["alignment_stage_commit"]),
                    accepted_anchor_root=anchor_root,
                )
                if live != training.get("preflight_artifact_digests"):
                    raise ValueError("G42 formal preflight digest binding mismatch")
            except (OSError, TypeError, ValueError) as error:
                errors.append(str(error))
    elif any(
        training.get(name) is not None
        for name in (
            "authorization_token",
            "alignment_audit_id",
            "alignment_disposition",
            "alignment_stage_commit",
            "preflight_root",
            "preflight_artifact_digests",
        )
    ):
        errors.append("G42 nonformal artifact carried formal authority")
    rows = training.get("replicate_results")
    if not isinstance(rows, list) or len(rows) != int(configuration["replicates"]):
        return errors + ["G42 training replicate inventory mismatch"]
    all_update_records: list[Mapping[str, object]] = []
    update_records_complete = True
    try:
        expected_files = _expected_final_checkpoint_files(rows)
    except (TypeError, ValueError) as error:
        errors.append(str(error))
        expected_files = None
    expected_steps = (
        int(configuration["branch_updates_per_arm"])
        * int(configuration["ppo_passes"])
    )
    for replicate, row in enumerate(rows):
        try:
            records = row["update_records"]
            if (
                row["replicate"] != replicate
                or row["seeds"] != seed_block(replicate, formal=formal)
                or row["accepted_anchor"] != g41.accepted_g40_anchor_identity(replicate)
                or row["accepted_anchor_state_digest"]
                != g41.accepted_g40_anchor_authority(replicate).complete_state_digest
                or row["branch_boundary_audit"]["passed"] is not True
                or row["paired_collection_before_update"] is not True
                or row["branch_update_order"] != list(source.ARMS)
                or not all(row["lifecycle_contract_valid"].values())
                or not all(row["actor_parameter_departure"].values())
                or not all(row["shared_baseline_parameter_departure"].values())
                or any(float(value) != float(expected_steps) for value in row["actor_head_optimizer_steps"].values())
                or not isinstance(records, list)
                or len(records) != int(configuration["branch_updates_per_arm"])
            ):
                raise ValueError("G42 replicate invariant mismatch")
            for update_index, record in enumerate(records):
                if (
                    record.get("update_index") != update_index
                    or not source._update_gradient_evidence_valid(record)
                    or record.get("paired_collection_before_update") is not True
                    or record.get("branch_update_order") != list(source.ARMS)
                    or record.get("K_search") != 0
                    or record.get("hypothetical_transitions") != 0
                ):
                    raise ValueError("G42 update evidence mismatch")
                all_update_records.append(record)
        except (KeyError, TypeError, ValueError) as error:
            errors.append(str(error))
            update_records_complete = False
        try:
            for arm in source.ARMS:
                arm_row = row["arms"][arm]
                reference = arm_row["final_checkpoint"]
                if (
                    arm_row["completed_branch_updates"]
                    != int(configuration["branch_updates_per_arm"])
                    or arm_row["actor_head_optimizer_steps"] != expected_steps
                    or arm_row["actor_parameter_departure"] is not True
                    or arm_row["shared_baseline_parameter_departure"] is not True
                    or arm_row["final_checkpoint_file_digest"]
                    != _artifact_digest(run_root / reference)
                ):
                    raise ValueError("G42 final checkpoint inventory mismatch")
                payload = _load_checkpoint_payload(
                    run_root / reference,
                    training=training,
                    replicate=replicate,
                    arm=arm,
                )
                if payload["model_state_digest"] != arm_row["final_state_digest"]:
                    raise ValueError("G42 final checkpoint digest mismatch")
        except (KeyError, OSError, TypeError, ValueError) as error:
            errors.append(str(error))
    conclusion_evidence = training.get("conclusion_evidence")
    if not source.validate_conclusion_evidence(conclusion_evidence):
        errors.append("G42 conclusion treatment-separation evidence mismatch")
    elif update_records_complete:
        expected_conclusion = source.build_conclusion_evidence(
            all_update_records, formal=formal
        )
        if expected_conclusion != conclusion_evidence:
            errors.append("G42 conclusion treatment-separation evidence mismatch")
    try:
        observed_files = {path.name for path in (run_root / "checkpoints").iterdir()}
        if expected_files is not None and observed_files != expected_files:
            errors.append("G42 checkpoint inventory is not final-only")
    except OSError as error:
        errors.append(str(error))
    return errors


class _G42RetainedEvaluationPolicy:
    """Expose only the accepted retained actor step to the generic evaluator."""

    __slots__ = ("_projection",)

    def __init__(self, projection: g41.G41NoSlowProjection) -> None:
        if projection.phase != "credit_branch" or hasattr(
            projection, "slow_critic"
        ):
            raise ValueError("G42 evaluation requires the retained no-slow branch")
        self._projection = projection

    @property
    def member_capacity(self) -> int:
        return self._projection.member_capacity

    @property
    def hidden_dim(self) -> int:
        return self._projection.hidden_dim

    def eval(self) -> _G42RetainedEvaluationPolicy:
        self._projection.eval()
        return self

    def forward_step(self, **arguments: Any) -> g41.G41ActorStep:
        return g41.retained_actor_step(self._projection, **arguments)


def _evaluate_cell(
    *,
    replicate: int,
    capacity: int,
    arm: str,
    name: str,
    processes: Sequence[g34.RandomProcessLedger],
    action_seed: int,
    deployed: g41.G41NoSlowProjection,
) -> dict[str, object]:
    contract = _cell_contract(name)
    before = _state_digest(deployed)
    episodes, lifecycle = g40.evaluate_model(
        _G42RetainedEvaluationPolicy(deployed),  # type: ignore[arg-type]
        processes=processes,
        action_seed=action_seed,
        process_kind=str(contract["process"]),
        deterministic=bool(contract["deterministic"]),
    )
    return {
        "replicate": replicate,
        "capacity": capacity,
        "arm": arm,
        "cell": name,
        **contract,
        "optimizer_steps": 0,
        "state_before": before,
        "state_after": _state_digest(deployed),
        "lifecycle_valid": lifecycle,
        "episodes": list(episodes),
    }


def evaluate(*, run_root: Path) -> dict[str, Any]:
    started = time.perf_counter()
    training = _read_json(run_root / "train_manifest.json")
    errors = _training_errors(run_root, training)
    if errors:
        raise ValueError("G42 training artifact invalid: " + " | ".join(errors))
    formal = bool(training["formal"])
    configuration = _configuration(formal=formal)
    configure_runtime(bootstrap_seed(formal=formal))
    native_backend = _native_backend_identity()
    cells: list[dict[str, object]] = []
    inventories: list[dict[str, object]] = []
    direct_source_valid = True
    for replicate in range(int(configuration["replicates"])):
        seeds = seed_block(replicate, formal=formal)
        for capacity in g34.CAPACITIES:
            processes, inventory = _source_inventory(
                replicate=replicate,
                capacity=capacity,
                episode_count=int(configuration["evaluation_episodes_per_cell"]),
                formal=formal,
            )
            inventories.append(inventory)
            direct_source_valid &= g38_runner._direct_source_validation(processes)
            final_models = {
                arm: _load_final_model(
                    run_root=run_root,
                    training=training,
                    replicate=replicate,
                    capacity=capacity,
                    arm=arm,
                )
                for arm in source.ARMS
            }
            for arm in source.ARMS:
                for name in MODEL_CELLS:
                    cells.append(
                        _evaluate_cell(
                            replicate=replicate,
                            capacity=capacity,
                            arm=arm,
                            name=name,
                            processes=processes,
                            action_seed=seeds["evaluation_action"],
                            deployed=final_models[arm],
                        )
                    )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "evaluate",
        "status": "COMPLETE",
        "formal": formal,
        "source_commit": training["source_commit"],
        "authorization_token": training["authorization_token"],
        "alignment_audit_id": training["alignment_audit_id"],
        "alignment_disposition": training["alignment_disposition"],
        "aligned_source_commit": training["aligned_source_commit"],
        "alignment_stage_commit": training["alignment_stage_commit"],
        "preflight_artifact_digests": training["preflight_artifact_digests"],
        "accepted_anchor_artifact_digests": training["accepted_anchor_artifact_digests"],
        "runtime": _runtime_identity(),
        "native_backend": native_backend,
        "configuration": configuration,
        "source_controls": source_controls(),
        "conclusion_evidence": training["conclusion_evidence"],
        "training_manifest_digest": _artifact_digest(run_root / "train_manifest.json"),
        "stage_wall_time_seconds": time.perf_counter() - started,
        "direct_source_validation": bool(direct_source_valid),
        "source_inventory": inventories,
        "cells": cells,
    }
    _write_json(run_root / "evaluation_manifest.json", manifest)
    return manifest


def _evaluation_errors(
    run_root: Path,
    training: Mapping[str, Any],
    evaluation: Mapping[str, Any],
) -> list[str]:
    errors = _training_errors(run_root, training)
    formal = bool(training.get("formal"))
    configuration = _configuration(formal=formal)
    if (
        evaluation.get("schema_version") != SCHEMA_VERSION
        or evaluation.get("algorithm") != ALGORITHM_ID
        or evaluation.get("source_id") != source.SOURCE_ID
        or evaluation.get("stage") != "evaluate"
        or evaluation.get("status") != "COMPLETE"
        or evaluation.get("formal") is not formal
        or evaluation.get("source_commit") != training.get("source_commit")
        or evaluation.get("authorization_token") != training.get("authorization_token")
        or evaluation.get("alignment_audit_id") != training.get("alignment_audit_id")
        or evaluation.get("alignment_disposition") != training.get("alignment_disposition")
        or evaluation.get("aligned_source_commit") != ALIGNED_IMPLEMENTATION_COMMIT
        or evaluation.get("alignment_stage_commit") != training.get("alignment_stage_commit")
        or evaluation.get("preflight_artifact_digests")
        != training.get("preflight_artifact_digests")
        or evaluation.get("accepted_anchor_artifact_digests")
        != training.get("accepted_anchor_artifact_digests")
        or evaluation.get("configuration") != configuration
        or evaluation.get("source_controls") != source_controls()
        or evaluation.get("conclusion_evidence") != training.get("conclusion_evidence")
        or evaluation.get("training_manifest_digest")
        != _artifact_digest(run_root / "train_manifest.json")
        or evaluation.get("direct_source_validation") is not True
    ):
        errors.append("G42 evaluation identity/source mismatch")
    backend = evaluation.get("native_backend")
    if (
        not isinstance(backend, Mapping)
        or backend.get("kind") != "ContinuousRosterToyBatch_CPU_CPP"
        or backend.get("required") is not True
        or backend.get("python_fallback") is not False
    ):
        errors.append("G42 evaluation native backend mismatch")
    cells = evaluation.get("cells")
    if not isinstance(cells, list) or len(cells) != int(configuration["total_cells"]):
        return errors + ["G42 evaluation cell inventory mismatch"]
    expected_inventories: list[dict[str, object]] = []
    for replicate in range(int(configuration["replicates"])):
        for capacity in g34.CAPACITIES:
            _, inventory = _source_inventory(
                replicate=replicate,
                capacity=capacity,
                episode_count=int(configuration["evaluation_episodes_per_cell"]),
                formal=formal,
            )
            expected_inventories.append(inventory)
    if evaluation.get("source_inventory") != expected_inventories:
        errors.append("G42 source inventory mismatch")
    inventories = {
        (int(row["replicate"]), int(row["capacity"])): row["processes"]
        for row in evaluation.get("source_inventory", [])
    }
    observed: set[tuple[int, int, str, str]] = set()
    for cell in cells:
        try:
            key = (
                int(cell["replicate"]),
                int(cell["capacity"]),
                str(cell["arm"]),
                str(cell["cell"]),
            )
            if (
                key in observed
                or key[0] not in range(int(configuration["replicates"]))
                or key[1] not in g34.CAPACITIES
                or key[2] not in source.ARMS
                or key[3] not in MODEL_CELLS
            ):
                raise ValueError("G42 evaluation cell identity mismatch")
            observed.add(key)
            contract = _cell_contract(key[3])
            if any(cell.get(name) != value for name, value in contract.items()):
                raise ValueError("G42 evaluation route mismatch")
            expected_digest = training["replicate_results"][key[0]]["arms"][key[2]]["final_state_digest"]
            if (
                cell.get("optimizer_steps") != 0
                or cell.get("state_before") != cell.get("state_after")
                or cell.get("state_before") != expected_digest
                or cell.get("lifecycle_valid") is not True
            ):
                raise ValueError("G42 evaluation mutation/checkpoint mismatch")
            episodes = cell.get("episodes")
            if not isinstance(episodes, list) or len(episodes) != int(
                configuration["evaluation_episodes_per_cell"]
            ):
                raise ValueError("G42 evaluation episode inventory mismatch")
            expected_rows = inventories[(key[0], key[1])]
            roster_field = (
                "random_expected_roster_sizes"
                if contract["process"] == "random"
                else "fixed_expected_roster_sizes"
            )
            for index, episode in enumerate(episodes):
                expected = expected_rows[index]
                if (
                    episode.get("local_episode_id") != index
                    or episode.get("episode_id") != expected["episode_id"]
                    or episode.get("signature") != expected["signature"]
                    or episode.get("event_times") != expected["event_times"]
                    or episode.get("event_order") != expected["event_order"]
                    or episode.get("roster_sizes_valid") is not True
                ):
                    raise ValueError("G42 paired evaluation episode mismatch")
                trace = g39_runner.g34_runner._trace_evidence(episode)
                if (
                    trace["roster_size_trace"] != tuple(expected[roster_field])
                    or not g39_runner.g34_runner._summary_matches_trace(episode, trace)
                ):
                    raise ValueError("G42 evaluation trace mismatch")
        except (KeyError, TypeError, ValueError) as error:
            errors.append(str(error))
    expected_keys = {
        (replicate, capacity, arm, name)
        for replicate in range(int(configuration["replicates"]))
        for capacity in g34.CAPACITIES
        for arm in source.ARMS
        for name in MODEL_CELLS
    }
    if observed != expected_keys:
        errors.append("G42 evaluation cell key set mismatch")
    return errors


def _cell_map(
    evaluation: Mapping[str, Any],
) -> dict[tuple[int, int, str, str], Mapping[str, Any]]:
    return {
        (
            int(row["replicate"]),
            int(row["capacity"]),
            str(row["arm"]),
            str(row["cell"]),
        ): row
        for row in evaluation["cells"]
    }


def _metric_arrays(
    evaluation: Mapping[str, Any], arm: str, cell: str, metric: str
) -> dict[int, np.ndarray]:
    cells = _cell_map(evaluation)
    replicates = int(evaluation["configuration"]["replicates"])
    return {
        capacity: np.asarray(
            [
                [
                    g39_runner.g34_runner._trace_evidence(episode)[metric]
                    for episode in cells[(replicate, capacity, arm, cell)]["episodes"]
                ]
                for replicate in range(replicates)
            ],
            dtype=np.float64,
        )
        for capacity in g34.CAPACITIES
    }


def _difference(
    left: Mapping[int, np.ndarray], right: Mapping[int, np.ndarray]
) -> dict[int, np.ndarray]:
    return {capacity: left[capacity] - right[capacity] for capacity in left}


def _bootstrap_plan(
    *, formal: bool, replicates: int, episodes: int, repetitions: int
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(bootstrap_seed(formal=formal))
    return (
        rng.integers(0, replicates, size=(repetitions, replicates), dtype=np.int16),
        rng.integers(
            0,
            episodes,
            size=(repetitions, replicates, len(g34.CAPACITIES), episodes),
            dtype=np.int16,
        ),
    )


def _hierarchical_ci(
    values: Mapping[int, np.ndarray],
    *,
    capacities: Sequence[int],
    plan: tuple[np.ndarray, np.ndarray],
) -> list[float]:
    return g35_runner._hierarchical_ci(values, capacities=capacities, plan=plan)


def _arm_access(
    evaluation: Mapping[str, Any], arm: str, plan: tuple[np.ndarray, np.ndarray]
) -> dict[str, object]:
    fixed = _metric_arrays(evaluation, arm, FINAL_FIXED_DET, "utility")
    fixed_stoch = _metric_arrays(evaluation, arm, FINAL_FIXED_STOCH, "utility")
    random = _metric_arrays(evaluation, arm, FINAL_RANDOM_DET, "utility")
    event = _metric_arrays(
        evaluation, arm, FINAL_RANDOM_DET, "minimum_event_window_utility"
    )
    segment = _metric_arrays(
        evaluation, arm, FINAL_RANDOM_DET, "minimum_process_segment_utility"
    )
    random_stoch = _metric_arrays(evaluation, arm, FINAL_RANDOM_STOCH, "utility")
    process = _difference(random, fixed)
    per_capacity = lambda values: {
        capacity: _hierarchical_ci(values, capacities=(capacity,), plan=plan)
        for capacity in g34.CAPACITIES
    }
    fixed_ci, random_ci, event_ci, segment_ci, process_ci = map(
        per_capacity, (fixed, random, event, segment, process)
    )
    fixed_stoch_ci = _hierarchical_ci(
        fixed_stoch, capacities=g34.CAPACITIES, plan=plan
    )
    random_stoch_ci = _hierarchical_ci(
        random_stoch, capacities=g34.CAPACITIES, plan=plan
    )
    min_fixed = g38_runner._minimum_replicate_mean(fixed)
    min_random = g38_runner._minimum_replicate_mean(random)
    access_pass = (
        all(g38_runner._inclusive_ge(fixed_ci[c][0], UTILITY_FLOOR) for c in g34.CAPACITIES)
        and g38_runner._inclusive_ge(fixed_stoch_ci[0], STOCHASTIC_FLOOR)
        and g38_runner._inclusive_ge(min_fixed, MINIMUM_REPLICATE_FLOOR)
        and all(g38_runner._inclusive_ge(random_ci[c][0], UTILITY_FLOOR) for c in g34.CAPACITIES)
        and all(g38_runner._inclusive_ge(event_ci[c][0], EVENT_FLOOR) for c in g34.CAPACITIES)
        and all(g38_runner._inclusive_ge(segment_ci[c][0], SEGMENT_FLOOR) for c in g34.CAPACITIES)
        and all(g38_runner._inclusive_ge(process_ci[c][0], PROCESS_MARGIN) for c in g34.CAPACITIES)
        and g38_runner._inclusive_ge(random_stoch_ci[0], STOCHASTIC_FLOOR)
        and g38_runner._inclusive_ge(min_random, MINIMUM_REPLICATE_FLOOR)
    )
    confident_fail = (
        any(not g38_runner._inclusive_ge(fixed_ci[c][2], UTILITY_FLOOR) for c in g34.CAPACITIES)
        or not g38_runner._inclusive_ge(fixed_stoch_ci[2], STOCHASTIC_FLOOR)
        or not g38_runner._inclusive_ge(min_fixed, MINIMUM_REPLICATE_FLOOR)
        or any(not g38_runner._inclusive_ge(random_ci[c][2], UTILITY_FLOOR) for c in g34.CAPACITIES)
        or any(not g38_runner._inclusive_ge(event_ci[c][2], EVENT_FLOOR) for c in g34.CAPACITIES)
        or any(not g38_runner._inclusive_ge(segment_ci[c][2], SEGMENT_FLOOR) for c in g34.CAPACITIES)
        or any(not g38_runner._inclusive_ge(process_ci[c][2], PROCESS_MARGIN) for c in g34.CAPACITIES)
        or not g38_runner._inclusive_ge(random_stoch_ci[2], STOCHASTIC_FLOOR)
        or not g38_runner._inclusive_ge(min_random, MINIMUM_REPLICATE_FLOOR)
    )
    return {
        "fixed_utility_ci95": fixed_ci,
        "fixed_stochastic_pooled_ci95": fixed_stoch_ci,
        "minimum_fixed_deterministic_replicate_mean": min_fixed,
        "random_utility_ci95": random_ci,
        "random_event_window_ci95": event_ci,
        "random_process_segment_ci95": segment_ci,
        "random_minus_fixed_ci95": process_ci,
        "random_stochastic_pooled_ci95": random_stoch_ci,
        "minimum_random_deterministic_replicate_mean": min_random,
        "access_pass": bool(access_pass),
        "access_confident_fail": bool(confident_fail),
    }


def _comparison(
    evaluation: Mapping[str, Any], plan: tuple[np.ndarray, np.ndarray]
) -> dict[str, object]:
    component_specs = (
        ("fixed_deterministic_utility", FINAL_FIXED_DET, "utility", False),
        ("random_deterministic_utility", FINAL_RANDOM_DET, "utility", False),
        ("fixed_stochastic_utility", FINAL_FIXED_STOCH, "utility", True),
        ("random_stochastic_utility", FINAL_RANDOM_STOCH, "utility", True),
        ("random_event_window", FINAL_RANDOM_DET, "minimum_event_window_utility", False),
        ("random_process_segment", FINAL_RANDOM_DET, "minimum_process_segment_utility", False),
    )
    component_ci: dict[str, object] = {}
    component_ucbs: list[float] = []
    for name, cell, metric, pooled in component_specs:
        delta = _difference(
            _metric_arrays(evaluation, source.DB_ARM, cell, metric),
            _metric_arrays(evaluation, source.NO_DB_ARM, cell, metric),
        )
        if pooled:
            ci = _hierarchical_ci(delta, capacities=g34.CAPACITIES, plan=plan)
            component_ci[name] = ci
            component_ucbs.append(ci[2])
        else:
            rows = {
                capacity: _hierarchical_ci(delta, capacities=(capacity,), plan=plan)
                for capacity in g34.CAPACITIES
            }
            component_ci[name] = rows
            component_ucbs.extend(row[2] for row in rows.values())
    transport = _difference(
        _difference(
            _metric_arrays(evaluation, source.DB_ARM, FINAL_RANDOM_DET, "utility"),
            _metric_arrays(evaluation, source.DB_ARM, FINAL_FIXED_DET, "utility"),
        ),
        _difference(
            _metric_arrays(evaluation, source.NO_DB_ARM, FINAL_RANDOM_DET, "utility"),
            _metric_arrays(evaluation, source.NO_DB_ARM, FINAL_FIXED_DET, "utility"),
        ),
    )
    transport_rows = {
        capacity: _hierarchical_ci(transport, capacities=(capacity,), plan=plan)
        for capacity in g34.CAPACITIES
    }
    component_ci["random_minus_fixed_transport"] = transport_rows
    component_ucbs.extend(row[2] for row in transport_rows.values())
    primary_values = _difference(
        _metric_arrays(evaluation, source.DB_ARM, FINAL_RANDOM_DET, "utility"),
        _metric_arrays(evaluation, source.NO_DB_ARM, FINAL_RANDOM_DET, "utility"),
    )
    primary = _hierarchical_ci(
        primary_values, capacities=g34.CAPACITIES, plan=plan
    )
    capacity_primary = {
        capacity: _hierarchical_ci(
            primary_values, capacities=(capacity,), plan=plan
        )
        for capacity in g34.CAPACITIES
    }
    noninferior = g38_runner._inclusive_le(primary[2], DIRECTION_MARGIN) and all(
        g38_runner._inclusive_le(value, DIRECTION_MARGIN)
        for value in component_ucbs
    )
    material = g38_runner._strict_gt(primary[0], DIRECTION_MARGIN) and all(
        g38_runner._strict_gt(capacity_primary[capacity][0], 0.0)
        for capacity in g34.CAPACITIES
    )
    return {
        "db_minus_no_db_primary_ci95": primary,
        "db_minus_no_db_capacity_ci95": capacity_primary,
        "component_ci95": component_ci,
        "no_db_noninferior": bool(noninferior),
        "material_db_advantage": bool(material),
    }


def select_g42_result_branch(metrics: Mapping[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    if not bool(metrics["source_valid"]) or bool(metrics["db_access_confident_fail"]):
        return SOURCE_FAILURE_BRANCH
    if (
        bool(metrics["db_access_pass"])
        and bool(metrics["no_db_access_pass"])
        and bool(metrics["no_db_noninferior"])
    ):
        return NO_DB_SUFFICIENT_BRANCH
    if bool(metrics["db_access_pass"]) and (
        bool(metrics["no_db_access_confident_fail"])
        or bool(metrics["material_db_advantage"])
    ):
        return DB_ADVANTAGE_BRANCH
    return UNDERPOWERED_BRANCH


def analyze(*, run_root: Path, require_formal: bool = False) -> dict[str, Any]:
    started = time.perf_counter()
    training = _read_json(run_root / "train_manifest.json")
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    formal = bool(training.get("formal"))
    if require_formal and not formal:
        raise ValueError("formal G42 analysis requires formal artifacts")
    configure_runtime(bootstrap_seed(formal=formal))
    errors = _evaluation_errors(run_root, training, evaluation)
    metrics: dict[str, Any] = {"operational_valid": not errors}
    if not errors:
        configuration = evaluation["configuration"]
        plan = _bootstrap_plan(
            formal=formal,
            replicates=int(configuration["replicates"]),
            episodes=int(configuration["evaluation_episodes_per_cell"]),
            repetitions=int(configuration["bootstrap_resamples"]),
        )
        access = {arm: _arm_access(evaluation, arm, plan) for arm in source.ARMS}
        comparison = _comparison(evaluation, plan)
        metrics.update(
            {
                "source_valid": evaluation["direct_source_validation"] is True,
                "arm_access": access,
                "db_access_pass": access[source.DB_ARM]["access_pass"],
                "no_db_access_pass": access[source.NO_DB_ARM]["access_pass"],
                "db_access_confident_fail": access[source.DB_ARM]["access_confident_fail"],
                "no_db_access_confident_fail": access[source.NO_DB_ARM]["access_confident_fail"],
                "treatment_separation_valid": source.validate_conclusion_evidence(
                    training["conclusion_evidence"]
                ),
                **comparison,
            }
        )
    analysis_seconds = time.perf_counter() - started
    projection: float | None = None
    projection_executable: bool | None = None
    nonformal_total: float | None = None
    if not formal and not errors:
        train_seconds = float(training["stage_wall_time_seconds"])
        eval_seconds = float(evaluation["stage_wall_time_seconds"])
        nonformal_total = train_seconds + eval_seconds + analysis_seconds
        projection = 1.25 * (
            30.0 * train_seconds + 24.0 * eval_seconds + 40.0 * analysis_seconds
        )
        projection_executable = bool(
            nonformal_total <= NONFORMAL_WALL_CLOCK_CAP_SECONDS
            and projection <= FORMAL_WALL_CLOCK_CAP_SECONDS
        )
    if errors:
        branch = INVALID_BRANCH
    elif formal:
        branch = select_g42_result_branch(metrics)
    elif projection_executable:
        branch = NONFORMAL_BRANCH
    else:
        branch = NON_EXECUTABLE_BRANCH
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "analyze",
        "status": "COMPLETE" if not errors else "INVALID",
        "formal": formal,
        "source_commit": training.get("source_commit"),
        "aligned_source_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "alignment_stage_commit": training.get("alignment_stage_commit"),
        "preflight_artifact_digests": training.get("preflight_artifact_digests"),
        "operational_valid": not errors,
        "operational_errors": errors,
        "branch": branch,
        "metrics": metrics,
        "native_backend": evaluation.get("native_backend"),
        "training_manifest_digest": _artifact_digest(run_root / "train_manifest.json"),
        "evaluation_manifest_digest": _artifact_digest(run_root / "evaluation_manifest.json"),
        "stage_wall_time_seconds": analysis_seconds,
        "nonformal_total_wall_time_seconds": nonformal_total,
        "nonformal_wall_clock_cap_seconds": NONFORMAL_WALL_CLOCK_CAP_SECONDS,
        "formal_projection_seconds": projection,
        "formal_projection_executable": projection_executable,
        "formal_wall_clock_cap_seconds": FORMAL_WALL_CLOCK_CAP_SECONDS,
        "thresholds": {
            "utility_floor": UTILITY_FLOOR,
            "event_floor": EVENT_FLOOR,
            "segment_floor": SEGMENT_FLOOR,
            "process_noninferiority_margin": PROCESS_MARGIN,
            "stochastic_floor": STOCHASTIC_FLOOR,
            "minimum_replicate_floor": MINIMUM_REPLICATE_FLOOR,
            "direction_margin": DIRECTION_MARGIN,
        },
    }
    _write_json(run_root / "analysis_result.json", result)
    return result


def exercise(
    *, run_root: Path, source_commit: str, accepted_anchor_root: Path
) -> dict[str, Any]:
    train(
        run_root=run_root,
        source_commit=source_commit,
        formal=False,
        authorization_token=None,
        accepted_anchor_root=accepted_anchor_root,
    )
    evaluate(run_root=run_root)
    return analyze(run_root=run_root)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("train", "evaluate", "analyze", "exercise"))
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit")
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--authorization-token")
    parser.add_argument("--accepted-anchor-root", type=Path)
    parser.add_argument("--preflight-root", type=Path)
    parser.add_argument("--alignment-disposition")
    parser.add_argument("--aligned-source-commit")
    parser.add_argument("--alignment-stage-commit")
    args = parser.parse_args()
    if args.stage == "train":
        if args.source_commit is None:
            raise ValueError("G42 train requires --source-commit")
        train(
            run_root=args.run_root,
            source_commit=args.source_commit,
            formal=args.formal,
            authorization_token=args.authorization_token,
            accepted_anchor_root=args.accepted_anchor_root,
            preflight_root=args.preflight_root,
            alignment_disposition=args.alignment_disposition,
            aligned_source_commit=args.aligned_source_commit,
            alignment_stage_commit=args.alignment_stage_commit,
        )
    elif args.stage == "evaluate":
        evaluate(run_root=args.run_root)
    elif args.stage == "analyze":
        analyze(run_root=args.run_root, require_formal=args.formal)
    else:
        if args.source_commit is None or args.accepted_anchor_root is None:
            raise ValueError("G42 exercise requires source and accepted anchor root")
        exercise(
            run_root=args.run_root,
            source_commit=args.source_commit,
            accepted_anchor_root=args.accepted_anchor_root,
        )


if __name__ == "__main__":
    main()
