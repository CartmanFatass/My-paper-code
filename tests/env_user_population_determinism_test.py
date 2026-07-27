"""Pin the environment fact that breaks fixed-history prefix replay.

This file exists to make a repository fact fail loudly if it ever changes,
because a silent change would alter the meaning of every Scenario-7 comparison
without anyone deciding to.

The fact (measured 2026-07-26, see
`docs/research/cdc/EVIDENCE_NOTES/20260726_D7_S_PREFIX_REPLAY_IS_NOT_FIXED_HISTORY.md`):
two FRESHLY CONSTRUCTED environments carrying the same episode seed do not
share a user population. `reset(seed=)` is idempotent on one object but does not
re-derive the user layout from the seed, so the layout is fixed by
construction-time state.

Two consequences the D7.S line depends on:

1. The R2 shared-prefix realization is a CORRECTNESS fix. One env construction
   per event is the only reason all arms of an event share one user world.
2. `compute_state_hash` cannot detect the divergence -- it covers UAV positions,
   battery, charging, station occupancy/queue, lifecycle mask and duty map, and
   no user, cluster or channel state.

If someone seeds the user layout properly, `test_fresh_envs_with_the_same_seed_do_not_share_users`
starts failing. That is not a broken test -- it is a decision point. Seeding the
layout changes what "same topology" means and what prior results compared, and
it must go to External Pro rather than being absorbed by deleting this file.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import scripts.audit_d7_s_event_aligned as audit

SEED = 12345


def _env():
    from envs.pettingzoo.scenario7_energy_aware import UAVEnergyAwareRelayEnv
    return UAVEnergyAwareRelayEnv(config=audit.build_config(), energy_stage="S3")


@pytest.fixture(scope="module")
def two_seeded_envs():
    a, b = _env(), _env()
    a.reset(seed=SEED)
    b.reset(seed=SEED)
    return a, b


def test_reset_with_the_same_seed_is_idempotent_on_one_object():
    """The seed does control everything reset re-derives -- which is why the
    divergence below is easy to miss."""
    env = _env()
    env.reset(seed=SEED)
    first = np.array(env.user_positions, dtype=float).copy()
    env.reset(seed=SEED)
    second = np.array(env.user_positions, dtype=float).copy()
    assert np.array_equal(first, second)


def test_fresh_envs_with_the_same_seed_do_not_share_users(two_seeded_envs):
    """The load-bearing fact. If this starts failing, read this file's
    docstring before changing anything."""
    a, b = two_seeded_envs
    ua = np.array(a.user_positions, dtype=float)
    ub = np.array(b.user_positions, dtype=float)
    assert ua.shape == ub.shape
    assert not np.array_equal(ua, ub), (
        "User layout is now seed-determined across constructions. This changes "
        "what 'same topology' means and what every prior Scenario-7 comparison "
        "compared. Escalate to External Pro; do not delete this test."
    )


def test_uav_positions_are_seed_determined_across_constructions(two_seeded_envs):
    """The contrast that makes the defect subtle: the UAV side IS reproducible,
    so a guard looking only at UAVs sees a clean, identical prefix."""
    a, b = two_seeded_envs
    assert np.array_equal(np.array(a.uav_positions, dtype=float),
                          np.array(b.uav_positions, dtype=float))


def test_state_hash_cannot_see_the_user_divergence(two_seeded_envs):
    """Why the frozen fixed-history assertion passed on every fork: the hashed
    surface excludes exactly the state that diverges."""
    a, b = two_seeded_envs
    duty_map = {i: i for i in range(int(a.n_uavs))}
    hash_a = audit.compute_state_hash(audit.real_env_state_snapshot(a, duty_map))
    hash_b = audit.compute_state_hash(audit.real_env_state_snapshot(b, duty_map))

    assert not np.array_equal(np.array(a.user_positions, dtype=float),
                              np.array(b.user_positions, dtype=float))
    assert hash_a == hash_b, (
        "The state hash now distinguishes these environments. If the hashed "
        "surface was widened, the fixed-history assertion means something "
        "different than it did at freeze -- escalate rather than adjust."
    )
