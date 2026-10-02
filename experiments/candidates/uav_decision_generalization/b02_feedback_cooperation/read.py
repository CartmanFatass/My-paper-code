"""Independent actual-history source reconstruction; no native environment queries."""
import json
from pathlib import Path
import time
import numpy as np
import torch
from experiments.candidates.uav_fleet_adaptation.b02 import controllers as inherited
from . import contract as c,io,metrics


def equal(actual,expected,label,atol=0.):
    a,b=np.asarray(actual),np.asarray(expected)
    if a.shape!=b.shape or not (np.allclose(a,b,rtol=0,atol=atol) if atol else np.array_equal(a,b)):
        raise AssertionError(label)


def native(raw,h):
    d=h//4*5
    shapes={'observations':(h,5,104),'terminal_observation':(5,104),'commands':(h,5,3),'positions':(h+1,5,3),
            'initial_users':(50,2),'reward':(h,),'served':(h,),'sinr_quality':(h,),'sinr':(h,5,50),
            'uav_sinr':(h,5,5),'initial_uav_sinr':(5,5),'connections':(h,5,50),'user_service_mask':(h,50),'transmitter_mask':(h,5),'online_q':(h,5),
            'terminated':(h,),'truncated':(h,),'initial_sinr':(5,50),'initial_connections':(5,50),
            'features':(d,114),'probabilities':(d,27),'policy_scores':(d,27),'policy_served':(d,27),'logits':(d,27)}
    for key in ('decision_ticks','decision_agents','source','takeover','nav_pre','nav_next','fallback','action_index','memo_hit','n_current','n_peers','innovation','entropy','c_index'):shapes[key]=(d,)
    if set(raw)!=set(shapes):raise AssertionError('complete raw schema changed')
    for key,shape in shapes.items():
        if raw[key].shape!=shape or (key!='source' and not np.isfinite(raw[key]).all()):raise AssertionError('raw shape/value: '+key)
    fp32=('observations','terminal_observation','commands','features','logits')
    fp64=('positions','initial_users','reward','sinr_quality','sinr','initial_sinr','uav_sinr','initial_uav_sinr','probabilities','innovation','entropy','policy_scores','policy_served')
    bools=('connections','initial_connections','user_service_mask','transmitter_mask','takeover','fallback','memo_hit','terminated','truncated')
    for keys,dtype in ((fp32,np.float32),(fp64,np.float64),(bools,np.bool_)):
        for key in keys:
            if raw[key].dtype!=dtype:raise AssertionError('raw dtype: '+key)
    for key in ('served','decision_ticks','decision_agents','nav_pre','nav_next','action_index','n_current','n_peers','c_index','online_q'):
        if not np.issubdtype(raw[key].dtype,np.integer):raise AssertionError('integer raw dtype: '+key)
    if not raw['transmitter_mask'].all() or raw['truncated'].any():raise AssertionError('all-on/truncation invariant')
    equal(raw['terminated'],np.arange(h)==h-1,'full mission termination')
    equal(raw['positions'][1:],np.clip(raw['positions'][:-1]+30*raw['commands'].astype(np.float64),(0,0,50),(1000,1000,150)),'native clipped geometry')
    xyz=raw['positions'].copy();xyz[...,:2]/=1000;xyz[...,2]=(xyz[...,2]-50)/100
    observations=np.concatenate((raw['observations'],raw['terminal_observation'][None]),axis=0)
    equal(observations[...,:3],xyz.astype(np.float32),'all257 own poses')
    equal(observations[...,-1],np.broadcast_to((np.arange(h+1)/h).astype(np.float32)[:,None],(h+1,5)),'all257 clocks')
    sinr=np.concatenate((raw['initial_sinr'][None],raw['sinr']),axis=0)
    connections=np.concatenate((raw['initial_connections'][None],raw['connections']),axis=0)
    if (np.any(connections.sum(1)>1) or np.any(connections.sum(2)>10) or np.any(sinr[connections]<3)
            or np.any((sinr>=3).sum(1)>1)):raise AssertionError('native uniqueness/capacity/eligibility')
    equal(connections.sum(2),np.minimum(10,(sinr>=3).sum(2)),'native eligible count at capacity')
    slots=np.count_nonzero(observations[...,3:63].reshape(h+1,5,20,3)[...,2]>0,axis=-1)
    equal(slots,np.minimum(20,(sinr>=3).sum(2)),'local slot count provenance')
    q=np.minimum(10,slots);equal(q,connections.sum(2),'all257 q/native own count')
    equal(raw['user_service_mask'],raw['connections'].any(1),'all50 service mask')
    served=raw['connections'].sum((1,2));equal(raw['served'],served,'native served users')
    quality=np.where(raw['connections'],np.clip((raw['sinr']-3)/30,0,1),0).sum((1,2))/np.maximum(served,1)
    equal(raw['sinr_quality'],quality,'served-user native quality',1e-14)
    equal(raw['reward'],.7*served/50+.3*quality,'native original reward',1e-12)
    # Reconstruct local user and visible-peer coordinates/order from the original observation rules.
    users=raw['initial_users'];peer_sinr=np.concatenate((raw['initial_uav_sinr'][None],raw['uav_sinr']),axis=0)
    for tick in range(h+1):
        for agent in range(5):
            row=observations[tick,agent];own=raw['positions'][tick,agent]
            candidates=np.flatnonzero(sinr[tick,agent]>=3)
            order=candidates[np.argsort(-sinr[tick,agent,candidates],kind='stable')][:20]
            entries=np.zeros((20,3),dtype=np.float32)
            if len(order):
                entries[:len(order),:2]=(users[order]-own[:2])/1000
                entries[:len(order),2]=np.clip((sinr[tick,agent,order]+10)/50,0,1)
            equal(row[3:63].reshape(20,3),entries,'visible user coordinates/SINR/order')
            eligible=np.flatnonzero(peer_sinr[tick,agent]>=3);eligible=eligible[eligible!=agent]
            order=eligible[np.argsort(-peer_sinr[tick,agent,eligible],kind='stable')][:10]
            peers=np.zeros((10,4),dtype=np.float32)
            if len(order):
                peers[:len(order),:2]=(raw['positions'][tick,order,:2]-own[:2])/1000
                peers[:len(order),2]=(raw['positions'][tick,order,2]-own[2])/100
                peers[:len(order),3]=np.clip((peer_sinr[tick,agent,order]+10)/50,0,1)
            equal(row[63:103].reshape(10,4),peers,'visible peer coordinates/SINR/order')
    return q


def source_c(controller,row,tick,nav):
    controller._nav_index=int(nav)
    command,diag=controller.act(row,int(tick))
    return {'action_index':int(diag['selected_index']),'next_nav':int(controller._nav_index),'fallback':bool(diag['fallback']),
            'scores':diag['scores'],'served':diag['served_candidates'],'command':command,
            'n_current':int(diag['n_current']),'n_peers':int(diag['n_visible_peers']),
            'features':inherited._features(row,int(nav),diag['fallback'])}


def source_s(actor,row,nav):
    result=inherited.analyze(row,int(nav))
    with torch.inference_mode():result['logits']=actor(torch.from_numpy(result['features']).reshape(1,114))[0].cpu().numpy().copy()
    return result


def probabilities(source,base):
    if source in ('C','G'):
        p=np.full(27,0. if source=='C' else .1/26,dtype=np.float64);p[base['action_index']]=1. if source=='C' else .9
        scores=base['scores']
        if source=='G' and not np.all(scores==scores[0]):
            others=np.arange(27)!=base['action_index'];weights=np.exp((scores[others]-scores[others].max())/.014)
            p[others]=.1*(weights/weights.sum(dtype=np.float64))
        return p
    logits=base['logits'].astype(np.float64)/(2. if source=='Bstar0' else 1.)
    weights=np.exp(logits-logits.max());return weights/weights.sum(dtype=np.float64)


def sample(source,base,p,root,world,tick,agent):
    if source=='C':return -1.,base['action_index']
    u=float(np.random.default_rng(np.random.SeedSequence([int(root),int(world),int(tick),int(agent)])).random())
    cdf=np.cumsum(p,dtype=np.float64);cdf[-1]=1.
    return u,int(np.searchsorted(cdf,u,side='right'))


def clipped_path(position,command):
    xyz=np.asarray(position,dtype=np.float64).copy();path=[]
    for _ in range(4):
        xyz=np.clip(xyz+30*np.asarray(command,dtype=np.float64),(0,0,50),(1000,1000,150));path.append(xyz.copy())
    return np.asarray(path)


def empty_counters(source):
    if source in ('C','G'):counts={key:0 for key in inherited.COUNTER_NAMES}
    else:counts=dict(requests=0,hits=0,misses=0,helper_calls=0,helper_setup_links=0,helper_extreme_links=0,neural_rows=0,sampled_draws=0,cache_entries=0,cache_key_bytes=0,cache_array_bytes=0)
    counts.update(sampled_draws=0,score_tail_evaluations=0);return counts


def check_episode(raw,row,actors,*,horizon=c.HORIZON,c_function=source_c,s_function=source_s,inflight=None):
    h=horizon;arm=row['arm'];parent=c.PARENTS.get(arm,arm)
    work=dict(reader_C_calls=0,reader_S_rows=0,reader_draws=0,reader_G_probabilities=0,reader_count_decodes=(h+1)*5,
              hypothetical_S_rows=0,hypothetical_G_probabilities=0,takeover_comparisons=0,geometric_comparison_steps=0,
              C_trajectories=0,C_model_ticks=0,C_candidate_links=0,C_setup_links=0,C_objective_reductions=0,
              helper_calls=0,helper_setup_links=0,helper_extreme_links=0)
    if inflight is not None:inflight['reader_work']=work
    q=native(raw,h)
    sources=('C',parent) if arm in c.PARENTS else (parent,)
    deployed=[{source:empty_counters(source) for source in sources} for _ in range(5)]
    caches=[{source:set() for source in sources} for _ in range(5)]
    controllers=[{source:inherited.original.LocalController(False) for source in sources if source in ('C','G')} for _ in range(5)]
    nav=[inherited.initial_nav(r) for r in raw['observations'][0]];commands=np.zeros((5,3),dtype=np.float32)
    comparisons=[];index=0
    for tick in range(h):
        equal(raw['online_q'][tick],q[tick] if arm in c.PARENTS else np.full(5,-1),'online switch count exposure')
        if tick%4==0:
            for agent in range(5):
                takeover=arm in c.PARENTS and tick>=4 and bool(np.all(q[tick-3:tick+1,agent]==0))
                source='C' if takeover else parent;observation=raw['observations'][tick,agent]
                equal((raw['decision_ticks'][index],raw['decision_agents'][index]),(tick,agent),'decision address/order')
                equal(raw['source'][index],source,'chosen source');equal(raw['takeover'][index],takeover,'four primitive observations gate')
                equal(raw['nav_pre'][index],nav[agent],'one actual navigation continuity')
                key=observation[:103].tobytes()+bytes([int(nav[agent])]);hit=key in caches[agent][source]
                equal(raw['memo_hit'][index],hit,'private agent/source cache')
                counts=deployed[agent][source];counts['requests']+=1;counts['hits' if hit else 'misses']+=1
                if source in ('C','G'):
                    work['reader_C_calls']+=1
                    base=c_function(controllers[agent][source],observation,tick,nav[agent])
                    equal(raw['c_index'][index],base['action_index'],'independent full C category')
                    equal(raw['policy_scores'][index],base['scores'],'independent full C scores')
                    equal(raw['policy_served'][index],base['served'],'independent full C served')
                    equal(raw['logits'][index],np.zeros(27,dtype=np.float32),'no unused actor record')
                    for k,v in dict(C_trajectories=27,C_model_ticks=108,C_candidate_links=108*base['n_current'],C_setup_links=(1+base['n_peers'])*base['n_current'],C_objective_reductions=108).items():work[k]+=v
                else:
                    work['reader_S_rows']+=1;base=s_function(actors[1 if source=='SL1' else 0],observation,nav[agent])
                    equal(raw['logits'][index],base['logits'],'independent one-row actor')
                    equal(raw['c_index'][index],-1,'no unused C category')
                    equal(raw['policy_scores'][index],np.zeros(27),'no unused C scores')
                    equal(raw['policy_served'][index],np.zeros(27),'no unused C served')
                    for k,v in base['counters'].items():work[k]+=v
                for key_name in ('features','fallback','n_current','n_peers'):equal(raw[key_name][index],base[key_name],'source binding: '+key_name)
                if not hit:
                    caches[agent][source].add(key);counts['cache_entries']+=1;counts['cache_key_bytes']+=len(key)
                    if source in ('C','G'):
                        for k,v in dict(trajectories=27,model_ticks=108,candidate_links=108*base['n_current'],setup_links=(1+base['n_peers'])*base['n_current'],objective_reductions=108).items():counts[k]+=v
                        counts['cache_array_bytes']+=sum(base[k].nbytes for k in ('command','scores','served','features'))
                    else:
                        for k,v in base['counters'].items():counts[k]+=v
                        counts['neural_rows']+=1;counts['cache_array_bytes']+=base['features'].nbytes+base['logits'].nbytes
                p=probabilities(source,base);u,choice=sample(source,base,p,row['sampling_root'],row['world'],tick,agent)
                work['reader_draws']+=int(source!='C');work['reader_G_probabilities']+=int(source=='G')
                counts['sampled_draws']+=int(source!='C');counts['score_tail_evaluations']+=int(source=='G')
                equal(raw['probabilities'][index],p,'independent probabilities');equal(raw['innovation'][index],u,'actual addressed draw')
                equal(raw['action_index'][index],choice,'original CDF category')
                positive=p>0;equal(raw['entropy'][index],float(-np.sum(p[positive]*np.log(p[positive]))),'entropy')
                if takeover:
                    work['takeover_comparisons']+=1;work['geometric_comparison_steps']+=4
                    if parent=='G':
                        hypothetical=base;work['reader_G_probabilities']+=1;work['hypothetical_G_probabilities']+=1
                    else:
                        hypothetical=s_function(actors[1 if parent=='SL1' else 0],observation,nav[agent])
                        work['reader_S_rows']+=1;work['hypothetical_S_rows']+=1
                        for k,v in hypothetical['counters'].items():work[k]+=v
                    hp=probabilities(parent,hypothetical);hu,hchoice=sample(parent,hypothetical,hp,row['sampling_root'],row['world'],tick,agent)
                    work['reader_draws']+=1
                    equal(hypothetical['next_nav'],base['next_nav'],'q0 chosen/hypothetical next nav')
                    equal(base['n_current'],0,'takeover empty users')
                    equal(base['scores'],np.zeros(27),'original C empty full calculation')
                    equal(base['served'],np.zeros(27),'original C empty service calculation')
                    actual_path=clipped_path(raw['positions'][tick,agent],inherited.COMMANDS[choice])
                    parent_path=clipped_path(raw['positions'][tick,agent],inherited.COMMANDS[hchoice])
                    following=q[tick+1:tick+5,agent];positive_tick=np.flatnonzero(following>0)
                    comparisons.append({'tick':tick,'agent':agent,'parent':parent,'category_changed':choice!=hchoice,
                                        'motion_changed':not np.array_equal(actual_path,parent_path),'actual_category':choice,'parent_category':hchoice,
                                        'parent_uniform':hu,'parent_probabilities':hp.tolist(),
                                        'actual_four_step_path':actual_path.tolist(),'parent_four_step_path':parent_path.tolist(),
                                        'following_H4_own_counts':following.tolist(),
                                        'first_regained_contact_offset':int(positive_tick[0])+1 if len(positive_tick) else None,
                                        'continued_zero_length':int(positive_tick[0]) if len(positive_tick) else len(following)})
                nav[agent]=int(base['next_nav']);equal(raw['nav_next'][index],nav[agent],'one chosen nav update')
                commands[agent]=inherited.COMMANDS[choice];index+=1
        equal(raw['commands'][tick],commands,'original H4 commitment')
    equal(index,h//4*5,'complete decision count')
    if deployed!=row['policy_counts']:raise AssertionError('deployed cache/source work counts')
    equal(row['online_count_decodes'],h*5 if arm in c.PARENTS else 0,'online count decoder work')
    equal(row['online_gate_checks'],(h//4-1)*5 if arm in c.PARENTS else 0,'online gate checks')
    if metrics.episode_metrics(raw)!=row['metrics']:raise AssertionError('complete native/service metric reductions')
    equal(row['initial_state_sha256'],c.initial_state_digest(raw['positions'][0],raw['initial_users'],raw['initial_sinr'],raw['initial_uav_sinr'],raw['initial_connections']),'initial state binding')
    return {'spec':{k:row[k] for k in ('phase','world','arm','tape','sampling_root')},'work':work,'takeover_comparisons':comparisons,'new_native_steps':0}
