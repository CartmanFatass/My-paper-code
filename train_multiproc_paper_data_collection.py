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

# 导入论文中的配置
from config_1 import Config
from hmasd.agent import HMASDAgent
from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter

class PaperDataTracker:
    """专门用于论文数据收集的追踪器"""
    
    def __init__(self, log_dir, config, num_envs):
        self.log_dir = log_dir
        self.config = config
        self.num_envs = num_envs
        
        # 确定导出频率（基于rollout）
        if num_envs <= 32:
            self.export_frequency = 5  # 每5个rollout导出
        elif num_envs <= 64:
            self.export_frequency = 3  # 每3个rollout导出
        else:  # num_envs >= 128
            self.export_frequency = 2  # 每2个rollout导出
        
        # 数据收集
        self.step_data = []  # 每步数据（用于实时TensorBoard记录）
        self.rollout_data = []  # 每rollout汇总数据
        self.episode_data = []  # episode数据
        
        # 性能指标缓存（用于滑动窗口计算）
        self.recent_throughput = deque(maxlen=100)
        self.recent_coverage = deque(maxlen=100)
        self.recent_rewards = deque(maxlen=100)
        
        # 计数器
        self.total_steps = 0
        self.rollout_count = 0
        self.episode_count = 0
        
        # 当前rollout的临时数据
        self.current_rollout_data = {
            'throughput_values': [],
            'coverage_values': [],
            'reward_values': [],
            'served_users': [],
            'total_users': [],
            'system_throughput': [],
            'avg_user_throughput': []
        }
        
    def log_step_data(self, step, env_id, reward, info, writer):
        """记录每步数据并实时写入TensorBoard"""
        self.total_steps += 1
        
        # 提取关键指标
        throughput_data = self._extract_throughput_info(info)
        coverage_data = self._extract_coverage_info(info)
        
        # 保存步级数据
        step_entry = {
            'step': step,
            'env_id': env_id,
            'reward': reward,
            'timestamp': time.time(),
            **throughput_data,
            **coverage_data
        }
        self.step_data.append(step_entry)
        
        # 添加到当前rollout数据
        if throughput_data.get('system_throughput_mbps') is not None:
            self.current_rollout_data['system_throughput'].append(throughput_data['system_throughput_mbps'])
        if throughput_data.get('avg_user_throughput_mbps') is not None:
            self.current_rollout_data['avg_user_throughput'].append(throughput_data['avg_user_throughput_mbps'])
        if throughput_data.get('served_users') is not None:
            self.current_rollout_data['served_users'].append(throughput_data['served_users'])
            self.current_rollout_data['total_users'].append(throughput_data.get('total_users', 0))
        if coverage_data.get('coverage_ratio') is not None:
            self.current_rollout_data['coverage_values'].append(coverage_data['coverage_ratio'])
        
        self.current_rollout_data['reward_values'].append(reward)
        
        # 实时TensorBoard记录（每100步记录一次以减少I/O）
        if self.total_steps % 100 == 0:
            self._log_realtime_tensorboard(writer, step)
    
    def _extract_throughput_info(self, info):
        """从info中提取吞吐量信息"""
        data = {}
        
        if 'reward_info' in info:
            reward_info = info['reward_info']
            
            # 系统吞吐量
            if 'system_throughput_mbps' in reward_info:
                data['system_throughput_mbps'] = reward_info['system_throughput_mbps']
            
            # 平均用户吞吐量
            if 'avg_throughput_per_user_mbps' in reward_info:
                data['avg_user_throughput_mbps'] = reward_info['avg_throughput_per_user_mbps']
            
            # 服务用户数
            if 'connected_users' in reward_info:
                data['served_users'] = reward_info['connected_users']
        
        # 兼容性检查
        if 'served_users' in info:
            data['served_users'] = info['served_users']
            data['total_users'] = info.get('total_users', 0)
        
        return data
    
    def _extract_coverage_info(self, info):
        """从info中提取覆盖率信息"""
        data = {}
        
        if 'coverage_ratio' in info:
            data['coverage_ratio'] = info['coverage_ratio']
        
        if 'connectivity_ratio' in info:
            data['connectivity_ratio'] = info['connectivity_ratio']
            
        return data
    
    def _log_realtime_tensorboard(self, writer, step):
        """实时记录到TensorBoard"""
        # 更新滑动窗口
        recent_data = self.step_data[-100:] if len(self.step_data) >= 100 else self.step_data
        
        if recent_data:
            # 吞吐量指标
            throughputs = [d.get('system_throughput_mbps') for d in recent_data if d.get('system_throughput_mbps') is not None]
            if throughputs:
                writer.add_scalar('Realtime/System_Throughput_Mbps_100steps', np.mean(throughputs), step)
                writer.add_scalar('Realtime/System_Throughput_Std_100steps', np.std(throughputs), step)
            
            # 用户吞吐量
            user_throughputs = [d.get('avg_user_throughput_mbps') for d in recent_data if d.get('avg_user_throughput_mbps') is not None]
            if user_throughputs:
                writer.add_scalar('Realtime/Avg_User_Throughput_Mbps_100steps', np.mean(user_throughputs), step)
            
            # 覆盖率
            coverages = [d.get('coverage_ratio') for d in recent_data if d.get('coverage_ratio') is not None]
            if coverages:
                writer.add_scalar('Realtime/Coverage_Ratio_100steps', np.mean(coverages), step)
                writer.add_scalar('Realtime/Coverage_Std_100steps', np.std(coverages), step)
            
            # 奖励
            rewards = [d['reward'] for d in recent_data]
            writer.add_scalar('Realtime/Reward_Mean_100steps', np.mean(rewards), step)
            writer.add_scalar('Realtime/Reward_Std_100steps', np.std(rewards), step)
    
    def log_rollout_completion(self, rollout_num, total_steps, writer):
        """记录rollout完成信息"""
        self.rollout_count += 1
        
        # 计算rollout汇总统计
        rollout_summary = {
            'rollout': rollout_num,
            'total_steps': total_steps,
            'timestamp': time.time(),
            'steps_in_rollout': len(self.current_rollout_data['reward_values'])
        }
        
        # 吞吐量统计
        if self.current_rollout_data['system_throughput']:
            rollout_summary.update({
                'avg_system_throughput_mbps': np.mean(self.current_rollout_data['system_throughput']),
                'std_system_throughput_mbps': np.std(self.current_rollout_data['system_throughput']),
                'max_system_throughput_mbps': np.max(self.current_rollout_data['system_throughput']),
                'min_system_throughput_mbps': np.min(self.current_rollout_data['system_throughput'])
            })
        
        if self.current_rollout_data['avg_user_throughput']:
            rollout_summary.update({
                'avg_user_throughput_mbps': np.mean(self.current_rollout_data['avg_user_throughput']),
                'std_user_throughput_mbps': np.std(self.current_rollout_data['avg_user_throughput'])
            })
        
        # 覆盖率统计
        if self.current_rollout_data['coverage_values']:
            rollout_summary.update({
                'avg_coverage_ratio': np.mean(self.current_rollout_data['coverage_values']),
                'std_coverage_ratio': np.std(self.current_rollout_data['coverage_values'])
            })
        
        # 服务用户统计
        if self.current_rollout_data['served_users']:
            served_users = np.array(self.current_rollout_data['served_users'])
            total_users = np.array(self.current_rollout_data['total_users'])
            rollout_summary.update({
                'avg_served_users': np.mean(served_users),
                'avg_total_users': np.mean(total_users),
                'avg_service_rate': np.mean(served_users) / max(np.mean(total_users), 1)
            })
        
        # 奖励统计
        rewards = self.current_rollout_data['reward_values']
        rollout_summary.update({
            'avg_reward': np.mean(rewards),
            'std_reward': np.std(rewards),
            'total_reward': np.sum(rewards)
        })
        
        # 保存rollout数据
        self.rollout_data.append(rollout_summary)
        
        # 记录到TensorBoard
        self._log_rollout_tensorboard(writer, rollout_summary, total_steps)
        
        # 定期导出详细数据
        if self.rollout_count % self.export_frequency == 0:
            self.export_detailed_data(total_steps)
        
        # 清空当前rollout数据
        self.current_rollout_data = {
            'throughput_values': [],
            'coverage_values': [],
            'reward_values': [],
            'served_users': [],
            'total_users': [],
            'system_throughput': [],
            'avg_user_throughput': []
        }
    
    def _log_rollout_tensorboard(self, writer, summary, step):
        """记录rollout汇总到TensorBoard"""
        # 吞吐量指标
        if 'avg_system_throughput_mbps' in summary:
            writer.add_scalar('Rollout/Avg_System_Throughput_Mbps', summary['avg_system_throughput_mbps'], step)
            writer.add_scalar('Rollout/Std_System_Throughput_Mbps', summary['std_system_throughput_mbps'], step)
            writer.add_scalar('Rollout/Max_System_Throughput_Mbps', summary['max_system_throughput_mbps'], step)
        
        if 'avg_user_throughput_mbps' in summary:
            writer.add_scalar('Rollout/Avg_User_Throughput_Mbps', summary['avg_user_throughput_mbps'], step)
        
        # 覆盖率指标
        if 'avg_coverage_ratio' in summary:
            writer.add_scalar('Rollout/Avg_Coverage_Ratio', summary['avg_coverage_ratio'], step)
            writer.add_scalar('Rollout/Std_Coverage_Ratio', summary['std_coverage_ratio'], step)
        
        # 服务用户指标
        if 'avg_served_users' in summary:
            writer.add_scalar('Rollout/Avg_Served_Users', summary['avg_served_users'], step)
            writer.add_scalar('Rollout/Avg_Service_Rate', summary['avg_service_rate'], step)
        
        # 奖励指标
        writer.add_scalar('Rollout/Avg_Reward', summary['avg_reward'], step)
        writer.add_scalar('Rollout/Total_Reward', summary['total_reward'], step)
        writer.add_scalar('Rollout/Steps_Count', summary['steps_in_rollout'], step)
    
    def log_episode_completion(self, episode_num, env_id, total_reward, episode_length, info):
        """记录episode完成"""
        self.episode_count += 1
        
        episode_entry = {
            'episode': episode_num,
            'env_id': env_id,
            'total_reward': total_reward,
            'episode_length': episode_length,
            'timestamp': time.time()
        }
        
        # 添加episode级别的性能指标
        if info:
            throughput_info = self._extract_throughput_info(info)
            coverage_info = self._extract_coverage_info(info)
            episode_entry.update(throughput_info)
            episode_entry.update(coverage_info)
        
        self.episode_data.append(episode_entry)
    
    def export_detailed_data(self, current_step):
        """导出详细数据到CSV"""
        export_dir = os.path.join(self.log_dir, 'paper_data')
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            # 导出步级数据
            if self.step_data:
                step_df = pd.DataFrame(self.step_data)
                step_df.to_csv(os.path.join(export_dir, f'step_data_{timestamp}_step_{current_step}.csv'), index=False)
            
            # 导出rollout汇总数据
            if self.rollout_data:
                rollout_df = pd.DataFrame(self.rollout_data)
                rollout_df.to_csv(os.path.join(export_dir, f'rollout_data_{timestamp}_step_{current_step}.csv'), index=False)
            
            # 导出episode数据
            if self.episode_data:
                episode_df = pd.DataFrame(self.episode_data)
                episode_df.to_csv(os.path.join(export_dir, f'episode_data_{timestamp}_step_{current_step}.csv'), index=False)
            
            main_logger.info(f"已导出详细数据到 {export_dir}，当前步数: {current_step}")
            
        except Exception as e:
            main_logger.error(f"导出数据时出错: {e}")
    
    def get_final_summary(self):
        """获取最终统计摘要"""
        summary = {
            'total_steps': self.total_steps,
            'total_rollouts': self.rollout_count,
            'total_episodes': self.episode_count,
            'export_frequency': self.export_frequency,
            'data_points_collected': len(self.step_data)
        }
        
        # 整体性能统计
        if self.rollout_data:
            # 吞吐量统计
            throughputs = [r.get('avg_system_throughput_mbps') for r in self.rollout_data if r.get('avg_system_throughput_mbps') is not None]
            if throughputs:
                summary.update({
                    'overall_avg_throughput_mbps': np.mean(throughputs),
                    'overall_std_throughput_mbps': np.std(throughputs),
                    'overall_max_throughput_mbps': np.max(throughputs),
                    'overall_min_throughput_mbps': np.min(throughputs)
                })
            
            # 覆盖率统计
            coverages = [r.get('avg_coverage_ratio') for r in self.rollout_data if r.get('avg_coverage_ratio') is not None]
            if coverages:
                summary.update({
                    'overall_avg_coverage': np.mean(coverages),
                    'overall_std_coverage': np.std(coverages)
                })
            
            # 奖励统计
            rewards = [r['avg_reward'] for r in self.rollout_data]
            summary.update({
                'overall_avg_reward': np.mean(rewards),
                'overall_std_reward': np.std(rewards)
            })
        
        return summary

def get_device(device_pref):
    """根据偏好选择计算设备"""
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

def make_env(scenario, n_uavs, n_users, user_distribution, channel_model, config=None, max_hops=None, render_mode=None, rank=0, seed=0):
    """创建环境实例的函数 (用于 SubprocVecEnv)"""
    def _init():
        env_seed = seed + rank
        if scenario == 1:
            raw_env = UAVBaseStationEnv(
                n_uavs=n_uavs,
                n_users=n_users,
                user_distribution=user_distribution,
                channel_model=channel_model,
                render_mode=render_mode,
                seed=env_seed
            )
        elif scenario == 2:
            reward_kwargs = {}
            if config is not None:
                reward_kwargs.update({
                    'coverage_weight': config.coverage_weight,
                    'quality_weight': config.quality_weight,
                    'connectivity_weight': config.connectivity_weight,
                    'throughput_weight': config.throughput_weight
                })
            
            raw_env = UAVCooperativeNetworkEnv(
                n_uavs=n_uavs,
                n_users=n_users,
                max_hops=max_hops,
                user_distribution=user_distribution,
                channel_model=channel_model,
                render_mode=render_mode,
                seed=env_seed,
                **reward_kwargs
            )
        else:
            raise ValueError(f"未知的场景: {scenario}")

        env = ParallelToArrayAdapter(raw_env, seed=env_seed)
        return env

    return _init

def parse_args():
    parser = argparse.ArgumentParser(description='优化的HMASD训练脚本，专门用于论文数据收集')
    
    # 基本参数
    parser.add_argument('--mode', type=str, default='train', help='运行模式: train或eval')
    parser.add_argument('--scenario', type=int, default=2, help='场景: 1=基站模式, 2=协作组网模式')
    parser.add_argument('--model_path', type=str, default='models/hmasd_paper_data.pt', help='模型保存/加载路径')
    parser.add_argument('--log_dir', type=str, default='logs', help='日志目录')
    parser.add_argument('--log_level', type=str, default='info', 
                        choices=['debug', 'info', 'warning', 'error', 'critical'], 
                        help='日志级别')
    parser.add_argument('--console_log_level', type=str, default='warning', 
                        choices=['debug', 'info', 'warning', 'error', 'critical'], 
                        help='控制台日志级别')
    parser.add_argument('--eval_episodes', type=int, default=10, help='评估的episode数量')
    parser.add_argument('--render', action='store_true', help='是否渲染环境')
    parser.add_argument('--device', type=str, default='auto', 
                        choices=['auto', 'cuda', 'cpu'], help='计算设备')

    # 环境参数
    parser.add_argument('--n_uavs', type=int, default=5, help='无人机数量')
    parser.add_argument('--n_users', type=int, default=50, help='用户数量')
    parser.add_argument('--max_hops', type=int, default=3, help='最大跳数')
    parser.add_argument('--user_distribution', type=str, default='uniform', 
                        choices=['uniform', 'cluster', 'hotspot'], help='用户分布类型')
    parser.add_argument('--channel_model', type=str, default='3gpp-36777',
                        choices=['free_space', 'urban', 'suburban','3gpp-36777'], help='信道模型')
    
    # 并行参数
    parser.add_argument('--num_envs', type=int, default=32, 
                        help='并行环境数量')
    parser.add_argument('--eval_rollout_threads', type=int, default=4, 
                        help='评估时的并行线程数')
    
    return parser.parse_args()

def train(vec_env, eval_vec_env, config, args, device):
    """训练HMASD代理，优化了数据收集"""
    num_envs = vec_env.num_envs
    main_logger.info(f"开始训练HMASD (论文数据收集版本，使用 {num_envs} 个并行环境)...")

    # 更新环境维度
    state_dim = vec_env.get_attr('state_dim')[0]
    obs_shape = vec_env.observation_space.shape
    if len(obs_shape) == 3:
         obs_dim = obs_shape[2]
         n_uavs_check = obs_shape[1]
         main_logger.info(f"从 observation_space 推断: obs_dim={obs_dim}, n_uavs={n_uavs_check}")
         if n_uavs_check != config.n_agents:
              main_logger.warning(f"从 observation_space 推断的 n_uavs ({n_uavs_check}) 与配置 ({config.n_agents}) 不匹配。")
              obs_dim = vec_env.get_attr('obs_dim')[0]
    else:
         main_logger.warning("无法从 observation_space 推断 obs_dim，尝试从适配器属性获取。")
         obs_dim = vec_env.get_attr('obs_dim')[0]

    config.update_env_dims(state_dim, obs_dim)
    main_logger.info(f"更新配置: state_dim={state_dim}, obs_dim={obs_dim}")

    # 创建日志目录
    log_dir = os.path.join(args.log_dir, f"paper_data_collection_{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(log_dir, exist_ok=True)
    model_dir = os.path.dirname(args.model_path)
    os.makedirs(model_dir, exist_ok=True)
    
    # 创建HMASD代理
    agent = HMASDAgent(config, log_dir=log_dir, device=device)
    
    # 创建专门的论文数据追踪器
    data_tracker = PaperDataTracker(log_dir, config, num_envs)
    
    # 记录配置到TensorBoard
    agent.writer.add_text('Config/n_agents', str(config.n_agents), 0)
    agent.writer.add_text('Config/num_envs', str(num_envs), 0)
    agent.writer.add_text('Config/rollout_length', str(config.rollout_length), 0)
    agent.writer.add_text('Config/export_frequency', str(data_tracker.export_frequency), 0)
    agent.writer.add_text('Config/scenario', str(args.scenario), 0)
    agent.writer.add_text('Config/n_users', str(args.n_users), 0)
    agent.writer.add_text('Config/channel_model', args.channel_model, 0)

    # 训练变量
    total_steps = 0
    n_episodes = 0
    rollout_count = 0
    episode_rewards = []
    update_times = 0
    best_reward = float('-inf')
    last_eval_step = 0
    
    start_time = time.time()

    # 重置所有环境
    main_logger.info("重置并行环境...")
    results = vec_env.env_method('reset')
    observations = np.array([res[0] for res in results])
    initial_infos = [res[1] for res in results]
    states = np.array([info.get('state', np.zeros(agent.config.state_dim)) for info in initial_infos])
    main_logger.info(f"环境已重置。观测形状: {observations.shape}, 状态形状: {states.shape}")

    # 环境状态跟踪
    env_steps = np.zeros(num_envs, dtype=int)
    env_rewards = np.zeros(num_envs)
    env_skill_durations = np.zeros(num_envs, dtype=int)
    
    while total_steps < config.total_timesteps:
        # 开始新的rollout
        rollout_start_step = total_steps
        
        # 收集rollout数据
        for rollout_step in range(config.rollout_length):
            # 代理为所有环境选择动作
            all_actions_list = []
            all_agent_infos_list = []

            for i in range(num_envs):
                actions, agent_info = agent.step(states[i], observations[i], env_steps[i], deterministic=False, env_id=i)
                all_actions_list.append(actions)
                all_agent_infos_list.append(agent_info)

            actions_array = np.array(all_actions_list)

            # 执行动作
            next_observations, rewards, dones, infos = vec_env.step(actions_array)
            next_states = np.array([info.get('next_state', np.zeros(state_dim)) for info in infos])

            # 存储经验到缓冲区
            for i in range(num_envs):
                current_agent_info = all_agent_infos_list[i]
                skill_timer_value = env_skill_durations[i]
                
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

                # 记录步级数据（移除detailed_logging限制）
                step_number = total_steps - num_envs + i + 1
                data_tracker.log_step_data(step_number, i, rewards[i], infos[i], agent.writer)

                # 处理episode完成
                if dones[i]:
                    n_episodes += 1
                    episode_rewards.append(env_rewards[i])

                    # 记录episode完成
                    episode_info = infos[i] if infos[i] else {}
                    data_tracker.log_episode_completion(
                        episode_num=n_episodes,
                        env_id=i,
                        total_reward=env_rewards[i],
                        episode_length=env_steps[i],
                        info=episode_info
                    )

                    # TensorBoard episode记录
                    agent.writer.add_scalar('Episode/Reward', env_rewards[i], n_episodes)
                    agent.writer.add_scalar('Episode/Length', env_steps[i], n_episodes)

                    main_logger.info(f"Episode {n_episodes} 完成 (环境 {i}): 奖励={env_rewards[i]:.2f}, 步数={env_steps[i]}")

                    # 重置环境状态跟踪
                    env_steps[i] = 0
                    env_rewards[i] = 0

            # 更新状态和观测
            states = next_states
            observations = next_observations
            total_steps += num_envs

            # 如果达到总步数限制，跳出rollout收集循环
            if total_steps >= config.total_timesteps:
                break

        # Rollout完成，记录rollout级别统计
        rollout_count += 1
        data_tracker.log_rollout_completion(rollout_count, total_steps, agent.writer)
        
        # 进行网络更新
        if len(agent.low_level_buffer) >= agent.config.batch_size:
            try:
                update_info = agent.update()
                update_times += 1
                elapsed = time.time() - start_time

                main_logger.info(f"Rollout {rollout_count} 更新完成, 总步数 {total_steps}, "
                      f"高层损失 {update_info['coordinator_loss']:.4f}, "
                      f"低层损失 {update_info['discoverer_loss']:.4f}, "
                      f"判别器损失 {update_info['discriminator_loss']:.4f}, "
                      f"已用时间 {elapsed:.2f}s")
                
                # 记录损失到TensorBoard
                agent.writer.add_scalar('Loss/Coordinator', update_info['coordinator_loss'], total_steps)
                agent.writer.add_scalar('Loss/Discoverer', update_info['discoverer_loss'], total_steps)
                agent.writer.add_scalar('Loss/Discriminator', update_info['discriminator_loss'], total_steps)
                
                # 清空缓冲区 (严格on-policy)
                agent.clear_buffers()
                
            except ValueError as e:
                main_logger.error(f"更新错误: {e}")
                update_times += 1
        else:
            main_logger.warning(f"缓冲区数据不足，跳过更新。当前缓冲区大小: {len(agent.low_level_buffer)}")

        # 评估
        if total_steps >= last_eval_step + config.eval_interval:
            main_logger.info(f"进行评估...")
            eval_reward, eval_std, eval_min, eval_max = evaluate(eval_vec_env, agent, config.eval_episodes)
            main_logger.info(f"评估完成: 平均奖励 {eval_reward:.2f} ± {eval_std:.2f}")

            # 记录评估结果
            agent.writer.add_scalar('Evaluation/Mean_Reward', eval_reward, total_steps)
            agent.writer.add_scalar('Evaluation/Std_Reward', eval_std, total_steps)
            agent.writer.add_scalar('Evaluation/Max_Reward', eval_max, total_steps)
            agent.writer.add_scalar('Evaluation/Min_Reward', eval_min, total_steps)

            # 保存最佳模型
            if eval_reward > best_reward:
                best_reward = eval_reward
                agent.save_model(args.model_path)
                main_logger.info(f"保存最佳模型，奖励: {best_reward:.2f}")
            
            last_eval_step = total_steps

    main_logger.info(f"训练完成! 总步数: {total_steps}, 总episodes: {n_episodes}, 总rollouts: {rollout_count}")

    # 最终数据导出
    data_tracker.export_detailed_data(total_steps)
    
    # 获取并保存最终统计摘要
    final_summary = data_tracker.get_final_summary()
    main_logger.info("\n===== 最终训练统计 =====")
    for key, value in final_summary.items():
        main_logger.info(f"{key}: {value}")
    
    # 保存摘要到JSON
    import json
    summary_path = os.path.join(log_dir, 'final_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(final_summary, f, indent=2)
    main_logger.info(f"最终摘要已保存到: {summary_path}")

    # 保存最终模型
    final_model_path = os.path.join(model_dir, 'hmasd_paper_data_final.pt')
    agent.save_model(final_model_path)
    main_logger.info(f"最终模型已保存到 {final_model_path}")
    
    return agent

def evaluate(vec_env, agent, n_episodes=10, render=False):
    """简化的评估函数"""
    num_envs = vec_env.num_envs
    main_logger.info(f"开始评估: {n_episodes} episodes，{num_envs} 环境")
    
    results = vec_env.env_method('reset')
    observations = np.array([res[0] for res in results])
    initial_infos = [res[1] for res in results]
    states = np.array([info.get('state', np.zeros(agent.config.state_dim)) for info in initial_infos])

    env_steps = np.zeros(num_envs, dtype=int)
    env_rewards = np.zeros(num_envs)
    active_envs = np.ones(num_envs, dtype=bool)
    completed_episodes = 0
    episode_rewards = []
    episode_lengths = []

    with torch.no_grad():
        while completed_episodes < n_episodes:
            all_actions_list = []
            all_agent_infos_list = []

            for i in range(num_envs):
                if active_envs[i]:
                    actions, agent_info = agent.step(states[i], observations[i], env_steps[i], deterministic=True, env_id=i)
                    all_actions_list.append(actions)
                    all_agent_infos_list.append(agent_info)
                else:
                    all_actions_list.append(np.zeros(vec_env.action_space.shape[1:]))
                    all_agent_infos_list.append({})

            actions_array = np.array(all_actions_list)
            next_observations, rewards, dones, infos = vec_env.step(actions_array)
            next_states = np.array([info.get('next_state', np.zeros(agent.config.state_dim)) for info in infos])

            for i in range(num_envs):
                if active_envs[i]:
                    env_steps[i] += 1
                    env_rewards[i] += rewards[i]

                    if dones[i]:
                        if completed_episodes < n_episodes:
                            episode_rewards.append(env_rewards[i])
                            episode_lengths.append(env_steps[i])
                            
                            main_logger.info(f"评估 Episode {completed_episodes+1}/{n_episodes}: 奖励={env_rewards[i]:.2f}, 步数={env_steps[i]}")
                            completed_episodes += 1

                        active_envs[i] = False

            states = next_states
            observations = next_observations

            if completed_episodes >= n_episodes:
                break
            if not np.any(active_envs):
                break

    mean_reward = np.mean(episode_rewards) if episode_rewards else 0
    std_reward = np.std(episode_rewards) if episode_rewards else 0
    min_reward = np.min(episode_rewards) if episode_rewards else 0
    max_reward = np.max(episode_rewards) if episode_rewards else 0

    return mean_reward, std_reward, min_reward, max_reward

def main():
    args = parse_args()
    
    # 创建日志目录
    os.makedirs(args.log_dir, exist_ok=True)
    
    # 初始化日志系统
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f"hmasd_paper_data_{timestamp}.log"
    
    file_level = LOG_LEVELS.get(args.log_level.lower(), logging.INFO)
    console_level = LOG_LEVELS.get(args.console_log_level.lower(), logging.WARNING)
    init_multiproc_logging(
        log_dir=args.log_dir, 
        log_file=log_file, 
        file_level=file_level, 
        console_level=console_level
    )
    
    global main_logger
    main_logger = get_logger("HMASD-PaperData")
    main_logger.info(f"论文数据收集系统已启动: 文件级别={args.log_level}, 控制台级别={args.console_log_level}")
    main_logger.info(f"并行环境数量: {args.num_envs}, 评估环境: {args.eval_rollout_threads}")
    
    config = Config()
    device = get_device(args.device)
    
    # 创建环境
    base_seed = getattr(config, 'seed', int(time.time()))
    main_logger.info(f"基础种子: {base_seed}")

    train_env_fns = [make_env(
        scenario=args.scenario,
        n_uavs=args.n_uavs,
        n_users=args.n_users,
        user_distribution=args.user_distribution,
        channel_model=args.channel_model,
        config=config,
        max_hops=args.max_hops if args.scenario == 2 else None,
        render_mode=None,
        rank=i,
        seed=base_seed
    ) for i in range(args.num_envs)]

    eval_env_fns = [make_env(
        scenario=args.scenario,
        n_uavs=args.n_uavs,
        n_users=args.n_users,
        user_distribution=args.user_distribution,
        channel_model=args.channel_model,
        config=config,
        max_hops=args.max_hops if args.scenario == 2 else None,
        render_mode="human" if args.render and i == 0 else None,
        rank=i,
        seed=base_seed + args.num_envs
    ) for i in range(args.eval_rollout_threads)]

    # 创建向量化环境
    main_logger.info("创建 SubprocVecEnv...")
    train_vec_env = SubprocVecEnv(train_env_fns, start_method='spawn')
    eval_vec_env = SubprocVecEnv(eval_env_fns, start_method='spawn')
    main_logger.info("环境创建完成")

    # 更新配置
    try:
         n_agents_from_env = train_vec_env.get_attr('n_uavs')[0]
         config.n_agents = n_agents_from_env
         main_logger.info(f"从环境更新智能体数量: n_agents={config.n_agents}")
    except Exception as e:
         main_logger.warning(f"无法从环境获取 n_uavs: {e}. 使用命令行参数: {args.n_uavs}")
         config.n_agents = args.n_uavs

    if args.mode == 'train':
        agent = train(train_vec_env, eval_vec_env, config, args, device)
    elif args.mode == 'eval':
        if not os.path.exists(args.model_path):
            main_logger.error(f"模型文件 {args.model_path} 不存在")
            return
        
        log_dir = os.path.join(args.log_dir, f"eval_paper_data_{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        os.makedirs(log_dir, exist_ok=True)
        
        agent = HMASDAgent(config, log_dir=log_dir, device=device)
        agent.load_model(args.model_path)
        
        evaluate(eval_vec_env, agent, n_episodes=args.eval_episodes, render=args.render)
    else:
        main_logger.error(f"未知运行模式: {args.mode}")
    
    # 关闭环境
    train_vec_env.close()
    eval_vec_env.close()

if __name__ == "__main__":
    mp.set_start_method('spawn', force=True)
    try:
        main()
    finally:
        try:
            shutdown_logging()
            print("日志系统已关闭")
        except Exception as e:
            print(f"关闭日志系统时出错: {e}")
