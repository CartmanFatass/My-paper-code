"""Only the new S_eta critic and its explicit routing; Q32 uses frozen B01 code."""
import math
import time

import torch
from torch import nn

from experiments.candidates.tail_return_distributional_learning.trdl_b01 import learner as old

ARMS = ("S_eta", "Q32")


class EtaCritic(nn.Module):
    arm = "S_eta"

    def __init__(self, base):
        super().__init__()
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(base + 13)
            self.trunk = nn.Sequential(nn.Linear(138, 128), nn.Tanh(),
                                       nn.Linear(128, 128), nn.Tanh())
            torch.manual_seed(base + 14)
            self.head = nn.Linear(128, 1)

    def forward(self, context):
        return self.head(self.trunk(context)).squeeze(-1)


def models(master, arm):
    if arm not in ARMS:
        raise ValueError(arm)
    if arm == "Q32":
        return old.models(master, "Q32")
    actor, _ = old.models(master, "SCALAR")
    return actor, EtaCritic(100000 * master)


def action_generator(master, arm, evaluation_episode=None):
    if arm not in ARMS:
        raise ValueError(arm)
    if arm == "Q32":
        return old.action_generator(master, "Q32", evaluation_episode)
    base = 100000 * master
    offset = 21 if evaluation_episode is None else 3000 + evaluation_episode
    return old.generator(base + offset)


@torch.no_grad()
def frozen_batch(critic, episodes):
    if critic.arm == "Q32":
        return old.frozen_batch(critic, episodes)
    if critic.arm != "S_eta":
        raise ValueError(critic.arm)
    batch = {key: torch.stack([episode[key] for episode in episodes]).detach()
             for key in episodes[0]}
    returns = batch["G"]
    eta = returns.sort().values[math.ceil(old.ALPHA * len(episodes)) - 1].detach()
    scores = old.tail_score(returns, eta).detach()
    context = torch.cat((batch["critic"], eta.expand(*batch["critic"].shape[:2], 1)), -1)
    baseline = critic(context).detach()
    batch.update(critic_eta=context.detach(), eta=eta, scores=scores,
                 baseline=baseline, advantages=(scores[:, None] - baseline).detach())
    return batch


def update(actor, critic, optimizer, batch, check, counts, emit_update, chunk=old.CHUNK):
    if critic.arm == "Q32":
        return old.update(actor, critic, optimizer, batch, check, counts, emit_update, chunk)
    if critic.arm != "S_eta":
        raise ValueError(critic.arm)
    parameters = list(actor.parameters()) + list(critic.parameters())
    mask = torch.ones_like(batch["logp"], dtype=torch.bool)
    target = batch["scores"][:, None].expand_as(batch["baseline"])
    for epoch in range(old.EPOCHS):
        check()
        started = time.monotonic()
        mean, _ = old.recurrent_outputs(actor, batch, chunk)
        logp = old.tanh_log_prob(batch["u"], mean, actor.log_std)
        actor_loss = old.clipped_policy_loss(logp, batch["logp"], batch["advantages"], mask)
        prediction = critic(batch["critic_eta"])
        critic_loss = (prediction - target).square().mean()
        loss = actor_loss + .5 * critic_loss
        if not torch.isfinite(loss):
            raise FloatingPointError("nonfinite S_eta loss")
        optimizer.zero_grad()
        loss.backward()
        actor_grad = torch.stack([p.grad.norm() for p in actor.parameters()
                                  if p.grad is not None]).norm()
        critic_grad = torch.stack([p.grad.norm() for p in critic.parameters()
                                   if p.grad is not None]).norm()
        norm = torch.nn.utils.clip_grad_norm_(parameters, .5)
        if not torch.isfinite(norm):
            raise FloatingPointError("nonfinite S_eta gradient")
        check()
        counts["optimizer_attempts"] += 1
        optimizer.step()
        counts["optimizer_steps"] += 1
        if not all(torch.isfinite(p).all() for p in parameters):
            raise FloatingPointError("nonfinite S_eta parameter after Adam")
        emit_update(dict(epoch=epoch, actor_loss=float(actor_loss.detach()),
                         critic_loss=float(critic_loss.detach()), loss=float(loss.detach()),
                         grad_norm=float(norm), actor_grad_norm=float(actor_grad),
                         critic_grad_norm=float(critic_grad), eta=float(batch["eta"]),
                         strictly_negative_scores=int((batch["scores"] < 0).sum()),
                         optimizer_step=counts["optimizer_steps"],
                         wall_seconds=time.monotonic() - started))
