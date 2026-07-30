"""The canonical post-pin initialization barrier, measured on the real env.

Ordered by the ruling of 2026-07-30 (`20260730_d7_s_manifest_replay_gate_result`,
§1.2): once topology, manifest world and initial energy are final, every derived
state that may enter an action, transition, observation, event certification,
reward component or continuation fingerprint is recomputed from those final
inputs -- and the six observed stale fields must NOT be repaired individually.

Every test here builds real `UAVEnergyAwareRelayEnv` instances through the audit
script's own `build_topology_template` / `build_pinned_env`, the same call
pattern `scripts/d7_s_manifest_replay_probe.py` uses. No doubles: the defect is a
property of that construction order, so a stand-in would test nothing.

The topology template is built once per module, but the env PAIR is rebuilt per
test on purpose: the barrier mutates the envs, and a shared pair would let one
test's repair satisfy the next test's premise.
"""
import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
pytest.importorskip("gymnasium")

import audit_d7_s_event_aligned as audit  # noqa: E402
from envs.pettingzoo.scenario7_energy_aware import (  # noqa: E402
    PostPinRandomnessError,
    UAVEnergyAwareRelayEnv,
)

# Development topology only. `d7_s_manifest_replay_probe.refuse_confirmatory_topology`
# forbids touching an R4 seed, and constructing one here would inspect a
# confirmatory world exactly as the ruling forbids.
TOPOLOGY_SEED = audit.TOPOLOGY_SEED_DEV
EPISODE_SEED = 1001
ENERGY_SEED = 2002
USER_WORLD_SEED = 3003
ENERGY_STAGE = "S3"


@pytest.fixture(scope="module")
def topology():
    """The recorded topology template. Read-only, so one build serves the file."""
    assert TOPOLOGY_SEED not in set(audit.TOPOLOGY_SEEDS_R4)
    config = audit.build_config()
    coords, coord_hash = audit.build_topology_template(
        config, topology_seed=TOPOLOGY_SEED, energy_stage=ENERGY_STAGE)
    return config, coords, coord_hash


@pytest.fixture
def pinned_pair(topology):
    """Two independently constructed pinned envs with IDENTICAL registered seeds.

    This is the exact construction `d7_s_manifest_replay_probe.replay_one_episode`
    performs, minus the manifest: `build_topology_template` once, then
    `build_pinned_env` twice against the same recorded coordinates.
    """
    config, coords, coord_hash = topology
    envs = [
        audit.build_pinned_env(
            config, episode_seed=EPISODE_SEED, coords=coords, coord_hash=coord_hash,
            energy_stage=ENERGY_STAGE, user_world_seed=USER_WORLD_SEED)
        for _ in range(2)
    ]
    return envs, coord_hash


def _world_digest(env):
    """A digest over the nine registered world arrays, in the registered order."""
    parts = []
    for name in audit.WORLD_COMPONENT_ORDER:
        arr = np.ascontiguousarray(np.asarray(getattr(env, name)))
        parts.append(name.encode("utf-8"))
        parts.append(str(arr.dtype).encode("utf-8"))
        parts.append(str(arr.shape).encode("utf-8"))
        parts.append(arr.tobytes())
    return hashlib.sha256(b"".join(parts)).hexdigest()


def _coordinate_hash(env):
    return audit.coordinate_hash(env.ground_bs_positions, env.charging_station_positions)


def _apply_registered_energy(envs):
    energies = audit.draw_energy_permutation(energy_seed=ENERGY_SEED)
    for env in envs:
        audit.apply_energy_profile(env, energies)
    return energies


# --------------------------------------------------------------------- (a) --

def test_a_two_pinned_constructions_disagree_before_the_barrier(pinned_pair):
    """The paired negative for test (b), and the reason the barrier exists.

    Two `build_pinned_env` calls with identical registered seeds agree on all
    nine world arrays and on the topology coordinates, and still disagree on
    `full_state_fingerprint` -- because `reset()` derives station distances, the
    graph potential and the cached `state` BEFORE `build_pinned_env` restores the
    registered coordinates over the construction-time ones drawn from unseeded OS
    entropy.

    If this ever goes red because the two fingerprints AGREE on construction,
    test (b) has become vacuous: it would then be passing on a fixture that never
    carried the defect, not on anything the barrier does. That is what this test
    is here to catch, so it asserts the disagreement rather than the repair.
    """
    envs, _ = pinned_pair

    # The premise: the inputs the barrier treats as final are already equal, so
    # any fingerprint difference is a stale DERIVED value and nothing else.
    assert _world_digest(envs[0]) == _world_digest(envs[1])
    assert _coordinate_hash(envs[0]) == _coordinate_hash(envs[1])
    assert np.array_equal(envs[0].uav_positions, envs[1].uav_positions)

    assert audit.full_state_fingerprint(envs[0]) != audit.full_state_fingerprint(envs[1])


# --------------------------------------------------------------------- (b) --

def test_b_barrier_makes_the_two_constructions_identical(pinned_pair):
    """THE load-bearing test: after the registered energy profile and the
    barrier, the complete pre-step environment identity matches exactly.

    §5.2 of the ruling records at least two stale initialization families --
    station/return-energy state, and the topology/radio-derived graph potential
    plus public `state`. A barrier that closed only the first would leave
    `current_graph_potential` differing here, and this assertion would fail.
    """
    envs, _ = pinned_pair
    _apply_registered_energy(envs)

    # Still stale at this point: the energy profile converges the two return
    # arrays (measured, and recorded in the evidence note) but nothing else.
    assert audit.full_state_fingerprint(envs[0]) != audit.full_state_fingerprint(envs[1])

    for env in envs:
        env.canonicalize_post_pin_initialization()

    assert audit.full_state_fingerprint(envs[0]) == audit.full_state_fingerprint(envs[1])


def test_b2_barrier_overwrites_every_field_the_ruling_names(pinned_pair):
    """Per-field, deterministic: plant a violation and require the barrier to be
    what removes it.

    Why this shape rather than "assert these fields differ on construction".
    MEASURED over 12 construction pairs in one process: `state` differed in
    12/12, the two station-distance caches in 10/12, and
    `current_graph_potential` in 6/12 -- the pre-barrier divergence set depends
    on the unseeded construction entropy, so a test asserting a fixed set is a
    coin flip. The barrier converged all 12/12.

    So the property is tested directly instead. `envs[1]` is canonicalized and
    untouched; it is the independent source of truth. `envs[0]` gets a violation
    planted in each field §1.2 and §5.2 name, and the barrier must restore
    agreement. A barrier that skips ANY of these fields leaves the planted value
    in the fingerprint and this goes red -- which is exactly what a station-only
    repair would do to `current_graph_potential`.
    """
    envs, _ = pinned_pair
    _apply_registered_energy(envs)
    for env in envs:
        env.canonicalize_post_pin_initialization()
    assert audit.full_state_fingerprint(envs[0]) == audit.full_state_fingerprint(envs[1])

    victim = envs[0]
    # The six fields the ruling and the evidence note name, planted one at a
    # time so a failure names the surviving carrier rather than the set.
    plants = {
        "last_min_station_distance_before": lambda v: v + 137.0,
        "last_min_station_distance_after": lambda v: v + 137.0,
        "uav_return_threshold_ratios": lambda v: v + 0.25,
        "uav_return_energy_margins": lambda v: v + 0.25,
        "current_graph_potential": lambda v: float(v) + 0.5,
        "state": lambda v: v + 1.0,
    }
    for name, perturb in plants.items():
        original = getattr(victim, name)
        setattr(victim, name, perturb(original))
        assert audit.full_state_fingerprint(victim) != audit.full_state_fingerprint(envs[1]), (
            f"planting into {name} did not move the fingerprint, so this field is "
            f"not covered by the identity the gate compares")
        victim.canonicalize_post_pin_initialization()
        assert audit.full_state_fingerprint(victim) == audit.full_state_fingerprint(envs[1]), (
            f"the barrier did not recompute {name} from the final inputs")


# --------------------------------------------------------------------- (c) --

def test_c_barrier_consumes_no_randomness(pinned_pair):
    """Measured with the audit's own RNG-state reader, not the env's.

    `_rng_state_token` reads the bit-generator state directly, so this cannot be
    satisfied by the barrier's internal check agreeing with itself.
    """
    envs, _ = pinned_pair
    env = envs[0]
    before = audit._rng_state_token(env)
    report = env.canonicalize_post_pin_initialization()
    after = audit._rng_state_token(env)

    assert after == before
    assert report["rng_state_unchanged"] is True


def test_c2_the_no_randomness_guard_can_go_red():
    """The paired negative for (c): plant an initialization step that draws.

    Without this, `rng_state_unchanged: True` could be a constant that never
    reads the RNG, and (c) would read as coverage forever. This subclass makes
    one barrier step consume randomness and requires the barrier to RAISE.
    """
    class DrawingEnv(UAVEnergyAwareRelayEnv):
        drawing = False

        def _reset_derived_energy_state(self):
            super()._reset_derived_energy_state()
            if self.drawing:
                self.np_random.uniform(0.0, 1.0)

    config = audit.build_config()
    env = DrawingEnv(config=config, energy_stage=ENERGY_STAGE)
    env.reset(seed=EPISODE_SEED)          # constructed with the draw disabled

    env.drawing = True
    with pytest.raises(PostPinRandomnessError):
        env.canonicalize_post_pin_initialization()

    env.drawing = False
    report = env.canonicalize_post_pin_initialization()
    assert report["rng_state_unchanged"] is True


# --------------------------------------------------------------------- (d) --

def test_d_barrier_is_idempotent(pinned_pair):
    envs, _ = pinned_pair
    env = envs[0]
    env.canonicalize_post_pin_initialization()
    once = audit.full_state_fingerprint(env)
    env.canonicalize_post_pin_initialization()
    env.canonicalize_post_pin_initialization()
    assert audit.full_state_fingerprint(env) == once


# --------------------------------------------------------------------- (e) --

def test_e_barrier_leaves_registered_inputs_untouched(pinned_pair):
    """The nine world arrays, the topology coordinate hash, the UAV positions,
    the registered energy profile and the episode seed are inputs, not derived
    state. The barrier must not move any of them."""
    envs, coord_hash = pinned_pair
    env = envs[0]
    energies = _apply_registered_energy([env])

    world_before = _world_digest(env)
    coords_before = _coordinate_hash(env)
    uav_before = env.uav_positions.copy()
    seed_before = env.seed_val
    pinned_before = env.pinned_coordinate_hash

    env.canonicalize_post_pin_initialization()

    assert _world_digest(env) == world_before
    assert _coordinate_hash(env) == coords_before == coord_hash
    assert np.array_equal(env.uav_positions, uav_before)
    assert np.array_equal(env.uav_battery_ratios, energies)
    assert env.seed_val == seed_before
    assert env.pinned_coordinate_hash == pinned_before


# ------------------------------------------------------- single code path --

def test_reset_runs_the_barrier_exactly_once():
    """The anti-drift guard for the recompute set.

    The barrier is not allowed to be a private re-implementation of `reset`'s
    tail: `reset` must reach its derived-state initialization THROUGH the
    barrier, so a step added later cannot be present in one and missing from the
    other. If someone re-inlines reset's tail, this goes red.
    """
    calls = []

    class CountingEnv(UAVEnergyAwareRelayEnv):
        def canonicalize_post_pin_initialization(self):
            calls.append(1)
            return super().canonicalize_post_pin_initialization()

    config = audit.build_config()
    env = CountingEnv(config=config, energy_stage=ENERGY_STAGE)
    env.reset(seed=EPISODE_SEED)
    assert len(calls) == 1

    # And the derived-energy recompute is inside the set the barrier runs, so a
    # replay reaches it. Named, not hand-listed: read off the step tuple itself.
    names = [name for name, _ in env._post_pin_initialization_steps()]
    assert names == list(env.canonicalize_post_pin_initialization()["recomputed"])
    assert "derived_energy_state" in names and "public_views" in names
