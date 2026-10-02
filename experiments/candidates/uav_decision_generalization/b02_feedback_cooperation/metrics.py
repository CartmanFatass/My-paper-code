"""Complete post-transition service and mission-boundary-censored user gaps."""
import numpy as np
from . import contract as c


def zero_runs(mask):
    mask=np.asarray(mask,dtype=bool)
    runs=[];start=None
    for tick,served in enumerate(np.r_[mask,True]):
        if not served and start is None:start=tick
        if served and start is not None:
            runs.append({'start':start,'stop':tick,'length':tick-start,'left_censored':start==0,'right_censored':tick==len(mask)})
            start=None
    return runs


def user_service(masks):
    masks=np.asarray(masks)
    if masks.ndim!=2 or masks.shape[1]!=50 or masks.dtype!=np.bool_:raise ValueError('full all50-user boolean mask required')
    h=len(masks);users=[]
    for i in range(50):
        m=masks[:,i];runs=zero_runs(m)
        users.append({'user':i,'served_ticks':int(m.sum()),'served_fraction':float(m.mean()),
                      'longest_gap':max((r['length'] for r in runs),default=0),
                      'leading_gap':runs[0]['length'] if runs and runs[0]['left_censored'] else 0,
                      'trailing_gap':runs[-1]['length'] if runs and runs[-1]['right_censored'] else 0,
                      'zero_runs':runs,'closed_internal_zero_lengths':[r['length'] for r in runs if not r['left_censored'] and not r['right_censored']]})
    fractions=np.array([r['served_fraction'] for r in users]);gaps=np.array([r['longest_gap'] for r in users])
    return {'users':users,'never_served_users':int((fractions==0).sum()),'never_served_fraction':float((fractions==0).mean()),
            'user_served_fraction_p10':float(np.quantile(fractions,.1)),'user_served_fraction_min':float(fractions.min()),
            'mean_user_longest_gap':float(gaps.mean()),'p90_user_longest_gap':float(np.quantile(gaps,.9)),
            'max_user_longest_gap':int(gaps.max())}


def episode_metrics(raw):
    served=raw['served'];position=raw['positions'][1:];motion=np.diff(raw['positions'],axis=0)
    zero=served==0;service=user_service(raw['user_service_mask'])
    return {'J':float(raw['reward'].mean()),'return_sum':float(raw['reward'].sum()),'mean_served':float(served.mean()),
            'service_p10':float(np.quantile(served,.1)),'min_served':int(served.min()),'team_zero_ticks':int(zero.sum()),
            'longest_team_zero_run':max((r['length'] for r in zero_runs(~zero)),default=0),
            'first_segment_team_zero_ticks':int(zero[:4].sum()),'subsequent_team_zero_ticks':int(zero[4:].sum()),
            'coverage_reward':float((.7*served/50.).mean()),'quality_reward':float((.3*raw['sinr_quality']).mean()),
            'mean_sinr_quality':float(raw['sinr_quality'].mean()),
            'mean_path_length_m':float(np.linalg.norm(motion,axis=-1).sum(axis=0).mean()),
            'xy_boundary_uav_steps':int(np.any((position[...,:2]==0)|(position[...,:2]==1000),axis=-1).sum()),
            'lower_altitude_uav_steps':int((position[...,2]==50).sum()),
            'zero_displacement_uav_ticks':int(np.all(motion==0,axis=-1).sum()),
            'takeovers':int(raw['takeover'].sum()),'queries':len(raw['decision_ticks']),
            'fallback_decisions':int(raw['fallback'].sum()),'policy_cache_hits':int(raw['memo_hit'].sum()),
            'mean_entropy':float(raw['entropy'].mean()),
            **{k:v for k,v in service.items() if k!='users'},'user_service':service['users']}


def sample(values,indices):
    values=np.asarray(values,dtype=np.float64);means=values[indices].mean(axis=1)
    return {'mean':float(values.mean()),'p95':np.quantile(means,[.025,.975]).tolist(),
            'world_values':values.tolist(),'positive':int((values>0).sum()),'negative':int((values<0).sum()),'zero':int((values==0).sum())}


def comparisons(rows):
    expected={(x['arm'],x['world'],x['tape']) for x in c.episode_order('main')}
    by_key={(r['arm'],r['world'],r['tape']):r for r in rows}
    if set(by_key)!=expected or len(by_key)!=len(rows):raise ValueError('incomplete fixed main panel')
    fields=[k for k,v in rows[0]['metrics'].items() if isinstance(v,(float,int))]
    fields+=['episode_cpu_seconds','episode_wall_seconds']
    def value(row,field):return row[field] if field.endswith('_seconds') else row['metrics'][field]
    arrays={arm:{field:np.asarray([np.mean([value(by_key[arm,w,t],field) for t in ((-1,) if arm=='C' else (0,1))]) for w in c.WORLDS]) for field in fields} for arm in c.ARMS}
    indices=np.random.default_rng(c.BOOTSTRAP_SEED).integers(0,32,size=(10000,32))
    primary=[('ZSL0','SL0'),('ZSL1','SL1'),('ZSL0','ZG'),('ZSL1','ZG')]
    # Store the28 unordered comparisons once in canonical orientation; primary views explicit.
    canonical={later+'-'+earlier:{field:sample(arrays[later][field]-arrays[earlier][field],indices) for field in fields}
               for i,earlier in enumerate(c.ARMS) for later in c.ARMS[i+1:]}
    primary_reads={left+'-'+right:{field:sample(arrays[left][field]-arrays[right][field],indices) for field in fields} for left,right in primary}
    interactions={z+'-parent-minus-ZG-G':{field:sample((arrays[z][field]-arrays[parent][field])-(arrays['ZG'][field]-arrays['G'][field]),indices) for field in fields} for z,parent in (('ZSL0','SL0'),('ZSL1','SL1'))}
    return {'levels':{arm:{field:sample(values,indices) for field,values in table.items()} for arm,table in arrays.items()},
            'all28_pairs':canonical,'primary':primary_reads,'interactions':interactions,
            'worlds':list(c.WORLDS),'bootstrap_seed':c.BOOTSTRAP_SEED,'bootstrap_resamples':10000,
            'scope':'two tapes averaged within world; C once;32 conditional worlds, two fixed learned assets; no counterfactual reward or training replication'}
