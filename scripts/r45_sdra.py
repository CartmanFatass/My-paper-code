"""Reward-off natural-support credit gate for R45-SDRA.

The source R41B HMASD skill system and the source-exact zero renewal residual
remain frozen.  This module only collects natural KEEP/RENEW rows and trains
cross-fitted action-conditional Q critics plus capacity-matched action-blind
shams.  It never updates the renewal actor or any source parameter.
"""

from __future__ import annotations

import copy
import math
from types import MethodType
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from r43_native_renewal import (
    ContextHead,
    KEEP,
    RENEW,
    R43_TREATMENT,
    _available_actions,
    _binary_and_conditional,
    _capture_torch_rng,
    _context_features,
    _enumeration_parity,
    _mask_logits,
    _patch_buffer,
    _patch_treatment_runner,
    _restore_torch_rng,
    _wrap_runtime_clock,
)
from r44_frozen_source_nrc import ZeroHead


EXPERIMENT_ID = "EXP-20260716-r45-sdra-g0"
ROLLOUT_ENVS = 16
OUTER_UPDATES = 100
ENV_STEPS = 160_000
CHECK_ROWS = 3_200
STRUCTURAL_ROWS = 16
NORMAL_ROWS = 3_184
FACTOR_ROWS = 6_368
CRITIC_EPOCHS = 15
CRITIC_MINIBATCH = 256
CRITIC_STEPS_PER_MODEL = 195
CRITIC_MODELS = 4
CRITIC_TOTAL_STEPS = 780
CRITIC_LR = 5e-4
CRITIC_EPS = 1e-5
BOOTSTRAP_REPETITIONS = 10_000
BOOTSTRAP_SEED = 62_045
EVAL_EPISODES = 100


class SDRAQHead(nn.Module):
    """Registered 148 -> 32 GELU -> 2 action-value model."""

    def __init__(self, input_dim: int) -> None:
        super().__init__()
        self.hidden = nn.Linear(input_dim, 32)
        self.output = nn.Linear(32, 2)
        nn.init.orthogonal_(self.hidden.weight, gain=nn.init.calculate_gain("relu"))
        nn.init.zeros_(self.hidden.bias)
        nn.init.zeros_(self.output.weight)
        nn.init.zeros_(self.output.bias)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.output(F.gelu(self.hidden(features)))


def _discounted_block_returns(runner: Any) -> np.ndarray:
    rewards = np.asarray(runner._r43_primitive_rewards, dtype=np.float32)
    expected = int(runner.episode_length)
    if rewards.shape != (expected, runner.n_rollout_threads):
        raise RuntimeError(
            f"R45 primitive reward trace {rewards.shape}, expected "
            f"({expected}, {runner.n_rollout_threads})"
        )
    interval = int(runner.skill_interval)
    if expected % interval != 0:
        raise RuntimeError("R45 controller blocks do not partition the rollout")
    gamma = float(runner.h_buffer.gamma)
    discount = np.power(gamma, np.arange(interval, dtype=np.float32))
    result = np.stack(
        [
            (rewards[start : start + interval] * discount[:, None]).sum(axis=0)
            for start in range(0, expected, interval)
        ],
        axis=0,
    )
    if result.shape != (2, runner.n_rollout_threads):
        raise RuntimeError("R45 first gate requires exactly two 50-step blocks")
    return result


@torch.no_grad()
def _collect_rollout_rows(runner: Any) -> None:
    """Replay each natural high check into exact contexts and propensities."""

    from hmasd.algorithms.utils.util import check

    buffer = runner.h_buffer
    policy = runner.h_policy
    transformer = policy.transformer
    block_returns = _discounted_block_returns(runner)
    num_agents = int(policy.num_agents)
    skill_dim = int(policy.act_dim)
    envs = int(runner.n_rollout_threads)
    if num_agents != 2 or envs != ROLLOUT_ENVS:
        raise RuntimeError("R45 formal collector requires N=2 and 16 envs")

    for block_index in range(buffer.episode_length):
        structural_values = np.asarray(buffer.r43_structural[block_index])
        structural = bool(structural_values.reshape(-1)[0] > 0.5)
        if not np.all(structural_values == float(structural)):
            raise RuntimeError("R45 structural rows diverged inside the env batch")

        cent = check(np.concatenate(buffer.share_obs[block_index])).to(
            **policy.tpdv
        ).reshape(-1, policy.num_agents, policy.share_obs_dim)
        local = check(np.concatenate(buffer.obs[block_index])).to(
            **policy.tpdv
        ).reshape(-1, policy.num_agents, policy.obs_dim)
        source_values, obs_rep = transformer.encoder(cent, local)
        del source_values
        actions = torch.as_tensor(
            buffer.actions[block_index], dtype=torch.long, device=policy.device
        ).reshape(envs, num_agents + 1, 1)
        team_action = actions[:, 0, 0]
        pre_roster = np.asarray(buffer.r43_pre_roster[block_index])
        pre_age = np.asarray(buffer.r43_pre_age[block_index])
        active_np = np.asarray(buffer.r43_active_mask[block_index])
        renew_np = np.asarray(buffer.r43_renew_token[block_index])
        old_logp_np = np.asarray(buffer.r43_renew_old_logp[block_index])
        truth_np = np.asarray(buffer.r43_working_prefix[block_index])
        working = torch.as_tensor(
            pre_roster, dtype=torch.long, device=policy.device
        ).reshape(envs, num_agents).clone()
        working_age = torch.as_tensor(
            pre_age, dtype=torch.float32, device=policy.device
        ).reshape(envs, num_agents).clone()
        active = torch.as_tensor(
            active_np, dtype=torch.float32, device=policy.device
        ).reshape(envs, num_agents)
        truth = torch.as_tensor(
            truth_np, dtype=torch.long, device=policy.device
        ).reshape(envs, num_agents, num_agents)
        available = _available_actions(policy, envs)
        shifted = torch.zeros(
            (envs, num_agents + 1, skill_dim + 1), **transformer.tpdv
        )
        shifted[:, 0, 0] = 1.0
        shifted[:, 1, 1:] = F.one_hot(
            team_action, num_classes=skill_dim
        ).to(shifted.dtype)

        runner.r45_collection_stats["env_check_rows"] += envs
        if structural:
            runner.r45_collection_stats["structural_rows"] += envs
        else:
            runner.r45_collection_stats["normal_rows"] += envs

        for focal_index in range(num_agents):
            mismatch = int((working != truth[:, focal_index]).sum().item())
            runner.r45_collection_stats["working_prefix_mismatch"] += mismatch
            source_logits = _mask_logits(
                transformer.decoder(shifted, obs_rep)[:, focal_index + 1, :],
                None
                if available is None
                else available[:, focal_index + 1, :],
            )
            features = _context_features(
                transformer,
                obs_rep,
                team_action,
                working,
                working_age,
                focal_index,
                active,
            )
            if int(features.shape[-1]) != int(runner.r45_context_dim):
                raise RuntimeError("R45 context dimension changed during collection")
            selected_skill = actions[:, focal_index + 1, 0]

            if not structural:
                incumbent = working[:, focal_index]
                distribution, _ = _binary_and_conditional(
                    transformer, source_logits, incumbent, features
                )
                selected_renew = torch.as_tensor(
                    renew_np[:, focal_index],
                    dtype=torch.long,
                    device=policy.device,
                )
                replay_logp = distribution.log_prob(selected_renew)
                stored_logp = torch.as_tensor(
                    old_logp_np[:, focal_index],
                    dtype=replay_logp.dtype,
                    device=policy.device,
                )
                replay_error = float((replay_logp - stored_logp).abs().max().item())
                runner.r45_collection_stats["binary_replay_logp_max_error"] = max(
                    runner.r45_collection_stats["binary_replay_logp_max_error"],
                    replay_error,
                )
                propensity = distribution.probs[:, RENEW]
                if not bool(torch.isfinite(propensity).all().item()):
                    raise RuntimeError("R45 propensity was non-finite")
                if bool(((propensity <= 0.0) | (propensity >= 1.0)).any().item()):
                    raise RuntimeError("R45 natural propensity lacks strict support")
                context_cpu = features.detach().cpu().numpy().astype(np.float32)
                propensity_cpu = propensity.detach().cpu().numpy().astype(np.float64)
                action_cpu = selected_renew.detach().cpu().numpy().astype(np.int64)
                check_index = runner.r45_outer_updates * 2 + block_index
                for env_index in range(envs):
                    runner.r45_rows.append(
                        {
                            "context": context_cpu[env_index].copy(),
                            "env_rank": env_index,
                            "update_index": runner.r45_outer_updates,
                            "block_index": block_index,
                            "check_index": check_index,
                            "event_id": check_index * envs + env_index,
                            "agent": focal_index,
                            "action": int(action_cpu[env_index]),
                            "propensity_renew": float(propensity_cpu[env_index]),
                            "outcome": float(block_returns[block_index, env_index]),
                        }
                    )
                runner.r45_collection_stats["factor_rows"] += envs
                selected_renew_for_age = selected_renew
            else:
                selected_renew_for_age = torch.full(
                    (envs,), RENEW, dtype=torch.long, device=policy.device
                )

            working = working.clone()
            working_age = working_age.clone()
            working[:, focal_index] = selected_skill
            working_age[:, focal_index] = torch.where(
                selected_renew_for_age == RENEW,
                torch.zeros_like(working_age[:, focal_index]),
                working_age[:, focal_index],
            )
            if focal_index + 2 < num_agents + 1:
                shifted = shifted.clone()
                shifted[:, focal_index + 2, 1:] = F.one_hot(
                    selected_skill, num_classes=skill_dim
                ).to(shifted.dtype)

        source_error = float(
            np.max(np.abs(buffer.r43_source_equivalence_error[block_index]))
        )
        runner.r45_collection_stats["source_probability_max_error"] = max(
            runner.r45_collection_stats["source_probability_max_error"],
            source_error,
        )


def install_r45_collector(runner: Any) -> dict[str, Any]:
    """Install frozen source-exact natural collection without actor updates."""

    if runner.num_agents != 2 or runner.h_policy.action_type != "Discrete":
        raise RuntimeError("R45 first gate requires N=2 discrete source HMASD")
    if runner.use_linear_lr_decay:
        raise RuntimeError("R45 source optimizers must not receive LR updates")
    policy = runner.h_policy
    transformer = policy.transformer
    if hasattr(transformer, "r43_renewal_actor"):
        raise RuntimeError("renewal overlay is already installed")
    for module in (
        transformer,
        runner.l_policy.actor,
        runner.l_policy.critic,
        runner.discri.team_discri,
        runner.discri.indi_discri,
    ):
        module.requires_grad_(False)

    n_embd = int(transformer.encoder.n_embd)
    input_dim = (
        2 * n_embd
        + policy.act_dim
        + runner.num_agents * policy.act_dim
        + 4 * runner.num_agents
    )
    construction_rng = _capture_torch_rng()
    renewal_actor = ContextHead(input_dim, 2).to(policy.device)
    _restore_torch_rng(construction_rng)
    renewal_actor.requires_grad_(False)
    transformer.add_module("r43_renewal_actor", renewal_actor)
    transformer.add_module("r43_renewal_critic", ZeroHead().to(policy.device))
    transformer.add_module("r43_skill_event_critic", ZeroHead().to(policy.device))

    parity = _enumeration_parity(runner)
    for field in (
        "maximum_logp_error",
        "maximum_probability_error",
        "maximum_probability_sum_error",
    ):
        value = float(parity[field])
        if not math.isfinite(value) or value > 1e-6:
            raise RuntimeError(f"R45 source-exact parity failed: {parity}")

    source_compute = runner.compute
    _wrap_runtime_clock(runner, R43_TREATMENT, policy.act_dim)
    _patch_buffer(runner.h_buffer, runner.num_agents)
    _patch_treatment_runner(runner, policy.act_dim)
    runner.r45_context_dim = input_dim
    runner.r45_rows: list[dict[str, Any]] = []
    runner.r45_outer_updates = 0
    runner.r45_collection_stats = {
        "env_check_rows": 0,
        "structural_rows": 0,
        "normal_rows": 0,
        "factor_rows": 0,
        "working_prefix_mismatch": 0,
        "binary_replay_logp_max_error": 0.0,
        "source_probability_max_error": 0.0,
    }

    @torch.no_grad()
    def compute(self: Any) -> None:
        _collect_rollout_rows(self)
        self._r43_primitive_rewards.clear()
        self._r43_primitive_dones.clear()
        source_compute()

    def train(self: Any) -> dict[str, float]:
        self.h_buffer.after_update()
        self.l_buffer.after_update()
        self.r45_outer_updates += 1
        return {
            "r45_source_optimizer_steps": 0.0,
            "r45_renewal_actor_steps": 0.0,
        }

    def save(self: Any, episode: int) -> None:
        del episode
        self.r45_collection_stats["suppressed_source_saves"] = (
            self.r45_collection_stats.get("suppressed_source_saves", 0) + 1
        )

    runner.compute = MethodType(compute, runner)
    runner.train = MethodType(train, runner)
    runner.save = MethodType(save, runner)
    return {
        "controller_clock": "source_global_k50_reset_censored",
        "context_input_dim": input_dim,
        "renewal_actor_parameters": sum(
            parameter.numel() for parameter in renewal_actor.parameters()
        ),
        "renewal_actor_trainable": False,
        "renewal_actor_optimizer": False,
        "source_parameters_frozen": True,
        "source_optimizers_enabled": False,
        "zero_residual_source_parity": parity,
        "task_specific_inputs": False,
        "reward_shaping": False,
        "intrinsic_reward_changed": False,
        "forced_branches": False,
    }


def rows_to_arrays(rows: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    if not rows:
        raise RuntimeError("R45 collected no normal renewal rows")
    return {
        "context": np.stack([row["context"] for row in rows]).astype(np.float32),
        "env_rank": np.asarray([row["env_rank"] for row in rows], dtype=np.int64),
        "update_index": np.asarray(
            [row["update_index"] for row in rows], dtype=np.int64
        ),
        "block_index": np.asarray(
            [row["block_index"] for row in rows], dtype=np.int64
        ),
        "check_index": np.asarray(
            [row["check_index"] for row in rows], dtype=np.int64
        ),
        "event_id": np.asarray([row["event_id"] for row in rows], dtype=np.int64),
        "agent": np.asarray([row["agent"] for row in rows], dtype=np.int64),
        "action": np.asarray([row["action"] for row in rows], dtype=np.int64),
        "propensity_renew": np.asarray(
            [row["propensity_renew"] for row in rows], dtype=np.float64
        ),
        "outcome": np.asarray([row["outcome"] for row in rows], dtype=np.float64),
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
    seed: int,
    epochs: int,
    minibatch: int,
) -> tuple[dict[str, Any], dict[str, np.ndarray], dict[str, Any]]:
    input_dim = int(arrays["context"].shape[1])
    mean = arrays["context"][train_indices].mean(axis=0, dtype=np.float64)
    std = arrays["context"][train_indices].std(axis=0, dtype=np.float64)
    std = np.where(std < 1e-6, 1.0, std)

    rng_state = _capture_torch_rng()
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    base = SDRAQHead(input_dim).to(device)
    true_model = copy.deepcopy(base)
    sham_model = copy.deepcopy(base)
    initial_difference = _state_max_difference(
        true_model.state_dict(), sham_model.state_dict()
    )
    del base
    true_optimizer = torch.optim.Adam(
        true_model.parameters(), lr=CRITIC_LR, eps=CRITIC_EPS
    )
    sham_optimizer = torch.optim.Adam(
        sham_model.parameters(), lr=CRITIC_LR, eps=CRITIC_EPS
    )
    schedule_rng = np.random.default_rng(seed + 1_000_003)
    schedules = [schedule_rng.permutation(train_indices) for _ in range(epochs)]
    stats = {
        "true_steps": 0,
        "sham_steps": 0,
        "true_gradient_checks": 0,
        "sham_gradient_checks": 0,
        "true_all_gradients_finite": True,
        "sham_all_gradients_finite": True,
        "true_nonzero_gradient_steps": 0,
        "sham_nonzero_gradient_steps": 0,
        "true_max_gradient_norm": 0.0,
        "sham_max_gradient_norm": 0.0,
        "initial_true_sham_max_difference": initial_difference,
    }

    def batch_tensor(name: str, indices: np.ndarray, dtype: torch.dtype) -> torch.Tensor:
        values = arrays[name][indices]
        if name == "context":
            values = (values.astype(np.float64) - mean) / std
        return torch.as_tensor(values, dtype=dtype, device=device)

    for schedule in schedules:
        for start in range(0, len(schedule), minibatch):
            indices = schedule[start : start + minibatch]
            contexts = batch_tensor("context", indices, torch.float32)
            actions = batch_tensor("action", indices, torch.long)
            outcomes = batch_tensor("outcome", indices, torch.float32)
            propensity = batch_tensor("propensity_renew", indices, torch.float32)

            true_values = true_model(contexts)
            true_prediction = true_values.gather(1, actions[:, None]).squeeze(1)
            true_loss = F.mse_loss(true_prediction, outcomes)
            true_optimizer.zero_grad(set_to_none=True)
            true_loss.backward()
            finite, nonzero, norm = _gradient_stats(true_model)
            stats["true_steps"] += 1
            stats["true_gradient_checks"] += 1
            stats["true_all_gradients_finite"] = bool(
                stats["true_all_gradients_finite"] and finite
            )
            stats["true_nonzero_gradient_steps"] += int(nonzero)
            stats["true_max_gradient_norm"] = max(
                stats["true_max_gradient_norm"], norm
            )
            true_optimizer.step()

            sham_values = sham_model(contexts)
            sham_prediction = (
                (1.0 - propensity) * sham_values[:, KEEP]
                + propensity * sham_values[:, RENEW]
            )
            sham_loss = F.mse_loss(sham_prediction, outcomes)
            sham_optimizer.zero_grad(set_to_none=True)
            sham_loss.backward()
            finite, nonzero, norm = _gradient_stats(sham_model)
            stats["sham_steps"] += 1
            stats["sham_gradient_checks"] += 1
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
        heldout_tensor = torch.as_tensor(
            heldout_context, dtype=torch.float32, device=device
        )
        true_q = true_model(heldout_tensor).cpu().numpy().astype(np.float64)
        sham_q = sham_model(heldout_tensor).cpu().numpy().astype(np.float64)
    states = {
        "true": {name: value.detach().cpu() for name, value in true_model.state_dict().items()},
        "sham": {name: value.detach().cpu() for name, value in sham_model.state_dict().items()},
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
        "epochs": int(epochs),
        "minibatch": int(minibatch),
        "drop_last": False,
        "parameter_count": sum(parameter.numel() for parameter in true_model.parameters()),
        "architecture": f"{input_dim}->32_GELU->2",
        "optimizer": "Adam",
        "learning_rate": CRITIC_LR,
        "eps": CRITIC_EPS,
        "normalization_fit_rows": int(len(train_indices)),
        "normalization_zero_variance_features": int((std == 1.0).sum()),
    }
    _restore_torch_rng(rng_state)
    return states, predictions, metadata


def train_crossfit_critics(
    arrays: dict[str, np.ndarray],
    device: torch.device,
    seed: int,
    epochs: int = CRITIC_EPOCHS,
    minibatch: int = CRITIC_MINIBATCH,
) -> tuple[dict[str, Any], dict[str, np.ndarray], dict[str, Any]]:
    """Train fold-A/B true-Q and action-blind sham models exactly once."""

    env_rank = arrays["env_rank"]
    fold_a = env_rank <= 7
    fold_b = env_rank >= 8
    if bool((fold_a & fold_b).any()) or not bool((fold_a | fold_b).all()):
        raise RuntimeError("R45 env-rank folds are invalid")
    predictions = {
        "true_q": np.full((len(env_rank), 2), np.nan, dtype=np.float64),
        "sham_q": np.full((len(env_rank), 2), np.nan, dtype=np.float64),
        "trained_on_fold": np.full(len(env_rank), -1, dtype=np.int64),
    }
    checkpoint: dict[str, Any] = {"schema": "r45_sdra_critics_v1", "folds": {}}
    metadata: dict[str, Any] = {"folds": {}}
    for fold_index, (label, train_mask, heldout_mask) in enumerate(
        (("A", fold_a, fold_b), ("B", fold_b, fold_a))
    ):
        train_indices = np.flatnonzero(train_mask)
        heldout_indices = np.flatnonzero(heldout_mask)
        states, heldout, fold_metadata = _train_fold_pair(
            arrays,
            train_indices,
            heldout_indices,
            device,
            seed + fold_index * 10_000,
            epochs,
            minibatch,
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
    if not bool(np.isfinite(predictions["true_q"]).all()):
        raise RuntimeError("R45 true-Q heldout predictions were non-finite")
    if not bool(np.isfinite(predictions["sham_q"]).all()):
        raise RuntimeError("R45 sham heldout predictions were non-finite")
    if bool((predictions["trained_on_fold"] < 0).any()):
        raise RuntimeError("R45 cross-fitting left rows unscored")
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
