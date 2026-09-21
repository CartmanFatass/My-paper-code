import numpy as np
import pytest

from experiments.candidates.vsp_03.opportunity_b08.opportunity import (
    EndpointCounts,
    Planner,
    fit_model,
)


def _row(t, own_present, own_age, partner_present, partner_age, actor_slot,
         partner_pending=1, ready=0):
    x = np.zeros(14, dtype=np.float32)
    x[0] = t / 40
    x[1] = own_present
    x[2] = own_age / 40
    x[5] = ready
    x[6] = partner_present
    x[7] = partner_age / 40
    x[11] = partner_pending
    x[12] = actor_slot
    x[13] = (t + 2 if t < 32 else 40) / 40
    return x


def test_endpoint_counts_follow_physical_identity_and_positive_gaps():
    # Relative slot 0 is own at t0, partner at t2, then own after a blocked gap.
    x = np.stack([
        _row(0, 1, 3, 0, 0, 0),
        _row(2, 1, 0, 1, 5, 1),
        _row(8, 0, 0, 1, 11, 0),
        _row(0, 0, 0, 1, 2, 0),
        _row(4, 1, 1, 1, 6, 0),
    ])
    counts = EndpointCounts().add_batch({
        "x": x,
        "episode_ids": np.array([0, 0, 0, 1, 1]),
        "times": np.array([0, 2, 8, 0, 4]),
    })

    assert counts.transitions == 6
    # Episode 0, relative slot 0: age3 -> age5 -> absent.
    assert counts.counts[2, 4, 6] == 1
    assert counts.counts[6, 6, 0] == 1
    # Episode 0, relative slot 1: absent -> age0 -> age11.
    assert counts.counts[2, 0, 1] == 1
    assert counts.counts[6, 1, 12] == 1
    # Episode 1 supplies the two gap-four transitions.
    assert counts.counts[4, 0, 2] == 1
    assert counts.counts[4, 3, 7] == 1
    serialized = counts.as_dict()
    assert serialized["transitions"] == 6
    assert serialized["shape"] == [41, 42, 42]


def test_endpoint_counts_reject_latent_or_non_public_batch_fields():
    x = np.stack([_row(0, 1, 0, 0, 0, 0)])
    with pytest.raises(ValueError, match="exactly"):
        EndpointCounts().add_batch({
            "x": x, "episode_ids": np.array([0]), "times": np.array([0]),
            "draws": np.zeros(1),
        })


def _reference_transition(c, p):
    matrix = np.zeros((42, 42), dtype=np.float64)
    matrix[0, 0] = 1 - p
    matrix[0, 1] = p
    for age in range(40):
        leave = 1 / (age + c)
        matrix[age + 1, 0] = leave
        matrix[age + 1, age + 2] = 1 - leave
    leave = 1 / (40 + c)
    matrix[41, 0] = leave
    matrix[41, 41] = 1 - leave
    return matrix


def _rounded_multinomial(probabilities, total):
    expected = probabilities * total
    result = np.floor(expected).astype(np.int64)
    remainder = total - int(result.sum())
    if remainder:
        largest = np.argsort(expected - result)[-remainder:]
        result[largest] += 1
    return result


def test_fixed_synthetic_endpoint_data_recovers_parameters():
    true_c, true_p = 4.75, 0.31
    reference = _reference_transition(true_c, true_p)
    counts = EndpointCounts()
    for gap in (1, 2, 5, 9):
        endpoint = np.linalg.matrix_power(reference, gap)
        for source in (0, 1, 4, 11, 21):
            counts.counts[gap, source] = _rounded_multinomial(endpoint[source], 50_000)
    result = fit_model(counts)

    assert result["success"]
    assert isinstance(result["message"], str)
    assert result["metadata"]["success"]
    assert result["c"] == pytest.approx(true_c, abs=0.015)
    assert result["p"] == pytest.approx(true_p, abs=0.001)
    assert result["counts"]["transitions"] == 1_000_000
    assert result["metadata"]["negative_log_likelihood"] < result["metadata"][
        "initial_negative_log_likelihood"
    ]


def test_service_survival_includes_absent_first_step_and_all_eight_ticks():
    c, p = 4.0, 0.25
    planner = Planner(c, p)
    assert planner.survival8[0] == pytest.approx(p * (c - 1) / (c + 6))
    assert planner.survival8[1] == pytest.approx((c - 1) / (c + 7))
    assert planner.survival8[8] == pytest.approx((7 + c - 1) / (7 + c + 7))


def test_late_clock_values_include_waiting_and_failed_attempt_occupancy():
    c, p = 4.0, 0.01
    planner = Planner(c, p)
    absent = 0
    age0 = 1
    own_submit = -10 + 200 * planner.survival8[absent]

    # Independent terminal accounting at t32: both pending jobs wait eight
    # ticks, or own attempts while partner remains pending for eight ticks.
    assert planner.solo_wait[32, absent] == -8
    assert planner.joint_wait[32, absent, age0] == -16
    assert planner.joint_submit[32, absent, age0] == pytest.approx(own_submit - 8)

    # At t22 the occupied slot skips partner clocks 24 and 28.  Its first free
    # clock is 32, after ten state transitions and ten pending-waiting units.
    reference10 = np.linalg.matrix_power(_reference_transition(c, p), 10)
    partner_continuation = -10 + reference10[age0] @ planner.solo[32]
    assert planner.joint_submit[22, absent, age0] == pytest.approx(
        own_submit + partner_continuation
    )
    # The partner delay is identical even when own success is very unlikely:
    # an attempted service occupies the slot through failure.
    assert partner_continuation == pytest.approx(
        planner.joint_submit[22, absent, age0] - own_submit
    )


def test_joint_wait_swaps_actor_and_advances_both_states_independently():
    c, p = 5.0, 0.3
    planner = Planner(c, p)
    reference2 = np.linalg.matrix_power(_reference_transition(c, p), 2)
    own, partner = 3, 7
    independently_enumerated = -4.0
    for own_end, own_probability in enumerate(reference2[own]):
        for partner_end, partner_probability in enumerate(reference2[partner]):
            independently_enumerated += (
                own_probability * partner_probability
                * planner.joint[32, partner_end, own_end]
            )
    assert planner.joint_wait[30, own, partner] == pytest.approx(independently_enumerated)


def test_actions_use_partner_pending_and_do_not_mask_unready_submission():
    planner = Planner(4.0, 0.5)
    row = _row(32, 1, 20, 0, 0, 0, partner_pending=0, ready=0)
    assert planner.actions(row, mode="joint").shape == (1,)
    assert planner.actions(row, mode="joint")[0] == planner.actions(row, mode="self")[0]
    assert planner.actions(row, mode="self")[0]

    both_pending = row.copy()
    both_pending[11] = 1
    joint_margin = planner.action_advantage(both_pending, mode="joint")[0]
    expected = planner.joint_submit[32, 21, 0] - planner.joint_wait[32, 21, 0]
    assert joint_margin == pytest.approx(expected)


def test_ties_favor_submit():
    planner = Planner(4.0, 0.5)
    row = _row(32, 1, 0, 0, 0, 0, partner_pending=0)
    planner.solo_submit[32, 1] = planner.solo_wait[32, 1]
    assert planner.actions(row, mode="self")[0]
