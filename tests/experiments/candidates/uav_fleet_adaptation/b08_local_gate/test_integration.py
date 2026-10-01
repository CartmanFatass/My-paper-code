"""Small synthetic, off-panel native fixtures; no production asset or world."""
from dataclasses import replace
import json

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import make_student, state_digest
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.assets import checked_path, load_parent
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.audit import audit_episode, audit_pair
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.contract import FROZEN, OBJECT
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.environment import make_real
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.read import _read_all, read_result
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.reading import _longest, episode_metrics
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.study import _execute, load_raw, run_batch


@pytest.fixture(scope='module')
def tiny(tmp_path_factory):
    root = tmp_path_factory.mktemp('b08_synthetic_complete')
    for folder in ('raw', 'data', 'assets'):
        (root / folder).mkdir()
    protocol = replace(FROZEN, training_worlds=(90811, 90812), worlds=(90813,), horizon=8,
                       training_motion_root=90821, evaluation_motion_roots=(90822, 90823),
                       training_gate_root=90824, evaluation_gate_roots=(90825, 90826),
                       bootstrap_seed=90827, constructor_seed=90828, bootstrap_resamples=31).validate()
    torch.set_num_threads(1)
    actor = make_student(90829).eval().requires_grad_(False)
    env = make_real(protocol.constructor_seed)
    env.env.max_steps = protocol.horizon
    counts = dict(optimizer_steps=0, motion_updates=0, paired_targets=0, fits_started=0, fits_completed=0,
                  constructor_calls=1, constructor_resets=1, native_dense_power_slots=275,
                  native_unique_distance_pairs=int(env.env._path_loss_cache_misses))
    batch = dict(actual=counts, inflight={}, rows=[], pairs=[], fits=[], initial_parent_state_sha256=state_digest(actor.state_dict()))
    try:
        _execute(root, actor, env, protocol, batch, lambda **kwargs: None)
    finally:
        env.close()
    return root, protocol, actor, batch


def test_complete_native_pipeline_and_one_reader_without_refit(tiny, monkeypatch):
    root, protocol, actor, batch = tiny
    report = dict(actual=dict(native_steps=0, optimizer_steps=0, refits=0), fit_audits={}, inflight={})
    def no_solve(*args, **kwargs):
        raise AssertionError('reader must never solve another ridge system')
    monkeypatch.setattr(np.linalg, 'solve', no_solve)
    result = _read_all(batch, root, actor, protocol, report, lambda value: None)
    expected = protocol.expected()
    assert len(batch['rows']) == 34 and batch['actual']['fits_completed'] == 2
    assert report['actual']['saved_native_ticks'] == 272
    assert report['actual']['scalar_states'] == 272 + 68 + 34
    assert report['actual']['refits'] == report['actual']['native_steps'] == 0
    assert len(result['levels']) == 16 and len(result['contrasts']) == 37
    assert report['actual']['policy_requests'] == expected['motion_requests']
    assert batch['label_diagnostics']['rows'] == 2
    for name in ('RAW', 'HIDDEN'):
        assert report['fit_audits'][name]['scaler_matches']


def test_boundary_old_mask_censorship_reactivation_and_hold(tiny):
    root, protocol, actor, batch = tiny
    row = next(r for r in batch['rows'] if r['id'] == 'acquisition_w90811_OFF')
    raw = load_raw(root / row['raw']['path'])
    assert raw['old_decision_mask'][0].all()
    assert not raw['installed_mask'][0, 0]
    assert not raw['old_decision_mask'][1, 0]
    assert raw['installed_mask'][1, 0]
    np.testing.assert_array_equal(raw['observations'][4, 0, 3:103], 0)
    assert raw['eligible_agent'].tolist() == [0, 1]
    assert np.any(raw['commands'][:4, 0] != 0)  # A silent member still receives held motion.
    np.testing.assert_array_equal(raw['commands'][:4], np.repeat(raw['commands'][0:1], 4, axis=0))
    assert not np.array_equal(raw['observations'][0], raw['refresh_observations'][0])
    bad = {key: value.copy() for key, value in raw.items()}
    bad['observations'][0] = bad['refresh_observations'][0]
    with pytest.raises(AssertionError, match='saved old returned observation'):
        audit_episode(bad, row, protocol, actor)


def test_complete_pair_and_scalar_tamper_detection(tiny):
    root, protocol, actor, batch = tiny
    off_row = next(r for r in batch['rows'] if r['id'] == 'acquisition_w90812_OFF')
    on_row = next(r for r in batch['rows'] if r['id'] == 'acquisition_w90812_ON')
    off, on = (load_raw(root / row['raw']['path']) for row in (off_row, on_row))
    features, label = audit_pair(off, on, off_row, on_row, protocol)
    assert label == off['reward'].mean() - on['reward'].mean()
    assert features['RAW'].shape == (125,) and features['HIDDEN'].shape == (253,)
    bad = {key: value.copy() for key, value in on.items()}
    bad['nav_pre'][0, 0] = (bad['nav_pre'][0, 0] + 1) % 10
    with pytest.raises(AssertionError, match='common forced decision nav_pre'):
        audit_pair(off, bad, off_row, on_row, protocol)
    bad = {key: value.copy() for key, value in off.items()}
    finite = np.argwhere(np.isfinite(bad['sinr'][0]))[0]
    bad['sinr'][0, finite[0], finite[1]] += .1
    with pytest.raises(AssertionError, match='radio'):
        audit_episode(bad, off_row, protocol, actor)


def test_fixed_ridge_and_episode_metadata_tamper(tiny):
    root, protocol, actor, batch = tiny
    from copy import deepcopy
    bad = deepcopy(batch)
    bad['rows'][0]['world'] += 1
    report = dict(actual=dict(native_steps=0, optimizer_steps=0, refits=0), fit_audits={}, inflight={})
    with pytest.raises(AssertionError, match='execution order'):
        _read_all(bad, root, actor, protocol, report, lambda value: None)
    bad = deepcopy(batch)
    bad['fits'][0]['sse'] += 1.
    with pytest.raises(AssertionError, match='fit complete diagnostics sse'):
        _read_all(bad, root, actor, protocol, report, lambda value: None)


def test_failed_pair_audit_preserves_both_completed_branch_costs(tiny):
    from copy import deepcopy
    from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
    root, protocol, actor, batch = tiny
    bad = deepcopy(batch)
    bad['pairs'][0]['target'] += 1.
    report = dict(actual=dict(native_steps=0, optimizer_steps=0, refits=0), fit_audits={}, inflight={})
    with pytest.raises(AssertionError, match='complete pair ledger'):
        _read_all(bad, root, actor, protocol, report, lambda value: None)
    assert report['policy_costs']['all_policy'] == sum_counts(row['policy_counts'] for row in batch['rows'][:2])
    assert report['actual']['saved_episodes'] == 2
    assert not report['inflight']


def test_masks_outages_and_per_agent_metrics(tiny):
    root, _, _, batch = tiny
    raw = load_raw(root / batch['rows'][0]['raw']['path'])
    raw['served'] = np.array([0, 0, 1, 0, 0, 0, 1, 0])
    raw['installed_mask'][:] = True
    raw['installed_mask'][0, 0] = False
    raw['installed_mask'][1, 1] = False
    raw['transmitter_mask'] = np.repeat(raw['installed_mask'], 4, axis=0)
    metrics = episode_metrics(raw)
    assert _longest([False, True, True, False, True]) == 2
    assert metrics['longest_zero_service_streak'] == 3
    assert metrics['zero_service_steps'] == 6 and metrics['zero_service_episode'] == 1
    assert metrics['mask_bit_switches'] == 3
    assert metrics['active_transmitter_ticks'] == 32
    assert metrics['uav0_mask_switches'] == 2 and metrics['uav1_mask_switches'] == 1
    assert metrics['uav0_active_ticks'] == metrics['uav1_active_ticks'] == 4


def test_production_refuses_no_admission_existing_output_and_fixture(tiny, tmp_path):
    root, protocol, _, batch = tiny
    with pytest.raises(ValueError, match='admission|accepted'):
        run_batch(tmp_path / 'not_created', 'fake', admission=None, parent_path='missing')
    assert not (tmp_path / 'not_created').exists()
    with pytest.raises(FileExistsError, match='scientific output'):
        run_batch(root, 'fake', admission={'sha': 'fake'}, parent_path='missing')
    malformed = dict(batch, state='COMPLETE', object=OBJECT, scientific_execution=True, protocol=protocol.to_dict())
    (root / 'summary.json').write_text(json.dumps(malformed))
    with pytest.raises(AssertionError, match='fixed complete production result'):
        read_result(root, root)
    with pytest.raises(FileExistsError):
        read_result(root, root)
    assert json.loads((root / 'reading.json').read_text())['actual'] == {'native_steps': 0, 'optimizer_steps': 0, 'refits': 0}


def test_input_digest_and_path_escape_refused(tmp_path):
    fake = tmp_path / 'fake.pt'
    fake.write_bytes(b'not an inherited checkpoint')
    with pytest.raises(ValueError, match='frozen artifact'):
        load_parent(fake)
    with pytest.raises(ValueError, match='escaped'):
        checked_path(tmp_path, '../escape', {'bytes': 0, 'sha256': ''})
    with pytest.raises(ValueError, match='identity'):
        checked_path(tmp_path, 'fake.pt', {'bytes': fake.stat().st_size, 'sha256': 'wrong'})
