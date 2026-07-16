"""R46-HMRV-G0 heterogeneous-maintenance identifiability gate.

This is a standalone synthetic positive-control substrate.  A fixed balanced
Bernoulli behavior policy generates KEEP/RENEW actions in an N=2 maintenance
process.  No policy, skill, low-level module, or intrinsic reward exists.  The
only learned objects are four cross-fitted action-Q/action-blind-sham critics.
"""

from __future__ import annotations

import copy
import math
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


EXPERIMENT_ID = "EXP-20260716-r46-hmrv-g0"
KEEP = 0
RENEW = 1
N_AGENTS = 2
K0 = 5
HORIZON = 40
CHECKS_PER_EPISODE = 8
USABLE_CHECKS = 6
ROLLOUT_ENVS = 16
EPISODES_PER_ENV = 100
ENVIRONMENT_SEED = 46_041
BEHAVIOR_ACTION_SEED = 46_041
EVAL_ACTION_SEED = 56_041
GAMMA = 0.99
ENV_STEPS = 64_000
TOTAL_CHECK_ROWS = 12_800
USABLE_EVENT_ROWS = 9_600
FOCAL_ROWS = 19_200
CRITIC_EPOCHS = 15
CRITIC_MINIBATCH = 256
CRITIC_STEPS_PER_MODEL = 570
CRITIC_MODELS = 4
CRITIC_TOTAL_STEPS = 2_280
CRITIC_LR = 5e-4
CRITIC_EPS = 1e-5
BOOTSTRAP_REPETITIONS = 10_000
BOOTSTRAP_SEED = 62_046
EVAL_EPISODES = 100


class HMRVQHead(nn.Module):
    """Registered 6 -> 32 GELU -> 2 critic."""

    def __init__(self) -> None:
        super().__init__()
        self.hidden = nn.Linear(6, 32)
        self.output = nn.Linear(32, 2)
        nn.init.orthogonal_(self.hidden.weight, gain=nn.init.calculate_gain("relu"))
        nn.init.zeros_(self.hidden.bias)
        nn.init.zeros_(self.output.weight)
        nn.init.zeros_(self.output.bias)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.output(F.gelu(self.hidden(features)))


def role_assignment(episode_index: int) -> np.ndarray:
    """Return the registered balanced degradation-rate assignment."""

    if episode_index % 2 == 0:
        return np.asarray([1, 2], dtype=np.int64)
    return np.asarray([2, 1], dtype=np.int64)


def behavior_schedule() -> np.ndarray:
    """Generate the complete formal Bernoulli-0.5 behavior schedule once."""

    rng = np.random.default_rng(BEHAVIOR_ACTION_SEED)
    return rng.integers(
        0,
        2,
        size=(ROLLOUT_ENVS, EPISODES_PER_ENV, CHECKS_PER_EPISODE, N_AGENTS),
        dtype=np.int64,
    )


def evaluation_schedule() -> tuple[np.ndarray, np.ndarray]:
    """Generate the registered paired M0 trace schedule."""

    assignments = np.stack(
        [role_assignment(episode) for episode in range(EVAL_EPISODES)]
    )
    rng = np.random.default_rng(EVAL_ACTION_SEED)
    actions = rng.integers(
        0,
        2,
        size=(EVAL_EPISODES, CHECKS_PER_EPISODE, N_AGENTS),
        dtype=np.int64,
    )
    return assignments, actions


def simulate_episode(actions: np.ndarray, degradation: np.ndarray) -> dict[str, np.ndarray]:
    """Execute one exact 40-step HMRV episode from health (4, 4)."""

    actions = np.asarray(actions, dtype=np.int64)
    degradation = np.asarray(degradation, dtype=np.int64)
    if actions.shape != (CHECKS_PER_EPISODE, N_AGENTS):
        raise ValueError(f"invalid action schedule shape {actions.shape}")
    if degradation.shape != (N_AGENTS,):
        raise ValueError(f"invalid degradation shape {degradation.shape}")
    if not np.isin(actions, [KEEP, RENEW]).all():
        raise ValueError("HMRV action must be KEEP=0 or RENEW=1")
    if sorted(degradation.tolist()) != [1, 2]:
        raise ValueError("HMRV degradation assignment must be a permutation of (1, 2)")

    pre_health = np.empty((CHECKS_PER_EPISODE, N_AGENTS), dtype=np.int64)
    post_health = np.empty_like(pre_health)
    service_output = np.empty((CHECKS_PER_EPISODE, N_AGENTS), dtype=np.float64)
    block_reward = np.empty(CHECKS_PER_EPISODE, dtype=np.float64)
    health = np.asarray([4, 4], dtype=np.int64)

    for check in range(CHECKS_PER_EPISODE):
        pre_health[check] = health
        keep = actions[check] == KEEP
        service = np.where(keep, health.astype(np.float64) / 4.0, 0.0)
        next_health = np.where(keep, np.maximum(0, health - degradation), 4)
        service_output[check] = service
        post_health[check] = next_health
        block_reward[check] = min(1.0, float(service.sum()))
        health = next_health.astype(np.int64, copy=False)

    primitive_reward = np.repeat(block_reward, K0)
    if primitive_reward.shape != (HORIZON,):
        raise RuntimeError("HMRV block rewards did not produce a 40-step trace")
    return {
        "actions": actions.copy(),
        "degradation": degradation.copy(),
        "pre_health": pre_health,
        "post_health": post_health,
        "service_output": service_output,
        "block_reward": block_reward,
        "primitive_reward": primitive_reward,
    }


def three_block_outcomes(block_reward: np.ndarray) -> np.ndarray:
    """Return the registered current-plus-next-two-block discounted outcome."""

    primitive_reward = np.repeat(np.asarray(block_reward, dtype=np.float64), K0)
    discount = np.power(GAMMA, np.arange(3 * K0, dtype=np.float64))
    return np.asarray(
        [
            float(
                np.dot(
                    discount,
                    primitive_reward[check * K0 : (check + 3) * K0],
                )
            )
            for check in range(USABLE_CHECKS)
        ],
        dtype=np.float64,
    )


def collect_formal_data() -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Collect all 64K deterministic-environment steps under natural support."""

    actions = behavior_schedule()
    pre_health = np.empty(
        (ROLLOUT_ENVS, EPISODES_PER_ENV, CHECKS_PER_EPISODE, N_AGENTS),
        dtype=np.int64,
    )
    post_health = np.empty_like(pre_health)
    service_output = np.empty(pre_health.shape, dtype=np.float64)
    block_reward = np.empty(
        (ROLLOUT_ENVS, EPISODES_PER_ENV, CHECKS_PER_EPISODE),
        dtype=np.float64,
    )
    degradation = np.empty(
        (ROLLOUT_ENVS, EPISODES_PER_ENV, N_AGENTS), dtype=np.int64
    )

    contexts: list[np.ndarray] = []
    env_ranks: list[int] = []
    episode_indices: list[int] = []
    check_indices: list[int] = []
    event_ids: list[int] = []
    cluster_ids: list[int] = []
    agents: list[int] = []
    focal_actions: list[int] = []
    outcomes: list[float] = []
    role_d0: list[int] = []
    role_d1: list[int] = []

    for env_rank in range(ROLLOUT_ENVS):
        for episode in range(EPISODES_PER_ENV):
            rates = role_assignment(episode)
            trace = simulate_episode(actions[env_rank, episode], rates)
            pre_health[env_rank, episode] = trace["pre_health"]
            post_health[env_rank, episode] = trace["post_health"]
            service_output[env_rank, episode] = trace["service_output"]
            block_reward[env_rank, episode] = trace["block_reward"]
            degradation[env_rank, episode] = rates
            registered_outcome = three_block_outcomes(trace["block_reward"])
            cluster_id = env_rank * EPISODES_PER_ENV + episode
            for check in range(USABLE_CHECKS):
                event_id = cluster_id * USABLE_CHECKS + check
                for focal in range(N_AGENTS):
                    other = 1 - focal
                    if focal == 0:
                        prefix_valid = 0.0
                        prefix_action = 0.0
                    else:
                        prefix_valid = 1.0
                        prefix_action = float(actions[env_rank, episode, check, 0])
                    contexts.append(
                        np.asarray(
                            [
                                trace["pre_health"][check, focal] / 4.0,
                                trace["pre_health"][check, other] / 4.0,
                                rates[focal] / 2.0,
                                rates[other] / 2.0,
                                prefix_valid,
                                prefix_action,
                            ],
                            dtype=np.float32,
                        )
                    )
                    env_ranks.append(env_rank)
                    episode_indices.append(episode)
                    check_indices.append(check)
                    event_ids.append(event_id)
                    cluster_ids.append(cluster_id)
                    agents.append(focal)
                    focal_actions.append(int(actions[env_rank, episode, check, focal]))
                    outcomes.append(float(registered_outcome[check]))
                    role_d0.append(int(rates[0]))
                    role_d1.append(int(rates[1]))

    rows = {
        "context": np.stack(contexts).astype(np.float32),
        "env_rank": np.asarray(env_ranks, dtype=np.int64),
        "episode_index": np.asarray(episode_indices, dtype=np.int64),
        "check_index": np.asarray(check_indices, dtype=np.int64),
        "event_id": np.asarray(event_ids, dtype=np.int64),
        "cluster_id": np.asarray(cluster_ids, dtype=np.int64),
        "agent": np.asarray(agents, dtype=np.int64),
        "action": np.asarray(focal_actions, dtype=np.int64),
        "propensity_renew": np.full(FOCAL_ROWS, 0.5, dtype=np.float64),
        "outcome": np.asarray(outcomes, dtype=np.float64),
        "role_d0": np.asarray(role_d0, dtype=np.int64),
        "role_d1": np.asarray(role_d1, dtype=np.int64),
    }
    traces = {
        "behavior_actions": actions,
        "degradation": degradation,
        "pre_health": pre_health,
        "post_health": post_health,
        "service_output": service_output,
        "block_reward": block_reward,
    }
    if rows["context"].shape != (FOCAL_ROWS, 6):
        raise RuntimeError(f"R46 row shape mismatch: {rows['context'].shape}")
    return rows, traces


def run_evaluation_trace(
    assignments: np.ndarray, actions: np.ndarray
) -> dict[str, np.ndarray]:
    """Run the fixed 100-episode schedule used only for M0 trace equality."""

    if assignments.shape != (EVAL_EPISODES, N_AGENTS):
        raise ValueError("R46 evaluation role schedule shape mismatch")
    if actions.shape != (EVAL_EPISODES, CHECKS_PER_EPISODE, N_AGENTS):
        raise ValueError("R46 evaluation action schedule shape mismatch")
    pre = np.empty((EVAL_EPISODES, CHECKS_PER_EPISODE, N_AGENTS), dtype=np.int64)
    post = np.empty_like(pre)
    service = np.empty(pre.shape, dtype=np.float64)
    reward = np.empty((EVAL_EPISODES, CHECKS_PER_EPISODE), dtype=np.float64)
    for episode in range(EVAL_EPISODES):
        trace = simulate_episode(actions[episode], assignments[episode])
        pre[episode] = trace["pre_health"]
        post[episode] = trace["post_health"]
        service[episode] = trace["service_output"]
        reward[episode] = trace["block_reward"]
    return {
        "role_assignments": assignments.copy(),
        "actions": actions.copy(),
        "pre_health": pre,
        "post_health": post,
        "service_output": service,
        "block_reward": reward,
    }


def _state_max_difference(
    left: dict[str, torch.Tensor], right: dict[str, torch.Tensor]
) -> float:
    return max(
        (
            float((left[name].detach().cpu() - right[name].detach().cpu()).abs().max())
            for name in left
        ),
        default=0.0,
    )


def _gradient_stats(model: nn.Module) -> tuple[bool, bool, float]:
    gradients = [
        parameter.grad.detach()
        for parameter in model.parameters()
        if parameter.grad is not None
    ]
    if not gradients:
        return False, False, 0.0
    finite = all(bool(torch.isfinite(value).all().item()) for value in gradients)
    norm = math.sqrt(
        sum(float(value.float().pow(2).sum().item()) for value in gradients)
    )
    return finite, math.isfinite(norm) and norm > 0.0, norm


def _train_fold_pair(
    arrays: dict[str, np.ndarray],
    train_indices: np.ndarray,
    heldout_indices: np.ndarray,
    device: torch.device,
    model_seed: int,
    shuffle_seed: int,
) -> tuple[dict[str, Any], dict[str, np.ndarray], dict[str, Any]]:
    mean = arrays["context"][train_indices].mean(axis=0, dtype=np.float64)
    std = arrays["context"][train_indices].std(axis=0, dtype=np.float64)
    std = np.where(std < 1e-6, 1.0, std)

    torch.manual_seed(model_seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(model_seed)
    base = HMRVQHead().to(device)
    true_model = copy.deepcopy(base)
    sham_model = copy.deepcopy(base)
    initial_difference = _state_max_difference(
        true_model.state_dict(), sham_model.state_dict()
    )
    del base
    true_optimizer = torch.optim.Adam(
        true_model.parameters(),
        lr=CRITIC_LR,
        eps=CRITIC_EPS,
        betas=(0.9, 0.999),
        weight_decay=0.0,
        amsgrad=False,
    )
    sham_optimizer = torch.optim.Adam(
        sham_model.parameters(),
        lr=CRITIC_LR,
        eps=CRITIC_EPS,
        betas=(0.9, 0.999),
        weight_decay=0.0,
        amsgrad=False,
    )
    schedule_rng = np.random.default_rng(shuffle_seed)
    schedules = [
        schedule_rng.permutation(train_indices) for _ in range(CRITIC_EPOCHS)
    ]
    stats: dict[str, Any] = {
        "true_steps": 0,
        "sham_steps": 0,
        "true_all_gradients_finite": True,
        "sham_all_gradients_finite": True,
        "true_nonzero_gradient_steps": 0,
        "sham_nonzero_gradient_steps": 0,
        "true_max_gradient_norm": 0.0,
        "sham_max_gradient_norm": 0.0,
        "initial_true_sham_max_difference": initial_difference,
    }

    def tensor(name: str, indices: np.ndarray, dtype: torch.dtype) -> torch.Tensor:
        values = arrays[name][indices]
        if name == "context":
            values = (values.astype(np.float64) - mean) / std
        return torch.as_tensor(values, dtype=dtype, device=device)

    for schedule in schedules:
        for start in range(0, len(schedule), CRITIC_MINIBATCH):
            indices = schedule[start : start + CRITIC_MINIBATCH]
            context = tensor("context", indices, torch.float32)
            action = tensor("action", indices, torch.long)
            outcome = tensor("outcome", indices, torch.float32)
            propensity = tensor("propensity_renew", indices, torch.float32)

            true_prediction = true_model(context).gather(1, action[:, None]).squeeze(1)
            true_loss = F.mse_loss(true_prediction, outcome)
            true_optimizer.zero_grad(set_to_none=True)
            true_loss.backward()
            finite, nonzero, norm = _gradient_stats(true_model)
            stats["true_steps"] += 1
            stats["true_all_gradients_finite"] = bool(
                stats["true_all_gradients_finite"] and finite
            )
            stats["true_nonzero_gradient_steps"] += int(nonzero)
            stats["true_max_gradient_norm"] = max(
                stats["true_max_gradient_norm"], norm
            )
            true_optimizer.step()

            sham_values = sham_model(context)
            sham_prediction = (
                (1.0 - propensity) * sham_values[:, KEEP]
                + propensity * sham_values[:, RENEW]
            )
            sham_loss = F.mse_loss(sham_prediction, outcome)
            sham_optimizer.zero_grad(set_to_none=True)
            sham_loss.backward()
            finite, nonzero, norm = _gradient_stats(sham_model)
            stats["sham_steps"] += 1
            stats["sham_all_gradients_finite"] = bool(
                stats["sham_all_gradients_finite"] and finite
            )
            stats["sham_nonzero_gradient_steps"] += int(nonzero)
            stats["sham_max_gradient_norm"] = max(
                stats["sham_max_gradient_norm"], norm
            )
            sham_optimizer.step()

    with torch.no_grad():
        heldout_context = (
            arrays["context"][heldout_indices].astype(np.float64) - mean
        ) / std
        heldout = torch.as_tensor(heldout_context, dtype=torch.float32, device=device)
        true_q = true_model(heldout).cpu().numpy().astype(np.float64)
        sham_q = sham_model(heldout).cpu().numpy().astype(np.float64)
    states = {
        "true": {
            name: value.detach().cpu()
            for name, value in true_model.state_dict().items()
        },
        "sham": {
            name: value.detach().cpu()
            for name, value in sham_model.state_dict().items()
        },
        "normalization_mean": torch.as_tensor(mean, dtype=torch.float64),
        "normalization_std": torch.as_tensor(std, dtype=torch.float64),
    }
    predictions = {
        "indices": heldout_indices.copy(),
        "true_q": true_q,
        "sham_q": sham_q,
    }
    metadata = {
        **stats,
        "train_rows": int(len(train_indices)),
        "heldout_rows": int(len(heldout_indices)),
        "epochs": CRITIC_EPOCHS,
        "minibatch": CRITIC_MINIBATCH,
        "drop_last": False,
        "parameter_count": sum(p.numel() for p in true_model.parameters()),
        "architecture": "6->32_GELU->2",
        "optimizer": "Adam",
        "learning_rate": CRITIC_LR,
        "eps": CRITIC_EPS,
        "betas": [0.9, 0.999],
        "weight_decay": 0.0,
        "amsgrad": False,
        "model_init_seed": model_seed,
        "shuffle_seed": shuffle_seed,
        "normalization_fit_rows": int(len(train_indices)),
    }
    return states, predictions, metadata


def train_crossfit_critics(
    arrays: dict[str, np.ndarray], device: torch.device
) -> tuple[dict[str, Any], dict[str, np.ndarray], dict[str, Any]]:
    """Train exactly four registered critics and return held-out predictions."""

    env_rank = arrays["env_rank"]
    fold_a = env_rank <= 7
    fold_b = env_rank >= 8
    if bool((fold_a & fold_b).any()) or not bool((fold_a | fold_b).all()):
        raise RuntimeError("R46 environment folds are invalid")
    predictions = {
        "true_q": np.full((len(env_rank), 2), np.nan, dtype=np.float64),
        "sham_q": np.full((len(env_rank), 2), np.nan, dtype=np.float64),
        "trained_on_fold": np.full(len(env_rank), -1, dtype=np.int64),
    }
    checkpoint: dict[str, Any] = {"schema": "r46_hmrv_critics_v1", "folds": {}}
    metadata: dict[str, Any] = {"folds": {}}
    fold_contracts = (
        ("A", fold_a, fold_b, 46_041, 1_046_044),
        ("B", fold_b, fold_a, 56_041, 1_056_044),
    )
    for fold_index, (label, train_mask, heldout_mask, model_seed, shuffle_seed) in enumerate(
        fold_contracts
    ):
        train_indices = np.flatnonzero(train_mask)
        heldout_indices = np.flatnonzero(heldout_mask)
        states, heldout, fold_metadata = _train_fold_pair(
            arrays,
            train_indices,
            heldout_indices,
            device,
            model_seed,
            shuffle_seed,
        )
        predictions["true_q"][heldout["indices"]] = heldout["true_q"]
        predictions["sham_q"][heldout["indices"]] = heldout["sham_q"]
        predictions["trained_on_fold"][heldout["indices"]] = fold_index
        checkpoint["folds"][label] = states
        metadata["folds"][label] = {
            **fold_metadata,
            "train_env_ranks": list(range(0, 8)) if label == "A" else list(range(8, 16)),
            "heldout_env_ranks": list(range(8, 16)) if label == "A" else list(range(0, 8)),
        }
    if not np.isfinite(predictions["true_q"]).all():
        raise RuntimeError("R46 true-Q held-out predictions are non-finite")
    if not np.isfinite(predictions["sham_q"]).all():
        raise RuntimeError("R46 sham held-out predictions are non-finite")
    if (predictions["trained_on_fold"] < 0).any():
        raise RuntimeError("R46 cross-fitting left rows unscored")
    metadata["total_optimizer_steps"] = int(
        sum(
            fold[name]
            for fold in metadata["folds"].values()
            for name in ("true_steps", "sham_steps")
        )
    )
    metadata["all_gradients_finite"] = bool(
        all(
            fold["true_all_gradients_finite"]
            and fold["sham_all_gradients_finite"]
            for fold in metadata["folds"].values()
        )
    )
    return checkpoint, predictions, metadata
