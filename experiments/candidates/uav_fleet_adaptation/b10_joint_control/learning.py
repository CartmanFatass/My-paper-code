"""B10 warm joint motion/transmission actor and fixed B04 team PPO update."""
from collections.abc import Mapping, Sequence
from numbers import Integral, Real

import numpy as np
import torch
from torch import nn

from experiments.candidates.uav_fleet_adaptation.b02.model import Student
from experiments.candidates.uav_fleet_adaptation.b04_native_development import learning as b04

COUNT_KEYS = ("actor_optimizer_steps", "critic_optimizer_steps", "actor_replay_rows",
              "critic_replay_rows", "density_identity_rows")
ADAM_OPTIONS = dict(lr=3e-4, betas=(.9, .999), eps=1e-8, weight_decay=0,
                    amsgrad=False, foreach=False, fused=False)


def _seed(seed):
    if isinstance(seed, (bool, np.bool_)) or not isinstance(seed, Integral):
        raise ValueError("constructor seed must be an integer")
    return int(seed)


def _tensor(value, shape, dtype, name):
    if (not isinstance(value, torch.Tensor) or tuple(value.shape) != tuple(shape)
            or value.dtype != dtype or value.device.type != "cpu"):
        raise ValueError(f"{name} requires CPU {dtype} shape {tuple(shape)}")
    if not torch.isfinite(value).all():
        raise FloatingPointError(f"nonfinite {name}")
    return value


class JointActor(nn.Module):
    """Private trainable body and duplicated ON27/OFF27 warm output rows."""
    def __init__(self, parent, seed=0):
        super().__init__()
        if not isinstance(parent, Student):
            raise ValueError("joint actor requires the original Student architecture")
        expected = ((128, 114), (128,), (128, 128), (128,), (27, 128), (27,))
        parameters = list(parent.parameters())
        if len(parameters) != 6:
            raise ValueError("parent must have exactly six parameter tensors")
        for value, shape in zip(parameters, expected):
            _tensor(value, shape, torch.float32, "parent parameter")
        if (len(parent.network) != 5 or not isinstance(parent.network[1], nn.ReLU)
                or not isinstance(parent.network[3], nn.ReLU)):
            raise ValueError("parent must retain its original two-ReLU body")
        seed = _seed(seed)
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(seed)
            self.network = nn.Sequential(nn.Linear(114, 128, device="cpu", dtype=torch.float32), nn.ReLU(),
                                         nn.Linear(128, 128, device="cpu", dtype=torch.float32), nn.ReLU(),
                                         nn.Linear(128, 54, device="cpu", dtype=torch.float32))
        with torch.no_grad():
            for index in (0, 2):
                self.network[index].weight.copy_(parent.network[index].weight)
                self.network[index].bias.copy_(parent.network[index].bias)
            self.network[4].weight.copy_(parent.network[4].weight.repeat(2, 1))
            self.network[4].bias.copy_(parent.network[4].bias.repeat(2))
        if sum(p.numel() for p in self.parameters()) != 38198:
            raise AssertionError("joint actor parameter contract changed")

    def forward(self, features):
        features = _tensor(features, (1, 114), torch.float32, "actor features")
        b04._finite_parameters(list(self.parameters()))
        # Canonical private row storage in collection and replay, including
        # NumPy-backed or strided inputs; retain all114 FP32 coordinates.
        output = self.network(features.clone(memory_format=torch.contiguous_format))
        return _tensor(output, (1, 54), torch.float32, "raw actor logits")


def make_actor(parent, seed=0):
    return JointActor(parent, seed=seed)


class Critic146(nn.Module):
    """Training-only CTDE136 plus old mask5 and eligible one-hot5."""
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(nn.Linear(146, 128, device="cpu", dtype=torch.float32), nn.Tanh(),
                                     nn.Linear(128, 128, device="cpu", dtype=torch.float32), nn.Tanh(),
                                     nn.Linear(128, 1, device="cpu", dtype=torch.float32))

    def forward(self, features):
        if not isinstance(features, torch.Tensor) or not features.ndim or features.shape[-1] != 146:
            raise ValueError("critic features require last dimension146")
        _tensor(features, features.shape, torch.float32, "critic features")
        b04._finite_parameters(list(self.parameters()))
        result = self.network(features).squeeze(-1)
        return _tensor(result, features.shape[:-1], torch.float32, "critic values")


def fresh_critic(seed):
    seed = _seed(seed)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        critic = Critic146().cpu().float()
    if sum(p.numel() for p in critic.parameters()) != 35457:
        raise AssertionError("critic parameter contract changed")
    return critic


def make_optimizers(actor, critic):
    if not isinstance(actor, JointActor) or not isinstance(critic, Critic146):
        raise ValueError("optimizers require JointActor and Critic146")
    for model in (actor, critic):
        b04._finite_parameters(list(model.parameters()))
    return b04.make_optimizers(actor, critic)


def _prior_valid(prior, eligible):
    preferred_on = (prior[..., 0] == .9) & (prior[..., 1] == .1)
    preferred_off = (prior[..., 0] == .1) & (prior[..., 1] == .9)
    sentinel = (prior == 1).all(-1)
    if not torch.where(eligible, preferred_on | preferred_off, sentinel).all():
        raise ValueError("prior must be frozen .9/.1 or .1/.9, and [1,1] when ineligible")


def torch_probabilities(raw_logits, prior, eligible):
    """Differentiable FP64 density; no gradient or normalization fit for prior."""
    if not isinstance(raw_logits, torch.Tensor) or not raw_logits.ndim or raw_logits.shape[-1] != 54:
        raise ValueError("raw logits require last dimension54")
    prefix = raw_logits.shape[:-1]
    _tensor(raw_logits, (*prefix, 54), torch.float32, "raw logits")
    _tensor(prior, (*prefix, 2), torch.float64, "prior")
    _tensor(eligible, prefix, torch.bool, "eligible")
    prior = prior.detach()
    _prior_valid(prior, eligible)
    on = torch.ones_like(raw_logits[..., :27], dtype=torch.bool)
    active = torch.cat((on, eligible[..., None].expand(*prefix, 27)), -1)
    z = raw_logits.double()
    shift = z.masked_fill(~active, -float("inf")).max(-1, keepdim=True).values
    # Inactive exponentials receive zero arguments before exp; finite masked
    # OFF logits cannot overflow or underflow the ON-only law.
    weights = torch.where(active, torch.exp(torch.where(active, z-shift, torch.zeros_like(z))), 0.)
    on_prior = torch.where(eligible, prior[..., 0], torch.ones_like(prior[..., 0]))
    off_prior = torch.where(eligible, prior[..., 1], torch.zeros_like(prior[..., 1]))
    factor = torch.cat((on_prior[..., None].expand(*prefix, 27),
                        off_prior[..., None].expand(*prefix, 27)), -1)
    weights = weights * factor
    probabilities = weights / weights.sum(-1, keepdim=True)
    if not torch.isfinite(probabilities).all():
        raise FloatingPointError("nonfinite joint density")
    return probabilities


def joint_probabilities(raw_logits, prior, eligible_bool):
    """One NumPy row, same shifted-exponential ON27/OFF27 law as replay."""
    raw = np.asarray(raw_logits)
    p = np.asarray(prior)
    if raw.shape != (54,) or raw.dtype != np.float32 or p.shape != (2,) or p.dtype != np.float64:
        raise ValueError("joint density requires FP32 logits54 and FP64 prior2")
    if not isinstance(eligible_bool, (bool, np.bool_)):
        raise ValueError("eligibility must be bool")
    if not np.isfinite(raw).all() or not np.isfinite(p).all():
        raise FloatingPointError("nonfinite raw logits/prior")
    if eligible_bool:
        if not (np.array_equal(p, [.9, .1]) or np.array_equal(p, [.1, .9])):
            raise ValueError("eligible prior must be frozen .9/.1 or .1/.9")
        z = raw.astype(np.float64)
        weights = np.exp(z-z.max()) * np.repeat(p, 27)
    else:
        if not np.array_equal(p, [1., 1.]):
            raise ValueError("ineligible prior requires unused [1,1] sentinel")
        z = raw[:27].astype(np.float64)
        weights = np.concatenate((np.exp(z-z.max()), np.zeros(27, dtype=np.float64)))
    probabilities = weights / weights.sum(dtype=np.float64)
    if not np.isfinite(probabilities).all():
        raise FloatingPointError("nonfinite joint density")
    return probabilities


def categorical_index54(probabilities, uniform):
    p = np.asarray(probabilities)
    if (p.shape != (54,) or p.dtype != np.float64 or not np.isfinite(p).all()
            or np.any(p < 0) or np.any(p > 1) or abs(p.sum(dtype=np.float64)-1) > 1e-12):
        raise ValueError("invalid FP64 categorical54 probabilities")
    if (isinstance(uniform, (bool, np.bool_)) or not isinstance(uniform, Real)
            or not np.isfinite(uniform) or not 0 <= uniform < 1):
        raise ValueError("uniform must be finite in [0,1)")
    cdf = np.minimum(np.cumsum(p, dtype=np.float64), 1.)
    # Close rounding at the last supported category, preserving masked zeros.
    cdf[np.flatnonzero(p > 0)[-1]:] = 1.
    choice = int(np.searchsorted(cdf, float(uniform), side="right"))
    if not 0 <= choice < 54 or p[choice] <= 0:
        raise FloatingPointError("CDF selected zero joint mass")
    return choice


def _rollout(episodes, horizon):
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon <= 0 or horizon % 4:
        raise ValueError("horizon must be a positive multiple of four")
    if not isinstance(episodes, Sequence) or len(episodes) != 2:
        raise ValueError("exactly two complete episodes required")
    d = horizon // 4
    contract = dict(features=((d, 5, 114), torch.float32), logits=((d, 5, 54), torch.float32),
                    prior=((d, 5, 2), torch.float64), eligible=((d, 5), torch.bool),
                    probabilities=((d, 5, 54), torch.float64), action_index=((d, 5), torch.int64),
                    logp=((d, 5), torch.float64), critic_features=((d, 146), torch.float32),
                    values=((d,), torch.float32), macro_rewards=((d,), torch.float64))
    rows = {key: [] for key in contract}
    for episode in episodes:
        if not isinstance(episode, Mapping):
            raise ValueError("episode must be a mapping")
        for key, (shape, dtype) in contract.items():
            if key not in episode:
                raise ValueError(f"missing episode field {key}")
            value = torch.as_tensor(episode[key]).detach()
            rows[key].append(_tensor(value, shape, dtype, key).clone())
    rollout = {key: torch.stack(values) for key, values in rows.items()}
    actions, p, eligible = rollout["action_index"], rollout["probabilities"], rollout["eligible"]
    _prior_valid(rollout["prior"], eligible)
    if ((actions < 0) | (actions >= 54) | ((actions >= 27) & ~eligible)).any():
        raise ValueError("action_index requires [0,54), with ON only when ineligible")
    if ((p < 0) | (p > 1)).any() or (p.sum(-1)-1).abs().max() > 1e-12:
        raise ValueError("invalid saved probabilities")
    if (p[..., 27:][~eligible] != 0).any():
        raise ValueError("ineligible saved OFF probability must be exactly zero")
    chosen = p.gather(-1, actions[..., None]).squeeze(-1)
    if (chosen <= 0).any() or (chosen.log()-rollout["logp"]).abs().max() > 1e-10:
        raise ValueError("saved chosen probability and independent logp disagree")
    return rollout, chosen


def _movement(model, initial):
    value = b04._norm([p-p0 for p, p0 in zip(model.parameters(), initial)])
    return value if np.isfinite(value) else None


def update_group(actor, critic, actor_optimizer, critic_optimizer, episodes, counts, *, horizon=256, live_record=None):
    """Two frozen collected episodes; four team-loss epochs, actor step first."""
    if not isinstance(actor, JointActor) or not isinstance(critic, Critic146):
        raise ValueError("group requires JointActor and Critic146")
    result = {} if live_record is None else live_record
    if any(key in result for key in ("epochs", "initial_identity", "target_summary", "advantage_summary")):
        raise ValueError("live group diagnostics must start empty")
    result.update(status="INCOMPLETE", epochs=[])
    ap, cp = list(actor.parameters()), list(critic.parameters())
    initial_actor, initial_critic = [p.detach().clone() for p in ap], [p.detach().clone() for p in cp]
    try:
        if set(ap) & set(cp) or len(ap) != 6 or len(cp) != 6:
            raise ValueError("actor and critic require separate six-tensor parameter sets")
        for optimizer, parameters in ((actor_optimizer, ap), (critic_optimizer, cp)):
            if not isinstance(optimizer, torch.optim.Adam):
                raise ValueError("separate Adam optimizers required")
            owned = [p for group in optimizer.param_groups for p in group["params"]]
            if len(owned) != len(parameters) or set(owned) != set(parameters):
                raise ValueError("optimizer must own exactly its model parameters")
            if any(group.get(key) != value for group in optimizer.param_groups for key, value in ADAM_OPTIONS.items()):
                raise ValueError("optimizer conventions differ from B04")
            if any(group.get(key, False) for group in optimizer.param_groups
                   for key in ("maximize", "differentiable", "capturable", "decoupled_weight_decay")):
                raise ValueError("optimizer must preserve ordinary B04 Adam semantics")
            b04._finite_parameters(parameters)
        for key in COUNT_KEYS:
            value = counts.get(key, 0)
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or value < 0:
                raise ValueError(f"invalid integer count {key}")
        rollout, old_chosen = _rollout(episodes, horizon)
        rewards = rollout["macro_rewards"].float()
        targets = (rewards.flip(-1).cumsum(-1).flip(-1)/horizon).detach()
        raw_advantage = targets-rollout["values"]
        advantages = ((raw_advantage-raw_advantage.mean())/(raw_advantage.std(unbiased=False)+1e-8)).detach()
        if not torch.isfinite(targets).all() or not torch.isfinite(advantages).all():
            raise FloatingPointError("nonfinite targets/advantages")
        result.update(target_summary=b04._summary(targets), advantage_summary=b04._summary(advantages))
        actor.train(); critic.train()
        for epoch in range(4):
            outputs = []
            for features in rollout["features"].reshape(-1, 114):
                outputs.append(actor(features.reshape(1, 114))[0])
                b04._add(counts, "actor_replay_rows", 1)
            logits = torch.stack(outputs).reshape(rollout["logits"].shape)
            probabilities = torch_probabilities(logits, rollout["prior"], rollout["eligible"])
            chosen = probabilities.gather(-1, rollout["action_index"][..., None]).squeeze(-1)
            ratio, logp = chosen/old_chosen, chosen.log()
            if not torch.isfinite(ratio).all() or not torch.isfinite(logp).all():
                raise FloatingPointError("nonfinite replay density")
            if epoch == 0:
                b04._add(counts, "density_identity_rows", ratio.numel())
                identity = dict(logits_exact=bool(torch.equal(logits.detach(), rollout["logits"])),
                                max_probability_abs=float((probabilities.detach()-rollout["probabilities"]).abs().max()),
                                max_chosen_logp_abs=float((logp.detach()-rollout["logp"]).abs().max()),
                                max_ratio_from_one=float((ratio.detach()-1).abs().max()), rows=ratio.numel())
                result["initial_identity"] = identity
                if (not identity["logits_exact"] or identity["max_probability_abs"] > 5e-14
                        or identity["max_chosen_logp_abs"] > 1e-10 or identity["max_ratio_from_one"] > 1e-10):
                    raise ValueError("initial replay density identity failed")
            advantage = advantages[..., None]
            actor_loss = -torch.minimum(ratio*advantage, ratio.clamp(.8, 1.2)*advantage).sum(-1).mean()
            if not torch.isfinite(actor_loss):
                raise FloatingPointError("nonfinite actor loss")
            record = dict(epoch=epoch, actor_loss=float(actor_loss.detach()),
                          actor_step_completed=False, critic_step_completed=False,
                          ratio_min=float(ratio.detach().min()), ratio_max=float(ratio.detach().max()),
                          ratio_mean=float(ratio.detach().mean()),
                          clip_fraction=float(((ratio.detach() < .8) | (ratio.detach() > 1.2)).double().mean()),
                          old_logp_mean=float(rollout["logp"].mean()), new_logp_mean=float(logp.detach().mean()))
            result["epochs"].append(record)
            actor_optimizer.zero_grad(set_to_none=True)
            actor_loss.backward()
            norm = torch.nn.utils.clip_grad_norm_(ap, .5, error_if_nonfinite=True, foreach=False)
            record.update(actor_grad_norm=float(norm), actor_clipped_grad_norm=b04._norm([p.grad for p in ap if p.grad is not None]))
            actor_optimizer.step()
            b04._add(counts, "actor_optimizer_steps", 1)
            record.update(actor_step_completed=True, actor_movement_l2=_movement(actor, initial_actor),
                          actor_optimizer_step_values=b04._step_values(actor_optimizer, ap))
            b04._finite_parameters(ap)
            b04._finite_parameters(cp)
            predicted = critic(rollout["critic_features"])
            b04._add(counts, "critic_replay_rows", targets.numel())
            critic_loss = .5*(predicted-targets).square().mean()
            if not torch.isfinite(critic_loss):
                raise FloatingPointError("nonfinite critic loss")
            record["critic_loss"] = float(critic_loss.detach())
            critic_optimizer.zero_grad(set_to_none=True)
            critic_loss.backward()
            norm = torch.nn.utils.clip_grad_norm_(cp, .5, error_if_nonfinite=True, foreach=False)
            record.update(critic_grad_norm=float(norm), critic_clipped_grad_norm=b04._norm([p.grad for p in cp if p.grad is not None]))
            critic_optimizer.step()
            b04._add(counts, "critic_optimizer_steps", 1)
            record.update(critic_step_completed=True, critic_movement_l2=_movement(critic, initial_critic),
                          critic_optimizer_step_values=b04._step_values(critic_optimizer, cp))
            b04._finite_parameters(cp)
        result["status"] = "COMPLETE"
        return result
    finally:
        result.update(actor_optimizer_step_values=(b04._step_values(actor_optimizer, ap)
                                                  if isinstance(actor_optimizer, torch.optim.Optimizer) else []),
                      critic_optimizer_step_values=(b04._step_values(critic_optimizer, cp)
                                                   if isinstance(critic_optimizer, torch.optim.Optimizer) else []),
                      actor_movement_l2=_movement(actor, initial_actor), critic_movement_l2=_movement(critic, initial_critic),
                      completed_counts={key: counts.get(key, 0) for key in COUNT_KEYS})
