"""Proof-sized tests for the FOLR common-snapshot branch cloner.

Two tests carry the component.

``test_the_partition_covers_every_core_attribute`` is the closure guard: a
runtime field that belongs to none of the four declared sets breaks it, instead
of silently escaping the clone and making the fixed-payload nulls pass because
the branches shared something nobody listed.

``test_restore_reproduces_the_run_bit_for_bit`` is the behavioural proof.  Field
equality is not the claim -- the claim is that a restored core *executes* the
same way, including its RNG draws.
"""

from __future__ import annotations

import importlib.util
import pathlib

import numpy as np
import pytest
import torch

from experiments.candidates.folr_core import branch_snapshot as bs
from ha_ctse_process.variable_roster_event import VariableRosterEventCore

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

initial_join = _helpers.initial_join
no_membership_transaction = _helpers.no_membership_transaction


def make_core(
    mode: str = "f1",
    *,
    model_seed: int = 17,
    partner_interaction_enabled: bool = False,
) -> VariableRosterEventCore:
    """A supplied-executor core, which is the FOLR instantiation.

    Pro chose this runtime for the experiment -- "the cleanest instantiation is
    SUPPLIED_EXECUTOR_RUNTIME, because it removes the learned low path" -- and
    it also lets `complete_primitive_transition` tick the opportunity clock
    without a low-step, which is what makes a second frontier reachable here.
    """
    torch.manual_seed(int(model_seed))
    return VariableRosterEventCore(
        architecture_mode=mode,
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
        partner_interaction_enabled=partner_interaction_enabled,
    )


def tick(core: VariableRosterEventCore, steps: int = 1) -> None:
    """Advance physical time so the opportunity gaps expire."""
    for _ in range(steps):
        core.complete_primitive_transition(0.0)


def test_the_partition_covers_every_core_attribute():
    """The closure guard. A missed mutable field fabricates the nulls."""
    core = make_core()
    declared = (
        set(bs.ARCHITECTURE_FIELDS)
        | set(bs.MODEL_FIELDS)
        | set(bs.MUTABLE_STATE_FIELDS)
        | set(bs.RNG_FIELDS)
    )
    actual = set(vars(core))
    # Hook fields are optional: they exist only once installed.
    unclassified = actual - declared - set(bs.HOOK_FIELDS)
    assert not unclassified, (
        f"unclassified runtime state {sorted(unclassified)} would escape the "
        "clone; add it to MUTABLE_STATE_FIELDS or justify it in ARCHITECTURE"
    )
    missing = declared - actual
    assert not missing, f"declared fields absent from the runtime: {sorted(missing)}"


def test_the_four_sets_are_disjoint():
    sets = (
        set(bs.ARCHITECTURE_FIELDS),
        set(bs.MODEL_FIELDS),
        set(bs.MUTABLE_STATE_FIELDS),
        set(bs.RNG_FIELDS),
        set(bs.HOOK_FIELDS),
    )
    for index, left in enumerate(sets):
        for right in sets[index + 1 :]:
            assert not (left & right)


def test_restore_reproduces_the_run_bit_for_bit():
    """The behavioural claim: a restored core executes identically."""
    core = make_core()
    initial_join(core, keys=("a", "b"))
    tick(core)  # expire the opportunity gaps so a second frontier is due
    snapshot = bs.capture(core)

    def advance() -> tuple[tuple[str, ...], list[int], list[float]]:
        transaction = no_membership_transaction(core, ("a", "b"), ("a", "b"))
        result = core.apply_transaction(transaction)
        return (
            result.sampled_order,
            [row.sampled_replacement_gap for row in result.token_rows],
            [row.old_token_log_probability for row in result.token_rows],
        )

    first = advance()
    bs.restore(core, snapshot)
    second = advance()

    assert first[0] == second[0], "frontier RNG was not restored"
    assert first[1] == second[1], "opportunity RNG was not restored"
    assert first[2] == second[2], "the model or records were not restored"


def test_restore_returns_the_digest_to_its_earlier_value():
    core = make_core()
    initial_join(core, keys=("a", "b"))
    tick(core)
    snapshot = bs.capture(core)
    before = snapshot.digest()

    core.apply_transaction(no_membership_transaction(core, ("a", "b"), ("a", "b")))
    assert bs.live_digest(core) != before, "the digest must notice a real change"

    bs.restore(core, snapshot)
    assert bs.live_digest(core) == before


def test_two_cores_restored_from_one_snapshot_are_indistinguishable():
    """This is what the branches actually rely on."""
    source = make_core()
    initial_join(source, keys=("a", "b"))
    snapshot = bs.capture(source)

    left, right = make_core(model_seed=1), make_core(model_seed=2)
    assert bs.live_digest(left) != bs.live_digest(right)
    bs.restore(left, snapshot)
    bs.restore(right, snapshot)
    assert bs.live_digest(left) == bs.live_digest(right) == snapshot.digest()


def test_the_digest_notices_a_single_hidden_coordinate():
    """S03 is one float32 vector; the digest must be sensitive at that scale."""
    core = make_core()
    initial_join(core, keys=("a", "b"))
    before = bs.live_digest(core)
    hidden = core.records["a"].high_hidden.copy()
    hidden[0] = np.float32(hidden[0] + np.float32(1e-3))
    core.records["a"].high_hidden = hidden
    assert bs.live_digest(core) != before


def test_restore_refuses_an_architecture_mismatch():
    source = make_core(partner_interaction_enabled=True)
    snapshot = bs.capture(source)
    other = make_core(partner_interaction_enabled=False)
    with pytest.raises(ValueError, match="partner_interaction_enabled"):
        bs.restore(other, snapshot)


def test_the_encoder_refuses_what_it_cannot_canonicalize():
    """A repr() fallback would embed an address and break reproducibility."""

    class Opaque:
        pass

    with pytest.raises(bs.UnencodableState):
        bs.digest_of({"x": Opaque()})


def test_the_digest_is_stable_across_independent_constructions():
    """Same state built twice must digest the same, or nothing else holds."""
    left, right = make_core(), make_core()
    initial_join(left, keys=("a", "b"))
    initial_join(right, keys=("a", "b"))
    assert bs.live_digest(left) == bs.live_digest(right)


def test_the_snapshot_does_not_carry_the_capture_sink():
    """Cloning a sink would carry one branch's captures into the next."""
    core = make_core()
    core.install_kernel_capture(object())
    snapshot = bs.capture(core)
    assert "_kernel_capture" not in snapshot.mutable_state
    assert "_kernel_capture" not in snapshot.architecture


def test_records_round_trip_through_the_runtimes_own_serializer():
    """Drift between the clone and the runtime's own round-trip is the risk."""
    core = make_core()
    initial_join(core, keys=("a", "b"))
    snapshot = bs.capture(core)
    for key, state in snapshot.mutable_state["records"].items():
        rebuilt = VariableRosterEventCore._record_from_state(state)
        original = core.records[key]
        assert rebuilt.lifecycle_key == original.lifecycle_key
        assert rebuilt.membership_epoch == original.membership_epoch
        assert np.array_equal(rebuilt.high_hidden, original.high_hidden)
        assert rebuilt.open_event_trace == original.open_event_trace
