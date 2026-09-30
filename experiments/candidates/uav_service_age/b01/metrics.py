"""Actual age accounting is an evaluator/reward function, never a policy input."""

import numpy as np
from scipy.stats import t as student_t


def actual_ages(contacts):
    contacts = np.asarray(contacts, dtype=bool)
    if contacts.ndim != 2 or contacts.shape[1] != 50 or len(contacts) > 256:
        raise ValueError('expected at most256 transitions by50 users')
    ticks = np.arange(len(contacts), dtype=np.int16)[:, None]
    last = np.maximum.accumulate(np.where(contacts, ticks, -1), axis=0)
    return (ticks - last).astype(np.int16)


def add_age_raw(raw, steps):
    ages = actual_ages(raw['connections'][:steps].any(axis=1))
    raw['actual_ages'] = ages
    raw['per_user_mean_age'] = ages.mean(axis=0) if steps else np.full(50, np.nan)
    if steps and steps % 4 == 0:
        raw['report_rewards'] = -ages.reshape(steps // 4, 4, 50).sum(axis=(1, 2), dtype=np.int64) / (50 * steps)
    else:
        # Partial evidence records its observed ages, not a claimed complete reward partition.
        raw['report_rewards'] = np.empty(0)


def age_metrics(raw, steps):
    ages = np.asarray(raw['actual_ages'])
    if ages.shape != (steps, 50) or not steps:
        raise ValueError('complete age metrics require all actual transitions')
    users = ages.mean(axis=0)
    return dict(A=float(ages.mean()), age_sum=int(ages.sum()),
                per_user_mean_age=users.tolist(),
                max_user_mean_age=float(users.max()), age_p95=float(np.quantile(ages, .95)),
                terminal_mean_age=float(ages[-1].mean()), terminal_max_age=int(ages[-1].max()))


def describe(values):
    values = np.asarray(values, dtype=np.float64)
    if not len(values) or not np.isfinite(values).all():
        raise ValueError('finite nonempty distribution required')
    mean = float(values.mean())
    half = float(student_t.ppf(.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values))) if len(values) > 1 else 0.
    return dict(mean=mean, descriptive_t95=[mean - half, mean + half],
                sd=float(values.std(ddof=1)) if len(values) > 1 else None,
                min=float(values.min()), p10=float(np.quantile(values, .1)),
                median=float(np.median(values)), p90=float(np.quantile(values, .9)), max=float(values.max()),
                positive=int((values > 0).sum()), negative=int((values < 0).sum()), zero=int((values == 0).sum()),
                values=values.tolist())


def paired_reading(rows, seeds, arms):
    by = {(r['arm'], r['seed']): r for r in rows}
    if len(by) != len(rows) or set(by) != {(a, s) for a in arms for s in seeds}:
        raise ValueError('complete paired seven-program panel required')
    metrics = ('A', 'F', 'J', 'mean_served', 'mean_quality', 'never_served',
               'max_unserved_gap', 'mean_user_max_unserved_gap', 'max_user_mean_age',
               'age_p95', 'terminal_mean_age', 'terminal_max_age', 'service_p10', 'min_served',
               'zero_service_steps', 'longest_zero_service', 'mean_path_length_m',
               'transmitter_on_ticks', 'mask_flips', 'deadline_misses',
               'candidate_requests', 'candidate_plans', 'state_reductions', 'geometry_snapshots',
               'scheduler_cpu_seconds', 'scheduler_wall_seconds', 'cpu_seconds', 'wall_seconds')
    levels = {a: {k: describe([by[a, s][k] for s in seeds]) for k in metrics} for a in arms}
    # All21 unordered arm pairs are retained; the direction of each contrast follows arms.
    contrasts = {f'{left}-{right}': {k: describe([by[left, s][k] - by[right, s][k] for s in seeds])
                                               for k in metrics}
                 for i, left in enumerate(arms) for right in arms[i + 1:]}
    # Explicit prespecified signs are convenient without changing or selecting any worlds.
    for right in ('M', 'L0', 'W', 'O', 'G', 'S2'):
        contrasts[f'L1-{right}'] = {k: describe([by['L1', s][k] - by[right, s][k] for s in seeds])
                                    for k in metrics}
    return dict(world_seeds=list(seeds), levels=levels, contrasts=contrasts,
                primary='L1-M:A; negative is favorable',
                scope='one fixed training instance; paired world variation, not training-population inference')
