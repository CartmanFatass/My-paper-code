"""Proof-sized tests for the UCOPE sibling environment.

The certificate proves the specified dynamics contain the mechanism. These
tests prove the environment implements those dynamics -- the two halves of the
gate the external ruling required before training may begin.
"""

from __future__ import annotations

from fractions import Fraction

import numpy as np
import pytest

from envs.continuous_roster import runtime_capacity as roster_env

from experiments.candidates.ucope import capability_certificate as cc
from experiments.candidates.ucope import regime_conformance as rc
from experiments.candidates.ucope import regime_roster_env as sibling


def _ledger():
    return rc.default_ledger()


def test_disabled_projection_reproduces_the_base_environment():
    """Exact base projection: intervention off must BE the base env, step by step."""
    assert rc.disabled_projection_matches_base()


def test_load_is_withheld_from_the_observation():
    env = sibling.UcopeRegimeRosterEnv(
        _ledger(), regime=cc.S, evidence_bits=(0, 0, 0)
    )
    view = env.observe()
    active = view.active_mask
    published = view.observations[active, sibling.LOAD_INDEX]
    assert np.all(published == sibling.WITHHELD_LOAD_VALUE)
    # ...while the reward still targets the true regime load.
    assert view.realized_load == float(cc.LOAD[cc.S])


def test_target_mix_is_still_exactly_observed():
    """Only the load coordinate is severed; the mix half stays solved."""
    ledger = _ledger()
    base = roster_env.RuntimeCapacityRosterEnv(ledger)
    env = sibling.UcopeRegimeRosterEnv(
        ledger, regime=cc.L, evidence_bits=(1, 1, 1)
    )
    base_view, view = base.observe(), env.observe()
    active = view.active_mask
    assert np.array_equal(
        view.observations[active, 4], base_view.observations[active, 4]
    )


def test_regime_changes_only_the_load_channel():
    """Capabilities, priority, count, age, previous action and time are untouched."""
    ledger = _ledger()
    small = sibling.UcopeRegimeRosterEnv(ledger, regime=cc.S, evidence_bits=(0, 0, 0))
    large = sibling.UcopeRegimeRosterEnv(ledger, regime=cc.L, evidence_bits=(0, 0, 0))
    a, b = small.observe(), large.observe()
    assert np.array_equal(a.observations, b.observations), (
        "the regime must not be visible anywhere in the observation"
    )
    assert a.realized_load != b.realized_load


def test_evidence_arrives_after_the_epoch_not_before():
    """Epoch t must decide under the count from epochs < t, or the gate is circular."""
    env = sibling.UcopeRegimeRosterEnv(
        _ledger(), regime=cc.S, evidence_bits=(1, 1, 1)
    )
    seen: list[tuple[int, int]] = []
    terminated = False
    while not terminated:
        view = env.observe()
        if view.base.time % sibling.EPOCH_LENGTH == 0:
            seen.append((view.completed_epochs, view.positive_count))
        actions = sibling.uniform_effort_actions(view, 0.25)
        _, terminated, _ = env.step(actions)
    assert seen == [(0, 0), (1, 1), (2, 2)]


def test_reward_is_exactly_the_certificate_tent():
    """The base reward under a matched mix must equal cc.reward to float32."""
    ledger = _ledger()
    for regime in cc.REGIMES:
        for effort in cc.CANDIDATE_EFFORTS:
            env = sibling.UcopeRegimeRosterEnv(
                ledger, regime=regime, evidence_bits=(0, 0, 0)
            )
            view = env.observe()
            reward, _, _ = env.step(
                sibling.uniform_effort_actions(view, float(effort))
            )
            expected = float(cc.reward(effort, cc.LOAD[regime]))
            assert reward == pytest.approx(expected, abs=2.0**-23)


def test_sibling_conforms_to_the_certificate_exactly():
    """The decisive environment-side gate, over the whole enumerated tree."""
    report = rc.conformance()
    assert report["terminal"] == "UCOPE_SIBLING_CONFORMS"
    for row in report["rows"].values():
        assert row["conforms"]


def test_measured_information_gain_matches_the_certified_gain():
    report = rc.conformance()
    assert report["measured_informed_minus_blind"] == pytest.approx(
        float(Fraction(9, 32) * sibling.EPOCH_LENGTH), abs=rc.TOLERANCE
    )


def test_severing_the_count_removes_the_gain_exactly():
    """The decisive control: the advantage is the information, not the wiring."""
    report = rc.conformance()
    assert report["measured_severed_minus_blind"] == 0.0


def test_severed_runs_the_informed_code_path():
    """SEVERED must differ from BLIND only in what it may read, not in how."""
    ledger = _ledger()
    totals = {
        arm: rc.run_episode(
            arm, ledger=ledger, regime=cc.S, evidence_bits=(1, 1, 1)
        )
        for arm in (rc.BLIND, rc.SEVERED)
    }
    assert totals[rc.SEVERED] == totals[rc.BLIND]


def test_evidence_likelihoods_are_regime_dependent():
    """If the evidence were uninformative the whole sibling would be pointless."""
    counts = {}
    for regime in cc.REGIMES:
        bits = [
            sum(
                sibling.draw_evidence(episode, regime, evidence_seed=7)
            )
            for episode in range(400)
        ]
        counts[regime] = sum(bits) / (400 * sibling.PERIODS)
    assert counts[cc.S] > counts[cc.L]


def test_regime_draw_respects_the_prior():
    draws = [
        sibling.draw_regime(episode, regime_seed=11) for episode in range(2000)
    ]
    share = draws.count(cc.S) / len(draws)
    assert 0.45 < share < 0.55


def test_illegal_action_is_still_refused():
    env = sibling.UcopeRegimeRosterEnv(
        _ledger(), regime=cc.S, evidence_bits=(0, 0, 0)
    )
    view = env.observe()
    actions = sibling.uniform_effort_actions(view, 0.25)
    actions[view.active_mask, 0] = 2.0
    with pytest.raises(ValueError):
        env.step(actions)


def test_unregistered_regime_is_refused():
    with pytest.raises(ValueError):
        sibling.UcopeRegimeRosterEnv(_ledger(), regime="M", evidence_bits=(0, 0, 0))


def test_wrong_evidence_length_is_refused():
    with pytest.raises(ValueError):
        sibling.UcopeRegimeRosterEnv(_ledger(), regime=cc.S, evidence_bits=(0, 0))
