"""Native fixed-H4 collection; privileged records never enter a program."""
from pathlib import Path
import time
import numpy as np
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS
from experiments.candidates.uav_local_history.b01.study import native_reading
from . import contract as c,io,metrics
from .policy import AgentProgram


def all_on(env):
    mask=np.asarray(env.env.transmitter_mask)
    if mask.shape!=(5,) or mask.dtype!=np.bool_ or not mask.all():raise AssertionError('original all-on host changed')
    return mask.copy()


def episode(env,spec,actors,out,counts,inflight,*,horizon=c.HORIZON,program_factory=AgentProgram):
    wall,cpu=time.perf_counter(),time.process_time()
    times={name+'_'+clock+'_seconds':0. for name in ('reset','gate_query','native_step','raw_write') for clock in ('wall','cpu')}
    target=Path(out)/'raw'/spec['phase']/f"{spec['arm']}_{spec['world']}_t{spec['tape']}.npz"
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists() or target.with_suffix('.partial.npz').exists():raise FileExistsError('no episode retry')
    raw={k:[] for k in ('observations','commands','positions','reward','served','sinr_quality','sinr','uav_sinr','connections','user_service_mask','transmitter_mask','terminated','truncated','online_q')}
    decisions={k:[] for k in ('decision_ticks','decision_agents','source','takeover','nav_pre','nav_next','features','fallback','action_index','memo_hit','n_current','n_peers','probabilities','innovation','entropy','c_index','policy_scores','policy_served','logits')}
    obs=users=initial_sinr=initial_uav_sinr=initial_connections=None;programs=[]
    inflight.update(**spec,tick=0,native_steps=0)
    try:
        t0,t1=time.perf_counter(),time.process_time();counts['explicit_resets']=counts.get('explicit_resets',0)+1
        obs,info=env.reset(seed=spec['world']);times['reset_wall_seconds']+=time.perf_counter()-t0;times['reset_cpu_seconds']+=time.process_time()-t1
        obs=np.asarray(obs,dtype=np.float32)
        if obs.shape!=(5,104) or not np.isfinite(obs).all():raise ValueError('five finite original local rows required')
        all_on(env)
        positions=np.array(info['state_info']['uav_positions'],dtype=np.float64,copy=True)
        users=np.array(info['state_info']['user_positions'],dtype=np.float64,copy=True)
        initial_sinr=np.array(env.env.sinr_matrix,dtype=np.float64,copy=True);initial_connections=np.array(env.env.connections,dtype=bool,copy=True);initial_uav_sinr=np.array(env.env.uav_sinr_matrix,dtype=np.float64,copy=True)
        raw['positions'].append(positions.copy())
        root=spec['sampling_root'] if spec['sampling_root'] is not None else c.AUDIT_ROOT if spec['phase']=='audit' else c.SAMPLING_ROOTS[0]
        programs=[program_factory(spec['arm'],row,world=spec['world'],agent=i,sampling_root=root,actors=actors) for i,row in enumerate(obs)]
        for tick in range(horizon):
            inflight['tick']=tick
            t0,t1=time.perf_counter(),time.process_time()
            qs=[]
            for agent,program in enumerate(programs):
                pd=program.step(obs[agent],tick);qs.append(program.switch.window[-1] if spec['arm'] in c.PARENTS else -1)
                if pd is None:continue
                answer=pd['answer'];source=pd['source']
                if not np.array_equal(answer['command'],COMMANDS[answer['action_index']]):raise AssertionError('original command/category changed')
                custom={'decision_ticks':tick,'decision_agents':agent,'source':source,'takeover':pd['takeover'],'nav_pre':pd['nav_pre'],'nav_next':answer['next_nav'],
                        'c_index':answer.get('c_index',-1),'policy_scores':answer.get('scores',np.zeros(27,dtype=np.float64)),
                        'policy_served':answer.get('served',np.zeros(27,dtype=np.float64)),
                        'logits':answer.get('logits',np.zeros(27,dtype=np.float32))}
                for key in decisions:decisions[key].append(custom[key] if key in custom else answer[key])
            times['gate_query_wall_seconds']+=time.perf_counter()-t0;times['gate_query_cpu_seconds']+=time.process_time()-t1
            commands=np.asarray([p.command for p in programs],dtype=np.float32)
            raw['observations'].append(obs.copy());raw['commands'].append(commands.copy());raw['online_q'].append(qs)
            raw['transmitter_mask'].append(all_on(env))
            t0,t1=time.perf_counter(),time.process_time();counts['native_step_calls']=counts.get('native_step_calls',0)+1
            next_obs,_,terminated,truncated,next_info=env.step(commands.copy())
            counts['native_steps']=counts.get('native_steps',0)+1;inflight['native_steps']+=1
            times['native_step_wall_seconds']+=time.perf_counter()-t0;times['native_step_cpu_seconds']+=time.process_time()-t1
            reward,served,quality=native_reading(next_info)
            after=np.array(next_info['state_info']['uav_positions'],dtype=np.float64,copy=True)
            if not np.array_equal(after,np.clip(positions+30*commands.astype(np.float64),(0,0,50),(1000,1000,150))):raise AssertionError('native per-coordinate motion changed')
            if not np.array_equal(users,next_info['state_info']['user_positions']):raise AssertionError('static user identity changed')
            if bool(terminated)!=(tick+1==horizon) or bool(truncated):raise AssertionError('original termination/truncation changed')
            global_info=next_info['infos_dict']['uav_0']['global'];connections=np.array(global_info['connections'],dtype=bool,copy=True)
            for key,value in {'positions':after,'reward':reward,'served':served,'sinr_quality':quality,
                              'sinr':np.array(global_info['sinr_matrix'],dtype=np.float64,copy=True),'uav_sinr':np.array(env.env.uav_sinr_matrix,dtype=np.float64,copy=True),'connections':connections,
                              'user_service_mask':connections.any(axis=0),'terminated':bool(terminated),'truncated':bool(truncated)}.items():raw[key].append(value)
            obs=np.asarray(next_obs,dtype=np.float32);positions=after
            if obs.shape!=(5,104) or not np.isfinite(obs).all():raise AssertionError('invalid next observation')
        arrays={k:np.asarray(v) for k,v in {**raw,**decisions}.items()}
        arrays.update(initial_users=users,initial_sinr=initial_sinr,initial_uav_sinr=initial_uav_sinr,initial_connections=initial_connections,terminal_observation=obs.copy())
        t0,t1=time.perf_counter(),time.process_time();np.savez_compressed(target,**arrays)
        file=io.identity(target);file['path']=str(target.relative_to(out))
        times['raw_write_wall_seconds']+=time.perf_counter()-t0;times['raw_write_cpu_seconds']+=time.process_time()-t1
        row={**spec,'raw':file,'metrics':metrics.episode_metrics(arrays),'times':times,
             'policy_counts':[p.counters() for p in programs],
             'online_count_decodes':sum(p.switch.count_decodes for p in programs),
             'online_gate_checks':sum(p.switch.gate_checks for p in programs),
             'initial_state_sha256':c.initial_state_digest(arrays['positions'][0],users,initial_sinr,initial_uav_sinr,initial_connections),
             'episode_cpu_seconds':time.process_time()-cpu,'episode_wall_seconds':time.perf_counter()-wall,
             'process_peak_rss_kib':io.resource.getrusage(io.resource.RUSAGE_SELF).ru_maxrss}
        counts['episodes']=counts.get('episodes',0)+1;inflight.clear()
        return row
    except BaseException:
        arrays={k:np.asarray(v) for k,v in {**raw,**decisions}.items()}
        for key,value in (('initial_users',users),('initial_sinr',initial_sinr),('initial_uav_sinr',initial_uav_sinr),('initial_connections',initial_connections),('last_observation',obs)):
            if value is not None:arrays[key]=value
        partial=target.with_suffix('.partial.npz');np.savez_compressed(partial,**arrays)
        inflight.update(partial_raw=io.identity(partial),policy_counts=[p.counters() for p in programs],times=times)
        raise
