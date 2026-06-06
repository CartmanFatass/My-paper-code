import os
import time
import numpy as np
import torch
import argparse
import logging
import cv2

# 使用非GUI后端生成图像，避免训练进程依赖桌面显示或虚拟显示。
os.environ.setdefault('MPLBACKEND', 'Agg')
import matplotlib
matplotlib.use('Agg', force=True)  # 强制使用非GUI后端
import matplotlib.pyplot as plt

from datetime import datetime
import multiprocessing as mp
import pandas as pd
from collections import defaultdict, deque
# from functools import partial # No longer needed for make_env directly
from logger import init_multiproc_logging, get_logger, shutdown_logging, LOG_LEVELS, set_log_level

# 初始化主日志器（如果尚未初始化）
main_logger = get_logger("HMASD-Main")

def convert_numpy_types(obj):
    """
    递归转换numpy类型为原生Python类型，用于JSON序列化
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj

# 导入 Stable Baselines3 的向量化环境
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.env_util import make_vec_env # Can also use this helper

# 导入论文中的配置
# from config_1 import Config # Now dynamically imported
from hmasd.agent import HMASDAgent
from hmasd.sb3_integration import (
    create_hmasd_training_setup, 
    AdvancedNumericalStabilizer,
    PerformanceMonitor,
    HMASDCallback,
    HMASDVecEnvWrapper
)
from hmasd.sharded_vec_env import ShardedSubprocVecEnv
from envs.pettingzoo.scenario4_discrete import UAVForcedRelayEnv
from envs.pettingzoo.scenario5 import UAVBeliefMapEnv
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from torch.utils.tensorboard import SummaryWriter
from visualization import VisualizationManager

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
        self.writer.add_text('Parameters/lr_discoverer_actor', str(self.config.lr_discoverer_actor), 0)
        self.writer.add_text('Parameters/lr_discoverer_critic', str(self.config.lr_discoverer_critic), 0)
        self.writer.add_text('Parameters/lr_discriminator', str(self.config.lr_discriminator), 0)
        
        # 【新增】奖励类型记录
        reward_type = getattr(self.config, 'reward_type', 'health')
        self.writer.add_text('Parameters/reward_type', str(reward_type), 0)
        
        # 【新增】根据奖励类型记录相应的权重参数
        if reward_type == 'health':
            # 网络健康度奖励权重
            self.writer.add_text('Parameters/w_connectivity', str(getattr(self.config, 'w_connectivity', 0.5)), 0)
            self.writer.add_text('Parameters/w_diversity', str(getattr(self.config, 'w_diversity', 1.0)), 0)
            self.writer.add_text('Parameters/w_coverage', str(getattr(self.config, 'w_coverage', 1.0)), 0)
            self.writer.add_text('Parameters/w_dispersion', str(getattr(self.config, 'w_dispersion', 0.05)), 0)
        elif reward_type == 'handover':
            # 切换奖励权重
            self.writer.add_text('Parameters/w_throughput', str(getattr(self.config, 'w_throughput', 1.0)), 0)
            self.writer.add_text('Parameters/w_handover', str(getattr(self.config, 'w_handover', 0.1)), 0)
            self.writer.add_text('Parameters/w_pingpong', str(getattr(self.config, 'w_pingpong', 1.0)), 0)
            self.writer.add_text('Parameters/w_outage', str(getattr(self.config, 'w_outage', 1.0)), 0)
            self.writer.add_text('Parameters/outage_sinr_threshold_db', str(getattr(self.config, 'outage_sinr_threshold_db', -5)), 0)
        elif reward_type == 'qos':
            # QoS奖励模式
            self.writer.add_text('Parameters/reward_mode', 'direct_qos_score', 0)
        elif reward_type == 'naive':
            # 朴素奖励模式（直接使用覆盖率）
            self.writer.add_text('Parameters/reward_mode', 'direct_coverage_ratio', 0)
        
        # 【新增】卡尔曼滤波相关参数记录
        self.writer.add_text('Parameters/enable_predictive_state', str(getattr(self.config, 'enable_predictive_state', False)), 0)
        self.writer.add_text('Parameters/prediction_horizon', str(getattr(self.config, 'prediction_horizon', 3)), 0)
        self.writer.add_text('Parameters/enable_cluster_kalman_filter', str(getattr(self.config, 'enable_cluster_kalman_filter', False)), 0)
        self.writer.add_text('Parameters/predictive_handover', str(getattr(self.config, 'predictive_handover', False)), 0)
        self.writer.add_text('Parameters/user_movement_model', str(getattr(self.config, 'user_movement_model', 'random_walk')), 0)
        
        # 如果启用了RPGM移动模型，记录相关参数
        if getattr(self.config, 'user_movement_model', 'random_walk') == 'rpgm':
            self.writer.add_text('Parameters/cluster_migration_speed', str(getattr(self.config, 'cluster_migration_speed', 15.0)), 0)
            self.writer.add_text('Parameters/cluster_pause_time_range', str(getattr(self.config, 'cluster_pause_time_range', (0, 5))), 0)
            self.writer.add_text('Parameters/user_pause_time_range', str(getattr(self.config, 'user_pause_time_range', (0, 3))), 0)
        
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
        self.writer.add_scalar('Losses/Coordinator/Total', update_info.get('coordinator_loss', 0), step)
        self.writer.add_scalar('Losses/Discoverer/Total', update_info.get('discoverer_loss', 0), step)
        self.writer.add_scalar('Losses/Discriminator/Total', update_info.get('discriminator_loss', 0), step)
        
        # 详细损失组成
        self.writer.add_scalar('Losses/Coordinator/Policy', update_info.get('coordinator_policy_loss', 0), step)
        self.writer.add_scalar('Losses/Coordinator/Value', update_info.get('coordinator_value_loss', 0), step)
        self.writer.add_scalar('Losses/Discoverer/Policy', update_info.get('discoverer_policy_loss', 0), step)
        self.writer.add_scalar('Losses/Discoverer/Value', update_info.get('discoverer_value_loss', 0), step)
        
        # 熵记录
        self.writer.add_scalar('Entropy/Coordinator/TeamSkill_Z', update_info.get('team_skill_entropy', 0), step)
        self.writer.add_scalar('Entropy/Coordinator/AgentSkill_z_Average', update_info.get('agent_skill_entropy', 0), step)
        self.writer.add_scalar('Entropy/Discoverer/Action', update_info.get('action_entropy', 0), step)

        # 奖励记录
        self.writer.add_scalar('Rewards/HighLevel/K_Step_Accumulated_Mean', update_info.get('mean_high_level_reward', 0), step)
        
        # 内在奖励记录 (使用 .get() 方法确保安全访问)
        self.writer.add_scalar('Rewards/Intrinsic/LowLevel_Average', update_info.get('avg_intrinsic_reward', 0), step)
        self.writer.add_scalar('Rewards/Intrinsic/Components/Environmental_Portion_Average', update_info.get('avg_env_comp', 0), step)
        self.writer.add_scalar('Rewards/Intrinsic/Components/TeamDiscriminator_Portion_Average', update_info.get('avg_team_disc_comp', 0), step)
        self.writer.add_scalar('Rewards/Intrinsic/Components/IndividualDiscriminator_Portion_Average', update_info.get('avg_ind_disc_comp', 0), step)

        # 价值函数估计记录
        self.writer.add_scalar('ValueEstimates/Coordinator/StateValue_Mean', update_info.get('mean_coord_state_val', 0), step)
        self.writer.add_scalar('ValueEstimates/Coordinator/AgentValue_Average_Mean', update_info.get('mean_coord_agent_val', 0), step)
        self.writer.add_scalar('ValueEstimates/Discoverer/Value_Mean', update_info.get('avg_discoverer_val', 0), step)

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
            
            # 新增: Episode级别的覆盖率统计
            'episode_coverage_mean': [],
            'episode_coverage_std': [],
            'episode_coverage_min': [],
            'episode_coverage_max': [],
            
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
                'discovered_users_count': [],

                # 网络健康度得分组成
                'rt_final_health_score': [],
                'connectivity_score': [],
                'role_diversity_bonus': [],
                'effective_coverage_score': [],
                'dispersion_penalty': [],
                'serving_uavs_count': [],
                'pure_relay_uavs_count': [],
                'weighted_serving_score': [], # 新增：服务贡献加权分
                
                # 场景5特有：信念地图相关指标
                'belief_map_entropy': [],
                'belief_map_coverage': [],
                'belief_map_max_value': [],
                'belief_map_min_value': [],
                'belief_map_std': [],
                'discovered_vs_predicted': [],
                'belief_prediction_accuracy': [],
                'high_belief_regions_count': [],
                'low_belief_regions_count': [],
                'belief_concentration_ratio': [],
                
                # 【新增】场景4 QoS 和 SINR 分布指标
                'qos_score': [],
                'sinr_dist_below_3dB': [],
                'sinr_dist_3_to_10dB': [],
                'sinr_dist_10_to_20dB': [],
                'sinr_dist_above_20dB': [],
                'sinr_avg_db': [],
                'sinr_min_db': [],
                'sinr_max_db': []
            },
            
            # 【新增】Episode结束时的专门数据记录
            'episode_end_metrics': []  # 存储每个episode结束时的详细性能指标
        }
        
        # 滑动窗口统计 - 使用rollout_length作为窗口大小
        self.window_size = config.rollout_length
        self.recent_rewards = deque(maxlen=self.window_size)
        self.recent_lengths = deque(maxlen=self.window_size)

        # 新增: 用于最差表现优化的性能历史记录
        self.episode_performance_history = []
        
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
        辅助函数：处理数据聚合并写入TensorBoard - 【性能优化版本】使用轻量级聚合，避免DataFrame开销
        
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
            
        # 【性能优化】使用defaultdict直接聚合，避免DataFrame开销
        try:
            # 使用轻量级字典聚合，按环境分组
            env_values = defaultdict(list)
            
            for entry in recent_data:
                if isinstance(entry, dict):
                    env_id = entry.get('env_id', 0)
                    value = entry.get(value_field, 0)
                    if value is not None and not (isinstance(value, float) and np.isnan(value)):
                        env_values[env_id].append(value)
            
            if not env_values:
                return
                
            # 计算每个环境的平均值，然后计算跨环境平均值
            env_means = []
            for env_id, values in env_values.items():
                if values:  # 确保列表不为空
                    env_mean = np.mean(values)
                    if not np.isnan(env_mean):
                        env_means.append(env_mean)
            
            if not env_means:
                return
                
            # 计算最终的跨环境平均值
            final_mean = np.mean(env_means)
            
            # 只写入TensorBoard平均值 - 使用rollout标识
            writer.add_scalar(f'{category}/{metric_name}_Mean_Rollout', final_mean, step)
                
        except Exception as e:
            main_logger.warning(f"聚合指标 {metric_name} 时出错: {e}")
            # 添加更详细的错误信息用于调试
            try:
                main_logger.debug(f"聚合错误详情 - recent_data长度: {len(recent_data) if recent_data else 0}, "
                                 f"env_values键数: {len(env_values) if 'env_values' in locals() else 0}, "
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
            
            # 严格优先使用 'effective_connected_users' - 【关键修复】使用安全的字典访问
            served_users = reward_info.get('effective_connected_users')
            if served_users is None:
                # 如果没有 effective_connected_users，则回退到 connected_users
                served_users = reward_info.get('connected_users')
            
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

                # 网络健康度得分组成
                health_score_keys = [
                    'rt_final_health_score', 'connectivity_score', 'role_diversity_bonus',
                    'effective_coverage_score', 'dispersion_penalty', 'serving_uavs_count',
                    'pure_relay_uavs_count', 'weighted_serving_score' # 新增
                ]
                for key in health_score_keys:
                    if key in reward_info:
                        self.performance_metrics['reward_components'][key].append({
                            'step': step, 'env_id': env_id, 'value': reward_info[key], 'timestamp': time.time()
                        })
                
                # 【新增】切换奖励特有指标记录
                handover_reward_keys = [
                    'handover_reward', 'handover_penalty', 'ping_pong_penalty', 
                    'outage_penalty', 'outage_users', 'outage_ratio',
                    'handover_increment', 'ping_pong_increment',
                    'serving_set_changes', 'uav_joins', 'uav_leaves'
                ]
                for key in handover_reward_keys:
                    if key in reward_info:
                        # 确保列表存在
                        if key not in self.performance_metrics['reward_components']:
                            self.performance_metrics['reward_components'][key] = []
                        
                        self.performance_metrics['reward_components'][key].append({
                            'step': step, 'env_id': env_id, 'value': reward_info[key], 'timestamp': time.time()
                        })
                
                # 【新增】卡尔曼滤波相关指标记录
                kalman_filter_keys = [
                    'kalman_prediction_accuracy', 'kalman_innovation_variance', 
                    'kalman_state_uncertainty', 'cluster_kalman_accuracy',
                    'user_prediction_error', 'cluster_prediction_error',
                    'kalman_filter_convergence', 'prediction_horizon_accuracy'
                ]
                for key in kalman_filter_keys:
                    if key in reward_info:
                        # 确保列表存在
                        if key not in self.performance_metrics['reward_components']:
                            self.performance_metrics['reward_components'][key] = []
                        
                        self.performance_metrics['reward_components'][key].append({
                            'step': step, 'env_id': env_id, 'value': reward_info[key], 'timestamp': time.time()
                        })

                # 【新增】QoS 和 SINR 分布指标记录
                qos_sinr_keys = [
                    'qos_score', 'sinr_dist_below_3dB', 'sinr_dist_3_to_10dB',
                    'sinr_dist_10_to_20dB', 'sinr_dist_above_20dB', 'sinr_avg_db',
                    'sinr_min_db', 'sinr_max_db'
                ]
                for key in qos_sinr_keys:
                    if key in reward_info:
                        # 确保列表存在
                        if key not in self.performance_metrics['reward_components']:
                            self.performance_metrics['reward_components'][key] = []
                        
                        self.performance_metrics['reward_components'][key].append({
                            'step': step, 'env_id': env_id, 'value': reward_info[key], 'timestamp': time.time()
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
        
        # 场景5特有：信念地图相关指标记录
        if info and hasattr(info, 'get'):
            # 尝试从环境info中提取信念地图数据
            belief_map_data = info.get('belief_map_data', None)
            if belief_map_data:
                self._log_belief_map_metrics(step, env_id, belief_map_data)
            
            # 如果环境直接提供了信念地图统计信息
            if 'belief_map_stats' in info:
                belief_stats = info['belief_map_stats']
                for stat_name, stat_value in belief_stats.items():
                    if stat_name in self.performance_metrics['reward_components']:
                        self.performance_metrics['reward_components'][stat_name].append({
                            'step': step,
                            'env_id': env_id,
                            'value': stat_value,
                            'timestamp': time.time()
                        })
    
    def _log_belief_map_metrics(self, step, env_id, belief_map_data):
        """
        处理信念地图数据并计算关键统计指标
        
        参数:
            step: 当前步数
            env_id: 环境ID
            belief_map_data: 从环境获取的信念地图数据，包含：
                - belief_map: 信念地图矩阵 (grid_resolution x grid_resolution)
                - discovered_users_this_episode: 本episode发现的用户集合
                - total_users: 总用户数
                - grid_resolution: 栅格分辨率
        """
        try:
            belief_map = belief_map_data.get('belief_map', None)
            if belief_map is None:
                return
            
            # 确保belief_map是numpy数组
            if not isinstance(belief_map, np.ndarray):
                belief_map = np.array(belief_map)
            
            # 1. 计算信念地图熵 (Shannon Entropy)
            # H = -Σ p_i * log(p_i)，衡量信念分布的不确定性
            flat_belief = belief_map.flatten()
            # 过滤掉零值以避免log(0)
            non_zero_beliefs = flat_belief[flat_belief > 1e-12]
            if len(non_zero_beliefs) > 0:
                belief_entropy = -np.sum(non_zero_beliefs * np.log(non_zero_beliefs + 1e-12))
            else:
                belief_entropy = 0.0
            
            # 2. 计算信念地图覆盖度 (有效信念区域比例)
            # 定义"有效信念"阈值，高于此阈值的区域被认为是有意义的
            effective_belief_threshold = 1.0 / (belief_map.size * 0.1)  # 比均匀分布高10倍
            effective_regions = np.sum(belief_map > effective_belief_threshold)
            belief_coverage = effective_regions / belief_map.size
            
            # 3. 计算信念地图的基本统计量
            belief_max = np.max(belief_map)
            belief_min = np.min(belief_map)
            belief_std = np.std(belief_map)
            
            # 4. 计算发现准确性指标
            discovered_users = belief_map_data.get('discovered_users_this_episode', set())
            total_users = belief_map_data.get('total_users', 0)
            
            # 发现进度 = 已发现用户数 / 总用户数
            discovery_progress = len(discovered_users) / total_users if total_users > 0 else 0
            
            # 5. 计算信念预测准确性
            # 这需要用户的实际位置信息，如果环境提供的话
            user_positions = belief_map_data.get('user_positions', None)
            prediction_accuracy = 0.0
            if user_positions is not None:
                grid_resolution = belief_map_data.get('grid_resolution', 100)
                area_size = belief_map_data.get('area_size', 2500)
                
                # 计算每个用户所在栅格的信念值
                user_belief_values = []
                for user_pos in user_positions:
                    # 转换用户位置到栅格坐标
                    gx = int(np.clip(user_pos[0] / area_size * grid_resolution, 0, grid_resolution - 1))
                    gy = int(np.clip(user_pos[1] / area_size * grid_resolution, 0, grid_resolution - 1))
                    user_belief_values.append(belief_map[gy, gx])
                
                # 预测准确性 = 用户所在位置的平均信念值
                prediction_accuracy = np.mean(user_belief_values) if user_belief_values else 0.0
            
            # 6. 计算高/低信念区域数量
            # 高信念区域：信念值高于平均值的2倍
            mean_belief = np.mean(belief_map)
            high_belief_threshold = mean_belief * 2.0
            low_belief_threshold = mean_belief * 0.5
            
            high_belief_regions = np.sum(belief_map > high_belief_threshold)
            low_belief_regions = np.sum(belief_map < low_belief_threshold)
            
            # 7. 计算信念集中度比例
            # 前10%最高信念区域包含的总信念量
            sorted_beliefs = np.sort(belief_map.flatten())[::-1]  # 降序排列
            top_10_percent_count = max(1, int(0.1 * len(sorted_beliefs)))
            top_10_percent_belief = np.sum(sorted_beliefs[:top_10_percent_count])
            belief_concentration_ratio = top_10_percent_belief
            
            # 8. 记录所有计算出的指标
            belief_metrics = {
                'belief_map_entropy': belief_entropy,
                'belief_map_coverage': belief_coverage,
                'belief_map_max_value': belief_max,
                'belief_map_min_value': belief_min,
                'belief_map_std': belief_std,
                'discovered_vs_predicted': discovery_progress,
                'belief_prediction_accuracy': prediction_accuracy,
                'high_belief_regions_count': high_belief_regions,
                'low_belief_regions_count': low_belief_regions,
                'belief_concentration_ratio': belief_concentration_ratio
            }
            
            # 将指标添加到性能指标记录中
            for metric_name, metric_value in belief_metrics.items():
                if metric_name in self.performance_metrics['reward_components']:
                    self.performance_metrics['reward_components'][metric_name].append({
                        'step': step,
                        'env_id': env_id,
                        'value': metric_value,
                        'timestamp': time.time()
                    })
            
        except Exception as e:
            main_logger.warning(f"处理信念地图指标时出错 (步骤 {step}, 环境 {env_id}): {e}")
    
    def log_episode_completion(self, episode_num, env_id, total_reward, episode_length, info=None):
        """记录episode完成信息 - 增强版本，专门捕获episode结束时的性能指标"""
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
        
        # 【新增】专门记录episode结束时的详细性能指标
        # 这些数据将用于生成"Episode End"类别的TensorBoard图表
        if info and 'reward_info' in info:
            episode_end_data = {
                'episode': episode_num,
                'env_id': env_id,
                'total_reward': total_reward,
                'episode_length': episode_length,
                'timestamp': time.time(),
                'final_metrics': info['reward_info'].copy()  # 复制完整的reward_info
            }
            
            # 添加一些计算出的衍生指标
            reward_info = info['reward_info']
            if 'effective_connected_users' in reward_info and self.n_users:
                episode_end_data['final_coverage_rate'] = reward_info['effective_connected_users'] / self.n_users
            
            if 'coverage_ratio' in reward_info:
                episode_end_data['final_coverage_ratio'] = reward_info['coverage_ratio']
            
            # 存储到专门的episode结束指标列表
            self.performance_metrics['episode_end_metrics'].append(episode_end_data)
            
            main_logger.debug(f"Episode {episode_num} (环境 {env_id}) 结束时指标已记录: "
                             f"覆盖率={episode_end_data.get('final_coverage_ratio', 'N/A')}, "
                             f"连接用户={reward_info.get('effective_connected_users', 'N/A')}")
        
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
        
        # 场景5特有：信念地图统计 - 新的BeliefMap分类
        belief_map_fields = [
            'belief_map_entropy', 'belief_map_coverage', 'belief_map_max_value',
            'belief_map_min_value', 'belief_map_std', 'discovered_vs_predicted',
            'belief_prediction_accuracy', 'high_belief_regions_count',
            'low_belief_regions_count', 'belief_concentration_ratio'
        ]
        
        for field in belief_map_fields:
            if reward_components.get(field):
                self._log_aggregated_metrics(writer, step,
                                           reward_components[field],
                                           field.replace('_', ' ').title().replace(' ', '_'),
                                           'BeliefMap')
        
        # 【新增】记录Episode结束时的指标到TensorBoard
        self._log_episode_end_metrics_to_tensorboard(writer, step)

        # 【新增】记录QoS和SINR分布指标
        self._log_qos_and_sinr_metrics_to_tensorboard(writer, step)

        # 【新增】记录软切换指标
        self._log_soft_handover_metrics_to_tensorboard(writer, step)

        # 【新增】记录切换奖励指标
        self._log_handover_reward_metrics_to_tensorboard(writer, step)

    def _log_handover_reward_metrics_to_tensorboard(self, writer, step):
        """记录切换奖励相关指标到TensorBoard"""
        reward_components = self.performance_metrics['reward_components']
        
        # 切换奖励特有指标
        handover_fields = [
            'handover_reward', 'handover_penalty', 'ping_pong_penalty', 
            'outage_penalty', 'outage_users', 'outage_ratio',
            'handover_increment', 'ping_pong_increment'
        ]
        
        for field in handover_fields:
            if reward_components.get(field):
                self._log_aggregated_metrics(writer, step,
                                           reward_components[field],
                                           field.replace('_', ' ').title().replace(' ', '_'),
                                           'HandoverReward')

    def _log_soft_handover_metrics_to_tensorboard(self, writer, step):
        """记录软切换相关指标到TensorBoard"""
        reward_components = self.performance_metrics['reward_components']
        
        soft_handover_keys = [
            'serving_set_changes', 'uav_joins', 'uav_leaves'
        ]
        
        for key in soft_handover_keys:
            if reward_components.get(key):
                self._log_aggregated_metrics(writer, step,
                                           reward_components[key],
                                           key.replace('_', ' ').title().replace(' ', '_'),
                                           'SoftHandover')

    def _log_qos_and_sinr_metrics_to_tensorboard(self, writer, step):
        """记录服务质量(QoS)和SINR分布指标到TensorBoard"""
        reward_components = self.performance_metrics['reward_components']
        
        # QoS得分
        self._log_aggregated_metrics(writer, step, 
                                   reward_components.get('qos_score', []), 
                                   'QoS_Score', 
                                   'QoS')
        
        # SINR统计
        self._log_aggregated_metrics(writer, step, 
                                   reward_components.get('sinr_avg_db', []), 
                                   'SINR_Average_dB', 
                                   'QoS')
        self._log_aggregated_metrics(writer, step, 
                                   reward_components.get('sinr_min_db', []), 
                                   'SINR_Min_dB', 
                                   'QoS')
        self._log_aggregated_metrics(writer, step, 
                                   reward_components.get('sinr_max_db', []), 
                                   'SINR_Max_dB', 
                                   'QoS')

        # SINR分布
        self._log_aggregated_metrics(writer, step, 
                                   reward_components.get('sinr_dist_below_3dB', []), 
                                   'Distribution_Below_3dB', 
                                   'QoS/SINR_Distribution')
        self._log_aggregated_metrics(writer, step, 
                                   reward_components.get('sinr_dist_3_to_10dB', []), 
                                   'Distribution_3_to_10dB', 
                                   'QoS/SINR_Distribution')
        self._log_aggregated_metrics(writer, step, 
                                   reward_components.get('sinr_dist_10_to_20dB', []), 
                                   'Distribution_10_to_20dB', 
                                   'QoS/SINR_Distribution')
        self._log_aggregated_metrics(writer, step, 
                                   reward_components.get('sinr_dist_above_20dB', []), 
                                   'Distribution_Above_20dB', 
                                   'QoS/SINR_Distribution')

    def _log_episode_end_metrics_to_tensorboard(self, writer, step):
        """
        专门记录episode结束时的性能指标到TensorBoard
        
        这些指标与rollout过程中的平均指标形成对比，帮助分析算法的真实性能
        
        参数:
            writer: TensorBoard writer
            step: 当前步数
        """
        if not self.performance_metrics['episode_end_metrics']:
            return
        
        # 使用最近的episode结束数据（使用episode数量作为窗口大小）
        recent_episodes = self.performance_metrics['episode_end_metrics'][-self.window_size:]
        if not recent_episodes:
            return
        
        # 提取各项指标的episode结束时数值
        episode_end_coverage_ratios = []
        episode_end_connected_users = []
        episode_end_health_scores = []
        episode_end_connectivity_scores = []
        episode_end_diversity_scores = []
        episode_end_dispersion_penalties = []
        episode_end_serving_uavs = []
        episode_end_relay_uavs = []
        episode_end_avg_hops = []
        episode_end_system_throughput = []
        
        for episode_data in recent_episodes:
            final_metrics = episode_data.get('final_metrics', {})
            
            # 覆盖率相关指标
            if 'coverage_ratio' in final_metrics:
                episode_end_coverage_ratios.append(final_metrics['coverage_ratio'])
            
            if 'effective_connected_users' in final_metrics:
                episode_end_connected_users.append(final_metrics['effective_connected_users'])
            
            # 网络健康度相关指标
            if 'rt_final_health_score' in final_metrics:
                episode_end_health_scores.append(final_metrics['rt_final_health_score'])
            
            if 'connectivity_score' in final_metrics:
                episode_end_connectivity_scores.append(final_metrics['connectivity_score'])
            
            if 'role_diversity_bonus' in final_metrics:
                episode_end_diversity_scores.append(final_metrics['role_diversity_bonus'])
            
            if 'dispersion_penalty' in final_metrics:
                episode_end_dispersion_penalties.append(final_metrics['dispersion_penalty'])
            
            if 'serving_uavs_count' in final_metrics:
                episode_end_serving_uavs.append(final_metrics['serving_uavs_count'])
            
            if 'pure_relay_uavs_count' in final_metrics:
                episode_end_relay_uavs.append(final_metrics['pure_relay_uavs_count'])
            
            if 'avg_hops' in final_metrics:
                episode_end_avg_hops.append(final_metrics['avg_hops'])
            
            if 'system_throughput_mbps' in final_metrics:
                episode_end_system_throughput.append(final_metrics['system_throughput_mbps'])
        
        # 计算并记录各项指标的episode结束时平均值
        if episode_end_coverage_ratios:
            avg_final_coverage = np.mean(episode_end_coverage_ratios)
            writer.add_scalar('Performance/EpisodeEnd/Coverage_Ratio_Final', avg_final_coverage, step)
        
        # 新增: 记录Episode覆盖率的min, max, std
        episode_end_coverage_std = [m.get('final_metrics', {}).get('episode_coverage_std', 0) for m in recent_episodes]
        episode_end_coverage_min = [m.get('final_metrics', {}).get('episode_coverage_min', 0) for m in recent_episodes]
        episode_end_coverage_max = [m.get('final_metrics', {}).get('episode_coverage_max', 0) for m in recent_episodes]

        if episode_end_coverage_std:
            writer.add_scalar('Performance/EpisodeEnd/Coverage_Std_Final', np.mean(episode_end_coverage_std), step)
        if episode_end_coverage_min:
            writer.add_scalar('Performance/EpisodeEnd/Coverage_Min_Final', np.mean(episode_end_coverage_min), step)
        if episode_end_coverage_max:
            writer.add_scalar('Performance/EpisodeEnd/Coverage_Max_Final', np.mean(episode_end_coverage_max), step)

        if episode_end_connected_users:
            avg_final_connected = np.mean(episode_end_connected_users)
            writer.add_scalar('Performance/EpisodeEnd/Connected_Users_Final', avg_final_connected, step)
            
            # 计算最终服务率
            if self.n_users:
                final_service_rate = avg_final_connected / self.n_users
                writer.add_scalar('Performance/EpisodeEnd/Service_Rate_Final', final_service_rate, step)
        
        if episode_end_health_scores:
            avg_final_health = np.mean(episode_end_health_scores)
            writer.add_scalar('HealthScore/EpisodeEnd/Final_Health_Score', avg_final_health, step)
        
        if episode_end_connectivity_scores:
            avg_final_connectivity = np.mean(episode_end_connectivity_scores)
            writer.add_scalar('HealthScore/EpisodeEnd/Connectivity_Score_Final', avg_final_connectivity, step)
        
        if episode_end_diversity_scores:
            avg_final_diversity = np.mean(episode_end_diversity_scores)
            writer.add_scalar('HealthScore/EpisodeEnd/Role_Diversity_Final', avg_final_diversity, step)
        
        if episode_end_dispersion_penalties:
            avg_final_dispersion = np.mean(episode_end_dispersion_penalties)
            writer.add_scalar('HealthScore/EpisodeEnd/Dispersion_Penalty_Final', avg_final_dispersion, step)
        
        if episode_end_serving_uavs:
            avg_final_serving = np.mean(episode_end_serving_uavs)
            writer.add_scalar('HealthScore/EpisodeEnd/Serving_UAVs_Final', avg_final_serving, step)
        
        if episode_end_relay_uavs:
            avg_final_relay = np.mean(episode_end_relay_uavs)
            writer.add_scalar('HealthScore/EpisodeEnd/Relay_UAVs_Final', avg_final_relay, step)
        
        if episode_end_avg_hops:
            avg_final_hops = np.mean(episode_end_avg_hops)
            writer.add_scalar('Performance/EpisodeEnd/Avg_Hops_Final', avg_final_hops, step)
        
        if episode_end_system_throughput:
            avg_final_throughput = np.mean(episode_end_system_throughput)
            writer.add_scalar('Performance/EpisodeEnd/System_Throughput_Final', avg_final_throughput, step)
        
        main_logger.debug(f"已记录 {len(recent_episodes)} 个episode的结束时指标到TensorBoard")

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
                
                # 场景4新增：网络健康度统计 - 新的HealthScore分类
                health_score_fields = [
                    'rt_final_health_score', 'connectivity_score', 'role_diversity_bonus',
                    'effective_coverage_score', 'dispersion_penalty', 'serving_uavs_count',
                    'pure_relay_uavs_count', 'weighted_serving_score' # 新增
                ]

                for field in health_score_fields:
                    if reward_components.get(field):
                        self._log_aggregated_metrics(writer, step,
                                                   reward_components[field],
                                                   field.replace('_', ' ').title().replace(' ', '_'),
                                                   'HealthScore')
                
                # 【新增】根据奖励类型记录特定的奖励组成部分
                reward_type = getattr(self.config, 'reward_type', 'health')
                
                if reward_type == 'naive':
                    # 朴素奖励模式：主要关注覆盖率
                    writer.add_scalar('NaiveReward/Coverage_Ratio_Direct', 
                                    np.mean([r['value'] for r in reward_components.get('coverage_ratios', [])[-self.window_size:]]) 
                                    if reward_components.get('coverage_ratios') else 0, step)
                
                # 【新增】卡尔曼滤波相关指标的TensorBoard记录
                kalman_filter_fields = [
                    'kalman_prediction_accuracy', 'kalman_innovation_variance', 
                    'kalman_state_uncertainty', 'cluster_kalman_accuracy',
                    'user_prediction_error', 'cluster_prediction_error',
                    'kalman_filter_convergence', 'prediction_horizon_accuracy'
                ]
                
                for field in kalman_filter_fields:
                    if reward_components.get(field):
                        self._log_aggregated_metrics(writer, step,
                                                   reward_components[field],
                                                   field.replace('_', ' ').title().replace(' ', '_'),
                                                   'KalmanFilter')

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
    创建环境实例的函数 (用于 SubprocVecEnv) - 使用config对象传递参数

    参数:
        rank: 环境的索引 (用于设置不同的种子)
        seed: 基础随机种子
        config: 配置对象，包含所有环境参数和奖励权重
        scenario: 场景编号 (1=基站模式, 2=协作组网模式, 3=强制多跳模式, 4=强制中继模式, 5=信念地图模式)
        render_mode: 渲染模式

    返回:
        一个返回环境实例的函数
    """
    def _init():
        env_seed = seed + rank # 为每个并行环境设置不同的种子
        
        if scenario == 4:
            # 场景4：强制多跳中继环境 - 直接传入config对象
            raw_env = UAVForcedRelayEnv(
                config=config,
                render_mode=render_mode,
                seed=env_seed
            )
        elif scenario == 5:
            # 场景5：基于信念地图的动态用户覆盖环境 - 直接传入config对象
            raw_env = UAVBeliefMapEnv(
                config=config,
                render_mode=render_mode,
                seed=env_seed
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
    
    # 实验管理参数
    parser.add_argument('--exp_name', type=str, default='hmasd_experiment', help='实验名称，用于组织日志')
    parser.add_argument('--seed', type=int, default=1, help='随机种子')
    parser.add_argument('--config', type=str, default='config_1', help='要使用的配置文件名 (不带.py后缀)')
    
    # 运行模式和环境参数
    parser.add_argument('--mode', type=str, default='train', help='运行模式: train或eval')
    parser.add_argument('--scenario', type=int, default=4, help='场景: 1=基站模式, 2=协作组网模式, 3=强制多跳模式, 4=强制中继模式, 5=信念地图模式')
    parser.add_argument('--model_path', type=str, default='models/hmasd_multiproc_paper_config.pt', help='模型保存/加载路径')
    parser.add_argument('--log_dir', type=str, default='../tf-logs', help='日志目录')
    parser.add_argument('--log_level', type=str, default='info', 
                        choices=['debug', 'info', 'warning', 'error', 'critical'], 
                        help='日志级别 (debug=详细, info=信息, warning=警告, error=错误, critical=严重)')
    parser.add_argument('--console_log_level', type=str, default='error', 
                        choices=['debug', 'info', 'warning', 'error', 'critical'], 
                        help='控制台日志级别')
    parser.add_argument('--eval_episodes', type=int, default=10, help='评估的episode数量')
    parser.add_argument('--render', action=argparse.BooleanOptionalAction, default=False,
                        help='是否实时渲染环境（使用--render启用，--no-render禁用）')
    parser.add_argument('--record_video', action=argparse.BooleanOptionalAction, default=False,
                        help='是否将评估过程录制为视频（使用--record_video启用，--no-record_video禁用）')
    parser.add_argument('--device', type=str, default='auto',
                        choices=['auto', 'cuda', 'cpu'], help='计算设备: auto=自动选择, cuda=GPU, cpu=CPU')
    parser.add_argument('--resume_from', type=str, default='', 
                        help='预训练模型路径，用于继续训练（如果为空则从头开始训练）')

    # 并行参数 (可覆盖配置文件中的值)
    parser.add_argument('--num_envs', type=int, default=0, 
                        help='并行环境数量 (0=使用配置文件中的值)')
    parser.add_argument('--num_workers', type=int, default=0,
                        help='分片采样worker数量 (0=自动，根据num_envs和envs_per_worker计算)')
    parser.add_argument('--envs_per_worker', type=int, default=0,
                        help='每个分片worker内串行运行的环境数量 (0=自动)')
    parser.add_argument('--collector_backend', type=str, default='auto',
                        choices=['auto', 'sharded', 'subproc'],
                        help='训练采样后端: auto=按环境数自动选择, sharded=分片共享内存, subproc=SB3 SubprocVecEnv')
    parser.add_argument('--metrics_mode', type=str, default='light',
                        choices=['light', 'full', 'train_only'],
                        help='分片采样器回传指标级别: light=核心指标, full=完整info, train_only=只训练')
    parser.add_argument('--eval_rollout_threads', type=int, default=0, 
                        help='评估时的并行线程数 (0=使用配置文件中的值)')
    parser.add_argument('--rollout_length', type=int, default=0,
                        help='覆盖配置中的rollout长度 (0=使用配置文件)')
    parser.add_argument('--total_timesteps', type=int, default=0,
                        help='覆盖配置中的总训练步数 (0=使用配置文件)')
    parser.add_argument('--eval_interval', type=int, default=0,
                        help='覆盖配置中的评估间隔 (0=使用配置文件)')
    parser.add_argument('--disable_eval', action='store_true',
                        help='训练期间禁用定期评估')
    parser.add_argument('--strict_hmasd_alignment', action=argparse.BooleanOptionalAction, default=None,
                        help='严格按HMASD论文对齐高层样本语义（默认使用配置文件）')
    parser.add_argument('--stability_check_interval', type=int, default=10,
                        help='数值稳定性检查间隔（按vector step计；1=每步，0=禁用）')
    parser.add_argument('--memory_monitor_interval', type=int, default=16,
                        help='显存监控间隔（按vector step计；1=每步）')
    
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
    parser.add_argument('--debug', action='store_true', help='启用调试模式，在训练期间收集数据并生成拓扑图')
    
    return parser.parse_args()

# 训练函数
def train(vec_env, eval_vec_env, config, args, device, trial=None, eval_env_fns=None): # Add eval_vec_env parameter
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

    # 设置随机种子以保证可复现性
    import random
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    random.seed(args.seed)
    main_logger.info(f"已为torch, numpy, random设置随机种子: {args.seed}")

    # 使用实验名称和种子来创建结构化的日志目录
    log_dir = os.path.join(args.log_dir, args.exp_name, f"seed_{args.seed}")
    os.makedirs(log_dir, exist_ok=True)
    
    # 模型保存路径也应结构化
    model_dir = os.path.join(log_dir, 'models')
    os.makedirs(model_dir, exist_ok=True)
    # 更新模型路径以包含新的目录结构
    args.model_path = os.path.join(model_dir, 'best_model.pt')
    
    # 创建HMASD代理（不再有TensorBoard writer）
    agent = HMASDAgent(config, log_dir=log_dir, device=device)
    
    # 创建增强的训练设置
    main_logger.info("设置增强的训练环境...")
    wrapped_vec_env, callbacks, performance_monitor, numerical_stabilizer = create_hmasd_training_setup(
        agent, vec_env, log_dir
    )
    
    # 确保智能体使用SB3集成的组件
    if hasattr(agent, 'numerical_stabilizer') and agent.numerical_stabilizer is not None:
        main_logger.info(f"智能体已使用SB3数值稳定器: {type(agent.numerical_stabilizer).__name__}")
    else:
        main_logger.info("智能体将使用训练设置中的数值稳定器")
        agent.numerical_stabilizer = numerical_stabilizer
    
    if hasattr(agent, 'metrics_collector') and agent.metrics_collector is not None:
        main_logger.info(f"智能体已使用SB3指标收集器: {type(agent.metrics_collector).__name__}")
    else:
        main_logger.info("智能体将使用内置指标收集器")
    
    # 创建统一的TensorBoard管理器
    tb_manager = TensorBoardManager(log_dir, config)
    
    # 如果指定了预训练模型路径，加载模型继续训练
    resume_from = getattr(args, 'resume_from', '')
    if resume_from and os.path.exists(resume_from):
        main_logger.info(f"加载预训练模型: {resume_from}")
        try:
            # 为了兼容新版PyTorch的安全加载机制，添加Config类到安全全局列表
            import torch.serialization
            # Config is now defined in main and passed to train
            # torch.serialization.add_safe_globals([Config])
            # main_logger.debug("已将Config类添加到PyTorch安全全局列表")

            agent.load_model(resume_from)
            main_logger.info(f"成功加载预训练模型，将在此基础上继续训练")

            # 记录续训信息到TensorBoard
            tb_manager.add_text('Training/resumed_from', resume_from, 0)
            tb_manager.add_text('Training/mode', 'resume_training', 0)
        except Exception as e:
            main_logger.error(f"加载预训练模型失败: {e}")
            main_logger.info("将从头开始训练")
            tb_manager.add_text('Training/mode', 'from_scratch_due_to_load_error', 0)
    elif resume_from:
        main_logger.warning(f"指定的预训练模型文件不存在: {resume_from}")
        main_logger.info("将从头开始训练")
        tb_manager.add_text('Training/mode', 'from_scratch_due_to_missing_file', 0)
    else:
        main_logger.info("从头开始训练")
        tb_manager.add_text('Training/mode', 'from_scratch', 0)
    
    # 创建增强的奖励追踪器
    reward_tracker = EnhancedRewardTracker(log_dir, config, n_users=config.n_users)
    reward_tracker.export_interval = args.export_interval
    
    # 调试模式下的可视化设置
    visualizers = None
    static_infos = None
    if args.debug:
        main_logger.info("调试模式已启用：将在训练期间生成拓扑图。")
        main_logger.warning("注意：在调试模式下，由于需要频繁从环境获取状态，训练速度会显著下降。")
        visualizers = [VisualizationManager(episode_num=i, log_dir=log_dir, config=config) for i in range(num_envs)]
        
        # 收集一次静态信息
        try:
            initial_env_states = [vec_env.env_method('get_current_state', indices=[i])[0] for i in range(num_envs)]
            static_infos = []
            for env_state in initial_env_states:
                static_infos.append({
                    'ground_bs_positions': env_state.get('ground_bs_positions'),
                    'area_size': env_state.get('area_size')
                })
            main_logger.info("已为所有环境收集静态信息用于调试可视化。")
        except Exception as e:
            main_logger.error(f"为调试模式收集静态信息时出错: {e}")
            main_logger.warning("无法收集静态信息，拓扑图可能不完整。将禁用调试模式。")
            args.debug = False # 出现错误时禁用调试模式
    
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
    
    # 【新增】用于存储评估结果的列表
    eval_steps_history = []
    eval_mean_rewards_history = []
    eval_std_rewards_history = []
    created_eval_vec_env = False
    
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

    # 初始化并启动回调
    for callback in callbacks:
        # 传递 agent 作为模型，并初始化
        callback.init_callback(agent)
        callback.on_training_start(locals(), globals())

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
    
    # 环境状态跟踪 (现在是批量的)
    env_steps = np.zeros(num_envs, dtype=int)
    dones_tracker = np.zeros(num_envs, dtype=bool) # 跟踪上一步的dones
    episode_rewards_tracker = np.zeros(num_envs, dtype=np.float32)

    while total_steps < config.total_timesteps:
        # 调用 on_rollout_start 回调
        for callback in callbacks:
            callback.on_rollout_start()

        # --- Start of NEW, CORRECTED & BATCHED Rollout Loop ---
        for rollout_step in range(config.rollout_length):
            step_start_time = time.time()
            
            # 1. 批量选择动作 (只调用一次 agent.step)
            # 传递上一步的 dones_tracker 以便正确重置内部状态
            actions_batch, infos_batch = agent.step(
                states, observations, env_steps, dones_tracker, deterministic=False
            )
            
            # 2. 批量执行环境步骤
            next_observations, rewards, dones, infos = wrapped_vec_env.step(actions_batch)

            # 3. 批量提取下一个状态
            next_states = np.array([info.get('next_state', np.zeros(config.state_dim)) for info in infos])

            # 4. 数值稳定性检查。该检查主要用于诊断，默认降频以减少每步Tensor构造开销。
            if args.stability_check_interval > 0 and rollout_step % args.stability_check_interval == 0:
                tensor_dict = {
                    'states': torch.FloatTensor(states),
                    'next_states': torch.FloatTensor(next_states),
                    'observations': torch.FloatTensor(observations),
                    'next_observations': torch.FloatTensor(next_observations),
                    'actions': torch.FloatTensor(actions_batch),
                    'rewards': torch.FloatTensor(rewards)
                }
                tensor_dict = numerical_stabilizer.comprehensive_check(tensor_dict)

            # 5. 批量存储经验。done环境中collector会返回reset后的next_observation用于下一步策略输入；
            # rollout/discriminator数据必须使用terminal_observation，避免把新episode初始观测写进终止transition。
            storage_next_states = next_states.copy()
            storage_next_observations = next_observations.copy()
            for i in range(num_envs):
                if dones[i] and 'terminal_state' in infos[i]:
                    storage_next_states[i] = infos[i]['terminal_state']
                if dones[i] and 'terminal_observation' in infos[i]:
                    storage_next_observations[i] = infos[i]['terminal_observation']

            agent.store_transition_batch(
                states=states,
                next_states=storage_next_states,
                observations=observations,
                next_observations=storage_next_observations,
                actions=actions_batch,
                rewards=rewards,
                dones=dones,
                infos_batch=infos_batch,
                rollout_step_idx=rollout_step
            )

            # 6. 更新逐环境追踪器、日志和episode状态
            for i in range(num_envs):
                # 记录每一步的详细信息
                reward_tracker.log_training_step(total_steps + i, i, rewards[i], info=infos[i])

                # 更新追踪器
                env_steps[i] += 1
                episode_rewards_tracker[i] += rewards[i]
                
                # 如果启用调试模式，则记录可视化数据
                if args.debug and visualizers is not None:
                    try:
                        # 【关键修复】从嵌套的info结构中正确提取UAV位置
                        # 尝试从 infos_dict 中的任意一个智能体获取共享的 uav_positions
                        uav_positions = np.zeros((agent.config.n_agents, 3))
                        if 'infos_dict' in infos[i] and infos[i]['infos_dict']:
                            # 从第一个可用的智能体信息中获取 uav_positions
                            for agent_key, agent_info in infos[i]['infos_dict'].items():
                                if 'uav_positions' in agent_info:
                                    uav_positions = agent_info['uav_positions']
                                    break
                        # 如果仍然没有找到，尝试直接从 infos[i] 获取
                        if np.array_equal(uav_positions, np.zeros((agent.config.n_agents, 3))):
                            uav_positions = infos[i].get('uav_positions', np.zeros((agent.config.n_agents, 3)))

                        # 【修复】确保reward_info包含完整的性能数据
                        reward_info = infos[i].get('reward_info', {})
                        
                        # 调试输出：检查reward_info内容
                        if env_steps[i] % 100 == 0:  # 每100步输出一次调试信息
                            main_logger.debug(f"[调试模式] 环境 {i} 步骤 {env_steps[i]} reward_info内容: "
                                             f"coverage_ratio={reward_info.get('coverage_ratio', 'N/A')}, "
                                             f"effective_connected_users={reward_info.get('effective_connected_users', 'N/A')}, "
                                             f"system_throughput_mbps={reward_info.get('system_throughput_mbps', 'N/A')}")

                        visualizers[i].record_step(
                            step_count=env_steps[i],
                            uav_positions=uav_positions,
                            team_skill=infos_batch[i].get('team_skill', -1),
                            agent_skills=infos_batch[i].get('agent_skills', []),
                            reward_info=reward_info,
                            static_info=static_infos[i] if static_infos else {},
                            # 【修复】在调试模式下传递连接和路由信息
                            connections=reward_info.get('connections'),
                            routing_paths=reward_info.get('routing_paths')
                        )
                    except Exception as e:
                        main_logger.warning(f"[调试模式] 环境 {i} 记录步骤数据时出错: {e}")
                        # 添加更详细的错误信息
                        main_logger.debug(f"[调试模式] 错误详情 - infos[{i}]键: {list(infos[i].keys()) if infos[i] else 'None'}")

                if dones[i]:
                    # 【关键修复】Episode结束时立即更新dones_tracker
                    # 这确保了在下一次agent.step调用时，新Episode的第一步会正确触发技能重新分配
                    dones_tracker[i] = True
                    
                    n_episodes += 1
                    main_logger.info(f"环境 {i} 完成第 {n_episodes} 个 episode, 奖励: {episode_rewards_tracker[i]:.2f}, 步数: {env_steps[i]}")
                    
                    # 如果启用调试模式，则生成绘图并重置可视化器
                    if args.debug and visualizers is not None:
                        try:
                            main_logger.info(f"[调试模式] 环境 {i} Episode {n_episodes} 结束，正在生成拓扑图...")
                            visualizers[i].episode_num = n_episodes # 更新 episode 编号
                            visualizers[i].generate_plots(prefix='train_debug') # 添加前缀以区分评估图
                            
                            # 为下一个episode重置此环境的可视化器
                            visualizers[i] = VisualizationManager(episode_num=i, log_dir=log_dir, config=config)
                            main_logger.info(f"[调试模式] 环境 {i} 的可视化器已重置。")
                        except Exception as e:
                            main_logger.error(f"[调试模式] 环境 {i} 生成绘图时出错: {e}")
                    
                    # 【关键修复】使用增强的奖励追踪器记录episode完成，传递完整的环境信息
                    # 确保episode结束时的reward_info被正确捕获
                    episode_info = infos[i].copy()  # 复制完整的环境信息
                    if 'global' in infos[i]:
                        episode_info.update(infos[i]['global'])
                    
                    # 在记录前，计算并添加当前episode的覆盖率统计信息
                    current_episode_coverages = [
                        step_data['coverage_ratio'] 
                        for step_data in reward_tracker.step_metric_buffer[i] 
                        if 'coverage_ratio' in step_data
                    ]
                    if current_episode_coverages:
                        mean_cov = np.mean(current_episode_coverages)
                        std_cov = np.std(current_episode_coverages)
                        min_cov = np.min(current_episode_coverages)
                        max_cov = np.max(current_episode_coverages)
                        
                        # 将统计信息添加到info中，以便被log_episode_completion记录
                        if 'reward_info' not in episode_info:
                            episode_info['reward_info'] = {}
                        episode_info['reward_info']['episode_coverage_mean'] = mean_cov
                        episode_info['reward_info']['episode_coverage_std'] = std_cov
                        episode_info['reward_info']['episode_coverage_min'] = min_cov
                        episode_info['reward_info']['episode_coverage_max'] = max_cov
                        
                        # 新增: 将episode表现记录到历史中，用于最差表现优化
                        reward_tracker.episode_performance_history.append({
                            'episode_num': n_episodes,
                            'env_id': i,
                            'avg_coverage': mean_cov
                        })

                    reward_tracker.log_episode_completion(
                        episode_num=n_episodes,
                        env_id=i,
                        total_reward=episode_rewards_tracker[i],
                        episode_length=env_steps[i],
                        info=episode_info  # 传递包含reward_info的完整信息
                    )

                    # 清空该环境的步级缓冲区
                    reward_tracker.step_metric_buffer[i].clear()

                    # 记录到 TensorBoard
                    agent.training_info['episode_rewards'].append(episode_rewards_tracker[i])
                    tb_manager.log_episode_completion(n_episodes, i, episode_rewards_tracker[i], env_steps[i])

                    # 奖励统计
                    episode_rewards.append(episode_rewards_tracker[i])
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
                    
                    # 重置追踪器
                    env_steps[i] = 0
                    episode_rewards_tracker[i] = 0
                    agent.reset_env_state(i)
            
            # 7. 更新状态为下一步做准备。done环境如果collector提供reset_state，则下一步策略使用reset后的状态；
            # rollout存储仍然使用上面的next_states（终止状态）来保持当前transition语义。
            policy_next_states = next_states.copy()
            for i in range(num_envs):
                if dones[i] and 'reset_state' in infos[i]:
                    policy_next_states[i] = infos[i]['reset_state']
            states = policy_next_states
            observations = next_observations
            dones_tracker = dones  # 保存当前步的dones供下一步使用
            total_steps += num_envs
            # 记录单个环境步的等效耗时，使steps_per_second表示总环境步吞吐。
            performance_monitor.record_step_time((time.time() - step_start_time) / max(num_envs, 1))
            if args.memory_monitor_interval <= 1 or rollout_step % args.memory_monitor_interval == 0:
                performance_monitor.record_memory_usage()

            if total_steps >= config.total_timesteps:
                break
        # --- End of NEW Rollout Loop ---

        # 【新增】最差表现优化 (Worst-Case Optimization)
        # 在计算GAE之前，识别并惩罚表现差的episode
        # ----------------------------------------------------------------
        worst_case_episodes = []
        if config.use_worst_case_optimization and reward_tracker.episode_performance_history:
            # 1. 获取所有已完成episode的平均覆盖率
            historical_perf = [perf['avg_coverage'] for perf in reward_tracker.episode_performance_history]
            
            # 2. 计算性能阈值 (例如，后20%)
            threshold = np.percentile(historical_perf, config.worst_case_threshold_percentile)
            
            # 3. 识别当前rollout中完成的、表现低于阈值的episode
            for i in range(num_envs):
                if dones_tracker[i]: # 如果这个环境在上一步结束了一个episode
                    # 从追踪器中找到这个刚结束的episode的性能
                    # 假设log_episode_completion已经将性能记录下来
                    last_perf_entry = next((item for item in reversed(reward_tracker.episode_performance_history) if item['env_id'] == i), None)
                    if last_perf_entry and last_perf_entry['avg_coverage'] < threshold:
                        worst_case_episodes.append(i)
                        main_logger.info(f"[鲁棒性优化] 环境 {i} 的Episode表现 ({last_perf_entry['avg_coverage']:.2f}) 低于阈值 ({threshold:.2f})，将施加惩罚。")

        # --- 在更新前计算GAE和Returns (最终修正版) ---
        main_logger.debug("为低层策略(Discoverer)计算GAE...")

        # 1. 获取最后一步的价值 (Critic的直接输出)
        # 【关键修复】使用正确的下一步技能进行价值引导，修复陈旧技能Bug
        last_values_predicted = np.zeros((num_envs, config.n_agents), dtype=np.float32)
        with torch.no_grad():
            for i in range(num_envs):
                # 【关键修复】确定在 next_state 将使用什么技能
                # 【重要修复】使用实际的env_steps而不是rollout_step来判断技能切换点
                # 这样可以正确处理环境重置导致的env_steps重置情况
                
                # 检查下一步是否是技能切换点 - 使用实际的环境步数
                next_env_step = env_steps[i] + 1
                is_skill_change_point = (next_env_step % config.k == 0)
                
                if is_skill_change_point:
                    # 为 next_state 分配新技能，确保使用正确的 next_states 和 next_observations
                    next_team_skill, next_agent_skills, _ = agent.assign_skills(
                        next_states[i], next_observations[i]
                    )
                    main_logger.debug(f"环境 {i}: 检测到技能切换点 (env_step={env_steps[i]}, next_env_step={next_env_step}), 为 s_{{T+1}} 分配新技能 Z_{{T+1}}={next_team_skill}")
                else:
                    # 使用当前技能
                    next_team_skill = agent.env_team_skills.get(i, 0)
                    if next_team_skill == -1: 
                        next_team_skill = 0
                    main_logger.debug(f"环境 {i}: 继续使用当前技能 Z={next_team_skill} (env_step={env_steps[i]}, next_env_step={next_env_step})")
                
                # 【关键修复】使用正确的、未来的技能来计算自举价值 V(s_{T+1}, Z_{T+1})
                # 此处的 'states' 变量实际上是 rollout 循环结束时的 'next_states'
                normalized_next_state = agent._normalize_states(next_states[i], update=False)
                global_state_tensor = torch.FloatTensor(normalized_next_state).unsqueeze(0).to(agent.device)
                team_skill_tensor = torch.tensor(next_team_skill, device=agent.device).unsqueeze(0)
                
                # 【根本原因修复】从agent获取并传递正确的critic隐藏状态
                critic_hidden_key = f"{i}_critic"
                last_critic_hidden_state = agent.env_hidden_states.get(critic_hidden_key)
                
                # 【正确修复】确保隐藏状态的批量维度与输入的批量维度(1)匹配
                if last_critic_hidden_state is not None:
                    # Critic的隐藏状态在同一环境中对所有智能体都是相同的，因此我们只取第一个
                    if last_critic_hidden_state.shape[0] > 1:
                        last_critic_hidden_state = last_critic_hidden_state[0:1]

                global_value_tensor, _ = agent.skill_discoverer.get_value(
                    global_state_tensor, 
                    team_skill_tensor,
                    critic_hidden_state=last_critic_hidden_state
                )

                if config.use_valuenorm and agent.value_norm_discoverer is not None:
                    global_value_tensor = agent._denormalize_values(
                        global_value_tensor,
                        agent.value_norm_discoverer
                    )
                
                last_values_predicted[i, :] = global_value_tensor.squeeze().item()
                
                # 数值稳定性检查
                last_values_predicted[i, :] = numerical_stabilizer.check_and_fix_tensor(
                    torch.FloatTensor(last_values_predicted[i, :]), name='last_values'
                ).numpy()

        # Rollout数据收集完成，进行更新
        # 修复：使用实际收集的步数，而不是可能不准确的rollout_steps变量
        steps_in_rollout = rollout_step + 1
        main_logger.info(f"Rollout收集完成: 实际步数={steps_in_rollout}, 预期步数={config.rollout_length}")
        try:
            # 执行回调函数 - 在更新前
            for callback in callbacks:
                callback.on_rollout_end()
            
            # 在调用update之前，应用最差情况优化
            if worst_case_episodes:
                main_logger.debug(f"对环境 {worst_case_episodes} 的回报应用惩罚权重...")
                agent.apply_reward_weighting(worst_case_episodes, config.worst_case_penalty_weight)

            # 准备最后的状态和观测数据用于GAE引导价值计算
            last_states_batch = states.copy()
            last_observations_batch = observations.copy()

            update_info = agent.update(
                steps_in_buffer=steps_in_rollout,
                last_values=last_values_predicted,
                dones=dones_tracker,
                last_state=last_states_batch,
                last_observations=last_observations_batch
            )
            update_times += 1
            elapsed = time.time() - start_time

            main_logger.info(f"Rollout更新 {update_times} (收集了 {steps_in_rollout} 步), 总步数 {total_steps}, "
                  f"高层损失 {update_info['coordinator_loss']:.4f}, "
                  f"低层损失 {update_info['discoverer_loss']:.4f}, "
                  f"判别器损失 {update_info['discriminator_loss']:.4f}, "
                  f"CD损失 {update_info.get('cd_loss', 0):.4f}, "
                  f"已用时间 {elapsed:.2f}s")
            
            # 记录训练指标到TensorBoard
            tb_manager.log_training_metrics(total_steps, update_info, args=args)
            
            # 执行回调函数 - 在更新后
            for callback in callbacks:
                callback.on_step()
            
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

        # 【关键修复】更新完成后，立即清空缓冲区，为下一次rollout做准备
        # 这是解决"陈旧数据污染"和"策略退化"问题的关键
        agent.clear_buffers()
        main_logger.debug(f"已清空经验缓冲区，准备下一次rollout (更新 {update_times})")

        # 重置rollout步数计数器
        rollout_steps = 0

        # 加强高层样本的累积情况监控
        if total_steps >= last_check_total_steps + check_interval_steps:
                # 获取当前高层缓冲区大小 (从统一的rollout buffer中计算)
                num_steps_in_buffer = config.rollout_length
                current_high_level_buffer_size = agent.high_level_samples_total
                
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
        
        # 记录性能监控指标
        if hasattr(performance_monitor, 'log_performance'):
            performance_monitor.log_performance()
        
        # 记录数值稳定性统计
        if hasattr(numerical_stabilizer, 'get_statistics'):
            stability_stats = numerical_stabilizer.get_statistics()
            if stability_stats['total_repairs'] > 0:
                main_logger.info(f"数值稳定性统计: {stability_stats}")
        
        # 评估 (基于总步数和上次评估的时间)
        if (not args.disable_eval) and total_steps >= last_eval_step + config.eval_interval:
            if eval_vec_env is None:
                if eval_env_fns is None:
                    raise RuntimeError("评估环境尚未创建，且未提供eval_env_fns用于延迟创建")
                main_logger.info("延迟创建评估 SubprocVecEnv...")
                eval_vec_env = SubprocVecEnv(eval_env_fns, start_method='spawn')
                created_eval_vec_env = True
            main_logger.info(f"即将进行评估，将评估 {config.eval_episodes} 个episodes...")
            main_logger.info(f"当前步数: {total_steps}, 距离上次评估: {total_steps - last_eval_step} 步")
            # 使用 eval_vec_env 进行评估
            eval_reward, eval_std, eval_min, eval_max = evaluate(eval_vec_env, agent, config.eval_episodes, render=args.render, record_video=args.record_video, eval_step=total_steps)
            main_logger.info(f"评估完成 ({config.eval_episodes} 个episodes): 平均奖励 {eval_reward:.2f} ± {eval_std:.2f}, 最大/最小: {eval_max:.2f}/{eval_min:.2f}")

            # 【新增】记录评估结果
            eval_steps_history.append(total_steps)
            eval_mean_rewards_history.append(eval_reward)
            eval_std_rewards_history.append(eval_std)

            # Optuna: 报告进度并支持剪枝
            if trial is not None:
                import optuna
                # 报告当前评估奖励作为中间指标
                trial.report(eval_reward, total_steps)

                # 检查是否应该剪枝（提前终止表现不佳的实验）
                if trial.should_prune():
                    raise optuna.TrialPruned()

            # 保存最佳模型
            if eval_reward > best_reward:
                best_reward = eval_reward
                agent.save_model(args.model_path)
                main_logger.info(f"保存最佳模型，奖励: {best_reward:.2f}")
            
            # 更新上次评估步数
            last_eval_step = total_steps
            
            # 【新增】绘制并保存更新的评估性能曲线
            if eval_steps_history:
                main_logger.info("正在更新评估性能曲线图...")
                plt.figure(figsize=(12, 8))
                
                # 转换为numpy数组方便计算
                eval_steps_history_np = np.array(eval_steps_history)
                eval_mean_rewards_history_np = np.array(eval_mean_rewards_history)
                eval_std_rewards_history_np = np.array(eval_std_rewards_history)
                
                # 绘制平均奖励曲线
                plt.plot(eval_steps_history_np, eval_mean_rewards_history_np, label='Mean Evaluation Reward', color='b', linewidth=2)
                
                # 绘制标准差范围（阴影区域）
                plt.fill_between(eval_steps_history_np, 
                                 eval_mean_rewards_history_np - eval_std_rewards_history_np, 
                                 eval_mean_rewards_history_np + eval_std_rewards_history_np, 
                                 color='b', alpha=0.2, label='Standard Deviation')
                
                plt.title('Evaluation Reward vs. Training Steps', fontsize=16)
                plt.xlabel('Total Training Steps', fontsize=12)
                plt.ylabel('Mean Reward', fontsize=12)
                plt.grid(True, linestyle='--', alpha=0.6)
                plt.legend(fontsize=10)
                plt.tight_layout()
                
                # 保存图像 (覆盖旧文件)
                eval_plot_path = os.path.join(log_dir, 'evaluation_performance_curve.png')
                plt.savefig(eval_plot_path, dpi=300)
                plt.close()
                main_logger.info(f"评估性能曲线图已更新并保存至: {eval_plot_path}")

                # 【新增】保存绘图数据
                try:
                    eval_data_df = pd.DataFrame({
                        'steps': eval_steps_history_np,
                        'mean_reward': eval_mean_rewards_history_np,
                        'std_reward': eval_std_rewards_history_np
                    })
                    eval_data_path = os.path.join(log_dir, 'evaluation_performance_data.csv')
                    eval_data_df.to_csv(eval_data_path, index=False)
                    #main_logger.info(f"评估性能数据已保存至: {eval_data_path}")
                except Exception as e:
                    main_logger.error(f"保存评估性能数据时出错: {e}")

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
        # 转换numpy类型为原生Python类型以确保JSON序列化兼容性
        json_compatible_stats = convert_numpy_types(summary_stats)
        json.dump(json_compatible_stats, f, indent=2)
    main_logger.info(f"最终训练摘要已保存到: {final_summary_path}")

    # 保存最终模型
    final_model_path = os.path.join(model_dir, 'hmasd_sb3_multiproc_paper_config_final.pt') # Update filename
    agent.save_model(final_model_path)
    main_logger.info(f"最终模型已保存到 {final_model_path}")

    # 调用 on_training_end 回调
    for callback in callbacks:
        callback.on_training_end()

    # 为 Optuna 返回最佳评估奖励
    if trial is not None:
        # 将最佳奖励存储在agent对象中，供Optuna使用
        agent.best_eval_reward = best_reward
        main_logger.info(f"为Optuna记录最佳评估奖励: {best_reward:.3f}")

    if created_eval_vec_env and eval_vec_env is not None:
        eval_vec_env.close()
        main_logger.info("延迟创建的评估环境已关闭")

    return agent

# 评估函数
def evaluate(vec_env, agent, n_episodes=10, render=False, record_video=False, eval_step=0):
    """
    评估HMASD代理 (使用 SubprocVecEnv)

    参数:
        vec_env: SubprocVecEnv 实例
        agent: HMASD代理实例
        n_episodes: 评估的episode数量 (总共要评估的episode数量)
        render: 是否实时渲染环境 (只渲染第一个环境)
        record_video: 是否将评估过程录制为视频
        eval_step (int): 当前的训练总步数，用于唯一标识评估图像

    返回:
        mean_reward: 平均奖励
        std_reward: 奖励标准差
        min_reward: 最小奖励
        max_reward: 最大奖励
    """
    import torch  # 添加这行确保 torch 在函数作用域内可用
    
    # 打印评估参数
    num_envs = vec_env.num_envs
    main_logger.info(f"开始评估: 目标完成 {n_episodes} 个episodes，使用 {num_envs} 个并行环境，实时渲染: {render}, 录制视频: {record_video}")
    
    # 切换到评估模式
    agent.eval()
    
    # 【新增】创建评估专用的TensorBoard管理器和奖励追踪器
    eval_log_dir = os.path.join(agent.log_dir, f'evaluation_step_{eval_step}')
    os.makedirs(eval_log_dir, exist_ok=True)
    
    eval_tb_manager = TensorBoardManager(eval_log_dir, agent.config)
    eval_reward_tracker = EnhancedRewardTracker(eval_log_dir, agent.config, n_users=agent.config.n_users)
    
    # 视频录制设置
    video_writers = [None] * num_envs
    if record_video:
        video_dir = os.path.join(eval_log_dir, 'videos')
        os.makedirs(video_dir, exist_ok=True)
        # 获取帧尺寸
        frame = vec_env.env_method('render', indices=[0])[0]
        if frame is not None and frame.shape[0] > 0 and frame.shape[1] > 0:
            height, width, _ = frame.shape
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            for i in range(num_envs):
                video_path = os.path.join(video_dir, f'eval_episode_{i}_step_{eval_step}.mp4')
                video_writers[i] = cv2.VideoWriter(video_path, fourcc, 10.0, (width, height))
                main_logger.info(f"为环境 {i} 初始化视频录制器，保存至: {video_path}")
        else:
            # 【增强日志】打印更详细的错误信息
            frame_shape = frame.shape if frame is not None else "None"
            main_logger.error(f"无法获取有效的渲染帧来初始化录制器 (帧形状: {frame_shape})，视频录制功能已禁用。")
            record_video = False

    # 用于计时的变量
    eval_start_time = time.time()
    step_times = []
    agent_step_times = []
    env_step_times = []
    episode_rewards = []
    episode_lengths = []
    eval_step = getattr(agent, 'global_step', eval_step) # Get current training step if available
    num_envs = vec_env.num_envs

    # 重置所有环境并获取初始状态
    results = vec_env.env_method('reset')
    observations = np.array([res[0] for res in results])
    initial_infos = [res[1] for res in results]
    # Use agent.config.state_dim for default state shape
    states = np.array([info.get('state', np.zeros(agent.config.state_dim)) for info in initial_infos]) # Use agent's state_dim

    # 为每个并行环境创建一个可视化管理器
    visualizers = [VisualizationManager(episode_num=i, log_dir=eval_log_dir, config=agent.config) for i in range(num_envs)]
    
    # 收集一次静态信息
    initial_env_states = [vec_env.env_method('get_current_state', indices=[i])[0] for i in range(num_envs)]
    static_infos = []
    for env_state in initial_env_states:
        static_infos.append({
            'ground_bs_positions': env_state.get('ground_bs_positions'),
            'area_size': env_state.get('area_size')
        })
    
    # 环境状态跟踪
    env_steps = np.zeros(num_envs, dtype=int)
    env_rewards = np.zeros(num_envs)
    active_envs = np.ones(num_envs, dtype=bool) # Track which envs are still running for the current eval round
    completed_episodes = 0
    
    # 【新增】评估期间的覆盖率追踪
    coverage_history = []  # 记录整个评估期间的覆盖率变化
    step_coverage_data = []  # 记录每步的覆盖率数据
    
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
            
            # 使用批量化的agent.step进行评估（与训练保持一致）
            agent_step_start = time.time()
            
            # 准备批量输入（只为活跃环境）
            active_indices = np.where(active_envs)[0]
            if len(active_indices) > 0:
                # 提取活跃环境的状态和观测
                active_states = states[active_indices]
                active_observations = observations[active_indices] 
                active_env_steps = env_steps[active_indices]
                active_dones = np.zeros(len(active_indices), dtype=bool)  # 评估中不使用dones重置
                
                # 批量调用agent.step - 【关键修复】评估时使用确定性模式
                active_actions_batch, active_infos_batch = agent.step(
                    active_states, active_observations, active_env_steps, active_dones, deterministic=True
                )
                
                # 重新组装为完整的actions数组
                actions_array = np.zeros((num_envs,) + vec_env.action_space.shape)
                all_agent_infos_list = [{}] * num_envs  # 初始化为空字典
                
                for idx, env_i in enumerate(active_indices):
                    # 【关键修复】直接使用确定性模式下返回的正确形状的动作
                    # agent.step在确定性模式下已经返回了正确形状的动作，无需reshape
                    actions_array[env_i] = active_actions_batch[idx]
                    all_agent_infos_list[env_i] = active_infos_batch[idx]
                    
                    # 收集技能分布信息
                    all_team_skills.append(active_infos_batch[idx]['team_skill'])
                    all_agent_skills.append(active_infos_batch[idx]['agent_skills'])
            else:
                # 如果没有活跃环境，创建空的actions数组
                actions_array = np.zeros((num_envs,) + vec_env.action_space.shape)
                all_agent_infos_list = [{}] * num_envs
            
            agent_step_end = time.time()
            agent_step_total = agent_step_end - agent_step_start
            agent_step_times.append(agent_step_total)

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
                    
                    # 直接使用环境返回的奖励值进行评估
                    # 在scenario4中，这是网络健康度奖励(shaped_team_reward)或测试模式下的距离惩罚
                    extrinsic_reward = rewards[i]
                    env_rewards[i] += extrinsic_reward
                    
                    # 使用新的可视化管理器记录数据
                    agent_info = all_agent_infos_list[i]
                    # 【关键修复】从嵌套的info结构中正确提取UAV位置
                    # 尝试从 infos_dict 中的任意一个智能体获取共享的 uav_positions
                    uav_positions = np.zeros((agent.config.n_agents, 3))
                    if 'infos_dict' in infos[i] and infos[i]['infos_dict']:
                        # 从第一个可用的智能体信息中获取 uav_positions
                        for agent_key, agent_info_dict in infos[i]['infos_dict'].items():
                            if 'uav_positions' in agent_info_dict:
                                uav_positions = agent_info_dict['uav_positions']
                                break
                    # 如果仍然没有找到，尝试直接从 infos[i] 获取
                    if np.array_equal(uav_positions, np.zeros((agent.config.n_agents, 3))):
                        uav_positions = infos[i].get('uav_positions', np.zeros((agent.config.n_agents, 3)))

                    # 【关键修复】正确提取reward_info从并行环境的嵌套结构
                    # 并行环境返回的infos是一个字典，每个agent都有自己的info
                    # 但reward_info是环境级别的，需要从任意一个agent的info中提取
                    reward_info = {}
                    
                    # 方法1：直接从环境级别的info获取
                    if 'reward_info' in infos[i]:
                        reward_info = infos[i]['reward_info']
                    else:
                        # 方法2：从第一个agent的info中获取（如果环境级别没有）
                        # 在并行环境中，每个agent的info可能包含相同的环境级别信息
                        first_agent_key = f"uav_0"  # 假设第一个agent的key
                        if first_agent_key in infos[i]:
                            agent_info_dict = infos[i][first_agent_key]
                            if 'reward_info' in agent_info_dict:
                                reward_info = agent_info_dict['reward_info']
                    
                    # 【新增】记录每步的覆盖率数据到评估追踪器
                    if reward_info:
                        eval_reward_tracker.log_training_step(
                            step=env_steps[i], 
                            env_id=i, 
                            reward=extrinsic_reward, 
                            info={'reward_info': reward_info}
                        )
                        
                        # 记录到覆盖率历史
                        coverage_ratio = reward_info.get('coverage_ratio', 0)
                        step_coverage_data.append({
                            'step': env_steps[i],
                            'env_id': i,
                            'coverage_ratio': coverage_ratio,
                            'effective_connected_users': reward_info.get('effective_connected_users', 0),
                            'system_throughput_mbps': reward_info.get('system_throughput_mbps', 0),
                            'rt_final_health_score': reward_info.get('rt_final_health_score', 0)
                        })
                    
                    # 调试输出：检查reward_info内容（评估模式）
                    if env_steps[i] % 50 == 0:  # 评估时更频繁地输出调试信息
                        main_logger.debug(f"[评估] 环境 {i} 步骤 {env_steps[i]} - infos结构: {list(infos[i].keys())}")
                        main_logger.debug(f"[评估] 环境 {i} 步骤 {env_steps[i]} reward_info内容: "
                                         f"coverage_ratio={reward_info.get('coverage_ratio', 'N/A')}, "
                                         f"effective_connected_users={reward_info.get('effective_connected_users', 'N/A')}, "
                                         f"system_throughput_mbps={reward_info.get('system_throughput_mbps', 'N/A')}, "
                                         f"rt_final_health_score={reward_info.get('rt_final_health_score', 'N/A')}")
                        
                        # 如果reward_info为空，打印更详细的调试信息
                        if not reward_info:
                            main_logger.warning(f"[评估] Episode结束时未找到reward_info，infos[{i}]键: {list(infos[i].keys())}")

                    visualizers[i].record_step(
                        step_count=env_steps[i],
                        uav_positions=uav_positions,
                        team_skill=agent_info.get('team_skill', -1),
                        agent_skills=agent_info.get('agent_skills', []),
                        reward_info=reward_info,
                        static_info=static_infos[i],
                        # 【修复】从reward_info中稳定地获取连接和路由信息
                        connections=reward_info.get('connections'),
                        routing_paths=reward_info.get('routing_paths')
                    )

                    # 实时渲染或录制视频
                    frame_to_process = None
                    if render and i == 0:
                        try:
                            # render() 返回图像帧用于显示或保存
                            frame_to_process = vec_env.env_method('render', indices=[0])[0]
                            if frame_to_process is not None:
                                # Matplotlib返回RGBA，需要转为BGR给OpenCV显示。
                                frame_bgr = cv2.cvtColor(frame_to_process, cv2.COLOR_RGBA2BGR)
                                try:
                                    cv2.imshow(f'Evaluation Env {i}', frame_bgr)
                                    cv2.waitKey(1)
                                except Exception as e:
                                    main_logger.warning(f"cv2.imshow 失败: {e}")
                        except Exception as e:
                            main_logger.error(f"渲染帧时出错: {e}")

                    if record_video and video_writers[i] is not None:
                        try:
                            # 如果之前没有为实时渲染获取帧，现在获取它
                            if frame_to_process is None:
                                frame_to_process = vec_env.env_method('render', indices=[i])[0]
                            
                            if frame_to_process is not None:
                                frame_bgr = cv2.cvtColor(frame_to_process, cv2.COLOR_RGBA2BGR)
                                video_writers[i].write(frame_bgr)
                        except Exception as e:
                            main_logger.error(f"为环境 {i} 录制视频帧时出错: {e}")

                    # 强制设置环境长度与训练一致
                    if env_steps[i] >= agent.config.episode_length:
                        dones[i] = True
                        main_logger.info(f"评估 Episode (来自环境 {i}) 达到 {agent.config.episode_length} 步上限，强制结束。")

                    # 如果环境完成
                    if dones[i]:
                        if completed_episodes < n_episodes:
                            episode_rewards.append(env_rewards[i])
                            episode_lengths.append(env_steps[i])
                            
                            # 【修复】获取服务用户数和覆盖率信息，使用与步骤中相同的提取逻辑
                            episode_reward_info = {}
                            
                            # 方法1：直接从环境级别的info获取
                            if 'reward_info' in infos[i]:
                                episode_reward_info = infos[i]['reward_info']
                            else:
                                # 方法2：从第一个agent的info中获取
                                first_agent_key = f"uav_0"
                                if first_agent_key in infos[i]:
                                    agent_info_dict = infos[i][first_agent_key]
                                    if 'reward_info' in agent_info_dict:
                                        episode_reward_info = agent_info_dict['reward_info']
                            
                            if episode_reward_info and 'effective_connected_users' in episode_reward_info:
                                # 使用瞬时有效连接用户数，而不是累积值
                                served_users = episode_reward_info['effective_connected_users']
                                # 从配置中获取用户总数
                                n_users = agent.config.n_users if hasattr(agent, 'config') and hasattr(agent.config, 'n_users') else 0
                                coverage_ratio = served_users / n_users if n_users > 0 else 0
                                
                                total_served_users.append(served_users)
                                total_coverage_ratios.append(coverage_ratio)
                                
                                main_logger.info(f"评估 Episode {completed_episodes+1}/{n_episodes} (来自环境 {i}), 奖励: {env_rewards[i]:.2f}, 步数: {env_steps[i]}, 瞬时有效连接用户数: {served_users}/{n_users} ({coverage_ratio:.2%})")
                                
                                # 【新增】记录episode结束时的完整性能指标到评估追踪器
                                eval_reward_tracker.log_episode_completion(
                                    episode_num=completed_episodes + 1,
                                    env_id=i,
                                    total_reward=env_rewards[i],
                                    episode_length=env_steps[i],
                                    info={'reward_info': episode_reward_info}
                                )
                            else:
                                main_logger.info(f"评估 Episode {completed_episodes+1}/{n_episodes} (来自环境 {i}), 奖励: {env_rewards[i]:.2f}, 步数: {env_steps[i]}")
                                main_logger.warning(f"[评估] Episode结束时未找到reward_info，infos[{i}]键: {list(infos[i].keys())}")

                            # 记录到TensorBoard (评估函数中暂时跳过，因为没有传入writer)
                            # 在实际使用中，应该通过参数传入TensorBoard writer
                            pass

                            # 记录高层奖励
                            high_level_rewards.append(env_rewards[i])
                            
                            # episode结束，生成并保存绘图
                            visualizers[i].episode_num = completed_episodes + 1
                            visualizers[i].generate_plots(eval_step=eval_step)
                            
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
    
    # 评估结束后，释放所有视频写入器
    if record_video:
        for i in range(num_envs):
            if video_writers[i] is not None:
                video_writers[i].release()
                main_logger.info(f"环境 {i} 的视频已保存。")
        if render:
            try:
                cv2.destroyAllWindows()
            except Exception as e:
                main_logger.warning(f"cv2.destroyAllWindows 失败: {e}")

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
    
    # 【新增】生成评估期间的覆盖率变化图表
    if step_coverage_data:
        main_logger.info(f"生成评估期间覆盖率变化图表，共收集 {len(step_coverage_data)} 个数据点")
        
        # 创建覆盖率变化图
        try:
            plt.figure(figsize=(15, 10))
            
            # 按环境分组数据
            env_data = {}
            for data_point in step_coverage_data:
                env_id = data_point['env_id']
                if env_id not in env_data:
                    env_data[env_id] = {'steps': [], 'coverage': [], 'users': [], 'throughput': [], 'health': []}
                
                env_data[env_id]['steps'].append(data_point['step'])
                env_data[env_id]['coverage'].append(data_point['coverage_ratio'])
                env_data[env_id]['users'].append(data_point['effective_connected_users'])
                env_data[env_id]['throughput'].append(data_point['system_throughput_mbps'])
                env_data[env_id]['health'].append(data_point['rt_final_health_score'])
            
            # 创建2x2子图
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(f'评估期间性能变化 (训练步数: {eval_step})', fontsize=16, fontweight='bold')
            
            # 子图1：覆盖率变化
            ax1 = axes[0, 0]
            for env_id, data in env_data.items():
                ax1.plot(data['steps'], data['coverage'], label=f'环境 {env_id}', alpha=0.7)
            ax1.set_title('覆盖率变化')
            ax1.set_xlabel('Episode内步数')
            ax1.set_ylabel('覆盖率')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # 子图2：连接用户数变化
            ax2 = axes[0, 1]
            for env_id, data in env_data.items():
                ax2.plot(data['steps'], data['users'], label=f'环境 {env_id}', alpha=0.7)
            ax2.set_title('有效连接用户数变化')
            ax2.set_xlabel('Episode内步数')
            ax2.set_ylabel('连接用户数')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            # 子图3：系统吞吐量变化
            ax3 = axes[1, 0]
            for env_id, data in env_data.items():
                ax3.plot(data['steps'], data['throughput'], label=f'环境 {env_id}', alpha=0.7)
            ax3.set_title('系统吞吐量变化')
            ax3.set_xlabel('Episode内步数')
            ax3.set_ylabel('吞吐量 (Mbps)')
            ax3.grid(True, alpha=0.3)
            ax3.legend()
            
            # 子图4：网络健康度变化
            ax4 = axes[1, 1]
            for env_id, data in env_data.items():
                ax4.plot(data['steps'], data['health'], label=f'环境 {env_id}', alpha=0.7)
            ax4.set_title('网络健康度变化')
            ax4.set_xlabel('Episode内步数')
            ax4.set_ylabel('健康度分数')
            ax4.grid(True, alpha=0.3)
            ax4.legend()
            
            plt.tight_layout()
            
            # 保存图表
            coverage_plot_path = os.path.join(eval_log_dir, f'evaluation_coverage_changes_step_{eval_step}.png')
            plt.savefig(coverage_plot_path, dpi=200, bbox_inches='tight')
            plt.close()
            
            main_logger.info(f"评估期间覆盖率变化图表已保存: {coverage_plot_path}")
            
        except Exception as e:
            main_logger.error(f"生成覆盖率变化图表时出错: {e}")
    
    # 【新增】记录评估统计到TensorBoard
    if step_coverage_data:
        # 计算整个评估期间的平均指标
        all_coverage = [d['coverage_ratio'] for d in step_coverage_data]
        all_users = [d['effective_connected_users'] for d in step_coverage_data]
        all_throughput = [d['system_throughput_mbps'] for d in step_coverage_data]
        all_health = [d['rt_final_health_score'] for d in step_coverage_data]
        
        if all_coverage:
            eval_tb_manager.add_scalar('Evaluation/Average_Coverage_Ratio', np.mean(all_coverage), eval_step)
            eval_tb_manager.add_scalar('Evaluation/Max_Coverage_Ratio', np.max(all_coverage), eval_step)
            eval_tb_manager.add_scalar('Evaluation/Min_Coverage_Ratio', np.min(all_coverage), eval_step)
            eval_tb_manager.add_scalar('Evaluation/Coverage_Std', np.std(all_coverage), eval_step)
        
        if all_users:
            eval_tb_manager.add_scalar('Evaluation/Average_Connected_Users', np.mean(all_users), eval_step)
            eval_tb_manager.add_scalar('Evaluation/Max_Connected_Users', np.max(all_users), eval_step)
        
        if all_throughput:
            eval_tb_manager.add_scalar('Evaluation/Average_System_Throughput', np.mean(all_throughput), eval_step)
            eval_tb_manager.add_scalar('Evaluation/Max_System_Throughput', np.max(all_throughput), eval_step)
        
        if all_health:
            eval_tb_manager.add_scalar('Evaluation/Average_Health_Score', np.mean(all_health), eval_step)
            eval_tb_manager.add_scalar('Evaluation/Max_Health_Score', np.max(all_health), eval_step)
    
    # 记录episode级别的评估统计
    if total_coverage_ratios:
        eval_tb_manager.add_scalar('Evaluation/Episode_Average_Coverage', np.mean(total_coverage_ratios), eval_step)
        eval_tb_manager.add_scalar('Evaluation/Episode_Coverage_Std', np.std(total_coverage_ratios), eval_step)
    
    if total_served_users:
        eval_tb_manager.add_scalar('Evaluation/Episode_Average_Served_Users', np.mean(total_served_users), eval_step)
    
    # 记录基本评估指标
    eval_tb_manager.add_scalar('Evaluation/Mean_Episode_Reward', mean_reward, eval_step)
    eval_tb_manager.add_scalar('Evaluation/Std_Episode_Reward', std_reward, eval_step)
    eval_tb_manager.add_scalar('Evaluation/Mean_Episode_Length', mean_length, eval_step)
    eval_tb_manager.add_scalar('Evaluation/Episodes_Completed', len(episode_rewards), eval_step)
    
    # 关闭评估TensorBoard
    eval_tb_manager.close()
    
    main_logger.info(f"\n评估完成 ({len(episode_rewards)} episodes): 平均奖励 {mean_reward:.2f} ± {std_reward:.2f}, 平均步数: {mean_length:.2f}")
    main_logger.info(f"评估数据已记录到TensorBoard: {eval_log_dir}")
    
    if step_coverage_data:
        final_avg_coverage = np.mean([d['coverage_ratio'] for d in step_coverage_data])
        main_logger.info(f"评估期间平均覆盖率: {final_avg_coverage:.2%}")

    # 切换回训练模式
    agent.train()

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
    
    # 动态导入指定的配置文件
    try:
        import importlib
        config_module = importlib.import_module(args.config)
        Config = getattr(config_module, 'Config')
        main_logger.info(f"成功从 '{args.config}.py' 加载配置")
    except (ImportError, AttributeError) as e:
        main_logger.error(f"错误：无法找到或加载配置文件 '{args.config}.py' 或其中缺少 'Config' 类。请确保文件存在且正确。详细错误: {e}")
        return

    # 使用加载的配置
    config = Config()
    
    # 只设置少量开关参数（其他参数已在config_1.py中定义）
    config.use_opt = args.use_opt
    config.use_reward_annealing = args.use_reward_annealing
    config.use_lr_decay = args.use_lr_decay
    if args.strict_hmasd_alignment is not None:
        config.strict_hmasd_alignment = bool(args.strict_hmasd_alignment)
    
    main_logger.info("配置已从config_1.py加载，运行时开关参数已设置")
    main_logger.info(
        f"OPT模块: {config.use_opt}, 权重退火: {config.use_reward_annealing}, "
        f"学习率衰减: {config.use_lr_decay}, 严格HMASD对齐: {getattr(config, 'strict_hmasd_alignment', True)}"
    )
    
    # 获取计算设备
    device = get_device(args.device)
    
    # 确定并行环境数量，并同步写回config，确保buffer/batch尺寸与实际collector一致。
    requested_backend = args.collector_backend
    base_num_envs = args.num_envs if args.num_envs > 0 else config.num_envs
    if requested_backend == 'auto':
        explicit_sharding = args.num_workers > 0 or args.envs_per_worker > 0
        cpu_count = os.cpu_count() or 1
        args.collector_backend = 'sharded' if explicit_sharding or base_num_envs > cpu_count * 2 else 'subproc'
        main_logger.info(
            f"collector_backend=auto 已解析为 {args.collector_backend} "
            f"(num_envs={base_num_envs}, cpu_count={cpu_count}, explicit_sharding={explicit_sharding})"
        )

    if args.collector_backend == 'sharded':
        if args.num_envs > 0:
            num_envs = int(args.num_envs)
        elif args.num_workers > 0 and args.envs_per_worker > 0:
            num_envs = int(args.num_workers * args.envs_per_worker)
        else:
            num_envs = int(config.num_envs)

        if args.num_workers > 0 and args.envs_per_worker <= 0:
            num_workers = int(args.num_workers)
            envs_per_worker = int(np.ceil(num_envs / num_workers))
        else:
            envs_per_worker = args.envs_per_worker if args.envs_per_worker > 0 else min(8, max(1, num_envs))
            num_workers = args.num_workers if args.num_workers > 0 else max(1, int(np.ceil(num_envs / envs_per_worker)))

        if num_workers * envs_per_worker < num_envs:
            num_workers = int(np.ceil(num_envs / envs_per_worker))
            main_logger.warning(
                f"分片容量小于num_envs，已将num_workers调整为{num_workers}以容纳{num_envs}个环境"
            )
        args.num_workers = num_workers
        args.envs_per_worker = envs_per_worker
    else:
        num_envs = args.num_envs if args.num_envs > 0 else config.num_envs
        args.num_workers = 0
        args.envs_per_worker = 0
    eval_rollout_threads = args.eval_rollout_threads if args.eval_rollout_threads > 0 else config.eval_rollout_threads

    config.num_envs = int(num_envs)
    config.eval_rollout_threads = int(eval_rollout_threads)
    if args.rollout_length > 0:
        config.rollout_length = int(args.rollout_length)
    if args.total_timesteps > 0:
        config.total_timesteps = int(args.total_timesteps)
    if args.eval_interval > 0:
        config.eval_interval = int(args.eval_interval)
    
    main_logger.info(
        f"使用 {num_envs} 个并行训练环境和 {eval_rollout_threads} 个并行评估环境 "
        f"(collector={args.collector_backend}, workers={args.num_workers}, envs_per_worker={args.envs_per_worker}, metrics={args.metrics_mode})"
    )
    
    # 创建环境构造函数列表 (使用修改后的 make_env)
    # 确保基础种子与命令行参数一致
    base_seed = args.seed
    main_logger.info(f"基础种子: {base_seed}")

    train_env_fns = [make_env(
        rank=i,
        seed=base_seed, # 使用命令行传入的种子
        config=config,
        scenario=args.scenario,
        render_mode=None
    ) for i in range(num_envs)]

    eval_env_fns = [make_env(
        rank=i,
        seed=base_seed + num_envs,
        config=config,
        scenario=args.scenario,
        render_mode="rgb_array" if args.render or args.record_video else None
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
    action_dim = getattr(temp_env, 'action_dim', None)
    if action_dim is None:
        action_space = getattr(temp_env, 'action_space', None)
        if hasattr(action_space, 'n'):
            action_dim = action_space.n
        elif hasattr(action_space, 'shape') and action_space.shape:
            action_dim = action_space.shape[-1]
    
    # 更新配置维度（n_agents已在之前设置）
    config.update_env_dims(state_dim, obs_dim)
    if action_dim is not None:
        config.action_dim = int(action_dim)
    
    main_logger.info(f"从环境获取维度信息: state_dim={state_dim}, obs_dim={obs_dim}, action_dim={config.action_dim}")
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

    # 现在按运行模式创建向量化环境。训练模式下评估环境延迟创建。
    train_vec_env = None
    eval_vec_env = None
    if args.mode == 'train':
        if args.collector_backend == 'sharded':
            main_logger.info("创建 ShardedSubprocVecEnv...")
            train_vec_env = ShardedSubprocVecEnv(
                train_env_fns,
                num_workers=args.num_workers,
                envs_per_worker=args.envs_per_worker,
                metrics_mode=args.metrics_mode,
                start_method='spawn'
            )
            main_logger.info("ShardedSubprocVecEnv 已创建。")
        else:
            main_logger.info("创建 SubprocVecEnv...")
            train_vec_env = SubprocVecEnv(train_env_fns, start_method='spawn') # Use spawn for better compatibility
            main_logger.info("SubprocVecEnv 已创建。")
    elif args.mode == 'eval':
        main_logger.info("创建评估 SubprocVecEnv...")
        eval_vec_env = SubprocVecEnv(eval_env_fns, start_method='spawn')
        main_logger.info("评估 SubprocVecEnv 已创建。")

    main_logger.info(f"使用论文中的超参数: n_Z={config.n_Z}, n_z={config.n_z}, k={config.k}, lambda_e={config.lambda_e}")

    if args.mode == 'train':
        # Pass eval_vec_env to the train function
        agent = train(train_vec_env, eval_vec_env, config, args, device, eval_env_fns=eval_env_fns)
    elif args.mode == 'eval':
        # 加载模型
        if not os.path.exists(args.model_path):
            main_logger.error(f"模型文件 {args.model_path} 不存在")
            if eval_vec_env is not None:
                eval_vec_env.close()
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
        evaluate(eval_vec_env, agent, n_episodes=args.eval_episodes, render=args.render, record_video=args.record_video)
    else:
        main_logger.error(f"未知的运行模式: {args.mode}")
    
    # 关闭环境
    if train_vec_env is not None:
        train_vec_env.close()
    if eval_vec_env is not None:
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
    except KeyboardInterrupt:
        print("\n训练被用户中断")
    except Exception as e:
        print(f"\n训练过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 1. 确保关闭日志系统，刷新所有日志
        try:
            shutdown_logging()
            print("日志系统已关闭")
        except Exception as e:
            print(f"关闭日志系统时出错: {e}")
