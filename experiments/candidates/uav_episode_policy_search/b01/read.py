"""Admitted full saved-data reconstruction: zero native steps and zero new fits."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import resource
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
if __name__=='__main__': __package__='experiments.candidates.uav_episode_policy_search.b01'

# Scientific modules are imported after admission for a standalone reader.
def _read_all(batch,out,actor,protocol,report,progress=lambda:None):
    import numpy as np
    from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest,state_copy,movement
    from experiments.candidates.uav_fleet_adaptation.b08_local_gate.assets import checked_path
    from experiments.candidates.uav_fleet_adaptation.b08_local_gate.study import costs,load_raw
    from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
    from .audit import audit_episode,equal,require
    from .contract import FAMILIES,LEARNERS,NEURAL,dimension,array_digest,episode_id
    from .reading import metric_values
    out=Path(out)
    counts=report['actual']
    parent_sha=state_digest(actor.state_dict())
    parent_before=state_copy(actor)
    from .study import parent_body
    require(batch['parent_body']==parent_body(actor),'frozen P0 body identity')
    require(batch['initial_parent_state_sha256']==parent_sha==batch['final_parent_state_sha256'],'frozen original P0')
    records={a['path']:a for a in batch['search_artifacts']}
    require(len(records)==len(batch['search_artifacts']),'duplicate immutable search artifact')
    seen=set()
    def search_file(name):
        relative='search/'+name+'.npz'
        require(relative in records and relative not in seen,'complete unique search artifact '+relative)
        seen.add(relative)
        return load_raw(checked_path(out,relative,records[relative]))
    episode_log=checked_path(out,batch['episode_log']['path'],batch['episode_log'])
    attempt_log=checked_path(out,batch['attempt_log']['path'],batch['attempt_log'])
    centers={(b,f):np.zeros(dimension(f),dtype=np.float64) for b in range(2) for f in FAMILIES}
    policy_rows=[];finals=[];completed=0
    identities=iter(protocol.identities())
    maxima=dict(radio=0.,observation=0.,reward=0.,prediction=0.)
    report['policy_costs']=costs([], {})
    with episode_log.open(encoding='utf-8') as stream,attempt_log.open(encoding='utf-8') as attempts:
        def require_attempt(expected):
            line=attempts.readline()
            require(bool(line),'missing attempted effect')
            require(json.loads(line)==expected,'attempt identity/order')
            counts['attempt_records']=counts.get('attempt_records',0)+1
        def episode(theta):
            nonlocal completed
            identity=next(identities)
            line=stream.readline();require(bool(line),'missing complete episode')
            row=json.loads(line)
            for key,value in identity.items(): require(row.get(key)==value,'exact episode execution order '+key)
            name=identity['program'];learner=name in LEARNERS
            parent,gate=('P0','A') if learner else name.split('_',1)
            require(row['parent']==parent and row['gate']==gate,'program/control binding')
            require(row['policy_sha256']==(parent_sha if parent in NEURAL else None),'P0 source binding')
            require(row['theta_sha256']==(array_digest(theta) if learner else None),'whole episode parameter/version binding')
            require(row['zero_check']==(identity['kind']=='training' and identity['iteration']==0),'first iteration zero identity exposure')
            identifier=episode_id(identity)
            require(row['id']==identifier and row['raw']['path']=='raw/'+identifier+'.npz','raw episode identity')
            raw=load_raw(checked_path(out,row['raw']['path'],row['raw']))
            equal(raw['initial_generation'],2+completed*(protocol.horizon+1),'one reused environment generation')
            # Replay the exact durable pre-effect journal. The adapter can never consume another scientific world.
            expected_reset=dict(id=identifier,tick=None,effect='reset',agent=None)
            require_attempt(expected_reset)
            for tick in range(protocol.horizon):
                if tick%4==0:
                    for agent in range(5): require_attempt(dict(id=identifier,tick=tick,effect='policy_query',agent=agent))
                    require_attempt(dict(id=identifier,tick=tick,effect='mask_install',agent=4))
                require_attempt(dict(id=identifier,tick=tick,effect='native_step',agent=4))
            require_attempt(dict(id=identifier,tick=protocol.horizon-1,effect='raw_write',agent=4))
            try:
                result=audit_episode(raw,row,protocol,actor if parent in NEURAL else None,theta=theta,counts=counts,inflight=report['inflight'])
            except BaseException:
                report['policy_costs']=costs(policy_rows,{},report['inflight'])
                raise
            policy_rows.append(dict(parent=parent,policy_counts=result['policy_counts']))
            report['policy_costs']=costs(policy_rows,{})
            for key,value in result['max_abs_errors'].items(): maxima[key]=max(maxima[key],value)
            report['max_abs_errors']=maxima
            completed+=1
            if identity['kind']=='evaluation': finals.append(row)
            progress()
            return float(np.sum(raw['reward'],dtype=np.float64)/protocol.horizon)
        for b in range(2):
            for f in FAMILIES:
                saved=search_file(f'{f}{b}_center_00')
                require(set(saved)=={'theta'},'zero center artifact fields')
                require(saved['theta'].dtype==np.float64,'FP64 center dtype')
                equal(saved['theta'],centers[b,f],'exact zero initialization')
            for i in range(protocol.iterations):
                directions={};fitness={f:np.zeros((protocol.directions,2),dtype=np.float64) for f in FAMILIES}
                for k in range(protocol.directions):
                    for fi,f in enumerate(FAMILIES):
                        # Independently construct exactly one normal vector from its prospective address.
                        delta=np.random.default_rng(np.random.SeedSequence([protocol.perturbation_root,b,fi,i,k])).standard_normal(dimension(f))
                        counts['directions']=counts.get('directions',0)+1
                        counts['normal_coordinates']=counts.get('normal_coordinates',0)+len(delta)
                        saved=search_file(f'{f}{b}_i{i:02d}_k{k:02d}')
                        require(set(saved)=={'delta','center_sha256'} and saved['delta'].dtype==np.float64 and saved['center_sha256'].shape==(),'FP64 direction/version schema')
                        equal(saved['delta'],delta,'prospective Gaussian address/vector')
                        require(str(saved['center_sha256'])==array_digest(centers[b,f]),'fixed iteration center digest')
                        directions[f,k]=delta
                        for si,sign in enumerate((1,-1)):
                            theta=centers[b,f]+sign*.05*delta
                            j0=episode(theta);j1=episode(theta)
                            fitness[f][k,si]=(j0+j1)/2.
                for f in FAMILIES:
                    signed=fitness[f][:,0]-fitness[f][:,1]
                    half=signed/2.
                    scale=max(float(np.sqrt(np.sum(half*half,dtype=np.float64)/protocol.directions)),1e-8)
                    accumulated=np.zeros(dimension(f),dtype=np.float64)
                    for k in range(protocol.directions): accumulated+=signed[k]*directions[f,k]
                    center=centers[b,f]+(.02/(protocol.directions*scale))*accumulated
                    center[0]=min(np.log(2.),max(-np.log(2.),float(center[0])))
                    require(np.isfinite(center).all(),'finite reconstructed update')
                    saved=search_file(f'{f}{b}_center_{i+1:02d}')
                    require(set(saved)=={'theta','fitness','scale','diff','accumulator'},'complete search update fields')
                    for key,value in (('theta',center),('fitness',fitness[f]),('scale',scale),('diff',signed),('accumulator',accumulated)):
                        require(saved[key].dtype==np.float64,'FP64 update '+key)
                        equal(saved[key],value,'independent search update '+key)
                    centers[b,f]=center;counts['updates']=counts.get('updates',0)+1
                    progress()
        for world in protocol.worlds:
            for name,tape in protocol.episode_order():
                episode(centers[int(name[-1]),name[:-1]] if name in LEARNERS else None)
        require(not stream.readline(),'extra episode exposure')
        require(not attempts.readline(),'extra attempt exposure')
    require(seen==set(records),'no unbound/dropped search artifacts')
    require(state_digest(actor.state_dict())==parent_sha,'reader P0 unchanged')
    report['parent_body']=parent_body(actor)
    report['parent_movement']=movement(parent_before,actor.state_dict())
    require(report['parent_movement']==batch['parent_movement']==dict(parameters=34715,l2=0.,max_abs=0.,changed_parameters=0),'worker/reader zero P0 movement')
    require(report['policy_costs']['all_policy']==batch['costs']['all_policy'],'worker/reader complete actual policy bill')
    e=protocol.expected()
    for key in ('directions','normal_coordinates','updates'):
        require(counts[key]==e[key],'reader '+key)
    require(counts['saved_episodes']==e['complete_episodes'] and counts['saved_native_ticks']==e['native_steps'],'full saved exposure')
    require(counts['scalar_states']==e['complete_episodes']*(protocol.horizon+protocol.horizon//4+1),'all physical states')
    counts['logical_power_links']=counts['scalar_states']*270
    # Original scalar implementation evaluates 250 user and 20 directed peer powers per state.
    require(counts['observation_rows']==counts['scalar_states']*5,'all old/refreshed local rows')
    movements={f+str(b):dict(l2=float(np.linalg.norm(t)),max_abs=float(np.max(np.abs(t))),nonzero=int(np.count_nonzero(t))) for (b,f),t in centers.items()}
    require(batch['center_movement']==movements,'all final center movements')
    report['arithmetic_work']=dict(P0_forward_MAC_terms=report['policy_costs']['neural_forward_rows']*34432,
                                  CONT_head_MAC_terms=report['policy_costs']['all_policy']['head_mac_terms'],
                                  CONT_zero_head_MAC_terms=report['policy_costs']['all_policy']['zero_head_mac_terms'],
                                  search_accumulation_coordinate_terms=counts['normal_coordinates'],
                                  scope='Multiply-accumulate coordinate counts, not FLOPs or speed; zero-head reconstruction is additional arithmetic.')
    require(report['arithmetic_work']==batch['arithmetic_work'],'actual worker/reader arithmetic bill')
    report['center_movement']=movements
    comparison=_comparisons(finals,protocol)
    # The reader rebuilds every summary from the paid per-world rows with its own reduction implementation.
    require(comparison==batch['comparisons'],'all fixed endpoint summaries/contrasts')
    report['comparisons']=comparison
    report['actual']['bootstrap_integers']=e['bootstrap_integers']
    return report


def _comparisons(rows,protocol):
    import numpy as np
    from .contract import PROGRAMS,CONTRASTS
    from .reading import metric_values
    by_key={(r['program'],r['world'],r['tape']):metric_values(r) for r in rows}
    expected={(p,w,t) for w in protocol.worlds for p,t in protocol.episode_order()}
    if len(by_key)!=len(rows) or set(by_key)!=expected: raise AssertionError('complete final population')
    metrics=sorted(next(iter(by_key.values())))
    indices=np.random.default_rng(protocol.bootstrap_seed).integers(0,len(protocol.worlds),size=(protocol.bootstrap_resamples,len(protocol.worlds)))
    values={}
    def summary(x):
        sampled=np.mean(x[indices],axis=1)
        return dict(n=len(x),mean=float(np.mean(x)),sd=float(np.std(x,ddof=1)) if len(x)>1 else None,
                    min=float(np.min(x)),max=float(np.max(x)),world_values=x.tolist(),
                    descriptive_bootstrap95=np.quantile(sampled,[.025,.975],method='linear').tolist(),
                    positive=int(np.sum(x>0)),negative=int(np.sum(x<0)),zero=int(np.sum(x==0)))
    for p in PROGRAMS:
        tapes=(None,) if p=='C_A' else (0,1)
        values[p]={m:np.array([np.mean([by_key[p,w,t][m] for t in tapes]) for w in protocol.worlds]) for m in metrics}
    levels={p:{m:summary(values[p][m]) for m in metrics} for p in PROGRAMS}
    contrasts={a+'-'+b:{m:summary(values[a][m]-values[b][m]) for m in metrics} for a,b in CONTRASTS}
    adverses={a+'-'+b:{label:[w for w,x in zip(protocol.worlds,contrasts[a+'-'+b][metric]['world_values']) if x*direction>0]
                        for label,metric,direction in (('lower_J','J',-1),('lower_mean_service','mean_served',-1),
                        ('more_zero_service_steps','zero_service_steps',1),('longer_zero_service_streak','longest_zero_service_streak',1))} for a,b in CONTRASTS}
    return dict(worlds=list(protocol.worlds),levels=levels,contrasts=contrasts,adverses=adverses,
                uncertainty='Pointwise percentile world bootstrap; two stochastic tapes averaged within world; C once. '
                            'Conditional on two realized paired training blocks and one frozen parent; no training-population, '
                            'simultaneous-comparison or equivalence coverage.',
                bootstrap=dict(seed=protocol.bootstrap_seed,resamples=protocol.bootstrap_resamples,quantile='linear'))


def read_result(out,repo,parent_path,*,report_out=None):
    wall,cpu=time.perf_counter(),time.process_time()
    import numpy as np
    import torch
    from .contract import FROZEN,OBJECT,source_identities,INHERITED_COST
    from .study import validate_counts,runtime
    from experiments.candidates.uav_fleet_adaptation.b08_local_gate.assets import load_parent
    from experiments.candidates.uav_local_history.b01.study import write_json,file_identity
    out=Path(out).resolve()
    report_out=out if report_out is None else Path(report_out).resolve()
    if report_out!=out:
        report_out.mkdir(parents=True,exist_ok=True)
        allowed={'launch-status.json','launch-manifest.json','admission-preflight.json','stdout.log','stderr.log'}
        if any(p.name not in allowed for p in report_out.iterdir()): raise FileExistsError('existing standalone reader output')
    if (report_out/'reading.json').exists(): raise FileExistsError('existing reader: reconcile before separate reading')
    report=dict(status='INCOMPLETE',actual=dict(native_steps=0,refits=0,optimizer_steps=0),inflight={},
                start_utc=datetime.now(timezone.utc).isoformat())
    def progress():
        report.update(reader_wall_seconds=time.perf_counter()-wall,reader_cpu_seconds=time.process_time()-cpu,
                      reader_peak_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        write_json(report_out/'reading-progress.json',{k:report[k] for k in ('status','actual','inflight','reader_wall_seconds','reader_cpu_seconds')})
    try:
        batch=json.loads((out/'summary.json').read_text())
        if batch.get('object')!=OBJECT or batch.get('state')!='COMPLETE' or batch.get('protocol')!=FROZEN.to_dict() or batch.get('scientific_execution') is not True:
            raise AssertionError('fixed complete production result required')
        if batch.get('expected')!=FROZEN.expected() or batch.get('admission',{}).get('sha')!=batch.get('launch_sha'):
            raise AssertionError('production expected/source admission binding')
        if batch.get('inherited_cost')!=INHERITED_COST: raise AssertionError('inherited cost binding')
        if batch['sources']!=source_identities(repo): raise AssertionError('source identities changed')
        config=json.loads((out/'config.json').read_text())
        if any(config[k]!=batch[k] for k in config): raise AssertionError('source/config/runtime binding')
        reader_runtime=runtime()
        report['runtime']=reader_runtime
        for key in ('python','compiler','numpy','torch','device','numpy_config','torch_threads','torch_interop_threads','deterministic_algorithms','thread_environment'):
            if reader_runtime[key]!=batch['runtime'][key]: raise AssertionError('frozen numerical/thread identity '+key)
        if reader_runtime['torch_threads']!=1 or reader_runtime['torch_interop_threads']!=1 or any(value!='1' for value in reader_runtime['thread_environment'].values()):
            raise AssertionError('one scientific numerical thread required')
        load_wall,load_cpu=time.perf_counter(),time.process_time()
        actor,parent=load_parent(parent_path)
        report.update(parent_load_wall_seconds=time.perf_counter()-load_wall,parent_load_cpu_seconds=time.process_time()-load_cpu)
        if parent!=batch['parent']: raise AssertionError('reader original P0 file binding')
        report.update(launch_sha=batch['launch_sha'],sources=batch['sources'],parent=parent,
                      canonical_input=dict(path=str(out),summary=file_identity(out/'summary.json'),config=file_identity(out/'config.json')))
        validate_counts(batch['actual'],batch['costs'],FROZEN)
        _read_all(batch,out,actor,FROZEN,report,progress)
        if file_identity(parent_path)['sha256']!=parent['sha256']: raise AssertionError('reader consumed P0 file changed')
        report['status']='VERIFIED'
    except BaseException:
        report.update(status='FAILED',failure=traceback.format_exc(),interrupted_call_work_may_be_unmeasured=True)
        raise
    finally:
        report['finish_utc']=datetime.now(timezone.utc).isoformat();progress();write_json(report_out/'reading.json',report)
    return report


def main(argv=None):
    entry_wall,entry_cpu=time.perf_counter(),time.process_time()
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('out','input-out','parent'): parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--seed',type=int,required=True);parser.add_argument('--launch-sha',required=True)
    args=parser.parse_args(argv)
    if args.seed!=40160000: parser.error('frozen study seed required')
    if args.out.resolve()==args.input_out.resolve(): parser.error('standalone reader needs a fresh --out distinct from --input-out')
    from scripts.hmasd_admission import require_admission
    admission=require_admission(__file__,direction='uav_episode_policy_search')
    if admission['sha']!=args.launch_sha: raise RuntimeError('accepted source mismatch')
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'): os.environ[key]='1'
    import torch
    torch.set_num_threads(1);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True)
    result=read_result(args.input_out,ROOT,args.parent,report_out=args.out)
    result.update(admission=admission,standalone_entry_wall_seconds=time.perf_counter()-entry_wall,standalone_entry_cpu_seconds=time.process_time()-entry_cpu)
    from experiments.candidates.uav_local_history.b01.study import write_json
    write_json(args.out/'reading.json',result)
    return result



def _publication(batch,reading,out):
    """Small scientific Git view; the full measurement reading remains canonical."""
    native=('J','mean_served','service_p10','min_served','zero_service_steps','zero_service_episode',
            'longest_zero_service_streak','mean_sinr_quality','mean_path_length_m','mean_height_m','end_height_m',
            'active_transmitter_ticks','active_transmitter_fraction','boundary_clipped_uav_ticks',
            'same_history_category_changes','same_history_clipped_step_changes','zero_head_max_error')
    comparison=batch['comparisons']
    compact={key:{name:{metric:values[metric] for metric in native} for name,values in comparison[key].items()}
             for key in ('levels','contrasts')}
    compact.update({k:comparison[k] for k in ('worlds','adverses','uncertainty','bootstrap')})
    return dict(object=batch['object'],state=batch['state'],reader_status=reading['status'],launch_sha=batch['launch_sha'],
                sources=batch['sources'],parent=batch['parent'],parent_body=batch['parent_body'],parent_movement=batch['parent_movement'],
                inherited_cost=batch['inherited_cost'],expected=batch['expected'],actual=batch['actual'],
                worker_costs=batch['costs'],reader_costs=reading['policy_costs'],reader_actual=reading['actual'],
                worker_arithmetic=batch['arithmetic_work'],reader_arithmetic=reading['arithmetic_work'],
                center_movement=batch['center_movement'],comparisons=compact,
                diagnostic_scope='Same-history category changes are decision-clock counts. Clipped step changes are alternate one-tick '
                                 'P0 commands at candidate-visited ticks, not a divergent four-tick shadow trajectory. '
                                 'Boundary-clipped ticks count clipped movement, not pairs of aliased categories. '
                                 'The full metric/work/time reading remains in canonical reading.json.',
                canonical_bulk=dict(node=batch['runtime']['host'],path=str(Path(out).resolve()),episode_log=batch['episode_log'],
                                    attempts=batch['attempt_log'],search_artifacts=batch['search_artifacts']),
                resources=dict(worker_cpu_seconds=batch['worker_cpu_seconds'],reader_cpu_seconds=reading['reader_cpu_seconds'],
                               chain_wall_seconds=reading['chain_wall_seconds'],chain_cpu_seconds=reading['chain_cpu_seconds'],
                               worker_peak_rss_kib=batch['worker_peak_rss_kib'],reader_peak_rss_kib=reading['reader_peak_rss_kib'],
                               resources_unmeasured=['staging','launcher_preflight','process_startup_before_main','support'],rss_scope='same sequential process lifetime peaks'))

if __name__=='__main__': main()
