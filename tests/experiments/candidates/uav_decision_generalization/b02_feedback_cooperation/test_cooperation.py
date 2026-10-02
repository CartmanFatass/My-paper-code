"""Bounded original-C arithmetic and fake actor/native wiring; no checkpoint loads."""
import ast
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
import torch
from experiments.candidates.uav_decision_generalization.b02_feedback_cooperation import contract as c,collect,io,metrics,phases,policy,read,run
from experiments.candidates.uav_fleet_adaptation.b02 import controllers as kernels
from experiments.candidates.uav_fleet_transmission.b05_score_sampling import policies as laws
from experiments.candidates.uav_fleet_adaptation.b02 import policies as sampling


@pytest.fixture(scope='module',autouse=True)
def usage():
    counts={'original_C_calls':0,'frozen_actor_rows':0,'count_decodes':0,'fake_actor_rows':0,'fake_native_step_calls':0}
    patch=pytest.MonkeyPatch()
    original=kernels.original.LocalController.act
    def act(*args,**kwargs):
        counts['original_C_calls']+=1
        assert counts['original_C_calls']<=c.SYNTHETIC_LIMITS['original_C_calls']
        return original(*args,**kwargs)
    patch.setattr(kernels.original.LocalController,'act',act)
    own=policy.own_count
    def decode(row):counts['count_decodes']+=1;return own(row)
    patch.setattr(policy,'own_count',decode)
    native=read.native
    def native_rows(raw,h):counts['count_decodes']+=(h+1)*5;return native(raw,h)
    patch.setattr(read,'native',native_rows)
    yield counts
    assert counts['count_decodes']<=10000
    print('B02_SYNTHETIC_USAGE='+json.dumps(counts,sort_keys=True))
    patch.undo()


def row(q=0,xyz=(.5,.5,.5),clock=0):
    result=np.zeros(104,dtype=np.float32);result[:3]=xyz;result[-1]=clock
    result[3:3+q*3].reshape(q,3)[:,2]=.26
    return result


def test_fixed_contract_and_cost_arithmetic():
    audit,main=list(c.episode_order('audit')),list(c.episode_order('main'))
    assert len(audit)==16 and len(main)==480 and len({(x['world'],x['arm'],x['tape']) for x in main})==480
    assert main[15]['arm']=='G' and main[15]['tape']==0
    for phase,m,g in [('main',40320,20160),('audit',1260,630)]:
        value=c.expected_counts(phase,m,g)
        assert value['reader_S_rows']==value['worker_S_requests']+m
        assert value['reader_draws']==value['worker_draws']+m+g
        assert value['reader_C_calls']==value['worker_C_requests']
    assert (122880+4096)==126976 and 275*(126976+496+2)==35055350
    with pytest.raises(ValueError):c.expected_counts('main',40321,0)


def test_window_uses_rows_one_through_four_and_boundaries():
    switch=policy.Switch('ZG');out=[]
    for tick,q in enumerate((5,0,0,0,0,2,0,0,0,0,0,0,0)):out.append(switch.observe(row(q),tick))
    assert out[0]['source']=='G' and out[4]['source']=='C'
    assert out[8]['source']=='G' and out[12]['source']=='C'
    assert all(not x['query'] and not x['source'] for t,x in enumerate(out) if t%4)
    assert switch.count_decodes==13 and switch.gate_checks==3
    with pytest.raises(ValueError):switch.observe(row(),14)
    capped=policy.Switch('ZSL0');assert capped.observe(row(20),0)['q']==10
    baseline=policy.Switch('G');baseline.observe(row(),0);assert baseline.count_decodes==0


def test_only_chosen_source_and_one_actual_nav():
    queries=[]
    class Fake:
        def __init__(self,arm,actor,**address):self.arm=arm;self.counters={}
        def query(self,observation,tick,nav):
            queries.append((self.arm,tick,nav));return {'next_nav':(nav+1)%10,'command':np.ones(3,dtype=np.float32),'action_index':26}
    program=policy.AgentProgram('ZSL0',row(),world=1,agent=0,sampling_root=2,actors=(object(),object()),factory=Fake)
    initial=program.nav
    for tick in range(9):program.step(row(),tick)
    assert queries==[('S_L0',0,initial),('C',4,(initial+1)%10),('C',8,(initial+2)%10)]
    assert program.nav==(initial+3)%10 and program.held==26


def test_private_cache_draw_and_original_empty_branch():
    a=laws.FixedPolicy('C',None,world=1,agent=0,sampling_root=2)
    empty=row();nav=kernels.initial_nav(empty)
    first=a.query(empty,0,nav);second=a.query(row(clock=.5),4,nav)
    assert not first['memo_hit'] and second['memo_hit']
    assert a.counters['trajectories']==27 and a.counters['model_ticks']==108 and a.counters['objective_reductions']==108
    assert a.counters['candidate_links']==a.counters['setup_links']==0 and first['fallback']
    assert np.array_equal(first['scores'],np.zeros(27)) and np.array_equal(first['served'],np.zeros(27))
    b=laws.FixedPolicy('G',None,world=1,agent=0,sampling_root=2)
    before=b.query(empty,0,nav);after=b.query(empty,8,nav)
    assert b.counters['misses']==1 and b.counters['hits']==1 and b.counters['sampled_draws']==2
    assert after['innovation']==sampling.indexed_uniform(2,1,8,0)
    assert before['innovation']!=after['innovation']
    assert b.base._cache is not a.base._cache
    changed=empty.copy();changed[0]+=np.float32(.01);a.query(changed,8,nav)
    assert a.counters['misses']==2


def test_functional_probability_rounding_and_clipping():
    scores=np.linspace(-.3,.1,27);base={'scores':scores,'action_index':11,'logits':np.linspace(-.9,1.3,27,dtype=np.float32)}
    assert np.array_equal(read.probabilities('G',base),laws.score_tail_probabilities(scores,11))
    for source,t in [('SL0',1),('SL1',1),('Bstar0',2)]:
        assert np.array_equal(read.probabilities(source,base),sampling.categorical_probabilities(base['logits'].astype(np.float64)/t))
    p=read.probabilities('G',base);u,index=read.sample('G',base,p,2,1,8,0)
    assert u==sampling.indexed_uniform(2,1,8,0) and index==sampling.categorical_index(p,u)
    assert read.sample('C',base,read.probabilities('C',base),None,1,8,0)==(-1.,11)
    assert np.array_equal(read.clipped_path((1000,1000,50),(1,1,-1)),read.clipped_path((1000,1000,50),(0,0,0)))


class FakeActor:
    def __init__(self,usage):self.usage=usage
    def __call__(self,x):
        assert x.shape==(1,114) and x.dtype==torch.float32
        self.usage['fake_actor_rows']+=1
        return torch.arange(27,dtype=torch.float32).reshape(1,27)*.04


class FakeNative:
    """No propagation, assignment or native environment query; always zero service."""
    def __init__(self,usage,h=8):self.usage=usage;self.h=h;self.env=self;self.transmitter_mask=np.ones(5,dtype=bool)
    def reset(self,seed):
        self.t=0;self.xyz=np.array([[300+i*50,400,100] for i in range(5)],dtype=np.float64)
        self.users=np.zeros((50,2),dtype=np.float64)
        self.sinr_matrix=np.full((5,50),-10.,dtype=np.float64);self.uav_sinr_matrix=np.full((5,5),-10.,dtype=np.float64)
        self.connections=np.zeros((5,50),dtype=bool)
        return self.obs(),self.info()
    def obs(self):
        rows=np.zeros((5,104),dtype=np.float32);rows[:,:2]=self.xyz[:,:2]/1000;rows[:,2]=(self.xyz[:,2]-50)/100;rows[:,-1]=self.t/self.h
        return rows
    def info(self):
        return {'state_info':{'uav_positions':self.xyz,'user_positions':self.users},'rewards_dict':{f'uav_{i}':0. for i in range(5)},
                'infos_dict':{'uav_0':{'global':{'connections':self.connections,'sinr_matrix':self.sinr_matrix,'served_users':0}}}}
    def step(self,commands):
        self.usage['fake_native_step_calls']+=1;self.xyz=np.clip(self.xyz+30*commands.astype(np.float64),(0,0,50),(1000,1000,150));self.t+=1
        return self.obs(),0.,self.t==self.h,False,self.info()


@pytest.fixture(scope='module')
def panel(tmp_path_factory,usage):
    out=tmp_path_factory.mktemp('b02_fake');actors=(FakeActor(usage),FakeActor(usage));rows=[];checks=[]
    for arm in c.ARMS:
        spec={'phase':'audit','arm':arm,'world':108310900,'tape':-1 if arm=='C' else 0,'sampling_root':None if arm=='C' else c.AUDIT_ROOT}
        result=collect.episode(FakeNative(usage),spec,actors,out,{}, {},horizon=8);rows.append(result)
        checked=read.check_episode(phases.load_raw(out,result),result,actors,horizon=8);checks.append(checked)
    return out,rows,checks,actors


def test_complete_collector_reader_and_takeover_cost(panel):
    out,rows,checks,actors=panel
    assert len(rows)==len(checks)==8
    by={r['arm']:check for r,check in zip(rows,checks)}
    assert by['ZG']['work']['reader_C_calls']==10 and by['ZG']['work']['reader_G_probabilities']==10
    for arm in ('ZSL0','ZSL1'):
        assert by[arm]['work']['reader_S_rows']==10 and by[arm]['work']['reader_C_calls']==5
        assert by[arm]['work']['hypothetical_S_rows']==5 and len(by[arm]['takeover_comparisons'])==5
        assert all(x['following_H4_own_counts']==[0]*4 for x in by[arm]['takeover_comparisons'])
    assert all(check['new_native_steps']==0 for check in checks)
    assert len(phases.prefix_identity(out,rows))==3
    for result in rows:
        assert all(x['longest_gap']==8 and x['leading_gap']==x['trailing_gap']==8 for x in result['metrics']['user_service'])


def test_reader_rejects_incomplete_or_corrupt_trace(panel):
    out,rows,checks,actors=panel;result=rows[0];raw=phases.load_raw(out,result)
    for key in ('user_service_mask','terminal_observation','initial_uav_sinr'):
        damaged=raw.copy();del damaged[key]
        with pytest.raises(AssertionError,match='schema'):read.check_episode(damaged,result,actors,horizon=8)
    damaged={k:v.copy() for k,v in raw.items()};damaged['observations'][1,-1,-1]=.9
    with pytest.raises(AssertionError,match='clocks'):read.check_episode(damaged,result,actors,horizon=8)
    damaged={k:v.copy() for k,v in raw.items()};damaged['probabilities'][0,0]=.01
    with pytest.raises(AssertionError,match='probabilities'):read.check_episode(damaged,result,actors,horizon=8)
    wrong=copy.deepcopy(result);wrong['raw']['sha256']='0'*64
    with pytest.raises(ValueError,match='bytes'):phases.load_raw(out,wrong)


def test_censored_zero_gaps_and_all50_users():
    mask=np.ones((8,50),dtype=bool);mask[:,0]=False;mask[:,1]=[False,False,True,False,True,True,False,False]
    service=metrics.user_service(mask);never=service['users'][0];mixed=service['users'][1]
    assert never['zero_runs']==[{'start':0,'stop':8,'length':8,'left_censored':True,'right_censored':True}]
    assert mixed['closed_internal_zero_lengths']==[1] and mixed['leading_gap']==mixed['trailing_gap']==2
    assert service['never_served_users']==1 and service['never_served_fraction']==.02
    assert mixed['zero_runs'][1]['left_censored']==mixed['zero_runs'][1]['right_censored']==False
    with pytest.raises(ValueError):metrics.user_service(mask[:,:49])


def test_all_levels_pairs_primary_and_interactions():
    rows=[{**spec,'metrics':{'J':float(c.ARMS.index(spec['arm']))+spec['tape']*.1},'episode_cpu_seconds':1.,'episode_wall_seconds':2.} for spec in c.episode_order('main')]
    result=metrics.comparisons(rows)
    assert len(result['levels'])==8 and len(result['all28_pairs'])==28 and len(result['primary'])==4 and len(result['interactions'])==2
    assert result['levels']['SL0']['J']['world_values']==[3.05]*32
    assert result['primary']['ZSL0-SL0']['J']['mean']==1.
    with pytest.raises(ValueError):metrics.comparisons(rows[:-1])


def test_source_identity_budget_and_real_entry_guard(tmp_path):
    root=Path(__file__).resolve().parents[5];sources=io.source_identity(root)
    assert all(sources[k]==v for k,v in c.SOURCE_SHA256.items())
    assert io.verify_calibration(root)==c.CALIBRATION
    tree=ast.parse(Path(run.__file__).read_text());calls=[x for x in ast.walk(tree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='require_admission']
    assert len(calls)==1 and isinstance(calls[0].args[0],ast.Name) and calls[0].args[0].id=='__file__'
    assert calls[0].keywords[0].value.value==c.DIRECTION
    budget=io.Budget({'schema':1,'prior_cpu_seconds':0.,'synthetic':dict.fromkeys(c.SYNTHETIC_LIMITS,0)})
    budget.check();assert budget.snapshot()['GPU_seconds']==0
    with pytest.raises(ValueError):io.Budget({'schema':1,'prior_cpu_seconds':3600,'synthetic':dict.fromkeys(c.SYNTHETIC_LIMITS,0)})
    with pytest.raises(ValueError):io.Budget({'schema':1,'prior_cpu_seconds':0,'synthetic':{**dict.fromkeys(c.SYNTHETIC_LIMITS,0),'original_C_calls':257}})
    path=tmp_path/'input.json';io.write_json(path,{'x':1});assert io.bound_json(path,io.hash_file(path))=={'x':1}
    with pytest.raises(ValueError):io.bound_json(path,'0'*64)
    args=run.parser().parse_args(['--mode','worker','--seed',str(c.MASTER),'--launch-sha','a'*40,'--out',str(tmp_path),'--actor-input','actors.json','--actor-input-sha256','b'*64,'--budget-ledger','budget.json','--budget-ledger-sha256','c'*64])
    assert args.out==tmp_path and args.worker_input is None


def test_nonempty_original_C_and_independent_source_agree():
    observation=row(1);observation[3:6]=(.02,-.01,.7)
    nav=kernels.initial_nav(observation);memo=kernels.MemoC();deployed=memo.query(observation,0,nav)
    reconstructed=read.source_c(kernels.original.LocalController(False),observation,0,nav)
    assert reconstructed['n_current']==1 and memo.counters['candidate_links']==108
    for key in ('scores','served','features','command','next_nav','fallback','action_index'):assert np.array_equal(deployed[key],reconstructed[key])


def test_worker_verifies_audit_before_fresh_main_environment(tmp_path,monkeypatch):
    from experiments.candidates.ucope.uav_motion_prefix_b01 import environment
    events=[]
    class Environment:
        def close(self):events.append('close')
    def factory(seed):events.append(('construct',seed));return Environment()
    def specs(phase):yield {'phase':phase,'arm':'C','world':1,'tape':-1,'sampling_root':None}
    def episode(env,spec,actors,out,counts,inflight):
        events.append(('collect',spec['phase']));counts.update(episodes=1,native_steps=256,native_step_calls=256,explicit_resets=1)
        return {**spec,'metrics':{},'raw':{},'episode_cpu_seconds':0.}
    def audit(*args,**kwargs):events.append(('read',kwargs['phase']));return {'status':'VERIFIED','results':[],'reader_cpu_seconds':0.}
    monkeypatch.setattr(environment,'make_real',factory);monkeypatch.setattr(c,'episode_order',specs)
    monkeypatch.setattr(collect,'episode',episode);monkeypatch.setattr(phases,'read_phase',audit)
    monkeypatch.setattr(phases,'work_table',lambda *args:{'phase':'audit'})
    monkeypatch.setattr(io,'verify_actors',lambda *args:events.append('verify_actors'))
    monkeypatch.setattr(run,'disk',lambda *args:[])
    io.write_json(tmp_path/'config.json',{})
    budget=io.Budget({'schema':1,'prior_cpu_seconds':0,'synthetic':dict.fromkeys(c.SYNTHETIC_LIMITS,0)})
    args=SimpleNamespace(actor_input_sha256='a'*64);summary={}
    run.worker(tmp_path,tmp_path,args,(),(),budget,{'source_sha256':{}},summary,{})
    assert events.index(('read','audit'))<events.index(('construct',c.WORLDS[0]))
    assert events.count(('read','audit'))==1 and events.count('close')==2
    assert summary['status']=='COMPLETE' and summary['audit_verified_before_main']
    assert (tmp_path/'audit_reading.json').exists()
    events.clear()
    def fail(*args,**kwargs):events.append(('read',kwargs['phase']));raise AssertionError('audit correctness failure')
    monkeypatch.setattr(phases,'read_phase',fail)
    with pytest.raises(AssertionError,match='audit correctness'):run.worker(tmp_path,tmp_path,args,(),(),budget,{'source_sha256':{}},{},{})
    assert ('construct',c.WORLDS[0]) not in events


def test_bound_audit_adoption_verifies_external_bytes_without_replay(tmp_path,monkeypatch):
    source={'source.py':'x'};actor_sha='a'*64;rows=[]
    for phase in ('audit','main'):
        spec={'phase':phase,'arm':'C','world':1,'tape':-1,'sampling_root':None}
        path=tmp_path/'raw'/phase/'C_1_t-1.npz';path.parent.mkdir(parents=True);path.write_bytes(b'FAKE-NATIVE-TRACE-NOT-LOADED')
        record=io.identity(path);record['path']=str(path.relative_to(tmp_path));rows.append({**spec,'raw':record})
    monkeypatch.setattr(c,'episode_order',lambda phase:iter([{k:r[k] for k in ('phase','arm','world','tape','sampling_root')} for r in rows if r['phase']==phase]))
    io.write_json(tmp_path/'config.json',{'mode':'worker','seed':c.MASTER,'launch_sha':'s','admission':{'sha':'s'},'source_sha256':source,'actor_input_sha256':actor_sha,'contract':c.contract()})
    io.write_json(tmp_path/'episodes.json',{'rows':rows})
    check_path=tmp_path/'audit_checks'/'C_1_t-1.json';check_path.parent.mkdir();payload={'raw':rows[0]['raw'],'work':{'reader_C_calls':1}}
    io.write_json(check_path,payload);check=io.identity(check_path);check['path']=str(check_path.relative_to(tmp_path))
    audit={'status':'VERIFIED','source_sha256':source,'actor_input_sha256':actor_sha,'new_native_steps':0,'all_raw_verified':True,'complete_native_and_source_reconstruction':True,
           'results':[{'raw':rows[0]['raw'],'work':payload['work'],'checks':check}]}
    io.write_json(tmp_path/'audit_reading.json',audit)
    io.write_json(tmp_path/'summary.json',{'status':'COMPLETE','mode':'worker','seed':c.MASTER,'launch_sha':'s','episodes':io.identity(tmp_path/'episodes.json'),'audit_reading':io.identity(tmp_path/'audit_reading.json')})
    locator=tmp_path/'locator.json';io.write_json(locator,{'schema':1,'root':str(tmp_path),'config_sha256':io.hash_file(tmp_path/'config.json'),'summary_sha256':io.hash_file(tmp_path/'summary.json')})
    def forbidden(*args,**kwargs):raise AssertionError('audit must not replay')
    monkeypatch.setattr(read,'check_episode',forbidden)
    bound=phases.bound_worker(locator,io.hash_file(locator),source,actor_sha)
    assert bound[0]==tmp_path and bound[-1]==audit
    check_path.write_text('{}')
    with pytest.raises(ValueError,match='audit check bytes'):phases.bound_worker(locator,io.hash_file(locator),source,actor_sha)


def test_bounded_check_function_without_checkpoint_load():
    from experiments.candidates.uav_decision_generalization.b02_feedback_cooperation import checks
    budget=io.Budget({'schema':1,'prior_cpu_seconds':0,'synthetic':dict.fromkeys(c.SYNTHETIC_LIMITS,0)})
    result=checks.bounded(budget)
    assert result['actual_usage']==budget.synthetic=={'original_C_calls':4,'frozen_actor_rows':0,'count_decodes':7}
    assert result['new_native_steps']==0 and result['status']=='VERIFIED'
    budget.synthetic['original_C_calls']=256
    with pytest.raises(RuntimeError,match='before call'):budget.pay('original_C_calls')


def test_exact_phase_and_combined_cost_tables_are_derived():
    tables=[]
    for phase in ('audit','main'):
        rows=[];results=[]
        for spec in c.episode_order(phase):
            arm=spec['arm'];parent=c.PARENTS.get(arm,arm);z=arm in c.PARENTS
            per_agent={source:read.empty_counters(source) for source in (('C',parent) if z else (parent,))}
            for source,counts in per_agent.items():
                requests=(63 if source=='C' else 1) if z else 64
                counts.update(requests=requests,hits=requests,sampled_draws=requests if source!='C' else 0,score_tail_evaluations=requests if source=='G' else 0)
            C_calls=320 if parent in ('C','G') else 315 if z else 0
            S_rows=320 if parent not in ('C','G') else 0
            work={'reader_C_calls':C_calls,'reader_S_rows':S_rows,'reader_draws':0 if arm=='C' else 320,
                  'reader_G_probabilities':320 if parent=='G' else 0,'reader_count_decodes':1285,
                  'C_model_ticks':C_calls*108,'C_candidate_links':0,'C_setup_links':0,'helper_setup_links':0,'helper_extreme_links':0,
                  'geometric_comparison_steps':1260 if z else 0}
            rows.append({**spec,'metrics':{'takeovers':315 if z else 0,'queries':320},'policy_counts':[copy.deepcopy(per_agent) for _ in range(5)],
                         'online_count_decodes':1280 if z else 0,'online_gate_checks':315 if z else 0})
            results.append({'work':work})
        n=len(rows);counts={'episodes':n,'native_steps':n*256,'constructor_resets':1,'explicit_resets':n,'native_step_calls':n*256}
        tables.append(phases.work_table(rows,results,phase,counts))
    cost=phases.combined_cost(tables,dict.fromkeys(c.SYNTHETIC_LIMITS,0))
    assert cost['totals']['native_steps']==126976 and cost['native_dense_power_slots']==35055350
    assert cost['slot_presence_tests']==17816000 and cost['geometric_comparison_steps']==249480
    assert cost['connection_entries_read']==31744000 and cost['totals']['reader_S_rows']==105600
    assert cost['actual_full_C_calculations']==94700
    wrong=copy.deepcopy(tables);wrong[0]['exact']['native_steps']-=1
    with pytest.raises(AssertionError,match='native bound'):phases.combined_cost(wrong,dict.fromkeys(c.SYNTHETIC_LIMITS,0))


@pytest.mark.parametrize('corrupt', [('SL1','ZSL1'),('C',)])
def test_initial_world_identity_rejects_joint_pair_or_baseline_corruption(tmp_path,corrupt):
    """Handcrafted hash/prefix evidence only; no controller, actor or environment."""
    rows=[];arrays={}
    for arm in c.ARMS:
        for tape in ((-1,) if arm=='C' else (0,1)):
            source=c.PARENTS.get(arm,arm)
            raw={key:np.zeros(shape,dtype=np.float64) for key,shape in {
                'positions':(5,5,3),'initial_users':(50,2),'initial_sinr':(5,50),'initial_uav_sinr':(5,5),
                'observations':(4,5,104),'commands':(4,5,3),'reward':(4,),'served':(4,),'sinr_quality':(4,),
                'sinr':(4,5,50),'uav_sinr':(4,5,5),'features':(5,114),'probabilities':(5,27),
                'innovation':(5,),'entropy':(5,),'policy_scores':(5,27),'policy_served':(5,27),'logits':(5,27)}.items()}
            for key,shape in {'initial_connections':(5,50),'connections':(4,5,50),'user_service_mask':(4,50),
                              'transmitter_mask':(4,5),'terminated':(4,),'truncated':(4,),'takeover':(5,),'fallback':(5,)}.items():raw[key]=np.zeros(shape,dtype=bool)
            for key in ('nav_pre','nav_next','action_index','c_index'):raw[key]=np.zeros(5,dtype=np.int64)
            raw['source']=np.full(5,source)
            spec={'phase':'main','world':108310000,'arm':arm,'tape':tape,'sampling_root':None if arm=='C' else c.SAMPLING_ROOTS[tape]}
            path=tmp_path/'raw'/'main'/f'{arm}_{spec["world"]}_t{tape}.npz';path.parent.mkdir(parents=True,exist_ok=True)
            np.savez_compressed(path,**raw)
            file=io.identity(path);file['path']=str(path.relative_to(tmp_path))
            rows.append({**spec,'raw':file,'initial_state_sha256':c.initial_state_digest(raw['positions'][0],raw['initial_users'],raw['initial_sinr'],raw['initial_uav_sinr'],raw['initial_connections'])})
            arrays[arm,tape]=raw
    assert len(phases.prefix_identity(tmp_path,rows))==6
    for item in rows:
        if item['arm'] not in corrupt:continue
        raw=arrays[item['arm'],item['tape']];raw['initial_uav_sinr'][0,1]=4.
        path=tmp_path/item['raw']['path'];np.savez_compressed(path,**raw)
        item['raw']={**io.identity(path),'path':item['raw']['path']}
        item['initial_state_sha256']=c.initial_state_digest(raw['positions'][0],raw['initial_users'],raw['initial_sinr'],raw['initial_uav_sinr'],raw['initial_connections'])
    if 'SL1' in corrupt:
        for tape in (0,1):
            pair=[r for r in rows if r['arm'] in corrupt and r['tape']==tape]
            assert pair[0]['initial_state_sha256']==pair[1]['initial_state_sha256']
    with pytest.raises(AssertionError,match='all arms/tapes initial world'):phases.prefix_identity(tmp_path,rows)
    # A radio-field mutation with a stale advertised reset digest is rejected too.
    item=rows[0];raw=arrays[item['arm'],item['tape']];raw['initial_uav_sinr'][1,0]+=1.
    path=tmp_path/item['raw']['path'];np.savez_compressed(path,**raw)
    item['raw']={**io.identity(path),'path':item['raw']['path']}
    with pytest.raises(AssertionError,match='initial state binding'):phases.prefix_identity(tmp_path,rows)
