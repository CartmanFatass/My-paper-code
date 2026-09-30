"""Native outcome endpoints and prespecified paired world contrasts."""

import numpy as np

from experiments.candidates.uav_radio_activation.b03.study import episode_metrics as native_metrics
from experiments.candidates.uav_registered_service.b01.metrics import periodic_metrics
from experiments.candidates.uav_user_waiting.b01.metrics import METRICS, waiting_metrics
from experiments.candidates.uav_service_age.b01.metrics import describe


EXTRA_METRICS = ('mean_age_square', 'age_square_sum', 'virtual_c_calls',
                 'current_candidate_requests', 'future_candidate_requests',
                 'current_state_reductions', 'future_state_reductions',
                 'anticipation_changed_pair', 'anticipation_two_finalists',
                 'c_cpu_seconds', 'c_wall_seconds')


def episode_metrics(raw, steps, arm, records):
    result = native_metrics(raw, steps, 'S2')
    result.update(periodic_metrics(raw['connections'][:steps].any(axis=1)))
    result.update(waiting_metrics(raw, steps))
    squares = np.asarray(raw['actual_ages'], dtype=np.int64) ** 2
    result.update(mean_age_square=float(squares.mean()), age_square_sum=int(squares.sum()))
    result['virtual_c_calls'] = sum(record['counts']['virtual_c_decisions'] for record in records)
    for label in ('current', 'future'):
        stages = [record['current'] for record in records] if label == 'current' else [
            branch['continuation'] for record in records for branch in record['branches'].values()]
        stages = [stage for stage in stages if stage]
        result[label + '_candidate_requests'] = sum(len(stage['request_pairs']) for stage in stages)
        result[label + '_state_reductions'] = sum(
            len(stage['evaluated_pairs']) * stage['length'] + len(stage['partial'].get('contacts', []))
            for stage in stages)
    result['anticipation_changed_pair'] = sum(record['timely'] and record['c_diagnostics_valid']
        and not np.array_equal(record['c0_pair'], record['c1_pair']) for record in records)
    result['anticipation_two_finalists'] = sum(len(record['first_finalists']) == 2 for record in records)
    result['decision_counts'] = {}
    for record in records:
        for key, value in record['counts'].items():
            if isinstance(value, (int, np.integer)):
                result['decision_counts'][key] = result['decision_counts'].get(key, 0) + int(value)
    valid = raw['model_valid'][:steps]
    truth = raw['connections'][:steps].any(axis=1)
    predicted = raw['model_contacts'][:steps]
    result['model_contact_false_positive'] = int((predicted[valid] & ~truth[valid]).sum())
    result['model_contact_false_negative'] = int((~predicted[valid] & truth[valid]).sum())
    result['model_contact_transitions'] = int(valid.sum())
    result['model_start_tick'] = int(raw['terminal_history_start'])
    result['model_unknown_prefix_transitions'] = max(0, result['model_start_tick']) if result['model_start_tick'] >= 0 else steps
    result['terminal_history_complete'] = bool(raw['terminal_history_complete'])
    result['terminal_burden_unknown'] = bool(raw['terminal_burden_unknown'])
    result['terminal_model_burden_abs_error_max'] = int(np.abs(
        raw['terminal_burden'] - np.asarray(raw['actual_ages'], dtype=np.int64).sum(axis=0)).max())
    return result


def paired_reading(rows, seeds, arms=('A', 'S', 'M', 'R')):
    by = {(row['arm'], row['seed']): row for row in rows}
    if len(by) != len(rows) or set(by) != {(arm, seed) for arm in arms for seed in seeds}:
        raise ValueError('complete paired A/S/M/R panel required')
    metrics = METRICS + EXTRA_METRICS
    levels = {arm: {key: describe([by[arm, seed][key] for seed in seeds])
                    for key in metrics} for arm in arms}
    contrasts = {f'{left}-{right}': {
        key: describe([by[left, seed][key] - by[right, seed][key] for seed in seeds])
        for key in metrics} for i, left in enumerate(arms) for right in arms[i + 1:]}
    return dict(world_seeds=list(seeds), levels=levels, contrasts=contrasts,
                primary='A-M:mean_user_max_unserved_gap; negative is favorable',
                planned_secondary='A-S:mean_user_max_unserved_gap; S-M ordinary cost comparison; R worst-user-mean reference',
                scope='fixed ordinary programs; independent paired worlds, no learned-policy or user-level independence claim')
