"""Analytical stored-record validation; no native environment, result worlds or fits."""

import ast
from copy import deepcopy
import inspect

import numpy as np
import pytest

from experiments.candidates.uav_user_waiting.b02 import scheduler as frozen
from experiments.candidates.uav_user_waiting.b02 import read as previous_reader
from experiments.candidates.uav_user_waiting.b02 import study as previous_study
from experiments.candidates.uav_user_waiting.b04 import read_core as reader
from experiments.candidates.uav_user_waiting.b04 import scheduler, study
from experiments.candidates.uav_user_waiting.b04.metrics import paired_reading, forecast_changes


@pytest.fixture
def analytical_radio(monkeypatch):
    def assignment(payload):
        position, mask = payload
        connections = np.zeros((5, 50), bool)
        occupied = set()
        for member in np.flatnonzero(mask):
            first = (int(position[member, 0] + 2 * position[member, 1]) // 30) % 50
            for user in (first + np.arange(2 + int(position[member, 2]) // 30)) % 50:
                if int(user) not in occupied:
                    connections[member, user] = True
                    occupied.add(int(user))
        return connections

    def metrics(payload, connections):
        position, mask = payload
        served = int(connections.sum())
        quality = float(position[mask].mean()) / 1000 if mask.any() else 0.
        return dict(J=.7 * served / 50 + .3 * quality, served=served, quality=quality)

    def radio(position, sites, mask):
        payload = position, scheduler.p.mask_array(mask)
        contacts = assignment(payload)
        return None, contacts, metrics(payload, contacts)

    monkeypatch.setattr(frozen, 'free_space_user_path_loss', lambda position, sites: position.copy())
    monkeypatch.setattr(frozen, 'user_sinr_from_path_loss', lambda position, transmitter_mask: (position, transmitter_mask))
    monkeypatch.setattr(frozen, 'greedy_connection_assignment', assignment)
    monkeypatch.setattr(frozen, 'service_metrics', metrics)
    monkeypatch.setattr(previous_reader, 'radio', radio)
    monkeypatch.setattr(reader, 'radio', radio)


def make_record(arm='K', *, terminal=False, clock=lambda: 0.):
    positions = np.array([[100, 100, 80], [300, 200, 100], [600, 400, 120],
                          [800, 700, 90], [400, 800, 110]], float)
    own = (positions - (0, 0, 50)) / (1000, 1000, 100)
    sites = np.column_stack((np.arange(50) * 19, np.arange(50) * 17))
    commands = np.zeros((5, 3))
    actor = scheduler.Scheduler(arm, scheduler.p.encode_map(sites), clock, lambda: 0., horizon=8)
    if terminal:
        for tick in range(4):
            actor.executed(tick, commands, 7)
    record = actor.decide(own, commands, commands, 4 if terminal else 0, 7,
                          np.arange(5), started=0., cpu_started=0.)['record']
    return record, scheduler.p.decode_map(scheduler.p.encode_map(sites))


@pytest.mark.parametrize('arm', study.ARMS)
@pytest.mark.parametrize('terminal', [False, True])
def test_independent_contacts_costs_paths_and_programs(arm, terminal, analytical_radio):
    record, sites = make_record(arm, terminal=terminal)
    checked = reader.verify_stage(record['current'], sites, full_physics=True)
    result = reader.verify_program(record, checked)
    assert record['current']['length'] == (2 if terminal else 4)
    assert (result is not None) == (arm in ('U', 'K'))
    if arm == 'K':
        assert result['selected_service_margin'] >= 0


@pytest.mark.parametrize('corrupt', ['floor', 'fractional_floor', 'feasible', 'pool', 'winner', 'path', 'cost'])
def test_reader_rejects_semantic_tampering(corrupt, analytical_radio):
    record, sites = make_record()
    checked = reader.verify_stage(record['current'], sites)
    broken = deepcopy(record)
    if corrupt == 'floor':
        broken['union']['service_floor_total'] += 1
    elif corrupt == 'fractional_floor':
        broken['union']['service_floor_total'] += .25
    elif corrupt == 'feasible':
        broken['union']['feasible'][0] ^= True
    elif corrupt == 'pool':
        broken['union']['pool_pairs'] = np.roll(broken['union']['pool_pairs'], 1, axis=0)
    elif corrupt == 'winner':
        broken['union']['k_pair'] = np.array([-1, -1])
    elif corrupt == 'path':
        broken['current']['request_pairs'][0] = [26, 31]
    else:
        broken['current']['q2_cost'][0] += 1
    with pytest.raises(AssertionError):
        if corrupt == 'cost':
            reader.verify_stage(broken['current'], sites)
        else:
            reader.verify_program(broken, checked)


@pytest.mark.parametrize('boundary', ['initial', 'candidate', 'between_searches', 'ranking', 'command'])
def test_reader_accepts_retained_incomplete_or_late_calculation(boundary, analytical_radio, monkeypatch):
    time = [2. if boundary == 'initial' else 0.]
    if boundary == 'candidate':
        original = frozen.service_metrics
        def metrics(*args):
            value = original(*args)
            time[0] = 2.
            return value
        monkeypatch.setattr(frozen, 'service_metrics', metrics)
    elif boundary == 'command':
        original = scheduler.p.encode_command
        def encode(*args):
            value = original(*args)
            time[0] = 2.
            return value
        monkeypatch.setattr(scheduler.p, 'encode_command', encode)
    elif boundary in ('between_searches', 'ranking'):
        class InterruptedStage(frozen._Stage):
            def key(self, pair, label):
                value = super().key(pair, label)
                if ((boundary == 'between_searches' and label == 'W' and
                     self.record['searches']['W']['completed']) or
                    (boundary == 'ranking' and self.record['completed'])):
                    time[0] = 2.
                return value
        monkeypatch.setattr(scheduler, '_Stage', InterruptedStage)
    record, sites = make_record(clock=lambda: time[0])
    checked = reader.verify_stage(record['current'], sites) if record['current'] else None
    reader.verify_program(record, checked)
    assert not record['timely']
    assert record['union']['completed'] == (boundary == 'command')


def test_collector_and_storage_preserve_frozen_delayed_loop():
    for name in ('collect_episode', 'save_episode'):
        actual = ast.dump(ast.parse(inspect.getsource(getattr(study, name))))
        previous = ast.dump(ast.parse(inspect.getsource(getattr(previous_study, name))))
        assert actual == previous
    for arm in study.ARMS:
        assert all(sum(order[index] == arm for order in study.ARM_ORDERS) == 2 for index in range(4))
    assert study.SEED == 29426000 and study.FIXTURE_SEED == 29426999
    assert len(study.frozen_config('0' * 40)['source_identities']) > 30


def test_mean_joint_signs_do_not_hide_adverse_worlds_or_turn_into_adoption_rule():
    from experiments.candidates.uav_user_waiting.b04.metrics import OUTCOME_METRICS, EXTRA_METRICS
    rows = []
    for seed in (10, 11):
        for arm in study.ARMS:
            row = dict.fromkeys(OUTCOME_METRICS + EXTRA_METRICS, 0.)
            row.update(arm=arm, seed=seed)
            if arm == 'K':
                row.update(mean_served=1. if seed == 10 else -1., max_unserved_gap=-1., F_user=-2.)
            rows.append(row)
    paired = paired_reading(rows, [10, 11])
    assert paired['mean_signs'] == dict(service=True, maximum_gap=True, worst_mean_age=True)
    assert paired['joint_favorable_worlds'] == 1 and paired['joint_world_vector'] == [True, False]
    assert paired['contrasts']['K-M']['mean_served']['values'] == [1., -1.]
    assert set(paired['contrasts']) == {'S-M', 'U-M', 'U-S', 'K-M', 'K-S', 'K-U'}
    assert paired['bootstrap']['seed'] == 29426998 and paired['bootstrap']['resamples'] == 10000


def test_clipped_command_change_is_not_counted_as_changed_motion_forecast():
    position = np.array([[1000., 1000., 150.]] * 5)
    assert not forecast_changes(position, np.zeros((5, 3)), np.ones((5, 3)), 4)
    assert forecast_changes(position, np.zeros((5, 3)), -np.ones((5, 3)), 2)
