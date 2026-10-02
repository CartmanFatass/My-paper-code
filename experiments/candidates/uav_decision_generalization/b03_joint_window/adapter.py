"""Original physics with registered users and one post-routing ledger advance."""
import numpy as np
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from experiments.candidates.coupled_host_joint_skills_stage1.host import CoupledRelayHost,HOST_CONTRACT_KWARGS,check_contract
from experiments.candidates.coupled_host_joint_skills_stage1.adapter import ContractCountAdapter
from . import task


class RegisteredHost(CoupledRelayHost):
    def __init__(self,world):
        self.event_counts={'constructor_calls':1,'reset_calls':0,'native_step_calls':0,'native_steps':0,'dense_reward_entries':0,'parent_reward_entries':0}
        self.registry=None
        super().__init__(area_size=5000,seed=int(world),**HOST_CONTRACT_KWARGS)
        check_contract(self)
    def reset(self,seed=None,options=None):
        if seed is None:raise ValueError('explicit registered world required')
        self.registry=task.world_registry(int(seed));self.event_counts['reset_calls']+=1
        return super().reset(seed=int(seed),options=options)
    def _generate_user_positions(self):
        # No draws from the original RandomState: its initial UAV draw order is retained.
        return self.registry[0].astype(np.float64)
    def _compute_reward(self):
        self.event_counts['dense_reward_entries']+=1;self.event_counts['parent_reward_entries']+=1
        return super()._compute_reward()
    def step(self,actions):
        self.event_counts['native_step_calls']+=1
        self.last_raw_actions=np.asarray([np.array(actions[a],copy=True) for a in self.possible_agents])
        executed=[]
        for raw in self.last_raw_actions:
            value=raw.copy()
            if not np.issubdtype(value.dtype,np.floating):value=value.astype(float)
            norm=float(np.linalg.norm(value))
            if norm>1.:value=value/norm
            executed.append(value)
        self.last_executed_actions=np.asarray(executed)
        before=int(self.current_step)
        try:return super().step(actions)
        finally:self.event_counts['native_steps']+=int(self.current_step)-before


def routes_array(paths):
    result=np.full((6,7),-1,dtype=np.int16);lengths=np.zeros(6,dtype=np.int16)
    for agent,path in paths.items():
        nodes=[int(index) if kind=='uav' else 6+int(index) if kind=='ground_bs' else -2 for kind,index in path]
        if len(nodes)>7 or any(n<0 or n>6 for n in nodes):raise ValueError('complete native route node identity')
        result[int(agent),:len(nodes)]=nodes;lengths[int(agent)]=len(nodes)
    return result,lengths


def snapshot(host,full):
    routes,lengths=routes_array(host.routing_paths)
    result={'positions':np.array(host.uav_positions,dtype=np.float64,copy=True),
            'connections':np.array(host.connections,dtype=bool,copy=True),'routes':routes,'route_lengths':lengths,
            'transmitter_mask':np.array(host.transmitter_mask,dtype=bool,copy=True)}
    if not result['transmitter_mask'].all():raise ValueError('all original transmitters stay on')
    if full:
        result.update(user_sinr=np.array(host.sinr_matrix,dtype=np.float64,copy=True),uav_sinr=np.array(host.uav_sinr_matrix,dtype=np.float64,copy=True),
                      uav_connections=np.array(host.uav_connections,dtype=bool,copy=True),bs_connections=np.array(host.uav_bs_connections,dtype=bool,copy=True))
    return result


class WindowAdapter:
    def __init__(self,base):
        self.base=base;self.host=base.host;self.n_uavs=6;self.n_users=50;self.obs_dim=211;self.state_dim=154
        self.action_dim=3;self.action_space=base.action_space;self.ledger=None
    def __getattr__(self,name):return getattr(self.base,name)
    def reset(self,seed=None,options=None):
        original,info=self.base.reset(seed=seed,options=options)
        self.users,self.schedule,self.packet=(x.copy() for x in self.host.registry)
        self.ledger=task.WindowLedger(self.schedule)
        if not np.array_equal(self.host.user_positions,self.users.astype(np.float64)):raise ValueError('host uses decoded registered integer users')
        info=dict(info);info['state']=task.augmented_state(info['state'],self.schedule,0)
        return task.augmented_observations(original,self.users,self.schedule,0),info
    def step(self,actions):
        if self.ledger is None:raise RuntimeError('explicit reset before action')
        before=self.ledger.tick;source=np.asarray(actions);saved=source.copy()
        observations,_,terminated,truncated,info=self.base.step(actions)
        if not np.array_equal(source,saved):raise AssertionError('native clip mutated original learner action')
        if self.host.current_step!=before+1 or bool(terminated)!=(before+1==500) or bool(truncated):raise ValueError('complete primitive successor/terminal contract')
        routed=np.array([i in self.host.routing_paths for i in range(6)],dtype=bool)
        facts=self.ledger.advance(np.asarray(self.host.connections,dtype=bool),routed)
        dense=info['contract']
        facts.update(dense_reward=float(dense['contract_reward']),coverage_backhauled=float(dense['coverage_backhauled']),
                     throughput_term=float(dense['throughput_term']),frontend_capacity_with_path_mbps=float(dense['frontend_capacity_with_path_mbps']),
                     action_clip_events=int(dense['action_clip_events']),terminated=bool(terminated),truncated=bool(truncated))
        info=dict(info);info['window']=facts;info['next_state']=task.augmented_state(info['next_state'],self.schedule,self.ledger.tick)
        return task.augmented_observations(observations,self.users,self.schedule,self.ledger.tick),facts['external_scalar'],terminated,truncated,info
    def close(self):self.base.close()


def make_env(world):
    host=RegisteredHost(int(world))
    return WindowAdapter(ContractCountAdapter(ParallelToArrayAdapter(host,seed=int(world))))
