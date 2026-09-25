import copy
import json
import os
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.uav_service_auxiliary.b10 import native
from experiments.candidates.uav_service_auxiliary.b01.native import seed_everything
from hmasd.agent import HMASDAgent
from scripts import run_uav_service_auxiliary_b10 as entry

SOURCE = Path(os.environ.get('HMASD_B10_SOURCE_ROOT',
    '/home/fires/hmasd-artifacts/uav_service_auxiliary/b09_an_925031_a01'))


def test_source_binding_and_saved_config():
    config, evaluation, summary = native.verify_source(SOURCE)
    assert summary['launch_sha'] == native.SOURCE_SHA
    assert config.num_envs == 2 and evaluation.num_envs == 1
    assert config.max_steps == evaluation.max_steps == 3000
    assert config.episode_length == evaluation.episode_length == 3000
    assert tuple(native.WORLD_SEEDS) == tuple(range(953001, 953033))
    with pytest.raises(ValueError, match='digest mismatch'):
        native.verify_source(SOURCE / 'missing')


def test_admission_precedes_scientific_imports_or_output(tmp_path, monkeypatch):
    from scripts import hmasd_admission
    target = tmp_path / 'not-created'
    def reject(*args, **kwargs):
        raise RuntimeError('admission rejected')
    monkeypatch.setattr(hmasd_admission, 'require_admission', reject)
    with pytest.raises(RuntimeError, match='admission rejected'):
        entry.main(['--source-root', str(SOURCE), '--out', str(target), '--launch-sha', 'fixture'])
    assert not target.exists()


def test_prefix_uses_allocation_membership_and_checks_F_after_common_overrides(tmp_path):
    def snap(selected):
        return {'prior_actual_station': [-1, -1], 'current_target_station': [0, 0],
                'battery_after_consumption': [.2, .3], 'wait_age_before_selection': [0, 0],
                'eligible_by_station': {'0': [0, 1]}, 'original_selected': {'0': [0, 1]},
                'actual_selected': {'0': selected}}
    old = [snap([0, 1]), snap([0])]
    new = [snap([1, 0]), snap([1])]
    old[1]['original_selected'] = {'0': [0]}
    new[1]['original_selected'] = {'0': [0]}
    fields = ('native_reward', 'metrics', 'ends', 'actions', 'physical_post_battery',
              'charger_input_wh', 'mode', 'entry', 'exit', 'pre_position_m', 'post_position_m',
              'original_action', 'submitted_action', 'mode_before', 'pre_legal_battery',
              'agent_skills', 'team_skills')
    arrays = {field: np.zeros((2, 2), dtype=np.float64) for field in fields}
    arrays['mode'][0, 0] = 1  # Earlier identical F decision is allowed.
    left, right = tmp_path / 'o.npz', tmp_path / 'c.npz'
    np.savez_compressed(left, **arrays)
    np.savez_compressed(right, **arrays)
    result = native.verify_prefix(left, right, old, new)
    assert result['first_differing_allocation_tick'] == 1
    assert result['verified_complete_transition_prefix_steps'] == 1
    changed = copy.deepcopy(arrays)
    changed['metrics'][0, 0] = 1
    np.savez_compressed(right, **changed)
    with pytest.raises(RuntimeError, match='prefix'):
        native.verify_prefix(left, right, old, new)


@pytest.mark.parametrize('device_name', [
    'cpu', pytest.param('cuda', marks=pytest.mark.skipif(not torch.cuda.is_available(), reason='CUDA unavailable')),
])
def test_tiny_native_closed_loops_preserve_policy_and_write_raw(tmp_path, device_name):
    saved, evaluation, _ = native.verify_source(SOURCE)
    tiny = copy.deepcopy(evaluation)
    tiny.episode_length = tiny.max_steps = 3
    tiny.calculate_and_set_buffer_sizes()
    out = tmp_path / 'b10-fixture'
    out.mkdir()
    (out / 'launch-manifest.json').write_text('{}')
    result = native.run_native(source_root=SOURCE, out=out, launch_sha='fixture',
                               device_name=device_name, threads=4,
                               _fixture_seeds=(7,), _fixture_config=tiny)
    assert result['status'] == 'COMPLETE'
    assert result['counts']['fits'] == result['counts']['training_transitions'] == result['counts']['optimizer_updates'] == 0
    assert result['counts']['episode_attempts'] == result['counts']['completed_episodes'] == 2
    assert result['counts']['evaluation_transitions'] <= 6
    assert result['torch_threads'] == 4 and result['tf32_disabled']
    assert len(result['prefixes']) == 1
    assert result['panels']['O']['learner_state_immutable']
    assert result['panels']['C']['learner_state_immutable']
    for rule in ('O', 'C'):
        world = result['panels'][rule]['worlds'][0]
        assert (out / world['raw_npz']).is_file()
        assert (out / world['raw_detail']).is_file()
        assert world['raw_sha256'][world['raw_npz']] == native.sha256_file(out / world['raw_npz'])
    assert json.loads((out / 'summary.json').read_text())['status'] == 'COMPLETE'


def test_postprocessing_failure_retains_completed_physical_reward_trace(tmp_path, monkeypatch):
    _, evaluation, _ = native.verify_source(SOURCE)
    tiny = copy.deepcopy(evaluation)
    tiny.episode_length = tiny.max_steps = 3
    tiny.calculate_and_set_buffer_sizes()
    seed_everything(7, torch.device('cpu'))
    evaluator = HMASDAgent(tiny, log_dir=str(tmp_path / 'agent'), device=torch.device('cpu'))
    evaluator.train(False)
    def fail(*args, **kwargs):
        raise RuntimeError('injected postprocessing failure')
    monkeypatch.setattr(native, 'station_intervals', fail)
    with pytest.raises(RuntimeError, match='injected postprocessing failure'):
        native.evaluate_one(evaluator, tiny, 7, 'O', out=tmp_path)
    trace = tmp_path / 'raw' / 'O_7.npz'
    assert trace.is_file()
    with np.load(trace, allow_pickle=False) as data:
        assert len(data['native_reward']) > 0
        assert len(data['native_reward']) == len(data['physical_post_battery'])
        assert len(data['native_reward']) == len(data['station_prior_actual'])
    assert (tmp_path / 'raw' / 'O_7_partial_station.json.gz').is_file()
