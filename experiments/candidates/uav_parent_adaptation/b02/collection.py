"""Forty-byte U training with the original joint PPO storage and decision views."""

import hashlib
import math

import numpy as np
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import (
    action_terms, sample_actions,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import team_reward
from experiments.candidates.uav_message_content.b05.channel import ForecastChannel, packet_for
from experiments.candidates.uav_message_content.b05.collector import (
    make_inputs, native_outcome, longest_zero_run,
)
from experiments.candidates.uav_message_content.b06.collector import (
    collect_episode as collect_retained, state_hash,
)


@torch.no_grad()
def collect_training(env, actor, critic, horizon, reset_seed, channel_seed,
                     motion_rng, metadata, counts, emit, check=lambda: None):
    if metadata["phase"] != "train" or metadata["arm"] != "U":
        raise ValueError("B02 trains only U")
    check()
    raw, info = env.reset(seed=reset_seed)
    state = info["state"]
    counts["explicit_resets"] += 1
    scene_hash = hashlib.sha256(np.asarray(raw).tobytes() + np.asarray(state).tobytes()).hexdigest()
    channel = ForecastChannel(channel_seed, horizon)
    last = np.zeros((5, 3), dtype=np.float32)
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
        extended_x, extended_cx = make_inputs(raw, state, last, channel)
        if torch.any(extended_x[:, 171:]) or torch.any(extended_cx[451:]):
            raise RuntimeError("geometry-only tails changed")
        x, cx = extended_x[:, :171], extended_cx[:451]
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
            raise RuntimeError("U actual action differs from the witnessed innovation")
        innovations.update(epsilon.numpy().tobytes())
        sender = t % 5
        if int(sends.sum()) != 1 or not bool(sends[sender]):
            raise RuntimeError("original RR sender/eligibility changed")
        logp, _ = action_terms(actor, mean, recurrent, u, sends, eligible)
        if not torch.isfinite(logp).all() or not torch.isfinite(value):
            raise FloatingPointError("nonfinite U likelihood/value")
        command = u.tanh().numpy()
        packet = packet_for(raw, sender, np.zeros(3, dtype=np.float32))
        if packet.shape != (10,) or packet[5] != 0 or packet[7:].any():
            raise RuntimeError("40-byte geometry/zero-tail contract changed")
        charge, due = channel.resolve_payload(sender, packet)
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
            raise FloatingPointError("nonfinite native U outcome")
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
            raise RuntimeError(f"incomplete U episode {t + 1}/{horizon}")
    if not torch.equal(witness_rng.get_state(), motion_rng.get_state()):
        raise RuntimeError("U motion RNG consumption changed")
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
              longest_zero_service=longest_zero_run(services), packet_bytes=40,
              log_std=actor.log_std.detach().tolist(),
              sigma=actor.log_std.detach().clamp(-5, 2).exp().tolist(), **channel.facts()))
    check()
    return {key: torch.stack(items) for key, items in storage.items()}


def collect_evaluation(env, actor, critic, program, horizon, reset_seed, channel_seed,
                       motion_rng, metadata, counts, emit, check=lambda: None, raw_path=None):
    if program not in ("P", "U", "K", "D") or metadata["phase"] != "final_eval":
        raise ValueError("fixed frozen P/U/K/D evaluation")
    # For U, the legacy base_mean field is U's own actual mean, never a P shadow.
    mapped = "B40" if program in ("P", "U") else program
    return collect_retained(env, actor, critic, mapped, horizon, reset_seed, channel_seed,
                            motion_rng, metadata, counts,
                            lambda row: emit(dict(row, packet_bytes=40)), check, raw_path=raw_path)
