"""
Stable Baselines3 集成模块
提供HMASD与SB3更好的集成支持
"""

import numpy as np
import torch
import threading
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import VecMonitor, VecEnvWrapper
from stable_baselines3.common.utils import safe_mean
from hmasd.logging import main_logger
import time
from typing import Dict, Any, Optional, List


class HMASDCallback(BaseCallback):
    """
    HMASD专用的SB3回调类
    用于监控训练过程、管理环境状态清理等
    """
    
    def __init__(self, agent, log_interval: int = 100, verbose: int = 0):
        super().__init__(verbose)
        self.agent = agent
        self.log_interval = log_interval
        self.episode_count = 0
        self.last_cleanup_time = time.time()
        self.cleanup_interval = 3600  # 1小时清理一次
        
        # 初始化SB3 BaseCallback需要的属性
        self.model = agent  # 将agent设置为model以兼容SB3接口
        self.num_timesteps = 0  # 初始化时间步计数器
        # Note: training_env is a property in BaseCallback, don't override it
        
        # 性能监控
        self.step_times = []
        self.memory_usage = []
    
    def init_callback(self, model) -> None:
        """
        自定义初始化方法，兼容SB3和自定义训练循环
        
        参数:
            model: 可以是SB3模型或HMASD agent
        """
        # 设置模型引用
        self.model = model
        self.agent = model  # 保持向后兼容
        
        # 初始化其他必要的属性
        if not hasattr(self, 'num_timesteps'):
            self.num_timesteps = 0
        
        # 如果模型有相关属性，尝试获取
        if hasattr(model, 'num_timesteps'):
            self.num_timesteps = model.num_timesteps
        elif hasattr(model, 'global_step'):
            self.num_timesteps = model.global_step
        
        # Note: training_env is a property in BaseCallback, cannot be set directly
        # The training environment will be set automatically by the BaseCallback
        
        main_logger.info(f"HMASDCallback已初始化，模型类型: {type(model).__name__}")
    
    def update_num_timesteps(self, num_timesteps: int) -> None:
        """
        更新时间步计数器
        
        参数:
            num_timesteps: 当前的时间步数
        """
        self.num_timesteps = num_timesteps
        
        # 如果模型有相应属性，也更新模型的时间步
        if hasattr(self.model, 'num_timesteps'):
            self.model.num_timesteps = num_timesteps
        elif hasattr(self.model, 'global_step'):
            self.model.global_step = num_timesteps
        
    def _on_training_start(self) -> None:
        """训练开始时的初始化"""
        main_logger.info("HMASD训练开始，初始化回调监控")
        
        # 记录初始状态
        if hasattr(self.agent, 'env_state_manager'):
            stats = self.agent.env_state_manager.get_stats()
            main_logger.info(f"初始环境状态管理器统计: {stats}")
        
        return True
    
    def _on_rollout_start(self) -> None:
        """在rollout开始时调用"""
        current_time = time.time()
        
        # 定期清理环境状态
        if current_time - self.last_cleanup_time > self.cleanup_interval:
            if hasattr(self.agent, 'env_state_manager'):
                self.agent.env_state_manager.cleanup_inactive()
                stats = self.agent.env_state_manager.get_stats()
                main_logger.info(f"定期清理后的环境状态统计: {stats}")
            
            # 清理指标收集器中的旧数据
            if hasattr(self.agent, 'metrics_collector'):
                # 只保留最近的数据
                for key in ['policy_loss', 'value_loss', 'entropy']:
                    recent_data = self.agent.metrics_collector.get_metrics(key)
                    if len(recent_data) > 1000:  # 只保留最近1000个数据点
                        self.agent.metrics_collector.clear_metrics(key)
                        # 重新添加最近的500个数据点
                        for item in recent_data[-500:]:
                            self.agent.metrics_collector.add_metric(key, item['value'], item['timestamp'])
            
            self.last_cleanup_time = current_time
        
        return True
    
    def _on_step(self) -> bool:
        """每步调用"""
        step_start_time = time.time()
        
        # 监控数值稳定性
        if hasattr(self.agent, 'training_info'):
            # 检查最近的损失值是否异常
            recent_losses = self.agent.training_info.get('high_level_loss', [])
            if recent_losses and len(recent_losses) > 0:
                recent_loss = recent_losses[-1]
                if not np.isfinite(recent_loss) or abs(recent_loss) > 1000:
                    main_logger.warning(f"检测到异常损失值: {recent_loss}")
        
        # 记录步骤时间
        step_time = time.time() - step_start_time
        self.step_times.append(step_time)
        
        # 定期报告性能统计 - 使用安全的时间步检查
        current_timesteps = getattr(self, 'num_timesteps', 0)
        if current_timesteps > 0 and current_timesteps % self.log_interval == 0:
            if len(self.step_times) > 0:
                avg_step_time = np.mean(self.step_times[-self.log_interval:])
                main_logger.debug(f"平均步骤时间: {avg_step_time:.4f}s")
            
            # 报告环境状态管理器统计
            if hasattr(self.agent, 'env_state_manager'):
                stats = self.agent.env_state_manager.get_stats()
                main_logger.debug(f"环境状态管理器统计: {stats}")
        
        return True
    
    def _on_rollout_end(self) -> None:
        """在rollout结束时调用"""
        # 强制进行一次数值检查
        self._check_numerical_stability()
        return True
    
    def _check_numerical_stability(self):
        """检查数值稳定性"""
        if not hasattr(self.agent, 'skill_coordinator'):
            return
        
        # 检查网络参数
        for name, param in self.agent.skill_coordinator.named_parameters():
            if torch.isnan(param).any():
                main_logger.error(f"检测到NaN参数: {name}")
            if torch.isinf(param).any():
                main_logger.error(f"检测到Inf参数: {name}")
            
            # 检查梯度
            if param.grad is not None:
                if torch.isnan(param.grad).any():
                    main_logger.error(f"检测到NaN梯度: {name}")
                if torch.isinf(param.grad).any():
                    main_logger.error(f"检测到Inf梯度: {name}")


class HMASDVecEnvWrapper(VecEnvWrapper):
    """
    HMASD专用的向量化环境包装器
    提供更好的环境状态管理和监控
    """
    
    def __init__(self, venv, agent=None):
        super().__init__(venv)
        self.agent = agent
        self.episode_rewards = np.zeros(self.num_envs)
        self.episode_lengths = np.zeros(self.num_envs)
        self.episode_count = 0
        
    def reset(self):
        """重置环境并清理相关状态"""
        obs = self.venv.reset()
        
        # 清理智能体的环境状态
        if self.agent is not None:
            for env_id in range(self.num_envs):
                if hasattr(self.agent, 'reset_env_state'):
                    self.agent.reset_env_state(env_id)
        
        self.episode_rewards.fill(0.0)
        self.episode_lengths.fill(0.0)
        
        return obs
    
    def step_wait(self):
        """执行环境步骤并收集统计信息"""
        obs, rewards, dones, infos = self.venv.step_wait()
        
        # 更新统计信息
        self.episode_rewards += rewards
        self.episode_lengths += 1
        
        # 处理完成的episode
        for i, done in enumerate(dones):
            if done:
                episode_info = {
                    'episode_reward': self.episode_rewards[i],
                    'episode_length': self.episode_lengths[i],
                    'episode_id': self.episode_count
                }
                
                # 添加到info中
                if 'episode' not in infos[i]:
                    infos[i]['episode'] = episode_info
                
                # 重置该环境的统计
                self.episode_rewards[i] = 0.0
                self.episode_lengths[i] = 0.0
                self.episode_count += 1
                
                # 不在 wrapper 内重置 agent 状态。
                # 训练/评估循环需要先用 terminal transition 写入 buffer，
                # 然后再调用 agent.reset_env_state(i)，否则会提前清掉高层 pending 样本。
        
        return obs, rewards, dones, infos


class AdvancedNumericalStabilizer:
    """
    高级数值稳定性工具类
    提供更全面的数值检查和修复功能
    """
    
    def __init__(self, config=None):
        self.config = config
        self.nan_count = 0
        self.inf_count = 0
        self.large_value_count = 0
        self.repair_history = []
        
    def comprehensive_check(self, tensor_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        对多个张量进行全面的数值检查和修复
        
        参数:
            tensor_dict: 包含张量名称和张量的字典
            
        返回:
            修复后的张量字典
        """
        repaired_tensors = {}
        repair_log = []
        
        for name, tensor in tensor_dict.items():
            if not isinstance(tensor, torch.Tensor):
                repaired_tensors[name] = tensor
                continue
            
            # 检查NaN
            nan_mask = torch.isnan(tensor)
            if nan_mask.any():
                self.nan_count += nan_mask.sum().item()
                tensor = torch.where(nan_mask, torch.zeros_like(tensor), tensor)
                repair_log.append(f"修复{name}中的{nan_mask.sum().item()}个NaN值")
            
            # 检查Inf
            inf_mask = torch.isinf(tensor)
            if inf_mask.any():
                self.inf_count += inf_mask.sum().item()
                # 用大但有限的值替换Inf
                finite_max = torch.finfo(tensor.dtype).max / 10
                tensor = torch.where(inf_mask & (tensor > 0), 
                                   torch.full_like(tensor, finite_max), tensor)
                tensor = torch.where(inf_mask & (tensor < 0), 
                                   torch.full_like(tensor, -finite_max), tensor)
                repair_log.append(f"修复{name}中的{inf_mask.sum().item()}个Inf值")
            
            # 检查过大的值
            large_threshold = 1e6
            large_mask = tensor.abs() > large_threshold
            if large_mask.any():
                self.large_value_count += large_mask.sum().item()
                tensor = torch.clamp(tensor, -large_threshold, large_threshold)
                repair_log.append(f"裁剪{name}中的{large_mask.sum().item()}个过大值")
            
            repaired_tensors[name] = tensor
        
        if repair_log:
            self.repair_history.extend(repair_log)
            main_logger.warning(f"数值修复: {'; '.join(repair_log)}")
        
        return repaired_tensors
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数值稳定性统计信息"""
        return {
            'nan_repairs': self.nan_count,
            'inf_repairs': self.inf_count,
            'large_value_clips': self.large_value_count,
            'total_repairs': self.nan_count + self.inf_count + self.large_value_count,
            'recent_repairs': self.repair_history[-10:] if self.repair_history else []
        }
    
    def reset_statistics(self):
        """重置统计信息"""
        self.nan_count = 0
        self.inf_count = 0
        self.large_value_count = 0
        self.repair_history = []
    
    def check_and_fix_tensor(self, tensor, name="tensor"):
        """
        检查并修复单个张量中的异常值
        
        参数:
            tensor: 要检查的张量
            name: 张量名称（用于日志）
            
        返回:
            修复后的张量
        """
        if not isinstance(tensor, torch.Tensor):
            return tensor
        
        repair_log = []
        
        # 检查NaN
        nan_mask = torch.isnan(tensor)
        if nan_mask.any():
            nan_count = nan_mask.sum().item()
            self.nan_count += nan_count
            tensor = torch.where(nan_mask, torch.zeros_like(tensor), tensor)
            repair_log.append(f"NaN={nan_count}")
            print(f"数值异常检测到在 {name}: NaN=True, Inf=False")
        
        # 检查Inf
        inf_mask = torch.isinf(tensor)
        if inf_mask.any():
            inf_count = inf_mask.sum().item()
            self.inf_count += inf_count
            # 用大但有限的值替换Inf
            finite_max = 10.0  # 使用固定的合理值
            tensor = torch.where(inf_mask & (tensor > 0), 
                               torch.full_like(tensor, finite_max), tensor)
            tensor = torch.where(inf_mask & (tensor < 0), 
                               torch.full_like(tensor, -finite_max), tensor)
            repair_log.append(f"Inf={inf_count}")
            if not nan_mask.any():  # 只有在没有NaN时才打印
                print(f"数值异常检测到在 {name}: NaN=False, Inf=True")
            else:
                print(f"数值异常检测到在 {name}: NaN=True, Inf=True")
        
        # 检查过大的值
        large_threshold = 1e6
        large_mask = tensor.abs() > large_threshold
        if large_mask.any():
            large_count = large_mask.sum().item()
            self.large_value_count += large_count
            tensor = torch.clamp(tensor, -large_threshold, large_threshold)
            repair_log.append(f"Large={large_count}")
        
        if repair_log:
            self.repair_history.extend(repair_log)
        
        return tensor
    
    @staticmethod
    def safe_log(x, eps=1e-8):
        """安全的对数运算"""
        return torch.log(torch.clamp(x, min=eps))
    
    @staticmethod
    def safe_div(numerator, denominator, eps=1e-8):
        """安全的除法运算"""
        return numerator / (denominator + eps)


class PerformanceMonitor:
    """
    性能监控器
    监控训练过程中的性能指标
    """
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.metrics = {
            'step_times': [],
            'memory_usage': [],
            'gpu_usage': [],
            'batch_sizes': [],
            'loss_computation_times': []
        }
        self.timings = {}
        self.counters = {}
        self.lock = threading.Lock()
    
    def time_context(self, name):
        """上下文管理器，用于测量代码块的执行时间"""
        return self._TimeContext(self, name)
    
    class _TimeContext:
        def __init__(self, monitor, name):
            self.monitor = monitor
            self.name = name
            self.start_time = None
        
        def __enter__(self):
            self.start_time = time.time()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            elapsed = time.time() - self.start_time
            with self.monitor.lock:
                if self.name not in self.monitor.timings:
                    self.monitor.timings[self.name] = []
                self.monitor.timings[self.name].append(elapsed)
    
    def increment_counter(self, name, value=1):
        """增加计数器"""
        with self.lock:
            if name not in self.counters:
                self.counters[name] = 0
            self.counters[name] += value
    
    def get_stats(self):
        """获取性能统计信息"""
        with self.lock:
            stats = {}
            for name, times in self.timings.items():
                stats[name] = {
                    'count': len(times),
                    'total_time': sum(times),
                    'avg_time': sum(times) / len(times) if times else 0,
                    'min_time': min(times) if times else 0,
                    'max_time': max(times) if times else 0
                }
            
            for name, count in self.counters.items():
                if name not in stats:
                    stats[name] = {}
                stats[name]['count'] = count
            
            return stats
        
    def record_step_time(self, step_time: float):
        """记录步骤时间"""
        self.metrics['step_times'].append(step_time)
        if len(self.metrics['step_times']) > self.window_size:
            self.metrics['step_times'].pop(0)
    
    def record_memory_usage(self):
        """记录内存使用情况"""
        if torch.cuda.is_available():
            memory_used = torch.cuda.memory_allocated() / 1024**3  # GB
            self.metrics['memory_usage'].append(memory_used)
            if len(self.metrics['memory_usage']) > self.window_size:
                self.metrics['memory_usage'].pop(0)
    
    def get_performance_summary(self) -> Dict[str, float]:
        """获取性能摘要"""
        summary = {}
        
        if self.metrics['step_times']:
            summary['avg_step_time'] = np.mean(self.metrics['step_times'])
            summary['max_step_time'] = np.max(self.metrics['step_times'])
            summary['steps_per_second'] = 1.0 / summary['avg_step_time']
        
        if self.metrics['memory_usage']:
            summary['avg_memory_gb'] = np.mean(self.metrics['memory_usage'])
            summary['max_memory_gb'] = np.max(self.metrics['memory_usage'])
        
        return summary
    
    def log_performance(self):
        """记录性能统计到日志"""
        summary = self.get_performance_summary()
        if summary:
            main_logger.info(f"性能统计: {summary}")


def create_hmasd_training_setup(agent, vec_env, log_dir: str):
    """
    创建完整的HMASD训练设置
    包括回调、环境包装器等
    
    参数:
        agent: HMASD智能体
        vec_env: 向量化环境
        log_dir: 日志目录
        
    返回:
        包装后的环境和回调列表
    """
    # 创建环境包装器
    wrapped_env = HMASDVecEnvWrapper(vec_env, agent=agent)
    
    # 如果需要，添加VecMonitor
    if hasattr(vec_env, 'num_envs'):
        wrapped_env = VecMonitor(wrapped_env, log_dir)
    
    # 创建回调
    callbacks = [
        HMASDCallback(agent, log_interval=100, verbose=1)
    ]
    
    # 创建性能监控器
    performance_monitor = PerformanceMonitor()
    
    # 创建高级数值稳定器
    numerical_stabilizer = AdvancedNumericalStabilizer()
    
    return wrapped_env, callbacks, performance_monitor, numerical_stabilizer


class ThreadSafeMetricsCollector:
    """
    SB3增强版线程安全指标收集器
    提供更高级的指标管理和分析功能
    """
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.metrics = {}
        self.lock = threading.Lock()
        self.creation_time = time.time()
        
    def add_metric(self, key: str, value: float, timestamp: Optional[float] = None):
        """线程安全地添加指标"""
        if timestamp is None:
            timestamp = time.time()
            
        with self.lock:
            if key not in self.metrics:
                from collections import deque
                self.metrics[key] = deque(maxlen=self.max_size)
            
            self.metrics[key].append({
                'value': value,
                'timestamp': timestamp
            })
    
    def get_metrics(self, key: Optional[str] = None) -> Dict[str, List]:
        """线程安全地获取指标"""
        with self.lock:
            if key is None:
                return {k: list(v) for k, v in self.metrics.items()}
            else:
                return list(self.metrics.get(key, []))
    
    def get_recent_mean(self, key: str, n: int = 100) -> Optional[float]:
        """获取最近n个值的平均值"""
        with self.lock:
            if key not in self.metrics:
                return None
            
            recent_values = list(self.metrics[key])[-n:]
            if not recent_values:
                return None
            
            return np.mean([item['value'] for item in recent_values])
    
    def get_recent_std(self, key: str, n: int = 100) -> Optional[float]:
        """获取最近n个值的标准差"""
        with self.lock:
            if key not in self.metrics:
                return None
            
            recent_values = list(self.metrics[key])[-n:]
            if len(recent_values) < 2:
                return None
            
            return np.std([item['value'] for item in recent_values])
    
    def get_trend(self, key: str, window: int = 50) -> Optional[str]:
        """分析指标趋势"""
        with self.lock:
            if key not in self.metrics or len(self.metrics[key]) < window:
                return None
            
            recent_values = [item['value'] for item in list(self.metrics[key])[-window:]]
            
            # 简单的趋势分析：比较前半部分和后半部分的均值
            mid = len(recent_values) // 2
            first_half_mean = np.mean(recent_values[:mid])
            second_half_mean = np.mean(recent_values[mid:])
            
            diff_ratio = (second_half_mean - first_half_mean) / (abs(first_half_mean) + 1e-8)
            
            if diff_ratio > 0.1:
                return "上升"
            elif diff_ratio < -0.1:
                return "下降"
            else:
                return "稳定"
    
    def clear_metrics(self, key: Optional[str] = None):
        """清理指标"""
        with self.lock:
            if key is None:
                self.metrics.clear()
            else:
                self.metrics.pop(key, None)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        with self.lock:
            summary = {
                'total_metrics': len(self.metrics),
                'uptime_hours': (time.time() - self.creation_time) / 3600,
                'metrics_info': {}
            }
            
            for key, values in self.metrics.items():
                if values:
                    values_list = [item['value'] for item in values]
                    summary['metrics_info'][key] = {
                        'count': len(values),
                        'mean': np.mean(values_list),
                        'std': np.std(values_list),
                        'min': np.min(values_list),
                        'max': np.max(values_list),
                        'trend': self.get_trend(key)
                    }
            
            return summary
