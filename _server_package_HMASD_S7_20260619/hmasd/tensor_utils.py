"""
安全的Tensor变换工具和运行时监控
用于修复多环境并行训练中的数据管理问题
"""

import torch
import numpy as np
from logger import main_logger
from typing import Tuple, Optional, Union, List
import threading
import time
from collections import defaultdict, deque


class TensorValidator:
    """Tensor验证器，确保数据完整性"""
    
    @staticmethod
    def validate_shape(tensor: Union[torch.Tensor, np.ndarray], 
                      expected_shape: Tuple[int, ...], 
                      name: str = "tensor") -> bool:
        """验证tensor形状"""
        if isinstance(tensor, torch.Tensor):
            actual_shape = tensor.shape
        else:
            actual_shape = tensor.shape
            
        if actual_shape != expected_shape:
            main_logger.error(f"{name}形状验证失败: 期望{expected_shape}, 实际{actual_shape}")
            return False
        return True
    
    @staticmethod
    def validate_dtype(tensor: Union[torch.Tensor, np.ndarray], 
                      expected_dtype: Union[torch.dtype, np.dtype], 
                      name: str = "tensor") -> bool:
        """验证tensor数据类型"""
        if isinstance(tensor, torch.Tensor):
            actual_dtype = tensor.dtype
            # 对于torch tensor，直接比较dtype
            if actual_dtype != expected_dtype:
                main_logger.warning(f"{name}数据类型不匹配: 期望{expected_dtype}, 实际{actual_dtype}")
                return False
        else:
            actual_dtype = tensor.dtype
            # 对于numpy array，需要处理dtype的比较
            if isinstance(expected_dtype, torch.dtype):
                # 如果期望的是torch dtype，需要转换比较
                torch_to_numpy_dtype = {
                    torch.float32: np.float32,
                    torch.float64: np.float64,
                    torch.int32: np.int32,
                    torch.int64: np.int64,
                    torch.bool: np.bool_,
                }
                expected_np_dtype = torch_to_numpy_dtype.get(expected_dtype, None)
                if expected_np_dtype is None or actual_dtype != expected_np_dtype:
                    main_logger.warning(f"{name}数据类型不匹配: 期望{expected_dtype}, 实际{actual_dtype}")
                    return False
            else:
                # 都是numpy dtype，直接比较
                if actual_dtype != expected_dtype:
                    main_logger.warning(f"{name}数据类型不匹配: 期望{expected_dtype}, 实际{actual_dtype}")
                    return False
        return True
    
    @staticmethod
    def validate_range(tensor: Union[torch.Tensor, np.ndarray], 
                      min_val: float = -1e6, 
                      max_val: float = 1e6, 
                      name: str = "tensor") -> bool:
        """验证tensor数值范围"""
        if isinstance(tensor, torch.Tensor):
            tensor_np = tensor.detach().cpu().numpy()
        else:
            tensor_np = tensor
            
        if np.any(tensor_np < min_val) or np.any(tensor_np > max_val):
            main_logger.warning(f"{name}数值超出范围[{min_val}, {max_val}]: "
                              f"最小值={np.min(tensor_np)}, 最大值={np.max(tensor_np)}")
            return False
        return True
    
    @staticmethod
    def check_for_anomalies(tensor: Union[torch.Tensor, np.ndarray], 
                           name: str = "tensor") -> Tuple[bool, bool]:
        """检查NaN和Inf"""
        if isinstance(tensor, torch.Tensor):
            has_nan = torch.isnan(tensor).any().item()
            has_inf = torch.isinf(tensor).any().item()
        else:
            has_nan = np.isnan(tensor).any()
            has_inf = np.isinf(tensor).any()
            
        if has_nan or has_inf:
            main_logger.error(f"{name}包含异常值: NaN={has_nan}, Inf={has_inf}")
            
        return has_nan, has_inf


class SafeTensorTransformer:
    """安全的Tensor变换器"""
    
    @staticmethod
    def safe_flatten_sequences(arr: np.ndarray, 
                              expected_input_shape: Tuple[int, ...],
                              name: str = "sequences") -> np.ndarray:
        """
        安全的序列展平: (T, E, A, D) -> (T, E*A, D)
        保持时间步连续性和智能体-环境对应关系
        """
        # 验证输入
        if not TensorValidator.validate_shape(arr, expected_input_shape, f"{name}_input"):
            raise ValueError(f"输入形状验证失败: {arr.shape} vs {expected_input_shape}")
        
        T, E, A = arr.shape[:3]
        remaining_dims = arr.shape[3:]
        
        try:
            # 安全的维度变换
            # 方法: (T, E, A, D) -> (E, A, T, D) -> (E*A, T, D) -> (T, E*A, D)
            result = arr.transpose(1, 2, 0, *range(3, len(arr.shape)))  # (E, A, T, D...)
            result = result.reshape(E * A, T, *remaining_dims)  # (E*A, T, D...)
            result = result.transpose(1, 0, *range(2, len(result.shape)))  # (T, E*A, D...)
            
            # 验证输出
            expected_output_shape = (T, E * A) + remaining_dims
            if not TensorValidator.validate_shape(result, expected_output_shape, f"{name}_output"):
                raise ValueError(f"输出形状验证失败: {result.shape} vs {expected_output_shape}")
            
            main_logger.debug(f"安全序列展平完成: {arr.shape} -> {result.shape}")
            return result
            
        except Exception as e:
            main_logger.error(f"序列展平失败: {e}")
            raise
    
    @staticmethod
    def safe_expand_no_agent_dim(arr: np.ndarray, 
                                n_agents: int,
                                expected_input_shape: Tuple[int, ...],
                                name: str = "no_agent_sequences") -> np.ndarray:
        """
        安全的无智能体维度扩展: (T, E, D) -> (T, E*A, D)
        """
        # 验证输入
        if not TensorValidator.validate_shape(arr, expected_input_shape, f"{name}_input"):
            raise ValueError(f"输入形状验证失败: {arr.shape} vs {expected_input_shape}")
        
        T, E = arr.shape[:2]
        remaining_dims = arr.shape[2:]
        
        try:
            # 安全的维度变换
            result = np.expand_dims(arr, axis=2)  # (T, E, 1, D...)
            result = np.repeat(result, n_agents, axis=2)  # (T, E, A, D...)
            result = result.reshape(T, E * n_agents, *remaining_dims)  # (T, E*A, D...)
            
            # 验证输出
            expected_output_shape = (T, E * n_agents) + remaining_dims
            if not TensorValidator.validate_shape(result, expected_output_shape, f"{name}_output"):
                raise ValueError(f"输出形状验证失败: {result.shape} vs {expected_output_shape}")
            
            main_logger.debug(f"安全维度扩展完成: {arr.shape} -> {result.shape}")
            return result
            
        except Exception as e:
            main_logger.error(f"维度扩展失败: {e}")
            raise
    
    @staticmethod
    def ensure_tensor_consistency(tensor: Union[torch.Tensor, np.ndarray], 
                                 target_device: torch.device, 
                                 target_dtype: torch.dtype,
                                 name: str = "tensor") -> torch.Tensor:
        """确保tensor的设备和数据类型一致性"""
        try:
            if isinstance(tensor, np.ndarray):
                # 使用torch.tensor()而不是torch.from_numpy()来避免内存共享问题
                tensor = torch.tensor(tensor, dtype=target_dtype, device=target_device)
            else:
                # 如果已经是tensor，先检查异常值再转换
                has_nan, has_inf = TensorValidator.check_for_anomalies(tensor, name)
                if has_nan or has_inf:
                    main_logger.warning(f"修复{name}中的异常值")
                    tensor = torch.nan_to_num(tensor, nan=0.0, posinf=1e6, neginf=-1e6)
                
                # 转换设备和数据类型
                tensor = tensor.to(device=target_device, dtype=target_dtype)
            
            main_logger.debug(f"Tensor一致性确保完成: {name}")
            return tensor
            
        except Exception as e:
            main_logger.error(f"Tensor一致性确保失败: {e}")
            raise


class RuntimeMonitor:
    """运行时数据完整性监控器"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.lock = threading.Lock()
        
        # 监控统计
        self.stats = defaultdict(lambda: {
            'count': 0,
            'errors': 0,
            'warnings': 0,
            'last_error': None,
            'error_history': deque(maxlen=max_history)
        })
        
        # 性能统计
        self.performance_stats = defaultdict(lambda: {
            'total_time': 0.0,
            'call_count': 0,
            'avg_time': 0.0,
            'max_time': 0.0,
            'recent_times': deque(maxlen=100)
        })
    
    def monitor_operation(self, operation_name: str):
        """装饰器：监控操作的执行"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    return result
                    
                except Exception as e:
                    # 记录错误
                    with self.lock:
                        self.stats[operation_name]['errors'] += 1
                        self.stats[operation_name]['last_error'] = str(e)
                        self.stats[operation_name]['error_history'].append({
                            'timestamp': time.time(),
                            'error': str(e)
                        })
                    
                    main_logger.error(f"操作{operation_name}失败: {e}")
                    raise
                    
                finally:
                    # 记录总操作数（无论成功还是失败）
                    with self.lock:
                        self.stats[operation_name]['count'] += 1
                    
                    # 记录性能
                    elapsed_time = time.time() - start_time
                    with self.lock:
                        perf_stats = self.performance_stats[operation_name]
                        perf_stats['total_time'] += elapsed_time
                        perf_stats['call_count'] += 1
                        perf_stats['avg_time'] = perf_stats['total_time'] / perf_stats['call_count']
                        perf_stats['max_time'] = max(perf_stats['max_time'], elapsed_time)
                        perf_stats['recent_times'].append(elapsed_time)
            
            return wrapper
        return decorator
    
    def record_warning(self, operation_name: str, message: str):
        """记录警告"""
        with self.lock:
            self.stats[operation_name]['warnings'] += 1
            main_logger.warning(f"{operation_name}: {message}")
    
    def get_stats(self) -> dict:
        """获取监控统计信息"""
        with self.lock:
            return {
                'operations': dict(self.stats),
                'performance': dict(self.performance_stats)
            }
    
    def get_health_report(self) -> dict:
        """获取健康报告"""
        with self.lock:
            total_operations = sum(stats['count'] for stats in self.stats.values())
            total_errors = sum(stats['errors'] for stats in self.stats.values())
            total_warnings = sum(stats['warnings'] for stats in self.stats.values())
            
            error_rate = total_errors / total_operations if total_operations > 0 else 0
            warning_rate = total_warnings / total_operations if total_operations > 0 else 0
            
            # 找出最慢的操作
            slowest_ops = []
            for op_name, perf_stats in self.performance_stats.items():
                if perf_stats['call_count'] > 0:
                    slowest_ops.append((op_name, perf_stats['avg_time']))
            slowest_ops.sort(key=lambda x: x[1], reverse=True)
            
            return {
                'total_operations': total_operations,
                'total_errors': total_errors,
                'total_warnings': total_warnings,
                'error_rate': error_rate,
                'warning_rate': warning_rate,
                'health_status': 'healthy' if error_rate < 0.01 else 'degraded' if error_rate < 0.05 else 'unhealthy',
                'slowest_operations': slowest_ops[:5]
            }
    
    def reset_stats(self):
        """重置统计信息"""
        with self.lock:
            self.stats.clear()
            self.performance_stats.clear()
            main_logger.info("运行时监控统计已重置")


# 全局监控器实例
runtime_monitor = RuntimeMonitor()


class DataIntegrityChecker:
    """数据完整性检查器"""
    
    @staticmethod
    @runtime_monitor.monitor_operation("rollout_buffer_validation")
    def validate_rollout_buffer_data(buffer_data: dict, 
                                   expected_num_steps: int,
                                   expected_num_envs: int,
                                   expected_n_agents: int) -> bool:
        """验证RolloutBuffer数据的完整性"""
        try:
            # 检查必需的键
            required_keys = ['obs', 'actions', 'rewards', 'values', 'log_probs', 
                           'dones', 'states', 'team_skills', 'agent_skills', 'masks']
            
            for key in required_keys:
                if key not in buffer_data:
                    main_logger.error(f"RolloutBuffer缺少必需的键: {key}")
                    return False
            
            # 检查形状一致性
            expected_shapes = {
                'obs': (expected_num_steps, expected_num_envs, expected_n_agents, -1),
                'actions': (expected_num_steps, expected_num_envs, expected_n_agents, -1),
                'rewards': (expected_num_steps, expected_num_envs, expected_n_agents),
                'values': (expected_num_steps, expected_num_envs, expected_n_agents),
                'log_probs': (expected_num_steps, expected_num_envs, expected_n_agents),
                'dones': (expected_num_steps, expected_num_envs, expected_n_agents),
                'states': (expected_num_steps, expected_num_envs, -1),
                'team_skills': (expected_num_steps, expected_num_envs),
                'agent_skills': (expected_num_steps, expected_num_envs, expected_n_agents),
                'masks': (expected_num_steps, expected_num_envs)
            }
            
            for key, expected_shape in expected_shapes.items():
                actual_shape = buffer_data[key].shape
                
                # 检查维度数量
                if len(actual_shape) != len(expected_shape):
                    main_logger.error(f"{key}维度数量不匹配: 期望{len(expected_shape)}, 实际{len(actual_shape)}")
                    return False
                
                # 检查每个维度（-1表示任意大小）
                for i, (expected_dim, actual_dim) in enumerate(zip(expected_shape, actual_shape)):
                    if expected_dim != -1 and expected_dim != actual_dim:
                        main_logger.error(f"{key}第{i}维不匹配: 期望{expected_dim}, 实际{actual_dim}")
                        return False
            
            # 检查数值异常
            for key in ['obs', 'actions', 'rewards', 'values', 'log_probs']:
                has_nan, has_inf = TensorValidator.check_for_anomalies(buffer_data[key], key)
                if has_nan or has_inf:
                    runtime_monitor.record_warning("rollout_buffer_validation", 
                                                  f"{key}包含异常值")
                    return False
            
            main_logger.debug("RolloutBuffer数据完整性验证通过")
            return True
            
        except Exception as e:
            main_logger.error(f"RolloutBuffer数据完整性验证失败: {e}")
            return False
    
    @staticmethod
    @runtime_monitor.monitor_operation("time_step_consistency_check")
    def check_time_step_consistency(env_buffers: List[List[dict]], 
                                   expected_max_steps: int) -> bool:
        """检查时间步索引的一致性"""
        try:
            for env_id, buffer in enumerate(env_buffers):
                if not buffer:
                    continue
                
                # 检查时间步是否连续
                time_steps = [exp.get('t', -1) for exp in buffer]
                
                # 检查是否有无效时间步
                if any(t < 0 or t >= expected_max_steps for t in time_steps):
                    main_logger.error(f"环境{env_id}存在无效时间步: {time_steps}")
                    return False
                
                # 检查是否严格递增
                for i in range(1, len(time_steps)):
                    if time_steps[i] <= time_steps[i-1]:
                        main_logger.error(f"环境{env_id}时间步不是严格递增: {time_steps}")
                        return False
                
                # 检查是否有跳跃
                expected_steps = list(range(len(time_steps)))
                if time_steps != expected_steps:
                    main_logger.warning(f"环境{env_id}时间步存在跳跃: 期望{expected_steps}, 实际{time_steps}")
            
            main_logger.debug("时间步一致性检查通过")
            return True
            
        except Exception as e:
            main_logger.error(f"时间步一致性检查失败: {e}")
            return False


def get_runtime_health_report() -> dict:
    """获取运行时健康报告"""
    return runtime_monitor.get_health_report()


def reset_runtime_monitor():
    """重置运行时监控器"""
    runtime_monitor.reset_stats()


# 导出主要接口
__all__ = [
    'TensorValidator',
    'SafeTensorTransformer', 
    'RuntimeMonitor',
    'DataIntegrityChecker',
    'runtime_monitor',
    'get_runtime_health_report',
    'reset_runtime_monitor'
]
