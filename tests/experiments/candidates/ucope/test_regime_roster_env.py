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
    # The nested view's own load slot is withheld too, not only the published
    # observation column.
    assert view.base.load == float(sibling.WITHHELD_LOAD_VALUE)
    # ...while the reward still targets the true regime load, reachable only
    # through the environment's explicit accessor.
    assert env.realized_load() == float(cc.LOAD[cc.S])


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
    assert small.realized_load() != large.realized_load()


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


def test_the_enabled_view_carries_no_reachable_load_anywhere():
    """Pro: the environment boundary itself must be fail-closed, not just the
    read set that `policy_features` happens to use today.

    This walks every attribute a policy could reach from the handed-out view and
    asserts the true regime load appears in none of them.  It is deliberately
    mechanical: a future field that reintroduces the leak fails here rather than
    surviving because nobody happened to read it.
    """
    for regime in cc.REGIMES:
        env = sibling.UcopeRegimeRosterEnv(
            _ledger(), regime=regime, evidence_bits=(1, 0, 1)
        )
        truth = float(cc.LOAD[regime])
        assert env.realized_load() == truth, "the env must still know the load"

        view = env.observe()
        reachable: list[float] = []
        for holder in (view, view.base):
            for name in vars(holder):
                value = getattr(holder, name)
                if isinstance(value, (int, float, np.floating, np.integer)):
                    reachable.append(float(value))
                elif isinstance(value, np.ndarray) and value.dtype.kind == "f":
                    reachable.extend(float(x) for x in value.reshape(-1))
        assert reachable, "the walk must actually reach numeric fields"
        assert truth not in reachable, (
            f"the {regime} load {truth} is reachable from the view"
        )


def test_sibling_streams_are_disjoint_from_the_base_ledger():
    """Pro: `_REGIME_STREAM = 0` collided with the base ledger's stream 0.

    `paired_training` passes one seed as BOTH the regime seed and the ledger
    master seed, so `default_rng((seed, episode, 0))` was literally the base
    ledger's temporary-leave generator.  Disjointness is checked by enumeration
    against the streams `make_ledger` actually consumes, so widening the base
    stream set later breaks this test instead of silently re-colliding.
    """
    profile = max(
        roster_env.TRAIN_PROFILES, key=lambda p: p.member_capacity
    )
    base_streams = {0, 1, 3, 4}
    base_streams |= {100 + key for key in range(profile.member_capacity)}
    base_streams |= {200 + key for key in range(profile.member_capacity)}
    assert sibling._REGIME_STREAM not in base_streams
    assert sibling._EVIDENCE_STREAM not in base_streams
    assert sibling._REGIME_STREAM != sibling._EVIDENCE_STREAM

    # ...and the far stronger property: even at the identical seed and episode
    # the sibling's generator state differs from every base stream's, because
    # the domain word sits in front of the entropy tuple.
    seed, episode = 20_260_806, 17
    sibling_draws = {
        tuple(
            sibling._sibling_rng(seed, episode, stream).random(4).tolist()
        )
        for stream in (sibling._REGIME_STREAM, sibling._EVIDENCE_STREAM)
    }
    base_draws = {
        tuple(
            np.random.default_rng(
                np.random.SeedSequence([seed, episode, stream])
            )
            .random(4)
            .tolist()
        )
        for stream in base_streams
    }
    assert not (sibling_draws & base_draws)


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
