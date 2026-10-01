"""Synthetic H8 caches only: no native environment, backbone or asset queries."""
from copy import deepcopy
import json
import random

import numpy as np
import pytest
import torch
from torch import nn

from experiments.candidates.uav_parent_adaptation.b09_managed_development import learning as new
from experiments.candidates.uav_fleet_adaptation.b04_native_development import learning as frozen
from experiments.candidates.uav_fleet_adaptation.b05_native_consequence.learning import Head
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import critic_features as old_features


@pytest.fixture(autouse=True)
def one_thread():
    previous=torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(previous)


def prequery(tick=0,horizon=8):
    state=np.concatenate((np.tile([500.,250.,100.],5),np.arange(100)*7.,[tick/horizon])).astype(np.float32)
    actual=np.linspace(-1,1,15,dtype=np.float32).reshape(5,3)
    mask=np.array([True,False,True,False,True],dtype=bool)
    nav=np.array([0,2,4,6,9],dtype=np.int64)
    return state,actual,mask,nav


def group(head,critic,*,readonly=True):
    rng=np.random.default_rng(91)
    episodes=[]
    for episode in range(2):
        hidden=(rng.normal(size=(2,5,128))*5).astype(np.float32)
        base=(rng.normal(size=(2,5,27))*2).astype(np.float32)
        cx=np.stack([new.critic_features(*prequery(t),tick=t,horizon=8) for t in (0,4)])
        cx[:,0]+=(episode+1)*.01
        with torch.inference_mode():
            logits=np.stack([head(torch.from_numpy(h),torch.from_numpy(z)).numpy().copy()
                for h,z in zip(hidden.reshape(-1,128),base.reshape(-1,27))]).reshape(2,5,27)
            values=critic(torch.from_numpy(cx)).numpy().copy()
        z=logits.astype(np.float64)
        p=np.exp(z-z.max(-1,keepdims=True)); p/=p.sum(-1,keepdims=True)
        actions=(np.arange(10).reshape(2,5)+episode*10).astype(np.int64)
        chosen=np.take_along_axis(p,actions[...,None],axis=-1)[...,0]
        data=dict(hidden=hidden,base_logits=base,logits=logits,probabilities=p,
            action_index=actions,logp=np.log(chosen),critic_features=cx,values=values,
            macro_rewards=np.array([1.+episode*10,2.+episode*10],np.float64))
        if readonly:
            for array in data.values():
                array.setflags(write=False)
        episodes.append(data)
    return episodes


def snapshot_rng():
    return torch.get_rng_state().clone(),deepcopy(np.random.get_state()),random.getstate()


def assert_rng(before):
    assert torch.equal(before[0],torch.get_rng_state())
    after=np.random.get_state()
    assert before[1][0]==after[0] and np.array_equal(before[1][1],after[1]) and before[1][2:]==after[2:]
    assert before[2]==random.getstate()


def test_native186_scaling_prequery_copy_and_clock_bits():
    values=prequery(4)
    before=deepcopy(values)
    features=new.critic_features(*values,tick=4,horizon=8)
    assert features.dtype==np.float32 and features.shape==(186,)
    expected=old_features(values[0],np.zeros((5,3),np.float32),np.zeros(5,np.int64))[:116]
    assert features[:116].tobytes()==expected.tobytes()
    assert features[116:131].tobytes()==values[1].reshape(-1).tobytes()
    assert features[131:136].tolist()==[1.,0.,1.,0.,1.]
    assert np.array_equal(features[136:].reshape(5,10),np.eye(10,dtype=np.float32)[values[3]])
    assert features[2]==.5 and features[-1]==1 and features[115]==.5
    for old,current in zip(before,values):
        assert old.tobytes()==current.tobytes()
    # The retained baseline precedes startup replacement/nav advancement.
    values[1][:]=0; values[2][:]=False; values[3][:]=1; values[0][:]=999
    assert features[116:131].tobytes()==before[1].reshape(-1).tobytes()
    assert features[131:136].tolist()==[1.,0.,1.,0.,1.]
    features[:]=0
    assert np.all(values[0]==999)


@pytest.mark.parametrize('corruption',['clock','negative_zero','state_dtype','state_shape','state_nan',
    'command_dtype','command_range','command_nan','mask_dtype','nav_dtype','nav_range','tick','horizon'])
def test_feature_input_rights_fail_closed(corruption):
    args=list(prequery())
    tick,horizon=0,8
    if corruption=='clock': args[0][-1]=np.float32(.5)
    elif corruption=='negative_zero': args[0][-1]=np.float32(-0.)
    elif corruption=='state_dtype': args[0]=args[0].astype(np.float64)
    elif corruption=='state_shape': args[0]=args[0][:-1]
    elif corruption=='state_nan': args[0][0]=np.nan
    elif corruption=='command_dtype': args[1]=args[1].astype(np.float64)
    elif corruption=='command_range': args[1][0,0]=1.01
    elif corruption=='command_nan': args[1][0,0]=np.nan
    elif corruption=='mask_dtype': args[2]=args[2].astype(np.float32)
    elif corruption=='nav_dtype': args[3]=args[3].astype(np.int32)
    elif corruption=='nav_range': args[3][0]=10
    elif corruption=='tick': tick=True
    else: horizon=0
    with pytest.raises((ValueError,FloatingPointError)):
        new.critic_features(*args,tick=tick,horizon=horizon)


def test_fresh_matching_critic_rng_architecture_and_adams():
    before=snapshot_rng()
    critic=new.fresh_critic(81)
    other=new.fresh_critic(81)
    assert_rng(before)
    assert sum(p.numel() for p in critic.parameters())==40577
    assert [type(layer).__name__ for layer in critic.network]==['Linear','Tanh','Linear','Tanh','Linear']
    assert critic.network[0].in_features==186
    assert all(torch.equal(p,q) for p,q in zip(critic.parameters(),other.parameters()))
    for kind,size in [('CAL',28),('CONT',3483)]:
        head=new.Head(kind)
        assert isinstance(head,Head) and sum(p.numel() for p in head.parameters())==size
        optimizers=new.make_optimizers(head,critic)
        assert_rng(before)
        for opt,model in zip(optimizers,(head,critic)):
            assert not opt.state
            assert set(p for g in opt.param_groups for p in g['params'])==set(model.parameters())
            for key,value in dict(lr=3e-4,betas=(.9,.999),eps=1e-8,weight_decay=0,
                    amsgrad=False,foreach=False,fused=False).items():
                assert opt.defaults[key]==value


@pytest.mark.parametrize('kind',['CAL','CONT'])
def test_four_epochs_targets_losses_counts_movement_inputs_and_rng(kind):
    head,critic=Head(kind),new.fresh_critic(81)
    before=snapshot_rng()
    opts=new.make_optimizers(head,critic)
    episodes=group(head,critic)
    original=deepcopy(episodes)
    forwards,critic_values,step_order=[],[],[]
    hook=head.register_forward_hook(lambda model,args,out:forwards.append((tuple(args[0].shape),tuple(args[1].shape),out.detach().numpy().copy())))
    chook=critic.register_forward_hook(lambda model,args,out:critic_values.append(out.detach().numpy().copy()))
    for name,opt in zip(('actor','critic'),opts):
        actual=opt.step
        def step(name=name,actual=actual):
            step_order.append(name)
            return actual()
        opt.step=step
    counts={key:3 for key in new.COUNT_KEYS}; counts['unrelated']=101
    record={'group':0}
    result=new.update_group(head,critic,*opts,episodes,counts,horizon=8,live_record=record)
    hook.remove(); chook.remove()
    assert result is record and result['status']=='COMPLETE'
    assert_rng(before)
    assert result['counts_delta']==dict(actor_optimizer_steps=4,actor_replay_rows=80,
        critic_optimizer_steps=4,critic_replay_rows=16,density_identity_rows=20,target_rows=4,
        actor_optimizer_attempts=4,critic_optimizer_attempts=4)
    assert counts['unrelated']==101
    assert len(forwards)==80 and all(h==(128,) and z==(27,) for h,z,_ in forwards)
    assert len(critic_values)==4 and step_order==['actor','critic']*4
    targets=np.array([[3/8,2/8],[23/8,12/8]],np.float32)
    assert np.array_equal(np.asarray(result['targets'],np.float32),targets)
    raw=targets-np.stack([ep['values'] for ep in episodes])
    advantages=(raw-raw.mean())/(raw.std(ddof=0)+np.float32(1e-8))
    np.testing.assert_allclose(result['advantages'],advantages,rtol=1e-6,atol=1e-7)
    oldp=np.stack([ep['probabilities'] for ep in episodes])
    actions=np.stack([ep['action_index'] for ep in episodes])
    oldchosen=np.take_along_axis(oldp,actions[...,None],axis=-1)[...,0]
    for epoch,r in enumerate(result['epochs']):
        z=np.stack([item[2] for item in forwards[epoch*20:(epoch+1)*20]]).reshape(2,2,5,27).astype(np.float64)
        p=np.exp(z-z.max(-1,keepdims=True));p/=p.sum(-1,keepdims=True)
        ratio=np.take_along_axis(p,actions[...,None],axis=-1)[...,0]/oldchosen
        loss=-np.minimum(ratio*advantages[...,None],np.clip(ratio,.8,1.2)*advantages[...,None]).sum(-1).mean()
        assert r['actor_loss']==pytest.approx(loss,abs=2e-6)
        assert r['critic_loss']==pytest.approx(.5*np.square(critic_values[epoch]-targets).mean(),abs=1e-7)
        assert r['actor_clipped_grad_norm']<=.500001 and r['critic_clipped_grad_norm']<=.500001
        assert r['actor_step_completed'] and r['critic_step_completed']
        assert r['actor_optimizer_step_values']==[epoch+1]*len(list(head.parameters()))
    assert result['initial_identity']['logits_exact']
    assert result['initial_identity']['max_probability_abs']<=5e-14
    assert result['initial_identity']['max_chosen_logp_abs']<=1e-10
    assert result['initial_identity']['max_ratio_from_one']<=1e-10
    assert result['actor_movement_l2']>0 and result['critic_movement_l2']>0
    assert result['initial_actor_sha256']!=result['final_actor_sha256']
    assert result['initial_critic_sha256']!=result['final_critic_sha256']
    for ep,old in zip(episodes,original):
        for key in ep:
            assert ep[key].tobytes()==old[key].tobytes() and not ep[key].flags.writeable
    json.dumps(result,allow_nan=False)
    # A second group uses the continuing moments, but freshly collected density.
    later=new.update_group(head,critic,*opts,group(head,critic),counts,horizon=8)
    assert later['actor_optimizer_step_values']==[8]*len(list(head.parameters()))
    assert later['critic_optimizer_step_values']==[8]*len(list(critic.parameters()))


@pytest.mark.parametrize('kind',['CAL','CONT'])
def test_bit_exact_optimizer_math_against_frozen_updater_with_cached_wrappers(kind):
    head,critic=Head(kind),new.fresh_critic(81)
    episodes=group(head,critic)
    rh,rc=deepcopy(head),deepcopy(critic)
    # These adapters present the old updater's API while retaining the SAME
    # one-row Head and 186-input critic operations. No backbone replay occurs.
    hidden=torch.tensor(np.stack([ep['hidden'] for ep in episodes])).reshape(-1,128)
    base=torch.tensor(np.stack([ep['base_logits'] for ep in episodes])).reshape(-1,27)
    extra=torch.tensor(np.stack([ep['critic_features'][...,136:] for ep in episodes]))
    class CachedActor(nn.Module):
        def __init__(self):
            super().__init__();self.head=rh;self.index=0
        def forward(self,feature):
            index=self.index%20;self.index+=1
            return self.head(hidden[index],base[index])[None]
    class PaddedCritic(nn.Module):
        def __init__(self):
            super().__init__();self.critic=rc
        def forward(self,features):
            return self.critic(torch.cat((features,extra),dim=-1))
    reference=[]
    for ep in episodes:
        data={key:ep[key].copy() for key in ('logits','probabilities','action_index','logp','values','macro_rewards')}
        data['features']=np.zeros((2,5,114),np.float32)
        data['critic_features']=ep['critic_features'][...,:136].copy()
        reference.append(data)
    ra,rv=CachedActor(),PaddedCritic()
    result=frozen.update_group(ra,rv,*frozen.make_optimizers(ra,rv),reference,{},horizon=8)
    actual=new.update_group(head,critic,*new.make_optimizers(head,critic),episodes,{},horizon=8)
    assert all(torch.equal(p,q) for p,q in zip(head.parameters(),rh.parameters()))
    assert all(torch.equal(p,q) for p,q in zip(critic.parameters(),rc.parameters()))
    for observed,expected in zip(actual['epochs'],result['epochs']):
        for key in ('actor_loss','critic_loss','ratio_min','ratio_max','actor_grad_norm','critic_grad_norm',
                    'actor_clipped_grad_norm','critic_clipped_grad_norm'):
            assert observed[key]==expected[key]
    assert actual['target_summary']==result['target_summary']
    assert actual['advantage_summary']==result['advantage_summary']


def test_fp32_reward_cast_precedes_reverse_suffix_sum():
    head,critic=Head('CAL'),new.fresh_critic(81)
    episodes=group(head,critic,readonly=False)
    episodes[0]['macro_rewards'][:]=[1+2**-24,2**-24]
    episodes[1]['macro_rewards'][:]=0
    result=new.update_group(head,critic,*new.make_optimizers(head,critic),episodes,{},horizon=8)
    assert result['targets'][0][0]==.125
    assert np.float32(episodes[0]['macro_rewards'].sum()/8)>.125


@pytest.mark.parametrize('corruption',['logit','base','probability','logp','zero_chosen','dtype','shape','action','nan','tensor'])
def test_identity_or_validation_failure_counts_and_unchanged_parameters(corruption):
    head,critic=Head('CAL'),new.fresh_critic(81)
    opts=new.make_optimizers(head,critic)
    episodes=group(head,critic,readonly=False)
    ep=episodes[0]
    if corruption=='logit':ep['logits'][0,0,0]=np.nextafter(ep['logits'][0,0,0],np.float32(np.inf))
    elif corruption=='base':ep['base_logits'][0,0,0]+=.01
    elif corruption=='probability':ep['probabilities'][0,0,25]+=1e-12;ep['probabilities'][0,0,26]-=1e-12
    elif corruption=='logp':ep['logp'][0,0]+=1e-7
    elif corruption=='zero_chosen':
        row=ep['probabilities'][0,0];row[1]+=row[0];row[0]=0
    elif corruption=='dtype':ep['probabilities']=ep['probabilities'].astype(np.float32)
    elif corruption=='shape':ep['hidden']=ep['hidden'][:1]
    elif corruption=='action':ep['action_index'][0,0]=27
    elif corruption=='tensor':ep['hidden']=torch.tensor(ep['hidden'],requires_grad=True)
    else:ep['macro_rewards'][0]=np.nan
    before=new.state_digest(head.state_dict()),new.state_digest(critic.state_dict())
    counts,record={},{}
    rng=snapshot_rng()
    with pytest.raises((ValueError,FloatingPointError)):
        new.update_group(head,critic,*opts,episodes,counts,horizon=8,live_record=record)
    assert_rng(rng)
    assert record['status']=='FAILED' and record['failure']['message']
    assert not opts[0].state and not opts[1].state
    assert before==(new.state_digest(head.state_dict()),new.state_digest(critic.state_dict()))
    assert counts.get('actor_optimizer_steps',0)==counts.get('critic_optimizer_steps',0)==0
    if corruption in ('logit','base','probability'):
        assert counts['actor_replay_rows']==counts['density_identity_rows']==20
        assert counts['target_rows']==4 and counts.get('critic_replay_rows',0)==0
        assert record['failure']['stage']=='density_identity'
        assert record['epochs'][0]['actor_step_completed'] is False
        assert record['final_actor_sha256']==record['initial_actor_sha256']
    json.dumps(record,allow_nan=False)


@pytest.mark.parametrize('failure',['actor_forward','actor_gradient','actor_optimizer','critic_forward','critic_gradient','critic_optimizer'])
def test_attempted_work_and_completed_step_failure_provenance(failure):
    head,critic=Head('CONT'),new.fresh_critic(81)
    opts=new.make_optimizers(head,critic)
    episodes=group(head,critic)
    counts,record={},{}
    handle=None
    if failure=='actor_forward':
        def forward(*args):raise RuntimeError('synthetic head forward failure')
        head.forward=forward
    elif failure=='critic_forward':
        def forward(*args):raise RuntimeError('synthetic critic forward failure')
        critic.forward=forward
    elif failure.endswith('gradient'):
        model=head if failure.startswith('actor') else critic
        handle=next(model.parameters()).register_hook(lambda gradient:gradient*float('inf'))
    else:
        opt=opts[0] if failure.startswith('actor') else opts[1]
        def step():raise RuntimeError('synthetic Adam failure')
        opt.step=step
    before=snapshot_rng()
    with pytest.raises(RuntimeError):
        new.update_group(head,critic,*opts,episodes,counts,horizon=8,live_record=record)
    if handle:handle.remove()
    assert_rng(before)
    stage=failure.replace('_forward','_replay')
    assert record['status']=='FAILED' and record['failure']['stage']==stage
    assert record['failure']['epoch']==0 and counts['target_rows']==4
    assert counts['actor_replay_rows']==(1 if failure=='actor_forward' else 20)
    actor_done=failure.startswith('critic')
    assert counts.get('actor_optimizer_steps',0)==int(actor_done)
    assert counts.get('critic_optimizer_steps',0)==0
    assert record['epochs'][0]['actor_step_completed']==actor_done
    assert record['epochs'][0]['critic_step_completed'] is False
    assert counts.get('actor_optimizer_attempts',0)==int(actor_done or failure=='actor_optimizer')
    assert counts.get('critic_optimizer_attempts',0)==int(failure=='critic_optimizer')
    assert counts.get('critic_replay_rows',0)==(4 if actor_done else 0)
    assert record['actor_movement_l2']>0 if actor_done else record['actor_movement_l2']==0
    json.dumps(record,allow_nan=False)


@pytest.mark.parametrize('bad',['single','triple','partial','horizon','count','ownership','dtype','shared','frozen'])
def test_group_model_optimizer_guards_before_replay(bad):
    head,critic=Head('CAL'),new.fresh_critic(81)
    opts=list(new.make_optimizers(head,critic))
    episodes=group(head,critic,readonly=False)
    horizon,counts=8,{}
    if bad=='single':episodes=episodes[:1]
    elif bad=='triple':episodes=episodes+[episodes[0]]
    elif bad=='partial':episodes[1]['values']=episodes[1]['values'][:1]
    elif bad=='horizon':horizon=6
    elif bad=='count':counts['critic_optimizer_steps']=float('nan')
    elif bad=='ownership':opts[0]=torch.optim.Adam(Head('CAL').parameters())
    elif bad=='dtype':head.double()
    elif bad=='shared':critic.shared=head.b
    else:head.b.requires_grad_(False)
    record={}
    with pytest.raises((ValueError,FloatingPointError)):
        new.update_group(head,critic,*opts,episodes,counts,horizon=horizon,live_record=record)
    assert record['status']=='FAILED' and 'actor_replay_rows' not in counts
    assert not opts[0].state and not opts[1].state


def test_callback_cannot_mutate_private_rollout_snapshots():
    head,critic=Head('CONT'),new.fresh_critic(81)
    episodes=group(head,critic,readonly=False)
    reference=deepcopy(episodes)
    other_head,other_critic=deepcopy(head),deepcopy(critic)
    mutated=[False]
    def mutate(model,inputs,output):
        if not mutated[0]:
            for ep in episodes:
                for key in new.ROLLOUT_KEYS:
                    ep[key][:]=0 if key=='action_index' else np.nan
            mutated[0]=True
    hook=head.register_forward_hook(mutate)
    actual=new.update_group(head,critic,*new.make_optimizers(head,critic),episodes,{},horizon=8)
    hook.remove()
    expected=new.update_group(other_head,other_critic,*new.make_optimizers(other_head,other_critic),reference,{},horizon=8)
    assert mutated[0] and actual==expected
    assert all(torch.equal(p,q) for p,q in zip(head.parameters(),other_head.parameters()))
    assert all(torch.equal(p,q) for p,q in zip(critic.parameters(),other_critic.parameters()))


def test_fp32_target_overflow_charges_attempted_targets_before_any_replay():
    head,critic=Head('CAL'),new.fresh_critic(81)
    episodes=group(head,critic,readonly=False)
    episodes[0]['macro_rewards'][:]=np.finfo(np.float64).max
    counts,record={},{}
    with pytest.raises(FloatingPointError,match='targets'):
        new.update_group(head,critic,*new.make_optimizers(head,critic),episodes,counts,horizon=8,live_record=record)
    assert counts=={'target_rows':4}
    assert record['failure']['stage']=='targets' and record['epochs']==[]
    assert record['initial_actor_sha256']==record['final_actor_sha256']
    json.dumps(record,allow_nan=False)


def test_optimizer_exception_after_mutation_retains_observed_state():
    head,critic=Head('CAL'),new.fresh_critic(81)
    episodes=group(head,critic)
    opts=new.make_optimizers(head,critic)
    step=opts[0].step
    def uncertain_step():
        step()
        raise RuntimeError('synthetic exception after Adam mutation')
    opts[0].step=uncertain_step
    counts,record={},{}
    with pytest.raises(RuntimeError,match='after Adam'):
        new.update_group(head,critic,*opts,episodes,counts,horizon=8,live_record=record)
    assert counts['actor_optimizer_attempts']==1 and counts.get('actor_optimizer_steps',0)==0
    assert record['actor_optimizer_step_values']==[1]*len(list(head.parameters()))
    assert record['actor_movement_l2']>0
    assert record['final_actor_sha256']!=record['initial_actor_sha256']
    assert record['epochs'][0]['actor_step_completed'] is False
    assert record['failure']['stage']=='actor_optimizer'
