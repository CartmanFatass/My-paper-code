"""Non-panel synthetic checks; no native episode, training, or fit."""

import inspect

import numpy as np
import pytest

from experiments.candidates.uav_radio_activation.b03 import protocol as p
from experiments.candidates.uav_registered_service.b01 import history as h, scheduler as old
from experiments.candidates.uav_service_age.b01 import features as f, scheduler as s


def inputs():
    own = np.tile([.5, .5, .5], (5, 1)).astype(np.float32)
    actual = np.zeros((5, 3))
    proposed = np.tile([1, 0, 0], (5, 1))
    packet = p.encode_map(np.tile([500, 500], (50, 1)))
    return own, actual, proposed, packet


def make(arm, *, clock=lambda: 0., horizon=8):
    own, actual, proposed, packet = inputs()
    return s.Scheduler(arm, packet, clock, lambda: 0., horizon=horizon), own, actual, proposed


def distinct_search(monkeypatch):
    calls = []

    def search(score, key, current_mask, proposal_q):
        pair = (0, 1) if not calls else (26, 31)
        calls.append(pair)
        score(*pair)
        return pair

    monkeypatch.setattr(s, 'sequential_search', search)
    return calls


def test_w_key_controls_both_inner_orders_and_final_choice():
    native = np.zeros((27, 32, 3))
    native[2, 1, 0] = 100
    costs = np.full((27, 32), 100)
    costs[1, 1], costs[1, 2], costs[0, 3], costs[4, 3] = 80, 50, 75, 60
    calls = []

    def score(q, mask):
        calls.append((q, mask))
        return native[q, mask]

    key = lambda q, m: s.ordering_w(q, m, native[q, m], costs[q, m], 0)
    assert s.sequential_search(score, key, 1, 0) == (1, 2)
    assert len(calls) == 116
    assert calls[:27] == [(q, 1) for q in range(27)]
    assert calls[27:58] == [(1, m) for m in range(1, 32)]
    assert calls[58:89] == [(0, m) for m in range(1, 32)]
    assert calls[89:] == [(q, 3) for q in range(27)]
    costs[4, 3] = 40
    assert s.sequential_search(score, key, 1, 0) == (4, 3)


def test_postmove_age_origin_reset_and_terminal_truncation():
    prefix = h.ServiceHistory()
    contacts = np.zeros((4, 50), bool)
    cost, last = s.age_cost(prefix, contacts, 2)
    assert cost == 50 * (3 + 4 + 5 + 6)
    assert (last == -1).all() and (prefix.last == -1).all()
    contacts[1, 0] = True
    cost, last = s.age_cost(prefix, contacts, 2)
    assert cost == 49 * 18 + 3 + 0 + 1 + 2
    assert last[0] == 3
    assert s.age_cost(prefix, np.zeros((2, 50), bool), 254)[0] == 50 * (255 + 256)
    assert f.model_ages(np.array([-1, 0, 3]), 3).tolist() == [4, 3, 0]


def test_dual_o_exact_frozen_equivalence_shared_cache_and_private_candidates():
    actor, own, actual, proposed = make('M', horizon=12)
    frozen = old.Scheduler('O', inputs()[3], lambda: 0., lambda: 0., horizon=12)
    for tick in range(12):
        if tick % 4 == 0:
            r = actor.decide(own, actual, proposed, tick, 1)
            o = frozen.decide(own, actual, proposed, tick, 1)
            assert r['plan_available'].tolist() == [True, True]
            assert r['candidate_requests'] == 232 and r['ordering_requests'].tolist() == [116, 116]
            assert r['request_orderings'].tolist() == [0] * 116 + [1] * 116
            assert list(dict.fromkeys(map(tuple, r['request_pairs'][:116]))) == o['evaluated_pairs']
            assert tuple(r['plan_pairs'][0]) == o['sequential_pair']
            np.testing.assert_array_equal(r['plan_commands'][0], o['commands'])
            assert r['plan_masks'][0] == o['mask']
            assert r['o_key_length'] == o['key_length']
            for q, m in o['evaluated_pairs']:
                np.testing.assert_array_equal(r['scores'][q, m], o['scores'][q, m])
                np.testing.assert_array_equal(r['candidate_contacts'][q, m], o['candidate_contacts'][q, m])
                np.testing.assert_array_equal(r['o_ordering_keys'][q, m], o['ordering_keys'][q, m])
            assert r['state_reductions'] == r['candidate_plans'] * r['scored_length']
            assert r['candidate_cache_hits'] == 232 - r['candidate_plans']
            assert r['geometry_snapshots'] == 27 * r['scored_length']
            prefix = h.ServiceHistory(actor.execution.history.start_tick, r['prefix_last'].copy(), r['prefix_windows'].copy())
            for q, m in r['evaluated_pairs']:
                cost, last = s.age_cost(prefix, r['candidate_contacts'][q, m], tick + 2)
                assert cost == r['candidate_age_costs'][q, m]
                assert r['w_ordering_keys'][q, m, 0] == -cost
                np.testing.assert_array_equal(last, r['candidate_endpoint_last'][q, m])
            # Neither prefix nor candidate forecast is persisted into execution.
            assert actor.execution.next_unsettled == tick
            assert sorted(actor.execution.predicted) == list(range(tick))
            np.testing.assert_array_equal(actor.execution.history.last, frozen.execution.history.last)
        actor.executed(tick, actual, 1)
        frozen.executed(tick, actual, 1)


def test_w_is_single_plan_cost_and_terminal_two_ticks():
    actor, own, actual, proposed = make('W')
    first = actor.decide(own, actual, proposed, 0, 7)
    assert first['plan_available'].tolist() == [False, True]
    assert first['ordering_requests'].tolist() == [0, 116]
    assert first['candidate_requests'] == 116
    assert first['o_key_length'] == 0 and np.isnan(first['o_ordering_keys']).all()
    assert first['request_count'] == 116 and (first['request_pairs'][116:] == -1).all()
    for tick in range(4):
        actor.executed(tick, actual, 7)
    terminal = actor.decide(own, actual, proposed, 4, 7)
    assert terminal['scored_length'] == 2
    assert terminal['candidate_contacts'].shape == (27, 32, 2, 50)
    assert terminal['state_reductions'] == 2 * terminal['candidate_plans']
    assert terminal['ordering_keys'].shape == (27, 32, 57)
    assert terminal['key_length'] == 7


def test_alias_is_exact_full_commands_and_mask_not_clipped_endpoint():
    commands = np.zeros((2, 5, 3))
    masks = np.array([7, 7])
    assert s.full_plan_alias(commands, masks, [True, True])
    assert not s.full_plan_alias(commands, masks, [False, True])
    commands[1, 4, 0] = 1
    assert not s.full_plan_alias(commands, masks, [True, True])
    commands[:] = 0
    masks[1] = 3
    assert not s.full_plan_alias(commands, masks, [True, True])
    # Different commands remain distinct when clipping makes trajectories equal.
    masks[:] = 7
    commands[1, 4, 0] = 1
    clipped = np.clip(np.full((2, 5, 3), p.HIGH) + commands * 30, p.LOW, p.HIGH)
    np.testing.assert_array_equal(clipped[0], clipped[1])
    assert not s.full_plan_alias(commands, masks, [True, True])


def test_alias_never_calls_selector_and_has_zero_actor_weight(monkeypatch):
    monkeypatch.setattr(s, 'model', lambda *a: (np.zeros(50, bool), np.zeros(3)))
    monkeypatch.setattr(s, 'greedy_connection_assignment', lambda *a: np.zeros((5, 50), bool))
    monkeypatch.setattr(s, 'service_metrics', lambda *a: dict(J=0., served=0, quality=0.))
    actor, own, actual, proposed = make('L')
    r = actor.decide(own, actual, proposed, 0, 7,
                     selector=lambda _: pytest.fail('alias must not infer'), innovation=None)
    assert r['timely'] and r['alias'] and not r['sampled']
    assert r['actor_weight'] == 0 and r['forced_reason'] == 'alias'
    assert r['features'].dtype == np.float32 and r['feature_available']


@pytest.mark.parametrize('innovation,expected', [(0., 0), (.249, 0), (.25, 1), (.999, 1)])
def test_prebound_uniform_and_m_reference(monkeypatch, innovation, expected):
    distinct_search(monkeypatch)
    actor, own, actual, proposed = make('L')
    seen = []
    r = actor.decide(own, actual, proposed, 0, 7,
                     selector=lambda x: seen.append(x.copy()) or np.array([.25, .75], np.float32), innovation=innovation)
    assert r['sampled'] and r['actor_weight'] == 1 and r['effective_actor_row']
    assert r['sampled_choice'] == r['requested_choice'] == r['actual_choice'] == expected
    assert r['m_choice'] == max(range(2), key=lambda i: tuple(r['plan_w_keys'][i]))
    assert r['logp'] == np.log(r['probabilities'][expected])
    np.testing.assert_array_equal(seen[0], r['features'])
    np.testing.assert_array_equal(r['commands'], r['plan_commands'][expected])
    assert r['mask'] == r['plan_masks'][expected]


@pytest.mark.parametrize('stage', ['packing', 'actor', 'decode'])
def test_forced_vs_sampled_late_retains_whole_actual_plan(monkeypatch, stage):
    distinct_search(monkeypatch)
    now, seen = [0.], []
    actor, own, actual, proposed = make('L', clock=lambda: now[0])
    actual[:] = [0, -1, 0]
    if stage == 'packing':
        original = s.pack_features

        def late_pack(*args, **kwargs):
            result = original(*args, **kwargs)
            now[0] = 2.
            return result

        monkeypatch.setattr(s, 'pack_features', late_pack)
    if stage == 'decode':
        original = s.decode_command

        def late_decode(*args):
            result = original(*args)
            now[0] = 2.
            return result

        monkeypatch.setattr(s, 'decode_command', late_decode)

    def selector(x):
        seen.append(x.copy())
        if stage == 'actor':
            now[0] = 2.
        return np.array([.5, .5], np.float32)

    r = actor.decide(own, actual, proposed, 0, 7, selector=selector, innovation=.75)
    assert not r['timely'] and r['actual_timeout']
    assert r['command_packet'] == b'' and r['mask'] == 7
    np.testing.assert_array_equal(r['commands'], actual)
    assert r['sampled'] == (stage != 'packing')
    assert r['sampled_late'] == (stage != 'packing')
    assert r['actor_weight'] == (0 if stage == 'packing' else 1)
    if stage != 'packing':
        assert r['requested_choice'] == 1 and r['actual_choice'] == -1
        assert r['requested_available'] and r['logp'] == np.log(.5)
        np.testing.assert_array_equal(r['features'], seen[0])
    else:
        assert seen == [] and r['forced_reason'] == 'deadline'
    assert actor.execution.predicted == {} and actor.execution.next_unsettled == 0


def test_first_missing_report_causal_zero_fills_and_censored_recovery():
    actor, own, actual, proposed = make('M', clock=lambda: 2., horizon=12)
    missing = actor.decide(own, actual, proposed, 0, 7, started=0.)
    assert not missing['decoded_anchor'] and missing['history_start'] == -1
    assert actor.execution.anchors == {}
    assert missing['feature_availability'].tolist() == [False] * 5
    assert missing['features'].shape == (f.FEATURE_DIM,)
    for name in ('positions', 'proposals', 'model_ages', 'model_unknown', 'prefix_ages',
                 'prefix_unknown', 'O_commands', 'W_commands', 'pending_commands', 'pending_mask', 'pending_available'):
        assert not missing['features'][f.FEATURE_SLICES[name]].any()
    saved = missing['features'].copy()
    for tick in range(4):
        actor.executed(tick, actual, 7)
    actor.clock = lambda: 0.
    recovered = actor.decide(own, actual, proposed, 4, 7)
    assert recovered['timely'] and recovered['history_start'] == 4
    assert recovered['unknown_age'].all() and recovered['model_tick'] == 3
    np.testing.assert_array_equal(recovered['features'][f.FEATURE_SLICES['model_ages']], np.full(50, 4 / 256., np.float32))
    assert recovered['window_valid'].tolist() == [False, True, True, True]
    assert actor.execution.predicted == {}
    np.testing.assert_array_equal(missing['features'], saved)


def test_interrupted_settlement_keeps_completed_past_and_causal_partial_features():
    now = [0.]
    actor, own, actual, proposed = make('M', clock=lambda: now[0], horizon=12)
    actor.execution.anchor(0, np.tile([500, 500, 100], (5, 1)))
    for tick in range(4):
        actor.executed(tick, actual, 7)
    calls = [0]

    def evaluate(*args):
        calls[0] += 1
        served = np.zeros(50, bool)
        served[calls[0] - 1] = True
        if calls[0] == 2:
            now[0] = 2.
        return served, np.zeros(3)

    retained_settle = actor.execution.settle
    actor.execution.settle = lambda stop, check: retained_settle(stop, check, evaluate)
    late = actor.decide(own, actual, proposed, 4, 7)
    assert not late['timely'] and late['history_after'] == 2
    assert late['history_reductions'] == 2 and not late['snapshot_valid']
    assert late['decoded_anchor'] and 4 in actor.execution.anchors
    assert sorted(actor.execution.predicted) == [0, 1]
    assert late['model_last'][:3].tolist() == [0, 1, -1]
    assert late['model_tick'] == 1
    np.testing.assert_array_equal(late['features'][f.FEATURE_SLICES['model_ages']][:3], np.array([1, 0, 2], np.float32) / 256.)
    saved = late['features'].copy()
    now[0] = 0.
    for tick in range(4, 8):
        actor.executed(tick, actual, 7)
    actor.execution.settle = retained_settle
    next_report = actor.decide(own, actual, proposed, 8, 7)
    assert next_report['timely'] and next_report['history_after'] == 8
    assert next_report['history_reductions'] == 6
    np.testing.assert_array_equal(late['features'], saved)


def test_encode_overrun_does_not_supply_position_or_proposal_features(monkeypatch):
    now = [0.]
    actor, own, actual, proposed = make('M', clock=lambda: now[0])
    original = s.encode_reports

    def late_encode(*args):
        result = original(*args)
        now[0] = 2.
        return result

    monkeypatch.setattr(s, 'encode_reports', late_encode)
    r = actor.decide(own, actual, proposed, 0, 7)
    assert r['reports'] and not r['decoded_anchor'] and actor.execution.anchors == {}
    assert not r['features'][f.FEATURE_SLICES['positions']].any()
    assert not r['features'][f.FEATURE_SLICES['proposals']].any()
    assert r['recurring_bytes'] == 120 and not r['sampled']


def test_feature_spec_exact_slices_fixed_scales_and_truth_free_api():
    actor, own, actual, proposed = make('M')
    r = actor.decide(own, actual, proposed, 0, 7)
    assert f.FEATURE_DIM == 635 and f.FEATURE_SPEC['dim'] == 635
    fields = f.FEATURE_SPEC['fields']
    assert fields[0]['start'] == 0 and fields[-1]['stop'] == f.FEATURE_DIM
    assert all(a['stop'] == b['start'] for a, b in zip(fields, fields[1:]))
    np.testing.assert_array_equal(r['features'][f.FEATURE_SLICES['map']], np.full(100, .5, np.float32))
    np.testing.assert_array_equal(r['features'][f.FEATURE_SLICES['positions']], np.full(15, .5, np.float32))
    np.testing.assert_array_equal(r['features'][f.FEATURE_SLICES['actual_mask']], [1, 1, 1, 0, 0])
    assert r['feature_wall'] == r['actor_wall'] == 0
    assert set(inspect.signature(actor.executed).parameters) == {'tick', 'commands', 'mask'}
    assert set(inspect.signature(actor.decide).parameters) == {
        'own_observation', 'actual_commands', 'proposals', 'tick', 'current_mask',
        'started', 'cpu_started', 'selector', 'innovation'}


def test_extra_records_are_fixed_shape_through_missing_terminal_and_strings():
    from experiments.candidates.uav_service_age.b01 import study

    actor, own, actual, proposed = make('M', clock=lambda: 2., horizon=12)
    raw = study.allocate_raw(12, 'M', actor.sites, inputs()[3])
    rows = []
    for tick in range(12):
        if tick % 4 == 0:
            r = actor.decide(own, actual, proposed, tick, 7, started=0.)
            study.record_round(raw, r, tick, 'M')
            rows.append(r)
            actor.clock = lambda: 0.
        actor.executed(tick, actual, 7)
    assert rows[0]['forced_reason'].dtype == np.dtype('<U32')
    assert rows[-1]['candidate_contacts'].shape[2] == 2
    for key in s.EXTRA_RECORD_FIELDS:
        assert np.asarray(rows[0][key]).dtype != np.dtype('O')
        assert np.asarray(rows[0][key]).shape == np.asarray(rows[-1][key]).shape
        np.testing.assert_array_equal(raw['age_' + key][0], rows[0][key])
        np.testing.assert_array_equal(raw['age_' + key][-1], rows[-1][key])
    assert raw['age_forced_reason'].dtype == np.dtype('<U32')


def test_float32_softmax_roundoff_has_matching_sampling_and_saved_law(monkeypatch):
    distinct_search(monkeypatch)
    actor, own, actual, proposed = make('L')
    probabilities = np.array([.3, .7], np.float32)
    r = actor.decide(own, actual, proposed, 0, 7,
                     selector=lambda x: probabilities, innovation=.5)
    assert r['probabilities'].sum() == 1.
    assert r['probabilities'][1] == 1. - r['probabilities'][0]
    assert r['logp'] == np.log(r['probabilities'][1])
