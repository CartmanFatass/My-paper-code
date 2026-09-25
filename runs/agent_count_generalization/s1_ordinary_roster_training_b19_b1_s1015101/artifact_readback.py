"""Artifact-only B19 readback; imports no project environment, learner or reducer."""
from pathlib import Path
import argparse
import hashlib
import json
import time
import numpy as np
import torch


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def close(a, b, label, atol=1e-9):
    if not np.allclose(a, b, rtol=1e-6, atol=atol):
        raise AssertionError(label)


def describe(values, worlds):
    a = np.asarray(values, dtype=np.float64)
    return {'mean': float(a.mean()), 'per_world': a.tolist(),
            'positive': int((a > 0).sum()), 'zero': int((a == 0).sum()),
            'negative': int((a < 0).sum()),
            'minimum': {'world': int(worlds[int(a.argmin())]), 'value': float(a.min())},
            'maximum': {'world': int(worlds[int(a.argmax())]), 'value': float(a.max())}}


def main(root, report):
    started = time.perf_counter()
    batch = read(root / 'summary.json')
    result = {'source_sha': batch['launch_sha'], 'runner_status': batch['status'],
              'reader_sha256': sha(Path(__file__)), 'panels': {}, 'by_n': {}}
    panels, initial_arrays = {}, {}
    rows = sorted(root.glob('[FM]/panel_stage*_n*.json'))
    assert len(rows) == 9 and batch['status'] == 'complete', 'complete 9-panel B19 required'
    for path in rows:
        row = read(path)
        assert row['status'] == 'complete'
        n, stage, arm = row['test_n'], row['policy_stage'], path.parent.name
        key = (arm, stage, n)
        trace_path = path.parent / 'raw' / ('trace_' + path.stem[len('panel_'):] + '.npz')
        assert sha(trace_path) == row['trace']['sha256']
        assert trace_path.stat().st_size == row['trace']['bytes']
        with np.load(trace_path, allow_pickle=False) as archive:
            trace = {k: archive[k] for k in archive.files}
        for k, a in trace.items():
            assert a.dtype != object
            if np.issubdtype(a.dtype, np.number):
                assert np.isfinite(a).all(), (key, k)
        assert trace['scalar_reward'].shape == (500, 32)
        assert trace['connections'].shape == (500, 32, n, 50)
        c, e = trace['connections'].astype(bool), trace['eligible_links'].astype(bool)
        assert not (c & ~e).any()
        assert (c.sum(axis=-2) <= 1).all() and (c.sum(axis=-1) <= 10).all()
        served, eligible = c.any(axis=-2).sum(axis=-1), e.any(axis=-2).sum(axis=-1)
        unserved = eligible - served
        coverage = served / 50
        quality = trace['connected_quality_sum'] / np.maximum(served, 1)
        height_penalty = .1 * (trace['uav_heights'].mean(axis=-1) - 50) / 100
        native_j = .7 * coverage + .3 * quality - height_penalty
        for k, value in {'served_user_counts': served, 'eligible_user_counts': eligible,
                         'eligible_unserved_user_counts': unserved,
                         'coverage_reward': coverage, 'quality_reward': quality,
                         'energy_penalty': height_penalty, 'total_reward': native_j,
                         'scalar_reward': native_j / n,
                         'per_uav_eligible_counts': e.sum(axis=-1),
                         'per_uav_connection_counts': c.sum(axis=-1)}.items():
            close(trace[k], value, (key, k))
        close(trace['executed_actions'], np.clip(trace['raw_actions'], -1, 1), (key, 'clipping'), 0)
        for current, nxt in [('states', 'next_states'), ('observations', 'next_observations')]:
            assert np.array_equal(trace[current][1:], trace[nxt][:-1]), (key, current)
            assert np.array_equal(trace[current][0], trace['initial_' + current])
        if n not in initial_arrays:
            initial_arrays[n] = {k: trace[k].copy() for k in (
                'initial_states', 'initial_observations', 'initial_uav_positions', 'initial_user_positions')}
        for k, value in initial_arrays[n].items():
            assert np.array_equal(trace[k], value), (key, 'world matching', k)
        quantities = {k: a.mean(axis=0) for k, a in dict(J=native_j, C=coverage, Q=quality,
                                                       P=height_penalty, E=eligible,
                                                       S=served, U=unserved,
                                                       height=trace['uav_heights'].mean(axis=-1)).items()}
        close(row['J'], quantities['J'], (key, 'J panel'))
        close(row['scalar_returns'], trace['scalar_reward'].sum(axis=0), (key, 'scalar returns'))
        for k, name in [('C', 'coverage_reward'), ('Q', 'quality_reward'), ('P', 'energy_penalty')]:
            close(row['component_means'][name], quantities[k], (key, name))
        for k, name in [('E', 'E_eligible_users_per_step'), ('S', 'S_served_users_per_step'),
                        ('U', 'U_eligible_unserved_users_per_step')]:
            close(row['service_arrays'][name], quantities[k], (key, name))
        assert row['training_storage_calls'] == 0 and not any(row['optimizer_calls'].values())
        assert row['parameter_normalizer_digest_before'] == row['parameter_normalizer_digest_after']
        panels[key] = (row['world_seeds'], quantities)
        result['panels']['%s_%s_n%s' % key] = {
            'trace_sha256': sha(trace_path), 'trace_arrays': len(trace),
            'single_eligible_per_user': bool((e.sum(axis=-2) <= 1).all()),
            'capacity_clipping_identity': bool(np.array_equal(served, np.minimum(e.sum(axis=-1), 10).sum(axis=-1))),
            'quantities': {k: describe(a, row['world_seeds']) for k, a in quantities.items()}}
    for n in (5, 7, 6):
        worlds, initial = panels[('F', 0, n)]
        fworlds, f = panels[('F', 45, n)]
        mworlds, m = panels[('M', 45, n)]
        assert worlds == fworlds == mworlds
        values = {'F_own': {k: f[k] - initial[k] for k in initial},
                  'M_own': {k: m[k] - initial[k] for k in initial},
                  'M_minus_F': {k: m[k] - f[k] for k in initial}}
        result['by_n'][str(n)] = {'worlds': worlds}
        for label, quantities in values.items():
            result['by_n'][str(n)][label] = {k: describe(a, worlds) for k, a in quantities.items()}
            result['by_n'][str(n)][label]['adverse_J_or_S'] = [
                {'world': worlds[i], **{k: float(a[i]) for k, a in quantities.items()}}
                for i in range(32) if quantities['J'][i] <= 0 or quantities['S'][i] <= 0]
        for k, a in values['M_minus_F'].items():
            close(batch['readings']['by_test_n'][str(n)]['final_M_minus_F'][k]['per_world'], a,
                  (n, k, 'batch reducer'))
    checkpoints = {}
    for arm in ('F', 'M'):
        arm_root = root / arm
        summary = read(arm_root / 'summary.json')
        assert summary['status'] == 'complete'
        counts = summary['counts']
        assert counts['training_team_steps'] == counts['stored_team_steps'] == 360000
        assert counts['updates'] == 45 and counts['training_episodes'] == 720
        assert summary['optimizer_calls']['discoverer_actor'] == summary['optimizer_calls']['discoverer_critic'] == 101250
        assert counts['panels'] == (6 if arm == 'F' else 3)
        for checkpoint in summary['checkpoints']:
            path = arm_root / checkpoint['relative_to_arm']
            assert path.stat().st_size == checkpoint['bytes']
            assert sha(path) == checkpoint['sha256']
        assert summary['source_hashes_before'] == summary['source_hashes_after']
        stream = summary['training_stream']
        stream_path = arm_root / stream['path']
        assert stream_path.stat().st_size == stream['bytes']
        assert sha(stream_path) == stream['sha256'] and stream['completed_rows'] == 45
        curve = [json.loads(s) for s in stream_path.read_text().splitlines()]
        assert len(curve) == 45
        assert len(summary['training_reset_scenes']) == 45
        for scene_record in summary['training_reset_scenes']:
            scene_path = arm_root / scene_record['path']
            assert scene_path.stat().st_size == scene_record['bytes']
            assert sha(scene_path) == scene_record['sha256']
        schedule = [6] * 45 if arm == 'F' else [4, 6, 8] * 15
        for i, (row, n) in enumerate(zip(curve, schedule), 1):
            assert row['n'] == n and row['rollout'] == i and row['team_steps'] == 8000 * i
            assert row['optimizer_delta']['discoverer_actor'] == row['optimizer_delta']['discoverer_critic'] == n * 375
            assert row['sampler']['short_tail_batches'] == row['sampler']['dropped_time_tail_steps'] == 0
            with np.load(arm_root / 'raw' / f'training_reset_r{i:02d}_n{n}.npz', allow_pickle=False) as scene:
                assert scene['lane_world_seeds'].tolist() == [3145100 + 100 * i + lane for lane in range(16)]
                assert scene['global_rng_before'] == scene['global_rng_after']
        for stage in (0, 45):
            checkpoint_path = arm_root / 'raw' / f'checkpoint_{stage:02d}.pt'
            payload = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
            assert payload['launch_sha'] == batch['launch_sha'] and payload['rollout'] == stage
            checkpoints[(arm, stage)] = payload
        result[arm + '_counts'] = counts
    f0, m0 = checkpoints[('F', 0)], checkpoints[('M', 0)]
    assert f0['normalizers'] == m0['normalizers']
    for module, state in f0['modules'].items():
        for k, tensor in state.items():
            assert torch.equal(tensor, m0['modules'][module][k]), (module, k, 'initial mismatch')
    result['common_initial_checkpoint_tensors_equal'] = True
    for i in range(2, 46, 3):
        with np.load(root / 'F/raw' / f'training_reset_r{i:02d}_n6.npz', allow_pickle=False) as f, \
             np.load(root / 'M/raw' / f'training_reset_r{i:02d}_n6.npz', allow_pickle=False) as m:
            for k in ('lane_world_seeds', 'states', 'observations', 'uav_positions', 'user_positions'):
                assert np.array_equal(f[k], m[k]), (i, k, 'common N6 reset mismatch')
    result['common_n6_training_scenes_equal'] = 15
    assert batch['source_hashes_before'] == batch['source_hashes_after']
    assert batch['counts']['training_team_steps'] == 720000
    assert batch['counts']['evaluation_team_steps'] == 144000
    assert batch['counts']['training_uav_steps'] == 4320000
    assert batch['counts']['evaluation_uav_steps'] == 864000
    result['primary_signs'] = {f'D{n}{k}': result['by_n'][str(n)]['M_minus_F'][k]['mean'] > 0
                               for n in (5, 7) for k in ('J', 'S')}
    assert result['primary_signs'] == batch['readings']['primary_signs']
    result['wall_seconds'] = time.perf_counter() - started
    report.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'report': str(report), 'panels': len(rows), 'primary_signs': result['primary_signs'],
                      'wall_seconds': result['wall_seconds']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    main(args.root.resolve(), args.report.resolve())
