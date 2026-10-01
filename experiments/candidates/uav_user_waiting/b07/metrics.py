"""Predeclared paired-world readings, with historical timing labeled explicitly."""

import math

import numpy as np

from experiments.candidates.uav_user_waiting.b05.protocol import OUTCOME_METRICS, INHERITED_METRICS
from . import protocol as p


def episode_metrics(raw, steps, records):
    from experiments.candidates.uav_radio_activation.b03.study import episode_metrics as native_metrics
    from experiments.candidates.uav_registered_service.b01.metrics import periodic_metrics
    from experiments.candidates.uav_user_waiting.b01.metrics import waiting_metrics
    from experiments.candidates.uav_user_waiting.b04.metrics import forecast_changes
    result = native_metrics(raw, steps, 'S2')
    result.update(periodic_metrics(raw['connections'][:steps].any(axis=1)))
    result.update(waiting_metrics(raw, steps))
    squares = np.asarray(raw['actual_ages'], np.int64)**2
    result.update(mean_age_square=float(squares.mean()), age_square_sum=int(squares.sum()),
        virtual_c_calls=0, current_candidate_requests=sum(r['counts']['candidate_requests'] for r in records),
        current_state_reductions=sum(r['counts']['state_reductions'] for r in records),
        future_candidate_requests=0, future_state_reductions=0,
        complete_calculations=sum(bool(r['completed_calculation']) for r in records),
        timely_decisions=sum(bool(r['timely']) for r in records), executed_command_changes=0,
        executed_mask_changes=0, executed_forecast_changes=0, decision_counts={})
    for record in records:
        for key, value in record['counts'].items():
            result['decision_counts'][key] = result['decision_counts'].get(key,0)+int(value)
        tick = int(record['tick'])
        if record['timely']:
            old, chosen = raw['commands'][tick], record['returned_commands']
            mask_changed = int(raw['mask'][tick]) != int(record['returned_mask'])
            result['executed_command_changes'] += int(not np.array_equal(old,chosen))
            result['executed_mask_changes'] += int(mask_changed)
            result['executed_forecast_changes'] += int(mask_changed or forecast_changes(
                raw['positions'][tick+2],old,chosen,min(4,steps-tick-2)))
    result['service_capacity_exposure'] = dict(
        active_over_two_ticks_after_start=int(sum(int(mask).bit_count()>2 for mask in raw['mask'][2:steps])),
        timely_cap_upper_bound=20.234375 if steps==256 and all(raw['timely']) else None,
        scope='bound conditional on timely cap delivery; actual startup/late mask exposure retained')
    return result


def describe(values):
    array = np.asarray(values, np.float64)
    mean, sd = float(array.mean()), float(array.std(ddof=1)) if len(array) > 1 else 0.
    half = p.T_CRITICAL * sd / math.sqrt(len(array))
    return dict(values=array.tolist(), n=len(array), mean=mean, sd=sd, descriptive_t95=[mean-half, mean+half])


def metric(row, name):
    return row['inherited'][name] if name in INHERITED_METRICS else row[name]


def paired_reading(rows, baselines, *, seeds=p.SEEDS):
    seeds = tuple(seeds)
    by = {row['seed']: row for row in rows}
    p.require(len(by) == len(rows) and set(by) == set(seeds), 'complete new paired panel required')
    metrics = OUTCOME_METRICS + INHERITED_METRICS
    new_package = p.PROGRAM + ':LRS'
    all_rows = dict(baselines)
    all_rows.update({(new_package, seed): by[seed] for seed in seeds})
    packages = (new_package,) + p.REFERENCES
    levels = {package: {name: describe([metric(all_rows[package, seed], name) for seed in seeds])
                        for name in metrics} for package in packages}
    contrasts = {f'{new_package}-{reference}': {
        name: describe([metric(by[seed], name) - metric(baselines[reference, seed], name) for seed in seeds])
        for name in metrics} for reference in p.REFERENCES}
    indices = np.random.RandomState(p.BOOTSTRAP_SEED).randint(len(seeds), size=(p.BOOTSTRAP_RESAMPLES, len(seeds)))
    bootstrap = {}
    for label, contrast in contrasts.items():
        bootstrap[label] = {}
        for name in ('max_unserved_gap', 'F_user', 'mean_served'):
            means = np.asarray(contrast[name]['values'])[indices].mean(axis=1)
            bootstrap[label][name] = dict(percentile95=np.quantile(means, [.025, .975]).tolist())
    primary = contrasts[f'{new_package}-S_F:LRS']['max_unserved_gap']
    values = np.asarray(primary['values'])
    return dict(world_seeds=list(seeds), levels=levels, contrasts=contrasts,
                primary=dict(contrast=f'{new_package}-S_F:LRS', metric='max_unserved_gap',
                             mean_difference=primary['mean'], favorable_worlds=int((values < 0).sum()),
                             equal_worlds=int((values == 0).sum()), adverse_worlds=int((values > 0).sum())),
                bootstrap=dict(seed=p.BOOTSTRAP_SEED, resamples=p.BOOTSTRAP_RESAMPLES, contrasts=bootstrap),
                timing_scope='different historical runtime/context costs are not a matched speed comparison',
                scope='adaptively reused development worlds; descriptive paired uncertainty; no automatic adoption/confirmation')
