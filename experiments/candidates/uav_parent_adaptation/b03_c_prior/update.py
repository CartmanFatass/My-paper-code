"""The fixed two-episode, four-full-epoch categorical PPO update for B03."""

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.learner import (
    clipped_policy_loss, returns_to_go,
)

from .policy import categorical_terms


_SHAPES = dict(context=(64, 5, 120), c_index=(64, 5), critic=(64, 136),
               action=(64, 5), logp=(64, 5), value=(64,), reward=(64,))


def _rollout(episodes):
    if len(episodes) != 2:
        raise ValueError('B03 update requires two complete 64-clock episodes')
    for episode in episodes:
        for key, shape in _SHAPES.items():
            if key not in episode or tuple(episode[key].shape) != shape:
                raise ValueError(f'{key} must have shape {shape}')
    rollout = {key: torch.stack([torch.as_tensor(ep[key]).detach() for ep in episodes])
               for key in _SHAPES}
    for key in ('context', 'critic', 'logp', 'value', 'reward'):
        rollout[key] = rollout[key].to(dtype=torch.float32, device='cpu')
        if not torch.isfinite(rollout[key]).all():
            raise FloatingPointError(f'nonfinite rollout {key}')
    for key in ('c_index', 'action'):
        if rollout[key].is_floating_point() or rollout[key].is_complex() or rollout[key].dtype == torch.bool:
            raise ValueError(f'{key} must contain integer indices')
        rollout[key] = rollout[key].to(dtype=torch.long, device='cpu')
        if (rollout[key] < 0).any() or (rollout[key] >= 27).any():
            raise ValueError(f'{key} indices must be in [0,27)')
    return rollout


def _targets_advantages(rewards, collected_values):
    targets = (returns_to_go(rewards) / 256.0).detach()
    raw = targets - collected_values.detach()
    advantages = ((raw - raw.mean()) / (raw.std(unbiased=False) + 1e-8)).detach()
    return targets, advantages


def _finite_parameters(parameters, where):
    if not all(torch.isfinite(param).all() for param in parameters):
        raise FloatingPointError(f'nonfinite parameters {where}')


def _add(counts, key, value):
    counts[key] = counts.get(key, 0) + value


def _norm(tensors):
    return float(torch.linalg.vector_norm(torch.cat([t.detach().reshape(-1) for t in tensors])))


def _grad_norm(parameters):
    gradients = [p.grad for p in parameters if p.grad is not None]
    return _norm(gradients) if gradients else 0.0


def update(actor, critic, aopt, copt, episodes, counts, emit=None):
    rollout = _rollout(episodes)
    targets, advantages = _targets_advantages(rollout['reward'], rollout['value'])
    actor_parameters = list(actor.parameters())
    critic_parameters = list(critic.parameters())
    groups = {'actor_table': [actor.table], 'actor_mlp': list(actor.mlp.parameters()),
              'actor_hidden': list(actor.mlp[0].parameters()) + list(actor.mlp[2].parameters()),
              'actor_head': list(actor.mlp[4].parameters()), 'critic': critic_parameters}
    initial = {name: [p.detach().clone() for p in params] for name, params in groups.items()}
    mask = torch.ones_like(rollout['action'], dtype=torch.bool)
    records = []
    _add(counts, 'ppo_rollouts', 1)
    for epoch in range(4):
        _finite_parameters(actor_parameters, 'before actor forward')
        _finite_parameters(critic_parameters, 'before critic forward')
        _add(counts, 'actor_forward_calls', 1)
        _add(counts, 'actor_forward_rows', 2 * 64 * 5)
        _add(counts, 'actor_replay_rows', 2 * 64 * 5)
        logits = actor(rollout['context'], rollout['c_index'])
        _add(counts, 'critic_forward_calls', 1)
        _add(counts, 'critic_forward_rows', 2 * 64)
        _add(counts, 'critic_replay_rows', 2 * 64)
        predicted = critic(rollout['critic'])
        if not torch.isfinite(predicted).all():
            raise FloatingPointError('nonfinite PPO critic forward')
        logp, entropy = categorical_terms(logits, rollout['action'])
        policy_loss = clipped_policy_loss(logp, rollout['logp'], advantages, mask)
        entropy_mean = entropy.sum(dim=-1).mean()
        actor_loss = policy_loss - .01 * entropy_mean
        value_mse = (predicted - targets).square().mean()
        critic_loss = .5 * value_mse
        if not torch.isfinite(actor_loss) or not torch.isfinite(critic_loss):
            raise FloatingPointError('nonfinite PPO loss')
        with torch.no_grad():
            ratio = (logp - rollout['logp']).exp()
            record = dict(epoch=epoch, loss=float(actor_loss + critic_loss),
                          actor_loss=float(actor_loss), critic_loss=float(critic_loss),
                          policy_loss=float(policy_loss), value_loss=float(value_mse),
                          entropy=float(entropy_mean),
                          approx_kl=float((rollout['logp'] - logp).mean()),
                          clip_fraction=float(((ratio < .8) | (ratio > 1.2)).float().mean()),
                          ratio_min=float(ratio.min()), ratio_max=float(ratio.max()),
                          target_mean=float(targets.mean()),
                          advantage_mean=float(advantages.mean()),
                          advantage_std=float(advantages.std(unbiased=False)),
                          actor_table_lr=float(aopt.param_groups[0]['lr']),
                          actor_mlp_lr=float(aopt.param_groups[1]['lr']),
                          critic_lr=float(copt.param_groups[0]['lr']))
        aopt.zero_grad()
        copt.zero_grad()
        actor_loss.backward()
        critic_loss.backward()
        for name, params in groups.items():
            record[name + '_grad_norm'] = _grad_norm(params)
        actor_grad_norm = torch.nn.utils.clip_grad_norm_(actor_parameters, .5)
        critic_grad_norm = torch.nn.utils.clip_grad_norm_(critic_parameters, .5)
        if not torch.isfinite(actor_grad_norm) or not torch.isfinite(critic_grad_norm):
            raise FloatingPointError('nonfinite PPO gradient')
        record.update(actor_grad_norm=float(actor_grad_norm),
                      critic_grad_norm=float(critic_grad_norm),
                      actor_clipped_grad_norm=_grad_norm(actor_parameters),
                      critic_clipped_grad_norm=_grad_norm(critic_parameters))
        aopt.step()
        _add(counts, 'actor_optimizer_steps', 1)
        _add(counts, 'optimizer_steps', 1)
        _finite_parameters(actor_parameters, 'after actor step')
        copt.step()
        _add(counts, 'critic_optimizer_steps', 1)
        _add(counts, 'optimizer_steps', 1)
        _finite_parameters(critic_parameters, 'after critic step')
        for name, params in groups.items():
            record[name + '_param_norm'] = _norm(params)
            record[name + '_movement_from_update_start'] = _norm(
                [p.detach() - start for p, start in zip(params, initial[name])])
        record['actor_param_norm'] = _norm(actor_parameters)
        records.append(record)
        if emit is not None:
            emit(record)
    return records
