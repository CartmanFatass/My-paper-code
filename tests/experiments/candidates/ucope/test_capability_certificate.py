"""Proof-sized tests for the UCOPE capability certificate.

The certificate is the gate the external ruling requires before any training
run, so these tests check the gate itself is sound -- not merely that it
returns a cheerful answer.  Every quantity is exact.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from experiments.candidates.ucope import capability_certificate as cc


def test_reward_is_the_base_environment_tent():
    # Peak at the realized load, zero at both ends of the support.
    assert cc.reward(Fraction(3, 4), Fraction(3, 4)) == 1
    assert cc.reward(Fraction(0), Fraction(3, 4)) == 0
    assert cc.reward(Fraction(3, 2), Fraction(3, 4)) == 0
    # Halfway out, exactly.
    assert cc.reward(Fraction(1, 4), Fraction(3, 4)) == Fraction(1, 3)


def test_posterior_is_exact_bayes():
    # No evidence -> the prior.
    assert cc.posterior_s(0, 0) == cc.PRIOR_S
    # One negative bit: P(neg|S)=1/4, P(neg|L)=3/4 -> (1/2)(1/4) / ((1/2)(1/4)+(1/2)(3/4))
    assert cc.posterior_s(0, 1) == Fraction(1, 4)
    # One positive bit is the mirror image.
    assert cc.posterior_s(1, 1) == Fraction(3, 4)


def test_evidence_is_informative_or_the_gate_is_meaningless():
    assert cc.EVIDENCE_POSITIVE[cc.S] != cc.EVIDENCE_POSITIVE[cc.L]


def test_switching_threshold_is_where_the_algebra_says():
    # f(1/4) = (2*rho + 1)/3 and f(3/4) = 1 - rho, equal at rho = 2/5.
    threshold = Fraction(2, 5)
    assert cc.expected_reward(Fraction(1, 4), threshold) == cc.expected_reward(
        Fraction(3, 4), threshold
    )
    # Strictly either side the argmax differs.
    assert cc.optimal_effort(threshold + Fraction(1, 100)) == Fraction(1, 4)
    assert cc.optimal_effort(threshold - Fraction(1, 100)) == Fraction(3, 4)


def test_action_switch_exists_with_reachable_witnesses():
    switches, witnesses = cc.action_switches()
    assert switches
    assert len(witnesses) >= 2
    actions = {
        cc.optimal_effort(cc.posterior_s(positive, trials))
        for positive, trials in witnesses
    }
    assert len(actions) >= 2, "witnesses must induce genuinely different actions"
    for positive, trials in witnesses:
        assert 0 <= positive <= trials < cc.PERIODS, "witness must be reachable"


def test_blind_value_is_the_hand_computed_two():
    # Blind always acts on the prior -> effort 1/4.
    # Per period: 1/2 * reward(1/4, 1/4) + 1/2 * reward(1/4, 3/4) = 1/2 + 1/6 = 2/3.
    value = cc.valuations()
    assert value.blind == Fraction(2, 3) * cc.PERIODS == Fraction(2)


def test_count_information_strictly_helps():
    value = cc.valuations()
    assert value.informed > value.blind
    assert value.informed - value.blind == Fraction(9, 32)


def test_severing_the_count_exactly_removes_the_gain():
    """The decisive control: the advantage must be the information, not the wiring."""
    value = cc.valuations()
    assert value.severed == value.blind
    assert value.severed - value.blind == 0


def test_certificate_terminal_is_present():
    report = cc.certificate()
    assert report["action_switch_exists"] is True
    assert Fraction(report["informed_minus_blind"]) > 0
    assert Fraction(report["severed_minus_blind"]) == 0
    assert report["terminal"] == "UCOPE_CAPABILITY_PRESENT"


def test_certificate_would_fail_if_evidence_were_uninformative(monkeypatch):
    """Negative control: identical likelihoods must NOT certify the mechanism."""
    monkeypatch.setattr(
        cc, "EVIDENCE_POSITIVE", {cc.S: Fraction(1, 2), cc.L: Fraction(1, 2)}
    )
    switches, _ = cc.action_switches()
    value = cc.valuations()
    assert not switches, "uninformative evidence cannot switch the optimal action"
    assert value.informed == value.blind
    assert cc.certificate()["terminal"] == "UCOPE_CAPABILITY_ABSENT"


def test_efforts_are_interior_to_the_action_support():
    for effort in cc.CANDIDATE_EFFORTS:
        assert Fraction(0) < effort < Fraction(1)


@pytest.mark.parametrize("trials", range(cc.PERIODS))
def test_posteriors_sum_consistently_over_reachable_counts(trials):
    for positive in range(trials + 1):
        rho = cc.posterior_s(positive, trials)
        assert Fraction(0) < rho < Fraction(1)
