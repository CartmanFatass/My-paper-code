"""
线程安全改进建议 - 为HMASD平行环境训练添加额外的安全保护
"""

import threading
from collections import defaultdict
import numpy as np

class ThreadSafeHMASDAgent:
    """线程安全的HMASD代理改进版本"""
    
    def __init__(self, config, **kwargs):
        # 原有初始化...
        
        # 添加线程锁
        self._buffer_lock = threading.RLock()  # 可重入锁
        self._env_state_lock = threading.RLock()
        self._stats_lock = threading.RLock()
        
        # 线程安全的环境状态管理
        self._env_states = {}
        
    def store_rollout_step(self, t, state, observations, actions, rewards, dones, 
                          values, log_probs, gru_hidden_states, env_id, **kwargs):
        """线程安全的数据存储"""
        with self._buffer_lock:
            # 检查是否已经存储过这个时间步和环境的数据
            if hasattr(self.rollout_buffer, '_stored_steps'):
                key = (t, env_id)
                if key in self.rollout_buffer._stored_steps:
                    main_logger.warning(f"检测到重复存储尝试: t={t}, env_id={env_id}")
                    return False
                self.rollout_buffer._stored_steps.add(key)
            else:
                self.rollout_buffer._stored_steps = set()
                self.rollout_buffer._stored_steps.add((t, env_id))
            
            # 调用原有的存储方法
            return super().store_rollout_step(t, state, observations, actions, 
                                            rewards, dones, values, log_probs, 
                                            gru_hidden_states, env_id, **kwargs)
    
    def _update_env_state_safe(self, env_id, **updates):
        """线程安全的环境状态更新"""
        with self._env_state_lock:
            if env_id not in self._env_states:
                self._env_states[env_id] = {}
            
            for key, value in updates.items():
                self._env_states[env_id][key] = value
    
    def step(self, state, observations, ep_t, deterministic=False, env_id=0):
        """线程安全的步进方法"""
        # 使用锁保护环境状态访问
        with self._env_state_lock:
            # 原有的step逻辑...
            actions, info = super().step(state, observations, ep_t, deterministic, env_id)
            
            # 安全地更新环境状态
            self._update_env_state_safe(env_id, 
                                      team_skill=info['team_skill'],
                                      agent_skills=info['agent_skills'],
                                      timer=info['skill_timer'])
            
            return actions, info

class SafeRolloutBuffer:
    """线程安全的RolloutBuffer改进版本"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._write_lock = threading.RLock()
        self._stored_steps = set()  # 跟踪已存储的(t, env_id)对
        
    def add(self, t, env_idx, **kwargs):
        """线程安全的数据添加"""
        with self._write_lock:
            # 检查重复存储
            key = (t, env_idx)
            if key in self._stored_steps:
                main_logger.warning(f"SafeRolloutBuffer: 阻止重复存储 t={t}, env_idx={env_idx}")
                return False
            
            # 调用原有的add方法
            success = super().add(t, env_idx, **kwargs)
            
            if success:
                self._stored_steps.add(key)
            
            return success
    
    def reset(self):
        """重置时清除存储记录"""
        with self._write_lock:
            self._stored_steps.clear()
            super().reset()

# 使用示例和验证函数
def validate_parallel_safety():
    """验证平行环境训练的数据安全性"""
    
    # 1. 检查数据一致性
    def check_data_consistency(rollout_buffer, num_steps, num_envs):
        """检查缓冲区数据的一致性"""
        issues = []
        
        for t in range(num_steps):
            for env_id in range(num_envs):
                # 检查观测数据是否合理
                obs = rollout_buffer.obs[t, env_id]
                if np.any(np.isnan(obs)) or np.any(np.isinf(obs)):
                    issues.append(f"无效观测数据: t={t}, env={env_id}")
                
                # 检查动作数据
                actions = rollout_buffer.actions[t, env_id]
                if np.any(np.isnan(actions)) or np.any(np.isinf(actions)):
                    issues.append(f"无效动作数据: t={t}, env={env_id}")
        
        return issues
    
    # 2. 检查环境状态同步
    def check_env_state_sync(agent, num_envs):
        """检查环境状态的同步性"""
        issues = []
        
        for env_id in range(num_envs):
            if env_id not in agent.env_team_skills:
                issues.append(f"环境{env_id}缺少团队技能状态")
            
            if env_id not in agent.env_agent_skills:
                issues.append(f"环境{env_id}缺少个体技能状态")
            
            if env_id not in agent.env_timers:
                issues.append(f"环境{env_id}缺少计时器状态")
        
        return issues
    
    return check_data_consistency, check_env_state_sync

# 监控和诊断工具
class ParallelTrainingMonitor:
    """平行训练监控器"""
    
    def __init__(self):
        self.data_access_counts = defaultdict(int)
        self.conflict_counts = defaultdict(int)
        self.lock = threading.Lock()
    
    def log_data_access(self, operation, env_id, t=None):
        """记录数据访问"""
        with self.lock:
            key = f"{operation}_env_{env_id}"
            if t is not None:
                key += f"_t_{t}"
            self.data_access_counts[key] += 1
    
    def log_conflict(self, conflict_type, env_id, t=None):
        """记录冲突"""
        with self.lock:
            key = f"{conflict_type}_env_{env_id}"
            if t is not None:
                key += f"_t_{t}"
            self.conflict_counts[key] += 1
    
    def get_report(self):
        """获取监控报告"""
        with self.lock:
            return {
                'data_accesses': dict(self.data_access_counts),
                'conflicts': dict(self.conflict_counts),
                'total_accesses': sum(self.data_access_counts.values()),
                'total_conflicts': sum(self.conflict_counts.values())
            }
