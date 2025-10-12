"""
训练流程协调器 - 统一协调整个训练流程
"""

import torch
import numpy as np
import time
from typing import Dict, Any, Tuple, List

from logger import main_logger
from hmasd.core.network_manager import NetworkManager
from hmasd.core.state_manager import StateManager
from hmasd.core.buffer_manager import BufferManager


class TrainingOrchestrator:
    """训练流程协调器，负责协调整个训练流程"""
    
    def __init__(self, config, device):
        self.config = config
        self.device = device
        
        # 创建各个管理器
        self.network_manager = NetworkManager(config, device)
        self.state_manager = StateManager(config)
        self.buffer_manager = BufferManager(config)
        
        # 训练状态
        self.global_step = 0
        self.num_timesteps = 0
        self.training = True
        
        # 内在奖励计算相关
        self._init_intrinsic_reward_components()
        
        # 权重退火相关
        self._init_reward_annealing()
        
        # 训练统计
        self.training_info = {
            'high_level_loss': [],
            'low_level_loss': [],
            'discriminator_loss': [],
            'team_skill_entropy': [],
            'agent_skill_entropy': [],
            'action_entropy': [],
            'episode_rewards': [],
            'intrinsic_reward_env_component': [],
            'intrinsic_reward_team_disc_component': [],
            'intrinsic_reward_ind_disc_component': [],
            'intrinsic_reward_low_level_average': [],
            'coordinator_state_value_mean': [],
            'coordinator_agent_value_mean': [],
            'discoverer_value_mean': []
        }
        
        main_logger.info("训练流程协调器初始化完成")
    
    def _init_intrinsic_reward_components(self):
        """初始化内在奖励计算组件"""
        # 初始化基线用于方差减少
        if not hasattr(self, 'team_disc_baseline'):
            self.team_disc_baseline = 0.0
            self.ind_disc_baseline = 0.0
            self.baseline_update_rate = 0.01
    
    def _init_reward_annealing(self):
        """初始化权重退火机制"""
        self.use_reward_annealing = getattr(self.config, 'use_reward_annealing', False)
        if self.use_reward_annealing:
            self.w_intrinsic_initial = getattr(self.config, 'w_intrinsic_initial', 3.0)
            self.w_intrinsic_final = getattr(self.config, 'w_intrinsic_final', 1.0)
            self.w_extrinsic_initial = getattr(self.config, 'w_extrinsic_initial', 0.5)
            self.w_extrinsic_final = getattr(self.config, 'w_extrinsic_final', 1.5)
            self.anneal_steps = getattr(self.config, 'anneal_steps', 1000000)
            self.anneal_schedule = getattr(self.config, 'anneal_schedule', 'linear')
            
            main_logger.info(f"已启用权重退火机制: "
                           f"内在奖励权重 {self.w_intrinsic_initial}→{self.w_intrinsic_final}, "
                           f"外部奖励权重 {self.w_extrinsic_initial}→{self.w_extrinsic_final}, "
                           f"退火步数: {self.anneal_steps}, 退火计划: {self.anneal_schedule}")
        else:
            main_logger.info("未启用权重退火机制")
    
    def train(self, mode=True):
        """设置训练或评估模式"""
        self.training = mode
        self.network_manager.train(mode)
        main_logger.info(f"训练流程协调器模式设置为: {'训练' if mode else '评估'}")
    
    def eval(self):
        """设置评估模式"""
        self.train(False)
    
    def step(self, states_batch, observations_batch, env_steps_batch, dones_batch, deterministic=False):
        """执行一个完整的步骤：技能分配 + 动作选择"""
        num_envs = states_batch.shape[0]
        
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
                'skill_timer': self.state_manager.get_skill_timer(i),
                'log_probs': log_probs_list[i],
                'env_id': i
            })
        
        return actions, infos_list
    
    def _batched_assign_skills(self, states_batch, observations_batch, env_steps_batch, dones_batch, deterministic=False):
        """批量分配技能"""
        num_envs = states_batch.shape[0]
        
        # 找出需要重新分配技能的环境
        needs_reassignment_mask = (env_steps_batch % self.config.k == 0) | dones_batch
        indices_to_update = np.where(needs_reassignment_mask)[0]
        
        # 准备最终的技能批次
        new_team_skills_batch = np.array([self.state_manager.get_team_skill(i) for i in range(num_envs)], dtype=int)
        new_agent_skills_batch = np.array([self.state_manager.get_agent_skills(i) for i in range(num_envs)], dtype=int)
        new_log_probs_batch = [self.state_manager.get_log_probs(i) for i in range(num_envs)]
        
        if len(indices_to_update) > 0:
            # 提取需要更新的状态和观测
            states_to_process = torch.FloatTensor(states_batch[indices_to_update]).to(self.device)
            obs_to_process_normalized = self.buffer_manager.normalize_observations(
                observations_batch[indices_to_update], training=self.training
            )
            obs_to_process = torch.FloatTensor(obs_to_process_normalized).to(self.device)
            
            # 批量运行SkillCoordinator
            with torch.no_grad():
                team_skills, agent_skills, Z_logits, z_logits, _, _ = self.network_manager.skill_coordinator(
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
                
                # 更新状态管理器
                new_team_skills_batch[env_idx] = team_skills[i].item()
                new_agent_skills_batch[env_idx] = agent_skills[i].cpu().numpy()
                new_log_probs_batch[env_idx] = log_probs
                
                self.state_manager.set_team_skill(env_idx, team_skills[i].item())
                self.state_manager.set_agent_skills(env_idx, agent_skills[i].cpu().numpy())
                self.state_manager.set_log_probs(env_idx, log_probs)
                self.state_manager.reset_skill_timer(env_idx)
        
        # 增加未更新环境的计时器
        indices_not_updated = np.where(~needs_reassignment_mask)[0]
        for env_idx in indices_not_updated:
            self.state_manager.increment_skill_timer(env_idx)
        
        return new_team_skills_batch, new_agent_skills_batch, new_log_probs_batch
    
    def _batched_select_action(self, states_batch, observations_batch, agent_skills_batch, 
                              team_skills_batch, dones_batch, deterministic=False):
        """批量选择动作"""
        num_envs, n_agents, _ = observations_batch.shape
        
        # 管理Actor和Critic的隐藏状态
        actor_hidden_states_batch = np.zeros((num_envs, n_agents, self.config.gru_hidden_size), dtype=np.float32)
        critic_hidden_states_batch = np.zeros((num_envs, n_agents, self.config.gru_hidden_size), dtype=np.float32)
        
        for i in range(num_envs):
            # Actor隐藏状态
            actor_hidden = self.state_manager.get_actor_hidden_state(i)
            if actor_hidden is not None:
                actor_hidden_states_batch[i] = actor_hidden.cpu().numpy()
            
            # Critic隐藏状态
            critic_hidden = self.state_manager.get_critic_hidden_state(i)
            if critic_hidden is not None:
                critic_hidden_states_batch[i] = critic_hidden.cpu().numpy()
        
        # 重置已完成环境的隐藏状态
        actor_hidden_states_batch[dones_batch] = 0.0
        critic_hidden_states_batch[dones_batch] = 0.0
        
        # 准备批量输入
        obs_flat = observations_batch.reshape(-1, self.config.obs_dim)
        obs_flat_normalized = self.buffer_manager.normalize_observations(obs_flat, training=self.training)
        skills_flat = agent_skills_batch.reshape(-1)
        actor_hidden_flat = actor_hidden_states_batch.reshape(-1, self.config.gru_hidden_size)
        
        obs_tensor = torch.FloatTensor(obs_flat_normalized).to(self.device)
        skills_tensor = torch.LongTensor(skills_flat).to(self.device)
        actor_hidden_tensor = torch.FloatTensor(actor_hidden_flat).to(self.device)
        
        with torch.no_grad():
            # 批量运行Actor网络获取动作
            actions_flat, logprobs_flat, _, new_actor_hidden_flat = self.network_manager.skill_discoverer(
                obs_tensor, skills_tensor, actor_hidden_tensor, deterministic
            )
            
            # 批量运行Critic网络获取价值估计
            states_expanded = np.repeat(states_batch, n_agents, axis=0)
            team_skills_expanded = np.repeat(team_skills_batch, n_agents, axis=0)
            
            states_expanded_normalized = self.buffer_manager.normalize_states(states_expanded, training=self.training)
            states_tensor = torch.FloatTensor(states_expanded_normalized).to(self.device)
            team_skills_tensor = torch.LongTensor(team_skills_expanded).to(self.device)
            
            critic_hidden_flat = critic_hidden_states_batch.reshape(-1, self.config.gru_hidden_size)
            critic_hidden_tensor = torch.FloatTensor(critic_hidden_flat).to(self.device)
            
            values_flat, new_critic_hidden_flat = self.network_manager.skill_discoverer.get_value(
                states_tensor, team_skills_tensor, critic_hidden_tensor
            )
        
        # Reshape输出
        action_space_type = getattr(self.config, 'action_space_type', 'continuous')
        if action_space_type == 'discrete':
            actions_batch = actions_flat.cpu().numpy().reshape(num_envs, n_agents)
        else:
            actions_batch = actions_flat.cpu().numpy().reshape(num_envs, n_agents, self.config.action_dim)
        
        logprobs_batch = logprobs_flat.cpu().numpy().reshape(num_envs, n_agents)
        values_batch = values_flat.cpu().numpy().reshape(num_envs, n_agents)
        
        new_actor_hidden_batch = new_actor_hidden_flat.reshape(num_envs, n_agents, self.config.gru_hidden_size)
        new_critic_hidden_batch = new_critic_hidden_flat.cpu().numpy().reshape(num_envs, n_agents, self.config.gru_hidden_size)
        
        # 更新内部隐藏状态
        for i in range(num_envs):
            self.state_manager.set_actor_hidden_state(i, new_actor_hidden_batch[i])
            self.state_manager.set_critic_hidden_state(i, torch.FloatTensor(new_critic_hidden_batch[i]).to(self.device))
        
        return actions_batch, logprobs_batch, values_batch
    
    def store_transition(self, state, next_state, observations, next_observations, actions, rewards, 
                        dones, team_skill, agent_skills, action_logprobs, log_probs=None, 
                        skill_timer_for_env=None, env_id=0, values=None, rollout_step_idx=None):
        """存储环境交互经验"""
        # 确保rewards是数值类型
        if isinstance(rewards, np.ndarray):
            current_reward = np.mean(rewards)
        else:
            current_reward = rewards
        
        # 更新环境特定的奖励累积
        accumulated_reward = self.state_manager.add_reward(env_id, current_reward)
        
        # 存储低层策略经验并获取奖励组成
        reward_components = self._store_discoverer_experience(
            state, next_state, observations, next_observations, actions, current_reward, 
            dones, values, action_logprobs, team_skill, agent_skills, env_id, rollout_step_idx
        )
        
        # 存储判别器数据
        self.buffer_manager.store_discriminator_data(next_state, team_skill, next_observations, agent_skills)
        
        # 处理高层策略经验存储
        skill_timer = skill_timer_for_env if skill_timer_for_env is not None else self.state_manager.get_skill_timer(env_id)
        
        # 判断是否应该存储高层经验
        any_done = np.any(dones) if hasattr(dones, '__iter__') else bool(dones)
        should_store_high_level = (skill_timer == self.config.k - 1) or any_done
        
        if should_store_high_level:
            self._store_coordinator_experience(
                state, observations, env_id, team_skill, agent_skills, 
                log_probs, dones, skill_timer, accumulated_reward, rollout_step_idx
            )
        
        return reward_components
    
    def _store_discoverer_experience(self, state, next_state, observations, next_observations, 
                                   actions, rewards, dones, values, action_logprobs, 
                                   team_skill, agent_skills, env_id, rollout_step_idx=None):
        """存储低层策略经验"""
        if values is None:
            return None
        
        n_agents = len(agent_skills)
        
        # 准备内在奖励数组
        intrinsic_rewards_array = np.zeros(n_agents)
        env_rewards_array = np.zeros(n_agents)
        team_disc_rewards_array = np.zeros(n_agents)
        ind_disc_rewards_array = np.zeros(n_agents)
        
        for i in range(n_agents):
            # 计算内在奖励
            intrinsic_reward, env_comp, team_disc_comp, ind_disc_comp, _ = self._compute_intrinsic_reward(
                next_state, rewards, next_observations[i], team_skill, agent_skills[i]
            )
            
            intrinsic_rewards_array[i] = intrinsic_reward
            env_rewards_array[i] = env_comp
            team_disc_rewards_array[i] = team_disc_comp
            ind_disc_rewards_array[i] = ind_disc_comp
        
        # 准备奖励组成字典
        reward_components = {
            'env': env_rewards_array,
            'team_disc': team_disc_rewards_array,
            'ind_disc': ind_disc_rewards_array
        }
        
        # 获取或创建环境特定的GRU隐藏状态
        actor_hidden_state = self.state_manager.get_actor_hidden_state(env_id)
        if actor_hidden_state is not None:
            if actor_hidden_state.dim() > 2:
                actor_hidden_state = actor_hidden_state.squeeze(0)
            gru_hidden_states = actor_hidden_state.expand(n_agents, -1)
        else:
            gru_hidden_states = torch.zeros(n_agents, self.config.gru_hidden_size, device=self.device)
        
        if rollout_step_idx is not None:
            t = rollout_step_idx
        else:
            t = self.global_step % self.buffer_manager.rollout_buffer.num_steps
        
        # 存储到缓冲区管理器
        self.buffer_manager.store_rollout_step(
            t=t,
            state=state,
            observations=observations,
            actions=actions,
            rewards=intrinsic_rewards_array,
            dones=dones,
            values=values,
            log_probs=action_logprobs,
            gru_hidden_states=gru_hidden_states,
            env_id=env_id,
            team_skill=team_skill,
            agent_skills=agent_skills,
            reward_components=reward_components
        )
        
        return reward_components
    
    def _store_coordinator_experience(self, state, observations, env_id, team_skill, agent_skills,
                                    log_probs, dones, skill_timer, accumulated_reward, rollout_step_idx=None):
        """存储高层策略经验"""
        # 计算高层策略的价值估计
        with torch.no_grad():
            state_tensor_for_value = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            obs_tensor_for_value = torch.FloatTensor(observations).unsqueeze(0).to(self.device)
            state_val, agent_vals, _ = self.network_manager.skill_coordinator.get_value(
                state_tensor_for_value, obs_tensor_for_value
            )
        
        if rollout_step_idx is None:
            main_logger.error("rollout_step_idx is None! Cannot store high-level experience correctly.")
            return False
        
        time_step_of_decision = rollout_step_idx - skill_timer
        if time_step_of_decision < 0:
            time_step_of_decision = 0
        
        # 存储到缓冲区管理器
        success = self.buffer_manager.store_high_level_data(
            env_id=env_id,
            time_step=time_step_of_decision,
            state_value=state_val.squeeze().cpu().numpy(),
            agent_values=[v.squeeze().cpu().numpy() for v in agent_vals],
            team_log_prob=log_probs.get('team_log_prob', 0.0),
            agent_log_probs=log_probs.get('agent_log_probs', [0.0] * self.config.n_agents),
            accumulated_reward=accumulated_reward
        )
        
        if success:
            # 重置该环境的奖励累积
            self.state_manager.reset_reward_sum(env_id)
            self.state_manager.reset_skill_timer(env_id)
        
        return success
    
    def _compute_intrinsic_reward(self, next_state, reward, next_obs, team_skill, agent_skill):
        """计算内在奖励"""
        with torch.no_grad():
            try:
                # Team Discriminator Reward
                next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0).to(self.device)
                team_disc_logits = self.network_manager.team_discriminator(next_state_tensor)
                team_disc_log_probs = torch.nn.functional.log_softmax(team_disc_logits, dim=-1)
                team_skill_log_prob = team_disc_log_probs[0, team_skill]
                team_mutual_info = team_skill_log_prob.item()
                
                # Individual Discriminator Reward
                agent_obs_tensor = torch.FloatTensor(next_obs).unsqueeze(0).to(self.device)
                team_skill_tensor = torch.tensor(team_skill, device=self.device)
                agent_disc_logits = self.network_manager.individual_discriminator(agent_obs_tensor, team_skill_tensor)
                agent_disc_log_probs = torch.nn.functional.log_softmax(agent_disc_logits, dim=-1)
                agent_skill_log_prob = agent_disc_log_probs[0, agent_skill]
                agent_mutual_info = agent_skill_log_prob.item()
                
                # Baseline Subtraction for Variance Reduction
                self.team_disc_baseline = (1 - self.baseline_update_rate) * self.team_disc_baseline + \
                                        self.baseline_update_rate * team_mutual_info
                self.ind_disc_baseline = (1 - self.baseline_update_rate) * self.ind_disc_baseline + \
                                       self.baseline_update_rate * agent_mutual_info
                
                team_disc_reward = team_mutual_info
                ind_disc_reward = agent_mutual_info
                
                # Reward Normalization and Clipping
                team_disc_reward_clipped = np.clip(team_disc_reward, -10.0, 10.0)
                ind_disc_reward_clipped = np.clip(ind_disc_reward, -10.0, 10.0)
                
                # Final Reward Computation
                env_component = self.config.lambda_e * reward
                team_disc_component = self.config.lambda_D * team_disc_reward_clipped
                ind_disc_component = self.config.lambda_d * ind_disc_reward_clipped
                
                intrinsic_reward = env_component + team_disc_component + ind_disc_component
                
                return intrinsic_reward, env_component, team_disc_component, ind_disc_component, 0.0
                
            except Exception as e:
                main_logger.error(f"Error in intrinsic reward computation: {e}")
                env_component = self.config.lambda_e * reward if hasattr(self.config, 'lambda_e') else 0.0
                return env_component, env_component, 0.0, 0.0, 0.0
    
    def update(self, last_values, dones, steps_in_buffer):
        """更新所有网络"""
        self.global_step += 1
        main_logger.debug(f"TrainingOrchestrator.update (step {self.global_step}): 开始更新所有网络，有效步数: {steps_in_buffer}")
        
        # 更新判别器
        discriminator_loss = self._update_discriminators(steps_in_buffer)
        
        # 更新高层技能协调器
        coordinator_results = self._update_coordinator(steps_in_buffer)
        
        # 更新低层技能发现器
        discoverer_results = self._update_discoverer_from_rollout(last_values, dones)
        
        # 更新学习率调度器
        self.network_manager.step_schedulers(self.global_step)
        
        # 更新训练信息
        self._update_training_info(coordinator_results, discoverer_results, discriminator_loss)
        
        # 返回更新结果
        return self._prepare_update_results(coordinator_results, discoverer_results, discriminator_loss)
    
    def _update_discriminators(self, num_steps):
        """更新技能判别器网络"""
        batch_size = self.config.batch_size
        
        # 从缓冲区管理器采样数据
        minibatch = self.buffer_manager.sample_discriminator_data(batch_size)
        if minibatch is None:
            return 0
        
        # 分离团队和个体技能的数据
        team_data = [d for d in minibatch if d['type'] == 'team']
        ind_data = [d for d in minibatch if d['type'] == 'individual']
        
        total_loss = 0.0
        team_disc_loss = torch.tensor(0.0, device=self.device)
        agent_disc_loss = torch.tensor(0.0, device=self.device)
        
        # 更新团队技能判别器
        if len(team_data) > 0:
            states = torch.FloatTensor(np.array([d['state'] for d in team_data])).to(self.device)
            team_skills = torch.LongTensor([d['skill'] for d in team_data]).to(self.device)
            
            team_disc_logits = self.network_manager.team_discriminator(states)
            team_disc_loss = torch.nn.functional.cross_entropy(team_disc_logits, team_skills)
            total_loss += team_disc_loss.item()
        
        # 更新个体技能判别器
        if len(ind_data) > 0:
            observations = torch.FloatTensor(np.array([d['obs'] for d in ind_data])).to(self.device)
            team_skills_cond = torch.LongTensor([d['team_skill'] for d in ind_data]).to(self.device)
            agent_skills = torch.LongTensor([d['skill'] for d in ind_data]).to(self.device)
            
            agent_disc_logits = self.network_manager.individual_discriminator(observations, team_skills_cond)
            agent_disc_loss = torch.nn.functional.cross_entropy(agent_disc_logits, agent_skills)
            total_loss += agent_disc_loss.item()
        
        # 总技能判别器损失
        disc_loss = team_disc_loss + agent_disc_loss
        
        # 更新网络
        if disc_loss.item() != 0:
            self.network_manager.discriminator_optimizer.zero_grad()
            disc_loss.backward()
            torch.nn.utils.clip_grad_norm_(
                list(self.network_manager.team_discriminator.parameters()) + 
                list(self.network_manager.individual_discriminator.parameters()),
                self.config.max_grad_norm
            )
            self.network_manager.discriminator_optimizer.step()
        
        return total_loss
    
    def _update_coordinator(self, num_steps):
        """更新高层技能协调器网络"""
        # 获取采样器
        coordinator_batch_size = getattr(self.config, 'coordinator_batch_size', 128)
        high_level_sampler = self.buffer_manager.get_coordinator_sampler(
            num_steps,
            getattr(self.config, 'ppo_epochs', 10),
            coordinator_batch_size
        )
        
        if high_level_sampler is None:
            main_logger.error("无法从统一rollout缓冲区获取Coordinator采样器")
            return self._get_empty_coordinator_results()
        
        # 更新Value Normalization统计量
        if self.config.use_valuenorm and self.buffer_manager.value_norm_coordinator is not None:
            all_returns = self.buffer_manager.rollout_buffer.get_all_high_level_returns(num_steps)
            if all_returns.size > 0:
                self.buffer_manager.value_norm_coordinator.update(all_returns)
        
        # 累积损失统计
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy_loss = 0.0
        total_loss = 0.0
        total_cd_loss = 0.0
        total_team_entropy = 0.0
        total_agent_entropy = 0.0
        update_count = 0
        
        for batch in high_level_sampler:
            # 提取批次数据
            observations_batch = batch['observations'].to(self.device)
            states_batch = batch['states'].to(self.device)
            team_skills_batch = batch['team_skills'].to(self.device)
            agent_skills_batch = batch['agent_skills'].to(self.device)
            
            old_team_log_probs_batch = batch['old_team_log_probs'].to(self.device)
            old_agent_log_probs_batch = batch['old_agent_log_probs'].to(self.device)
            
            team_advantages_batch = batch['team_advantages'].to(self.device)
            agent_advantages_batch = batch['agent_advantages'].to(self.device)
            team_returns_tensor = batch['team_returns'].to(self.device)
            agent_returns_tensor = batch['agent_returns'].to(self.device)
            
            # 重新评估当前策略下的log_probs和entropy
            _, _, Z_logits, z_logits_list, _, _ = self.network_manager.skill_coordinator(states_batch, observations_batch)
            
            Z_dist = torch.distributions.Categorical(logits=Z_logits)
            team_log_probs = Z_dist.log_prob(team_skills_batch)
            team_entropy = Z_dist.entropy()
            
            agent_log_probs_list = []
            agent_entropies = []
            for i in range(self.config.n_agents):
                zi_dist = torch.distributions.Categorical(logits=z_logits_list[i])
                agent_log_probs_list.append(zi_dist.log_prob(agent_skills_batch[:, i]))
                agent_entropies.append(zi_dist.entropy())
            
            agent_log_probs = torch.stack(agent_log_probs_list, dim=1)
            agent_entropies_tensor = torch.stack(agent_entropies, dim=1)
            
            # 计算总熵
            total_entropy_per_sample = team_entropy + agent_entropies_tensor.sum(dim=1)
            entropy = total_entropy_per_sample.mean()
            
            # 获取当前策略下的价值估计
            state_values, agent_values_list, _ = self.network_manager.skill_coordinator.get_value(states_batch, observations_batch)
            state_values = state_values.squeeze(-1)
            
            if agent_values_list is not None and len(agent_values_list) > 0:
                agent_values_tensor = torch.stack(agent_values_list).squeeze(-1)
            else:
                batch_size = states_batch.size(0)
                agent_values_tensor = torch.zeros(self.config.n_agents, batch_size, device=self.device)
            
            # 标准化优势
            # 【致命问题修复】移除错误的独立优势标准化
            # 团队技能和个体技能的优势来源于同一个奖励流，应保持相对尺度
            # PPO的主要优势来自裁剪，而非标准化。让原始优势值指导策略更新。
            # team_advantages_batch = (team_advantages_batch - team_advantages_batch.mean()) / (team_advantages_batch.std() + 1e-8)
            # agent_advantages_batch = (agent_advantages_batch - agent_advantages_batch.mean()) / (agent_advantages_batch.std() + 1e-8)
            
            # 计算解耦的PPO策略损失
            team_ratios = torch.exp(team_log_probs - old_team_log_probs_batch.detach())
            team_surr1 = team_ratios * team_advantages_batch
            team_surr2 = torch.clamp(team_ratios, 1.0 - self.config.clip_epsilon, 1.0 + self.config.clip_epsilon) * team_advantages_batch
            team_policy_loss = -torch.min(team_surr1, team_surr2).mean()
            
            agent_ratios = torch.exp(agent_log_probs - old_agent_log_probs_batch.detach())
            agent_surr1 = agent_ratios * agent_advantages_batch
            agent_surr2 = torch.clamp(agent_ratios, 1.0 - self.config.clip_epsilon, 1.0 + self.config.clip_epsilon) * agent_advantages_batch
            agent_policy_loss = -torch.min(agent_surr1, agent_surr2).mean()
            
            policy_loss = team_policy_loss + agent_policy_loss
            
            # 计算价值损失
            if self.config.use_valuenorm and self.buffer_manager.value_norm_coordinator is not None:
                state_values_for_loss = self.buffer_manager.normalize_values(state_values, self.buffer_manager.value_norm_coordinator)
                team_returns_for_loss = self.buffer_manager.normalize_values(team_returns_tensor, self.buffer_manager.value_norm_coordinator)
                team_value_loss = torch.nn.functional.mse_loss(state_values_for_loss, team_returns_for_loss.detach())
                
                agent_value_loss = 0.0
                for i in range(self.config.n_agents):
                    agent_values_for_loss = self.buffer_manager.normalize_values(agent_values_tensor[i], self.buffer_manager.value_norm_coordinator)
                    agent_returns_for_loss = self.buffer_manager.normalize_values(agent_returns_tensor[:, i], self.buffer_manager.value_norm_coordinator)
                    agent_value_loss += torch.nn.functional.mse_loss(agent_values_for_loss, agent_returns_for_loss.detach())
                agent_value_loss /= self.config.n_agents
            else:
                team_value_loss = torch.nn.functional.mse_loss(state_values, team_returns_tensor.detach())
                agent_value_loss = 0.0
                for i in range(self.config.n_agents):
                    agent_value_loss += torch.nn.functional.mse_loss(agent_values_tensor[i], agent_returns_tensor[:, i].detach())
                agent_value_loss /= self.config.n_agents
            
            value_loss = team_value_loss + agent_value_loss
            
            # 熵损失
            entropy_loss = -self.config.lambda_h * entropy
            
            # CD损失（如果启用OPT）
            cd_loss = torch.tensor(0.0, device=self.device)
            if getattr(self.config, 'use_opt_coordinator', False):
                _, _, cd_loss = self.network_manager.skill_coordinator.get_value(states_batch, observations_batch)
            
            # 总损失
            if getattr(self.config, 'use_opt_coordinator', False):
                loss = policy_loss + self.config.value_loss_coef * value_loss + entropy_loss + getattr(self.config, 'lambda_cd', 0.1) * cd_loss
            else:
                loss = policy_loss + self.config.value_loss_coef * value_loss + entropy_loss
            
            # 更新网络
            self.network_manager.coordinator_optimizer.zero_grad()
            if torch.isnan(loss).any() or torch.isinf(loss).any():
                main_logger.error("Loss contains NaN or Inf! Skipping update.")
                continue
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.network_manager.skill_coordinator.parameters(), self.config.max_grad_norm)
            self.network_manager.coordinator_optimizer.step()
            
            # 累积统计
            total_policy_loss += policy_loss.item()
            total_value_loss += value_loss.item()
            total_entropy_loss += entropy_loss.item()
            total_loss += loss.item()
            total_cd_loss += cd_loss.item()
            total_team_entropy += team_entropy.mean().item()
            total_agent_entropy += agent_entropies_tensor.mean().item()
            update_count += 1
        
        # 计算平均损失
        if update_count > 0:
            return {
                'avg_policy_loss': total_policy_loss / update_count,
                'avg_value_loss': total_value_loss / update_count,
                'avg_entropy_loss': total_entropy_loss / update_count,
                'avg_total_loss': total_loss / update_count,
                'avg_cd_loss': total_cd_loss / update_count,
                'avg_team_entropy': total_team_entropy / update_count,
                'avg_agent_entropy': total_agent_entropy / update_count,
                'update_count': update_count
            }
        else:
            return self._get_empty_coordinator_results()
    
    def _update_discoverer_from_rollout(self, last_values, dones):
        """更新低层技能发现器网络"""
        main_logger.info("开始使用重构后的RolloutBuffer更新Discoverer...")
        
        # 计算GAE
        self.buffer_manager.compute_advantages(last_values, dones, self.config.gamma, self.config.gae_lambda)
        
        # 累积损失统计
        total_policy_loss, total_value_loss, total_entropy_loss, total_loss = 0.0, 0.0, 0.0, 0.0
        update_count = 0
        
        ppo_epochs = getattr(self.config, 'ppo_epochs', 4)
        num_sequences_per_batch = getattr(self.config, 'sequence_batch_size', 32)
        
        # 获取采样器
        sequence_sampler = self.buffer_manager.get_discoverer_sampler(ppo_epochs, num_sequences_per_batch)
        
        if sequence_sampler is None:
            main_logger.error("无法获取Discoverer采样器，跳过更新。")
            return self._get_empty_discoverer_results()
        
        # 更新Value Normalization统计量
        if self.config.use_valuenorm and self.buffer_manager.value_norm_discoverer is not None:
            all_returns = self.buffer_manager.rollout_buffer.returns.reshape(-1)
            self.buffer_manager.value_norm_discoverer.update(all_returns)
        
        for batch in sequence_sampler:
            # 提取并转换数据
            observations_seq = batch['observations'].to(self.device)
            agent_skills_seq = batch['agent_skills'].to(self.device)
            actions_seq = batch['actions'].to(self.device)
            global_states_seq = batch['global_states'].to(self.device)
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
            new_log_probs, new_values, entropy = self.network_manager.skill_discoverer.evaluate_sequence(
                observations_seq, agent_skills_seq, actions_seq, 
                global_states_seq, team_skills_seq,
                initial_hxs, dones_seq, initial_critic_hxs=initial_critic_hxs
            )
            
            # 展平数据
            advantages_flat = advantages_seq.reshape(-1)
            returns_flat = returns_seq.reshape(-1)
            old_log_probs_flat = old_log_probs_seq.reshape(-1)
            new_log_probs_flat = new_log_probs.reshape(-1)
            new_values_flat = new_values.reshape(-1)
            masks_flat = masks_seq.reshape(-1)
            
            # 使用掩码过滤无效数据
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
            
            # 价值损失
            value_loss = torch.nn.functional.mse_loss(new_values_flat, returns_flat.detach())
            
            # 熵损失
            entropy_loss = -entropy * self.config.lambda_l
            
            # 解耦更新
            actor_loss = policy_loss + entropy_loss
            critic_loss = self.config.value_loss_coef * value_loss
            
            self.network_manager.discoverer_actor_optimizer.zero_grad()
            actor_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.network_manager.skill_discoverer.actor.parameters(), self.config.max_grad_norm)
            self.network_manager.discoverer_actor_optimizer.step()
            
            self.network_manager.discoverer_critic_optimizer.zero_grad()
            critic_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.network_manager.skill_discoverer.critic.parameters(), self.config.max_grad_norm)
            self.network_manager.discoverer_critic_optimizer.step()
            
            total_loss += (actor_loss + critic_loss).item()
            total_policy_loss += policy_loss.item()
            total_value_loss += value_loss.item()
            total_entropy_loss += entropy_loss.item()
            update_count += 1
        
        # 计算平均值
        if update_count > 0:
            return {
                'avg_loss': total_loss / update_count,
                'avg_policy_loss': total_policy_loss / update_count,
                'avg_value_loss': total_value_loss / update_count,
                'avg_entropy_loss': total_entropy_loss / update_count,
                'update_count': update_count
            }
        else:
            return self._get_empty_discoverer_results()
    
    def _get_empty_coordinator_results(self):
        """返回空的coordinator结果"""
        return {
            'avg_policy_loss': 0.0,
            'avg_value_loss': 0.0,
            'avg_entropy_loss': 0.0,
            'avg_total_loss': 0.0,
            'avg_cd_loss': 0.0,
            'avg_team_entropy': 0.0,
            'avg_agent_entropy': 0.0,
            'update_count': 0
        }
    
    def _get_empty_discoverer_results(self):
        """返回空的discoverer结果"""
        return {
            'avg_loss': 0.0,
            'avg_policy_loss': 0.0,
            'avg_value_loss': 0.0,
            'avg_entropy_loss': 0.0,
            'update_count': 0
        }
    
    def _update_training_info(self, coordinator_results, discoverer_results, discriminator_loss):
        """更新训练信息"""
        self.training_info['high_level_loss'].append(coordinator_results['avg_total_loss'])
        self.training_info['low_level_loss'].append(discoverer_results['avg_loss'])
        self.training_info['discriminator_loss'].append(discriminator_loss)
        self.training_info['team_skill_entropy'].append(coordinator_results['avg_team_entropy'])
        self.training_info['agent_skill_entropy'].append(coordinator_results['avg_agent_entropy'])
        self.training_info['action_entropy'].append(-discoverer_results['avg_entropy_loss'] / self.config.lambda_l if self.config.lambda_l > 0 else 0)
    
    def _prepare_update_results(self, coordinator_results, discoverer_results, discriminator_loss):
        """准备更新结果"""
        # 获取缓冲区数据用于统计
        data = self.buffer_manager.rollout_buffer._get_full_rollout_data()
        
        avg_intrinsic_reward = np.mean(data["rewards"]) if data and "rewards" in data else 0
        avg_env_comp = np.mean(data["reward_env"]) if data and "reward_env" in data else 0
        avg_team_disc_comp = np.mean(data["reward_team_disc"]) if data and "reward_team_disc" in data else 0
        avg_ind_disc_comp = np.mean(data["reward_ind_disc"]) if data and "reward_ind_disc" in data else 0
        avg_discoverer_val = np.mean(data["values"]) if data and "values" in data else 0
        
        return {
            'discriminator_loss': discriminator_loss,
            'coordinator_loss': coordinator_results['avg_total_loss'],
            'coordinator_policy_loss': coordinator_results['avg_policy_loss'],
            'coordinator_value_loss': coordinator_results['avg_value_loss'],
            'discoverer_loss': discoverer_results['avg_loss'],
            'discoverer_policy_loss': discoverer_results['avg_policy_loss'],
            'discoverer_value_loss': discoverer_results['avg_value_loss'],
            'team_skill_entropy': coordinator_results['avg_team_entropy'],
            'agent_skill_entropy': coordinator_results['avg_agent_entropy'],
            'action_entropy': -discoverer_results['avg_entropy_loss'] / self.config.lambda_l if self.config.lambda_l > 0 else 0,
            'avg_intrinsic_reward': avg_intrinsic_reward,
            'avg_env_comp': avg_env_comp,
            'avg_team_disc_comp': avg_team_disc_comp,
            'avg_ind_disc_comp': avg_ind_disc_comp,
            'mean_coord_state_val': 0.0,  # 需要从采样器中计算
            'mean_coord_agent_val': 0.0,  # 需要从采样器中计算
            'avg_discoverer_val': avg_discoverer_val,
            'mean_high_level_reward': 0.0,  # 需要从高层数据中计算
            'cd_loss': coordinator_results['avg_cd_loss']
        }
    
    def clear_buffers(self):
        """清空缓冲区"""
        self.buffer_manager.clear_rollout_buffer()
        
        # 重置计数器和累积值
        for env_id in self.state_manager.get_all_env_ids():
            self.state_manager.reset_reward_sum(env_id)
            self.state_manager.reset_skill_timer(env_id)
        
        # 定期清理环境状态管理器中的超时状态
        self.state_manager.cleanup_inactive()
    
    def reset_env_state(self, env_id):
        """重置指定环境的状态"""
        self.state_manager.reset_env_state(env_id)
    
    def save_model(self, path):
        """保存模型"""
        checkpoint = self.network_manager.get_checkpoint()
        
        # 添加缓冲区管理器的标准化状态
        normalization_state = self.buffer_manager.save_normalization_state()
        checkpoint.update(normalization_state)
        
        # 添加配置
        checkpoint['config'] = self.config
        
        torch.save(checkpoint, path)
        main_logger.info(f"模型已保存到 {path}")
    
    def load_model(self, path):
        """加载模型"""
        # 导入Config类并将其添加到安全列表
        from config_1 import Config
        import numpy.core.multiarray
        torch.serialization.add_safe_globals([Config, numpy.core.multiarray._reconstruct])
        
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        
        # 加载网络参数
        self.network_manager.load_checkpoint(checkpoint)
        
        # 加载标准化状态
        self.buffer_manager.load_normalization_state(checkpoint)
        
        main_logger.info(f"模型已从 {path} 加载")
    
    def get_stats(self):
        """获取统计信息"""
        return {
            'global_step': self.global_step,
            'num_timesteps': self.num_timesteps,
            'training': self.training,
            'network_stats': self.network_manager.get_stats(),
            'state_stats': self.state_manager.get_stats(),
            'buffer_stats': self.buffer_manager.get_buffer_stats()
        }
