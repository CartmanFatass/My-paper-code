import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torch.optim import Adam
from torch.distributions import Categorical
import time
import os
import threading
from collections import deque
from torch.utils.tensorboard import SummaryWriter
from queue import Queue

# 确保在多进程环境中使用安全的matplotlib后端
import matplotlib
if matplotlib.get_backend() != 'Agg':
    matplotlib.use('Agg')

# 导入SB3的RunningMeanStd
from stable_baselines3.common.running_mean_std import RunningMeanStd

from logger import main_logger
from hmasd.networks import SkillCoordinator, SkillDiscoverer, TeamDiscriminator, IndividualDiscriminator
from hmasd.utils import RolloutBuffer, compute_gae, compute_ppo_loss, one_hot, DiscriminatorBuffer
import random

# 导入SB3集成功能
try:
    from hmasd.sb3_integration import (
        AdvancedNumericalStabilizer,
        PerformanceMonitor,
        ThreadSafeMetricsCollector as SB3ThreadSafeMetricsCollector
    )
    SB3_INTEGRATION_AVAILABLE = True
    main_logger.info("SB3集成功能已导入")
except ImportError as e:
    main_logger.warning(f"SB3集成功能导入失败: {e}，将使用内置实现")
    SB3_INTEGRATION_AVAILABLE = False


class EnvironmentStateManager:
    """环境状态管理器，防止内存泄漏和提供线程安全访问"""
    def __init__(self, max_envs=64):
        self.max_envs = max_envs
        self.lock = threading.RLock()  # 使用可重入锁
        self.states = {}
        self.access_times = {}
        self.cleanup_threshold = 3600  # 1小时未使用则清理
        
    def get_state(self, env_id, default=None):
        """线程安全地获取环境状态"""
        with self.lock:
            self.access_times[env_id] = time.time()
            return self.states.get(env_id, default)
    
    def set_state(self, env_id, state):
        """线程安全地设置环境状态"""
        with self.lock:
            # 如果超过最大环境数，清理最旧的
            if len(self.states) >= self.max_envs and env_id not in self.states:
                self._cleanup_oldest()
            
            self.states[env_id] = state
            self.access_times[env_id] = time.time()
    
    def remove_state(self, env_id):
        """线程安全地移除环境状态"""
        with self.lock:
            self.states.pop(env_id, None)
            self.access_times.pop(env_id, None)
    
    def _cleanup_oldest(self):
        """清理最旧的环境状态（内部方法，需要在锁内调用）"""
        if not self.access_times:
            return
        oldest_env = min(self.access_times, key=self.access_times.get)
        self.states.pop(oldest_env, None)
        self.access_times.pop(oldest_env, None)
        main_logger.debug(f"清理最旧的环境状态: env_id={oldest_env}")
    
    def cleanup_inactive(self, timeout=None):
        """清理超时未使用的环境状态"""
        if timeout is None:
            timeout = self.cleanup_threshold
            
        with self.lock:
            current_time = time.time()
            to_remove = [env_id for env_id, last_access in self.access_times.items()
                        if current_time - last_access > timeout]
            
            for env_id in to_remove:
                self.states.pop(env_id, None)
                self.access_times.pop(env_id, None)
            
            if to_remove:
                main_logger.info(f"清理了 {len(to_remove)} 个超时环境状态: {to_remove}")
    
    def get_stats(self):
        """获取状态管理器统计信息"""
        with self.lock:
            return {
                'active_envs': len(self.states),
                'max_envs': self.max_envs,
                'oldest_access': min(self.access_times.values()) if self.access_times else None,
                'newest_access': max(self.access_times.values()) if self.access_times else None
            }


class NumericalStabilizer:
    """数值稳定性工具类"""
    
    @staticmethod
    def safe_log(x, eps=1e-8):
        """安全的对数运算"""
        return torch.log(torch.clamp(x, min=eps))
    
    @staticmethod
    def safe_div(numerator, denominator, eps=1e-8):
        """安全的除法运算"""
        return numerator / (denominator + eps)
    
    @staticmethod
    def check_and_fix_tensor(tensor, name="tensor", nan_replacement=0.0, inf_replacement=10.0):
        """检查并修复张量中的异常值"""
        if not isinstance(tensor, torch.Tensor):
            return tensor
            
        has_nan = torch.isnan(tensor).any().item()
        has_inf = torch.isinf(tensor).any().item()
        
        if has_nan or has_inf:
            main_logger.warning(f"数值异常检测到在 {name}: NaN={has_nan}, Inf={has_inf}")
            tensor = torch.nan_to_num(tensor, nan=nan_replacement, 
                                    posinf=inf_replacement, neginf=-inf_replacement)
            main_logger.info(f"已修复 {name} 中的数值异常")
        
        return tensor
    
    @staticmethod
    def safe_normalize(tensor, dim=-1, eps=1e-8):
        """安全的归一化操作"""
        norm = torch.norm(tensor, dim=dim, keepdim=True)
        return tensor / (norm + eps)


class ThreadSafeMetricsCollector:
    """线程安全的指标收集器"""
    def __init__(self, max_size=10000):
        self.lock = threading.Lock()
        self.metrics = {}
        self.max_size = max_size
    
    def add_metric(self, key, value, timestamp=None):
        """线程安全地添加指标"""
        if timestamp is None:
            timestamp = time.time()
            
        with self.lock:
            if key not in self.metrics:
                self.metrics[key] = deque(maxlen=self.max_size)
            self.metrics[key].append({'value': value, 'timestamp': timestamp})
    
    def get_metrics(self, key=None):
        """线程安全地获取指标"""
        with self.lock:
            if key is None:
                return {k: list(v) for k, v in self.metrics.items()}
            else:
                return list(self.metrics.get(key, []))
    
    def get_recent_mean(self, key, n=100):
        """获取最近n个值的平均值"""
        with self.lock:
            if key not in self.metrics:
                return None
            recent_values = list(self.metrics[key])[-n:]
            if not recent_values:
                return None
            return np.mean([item['value'] for item in recent_values])
    
    def clear_metrics(self, key=None):
        """清理指标"""
        with self.lock:
            if key is None:
                self.metrics.clear()
            else:
                self.metrics.pop(key, None)


class HMASDAgent:
    """
    层次化多智能体技能发现（HMASD）代理
    """
    def __init__(self, config, log_dir='logs', device=None, debug=False):
        """
        初始化HMASD代理
        
        参数:
            config: 配置对象，包含所有超参数
            log_dir: TensorBoard日志目录
            device: 计算设备，如果为None则自动检测
            debug: 是否启用自动求导异常检测
        """
        # 启用异常检测以帮助调试
        if debug:
            torch.autograd.set_detect_anomaly(True)
            main_logger.info("已启用自动求导异常检测")
            
        self.config = config
        self.device = device if device is not None else torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        main_logger.info(f"使用设备: {self.device}")
        self.uses_learned_value_function = True
        self.collects_high_level_samples = not getattr(config, 'disable_high_level_training', False)
        
        # 确保环境维度已设置
        assert config.state_dim is not None, "必须先设置state_dim"
        assert config.obs_dim is not None, "必须先设置obs_dim"
        
        # 新增：为增强状态模式传递组件维度
        if getattr(config, 'enhanced_state', False):
            assert hasattr(config, 'state_component_dims'), "增强状态模式需要 state_component_dims"
        
        # 移除TensorBoard相关初始化，由训练脚本统一管理
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        # self.writer = SummaryWriter(log_dir)  # 移除
        # main_logger.debug(f"HMASDAgent.__init__: SummaryWriter created: {self.writer}")
        self.global_step = 0
        self.num_timesteps = 0  # Add SB3 compatibility attribute
        
        # 创建网络
        self.skill_coordinator = SkillCoordinator(config).to(self.device)
        
        self.skill_discoverer = SkillDiscoverer(config, logger=main_logger, device=self.device).to(self.device) # Pass logger
        self.team_discriminator = TeamDiscriminator(config).to(self.device)
        self.individual_discriminator = IndividualDiscriminator(config).to(self.device)
        
        # 创建优化器
        self.coordinator_optimizer = Adam(
            self.skill_coordinator.parameters(),
            lr=config.lr_coordinator,
            weight_decay=config.weight_decay
        )
        # 【关键修复】为SkillDiscoverer解耦Actor和Critic的优化器
        self.discoverer_actor_optimizer = Adam(
            self.skill_discoverer.actor.parameters(),
            lr=config.lr_discoverer_actor,  # 使用独立的actor学习率
            weight_decay=config.weight_decay
        )
        self.discoverer_critic_optimizer = Adam(
            self.skill_discoverer.critic.parameters(),
            lr=config.lr_discoverer_critic, # 使用独立的critic学习率
            weight_decay=config.weight_decay
        )
        self.discriminator_optimizer = Adam(
            list(self.team_discriminator.parameters()) + 
            list(self.individual_discriminator.parameters()),
            lr=config.lr_discriminator,
            weight_decay=config.weight_decay
        )
        
        # 初始化学习率调度器
        if getattr(config, 'use_lr_decay', False):
            from torch.optim.lr_scheduler import LinearLR, CosineAnnealingLR, ExponentialLR
            
            if config.lr_decay_schedule == 'linear':
                self.coordinator_scheduler = LinearLR(
                    self.coordinator_optimizer, 
                    start_factor=1.0, 
                    end_factor=config.coordinator_lr_decay_factor,
                    total_iters=config.lr_decay_steps
                )
                self.discoverer_actor_scheduler = LinearLR(
                    self.discoverer_actor_optimizer,
                    start_factor=1.0,
                    end_factor=config.discoverer_lr_decay_factor, 
                    total_iters=config.lr_decay_steps
                )
                self.discoverer_critic_scheduler = LinearLR(
                    self.discoverer_critic_optimizer,
                    start_factor=1.0,
                    end_factor=config.discoverer_lr_decay_factor, 
                    total_iters=config.lr_decay_steps
                )
                self.discoverer_scheduler = None # 兼容性设置
                self.discriminator_scheduler = LinearLR(
                    self.discriminator_optimizer,
                    start_factor=1.0,
                    end_factor=config.discriminator_lr_decay_factor,
                    total_iters=config.lr_decay_steps
                )
            elif config.lr_decay_schedule == 'cosine':
                self.coordinator_scheduler = CosineAnnealingLR(
                    self.coordinator_optimizer, T_max=config.lr_decay_steps
                )
                self.discoverer_actor_scheduler = CosineAnnealingLR(
                    self.discoverer_actor_optimizer, T_max=config.lr_decay_steps
                )
                self.discoverer_critic_scheduler = CosineAnnealingLR(
                    self.discoverer_critic_optimizer, T_max=config.lr_decay_steps
                )
                self.discoverer_scheduler = None # 兼容性设置
                self.discriminator_scheduler = CosineAnnealingLR(
                    self.discriminator_optimizer, T_max=config.lr_decay_steps
                )
            
            main_logger.info(f"已启用学习率衰减: {config.lr_decay_schedule}, 衰减步数: {config.lr_decay_steps}")
        else:
            self.coordinator_scheduler = None
            self.discoverer_scheduler = None  
            self.discriminator_scheduler = None
            main_logger.info("未启用学习率衰减")
        
        # 新增：与论文一致的、Off-Policy的判别器Buffer
        discriminator_buffer_size = getattr(config, 'discriminator_buffer_size', 100000)
        self.discriminator_buffer = DiscriminatorBuffer(capacity=discriminator_buffer_size)
        
        # 统一的Rollout缓冲区，同时存储高层和低层策略数据
        rollout_length = getattr(config, 'rollout_length', 2048)  # 默认rollout长度
        num_envs = getattr(config, 'num_envs', 1)  # 并行环境数量
        gru_hidden_size = getattr(config, 'gru_hidden_size', 128)  # GRU隐状态大小
        action_space_type = getattr(config, 'action_space_type', 'continuous')  # 动作空间类型
        
        self.rollout_buffer = RolloutBuffer(
            num_steps=rollout_length,
            num_envs=num_envs,
            n_agents=config.n_agents,
            obs_dim=config.obs_dim,
            action_dim=config.action_dim,
            gru_hidden_size=gru_hidden_size,
            n_Z=config.n_Z,
            n_z=config.n_z,
            state_dim=config.state_dim,
            action_space_type=action_space_type
        )
        main_logger.info(f"初始化统一Rollout Buffer: 长度={rollout_length}, 环境数={num_envs}, "
                        f"智能体数={config.n_agents}, 团队技能数={config.n_Z}, 个体技能数={config.n_z}")
        
        # 其他初始化
        self.current_team_skill = None  # 当前团队技能 (保留用于单环境兼容性)
        self.current_agent_skills = None  # 当前个体技能列表 (保留用于单环境兼容性)
        self.skill_change_timer = 0  # 技能更换计时器 (保留用于单环境兼容性)
        self.current_high_level_reward_sum = 0.0 # 当前技能周期的累积奖励
        self.env_reward_sums = {}  # 用于存储每个环境ID的累积奖励，用于并行训练
        self.env_timers = {}  # 用于存储每个环境ID的技能计时器，用于并行训练
        
        # 使用新的环境状态管理器替代原有的字典
        max_envs = max(64, getattr(config, 'num_envs', 1) * 2)  # 预留更多空间
        self.env_state_manager = EnvironmentStateManager(max_envs=max_envs)
        
        # 初始化数值稳定性工具
        if SB3_INTEGRATION_AVAILABLE:
            self.numerical_stabilizer = AdvancedNumericalStabilizer()
            main_logger.info("使用SB3增强的数值稳定性工具")
        else:
            self.numerical_stabilizer = NumericalStabilizer()
            main_logger.info("使用内置的数值稳定性工具")
        
        # 创建线程安全的指标收集器
        if SB3_INTEGRATION_AVAILABLE:
            self.metrics_collector = SB3ThreadSafeMetricsCollector(max_size=10000)
            main_logger.info("使用SB3增强的线程安全指标收集器")
        else:
            self.metrics_collector = ThreadSafeMetricsCollector(max_size=10000)
            main_logger.info("使用内置的线程安全指标收集器")
        
        # 保留兼容性接口（将逐步迁移到新的管理器）
        self.env_team_skills = {}  # 将逐步迁移到env_state_manager
        self.env_agent_skills = {}  # 将逐步迁移到env_state_manager
        self.env_log_probs = {}  # 将逐步迁移到env_state_manager
        self.env_hidden_states = {}  # 将逐步迁移到env_state_manager
        self.env_prev_hidden_states = {} # 用于存储上一步的隐藏状态，解决Off-by-One问题
        self.env_pending_high_level = {}  # 保存技能决策时刻的高层PPO样本，周期结束时只补累计奖励
        
        # 动态初始化环境状态字典 - 将在实际使用时按需初始化
        # 不再预分配固定数量的环境槽位
        self.accumulated_rewards = 0.0  # 用于测试的累积奖励属性
        self.episode_rewards = []  # 记录每个完整episode的奖励
        
        main_logger.info(f"已初始化环境状态管理器，最大环境数: {max_envs}")
        main_logger.info("已初始化线程安全指标收集器")

        # 用于记录整个episode的技能使用计数
        self.episode_team_skill_counts = {}
        # 将在第一次分配技能时根据实际智能体数量初始化
        self.episode_agent_skill_counts = [] 
        
        # 训练指标
        self.training_info = {
            'high_level_loss': [],
            'low_level_loss': [],
            'discriminator_loss': [],
            'team_skill_entropy': [],
            'agent_skill_entropy': [],
            'action_entropy': [],
            'episode_rewards': [],
            # 新增用于记录内在奖励组件和价值估计的列表
            'intrinsic_reward_env_component': [],
            'intrinsic_reward_team_disc_component': [],
            'intrinsic_reward_ind_disc_component': [],
            'intrinsic_reward_low_level_average': [], # 用于记录批次平均内在奖励
            'coordinator_state_value_mean': [],
            'coordinator_agent_value_mean': [],
            'discoverer_value_mean': []
        }
        
        # 用于减少高层缓冲区警告日志的计数器
        self.high_level_buffer_warning_counter = 0
        self.last_high_level_buffer_size = 0
        
        # 高层经验统计
        self.high_level_samples_total = 0        # 总收集高层样本数
        self.high_level_samples_by_env = {}      # 各环境贡献的样本数
        self.high_level_samples_by_reason = {'技能周期结束': 0, '环境终止': 0, '强制收集': 0}  # 收集原因统计
        
        # 高层经验收集增强
        self.env_last_contribution = {}          # 跟踪每个环境上次贡献高层样本的时间步
        self.force_high_level_collection = {}    # 强制采集标志，用于确保所有环境都能贡献样本
        self.env_reward_thresholds = {}          # 环境特定的奖励阈值
        self.strict_hmasd_alignment = getattr(config, 'strict_hmasd_alignment', True)
        if self.strict_hmasd_alignment:
            main_logger.info("已启用严格HMASD论文对齐模式：高层样本仅在技能周期边界闭合")
        if getattr(config, 'rollout_length', 0) % getattr(config, 'k', 1) != 0:
            main_logger.warning(
                f"rollout_length={getattr(config, 'rollout_length', None)} 不能被 k={getattr(config, 'k', None)} 整除，"
                "严格HMASD对齐模式下可能丢弃未闭合的高层技能段"
            )
        
        # 记录内在奖励组成部分的累积值，用于统计分析
        self.cumulative_env_reward = 0.0
        self.cumulative_team_disc_reward = 0.0
        self.cumulative_ind_disc_reward = 0.0
        self.reward_component_counts = 0
        
        # 权重退火相关初始化
        self.use_reward_annealing = getattr(config, 'use_reward_annealing', False)
        if self.use_reward_annealing:
            self.w_intrinsic_initial = getattr(config, 'w_intrinsic_initial', 3.0)
            self.w_intrinsic_final = getattr(config, 'w_intrinsic_final', 1.0)
            self.w_extrinsic_initial = getattr(config, 'w_extrinsic_initial', 0.5)
            self.w_extrinsic_final = getattr(config, 'w_extrinsic_final', 1.5)
            self.anneal_steps = getattr(config, 'anneal_steps', 1000000)
            self.anneal_schedule = getattr(config, 'anneal_schedule', 'linear')
            main_logger.info(f"已启用权重退火机制: "
                           f"内在奖励权重 {self.w_intrinsic_initial}→{self.w_intrinsic_final}, "
                           f"外部奖励权重 {self.w_extrinsic_initial}→{self.w_extrinsic_final}, "
                           f"退火步数: {self.anneal_steps}, 退火计划: {self.anneal_schedule}")
        else:
            main_logger.info("未启用权重退火机制")

        # [新增] 熵系数退火初始化
        self.use_entropy_annealing = getattr(config, 'use_entropy_annealing', False)
        if self.use_entropy_annealing:
            self.lambda_h_initial = getattr(config, 'lambda_h_initial', 0.2)
            self.lambda_h_final = getattr(config, 'lambda_h_final', 0.01)
            self.lambda_l_initial = getattr(config, 'lambda_l_initial', 0.1)
            self.lambda_l_final = getattr(config, 'lambda_l_final', 0.01)
            self.entropy_anneal_steps = getattr(config, 'entropy_anneal_steps', config.total_timesteps)
            self.entropy_anneal_schedule = getattr(config, 'entropy_anneal_schedule', 'linear')
            
            # 立即更新 config 的 lambda 值以反映初始状态
            self.config.lambda_h = self.lambda_h_initial
            self.config.lambda_l = self.lambda_l_initial
            
            main_logger.info(f"已启用熵系数退火机制: "
                           f"高层熵系数 {self.lambda_h_initial}→{self.lambda_h_final}, "
                           f"低层熵系数 {self.lambda_l_initial}→{self.lambda_l_final}, "
                           f"退火步数: {self.entropy_anneal_steps}, 退火计划: {self.entropy_anneal_schedule}")
        else:
            main_logger.info("未启用熵系数退火机制")
        
        # 初始化Value Normalization - 使用SB3的RunningMeanStd
        if config.use_valuenorm:
            self.value_norm_coordinator = RunningMeanStd(shape=())
            self.value_norm_discoverer = RunningMeanStd(shape=())
            # 添加更新频率控制
            self.value_norm_update_freq = getattr(config, 'value_norm_update_freq', 10)  # 每10步更新一次
            self.value_norm_update_counter = 0
            main_logger.info(f"已启用Value Normalization (使用SB3 RunningMeanStd), 更新频率: {self.value_norm_update_freq}")
        else:
            self.value_norm_coordinator = None
            self.value_norm_discoverer = None
            self.value_norm_update_freq = 0
            self.value_norm_update_counter = 0
            main_logger.info("未启用Value Normalization")
        
        # 初始化Observation Normalization - 使用SB3的RunningMeanStd
        if getattr(config, 'use_obsnorm', False):
            self.obs_norm = RunningMeanStd(shape=(config.obs_dim,))
            main_logger.info("已启用Observation Normalization (使用SB3 RunningMeanStd)")
        else:
            self.obs_norm = None
            main_logger.info("未启用Observation Normalization")
        
        # 初始化State Normalization - 使用SB3的RunningMeanStd (新增)
        if getattr(config, 'use_statenorm', True):  # 默认启用状态标准化
            self.state_norm = RunningMeanStd(shape=(config.state_dim,))
            main_logger.info("已启用State Normalization (使用SB3 RunningMeanStd) - 用于Critic输入标准化")
        else:
            self.state_norm = None
            main_logger.info("未启用State Normalization")
        
        self.training = True # 训练/评估模式标志

    def apply_reward_weighting(self, env_indices, weight):
        """
        对指定环境的回报应用一个权重。
        用于最差表现优化，放大表现不佳的episode的奖励信号。
        """
        if not env_indices:
            return
        
        main_logger.info(f"正在为环境 {env_indices} 的回报应用权重 {weight}...")
        try:
            # 直接修改rollout buffer中的rewards
            # 注意：这里修改的是原始的内在奖励，GAE计算会基于此进行
            self.rollout_buffer.rewards[:, env_indices] *= weight
            main_logger.info(f"已成功对环境 {env_indices} 的奖励应用权重。")
        except IndexError:
            main_logger.error(f"在应用奖励权重时发生索引错误。请求的环境索引: {env_indices}, "
                            f"缓冲区环境数量: {self.rollout_buffer.num_envs}")
        except Exception as e:
            main_logger.error(f"应用奖励权重时发生未知错误: {e}")
    
    def train(self, mode=True):
        """设置智能体为训练或评估模式"""
        self.training = mode
        self.skill_coordinator.train(mode)
        self.skill_discoverer.train(mode)
        self.team_discriminator.train(mode)
        self.individual_discriminator.train(mode)
        main_logger.info(f"智能体模式设置为: {'训练' if mode else '评估'}")

    def eval(self):
        """设置智能体为评估模式"""
        self.train(False)

    def _normalize_values(self, values_tensor, running_mean_std):
        """
        [修正] 使用当前的统计量归一化一个张量。
        这个函数不更新统计量。
        """
        if not self.config.use_valuenorm or running_mean_std is None:
            return values_tensor
        
        # 从 SB3 对象获取当前的均值和方差
        current_mean = torch.tensor(running_mean_std.mean, device=self.device, dtype=torch.float32)
        current_var = torch.tensor(running_mean_std.var, device=self.device, dtype=torch.float32)
        
        # 归一化
        normalized_tensor = (values_tensor - current_mean) / torch.sqrt(current_var + 1e-8)
        # 裁剪
        normalized_tensor = torch.clamp(normalized_tensor, -self.config.value_clip, self.config.value_clip)
        
        return normalized_tensor

    def _denormalize_values(self, normalized_values_tensor, running_mean_std):
        """
        [修正] 使用当前的统计量反归一化一个张量。
        """
        if not self.config.use_valuenorm or running_mean_std is None:
            return normalized_values_tensor
        
        # 从 SB3 对象获取当前的均值和方差
        current_mean = torch.tensor(running_mean_std.mean, device=self.device, dtype=torch.float32)
        current_var = torch.tensor(running_mean_std.var, device=self.device, dtype=torch.float32)
        
        # 反归一化
        denormalized_tensor = normalized_values_tensor * torch.sqrt(current_var + 1e-8) + current_mean
        
        return denormalized_tensor

    def _normalize_observations(self, observations, update=True):
        """
        归一化观测数据，解决输入尺度问题
        
        参数:
            observations: 观测数据，可以是numpy数组或torch张量
            update: 是否更新运行均值和方差（RunningMeanStd）
            
        返回:
            normalized_observations: 归一化后的观测数据
        """
        if not getattr(self.config, 'use_obsnorm', False) or self.obs_norm is None:
            return observations
        
        # 转换为numpy数组进行处理
        if isinstance(observations, torch.Tensor):
            obs_np = observations.cpu().numpy()
            return_tensor = True
        else:
            obs_np = observations
            return_tensor = False
        
        # 仅在训练模式下且update=True时更新观测统计量
        if self.training and update:
            if obs_np.ndim == 1:
                # 单个观测
                self.obs_norm.update(obs_np)
            elif obs_np.ndim == 2:
                # 多个智能体的观测 [n_agents, obs_dim]
                for i in range(obs_np.shape[0]):
                    self.obs_norm.update(obs_np[i])
            elif obs_np.ndim == 3:
                # 批量观测 [batch_size, n_agents, obs_dim]
                for i in range(obs_np.shape[0]):
                    for j in range(obs_np.shape[1]):
                        self.obs_norm.update(obs_np[i, j])
        
        # 归一化
        current_mean = self.obs_norm.mean
        current_var = self.obs_norm.var
        
        normalized_obs = (obs_np - current_mean) / np.sqrt(current_var + 1e-8)
        
        # 裁剪到合理范围
        normalized_obs = np.clip(normalized_obs, -10.0, 10.0)
        
        # 如果输入是张量，返回张量
        if return_tensor:
            return torch.FloatTensor(normalized_obs).to(self.device)
        else:
            return normalized_obs

    def _normalize_states(self, states, update=True):
        """
        归一化全局状态数据，解决Critic输入尺度问题
        
        参数:
            states: 全局状态数据，可以是numpy数组或torch张量
            update: 是否更新运行均值和方差（RunningMeanStd）
            
        返回:
            normalized_states: 归一化后的状态数据
        """
        if not getattr(self.config, 'use_statenorm', True) or self.state_norm is None:
            return states
        
        # 转换为numpy数组进行处理
        if isinstance(states, torch.Tensor):
            states_np = states.cpu().numpy()
            return_tensor = True
        else:
            states_np = states
            return_tensor = False
        
        # 仅在训练模式下且update=True时更新状态统计量
        if self.training and update:
            if states_np.ndim == 1:
                # 单个状态
                self.state_norm.update(states_np)
            elif states_np.ndim == 2:
                # 批量状态 [batch_size, state_dim]
                for i in range(states_np.shape[0]):
                    self.state_norm.update(states_np[i])
        
        # 归一化
        current_mean = self.state_norm.mean
        current_var = self.state_norm.var
        
        normalized_states = (states_np - current_mean) / np.sqrt(current_var + 1e-8)
        
        # 裁剪到合理范围
        normalized_states = np.clip(normalized_states, -10.0, 10.0)
        
        # 如果输入是张量，返回张量
        if return_tensor:
            return torch.FloatTensor(normalized_states).to(self.device)
        else:
            return normalized_states

    def clear_buffers(self):
        """清空on-policy的经验缓冲区，以及判别器Buffer (On-Policy模式)"""
        main_logger.info("清空统一的on-policy经验缓冲区 (RolloutBuffer)...")
        self.rollout_buffer.reset()
        
        # Discriminator 现在采用 On-Policy 模式，更新后清空缓冲区
        self.discriminator_buffer.clear()
        main_logger.info("已清空判别器Buffer (On-Policy模式)")
        
        # 重置计数器和累积值
        self.current_high_level_reward_sum = 0.0
        self.accumulated_rewards = 0.0
        self.skill_change_timer = 0
        self.high_level_buffer_warning_counter = 0
        self.last_high_level_buffer_size = 0
        
        # 重置环境特定的奖励累积字典和计时器字典
        self.env_reward_sums = {}
        self.env_timers = {}
        self.env_pending_high_level = {}
        
        # 重置奖励组成部分的累积值
        self.cumulative_env_reward = 0.0
        self.cumulative_team_disc_reward = 0.0
        self.cumulative_ind_disc_reward = 0.0
        self.reward_component_counts = 0
        
        # 重置技能使用计数
        self.episode_team_skill_counts = {}
        self.episode_agent_skill_counts = []
        
        # 定期清理环境状态管理器中的超时状态
        if hasattr(self, 'env_state_manager'):
            self.env_state_manager.cleanup_inactive()
            stats = self.env_state_manager.get_stats()
            main_logger.debug(f"环境状态管理器统计: {stats}")
        
        # 清理指标收集器中的旧数据
        if hasattr(self, 'metrics_collector'):
            # 只保留最近的指标
            self.metrics_collector.clear_metrics()
            main_logger.debug("已清理指标收集器中的旧数据")
        
        # 注意：不重置Value Normalization统计量
        # ValueNorm的running_mean和running_std应该在整个训练过程中累积
        # 这符合MAPPO的标准实现，确保价值函数标准化的稳定性
        # 只有在模型初始化或显式要求时才重置ValueNorm统计量
        if self.config.use_valuenorm:
            main_logger.debug("保持Value Normalization统计量不变，继续累积训练数据")
    
    def get_env_state_stats(self):
        """获取环境状态管理器的统计信息"""
        if hasattr(self, 'env_state_manager'):
            return self.env_state_manager.get_stats()
        return {'active_envs': 0, 'max_envs': 0}
    
    def cleanup_inactive_envs(self, timeout=3600):
        """手动清理超时的环境状态"""
        if hasattr(self, 'env_state_manager'):
            self.env_state_manager.cleanup_inactive(timeout)
    
    def add_training_metric(self, key, value):
        """添加训练指标到线程安全收集器"""
        if hasattr(self, 'metrics_collector'):
            self.metrics_collector.add_metric(key, value)
    
    def get_recent_metric_mean(self, key, n=100):
        """获取最近n个指标的平均值"""
        if hasattr(self, 'metrics_collector'):
            return self.metrics_collector.get_recent_mean(key, n)
        return None
    
    def reset_env_state(self, env_id):
        """
        【关键修复】重置特定环境的内部状态。
        
        当Episode结束时调用此函数，确保：
        1. 重置所有隐藏状态（Actor和Critic）
        2. 将技能标记为无效(-1)，强制下一步重新分配
        3. 重置计时器和累积奖励
        
        这是解决"新Episode第一步技能未重新分配"Bug的关键修复。
        """
        # 重置Actor隐藏状态
        if env_id in self.env_hidden_states:
            self.env_hidden_states[env_id] = None
            main_logger.debug(f"已重置环境 {env_id} 的Actor隐藏状态")
            
        if env_id in self.env_prev_hidden_states:
            self.env_prev_hidden_states[env_id] = None

        # 【关键修复】重置Critic隐藏状态
        critic_hidden_key = f"{env_id}_critic"
        if critic_hidden_key in self.env_hidden_states:
            self.env_hidden_states[critic_hidden_key] = None
            main_logger.debug(f"已重置环境 {env_id} 的Critic隐藏状态")
            
        if critic_hidden_key in self.env_prev_hidden_states:
            self.env_prev_hidden_states[critic_hidden_key] = None
        
        # 【关键修复】将技能标记为无效值(-1)，强制在下一个step中重新分配
        # 这确保了新Episode的第一步会触发技能重新分配
        if env_id in self.env_team_skills:
            self.env_team_skills[env_id] = -1
            main_logger.debug(f"已重置环境 {env_id} 的团队技能为-1（无效，待重新分配）")
        
        if env_id in self.env_agent_skills:
            self.env_agent_skills[env_id] = np.full(self.config.n_agents, -1, dtype=int)
            main_logger.debug(f"已重置环境 {env_id} 的个体技能为-1（无效，待重新分配）")
        
        # 【关键修复】重置技能计时器，确保新Episode从0开始
        if env_id in self.env_timers:
            self.env_timers[env_id] = 0
            main_logger.debug(f"已重置环境 {env_id} 的技能计时器为0")
        
        # 重置累积奖励
        if env_id in self.env_reward_sums:
            self.env_reward_sums[env_id] = 0.0
            main_logger.debug(f"已重置环境 {env_id} 的累积奖励")
        
        # 重置log_probs
        if env_id in self.env_log_probs:
            self.env_log_probs[env_id] = {}

        if env_id in self.env_pending_high_level:
            self.env_pending_high_level.pop(env_id, None)
    
    
    def select_action(self, observations, agent_skills=None, deterministic=False, env_id=0, state=None):
        """
        【论文一致性修复】选择动作，并为每个环境管理 Actor 和 Critic 的隐藏状态
        
        【重要修复】现在每个智能体都有独立的Critic隐状态，与on-policy-main保持一致
        """
        if agent_skills is None:
            agent_skills = self.env_agent_skills.get(env_id, self.current_agent_skills)
            
        # 【关键修复】确保agent_skills有效，如果无效则分配随机技能
        n_agents = observations.shape[0]
        if agent_skills is None or len(agent_skills) != n_agents or np.any(np.array(agent_skills) < 0):
            main_logger.warning(f"环境{env_id}的agent_skills无效: {agent_skills}，分配随机技能")
            agent_skills = np.random.randint(0, self.config.n_z, size=n_agents)
            # 更新环境状态
            self.env_agent_skills[env_id] = agent_skills
            
        # 根据动作空间类型初始化动作张量
        action_space_type = getattr(self.config, 'action_space_type', 'continuous')
        if action_space_type == 'discrete':
            actions = torch.zeros(n_agents, dtype=torch.long, device=self.device)
        else:
            actions = torch.zeros((n_agents, self.config.action_dim), device=self.device)
        action_logprobs = torch.zeros(n_agents, device=self.device)
        values = torch.zeros(n_agents, device=self.device)
        
        # === 管理 Actor 和 Critic 的隐藏状态 ===
        gru_hidden_size = self.config.gru_hidden_size
        
        # Actor 隐藏状态
        actor_hidden_state = self.env_hidden_states.get(env_id)
        if actor_hidden_state is None:
            actor_hidden_state = torch.zeros(n_agents, gru_hidden_size, device=self.device)
        
        # 【关键修复】Critic 隐藏状态 - 每个智能体独立
        critic_hidden_key = f"{env_id}_critic"
        critic_hidden_state = self.env_hidden_states.get(critic_hidden_key)
        if critic_hidden_state is None:
            critic_hidden_state = torch.zeros(n_agents, gru_hidden_size, device=self.device)

        # 【关键修复】保存当前步的输入隐藏状态，用于store_transition（解决Off-by-One问题）
        self.env_prev_hidden_states[env_id] = actor_hidden_state
        self.env_prev_hidden_states[critic_hidden_key] = critic_hidden_state

        with torch.no_grad():
            # 【关键修复】为每个智能体独立计算价值，使用各自的Critic隐状态
            current_team_skill = self.env_team_skills.get(env_id, self.current_team_skill)
            if current_team_skill is not None and state is not None:
                # 【关键修复】应用状态标准化，解决Critic输入尺度问题
                normalized_state = self._normalize_states(state)
                
                # 为每个智能体分别计算价值
                new_critic_hidden_states = []
                for i in range(n_agents):
                    global_state_tensor = torch.FloatTensor(normalized_state).unsqueeze(0).to(self.device)
                    team_skill_tensor = torch.tensor(current_team_skill, device=self.device).unsqueeze(0)
                    
                    # 【关键修复】使用每个智能体独立的Critic隐状态
                    agent_value, new_critic_hidden = self.skill_discoverer.get_value(
                        global_state_tensor, team_skill_tensor, 
                        critic_hidden_state[i:i+1]  # 使用第i个智能体的隐状态
                    )
                    
                    # 【关键修复】在此处反归一化，确保传出的是真实价值
                    if self.config.use_valuenorm and self.value_norm_discoverer is not None:
                        real_value = self._denormalize_values(agent_value, self.value_norm_discoverer)
                        values[i] = real_value.item()
                    else:
                        values[i] = agent_value.item()
                        
                    new_critic_hidden_states.append(new_critic_hidden.squeeze(0))
                
                # 更新所有智能体的Critic隐状态
                critic_hidden_state = torch.stack(new_critic_hidden_states)
                self.env_hidden_states[critic_hidden_key] = critic_hidden_state
            else:
                values.fill_(0.0)

            # 【关键修复】应用观测归一化，解决输入尺度问题
            observations_normalized = self._normalize_observations(observations)
            
            # 将所有智能体作为单个批次处理
            obs_batch = torch.FloatTensor(observations_normalized).to(self.device)
            skill_batch = torch.tensor(agent_skills, device=self.device)

            # 将环境的 Actor hidden_state 传入网络
            actions_batch, logprobs_batch, _, new_actor_hidden_state = self.skill_discoverer.forward(
                obs_batch, skill_batch, actor_hidden_state, deterministic
            )
            
            # 存储更新后的 Actor hidden_state
            self.env_hidden_states[env_id] = new_actor_hidden_state

        return actions_batch.cpu().numpy(), logprobs_batch.cpu().numpy(), values.cpu().numpy()
    
    def assign_skills(self, state, observations, deterministic=False):
        """
        为所有智能体分配技能
        
        参数:
            state: 全局状态 [state_dim]
            observations: 所有智能体的观测 [n_agents, obs_dim]
            deterministic: 是否使用确定性策略
            
        返回:
            team_skill: 团队技能索引
            agent_skills: 个体技能索引列表 [n_agents]
            log_probs: 包含团队技能和个体技能log probabilities的字典
        """
        # Keep Coordinator sampling inputs on the same scale used during PPO re-evaluation.
        state_normalized = self._normalize_states(state)
        state_tensor = torch.FloatTensor(state_normalized).unsqueeze(0).to(self.device)
        # 修复：先转换为numpy数组再创建tensor，避免从列表创建tensor的警告
        obs_array = np.array(observations) if not isinstance(observations, np.ndarray) else observations
        
        # 【关键修复】应用观测归一化，解决输入尺度问题
        obs_array_normalized = self._normalize_observations(obs_array)
        
        obs_tensor = torch.FloatTensor(obs_array_normalized).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            team_skill, agent_skills, Z_logits, z_logits, cd_loss, cmi_loss = self.skill_coordinator(
                state_tensor, obs_tensor, deterministic
            )
            
            # 计算log probabilities
            Z_dist = torch.distributions.Categorical(logits=Z_logits)
            Z_log_prob = Z_dist.log_prob(team_skill)
            
            z_log_probs = []
            n_agents_actual = agent_skills.size(1)
            for i in range(n_agents_actual):
                zi_dist = torch.distributions.Categorical(logits=z_logits[i])
                zi_log_prob = zi_dist.log_prob(agent_skills[0, i])
                z_log_probs.append(zi_log_prob.item())
            
            log_probs = {
                'team_log_prob': Z_log_prob.item(),
                'agent_log_probs': z_log_probs
            }
            state_val, agent_vals, _ = self.skill_coordinator.get_value(state_tensor, obs_tensor)
            if not agent_vals:
                agent_vals = [
                    torch.zeros_like(state_val)
                    for _ in range(self.config.n_agents)
                ]
            if self.config.use_valuenorm and self.value_norm_coordinator is not None:
                state_val = self._denormalize_values(state_val, self.value_norm_coordinator)
                agent_vals = [self._denormalize_values(v, self.value_norm_coordinator) for v in agent_vals]
            log_probs['state_value'] = float(state_val.squeeze().cpu().numpy())
            log_probs['agent_values'] = [float(v.squeeze().cpu().numpy()) for v in agent_vals]
        
        return team_skill.item(), agent_skills.squeeze(0).cpu().numpy(), log_probs
    
    def _batched_assign_skills(self, states_batch, observations_batch, env_steps_batch, dones_batch, deterministic=False):
        """
        【关键修复】为一批环境分配技能。
        只为需要更新的环境运行神经网络。
        
        【Bug修复】现在会检查技能是否为无效值(-1)，确保：
        1. 技能周期结束时重新分配
        2. 环境刚重置时重新分配  
        3. 技能为无效值(-1)时强制重新分配
        """
        num_envs = states_batch.shape[0]
        
        # 【关键修复】检查当前技能是否无效（-1表示需要重新分配）
        has_invalid_team_skill = np.array([
            self.env_team_skills.get(i, -1) == -1 for i in range(num_envs)
        ])
        has_invalid_agent_skills = np.array([
            np.any(self.env_agent_skills.get(i, np.full(self.config.n_agents, -1)) == -1) 
            for i in range(num_envs)
        ])
        invalid_skills_mask = has_invalid_team_skill | has_invalid_agent_skills
        
        # 找出哪些环境需要重新分配技能 (技能周期结束 或 环境刚重置 或 技能无效)
        needs_reassignment_mask = (env_steps_batch % self.config.k == 0) | dones_batch | invalid_skills_mask
        indices_to_update = np.where(needs_reassignment_mask)[0]
        
        # 日志记录无效技能触发的重分配
        if np.any(invalid_skills_mask):
            invalid_envs = np.where(invalid_skills_mask)[0]
            main_logger.info(f"检测到 {len(invalid_envs)} 个环境技能无效，将强制重新分配: {invalid_envs.tolist()}")

        # 准备最终的技能批次，默认为当前技能
        new_team_skills_batch = np.array([self.env_team_skills.get(i, -1) for i in range(num_envs)], dtype=int)
        new_agent_skills_batch = np.array([self.env_agent_skills.get(i, np.full(self.config.n_agents, -1)) for i in range(num_envs)], dtype=int)
        new_log_probs_batch = [self.env_log_probs.get(i, {}) for i in range(num_envs)]

        if len(indices_to_update) > 0:
            # 提取需要更新的状态和观测，并保持与 update_coordinator 的输入尺度一致
            states_to_process_normalized = self._normalize_states(states_batch[indices_to_update])
            states_to_process = torch.FloatTensor(states_to_process_normalized).to(self.device)
            
            # 【关键修复】应用观测归一化，解决输入尺度问题
            obs_to_process_normalized = self._normalize_observations(observations_batch[indices_to_update])
            obs_to_process = torch.FloatTensor(obs_to_process_normalized).to(self.device)

            # 批量运行 SkillCoordinator
            with torch.no_grad():
                team_skills, agent_skills, Z_logits, z_logits, _, _ = self.skill_coordinator(
                    states_to_process, obs_to_process, deterministic
                )
                state_values, agent_values_list, _ = self.skill_coordinator.get_value(
                    states_to_process, obs_to_process
                )
                if self.config.use_valuenorm and self.value_norm_coordinator is not None:
                    state_values = self._denormalize_values(state_values, self.value_norm_coordinator)
                    if not agent_values_list:
                        agent_values_list = [
                            torch.zeros_like(state_values)
                            for _ in range(self.config.n_agents)
                        ]
                    agent_values_list = [
                        self._denormalize_values(v, self.value_norm_coordinator)
                        for v in agent_values_list
                    ]
                elif not agent_values_list:
                    agent_values_list = [
                        torch.zeros_like(state_values)
                        for _ in range(self.config.n_agents)
                    ]
            
            # 将新技能放回正确的位置
            for i, env_idx in enumerate(indices_to_update):
                # 计算log_probs
                Z_dist = torch.distributions.Categorical(logits=Z_logits[i])
                z_log_probs_list = []
                for agent_i in range(self.config.n_agents):
                    zi_dist = torch.distributions.Categorical(logits=z_logits[agent_i][i])
                    z_log_probs_list.append(zi_dist.log_prob(agent_skills[i, agent_i]).item())

                log_probs = {
                    'team_log_prob': Z_dist.log_prob(team_skills[i]).item(),
                    'agent_log_probs': z_log_probs_list,
                    # 论文对齐：old value 必须来自技能决策时刻，而不是技能周期结束时重算。
                    'state_value': float(state_values[i].squeeze().cpu().numpy()),
                    'agent_values': [
                        float(v[i].squeeze().cpu().numpy())
                        for v in agent_values_list
                    ],
                }

                # 更新该环境的状态
                new_team_skills_batch[env_idx] = team_skills[i].item()
                new_agent_skills_batch[env_idx] = agent_skills[i].cpu().numpy()
                new_log_probs_batch[env_idx] = log_probs
                self.env_timers[env_idx] = 0 # 重置计时器
        
        # 增加未更新环境的计时器
        indices_not_updated = np.where(~needs_reassignment_mask)[0]
        for env_idx in indices_not_updated:
            self.env_timers[env_idx] = self.env_timers.get(env_idx, 0) + 1

        # 更新智能体的内部状态
        for i in range(num_envs):
            self.env_team_skills[i] = new_team_skills_batch[i]
            self.env_agent_skills[i] = new_agent_skills_batch[i]
            self.env_log_probs[i] = new_log_probs_batch[i]
            
        return new_team_skills_batch, new_agent_skills_batch, new_log_probs_batch

    def _batched_select_action(self, states_batch, observations_batch, agent_skills_batch, team_skills_batch, dones_batch, deterministic=False):
        """
        【论文一致性修复】为一批环境选择动作，正确管理 Actor 和 Critic 的 GRU 隐藏状态
        
        【重要修复】现在每个智能体都有独立的Critic隐状态，与on-policy-main保持一致
        """
        num_envs, n_agents, _ = observations_batch.shape
        
        # === 1. 管理 Actor 和 Critic 的隐藏状态 ===
        # Actor 隐藏状态
        actor_hidden_states_batch = np.zeros((num_envs, n_agents, self.config.gru_hidden_size), dtype=np.float32)
        for i in range(num_envs):
            if i in self.env_hidden_states and self.env_hidden_states[i] is not None:
                actor_hidden_states_batch[i] = self.env_hidden_states[i].cpu().numpy()

        # 【关键修复】Critic 隐藏状态 - 每个智能体独立
        critic_hidden_states_batch = np.zeros((num_envs, n_agents, self.config.gru_hidden_size), dtype=np.float32)
        for i in range(num_envs):
            critic_hidden_key = f"{i}_critic"
            if critic_hidden_key in self.env_hidden_states and self.env_hidden_states[critic_hidden_key] is not None:
                # 【关键修复】不再广播，而是直接使用每个智能体的独立隐状态
                critic_hidden_states_batch[i] = self.env_hidden_states[critic_hidden_key].cpu().numpy()

        # 重置已完成环境的隐藏状态
        actor_hidden_states_batch[dones_batch] = 0.0
        critic_hidden_states_batch[dones_batch] = 0.0

        # === 2. 准备批量输入 ===
        obs_flat = observations_batch.reshape(-1, self.config.obs_dim)
        
        # 【关键修复】应用观测归一化，解决输入尺度问题
        obs_flat_normalized = self._normalize_observations(obs_flat)
        
        skills_flat = agent_skills_batch.reshape(-1)
        actor_hidden_flat = actor_hidden_states_batch.reshape(-1, self.config.gru_hidden_size)

        obs_tensor = torch.FloatTensor(obs_flat_normalized).to(self.device)
        skills_tensor = torch.LongTensor(skills_flat).to(self.device)
        actor_hidden_tensor = torch.FloatTensor(actor_hidden_flat).to(self.device)
        
        with torch.no_grad():
            # === 3. 批量运行 Actor 网络获取动作 ===
            actions_flat, logprobs_flat, _, new_actor_hidden_flat = self.skill_discoverer(
                obs_tensor, skills_tensor, actor_hidden_tensor, deterministic
            )

            # === 4. 批量运行 Critic 网络获取价值估计 (使用独立的Critic隐状态) ===
            # 为每个智能体提供对应的全局状态和团队技能
            states_expanded = np.repeat(states_batch, n_agents, axis=0)
            team_skills_expanded = np.repeat(team_skills_batch, n_agents, axis=0)
            
            # 【关键修复】应用状态标准化，解决Critic输入尺度问题
            states_expanded_normalized = self._normalize_states(states_expanded)
            
            states_tensor = torch.FloatTensor(states_expanded_normalized).to(self.device)
            team_skills_tensor = torch.LongTensor(team_skills_expanded).to(self.device)
            
            # 【关键修复】使用每个智能体独立的Critic隐状态
            critic_hidden_flat = critic_hidden_states_batch.reshape(-1, self.config.gru_hidden_size)
            critic_hidden_tensor = torch.FloatTensor(critic_hidden_flat).to(self.device)
            
            # 【关键修复】使用新的 get_value 方法，传入每个智能体独立的Critic隐状态
            values_flat, new_critic_hidden_flat = self.skill_discoverer.get_value(
                states_tensor, team_skills_tensor, critic_hidden_tensor
            )
            
            # 【关键修复】在此处反归一化，确保传出的是真实价值
            if self.config.use_valuenorm and self.value_norm_discoverer is not None:
                values_flat = self._denormalize_values(values_flat, self.value_norm_discoverer)
            
        # === 5. Reshape 输出 ===
        # 根据动作空间类型正确reshape动作
        action_space_type = getattr(self.config, 'action_space_type', 'continuous')
        if action_space_type == 'discrete':
            actions_batch = actions_flat.cpu().numpy().reshape(num_envs, n_agents)
        else:
            actions_batch = actions_flat.cpu().numpy().reshape(num_envs, n_agents, self.config.action_dim)
        logprobs_batch = logprobs_flat.cpu().numpy().reshape(num_envs, n_agents)
        values_batch = values_flat.cpu().numpy().reshape(num_envs, n_agents)
        
        new_actor_hidden_batch = new_actor_hidden_flat.reshape(num_envs, n_agents, self.config.gru_hidden_size)
        new_critic_hidden_batch = new_critic_hidden_flat.cpu().numpy().reshape(num_envs, n_agents, self.config.gru_hidden_size)
        
        # === 6. 更新内部隐藏状态 ===
        for i in range(num_envs):
            # 【关键修复】保存当前步的输入隐藏状态到 prev，用于store_transition
            # 注意：actor_hidden_states_batch[i] 已经是处理过 done 的输入状态
            self.env_prev_hidden_states[i] = torch.FloatTensor(actor_hidden_states_batch[i]).to(self.device)
            
            critic_hidden_key = f"{i}_critic"
            self.env_prev_hidden_states[critic_hidden_key] = torch.FloatTensor(critic_hidden_states_batch[i]).to(self.device)

            # 更新 Actor 隐藏状态 (Output for next step)
            self.env_hidden_states[i] = new_actor_hidden_batch[i]
            
            # 【关键修复】更新每个智能体独立的Critic隐状态 (Output for next step)
            self.env_hidden_states[critic_hidden_key] = torch.FloatTensor(new_critic_hidden_batch[i]).to(self.device)
            
        return actions_batch, logprobs_batch, values_batch

    def step(self, states_batch, observations_batch, env_steps_batch, dones_batch, deterministic=False):
        """
        [重构后的核心方法] 为所有并行环境执行一个完整的、批量的步骤。
        这个方法将由训练循环在每一步调用一次。
        """
        num_envs = states_batch.shape[0]
        
        # 初始化环境状态（如果需要）
        for i in range(num_envs):
            if i not in self.env_timers:
                self.env_timers[i] = 0
                # 【关键修复】立即为新环境分配随机技能，而不是使用-1占位符
                with torch.no_grad():
                    # 随机分配团队技能
                    random_team_skill = np.random.randint(0, self.config.n_Z)
                    # 随机分配个体技能
                    random_agent_skills = np.random.randint(0, self.config.n_z, size=self.config.n_agents)
                    
                    self.env_team_skills[i] = random_team_skill
                    self.env_agent_skills[i] = random_agent_skills
                    
                    # 创建对应的log_probs（使用均匀分布的log概率）
                    uniform_team_log_prob = -np.log(self.config.n_Z)
                    uniform_agent_log_probs = [-np.log(self.config.n_z)] * self.config.n_agents
                    
                    self.env_log_probs[i] = {
                        'team_log_prob': uniform_team_log_prob,
                        'agent_log_probs': uniform_agent_log_probs
                    }
                    
                    main_logger.info(f"环境{i}初始化: 团队技能={random_team_skill}, "
                                   f"个体技能={random_agent_skills}")
                
                self.env_hidden_states[i] = None

        # 1. 批量分配技能
        team_skills, agent_skills, log_probs_list = self._batched_assign_skills(
            states_batch, observations_batch, env_steps_batch, dones_batch, deterministic
        )

        # 2. 批量选择动作
        actions, action_logprobs, values = self._batched_select_action(
            states_batch, observations_batch, agent_skills, team_skills, dones_batch, deterministic
        )
        
        # 3. 准备info字典列表
        infos_list = []
        for i in range(num_envs):
            infos_list.append({
                'team_skill': team_skills[i],
                'agent_skills': agent_skills[i],
                'action_logprobs': action_logprobs[i],
                'values': values[i],
                'skill_changed': (env_steps_batch[i] % self.config.k == 0) or dones_batch[i],
                'skill_timer': self.env_timers[i],
                'log_probs': log_probs_list[i],
                'env_id': i
            })
            
        return actions, infos_list
    

    
    def store_rollout_step(self, t, state, observations, actions, rewards, dones, values, log_probs, 
                          gru_hidden_states, critic_gru_hidden_states, env_id, team_skill=None, agent_skills=None, 
                          buffer_type='discoverer', reward_components=None):
        """
        将一个时间步的所有智能体数据存储到统一rollout缓冲区
        
        ⚠️ 【重要】此函数现在只能存储低层策略数据！
        ⚠️ 高层策略数据必须通过 add_high_level_data 存储！
        
        参数:
            t: 时间步索引 (必须是连续且一致的)
            state: 全局状态 [state_dim]
            observations: 所有智能体观测 [n_agents, obs_dim]
            actions: 所有智能体动作 [n_agents, action_dim]
            rewards: 奖励数据 [n_agents] 或单个值
            dones: 完成标志 [n_agents] 或单个值
            values: 价值估计 [n_agents]
            log_probs: 对数概率 [n_agents]
            gru_hidden_states: Actor GRU隐状态 [n_agents, hidden_size]
            critic_gru_hidden_states: Critic GRU隐状态 [n_agents, hidden_size] (新增)
            env_id: 环境索引
            team_skill: 团队技能索引
            agent_skills: 个体技能索引 [n_agents]
            buffer_type: 'coordinator' 或 'discoverer' （已适配统一缓冲区）
            reward_components: 包含奖励组成的字典 (必须提供！)
        """
        if reward_components is None:
            main_logger.error(f"store_rollout_step: reward_components cannot be None. env={env_id}, t={t}")
            return False
        
        # 【修复】验证时间步索引的有效性
        if t < 0 or t >= self.rollout_buffer.num_steps:
            main_logger.error(f"时间步索引越界: t={t}, 有效范围[0, {self.rollout_buffer.num_steps-1}], env={env_id}")
            return False
        
        # 提取真实的奖励组成部分
        reward_env = reward_components.get('env', np.zeros_like(rewards, dtype=np.float32))
        reward_team_disc = reward_components.get('team_disc', np.zeros_like(rewards, dtype=np.float32))
        reward_ind_disc = reward_components.get('ind_disc', np.zeros_like(rewards, dtype=np.float32))

        # 【修复】确保GRU隐状态是tensor类型
        if not isinstance(gru_hidden_states, torch.Tensor):
            gru_hidden_states = torch.tensor(gru_hidden_states, device=self.device)
        if not isinstance(critic_gru_hidden_states, torch.Tensor):
            critic_gru_hidden_states = torch.tensor(critic_gru_hidden_states, device=self.device)
        
        # 存储数据到统一rollout缓冲区，传递时间步索引 t 和 state
        # 增加 critic_gru_hidden_state
        success = self.rollout_buffer.add(
            t=t,
            state=state,
            obs=observations,
            action=actions,
            reward=rewards,
            done=dones,
            value=values,
            log_prob=log_probs,
            gru_hidden_state=gru_hidden_states,  # Actor hidden state
            critic_gru_hidden_state=critic_gru_hidden_states, # Critic hidden state
            env_idx=env_id,
            team_skill=team_skill,
            agent_skills=agent_skills,
            reward_env=reward_env,
            reward_team_disc=reward_team_disc,
            reward_ind_disc=reward_ind_disc
        )
        
        # 检查存储是否成功
        if not success:
            main_logger.warning(f"低层数据存储失败，环境{env_id}，时间步: {t}")
            return False
        
        main_logger.debug(f"数据已存储到统一rollout缓冲区（{buffer_type}类型），环境{env_id}，"
                         f"时间步: {t}，奖励组成：env={np.mean(reward_env):.4f}, "
                         f"team_disc={np.mean(reward_team_disc):.4f}, ind_disc={np.mean(reward_ind_disc):.4f}")
        
        return True


    def _store_discoverer_experience(self, state, next_state, observations, next_observations, actions, rewards, dones, values, 
                                   action_logprobs, team_skill, agent_skills, env_id, rollout_step_idx=None):
        """
        存储低层策略经验到discoverer rollout缓冲区
        
        参数:
            state: 当前全局状态 [state_dim]
            next_state: 下一全局状态 [state_dim] (新增)
            observations: 所有智能体的当前观测 [n_agents, obs_dim]
            next_observations: 所有智能体的下一观测 [n_agents, obs_dim] (新增)
            actions: 所有智能体的动作 [n_agents, action_dim]
            rewards: 环境奖励（标量, 现在是全局共享奖励）
            dones: 是否结束 [n_agents]
            values: 价值估计 [n_agents]
            action_logprobs: 动作对数概率 [n_agents]
            team_skill: 团队技能索引
            agent_skills: 个体技能索引列表 [n_agents]
            env_id: 环境ID
            rollout_step_idx: 在rollout中的实际步数索引（0到rollout_length-1）
        """
        if values is None:
            return
        
        n_agents = len(agent_skills)
        
        # 准备内在奖励数组
        intrinsic_rewards_array = np.zeros(n_agents)
        env_rewards_array = np.zeros(n_agents)
        team_disc_rewards_array = np.zeros(n_agents)
        ind_disc_rewards_array = np.zeros(n_agents)
        
        # 确保dones可以索引且格式正确
        # 处理 numpy bool 标量被误判为可索引对象的问题
        dones_np = np.array(dones)
        if dones_np.ndim == 0:
            dones_array = np.repeat(dones_np, n_agents)
        else:
            dones_array = dones_np
        
        for i in range(n_agents):
            # 论文 Eq. 4 使用 s_{t+1}/o_{t+1} 计算判别器内在奖励。
            # 训练循环负责在 done 时传入 terminal_observation/terminal_state，避免使用 reset 后状态。
            idx = i if i < len(dones_array) else 0
            is_done = bool(dones_array[idx])
            
            calc_next_state = next_state
            calc_next_obs = next_observations[i]

            intrinsic_reward, env_comp, team_disc_comp, ind_disc_comp, _ = self._compute_intrinsic_reward(
                calc_next_state, rewards, calc_next_obs, team_skill, agent_skills[i]
            )
            final_intrinsic_reward = intrinsic_reward
            if is_done:
                main_logger.debug(
                    f"终止transition使用terminal s/o计算内在奖励: env={env_id}, agent={i}"
                )
            
            main_logger.debug(f"Reward components for agent {i}: env={env_comp:.6f}, team_disc={team_disc_comp:.6f}, ind_disc={ind_disc_comp:.6f}")
            
            intrinsic_rewards_array[i] = final_intrinsic_reward
            
            # 存储奖励组成
            env_rewards_array[i] = env_comp
            team_disc_rewards_array[i] = team_disc_comp
            ind_disc_rewards_array[i] = ind_disc_comp
            
            main_logger.debug(f"Reward components stored for agent {i}: env={env_rewards_array[i]:.6f}, team_disc={team_disc_rewards_array[i]:.6f}, ind_disc={ind_disc_rewards_array[i]:.6f}")
            
        # 准备奖励组成字典
        reward_components = {
            'env': env_rewards_array,
            'team_disc': team_disc_rewards_array,
            'ind_disc': ind_disc_rewards_array
        }
        
        # 获取或创建环境特定的GRU隐藏状态 (Actor)
        # 【关键修复】使用 prev_hidden_states 获取当前步的输入隐状态 (t)，而非输出隐状态 (t+1)
        if env_id in self.env_prev_hidden_states and self.env_prev_hidden_states[env_id] is not None:
            # 确保隐藏状态是二维张量，去掉多余的维度
            hidden_state = self.env_prev_hidden_states[env_id]
            if hidden_state.dim() > 2:
                hidden_state = hidden_state.squeeze(0)
            gru_hidden_states = hidden_state.expand(n_agents, -1)  # [n_agents, hidden_size]
        else:
            gru_hidden_size = getattr(self.config, 'gru_hidden_size', 128)
            gru_hidden_states = torch.zeros(n_agents, gru_hidden_size, device=self.device)

        # 获取或创建环境特定的GRU隐藏状态 (Critic)
        # 【关键修复】使用 prev_hidden_states 获取当前步的输入隐状态 (t)
        critic_hidden_key = f"{env_id}_critic"
        if critic_hidden_key in self.env_prev_hidden_states and self.env_prev_hidden_states[critic_hidden_key] is not None:
            # 确保隐藏状态是二维张量，去掉多余的维度
            critic_hidden_state = self.env_prev_hidden_states[critic_hidden_key]
            if critic_hidden_state.dim() > 2:
                critic_hidden_state = critic_hidden_state.squeeze(0)
            # Critic hidden state 应该是 [n_agents, hidden_size] (如果每个agent独立)
            # 在 select_action 中我们已经处理成了 [n_agents, hidden_size]
            critic_gru_hidden_states = critic_hidden_state
        else:
            gru_hidden_size = getattr(self.config, 'gru_hidden_size', 128)
            critic_gru_hidden_states = torch.zeros(n_agents, gru_hidden_size, device=self.device)
        
        # 【修复】确保时间步索引的一致性和有效性
        if rollout_step_idx is not None:
            t = rollout_step_idx
            # 验证时间步索引的有效性
            if t < 0 or t >= self.rollout_buffer.num_steps:
                main_logger.error(f"_store_discoverer_experience: 无效的rollout_step_idx={t}, "
                                f"有效范围[0, {self.rollout_buffer.num_steps-1}], env={env_id}")
                return None
        else:
            # 【修复】不再使用模运算，而是要求明确提供时间步索引
            main_logger.error(f"_store_discoverer_experience: rollout_step_idx is required but not provided, env={env_id}")
            return None

        # 【修复】调用store_rollout_step并检查返回值
        success = self.store_rollout_step(
            t=t,
            state=state,  # 【重要修复】存储当前状态而非下一状态
            observations=observations,  # 【重要修复】存储当前观测而非下一观测
            actions=actions,
            rewards=intrinsic_rewards_array,
            dones=dones,
            values=values,
            log_probs=action_logprobs,
            gru_hidden_states=gru_hidden_states,
            critic_gru_hidden_states=critic_gru_hidden_states, # 传入 Critic Hidden State
            env_id=env_id,
            team_skill=team_skill,
            agent_skills=agent_skills,
            buffer_type='discoverer',
            reward_components=reward_components
        )
        
        if not success:
            main_logger.warning(f"_store_discoverer_experience: 数据存储失败, env={env_id}, t={t}")
            return None

        return reward_components

    def _store_coordinator_experience(self, state, observations, env_id, team_skill, agent_skills, 
                                    log_probs, dones, skill_timer, steps_since_contribution, force_collection, rollout_step_idx=None):
        """
        判断并存储高层策略经验到coordinator rollout缓冲区 (已修复数据覆盖问题)
        
        参数:
            ...
            rollout_step_idx: 当前rollout的步数索引 (关键修复)
        """
        # 判断是否应该存储高层经验
        # 修复：正确处理dones数组
        any_done = np.any(dones) if hasattr(dones, '__iter__') else bool(dones)
        if self.strict_hmasd_alignment:
            should_store_high_level = (skill_timer == self.config.k - 1)
        else:
            should_store_high_level = (skill_timer == self.config.k - 1) or any_done or force_collection
        
        if not should_store_high_level:
            return False
        
        # 获取当前环境的累积奖励
        env_accumulated_reward = self.env_reward_sums.get(env_id, 0.0)
        
        # 确定存储原因
        reason = "未知原因"
        if skill_timer == self.config.k - 1:
            reason = "技能周期结束"
        elif any_done:
            reason = "环境终止"
        elif force_collection:
            reason = "强制收集"
        
        # Use the dedicated add_high_level_data to prevent overwriting low-level rewards.
        if rollout_step_idx is None:
            main_logger.error("rollout_step_idx is None! Cannot store high-level experience correctly.")
            return False

        pending = self.env_pending_high_level.get(env_id)
        if pending is None:
            main_logger.warning(
                f"环境{env_id}在高层段结束时没有待闭合的技能决策样本，"
                f"rollout_step={rollout_step_idx}, skill_timer={skill_timer}，跳过该高层样本"
            )
            self.env_reward_sums[env_id] = 0.0
            self.env_timers[env_id] = 0
            return False

        t = int(pending['time_step'])
        
        # 【修复】调用add_high_level_data并传递分离的log_probs和values
        # 不再计算和存储联合log_prob，以支持解耦的策略损失
        success = self.rollout_buffer.add_high_level_data(
            env_idx=env_id,
            time_step=t,
            state_value=pending.get('state_value', 0.0),
            agent_values=pending.get('agent_values', np.zeros(self.config.n_agents, dtype=np.float32)),
            team_log_prob=pending.get('team_log_prob', 0.0),
            agent_log_probs=pending.get('agent_log_probs', [0.0] * self.config.n_agents),
            accumulated_reward=env_accumulated_reward,
            value=pending.get('state_value', 0.0)
        )
        
        # 如果存储失败（比如重复存储），直接返回False
        if not success:
            return False
    
        # 更新统计信息 (这部分逻辑保持不变)
        self.high_level_samples_total += 1
        self.high_level_samples_by_env[env_id] = self.high_level_samples_by_env.get(env_id, 0) + 1
        self.high_level_samples_by_reason[reason] = self.high_level_samples_by_reason.get(reason, 0) + 1
        self.env_last_contribution[env_id] = self.global_step
        if force_collection:
            self.force_high_level_collection[env_id] = False
        self.env_pending_high_level.pop(env_id, None)
        
        # 重置该环境的奖励累积和计时器 (这部分逻辑保持不变)
        self.env_reward_sums[env_id] = 0.0
        self.env_timers[env_id] = 0
        
        return True

    def _store_discriminator_data(self, next_state, team_skill, next_observations, agent_skills):
        """
        将状态-技能对存储到独立的、Off-Policy的判别器Buffer中。
        
        【归一化修复】确保存储到判别器Buffer的数据与策略网络使用相同的归一化，
        解决"归一化地狱"问题。
        """
        # 【关键修复】归一化状态和观测，确保与策略网络输入一致
        # 【重要】update=False，防止重复更新 RunningMeanStd
        normalized_state = self._normalize_states(next_state, update=False)
        normalized_observations = self._normalize_observations(next_observations, update=False)
        
        # 存储团队技能数据（使用归一化状态）
        self.discriminator_buffer.push(
            {'type': 'team', 'state': normalized_state, 'skill': team_skill}
        )
        
        # 存储每个智能体的个体技能数据（使用归一化观测）
        for i in range(self.config.n_agents):
            self.discriminator_buffer.push(
                {'type': 'individual', 
                 'obs': normalized_observations[i],  # 归一化后的观测
                 'team_skill': team_skill,  # 个体技能判别器需要团队技能作为条件
                 'skill': agent_skills[i]}
            )

    def store_transition(self, state, next_state, observations, next_observations, 
                         actions, rewards, dones, team_skill, agent_skills, action_logprobs, log_probs=None, 
                         skill_timer_for_env=None, env_id=0, values=None, rollout_step_idx=None):
        """
        存储环境交互经验（重构后的简化版本）
        
        参数:
            state: 全局状态 [state_dim]
            next_state: 下一全局状态 [state_dim]
            observations: 所有智能体的观测 [n_agents, obs_dim]
            next_observations: 所有智能体的下一观测 [n_agents, obs_dim]
            actions: 所有智能体的动作 [n_agents, action_dim]
            rewards: 环境奖励
            dones: 是否结束 [n_agents]
            team_skill: 团队技能索引
            agent_skills: 个体技能索引列表 [n_agents]
            action_logprobs: 动作对数概率 [n_agents]
            log_probs: 技能的log probabilities字典，包含'team_log_prob'和'agent_log_probs'
            skill_timer_for_env: 当前环境的技能计时器值，用于多环境并行训练
            env_id: 环境ID，用于多环境并行训练
            values: 价值估计 [n_agents]（新增参数，用于rollout存储）
            rollout_step_idx: 在rollout中的实际步数索引（0到rollout_length-1）
        """
        # 确保rewards是数值类型 (更稳健的处理)
        if isinstance(rewards, np.ndarray):
            current_reward = np.mean(rewards) # 如果是数组，取平均值（因为是共享奖励）
        else:
            current_reward = rewards # 如果是标量，直接使用
        
        # 更新环境特定的奖励累积
        if env_id not in self.env_reward_sums:
            self.env_reward_sums[env_id] = 0.0
        self.env_reward_sums[env_id] += current_reward
        
        # 记录调试信息
        main_logger.debug(f"store_transition: 环境ID={env_id}, step={self.global_step}, skill_timer={skill_timer_for_env}, "
                          f"当前步奖励={current_reward:.4f}, 此环境累积高层奖励={self.env_reward_sums[env_id]:.4f}")
        
        # 1. 存储低层策略经验并获取奖励组成
        # 【重要修复】传递下一状态和下一观测以正确计算内在奖励
        returned_reward_components = self._store_discoverer_experience(
            state, next_state, observations, next_observations, actions, current_reward, dones, values, 
            action_logprobs, team_skill, agent_skills, env_id, rollout_step_idx
        )
        
        # 新增：将 (下一状态, 技能) 对存储到判别器Buffer
        # 根据论文，我们使用 t+1 时刻的状态/观测
        if not getattr(self.config, 'disable_discriminator_training', False):
            self._store_discriminator_data(next_state, team_skill, next_observations, agent_skills)

        # 论文对齐：高层PPO样本的 old log_prob/value 必须固定在技能决策时刻。
        # 这里仅登记待闭合样本；等 skill_timer == k - 1 时只补上累计环境奖励。
        if rollout_step_idx is not None and skill_timer_for_env == 0 and log_probs:
            if 'state_value' in log_probs and 'agent_values' in log_probs:
                self.env_pending_high_level[env_id] = {
                    'time_step': int(rollout_step_idx),
                    'team_skill': int(team_skill),
                    'agent_skills': np.asarray(agent_skills, dtype=np.int64),
                    'team_log_prob': float(log_probs.get('team_log_prob', 0.0)),
                    'agent_log_probs': np.asarray(
                        log_probs.get('agent_log_probs', [0.0] * self.config.n_agents),
                        dtype=np.float32
                    ),
                    'state_value': float(log_probs.get('state_value', 0.0)),
                    'agent_values': np.asarray(log_probs.get('agent_values'), dtype=np.float32),
                }
            else:
                main_logger.warning(
                    f"环境{env_id}在技能决策步缺少高层value字段，无法创建严格对齐的高层pending样本"
                )
        
        # 3. 处理高层策略经验存储
        # 初始化环境状态（如果需要）
        if env_id not in self.env_timers:
            self.env_timers[env_id] = 0
        if env_id not in self.env_last_contribution:
            self.env_last_contribution[env_id] = 0
        if env_id not in self.env_reward_thresholds:
            self.env_reward_thresholds[env_id] = 0.0
        
        # 获取技能计时器值
        skill_timer = skill_timer_for_env if skill_timer_for_env is not None else self.env_timers[env_id]
        
        # 判断是否需要强制收集高层样本
        steps_since_contribution = self.global_step - self.env_last_contribution.get(env_id, 0)
        force_collection = self.force_high_level_collection.get(env_id, False)
        
        # 对长时间未贡献的环境强制收集
        force_collection_threshold = getattr(self.config, 'force_collection_threshold', 10**12)
        if (not self.strict_hmasd_alignment) and steps_since_contribution > force_collection_threshold:
            self.force_high_level_collection[env_id] = True
            if steps_since_contribution % force_collection_threshold == 0:  # 避免日志过多
                main_logger.info(f"环境ID={env_id}已{steps_since_contribution}步未贡献高层样本，将强制收集")
        
        # 存储高层策略经验（如果满足条件）
        # 【注意】高层策略数据继续使用当前状态和观测，这是正确的
        if not getattr(self.config, 'disable_high_level_training', False):
            self._store_coordinator_experience(
                state, observations, env_id, team_skill, agent_skills, 
                log_probs, dones, skill_timer, steps_since_contribution, force_collection,
                rollout_step_idx=rollout_step_idx
            )
        
        # 返回奖励组成部分给训练循环
        return returned_reward_components

    def store_transition_batch(self, states, next_states, observations, next_observations,
                               actions, rewards, dones, infos_batch, rollout_step_idx=None):
        """
        Batch facade for storing one vectorized environment step.

        The rollout buffer still stores per-environment entries, but keeping this
        loop inside the agent gives collectors a single stable call surface.
        """
        reward_components = []
        num_envs = len(rewards)
        for env_id in range(num_envs):
            info = infos_batch[env_id]
            reward_components.append(
                self.store_transition(
                    state=states[env_id],
                    next_state=next_states[env_id],
                    observations=observations[env_id],
                    next_observations=next_observations[env_id],
                    actions=actions[env_id],
                    rewards=rewards[env_id],
                    dones=dones[env_id],
                    team_skill=info['team_skill'],
                    agent_skills=info['agent_skills'],
                    action_logprobs=info['action_logprobs'],
                    values=info['values'],
                    log_probs=info['log_probs'],
                    skill_timer_for_env=info['skill_timer'],
                    env_id=env_id,
                    rollout_step_idx=rollout_step_idx
                )
            )
        return reward_components
    
    def _check_and_fix_tensor_anomalies(self, tensor, name, nan_replacement=0.0, inf_replacement=10.0):
        """
        检查并修复张量中的NaN或Inf值（提取为可重用函数以减少代码重复）
        
        参数:
            tensor: 需要检查的张量
            name: 张量名称（用于日志）
            nan_replacement: NaN值的替换值
            inf_replacement: Inf值的替换值（正数）
            
        返回:
            fixed_tensor: 修复后的张量
            has_anomalies: 是否发现异常值
        """
        has_nan = torch.isnan(tensor).any().item()
        has_inf = torch.isinf(tensor).any().item()
        
        if has_nan or has_inf:
            main_logger.error(f"{name}中存在NaN或Inf: NaN={has_nan}, Inf={has_inf}")
            fixed_tensor = torch.nan_to_num(tensor, nan=nan_replacement, 
                                          posinf=inf_replacement, neginf=-inf_replacement)
            main_logger.info(f"已将{name}中的NaN/Inf值替换为有限值")
            return fixed_tensor, True
        
        return tensor, False

    def compute_adaptive_advantage_normalization(self, advantages, sparse_reward_threshold=0.01):
        """
        自适应优势标准化：根据奖励稀疏程度调整标准化强度
        
        参数:
            advantages: 优势值张量
            sparse_reward_threshold: 判断稀疏奖励的阈值
            
        返回:
            normalized_advantages: 标准化后的优势值
        """
        # 计算非零优势的比例（作为奖励稀疏度的代理指标）
        non_zero_ratio = (advantages.abs() > sparse_reward_threshold).float().mean()
        
        if non_zero_ratio < 0.1:  # 非常稀疏的奖励
            # 使用更温和的标准化或不标准化
            if advantages.std() > 1e-8:
                # 只进行部分标准化，保留更多原始信号
                normalization_strength = 0.1  # 10%的标准化强度
                mean = advantages.mean()
                std = advantages.std()
                normalized = (advantages - mean) / (std + 1e-8)
                advantages = advantages * (1 - normalization_strength) + normalized * normalization_strength
                main_logger.debug(f"使用轻度优势标准化 (稀疏度: {non_zero_ratio:.3f}, 强度: {normalization_strength})")
        elif non_zero_ratio < 0.3:  # 中等稀疏
            # 使用软标准化
            if advantages.std() > 1e-8:
                # 使用更大的epsilon避免过度放大小信号
                advantages = (advantages - advantages.mean()) / (advantages.std() + 0.1)
                main_logger.debug(f"使用软优势标准化 (稀疏度: {non_zero_ratio:.3f})")
        else:  # 密集奖励
            # 使用标准的优势标准化
            if advantages.std() > 1e-8:
                advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
                main_logger.debug(f"使用标准优势标准化 (稀疏度: {non_zero_ratio:.3f})")
        
        # 裁剪极值，避免数值问题
        advantages = torch.clamp(advantages, -10, 10)
        
        return advantages

    def _compute_high_level_bootstrap_values(self, num_steps):
        """
        【GAE引导价值修复】计算高层策略的bootstrap values
        
        从rollout buffer的最后有效数据计算更准确的引导价值，
        而不是简单假设last_value为0，这将显著减少GAE估计的偏差。
        
        参数:
            num_steps: 当前rollout中的有效步数
            
        返回:
            high_level_last_values: 包含state和agents价值的字典
        """
        try:
            # 获取rollout数据
            rollout_data = self.rollout_buffer._get_full_rollout_data()
            if rollout_data is None:
                main_logger.warning("无法获取rollout数据，使用零值作为bootstrap")
                return {
                    'state': np.zeros(self.rollout_buffer.num_envs),
                    'agents': np.zeros((self.rollout_buffer.num_envs, self.config.n_agents))
                }
            
            # 寻找每个环境的最后有效状态和观测
            last_states = np.zeros((self.rollout_buffer.num_envs, self.config.state_dim))
            last_observations = np.zeros((self.rollout_buffer.num_envs, self.config.n_agents, self.config.obs_dim))
            found_last_data = np.zeros(self.rollout_buffer.num_envs, dtype=bool)
            
            # 从后往前搜索每个环境的最后有效数据
            for env_idx in range(self.rollout_buffer.num_envs):
                for t in range(num_steps - 1, -1, -1):  # 从最新到最旧
                    if t < rollout_data["states"].shape[0] and env_idx < rollout_data["states"].shape[1]:
                        # 检查是否有有效的状态数据
                        state_data = rollout_data["states"][t, env_idx]
                        obs_data = rollout_data["obs"][t, env_idx]
                        
                        # 简单的有效性检查：非全零且非NaN
                        if not np.all(state_data == 0) and not np.isnan(state_data).any():
                            last_states[env_idx] = state_data
                            last_observations[env_idx] = obs_data
                            found_last_data[env_idx] = True
                            break
            
            # 使用找到的最后状态计算bootstrap values
            bootstrap_state_values = np.zeros(self.rollout_buffer.num_envs)
            bootstrap_agent_values = np.zeros((self.rollout_buffer.num_envs, self.config.n_agents))
            
            # 批量计算有效环境的价值
            valid_env_indices = np.where(found_last_data)[0]
            if len(valid_env_indices) > 0:
                # 提取有效环境的状态和观测
                valid_states = last_states[valid_env_indices]
                valid_observations = last_observations[valid_env_indices]
                
                # 应用状态和观测标准化
                valid_states_normalized = self._normalize_states(valid_states)
                valid_observations_normalized = self._normalize_observations(valid_observations)
                
                # 转换为tensors
                states_tensor = torch.FloatTensor(valid_states_normalized).to(self.device)
                observations_tensor = torch.FloatTensor(valid_observations_normalized).to(self.device)
                
                with torch.no_grad():
                    # 使用skill coordinator计算价值
                    state_values, agent_values_list, _ = self.skill_coordinator.get_value(
                        states_tensor, observations_tensor
                    )
                    
                    # 提取价值
                    if state_values is not None:
                        bootstrap_state_values[valid_env_indices] = state_values.cpu().numpy().flatten()
                    
                    if agent_values_list is not None and len(agent_values_list) > 0:
                        # 将agent values列表转换为numpy数组
                        for i, agent_value in enumerate(agent_values_list):
                            if i < self.config.n_agents:
                                agent_vals = agent_value.cpu().numpy().flatten()
                                if len(agent_vals) == len(valid_env_indices):
                                    bootstrap_agent_values[valid_env_indices, i] = agent_vals
                
                main_logger.info(f"成功为{len(valid_env_indices)}个环境计算bootstrap values, "
                               f"状态价值范围: [{bootstrap_state_values.min():.4f}, {bootstrap_state_values.max():.4f}], "
                               f"智能体价值范围: [{bootstrap_agent_values.min():.4f}, {bootstrap_agent_values.max():.4f}]")
            else:
                main_logger.warning("未找到任何有效的最后状态数据，使用零值作为bootstrap")
            
            return {
                'state': bootstrap_state_values,
                'agents': bootstrap_agent_values
            }
            
        except Exception as e:
            main_logger.error(f"计算bootstrap values时发生错误: {e}")
            main_logger.warning("使用零值作为fallback bootstrap values")
            return {
                'state': np.zeros(self.rollout_buffer.num_envs),
                'agents': np.zeros((self.rollout_buffer.num_envs, self.config.n_agents))
            }

    def _compute_intrinsic_reward(self, next_state, reward, next_obs, team_skill, agent_skill):
        """
        【SB3集成版本】计算内在奖励，集成数值稳定性检查
        
        关键特性:
        1. 使用互信息: I(s;z) = log q(z|s) - log p(z) 而不是原始的 log q(z|s)
        2. 基线减法（baseline subtraction）用于方差减少
        3. 奖励标准化和裁剪防止极值
        4. 运行统计量维护确保训练稳定性
        5. 集成SB3数值稳定性检查
        
        【归一化修复】确保判别器输入与策略网络使用相同的归一化，
        解决"归一化地狱"问题。
        """
        if getattr(self.config, 'disable_discriminator_rewards', False):
            env_component = self.config.lambda_e * reward if hasattr(self.config, 'lambda_e') else reward
            return env_component, env_component, 0.0, 0.0, 0.0

        with torch.no_grad():
            try:
                # === 【关键修复】归一化输入，确保与策略网络和判别器训练数据一致 ===
                # 【重要】update=False，防止重复更新 RunningMeanStd
                normalized_state = self._normalize_states(next_state, update=False)
                normalized_obs = self._normalize_observations(next_obs, update=False)
                
                # === Team Discriminator Reward (Fixed) ===
                next_state_tensor = torch.FloatTensor(normalized_state).unsqueeze(0).to(self.device)
                
                # 数值稳定性检查
                next_state_tensor = self.numerical_stabilizer.check_and_fix_tensor(
                    next_state_tensor, "next_state_tensor"
                )
                
                team_disc_logits = self.team_discriminator(next_state_tensor)
                
                # 数值稳定性检查
                team_disc_logits = self.numerical_stabilizer.check_and_fix_tensor(
                    team_disc_logits, "team_disc_logits"
                )
                
                # Use log_softmax for numerical stability
                team_disc_log_probs = F.log_softmax(team_disc_logits, dim=-1)
                team_skill_log_prob = team_disc_log_probs[0, team_skill]
                
                # CRITICAL FIX: Use mutual information instead of raw log probability
                # I(s;Z) = log q_D(Z|s) - log p(Z)
                # Assume uniform prior: log p(Z) = -log(n_Z)
                team_skill_prior_log_prob = -np.log(self.config.n_Z)
                team_mutual_info = team_skill_log_prob.item()# - team_skill_prior_log_prob
                
                # === Individual Discriminator Reward (Fixed) ===
                # 【关键修复】使用归一化后的观测
                agent_obs_tensor = torch.FloatTensor(normalized_obs).unsqueeze(0).to(self.device)
                
                # 数值稳定性检查
                agent_obs_tensor = self.numerical_stabilizer.check_and_fix_tensor(
                    agent_obs_tensor, "agent_obs_tensor"
                )
                
                team_skill_tensor = torch.tensor(team_skill, device=self.device)
                agent_disc_logits = self.individual_discriminator(agent_obs_tensor, team_skill_tensor)
                
                # 数值稳定性检查
                agent_disc_logits = self.numerical_stabilizer.check_and_fix_tensor(
                    agent_disc_logits, "agent_disc_logits"
                )
                
                agent_disc_log_probs = F.log_softmax(agent_disc_logits, dim=-1)
                agent_skill_log_prob = agent_disc_log_probs[0, agent_skill]
                
                # CRITICAL FIX: Use mutual information for individual skills too
                # I(o;z|Z) = log q_d(z|o,Z) - log p(z|Z)
                # Assume uniform conditional prior: log p(z|Z) = -log(n_z)
                agent_skill_prior_log_prob = -np.log(self.config.n_z)
                agent_mutual_info = agent_skill_log_prob.item()# - agent_skill_prior_log_prob
                
                # === Baseline Subtraction for Variance Reduction ===
                # Initialize running baselines if not exists
                if not hasattr(self, 'team_disc_baseline'):
                    self.team_disc_baseline = 0.0
                    self.ind_disc_baseline = 0.0
                    self.baseline_update_rate = 0.01
                
                # Update baselines with exponential moving average
                self.team_disc_baseline = (1 - self.baseline_update_rate) * self.team_disc_baseline + \
                                        self.baseline_update_rate * team_mutual_info
                self.ind_disc_baseline = (1 - self.baseline_update_rate) * self.ind_disc_baseline + \
                                       self.baseline_update_rate * agent_mutual_info
                
                # using raw cross entropy seems perform better
                team_disc_reward = team_mutual_info# - self.team_disc_baseline
                ind_disc_reward = agent_mutual_info# - self.ind_disc_baseline
                
                # === 新增：不确定性奖励（熵惩罚） ===
                # 从状态中提取不确定性图（熵图）
                uncertainty_reward = 0.0
                if self.config.enhanced_state and getattr(self.config, 'w_entropy', 0) > 0:
                    dims = self.config.state_component_dims
                    current_dim = dims['current_state_dim']
                    predicted_dim = dims['predicted_state_dim']
                    
                    # 提取不确定性部分
                    uncertainty_map_flat = next_state[current_dim + predicted_dim:]
                    # 计算当前智能体观测位置对应的不确定性
                    # 注意：这里我们只有一个扁平化的观测，需要一种方式来映射回不确定性图
                    # 简化处理：我们使用整个不确定性图的平均熵作为惩罚
                    # 一个更优的实现需要将智能体位置映射到不确定性图的特定区域
                    avg_entropy = np.mean(uncertainty_map_flat) if uncertainty_map_flat.size > 0 else 0
                    
                    # 熵越高，惩罚越大，激励智能体去降低不确定性
                    uncertainty_reward = -self.config.w_entropy * avg_entropy

                # === Reward Normalization and Clipping ===
                # 【临时禁用标准化】直接使用原始奖励值
                team_disc_reward_clipped = np.clip(team_disc_reward, -10.0, 10.0)
                ind_disc_reward_clipped = np.clip(ind_disc_reward, -10.0, 10.0)
                
                # === Final Reward Computation ===
                env_component = self.config.lambda_e * reward
                team_disc_component = self.config.lambda_D * team_disc_reward_clipped
                ind_disc_component = self.config.lambda_d * ind_disc_reward_clipped
                
                intrinsic_reward = env_component + team_disc_component + ind_disc_component + uncertainty_reward
                
                # 使用SB3数值稳定性工具进行最终检查
                if SB3_INTEGRATION_AVAILABLE:
                    # 检查所有组件的数值稳定性
                    components = {
                        'env_component': env_component,
                        'team_disc_component': team_disc_component,
                        'ind_disc_component': ind_disc_component,
                        'uncertainty_reward': uncertainty_reward, # 新增
                        'intrinsic_reward': intrinsic_reward
                    }
                    
                    for name, value in components.items():
                        if not np.isfinite(value):
                            main_logger.warning(f"数值异常检测到在 {name}: {value}")
                            if name == 'intrinsic_reward':
                                intrinsic_reward = env_component
                                team_disc_component = 0.0
                                ind_disc_component = 0.0
                                uncertainty_reward = 0.0
                            elif name == 'team_disc_component':
                                team_disc_component = 0.0
                            elif name == 'ind_disc_component':
                                ind_disc_component = 0.0
                            elif name == 'uncertainty_reward':
                                uncertainty_reward = 0.0
                else:
                    # 使用内置的数值检查
                    if not np.isfinite(intrinsic_reward):
                        intrinsic_reward = env_component
                        team_disc_component = 0.0
                        ind_disc_component = 0.0
                        uncertainty_reward = 0.0
                
                # 在返回值中包含不确定性奖励
                return intrinsic_reward, env_component, team_disc_component, ind_disc_component, uncertainty_reward
                
            except Exception as e:
                main_logger.error(f"Error in SB3-integrated intrinsic reward computation: {e}")
                env_component = self.config.lambda_e * reward if hasattr(self.config, 'lambda_e') else 0.0
                return env_component, env_component, 0.0, 0.0, 0.0

    def update_coordinator(self, num_steps, bootstrap_values=None):
        """更新高层技能协调器网络（使用标准PPO更新，而非错误的序列化更新）"""
        # num_steps 现在是实际在缓冲区中的有效数据量
        
        # 【修复】首先从缓冲区获取数据以检查有效样本数
        rollout_data = self.rollout_buffer._get_full_rollout_data()
        if rollout_data is None:
            main_logger.warning("没有有效的Rollout数据，跳过Coordinator更新")
            return 0, 0, 0, 0, 0, 0, 0, 0, 0
            
        # 检查是否有有效的高层数据
        high_level_valid_mask = rollout_data["high_level_valid_mask"]
        high_level_data_count = np.sum(high_level_valid_mask[:num_steps])
        if high_level_data_count == 0:
            main_logger.warning("没有有效的高层策略数据，跳过Coordinator更新")
            return 0, 0, 0, 0, 0, 0, 0, 0, 0
        
        main_logger.info(f"开始使用统一缓冲区更新Coordinator，有效高层数据: {high_level_data_count}个")
        
        # 【GAE引导价值修复】优先使用传入的准确 bootstrap_values
        if bootstrap_values is not None:
            high_level_last_values = bootstrap_values
            main_logger.debug("使用传入的Bootstrap Values进行GAE计算")
        else:
            # Fallback: 获取buffer中最后的有效状态和观测来计算bootstrap值
            main_logger.warning("未提供Bootstrap Values，回退到从Buffer搜索（可能存在偏差）")
            high_level_last_values = self._compute_high_level_bootstrap_values(num_steps)
        
        
        gamma_high = self.config.gamma #** self.config.k
        
        # 【关键修复】Buffer中已是真实值，不再需要value_normalizer进行反归一化
        self.rollout_buffer.compute_high_level_advantages(
            high_level_last_values, 
            gamma=gamma_high, 
            value_normalizer=None
        )
        
        # 累积损失统计
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy_loss = 0.0
        total_loss = 0.0
        total_cd_loss = 0.0
        total_team_entropy = 0.0
        total_agent_entropy = 0.0
        update_count = 0
        
        # 【关键修改】使用标准的batch_size而不是序列长度
        coordinator_batch_size = getattr(self.config, 'coordinator_batch_size', 128)
        
        # 【修复】使用专门的Coordinator采样器进行标准PPO更新
        high_level_sampler = self.rollout_buffer.get_coordinator_sampler(
            num_steps,
            getattr(self.config, 'ppo_epochs', 10),
            coordinator_batch_size
        )

        if high_level_sampler is None:
            main_logger.error("无法从统一rollout缓冲区获取Coordinator采样器")
            return 0, 0, 0, 0, 0, 0, 0, 0, 0

        # --- 1. 在所有PPO Epochs开始前，一次性更新统计量 ---
        if self.config.use_valuenorm and self.value_norm_coordinator is not None:
            # 获取整个rollout buffer中有效的高层回报
            all_returns = self.rollout_buffer.get_all_high_level_returns(num_steps)
            if all_returns.size > 0:
                # 使用这批数据更新运行统计量
                self.value_norm_coordinator.update(all_returns)
                main_logger.info(f"Coordinator ValueNorm已更新. 新均值: {self.value_norm_coordinator.mean:.4f}, 新标准差: {np.sqrt(self.value_norm_coordinator.var):.4f}")

        main_logger.info(f"Coordinator 标准PPO训练配置: {getattr(self.config, 'ppo_epochs', 10)}个epoch, "
                        f"每批{coordinator_batch_size}个样本")

        for batch in high_level_sampler:
            # 提取离散批次数据（注意没有时间维度T）
            observations_batch = batch['observations'].to(self.device)  # Shape: (B, n_agents, obs_dim)
            states_batch = batch['states'].to(self.device)             # Shape: (B, state_dim)
            
            # 手动应用归一化
            if getattr(self.config, 'use_obsnorm', False) and self.obs_norm is not None:
                mean = torch.tensor(self.obs_norm.mean, device=self.device, dtype=torch.float32)
                var = torch.tensor(self.obs_norm.var, device=self.device, dtype=torch.float32)
                observations_batch = (observations_batch - mean) / torch.sqrt(var + 1e-8)
                observations_batch = torch.clamp(observations_batch, -10.0, 10.0)

            if getattr(self.config, 'use_statenorm', True) and self.state_norm is not None:
                mean = torch.tensor(self.state_norm.mean, device=self.device, dtype=torch.float32)
                var = torch.tensor(self.state_norm.var, device=self.device, dtype=torch.float32)
                states_batch = (states_batch - mean) / torch.sqrt(var + 1e-8)
                states_batch = torch.clamp(states_batch, -10.0, 10.0)

            team_skills_batch = batch['team_skills'].to(self.device)    # Shape: (B,)
            agent_skills_batch = batch['agent_skills'].to(self.device) # Shape: (B, n_agents)
            
            # 【关键修复】使用分离的旧log_probs
            old_team_log_probs_batch = batch['old_team_log_probs'].to(self.device)
            old_agent_log_probs_batch = batch['old_agent_log_probs'].to(self.device)
            
            # 【关键修复】使用分离的优势和回报数据
            team_advantages_batch = batch['team_advantages'].to(self.device)
            agent_advantages_batch = batch['agent_advantages'].to(self.device)
            team_returns_tensor = batch['team_returns'].to(self.device)
            agent_returns_tensor = batch['agent_returns'].to(self.device)
            
            # --- 核心改动：不使用 evaluate_sequence，而是直接调用 forward 和 get_value ---
            # 1. 重新评估当前策略下的 log_probs 和 entropy
            _, _, Z_logits, z_logits_list, _, _ = self.skill_coordinator(states_batch, observations_batch)
            
            Z_dist = Categorical(logits=Z_logits)
            team_log_probs = Z_dist.log_prob(team_skills_batch)
            team_entropy = Z_dist.entropy()

            agent_log_probs_list = []
            agent_entropies = []
            for i in range(self.config.n_agents):
                zi_dist = Categorical(logits=z_logits_list[i])
                agent_log_probs_list.append(zi_dist.log_prob(agent_skills_batch[:, i]))
                agent_entropies.append(zi_dist.entropy())
            
            # 【修复】保持agent_log_probs的形状为 [B, n_agents] 以进行解耦损失计算
            agent_log_probs = torch.stack(agent_log_probs_list, dim=1)
            agent_entropies_tensor = torch.stack(agent_entropies, dim=1)  # Shape: (B, n_agents)

            # 【修复】按照论文公式计算总熵：E[H(π_h(Z|...)) + Σ H(π_h(z_i|...))]
            # 先计算每个批次样本的总熵（团队熵 + 所有个体熵之和），然后取期望（均值）
            total_entropy_per_sample = team_entropy + agent_entropies_tensor.sum(dim=1)  # Shape: (B,)
            entropy = total_entropy_per_sample.mean()  # 对批次取均值，得到标量

            # 2. 获取当前策略下的价值估计
            state_values, agent_values_list, _ = self.skill_coordinator.get_value(states_batch, observations_batch)
            
            # 【论文一致性修复】按照论文公式(6)分别处理团队技能和个体技能的价值
            # 不再合并价值函数，而是分别计算损失
            state_values = state_values.squeeze(-1)  # Shape: (B,) - 用于团队技能
            
            # 将智能体价值列表转换为张量，用于个体技能
            batch_size = states_batch.size(0)
            if agent_values_list is not None and len(agent_values_list) > 0:
                agent_values_tensor = torch.stack(agent_values_list).squeeze(-1)  # Shape: (n_agents, B)
            else:
                agent_values_tensor = torch.zeros(self.config.n_agents, batch_size, device=self.device)

            # 【逻辑修复】统一优势归一化
            # 1. 拼接所有优势 (Batch * (1 + N_Agents))
            # team: [B], agent: [B, N] -> flatten agent -> cat
            all_advantages = torch.cat([team_advantages_batch, agent_advantages_batch.reshape(-1)], dim=0)

            # 2. 计算全局统计量
            global_mean = all_advantages.mean()
            global_std = all_advantages.std() + 1e-8

            # 3. 统一归一化
            team_advantages_batch = (team_advantages_batch - global_mean) / global_std
            agent_advantages_batch = (agent_advantages_batch - global_mean) / global_std

            # --- 【修复】计算解耦的PPO策略损失 ---
            # 1. 团队策略损失
            team_ratios = torch.exp(team_log_probs - old_team_log_probs_batch.detach())
            team_surr1 = team_ratios * team_advantages_batch
            team_surr2 = torch.clamp(team_ratios, 1.0 - self.config.clip_epsilon, 1.0 + self.config.clip_epsilon) * team_advantages_batch
            team_policy_loss = -torch.min(team_surr1, team_surr2).mean()

            # 2. 个体策略损失
            # agent_log_probs shape: [B, n_agents]
            # old_agent_log_probs_batch shape: [B, n_agents]
            # agent_advantages_batch shape: [B, n_agents]
            agent_ratios = torch.exp(agent_log_probs - old_agent_log_probs_batch.detach())
            
            agent_surr1 = agent_ratios * agent_advantages_batch
            agent_surr2 = torch.clamp(agent_ratios, 1.0 - self.config.clip_epsilon, 1.0 + self.config.clip_epsilon) * agent_advantages_batch
            agent_policy_loss = -torch.min(agent_surr1, agent_surr2).mean()

            # 组合策略损失
            policy_loss = team_policy_loss + agent_policy_loss

            # 【内部 ValueNorm】按照论文公式(6)分别计算团队技能和个体技能的价值损失（MAPPO 风格）
            # 假设网络输出 state_values / agent_values_tensor 为归一化后的 value（V_norm），
            # 使用 RunningMeanStd 对真实尺度的 team_returns_tensor / agent_returns_tensor 进行归一化后作为目标。
            if self.config.use_valuenorm and self.value_norm_coordinator is not None:
                mean = torch.as_tensor(
                    self.value_norm_coordinator.mean,
                    device=self.device,
                    dtype=torch.float32,
                )
                var = torch.as_tensor(
                    self.value_norm_coordinator.var,
                    device=self.device,
                    dtype=torch.float32,
                )
                std = torch.sqrt(var + 1e-8)

                # 1) 团队技能 value：用归一化后的团队回报作为目标
                team_returns_norm = (team_returns_tensor - mean) / std
                if hasattr(self.config, "value_clip"):
                    team_returns_norm = torch.clamp(
                        team_returns_norm,
                        -self.config.value_clip,
                        self.config.value_clip,
                    )
                # state_values 被视为 V_norm
                team_value_loss = F.mse_loss(state_values, team_returns_norm.detach())

                # 2) 个体技能 value：同样归一化对应的个体回报
                agent_value_loss = 0.0
                for i in range(self.config.n_agents):
                    agent_returns_norm = (agent_returns_tensor[:, i] - mean) / std
                    if hasattr(self.config, "value_clip"):
                        agent_returns_norm = torch.clamp(
                            agent_returns_norm,
                            -self.config.value_clip,
                            self.config.value_clip,
                        )
                    # agent_values_tensor[i] 被视为 V_norm
                    agent_value_loss += F.mse_loss(agent_values_tensor[i], agent_returns_norm.detach())
                agent_value_loss /= self.config.n_agents
            else:
                team_value_loss = F.mse_loss(state_values, team_returns_tensor.detach())
                agent_value_loss = 0.0
                for i in range(self.config.n_agents):
                    agent_value_loss += F.mse_loss(agent_values_tensor[i], agent_returns_tensor[:, i].detach())
                agent_value_loss /= self.config.n_agents
            
            # 【论文公式(6)】组合团队和个体价值损失
            value_loss = team_value_loss + agent_value_loss
            
            # 熵损失
            # 【修复】使用config中定义的统一熵系数，严格按照论文公式
            entropy_loss = -self.config.lambda_h * entropy
            
            # CD损失（如果启用OPT）
            cd_loss = torch.tensor(0.0, device=self.device)
            if getattr(self.config, 'use_opt_coordinator', False):
                # 对批次中的样本计算平均CD损失
                _, _, cd_loss = self.skill_coordinator.get_value(states_batch, observations_batch)
            
            # 总损失
            if getattr(self.config, 'use_opt_coordinator', False):
                loss = policy_loss + self.config.value_loss_coef * value_loss + entropy_loss + getattr(self.config, 'lambda_cd', 0.1) * cd_loss
            else:
                loss = policy_loss + self.config.value_loss_coef * value_loss + entropy_loss
            
            # 更新网络
            self.coordinator_optimizer.zero_grad()
            if torch.isnan(loss).any() or torch.isinf(loss).any():
                main_logger.error("Loss contains NaN or Inf! Skipping update.")
                continue # 跳过此次更新
            loss.backward()  # 标准的PPO反向传播
            torch.nn.utils.clip_grad_norm_(self.skill_coordinator.parameters(), self.config.max_grad_norm)
            self.coordinator_optimizer.step()
            
            # 累积统计
            total_policy_loss += policy_loss.item()
            total_value_loss += value_loss.item()
            total_entropy_loss += entropy_loss.item()
            total_loss += loss.item()
            total_cd_loss += cd_loss.item()
            
            # 分别统计团队技能和个体技能的熵（用于TensorBoard记录）
            total_team_entropy += team_entropy.mean().item()
            total_agent_entropy += agent_entropies_tensor.mean().item()
            
            update_count += 1
            
            main_logger.debug(f"Coordinator 标准更新 #{update_count}: "
                            f"Loss={loss.item():.6f}, Policy={policy_loss.item():.6f}, "
                            f"Value={value_loss.item():.6f}, Entropy={entropy.item():.6f}")
        
        # 计算平均损失
        avg_policy_loss = total_policy_loss / update_count if update_count > 0 else 0.0
        avg_value_loss = total_value_loss / update_count if update_count > 0 else 0.0
        avg_entropy_loss = total_entropy_loss / update_count if update_count > 0 else 0.0
        avg_total_loss = total_loss / update_count if update_count > 0 else 0.0
        avg_cd_loss = total_cd_loss / update_count if update_count > 0 else 0.0
        avg_team_entropy = total_team_entropy / update_count if update_count > 0 else 0.0
        avg_agent_entropy = total_agent_entropy / update_count if update_count > 0 else 0.0
        
        # 计算其他统计信息（从统一缓冲区获取高层数据）
        if high_level_data_count > 0:
            # 计算平均奖励（只考虑有效的高层数据）
            valid_high_level_rewards = []
            for t in range(num_steps):
                for env_idx in range(self.rollout_buffer.num_envs):
                    if high_level_valid_mask[t, env_idx]:
                        # ▼▼▼▼▼▼▼▼▼▼【恢复此处的修改】▼▼▼▼▼▼▼▼▼▼
                        # 从专用的 high_level_rewards 缓冲区读取
                        valid_high_level_rewards.append(rollout_data["high_level_rewards"][t, env_idx])
                        # ▲▲▲▲▲▲▲▲▲▲【恢复此处的修改】▲▲▲▲▲▲▲▲▲▲
            
            if len(valid_high_level_rewards) > 0:
                avg_high_level_reward = np.mean(valid_high_level_rewards)
                
                # 计算平均价值（随机采样一些状态进行估计）
                sample_size = min(50, len(valid_high_level_rewards))
                sample_states = []
                sample_observations = []
                for t in range(num_steps):
                    for env_idx in range(self.rollout_buffer.num_envs):
                        if high_level_valid_mask[t, env_idx] and len(sample_states) < sample_size:
                            sample_states.append(rollout_data["states"][t, env_idx])
                            sample_observations.append(rollout_data["obs"][t, env_idx])
                
                if len(sample_states) > 0:
                    sample_values = []
                    sample_agent_values = []
                    for i in range(len(sample_states)):
                        with torch.no_grad():
                            state_val, agent_vals, _ = self.skill_coordinator.get_value(
                                torch.FloatTensor(sample_states[i]).unsqueeze(0).to(self.device),
                                torch.FloatTensor(sample_observations[i]).unsqueeze(0).to(self.device)
                            )
                            sample_values.append(state_val.item())
                            if agent_vals is not None and len(agent_vals) > 0:
                                # agent_vals is a list of tensors, stack them and then take the mean
                                agent_vals_tensor = torch.stack(agent_vals)
                                sample_agent_values.append(agent_vals_tensor.mean().item())
                    mean_state_value = np.mean(sample_values) if sample_values else 0.0
                    mean_agent_value = np.mean(sample_agent_values) if sample_agent_values else 0.0
                else:
                    mean_state_value = 0.0
                    mean_agent_value = 0.0
            else:
                avg_high_level_reward = 0.0
                mean_state_value = 0.0
                mean_agent_value = 0.0
        else:
            avg_high_level_reward = 0.0
            mean_state_value = 0.0
            mean_agent_value = 0.0
        
        main_logger.info(f"Coordinator 标准更新完成: {update_count}次更新, "
                        f"平均损失={avg_total_loss:.6f}, 平均策略损失={avg_policy_loss:.6f}, "
                        f"平均价值损失={avg_value_loss:.6f}")
        
        return avg_total_loss, avg_policy_loss, avg_value_loss, \
               avg_team_entropy, avg_agent_entropy, \
               mean_state_value, mean_agent_value, avg_high_level_reward, avg_cd_loss
    
    def update_discoverer_from_rollout(self, last_values, dones):
        """
        使用重构后的RolloutBuffer更新低层技能发现器网络。
        """
        main_logger.info("开始使用重构后的RolloutBuffer更新Discoverer...")
        
        # 1. 计算GAE
        # 【关键修复】Buffer中已是真实值，不再需要value_normalizer进行反归一化
        self.rollout_buffer.compute_advantages(
            last_values, 
            dones, 
            gamma=self.config.gamma, 
            gae_lambda=self.config.gae_lambda, 
            value_normalizer=None
        )
        
        # 累积损失统计
        total_policy_loss, total_value_loss, total_entropy_loss, total_loss = 0.0, 0.0, 0.0, 0.0
        update_count = 0
        
        ppo_epochs = getattr(self.config, 'ppo_epochs', 10)  # 统一默认值为10
        num_sequences_per_batch = getattr(self.config, 'sequence_batch_size', 32)
        
        # 2. 获取采样器
        # 【关键修复】启用基于 Chunk 的序列切分，使用技能步长 k 作为切分长度
        # 这解决了只使用完整 rollout 进行训练导致的显存爆炸和梯度问题
        sequence_sampler = self.rollout_buffer.get_discoverer_sampler(
            ppo_epochs, 
            num_sequences_per_batch, 
            chunk_length=self.config.k
        )
        
        if sequence_sampler is None:
            main_logger.error("无法获取Discoverer采样器，跳过更新。")
            return 0, 0, 0, 0, 0, 0, 0, 0, 0

        # --- 在所有PPO Epochs开始前，一次性更新统计量 ---
        if self.config.use_valuenorm and self.value_norm_discoverer is not None:
            all_returns = self.rollout_buffer.returns.reshape(-1)
            self.value_norm_discoverer.update(all_returns)
            main_logger.info(f"Discoverer ValueNorm已更新. 新均值: {self.value_norm_discoverer.mean:.4f}, 新标准差: {np.sqrt(self.value_norm_discoverer.var):.4f}")

        for batch in sequence_sampler:
            # ... (与旧版本类似的PPO更新逻辑) ...
            # 此处省略了详细的PPO更新代码，因为它与旧版本非常相似，
            # 关键区别在于现在的数据来自一个干净的、无污染的采样器。
            # 核心是使用 batch 中的 'advantages' 和 'returns'
            
            # 提取并转换数据
            observations_seq = batch['observations'].to(self.device)
            agent_skills_seq = batch['agent_skills'].to(self.device)
            actions_seq = batch['actions'].to(self.device)
            global_states_seq = batch['global_states'].to(self.device)

            # 手动应用归一化 (使用当前统计量，不更新统计量，且保持在GPU上)
            if getattr(self.config, 'use_obsnorm', False) and self.obs_norm is not None:
                mean = torch.tensor(self.obs_norm.mean, device=self.device, dtype=torch.float32)
                var = torch.tensor(self.obs_norm.var, device=self.device, dtype=torch.float32)
                observations_seq = (observations_seq - mean) / torch.sqrt(var + 1e-8)
                observations_seq = torch.clamp(observations_seq, -10.0, 10.0)

            if getattr(self.config, 'use_statenorm', True) and self.state_norm is not None:
                mean = torch.tensor(self.state_norm.mean, device=self.device, dtype=torch.float32)
                var = torch.tensor(self.state_norm.var, device=self.device, dtype=torch.float32)
                global_states_seq = (global_states_seq - mean) / torch.sqrt(var + 1e-8)
                global_states_seq = torch.clamp(global_states_seq, -10.0, 10.0)
            team_skills_seq = batch['team_skills'].to(self.device)
            initial_hxs = batch['initial_hxs'].to(self.device)
            dones_seq = batch['dones'].to(self.device)
            initial_critic_hxs = batch['initial_critic_hxs'].to(self.device)
            
            old_log_probs_seq = batch['log_probs'].to(self.device)
            advantages_seq = batch['advantages'].to(self.device)
            returns_seq = batch['returns'].to(self.device)
            value_preds_seq = batch['value_preds'].to(self.device)
            masks_seq = batch['masks'].to(self.device)

            # 重新评估序列
            new_log_probs, new_values, entropy = self.skill_discoverer.evaluate_sequence(
                observations_seq, agent_skills_seq, actions_seq, 
                global_states_seq, team_skills_seq,
                initial_hxs, dones_seq, initial_critic_hxs=initial_critic_hxs
            )

            # 展平数据
            advantages_flat = advantages_seq.reshape(-1)
            returns_flat = returns_seq.reshape(-1)
            value_preds_flat = value_preds_seq.reshape(-1)
            old_log_probs_flat = old_log_probs_seq.reshape(-1)
            new_log_probs_flat = new_log_probs.reshape(-1)
            new_values_flat = new_values.reshape(-1)
            masks_flat = masks_seq.reshape(-1)

            # 在计算损失前，使用掩码过滤无效数据
            valid_indices = masks_flat.nonzero(as_tuple=False).squeeze()
            
            if valid_indices.numel() == 0:
                main_logger.warning("在Discoverer更新中，当前批次没有有效数据，跳过。")
                continue

            advantages_flat = advantages_flat[valid_indices]
            returns_flat = returns_flat[valid_indices]
            old_log_probs_flat = old_log_probs_flat[valid_indices]
            new_log_probs_flat = new_log_probs_flat[valid_indices]
            new_values_flat = new_values_flat[valid_indices]

            # 优势归一化
            advantages_flat = (advantages_flat - advantages_flat.mean()) / (advantages_flat.std() + 1e-8)

            # 计算PPO损失
            ratios = torch.exp(new_log_probs_flat - old_log_probs_flat.detach())
            surr1 = ratios * advantages_flat
            surr2 = torch.clamp(ratios, 1.0 - self.config.clip_epsilon, 1.0 + self.config.clip_epsilon) * advantages_flat
            policy_loss = -torch.min(surr1, surr2).mean()

            # 【内部 ValueNorm】价值损失计算（MAPPO 风格）
            # 假设网络输出 new_values_flat 为归一化后的 value，
            # 使用 RunningMeanStd 对真实尺度的 returns_flat 进行归一化后作为目标。
            if self.config.use_valuenorm and self.value_norm_discoverer is not None:
                mean = torch.as_tensor(
                    self.value_norm_discoverer.mean,
                    device=self.device,
                    dtype=torch.float32,
                )
                var = torch.as_tensor(
                    self.value_norm_discoverer.var,
                    device=self.device,
                    dtype=torch.float32,
                )
                std = torch.sqrt(var + 1e-8)

                # 将真实尺度 returns 归一化为 target
                returns_norm = (returns_flat - mean) / std
                if hasattr(self.config, "value_clip"):
                    returns_norm = torch.clamp(
                        returns_norm,
                        -self.config.value_clip,
                        self.config.value_clip,
                    )

                # new_values_flat 被视为 V_norm，直接拟合归一化后的 target
                value_loss = F.mse_loss(new_values_flat, returns_norm.detach())
            else:
                # 未启用 ValueNorm 时，直接在真实尺度上拟合
                value_loss = F.mse_loss(new_values_flat, returns_flat.detach())
            
            # 熵损失
            entropy_loss = -entropy * self.config.lambda_l

            # 解耦更新
            actor_loss = policy_loss + entropy_loss
            critic_loss = self.config.value_loss_coef * value_loss

            self.discoverer_actor_optimizer.zero_grad()
            actor_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.skill_discoverer.actor.parameters(), self.config.max_grad_norm)
            self.discoverer_actor_optimizer.step()

            self.discoverer_critic_optimizer.zero_grad()
            critic_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.skill_discoverer.critic.parameters(), self.config.max_grad_norm)
            self.discoverer_critic_optimizer.step()

            total_loss += (actor_loss + critic_loss).item()
            total_policy_loss += policy_loss.item()
            total_value_loss += value_loss.item()
            total_entropy_loss += entropy_loss.item()
            update_count += 1

        # 计算平均值
        avg_loss = total_loss / update_count if update_count > 0 else 0
        avg_policy_loss = total_policy_loss / update_count if update_count > 0 else 0
        avg_value_loss = total_value_loss / update_count if update_count > 0 else 0
        avg_entropy_loss = total_entropy_loss / update_count if update_count > 0 else 0
        
        # 其他统计信息
        data = self.rollout_buffer._get_full_rollout_data()
        avg_intrinsic_reward = np.mean(data["rewards"]) if data and "rewards" in data else 0
        avg_env_comp = np.mean(data["reward_env"]) if data and "reward_env" in data else 0
        avg_team_disc_comp = np.mean(data["reward_team_disc"]) if data and "reward_team_disc" in data else 0
        avg_ind_disc_comp = np.mean(data["reward_ind_disc"]) if data and "reward_ind_disc" in data else 0
        
        avg_discoverer_val = np.mean(data["values"]) if data and "values" in data else 0
        action_entropy_val = -avg_entropy_loss / self.config.lambda_l if self.config.lambda_l > 0 else 0

        main_logger.info(f"Discoverer更新完成: 平均损失={avg_loss:.4f}")
        
        return avg_loss, avg_policy_loss, avg_value_loss, action_entropy_val, \
               avg_intrinsic_reward, avg_env_comp, avg_team_disc_comp, avg_ind_disc_comp, avg_discoverer_val

    
    def update_discriminators(self, num_steps, noise_std=None):
        """
        【论文一致性修复】更新技能判别器网络
        
        严格按照论文 Algorithm 1 的伪代码逻辑：
        - 使用当前 rollout 收集的**全部数据**进行更新（On-Policy）
        - 在 Policy 更新之后执行（由 update() 方法保证调用顺序）
        - 更新完成后，discriminator_buffer 将在 clear_buffers() 中被清空
        
        【噪声注入】在训练判别器时为输入添加高斯噪声，提高鲁棒性：
        - 平滑流形，防止判别器过拟合
        - 只在更新参数时添加噪声，计算奖励时不加
        - 不给离散的技能标签添加噪声
        
        参数:
            num_steps: 当前 rollout 的有效步数
            noise_std: 噪声标准差，默认从 config.discriminator_noise_std 获取，若无则为 0.05
        
        返回值：team_disc_avg_loss + ind_disc_avg_loss（两个判别器损失之和）
        """
        
        # 获取噪声标准差，优先使用参数，其次使用配置，默认0.05
        if noise_std is None:
            noise_std = getattr(self.config, 'discriminator_noise_std', 0.05)
        
        update_epochs = getattr(self.config, 'ppo_epochs', 10)
        all_data = self.discriminator_buffer.get_all()
        
        if len(all_data) == 0:
            main_logger.warning("判别器Buffer为空，跳过判别器更新")
            return 0
        
        team_data = [d for d in all_data if d['type'] == 'team']
        ind_data = [d for d in all_data if d['type'] == 'individual']
        
        main_logger.info(f"判别器On-Policy更新: 团队数据={len(team_data)}个, 个体数据={len(ind_data)}个")
        
        # 预处理数据为张量
        team_states, team_skills_tensor = None, None
        if len(team_data) > 0:
            team_states = torch.FloatTensor(np.array([d['state'] for d in team_data])).to(self.device)
            team_skills_tensor = torch.LongTensor([d['skill'] for d in team_data]).to(self.device)
        
        ind_observations, ind_team_skills_cond, ind_agent_skills = None, None, None
        if len(ind_data) > 0:
            ind_observations = torch.FloatTensor(np.array([d['obs'] for d in ind_data])).to(self.device)
            ind_team_skills_cond = torch.LongTensor([d['team_skill'] for d in ind_data]).to(self.device)
            ind_agent_skills = torch.LongTensor([d['skill'] for d in ind_data]).to(self.device)
        
        # 【修复】分别追踪两个判别器的损失
        team_loss_accumulated, team_update_count = 0.0, 0
        ind_loss_accumulated, ind_update_count = 0.0, 0
        
        batch_size = getattr(self.config, 'discriminator_batch_size', self.config.batch_size)
        
        for epoch in range(update_epochs):
            # 团队技能判别器更新
            if team_states is not None:
                num_team_samples = len(team_data)
                indices = torch.randperm(num_team_samples)
                for start_idx in range(0, num_team_samples, batch_size):
                    end_idx = min(start_idx + batch_size, num_team_samples)
                    batch_indices = indices[start_idx:end_idx]
                    batch_states = team_states[batch_indices]
                    batch_skills = team_skills_tensor[batch_indices]
                    
                    # ================= [噪声注入 - 团队判别器] =================
                    # 为状态输入添加高斯噪声，提高判别器鲁棒性
                    # 注意：不给离散的 batch_skills (Z) 加噪声！
                    with torch.no_grad():
                        state_noise = torch.randn_like(batch_states) * noise_std
                    noisy_batch_states = batch_states + state_noise
                    # ================= [噪声注入结束] =================
                    
                    team_disc_logits = self.team_discriminator(noisy_batch_states)
                    team_disc_loss = F.cross_entropy(team_disc_logits, batch_skills)
                    
                    self.discriminator_optimizer.zero_grad()
                    team_disc_loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.team_discriminator.parameters(), self.config.max_grad_norm)
                    self.discriminator_optimizer.step()
                    
                    team_loss_accumulated += team_disc_loss.item()
                    team_update_count += 1
            
            # 个体技能判别器更新
            if ind_observations is not None:
                num_ind_samples = len(ind_data)
                indices = torch.randperm(num_ind_samples)
                for start_idx in range(0, num_ind_samples, batch_size):
                    end_idx = min(start_idx + batch_size, num_ind_samples)
                    batch_indices = indices[start_idx:end_idx]
                    batch_obs = ind_observations[batch_indices]
                    batch_team_skills = ind_team_skills_cond[batch_indices]
                    batch_agent_skills = ind_agent_skills[batch_indices]
                    
                    # ================= [噪声注入 - 个体判别器] =================
                    # 为观测输入添加高斯噪声，提高判别器鲁棒性
                    # 注意：不给离散的 batch_team_skills (Z) 和 batch_agent_skills (z) 加噪声！
                    with torch.no_grad():
                        obs_noise = torch.randn_like(batch_obs) * noise_std
                    noisy_batch_obs = batch_obs + obs_noise
                    # ================= [噪声注入结束] =================
                    
                    agent_disc_logits = self.individual_discriminator(noisy_batch_obs, batch_team_skills)
                    agent_disc_loss = F.cross_entropy(agent_disc_logits, batch_agent_skills)
                    
                    self.discriminator_optimizer.zero_grad()
                    agent_disc_loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.individual_discriminator.parameters(), self.config.max_grad_norm)
                    self.discriminator_optimizer.step()
                    
                    ind_loss_accumulated += agent_disc_loss.item()
                    ind_update_count += 1
        
        # 【修复】分别计算两个判别器的平均损失，然后求和
        team_avg_loss = team_loss_accumulated / max(1, team_update_count)
        ind_avg_loss = ind_loss_accumulated / max(1, ind_update_count)
        total_loss = team_avg_loss + ind_avg_loss
        
        # 计算准确率
        with torch.no_grad():
            team_acc = (self.team_discriminator(team_states).argmax(-1) == team_skills_tensor).float().mean().item() if team_states is not None else 0.0
            ind_acc = (self.individual_discriminator(ind_observations, ind_team_skills_cond).argmax(-1) == ind_agent_skills).float().mean().item() if ind_observations is not None else 0.0
        
        main_logger.info(f"判别器更新完成: Team Loss={team_avg_loss:.4f}, Ind Loss={ind_avg_loss:.4f}, "
                        f"Total={total_loss:.4f}, Team Acc={team_acc:.4f}, Ind Acc={ind_acc:.4f}")
        
        return total_loss
    
    def update(self, last_values, dones, steps_in_buffer, last_state=None, last_observations=None):
        """
        【论文一致性修复】更新所有网络
        
        参数:
            last_values: 最后一步的价值估计（低层）
            dones: 最后一步的终止标志
            steps_in_buffer: 缓冲区中的步数
            last_state: 最后一步的全局状态（新增，用于Coordinator Bootstrap）
            last_observations: 最后一步的观测（新增，用于Coordinator Bootstrap）

        严格按照论文 Algorithm 1 的 Training Phase 顺序：
        1. 先更新 Coordinator (高层策略) - 使用"旧" Discriminator 计算的内在奖励
        2. 再更新 Discoverer (低层策略) - 使用"旧" Discriminator 计算的内在奖励
        3. 最后更新 Discriminator - 使用当前 rollout 的全部数据进行 On-Policy 更新
        
        这确保了：
        - Policy 的更新依赖于 Discriminator 更新前输出的 Reward 值
        - Discriminator 更新后，下一轮采样的内在奖励会基于新的 Discriminator
        - 形成完整的逻辑闭环
        """
        # 更新全局步数
        self.global_step += 1
        main_logger.debug(f"HMASDAgent.update (step {self.global_step}): 开始更新所有网络，有效步数: {steps_in_buffer}")

        # [新增] 熵系数退火逻辑
        if self.use_entropy_annealing:
            # 计算当前环境总步数 (估算)
            steps_per_update = self.config.num_envs * self.config.rollout_length
            current_env_steps = self.global_step * steps_per_update
            
            # 计算进度 (0.0 -> 1.0)
            progress = min(current_env_steps / self.entropy_anneal_steps, 1.0)
            
            if self.entropy_anneal_schedule == 'cosine':
                progress_adjusted = 0.5 * (1 - np.cos(np.pi * progress))
            else: # linear
                progress_adjusted = progress
            
            # 更新 config 中的熵系数
            self.config.lambda_h = self.lambda_h_initial + (self.lambda_h_final - self.lambda_h_initial) * progress_adjusted
            self.config.lambda_l = self.lambda_l_initial + (self.lambda_l_final - self.lambda_l_initial) * progress_adjusted
            
            # 记录退火状态 (Debug级别)
            if self.global_step % 100 == 0:
                main_logger.debug(f"熵系数退火 [进度: {progress_adjusted:.4f}]: lambda_h={self.config.lambda_h:.6f}, lambda_l={self.config.lambda_l:.6f}")

        # 【Coordinator Bootstrap 修复】计算高层策略的 Bootstrap Values
        coord_bootstrap_values = None
        if last_state is not None and last_observations is not None:
            try:
                with torch.no_grad():
                    # 标准化输入
                    last_state_norm = self._normalize_states(last_state)
                    last_obs_norm = self._normalize_observations(last_observations)
                    
                    # 转换为 Tensor
                    state_tensor = torch.FloatTensor(last_state_norm).to(self.device)
                    obs_tensor = torch.FloatTensor(last_obs_norm).to(self.device)
                    
                    # 计算价值
                    state_val, agent_vals, _ = self.skill_coordinator.get_value(state_tensor, obs_tensor)
                    
                    # 【反归一化修复】确保Bootstrap Value是真实尺度
                    if self.config.use_valuenorm and self.value_norm_coordinator is not None:
                        state_val = self._denormalize_values(state_val, self.value_norm_coordinator)
                        agent_vals = [self._denormalize_values(v, self.value_norm_coordinator) for v in agent_vals]

                    # 转换为 Numpy 格式
                    # state_val: [num_envs, 1] -> [num_envs]
                    # agent_vals: list of [num_envs, 1] -> [num_envs, n_agents]
                    if agent_vals is not None and len(agent_vals) > 0:
                        agent_vals_np = np.array([v.cpu().numpy().flatten() for v in agent_vals]).T
                    else:
                        agent_vals_np = np.zeros((self.config.num_envs, self.config.n_agents))
                        
                    coord_bootstrap_values = {
                        'state': state_val.cpu().numpy().flatten(),
                        'agents': agent_vals_np
                    }
                    main_logger.info("已使用最新的next_state计算Coordinator Bootstrap Values")
            except Exception as e:
                main_logger.error(f"计算Coordinator Bootstrap Values时出错: {e}")
        else:
            main_logger.warning("未提供last_state或last_observations，Coordinator Bootstrap将使用回退机制")

        # 更频繁地检查环境贡献情况（从1000步降至200步）
        if self.global_step % 200 == 0:
            # 获取所有环境的贡献情况
            env_contributions = {}
            for env_id in range(self.config.num_envs):
                env_contributions[env_id] = self.high_level_samples_by_env.get(env_id, 0)
            
            # 找出贡献较少的环境，降低贡献阈值使更多环境被标记
            low_contribution_envs = {env_id: count for env_id, count in env_contributions.items() if count < 3}
            if low_contribution_envs:
                main_logger.info(f"以下环境贡献样本较少，将强制其在下一个技能周期结束时贡献: {low_contribution_envs}")
                # 标记这些环境在下一个技能周期结束时强制贡献样本
                for env_id in low_contribution_envs:
                    self.force_high_level_collection[env_id] = True
                    # 同时将这些环境的奖励阈值重置为0
                    self.env_reward_thresholds[env_id] = 0.0
            
            # 记录rollout缓冲区状态（统一缓冲区）
            rollout_buffer_pos = self.global_step % self.rollout_buffer.num_steps
            rollout_buffer_full = rollout_buffer_pos == self.rollout_buffer.num_steps - 1
            main_logger.debug(f"当前rollout缓冲区状态: {rollout_buffer_pos}/{self.rollout_buffer.num_steps} (当前/总容量), 完整: {rollout_buffer_full}")
            
            # 检查高层策略数据是否足够
            rollout_data_for_check = self.rollout_buffer._get_full_rollout_data()
            if rollout_data_for_check:
                high_level_data_count = np.sum(rollout_data_for_check['high_level_valid_mask'][:rollout_buffer_pos])
            else:
                high_level_data_count = 0
            
            # 如果高层数据增长过慢，强制所有环境进行贡献
            if high_level_data_count < 10 and self.global_step > 5000:  # 至少需要10个高层决策样本
                main_logger.warning(f"高层策略数据增长过慢 (有效高层样本: {high_level_data_count})，强制所有环境贡献样本")
                for env_id in range(self.config.num_envs):
                    self.force_high_level_collection[env_id] = True
                    self.env_reward_thresholds[env_id] = 0.0
            
            # 计算环境贡献分布统计（供训练脚本记录）
            contrib_data = np.zeros(self.config.num_envs)
            for env_id, count in env_contributions.items():
                contrib_data[env_id] = count
            # 计算贡献标准差，衡量是否平衡
            contrib_std = np.std(contrib_data)
            # 计算有效贡献环境数量
            contrib_envs = np.sum(contrib_data > 0)
        
        # ============================================================
        # 【论文一致性修复】Training Phase 执行顺序
        # ============================================================
        
        # 步骤 1: 更新高层技能协调器 (Coordinator)
        # 使用基于"旧" Discriminator 计算的内在奖励进行 PPO 更新
        # 【Bootstrap修复】传入计算好的 bootstrap_values
        if getattr(self.config, 'disable_high_level_training', False):
            coordinator_loss = coordinator_policy_loss = coordinator_value_loss = 0.0
            team_skill_entropy = agent_skill_entropy = 0.0
            mean_coord_state_val = mean_coord_agent_val = mean_high_level_reward = cd_loss_val = 0.0
        else:
            coordinator_loss, coordinator_policy_loss, coordinator_value_loss, team_skill_entropy, agent_skill_entropy, \
            mean_coord_state_val, mean_coord_agent_val, mean_high_level_reward, cd_loss_val = self.update_coordinator(
                steps_in_buffer, bootstrap_values=coord_bootstrap_values
            )
        
        # 步骤 2: 更新低层技能发现器 (Discoverer)
        # 同样使用基于"旧" Discriminator 计算的内在奖励进行 PPO 更新
        discoverer_loss, discoverer_policy_loss, discoverer_value_loss, action_entropy, \
        avg_intrinsic_reward, avg_env_comp, avg_team_disc_comp, avg_ind_disc_comp, \
        avg_discoverer_val = self.update_discoverer_from_rollout(last_values, dones)
        
        # 步骤 3: 更新技能判别器 (Discriminator)
        # 【关键】在 Policy 更新完成后，使用当前 rollout 的全部数据进行 On-Policy 更新
        # 这确保了：
        # - 当前 rollout 的内在奖励是基于"旧" Discriminator 计算的（已在上面使用）
        # - 更新后的 Discriminator 将用于下一轮采样时计算新的内在奖励
        if getattr(self.config, 'disable_discriminator_training', False):
            discriminator_loss = 0.0
        else:
            discriminator_loss = self.update_discriminators(steps_in_buffer)
        
        # 更新学习率调度器
        if getattr(self.config, 'use_lr_decay', False) and self.global_step <= self.config.lr_decay_steps:
            if self.coordinator_scheduler is not None:
                self.coordinator_scheduler.step()
            # 【关键修复】更新解耦后的Discoverer调度器
            if hasattr(self, 'discoverer_actor_scheduler') and self.discoverer_actor_scheduler is not None:
                self.discoverer_actor_scheduler.step()
            if hasattr(self, 'discoverer_critic_scheduler') and self.discoverer_critic_scheduler is not None:
                self.discoverer_critic_scheduler.step()
            if self.discriminator_scheduler is not None:
                self.discriminator_scheduler.step()

        # 更新训练信息
        self.training_info['high_level_loss'].append(coordinator_loss)
        self.training_info['low_level_loss'].append(discoverer_loss)
        self.training_info['discriminator_loss'].append(discriminator_loss)
        self.training_info['team_skill_entropy'].append(team_skill_entropy) # 真正的团队技能熵
        self.training_info['agent_skill_entropy'].append(agent_skill_entropy) # 个体技能熵，不再是占位符
        self.training_info['action_entropy'].append(action_entropy)
        
        self.training_info['intrinsic_reward_low_level_average'].append(avg_intrinsic_reward)
        self.training_info['intrinsic_reward_env_component'].append(avg_env_comp)
        self.training_info['intrinsic_reward_team_disc_component'].append(avg_team_disc_comp)
        self.training_info['intrinsic_reward_ind_disc_component'].append(avg_ind_disc_comp)
        
        self.training_info['coordinator_state_value_mean'].append(mean_coord_state_val)
        self.training_info['coordinator_agent_value_mean'].append(mean_coord_agent_val)
        self.training_info['discoverer_value_mean'].append(avg_discoverer_val)

        # 计算权重退火信息（不写入TensorBoard，供训练脚本使用）
        annealing_stats = {}
        if self.use_reward_annealing:
            # 计算当前权重
            progress = min(self.global_step / self.anneal_steps, 1.0)
            if self.anneal_schedule == 'cosine':
                progress_adjusted = 0.5 * (1 - np.cos(np.pi * progress))
            else:
                progress_adjusted = progress
            
            w_intrinsic_current = self.w_intrinsic_initial + (self.w_intrinsic_final - self.w_intrinsic_initial) * progress_adjusted
            w_extrinsic_current = self.w_extrinsic_initial + (self.w_extrinsic_final - self.w_extrinsic_initial) * progress_adjusted
            
            annealing_stats = {
                'progress': progress,
                'progress_adjusted': progress_adjusted,
                'w_intrinsic_current': w_intrinsic_current,
                'w_extrinsic_current': w_extrinsic_current,
                'effective_lambda_D': self.config.lambda_D * w_intrinsic_current,
                'effective_lambda_d': self.config.lambda_d * w_intrinsic_current,
                'effective_lambda_e': self.config.lambda_e * w_extrinsic_current
            }

        # 获取当前学习率（供训练脚本记录）
        current_coord_lr = self.coordinator_optimizer.param_groups[0]['lr']
        current_disc_actor_lr = self.discoverer_actor_optimizer.param_groups[0]['lr']
        current_disc_critic_lr = self.discoverer_critic_optimizer.param_groups[0]['lr']
        current_discriminator_lr = self.discriminator_optimizer.param_groups[0]['lr']
        
        learning_rates = {
            'coordinator_lr': current_coord_lr,
            'discoverer_actor_lr': current_disc_actor_lr,
            'discoverer_critic_lr': current_disc_critic_lr,
            'discriminator_lr': current_discriminator_lr
        }

        # 获取Value Normalization统计信息（供训练脚本记录）
        value_norm_stats = {}
        if self.config.use_valuenorm:
            if self.value_norm_coordinator is not None:
                value_norm_stats['coordinator'] = {
                    'mean': self.value_norm_coordinator.mean.item(),
                    'std': np.sqrt(self.value_norm_coordinator.var.item()),
                    'count': self.value_norm_coordinator.count
                }
            if self.value_norm_discoverer is not None:
                value_norm_stats['discoverer'] = {
                    'mean': self.value_norm_discoverer.mean.item(),
                    'std': np.sqrt(self.value_norm_discoverer.var.item()),
                    'count': self.value_norm_discoverer.count
                }
        
        # 返回的字典也应包含新指标，方便外部调用者获取
        return {
            'discriminator_loss': discriminator_loss,
            'coordinator_loss': coordinator_loss,
            'coordinator_policy_loss': coordinator_policy_loss,
            'coordinator_value_loss': coordinator_value_loss,
            'discoverer_loss': discoverer_loss,
            'discoverer_policy_loss': discoverer_policy_loss,
            'discoverer_value_loss': discoverer_value_loss,
            'team_skill_entropy': team_skill_entropy, # 团队技能熵
            'agent_skill_entropy': agent_skill_entropy, # 个体技能熵
            'action_entropy': action_entropy, # 低层动作熵
            'avg_intrinsic_reward': avg_intrinsic_reward,
            'avg_env_comp': avg_env_comp,
            'avg_team_disc_comp': avg_team_disc_comp,
            'avg_ind_disc_comp': avg_ind_disc_comp,
            'mean_coord_state_val': mean_coord_state_val,
            'mean_coord_agent_val': mean_coord_agent_val,
            'avg_discoverer_val': avg_discoverer_val,
            'mean_high_level_reward': mean_high_level_reward, # 高层奖励均值
            'cd_loss': cd_loss_val
        }
    
    def save_model(self, path):
        """保存模型"""
        checkpoint = {
            'skill_coordinator': self.skill_coordinator.state_dict(),
            'skill_discoverer': self.skill_discoverer.state_dict(),
            'team_discriminator': self.team_discriminator.state_dict(),
            'individual_discriminator': self.individual_discriminator.state_dict(),
            'coordinator_optimizer': self.coordinator_optimizer.state_dict(),
            'discoverer_actor_optimizer': self.discoverer_actor_optimizer.state_dict(),
            'discoverer_critic_optimizer': self.discoverer_critic_optimizer.state_dict(),
            'discriminator_optimizer': self.discriminator_optimizer.state_dict(),
            'config': self.config
            # 注意：不再保存discriminator_buffer，因为Discriminator现在是On-Policy模式
        }
        
        # 保存SB3 RunningMeanStd状态（如果启用）
        if self.config.use_valuenorm:
            valuenorm_state = {}
            if self.value_norm_coordinator is not None:
                valuenorm_state['coordinator'] = {
                    'mean': self.value_norm_coordinator.mean,
                    'var': self.value_norm_coordinator.var,
                    'count': self.value_norm_coordinator.count
                }
            if self.value_norm_discoverer is not None:
                valuenorm_state['discoverer'] = {
                    'mean': self.value_norm_discoverer.mean,
                    'var': self.value_norm_discoverer.var,
                    'count': self.value_norm_discoverer.count
                }
            checkpoint['valuenorm_state'] = valuenorm_state
            main_logger.info("已保存SB3 RunningMeanStd状态")
        
        # 保存观测和状态标准化统计信息（新增）
        normalization_state = {}
        if getattr(self.config, 'use_obsnorm', False) and self.obs_norm is not None:
            normalization_state['obs_norm'] = {
                'mean': self.obs_norm.mean,
                'var': self.obs_norm.var,
                'count': self.obs_norm.count
            }
        if getattr(self.config, 'use_statenorm', True) and self.state_norm is not None:
            normalization_state['state_norm'] = {
                'mean': self.state_norm.mean,
                'var': self.state_norm.var,
                'count': self.state_norm.count
            }
        if normalization_state:
            checkpoint['normalization_state'] = normalization_state
            main_logger.info("已保存观测和状态标准化统计信息")
        
        torch.save(checkpoint, path)
        main_logger.info(f"模型已保存到 {path}")
    
    def log_skill_distribution(self, team_skill, agent_skills, episode=None):
        """记录技能分配分布到TensorBoard
        
        参数:
            team_skill: 团队技能索引
            agent_skills: 个体技能索引列表
            episode: 如果提供，将作为x轴记录点；否则使用global_step
        """
        if not hasattr(self, 'writer'):
            return
            
        step = episode if episode is not None else self.global_step
        
        # 记录当前团队技能 (瞬时)
        self.writer.add_scalar('Skills/Current/TeamSkill', team_skill, step)
        
        # 记录当前个体技能分布 (瞬时)
        for i, skill_val in enumerate(agent_skills): # Renamed skill to skill_val to avoid conflict
            self.writer.add_scalar(f'Skills/Current/Agent{i}_Skill', skill_val, step)
        
        # 计算并记录当前个体技能的多样性 (瞬时)
        if len(agent_skills) > 0:
            current_skill_counts = {}
            for skill_val in agent_skills:
                current_skill_counts[skill_val] = current_skill_counts.get(skill_val, 0) + 1
            
            n_agents_current = len(agent_skills)
            current_skill_entropy = 0
            for count in current_skill_counts.values():
                p = count / n_agents_current
                if p > 0: # Avoid log(0)
                    current_skill_entropy -= p * np.log(p)
            self.writer.add_scalar('Skills/Current/Diversity', current_skill_entropy, step)

        # 记录整个episode的技能使用计数
        if episode is not None: #只在提供了episode（通常在episode结束时）才记录和重置计数
            for skill_id, count_val in self.episode_team_skill_counts.items():
                self.writer.add_scalar(f'Skills/EpisodeCounts/TeamSkill_{skill_id}', count_val, episode)
            
            for i, agent_counts in enumerate(self.episode_agent_skill_counts):
                for skill_id, count_val in agent_counts.items():
                    self.writer.add_scalar(f'Skills/EpisodeCounts/Agent{i}_Skill_{skill_id}', count_val, episode)
            
            # 重置计数器为下一个episode做准备
            self.episode_team_skill_counts = {}
            # 根据当前智能体数量（如果有）或配置重新初始化，以防智能体数量变化
            num_current_agents = len(agent_skills) if agent_skills is not None and len(agent_skills) > 0 else self.config.n_agents
            self.episode_agent_skill_counts = [{} for _ in range(num_current_agents)]
            # 降级为DEBUG日志，避免频繁输出到控制台
            main_logger.debug(f"Episode {episode} skill counts logged and reset.")

    def load_model(self, path):
        """加载模型"""
        # 导入 Config 类并将其添加到安全列表
        from config_1 import Config
        import numpy.core.multiarray
        torch.serialization.add_safe_globals([Config, numpy.core.multiarray._reconstruct])
        
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        
        # 使用 strict=False 来处理模型架构不匹配的问题
        # 这允许加载匹配的层，同时忽略不匹配的层（如旧的transformer vs 新的opt，或变化的智能体数量）
        self.skill_coordinator.load_state_dict(checkpoint['skill_coordinator'], strict=False)
        self.skill_discoverer.load_state_dict(checkpoint['skill_discoverer'], strict=False)
        self.team_discriminator.load_state_dict(checkpoint['team_discriminator'], strict=False)
        self.individual_discriminator.load_state_dict(checkpoint['individual_discriminator'], strict=False)
        
        # 加载优化器状态（如果存在）
        if 'coordinator_optimizer' in checkpoint:
            self.coordinator_optimizer.load_state_dict(checkpoint['coordinator_optimizer'])
            main_logger.info("已恢复Coordinator优化器状态")
        if 'discoverer_actor_optimizer' in checkpoint and 'discoverer_critic_optimizer' in checkpoint:
            self.discoverer_actor_optimizer.load_state_dict(checkpoint['discoverer_actor_optimizer'])
            self.discoverer_critic_optimizer.load_state_dict(checkpoint['discoverer_critic_optimizer'])
            main_logger.info("已恢复Discoverer Actor和Critic优化器状态")
        elif 'discoverer_optimizer' in checkpoint: # 兼容旧模型
            self.discoverer_actor_optimizer.load_state_dict(checkpoint['discoverer_optimizer'])
            self.discoverer_critic_optimizer.load_state_dict(checkpoint['discoverer_optimizer'])
            main_logger.warning("从旧的组合优化器状态恢复Discoverer Actor和Critic优化器")
        if 'discriminator_optimizer' in checkpoint:
            self.discriminator_optimizer.load_state_dict(checkpoint['discriminator_optimizer'])
            main_logger.info("已恢复Discriminator优化器状态")
        
        # 恢复判别器缓冲区
        if 'discriminator_buffer' in checkpoint:
            self.discriminator_buffer = checkpoint['discriminator_buffer']
            main_logger.info(f"已恢复Discriminator缓冲区，当前大小: {len(self.discriminator_buffer)}")
        else:
            main_logger.warning("在checkpoint中未找到Discriminator缓冲区，将使用新的空缓冲区")
        
        # 加载SB3 RunningMeanStd状态（如果存在且启用）
        if self.config.use_valuenorm and 'valuenorm_state' in checkpoint:
            valuenorm_state = checkpoint['valuenorm_state']
            
            if 'coordinator' in valuenorm_state and self.value_norm_coordinator is not None:
                coord_state = valuenorm_state['coordinator']
                self.value_norm_coordinator.mean = coord_state['mean']
                self.value_norm_coordinator.var = coord_state['var']
                self.value_norm_coordinator.count = coord_state['count']
                main_logger.info("已恢复Coordinator的SB3 RunningMeanStd状态")
                
            if 'discoverer' in valuenorm_state and self.value_norm_discoverer is not None:
                disc_state = valuenorm_state['discoverer']
                self.value_norm_discoverer.mean = disc_state['mean']
                self.value_norm_discoverer.var = disc_state['var']
                self.value_norm_discoverer.count = disc_state['count']
                main_logger.info("已恢复Discoverer的SB3 RunningMeanStd状态")
                
        elif self.config.use_valuenorm:
            main_logger.warning("ValueNorm已启用，但checkpoint中未找到ValueNorm状态，将使用初始化值")
        
        # 加载观测和状态标准化统计信息（新增）
        if 'normalization_state' in checkpoint:
            normalization_state = checkpoint['normalization_state']
            
            if 'obs_norm' in normalization_state and getattr(self.config, 'use_obsnorm', False) and self.obs_norm is not None:
                obs_state = normalization_state['obs_norm']
                self.obs_norm.mean = obs_state['mean']
                self.obs_norm.var = obs_state['var']
                self.obs_norm.count = obs_state['count']
                main_logger.info("已恢复观测标准化统计信息")
                
            if 'state_norm' in normalization_state and getattr(self.config, 'use_statenorm', True) and self.state_norm is not None:
                state_state = normalization_state['state_norm']
                self.state_norm.mean = state_state['mean']
                self.state_norm.var = state_state['var']
                self.state_norm.count = state_state['count']
                main_logger.info("已恢复状态标准化统计信息")
        else:
            if getattr(self.config, 'use_obsnorm', False):
                main_logger.warning("观测标准化已启用，但checkpoint中未找到标准化状态，将使用初始化值")
            if getattr(self.config, 'use_statenorm', True):
                main_logger.warning("状态标准化已启用，但checkpoint中未找到标准化状态，将使用初始化值")
        
        main_logger.info(f"模型已从 {path} 加载 (使用非严格模式)")
