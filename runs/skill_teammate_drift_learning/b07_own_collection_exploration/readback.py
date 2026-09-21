"""Read-only B07 audit. Does not import or invoke a learner, simulator, or optimizer."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np

root = Path(sys.argv[1])
launch_sha = sys.argv[2]
summary = json.loads((root / 'summary.json').read_text())
assert summary['status'] == 'COMPLETE'
assert summary['launch_sha'] == launch_sha
assert summary['seeds'] == [95301, 95302, 95303]
assert summary['completed_decision_fits'] == summary['completed_law_fits'] == 12
source, total = 2048, 2304
endpoints = {'first64': (2048, 2112), 'full': (2048, 2304), 'late64': (2240, 2304)}
branches = ('R_U', 'F_U', 'R_E', 'F_E')
records = []
verified = 0
all_counts = {}

def close(a, b, atol=2e-12):
    np.testing.assert_allclose(a, b, atol=atol, rtol=2e-12)

def load(path):
    with np.load(path, allow_pickle=False) as data:
        arrays = {name: data[name] for name in data.files}
    assert all(value.dtype != object for value in arrays.values())
    return arrays

for seed in summary['seeds']:
    block = root / f'seed_{seed}'
    for relative, digest in json.loads((block / 'artifacts.json').read_text()).items():
        assert hashlib.sha256((block / relative).read_bytes()).hexdigest() == digest
        verified += 1
    common = load(block / 'common.npz')
    by_branch, branch_means = {}, {}
    for branch in branches:
        t = load(block / branch / 'trajectory.npz')
        state = load(block / branch / 'state.npz')
        reported = json.loads((block / branch / 'summary.json').read_text())
        assert reported['source_identity'] == launch_sha
        by_branch[branch] = t
        assert len(t['reward']) == total
        np.testing.assert_array_equal(t['decision_updates_before'], np.arange(total))
        close(t['clipped_predictions'], np.clip(t['raw_predictions'], 0, 1))
        greedy = (t['clipped_predictions'][:, 1] > t['clipped_predictions'][:, 0]).astype(int)
        np.testing.assert_array_equal(greedy, t['greedy_action'])
        matched_p = .1 + .8 * greedy
        actual_p = np.full(total, .5)
        if branch.endswith('_E'):
            actual_p[source:] = matched_p[source:]
        close(t['collection_propensity'], actual_p)
        close(t['matched_epsilon_propensity'], matched_p)
        np.testing.assert_array_equal(t['collection_action'], common['collector_uniform'] >= 1-actual_p)
        true_law = np.stack([common['source_law'], common['target_law']])[t['version'], t['context']]
        truth = np.column_stack([np.full(total, .6), .05 + .9*true_law[:, 3]])
        close(t['exact_values'], truth)
        readouts = {
            'greedy_expected_return': truth[np.arange(total), greedy],
            'matched_epsilon_expected_return': (1-matched_p)*truth[:, 0]+matched_p*truth[:, 1],
            'actual_collector_expected_return': (1-actual_p)*truth[:, 0]+actual_p*truth[:, 1],
        }
        for name, value in readouts.items():
            close(t[name], value)
        counts = np.zeros((2, 4, 4), dtype=int)
        center = np.full(4, .25)
        safe_count = 0
        safe_sum = 0
        response_count = np.zeros(4, dtype=int)
        response_sum = np.zeros(4)
        for index in range(total):
            version, context = int(t['version'][index]), int(t['context'][index])
            if index == source:
                center = ((counts[0] + .5)/(counts[0].sum(axis=1, keepdims=True)+2)).mean(axis=0)
            expected_law = (counts[version, context]+2*center)/(counts[version, context].sum()+2)
            close(t['estimated_law'][index], expected_law)
            close(t['law_prior_center'][index], center)
            assert t['law_counts_before'][index] == counts[version, context].sum()
            close(t['raw_predictions'][index, 0], (safe_sum+1)/(safe_count+2))
            if branch.startswith('R_'):
                response_means = (response_sum+1)/(response_count+2)
                close(t['response_means'][index], response_means)
                close(t['raw_predictions'][index, 1], expected_law @ response_means)
            action, outcome, reward = (int(t[k][index]) for k in ('collection_action', 'outcome', 'reward'))
            if action:
                expected_outcome = min(int(np.searchsorted(np.cumsum(true_law[index]), common['outcome_uniform'][index], side='right')), 3)
                assert outcome == expected_outcome
                counts[version, context, outcome] += 1
                response_count[outcome] += 1
                response_sum[outcome] += reward
            else:
                assert outcome == 0
                safe_count += 1
                safe_sum += reward
            reward_p = .6 if not action else (.95 if outcome == 3 else .05)
            close(t['reward_probability'][index], reward_p)
            assert reward == int(common['reward_uniform_slots'][index, action, outcome] < reward_p)
            assert t['law_counts_after'][index] == counts[version, context].sum()
            np.testing.assert_array_equal(t['terminal_outcome'][index], [outcome//2, outcome%2])
            np.testing.assert_array_equal(t['post_positions'][index, -1], t['terminal_outcome'][index])
            if index+1 in (source, total):
                prefix = 'source' if index+1 == source else 'final'
                np.testing.assert_array_equal(state[f'{prefix}_law_counts'], counts)
                assert int(state[f'{prefix}_decision_safe_count'][0]) == safe_count
                close(state[f'{prefix}_decision_safe_reward_sum'][0], safe_sum)
                assert int(state[f'{prefix}_decision_cooperative_observations'][0]) == int(response_count.sum())
                if branch.startswith('R_'):
                    np.testing.assert_array_equal(state[f'{prefix}_decision_response_counts'], response_count)
                    close(state[f'{prefix}_decision_response_reward_sums'], response_sum)
                else:
                    coop = np.flatnonzero(t['collection_action'][:index+1])
                    features = np.zeros((len(coop), 12))
                    features[:, :4] = t['estimated_law'][coop]
                    features[np.arange(len(coop)), 4+t['version'][coop]*4+t['context'][coop]] = 1
                    close(state[f'{prefix}_decision_xtx'], features.T @ features, atol=2e-10)
                    close(state[f'{prefix}_decision_xty'], features.T @ t['reward'][coop], atol=2e-10)
                    coefficient = state[f'{prefix}_decision_coefficients']
                    prior = np.r_[np.full(4, .5), np.zeros(8)]
                    close((state[f'{prefix}_decision_xtx']+2*np.eye(12)) @ coefficient,
                          state[f'{prefix}_decision_xty']+2*prior, atol=2e-10)
        assert reported['counts']['actual_macros'] == total
        assert reported['counts']['law_posterior_updates'] == int(response_count.sum())
        for key, value in reported['counts'].items():
            all_counts[key] = all_counts.get(key, 0) + value
        branch_means[branch] = {}
        for name, (start, stop) in endpoints.items():
            values = {key: float(value[start:stop].mean()) for key, value in readouts.items()}
            values['sampled_return'] = float(t['reward'][start:stop].mean())
            branch_means[branch][name] = values
            for key, value in values.items():
                close(reported['target_by_endpoint'][name]['mean_'+key], value)
    source_keys = ('collection_action','outcome','reward','reward_probability','primitive_actions','pre_positions','post_positions','estimated_law')
    for branch in branches:
        for key in source_keys:
            np.testing.assert_array_equal(by_branch[branch][key][:source], by_branch['R_U'][key][:source])
    for key in source_keys:
        np.testing.assert_array_equal(by_branch['R_U'][key], by_branch['F_U'][key])
    for learner in ('R', 'F'):
        np.testing.assert_array_equal(by_branch[learner+'_U']['raw_predictions'][:source+1],
                                      by_branch[learner+'_E']['raw_predictions'][:source+1])
        uniform_state = load(block / (learner+'_U') / 'state.npz')
        own_state = load(block / (learner+'_E') / 'state.npz')
        for name in uniform_state:
            if name.startswith(('initial_', 'source_')):
                np.testing.assert_array_equal(uniform_state[name], own_state[name])
    for branch in branches:
        t = by_branch[branch]
        mean_mistake_cost = float((t['exact_values'][source:].max(axis=1)-t['greedy_expected_return'][source:]).mean())
        close(branch_means[branch]['full']['matched_epsilon_expected_return'], .649-.8*mean_mistake_cost)
        if branch.endswith('_U'):
            close(branch_means[branch]['full']['actual_collector_expected_return'], .595)
    gaps = {}
    for endpoint in endpoints:
        e = branch_means['R_E'][endpoint]['actual_collector_expected_return'] - branch_means['F_E'][endpoint]['actual_collector_expected_return']
        u = branch_means['R_U'][endpoint]['matched_epsilon_expected_return'] - branch_means['F_U'][endpoint]['matched_epsilon_expected_return']
        wr = branch_means['R_E'][endpoint]['matched_epsilon_expected_return']-branch_means['R_U'][endpoint]['matched_epsilon_expected_return']
        wf = branch_means['F_E'][endpoint]['matched_epsilon_expected_return']-branch_means['F_U'][endpoint]['matched_epsilon_expected_return']
        close(e-u, wr-wf)
        gaps[endpoint] = {'executed_e_response_minus_full': e, 'matched_u_response_minus_full': u, 'matched_feedback_interaction': e-u, 'response_matched_e_minus_u': wr, 'full_matched_e_minus_u': wf}
    records.append({'seed': seed, 'branch_means': branch_means, 'gaps': gaps})
for endpoint in endpoints:
    for raw_key, summary_key in (
        ('executed_e_response_minus_full','primary_executed_e_response_minus_full'),
        ('matched_u_response_minus_full','matched_u_response_minus_full'),
        ('matched_feedback_interaction','matched_feedback_interaction'),
    ):
        values = [r['gaps'][endpoint][raw_key] for r in records]
        reported = summary['reduction']['by_endpoint'][endpoint][summary_key]
        close(reported['paired_values'], values)
        close(reported['mean'], sum(values)/3)
assert all_counts['actual_macros'] == 27648
assert all_counts['primitive_ticks'] == 82944
assert all_counts['sampled_reward_labels'] == 27648
assert all_counts['q_truth_panels'] == 27648
assert all_counts['scalar_policy_values'] == 82944
result = {
    'status': 'VERIFIED', 'launch_sha': launch_sha,
    'artifact_digests_verified': verified,
    'scope': 'Raw-array arithmetic; no learner, simulator, optimizer, new policy input, reward draw or evaluation rollout invoked.',
    'checks': ['all artifact digests', 'source identity', 'pre-outcome action propensities', 'all law priors and own-history counts', 'SAFE and response means', 'saved source/final counts and regression normal equations', 'addressed action/outcome/reward draws', 'terminal macro state', 'all three policy readouts', 'matched-data feedback contrasts', 'source and uniform stream matching'],
    'counts': all_counts, 'blocks': records,
    'process_resources': {key:summary[key] for key in ('runner_wall_seconds','runner_cpu_seconds','peak_rss_kib','cpu_scope','rss_scope')},
}
(root/'readback.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
print(json.dumps({key:result[key] for key in ('status','artifact_digests_verified','counts','process_resources')}, indent=2))
