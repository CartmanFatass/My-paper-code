"""All nine fixed levels and all paired final contrasts, clustered by world."""
from itertools import combinations

import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.reading import numeric_summary, sum_counts
from experiments.candidates.uav_parent_adaptation.b05_radio_composition.reading import METRICS as BASE_METRICS
from .contract import ARMS, arm_parts

METRICS = BASE_METRICS + ('mean_height_m',)
# Orient the primary and its two companions explicitly; retain every other pair.
PRIMARY = (('CONT_S2', 'CAL_S2'), ('CONT_S2', 'S_I_S2'), ('CAL_S2', 'S_I_S2'))
PAIRS = PRIMARY + tuple((left, right) for left, right in combinations(ARMS, 2)
                        if frozenset((left, right)) not in {frozenset(pair) for pair in PRIMARY})


def cost_totals(rows):
    result = {family: sum_counts(r['policy_counts'] for r in rows
                                if ('C' if arm_parts(r['arm'])[0] in ('C', 'Q_I') else 'S') == family)
              for family in ('C', 'S')}
    result.update({coordinator: sum_counts(r['coordinator_counts'] for r in rows
                                          if arm_parts(r['arm'])[1] == coordinator)
                   for coordinator in ('S2', 'T2')})
    result['by_phase'] = {phase: dict(episodes=sum(r['phase'] == phase for r in rows),
                                     episode_cpu_seconds=sum(r['cpu_seconds'] for r in rows if r['phase'] == phase),
                                     episode_wall_seconds=sum(r['wall_seconds'] for r in rows if r['phase'] == phase),
                                     critic_cpu_seconds=sum(r['critic_cpu_seconds'] for r in rows if r['phase'] == phase))
                          for phase in ('training', 'final')}
    return result


def read_comparisons(rows, protocol):
    final = [row for row in rows if row['phase'] == 'final']
    by_key = {(r['arm'], r['world'], r['tape']): r for r in final}
    if len(by_key) != len(final) or set(by_key) != set(protocol.schedule()):
        raise ValueError('incomplete or duplicated final B09 panel')

    def at(arm, world, metric, tape=None):
        deterministic = arm_parts(arm)[0] == 'C'
        tapes = (-1,) if deterministic else protocol.tapes if tape is None else (tape,)
        return float(np.mean([by_key[arm, world, t][metric] for t in tapes]))

    levels = {arm: {metric: dict(numeric_summary([at(arm, w, metric) for w in protocol.worlds]),
                                world_values=[at(arm, w, metric) for w in protocol.worlds])
                    for metric in METRICS} for arm in ARMS}
    paired = {}
    for left, right in PAIRS:
        metrics = {}
        tapes = (-1,) if arm_parts(left)[0] == arm_parts(right)[0] == 'C' else protocol.tapes
        for metric in METRICS:
            delta = np.array([at(left, w, metric) - at(right, w, metric) for w in protocol.worlds])
            metrics[metric] = dict(numeric_summary(delta), differences=delta.tolist(),
                                   positive_worlds=int((delta > 0).sum()), negative_worlds=int((delta < 0).sum()),
                                   equal_worlds=int((delta == 0).sum()),
                                   world_tape_differences=[dict(world=w, tape=t,
                                       difference=at(left, w, metric, t) - at(right, w, metric, t))
                                       for w in protocol.worlds for t in tapes])
        paired[left + '-' + right] = metrics
    return dict(worlds=list(protocol.worlds), tapes=list(protocol.tapes), levels=levels, paired=paired,
                primary='CONT_S2-CAL_S2', companion_contrasts=['CONT_S2-S_I_S2', 'CAL_S2-S_I_S2'],
                unit='average the two I tapes within each final world before paired summaries',
                uncertainty='descriptive paired-world t interval; one training realization per arm; no training-population inference',
                zero_service_episodes={arm: sum(by_key[arm, w, t]['zero_service_steps'] > 0
                                               for w in protocol.worlds
                                               for t in ((-1,) if arm_parts(arm)[0] == 'C' else protocol.tapes))
                                       for arm in ARMS})
