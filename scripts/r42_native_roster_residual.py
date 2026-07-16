"""Runtime overlay for the native HMASD incumbent-roster residual.

The official source tree is imported unchanged.  This module attaches one
zero-output residual to the existing MAT individual logits and carries the
pre-check roster through collection and teacher-forced PPO replay.
"""

from __future__ import annotations

import math
from types import MethodType
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical


R42_FIXED = "fixed_refresh"
R42_TREATMENT = "incumbent_roster_residual"
R42_MODES = (R42_FIXED, R42_TREATMENT)


class IncumbentRosterResidual(nn.Module):
    """Task-blind shared correction for one individual categorical token."""

    def __init__(self, num_agents: int, skill_dim: int, hidden_dim: int = 32) -> None:
        super().__init__()
        self.num_agents = int(num_agents)
        self.skill_dim = int(skill_dim)
        input_dim = self.num_agents * self.skill_dim + 2 * self.num_agents
        self.hidden = nn.Linear(input_dim, hidden_dim)
        self.output = nn.Linear(hidden_dim, self.skill_dim)
        nn.init.orthogonal_(self.hidden.weight, gain=nn.init.calculate_gain("relu"))
        nn.init.zeros_(self.hidden.bias)
        nn.init.zeros_(self.output.weight)
        nn.init.zeros_(self.output.bias)

    def forward(
        self,
        working_roster: torch.Tensor,
        focal_index: int,
        active_mask: torch.Tensor,
    ) -> torch.Tensor:
        safe_roster = working_roster.clamp(min=0, max=self.skill_dim - 1)
        roster_one_hot = F.one_hot(
            safe_roster, num_classes=self.skill_dim
        ).to(dtype=self.hidden.weight.dtype)
        roster_one_hot = roster_one_hot * active_mask.unsqueeze(-1).to(
            dtype=roster_one_hot.dtype
        )
        batch_size = working_roster.shape[0]
        focal = torch.zeros(
            (batch_size, self.num_agents),
            dtype=roster_one_hot.dtype,
            device=working_roster.device,
        )
        focal[:, focal_index] = 1.0
        features = torch.cat(
            (
                roster_one_hot.reshape(batch_size, -1),
                focal,
                active_mask.to(dtype=roster_one_hot.dtype),
            ),
            dim=-1,
        )
        logits = self.output(F.gelu(self.hidden(features)))
        row_active = active_mask.any(dim=-1, keepdim=True).to(dtype=logits.dtype)
        return logits * row_active


def _capture_torch_rng() -> dict[str, Any]:
    return {
        "cpu": torch.get_rng_state(),
        "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
    }


def _restore_torch_rng(state: dict[str, Any]) -> None:
    torch.set_rng_state(state["cpu"])
    if torch.cuda.is_available():
        torch.cuda.set_rng_state_all(state["cuda"])


def _as_incumbent(
    incumbent_roster: Any,
    batch_size: int,
    num_agents: int,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    if incumbent_roster is None:
        roster = torch.full(
            (batch_size, num_agents), -1, dtype=torch.long, device=device
        )
    else:
        roster = torch.as_tensor(
            incumbent_roster, dtype=torch.long, device=device
        ).reshape(batch_size, num_agents)
    return roster, roster >= 0


def _residual_logits(
    transformer: nn.Module,
    working_roster: torch.Tensor,
    focal_index: int,
    active_mask: torch.Tensor,
) -> torch.Tensor:
    residual = transformer.r42_incumbent_roster_residual(
        working_roster, focal_index, active_mask
    )
    return residual * float(transformer.r42_residual_scale)


def _sample_with_residual(
    transformer: nn.Module,
    state: Any,
    obs: Any,
    available_actions: Any,
    deterministic: bool,
    incumbent_roster: Any,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    from hmasd.algorithms.utils.util import check

    state = check(state).to(**transformer.tpdv)
    obs = check(obs).to(**transformer.tpdv)
    if available_actions is not None:
        available_actions = check(available_actions).to(**transformer.tpdv)
    batch_size = int(obs.shape[0])
    values, obs_rep = transformer.encoder(state, obs)
    action_dim = transformer.action_dim
    num_agents = transformer.n_agent
    shifted_action = torch.zeros(
        (batch_size, num_agents + 1, action_dim + 1), **transformer.tpdv
    )
    shifted_action[:, 0, 0] = 1
    output_action = torch.zeros(
        (batch_size, num_agents + 1, 1), dtype=torch.long
    )
    output_log_prob = torch.zeros_like(output_action, dtype=torch.float32)
    working_roster, active_mask = _as_incumbent(
        incumbent_roster, batch_size, num_agents, obs_rep.device
    )
    working_roster = working_roster.clone()

    for token_index in range(num_agents + 1):
        logits = transformer.decoder(shifted_action, obs_rep)[:, token_index, :]
        if token_index > 0:
            logits = logits + _residual_logits(
                transformer,
                working_roster,
                token_index - 1,
                active_mask,
            )
        if available_actions is not None:
            logits[available_actions[:, token_index, :] == 0] = -1e10
        distribution = Categorical(logits=logits)
        action = (
            distribution.probs.argmax(dim=-1)
            if deterministic
            else distribution.sample()
        )
        action_log_prob = distribution.log_prob(action)
        output_action[:, token_index, :] = action.unsqueeze(-1)
        output_log_prob[:, token_index, :] = action_log_prob.unsqueeze(-1)
        if token_index > 0:
            working_roster[:, token_index - 1] = action
        if token_index + 1 < num_agents + 1:
            shifted_action[:, token_index + 1, 1:] = F.one_hot(
                action, num_classes=action_dim
            )
    return output_action, output_log_prob, values


def _evaluate_with_residual(
    transformer: nn.Module,
    state: Any,
    obs: Any,
    action: Any,
    available_actions: Any,
    incumbent_roster: Any,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    from hmasd.algorithms.utils.util import check

    state = check(state).to(**transformer.tpdv)
    obs = check(obs).to(**transformer.tpdv)
    action = check(action).to(**transformer.tpdv).long()
    if available_actions is not None:
        available_actions = check(available_actions).to(**transformer.tpdv)
    batch_size = int(state.shape[0])
    num_agents = transformer.n_agent
    action_dim = transformer.action_dim
    values, obs_rep = transformer.encoder(state, obs)
    one_hot_action = F.one_hot(
        action.squeeze(-1), num_classes=action_dim
    )
    shifted_action = torch.zeros(
        (batch_size, num_agents + 1, action_dim + 1), **transformer.tpdv
    )
    shifted_action[:, 0, 0] = 1
    shifted_action[:, 1:, 1:] = one_hot_action[:, :-1, :]
    logits = transformer.decoder(shifted_action, obs_rep)
    working_roster, active_mask = _as_incumbent(
        incumbent_roster, batch_size, num_agents, obs_rep.device
    )
    residual_by_token = torch.zeros_like(logits)
    for focal_index in range(num_agents):
        if focal_index > 0:
            working_roster = working_roster.clone()
            working_roster[:, focal_index - 1] = action[:, focal_index, 0]
        residual_by_token[:, focal_index + 1, :] = _residual_logits(
            transformer,
            working_roster,
            focal_index,
            active_mask,
        )
    logits = logits + residual_by_token
    if available_actions is not None:
        logits[available_actions == 0] = -1e10
    distribution = Categorical(logits=logits)
    action_log_prob = distribution.log_prob(action.squeeze(-1)).unsqueeze(-1)
    entropy = distribution.entropy().unsqueeze(-1)
    return action_log_prob, values, entropy


def _patch_policy(policy: Any) -> None:
    def get_actions(
        self: Any,
        cent_obs: Any,
        obs: Any,
        deterministic: bool = False,
        incumbent_roster: Any = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        cent_obs = cent_obs.reshape(-1, self.num_agents, self.share_obs_dim)
        obs = obs.reshape(-1, self.num_agents, self.obs_dim)
        batch_size = obs.shape[0]
        available = self.available_actions
        if available is not None:
            available = np.expand_dims(available, 0).repeat(batch_size, 0)
        actions, log_probs, values = _sample_with_residual(
            self.transformer,
            cent_obs,
            obs,
            available,
            deterministic,
            incumbent_roster,
        )
        return (
            values.view(-1, 1),
            actions.view(-1, self.act_num),
            log_probs.view(-1, self.act_num),
        )

    def evaluate_actions(
        self: Any,
        cent_obs: Any,
        obs: Any,
        actions: Any,
        incumbent_roster: Any = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        cent_obs = cent_obs.reshape(-1, self.num_agents, self.share_obs_dim)
        obs = obs.reshape(-1, self.num_agents, self.obs_dim)
        actions = actions.reshape(-1, self.num_agents + 1, self.act_num)
        batch_size = obs.shape[0]
        available = self.available_actions
        if available is not None:
            available = np.expand_dims(available, 0).repeat(batch_size, 0)
        if incumbent_roster is None:
            incumbent_roster = getattr(self, "_r42_replay_incumbent", None)
        log_probs, values, entropy = _evaluate_with_residual(
            self.transformer,
            cent_obs,
            obs,
            actions,
            available,
            incumbent_roster,
        )
        return (
            values.view(-1, 1),
            log_probs.view(-1, self.act_num),
            entropy.view(-1, self.act_num).mean(),
        )

    def act(
        self: Any,
        cent_obs: Any,
        obs: Any,
        deterministic: bool = True,
        incumbent_roster: Any = None,
    ) -> torch.Tensor:
        _, actions, _ = self.get_actions(
            cent_obs,
            obs,
            deterministic=deterministic,
            incumbent_roster=incumbent_roster,
        )
        return actions

    policy.get_actions = MethodType(get_actions, policy)
    policy.evaluate_actions = MethodType(evaluate_actions, policy)
    policy.act = MethodType(act, policy)


def _patch_buffer(buffer: Any, num_agents: int) -> None:
    buffer.r42_incumbent_roster = np.full(
        (buffer.episode_length, buffer.n_rollout_threads, num_agents),
        -1,
        dtype=np.int64,
    )

    def generator(
        self: Any,
        advantages: Any,
        num_mini_batch: int | None = None,
        mini_batch_size: int | None = None,
    ):
        episode_length, n_rollout_threads = self.rewards.shape[0:2]
        batch_size = n_rollout_threads * episode_length
        if mini_batch_size is None:
            if num_mini_batch is None or batch_size < num_mini_batch:
                raise ValueError("invalid R42 high PPO minibatch geometry")
            mini_batch_size = batch_size // num_mini_batch
        rand = torch.randperm(batch_size).numpy()
        sampler = [
            rand[index * mini_batch_size : (index + 1) * mini_batch_size]
            for index in range(int(num_mini_batch))
        ]
        share_obs = self.share_obs[:-1].reshape(-1, *self.share_obs.shape[2:])
        obs = self.obs[:-1].reshape(-1, *self.obs.shape[2:])
        actions = self.actions.reshape(-1, *self.actions.shape[2:])
        value_preds = self.value_preds[:-1].reshape(
            -1, *self.value_preds.shape[2:]
        )
        returns = self.returns[:-1].reshape(-1, *self.returns.shape[2:])
        old_log_probs = self.action_log_probs.reshape(
            -1, *self.action_log_probs.shape[2:]
        )
        incumbent = self.r42_incumbent_roster.reshape(-1, num_agents)
        advantages_flat = (
            None
            if advantages is None
            else advantages.reshape(-1, *advantages.shape[2:])
        )
        for indices in sampler:
            self._r42_current_incumbent_batch = incumbent[indices].copy()
            yield (
                share_obs[indices].reshape(-1, *share_obs.shape[2:]),
                obs[indices].reshape(-1, *obs.shape[2:]),
                actions[indices].reshape(-1, *actions.shape[2:]),
                value_preds[indices].reshape(-1, *value_preds.shape[2:]),
                returns[indices].reshape(-1, *returns.shape[2:]),
                old_log_probs[indices].reshape(-1, *old_log_probs.shape[2:]),
                None
                if advantages_flat is None
                else advantages_flat[indices].reshape(
                    -1, *advantages_flat.shape[2:]
                ),
            )

    buffer.feed_forward_generator_transformer = MethodType(generator, buffer)


def _patch_trainer(trainer: Any, buffer: Any) -> None:
    original_ppo_update = trainer.ppo_update

    def ppo_update(self: Any, sample: Any):
        incumbent = getattr(buffer, "_r42_current_incumbent_batch", None)
        if incumbent is None:
            raise RuntimeError("R42 replay incumbent batch was not set")
        self.policy._r42_replay_incumbent = incumbent
        try:
            return original_ppo_update(sample)
        finally:
            self.policy._r42_replay_incumbent = None

    trainer.ppo_update = MethodType(ppo_update, trainer)


def _empty_event_ledger(num_agents: int, skill_dim: int) -> dict[str, Any]:
    return {
        "events": 0,
        "agent_keep": [0 for _ in range(num_agents)],
        "agent_set": [0 for _ in range(num_agents)],
        "discordant": 0,
        "full_sync_set": 0,
        "set_skill_counts": [0 for _ in range(skill_dim)],
    }


def _patch_runner(runner: Any, skill_dim: int) -> None:
    runner.r42_event_ledger = _empty_event_ledger(runner.num_agents, skill_dim)
    runner._r42_current_roster = None

    @torch.no_grad()
    def h_collect(self: Any, step: int):
        self.h_trainer.prep_rollout()
        if step == 0:
            incumbent = np.full(
                (self.n_rollout_threads, self.num_agents), -1, dtype=np.int64
            )
        else:
            if self._r42_current_roster is None:
                raise RuntimeError("R42 incumbent roster is missing at renewal")
            incumbent = self._r42_current_roster.copy()
        value, action, action_log_prob = self.h_trainer.policy.get_actions(
            np.concatenate(self.h_buffer.share_obs[step]),
            np.concatenate(self.h_buffer.obs[step]),
            incumbent_roster=incumbent,
        )
        values = np.array(
            np.split(value.detach().cpu().numpy(), self.n_rollout_threads)
        )
        actions = np.array(
            np.split(action.detach().cpu().numpy(), self.n_rollout_threads)
        )
        action_log_probs = np.array(
            np.split(
                action_log_prob.detach().cpu().numpy(), self.n_rollout_threads
            )
        )
        self.h_buffer.r42_incumbent_roster[step] = incumbent
        next_roster = actions[:, 1:, 0].astype(np.int64, copy=True)
        if step > 0:
            changes = next_roster != incumbent
            ledger = self.r42_event_ledger
            ledger["events"] += int(changes.shape[0])
            for agent_index in range(self.num_agents):
                ledger["agent_set"][agent_index] += int(
                    changes[:, agent_index].sum()
                )
                ledger["agent_keep"][agent_index] += int(
                    (~changes[:, agent_index]).sum()
                )
            if self.num_agents == 2:
                ledger["discordant"] += int(
                    np.logical_xor(changes[:, 0], changes[:, 1]).sum()
                )
            ledger["full_sync_set"] += int(changes.all(axis=1).sum())
            for label in range(skill_dim):
                ledger["set_skill_counts"][label] += int(
                    ((next_roster == label) & changes).sum()
                )
        self._r42_current_roster = next_roster
        return values, actions, action_log_probs

    runner.h_collect = MethodType(h_collect, runner)


def _gradient_snapshot(transformer: nn.Module) -> dict[str, torch.Tensor]:
    return {
        name: parameter.grad.detach().cpu().clone()
        for name, parameter in transformer.named_parameters()
        if parameter.grad is not None
        and not name.startswith("r42_incumbent_roster_residual.")
    }


def _max_gradient_error(
    before: dict[str, torch.Tensor], after: dict[str, torch.Tensor]
) -> float:
    if before.keys() != after.keys():
        return math.inf
    return max(
        (float((before[name] - after[name]).abs().max().item()) for name in before),
        default=0.0,
    )


def install_native_roster_residual(runner: Any, mode: str) -> dict[str, Any]:
    """Attach the R42 overlay and return its zero-output parity evidence."""

    if mode not in R42_MODES:
        raise ValueError(f"unsupported R42 mode: {mode}")
    policy = runner.h_policy
    transformer = policy.transformer
    if hasattr(transformer, "r42_incumbent_roster_residual"):
        raise RuntimeError("R42 residual is already installed")
    if policy.action_type != "Discrete" or runner.num_agents != 2:
        raise RuntimeError("the first R42 gate requires N=2 discrete HMASD")

    original_get_actions = policy.get_actions
    original_evaluate_actions = policy.evaluate_actions
    batch_size = 4
    cent_obs = np.linspace(
        -1.0,
        1.0,
        batch_size * runner.num_agents * policy.share_obs_dim,
        dtype=np.float32,
    ).reshape(batch_size * runner.num_agents, policy.share_obs_dim)
    obs = np.linspace(
        1.0,
        -1.0,
        batch_size * runner.num_agents * policy.obs_dim,
        dtype=np.float32,
    ).reshape(batch_size * runner.num_agents, policy.obs_dim)
    incumbent = np.asarray([[0, 1], [2, 3], [1, 1], [3, 0]], dtype=np.int64)
    rng_state = _capture_torch_rng()
    was_training = transformer.training
    transformer.eval()
    with torch.no_grad():
        original_values, original_actions, original_log_probs = original_get_actions(
            cent_obs, obs, deterministic=False
        )
    actions_numpy = original_actions.detach().cpu().numpy()
    policy.optimizer.zero_grad(set_to_none=True)
    original_eval_values, original_eval_log_probs, original_entropy = (
        original_evaluate_actions(cent_obs, obs, actions_numpy)
    )
    original_loss = -original_eval_log_probs.mean() + 0.01 * original_entropy
    original_loss.backward()
    original_gradients = _gradient_snapshot(transformer)
    policy.optimizer.zero_grad(set_to_none=True)

    construction_rng = _capture_torch_rng()
    residual = IncumbentRosterResidual(
        runner.num_agents, policy.act_dim, hidden_dim=32
    ).to(policy.device)
    _restore_torch_rng(construction_rng)
    transformer.add_module("r42_incumbent_roster_residual", residual)
    transformer.r42_residual_scale = 1.0
    _patch_policy(policy)
    _restore_torch_rng(rng_state)
    with torch.no_grad():
        patched_values, patched_actions, patched_log_probs = policy.get_actions(
            cent_obs,
            obs,
            deterministic=False,
            incumbent_roster=incumbent,
        )
    policy.optimizer.zero_grad(set_to_none=True)
    patched_eval_values, patched_eval_log_probs, patched_entropy = (
        policy.evaluate_actions(
            cent_obs, obs, actions_numpy, incumbent_roster=incumbent
        )
    )
    patched_loss = -patched_eval_log_probs.mean() + 0.01 * patched_entropy
    patched_loss.backward()
    patched_gradients = _gradient_snapshot(transformer)
    residual_gradients = [
        parameter.grad.detach()
        for parameter in residual.parameters()
        if parameter.grad is not None
    ]
    residual_gradient_norm = math.sqrt(
        sum(float(gradient.float().pow(2).sum().item()) for gradient in residual_gradients)
    )
    policy.optimizer.zero_grad(set_to_none=True)
    _restore_torch_rng(rng_state)

    parity = {
        "sample_action_max_abs_error": float(
            (patched_actions.cpu() - original_actions.cpu()).abs().max().item()
        ),
        "sample_logp_max_abs_error": float(
            (patched_log_probs.cpu() - original_log_probs.cpu()).abs().max().item()
        ),
        "sample_value_max_abs_error": float(
            (patched_values.cpu() - original_values.cpu()).abs().max().item()
        ),
        "replay_logp_max_abs_error": float(
            (patched_eval_log_probs - original_eval_log_probs).abs().max().item()
        ),
        "replay_value_max_abs_error": float(
            (patched_eval_values - original_eval_values).abs().max().item()
        ),
        "entropy_abs_error": float(
            (patched_entropy - original_entropy).abs().item()
        ),
        "base_gradient_max_abs_error": _max_gradient_error(
            original_gradients, patched_gradients
        ),
        "residual_gradient_norm": residual_gradient_norm,
        "residual_parameter_count": int(
            sum(parameter.numel() for parameter in residual.parameters())
        ),
        "rng_restored": True,
    }
    if max(
        parity["sample_action_max_abs_error"],
        parity["sample_logp_max_abs_error"],
        parity["sample_value_max_abs_error"],
        parity["replay_logp_max_abs_error"],
        parity["replay_value_max_abs_error"],
        parity["entropy_abs_error"],
        parity["base_gradient_max_abs_error"],
    ) > 1e-6:
        raise RuntimeError(f"R42 zero-output parity failed: {parity}")
    if not math.isfinite(residual_gradient_norm) or residual_gradient_norm <= 0.0:
        raise RuntimeError("R42 residual has no direct policy gradient")

    policy.optimizer.add_param_group({"params": list(residual.parameters())})
    if mode == R42_FIXED:
        transformer.r42_residual_scale = 0.0
        residual.requires_grad_(False)
    else:
        transformer.r42_residual_scale = 1.0
    _patch_buffer(runner.h_buffer, runner.num_agents)
    _patch_trainer(runner.h_trainer, runner.h_buffer)
    _patch_runner(runner, policy.act_dim)
    if was_training:
        transformer.train()
    else:
        transformer.eval()
    parity["mode"] = mode
    parity["active_scale"] = float(transformer.r42_residual_scale)
    return parity


def residual_parameter_drift(runner: Any, initial: dict[str, torch.Tensor]) -> dict[str, float]:
    current = runner.h_policy.transformer.r42_incumbent_roster_residual.state_dict()
    squared_delta = 0.0
    squared_initial = 0.0
    maximum = 0.0
    for name, before in initial.items():
        after = current[name].detach().cpu()
        delta = after - before
        squared_delta += float(delta.float().pow(2).sum().item())
        squared_initial += float(before.float().pow(2).sum().item())
        maximum = max(maximum, float(delta.abs().max().item()))
    absolute = math.sqrt(squared_delta)
    return {
        "absolute_l2": absolute,
        "relative_l2": absolute / (math.sqrt(squared_initial) + 1e-12),
        "max_abs": maximum,
    }


def summarize_event_ledger(ledger: dict[str, Any]) -> dict[str, Any]:
    events = int(ledger["events"])
    set_counts = np.asarray(ledger["set_skill_counts"], dtype=np.float64)
    total_set = float(set_counts.sum())
    if total_set > 0:
        probabilities = set_counts[set_counts > 0] / total_set
        entropy = float(-(probabilities * np.log(probabilities)).sum())
        normalized_entropy = entropy / math.log(len(set_counts))
    else:
        normalized_entropy = 0.0
    return {
        **ledger,
        "agent_keep_rate": [
            count / events if events else 0.0 for count in ledger["agent_keep"]
        ],
        "agent_set_rate": [
            count / events if events else 0.0 for count in ledger["agent_set"]
        ],
        "discordant_rate": ledger["discordant"] / events if events else 0.0,
        "full_sync_set_rate": ledger["full_sync_set"] / events if events else 0.0,
        "set_skill_entropy_normalized": normalized_entropy,
    }
