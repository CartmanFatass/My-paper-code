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
from envs.pettingzoo.scenario4 import UAVForcedRelayEnv
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from torch.utils.tensorboard import SummaryWriter

class TensorBoardManager:
    """统一的TensorBoard管理器 - 处理从agent.py移除的所有TensorBoard写入逻辑"""
    
    def __init__(self, log_dir, config):
        self.log_dir = log_dir
        self.config = config
        self.writer = SummaryWriter(log_dir)
        
        # 记录配置参数到TensorBoard
        self._log_config_parameters()
    
    def _log_config_parameters(self):
        """记录配置参数到TensorBoard"""
        # 基础参数
        self.writer.add_text('Parameters/n_agents', str(self.config.n_agents), 0)
        self.writer.add_text('Parameters/n_Z', str(self.config.n_Z), 0)
        self.writer.add_text('Parameters/n_z', str(self.config.n_z), 0)
        self.writer.add_text('Parameters/k', str(self.config.k), 0)
        self.writer.add_text('Parameters/gamma', str(self.config.gamma), 0)
        self.writer.add_text('Parameters/lambda_e', str(self.config.lambda_e), 0)
        self.writer.add_text('Parameters/lambda_D', str(self.config.lambda_D), 0)
        self.writer.add_text('Parameters/lambda_d', str(self.config.lambda_d), 0)
        self.writer.add_text('Parameters/lambda_h', str(self.config.lambda_h), 0)
        self.writer.add_text('Parameters/lambda_l', str(self.config.lambda_l), 0)
        self.writer.add_text('Parameters/hidden_size', str(self.config.hidden_size), 0)
        self.writer.add_text('Parameters/lr_coordinator', str(self.config.lr_coordinator), 0)
        self.writer.add_text('Parameters/lr_discoverer', str(self.config.lr_discoverer), 0)
        self.writer.add_text('Parameters/lr_discriminator', str(self.config.lr_discriminator), 0)
        
        # 高级功能参数
        self.writer.add_text('Parameters/use_opt', str(self.config.use_opt), 0)
        self.writer.add_text('Parameters/use_reward_annealing', str(getattr(self.config, 'use_reward_annealing', False)), 0)
        self.writer.add_text('Parameters/use_lr_decay', str(getattr(self.config, 'use_lr_decay', False)), 0)
        self.writer.add_text('Parameters/use_valuenorm', str(getattr(self.config, 'use_valuenorm', False)), 0)
        
        # OPT相关参数
        if self.config.use_opt:
            self.writer.add_text('Parameters/lambda_cd', str(getattr(self.config, 'lambda_cd', 0.1)), 0)
        
        # 权重退火相关参数
        if getattr(self.config, 'use_reward_annealing', False):
            self.writer.add_text('Parameters/w_intrinsic_initial', str(getattr(self.config, 'w_intrinsic_initial', 3.0)), 0)
            self.writer.add_text('Parameters/w_intrinsic_final', str(getattr(self.config, 'w_intrinsic_final', 1.0)), 0)
            self.writer.add_text('Parameters/w_extrinsic_initial', str(getattr(self.config, 'w_extrinsic_initial', 0.5)), 0)
            self.writer.add_text('Parameters/w_extrinsic_final', str(getattr(self.config, 'w_extrinsic_final', 1.5)), 0)
            self.writer.add_text('Parameters/anneal_steps', str(getattr(self.config, 'anneal_steps', 1000000)), 0)
            self.writer.add_text('Parameters/anneal_schedule', str(getattr(self.config, 'anneal_schedule', 'linear')), 0)

        # 学习率衰减相关参数
        if getattr(self.config, 'use_lr_decay', False):
            self.writer.add_text('Parameters/lr_decay_schedule', str(getattr(self.config, 'lr_decay_schedule', 'linear')), 0)
            self.writer.add_text('Parameters/lr_decay_steps', str(getattr(self.config, 'lr_decay_steps', 100000)), 0)
            self.writer.add_text('Parameters/coordinator_lr_decay_factor', str(getattr(self.config, 'coordinator_lr_decay_factor', 0.1)), 0)
            self.writer.add_text('Parameters/discoverer_lr_decay_factor', str(getattr(self.config, 'discoverer_lr_decay_factor', 0.1)), 0)
            self.writer.add_text('Parameters/discriminator_lr_decay_factor', str(getattr(self.config, 'discriminator_lr_decay_factor', 0.1)), 0)
    
    def log_training_metrics(self, step, update_info, args=None):
        """记录训练指标到TensorBoard"""
        # 基础损失
        self.writer.add_scalar('Losses/Coordinator/Total', update_info['coordinator_loss'], step)
        self.writer.add_scalar('Losses/Discoverer/Total', update_info['discoverer_loss'], step)
        self.writer.add_scalar('Losses/Discriminator/Total', update_info['discriminator_loss'], step)
        
        # 详细损失组成
        self.writer.add_scalar('Losses/Coordinator/Policy', update_info['coordinator_policy_loss'], step)
        self.writer.add_scalar('Losses/Coordinator/Value', update_info['coordinator_value_loss'], step)
        self.writer.add_scalar('Losses/Discoverer/Policy', update_info['discoverer_policy_loss'], step)
        self.writer.add_scalar('Losses/Discoverer/Value', update_info['discoverer_value_loss'], step)
        
        # 熵记录
        self.writer.add_scalar('Entropy/Coordinator/TeamSkill_Z', update_info['team_skill_entropy'], step)
        self.writer.add_scalar('Entropy/Coordinator/AgentSkill_z_Average', update_info['agent_skill_entropy'], step)
        self.writer.add_scalar('Entropy/Discoverer/Action', update_info['action_entropy'], step)

        # 奖励记录
        self.writer.add_scalar('Rewards/HighLevel/K_Step_Accumulated_Mean', update_info['mean_high_level_reward'], step)
        
        # 内在奖励记录
        self.writer.add_scalar('Rewards/Intrinsic/LowLevel_Average', update_info['avg_intrinsic_reward'], step)
        self.writer.add_scalar('Rewards/Intrinsic/Components/Environmental_Portion_Average', update_info['avg_env_comp'], step)
        self.writer.add_scalar('Rewards/Intrinsic/Components/TeamDiscriminator_Portion_Average', update_info['avg_team_disc_comp'], step)
        self.writer.add_scalar('Rewards/Intrinsic/Components/IndividualDiscriminator_Portion_Average', update_info['avg_ind_disc_comp'], step)

        # 价值函数估计记录
        self.writer.add_scalar('ValueEstimates/Coordinator/StateValue_Mean', update_info['mean_coord_state_val'], step)
        self.writer.add_scalar('ValueEstimates/Coordinator/AgentValue_Average_Mean', update_info['mean_coord_agent_val'], step)
        self.writer.add_scalar('ValueEstimates/Discoverer/Value_Mean', update_info['avg_discoverer_val'], step)

        # CD Loss
        if 'cd_loss' in update_info:
            self.writer.add_scalar('Losses/Coordinator/CD_Loss', update_info['cd_loss'], step)

        # 记录关键超参数
        self.writer.add_scalar('Parameters/Lambda_D', self.config.lambda_D, step)
        self.writer.add_scalar('Parameters/Lambda_d', self.config.lambda_d, step)
        self.writer.add_scalar('Parameters/Lambda_h', self.config.lambda_h, step)
        self.writer.add_scalar('Parameters/Lambda_l', self.config.lambda_l, step)
    
    def log_annealing_stats(self, step, annealing_stats):
        """记录权重退火信息到TensorBoard"""
        if not annealing_stats:
            return
            
        self.writer.add_scalar('RewardAnnealing/Progress', annealing_stats['progress'], step)
        self.writer.add_scalar('RewardAnnealing/Progress_Adjusted', annealing_stats['progress_adjusted'], step)
        self.writer.add_scalar('RewardAnnealing/Intrinsic_Weight_Multiplier', annealing_stats['w_intrinsic_current'], step)
        self.writer.add_scalar('RewardAnnealing/Extrinsic_Weight_Multiplier', annealing_stats['w_extrinsic_current'], step)
        
        # 记录实际生效的权重
        self.writer.add_scalar('RewardAnnealing/Effective_Lambda_D', annealing_stats['effective_lambda_D'], step)
        self.writer.add_scalar('RewardAnnealing/Effective_Lambda_d', annealing_stats['effective_lambda_d'], step)
        self.writer.add_scalar('RewardAnnealing/Effective_Lambda_e', annealing_stats['effective_lambda_e'], step)
    
    def log_learning_rates(self, step, learning_rates):
        """记录学习率到TensorBoard"""
        self.writer.add_scalar('LearningRate/Coordinator', learning_rates['coordinator_lr'], step)
        self.writer.add_scalar('LearningRate/Discoverer', learning_rates['discoverer_lr'], step)
        self.writer.add_scalar('LearningRate/Discriminator', learning_rates['discriminator_lr'], step)
    
    def log_value_norm_stats(self, step, value_norm_stats):
        """记录Value Normalization统计信息到TensorBoard"""
        if 'coordinator' in value_norm_stats:
            coord_stats = value_norm_stats['coordinator']
            self.writer.add_scalar('ValueNorm/Coordinator/Mean', coord_stats['mean'], step)
            self.writer.add_scalar('ValueNorm/Coordinator/Std', coord_stats['std'], step)
            self.writer.add_scalar('ValueNorm/Coordinator/Count', coord_stats['count'], step)
        
        if 'discoverer' in value_norm_stats:
            disc_stats = value_norm_stats['discoverer']
            self.writer.add_scalar('ValueNorm/Discoverer/Mean', disc_stats['mean'], step)
            self.writer.add_scalar('ValueNorm/Discoverer/Std', disc_stats['std'], step)
            self.writer.add_scalar('ValueNorm/Discoverer/Count', disc_stats['count'], step)
    
    def log_episode_completion(self, episode_num, env_id, total_reward, episode_length):
        """记录episode完成信息"""
        self.writer.add_scalar('Reward/episode_reward', total_reward, episode_num)
        self.writer.add_scalar('Reward/episode_length', episode_length, episode_num)
    
    def log_skill_distribution(self, team_skill, agent_skills, step=None, episode=None):
        """记录技能分配分布到TensorBoard"""
        use_step = episode if episode is not None else step
        if use_step is None:
            return
            
        # 记录当前团队技能
        self.writer.add_scalar('Skills/Current/TeamSkill', team_skill, use_step)
        
        # 记录当前个体技能分布
        for i, skill_val in enumerate(agent_skills):
            self.writer.add_scalar(f'Skills/Current/Agent{i}_Skill', skill_val, use_step)
        
        # 计算并记录当前个体技能的多样性
        if len(agent_skills) > 0:
            current_skill_counts = {}
            for skill_val in agent_skills:
                current_skill_counts[skill_val] = current_skill_counts.get(skill_val, 0) + 1
            
            n_agents_current = len(agent_skills)
            current_skill_entropy = 0
            for count in current_skill_counts.values():
                p = count / n_agents_current
                if p > 0:
                    current_skill_entropy -= p * np.log(p)
            self.writer.add_scalar('Skills/Current/Diversity', current_skill_entropy, use_step)
    
    def add_text(self, tag, text_string, global_step=None):
        """添加文本到TensorBoard"""
        self.writer.add_text(tag, text_string, global_step)
    
    def add_scalar(self, tag, scalar_value, global_step=None):
        """添加标量到TensorBoard"""
        self.writer.add_scalar(tag, scalar_value, global_step)
    
    def flush(self):
        """刷新TensorBoard写入"""
        self.writer.flush()
    
    def close(self):
        """关闭TensorBoard writer"""
        self.writer.close()

# Removed VectorizedEnvAdapter class

class TrajectoryRecorder:
    """轨迹记录管理器 - 完整记录每一步的轨迹数据"""
    
    def __init__(self, config):
        # 启用完整记录模式，记录每一步
        self.full_recording_mode = getattr(config, 'full_trajectory_recording', True)
        self.enable_trajectory_smoothing = getattr(config, 'enable_trajectory_smoothing', True)
        
        # 保留原有配置以保持兼容性
        self.interval = getattr(config, 'trajectory_record_interval', 1)  # 默认每步记录
        self.max_points = getattr(config, 'max_trajectory_points', 10000)  # 增大限制
        self.enable_points = getattr(config, 'enable_trajectory_points', True)
        self.point_size = getattr(config, 'trajectory_point_size', 3)
        self.record_skill_changes = getattr(config, 'record_skill_change_points', True)
        self.record_episode_end = getattr(config, 'record_episode_end', True)
        
        # 记录状态
        self.last_recorded_step = {}  # 每个环境上次记录的步数
        self.trajectory_counts = {}   # 每个环境的轨迹点计数
    
    def should_record(self, env_id, current_step, skill_changed=False, episode_end=False):
        """判断是否应该记录轨迹点 - 完整记录模式下每步都记录"""
        if self.full_recording_mode:
            # 完整记录模式：每步都记录
            return True
        
        # 保留原有逻辑以保持兼容性
        if episode_end and self.record_episode_end:
            return True
        
        if skill_changed and self.record_skill_changes:
            return True
        
        # 第一步总是记录
        if env_id not in self.last_recorded_step:
            self.last_recorded_step[env_id] = current_step
            self.trajectory_counts[env_id] = 1
            return True
        
        # 检查轨迹点数量限制
        if self.trajectory_counts.get(env_id, 0) >= self.max_points:
            return False
        
        # 间隔检查
        steps_since_last = current_step - self.last_recorded_step[env_id]
        if steps_since_last >= self.interval:
            self.last_recorded_step[env_id] = current_step
            self.trajectory_counts[env_id] = self.trajectory_counts.get(env_id, 0) + 1
            return True
        
        return False
    
    def reset_env(self, env_id):
        """重置环境的记录状态 - episode完成后清除数据"""
        self.last_recorded_step.pop(env_id, None)
        self.trajectory_counts.pop(env_id, None)

class EnhancedRewardTracker:
    """增强的奖励追踪器，用于论文数据收集 - 存储空间优化版本"""
    
    def __init__(self, log_dir, config, n_users=None):
        self.log_dir = log_dir
        self.config = config
        self.n_users = n_users  # 存储用户总数，用于准确计算服务率
        
        # === 存储优化配置 ===
        self.paper_data_level = getattr(config, 'paper_data_level', 'standard')
        self.enable_data_sampling = getattr(config, 'enable_data_sampling', True)
        self.data_sampling_interval = getattr(config, 'data_sampling_interval', 50)  # 增加采样间隔
        self.enable_data_aggregation = getattr(config, 'enable_data_aggregation', True)
        self.enable_incremental_export = getattr(config, 'enable_incremental_export', True)
        self.max_step_data_buffer = getattr(config, 'max_step_data_buffer', 500)  # 减少缓冲区大小
        self.auto_clear_old_data = getattr(config, 'auto_clear_old_data', True)
        self.enable_data_compression = getattr(config, 'enable_data_compression', True)  # 启用压缩
        self.max_export_files = getattr(config, 'max_export_files', 10)  # 限制导出文件数量
        
        # === 选择性数据收集控制 ===
        self.collect_step_rewards = getattr(config, 'collect_step_rewards', False)
        self.collect_skill_diversity = getattr(config, 'collect_skill_diversity', True)
        self.collect_performance_metrics = getattr(config, 'collect_performance_metrics', True)
        self.collect_reward_components = getattr(config, 'collect_reward_components', False)
        
        # === 优化后的数据结构 ===
        if self.paper_data_level == 'minimal':
            # 最小模式：只保留核心统计信息
            self.training_rewards = {
                'episode_rewards': [],  # 只保留episode级别的奖励
                'episodes_completed': 0,
                'total_steps': 0
            }
        elif self.paper_data_level == 'standard':
            # 标准模式：保留重要信息但减少详细数据
            self.training_rewards = {
                'episode_rewards': [],
                'step_rewards': deque(maxlen=self.max_step_data_buffer) if self.collect_step_rewards else [],
                'reward_components': {
                    'env_component': deque(maxlen=self.max_step_data_buffer//2),
                    'team_disc_component': deque(maxlen=self.max_step_data_buffer//2),
                    'ind_disc_component': deque(maxlen=self.max_step_data_buffer//2)
                } if self.collect_reward_components else {},
                'reward_variance': [],
                'episodes_completed': 0,
                'total_steps': 0
            }
        else:  # detailed
            # 详细模式：保留所有数据（原始行为）
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
        
        # 数据聚合缓冲区 - 用于解决并行环境数据堆积问题
        self.step_metric_buffer = defaultdict(list)
        self.last_tensorboard_step = 0  # 记录上次记录TensorBoard的步数
        
        # === 数据采样控制 ===
        self.sample_counter = 0  # 采样计数器
        self.last_exported_episode = 0  # 上次导出的episode数
        
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
                'coverage_ratios': [],    # 覆盖率比例
                
                # 场景4发现机制指标
                'discovery_reward': [],
                'weighted_discovery_reward': [],
                'discovered_users_count': []
            }
        }
        
        # 滑动窗口统计 - 使用rollout_length作为窗口大小
        self.window_size = config.rollout_length
        self.recent_rewards = deque(maxlen=self.window_size)
        self.recent_lengths = deque(maxlen=self.window_size)
        
        # 数据导出设置 - 增加导出间隔
        self.export_interval = 5000  # 每5000步导出一次数据（减少导出频率）
        self.last_export_step = 0
        
        # 数据聚合缓冲区 - 用于存储聚合后的数据
        self.aggregated_episode_data = []
        self.aggregated_performance_data = []
        
        # 清理控制
        self.last_cleanup_step = 0
        self.cleanup_interval = 50000  # 每50000步清理一次旧数据
        
    def _log_aggregated_metrics(self, writer, step, data_list, metric_name, category="Training", 
                               recent_window=None, value_field='value'):
        """
        辅助函数：处理数据聚合并写入TensorBoard - 简化版本，只记录平均值
        
        参数:
            writer: TensorBoard writer
            step: 当前步数
            data_list: 包含数据的列表
            metric_name: 指标名称
            category: TensorBoard分类
            recent_window: 最近数据窗口大小 (如果为None，使用rollout_length)
            value_field: 数据字段名
        """
        if not data_list:
            return
        
        # 使用rollout_length作为默认窗口大小
        if recent_window is None:
            recent_window = self.config.rollout_length
            
        # 获取最近的数据
        recent_data = data_list[-recent_window:]
        if not recent_data:
            return
            
        # 按环境分组并聚合（简化版本：只计算平均值）
        try:
            # 构建DataFrame
            df_data = []
            for entry in recent_data:
                if isinstance(entry, dict):
                    step_value = entry.get('step', step)
                    env_id = entry.get('env_id', 0)
                    value = entry.get(value_field, 0)
                    df_data.append({
                        'step': step_value,
                        'env_id': env_id,
                        'value': value
                    })
            
            if not df_data:
                return
                
            df = pd.DataFrame(df_data)
            
            # 按env_id分组，先计算每个环境的内部平均值
            env_aggregated = df.groupby('env_id')['value'].mean().reset_index()
            
            if len(env_aggregated) == 0:
                return
                
            # 计算跨环境的最终平均值
            env_mean_values = env_aggregated['value'].values
            final_mean = np.mean(env_mean_values)  # 跨环境平均
            
            # 只写入TensorBoard平均值 - 使用rollout标识
            writer.add_scalar(f'{category}/{metric_name}_Mean_Rollout', final_mean, step)
                
        except Exception as e:
            main_logger.warning(f"聚合指标 {metric_name} 时出错: {e}")
            # 添加更详细的错误信息用于调试
            try:
                main_logger.debug(f"聚合错误详情 - 数据形状: {df.shape if 'df' in locals() else 'df未定义'}, "
                                 f"recent_data长度: {len(recent_data) if recent_data else 0}, "
                                 f"metric_name: {metric_name}, category: {category}")
            except:
                pass  # 避免调试信息本身出错
    
    def log_training_step(self, step, env_id, reward, reward_components=None, info=None):
        """记录训练步骤的奖励信息 - 存储优化版本"""
        self.training_rewards['total_steps'] += 1
        
        # === 数据采样逻辑 ===
        self.sample_counter += 1
        should_record_step = True
        
        if self.enable_data_sampling:
            # 只在采样间隔时记录详细的步级数据
            should_record_step = (self.sample_counter % self.data_sampling_interval == 0)
        
        # === 记录步级数据（根据采样策略和数据级别） ===
        if should_record_step and self.collect_step_rewards:
            if isinstance(self.training_rewards['step_rewards'], list):
                # 详细模式：正常列表
                self.training_rewards['step_rewards'].append({
                    'step': step,
                    'env_id': env_id,
                    'reward': reward,
                    'timestamp': time.time(),
                    'info': info if self.paper_data_level == 'detailed' else None  # 最小模式下不保存info
                })
            elif hasattr(self.training_rewards['step_rewards'], 'append'):
                # 标准模式：有界队列
                self.training_rewards['step_rewards'].append({
                    'step': step,
                    'env_id': env_id,
                    'reward': reward,
                    'timestamp': time.time(),
                    'info': None  # 标准模式下不保存详细info
                })
        
        if reward_components:
            for comp_name, comp_value in reward_components.items():
                if comp_name in self.training_rewards['reward_components']:
                    self.training_rewards['reward_components'][comp_name].append({
                        'step': step,
                        'env_id': env_id,
                        'value': comp_value
                    })
        
        # 记录额外信息（修正为仅在找到有效数据时记录，避免错误地记录0）
        if info and 'reward_info' in info:
            reward_info = info['reward_info']
            served_users = None  # 初始化为 None，表示"未找到"
            
            # 严格优先使用 'effective_connected_users'
            if 'effective_connected_users' in reward_info:
                served_users = reward_info['effective_connected_users']
            elif 'connected_users' in reward_info:
                # 如果没有 effective_connected_users，则回退到 connected_users
                served_users = reward_info['connected_users']
            
            # 只有在成功获取到 served_users 值 (不为 None) 时才记录
            if served_users is not None:
                self.performance_metrics['served_users'].append({
                    'step': step,
                    'env_id': env_id,
                    'served_users': served_users,
                    'total_users': self.n_users  # 使用固定的n_users
                })
            
            # 场景4特有指标：覆盖栅格数 (从info根部获取)
            if 'covered_grids' in info:
                # 确保 covered_grids 列表存在
                if 'covered_grids' not in self.performance_metrics['reward_components']:
                    self.performance_metrics['reward_components']['covered_grids'] = []
                
                self.performance_metrics['reward_components']['covered_grids'].append({
                    'step': step,
                    'env_id': env_id,
                    'value': info['covered_grids'],
                    'timestamp': time.time()
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
                
                # 场景4特有指标：探索奖励
                if 'exploration_reward' in reward_info:
                    # 确保 exploration_rewards 列表存在
                    if 'exploration_rewards' not in self.performance_metrics['reward_components']:
                        self.performance_metrics['reward_components']['exploration_rewards'] = []
                    
                    self.performance_metrics['reward_components']['exploration_rewards'].append({
                        'step': step,
                        'env_id': env_id,
                        'value': reward_info['exploration_reward'],
                        'timestamp': time.time()
                    })
                
                # 场景4特有指标：覆盖重叠惩罚
                if 'coverage_overlap_penalty' in reward_info:
                    # 确保 coverage_overlap_penalty 列表存在
                    if 'coverage_overlap_penalty' not in self.performance_metrics['reward_components']:
                        self.performance_metrics['reward_components']['coverage_overlap_penalty'] = []
                    
                    self.performance_metrics['reward_components']['coverage_overlap_penalty'].append({
                        'step': step,
                        'env_id': env_id,
                        'value': reward_info['coverage_overlap_penalty'],
                        'timestamp': time.time()
                    })
                
                # 场景4新增：Reward Shaping机制
                if 'connectivity_shaping_reward' in reward_info:
                    if 'connectivity_shaping_reward' not in self.performance_metrics['reward_components']:
                        self.performance_metrics['reward_components']['connectivity_shaping_reward'] = []
                    self.performance_metrics['reward_components']['connectivity_shaping_reward'].append({
                        'step': step, 'env_id': env_id, 'value': reward_info['connectivity_shaping_reward'], 'timestamp': time.time()
                    })
                
                if 'quality_shaping_reward' in reward_info:
                    if 'quality_shaping_reward' not in self.performance_metrics['reward_components']:
                        self.performance_metrics['reward_components']['quality_shaping_reward'] = []
                    self.performance_metrics['reward_components']['quality_shaping_reward'].append({
                        'step': step, 'env_id': env_id, 'value': reward_info['quality_shaping_reward'], 'timestamp': time.time()
                    })
                
                if 'distance_overlap_penalty' in reward_info:
                    if 'distance_overlap_penalty' not in self.performance_metrics['reward_components']:
                        self.performance_metrics['reward_components']['distance_overlap_penalty'] = []
                    self.performance_metrics['reward_components']['distance_overlap_penalty'].append({
                        'step': step, 'env_id': env_id, 'value': reward_info['distance_overlap_penalty'], 'timestamp': time.time()
                    })
                
                # 其他有用指标
                if 'avg_hops' in reward_info:
                    self.performance_metrics['reward_components']['avg_hops'].append({
                        'step': step,
                        'env_id': env_id,
                        'value': reward_info['avg_hops'],
                        'timestamp': time.time()
                    })
                
                if 'coverage_ratio' in reward_info:
                    self.performance_metrics['reward_components']['coverage_ratios'].append({
                        'step': step,
                        'env_id': env_id,
                        'value': reward_info['coverage_ratio'],
                        'timestamp': time.time()
                    })
                
                # 确保使用瞬时有效连接用户数
                if 'effective_connected_users' in reward_info:
                    self.performance_metrics['reward_components']['connected_users'].append({
                        'step': step,
                        'env_id': env_id,
                        'value': reward_info['effective_connected_users'],
                        'timestamp': time.time()
                    })
                
                # 场景4发现机制指标
                if 'discovery_reward' in reward_info:
                    self.performance_metrics['reward_components']['discovery_reward'].append({
                        'step': step, 'env_id': env_id, 'value': reward_info['discovery_reward'], 'timestamp': time.time()
                    })
                if 'weighted_discovery_reward' in reward_info:
                    self.performance_metrics['reward_components']['weighted_discovery_reward'].append({
                        'step': step, 'env_id': env_id, 'value': reward_info['weighted_discovery_reward'], 'timestamp': time.time()
                    })
                if 'discovered_users_count' in reward_info:
                    self.performance_metrics['reward_components']['discovered_users_count'].append({
                        'step': step, 'env_id': env_id, 'value': reward_info['discovered_users_count'], 'timestamp': time.time()
                    })
                
                # 场景4新增：潜能奖励
                if 'potential_reward' in reward_info:
                    if 'potential_reward' not in self.performance_metrics['reward_components']:
                        self.performance_metrics['reward_components']['potential_reward'] = []
                    self.performance_metrics['reward_components']['potential_reward'].append({
                        'step': step, 'env_id': env_id, 'value': reward_info['potential_reward'], 'timestamp': time.time()
                    })
                
                if 'weighted_potential_reward' in reward_info:
                    if 'weighted_potential_reward' not in self.performance_metrics['reward_components']:
                        self.performance_metrics['reward_components']['weighted_potential_reward'] = []
                    self.performance_metrics['reward_components']['weighted_potential_reward'].append({
                        'step': step, 'env_id': env_id, 'value': reward_info['weighted_potential_reward'], 'timestamp': time.time()
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
    
    def _cleanup_old_export_files(self, export_dir):
        """清理旧的导出文件，保持文件数量在限制范围内"""
        try:
            import glob
            
            # 获取所有导出文件
            files = []
            patterns = ['episode_rewards_*.csv*', 'reward_components_*.csv*', 'skill_usage_*.json']
            
            for pattern in patterns:
                files.extend(glob.glob(os.path.join(export_dir, pattern)))
            
            if len(files) <= self.max_export_files:
                return
            
            # 按修改时间排序，删除最旧的文件
            files.sort(key=os.path.getmtime)
            files_to_delete = files[:-self.max_export_files]
            
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    main_logger.debug(f"已删除旧导出文件: {file_path}")
                except Exception as e:
                    main_logger.warning(f"删除文件 {file_path} 失败: {e}")
                    
            main_logger.info(f"清理完成，删除了 {len(files_to_delete)} 个旧文件，保留 {len(files) - len(files_to_delete)} 个最新文件")
            
        except Exception as e:
            main_logger.error(f"清理旧导出文件时出错: {e}")
    
    def _export_minimal_data(self, step, writer=None, args=None):
        """最小模式数据导出 - 只导出核心统计信息"""
        try:
            export_dir = '../autodl-tmp/paper_data'
            os.makedirs(export_dir, exist_ok=True)
            
            # 只导出episode级别的统计摘要
            summary_data = {
                'timestamp': time.time(),
                'step': step,
                'total_episodes': self.training_rewards['episodes_completed'],
                'total_steps': self.training_rewards['total_steps'],
                'skill_switches': self.skill_usage['skill_switches']
            }
            
            # 添加奖励统计（如果有数据）
            if self.training_rewards['episode_rewards']:
                rewards = [r['total_reward'] for r in self.training_rewards['episode_rewards']]
                summary_data.update({
                    'reward_mean': np.mean(rewards),
                    'reward_std': np.std(rewards),
                    'reward_min': np.min(rewards),
                    'reward_max': np.max(rewards),
                    'recent_10_reward_mean': np.mean(rewards[-self.window_size:]) if len(rewards) >= self.window_size else np.mean(rewards)
                })
            
            # 导出到JSON文件
            import json
            filename = f'training_summary_minimal_step_{step}.json'
            filepath = os.path.join(export_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(summary_data, f, indent=2)
            
            main_logger.debug(f"最小模式数据已导出: {filepath}")
            
            # 记录到TensorBoard（如果提供）
            if writer:
                self.log_to_tensorboard(writer, step, args=args)
                
        except Exception as e:
            main_logger.error(f"最小模式数据导出失败: {e}")
    
    def export_training_data(self, step, writer=None, args=None):
        """导出训练数据用于论文分析 - 存储优化版本"""
        # 应用配置中的导出间隔倍数
        effective_export_interval = self.export_interval * getattr(self.config, 'export_interval_multiplier', 1)
        
        if step - self.last_export_step < effective_export_interval:
            return
        
        # 如果是最小模式，只导出基础统计信息
        if self.paper_data_level == 'minimal':
            self._export_minimal_data(step, writer, args)
            return
        
        # 原始导出目录
        export_dir = '../autodl-tmp/paper_data'
        os.makedirs(export_dir, exist_ok=True)
        
        # === 数据轮转管理 ===
        if self.max_export_files > 0:
            self._cleanup_old_export_files(export_dir)
        
        # === 定期数据清理 ===
        if self.auto_clear_old_data and step - self.last_cleanup_step >= self.cleanup_interval:
            self._perform_data_cleanup(step)
            self.last_cleanup_step = step
        
        # === 增量导出逻辑 ===
        if self.enable_incremental_export:
            # 只导出新的episode数据
            new_episodes = self.training_rewards['episodes_completed'] - self.last_exported_episode
            if new_episodes > 0:
                recent_episode_data = self.training_rewards['episode_rewards'][-new_episodes:]
                if recent_episode_data:
                    rewards_df = pd.DataFrame(recent_episode_data)
                    # 使用增量文件名
                    filename = f'episode_rewards_incremental_step_{step}_episodes_{new_episodes}.csv'
                    if self.enable_data_compression:
                        filename = filename.replace('.csv', '.csv.gz')
                        rewards_df.to_csv(os.path.join(export_dir, filename), index=False, compression='gzip')
                    else:
                        rewards_df.to_csv(os.path.join(export_dir, filename), index=False)
                self.last_exported_episode = self.training_rewards['episodes_completed']
        else:
            # 传统的全量导出
            if self.training_rewards['episode_rewards']:
                rewards_df = pd.DataFrame(self.training_rewards['episode_rewards'])
                filename = f'episode_rewards_step_{step}.csv'
                if self.enable_data_compression:
                    filename = filename.replace('.csv', '.csv.gz')
                    rewards_df.to_csv(os.path.join(export_dir, filename), index=False, compression='gzip')
                else:
                    rewards_df.to_csv(os.path.join(export_dir, filename), index=False)
        
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
        
        # 导出性能指标中的奖励组成部分
        for comp_name, comp_list in self.performance_metrics['reward_components'].items():
            for entry in comp_list:
                components_data.append({
                    'step': entry['step'],
                    'env_id': entry['env_id'],
                    'component': comp_name,
                    'value': entry['value'],
                    'timestamp': entry.get('timestamp', 0)
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
            self.log_to_tensorboard(writer, step, args=args)
        
        self.last_export_step = step
        main_logger.debug(f"已导出步骤 {step} 的训练数据到 {export_dir}")
    
    def _perform_data_cleanup(self, current_step):
        """执行数据清理，释放内存"""
        try:
            cleanup_count = 0
            
            # 清理旧的step级数据（超过缓冲区限制的部分）
            if hasattr(self.training_rewards['step_rewards'], '__len__') and len(self.training_rewards['step_rewards']) > self.max_step_data_buffer:
                if isinstance(self.training_rewards['step_rewards'], list):
                    # 只保留最近的数据
                    self.training_rewards['step_rewards'] = self.training_rewards['step_rewards'][-self.max_step_data_buffer:]
                    cleanup_count += 1
            
            # 清理旧的技能多样性历史数据
            if len(self.skill_usage['skill_diversity_history']) > self.max_step_data_buffer:
                self.skill_usage['skill_diversity_history'] = self.skill_usage['skill_diversity_history'][-self.max_step_data_buffer:]
                cleanup_count += 1
            
            # 清理性能指标中的数据
            for metric_name, metric_data in self.performance_metrics.items():
                if isinstance(metric_data, list) and len(metric_data) > self.max_step_data_buffer * 2:
                    self.performance_metrics[metric_name] = metric_data[-self.max_step_data_buffer:]
                    cleanup_count += 1
            
            # 清理奖励组成部分数据
            for comp_name, comp_data in self.performance_metrics['reward_components'].items():
                if isinstance(comp_data, list) and len(comp_data) > self.max_step_data_buffer:
                    self.performance_metrics['reward_components'][comp_name] = comp_data[-self.max_step_data_buffer:]
                    cleanup_count += 1
            
            if cleanup_count > 0:
                main_logger.info(f"数据清理完成: 清理了 {cleanup_count} 个数据缓冲区，释放内存")
            else:
                main_logger.debug("数据清理检查: 无需清理")
                
        except Exception as e:
            main_logger.error(f"执行数据清理时出错: {e}")
    
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
    
    def log_rollout_metrics_to_tensorboard(self, writer, step, args=None):
        """记录rollout指标到TensorBoard - 与agent.update()同步调用
        
        这个函数专门用于记录需要与Environmental_Portion同步的性能指标，
        解决TensorBoard图表时间戳不一致的问题。
        
        参数:
            writer: TensorBoard writer
            step: 当前步数
            args: 命令行参数
        """
        
        # Throughput统计（修正后使用n_users，使用rollout_length窗口）
        if self.performance_metrics['served_users'] and self.n_users is not None:
            # 计算最近rollout_length步的滑动窗口平均吞吐量
            recent_served_data = self.performance_metrics['served_users'][-self.window_size:]
            recent_served_users = [u['served_users'] for u in recent_served_data]
            recent_total_users = [u['total_users'] for u in recent_served_data]
            
            if recent_served_users:
                # 平均服务用户数
                avg_served_users = np.mean(recent_served_users)
                writer.add_scalar('Performance/Throughput_ServedUsers_Rollout', avg_served_users, step)
                
                # 平均总用户数（记录但不用于计算服务率）
                avg_total_users = np.mean(recent_total_users)
                writer.add_scalar('Performance/Throughput_TotalUsers_Rollout', avg_total_users, step)
                
                # 服务率（吞吐率）- 使用固定的n_users作为分母
                service_rate = avg_served_users / self.n_users
                writer.add_scalar('Performance/Throughput_ServiceRate_Rollout', service_rate, step)
        
        # 系统吞吐量统计
        self._log_aggregated_metrics(writer, step, 
                                   self.performance_metrics['total_throughput'], 
                                   'System_Throughput_Mbps', 
                                   'Performance',
                                   value_field='system_throughput_mbps')
        
        # 平均用户吞吐量统计
        self._log_aggregated_metrics(writer, step, 
                                   self.performance_metrics['avg_throughput_per_user'], 
                                   'Avg_User_Throughput_Mbps', 
                                   'Performance',
                                   value_field='avg_throughput_per_user_mbps')
        
        # 使用新的聚合逻辑处理环境奖励组成部分
        reward_components = self.performance_metrics['reward_components']
        
        # 连接用户数统计
        self._log_aggregated_metrics(writer, step, 
                                   reward_components['connected_users'], 
                                   'Connected_Users', 
                                   'Performance')
        
        # 覆盖率统计
        self._log_aggregated_metrics(writer, step, 
                                   reward_components['coverage_ratios'], 
                                   'Coverage_Ratio', 
                                   'Performance')

    def log_to_tensorboard(self, writer, step, args=None):
        """记录详细数据到TensorBoard - 使用聚合数据避免并行环境数据堆积"""
        
        # 训练奖励统计 - 使用"均值的均值"方法统一标准
        if self.recent_rewards:
            coordinator_rewards = list(self.recent_rewards)  # 这些是coordinator的k步奖励
            
            # 如果有足够的数据，按环境分组计算平均值，然后再求总平均值
            # 注意：self.recent_rewards是从多个环境收集的奖励
            # 我们需要重新构造按环境分组的逻辑
            
            # 由于这里的数据已经是聚合后的coordinator奖励，直接计算平均值
            # 但为了统一标准，我们保持命名一致性
            mean_reward = np.mean(coordinator_rewards)
            
            # 使用rollout标识，保持与agent.py中的命名一致
            writer.add_scalar('Training/Coordinator_Reward_Mean_Rollout', mean_reward, step)
            writer.add_scalar('Training/Reward_Mean_Rollout', mean_reward, step)
        
        if self.recent_lengths:
            mean_length = np.mean(self.recent_lengths)
            writer.add_scalar('Training/EpisodeLength_Mean_Rollout', mean_length, step)
        
        # 技能多样性 - 使用"均值的均值"方法统一标准
        if self.skill_usage['skill_diversity_history']:
            recent_diversity = self.skill_usage['skill_diversity_history'][-self.window_size:]  # 使用rollout_length窗口
            
            # 按环境分组计算多样性平均值，然后再计算总平均值
            env_diversity_dict = {}
            for d in recent_diversity:
                env_id = d.get('env_id', 0)  # 如果没有env_id字段，默认为0
                if env_id not in env_diversity_dict:
                    env_diversity_dict[env_id] = []
                env_diversity_dict[env_id].append(d['diversity'])
            
            # 计算每个环境的平均多样性，然后计算跨环境平均值
            if env_diversity_dict:
                env_means = [np.mean(values) for values in env_diversity_dict.values()]
                avg_diversity = np.mean(env_means)
            else:
                avg_diversity = 0.0
            
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
        
        # 奖励组成比例（使用rollout_length窗口）
        if any(self.training_rewards['reward_components'].values()):
            recent_components = {}
            for comp_name, comp_list in self.training_rewards['reward_components'].items():
                if comp_list:
                    recent_data = comp_list[-self.window_size:]  # 使用rollout_length窗口
                    recent_components[comp_name] = np.mean([d['value'] for d in recent_data])
            
            total_intrinsic = sum(recent_components.values())
            if total_intrinsic != 0:
                for comp_name, comp_value in recent_components.items():
                    proportion = comp_value / total_intrinsic
                    writer.add_scalar(f'Training/Reward_Proportion_{comp_name}', proportion, step)
        
        # Throughput统计（修正后使用n_users，使用rollout_length窗口）
        if self.performance_metrics['served_users'] and self.n_users is not None:
            # 计算最近rollout_length步的滑动窗口平均吞吐量
            recent_served_data = self.performance_metrics['served_users'][-self.window_size:]
            recent_served_users = [u['served_users'] for u in recent_served_data]
            recent_total_users = [u['total_users'] for u in recent_served_data]
            
            if recent_served_users:
                # 平均服务用户数
                avg_served_users = np.mean(recent_served_users)
                writer.add_scalar('Performance/Throughput_ServedUsers_Rollout', avg_served_users, step)
                
                # 平均总用户数（记录但不用于计算服务率）
                avg_total_users = np.mean(recent_total_users)
                writer.add_scalar('Performance/Throughput_TotalUsers_Rollout', avg_total_users, step)
                
                # 服务率（吞吐率）- 使用固定的n_users作为分母
                service_rate = avg_served_users / self.n_users
                writer.add_scalar('Performance/Throughput_ServiceRate_Rollout', service_rate, step)
        
        # 使用新的聚合逻辑处理性能指标
        # 系统吞吐量统计
        self._log_aggregated_metrics(writer, step, 
                                   self.performance_metrics['total_throughput'], 
                                   'System_Throughput_Mbps', 
                                   'Performance',
                                   value_field='system_throughput_mbps')
        
        # 平均用户吞吐量统计
        self._log_aggregated_metrics(writer, step, 
                                   self.performance_metrics['avg_throughput_per_user'], 
                                   'Avg_User_Throughput_Mbps', 
                                   'Performance',
                                   value_field='avg_throughput_per_user_mbps')
        
        # 使用新的聚合逻辑处理环境奖励组成部分
        reward_components = self.performance_metrics['reward_components']
        
        # 通用奖励组成 - 统一到Rewards分类
        self._log_aggregated_metrics(writer, step, 
                                   reward_components['throughput_rewards'], 
                                   'Throughput_Reward', 
                                   'Rewards')
        
        self._log_aggregated_metrics(writer, step, 
                                   reward_components['coverage_rewards'], 
                                   'Coverage_Reward', 
                                   'Rewards')
        
        # 场景3特有奖励组成 - 统一到Rewards分类
        self._log_aggregated_metrics(writer, step, 
                                   reward_components['effective_coverage_rewards'], 
                                   'Effective_Coverage_Reward', 
                                   'Rewards')
        
        self._log_aggregated_metrics(writer, step, 
                                   reward_components['load_balance_rewards'], 
                                   'Load_Balance_Reward', 
                                   'Rewards')
        
        self._log_aggregated_metrics(writer, step, 
                                   reward_components['network_connectivity_rewards'], 
                                   'Network_Connectivity_Reward', 
                                   'Rewards')
        
        # 场景4特有奖励组成 - 使用聚合逻辑
        # 探索奖励
        if reward_components.get('exploration_rewards'):
            self._log_aggregated_metrics(writer, step, 
                                       reward_components['exploration_rewards'], 
                                       'Exploration_Reward', 
                                       'Rewards')
            
            # 探索奖励占总奖励的比例（使用rollout_length窗口）
            if self.recent_rewards:
                recent_exploration_rewards_data = reward_components['exploration_rewards'][-self.window_size:]
                if recent_exploration_rewards_data:
                    recent_values = [r['value'] for r in recent_exploration_rewards_data]
                    avg_exploration_reward = np.mean(recent_values)
                    recent_total_rewards = list(self.recent_rewards)
                    if recent_total_rewards:
                        avg_total_reward = np.mean(recent_total_rewards)
                        if avg_total_reward != 0:
                            exploration_ratio = avg_exploration_reward / abs(avg_total_reward)
                            writer.add_scalar('Rewards/Exploration_Reward_Ratio_Rollout', exploration_ratio, step)

        # 重叠惩罚
        self._log_aggregated_metrics(writer, step, 
                                   reward_components.get('coverage_overlap_penalty', []), 
                                   'Coverage_Overlap_Penalty', 
                                   'Rewards')

        # 覆盖栅格统计 - 移到Exploration分类
        self._log_aggregated_metrics(writer, step, 
                                   reward_components.get('covered_grids', []), 
                                   'Covered_Grids', 
                                   'Exploration')
        
        # 场景4新增：发现奖励机制统计 - 新的Discovery分类
        discovery_fields = [
            'discovery_reward', 'weighted_discovery_reward', 'discovered_users_count'
        ]
        
        for field in discovery_fields:
            if reward_components.get(field):
                recent_data = reward_components[field][-self.window_size:]
                if recent_data:
                    recent_values = [r['value'] if isinstance(r, dict) and 'value' in r else r for r in recent_data]
                    if recent_values:
                        avg_value = np.mean(recent_values)
                        
                        # 格式化字段名
                        formatted_field = field.replace('_', ' ').title().replace(' ', '_')
                        writer.add_scalar(f'Discovery/{formatted_field}_Mean_Rollout', avg_value, step)
        
        # 场景4新增：Reward Shaping机制统计 - 新的RewardShaping分类
        reward_shaping_fields = [
            'connectivity_shaping_reward', 'quality_shaping_reward', 'distance_overlap_penalty'
        ]
        
        for field in reward_shaping_fields:
            if reward_components.get(field):
                recent_data = reward_components[field][-self.window_size:]
                if recent_data:
                    recent_values = [r['value'] if isinstance(r, dict) and 'value' in r else r for r in recent_data]
                    if recent_values:
                        avg_value = np.mean(recent_values)
                        
                        # 格式化字段名
                        formatted_field = field.replace('_', ' ').title().replace(' ', '_')
                        writer.add_scalar(f'RewardShaping/{formatted_field}_Mean_Rollout', avg_value, step)
        
        # 场景4新增：发现进度统计（从环境适配器获取）
        # 这些数据可能直接来自环境的info，不在reward_components中
        # 我们需要从self.training_rewards或其他地方获取
        discovery_progress_fields = [
            'discovered_users_this_episode', 'total_users', 'discovery_progress'
        ]
        
        # 尝试从最近的训练步骤中获取发现进度信息
        if self.training_rewards and 'step_rewards' in self.training_rewards:
            recent_step_rewards = self.training_rewards['step_rewards'][-self.window_size:]
            if recent_step_rewards:
                # 从最近的步骤中提取发现进度信息
                for field in discovery_progress_fields:
                    field_values = []
                    for step_reward in recent_step_rewards:
                        # 增加对 step_reward['info'] 的非空检查
                        if 'info' in step_reward and step_reward['info'] and field in step_reward['info']:
                            field_values.append(step_reward['info'][field])
                    
                    if field_values:
                        avg_value = np.mean(field_values)
                        formatted_field = field.replace('_', ' ').title().replace(' ', '_')
                        writer.add_scalar(f'Discovery/{formatted_field}_Mean_Rollout', avg_value, step)
        
        # 计算Real_Rewards（乘以超参数后的真实值）
        # 权重参数统一从 self.config 读取
        
        # 定义奖励组件、其权重名称和显示名称的映射
        reward_to_weight_map = {
            # 奖励组件内部名称: (config中的权重属性名, TensorBoard中的显示名)
            'exploration_rewards': ('potential_reward_weight', 'Exploration'),
            'overlap_penalty': ('coverage_overlap_penalty_weight', 'OverlapPenalty'),
            'effective_coverage_rewards': ('effective_coverage_weight', 'EffectiveCoverage'),
            'throughput_rewards': ('throughput_weight', 'Throughput'),
            'load_balance_rewards': ('load_balance_weight', 'LoadBalance'),
            'coverage_rewards': ('coverage_weight', 'Coverage'),
            'network_connectivity_rewards': ('connectivity_weight', 'Connectivity'),
            # 可以根据需要添加更多映射
        }

        real_rewards_calculated = False
        if hasattr(self, 'config') and self.config:
            for reward_key, (weight_key, display_name) in reward_to_weight_map.items():
                # 检查奖励数据和权重是否存在
                if reward_components.get(reward_key) and hasattr(self.config, weight_key):
                    recent_rewards_data = reward_components[reward_key][-self.window_size:]
                    weight_value = getattr(self.config, weight_key)
                    
                    if recent_rewards_data:
                        # 计算平均原始奖励值
                        avg_raw_reward = np.mean([r['value'] for r in recent_rewards_data])
                        # 计算加权后的真实奖励
                        real_reward = avg_raw_reward * weight_value
                        
                        # 构建TensorBoard标签
                        # 格式: Real_Rewards/奖励名字_权重名字_权重数值
                        tb_tag = f"Real_Rewards/{display_name}_{weight_key}_{weight_value:.4f}"
                        
                        # 记录到TensorBoard
                        writer.add_scalar(tb_tag, real_reward, step)
                        real_rewards_calculated = True

        if not real_rewards_calculated:
            # 如果没有任何一个真实奖励被计算和记录，则记录一个提示
            writer.add_text('Real_Rewards/Note', 'No real rewards were calculated. Check config for weights.', step)
        
        # 其他有用指标 - 使用聚合逻辑
        self._log_aggregated_metrics(writer, step, 
                                   reward_components['avg_hops'], 
                                   'Avg_Hops', 
                                   'Performance')
        
        self._log_aggregated_metrics(writer, step, 
                                   reward_components['connected_users'], 
                                   'Connected_Users', 
                                   'Performance')
        
        self._log_aggregated_metrics(writer, step, 
                                   reward_components['coverage_ratios'], 
                                   'Coverage_Ratio', 
                                   'Performance')
    
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

# 创建环境函数 (简化后用于 SubprocVecEnv)
def make_env(rank, seed, config, scenario, render_mode=None):
    """
    创建环境实例的函数 (用于 SubprocVecEnv) - 简化版本

    参数:
        rank: 环境的索引 (用于设置不同的种子)
        seed: 基础随机种子
        config: 配置对象，包含所有环境参数和奖励权重
        scenario: 场景编号 (1=基站模式, 2=协作组网模式, 3=强制多跳模式, 4=强制中继模式)
        render_mode: 渲染模式

    返回:
        一个返回环境实例的函数
    """
    def _init():
        env_seed = seed + rank # 为每个并行环境设置不同的种子
        
        # 从配置对象获取通用环境参数
        env_kwargs = {
            'n_uavs': config.n_agents,
            'n_users': config.n_users,
            'user_distribution': config.user_distribution,
            'render_mode': render_mode,
            'seed': env_seed,
            'use_fdma': config.use_fdma,
            'bandwidth': config.bandwidth
        }
        
        if scenario == 4:
            # 场景4：强制多跳中继环境（使用简化的奖励权重参数）
            scenario4_kwargs = {
                'max_steps': config.episode_length,           # 从配置中传入episode长度
                'user_distribution': 'forced_relay_cluster',  # 场景4强制使用此分布类型
                'max_hops': config.max_hops,
                'area_size': config.area_size,
                'n_clusters': config.n_clusters,
                'cluster_std': config.cluster_std,
                'central_area_ratio': config.central_area_ratio,
                'min_sinr': config.min_sinr,
                'max_connections': config.max_connections,
                'uav_init_mode': config.uav_init_mode,
                'uav_start_area_size': config.uav_start_area_size,
            }
            
            # 将场景4的参数合并到通用参数中
            env_kwargs.update(scenario4_kwargs)
            
            raw_env = UAVForcedRelayEnv(**env_kwargs)
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
    parser.add_argument('--scenario', type=int, default=4, help='场景: 1=基站模式, 2=协作组网模式, 3=强制多跳模式, 4=强制中继模式')
    parser.add_argument('--model_path', type=str, default='models/hmasd_multiproc_paper_config.pt', help='模型保存/加载路径')
    parser.add_argument('--log_dir', type=str, default='../tf-logs', help='日志目录')
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

    # 并行参数 (可覆盖配置文件中的值)
    parser.add_argument('--num_envs', type=int, default=0, 
                        help='并行环境数量 (0=使用配置文件中的值)')
    parser.add_argument('--eval_rollout_threads', type=int, default=0, 
                        help='评估时的并行线程数 (0=使用配置文件中的值)')
    
    # 数据收集参数
    parser.add_argument('--export_interval', type=int, default=1000, 
                        help='数据导出间隔步数')
    parser.add_argument('--detailed_logging', action='store_true', default=True,
                        help='启用详细的奖励日志记录')
    
    # 高级功能开关 (详细参数在config_1.py中定义)
    parser.add_argument('--use_opt', action=argparse.BooleanOptionalAction, default=False,
                        help='是否使用OPT (Interaction Pattern Disentangling) 模块 (使用--use_opt启用，--no-use_opt禁用)')
    parser.add_argument('--use_reward_annealing', action=argparse.BooleanOptionalAction, default=False,
                        help='是否启用奖励权重退火机制 (使用--use_reward_annealing启用，--no-use_reward_annealing禁用)')
    parser.add_argument('--use_lr_decay', action=argparse.BooleanOptionalAction, default=False,
                        help='是否启用学习率衰减 (使用--use_lr_decay启用，--no-use_lr_decay禁用)')
    
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
    import torch  # 添加这行确保 torch 在函数作用域内可用
    
    num_envs = vec_env.num_envs # Get num_envs from SubprocVecEnv
    main_logger.info(f"开始训练HMASD (多进程版本，使用 {num_envs} 个并行环境)...")
    main_logger.info(f"配置已预先初始化: state_dim={config.state_dim}, obs_dim={config.obs_dim}, n_agents={config.n_agents}")

    # 创建日志目录
    log_dir = os.path.join(args.log_dir, f"sb3_multiproc_paper_config_{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(log_dir, exist_ok=True)
    model_dir = os.path.dirname(args.model_path)
    os.makedirs(model_dir, exist_ok=True)
    
    # 创建HMASD代理（不再有TensorBoard writer）
    agent = HMASDAgent(config, log_dir=log_dir, device=device)
    
    # 创建统一的TensorBoard管理器
    tb_manager = TensorBoardManager(log_dir, config)
    
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
            tb_manager.add_text('Training/resumed_from', args.resume_from, 0)
            tb_manager.add_text('Training/mode', 'resume_training', 0)
        except Exception as e:
            main_logger.error(f"加载预训练模型失败: {e}")
            main_logger.info("将从头开始训练")
            tb_manager.add_text('Training/mode', 'from_scratch_due_to_load_error', 0)
    elif args.resume_from:
        main_logger.warning(f"指定的预训练模型文件不存在: {args.resume_from}")
        main_logger.info("将从头开始训练")
        tb_manager.add_text('Training/mode', 'from_scratch_due_to_missing_file', 0)
    else:
        main_logger.info("从头开始训练")
        tb_manager.add_text('Training/mode', 'from_scratch', 0)
    
    # 创建增强的奖励追踪器
    reward_tracker = EnhancedRewardTracker(log_dir, config, n_users=config.n_users)
    reward_tracker.export_interval = args.export_interval
    
    # 记录额外超参数
    tb_manager.add_text('Parameters/num_envs', str(num_envs), 0)
    tb_manager.add_text('Parameters/export_interval', str(args.export_interval), 0)
    tb_manager.add_text('Parameters/detailed_logging', str(args.detailed_logging), 0)
    
    
    # 训练变量
    total_steps = 0
    n_episodes = 0
    max_episodes = config.total_timesteps // config.batch_size  # 估计的最大episode数量
    episode_rewards = []
    update_times = 0
    best_reward = float('-inf')
    last_eval_step = 0  # 跟踪上次评估的步数
    
    # 高层样本累积检测变量
    high_level_samples_collected_total = 0  # 总共收集的高层样本数
    last_check_total_steps = 0              # 上次检查时的总步数
    last_check_hl_samples = 0               # 上次检查时的高层样本数
    last_high_level_buffer_size = 0         # 上次检查时的高层缓冲区大小
    check_interval_steps = config.batch_size * num_envs  # 检查间隔步数
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

            # 简化奖励处理，直接使用环境原始奖励，与agent.py逻辑保持一致
            reward_components_list = []
            
            for i in range(num_envs):
                # 提取奖励组成部分（用于详细记录和分析）
                reward_components = infos[i].get('reward_components', {})
                reward_components_list.append(reward_components)

            # 存储经验到缓冲区
            for i in range(num_envs):
                current_agent_info = all_agent_infos_list[i]
                skill_timer_value = env_skill_durations[i]
                
                # 从agent_info中提取values（新的agent.py API）
                values = current_agent_info.get('values', None)
                
                # 使用环境原始奖励，与agent.py逻辑保持一致
                returned_reward_components = agent.store_transition(
                    states[i], next_states[i], observations[i], next_observations[i],
                    actions_array[i], rewards[i], dones[i], current_agent_info['team_skill'],
                    current_agent_info['agent_skills'], current_agent_info['action_logprobs'],
                    values=values,
                    log_probs=current_agent_info['log_probs'],
                    skill_timer_for_env=skill_timer_value,
                    env_id=i,
                    rollout_step_idx=rollout_step  # 【修复】传递正确的rollout步数索引
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
                # 使用环境原始奖励累积
                env_rewards[i] += rewards[i]

                # 使用增强的奖励追踪器记录训练步骤
                if args.detailed_logging:
                    # 使用从 store_transition 返回的奖励组成部分
                    reward_tracker.log_training_step(
                        step=total_steps - num_envs + i + 1,
                        env_id=i,
                        reward=rewards[i],  # 【修复】记录原始环境奖励，而不是未定义的高层奖励
                        reward_components=returned_reward_components,
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
                    tb_manager.log_skill_distribution(
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
                    tb_manager.log_episode_completion(n_episodes, i, env_rewards[i], env_steps[i])

                    main_logger.info(f"环境 {i}/{num_envs} 完成: Episode {n_episodes}, 奖励: {env_rewards[i]:.2f}, 步数: {env_steps[i]}")

                    # 重置环境状态跟踪
                    env_steps[i] = 0
                    env_rewards[i] = 0
                    
                    # 【修复】重置智能体中该环境的内部状态
                    agent.reset_env_state(i)

                    # 奖励统计
                    window_size = min(config.rollout_length, len(episode_rewards))
                    if len(episode_rewards) >= window_size:
                        recent_rewards = episode_rewards[-window_size:]
                        avg_reward = np.mean(recent_rewards)
                        std_reward = np.std(recent_rewards)
                        max_reward = np.max(recent_rewards)
                        min_reward = np.min(recent_rewards)

                        tb_manager.add_scalar(f'Reward/avg_reward_{window_size}', avg_reward, n_episodes)
                        tb_manager.add_scalar(f'Reward/std_reward_{window_size}', std_reward, n_episodes)
                        tb_manager.add_scalar(f'Reward/max_reward_{window_size}', max_reward, n_episodes)
                        tb_manager.add_scalar(f'Reward/min_reward_{window_size}', min_reward, n_episodes)

                        main_logger.info(f"最近{window_size}个episodes: 平均奖励 {avg_reward:.2f} ± {std_reward:.2f}, 最大/最小: {max_reward:.2f}/{min_reward:.2f}")

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

        # --- 在更新前计算GAE和Returns (最终修正版) ---
        main_logger.debug("为低层策略(Discoverer)计算GAE...")

        # 1. 获取最后一步的价值 (Critic的直接输出)
        last_values_predicted = np.zeros((num_envs, config.n_agents), dtype=np.float32)
        with torch.no_grad():
            for i in range(num_envs):
                current_team_skill = agent.env_team_skills.get(i, 0)
                if current_team_skill == -1: current_team_skill = 0
                
                global_state_tensor = torch.FloatTensor(states[i]).unsqueeze(0).to(agent.device)
                team_skill_tensor = torch.tensor(current_team_skill, device=agent.device).unsqueeze(0)
                global_value_tensor, _ = agent.skill_discoverer.get_value(global_state_tensor, team_skill_tensor)
                
                last_values_predicted[i, :] = global_value_tensor.squeeze().item()

        # 2. 将所有价值（缓冲区内的和最后一步的）反归一化到原始奖励尺度
        if config.use_valuenorm:
            main_logger.info("ValueNorm已启用，正在反归一化价值以计算GAE...")
            # a. 反归一化缓冲区中存储的价值
            values_in_buffer_tensor = torch.from_numpy(agent.rollout_buffer.values[:rollout_steps]).to(agent.device)
            values_in_buffer_denorm = agent._denormalize_values(values_in_buffer_tensor, agent.value_norm_discoverer)
            
            # b. 反归一化最后一步的价值
            last_values_tensor = torch.from_numpy(last_values_predicted).to(agent.device)
            last_values_denorm = agent._denormalize_values(last_values_tensor, agent.value_norm_discoverer)
            
            # 将反归一化后的值（numpy格式）传递给 GAE 计算
            values_for_gae = values_in_buffer_denorm.cpu().numpy()
            last_values_for_gae = last_values_denorm.cpu().numpy()
        else:
            # 如果不使用ValueNorm，直接使用Critic的原始输出
            values_for_gae = agent.rollout_buffer.values[:rollout_steps]
            last_values_for_gae = last_values_predicted

        # 3. 调用 compute_advantages，现在所有价值都在正确的原始尺度上
        # 使用已有的 denormalized_values 和 denormalized_last_values 参数
        agent.rollout_buffer.compute_advantages(
            last_values=last_values_predicted, # 原始的预测值，用于兼容性
            dones=np.zeros((num_envs, config.n_agents), dtype=bool), # 假设rollout结束时非终止
            gamma=config.gamma, 
            gae_lambda=config.gae_lambda,
            denormalized_values=values_for_gae, # 传入反归一化后的序列价值
            denormalized_last_values=last_values_for_gae # 传入反归一化后的最后一步价值
        )

        # Rollout数据收集完成，进行更新
        try:
            update_info = agent.update(steps_in_buffer=rollout_steps)
            update_times += 1
            elapsed = time.time() - start_time

            main_logger.info(f"Rollout更新 {update_times} (收集了 {rollout_steps} 步), 总步数 {total_steps}, "
                  f"高层损失 {update_info['coordinator_loss']:.4f}, "
                  f"低层损失 {update_info['discoverer_loss']:.4f}, "
                  f"判别器损失 {update_info['discriminator_loss']:.4f}, "
                  f"CD损失 {update_info.get('cd_loss', 0):.4f}, "
                  f"已用时间 {elapsed:.2f}s")
            
            # 记录训练指标到TensorBoard
            tb_manager.log_training_metrics(total_steps, update_info, args=args)
            
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
            
        except ValueError as e:
            main_logger.error(f"更新错误: {e}")
            update_times += 1

        # 【修复】更新完成后，清空缓冲区，为下一次rollout做准备
        # 这是解决“重复存储”问题的关键
        agent.clear_buffers()

        # 重置rollout步数计数器
        rollout_steps = 0

        # 加强高层样本的累积情况监控
        if total_steps >= last_check_total_steps + check_interval_steps:
                # 获取当前高层缓冲区大小 (从统一的rollout buffer中计算)
                num_steps_in_buffer = config.rollout_length
                current_high_level_buffer_size = np.sum(agent.rollout_buffer.high_level_valid_mask[:num_steps_in_buffer])
                
                # 从agent获取总收集的高层样本数(现在总是准确的，不受缓冲区满的影响)
                current_high_level_samples_total = agent.high_level_samples_total
                
                # 计算自上次检查以来的步数和增加的高层样本数
                steps_since_last_check = total_steps - last_check_total_steps
                parallel_steps_since_last_check = steps_since_last_check // num_envs
                samples_since_last_check = current_high_level_samples_total - last_check_hl_samples
                
                # 记录样本收集情况
                main_logger.debug(f"高层样本收集统计: 当前总样本数={current_high_level_samples_total}, "
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
                
        
        # 定期导出训练数据
        reward_tracker.export_training_data(total_steps, tb_manager.writer, args=args)
        
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

        # 在调用 agent.update() 之后立即记录rollout指标到TensorBoard
        reward_tracker.log_rollout_metrics_to_tensorboard(tb_manager.writer, total_steps, args=args)

    # 【修复】将"训练完成"相关代码移出while循环
    main_logger.info(f"训练完成! 总步数: {total_steps}, 总episodes: {n_episodes}")
    main_logger.info(f"最佳奖励: {best_reward:.2f}")

    # 最终数据导出和统计
    main_logger.info("生成最终训练统计报告...")
    reward_tracker.export_training_data(total_steps, tb_manager.writer, args=args)
    
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
    import torch  # 添加这行确保 torch 在函数作用域内可用
    
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

    # 创建轨迹记录器
    trajectory_recorder = TrajectoryRecorder(agent.config)
    
    # 为绘图收集历史数据 - 使用灵活的记录管理器
    env_histories = [
        {
            'steps': [], 'uav_positions': [], 'connectivity': [], 'throughput': [],
            'static_info': None  # 用于存储静态信息
        } for _ in range(num_envs)
    ]
    plots_generated = 0  # 追踪本次评估已生成的图片数量
    
    def record_env_history(env_id, step_count, skill_changed=False, episode_end=False):
        """记录环境历史数据 - 使用轨迹记录器控制记录频率"""
        # 使用轨迹记录器判断是否应该记录
        should_record = trajectory_recorder.should_record(env_id, step_count, skill_changed, episode_end)
        
        if not should_record:
            return False
        
        try:
            # 获取当前环境状态
            env_state = vec_env.env_method('get_current_state', indices=[env_id])[0]
            
            # 记录步数和UAV位置
            env_histories[env_id]['steps'].append(step_count)
            env_histories[env_id]['uav_positions'].append(env_state['uav_positions'].copy())
            
            # 记录性能指标
            if env_id < len(infos) and 'reward_info' in infos[env_id]:
                reward_info = infos[env_id]['reward_info']
                env_histories[env_id]['connectivity'].append(reward_info.get('effective_connected_users', 0))
                env_histories[env_id]['throughput'].append(reward_info.get('system_throughput_mbps', 0))
            else:
                env_histories[env_id]['connectivity'].append(0)
                env_histories[env_id]['throughput'].append(0)
            
            # 收集静态信息（只需要收集一次）
            if env_histories[env_id]['static_info'] is None:
                static_info = {}
                if 'user_positions' in env_state:
                    static_info['user_positions'] = env_state['user_positions'].copy()
                if 'ground_bs_positions' in env_state:
                    static_info['ground_bs_positions'] = env_state['ground_bs_positions'].copy()
                if 'area_size' in env_state:
                    static_info['area_size'] = env_state['area_size']
                env_histories[env_id]['static_info'] = static_info
            
            main_logger.debug(f"已记录环境 {env_id} 步骤 {step_count} 的轨迹数据 (总计: {len(env_histories[env_id]['steps'])} 个点)")
            return True
                
        except Exception as e:
            main_logger.warning(f"记录环境 {env_id} 历史数据时出错: {e}")
            return False
    
    # 记录初始状态的历史数据
    infos = initial_infos  # 临时设置用于记录初始状态
    for i in range(num_envs):
        record_env_history(i, 0)

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
                    
                    # 统一使用global_reward进行评估
                    extrinsic_reward = infos[i].get('reward_info', {}).get('final_global_reward', rewards[i])
                    env_rewards[i] += extrinsic_reward
                    
                    # 使用轨迹记录器收集历史数据用于绘图
                    skill_changed = all_agent_infos_list[i].get('skill_changed', False) if i < len(all_agent_infos_list) else False
                    record_env_history(i, env_steps[i], skill_changed=skill_changed, episode_end=False)

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
                            
                            # 获取服务用户数和覆盖率信息（修正为使用瞬时值）
                            if 'reward_info' in infos[i] and 'effective_connected_users' in infos[i]['reward_info']:
                                # 使用瞬时有效连接用户数，而不是累积值
                                served_users = infos[i]['reward_info']['effective_connected_users']
                                # 从配置中获取用户总数
                                n_users = agent.config.n_users if hasattr(agent, 'config') and hasattr(agent.config, 'n_users') else 0
                                coverage_ratio = served_users / n_users if n_users > 0 else 0
                                
                                total_served_users.append(served_users)
                                total_coverage_ratios.append(coverage_ratio)
                                
                                main_logger.info(f"评估 Episode {completed_episodes+1}/{n_episodes} (来自环境 {i}), 奖励: {env_rewards[i]:.2f}, 步数: {env_steps[i]}, 瞬时有效连接用户数: {served_users}/{n_users} ({coverage_ratio:.2%})")
                            else:
                                main_logger.info(f"评估 Episode {completed_episodes+1}/{n_episodes} (来自环境 {i}), 奖励: {env_rewards[i]:.2f}, 步数: {env_steps[i]}")

                            # 记录到TensorBoard (评估函数中暂时跳过，因为没有传入writer)
                            # 在实际使用中，应该通过参数传入TensorBoard writer
                            pass

                            # 记录高层奖励
                            high_level_rewards.append(env_rewards[i])
                            
                            # 确保记录episode结束时的最终位置
                            record_env_history(i, env_steps[i], skill_changed=False, episode_end=True)
                            
                            # 为最先完成的4个环境生成绘图
                            if plots_generated < 4 and len(env_histories[i]['uav_positions']) > 0:
                                try:
                                    # 创建保存目录
                                    eval_plots_dir = os.path.join(agent.log_dir, 'evaluation_plots')
                                    os.makedirs(eval_plots_dir, exist_ok=True)
                                    
                                    # 生成2D拓扑图 - 为当前环境单独生成
                                    topology_path = os.path.join(eval_plots_dir, f'eval_topology_step_{eval_step}_env_{i}.png')
                                    save_evaluation_2d_topology_plot(
                                        env_histories[i], 
                                        env_histories[i]['static_info'], 
                                        topology_path, 
                                        completed_episodes+1, 
                                        agent.config
                                    )
                                    
                                    # 生成性能图表（使用当前环境的数据）
                                    performance_path = os.path.join(eval_plots_dir, f'eval_performance_step_{eval_step}_env_{i}.png')
                                    save_evaluation_performance_plot(
                                        env_histories[i], 
                                        performance_path, 
                                        completed_episodes+1
                                    )
                                    
                                    plots_generated += 1
                                    main_logger.info(f"已为环境 {i} 生成评估绘图 ({plots_generated}/4): {eval_plots_dir}")
                                    
                                except Exception as e:
                                    main_logger.error(f"为环境 {i} 生成评估绘图时出错: {e}")
                            
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

    # 记录评估统计信息 (评估函数中暂时跳过，因为没有传入writer)
    # 在实际使用中，应该通过参数传入TensorBoard writer
    pass

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
        
        # 将性能指标也记录到TensorBoard中 (评估函数中暂时跳过，因为没有传入writer)
        # 在实际使用中，应该通过参数传入TensorBoard writer
        pass
    
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
    
    # 只设置少量开关参数（其他参数已在config_1.py中定义）
    config.use_opt = args.use_opt
    config.use_reward_annealing = args.use_reward_annealing
    config.use_lr_decay = args.use_lr_decay
    
    main_logger.info("配置已从config_1.py加载，运行时开关参数已设置")
    main_logger.info(f"OPT模块: {config.use_opt}, 权重退火: {config.use_reward_annealing}, 学习率衰减: {config.use_lr_decay}")
    
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
        rank=i,
        seed=base_seed,
        config=config,
        scenario=args.scenario,
        render_mode=None
    ) for i in range(num_envs)]

    eval_env_fns = [make_env(
        rank=i,
        seed=base_seed + num_envs,
        config=config,
        scenario=args.scenario,
        render_mode="human" if args.render and i == 0 else None
    ) for i in range(eval_rollout_threads)]

    # 首先创建一个临时环境来获取维度信息
    main_logger.info("创建临时环境以获取状态和观测维度...")
    temp_env_fn = make_env(
        rank=0,
        seed=base_seed,
        config=config,
        scenario=args.scenario,
        render_mode=None
    )
    temp_env = temp_env_fn()
    
    # 从临时环境获取维度信息
    state_dim = temp_env.state_dim
    obs_dim = temp_env.obs_dim
    
    # 更新配置维度（n_agents已在之前设置）
    config.update_env_dims(state_dim, obs_dim)
    
    main_logger.info(f"从环境获取维度信息: state_dim={state_dim}, obs_dim={obs_dim}")
    main_logger.info(f"确认无人机数量: n_agents={config.n_agents}")

    # 打印环境参数以供确认
    main_logger.info("="*50)
    main_logger.info("已应用的环境和算法配置参数:")
    
    # 根据场景分类参数
    scenario_param_categories = {
        1: "基站模式参数",
        2: "协作组网模式参数", 
        3: "强制多跳模式参数",
        4: "强制中继模式参数"
    }
    
    main_logger.info(f"当前场景: {args.scenario} ({scenario_param_categories.get(args.scenario, '未知场景')})")
    main_logger.info("")

    def print_config_section(title, config_obj, attr_names, format_func=None):
        """打印配置对象的指定属性"""
        params = []
        for attr_name in attr_names:
            if hasattr(config_obj, attr_name):
                value = getattr(config_obj, attr_name)
                if format_func:
                    formatted_value = format_func(value)
                else:
                    formatted_value = str(value)
                params.append(f"{attr_name}: {formatted_value}")
        
        if params:
            main_logger.info(f"{title}:")
            for param in params:
                main_logger.info(f"  - {param}")
            main_logger.info("")
        return len(params)

    # 基础环境参数
    basic_env_params = [
        "n_agents", "n_users", "area_size", "user_distribution", "channel_model",
        "use_fdma", "bandwidth", "max_hops"
    ]
    
    # 场景4参数
    scenario4_params = [
        "n_clusters", "cluster_std", "central_area_ratio"
    ]
    
    # 场景4特有环境参数
    scenario4_env_params = [
        "min_sinr", "max_connections", "uav_init_mode", "uav_start_area_size", 
        "grid_resolution"
    ]
    
    # HMASD算法核心参数
    hmasd_core_params = [
        "n_Z", "n_z", "k", "state_dim", "obs_dim", "action_dim"
    ]
    
    # HMASD超参数
    hmasd_hyperparams = [
        "gamma", "lambda_e", "lambda_D", "lambda_d", "lambda_h", "lambda_l",
        "lr_coordinator", "lr_discoverer", "lr_discriminator"
    ]
    
    # 训练参数
    training_params = [
        "total_timesteps", "num_envs", "eval_rollout_threads", "rollout_length",
        "buffer_size", "batch_size", "high_level_batch_size", "eval_interval", 
        "eval_episodes"
    ]
    
    # 网络结构参数
    network_params = [
        "hidden_size", "embedding_dim", "n_encoder_layers", "n_decoder_layers",
        "n_heads", "gru_hidden_size"
    ]
    
    # OPT模块参数
    opt_params = [
        "use_opt_coordinator", "use_opt_discoverer_actor", "use_opt_discoverer_critic",
        "opt_num_prototypes", "opt_prototype_dim", "opt_alpha", "opt_beta", "opt_layers"
    ]
    
    # 权重退火参数
    annealing_params = [
        "use_reward_annealing", "w_intrinsic_initial", "w_intrinsic_final",
        "w_extrinsic_initial", "w_extrinsic_final", "anneal_steps", "anneal_schedule"
    ]
    
    # 学习率衰减参数
    lr_decay_params = [
        "use_lr_decay", "lr_decay_schedule", "lr_decay_steps",
        "coordinator_lr_decay_factor", "discoverer_lr_decay_factor", "discriminator_lr_decay_factor"
    ]

    # 打印各类参数
    total_params = 0
    
    # 1. 基础环境参数
    total_params += print_config_section("基础环境参数", config, basic_env_params)
    
    # 2. 场景4参数
    if args.scenario == 4:
        total_params += print_config_section("场景4参数", config, scenario4_params)
        total_params += print_config_section("场景4环境参数", config, scenario4_env_params)
    
    # 4. HMASD算法参数
    total_params += print_config_section("HMASD核心参数", config, hmasd_core_params)
    total_params += print_config_section("HMASD超参数", config, hmasd_hyperparams)
    
    # 5. 训练参数
    total_params += print_config_section("训练参数", config, training_params)
    
    # 6. 网络结构参数
    total_params += print_config_section("网络结构参数", config, network_params)
    
    # 7. 可选模块参数（只有在启用时才打印）
    if hasattr(config, 'use_opt_coordinator') and (config.use_opt_coordinator or config.use_opt_discoverer_actor or config.use_opt_discoverer_critic):
        total_params += print_config_section("OPT模块参数", config, opt_params)
    
    if hasattr(config, 'use_reward_annealing') and config.use_reward_annealing:
        total_params += print_config_section("奖励权重退火参数", config, annealing_params)
    
    if hasattr(config, 'use_lr_decay') and config.use_lr_decay:
        total_params += print_config_section("学习率衰减参数", config, lr_decay_params)

    # 总结
    main_logger.info(f"总计显示了 {total_params} 个配置参数")
    
    # 额外验证：从环境获取部分关键参数进行对比
    env_to_check = temp_env.unwrapped if hasattr(temp_env, 'unwrapped') else temp_env
    env_verification_params = ["n_uavs", "n_users", "area_size"]
    
    verification_info = []
    for param in env_verification_params:
        if hasattr(env_to_check, param):
            env_value = getattr(env_to_check, param)
            config_value = getattr(config, param, "未设置")
            if env_value == config_value:
                verification_info.append(f"{param}: ✓ ({env_value})")
            else:
                verification_info.append(f"{param}: ⚠ 环境={env_value}, 配置={config_value}")
    
    if verification_info:
        main_logger.info("配置与环境一致性验证:")
        for info in verification_info:
            main_logger.info(f"  - {info}")
        main_logger.info("")

    main_logger.info("="*50)
    
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
        
        # 创建评估用的TensorBoard管理器
        eval_tb_manager = TensorBoardManager(log_dir, config)
        
        # 记录模型配置
        eval_tb_manager.add_text('Eval/model_path', args.model_path, 0)
        eval_tb_manager.add_text('Eval/scenario', str(args.scenario), 0)
        eval_tb_manager.add_text('Eval/n_agents', str(config.n_agents), 0)
        eval_tb_manager.add_text('Eval/num_envs', str(eval_vec_env.num_envs), 0)

        # 评估模型
        evaluate(eval_vec_env, agent, n_episodes=args.eval_episodes, render=args.render)
    else:
        main_logger.error(f"未知的运行模式: {args.mode}")
    
    # 关闭环境
    train_vec_env.close()
    eval_vec_env.close()

def smooth_trajectory(trajectory, window_size=3):
    """
    平滑轨迹，减少噪声
    
    参数:
        trajectory: 轨迹数组 [steps, 2] (x, y坐标)
        window_size: 滑动窗口大小
    
    返回:
        smoothed: 平滑后的轨迹数组
    """
    if len(trajectory) <= window_size:
        return trajectory
    
    # 使用简单的移动平均
    smoothed = np.zeros_like(trajectory)
    for i in range(len(trajectory)):
        start_idx = max(0, i - window_size // 2)
        end_idx = min(len(trajectory), i + window_size // 2 + 1)
        smoothed[i] = np.mean(trajectory[start_idx:end_idx], axis=0)
    
    return smoothed

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

def save_evaluation_2d_topology_plot(history, static_info, save_path, episode_num, config):
    """
    生成并保存2D俯瞰拓扑图，显示无人机轨迹（优化版）
    
    参数:
        history: 包含历史数据的字典，包含 'uav_positions' 列表
        static_info: 静态环境信息，包含 'user_positions', 'ground_bs_positions', 'area_size'
        save_path: 图像保存的完整文件路径
        episode_num: episode编号
        config: 配置对象
    """
    try:
        import matplotlib.pyplot as plt
        
        # 配置中文字体支持
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # 绘制历史轨迹
        positions_history = np.array(history['uav_positions'])  # [steps, n_uavs, 3]
        
        if len(positions_history) == 0:
            main_logger.warning("没有轨迹数据可绘制")
            return
        
        # 检查是否启用轨迹平滑
        enable_smoothing = getattr(config, 'enable_trajectory_smoothing', True)
        
        for i in range(config.n_agents):
            # 使用颜色循环来区分不同无人机
            color = plt.cm.jet(i / config.n_agents)
            
            # 提取轨迹数据（只使用x, y坐标）
            trajectory = positions_history[:, i, :2]
            
            # 平滑轨迹（如果启用且点数足够）
            if enable_smoothing and len(trajectory) > 5:
                trajectory = smooth_trajectory(trajectory)
            
            # 绘制轨迹线
            ax.plot(trajectory[:, 0], trajectory[:, 1], 
                    color=color, alpha=0.6, linewidth=1.5,
                    label=f'UAV {i} 轨迹' if i < 3 else "")  # 只为前3个UAV添加图例
            
            # 起点：圆形标记
            ax.scatter(trajectory[0, 0], trajectory[0, 1],
                       marker='o', color=color, s=80, edgecolors='black', zorder=6)
            
            # 终点：三角形标记（唯一的终点标记）
            ax.scatter(trajectory[-1, 0], trajectory[-1, 1],
                       marker='^', color=color, s=120, edgecolors='black', zorder=6)
            
            # 添加UAV标识文本
            ax.text(trajectory[-1, 0] + 10, trajectory[-1, 1] + 10, f'UAV{i}', fontsize=9)

        # 绘制静态实体
        if static_info:
            # 1. 地面基站
            if 'ground_bs_positions' in static_info and static_info['ground_bs_positions'] is not None:
                bs_pos = static_info['ground_bs_positions']
                ax.scatter(bs_pos[:, 0], bs_pos[:, 1], c='black', marker='s', s=200, 
                          label='地面基站', zorder=5)

            # 2. 用户
            if 'user_positions' in static_info and static_info['user_positions'] is not None:
                user_pos = static_info['user_positions']
                ax.scatter(user_pos[:, 0], user_pos[:, 1], c='blue', marker='.', s=50, 
                          label='用户', zorder=5)

        # 添加图例说明
        from matplotlib.lines import Line2D
        legend_elements = []
        if enable_smoothing:
            legend_elements.append(Line2D([0], [0], marker='o', color='gray', label='起点',
                                        markerfacecolor='gray', markersize=8, linestyle='None'))
            legend_elements.append(Line2D([0], [0], marker='^', color='gray', label='终点',
                                        markerfacecolor='gray', markersize=10, linestyle='None'))
        
        # 获取现有图例并添加起点终点说明
        handles, labels = ax.get_legend_handles_labels()
        handles.extend(legend_elements)
        
        ax.set_title(f'评估 Episode {episode_num}: 2D拓扑与无人机轨迹{"（平滑）" if enable_smoothing else ""}')
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        
        area_size = static_info.get('area_size', 1000) if static_info else 1000
        ax.set_xlim(0, area_size)
        ax.set_ylim(0, area_size)
        ax.set_aspect('equal', adjustable='box')
        ax.legend(handles=handles)
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # 保存图像
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=200, bbox_inches='tight')
        plt.close(fig)
        main_logger.info(f"2D拓扑图已保存: {save_path}")
        
    except Exception as e:
        main_logger.error(f"生成2D拓扑图时出错: {e}")


def save_evaluation_2d_topology_plot_enhanced(env_histories, save_path, config):
    """
    增强版2D拓扑图绘制函数 - 基于visualize_evaluation.py的成功方案
    选择最佳轨迹进行绘制
    
    参数:
        env_histories: 所有环境的历史数据列表
        save_path: 图像保存的完整文件路径
        config: 配置对象
    """
    main_logger.info(f"[DEBUG] save_evaluation_2d_topology_plot_enhanced 函数开始执行")
    main_logger.info(f"[DEBUG] 输入参数: env_histories长度={len(env_histories)}, save_path={save_path}")
    
    try:
        import matplotlib.pyplot as plt
        
        # 配置中文字体支持
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 选择最佳轨迹进行绘制
        best_history = None
        best_score = 0
        
        for i, history in enumerate(env_histories):
            if len(history['uav_positions']) < 2:
                continue
                
            # 计算轨迹质量分数
            trajectory_length = len(history['uav_positions'])
            positions_array = np.array(history['uav_positions'])
            
            # 计算总移动距离
            total_distance = 0
            for uav_idx in range(positions_array.shape[1]):
                uav_positions = positions_array[:, uav_idx, :2]
                distances = np.sqrt(np.sum(np.diff(uav_positions, axis=0)**2, axis=1))
                total_distance += np.sum(distances)
            
            # 综合评分：长度权重0.7，移动距离权重0.3
            score = trajectory_length * 0.7 + total_distance * 0.3
            
            if score > best_score:
                best_score = score
                best_history = history
        
        if best_history is None:
            main_logger.warning("没有找到合适的轨迹数据进行绘制")
            return
        
        # 使用与visualize_evaluation.py相同的绘图逻辑
        fig, ax = plt.subplots(figsize=(10, 10))
        
        positions_history = np.array(best_history['uav_positions'])
        main_logger.info(f"绘制轨迹数据：{positions_history.shape} (步数={len(positions_history)})")
        
        # 输出调试信息
        for i in range(config.n_agents):
            start_pos = positions_history[0, i, :2]
            end_pos = positions_history[-1, i, :2]
            distance = np.linalg.norm(end_pos - start_pos)
            main_logger.info(f"UAV{i}: 起点({start_pos[0]:.1f}, {start_pos[1]:.1f}) -> 终点({end_pos[0]:.1f}, {end_pos[1]:.1f}), 距离={distance:.1f}m")
        
        # 绘制轨迹（与visualize_evaluation.py完全相同的逻辑）
        for i in range(config.n_agents):
            color = plt.cm.jet(i / config.n_agents)
            ax.plot(positions_history[:, i, 0], positions_history[:, i, 1], 
                    color=color, alpha=0.6, linewidth=1.5,
                    label=f'UAV {i} 轨迹' if i < 3 else "")
            
            # 标记起点和终点
            ax.scatter(positions_history[0, i, 0], positions_history[0, i, 1],
                       marker='o', color=color, s=50, edgecolors='black')
            ax.scatter(positions_history[-1, i, 0], positions_history[-1, i, 1],
                       marker='>', color=color, s=100, edgecolors='black')
        
        # 绘制静态实体（与visualize_evaluation.py相同）
        static_info = best_history['static_info']
        if static_info:
            if 'ground_bs_positions' in static_info and static_info['ground_bs_positions'] is not None:
                bs_pos = static_info['ground_bs_positions']
                ax.scatter(bs_pos[:, 0], bs_pos[:, 1], c='black', marker='s', s=200, 
                          label='地面基站', zorder=5)
            
            if 'user_positions' in static_info and static_info['user_positions'] is not None:
                user_pos = static_info['user_positions']
                ax.scatter(user_pos[:, 0], user_pos[:, 1], c='blue', marker='.', s=50, 
                          label='用户', zorder=5)
        
        # 无人机最终位置
        uav_final_pos = positions_history[-1]
        ax.scatter(uav_final_pos[:, 0], uav_final_pos[:, 1], c='red', marker='^', s=150, 
                  label='UAV (最终位置)', zorder=5)
        
        for i in range(config.n_agents):
            ax.text(uav_final_pos[i, 0] + 10, uav_final_pos[i, 1] + 10, f'UAV{i}', fontsize=9)
        
        ax.set_title('评估结果: 2D拓扑与无人机轨迹（增强版）')
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        
        area_size = static_info.get('area_size', 1000) if static_info else 1000
        ax.set_xlim(0, area_size)
        ax.set_ylim(0, area_size)
        ax.set_aspect('equal', adjustable='box')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # 保存图像
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=200, bbox_inches='tight')
        plt.close(fig)
        main_logger.info(f"增强版2D拓扑图已保存: {save_path}")
        
    except Exception as e:
        main_logger.error(f"生成增强版2D拓扑图时出错: {e}")

def save_evaluation_performance_plot(history, save_path, episode_num):
    """
    生成并保存性能指标随时间变化的图表
    
    参数:
        history: 包含历史数据的字典，包含 'steps', 'connectivity', 'throughput'
        save_path: 图像保存的完整文件路径
        episode_num: episode编号
    """
    try:
        import matplotlib.pyplot as plt
        
        # 配置中文字体支持
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        steps = history['steps']
        connectivity = history['connectivity']
        throughput = history['throughput']
        
        if len(steps) == 0:
            main_logger.warning("没有性能数据可绘制")
            return
        
        # 连通性图
        ax1.plot(steps, connectivity, color='b', marker='.', linestyle='-', label='有效连接用户数')
        ax1.set_title(f'评估 Episode {episode_num}: 网络性能变化')
        ax1.set_ylabel('有效连接用户数')
        ax1.grid(True, linestyle='--', alpha=0.6)
        ax1.legend()
        
        # 吞吐量图
        ax2.plot(steps, throughput, color='g', marker='.', linestyle='-', label='系统吞吐量')
        ax2.set_ylabel('系统吞吐量 (Mbps)')
        ax2.set_xlabel('时间步 (Step)')
        ax2.grid(True, linestyle='--', alpha=0.6)
        ax2.legend()
        
        fig.tight_layout()
        
        # 保存图像
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=200, bbox_inches='tight')
        plt.close(fig)
        main_logger.info(f"性能图表已保存: {save_path}")
        
    except Exception as e:
        main_logger.error(f"生成性能图表时出错: {e}")


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
