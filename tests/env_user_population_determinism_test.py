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

Task 14 (R3 section E) resolved this WITHOUT changing `reset(seed=)`, and the
predicted failure of `test_fresh_envs_with_the_same_seed_do_not_share_users`
therefore did not happen. The measurement that decided it is at the bottom of
this file's second section: the divergence was never unseeded user generation.
The user RNG stream is already fully seed-controlled -- pin `ground_bs_positions`
before the reset that generates users and two fresh envs produce bit-identical
user populations. The single unseeded input was the BS layout, which
`_generate_forced_relay_cluster_positions` reads to choose its remote corner.

So the repair is an ORDERING plus an explicit seed, not a new draw:
`regenerate_user_world` re-derives the world once the topology is already
pinned. `reset(seed=)` is untouched, so the fact pinned by the first section
below is still true and prior comparisons still mean exactly what they meant.

**The distribution claim, stated precisely, because a looser version of it was
wrong.** The GENERATOR and its parameters are untouched: same routines, same
`cluster_std`, same cluster count, and measured per-cluster spread is unchanged
(109.59 +/- 31.99 old vs 110.09 +/- 32.83 new over 400 draws each). What DID
change is where one factor lives. The remote-cluster corner is chosen from the
BS quadrant; under the old ordering that was the discarded construction-time
layout, so it was an unseeded roughly-uniform draw varying EPISODE to episode,
and under the new ordering it is a deterministic function of the pinned
topology, constant across every episode of that topology.

That is a real change to the variance decomposition — the largest geometric
factor in the user world moved from the within-topology episode level to the
topology level — and it is disclosed rather than absorbed. It is also the more
faithful behaviour: under the old ordering the "remote" cluster was placed
relative to a BS layout the episode then threw away, so in roughly three
episodes in four the remote users were not actually remote from the base
stations the episode ran with, which is the premise the forced-relay scenario
rests on.

Both halves must keep holding, so this file now pins both:

- section 1: plain `reset(seed=)` still does not reproduce a user world across
  constructions (unchanged repository fact, unchanged meaning of prior results);
- section 2: the pinned path DOES, and is independent of the arm streams.

If section 1 ever starts failing, that is still the escalation this docstring
originally described. Section 2 failing means episode-world provenance has
silently regressed to the state that retired ep64.
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


def _env_with_bs_in_corner(corner):
    """A fresh env whose ground-BS layout sits in a CHOSEN corner, with users
    then generated against it.

    Two freshly constructed envs land in the same BS quadrant about a third of
    the time (measured 2026-07-27, 60 trials: 35 %), and when they do they share
    a user world exactly. Building the pair from unseeded constructions
    therefore makes the divergence a coin flip. Choosing the quadrant makes the
    same fact deterministic without changing what it says.
    """
    env = _env()
    env.reset(seed=SEED)
    fx, fy = corner
    size = env.area_size
    env.ground_bs_positions = np.array(
        [[fx * size, fy * size, 30.0] for _ in range(env.n_ground_bs)], dtype=float)
    env.reset(seed=SEED)          # regenerate users against the chosen layout
    return env


@pytest.fixture(scope="module")
def two_seeded_envs():
    """Same episode seed, BS layouts in OPPOSITE corners -- the deterministic
    form of "two fresh constructions that happened to disagree"."""
    return _env_with_bs_in_corner((0.05, 0.05)), _env_with_bs_in_corner((0.95, 0.95))


def test_reset_with_the_same_seed_is_idempotent_on_one_object():
    """The seed does control everything reset re-derives -- which is why the
    divergence below is easy to miss."""
    env = _env()
    env.reset(seed=SEED)
    first = np.array(env.user_positions, dtype=float).copy()
    env.reset(seed=SEED)
    second = np.array(env.user_positions, dtype=float).copy()
    assert np.array_equal(first, second)


def test_the_user_world_is_a_function_of_the_bs_quadrant():
    """The mechanism, stated exactly. `_generate_forced_relay_cluster_positions`
    reads `ground_bs_positions` only to pick the remote corner, so the user
    world is a deterministic function of (episode seed, BS quadrant) -- not of
    the BS coordinates themselves, and not of anything continuous.

    Measured 2026-07-27 over 60 unseeded construction pairs: 'shared user world'
    and 'same BS quadrant' agreed 60/60. That is why the divergence is a
    discrete kilometre-scale jump rather than jitter, and why it appears only
    about 65 % of the time."""
    same_a = _env_with_bs_in_corner((0.05, 0.05))
    same_b = _env_with_bs_in_corner((0.10, 0.10))     # same quadrant, different coords
    diff = _env_with_bs_in_corner((0.95, 0.95))       # opposite quadrant

    assert np.array_equal(np.asarray(same_a.user_positions, dtype=float),
                          np.asarray(same_b.user_positions, dtype=float)), (
        "Same quadrant must give the same user world -- the BS coordinates "
        "themselves are not an input to user generation."
    )
    assert not np.array_equal(np.asarray(same_a.user_positions, dtype=float),
                              np.asarray(diff.user_positions, dtype=float))


def test_fresh_envs_with_the_same_seed_do_not_share_users(two_seeded_envs):
    """The load-bearing fact. If this starts failing, read this file's
    docstring before changing anything.

    Note the fixture pins the BS quadrants apart deliberately. Two genuinely
    fresh constructions agree about a third of the time, so this assertion held
    only probabilistically before 2026-07-27 and had been passing on luck."""
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


# =============================================================================
# Section 2 -- what the pinned path DOES guarantee (task 14, R3 section E)
# =============================================================================

TOPOLOGY_SEED = 20260726
UW_SEED = 777_000_111


def _pinned(user_world_seed=None, *, coords=None, coord_hash=None, episode_seed=4242):
    config = audit.build_config()
    if coords is None:
        coords, coord_hash = audit.build_topology_template(
            config, topology_seed=TOPOLOGY_SEED)[:2]
    env = audit.build_pinned_env(config, episode_seed=episode_seed, coords=coords,
                                  coord_hash=coord_hash,
                                  user_world_seed=user_world_seed)
    return env, coords, coord_hash


def test_the_bs_layout_was_the_only_unseeded_input():
    """The measurement the whole task-14 design rests on. Give two fresh envs
    the same BS layout BEFORE the reset that generates users and their user
    populations become bit-identical -- so the user RNG stream was always
    seed-controlled, and only the BS layout it reads was not."""
    a, b = _env(), _env()
    a.reset(seed=SEED)
    b.reset(seed=SEED)
    b.ground_bs_positions = a.ground_bs_positions.copy()
    b.charging_station_positions = a.charging_station_positions.copy()
    a.reset(seed=SEED)
    b.reset(seed=SEED)
    assert np.array_equal(np.array(a.user_positions, dtype=float),
                          np.array(b.user_positions, dtype=float))


def test_pinned_envs_with_the_same_user_world_seed_share_the_whole_user_world():
    """The guarantee task 14 buys, and the one ep64 could not make."""
    a, coords, coord_hash = _pinned(UW_SEED)
    b, _, _ = _pinned(UW_SEED, coords=coords, coord_hash=coord_hash)

    fa = audit.episode_world_fingerprint(a, seed_value=UW_SEED)
    fb = audit.episode_world_fingerprint(b, seed_value=UW_SEED)

    assert fa["fingerprint"] == fb["fingerprint"]
    assert fa["seed_controls_generation"] is True
    assert np.array_equal(np.array(a.user_positions, dtype=float),
                          np.array(b.user_positions, dtype=float))


def test_a_different_user_world_seed_gives_a_different_world():
    """Reproducible must not mean constant -- the user world stays a nested
    episode-level random factor, not part of topology identity."""
    a, coords, coord_hash = _pinned(UW_SEED)
    b, _, _ = _pinned(UW_SEED + 1, coords=coords, coord_hash=coord_hash)
    assert (audit.episode_world_fingerprint(a, seed_value=UW_SEED)["fingerprint"]
            != audit.episode_world_fingerprint(b, seed_value=UW_SEED + 1)["fingerprint"])


def test_regenerating_the_user_world_does_not_disturb_the_arm_stream():
    """The disjointness requirement, checked on behaviour rather than on the
    seed derivation: the continuation streams must see the same RNG they would
    have seen if no user world had been regenerated."""
    env, _, _ = _pinned(None)
    before = env.np_random.uniform(size=8).copy()

    env2, _, _ = _pinned(None)
    env2.regenerate_user_world(user_world_seed=UW_SEED)
    after = env2.np_random.uniform(size=8)

    assert np.array_equal(before, after)


def test_the_continuation_stream_is_installed_identically_whatever_the_user_world():
    """The named wrong-claim risk, asserted where it would actually bite.

    `test_regenerating_the_user_world_does_not_disturb_the_arm_stream` checks
    the save/restore around regeneration, but an implementation that restored
    the stream AND leaked the user-world seed into `stream_seed`'s field tuple
    would still pass it. This one goes through `fork_continuation`, which is
    what really installs the arm RNG: two pinned envs differing ONLY in
    `user_world_seed`, forked at the SAME continuation seed, must install
    byte-identical generator state.

    If this ever fails, SET and KEEP are no longer common-random-number paired
    and `U*` carries an RNG artifact that reads as a persistence effect."""
    cont_seed = 0xC0FFEE
    states = []
    coords = coord_hash = None
    for uw in (UW_SEED, UW_SEED + 12345):
        env, coords, coord_hash = _pinned(uw, coords=coords, coord_hash=coord_hash)
        duty_positions, centroids = audit.compute_duty_positions(env)
        audit.fork_continuation(
            env, duty_map_at_te={i: i for i in range(int(env.n_uavs))},
            duty_positions_at_te=duty_positions, service_centroids_at_te=centroids,
            schedule="constructive_mixed", horizon=0, continuation_seed=cont_seed)
        states.append(env.np_random.get_state())

    a, b = states
    assert a[0] == b[0]
    assert np.array_equal(a[1], b[1]), (
        "The continuation RNG state depends on the user world. The arm streams "
        "are supposed to be independent of it -- a user-world field has leaked "
        "into the continuation seed derivation."
    )
    assert (a[2], a[3], a[4]) == (b[2], b[3], b[4])


def test_seed_controls_generation_is_false_when_the_seed_was_never_applied():
    """The provenance flag is self-certifying: recording a seed the env never
    used must not produce a reproducibility claim the artifact cannot honour."""
    env, _, _ = _pinned(None)
    assert env.user_world_seed_applied is None
    assert audit.episode_world_fingerprint(env, seed_value=UW_SEED
                                            )["seed_controls_generation"] is False


def test_reset_clears_the_applied_user_world_seed():
    """`reset` re-draws users from the episode seed, so any previously applied
    user-world seed no longer describes the live world and must stop being
    claimed."""
    env, _, _ = _pinned(UW_SEED)
    assert env.user_world_seed_applied == UW_SEED
    env.reset(seed=SEED)
    assert env.user_world_seed_applied is None


def test_the_user_world_seed_must_be_applied_after_the_topology_is_pinned():
    """Why step 8 follows the hash assert instead of preceding it.

    Stated as QUADRANT, not as layout. "Two different BS layouts give two
    different worlds" is false — two layouts in the same quadrant give the SAME
    world, which is this file's whole mechanism. An earlier version of this test
    asserted the layout form and passed only because the two topology seeds it
    picked happened to land in different quadrants; on seeds 20260726/20260728
    the fingerprints are equal. That is the same passing-on-luck defect section 1
    was rewritten to remove."""
    a = _env_with_bs_in_corner((0.05, 0.05))
    b = _env_with_bs_in_corner((0.95, 0.95))
    a.regenerate_user_world(user_world_seed=UW_SEED)
    b.regenerate_user_world(user_world_seed=UW_SEED)

    fa = audit.episode_world_fingerprint(a, seed_value=UW_SEED)
    fb = audit.episode_world_fingerprint(b, seed_value=UW_SEED)
    assert fa["fingerprint"] != fb["fingerprint"], (
        "The same user-world seed against two different BS QUADRANTS must give "
        "two different worlds -- otherwise the seed alone would be a valid "
        "reproduction key, and it is not."
    )


def test_a_seed_alone_is_not_a_reproduction_key():
    """`seed_controls_generation` needs both halves. An env that had the seed
    applied but no proven topology is not regenerable, and must not claim to
    be."""
    env = _env_with_bs_in_corner((0.05, 0.05))
    env.regenerate_user_world(user_world_seed=UW_SEED)
    assert env.user_world_seed_applied == UW_SEED
    assert getattr(env, "pinned_coordinate_hash", None) is None
    assert audit.episode_world_fingerprint(
        env, seed_value=UW_SEED)["seed_controls_generation"] is False


@pytest.mark.parametrize("corner", [(0.05, 0.05), (0.95, 0.95)])
def test_regenerating_the_user_world_books_no_lifecycle_events(corner):
    """The defect `test_pinning_books_no_uav_leaves_before_the_episode_starts`
    can only catch by luck, asserted where it is deterministic.

    `_update_channel_state` books the difference between the serving sets it
    computes and the ones already in `self.connections` as handovers, joins and
    leaves. Across a `step` that is the right reading. Across
    `regenerate_user_world` it is not: the user world has been REPLACED, so the
    serving sets it diffs against belong to users that no longer exist, and every
    one of them is booked as a pre-episode "leave" that never happened.

    Why this test is deterministic and the one below is not. Whether the
    post-`reset` world puts any user in reach of the (seed-determined) UAV start
    positions is decided by the ground-BS quadrant, and that layout is drawn at
    CONSTRUCTION from `np.random.RandomState(None)` -- OS entropy, seeded by
    nothing. Unpinned, the pre-condition `served_before > 0` holds in roughly a
    third of constructions, so the leave count below was a coin flip run to run.
    Pinning the corner makes the same fact hold every time; the `served_before`
    assert states the pre-condition rather than assuming it, so a future world
    change makes this fail loudly instead of passing vacuously.
    """
    env = _env_with_bs_in_corner(corner)

    served_before = int(env.connections.sum())
    assert served_before > 0, (
        "Pre-condition for this test: the post-reset world must already have "
        "UAVs serving users, otherwise the regeneration below has nothing to "
        "mis-book and the assertions are vacuous."
    )
    assert int(env.uav_leaves_count) == 0    # a first pass can only join

    env.regenerate_user_world(user_world_seed=UW_SEED)

    assert int(env.uav_leaves_count) == 0, (
        "Replacing the user world booked UAV leaves. The rebuild inside "
        "`regenerate_user_world` diffed the new serving sets against the "
        "discarded world's serving sets instead of against an empty baseline."
    )
    assert int(env.uav_joins_count) == int(env.connections.sum()), (
        "Joins must describe the new world alone; a larger count means the "
        "discarded world's joins are still accumulated in."
    )
    assert int(env.handover_count) == 0
    assert int(env.ping_pong_count) == 0


def test_pinning_books_no_uav_leaves_before_the_episode_starts():
    """No UAV may have left a serving set before the episode has stepped.
    Measured at 18 phantom leaves before step 6 was moved after step 8.

    The accumulator is `_update_channel_state`, not `_update_uav_connections`,
    and it diffs against `self.connections` rather than against
    `previous_connections_snapshot`: it hands the serving sets it just computed
    to `_update_soft_handover_stats` together with the ones already in
    `self.connections`, and books the difference as joins and leaves. A pass
    that starts from a zeroed baseline can therefore only record joins.

    This test is a WEAK form of the invariant and is kept only because it
    asserts it on the real `build_pinned_env` path. Whether the post-`reset`
    world puts any user in reach at all depends on the construction-time
    ground-BS layout, which is drawn from an entropy-seeded RNG, so on most
    constructions the baseline is empty and this passes vacuously.
    `test_regenerating_the_user_world_books_no_lifecycle_events` above pins that
    away and is the assertion that actually holds the line.

    Asserted as `leaves == 0` rather than by comparing against the unseeded
    path, because the two paths hold genuinely different user worlds and their
    JOIN counts differ for that legitimate reason. Comparing them would be
    another world-dependent assertion of the kind this file exists to remove."""
    seeded, coords, coord_hash = _pinned(UW_SEED)
    plain, _, _ = _pinned(None, coords=coords, coord_hash=coord_hash)

    assert int(seeded.uav_leaves_count) == 0, (
        "A UAV cannot leave a serving set before the episode has stepped; a "
        "non-zero count means the connection rebuild ran twice."
    )
    assert int(plain.uav_leaves_count) == 0
