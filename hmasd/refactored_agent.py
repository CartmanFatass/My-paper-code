"""
重构后的HMASD Agent - 简化的接口层
"""

import torch
import numpy as np
import os
from logger import main_logger
from hmasd.core.training_orchestrator import TrainingOrchestrator


class RefactoredHMASDAgent:
    """
    重构后的HMASD Agent - 作为简洁的接口层
    所有复杂逻辑都委托给TrainingOrchestrator处理
    """
    
    def __init__(self, config, log_dir='logs', device=None, debug=False):
        """
        初始化重构后的HMASD代理
        
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
        self.log_dir = log_dir
        
        main_logger.info(f"重构后的HMASD Agent使用设备: {self.device}")
        
        # 确保环境维度已设置
        assert config.state_dim is not None, "必须先设置state_dim"
        assert config.obs_dim is not None, "必须先设置obs_dim"
        
        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建训练流程协调器 - 这是核心组件
        self.orchestrator = TrainingOrchestrator(config, self.device)
        
        main_logger.info("重构后的HMASD Agent初始化完成")
    
    @property
    def global_step(self):
        """获取全局步数"""
        return self.orchestrator.global_step
    
    @property
    def num_timesteps(self):
        """获取时间步数（SB3兼容性）"""
        return self.orchestrator.num_timesteps
    
    @property
    def training_info(self):
        """获取训练信息"""
        return self.orchestrator.training_info
    
    def train(self, mode=True):
        """设置训练或评估模式"""
        self.orchestrator.train(mode)
    
    def eval(self):
        """设置评估模式"""
        self.orchestrator.eval()
    
    def step(self, states_batch, observations_batch, env_steps_batch, dones_batch, deterministic=False):
        """
        执行一个完整的步骤：技能分配 + 动作选择
        
        参数:
            states_batch: 批量全局状态 [num_envs, state_dim]
            observations_batch: 批量观测 [num_envs, n_agents, obs_dim]
            env_steps_batch: 每个环境的步数 [num_envs]
            dones_batch: 完成标志 [num_envs]
            deterministic: 是否使用确定性策略
            
        返回:
            actions: 批量动作 [num_envs, n_agents, action_dim]
            infos_list: 信息字典列表
        """
        return self.orchestrator.step(states_batch, observations_batch, env_steps_batch, dones_batch, deterministic)
    
    def store_transition(self, state, next_state, observations, next_observations, actions, rewards, 
                        dones, team_skill, agent_skills, action_logprobs, log_probs=None, 
                        skill_timer_for_env=None, env_id=0, values=None, rollout_step_idx=None):
        """
        存储环境交互经验
        
        参数:
            state: 当前全局状态
            next_state: 下一全局状态
            observations: 当前观测
            next_observations: 下一观测
            actions: 动作
            rewards: 奖励
            dones: 完成标志
            team_skill: 团队技能
            agent_skills: 个体技能
            action_logprobs: 动作对数概率
            log_probs: 技能对数概率字典
            skill_timer_for_env: 技能计时器
            env_id: 环境ID
            values: 价值估计
            rollout_step_idx: rollout步骤索引
            
        返回:
            reward_components: 奖励组成字典
        """
        return self.orchestrator.store_transition(
            state, next_state, observations, next_observations, actions, rewards,
            dones, team_skill, agent_skills, action_logprobs, log_probs,
            skill_timer_for_env, env_id, values, rollout_step_idx
        )
    
    def update(self, last_values, dones, steps_in_buffer):
        """
        更新所有网络
        
        参数:
            last_values: 最后一步的价值估计
            dones: 完成标志
            steps_in_buffer: 缓冲区中的步数
            
        返回:
            update_info: 更新信息字典
        """
        return self.orchestrator.update(last_values, dones, steps_in_buffer)
    
    def clear_buffers(self):
        """清空缓冲区"""
        self.orchestrator.clear_buffers()
    
    def reset_env_state(self, env_id):
        """重置指定环境的状态"""
        self.orchestrator.reset_env_state(env_id)
    
    def save_model(self, path):
        """保存模型"""
        self.orchestrator.save_model(path)
    
    def load_model(self, path):
        """加载模型"""
        self.orchestrator.load_model(path)
    
    def get_stats(self):
        """获取统计信息"""
        return self.orchestrator.get_stats()
    
    # === 兼容性方法 - 为了与现有训练脚本兼容 ===
    
    def assign_skills(self, state, observations, deterministic=False):
        """
        为所有智能体分配技能（兼容性方法）
        
        参数:
            state: 全局状态 [state_dim]
            observations: 所有智能体的观测 [n_agents, obs_dim]
            deterministic: 是否使用确定性策略
            
        返回:
            team_skill: 团队技能索引
            agent_skills: 个体技能索引列表 [n_agents]
            log_probs: 包含团队技能和个体技能log probabilities的字典
        """
        # 将单个环境的数据转换为批量格式
        states_batch = state.reshape(1, -1)
        observations_batch = observations.reshape(1, self.config.n_agents, -1)
        env_steps_batch = np.array([0])  # 假设是技能切换点
        dones_batch = np.array([False])
        
        # 调用批量方法
        team_skills, agent_skills, log_probs_list = self.orchestrator._batched_assign_skills(
            states_batch, observations_batch, env_steps_batch, dones_batch, deterministic
        )
        
        return team_skills[0], agent_skills[0], log_probs_list[0]
    
    def select_action(self, observations, agent_skills=None, deterministic=False, env_id=0, state=None):
        """
        选择动作（兼容性方法）
        
        参数:
            observations: 观测 [n_agents, obs_dim]
            agent_skills: 个体技能 [n_agents]
            deterministic: 是否使用确定性策略
            env_id: 环境ID
            state: 全局状态
            
        返回:
            actions: 动作 [n_agents, action_dim]
            action_logprobs: 动作对数概率 [n_agents]
            values: 价值估计 [n_agents]
        """
        if agent_skills is None:
            agent_skills = self.orchestrator.state_manager.get_agent_skills(env_id)
        
        if state is None:
            # 如果没有提供状态，创建一个零状态
            state = np.zeros(self.config.state_dim)
        
        # 将单个环境的数据转换为批量格式
        states_batch = state.reshape(1, -1)
        observations_batch = observations.reshape(1, self.config.n_agents, -1)
        agent_skills_batch = np.array([agent_skills])
        team_skills_batch = np.array([self.orchestrator.state_manager.get_team_skill(env_id)])
        dones_batch = np.array([False])
        
        # 调用批量方法
        actions_batch, logprobs_batch, values_batch = self.orchestrator._batched_select_action(
            states_batch, observations_batch, agent_skills_batch, team_skills_batch, dones_batch, deterministic
        )
        
        return actions_batch[0], logprobs_batch[0], values_batch[0]
    
    # === 属性访问器 - 为了与现有代码兼容 ===
    
    @property
    def skill_coordinator(self):
        """获取技能协调器网络"""
        return self.orchestrator.network_manager.skill_coordinator
    
    @property
    def skill_discoverer(self):
        """获取技能发现器网络"""
        return self.orchestrator.network_manager.skill_discoverer
    
    @property
    def team_discriminator(self):
        """获取团队判别器网络"""
        return self.orchestrator.network_manager.team_discriminator
    
    @property
    def individual_discriminator(self):
        """获取个体判别器网络"""
        return self.orchestrator.network_manager.individual_discriminator
    
    @property
    def rollout_buffer(self):
        """获取rollout缓冲区"""
        return self.orchestrator.buffer_manager.rollout_buffer
    
    @property
    def discriminator_buffer(self):
        """获取判别器缓冲区"""
        return self.orchestrator.buffer_manager.discriminator_buffer
    
    # === 环境状态访问器 ===
    
    @property
    def env_team_skills(self):
        """获取环境团队技能字典（兼容性）"""
        # 创建一个动态字典，从状态管理器获取数据
        class DynamicDict:
            def __init__(self, state_manager):
                self.state_manager = state_manager
            
            def get(self, env_id, default=None):
                return self.state_manager.get_team_skill(env_id, default)
            
            def __getitem__(self, env_id):
                return self.state_manager.get_team_skill(env_id)
            
            def __setitem__(self, env_id, value):
                self.state_manager.set_team_skill(env_id, value)
        
        return DynamicDict(self.orchestrator.state_manager)
    
    @property
    def env_agent_skills(self):
        """获取环境个体技能字典（兼容性）"""
        class DynamicDict:
            def __init__(self, state_manager):
                self.state_manager = state_manager
            
            def get(self, env_id, default=None):
                return self.state_manager.get_agent_skills(env_id, default)
            
            def __getitem__(self, env_id):
                return self.state_manager.get_agent_skills(env_id)
            
            def __setitem__(self, env_id, value):
                self.state_manager.set_agent_skills(env_id, value)
        
        return DynamicDict(self.orchestrator.state_manager)
    
    @property
    def env_log_probs(self):
        """获取环境log概率字典（兼容性）"""
        class DynamicDict:
            def __init__(self, state_manager):
                self.state_manager = state_manager
            
            def get(self, env_id, default=None):
                return self.state_manager.get_log_probs(env_id, default)
            
            def __getitem__(self, env_id):
                return self.state_manager.get_log_probs(env_id)
            
            def __setitem__(self, env_id, value):
                self.state_manager.set_log_probs(env_id, value)
        
        return DynamicDict(self.orchestrator.state_manager)
    
    @property
    def env_hidden_states(self):
        """获取环境隐藏状态字典（兼容性）"""
        class DynamicDict:
            def __init__(self, state_manager):
                self.state_manager = state_manager
            
            def get(self, key, default=None):
                if isinstance(key, str) and key.endswith('_critic'):
                    env_id = int(key.split('_')[0])
                    return self.state_manager.get_critic_hidden_state(env_id, default)
                else:
                    env_id = key
                    return self.state_manager.get_actor_hidden_state(env_id, default)
            
            def __getitem__(self, key):
                return self.get(key)
            
            def __setitem__(self, key, value):
                if isinstance(key, str) and key.endswith('_critic'):
                    env_id = int(key.split('_')[0])
                    self.state_manager.set_critic_hidden_state(env_id, value)
                else:
                    env_id = key
                    self.state_manager.set_actor_hidden_state(env_id, value)
        
        return DynamicDict(self.orchestrator.state_manager)
    
    @property
    def env_reward_sums(self):
        """获取环境奖励累积字典（兼容性）"""
        class DynamicDict:
            def __init__(self, state_manager):
                self.state_manager = state_manager
            
            def get(self, env_id, default=0.0):
                return self.state_manager.get_reward_sum(env_id, default)
            
            def __getitem__(self, env_id):
                return self.state_manager.get_reward_sum(env_id)
            
            def __setitem__(self, env_id, value):
                self.state_manager.set_reward_sum(env_id, value)
        
        return DynamicDict(self.orchestrator.state_manager)
    
    @property
    def env_timers(self):
        """获取环境计时器字典（兼容性）"""
        class DynamicDict:
            def __init__(self, state_manager):
                self.state_manager = state_manager
            
            def get(self, env_id, default=0):
                return self.state_manager.get_skill_timer(env_id, default)
            
            def __getitem__(self, env_id):
                return self.state_manager.get_skill_timer(env_id)
            
            def __setitem__(self, env_id, value):
                self.state_manager.set_skill_timer(env_id, value)
        
        return DynamicDict(self.orchestrator.state_manager)
