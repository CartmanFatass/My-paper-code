"""Only synthetic arrays, fake agents/hosts and mocked admission/resource calls."""
import contextlib
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from experiments.candidates.uav_decision_generalization.b03_joint_window import evidence as e, independent as oldreader, worker as oldworker, trace, adapter
from experiments.candidates.uav_decision_generalization.b04_set_mean import bindings as b, contract as c, reader, run, worker

ROOT = Path(__file__).resolve().parents[5]


def meter():
    return e.Meter({'schema': 1, 'prior_cpu_seconds': 0., 'prior_counts': {}})


@pytest.mark.parametrize('deterministic', [False, True])
def test_frozen_dispatch_reset_seed_terminal_rng_and_immutable(monkeypatch, tmp_path, deterministic):
    events = []
    state = np.zeros(154, dtype=np.float32)
    env = SimpleNamespace(host=SimpleNamespace(event_counts={'native_steps': 0}), close=lambda: events.append('close'))
    env.reset = lambda seed: (events.append(('reset', seed)) or (np.zeros((6,211)), {'state': state}))
    agent = SimpleNamespace(train=lambda mode: events.append(('train', mode)), reset_env_state=lambda index: events.append(('agent-reset', index)), d2_enabled=False)
    def step(*args, **kwargs):
        events.append(('step', kwargs['deterministic']))
        return np.zeros((1,6,3), dtype=np.float32), None, {}
    agent.step = step
    class FakeTrace:
        initial_host_rng = {'mock': True}
        def __init__(self, *args): pass
        def initial_digest(self): return 'initial'
        def policy(self, *args): pass
        def transition(self, *args): pass
        def summary(self): return {'W': 0}
        def arrays(self): return {}
    monkeypatch.setattr(adapter, 'make_env', lambda world: env)
    monkeypatch.setattr(trace, 'EpisodeTrace', FakeTrace)
    monkeypatch.setattr(trace, 'reset_context', lambda a: {'reset': True})
    monkeypatch.setattr(e, 'digest_agent', lambda a: 'frozen')
    monkeypatch.setattr(e, 'seed_rng', lambda seed: events.append(('seed', seed)))
    monkeypatch.setattr(e, 'rng_state', lambda: {'mock': len([x for x in events if isinstance(x,tuple) and x[0]=='step'])})
    monkeypatch.setattr(e, 'instrument_agent', lambda a,m: contextlib.nullcontext({'mock': 0}))
    def native(env, action, m, category):
        m.add('native_step_attempts'); m.add('native_steps'); m.add(category)
        tick = env.host.event_counts['native_steps'];env.host.event_counts['native_steps'] += 1
        return np.zeros((6,211)), None, tick == 499, False, {'next_state': state}
    monkeypatch.setattr(oldworker, 'native_transition', native)
    e.write_json(tmp_path/'config.json', {})
    store = SimpleNamespace(meter=meter(), out=tmp_path, args=SimpleNamespace(launch_sha='launch'), config={'source_sha256':{}}, inflight=lambda *a,**k:None,
                            record=lambda kind,arrays,metadata,path:metadata, failed_trace=lambda traces:events.append('partial'))
    kw = {'deterministic': True} if deterministic else {}
    result = oldworker.frozen_mission(store, 'SET-initial-mean', c.WORLDS[0], 'main', agent, {}, **kw)
    assert [x for x in events if isinstance(x,tuple) and x[0]=='step'] == [('step',deterministic)]*500
    assert events.index(('agent-reset',0)) < events.index(('seed',c.WORLDS[0]+51))
    assert result['inference_mode'] == (c.MODE if deterministic else 'sampled')
    assert result['pre_world_rng']=={'mock':0} and result['terminal_rng']=={'mock':500}
    assert result['optimizer_steps']==0 and store.meter.counts['native_steps']==500
    calls=iter(['frozen','changed'])
    monkeypatch.setattr(e,'digest_agent',lambda a:next(calls))
    env.host.event_counts['native_steps'] = 0
    with pytest.raises(AssertionError,match='normalizer changed'):
        oldworker.frozen_mission(store,'SET-initial-mean',c.WORLDS[0],'main',agent,{},deterministic=deterministic)
    assert events[-2:]==['partial','close']


def replay_fixture(monkeypatch, deterministic=True):
    calls=[]
    agent=SimpleNamespace(reset_env_state=lambda i:calls.append('reset'), use_central_snapshot=False,d2_enabled=False,
        get_prev_actor_hidden_np=lambda *a,**k:np.zeros((6,2)),get_prev_critic_hidden_np=lambda *a,**k:np.zeros((6,2)))
    def step(*a,**kw):
        calls.append(kw['deterministic']);return np.zeros((1,6,3)),None,{'log_probs':[{}]}
    agent.step=step
    monkeypatch.setattr(e,'seed_rng',lambda s:None)
    monkeypatch.setattr(e,'restore_rng',lambda r:None)
    monkeypatch.setattr(e,'rng_state',lambda:{'state':True})
    monkeypatch.setattr(e,'digest_agent',lambda a:'digest')
    monkeypatch.setattr(e,'instrument_agent',lambda a,m:contextlib.nullcontext({'fake':0}))
    monkeypatch.setattr(trace,'reset_context',lambda a:{'mock_reset':True})
    raw={'states':np.zeros((501,154)), 'observations':np.zeros((501,6,211)), 'raw_actions':np.zeros((500,6,3)),
         'actor_hidden_input':np.zeros((500,6,2)),'critic_hidden_input':np.zeros((500,6,2))}
    for key in ('team_log_prob','state_value'):raw['coord__'+key]=np.zeros(500,dtype=np.float32)
    for key in ('agent_log_probs','agent_values'):raw['coord__'+key]=np.zeros((500,6),dtype=np.float32)
    meta={'world':c.WORLDS[0],'pre_world_rng':{'state':True}}
    if deterministic:meta.update(inference_mode=c.MODE,terminal_rng={'state':True},reset_context={'mock_reset':True})
    return agent,raw,meta,calls


@pytest.mark.parametrize('deterministic',[False,True])
def test_replay_mean_and_historical_sampled_default(monkeypatch, deterministic):
    agent,raw,meta,calls=replay_fixture(monkeypatch,deterministic)
    m=meter()
    kw={'deterministic':True} if deterministic else {}
    result=oldreader.replay_model(agent,{'state_digest':'digest'},raw,meta,m,**kw)
    assert calls==['reset']+[deterministic]*500
    assert result['frozen_state_digest']=='digest'
    assert m.counts=={'reader_model_team_steps':500,'reader_actor_agent_rows':3000,'reader_critic_agent_rows':3000}


@pytest.mark.parametrize('defect',['mode','terminal','missing_terminal','digest','optimizer','mutation'])
def test_replay_refuses_binding_or_effect_failure(monkeypatch,defect):
    agent,raw,meta,calls=replay_fixture(monkeypatch)
    if defect=='mode':meta['inference_mode']='sampled'
    if defect=='terminal':meta['terminal_rng']={'changed':True}
    if defect=='missing_terminal':meta.pop('terminal_rng')
    if defect=='digest':monkeypatch.setattr(e,'digest_agent',lambda a:'wrong')
    if defect=='mutation':
        seq=iter(['digest','changed']);monkeypatch.setattr(e,'digest_agent',lambda a:next(seq))
    if defect=='optimizer':monkeypatch.setattr(e,'instrument_agent',lambda a,m:contextlib.nullcontext({'fake':1}))
    with pytest.raises(AssertionError):oldreader.replay_model(agent,{'state_digest':'digest'},raw,meta,meter(),deterministic=True)
    if defect in ('mode','missing_terminal','digest'):assert True not in calls


def test_roster_counts_zero_updates_and_watchdogs(monkeypatch):
    rows=[dict(programme=p,world=w,phase=s) for p,w,s in c.roster()]
    b.validate_roster(rows)
    for bad in (rows[:-1],rows+[rows[0]],rows[:-1]+[rows[0]],rows[:-1]+[dict(rows[-1],world=0)]):
        with pytest.raises(ValueError):b.validate_roster(bad)
    for mode,expected in [('worker',c.WORKER_COUNTS),('reader',c.READER_COUNTS)]:
        m=meter();m.counts=expected.copy();b.check_counts(m,mode,True)
        m.counts['optimizer_discoverer_critic']=1
        with pytest.raises(AssertionError):b.check_counts(m,mode)
        m.counts=expected.copy();m.counts[next(iter(expected))]-=1
        with pytest.raises(AssertionError):b.check_counts(m,mode,True)
    m=meter();monkeypatch.setattr(m,'resources',lambda:{'cumulative_cpu_seconds':7201,'wall_seconds':0})
    with pytest.raises(RuntimeError):b.check_counts(m,'worker')
    m=meter();m.counts['native_step_attempts']=1
    with pytest.raises(AssertionError):b.check_counts(m,'reader')


def test_stage_ledger_carries_checks_worker_cost_exactly():
    previous={'schema':1,'prior_cpu_seconds':2.,'prior_counts':{'checks':1,'model_constructions':1}}
    worker_summary={'new_native_steps':33000,'new_fits':0,'optimizer_steps':0,'cost':{
        'prior':previous,'counts':c.WORKER_COUNTS.copy(),'resources':{'cumulative_cpu_seconds':10.}}}
    ledger={'schema':1,'prior_cpu_seconds':10.,'prior_counts':dict(previous['prior_counts'],**c.WORKER_COUNTS)}
    ledger['prior_counts']['model_constructions']=3
    b.bind_ledger(ledger,worker_summary)
    for bad in [dict(ledger,prior_cpu_seconds=9.),dict(ledger,prior_counts=c.WORKER_COUNTS),dict(ledger,prior_counts={**ledger['prior_counts'],'extra':1})]:
        with pytest.raises(ValueError):b.bind_ledger(bad,worker_summary)


def test_accepted_source_output_duplicate_guard_and_admission_first(monkeypatch,tmp_path):
    from scripts import hmasd_admission as admission
    from scripts.hmasd_launch import _validate_guard_contract
    _validate_guard_contract(ROOT/'experiments/candidates/uav_decision_generalization/b04_set_mean/run.py',c.DIRECTION)
    args=SimpleNamespace(out=tmp_path,launch_sha='sha')
    accepted={'sha':'sha','command_sha256':'cmd'}
    paths={'source_root':str(ROOT),'output_root':str(tmp_path)}
    e.write_json(tmp_path/'launch-manifest.json',dict(paths,direction=c.DIRECTION,sha='sha',command_sha256='cmd'))
    assert run.accepted_output(args,accepted,paths)==(ROOT,tmp_path)
    with pytest.raises(ValueError):run.accepted_output(SimpleNamespace(out=tmp_path,launch_sha='wrong'),accepted,paths)
    for name in ('config.json','summary.json','manifest.json','reading.json','raw'):
        path=tmp_path/name;path.write_text('{}')
        with pytest.raises(FileExistsError):run.accepted_output(args,accepted,paths)
        path.unlink()
    effects=[]
    def refuse(*a,**k):effects.append('admission');raise RuntimeError('mock refused')
    monkeypatch.setattr(admission,'require_admission',refuse)
    monkeypatch.setattr(run,'accepted_output',lambda *a:pytest.fail('effects before admission'))
    with pytest.raises(RuntimeError,match='mock refused'):
        run.main(['--mode','worker','--seed',str(c.MASTER),'--launch-sha','sha','--out',str(tmp_path),
                  '--study-input','unused','--study-input-sha256','x','--budget-ledger','unused','--budget-ledger-sha256','y'])
    assert effects==['admission']


def test_resource_request_is_mocked_and_uses_selected_floors(monkeypatch,tmp_path):
    from scripts import hmasd_resource_preflight as p
    monkeypatch.setattr(p,'capture_snapshot',lambda:{'mock':True})
    monkeypatch.setattr(p,'assess_memory_floor',lambda s:{'available_physical_bytes':8*1024**3,'effective_available_bytes':8*1024**3})
    monkeypatch.setattr(run.shutil,'disk_usage',lambda p:SimpleNamespace(free=4*1024**3))
    assert run.resource_request(tmp_path)['requested_disk_free_bytes']==4*1024**3
    monkeypatch.setattr(run.shutil,'disk_usage',lambda p:SimpleNamespace(free=4*1024**3-1))
    with pytest.raises(RuntimeError):run.resource_request(tmp_path)


def metric(W):
    return {'W':W,'coverage_backhauled':.1,'total_path_length_m':30.,
            'user_details':[{'user':u,'served_ticks':0,'longest_gap':500,'leading_gap':500,'trailing_gap':500,
                             'gaps':[{'start':0,'stop':500,'length':500,'left_censored':True,'right_censored':True}]} for u in range(50)],
            'window_details':[{'window':w,'cluster':w,'completed':w<W,'qualified_ticks':20 if w<W else 0,
                              'max_consecutive_qualified_ticks':20 if w<W else 0,'max_active_users':8 if w<W else 0} for w in range(4)]}


def test_complete_reference_join_mode_interaction_adverse_and_matched_tails():
    rows=[{'programme':p,'world':w,'phase':s,'metrics':metric(int(p==c.PROGRAMMES[0]))} for p,w,s in c.roster()]
    refs=[{'programme':p,'world':w,'phase':s,'metrics':metric(int(p=='SET-final' and w in c.WORLDS[:2]))} for p,w,s in c.roster(c.BASELINES)]
    result=reader.comparisons(rows,refs)
    primary=c.PROGRAMMES[1]+' minus '+c.PROGRAMMES[0]
    assert result['contrasts'][primary]['W']['mean']==-1
    assert result['mode_interaction']['W']['mean']==-1.0625
    assert result['case_worlds'][primary]['adverse_worlds']==list(c.WORLDS)
    assert len(result['matched_tails'][primary])==32 and len(result['matched_tails'][primary][0]['users'])==50
    assert result['matched_tails'][primary][0]['windows'][0]['qualified_ticks_delta']==-20
    with pytest.raises(ValueError):reader.comparisons(rows,refs[:-1])
    refs[0]['metrics']['user_details'][0]['user']=1
    with pytest.raises(AssertionError):reader.comparisons(rows,refs)


def test_worker_exact_66_dispatch_two_constructions_no_ordinary(monkeypatch,tmp_path):
    calls=[]
    m=meter()
    monkeypatch.setattr(e,'digest_agent',lambda a:'digest')
    def load(ancestor, endpoint, out, programme, meter):
        meter.add('model_constructions');calls.append(('construct',endpoint));return object(),{'state_digest':'digest'}
    monkeypatch.setattr(worker,'load_endpoint',load)
    def mission(store,programme,world,phase,agent,checkpoint,*,deterministic):
        assert deterministic and checkpoint==c.CHECKPOINTS[c.ENDPOINTS[programme]]
        calls.append((programme,world,phase))
        for key in ('native_step_attempts','native_steps','frozen_native_steps','frozen_model_steps'):store.meter.add(key,500)
        for name in ('actor', 'critic'):
            key = 'frozen/mock|skill_discoverer.' + name
            item = store.meter.calls.setdefault(key, {'leading_rows': 0})
            item['leading_rows'] += 3000
        store.manifest['frozen'].append(dict(programme=programme,world=world,phase=phase))
    monkeypatch.setattr(oldworker,'frozen_mission',mission)
    worker.run(ROOT,tmp_path,SimpleNamespace(launch_sha='sha',seed=c.MASTER),{'meter':m,'config':{},'ancestor':{}})
    assert [v for v in calls if len(v)==3]==c.roster()[:32]+[c.roster()[-2]]+c.roster()[32:64]+[c.roster()[-1]]
    assert [v for v in calls if len(v)==2]==[('construct','initial'),('construct','final')]
    assert json.loads((tmp_path/'summary.json').read_bytes())['new_native_steps']==33000
    assert not (tmp_path/'checkpoints').exists()


def test_worker_context_exact_input_source_and_wrong_hash_refusal(tmp_path):
    config={'mode':'worker','launch_sha':'worker','contract':c.frozen_contract(),'source_sha256':{'p':'sha'},
            'ancestor':c.ANCESTOR,'baseline_reading':c.READING,'study_input':{'sha256':'study'}}
    summary={'status':'COMPLETE','launch_sha':'worker','object':c.OBJECT,'inference_mode':c.MODE}
    manifest={'object':c.OBJECT,'inference_mode':c.MODE,'frozen':[dict(programme=p,world=w,phase=s) for p,w,s in c.roster()],'checkpoints':c.CHECKPOINTS}
    for name,value in [('config',config),('summary',summary),('manifest',manifest)]:e.write_json(tmp_path/(name+'.json'),value)
    locator={'schema':1,'root':str(tmp_path),**{name+'_sha256':e.hash_file(tmp_path/(name+'.json')) for name in ('config','summary','manifest')}}
    assert b.worker_context(locator,config)['manifest']==manifest
    bad=copy.deepcopy(config);bad['source_sha256']['p']='different'
    with pytest.raises(ValueError):b.worker_context(locator,bad)
    bad=copy.deepcopy(config);bad['study_input']['sha256']='different'
    with pytest.raises(ValueError):b.worker_context(locator,bad)
    with pytest.raises(ValueError):b.worker_context(dict(locator,manifest_sha256='wrong'),config)


def test_study_complete_paid_check_join_source_exceptions_and_wrong_identities(monkeypatch,tmp_path):
    a02=tmp_path/'b03_joint_window_read_a02';a01=tmp_path/'b03_joint_window_read_a01'
    ancestor_root=tmp_path/'ancestor';ancestor_root.mkdir()
    monkeypatch.setattr(c,'ANCESTOR',{'schema':1,'root':str(ancestor_root),'config_sha256':'cfg','summary_sha256':'sum','manifest_sha256':'man'})
    ancestor={'worker_root':ancestor_root,'worker_config':{'launch_sha':'old'},'manifest':{'checkpoints':{'SET':{}}}}
    checkpoints={}
    for endpoint in ('initial','final'):
        f=ancestor_root/(endpoint+'.bin');f.write_bytes(b'fake checkpoint bytes, never deserialized')
        checkpoints[endpoint]=e.identity(f,ancestor_root)
    monkeypatch.setattr(c,'CHECKPOINTS',checkpoints)
    ancestor['manifest']['checkpoints']['SET']=checkpoints
    from experiments.candidates.uav_decision_generalization.b03_joint_window import run as b03run
    monkeypatch.setattr(b03run,'worker_context',lambda locator:ancestor)
    checks=[];paid=[];prefix=[]
    for programme,world,phase in c.roster(c.BASELINES):
        metrics=metric(0)
        result={'programme':programme,'world':world,'phase':phase,'raw':{'sha256':'raw'},'metadata':{'sha256':'meta'},'metrics':metrics}
        root=a01 if programme.startswith('SET-') or (programme=='O' and world==c.WORLDS[0] and phase=='main') else a02
        path=root/'checks'/'frozen'/f'{programme}_{world}.json';e.write_json(path,result)
        identity=e.identity(path)
        checks.append(dict(programme=programme,world=world,phase=phase,identity=identity))
        if root==a01:prefix.append(e.identity(path,root))
        paid.append({**result,'metrics':{k:v for k,v in metrics.items() if k!='user_details'}})
    baseline_sources={f'base_{k}.py':'fixed' for k in range(44)}|{p:'old' for p in c.EXCEPTIONS}
    reading={'source_sha256':baseline_sources,'frozen_results':paid,'worker_config':{'sha256':'cfg'},'worker_summary':{'sha256':'sum'},'worker_manifest':{'sha256':'man'},
             'reused_prefix':{'root':str(a01),'checks':{'frozen':prefix}}}
    path=a02/'reading.json';e.write_json(path,reading)
    identity=e.identity(path);monkeypatch.setattr(c,'READING',{k:identity[k] for k in ('path','sha256')})
    sources={**baseline_sources,**{p:'extended' for p in c.EXCEPTIONS},'new_b04.py':'new'}
    study={'schema':1,'contract':c.frozen_contract(),'source_sha256':sources,'ancestor':c.ANCESTOR,'baseline_reading':identity,'baseline_checks':checks}
    assert len(b.study_context(study,sources)['baseline_results'])==132
    changed=dict(sources,**{'base_0.py':'changed'})
    altered={**study,'source_sha256':changed}
    with pytest.raises(ValueError,match='inherited'):b.study_context(altered,changed)
    altered=copy.deepcopy(study);altered['baseline_checks'][0]['identity']['sha256']='wrong'
    with pytest.raises(AssertionError):b.study_context(altered,sources)
    altered=copy.deepcopy(study);altered['baseline_checks'][0]['world']=0
    with pytest.raises(ValueError):b.study_context(altered,sources)
    altered=copy.deepcopy(study);altered['ancestor']['root']='wrong'
    with pytest.raises(ValueError):b.study_context(altered,sources)


def test_actual_neural_hook_rows_are_required_not_assumed_from_steps():
    m=meter();m.counts=c.WORKER_COUNTS.copy()
    with pytest.raises(AssertionError):b.neural_rows(m,terminal=True)
    for name in ('actor','critic'):
        m.observe_forward('skill_discoverer.'+name,(np.zeros((6,3)),))
        assert m.calls['entry|skill_discoverer.'+name]['leading_rows']==6
    assert b.neural_rows(m)=={'actor':6,'critic':6}
    m.calls={f'phase|skill_discoverer.{name}':{'leading_rows':198000} for name in ('actor','critic')}
    assert b.neural_rows(m,terminal=True)=={'actor':198000,'critic':198000}


def test_replay_wrong_recurrent_reset_refuses_before_first_action(monkeypatch):
    agent,raw,meta,calls=replay_fixture(monkeypatch)
    meta['reset_context']={'wrong':True}
    with pytest.raises(AssertionError,match='recurrent reset'):
        oldreader.replay_model(agent,{'state_digest':'digest'},raw,meta,meter(),deterministic=True)
    assert calls==['reset']


def test_current_source_manifest_binds_all_b04_files_and_inherited_sources():
    sources=b.source_manifest(ROOT)
    expected=e.source_manifest(ROOT)
    assert expected.items() <= sources.items()
    owned=ROOT/'experiments/candidates/uav_decision_generalization/b04_set_mean'
    assert all(str(path.relative_to(ROOT)) in sources for path in owned.glob('*.py'))
    assert all(e.hash_file(ROOT/path)==sha for path,sha in sources.items())


def test_complete_reader_output_and_counters_without_physics_or_model(monkeypatch,tmp_path):
    from experiments.candidates.uav_decision_generalization.b03_joint_window import contract as b03
    root=tmp_path/'worker';out=tmp_path/'reader';m=meter()
    raw={key:np.zeros((501,)+shape,dtype=dtype) for key,(shape,dtype) in b03.STATE_FIELDS.items()}
    raw.update(users=np.zeros((50,2)),schedule=np.zeros(4),packet=np.zeros(404),bs_positions=np.zeros((1,3)),
               observations=np.zeros((501,6,211)),states=np.zeros((501,154)))
    initial=[raw[k] for k in ('users','schedule','packet','bs_positions')]+[raw[k][0] for k in b03.STATE_FIELDS]+[raw[k][0] for k in ('observations','states')]
    digest=e.array_digest(*initial)
    rows=[]
    for programme,world,phase in c.roster():
        meta={'programme':programme,'world':world,'phase':phase,'object':b03.OBJECT,'inference_mode':c.MODE,
              'terminal_rng':{},'source_sha256':{'source':'sha'},'worker_config_sha256':'config','launch_sha':'worker',
              'checkpoint':c.CHECKPOINTS[c.ENDPOINTS[programme]],'state_digest':'digest','optimizer_steps':0,'sampling_seed':world+51,
              'counts_delta':{k:500 for k in ('native_step_attempts','native_steps','frozen_native_steps','frozen_model_steps')},
              'metrics':{},'initial_state_sha256':digest}
        path=root/(programme+'_'+str(world)+'.json');e.write_json(path,meta)
        rows.append(dict(programme=programme,world=world,phase=phase,metadata=e.identity(path,root),raw={}))
    def load(ancestor,endpoint,out,programme,meter):
        meter.add('model_constructions');return object(),{'state_digest':'digest'}
    monkeypatch.setattr(reader,'load_endpoint',load)
    monkeypatch.setattr(oldreader,'load_arrays',lambda *a:raw)
    def check(raw,world,full,meter):
        assert full
        for k,v in c.READER_COUNTS.items():
            if k not in ('model_constructions','reader_model_team_steps','reader_actor_agent_rows','reader_critic_agent_rows'):meter.add(k,v//66)
        return {'world':world,'metrics':metric(0),'max_errors':{}},raw
    monkeypatch.setattr(oldreader,'check_episode',check)
    monkeypatch.setattr(oldreader,'compare_worker_metrics',lambda *a:None)
    def replay(agent,payload,raw,metadata,meter,*,deterministic):
        assert deterministic
        meter.add('reader_model_team_steps',500);meter.add('reader_actor_agent_rows',3000);meter.add('reader_critic_agent_rows',3000)
        for name in ('actor','critic'):
            meter.calls.setdefault('mock|skill_discoverer.'+name,{'leading_rows':0})['leading_rows']+=3000
        return {'mock':True}
    monkeypatch.setattr(oldreader,'replay_model',replay)
    refs=[{'programme':p,'world':w,'phase':s,'metrics':metric(int(p=='SET-final' and w in c.WORLDS[:2]))} for p,w,s in c.roster(c.BASELINES)]
    context={'meter':m,'manifest':{'object':c.OBJECT,'inference_mode':c.MODE,'frozen':rows},'ancestor':{},
             'worker_root':root,'source_sha256':{'source':'sha'},'config_identity':{'sha256':'config'},
             'worker_config':{'launch_sha':'worker'},'summary_identity':{},'manifest_identity':{},
             'baseline_results':refs,'baseline_reading_identity':{},'baseline_reading':{'cost':{'retained':True}}}
    reader.run(ROOT,out,SimpleNamespace(launch_sha='reader'),context)
    summary=json.loads((out/'summary.json').read_bytes());reading=json.loads((out/'reading.json').read_bytes())
    assert summary['status']=='COMPLETE' and summary['frozen_checked']==66
    assert summary['new_native_steps']==summary['new_fits']==summary['optimizer_steps']==0
    assert summary['actual_neural_agent_rows']=={'actor':198000,'critic':198000}
    assert len(reading['frozen_results'])==66 and reading['coverage_counts']==c.READER_COUNTS
    assert len(list((out/'checks'/'frozen').glob('*.json')))==66
    assert reading['retained_baseline_cost']=={'retained':True}
