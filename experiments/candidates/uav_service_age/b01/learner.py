"""One finite, fixed-slot PPO fit; no observation normalizer or evaluation update."""

import hashlib
import math

import numpy as np
import torch
from torch import nn

REPORT_SLOTS = 64
INIT_SEED = 29313000
TRAIN_CHOICE_KEY = 29314000
EVAL_CHOICE_KEY = 29315000
EPOCHS = 4
LEARNING_RATE = 3e-4
CLIP = .2
ENTROPY = .01
GRAD_NORM = .5


def innovations(world_seed, *, training):
    key = TRAIN_CHOICE_KEY if training else EVAL_CHOICE_KEY
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(
        [key, int(world_seed)]))).random(REPORT_SLOTS)


def finite_returns(rewards):
    rewards = np.asarray(rewards, dtype=np.float64)
    if rewards.shape != (REPORT_SLOTS,) or not np.isfinite(rewards).all():
        raise ValueError('finite returns require all64 report rewards')
    return np.cumsum(rewards[::-1], dtype=np.float64)[::-1].copy()


def parameter_digest(network):
    digest = hashlib.sha256()
    for name, value in network.state_dict().items():
        array = value.detach().cpu().contiguous().numpy()
        digest.update(name.encode('utf-8'))
        digest.update(str(array.dtype).encode('ascii'))
        digest.update(str(array.shape).encode('ascii'))
        digest.update(array.tobytes())
    return digest.hexdigest()


def flat_parameters(network):
    return torch.cat([value.detach().reshape(-1).cpu() for value in network.parameters()])


def network(input_dim, outputs, *, actor):
    result = nn.Sequential(nn.Linear(input_dim, 64), nn.Tanh(), nn.Linear(64, outputs))
    nn.init.orthogonal_(result[0].weight, gain=math.sqrt(2))
    nn.init.zeros_(result[0].bias)
    if actor:
        nn.init.zeros_(result[2].weight)
    else:
        nn.init.orthogonal_(result[2].weight, gain=1.)
    nn.init.zeros_(result[2].bias)
    return result.float()


def actor_objective(logits, actions, old_logp, advantages, sampled):
    """Forced/alias rows carry zero actor/entropy weight, always divided by64."""
    if len(logits) != REPORT_SLOTS:
        raise ValueError('PPO denominator is the fixed64 report slots')
    distribution = torch.distributions.Categorical(logits=logits)
    logp = distribution.log_prob(actions)
    ratio = torch.exp(logp - old_logp)
    surrogate = torch.minimum(ratio * advantages,
                              torch.clamp(ratio, 1 - CLIP, 1 + CLIP) * advantages)
    weight = sampled.to(logits.dtype)
    policy_loss = -(surrogate * weight).sum() / REPORT_SLOTS
    entropy = (distribution.entropy() * weight).sum() / REPORT_SLOTS
    return policy_loss - ENTROPY * entropy, policy_loss, entropy


class Learner:
    def __init__(self, input_dim, seed=INIT_SEED):
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(int(seed))
            self.actor = network(input_dim, 2, actor=True)
            self.critic = network(input_dim, 1, actor=False)
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=LEARNING_RATE,
                                               betas=(.9, .999), eps=1e-5, weight_decay=0)
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(), lr=LEARNING_RATE,
                                                betas=(.9, .999), eps=1e-5, weight_decay=0)
        self.actor_updates = self.critic_updates = self.episodes_updated = 0
        self.initial_actor = flat_parameters(self.actor).clone()
        self.initial_critic = flat_parameters(self.critic).clone()
        self.input_dim = input_dim

    @torch.no_grad()
    def probabilities(self, features):
        features = np.asarray(features, dtype=np.float32)
        if features.shape != (self.input_dim,) or not np.isfinite(features).all():
            raise ValueError('selector feature shape or finiteness')
        return torch.softmax(self.actor(torch.from_numpy(features.copy())), dim=-1).numpy()

    @torch.no_grad()
    def values(self, features):
        features = np.asarray(features, dtype=np.float32)
        if features.shape != (REPORT_SLOTS, self.input_dim) or not np.isfinite(features).all():
            raise ValueError('critic requires complete causal64-row features')
        return self.critic(torch.from_numpy(features.copy())).squeeze(-1).numpy()

    def update(self, features, choices, old_logp, sampled, rewards):
        features = np.asarray(features, dtype=np.float32)
        sampled = np.asarray(sampled, dtype=bool)
        choices = np.asarray(choices, dtype=np.int64)
        old_logp = np.asarray(old_logp, dtype=np.float32)
        if (features.shape != (REPORT_SLOTS, self.input_dim) or sampled.shape != (REPORT_SLOTS,)
                or choices.shape != (REPORT_SLOTS,) or old_logp.shape != (REPORT_SLOTS,)
                or not np.isfinite(features).all() or not np.isfinite(old_logp[sampled]).all()
                or not np.isin(choices[sampled], (0, 1)).all()):
            raise ValueError('incomplete or invalid PPO report rows')
        # Forced rows have no sampled likelihood. Safe placeholders are multiplied by0.
        actions = torch.from_numpy(np.where(sampled, choices, 0))
        old = torch.from_numpy(np.where(sampled, old_logp, 0.).astype(np.float32))
        mask = torch.from_numpy(sampled.copy())
        x = torch.from_numpy(features.copy())
        targets64 = finite_returns(rewards)
        target = torch.from_numpy(targets64.astype(np.float32))
        before_actor = parameter_digest(self.actor)
        before_critic = parameter_digest(self.critic)
        old_values = self.values(features).copy()
        advantage = target - torch.from_numpy(old_values)
        epoch_rows = []
        for epoch in range(EPOCHS):
            actor_loss = policy_loss = entropy = actor_grad = None
            if sampled.any():
                self.actor_optimizer.zero_grad(set_to_none=True)
                loss, surrogate, ent = actor_objective(self.actor(x), actions, old,
                                                     advantage, mask)
                if not torch.isfinite(loss):
                    raise FloatingPointError('nonfinite actor loss')
                loss.backward()
                norm = nn.utils.clip_grad_norm_(self.actor.parameters(), GRAD_NORM,
                                                 error_if_nonfinite=True)
                self.actor_optimizer.step()
                self.actor_updates += 1
                actor_loss, policy_loss, entropy, actor_grad = map(float, (loss.detach(), surrogate.detach(),
                                                                         ent.detach(), norm.detach()))
            self.critic_optimizer.zero_grad(set_to_none=True)
            value = self.critic(x).squeeze(-1)
            critic_loss = .5 * (value - target).square().mean()
            if not torch.isfinite(critic_loss):
                raise FloatingPointError('nonfinite critic loss')
            critic_loss.backward()
            critic_grad = nn.utils.clip_grad_norm_(self.critic.parameters(), GRAD_NORM,
                                                   error_if_nonfinite=True)
            self.critic_optimizer.step()
            self.critic_updates += 1
            epoch_rows.append(dict(epoch=epoch, actor_loss=actor_loss, policy_loss=policy_loss,
                                   entropy=entropy, actor_gradient_norm=actor_grad,
                                   critic_loss=float(critic_loss.detach()),
                                   critic_gradient_norm=float(critic_grad.detach())))
        self.episodes_updated += 1
        return dict(sampled_slots=int(sampled.sum()), denominator=REPORT_SLOTS,
                    actor_updates=EPOCHS if sampled.any() else 0, critic_updates=EPOCHS,
                    before_actor_sha256=before_actor, before_critic_sha256=before_critic,
                    after_actor_sha256=parameter_digest(self.actor),
                    after_critic_sha256=parameter_digest(self.critic),
                    actor_displacement=float(torch.linalg.vector_norm(flat_parameters(self.actor) - self.initial_actor)),
                    critic_displacement=float(torch.linalg.vector_norm(flat_parameters(self.critic) - self.initial_critic)),
                    epochs=epoch_rows), dict(old_values=old_values, returns=targets64,
                                             advantages=advantage.numpy().copy())

    def state(self):
        return dict(actor=self.actor.state_dict(), critic=self.critic.state_dict(),
                    input_dim=self.input_dim, actor_updates=self.actor_updates,
                    critic_updates=self.critic_updates, episodes_updated=self.episodes_updated,
                    actor_sha256=parameter_digest(self.actor), critic_sha256=parameter_digest(self.critic))
