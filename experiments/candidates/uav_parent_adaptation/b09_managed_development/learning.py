"""Head-only cached PPO and the pre-proposal native/S2 baseline.

The one-row FP32 Head is imported unchanged from fleet B05. PPO's target,
advantage, FP64 density, clipping and sequential Adam math follows fleet B04.
There is no backbone, sampler, native environment or production asset query.
"""
from collections.abc import Mapping
from numbers import Integral

import numpy as np
import torch
from torch import nn

from experiments.candidates.uav_fleet_adaptation.b04_native_development import learning as frozen
from experiments.candidates.uav_fleet_adaptation.b05_native_consequence.learning import Head
from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest

COUNT_KEYS = ("actor_optimizer_steps", "actor_replay_rows", "critic_optimizer_steps",
              "critic_replay_rows", "density_identity_rows", "target_rows",
              "actor_optimizer_attempts", "critic_optimizer_attempts")
ROLLOUT_KEYS = ("hidden", "base_logits", "logits", "probabilities", "action_index",
                "logp", "critic_features", "values", "macro_rewards")


def _integer(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an integer")
    return int(value)


def _array(value, name, shape, dtype):
    if not isinstance(value, np.ndarray) or value.shape != shape or value.dtype != np.dtype(dtype):
        raise ValueError(f"{name} requires NumPy {np.dtype(dtype)} with shape {shape}")
    if not np.isfinite(value).all():
        raise FloatingPointError(f"nonfinite {name}")
    return value.copy()


def critic_features(state, actual, mask, nav, *, tick, horizon=256):
    """Copy pre-query state, delivered commands/mask and pre-advance navs.

    The caller captures these before policy proposals or startup replacement.
    Native116 contains raw xyz/user coordinates and the normalized clock.
    """
    tick, horizon = _integer(tick, "tick"), _integer(horizon, "horizon")
    if horizon <= 0 or not 0 <= tick < horizon:
        raise ValueError("critic tick must precede its positive terminal horizon")
    state = _array(state, "state", (116,), np.float32)
    actual = _array(actual, "actual", (5, 3), np.float32)
    mask = _array(mask, "mask", (5,), np.bool_)
    nav = _array(nav, "nav", (5,), np.int64)
    clock = np.float32(float(tick)/float(horizon))
    if state[-1].tobytes() != clock.tobytes():
        raise ValueError("native state clock disagrees with exact tick/horizon")
    if np.any(np.abs(actual) > 1):
        raise ValueError("actual commands must retain normalized [-1,1] values")
    if np.any((nav < 0) | (nav >= 10)):
        raise ValueError("pre-query nav must be in [0,10)")
    xyz = state[:15].reshape(5, 3)
    xyz[:, :2] /= 1000
    xyz[:, 2] = (xyz[:, 2]-50)/100
    state[15:115] /= 1000
    state[-1] = clock
    onehot = np.eye(10, dtype=np.float32)[nav]
    return np.concatenate((state, actual.reshape(-1), mask.astype(np.float32), onehot.reshape(-1)))


class Critic186(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(nn.Linear(186, 128), nn.Tanh(),
                                     nn.Linear(128, 128), nn.Tanh(), nn.Linear(128, 1))

    def forward(self, values):
        return self.network(values).squeeze(-1)


def fresh_critic(seed):
    seed = _integer(seed, "seed")
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        critic = Critic186().cpu().float()
    if sum(p.numel() for p in critic.parameters()) != 40577:
        raise AssertionError("critic parameter contract changed")
    return critic


def make_optimizers(head, critic):
    if not isinstance(head, Head) or not isinstance(critic, Critic186):
        raise ValueError("optimizers require the frozen Head and Critic186")
    for model in (head, critic):
        frozen._finite_parameters(list(model.parameters()))
    return frozen.make_optimizers(head, critic)


def _rollout(episodes, horizon):
    horizon = _integer(horizon, "horizon")
    if horizon <= 0 or horizon % 4:
        raise ValueError("horizon must be a positive multiple of four")
    if len(episodes) != 2:
        raise ValueError("exactly two complete episodes required")
    clocks = horizon//4
    contract = dict(hidden=((clocks, 5, 128), np.float32),
                    base_logits=((clocks, 5, 27), np.float32),
                    logits=((clocks, 5, 27), np.float32),
                    probabilities=((clocks, 5, 27), np.float64),
                    action_index=((clocks, 5), np.int64), logp=((clocks, 5), np.float64),
                    critic_features=((clocks, 186), np.float32), values=((clocks,), np.float32),
                    macro_rewards=((clocks,), np.float64))
    rows = {key: [] for key in contract}
    for episode in episodes:
        if not isinstance(episode, Mapping):
            raise ValueError("episode must be a mapping")
        for key, (shape, dtype) in contract.items():
            if key not in episode:
                raise ValueError(f"missing episode field {key}")
            # Private copies support both read-only and writable NumPy caches;
            # no tensor borrows a buffer that a callback could mutate.
            rows[key].append(torch.from_numpy(_array(episode[key], key, shape, dtype)))
    rollout = {key: torch.stack(values).detach() for key, values in rows.items()}
    actions, probabilities = rollout["action_index"], rollout["probabilities"]
    if ((actions < 0) | (actions >= 27)).any():
        raise ValueError("action_index must be in [0,27)")
    if ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError("invalid saved probabilities")
    if (probabilities.sum(-1)-1).abs().max() > 1e-12:
        raise ValueError("saved probabilities must sum to one")
    chosen = probabilities.gather(-1, actions[..., None]).squeeze(-1)
    if (chosen <= 0).any():
        raise ValueError("chosen saved probability must be positive")
    if (chosen.log()-rollout["logp"]).abs().max() > 1e-10:
        raise ValueError("saved chosen probability and independent logp disagree")
    return rollout, chosen


def _snapshot(model, initial):
    norm = frozen._norm([p.detach()-p0 for p, p0 in zip(model.parameters(), initial)])
    return dict(sha256=state_digest(model.state_dict()), movement_l2=norm if np.isfinite(norm) else None)


def update_group(head, critic, headopt, critopt, episodes, counts, *, horizon=256, live_record=None):
    """Four complete-rollout epochs; live provenance survives any failed operation.

    Returned targets/advantages are independent JSON lists of FP32 values. Counters
    charge attempted forward rows and optimizer calls before those operations;
    completed optimizer steps are charged only after a successful return.
    """
    result = {} if live_record is None else live_record
    if not isinstance(result, dict) or any(key in result for key in ("status", "epochs", "initial_identity", "target_summary")):
        raise ValueError("live group diagnostics must start empty")
    result.update(status="INCOMPLETE", epochs=[])
    stage, epoch, actor_initial, critic_initial = "validation", None, None, None
    try:
        if not isinstance(head, Head) or not isinstance(critic, Critic186):
            raise ValueError("fixed Head/Critic186 required")
        for key in COUNT_KEYS:
            value = counts.get(key, 0)
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or value < 0:
                raise ValueError(f"invalid count {key}")
        result["counts_before"] = {key:int(counts.get(key,0)) for key in COUNT_KEYS}
        rollout, old_chosen = _rollout(episodes, horizon)
        ap, cp = list(head.parameters()), list(critic.parameters())
        if not ap or not cp or set(ap) & set(cp):
            raise ValueError("head and critic require separate nonempty parameters")
        for optimizer, parameters in ((headopt, ap), (critopt, cp)):
            owned = [p for group in optimizer.param_groups for p in group['params']]
            if len(owned) != len(parameters) or set(owned) != set(parameters):
                raise ValueError("optimizer must own exactly its model's parameters")
            frozen._finite_parameters(parameters)
        actor_initial, critic_initial = [p.detach().clone() for p in ap], [p.detach().clone() for p in cp]
        result.update(initial_actor_sha256=state_digest(head.state_dict()), initial_critic_sha256=state_digest(critic.state_dict()))
        stage = "targets"
        rewards = rollout['macro_rewards'].float()
        targets = (rewards.flip(-1).cumsum(-1).flip(-1)/horizon).detach()
        frozen._add(counts, 'target_rows', targets.numel())
        raw = targets-rollout['values']
        advantages = ((raw-raw.mean())/(raw.std(unbiased=False)+1e-8)).detach()
        if not torch.isfinite(targets).all() or not torch.isfinite(advantages).all():
            raise FloatingPointError("nonfinite targets or advantages")
        result.update(targets=targets.tolist(), advantages=advantages.tolist(),
                      target_summary=frozen._summary(targets), advantage_summary=frozen._summary(advantages))
        head.train(); critic.train()
        for epoch in range(4):
            record = dict(epoch=epoch, actor_step_completed=False, critic_step_completed=False)
            result['epochs'].append(record)
            stage = 'actor_replay'
            frozen._finite_parameters(ap)
            outputs=[]
            for hidden, base in zip(rollout['hidden'].reshape(-1,128), rollout['base_logits'].reshape(-1,27)):
                frozen._add(counts,'actor_replay_rows',1)
                output=head(hidden,base)
                if output.shape != (27,) or output.dtype != torch.float32 or output.device.type != 'cpu':
                    raise ValueError("head replay requires one CPU FP32 27-logit row")
                outputs.append(output)
            logits=torch.stack(outputs).reshape(rollout['logits'].shape)
            if not torch.isfinite(logits).all():
                raise FloatingPointError("nonfinite head replay")
            stage = 'actor_density'
            z=logits.double()
            weights=(z-z.max(-1,keepdim=True).values).exp()
            probabilities=weights/weights.sum(-1,keepdim=True)
            chosen=probabilities.gather(-1,rollout['action_index'][...,None]).squeeze(-1)
            ratio, logp = chosen/old_chosen, chosen.log()
            if (not torch.isfinite(probabilities).all() or not torch.isfinite(ratio).all()
                    or not torch.isfinite(logp).all() or (chosen <= 0).any()):
                raise FloatingPointError("nonfinite or nonpositive replay density")
            if epoch == 0:
                stage='density_identity'
                frozen._add(counts,'density_identity_rows',ratio.numel())
                identity=dict(logits_exact=bool(torch.equal(logits.detach(),rollout['logits'])),
                    max_probability_abs=float((probabilities.detach()-rollout['probabilities']).abs().max()),
                    max_chosen_logp_abs=float((logp.detach()-rollout['logp']).abs().max()),
                    max_ratio_from_one=float((ratio.detach()-1).abs().max()),rows=ratio.numel())
                result['initial_identity']=identity
                if (not identity['logits_exact'] or identity['max_probability_abs'] > 5e-14
                        or identity['max_chosen_logp_abs'] > 1e-10 or identity['max_ratio_from_one'] > 1e-10):
                    raise ValueError("initial replay density identity failed")
            stage='actor_loss'
            advantage=advantages[...,None]
            actor_loss=-torch.minimum(ratio*advantage,ratio.clamp(.8,1.2)*advantage).sum(-1).mean()
            if not torch.isfinite(actor_loss):
                raise FloatingPointError("nonfinite actor loss")
            record.update(actor_loss=float(actor_loss.detach()),ratio_min=float(ratio.detach().min()),
                ratio_max=float(ratio.detach().max()),ratio_mean=float(ratio.detach().mean()),
                clip_fraction=float(((ratio.detach()<.8)|(ratio.detach()>1.2)).double().mean()),
                old_logp_mean=float(rollout['logp'].mean()),new_logp_mean=float(logp.detach().mean()))
            stage='actor_gradient'
            headopt.zero_grad(set_to_none=True)
            actor_loss.backward()
            actor_norm=torch.nn.utils.clip_grad_norm_(ap,.5,error_if_nonfinite=True,foreach=False)
            record.update(actor_grad_norm=float(actor_norm),
                          actor_clipped_grad_norm=frozen._norm([p.grad for p in ap if p.grad is not None]))
            stage='actor_optimizer'
            frozen._add(counts,'actor_optimizer_attempts',1)
            headopt.step()
            frozen._add(counts,'actor_optimizer_steps',1)
            record.update(actor_step_completed=True,actor_optimizer_step_values=frozen._step_values(headopt,ap),
                          actor_movement_l2=frozen._norm([p-p0 for p,p0 in zip(ap,actor_initial)]),
                          actor_sha256=state_digest(head.state_dict()))
            frozen._finite_parameters(ap)
            stage='critic_replay'
            frozen._finite_parameters(cp)
            frozen._add(counts,'critic_replay_rows',targets.numel())
            predicted=critic(rollout['critic_features'])
            if predicted.shape != targets.shape or predicted.dtype != torch.float32 or predicted.device.type != 'cpu':
                raise ValueError("critic replay requires CPU FP32 team-row values")
            stage='critic_loss'
            critic_loss=.5*(predicted-targets).square().mean()
            if not torch.isfinite(critic_loss):
                raise FloatingPointError("nonfinite critic loss")
            record['critic_loss']=float(critic_loss.detach())
            stage='critic_gradient'
            critopt.zero_grad(set_to_none=True)
            critic_loss.backward()
            critic_norm=torch.nn.utils.clip_grad_norm_(cp,.5,error_if_nonfinite=True,foreach=False)
            record.update(critic_grad_norm=float(critic_norm),
                          critic_clipped_grad_norm=frozen._norm([p.grad for p in cp if p.grad is not None]))
            stage='critic_optimizer'
            frozen._add(counts,'critic_optimizer_attempts',1)
            critopt.step()
            frozen._add(counts,'critic_optimizer_steps',1)
            record['critic_step_completed']=True
            frozen._finite_parameters(cp)
            record.update(critic_movement_l2=frozen._norm([p-p0 for p,p0 in zip(cp,critic_initial)]),
                          critic_optimizer_step_values=frozen._step_values(critopt,cp),
                          critic_sha256=state_digest(critic.state_dict()))
        result.update(status='COMPLETE',actor_optimizer_step_values=frozen._step_values(headopt,ap),
                      critic_optimizer_step_values=frozen._step_values(critopt,cp))
        return result
    except Exception as error:
        result.update(status='FAILED',failure=dict(stage=stage,epoch=epoch,type=type(error).__name__,message=str(error)))
        raise
    finally:
        if 'counts_before' in result:
            result['counts_after']={key:int(counts.get(key,0)) for key in COUNT_KEYS}
            result['counts_delta']={key:result['counts_after'][key]-result['counts_before'][key] for key in COUNT_KEYS}
        if actor_initial is not None:
            snapshot=_snapshot(head,actor_initial)
            result.update(final_actor_sha256=snapshot['sha256'],actor_movement_l2=snapshot['movement_l2'],
                          actor_optimizer_step_values=frozen._step_values(headopt,list(head.parameters())))
        if critic_initial is not None:
            snapshot=_snapshot(critic,critic_initial)
            result.update(final_critic_sha256=snapshot['sha256'],critic_movement_l2=snapshot['movement_l2'],
                          critic_optimizer_step_values=frozen._step_values(critopt,list(critic.parameters())))
