"""Hand-built saved records and analytical outcomes; zero native episodes/fits."""

from collections import Counter
from copy import deepcopy

import numpy as np
import pytest

from experiments.candidates.uav_user_waiting.b02 import protocol as wire
from experiments.candidates.uav_user_waiting.b02.study import allocate_raw, record_round
from experiments.candidates.uav_user_waiting.b02.storage import pack_records, unpack_records
from experiments.candidates.uav_user_waiting.b05 import protocol as fair
from experiments.candidates.uav_user_waiting.b05.reader import compare_tree
from experiments.candidates.uav_user_waiting.b06.collect import augment_model_raw, PairCheckedEnvironment
from experiments.candidates.uav_user_waiting.b06.scheduler import Scheduler
from experiments.candidates.uav_user_waiting.b06.read_model import verify_decisions, verify_stage, reference_grants
from experiments.candidates.uav_user_waiting.b06.outcomes import replay_lrs, compact_row, physical_comparison
from experiments.candidates.uav_user_waiting.b06.read_outcomes import verify_lrs, reference_physical, reference_paired
from experiments.candidates.uav_user_waiting.b06.metrics import paired_reading
from experiments.candidates.uav_user_waiting.b06.read_native import c_act
from experiments.candidates.uav_user_waiting.b06 import protocol as p


def saved_model():
    position = np.array([[100, 100, 80], [300, 200, 100], [600, 400, 120],
                         [800, 700, 90], [400, 800, 110]], float)
    sites = np.column_stack((np.arange(50) * 19, np.arange(50) * 17))
    packet, actual = wire.encode_map(sites), np.zeros((5, 3), np.float32)
    proposals, nav = actual.copy(), np.arange(5, dtype=np.uint8)
    actor = Scheduler('S', packet, lambda: 0., lambda: 0., horizon=8)
    raw, records = allocate_raw(8, 'S', sites, packet), []
    raw['positions'][0] = position
    mask = 31
    for tick in range(8):
        raw['commands'][tick], raw['proposals'][tick], raw['mask'][tick] = actual, proposals, mask
        raw['observations'][tick, :, :3] = (position - wire.LOW) / (wire.HIGH - wire.LOW)
        if tick % 4 == 0:
            raw['post_c_nav'][tick // 4] = nav
            pending = actor.decide(raw['observations'][tick, :, :3], actual, proposals, tick, mask, nav)
            records.append(pending['record'])
            record_round(raw, pending, tick)
        position = np.clip(position + 30 * actual, wire.LOW, wire.HIGH)
        raw['positions'][tick + 1] = position
        actor.executed(tick, actual, mask)
        if tick % 4 == 1:
            actual, mask = pending['commands'].copy(), pending['mask']
    before = actor.execution.next_unsettled
    actor.execution.settle(8)
    raw.update(completed_steps=np.array(8), model_valid=np.ones(8, bool),
        model_contacts=np.array([actor.execution.predicted[tick] for tick in range(8)]),
        terminal_history_reductions=np.array(8 - before), terminal_history_start=np.array(0),
        terminal_history_complete=np.array(True), terminal_burden_unknown=np.array(False),
        terminal_last=actor.execution.history.last.copy(), terminal_windows=actor.execution.history.windows.copy(),
        terminal_burden=actor.execution.history.burden.copy())
    raw.update(pack_records(records))
    augment_model_raw(raw, actor, dict(sha256='a' * 64, bytes=1))
    return raw


@pytest.fixture(scope='module')
def model_raw():
    return saved_model()


def test_complete_settlement_private_state_and_tail_reader(model_raw):
    counts = Counter()
    checked = verify_decisions(model_raw, counts)
    assert checked['verified_model_transitions'] == 8
    assert counts['modeled_physics_attempts'] == counts['modeled_physics_completed']
    records = unpack_records(model_raw)
    assert records[-1]['current']['length'] == 2
    assert records[-1]['history_after'] == 4
    assert int(model_raw['terminal_last_grant'].max()) == 7


@pytest.mark.parametrize('corrupt', ['local_state', 'grant', 'key', 'path', 'terminal', 'wrong_native_tie'])
def test_reader_rejects_causal_priority_key_and_path_corruption(model_raw, corrupt):
    raw = {key: value.copy() for key, value in model_raw.items()}
    records = unpack_records(raw)
    stage = records[0]['current']
    if corrupt == 'local_state':
        records[1]['history_last_grant'][0, 0] += 1
    elif corrupt == 'grant':
        # Corrupt the independently checked winner's local identities.
        pair = tuple(records[0]['requested_pair'])
        index = [tuple(value) for value in stage['evaluated_pairs']].index(pair)
        stage['candidate_grants'][index, 0, 0, 0] = 49
    elif corrupt == 'key':
        stage['keys']['S'][0, 0] += 1
    elif corrupt == 'path':
        stage['request_pairs'][0] = (26, 1)
    elif corrupt == 'terminal':
        raw['terminal_last_grant'][0, 0] += 1
    else:
        stage['native'][0, 2] += .1
    raw.update(pack_records(records))
    with pytest.raises((AssertionError, ValueError, IndexError)):
        verify_decisions(raw, Counter())


def test_reference_uses_own_uav_history_and_exact_sinr_id_ties():
    values = np.full((5, 50), -10.)
    values[0, :12] = 8.
    own = np.full((5, 50), -1, np.int64)
    own[0, 0] = 100
    own[1, 1] = 200  # Another UAV's timestamp may not make user1 recent locally.
    before = own.copy()
    grants = reference_grants(values, own)
    np.testing.assert_array_equal(grants[0], np.arange(1, 11))
    np.testing.assert_array_equal(own, before)
    values[0, 11] = 9.
    assert reference_grants(values, own)[0, 0] == 11


def analytical_outcomes():
    steps = 8
    values = np.full((steps, 5, 50), -20., np.float64)
    values[:, 0, :12] = 10.
    values[3:6, 0, 11] = -20.  # Mixed denial/no-link intervals and a censored user.
    greedy = np.zeros_like(values, bool)
    greedy[:, 0, :10] = True
    native_quality = 7. / 30.
    raw = dict(completed_steps=np.array(steps), commands=np.zeros((steps, 5, 3)), sinr=values,
               mask=np.full(steps, 31), connections=greedy, served=np.full(steps, 10),
               quality=np.full(steps, native_quality), reward=np.full(steps, .14 + .3 * native_quality))
    collector = dict(arm='S', seed=17, **{key: 0. for key in fair.INHERITED_METRICS})
    full, arrays, _ = replay_lrs(raw, collector, Counter())
    raw.update(arrays)
    return raw, collector, full, compact_row(full)


def test_complete_lrs_censored_gaps_and_signed_paired_uncertainty():
    raw, collector, full, compact = analytical_outcomes()
    checked = verify_lrs(raw, full, compact, collector, Counter(), {})
    assert checked['max_unserved_gap'] == 8
    assert checked['per_user'][49]['gaps'] == [[0, 8, 1, 1, 0, 8]]
    assert checked['changed_grant_user_ticks'] > 0
    rows, baselines = [], {}
    for seed, effect in ((1, -3), (2, 5)):
        row = deepcopy(compact)
        row.update(seed=seed, max_unserved_gap=8 + effect)
        rows.append(row)
        for package in p.REFERENCES:
            base = deepcopy(compact)
            base.update(seed=seed, package=package, program=package.split(':')[0])
            baselines[package, seed] = base
    produced = paired_reading(rows, baselines, seeds=(1, 2))
    checked = reference_paired(rows, baselines, seeds=(1, 2))
    compare_tree(produced, checked, 'paired', {})
    assert produced['primary']['mean_difference'] == 1.
    assert produced['primary']['favorable_worlds'] == produced['primary']['adverse_worlds'] == 1
    assert produced['contrasts']['S_F:LRS-S:LRS']['max_unserved_gap']['values'] == [-3., 5.]


@pytest.mark.parametrize('field', ['grant', 'gap_partition', 'censor', 'vector', 'quality'])
def test_native_lrs_output_corruption_rejected(field):
    raw, collector, full, compact = analytical_outcomes()
    if field == 'grant':
        raw['lrs_grants'][0, 0, 49] = True
    elif field == 'gap_partition':
        full['per_user'][49]['gaps'][0][-1] -= 1
    elif field == 'censor':
        full['per_user'][49]['gaps'][0][2] = 0
    elif field == 'vector':
        compact['per_user_vectors']['mean_age'][49] += 1
    else:
        raw['lrs_quality'][0] += 1e-5
    with pytest.raises((AssertionError, ValueError)):
        verify_lrs(raw, full, compact, collector, Counter(), {})


def test_mask_only_change_activates_and_pairing_precedes_policy_query():
    old = dict(positions=np.zeros((9, 5, 3)), observations=np.zeros((9, 5, 104)),
               commands=np.zeros((8, 5, 3)), mask=np.full(8, 31),
               map_packet=np.zeros(400, np.uint8), true_sites=np.zeros((50, 2)))
    new = deepcopy(old)
    new['mask'][2:] = 1
    actual = physical_comparison(new, old)
    assert actual == reference_physical(new, old)
    assert actual['activated'] and actual['first_executed_command_or_mask_tick'] == 2
    assert actual['first_position_tick'] is None
    class Fake:
        def reset(self, *, seed):
            return old['observations'][0], dict(state_info=dict(uav_positions=np.ones((5, 3)),
                                                                user_positions=old['true_sites']))
    counts = Counter()
    with pytest.raises(ValueError, match='reset pairing'):
        PairCheckedEnvironment(Fake(), old, counts).reset(seed=17)
    assert counts['reset_calls_attempted'] == 1 and counts['paired_resets_verified'] == 0


def test_reader_failed_c_keeps_attempt_and_actual_inner_work():
    class Broken:
        counters = dict(paths=0, model_ticks=0)
        def act(self, observation, tick):
            self.counters['paths'] += 3
            self.counters['model_ticks'] += 4
            raise ArithmeticError('synthetic')
    counts = Counter()
    with pytest.raises(ArithmeticError):
        c_act(Broken(), None, 0, counts)
    assert counts['reader_current_c_calls_attempted'] == 1
    assert counts['reader_current_c_calls'] == 0
    assert counts['reader_c_paths'] == 3 and counts['reader_c_model_ticks'] == 4
