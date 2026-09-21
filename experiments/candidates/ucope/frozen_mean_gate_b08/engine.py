"""Frozen-mean KEEP/END collection and gate-only PPO for UCOPE B08.

This module owns no environment construction, foundation loading, publication,
or launch behavior.  It operates on the existing CPU FP32 Actor/adapter
interfaces and stores complete predecision episode tensors for the caller.
"""

from __future__ import annotations

import math
from typing import Any, Literal, Mapping, MutableMapping

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from ..uav_motion_prefix_b01.environment import actor_features, critic_features, team_reward
from ..uav_motion_prefix_b01.policy import Critic


GateMode = Literal["agreement", "contextual"]
_AGENTS = 5
_GATE_FEATURES = 175
_CRITIC_FEATURES = 136


def _add(counts: MutableMapping[str, int], key: str, amount: int = 1) -> None:
    counts[key] = int(counts.get(key, 0)) + int(amount)


class Gate(nn.Module):
    """Shared per-agent KEEP policy with an affine disagreement reference.

    ``agreement`` uses ``b0 + b1*d``.  ``contextual`` adds a 175->32->1 tanh
    residual whose final layer is zero initialized, so both modes initially
    emit exactly zero logits without advancing PyTorch's global CPU RNG.
    """

    def __init__(self, mode: GateMode, seed: int) -> None:
        super().__init__()
        if mode not in ("agreement", "contextual"):
            raise ValueError("mode must be 'agreement' or 'contextual'")
        self.mode: GateMode = mode
        self.b0 = nn.Parameter(torch.zeros((), dtype=torch.float32))
        self.b1 = nn.Parameter(torch.zeros((), dtype=torch.float32))
        self.residual: nn.Sequential | None = None
        if mode == "contextual":
            with torch.random.fork_rng(devices=[]):
                torch.random.default_generator.manual_seed(int(seed))
                self.residual = nn.Sequential(
                    nn.Linear(_GATE_FEATURES, 32),
                    nn.Tanh(),
                    nn.Linear(32, 1),
                )
            nn.init.zeros_(self.residual[-1].weight)
            nn.init.zeros_(self.residual[-1].bias)

    def forward(self, context: torch.Tensor) -> torch.Tensor:
        if context.shape[-2:] != (_AGENTS, _GATE_FEATURES):
            raise ValueError("context must end in [5, 175]")
        if context.dtype != torch.float32 or context.device.type != "cpu":
            raise TypeError("gate context must be CPU float32")
        if not bool(torch.isfinite(context).all()):
            raise FloatingPointError("gate context must be finite")
        logits = self.b0 + self.b1 * context[..., -1]
        if self.residual is not None:
            logits = logits + self.residual(context).squeeze(-1)
        return logits

    def log_prob(self, context: torch.Tensor, keep_bool: torch.Tensor) -> torch.Tensor:
        """Return stable elementwise Bernoulli log likelihoods for KEEP bits."""

        logits = self(context)
        if keep_bool.shape != logits.shape or keep_bool.dtype != torch.bool:
            raise TypeError("keep_bool must be bool with the gate-logit shape")
        if keep_bool.device != logits.device:
            raise ValueError("keep_bool and context must share a device")
        return torch.where(keep_bool, -F.softplus(-logits), -F.softplus(logits))


def make_critic(seed: int) -> Critic:
    """Build the unchanged 136->128->128->1 critic with private initialization."""

    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(int(seed))
        return Critic()


def freeze_foundation(actor: nn.Module) -> nn.Module:
    """Put the supplied foundation in eval mode and freeze every parameter."""

    actor.eval()
    actor.requires_grad_(False)
    return actor


def _require_frozen_foundation(actor: nn.Module) -> None:
    if actor.training or any(parameter.requires_grad for parameter in actor.parameters()):
        raise ValueError("foundation must be frozen with freeze_foundation before collection")
    if any(parameter.device.type != "cpu" for parameter in actor.parameters()):
        raise ValueError("foundation must be on CPU")


def _private_uniforms(horizon: int, seed: int) -> torch.Tensor:
    generator = torch.Generator(device="cpu").manual_seed(int(seed))
    return torch.rand((horizon, _AGENTS), generator=generator, dtype=torch.float32)


@torch.no_grad()
def collect_episode(
    env: Any,
    foundation: nn.Module,
    gate_or_none: Gate | None,
    critic_or_none: Critic | None,
    *,
    horizon: int,
    reset_seed: int,
    gate_seed: int,
    phase: str,
    check: Any,
    counts: MutableMapping[str, int],
) -> dict[str, torch.Tensor]:
    """Collect one exact finite episode using frozen recurrent mean feedback.

    Learned arms pre-generate one private ``[horizon, 5]`` uniform array.
    Ordinary collection (``gate_or_none is None``) executes a fresh mean every
    tick and consumes no gate RNG or critic forward.
    """

    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon <= 0:
        raise ValueError("horizon must be a positive integer")
    if phase not in ("train", "eval"):
        raise ValueError("phase must be 'train' or 'eval'")
    if not callable(check):
        raise TypeError("check must be callable")
    _require_frozen_foundation(foundation)
    learned = gate_or_none is not None
    if learned and critic_or_none is None:
        raise ValueError("learned gate collection requires a critic")
    if learned and (
        any(parameter.device.type != "cpu" for parameter in gate_or_none.parameters())
        or any(parameter.device.type != "cpu" for parameter in critic_or_none.parameters())
    ):
        raise ValueError("gate and critic must be on CPU")
    for key in (
        "reset_calls",
        "foundation_forward_calls",
        "recurrent_agent_observations",
        "gate_decisions",
        "keep_decisions",
        "end_decisions",
        "forced_fresh_decisions",
        "final_gate_credit_decisions",
        "team_steps",
        f"{phase}_team_steps",
        f"{phase}_episodes",
        "gate_uniform_values",
    ):
        counts.setdefault(key, 0)

    gate_uniforms = _private_uniforms(horizon, gate_seed) if learned else torch.zeros(
        (horizon, _AGENTS), dtype=torch.float32
    )
    if learned:
        _add(counts, "gate_uniform_values", horizon * _AGENTS)

    check()
    obs, info = env.reset(seed=reset_seed)
    _add(counts, "reset_calls")
    check()
    state = info["state"]
    last = np.zeros((_AGENTS, 3), dtype=np.float32)
    eligible = np.zeros(_AGENTS, dtype=bool)
    hidden = torch.zeros(1, _AGENTS, 64, dtype=torch.float32)
    storage: dict[str, list[torch.Tensor]] = {
        name: []
        for name in (
            "context",
            "critic",
            "eligible",
            "keep",
            "logp",
            "value",
            "reward",
            "commands",
            "means",
            "previous",
            "gate_uniforms",
            "keep_probability",
        )
    }

    for tick in range(horizon):
        check()
        obs_array = np.asarray(obs, dtype=np.float32)
        if obs_array.shape != (_AGENTS, 104):
            raise ValueError("foundation observation must have shape [5, 104]")
        previous = last.copy()
        actor_input = actor_features(
            obs_array, previous, np.zeros(_AGENTS, dtype=np.int64)
        )
        raw_mean, recurrent, hidden = foundation(
            torch.from_numpy(actor_input)[None], hidden
        )
        _add(counts, "foundation_forward_calls")
        _add(counts, "recurrent_agent_observations", _AGENTS)
        raw_mean, recurrent = raw_mean[0], recurrent[0]
        if (
            raw_mean.shape != (_AGENTS, 3)
            or recurrent.shape != (_AGENTS, 64)
            or raw_mean.dtype != torch.float32
            or recurrent.dtype != torch.float32
            or not bool(torch.isfinite(raw_mean).all())
            or not bool(torch.isfinite(recurrent).all())
            or hidden.shape != (1, _AGENTS, 64)
            or hidden.dtype != torch.float32
            or not bool(torch.isfinite(hidden).all())
        ):
            raise FloatingPointError("foundation returned invalid mean or recurrent output")
        fresh = raw_mean.tanh()
        previous_tensor = torch.from_numpy(previous)
        distance = ((fresh - previous_tensor).square().sum(-1) / 12.0).unsqueeze(-1)
        context = torch.cat(
            (
                torch.from_numpy(obs_array),
                previous_tensor,
                fresh,
                recurrent,
                distance,
            ),
            dim=-1,
        )
        if context.shape != (_AGENTS, _GATE_FEATURES) or not bool(
            torch.isfinite(context).all()
        ):
            raise FloatingPointError("constructed gate context is invalid")
        critic_input = torch.from_numpy(
            critic_features(state, previous, eligible.astype(np.int64))
        )
        if critic_input.shape != (_CRITIC_FEATURES,) or not bool(
            torch.isfinite(critic_input).all()
        ):
            raise FloatingPointError("constructed critic input is invalid")

        eligible_tensor = torch.from_numpy(eligible.copy())
        if learned:
            logits = gate_or_none(context)
            probability = torch.sigmoid(logits)
            keep = eligible_tensor & (gate_uniforms[tick] < probability)
            logp = torch.where(
                eligible_tensor,
                gate_or_none.log_prob(context, keep),
                torch.zeros_like(logits),
            )
            value = critic_or_none(critic_input)
            if value.ndim != 0 or not bool(torch.isfinite(value)):
                raise FloatingPointError("critic returned a nonfinite scalar")
            gate_decisions = int(eligible.sum())
            keep_decisions = int(keep.sum())
            end_decisions = gate_decisions - keep_decisions
            _add(counts, "gate_decisions", gate_decisions)
            _add(counts, "keep_decisions", keep_decisions)
            _add(counts, "end_decisions", end_decisions)
            if tick + 1 == horizon:
                _add(counts, "final_gate_credit_decisions", gate_decisions)
            command = fresh.clone()
            command[keep] = previous_tensor[keep]
            next_eligible = np.ones(_AGENTS, dtype=bool)
            next_eligible[keep.numpy()] = False
        else:
            probability = torch.zeros(_AGENTS, dtype=torch.float32)
            keep = torch.zeros(_AGENTS, dtype=torch.bool)
            logp = torch.zeros(_AGENTS, dtype=torch.float32)
            value = torch.zeros((), dtype=torch.float32)
            command = fresh
            next_eligible = np.zeros(_AGENTS, dtype=bool)

        forced = int((~eligible).sum())
        _add(counts, "forced_fresh_decisions", forced)
        for name, item in (
            ("context", context),
            ("critic", critic_input),
            ("eligible", eligible_tensor),
            ("keep", keep),
            ("logp", logp),
            ("value", value),
            ("commands", command),
            ("means", raw_mean),
            ("previous", previous_tensor),
            ("gate_uniforms", gate_uniforms[tick]),
            ("keep_probability", probability),
        ):
            storage[name].append(item.detach().clone())

        check()
        next_obs, _scalar, terminated, truncated, info = env.step(command.numpy())
        _add(counts, "team_steps")
        _add(counts, f"{phase}_team_steps")
        reward = float(team_reward(info))
        if not math.isfinite(reward):
            raise FloatingPointError("environment returned nonfinite team reward")
        # Retain the native Python-double reading for publication.  Training
        # casts the derived targets to the critic's FP32 dtype below.
        storage["reward"].append(torch.tensor(reward, dtype=torch.float64))
        boundary = bool(terminated or truncated)
        if bool(terminated) and bool(truncated):
            raise RuntimeError("episode cannot be both terminated and truncated")
        if tick + 1 < horizon and boundary:
            raise RuntimeError(f"incomplete episode: boundary at {tick + 1}/{horizon}")
        if tick + 1 == horizon and not boundary:
            raise RuntimeError(f"episode did not terminate at exact horizon {horizon}")
        last = command.numpy().copy()
        eligible = next_eligible
        obs, state = next_obs, info["next_state"]
        check()

    result = {name: torch.stack(items) for name, items in storage.items()}
    if any(tensor.device.type != "cpu" for tensor in result.values()) or any(
        tensor.is_floating_point() and not bool(torch.isfinite(tensor).all())
        for tensor in result.values()
    ):
        raise FloatingPointError("complete episode contains invalid tensors")
    _add(counts, f"{phase}_episodes")
    return result


def make_optimizers(
    gate: Gate, critic: Critic
) -> tuple[torch.optim.Adam, torch.optim.Adam]:
    """Return separate gate-only and critic-only Adam optimizers at 3e-4."""

    return (
        torch.optim.Adam(gate.parameters(), lr=3e-4),
        torch.optim.Adam(critic.parameters(), lr=3e-4),
    )


def _validate_optimizer_ownership(
    optimizer: torch.optim.Optimizer, parameters: list[nn.Parameter], name: str
) -> None:
    owned = [parameter for group in optimizer.param_groups for parameter in group["params"]]
    if len(owned) != len(parameters) or any(a is not b for a, b in zip(owned, parameters)):
        raise ValueError(f"{name} optimizer must contain only its model parameters")


def _flatten_episodes(
    episodes: list[Mapping[str, torch.Tensor]], horizon: int
) -> dict[str, torch.Tensor]:
    if len(episodes) != 2:
        raise ValueError("one update requires exactly two complete episodes")
    shapes = {
        "context": (horizon, _AGENTS, _GATE_FEATURES),
        "critic": (horizon, _CRITIC_FEATURES),
        "eligible": (horizon, _AGENTS),
        "keep": (horizon, _AGENTS),
        "logp": (horizon, _AGENTS),
        "value": (horizon,),
        "reward": (horizon,),
    }
    flattened: dict[str, torch.Tensor] = {}
    for name, shape in shapes.items():
        values = [episode.get(name) for episode in episodes]
        if any(not isinstance(value, torch.Tensor) or value.shape != shape for value in values):
            raise ValueError(f"episode {name} must have shape {shape}")
        flattened[name] = torch.cat(values, dim=0)
    if flattened["eligible"].dtype != torch.bool or flattened["keep"].dtype != torch.bool:
        raise TypeError("eligible and keep episode tensors must be bool")
    if bool((flattened["keep"] & ~flattened["eligible"]).any()):
        raise ValueError("KEEP is illegal outside gate eligibility")
    if any(tensor.device.type != "cpu" for tensor in flattened.values()) or any(
        tensor.is_floating_point() and not bool(torch.isfinite(tensor).all())
        for tensor in flattened.values()
    ):
        raise FloatingPointError("update episodes must contain finite CPU tensors")
    return flattened


def update(
    gate: Gate,
    critic: Critic,
    gate_optimizer: torch.optim.Adam,
    critic_optimizer: torch.optim.Adam,
    episodes: list[Mapping[str, torch.Tensor]],
    shuffle_rng: torch.Generator,
    *,
    horizon: int,
    check: Any,
    counts: MutableMapping[str, int],
) -> list[dict[str, float | int | bool]]:
    """Run four minibatched gate-only PPO and separate critic epochs."""

    _add(counts, "update_calls")
    if str(shuffle_rng.device) != "cpu":
        raise ValueError("shuffle_rng must be a private CPU generator")
    if not isinstance(gate_optimizer, torch.optim.Adam) or not isinstance(
        critic_optimizer, torch.optim.Adam
    ):
        raise TypeError("gate and critic optimizers must be Adam")
    for key in (
        "gate_optimizer_steps",
        "critic_optimizer_steps",
        "optimizer_steps",
        "visited_rows",
        "max_minibatch",
    ):
        counts.setdefault(key, 0)
    _validate_optimizer_ownership(gate_optimizer, list(gate.parameters()), "gate")
    _validate_optimizer_ownership(critic_optimizer, list(critic.parameters()), "critic")
    check()
    rollout = _flatten_episodes(episodes, horizon)
    rows = 2 * horizon
    rewards = rollout["reward"].detach().reshape(2, horizon).to(torch.float64)
    targets64 = rewards.flip(-1).cumsum(-1).flip(-1).reshape(rows) / float(horizon)
    raw_advantage = targets64 - rollout["value"].detach().to(torch.float64)
    advantage = (
        (raw_advantage - raw_advantage.mean())
        / (raw_advantage.std(unbiased=False) + 1e-8)
    ).to(torch.float32).detach()
    target = targets64.to(torch.float32).detach()
    records: list[dict[str, float | int | bool]] = []
    gate_parameters = list(gate.parameters())
    critic_parameters = list(critic.parameters())

    for epoch in range(4):
        order = torch.randperm(rows, generator=shuffle_rng)
        for start in range(0, rows, 256):
            check()
            indices = order[start : start + 256]
            minibatch_rows = int(indices.numel())
            _add(counts, "visited_rows", minibatch_rows)
            counts["max_minibatch"] = max(
                int(counts.get("max_minibatch", 0)), minibatch_rows
            )
            eligible = rollout["eligible"][indices]
            gate_step = bool(eligible.any())
            gate_loss = torch.zeros((), dtype=torch.float32)
            gate_grad_norm = 0.0
            if gate_step:
                new_logp = gate.log_prob(
                    rollout["context"][indices], rollout["keep"][indices]
                )
                log_ratio = torch.where(
                    eligible,
                    new_logp - rollout["logp"][indices].detach(),
                    torch.zeros_like(new_logp),
                )
                if not bool(torch.isfinite(log_ratio).all()):
                    raise FloatingPointError("nonfinite eligible gate log ratio")
                ratio = torch.exp(log_ratio)
                if not bool(torch.isfinite(ratio).all()):
                    raise FloatingPointError("nonfinite eligible gate ratio")
                clipped = ratio.clamp(0.8, 1.2)
                per_bit = torch.minimum(
                    ratio * advantage[indices, None],
                    clipped * advantage[indices, None],
                )
                gate_loss = -torch.where(
                    eligible, per_bit, torch.zeros_like(per_bit)
                ).sum() / minibatch_rows
                if not bool(torch.isfinite(gate_loss)):
                    raise FloatingPointError("nonfinite gate PPO loss")
                gate_optimizer.zero_grad(set_to_none=True)
                gate_loss.backward()
                try:
                    norm = nn.utils.clip_grad_norm_(
                        gate_parameters, 0.5, error_if_nonfinite=True
                    )
                except RuntimeError as error:
                    raise FloatingPointError("nonfinite gate gradient") from error
                gate_grad_norm = float(norm.detach())
                check()
                gate_optimizer.step()
                _add(counts, "gate_optimizer_steps")
                _add(counts, "optimizer_steps")

            predicted = critic(rollout["critic"][indices])
            critic_loss = 0.5 * (predicted - target[indices]).square().mean()
            if not bool(torch.isfinite(critic_loss)):
                raise FloatingPointError("nonfinite critic loss")
            critic_optimizer.zero_grad(set_to_none=True)
            critic_loss.backward()
            try:
                norm = nn.utils.clip_grad_norm_(
                    critic_parameters, 0.5, error_if_nonfinite=True
                )
            except RuntimeError as error:
                raise FloatingPointError("nonfinite critic gradient") from error
            critic_grad_norm = float(norm.detach())
            check()
            critic_optimizer.step()
            _add(counts, "critic_optimizer_steps")
            _add(counts, "optimizer_steps")
            if any(not bool(torch.isfinite(parameter).all()) for parameter in gate_parameters):
                raise FloatingPointError("nonfinite gate parameter after Adam")
            if any(not bool(torch.isfinite(parameter).all()) for parameter in critic_parameters):
                raise FloatingPointError("nonfinite critic parameter after Adam")
            records.append(
                {
                    "epoch": epoch,
                    "rows": minibatch_rows,
                    "eligible_decisions": int(eligible.sum()),
                    "gate_step": gate_step,
                    "gate_loss": float(gate_loss.detach()),
                    "critic_loss": float(critic_loss.detach()),
                    "gate_grad_norm": gate_grad_norm,
                    "critic_grad_norm": critic_grad_norm,
                }
            )
            check()
    return records
