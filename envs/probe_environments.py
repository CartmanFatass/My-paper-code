"""
探针环境 (Probe Environments)
用于在极简环境中测试HMASD系统的各个组件

基于论文"Debugging Reinforcement Learning Systems"的建议，
这些环境被设计为尽可能简单，以便独立验证系统组件的正确性。
"""

import numpy as np
import gym
from gym import spaces
from typing import Dict, Any, Tuple, List
from logger import main_logger


class ProbeEnvironment:
    """探针环境基类"""
    
    def __init__(self, n_agents: int = 2):
        self.n_agents = n_agents
        self.current_step = 0
        self.max_steps = 5
        self.done = False
        
    def reset(self):
        """重置环境"""
        self.current_step = 0
        self.done = False
        return self._get_observations(), self._get_state()
    
    def step(self, actions):
        """执行一步"""
        self.current_step += 1
        
        # 计算奖励
        reward = self._compute_reward(actions)
        
        # 检查是否结束
        self.done = self._is_done()
        
        # 获取新的观测和状态
        obs = self._get_observations()
        state = self._get_state()
        
        # 创建info字典
        info = {
            'step': self.current_step,
            'max_steps': self.max_steps,
            'episode_reward': reward
        }
        
        return obs, state, reward, self.done, info
    
    def _get_observations(self):
        """获取观测（子类实现）"""
        raise NotImplementedError
    
    def _get_state(self):
        """获取全局状态（子类实现）"""
        raise NotImplementedError
    
    def _compute_reward(self, actions):
        """计算奖励（子类实现）"""
        raise NotImplementedError
    
    def _is_done(self):
        """检查是否结束"""
        return self.current_step >= self.max_steps


class ValueFunctionProbe(ProbeEnvironment):
    """
    探针环境1：价值函数测试
    
    设置：
    - 单一状态，单一动作
    - 固定奖励 +1
    - Episode长度为5
    
    目标：
    验证SkillDiscoverer的价值函数能否学会预测正确的折扣回报
    在gamma=0.99时，第一步的价值应收敛到 1 + 0.99 + 0.99^2 + 0.99^3 + 0.99^4 ≈ 4.9
    """
    
    def __init__(self, n_agents: int = 2):
        super().__init__(n_agents)
        self.obs_dim = 1  # 单一观测维度
        self.state_dim = 1  # 单一状态维度
        self.action_dim = 1  # 单一动作维度
        self.action_bound = 1.0
        
        # 理论价值（gamma=0.99）
        gamma = 0.99
        self.theoretical_value = sum([gamma**i for i in range(self.max_steps)])
        
        main_logger.info(f"ValueFunctionProbe初始化: 理论价值={self.theoretical_value:.4f}")
    
    def _get_observations(self):
        """所有智能体观测相同的单一状态"""
        obs = np.ones((self.n_agents, self.obs_dim), dtype=np.float32)
        return obs
    
    def _get_state(self):
        """全局状态也是单一值"""
        return np.ones(self.state_dim, dtype=np.float32)
    
    def _compute_reward(self, actions):
        """固定奖励+1"""
        return 1.0
    
    def get_expected_value(self, gamma=0.99):
        """获取期望的价值函数值"""
        return self.theoretical_value


class PolicyProbe(ProbeEnvironment):
    """
    探针环境2：低层策略测试
    
    设置：
    - 两个状态 {S0, S1}
    - 在S0，动作A(>0)导致+1奖励并结束，动作B(<=0)导致-1奖励并结束
    
    目标：
    验证SkillDiscoverer的Actor能否在给定固定技能的情况下学会选择正确动作
    """
    
    def __init__(self, n_agents: int = 2):
        super().__init__(n_agents)
        self.obs_dim = 1
        self.state_dim = 1
        self.action_dim = 1
        self.action_bound = 2.0
        self.max_steps = 5
        
        # 随机初始化状态（0或1）
        self.current_state = 0
        
        main_logger.info("PolicyProbe初始化: 动作>0获得+1奖励，动作<=0获得-1奖励")
    
    def reset(self):
        """重置环境，随机选择初始状态"""
        self.current_step = 0
        self.done = False
        self.current_state = np.random.randint(0, 2)  # 随机选择状态0或1
        return self._get_observations(), self._get_state()
    
    def _get_observations(self):
        """返回当前状态的标量编码"""
        obs = np.full((self.n_agents, self.obs_dim), float(self.current_state), dtype=np.float32)
        return obs
    
    def _get_state(self):
        """全局状态"""
        state = np.array([float(self.current_state)], dtype=np.float32)
        return state
    
    def _compute_reward(self, actions):
        """根据动作计算奖励"""
        # 取第一个智能体的动作作为代表
        action = actions[0, 0] if len(actions.shape) > 1 else actions[0]
        
        if action > 0:
            reward = 1.0
        else:
            reward = -1.0
            
        main_logger.debug(f"PolicyProbe: 状态={self.current_state}, 动作={action:.3f}, 奖励={reward}")
        return reward
    
    def _is_done(self):
        """检查是否结束"""
        return self.current_step >= self.max_steps


class DiscriminatorProbe(ProbeEnvironment):
    """
    探针环境3：判别器测试
    
    设置：
    - 两个状态 {SA, SB}
    - 智能体只有一个动作，但有两个技能 {0, 1}
    - 如果分配技能0，进入SA并获得+1奖励
    - 如果分配技能1，进入SB并获得+1奖励
    
    目标：
    验证TeamDiscriminator能否学会将状态SA与技能0关联，状态SB与技能1关联
    """
    
    def __init__(self, n_agents: int = 2):
        super().__init__(n_agents)
        self.obs_dim = 1
        self.state_dim = 2
        self.action_dim = 1
        self.action_bound = 1.0
        self.max_steps = 5
        
        # 状态将由分配的技能决定
        self.current_state = 0
        self.assigned_team_skill = 0
        
        main_logger.info("DiscriminatorProbe初始化: 技能0->状态A, 技能1->状态B")
    
    def reset(self):
        """重置环境"""
        self.current_step = 0
        self.done = False
        # 状态将在set_skill中设置
        return self._get_observations(), self._get_state()
    
    def set_skill(self, team_skill: int):
        """设置技能，这将决定环境状态"""
        self.assigned_team_skill = team_skill
        # 技能0对应状态0，技能1对应状态1
        self.current_state = team_skill % 2
        main_logger.debug(f"DiscriminatorProbe: 分配技能={team_skill}, 对应状态={self.current_state}")
    
    def _get_observations(self):
        """返回当前状态的标量编码"""
        obs = np.full((self.n_agents, self.obs_dim), float(self.current_state), dtype=np.float32)
        return obs
    
    def _get_state(self):
        """全局状态 - one-hot编码"""
        state = np.zeros(self.state_dim, dtype=np.float32)
        state[self.current_state] = 1.0
        return state
    
    def _compute_reward(self, actions):
        """固定奖励+1（重点是状态-技能关联，不是奖励）"""
        return 1.0
    
    def _is_done(self):
        """检查是否结束"""
        return self.current_step >= self.max_steps
    
    def get_state_skill_pair(self):
        """获取当前的状态-技能对，用于判别器训练"""
        return self.current_state, self.assigned_team_skill


class ProbeEnvironmentWrapper:
    """
    探针环境包装器，使其兼容HMASD训练循环
    """
    
    def __init__(self, probe_env: ProbeEnvironment):
        self.env = probe_env
        self.n_agents = probe_env.n_agents
        self.obs_dim = probe_env.obs_dim
        self.state_dim = probe_env.state_dim
        self.action_dim = probe_env.action_dim
        self.action_bound = probe_env.action_bound
        
        # 为兼容性添加的属性
        self.num_envs = 1  # 单环境
        
    def reset(self):
        """重置环境"""
        obs, state = self.env.reset()
        
        # 返回格式：([obs], [state])，兼容多环境训练循环
        return [obs], [state]
    
    def step(self, actions_list):
        """执行步骤"""
        # actions_list是一个列表，包含每个环境的动作
        actions = actions_list[0]  # 只有一个环境
        
        obs, state, reward, done, info = self.env.step(actions)
        
        # 返回格式兼容多环境
        return [obs], [state], [reward], [done], [info]
    
    def set_skill(self, team_skill: int):
        """设置技能（仅对DiscriminatorProbe有效）"""
        if hasattr(self.env, 'set_skill'):
            self.env.set_skill(team_skill)
    
    def get_expected_value(self, gamma=0.99):
        """获取期望价值（仅对ValueFunctionProbe有效）"""
        if hasattr(self.env, 'get_expected_value'):
            return self.env.get_expected_value(gamma)
        return None
    
    def get_state_skill_pair(self):
        """获取状态-技能对（仅对DiscriminatorProbe有效）"""
        if hasattr(self.env, 'get_state_skill_pair'):
            return self.env.get_state_skill_pair()
        return None, None


def create_probe_environment(env_type: str, n_agents: int = 2) -> ProbeEnvironmentWrapper:
    """
    创建探针环境的工厂函数
    
    参数:
        env_type: 环境类型 ('value', 'policy', 'discriminator')
        n_agents: 智能体数量
        
    返回:
        包装后的探针环境
    """
    if env_type == 'value':
        env = ValueFunctionProbe(n_agents)
    elif env_type == 'policy':
        env = PolicyProbe(n_agents)
    elif env_type == 'discriminator':
        env = DiscriminatorProbe(n_agents)
    else:
        raise ValueError(f"未知的探针环境类型: {env_type}")
    
    return ProbeEnvironmentWrapper(env)


# 测试函数
def test_probe_environments():
    """测试所有探针环境"""
    main_logger.info("开始测试探针环境...")
    
    # 测试价值函数探针
    main_logger.info("=" * 50)
    main_logger.info("测试价值函数探针")
    value_env = create_probe_environment('value', n_agents=2)
    obs_list, state_list = value_env.reset()
    main_logger.info(f"初始观测形状: {obs_list[0].shape}")
    main_logger.info(f"初始状态形状: {state_list[0].shape}")
    main_logger.info(f"期望价值: {value_env.get_expected_value():.4f}")
    
    # 执行几步
    for step in range(3):
        actions = [np.random.randn(2, 1)]  # 随机动作
        obs_list, state_list, rewards, dones, infos = value_env.step(actions)
        main_logger.info(f"步骤{step+1}: 奖励={rewards[0]}, 完成={dones[0]}")
    
    # 测试策略探针
    main_logger.info("=" * 50)
    main_logger.info("测试策略探针")
    policy_env = create_probe_environment('policy', n_agents=2)
    
    for episode in range(3):
        obs_list, state_list = policy_env.reset()
        main_logger.info(f"Episode {episode+1}: 初始状态={np.argmax(state_list[0])}")
        
        # 测试正动作和负动作
        for action_val in [1.0, -1.0]:
            actions = [np.full((2, 1), action_val)]
            obs_list, state_list, rewards, dones, infos = policy_env.step(actions)
            main_logger.info(f"  动作={action_val}: 奖励={rewards[0]}")
            
            # 重置以测试下一个动作
            if not dones[0]:
                obs_list, state_list = policy_env.reset()
    
    # 测试判别器探针
    main_logger.info("=" * 50)
    main_logger.info("测试判别器探针")
    disc_env = create_probe_environment('discriminator', n_agents=2)
    
    for skill in [0, 1]:
        obs_list, state_list = disc_env.reset()
        disc_env.set_skill(skill)
        obs_list, state_list = disc_env.reset()  # 重新获取设置技能后的状态
        
        actions = [np.random.randn(2, 1)]
        obs_list, state_list, rewards, dones, infos = disc_env.step(actions)
        
        state_idx, skill_idx = disc_env.get_state_skill_pair()
        main_logger.info(f"技能{skill}: 状态={state_idx}, 奖励={rewards[0]}")
    
    main_logger.info("探针环境测试完成！")


if __name__ == "__main__":
    test_probe_environments()
