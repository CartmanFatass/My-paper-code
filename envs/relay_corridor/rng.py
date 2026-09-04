"""Key-stable RNG streams for the relay corridor host.

Mechanics page, "Entities": entity RNG keys are ``(master seed, episode, entity
id)``; region-event keys replace ``entity id`` with ``region id``.  ADR 02
invariant 2 requires those streams to be *key-stable* (the same key always
yields the same tape) and *order-independent* (the tape does not depend on the
position of the episode inside a batch, nor on how many other streams were
built first).

The implementation therefore never draws from a shared global generator.  Each
key is turned into its own :class:`numpy.random.SeedSequence` and its own
Philox bit generator; nothing about batch order can reach the draws.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np

#: Stream kind for per-agent (entity) draws, keyed by ``(seed, episode, agent id)``.
STREAM_ENTITY = 1

#: Stream kind for per-region event draws, keyed by ``(seed, episode, region id)``.
STREAM_REGION_EVENT = 2

__all__ = [
    "STREAM_ENTITY",
    "STREAM_REGION_EVENT",
    "stream_key",
    "stream_generator",
]


def stream_key(master_seed: int, episode: int, kind: int, entity_id: int) -> Tuple[int, int, int, int]:
    """Return the canonical, hashable stream key.

    ``kind`` is :data:`STREAM_ENTITY` or :data:`STREAM_REGION_EVENT`; it keeps
    an agent id and a region id with the same integer value on disjoint
    streams.
    """
    key = (int(master_seed), int(episode), int(kind), int(entity_id))
    if key[0] < 0 or key[1] < 0 or key[3] < 0:
        raise ValueError(f"stream key components must be non-negative, got {key}")
    if key[2] not in (STREAM_ENTITY, STREAM_REGION_EVENT):
        raise ValueError(f"unknown stream kind {key[2]}")
    return key


def stream_generator(master_seed: int, episode: int, kind: int, entity_id: int) -> np.random.Generator:
    """Build the generator for one key.

    The generator depends on the key alone, so two hosts that hold the same
    episode at different batch positions draw identical tapes.
    """
    key = stream_key(master_seed, episode, kind, entity_id)
    seed_sequence = np.random.SeedSequence(entropy=list(key))
    return np.random.Generator(np.random.Philox(seed_sequence))
