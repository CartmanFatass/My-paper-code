import os
import time
import numpy as np
import torch
import argparse
import logging
import matplotlib.pyplot as plt
from datetime import datetime
import multiprocessing as mp
import pandas as pd
from collections import defaultdict, deque
import traceback
import sys
import gc
import psutil
from hmasd.logging import init_multiproc_logging, get_logger, shutdown_logging, LOG_LEVELS, set_log_level

# 导入 PyTorch 相关库
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.tensorboard import SummaryWriter
from torch.distributions import Categorical, Normal

# 导入 Stable Baselines3 向量化环境
from stable_baselines3.common.vec_env import SubprocVecEnv, VecEnv
from stable_baselines3.common.monitor import Monitor

# 导入配置和环境
from config_1 import Config
from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv
from envs.pettingzoo.scenario3 import UAVMultiHopEnv
from envs.pettingzoo.relay.forced_relay import UAVForcedRelayEnv
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter

# 导入工具类
from hmasd.utils import compute_gae, compute_ppo_loss

# 导入现代网络架构组件
from hmasd.networks import ResBlock, initialize_weights

class MAPPORolloutBuffer:
    """MAPPO专用的Rollout缓冲区 - 严格on-policy实现，支持多智能体数据格式，参考hmasd/utils.py的RolloutBuffer"""
    
    def __init__(self, num_steps, num_envs, n_agents, obs_dim, action_dim, state_dim):
        self.num_steps = num_steps
        self.num_envs = num_envs
        self.n_agents = n_agents
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.state_dim = state_dim
        
        # 存储rollout数据 - 按时间步组织，支持多智能体格式
        # 参考hmasd/utils.py的RolloutBuffer数据格式
        self.obs = np.zeros((num_steps, num_envs, n_agents, obs_dim), dtype=np.float32)
        self.next_obs = np.zeros((num_steps, num_envs, n_agents, obs_dim), dtype=np.float32)
        self.states = np.zeros((num_steps, num_envs, state_dim), dtype=np.float32)
        self.next_states = np.zeros((num_steps, num_envs, state_dim), dtype=np.float32)
        self.actions = np.zeros((num_steps, num_envs, n_agents, action_dim), dtype=np.float32)
        self.rewards = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)
        self.dones = np.zeros((num_steps, num_envs, n_agents), dtype=np.bool_)
        self.log_probs = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)
        self.values = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)
        
        # GAE计算结果 - 多智能体格式
        self.advantages = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)
        self.returns = np.zeros((num_steps, num_envs, n_agents), dtype=np.float32)
        
        # 当前存储位置
        self.step = 0
        self.ready_for_update = False
        
    def add(self, t, state, obs, action, reward, done, value, log_prob, gru_hidden_state, env_idx):
        """
        存储单个环境的经验数据 - 参考hmasd/utils.py的RolloutBuffer.add方法
        
        参数:
            t: 时间步索引
            state: 全局状态 [state_dim]
            obs: 观测数据 [n_agents, obs_dim]
            action: 动作数据 [n_agents, action_dim]
            reward: 奖励数据 [n_agents]
            done: 完成标志 [n_agents]
            value: 价值估计 [n_agents]
            log_prob: 对数概率 [n_agents]
            gru_hidden_state: GRU隐状态（占位符，MAPPO不使用）
            env_idx: 环境索引
        """
        # 边界检查
        if t >= self.num_steps:
            main_logger.error(f"MAPPORolloutBuffer.add: 时间步越界! t={t} >= num_steps={self.num_steps}, env_idx={env_idx}")
            return False
        
        if env_idx >= self.num_envs:
            main_logger.error(f"MAPPORolloutBuffer.add: 环境索引越界! env_idx={env_idx} >= num_envs={self.num_envs}, t={t}")
            return False
        
        try:
            # 确保所有输入都是numpy数组
            obs = np.asarray(obs, dtype=np.float32)
            action = np.asarray(action, dtype=np.float32)
            state = np.asarray(state, dtype=np.float32)
            reward = np.asarray(reward, dtype=np.float32)
            done = np.asarray(done, dtype=bool)
            value = np.asarray(value, dtype=np.float32)
            log_prob = np.asarray(log_prob, dtype=np.float32)

            # 数据形状验证 - 参考hmasd/utils.py的RolloutBuffer.add验证
            if obs.shape != (self.n_agents, self.obs_dim):
                main_logger.error(f"MAPPORolloutBuffer.add: 观测形状不匹配! 期望{(self.n_agents, self.obs_dim)}, 实际{obs.shape}, t={t}, env_idx={env_idx}")
                return False
            
            if action.shape != (self.n_agents, self.action_dim):
                main_logger.error(f"MAPPORolloutBuffer.add: 动作形状不匹配! 期望{(self.n_agents, self.action_dim)}, 实际{action.shape}, t={t}, env_idx={env_idx}")
                return False
            
            if state.shape != (self.state_dim,):
                main_logger.error(f"MAPPORolloutBuffer.add: 状态形状不匹配! 期望{(self.state_dim,)}, 实际{state.shape}, t={t}, env_idx={env_idx}")
                return False
            
            if value.shape != (self.n_agents,):
                main_logger.error(f"MAPPORolloutBuffer.add: 价值形状不匹配! 期望{(self.n_agents,)}, 实际{value.shape}, t={t}, env_idx={env_idx}")
                return False
            
            if log_prob.shape != (self.n_agents,):
                main_logger.error(f"MAPPORolloutBuffer.add: log_prob形状不匹配! 期望{(self.n_agents,)}, 实际{log_prob.shape}, t={t}, env_idx={env_idx}")
                return False
            
            if reward.shape != (self.n_agents,):
                main_logger.error(f"MAPPORolloutBuffer.add: 奖励形状不匹配! 期望{(self.n_agents,)}, 实际{reward.shape}, t={t}, env_idx={env_idx}")
                return False
            
            if done.shape != (self.n_agents,):
                main_logger.error(f"MAPPORolloutBuffer.add: done形状不匹配! 期望{(self.n_agents,)}, 实际{done.shape}, t={t}, env_idx={env_idx}")
                return False

            # 数据合理性检查 - 参考RolloutBuffer的健康检查
            if np.isnan(obs).any() or np.isinf(obs).any():
                main_logger.error(f"MAPPORolloutBuffer.add: 无效的观测数据! t={t}, env_idx={env_idx}")
                return False
            
            if np.isnan(action).any() or np.isinf(action).any():
                main_logger.error(f"MAPPORolloutBuffer.add: 无效的动作数据! t={t}, env_idx={env_idx}")
                return False
            
            if np.isnan(value).any() or np.isinf(value).any():
                main_logger.error(f"MAPPORolloutBuffer.add: 无效的价值数据! t={t}, env_idx={env_idx}")
                return False
            
            # 存储数据到指定位置 - 参考RolloutBuffer.add
            self.obs[t, env_idx] = obs
            self.actions[t, env_idx] = action
            self.states[t, env_idx] = state
            self.rewards[t, env_idx] = reward
            self.dones[t, env_idx] = done
            self.values[t, env_idx] = value
            self.log_probs[t, env_idx] = log_prob
            
            main_logger.debug(f"MAPPORolloutBuffer.add: 成功存储数据 t={t}, env_idx={env_idx}, "
                             f"reward={np.mean(reward):.4f}")
            return True
            
        except Exception as e:
            main_logger.error(f"MAPPORolloutBuffer.add: 存储数据失败: {e}")
            main_logger.error(f"输入形状: obs={obs.shape}, reward={reward.shape}, done={done.shape}")
            return False
    
    def compute_gae_and_returns(self, last_values, last_dones, gamma=0.99, gae_lambda=0.95):
        """计算GAE优势和returns - 修复张量维度问题，参考hmasd/utils.py的compute_gae实现"""
        if not self.ready_for_update:
            main_logger.warning("Rollout数据未收集完整，无法计算GAE")
            return
        
        try:
            # 确保last_values和last_dones的形状正确
            last_values = np.asarray(last_values, dtype=np.float32)
            last_dones = np.asarray(last_dones, dtype=np.float32)
            
            # 验证输入形状
            expected_last_values_shape = (self.num_envs, self.n_agents)
            if last_values.shape != expected_last_values_shape:
                main_logger.error(f"last_values形状不匹配! 期望{expected_last_values_shape}, 实际{last_values.shape}")
                return
            
            # 确保last_dones的形状正确
            if last_dones.ndim == 1:  # (num_envs,) -> (num_envs, n_agents)
                last_dones = np.tile(last_dones[:, np.newaxis], (1, self.n_agents))
            
            main_logger.debug(f"GAE计算开始: rewards形状={self.rewards.shape}, values形状={self.values.shape}, "
                            f"last_values形状={last_values.shape}, last_dones形状={last_dones.shape}")
            
            # 为每个环境和每个智能体分别计算GAE - 使用标准的逆序GAE算法
            for env_idx in range(self.num_envs):
                for agent_idx in range(self.n_agents):
                    # 提取单个智能体的时间序列数据
                    agent_rewards = self.rewards[:, env_idx, agent_idx]  # (num_steps,)
                    agent_values = self.values[:, env_idx, agent_idx]    # (num_steps,)
                    agent_dones = self.dones[:, env_idx, agent_idx]      # (num_steps,)
                    
                    # 计算GAE - 使用标准算法，不依赖utils.compute_gae
                    advantages = np.zeros_like(agent_rewards)
                    last_gae = 0
                    
                    # 逆序计算GAE
                    for t in reversed(range(self.num_steps)):
                        if t == self.num_steps - 1:
                            next_value = last_values[env_idx, agent_idx] * (1 - last_dones[env_idx, agent_idx])
                        else:
                            next_value = agent_values[t + 1] * (1 - agent_dones[t])
                        
                        delta = agent_rewards[t] + gamma * next_value - agent_values[t]
                        advantages[t] = last_gae = delta + gamma * gae_lambda * (1 - agent_dones[t]) * last_gae
                    
                    # 计算returns
                    returns = advantages + agent_values
                    
                    # 存储结果
                    self.advantages[:, env_idx, agent_idx] = advantages
                    self.returns[:, env_idx, agent_idx] = returns
            
            main_logger.debug(f"GAE计算完成，处理了{self.num_envs}个环境，每个环境{self.n_agents}个智能体")
            
        except Exception as e:
            main_logger.error(f"GAE计算失败: {e}")
            main_logger.error(f"异常详情: {traceback.format_exc()}")
            raise
    
    def get_all_data(self):
        """获取所有rollout数据用于训练 - 修复多智能体数据展平"""
        if not self.ready_for_update:
            main_logger.warning("Rollout数据未准备好")
            return None
            
        # 展平多智能体数据为训练批次 - 参考hmasd/utils.py的RolloutBuffer
        # 原始形状: (num_steps, num_envs, n_agents, feature_dim)
        # 目标形状: (num_steps * num_envs * n_agents, feature_dim)
        batch_size = self.num_steps * self.num_envs * self.n_agents
        
        return {
            'observations': self.obs.reshape(batch_size, self.obs_dim),
            'states': np.repeat(self.states.reshape(self.num_steps * self.num_envs, self.state_dim), self.n_agents, axis=0),
            'actions': self.actions.reshape(batch_size, self.action_dim),
            'old_log_probs': self.log_probs.reshape(batch_size),
            'advantages': self.advantages.reshape(batch_size),
            'returns': self.returns.reshape(batch_size),
            'values': self.values.reshape(batch_size)
        }
    
    def get_minibatch_generator(self, batch_size):
        """生成mini-batch用于PPO更新 - 修复多智能体数据索引"""
        if not self.ready_for_update:
            return None
            
        all_data = self.get_all_data()
        if all_data is None:
            return None
            
        # 修复：总样本数应该包括所有智能体
        total_samples = self.num_steps * self.num_envs * self.n_agents
        indices = np.arange(total_samples)
        
        # 随机打乱索引
        np.random.shuffle(indices)
        
        # 生成mini-batches
        for start in range(0, total_samples, batch_size):
            end = min(start + batch_size, total_samples)
            batch_indices = indices[start:end]
            
            yield {
                'observations': torch.from_numpy(all_data['observations'][batch_indices]).float(),
                'states': torch.from_numpy(all_data['states'][batch_indices]).float(),
                'actions': torch.from_numpy(all_data['actions'][batch_indices]).float(),
                'old_log_probs': torch.from_numpy(all_data['old_log_probs'][batch_indices]).float(),
                'advantages': torch.from_numpy(all_data['advantages'][batch_indices]).float(),
                'returns': torch.from_numpy(all_data['returns'][batch_indices]).float(),
                'values': torch.from_numpy(all_data['values'][batch_indices]).float()
            }
    
    def clear(self):
        """清空buffer，准备下一个rollout"""
        self.step = 0
        self.ready_for_update = False
        
        # 重置所有数组 - 修复属性名称
        self.obs.fill(0)
        self.next_obs.fill(0)
        self.states.fill(0)
        self.next_states.fill(0)
        self.actions.fill(0)
        self.rewards.fill(0)
        self.dones.fill(False)
        self.log_probs.fill(0)
        self.values.fill(0)
        self.advantages.fill(0)
        self.returns.fill(0)
    
    def __len__(self):
        """返回当前存储的步数"""
        return self.step
    
    def is_full(self):
        """检查buffer是否已满 - 修复逻辑，参考hmasd/utils.py"""
        return self.step >= self.num_steps

# 初始化默认的主logger，供模块级别导入使用
main_logger = None

def init_main_logger():
    """初始化主logger"""
    global main_logger
    if main_logger is None:
        # 创建一个基本的logger作为默认值
        import logging
        main_logger = logging.getLogger("MAPPO-Enhanced-Default")
        main_logger.setLevel(logging.INFO)
        if not main_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            main_logger.addHandler(handler)
    return main_logger

# 初始化默认logger
main_logger = init_main_logger()

# 数值稳定性和监控工具
def check_tensor_health(tensor, name="", logger=None, raise_on_error=False):
    """检查张量的数值健康状况 - 增强版本，支持布尔张量"""
    if logger is None:
        logger = main_logger
        
    try:
        if tensor is None:
            msg = f"张量 {name} 为 None"
            logger.error(msg)
            if raise_on_error:
                raise ValueError(msg)
            return False
            
        if not isinstance(tensor, torch.Tensor):
            msg = f"张量 {name} 不是 torch.Tensor 类型: {type(tensor)}"
            logger.error(msg)
            if raise_on_error:
                raise TypeError(msg)
            return False
        
        # 检查张量是否为空
        if tensor.numel() == 0:
            msg = f"张量 {name} 为空张量"
            logger.error(msg)
            if raise_on_error:
                raise ValueError(msg)
            return False
        
        # 对于布尔张量，跳过数值统计，只检查基本属性
        if tensor.dtype == torch.bool:
            logger.debug(f"张量 {name} 是布尔类型，跳过数值统计检查")
            logger.debug(f"布尔张量 {name} 健康检查通过: 形状={tensor.shape}, "
                        f"True数量={tensor.sum().item()}, False数量={(~tensor).sum().item()}")
            return True
            
        # 检查是否包含 NaN 或 Inf (仅对数值类型)
        if tensor.dtype in [torch.float16, torch.float32, torch.float64, torch.complex64, torch.complex128]:
            has_nan = torch.isnan(tensor).any()
            has_inf = torch.isinf(tensor).any()
            
            if has_nan:
                nan_count = torch.isnan(tensor).sum().item()
                msg = f"张量 {name} 包含 {nan_count} 个 NaN 值"
                logger.error(msg)
                if raise_on_error:
                    raise ValueError(msg)
                return False
                
            if has_inf:
                inf_count = torch.isinf(tensor).sum().item()
                msg = f"张量 {name} 包含 {inf_count} 个 Inf 值"
                logger.error(msg)
                if raise_on_error:
                    raise ValueError(msg)
                return False
        
        # 数值统计检查 (仅对数值类型张量)
        if tensor.dtype in [torch.float16, torch.float32, torch.float64, torch.int8, torch.int16, torch.int32, torch.int64]:
            # 安全转换为浮点数进行统计
            float_tensor = tensor.float() if tensor.dtype != torch.float32 else tensor
            
            tensor_min = float_tensor.min().item()
            tensor_max = float_tensor.max().item()
            tensor_mean = float_tensor.mean().item()
            # 避免对单元素张量计算标准差时的UserWarning
            if float_tensor.numel() > 1:
                tensor_std = torch.std(float_tensor).item()
            else:
                tensor_std = 0.0
            
            # 检查数值是否过大或过小
            if abs(tensor_max) > 1e6 or abs(tensor_min) > 1e6:
                logger.warning(f"张量 {name} 数值范围异常: 最小值={tensor_min:.6f}, 最大值={tensor_max:.6f}")
            
            if tensor_std > 1e3:
                logger.warning(f"张量 {name} 标准差过大: {tensor_std:.6f}")
            
            # 记录张量统计信息（仅在debug模式下）
            logger.debug(f"张量 {name} 健康检查通过: 形状={tensor.shape}, "
                        f"范围=[{tensor_min:.6f}, {tensor_max:.6f}], "
                        f"均值={tensor_mean:.6f}, 标准差={tensor_std:.6f}")
        else:
            # 对于其他类型（如整数），只记录基本信息
            logger.debug(f"张量 {name} 健康检查通过: 形状={tensor.shape}, 类型={tensor.dtype}")
        
        return True
        
    except Exception as e:
        msg = f"检查张量 {name} 时发生异常: {e}"
        logger.error(msg)
        if raise_on_error:
            raise
        return False

def safe_divide(numerator, denominator, epsilon=1e-8, logger=None):
    """安全除法，避免除零错误 - 增强版本"""
    if logger is None:
        logger = main_logger
        
    try:
        # 检查输入张量健康性
        if not check_tensor_health(numerator, "numerator", logger, raise_on_error=False):
            logger.warning("分子张量异常，返回零张量")
            return torch.zeros_like(numerator) if isinstance(numerator, torch.Tensor) else torch.tensor(0.0)
            
        if not check_tensor_health(denominator, "denominator", logger, raise_on_error=False):
            logger.warning("分母张量异常，返回零张量")
            return torch.zeros_like(numerator) if isinstance(numerator, torch.Tensor) else torch.tensor(0.0)
        
        # 检查分母是否接近零
        if isinstance(denominator, torch.Tensor):
            zero_mask = torch.abs(denominator) < epsilon
            if zero_mask.any():
                logger.debug(f"检测到 {zero_mask.sum().item()} 个接近零的分母值，将使用epsilon调整")
                safe_denominator = torch.where(zero_mask, epsilon, denominator)
            else:
                safe_denominator = denominator
        else:
            if abs(denominator) < epsilon:
                logger.debug("标量分母接近零，使用epsilon")
                safe_denominator = epsilon if denominator >= 0 else -epsilon
            else:
                safe_denominator = denominator
        
        result = numerator / safe_denominator
        
        # 检查结果健康性
        if not check_tensor_health(result, "division_result", logger):
            logger.warning("除法结果异常，使用备用值")
            return torch.zeros_like(numerator) if isinstance(numerator, torch.Tensor) else torch.tensor(0.0)
            
        return result
        
    except Exception as e:
        logger.error(f"安全除法操作失败: {e}")
        return torch.zeros_like(numerator) if isinstance(numerator, torch.Tensor) else torch.tensor(0.0)

def safe_log(tensor, epsilon=1e-8, logger=None):
    """安全对数运算，避免log(0)"""
    if logger is None:
        logger = main_logger
        
    try:
        # 确保输入大于零
        safe_tensor = torch.clamp(tensor, min=epsilon)
        result = torch.log(safe_tensor)
        
        if not check_tensor_health(result, "log_result", logger):
            logger.warning(f"对数运算结果异常")
            return torch.zeros_like(tensor)
            
        return result
        
    except Exception as e:
        logger.error(f"安全对数运算失败: {e}")
        return torch.zeros_like(tensor)

def safe_exp(tensor, max_value=50.0, logger=None):
    """安全指数运算，避免数值溢出"""
    if logger is None:
        logger = main_logger
        
    try:
        # 限制指数输入范围
        safe_tensor = torch.clamp(tensor, max=max_value)
        result = torch.exp(safe_tensor)
        
        if not check_tensor_health(result, "exp_result", logger):
            logger.warning(f"指数运算结果异常")
            return torch.ones_like(tensor)
            
        return result
        
    except Exception as e:
        logger.error(f"安全指数运算失败: {e}")
        return torch.ones_like(tensor)

def monitor_gradients(model, name="", logger=None, max_norm_threshold=10.0):
    """监控模型梯度"""
    if logger is None:
        logger = main_logger
        
    try:
        total_norm = 0.0
        param_count = 0
        grad_norms = []
        
        for param in model.parameters():
            if param.grad is not None:
                param_norm = param.grad.data.norm(2)
                total_norm += param_norm.item() ** 2
                grad_norms.append(param_norm.item())
                param_count += 1
        
        total_norm = total_norm ** (1. / 2)
        
        if param_count > 0:
            avg_grad_norm = np.mean(grad_norms)
            max_grad_norm = np.max(grad_norms)
            min_grad_norm = np.min(grad_norms)
            
            logger.debug(f"模型 {name} 梯度统计: 总范数={total_norm:.6f}, 平均={avg_grad_norm:.6f}, "
                        f"最大={max_grad_norm:.6f}, 最小={min_grad_norm:.6f}")
            
            # 检查梯度爆炸
            if total_norm > max_norm_threshold:
                logger.warning(f"模型 {name} 检测到梯度爆炸: 总范数={total_norm:.6f} > 阈值={max_norm_threshold}")
                
            # 检查梯度消失
            if total_norm < 1e-7:
                logger.warning(f"模型 {name} 检测到梯度消失: 总范数={total_norm:.6f}")
                
        return total_norm, grad_norms
        
    except Exception as e:
        logger.error(f"监控模型 {name} 梯度时发生异常: {e}")
        return 0.0, []

def log_memory_usage(logger=None, step=None):
    """记录内存使用情况 - 增强版本，包含内存泄漏检测"""
    if logger is None:
        logger = main_logger
        
    try:
        # GPU内存使用
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.memory_allocated() / (1024**3)  # GB
            gpu_memory_cached = torch.cuda.memory_reserved() / (1024**3)  # GB
            gpu_max_memory = torch.cuda.max_memory_allocated() / (1024**3)  # GB
            
            logger.debug(f"步骤 {step} GPU内存: 已分配={gpu_memory:.2f}GB, "
                        f"缓存={gpu_memory_cached:.2f}GB, 峰值={gpu_max_memory:.2f}GB")
            
            # GPU内存预警
            if gpu_memory > 8.0:  # 8GB阈值
                logger.warning(f"步骤 {step} GPU内存使用过高: {gpu_memory:.2f}GB")
            
            # 检测内存泄漏 - 如果缓存内存远大于已分配内存
            if gpu_memory_cached > gpu_memory * 2:
                logger.warning(f"步骤 {step} 检测到可能的GPU内存泄漏: "
                              f"缓存({gpu_memory_cached:.2f}GB) >> 已分配({gpu_memory:.2f}GB)")
        
        # CPU内存使用
        process = psutil.Process()
        memory_info = process.memory_info()
        cpu_memory = memory_info.rss / (1024**3)  # GB
        cpu_memory_percent = process.memory_percent()
        
        logger.debug(f"步骤 {step} CPU内存: {cpu_memory:.2f}GB ({cpu_memory_percent:.1f}%)")
        
        # CPU内存预警
        if cpu_memory > 16.0:  # 16GB阈值
            logger.warning(f"步骤 {step} CPU内存使用过高: {cpu_memory:.2f}GB")
        
        # 系统内存使用
        system_memory = psutil.virtual_memory()
        logger.debug(f"步骤 {step} 系统内存: 使用率={system_memory.percent}%, "
                    f"可用={system_memory.available / (1024**3):.2f}GB")
        
        # 系统内存预警
        if system_memory.percent > 85:
            logger.warning(f"步骤 {step} 系统内存使用率过高: {system_memory.percent}%")
            
        # 返回内存统计信息用于监控
        return {
            'gpu_memory': gpu_memory if torch.cuda.is_available() else 0,
            'gpu_memory_cached': gpu_memory_cached if torch.cuda.is_available() else 0,
            'cpu_memory': cpu_memory,
            'cpu_memory_percent': cpu_memory_percent,
            'system_memory_percent': system_memory.percent
        }
        
    except Exception as e:
        logger.error(f"记录内存使用时发生异常: {e}")
        return {}

def safe_tensor_ops_wrapper(func):
    """装饰器：为张量操作添加安全检查"""
    def wrapper(*args, **kwargs):
        try:
            # 检查输入张量
            for i, arg in enumerate(args):
                if isinstance(arg, torch.Tensor):
                    if not check_tensor_health(arg, f"input_{i}"):
                        raise ValueError(f"输入张量 {i} 健康检查失败")
            
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 检查输出张量
            if isinstance(result, torch.Tensor):
                if not check_tensor_health(result, "output"):
                    raise ValueError("输出张量健康检查失败")
            elif isinstance(result, (list, tuple)):
                for i, item in enumerate(result):
                    if isinstance(item, torch.Tensor):
                        if not check_tensor_health(item, f"output_{i}"):
                            raise ValueError(f"输出张量 {i} 健康检查失败")
            
            return result
            
        except Exception as e:
            main_logger.error(f"安全张量操作失败: {e}")
            main_logger.error(f"函数: {func.__name__}, 参数: {args}, 关键字参数: {kwargs}")
            raise
    
    return wrapper

class EnhancedRewardTracker:
    """增强的奖励追踪器，用于MAPPO训练数据收集"""
    
    def __init__(self, log_dir, config, n_users=None):
        self.log_dir = log_dir
        self.config = config
        self.n_users = n_users  # 存储用户总数，用于准确计算服务率
        
        # 训练过程中的奖励数据收集
        self.training_rewards = {
            'episode_rewards': [],
            'step_rewards': [],
            'env_rewards': [],
            'agent_rewards': [],  # MAPPO特有：每个智能体的奖励
            'cumulative_rewards': [],
            'reward_variance': [],
            'episodes_completed': 0,
            'total_steps': 0
        }
        
        # 性能指标
        self.performance_metrics = {
            'episode_lengths': [],
            'success_rates': [],
            'coverage_ratios': [],
            'served_users': [],
            'network_efficiency': [],
            'total_throughput': [],
            'avg_throughput_per_user': [],
            'agent_coordination': []  # MAPPO特有：智能体协调指标
        }
        
        # 滑动窗口统计
        self.window_size = 100
        self.recent_rewards = deque(maxlen=self.window_size)
        self.recent_lengths = deque(maxlen=self.window_size)
        
        # 数据导出设置
        self.export_interval = 1000
        self.last_export_step = 0
    
    def log_training_step(self, step, env_id, reward, agent_rewards=None, info=None):
        """记录训练步骤的奖励信息"""
        self.training_rewards['total_steps'] += 1
        self.training_rewards['step_rewards'].append({
            'step': step,
            'env_id': env_id,
            'reward': reward,
            'timestamp': time.time()
        })
        
        # 记录每个智能体的奖励
        if agent_rewards is not None:
            self.training_rewards['agent_rewards'].append({
                'step': step,
                'env_id': env_id,
                'agent_rewards': agent_rewards.copy(),
                'timestamp': time.time()
            })
        
        # 记录额外信息
        if info:
            served_users = 0
            
            # 从多个来源获取服务用户数
            if 'reward_info' in info and 'effective_connected_users' in info['reward_info']:
                served_users = info['reward_info']['effective_connected_users']
            elif 'reward_info' in info and 'connected_users' in info['reward_info']:
                served_users = info['reward_info']['connected_users']
            elif 'coverage_ratio' in info and self.n_users is not None:
                # 从覆盖率计算服务用户数，使用固定的n_users
                served_users = int(info['coverage_ratio'] * self.n_users)
            elif 'served_users' in info:
                # 兼容原有字段名
                served_users = info['served_users']

            if served_users > 0:
                self.performance_metrics['served_users'].append({
                    'step': step,
                    'env_id': env_id,
                    'served_users': served_users,
                    'total_users': self.n_users
                })
            
            # 记录吞吐量信息
            if 'reward_info' in info:
                reward_info = info['reward_info']
                if 'system_throughput_mbps' in reward_info:
                    self.performance_metrics['total_throughput'].append({
                        'step': step,
                        'env_id': env_id,
                        'total_throughput_mbps': reward_info['system_throughput_mbps'],
                        'timestamp': time.time()
                    })
    
    def log_episode_completion(self, episode_num, env_id, total_reward, episode_length, agent_rewards=None, info=None):
        """记录episode完成信息"""
        self.training_rewards['episodes_completed'] += 1
        
        episode_data = {
            'episode': episode_num,
            'env_id': env_id,
            'total_reward': total_reward,
            'episode_length': episode_length,
            'timestamp': time.time()
        }
        
        if agent_rewards is not None:
            episode_data['agent_rewards'] = agent_rewards.copy()
            # 计算智能体协调指标
            reward_std = np.std(agent_rewards)
            reward_mean = np.mean(agent_rewards)
            coordination_metric = 1.0 / (1.0 + reward_std) if reward_std > 0 else 1.0
            episode_data['coordination_metric'] = coordination_metric
            
            self.performance_metrics['agent_coordination'].append({
                'episode': episode_num,
                'env_id': env_id,
                'coordination_metric': coordination_metric,
                'reward_std': reward_std,
                'reward_mean': reward_mean
            })
        
        if info:
            episode_data.update(info)
        
        self.training_rewards['episode_rewards'].append(episode_data)
        self.recent_rewards.append(total_reward)
        self.recent_lengths.append(episode_length)
        
        # 计算滑动窗口统计
        if len(self.recent_rewards) >= 10:
            self.training_rewards['reward_variance'].append({
                'episode': episode_num,
                'mean': np.mean(self.recent_rewards),
                'std': np.std(self.recent_rewards),
                'min': np.min(self.recent_rewards),
                'max': np.max(self.recent_rewards)
            })
    
    def export_training_data(self, step):
        """导出训练数据用于论文分析"""
        if step - self.last_export_step < self.export_interval:
            return
        
        export_dir = os.path.join(self.log_dir, 'paper_data')
        os.makedirs(export_dir, exist_ok=True)
        
        # 导出奖励数据
        if self.training_rewards['episode_rewards']:
            rewards_df = pd.DataFrame(self.training_rewards['episode_rewards'])
            rewards_df.to_csv(os.path.join(export_dir, f'episode_rewards_step_{step}.csv'), index=False)
        
        # 导出智能体协调数据
        if self.performance_metrics['agent_coordination']:
            coord_df = pd.DataFrame(self.performance_metrics['agent_coordination'])
            coord_df.to_csv(os.path.join(export_dir, f'agent_coordination_step_{step}.csv'), index=False)
        
        # 生成训练曲线图
        self.generate_training_plots(export_dir, step)
        
        self.last_export_step = step
        main_logger.debug(f"已导出步骤 {step} 的训练数据到 {export_dir}")
    
    def generate_training_plots(self, export_dir, step):
        """生成训练过程的可视化图表"""
        
        # Episode奖励趋势图
        if self.training_rewards['episode_rewards']:
            episodes = [r['episode'] for r in self.training_rewards['episode_rewards']]
            rewards = [r['total_reward'] for r in self.training_rewards['episode_rewards']]
            
            plt.figure(figsize=(15, 10))
            
            # 原始奖励曲线
            plt.subplot(2, 3, 1)
            plt.plot(episodes, rewards, alpha=0.3, color='blue', label='Episode Rewards')
            # 滑动平均
            if len(rewards) >= 10:
                window = 50
                if len(rewards) >= window:
                    smoothed = pd.Series(rewards).rolling(window=window, center=True).mean()
                    plt.plot(episodes, smoothed, color='red', linewidth=2, label=f'{window}-episode MA')
            plt.xlabel('Episode')
            plt.ylabel('Total Reward')
            plt.title('MAPPO Training Reward Progress')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # 奖励分布直方图
            plt.subplot(2, 3, 2)
            plt.hist(rewards, bins=50, alpha=0.7, color='green')
            plt.xlabel('Total Reward')
            plt.ylabel('Frequency')
            plt.title('Reward Distribution')
            plt.grid(True, alpha=0.3)
            
            # Episode长度趋势
            if len(episodes) == len([r['episode_length'] for r in self.training_rewards['episode_rewards']]):
                lengths = [r['episode_length'] for r in self.training_rewards['episode_rewards']]
                plt.subplot(2, 3, 3)
                plt.plot(episodes, lengths, alpha=0.6, color='orange')
                plt.xlabel('Episode')
                plt.ylabel('Episode Length')
                plt.title('Episode Length Progression')
                plt.grid(True, alpha=0.3)
            
            # 智能体协调指标
            if self.performance_metrics['agent_coordination']:
                coord_episodes = [c['episode'] for c in self.performance_metrics['agent_coordination']]
                coord_metrics = [c['coordination_metric'] for c in self.performance_metrics['agent_coordination']]
                
                plt.subplot(2, 3, 4)
                plt.plot(coord_episodes, coord_metrics, alpha=0.7, color='purple')
                plt.xlabel('Episode')
                plt.ylabel('Coordination Metric')
                plt.title('Agent Coordination Over Time')
                plt.grid(True, alpha=0.3)
            
            # 奖励方差趋势
            if self.training_rewards['reward_variance']:
                var_episodes = [v['episode'] for v in self.training_rewards['reward_variance']]
                var_means = [v['mean'] for v in self.training_rewards['reward_variance']]
                var_stds = [v['std'] for v in self.training_rewards['reward_variance']]
                
                plt.subplot(2, 3, 5)
                plt.errorbar(var_episodes, var_means, yerr=var_stds, alpha=0.7, color='red')
                plt.xlabel('Episode')
                plt.ylabel('Mean Reward ± Std')
                plt.title('Reward Stability (100-episode window)')
                plt.grid(True, alpha=0.3)
            
            # 智能体奖励标准差趋势
            if self.performance_metrics['agent_coordination']:
                reward_stds = [c['reward_std'] for c in self.performance_metrics['agent_coordination']]
                
                plt.subplot(2, 3, 6)
                plt.plot(coord_episodes, reward_stds, alpha=0.7, color='brown')
                plt.xlabel('Episode')
                plt.ylabel('Agent Reward Std')
                plt.title('Agent Reward Variance')
                plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(os.path.join(export_dir, f'mappo_training_progress_step_{step}.png'), dpi=300, bbox_inches='tight')
            plt.close()
        
        # 生成场景4特有的网络健康度图表
        if self.performance_metrics['network_health_scores']:
            self.generate_scenario4_plots(export_dir, step)
    
    def generate_scenario4_plots(self, export_dir, step):
        """生成场景4特有的网络健康度可视化图表"""
        try:
            health_data = self.performance_metrics['network_health_scores']
            if not health_data:
                return
            
            steps = [h['step'] for h in health_data]
            health_scores = [h['health_score'] for h in health_data]
            connectivity_scores = [h['connectivity_score'] for h in health_data]
            role_diversity_scores = [h['role_diversity_bonus'] for h in health_data]
            coverage_scores = [h['effective_coverage_score'] for h in health_data]
            dispersion_penalties = [h['dispersion_penalty'] for h in health_data]
            serving_counts = [h['serving_uavs_count'] for h in health_data]
            relay_counts = [h['pure_relay_uavs_count'] for h in health_data]
            
            plt.figure(figsize=(20, 12))
            
            # 网络健康度总分趋势
            plt.subplot(2, 4, 1)
            plt.plot(steps, health_scores, alpha=0.7, color='red', linewidth=2)
            plt.xlabel('Training Steps')
            plt.ylabel('Network Health Score')
            plt.title('Network Health Score Over Time')
            plt.grid(True, alpha=0.3)
            
            # 连接性得分
            plt.subplot(2, 4, 2)
            plt.plot(steps, connectivity_scores, alpha=0.7, color='blue')
            plt.xlabel('Training Steps')
            plt.ylabel('Connectivity Score')
            plt.title('UAV Connectivity Score')
            plt.grid(True, alpha=0.3)
            
            # 角色多样性得分
            plt.subplot(2, 4, 3)
            plt.plot(steps, role_diversity_scores, alpha=0.7, color='green')
            plt.xlabel('Training Steps')
            plt.ylabel('Role Diversity Bonus')
            plt.title('Role Diversity Score')
            plt.grid(True, alpha=0.3)
            
            # 有效覆盖得分
            plt.subplot(2, 4, 4)
            plt.plot(steps, coverage_scores, alpha=0.7, color='orange')
            plt.xlabel('Training Steps')
            plt.ylabel('Effective Coverage Score')
            plt.title('Coverage Performance')
            plt.grid(True, alpha=0.3)
            
            # 分散惩罚
            plt.subplot(2, 4, 5)
            plt.plot(steps, dispersion_penalties, alpha=0.7, color='purple')
            plt.xlabel('Training Steps')
            plt.ylabel('Dispersion Penalty')
            plt.title('UAV Dispersion Penalty')
            plt.grid(True, alpha=0.3)
            
            # 服务无人机数量
            plt.subplot(2, 4, 6)
            plt.plot(steps, serving_counts, alpha=0.7, color='cyan', label='Serving UAVs')
            plt.plot(steps, relay_counts, alpha=0.7, color='magenta', label='Pure Relay UAVs')
            plt.xlabel('Training Steps')
            plt.ylabel('UAV Count')
            plt.title('UAV Role Distribution')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # 网络健康度组件堆叠图
            plt.subplot(2, 4, 7)
            plt.stackplot(steps, connectivity_scores, role_diversity_scores, coverage_scores,
                         labels=['Connectivity', 'Role Diversity', 'Coverage'],
                         alpha=0.7)
            plt.xlabel('Training Steps')
            plt.ylabel('Score Components')
            plt.title('Health Score Components')
            plt.legend(loc='upper left')
            plt.grid(True, alpha=0.3)
            
            # 角色平衡指标
            plt.subplot(2, 4, 8)
            role_balance = []
            for i in range(len(serving_counts)):
                total_active = serving_counts[i] + relay_counts[i]
                if total_active > 0:
                    balance = min(serving_counts[i], relay_counts[i]) / total_active
                else:
                    balance = 0
                role_balance.append(balance)
            
            plt.plot(steps, role_balance, alpha=0.7, color='brown')
            plt.xlabel('Training Steps')
            plt.ylabel('Role Balance Score')
            plt.title('UAV Role Balance (min(serving,relay)/total)')
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(os.path.join(export_dir, f'scenario4_network_health_step_{step}.png'), dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            main_logger.warning(f"生成场景4图表失败: {e}")
    
    def get_summary_statistics(self):
        """获取训练摘要统计信息"""
        summary = {
            'total_episodes': self.training_rewards['episodes_completed'],
            'total_steps': self.training_rewards['total_steps']
        }
        
        if self.training_rewards['episode_rewards']:
            rewards = [r['total_reward'] for r in self.training_rewards['episode_rewards']]
            summary.update({
                'reward_mean': np.mean(rewards),
                'reward_std': np.std(rewards),
                'reward_min': np.min(rewards),
                'reward_max': np.max(rewards)
            })
        
        if self.performance_metrics['agent_coordination']:
            coord_metrics = [c['coordination_metric'] for c in self.performance_metrics['agent_coordination']]
            summary.update({
                'avg_coordination': np.mean(coord_metrics),
                'coordination_std': np.std(coord_metrics)
            })
        
        return summary

class MAPPOActor(nn.Module):
    """MAPPO Actor网络 - 增强架构，参考SkillDiscoverer设计"""
    
    def __init__(self, obs_dim, action_dim, hidden_size=128, config=None):
        super(MAPPOActor, self).__init__()
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.hidden_size = hidden_size
        self.config = config
        
        # 现代化的网络架构 - 参考SkillDiscoverer
        # 输入嵌入层
        self.input_embedding = nn.Linear(obs_dim, hidden_size)
        
        # 主干网络 - 使用ResBlock和LayerNorm
        self.backbone = nn.Sequential(
            nn.LayerNorm(hidden_size),
            nn.GELU(),
            ResBlock(hidden_size),
            ResBlock(hidden_size),
            nn.LayerNorm(hidden_size),
            nn.GELU()
        )
        
        # 动作输出头
        self.action_mean_head = nn.Linear(hidden_size, action_dim)
        self.action_log_std_head = nn.Linear(hidden_size, action_dim)
        
        # 连续动作空间的标准差参数 - 限制范围避免数值不稳定
        self.log_std = nn.Parameter(torch.zeros(action_dim))
        
        # 数值稳定性参数
        self.epsilon = 1e-8
        self.log_std_min = -20
        self.log_std_max = 2
        self.action_bound = getattr(config, 'action_bound', 3.0) if config else 3.0
        
        # 初始化网络权重
        self._init_weights()
    
    def _init_weights(self):
        """初始化网络权重，参考SkillDiscoverer的初始化策略"""
        # 初始化嵌入层
        initialize_weights(self.input_embedding, gain=1.0)
        
        # 初始化主干网络
        for module in self.backbone:
            if isinstance(module, (nn.Linear, ResBlock)):
                initialize_weights(module, gain=1.0)
        
        # 初始化输出头 - 动作均值使用较小的初始化
        initialize_weights(self.action_mean_head, gain=0.01)
        initialize_weights(self.action_log_std_head, gain=0.01)
        
        # 初始化log_std参数
        nn.init.constant_(self.action_log_std_head.bias, -1.0)  # exp(-1) ≈ 0.37
        
    def forward(self, obs):
        """前向传播 - 使用增强架构"""
        try:
            # 检查输入健康性
            if not check_tensor_health(obs, "actor_input", main_logger):
                main_logger.error("Actor输入张量异常，使用零张量")
                obs = torch.zeros_like(obs)
            
            # 确保输入是float32类型
            obs = obs.float()
            
            # 通过增强的网络架构
            # 1. 输入嵌入
            embedded = self.input_embedding(obs)
            
            # 2. 主干网络处理
            features = self.backbone(embedded)
            
            # 3. 生成动作均值
            action_mean = self.action_mean_head(features)
            
            # 4. 生成动作标准差 - 使用学习的参数
            action_log_std = self.action_log_std_head(features)
            action_log_std = torch.clamp(action_log_std, self.log_std_min, self.log_std_max)
            
            # 应用动作边界约束
            action_mean = torch.clamp(action_mean, -self.action_bound, self.action_bound)
            
            # 计算标准差
            std = safe_exp(action_log_std, max_value=self.log_std_max, logger=main_logger)
            std = torch.clamp(std, min=self.epsilon)
            
            # 检查输出健康性
            if not check_tensor_health(action_mean, "actor_mean", main_logger):
                main_logger.error("Actor均值异常，使用零张量")
                action_mean = torch.zeros_like(action_mean)
            
            if not check_tensor_health(std, "actor_std", main_logger):
                main_logger.error("Actor标准差异常，使用单位张量")
                std = torch.ones_like(std)
            
            return action_mean, std
            
        except Exception as e:
            main_logger.error(f"Actor前向传播失败: {e}")
            # 返回安全的默认值
            return torch.zeros(obs.shape[0], self.action_dim), torch.ones(obs.shape[0], self.action_dim)
    
    def get_action_and_log_prob(self, obs):
        """获取动作和对数概率 - 增强数值稳定性"""
        try:
            mean, std = self.forward(obs)
            
            # 创建分布时添加数值稳定性检查
            dist = Normal(mean, std)
            action = dist.sample()
            
            # 检查动作健康性
            if not check_tensor_health(action, "sampled_action", main_logger):
                main_logger.warning("采样动作异常，使用均值")
                action = mean
            
            # 安全计算对数概率
            log_prob = dist.log_prob(action)
            
            # 检查对数概率健康性
            if not check_tensor_health(log_prob, "log_prob", main_logger):
                main_logger.warning("对数概率异常，使用零值")
                log_prob = torch.zeros_like(log_prob)
            
            log_prob = log_prob.sum(dim=-1)
            
            return action, log_prob
            
        except Exception as e:
            main_logger.error(f"获取动作和对数概率失败: {e}")
            # 返回安全的默认值
            batch_size = obs.shape[0]
            return torch.zeros(batch_size, self.action_dim), torch.zeros(batch_size)
    
    def evaluate_actions(self, obs, actions):
        """评估动作的对数概率和熵 - 增强数值稳定性"""
        try:
            mean, std = self.forward(obs)
            
            # 检查动作健康性
            if not check_tensor_health(actions, "input_actions", main_logger):
                main_logger.error("输入动作异常")
                actions = torch.zeros_like(actions)
            
            # 创建分布
            dist = Normal(mean, std)
            
            # 安全计算对数概率
            log_prob = dist.log_prob(actions)
            if not check_tensor_health(log_prob, "eval_log_prob", main_logger):
                main_logger.warning("评估对数概率异常，使用零值")
                log_prob = torch.zeros_like(log_prob)
            
            log_prob = log_prob.sum(dim=-1)
            
            # 安全计算熵
            entropy = dist.entropy()
            if not check_tensor_health(entropy, "entropy", main_logger):
                main_logger.warning("熵计算异常，使用零值")
                entropy = torch.zeros_like(entropy)
            
            entropy = entropy.sum(dim=-1)
            
            return log_prob, entropy
            
        except Exception as e:
            main_logger.error(f"评估动作失败: {e}")
            # 返回安全的默认值
            batch_size = obs.shape[0]
            return torch.zeros(batch_size), torch.zeros(batch_size)

class MAPPOCritic(nn.Module):
    """MAPPO Critic网络 - 增强架构，参考SkillDiscoverer设计"""
    
    def __init__(self, state_dim, hidden_size=128, config=None):
        super(MAPPOCritic, self).__init__()
        self.state_dim = state_dim
        self.hidden_size = hidden_size
        self.config = config
        
        # 现代化的网络架构 - 参考SkillDiscoverer的critic设计
        # 输入嵌入层
        self.input_embedding = nn.Linear(state_dim, hidden_size)
        
        # 主干网络 - 使用ResBlock和LayerNorm，参考critic_state_encoder
        self.backbone = nn.Sequential(
            nn.LayerNorm(hidden_size),
            nn.GELU(),
            ResBlock(hidden_size),
            ResBlock(hidden_size),
            nn.LayerNorm(hidden_size),
            nn.GELU()
        )
        
        # 后续处理网络 - 参考critic_post_film
        self.post_processing = nn.Sequential(
            ResBlock(hidden_size),
            nn.Linear(hidden_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.GELU()
        )
        
        # 价值输出头
        self.value_head = nn.Linear(hidden_size, 1)
        
        # 初始化网络权重
        self._init_weights()
    
    def _init_weights(self):
        """初始化网络权重，参考SkillDiscoverer的初始化策略"""
        # 初始化嵌入层
        initialize_weights(self.input_embedding, gain=1.0)
        
        # 初始化主干网络
        for module in self.backbone:
            if isinstance(module, (nn.Linear, ResBlock)):
                initialize_weights(module, gain=1.0)
        
        # 初始化后续处理网络
        for module in self.post_processing:
            if isinstance(module, (nn.Linear, ResBlock)):
                initialize_weights(module, gain=1.0)
        
        # 初始化价值头 - 使用较小的初始化，参考SkillDiscoverer
        initialize_weights(self.value_head, gain=0.01)
        
    def forward(self, state):
        """前向传播 - 使用增强架构"""
        try:
            # 检查输入健康性
            if not check_tensor_health(state, "critic_input", main_logger):
                main_logger.error("Critic输入张量异常，使用零张量")
                state = torch.zeros_like(state)
            
            # 确保输入是float32类型
            state = state.float()
            
            # 通过增强的网络架构
            # 1. 输入嵌入
            embedded = self.input_embedding(state)
            
            # 2. 主干网络处理
            backbone_features = self.backbone(embedded)
            
            # 3. 后续处理
            processed_features = self.post_processing(backbone_features)
            
            # 4. 价值输出
            value = self.value_head(processed_features)
            
            # 检查输出健康性
            if not check_tensor_health(value, "critic_value", main_logger):
                main_logger.error("Critic价值输出异常，使用零张量")
                value = torch.zeros_like(value)
            
            return value
            
        except Exception as e:
            main_logger.error(f"Critic前向传播失败: {e}")
            # 返回安全的默认值
            batch_size = state.shape[0] if state.dim() > 0 else 1
            return torch.zeros(batch_size, 1, device=state.device if isinstance(state, torch.Tensor) else 'cpu')

class MAPPOAgent:
    """MAPPO智能体"""
    
    def __init__(self, config, log_dir, device='cpu'):
        self.config = config
        self.device = device
        self.log_dir = log_dir
        
        # 创建网络 - 传递config参数以支持增强架构
        self.actor = MAPPOActor(
            obs_dim=config.obs_dim,
            action_dim=config.action_dim,
            hidden_size=config.hidden_size,
            config=config
        ).to(device)
        
        self.critic = MAPPOCritic(
            state_dim=config.state_dim,
            hidden_size=config.hidden_size,
            config=config
        ).to(device)
        
        # 优化器
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=config.lr_coordinator)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=config.lr_coordinator)
        
        # 经验缓冲区 - 使用MAPPO专用的RolloutBuffer
        self.buffer = MAPPORolloutBuffer(
            num_steps=config.rollout_length,
            num_envs=config.num_envs,
            n_agents=config.n_agents,
            obs_dim=config.obs_dim,
            action_dim=config.action_dim,
            state_dim=config.state_dim
        )
        
        # TensorBoard
        self.writer = SummaryWriter(log_dir)
        self.update_step = 0
        
    def select_actions(self, obs, states, deterministic=False):
        """选择动作 - 修复多智能体观察格式处理"""
        with torch.no_grad():
            # 处理多智能体观察格式 - 参考hmasd/utils.py的数据处理
            # obs形状: (num_envs, n_agents, obs_dim)
            # 需要展平为: (num_envs * n_agents, obs_dim)
            if obs.ndim == 3:  # 多智能体格式
                batch_size = obs.shape[0] * obs.shape[1]  # num_envs * n_agents
                obs_flat = obs.reshape(batch_size, obs.shape[2])  # (num_envs * n_agents, obs_dim)
            else:  # 已经是展平格式
                obs_flat = obs
                batch_size = obs.shape[0]
            
            obs_tensor = torch.FloatTensor(obs_flat).to(self.device)
            
            if deterministic:
                mean, _ = self.actor(obs_tensor)
                actions = mean
                log_probs = torch.zeros(batch_size, device=self.device)
            else:
                actions, log_probs = self.actor.get_action_and_log_prob(obs_tensor)
            
            # 计算值函数 - 使用全局状态
            # states形状: (num_envs, state_dim)
            # 需要为每个智能体重复: (num_envs * n_agents, state_dim)
            if states.ndim == 2:  # 全局状态格式
                states_expanded = np.repeat(states, self.config.n_agents, axis=0)  # (num_envs * n_agents, state_dim)
            else:  # 已经是展开格式
                states_expanded = states
                
            states_tensor = torch.FloatTensor(states_expanded).to(self.device)
            values = self.critic(states_tensor).squeeze()
            
            # 将结果重新整形为多智能体格式
            if obs.ndim == 3:  # 原始输入是多智能体格式
                num_envs, n_agents = obs.shape[0], obs.shape[1]
                actions_reshaped = actions.cpu().numpy().reshape(num_envs, n_agents, -1)
                log_probs_reshaped = log_probs.cpu().numpy().reshape(num_envs, n_agents)
                values_reshaped = values.cpu().numpy().reshape(num_envs, n_agents)
                return actions_reshaped, log_probs_reshaped, values_reshaped
            else:
                return actions.cpu().numpy(), log_probs.cpu().numpy(), values.cpu().numpy()
    
    
    def update(self, last_values, last_dones):
        """更新网络 - 使用MAPPORolloutBuffer的严格on-policy实现"""
        try:
            # 检查rollout buffer是否准备好更新
            if not self.buffer.is_full():
                main_logger.debug(f"Rollout buffer未满，无法更新: {len(self.buffer)}/{self.buffer.num_steps}")
                return {}
            
            main_logger.debug(f"开始MAPPO网络更新，rollout buffer已满: {len(self.buffer)} 步")
            
            # 计算GAE优势和returns
            try:
                self.buffer.compute_gae_and_returns(
                    last_values, last_dones, 
                    self.config.gamma, self.config.gae_lambda
                )
                main_logger.debug("GAE计算完成")
            except Exception as e:
                main_logger.error(f"GAE计算失败: {e}")
                return {}
            
            # 获取所有rollout数据
            all_data = self.buffer.get_all_data()
            if all_data is None:
                main_logger.error("无法获取rollout数据")
                return {}
            
            # 转换为torch张量并移到设备
            try:
                obs = torch.from_numpy(all_data['observations']).float().to(self.device)
                states = torch.from_numpy(all_data['states']).float().to(self.device)
                actions = torch.from_numpy(all_data['actions']).float().to(self.device)
                old_log_probs = torch.from_numpy(all_data['old_log_probs']).float().to(self.device)
                advantages = torch.from_numpy(all_data['advantages']).float().to(self.device)
                returns = torch.from_numpy(all_data['returns']).float().to(self.device)
                
                # 检查所有张量的健康性
                tensors_to_check = [
                    (obs, "obs"), (states, "states"), (actions, "actions"),
                    (old_log_probs, "old_log_probs"), (advantages, "advantages"), (returns, "returns")
                ]
                
                for tensor, name in tensors_to_check:
                    if not check_tensor_health(tensor, name, main_logger):
                        main_logger.error(f"张量 {name} 健康检查失败，跳过此次更新")
                        return {}
                        
            except Exception as e:
                main_logger.error(f"转换rollout数据为张量失败: {e}")
                return {}
            
            # 安全的优势标准化 - MAPPO关键步骤
            try:
                adv_mean = advantages.mean()
                adv_std = advantages.std()
                
                if adv_std < 1e-8:
                    main_logger.warning(f"优势标准差过小: {adv_std}, 跳过标准化")
                    advantages_norm = advantages
                else:
                    advantages_norm = safe_divide(
                        advantages - adv_mean, 
                        adv_std, 
                        epsilon=1e-8, 
                        logger=main_logger
                    )
                    
                if not check_tensor_health(advantages_norm, "advantages_norm", main_logger):
                    main_logger.warning("优势标准化异常，使用原始值")
                    advantages_norm = advantages
                    
                main_logger.debug(f"优势标准化: 均值={adv_mean:.6f}, 标准差={adv_std:.6f}")
                    
            except Exception as e:
                main_logger.error(f"优势标准化失败: {e}")
                advantages_norm = advantages
            
            total_actor_loss = 0
            total_critic_loss = 0
            total_entropy = 0
            total_kl_div = 0
            
            # PPO多轮更新 - 使用minibatch
            batch_size = getattr(self.config, 'batch_size', 256)
            
            for epoch in range(self.config.ppo_epochs):
                try:
                    # 使用minibatch生成器进行更新
                    minibatch_generator = self.buffer.get_minibatch_generator(batch_size)
                    if minibatch_generator is None:
                        main_logger.error(f"Epoch {epoch}: 无法获取minibatch生成器")
                        continue
                    
                    epoch_actor_loss = 0
                    epoch_critic_loss = 0
                    epoch_entropy = 0
                    epoch_kl_div = 0
                    batch_count = 0
                    
                    for batch in minibatch_generator:
                        batch_count += 1
                        
                        # 移动batch数据到设备
                        batch_obs = batch['observations'].to(self.device)
                        batch_states = batch['states'].to(self.device)
                        batch_actions = batch['actions'].to(self.device)
                        batch_old_log_probs = batch['old_log_probs'].to(self.device)
                        batch_advantages = batch['advantages'].to(self.device)
                        batch_returns = batch['returns'].to(self.device)
                        
                        # Actor更新
                        log_probs, entropy = self.actor.evaluate_actions(batch_obs, batch_actions)
                        
                        if not check_tensor_health(log_probs, f"log_probs_epoch_{epoch}_batch_{batch_count}", main_logger) or \
                           not check_tensor_health(entropy, f"entropy_epoch_{epoch}_batch_{batch_count}", main_logger):
                            main_logger.warning(f"Epoch {epoch} Batch {batch_count}: Actor评估结果异常，跳过此批次")
                            continue
                        
                        # 安全计算比率 - PPO核心
                        ratio_exp = log_probs - batch_old_log_probs
                        ratio_exp = torch.clamp(ratio_exp, min=-20, max=20)  # 限制指数范围
                        ratio = safe_exp(ratio_exp, max_value=20, logger=main_logger)
                        
                        if not check_tensor_health(ratio, f"ratio_epoch_{epoch}_batch_{batch_count}", main_logger):
                            main_logger.warning(f"Epoch {epoch} Batch {batch_count}: 比率计算异常，跳过此批次")
                            continue
                        
                        # PPO clipped surrogate objective
                        surr1 = ratio * batch_advantages
                        surr2 = torch.clamp(ratio, 1 - self.config.clip_epsilon, 1 + self.config.clip_epsilon) * batch_advantages
                        
                        # 处理entropy_coef参数
                        entropy_coef = getattr(self.config, 'entropy_coef', 0.01)
                        actor_loss = -torch.min(surr1, surr2).mean() - entropy_coef * entropy.mean()
                        
                        if not check_tensor_health(actor_loss, f"actor_loss_epoch_{epoch}_batch_{batch_count}", main_logger):
                            main_logger.warning(f"Epoch {epoch} Batch {batch_count}: Actor损失异常，跳过此批次")
                            continue
                        
                        # 更新Actor
                        self.actor_optimizer.zero_grad()
                        actor_loss.backward()
                        
                        # 监控和裁剪梯度
                        actor_grad_norm, _ = monitor_gradients(self.actor, "Actor", main_logger)
                        torch.nn.utils.clip_grad_norm_(self.actor.parameters(), self.config.max_grad_norm)
                        self.actor_optimizer.step()
                        
                        # Critic更新
                        current_values = self.critic(batch_states).squeeze()
                        
                        if not check_tensor_health(current_values, f"current_values_epoch_{epoch}_batch_{batch_count}", main_logger):
                            main_logger.warning(f"Epoch {epoch} Batch {batch_count}: 当前值函数异常，跳过此批次")
                            continue
                        
                        critic_loss = F.mse_loss(current_values, batch_returns)
                        
                        if not check_tensor_health(critic_loss, f"critic_loss_epoch_{epoch}_batch_{batch_count}", main_logger):
                            main_logger.warning(f"Epoch {epoch} Batch {batch_count}: Critic损失异常，跳过此批次")
                            continue
                        
                        # 更新Critic
                        self.critic_optimizer.zero_grad()
                        critic_loss.backward()
                        
                        # 监控和裁剪梯度
                        critic_grad_norm, _ = monitor_gradients(self.critic, "Critic", main_logger)
                        torch.nn.utils.clip_grad_norm_(self.critic.parameters(), self.config.max_grad_norm)
                        self.critic_optimizer.step()
                        
                        # 累积损失
                        epoch_actor_loss += actor_loss.item()
                        epoch_critic_loss += critic_loss.item()
                        epoch_entropy += entropy.mean().item()
                        
                        # 计算KL散度用于监控
                        with torch.no_grad():
                            kl_div = (batch_old_log_probs - log_probs).mean()
                            epoch_kl_div += kl_div.item()
                        
                        main_logger.debug(f"Epoch {epoch} Batch {batch_count}: Actor损失={actor_loss.item():.6f}, "
                                        f"Critic损失={critic_loss.item():.6f}, "
                                        f"Actor梯度范数={actor_grad_norm:.6f}, "
                                        f"Critic梯度范数={critic_grad_norm:.6f}")
                    
                    # 计算epoch平均值
                    if batch_count > 0:
                        total_actor_loss += epoch_actor_loss / batch_count
                        total_critic_loss += epoch_critic_loss / batch_count
                        total_entropy += epoch_entropy / batch_count
                        total_kl_div += epoch_kl_div / batch_count
                        
                        main_logger.debug(f"Epoch {epoch} 完成: 平均Actor损失={epoch_actor_loss/batch_count:.6f}, "
                                        f"平均Critic损失={epoch_critic_loss/batch_count:.6f}, "
                                        f"平均熵={epoch_entropy/batch_count:.6f}, "
                                        f"平均KL散度={epoch_kl_div/batch_count:.6f}")
                    
                except Exception as e:
                    main_logger.error(f"PPO Epoch {epoch} 更新失败: {e}")
                    main_logger.error(f"异常详情: {traceback.format_exc()}")
                    continue
            
            # 清空rollout buffer，准备下一个rollout
            self.buffer.clear()
            self.update_step += 1
            
            # 计算平均损失
            if self.config.ppo_epochs > 0:
                avg_actor_loss = total_actor_loss / self.config.ppo_epochs
                avg_critic_loss = total_critic_loss / self.config.ppo_epochs
                avg_entropy = total_entropy / self.config.ppo_epochs
                avg_kl_div = total_kl_div / self.config.ppo_epochs
            else:
                avg_actor_loss = 0.0
                avg_critic_loss = 0.0
                avg_entropy = 0.0
                avg_kl_div = 0.0
            
            # 记录到TensorBoard
            try:
                self.writer.add_scalar('Training/Actor_Loss', avg_actor_loss, self.update_step)
                self.writer.add_scalar('Training/Critic_Loss', avg_critic_loss, self.update_step)
                self.writer.add_scalar('Training/Entropy', avg_entropy, self.update_step)
                self.writer.add_scalar('Training/KL_Divergence', avg_kl_div, self.update_step)
                self.writer.add_scalar('Training/Advantages_Mean', advantages.mean().item(), self.update_step)
                self.writer.add_scalar('Training/Advantages_Std', advantages.std().item(), self.update_step)
                self.writer.add_scalar('Training/Returns_Mean', returns.mean().item(), self.update_step)
                
                # 记录内存使用情况
                if torch.cuda.is_available():
                    gpu_memory = torch.cuda.memory_allocated() / (1024**3)
                    self.writer.add_scalar('Memory/GPU_Memory_GB', gpu_memory, self.update_step)
                    
            except Exception as e:
                main_logger.warning(f"记录TensorBoard数据失败: {e}")
            
            main_logger.info(f"MAPPO网络更新完成: Actor损失={avg_actor_loss:.6f}, Critic损失={avg_critic_loss:.6f}, "
                           f"熵={avg_entropy:.6f}, KL散度={avg_kl_div:.6f}")
            
            return {
                'actor_loss': avg_actor_loss,
                'critic_loss': avg_critic_loss,
                'entropy': avg_entropy,
                'kl_divergence': avg_kl_div,
                'update_step': self.update_step,
                'advantages_mean': advantages.mean().item(),
                'advantages_std': advantages.std().item(),
                'returns_mean': returns.mean().item()
            }
            
        except Exception as e:
            main_logger.error(f"MAPPO网络更新发生未捕获的异常: {e}")
            main_logger.error(f"异常详情: {traceback.format_exc()}")
            
            # 尝试清理GPU内存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # 强制垃圾回收
            gc.collect()
            
            return {
                'error': str(e),
                'update_step': self.update_step
            }
    
    
    def save_model(self, path):
        """保存模型"""
        torch.save({
            'actor_state_dict': self.actor.state_dict(),
            'critic_state_dict': self.critic.state_dict(),
            'actor_optimizer_state_dict': self.actor_optimizer.state_dict(),
            'critic_optimizer_state_dict': self.critic_optimizer.state_dict(),
            'config': self.config
        }, path)
    
    def log_scenario4_metrics(self, infos, total_steps):
        """记录场景4特有的网络健康度指标到TensorBoard"""
        try:
            # 收集所有环境的网络健康度指标
            health_scores = []
            connectivity_scores = []
            role_diversity_scores = []
            coverage_scores = []
            dispersion_penalties = []
            serving_uav_counts = []
            relay_uav_counts = []
            weighted_serving_scores = []
            
            for info in infos:
                if 'reward_info' in info:
                    reward_info = info['reward_info']
                    
                    # 提取网络健康度组件
                    if 'rt_final_health_score' in reward_info:
                        health_scores.append(reward_info['rt_final_health_score'])
                    if 'connectivity_score' in reward_info:
                        connectivity_scores.append(reward_info['connectivity_score'])
                    if 'role_diversity_bonus' in reward_info:
                        role_diversity_scores.append(reward_info['role_diversity_bonus'])
                    if 'effective_coverage_score' in reward_info:
                        coverage_scores.append(reward_info['effective_coverage_score'])
                    if 'dispersion_penalty' in reward_info:
                        dispersion_penalties.append(reward_info['dispersion_penalty'])
                    if 'serving_uavs_count' in reward_info:
                        serving_uav_counts.append(reward_info['serving_uavs_count'])
                    if 'pure_relay_uavs_count' in reward_info:
                        relay_uav_counts.append(reward_info['pure_relay_uavs_count'])
                    if 'weighted_serving_score' in reward_info:
                        weighted_serving_scores.append(reward_info['weighted_serving_score'])
            
            # 计算平均值并记录到TensorBoard
            if health_scores:
                avg_health_score = np.mean(health_scores)
                self.writer.add_scalar('Scenario4/Network_Health_Score', avg_health_score, total_steps)
                
            if connectivity_scores:
                avg_connectivity = np.mean(connectivity_scores)
                self.writer.add_scalar('Scenario4/Connectivity_Score', avg_connectivity, total_steps)
                
            if role_diversity_scores:
                avg_role_diversity = np.mean(role_diversity_scores)
                self.writer.add_scalar('Scenario4/Role_Diversity_Bonus', avg_role_diversity, total_steps)
                
            if coverage_scores:
                avg_coverage = np.mean(coverage_scores)
                self.writer.add_scalar('Scenario4/Effective_Coverage_Score', avg_coverage, total_steps)
                
            if dispersion_penalties:
                avg_dispersion = np.mean(dispersion_penalties)
                self.writer.add_scalar('Scenario4/Dispersion_Penalty', avg_dispersion, total_steps)
                
            if serving_uav_counts:
                avg_serving_uavs = np.mean(serving_uav_counts)
                self.writer.add_scalar('Scenario4/Serving_UAVs_Count', avg_serving_uavs, total_steps)
                
            if relay_uav_counts:
                avg_relay_uavs = np.mean(relay_uav_counts)
                self.writer.add_scalar('Scenario4/Pure_Relay_UAVs_Count', avg_relay_uavs, total_steps)
                
            if weighted_serving_scores:
                avg_weighted_serving = np.mean(weighted_serving_scores)
                self.writer.add_scalar('Scenario4/Weighted_Serving_Score', avg_weighted_serving, total_steps)
                
            # 计算角色平衡指标
            if serving_uav_counts and relay_uav_counts:
                role_balance_scores = []
                for serving, relay in zip(serving_uav_counts, relay_uav_counts):
                    total_active = serving + relay
                    if total_active > 0:
                        balance = min(serving, relay) / total_active
                    else:
                        balance = 0
                    role_balance_scores.append(balance)
                
                if role_balance_scores:
                    avg_role_balance = np.mean(role_balance_scores)
                    self.writer.add_scalar('Scenario4/Role_Balance_Score', avg_role_balance, total_steps)
            
            main_logger.debug(f"已记录场景4网络健康度指标到TensorBoard (步骤 {total_steps})")
            
        except Exception as e:
            main_logger.warning(f"记录场景4指标失败: {e}")
    
    def load_model(self, path):
        """加载模型"""
        # 导入 Config 类并将其添加到安全列表
        from config_1 import Config
        torch.serialization.add_safe_globals([Config])
        
        checkpoint = torch.load(path, map_location=self.device)
        self.actor.load_state_dict(checkpoint['actor_state_dict'])
        self.critic.load_state_dict(checkpoint['critic_state_dict'])
        self.actor_optimizer.load_state_dict(checkpoint['actor_optimizer_state_dict'])
        self.critic_optimizer.load_state_dict(checkpoint['critic_optimizer_state_dict'])


def get_device(device_pref):
    """根据偏好选择计算设备"""
    if device_pref == 'auto':
        if torch.cuda.is_available():
            main_logger.info("检测到GPU可用，使用CUDA")
            return 'cuda'
        else:
            main_logger.info("未检测到GPU，使用CPU")
            return 'cpu'
    elif device_pref == 'cuda':
        if torch.cuda.is_available():
            main_logger.info("使用CUDA")
            return 'cuda'
        else:
            main_logger.warning("请求使用CUDA但未检测到GPU，回退到CPU")
            return 'cpu'
    else:
        main_logger.info("使用CPU")
        return 'cpu'

def make_env(scenario, config, rank=0, seed=0, render_mode=None, **kwargs):
    """创建环境实例的函数 - 优化为使用config参数"""
    def _init():
        env_seed = seed + rank
        if scenario == 1:
            raw_env = UAVBaseStationEnv(
                n_uavs=config.n_agents,
                n_users=config.n_users,
                user_distribution=config.user_distribution,
                channel_model=config.channel_model,
                render_mode=render_mode,
                seed=env_seed
            )
        elif scenario == 2:
            raw_env = UAVCooperativeNetworkEnv(
                n_uavs=config.n_agents,
                n_users=config.n_users,
                max_hops=config.max_hops,
                user_distribution=config.user_distribution,
                channel_model=config.channel_model,
                render_mode=render_mode,
                seed=env_seed
            )
        elif scenario == 3:
            raw_env = UAVMultiHopEnv(
                n_uavs=config.n_agents,
                n_users=config.n_users,
                user_distribution=config.user_distribution,
                channel_model=config.channel_model,
                max_hops=config.max_hops,
                render_mode=render_mode,
                seed=env_seed,
                area_size=config.area_size,
                n_clusters=config.n_clusters,
                cluster_std=config.cluster_std,
                central_area_ratio=config.central_area_ratio
            )
        elif scenario == 4:
            # 场景4：强制多跳中继环境 - 使用config_1.py中的参数
            # 注意：UAVForcedRelayEnv不接受channel_model参数，它使用自己的精确信道模型
            scenario4_kwargs = {
                'n_uavs': config.n_agents,
                'n_users': config.n_users,
                'user_distribution': 'forced_relay_cluster',  # 场景4强制使用此分布类型
                'render_mode': render_mode,
                'seed': env_seed,
                'max_hops': config.max_hops,
                'area_size': config.area_size,
                'n_clusters': config.n_clusters,
                'cluster_std': config.cluster_std,
                'central_area_ratio': config.central_area_ratio,
                'min_sinr': config.min_sinr,
                'max_connections': config.max_connections,
                'uav_init_mode': config.uav_init_mode,
                'uav_start_area_size': config.uav_start_area_size,
                'use_fdma': config.use_fdma,
                'bandwidth': config.bandwidth,
                'observation_radius': config.observation_radius,
                'max_observed_uavs': config.max_observed_uavs,
                'max_observed_users': config.max_observed_users,
                'max_observed_bs': config.max_observed_bs,
                'test_reward_mode': config.test_reward_mode,
                # 网络健康度权重
                'w_connectivity': config.w_connectivity,
                'w_diversity': config.w_diversity,
                'w_coverage': config.w_coverage,
                'w_dispersion': config.w_dispersion,
            }
            
            # 添加kwargs中的覆盖参数
            scenario4_kwargs.update(kwargs)
            
            # 过滤掉值为None的参数，以便环境使用其内部默认值
            scenario4_kwargs = {k: v for k, v in scenario4_kwargs.items() if v is not None}
            
            raw_env = UAVForcedRelayEnv(**scenario4_kwargs)
        else:
            raise ValueError(f"未知的场景: {scenario}")

        env = ParallelToArrayAdapter(raw_env, seed=env_seed)
        return env

    return _init

def parse_args():
    """精简的命令行参数解析 - 优先使用config_1.py中的参数"""
    parser = argparse.ArgumentParser(description='基于MAPPO的增强训练，适配场景4和config_1.py')
    
    # 核心运行参数
    parser.add_argument('--mode', type=str, default='train', 
                        choices=['train', 'eval'], help='运行模式')
    parser.add_argument('--scenario', type=int, default=4, 
                        help='场景: 1=基站模式, 2=协作组网模式, 3=强制多跳模式, 4=强制中继模式')
    parser.add_argument('--model_path', type=str, default='models/mappo_scenario4_enhanced.pt', 
                        help='模型保存/加载路径')
    parser.add_argument('--log_dir', type=str, default='../tf-logs', help='日志目录')
    
    # 日志控制
    parser.add_argument('--log_level', type=str, default='info', 
                        choices=['debug', 'info', 'warning', 'error', 'critical'], 
                        help='文件日志级别')
    parser.add_argument('--console_log_level', type=str, default='info', 
                        choices=['debug', 'info', 'warning', 'error', 'critical'], 
                        help='控制台日志级别')
    
    # 设备和渲染
    parser.add_argument('--device', type=str, default='auto', 
                        choices=['auto', 'cuda', 'cpu'], help='计算设备')
    parser.add_argument('--render', action='store_true', help='是否渲染环境（仅评估模式）')
    
    # 评估参数
    parser.add_argument('--eval_episodes', type=int, default=10, help='评估的episode数量')
    
    # 数据收集控制
    parser.add_argument('--detailed_logging', action='store_true', 
                        help='启用详细的TensorBoard和控制台日志记录')
    parser.add_argument('--export_interval', type=int, default=5000, 
                        help='数据导出间隔步数（基于config中的export_interval_multiplier）')
    
    # 配置覆盖参数（可选，用于临时调试）
    parser.add_argument('--test_reward_mode', action='store_true', 
                        help='启用测试奖励模式（覆盖config设置）')
    parser.add_argument('--short_test', action='store_true', 
                        help='启用短时间测试模式')
    
    return parser.parse_args()

def train(config, args, device):
    """MAPPO训练函数 - GPU加速版本，使用SubprocVecEnv，适配scenario4"""
    main_logger.info("开始MAPPO训练（GPU加速版本）...")

    # 确认从配置中读取的环境数量
    num_envs = config.num_envs
    main_logger.info(f"从配置中读取的训练环境数量: {num_envs}")
    
    # 创建日志目录
    log_dir = os.path.join(args.log_dir, f"mappo_scenario4_{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(log_dir, exist_ok=True)
    model_dir = os.path.dirname(args.model_path)
    os.makedirs(model_dir, exist_ok=True)
    
    # 创建环境 - 使用config参数
    base_seed = getattr(config, 'seed', int(time.time()))
    main_logger.info(f"基础种子: {base_seed}")

    env_fns = [make_env(
        scenario=args.scenario,
        config=config,
        rank=i,
        seed=base_seed,
        render_mode=None
    ) for i in range(num_envs)]

    # 使用SubprocVecEnv创建并行环境
    actual_num_envs = num_envs  # 记录实际环境数量
    try:
        main_logger.info(f"尝试创建 {len(env_fns)} 个并行环境...")
        envs = SubprocVecEnv(env_fns)
        main_logger.info("SubprocVecEnv创建成功")
        # 验证SubprocVecEnv的环境数量
        actual_num_envs = envs.num_envs
        main_logger.info(f"SubprocVecEnv实际环境数量: {actual_num_envs}")
    except Exception as e:
        main_logger.error(f"SubprocVecEnv创建失败: {e}")
        main_logger.info("回退到单个环境实例")
        envs = [env_fn() for env_fn in env_fns]
        actual_num_envs = len(envs)
        main_logger.info(f"回退模式实际环境数量: {actual_num_envs}")
        sample_env = envs[0]
        n_agents = sample_env.n_uavs
        obs_dim = sample_env.obs_dim
        state_dim = sample_env.state_dim
        action_dim = sample_env.action_dim
    else:
        # 获取环境信息（从单个环境实例）
        sample_env = env_fns[0]()
        n_agents = sample_env.n_uavs
        obs_dim = sample_env.obs_dim
        state_dim = sample_env.state_dim
        action_dim = sample_env.action_dim
        sample_env.close()  # 关闭临时环境
    
    # 检查环境数量不匹配的情况
    if actual_num_envs != num_envs:
        main_logger.warning(f"配置的环境数量({num_envs})与实际环境数量({actual_num_envs})不匹配")
        main_logger.info(f"将使用实际环境数量: {actual_num_envs}")
        # 更新配置中的环境数量
        config.num_envs = actual_num_envs
        num_envs = actual_num_envs
        main_logger.info(f"配置中的num_envs已更新为: {config.num_envs}")
    
    # 更新配置 - 使用config中的参数，只在必要时使用args覆盖
    config.n_agents = n_agents
    config.obs_dim = obs_dim
    config.state_dim = state_dim
    config.action_dim = action_dim
    
    # 应用配置覆盖（如果通过命令行指定）
    if hasattr(args, 'test_reward_mode') and args.test_reward_mode:
        config.test_reward_mode = True
        main_logger.info("启用测试奖励模式（命令行覆盖）")
    
    if hasattr(args, 'short_test') and args.short_test:
        config.set_short_test_mode()
        main_logger.info("启用短时间测试模式")
    
    # 更新环境维度并计算buffer大小
    config.update_env_dims(state_dim, obs_dim, n_agents)
    
    main_logger.info(f"环境信息: n_agents={n_agents}, obs_dim={obs_dim}, state_dim={state_dim}, action_dim={action_dim}")

    # 创建MAPPO智能体
    agent = MAPPOAgent(config, log_dir, device)
    
    # 创建增强的奖励追踪器 - 使用config参数
    reward_tracker = EnhancedRewardTracker(log_dir, config, n_users=config.n_users)
    reward_tracker.export_interval = args.export_interval
    
    # 为场景4添加网络健康度指标追踪
    if args.scenario == 4:
        reward_tracker.performance_metrics['network_health_scores'] = []
        main_logger.info("已启用场景4网络健康度指标追踪")
    
    # 初始化环境
    if isinstance(envs, SubprocVecEnv):
        # 使用SubprocVecEnv的向量化接口
        observations = envs.reset()
        # 从第一个环境获取状态信息（假设所有环境状态维度相同）
        states = np.zeros((num_envs, state_dim))
        main_logger.info("使用SubprocVecEnv向量化接口初始化环境")
    else:
        # 回退到原始方式
        observations = []
        states = []
        for env in envs:
            obs, info = env.reset()
            observations.append(obs)
            states.append(info.get('state', np.zeros(state_dim)))
        
        observations = np.array(observations)
        states = np.array(states)
        main_logger.info("使用传统方式初始化环境")
    
    # 训练循环
    total_steps = 0
    episode_count = 0
    env_episode_rewards = np.zeros(num_envs)
    env_episode_lengths = np.zeros(num_envs, dtype=int)
    
    start_time = time.time()
    
    # 增强的训练循环 - 添加异常处理和监控
    consecutive_errors = 0
    max_consecutive_errors = 10
    last_save_step = 0
    save_interval = 5000
    
    # 严格on-policy训练循环 - 基于rollout的训练模式
    rollout_steps = 0  # 当前rollout中的步数
    
    while total_steps < config.total_timesteps:
        try:
            rollout_throughputs = []
            rollout_service_rates = []
            # 定期记录内存使用情况
            # if total_steps % 1000 == 0:
            #     log_memory_usage(main_logger, total_steps)
            
            # 收集rollout数据 - 固定长度的数据收集
            for rollout_step in range(config.rollout_length):
                # 检查buffer是否已满，如果满了就跳出收集循环
                if agent.buffer.is_full():
                    main_logger.debug(f"Rollout buffer已满，跳出数据收集循环")
                    break
                
                # 选择动作
                try:
                    actions, log_probs, values = agent.select_actions(observations, states)
                    
                    # 检查动作的有效性
                    if not isinstance(actions, np.ndarray) or np.isnan(actions).any() or np.isinf(actions).any():
                        main_logger.error(f"步骤 {total_steps}: 动作选择异常，跳过此步")
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            main_logger.error(f"连续错误达到 {max_consecutive_errors} 次，退出训练")
                            break
                        continue
                    
                except Exception as e:
                    main_logger.error(f"步骤 {total_steps}: 动作选择失败: {e}")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        main_logger.error(f"连续错误达到 {max_consecutive_errors} 次，退出训练")
                        break
                    continue
                
                # 执行动作 - 支持SubprocVecEnv和传统环境
                if isinstance(envs, SubprocVecEnv):
                    # 使用SubprocVecEnv的向量化接口
                    try:
                        next_observations, rewards, dones, infos = envs.step(actions)
                        
                        # SubprocVecEnv返回的dones可能是terminated和truncated的组合
                        if isinstance(dones, tuple) and len(dones) == 2:
                            terminated, truncated = dones
                            dones = np.logical_or(terminated, truncated)
                        
                        # 从infos字典中提取真实的全局状态
                        next_states = np.array([info.get('state', np.zeros(state_dim)) for info in infos])
                        
                        # 验证向量化环境返回值
                        if next_observations is None or np.isnan(next_observations).any() or np.isinf(next_observations).any():
                            main_logger.warning(f"步骤 {total_steps}: SubprocVecEnv返回异常观察值")
                            next_observations = observations  # 使用上一步的观察
                        
                        if np.isnan(rewards).any() or np.isinf(rewards).any():
                            main_logger.warning(f"步骤 {total_steps}: SubprocVecEnv返回异常奖励值")
                            rewards = np.zeros(num_envs)  # 使用默认奖励
                        
                        env_step_success = True
                        
                    except Exception as e:
                        main_logger.error(f"步骤 {total_steps}: SubprocVecEnv步骤执行失败: {e}")
                        # 使用安全的默认值
                        next_observations = observations
                        next_states = states
                        rewards = np.zeros(num_envs)
                        dones = np.zeros(num_envs, dtype=bool)
                        infos = [{}] * num_envs
                        env_step_success = False
                        
                else:
                    # 传统环境循环方式
                    next_observations = []
                    next_states = []
                    rewards = []
                    dones = []
                    infos = []
                    
                    env_step_success = True
                    
                    for i, env in enumerate(envs):
                        try:
                            next_obs, reward, terminated, truncated, info = env.step(actions[i])
                            done = bool(terminated or truncated)  # 显式转换为Python bool
                            
                            # 验证环境返回值
                            if next_obs is None or np.isnan(next_obs).any() or np.isinf(next_obs).any():
                                main_logger.warning(f"步骤 {total_steps}: 环境{i}返回异常观察值")
                                next_obs = observations[i]  # 使用上一步的观察
                            
                            if not isinstance(reward, (int, float)) or np.isnan(reward) or np.isinf(reward):
                                main_logger.warning(f"步骤 {total_steps}: 环境{i}返回异常奖励值: {reward}")
                                reward = 0.0  # 使用默认奖励
                            
                            next_observations.append(next_obs)
                            next_states.append(info.get('next_state', np.zeros(state_dim)))
                            rewards.append(reward)
                            dones.append(done)
                            infos.append(info)
                            
                        except Exception as e:
                            main_logger.error(f"步骤 {total_steps}: 环境{i}步骤执行失败: {e}")
                            # 使用安全的默认值
                            next_observations.append(observations[i])
                            next_states.append(states[i])
                            rewards.append(0.0)
                            dones.append(False)
                            infos.append({})
                            env_step_success = False
                    
                    # 转换为数组
                    try:
                        next_observations = np.array(next_observations)
                        next_states = np.array(next_states)
                        rewards = np.array(rewards)
                        dones = np.array(dones)
                        
                    except Exception as e:
                        main_logger.error(f"步骤 {total_steps}: 数组转换失败: {e}")
                        consecutive_errors += 1
                        continue
                
                if not env_step_success:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        main_logger.error(f"连续错误达到 {max_consecutive_errors} 次，退出训练")
                        break
                    continue
                
                # 记录训练步骤信息
                for i, info in enumerate(infos):
                    try:
                        # 计算每个智能体的奖励（简化处理）
                        agent_rewards = [rewards[i]] * n_agents
                        
                        # 记录训练步骤信息，包括吞吐量和服务用户数
                        reward_tracker.log_training_step(
                            step=total_steps + i,  # 为每个环境分配不同的步骤编号
                            env_id=i,
                            reward=rewards[i],
                            agent_rewards=agent_rewards,
                            info=info
                        )
                        
                        # 场景4特有：记录网络健康度指标到reward_tracker
                        if args.scenario == 4 and 'reward_info' in info:
                            reward_info = info['reward_info']
                            health_data = {
                                'step': total_steps + i,
                                'env_id': i,
                                'health_score': reward_info.get('rt_final_health_score', 0),
                                'connectivity_score': reward_info.get('connectivity_score', 0),
                                'role_diversity_bonus': reward_info.get('role_diversity_bonus', 0),
                                'effective_coverage_score': reward_info.get('effective_coverage_score', 0),
                                'dispersion_penalty': reward_info.get('dispersion_penalty', 0),
                                'serving_uavs_count': reward_info.get('serving_uavs_count', 0),
                                'pure_relay_uavs_count': reward_info.get('pure_relay_uavs_count', 0),
                                'weighted_serving_score': reward_info.get('weighted_serving_score', 0),
                                'timestamp': time.time()
                            }
                            reward_tracker.performance_metrics['network_health_scores'].append(health_data)
                        
                        # 如果启用了详细日志，则记录更多信息到控制台
                        if args.detailed_logging:
                            if 'reward_info' in info and 'system_throughput_mbps' in info['reward_info']:
                                throughput_mbps = info['reward_info']['system_throughput_mbps']
                                main_logger.debug(f"步骤 {total_steps}: 环境{i} 系统吞吐量={throughput_mbps:.2f} Mbps")
                            
                            if 'reward_info' in info and 'avg_throughput_per_user_mbps' in info['reward_info']:
                                avg_throughput_mbps = info['reward_info']['avg_throughput_per_user_mbps']
                                main_logger.debug(f"步骤 {total_steps}: 环境{i} 平均用户吞吐量={avg_throughput_mbps:.2f} Mbps")
                            
                            # 场景4详细日志：网络健康度组件
                            if args.scenario == 4 and 'reward_info' in info:
                                reward_info = info['reward_info']
                                main_logger.debug(f"步骤 {total_steps}: 环境{i} 网络健康度={reward_info.get('rt_final_health_score', 0):.3f}, "
                                                f"连接性={reward_info.get('connectivity_score', 0):.3f}, "
                                                f"角色多样性={reward_info.get('role_diversity_bonus', 0):.3f}, "
                                                f"覆盖率={reward_info.get('effective_coverage_score', 0):.3f}")
                                
                    except Exception as log_e:
                        main_logger.warning(f"步骤 {total_steps}: 记录环境{i}信息失败: {log_e}")
                
                # 从info中收集吞吐量和用户服务率数据
                for info in infos:
                    if 'reward_info' in info and 'system_throughput_mbps' in info['reward_info']:
                        rollout_throughputs.append(info['reward_info']['system_throughput_mbps'])
                    
                    # 记录用户服务率
                    if 'served_users' in info and 'total_users' in info and info['total_users'] > 0:
                        service_rate = info['served_users'] / info['total_users']
                        rollout_service_rates.append(service_rate)
                
                # 验证数组健康性
                if np.isnan(next_observations).any() or np.isinf(next_observations).any():
                    main_logger.error(f"步骤 {total_steps}: next_observations包含异常值")
                    consecutive_errors += 1
                    continue
                    
                if np.isnan(rewards).any() or np.isinf(rewards).any():
                    main_logger.error(f"步骤 {total_steps}: rewards包含异常值")
                    consecutive_errors += 1
                    continue
                
                # 存储经验 - 修复为逐个环境存储，参考hmasd/utils.py的RolloutBuffer.add方法
                try:
                    # 验证数据有效性
                    if np.isnan(rewards).any() or np.isinf(rewards).any():
                        main_logger.warning(f"步骤 {total_steps}: 奖励异常，使用零值")
                        rewards = np.zeros_like(rewards)
                    
                    # 逐个环境存储数据 - 参考hmasd/utils.py的RolloutBuffer.add方法
                    storage_success = True
                    for env_idx in range(num_envs):
                        try:
                            # 提取单个环境的数据
                            env_obs = observations[env_idx]  # (n_agents, obs_dim)
                            env_next_obs = next_observations[env_idx]  # (n_agents, obs_dim)
                            env_state = states[env_idx]  # (state_dim,)
                            env_next_state = next_states[env_idx]  # (state_dim,)
                            env_actions = actions[env_idx]  # (n_agents, action_dim)
                            env_log_probs = log_probs[env_idx]  # (n_agents,)
                            env_values = values[env_idx]  # (n_agents,)
                            
                            # 处理奖励和done标志 - 扩展为多智能体格式
                            if rewards.ndim == 1:  # 环境级别奖励
                                env_reward = np.full(n_agents, rewards[env_idx], dtype=np.float32)
                            else:  # 已经是多智能体格式
                                env_reward = rewards[env_idx]
                            
                            if dones.ndim == 1:  # 环境级别done
                                env_done = np.full(n_agents, dones[env_idx], dtype=bool)
                            else:  # 已经是多智能体格式
                                env_done = dones[env_idx]
                            
                            # 调用buffer的add方法存储单个环境的数据
                            success = agent.buffer.add(
                                t=rollout_step,  # 使用rollout步骤索引，而不是buffer.step
                                state=env_state,
                                obs=env_obs,
                                action=env_actions,
                                reward=env_reward,
                                done=env_done,
                                value=env_values,
                                log_prob=env_log_probs,
                                gru_hidden_state=torch.zeros(n_agents, 64),  # 占位符，MAPPO不使用GRU
                                env_idx=env_idx
                            )
                            
                            if not success:
                                main_logger.warning(f"环境{env_idx}数据存储失败")
                                storage_success = False
                                
                        except Exception as env_e:
                            main_logger.error(f"环境{env_idx}数据存储异常: {env_e}")
                            storage_success = False
                    
                    # 只有所有环境都存储成功才推进buffer步数
                    if storage_success:
                        agent.buffer.step += 1
                        
                        # 【关键修复】检查buffer是否已满，设置ready_for_update标志
                        if agent.buffer.is_full():
                            agent.buffer.ready_for_update = True
                            main_logger.debug(f"Rollout buffer已满，设置ready_for_update=True: step={agent.buffer.step}")
                        
                        main_logger.debug(f"成功存储所有环境数据到rollout buffer: step={agent.buffer.step-1}, "
                                        f"奖励均值={np.mean(rewards):.4f}")
                    else:
                        main_logger.warning(f"部分环境数据存储失败，不推进buffer步数")
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            main_logger.error(f"连续错误达到 {max_consecutive_errors} 次，退出训练")
                            break
                        continue
                        
                except Exception as e:
                    main_logger.error(f"步骤 {total_steps}: 存储经验失败: {e}")
                    main_logger.error(f"数据形状调试: observations={observations.shape}, actions={actions.shape}, "
                                    f"rewards={rewards.shape}, dones={dones.shape}, log_probs={log_probs.shape}, values={values.shape}")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        main_logger.error(f"连续错误达到 {max_consecutive_errors} 次，退出训练")
                        break
                    continue
                
                # 更新环境奖励和长度
                env_episode_rewards += rewards
                env_episode_lengths += 1
                
                # 处理episode结束 - 支持SubprocVecEnv和传统环境
                for i, done in enumerate(dones):
                    if done:
                        episode_count += 1
                        
                        try:
                            # 记录episode完成
                            agent_rewards = [env_episode_rewards[i]] * n_agents  # 简化处理
                            reward_tracker.log_episode_completion(
                                episode_count, i, env_episode_rewards[i], 
                                env_episode_lengths[i], agent_rewards, infos[i]
                            )
                            
                            main_logger.info(f"Episode {episode_count}: 环境{i}, 奖励={env_episode_rewards[i]:.2f}, 长度={env_episode_lengths[i]}")
                            
                            # 重置环境状态（SubprocVecEnv会自动重置）
                            if not isinstance(envs, SubprocVecEnv):
                                # 传统环境需要手动重置
                                obs, info = envs[i].reset()
                                
                                # 验证重置后的观察
                                if obs is None or np.isnan(obs).any() or np.isinf(obs).any():
                                    main_logger.error(f"环境{i}重置后观察异常")
                                    obs = np.zeros_like(observations[i])
                                    
                                observations[i] = obs
                                states[i] = info.get('state', np.zeros(state_dim))
                            
                            # 重置奖励和长度计数器
                            env_episode_rewards[i] = 0
                            env_episode_lengths[i] = 0
                            
                        except Exception as e:
                            main_logger.error(f"处理环境{i} episode结束时失败: {e}")
                            # 强制重置
                            if not isinstance(envs, SubprocVecEnv):
                                try:
                                    obs, info = envs[i].reset()
                                    observations[i] = obs if obs is not None else np.zeros_like(observations[i])
                                    states[i] = info.get('state', np.zeros(state_dim)) if info else np.zeros(state_dim)
                                except:
                                    main_logger.error(f"环境{i}强制重置也失败")
                            
                            env_episode_rewards[i] = 0
                            env_episode_lengths[i] = 0
                
                # 更新状态
                observations = next_observations
                states = next_states
                total_steps += num_envs
                rollout_steps += 1
                
                # 重置连续错误计数器
                consecutive_errors = 0
                
                # 如果达到总步数限制，跳出rollout收集循环
                if total_steps >= config.total_timesteps:
                    break
            
            # Rollout数据收集完成，进行网络更新
            try:
                # 记录rollout的平均吞吐量
                if rollout_throughputs:
                    avg_throughput = np.mean(rollout_throughputs)
                    agent.writer.add_scalar('Performance/System_Throughput_Mbps', avg_throughput, total_steps)
                    main_logger.debug(f"Rollout Throughput: Avg={avg_throughput:.2f} Mbps over {len(rollout_throughputs)} samples")

                # 记录用户服务率 (与 train_multiproc_config_1.py 保持一致)
                if reward_tracker.performance_metrics['served_users'] and reward_tracker.n_users is not None:
                    # 使用最近1000个数据点计算滑动平均
                    recent_served_data = reward_tracker.performance_metrics['served_users'][-1000:]
                    if recent_served_data:
                        recent_served_users = [u['served_users'] for u in recent_served_data]
                        avg_served_users = np.mean(recent_served_users)
                        
                        # 使用固定的 n_users 计算服务率
                        service_rate = avg_served_users / reward_tracker.n_users
                        agent.writer.add_scalar('Performance/User_Service_Rate_1000steps', service_rate, total_steps)
                        main_logger.debug(f"User Service Rate (1000 steps avg): {service_rate:.4f}")

                # 场景4特有：记录网络健康度指标到TensorBoard
                if args.scenario == 4:
                    # 从最近收集的infos中提取网络健康度指标
                    recent_infos = []
                    if isinstance(envs, SubprocVecEnv):
                        # 使用最后一步的infos
                        recent_infos = infos if 'infos' in locals() else []
                    else:
                        # 传统环境的infos已经在上面定义
                        recent_infos = infos if 'infos' in locals() else []
                    
                    if recent_infos:
                        agent.log_scenario4_metrics(recent_infos, total_steps)

                # 检查rollout buffer是否已满，准备进行MAPPO更新
                if agent.buffer.is_full():
                    # 计算最后一步的值函数和done状态，用于GAE计算
                    try:
                        with torch.no_grad():
                            # 获取当前状态的值函数作为last_values
                            _, _, last_values = agent.select_actions(observations, states, deterministic=True)
                            
                            # 当前步骤不是done状态（因为我们还在继续训练）
                            last_dones = np.zeros(num_envs, dtype=bool)
                            
                        # 执行MAPPO更新
                        update_info = agent.update(last_values, last_dones)
                        
                        if update_info and 'error' not in update_info:
                            main_logger.info(f"MAPPO Rollout更新完成 (收集了 {config.rollout_length} 步), 总步数 {total_steps}, "
                                  f"Actor损失={update_info['actor_loss']:.4f}, Critic损失={update_info['critic_loss']:.4f}, "
                                  f"熵={update_info['entropy']:.4f}, KL散度={update_info['kl_divergence']:.4f}")
                        elif 'error' in update_info:
                            main_logger.error(f"步骤 {total_steps}: MAPPO网络更新失败: {update_info['error']}")
                            
                    except Exception as update_e:
                        main_logger.error(f"步骤 {total_steps}: MAPPO更新过程失败: {update_e}")
                        # 清空buffer以避免数据积累
                        agent.buffer.clear()
                        
                    main_logger.debug(f"Rollout完成，buffer已清空，开始新的rollout")
                else:
                    main_logger.debug(f"Rollout buffer未满，继续收集数据: {len(agent.buffer)}/{config.rollout_length}")
                        
            except Exception as e:
                main_logger.error(f"步骤 {total_steps}: 网络更新异常: {e}")
                main_logger.error(f"异常详情: {traceback.format_exc()}")
            
            # 重置rollout步数计数器
            rollout_steps = 0
            
            # 定期保存模型和导出数据
            try:
                # 定期导出数据
                if total_steps % reward_tracker.export_interval == 0:
                    reward_tracker.export_training_data(total_steps)
                
                # 定期保存模型
                if total_steps - last_save_step >= save_interval:
                    agent.save_model(args.model_path)
                    main_logger.info(f"步骤 {total_steps}: 模型已保存")
                    last_save_step = total_steps
                    
            except Exception as e:
                main_logger.error(f"步骤 {total_steps}: 保存模型或导出数据失败: {e}")
            
            # 定期清理内存 - 增强版本
            if total_steps % 1000 == 0:  # 更频繁的清理
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                gc.collect()
                main_logger.debug(f"步骤 {total_steps}: 定期内存清理完成")
            
            # 深度内存清理
            if total_steps % 10000 == 0:
                if torch.cuda.is_available():
                    # 重置GPU内存统计
                    torch.cuda.reset_peak_memory_stats()
                    torch.cuda.empty_cache()
                    main_logger.info(f"步骤 {total_steps}: 深度GPU内存清理完成")
                
                # 强制Python垃圾回收
                collected = gc.collect()
                main_logger.info(f"步骤 {total_steps}: 垃圾回收清理了 {collected} 个对象")
                
        except KeyboardInterrupt:
            main_logger.info("接收到中断信号，保存当前进度并退出...")
            try:
                agent.save_model(args.model_path)
                reward_tracker.export_training_data(total_steps)
                main_logger.info("进度保存完成")
            except Exception as e:
                main_logger.error(f"保存进度失败: {e}")
            break
            
        except Exception as e:
            main_logger.error(f"步骤 {total_steps}: 训练循环发生未捕获异常: {e}")
            main_logger.error(f"异常详情: {traceback.format_exc()}")
            consecutive_errors += 1
            
            if consecutive_errors >= max_consecutive_errors:
                main_logger.error(f"连续错误达到 {max_consecutive_errors} 次，退出训练")
                break
                
            # 尝试恢复
            try:
                # 清理GPU内存
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                gc.collect()
                
                # 重置环境状态 - 支持SubprocVecEnv和传统环境
                if isinstance(envs, SubprocVecEnv):
                    try:
                        observations = envs.reset()
                        states = np.zeros((num_envs, state_dim))
                        env_episode_rewards = np.zeros(num_envs)
                        env_episode_lengths = np.zeros(num_envs, dtype=int)
                        main_logger.info("SubprocVecEnv环境重置成功")
                    except Exception as reset_e:
                        main_logger.error(f"SubprocVecEnv重置失败: {reset_e}")
                else:
                    for i, env in enumerate(envs):
                        try:
                            obs, info = env.reset()
                            observations[i] = obs if obs is not None else np.zeros_like(observations[i])
                            states[i] = info.get('state', np.zeros(state_dim)) if info else np.zeros(state_dim)
                            env_episode_rewards[i] = 0
                            env_episode_lengths[i] = 0
                        except Exception as reset_e:
                            main_logger.error(f"重置环境{i}失败: {reset_e}")
                        
                main_logger.info("尝试恢复训练状态")
                
            except Exception as recovery_e:
                main_logger.error(f"恢复训练状态失败: {recovery_e}")
    
    # 训练完成
    elapsed_time = time.time() - start_time
    main_logger.info(f"MAPPO训练完成! 总用时: {elapsed_time:.2f}秒")
    
    # 最终保存
    agent.save_model(args.model_path)
    reward_tracker.export_training_data(total_steps)
    
    # 生成摘要
    summary = reward_tracker.get_summary_statistics()
    main_logger.info("训练摘要:")
    for key, value in summary.items():
        main_logger.info(f"  {key}: {value}")
    
    # 保存摘要到文件
    import json
    summary_path = os.path.join(log_dir, 'training_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    main_logger.info(f"训练数据已保存到: {log_dir}")
    
    # 关闭环境
    if isinstance(envs, SubprocVecEnv):
        envs.close()
        main_logger.info("SubprocVecEnv已关闭")
    else:
        for env in envs:
            env.close()
        main_logger.info("传统环境已关闭")
    
    return agent

def evaluate(agent, envs, n_episodes=10, render=False):
    """评估MAPPO模型 - 支持SubprocVecEnv和传统环境"""
    main_logger.info(f"开始评估: {n_episodes} episodes")
    
    # 检查环境类型
    if isinstance(envs, SubprocVecEnv):
        num_envs = envs.num_envs
        use_vecenv = True
        main_logger.info("使用SubprocVecEnv进行评估")
    else:
        num_envs = len(envs)
        use_vecenv = False
        main_logger.info("使用传统环境进行评估")
    
    episode_rewards = []
    completed_episodes = 0
    
    # 重置环境
    if use_vecenv:
        observations = envs.reset()
        states = np.zeros((num_envs, agent.config.state_dim))
    else:
        observations = []
        states = []
        for env in envs:
            obs, info = env.reset()
            observations.append(obs)
            states.append(info.get('state', np.zeros(agent.config.state_dim)))
        
        observations = np.array(observations)
        states = np.array(states)
    
    env_rewards = np.zeros(num_envs)
    
    while completed_episodes < n_episodes:
        # 预测动作
        actions, _, _ = agent.select_actions(observations, states, deterministic=True)
        
        # 执行动作
        if use_vecenv:
            # 使用SubprocVecEnv的向量化接口
            next_observations, rewards, dones, infos = envs.step(actions)
            
            # 处理dones格式
            if isinstance(dones, tuple) and len(dones) == 2:
                terminated, truncated = dones
                dones = np.logical_or(terminated, truncated)
            
            # 生成next_states（简化处理）
            next_states = np.zeros((num_envs, agent.config.state_dim))
            
        else:
            # 传统环境循环方式
            next_observations = []
            next_states = []
            rewards = []
            dones = []
            infos = []
            
            for i, env in enumerate(envs):
                next_obs, reward, terminated, truncated, info = env.step(actions[i])
                done = bool(terminated or truncated)  # 显式转换为Python bool
                next_observations.append(next_obs)
                next_states.append(info.get('next_state', np.zeros(agent.config.state_dim)))
                rewards.append(reward)
                dones.append(done)
                infos.append(info)
            
            next_observations = np.array(next_observations)
            next_states = np.array(next_states)
            rewards = np.array(rewards)
            dones = np.array(dones)
        
        env_rewards += rewards
        
        # 检查完成的环境
        for i, done in enumerate(dones):
            if done and completed_episodes < n_episodes:
                episode_rewards.append(env_rewards[i])
                completed_episodes += 1
                main_logger.info(f"评估 Episode {completed_episodes}/{n_episodes}, 奖励: {env_rewards[i]:.2f}")
                
                # 重置环境状态（SubprocVecEnv会自动重置）
                if not use_vecenv:
                    # 传统环境需要手动重置
                    obs, info = envs[i].reset()
                    observations[i] = obs
                    states[i] = info.get('state', np.zeros(agent.config.state_dim))
                
                env_rewards[i] = 0
        
        observations = next_observations
        states = next_states

    mean_reward = np.mean(episode_rewards) if episode_rewards else 0
    std_reward = np.std(episode_rewards) if episode_rewards else 0
    min_reward = np.min(episode_rewards) if episode_rewards else 0
    max_reward = np.max(episode_rewards) if episode_rewards else 0

    return mean_reward, std_reward, min_reward, max_reward

def main():
    args = parse_args()
    
    # 创建日志目录
    os.makedirs(args.log_dir, exist_ok=True)
    
    # 为训练会话创建固定的日志文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f"mappo_enhanced_tracking_{timestamp}.log"
    
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
    main_logger = get_logger("MAPPO-Enhanced")
    main_logger.info(f"基于MAPPO的增强训练启动: 文件级别={args.log_level}, 控制台级别={args.console_log_level}")
    main_logger.info(f"日志文件: {os.path.join(args.log_dir, log_file)}")
    
    # 使用配置
    config = Config()
    
    # 获取计算设备
    device = get_device(args.device)
    
    main_logger.info(f"详细日志记录: {args.detailed_logging}")
    main_logger.info(f"数据导出间隔: {args.export_interval} 步")

    if args.mode == 'train':
        agent = train(config, args, device)
        main_logger.info("MAPPO训练完成，增强的数据收集已启用")
    elif args.mode == 'eval':
        # 评估模式
        if not os.path.exists(args.model_path):
            main_logger.error(f"模型文件 {args.model_path} 不存在")
            return
        
        # 创建评估环境
        base_seed = getattr(config, 'seed', int(time.time()))
        
        # 确认评估环境数量
        eval_num_envs = config.eval_rollout_threads
        main_logger.info(f"从配置中读取的评估环境数量: {eval_num_envs}")
        
        eval_env_fns = [make_env(
            scenario=args.scenario,
            config=config,
            rank=i,
            seed=base_seed,
            render_mode="human" if args.render and i == 0 else None
        ) for i in range(eval_num_envs)]
        
        eval_envs = [env_fn() for env_fn in eval_env_fns]
        main_logger.info(f"已创建 {len(eval_envs)} 个评估环境")
        
        # 更新配置维度
        sample_env = eval_envs[0]
        config.n_agents = sample_env.n_uavs
        config.obs_dim = sample_env.obs_dim
        config.state_dim = sample_env.state_dim
        config.action_dim = sample_env.action_dim
        
        # 创建智能体并加载模型
        log_dir = os.path.join(args.log_dir, f"mappo_eval_{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        os.makedirs(log_dir, exist_ok=True)
        
        agent = MAPPOAgent(config, log_dir, device)
        agent.load_model(args.model_path)
        main_logger.info(f"已加载模型: {args.model_path}")
        
        # 进行评估
        mean_reward, std_reward, min_reward, max_reward = evaluate(
            agent, eval_envs, n_episodes=args.eval_episodes, render=args.render
        )
        
        main_logger.info(f"评估结果: 平均奖励 {mean_reward:.2f} ± {std_reward:.2f}, 最大/最小: {max_reward:.2f}/{min_reward:.2f}")
        
        if isinstance(eval_envs, SubprocVecEnv):
            eval_envs.close()
        else:
            for env in eval_envs:
                env.close()
    else:
        main_logger.error(f"未知的运行模式: {args.mode}")

if __name__ == "__main__":
    try:
        main()
    finally:
        try:
            shutdown_logging()
            print("日志系统已关闭")
        except Exception as e:
            print(f"关闭日志系统时出错: {e}")
