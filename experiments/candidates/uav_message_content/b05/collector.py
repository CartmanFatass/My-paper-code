"""Behavioral collection with frozen-base state on actual executed history."""

import hashlib
import math

import numpy as np
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import sample_actions
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import (
    AGENTS, actor_features, critic_features, team_reward,
)
from .channel import ForecastChannel, cache_timing, endpoints, packet_for
from .model import CORRECTION_BOUND, motion_terms


def make_inputs(raw, state, last, channel):
    remaining = np.zeros(5, dtype=np.int64)
    extra = channel.features()
    base_actor = np.concatenate((actor_features(raw, last, remaining), extra), axis=1)
    base_critic = np.concatenate((critic_features(state, last, remaining), extra.ravel()))
    if base_actor.shape != (5, 171) or base_critic.shape != (451,):
        raise ValueError("retained input shape changed")
    x = np.concatenate((base_actor, channel.forecasts.reshape(5, 15)), axis=1)
    cx = np.concatenate((base_critic, channel.forecasts.ravel()))
    return torch.from_numpy(x), torch.from_numpy(cx)


def native_outcome(info, connections=False):
    value = info["infos_dict"][AGENTS[0]]["global"]
    served = int(value["served_users"])
    connection = np.asarray(value["connections"], dtype=bool)
    sinr = np.asarray(value["sinr_matrix"])
    if connection.shape != (5, 50) or sinr.shape != (5, 50):
        raise ValueError("native connection contract changed")
    q = float(np.clip((sinr[connection] - 3) / 30, 0, 1).mean()) if served else 0.0
    bits = np.any(connection, axis=0).astype(np.uint8) if connections else None
    return served, q, bits


def longest_zero_run(values):
    longest = current = 0
    for value in values:
        current = current + 1 if value == 0 else 0
        longest = max(longest, current)
    return longest


@torch.no_grad()
def collect_episode(env, actor, critic, arm, horizon, reset_seed, channel_seed,
                    motion_rng, metadata, counts, emit, check=lambda: None, raw_path=None,
                    sampler=sample_actions):
    if arm not in ("B40", "M_G", "M_O"):
        raise ValueError("B05 arm")
    training = metadata["phase"] == "train"
    if training and arm == "B40":
        raise ValueError("B40 never trains")
    check()
    raw, info = env.reset(seed=reset_seed)
    state = info["state"]
    initial_state = np.asarray(state).copy()
    counts["explicit_resets"] += 1
    scene_hash = hashlib.sha256(np.asarray(raw).tobytes() + np.asarray(state).tobytes()).hexdigest()
    channel = ForecastChannel(channel_seed, horizon)
    last = np.zeros((5, 3), dtype=np.float32)
    hidden = torch.zeros(1, 5, 64)
    names = ("obs", "hidden", "critic", "u", "logp", "value", "reward")
    storage = {key: [] for key in names} if training else None
    positions = [np.asarray(raw, dtype=np.float32)[:, :3].copy()]
    trace_names = (
        "actor_input", "critic_input", "base_mean", "composed_mean", "correction",
        "sample_logp", "pre_tanh_motion", "central_motion", "action", "packet",
        "ordinary_endpoint", "sampled_cv_endpoint", "forecast_endpoint", "sender", "due",
        "good", "deliveries", "records", "cache_age", "cache_remaining_lead",
        "pending_after_send", "reward_physical", "reward_net", "served_users", "Q",
        "shadow_central_motion", "connected_users",
    )
    trace = {key: [] for key in trace_names} if raw_path is not None else None
    physical, charges, services, quality, good_sequence = [], [], [], [], []
    correction_sq = correction_abs = correction_max = executed_sq = 0.0
    saturated = nonzero = boundary_count = floor_count = ceiling_count = 0
    height_sum = response_sq = response_max = 0.0
    valid_future_uses = 0
    for t in range(horizon):
        check()
        before_delivered = channel.delivered
        channel.begin_tick()
        deliveries = channel.delivered - before_delivered
        x, cx = make_inputs(raw, state, last, channel)
        h0 = hidden[0].clone()
        if arm == "B40":
            mean, recurrent, hidden = actor(x[None, :, :171], hidden)
            base_mean = mean
            correction = torch.zeros_like(mean)
        else:
            mean, recurrent, hidden, base_mean, correction = actor.components(x[None], hidden)
        mean, recurrent, base_mean, correction = (
            value[0] for value in (mean, recurrent, base_mean, correction)
        )
        counts["behavior_actor_forward_calls"] += 1
        counts["behavior_actor_forward_rows"] += 5
        shadow_mean = np.zeros((5, 3), dtype=np.float32)
        if raw_path is not None and arm == "M_O":
            shadow_x = x.clone()
            shadow_x[:, 171:] = 0
            shadow_mean = actor(shadow_x[None], h0[None])[0][0].tanh().numpy().copy()
            counts["diagnostic_forward_calls"] += 1
            response = mean.tanh().numpy() - shadow_mean
            response_sq += float(np.square(response).sum())
            response_max = max(response_max, float(np.abs(response).max()))
        value = critic(cx) if training else torch.tensor(0.)
        if training:
            counts["behavior_critic_forward_calls"] += 1
            counts["behavior_critic_forward_rows"] += 1
        eligible = torch.from_numpy(~channel.pending.copy())
        u, sends = sampler(actor, mean, recurrent, eligible, t, motion_rng, None)
        sender = t % 5
        if int(sends.sum()) != 1 or not bool(sends[sender]):
            raise RuntimeError("fixed RR sender/eligibility changed")
        logp, _ = motion_terms(actor, mean, u)
        if not torch.isfinite(logp).all() or not torch.isfinite(value):
            raise FloatingPointError("nonfinite sampled density or value")
        command = u.tanh().numpy()
        central = mean.tanh().numpy()
        delta = correction.numpy()
        if float(np.abs(delta).max()) > CORRECTION_BOUND + 1e-7:
            raise FloatingPointError("residual escaped its bound")
        correction_sq += float(np.square(delta).sum())
        correction_abs += float(np.abs(delta).sum())
        correction_max = max(correction_max, float(np.abs(delta).max()))
        saturated += int((np.abs(delta) >= .095).sum())
        nonzero += int((delta != 0).sum())
        executed_change = command - (u - correction).tanh().numpy()
        executed_sq += float(np.square(executed_change).sum())
        ordinary = sampled_cv = np.zeros(3, dtype=np.float32)
        if arm == "M_O":
            ordinary, sampled_cv = endpoints(positions[-1][sender], command[sender],
                                             central[sender], min(10, horizon - t))
        packet = packet_for(raw, sender, ordinary)
        charge, due = channel.resolve_payload(sender, packet)
        age, lead = cache_timing(channel.records, t, horizon)
        valid_future_uses += int((lead > 0).sum())
        good_sequence.append(int(channel.good))
        counts["motion_samples"] += 5
        counts["broadcasts"] += 1
        counts["attempts"] += 1
        if due >= horizon:
            counts["censored_packets"] += 1
        counts["native_step_calls"] += 1
        raw_next, _, terminated, truncated, info = env.step(command)
        counts["team_steps"] += 1
        counts[f"{metadata['phase']}_team_steps"] += 1
        reward_physical = team_reward(info)
        reward_net = reward_physical - charge
        served, q, bits = native_outcome(info, connections=trace is not None)
        if not math.isfinite(reward_net) or not math.isfinite(q):
            raise FloatingPointError("nonfinite native outcome")
        physical.append(reward_physical)
        charges.append(charge)
        services.append(served)
        quality.append(q)
        counts["delivered_packets"] += deliveries
        if storage is not None:
            values = (x, h0, cx, u, logp, value, torch.tensor(reward_net, dtype=torch.float32))
            for key, item in zip(names, values):
                storage[key].append(item.detach().clone())
        p = positions[-1]
        boundary_count += int((np.isclose(p[:, :2], 0, atol=1e-7, rtol=0) |
                               np.isclose(p[:, :2], 1, atol=1e-7, rtol=0)).any(axis=1).sum())
        floor_count += int(np.isclose(p[:, 2], 0, atol=1e-7, rtol=0).sum())
        ceiling_count += int(np.isclose(p[:, 2], 1, atol=1e-7, rtol=0).sum())
        height_sum += float((50 + 100 * p[:, 2]).sum())
        if trace is not None:
            sample = dict(
                actor_input=x.numpy(), critic_input=cx.numpy(), base_mean=base_mean.numpy(),
                composed_mean=mean.numpy(), correction=delta, sample_logp=logp.numpy(),
                pre_tanh_motion=u.numpy(), central_motion=central, action=command,
                packet=packet, ordinary_endpoint=ordinary, sampled_cv_endpoint=sampled_cv,
                forecast_endpoint=ordinary, sender=sender, due=due, good=int(channel.good),
                deliveries=deliveries, records=channel.visible_records().copy(), cache_age=age,
                cache_remaining_lead=lead, pending_after_send=channel.pending.copy(),
                reward_physical=reward_physical, reward_net=reward_net, served_users=served,
                Q=q, shadow_central_motion=shadow_mean, connected_users=bits,
            )
            for key in trace:
                trace[key].append(sample[key])
        last[:] = command
        raw, state = raw_next, info["next_state"]
        positions.append(np.asarray(raw, dtype=np.float32)[:, :3].copy())
        channel.advance()
        if (terminated or truncated) and t + 1 < horizon:
            raise RuntimeError(f"incomplete native episode {t + 1}/{horizon}")
    counts[f"{metadata['phase']}_episodes"] += 1
    coordinates = horizon * 5 * 3
    row = dict(
        metadata, reset_seed=reset_seed, channel_seed=channel_seed, steps=horizon,
        initial_scene_sha256=scene_hash,
        channel_sequence_sha256=hashlib.sha256(bytes(good_sequence)).hexdigest(),
        J_net=(sum(physical) - sum(charges)) / horizon, J_physical=sum(physical) / horizon,
        charge_per_tick=sum(charges) / horizon, served_users_per_tick=sum(services) / horizon,
        Q=sum(quality) / horizon, worst_tick_service=min(services),
        zero_service_steps=services.count(0), longest_zero_service=longest_zero_run(services),
        boundary_fraction=boundary_count / (5 * horizon), height_floor_fraction=floor_count / (5 * horizon),
        height_ceiling_fraction=ceiling_count / (5 * horizon), mean_height_m=height_sum / (5 * horizon),
        correction_rms=math.sqrt(correction_sq / coordinates), correction_abs_mean=correction_abs / coordinates,
        correction_max=correction_max, correction_saturation_fraction=saturated / coordinates,
        correction_nonzero_fraction=nonzero / coordinates,
        same_noise_action_change_rms=math.sqrt(executed_sq / coordinates),
        valid_future_cache_uses=valid_future_uses,
        shadow_response_rms=math.sqrt(response_sq / coordinates) if arm == "M_O" and trace is not None else None,
        shadow_response_max=response_max if arm == "M_O" and trace is not None else None,
        **channel.facts(),
    )
    if trace is not None:
        trace["position"] = np.asarray(positions, dtype=np.float32)
        trace["initial_state"] = initial_state
        trace["user_positions"] = np.asarray(state[15:115], dtype=np.float32).reshape(50, 2)
        trace["log_std"] = actor.log_std.detach().numpy().copy()
        np.savez_compressed(raw_path, **{key: np.asarray(values) for key, values in trace.items()})
        row["raw"] = str(raw_path)
        row["raw_sha256"] = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        row["action_sequence_sha256"] = hashlib.sha256(np.asarray(trace["action"], dtype=np.float32).tobytes()).hexdigest()
    emit(row)
    check()
    return None if storage is None else {key: torch.stack(items) for key, items in storage.items()}
