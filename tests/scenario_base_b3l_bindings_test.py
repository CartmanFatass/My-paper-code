"""D6/D7 bindings from `docs/research/designs/D7_S_B3L_DECISION_LEDGER.md`.

D7: `user_cluster_assignments` is pinned to `dtype=np.int32` at construction
(`scenario_base.py:369`); the writers at `:791`/`:2507` assign scalars into
the already-typed array and are untouched.

D6 / A-D6: three write-only liveness counters --
`user_intra_waypoint_regenerations`, `user_inter_waypoint_regenerations`,
`cluster_target_regenerations` -- incremented unconditionally in the RPGM
redraw branches that actually write a new waypoint/target, including when
reached during construction/reset (the gate subtracts a pre-action baseline
itself; this file does not attempt to separate init from stepping).

Envs are built exactly the way `tests/scenario7_canonical_initialization_test.py`
builds them: through the audit script's own
`build_config`/`build_topology_template`/`build_pinned_env`, never a double.
"""
import re
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
pytest.importorskip("gymnasium")

import audit_d7_s_event_aligned as audit  # noqa: E402

SCENARIO_BASE_PATH = ROOT / "envs" / "pettingzoo" / "scenario_base.py"

# Development topology only, mirroring the canonical-initialization test --
# the ruling forbids touching an R4 seed for anything but a confirmatory run.
TOPOLOGY_SEED = audit.TOPOLOGY_SEED_DEV
EPISODE_SEED = 1001
USER_WORLD_SEED = 3003
ENERGY_STAGE = "S3"


@pytest.fixture
def built_env():
    assert TOPOLOGY_SEED not in set(audit.TOPOLOGY_SEEDS_R4)
    config = audit.build_config()
    coords, coord_hash = audit.build_topology_template(
        config, topology_seed=TOPOLOGY_SEED, energy_stage=ENERGY_STAGE)
    env = audit.build_pinned_env(
        config, episode_seed=EPISODE_SEED, coords=coords, coord_hash=coord_hash,
        energy_stage=ENERGY_STAGE, user_world_seed=USER_WORLD_SEED)
    return env


# ------------------------------------------------------------------- D7 ---

def test_user_cluster_assignments_is_int32_after_construction_reset_and_regeneration(built_env):
    """`build_pinned_env` already carries construction, `reset(seed=...)` and
    (with `user_world_seed` given) `regenerate_user_world` -- all three of the
    paths named in the brief. `regenerate_user_world` calls
    `_generate_user_positions`, whose writer at `:791` assigns scalars into
    the SAME array object (never reallocates it), so the dtype pinned at
    construction must survive every one of these paths."""
    env = built_env
    assert env.user_cluster_assignments.dtype == np.int32
    assert env.user_cluster_assignments.dtype.str == "<i4"

    env.reset(seed=EPISODE_SEED + 1)
    assert env.user_cluster_assignments.dtype == np.int32

    env.regenerate_user_world(user_world_seed=USER_WORLD_SEED + 1)
    assert env.user_cluster_assignments.dtype == np.int32


def test_creation_line_literally_pins_np_int32():
    """Why this reads the source text rather than trusting the dtype value
    alone: on this Windows/NumPy build `np.dtype(int).str == '<i4'` already
    (`int` maps to the platform C `long`, 32-bit under Windows LLP64), so a
    value-only assertion cannot tell the pinned line apart from the pre-pin
    `dtype=int` on THIS platform -- the paired negative (reverting to
    `dtype=int`) would stay green here otherwise. Reading the literal source
    text is the only way that negative can be observed to go red on this box,
    per the brief's own reasoning."""
    text = SCENARIO_BASE_PATH.read_text(encoding="utf-8")
    assert re.search(
        r"user_cluster_assignments\s*=\s*np\.zeros\(self\.n_users,\s*dtype=np\.int32\)",
        text,
    ), "the user_cluster_assignments creation line must literally read dtype=np.int32"


# ------------------------------------------------------------------- D6 ---

def test_liveness_counters_exist_and_are_nonnegative_ints_after_construction(built_env):
    env = built_env
    for name in (
        "user_intra_waypoint_regenerations",
        "user_inter_waypoint_regenerations",
        "cluster_target_regenerations",
    ):
        value = getattr(env, name)
        assert isinstance(value, int), f"{name} must be a plain int, got {type(value)}"
        assert value >= 0, f"{name} must be non-negative, got {value}"


def test_intra_cluster_waypoint_regeneration_increments_only_its_own_counter(built_env):
    """Independent source of truth: the counter must move by exactly +1 per
    call to the function that actually redraws, and the OTHER two counters
    must not move -- a plant of the wrong counter in the wrong branch would
    otherwise pass a same-file-only check."""
    env = built_env
    before = (
        env.user_intra_waypoint_regenerations,
        env.user_inter_waypoint_regenerations,
        env.cluster_target_regenerations,
    )
    env._generate_intra_cluster_waypoint(0, int(env.user_cluster_assignments[0]))
    assert env.user_intra_waypoint_regenerations == before[0] + 1
    assert env.user_inter_waypoint_regenerations == before[1]
    assert env.cluster_target_regenerations == before[2]


def test_inter_cluster_waypoint_regeneration_increments_only_its_own_counter(built_env):
    env = built_env
    # The `else` fallback of `_generate_inter_cluster_waypoint` (scenario_base.py:2509-2510)
    # redraws intra-cluster instead when there is no OTHER cluster to move to; n_clusters
    # must exceed 1 here so this call exercises the true inter branch (the `:2507` writer).
    assert env.n_clusters > 1
    before = (
        env.user_intra_waypoint_regenerations,
        env.user_inter_waypoint_regenerations,
        env.cluster_target_regenerations,
    )
    env._generate_inter_cluster_waypoint(0)
    assert env.user_inter_waypoint_regenerations == before[1] + 1
    assert env.user_intra_waypoint_regenerations == before[0]
    assert env.cluster_target_regenerations == before[2]


def test_cluster_target_regeneration_increments_only_its_own_counter(built_env):
    env = built_env
    before = (
        env.user_intra_waypoint_regenerations,
        env.user_inter_waypoint_regenerations,
        env.cluster_target_regenerations,
    )
    env._generate_new_cluster_target_rpgm(0)
    assert env.cluster_target_regenerations == before[2] + 1
    assert env.user_intra_waypoint_regenerations == before[0]
    assert env.user_inter_waypoint_regenerations == before[1]


def test_construction_reaches_the_regeneration_branches_and_the_gate_can_read_a_delta(built_env):
    """`build_pinned_env` runs `reset()` (and, with `user_world_seed`,
    `regenerate_user_world`), both of which call `_initialize_user_waypoints_rpgm`
    for every user when `user_movement_model == "rpgm"`. This is the
    'reached during construction/initialization' case the brief names: the
    counter must count it exactly like a stepping-time regeneration, so the
    contract's `postinitialization_regen_delta` baseline (recorded by the
    GATE, not here) has something nonzero to subtract from. This test does
    not assume rpgm is configured -- it forces the branch directly and checks
    the gate-relevant property: a delta is observable across a call."""
    env = built_env
    baseline = env.user_intra_waypoint_regenerations + env.user_inter_waypoint_regenerations
    env._initialize_user_waypoints_rpgm()
    after = env.user_intra_waypoint_regenerations + env.user_inter_waypoint_regenerations
    assert after > baseline, (
        "the gate requires postinitialization_regen_delta > 0; "
        "_initialize_user_waypoints_rpgm must move at least one of the two counters"
    )
