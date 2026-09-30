"""Evaluator-only gate exposure and actual completion; never imported by actor."""

import numpy as np

from experiments.candidates.uav_radio_activation.b03.protocol import DELIVERY, HOLD


def add_gate_raw(raw, steps):
    """Truth at report t and at arrival t+2 have separate, explicit boundaries."""
    rounds = len(raw['gate_computed'])
    actual = raw['connections'][:steps].any(axis=1)
    fields = ('gate_actual_report_bits', 'gate_actual_prefix_bits',
              'gate_actual_window_bits', 'gate_model_window_bits')
    for name in fields:
        raw[name] = np.zeros((rounds, 50), dtype=bool)
    raw['gate_model_window_valid'] = np.zeros(rounds, dtype=bool)
    raw['gate_timely_executed'] = raw['gate_released'] & raw['timely']
    raw['gate_executed_transitions'] = np.zeros(rounds, dtype=int)
    raw['gate_command_changed'] = np.zeros(rounds, dtype=bool)
    raw['gate_mask_changed'] = np.zeros(rounds, dtype=bool)
    for index in range(int(raw['round_count'])):
        tick = int(raw['round_tick'][index])
        if not raw['gate_computed'][index]:
            continue
        window = int(raw['gate_window'][index])
        start, end = window * 64, min((window + 1) * 64, steps)
        raw['gate_actual_report_bits'][index] = actual[start:min(tick, end)].any(axis=0)
        raw['gate_actual_prefix_bits'][index] = actual[start:min(tick + DELIVERY, end)].any(axis=0)
        raw['gate_actual_window_bits'][index] = actual[start:end].any(axis=0)
        raw['gate_model_window_bits'][index] = raw['model_contacts'][start:end].any(axis=0)
        raw['gate_model_window_valid'][index] = bool(end > start and raw['model_valid'][start:end].all())
        if raw['gate_timely_executed'][index]:
            raw['gate_executed_transitions'][index] = max(0, min(HOLD, steps - tick - DELIVERY))
            raw['gate_command_changed'][index] = bool(np.any(raw['commitments'][index] != raw['proposals'][tick]))
            raw['gate_mask_changed'][index] = raw['applied_mask'][index] != raw['mask'][tick]


def gate_metrics(raw, steps):
    computed = raw['gate_computed']
    eligible = raw['gate_eligible']
    released = raw['gate_released']
    timely = raw['gate_timely_executed']
    actual_prefix_complete = raw['gate_actual_prefix_bits'].all(axis=1)
    actual_window_complete = raw['gate_actual_window_bits'].all(axis=1)
    model_complete = np.zeros(len(computed), dtype=bool)
    for index in np.flatnonzero(computed):
        model_complete[index] = raw['prefix_windows'][index, int(raw['gate_window'][index])].all()
    # Count missing users as well as false whole-window completion at release.
    later_losses = []
    for window in range((steps + 63) // 64):
        indices = released & (raw['gate_window'] == window)
        following = raw['actual_window_bits'][window + 1] if window + 1 < len(raw['actual_window_bits']) else None
        later_losses.append(dict(window=window, released_rounds=int(indices.sum()),
                                 timely_executed_rounds=int((indices & timely).sum()),
                                 actual_covered_users=int(raw['actual_window_bits'][window].sum()),
                                 next_window_covered_users=None if following is None else int(following.sum()),
                                 next_window_missing_users=None if following is None else int((~following).sum())))
    return dict(gate_computed_rounds=int(computed.sum()), gate_eligible_rounds=int(eligible.sum()),
                gate_released_rounds=int(released.sum()), gate_timely_executed_rounds=int(timely.sum()),
                gate_released_late_rounds=int((released & ~timely).sum()),
                gate_executed_transitions=int(raw['gate_executed_transitions'].sum()),
                gate_command_changed_rounds=int(raw['gate_command_changed'].sum()),
                gate_mask_changed_rounds=int(raw['gate_mask_changed'].sum()),
                gate_action_effect_scope='timely released commands versus current C proposals; masks versus prearrival executed mask; no same-input alternate-O comparison',
                gate_wall_seconds=float(raw['gate_wall'].sum()), gate_cpu_seconds=float(raw['gate_cpu'].sum()),
                gate_prefix_false_releases=int((released & ~actual_prefix_complete).sum()),
                gate_timely_prefix_false_releases=int((timely & ~actual_prefix_complete).sum()),
                gate_release_prefix_missing_user_events=int((~raw['gate_actual_prefix_bits'][released]).sum()),
                gate_eligible_prefix_completion_false_positive=int((eligible & model_complete & ~actual_prefix_complete).sum()),
                gate_eligible_prefix_completion_false_negative=int((eligible & ~model_complete & actual_prefix_complete).sum()),
                gate_release_actual_report_complete_rounds=int((released & raw['gate_actual_report_bits'].all(axis=1)).sum()),
                gate_release_actual_window_incomplete_rounds=int((released & ~actual_window_complete).sum()),
                gate_windows=later_losses,
                gate_truth_scope='evaluator only: report t excludes transition t; arrival t+2 includes committed transitions t,t+1; full window after episode')
