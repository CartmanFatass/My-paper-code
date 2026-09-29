"""Native RR collection and delayed-content recurrent PPO."""

import hashlib
import math

import numpy as np
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import sample_actions
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import (
    AGENTS, actor_features, critic_features, team_reward,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import (
    clipped_policy_loss, optimizer_for, recurrent_outputs, returns_to_go,
)
from .channel import ContentChannel, Sightings, hand_payload
from .model import SCALAR_ACTOR_COLUMNS, action_terms, parameter_groups, sample_content


def native_service(info):
    global_info = info["infos_dict"][AGENTS[0]]["global"]
    served = int(global_info["served_users"])
    if "connections" not in global_info or "sinr_matrix" not in global_info:
        return served, None
    connection = np.asarray(global_info["connections"], dtype=bool)
    sinr = np.asarray(global_info["sinr_matrix"])
    quality = np.clip((sinr[connection] - 3) / 30, 0, 1)
    return served, float(quality.mean()) if served else 0.0


def content_can_affect_later_action(t, delay, horizon):
    return t + delay < horizon


@torch.no_grad()
def collect_episode(env, actor, critic, arm, horizon, reset_seed, channel_seed,
                    motion_rng, content_rng, metadata, counts, emit, check,
                    raw_path=None):
    check()
    raw, info = env.reset(seed=reset_seed)
    state = info["state"]
    counts["explicit_resets"] += 1
    scene_hash = hashlib.sha256(np.asarray(raw).tobytes() + np.asarray(state).tobytes()).hexdigest()
    channel = ContentChannel(channel_seed)
    sightings = Sightings()
    last = np.zeros((5, 3), dtype=np.float32)
    remaining = np.zeros(5, dtype=np.int64)
    hidden = torch.zeros(1, 5, 64)
    names = ("obs", "hidden", "critic", "u", "content_u", "content_mask", "logp", "value", "reward")
    storage = {key: [] for key in names} if metadata["phase"] == "train" else None
    trace = {key: [] for key in ("actor_input", "critic_input", "pre_tanh_motion", "action",
                                  "packet", "pre_tanh_content", "content_credit_mask", "due",
                                  "good", "deliveries", "reward_physical", "reward_net",
                                  "served_users", "Q", "records", "pending_after_send",
                                  "sender", "old_compound_logp", "scalar_response_rms",
                                  "scalar_response_max") } if raw_path else None
    physical, charges, services, quality, good_sequence = [], [], [], [], []
    responses, response_maxima = [], []
    boundary_count = floor_count = ceiling_count = 0
    height_sum = 0.0
    for t in range(horizon):
        check()
        phase = metadata["phase"]
        before_delivered = channel.delivered
        channel.begin_tick()
        deliveries = channel.delivered - before_delivered
        sightings.observe(raw)
        extras = channel.features()
        x = torch.from_numpy(np.concatenate((actor_features(raw, last, remaining), extras), axis=1))
        cx = torch.from_numpy(np.concatenate((critic_features(state, last, remaining), extras.ravel())))
        if x.shape != (5, 171) or cx.shape != (451,):
            raise ValueError("CADC actor/critic input contract changed")
        h0 = hidden[0].clone()
        mean, recurrent, hidden = actor(x[None], hidden)
        mean, recurrent = mean[0], recurrent[0]
        if phase != "train":
            zero_x = x.clone()
            zero_x[:, SCALAR_ACTOR_COLUMNS] = 0
            zero_mean = actor(zero_x[None], h0[None])[0][0]
            response = (mean.tanh() - zero_mean.tanh()).abs()
            responses.append(float(response.square().mean().sqrt()))
            response_maxima.append(float(response.max()))
            counts["diagnostic_forward_calls"] += 1
            positions = np.asarray(raw, dtype=np.float32)[:, :3]
            boundary_count += int((np.isclose(positions[:, :2], 0, atol=1e-7, rtol=0) |
                                   np.isclose(positions[:, :2], 1, atol=1e-7, rtol=0)).any(axis=1).sum())
            floor_count += int(np.isclose(positions[:, 2], 0, atol=1e-7, rtol=0).sum())
            ceiling_count += int(np.isclose(positions[:, 2], 1, atol=1e-7, rtol=0).sum())
            height_sum += float((50 + 100 * positions[:, 2]).sum())
        value = critic(cx)
        eligible = torch.from_numpy(~channel.pending.copy())
        u, sends = sample_actions(actor, mean, recurrent, eligible, t, motion_rng, content_rng)
        sender = t % 5
        if int(sends.sum()) != 1 or not bool(sends[sender]):
            raise RuntimeError("fixed RR sender/eligibility changed")
        content_u = torch.zeros((5, 1))
        mask = torch.zeros(5, dtype=torch.bool)
        if arm == "L":
            sampled, encoded = sample_content(actor, recurrent, sender, content_rng)
            content_u[sender] = sampled
            packet = hand_payload(arm, raw, sender, sightings, encoded.item())
            counts["content_samples"] += 1
            counts[f"{phase}_content_samples"] += 1
        else:
            packet = hand_payload(arm, raw, sender, sightings)
        delay = 1 if channel.good else 5
        if arm == "L" and content_can_affect_later_action(t, delay, horizon):
            mask[sender] = True
            counts["content_credit_rows"] += 1
            counts[f"{phase}_content_credit_rows"] += 1
        logp, _ = action_terms(actor, mean, recurrent, u, content_u, mask)
        if not torch.isfinite(logp).all() or not torch.isfinite(value):
            raise FloatingPointError("nonfinite sampled density or value")
        command = u.tanh().numpy()
        good_sequence.append(int(channel.good))
        charge, due = channel.resolve_payload(sender, packet)
        counts["motion_samples"] += 5
        counts[f"{phase}_motion_samples"] += 5
        counts["broadcasts"] += 1
        counts[f"{phase}_broadcasts"] += 1
        counts["attempts"] += 1
        if due >= horizon:
            counts["censored_packets"] += 1
            counts[f"{phase}_censored_packets"] += 1
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
        counts[f"{phase}_delivered_packets"] += deliveries
        if storage is not None:
            values = (x, h0, cx, u, content_u, mask, logp, value,
                      torch.tensor(reward_net, dtype=torch.float32))
            for key, item in zip(names, values):
                storage[key].append(item.detach().clone())
        if trace is not None:
            values = (x.numpy(), cx.numpy(), u.numpy(), command.copy(), packet.copy(),
                      content_u[sender].numpy().copy(), bool(mask[sender]), due,
                      int(channel.good), deliveries, reward_physical, reward_net,
                      served, np.nan if q is None else q, channel.records.copy(), channel.pending.copy(),
                      sender, logp.numpy().copy(),
                      responses[-1] if responses else np.nan,
                      response_maxima[-1] if response_maxima else np.nan)
            for key, item in zip(trace, values):
                trace[key].append(item)
        last[:] = command
        raw, state = raw_next, info["next_state"]
        channel.advance()
        if (terminated or truncated) and t + 1 < horizon:
            raise RuntimeError(f"incomplete native episode {t + 1}/{horizon}")
    counts[f"{metadata['phase']}_episodes"] += 1
    row = dict(metadata, reset_seed=reset_seed, channel_seed=channel_seed, steps=horizon,
               initial_scene_sha256=scene_hash,
               channel_sequence_sha256=hashlib.sha256(bytes(good_sequence)).hexdigest(),
               J_net=(sum(physical) - sum(charges)) / horizon,
               J_physical=sum(physical) / horizon, charge_per_tick=sum(charges) / horizon,
               served_users_per_tick=sum(services) / horizon,
               Q=(sum(quality) / horizon if all(x is not None for x in quality) else None),
               **channel.facts())
    if phase != "train":
        row.update(scalar_response_rms=math.sqrt(sum(x * x for x in responses) / horizon),
                   scalar_response_max=max(response_maxima),
                   boundary_fraction=boundary_count / (5 * horizon),
                   height_floor_fraction=floor_count / (5 * horizon),
                   height_ceiling_fraction=ceiling_count / (5 * horizon),
                   mean_height_m=height_sum / (5 * horizon))
    if raw_path is not None:
        np.savez_compressed(raw_path, **{key: np.asarray(values) for key, values in trace.items()})
        row["raw"] = str(raw_path)
        row["raw_sha256"] = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        row["action_sequence_sha256"] = hashlib.sha256(
            np.asarray(trace["action"], dtype=np.float32).tobytes()).hexdigest()
    emit(row)
    check()
    return {key: torch.stack(items) for key, items in storage.items()} if storage is not None else None


def update(actor, critic, optimizer, episodes, counts, check, chunk=32, emit_update=None):
    rollout = {key: torch.stack([episode[key] for episode in episodes]) for key in episodes[0]}
    targets = returns_to_go(rollout["reward"])
    raw_advantage = targets - rollout["value"]
    advantages = ((raw_advantage - raw_advantage.mean()) /
                  (raw_advantage.std(unbiased=False) + 1e-8)).detach()
    groups = parameter_groups(actor, critic)
    params = list(actor.parameters()) + list(critic.parameters())
    records = []
    for epoch in range(4):
        check()
        mean, recurrent = recurrent_outputs(actor, rollout, chunk)
        logp, entropy = action_terms(actor, mean, recurrent, rollout["u"],
                                     rollout["content_u"], rollout["content_mask"])
        policy_loss = clipped_policy_loss(logp, rollout["logp"], advantages,
                                          torch.ones_like(logp, dtype=torch.bool))
        value_loss = (critic(rollout["critic"]) - targets).square().mean()
        loss = policy_loss + .5 * value_loss - .01 * entropy.mean()
        if not torch.isfinite(loss):
            raise FloatingPointError("nonfinite PPO loss")
        optimizer.zero_grad()
        loss.backward()
        grad_groups = {name: math.sqrt(sum(float(p.grad.detach().square().sum())
                                           for p in group if p.grad is not None))
                       for name, group in groups.items()}
        grad_norm = torch.nn.utils.clip_grad_norm_(params, .5)
        if not torch.isfinite(grad_norm):
            raise FloatingPointError("nonfinite PPO gradient")
        check()
        optimizer.step()
        counts["optimizer_steps"] += 1
        counts["replayed_actor_rows"] += int(rollout["obs"].shape[0] * rollout["obs"].shape[1] * 5)
        if not all(torch.isfinite(p).all() for p in params):
            raise FloatingPointError("nonfinite Adam parameters")
        record = dict(epoch=epoch, loss=float(loss.detach()),
                            policy_loss=float(policy_loss.detach()),
                            value_loss=float(value_loss.detach()),
                            gaussian_entropy=float(entropy.mean().detach()),
                            grad_norm=float(grad_norm), grad_groups=grad_groups)
        records.append(record)
        if emit_update is not None:
            emit_update(record)
    return records
