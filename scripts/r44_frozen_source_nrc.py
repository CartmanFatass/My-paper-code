"""Frozen-source native renewal control for the R44-FS-NRC gate.

This overlay deliberately reuses the probability and clock machinery that was
validated in R43 while removing every source-HMASD optimizer update.  The only
trainable behavior parameter in the treatment arm is the renewal residual;
both arms train the same renewal critic with the same independent optimizer.
"""

from __future__ import annotations

import math
from types import MethodType
from typing import Any

import numpy as np
import torch
import torch.nn as nn

from r43_native_renewal import (
    ContextHead,
    R43_TREATMENT,
    _capture_torch_rng,
    _custom_value_loss,
    _denormalize_values,
    _enumeration_parity,
    _masked_normalize,
    _patch_buffer,
    _patch_treatment_runner,
    _restore_torch_rng,
    _wrap_runtime_clock,
    boundary_critic_values,
    evaluate_r43_factors,
)


R44_CONTROL = "frozen_source_nrc0"
R44_TREATMENT = "frozen_source_nrc"
R44_MODES = (R44_CONTROL, R44_TREATMENT)


class ZeroHead(nn.Module):
    """Parameter-free compatibility head for the retired skill-event critic."""

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return features.new_zeros((features.shape[0], 1))


def _compute_r44_credit(runner: Any) -> None:
    """Compute only the registered reset-censored renewal return and GAE."""

    rewards = np.asarray(runner._r43_primitive_rewards, dtype=np.float32)
    dones = np.asarray(runner._r43_primitive_dones, dtype=bool)
    expected = int(runner.episode_length)
    if rewards.shape != (expected, runner.n_rollout_threads):
        raise RuntimeError(
            f"R44 primitive reward trace {rewards.shape}, expected "
            f"({expected}, {runner.n_rollout_threads})"
        )
    if dones.shape != rewards.shape:
        raise RuntimeError("R44 primitive done trace shape mismatch")

    interval = int(runner.skill_interval)
    gamma = float(runner.h_buffer.gamma)
    gae_lambda = float(runner.h_buffer.gae_lambda)
    discount = np.power(gamma, np.arange(interval, dtype=np.float32))
    block_returns = np.stack(
        [
            (rewards[start : start + interval] * discount[:, None]).sum(axis=0)
            for start in range(0, expected, interval)
        ],
        axis=0,
    )
    if block_returns.shape[0] != 2:
        raise RuntimeError("R44 first gate requires exactly two controller blocks")

    runner.h_trainer.prep_rollout()
    boundary_renewal, _ = boundary_critic_values(
        runner.h_policy,
        np.concatenate(runner.h_buffer.share_obs[-1]),
        np.concatenate(runner.h_buffer.obs[-1]),
        runner._r43_current_team,
        runner._r43_current_roster,
        runner._r43_age,
        np.ones_like(runner._r43_age, dtype=np.float32),
    )
    buffer = runner.h_buffer
    renewal_values = _denormalize_values(
        runner.h_trainer, buffer.r43_renew_value
    )
    boundary_values = _denormalize_values(
        runner.h_trainer, boundary_renewal.detach().cpu().numpy()
    )
    repeated_rewards = np.repeat(
        block_returns[:, :, None], runner.num_agents, axis=2
    )
    controller_gamma = gamma**interval

    delta_last = (
        repeated_rewards[1]
        + controller_gamma * boundary_values
        - renewal_values[1]
    )
    advantage_last = delta_last
    delta_first = (
        repeated_rewards[0]
        + controller_gamma * renewal_values[1]
        - renewal_values[0]
    )
    advantage_first = (
        delta_first
        + controller_gamma * gae_lambda * advantage_last
    )
    buffer.r43_renew_advantages[0] = advantage_first
    buffer.r43_renew_advantages[1] = advantage_last
    buffer.r43_renew_returns[:] = (
        buffer.r43_renew_advantages + renewal_values
    )
    buffer.r43_policy_truncated[1] = 1.0

    rows = runner.n_rollout_threads * runner.num_agents
    runner.r43_clock_ledger["update_policy_truncations"] += rows
    runner.r43_clock_ledger["continuation_critic_only_states"] += rows
    for start in (0, interval):
        block_done = dones[start : start + interval]
        for env_index in range(runner.n_rollout_threads):
            offsets = np.flatnonzero(block_done[:, env_index])
            if offsets.size and int(offsets[0]) < interval - 1:
                runner.r43_clock_ledger["early_reset_blocks"] += 1
                first = int(offsets[0])
                if rewards[start + first, env_index] != 0.0:
                    runner.r43_clock_ledger["early_reset_reward_blocks"] += 1
                runner.r43_clock_ledger["post_reset_steps_in_same_block"] += (
                    interval - first - 1
                )
    runner._r43_primitive_rewards.clear()
    runner._r43_primitive_dones.clear()


def _factor_arrays(buffer: Any) -> dict[str, np.ndarray]:
    total_rows = buffer.episode_length * buffer.n_rollout_threads
    renewal_advantage = _masked_normalize(
        buffer.r43_renew_advantages,
        buffer.r43_renew_valid,
    )
    return {
        "share_obs": buffer.share_obs[:-1].reshape(
            total_rows, *buffer.share_obs.shape[2:]
        ),
        "obs": buffer.obs[:-1].reshape(total_rows, *buffer.obs.shape[2:]),
        "actions": buffer.actions.reshape(total_rows, *buffer.actions.shape[2:]),
        "pre_roster": buffer.r43_pre_roster.reshape(
            total_rows, buffer.num_agents
        ),
        "pre_age": buffer.r43_pre_age.reshape(total_rows, buffer.num_agents),
        "active": buffer.r43_active_mask.reshape(total_rows, buffer.num_agents),
        "renew": buffer.r43_renew_token.reshape(total_rows, buffer.num_agents),
        "renew_valid": buffer.r43_renew_valid.reshape(
            total_rows, buffer.num_agents
        ),
        "renew_old_logp": buffer.r43_renew_old_logp.reshape(
            total_rows, buffer.num_agents
        ),
        "renew_value": buffer.r43_renew_value.reshape(
            total_rows, buffer.num_agents
        ),
        "renew_returns": buffer.r43_renew_returns.reshape(
            total_rows, buffer.num_agents
        ),
        "renew_advantage": renewal_advantage.reshape(
            total_rows, buffer.num_agents
        ),
        "skill_valid": buffer.r43_skill_valid.reshape(
            total_rows, buffer.num_agents
        ),
        "prefix": buffer.r43_working_prefix.reshape(
            total_rows, buffer.num_agents, buffer.num_agents
        ),
    }


def _gradient_measure(module: nn.Module) -> tuple[bool, bool, float]:
    gradients = [
        parameter.grad.detach()
        for parameter in module.parameters()
        if parameter.grad is not None
    ]
    if not gradients:
        return False, False, 0.0
    finite = all(bool(torch.isfinite(gradient).all().item()) for gradient in gradients)
    norm_sq = sum(float(gradient.float().pow(2).sum().item()) for gradient in gradients)
    norm = math.sqrt(norm_sq)
    return finite, math.isfinite(norm) and norm > 0.0, norm


def _factor_train(runner: Any) -> dict[str, float]:
    trainer = runner.h_trainer
    buffer = runner.h_buffer
    transformer = runner.h_policy.transformer
    transformer.eval()
    arrays = _factor_arrays(buffer)
    total_rows = buffer.episode_length * buffer.n_rollout_threads
    actor_enabled = runner.r44_mode == R44_TREATMENT
    parameters = [
        parameter
        for module in (transformer.r43_renewal_actor, transformer.r43_renewal_critic)
        for parameter in module.parameters()
        if parameter.requires_grad
    ]
    totals = {
        "h_value_loss": 0.0,
        "h_policy_loss": 0.0,
        "h_dist_entropy": 0.0,
        "h_actor_grad_norm": 0.0,
        "h_critic_grad_norm": 0.0,
        "h_ratio": 0.0,
        "r44_renew_value_loss": 0.0,
        "r44_renew_actor_mask": float(actor_enabled),
    }

    def tensor(name: str, indices: np.ndarray) -> torch.Tensor:
        return torch.as_tensor(
            arrays[name][indices], dtype=torch.float32, device=trainer.device
        )

    for _ in range(int(trainer.ppo_epoch)):
        indices = torch.randperm(total_rows).cpu().numpy()
        evaluated = evaluate_r43_factors(
            runner.h_policy,
            arrays["share_obs"][indices].reshape(
                -1, *arrays["share_obs"].shape[2:]
            ),
            arrays["obs"][indices].reshape(-1, *arrays["obs"].shape[2:]),
            arrays["actions"][indices],
            arrays["pre_roster"][indices],
            arrays["pre_age"][indices],
            arrays["active"][indices],
            arrays["renew"][indices],
            arrays["renew_valid"][indices],
            arrays["skill_valid"][indices],
            arrays["prefix"][indices],
        )
        mismatch = int(evaluated["prefix_mismatch"].item())
        stats = runner.r44_factor_gradient_stats
        stats["maximum_prefix_mismatch"] = max(
            stats["maximum_prefix_mismatch"], mismatch
        )
        if mismatch:
            raise RuntimeError("R44 teacher-forced working prefix mismatch")

        renew_mask = tensor("renew_valid", indices)
        renew_ratio = torch.exp(
            evaluated["renew_logp"] - tensor("renew_old_logp", indices)
        )
        target = tensor("renew_advantage", indices)
        objective = torch.minimum(
            renew_ratio * target,
            renew_ratio.clamp(1.0 - trainer.clip_param, 1.0 + trainer.clip_param)
            * target,
        ) * renew_mask
        policy_loss = -objective.sum() / renew_mask.sum().clamp_min(1.0)
        value_loss = _custom_value_loss(
            trainer,
            evaluated["renew_value"],
            tensor("renew_value", indices),
            tensor("renew_returns", indices),
        )
        loss = value_loss * trainer.value_loss_coef
        if actor_enabled:
            loss = loss + policy_loss

        runner.r44_factor_optimizer.zero_grad(set_to_none=True)
        loss.backward()
        actor_finite, actor_nonzero, actor_norm = _gradient_measure(
            transformer.r43_renewal_actor
        )
        critic_finite, critic_nonzero, critic_norm = _gradient_measure(
            transformer.r43_renewal_critic
        )
        stats["steps"] += 1
        stats["actor_gradient_checks"] += 1
        stats["critic_gradient_checks"] += 1
        stats["actor_all_gradients_finite"] = bool(
            stats["actor_all_gradients_finite"] and (actor_finite if actor_enabled else True)
        )
        stats["critic_all_gradients_finite"] = bool(
            stats["critic_all_gradients_finite"] and critic_finite
        )
        stats["actor_nonzero_steps"] += int(actor_nonzero)
        stats["critic_nonzero_steps"] += int(critic_nonzero)
        stats["actor_max_gradient_norm"] = max(
            stats["actor_max_gradient_norm"], actor_norm
        )
        stats["critic_max_gradient_norm"] = max(
            stats["critic_max_gradient_norm"], critic_norm
        )
        source_gradients = [
            parameter.grad
            for name, parameter in transformer.named_parameters()
            if not name.startswith("r43_") and parameter.grad is not None
        ]
        stats["source_gradient_tensors"] += len(source_gradients)
        if trainer._use_max_grad_norm:
            nn.utils.clip_grad_norm_(parameters, trainer.max_grad_norm)
        runner.r44_factor_optimizer.step()

        valid_ratio = renew_ratio[renew_mask > 0]
        totals["h_value_loss"] += float(value_loss.detach().item())
        totals["h_policy_loss"] += float(policy_loss.detach().item())
        totals["h_actor_grad_norm"] += actor_norm
        totals["h_critic_grad_norm"] += critic_norm
        totals["h_ratio"] += float(valid_ratio.mean().detach().item())
        totals["r44_renew_value_loss"] += float(value_loss.detach().item())

    epochs = float(trainer.ppo_epoch)
    for name in totals:
        if name != "r44_renew_actor_mask":
            totals[name] /= epochs
    return totals


def _patch_r44_runner(runner: Any) -> None:
    source_compute = runner.compute
    _patch_buffer(runner.h_buffer, runner.num_agents)
    _patch_treatment_runner(runner, runner.h_policy.act_dim)

    @torch.no_grad()
    def compute(self: Any) -> None:
        _compute_r44_credit(self)
        source_compute()

    def train(self: Any) -> dict[str, float]:
        info = _factor_train(self)
        self.h_buffer.after_update()
        self.l_buffer.after_update()
        return info

    runner.compute = MethodType(compute, runner)
    runner.train = MethodType(train, runner)


def install_frozen_source_nrc(runner: Any, mode: str) -> dict[str, Any]:
    """Install the exact R44 control/treatment boundary."""

    if mode not in R44_MODES:
        raise ValueError(f"unsupported R44 mode: {mode}")
    if runner.num_agents != 2 or runner.h_policy.action_type != "Discrete":
        raise RuntimeError("R44 first gate requires N=2 discrete source HMASD")
    if runner.use_linear_lr_decay:
        raise RuntimeError("R44 source optimizers must not receive LR updates")

    policy = runner.h_policy
    transformer = policy.transformer
    if hasattr(transformer, "r43_renewal_actor"):
        raise RuntimeError("native renewal overlay is already installed")

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
    renewal_critic = ContextHead(input_dim, 1).to(policy.device)
    _restore_torch_rng(construction_rng)
    transformer.add_module("r43_renewal_actor", renewal_actor)
    transformer.add_module("r43_renewal_critic", renewal_critic)
    transformer.add_module("r43_skill_event_critic", ZeroHead().to(policy.device))
    if mode == R44_CONTROL:
        renewal_actor.requires_grad_(False)

    parity = _enumeration_parity(runner)
    for field in (
        "maximum_logp_error",
        "maximum_probability_error",
        "maximum_probability_sum_error",
    ):
        value = float(parity[field])
        if not math.isfinite(value) or value > 1e-6:
            raise RuntimeError(f"R44 zero-init source parity failed: {parity}")

    factor_parameters = list(renewal_actor.parameters()) + list(
        renewal_critic.parameters()
    )
    source_defaults = dict(policy.optimizer.defaults)
    runner.r44_factor_optimizer = torch.optim.Adam(
        factor_parameters, **source_defaults
    )
    runner.r44_mode = mode
    runner.r44_factor_gradient_stats = {
        "steps": 0,
        "actor_gradient_checks": 0,
        "critic_gradient_checks": 0,
        "actor_all_gradients_finite": True,
        "critic_all_gradients_finite": True,
        "actor_nonzero_steps": 0,
        "critic_nonzero_steps": 0,
        "actor_max_gradient_norm": 0.0,
        "critic_max_gradient_norm": 0.0,
        "source_gradient_tensors": 0,
        "maximum_prefix_mismatch": 0,
    }
    _wrap_runtime_clock(runner, R43_TREATMENT, policy.act_dim)
    _patch_r44_runner(runner)
    return {
        "mode": mode,
        "controller_clock": "source_global_k50_reset_censored",
        "context_input_dim": input_dim,
        "module_parameter_counts": {
            "renewal_actor": sum(p.numel() for p in renewal_actor.parameters()),
            "renewal_critic": sum(p.numel() for p in renewal_critic.parameters()),
        },
        "zero_init_probability": parity,
        "source_parameters_frozen": True,
        "renewal_actor_trainable": mode == R44_TREATMENT,
        "renewal_critic_trainable": True,
        "conditional_skill_trainable": False,
        "renewal_entropy": False,
        "task_specific_inputs": False,
        "reward_shaping": False,
        "intrinsic_reward_changed": False,
        "factor_optimizer_class": type(runner.r44_factor_optimizer).__name__,
        "factor_optimizer_defaults": {
            name: value
            for name, value in source_defaults.items()
            if isinstance(value, (bool, int, float, str, type(None)))
        },
    }


def factor_state_snapshot(runner: Any) -> dict[str, dict[str, torch.Tensor]]:
    transformer = runner.h_policy.transformer
    return {
        name: {
            key: value.detach().cpu().clone()
            for key, value in getattr(transformer, name).state_dict().items()
        }
        for name in ("r43_renewal_actor", "r43_renewal_critic")
    }


def factor_parameter_drift(
    runner: Any, initial: dict[str, dict[str, torch.Tensor]]
) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    transformer = runner.h_policy.transformer
    for module_name, before_state in initial.items():
        after_state = getattr(transformer, module_name).state_dict()
        delta_sq = 0.0
        initial_sq = 0.0
        maximum = 0.0
        for name, before in before_state.items():
            after = after_state[name].detach().cpu()
            delta = after - before
            delta_sq += float(delta.float().pow(2).sum().item())
            initial_sq += float(before.float().pow(2).sum().item())
            maximum = max(maximum, float(delta.abs().max().item()))
        absolute = math.sqrt(delta_sq)
        result[module_name] = {
            "absolute_l2": absolute,
            "relative_l2": absolute / (math.sqrt(initial_sq) + 1e-12),
            "max_abs": maximum,
        }
    return result
