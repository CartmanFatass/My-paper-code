"""One sequential environment, four fixed fits, complete endpoints and durable failures."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import platform
import resource
import time
import traceback
import numpy as np
import torch
from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest,state_copy,movement
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.assets import load_parent
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.environment import make_real,check_host
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.study import artifact,load_raw,costs
from experiments.candidates.uav_local_history.b01.study import write_json,file_identity
from .contract import FROZEN,FAMILIES,NEURAL,LEARNERS,OBJECT,dimension,array_digest,source_identities,INHERITED_COST
from .collect import collect_episode
from .search import perturbation,update
from .reading import comparisons

ROOT=Path(__file__).resolve().parents[4]

def runtime():
    return dict(python=platform.python_version(),compiler=platform.python_compiler(),numpy=np.__version__,torch=torch.__version__,
                host=platform.node(),device='cpu',torch_threads=torch.get_num_threads(),torch_interop_threads=torch.get_num_interop_threads(),deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
                numpy_config=str(np.__config__.get_info('blas_opt_info')) if hasattr(np.__config__,'get_info') else str(np.__config__.CONFIG),
                thread_environment={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')})

def parent_body(actor):
    parameters=list(actor.parameters())
    if any(p.dtype!=torch.float32 or p.requires_grad or not torch.isfinite(p).all() for p in parameters):
        raise AssertionError('frozen finite FP32 P0 parameters required')
    n=sum(p.numel() for p in parameters)
    if n!=34715: raise AssertionError('original 34715-parameter P0 body required')
    return dict(parameters=n,dtype='float32',architecture=[114,128,128,27],activation='relu',
                state_sha256=state_digest(actor.state_dict()),trainable_parameters=0)


def validate_counts(actual,cost,protocol):
    e=protocol.expected()
    for k in ('training_episodes','evaluation_episodes','complete_episodes','native_steps','native_uav_ticks',
              'explicit_resets','constructor_resets','mask_installs','motion_requests','motion_draws','directions','normal_coordinates','updates'):
        if actual.get(k)!=e[k]: raise AssertionError('fixed complete exposure '+k)
    for name in ('fits_started','fits_completed'):
        if actual.get(name)!=4: raise AssertionError('exactly four fits '+name)
    for call,done in (('raw_write_calls','raw_writes'),('direction_calls','directions'),('update_calls','updates'),('explicit_reset_calls','explicit_resets'),('native_step_calls','native_steps'),
                      ('mask_install_calls','mask_installs'),('motion_request_calls','motion_requests'),('constructor_calls','constructor_resets')):
        if actual.get(call)!=actual.get(done): raise AssertionError('incomplete effect '+call)
    if actual.get('optimizer_steps',0)!=0: raise AssertionError('no torch optimizer updates')
    if actual.get('raw_writes')!=e['complete_episodes']: raise AssertionError('all canonical raw writes')
    policy=cost['all_policy']
    for k in ('head_requests','zero_head_requests'):
        if policy[k]!=e[k]: raise AssertionError('readout exposure '+k)
    if policy['head_mac_terms']!=(e['training_episodes']//2+len(protocol.worlds)*4)*(protocol.horizon//4*5)*3456 or policy['zero_head_mac_terms']!=e['zero_head_requests']//2*3456:
        raise AssertionError('actual CONT readout coordinate terms')
    if policy['sampled_draws']!=e['motion_draws'] or policy['law_evaluations']!=e['motion_requests']:
        raise AssertionError('private action draws/requests')
    final=len(protocol.worlds); q=protocol.horizon//4*5
    if (cost['C_family_programs']['requests']!=final*7*q or policy['target_vectors']!=final*4*q*2
            or policy['score_tail_evaluations']!=final*2*q or actual['zero_decisions']!=final*6*(protocol.horizon//4)):
        raise AssertionError('reference/helper bill')
    if cost['neural_forward_rows']>(e['training_episodes']+final*20)*q:
        raise AssertionError('P0 forward ceiling')
    if cost['C_family_programs']['trajectories']>final*7*q*27 or cost['C_family_programs']['model_ticks']>final*7*q*27*4:
        raise AssertionError('C path ceiling')
    links=lambda group:sum(group.get(k,0) for k in ('candidate_links','setup_links','helper_setup_links','helper_extreme_links'))
    if links(cost['helper_programs'])>(e['training_episodes']+final*16)*q*140 or links(cost['C_family_programs'])>final*7*q*2260:
        raise AssertionError('helper link ceiling')
    if (actual['native_dense_power_slots']!=275*(e['native_steps']+e['explicit_resets']+1)
            or actual['native_unique_distance_pairs']!=260*(e['native_steps']+e['explicit_resets']+1)):
        raise AssertionError('native physical work')

def _execute(out,actor,env,protocol,batch,publish):
    """Fixture-only configurable core; production calls it only with FROZEN."""
    protocol.validate()
    actual,inflight=batch['actual'],batch['inflight']
    parent_sha=state_digest(actor.state_dict())
    parent_before=state_copy(actor)
    batch['parent_body']=parent_body(actor)
    centers={(b,f):np.zeros(dimension(f),dtype=np.float64) for b in range(2) for f in FAMILIES}
    cost_rows=[]; finals=[]; fit_started=set()
    with (out/'episodes.jsonl').open('x',encoding='utf-8') as stream, (out/'attempts.jsonl').open('x',encoding='utf-8') as attempts:
        def persist():
            # Append the attempt before its effects. Compact progress snapshots retain full counters.
            event={k:inflight.get(k) for k in ('id','tick','effect','agent')}
            attempts.write(json.dumps(event,separators=(',',':'))+'\n');attempts.flush()
        def run(identity,theta):
            if identity['kind']=='training' and identity['program'] not in fit_started:
                fit_started.add(identity['program']);actual['fits_started']=len(fit_started)
                publish()
            parent='P0' if identity['program'] in LEARNERS else identity['program'].split('_')[0]
            try:
                row=collect_episode(env,identity=identity,actor=actor if parent in NEURAL else None,out=out,protocol=protocol,
                                    counts=actual,inflight=inflight,policy_sha=parent_sha if parent in NEURAL else None,
                                    theta=theta,persist=persist)
            except BaseException:
                batch['costs']=costs(cost_rows,actual,inflight)
                raise
            stream.write(json.dumps(row,allow_nan=False,sort_keys=True)+'\n');stream.flush()
            cost_rows.append(dict(parent=parent,policy_counts=row['policy_counts']))
            if identity['kind']=='evaluation': finals.append(row)
            batch['last_episode']=row['id'];batch['costs']=costs(cost_rows,actual)
            publish()
            return row
        identities=iter(protocol.identities())
        for b in range(2):
            for f in FAMILIES:
                path=out/'search'/f'{f}{b}_center_00.npz'
                np.savez_compressed(path,theta=centers[b,f])
                batch['search_artifacts'].append(artifact(path,out))
            for i in range(protocol.iterations):
                ds={}; fitness={f:np.zeros((protocol.directions,2),dtype=np.float64) for f in FAMILIES}
                for k in range(protocol.directions):
                    for fi,f in enumerate(FAMILIES):
                        inflight.update(effect='direction',block=b,iteration=i,direction=k,family=f)
                        actual['direction_calls']=actual.get('direction_calls',0)+1
                        publish()
                        delta=perturbation(protocol,b,fi,i,k)
                        actual['directions']=actual.get('directions',0)+1
                        actual['normal_coordinates']=actual.get('normal_coordinates',0)+len(delta)
                        ds[f,k]=delta
                        path=out/'search'/f'{f}{b}_i{i:02d}_k{k:02d}.npz'
                        np.savez_compressed(path,delta=delta,center_sha256=np.asarray(array_digest(centers[b,f])))
                        batch['search_artifacts'].append(artifact(path,out))
                        for si,sign in enumerate((1,-1)):
                            theta=centers[b,f]+sign*.05*delta
                            js=[]
                            for j in range(2): js.append(run(next(identities),theta)['J'])
                            fitness[f][k,si]=(js[0]+js[1])/2.
                # Both centers remain fixed until the complete iteration has been collected.
                for f in FAMILIES:
                    deltas=np.array([ds[f,k] for k in range(protocol.directions)],dtype=np.float64)
                    actual['update_calls']=actual.get('update_calls',0)+1
                    inflight.update(effect='update',block=b,iteration=i,family=f)
                    publish()
                    center,diagnostics=update(centers[b,f],deltas,fitness[f])
                    path=out/'search'/f'{f}{b}_center_{i+1:02d}.npz'
                    np.savez_compressed(path,theta=center,fitness=fitness[f],**diagnostics)
                    batch['search_artifacts'].append(artifact(path,out))
                    centers[b,f]=center
                    actual['updates']=actual.get('updates',0)+1
                    publish()
            actual['fits_completed']=actual.get('fits_completed',0)+2
        for identity in identities:
            name=identity['program']
            theta=centers[int(name[-1]),name[:-1]] if name in LEARNERS else None
            run(identity,theta)
    batch['episode_log']=artifact(out/'episodes.jsonl',out)
    batch['attempt_log']=artifact(out/'attempts.jsonl',out)
    batch['final_parent_state_sha256']=state_digest(actor.state_dict())
    batch['parent_movement']=movement(parent_before,actor.state_dict())
    if batch['final_parent_state_sha256']!=parent_sha: raise AssertionError('P0 mutated')
    batch['arithmetic_work']=dict(P0_forward_MAC_terms=batch['costs']['neural_forward_rows']*34432,
                                  CONT_head_MAC_terms=batch['costs']['all_policy']['head_mac_terms'],
                                  CONT_zero_head_MAC_terms=batch['costs']['all_policy']['zero_head_mac_terms'],
                                  search_accumulation_coordinate_terms=actual['normal_coordinates'],
                                  scope='Multiply-accumulate coordinate counts, not FLOPs or speed; zero-head reconstruction is additional arithmetic.')
    batch['center_movement']={f+str(b):dict(l2=float(np.linalg.norm(t)),max_abs=float(np.max(np.abs(t))),nonzero=int(np.count_nonzero(t))) for (b,f),t in centers.items()}
    validate_counts(actual,batch['costs'],protocol)
    batch['comparisons']=comparisons(finals,protocol)


def run_batch(out,launch_sha,*,admission,parent_path,entry_start=None,entry_cpu=None,import_timing=None):
    if not admission or admission.get('sha')!=launch_sha: raise ValueError('accepted admission required')
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    allowed={'launch-status.json','launch-manifest.json','admission-preflight.json','stdout.log','stderr.log'}
    if any(p.name not in allowed for p in out.iterdir()): raise FileExistsError('existing scientific output: reconcile same operation')
    for name in ('raw','search'): (out/name).mkdir()
    wall=time.perf_counter() if entry_start is None else entry_start
    cpu=time.process_time() if entry_cpu is None else entry_cpu
    batch=dict(object=OBJECT,state='INCOMPLETE',scientific_execution=True,launch_sha=launch_sha,admission=dict(admission),
               protocol=FROZEN.to_dict(),expected=FROZEN.expected(),inherited_cost=INHERITED_COST,actual=dict(fits_started=0,fits_completed=0,updates=0,optimizer_steps=0,
               constructor_calls=0,constructor_resets=0,native_dense_power_slots=0,native_unique_distance_pairs=0,zero_decisions=0),
               inflight={},search_artifacts=[],start_utc=datetime.now(timezone.utc).isoformat(),runtime=runtime())
    def publish():
        batch.update(worker_wall_seconds=time.perf_counter()-wall,worker_cpu_seconds=time.process_time()-cpu,
                     worker_peak_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        write_json(out/'progress.json',{k:batch.get(k) for k in ('state','actual','inflight','last_episode','worker_wall_seconds','worker_cpu_seconds')})
    batch['scientific_import_timing']=import_timing
    env=None
    try:
        if (batch['runtime']['torch_threads']!=1 or batch['runtime']['torch_interop_threads']!=1
                or any(v!='1' for v in batch['runtime']['thread_environment'].values())):
            raise AssertionError('one scientific numerical thread required')
        batch['sources']=source_identities(ROOT)
        start=time.perf_counter();start_cpu=time.process_time()
        actor,batch['parent']=load_parent(parent_path)
        batch['parent_load_wall_seconds']=time.perf_counter()-start
        batch['parent_load_cpu_seconds']=time.process_time()-start_cpu
        batch['initial_parent_state_sha256']=state_digest(actor.state_dict())
        write_json(out/'config.json',{k:batch[k] for k in ('object','scientific_execution','launch_sha','protocol','expected','sources','parent','runtime','inherited_cost')})
        write_json(out/'summary.json',batch)
        batch['actual']['constructor_calls']+=1;publish()
        start=time.perf_counter();start_cpu=time.process_time()
        env=make_real(FROZEN.constructor_seed)
        batch['constructor_wall_seconds']=time.perf_counter()-start
        batch['constructor_cpu_seconds']=time.process_time()-start_cpu
        batch['actual'].update(constructor_resets=1,native_dense_power_slots=275,native_unique_distance_pairs=int(env.env._path_loss_cache_misses))
        batch['host']=check_host(env)
        _execute(out,actor,env,FROZEN,batch,publish)
        if file_identity(parent_path)['sha256']!=batch['parent']['sha256']: raise AssertionError('P0 file changed')
        batch['state']='COMPLETE'
    except BaseException:
        batch.update(state='FAILED',failure=traceback.format_exc(),interrupted_call_work_may_be_unmeasured=True)
        raise
    finally:
        if env is not None: env.close()
        for name,key in (('episodes.jsonl','episode_log'),('attempts.jsonl','attempt_log')):
            if (out/name).exists(): batch[key]=artifact(out/name,out)
        batch['finish_utc']=datetime.now(timezone.utc).isoformat();publish()
        write_json(out/'summary.json',batch)
    return batch
