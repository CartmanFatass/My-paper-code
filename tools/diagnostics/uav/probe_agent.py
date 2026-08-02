"""
探针智能体 (Probe Agent)
基于HMASD智能体，但简化了高层策略，专注于测试低层组件

这个智能体将：
1. 禁用SkillCoordinator的动态决策
2. 使用固定的技能分配
3. 专注于测试SkillDiscoverer和判别器
"""

import torch
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from hmasd.logging import main_logger
from hmasd.agent import HMASDAgent
from config_1 import Config


class ProbeAgent(HMASDAgent):
    """
    探针智能体，继承自HMASDAgent但简化了高层策略
    """
    
    def __init__(self, config, log_dir='logs', device=None, debug=False, probe_mode='fixed_skills'):
        """
        初始化探针智能体
        
        参数:
            config: 配置对象
            log_dir: 日志目录
            device: 计算设备
            debug: 是否启用调试
            probe_mode: 探针模式
                - 'fixed_skills': 使用固定技能
                - 'random_skills': 使用随机技能
                - 'no_coordinator': 完全禁用协调器
        """
        super().__init__(config, log_dir, device, debug)
        
        self.probe_mode = probe_mode
        self.fixed_team_skill = 0
        self.fixed_agent_skills = np.zeros(config.n_agents, dtype=int)
        
        # 【关键修复】立即初始化环境状态，确保价值函数能正确调用
        self.env_team_skills[0] = self.fixed_team_skill
        self.env_agent_skills[0] = self.fixed_agent_skills.copy()
        self.current_team_skill = self.fixed_team_skill
        self.current_agent_skills = self.fixed_agent_skills.copy()
        
        # 探针模式特定的统计
        self.probe_stats = {
            'total_steps': 0,
            'skill_assignments': 0,
            'value_predictions': [],
            'policy_rewards': [],
            'discriminator_accuracies': []
        }
        
        main_logger.info(f"ProbeAgent初始化完成，模式: {probe_mode}")
        main_logger.info(f"固定团队技能: {self.fixed_team_skill}")
        main_logger.info(f"固定个体技能: {self.fixed_agent_skills}")
        main_logger.info(f"环境状态已初始化: env_team_skills[0]={self.env_team_skills[0]}")
    
    def set_fixed_skills(self, team_skill: int, agent_skills: List[int]):
        """设置固定的技能分配"""
        self.fixed_team_skill = team_skill
        self.fixed_agent_skills = np.array(agent_skills, dtype=int)
        
        # 【关键修复】同步更新环境状态，确保价值函数能正确调用
        self.env_team_skills[0] = self.fixed_team_skill
        self.env_agent_skills[0] = self.fixed_agent_skills.copy()
        self.current_team_skill = self.fixed_team_skill
        self.current_agent_skills = self.fixed_agent_skills.copy()
        
        main_logger.info(f"设置固定技能 - 团队: {team_skill}, 个体: {agent_skills}")
        main_logger.info(f"环境状态已同步更新: env_team_skills[0]={self.env_team_skills[0]}")
    
    def assign_skills(self, state, observations, deterministic=False):
        """
        重写技能分配方法，使用固定技能而不是动态决策
        """
        if self.probe_mode == 'fixed_skills':
            # 使用固定技能
            team_skill = self.fixed_team_skill
            agent_skills = self.fixed_agent_skills.copy()
            
            # 创建虚拟的log_probs（用于兼容性）
            log_probs = {
                'team_log_prob': 0.0,  # 固定技能的log概率为0
                'agent_log_probs': [0.0] * len(agent_skills)
            }
            
        elif self.probe_mode == 'random_skills':
            # 使用随机技能
            team_skill = np.random.randint(0, self.config.n_Z)
            agent_skills = np.random.randint(0, self.config.n_z, size=self.config.n_agents)
            
            # 创建均匀分布的log_probs
            uniform_team_log_prob = -np.log(self.config.n_Z)
            uniform_agent_log_probs = [-np.log(self.config.n_z)] * self.config.n_agents
            
            log_probs = {
                'team_log_prob': uniform_team_log_prob,
                'agent_log_probs': uniform_agent_log_probs
            }
            
        elif self.probe_mode == 'no_coordinator':
            # 完全禁用协调器，使用默认技能
            team_skill = 0
            agent_skills = np.zeros(self.config.n_agents, dtype=int)
            
            log_probs = {
                'team_log_prob': 0.0,
                'agent_log_probs': [0.0] * self.config.n_agents
            }
        
        else:
            # 回退到原始的动态分配
            return super().assign_skills(state, observations, deterministic)
        
        self.probe_stats['skill_assignments'] += 1
        
        main_logger.debug(f"ProbeAgent分配技能: 团队={team_skill}, 个体={agent_skills}")
        
        return team_skill, agent_skills, log_probs
    
    def select_action(self, observations, agent_skills=None, deterministic=False, env_id=0, state=None):
        """
        重写动作选择，添加探针模式的统计收集
        """
        actions, logprobs, values = super().select_action(
            observations, agent_skills, deterministic, env_id, state
        )
        
        # 收集价值预测统计
        if values is not None:
            mean_value = np.mean(values)
            self.probe_stats['value_predictions'].append(mean_value)
            
            # 限制统计列表长度
            if len(self.probe_stats['value_predictions']) > 1000:
                self.probe_stats['value_predictions'] = self.probe_stats['value_predictions'][-500:]
        
        self.probe_stats['total_steps'] += 1
        
        return actions, logprobs, values
    
    def store_transition(self, state, next_state, observations, next_observations, 
                         actions, rewards, dones, team_skill, agent_skills, action_logprobs, 
                         log_probs=None, skill_timer_for_env=None, env_id=0, values=None, 
                         rollout_step_idx=None):
        """
        重写存储转换，添加探针模式的奖励统计，并确保高层数据被正确存储
        """
        # 收集策略奖励统计
        if isinstance(rewards, (int, float)):
            self.probe_stats['policy_rewards'].append(rewards)
        else:
            self.probe_stats['policy_rewards'].append(np.mean(rewards))
        
        # 限制统计列表长度
        if len(self.probe_stats['policy_rewards']) > 1000:
            self.probe_stats['policy_rewards'] = self.probe_stats['policy_rewards'][-500:]
        
        # 【关键修复】确保log_probs存在，即使是固定技能模式
        if log_probs is None:
            if self.probe_mode == 'fixed_skills':
                # 为固定技能创建虚拟的log_probs
                log_probs = {
                    'team_log_prob': 0.0,  # 固定技能的log概率为0
                    'agent_log_probs': [0.0] * len(agent_skills)
                }
            else:
                # 为其他模式创建默认log_probs
                log_probs = {
                    'team_log_prob': -np.log(self.config.n_Z),
                    'agent_log_probs': [-np.log(self.config.n_z)] * len(agent_skills)
                }
        
        # 【关键修复】确保技能计时器存在
        if skill_timer_for_env is None:
            # 初始化或获取环境的技能计时器
            if env_id not in self.env_timers:
                self.env_timers[env_id] = 0
            skill_timer_for_env = self.env_timers[env_id]
            
            # 更新技能计时器
            self.env_timers[env_id] = (self.env_timers[env_id] + 1) % self.config.k
        
        # 调用父类方法
        return super().store_transition(
            state, next_state, observations, next_observations, 
            actions, rewards, dones, team_skill, agent_skills, action_logprobs, 
            log_probs, skill_timer_for_env, env_id, values, rollout_step_idx
        )
    
    def update_discriminators(self, num_steps):
        """
        重写判别器更新，添加准确率统计
        """
        discriminator_loss = super().update_discriminators(num_steps)
        
        # 计算判别器准确率（简化版本）
        if hasattr(self, 'rollout_buffer') and num_steps > 0:
            # 从rollout buffer中采样一小批数据来计算准确率
            batch_size = min(32, num_steps * self.rollout_buffer.num_envs)
            
            if batch_size > 0:
                # 随机选择时间步和环境
                time_indices = np.random.choice(num_steps, batch_size, replace=True)
                env_indices = np.random.choice(self.rollout_buffer.num_envs, batch_size, replace=True)
                
                # 收集数据
                states_list = []
                team_skills_list = []
                observations_list = []
                agent_skills_list = []
                
                for i in range(batch_size):
                    t, env_idx = time_indices[i], env_indices[i]
                    
                    states_list.append(self.rollout_buffer.states[t, env_idx])
                    team_skills_list.append(self.rollout_buffer.team_skills[t, env_idx])
                    
                    # 随机选择一个智能体
                    agent_idx = np.random.randint(0, self.rollout_buffer.n_agents)
                    observations_list.append(self.rollout_buffer.obs[t, env_idx, agent_idx])
                    agent_skills_list.append(self.rollout_buffer.agent_skills[t, env_idx, agent_idx])
                
                # 转换为张量
                states = torch.FloatTensor(np.stack(states_list)).to(self.device)
                team_skills = torch.LongTensor(team_skills_list).to(self.device)
                observations = torch.FloatTensor(np.stack(observations_list)).to(self.device)
                agent_skills = torch.LongTensor(agent_skills_list).to(self.device)
                
                # 计算准确率
                with torch.no_grad():
                    team_disc_logits = self.team_discriminator(states)
                    team_predictions = team_disc_logits.argmax(dim=-1)
                    team_accuracy = (team_predictions == team_skills).float().mean().item()
                    
                    agent_disc_logits = self.individual_discriminator(observations, team_skills)
                    agent_predictions = agent_disc_logits.argmax(dim=-1)
                    agent_accuracy = (agent_predictions == agent_skills).float().mean().item()
                    
                    overall_accuracy = (team_accuracy + agent_accuracy) / 2
                    self.probe_stats['discriminator_accuracies'].append(overall_accuracy)
                    
                    # 限制统计列表长度
                    if len(self.probe_stats['discriminator_accuracies']) > 100:
                        self.probe_stats['discriminator_accuracies'] = self.probe_stats['discriminator_accuracies'][-50:]
                    
                    main_logger.debug(f"判别器准确率: 团队={team_accuracy:.3f}, 个体={agent_accuracy:.3f}, 总体={overall_accuracy:.3f}")
        
        return discriminator_loss
    
    def get_probe_statistics(self) -> Dict[str, Any]:
        """获取探针模式的统计信息"""
        stats = self.probe_stats.copy()
        
        # 计算统计摘要
        if self.probe_stats['value_predictions']:
            stats['value_mean'] = np.mean(self.probe_stats['value_predictions'])
            stats['value_std'] = np.std(self.probe_stats['value_predictions'])
            stats['value_min'] = np.min(self.probe_stats['value_predictions'])
            stats['value_max'] = np.max(self.probe_stats['value_predictions'])
        
        if self.probe_stats['policy_rewards']:
            stats['reward_mean'] = np.mean(self.probe_stats['policy_rewards'])
            stats['reward_std'] = np.std(self.probe_stats['policy_rewards'])
            stats['reward_min'] = np.min(self.probe_stats['policy_rewards'])
            stats['reward_max'] = np.max(self.probe_stats['policy_rewards'])
        
        if self.probe_stats['discriminator_accuracies']:
            stats['disc_accuracy_mean'] = np.mean(self.probe_stats['discriminator_accuracies'])
            stats['disc_accuracy_std'] = np.std(self.probe_stats['discriminator_accuracies'])
            stats['disc_accuracy_latest'] = self.probe_stats['discriminator_accuracies'][-1]
        
        return stats
    
    def log_probe_statistics(self):
        """记录探针统计信息到日志"""
        stats = self.get_probe_statistics()
        
        main_logger.info("=" * 60)
        main_logger.info("探针智能体统计报告")
        main_logger.info("=" * 60)
        main_logger.info(f"模式: {self.probe_mode}")
        main_logger.info(f"总步数: {stats['total_steps']}")
        main_logger.info(f"技能分配次数: {stats['skill_assignments']}")
        
        if 'value_mean' in stats:
            main_logger.info(f"价值预测统计:")
            main_logger.info(f"  均值: {stats['value_mean']:.4f}")
            main_logger.info(f"  标准差: {stats['value_std']:.4f}")
            main_logger.info(f"  范围: [{stats['value_min']:.4f}, {stats['value_max']:.4f}]")
        
        if 'reward_mean' in stats:
            main_logger.info(f"奖励统计:")
            main_logger.info(f"  均值: {stats['reward_mean']:.4f}")
            main_logger.info(f"  标准差: {stats['reward_std']:.4f}")
            main_logger.info(f"  范围: [{stats['reward_min']:.4f}, {stats['reward_max']:.4f}]")
        
        if 'disc_accuracy_mean' in stats:
            main_logger.info(f"判别器准确率:")
            main_logger.info(f"  平均: {stats['disc_accuracy_mean']:.3f}")
            main_logger.info(f"  最新: {stats['disc_accuracy_latest']:.3f}")
        
        main_logger.info("=" * 60)
    
    def reset_probe_statistics(self):
        """重置探针统计信息"""
        self.probe_stats = {
            'total_steps': 0,
            'skill_assignments': 0,
            'value_predictions': [],
            'policy_rewards': [],
            'discriminator_accuracies': []
        }
        main_logger.info("探针统计信息已重置")


def create_probe_agent(config, probe_mode='fixed_skills', log_dir='logs/probe', device=None):
    """
    创建探针智能体的工厂函数
    
    参数:
        config: 配置对象
        probe_mode: 探针模式
        log_dir: 日志目录
        device: 计算设备
        
    返回:
        ProbeAgent实例
    """
    # 确保配置适合探针测试
    probe_config = config
    
    # 为探针测试调整一些配置
    if not hasattr(probe_config, 'rollout_length'):
        probe_config.rollout_length = 64  # 较短的rollout用于快速测试
    
    if not hasattr(probe_config, 'batch_size'):
        probe_config.batch_size = 32  # 较小的批次大小
    
    # 创建探针智能体
    agent = ProbeAgent(
        config=probe_config,
        log_dir=log_dir,
        device=device,
        debug=True,  # 启用调试模式
        probe_mode=probe_mode
    )
    
    main_logger.info(f"创建探针智能体成功，模式: {probe_mode}")
    
    return agent


# 测试函数
def test_probe_agent():
    """测试探针智能体"""
    main_logger.info("开始测试探针智能体...")
    
    # 创建简单的配置
    config = Config()
    config.state_dim = 2
    config.obs_dim = 2
    config.action_dim = 1
    config.n_agents = 2
    config.n_Z = 2
    config.n_z = 2
    config.action_bound = 1.0
    
    # 测试不同的探针模式
    for mode in ['fixed_skills', 'random_skills', 'no_coordinator']:
        main_logger.info(f"\n测试模式: {mode}")
        
        agent = create_probe_agent(config, probe_mode=mode)
        
        # 模拟一些交互
        state = np.array([1.0, 0.0])
        observations = np.array([[1.0, 0.0], [0.0, 1.0]])
        
        # 测试技能分配
        team_skill, agent_skills, log_probs = agent.assign_skills(state, observations)
        main_logger.info(f"分配的技能: 团队={team_skill}, 个体={agent_skills}")
        
        # 测试动作选择
        actions, logprobs, values = agent.select_action(observations, agent_skills, state=state)
        main_logger.info(f"选择的动作: {actions}")
        main_logger.info(f"价值估计: {values}")
        
        # 获取统计信息
        stats = agent.get_probe_statistics()
        main_logger.info(f"统计信息: {stats}")
    
    main_logger.info("探针智能体测试完成！")


if __name__ == "__main__":
    test_probe_agent()
