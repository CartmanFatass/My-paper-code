"""Independent label, sampling, CPU scorer, native and control evidence reading."""
from __future__ import annotations
import hashlib
import itertools
import json
import math
import time
from . import contract as c, evidence as e, bank, functional, model
from .native import SERIES, state, rng_identity
from .planner_reader import assignment
from .shortlist import select_menu


def exact(a,b,name,diagnostics):
    okay=e.encoded(a)==e.encoded(b)
    diagnostics.append({'check':name,'passed':okay,'comparison':'exact discrete/serialized identity'})
    if not okay:
        raise AssertionError('exact identity mismatch: '+name)


def close(a,b,name,diagnostics,atol=1e-10,rtol=1e-10,fatal=True):
    import numpy as np
    a,b=np.asarray(a),np.asarray(b)
    okay=a.shape==b.shape and bool(np.allclose(a,b,atol=atol,rtol=rtol,equal_nan=False))
    maximum=float(np.max(np.abs(a.astype(float)-b.astype(float)))) if a.shape==b.shape and a.size else None
    diagnostics.append({'check':name,'passed':okay,'max_abs_error':maximum,'atol':atol,'rtol':rtol,'fatal':fatal})
    if not okay and fatal:
        raise AssertionError('numeric reconstruction mismatch: '+name)
    return okay


def world_gate(decision,record,diagnostics):
    for key in ('world','initial_positions_xyz','user_positions_xy','bs_xyz'):
        exact(decision[key],record['identity'][key],f'{decision["world"]}/{decision["arm"]} world {key}',diagnostics)
    exact(decision['construction_identity'],record['identity'],'constructor world/RNG/agents/mask',diagnostics)
    reset=decision['reset_identity']
    for key in ('native_rng_sha256','agents','transmitter_mask'):
        exact(reset[key],record['identity'][key],'execution reset '+key,diagnostics)
    exact(reset['state']['current_step'],0,'full reset step',diagnostics)
    exact(reset['state']['positions_xyz'],record['identity']['initial_positions_xyz'],'full reset initial pose',diagnostics)
    if decision['arm']!='P':
        exact(decision['feature_sha256'],hashlib.sha256(e.encoded(bank.features(record))).hexdigest(),'complete raw feature bytes',diagnostics)
        exact(decision['construction_sha256'],hashlib.sha256(e.encoded(record['construction'])).hexdigest(),'raw construction/RNG/metadata',diagnostics)
        i=decision['chosen_raw_index']
        exact(decision['positions_xyz'],record['layouts_xyz'][i],'chosen original raw row',diagnostics)


def rebuild_bank(store,native,view,diagnostics):
    import numpy as np
    start,count=(c.TRAIN_START,c.TRAIN_COUNT) if view.split=='train' else (c.FRESH_START,c.FRESH_COUNT)
    for offset in range(0,count,64):
        rebuilt=[];checks=[]
        partial=e.relative_path(store.root,f'raw/label-reader/{view.split}/{offset//64:04d}-partial.jsonl.gz')
        journal=e.Trace(partial,store.bill)
        try:
            for world in range(start+offset,start+min(offset+64,count)):
                record=view.load(world)
                env,identity,raw,f,construction,_=bank.prepare(native,world)
                exact(identity,record['identity'],'independent label world identity',diagnostics)
                exact(f,bank.features(record),'independent complete raw rows',diagnostics)
                exact(construction,record['construction'],'independent raw metadata/RNG',diagnostics)
                infos=[]
                for i,r in enumerate(raw):
                    info=e.plain(native.host.static_evaluate(env,r['positions_xyz'],allow_a2a=True));infos.append(info)
                    journal.write({'world':world,'raw_index':i,'positions_xyz':r['positions_xyz'],'info':info})
                    numeric=[];saved_numeric=[];numeric_keys=[]
                    for key,value in info.items():
                        expected=record['infos'][i][key]
                        if isinstance(value,(str,bool)):
                            exact(value,expected,'label discrete '+key,diagnostics)
                        else:
                            numeric.append(value);saved_numeric.append(expected);numeric_keys.append(key)
                    close(numeric,saved_numeric,f'{world}/{i} label physical fields '+','.join(numeric_keys),diagnostics)
                rebuilt.extend([[v['contract_reward'],v['coverage_backhauled'],v['frontend_capacity_with_path_mbps']] for v in infos])
                best=max(range(len(infos)),key=lambda i:(infos[i]['contract_reward'],-i))
                exact(best,record['best'],'teacher lower raw-index tie',diagnostics)
                checks.append({'world':world,'M':len(raw),'teacher':best,'attempts':len(raw),'completed':len(raw)})
                store.bill.charge('label_rebuild_worlds')
            e.npz_write(store,f'raw/label-reader/{view.split}/{offset//64:04d}.npz',
                        {'J_C_frontend':np.asarray(rebuilt,dtype=np.float64),'records':np.asarray(e.encoded(checks).decode('ascii'))})
        finally:
            journal.close()
        partial.unlink()
        store.progress('label_reader_'+view.split,completed_worlds=offset+len(checks))


def engineering_checks(store,network,initial,view):
    import numpy as np
    results=[]
    # These eight production and eight CPU contexts are all charged to engineering.
    for world in range(c.TRAIN_START,c.TRAIN_START+4):
        r=view.load(world);f=bank.features(r);reverse=list(reversed(range(len(bank.rewards(r)))))
        a,_=model.score(network,f,store.bill,'engineering');store.bill.charge('engineering_contexts')
        b,_=model.score(network,f,store.bill,'engineering',reverse);store.bill.charge('engineering_contexts')
        fa=functional.score(initial,f,store.bill,'engineering');store.bill.charge('engineering_contexts')
        fb=functional.score(initial,f,store.bill,'engineering',reverse);store.bill.charge('engineering_contexts')
        results.append({'world':world,'production_canonical':a,'production_reverse':b,
                        'functional_canonical':fa,'functional_reverse':fb,'display':functional.compare(a,b),
                        'canonical_CPU_GPU':functional.compare(fa,a),'reverse_CPU_GPU':functional.compare(fb,b)})
    store.write_gzip('raw/engineering/scorers.json.gz',results)


def engineering_static(store,native,view):
    import numpy as np
    records=[]
    for world in range(c.TRAIN_START,c.TRAIN_START+4):
        r=view.load(world);env=native.host.make_host(world,area_size=5000)
        x=np.asarray(r['layouts_xyz'][r['best']],dtype=np.float64)
        orders=[list(range(6)),list(reversed(range(6))),[1,2,3,4,5,0],sorted(range(6),key=lambda i:tuple(x[i]))]
        for order in orders:
            info=e.plain(native.host.static_evaluate(env,x[order],allow_a2a=True))
            records.append({'world':world,'teacher':r['best'],'row_permutation':order,'static':info,
                            'raw_J':r['infos'][r['best']]['contract_reward'],
                            'difference_J':info['contract_reward']-r['infos'][r['best']]['contract_reward'],
                            'scope':'raw-row permutation differences are science, no invariance assumption'})
    store.write_gzip('raw/engineering/static-permutations.json.gz',records)


def learner_movement(final,initial):
    """Independent float64 saved-array subtraction; no learner/optimizer replay."""
    import numpy as np
    if set(final)!=set(initial):
        raise AssertionError('initial/final parameter schema mismatch')
    squares=0.;maximum=0.
    for name in sorted(final):
        convert=lambda v:np.asarray(v.detach().cpu().numpy() if hasattr(v,'detach') else v,dtype=np.float64)
        a,b=convert(final[name]),convert(initial[name])
        if a.shape!=b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
            raise AssertionError('finite compatible parameter arrays required')
        delta=a-b;squares+=float(np.sum(delta*delta));maximum=max(maximum,float(np.max(np.abs(delta))))
    return {'l2':math.sqrt(squares),'max_absolute':maximum}


def gradient_and_movement(row):
    grad=float(row['grad_norm']);movement=row['parameter_movement']
    if (set(movement)!={'l2','max_absolute'}
        or not all(math.isfinite(float(v)) and float(v)>=0 for v in (grad,movement['l2'],movement['max_absolute']))):
        raise AssertionError('invalid saved gradient/movement diagnostic')
    return grad,movement


def read_updates(store,view,fit,checkpoint,final_movement,diagnostics):
    import numpy as np
    # Independent fixed-seed reconstruction; no optimizer or production forward replay.
    order_rng=np.random.default_rng(fit['order_seed']);sub_rng=np.random.default_rng(fit['subset_seed'])
    permutation=[];cursor=0;world_counts=np.zeros(fit['n'],dtype=np.uint32)
    sizes=[len(bank.rewards(view.load(c.TRAIN_START+i))) for i in range(fit['n'])]
    counts=[np.zeros(n,dtype=np.uint32) for n in sizes]
    previous=checkpoint['initial_sha256'];updates=0;sum_kl=0.;gradients=[];movements=[]
    from .training import completed_updates
    for row in completed_updates(e.read_trace(e.relative_path(store.root,f'raw/fit/{fit["id"]}/updates.jsonl.gz'))):
        updates+=1
        gradient,movement=gradient_and_movement(row);gradients.append(gradient);movements.append(movement)
        local=[]
        for _ in range(32):
            if cursor==len(permutation):
                permutation=order_rng.permutation(fit['n']).tolist();cursor=0
            local.append(permutation[cursor]);cursor+=1
        exact(row['worlds'],[c.TRAIN_START+i for i in local],'update continuous-world order',diagnostics)
        if row['update']!=updates or row['fit']!=fit['id'] or row['before_sha256']!=previous or row['finite'] is not True:
            raise AssertionError('update digest/order/finite chain mismatch')
        previous=row['after_sha256']
        for b,i in enumerate(local):
            r=view.load(c.TRAIN_START+i);js=np.asarray(bank.rewards(r))
            best=int(js.argmax())
            if len(js)>16:
                others=[j for j in range(len(js)) if j!=best]
                selected=sorted([best]+sub_rng.choice(np.asarray(others),15,replace=False).tolist())
            else:
                selected=list(range(len(js)))
            padded=selected+[0]*(16-len(selected));mask=[True]*len(selected)+[False]*(16-len(selected))
            exact(row['raw_indices'][b],padded,'best-plus15 uniform raw subset',diagnostics)
            exact(row['valid_mask'][b],mask,'physical-padding mask',diagnostics)
            z=(js[selected]-js[selected].max())/.02;z-=np.log(np.exp(z).sum());q=np.exp(z)
            entropy=-float(np.sum(q*z))
            close(row['target_entropy'][b],entropy,'subset entropy reconstruction',diagnostics)
            close(row['CE'][b]-row['target_entropy'][b],row['KL'][b],'CE-H(q) KL reading',diagnostics,atol=1e-6,rtol=1e-5)
            world_counts[i]+=1
            for j in selected:
                counts[i][j]+=1
        sum_kl+=sum(row['KL'])
        if not all(math.isfinite(v) for name in ('CE','KL','prediction_entropy','subset_regret') for v in row[name]):
            raise AssertionError('nonfinite retained update metrics')
        expected_hash=hashlib.sha256(e.encoded({'worlds':row['worlds'],'ids':row['raw_indices'],'mask':row['valid_mask']})).hexdigest()
        exact(expected_hash,row['subset_identity_sha256'],'update subset digest',diagnostics)
        store.bill.check()
    if updates!=4096 or previous!=checkpoint['final_sha256'] or int(world_counts.sum())!=131072 or np.any(world_counts==0):
        raise AssertionError('complete fit/end state/exposure mismatch')
    for key,value in final_movement.items():
        close(value,movements[-1][key],'independently read final movement '+key,diagnostics)
    relative=f'raw/fit/{fit["id"]}/exposure.npz'
    if relative not in store.files:
        raise ValueError('unbound exposure artifact')
    with np.load(e.relative_path(store.root,relative),allow_pickle=False) as saved:
        exact(world_counts,saved['world_counts'],'all prefix world exposures',diagnostics)
        exact(np.concatenate(counts),saved['candidate_counts'],'all candidates including zero exposures',diagnostics)
        exact(np.concatenate(([0],np.cumsum(sizes))),saved['offsets'],'ragged exposure identity',diagnostics)
    optimizer=checkpoint['optimizer']
    if len(optimizer['param_groups'])!=1:
        raise AssertionError('one fixed optimizer group required')
    group=optimizer['param_groups'][0]
    if (group['lr']!=.001 or group['weight_decay']!=.0001 or tuple(group['betas'])!=(.9,.999)
        or group['eps']!=1e-8 or len(group['params'])!=len(checkpoint['state'])
        or set(optimizer['state'])!=set(group['params'])):
        raise AssertionError('complete fixed final optimizer parameter identity')
    if any(float(v['step'])!=4096 for v in optimizer['state'].values()):
        raise AssertionError('final optimizer step identity mismatch')
    return counts,{'fit':fit,'updates':updates,'world_presentations':int(world_counts.sum()),'mean_stream_KL':sum_kl/(4096*32),
                   'final_parameter_movement':final_movement,
                   'gradient_norms':{'count':len(gradients),'mean':sum(gradients)/len(gradients),
                                     'min':min(gradients),'max':max(gradients),'zero':sum(v==0 for v in gradients)},
                   'observed_movement_l2_range':[min(v['l2'] for v in movements),max(v['l2'] for v in movements)],
                   'never_sampled_candidates':sum(int((v==0).sum()) for v in counts),'optimizer_replay':False,
                   'trust':'bound source/update-chain/final optimizer identities; intermediate gradients and weights not replayed'}


def read_endpoint(store,view,fit,split,state,exposure,diagnostics):
    import numpy as np
    relative=f'raw/endpoints/{fit["id"]}/{split}.npz'
    if relative not in store.files:
        raise ValueError('unbound endpoint')
    with np.load(e.relative_path(store.root,relative),allow_pickle=False) as saved:
        saved={k:saved[k] for k in saved.files}
    records=json.loads(str(saved['records']));results=[];scores=[];offsets=[0];exposure_buckets={}
    start=c.TRAIN_START if split=='train' else c.FRESH_START
    for i,world in enumerate(range(start,start+512)):
        record=view.load(world);f=bank.features(record)
        reconstructed=functional.score(state,f,store.bill)
        store.bill.charge('functional_contexts')
        a,b=int(saved['offsets'][i]),int(saved['offsets'][i+1]);gpu=saved['scores'][a:b].tolist()
        comparison=functional.compare(reconstructed,gpu)
        js=np.asarray(bank.rewards(record),dtype=float)
        choice=max(range(len(gpu)),key=lambda k:(gpu[k],-k));independent=comparison['functional_choice']
        exact(records[i]['world'],world,'endpoint world identity',diagnostics)
        exact(records[i]['choice'],choice,'authoritative GPU endpoint choice',diagnostics)
        close(records[i]['regret'],float(js.max()-js[choice]),'full-menu GPU regret',diagnostics)
        logq=(js-js.max())/.02;logq-=np.log(np.exp(logq).sum());q=np.exp(logq)
        z=np.asarray(gpu,dtype=float);logp=z-z.max()-np.log(np.exp(z-z.max()).sum())
        terms=-q*logp
        close(saved['per_candidate_CE_terms'][a:b],terms,'all candidate score/error reading',diagnostics)
        if exposure is not None:
            exact(saved['training_counts'][a:b],exposure[i],'probe candidate exposure join including zero',diagnostics)
        ranks=sorted(range(len(gpu)),key=lambda k:(-gpu[k],k))
        teacher_order=sorted(range(len(js)),key=lambda k:(-js[k],k))
        score_rank=[ranks.index(k) for k in range(len(gpu))];teacher_rank=[teacher_order.index(k) for k in range(len(js))]
        teacher=int(js.argmax())
        if exposure is not None:
            for raw,count in enumerate(exposure[i]):
                bucket=exposure_buckets.setdefault(str(int(count)),{'candidates':0,'chosen':0,'teacher':0,
                    'non_teacher':0,'ranked_above_teacher':0,'sum_abs_target_log_probability_error':0.})
                bucket['candidates']+=1;bucket['chosen']+=int(raw==choice);bucket['teacher']+=int(raw==teacher)
                bucket['non_teacher']+=int(raw!=teacher)
                bucket['ranked_above_teacher']+=int(raw!=teacher and score_rank[raw]<score_rank[teacher])
                bucket['sum_abs_target_log_probability_error']+=float(abs(logp[raw]-logq[raw]))
        results.append({'world':world,'comparison':comparison,'GPU_choice':choice,'functional_choice':independent,
                        'GPU_regret':float(js.max()-js[choice]),'functional_choice_delta_J':float(js[independent]-js[choice]),
                        'raw_labels':js.tolist(),'full_menu_target':q.tolist(),'CE_terms':terms.tolist(),
                        'score_rank':score_rank,'teacher_rank':teacher_rank,'actual_training_exposure':None if exposure is None else exposure[i].tolist(),
                        'candidate_error_vs_target_logit':(logp-logq).tolist()})
        scores.extend(reconstructed);offsets.append(len(scores))
    e.npz_write(store,f'raw/functional/{fit["id"]}/{split}.npz',{'scores':np.asarray(scores,dtype=np.float32),
                'offsets':np.asarray(offsets,dtype=np.int64),'records':np.asarray(e.encoded(results).decode('ascii'))})
    return {'fit':fit['id'],'split':split,'contexts':512,'all_candidates':len(scores),
            'mean_GPU_regret':float(np.mean([r['GPU_regret'] for r in results])),
            'flagged_worlds':[r['world'] for r in results if not r['comparison']['all_within_tolerance']],
            'choice_discrepancy_worlds':[r['world'] for r in results if r['comparison']['choice_discrepancy']],
            'ranking_error_by_exact_training_exposure':exposure_buckets if exposure is not None else None,
            'reading':'CPU discrepancies retained; GPU choices stay authoritative, no tolerance widening'}


def service_summary(masks):
    """Executed t1..t500 masks, explicit individual left/right censoring and outages."""
    per_user=[]
    for user in range(50):
        served=[bool(row[user]) for row in masks];times=[i+1 for i,v in enumerate(served) if v]
        gaps=[];begin=None
        for i,value in enumerate(served+[True]):
            if not value and begin is None:
                begin=i
            elif value and begin is not None:
                gaps.append({'start_step':begin+1,'length':i-begin,'left_censored':begin==0,'right_censored':i==len(served)})
                begin=None
        per_user.append({'user_row':user,'served_steps':len(times),'first_service_step':times[0] if times else None,
                         'never_served':not times,'always_served':len(times)==len(served),'gaps':gaps,
                         'longest_gap':max((g['length'] for g in gaps),default=0)})
    outages=[i+1 for i,row in enumerate(masks) if not any(row)]
    return {'mask_scope':'executed t1..t500; initial state is separately checked','per_user':per_user,
            'never_served_users':[r['user_row'] for r in per_user if r['never_served']],
            'always_served_users':[r['user_row'] for r in per_user if r['always_served']],
            'all_team_outage_steps':outages,'all_team_outage_count':len(outages),
            'longest_user_gap':max(r['longest_gap'] for r in per_user)}


def frame_reader(native,path,decision,result,diagnostics):
    import numpy as np
    env=native.host.make_host(decision['world'],area_size=5000)
    fresh=bank.identity(env)
    exact(fresh,decision['construction_identity'],'fresh native world/executor identity',diagnostics)
    perm=assignment(decision['initial_positions_xyz'],decision['positions_xyz'],native.bill)
    exact(perm,decision['target_permutation'],'native independent matching',diagnostics)
    exact(np.asarray(decision['positions_xyz'])[perm],decision['assigned_targets_xyz'],'assigned target bytes',diagnostics)
    rows=iter(e.read_trace(path));first=next(rows)
    if first['type']!='initial' or first['world']!=decision['world'] or first['arm']!=decision['arm']:
        raise AssertionError('episode header world/arm mismatch')
    exact(first['reset'],decision['reset_identity'],'episode full committed reset/RNG',diagnostics)
    exact(first['reset'],result['reset_identity'],'result full reset identity',diagnostics)
    exact(first['assigned_targets_xyz'],decision['assigned_targets_xyz'],'trace assigned targets',diagnostics)
    previous=first['reset']['state'];values={k:[] for k in SERIES};masks=[];changes=[];losses=[];arrival=None
    assigned=np.asarray(decision['assigned_targets_xyz'],dtype=np.float64)
    def physical(saved,label):
        native.bill.charge('reader_state_checks')
        env.current_step=saved['current_step']
        native.host.static_evaluate(env,saved['positions_xyz'],allow_a2a=True)
        actual=state(env)
        for key in ('positions_xyz','connections','user_association','backhauled_users_mask','routing_paths','uav_connections','uav_bs_connections'):
            exact(saved[key],actual[key],label+'/'+key,diagnostics)
        for key,value in actual['reward_info'].items():
            if isinstance(value,(str,bool)):
                exact(value,saved['reward_info'][key],label+'/'+key,diagnostics)
            else:
                close(value,saved['reward_info'][key],label+'/'+key,diagnostics)
    physical(previous,'native initial')
    for t,row in enumerate(rows):
        if t>=500 or row['t']!=t or row['state']['current_step']!=t+1:
            raise AssertionError('complete contiguous H500 required')
        positions=np.asarray(previous['positions_xyz'],dtype=np.float64);delta=assigned-positions
        distance=np.sqrt(np.sum(delta*delta,axis=1));action=np.zeros((6,3),dtype=np.float64)
        moving=distance>1e-6;action[moving]=delta[moving]/np.maximum(30.,distance[moving])[:,None]
        norms=np.linalg.norm(action,axis=1);action[norms>1]/=norms[norms>1,None]
        if arrival is None and np.all(distance<=1e-6):
            arrival=t
        close(action,row['actions'],'independent executor action',diagnostics,atol=1e-12,rtol=0)
        a=np.asarray(row['actions'],dtype=np.float64);norms=np.linalg.norm(a,axis=1);a[norms>1]/=norms[norms>1,None]
        after=positions+30*a;after[:,:2]=np.clip(after[:,:2],0,5000);after[:,2]=np.clip(after[:,2],50,150)
        close(after,row['state']['positions_xyz'],'independent native kinematics',diagnostics,atol=1e-8,rtol=0)
        exact(row['native_rng_sha256'],first['reset']['native_rng_sha256'],'native RNG unchanged',diagnostics)
        exact(row['terminations'],{agent:t==499 for agent in first['reset']['agents']},'H500 done',diagnostics)
        exact(row['truncations'],{agent:False for agent in first['reset']['agents']},'no truncation',diagnostics)
        physical(row['state'],f'native step{t}')
        info=row['state']['reward_info'];association=row['state']['user_association'];routes=row['state']['routing_paths']
        mask=[a>=0 and str(a) in routes for a in association]
        exact(mask,row['state']['backhauled_users_mask'],'primary per-user routed service',diagnostics)
        close(sum(mask)/50,info['coverage_backhauled'],'primary C arithmetic',diagnostics)
        close(.5*(info['coverage_backhauled']+info['throughput_term']),info['contract_reward'],'primary J arithmetic',diagnostics)
        close(sum(row['rewards'].values()),info['contract_reward'],'returned team reward',diagnostics,atol=1e-9,rtol=0)
        for k in SERIES:
            values[k].append(info[k])
        masks.append(mask);changes.append(sum(a!=b for a,b in zip(previous['user_association'],association)))
        losses.append(sum(a and not b for a,b in zip(previous['backhauled_users_mask'],mask)))
        previous=row['state']
    if len(masks)!=500 or result['steps']!=500:
        raise AssertionError('incomplete retained native episode')
    gap=float(np.linalg.norm(np.asarray(previous['positions_xyz'])-assigned,axis=1).max())
    if arrival is None and gap<=1e-6:
        arrival=500
    exact(arrival,result['arrival_step'],'arrival',diagnostics)
    close(gap,result['final_max_distance_to_target_m'],'endpoint gap',diagnostics,atol=1e-8,rtol=0)
    for k in SERIES:
        close(values[k],result['series'][k],'whole native series '+k,diagnostics)
        close([np.mean(values[k]),np.mean(values[k][-100:])],[result[k+'_mean_all'],result[k+'_mean_final100']],
              'native aggregate '+k,diagnostics)
    exact(changes,result['association_changes_per_step'],'all association changes',diagnostics)
    exact(losses,result['backhaul_losses_per_step'],'all backhaul losses',diagnostics)
    summary={k:{'mean_all':float(np.mean(v)),'mean_final100':float(np.mean(v[-100:]))} for k,v in values.items()}
    summary.update(arrival_step=arrival,association_change_count=sum(changes),backhaul_loss_events=sum(losses),
                   service=service_summary(masks),user_positions_xy=decision['user_positions_xy'],initial_state_checked=True,
                   travel_distances_m=np.linalg.norm(assigned-np.asarray(decision['initial_positions_xyz']),axis=1).tolist())
    return summary


def original_audit(store,native,decision,main_path,diagnostics):
    env=native.host.make_host(decision['world'],area_size=5000)
    expected=iter(e.read_trace(main_path));header=next(expected)
    base=f'raw/audit/{decision["world"]}/{decision["arm"]}'
    trace=e.Trace(e.relative_path(store.root,base+'/trace.jsonl.gz'),store.bill)
    original=env.step;frame=0;reset=None
    def step(actions):
        nonlocal frame,reset
        if frame==0:
            env._compute_reward()
            reset={'native_rng_sha256':rng_identity(env),'agents':list(env.agents),'transmitter_mask':e.plain(env._transmitter_mask),'state':state(env)}
            exact(reset,header['reset'],'original executor reset',diagnostics)
            trace.write({**header,'reset':reset})
        result=original(actions)
        row={'type':'step','t':frame,'actions':[e.plain(actions[a]) for a in env.agents],
             'state':state(env),'rewards':result[1],'terminations':result[2],'truncations':result[3],
             'native_rng_sha256':rng_identity(env)}
        trace.write(row);main=next(expected)
        for key in ('actions','state','rewards','terminations','truncations','native_rng_sha256'):
            exact(row[key],main[key],'original executor whole frame '+key,diagnostics)
        frame+=1
        return result
    env.step=step;store.bill.charge('audit_episodes')
    try:
        result=native.p.closed_loop_execute(env,decision['positions_xyz'],max_steps=500,allow_a2a=True)
    finally:
        del env.step;trace.close();store.register(base+'/trace.jsonl.gz')
    if frame!=500 or next(expected,None) is not None:
        raise AssertionError('original whole audit completeness')
    result['reset_identity']=reset
    store.write_gzip(base+'/native.json.gz',result)
    # Every initial+500 audit state receives its own paid physics reader too.
    read=frame_reader(native,e.relative_path(store.root,base+'/trace.jsonl.gz'),decision,result,diagnostics)
    store.write_gzip(base+'/reading.json.gz',read)
    return read


def statistic(values):
    n=len(values);mean=sum(values)/n
    sd=math.sqrt(sum((v-mean)**2 for v in values)/(n-1)) if n>1 else None
    se=sd/math.sqrt(n) if sd is not None else None
    return {'n':n,'mean':mean,'sd':sd,'se':se,'min':min(values),'max':max(values),
            'positive':sum(v>0 for v in values),'negative':sum(v<0 for v in values),'zero':sum(v==0 for v in values),
            'uncertainty':'world pairing conditional on fixed assets; two streams on one bank are not independent bank replications'}


def complete(store,train_view,training_view,fresh_view,assets,cases,diagnostics):
    import numpy as np
    from .native import Native
    from .planner_reader import replay
    e.verify_outputs(store.root,store.files)
    endpoint_readings=[];fits=[];initials={}
    for asset in assets:
        fit=asset['fit'];path=e.relative_path(store.root,asset['path'])
        if asset['path'] not in store.files or store.files[asset['path']]['sha256']!=asset['sha256']:
            raise ValueError('unbound final model')
        checkpoint=e.checked_torch(path,asset['sha256'])
        if checkpoint['launch_sha']!=store.launch_sha or checkpoint['input_sha256']!=store.input_sha256 or checkpoint['fit']!=fit:
            raise ValueError('functional-reader model source identity')
        exact(model.digest(checkpoint['state']),checkpoint['final_sha256'],'final whole parameter bytes',diagnostics)
        initial_path=f'raw/initial/stream{fit["stream"]}.pt'
        if initial_path not in store.files:
            raise ValueError('unbound initial state')
        initial=e.checked_torch(e.relative_path(store.root,initial_path),store.files[initial_path]['sha256'])
        exact(model.digest(initial['state']),checkpoint['initial_sha256'],'saved actual initial weights',diagnostics)
        if fit['stream'] in initials:
            exact(initials[fit['stream']],checkpoint['initial_sha256'],'same-stream initializer equality',diagnostics)
        initials[fit['stream']]=checkpoint['initial_sha256']
        final_movement=learner_movement(checkpoint['state'],initial['state'])
        exposure,reading=read_updates(store,training_view,fit,checkpoint,final_movement,diagnostics);fits.append(reading)
        endpoint_readings.append(read_endpoint(store,training_view,fit,'train',checkpoint['state'],exposure,diagnostics))
        endpoint_readings.append(read_endpoint(store,fresh_view,fit,'fresh',checkpoint['state'],None,diagnostics))
    per_world=[];main_read=[];audits=[]
    with Native(store.bill) as native:
        for offset,world in enumerate(range(c.FRESH_START,c.FRESH_START+128)):
            row={'world':world,'arms':{}}
            reference=fresh_view.load(world)
            raw=[{**meta,'positions_xyz':xyz} for meta,xyz in zip(reference['construction']['raw_metadata'],reference['layouts_xyz'])]
            shortlist,_=select_menu(raw);short_ids=[p['source_index'] for p in shortlist]
            raw8=max(short_ids,key=lambda i:(reference['infos'][i]['contract_reward'],-i))
            for arm in c.ARMS:
                case=cases[(world,arm)]
                decision=e.load_output(store.root,store.files,case['decision'])
                result=e.load_output(store.root,store.files,case['native'])
                world_gate(decision,reference,diagnostics)
                path=e.relative_path(store.root,case['trace'])
                reading=frame_reader(native,path,decision,result,diagnostics)
                store.write_gzip(f'raw/native-reader/{world}/{arm}.json.gz',reading)
                planner=None
                if arm=='P':
                    env=native.host.make_host(world,area_size=5000)
                    exact(bank.identity(env),reference['identity'],'P cache replay fresh world',diagnostics)
                    planner=replay(env,native.p,e.relative_path(store.root,case['queries']),decision,store.bill)
                elif arm in ('Raw8J','RawJ'):
                    expected_choice=raw8 if arm=='Raw8J' else reference['best']
                    exact(decision['chosen_raw_index'],expected_choice,'ordinary raw J decision',diagnostics)
                    queries=list(e.read_trace(e.relative_path(store.root,case['queries'])))
                    selected=short_ids if arm=='Raw8J' else list(range(len(raw)))
                    if len(queries)!=len(selected):
                        raise AssertionError('ordinary complete paid query count')
                    for query,i in zip(queries,sorted(selected)):
                        exact(query['positions_xyz'],raw[i]['positions_xyz'],'ordinary original raw query row',diagnostics)
                        for key,value in query['info'].items():
                            if isinstance(value,(str,bool)):
                                exact(value,reference['infos'][i][key],'ordinary label discrete',diagnostics)
                            else:
                                close(value,reference['infos'][i][key],'ordinary current query/full bank label',diagnostics)
                audit=(offset in (0,1) and arm not in ('Raw8J','RawJ')) or (offset==0 and arm in ('Raw8J','RawJ'))
                if audit:
                    audit_reading=original_audit(store,native,decision,path,diagnostics)
                    audits.append({'world':world,'arm':arm,'reading':audit_reading})
                matched=case['matched_endpoint']
                raw_j=(reference['infos'][decision['chosen_raw_index']]['contract_reward'] if arm!='P'
                       else decision['P_menu']['static']['P_relay_contract_reward'])
                metrics={k:reading[k] for k in SERIES}
                metrics.update(association_change_count=reading['association_change_count'],backhaul_loss_events=reading['backhaul_loss_events'],
                               all_team_outage_count=reading['service']['all_team_outage_count'],never_served_count=len(reading['service']['never_served_users']),
                               longest_user_gap=reading['service']['longest_user_gap'],arrival_step=reading['arrival_step'],
                               cold_selection_seconds=decision['parent_cold_selection_seconds'],
                               selection_child_cpu_seconds=decision['selection_child_cpu']['total_seconds'],
                               selection_parent_cpu_seconds=decision['selection_parent_cpu_seconds'],
                               selection_counts=decision['selection_counts'],timing=decision['timing'],
                               raw_static_J=raw_j,matched_static_J=matched['contract_reward'],matched_minus_raw_J=matched['contract_reward']-raw_j,
                               planner_reading=planner,native_wall_seconds=result['native_wall_seconds_including_trace'],chosen_raw_index=decision['chosen_raw_index'])
                metrics['native_trace_instrumentation']=result['trace_instrumentation']
                row['arms'][arm]=metrics;main_read.append({'world':world,'arm':arm,'metrics':metrics})
            per_world.append(row);store.progress('native_reader',completed_worlds=len(per_world),total_worlds=128)
    store.write_gzip('reading/native-per-world.json.gz',per_world)
    pairs={}
    for left,right in itertools.combinations(c.ARMS,2):
        label=left+'_minus_'+right
        native_metrics={k:statistic([r['arms'][left][k]['mean_all']-r['arms'][right][k]['mean_all'] for r in per_world]) for k in SERIES}
        native_metrics.update({k:statistic([r['arms'][left][k]-r['arms'][right][k] for r in per_world])
                               for k in ('cold_selection_seconds','selection_child_cpu_seconds','selection_parent_cpu_seconds',
                                         'association_change_count','backhaul_loss_events','all_team_outage_count','never_served_count',
                                         'longest_user_gap','raw_static_J','matched_static_J','matched_minus_raw_J')})
        pairs[label]=native_metrics
    raw8_fresh=[]
    for world in range(c.FRESH_START,c.FRESH_START+512):
        r=fresh_view.load(world);raw=[{**m,'positions_xyz':x} for m,x in zip(r['construction']['raw_metadata'],r['layouts_xyz'])]
        short,_=select_menu(raw);ids=[v['source_index'] for v in short]
        best=max(ids,key=lambda i:(r['infos'][i]['contract_reward'],-i))
        raw8_fresh.append({'world':world,'choice':best,'raw8_J':r['infos'][best]['contract_reward'],
                           'RawJ_J':r['infos'][r['best']]['contract_reward'],
                           'regret':r['infos'][r['best']]['contract_reward']-r['infos'][best]['contract_reward']})
    store.write_gzip('reading/Raw8J-fresh512.json.gz',raw8_fresh)
    curves={}
    for stream in (0,1):
        curves[str(stream)]=[r for r in endpoint_readings if next(f for f in c.FITS if f['id']==r['fit'])['stream']==stream]
    curve_pairs={}
    for stream in (0,1):
        ids=[f['id'] for f in sorted(c.FITS,key=lambda f:f['n']) if f['stream']==stream]
        for split in ('train','fresh'):
            readings={}
            for fit_id in ids:
                with np.load(e.relative_path(store.root,f'raw/endpoints/{fit_id}/{split}.npz'),allow_pickle=False) as z:
                    readings[fit_id]=json.loads(str(z['records']))
            for left,right in itertools.combinations(ids,2):
                paired=[{'world':a['world'],'left_regret':a['regret'],'right_regret':b['regret'],
                         'delta_regret':a['regret']-b['regret'],'delta_J':a['J']-b['J']}
                        for a,b in zip(readings[left],readings[right])]
                if any(a['world']!=b['world'] for a,b in zip(readings[left],readings[right])):
                    raise AssertionError('paired nested curve world identities')
                label=f'{split}/{left}_minus_{right}'
                curve_pairs[label]={'delta_regret':statistic([r['delta_regret'] for r in paired]),
                                    'delta_J':statistic([r['delta_J'] for r in paired])}
                store.write_gzip('reading/curve-pairs/'+label+'.json.gz',paired)
    return {'status':'complete','fits':fits,'endpoint_readings':endpoint_readings,'curves_by_fixed_stream':curves,
            'paired_nested_curves':curve_pairs,
            'native_worlds':128,'native_arms':list(c.ARMS),'native_comparisons':pairs,
            'native_absolute':{a:{k:statistic([r['arms'][a][k]['mean_all'] for r in per_world]) for k in SERIES} for a in c.ARMS},
            'audits':len(audits),'Raw8J_fresh_static_regret':statistic([r['regret'] for r in raw8_fresh]),
            'matched_row_differences':'retained as scientific endpoint/execution differences, not automatically technical failures',
            'uncertainty':'two optimization streams on one nested bank; world comparisons conditional on each fixed asset; no data-only causal or scaling-law inference',
            'trust':'independent labels/native refresh use pinned radio; functional CPU scorer has no production forward; no optimizer replay; P control uses paid cached responses',
            'cold_scope':'fresh child through immutable selection-ready, includes matching/reset/serialization; segmented compute is not an independently measured uninstrumented latency',
            'host_clock':'planning wall delay does not advance H500; no high-level service-history adaptation',
            'support':'unmetered support remains unknown; phase resource bill measures this actual operation'}
