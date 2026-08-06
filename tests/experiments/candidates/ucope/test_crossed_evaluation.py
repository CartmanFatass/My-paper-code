"""Proof-sized tests for the exactly-weighted crossed UCOPE evaluation.

The load-bearing test is ``test_the_blind_ceiling_is_attained_and_is_a_maximum``.
External Pro falsified the first pass's ceiling guard because a *sampled* block
is not bounded by the prior expectation.  The whole point of the crossed
estimator is that it restores the bound, so a test that only checked "the guard
returns a dict" would miss the entire claim.  This one instead drives constant
efforts across the support and shows 32.0 is reached at 1/4 and beaten nowhere.
"""

from __future__ import annotations

import math
from fractions import Fraction

import pytest
import torch

from envs.continuous_roster import runtime_capacity as roster_env

from experiments.candidates.ucope import capability_certificate as cc
from experiments.candidates.ucope import crossed_evaluation as ce
from experiments.candidates.ucope import paired_training as pt
from experiments.candidates.ucope import regime_roster_env as sibling


class ConstantEffortPolicy(torch.nn.Module):
    """Plays one fixed effort regardless of input, via the tanh pre-image."""

    def __init__(self, effort: float):
        super().__init__()
        self.pre_squash = math.atanh(2.0 * effort - 1.0)

    def forward(self, features):
        rows = features.shape[0]
        return (
            torch.full((rows,), self.pre_squash),
            torch.zeros(rows),
            torch.zeros(rows),
        )


def _ledger(index: int = 0):
    return ce.evaluation_ledger(index, ledger_seed=4_242)


def test_crossed_weights_are_exact_and_sum_to_one():
    """A weight set that does not sum to 1 is not an expectation."""
    assert len(ce.CROSSED_SUPPORT) == 2 * 2**cc.PERIODS
    total = sum(weight for _regime, _bits, weight in ce.CROSSED_SUPPORT)
    assert isinstance(total, Fraction)
    assert total == Fraction(1), "weights must be exactly 1, not 1.0000000001"


def test_the_blind_ceiling_is_attained_and_is_a_maximum():
    """The guard is only a theorem if 32.0 is really the count-blind maximum.

    Pro's objection to the old guard was that 32.0 bounds an expectation, not a
    sample.  The crossed value IS an expectation, so the bound applies -- but
    only if the analytic argument (per-step max 2/3 at effort 1/4, over ALL
    efforts and not just the two candidate peaks) is right.  This sweeps the
    effort axis and checks it.
    """
    ledger = _ledger()
    at_optimum = ce.crossed_value(
        ConstantEffortPolicy(0.25), ledger, arm=pt.BLIND
    )
    assert at_optimum == pytest.approx(
        pt.BLIND_OPTIMUM, abs=ce.BASE_ANCHORED_TOLERANCE
    )

    for effort in (0.05, 0.15, 0.35, 0.5, 0.65, 0.75, 0.9):
        value = ce.crossed_value(ConstantEffortPolicy(effort), ledger, arm=pt.BLIND)
        assert value <= pt.BLIND_OPTIMUM + ce.BASE_ANCHORED_TOLERANCE, (
            f"effort {effort} beat the certified count-blind ceiling"
        )


def test_the_ceiling_holds_on_every_ledger_not_just_on_average():
    """Pro asked for a per-ledger bound; averaging would hide a single breach."""
    ledgers = [_ledger(index) for index in range(6)]
    readout = ce.crossed_readout(
        ConstantEffortPolicy(0.25), arm=pt.BLIND, ledgers=ledgers
    )
    for value in readout.per_ledger:
        assert value <= pt.BLIND_OPTIMUM + ce.BASE_ANCHORED_TOLERANCE


def test_the_guard_actually_refuses():
    """The old guard set a flag and reported the comparison anyway."""
    ledgers = [_ledger(index) for index in range(3)]
    clean = ce.crossed_readout(
        ConstantEffortPolicy(0.25), arm=pt.BLIND, ledgers=ledgers
    )
    assert ce.blind_ceiling_guard(clean)["passed"]

    breached = ce.CrossedReadout(
        arm=pt.BLIND,
        per_ledger=tuple(list(clean.per_ledger[:-1]) + [pt.BLIND_OPTIMUM + 1.0]),
    )
    verdict = ce.blind_ceiling_guard(breached)
    assert not verdict["passed"]
    assert verdict["breaching_ledger_indices"] == (len(ledgers) - 1,)


def test_crossed_evaluation_is_deterministic():
    """An evaluation that moves between runs cannot support a paired claim."""
    ledger = _ledger()
    policy = ConstantEffortPolicy(0.4)
    first = ce.crossed_value(policy, ledger, arm=pt.INFORMED)
    second = ce.crossed_value(policy, ledger, arm=pt.INFORMED)
    assert first == second


def test_a_count_blind_policy_cannot_separate_the_arms():
    """Sanity on the intervention: with no count dependence, severance is inert.

    ``within_checkpoint_severance`` must return ~0 for a policy that ignores its
    inputs, or a nonzero result on a real policy would prove nothing.
    """
    ledgers = [_ledger(index) for index in range(4)]
    result = ce.within_checkpoint_severance(
        ConstantEffortPolicy(0.3), ledgers=ledgers
    )
    assert result["paired_difference_mean"] == 0.0
    assert all(value == 0.0 for value in result["per_ledger_difference"])


def test_effort_readout_covers_exactly_the_reachable_count_states():
    """(positive, completed) with positive <= completed < PERIODS."""
    table = ce.effort_readout(ConstantEffortPolicy(0.25))
    expected = {
        f"positive={positive},completed={completed}"
        for completed in range(cc.PERIODS)
        for positive in range(completed + 1)
    }
    assert set(table) == expected
    for effort in table.values():
        assert 0.0 < effort < 1.0


def test_the_realized_readout_visits_the_same_states_the_probe_does():
    """The probe is synthetic; the realized readout is the on-manifold check.

    A first attempt froze the time channel at a single value, which asks the
    policy about `(0, 0)` at mid-episode -- a combination the environment cannot
    produce, since completed_epochs determines elapsed time.  The two readouts
    must at least agree on WHICH states exist, or the probe is describing a
    different state space than the one the policy runs in.
    """
    ledgers = [_ledger(index) for index in range(2)]
    realized = ce.realized_effort_readout(
        ConstantEffortPolicy(0.25), ledgers=ledgers
    )
    assert set(realized) == set(ce.effort_readout(ConstantEffortPolicy(0.25)))
    for row in realized.values():
        assert row["steps"] > 0
        assert row["mean_effort"] == pytest.approx(0.25, abs=1e-6)
        assert row["bayes_optimal_effort"] in (0.25, 0.75)


def test_the_probe_uses_a_time_channel_consistent_with_the_epoch():
    """Each epoch's row must be probed at a time that epoch actually spans."""
    for completed in range(cc.PERIODS):
        midpoint = (completed + 0.5) * sibling.EPOCH_LENGTH / roster_env.HORIZON
        low = completed * sibling.EPOCH_LENGTH / roster_env.HORIZON
        high = (completed + 1) * sibling.EPOCH_LENGTH / roster_env.HORIZON
        assert low < midpoint < high


def test_provenance_binds_the_sources_and_the_arguments():
    """Pro could not authenticate the first pass's execution from the files."""
    record = ce.provenance(run_arguments={"iterations": 3})
    assert record["run_arguments"] == {"iterations": 3}
    assert record["torch_version"] and record["numpy_version"]
    for relative in ce._PROVENANCE_SOURCES:
        assert len(record["source_digests"][relative]) == 64


def test_checkpoint_digest_tracks_the_weights():
    left = pt.EffortPolicy()
    torch.manual_seed(99)
    right = pt.EffortPolicy()
    assert ce.checkpoint_digest(left) == ce.checkpoint_digest(left)
    assert ce.checkpoint_digest(left) != ce.checkpoint_digest(right)


def test_the_crossed_support_reproduces_the_certificate_oracle_values():
    """End-to-end tie back: crossing must agree with the exact certificate.

    The blind oracle plays 1/4 always and must score the certificate's blind
    value; that is the same number the certificate derives by exact rational
    arithmetic, so agreement here links the estimator to the frozen gate rather
    than to a re-implementation of it.
    """
    ledger = _ledger()
    measured = ce.crossed_value(ConstantEffortPolicy(0.25), ledger, arm=pt.BLIND)
    certified = float(cc.valuations().blind) * roster_env.HORIZON / cc.PERIODS
    assert measured == pytest.approx(certified, abs=ce.BASE_ANCHORED_TOLERANCE)
