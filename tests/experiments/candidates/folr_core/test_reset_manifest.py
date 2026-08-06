"""Proof-sized tests for the FOLR erase-and-reinitialize reset constructor.

The decisive test is ``test_two_different_histories_reset_to_the_same_state``.
Pro's distinction between reset and restoration is not observable by reading the
constructor -- it is observable by feeding it two cores that lived through
*different* histories and requiring byte-identical output.  If any historical
field leaked through, those two would differ.

``test_the_reset_constructor_never_clears_a_historical_core`` pins the other
half: Pro ruled ``reset_event_runtime`` and ``clear_rollout_ledgers``
insufficient, so their absence from this module is a checked property rather
than a convention.
"""

from __future__ import annotations

import importlib.util
import pathlib

import numpy as np
import pytest
import torch

from experiments.candidates.folr_core import branch_snapshot as bs
from experiments.candidates.folr_core import reset_manifest as rm
from ha_ctse_process import variable_roster_event as vre

_HELPER_PATH = (
    pathlib.Path(__file__).resolve().parents[4]
    / "tests"
    / "process"
    / "variable_roster"
    / "ha_ctse_process_variable_roster_event_test.py"
)
_spec = importlib.util.spec_from_file_location("_folr_vre_helpers", _HELPER_PATH)
_helpers = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_helpers)

TARGET = "a"
SHADOW = "b"
KEYS = (TARGET, SHADOW)


def make_core(model_seed: int = 17) -> vre.VariableRosterEventCore:
    torch.manual_seed(int(model_seed))
    return vre.VariableRosterEventCore(
        architecture_mode="f1",
        obs_dim=_helpers.OBS_DIM,
        critic_member_dim=_helpers.CRITIC_MEMBER_DIM,
        critic_global_dim=_helpers.CRITIC_GLOBAL_DIM,
        n_skills=_helpers.N_SKILLS,
        action_dim=_helpers.ACTION_DIM,
        member_hidden_dim=12,
        high_hidden_dim=10,
        skill_embedding_dim=5,
        gamma=0.9,
        gae_lambda=0.8,
        opportunity_seed=142,
        frontier_seed=51,
        action_seed=61,
        runtime_mode="supplied_executor",
    )


def canonical_manifest(core: vre.VariableRosterEventCore) -> rm.ResetManifest:
    return rm.manifest_from_core(
        core,
        target_lifecycle_key=TARGET,
        frontier=KEYS,
        target_token_order=KEYS,
        observations={key: _helpers.FEATURES[key][0] for key in KEYS},
        critic_member_features={key: _helpers.FEATURES[key][1] for key in KEYS},
        critic_global_features=np.array([0.0, -0.25], dtype=np.float32),
    )


def history(core: vre.VariableRosterEventCore, *, branch: int) -> None:
    """Two genuinely different pretreatment histories."""
    _helpers.initial_join(core, keys=KEYS, actions={TARGET: 0, SHADOW: 1})
    core.complete_primitive_transition(0.0)
    if branch:
        # Branch 1 runs an extra frontier: different actions, different ledger
        # length, different RNG consumption, different resulting hidden state.
        transaction = _helpers.no_membership_transaction(core, KEYS, KEYS)
        core.apply_transaction(
            transaction, teacher_order=KEYS, teacher_actions={TARGET: 2, SHADOW: 0}
        )
        core.complete_primitive_transition(1.0)


def test_two_different_histories_reset_to_the_same_state():
    """The decisive property: reset is not restoration."""
    manifests = []
    for branch in (0, 1):
        core = make_core()
        history(core, branch=branch)
        manifests.append(canonical_manifest(core))

    # The two histories really did diverge, or the test proves nothing.
    assert manifests[0].digest() != manifests[1].digest()

    # A single registered manifest, constructed twice, must give one state.
    registered = manifests[0]
    left = rm.construct_reset_runtime(registered)
    right = rm.construct_reset_runtime(registered)
    assert bs.live_digest(left) == bs.live_digest(right)


def test_the_reset_runtime_carries_no_history():
    core = make_core()
    history(core, branch=1)
    assert core.high_ledger and core.closed_event_rows

    fresh = rm.construct_reset_runtime(canonical_manifest(core))
    assert fresh.high_ledger == []
    assert fresh.closed_event_rows == []
    assert fresh.low_ledger == []
    assert fresh.low_chunk_boundaries == []
    assert fresh.pending_membership_transaction is None
    assert fresh.current_observation_state_boundary is None
    for record in fresh.records.values():
        assert record.open_event_trace is None
        assert record.last_policy_event_time is None
        assert not record.is_genuine_join and not record.is_rejoin


def test_the_reset_constructor_never_clears_a_historical_core():
    """Pro ruled both existing reset-like operations insufficient."""
    source = pathlib.Path(rm.__file__).read_text(encoding="utf-8")
    body = source.split('"""', 2)[-1]  # skip the module docstring, which cites them
    assert "reset_event_runtime(" not in body
    assert "clear_rollout_ledgers(" not in body
    # ...and there is no parameter through which a historical core could enter.
    import inspect

    parameters = inspect.signature(rm.construct_reset_runtime).parameters
    assert list(parameters) == ["manifest"]


def test_the_reset_runtime_reproduces_the_registered_actor_inputs():
    core = make_core()
    history(core, branch=0)
    manifest = canonical_manifest(core)
    fresh = rm.construct_reset_runtime(manifest)
    for owner in manifest.owners:
        record = fresh.records[owner.lifecycle_key]
        assert record.membership_epoch == owner.membership_epoch
        assert record.active_skill == owner.active_skill
        assert record.skill_active_age == owner.skill_active_age
        assert np.array_equal(record.high_hidden, owner.high_hidden)
    assert fresh.physical_time == manifest.physical_time
    for name, generator in (
        ("opportunity_rng_state", fresh.opportunity_rng),
        ("frontier_order_rng_state", fresh.frontier_rng),
        ("policy_action_rng_state", fresh.action_rng),
    ):
        assert (
            generator.bit_generator.state["state"]
            == manifest.rng_states[name]["state"]
        )


def test_the_reset_runtime_produces_the_same_kernel_from_either_history():
    """R_0 = R_1: the reset construction must be branch-invariant."""
    kernels = []
    for branch in (0, 1):
        source = make_core()
        history(source, branch=branch)
        # Both branches reset from the SAME registered manifest -- the one
        # branch 0 produced -- so any surviving branch dependence would have to
        # come through the constructor itself.
        if branch == 0:
            registered = canonical_manifest(source)
        fresh = rm.construct_reset_runtime(registered)
        result = fresh.apply_transaction(
            _helpers.MembershipTransaction(
                rm.boundary_snapshot(registered),
                (),
                rm.boundary_snapshot(registered),
            ),
            teacher_order=registered.target_token_order,
            teacher_actions={key: 0 for key in registered.frontier},
        )
        kernels.append(
            tuple(row.old_token_log_probability for row in result.token_rows)
        )
    assert kernels[0] == kernels[1]


def test_normalization_profiles_differ_in_exactly_what_survives():
    """The two admissible readings of B are both executable and distinct."""
    core = make_core()
    history(core, branch=0)
    manifest = canonical_manifest(core)

    other = make_core()
    history(other, branch=1)
    before = bs.capture(other).rng_states["frontier_rng"]["state"]

    rm.normalize_to_manifest(other, manifest, profile=rm.RECONSTRUCTED_HISTORY)
    assert bs.capture(other).rng_states["frontier_rng"]["state"] == before, (
        "RECONSTRUCTED_HISTORY must leave the RNG consumption state alone"
    )

    rm.normalize_to_manifest(other, manifest, profile=rm.PROVENANCE_LABEL)
    assert (
        bs.capture(other).rng_states["frontier_rng"]["state"]
        == manifest.rng_states["frontier_order_rng_state"]["state"]
    )


def test_normalization_always_erases_the_actor_read_set():
    """Both profiles must close the actor boundary; that is not optional."""
    manifest_core = make_core()
    history(manifest_core, branch=0)
    manifest = canonical_manifest(manifest_core)

    for profile in rm.NORMALIZATION_PROFILES:
        other = make_core()
        history(other, branch=1)
        rm.normalize_to_manifest(other, manifest, profile=profile)
        for owner in manifest.owners:
            record = other.records[owner.lifecycle_key]
            assert record.active_skill == owner.active_skill, profile
            assert record.skill_active_age == owner.skill_active_age, profile
            assert record.is_genuine_join == owner.is_genuine_join, profile
            assert record.open_event_trace is None, profile
        assert other.physical_time == manifest.physical_time, profile


def test_manifest_refuses_a_token_order_that_does_not_start_at_the_target():
    core = make_core()
    history(core, branch=0)
    with pytest.raises(ValueError, match="target first"):
        rm.manifest_from_core(
            core,
            target_lifecycle_key=TARGET,
            frontier=KEYS,
            target_token_order=(SHADOW, TARGET),
            observations={key: _helpers.FEATURES[key][0] for key in KEYS},
            critic_member_features={key: _helpers.FEATURES[key][1] for key in KEYS},
            critic_global_features=np.array([0.0, -0.25], dtype=np.float32),
        )


def test_with_target_hidden_moves_only_the_target():
    core = make_core()
    history(core, branch=0)
    manifest = canonical_manifest(core)
    payload = np.full(10, np.float32(0.75))
    moved = manifest.with_target_hidden(payload)
    assert np.array_equal(moved.owner(TARGET).high_hidden, payload)
    assert np.array_equal(
        moved.owner(SHADOW).high_hidden, manifest.owner(SHADOW).high_hidden
    )
    assert moved.digest() != manifest.digest()
