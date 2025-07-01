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
# from functools import partial # No longer needed for make_env directly
from logger import init_multiproc_logging, get_logger, shutdown_logging, LOG_LEVELS, set_log_level

# 导入 Stable Baselines3 的向量化环境
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.env_util import make_vec_env # Can also use this helper

# 导入论文中的配置
from config_1 import Config
from hmasd.agent import HMASDAgent
from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv
from envs.pettingzoo.scenario3 import UAVMultiHopEnv
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter

# Removed VectorizedEnvAdapter class

class EnhancedRewardTracker:
    """增强的奖励追踪器，用于论文数据收集"""
    
    def __init__(self, log_dir, config, n_users=None):
        self.log_dir = log_dir
        self.config = config
        self.n_users = n_users  # 存储用户总数，用于准确计算服务率
        
        # 训练过程中的奖励数据收集
        self.training_rewards = {
            'episode_rewards': [],
            'step_rewards': [],
            'env_rewards': [],
            'intrinsic_rewards': [],
            'reward_components': {
                'env_component': [],
                'team_disc_component': [],
                'ind_disc_component': []
            },
            'cumulative_rewards': [],
            'reward_variance': [],
            'episodes_completed': 0,
            'total_steps': 0
        }
        
        # 技能使用统计
        self.skill_usage = {
            'team_skills': defaultdict(int),
            'agent_skills': defaultdict(lambda: defaultdict(int)),
            'skill_switches': 0,
            'skill_diversity_history': [],
            'episode_skill_counts': []
        }
        
        # 性能指标
        self.performance_metrics = {
            'episode_lengths': [],
            'success_rates': [],
            'coverage_ratios': [],
            'served_users': [],
            'network_efficiency': [],
            'total_throughput': [],  # 新增：总吞吐量记录
            'avg_throughput_per_user': [],  # 新增：平均用户吞吐量记录
            
            # 奖励组成部分记录 (场景2和场景3通用)
            'reward_components': {
                # 通用奖励组成
                'throughput_rewards': [],  # 吞吐量奖励 (场景2和3都有)
                'coverage_rewards': [],    # 覆盖率奖励 (场景2有)
                
                # 场景3特有的奖励组成
                'effective_coverage_rewards': [],    # 有效覆盖率奖励
                'load_balance_rewards': [],          # 负载均衡奖励
                'network_connectivity_rewards': [],  # 网络连通性奖励
                
                # 其他指标
                'avg_hops': [],           # 平均跳数
                'connected_users': [],    # 连接用户数
                'coverage_ratios': []     # 覆盖率比例
            }
        }
        
        # 滑动窗口统计
        self.window_size = 100
        self.recent_rewards = deque(maxlen=self.window_size)
        self.recent_lengths = deque(maxlen=self.window_size)
        
        # 数据导出设置
        self.export_interval = 1000  # 每1000步导出一次数据
        self.last_export_step = 0
        
    def log_training_step(self, step, env_id, reward, reward_components=None, info=None):
        """记录训练步骤的奖励信息"""
        self.training_rewards['total_steps'] += 1
        self.training_rewards['step_rewards'].append({
            'step': step,
            'env_id': env_id,
            'reward': reward,
            'timestamp': time.time()
        })
        
        if reward_components:
            for comp_name, comp_value in reward_components.items():
                if comp_name in self.training_rewards['reward_components']:
                    self.training_rewards['reward_components'][comp_name].append({
                        'step': step,
                        'env_id': env_id,
                        'value': comp_value
                    })
        
        # 记录额外信息（简化后只记录served_users）
        if info:
            served_users = 0
            
            # 从多个来源获取服务用户数
            if 'reward_info' in info and 'connected_users' in info['reward_info']:
                served_users = info['reward_info']['connected_users']
            elif 'coverage_ratio' in info and self.n_users is not None:
                # 从覆盖率计算服务用户数，使用固定的n_users
                served_users = int(info['coverage_ratio'] * self.n_users)
            elif 'coverage_ratio' in info and 'n_users' in info:
                # 备用方案：从info中获取n_users
                served_users = int(info['coverage_ratio'] * info['n_users'])
            elif 'served_users' in info:
                # 兼容原有字段名
                served_users = info['served_users']
            
            # 如果获取到了服务用户信息，记录到性能指标
            if served_users > 0:
                self.performance_metrics['served_users'].append({
                    'step': step,
                    'env_id': env_id,
                    'served_users': served_users,
                    'total_users': self.n_users  # 使用固定的n_users
                })
            
            # 记录吞吐量信息（修正后的字段名）
            if 'reward_info' in info:
                reward_info = info['reward_info']
                if 'system_throughput_mbps' in reward_info:
                    self.performance_metrics['total_throughput'].append({
                        'step': step,
                        'env_id': env_id,
                        'system_throughput_mbps': reward_info['system_throughput_mbps'],
                        'timestamp': time.time()
                    })
                
                if 'avg_throughput_per_user_mbps' in reward_info:
                    self.performance_metrics['avg_throughput_per_user'].append({
                        'step': step,
                        'env_id': env_id,
                        'avg_throughput_per_user_mbps': reward_info['avg_throughput_per_user_mbps'],
                        'timestamp': time.time()
                    })
                
                # 记录奖励组成部分 (场景2和场景3通用)
                # 通用指标
                if 'throughput_reward' in reward_info:
                    self.performance_metrics['reward_components']['throughput_rewards'].append({
                        'step': step,
                        'env_id': env_id,
                        'value': reward_info['throughput_reward'],
                        'timestamp': time.time()
                    })
                
                if 'coverage_reward' in reward_info:
                    self.performance_metrics['reward_components']['coverage_rewards'].append({
                        'step': step,
                        'env_id': env_id,
                        'value': reward_info['coverage_reward'],
                        'timestamp': time.time()
                    })
                
                # 场景3特有指标
                if 'effective_coverage_reward' in reward_info:
                    self.performance_metrics['reward_components']['effective_coverage_rewards'].append({
                        'step': step,
                        'env_id': env_id,
                        'value': reward_info['effective_coverage_reward'],
                        'timestamp': time.time()
                    })
                
                if 'load_balance_reward' in reward_info:
                    self.performance_metrics['reward_components']['load_balance_rewards'].append({
                        'step': step,
                        'env_id': env_id,
                        'value': reward_info['load_balance_reward'],
                        'timestamp': time.time()
                    })
                
                if 'network_connectivity_reward' in reward_info:
                    self.performance_metrics['reward_components']['network_connectivity_rewards'].append({
                        'step': step,
                        'env_id': env_id,
                        'value': reward_info['network_connectivity_reward'],
                        'timestamp': time.time()
                    })
                
                # 其他有用指标
                if 'avg_hops' in reward_info:
                    self.performance_metrics['reward_components']['avg_hops'].append({
                        'step': step,
                        'env_id': env_id,
                        'value': reward_info['avg_hops'],
                        'timestamp': time.time()
                    })
                
                if 'connected_users' in reward_info:
                    self.performance_metrics['reward_components']['connected_users'].append({
                        'step': step,
                        'env_id': env_id,
                        'value': reward_info['connected_users'],
                        'timestamp': time.time()
                    })
                
                if 'coverage_ratio' in reward_info:
                    self.performance_metrics['reward_components']['coverage_ratios'].append({
                        'step': step,
                        'env_id': env_id,
                        'value': reward_info['coverage_ratio'],
                        'timestamp': time.time()
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
        
        # 计算滑动窗口统计
        if len(self.recent_rewards) >= 10:
            self.training_rewards['reward_variance'].append({
                'episode': episode_num,
                'mean': np.mean(self.recent_rewards),
                'std': np.std(self.recent_rewards),
                'min': np.min(self.recent_rewards),
                'max': np.max(self.recent_rewards)
            })
    
    def log_skill_usage(self, step, team_skill, agent_skills, skill_changed=False):
        """记录技能使用情况"""
        self.skill_usage['team_skills'][team_skill] += 1
        
        for i, skill in enumerate(agent_skills):
            self.skill_usage['agent_skills'][i][skill] += 1
        
        if skill_changed:
            self.skill_usage['skill_switches'] += 1
        
        # 计算技能多样性
        unique_skills = len(set(agent_skills))
        diversity = unique_skills / len(agent_skills) if len(agent_skills) > 0 else 0
        self.skill_usage['skill_diversity_history'].append({
            'step': step,
            'diversity': diversity,
            'unique_skills': unique_skills,
            'total_agents': len(agent_skills)
        })
    
    def export_training_data(self, step, writer=None):
        """导出训练数据用于论文分析"""
        if step - self.last_export_step < self.export_interval:
            return    
        
        export_dir = os.path.join(self.log_dir, 'paper_data')
        os.makedirs(export_dir, exist_ok=True)
        
        # 导出奖励数据
        if self.training_rewards['episode_rewards']:
            rewards_df = pd.DataFrame(self.training_rewards['episode_rewards'])
            rewards_df.to_csv(os.path.join(export_dir, f'episode_rewards_step_{step}.csv'), index=False)
        
        # 导出奖励组成分析
        components_data = []
        for comp_name, comp_list in self.training_rewards['reward_components'].items():
            for entry in comp_list:
                components_data.append({
                    'step': entry['step'],
                    'env_id': entry['env_id'],
                    'component': comp_name,
                    'value': entry['value']
                })
        
        if components_data:
            components_df = pd.DataFrame(components_data)
            components_df.to_csv(os.path.join(export_dir, f'reward_components_step_{step}.csv'), index=False)
        
        # 导出技能使用统计
        skill_stats = {
            'team_skills': dict(self.skill_usage['team_skills']),
            'skill_switches': self.skill_usage['skill_switches'],
            'total_steps': step
        }
        
        import json
        with open(os.path.join(export_dir, f'skill_usage_step_{step}.json'), 'w') as f:
            json.dump(skill_stats, f, indent=2)
        
        # 生成训练曲线图 - 已禁用以避免内存错误
        # self.generate_training_plots(export_dir, step)
        main_logger.debug(f"跳过训练过程中的绘图生成 (步骤 {step}) 以避免内存问题")
        
        # 记录到TensorBoard（如果提供）
        if writer:
            self.log_to_tensorboard(writer, step)
        
        self.last_export_step = step
        main_logger.debug(f"已导出步骤 {step} 的训练数据到 {export_dir}")
    
    def generate_training_plots(self, export_dir, step):
        """生成训练过程的可视化图表"""
        
        # 1. Episode奖励趋势图
        if self.training_rewards['episode_rewards']:
            episodes = [r['episode'] for r in self.training_rewards['episode_rewards']]
            rewards = [r['total_reward'] for r in self.training_rewards['episode_rewards']]
            
            plt.figure(figsize=(12, 8))
            
            # 原始奖励曲线
            plt.subplot(2, 2, 1)
            plt.plot(episodes, rewards, alpha=0.3, color='blue', label='Episode Rewards')
            # 滑动平均
            if len(rewards) >= 10:
                window = 50
                if len(rewards) >= window:
                    smoothed = pd.Series(rewards).rolling(window=window, center=True).mean()
                    plt.plot(episodes, smoothed, color='red', linewidth=2, label=f'{window}-episode MA')
            plt.xlabel('Episode')
            plt.ylabel('Total Reward')
            plt.title('Training Reward Progress')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # 奖励分布直方图
            plt.subplot(2, 2, 2)
            plt.hist(rewards, bins=50, alpha=0.7, color='green')
            plt.xlabel('Total Reward')
            plt.ylabel('Frequency')
            plt.title('Reward Distribution')
            plt.grid(True, alpha=0.3)
            
            # Episode长度趋势
            if self.performance_metrics['episode_lengths'] or len(episodes) == len([r['episode_length'] for r in self.training_rewards['episode_rewards']]):
                lengths = [r['episode_length'] for r in self.training_rewards['episode_rewards']]
                plt.subplot(2, 2, 3)
                plt.plot(episodes, lengths, alpha=0.6, color='orange')
                plt.xlabel('Episode')
                plt.ylabel('Episode Length')
                plt.title('Episode Length Progression')
                plt.grid(True, alpha=0.3)
            
            # 奖励方差趋势
            if self.training_rewards['reward_variance']:
                var_episodes = [v['episode'] for v in self.training_rewards['reward_variance']]
                var_means = [v['mean'] for v in self.training_rewards['reward_variance']]
                var_stds = [v['std'] for v in self.training_rewards['reward_variance']]
                
                plt.subplot(2, 2, 4)
                plt.errorbar(var_episodes, var_means, yerr=var_stds, alpha=0.7, color='purple')
                plt.xlabel('Episode')
                plt.ylabel('Mean Reward ± Std')
                plt.title('Reward Stability (100-episode window)')
                plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(os.path.join(export_dir, f'training_progress_step_{step}.png'), dpi=300, bbox_inches='tight')
            plt.close()
        
        # 2. 奖励组成分析图
        if any(self.training_rewards['reward_components'].values()):
            plt.figure(figsize=(15, 5))
            
            components = ['env_component', 'team_disc_component', 'ind_disc_component']
            colors = ['blue', 'red', 'green']
            
            for i, (comp_name, color) in enumerate(zip(components, colors)):
                if comp_name in self.training_rewards['reward_components'] and self.training_rewards['reward_components'][comp_name]:
                    comp_data = self.training_rewards['reward_components'][comp_name]
                    steps = [d['step'] for d in comp_data]
                    values = [d['value'] for d in comp_data]
                    
                    plt.subplot(1, 3, i+1)
                    plt.plot(steps, values, alpha=0.6, color=color)
                    plt.xlabel('Training Step')
                    plt.ylabel('Reward Component Value')
                    plt.title(f'{comp_name.replace("_", " ").title()}')
                    plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(os.path.join(export_dir, f'reward_components_step_{step}.png'), dpi=300, bbox_inches='tight')
            plt.close()
        
        # 3. 技能使用分析图
        if self.skill_usage['skill_diversity_history']:
            plt.figure(figsize=(12, 4))
            
            diversity_data = self.skill_usage['skill_diversity_history']
            steps = [d['step'] for d in diversity_data]
            diversity_values = [d['diversity'] for d in diversity_data]
            
            plt.subplot(1, 2, 1)
            plt.plot(steps, diversity_values, alpha=0.7, color='purple')
            plt.xlabel('Training Step')
            plt.ylabel('Skill Diversity')
            plt.title('Agent Skill Diversity Over Time')
            plt.grid(True, alpha=0.3)
            
            # 团队技能使用分布
            if self.skill_usage['team_skills']:
                plt.subplot(1, 2, 2)
                skills = list(self.skill_usage['team_skills'].keys())
                counts = list(self.skill_usage['team_skills'].values())
                plt.bar(skills, counts, alpha=0.7, color='orange')
                plt.xlabel('Team Skill ID')
                plt.ylabel('Usage Count')
                plt.title('Team Skill Usage Distribution')
                plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(os.path.join(export_dir, f'skill_analysis_step_{step}.png'), dpi=300, bbox_inches='tight')
            plt.close()
    
    def log_to_tensorboard(self, writer, step):
        """记录详细数据到TensorBoard"""
        
        # 训练奖励统计
        if self.recent_rewards:
            writer.add_scalar('Training/Reward_Mean_100ep', np.mean(self.recent_rewards), step)
            writer.add_scalar('Training/Reward_Std_100ep', np.std(self.recent_rewards), step)
            writer.add_scalar('Training/Reward_Min_100ep', np.min(self.recent_rewards), step)
            writer.add_scalar('Training/Reward_Max_100ep', np.max(self.recent_rewards), step)
        
        if self.recent_lengths:
            writer.add_scalar('Training/EpisodeLength_Mean_100ep', np.mean(self.recent_lengths), step)
        
        # 技能多样性
        if self.skill_usage['skill_diversity_history']:
            recent_diversity = self.skill_usage['skill_diversity_history'][-10:]  # 最近10次
            avg_diversity = np.mean([d['diversity'] for d in recent_diversity])
            writer.add_scalar('Training/Skill_Diversity_Recent', avg_diversity, step)
        
        # 技能使用分布熵
        if self.skill_usage['team_skills']:
            total_usage = sum(self.skill_usage['team_skills'].values())
            skill_probs = [count/total_usage for count in self.skill_usage['team_skills'].values()]
            skill_entropy = -sum(p * np.log(p + 1e-8) for p in skill_probs)
            writer.add_scalar('Training/Team_Skill_Entropy', skill_entropy, step)
        
        # 训练效率指标
        writer.add_scalar('Training/Episodes_Completed', self.training_rewards['episodes_completed'], step)
        writer.add_scalar('Training/Skill_Switches_Total', self.skill_usage['skill_switches'], step)
        
        # 奖励组成比例
        if any(self.training_rewards['reward_components'].values()):
            recent_components = {}
            for comp_name, comp_list in self.training_rewards['reward_components'].items():
                if comp_list:
                    recent_data = comp_list[-100:]  # 最近100个数据点
                    recent_components[comp_name] = np.mean([d['value'] for d in recent_data])
            
            total_intrinsic = sum(recent_components.values())
            if total_intrinsic != 0:
                for comp_name, comp_value in recent_components.items():
                    proportion = comp_value / total_intrinsic
                    writer.add_scalar(f'Training/Reward_Proportion_{comp_name}', proportion, step)
        
        # Throughput统计（修正后使用n_users）
        if self.performance_metrics['served_users'] and self.n_users is not None:
            # 计算最近100步的滑动窗口平均吞吐量
            recent_served_data = self.performance_metrics['served_users'][-100:]
            recent_served_users = [u['served_users'] for u in recent_served_data]
            recent_total_users = [u['total_users'] for u in recent_served_data]
            
            if recent_served_users:
                # 平均服务用户数
                avg_served_users = np.mean(recent_served_users)
                writer.add_scalar('Performance/Throughput_ServedUsers_100steps', avg_served_users, step)
                
                # 平均总用户数（记录但不用于计算服务率）
                avg_total_users = np.mean(recent_total_users)
                writer.add_scalar('Performance/Throughput_TotalUsers_100steps', avg_total_users, step)
                
                # 服务率（吞吐率）- 使用固定的n_users作为分母
                service_rate = avg_served_users / self.n_users
                writer.add_scalar('Performance/Throughput_ServiceRate_100steps', service_rate, step)
                
                # 计算吞吐率变化趋势（最近50步 vs 前50步）
                if len(recent_served_data) >= 100:
                    first_half = recent_served_data[:50]
                    second_half = recent_served_data[50:]
                    
                    first_half_rate = np.mean([u['served_users'] for u in first_half]) / max(np.mean([u['total_users'] for u in first_half]), 1)
                    second_half_rate = np.mean([u['served_users'] for u in second_half]) / max(np.mean([u['total_users'] for u in second_half]), 1)
                    
                    throughput_trend = second_half_rate - first_half_rate
                    writer.add_scalar('Performance/Throughput_Trend_100steps', throughput_trend, step)
            
            # 按环境分别统计吞吐量
            env_throughputs = defaultdict(list)
            env_total_users = defaultdict(list)
            for entry in recent_served_data:
                env_throughputs[entry['env_id']].append(entry['served_users'])
                env_total_users[entry['env_id']].append(entry['total_users'])
            
            for env_id in env_throughputs.keys():
                served_values = env_throughputs[env_id]
                total_values = env_total_users[env_id]
                
                if served_values:
                    env_avg_served = np.mean(served_values)
                    env_avg_total = np.mean(total_values)
                    env_service_rate = env_avg_served / max(env_avg_total, 1)
                    
                    writer.add_scalar(f'Performance/Env_{env_id}_ServedUsers', env_avg_served, step)
                    writer.add_scalar(f'Performance/Env_{env_id}_ServiceRate', env_service_rate, step)
            
            # 吞吐量方差（稳定性指标）
            if len(recent_served_users) > 1:
                throughput_std = np.std(recent_served_users)
                throughput_cv = throughput_std / max(np.mean(recent_served_users), 1e-8)  # 变异系数
                writer.add_scalar('Performance/Throughput_Std_100steps', throughput_std, step)
                writer.add_scalar('Performance/Throughput_CV_100steps', throughput_cv, step)
        
        # 系统吞吐量统计（修正后）
        if self.performance_metrics['total_throughput']:
            # 计算最近100步的系统吞吐量统计
            recent_throughput_data = self.performance_metrics['total_throughput'][-100:]
            recent_system_throughput = [t['system_throughput_mbps'] for t in recent_throughput_data if 'system_throughput_mbps' in t]
            
            if recent_system_throughput:
                # 平均系统吞吐量
                avg_system_throughput = np.mean(recent_system_throughput)
                writer.add_scalar('Performance/System_Throughput_Mbps_100steps', avg_system_throughput, step)
                
                # 系统吞吐量标准差
                throughput_std = np.std(recent_system_throughput)
                writer.add_scalar('Performance/System_Throughput_Std_100steps', throughput_std, step)
                
                # 系统吞吐量最大值和最小值
                writer.add_scalar('Performance/System_Throughput_Max_100steps', np.max(recent_system_throughput), step)
                writer.add_scalar('Performance/System_Throughput_Min_100steps', np.min(recent_system_throughput), step)
                
                # 按环境分别统计系统吞吐量
                env_system_throughputs = defaultdict(list)
                for entry in recent_throughput_data:
                    if 'system_throughput_mbps' in entry:
                        env_system_throughputs[entry['env_id']].append(entry['system_throughput_mbps'])
                
                for env_id, throughput_values in env_system_throughputs.items():
                    if throughput_values:
                        env_avg_throughput = np.mean(throughput_values)
                        writer.add_scalar(f'Performance/Env_{env_id}_System_Throughput_Mbps', env_avg_throughput, step)
        
        # 平均用户吞吐量统计（新增）
        if self.performance_metrics['avg_throughput_per_user']:
            # 计算最近100步的平均用户吞吐量统计
            recent_avg_throughput_data = self.performance_metrics['avg_throughput_per_user'][-100:]
            recent_avg_throughput = [t['avg_throughput_per_user_mbps'] for t in recent_avg_throughput_data]
            
            if recent_avg_throughput:
                # 平均用户吞吐量
                avg_user_throughput = np.mean(recent_avg_throughput)
                writer.add_scalar('Performance/Avg_User_Throughput_Mbps_100steps', avg_user_throughput, step)
                
                # 平均用户吞吐量标准差
                user_throughput_std = np.std(recent_avg_throughput)
                writer.add_scalar('Performance/Avg_User_Throughput_Std_100steps', user_throughput_std, step)
                
                # 按环境分别统计平均用户吞吐量
                env_avg_user_throughputs = defaultdict(list)
                for entry in recent_avg_throughput_data:
                    env_avg_user_throughputs[entry['env_id']].append(entry['avg_throughput_per_user_mbps'])
                
                for env_id, throughput_values in env_avg_user_throughputs.items():
                    if throughput_values:
                        env_avg_user_throughput = np.mean(throughput_values)
                        writer.add_scalar(f'Performance/Env_{env_id}_Avg_User_Throughput_Mbps', env_avg_user_throughput, step)
        
        # 记录环境奖励组成部分到TensorBoard (场景2和场景3通用)
        reward_components = self.performance_metrics['reward_components']
        
        # 通用奖励组成
        if reward_components['throughput_rewards']:
            recent_throughput_rewards = reward_components['throughput_rewards'][-100:]
            if recent_throughput_rewards:
                avg_throughput_reward = np.mean([r['value'] for r in recent_throughput_rewards])
                writer.add_scalar('Reward_Components/Throughput_Reward_100steps', avg_throughput_reward, step)
        
        if reward_components['coverage_rewards']:
            recent_coverage_rewards = reward_components['coverage_rewards'][-100:]
            if recent_coverage_rewards:
                avg_coverage_reward = np.mean([r['value'] for r in recent_coverage_rewards])
                writer.add_scalar('Reward_Components/Coverage_Reward_100steps', avg_coverage_reward, step)
        
        # 场景3特有奖励组成
        if reward_components['effective_coverage_rewards']:
            recent_effective_coverage = reward_components['effective_coverage_rewards'][-100:]
            if recent_effective_coverage:
                avg_effective_coverage = np.mean([r['value'] for r in recent_effective_coverage])
                writer.add_scalar('Reward_Components/Effective_Coverage_Reward_100steps', avg_effective_coverage, step)
        
        if reward_components['load_balance_rewards']:
            recent_load_balance = reward_components['load_balance_rewards'][-100:]
            if recent_load_balance:
                avg_load_balance = np.mean([r['value'] for r in recent_load_balance])
                writer.add_scalar('Reward_Components/Load_Balance_Reward_100steps', avg_load_balance, step)
        
        if reward_components['network_connectivity_rewards']:
            recent_network_connectivity = reward_components['network_connectivity_rewards'][-100:]
            if recent_network_connectivity:
                avg_network_connectivity = np.mean([r['value'] for r in recent_network_connectivity])
                writer.add_scalar('Reward_Components/Network_Connectivity_Reward_100steps', avg_network_connectivity, step)
        
        # 其他有用指标
        if reward_components['avg_hops']:
            recent_avg_hops = reward_components['avg_hops'][-100:]
            if recent_avg_hops:
                avg_hops_value = np.mean([r['value'] for r in recent_avg_hops])
                writer.add_scalar('Performance/Avg_Hops_100steps', avg_hops_value, step)
        
        if reward_components['connected_users']:
            recent_connected_users = reward_components['connected_users'][-100:]
            if recent_connected_users:
                avg_connected_users = np.mean([r['value'] for r in recent_connected_users])
                writer.add_scalar('Performance/Connected_Users_100steps', avg_connected_users, step)
        
        if reward_components['coverage_ratios']:
            recent_coverage_ratios = reward_components['coverage_ratios'][-100:]
            if recent_coverage_ratios:
                avg_coverage_ratio = np.mean([r['value'] for r in recent_coverage_ratios])
                writer.add_scalar('Performance/Coverage_Ratio_100steps', avg_coverage_ratio, step)
    
    def get_summary_statistics(self):
        """获取训练摘要统计信息"""
        summary = {
            'total_episodes': self.training_rewards['episodes_completed'],
            'total_steps': self.training_rewards['total_steps'],
            'skill_switches': self.skill_usage['skill_switches']
        }
        
        if self.training_rewards['episode_rewards']:
            rewards = [r['total_reward'] for r in self.training_rewards['episode_rewards']]
            summary.update({
                'reward_mean': np.mean(rewards),
                'reward_std': np.std(rewards),
                'reward_min': np.min(rewards),
                'reward_max': np.max(rewards)
            })
        
        if self.skill_usage['team_skills']:
            summary['team_skill_usage'] = dict(self.skill_usage['team_skills'])
        
        return summary

# 获取计算设备
def get_device(device_pref):
    """
    根据偏好选择计算设备
    
    参数:
        device_pref: 设备偏好 ('auto', 'cuda', 'cpu')
        
    返回:
        device: torch.device对象
    """
    if device_pref == 'auto':
        if torch.cuda.is_available():
            main_logger.info("检测到GPU可用，使用CUDA")
            return torch.device('cuda')
        else:
            main_logger.info("未检测到GPU，使用CPU")
            return torch.device('cpu')
    elif device_pref == 'cuda':
        if torch.cuda.is_available():
            main_logger.info("使用CUDA")
            return torch.device('cuda')
        else:
            main_logger.warning("请求使用CUDA但未检测到GPU，回退到CPU")
            return torch.device('cpu')
    else:  # 'cpu'或其他值
        main_logger.info("使用CPU")
        return torch.device('cpu')

# 创建环境函数 (修改后用于 SubprocVecEnv)
def make_env(scenario, n_uavs, n_users, user_distribution, channel_model, config=None, max_hops=None, render_mode=None, rank=0, seed=0, n_clusters=None, cluster_std=None, central_area_ratio=None, area_size=None, use_fdma=True, bandwidth=None):
    """
    创建环境实例的函数 (用于 SubprocVecEnv)

    参数:
        scenario: 场景编号 (1=基站模式, 2=协作组网模式, 3=强制多跳模式)
        n_uavs: 无人机数量
        n_users: 用户数量
        user_distribution: 用户分布类型
        channel_model: 信道模型
        config: 配置对象，包含奖励权重等参数
        max_hops: 最大跳数 (仅用于场景2和3)
        render_mode: 渲染模式
        rank: 环境的索引 (用于设置不同的种子)
        seed: 基础随机种子
        n_clusters: 用户簇数量 (仅用于场景3)
        cluster_std: 簇内用户分布标准差 (仅用于场景3)
        central_area_ratio: 中心用户区域占总区域的比例 (仅用于场景3)
        area_size: 区域大小 (仅用于场景3)
        use_fdma: 是否启用FDMA
        bandwidth: 每个无人机的带宽 (Hz)

    返回:
        一个返回环境实例的函数
    """
    def _init():
        env_seed = seed + rank # 为每个并行环境设置不同的种子
        
        # 如果未提供带宽，则使用默认值
        effective_bandwidth = bandwidth
        if effective_bandwidth is None:
            effective_bandwidth = 20e6
        
        # 准备通用环境参数
        env_kwargs = {
            'n_uavs': n_uavs,
            'n_users': n_users,
            'user_distribution': user_distribution,
            'channel_model': channel_model,
            'render_mode': render_mode,
            'seed': env_seed,
            'use_fdma': use_fdma,
            'bandwidth': effective_bandwidth
        }
        
        if scenario == 1:
            raw_env = UAVBaseStationEnv(**env_kwargs)
        elif scenario == 2:
            # 场景2不再需要传递奖励权重参数，奖励已固化为覆盖率+归一化吞吐量
            raw_env = UAVCooperativeNetworkEnv(
                max_hops=max_hops,
                **env_kwargs
            )
        elif scenario == 3:
            # 准备场景3的新奖励权重参数（如果配置可用）
            reward_kwargs = {}
            if config is not None:
                reward_kwargs.update({
                    'effective_coverage_weight': config.effective_coverage_weight,
                    'throughput_weight': config.throughput_weight,
                    'load_balance_weight': config.load_balance_weight,
                    'proximity_penalty_weight': config.proximity_penalty_weight
                })
            
            # 准备场景3特有的参数
            scenario3_kwargs = {}
            if n_clusters is not None:
                scenario3_kwargs['n_clusters'] = n_clusters
            if cluster_std is not None:
                scenario3_kwargs['cluster_std'] = cluster_std
            if central_area_ratio is not None:
                scenario3_kwargs['central_area_ratio'] = central_area_ratio
            if area_size is not None:
                scenario3_kwargs['area_size'] = area_size
            
            raw_env = UAVMultiHopEnv(
                max_hops=max_hops,
                **env_kwargs, # 传递通用参数
                **reward_kwargs, # 传递场景3的新奖励权重参数
                **scenario3_kwargs # 传递场景3特有参数
            )
        else:
            raise ValueError(f"未知的场景: {scenario}")

        # 使用适配器包装环境，并传递种子
        env = ParallelToArrayAdapter(raw_env, seed=env_seed)
        return env

    return _init

# 解析命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description='使用论文《Hierarchical Multi-Agent Skill Discovery》中的超参数运行HMASD (多进程版本)')
    # 运行模式和环境参数
    parser.add_argument('--mode', type=str, default='train', help='运行模式: train或eval')
    parser.add_argument('--scenario', type=int, default=3, help='场景: 1=基站模式, 2=协作组网模式, 3=强制多跳模式')
    parser.add_argument('--model_path', type=str, default='models/hmasd_multiproc_paper_config.pt', help='模型保存/加载路径')
    parser.add_argument('--log_dir', type=str, default='logs', help='日志目录')
    parser.add_argument('--log_level', type=str, default='info', 
                        choices=['debug', 'info', 'warning', 'error', 'critical'], 
                        help='日志级别 (debug=详细, info=信息, warning=警告, error=错误, critical=严重)')
    parser.add_argument('--console_log_level', type=str, default='error', 
                        choices=['debug', 'info', 'warning', 'error', 'critical'], 
                        help='控制台日志级别')
    parser.add_argument('--eval_episodes', type=int, default=10, help='评估的episode数量')
    parser.add_argument('--render', action='store_true', help='是否渲染环境')
    parser.add_argument('--device', type=str, default='auto', 
                        choices=['auto', 'cuda', 'cpu'], help='计算设备: auto=自动选择, cuda=GPU, cpu=CPU')
    parser.add_argument('--resume_from', type=str, default='', 
                        help='预训练模型路径，用于继续训练（如果为空则从头开始训练）')

    # 环境参数
    parser.add_argument('--n_uavs', type=int, default=10, help='无人机数量 ')
    parser.add_argument('--n_users', type=int, default=50, help='用户数量 ')
    parser.add_argument('--area_size', type=int, default=3000, help='区域大小 (米, 场景3默认3000)')
    parser.add_argument('--max_hops', type=int, default=5, help='最大跳数 (场景2和3使用)')
    parser.add_argument('--user_distribution', type=str, default='multi_cluster', 
                        choices=['uniform', 'cluster', 'hotspot', 'multi_cluster'], help='用户分布类型')
    parser.add_argument('--channel_model', type=str, default='3gpp-36777',
                        choices=['free_space', 'urban', 'suburban','3gpp-36777', 'probabilistic'], help='信道模型')
    
    # FDMA 参数
    parser.add_argument('--use-fdma', action=argparse.BooleanOptionalAction, default=True,
                        help='理想FDMA,0干扰 (默认: --use-fdma, 使用 --no-use-fdma 禁用)')
    parser.add_argument('--bandwidth', type=float, default=20e6, help='每个无人机的带宽 (Hz)。默认: 20e6')
    
    # 场景3特有参数
    parser.add_argument('--n_clusters', type=int, default=5, help='用户簇数量 (仅用于场景3)')
    parser.add_argument('--cluster_std', type=int, default=150, help='簇内用户分布标准差 (米, 仅用于场景3)')
    parser.add_argument('--central_area_ratio', type=float, default=0.5, help='中心用户区域占总区域的比例 (仅用于场景3)')
    
    # 并行参数
    parser.add_argument('--num_envs', type=int, default=0, 
                        help='并行环境数量 (0=使用配置文件中的值)')
    parser.add_argument('--eval_rollout_threads', type=int, default=0, 
                        help='评估时的并行线程数 (0=使用配置文件中的值)')
    
    # 数据收集参数
    parser.add_argument('--export_interval', type=int, default=1000, 
                        help='数据导出间隔步数')
    parser.add_argument('--detailed_logging', action='store_true', 
                        help='启用详细的奖励日志记录')
    
    # OPT模块参数
    parser.add_argument('--use_opt', action=argparse.BooleanOptionalAction, default=True,
                        help='是否使用OPT (Interaction Pattern Disentangling) 模块 (使用--use_opt启用，--no-use_opt禁用)')
    
    return parser.parse_args()

# 训练函数
def train(vec_env, eval_vec_env, config, args, device): # Add eval_vec_env parameter
    """
    训练HMASD代理 (多进程版本)

    参数:
        vec_env: 训练用的向量化环境实例
        eval_vec_env: 评估用的向量化环境实例
        config: 配置对象
        args: 命令行参数
        device: 计算设备
    """
    num_envs = vec_env.num_envs # Get num_envs from SubprocVecEnv
    main_logger.info(f"开始训练HMASD (多进程版本，使用 {num_envs} 个并行环境)...")
    main_logger.info(f"配置已预先初始化: state_dim={config.state_dim}, obs_dim={config.obs_dim}, n_agents={config.n_agents}")

    # 创建日志目录
    log_dir = os.path.join(args.log_dir, f"sb3_multiproc_paper_config_{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(log_dir, exist_ok=True)
    model_dir = os.path.dirname(args.model_path)
    os.makedirs(model_dir, exist_ok=True)
    
    # 创建HMASD代理
    agent = HMASDAgent(config, log_dir=log_dir, device=device)
    
    # 如果指定了预训练模型路径，加载模型继续训练
    if args.resume_from and os.path.exists(args.resume_from):
        main_logger.info(f"加载预训练模型: {args.resume_from}")
        try:
            # 为了兼容新版PyTorch的安全加载机制，添加Config类到安全全局列表
            import torch.serialization
            torch.serialization.add_safe_globals([Config])
            main_logger.debug("已将Config类添加到PyTorch安全全局列表")
            
            agent.load_model(args.resume_from)
            main_logger.info(f"成功加载预训练模型，将在此基础上继续训练")
            
            # 记录续训信息到TensorBoard
            agent.writer.add_text('Training/resumed_from', args.resume_from, 0)
            agent.writer.add_text('Training/mode', 'resume_training', 0)
        except Exception as e:
            main_logger.error(f"加载预训练模型失败: {e}")
            main_logger.info("将从头开始训练")
            agent.writer.add_text('Training/mode', 'from_scratch_due_to_load_error', 0)
    elif args.resume_from:
        main_logger.warning(f"指定的预训练模型文件不存在: {args.resume_from}")
        main_logger.info("将从头开始训练")
        agent.writer.add_text('Training/mode', 'from_scratch_due_to_missing_file', 0)
    else:
        main_logger.info("从头开始训练")
        agent.writer.add_text('Training/mode', 'from_scratch', 0)
    
    # 创建增强的奖励追踪器
    reward_tracker = EnhancedRewardTracker(log_dir, config, n_users=args.n_users)
    reward_tracker.export_interval = args.export_interval
    
    # 记录超参数
    agent.writer.add_text('Parameters/n_agents', str(config.n_agents), 0)
    agent.writer.add_text('Parameters/n_Z', str(config.n_Z), 0)
    agent.writer.add_text('Parameters/n_z', str(config.n_z), 0)
    agent.writer.add_text('Parameters/k', str(config.k), 0)
    agent.writer.add_text('Parameters/gamma', str(config.gamma), 0)
    agent.writer.add_text('Parameters/lambda_e', str(config.lambda_e), 0)
    agent.writer.add_text('Parameters/lambda_D', str(config.lambda_D), 0)
    agent.writer.add_text('Parameters/lambda_d', str(config.lambda_d), 0)
    agent.writer.add_text('Parameters/lambda_h', str(config.lambda_h), 0)
    agent.writer.add_text('Parameters/lambda_l', str(config.lambda_l), 0)
    agent.writer.add_text('Parameters/hidden_size', str(config.hidden_size), 0)
    agent.writer.add_text('Parameters/lr', str(config.lr_coordinator), 0)
    agent.writer.add_text('Parameters/num_envs', str(num_envs), 0) # Use num_envs variable
    agent.writer.add_text('Parameters/export_interval', str(args.export_interval), 0)
    agent.writer.add_text('Parameters/detailed_logging', str(args.detailed_logging), 0)
    agent.writer.add_text('Parameters/use_opt', str(config.use_opt), 0)
    
    # 记录OPT相关参数
    if config.use_opt:
        agent.writer.add_text('Parameters/lambda_cd', str(config.lambda_cd), 0)
    
    # 记录环境奖励权重配置（场景3的新权重）
    agent.writer.add_text('Environment/effective_coverage_weight', str(config.effective_coverage_weight), 0)
    agent.writer.add_text('Environment/throughput_weight', str(config.throughput_weight), 0)
    agent.writer.add_text('Environment/load_balance_weight', str(config.load_balance_weight), 0)
    # agent.writer.add_text('Environment/network_connectivity_weight', str(config.network_connectivity_weight), 0)  # 已废弃

    # 训练变量
    total_steps = 0
    n_episodes = 0
    max_episodes = config.total_timesteps // config.buffer_size  # 估计的最大episode数量
    episode_rewards = []
    update_times = 0
    best_reward = float('-inf')
    last_eval_step = 0  # 跟踪上次评估的步数
    
    # 高层样本累积检测变量
    high_level_samples_collected_total = 0  # 总共收集的高层样本数
    last_check_total_steps = 0              # 上次检查时的总步数
    last_check_hl_samples = 0               # 上次检查时的高层样本数
    last_high_level_buffer_size = 0         # 上次检查时的高层缓冲区大小
    check_interval_steps = config.buffer_size * num_envs  # 检查间隔步数
    warning_threshold_ratio = 0.1  # 如果实际样本数少于预期的10%，则发出警告
    error_threshold_steps = config.k * num_envs * 10  # 足够执行10个完整技能周期的步数
    
    # 记录训练开始时间
    start_time = time.time()

    # 重置所有环境 (使用 SubprocVecEnv)
    # SubprocVecEnv.reset() 只返回 observations
    # 我们需要通过 env_method 获取初始状态
    main_logger.info("重置并行环境...")
    results = vec_env.env_method('reset') # This calls reset on each env in parallel
    observations = np.array([res[0] for res in results]) # Shape: (num_envs, n_uavs, obs_dim)
    initial_infos = [res[1] for res in results]
    # Use agent.config.state_dim for default state shape
    states = np.array([info.get('state', np.zeros(agent.config.state_dim)) for info in initial_infos]) # Extract initial states, provide default
    main_logger.info(f"环境已重置。观测形状: {observations.shape}, 状态形状: {states.shape}")

    # 环境状态跟踪
    env_steps = np.zeros(num_envs, dtype=int)  # 每个环境的步数
    env_rewards = np.zeros(num_envs)  # 每个环境的累积奖励
    env_skill_durations = np.zeros(num_envs, dtype=int)  # 每个环境当前技能的持续时间
    # env_dones is handled by SubprocVecEnv's return value
    
    # 严格on-policy训练循环
    rollout_steps = 0  # 当前rollout中的步数
    
    while total_steps < config.total_timesteps:
        # 收集rollout数据
        for rollout_step in range(config.rollout_length):
            # 代理为所有环境选择动作
            all_actions_list = []
            all_agent_infos_list = []

            for i in range(num_envs):
                # 代理选择动作
                actions, agent_info = agent.step(states[i], observations[i], env_steps[i], deterministic=False, env_id=i)
                all_actions_list.append(actions)
                all_agent_infos_list.append(agent_info)

            # 将动作列表转换为 NumPy 数组
            actions_array = np.array(all_actions_list)

            # 执行动作
            next_observations, rewards, dones, infos = vec_env.step(actions_array)

            # 从 infos 提取 next_states
            next_states = np.array([info.get('next_state', np.zeros(config.state_dim)) for info in infos])

            # 存储经验到缓冲区
            for i in range(num_envs):
                current_agent_info = all_agent_infos_list[i]
                skill_timer_value = env_skill_durations[i]
                
                # 存储转换
                agent.store_transition(
                    states[i], next_states[i], observations[i], next_observations[i],
                    actions_array[i], rewards[i], dones[i], current_agent_info['team_skill'],
                    current_agent_info['agent_skills'], current_agent_info['action_logprobs'],
                    log_probs=current_agent_info['log_probs'],
                    skill_timer_for_env=skill_timer_value,
                    env_id=i
                )
                
                # 更新技能持续时间
                if dones[i]:
                    env_skill_durations[i] = 0
                elif skill_timer_value == config.k - 1:
                    env_skill_durations[i] = 0
                elif current_agent_info['skill_changed']:
                    env_skill_durations[i] = 0
                else:
                    env_skill_durations[i] += 1

                # 更新环境状态跟踪
                env_steps[i] += 1
                env_rewards[i] += rewards[i]

                # 使用增强的奖励追踪器记录训练步骤
                if args.detailed_logging:
                    # 获取奖励组成部分（如果可用）
                    reward_components = None
                    if hasattr(agent, 'last_reward_components') and agent.last_reward_components:
                        reward_components = agent.last_reward_components.get(i, None)
                    
                    reward_tracker.log_training_step(
                        step=total_steps - num_envs + i + 1,
                        env_id=i,
                        reward=rewards[i],
                        reward_components=reward_components,
                        info=infos[i]
                    )

                # 记录技能使用
                reward_tracker.log_skill_usage(
                    step=total_steps - num_envs + i + 1,
                    team_skill=current_agent_info['team_skill'],
                    agent_skills=current_agent_info['agent_skills'],
                    skill_changed=current_agent_info.get('skill_changed', False)
                )

                # 记录技能分布
                if current_agent_info['skill_changed']:
                    agent.log_skill_distribution(
                        current_agent_info['team_skill'],
                        current_agent_info['agent_skills'],
                        episode=n_episodes
                    )

                # 处理episode完成
                if dones[i]:
                    n_episodes += 1
                    episode_rewards.append(env_rewards[i])

                    # 使用增强的奖励追踪器记录episode完成
                    episode_info = {}
                    if 'global' in infos[i]:
                        episode_info.update(infos[i]['global'])
                    
                    reward_tracker.log_episode_completion(
                        episode_num=n_episodes,
                        env_id=i,
                        total_reward=env_rewards[i],
                        episode_length=env_steps[i],
                        info=episode_info
                    )

                    # 记录到 TensorBoard
                    agent.training_info['episode_rewards'].append(env_rewards[i])
                    agent.writer.add_scalar('Reward/episode_reward', env_rewards[i], n_episodes)
                    agent.writer.add_scalar('Reward/episode_length', env_steps[i], n_episodes)

                    main_logger.info(f"环境 {i}/{num_envs} 完成: Episode {n_episodes}, 奖励: {env_rewards[i]:.2f}, 步数: {env_steps[i]}")

                    # 重置环境状态跟踪
                    env_steps[i] = 0
                    env_rewards[i] = 0

                    # 奖励统计
                    if len(episode_rewards) >= 10:
                        recent_rewards = episode_rewards[-10:]
                        avg_reward = np.mean(recent_rewards)
                        std_reward = np.std(recent_rewards)
                        max_reward = np.max(recent_rewards)
                        min_reward = np.min(recent_rewards)

                        agent.writer.add_scalar('Reward/avg_reward_10', avg_reward, n_episodes)
                        agent.writer.add_scalar('Reward/std_reward_10', std_reward, n_episodes)
                        agent.writer.add_scalar('Reward/max_reward_10', max_reward, n_episodes)
                        agent.writer.add_scalar('Reward/min_reward_10', min_reward, n_episodes)

                        main_logger.info(f"最近10个episodes: 平均奖励 {avg_reward:.2f} ± {std_reward:.2f}, 最大/最小: {max_reward:.2f}/{min_reward:.2f}")

                    # 绘图
                    if n_episodes % 10 == 0:
                        plt.figure(figsize=(10, 5))
                        plt.plot(episode_rewards)
                        plt.title('Episode Rewards')
                        plt.xlabel('Episode')
                        plt.ylabel('Reward')
                        plt.savefig(os.path.join(log_dir, 'rewards.png'))
                        plt.close()

            # 更新状态和观测
            states = next_states
            observations = next_observations
            total_steps += num_envs
            rollout_steps += 1

            # 如果达到总步数限制，跳出rollout收集循环
            if total_steps >= config.total_timesteps:
                break

        # Rollout数据收集完成，进行更新
        if len(agent.low_level_buffer) >= agent.config.batch_size:
            try:
                update_info = agent.update()
                update_times += 1
                elapsed = time.time() - start_time

                main_logger.info(f"Rollout更新 {update_times} (收集了 {rollout_steps} 步), 总步数 {total_steps}, "
                      f"高层损失 {update_info['coordinator_loss']:.4f}, "
                      f"低层损失 {update_info['discoverer_loss']:.4f}, "
                      f"判别器损失 {update_info['discriminator_loss']:.4f}, "
                      f"CD损失 {update_info.get('cd_loss', 0):.4f}, "
                      f"已用时间 {elapsed:.2f}s")
                
                # 详细记录低层损失的组成部分
                main_logger.info(f"低层损失详情 - 总损失: {update_info['discoverer_loss']:.4f}, "
                      f"策略损失: {update_info['discoverer_policy_loss']:.4f}, "
                      f"价值损失: {update_info['discoverer_value_loss']:.4f}, "
                      f"动作熵: {update_info['action_entropy']:.4f}")
                
                # 详细记录内在奖励组成部分
                main_logger.info(f"内在奖励组成 - 平均总奖励: {update_info['avg_intrinsic_reward']:.4f}, "
                      f"环境奖励部分: {update_info['avg_env_comp']:.4f}, "
                      f"团队判别器部分: {update_info['avg_team_disc_comp']:.4f}, "
                      f"个体判别器部分: {update_info['avg_ind_disc_comp']:.4f}")
                
                # 详细记录价值函数估计
                main_logger.info(f"价值函数估计 - Discoverer均值: {update_info['avg_discoverer_val']:.4f}, "
                      f"Coordinator状态价值: {update_info['mean_coord_state_val']:.4f}, "
                      f"Coordinator智能体价值: {update_info['mean_coord_agent_val']:.4f}")
                
                # 清空缓冲区 (严格on-policy)
                agent.clear_buffers()
                main_logger.debug(f"已清空缓冲区，开始新的rollout")
                
            except ValueError as e:
                main_logger.error(f"更新错误: {e}")
                update_times += 1
        else:
            main_logger.warning(f"缓冲区数据不足，跳过更新。当前缓冲区大小: {len(agent.low_level_buffer)}")

        # 重置rollout步数计数器
        rollout_steps = 0

        # 加强高层样本的累积情况监控
        if total_steps >= last_check_total_steps + check_interval_steps:
                # 获取当前高层缓冲区大小
                current_high_level_buffer_size = len(agent.high_level_buffer)
                
                # 从agent获取总收集的高层样本数(现在总是准确的，不受缓冲区满的影响)
                current_high_level_samples_total = agent.high_level_samples_total
                
                # 计算自上次检查以来的步数和增加的高层样本数
                steps_since_last_check = total_steps - last_check_total_steps
                parallel_steps_since_last_check = steps_since_last_check // num_envs
                samples_since_last_check = current_high_level_samples_total - last_check_hl_samples
                
                # 记录样本收集情况
                main_logger.info(f"高层样本收集统计: 当前总样本数={current_high_level_samples_total}, "
                               f"上次检查时样本数={last_check_hl_samples}, 新增样本数={samples_since_last_check}")
                
                # 更改理论期望样本计算：每k个时间步应该产生一个高层样本
                # 考虑到不同环境可能步调不一致，使用更宽松的期望值
                min_expected_environments = num_envs * 0.5  # 假设至少一半的环境应该贡献样本
                expected_samples_min = (parallel_steps_since_last_check / config.k) * min_expected_environments
                
                # 获取智能体中的样本收集统计
                high_level_samples_by_env = getattr(agent, 'high_level_samples_by_env', {})
                high_level_samples_by_reason = getattr(agent, 'high_level_samples_by_reason', {})
                
                # 统计各环境的技能计时器状态和奖励累积，以便排查问题
                env_timers_status = {env_id: agent.env_timers.get(env_id, -1) for env_id in range(num_envs)}
                env_rewards_status = {env_id: agent.env_reward_sums.get(env_id, -1.0) for env_id in range(num_envs)}
                
                # 分析样本收集情况
                contributing_envs = sum(1 for count in high_level_samples_by_env.values() if count > 0)
                
                # 记录当前检查点的统计信息（增加环境分析）
                main_logger.info(f"高层样本累积检查: 总步数: {total_steps}, 并行步数: {total_steps//num_envs}, "
                     f"自上次检查增加的高层样本数: {samples_since_last_check}, "
                     f"当前高层缓冲区大小: {current_high_level_buffer_size}/(需要{config.high_level_batch_size}), "
                     f"正在贡献的环境数: {contributing_envs}/{num_envs}")
                
                # 记录详细统计信息
                main_logger.info(f"高层样本收集原因: {high_level_samples_by_reason}")
                main_logger.info(f"环境技能计时器状态: {env_timers_status}")
                main_logger.info(f"环境奖励累积状态: {env_rewards_status}")
                
                # 检查是否有环境未贡献样本
                non_contributing_envs = [env_id for env_id in range(num_envs) 
                                         if high_level_samples_by_env.get(env_id, 0) == 0]
                if non_contributing_envs:
                    main_logger.warning(f"存在{len(non_contributing_envs)}个环境未贡献高层样本: {non_contributing_envs}")
                    
                    # 对未贡献样本的环境强制收集
                    for env_id in non_contributing_envs:
                        if hasattr(agent, 'force_high_level_collection'):
                            agent.force_high_level_collection[env_id] = True
                            main_logger.info(f"已标记环境{env_id}强制收集高层样本")
                
                # 如果自上次检查以来收集样本很少，发出警告
                if parallel_steps_since_last_check > config.k * 2 and samples_since_last_check < 1:
                    warning_msg = (
                        f"警告：高层经验累积速度不足！\n"
                        f"在过去的 {parallel_steps_since_last_check} 个并行时间步中 (总步数 {steps_since_last_check}), "
                        f"没有收集到高层样本。"
                    )
                    main_logger.warning(warning_msg)
                
                # 如果长时间内高层样本几乎没有增长，记录严重错误但不中断训练
                if parallel_steps_since_last_check > config.k * 5 and samples_since_last_check == 0:
                    error_msg = (
                        f"高层经验累积速度严重不足！\n"
                        f"在过去的 {parallel_steps_since_last_check} 个并行时间步中 (总步数 {steps_since_last_check}), "
                        f"仅收集到 {samples_since_last_check} 个高层样本。\n"
                        f"预期至少收集到约 {expected_samples_min:.1f} 个 (基于 k={config.k}, num_envs={num_envs})。\n"
                        f"当前高层缓冲区总大小: {current_high_level_buffer_size} (批次需求: {config.high_level_batch_size})。"
                    )
                    main_logger.error(error_msg)
                    
                    # 修改：不再中断训练，而是尝试通过循环强制收集
                    if hasattr(agent, 'force_high_level_collection'):
                        for env_id in range(num_envs):
                            agent.force_high_level_collection[env_id] = True
                        main_logger.info("已强制标记所有环境在下一个技能周期结束时贡献样本")
                
                # 更新检查点变量
                last_check_total_steps = total_steps
                last_check_hl_samples = current_high_level_samples_total
                last_high_level_buffer_size = current_high_level_buffer_size
                
                # 将高层样本累积情况记录到TensorBoard（增强记录指标）
                agent.writer.add_scalar('Buffer/high_level_buffer_size', current_high_level_buffer_size, total_steps)
                agent.writer.add_scalar('Buffer/high_level_samples_collected_total', current_high_level_samples_total, total_steps)
                agent.writer.add_scalar('Buffer/contributing_environments', contributing_envs, total_steps)
                if parallel_steps_since_last_check > 0:
                    samples_per_k_steps = (samples_since_last_check / parallel_steps_since_last_check) * config.k
                    agent.writer.add_scalar('Buffer/high_level_samples_per_k_steps', samples_per_k_steps, total_steps)
                    
                # 记录各种收集原因的比例
                for reason, count in high_level_samples_by_reason.items():
                    agent.writer.add_scalar(f'Buffer/collection_reason_{reason}', count, total_steps)
        
        # 定期导出训练数据
        reward_tracker.export_training_data(total_steps, agent.writer)
        
        # 评估 (基于总步数和上次评估的时间)
        if total_steps >= last_eval_step + config.eval_interval:
            main_logger.info(f"即将进行评估，将评估 {config.eval_episodes} 个episodes...")
            main_logger.info(f"当前步数: {total_steps}, 距离上次评估: {total_steps - last_eval_step} 步")
            # 使用 eval_vec_env 进行评估
            eval_reward, eval_std, eval_min, eval_max = evaluate(eval_vec_env, agent, config.eval_episodes)
            main_logger.info(f"评估完成 ({config.eval_episodes} 个episodes): 平均奖励 {eval_reward:.2f} ± {eval_std:.2f}, 最大/最小: {eval_max:.2f}/{eval_min:.2f}")

            # 保存最佳模型
            if eval_reward > best_reward:
                best_reward = eval_reward
                agent.save_model(args.model_path)
                main_logger.info(f"保存最佳模型，奖励: {best_reward:.2f}")
            
            # 更新上次评估步数
            last_eval_step = total_steps

    main_logger.info(f"训练完成! 总步数: {total_steps}, 总episodes: {n_episodes}")
    main_logger.info(f"最佳奖励: {best_reward:.2f}")

    # 最终数据导出和统计
    main_logger.info("生成最终训练统计报告...")
    reward_tracker.export_training_data(total_steps, agent.writer)
    
    # 获取并打印训练摘要统计
    summary_stats = reward_tracker.get_summary_statistics()
    main_logger.info("\n===== 训练摘要统计 =====")
    main_logger.info(f"总训练步数: {summary_stats['total_steps']}")
    main_logger.info(f"总完成episodes: {summary_stats['total_episodes']}")
    main_logger.info(f"技能切换总次数: {summary_stats['skill_switches']}")
    
    if 'reward_mean' in summary_stats:
        main_logger.info(f"平均episode奖励: {summary_stats['reward_mean']:.2f} ± {summary_stats['reward_std']:.2f}")
        main_logger.info(f"最大/最小episode奖励: {summary_stats['reward_max']:.2f}/{summary_stats['reward_min']:.2f}")
    
    if 'team_skill_usage' in summary_stats:
        main_logger.info(f"团队技能使用分布: {summary_stats['team_skill_usage']}")
    
    # 导出最终数据摘要到JSON文件
    import json
    final_summary_path = os.path.join(log_dir, 'final_training_summary.json')
    with open(final_summary_path, 'w') as f:
        json.dump(summary_stats, f, indent=2)
    main_logger.info(f"最终训练摘要已保存到: {final_summary_path}")

    # 保存最终模型
    final_model_path = os.path.join(model_dir, 'hmasd_sb3_multiproc_paper_config_final.pt') # Update filename
    agent.save_model(final_model_path)
    main_logger.info(f"最终模型已保存到 {final_model_path}")
    
    return agent

# 评估函数
def evaluate(vec_env, agent, n_episodes=10, render=False):
    """
    评估HMASD代理 (使用 SubprocVecEnv)

    参数:
        vec_env: SubprocVecEnv 实例
        agent: HMASD代理实例
        n_episodes: 评估的episode数量 (总共要评估的episode数量)
        render: 是否渲染环境 (只渲染第一个环境)

    返回:
        mean_reward: 平均奖励
        std_reward: 奖励标准差
        min_reward: 最小奖励
        max_reward: 最大奖励
    """
    # 打印评估参数
    num_envs = vec_env.num_envs
    main_logger.info(f"开始评估: 目标完成 {n_episodes} 个episodes，使用 {num_envs} 个并行环境，是否渲染: {render}")
    
    # 用于计时的变量
    eval_start_time = time.time()
    step_times = []
    agent_step_times = []
    env_step_times = []
    episode_rewards = []
    episode_lengths = []
    eval_step = getattr(agent, 'global_step', 0) # Get current training step if available
    num_envs = vec_env.num_envs

    # 重置所有环境并获取初始状态
    results = vec_env.env_method('reset')
    observations = np.array([res[0] for res in results])
    initial_infos = [res[1] for res in results]
    # Use agent.config.state_dim for default state shape
    states = np.array([info.get('state', np.zeros(agent.config.state_dim)) for info in initial_infos]) # Use agent's state_dim

    # 环境状态跟踪
    env_steps = np.zeros(num_envs, dtype=int)
    env_rewards = np.zeros(num_envs)
    active_envs = np.ones(num_envs, dtype=bool) # Track which envs are still running for the current eval round
    completed_episodes = 0
    
    # 统计信息
    all_team_skills = []  # 记录每个时间步的团队技能
    all_agent_skills = []  # 记录每个时间步的个体技能
    total_served_users = []  # 记录每个episode的服务用户数
    total_coverage_ratios = []  # 记录每个episode的覆盖率
    
    # 奖励统计
    high_level_rewards = []  # 高层奖励 (环境奖励)
    low_level_rewards = {   # 底层奖励组成
        'env_component': [],        # 环境奖励部分
        'team_disc_component': [],  # 团队判别器部分
        'ind_disc_component': []    # 个体判别器部分
    }

    # 设置确定性评估模式
    with torch.no_grad():
        while completed_episodes < n_episodes:
            loop_start_time = time.time()
            
            # 为活跃环境选择动作
            all_actions_list = []
            all_agent_infos_list = [] # Store agent info for logging if needed

            # 记录agent.step总时间
            agent_step_start = time.time()
            for i in range(num_envs):
                if active_envs[i]:
                    # 记录每个agent.step调用的时间
                    step_start = time.time()
                    actions, agent_info = agent.step(states[i], observations[i], env_steps[i], deterministic=True, env_id=i)
                    step_end = time.time()
                    agent_step_times.append(step_end - step_start)
                    
                    all_actions_list.append(actions)
                    all_agent_infos_list.append(agent_info)
                    
                    # 收集技能分布信息
                    all_team_skills.append(agent_info['team_skill'])
                    all_agent_skills.append(agent_info['agent_skills'])
                else:
                    # Append dummy action if env is already done for this eval round
                    all_actions_list.append(np.zeros(vec_env.action_space.shape[1:])) # Use action space shape
                    all_agent_infos_list.append({}) # Dummy info
            agent_step_end = time.time()
            agent_step_total = agent_step_end - agent_step_start

            actions_array = np.array(all_actions_list)

            # 执行动作并记录环境步进时间
            env_step_start = time.time()
            next_observations, rewards, dones, infos = vec_env.step(actions_array)
            env_step_end = time.time()
            env_step_times.append(env_step_end - env_step_start)
            
            # 每100步打印一次性能统计
            steps_done = len(agent_step_times)
            if steps_done % 100 == 0 and steps_done > 0:
                avg_agent_step = np.mean(agent_step_times[-100:])
                avg_env_step = np.mean(env_step_times[-100:])
                main_logger.info(f"评估性能统计 [{steps_done}步]: agent.step平均耗时: {avg_agent_step:.6f}秒/步, "
                      f"vec_env.step平均耗时: {avg_env_step:.6f}秒/步")
            
            loop_end_time = time.time()
            step_times.append(loop_end_time - loop_start_time)

            # 从 infos 提取 next_states
            # Use agent.config.state_dim for default state shape
            next_states = np.array([info.get('next_state', np.zeros(agent.config.state_dim)) for info in infos])

            # 更新环境状态
            for i in range(num_envs):
                if active_envs[i]:
                    env_steps[i] += 1
                    env_rewards[i] += rewards[i]

                    if render and i == 0:
                        try:
                            vec_env.env_method('render', indices=[0]) # Render only the first env
                        except Exception as e:
                            main_logger.error(f"渲染错误: {e}")
                            render = False # Disable rendering if it fails

                    # 如果环境完成
                    if dones[i]:
                        if completed_episodes < n_episodes:
                            episode_rewards.append(env_rewards[i])
                            episode_lengths.append(env_steps[i])
                            
                            # 获取服务用户数和覆盖率信息（如果可用）
                            if 'global' in infos[i] and 'served_users' in infos[i]['global']:
                                served_users = infos[i]['global']['served_users']
                                n_users = len(infos[i]['global']['connections'][0]) if infos[i]['global']['connections'].shape[0] > 0 else 0
                                coverage_ratio = served_users / n_users if n_users > 0 else 0
                                
                                total_served_users.append(served_users)
                                total_coverage_ratios.append(coverage_ratio)
                                
                                main_logger.info(f"评估 Episode {completed_episodes+1}/{n_episodes} (来自环境 {i}), 奖励: {env_rewards[i]:.2f}, 步数: {env_steps[i]}, 服务用户数: {served_users}/{n_users} ({coverage_ratio:.2%})")
                            else:
                                main_logger.info(f"评估 Episode {completed_episodes+1}/{n_episodes} (来自环境 {i}), 奖励: {env_rewards[i]:.2f}, 步数: {env_steps[i]}")

                            # 记录到TensorBoard
                            if hasattr(agent, 'writer'):
                                agent.writer.add_scalar('Eval/episode_reward', env_rewards[i], eval_step + completed_episodes)
                                agent.writer.add_scalar('Eval/episode_length', env_steps[i], eval_step + completed_episodes)
                                if 'global' in infos[i] and 'served_users' in infos[i]['global']:
                                    agent.writer.add_scalar('Eval/served_users', served_users, eval_step + completed_episodes)
                                    agent.writer.add_scalar('Eval/coverage_ratio', coverage_ratio, eval_step + completed_episodes)

                            # 记录高层奖励
                            high_level_rewards.append(env_rewards[i])
                            completed_episodes += 1

                        # 标记此环境在此评估轮次中完成
                        active_envs[i] = False

                        # 不需要手动重置，SubprocVecEnv 会自动处理
                        # 也不需要重置 env_steps 和 env_rewards，因为我们只运行 n_episodes

            # 更新状态和观测
            states = next_states
            observations = next_observations

            # 如果所有需要的 episodes 都已完成，则退出循环
            if completed_episodes >= n_episodes:
                break
            # 如果所有环境都已完成其当前 episode 但仍未达到 n_episodes，也可能需要退出或处理
            if not np.any(active_envs):
                main_logger.warning("所有评估环境都已完成，但尚未达到目标 episode 数量。")
                break

    mean_reward = np.mean(episode_rewards) if episode_rewards else 0
    std_reward = np.std(episode_rewards) if episode_rewards else 0
    min_reward = np.min(episode_rewards) if episode_rewards else 0
    max_reward = np.max(episode_rewards) if episode_rewards else 0
    mean_length = np.mean(episode_lengths) if episode_lengths else 0

    # 记录评估统计信息
    if hasattr(agent, 'writer'):
        agent.writer.add_scalar('Eval/mean_reward', mean_reward, eval_step)
        agent.writer.add_scalar('Eval/reward_std', std_reward, eval_step)
        agent.writer.add_scalar('Eval/mean_episode_length', mean_length, eval_step)
        agent.writer.flush()

    # 分析技能使用分布
    if all_team_skills:
        team_skill_counts = np.zeros(agent.config.n_Z)
        for skill in all_team_skills:
            team_skill_counts[skill] += 1
        team_skill_probs = team_skill_counts / len(all_team_skills)
        
        main_logger.info("\n===== 评估技能分布统计 =====")
        main_logger.info(f"团队技能使用分布: {team_skill_probs}")
        
        # 统计智能体技能使用情况
        if all_agent_skills:
            all_agent_skills_np = np.array(all_agent_skills)
            agent_skill_counts = np.zeros((agent.config.n_agents, agent.config.n_z))
            for skills in all_agent_skills:
                for i, skill in enumerate(skills):
                    if i < agent.config.n_agents:  # 确保索引在范围内
                        agent_skill_counts[i, skill] += 1
            
            # 计算每个智能体的技能使用概率
            agent_skill_probs = agent_skill_counts / len(all_agent_skills)
            
            # 打印每个智能体的技能使用情况
            for i in range(min(3, agent.config.n_agents)):  # 只打印前3个智能体以避免输出过多
                main_logger.info(f"智能体 {i} 技能使用分布: {agent_skill_probs[i]}")
            
            if agent.config.n_agents > 3:
                main_logger.info(f"... (共 {agent.config.n_agents} 个智能体)")
    
        # 记录到TensorBoard
        if hasattr(agent, 'writer'):
            for z in range(agent.config.n_Z):
                agent.writer.add_scalar(f'Eval/TeamSkill_{z}_Probability', team_skill_probs[z], eval_step)
            
            for i in range(agent.config.n_agents):
                for z in range(agent.config.n_z):
                    agent.writer.add_scalar(f'Eval/Agent{i}_Skill_{z}_Probability', agent_skill_probs[i][z], eval_step)

    # 打印奖励统计信息
    if high_level_rewards:
        main_logger.info("\n===== 评估奖励统计 =====")
        mean_high_level = np.mean(high_level_rewards)
        main_logger.info(f"高层奖励平均值: {mean_high_level:.4f}")

    # 计算并打印性能统计
    eval_total_time = time.time() - eval_start_time
    total_steps_taken = sum(episode_lengths) if episode_lengths else 0
    if total_steps_taken > 0:
        avg_step_time = eval_total_time / total_steps_taken
        avg_agent_step_time = np.mean(agent_step_times) if agent_step_times else 0
        avg_env_step_time = np.mean(env_step_times) if env_step_times else 0
        
        main_logger.info("\n===== 评估性能统计 =====")
        main_logger.info(f"总评估时间: {eval_total_time:.2f}秒 (完成 {len(episode_rewards)} episodes, 共 {total_steps_taken} 步)")
        main_logger.info(f"每步平均耗时: {avg_step_time:.6f}秒")
        main_logger.info(f"agent.step 平均耗时: {avg_agent_step_time:.6f}秒/步 (占 {avg_agent_step_time/avg_step_time*100:.1f}%)")
        main_logger.info(f"env.step 平均耗时: {avg_env_step_time:.6f}秒/步 (占 {avg_env_step_time/avg_step_time*100:.1f}%)")
        main_logger.info(f"其他操作耗时: {avg_step_time - avg_agent_step_time - avg_env_step_time:.6f}秒/步")
        
        # 将性能指标也记录到TensorBoard中
        if hasattr(agent, 'writer'):
            agent.writer.add_scalar('Performance/total_eval_time', eval_total_time, eval_step)
            agent.writer.add_scalar('Performance/avg_step_time', avg_step_time, eval_step)
            agent.writer.add_scalar('Performance/avg_agent_step_time', avg_agent_step_time, eval_step)
            agent.writer.add_scalar('Performance/avg_env_step_time', avg_env_step_time, eval_step)
    
    main_logger.info(f"\n评估完成 ({len(episode_rewards)} episodes): 平均奖励 {mean_reward:.2f} ± {std_reward:.2f}, 平均步数: {mean_length:.2f}")

    return mean_reward, std_reward, min_reward, max_reward

# 主函数
def main():
    args = parse_args()
    
    # 创建日志目录
    os.makedirs(args.log_dir, exist_ok=True)
    
    # 为训练会话创建固定的日志文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f"hmasd_training_{timestamp}.log"
    
    # 初始化多进程日志系统
    file_level = LOG_LEVELS.get(args.log_level.lower(), logging.INFO)
    console_level = LOG_LEVELS.get(args.console_log_level.lower(), logging.WARNING)
    init_multiproc_logging(
        log_dir=args.log_dir, 
        log_file=log_file, 
        file_level=file_level, 
        console_level=console_level
    )
    
    # 获取main_logger实例
    global main_logger
    main_logger = get_logger("HMASD-Main")
    main_logger.info(f"多进程日志系统已初始化: 文件级别={args.log_level}, 控制台级别={args.console_log_level}")
    main_logger.info(f"日志文件: {os.path.join(args.log_dir, log_file)}")
    
    # 使用config_1.py中的配置（基于论文超参数）
    config = Config()
    
    # 设置无人机数量（n_agents和n_uavs是同一个参数）
    config.n_agents = args.n_uavs
    main_logger.info(f"设置无人机数量: n_agents = n_uavs = {config.n_agents}")
    
    # 根据命令行参数设置OPT模块使用状态
    config.use_opt = args.use_opt
    main_logger.info(f"OPT模块使用状态: use_opt = {config.use_opt}")
    
    # 获取计算设备
    device = get_device(args.device)
    
    # 确定并行环境数量
    num_envs = args.num_envs if args.num_envs > 0 else config.num_envs
    eval_rollout_threads = args.eval_rollout_threads if args.eval_rollout_threads > 0 else config.eval_rollout_threads
    
    main_logger.info(f"使用 {num_envs} 个并行训练环境和 {eval_rollout_threads} 个并行评估环境")
    
    # 创建环境构造函数列表 (使用修改后的 make_env)
    base_seed = config.seed if hasattr(config, 'seed') else int(time.time()) # Use config seed or time
    main_logger.info(f"基础种子: {base_seed}")

    train_env_fns = [make_env(
        scenario=args.scenario,
        n_uavs=args.n_uavs,
        n_users=args.n_users,
        user_distribution=args.user_distribution,
        channel_model=args.channel_model,
        config=config,  # 传递配置对象
        max_hops=args.max_hops if args.scenario in [2, 3] else None,
        render_mode=None,
        rank=i,
        seed=base_seed,
        # 场景3特有参数
        n_clusters=args.n_clusters if args.scenario == 3 else None,
        cluster_std=args.cluster_std if args.scenario == 3 else None,
        central_area_ratio=args.central_area_ratio if args.scenario == 3 else None,
        area_size=args.area_size if args.scenario == 3 else None,
        use_fdma=args.use_fdma,
        bandwidth=args.bandwidth
    ) for i in range(num_envs)]

    eval_env_fns = [make_env(
        scenario=args.scenario,
        n_uavs=args.n_uavs,
        n_users=args.n_users,
        user_distribution=args.user_distribution,
        channel_model=args.channel_model,
        config=config,  # 传递配置对象
        max_hops=args.max_hops if args.scenario in [2, 3] else None,
        render_mode="human" if args.render and i == 0 else None, # 只在第一个评估环境中渲染
        rank=i,
        seed=base_seed + num_envs, # Use different seeds for eval envs
        # 场景3特有参数
        n_clusters=args.n_clusters if args.scenario == 3 else None,
        cluster_std=args.cluster_std if args.scenario == 3 else None,
        central_area_ratio=args.central_area_ratio if args.scenario == 3 else None,
        area_size=args.area_size if args.scenario == 3 else None,
        use_fdma=args.use_fdma,
        bandwidth=args.bandwidth
    ) for i in range(eval_rollout_threads)]

    # 首先创建一个临时环境来获取维度信息
    main_logger.info("创建临时环境以获取状态和观测维度...")
    temp_env_fn = make_env(
        scenario=args.scenario,
        n_uavs=args.n_uavs,
        n_users=args.n_users,
        user_distribution=args.user_distribution,
        channel_model=args.channel_model,
        config=config,
        max_hops=args.max_hops if args.scenario in [2, 3] else None,
        render_mode=None,
        rank=0,
        seed=base_seed,
        # 场景3特有参数
        n_clusters=args.n_clusters if args.scenario == 3 else None,
        cluster_std=args.cluster_std if args.scenario == 3 else None,
        central_area_ratio=args.central_area_ratio if args.scenario == 3 else None,
        area_size=args.area_size if args.scenario == 3 else None,
        use_fdma=args.use_fdma,
        bandwidth=args.bandwidth
    )
    temp_env = temp_env_fn()
    
    # 从临时环境获取维度信息
    state_dim = temp_env.state_dim
    obs_dim = temp_env.obs_dim
    
    # 更新配置维度（n_agents已在之前设置）
    config.update_env_dims(state_dim, obs_dim)
    
    main_logger.info(f"从环境获取维度信息: state_dim={state_dim}, obs_dim={obs_dim}")
    main_logger.info(f"确认无人机数量: n_agents={config.n_agents}")
    
    # 关闭临时环境
    temp_env.close()
    main_logger.info("临时环境已关闭")

    # 现在创建向量化环境 (使用 SubprocVecEnv)
    main_logger.info("创建 SubprocVecEnv...")
    train_vec_env = SubprocVecEnv(train_env_fns, start_method='spawn') # Use spawn for better compatibility
    eval_vec_env = SubprocVecEnv(eval_env_fns, start_method='spawn')
    main_logger.info("SubprocVecEnv 已创建。")

    main_logger.info(f"使用论文中的超参数: n_Z={config.n_Z}, n_z={config.n_z}, k={config.k}, lambda_e={config.lambda_e}")

    if args.mode == 'train':
        # Pass eval_vec_env to the train function
        agent = train(train_vec_env, eval_vec_env, config, args, device)
    elif args.mode == 'eval':
        # 加载模型
        if not os.path.exists(args.model_path):
            main_logger.error(f"模型文件 {args.model_path} 不存在")
            return
        
        # 更新环境维度 (在 evaluate 函数内部处理，或在这里获取)
        # state_dim_eval = eval_vec_env.get_attr('state_dim')[0]
        # obs_dim_eval = eval_vec_env.get_attr('obs_dim')[0]
        # config.update_env_dims(state_dim_eval, obs_dim_eval) # Ensure config matches eval env if different

        # 创建日志目录
        log_dir = os.path.join(args.log_dir, f"eval_sb3_multiproc_paper_config_{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建代理并加载模型
        agent = HMASDAgent(config, log_dir=log_dir, device=device)
        agent.load_model(args.model_path)
        
        # 记录模型配置
        agent.writer.add_text('Eval/model_path', args.model_path, 0)
        agent.writer.add_text('Eval/scenario', str(args.scenario), 0)
        agent.writer.add_text('Eval/n_agents', str(config.n_agents), 0)
        agent.writer.add_text('Eval/num_envs', str(eval_vec_env.num_envs), 0)

        # 评估模型
        evaluate(eval_vec_env, agent, n_episodes=args.eval_episodes, render=args.render)
    else:
        main_logger.error(f"未知的运行模式: {args.mode}")
    
    # 关闭环境
    train_vec_env.close()
    eval_vec_env.close()

# 全局队列引用，供子进程使用
_shared_log_queue = None

# 为SubprocVecEnv的子进程添加一个直接日志记录的辅助函数
def env_log(level, message, queue=None):
    """
    在子进程中记录日志的辅助函数
    
    参数:
        level: 日志级别 (如 logging.INFO)
        message: 日志消息
        queue: 日志队列 (如果为None，则使用全局队列)
    """
    global _shared_log_queue
    # 使用显式传入的队列或全局队列
    q = queue if queue is not None else _shared_log_queue
    
    try:
        import logging
        # 获取当前进程ID，用于区分不同的环境
        pid = os.getpid()
        
        if q:
            # 创建一个日志记录
            record = logging.LogRecord(
                name=f"Env-{pid}",
                level=level,
                pathname="",
                lineno=0,
                msg=message,
                args=(),
                exc_info=None
            )
            # 将记录直接放入队列
            q.put_nowait(record)
            return True
        else:
            # 如果队列不可用，至少打印到控制台
            print(f"[Env-{pid}] {message} (队列不可用)")
            return False
    except Exception as e:
        # 如果日志记录失败，至少打印到控制台
        pid = os.getpid()
        print(f"[Env-{pid}] {message} (日志记录失败: {e})")
        return False

if __name__ == "__main__":
    # 设置多进程启动方法
    mp.set_start_method('spawn', force=True)
    try:
        main()
    finally:
        # 确保关闭日志系统，刷新所有日志
        try:
            shutdown_logging()
            print("日志系统已关闭")
        except Exception as e:
            print(f"关闭日志系统时出错: {e}")
