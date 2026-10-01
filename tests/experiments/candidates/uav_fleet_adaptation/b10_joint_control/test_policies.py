"""Finite source-interface cases for frozen prior, eligibility, CJ and caches."""
import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS
from experiments.candidates.uav_fleet_adaptation.b02.model import make_student
from experiments.candidates.uav_fleet_adaptation.b10_joint_control.learning import JointActor
from experiments.candidates.uav_fleet_adaptation.b10_joint_control.policies import Policy, off_score, select_cj, ZERO_INDEX
from experiments.candidates.uav_fleet_adaptation.b10_joint_control.reference import Reference, _off


def test_original_prior_private_cache_eligibility_and_fresh_uniforms():
    torch_before, numpy_before = torch.random.get_rng_state().clone(), np.random.get_state()
    parent = make_student(95101).eval().requires_grad_(False)
    actor = JointActor(parent, seed=95102).eval()
    gate = dict(mean=np.zeros(253), scale=np.ones(253), constant=np.zeros(253, dtype=bool),
                coefficients=np.r_[np.zeros(125), np.ones(128)], intercept=np.asarray(.1))
    row = np.zeros(104, dtype=np.float32); row[:3] = (.5, .5, .5)
    p = Policy("J0", parent, gate, actor=actor, world=95103, agent=0, sampling_root=95104)
    first, unavailable, later = (p.query(row, tick, 0) for tick in (0, 4, 20))
    assert first["eligible"] and not unavailable["eligible"] and later["eligible"]
    assert not unavailable["probabilities"][27:].any() and unavailable["action_index"] < 27
    assert unavailable["memo_hit"] and later["memo_hit"] and p.counters["joint_neural_rows"] == 1
    assert p.counters["frozen_neural_rows"] == 1 and p.counters["sampled_draws"] == 3
    assert len({first["innovation"], unavailable["innovation"], later["innovation"]}) == 3
    peer = Policy("J0", parent, gate, actor=actor, world=95103, agent=1, sampling_root=95104)
    other = peer.query(row, 4, 0)
    assert peer.base.cache is not p.base.cache and other["innovation"] != unavailable["innovation"]
    with torch.no_grad(): actor.network[2].bias.add_(.2)
    # New model-version owner after an optimizer-like change: no stale cache.
    new = Policy("J0", parent, gate, actor=actor, world=95103, agent=0, sampling_root=95104)
    changed = new.query(row, 0, 0)
    np.testing.assert_array_equal(changed["prior_hidden"], first["prior_hidden"])
    assert changed["gate_prediction"] == first["gate_prediction"] and not np.array_equal(changed["logits"], first["logits"])
    reference = Reference("J0", parent, gate, actor=actor, world=95103, agent=0, sampling_root=95104)
    rebuilt = reference.query(row, 0, 0)
    assert rebuilt["action_index"] == changed["action_index"]
    np.testing.assert_allclose(rebuilt["probabilities"], changed["probabilities"], rtol=0, atol=5e-14)
    assert reference.counters == new.counters
    assert torch.equal(torch_before, torch.random.get_rng_state())
    assert all(np.array_equal(a, b) for a, b in zip(numpy_before, np.random.get_state()))
    print("B10 policy interface exposure:3 joint forward +1 independent joint forward,4 frozen forwards,6 draws,4 helper misses,0 native/canonical")


def test_cj_strict_ties_all_zero_fallback_and_zero_command():
    assert np.array_equal(COMMANDS[ZERO_INDEX], np.zeros(3)) and ZERO_INDEX == 0
    features = np.zeros(114, dtype=np.float32)
    answer = dict(c_index=7, scores=np.zeros(27), served=np.zeros(27), features=features, next_nav=8)
    assert select_cj(answer, 0., 0.) == (7, True)
    features[5] = .3
    assert select_cj(answer, 0., 0.) == (7, False)
    assert select_cj(answer, .1, 1.) == (ZERO_INDEX, True)
    assert answer["next_nav"] == 8  # Already-advanced original navigation is preserved.
    answer["scores"][7], answer["served"][7] = .1, 1.
    assert select_cj(answer, .1, 1.) == (7, False)
    assert select_cj(answer, .09, 1.) == (7, False)


def test_off_score_matches_separate_scalar_expression_empty_and_one_peer():
    row = np.zeros(104, dtype=np.float32); row[:3] = (.5, .5, .5)
    assert off_score(row) == _off(row) == (0., 0., 0)
    row[3:6] = (.01, .01, .3)
    row[63:67] = (.01, .01, 0., .5)
    a, b = off_score(row), _off(row)
    assert a[2] == b[2] == 2
    np.testing.assert_allclose(a[:2], b[:2], rtol=0, atol=1e-12)
    assert np.isfinite(a[:2]).all()
    print("B10 CJ expression exposure:5 algebraic selections,4 OFF evaluations/16logical held ticks,4 total power links,0 ON search/native")
