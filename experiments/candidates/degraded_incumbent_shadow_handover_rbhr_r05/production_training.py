"""Batched PyTorch policy/replay boundary for frozen DISH RBHR r05.

PyTorch is the explicitly frozen model/backward/optimizer stage.  Environment
state transitions and rollout are never implemented here.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import io
import math
import time
from typing import Mapping

import torch
from torch import nn
from torch.nn import functional as F


class TrainingBoundaryError(RuntimeError):
    pass


class ExactPolicyGraph(nn.Module):
    """Exact-shape shared graph with the manifest's displayed GRU convention."""

    def __init__(self) -> None:
        super().__init__()
        self.encoder1 = nn.Linear(54, 128)
        self.encoder2 = nn.Linear(128, 128)
        self.wz = nn.Linear(128, 128); self.uz = nn.Linear(128, 128, bias=False)
        self.wr = nn.Linear(128, 128); self.ur = nn.Linear(128, 128, bias=False)
        self.wh = nn.Linear(128, 128); self.uh = nn.Linear(128, 128, bias=False)
        self.motion = nn.Linear(128, 2); self.prepare = nn.Linear(128, 1); self.commit = nn.Linear(128, 1)
        self.prediction_mean = nn.Linear(128, 4); self.prediction_cholesky = nn.Linear(128, 10)
        self.service_q = nn.Linear(128, 20); self.link_mean = nn.Linear(128, 2)
        self.link_sigma = nn.Linear(128, 2); self.missing = nn.Linear(128, 1)
        self.snapshot_encoder = nn.Linear(18, 128); self.snapshot_bridge = nn.Linear(256, 128)
        self.flex_delta = nn.Linear(128, 128); self.flex_alpha = nn.Linear(128, 1)
        self.flex_readiness = nn.Linear(128, 1); self.flex_beta = nn.Linear(128, 1)
        self.critic1 = nn.Linear(58, 128); self.critic2 = nn.Linear(128, 128); self.critic_out = nn.Linear(128, 1)
        self.log_std = nn.Parameter(torch.full((4,), -0.5))

    def encode(self, observation: torch.Tensor) -> torch.Tensor:
        return torch.tanh(self.encoder2(torch.tanh(self.encoder1(observation))))

    def gru_step(self, encoded: torch.Tensor, previous: torch.Tensor) -> torch.Tensor:
        z = torch.sigmoid(self.wz(encoded) + self.uz(previous))
        r = torch.sigmoid(self.wr(encoded) + self.ur(previous))
        candidate = torch.tanh(self.wh(encoded) + self.uh(r * previous))
        return (1.0 - z) * previous + z * candidate

    def heads(self, hidden: torch.Tensor) -> dict[str, torch.Tensor]:
        return {
            "motion": self.motion(hidden), "prepare": self.prepare(hidden), "commit": self.commit(hidden),
            "prediction_mean": self.prediction_mean(hidden), "prediction_cholesky": self.prediction_cholesky(hidden),
            "service_q": self.service_q(hidden), "link_mean": self.link_mean(hidden),
            "link_sigma": F.softplus(self.link_sigma(hidden)) + 1e-3, "missing": self.missing(hidden),
            "flex_delta": 0.25 * torch.tanh(self.flex_delta(hidden)),
            "flex_alpha": 1.0 + torch.tanh(self.flex_alpha(hidden)),
            "flex_readiness": 0.25 * torch.tanh(self.flex_readiness(hidden)),
            "flex_beta": torch.tanh(self.flex_beta(hidden)),
        }

    def critic(self, value: torch.Tensor) -> torch.Tensor:
        return self.critic_out(torch.tanh(self.critic2(torch.tanh(self.critic1(value))))).squeeze(-1)

    def replay(
        self,
        observation: torch.Tensor,
        initial_hidden: torch.Tensor,
        snapshot: torch.Tensor,
        snapshot_mask: torch.Tensor,
        reset_mask: torch.Tensor,
        promotion_mask: torch.Tensor | None = None,
        promotion_alpha: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        if observation.ndim != 4 or observation.shape[1:] != (64, 4, 54):
            raise TrainingBoundaryError("replay observation must be [fragments,64,4,54]")
        fragments = observation.shape[0]
        if initial_hidden.shape != (fragments, 4, 128):
            raise TrainingBoundaryError("fragment hidden shape differs")
        hidden = initial_hidden
        if promotion_mask is None:
            promotion_mask = torch.zeros((fragments, 64), dtype=torch.bool, device=observation.device)
        if promotion_alpha is None:
            promotion_alpha = torch.ones((fragments, 64), dtype=observation.dtype, device=observation.device)
        histories: list[torch.Tensor] = []
        for tick in range(64):
            hidden = hidden * reset_mask[:, tick, None, None]
            promote = promotion_mask[:, tick]
            if torch.any(promote):
                old = hidden
                alpha = promotion_alpha[:, tick, None]
                promoted = torch.clamp(alpha * old[:, 1] + (1.0 - alpha) * old[:, 0], -1.0, 1.0)
                edited = old.clone()
                edited[:, 0] = torch.where(promote[:, None], promoted, old[:, 0])
                edited[:, 3] = torch.where(promote[:, None], old[:, 0], old[:, 3])
                hidden = edited
            active = snapshot_mask[:, tick]
            if torch.any(active):
                encoded_snapshot = torch.tanh(self.snapshot_encoder(snapshot[:, tick]))
                standby = hidden[:, 1]
                bridged = torch.tanh(self.snapshot_bridge(torch.cat((standby, encoded_snapshot), dim=-1)))
                hidden = hidden.clone(); hidden[:, 1] = torch.where(active[:, None], bridged, standby)
            encoded = self.encode(observation[:, tick].reshape(-1, 54))
            hidden = self.gru_step(encoded, hidden.reshape(-1, 128)).reshape(fragments, 4, 128)
            histories.append(hidden)
        states = torch.stack(histories, dim=1)
        return states, self.heads(states)


@dataclass
class WelfordState:
    count: int
    mean: torch.Tensor
    m2: torch.Tensor

    @classmethod
    def empty(cls, width: int) -> "WelfordState":
        return cls(0, torch.zeros(width, dtype=torch.float64), torch.zeros(width, dtype=torch.float64))

    def update(self, rows: torch.Tensor, present: torch.Tensor | None = None) -> None:
        values = rows.detach().to(torch.float64).reshape(-1, rows.shape[-1])
        if present is not None:
            mask = present.detach().reshape(-1).to(torch.bool)
            values = values[mask]
        for row in values:
            self.count += 1
            delta = row - self.mean
            self.mean += delta / self.count
            self.m2 += delta * (row - self.mean)

    def normalized(self, rows: torch.Tensor) -> torch.Tensor:
        variance = torch.ones_like(self.mean) if self.count < 2 else self.m2 / (self.count - 1)
        return torch.clamp((rows - self.mean.to(rows)) / torch.sqrt(variance.to(rows) + 1e-8), -10.0, 10.0)


def deterministic_test_initialize(model: ExactPolicyGraph) -> None:
    with torch.no_grad():
        for ordinal, parameter in enumerate(model.parameters()):
            if parameter is model.log_std:
                continue
            values = torch.arange(parameter.numel(), dtype=parameter.dtype).reshape(parameter.shape)
            parameter.copy_(0.01 * torch.sin(0.013 * values + 0.17 * ordinal))
        for layer in (model.flex_delta, model.flex_alpha, model.flex_readiness, model.flex_beta):
            layer.weight.zero_(); layer.bias.zero_()


def _digest(value: object) -> str:
    stream = io.BytesIO(); torch.save(value, stream); return hashlib.sha256(stream.getvalue()).hexdigest()


def _test_fragments() -> tuple[torch.Tensor, ...]:
    fragment = torch.arange(8, dtype=torch.float32)[:, None, None, None]
    tick = torch.arange(64, dtype=torch.float32)[None, :, None, None]
    copy = torch.arange(4, dtype=torch.float32)[None, None, :, None]
    feature = torch.arange(54, dtype=torch.float32)[None, None, None, :]
    observation = torch.sin(fragment * 0.07 + tick * 0.009 + copy * 0.13 + feature * 0.003)
    critic = torch.cos(torch.arange(512, dtype=torch.float32)[:, None] * 0.01 + torch.arange(58)[None] * 0.005)
    snapshot = torch.sin(fragment[:, :, 0, :1] * 0.1 + tick[:, :, 0, :1] * 0.02 + torch.arange(18)[None, None] * 0.03)
    snapshot_mask = torch.zeros((8, 64), dtype=torch.bool); snapshot_mask[:, ::16] = True
    reset_mask = torch.ones((8, 64), dtype=torch.float32)
    action = torch.tanh(torch.arange(512, dtype=torch.float32)[:, None] * torch.tensor([0.001, -0.001, 0.0007, -0.0007]))
    reward = ((torch.arange(512) % 17) < 11).to(torch.float32)
    return observation, critic, snapshot, snapshot_mask, reset_mask, action, reward


def run_result_blind_training_seam() -> dict[str, object]:
    previous_threads = torch.get_num_threads(); torch.set_num_threads(1); started = time.perf_counter()
    try:
        model = ExactPolicyGraph(); deterministic_test_initialize(model)
        matrix_parameters = [parameter for name, parameter in model.named_parameters() if parameter.ndim >= 2 and "flex_" not in name]
        matrix_ids = {id(parameter) for parameter in matrix_parameters}
        other_parameters = [parameter for parameter in model.parameters() if id(parameter) not in matrix_ids]
        optimizer = torch.optim.AdamW(
            [{"params": matrix_parameters, "weight_decay": 1e-4}, {"params": other_parameters, "weight_decay": 0.0}],
            lr=3e-4, betas=(0.9, 0.999), eps=1e-8,
        )
        observation, critic, snapshot, snapshot_mask, reset_mask, action, reward = _test_fragments()
        initial_hidden = torch.zeros((8, 4, 128), dtype=torch.float32)
        states, heads = model.replay(observation, initial_hidden, snapshot, snapshot_mask, reset_mask)
        authoritative = torch.stack((heads["motion"][:, :, 0, 0], heads["motion"][:, :, 0, 1], heads["motion"][:, :, 1, 0], heads["motion"][:, :, 1, 1]), dim=-1).reshape(512, 4)
        mean = 3.0 * torch.tanh(authoritative); log_std = torch.clamp(model.log_std, -5.0, 1.0)
        log_prob = -0.5 * ((((action - mean) / torch.exp(log_std)) ** 2) + 2 * log_std + math.log(2 * math.pi)).sum(-1)
        advantage = reward - reward.mean(); advantage = advantage / torch.clamp(advantage.std(unbiased=False), min=1e-8)
        policy_loss = -(log_prob * advantage).mean()
        value = model.critic(critic); target = reward
        value_loss = (value - target).square().mean()
        q_logits = heads["service_q"][:, :, 1].reshape(512, 20)
        q_labels = ((torch.arange(512)[:, None] + torch.arange(20)[None]) % 7 < 4).to(torch.float32)
        passive = F.binary_cross_entropy_with_logits(q_logits, q_labels)
        loss = policy_loss + 0.5 * value_loss + 0.1 * passive
        optimizer.zero_grad(set_to_none=True); loss.backward(); gradient_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 0.5); optimizer.step()
        actor_welford = WelfordState.empty(54); actor_welford.update(observation)
        snapshot_welford = WelfordState.empty(18); snapshot_welford.update(snapshot, snapshot_mask)
        critic_welford = WelfordState.empty(58); critic_welford.update(critic)
        state = {
            "model": model.state_dict(), "optimizer": optimizer.state_dict(),
            "welford": {"actor": actor_welford, "snapshot": snapshot_welford, "critic": critic_welford},
            "update": 1, "evaluation_checkpoint": False,
        }
        buffer = io.BytesIO(); torch.save(state, buffer)
        return {
            "schema": "DISH_RBHR_R05_PRODUCTION_TRAINING_SEAM_V1",
            "test_only": True, "scientific_model": False, "checkpoint_created": False,
            "question_relevant_output": False, "fragments": 8, "fragment_ticks": 64,
            "copies": 4, "transitions": 512, "loss_finite": math.isfinite(float(loss.detach())),
            "gradient_norm_finite": math.isfinite(float(gradient_norm)),
            "flex_zero_exact": bool(torch.count_nonzero(heads["flex_delta"]) == 0 and torch.count_nonzero(heads["flex_alpha"] - 1.0) == 0 and torch.count_nonzero(heads["flex_readiness"]) == 0 and torch.count_nonzero(heads["flex_beta"]) == 0),
            "model_state_sha256": _digest(model.state_dict()), "optimizer_state_sha256": _digest(optimizer.state_dict()),
            "checkpoint_resume_projected_bytes_per_job": len(buffer.getvalue()),
            "wall_seconds": time.perf_counter() - started,
        }
    finally:
        torch.set_num_threads(previous_threads)


def _bernoulli_log_prob(logit: torch.Tensor, outcome: torch.Tensor) -> torch.Tensor:
    return -F.binary_cross_entropy_with_logits(logit, outcome, reduction="none")


def _synthetic_complete_update() -> dict[str, torch.Tensor]:
    transition = torch.arange(4_096, dtype=torch.float32)
    fragment = transition.div(64, rounding_mode="floor")
    tick = transition.remainder(64)
    copy = torch.arange(4, dtype=torch.float32)
    feature = torch.arange(54, dtype=torch.float32)
    observation = torch.sin(
        fragment[:, None, None] * 0.021 + tick[:, None, None] * 0.009
        + copy[None, :, None] * 0.13 + feature[None, None, :] * 0.003
    ).reshape(64, 64, 4, 54)
    critic_feature = torch.arange(58, dtype=torch.float32)
    critic = torch.cos(transition[:, None] * 0.007 + critic_feature[None] * 0.005)
    snapshot = torch.sin(fragment[:, None] * 0.031 + tick[:, None] * 0.011 + torch.arange(18)[None] * 0.017).reshape(64, 64, 18)
    snapshot_mask = torch.zeros((64, 64), dtype=torch.bool); snapshot_mask[:, ::16] = True
    promotion_mask = torch.zeros((64, 64), dtype=torch.bool); promotion_mask[::7, 33] = True
    promotion_alpha = torch.ones((64, 64), dtype=torch.float32)
    reset_mask = torch.ones((64, 64), dtype=torch.float32); reset_mask[::11, 0] = 0.0
    lane = torch.arange(32)[:, None]
    offset = torch.arange(128)[None, :]
    periods = torch.where((lane % 4) < 2, torch.tensor(4), torch.tensor(12))
    renew_lane = (offset % periods) == 0
    renew = renew_lane.reshape(32, 2, 64).reshape(64, 64)
    prepare_mask = renew & ((torch.arange(64)[:, None] + torch.arange(64)[None]) % 3 == 0)
    commit_mask = renew & ((torch.arange(64)[:, None] + torch.arange(64)[None]) % 5 == 0)
    action = torch.tanh(torch.stack((transition * 0.001, -transition * 0.001, transition * 0.0007, -transition * 0.0007), dim=-1)).reshape(64, 64, 4)
    prepare_outcome = ((transition.reshape(64, 64) % 7) < 3).to(torch.float32)
    commit_outcome = ((transition.reshape(64, 64) % 11) < 4).to(torch.float32)
    reward = ((torch.arange(32)[:, None] * 3 + torch.arange(128)[None]) % 17 < 11).to(torch.float32)
    done = torch.zeros((32, 128), dtype=torch.float32); done[:, 119] = 1.0
    target = torch.sin(transition[:, None] * 0.004 + torch.arange(4)[None] * 0.1)
    links = torch.cos(transition[:, None] * 0.006 + torch.arange(2)[None] * 0.2)
    missing = ((transition % 13) < 3).to(torch.float32)
    q_labels = ((transition[:, None] + torch.arange(20)[None]) % 7 < 4).to(torch.float32)
    return locals()


def _gae(
    reward: torch.Tensor,
    value: torch.Tensor,
    done: torch.Tensor,
    bootstrap: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    gamma = math.exp(-0.1 / 20.0)
    advantage = torch.zeros_like(reward)
    running = torch.zeros(reward.shape[0], dtype=reward.dtype)
    next_value = bootstrap
    for tick in range(127, -1, -1):
        live = 1.0 - done[:, tick]
        delta = reward[:, tick] + gamma * live * next_value - value[:, tick]
        running = delta + gamma * 0.95 * live * running
        advantage[:, tick] = running
        next_value = value[:, tick]
    return advantage, advantage + value


def _arm_policy_terms(
    arm: str,
    motion_log_prob: torch.Tensor,
    motion_entropy: torch.Tensor,
    prepare_log_prob: torch.Tensor,
    prepare_entropy: torch.Tensor,
    commit_log_prob: torch.Tensor,
    commit_entropy: torch.Tensor,
    renew: torch.Tensor,
    prepare_mask: torch.Tensor,
    commit_mask: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    if arm not in ("STRUCTURED", "FLEX", "NEVER", "IMMEDIATE", "HYSTERESIS"):
        raise TrainingBoundaryError("arm is not registered")
    active = renew.to(motion_log_prob.dtype)
    log_prob = motion_log_prob * active
    entropy = motion_entropy * active
    if arm in ("STRUCTURED", "FLEX", "NEVER"):
        log_prob = log_prob + prepare_log_prob * prepare_mask + commit_log_prob * commit_mask
        entropy = entropy + prepare_entropy * prepare_mask + commit_entropy * commit_mask
    return log_prob, entropy, active


def arm_mask_inventory() -> dict[str, dict[str, int]]:
    data = _synthetic_complete_update()
    renew = int(data["renew"].sum())
    prepare = int(data["prepare_mask"].sum())
    commit = int(data["commit_mask"].sum())
    return {
        arm: {
            "motion_gaussian_dimensions": 4 * renew,
            "prepare_bernoulli": prepare if arm in ("STRUCTURED", "FLEX", "NEVER") else 0,
            "commit_bernoulli": commit if arm in ("STRUCTURED", "FLEX", "NEVER") else 0,
            "noop_bernoulli": commit if arm == "NEVER" else 0,
            "transfer_authority": 0 if arm == "NEVER" else commit,
        }
        for arm in ("STRUCTURED", "FLEX", "NEVER", "IMMEDIATE", "HYSTERESIS")
    }


def run_full_4096_dry_update(
    *,
    arm: str = "STRUCTURED",
    fragments: Mapping[str, torch.Tensor] | None = None,
    source_label: str = "SYNTHETIC_TEST_FIXTURE",
) -> dict[str, object]:
    """Execute one complete result-blind frozen update without publishing state."""

    previous_threads = torch.get_num_threads(); torch.set_num_threads(1); started = time.perf_counter()
    try:
        data = dict(_synthetic_complete_update() if fragments is None else fragments)
        required = {
            "observation", "critic", "snapshot", "snapshot_mask", "promotion_mask",
            "promotion_alpha", "reset_mask", "renew", "prepare_mask", "commit_mask",
            "action", "prepare_outcome", "commit_outcome", "reward", "done", "target",
            "links", "missing", "q_labels",
        }
        if not required.issubset(data):
            raise TrainingBoundaryError(
                f"complete 4096-fragment schema differs: missing={sorted(required-set(data))}"
            )
        data = {name: data[name] for name in required}
        model = ExactPolicyGraph(); deterministic_test_initialize(model)
        matrix_parameters = [parameter for name, parameter in model.named_parameters() if parameter.ndim >= 2 and "flex_" not in name]
        matrix_ids = {id(parameter) for parameter in matrix_parameters}
        other_parameters = [parameter for parameter in model.parameters() if id(parameter) not in matrix_ids]
        optimizer = torch.optim.AdamW(
            [{"params": matrix_parameters, "weight_decay": 1e-4}, {"params": other_parameters, "weight_decay": 0.0}],
            lr=3e-4, betas=(0.9, 0.999), eps=1e-8,
        )
        initial_hidden = torch.zeros((64, 4, 128), dtype=torch.float32)
        with torch.no_grad():
            old_states, old_heads = model.replay(
                data["observation"], initial_hidden, data["snapshot"], data["snapshot_mask"],
                data["reset_mask"], data["promotion_mask"], data["promotion_alpha"],
            )
            old_value_flat = model.critic(data["critic"])
            old_value = old_value_flat.reshape(32, 128)
            bootstrap = old_value[:, -1].clone()
            advantage_raw, returns = _gae(data["reward"], old_value, data["done"], bootstrap)
            advantage_fragment = advantage_raw.reshape(32, 2, 64).reshape(64, 64)
            active_advantage = advantage_fragment[data["renew"]]
            policy_advantage = torch.zeros_like(advantage_fragment)
            if active_advantage.numel() and active_advantage.std(unbiased=False) >= 1e-8:
                policy_advantage[data["renew"]] = (active_advantage - active_advantage.mean()) / active_advantage.std(unbiased=False)
            old_motion = old_heads["motion"]
            old_mean = 3.0 * torch.tanh(torch.stack((old_motion[:, :, 0, 0], old_motion[:, :, 0, 1], old_motion[:, :, 1, 0], old_motion[:, :, 1, 1]), dim=-1))
            ell = torch.clamp(model.log_std, -5.0, 1.0)
            old_motion_lp = -0.5 * ((((data["action"] - old_mean) / torch.exp(ell)) ** 2) + 2 * ell + math.log(2 * math.pi)).sum(-1)
            old_motion_entropy = torch.full_like(old_motion_lp, float((ell + 0.5 * math.log(2 * math.pi * math.e)).sum()))
            old_prepare = old_heads["prepare"][:, :, 0, 0]
            old_commit = old_heads["commit"][:, :, 1, 0]
            old_prepare_lp = _bernoulli_log_prob(old_prepare, data["prepare_outcome"])
            old_commit_lp = _bernoulli_log_prob(old_commit, data["commit_outcome"])
            old_prepare_entropy = torch.distributions.Bernoulli(logits=old_prepare).entropy()
            old_commit_entropy = torch.distributions.Bernoulli(logits=old_commit).entropy()
            old_log_prob, _, _ = _arm_policy_terms(
                arm, old_motion_lp, old_motion_entropy, old_prepare_lp, old_prepare_entropy,
                old_commit_lp, old_commit_entropy, data["renew"], data["prepare_mask"], data["commit_mask"],
            )
        losses: list[float] = []
        gradient_norms: list[float] = []
        optimizer_steps = 0
        for epoch in range(4):
            scores = torch.sin(torch.arange(64, dtype=torch.float64) * 0.619 + epoch * 0.37)
            order = torch.argsort(scores, stable=True)
            for minibatch in range(8):
                selected = order[minibatch * 8:(minibatch + 1) * 8]
                states, heads = model.replay(
                    data["observation"][selected], initial_hidden[selected], data["snapshot"][selected],
                    data["snapshot_mask"][selected], data["reset_mask"][selected],
                    data["promotion_mask"][selected], data["promotion_alpha"][selected],
                )
                motion = heads["motion"]
                mean = 3.0 * torch.tanh(torch.stack((motion[:, :, 0, 0], motion[:, :, 0, 1], motion[:, :, 1, 0], motion[:, :, 1, 1]), dim=-1))
                ell = torch.clamp(model.log_std, -5.0, 1.0)
                motion_lp = -0.5 * ((((data["action"][selected] - mean) / torch.exp(ell)) ** 2) + 2 * ell + math.log(2 * math.pi)).sum(-1)
                motion_entropy = torch.ones_like(motion_lp) * (ell + 0.5 * math.log(2 * math.pi * math.e)).sum()
                prepare_logit = heads["prepare"][:, :, 0, 0]
                commit_logit = heads["commit"][:, :, 1, 0]
                prepare_lp = _bernoulli_log_prob(prepare_logit, data["prepare_outcome"][selected])
                commit_lp = _bernoulli_log_prob(commit_logit, data["commit_outcome"][selected])
                prepare_entropy = torch.distributions.Bernoulli(logits=prepare_logit).entropy()
                commit_entropy = torch.distributions.Bernoulli(logits=commit_logit).entropy()
                log_prob, entropy, active = _arm_policy_terms(
                    arm, motion_lp, motion_entropy, prepare_lp, prepare_entropy, commit_lp, commit_entropy,
                    data["renew"][selected], data["prepare_mask"][selected], data["commit_mask"][selected],
                )
                ratio = torch.exp(log_prob - old_log_prob[selected])
                adv = policy_advantage[selected]
                eligible = active.bool()
                unclipped = ratio[eligible] * adv[eligible]
                clipped = torch.clamp(ratio[eligible], 0.8, 1.2) * adv[eligible]
                policy_loss = -torch.minimum(unclipped, clipped).mean()
                flat_indices = torch.cat([torch.arange(int(fragment) * 64, int(fragment) * 64 + 64) for fragment in selected])
                value = model.critic(data["critic"][flat_indices]).reshape(8, 64)
                old_v = old_value.reshape(64, 64)[selected]
                ret = returns.reshape(32, 2, 64).reshape(64, 64)[selected]
                value_clipped = old_v + torch.clamp(value - old_v, -0.2, 0.2)
                value_loss = torch.maximum((value - ret) ** 2, (value_clipped - ret) ** 2).mean()
                state_flat = states.reshape(512, 4, 128)
                prediction_mean = heads["prediction_mean"].reshape(512, 4, 4)
                target_label = data["target"][flat_indices]
                target_loss = (prediction_mean - target_label[:, None]).square().mean()
                link_mean = heads["link_mean"].reshape(512, 4, 2)
                link_sigma = heads["link_sigma"].reshape(512, 4, 2)
                link_label = data["links"][flat_indices][:, None]
                link_loss = (0.5 * (((link_label - link_mean) / link_sigma) ** 2 + 2 * torch.log(link_sigma) + math.log(2 * math.pi))).mean()
                missing_logit = heads["missing"].reshape(512, 4)
                missing_label = data["missing"][flat_indices][:, None].expand(-1, 4)
                missing_loss = F.binary_cross_entropy_with_logits(missing_logit, missing_label)
                q_logits = heads["service_q"][:, :, 1].reshape(512, 20)
                q_loss = F.binary_cross_entropy_with_logits(q_logits, data["q_labels"][flat_indices])
                auxiliary = (target_loss + link_loss + missing_loss + q_loss) / 4.0
                loss = policy_loss + 0.5 * value_loss - 0.01 * entropy[eligible].mean() + 0.1 * auxiliary
                optimizer.zero_grad(set_to_none=True); loss.backward()
                norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 0.5); optimizer.step()
                losses.append(float(loss.detach())); gradient_norms.append(float(norm)); optimizer_steps += 1
        actor_welford = WelfordState.empty(54); actor_welford.update(data["observation"])
        snapshot_welford = WelfordState.empty(18); snapshot_welford.update(data["snapshot"], data["snapshot_mask"])
        critic_welford = WelfordState.empty(58); critic_welford.update(data["critic"])
        checkpoint = {
            "model": model.state_dict(), "optimizer": optimizer.state_dict(),
            "welford": {"actor": actor_welford, "snapshot": snapshot_welford, "critic": critic_welford},
            "update": 1, "evaluation_checkpoint": False,
        }
        stream = io.BytesIO(); torch.save(checkpoint, stream); checkpoint_bytes = stream.getvalue()
        restored = torch.load(io.BytesIO(checkpoint_bytes), map_location="cpu", weights_only=False)
        return {
            "schema": "DISH_RBHR_R05_PRODUCTION_FULL_4096_DRY_UPDATE_V1",
            "test_only": True, "scientific_model": False, "checkpoint_created": False,
            "fragment_source": source_label,
            "question_relevant_output": False, "arm": arm, "transitions": 4_096,
            "fragments": 64, "epochs": 4, "minibatches_per_epoch": 8,
            "optimizer_steps": optimizer_steps, "losses_finite": all(math.isfinite(value) for value in losses),
            "gradient_norms_finite": all(math.isfinite(value) for value in gradient_norms),
            "ratio_clip": 0.20, "value_clip": 0.20, "gae_lambda": 0.95,
            "gamma": math.exp(-0.1 / 20.0), "checkpoint_resume_bytes": len(checkpoint_bytes),
            "checkpoint_resume_equal": _digest(restored) == _digest(checkpoint),
            "model_state_sha256": _digest(model.state_dict()), "optimizer_state_sha256": _digest(optimizer.state_dict()),
            "welford_counts": {"actor": actor_welford.count, "snapshot": snapshot_welford.count, "critic": critic_welford.count},
            "wall_seconds": time.perf_counter() - started,
        }
    finally:
        torch.set_num_threads(previous_threads)


__all__ = ["ExactPolicyGraph", "TrainingBoundaryError", "WelfordState", "arm_mask_inventory", "run_full_4096_dry_update", "run_result_blind_training_seam"]
