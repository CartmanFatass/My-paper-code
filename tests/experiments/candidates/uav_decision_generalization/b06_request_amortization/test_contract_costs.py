"""Pure static arithmetic and temporary-file budget checks; no scientific host."""
import os
import pytest

from experiments.candidates.uav_decision_generalization.b06_request_amortization import contract as c
from experiments.candidates.uav_decision_generalization.b06_request_amortization.costs import (
    BudgetExceeded, Meter, allocated_inventory,
)


def test_complete_purchase_arithmetic_and_rotation():
    rows = c.expected_roster()
    assert len(rows) == len(set(rows)) == 224
    assert rows[:7] == [(109255000, 'main/' + arm) for arm in c.ARMS]
    assert rows[7:14] == [(109255001, 'main/' + arm) for arm in c.ARMS[1:] + c.ARMS[:1]]
    spec = c.frozen_contract()
    ticks = tuple(range(0, 1200, 20))
    r4 = sum(4 * (4 if t < 940 else 1) * min(160, 1200 - t) for t in ticks)
    r1 = sum(4 * min(160, 1200 - t) for t in ticks)
    assert 32 * (r4 + r1) == spec['worker_r_model_steps_max'] == 5201920
    assert spec['worker_missions'] * 1200 == spec['worker_native_steps']
    assert spec['worker_missions'] * (404 + 61 * 171 + 60 * 6) == spec['logical_task_bytes']
    assert 3 * 64 * 2100 * 4 + 6 * 2100 * 4 + 3 * 32 * 60 * 4 == spec['worker_neural_rows_max']
    assert 6 * 2100 * 4 + 3 * 32 * 60 * 4 == spec['reader_neural_rows_max']
    assert spec['worker_neural_rows_max'] + spec['reader_neural_rows_max'] == 1759680
    assert 269024 + 3840 + 5201920 == spec['reader_total_physical_states_max']
    assert c.rng_domain('R', 109255000, 0, 0) == (109259999, 30, 109255000, 0, 0)
    assert c.rng_domain('shuffle', 2) == (109259999, 51, 2)
    with pytest.raises(ValueError):
        c.rng_domain('exploration', 0)


def test_disk_is_allocated_inode_union_without_following_links(tmp_path):
    owned = tmp_path / 'owned'
    owned.mkdir()
    data = owned / 'data'
    data.write_bytes(b'x' * 10000)
    os.link(data, owned / 'second-name')
    external = tmp_path / 'not-owned'
    external.mkdir()
    (external / 'untouched').write_bytes(b'y' * 100000)
    link = owned / 'external-link'
    link.symlink_to(external, target_is_directory=True)
    actual = allocated_inventory([owned, data, owned])
    expected = sum(p.lstat().st_blocks * 512 for p in (owned, data, link))
    assert actual['allocated_bytes'] == expected
    assert actual['unique_inodes'] == 3
    assert actual['roots'][1]['allocated_bytes'] == 0
    assert (external / 'untouched').read_bytes() == b'y' * 100000


def test_stop_reserve_cannot_buy_another_effect(tmp_path, monkeypatch):
    prior = {'cumulative_cpu_seconds': 0, 'aggregate_operation_wall_seconds': 0}
    meter = Meter(prior, 0., disk_roots=[tmp_path])
    monkeypatch.setattr(meter, 'report', lambda: {
        'cumulative_cpu_seconds': c.CPU_STOP_SECONDS,
        'aggregate_operation_wall_seconds': 1.,
    })
    with pytest.raises(BudgetExceeded, match='science stop'):
        meter.reserve('test_effect')
    assert meter.finalizing and meter.counts == {}
    with pytest.raises(BudgetExceeded, match='finalization'):
        meter.check()
    assert c.CPU_LIMIT_SECONDS - c.CPU_STOP_SECONDS == 1800
    assert c.WALL_LIMIT_SECONDS - c.WALL_STOP_SECONDS == 3600


def test_disk_normal_and_finalization_scopes_are_distinct(tmp_path, monkeypatch):
    meter = Meter({'cumulative_cpu_seconds': 0, 'aggregate_operation_wall_seconds': 0},
                  0., disk_roots=[tmp_path])
    measured = meter.check_disk()['allocated_bytes']
    monkeypatch.setattr(c, 'DISK_STOP_BYTES', measured + 100)
    monkeypatch.setattr(c, 'DISK_LIMIT_BYTES', measured + 200)
    assert meter.check_disk(anticipated_bytes=100)['allocated_bytes'] == measured
    with pytest.raises(BudgetExceeded):
        meter.check_disk(anticipated_bytes=101)
    assert meter.finalizing
    assert meter.check_disk(anticipated_bytes=200, finalization=True)['allocated_bytes'] == measured
    with pytest.raises(BudgetExceeded):
        meter.check_disk(anticipated_bytes=201, finalization=True)


def test_reader_new_actual_scope_and_attempt_bound(tmp_path):
    meter = Meter({'cumulative_cpu_seconds': 0, 'aggregate_operation_wall_seconds': 0},
                  0., disk_roots=[tmp_path])
    meter.add('reader_native_physical_attempts', 269024)
    with pytest.raises(RuntimeError, match='exposure ceiling'):
        meter.add('reader_native_physical_attempts')
    assert meter.counts['reader_native_physical_attempts'] == 269025


def test_acquisition_phase_caps_and_reader_aggregate_do_not_double_count(tmp_path):
    meter = Meter({'cumulative_cpu_seconds': 0, 'aggregate_operation_wall_seconds': 0},
                  0., disk_roots=[tmp_path])
    meter.add('b06_fit0_forward_attempted_rows', 256)
    meter.add('b06_fit0_initial_bank_forward_attempted_rows', 256)
    assert meter.counts['worker_acquisition_neural_attempted_rows'] == 512
    meter.add('b06_reader_fit0_initial_bank_forward_attempted_rows', 256)
    assert 'reader_neural_attempted_rows' not in meter.counts
    meter.add('reader_neural_attempted_rows', 256)
    assert meter.counts['reader_neural_attempted_rows'] == 256
    meter.add('b06_constant_acquisition_solve_attempts')
    with pytest.raises(RuntimeError, match='exposure ceiling'):
        meter.add('b06_constant_acquisition_solve_attempts')
