"""Complete native outcomes and separate computation/delivery/change exposure."""

import numpy as np

from experiments.candidates.uav_service_age.b01.metrics import describe
from experiments.candidates.uav_user_waiting.b01.metrics import METRICS as OUTCOME_METRICS
from experiments.candidates.uav_user_waiting.b02.metrics import episode_metrics as inherited_metrics
from experiments.candidates.uav_user_waiting.b02 import protocol as p


BOOTSTRAP_SEED, BOOTSTRAP_RESAMPLES = 29426998, 10000
PRIMARY = ('mean_served', 'max_unserved_gap', 'F_user')
EXTRA_METRICS = (
    'mean_age_square', 'age_square_sum', 'c_cpu_seconds', 'c_wall_seconds',
    'complete_calculations', 'timely_decisions', 'executed_command_changes',
    'executed_mask_changes', 'executed_forecast_changes', 'union_complete',
    'union_pool_size_total', 'union_excluded_total', 'union_filter_changes',
    'union_U_differs_S', 'union_K_differs_M', 'selected_floor_satisfied',
    'selected_model_service_minus_floor', 'selected_native_minus_model_service',
)


def forecast_changes(position, old_commands, new_commands, length):
    """Whether an actual delivered block can move differently from holding old motion."""
    old, new = position.copy(), position.copy()
    for _ in range(length):
        old = np.clip(old + 30. * old_commands, p.LOW, p.HIGH)
        new = np.clip(new + 30. * new_commands, p.LOW, p.HIGH)
        if not np.array_equal(old, new):
            return True
    return False


def episode_metrics(raw, steps, arm, records):
    result = inherited_metrics(raw, steps, arm, records)
    result.update({key: 0 for key in EXTRA_METRICS[4:]})
    for record in records:
        tick = int(record['tick'])
        current = record['current']
        union = record.get('union')
        complete = bool(current and current['completed'] and
                        (union is None or union['completed']))
        result['complete_calculations'] += int(complete)
        timely = bool(record['timely'])
        result['timely_decisions'] += int(timely)
        if timely:
            old, chosen = raw['commands'][tick], record['returned_commands']
            mask_changed = int(raw['mask'][tick]) != int(record['returned_mask'])
            result['executed_command_changes'] += int(not np.array_equal(old, chosen))
            result['executed_mask_changes'] += int(mask_changed)
            result['executed_forecast_changes'] += int(mask_changed or forecast_changes(
                raw['positions'][tick + 2], old, chosen, min(4, steps - tick - 2)))
        if union is None or not union['completed']:
            continue
        result['union_complete'] += 1
        pool = [tuple(map(int, pair)) for pair in union['pool_pairs']]
        result['union_pool_size_total'] += len(pool)
        result['union_excluded_total'] += int((~union['feasible']).sum())
        for metric, left, right in (('union_filter_changes', 'k_pair', 'u_pair'),
                                    ('union_U_differs_S', 'u_pair', 's_pair'),
                                    ('union_K_differs_M', 'k_pair', 'm_pair')):
            result[metric] += int(not np.array_equal(union[left], union[right]))
        selected = tuple(map(int, union['u_pair' if arm == 'U' else 'k_pair']))
        service = int(union['service_totals'][pool.index(selected)])
        delta = service - int(union['service_floor_total'])
        result['selected_floor_satisfied'] += int(delta >= 0)
        result['selected_model_service_minus_floor'] += delta
        if timely:
            actual = int(raw['connections'][tick + 2:min(tick + 6, steps)].sum())
            result['selected_native_minus_model_service'] += actual - service
    return result


def paired_reading(rows, seeds, arms=('M', 'S', 'U', 'K')):
    by = {(row['arm'], row['seed']): row for row in rows}
    if len(by) != len(rows) or set(by) != {(arm, seed) for arm in arms for seed in seeds}:
        raise ValueError('complete paired M/S/U/K panel required')
    metrics = OUTCOME_METRICS + EXTRA_METRICS
    levels = {arm: {key: describe([by[arm, seed][key] for seed in seeds])
                    for key in metrics} for arm in arms}
    contrasts = {f'{left}-{right}': {
        key: describe([by[left, seed][key] - by[right, seed][key] for seed in seeds])
        for key in metrics} for index, left in enumerate(arms) for right in arms[:index]}
    indices = np.random.RandomState(BOOTSTRAP_SEED).randint(
        len(seeds), size=(BOOTSTRAP_RESAMPLES, len(seeds)))
    bootstrap = {}
    for name, contrast in contrasts.items():
        bootstrap[name] = {}
        for key in PRIMARY:
            means = np.array(contrast[key]['values'])[indices].mean(axis=1)
            bootstrap[name][key] = dict(percentile95=np.quantile(means, [.025, .975]).tolist())
    primary = contrasts['K-M']
    joint = ((np.array(primary['mean_served']['values']) >= 0) &
             (np.array(primary['max_unserved_gap']['values']) < 0) &
             (np.array(primary['F_user']['values']) < 0))
    return dict(world_seeds=list(seeds), levels=levels, contrasts=contrasts,
                primary='K-M joint native mean service>=0, episode maximum gap<0, worst-user mean age<0',
                mean_signs=dict(service=primary['mean_served']['mean'] >= 0,
                                maximum_gap=primary['max_unserved_gap']['mean'] < 0,
                                worst_mean_age=primary['F_user']['mean'] < 0),
                joint_favorable_worlds=int(joint.sum()), joint_world_vector=joint.tolist(),
                bootstrap=dict(seed=BOOTSTRAP_SEED, resamples=BOOTSTRAP_RESAMPLES,
                               contrasts=bootstrap, scope='paired-world percentile diagnostics'),
                secondary='K-U local floor; U-S expanded ordinary search; all six arm contrasts retained',
                scope='exploratory fixed ordinary programs; joint signs are not a noninferiority tolerance or adoption rule; worlds independent, users and slots nested')
