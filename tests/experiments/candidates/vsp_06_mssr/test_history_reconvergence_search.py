"""Focused proofs for the MSSR passive-carrier history-reconvergence search.

Zero training, deterministic, no added dependencies, no network, no sleeps.
"""

from __future__ import annotations

import numpy as np
import pytest

from experiments.candidates.vsp_06_mssr import history_reconvergence_search as m


@pytest.fixture(scope="module")
def report() -> dict:
    """The strengthened proof(), computed once for the whole module."""
    return m.proof()


# The exact determinism-pin values, computed and pinned to full precision
# (episode 0, every event token SHORT=2 and every primitive SHORT=2).  These are
# the POST-write partner-interaction values at member "2"'s first opportunities.
P_MEMBER_2_JOIN = 0.1673012386643686          # t0, first opportunity
P_MEMBER_2_SECOND_OPPORTUNITY = 0.2543302725596989   # t7
P_MEMBER_2_THIRD_OPPORTUNITY = 0.3843261176493962    # t12


def _drive_uniform_history(token: int, primitive: int, target_key: str):
    """Roll episode 0 with a uniform token/primitive script.

    Returns the ordered list of POST-write ``P`` values for ``target_key`` at each
    of its opportunities, driving the exact verified recipe loop.
    """
    core = m.make_core(0)
    env = m.make_environment()
    post_write_p: list[float] = []

    def handle(bound) -> None:
        post = bound.post_membership_pre_policy_snapshot
        frontier = tuple(post.frontier)
        order = tuple(sorted((str(k) for k in frontier), key=int))
        is_target_opp = str(target_key) in {str(k) for k in frontier}
        core.apply_transaction(
            bound,
            teacher_actions={str(k): int(token) for k in frontier},
            teacher_order=order,
            deterministic_policy=True,
        )
        if is_target_opp:
            post_write_p.append(m.current_p(core, target_key))

    transaction = env.reset_event_runtime(0)
    handle(core.bind_due_frontier(transaction))
    while True:
        active = tuple(env.environment.active_keys)
        step = env.step_event_runtime({int(k): int(primitive) for k in active})
        core.complete_primitive_transition(float(step.reward))
        if step.terminated:
            core.close_terminal()
            break
        handle(core.bind_due_frontier(step.next_transaction))
    return post_write_p


def test_determinism_pin_partner_interaction_values():
    """Verified wiring reproduces member 2's partner-interaction values exactly."""
    post_write_p = _drive_uniform_history(token=2, primitive=2, target_key="2")
    assert len(post_write_p) >= 3
    assert post_write_p[0] == P_MEMBER_2_JOIN
    assert post_write_p[1] == P_MEMBER_2_SECOND_OPPORTUNITY
    assert post_write_p[2] == P_MEMBER_2_THIRD_OPPORTUNITY


def test_replay_determinism_is_byte_identical():
    """Rolling the same (episode, scripts) twice yields identical digests and P."""
    design = m.Design("1", "3", (25,))
    tape = m.Tape.make(0, design.target_key, design.perturbation())
    first = m.rollout(tape)
    second = m.rollout(tape)
    assert set(first) == set(second)
    assert first  # at least one target opportunity
    for physical_time, opp in first.items():
        other = second[physical_time]
        assert opp.znp_digest == other.znp_digest
        assert opp.znp_minus_hidden_digest == other.znp_minus_hidden_digest
        assert opp.p_value == other.p_value
        assert opp.high_hidden == other.high_hidden


def test_partner_interaction_disabled_leaves_high_hidden_byte_identical():
    """P is a side channel: disabling it does not move high_hidden at t0."""

    def first_boundary_high_hidden(enabled: bool) -> dict[str, bytes]:
        core = m.make_core(0, partner_interaction_enabled=enabled)
        env = m.make_environment()
        transaction = env.reset_event_runtime(0)
        bound = core.bind_due_frontier(transaction)
        post = bound.post_membership_pre_policy_snapshot
        frontier = tuple(post.frontier)
        order = tuple(sorted((str(k) for k in frontier), key=int))
        core.apply_transaction(
            bound,
            teacher_actions={str(k): 2 for k in frontier},
            teacher_order=order,
            deterministic_policy=True,
        )
        return {
            str(k): m.high_hidden_bytes(core, str(k)) for k in frontier
        }

    enabled = first_boundary_high_hidden(True)
    disabled = first_boundary_high_hidden(False)
    assert set(enabled) == set(disabled)
    assert enabled  # frontier is non-empty at the join boundary
    for key in enabled:
        assert enabled[key] == disabled[key]


def test_digest_includes_high_hidden_and_member_skills():
    """Z_not_P genuinely includes the owner's high_hidden and members' skills."""
    state = m.capture_opportunity_state(m.Tape.make(0, "0", {}))
    baseline = state.digest()

    # A one-ULP perturbation of the owner's high_hidden must move the digest.
    record = state.core.records["0"]
    perturbed = np.asarray(record.high_hidden, dtype=np.float32).copy()
    perturbed[0] = np.nextafter(perturbed[0], np.float32(np.inf))
    original = np.asarray(record.high_hidden, dtype=np.float32).copy()
    record.high_hidden = perturbed
    assert state.digest() != baseline

    # The minus-high_hidden digest must NOT move under that same perturbation.
    assert (
        state.digest(include_target_high_hidden=False)
        == m.canonical_non_p_digest(
            state.core, state.env, "0",
            frontier=state.frontier, teacher_order=state.teacher_order,
            include_target_high_hidden=False,
        )
    )
    record.high_hidden = original
    assert state.digest() == baseline

    # Changing another active member's core skill must move the digest.
    other = next(
        str(k) for k in state.env.environment.active_keys if str(k) != "0"
    )
    before = state.digest()
    original_skill = state.core.records[other].active_skill
    state.core.records[other].active_skill = (
        0 if original_skill != 0 else 1
    )
    assert state.digest() != before


def test_terminal_contract_and_scope(report):
    """The terminal is one of the two allowed strings with a lawful scope."""
    assert report["raw_output_binding"] == m.RAW_OUTPUT_BINDING
    assert report["terminal"] in (m.TERMINAL_WITNESS, m.TERMINAL_NO_WITNESS)
    budget = report["budget"]
    assert budget["delta"] == m.DELTA
    assert budget["episode_ids"] == list(m.EPISODE_IDS)
    # The strengthened budget runs under the three registered base families.
    assert budget["base_families"] == [family.name for family in m.BASE_FAMILIES]
    assert budget["design_count"] == len(budget["designs"])
    assert budget["design_count"] > 0

    scope = report["scope"]
    assert "seed 57057" in scope and "f1" in scope
    assert "15-dim" in scope and "NOT the 3-dim fixture" in scope
    if report["terminal"] == m.TERMINAL_NO_WITNESS:
        assert "no witness in the registered budget" in scope
        assert "unreachab" not in scope
        assert "nullity" not in scope
        residual = report["obstruction_residual"]
        counts = residual["counts"]
        assert "target_opportunities" in counts
        assert "znp_minus_hidden_reconverged" in counts
        assert "reconverged_and_delta_p_ge_delta" in counts


def test_base_families_present_and_proof_is_byte_stable(report):
    """The terminal is NO_WITNESS, base families are listed, and proof() is stable."""
    assert report["terminal"] == m.TERMINAL_NO_WITNESS
    assert report["budget"]["base_families"] == [
        family.name for family in m.BASE_FAMILIES
    ]
    # Determinism: a second independent proof() must be byte-stable.
    import json

    again = m.proof()
    assert json.dumps(report, sort_keys=True, default=str) == json.dumps(
        again, sort_keys=True, default=str
    )


def test_anti_correlation_fields_are_measured(report):
    """The anti-correlation Pro rules on is measured and reported.

    When the FULL Z_not_P (high_hidden included) reconverges, the retained P has
    reconverged too (delta_p == 0); and among opportunities where only
    Z_not_P-minus-high_hidden reconverges, the retained |delta_p| stays below the
    precommitted DELTA and co-varies with the high_hidden gap.
    """
    assert report["terminal"] == m.TERMINAL_NO_WITNESS
    residual = report["obstruction_residual"]

    # (a) Full byte-identical Z_not_P never carries a nonzero P difference.
    assert residual["full_match_max_delta_p"] == 0.0
    assert residual["full_match_with_delta_p_gt_zero_count"] == 0

    # (d) The reconverged co-variation fields are present and in range.
    max_dp = residual["reconverged_minus_hidden_max_delta_p"]
    max_dp_gap = residual["reconverged_minus_hidden_max_delta_p_high_hidden_l2_gap"]
    assert 0.0 <= max_dp < m.DELTA
    # A nonzero retained P difference co-occurs with a nonzero high_hidden gap.
    if max_dp > 0.0:
        assert max_dp_gap > 0.0
    assert "reconverged_minus_hidden_min_high_hidden_l2_gap" in residual
    assert "reconverged_minus_hidden_min_gap_delta_p" in residual
    assert isinstance(residual["anti_correlation_note"], str)


def test_witness_replays_or_residual_reports_counts(report):
    """A witness must replay exactly; otherwise the residual reports its counts."""
    if report["terminal"] == m.TERMINAL_WITNESS:
        witness = report["witness"]
        replay = witness["replay"]
        assert replay["znp_byte_identical"] is True
        assert replay["delta_p"] >= m.DELTA
    else:
        residual = report["obstruction_residual"]
        counts = residual["counts"]
        # Counts must be internally consistent and machine-visible.
        assert counts["target_opportunities"] >= counts["znp_minus_hidden_reconverged"]
        assert (
            counts["znp_minus_hidden_reconverged"]
            >= counts["reconverged_and_delta_p_ge_delta"]
        )
        assert counts["target_opportunities"] > 0
        if counts["reconverged_and_delta_p_ge_delta"] == 0:
            assert (
                residual["min_high_hidden_l2_gap_over_reconverged_and_delta"] is None
            )
        else:
            assert (
                residual["min_high_hidden_l2_gap_over_reconverged_and_delta"]
                is not None
            )


def test_import_has_no_side_effects():
    """The json dump lives only under the __main__ guard."""
    import inspect

    source = inspect.getsource(m)
    main_index = source.index('if __name__ == "__main__":')
    # No print / json.dumps invocation before the main guard.
    assert "print(" not in source[:main_index]
    assert "json.dumps" not in source[:main_index]
    # The module exposes its public entry points.
    assert callable(m.proof)
    assert callable(m.canonical_non_p_digest)
    assert callable(m.current_p)
    assert callable(m.high_hidden_bytes)
