"""One append-only episode prefix; training omits full row/channel duplication."""
import numpy as np
from . import adapter,contract as c,evidence as e,metrics

TRAIN_STATE_FIELDS=('positions','connections','routes','route_lengths','transmitter_mask')


def own_positions(observations):
    positions=np.asarray(observations,dtype=np.float64)[:,:3].copy();positions[:,:2]*=5000;positions[:,2]=50+100*positions[:,2]
    return positions


def held_positions(state):
    positions=np.asarray(state,dtype=np.float64)[:18].reshape(6,3).copy();positions[:,:2]*=5000;positions[:,2]=50+100*positions[:,2]
    return positions


def reset_context(agent):
    return {'actor_hidden':e.jsonable(getattr(agent,'actor_hidden_np',None)),'critic_hidden':e.jsonable(getattr(agent,'critic_hidden_np',None)),
            'team_skills':e.jsonable(agent.env_team_skills),'agent_skills':e.jsonable(agent.env_agent_skills),
            'timers':e.jsonable(agent.env_timers),'skill_ages':e.jsonable(agent.env_skill_ages),
            'central_snapshot_valid':e.jsonable(getattr(agent,'_central_snapshot_valid',None)),
            'entry_dones':[False],'entry_steps':[0],'skill_reset':'reset_env_state(0) before every frozen episode; no carried episode state'}


class EpisodeTrace:
    def __init__(self,env,observations,state,full):
        self.full=full;self.state_keys=tuple(c.STATE_FIELDS) if full else TRAIN_STATE_FIELDS
        self.static={'users':env.users.copy(),'schedule':env.schedule.copy(),'packet':env.packet.copy(),
                     'bs_positions':np.array(env.host.ground_bs_positions,dtype=np.float64,copy=True)}
        self.rows={key:[] for key in self.state_keys};self.rows.update({key:[] for key in c.LEDGER_FIELDS})
        self.rows.update(raw_actions=[],executed_actions=[])
        if full:self.rows.update(observations=[],states=[])
        self.initial_host_rng=e.jsonable(env.host.np_random.get_state())
        self.state(env,observations,state)
    def state(self,env,observations,state):
        snap=adapter.snapshot(env.host,self.full)
        for key in self.state_keys:self.rows[key].append(snap[key])
        if self.full:self.rows['observations'].append(np.asarray(observations,dtype=np.float32).copy());self.rows['states'].append(np.asarray(state,dtype=np.float32).copy())
    def policy(self,agent,data,lane=0):
        for key in c.STEP_FIELDS:
            if key in data:self.rows.setdefault('step__'+key,[]).append(np.asarray(data[key])[lane].copy())
        logs=data['log_probs'][lane]
        for key in ('team_log_prob','agent_log_probs','state_value','agent_values'):
            value=logs.get(key,0. if key in ('team_log_prob','state_value') else [0.]*6)
            self.rows.setdefault('coord__'+key,[]).append(np.asarray(value,dtype=np.float32))
        if self.full:
            self.rows.setdefault('actor_hidden_input',[]).append(agent.get_prev_actor_hidden_np(lane,n_agents=6))
            self.rows.setdefault('critic_hidden_input',[]).append(agent.get_prev_critic_hidden_np(lane,n_agents=6))
            if agent.use_central_snapshot:
                self.rows.setdefault('held_states',[]).append(agent._central_snapshot_states[lane].copy())
                self.rows.setdefault('held_observations',[]).append(agent._central_snapshot_obs[lane].copy())
    def transition(self,env,obs,state,info):
        if not np.array_equal(env.host.user_positions,self.static['users'].astype(np.float64)):raise AssertionError('static registered user identity')
        previous=self.rows['positions'][-1]
        expected=previous+env.host.last_executed_actions*env.host.max_speed*env.host.time_step
        expected[:,:2]=np.clip(expected[:,:2],0,env.host.area_size);expected[:,2]=np.clip(expected[:,2],*env.host.height_range)
        if not np.array_equal(expected,env.host.uav_positions):raise AssertionError('dtype-preserving original clipped motion')
        self.rows['raw_actions'].append(env.host.last_raw_actions.copy());self.rows['executed_actions'].append(env.host.last_executed_actions.copy())
        for key in c.LEDGER_FIELDS:self.rows[key].append(np.asarray(info['window'][key],dtype=c.LEDGER_FIELDS[key][1]))
        self.state(env,obs,state)
    def reward_components(self,components):
        if not isinstance(components,dict):raise ValueError('native transition storage failed')
        for key in ('env','team_disc','ind_disc','process'):
            self.rows.setdefault('reward_'+key,[]).append(np.asarray(components[key],dtype=np.float32).copy())
    def arrays(self):return {**self.static,**{key:np.asarray(values) for key,values in self.rows.items()}}
    def initial_digest(self):
        keys=('users','schedule','packet','bs_positions')
        values=[self.static[k] for k in keys]+[self.rows[k][0] for k in self.state_keys]
        if self.full:values+=[self.rows['observations'][0],self.rows['states'][0]]
        return e.array_digest(*values)
    def summary(self):return metrics.mission(self.arrays())
