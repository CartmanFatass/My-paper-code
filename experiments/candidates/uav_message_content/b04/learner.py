"""Detached packet collection, motion PPO, and post-episode forecast labels."""

import hashlib
import math

import numpy as np
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.channel import Channel, payloads
from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import sample_actions
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import (
    AGENTS, actor_features, critic_features, team_reward,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import (
    clipped_policy_loss, recurrent_outputs, returns_to_go,
)
from .channel import ForecastChannel, packet_for
from .model import D, endpoints, forecast_context, motion_terms


def native_service(info):
    global_info = info["infos_dict"][AGENTS[0]]["global"]
    served = int(global_info["served_users"])
    if "connections" not in global_info or "sinr_matrix" not in global_info:
        return served, None
    connection = np.asarray(global_info["connections"], dtype=bool)
    sinr = np.asarray(global_info["sinr_matrix"])
    quality = np.clip((sinr[connection] - 3) / 30, 0, 1)
    return served, float(quality.mean()) if served else 0.0


def connection_bits(info):
    connection = np.asarray(info["infos_dict"][AGENTS[0]]["global"]["connections"])
    if connection.shape != (5, 50):
        raise ValueError("evaluation connection matrix contract changed")
    return np.any(connection.astype(bool), axis=0).astype(np.uint8)


def cache_timing(records, t, horizon=256):
    valid = records[..., 7] > 0
    sent = np.rint(records[..., 8] * 256).astype(np.int32)
    age = np.where(valid, t - sent, -1).astype(np.int16)
    lead = np.where(valid, np.maximum(np.minimum(10, horizon - sent) - age, 0), 0)
    return age, lead.astype(np.int16)


def _make_inputs(raw, state, last, remaining, channel, arm):
    extra = channel.features()
    base_actor = np.concatenate((actor_features(raw, last, remaining), extra), axis=1)
    base_critic = np.concatenate((critic_features(state, last, remaining), extra.ravel()))
    if base_actor.shape != (5, 171) or base_critic.shape != (451,):
        raise ValueError("CADC actor/critic input contract changed")
    if arm == "B0":
        return torch.from_numpy(base_actor), torch.from_numpy(base_critic)
    return (torch.from_numpy(np.concatenate((base_actor, channel.forecasts.reshape(5, 15)), axis=1)),
            torch.from_numpy(np.concatenate((base_critic, channel.forecasts.ravel()))))


def _shadow_inputs(x, shadow):
    changed = x.clone()
    changed[:, 171:] = torch.from_numpy(shadow.reshape(5, 15))
    return changed


@torch.no_grad()
def collect_episode(env, actor, critic, predictor, arm, horizon, reset_seed, channel_seed,
                    motion_rng, metadata, counts, emit, check, raw_path=None):
    check()
    raw, info = env.reset(seed=reset_seed)
    state = info["state"]
    initial_state = np.asarray(state).copy()
    counts["explicit_resets"] += 1
    scene_hash = hashlib.sha256(np.asarray(raw).tobytes() + np.asarray(state).tobytes()).hexdigest()
    channel = Channel(channel_seed) if arm == "B0" else ForecastChannel(channel_seed, horizon)
    last = np.zeros((5, 3), dtype=np.float32)
    remaining = np.zeros(5, dtype=np.int64)
    hidden = torch.zeros(1, 5, 64)
    names = ("obs", "hidden", "critic", "u", "logp", "value", "reward")
    storage = {key: [] for key in names} if metadata["phase"] == "train" else None
    labels = {key: [] for key in ("context", "first", "ordinary", "horizon", "target")}
    pending_labels = []
    positions = [np.asarray(raw, dtype=np.float32)[:, :3].copy()]
    ordinary_by_send = {}
    shadow_cache = np.zeros((5, 5, 3), dtype=np.float32)
    trace_names = ("actor_input", "critic_input", "pre_tanh_motion", "central_motion", "action",
                   "packet", "ordinary_endpoint", "sampled_cv_endpoint", "forecast_endpoint",
                   "sender", "due", "good", "deliveries", "records", "cache_age",
                   "cache_remaining_lead", "pending_after_send", "reward_physical", "reward_net",
                   "served_users", "Q", "shadow_central_motion", "connected_users")
    trace = {key: [] for key in trace_names} if raw_path is not None else None
    physical, charges, services, quality, good_sequence = [], [], [], [], []
    response_squares, response_maxima = [], []
    boundary_count = floor_count = ceiling_count = 0
    height_sum = 0.0
    for t in range(horizon):
        check()
        before_delivered = channel.delivered
        channel.begin_tick()
        deliveries = channel.delivered - before_delivered
        if arm == "F":
            for sender, sent, _ in channel.delivered_events:
                peers = np.arange(5) != sender
                shadow_cache[peers, sender] = ordinary_by_send[sent]
            _, leads = cache_timing(channel.records, t, horizon)
            shadow_cache[leads == 0] = 0
        x, cx = _make_inputs(raw, state, last, remaining, channel, arm)
        h0 = hidden[0].clone()
        mean, recurrent, hidden = actor(x[None], hidden)
        mean, recurrent = mean[0], recurrent[0]
        counts["behavior_actor_forward_calls"] += 1
        counts["behavior_actor_forward_rows"] += 5
        shadow_mean = np.zeros((5, 3), dtype=np.float32)
        if raw_path is not None and arm in ("O", "F"):
            shadow_x = _shadow_inputs(x, np.zeros_like(shadow_cache) if arm == "O" else shadow_cache)
            shadow_mean = actor(shadow_x[None], h0[None])[0][0].tanh().numpy().copy()
            counts["diagnostic_forward_calls"] += 1
            response = mean.tanh().numpy() - shadow_mean
            response_squares.append(float(np.mean(np.square(response))))
            response_maxima.append(float(np.max(np.abs(response))))
        if raw_path is not None:
            p = np.asarray(raw, dtype=np.float32)[:, :3]
            boundary_count += int((np.isclose(p[:, :2], 0, atol=1e-7, rtol=0) |
                                   np.isclose(p[:, :2], 1, atol=1e-7, rtol=0)).any(axis=1).sum())
            floor_count += int(np.isclose(p[:, 2], 0, atol=1e-7, rtol=0).sum())
            ceiling_count += int(np.isclose(p[:, 2], 1, atol=1e-7, rtol=0).sum())
            height_sum += float((50 + 100 * p[:, 2]).sum())
        value = critic(cx)
        counts["behavior_critic_forward_calls"] += 1
        counts["behavior_critic_forward_rows"] += 1
        eligible = torch.from_numpy(~channel.pending.copy())
        u, sends = sample_actions(actor, mean, recurrent, eligible, t, motion_rng, None)
        sender = t % 5
        if int(sends.sum()) != 1 or not bool(sends[sender]):
            raise RuntimeError("fixed RR sender/eligibility changed")
        logp, _ = motion_terms(actor, mean, u)
        if not torch.isfinite(logp).all() or not torch.isfinite(value):
            raise FloatingPointError("nonfinite sampled density or value")
        command = u.tanh().numpy()
        central = mean.tanh().numpy()
        first = ordinary = cv = forecast = None
        context = None
        if arm == "B0":
            packet = payloads(raw)[sender].copy()
            charge = channel.resolve(sends.numpy(), raw)
            due = t + (1 if channel.good else 5)
        else:
            k = min(10, horizon - t)
            if arm in ("O", "F"):
                first, ordinary, cv, forecast = endpoints(positions[-1][sender],
                    u[sender].tanh(), mean[sender].tanh(), k)
            if arm == "F":
                context = forecast_context(recurrent[sender], positions[-1][sender],
                                           u[sender].tanh(), mean[sender].tanh(), k)
                first, ordinary, cv, forecast = endpoints(positions[-1][sender],
                    u[sender].tanh(), mean[sender].tanh(), k, predictor(context))
                counts["predictor_forwards"] += 1
                ordinary_by_send[t] = ordinary.numpy().copy()
            encoded = np.zeros(3, dtype=np.float32) if arm == "G" else forecast.numpy()
            packet = packet_for(raw, sender, encoded)
            charge, due = channel.resolve_payload(sender, packet)
            if arm == "F" and due < horizon and metadata["phase"] == "train":
                pending_labels.append((t, sender, k, context.clone(), first.clone(), ordinary.clone()))
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
        served, q = native_service(info)
        if not math.isfinite(reward_net) or q is not None and not math.isfinite(q):
            raise FloatingPointError("nonfinite native outcome")
        physical.append(reward_physical)
        charges.append(charge)
        services.append(served)
        quality.append(q)
        counts["delivered_packets"] += deliveries
        if storage is not None:
            values = (x, h0, cx, u, logp, value,
                      torch.tensor(reward_net, dtype=torch.float32))
            for key, item in zip(names, values):
                storage[key].append(item.detach().clone())
        if trace is not None:
            age, lead = cache_timing(channel.records, t, horizon)
            records = channel.records.copy() if arm == "B0" else channel.visible_records().copy()
            sample = dict(actor_input=x.numpy(), critic_input=cx.numpy(), pre_tanh_motion=u.numpy(),
                          central_motion=central.copy(), action=command.copy(), packet=packet.copy(),
                          ordinary_endpoint=np.zeros(3, dtype=np.float32) if ordinary is None else ordinary.numpy(),
                          sampled_cv_endpoint=np.zeros(3, dtype=np.float32) if cv is None else cv.numpy(),
                          forecast_endpoint=np.zeros(3, dtype=np.float32) if arm in ("G", "B0") else forecast.numpy(),
                          sender=sender, due=due, good=int(channel.good), deliveries=deliveries,
                          records=records, cache_age=age, cache_remaining_lead=lead,
                          pending_after_send=channel.pending.copy(), reward_physical=reward_physical,
                          reward_net=reward_net, served_users=served, Q=np.nan if q is None else q,
                          shadow_central_motion=shadow_mean,
                          connected_users=connection_bits(info))
            for key in trace:
                trace[key].append(sample[key])
        last[:] = command
        raw, state = raw_next, info["next_state"]
        positions.append(np.asarray(raw, dtype=np.float32)[:, :3].copy())
        channel.advance()
        if (terminated or truncated) and t + 1 < horizon:
            raise RuntimeError(f"incomplete native episode {t + 1}/{horizon}")
    counts[f"{metadata['phase']}_episodes"] += 1
    if storage is not None and arm == "F":
        for sent, sender, k, context, first, ordinary in pending_labels:
            for key, value in (("context", context), ("first", first), ("ordinary", ordinary),
                               ("horizon", torch.tensor(k)),
                               ("target", torch.from_numpy(positions[sent + k][sender]))):
                labels[key].append(value.detach().clone())
        counts["eligible_labels"] += len(pending_labels)
    row = dict(metadata, reset_seed=reset_seed, channel_seed=channel_seed, steps=horizon,
               initial_scene_sha256=scene_hash,
               channel_sequence_sha256=hashlib.sha256(bytes(good_sequence)).hexdigest(),
               J_net=(sum(physical) - sum(charges)) / horizon,
               J_physical=sum(physical) / horizon, charge_per_tick=sum(charges) / horizon,
               served_users_per_tick=sum(services) / horizon,
               Q=(sum(quality) / horizon if all(x is not None for x in quality) else None),
               **channel.facts())
    if raw_path is not None:
        row.update(boundary_fraction=boundary_count / (5 * horizon),
                   height_floor_fraction=floor_count / (5 * horizon),
                   height_ceiling_fraction=ceiling_count / (5 * horizon),
                   mean_height_m=height_sum / (5 * horizon),
                   worst_service=min(services),
                   shadow_response_rms=math.sqrt(sum(response_squares) / horizon) if response_squares else None,
                   shadow_response_max=max(response_maxima) if response_maxima else None)
        trace["position"] = np.asarray(positions, dtype=np.float32)
        trace["initial_state"] = initial_state
        trace["user_positions"] = np.asarray(state[15:115], dtype=np.float32).reshape(50, 2)
        np.savez_compressed(raw_path, **{key: np.asarray(values) for key, values in trace.items()})
        row["raw"] = str(raw_path)
        row["raw_sha256"] = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        row["action_sequence_sha256"] = hashlib.sha256(np.asarray(trace["action"], dtype=np.float32).tobytes()).hexdigest()
    emit(row)
    check()
    if storage is None:
        return None
    episode = {key: torch.stack(items) for key, items in storage.items()}
    return episode, {key: torch.stack(items) for key, items in labels.items()} if arm == "F" else None


def update_motion(actor, critic, optimizer, episodes, counts, check, emit_update=None):
    rollout = {key: torch.stack([episode[key] for episode in episodes]) for key in episodes[0]}
    targets = returns_to_go(rollout["reward"])
    raw_advantage = targets - rollout["value"]
    advantages = ((raw_advantage - raw_advantage.mean()) /
                  (raw_advantage.std(unbiased=False) + 1e-8)).detach()
    params = list(actor.parameters()) + list(critic.parameters())
    for epoch in range(4):
        check()
        mean, _ = recurrent_outputs(actor, rollout, 32)
        counts["ppo_actor_forward_calls"] += 1
        counts["ppo_actor_forward_rows"] += int(rollout["obs"].shape[0] * rollout["obs"].shape[1] * 5)
        logp, entropy = motion_terms(actor, mean, rollout["u"])
        policy_loss = clipped_policy_loss(logp, rollout["logp"], advantages,
                                          torch.ones_like(logp, dtype=torch.bool))
        value_loss = (critic(rollout["critic"]) - targets).square().mean()
        counts["ppo_critic_forward_calls"] += 1
        counts["ppo_critic_forward_rows"] += int(rollout["critic"].shape[0] * rollout["critic"].shape[1])
        loss = policy_loss + .5 * value_loss - .01 * entropy.mean()
        if not torch.isfinite(loss):
            raise FloatingPointError("nonfinite PPO loss")
        optimizer.zero_grad()
        loss.backward()
        norm = torch.nn.utils.clip_grad_norm_(params, .5)
        if not torch.isfinite(norm):
            raise FloatingPointError("nonfinite PPO gradient")
        check()
        optimizer.step()
        counts["optimizer_steps"] += 1
        counts["replayed_actor_rows"] += int(rollout["obs"].shape[0] * rollout["obs"].shape[1] * 5)
        if not all(torch.isfinite(p).all() for p in params):
            raise FloatingPointError("nonfinite Adam parameters")
        if emit_update is not None:
            emit_update(dict(kind="ppo", epoch=epoch, loss=float(loss.detach()),
                             policy_loss=float(policy_loss.detach()), value_loss=float(value_loss.detach()),
                             gaussian_entropy=float(entropy.mean().detach()), grad_norm=float(norm)))


def update_predictor(predictor, optimizer, labels, counts, check, emit_update=None):
    batch = {key: torch.cat([episode[key] for episode in labels]) for key in labels[0]}
    if not len(batch["context"]):
        raise ValueError("F rollout has no eligible future labels")
    k = batch["horizon"].float()[:, None]
    speed = torch.as_tensor(D)[None]
    lower = torch.clamp(batch["first"] - (k - 1) * speed, min=0)
    upper = torch.clamp(batch["first"] + (k - 1) * speed, max=1)
    for epoch in range(4):
        check()
        residual = predictor(batch["context"])
        prediction = torch.maximum(lower, torch.minimum(upper,
            batch["ordinary"] + 2 * (k - 1) * speed * torch.tanh(residual)))
        loss = (((prediction - batch["target"]) / (k * speed)).square()).mean()
        if not torch.isfinite(loss):
            raise FloatingPointError("nonfinite predictor loss")
        optimizer.zero_grad()
        loss.backward()
        norm = torch.nn.utils.clip_grad_norm_(predictor.parameters(), .5)
        if not torch.isfinite(norm):
            raise FloatingPointError("nonfinite predictor gradient")
        check()
        optimizer.step()
        counts["predictor_updates"] += 1
        counts["predictor_rows"] += len(batch["context"])
        if not all(torch.isfinite(p).all() for p in predictor.parameters()):
            raise FloatingPointError("nonfinite predictor parameters")
        if emit_update is not None:
            emit_update(dict(kind="predictor", epoch=epoch, loss=float(loss.detach()),
                             grad_norm=float(norm), eligible_rows=len(batch["context"])))
