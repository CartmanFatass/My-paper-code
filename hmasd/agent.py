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
from hmasd.utils import RolloutBuffer, compute_gae, compute_ppo_loss, one_hot


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
        
        # 移除TensorBoard相关初始化，由训练脚本统一管理
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        # self.writer = SummaryWriter(log_dir)  # 移除
        # main_logger.debug(f"HMASDAgent.__init__: SummaryWriter created: {self.writer}")
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
        
        # 状态-技能数据集已废弃，判别器现在直接从RolloutBuffer获取数据
        # self.state_skill_dataset = StateSkillDataset(getattr(config, 'low_level_buffer_size', 10000))  # 已废弃
        
        # 统一的Rollout缓冲区，同时存储高层和低层策略数据
        rollout_length = getattr(config, 'rollout_length', 2048)  # 默认rollout长度
        num_envs = getattr(config, 'num_envs', 1)  # 并行环境数量
        gru_hidden_size = getattr(config, 'gru_hidden_size', 128)  # GRU隐状态大小
        
        self.rollout_buffer = RolloutBuffer(
            num_steps=rollout_length,
            num_envs=num_envs,
            n_agents=config.n_agents,
            obs_dim=config.obs_dim,
            action_dim=config.action_dim,
            gru_hidden_size=gru_hidden_size,
            n_Z=config.n_Z,
            n_z=config.n_z,
            state_dim=config.state_dim
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

    def clear_buffers(self):
        """清空经验缓冲区（用于严格on-policy训练）"""
        main_logger.info("清空统一的经验缓冲区")
        # 注意：不清空 state_skill_dataset，因为它用于判别器训练
        
        # 清空统一的rollout缓冲区
        self.rollout_buffer.reset()
        
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
    
    def reset_env_state(self, env_id):
        """Resets the internal state for a specific environment."""
        if env_id in self.env_hidden_states:
            self.env_hidden_states[env_id] = None
            main_logger.debug(f"Reset hidden state for env {env_id}")
        # ... (rest of the reset logic for skills, etc., is the same)
        if env_id in self.env_team_skills:
            self.env_team_skills[env_id] = -1
        if env_id in self.env_agent_skills:
            self.env_agent_skills[env_id] = np.full(self.config.n_agents, -1, dtype=int)
    
    
    def select_action(self, observations, agent_skills=None, deterministic=False, env_id=0, state=None):
        """
        [最终修正版] 选择动作，并为每个环境管理正确的隐藏状态形状。
        """
        if agent_skills is None:
            agent_skills = self.env_agent_skills.get(env_id, self.current_agent_skills)
            
        n_agents = observations.shape[0]
        actions = torch.zeros((n_agents, self.config.action_dim), device=self.device)
        action_logprobs = torch.zeros(n_agents, device=self.device)
        values = torch.zeros(n_agents, device=self.device)
        
        # --- 核心隐藏状态管理 ---
        gru_hidden_size = self.config.gru_hidden_size
        hidden_state = self.env_hidden_states.get(env_id)
        if hidden_state is None:
            # --- 核心修正：初始化为正确的2D形状 [n_agents, gru_hidden_size] ---
            hidden_state = torch.zeros(n_agents, gru_hidden_size, device=self.device)

        with torch.no_grad():
            # Get global value (this part is correct and does not need to change)
            current_team_skill = self.env_team_skills.get(env_id, self.current_team_skill)
            if current_team_skill is not None and state is not None:
                global_state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                team_skill_tensor = torch.tensor(current_team_skill, device=self.device).unsqueeze(0)
                global_value, _ = self.skill_discoverer.get_value(global_state_tensor, team_skill_tensor)
                values.fill_(global_value.item())
            else:
                values.fill_(0.0)

            # 将所有智能体作为单个批次处理
            obs_batch = torch.FloatTensor(observations).to(self.device)
            skill_batch = torch.tensor(agent_skills, device=self.device)

            # 将环境的 hidden_state (现在是正确的2D形状) 传入网络
            actions_batch, logprobs_batch, _, new_hidden_state = self.skill_discoverer.forward(
                obs_batch, skill_batch, hidden_state, deterministic
            )
            
            # 存储更新后的 hidden_state (也是2D形状)
            self.env_hidden_states[env_id] = new_hidden_state

        return actions_batch.cpu().numpy(), logprobs_batch.cpu().numpy(), values.cpu().numpy()
    
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
    
    def _batched_assign_skills(self, states_batch, observations_batch, env_steps_batch, dones_batch, deterministic=False):
        """
        [新方法] 为一批环境分配技能。
        只为需要更新的环境运行神经网络。
        """
        num_envs = states_batch.shape[0]
        
        # 找出哪些环境需要重新分配技能 (技能周期结束 或 环境刚重置)
        needs_reassignment_mask = (env_steps_batch % self.config.k == 0) | dones_batch
        indices_to_update = np.where(needs_reassignment_mask)[0]

        # 准备最终的技能批次，默认为当前技能
        new_team_skills_batch = np.array([self.env_team_skills.get(i, -1) for i in range(num_envs)], dtype=int)
        new_agent_skills_batch = np.array([self.env_agent_skills.get(i, np.full(self.config.n_agents, -1)) for i in range(num_envs)], dtype=int)
        new_log_probs_batch = [self.env_log_probs.get(i, {}) for i in range(num_envs)]

        if len(indices_to_update) > 0:
            # 提取需要更新的状态和观测
            states_to_process = torch.FloatTensor(states_batch[indices_to_update]).to(self.device)
            obs_to_process = torch.FloatTensor(observations_batch[indices_to_update]).to(self.device)

            # 批量运行 SkillCoordinator
            with torch.no_grad():
                team_skills, agent_skills, Z_logits, z_logits, _, _ = self.skill_coordinator(
                    states_to_process, obs_to_process, deterministic
                )
            
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
                    'agent_log_probs': z_log_probs_list
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
        [最终修正版] 为一批环境选择动作，并正确计算价值估计。
        """
        num_envs, n_agents, _ = observations_batch.shape
        
        # 1. 获取或初始化批量的隐藏状态 (这部分逻辑保持不变)
        hidden_states_batch = np.zeros((num_envs, n_agents, self.config.gru_hidden_size), dtype=np.float32)
        for i in range(num_envs):
            if i in self.env_hidden_states and self.env_hidden_states[i] is not None:
                hidden_states_batch[i] = self.env_hidden_states[i].cpu().numpy()

        hidden_states_batch[dones_batch] = 0.0

        # 2. 准备批量输入 (这部分逻辑保持不变)
        obs_flat = observations_batch.reshape(-1, self.config.obs_dim)
        skills_flat = agent_skills_batch.reshape(-1)
        hidden_states_flat = hidden_states_batch.reshape(-1, self.config.gru_hidden_size)

        obs_tensor = torch.FloatTensor(obs_flat).to(self.device)
        skills_tensor = torch.LongTensor(skills_flat).to(self.device)
        hidden_tensor = torch.FloatTensor(hidden_states_flat).to(self.device)
        
        with torch.no_grad():
            # 3. 批量运行 Actor 网络获取动作 (这部分逻辑保持不变)
            actions_flat, logprobs_flat, _, new_hidden_flat = self.skill_discoverer(
                obs_tensor, skills_tensor, hidden_tensor, deterministic
            )

            # ======================= ▼▼▼ 核心修复点 ▼▼▼ =======================
            # 4. 批量运行 Critic 网络获取价值估计 V(s, Z)
            #    为批次中的每个智能体提供其对应的全局状态和团队技能
            states_expanded = np.repeat(states_batch, n_agents, axis=0)
            team_skills_expanded = np.repeat(team_skills_batch, n_agents, axis=0)
            
            states_tensor = torch.FloatTensor(states_expanded).to(self.device)
            team_skills_tensor = torch.LongTensor(team_skills_expanded).to(self.device)
            
            # 从 Critic 获取价值估计 - 这是被切断的关键信号！
            values_flat, _ = self.skill_discoverer.get_value(states_tensor, team_skills_tensor)
            # ======================= ▲▲▲ 核心修复点 ▲▲▲ =======================
            
        # 5. Reshape back (这部分逻辑保持不变)
        actions_batch = actions_flat.cpu().numpy().reshape(num_envs, n_agents, self.config.action_dim)
        logprobs_batch = logprobs_flat.cpu().numpy().reshape(num_envs, n_agents)
        new_hidden_batch = new_hidden_flat.reshape(num_envs, n_agents, self.config.gru_hidden_size)
        
        # 6. 【重要】将计算出的价值也 Reshape 并准备返回
        values_batch = values_flat.cpu().numpy().reshape(num_envs, n_agents)
        
        # 7. 更新内部隐藏状态 (这部分逻辑保持不变)
        for i in range(num_envs):
            self.env_hidden_states[i] = new_hidden_batch[i]
            
        # 8. 【重要】在返回值中包含正确的 values_batch
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
                self.env_team_skills[i] = -1
                self.env_agent_skills[i] = np.full(self.config.n_agents, -1)
                self.env_log_probs[i] = {}
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
                          gru_hidden_states, env_id, team_skill=None, agent_skills=None, 
                          buffer_type='discoverer', reward_components=None):
        """
        将一个时间步的所有智能体数据存储到统一rollout缓冲区
        
        ⚠️ 【重要】此函数现在只能存储低层策略数据！
        ⚠️ 高层策略数据必须通过 add_high_level_data 存储！
        
        参数:
            t: 时间步索引
            state: 全局状态 [state_dim]
            observations: 所有智能体观测 [n_agents, obs_dim]
            actions: 所有智能体动作 [n_agents, action_dim]
            rewards: 奖励数据 [n_agents] 或单个值
            dones: 完成标志 [n_agents] 或单个值
            values: 价值估计 [n_agents]
            log_probs: 对数概率 [n_agents]
            gru_hidden_states: GRU隐状态 [n_agents, hidden_size]
            env_id: 环境索引
            team_skill: 团队技能索引
            agent_skills: 个体技能索引 [n_agents]
            buffer_type: 'coordinator' 或 'discoverer' （已适配统一缓冲区）
            reward_components: 包含奖励组成的字典 (必须提供！)
        """
        if reward_components is None:
            main_logger.error(f"store_rollout_step: reward_components cannot be None. env={env_id}, t={t}")
            return
        
        # 提取真实的奖励组成部分
        reward_env = reward_components.get('env', np.zeros_like(rewards, dtype=np.float32))
        reward_team_disc = reward_components.get('team_disc', np.zeros_like(rewards, dtype=np.float32))
        reward_ind_disc = reward_components.get('ind_disc', np.zeros_like(rewards, dtype=np.float32))

        # 存储数据到统一rollout缓冲区，传递时间步索引 t 和 state
        success = self.rollout_buffer.add(
            t=t,
            state=state,
            obs=observations,
            action=actions,
            reward=rewards,
            done=dones,
            value=values,
            log_prob=log_probs,
            gru_hidden_state=gru_hidden_states.cpu(),
            env_idx=env_id,
            team_skill=team_skill,
            agent_skills=agent_skills,
            reward_env=reward_env,
            reward_team_disc=reward_team_disc,
            reward_ind_disc=reward_ind_disc
        )
        
        # 检查存储是否成功
        if not success:
            main_logger.warning(f"低层数据存储失败（可能重复存储），环境{env_id}，时间步: {t}")
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
        
        for i in range(n_agents):
            # 【重要修复】使用下一状态和下一观测计算内在奖励，与论文保持一致
            # 这确保了奖励是基于动作的直接后果
            intrinsic_reward, env_comp, team_disc_comp, ind_disc_comp = self._compute_intrinsic_reward(
                next_state, rewards, next_observations[i], team_skill, agent_skills[i]
            )
            
            main_logger.debug(f"Reward components for agent {i}: env={env_comp:.6f}, team_disc={team_disc_comp:.6f}, ind_disc={ind_disc_comp:.6f}")
            
            # 【重要改动】移除基于潜能的个体化塑形奖励
            # 探索奖励的职责现在由判别器内在奖励机制承担
            # exploration_component = self.config.potential_reward_weight * potential_reward if hasattr(self.config, 'potential_reward_weight') else 0.0
            # final_intrinsic_reward = intrinsic_reward + exploration_component
            final_intrinsic_reward = intrinsic_reward # 直接使用计算出的内在奖励
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
        
        # 获取或创建环境特定的GRU隐藏状态
        if env_id in self.env_hidden_states and self.env_hidden_states[env_id] is not None:
            # 确保隐藏状态是二维张量，去掉多余的维度
            hidden_state = self.env_hidden_states[env_id]
            if hidden_state.dim() > 2:
                hidden_state = hidden_state.squeeze(0)
            gru_hidden_states = hidden_state.expand(n_agents, -1)  # [n_agents, hidden_size]
        else:
            gru_hidden_size = getattr(self.config, 'gru_hidden_size', 128)
            gru_hidden_states = torch.zeros(n_agents, gru_hidden_size, device=self.device)
        
        if rollout_step_idx is not None:
            t = rollout_step_idx
        else:
            t = self.global_step % self.rollout_buffer.num_steps
            main_logger.warning(f"_store_discoverer_experience: rollout_step_idx not provided, falling back to modulo logic. t={t}")
        
        self.store_rollout_step(
            t=t,
            state=state,  # 【重要修复】存储当前状态而非下一状态
            observations=observations,  # 【重要修复】存储当前观测而非下一观测
            actions=actions,
            rewards=intrinsic_rewards_array,
            dones=dones,
            values=values,
            log_probs=action_logprobs,
            gru_hidden_states=gru_hidden_states,
            env_id=env_id,
            team_skill=team_skill,
            agent_skills=agent_skills,
            buffer_type='discoverer',
            reward_components=reward_components
        )

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
        
        # 计算高层策略的价值估计
        with torch.no_grad():
            state_tensor_for_value = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            obs_tensor_for_value = torch.FloatTensor(observations).unsqueeze(0).to(self.device)
            state_val, agent_vals, _ = self.skill_coordinator.get_value(state_tensor_for_value, obs_tensor_for_value)
            
            # 【修复】将全局状态价值与所有智能体价值的平均值相加
            if agent_vals is not None and len(agent_vals) > 0:
                # agent_vals 是一个张量列表，将它们堆叠起来然后计算均值
                agent_vals_tensor = torch.stack(agent_vals)
                mean_agent_val = agent_vals_tensor.mean()
                high_level_value = state_val + mean_agent_val
            else:
                high_level_value = state_val

            high_level_value_np = high_level_value.squeeze().cpu().numpy()

        # 计算联合log概率
        if log_probs:
            total_log_prob = log_probs['team_log_prob'] + sum(log_probs['agent_log_probs'])
        else:
            total_log_prob = 0.0
        
        # Use the dedicated add_high_level_data to prevent overwriting low-level rewards.
        if rollout_step_idx is None:
            main_logger.error("rollout_step_idx is None! Cannot store high-level experience correctly.")
            return False
            
        time_step_of_decision = rollout_step_idx - skill_timer
        if time_step_of_decision < 0:
            main_logger.warning(f"Calculated a negative time_step_of_decision: {time_step_of_decision}. Clamping to 0.")
            time_step_of_decision = 0
            
        t = time_step_of_decision
        
        # 调用add_high_level_data并检查返回值
        success = self.rollout_buffer.add_high_level_data(
            env_idx=env_id,
            time_step=t,
            value=high_level_value_np,
            joint_log_prob=total_log_prob,
            accumulated_reward=env_accumulated_reward
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
        
        # 重置该环境的奖励累积和计时器 (这部分逻辑保持不变)
        self.env_reward_sums[env_id] = 0.0
        self.env_timers[env_id] = 0
        
        return True

    # _store_discriminator_data 函数已废弃，判别器现在直接从RolloutBuffer获取数据

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
        # 确保rewards是数值类型
        current_reward = rewards if isinstance(rewards, (int, float)) else rewards.item()
        
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
        
        # 2. 判别器训练数据现在直接从RolloutBuffer获取，无需单独存储
        # self._store_discriminator_data(next_state, team_skill, next_observations, agent_skills)  # 已废弃
        
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
        if steps_since_contribution > self.config.force_collection_threshold:
            self.force_high_level_collection[env_id] = True
            if steps_since_contribution % self.config.force_collection_threshold == 0:  # 避免日志过多
                main_logger.info(f"环境ID={env_id}已{steps_since_contribution}步未贡献高层样本，将强制收集")
        
        # 存储高层策略经验（如果满足条件）
        # 【注意】高层策略数据继续使用当前状态和观测，这是正确的
        self._store_coordinator_experience(
            state, observations, env_id, team_skill, agent_skills, 
            log_probs, dones, skill_timer, steps_since_contribution, force_collection,
            rollout_step_idx=rollout_step_idx
        )
        
        # 返回奖励组成部分给训练循环
        return returned_reward_components
    
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

    def _compute_intrinsic_reward(self, next_state, reward, next_obs, team_skill, agent_skill):
        """
        计算单个智能体的内在奖励（修改版本，确保High-Level和Low-Level协调一致）
        
        核心修改：
        - 环境奖励组件：直接使用纯净的团队奖励（不加权重）
        - 判别器奖励：保持原有的内在奖励机制，用于技能多样性
        - 确保两个层次优化相同的底层团队目标
        
        参数:
            next_state: 下一全局状态
            reward: 环境奖励（现在是纯净的团队奖励）
            next_obs: 智能体的下一观测
            team_skill: 团队技能索引
            agent_skill: 智能体技能索引
            
        返回:
            intrinsic_reward: 内在奖励值
            env_component: 环境奖励组件
            team_disc_component: 团队判别器奖励组件
            ind_disc_component: 个体判别器奖励组件
        """
        with torch.no_grad():
            # 计算团队技能判别器奖励
            next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0).to(self.device)
            team_disc_logits = self.team_discriminator(next_state_tensor)
            team_disc_log_probs = F.log_softmax(team_disc_logits, dim=-1)
            team_skill_log_prob = team_disc_log_probs[0, team_skill]
            
            # main_logger.debug(f"Team discriminator: team_skill={team_skill}, raw_log_prob={team_skill_log_prob.item():.6f}")
            
            # 计算个体技能判别器奖励
            agent_obs_tensor = torch.FloatTensor(next_obs).unsqueeze(0).to(self.device)
            team_skill_tensor = torch.tensor(team_skill, device=self.device)
            agent_disc_logits = self.individual_discriminator(agent_obs_tensor, team_skill_tensor)
            agent_disc_log_probs = F.log_softmax(agent_disc_logits, dim=-1)
            agent_skill_log_prob = agent_disc_log_probs[0, agent_skill]
            
            # main_logger.debug(f"Individual discriminator: agent_skill={agent_skill}, raw_log_prob={agent_skill_log_prob.item():.6f}")
            
           
            
            env_component = self.config.lambda_e * reward

            # 判别器内在奖励：保持原有机制，用于技能多样性和探索
            if self.use_reward_annealing:
                progress = min(self.global_step / self.anneal_steps, 1.0)
                if self.anneal_schedule == 'cosine':
                    progress_adjusted = 0.5 * (1 - np.cos(np.pi * progress))
                else:
                    progress_adjusted = progress
                
                w_intrinsic_current = self.w_intrinsic_initial + (self.w_intrinsic_final - self.w_intrinsic_initial) * progress_adjusted
                
                team_disc_component = self.config.lambda_D * w_intrinsic_current * team_skill_log_prob.item()
                ind_disc_component = self.config.lambda_d * w_intrinsic_current * agent_skill_log_prob.item()
                
                # main_logger.debug(f"Annealing mode: w_intrinsic={w_intrinsic_current:.4f}")
                # main_logger.debug(f"Annealed reward components: team_disc={team_disc_component:.6f}, ind_disc={ind_disc_component:.6f}")
            else:
                team_disc_component = self.config.lambda_D * team_skill_log_prob.item()
                ind_disc_component = self.config.lambda_d * agent_skill_log_prob.item()
                
                # main_logger.debug(f"Normal mode: lambda_D={self.config.lambda_D}, lambda_d={self.config.lambda_d}")
                # main_logger.debug(f"Calculated reward components: team_disc={team_disc_component:.6f}, ind_disc={ind_disc_component:.6f}")
            
            # 【核心修改】Low-Level策略接收：纯净团队奖励 + 判别器内在奖励
            intrinsic_reward = env_component + team_disc_component + ind_disc_component
            
            # main_logger.debug(f"Modified intrinsic reward: env={env_component:.6f}, team_disc={team_disc_component:.6f}, ind_disc={ind_disc_component:.6f}")
            
            return intrinsic_reward, env_component, team_disc_component, ind_disc_component

    def update_coordinator(self, num_steps):
        """更新高层技能协调器网络（使用标准PPO更新，而非错误的序列化更新）"""
        # num_steps 现在是实际在缓冲区中的有效数据量
        
        # 检查是否有有效的高层数据
        high_level_data_count = np.sum(self.rollout_buffer.high_level_valid_mask[:num_steps])
        if high_level_data_count == 0:
            main_logger.warning("没有有效的高层策略数据，跳过Coordinator更新")
            return 0, 0, 0, 0, 0, 0, 0, 0, 0
        
        main_logger.info(f"开始使用统一缓冲区更新Coordinator，有效高层数据: {high_level_data_count}个")
        
        # 计算高层策略的GAE，传递实际使用的步数
        self.rollout_buffer.compute_high_level_advantages(num_steps=num_steps)
        
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
            team_skills_batch = batch['team_skills'].to(self.device)    # Shape: (B,)
            agent_skills_batch = batch['agent_skills'].to(self.device) # Shape: (B, n_agents)
            old_log_probs_batch = batch['log_probs'].to(self.device)    # Shape: (B,)
            advantages_batch = batch['advantages'].to(self.device)      # Shape: (B,)
            returns_batch = batch['returns'].to(self.device)           # Shape: (B,)
            
            # --- 核心改动：不使用 evaluate_sequence，而是直接调用 forward 和 get_value ---
            # 1. 重新评估当前策略下的 log_probs 和 entropy
            _, _, Z_logits, z_logits_list, _, _ = self.skill_coordinator(states_batch, observations_batch)
            
            Z_dist = Categorical(logits=Z_logits)
            team_log_probs = Z_dist.log_prob(team_skills_batch)
            team_entropy = Z_dist.entropy()

            agent_log_probs = []
            agent_entropies = []
            for i in range(self.config.n_agents):
                zi_dist = Categorical(logits=z_logits_list[i])
                agent_log_probs.append(zi_dist.log_prob(agent_skills_batch[:, i]))
                agent_entropies.append(zi_dist.entropy())
                
            agent_log_probs = torch.stack(agent_log_probs, dim=1).sum(dim=1)
            agent_entropies_tensor = torch.stack(agent_entropies, dim=1)  # Shape: (B, n_agents)

            # 计算联合log_prob和总熵
            total_log_probs = team_log_probs + agent_log_probs
            # 【修复】按照论文公式计算总熵：E[H(π_h(Z|...)) + Σ H(π_h(z_i|...))]
            # 先计算每个批次样本的总熵（团队熵 + 所有个体熵之和），然后取期望（均值）
            total_entropy_per_sample = team_entropy + agent_entropies_tensor.sum(dim=1)  # Shape: (B,)
            entropy = total_entropy_per_sample.mean()  # 对批次取均值，得到标量

            # 2. 获取当前策略下的价值估计
            state_values, agent_values_list, _ = self.skill_coordinator.get_value(states_batch, observations_batch)
            
            # 【修复】将全局状态价值与所有智能体价值的平均值相加
            if agent_values_list is not None and len(agent_values_list) > 0:
                # agent_values_list 是一个张量列表，将它们堆叠起来然后计算均值
                agent_values_tensor = torch.stack(agent_values_list).squeeze(-1) # Shape: (n_agents, B)
                mean_agent_values = agent_values_tensor.mean(dim=0) # Shape: (B,)
                values = state_values.squeeze(-1) + mean_agent_values # Shape: (B,)
            else:
                values = state_values.squeeze(-1)  # Shape: (B,)

            # 【核心改动】移除优势标准化，使用Value Normalization作为替代
            advantages_batch = (advantages_batch - advantages_batch.mean()) / (advantages_batch.std() + 1e-8)
            
            # --- 计算PPO损失 (标准的、非序列化的) ---
            ratios = torch.exp(total_log_probs - old_log_probs_batch.detach())
            surr1 = ratios * advantages_batch
            surr2 = torch.clamp(ratios, 1.0 - self.config.clip_epsilon, 1.0 + self.config.clip_epsilon) * advantages_batch
            policy_loss = -torch.min(surr1, surr2).mean()
            
            # 价值损失
            if self.config.use_valuenorm and self.value_norm_coordinator is not None:
                # a. Critic的预测值需要被归一化，以便与归一化的目标进行比较
                values_for_loss = self._normalize_values(values, self.value_norm_coordinator)
                # b. Critic的训练目标(returns)也需要被归一化
                returns_for_loss = self._normalize_values(returns_batch, self.value_norm_coordinator)
                value_loss = F.mse_loss(values_for_loss, returns_for_loss.detach())
            else:
                # 如果不使用ValueNorm，一切照旧
                value_loss = F.mse_loss(values, returns_batch)
            
            # 熵损失
            # 【修复】使用config中定义的统一熵系数，严格按照论文公式
            entropy_loss = -self.config.lambda_h * entropy
            
            # CD损失（如果启用OPT）
            cd_loss = torch.tensor(0.0, device=self.device, requires_grad=True)
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
                    if self.rollout_buffer.high_level_valid_mask[t, env_idx]:
                        # ▼▼▼▼▼▼▼▼▼▼【恢复此处的修改】▼▼▼▼▼▼▼▼▼▼
                        # 从专用的 high_level_rewards 缓冲区读取
                        valid_high_level_rewards.append(self.rollout_buffer.high_level_rewards[t, env_idx])
                        # ▲▲▲▲▲▲▲▲▲▲【恢复此处的修改】▲▲▲▲▲▲▲▲▲▲
            
            if len(valid_high_level_rewards) > 0:
                avg_high_level_reward = np.mean(valid_high_level_rewards)
                
                # 计算平均价值（随机采样一些状态进行估计）
                sample_size = min(50, len(valid_high_level_rewards))
                sample_states = []
                sample_observations = []
                for t in range(num_steps):
                    for env_idx in range(self.rollout_buffer.num_envs):
                        if self.rollout_buffer.high_level_valid_mask[t, env_idx] and len(sample_states) < sample_size:
                            sample_states.append(self.rollout_buffer.states[t, env_idx])
                            sample_observations.append(self.rollout_buffer.obs[t, env_idx])
                
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
    
    def update_discoverer_from_rollout(self, num_steps, ppo_epochs=4):
        """
        使用统一rollout缓冲区更新低层技能发现器网络，实现真正的BPTT
        这是新PPO流程的核心：一次性评估整个序列并进行反向传播
        
        注意：GAE计算已经在主训练循环中完成，这里直接使用预计算的advantages和returns
        
        参数:
            num_steps: 缓冲区中的有效步数
            ppo_epochs: PPO更新轮数
            
        返回:
            与原update_discoverer相同格式的返回值
        """
        
        main_logger.info(f"开始使用统一缓冲区更新Discoverer (真正的BPTT)，低层数据量: {num_steps}步")
        main_logger.info("GAE已在主训练循环中计算完成，直接使用预计算的advantages和returns")
        
        # 累积损失统计
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy_loss = 0.0
        total_loss = 0.0
        update_count = 0
        
        # 计算每个批次包含的序列数量（环境数×智能体数）
        num_sequences_per_batch = getattr(self.config, 'sequence_batch_size', 
                                        min(self.rollout_buffer.num_envs * self.rollout_buffer.n_agents, 32))
        
        # 【修复】使用专门的Discoverer采样器进行GRU友好的更新
        sequence_sampler = self.rollout_buffer.get_discoverer_sampler(num_steps, ppo_epochs, num_sequences_per_batch)
        
        if sequence_sampler is None:
            main_logger.error("无法从统一rollout缓冲区获取Discoverer序列采样器")
            return 0, 0, 0, 0, 0, 0, 0, 0, 0
            
        # --- 1. 在所有PPO Epochs开始前，一次性更新统计量 ---
        if self.config.use_valuenorm and self.value_norm_discoverer is not None:
            # 获取整个rollout buffer的回报
            all_returns = self.rollout_buffer.returns[:num_steps].reshape(-1)
            # 使用这批数据更新运行统计量
            self.value_norm_discoverer.update(all_returns)
            main_logger.info(f"Discoverer ValueNorm已更新. 新均值: {self.value_norm_discoverer.mean:.4f}, 新标准差: {np.sqrt(self.value_norm_discoverer.var):.4f}")

        for batch in sequence_sampler:
            # 提取序列批次数据
            observations_seq = batch['observations']  # Shape: (T, batch_size, obs_dim)
            actions_seq = batch['actions']           # Shape: (T, batch_size, action_dim)
            old_log_probs_seq = batch['log_probs']    # Shape: (T, batch_size)
            advantages_seq = batch['advantages']      # Shape: (T, batch_size)
            returns_seq = batch['returns']           # Shape: (T, batch_size)
            global_states_seq = batch['global_states'] # Shape: (T, batch_size, state_dim) # 新增
            team_skills_seq = batch['team_skills']    # Shape: (T, batch_size)           # 新增
            agent_skills_seq = batch['agent_skills'] # Shape: (T, batch_size)
            # **** 提取新增的 initial_hxs ****
            initial_hxs = batch['initial_hxs']       # Shape: (batch_size, hidden_size)
            dones_seq = batch['dones'].to(self.device)
            
            # 转换到正确的设备
            observations_seq = observations_seq.to(self.device)
            actions_seq = actions_seq.to(self.device)
            old_log_probs_seq = old_log_probs_seq.to(self.device)
            advantages_seq = advantages_seq.to(self.device)
            returns_seq = returns_seq.to(self.device)
            global_states_seq = global_states_seq.to(self.device)  # 新增
            team_skills_seq = team_skills_seq.to(self.device)      # 新增
            agent_skills_seq = agent_skills_seq.to(self.device)
            initial_hxs = initial_hxs.to(self.device)
            
            T, batch_size = observations_seq.shape[:2]
            
            # **** 核心改动：将 initial_hxs 传递给 evaluate_sequence ****
            new_log_probs, new_values, entropy = self.skill_discoverer.evaluate_sequence(
                observations_seq, agent_skills_seq, actions_seq, 
                global_states_seq, team_skills_seq,
                initial_hxs,  # **** 传入初始隐状态 ****
                dones_seq
            )
            
            # --- 将所有数据展平以计算损失 ---
            # 展平数据: (T, B) -> (T*B)
            advantages_flat = advantages_seq.reshape(-1)
            returns_flat = returns_seq.reshape(-1)
            old_log_probs_flat = old_log_probs_seq.reshape(-1)
            new_log_probs_flat = new_log_probs.reshape(-1)
            new_values_flat = new_values.reshape(-1)
            
            # 【核心改动】移除优势标准化，使用Value Normalization作为替代
            advantages_flat = (advantages_flat - advantages_flat.mean()) / (advantages_flat.std() + 1e-8)
            
            # --- 计算PPO损失（在展平后的数据上） ---
            ratios = torch.exp(new_log_probs_flat - old_log_probs_flat.detach())
            surr1 = ratios * advantages_flat
            surr2 = torch.clamp(ratios, 1.0 - self.config.clip_epsilon, 1.0 + self.config.clip_epsilon) * advantages_flat
            policy_loss = -torch.min(surr1, surr2).mean()
            
            # 价值损失
            if self.config.use_valuenorm and self.value_norm_discoverer is not None:
                # a. Critic的预测值需要被归一化，以便与归一化的目标进行比较
                values_for_loss = self._normalize_values(new_values_flat, self.value_norm_discoverer)
                # b. Critic的训练目标(returns)也需要被归一化
                returns_for_loss = self._normalize_values(returns_flat, self.value_norm_discoverer)
                value_loss = F.mse_loss(values_for_loss, returns_for_loss.detach())
            else:
                # 如果不使用ValueNorm，一切照旧
                value_loss = F.mse_loss(new_values_flat, returns_flat)
            
            # 熵损失
            entropy_loss = -entropy * self.config.lambda_l
            
            # 总损失
            if self.config.use_opt:
                # 注意：这里没有cd_loss，因为evaluate_sequence方法中没有返回CD损失
                # 如果需要CD损失，需要在evaluate_sequence中添加相应逻辑
                loss = policy_loss + self.config.value_loss_coef * value_loss + entropy_loss
            else:
                loss = policy_loss + self.config.value_loss_coef * value_loss + entropy_loss
            
            # 更新网络
            self.discoverer_optimizer.zero_grad()
            if torch.isnan(loss).any() or torch.isinf(loss).any():
                main_logger.error("Loss contains NaN or Inf! Skipping update.")
                continue # 跳过此次更新
            loss.backward()  # <--- 这一步会通过整个序列反向传播！实现真正的BPTT
            torch.nn.utils.clip_grad_norm_(self.skill_discoverer.parameters(), self.config.max_grad_norm)
            self.discoverer_optimizer.step()
            
            # 累积统计
            total_policy_loss += policy_loss.item()
            total_value_loss += value_loss.item()
            total_entropy_loss += entropy_loss.item()
            total_loss += loss.item()
            update_count += 1
            
            main_logger.debug(f"Discoverer BPTT更新 #{update_count}: "
                            f"Loss={loss.item():.6f}, Policy={policy_loss.item():.6f}, "
                            f"Value={value_loss.item():.6f}, Entropy={entropy.item():.6f}")
        
        # 计算平均损失
        avg_policy_loss = total_policy_loss / update_count if update_count > 0 else 0.0
        avg_value_loss = total_value_loss / update_count if update_count > 0 else 0.0
        avg_entropy_loss = total_entropy_loss / update_count if update_count > 0 else 0.0
        avg_total_loss = total_loss / update_count if update_count > 0 else 0.0
        
        # 计算其他统计信息（从统一rollout缓冲区获取）
        # 假设缓冲区已满，使用num_steps进行计算
        if num_steps > 0:
            # 计算平均奖励（所有环境和智能体）
            avg_intrinsic_reward = np.mean(self.rollout_buffer.rewards[:num_steps])
            # 计算平均价值（所有环境和智能体）
            avg_discoverer_value = np.mean(self.rollout_buffer.values[:num_steps])
            action_entropy_val = -avg_entropy_loss / self.config.lambda_l if self.config.lambda_l > 0 else 0.0
            # 从rollout缓冲区计算奖励组成部分的平均值（统一为"均值的均值"方法）
            # 1. 先计算每个环境内部的平均值（跨越steps和agents维度）
            env_means_env_comp = np.mean(self.rollout_buffer.rewards_env[:num_steps], axis=(0, 2))
            env_means_team_disc_comp = np.mean(self.rollout_buffer.rewards_team_disc[:num_steps], axis=(0, 2))
            env_means_ind_disc_comp = np.mean(self.rollout_buffer.rewards_ind_disc[:num_steps], axis=(0, 2))
            
            # 2. 再计算所有环境平均值的平均值
            avg_env_comp = np.mean(env_means_env_comp)
            avg_team_disc_comp = np.mean(env_means_team_disc_comp)
            avg_ind_disc_comp = np.mean(env_means_ind_disc_comp)
        else:
            avg_intrinsic_reward = 0.0
            avg_discoverer_value = 0.0
            action_entropy_val = 0.0
            avg_env_comp = 0.0
            avg_team_disc_comp = 0.0
            avg_ind_disc_comp = 0.0
        
        main_logger.info(f"Discoverer BPTT更新完成: {update_count}次更新, "
                        f"平均损失={avg_total_loss:.6f}, 平均策略损失={avg_policy_loss:.6f}, "
                        f"平均价值损失={avg_value_loss:.6f}, 平均动作熵={action_entropy_val:.6f}")
        
        return avg_total_loss, avg_policy_loss, avg_value_loss, action_entropy_val, \
               avg_intrinsic_reward, avg_env_comp, avg_team_disc_comp, avg_ind_disc_comp, avg_discoverer_value

    
    def update_discriminators(self, num_steps):
        """更新技能判别器网络（使用RolloutBuffer数据，修复多进程问题）"""
        # Now 'num_steps' is the actual amount of valid data
        total_samples = num_steps * self.rollout_buffer.num_envs * self.rollout_buffer.n_agents
        if total_samples < self.config.batch_size:
            main_logger.warning(f"RolloutBuffer中的样本数({total_samples})少于批次大小({self.config.batch_size})，跳过判别器更新")
            return 0
        
        # 从RolloutBuffer中采样数据
        # 随机选择时间步、环境和智能体
        batch_size = self.config.batch_size
        
        # 生成随机索引
        time_indices = np.random.choice(num_steps, batch_size, replace=True)
        env_indices = np.random.choice(self.rollout_buffer.num_envs, batch_size, replace=True)
        agent_indices = np.random.choice(self.rollout_buffer.n_agents, batch_size, replace=True)
        
        # 收集批次数据
        states_list = []
        team_skills_list = []
        observations_list = []
        agent_skills_list = []
        
        for i in range(batch_size):
            t, env_idx, agent_idx = time_indices[i], env_indices[i], agent_indices[i]
            
            # 获取全局状态和团队技能
            state = self.rollout_buffer.states[t, env_idx]
            team_skill = self.rollout_buffer.team_skills[t, env_idx]
            
            # 获取特定智能体的观测和技能
            observation = self.rollout_buffer.obs[t, env_idx, agent_idx]
            agent_skill = self.rollout_buffer.agent_skills[t, env_idx, agent_idx]
            
            states_list.append(state)
            team_skills_list.append(team_skill)
            observations_list.append(observation)
            agent_skills_list.append(agent_skill)
        
        # 转换为张量
        states = torch.FloatTensor(np.stack(states_list)).to(self.device)
        team_skills = torch.LongTensor(team_skills_list).to(self.device)
        observations = torch.FloatTensor(np.stack(observations_list)).to(self.device)
        agent_skills = torch.LongTensor(agent_skills_list).to(self.device)
        
        # 更新团队技能判别器
        team_disc_logits = self.team_discriminator(states)
        team_disc_loss = F.cross_entropy(team_disc_logits, team_skills)
        
        # 添加团队判别器熵正则化（防止过度自信）
        team_disc_probs = F.softmax(team_disc_logits, dim=-1)
        team_disc_entropy = -(team_disc_probs * F.log_softmax(team_disc_logits, dim=-1)).sum(dim=-1).mean()
        
        # 更新个体技能判别器
        agent_disc_logits = self.individual_discriminator(observations, team_skills)
        agent_disc_loss = F.cross_entropy(agent_disc_logits, agent_skills)
        
        # 添加个体判别器熵正则化（防止过度自信）
        agent_disc_probs = F.softmax(agent_disc_logits, dim=-1)
        agent_disc_entropy = -(agent_disc_probs * F.log_softmax(agent_disc_logits, dim=-1)).sum(dim=-1).mean()
        
        # 总技能判别器损失（添加熵正则化项）
        entropy_reg_weight = 0.1  # 熵正则化权重
        disc_loss = team_disc_loss + agent_disc_loss - entropy_reg_weight * (team_disc_entropy + agent_disc_entropy)
        
        # 更新网络
        self.discriminator_optimizer.zero_grad()
        disc_loss.backward()
        torch.nn.utils.clip_grad_norm_(
            list(self.team_discriminator.parameters()) + list(self.individual_discriminator.parameters()),
            self.config.max_grad_norm
        )
        self.discriminator_optimizer.step()
        
        # 每100步记录判别器性能监控指标（移除TensorBoard写入，只保留日志）
        if self.global_step % 100 == 0:
            with torch.no_grad():
                # 计算判别器准确率
                team_disc_acc = (team_disc_logits.argmax(dim=-1) == team_skills).float().mean()
                agent_disc_acc = (agent_disc_logits.argmax(dim=-1) == agent_skills).float().mean()
                
                # 只记录日志，不写入TensorBoard
                main_logger.debug(f"判别器更新: Team Loss={team_disc_loss.item():.4f}, Agent Loss={agent_disc_loss.item():.4f}, "
                                f"Team Acc={team_disc_acc.item():.4f}, Agent Acc={agent_disc_acc.item():.4f}, "
                                f"Team Entropy={team_disc_entropy.item():.4f}, Agent Entropy={agent_disc_entropy.item():.4f}")
        
        return disc_loss.item()
    
    def update(self, steps_in_buffer):
        """更新所有网络"""
        # 更新全局步数
        self.global_step += 1
        main_logger.debug(f"HMASDAgent.update (step {self.global_step}): 开始更新所有网络，有效步数: {steps_in_buffer}")
        
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
            
            # 记录rollout缓冲区状态（统一缓冲区）
            rollout_buffer_pos = self.global_step % self.rollout_buffer.num_steps
            rollout_buffer_full = rollout_buffer_pos == self.rollout_buffer.num_steps - 1
            main_logger.debug(f"当前rollout缓冲区状态: {rollout_buffer_pos}/{self.rollout_buffer.num_steps} (当前/总容量), 完整: {rollout_buffer_full}")
            
            # 检查高层策略数据是否足够
            high_level_data_count = np.sum(self.rollout_buffer.high_level_valid_mask[:rollout_buffer_pos])
            
            # 如果高层数据增长过慢，强制所有环境进行贡献
            if high_level_data_count < 10 and self.global_step > 5000:  # 至少需要10个高层决策样本
                main_logger.warning(f"高层策略数据增长过慢 (有效高层样本: {high_level_data_count})，强制所有环境贡献样本")
                for env_id in range(32):
                    self.force_high_level_collection[env_id] = True
                    self.env_reward_thresholds[env_id] = 0.0
            
            # 计算环境贡献分布统计（供训练脚本记录）
            contrib_data = np.zeros(32)
            for env_id, count in env_contributions.items():
                contrib_data[env_id] = count
            # 计算贡献标准差，衡量是否平衡
            contrib_std = np.std(contrib_data)
            # 计算有效贡献环境数量
            contrib_envs = np.sum(contrib_data > 0)
        
        # 更新技能判别器
        discriminator_loss = self.update_discriminators(steps_in_buffer)
        
        # 更新高层技能协调器
        coordinator_loss, coordinator_policy_loss, coordinator_value_loss, team_skill_entropy, agent_skill_entropy, \
        mean_coord_state_val, mean_coord_agent_val, mean_high_level_reward, cd_loss_val = self.update_coordinator(steps_in_buffer)
        
        # 更新低层技能发现器 - 使用新的rollout方法
        discoverer_loss, discoverer_policy_loss, discoverer_value_loss, action_entropy, \
        avg_intrinsic_reward, avg_env_comp, avg_team_disc_comp, avg_ind_disc_comp, \
        avg_discoverer_val = self.update_discoverer_from_rollout(steps_in_buffer)
        
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
        current_disc_lr = self.discoverer_optimizer.param_groups[0]['lr']
        current_discriminator_lr = self.discriminator_optimizer.param_groups[0]['lr']
        
        learning_rates = {
            'coordinator_lr': current_coord_lr,
            'discoverer_lr': current_disc_lr,
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
