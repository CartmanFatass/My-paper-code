import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torch.optim import Adam
from torch.distributions import Categorical
import time
import os
from collections import deque
from torch.utils.tensorboard import SummaryWriter

# 确保在多进程环境中使用安全的matplotlib后端
import matplotlib
if matplotlib.get_backend() != 'Agg':
    matplotlib.use('Agg')

# 导入SB3的RunningMeanStd
from stable_baselines3.common.running_mean_std import RunningMeanStd

from logger import main_logger
from hmasd.networks import SkillCoordinator, SkillDiscoverer, TeamDiscriminator, IndividualDiscriminator
from hmasd.utils import ReplayBuffer, StateSkillDataset, compute_gae, compute_ppo_loss, one_hot


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
        
        # 确保环境维度已设置
        assert config.state_dim is not None, "必须先设置state_dim"
        assert config.obs_dim is not None, "必须先设置obs_dim"
        
        # 初始化TensorBoard
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.writer = SummaryWriter(log_dir)
        main_logger.debug(f"HMASDAgent.__init__: SummaryWriter created: {self.writer}")
        self.global_step = 0
        
        # 创建网络
        self.skill_coordinator = SkillCoordinator(config).to(self.device)
        self.skill_discoverer = SkillDiscoverer(config, logger=main_logger).to(self.device) # Pass logger
        self.team_discriminator = TeamDiscriminator(config).to(self.device)
        self.individual_discriminator = IndividualDiscriminator(config).to(self.device)
        
        # 创建优化器
        self.coordinator_optimizer = Adam(
            self.skill_coordinator.parameters(),
            lr=config.lr_coordinator,
            weight_decay=config.weight_decay
        )
        self.discoverer_optimizer = Adam(
            self.skill_discoverer.parameters(),
            lr=config.lr_discoverer,
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
                self.discoverer_scheduler = LinearLR(
                    self.discoverer_optimizer,
                    start_factor=1.0,
                    end_factor=config.discoverer_lr_decay_factor, 
                    total_iters=config.lr_decay_steps
                )
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
                self.discoverer_scheduler = CosineAnnealingLR(
                    self.discoverer_optimizer, T_max=config.lr_decay_steps
                )
                self.discriminator_scheduler = CosineAnnealingLR(
                    self.discriminator_optimizer, T_max=config.lr_decay_steps
                )
            
            main_logger.info(f"已启用学习率衰减: {config.lr_decay_schedule}, 衰减步数: {config.lr_decay_steps}")
        else:
            self.coordinator_scheduler = None
            self.discoverer_scheduler = None  
            self.discriminator_scheduler = None
            main_logger.info("未启用学习率衰减")
        
        # 创建经验回放缓冲区
        # 训练脚本应已通过调用 config.calculate_and_set_buffer_sizes() 设置了这些值
        # 使用断言确保配置已正确设置，避免使用不明确的备用值
        assert hasattr(config, 'high_level_buffer_size') and config.high_level_buffer_size is not None, \
            "config.high_level_buffer_size 未设置, 请确保在创建Agent前调用了config.update_env_dims()"
        assert hasattr(config, 'low_level_buffer_size') and config.low_level_buffer_size is not None, \
            "config.low_level_buffer_size 未设置, 请确保在创建Agent前调用了config.update_env_dims()"

        main_logger.info(f"初始化 Replay Buffers: High-level size={config.high_level_buffer_size}, Low-level size={config.low_level_buffer_size}")

        self.high_level_buffer = ReplayBuffer(config.high_level_buffer_size)
        self.high_level_buffer_with_logprobs = []  # 新增：高层经验缓冲区（带log probabilities）
        self.low_level_buffer = ReplayBuffer(config.low_level_buffer_size)
        self.state_skill_dataset = StateSkillDataset(config.low_level_buffer_size) # 判别器数据集与低层buffer大小保持一致
        
        # 其他初始化
        self.current_team_skill = None  # 当前团队技能 (保留用于单环境兼容性)
        self.current_agent_skills = None  # 当前个体技能列表 (保留用于单环境兼容性)
        self.skill_change_timer = 0  # 技能更换计时器 (保留用于单环境兼容性)
        self.current_high_level_reward_sum = 0.0 # 当前技能周期的累积奖励
        self.env_reward_sums = {}  # 用于存储每个环境ID的累积奖励，用于并行训练
        self.env_timers = {}  # 用于存储每个环境ID的技能计时器，用于并行训练
        
        # 新增：环境特定的状态跟踪
        self.env_team_skills = {}  # 各环境的当前团队技能
        self.env_agent_skills = {}  # 各环境的当前个体技能列表
        self.env_log_probs = {}  # 各环境的log probabilities
        self.env_hidden_states = {}  # 各环境的GRU隐藏状态
        
        # 动态初始化环境状态字典 - 将在实际使用时按需初始化
        # 不再预分配固定数量的环境槽位
        self.accumulated_rewards = 0.0  # 用于测试的累积奖励属性
        self.episode_rewards = []  # 记录每个完整episode的奖励

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
        self.high_level_samples_by_reason = {'技能周期结束': 0, '环境终止': 0}  # 收集原因统计
        
        # 高层经验收集增强
        self.env_last_contribution = {}          # 跟踪每个环境上次贡献高层样本的时间步
        self.force_high_level_collection = {}    # 强制采集标志，用于确保所有环境都能贡献样本
        self.env_reward_thresholds = {}          # 环境特定的奖励阈值
        
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
        
        # 初始化Value Normalization - 使用SB3的RunningMeanStd
        if config.use_valuenorm:
            self.value_norm_coordinator = RunningMeanStd(shape=())
            self.value_norm_discoverer = RunningMeanStd(shape=())
            main_logger.info("已启用Value Normalization (使用SB3 RunningMeanStd)")
        else:
            self.value_norm_coordinator = None
            self.value_norm_discoverer = None
            main_logger.info("未启用Value Normalization")
    
    def _normalize_values(self, values, running_mean_std):
        """使用SB3的RunningMeanStd进行标准化"""
        if not self.config.use_valuenorm:
            return values
        
        # 转换为numpy进行标准化
        values_np = values.detach().cpu().numpy()
        normalized_np = (values_np - running_mean_std.mean) / np.sqrt(running_mean_std.var + 1e-8)
        
        # 裁剪并转回tensor
        normalized_np = np.clip(normalized_np, -5.0, 5.0)
        return torch.tensor(normalized_np, dtype=values.dtype, device=values.device)

    def _denormalize_values(self, values, running_mean_std):
        """使用SB3的RunningMeanStd进行反标准化"""
        if not self.config.use_valuenorm:
            return values
        
        values_np = values.detach().cpu().numpy()
        denormalized_np = values_np * np.sqrt(running_mean_std.var + 1e-8) + running_mean_std.mean
        return torch.tensor(denormalized_np, dtype=values.dtype, device=values.device)

    def clear_buffers(self):
        """清空经验缓冲区（用于严格on-policy训练）"""
        main_logger.info("清空经验缓冲区")
        self.high_level_buffer.clear()
        self.high_level_buffer_with_logprobs = []
        self.low_level_buffer.clear()
        # 注意：不清空 state_skill_dataset，因为它用于判别器训练
        
        # 重置计数器和累积值
        self.current_high_level_reward_sum = 0.0
        self.accumulated_rewards = 0.0
        self.skill_change_timer = 0
        self.high_level_buffer_warning_counter = 0
        self.last_high_level_buffer_size = 0
        
        # 重置环境特定的奖励累积字典和计时器字典
        self.env_reward_sums = {}
        self.env_timers = {}
        
        # 重置奖励组成部分的累积值
        self.cumulative_env_reward = 0.0
        self.cumulative_team_disc_reward = 0.0
        self.cumulative_ind_disc_reward = 0.0
        self.reward_component_counts = 0
        
        # 重置技能使用计数
        self.episode_team_skill_counts = {}
        self.episode_agent_skill_counts = []
        
        # 注意：不重置Value Normalization统计量
        # ValueNorm的running_mean和running_std应该在整个训练过程中累积
        # 这符合MAPPO的标准实现，确保价值函数标准化的稳定性
        # 只有在模型初始化或显式要求时才重置ValueNorm统计量
        if self.config.use_valuenorm:
            main_logger.debug("保持Value Normalization统计量不变，继续累积训练数据")
    
    def select_action(self, observations, agent_skills=None, deterministic=False, env_id=0):
        """
        为所有智能体选择动作
        
        参数:
            observations: 所有智能体的观测 [n_agents, obs_dim]
            agent_skills: 所有智能体的技能 [n_agents]，如果为None则使用当前技能
            deterministic: 是否使用确定性策略
            env_id: 环境ID，用于多环境并行训练
            
        返回:
            actions: 所有智能体的动作 [n_agents, action_dim]
            action_logprobs: 所有智能体的动作对数概率 [n_agents]
        """
        if agent_skills is None:
            agent_skills = self.env_agent_skills.get(env_id, self.current_agent_skills)
            
        n_agents = observations.shape[0]
        actions = torch.zeros((n_agents, self.config.action_dim), device=self.device)
        action_logprobs = torch.zeros(n_agents, device=self.device)
        
        # 初始化或获取环境特定的GRU隐藏状态
        if env_id not in self.env_hidden_states or self.env_hidden_states[env_id] is None:
            self.skill_discoverer.init_hidden(batch_size=1)
            self.env_hidden_states[env_id] = self.skill_discoverer.actor_hidden
        else:
            self.skill_discoverer.actor_hidden = self.env_hidden_states[env_id]
        
        with torch.no_grad():
            for i in range(n_agents):
                obs = torch.FloatTensor(observations[i]).unsqueeze(0).to(self.device)
                skill = torch.tensor(agent_skills[i], device=self.device)
                
                action, action_logprob, _ = self.skill_discoverer(obs, skill, deterministic)
                
                actions[i] = action.squeeze(0)
                action_logprobs[i] = action_logprob.squeeze(0)
        
        # 保存更新后的GRU隐藏状态
        self.env_hidden_states[env_id] = self.skill_discoverer.actor_hidden
        
        return actions.cpu().numpy(), action_logprobs.cpu().numpy()
    
    def reset_value_norm(self):
        """显式重置Value Normalization统计量"""
        if self.config.use_valuenorm:
            if self.value_norm_coordinator is not None:
                self.value_norm_coordinator.running_mean.zero_()
                self.value_norm_coordinator.running_std.fill_(1.0)
                self.value_norm_coordinator.count = 0
                main_logger.info("已重置Coordinator的Value Normalization统计量")
            if self.value_norm_discoverer is not None:
                self.value_norm_discoverer.running_mean.zero_()
                self.value_norm_discoverer.running_std.fill_(1.0)
                self.value_norm_discoverer.count = 0
                main_logger.info("已重置Discoverer的Value Normalization统计量")
        else:
            main_logger.warning("Value Normalization未启用，无法重置")
    
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
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        obs_tensor = torch.FloatTensor(observations).unsqueeze(0).to(self.device)
        
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
        
        return team_skill.item(), agent_skills.squeeze(0).cpu().numpy(), log_probs
    
    def step(self, state, observations, ep_t, deterministic=False, env_id=0):
        """
        执行一个环境步骤
        
        参数:
            state: 全局状态 [state_dim]
            observations: 所有智能体的观测 [n_agents, obs_dim]
            ep_t: 当前episode中的时间步
            deterministic: 是否使用确定性策略（用于评估）
            env_id: 环境ID，用于多环境并行训练
            
        返回:
            actions: 所有智能体的动作 [n_agents, action_dim]
            info: 额外信息，如当前技能
        """
        # 启用自动求导异常检测，帮助查找梯度计算失败的操作
        #torch.autograd.set_detect_anomaly(True)
        
        # 确保环境ID已初始化
        if env_id not in self.env_timers:
            self.env_reward_sums[env_id] = 0.0
            self.env_timers[env_id] = 0
            self.env_team_skills[env_id] = None
            self.env_agent_skills[env_id] = None
            self.env_log_probs[env_id] = None
            self.env_hidden_states[env_id] = None
            main_logger.debug(f"初始化环境 {env_id} 的状态")

        # 获取或初始化环境特定的状态
        current_team_skill = self.env_team_skills.get(env_id, self.current_team_skill)
        current_agent_skills = self.env_agent_skills.get(env_id, self.current_agent_skills)
        env_timer = self.env_timers.get(env_id, 0)
        
        # 判断是否需要重新分配技能
        main_logger.debug(f"step: env_id={env_id}, ep_t={ep_t}, k={self.config.k}, ep_t % k = {ep_t % self.config.k}, current_team_skill={current_team_skill}")
        if ep_t % self.config.k == 0 or current_team_skill is None:
            # 重置环境特定的累积奖励
            if env_id not in self.env_reward_sums:
                self.env_reward_sums[env_id] = 0.0
            else:
                self.env_reward_sums[env_id] = 0.0
                
            # 分配新技能
            team_skill, agent_skills, log_probs = self.assign_skills(state, observations, deterministic)
            
            # 更新环境特定的状态
            self.env_team_skills[env_id] = team_skill
            self.env_agent_skills[env_id] = agent_skills
            self.env_log_probs[env_id] = log_probs
            self.env_timers[env_id] = 0
            
            # 同时更新全局状态（用于兼容性）
            if env_id == 0:  # 只有环境0更新全局状态
                self.current_team_skill = team_skill
                self.current_agent_skills = agent_skills
                self.current_log_probs = log_probs
                self.skill_change_timer = 0
                self.current_high_level_reward_sum = 0.0
                self.accumulated_rewards = 0.0
            
            skill_changed = True
            main_logger.debug(f"环境{env_id}技能已更新: team_skill={team_skill}, timer重置为0")

            # 更新技能使用计数（只有环境0更新全局计数）
            if env_id == 0:
                # 初始化 agent skill counts 列表（如果尚未初始化或智能体数量已更改）
                if not self.episode_agent_skill_counts or len(self.episode_agent_skill_counts) != len(agent_skills):
                    self.episode_agent_skill_counts = [{} for _ in range(len(agent_skills))]

                # 记录团队技能
                self.episode_team_skill_counts[team_skill] = self.episode_team_skill_counts.get(team_skill, 0) + 1
                # 记录个体技能
                for i, agent_skill in enumerate(agent_skills):
                    self.episode_agent_skill_counts[i][agent_skill] = self.episode_agent_skill_counts[i].get(agent_skill, 0) + 1
        else:
            self.env_timers[env_id] += 1
            # 同时更新全局计时器（用于兼容性）
            if env_id == 0:
                self.skill_change_timer += 1
            skill_changed = False
            main_logger.debug(f"环境{env_id}技能未更新: timer增加到{self.env_timers[env_id]}")
            
        # 选择动作，使用环境特定的技能
        actions, action_logprobs = self.select_action(observations, self.env_agent_skills[env_id], deterministic, env_id)
        
        info = {
            'team_skill': self.env_team_skills[env_id],
            'agent_skills': self.env_agent_skills[env_id],
            'action_logprobs': action_logprobs,
            'skill_changed': skill_changed,
            'skill_timer': self.env_timers[env_id],
            'log_probs': self.env_log_probs[env_id],
            'env_id': env_id
        }
        
        return actions, info
    

    
    def store_transition(self, state, next_state, observations, next_observations, 
                         actions, rewards, dones, team_skill, agent_skills, action_logprobs, log_probs=None, 
                         skill_timer_for_env=None, env_id=0, potential_reward=0.0):
        """
        存储环境交互经验
        
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
            potential_reward: 基于信念地图的探索奖励，用于低层策略
        """
        n_agents = len(agent_skills)
        state_tensor = torch.FloatTensor(state).to(self.device)
        next_state_tensor = torch.FloatTensor(next_state).to(self.device)
        team_skill_tensor = torch.tensor(team_skill, device=self.device)
        
        # 累加当前步的团队奖励
        # 确保rewards是数值类型
        current_reward = rewards if isinstance(rewards, (int, float)) else rewards.item()
        
        # 使用环境ID为键创建或更新环境特定的奖励累积
        if env_id not in self.env_reward_sums:
            self.env_reward_sums[env_id] = 0.0
        
        self.env_reward_sums[env_id] += current_reward
        
        # 记录高层奖励累积情况（增加total_step和skill_timer信息）
        main_logger.debug(f"store_transition: 环境ID={env_id}, step={self.global_step}, skill_timer={skill_timer_for_env}, "
                          f"当前步奖励={current_reward:.4f}, 此环境累积高层奖励={self.env_reward_sums[env_id]:.4f}")
        
        # 计算团队技能判别器输出
        with torch.no_grad():
            team_disc_logits = self.team_discriminator(next_state_tensor.unsqueeze(0))
            team_disc_log_probs = F.log_softmax(team_disc_logits, dim=-1)
            team_skill_log_prob = team_disc_log_probs[0, team_skill]
        
        # 为每个智能体存储低层经验
        for i in range(n_agents):
            obs = torch.FloatTensor(observations[i]).to(self.device)
            next_obs = torch.FloatTensor(next_observations[i]).to(self.device)
            action = torch.FloatTensor(actions[i]).to(self.device)
            done = dones[i] if isinstance(dones, list) else dones
            
            # 计算个体技能判别器输出
            with torch.no_grad():
                agent_disc_logits = self.individual_discriminator(
                    next_obs.unsqueeze(0), 
                    team_skill_tensor
                )
                agent_disc_log_probs = F.log_softmax(agent_disc_logits, dim=-1)
                agent_skill_log_prob = agent_disc_log_probs[0, agent_skills[i]]
                
            # 计算动态权重（权重退火机制）
            if self.use_reward_annealing:
                # 计算退火进度 (0.0 到 1.0)
                progress = min(self.global_step / self.anneal_steps, 1.0)
                
                # 根据退火计划计算当前权重
                if self.anneal_schedule == 'cosine':
                    # 余弦退火：前期变化慢，后期变化快
                    progress_adjusted = 0.5 * (1 - np.cos(np.pi * progress))
                else:
                    # 线性退火
                    progress_adjusted = progress
                
                # 线性插值计算当前权重倍数
                w_intrinsic_current = self.w_intrinsic_initial + (self.w_intrinsic_final - self.w_intrinsic_initial) * progress_adjusted
                w_extrinsic_current = self.w_extrinsic_initial + (self.w_extrinsic_final - self.w_extrinsic_initial) * progress_adjusted
                
                # 应用动态权重到各个奖励组件
                env_reward_component = self.config.lambda_e * w_extrinsic_current * current_reward
                team_disc_component = self.config.lambda_D * w_intrinsic_current * team_skill_log_prob.item()
                ind_disc_component = self.config.lambda_d * w_intrinsic_current * agent_skill_log_prob.item()
                
                # 记录当前权重到日志（每1000步记录一次以避免日志过多）
                if self.global_step % 1000 == 0:
                    main_logger.debug(f"权重退火进度: {progress:.3f} ({self.global_step}/{self.anneal_steps}), "
                                   f"内在权重倍数: {w_intrinsic_current:.3f}, "
                                   f"外部权重倍数: {w_extrinsic_current:.3f}")
            else:
                # 使用固定权重（原始方式）
                env_reward_component = self.config.lambda_e * current_reward
                team_disc_component = self.config.lambda_D * team_skill_log_prob.item()
                ind_disc_component = self.config.lambda_d * agent_skill_log_prob.item()
                w_intrinsic_current = 1.0
                w_extrinsic_current = 1.0
            
            # 添加基于信念地图的探索奖励到内在奖励中
            # 这个探索奖励主要用于指导低层策略的探索行为
            exploration_component = self.config.potential_reward_weight * potential_reward if hasattr(self.config, 'potential_reward_weight') else 0.0
            
            intrinsic_reward = env_reward_component + team_disc_component + ind_disc_component + exploration_component
            
            # 新增：对总内在奖励进行裁剪，以稳定训练
            # 这防止了因奖励值过大导致的损失爆炸问题
            intrinsic_reward = np.clip(intrinsic_reward, -10.0, 10.0)
            
            # 存储低层经验
            low_level_experience = (
                state_tensor,                           # 全局状态s
                team_skill_tensor,                      # 团队技能Z
                obs,                                    # 智能体观测o_i
                torch.tensor(agent_skills[i], device=self.device),  # 个体技能z_i
                action,                                 # 动作a_i
                torch.tensor(intrinsic_reward, device=self.device),  # 总内在奖励r_i
                torch.tensor(done, dtype=torch.float, device=self.device),  # 是否结束
                torch.tensor(action_logprobs[i], device=self.device),  # 动作对数概率
                torch.tensor(env_reward_component, device=self.device), # 环境奖励部分
                torch.tensor(team_disc_component, device=self.device),  # 团队判别器部分
                torch.tensor(ind_disc_component, device=self.device)   # 个体判别器部分
            )
            self.low_level_buffer.push(low_level_experience)
            
        # 存储技能判别器训练数据
        observations_tensor = torch.FloatTensor(next_observations).to(self.device)
        agent_skills_tensor = torch.tensor(agent_skills, device=self.device)
        self.state_skill_dataset.push(
            next_state_tensor,
            team_skill_tensor,
            observations_tensor,
            agent_skills_tensor
        )
        
        # 获取或初始化当前环境的技能计时器
        if env_id not in self.env_timers:
            self.env_timers[env_id] = 0
        
        # 优先使用传入的技能计时器值，如果没有则使用环境专用计时器
        skill_timer = skill_timer_for_env if skill_timer_for_env is not None else self.env_timers[env_id]
        
        # 记录当前技能计时器状态
        main_logger.debug(f"store_transition: 环境ID={env_id}, skill_timer={skill_timer}, k={self.config.k}, 条件判断={skill_timer == self.config.k - 1}")
        
        # 获取或初始化环境的最后贡献时间
        if env_id not in self.env_last_contribution:
            self.env_last_contribution[env_id] = 0
        
        # 获取或初始化环境特定的奖励阈值
        if env_id not in self.env_reward_thresholds:
            self.env_reward_thresholds[env_id] = 0.0  # 将默认阈值设为0，确保始终能存储高层经验
        
        # 判断该环境是否需要强制收集高层样本
        force_collection = self.force_high_level_collection.get(env_id, False)
        
        # 简化逻辑：取消所有奖励阈值，确保始终收集高层样本
        self.env_reward_thresholds[env_id] = 0.0
        
        # 对长时间未贡献的环境强制收集
        steps_since_contribution = self.global_step - self.env_last_contribution.get(env_id, 0)
        if steps_since_contribution > 500:  # 降低检查间隔至500步
            self.force_high_level_collection[env_id] = True
            if steps_since_contribution % 500 == 0:  # 避免日志过多
                main_logger.info(f"环境ID={env_id}已{steps_since_contribution}步未贡献高层样本，将强制收集")
        
        # 存储高层经验（每k步一次或者环境终止时）
        # 简化存储条件：每当达到k-1步或环境终止或强制收集时，都存储高层经验
        should_store_high_level = (skill_timer == self.config.k - 1) or dones or force_collection
        
        if should_store_high_level:
            # 获取当前环境的累积奖励
            env_accumulated_reward = self.env_reward_sums.get(env_id, 0.0)
            
            # 记录高层经验存储检查信息
            reason = "未知原因"
            if skill_timer == self.config.k - 1:
                reason = "技能周期结束"
                main_logger.debug(f"环境ID={env_id}技能周期结束: 累积奖励={env_accumulated_reward:.4f}, "
                               f"离上次贡献={steps_since_contribution}步, k={self.config.k}")
            elif dones:
                reason = "环境终止"
                # 记录episode结束信息，包含环境ID和详细信息
                episode_info = {
                    'env_id': env_id,
                    'total_reward': env_accumulated_reward,
                    'skill_timer': skill_timer,
                    'team_skill': team_skill,
                    'agent_skills': agent_skills
                }
                
                # 从环境信息中提取额外的episode统计信息
                if hasattr(next_state, '__len__') and len(next_state) > 0:
                    episode_info['final_state_norm'] = float(torch.norm(torch.tensor(next_state)).item())
                
                # 记录episode结束的详细信息
                main_logger.info(f"Episode结束 - 环境ID: {env_id}, "
                               f"总奖励: {env_accumulated_reward:.4f}, "
                               f"技能计时器: {skill_timer}, "
                               f"团队技能: {team_skill}, "
                               f"个体技能: {agent_skills}")
            elif force_collection:
                reason = "强制收集"
                main_logger.info(f"环境ID={env_id}强制收集: 累积奖励={env_accumulated_reward:.4f}, 技能计时器={skill_timer}")
            # 创建高层经验元组
            high_level_experience = (
                state_tensor,                  # 全局状态s
                team_skill_tensor,             # 团队技能Z
                observations_tensor,           # 所有智能体观测o
                agent_skills_tensor,           # 所有个体技能z
                torch.tensor(env_accumulated_reward, device=self.device) # 存储该环境的k步累积奖励
            )
            
            # 存储高层经验
            self.high_level_buffer.push(high_level_experience)
        
            # 无论buffer长度是否变化，都认为成功添加了一个样本
            # 避免在buffer满时因为长度不变而误判为未添加样本
            samples_added = 1
            self.high_level_samples_total += samples_added
            # 记录环境贡献
            self.high_level_samples_by_env[env_id] = self.high_level_samples_by_env.get(env_id, 0) + 1
            # 记录原因统计
            self.high_level_samples_by_reason[reason] = self.high_level_samples_by_reason.get(reason, 0) + 1
            
            # 更新环境最后贡献时间
            self.env_last_contribution[env_id] = self.global_step
            
            # 重置强制收集标志
            if force_collection:
                self.force_high_level_collection[env_id] = False
            
            # 每收集5个样本记录一次统计信息（从10改为5，增加反馈频率）
            if self.high_level_samples_total % 5 == 0:
                main_logger.debug(f"高层经验统计 - 总样本: {self.high_level_samples_total}, 环境贡献: {self.high_level_samples_by_env}, 原因统计: {self.high_level_samples_by_reason}")
                
                # 记录到TensorBoard
                if hasattr(self, 'writer'):
                    self.writer.add_scalar('Buffer/high_level_samples_total', self.high_level_samples_total, self.global_step)
                    # 记录各环境的样本贡献比例
                    for e_id, count in self.high_level_samples_by_env.items():
                        self.writer.add_scalar(f'Buffer/env_{e_id}_contribution', count, self.global_step)
        
            # 增加日志以便跟踪高层经验添加状态
            current_buffer_size = len(self.high_level_buffer)
            main_logger.debug(f"高层经验添加状态：环境ID={env_id}, step={self.global_step}, "
                           f"当前缓冲区大小: {current_buffer_size}, 此环境累积奖励: {env_accumulated_reward:.4f}, "
                           f"原因：{reason}")
            
            # 将带有log probabilities的经验存储到专用缓冲区
            if log_probs is not None:
                self.high_level_buffer_with_logprobs.append({
                    'state': state_tensor.clone(),
                    'team_skill': team_skill,
                    'observations': observations_tensor.clone(),
                    'agent_skills': agent_skills_tensor.clone(),
                    'reward': env_accumulated_reward,  # 使用环境特定的累积奖励
                    'team_log_prob': log_probs['team_log_prob'],
                    'agent_log_probs': log_probs['agent_log_probs']
                })
                
                # 保持缓冲区大小不超过其配置的大小
                buffer_capacity = self.config.high_level_buffer_size
                if len(self.high_level_buffer_with_logprobs) > buffer_capacity:
                    self.high_level_buffer_with_logprobs = self.high_level_buffer_with_logprobs[-buffer_capacity:]
            
            # 重置该环境的奖励累积
            self.env_reward_sums[env_id] = 0.0
            
            # 重置该环境的技能计时器
            self.env_timers[env_id] = 0
            
        # else:
        #     # 如果不到技能周期结束时间，增加该环境的技能计时器，但确保不超过k-1
        #     # if self.env_timers[env_id] < self.config.k - 1:
        #     #     self.env_timers[env_id] += 1
    
    def update_coordinator(self):
        """更新高层技能协调器网络"""
        # 记录高层缓冲区状态
        buffer_len = len(self.high_level_buffer)
        required_batch_size = self.config.high_level_batch_size
        main_logger.debug(f"高层缓冲区状态: {buffer_len}/{required_batch_size} (当前/所需)")
        
        if buffer_len < required_batch_size:
            # 如果缓冲区不足，使用计数器减少警告日志频率
            # 只有当缓冲区大小变化或者每10次更新才记录一次警告
            if buffer_len != self.last_high_level_buffer_size or self.high_level_buffer_warning_counter % 10 == 0:
                main_logger.warning(f"高层缓冲区样本不足，需要{required_batch_size}个样本，但只有{buffer_len}个。跳过更新。")
            else:
                main_logger.debug(f"高层缓冲区样本不足，需要{required_batch_size}个样本，但只有{buffer_len}个。跳过更新。")
            
            # 更新计数器和上次缓冲区大小
            self.high_level_buffer_warning_counter += 1
            self.last_high_level_buffer_size = buffer_len
            
            # 保持与函数正常返回值相同数量的元素
            return 0, 0, 0, 0, 0, 0, 0, 0, 0
        
        # 缓冲区已满，继续更新
        main_logger.debug(f"高层缓冲区满足更新条件，从{buffer_len}个样本中采样{required_batch_size}个")
            
        # 从缓冲区采样数据
        batch = self.high_level_buffer.sample(self.config.high_level_batch_size)
        states, team_skills, observations, agent_skills, rewards = zip(*batch)
        
        states = torch.stack(states)
        team_skills = torch.stack(team_skills)
        observations = torch.stack(observations)
        agent_skills = torch.stack(agent_skills)
        rewards = torch.stack(rewards) # rewards现在是累积的k步奖励r_h
        
        # 记录高层奖励的统计信息
        reward_mean = rewards.mean().item()
        reward_std = rewards.std().item()
        reward_min = rewards.min().item()
        reward_max = rewards.max().item()
        main_logger.debug(f"高层奖励统计: 均值={reward_mean:.4f}, 标准差={reward_std:.4f}, 最小值={reward_min:.4f}, 最大值={reward_max:.4f}")
        
        # 获取当前状态价值
        state_values, agent_values, cd_loss_critic = self.skill_coordinator.get_value(states, observations)
        
        # 由于我们假设每个高层经验都是一个k步序列的端点，
        # 所以我们可以假设下一状态价值为0（或者可以从新的状态计算）
        next_values = torch.zeros_like(state_values)
        
        # 【关键修复】在计算GAE之前，对价值网络输出进行反归一化
        # 这确保了用于GAE计算的价值与原始尺度的奖励在同一数值尺度上
        if self.config.use_valuenorm and self.value_norm_coordinator is not None:
            denormalized_state_values = self._denormalize_values(state_values, self.value_norm_coordinator)
            denormalized_next_values = self._denormalize_values(next_values, self.value_norm_coordinator)
            main_logger.debug(f"Coordinator GAE: 使用反归一化后的价值进行GAE计算")
        else:
            denormalized_state_values = state_values
            denormalized_next_values = next_values
        
        # 在计算GAE之前详细记录奖励和价值的统计信息
        rewards_mean = rewards.mean().item()
        rewards_std = rewards.std().item()
        rewards_min = rewards.min().item()
        rewards_max = rewards.max().item()
        denorm_values_mean = denormalized_state_values.mean().item()
        denorm_values_std = denormalized_state_values.std().item()
        denorm_values_min = denormalized_state_values.min().item()
        denorm_values_max = denormalized_state_values.max().item()
        
        main_logger.debug(f"GAE输入统计:")
        main_logger.debug(f"  rewards: 均值={rewards_mean:.4f}, 标准差={rewards_std:.4f}, 最小值={rewards_min:.4f}, 最大值={rewards_max:.4f}")
        main_logger.debug(f"  denormalized_state_values: 均值={denorm_values_mean:.4f}, 标准差={denorm_values_std:.4f}, 最小值={denorm_values_min:.4f}, 最大值={denorm_values_max:.4f}")
        
        # 检查是否有异常值
        rewards_has_nan = torch.isnan(rewards).any().item()
        rewards_has_inf = torch.isinf(rewards).any().item()
        values_has_nan = torch.isnan(denormalized_state_values).any().item()
        values_has_inf = torch.isinf(denormalized_state_values).any().item()
        
        if rewards_has_nan or rewards_has_inf:
            main_logger.error(f"奖励中存在NaN或Inf: NaN={rewards_has_nan}, Inf={rewards_has_inf}")
            # 尝试修复NaN/Inf值，以避免整个训练中断
            rewards = torch.nan_to_num(rewards, nan=0.0, posinf=10.0, neginf=-10.0)
            main_logger.info("已将奖励中的NaN/Inf值替换为有限值")
        
        if values_has_nan or values_has_inf:
            main_logger.error(f"反归一化状态价值中存在NaN或Inf: NaN={values_has_nan}, Inf={values_has_inf}")
            # 尝试修复NaN/Inf值
            denormalized_state_values = torch.nan_to_num(denormalized_state_values, nan=0.0, posinf=10.0, neginf=-10.0)
            denormalized_next_values = torch.nan_to_num(denormalized_next_values, nan=0.0, posinf=10.0, neginf=-10.0)
            main_logger.info("已将反归一化状态价值中的NaN/Inf值替换为有限值")
        
        # 计算GAE - 使用反归一化后的价值
        dones = torch.zeros_like(rewards)  # 假设高层经验不包含终止信息
        # 确保传递给compute_gae的values是1D，使用clone避免原地操作
        try:
            advantages, returns = compute_gae(rewards.clone(), denormalized_state_values.squeeze(-1).clone(), 
                                            denormalized_next_values.squeeze(-1).clone(), dones.clone(), 
                                            self.config.gamma, self.config.gae_lambda)
            # advantages 和 returns 都是 [batch_size]，分离计算图
            advantages = advantages.detach()
            returns = returns.detach()
            
            # The GAE returns (V_target) will be normalized later, right before the value loss calculation.
            # This avoids incorrect double normalization and ensures consistency.
            main_logger.debug(f"GAE returns (unnormalized): 均值={returns.mean().item():.4f}, 标准差={returns.std().item():.4f}")
            
            # 检查 advantages 和 returns 的统计信息
            adv_mean = advantages.mean().item()
            adv_std = advantages.std().item()
            adv_min = advantages.min().item()
            adv_max = advantages.max().item()
            ret_mean = returns.mean().item()
            ret_std = returns.std().item()
            ret_min = returns.min().item()
            ret_max = returns.max().item()
            
            main_logger.debug(f"GAE输出统计:")
            main_logger.debug(f"  Advantages: 均值={adv_mean:.4f}, 标准差={adv_std:.4f}, 最小值={adv_min:.4f}, 最大值={adv_max:.4f}")
            main_logger.debug(f"  Returns: 均值={ret_mean:.4f}, 标准差={ret_std:.4f}, 最小值={ret_min:.4f}, 最大值={ret_max:.4f}")
            
            # 检查GAE输出是否有异常值
            adv_has_nan = torch.isnan(advantages).any().item()
            adv_has_inf = torch.isinf(advantages).any().item()
            ret_has_nan = torch.isnan(returns).any().item()
            ret_has_inf = torch.isinf(returns).any().item()
            
            if adv_has_nan or adv_has_inf:
                main_logger.error(f"advantages中存在NaN或Inf: NaN={adv_has_nan}, Inf={adv_has_inf}")
                # 尝试修复NaN/Inf值
                advantages = torch.nan_to_num(advantages, nan=0.0, posinf=10.0, neginf=-10.0)
                main_logger.info("已将advantages中的NaN/Inf值替换为有限值")
            
            if ret_has_nan or ret_has_inf:
                main_logger.error(f"returns中存在NaN或Inf: NaN={ret_has_nan}, Inf={ret_has_inf}")
                # 尝试修复NaN/Inf值
                returns = torch.nan_to_num(returns, nan=0.0, posinf=10.0, neginf=-10.0)
                main_logger.info("已将returns中的NaN/Inf值替换为有限值")
                
            # 归一化advantages，有助于稳定训练
            if adv_std > 0:
                advantages = (advantages - adv_mean) / (adv_std + 1e-8)
                main_logger.debug("已对advantages进行归一化处理")
                
        except Exception as e:
            main_logger.error(f"计算GAE时发生错误: {e}")
            # 使用安全的默认值
            advantages = torch.zeros_like(rewards)
            returns = rewards.clone()  # 在缺乏更好选择的情况下，使用原始奖励作为返回值
            main_logger.info("由于GAE计算失败，使用安全的默认值作为替代")
        
        # 获取当前策略
        try:
            Z, z, Z_logits, z_logits, cd_loss, cmi_loss = self.skill_coordinator(states, observations)
            
            # 在使用logits前检查是否有异常值
            Z_logits_has_nan = torch.isnan(Z_logits).any().item()
            Z_logits_has_inf = torch.isinf(Z_logits).any().item()
            
            if Z_logits_has_nan or Z_logits_has_inf:
                main_logger.error(f"Z_logits中存在NaN或Inf: NaN={Z_logits_has_nan}, Inf={Z_logits_has_inf}")
                # 尝试修复NaN/Inf值
                Z_logits = torch.nan_to_num(Z_logits, nan=0.0, posinf=10.0, neginf=-10.0)
                main_logger.info("已将Z_logits中的NaN/Inf值替换为有限值")
            
            # 重新计算团队技能概率分布
            team_skills_detached = team_skills.clone().detach()  # 分离计算图，防止原地操作
            Z_dist = Categorical(logits=Z_logits)
            Z_log_probs = Z_dist.log_prob(team_skills_detached)
            Z_entropy = Z_dist.entropy().mean()
            
            # 记录团队技能熵的统计信息
            main_logger.debug(f"团队技能熵: {Z_entropy.item():.4f}")
            
        except Exception as e:
            main_logger.error(f"在计算策略分布时发生错误: {e}")
            # 使用安全的默认值
            batch_size = states.size(0)
            Z = torch.zeros(batch_size, dtype=torch.long, device=self.device)
            z = torch.zeros(batch_size, self.config.n_agents, dtype=torch.long, device=self.device)
            Z_logits = torch.zeros((batch_size, self.config.n_Z), device=self.device)
            z_logits = [torch.zeros((batch_size, self.config.n_z), device=self.device) for _ in range(self.config.n_agents)]
            Z_log_probs = torch.zeros(batch_size, device=self.device)
            Z_entropy = torch.tensor(0.0, device=self.device)
            main_logger.info("由于错误，使用安全的默认值进行计算")
        
        # 检查是否有带log probabilities的高层经验
        use_stored_logprobs = len(self.high_level_buffer_with_logprobs) >= self.config.high_level_batch_size
        
        try:
            # 计算高层策略损失
            if use_stored_logprobs:
                # 使用存储的log probabilities计算更准确的PPO ratio
                
                # 从带log probabilities的缓冲区中随机选择样本
                indices = torch.randperm(len(self.high_level_buffer_with_logprobs))[:self.config.high_level_batch_size]
                old_team_log_probs = [self.high_level_buffer_with_logprobs[i]['team_log_prob'] for i in indices]
                old_team_log_probs_tensor = torch.tensor(old_team_log_probs, device=self.device).detach()  # 使用detach()防止求导错误
                
                # 检查old_team_log_probs_tensor是否有异常值
                old_log_probs_has_nan = torch.isnan(old_team_log_probs_tensor).any().item()
                old_log_probs_has_inf = torch.isinf(old_team_log_probs_tensor).any().item()
                
                if old_log_probs_has_nan or old_log_probs_has_inf:
                    main_logger.error(f"old_team_log_probs_tensor中存在NaN或Inf: NaN={old_log_probs_has_nan}, Inf={old_log_probs_has_inf}")
                    # 尝试修复NaN/Inf值
                    old_team_log_probs_tensor = torch.nan_to_num(old_team_log_probs_tensor, nan=0.0, posinf=0.0, neginf=0.0)
                    main_logger.info("已将old_team_log_probs_tensor中的NaN/Inf值替换为0")
                
                # 记录log_probs的统计信息
                main_logger.debug(f"当前log_probs统计: 均值={Z_log_probs.mean().item():.4f}, 标准差={Z_log_probs.std().item():.4f}")
                main_logger.debug(f"历史log_probs统计: 均值={old_team_log_probs_tensor.mean().item():.4f}, 标准差={old_team_log_probs_tensor.std().item():.4f}")
                
                # 安全计算PPO ratio，避免数值上溢
                log_ratio = Z_log_probs - old_team_log_probs_tensor
                # 裁剪log_ratio以避免exp操作导致数值溢出
                log_ratio = torch.clamp(log_ratio, -10.0, 10.0)
                Z_ratio = torch.exp(log_ratio)
                
                # 记录ratio的统计信息
                ratio_mean = Z_ratio.mean().item()
                ratio_std = Z_ratio.std().item()
                ratio_min = Z_ratio.min().item()
                ratio_max = Z_ratio.max().item()
                main_logger.debug(f"PPO ratio统计: 均值={ratio_mean:.4f}, 标准差={ratio_std:.4f}, 最小值={ratio_min:.4f}, 最大值={ratio_max:.4f}")
                
                # 打印debug信息
                main_logger.debug(f"使用存储的log probabilities进行PPO更新，共有{len(self.high_level_buffer_with_logprobs)}个样本")
            else:
                # 如果没有存储log probabilities，则假设old_log_probs=0
                # 同样需要裁剪以避免数值溢出
                log_ratio = torch.clamp(Z_log_probs, -10.0, 10.0)
                Z_ratio = torch.exp(log_ratio)
                main_logger.warning("未使用存储的log probabilities，假设old_log_probs=0")
            
            # 检查ratio是否有异常值
            ratio_has_nan = torch.isnan(Z_ratio).any().item()
            ratio_has_inf = torch.isinf(Z_ratio).any().item()
            
            if ratio_has_nan or ratio_has_inf:
                main_logger.error(f"Z_ratio中存在NaN或Inf: NaN={ratio_has_nan}, Inf={ratio_has_inf}")
                # 尝试修复NaN/Inf值
                Z_ratio = torch.nan_to_num(Z_ratio, nan=1.0, posinf=2.0, neginf=0.5)
                main_logger.info("已将Z_ratio中的NaN/Inf值替换为有限值")
            
            # 计算带裁剪的目标函数
            Z_surr1 = Z_ratio * advantages
            Z_surr2 = torch.clamp(Z_ratio, 1.0 - self.config.clip_epsilon, 1.0 + self.config.clip_epsilon) * advantages
            Z_policy_loss = -torch.min(Z_surr1, Z_surr2).mean()
            
            # 检查损失是否有异常值
            if torch.isnan(Z_policy_loss).any().item() or torch.isinf(Z_policy_loss).any().item():
                main_logger.error(f"Z_policy_loss包含NaN或Inf值: {Z_policy_loss.item()}")
                # 使用一个安全的默认损失值
                Z_policy_loss = torch.tensor(0.1, device=self.device, requires_grad=True)
                main_logger.info("已将Z_policy_loss替换为安全的默认值0.1")
                
        except Exception as e:
            main_logger.error(f"计算高层策略损失时发生错误: {e}")
            # 使用安全的默认损失值
            Z_policy_loss = torch.tensor(0.1, device=self.device, requires_grad=True)
            main_logger.info("由于错误，使用安全的默认值0.1作为Z_policy_loss")
        
        try:
            # 计算高层价值损失
            state_values = state_values.float() # Shape [batch_size, 1]
            # returns 是 [batch_size], 需要 unsqueeze 匹配 state_values
            returns = returns.float().unsqueeze(-1) # Shape [batch_size, 1]
            
            # Correctly apply Value Normalization for the value loss calculation.
            if self.config.use_valuenorm and self.value_norm_coordinator is not None:
                # 1. 先用当前统计量标准化（确保网络输出和targets使用相同的标准化基准）
                normalized_state_values = self._normalize_values(state_values, self.value_norm_coordinator)
                normalized_returns = self._normalize_values(returns, self.value_norm_coordinator)
                
                # 2. 计算损失（使用一致的标准化基准）
                Z_value_loss = F.mse_loss(normalized_state_values, normalized_returns)
                
                # 3. 最后更新统计量（为下次使用做准备）
                self.value_norm_coordinator.update(returns.detach().cpu().numpy())
                
                main_logger.debug(f"Coordinator using ValueNorm: "
                                f"Normalized state_values mean={normalized_state_values.mean().item():.4f}, "
                                f"Normalized returns mean={normalized_returns.mean().item():.4f}")
            else:
                # Without ValueNorm, use raw values.
                Z_value_loss = F.mse_loss(state_values, returns)
            
            # 检查价值损失是否有异常值
            if torch.isnan(Z_value_loss).any().item() or torch.isinf(Z_value_loss).any().item():
                main_logger.error(f"Z_value_loss包含NaN或Inf值: {Z_value_loss.item()}")
                # 使用安全的默认损失值
                Z_value_loss = torch.tensor(0.1, device=self.device, requires_grad=True)
                main_logger.info("已将Z_value_loss替换为安全的默认值0.1")
            
        except Exception as e:
            main_logger.error(f"计算高层价值损失时发生错误: {e}")
            # 使用安全的默认损失值
            Z_value_loss = torch.tensor(0.1, device=self.device, requires_grad=True)
            main_logger.info("由于错误，使用安全的默认值0.1作为Z_value_loss")
        
        # 初始化智能体策略损失
        z_policy_losses = []
        z_entropy_losses = []
        z_value_losses = []
        
        # 处理每个智能体的个体技能损失
        # 使用实际智能体数量，由智能体技能形状决定，而不是配置中的n_agents
        n_agents_actual = agent_skills.shape[1]  # 从采样的agent_skills中获取实际智能体数量
        for i in range(n_agents_actual):
            agent_skills_i = agent_skills[:, i].clone().detach()  # 分离计算图，防止原地操作
            zi_dist = Categorical(logits=z_logits[i])
            zi_log_probs = zi_dist.log_prob(agent_skills_i)
            zi_entropy = zi_dist.entropy().mean()
            
            if use_stored_logprobs:
                # 使用存储的agent log probabilities
                old_agent_log_probs = [self.high_level_buffer_with_logprobs[j]['agent_log_probs'][i] 
                                      for j in indices 
                                      if i < len(self.high_level_buffer_with_logprobs[j]['agent_log_probs'])]
                
                if len(old_agent_log_probs) == len(zi_log_probs):
                    old_agent_log_probs_tensor = torch.tensor(old_agent_log_probs, device=self.device).detach()  # 使用detach()防止求导错误
                    zi_ratio = torch.exp(zi_log_probs - old_agent_log_probs_tensor)
                else:
                    # 如果长度不匹配（例如智能体数量变化），则退回到假设old_log_probs=0
                    zi_ratio = torch.exp(zi_log_probs)
            else:
                # 如果没有存储的log probabilities，则假设old_log_probs=0
                zi_ratio = torch.exp(zi_log_probs)
                
            zi_surr1 = zi_ratio * advantages
            zi_surr2 = torch.clamp(zi_ratio, 1.0 - self.config.clip_epsilon, 1.0 + self.config.clip_epsilon) * advantages
            zi_policy_loss = -torch.min(zi_surr1, zi_surr2).mean()
            
            z_policy_losses.append(zi_policy_loss)
            z_entropy_losses.append(zi_entropy)
            
            if i < len(agent_values):
                # 确保数据类型匹配
                agent_value = agent_values[i].float() # Shape [128, 1]
                # returns 已经是 [128, 1]
                returns_i = returns.float() 
                
                zi_value_loss = F.mse_loss(agent_value, returns_i)
                z_value_losses.append(zi_value_loss)
        
        # 合并所有智能体的损失
        z_policy_loss = torch.stack(z_policy_losses).mean()
        z_entropy = torch.stack(z_entropy_losses).mean()
        
        if z_value_losses:
            z_value_loss = torch.stack(z_value_losses).mean()
        else:
            z_value_loss = torch.tensor(0.0, device=self.device)
        
        try:
            # 总策略损失
            policy_loss = Z_policy_loss + z_policy_loss
            
            # 总价值损失
            value_loss = Z_value_loss + z_value_loss
            
            # 总熵损失
            entropy_loss = -(Z_entropy + z_entropy) * self.config.lambda_h
            
            # 总损失
            # 同时加上来自actor和critic路径的CD loss
            total_cd_loss = cd_loss + cd_loss_critic
            # 只有在使用OPT时才添加CD损失
            if self.config.use_opt:
                loss = policy_loss + self.config.value_loss_coef * value_loss + entropy_loss + self.config.lambda_cd * total_cd_loss
            else:
                loss = policy_loss + self.config.value_loss_coef * value_loss + entropy_loss
            
            # 检查总损失是否有异常值
            if torch.isnan(loss).any().item() or torch.isinf(loss).any().item():
                main_logger.error(f"总损失包含NaN或Inf值: {loss.item()}")
                # 分析损失组成部分
                main_logger.error(f"损失组成部分: policy_loss={policy_loss.item()}, value_loss={value_loss.item()}, entropy_loss={entropy_loss.item()}")
                
                # 尝试创建一个新的、安全的损失
                policy_loss_safe = torch.tensor(0.1, device=self.device, requires_grad=True)
                value_loss_safe = torch.tensor(0.1, device=self.device, requires_grad=True)
                entropy_loss_safe = torch.tensor(-0.1, device=self.device, requires_grad=True)
                loss = policy_loss_safe + self.config.value_loss_coef * value_loss_safe + entropy_loss_safe
                main_logger.info("已将总损失替换为安全的默认值")
            
            # 记录损失值
            main_logger.debug(f"损失统计: 总损失={loss.item():.6f}, 策略损失={policy_loss.item():.6f}, 价值损失={value_loss.item():.6f}, 熵损失={entropy_loss.item():.6f}")
            
            # 更新网络
            self.coordinator_optimizer.zero_grad()
            loss.backward()
            
        except Exception as e:
            main_logger.error(f"计算总损失时发生错误: {e}")
            # 创建一个新的、安全的损失
            loss = torch.tensor(0.3, device=self.device, requires_grad=True)
            policy_loss = torch.tensor(0.1, device=self.device)
            value_loss = torch.tensor(0.1, device=self.device)
            entropy_loss = torch.tensor(-0.1, device=self.device)
            
            main_logger.info("由于错误，使用安全的默认值作为损失")
            
            # 更新网络
            self.coordinator_optimizer.zero_grad()
            loss.backward()
        
        # 检查loss是否正确连接到计算图
        main_logger.debug(f"损失连接状态: requires_grad={loss.requires_grad}, grad_fn={loss.grad_fn}")
        
        # 检查coordinator参数是否正确设置requires_grad
        params_requiring_grad = 0
        for name, param in self.skill_coordinator.named_parameters():
            if param.requires_grad:
                params_requiring_grad += 1
                main_logger.debug(f"参数 {name} requires_grad=True")
        main_logger.debug(f"Coordinator中需要梯度的参数数量: {params_requiring_grad}")
        
        # 详细记录梯度信息
        params_with_grads = [p for p in self.skill_coordinator.parameters() if p.grad is not None]
        if params_with_grads:
            # 检查梯度是否包含NaN或Inf
            has_nan_grad = any(torch.isnan(p.grad).any().item() for p in params_with_grads)
            has_inf_grad = any(torch.isinf(p.grad).any().item() for p in params_with_grads)
            
            if has_nan_grad or has_inf_grad:
                main_logger.error(f"梯度中包含NaN或Inf值: NaN={has_nan_grad}, Inf={has_inf_grad}")
                # 尝试修复梯度中的NaN/Inf值
                for p in params_with_grads:
                    if torch.isnan(p.grad).any() or torch.isinf(p.grad).any():
                        p.grad.data = torch.nan_to_num(p.grad.data, nan=0.0, posinf=1.0, neginf=-1.0)
                main_logger.info("已将梯度中的NaN和Inf值替换为有限值")
            
            # 计算梯度的统计信息
            grad_norms = [torch.norm(p.grad.detach()).item() for p in params_with_grads]
            mean_norm = np.mean(grad_norms)
            max_norm = max(grad_norms)
            min_norm = min(grad_norms)
            std_norm = np.std(grad_norms)
            total_norm = torch.sqrt(sum(p.grad.detach().pow(2).sum() for p in params_with_grads)).item()
            
            main_logger.debug(f"梯度统计 (裁剪前): 总范数={total_norm:.6f}, 均值={mean_norm:.6f}, "
                             f"标准差={std_norm:.6f}, 最大={max_norm:.6f}, 最小={min_norm:.6f}")
            
            # 检查是否有较大梯度
            large_grad_threshold = 10.0
            large_grads = [(name, torch.norm(param.grad).item()) 
                           for name, param in self.skill_coordinator.named_parameters() 
                           if param.grad is not None and torch.norm(param.grad).item() > large_grad_threshold]
            
            if large_grads:
                main_logger.warning(f"检测到{len(large_grads)}个参数具有较大梯度 (>{large_grad_threshold}):")
                for name, norm in large_grads[:5]:  # 只显示前5个
                    main_logger.warning(f"  参数 {name}: 梯度范数 = {norm:.6f}")
                if len(large_grads) > 5:
                    main_logger.warning(f"  ... 还有{len(large_grads)-5}个参数有较大梯度")
            
            # 梯度裁剪
            try:
                torch.nn.utils.clip_grad_norm_(self.skill_coordinator.parameters(), self.config.max_grad_norm)
                
                # 记录裁剪后的梯度信息
                params_with_grads_after = [p for p in self.skill_coordinator.parameters() if p.grad is not None]
                if params_with_grads_after:
                    grad_norms_after = [torch.norm(p.grad.detach()).item() for p in params_with_grads_after]
                    mean_norm_after = np.mean(grad_norms_after)
                    max_norm_after = max(grad_norms_after)
                    min_norm_after = min(grad_norms_after)
                    std_norm_after = np.std(grad_norms_after)
                    total_norm_after = torch.sqrt(sum(p.grad.detach().pow(2).sum() for p in params_with_grads_after)).item()
                    
                    main_logger.debug(f"梯度统计 (裁剪后): 总范数={total_norm_after:.6f}, 均值={mean_norm_after:.6f}, "
                                     f"标准差={std_norm_after:.6f}, 最大={max_norm_after:.6f}, 最小={min_norm_after:.6f}")
            except Exception as e:
                main_logger.error(f"梯度裁剪失败: {e}")
                
        else:
            main_logger.warning("没有参数接收到梯度! 检查loss.backward()是否正确传播梯度。")
            
            # 详细检查每个参数的梯度状态
            grad_status = {}
            for name, param in self.skill_coordinator.named_parameters():
                if param.grad is None:
                    grad_status[name] = "None"
                else:
                    norm = torch.norm(param.grad).item()
                    has_nan = torch.isnan(param.grad).any().item()
                    has_inf = torch.isinf(param.grad).any().item()
                    grad_status[name] = f"有梯度，范数: {norm:.6f}, NaN: {has_nan}, Inf: {has_inf}"
            
            # 记录所有参数的梯度状态
            main_logger.debug("详细的参数梯度状态:")
            for name, status in grad_status.items():
                main_logger.debug(f"参数 {name} 梯度状态: {status}")
        
        # 记录参数更新前的多个网络参数样本
        sample_params = {}
        for name, param in list(self.skill_coordinator.named_parameters())[:5]:  # 只取前5个参数作为样本
            if param.requires_grad and param.numel() > 0:
                sample_params[name] = param.clone().detach()
                main_logger.debug(f"参数 {name} 更新前: 均值={param.mean().item():.6f}, 标准差={param.std().item():.6f}")
        
        try:
            self.coordinator_optimizer.step()
            
            # 记录参数更新后的变化
            for name, old_param in sample_params.items():
                for curr_name, curr_param in self.skill_coordinator.named_parameters():
                    if curr_name == name:
                        param_mean_diff = (curr_param.detach().mean() - old_param.mean()).item()
                        param_abs_diff = torch.mean(torch.abs(curr_param.detach() - old_param)).item()
                        main_logger.debug(f"参数 {name} 更新后: 均值变化={param_mean_diff:.6f}, 平均绝对变化={param_abs_diff:.6f}")
                        break
                        
        except Exception as e:
            main_logger.error(f"优化器step失败: {e}")
            # 这种情况下我们无法继续，但至少记录了错误
        
        # 计算平均价值估计
        mean_state_value = state_values.mean().item()
        mean_agent_value = 0.0
        if agent_values and len(agent_values) > 0:
            # agent_values 是一个列表的张量，每个张量是 [batch_size, 1]
            # 我们需要将它们堆叠起来，然后计算均值
            stacked_agent_values = torch.stack(agent_values, dim=0) # Shape [n_agents, batch_size, 1]
            mean_agent_value = stacked_agent_values.mean().item()
        
        # rewards 是累积的k步环境奖励 r_h
        mean_high_level_reward = rewards.mean().item()
            
        # 返回：总损失, 策略损失, 价值损失, 团队熵, 个体熵, 状态价值均值, 智能体价值均值, 高层奖励均值
        return loss.item(), policy_loss.item(), value_loss.item(), \
               Z_entropy.item(), z_entropy.item(), \
               mean_state_value, mean_agent_value, mean_high_level_reward, total_cd_loss.item()
    
    def update_discoverer(self):
        """更新低层技能发现器网络"""
        if len(self.low_level_buffer) < self.config.batch_size:
            return 0, 0, 0, 0, 0, 0, 0, 0, 0 # 增加返回数量以匹配期望
        
        # 从缓冲区采样数据，包含内在奖励的三个组成部分
        batch = self.low_level_buffer.sample(self.config.batch_size)
        states, team_skills, observations, agent_skills, actions, rewards, dones, old_log_probs, \
        env_rewards_comp, team_disc_rewards_comp, ind_disc_rewards_comp = zip(*batch)
        
        states = torch.stack(states)
        team_skills = torch.stack(team_skills)
        observations = torch.stack(observations)
        agent_skills = torch.stack(agent_skills)
        actions = torch.stack(actions)
        rewards = torch.stack(rewards)
        dones = torch.stack(dones)
        old_log_probs = torch.stack(old_log_probs)
        
        # 关键修复：在Off-Policy更新中，为乱序批次数据初始化一次隐藏状态
        # 这确保了在整个更新步骤中使用一致的隐藏状态，避免引入不相关的历史信息
        self.skill_discoverer.init_hidden(batch_size=self.config.batch_size)
        
        # 获取当前状态价值和cd_loss
        values, cd_loss_discoverer = self.skill_discoverer.get_value(states, team_skills)
        
        # 构造下一状态的占位符
        next_values = torch.zeros_like(values)  # 实际应用中应该使用真实下一状态计算
        
        # 【关键修复】在计算GAE之前，对价值网络输出进行反归一化
        # 这确保了用于GAE计算的价值与原始尺度的奖励在同一数值尺度上
        if self.config.use_valuenorm and self.value_norm_discoverer is not None:
            denormalized_values = self._denormalize_values(values, self.value_norm_discoverer)
            denormalized_next_values = self._denormalize_values(next_values, self.value_norm_discoverer)
            main_logger.debug(f"Discoverer GAE: 使用反归一化后的价值进行GAE计算")
        else:
            denormalized_values = values
            denormalized_next_values = next_values
        
        # 计算GAE - 使用反归一化后的价值
        # 确保传递给compute_gae的values是1D，使用clone避免原地操作
        advantages, returns = compute_gae(rewards.clone(), denormalized_values.squeeze(-1).clone(), 
                                         denormalized_next_values.squeeze(-1).clone(), dones.clone(), 
                                         self.config.gamma, self.config.gae_lambda)
        # advantages 和 returns 都是 [batch_size]，分离计算图
        advantages = advantages.detach()
        returns = returns.detach()
        
        # The GAE returns (V_target) will be normalized later, right before the value loss calculation.
        main_logger.debug(f"Discoverer GAE returns (unnormalized): 均值={returns.mean().item():.4f}, 标准差={returns.std().item():.4f}")

        # 新增：优势归一化，稳定策略更新
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # 获取当前策略（复用已初始化的隐藏状态）
        _, action_log_probs, action_dist = self.skill_discoverer(observations, agent_skills)
        
        # 计算策略比率，使用detach()防止求导错误
        old_log_probs_detached = old_log_probs.clone().detach()
        ratios = torch.exp(action_log_probs - old_log_probs_detached)
        
        # 限制策略比率
        surr1 = ratios * advantages
        surr2 = torch.clamp(ratios, 1.0 - self.config.clip_epsilon, 1.0 + self.config.clip_epsilon) * advantages
        
        # 计算策略损失
        policy_loss = -torch.min(surr1, surr2).mean()
        
        # 记录PPO相关统计信息
        main_logger.debug(f"Discoverer PPO统计: 比率均值={ratios.mean().item():.4f}, "
                         f"比率标准差={ratios.std().item():.4f}, "
                         f"比率最大值={ratios.max().item():.4f}, "
                         f"比率最小值={ratios.min().item():.4f}")
        main_logger.debug(f"Discoverer 优势值统计: 均值={advantages.mean().item():.4f}, "
                         f"标准差={advantages.std().item():.4f}, "
                         f"最大值={advantages.max().item():.4f}, "
                         f"最小值={advantages.min().item():.4f}")
        
        # 计算价值损失（复用已初始化的隐藏状态）
        current_values, _ = self.skill_discoverer.get_value(states, team_skills) # Shape [128, 1]
        # 确保维度匹配并转换为float32类型
        current_values = current_values.float()
        # returns 是 [128], 需要 unsqueeze 匹配 current_values
        returns = returns.float().unsqueeze(-1) # Shape [128, 1]
        
        # 记录价值函数相关统计信息
        main_logger.debug(f"Discoverer 价值函数统计: 当前价值均值={current_values.mean().item():.4f}, "
                         f"当前价值标准差={current_values.std().item():.4f}, "
                         f"目标returns均值={returns.mean().item():.4f}, "
                         f"目标returns标准差={returns.std().item():.4f}")
        
        # Correctly apply Value Normalization for the value loss calculation.
        if self.config.use_valuenorm and self.value_norm_discoverer is not None:
            # 1. 先用当前统计量标准化（确保网络输出和targets使用相同的标准化基准）
            normalized_current_values = self._normalize_values(current_values, self.value_norm_discoverer)
            normalized_returns = self._normalize_values(returns, self.value_norm_discoverer)
            
            # 2. 计算损失（使用一致的标准化基准）
            value_loss = F.mse_loss(normalized_current_values, normalized_returns)
            
            # 3. 最后更新统计量（为下次使用做准备）
            self.value_norm_discoverer.update(returns.detach().cpu().numpy())
            
            main_logger.debug(f"Discoverer using ValueNorm: "
                            f"Normalized current_values mean={normalized_current_values.mean().item():.4f}, "
                            f"Normalized returns mean={normalized_returns.mean().item():.4f}")
        else:
            # Without ValueNorm, use raw values.
            value_loss = F.mse_loss(current_values, returns)
        
        # 计算熵损失
        entropy_loss = -action_dist.entropy().mean() * self.config.lambda_l
        
        # 记录各项损失的详细信息
        main_logger.debug(f"Discoverer 损失组成详情: "
                         f"策略损失={policy_loss.item():.6f}, "
                         f"价值损失={value_loss.item():.6f}, "
                         f"熵损失={entropy_loss.item():.6f}, "
                         f"动作熵均值={action_dist.entropy().mean().item():.6f}")
        
        # 总损失
        # 只有在使用OPT时才添加CD损失
        if self.config.use_opt:
            loss = policy_loss + self.config.value_loss_coef * value_loss + entropy_loss + self.config.lambda_cd * cd_loss_discoverer
        else:
            loss = policy_loss + self.config.value_loss_coef * value_loss + entropy_loss
        
        # 记录总损失和各组成部分的权重影响
        main_logger.debug(f"Discoverer 损失权重影响: "
                         f"策略损失贡献={policy_loss.item():.6f}, "
                         f"价值损失贡献={self.config.value_loss_coef * value_loss.item():.6f}, "
                         f"熵损失贡献={entropy_loss.item():.6f}, "
                         f"总损失={loss.item():.6f}")
        
        # 更新网络
        self.discoverer_optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.skill_discoverer.parameters(), self.config.max_grad_norm)
        self.discoverer_optimizer.step()
        
        # 计算内在奖励各部分的平均值
        avg_intrinsic_reward = rewards.mean().item()
        avg_env_reward_comp = torch.stack(env_rewards_comp).mean().item()
        avg_team_disc_reward_comp = torch.stack(team_disc_rewards_comp).mean().item()
        avg_ind_disc_reward_comp = torch.stack(ind_disc_rewards_comp).mean().item()
        avg_discoverer_value = current_values.mean().item() # 使用更新前的 current_values
        
        action_entropy_val = -entropy_loss.item() / self.config.lambda_l if self.config.lambda_l > 0 else 0.0

        return loss.item(), policy_loss.item(), value_loss.item(), action_entropy_val, \
               avg_intrinsic_reward, avg_env_reward_comp, avg_team_disc_reward_comp, avg_ind_disc_reward_comp, avg_discoverer_value
    
    def update_discriminators(self):
        """更新技能判别器网络（添加正则化防止过度训练）"""
        if len(self.state_skill_dataset) < self.config.batch_size:
            return 0
        
        # 从数据集采样数据
        batch = self.state_skill_dataset.sample(self.config.batch_size)
        states, team_skills, observations, agent_skills = zip(*batch)
        
        states = torch.stack(states)
        team_skills = torch.stack(team_skills)
        observations = torch.stack(observations)
        agent_skills = torch.stack(agent_skills)
        
        # 更新团队技能判别器
        team_disc_logits = self.team_discriminator(states)
        team_disc_loss = F.cross_entropy(team_disc_logits, team_skills)
        
        # 添加团队判别器熵正则化（防止过度自信）
        team_disc_probs = F.softmax(team_disc_logits, dim=-1)
        team_disc_entropy = -(team_disc_probs * F.log_softmax(team_disc_logits, dim=-1)).sum(dim=-1).mean()
        
        # 更新个体技能判别器
        batch_size, n_agents = agent_skills.shape
        
        # 扁平化处理
        observations_flat = observations.reshape(-1, observations.size(-1))
        agent_skills_flat = agent_skills.reshape(-1)
        team_skills_expanded = team_skills.unsqueeze(1).expand(-1, n_agents).reshape(-1)
        
        agent_disc_logits = self.individual_discriminator(observations_flat, team_skills_expanded)
        agent_disc_loss = F.cross_entropy(agent_disc_logits, agent_skills_flat)
        
        # 添加个体判别器熵正则化（防止过度自信）
        agent_disc_probs = F.softmax(agent_disc_logits, dim=-1)
        agent_disc_entropy = -(agent_disc_probs * F.log_softmax(agent_disc_logits, dim=-1)).sum(dim=-1).mean()
        
        # 总技能判别器损失（添加熵正则化项）
        entropy_reg_weight = 0.1  # 熵正则化权重
        disc_loss = team_disc_loss + agent_disc_loss - entropy_reg_weight * (team_disc_entropy + agent_disc_entropy)
        
        # 更新网络
        self.discriminator_optimizer.zero_grad()
        disc_loss.backward()
        self.discriminator_optimizer.step()
        
        # 每100步记录判别器性能监控指标
        if self.global_step % 100 == 0:
            with torch.no_grad():
                # 计算判别器准确率
                team_disc_acc = (team_disc_logits.argmax(dim=-1) == team_skills).float().mean()
                agent_disc_acc = (agent_disc_logits.argmax(dim=-1) == agent_skills_flat).float().mean()
                
                # 记录到TensorBoard
                self.writer.add_scalar('Discriminator/Team_Accuracy', team_disc_acc.item(), self.global_step)
                self.writer.add_scalar('Discriminator/Agent_Accuracy', agent_disc_acc.item(), self.global_step)
                self.writer.add_scalar('Discriminator/Team_Entropy', team_disc_entropy.item(), self.global_step)
                self.writer.add_scalar('Discriminator/Agent_Entropy', agent_disc_entropy.item(), self.global_step)
                self.writer.add_scalar('Discriminator/Team_Loss', team_disc_loss.item(), self.global_step)
                self.writer.add_scalar('Discriminator/Agent_Loss', agent_disc_loss.item(), self.global_step)
        
        return disc_loss.item()
    
    def update(self):
        """更新所有网络"""
        # 更新全局步数
        self.global_step += 1
        main_logger.debug(f"HMASDAgent.update (step {self.global_step}): self.writer object: {self.writer}")
        
        # 更频繁地检查环境贡献情况（从1000步降至200步）
        if self.global_step % 200 == 0:
            # 获取所有环境的贡献情况
            env_contributions = {}
            for env_id in range(32):  # 假设最多32个并行环境
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
            
            # 记录高层缓冲区状态
            high_level_buffer_size = len(self.high_level_buffer)
            main_logger.debug(f"当前高层缓冲区大小: {high_level_buffer_size}/{self.config.high_level_batch_size} (当前/所需)")
            
            # 如果高层缓冲区增长过慢，强制所有环境进行贡献
            if high_level_buffer_size < self.config.high_level_batch_size * 0.5 and self.global_step > 5000:
                main_logger.warning(f"高层缓冲区增长过慢 ({high_level_buffer_size}/{self.config.high_level_batch_size})，强制所有环境贡献样本")
                for env_id in range(32):
                    self.force_high_level_collection[env_id] = True
                    self.env_reward_thresholds[env_id] = 0.0
            
            # 记录环境贡献分布到TensorBoard
            if hasattr(self, 'writer'):
                contrib_data = np.zeros(32)
                for env_id, count in env_contributions.items():
                    contrib_data[env_id] = count
                # 记录贡献标准差，衡量是否平衡
                contrib_std = np.std(contrib_data)
                self.writer.add_scalar('Buffer/contribution_stddev', contrib_std, self.global_step)
                # 记录有效贡献环境数量
                contrib_envs = np.sum(contrib_data > 0)
                self.writer.add_scalar('Buffer/contributing_envs_count', contrib_envs, self.global_step)
        
        # 更新技能判别器
        discriminator_loss = self.update_discriminators()
        
        # 更新高层技能协调器
        coordinator_loss, coordinator_policy_loss, coordinator_value_loss, team_skill_entropy, agent_skill_entropy, \
        mean_coord_state_val, mean_coord_agent_val, mean_high_level_reward, cd_loss_val = self.update_coordinator()
        
        # 更新低层技能发现器
        discoverer_loss, discoverer_policy_loss, discoverer_value_loss, action_entropy, \
        avg_intrinsic_reward, avg_env_comp, avg_team_disc_comp, avg_ind_disc_comp, \
        avg_discoverer_val = self.update_discoverer()
        
        # 更新学习率调度器
        if getattr(self.config, 'use_lr_decay', False) and self.global_step <= self.config.lr_decay_steps:
            if self.coordinator_scheduler is not None:
                self.coordinator_scheduler.step()
            if self.discoverer_scheduler is not None:
                self.discoverer_scheduler.step()
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

        # 记录权重退火信息到TensorBoard
        if self.use_reward_annealing:
            # 计算当前权重
            progress = min(self.global_step / self.anneal_steps, 1.0)
            if self.anneal_schedule == 'cosine':
                progress_adjusted = 0.5 * (1 - np.cos(np.pi * progress))
            else:
                progress_adjusted = progress
            
            w_intrinsic_current = self.w_intrinsic_initial + (self.w_intrinsic_final - self.w_intrinsic_initial) * progress_adjusted
            w_extrinsic_current = self.w_extrinsic_initial + (self.w_extrinsic_final - self.w_extrinsic_initial) * progress_adjusted
            
            # 记录权重退火相关指标
            self.writer.add_scalar('RewardAnnealing/Progress', progress, self.global_step)
            self.writer.add_scalar('RewardAnnealing/Progress_Adjusted', progress_adjusted, self.global_step)
            self.writer.add_scalar('RewardAnnealing/Intrinsic_Weight_Multiplier', w_intrinsic_current, self.global_step)
            self.writer.add_scalar('RewardAnnealing/Extrinsic_Weight_Multiplier', w_extrinsic_current, self.global_step)
            
            # 记录实际生效的权重
            self.writer.add_scalar('RewardAnnealing/Effective_Lambda_D', self.config.lambda_D * w_intrinsic_current, self.global_step)
            self.writer.add_scalar('RewardAnnealing/Effective_Lambda_d', self.config.lambda_d * w_intrinsic_current, self.global_step)
            self.writer.add_scalar('RewardAnnealing/Effective_Lambda_e', self.config.lambda_e * w_extrinsic_current, self.global_step)

        # 记录到TensorBoard
        # 损失函数记录
        self.writer.add_scalar('Losses/Coordinator/Total', coordinator_loss, self.global_step)
        self.writer.add_scalar('Losses/Discoverer/Total', discoverer_loss, self.global_step)
        self.writer.add_scalar('Losses/Discriminator/Total', discriminator_loss, self.global_step)
        
        # 详细损失组成
        self.writer.add_scalar('Losses/Coordinator/Policy', coordinator_policy_loss, self.global_step)
        self.writer.add_scalar('Losses/Coordinator/Value', coordinator_value_loss, self.global_step)
        self.writer.add_scalar('Losses/Discoverer/Policy', discoverer_policy_loss, self.global_step)
        self.writer.add_scalar('Losses/Discoverer/Value', discoverer_value_loss, self.global_step)
        
        # 熵记录
        # 现在分别记录团队和个体技能熵，而不是平均值
        self.writer.add_scalar('Entropy/Coordinator/TeamSkill_Z', team_skill_entropy, self.global_step)
        self.writer.add_scalar('Entropy/Coordinator/AgentSkill_z_Average', agent_skill_entropy, self.global_step)
        self.writer.add_scalar('Entropy/Discoverer/Action', action_entropy, self.global_step)

        # 奖励记录
        # 新增对高层奖励的记录（k步累积环境奖励均值）
        self.writer.add_scalar('Rewards/HighLevel/K_Step_Accumulated_Mean', mean_high_level_reward, self.global_step)
        
        # 内在奖励记录
        self.writer.add_scalar('Rewards/Intrinsic/LowLevel_Average', avg_intrinsic_reward, self.global_step)
        self.writer.add_scalar('Rewards/Intrinsic/Components/Environmental_Portion_Average', avg_env_comp, self.global_step)
        self.writer.add_scalar('Rewards/Intrinsic/Components/TeamDiscriminator_Portion_Average', avg_team_disc_comp, self.global_step)
        self.writer.add_scalar('Rewards/Intrinsic/Components/IndividualDiscriminator_Portion_Average', avg_ind_disc_comp, self.global_step)

        # 价值函数估计记录
        self.writer.add_scalar('ValueEstimates/Coordinator/StateValue_Mean', mean_coord_state_val, self.global_step)
        self.writer.add_scalar('ValueEstimates/Coordinator/AgentValue_Average_Mean', mean_coord_agent_val, self.global_step)
        self.writer.add_scalar('ValueEstimates/Discoverer/Value_Mean', avg_discoverer_val, self.global_step)

        # 记录当前学习率
        if hasattr(self, 'writer'):
            current_coord_lr = self.coordinator_optimizer.param_groups[0]['lr']
            current_disc_lr = self.discoverer_optimizer.param_groups[0]['lr']
            current_discriminator_lr = self.discriminator_optimizer.param_groups[0]['lr']
            
            self.writer.add_scalar('LearningRate/Coordinator', current_coord_lr, self.global_step)
            self.writer.add_scalar('LearningRate/Discoverer', current_disc_lr, self.global_step)
            self.writer.add_scalar('LearningRate/Discriminator', current_discriminator_lr, self.global_step)

        # CD Loss
        self.writer.add_scalar('Losses/Coordinator/CD_Loss', cd_loss_val, self.global_step)

        # 记录关键超参数
        self.writer.add_scalar('Parameters/Lambda_D', self.config.lambda_D, self.global_step)
        self.writer.add_scalar('Parameters/Lambda_d', self.config.lambda_d, self.global_step)
        self.writer.add_scalar('Parameters/Lambda_h', self.config.lambda_h, self.global_step)
        self.writer.add_scalar('Parameters/Lambda_l', self.config.lambda_l, self.global_step)

        # Value Normalization统计信息记录 - 使用SB3 RunningMeanStd
        if self.config.use_valuenorm:
            if self.value_norm_coordinator is not None:
                self.writer.add_scalar('ValueNorm/Coordinator/Mean', 
                                     self.value_norm_coordinator.mean.item(), self.global_step)
                self.writer.add_scalar('ValueNorm/Coordinator/Std', 
                                     np.sqrt(self.value_norm_coordinator.var.item()), self.global_step)
                self.writer.add_scalar('ValueNorm/Coordinator/Count', 
                                     self.value_norm_coordinator.count, self.global_step)
            if self.value_norm_discoverer is not None:
                self.writer.add_scalar('ValueNorm/Discoverer/Mean', 
                                     self.value_norm_discoverer.mean.item(), self.global_step)
                self.writer.add_scalar('ValueNorm/Discoverer/Std', 
                                     np.sqrt(self.value_norm_discoverer.var.item()), self.global_step)
                self.writer.add_scalar('ValueNorm/Discoverer/Count', 
                                     self.value_norm_discoverer.count, self.global_step)

        # 添加一个固定的测试值，用于调试TensorBoard显示问题
        self.writer.add_scalar('Debug/test_value', 1.0, self.global_step)
        
        # 每次更新后都刷新数据到硬盘，确保TensorBoard能尽快看到
        self.writer.flush()
        
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
            'config': self.config
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
        
        main_logger.info(f"模型已从 {path} 加载 (使用非严格模式)")
