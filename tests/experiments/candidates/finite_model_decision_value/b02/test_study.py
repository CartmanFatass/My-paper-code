"""Small fixtures for B02's five-arm accounting and durable evidence."""

from dataclasses import replace
import hashlib
import json

import numpy as np
import pytest

from experiments.candidates.finite_model_decision_value.b01.study import THETAS, calibration_posterior
from experiments.candidates.finite_model_decision_value.b02 import study


def _tiny():
    return study.Config(seed=815, model_seed=819, calibration_phase=24,
        evaluation_phase=25, model_phase=26, contexts=2, batch=1,
        horizon=48, particles_low=2, particles_high=4)


def test_explicit_arm_dispatch_and_four_move_calibration():
    default = study.arm_specs(study.Config())
    assert [arm.name for arm in default] == [
        'P_k4_M32', 'U_k4_M32', 'P_k4_M256', 'U_k4_M256', 'AF']
    assert [(arm.mode, arm.calibration_k, arm.particles) for arm in default] == [
        ('POSTERIOR_MEAN', 4, 32), ('JOINT', 4, 32),
        ('POSTERIOR_MEAN', 4, 256), ('JOINT', 4, 256), (None, None, 0)]
    config = _tiny()
    theta, positions = study.collect_calibration(config, [17, 23])
    assert positions.shape == (2, 5)
    assert set(theta).issubset(set(THETAS))
    assert np.all(np.isin(np.diff(positions), [-1, 0]))
    q, successes = calibration_posterior(positions, 4)
    for row in range(2):
        n = int(successes[row])
        expected = THETAS ** n * (1 - THETAS) ** (4 - n)
        np.testing.assert_allclose(q[row], expected / expected.sum(), atol=1e-15)
    with pytest.raises(ValueError):
        study.collect_calibration(replace(config, calibration_steps=32), [17])


def test_primary_interaction_and_native_adverse_components_are_paired():
    config = _tiny()
    arms = [arm.name for arm in study.arm_specs(config)]
    # Rows are context 0, 1. Distinct own-budget changes make I nontrivial.
    completed = {arms[0]: [11, 9], arms[1]: [13, 9],
                 arms[2]: [12, 10], arms[3]: [11, 12], 'AF': [10, 10]}
    episodes = []
    for arm in arms:
        for context in range(2):
            episodes.append(dict(arm=arm, context=context, theta=float(THETAS[context]),
                completed_jobs=completed[arm][context], service=completed[arm][context]/14,
                conflicts=2+context+(arm == arms[3]), wait_ticks=4+context+(arm == arms[1]),
                packets=12))
    roots = [dict(context=i, nested_prefix_verified=True,
                  low=dict(p_send=False, u_send=bool(i)),
                  high=dict(p_send=True, u_send=bool(i))) for i in range(2)]
    result = study.summarize(episodes, roots, config)
    assert result['primary_interaction'] == f'I=({arms[3]}-{arms[2]})-({arms[1]}-{arms[0]})'
    assert [row['contrasts']['I']['completed_jobs'] for row in result['per_context']] == [-3, 2]
    assert result['contrasts']['I']['completed_jobs']['mean'] == -.5
    assert result['contrasts'][f'{arms[1]}-{arms[0]}']['completed_jobs']['mean'] == 1
    assert result['contrasts'][f'{arms[3]}-{arms[2]}']['completed_jobs']['mean'] == .5
    assert result['contrasts'][f'{arms[3]}-{arms[1]}']['completed_jobs']['mean'] == .5
    assert result['contrasts'][f'{arms[2]}-{arms[0]}']['completed_jobs']['mean'] == 1
    assert result['contrasts'][f'{arms[1]}-AF']['wait_ticks']['mean'] == 1
    assert result['contrasts'][f'{arms[3]}-AF']['conflicts']['mean'] == 1
    with pytest.raises(ValueError, match='five complete'):
        study.summarize(episodes[:-1], roots, config)
    with pytest.raises(ValueError, match='five complete'):
        study.summarize([row for row in episodes if row['context'] == 0], roots[:1], config)
    with pytest.raises(ValueError, match='five complete'):
        study.summarize(episodes + [dict(episodes[0], arm='KNOW_P_NEAR')], roots, config)


def test_full_tiny_fixture_has_five_complete_arms_nested_roots_and_hashes(tmp_path):
    out = tmp_path / 'run'
    out.mkdir()
    (out / 'stdout.log').write_text('native supervisor placeholder')
    (out / 'launch-manifest.json').write_text('{}')
    config = _tiny()
    summary = study.run_study(out, 'fixture-sha', config)
    assert summary['state'] == 'COMPLETE'
    assert summary['config']['launch_sha'] == 'fixture-sha'
    assert [arm['name'] for arm in summary['config']['arms']] == [
        'P_k4_M2', 'U_k4_M2', 'P_k4_M4', 'U_k4_M4', 'AF']
    assert summary['counts']['calibration_steps'] == 8
    assert summary['counts']['calibration_fits_completed'] == 2
    assert summary['counts']['evaluation_episodes'] == 10
    assert summary['counts']['evaluation_team_ticks'] == 10 * 48
    assert summary['counts']['model_branch_transitions'] <= summary['counts']['model_branch_transition_upper']
    assert summary['counts']['model_root_particles'] * 2 == summary['counts']['model_initialization_worlds']
    assert summary['initial_root']['nested_prefix_verified']
    assert len(json.loads((out / 'per_context.json').read_text())) == 2
    assert len(json.loads((out / 'initial_roots.json').read_text())) == 2
    with np.load(out / 'raw' / 'calibration.npz') as calibration:
        assert calibration['positions'].shape == (2, 5)
        assert calibration['q4'].shape == (2, 4)
        assert 'q32' not in calibration.files
    assert len(list((out / 'raw').glob('*.npz'))) == 11  # calibration + five arms x two batches
    assert len(list((out / 'raw').glob('*.cost.json'))) == 10
    for artifact in summary['artifacts']:
        path = out / artifact['path']
        assert path.stat().st_size == artifact['bytes']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact['sha256']
    assert 'stdout.log' not in [artifact['path'] for artifact in summary['artifacts']]
    assert 'launch-manifest.json' not in [artifact['path'] for artifact in summary['artifacts']]
    assert (out / 'stdout.log').read_text() == 'native supervisor placeholder'
    with pytest.raises(FileExistsError):
        study.run_study(out, 'fixture-sha', config)


def test_failure_retains_current_batch_cost_and_partial_work(tmp_path, monkeypatch):
    original = study.evaluate_batch
    calls = 0

    def interrupted(config, ids, theta, q, arm, raw_path):
        nonlocal calls
        calls += 1
        if calls == 2:
            np.savez_compressed(raw_path, completed_steps=np.array(1))
            study.write_json(raw_path.with_suffix('.cost.json'), dict(
                state='FAILED', arm=arm, steps=len(ids), model=dict(model_branch_transitions=2)))
            raise RuntimeError('fixture interruption')
        return original(config, ids, theta, q, arm, raw_path)

    monkeypatch.setattr(study, 'evaluate_batch', interrupted)
    out = tmp_path / 'failed'
    with pytest.raises(RuntimeError, match='fixture interruption'):
        study.run_study(out, 'fixture-sha', _tiny())
    summary = json.loads((out / 'summary.json').read_text())
    assert summary['state'] == 'FAILED'
    assert summary['status']['completed_arm_contexts'] == 1
    assert len(summary['batch_costs']) == 2
    assert summary['batch_costs'][1]['state'] == 'FAILED'
    assert (out / 'raw' / 'U_k4_M2_0000_0001.cost.json').exists()
    assert len(json.loads((out / 'episodes.json').read_text())) == 1
    assert all((out / item['path']).exists() for item in summary['artifacts'])
