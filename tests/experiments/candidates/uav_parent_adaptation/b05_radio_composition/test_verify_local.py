"""Synthetic saved-array audits; no host, production actor, or C ranking calls."""

import copy

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.contract import array_digest
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, WAYPOINTS
from experiments.candidates.uav_fleet_adaptation.b02.read import check_memo, saved_ranking_choice
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.sampling import decode, make_bundle
from experiments.candidates.uav_parent_adaptation.b05_radio_composition.contract import Protocol
from experiments.candidates.uav_parent_adaptation.b05_radio_composition import verify_local as module


def synthetic_radio(positions, users, mask):
    active = np.array([bool(mask & (1 << i)) for i in range(5)])
    sinr = np.full((5, 50), -np.inf)
    sinr[active] = 0.
    return sinr, np.zeros((5, 50), bool), dict(J=0., served=0, quality=0.)


def synthetic_observation(positions, users, mask, tick):
    rows = np.zeros((5, 104), dtype=np.float32)
    rows[:, :3] = (positions - [0, 0, 50]) / [1000, 1000, 100]
    active = [i for i in range(5) if mask & (1 << i)]
    for i in active:
        for slot, j in enumerate(peer for peer in active if peer != i):
            rows[i, 63 + slot * 4:67 + slot * 4] = [j / 10, 0, 0, .2]
    rows[:, -1] = tick / 256  # Verifier must reset short-fixture clock units.
    return rows


def synthetic_helper(row, nav):
    own = row[:3].astype(np.float64) * [1000, 1000, 100] + [0, 0, 50]
    next_nav = (nav + 1) % 10 if np.linalg.norm(WAYPOINTS[nav] - own[:2]) <= 60 else nav
    n = int(np.count_nonzero(row[3:63].reshape(20, 3)[:, 2] > 0))
    peers = int(np.count_nonzero(row[63:103].reshape(10, 4)[:, 3] > 0))
    return dict(features=np.concatenate((row[:103], np.eye(10, dtype=np.float32)[nav],
                                         np.ones(1, np.float32))), fallback=True, next_nav=next_nav,
                n_current=n, n_peers=peers,
                counters=dict(helper_calls=1, helper_setup_links=(1 + peers) * n, helper_extreme_links=2 * n))


class SyntheticActor:
    def __init__(self, fail_at=None):
        self.calls, self.fail_at = [], fail_at

    def __call__(self, features):
        assert features.shape == (1, 114) and features.dtype == torch.float32
        self.calls.append(features.clone())
        if len(self.calls) == self.fail_at:
            raise RuntimeError('synthetic forward failure')
        return torch.zeros((1, 27), dtype=torch.float32)


@pytest.fixture
def fixture(monkeypatch):
    radio_masks, report_masks, helper_calls = [], [], []

    def radio(positions, users, mask):
        radio_masks.append(mask)
        return synthetic_radio(positions, users, mask)

    def observation(positions, users, mask, tick):
        report_masks.append((tick, mask))
        return synthetic_observation(positions, users, mask, tick)

    def helper(row, nav):
        helper_calls.append((row.copy(), nav))
        return synthetic_helper(row, nav)

    monkeypatch.setattr(module, 'radio', radio)
    monkeypatch.setattr(module, 'observed_rows', observation)
    monkeypatch.setattr(module, 'analyze', helper)

    def build(family='S_I', masked=True):
        protocol = Protocol(worlds=(29347000,), horizon=8).validate()
        world, h, d = protocol.worlds[0], protocol.horizon, protocol.horizon // 4
        rng = np.random.RandomState(world)
        positions = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000), rng.uniform(50, 150)]
                              for _ in range(5)])
        users = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000)] for _ in range(50)])
        masks = [31, 31] + [21] * 6 if masked else [31] * 8
        raw = dict(positions=np.broadcast_to(positions, (h + 1, 5, 3)).copy(),
                   initial_users=users, observations=np.stack([synthetic_observation(positions, users, masks[t], t)
                                                             for t in range(h)]),
                   terminal_observation=synthetic_observation(positions, users, masks[-1], h),
                   commands=np.zeros((h, 5, 3), np.float32), proposals=np.zeros((d, 5, 3), np.float32),
                   transmitter_mask=np.array([[bool(mask & 1 << i) for i in range(5)] for mask in masks]),
                   terminal_mask=np.array([bool(masks[-1] & 1 << i) for i in range(5)]),
                   reward=np.zeros(h), served=np.zeros(h, np.int16), sinr_quality=np.zeros(h),
                   sinr=np.stack([synthetic_radio(positions, users, mask)[0] for mask in masks]),
                   connections=np.zeros((h, 5, 50), bool), decision_ticks=np.arange(0, h, 4, dtype=np.int64),
                   completed_steps=np.array(h), completed_decisions=np.array(d), episode_complete=np.array(True),
                   features=np.zeros((d, 5, 114), np.float32), nav_pre=np.zeros((d, 5), np.int64),
                   nav_next=np.zeros((d, 5), np.int64), fallback=np.ones((d, 5), bool),
                   memo_hit=np.zeros((d, 5), bool), n_current=np.zeros((d, 5), np.int64),
                   n_peers=np.zeros((d, 5), np.int64), action_index=np.zeros((d, 5), np.int64),
                   modal_index=np.zeros((d, 5), np.int64), probabilities=np.zeros((d, 5, 27)))
        raw['observations'][..., -1] = (np.arange(h) / h).astype(np.float32)[:, None]
        raw['terminal_observation'][:, -1] = 1.
        student, stochastic = family == 'S_I', family != 'C'
        actor = SyntheticActor() if student else None
        if student:
            raw['logits'] = np.zeros((d, 5, 27), np.float32)
        else:
            raw['policy_scores'] = np.zeros((d, 5, 27))
            raw['policy_served'] = np.zeros((d, 5, 27))
        bundle = make_bundle(world, 0, horizon=h, public_root=protocol.public_root,
                             departure_root=protocol.departure_root, tail_root=protocol.tail_root) if stochastic else None
        if stochastic:
            raw.update(departure_threshold=np.zeros((d, 5), np.int64), tail_thresholds=np.zeros((d, 5, 26), np.uint64),
                       effective_probabilities=np.zeros((d, 5, 27)), departure_integer=np.zeros((d, 5), np.int64),
                       requested_departure=np.zeros((d, 5), bool),
                       private_depart_integer=bundle['private_depart'].copy(), private_tail_integer=bundle['private_tail'].copy())
        nav = np.array([np.argmin(np.sum((WAYPOINTS - module.own_position(r)[:2]) ** 2, axis=1))
                        for r in raw['observations'][0]])
        caches = [{} for _ in range(5)]
        for j, tick in enumerate(raw['decision_ticks']):
            raw['nav_pre'][j] = nav
            for agent in range(5):
                obs = raw['observations'][tick, agent]
                pd = synthetic_helper(obs, int(nav[agent]))
                for target, source in (('features', 'features'), ('fallback', 'fallback'), ('nav_next', 'next_nav'),
                                       ('n_current', 'n_current'), ('n_peers', 'n_peers')):
                    raw[target][j, agent] = pd[source]
                key = obs[:103].tobytes() + bytes([int(nav[agent])])
                raw['memo_hit'][j, agent] = key in caches[agent]
                caches[agent][key] = True
                modal = 0 if student else saved_ranking_choice(obs, pd['next_nav'], True,
                                                              np.zeros(27), np.arange(27))
                p = np.full(27, 1 / 27 if student else .1 / 26 if stochastic else 0.)
                if not student:
                    p[modal] = .9 if stochastic else 1.
                raw['modal_index'][j, agent], raw['probabilities'][j, agent] = modal, p
                if stochastic:
                    decoded = decode(p, law='I', rank=agent, public=0,
                                     private_depart=int(bundle['private_depart'][j, agent]),
                                     private_tail=int(bundle['private_tail'][j, agent]))
                    for key in ('departure_threshold', 'tail_thresholds', 'effective_probabilities',
                                'departure_integer', 'requested_departure', 'action_index'):
                        raw[key][j, agent] = decoded[key]
                else:
                    raw['action_index'][j, agent] = modal
                raw['proposals'][j, agent] = COMMANDS[raw['action_index'][j, agent]]
            nav = raw['nav_next'][j].copy()
        row = dict(arm=family + '_S2', world=world, tape=0 if stochastic else -1,
                   initial_state_sha256=array_digest(positions, users),
                   bundle_sha256=array_digest(bundle['public'], bundle['private_depart'], bundle['private_tail'])
                   if stochastic else None)
        row['policy_counts'] = check_memo({**raw, 'action_index': raw['modal_index']},
                                         {**row, 'arm': 'S_greedy' if student else 'C_memo'},
                                         '', 'student' if student else 'C')
        raw['coord_dummy_field'] = np.array([np.nan])  # Another writer owns coordinator schema.
        return raw, row, protocol, actor, bundle

    return build, radio_masks, report_masks, helper_calls


@pytest.mark.parametrize('family', ['C', 'Q_I', 'S_I'])
def test_actual_mask_reconstruction_complete_counts_and_allowed_proposal_overrides(fixture, family):
    build, radio_masks, report_masks, helper_calls = fixture
    raw, row, protocol, actor, bundle = build(family)
    calls = module.local_counts()
    checks = []
    audit = module.verify_local(raw, row, protocol, actor, bundle, calls, lambda: checks.append(True))
    assert radio_masks == [31, 31] + [21] * 6
    assert report_masks == [(0, 31), (4, 21), (8, 21)]
    assert calls['native_formula_attempts'] == calls['native_formula_completed'] == 8 + 2 + 1
    assert calls['native_user_links_attempts'] == calls['native_user_links_completed'] == 11 * 250
    assert calls['native_peer_geometry_links_attempts'] == calls['native_peer_geometry_links_completed'] == 80 + 12 + 12
    assert calls['actual_motion_agent_ticks'] == 40
    assert audit['empty_local_rows'] == audit['fallback_local_rows'] == 10
    assert audit['silent_local_rows'] == 2
    assert audit['max_native_sinr_error'] == audit['max_native_metric_error'] == audit['max_report_observation_error'] == 0
    if family == 'S_I':
        assert len(helper_calls) == len(actor.calls) == 10
        assert calls['S_helper_attempts'] == calls['S_helper_completed'] == 10
        assert calls['S_forward_attempts'] == calls['S_forward_completed'] == 10
        assert len(checks) == 11 + 10 + 10
    else:
        assert not helper_calls
        assert calls['C_fallback_candidate_motion_steps'] == row['policy_counts']['misses'] * 108
    assert not np.array_equal(raw['commands'], np.repeat(raw['proposals'], 4, axis=0))


def test_S_recomputes_every_cache_hit_without_reusing_sampled_result(fixture):
    build, _, _, helper_calls = fixture
    raw, row, protocol, actor, bundle = build('S_I', masked=False)
    assert raw['memo_hit'][1].any()
    calls = module.local_counts()
    module.verify_local(raw, row, protocol, actor, bundle, calls, lambda: None)
    assert len(helper_calls) == len(actor.calls) == calls['S_forward_completed'] == 10
    assert row['policy_counts']['neural_rows'] < 10


@pytest.mark.parametrize('value,active', [(np.nan, True), (np.inf, True), (-np.inf, True),
                                        (np.nan, False), (np.inf, False), (0., False)])
def test_only_masked_negative_infinity_is_legal(fixture, value, active):
    raw, row, protocol, actor, bundle = fixture[0]('C')
    raw['sinr'][2, 0 if active else 1, 0] = value
    calls = module.local_counts()
    with pytest.raises(AssertionError, match='SINR'):
        module.verify_local(raw, row, protocol, actor, bundle, calls, lambda: None)
    assert calls['native_formula_attempts'] == 0


@pytest.mark.parametrize('field', ['nav_next', 'features', 'private_depart_integer', 'tail_thresholds',
                                 'departure_integer', 'action_index', 'memo_hit', 'initial_users',
                                 'observations', 'probabilities'])
def test_local_seed_nav_observation_cache_and_tape_corruptions_fail(fixture, field):
    raw, row, protocol, actor, bundle = fixture[0]('S_I', masked=False)
    if field == 'observations':
        raw[field][4, 0, 65] += .01  # Report boundary must be reconstructed, not just own xyz.
    elif field == 'features':
        raw[field][0, 0, 103:113] = np.roll(raw[field][0, 0, 103:113], 1)
    elif field == 'memo_hit':
        raw[field][0, 0] = True
    elif field == 'initial_users':
        raw[field][0, 0] += 1
    elif field == 'nav_next':
        raw[field][0, 0] = (raw[field][0, 0] + 1) % 10
    elif field == 'action_index':
        raw[field][0, 0] = (raw[field][0, 0] + 1) % 27
        raw['proposals'][0, 0] = COMMANDS[raw[field][0, 0]]
    else:
        raw[field].flat[0] += 1
    with pytest.raises(AssertionError):
        module.verify_local(raw, row, protocol, actor, bundle, module.local_counts(), lambda: None)


def test_tape_digest_includes_unused_public_stream(fixture):
    raw, row, protocol, actor, bundle = fixture[0]('Q_I')
    bundle = copy.deepcopy(bundle)
    bundle['public'][0] ^= np.uint64(1)
    with pytest.raises(AssertionError, match='bundle digest'):
        module.verify_local(raw, row, protocol, actor, bundle, module.local_counts(), lambda: None)


def test_motion_attempt_count_is_charged_before_failed_clip_comparison(fixture):
    raw, row, protocol, actor, bundle = fixture[0]('C')
    raw['positions'][2, 0, 0] += 1
    calls = module.local_counts()
    with pytest.raises(AssertionError, match='motion'):
        module.verify_local(raw, row, protocol, actor, bundle, calls, lambda: None)
    assert calls['actual_motion_agent_ticks'] == 40 and calls['native_formula_attempts'] == 0


def test_forward_failure_preserves_before_call_exposure(fixture):
    raw, row, protocol, _, bundle = fixture[0]('S_I')
    actor, calls = SyntheticActor(fail_at=3), module.local_counts()
    with pytest.raises(RuntimeError, match='forward failure'):
        module.verify_local(raw, row, protocol, actor, bundle, calls, lambda: None)
    assert calls['S_helper_attempts'] == calls['S_helper_completed'] == 3
    assert calls['S_forward_attempts'] == 3 and calls['S_forward_completed'] == 2


def test_helper_failure_and_budget_expiry_preserve_only_attempted_calls(fixture, monkeypatch):
    raw, row, protocol, actor, bundle = fixture[0]('S_I')
    calls = module.local_counts()

    def failed_helper(*args):
        raise RuntimeError('synthetic helper failure')

    monkeypatch.setattr(module, 'analyze', failed_helper)
    with pytest.raises(RuntimeError, match='helper failure'):
        module.verify_local(raw, row, protocol, actor, bundle, calls, lambda: None)
    assert calls['S_helper_attempts'] == 1 and calls['S_helper_completed'] == 0
    assert calls['S_forward_attempts'] == 0
    calls = module.local_counts()

    def expired():
        raise RuntimeError('synthetic expired budget')

    with pytest.raises(RuntimeError, match='budget'):
        module.verify_local(raw, row, protocol, actor, bundle, calls, expired)
    assert calls['native_formula_attempts'] == 0 and calls['S_helper_attempts'] == 0


def test_native_formula_failure_preserves_attempted_links(fixture, monkeypatch):
    raw, row, protocol, actor, bundle = fixture[0]('C')

    def fail(*args):
        raise RuntimeError('synthetic radio failure')

    monkeypatch.setattr(module, 'radio', fail)
    calls = module.local_counts()
    with pytest.raises(RuntimeError, match='radio failure'):
        module.verify_local(raw, row, protocol, actor, bundle, calls, lambda: None)
    assert calls['native_formula_attempts'] == 1 and calls['native_formula_completed'] == 0
    assert calls['native_user_links_attempts'] == 250 and calls['native_user_links_completed'] == 0


@pytest.mark.parametrize('field,dtype', [('sinr', np.float32), ('commands', np.float64),
                                      ('features', np.float64), ('served', np.int64),
                                      ('transmitter_mask', np.int8), ('tail_thresholds', np.int64)])
def test_local_native_dtypes_are_checked_without_entire_keyset_equality(fixture, field, dtype):
    raw, row, protocol, actor, bundle = fixture[0]('S_I')
    raw[field] = raw[field].astype(dtype)
    with pytest.raises(AssertionError, match='dtype'):
        module.verify_local(raw, row, protocol, actor, bundle, module.local_counts(), lambda: None)
