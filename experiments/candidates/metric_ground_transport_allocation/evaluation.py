"""Frozen final evaluation, permutation replay, and retained seed packets."""

from __future__ import annotations

from collections import defaultdict

import numpy as np
import torch

from .actor import Actor
from .config import EVALUATION_TAPES, EVAL_SIZES, LOADS, ORDERED_PAIRS, TRUE_UTILITY, demand
from .decoder import DecodeResult, decode
from .environment import (
    alignment, canonical_roles, canonicalize_task_values, coupling_from_actions,
    feasibility_residuals, reward,
)
from .rng import replay_permutations, tapes_for_decisions


MAX_N = max(EVAL_SIZES)


def _pad(array: np.ndarray, shape: tuple[int, ...], fill: float | int = 0) -> np.ndarray:
    result = np.full((array.shape[0], *shape), fill, dtype=array.dtype)
    slices = (slice(None),) + tuple(slice(0, size) for size in array.shape[1:])
    result[slices] = array
    return result


def _feature(n: int, demands: np.ndarray, epoch: int) -> np.ndarray:
    return np.column_stack((np.ones(len(demands)), demands / float(n), np.full(len(demands), epoch - 1.0)))


def _decode(actor: Actor, features: np.ndarray, demands: np.ndarray, roles: np.ndarray, priorities: np.ndarray, uniforms: np.ndarray):
    with torch.no_grad():
        raw, mapped, idle = actor.scores(torch.as_tensor(features, dtype=torch.float64))
        result = decode(
            mapped,
            idle,
            torch.as_tensor(roles, dtype=torch.long),
            torch.as_tensor(demands, dtype=torch.long),
            torch.as_tensor(priorities, dtype=torch.long),
            torch.as_tensor(uniforms, dtype=torch.float64),
        )
    return raw.numpy(), mapped.numpy(), idle.numpy(), result


def _numpy_decode(result: DecodeResult) -> dict[str, np.ndarray]:
    return {
        "actions": result.actions.numpy().astype(np.int8),
        "residual": result.residual.numpy().astype(np.int16),
        "log_probability": result.log_probability.numpy(),
        "mean_entropy": result.mean_entropy.numpy(),
        "probabilities": result.probabilities.numpy(),
        "masks": result.masks.numpy(),
        "expanded_logits": result.expanded_logits.numpy(),
        "idle_logits": result.idle_logits.numpy(),
    }


def _agent_records(roles: np.ndarray) -> np.ndarray:
    result = np.empty((*roles.shape, 3), dtype=np.float64)
    result[:, :, 0] = roles
    result[:, :, 1] = roles * 6.0
    result[:, :, 2] = 1.0
    return result


def _task_records(demands: np.ndarray, displayed: np.ndarray) -> np.ndarray:
    batch = demands.shape[0]
    result = np.empty((batch, 4, 3), dtype=np.float64)
    result[:, :, 0] = np.arange(4)[None, :]
    result[:, :, 1] = displayed[None, :]
    result[:, :, 2] = demands
    return result


def evaluate_fit(actor: Actor, seed: int, arm_code: int, binding_code: int, panel_lookup: dict[tuple[int, int, int, int], int]) -> dict[str, np.ndarray]:
    binding = "INTACT" if binding_code == 0 else "CUT"
    displayed = np.asarray((0.0, 2.0, 4.0, 6.0) if binding == "INTACT" else (6.0, 2.0, 4.0, 0.0))
    parts: dict[str, list[np.ndarray]] = defaultdict(list)
    address_key = 0
    for n in EVAL_SIZES:
        for pair_index, pair in enumerate(ORDERED_PAIRS):
            for load_index, load in enumerate(LOADS):
                episode_rows = []
                for epoch in (1, 2):
                    batch = EVALUATION_TAPES
                    demand_row = np.asarray(demand(n, pair, load, epoch), dtype=np.int16)
                    demands = np.broadcast_to(demand_row, (batch, 4)).copy()
                    features = _feature(n, demands, epoch)
                    roles = np.broadcast_to(canonical_roles(n), (batch, n)).copy()
                    tapes = tapes_for_decisions("evaluation", seed, (n, pair_index, load_index, epoch), batch, n)
                    raw, mapped, idle_scores, decoded_t = _decode(actor, features, demands, roles, tapes["priority_ranks"], tapes["action_uniforms"])
                    decoded = _numpy_decode(decoded_t)
                    base_reward = reward(roles, decoded["actions"], decoded["residual"])
                    x, idle, unmet = coupling_from_actions(decoded["actions"], demands)
                    feasibility = feasibility_residuals(x, idle, unmet, demands)
                    rank_order = np.argsort(tapes["priority_ranks"], axis=1)
                    step_actions = np.take_along_axis(decoded["actions"], rank_order, axis=1)

                    replay = replay_permutations(seed, (n, pair_index, load_index, epoch), batch, n)
                    replay_roles = np.take_along_axis(roles, replay["row_permutations"], axis=1)
                    replay_priorities = np.take_along_axis(tapes["priority_ranks"], replay["row_permutations"], axis=1)
                    presented_demands = np.take_along_axis(demands, replay["task_permutations"], axis=1)
                    replay_demands = canonicalize_task_values(presented_demands, replay["task_permutations"])
                    replay_features = _feature(n, replay_demands, epoch)
                    _, _, _, replay_decoded_t = _decode(actor, replay_features, replay_demands, replay_roles, replay_priorities, tapes["action_uniforms"])
                    replay_decoded = _numpy_decode(replay_decoded_t)
                    replay_reward = reward(replay_roles, replay_decoded["actions"], replay_decoded["residual"])
                    replay_x, replay_idle, replay_unmet = coupling_from_actions(replay_decoded["actions"], replay_demands)
                    replay_feasibility = feasibility_residuals(replay_x, replay_idle, replay_unmet, replay_demands)
                    restored_actions = np.empty_like(replay_decoded["actions"])
                    np.put_along_axis(restored_actions, replay["row_permutations"], replay_decoded["actions"], axis=1)
                    # Exercise presentation-order output columns explicitly, then
                    # inverse both row and task presentation for the semantic check.
                    task_index = np.broadcast_to(replay["task_permutations"][:, None, :], replay_x.shape)
                    replay_x_presented = np.take_along_axis(replay_x, task_index, axis=2)
                    replay_unmet_presented = np.take_along_axis(replay_unmet, replay["task_permutations"], axis=1)
                    restored_rows = np.empty_like(replay_x_presented)
                    row_index_3d = np.broadcast_to(replay["row_permutations"][:, :, None], replay_x_presented.shape)
                    np.put_along_axis(restored_rows, row_index_3d, replay_x_presented, axis=1)
                    restored_x = np.empty_like(restored_rows)
                    np.put_along_axis(restored_x, task_index, restored_rows, axis=2)
                    if not np.array_equal(restored_actions, decoded["actions"]):
                        raise RuntimeError("agent/task permutation replay changed semantic action")
                    if not np.array_equal(restored_x, x):
                        raise RuntimeError("task-presentation replay changed semantic coupling")
                    if not np.array_equal(replay_reward, base_reward):
                        raise RuntimeError("permutation replay changed reward")
                    if np.any(feasibility) or np.any(replay_feasibility):
                        raise RuntimeError("decoder emitted infeasible action")

                    scalar = lambda value, dtype: np.full(batch, value, dtype=dtype)
                    tape_ids = np.arange(batch, dtype=np.int16)
                    parts["arm"].append(scalar(arm_code, np.int8))
                    parts["binding"].append(scalar(binding_code, np.int8))
                    parts["phase"].append(scalar(3, np.int8))
                    parts["training_seed"].append(scalar(seed, np.int32))
                    parts["tape_address"].append(np.arange(address_key, address_key + batch, dtype=np.int32))
                    address_key += batch
                    parts["N"].append(scalar(n, np.int8))
                    parts["ordered_pair"].append(np.broadcast_to(np.asarray(pair, dtype=np.int8), (batch, 2)).copy())
                    parts["ordered_pair_index"].append(scalar(pair_index, np.int8))
                    parts["load_flag"].append(scalar(load_index, np.int8))
                    parts["epoch"].append(scalar(epoch, np.int8))
                    parts["tape"].append(tape_ids)
                    parts["agent_records"].append(_pad(_agent_records(roles), (MAX_N, 3)))
                    parts["task_records"].append(_task_records(demands, displayed))
                    parts["raw_supply"].append(scalar(n, np.int8))
                    parts["raw_demand"].append(demands)
                    parts["displayed_coordinates"].append(np.broadcast_to(displayed, (batch, 4)).copy())
                    parts["true_utility_table_key"].append(scalar(0, np.int8))
                    parts["priority_ranks"].append(_pad(tapes["priority_ranks"], (MAX_N,), -1))
                    parts["action_uniforms"].append(_pad(tapes["action_uniforms"], (MAX_N,), np.nan))
                    parts["row_permutation"].append(_pad(np.broadcast_to(np.arange(n, dtype=np.int16), (batch, n)).copy(), (MAX_N,), -1))
                    parts["task_permutation"].append(np.broadcast_to(np.arange(4, dtype=np.int16), (batch, 4)).copy())
                    parts["replay_row_permutation"].append(_pad(replay["row_permutations"], (MAX_N,), -1))
                    parts["replay_task_permutation"].append(replay["task_permutations"])
                    parts["feature_vector"].append(features)
                    map_key = binding_code if arm_code == 0 else 2
                    parts["edge_map_key"].append(scalar(map_key, np.int8))
                    parts["raw_edge_scores"].append(raw)
                    parts["expanded_Nx4_logits"].append(_pad(decoded["expanded_logits"], (MAX_N, 4), np.nan))
                    parts["idle_logits"].append(_pad(decoded["idle_logits"], (MAX_N,), np.nan))
                    parts["step_masks"].append(_pad(decoded["masks"].astype(np.int8), (MAX_N, 5), -1))
                    parts["categorical_probabilities"].append(_pad(decoded["probabilities"], (MAX_N, 5), np.nan))
                    parts["sampled_step_actions"].append(_pad(step_actions, (MAX_N,), -1))
                    parts["coupling_X"].append(_pad(x, (MAX_N, 4)))
                    parts["idle_iota"].append(_pad(idle, (MAX_N,)))
                    parts["unmet_mu"].append(unmet)
                    parts["feasibility_residuals"].append(_pad(feasibility, (MAX_N + 4,)))
                    parts["reward"].append(base_reward)
                    parts["coupling_log_probability"].append(decoded["log_probability"])
                    parts["mean_entropy"].append(decoded["mean_entropy"])
                    panel_key = panel_lookup[(n, pair_index, load_index, epoch)]
                    parts["oracle_panel_key"].append(scalar(panel_key, np.int16))
                    parts["parameter_count"].append(scalar(60, np.int8))
                    parts["feature_ops"].append(scalar(60, np.int16))
                    parts["map_ops"].append(scalar(64, np.int16))
                    parts["edge_evaluations"].append(scalar(4 * n, np.int16))
                    parts["decoder_steps"].append(scalar(n, np.int8))
                    parts["softmax_categories"].append(scalar(5 * n, np.int8))
                    parts["input_words"].append(scalar(3 * n + 14, np.int8))
                    parts["output_words"].append(scalar(5 * n + 4, np.int8))
                    parts["messages"].append(scalar(0, np.int8))
                    parts["alignment"].append(alignment(decoded["actions"], roles, pair, n))
                    parts["replay_sampled_actions"].append(_pad(replay_decoded["actions"], (MAX_N,), -1))
                    parts["replay_coupling_X"].append(_pad(replay_x_presented, (MAX_N, 4)))
                    parts["replay_idle_iota"].append(_pad(replay_idle, (MAX_N,)))
                    parts["replay_unmet_mu"].append(replay_unmet_presented)
                    parts["replay_feasibility_residuals"].append(_pad(replay_feasibility, (MAX_N + 4,)))
                    parts["replay_reward"].append(replay_reward)
                    episode_rows.append((len(parts["reward"]) - 1, base_reward, replay_reward))
                # There are exactly two just-appended epoch blocks, with equal batch.
                y = (episode_rows[0][1] + episode_rows[1][1]) / (2.0 * n)
                ry = (episode_rows[0][2] + episode_rows[1][2]) / (2.0 * n)
                parts["normalized_endpoint"].extend([y.copy(), y.copy()])
                parts["replay_normalized_endpoint"].extend([ry.copy(), ry.copy()])
    return {key: np.concatenate(values, axis=0) for key, values in parts.items()}


def combine_fits(fits: list[dict[str, np.ndarray]], parameters: np.ndarray, selected_hyper: np.ndarray) -> dict[str, np.ndarray]:
    keys = fits[0].keys()
    result = {key: np.concatenate([fit[key] for fit in fits], axis=0) for key in keys}
    result["checkpoint_parameters"] = np.asarray(parameters, dtype=np.float64)
    result["selected_hyperparameters"] = np.asarray(selected_hyper, dtype=np.float64)
    return result
