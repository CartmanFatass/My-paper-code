"""Complete actual user-waiting endpoints; never policy inputs."""

import numpy as np

from experiments.candidates.uav_service_age.b01.metrics import age_metrics, describe


METRICS = (
    'F_user', 'A', 'F', 'J', 'mean_served', 'mean_quality', 'never_served',
    'max_unserved_gap', 'mean_user_max_unserved_gap', 'max_closed_gap',
    'max_left_censored_gap', 'max_right_censored_gap', 'age_p95',
    'terminal_mean_age', 'terminal_max_age', 'service_p10', 'min_served',
    'zero_service_steps', 'longest_zero_service', 'mean_path_length_m',
    'transmitter_on_ticks', 'mask_flips', 'deadline_misses',
    'candidate_requests', 'candidate_plans', 'state_reductions',
    'geometry_snapshots', 'scheduler_cpu_seconds', 'scheduler_wall_seconds',
    'cpu_seconds', 'wall_seconds',
)


def waiting_metrics(raw, steps):
    result = age_metrics(raw, steps)
    result['F_user'] = result['max_user_mean_age']
    result['worst_users'] = np.flatnonzero(
        np.asarray(result['per_user_mean_age']) == result['F_user']).tolist()
    gaps = np.asarray(raw['unserved_gap_rows'])
    group_masks = {
        'all': np.ones(len(gaps), dtype=bool),
        'closed': (gaps[:, 4] == 0) & (gaps[:, 5] == 0),
        'left_censored': gaps[:, 4] == 1,
        'right_censored': gaps[:, 5] == 1,
    }
    result['per_user_gaps'] = {}
    for name, mask in group_masks.items():
        chosen = gaps[mask]
        per_user = [chosen[chosen[:, 0] == user, 3] for user in range(50)]
        maxima = [int(lengths.max()) if len(lengths) else 0 for lengths in per_user]
        result['per_user_gaps'][name] = dict(
            counts=[len(lengths) for lengths in per_user], maxima=maxima,
            totals=[int(lengths.sum()) for lengths in per_user])
        if name != 'all':
            result['max_' + name + '_gap'] = max(maxima)
    return result


def paired_reading(rows, seeds, arms=('R', 'O', 'W', 'M')):
    by = {(row['arm'], row['seed']): row for row in rows}
    if len(by) != len(rows) or set(by) != {(arm, seed) for arm in arms for seed in seeds}:
        raise ValueError('complete four-program paired world panel required')
    levels = {arm: {key: describe([by[arm, seed][key] for seed in seeds])
                    for key in METRICS} for arm in arms}
    contrasts = {
        f'{left}-{right}': {
            key: describe([by[left, seed][key] - by[right, seed][key] for seed in seeds])
            for key in METRICS}
        for i, left in enumerate(arms) for right in arms[i + 1:]
    }
    return dict(world_seeds=list(seeds), levels=levels, contrasts=contrasts,
                primary='R-O:F_user; negative is favorable',
                scope='fixed ordinary programs; paired independent world variation, no learning claim; users/slots are nested')
