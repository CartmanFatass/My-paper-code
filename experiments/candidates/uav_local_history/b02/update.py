"""Fixed full-rollout categorical PPO update for B02."""

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.learner import (
    clipped_policy_loss, returns_to_go,
)

from .model import categorical_terms


_SHAPES = dict(context=(64, 5, 107), points=(64, 5, 64, 7),
               valid=(64, 5, 64), critic=(64, 136), action=(64, 5),
               logp=(64, 5), value=(64,), reward=(64,))


def _rollout(episodes):
    if len(episodes) != 2:
        raise ValueError('B02 update requires two complete 64-clock episodes')
    for episode in episodes:
        for key, shape in _SHAPES.items():
            if key not in episode or tuple(episode[key].shape) != shape:
                raise ValueError(f'{key} must have shape {shape}')
    rollout = {key: torch.stack([torch.as_tensor(ep[key]).detach() for ep in episodes])
               for key in _SHAPES}
    for key in ('context', 'points', 'critic', 'logp', 'value', 'reward'):
        rollout[key] = rollout[key].to(dtype=torch.float32, device='cpu')
    rollout['valid'] = rollout['valid'].to(dtype=torch.bool, device='cpu')
    rollout['action'] = rollout['action'].to(dtype=torch.long, device='cpu')
    if (not all(torch.isfinite(rollout[key]).all()
                for key in ('context', 'critic', 'logp', 'value', 'reward'))
            or not torch.isfinite(rollout['points'][rollout['valid']]).all()):
        raise FloatingPointError('nonfinite rollout input')
    if (rollout['action'] < 0).any() or (rollout['action'] >= 27).any():
        raise ValueError('action indices must be in [0,27)')
    return rollout


def _finite_parameters(parameters, where):
    if not all(torch.isfinite(param).all() for param in parameters):
        raise FloatingPointError(f'nonfinite parameters {where}')


def _add(counts, key, value):
    counts[key] = counts.get(key, 0) + value


def _norm(parameters):
    return float(torch.linalg.vector_norm(torch.cat([param.detach().reshape(-1)
                                                     for param in parameters])))


def _targets_advantages(rewards, collected_values):
    targets = (returns_to_go(rewards) / 256.0).detach()
    raw = targets - collected_values
    advantage = ((raw - raw.mean()) / (raw.std(unbiased=False) + 1e-8)).detach()
    return targets, advantage


def update(actor, critic, aopt, copt, episodes, counts, emit=None):
    rollout = _rollout(episodes)
    targets, advantage = _targets_advantages(rollout['reward'], rollout['value'])
    actor_parameters = list(actor.parameters())
    critic_parameters = list(critic.parameters())
    velocity_mask = torch.ones_like(rollout['action'], dtype=torch.bool)
    records = []
    _add(counts, 'ppo_rollouts', 1)
    for epoch in range(4):
        _finite_parameters(actor_parameters, 'before actor forward')
        _finite_parameters(critic_parameters, 'before critic forward')
        _add(counts, 'actor_forward_calls', 1)
        _add(counts, 'actor_forward_rows', 2 * 64 * 5)
        logits = actor(rollout['context'], rollout['points'], rollout['valid'])
        _add(counts, 'critic_forward_calls', 1)
        _add(counts, 'critic_forward_rows', 2 * 64)
        predicted = critic(rollout['critic'])
        if not torch.isfinite(logits).all() or not torch.isfinite(predicted).all():
            raise FloatingPointError('nonfinite PPO forward')
        logp, entropy = categorical_terms(logits, rollout['action'])
        if not torch.isfinite(logp).all() or not torch.isfinite(entropy).all():
            raise FloatingPointError('nonfinite categorical density')
        policy_loss = clipped_policy_loss(logp, rollout['logp'], advantage, velocity_mask)
        entropy_mean = entropy.sum(dim=-1).mean()
        actor_loss = policy_loss - 0.01 * entropy_mean
        value_mse = (predicted - targets).square().mean()
        critic_loss = 0.5 * value_mse
        if not torch.isfinite(actor_loss) or not torch.isfinite(critic_loss):
            raise FloatingPointError('nonfinite PPO loss')
        with torch.no_grad():
            ratio = (logp - rollout['logp']).exp()
            approx_kl = (rollout['logp'] - logp).mean()
            clip_fraction = ((ratio < 0.8) | (ratio > 1.2)).float().mean()
            record = dict(epoch=epoch, loss=float(actor_loss + critic_loss),
                          actor_loss=float(actor_loss), critic_loss=float(critic_loss),
                          policy_loss=float(policy_loss), value_loss=float(value_mse),
                          entropy=float(entropy_mean), approx_kl=float(approx_kl),
                          clip_fraction=float(clip_fraction))
        aopt.zero_grad()
        copt.zero_grad()
        actor_loss.backward()
        critic_loss.backward()
        actor_grad_norm = torch.nn.utils.clip_grad_norm_(actor_parameters, 0.5)
        critic_grad_norm = torch.nn.utils.clip_grad_norm_(critic_parameters, 0.5)
        if not torch.isfinite(actor_grad_norm) or not torch.isfinite(critic_grad_norm):
            raise FloatingPointError('nonfinite PPO gradient')
        _finite_parameters(actor_parameters, 'before actor step')
        _finite_parameters(critic_parameters, 'before critic step')
        aopt.step()
        _add(counts, 'actor_optimizer_steps', 1)
        _add(counts, 'optimizer_steps', 1)
        _finite_parameters(actor_parameters, 'after actor step')
        copt.step()
        _add(counts, 'critic_optimizer_steps', 1)
        _add(counts, 'optimizer_steps', 1)
        _finite_parameters(critic_parameters, 'after critic step')
        record.update(actor_grad_norm=float(actor_grad_norm),
                      critic_grad_norm=float(critic_grad_norm),
                      actor_param_norm=_norm(actor_parameters),
                      critic_param_norm=_norm(critic_parameters))
        records.append(record)
        if emit is not None:
            emit(record)
    return records
