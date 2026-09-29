"""Geometry-only collection with verified, constructor-independent innovations."""

import hashlib

import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import sample_actions
from experiments.candidates.uav_message_content.b05.collector import collect_episode as collect_retained


def state_hash(rng):
    return hashlib.sha256(rng.get_state().numpy().tobytes()).hexdigest()


def collect_episode(env, actor, critic, arm, horizon, reset_seed, channel_seed,
                    motion_rng, metadata, counts, emit, check=lambda: None, raw_path=None):
    if arm not in ("K", "D", "B40"):
        raise ValueError("fixed B06 arm")
    witness_rng = torch.Generator(device="cpu")
    witness_rng.set_state(motion_rng.get_state())
    initial_state = state_hash(motion_rng)
    innovations = hashlib.sha256()
    vectors = 0

    def sample_verified(policy, mean, recurrent, eligible, tick, rng, send_rng):
        nonlocal vectors
        u, sends = sample_actions(policy, mean, recurrent, eligible, tick, rng, send_rng)
        epsilon = torch.stack([torch.randn(3, generator=witness_rng) for _ in range(5)])
        expected = mean + policy.log_std.clamp(-5, 2).exp() * epsilon
        if not torch.equal(u, expected):
            raise RuntimeError("actual composed sample does not match the independent innovation stream")
        innovations.update(epsilon.numpy().tobytes())
        vectors += 5
        return u, sends

    def emit_verified(row):
        if not torch.equal(witness_rng.get_state(), motion_rng.get_state()):
            raise RuntimeError("motion generator consumption differs from five three-vector draws per tick")
        if vectors != 5 * horizon:
            raise RuntimeError("incomplete motion innovation witness")
        emit(dict(row, motion_rng_start_sha256=initial_state,
                  motion_rng_end_sha256=state_hash(motion_rng),
                  innovation_sha256=innovations.hexdigest(), innovation_vectors=vectors))

    return collect_retained(
        env, actor, critic, "B40" if arm == "B40" else "M_G", horizon,
        reset_seed, channel_seed, motion_rng, metadata, counts, emit_verified, check,
        raw_path=raw_path, sampler=sample_verified,
    )
