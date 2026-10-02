"""Fixed real per-step training and sampled frozen missions; no counterfactual panel."""
import gc
from pathlib import Path
import time
import numpy as np
from . import contract as c,evidence as e,trace,ordinary


def check_counts(meter,terminal=False):
    if meter.counts.get('native_steps',0)>1196000:raise AssertionError('fixed native exposure exceeded')
    if sum(meter.counts.get('optimizer_'+k,0) for k in e.OPTIMIZERS)>615600:raise AssertionError('fixed optimizer exposure exceeded')
    if terminal and (meter.counts.get('native_steps')!=1196000 or sum(meter.counts.get('optimizer_'+k,0) for k in e.OPTIMIZERS)!=615600):raise AssertionError('incomplete fixed study exposure')


def native_transition(env,action,meter,category):
    before=env.host.event_counts['native_steps'];meter.add('native_step_attempts')
    try:return env.step(action)
    finally:
        completed=env.host.event_counts['native_steps']-before
        meter.add('native_steps',completed);meter.add(category,completed)


def account_host(host,meter):
    for key,value in host.event_counts.items():meter.add('host_'+key,value)


def validate_prefix(arrays,complete):
    ticks=len(arrays['payment'])
    if ticks>500 or complete and ticks!=500:raise AssertionError('complete500 transition evidence')
    for key in c.LEDGER_FIELDS:
        if arrays[key].shape!=(ticks,)+c.LEDGER_FIELDS[key][0]:raise AssertionError('ledger shape '+key)
    for key in ('positions','connections','routes','route_lengths','transmitter_mask'):
        if arrays[key].shape!=(ticks+1,)+c.STATE_FIELDS[key][0]:raise AssertionError('successor evidence '+key)
    if arrays['raw_actions'].shape!=(ticks,6,3) or arrays['executed_actions'].shape!=(ticks,6,3):raise AssertionError('all actual commands')
    if complete and (not arrays['terminated'][-1] or arrays['terminated'][:-1].any() or arrays['truncated'].any()):raise AssertionError('native complete terminal boundary')
    if not np.allclose(arrays['external_scalar'],arrays['payment']/6,rtol=0,atol=0):raise AssertionError('actual external R/6')
    if arrays['paid'].size and (np.diff(arrays['paid'].astype(int),axis=0)<0).any():raise AssertionError('private once-only window ledger')
    for key,value in arrays.items():e.finite(value,key)


class Store:
    def __init__(self,out,args,meter,config):
        self.out=Path(out);self.args=args;self.meter=meter;self.config=config
        self.manifest={'schema':1,'frozen':[],'training':[],'checkpoints':{},'initial_alias':None}
        self.summary={'schema':1,'object':c.OBJECT,'launch_sha':args.launch_sha,'seed':args.seed,'status':'STARTED','fits':{},'inflight':None}
    def publish(self):
        check_counts(self.meter);self.summary['cost']=self.meter.report()
        e.write_json(self.out/'manifest.json',self.manifest);e.write_json(self.out/'summary.json',self.summary)
    def inflight(self,kind,**details):self.summary['inflight']={'kind':kind,**details};self.publish()
    def saved(self,path):return e.identity(path,self.out)
    def record(self,kind,arrays,metadata,relative):
        raw=self.out/(relative+'.npz');meta=self.out/(relative+'.json')
        validate_prefix(arrays,True) if kind=='frozen' else None
        e.write_npz(raw,arrays);e.write_json(meta,metadata)
        row={k:metadata[k] for k in ('programme','world','phase') if k in metadata}
        if kind=='training':row.update(arm=metadata['arm'],rollout=metadata['rollout'],worlds=metadata['worlds'])
        row.update(raw=self.saved(raw),metadata=self.saved(meta));self.manifest[kind].append(row);self.summary['inflight']=None;self.publish();return row
    def failed_trace(self,traces):
        for lane,item in enumerate(traces):
            e.write_npz(self.out/'partial'/f'inflight_lane_{lane:02}.npz',item.arrays())


def frozen_mission(store,programme,world,phase,agent=None,checkpoint=None):
    from .adapter import make_env
    import torch
    meter=store.meter;meter.phase='frozen/'+programme+'/'+phase
    store.inflight('frozen',programme=programme,world=world,phase=phase)
    env=make_env(world);item=None;before_counts=meter.counts.copy();start=time.process_time()
    try:
        obs,info=env.reset(seed=world);state=info['state'];item=trace.EpisodeTrace(env,obs,state,True)
        controller=None;held=state.copy()
        if agent is not None:
            agent.train(False);agent.reset_env_state(0);digest=e.digest_agent(agent);context=trace.reset_context(agent)
        else:
            controller=ordinary.RayChain(trace.held_positions(state),env.users,env.schedule) if programme=='O' else ordinary.Sticky(world)
            digest=None;context=None
        # Factory and native reset work precede this addressed inference stream.
        e.seed_rng(world+51);rng=e.rng_state()
        metadata={'schema':1,'object':c.OBJECT,'programme':programme,'world':world,'phase':phase,'launch_sha':store.args.launch_sha,
                  'pre_world_rng':rng,'reset_context':context,'initial_host_rng':item.initial_host_rng,'initial_state_sha256':item.initial_digest(),
                  'checkpoint':checkpoint,'state_digest':digest,'sampling_seed':world+51,'source_sha256':store.config['source_sha256'],
                  'worker_config_sha256':e.hash_file(store.out/'config.json')}
        guard=e.instrument_agent(agent,meter) if agent is not None else __import__('contextlib').nullcontext({})
        with guard as optimizer_counts,torch.no_grad():
            for tick in range(500):
                if agent is not None:
                    actions,_,data=agent.step(state[None],obs[None],np.array([tick]),np.array([False]),deterministic=False,return_step_data=True,build_infos=False)
                    e.finite((actions,data),'frozen sampled policy')
                    if agent.d2_enabled:
                        decision=tick%10==0
                        if bool(data['d2_sample_Z'][0])!=decision or not np.array_equal(data['d2_sampled_mask'][0],np.full(6,decision)):raise AssertionError('inline fixed ten-step/six-agent audit clock')
                    item.policy(agent,data);action=actions[0]
                    meter.add('frozen_model_steps')
                else:
                    if tick%10==0:held=state.copy()
                    action=controller.actions(tick,trace.own_positions(obs),trace.held_positions(held))
                    item.rows.setdefault('ordinary_targets',[]).append(controller.targets.copy())
                obs,_,term,trunc,info=native_transition(env,action,meter,'frozen_native_steps');state=info['next_state'];item.transition(env,obs,state,info)
                if term!=(tick==499) or trunc:raise AssertionError('frozen cadence/terminal')
            if any(optimizer_counts.values()):raise AssertionError('frozen inference trained')
        if agent is not None and e.digest_agent(agent)!=digest:raise AssertionError('frozen full model or normalizer changed')
        metadata.update(cpu_seconds=time.process_time()-start,host_counts=env.host.event_counts.copy(),counts_delta={k:v-before_counts.get(k,0) for k,v in meter.counts.items()},metrics=item.summary(),optimizer_steps=0)
        if controller is not None:
            metadata['ordinary']={key:e.jsonable(value) for key,value in vars(controller).items() if key!='rng'}
            if programme=='B':metadata['ordinary']['terminal_rng']=e.jsonable(controller.rng.bit_generator.state)
            if programme=='O' and (controller.assignment_comparisons!=722 or controller.slot_distances!=40):raise AssertionError('fixed O assignment budget')
        return store.record('frozen',item.arrays(),metadata,f'raw/frozen/{programme}_{world}')
    except BaseException:
        if item is not None:store.failed_trace([item])
        raise
    finally:account_host(env.host,meter);env.close()


def panel(store,programme,checkpoint,arm):
    agent,_,_=e.load_agent(store.out/checkpoint['path'],arm,1,store.out/'logs'/programme,store.meter)
    try:
        rows=[]
        for world in c.WORLDS if programme in c.PROGRAMMES else ():
            rows.append(frozen_mission(store,programme,world,'main',agent,checkpoint))
        rows.append(frozen_mission(store,programme,c.AUDIT_WORLD,'audit',agent,checkpoint))
        return rows
    finally:del agent;gc.collect()


def attach_training_rewards(agent,traces):
    buffer=agent.rollout_buffer
    for lane,item in enumerate(traces):
        item.rows['mixed_low_reward']=list(buffer.rewards[:500,lane].copy())
        for key in c.D2_FIELDS:
            if hasattr(buffer,key):item.rows[key]=list(getattr(buffer,key)[:500,lane].copy())
        # Existing stored component arrays: no discriminator re-evaluation for evidence.
        for target,key in (('reward_env','reward_env'),('reward_team_disc','reward_team_disc'),('reward_ind_disc','reward_ind_disc'),('reward_process','reward_process')):
            item.rows[target]=list(getattr(buffer,key)[:500,lane].copy())
        if not np.allclose(np.asarray(item.rows['reward_env']),np.asarray(item.rows['external_scalar'])[:,None],rtol=1e-6,atol=1e-8):raise AssertionError('stored external scalar units')
        if agent.config.disable_discriminator_rewards and not np.allclose(buffer.rewards[:500,lane],buffer.reward_env[:500,lane],rtol=0,atol=0):raise AssertionError('noD/SET low reward identity')
        if agent.config.policy_interruption_mode=='d2':
            valid=buffer.d2_team_valid[:500,lane];starts=np.flatnonzero(valid)
            if not np.array_equal(starts,np.arange(0,500,10)):raise AssertionError('synchronous ten-step D2 segments')
            rewards=np.asarray(item.rows['external_scalar'])
            expected=np.array([np.dot(np.power(agent.config.gamma,np.arange(10)),rewards[s:s+10]) for s in starts])
            if not np.allclose(buffer.d2_team_reward[starts,lane],expected,rtol=2e-6,atol=1e-8):raise AssertionError('D2 external discounted team segments')


def fit(store,arm,initial_checkpoint,agent,cfg):
    from .adapter import make_env
    from experiments.candidates.coupled_host_joint_skills_stage1.runner import capture_parameters,parameter_motion,terminal_facts
    from .configuration import config_dict
    meter=store.meter;envs=[];traces=[];initial=capture_parameters(agent);fit_summary={'status':'STARTED','rollouts':[],'config':config_dict(cfg)}
    store.summary['fits'][arm]=fit_summary;store.inflight('fit',arm=arm,rollout=0);meter.add('fits_started')
    try:
        for lane in range(16):envs.append(make_env(c.training_world(lane,0)))
        states=[];observations=[]
        for lane,env in enumerate(envs):
            obs,info=env.reset(seed=c.training_world(lane,0));observations.append(obs);states.append(info['state']);agent.reset_env_state(lane)
        states,observations=np.stack(states),np.stack(observations);steps=np.zeros(16,dtype=int);dones=np.zeros(16,dtype=bool)
        # All factory/reset/initial frozen work is outside this training RNG stream.
        e.seed_rng(c.TRAIN_SEEDS[arm]);agent.train(True)
        fit_summary['training_rng_initial']=e.rng_state()
        with e.instrument_agent(agent,meter) as optimizer_counts:
            for rollout in range(1,46):
                store.inflight('fit',arm=arm,rollout=rollout);meter.phase='collection/'+arm
                pre_rng=e.rng_state();start=time.process_time();worlds=[c.training_world(l,rollout-1) for l in range(16)]
                traces=[trace.EpisodeTrace(env,observations[l],states[l],False) for l,env in enumerate(envs)]
                before=optimizer_counts.copy()
                if arm!='SET':agent.reset_d2_metrics()
                for tick in range(500):
                    actions,_,data=agent.step(states,observations,steps,dones,deterministic=False,return_step_data=True,build_infos=False)
                    e.finite((actions,data),'training sampled policy')
                    if actions.shape!=(16,6,3):raise AssertionError('all six original commands')
                    saved=actions.copy();next_states=[];next_observations=[];rewards=[];next_dones=[]
                    for lane,env in enumerate(envs):
                        traces[lane].policy(agent,data,lane)
                        obs,reward,term,trunc,info=native_transition(env,actions[lane],meter,'training_native_steps');ns=info['next_state']
                        traces[lane].transition(env,obs,ns,info);next_states.append(ns);next_observations.append(obs);rewards.append(reward);next_dones.append(bool(term))
                        if trunc or term!=(tick==499):raise AssertionError('training500 full terminal')
                    if not np.array_equal(actions,saved):raise AssertionError('raw sampled training commands mutated')
                    next_states,next_observations=np.stack(next_states),np.stack(next_observations);rewards=np.asarray(rewards);next_dones=np.asarray(next_dones,dtype=bool)
                    meter.phase='intrinsic/'+arm
                    try:components=agent.store_transition_batch(states=states,next_states=next_states.copy(),observations=observations,next_observations=next_observations.copy(),actions=actions,rewards=rewards,dones=next_dones,infos_batch=None,rollout_step_idx=tick,step_data=data)
                    finally:meter.phase='collection/'+arm
                    for lane,item in enumerate(traces):
                        item.reward_components(components[lane])
                        if not cfg.disable_discriminator_training:
                            meter.add('endogenous_team_discriminator_labels');meter.add('endogenous_individual_discriminator_labels',6)
                    meter.add('training_model_steps',16);meter.add('stored_team_steps',16)
                    # Real terminal successor was stored before the original eager reset.
                    for lane,env in enumerate(envs):
                        if next_dones[lane]:
                            obs,info=env.reset(seed=c.training_world(lane,rollout));next_states[lane],next_observations[lane]=info['state'],obs;agent.reset_env_state(lane);steps[lane]=0
                            meter.add('eager_terminal_resets');meter.add('unused_final_world_materializations',int(rollout==45))
                        else:steps[lane]+=1
                    states,observations,dones=next_states,next_observations,next_dones
                attach_training_rewards(agent,traces)
                facts=terminal_facts(agent,'H' if arm!='SET' else 'SET',500)
                if not facts['low_level_dones_last_step_all_true'] or facts['low_level_dones_before_last_any']:raise AssertionError('terminal bootstrap masks')
                collection_cpu=time.process_time()-start;meter.phase='update/'+arm;update_start=time.process_time()
                losses=agent.update(last_values=np.zeros((16,6),dtype=np.float32),dones=dones.copy(),steps_in_buffer=500,last_state=states.copy(),last_observations=observations.copy());e.finite(losses,'real update losses');meter.add('rollout_updates')
                meta={'schema':1,'arm':arm,'rollout':rollout,'worlds':worlds,'pre_rollout_rng':pre_rng,'terminal_facts':facts,'losses':e.jsonable(losses),
                      'optimizer_delta':{k:v-before[k] for k,v in optimizer_counts.items()},'optimizer_total':optimizer_counts.copy(),'parameter_motion':parameter_motion(agent,initial),
                      'collection_cpu_seconds':collection_cpu,'update_cpu_seconds':time.process_time()-update_start,'launch_sha':store.args.launch_sha,
                      'reward_units':'existing buffer reward_env/team_disc/ind_disc/process; mixed_low_reward actual PPO low reward; D2 rewards external-only gamma-discounted',
                      'metrics':[item.summary() for item in traces], 'initial_state_sha256':[item.initial_digest() for item in traces]}
                if arm!='SET':
                    d2=agent.get_d2_metrics();meta['d2_metrics']=e.jsonable(d2)
                    if any(d2['cause_counts'][name] for name in ('gap','team_gap','cap')):raise AssertionError('unselected interruption cause')
                    if d2['team_decisions']!=d2['decision_steps'] or d2['sampled_total']!=6*d2['decision_steps'] or d2['decision_steps']*10!=d2['steps']:raise AssertionError('six synchronous D2 labels')
                lane_arrays=[item.arrays() for item in traces]
                arrays={key:np.stack([lane[key] for lane in lane_arrays]) for key in lane_arrays[0]}
                for lane in lane_arrays:validate_prefix(lane,True)
                store.record('training',arrays,meta,f'raw/training/{arm}/rollout_{rollout:02}')
                fit_summary['rollouts'].append({'rollout':rollout,'optimizer_total':optimizer_counts.copy(),'parameter_motion':meta['parameter_motion']});agent.clear_buffers();traces=[];store.publish()
            if optimizer_counts!=c.OPTIMIZER_TOTALS[arm]:raise AssertionError('exact real optimizer totals '+repr(optimizer_counts))
        fit_summary.update(status='COMPLETE',parameter_motion=parameter_motion(agent,initial))
        final=store.out/'checkpoints'/arm/'final.pt';e.save_checkpoint(agent,cfg,final,arm,'final',store.args.launch_sha,meter)
        store.manifest['checkpoints'][arm]['final']=store.saved(final);store.publish();return store.saved(final)
    except BaseException:
        if traces:store.failed_trace(traces)
        fit_summary.update(status='FAILED',failure_rng=e.rng_state())
        try:
            failed=store.out/'checkpoints'/arm/'failed.pt'
            e.save_checkpoint(agent,cfg,failed,arm,'failed',store.args.launch_sha,meter)
            fit_summary['failed_checkpoint']=store.saved(failed)
        except BaseException as checkpoint_error:fit_summary['failed_checkpoint_error']=repr(checkpoint_error)
        raise
    finally:
        for env in envs:account_host(env.host,meter);env.close()


def run(root,out,args,context):
    from .configuration import initial_alias_configs,make_config
    store=Store(out,args,context['meter'],context['config']);meter=store.meter
    try:
        H_digest=None;H_initial=None;H_rng=None
        for arm in c.ARMS:
            e.seed_rng(c.INIT_SEEDS[arm]);pre_init=e.rng_state();agent,cfg=e.build_agent(arm,16,store.out/'logs'/(arm+'_training'),meter);after_init=e.rng_state();digest=e.digest_agent(agent)
            if arm=='H-noD':
                proof=initial_alias_configs(make_config('H',16),cfg)
                if digest!=H_digest or pre_init!=H_rng['before'] or after_init!=H_rng['after']:raise AssertionError('rigorous H/noD initial module/input/RNG identity')
                proof.update(state_digest=digest,initial_checkpoint=H_initial,construction_rng=H_rng,source_sha256=context['config']['source_sha256'],alias_main='H-initial',aliased_worlds=c.WORLDS)
                alias=store.out/'initial_alias.json';e.write_json(alias,proof);store.manifest['initial_alias']=store.saved(alias);initial_checkpoint=H_initial
            else:
                initial_path=store.out/'checkpoints'/arm/'initial.pt';e.save_checkpoint(agent,cfg,initial_path,arm,'initial',args.launch_sha,meter);initial_checkpoint=store.saved(initial_path)
                if arm=='H':H_digest=digest;H_initial=initial_checkpoint;H_rng={'before':pre_init,'after':after_init}
            store.manifest['checkpoints'][arm]={'initial':initial_checkpoint};store.publish()
            panel(store,arm+'-initial',initial_checkpoint,arm)
            final=fit(store,arm,initial_checkpoint,agent,cfg);del agent;gc.collect()
            panel(store,arm+'-final',final,arm)
        # The two wiring audits compare raw commands/hidden/inputs, never performance.
        H=next(r for r in store.manifest['frozen'] if r['programme']=='H-initial' and r['phase']=='audit')
        N=next(r for r in store.manifest['frozen'] if r['programme']=='H-noD-initial')
        with np.load(store.out/H['raw']['path'],allow_pickle=False) as a,np.load(store.out/N['raw']['path'],allow_pickle=False) as b:
            if set(a.files)!=set(b.files) or any(not np.array_equal(a[k],b[k]) for k in a.files):raise AssertionError('initial H/noD full audit inference identity')
        for programme in ('O','B'):
            for world in (*c.WORLDS,c.AUDIT_WORLD):frozen_mission(store,programme,world,'audit' if world==c.AUDIT_WORLD else 'main')
        check_counts(meter,True)
        if len(store.manifest['frozen'])!=232 or len(store.manifest['training'])!=135:raise AssertionError('complete evidence counts')
        store.summary.update(status='COMPLETE',inflight=None,manifest=store.saved(store.out/'manifest.json'),new_fits=3,new_native_steps=meter.counts['native_steps'],optimizer_steps=615600)
        store.publish();return store.summary
    except BaseException as exc:
        store.summary.update(status='FAILED',error=type(exc).__name__+': '+str(exc));store.publish();raise
