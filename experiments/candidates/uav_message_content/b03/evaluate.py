"""Sampled native RR evaluation with no learner or counterfactual forwards."""

import hashlib
import math

import numpy as np
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import sample_actions
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import (
    AGENTS, actor_features, team_reward,
)
from .channel import ContentChannel, Sightings, hand_payload
from .model import sample_content


def native_service(info):
    global_info = info["infos_dict"][AGENTS[0]]["global"]
    served = int(global_info["served_users"])
    if "connections" not in global_info or "sinr_matrix" not in global_info:
        return served, None
    connection = np.asarray(global_info["connections"], dtype=bool)
    sinr = np.asarray(global_info["sinr_matrix"])
    quality = np.clip((sinr[connection] - 3) / 30, 0, 1)
    return served, float(quality.mean()) if served else 0.0


@torch.no_grad()
def collect_episode(env, actor, arm, horizon, reset_seed, channel_seed,
                    motion_rng, content_rng, metadata, counts, emit, check,
                    raw_path, require_quality=False):
    check()
    raw, info = env.reset(seed=reset_seed)
    state = info["state"]
    counts["explicit_resets"] += 1
    scene_hash = hashlib.sha256(
        np.asarray(raw).tobytes() + np.asarray(state).tobytes()).hexdigest()
    channel = ContentChannel(channel_seed)
    sightings = Sightings()
    last = np.zeros((5, 3), dtype=np.float32)
    remaining = np.zeros(5, dtype=np.int64)
    hidden = torch.zeros(1, 5, 64)
    trace = {key: [] for key in (
        "actor_input", "pre_tanh_motion", "action", "packet", "pre_tanh_content",
        "due", "good", "deliveries", "reward_physical", "reward_net",
        "served_users", "Q", "records", "pending_after_send", "sender")}
    physical, charges, services, quality, good_sequence = [], [], [], [], []
    boundary_count = floor_count = ceiling_count = 0
    height_sum = 0.0
    for t in range(horizon):
        check()
        before_delivered = channel.delivered
        channel.begin_tick()
        deliveries = channel.delivered - before_delivered
        sightings.observe(raw)
        extras = channel.features()
        x = torch.from_numpy(np.concatenate(
            (actor_features(raw, last, remaining), extras), axis=1))
        if x.shape != (5, 171):
            raise ValueError("CADC actor input contract changed")
        positions = np.asarray(raw, dtype=np.float32)[:, :3]
        boundary_count += int((np.isclose(positions[:, :2], 0, atol=1e-7, rtol=0) |
                               np.isclose(positions[:, :2], 1, atol=1e-7, rtol=0)).any(axis=1).sum())
        floor_count += int(np.isclose(positions[:, 2], 0, atol=1e-7, rtol=0).sum())
        ceiling_count += int(np.isclose(positions[:, 2], 1, atol=1e-7, rtol=0).sum())
        height_sum += float((50 + 100 * positions[:, 2]).sum())
        counts["actor_forward_calls"] += 1
        mean, recurrent, hidden = actor(x[None], hidden)
        mean, recurrent = mean[0], recurrent[0]
        if not torch.isfinite(mean).all():
            raise FloatingPointError("nonfinite frozen actor mean")
        eligible = torch.from_numpy(~channel.pending.copy())
        u, sends = sample_actions(
            actor, mean, recurrent, eligible, t, motion_rng, content_rng)
        sender = t % 5
        if int(sends.sum()) != 1 or not bool(sends[sender]):
            raise RuntimeError("fixed RR sender/eligibility changed")
        content_u = np.zeros(1, dtype=np.float32)
        if arm == "L":
            sampled, encoded = sample_content(actor, recurrent, sender, content_rng)
            content_u = sampled.numpy().copy()
            packet = hand_payload(arm, raw, sender, sightings, encoded.item())
            counts["content_samples"] += 1
        else:
            packet = hand_payload(arm, raw, sender, sightings)
        command = u.tanh().numpy()
        good_sequence.append(int(channel.good))
        charge, due = channel.resolve_payload(sender, packet)
        counts["motion_samples"] += 5
        counts["broadcasts"] += 1
        counts["attempts"] += 1
        if due >= horizon:
            counts["censored_packets"] += 1
        counts["native_step_calls"] += 1
        raw_next, _, terminated, truncated, info = env.step(command)
        counts["team_steps"] += 1
        reward_physical = team_reward(info)
        reward_net = reward_physical - charge
        served, q = native_service(info)
        if not math.isfinite(reward_net) or (q is not None and not math.isfinite(q)):
            raise FloatingPointError("nonfinite native outcome")
        if require_quality and q is None:
            raise ValueError("native Q is unavailable")
        physical.append(reward_physical)
        charges.append(charge)
        services.append(served)
        quality.append(q)
        counts["delivered_packets"] += deliveries
        values = (x.numpy(), u.numpy(), command.copy(), packet.copy(), content_u,
                  due, int(channel.good), deliveries, reward_physical, reward_net,
                  served, np.nan if q is None else q, channel.records.copy(),
                  channel.pending.copy(), sender)
        for key, value in zip(trace, values):
            trace[key].append(value)
        last[:] = command
        raw, state = raw_next, info["next_state"]
        channel.advance()
        if (terminated or truncated) and t + 1 < horizon:
            raise RuntimeError(f"incomplete native episode {t + 1}/{horizon}")
    counts["eval_episodes"] += 1
    row = dict(metadata, reset_seed=reset_seed, channel_seed=channel_seed, steps=horizon,
               initial_scene_sha256=scene_hash,
               channel_sequence_sha256=hashlib.sha256(bytes(good_sequence)).hexdigest(),
               J_net=(sum(physical) - sum(charges)) / horizon,
               J_physical=sum(physical) / horizon, charge_per_tick=sum(charges) / horizon,
               served_users_per_tick=sum(services) / horizon,
               Q=(sum(quality) / horizon if all(x is not None for x in quality) else None),
               boundary_fraction=boundary_count / (5 * horizon),
               height_floor_fraction=floor_count / (5 * horizon),
               height_ceiling_fraction=ceiling_count / (5 * horizon),
               mean_height_m=height_sum / (5 * horizon), **channel.facts())
    np.savez_compressed(raw_path, **{key: np.asarray(values) for key, values in trace.items()})
    row["raw"] = str(raw_path)
    row["raw_sha256"] = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    row["action_sequence_sha256"] = hashlib.sha256(
        np.asarray(trace["action"], dtype=np.float32).tobytes()).hexdigest()
    emit(row)
    check()
    return row
