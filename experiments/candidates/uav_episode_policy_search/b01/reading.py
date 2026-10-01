"""Complete episode readings and the fixed descriptive world comparison."""
import numpy as np

from .contract import CONTRASTS, PROGRAMS


def _longest(values):
    longest = current = 0
    for value in values:
        current = current + 1 if value else 0
        longest = max(current, longest)
    return longest


def episode_metrics(raw):
    reward = np.asarray(raw['reward'], dtype=np.float64)
    served = np.asarray(raw['served'], dtype=np.int64)
    quality = np.asarray(raw['sinr_quality'], dtype=np.float64)
    positions = np.asarray(raw['positions'], dtype=np.float64)
    post = positions[1:]
    displacement = np.diff(positions, axis=0)
    travel = np.linalg.norm(displacement, axis=-1).sum(axis=0)
    active = np.asarray(raw['transmitter_mask'], dtype=bool)
    masks = np.asarray(raw['installed_mask'], dtype=bool)
    eligible = np.asarray(raw['eligible_agent'], dtype=np.int64)
    di = np.arange(len(eligible))
    predictions = np.asarray(raw['gate_prediction'], dtype=np.float64)
    lower, upper = post[..., 2] <= 50.001, post[..., 2] >= 149.999
    xy = ((post[..., :2] <= .001) | (post[..., :2] >= 999.999)).any(axis=-1)
    switches = np.count_nonzero(np.diff(np.vstack((np.ones((1, 5), dtype=bool), masks)), axis=0), axis=0)
    result = dict(steps=len(reward), J=float(reward.mean()), return_sum=float(reward.sum()),
                  mean_served=float(served.mean()), service_p10=float(np.quantile(served, .1, method='linear')),
                  min_served=int(served.min()), zero_service_steps=int(np.count_nonzero(served == 0)),
                  zero_service_episode=int(np.any(served == 0)), longest_zero_service_streak=_longest(served == 0),
                  mean_sinr_quality=float(quality.mean()), coverage_reward=float(.7 * served.mean() / 50),
                  quality_reward=float(.3 * quality.mean()), mean_path_length_m=float(travel.mean()),
                  mean_height_m=float(post[..., 2].mean()), end_height_m=float(post[-1, :, 2].mean()),
                  lower_altitude_uav_steps=int(lower.sum()), upper_altitude_uav_steps=int(upper.sum()),
                  xy_boundary_uav_steps=int(xy.sum()), zero_displacement_uav_ticks=int(np.all(displacement == 0, axis=-1).sum()),
                  active_transmitter_ticks=int(active.sum()), active_transmitter_fraction=float(active.mean()),
                  mask_bit_switches=int(switches.sum()),
                  old_mask_censored_decision_rows=int((~raw['old_decision_mask']).sum()),
                  mean_visible_users=float(np.mean(raw['n_current'])), mean_visible_peers=float(np.mean(raw['n_peers'])),
                  eligible_zero_count=int(np.count_nonzero(raw['gate_count'] == 0)),
                  eligible_mean_capped_count=float(np.mean(raw['gate_count'])),
                  fallback_decisions=int(np.count_nonzero(raw['fallback'])),
                  eligible_fallback_decisions=int(np.count_nonzero(raw['fallback'][di, eligible])),
                  gate_requests=len(eligible), requested_off=int(np.count_nonzero(raw['gate_requested_off'])),
                  executed_off=int(np.count_nonzero(raw['gate_off'])), forced_decisions=int(np.count_nonzero(raw['gate_forced'])),
                  off_fraction=float(np.mean(raw['gate_off'])),
                  prediction_mean=float(predictions.mean()), prediction_sd=float(predictions.std()),
                  prediction_min=float(predictions.min()), prediction_max=float(predictions.max()),
                  prediction_positive=int(np.count_nonzero(predictions > 0)), prediction_negative=int(np.count_nonzero(predictions < 0)),
                  prediction_zero=int(np.count_nonzero(predictions == 0)),
                  mean_motion_entropy=float(np.mean(raw['entropy'])),
                  policy_cache_hits=int(np.count_nonzero(raw['memo_hit'])), policy_decisions=int(raw['action_index'].size))
    for agent in range(5):
        result.update({f'uav{agent}_{name}': value for name, value in (
            ('travel_m', float(travel[agent])), ('mean_height_m', float(post[:, agent, 2].mean())),
            ('end_height_m', float(post[-1, agent, 2])), ('lower_height_ticks', int(lower[:, agent].sum())),
            ('upper_height_ticks', int(upper[:, agent].sum())), ('active_ticks', int(active[:, agent].sum())),
            ('mask_switches', int(switches[agent])))})
    indices=np.repeat(raw['p0_action_index'],4,axis=0) if 'p0_action_index' in raw else np.repeat(raw['action_index'],4,axis=0)
    from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS
    p0_commands=COMMANDS[indices]
    projected=np.clip(positions[:-1]+p0_commands.astype(np.float64)*30.,[0.,0.,50.],[1000.,1000.,150.])
    requested=positions[:-1]+raw['commands'].astype(np.float64)*30.
    result.update(boundary_clipped_uav_ticks=int(np.any(requested!=positions[1:],axis=-1).sum()),
                  same_history_category_changes=int(np.count_nonzero(raw.get('p0_action_index',raw['action_index'])!=raw['action_index'])),
                  same_history_clipped_step_changes=int(np.any(projected!=positions[1:],axis=-1).sum()),
                  zero_head_max_error=float(np.max(raw.get('zero_head_error',np.zeros(1)))))
    return result


def metric_values(row):
    # All scalar episode measurements, including work and scoped times. Identity
    # integers such as world/tape/force_tick are deliberately not measurements.
    exclude = {'world', 'tape', 'block', 'iteration', 'direction', 'sign', 'world_index', 'motion_root', 'gate_root'}
    values = {key: float(value) for key, value in row.items()
              if key not in exclude and type(value) in (int, float)}
    values.update({'policy_' + key: float(value) for key, value in row['policy_counts'].items()})
    if not all(np.isfinite(value) for value in values.values()):
        raise ValueError('nonfinite episode reading')
    return values


def _summary(values, indices):
    values = np.asarray(values, dtype=np.float64)
    means = values[indices].mean(axis=1)
    return dict(n=len(values), mean=float(values.mean()), sd=float(values.std(ddof=1)) if len(values) > 1 else None,
                min=float(values.min()), max=float(values.max()), world_values=values.tolist(),
                descriptive_bootstrap95=np.quantile(means, [.025, .975], method='linear').tolist(),
                positive=int(np.count_nonzero(values > 0)), negative=int(np.count_nonzero(values < 0)),
                zero=int(np.count_nonzero(values == 0)))


def comparisons(rows, protocol):
    final = [row for row in rows if row['kind'] == 'evaluation']
    by_key = {(row['program'], row['world'], row['tape']): row for row in final}
    expected = {(program, world, tape) for world in protocol.worlds for program, tape in protocol.episode_order(0)}
    if len(by_key) != len(final) or set(by_key) != expected:
        raise ValueError('incomplete or duplicated fixed final panel')
    all_values = {key: metric_values(row) for key, row in by_key.items()}
    metrics = tuple(sorted(next(iter(all_values.values()))))
    if any(tuple(sorted(value)) != metrics for value in all_values.values()):
        raise ValueError('programs expose different measurement columns')
    world_values = {program: {} for program in PROGRAMS}
    for program in PROGRAMS:
        tapes = (None,) if program.startswith('C_') else (0, 1)
        for metric in metrics:
            world_values[program][metric] = np.array([
                np.mean([all_values[program, world, tape][metric] for tape in tapes]) for world in protocol.worlds])
    indices = np.random.default_rng(protocol.bootstrap_seed).integers(
        0, len(protocol.worlds), size=(protocol.bootstrap_resamples, len(protocol.worlds)))
    levels = {program: {metric: _summary(values, indices) for metric, values in measurements.items()}
              for program, measurements in world_values.items()}
    contrasts = {f'{left}-{right}': {metric: _summary(world_values[left][metric] - world_values[right][metric], indices)
                                    for metric in metrics} for left, right in CONTRASTS}
    # Adverse-world lists are descriptive signed components, not a pass rule.
    adverses = {f'{left}-{right}': {
        'lower_J': [w for w, x in zip(protocol.worlds, contrasts[f'{left}-{right}']['J']['world_values']) if x < 0],
        'lower_mean_service': [w for w, x in zip(protocol.worlds, contrasts[f'{left}-{right}']['mean_served']['world_values']) if x < 0],
        'more_zero_service_steps': [w for w, x in zip(protocol.worlds, contrasts[f'{left}-{right}']['zero_service_steps']['world_values']) if x > 0],
        'longer_zero_service_streak': [w for w, x in zip(protocol.worlds, contrasts[f'{left}-{right}']['longest_zero_service_streak']['world_values']) if x > 0],
    } for left, right in CONTRASTS}
    return dict(worlds=list(protocol.worlds), levels=levels, contrasts=contrasts, adverses=adverses,
                uncertainty='Pointwise percentile world bootstrap; two stochastic tapes averaged within world; C once. '
                            'Conditional on two realized paired training blocks and one frozen parent; no training-population, '
                            'simultaneous-comparison or equivalence coverage.',
                bootstrap=dict(seed=protocol.bootstrap_seed, resamples=protocol.bootstrap_resamples, quantile='linear'))
