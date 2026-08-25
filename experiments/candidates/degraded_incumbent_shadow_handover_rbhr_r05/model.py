"""Batched synthetic model/replay seam for DISH r05 Gate B.

The module constructs only deterministic TEST tensors.  It never creates or
serializes a scientific model or checkpoint.
"""

from __future__ import annotations

import hashlib
import io
import math
import time

import torch
from torch import nn
from torch.nn import functional as F


class GateBModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.encoder1 = nn.Linear(54, 128)
        self.encoder2 = nn.Linear(128, 128)
        self.gru = nn.GRUCell(128, 128)
        self.motion = nn.Linear(128, 2)
        self.prepare = nn.Linear(128, 1)
        self.commit = nn.Linear(128, 1)
        self.prediction = nn.Linear(128, 14)
        self.service_q = nn.Linear(128, 20)
        self.snapshot = nn.Linear(18, 128)
        self.bridge = nn.Linear(256, 128)
        self.flex_delta = nn.Linear(128, 128)
        self.flex_scalars = nn.Linear(128, 3)
        self.critic1 = nn.Linear(58, 128)
        self.critic2 = nn.Linear(128, 128)
        self.critic_out = nn.Linear(128, 1)
        self.log_std = nn.Parameter(torch.full((4,), -0.5))
        self._deterministic_initialize()

    def _deterministic_initialize(self) -> None:
        with torch.no_grad():
            for ordinal, parameter in enumerate(self.parameters()):
                if parameter is self.log_std:
                    continue
                values = torch.arange(parameter.numel(), dtype=parameter.dtype).reshape(parameter.shape)
                parameter.copy_(0.01 * torch.sin(values * 0.017 + ordinal * 0.13))
            self.flex_delta.weight.zero_(); self.flex_delta.bias.zero_()
            self.flex_scalars.weight.zero_(); self.flex_scalars.bias.zero_()

    def actor_step(self, observation: torch.Tensor, hidden: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        encoded = torch.tanh(self.encoder2(torch.tanh(self.encoder1(observation))))
        current = self.gru(encoded, hidden)
        heads = torch.cat((self.motion(current), self.prepare(current), self.commit(current), self.service_q(current)), dim=-1)
        return current, heads

    def critic(self, value: torch.Tensor) -> torch.Tensor:
        return self.critic_out(torch.tanh(self.critic2(torch.tanh(self.critic1(value))))).squeeze(-1)

    def flex_residuals(self, hidden: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        delta = 0.25 * torch.tanh(self.flex_delta(hidden))
        raw = self.flex_scalars(hidden)
        alpha = 1.0 + torch.tanh(raw[..., 0])
        readiness = 0.25 * torch.tanh(raw[..., 1])
        beta = torch.tanh(raw[..., 2])
        return delta, alpha, readiness, beta


def _digest_state(value: object) -> str:
    buffer = io.BytesIO()
    torch.save(value, buffer)
    return hashlib.sha256(buffer.getvalue()).hexdigest()


def _synthetic_tensors() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    transition = torch.arange(4096, dtype=torch.float32)
    feature = torch.arange(54, dtype=torch.float32)
    copy = torch.arange(4, dtype=torch.float32)
    observation = torch.sin(transition[:, None, None] * 0.003 + copy[None, :, None] * 0.17 + feature[None, None, :] * 0.011)
    critic_feature = torch.arange(58, dtype=torch.float32)
    critic = torch.cos(transition[:, None] * 0.002 + critic_feature[None, :] * 0.013)
    action = torch.tanh(torch.stack((transition * 0.001, transition * -0.001, transition * 0.0007, transition * -0.0007), dim=-1))
    reward = ((transition.to(torch.int64) % 17) < 11).to(torch.float32)
    return observation, critic, action, reward


def run_synthetic_update() -> dict[str, object]:
    previous_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    started = time.perf_counter()
    try:
        model = GateBModel()
        optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, betas=(0.9, 0.999), eps=1e-8, weight_decay=1e-4)
        observations, critic_input, actions, rewards = _synthetic_tensors()
        losses: list[float] = []
        for epoch in range(4):
            order = torch.roll(torch.arange(64), shifts=epoch * 7)
            for batch in range(8):
                selected = order[batch*8:(batch+1)*8]
                indices = torch.cat([torch.arange(int(fragment)*64, int(fragment)*64+64) for fragment in selected])
                obs = observations[indices].reshape(8, 64, 4, 54)
                hidden = torch.zeros((8 * 4, 128), dtype=torch.float32)
                replayed: list[torch.Tensor] = []
                for tick_offset in range(64):
                    # Synthetic accepted-snapshot assimilation is recomputed
                    # with current parameters inside the fragment.  It is a
                    # TEST seam, not a production message or scientific tape.
                    if tick_offset % 16 == 0:
                        snapshot_fields = obs[:, tick_offset, 1, :18]
                        encoded_snapshot = torch.tanh(model.snapshot(snapshot_fields))
                        standby = hidden.reshape(8, 4, 128)[:, 1]
                        bridged = torch.tanh(model.bridge(torch.cat((standby, encoded_snapshot), dim=-1)))
                        hidden_view = hidden.reshape(8, 4, 128).clone()
                        hidden_view[:, 1] = bridged
                        hidden = hidden_view.reshape(8 * 4, 128)
                    hidden, tick_heads = model.actor_step(obs[:, tick_offset].reshape(-1, 54), hidden)
                    replayed.append(tick_heads.reshape(8, 4, -1))
                heads = torch.stack(replayed, dim=1).reshape(512, 4, -1)
                mean = 3.0 * torch.tanh(torch.stack((heads[:,0,0], heads[:,0,1], heads[:,1,0], heads[:,1,1]), dim=-1))
                log_std = torch.clamp(model.log_std, -5.0, 1.0)
                log_prob = -0.5 * (((actions[indices]-mean)/torch.exp(log_std))**2 + 2.0*log_std + math.log(2.0*math.pi)).sum(dim=-1)
                advantage = rewards[indices] - rewards[indices].mean()
                advantage = advantage / torch.clamp(advantage.std(unbiased=False), min=1e-8)
                policy_loss = -(log_prob * advantage).mean()
                value = model.critic(critic_input[indices])
                value_loss = (value - rewards[indices]).square().mean()
                q_logits = heads[:,1,4:24]
                q_labels = ((indices[:,None] + torch.arange(20)[None,:]) % 7 < 4).to(torch.float32)
                passive_loss = F.binary_cross_entropy_with_logits(q_logits, q_labels)
                loss = policy_loss + 0.5 * value_loss + 0.1 * passive_loss
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 0.5)
                optimizer.step()
                losses.append(float(loss.detach()))
        # Exact result-blind Welford seam over the synthetic actor tensor.
        flat = observations.reshape(-1, 54).to(torch.float64)
        welford = {"count": int(flat.shape[0]), "mean": flat.mean(dim=0), "m2": ((flat-flat.mean(dim=0))**2).sum(dim=0)}
        elapsed = time.perf_counter() - started
        return {
            "schema": "DISH_RBHR_R05_GATE_B_SYNTHETIC_UPDATE_V1",
            "test_only": True,
            "scientific_model": False,
            "question_relevant_output": False,
            "lanes": 32,
            "transitions": 4096,
            "epochs": 4,
            "minibatches_per_epoch": 8,
            "optimizer_steps": 32,
            "loss_count": len(losses),
            "losses_finite": all(math.isfinite(value) for value in losses),
            "wall_seconds": elapsed,
            "model_state_digest": _digest_state(model.state_dict()),
            "optimizer_state_digest": _digest_state(optimizer.state_dict()),
            "welford_state_digest": _digest_state(welford),
        }
    finally:
        torch.set_num_threads(previous_threads)
