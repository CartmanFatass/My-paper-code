"""Pure bounded engineering fixtures: zero environment/RF/model/optimizer effects."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from experiments.candidates.uav_decision_generalization.b03_joint_window import contract as c,task,ordinary,metrics,run

ROOT=Path(__file__).resolve().parents[5]
PACKAGE=ROOT/'experiments/candidates/uav_decision_generalization/b03_joint_window'


def test_registry_packet_and_rng_are_addressed_without_parent_draws():
    np.random.seed(123);before=np.random.get_state()
    users,schedule,packet=task.world_registry(c.WORLDS[0])
    after=np.random.get_state()
    assert all(np.array_equal(a,b) for a,b in zip(before,after))
    assert users.dtype==np.dtype('<i4') and users.shape==(50,2) and packet.nbytes==404
    decoded=task.decode_packet(packet)
    assert np.array_equal(decoded[0],users) and np.array_equal(decoded[1],schedule)
    assert all(np.array_equal(a,b) for a,b in zip(task.world_registry(c.WORLDS[0]),(users,schedule,packet)))
    assert not np.array_equal(users,task.world_registry(c.WORLDS[1])[0])
    assert np.array_equal(packet[:400],np.frombuffer(users.tobytes(),dtype=np.uint8))
    with pytest.raises(ValueError):task.decode_packet(packet[:-1])


def test_features_off_grid_full_clock_and_terminal():
    order=np.array([3,0,2,1],dtype=np.uint8)
    assert task.augmented_observations(np.zeros((6,90)),np.zeros((50,2)),order,125).shape==(6,211)
    assert task.augmented_state(np.zeros(133),order,125).shape==(154,)
    for tick,cluster in ((0,3),(124,3),(125,0),(249,0),(250,2),(375,1)):
        value=task.task_features(order,tick)
        assert value.shape==(21,) and value.dtype==np.float32 and value[16+cluster]==1
        assert value[-1]==np.float32((125-tick%125)/125)
    assert np.count_nonzero(task.task_features(order,500)[16:])==0


def test_private_ledger_uses_post_routing_once_and_resets_at_window():
    ledger=task.WindowLedger(np.arange(4,dtype=np.uint8));conn=np.zeros((6,50),dtype=bool);conn[0,10:18]=True
    for _ in range(19):assert ledger.advance(conn,np.array([1,0,0,0,0,0]))['payment']==0
    assert ledger.advance(conn,np.zeros(6,dtype=bool))['run_length']==0
    payments=[]
    for _ in range(105):payments.append(ledger.advance(conn,np.array([1,0,0,0,0,0]))['payment'])
    assert sum(payments)==1 and ledger.tick==125 and ledger.paid.tolist()==[True,False,False,False]
    conn[:]=False;conn[0,20:28]=True
    facts=ledger.advance(conn,np.array([1,0,0,0,0,0]))
    assert facts['run_length']==1 and facts['window']==1 and facts['active_count']==8
    assert not facts['routed_user_mask'][:20].any()


def test_adapter_advances_only_after_complete_parent_step():
    from experiments.candidates.uav_decision_generalization.b03_joint_window.adapter import WindowAdapter
    host=SimpleNamespace(current_step=0,connections=np.zeros((6,50),dtype=bool),routing_paths={0:[('uav',0),('ground_bs',0)]})
    ledger=task.WindowLedger(np.arange(4,dtype=np.uint8));host.connections[0,10:18]=True
    def step(actions):
        # Two original diagnostic entries cannot touch a private ledger.
        for _ in range(2):assert ledger.tick==0
        host.current_step=1
        return np.zeros((6,90),dtype=np.float32),999,False,False,{'next_state':np.zeros(133,dtype=np.float32),'contract':{'contract_reward':.8,'coverage_backhauled':.16,'throughput_term':1.44,'frontend_capacity_with_path_mbps':5,'action_clip_events':0}}
    base=SimpleNamespace(host=host,action_space=None,step=step)
    env=WindowAdapter(base);env.ledger=ledger;env.schedule=np.arange(4,dtype=np.uint8);env.users=np.zeros((50,2),dtype='<i4')
    action=np.zeros((6,3),dtype=np.float32)
    obs,reward,_,_,info=env.step(action)
    assert ledger.tick==1 and reward==0 and info['window']['active_count']==8 and obs.shape==(6,211)
    assert info['window']['dense_reward']==.8


def test_ordinary_legal_decode_ties_clock_and_dtype():
    from experiments.candidates.uav_decision_generalization.b03_joint_window.trace import own_positions,held_positions
    users,schedule,_=task.world_registry(c.WORLDS[0]);rows=np.zeros((6,211),dtype=np.float32);rows[:,0]=np.float32(.12345678);rows[:,2]=np.float32(.8)
    decoded=own_positions(rows)
    assert np.array_equal(decoded[:,0],rows[:,0].astype(np.float64)*5000)
    state=np.zeros(154,dtype=np.float32);state[:18]=rows[:,:3].ravel()
    assert np.array_equal(decoded,held_positions(state))
    controller=ordinary.RayChain(decoded,users,schedule)
    assert sorted(controller.assignment)==list(range(6)) and controller.assignment_comparisons==720
    old=controller.targets.copy();controller.actions(125,decoded,decoded)
    assert np.array_equal(old,controller.targets)
    action=controller.actions(130,decoded,decoded)
    assert controller.assignment_comparisons==722 and controller.slot_distances==40 and action.dtype==np.float64
    assert np.all(np.linalg.norm(action,axis=1)<=1+1e-15)
    unaffected=set(range(6))-set(controller.assignment[:2])
    assert all(np.array_equal(old[u],controller.targets[u]) for u in unaffected)
    a,b=ordinary.Sticky(c.WORLDS[0]),ordinary.Sticky(c.WORLDS[0])
    for tick in range(21):assert np.array_equal(a.actions(tick,decoded,decoded),b.actions(tick,decoded,decoded))
    assert a.draws==18+12+3*a.replacements


def test_complete_all_user_censored_gaps():
    mask=np.zeros((500,50),dtype=bool);mask[2:497,0]=True;mask[[5,10],1]=True
    value=metrics.all_user_service(mask)
    assert value['never_served_users']==48 and len(value['users'])==50
    assert value['users'][0]['leading_gap']==2 and value['users'][0]['trailing_gap']==3
    assert value['users'][0]['closed_internal_zero_lengths']==[]
    gaps=value['users'][1]['zero_runs'];assert gaps[0]['left_censored'] and gaps[-1]['right_censored'] and gaps[1]['length']==4
    assert value['users'][2]['zero_runs']==[{'start':0,'stop':500,'length':500,'left_censored':True,'right_censored':True}]


def test_exact_exposure_and_source_guard():
    from scripts.hmasd_launch import _validate_guard_contract
    _validate_guard_contract(PACKAGE/'run.py',c.DIRECTION)
    assert 3*16*500*45+7*32*500+8*500==1196000
    assert sum(sum(v.values()) for v in c.OPTIMIZER_TOTALS.values())==615600
    tree=ast.parse((PACKAGE/'run.py').read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    admission=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='require_admission')
    effects=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='accepted_output')
    assert admission<effects
    assert 'run_fit(' not in (PACKAGE/'worker.py').read_text() and 'build_matching_table(' not in (PACKAGE/'worker.py').read_text()
    assert run.parser().parse_args(['--mode','worker','--seed',str(c.MASTER),'--launch-sha','sha','--out','out','--study-input','study','--study-input-sha256','x','--budget-ledger','budget','--budget-ledger-sha256','y']).mode=='worker'


def test_configuration_without_constructing_a_model():
    from experiments.candidates.uav_decision_generalization.b03_joint_window.configuration import make_config,initial_alias_configs
    H,N,S=(make_config(a,16) for a in c.ARMS)
    assert initial_alias_configs(H,N)['only_difference']=='disable_discriminator_rewards'
    for cfg in (H,N,S):
        assert (cfg.gamma,cfg.gae_lambda,cfg.ppo_epochs,cfg.sequence_batch_size)==(.99,.95,15,32)
        assert (cfg.obs_dim,cfg.state_dim,cfg.hidden_size,cfg.gru_hidden_size)==(211,154,256,256)
        assert cfg.continuous_action_distribution=='gaussian' and cfg.continuous_logstd_init==0
        assert cfg.discriminator_batch_size==12000 and cfg.use_valuenorm and not cfg.use_obsnorm and not cfg.use_statenorm
        assert (cfg.lambda_e,cfg.lambda_l)==(1,.05) and cfg.weight_decay==0
        assert all(getattr(cfg,k)==1e-4 for k in ('lr_coordinator','lr_discoverer_actor','lr_discoverer_critic','lr_discriminator'))
    assert (H.lambda_h,S.lambda_h)==(.07,0)
    assert not N.disable_discriminator_training and N.disable_discriminator_rewards
    assert S.n_Z==S.n_z==1 and S.k==10 and S.use_central_snapshot_in_flat_actor


def test_bound_canonical_locator_and_source_manifest(tmp_path):
    from experiments.candidates.uav_decision_generalization.b03_joint_window import evidence as e
    worker=tmp_path/'canonical';worker.mkdir()
    values={'config':{'mode':'worker','contract':e.jsonable(c.frozen_contract())},'summary':{'status':'COMPLETE'},'manifest':{'schema':1}}
    for key,value in values.items():e.write_json(worker/(key+'.json'),value)
    locator={'schema':1,'root':str(worker),**{k+'_sha256':e.hash_file(worker/(k+'.json')) for k in values}}
    context=run.worker_context(locator)
    assert context['worker_root']==worker and context['manifest']=={'schema':1}
    e.write_json(worker/'manifest.json',{'schema':2})
    with pytest.raises(ValueError):run.worker_context(locator)
    manifest=e.source_manifest(ROOT)
    assert 'hmasd/agent.py' in manifest and 'envs/pettingzoo/scenario2.py' in manifest
    assert all(e.hash_file(ROOT/path)==sha for path,sha in manifest.items())
    assert e.Meter({'schema':1,'prior_cpu_seconds':0,'prior_counts':{}}).resources()['GPU_seconds']==0


def test_saved_raw_dtype_and_complete_evidence(tmp_path):
    from experiments.candidates.uav_decision_generalization.b03_joint_window import evidence as e,worker
    raw={k:np.zeros((500,)+shape,dtype=dtype) for k,(shape,dtype) in c.LEDGER_FIELDS.items()}
    raw.update({k:np.zeros((501,)+c.STATE_FIELDS[k][0],dtype=c.STATE_FIELDS[k][1]) for k in ('positions','connections','routes','route_lengths','transmitter_mask')})
    raw.update(raw_actions=np.zeros((500,6,3),dtype=np.float32),executed_actions=np.zeros((500,6,3),dtype=np.float32));raw['terminated'][-1]=True
    worker.validate_prefix(raw,True);e.write_npz(tmp_path/'raw.npz',raw)
    with np.load(tmp_path/'raw.npz',allow_pickle=False) as saved:assert saved['raw_actions'].dtype==np.float32
    raw['positions']=raw['positions'][:-1]
    with pytest.raises(AssertionError):worker.validate_prefix(raw,True)


def test_provisional_resource_request_without_resource_probe(monkeypatch,tmp_path):
    from scripts import hmasd_resource_preflight as preflight
    gib=1024**3
    monkeypatch.setattr(preflight,'capture_snapshot',lambda:{'mock':'no actual host/resource query'})
    monkeypatch.setattr(preflight,'assess_memory_floor',lambda value:{'available_physical_bytes':9*gib,'effective_available_bytes':8*gib})
    monkeypatch.setattr(run.shutil,'disk_usage',lambda path:SimpleNamespace(free=8*gib))
    assert run.resource_request(tmp_path)['requested_memory_bytes']==8*gib
    monkeypatch.setattr(run.shutil,'disk_usage',lambda path:SimpleNamespace(free=8*gib-1))
    with pytest.raises(RuntimeError):run.resource_request(tmp_path)
    source=(PACKAGE/'run.py').read_text()
    main=source[source.index('def main'):]
    assert main.index("os.environ[key]='1'")<main.index('import evidence as e')
    assert c.MASTER==109230101


def test_checkpoint_configuration_binding_without_model_load_or_forward(monkeypatch,tmp_path):
    import torch
    from experiments.candidates.uav_decision_generalization.b03_joint_window import evidence as e
    from experiments.candidates.uav_decision_generalization.b03_joint_window.configuration import make_config,config_dict
    cfg=make_config('H',16)
    payload={'schema':1,'object':c.OBJECT,'arm':'H','endpoint':'initial','config':config_dict(cfg),'modules':{},'normalizers':{name:None for name in e.NORMALIZERS}}
    agent=SimpleNamespace(**{name:None for name in (*e.MODULES,*e.NORMALIZERS)},train=lambda value:None)
    payload['state_digest']=e.digest_agent(agent)
    calls=[]
    monkeypatch.setattr(torch,'load',lambda *a,**k:payload)
    monkeypatch.setattr(e,'build_agent',lambda *a,**k:(calls.append('mock factory') or agent,cfg))
    e.load_agent(tmp_path/'not-read.pt','H-noD',1,tmp_path,e.Meter({'schema':1,'prior_cpu_seconds':0,'prior_counts':{}}))
    assert calls==['mock factory']
    payload['config']=dict(payload['config'],continuous_action_distribution='tanh')
    with pytest.raises(ValueError):e.load_agent(tmp_path/'not-read.pt','H',1,tmp_path,None)
    assert calls==['mock factory']


def test_failed_primitive_counts_actual_paid_effect_without_retry():
    from experiments.candidates.uav_decision_generalization.b03_joint_window import worker,evidence as e
    host=SimpleNamespace(event_counts={'native_steps':0});calls=[]
    def step(action):
        calls.append('mock primitive');host.event_counts['native_steps']+=1;raise ValueError('mock failure after primitive')
    env=SimpleNamespace(host=host,step=step);meter=e.Meter({'schema':1,'prior_cpu_seconds':0,'prior_counts':{}})
    with pytest.raises(ValueError):worker.native_transition(env,None,meter,'training_native_steps')
    assert calls==['mock primitive'] and meter.counts=={'native_step_attempts':1,'native_steps':1,'training_native_steps':1}


def test_intrinsic_context_accounting_from_mock_forward_hook_only():
    from experiments.candidates.uav_decision_generalization.b03_joint_window.evidence import Meter
    meter=Meter({'schema':1,'prior_cpu_seconds':0,'prior_counts':{}});meter.phase='intrinsic/H'
    meter.observe_forward('team_discriminator',(np.zeros((16,154),dtype=np.float32),))
    meter.observe_forward('individual_discriminator',(np.zeros((96,211),dtype=np.float32),))
    meter.phase='update/H';meter.observe_forward('team_discriminator',(np.zeros((12000,154),dtype=np.float32),))
    assert meter.counts=={'intrinsic_reward_team_discriminator_forward_calls':1,'intrinsic_reward_team_discriminator_forward_contexts':16,'intrinsic_reward_individual_discriminator_forward_calls':1,'intrinsic_reward_individual_discriminator_forward_contexts':96}


def test_direct_ppo_method_counts_sequence_contexts_once_and_restores():
    from experiments.candidates.uav_decision_generalization.b03_joint_window import evidence as e
    calls=[];answer=object()
    class FakeModule:
        def named_modules(self):return iter(())
    class FakeActor(FakeModule):
        def evaluate_actions(self,*args,**kwargs):calls.append((args,kwargs));return answer
    actor=FakeActor();original=actor.evaluate_actions
    discoverer=FakeModule();discoverer.actor=actor;discoverer.critic=FakeModule()
    agent=SimpleNamespace(skill_coordinator=FakeModule(),skill_discoverer=discoverer)
    meter=e.Meter({'schema':1,'prior_cpu_seconds':0,'prior_counts':{}});meter.phase='update/H'
    observations=np.zeros((10,32,211),dtype=np.float32)
    with pytest.raises(RuntimeError,match='mock interruption'):
        with e.instrument_agent(agent,meter):
            assert actor.evaluate_actions(observations,flag=True) is answer
            assert len(calls)==1 and calls[0][0][0] is observations and calls[0][1]=={'flag':True}
            raise RuntimeError('mock interruption')
    assert actor.evaluate_actions==original and len(calls)==1
    item=meter.calls['update/H|discoverer_actor.evaluate_actions']
    assert item['calls']==1 and item['leading_rows']==10 and item['agent_tick_contexts']==320
    assert meter.counts=={'direct_actor_evaluate_calls':1,'direct_actor_evaluate_agent_tick_contexts':320}
