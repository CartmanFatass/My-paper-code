"""Predeclared paired-world readings, with historical timing labeled explicitly."""

import math

import numpy as np

from experiments.candidates.uav_user_waiting.b05.protocol import OUTCOME_METRICS, INHERITED_METRICS
from . import protocol as p


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
    primary = contrasts[f'{new_package}-S:LRS']['max_unserved_gap']
    values = np.asarray(primary['values'])
    return dict(world_seeds=list(seeds), levels=levels, contrasts=contrasts,
                primary=dict(contrast=f'{new_package}-S:LRS', metric='max_unserved_gap',
                             mean_difference=primary['mean'], favorable_worlds=int((values < 0).sum()),
                             equal_worlds=int((values == 0).sum()), adverse_worlds=int((values > 0).sum())),
                bootstrap=dict(seed=p.BOOTSTRAP_SEED, resamples=p.BOOTSTRAP_RESAMPLES, contrasts=bootstrap),
                timing_scope='new local runtime vs historical remote baseline costs is not a matched speed comparison',
                scope='adaptively reused development worlds; descriptive paired uncertainty; no automatic adoption/confirmation')
