"""Arithmetic readback of B08; no learner, fitting, solve, simulator or new policy input."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

root = Path(sys.argv[1])
input_root = root.parent / 'b07_own_collection_exploration'
launch_sha = sys.argv[2]
summary = json.loads((root / 'summary.json').read_text())
assert summary['status'] == 'COMPLETE'
assert summary['launch_sha'] == launch_sha
assert summary['started_decision_fits'] == summary['completed_decision_fits'] == 6
assert summary['seeds'] == [95301, 95302, 95303]
assert all(a['status'] == 'COMPLETE' and a['saved'] for a in summary['fit_attempts'])
assert summary['total_source_state_restore_events'] == 12


def close(a, b, atol=2e-12):
    np.testing.assert_allclose(a, b, atol=atol, rtol=2e-12)


def load(path):
    with np.load(path, allow_pickle=False) as data:
        result = {key: data[key] for key in data.files}
    assert all(value.dtype != object for value in result.values())
    return result


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def before(values):
    return np.r_[0, np.cumsum(values)[:-1]]


for relative, digest in json.loads((root / 'artifacts.json').read_text()).items():
    assert sha(root / relative) == digest
science_digest_count = len(json.loads((root / 'artifacts.json').read_text()))
manifest = json.loads((root / 'input-manifest.json').read_text())
assert manifest['evidence_commit'] == '6ab8db786a2dc2397d883e8476ccb0303b059f0e'
assert manifest['scientific_source'] == '03d3633bd55b4095d7b195ad5ecd3f44eb3c864a'
assert sha(input_root / 'summary.json') == manifest['root_summary_sha256']
input_digest_count = 1
blocks = []
counts = {}
endpoints = {'first64': slice(0, 64), 'full': slice(0, 256), 'late64': slice(192, 256)}
donor_keys = ('macro_index', 'version', 'context', 'estimated_law', 'collection_action', 'outcome', 'reward', 'exact_values')
comparisons = {
    'R_minus_F_on_R_history': ('R_on_R', 'F_on_R'),
    'R_minus_F_on_F_history': ('R_on_F', 'F_on_F'),
    'R_history_minus_F_history_for_R': ('R_on_R', 'R_on_F'),
    'R_history_minus_F_history_for_F': ('F_on_R', 'F_on_F'),
}
for seed in summary['seeds']:
    block, old = root / f'seed_{seed}', input_root / f'seed_{seed}'
    for relative, digest in manifest['seeds'][str(seed)]['verified_required_artifacts'].items():
        assert sha(old / relative) == digest
        input_digest_count += 1
    for relative, digest in json.loads((block / 'artifacts.json').read_text()).items():
        assert sha(block / relative) == digest
    old_t = {name: load(old / name / 'trajectory.npz') for name in ('R_E', 'F_E')}
    old_s = {name: load(old / name / 'state.npz') for name in ('R_E', 'F_E')}
    panels = {name + '_on_' + name: {k: v[2048:] for k, v in old_t[name + '_E'].items()} for name in ('R', 'F')}
    reused = load(block / 'reused_diagonals.npz')
    for name in ('R', 'F'):
        for key in ('context', 'matched_epsilon_expected_return'):
            np.testing.assert_array_equal(reused[name + '_on_' + name + '_' + key], panels[name + '_on_' + name][key])
    for name, recipient, donor, panel_id in (
        ('R_on_F_E_history', 'R_E', 'F_E', 'R_on_F'),
        ('F_on_R_E_history', 'F_E', 'R_E', 'F_on_R'),
    ):
        path = block / name
        t, state = load(path / 'trajectory.npz'), load(path / 'state.npz')
        reported = json.loads((path / 'summary.json').read_text())
        assert reported['seed'] == seed and reported['launch_sha'] == launch_sha
        assert reported['donor_branch'] == donor and reported['recipient_branch'] == recipient
        for key in donor_keys:
            np.testing.assert_array_equal(t[key], old_t[donor][key][2048:])
        for key in old_s[recipient]:
            if key.startswith('source_decision_'):
                np.testing.assert_array_equal(state[key], old_s[recipient][key])
        np.testing.assert_array_equal(t['raw_predictions'][0], old_t[recipient]['raw_predictions'][2048])
        for key in ('fidelity_expected_first_raw_prediction', 'fidelity_actual_first_raw_prediction'):
            np.testing.assert_array_equal(state[key], t['raw_predictions'][0])
        np.testing.assert_array_equal(state['fidelity_donor_first_estimated_law'], t['estimated_law'][0])
        np.testing.assert_array_equal(t['decision_updates_before'], np.arange(2048, 2304))
        coop = t['collection_action'].astype(bool)
        safe = ~coop
        source = {k.removeprefix('source_decision_'): v for k, v in state.items() if k.startswith('source_decision_')}
        final = {k.removeprefix('final_decision_'): v for k, v in state.items() if k.startswith('final_decision_')}
        safe_n = source['safe_count'][0] + before(safe)
        safe_r = source['safe_reward_sum'][0] + before(safe * t['reward'])
        close(t['raw_predictions'][:, 0], (safe_r + 1) / (safe_n + 2))
        assert final['safe_count'][0] == source['safe_count'][0] + safe.sum()
        close(final['safe_reward_sum'][0], source['safe_reward_sum'][0] + (safe * t['reward']).sum())
        assert final['cooperative_observations'][0] == source['cooperative_observations'][0] + coop.sum()
        is_response = recipient == 'R_E'
        expected_counts = {
            'decision_observations': 256,
            'safe_posterior_updates': int(safe.sum()),
            'cooperative_observations': int(coop.sum()),
            'cooperative_posterior_updates': int(coop.sum()) if is_response else 0,
            'regression_statistic_updates': 0 if is_response else int(coop.sum()),
            'regression_solves': 0 if is_response else int(coop.sum()),
            'expiration_recomputations': 0,
        }
        assert reported['counts'] == expected_counts
        for key, value in expected_counts.items():
            counts[key] = counts.get(key, 0) + value
            if key != 'decision_observations':
                assert final[key][0] - source[key][0] == value
        solve_before = source['regression_solves'][0] + (np.zeros(256, dtype=int) if is_response else before(coop))
        np.testing.assert_array_equal(t['regression_solves_before'], solve_before)
        if is_response:
            means = []
            for outcome in range(4):
                mask = coop & (t['outcome'] == outcome)
                n = source['response_counts'][outcome] + before(mask)
                r = source['response_reward_sums'][outcome] + before(mask * t['reward'])
                means.append((r + 1) / (n + 2))
                assert final['response_counts'][outcome] == source['response_counts'][outcome] + mask.sum()
                close(final['response_reward_sums'][outcome], source['response_reward_sums'][outcome] + (mask * t['reward']).sum())
            close(t['raw_predictions'][:, 1], np.sum(t['estimated_law'] * np.asarray(means).T, axis=1))
            close(final['estimate'], np.r_[(final['safe_reward_sum'][0]+1)/(final['safe_count'][0]+2), (final['response_reward_sums']+1)/(final['response_counts']+2)])
        else:
            idx = np.flatnonzero(coop)
            x = np.zeros((len(idx), 12))
            x[:, :4] = t['estimated_law'][idx]
            x[np.arange(len(idx)), 4 + 4 * t['version'][idx] + t['context'][idx]] = 1
            close(final['xtx'], source['xtx'] + x.T @ x, atol=2e-10)
            close(final['xty'], source['xty'] + x.T @ t['reward'][idx], atol=2e-10)
            prior = np.r_[np.full(4, .5), np.zeros(8)]
            close((final['xtx'] + 2*np.eye(12)) @ final['coefficients'], final['xty'] + 2*prior, atol=2e-10)
            # No reconstruction of intermediate ridge coefficients: that would require new solves.
            for key in ('response_counts', 'response_reward_sums'):
                np.testing.assert_array_equal(final[key], source[key])
        for key in ('cell_counts', 'cell_reward_sums', 'window_macro_index', 'window_reward', 'window_version', 'window_context', 'window_features'):
            np.testing.assert_array_equal(final[key], source[key])
        close(t['clipped_predictions'], np.clip(t['raw_predictions'], 0, 1))
        greedy = (t['clipped_predictions'][:, 1] > t['clipped_predictions'][:, 0]).astype(int)
        np.testing.assert_array_equal(t['greedy_action'], greedy)
        p = .1 + .8 * greedy
        close(t['matched_epsilon_propensity'], p)
        close(t['greedy_expected_return'], t['exact_values'][np.arange(256), greedy])
        close(t['matched_epsilon_expected_return'], (1-p)*t['exact_values'][:, 0]+p*t['exact_values'][:, 1])
        panels[panel_id] = t
    reduction = json.loads((block / 'reduction.json').read_text())
    by_endpoint = {}
    for endpoint, sl in endpoints.items():
        values = {k: float(p['matched_epsilon_expected_return'][sl].mean()) for k, p in panels.items()}
        reported = reduction['by_endpoint'][endpoint]
        for history in ('R', 'F'):
            for method in ('R', 'F'):
                close(reported['matched_epsilon_2x2'][history+'_history'][method], values[method+'_on_'+history])
            close(reported['per_history_response_minus_full'][history+'_history'], values['R_on_'+history]-values['F_on_'+history])
        for method in ('R', 'F'):
            close(reported['per_method_R_history_minus_F_history'][method], values[method+'_on_R']-values[method+'_on_F'])
        by_endpoint[endpoint] = {k: values[a]-values[b] for k, (a, b) in comparisons.items()}
        by_endpoint[endpoint]['means'] = values
    context_rows = []
    for context in range(4):
        mask = panels['R_on_R']['context'] == context
        row = {'context': context, 'true_p11': float((panels['R_on_R']['exact_values'][mask, 1][0]-.05)/.9)}
        for key, (a, b) in comparisons.items():
            contribution = float((panels[a]['matched_epsilon_expected_return'][mask]-panels[b]['matched_epsilon_expected_return'][mask]).sum()/256)
            close(reduction['context_contributions'][str(context)][key], contribution)
            row[key] = contribution
        row['panels'] = {}
        for name, panel in panels.items():
            last = np.flatnonzero(mask)[-1]
            row['panels'][name] = {'greedy_cooperation_count': int(panel['greedy_action'][mask].sum()), 'donor_cooperation_count': int(panel['collection_action'][mask].sum()), 'last_estimated_p11': float(panel['estimated_law'][last, 3]), 'last_raw_cooperative_prediction': float(panel['raw_predictions'][last, 1])}
        context_rows.append(row)
    for key in comparisons:
        close(sum(c[key] for c in context_rows), by_endpoint['full'][key])
    blocks.append({'seed': seed, 'by_endpoint': by_endpoint, 'context_rows': context_rows})

assert counts['decision_observations'] == 1536
assert counts['safe_posterior_updates'] == 936
assert counts['cooperative_posterior_updates'] == 278
assert counts['regression_solves'] == counts['regression_statistic_updates'] == 322
means = {ep: {key: float(np.mean([b['by_endpoint'][ep][key] for b in blocks])) for key in comparisons} for ep in endpoints}
result = {
    'status': 'VERIFIED', 'launch_sha': launch_sha, 'science_artifact_digests_verified': science_digest_count,
    'input_digests_verified': input_digest_count, 'counts': counts, 'blocks': blocks, 'three_block_means': means,
    'scope': 'Existing arrays and arithmetic only; no imported learner, solve, optimizer, simulator, new policy input, reward draw or evaluation rollout. Intermediate F ridge coefficients were not reconstructed.',
    'checks': ['science/input digests', 'complete source-state equality', 'donor record equality', 'first-target fidelity', 'pre-feedback counters', 'all SAFE/response predictions', 'final counts and ridge sufficient statistics/normal equations without solve', 'reused diagonals', 'both recommendation readouts', 'all 2x2 and context contrasts'],
    'process_resources': {k: summary[k] for k in ('runner_wall_seconds', 'runner_cpu_seconds', 'peak_rss_kib', 'cpu_scope', 'rss_scope')},
}
(root / 'readback.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
print(json.dumps({k: result[k] for k in ('status', 'science_artifact_digests_verified', 'input_digests_verified', 'counts', 'three_block_means', 'process_resources')}, indent=2))
