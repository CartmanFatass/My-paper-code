import os
import time
import numpy as np
import torch
import argparse
import logging

# 修复多进程环境中的matplotlib线程安全问题
import matplotlib
matplotlib.use('Agg')  # 使用非GUI后端，避免tkinter冲突
import matplotlib.pyplot as plt

from datetime import datetime
import multiprocessing as mp
import pandas as pd
from collections import defaultdict, deque
from logger import init_multiproc_logging, get_logger, shutdown_logging, LOG_LEVELS, set_log_level

# 导入 Stable Baselines3 的向量化环境
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.env_util import make_vec_env

# 导入HMALS的配置和代理
from hmalsd.config import Config
from hmalsd.agent import HMALSAgent
from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv
from envs.pettingzoo.scenario3 import UAVMultiHopEnv
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter

# 初始化默认的主logger，供模块级别导入使用
main_logger = get_logger("HMALS-Main")

class EnhancedRewardTracker:
    """增强的奖励追踪器，用于HMALS数据收集"""
    
    def __init__(self, log_dir, config, n_users=None):
        self.log_dir = log_dir
        self.config = config
        self.n_users = n_users
        
        self.training_rewards = {
            'episode_rewards': [],
            'step_rewards': [],
            'env_rewards': [],
            'intrinsic_rewards': [],
            'reward_components': {
                'env_component': [],
                'ind_disc_component': []
            },
            'cumulative_rewards': [],
            'reward_variance': [],
            'episodes_completed': 0,
            'total_steps': 0
        }
        
        self.skill_usage = {
            'louvain_skills': defaultdict(lambda: defaultdict(int)), # level -> skill_id -> count
            'agent_skills': defaultdict(lambda: defaultdict(int)),
            'skill_switches': 0,
            'skill_diversity_history': [],
        }
        
        self.performance_metrics = {
            'episode_lengths': [],
            'served_users': [],
            'total_throughput': [],
            'avg_throughput_per_user': [],
        }
        
        self.window_size = 100
        self.recent_rewards = deque(maxlen=self.window_size)
        self.recent_lengths = deque(maxlen=self.window_size)
        
        self.export_interval = 1000
        self.last_export_step = 0
        
    def log_training_step(self, step, env_id, reward, info=None):
        """记录训练步骤的奖励信息"""
        self.training_rewards['total_steps'] += 1
        self.training_rewards['step_rewards'].append({
            'step': step,
            'env_id': env_id,
            'reward': reward,
            'timestamp': time.time()
        })
        
        if info:
            if 'reward_info' in info and 'connected_users' in info['reward_info']:
                served_users = info['reward_info']['connected_users']
                self.performance_metrics['served_users'].append({
                    'step': step,
                    'env_id': env_id,
                    'served_users': served_users,
                    'total_users': self.n_users
                })

            if 'reward_info' in info:
                reward_info = info['reward_info']
                if 'system_throughput_mbps' in reward_info:
                    self.performance_metrics['total_throughput'].append({
                        'step': step,
                        'env_id': env_id,
                        'system_throughput_mbps': reward_info['system_throughput_mbps']
                    })
    
    def log_episode_completion(self, episode_num, env_id, total_reward, episode_length, info=None):
        """记录episode完成信息"""
        self.training_rewards['episodes_completed'] += 1
        
        episode_data = {
            'episode': episode_num,
            'env_id': env_id,
            'total_reward': total_reward,
            'episode_length': episode_length,
            'timestamp': time.time()
        }
        
        if info:
            episode_data.update(info)
        
        self.training_rewards['episode_rewards'].append(episode_data)
        self.recent_rewards.append(total_reward)
        self.recent_lengths.append(episode_length)
        
    def log_skill_usage(self, step, active_skill_path, agent_skills, skill_changed=False):
        """记录技能使用情况"""
        if skill_changed:
            self.skill_usage['skill_switches'] += 1

        if active_skill_path:
            for level, skill_id in enumerate(active_skill_path):
                self.skill_usage['louvain_skills'][level][skill_id] += 1

        for i, skill in enumerate(agent_skills):
            self.skill_usage['agent_skills'][i][skill] += 1
        
        unique_skills = len(set(agent_skills))
        diversity = unique_skills / len(agent_skills) if len(agent_skills) > 0 else 0
        self.skill_usage['skill_diversity_history'].append({
            'step': step,
            'diversity': diversity
        })

    def export_training_data(self, step, writer=None):
        """导出训练数据"""
        if step - self.last_export_step < self.export_interval:
            return    
        
        export_dir = os.path.join(self.log_dir, 'paper_data')
        os.makedirs(export_dir, exist_ok=True)
        
        if self.training_rewards['episode_rewards']:
            rewards_df = pd.DataFrame(self.training_rewards['episode_rewards'])
            rewards_df.to_csv(os.path.join(export_dir, f'episode_rewards_step_{step}.csv'), index=False)
        
        main_logger.debug(f"已导出步骤 {step} 的训练数据到 {export_dir}")
        self.last_export_step = step

    def log_to_tensorboard(self, writer, step):
        """记录详细数据到TensorBoard"""
        if self.recent_rewards:
            writer.add_scalar('Training/Reward_Mean_100ep', np.mean(self.recent_rewards), step)
        if self.recent_lengths:
            writer.add_scalar('Training/EpisodeLength_Mean_100ep', np.mean(self.recent_lengths), step)
        if self.skill_usage['skill_diversity_history']:
            avg_diversity = np.mean([d['diversity'] for d in self.skill_usage['skill_diversity_history'][-100:]])
            writer.add_scalar('Training/Skill_Diversity_Recent', avg_diversity, step)

def get_device(device_pref):
    """根据偏好选择计算设备"""
    if device_pref == 'auto':
        return torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    return torch.device(device_pref)

def make_env(scenario, n_uavs, n_users, user_distribution, channel_model, config=None, max_hops=None, render_mode=None, rank=0, seed=0, **kwargs):
    """创建环境实例的函数"""
    def _init():
        env_seed = seed + rank
        env_kwargs = {
            'n_uavs': n_uavs,
            'n_users': n_users,
            'user_distribution': user_distribution,
            'channel_model': channel_model,
            'render_mode': render_mode,
            'seed': env_seed,
            **kwargs
        }
        
        if scenario == 1:
            raw_env = UAVBaseStationEnv(**env_kwargs)
        elif scenario == 2:
            raw_env = UAVCooperativeNetworkEnv(max_hops=max_hops, **env_kwargs)
        elif scenario == 3:
            raw_env = UAVMultiHopEnv(max_hops=max_hops, **env_kwargs)
        else:
            raise ValueError(f"未知的场景: {scenario}")

        env = ParallelToArrayAdapter(raw_env, seed=env_seed)
        return env
    return _init

def parse_args():
    parser = argparse.ArgumentParser(description='运行HMALS算法训练')
    parser.add_argument('--mode', type=str, default='train', help='运行模式: train或eval')
    parser.add_argument('--scenario', type=int, default=3, help='场景: 1, 2, or 3')
    parser.add_argument('--model_path', type=str, default='models/hmals_model.pt', help='模型保存/加载路径')
    parser.add_argument('--log_dir', type=str, default='logs', help='日志目录')
    parser.add_argument('--log_level', type=str, default='info', choices=['debug', 'info', 'warning', 'error', 'critical'])
    parser.add_argument('--console_log_level', type=str, default='info', choices=['debug', 'info', 'warning', 'error', 'critical'])
    parser.add_argument('--device', type=str, default='auto', choices=['auto', 'cuda', 'cpu'])
    parser.add_argument('--num_envs', type=int, default=16, help='并行环境数量')
    parser.add_argument('--total_timesteps', type=int, default=5e6, help='总训练步数')
    parser.add_argument('--n_uavs', type=int, default=10, help='无人机数量')
    parser.add_argument('--n_users', type=int, default=50, help='用户数量')
    parser.add_argument('--user_distribution', type=str, default='multi_cluster', choices=['uniform', 'cluster', 'hotspot', 'multi_cluster'])
    parser.add_argument('--channel_model', type=str, default='3gpp-36777', choices=['free_space', 'urban', 'suburban', '3gpp-36777'])
    parser.add_argument('--max_hops', type=int, default=5, help='最大跳数')
    parser.add_argument('--area_size', type=int, default=3000, help='区域大小 (米)')
    parser.add_argument('--n_clusters', type=int, default=5, help='用户簇数量')
    parser.add_argument('--cluster_std', type=int, default=150, help='簇内用户分布标准差')
    return parser.parse_args()

def train(vec_env, config, args, device):
    main_logger.info(f"开始训练HMALS，使用 {args.num_envs} 个并行环境...")
    log_dir = os.path.join(args.log_dir, f"hmals_{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(log_dir, exist_ok=True)
    
    agent = HMALSAgent(config, log_dir=log_dir, device=device)
    reward_tracker = EnhancedRewardTracker(log_dir, config, n_users=args.n_users)
    
    total_steps = 0
    n_episodes = 0
    start_time = time.time()

    results = vec_env.env_method('reset')
    observations = np.array([res[0] for res in results])
    initial_infos = [r[1] for r in results]
    states = np.array([info.get('state', np.zeros(agent.config.state_dim)) for info in initial_infos])

    env_steps = np.zeros(args.num_envs, dtype=int)
    env_rewards = np.zeros(args.num_envs)

    while total_steps < args.total_timesteps:
        all_actions_list = []
        all_agent_infos_list = []

        for i in range(args.num_envs):
            actions, agent_info = agent.step(states[i], observations[i], env_steps[i], deterministic=False, env_id=i)
            all_actions_list.append(actions)
            all_agent_infos_list.append(agent_info)

        actions_array = np.array(all_actions_list)
        next_observations, rewards, dones, infos = vec_env.step(actions_array)
        next_states = np.array([info.get('next_state', np.zeros(config.state_dim)) for info in infos])

        for i in range(args.num_envs):
            current_agent_info = all_agent_infos_list[i]
            agent.store_transition(
                states[i], next_states[i], observations[i], next_observations[i],
                actions_array[i], rewards[i], dones[i], 
                current_agent_info['team_skill'],
                current_agent_info['agent_skills'], 
                current_agent_info['action_logprobs'],
                log_probs=current_agent_info['log_probs'],
                skill_timer_for_env=current_agent_info['skill_timer'],
                env_id=i,
                active_skill_path=current_agent_info['active_skill_path']
            )
            
            reward_tracker.log_training_step(total_steps + i, i, rewards[i], infos[i])
            reward_tracker.log_skill_usage(total_steps + i, current_agent_info['active_skill_path'], current_agent_info['agent_skills'], current_agent_info['skill_changed'])

            env_steps[i] += 1
            env_rewards[i] += rewards[i]

            if dones[i]:
                n_episodes += 1
                reward_tracker.log_episode_completion(n_episodes, i, env_rewards[i], env_steps[i], infos[i])
                main_logger.info(f"Episode {n_episodes}: Env {i}, Reward: {env_rewards[i]:.2f}, Length: {env_steps[i]}")
                env_steps[i] = 0
                env_rewards[i] = 0

        states = next_states
        observations = next_observations
        total_steps += args.num_envs

        if len(agent.low_level_buffer) >= agent.config.batch_size:
            update_info = agent.update()
            if update_info:
                reward_tracker.log_to_tensorboard(agent.writer, total_steps)

        if total_steps % 10000 == 0:
            agent.save_model(args.model_path)
            reward_tracker.export_training_data(total_steps)
            main_logger.info(f"模型已保存，步数: {total_steps}")

    main_logger.info("训练完成!")
    agent.save_model(args.model_path)
    vec_env.close()

def main():
    args = parse_args()
    init_multiproc_logging(log_dir=args.log_dir, log_file=f"hmals_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", file_level=LOG_LEVELS[args.log_level], console_level=LOG_LEVELS[args.console_log_level])
    
    config = Config()
    config.n_agents = args.n_uavs
    
    device = get_device(args.device)
    
    env_kwargs = {
        'n_uavs': args.n_uavs,
        'n_users': args.n_users,
        'user_distribution': args.user_distribution,
        'channel_model': args.channel_model,
        'max_hops': args.max_hops,
        'area_size': args.area_size,
        'n_clusters': args.n_clusters,
        'cluster_std': args.cluster_std,
    }

    env_fns = [make_env(scenario=args.scenario, config=config, rank=i, seed=int(time.time()) + i, **env_kwargs) for i in range(args.num_envs)]
    
    temp_env = env_fns[0]()
    config.update_env_dims(temp_env.state_dim, temp_env.obs_dim)
    temp_env.close()

    vec_env = SubprocVecEnv(env_fns, start_method='spawn')

    if args.mode == 'train':
        train(vec_env, config, args, device)
    else:
        # 评估逻辑（此处省略）
        main_logger.info("评估模式待实现")

    shutdown_logging()

if __name__ == "__main__":
    mp.set_start_method('spawn', force=True)
    main()
