"""
状态管理器 - 统一管理环境状态、技能分配和隐藏状态
"""

import torch
import numpy as np
import threading
import time
from collections import defaultdict

from logger import main_logger


class StateManager:
    """统一的状态管理器，负责环境状态、技能分配和隐藏状态的管理"""
    
    def __init__(self, config, max_envs=64):
        self.config = config
        self.max_envs = max_envs
        self.lock = threading.RLock()
        
        # 环境状态存储
        self.env_states = {}
        self.env_access_times = {}
        
        # 技能分配存储
        self.env_team_skills = {}
        self.env_agent_skills = {}
        self.env_skill_timers = {}
        self.env_log_probs = {}
        
        # 隐藏状态存储
        self.env_hidden_states = {}  # Actor隐藏状态
        self.env_critic_hidden_states = {}  # Critic隐藏状态
        
        # 奖励累积
        self.env_reward_sums = {}
        
        # 清理配置
        self.cleanup_threshold = 3600  # 1小时未使用则清理
        
        main_logger.info(f"状态管理器初始化完成，最大环境数: {max_envs}")
    
    def get_env_state(self, env_id, key, default=None):
        """线程安全地获取环境状态"""
        with self.lock:
            self.env_access_times[env_id] = time.time()
            return self.env_states.get(env_id, {}).get(key, default)
    
    def set_env_state(self, env_id, key, value):
        """线程安全地设置环境状态"""
        with self.lock:
            if len(self.env_states) >= self.max_envs and env_id not in self.env_states:
                self._cleanup_oldest()
            
            if env_id not in self.env_states:
                self.env_states[env_id] = {}
            
            self.env_states[env_id][key] = value
            self.env_access_times[env_id] = time.time()
    
    def get_team_skill(self, env_id):
        """获取环境的团队技能"""
        with self.lock:
            return self.env_team_skills.get(env_id, -1)
    
    def set_team_skill(self, env_id, team_skill):
        """设置环境的团队技能"""
        with self.lock:
            self.env_team_skills[env_id] = team_skill
            self.env_access_times[env_id] = time.time()
    
    def get_agent_skills(self, env_id):
        """获取环境的个体技能"""
        with self.lock:
            return self.env_agent_skills.get(env_id, np.full(self.config.n_agents, -1, dtype=int))
    
    def set_agent_skills(self, env_id, agent_skills):
        """设置环境的个体技能"""
        with self.lock:
            self.env_agent_skills[env_id] = np.array(agent_skills)
            self.env_access_times[env_id] = time.time()
    
    def get_skill_timer(self, env_id):
        """获取环境的技能计时器"""
        with self.lock:
            return self.env_skill_timers.get(env_id, 0)
    
    def set_skill_timer(self, env_id, timer):
        """设置环境的技能计时器"""
        with self.lock:
            self.env_skill_timers[env_id] = timer
            self.env_access_times[env_id] = time.time()
    
    def increment_skill_timer(self, env_id):
        """增加环境的技能计时器"""
        with self.lock:
            self.env_skill_timers[env_id] = self.env_skill_timers.get(env_id, 0) + 1
            self.env_access_times[env_id] = time.time()
            return self.env_skill_timers[env_id]
    
    def reset_skill_timer(self, env_id):
        """重置环境的技能计时器"""
        with self.lock:
            self.env_skill_timers[env_id] = 0
            self.env_access_times[env_id] = time.time()
    
    def get_log_probs(self, env_id):
        """获取环境的技能log概率"""
        with self.lock:
            return self.env_log_probs.get(env_id, {})
    
    def set_log_probs(self, env_id, log_probs):
        """设置环境的技能log概率"""
        with self.lock:
            self.env_log_probs[env_id] = log_probs
            self.env_access_times[env_id] = time.time()
    
    def get_actor_hidden_state(self, env_id):
        """获取环境的Actor隐藏状态"""
        with self.lock:
            return self.env_hidden_states.get(env_id)
    
    def set_actor_hidden_state(self, env_id, hidden_state):
        """设置环境的Actor隐藏状态"""
        with self.lock:
            self.env_hidden_states[env_id] = hidden_state
            self.env_access_times[env_id] = time.time()
    
    def get_critic_hidden_state(self, env_id):
        """获取环境的Critic隐藏状态"""
        with self.lock:
            critic_key = f"{env_id}_critic"
            return self.env_critic_hidden_states.get(critic_key)
    
    def set_critic_hidden_state(self, env_id, hidden_state):
        """设置环境的Critic隐藏状态"""
        with self.lock:
            critic_key = f"{env_id}_critic"
            self.env_critic_hidden_states[critic_key] = hidden_state
            self.env_access_times[env_id] = time.time()
    
    def get_reward_sum(self, env_id):
        """获取环境的累积奖励"""
        with self.lock:
            return self.env_reward_sums.get(env_id, 0.0)
    
    def add_reward(self, env_id, reward):
        """增加环境的累积奖励"""
        with self.lock:
            self.env_reward_sums[env_id] = self.env_reward_sums.get(env_id, 0.0) + reward
            self.env_access_times[env_id] = time.time()
            return self.env_reward_sums[env_id]
    
    def reset_reward_sum(self, env_id):
        """重置环境的累积奖励"""
        with self.lock:
            self.env_reward_sums[env_id] = 0.0
            self.env_access_times[env_id] = time.time()
    
    def reset_env_state(self, env_id):
        """重置指定环境的所有状态"""
        with self.lock:
            # 重置技能状态
            self.env_team_skills[env_id] = -1
            self.env_agent_skills[env_id] = np.full(self.config.n_agents, -1, dtype=int)
            self.env_skill_timers[env_id] = 0
            self.env_log_probs[env_id] = {}
            
            # 重置隐藏状态
            self.env_hidden_states[env_id] = None
            critic_key = f"{env_id}_critic"
            self.env_critic_hidden_states[critic_key] = None
            
            # 重置奖励累积
            self.env_reward_sums[env_id] = 0.0
            
            # 更新访问时间
            self.env_access_times[env_id] = time.time()
            
            main_logger.debug(f"环境 {env_id} 的状态已重置")
    
    def should_reassign_skills(self, env_id, env_step, done):
        """判断是否应该重新分配技能"""
        timer = self.get_skill_timer(env_id)
        return (timer % self.config.k == 0) or done
    
    def assign_random_skills(self, env_id):
        """为环境分配随机技能"""
        with self.lock:
            # 随机分配团队技能
            random_team_skill = np.random.randint(0, self.config.n_Z)
            # 随机分配个体技能
            random_agent_skills = np.random.randint(0, self.config.n_z, size=self.config.n_agents)
            
            self.env_team_skills[env_id] = random_team_skill
            self.env_agent_skills[env_id] = random_agent_skills
            
            # 创建对应的log_probs（使用均匀分布的log概率）
            uniform_team_log_prob = -np.log(self.config.n_Z)
            uniform_agent_log_probs = [-np.log(self.config.n_z)] * self.config.n_agents
            
            self.env_log_probs[env_id] = {
                'team_log_prob': uniform_team_log_prob,
                'agent_log_probs': uniform_agent_log_probs
            }
            
            self.env_access_times[env_id] = time.time()
            
            main_logger.debug(f"环境 {env_id} 分配随机技能: 团队={random_team_skill}, 个体={random_agent_skills}")
            
            return random_team_skill, random_agent_skills, self.env_log_probs[env_id]
    
    def _cleanup_oldest(self):
        """清理最旧的环境状态（内部方法，需要在锁内调用）"""
        if not self.env_access_times:
            return
        
        oldest_env = min(self.env_access_times, key=self.env_access_times.get)
        
        # 清理所有相关状态
        self.env_states.pop(oldest_env, None)
        self.env_team_skills.pop(oldest_env, None)
        self.env_agent_skills.pop(oldest_env, None)
        self.env_skill_timers.pop(oldest_env, None)
        self.env_log_probs.pop(oldest_env, None)
        self.env_hidden_states.pop(oldest_env, None)
        self.env_reward_sums.pop(oldest_env, None)
        
        critic_key = f"{oldest_env}_critic"
        self.env_critic_hidden_states.pop(critic_key, None)
        
        self.env_access_times.pop(oldest_env, None)
        
        main_logger.debug(f"清理最旧的环境状态: env_id={oldest_env}")
    
    def cleanup_inactive(self, timeout=None):
        """清理超时未使用的环境状态"""
        if timeout is None:
            timeout = self.cleanup_threshold
        
        with self.lock:
            current_time = time.time()
            to_remove = [env_id for env_id, last_access in self.env_access_times.items()
                        if current_time - last_access > timeout]
            
            for env_id in to_remove:
                # 清理所有相关状态
                self.env_states.pop(env_id, None)
                self.env_team_skills.pop(env_id, None)
                self.env_agent_skills.pop(env_id, None)
                self.env_skill_timers.pop(env_id, None)
                self.env_log_probs.pop(env_id, None)
                self.env_hidden_states.pop(env_id, None)
                self.env_reward_sums.pop(env_id, None)
                
                critic_key = f"{env_id}_critic"
                self.env_critic_hidden_states.pop(critic_key, None)
                
                self.env_access_times.pop(env_id, None)
            
            if to_remove:
                main_logger.info(f"清理了 {len(to_remove)} 个超时环境状态: {to_remove}")
    
    def get_stats(self):
        """获取状态管理器统计信息"""
        with self.lock:
            return {
                'active_envs': len(self.env_access_times),
                'max_envs': self.max_envs,
                'oldest_access': min(self.env_access_times.values()) if self.env_access_times else None,
                'newest_access': max(self.env_access_times.values()) if self.env_access_times else None,
                'total_states': len(self.env_states),
                'total_skills': len(self.env_team_skills),
                'total_hidden_states': len(self.env_hidden_states) + len(self.env_critic_hidden_states)
            }
    
    def get_all_env_ids(self):
        """获取所有活跃的环境ID"""
        with self.lock:
            return list(self.env_access_times.keys())
    
    def batch_get_skills(self, env_ids):
        """批量获取多个环境的技能"""
        with self.lock:
            team_skills = []
            agent_skills = []
            log_probs = []
            
            for env_id in env_ids:
                team_skills.append(self.env_team_skills.get(env_id, -1))
                agent_skills.append(self.env_agent_skills.get(env_id, np.full(self.config.n_agents, -1, dtype=int)))
                log_probs.append(self.env_log_probs.get(env_id, {}))
                self.env_access_times[env_id] = time.time()
            
            return team_skills, agent_skills, log_probs
    
    def batch_set_skills(self, env_ids, team_skills, agent_skills, log_probs):
        """批量设置多个环境的技能"""
        with self.lock:
            current_time = time.time()
            for i, env_id in enumerate(env_ids):
                self.env_team_skills[env_id] = team_skills[i]
                self.env_agent_skills[env_id] = np.array(agent_skills[i])
                self.env_log_probs[env_id] = log_probs[i]
                self.env_access_times[env_id] = current_time
