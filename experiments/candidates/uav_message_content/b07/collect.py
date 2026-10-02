"""Own-history native evaluation with one actor call and five motion draws per tick."""

import hashlib
from pathlib import Path

import numpy as np
import torch

from experiments.candidates.uav_message_content.b05.collector import native_outcome
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import actor_features, team_reward
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import tanh_log_prob
from .contract import artifact, increment, require
from .receiver import forward_step
from .transport import ByteChannel, beacon


def make_input(raw, last, channel):
    return torch.from_numpy(np.concatenate((actor_features(raw, last, np.zeros(5, dtype=np.int64)),
                                           channel.features(), np.zeros((5, 15), dtype=np.float32)), 1))


def rng_hash(rng):
    return hashlib.sha256(rng.get_state().numpy().tobytes()).hexdigest()


@torch.no_grad()
def _collect_episode(env, actor, kind, codec, world, path, counts, progress, horizon, partial):
    require(1 <= horizon <= 256, "native horizon")
    physical_seed, channel_seed, motion_seed = 1981002000 + world, 1981007000 + world, 1981003000 + world
    raw, info = env.reset(seed=physical_seed)
    increment(counts, "explicit_resets")
    channel = ByteChannel(channel_seed, codec)
    motion = torch.Generator().manual_seed(motion_seed)
    witness = torch.Generator().manual_seed(motion_seed)
    start_rng = rng_hash(motion)
    innovation_digest = hashlib.sha256()
    scene_digest = hashlib.sha256(raw.tobytes() + np.asarray(info["state"]).tobytes()).hexdigest()
    initial_state = np.asarray(info["state"]).copy()
    last, hidden = np.zeros((5, 3), dtype=np.float32), torch.zeros(1, 5, 64)
    trace = {k: [] for k in ("raw_observation", "actor_input", "composed_mean", "pre_tanh_motion", "action",
                             "sample_logp", "packet_bytes", "beacon_bytes", "due", "records",
                             "pending_after_send", "served_users", "Q", "connected_users",
                             "reward_physical", "reward_net", "deliveries")}
    xyz = [np.asarray(env.env.uav_positions, dtype=np.float64).copy()]
    users = np.asarray(env.env.user_positions, dtype=np.float64).copy()
    partial.update(trace=trace, physical_position=xyz, user_positions=users, initial_state=initial_state,
                   log_std=actor.log_std.detach().numpy().copy())
    for tick in range(horizon):
        channel.begin_tick()
        x = make_input(raw, last, channel)
        mean, _, hidden = forward_step(actor, x, hidden, kind)
        mean = mean[0]
        increment(counts, "native_actor_calls")
        increment(counts, "native_actor_rows", 5)
        epsilon = torch.stack([torch.randn(3, generator=motion) for _ in range(5)])
        independent = torch.stack([torch.randn(3, generator=witness) for _ in range(5)])
        require(torch.equal(epsilon, independent), "native innovation witness")
        innovation_digest.update(independent.numpy().tobytes())
        increment(counts, "motion_vectors", 5)
        u = mean + actor.log_std.clamp(-5, 2).exp() * epsilon
        logp = tanh_log_prob(u, mean, actor.log_std)
        require(bool(torch.isfinite(mean).all() and torch.isfinite(logp).all()), "nonfinite native actor")
        action = u.tanh().numpy()
        packet, due = channel.send(raw)
        public = beacon(tick, channel.good)
        records = channel.records.copy()
        pending = channel.pending.copy()
        # Increment immediately before the accepted native effect, retaining an interrupted frontier.
        increment(counts, "native_step_calls")
        progress()
        next_raw, _, terminated, truncated, info = env.step(action)
        increment(counts, "native_steps")
        reward = team_reward(info)
        served, q, bits = native_outcome(info, connections=True)
        sample = dict(raw_observation=raw.copy(), actor_input=x.numpy(), composed_mean=mean.numpy(),
                      pre_tanh_motion=u.numpy(), action=action, sample_logp=logp.numpy(),
                      packet_bytes=np.frombuffer(packet, dtype=np.uint8).copy(),
                      beacon_bytes=np.frombuffer(public, dtype=np.uint8).copy(), due=due,
                      records=records, pending_after_send=pending, served_users=served, Q=q,
                      connected_users=bits, reward_physical=reward, reward_net=reward - .001,
                      deliveries=len(channel.delivered_events))
        for key, value in sample.items():
            trace[key].append(value)
        xyz.append(np.asarray(env.env.uav_positions, dtype=np.float64).copy())
        require(np.array_equal(users, np.asarray(env.env.user_positions)), "users moved")
        last[:] = action
        raw = next_raw
        channel.advance()
        require(not (terminated or truncated) or tick + 1 == horizon, "early native termination")
    require(torch.equal(motion.get_state(), witness.get_state()), "motion generator consumption")
    arrays = {key: np.asarray(value) for key, value in trace.items()}
    arrays.update(physical_position=np.asarray(xyz), user_positions=users, initial_state=initial_state)
    arrays["log_std"] = actor.log_std.detach().numpy().copy()
    np.savez_compressed(path, **arrays)
    increment(counts, "native_episodes")
    row = dict(world=world, steps=horizon, physical_seed=physical_seed, channel_seed=channel_seed,
               motion_seed=motion_seed, initial_scene_sha256=scene_digest,
               user_positions_sha256=hashlib.sha256(users.tobytes()).hexdigest(),
               channel_sequence_sha256=hashlib.sha256(arrays["beacon_bytes"][:, 1].tobytes()).hexdigest(),
               innovation_sha256=innovation_digest.hexdigest(), innovation_vectors=5 * horizon,
               motion_rng_start_sha256=start_rng, motion_rng_end_sha256=rng_hash(motion),
               action_sequence_sha256=hashlib.sha256(arrays["action"].tobytes()).hexdigest(),
               raw=artifact(path), J_net=float(arrays["reward_net"].mean()),
               J_physical=float(arrays["reward_physical"].mean()),
               served_users_per_tick=float(arrays["served_users"].mean()), Q=float(arrays["Q"].mean()),
               delivered=channel.delivered, censored=len(channel.inflight),
               codec_encode_cpu_seconds=codec.encode_cpu_seconds,
               codec_decode_cpu_seconds=codec.decode_cpu_seconds, **channel.facts())
    require(row["delivered"] + row["censored"] == horizon, "terminal packet count")
    return row


def collect_episode(env, actor, kind, codec, world, path, counts, progress=lambda: None, horizon=256):
    partial = {}
    try:
        return _collect_episode(env, actor, kind, codec, world, path, counts, progress, horizon, partial)
    except Exception:
        if partial:
            arrays = {key: np.asarray(value) for key, value in partial.pop("trace").items()}
            arrays.update({key: np.asarray(value) for key, value in partial.items()})
            np.savez_compressed(Path(path).with_suffix(".partial.npz"), **arrays)
        raise
