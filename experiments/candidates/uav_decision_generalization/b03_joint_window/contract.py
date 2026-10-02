"""Frozen exposure, programme order and explicit saved-state schema."""
DIRECTION = 'uav_decision_generalization'
OBJECT = 'UAV-JOINT-WINDOW-B03'
MASTER = 109230101
ARMS = ('H', 'H-noD', 'SET')
INIT_SEEDS = {'H':109230101, 'H-noD':109230101, 'SET':109230102}
TRAIN_SEEDS = {'H':109230201, 'H-noD':109230201, 'SET':109230202}
WORLDS = tuple(range(109220000,109220032))
AUDIT_WORLD = 109229000
PROGRAMMES = ('H-initial','SET-initial','H-final','H-noD-final','SET-final','O','B')
AUDITS = ('H-initial','H-noD-initial','SET-initial','H-final','H-noD-final','SET-final','O','B')
HORIZON, LANES, ROLLOUTS = 500,16,45
OBS_DIM,STATE_DIM,SET_INPUT_DIM = 211,154,1637
OPTIMIZER_TOTALS = {'H':{'coordinator':675,'discoverer_actor':101250,'discoverer_critic':101250,'team_discriminator':675,'individual_discriminator':2700},
                    'H-noD':{'coordinator':675,'discoverer_actor':101250,'discoverer_critic':101250,'team_discriminator':675,'individual_discriminator':2700},
                    'SET':{'coordinator':0,'discoverer_actor':101250,'discoverer_critic':101250,'team_discriminator':0,'individual_discriminator':0}}
# Routes contain the complete original node sequence: UAV0..5, BS0 encoded6;
# -1 padding, length0 for unrouted. No inferred path replaces a native path.
STATE_FIELDS = {'positions':((6,3),'float64'), 'connections':((6,50),'bool'),
                'user_sinr':((6,50),'float64'), 'uav_sinr':((6,6),'float64'),
                'uav_connections':((6,6),'bool'), 'bs_connections':((6,1),'bool'),
                'routes':((6,7),'int16'), 'route_lengths':((6,),'int16'),
                'transmitter_mask':((6,),'bool')}
LEDGER_FIELDS = {'routed_user_mask':((50,),'bool'),'associated_user_mask':((50,),'bool'),
                 'active_cluster':((),'int16'),'active_count':((),'int16'), 'window':((),'int16'),
                 'run_length':((),'int16'),'paid':((4,),'bool'),'payment':((),'float64'),
                 'external_scalar':((),'float64'),'dense_reward':((),'float64'),
                 'coverage_backhauled':((),'float64'),'throughput_term':((),'float64'),
                 'frontend_capacity_with_path_mbps':((),'float64'),
                 'action_clip_events':((),'int16'),'terminated':((),'bool'),'truncated':((),'bool')}
STEP_FIELDS = ('team_skills','agent_skills','action_logprobs','values','skill_changed','skill_timer','env_id',
               'd2_decision','d2_team_decision','d2_sampled_mask','d2_sample_Z','d2_order','d2_agent_ages','d2_team_ages','d2_agent_cause','d2_team_cause')
D2_FIELDS = ('d2_team_valid','d2_team_reward','d2_team_elapsed','d2_team_terminal',
             'd2_agent_valid','d2_agent_reward','d2_agent_elapsed','d2_agent_terminal')


def training_world(lane,episode):
    if type(lane)!=int or type(episode)!=int or not 0<=lane<16 or not 0<=episode<=45:
        raise ValueError('fixed training lane/episode address required')
    return 109210000+16*episode+lane


def frozen_contract():
    return {'schema':1,'object':OBJECT,'master':MASTER,'arms':ARMS,'init_seeds':INIT_SEEDS,'training_rng_seeds':TRAIN_SEEDS,
            'training_worlds':[training_world(l,e) for e in range(45) for l in range(16)],
            'unused_final_reset_worlds':[training_world(l,45) for l in range(16)],'worlds':WORLDS,'audit_world':AUDIT_WORLD,
            'programmes':PROGRAMMES,'audit_programmes':AUDITS,'horizon':HORIZON,'lanes':LANES,'rollouts':ROLLOUTS,
            'obs_dim':OBS_DIM,'state_dim':STATE_DIM,'SET_input_dim':SET_INPUT_DIM,'packet_bytes':404,
            'native_steps':1196000,'optimizer_steps':615600,'optimizer_totals':OPTIMIZER_TOTALS,
            'action_head':'original unbounded DiagGaussian; ignored nominal logstd bounds; native unit-ball clip',
            'reward':'once-only post-routing20-consecutive/8-users window payment; R/6; dense learning weight0',
            'state_fields':STATE_FIELDS,'ledger_fields':LEDGER_FIELDS,'step_fields':STEP_FIELDS,'d2_fields':D2_FIELDS}
