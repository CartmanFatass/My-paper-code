"""Fixed phase composition, complete-file identities and cumulative work ledger."""
from pathlib import Path
import json
import time
import numpy as np
from . import contract as c, io, metrics, read


def raw_path(root,row):
    relative=Path(row['raw']['path']);expected=Path('raw')/row['phase']/f"{row['arm']}_{row['world']}_t{row['tape']}.npz"
    if relative!=expected:raise ValueError('raw address changed')
    path=Path(root)/relative
    if io.identity(path)!={**row['raw'],'path':str(path)}:raise ValueError('raw bytes changed')
    return path


def load_raw(root,row):
    with np.load(raw_path(root,row),allow_pickle=False) as bundle:return {k:bundle[k] for k in bundle.files}


def complete_rows(rows,phase):
    expected=list(c.episode_order(phase))
    if len(rows)!=len(expected) or any({k:row[k] for k in spec}!=spec for row,spec in zip(rows,expected)):
        raise AssertionError('incomplete or reordered fixed '+phase+' panel')


def prefix_identity(root,rows):
    # Validate the saved reset digest, then bind one common world across every
    # arm and tape. Pairwise agreement alone can hide a jointly corrupted pair.
    initial_by_world={}
    for row in rows:
        raw=load_raw(root,row)
        initial=c.initial_state_digest(raw['positions'][0],raw['initial_users'],raw['initial_sinr'],raw['initial_uav_sinr'],raw['initial_connections'])
        read.equal(row['initial_state_sha256'],initial,'initial state binding before prefix checks')
        previous=initial_by_world.setdefault(row['world'],initial)
        if previous!=initial:raise AssertionError('all arms/tapes initial world changed')
    table={(r['arm'],r['world'],r['tape']):r for r in rows};checks=[]
    for row in rows:
        if row['arm'] not in c.PARENTS:continue
        parent=table[c.PARENTS[row['arm']],row['world'],row['tape']]
        if parent['initial_state_sha256']!=row['initial_state_sha256']:raise AssertionError('paired initial world changed')
        z,p=load_raw(root,row),load_raw(root,parent)
        for key in ('observations','commands','reward','served','sinr_quality','sinr','uav_sinr','connections','user_service_mask','transmitter_mask','terminated','truncated'):
            read.equal(z[key][:4],p[key][:4],'first4 parent identity: '+key)
        read.equal(z['positions'][:5],p['positions'][:5],'first4 parent positions')
        for key in ('initial_users','initial_sinr','initial_uav_sinr','initial_connections'):
            read.equal(z[key],p[key],'paired native reset: '+key)
        for key in ('features','source','takeover','nav_pre','nav_next','fallback','action_index','probabilities','innovation','entropy','c_index','policy_scores','policy_served','logits'):
            read.equal(z[key][:5],p[key][:5],'tick0 parent source identity: '+key)
        checks.append({'world':row['world'],'tape':row['tape'],'arm':row['arm'],'parent':parent['arm'],'first_four_transitions_identical':True})
    return checks


def sum_work(results):
    total={}
    for result in results:
        for k,v in result['work'].items():total[k]=total.get(k,0)+v
    return total


def work_table(rows,results,phase,counts):
    complete_rows(rows,phase)
    m=sum(r['metrics']['takeovers'] for r in rows if r['arm'] in ('ZSL0','ZSL1'))
    g=sum(r['metrics']['takeovers'] for r in rows if r['arm']=='ZG')
    actual={k:counts[k] for k in ('episodes','native_steps','constructor_resets','explicit_resets')}
    actual['decision_slots']=sum(r['metrics']['queries'] for r in rows)
    actual['online_count_decodes']=sum(r['online_count_decodes'] for r in rows)
    actual['online_gate_checks']=sum(r['online_gate_checks'] for r in rows)
    worker={}
    for row in rows:
        for agent in row['policy_counts']:
            for source,counters in agent.items():
                kind='C' if source in ('C','G') else 'S'
                actual['worker_'+kind+'_requests']=actual.get('worker_'+kind+'_requests',0)+counters['requests']
                actual['worker_draws']=actual.get('worker_draws',0)+counters['sampled_draws']
                actual['worker_G_probabilities']=actual.get('worker_G_probabilities',0)+counters['score_tail_evaluations']
                for key,value in counters.items():worker[kind+'_'+key]=worker.get(kind+'_'+key,0)+value
    independent=sum_work(results)
    for key in ('reader_C_calls','reader_S_rows','reader_draws','reader_G_probabilities','reader_count_decodes'):actual[key]=independent[key]
    if actual!=c.expected_counts(phase,m,g):raise AssertionError('exact fixed source/query/native work ledger')
    if counts['native_step_calls']!=actual['native_steps']:raise AssertionError('attempted native step count')
    return {'phase':phase,'student_takeovers':m,'G_takeovers':g,'exact':actual,'worker_actual':worker,'reader_actual':independent,
            'native_dense_power_slots':275*(actual['native_steps']+actual['explicit_resets']+actual['constructor_resets']),
            'connection_entries_read':actual['episodes']*256*5*50,
            'slot_presence_tests':20*(actual['online_count_decodes']+actual['reader_count_decodes'])}


def combined_cost(tables,synthetic):
    totals={}
    for table in tables:
        for k,v in table['exact'].items():totals[k]=totals.get(k,0)+v
    def total(section,key):return sum(t[section].get(key,0) for t in tables)
    real_C=total('worker_actual','C_misses')+total('reader_actual','reader_C_calls')
    actor_rows=total('worker_actual','S_neural_rows')+total('reader_actual','reader_S_rows')
    C_ticks=total('worker_actual','C_model_ticks')+total('reader_actual','C_model_ticks')
    C_links=total('worker_actual','C_candidate_links')+total('worker_actual','C_setup_links')+total('reader_actual','C_candidate_links')+total('reader_actual','C_setup_links')
    helper_links=total('worker_actual','S_helper_setup_links')+total('worker_actual','S_helper_extreme_links')+total('reader_actual','helper_setup_links')+total('reader_actual','helper_extreme_links')
    if totals['native_steps']!=126976 or totals['constructor_resets']!=2 or totals['explicit_resets']!=496:raise AssertionError('complete native bound')
    if real_C+synthetic['original_C_calls']>189656 or actor_rows+synthetic['frozen_actor_rows']>211456:raise AssertionError('source query bound')
    if C_links+2260*synthetic['original_C_calls']>240680960 or helper_links+140*synthetic['frozen_actor_rows']>29603840:raise AssertionError('source radio bound')
    return {'totals':totals,'actual_full_C_calculations':real_C,'actual_actor_rows':actor_rows,
            'actual_C_trajectories':27*real_C,'actual_C_modeled_ticks':C_ticks,'actual_C_objective_reductions':C_ticks,
            'actual_C_radio_links':C_links,'actual_helper_radio_links':helper_links,
            'native_dense_power_slots':sum(t['native_dense_power_slots'] for t in tables),
            'geometric_comparison_steps':total('reader_actual','geometric_comparison_steps'),
            'connection_entries_read':sum(t['connection_entries_read'] for t in tables),
            'slot_presence_tests':sum(t['slot_presence_tests'] for t in tables),'synthetic':synthetic,
            'new_fits':0,'optimizer_updates':0,'training_contexts':0,'labels':0,'calibrations':0,'LLM_forwards':0,'downloads':0,'GPU_seconds':0}


def read_phase(root,rows,actors,budget,out,inflight,*,phase):
    complete_rows(rows,phase)
    for row in rows:
        clocks={'reset_wall_seconds','reset_cpu_seconds','gate_query_wall_seconds','gate_query_cpu_seconds','native_step_wall_seconds','native_step_cpu_seconds','raw_write_wall_seconds','raw_write_cpu_seconds'}
        if set(row['times'])!=clocks or any(type(v) not in (float,int) or not np.isfinite(v) or v<0 for v in row['times'].values()):raise ValueError('complete disjoint episode CPU/wall components')
        for clock in ('cpu','wall'):
            if sum(v for k,v in row['times'].items() if k.endswith(clock+'_seconds'))>row['episode_'+clock+'_seconds']+1e-7:raise ValueError('overlapping episode timing components')
    results=[];started_cpu=time.process_time();started_wall=time.perf_counter()
    directory=Path(out)/('audit_checks' if phase=='audit' else 'main_checks');directory.mkdir()
    for row in rows:
        budget.check();inflight.clear();inflight.update(phase=phase,raw=row['raw'],files_completed=len(results))
        t0,t1=time.perf_counter(),time.process_time()
        result=read.check_episode(load_raw(root,row),row,actors,inflight=inflight)
        result.update(raw=row['raw'],reader_cpu_seconds=time.process_time()-t1,reader_wall_seconds=time.perf_counter()-t0,
                      process_peak_rss_kib=io.resource.getrusage(io.resource.RUSAGE_SELF).ru_maxrss)
        path=directory/f"{row['arm']}_{row['world']}_t{row['tape']}.json";io.write_json(path,result)
        item=io.identity(path);item['path']=str(path.relative_to(out))
        results.append({'spec':result['spec'],'raw':row['raw'],'work':result['work'],'checks':item,
                        'reader_cpu_seconds':result['reader_cpu_seconds'],'reader_wall_seconds':result['reader_wall_seconds']})
        io.write_json(Path(out)/(phase+'_reading_progress.json'),{'status':'PARTIAL','results':results,'cost':budget.snapshot(),'inflight':inflight})
        budget.check()
    first4=prefix_identity(root,rows);inflight.clear()
    return {'status':'VERIFIED','phase':phase,'results':results,'first4_parent_identity':first4,
            'reader_cpu_seconds':time.process_time()-started_cpu,'reader_wall_seconds':time.perf_counter()-started_wall,
            'new_native_steps':0,'all_raw_verified':True,'complete_native_and_source_reconstruction':True}


def bound_worker(path,sha,source,actor_sha):
    locator=io.bound_json(path,sha)
    if set(locator)!={'schema','root','config_sha256','summary_sha256'} or locator['schema']!=1:raise ValueError('worker locator schema')
    root=Path(locator['root'])
    if not root.is_absolute() or root.resolve()!=root:raise ValueError('worker canonical external root')
    config=io.bound_json(root/'config.json',locator['config_sha256']);summary=io.bound_json(root/'summary.json',locator['summary_sha256'])
    if (config['mode']!='worker' or config['source_sha256']!=source or config['actor_input_sha256']!=actor_sha
            or config['contract']!=json.loads(json.dumps(c.contract()))
            or summary['status']!='COMPLETE' or summary['mode']!='worker'
            or config['seed']!=c.MASTER or summary['seed']!=c.MASTER
            or summary['launch_sha']!=config['launch_sha'] or config['launch_sha']!=config['admission']['sha']):
        raise ValueError('worker source/input/complete identity')
    rows_value=io.bound_json(root/'episodes.json',summary['episodes']['sha256']);rows=rows_value['rows']
    audit=[r for r in rows if r['phase']=='audit'];main=[r for r in rows if r['phase']=='main']
    complete_rows(audit,'audit');complete_rows(main,'main')
    expected={str(Path(r['raw']['path'])) for r in rows}
    if {str(p.relative_to(root)) for p in (root/'raw').rglob('*') if p.is_file()}!=expected:raise ValueError('extra/missing worker raw evidence')
    for row in rows:raw_path(root,row)
    audit_reading=io.bound_json(root/'audit_reading.json',summary['audit_reading']['sha256'])
    if (audit_reading['status']!='VERIFIED' or audit_reading['source_sha256']!=source
            or audit_reading['actor_input_sha256']!=actor_sha or audit_reading['new_native_steps']!=0
            or not audit_reading['all_raw_verified'] or not audit_reading['complete_native_and_source_reconstruction']
            or [r['raw'] for r in audit_reading['results']]!=[r['raw'] for r in audit]):raise ValueError('complete bound audit reading')
    for result in audit_reading['results']:
        check=result['checks'];p=root/check['path']
        if io.identity(p)!={**check,'path':str(p)}:raise ValueError('audit check bytes changed')
        payload=io.bound_json(p,check['sha256'])
        if payload['raw']!=result['raw'] or payload['work']!=result['work']:raise ValueError('audit check content binding')
    return root,config,summary,audit,main,audit_reading
