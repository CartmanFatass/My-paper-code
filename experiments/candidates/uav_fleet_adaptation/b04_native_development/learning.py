"""B04's fixed two-complete-episode, four-epoch Student continuation.

The differentiable density is the nominal smooth FP64 categorical law; the
collector retains the original NumPy inverse-CDF finite-bit sampling law.
"""
from collections.abc import Mapping
from numbers import Real

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.policy import Critic


_COUNT_KEYS = ("actor_optimizer_steps", "critic_optimizer_steps",
               "actor_replay_rows", "critic_replay_rows", "density_identity_rows")


def fresh_critic(seed):
    """Initialize the existing critic without consuming the caller's RNG."""
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(int(seed))
        critic = Critic().cpu().float()
    if sum(p.numel() for p in critic.parameters()) != 34177:
        raise AssertionError("critic parameter contract changed")
    return critic


def make_optimizers(actor, critic):
    """Discard inherited optimizer state; continue these two Adams across groups."""
    options = dict(lr=3e-4, betas=(.9, .999), eps=1e-8, weight_decay=0,
                   amsgrad=False, foreach=False, fused=False)
    return (torch.optim.Adam(actor.parameters(), **options),
            torch.optim.Adam(critic.parameters(), **options))


def _rollout(episodes, horizon):
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon <= 0 or horizon % 4:
        raise ValueError("horizon must be a positive multiple of four")
    if len(episodes) != 2:
        raise ValueError("exactly two complete episodes required")
    clocks = horizon // 4
    contract = {
        "features": ((clocks, 5, 114), torch.float32),
        "logits": ((clocks, 5, 27), torch.float32),
        "probabilities": ((clocks, 5, 27), torch.float64),
        "action_index": ((clocks, 5), torch.int64),
        "logp": ((clocks, 5), torch.float64),
        "critic_features": ((clocks, 136), torch.float32),
        "values": ((clocks,), torch.float32),
        "macro_rewards": ((clocks,), torch.float64),
    }
    rows = {key: [] for key in contract}
    for episode in episodes:
        if not isinstance(episode, Mapping):
            raise ValueError("episode must be a mapping")
        for key, (shape, dtype) in contract.items():
            if key not in episode:
                raise ValueError(f"missing episode field {key}")
            value = torch.as_tensor(episode[key]).detach()
            if value.shape != shape or value.dtype != dtype or value.device.type != "cpu":
                raise ValueError(f"{key} requires CPU {dtype} with shape {shape}")
            if not torch.isfinite(value).all():
                raise FloatingPointError(f"nonfinite {key}")
            rows[key].append(value)
    rollout = {key: torch.stack(values) for key, values in rows.items()}
    actions, probabilities = rollout["action_index"], rollout["probabilities"]
    if ((actions < 0) | (actions >= 27)).any():
        raise ValueError("action_index must be in [0,27)")
    if ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError("invalid saved probabilities")
    if (probabilities.sum(-1) - 1).abs().max() > 1e-12:
        raise ValueError("saved probabilities must sum to one")
    chosen = probabilities.gather(-1, actions[..., None]).squeeze(-1)
    if (chosen <= 0).any():
        raise ValueError("chosen saved probability must be positive")
    if (chosen.log() - rollout["logp"]).abs().max() > 1e-10:
        raise ValueError("saved chosen probability and independent logp disagree")
    return rollout, chosen


def _add(counts, key, amount):
    counts[key] = counts.get(key, 0) + amount


def _finite_parameters(parameters):
    for parameter in parameters:
        if parameter.dtype != torch.float32 or parameter.device.type != "cpu":
            raise ValueError("models require CPU FP32 parameters")
        if not parameter.requires_grad:
            raise ValueError("all actor and critic parameters must remain trainable")
        if not torch.isfinite(parameter).all():
            raise FloatingPointError("nonfinite parameters")


def _norm(values):
    return float(torch.linalg.vector_norm(torch.cat([value.detach().reshape(-1) for value in values])))


def _step_values(optimizer, parameters):
    return [float(optimizer.state.get(p, {}).get("step", 0)) for p in parameters]


def _summary(values):
    return dict(min=float(values.min()), max=float(values.max()), mean=float(values.mean()),
                std=float(values.std(unbiased=False)), dtype=str(values.dtype))


def update_group(actor, critic, actor_optimizer, critic_optimizer, episodes, counts, *, horizon=256, live_record=None):
    """Consume one fixed group, retaining counts for every completed paid operation.

    Saved tensors, targets and collected-value advantages stay detached and fixed
    throughout all four epochs. No sampling or additional diagnostic forward occurs.
    """
    result = {} if live_record is None else live_record
    if any(key in result for key in ("epochs", "initial_identity", "target_summary", "advantage_summary")):
        raise ValueError("live group diagnostics must start empty")
    result.update(status="INCOMPLETE", epochs=[])
    rollout, old_chosen = _rollout(episodes, horizon)
    for key in _COUNT_KEYS:
        value = counts.get(key, 0)
        if isinstance(value, bool) or not isinstance(value, Real) or not torch.isfinite(torch.tensor(value)).item() or value < 0:
            raise ValueError(f"invalid count {key}")
    actor_parameters, critic_parameters = list(actor.parameters()), list(critic.parameters())
    if not actor_parameters or not critic_parameters or set(actor_parameters) & set(critic_parameters):
        raise ValueError("actor and critic must have separate nonempty parameter sets")
    for optimizer, parameters in ((actor_optimizer, actor_parameters), (critic_optimizer, critic_parameters)):
        owned = [p for group in optimizer.param_groups for p in group["params"]]
        if len(owned) != len(parameters) or set(owned) != set(parameters):
            raise ValueError("optimizer must own exactly its model's parameters")
        _finite_parameters(parameters)
    initial_actor = [p.detach().clone() for p in actor_parameters]
    initial_critic = [p.detach().clone() for p in critic_parameters]
    rewards = rollout["macro_rewards"].float()
    targets = (rewards.flip(-1).cumsum(-1).flip(-1) / horizon).detach()
    raw_advantage = targets - rollout["values"]
    advantages = ((raw_advantage - raw_advantage.mean()) /
                  (raw_advantage.std(unbiased=False) + 1e-8)).detach()
    if not torch.isfinite(targets).all() or not torch.isfinite(advantages).all():
        raise FloatingPointError("nonfinite targets or advantages")
    actor.train()
    critic.train()
    result.update(target_summary=_summary(targets), advantage_summary=_summary(advantages))
    records = result["epochs"]
    identity = None
    for epoch in range(4):
        _finite_parameters(actor_parameters)
        outputs = []
        for feature in rollout["features"].reshape(-1, 114):
            output = actor(feature.reshape(1, 114))
            _add(counts, "actor_replay_rows", 1)
            if output.shape != (1, 27) or output.dtype != torch.float32:
                raise ValueError("actor replay must yield one FP32 27-logit row")
            outputs.append(output[0])
        logits = torch.stack(outputs).reshape(rollout["logits"].shape)
        if not torch.isfinite(logits).all():
            raise FloatingPointError("nonfinite actor replay")
        z = logits.double()
        weights = (z - z.max(-1, keepdim=True).values).exp()
        probabilities = weights / weights.sum(-1, keepdim=True)
        chosen = probabilities.gather(-1, rollout["action_index"][..., None]).squeeze(-1)
        ratio = chosen / old_chosen
        logp = chosen.log()
        if not torch.isfinite(probabilities).all() or not torch.isfinite(ratio).all() or not torch.isfinite(logp).all():
            raise FloatingPointError("nonfinite replay density")
        if epoch == 0:
            _add(counts, "density_identity_rows", ratio.numel())
            identity = dict(logits_exact=bool(torch.equal(logits.detach(), rollout["logits"])),
                            max_probability_abs=float((probabilities.detach() - rollout["probabilities"]).abs().max()),
                            max_chosen_logp_abs=float((logp.detach() - rollout["logp"]).abs().max()),
                            max_ratio_from_one=float((ratio.detach() - 1).abs().max()), rows=ratio.numel())
            result["initial_identity"] = identity
            if (not identity["logits_exact"] or identity["max_probability_abs"] > 5e-14 or
                    identity["max_chosen_logp_abs"] > 1e-10 or identity["max_ratio_from_one"] > 1e-10):
                raise ValueError("initial replay density identity failed")
        advantage = advantages[..., None]
        actor_loss = -torch.minimum(ratio * advantage, ratio.clamp(.8, 1.2) * advantage).sum(-1).mean()
        if not torch.isfinite(actor_loss):
            raise FloatingPointError("nonfinite actor loss")
        record = dict(epoch=epoch, actor_loss=float(actor_loss.detach()),
                      actor_step_completed=False, critic_step_completed=False,
                      ratio_min=float(ratio.detach().min()), ratio_max=float(ratio.detach().max()),
                      ratio_mean=float(ratio.detach().mean()),
                      clip_fraction=float(((ratio.detach() < .8) | (ratio.detach() > 1.2)).double().mean()),
                      old_logp_mean=float(rollout["logp"].mean()), new_logp_mean=float(logp.detach().mean()))
        records.append(record)
        actor_optimizer.zero_grad(set_to_none=True)
        actor_loss.backward()
        actor_norm = torch.nn.utils.clip_grad_norm_(actor_parameters, .5, error_if_nonfinite=True, foreach=False)
        record["actor_grad_norm"] = float(actor_norm)
        record["actor_clipped_grad_norm"] = _norm([p.grad for p in actor_parameters if p.grad is not None])
        actor_optimizer.step()
        _add(counts, "actor_optimizer_steps", 1)
        record.update(actor_step_completed=True,
                      actor_movement_l2=_norm([p - p0 for p, p0 in zip(actor_parameters, initial_actor)]),
                      actor_optimizer_step_values=_step_values(actor_optimizer, actor_parameters))
        _finite_parameters(actor_parameters)

        _finite_parameters(critic_parameters)
        predicted = critic(rollout["critic_features"])
        _add(counts, "critic_replay_rows", targets.numel())
        if predicted.shape != targets.shape or predicted.dtype != torch.float32:
            raise ValueError("critic replay must yield FP32 team-row values")
        critic_loss = .5 * (predicted - targets).square().mean()
        if not torch.isfinite(critic_loss):
            raise FloatingPointError("nonfinite critic loss")
        record["critic_loss"] = float(critic_loss.detach())
        critic_optimizer.zero_grad(set_to_none=True)
        critic_loss.backward()
        critic_norm = torch.nn.utils.clip_grad_norm_(critic_parameters, .5, error_if_nonfinite=True, foreach=False)
        record.update(critic_loss=float(critic_loss.detach()), critic_grad_norm=float(critic_norm),
                      critic_clipped_grad_norm=_norm([p.grad for p in critic_parameters if p.grad is not None]))
        critic_optimizer.step()
        _add(counts, "critic_optimizer_steps", 1)
        record["critic_step_completed"] = True
        _finite_parameters(critic_parameters)
        record.update(actor_movement_l2=_norm([p - p0 for p, p0 in zip(actor_parameters, initial_actor)]),
                      critic_movement_l2=_norm([p - p0 for p, p0 in zip(critic_parameters, initial_critic)]),
                      actor_optimizer_step_values=_step_values(actor_optimizer, actor_parameters),
                      critic_optimizer_step_values=_step_values(critic_optimizer, critic_parameters))
    result.update(status="COMPLETE", actor_optimizer_step_values=_step_values(actor_optimizer, actor_parameters),
                  critic_optimizer_step_values=_step_values(critic_optimizer, critic_parameters))
    return result
