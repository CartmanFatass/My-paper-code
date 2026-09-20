"""Frozen UCOPE calendar-exchange prototype; no training or native-run entrypoint.

The five-UAV, three-command, 104-observation and 64-hidden dimensions are the
pinned reactive_renewal_b01 interface, not a general policy/environment adapter.
Full random tables give each recipient its own fixed primitive-time innovations.
See docs/research/designs/TEMPORAL_BEHAVIOR_STATE_ALIGNMENT_20260919.md.
"""
from dataclasses import dataclass
from numbers import Integral

import numpy as np
import torch


@dataclass(frozen=True)
class EpisodeTrace:
    commands: np.ndarray
    fresh: np.ndarray
    actor_inputs: np.ndarray
    rewards: np.ndarray

    @property
    def score(self):
        """The UCOPE sum-of-team-rewards / primitive-horizon convention."""
        return float(self.rewards.mean())


def _nonnegative_integer(value, name):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return int(value)


def random_inputs(seed, world_id, horizon):
    """Separate local RNGs; horizon extension preserves every existing slot."""
    seed = _nonnegative_integer(seed, "seed")
    world_id = _nonnegative_integer(world_id, "world_id")
    horizon = _nonnegative_integer(horizon, "horizon")
    if horizon == 0:
        raise ValueError("horizon must be positive")
    velocity = np.random.default_rng(np.random.SeedSequence([seed, world_id, 0]))
    gate = np.random.default_rng(np.random.SeedSequence([seed, world_id, 1]))
    return (velocity.standard_normal((horizon, 5, 3)).astype(np.float32),
            gate.random((horizon, 5)))


def validate_calendar(calendar):
    """A fresh first command and no consecutive holds, independently per UAV."""
    calendar = np.asarray(calendar)
    if calendar.dtype != np.bool_:
        raise ValueError("calendar must have Boolean dtype")
    if calendar.ndim != 2 or calendar.shape[0] == 0 or calendar.shape[1] != 5:
        raise ValueError("calendar must have shape (positive horizon, 5)")
    if not calendar[0].all():
        raise ValueError("every UAV must be fresh at reset")
    if ((~calendar[1:]) & (~calendar[:-1])).any():
        raise ValueError("a held command must renew on the next tick")
    return calendar


def exchange_calendars(calendars):
    """Swap adjacent prespecified world pairs; preserve whole joint calendars."""
    calendars = np.asarray(calendars)
    if calendars.ndim != 3 or len(calendars) == 0 or len(calendars) % 2:
        raise ValueError("expected a positive even number of world calendars")
    for calendar in calendars:
        validate_calendar(calendar)
    return calendars.reshape(-1, 2, *calendars.shape[1:])[:, ::-1].reshape(calendars.shape).copy()


def paired_effects(online_scores, exchanged_scores):
    """One online-minus-exchange effect per coupled world pair, per checkpoint."""
    online = np.asarray(online_scores, dtype=np.float64)
    exchanged = np.asarray(exchanged_scores, dtype=np.float64)
    if (online.ndim != 1 or online.shape != exchanged.shape
            or online.size == 0 or online.size % 2):
        raise ValueError("score vectors must have the same positive even length")
    if not np.isfinite(online).all() or not np.isfinite(exchanged).all():
        raise ValueError("all outcomes must be finite; missing worlds cannot be dropped")
    return (online - exchanged).reshape(-1, 2).mean(axis=1)


@torch.no_grad()
def _commands(actor, mean, recurrent, previous, eligible, epsilon, uniforms, imposed):
    if imposed is None:
        fresh = ~eligible.copy()
        if eligible.any():
            mask = torch.from_numpy(eligible)
            inputs = torch.cat((recurrent[mask], torch.from_numpy(previous[eligible])), -1)
            probabilities = actor.duration(inputs).softmax(-1)
            if probabilities.shape != (int(eligible.sum()), 2) or not torch.isfinite(probabilities).all():
                raise ValueError("gate must return finite KEEP/END probabilities")
            fresh[eligible] = uniforms[eligible] >= probabilities[:, 0].numpy()
    else:
        fresh = imposed.copy()
    sent = previous.copy()
    mask = torch.from_numpy(fresh)
    if mask.any():
        u = mean[mask] + actor.log_std.clamp(-5, 2).exp() * torch.from_numpy(epsilon[fresh])
        sent[fresh] = u.tanh().numpy()
    return sent, fresh


@torch.no_grad()
def frozen_episode(actor, env, reset_seed, innovations, gate_uniforms, calendar=None):
    """Run one frozen, CPU FP32 episode, online or under an external calendar.

    The caller owns the environment and any checkpoint/admission/publication for
    a future native study. Tests supply only synthetic adapters. This function
    never calls an optimizer, loads a checkpoint, or uses a global random stream.
    """
    innovations = np.asarray(innovations, dtype=np.float32)
    uniforms = np.asarray(gate_uniforms, dtype=np.float64)
    if innovations.ndim != 3 or innovations.shape[1:] != (5, 3) or len(innovations) == 0:
        raise ValueError("innovations must have shape (positive horizon, 5, 3)")
    horizon = len(innovations)
    if uniforms.shape != (horizon, 5):
        raise ValueError("gate uniforms must have shape (horizon, 5)")
    if (not np.isfinite(innovations).all() or not np.isfinite(uniforms).all()
            or (uniforms < 0).any() or (uniforms >= 1).any()):
        raise ValueError("innovations must be finite and uniforms must lie in [0, 1)")
    if calendar is not None:
        calendar = validate_calendar(calendar).copy()
        if len(calendar) != horizon:
            raise ValueError("calendar and innovations must have the same horizon")
    if any(p.device.type != "cpu" or p.dtype != torch.float32 for p in actor.parameters()):
        raise ValueError("the pinned actor must use CPU FP32")
    if actor.log_std.shape != (3,):
        raise ValueError("the pinned actor must have three global log standard deviations")
    obs, _ = env.reset(seed=reset_seed)
    previous = np.zeros((5, 3), dtype=np.float32)
    eligible = np.zeros(5, dtype=bool)
    hidden = torch.zeros(1, 5, 64)
    commands, schedules, inputs, rewards = [], [], [], []
    for tick in range(horizon):
        obs = np.asarray(obs, dtype=np.float32)
        if obs.shape != (5, 104) or not np.isfinite(obs).all():
            raise ValueError("the pinned actor requires five finite 104-wide observations")
        x = np.concatenate((obs, previous, eligible[:, None].astype(np.float32) / 4), axis=-1)
        mean, recurrent, hidden = actor(torch.from_numpy(x)[None], hidden)
        if (mean.shape != (1, 5, 3) or recurrent.shape != (1, 5, 64)
                or hidden.shape != (1, 5, 64)
                or not all(torch.isfinite(v).all() for v in (mean, recurrent, hidden))):
            raise ValueError("actor returned invalid mean or recurrent state")
        sent, fresh = _commands(actor, mean[0], recurrent[0], previous, eligible,
                                innovations[tick], uniforms[tick],
                                None if calendar is None else calendar[tick])
        if not np.isfinite(sent).all():
            raise ValueError("actor returned nonfinite commands")
        obs, _, terminated, truncated, info = env.step(sent.copy())
        if (terminated or truncated) and tick + 1 < horizon:
            raise ValueError("incomplete episode; no partial comparison")
        if tick + 1 == horizon and not (terminated or truncated):
            raise ValueError("episode has not terminated at the declared horizon")
        reward = sum(float(info["rewards_dict"][f"uav_{i}"]) for i in range(5))
        if not np.isfinite(reward):
            raise ValueError("nonfinite native team reward")
        commands.append(sent.copy())
        schedules.append(fresh.copy())
        inputs.append(x.copy())
        rewards.append(reward)
        previous, eligible = sent.copy(), fresh.copy()
    return EpisodeTrace(np.stack(commands), np.stack(schedules), np.stack(inputs),
                        np.asarray(rewards, dtype=np.float64))
