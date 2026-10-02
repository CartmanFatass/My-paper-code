"""One fixed original per-step configuration with registered tensor dimensions."""
from configs.config_1 import Config
from hmasd.baselines import apply_algorithm_config
from experiments.candidates.coupled_host_joint_skills_stage1.configuration import config_dict as original_config_dict
from . import contract as c


def make_config(arm,lanes):
    if arm not in c.ARMS or lanes not in (1,16):raise ValueError('fixed arm and scientific lane count required')
    config=Config();config.n_uavs=6;config.n_users=50;config.num_envs=lanes
    config.rollout_length=config.episode_length=500;config.k=10;config.seed=c.INIT_SEEDS[arm]
    config.hidden_size=config.embedding_dim=config.gru_hidden_size=256
    config.n_heads=8;config.n_encoder_layers=config.n_decoder_layers=2
    config.continuous_action_distribution='gaussian';config.continuous_logstd_init=0.;config.continuous_logstd_min=-20.;config.continuous_logstd_max=2.
    config.policy_interruption_mode='off' if arm=='SET' else 'd2'
    config.interruption_delta=1;config.interruption_cost_c=float('inf');config.interruption_cost_c_Z=float('inf')
    config.skill_cap_k_max=config.team_cap_k_Z=10;config.age_feature='off'
    config.use_obsnorm=config.use_statenorm=config.use_lr_decay=config.use_entropy_annealing=False
    config.n_Z=config.n_z=6;config.ppo_epochs=15;config.sequence_batch_size=32;config.coordinator_batch_size=1280
    config.total_timesteps=360000;config.update_env_dims(state_dim=154,obs_dim=211,n_agents=6)
    config=apply_algorithm_config(config,'mappo' if arm=='SET' else 'hmasd')
    config.k=10;config.use_central_snapshot_in_flat_actor=arm=='SET';config.contract_arm='SET' if arm=='SET' else 'H'
    config.disable_discriminator_rewards=arm!='H';config.disable_discriminator_training=arm=='SET'
    config.calculate_and_set_buffer_sizes();config.discriminator_batch_size=config.batch_size
    if lanes==16 and config.discriminator_batch_size!=12000:raise AssertionError('original classifier batch12000')
    config.validate_config()
    if (config.obs_dim,config.state_dim,config.n_agents)!=(211,154,6):raise AssertionError('registered input dimensions')
    return config


def config_dict(config):return original_config_dict(config)


def initial_alias_configs(H,noD):
    a,b=config_dict(H),config_dict(noD)
    differing={key for key in a if a[key]!=b[key]}
    if differing!={'disable_discriminator_rewards'} or a['disable_discriminator_training'] or b['disable_discriminator_training']:
        raise AssertionError('noD initial configuration changes inference/classifier ownership')
    return {'only_difference':'disable_discriminator_rewards','H':a,'H-noD':b,
            'source_proof':'flag controls store_transition_batch intrinsic reward; use_discriminator_path remains true and step inference is unchanged'}
