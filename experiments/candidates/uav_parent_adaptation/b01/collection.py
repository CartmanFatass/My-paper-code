"""Original 28-byte parent collection and retained 40-byte composed collection."""

import hashlib
import math

import numpy as np
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.channel import (
    Channel, payloads,
)
from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import (
    action_terms, sample_actions,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import (
    actor_features, critic_features, team_reward,
)
from experiments.candidates.uav_message_content.b05.collector import native_outcome, longest_zero_run
from experiments.candidates.uav_message_content.b06.collector import (
    collect_episode as collect_retained, state_hash,
)


@torch.no_grad()
def collect_parent(env, actor, critic, stage, horizon, reset_seed, channel_seed,
                   motion_rng, metadata, counts, emit, check=lambda: None):
    """C/B share the original C geometry, joint-learner storage and no content head."""
    if stage not in ("C", "B") or metadata["phase"] != "train":
        raise ValueError("parent collection is C/B training only")
    check()
    raw, info = env.reset(seed=reset_seed)
    state = info["state"]
    counts["explicit_resets"] += 1
    scene_hash = hashlib.sha256(np.asarray(raw).tobytes() + np.asarray(state).tobytes()).hexdigest()
    channel = Channel(channel_seed)
    last = np.zeros((5, 3), dtype=np.float32)
    remaining = np.zeros(5, dtype=np.int64)
    hidden = torch.zeros(1, 5, 64)
    names = ("obs", "hidden", "critic", "u", "sends", "eligible", "logp", "value", "reward")
    storage = {key: [] for key in names}
    physical, charges, services, quality, good_sequence = [], [], [], [], []
    witness_rng = torch.Generator().set_state(motion_rng.get_state())
    initial_rng = state_hash(motion_rng)
    innovations = hashlib.sha256()
    for t in range(horizon):
        check()
        before_delivered = channel.delivered
        channel.begin_tick()
        extras = channel.features()
        x = torch.from_numpy(np.concatenate((actor_features(raw, last, remaining), extras), axis=1))
        cx = torch.from_numpy(np.concatenate((critic_features(state, last, remaining), extras.ravel())))
        if x.shape != (5, 171) or cx.shape != (451,):
            raise ValueError("original C/B input contract changed")
        h0 = hidden[0].clone()
        mean, recurrent, hidden = actor(x[None], hidden)
        mean, recurrent = mean[0], recurrent[0]
        value = critic(cx)
        counts["behavior_actor_forward_calls"] += 1
        counts["behavior_actor_forward_rows"] += 5
        counts["behavior_critic_forward_calls"] += 1
        counts["behavior_critic_forward_rows"] += 1
        eligible = torch.from_numpy(~channel.pending.copy())
        u, sends = sample_actions(actor, mean, recurrent, eligible, t, motion_rng, None)
        epsilon = torch.stack([torch.randn(3, generator=witness_rng) for _ in range(5)])
        if not torch.equal(u, mean + actor.log_std.clamp(-5, 2).exp() * epsilon):
            raise RuntimeError("parent actual sample differs from the witnessed innovation")
        innovations.update(epsilon.numpy().tobytes())
        sender = t % 5
        if int(sends.sum()) != 1 or not bool(sends[sender]):
            raise RuntimeError("original RR sender/eligibility changed")
        packet = payloads(raw)[sender]
        if packet.shape != (7,) or packet[5] != 0:
            raise RuntimeError("original geometry/structural-zero contract changed")
        logp, _ = action_terms(actor, mean, recurrent, u, sends, eligible)
        if not torch.isfinite(logp).all() or not torch.isfinite(value):
            raise FloatingPointError("nonfinite parent likelihood/value")
        command = u.tanh().numpy()
        due = t + (1 if channel.good else 5)
        charge = channel.resolve(sends.numpy(), raw)
        good_sequence.append(int(channel.good))
        counts["motion_samples"] += 5
        counts["broadcasts"] += 1
        counts["attempts"] += 1
        counts["censored_packets"] += int(due >= horizon)
        counts["native_step_calls"] += 1
        raw_next, _, terminated, truncated, info = env.step(command)
        counts["team_steps"] += 1
        counts["train_team_steps"] += 1
        reward_physical = team_reward(info)
        reward_net = reward_physical - charge
        served, q, _ = native_outcome(info)
        if not math.isfinite(reward_net) or not math.isfinite(q):
            raise FloatingPointError("nonfinite native parent outcome")
        physical.append(reward_physical)
        charges.append(charge)
        services.append(served)
        quality.append(q)
        counts["delivered_packets"] += channel.delivered - before_delivered
        values = (x, h0, cx, u, sends, eligible, logp, value,
                  torch.tensor(reward_net, dtype=torch.float32))
        for key, item in zip(names, values):
            storage[key].append(item.detach().clone())
        last[:] = command
        raw, state = raw_next, info["next_state"]
        channel.advance()
        if (terminated or truncated) and t + 1 < horizon:
            raise RuntimeError(f"incomplete parent episode {t + 1}/{horizon}")
    if not torch.equal(witness_rng.get_state(), motion_rng.get_state()):
        raise RuntimeError("parent motion RNG consumption changed")
    counts["train_episodes"] += 1
    emit(dict(metadata, reset_seed=reset_seed, channel_seed=channel_seed, steps=horizon,
              initial_scene_sha256=scene_hash,
              channel_sequence_sha256=hashlib.sha256(bytes(good_sequence)).hexdigest(),
              motion_rng_start_sha256=initial_rng, motion_rng_end_sha256=state_hash(motion_rng),
              innovation_sha256=innovations.hexdigest(), innovation_vectors=horizon * 5,
              J_net=(sum(physical) - sum(charges)) / horizon,
              J_physical=sum(physical) / horizon, charge_per_tick=sum(charges) / horizon,
              served_users_per_tick=sum(services) / horizon, Q=sum(quality) / horizon,
              worst_tick_service=min(services), zero_service_steps=services.count(0),
              longest_zero_service=longest_zero_run(services), packet_bytes=28,
              **channel.facts()))
    check()
    return {key: torch.stack(items) for key, items in storage.items()}


def collect_composed(env, actor, critic, program, horizon, reset_seed, channel_seed,
                     motion_rng, metadata, counts, emit, check=lambda: None, raw_path=None):
    if program not in ("I", "P", "K", "D"):
        raise ValueError("fixed I/P/K/D program")
    mapped = "B40" if program in ("I", "P") else program
    return collect_retained(env, actor, critic, mapped, horizon, reset_seed, channel_seed,
                            motion_rng, metadata, counts,
                            lambda row: emit(dict(row, packet_bytes=40)), check, raw_path=raw_path)
