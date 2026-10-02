"""All50-user mission gaps and task/native/travel reductions from saved records."""
import numpy as np


def zero_runs(mask):
    mask=np.asarray(mask,dtype=bool);runs=[];start=None
    for tick,served in enumerate(np.r_[mask,True]):
        if not served and start is None:start=tick
        if served and start is not None:
            runs.append({'start':start,'stop':tick,'length':tick-start,'left_censored':start==0,'right_censored':tick==len(mask)});start=None
    return runs


def all_user_service(mask):
    mask=np.asarray(mask)
    if mask.shape!=(500,50) or mask.dtype!=np.bool_:raise ValueError('all500 post-state, all50 user masks')
    users=[]
    for user in range(50):
        m=mask[:,user];gaps=zero_runs(m)
        users.append({'user':user,'served_ticks':int(m.sum()),'served_fraction':float(m.mean()),'longest_gap':max((r['length'] for r in gaps),default=0),
                      'leading_gap':gaps[0]['length'] if gaps and gaps[0]['left_censored'] else 0,
                      'trailing_gap':gaps[-1]['length'] if gaps and gaps[-1]['right_censored'] else 0,'zero_runs':gaps,
                      'closed_internal_zero_lengths':[r['length'] for r in gaps if not r['left_censored'] and not r['right_censored']]})
    fractions=np.array([u['served_fraction'] for u in users]);gaps=np.array([u['longest_gap'] for u in users])
    return {'users':users,'never_served_users':int((fractions==0).sum()),'never_served_fraction':float((fractions==0).mean()),
            'user_served_fraction_p10':float(np.quantile(fractions,.1)),'user_served_fraction_min':float(fractions.min()),
            'mean_user_longest_gap':float(gaps.mean()),'p90_user_longest_gap':float(np.quantile(gaps,.9)),'max_user_longest_gap':int(gaps.max())}


def mission(raw):
    mask=raw['routed_user_mask'];served=mask.sum(axis=1);zero=served==0;motion=np.diff(raw['positions'],axis=0)
    return {'W':float(raw['payment'].sum()),'window_fraction':float(raw['payment'].sum()/4),
            'payments_per_window':[float(raw['payment'][j*125:(j+1)*125].sum()) for j in range(4)],
            'J_dense':float(raw['dense_reward'].mean()),'mean_served':float(served.mean()),'p10_served':float(np.quantile(served,.1)),'min_served':int(served.min()),
            'team_zero_ticks':int(zero.sum()),'longest_team_zero_run':max((r['length'] for r in zero_runs(~zero)),default=0),
            'mean_path_length_m':float(np.linalg.norm(motion,axis=-1).sum(axis=0).mean()),
            'zero_displacement_uav_ticks':int(np.all(motion==0,axis=-1).sum()),'clip_events':int(raw['action_clip_events'].sum()),
            'coverage_backhauled':float(raw['coverage_backhauled'].mean()),'throughput_term':float(raw['throughput_term'].mean()),
            'all_user_service':all_user_service(mask)}
