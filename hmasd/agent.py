import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from copy import deepcopy
from torch.optim import Adam
from torch.distributions import Categorical
import time
import os
import threading
from collections import deque
from contextlib import nullcontext
try:
    from torch.utils.tensorboard import SummaryWriter
except ModuleNotFoundError:
    SummaryWriter = None
from queue import Queue

# 确保在多进程环境中使用安全的matplotlib后端
import matplotlib
if matplotlib.get_backend() != 'Agg':
    matplotlib.use('Agg')

# 导入SB3的RunningMeanStd；测试/轻量环境没有SB3时使用兼容fallback。
try:
    from stable_baselines3.common.running_mean_std import RunningMeanStd
except ModuleNotFoundError:
    class RunningMeanStd:
        def __init__(self, shape=()):
            self.mean = np.zeros(shape, dtype=np.float64)
            self.var = np.ones(shape, dtype=np.float64)
            self.count = 1e-4

        def update(self, arr):
            arr = np.asarray(arr, dtype=np.float64)
            if arr.ndim == 0:
                arr = arr.reshape(1)
            batch_mean = np.mean(arr, axis=0)
            batch_var = np.var(arr, axis=0)
            batch_count = arr.shape[0] if arr.ndim > 0 else 1
            delta = batch_mean - self.mean
            total_count = self.count + batch_count
            new_mean = self.mean + delta * batch_count / total_count
            m_a = self.var * self.count
            m_b = batch_var * batch_count
            m_2 = m_a + m_b + np.square(delta) * self.count * batch_count / total_count
            self.mean = new_mean
            self.var = m_2 / total_count
            self.count = total_count

from hmasd.logging import main_logger
from hmasd.networks import SkillCoordinator, SkillDiscoverer, TeamDiscriminator, IndividualDiscriminator
from hmasd.ha_ctse import (
    CompactIndividualDiscriminator,
    CompactTeamDiscriminator,
    HorizonSkillEditor,
    OPTCompactExtractor,
)
from hmasd.utils import (
    RolloutBuffer,
    compute_gae,
    compute_ppo_loss,
    one_hot,
    DiscriminatorBuffer,
    SkillProcessSegmentBuffer,
)
from hmasd.process_exploration import SkillProcessOutcomeExtractor
from hmasd.process_exploration import (
    SkillOutcomePredictor,
    SkillProcessContrastiveHead,
    SkillProcessEncoder,
    duration_only_baseline_accuracy,
    process_positive_skill_labels,
)
import random


def _split_legacy_discriminator_adam_state_dict(
    legacy_state_dict,
    team_parameters,
    individual_parameters,
):
    """Strictly split the old one-group Adam state by registered parameter order."""

    if not isinstance(legacy_state_dict, dict) or set(legacy_state_dict) != {
        'state', 'param_groups'
    }:
        raise ValueError('legacy discriminator optimizer state has an invalid schema')
    groups = legacy_state_dict['param_groups']
    states = legacy_state_dict['state']
    if not isinstance(groups, list) or len(groups) != 1 or not isinstance(states, dict):
        raise ValueError('legacy discriminator optimizer must contain exactly one Adam group')
    group = groups[0]
    if not isinstance(group, dict) or 'params' not in group:
        raise ValueError('legacy discriminator optimizer parameter group is invalid')
    parameter_ids = list(group['params'])
    team_parameters = tuple(team_parameters)
    individual_parameters = tuple(individual_parameters)
    expected_count = len(team_parameters) + len(individual_parameters)
    if len(parameter_ids) != expected_count or len(set(parameter_ids)) != expected_count:
        raise ValueError('legacy discriminator optimizer parameter inventory mismatch')
    if not set(states).issubset(set(parameter_ids)):
        raise ValueError('legacy discriminator optimizer contains foreign state rows')

    parameters = team_parameters + individual_parameters
    allowed_state_fields = {'step', 'exp_avg', 'exp_avg_sq', 'max_exp_avg_sq'}
    for parameter_id, parameter in zip(parameter_ids, parameters):
        row = states.get(parameter_id)
        if row is None:
            continue
        if not isinstance(row, dict) or not set(row).issubset(allowed_state_fields):
            raise ValueError('legacy discriminator Adam state row is invalid')
        if not {'step', 'exp_avg', 'exp_avg_sq'}.issubset(row):
            raise ValueError('legacy discriminator Adam state row is incomplete')
        for field in ('exp_avg', 'exp_avg_sq', 'max_exp_avg_sq'):
            if field in row and (
                not torch.is_tensor(row[field])
                or tuple(row[field].shape) != tuple(parameter.shape)
            ):
                raise ValueError(
                    f'legacy discriminator Adam {field} shape does not match parameter'
                )
        step = row['step']
        if torch.is_tensor(step):
            if step.numel() != 1:
                raise ValueError('legacy discriminator Adam step must be scalar')
        elif not isinstance(step, (int, float)):
            raise ValueError('legacy discriminator Adam step has an invalid type')

    team_count = len(team_parameters)

    def split_group(selected_ids, start, stop):
        selected = deepcopy(group)
        selected['params'] = list(selected_ids)
        if 'param_names' in selected:
            names = list(selected['param_names'])
            if len(names) != expected_count:
                raise ValueError('legacy discriminator optimizer param_names mismatch')
            selected['param_names'] = names[start:stop]
        return {
            'state': {
                parameter_id: deepcopy(states[parameter_id])
                for parameter_id in selected_ids
                if parameter_id in states
            },
            'param_groups': [selected],
        }

    return (
        split_group(parameter_ids[:team_count], 0, team_count),
        split_group(parameter_ids[team_count:], team_count, expected_count),
    )


def _rollout_sampler_seed_from_config(config, *, stream: int) -> int:
    """Derive one named sampler stream without consuming process-global RNG."""

    explicit = getattr(config, 'rollout_sampler_seed', None)
    if explicit is not None:
        if isinstance(explicit, bool) or not isinstance(explicit, (int, np.integer)):
            raise ValueError('rollout_sampler_seed must be an integer')
        if int(explicit) < 0:
            raise ValueError('rollout_sampler_seed must be non-negative')
        return int(explicit)
    run_seed = getattr(config, 'runtime_seed', None)
    if run_seed is None:
        run_seed = getattr(config, 'seed', None)
    if run_seed is None:
        raise ValueError(
            'HMASDAgent requires config.runtime_seed or config.seed for rollout sampling'
        )
    if isinstance(run_seed, bool) or not isinstance(run_seed, (int, np.integer)):
        raise ValueError('config.seed must be an integer for rollout sampling')
    if int(run_seed) < 0:
        raise ValueError('config.seed must be non-negative for rollout sampling')
    if isinstance(stream, bool) or not isinstance(stream, int) or stream < 0:
        raise ValueError('rollout sampler stream must be a non-negative integer')
    return int(
        np.random.SeedSequence(
            [int(run_seed), 0x484D4153, int(stream)]
        ).generate_state(1, dtype=np.uint64)[0]
    )

# 导入SB3集成功能
try:
    from hmasd.sb3_integration import (
        AdvancedNumericalStabilizer,
        PerformanceMonitor,
        ThreadSafeMetricsCollector as SB3ThreadSafeMetricsCollector
    )
    SB3_INTEGRATION_AVAILABLE = True
    main_logger.info("SB3集成功能已导入")
except ImportError as e:
    main_logger.warning(f"SB3集成功能导入失败: {e}，将使用内置实现")
    SB3_INTEGRATION_AVAILABLE = False


class NativeToyFixedPrimitiveExecutor(nn.Module):
    def __init__(self, n_skills, action_dim, action_space_type):
        super().__init__()
        if int(n_skills) != 4 or int(action_dim) != 2 or action_space_type != 'continuous':
            raise ValueError('native toy fixed primitives require four skills and 2D continuous actions')
        self.register_buffer(
            'action_table',
            torch.tensor(
                [[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0], [0.0, -1.0]],
                dtype=torch.float32,
            ),
        )

    def forward(self, skills):
        if skills.ndim != 2 or skills.shape[-1] != 2:
            raise ValueError(f'native toy skills must have shape [num_envs, 2], got {tuple(skills.shape)}')
        skills = skills.to(dtype=torch.long)
        if torch.any((skills < 0) | (skills >= 4)):
            raise ValueError('native toy skill index is outside [0, 3]')
        actions = self.action_table[skills]
        zeros = torch.zeros(skills.shape, dtype=torch.float32, device=skills.device)
        return actions, zeros, zeros


class EnvironmentStateManager:
    """环境状态管理器，防止内存泄漏和提供线程安全访问"""
    def __init__(self, max_envs=64):
        self.max_envs = max_envs
        self.lock = threading.RLock()  # 使用可重入锁
        self.states = {}
        self.access_times = {}
        self.cleanup_threshold = 3600  # 1小时未使用则清理
        
    def get_state(self, env_id, default=None):
        """线程安全地获取环境状态"""
        with self.lock:
            self.access_times[env_id] = time.time()
            return self.states.get(env_id, default)
    
    def set_state(self, env_id, state):
        """线程安全地设置环境状态"""
        with self.lock:
            # 如果超过最大环境数，清理最旧的
            if len(self.states) >= self.max_envs and env_id not in self.states:
                self._cleanup_oldest()
            
            self.states[env_id] = state
            self.access_times[env_id] = time.time()
    
    def remove_state(self, env_id):
        """线程安全地移除环境状态"""
        with self.lock:
            self.states.pop(env_id, None)
            self.access_times.pop(env_id, None)
    
    def _cleanup_oldest(self):
        """清理最旧的环境状态（内部方法，需要在锁内调用）"""
        if not self.access_times:
            return
        oldest_env = min(self.access_times, key=self.access_times.get)
        self.states.pop(oldest_env, None)
        self.access_times.pop(oldest_env, None)
        main_logger.debug(f"清理最旧的环境状态: env_id={oldest_env}")
    
    def cleanup_inactive(self, timeout=None):
        """清理超时未使用的环境状态"""
        if timeout is None:
            timeout = self.cleanup_threshold
            
        with self.lock:
            current_time = time.time()
            to_remove = [env_id for env_id, last_access in self.access_times.items()
                        if current_time - last_access > timeout]
            
            for env_id in to_remove:
                self.states.pop(env_id, None)
                self.access_times.pop(env_id, None)
            
            if to_remove:
                main_logger.info(f"清理了 {len(to_remove)} 个超时环境状态: {to_remove}")
    
    def get_stats(self):
        """获取状态管理器统计信息"""
        with self.lock:
            return {
                'active_envs': len(self.states),
                'max_envs': self.max_envs,
                'oldest_access': min(self.access_times.values()) if self.access_times else None,
                'newest_access': max(self.access_times.values()) if self.access_times else None
            }


class NumericalStabilizer:
    """数值稳定性工具类"""
    
    @staticmethod
    def safe_log(x, eps=1e-8):
        """安全的对数运算"""
        return torch.log(torch.clamp(x, min=eps))
    
    @staticmethod
    def safe_div(numerator, denominator, eps=1e-8):
        """安全的除法运算"""
        return numerator / (denominator + eps)
    
    @staticmethod
    def check_and_fix_tensor(tensor, name="tensor", nan_replacement=0.0, inf_replacement=10.0):
        """检查并修复张量中的异常值"""
        if not isinstance(tensor, torch.Tensor):
            return tensor
            
        has_nan = torch.isnan(tensor).any().item()
        has_inf = torch.isinf(tensor).any().item()
        
        if has_nan or has_inf:
            main_logger.warning(f"数值异常检测到在 {name}: NaN={has_nan}, Inf={has_inf}")
            tensor = torch.nan_to_num(tensor, nan=nan_replacement, 
                                    posinf=inf_replacement, neginf=-inf_replacement)
            main_logger.info(f"已修复 {name} 中的数值异常")
        
        return tensor
    
    @staticmethod
    def safe_normalize(tensor, dim=-1, eps=1e-8):
        """安全的归一化操作"""
        norm = torch.norm(tensor, dim=dim, keepdim=True)
        return tensor / (norm + eps)


class ThreadSafeMetricsCollector:
    """线程安全的指标收集器"""
    def __init__(self, max_size=10000):
        self.lock = threading.Lock()
        self.metrics = {}
        self.max_size = max_size
    
    def add_metric(self, key, value, timestamp=None):
        """线程安全地添加指标"""
        if timestamp is None:
            timestamp = time.time()
            
        with self.lock:
            if key not in self.metrics:
                self.metrics[key] = deque(maxlen=self.max_size)
            self.metrics[key].append({'value': value, 'timestamp': timestamp})
    
    def get_metrics(self, key=None):
        """线程安全地获取指标"""
        with self.lock:
            if key is None:
                return {k: list(v) for k, v in self.metrics.items()}
            else:
                return list(self.metrics.get(key, []))
    
    def get_recent_mean(self, key, n=100):
        """获取最近n个值的平均值"""
        with self.lock:
            if key not in self.metrics:
                return None
            recent_values = list(self.metrics[key])[-n:]
            if not recent_values:
                return None
            return np.mean([item['value'] for item in recent_values])
    
    def clear_metrics(self, key=None):
        """清理指标"""
        with self.lock:
            if key is None:
                self.metrics.clear()
            else:
                self.metrics.pop(key, None)


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
        self.uses_learned_value_function = True
        self.collects_high_level_samples = not getattr(config, 'disable_high_level_training', False)
        self.r39_native_hmasd_toy = bool(getattr(config, 'r39_native_hmasd_toy', False))
        self.r39_native_toy_fixed_primitives = bool(
            getattr(config, 'r39_native_toy_fixed_primitives', False)
        )
        
        # 确保环境维度已设置
        assert config.state_dim is not None, "必须先设置state_dim"
        assert config.obs_dim is not None, "必须先设置obs_dim"
        
        # 新增：为增强状态模式传递组件维度
        if getattr(config, 'enhanced_state', False):
            assert hasattr(config, 'state_component_dims'), "增强状态模式需要 state_component_dims"
        
        # 移除TensorBoard相关初始化，由训练脚本统一管理
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        # self.writer = SummaryWriter(log_dir)  # 移除
        # main_logger.debug(f"HMASDAgent.__init__: SummaryWriter created: {self.writer}")
        self.global_step = 0
        self.num_timesteps = 0  # Add SB3 compatibility attribute
        self.enable_runtime_profiling = False
        self.update_amp_enabled = bool(getattr(config, 'update_amp', False)) and self.device.type == 'cuda'
        try:
            self.update_grad_scaler = torch.amp.GradScaler('cuda', enabled=self.update_amp_enabled)
        except TypeError:
            self.update_grad_scaler = torch.cuda.amp.GradScaler(enabled=self.update_amp_enabled)
        self._step_profile = {
            'skill_assign': 0.0,
            'action_select': 0.0,
            'info_build': 0.0,
            'input_prepare': 0.0,
            'hidden_extract': 0.0,
            'tensor_upload': 0.0,
            'gpu_forward': 0.0,
            'policy_forward': 0.0,
            'critic_forward': 0.0,
            'output_sync': 0.0,
            'action_sync': 0.0,
            'value_logprob_sync': 0.0,
            'hidden_sync': 0.0,
            'hidden_state_update': 0.0,
            'hidden_store': 0.0,
            'calls': 0,
        }
        self._transition_profile = {
            'intrinsic_reward_compute': 0.0,
            'intrinsic_normalize': 0.0,
            'intrinsic_team_forward': 0.0,
            'intrinsic_ind_forward': 0.0,
            'intrinsic_postprocess': 0.0,
            'rollout_buffer_write': 0.0,
            'discriminator_buffer_write': 0.0,
            'high_level_bookkeeping': 0.0,
            'store_calls': 0,
        }
        self._update_profile = {
            'coord_advantage': 0.0,
            'coord_sampler': 0.0,
            'coord_forward_backward': 0.0,
            'coord_encode_policy': 0.0,
            'coord_value': 0.0,
            'coord_backward': 0.0,
            'coord_optimizer': 0.0,
            'coord_stats': 0.0,
            'discoverer_advantage': 0.0,
            'discoverer_sampler': 0.0,
            'discoverer_eval': 0.0,
            'discoverer_actor_eval': 0.0,
            'discoverer_critic_eval': 0.0,
            'discoverer_loss': 0.0,
            'discoverer_backward': 0.0,
            'discoverer_optimizer': 0.0,
            'discoverer_stats': 0.0,
            'disc_pack': 0.0,
            'disc_train': 0.0,
            'disc_accuracy': 0.0,
        }
        
        self.use_ha_ctse = bool(getattr(config, 'use_horizon_window', False))
        # D2 policy-based interruption (ADR 01 revision 3). `off` is the default and
        # must stay byte-identical to the pre-D2 route: every `d2` branch below is
        # guarded by `self.d2_enabled`, and nothing is allocated or drawn in `off`.
        self.policy_interruption_mode = str(getattr(config, 'policy_interruption_mode', 'off'))
        self.d2_enabled = (self.policy_interruption_mode == 'd2')
        if self.d2_enabled:
            self.d2_cost_c = float(getattr(config, 'interruption_cost_c', float('inf')))
            self.d2_cost_c_Z = float(getattr(config, 'interruption_cost_c_Z', float('inf')))
            self.d2_k_max = int(getattr(config, 'skill_cap_k_max', getattr(config, 'k', 10)))
            _team_cap = getattr(config, 'team_cap_k_Z', None)
            self.d2_k_Z = self.d2_k_max if _team_cap is None else int(_team_cap)
            self.d2_age_feature = str(getattr(config, 'age_feature', 'off'))
        else:
            self.d2_cost_c = float('inf')
            self.d2_cost_c_Z = float('inf')
            self.d2_k_max = int(getattr(config, 'k', 10))
            self.d2_k_Z = self.d2_k_max
            self.d2_age_feature = 'off'
        self.use_low_level_compact = bool(getattr(config, 'use_compact_in_low_level_actor', False))
        self.use_process_exploration = bool(
            self.use_ha_ctse and getattr(config, 'use_process_exploration', False)
        )
        self.use_discrete_skill_lifetimes = bool(
            self.use_process_exploration and getattr(config, 'use_discrete_skill_lifetimes', False)
        )
        if self.r39_native_toy_fixed_primitives:
            if (
                not self.r39_native_hmasd_toy
                or self.use_ha_ctse
                or getattr(config, 'scenario', '') != 'two_timescale_role_free_actions'
                or int(getattr(config, 'n_agents', 0)) != 2
                or int(getattr(config, 'n_Z', 0)) != 4
                or int(getattr(config, 'n_z', 0)) != 4
                or int(getattr(config, 'action_dim', 0)) != 2
                or getattr(config, 'action_space_type', 'continuous') != 'continuous'
                or not bool(getattr(config, 'disable_discriminator_training', False))
                or not bool(getattr(config, 'disable_discriminator_rewards', False))
                or float(getattr(config, 'lambda_D', 0.0)) != 0.0
                or float(getattr(config, 'lambda_d', 0.0)) != 0.0
                or bool(getattr(config, 'use_process_exploration', False))
                or bool(getattr(config, 'use_process_reward_for_discoverer', False))
                or bool(getattr(config, 'use_reward_annealing', False))
            ):
                raise ValueError('native toy fixed primitives require the isolated fixed-N external-reward profile')
            if getattr(config, 'r39_native_toy_fixed_skill_action_schema', '') != 'axis4_xy_v1':
                raise ValueError('unsupported native toy fixed primitive schema')
        self.use_discriminator_path = not (
            bool(getattr(config, 'disable_discriminator_training', False))
            and bool(getattr(config, 'disable_discriminator_rewards', False))
        )
        self.use_compact_team_discriminator = bool(
            self.use_discriminator_path
            and self.use_ha_ctse
            and getattr(config, 'use_team_code_discriminator', False)
            and getattr(config, 'discriminator_condition_on_compact', False)
        )
        self.use_compact_individual_discriminator = bool(
            self.use_discriminator_path
            and self.use_ha_ctse
            and getattr(config, 'use_individual_skill_discriminator', True)
            and (
                getattr(config, 'discriminator_condition_on_compact', False)
                or getattr(config, 'discriminator_condition_on_team_code', False)
            )
        )
        if self.use_ha_ctse and int(getattr(config, 'num_team_codes', config.n_Z)) != int(config.n_Z):
            main_logger.warning(
                "当前集成版HA-CTSE要求 num_team_codes == n_Z；"
                f"已将 num_team_codes={getattr(config, 'num_team_codes', None)} 调整为 n_Z={config.n_Z}"
            )
            config.num_team_codes = int(config.n_Z)

        # 创建网络
        self.skill_coordinator = SkillCoordinator(config).to(self.device)
        self.ha_ctse_editor = HorizonSkillEditor(config).to(self.device) if self.use_ha_ctse else None
        self.low_level_compact_extractor = (
            OPTCompactExtractor(config).to(self.device)
            if self.use_low_level_compact
            else None
        )
        process_action_dim = 1 if getattr(config, 'action_space_type', 'continuous') == 'discrete' else int(config.action_dim)
        self.process_encoder = (
            SkillProcessEncoder(
                obs_dim=config.obs_dim,
                action_dim=process_action_dim,
                hidden_dim=getattr(config, 'process_encoder_hidden_dim', 128),
                embedding_dim=getattr(config, 'process_encoder_embedding_dim', 64),
            ).to(self.device)
            if self.use_process_exploration
            else None
        )
        self.process_outcome_predictor = (
            SkillOutcomePredictor(
                segment_dim=getattr(config, 'process_encoder_embedding_dim', 64),
                outcome_dim=len(SkillProcessOutcomeExtractor.FIELD_NAMES),
            ).to(self.device)
            if self.use_process_exploration
            else None
        )
        self.process_contrastive_head = (
            SkillProcessContrastiveHead(
                segment_dim=getattr(config, 'process_encoder_embedding_dim', 64),
                num_skills=config.n_z,
                embedding_dim=getattr(config, 'process_contrastive_dim', getattr(config, 'process_encoder_embedding_dim', 64)),
                temperature=getattr(config, 'process_contrastive_temperature', 0.1),
            ).to(self.device)
            if self.use_process_exploration
            else None
        )
        
        self.skill_discoverer = SkillDiscoverer(config, logger=main_logger, device=self.device).to(self.device) # Pass logger
        self.native_toy_fixed_primitive_executor = (
            NativeToyFixedPrimitiveExecutor(
                config.n_z,
                config.action_dim,
                getattr(config, 'action_space_type', 'continuous'),
            ).to(self.device)
            if self.r39_native_toy_fixed_primitives
            else None
        )
        if self.r39_native_toy_fixed_primitives:
            for parameter in self.skill_discoverer.parameters():
                parameter.requires_grad_(False)
            if self.low_level_compact_extractor is not None:
                for parameter in self.low_level_compact_extractor.parameters():
                    parameter.requires_grad_(False)
        if self.use_discriminator_path:
            self.team_discriminator = (
                CompactTeamDiscriminator(config).to(self.device)
                if self.use_compact_team_discriminator
                else TeamDiscriminator(config).to(self.device)
            )
            self.individual_discriminator = (
                CompactIndividualDiscriminator(config).to(self.device)
                if self.use_compact_individual_discriminator
                else IndividualDiscriminator(config).to(self.device)
            )
        else:
            self.team_discriminator = None
            self.individual_discriminator = None
        
        # 创建优化器
        high_level_params = (
            self.ha_ctse_editor.parameters()
            if self.use_ha_ctse and self.ha_ctse_editor is not None
            else self.skill_coordinator.parameters()
        )
        self.coordinator_optimizer = Adam(
            high_level_params,
            lr=config.lr_coordinator,
            weight_decay=config.weight_decay
        )
        # 【关键修复】为SkillDiscoverer解耦Actor和Critic的优化器
        discoverer_actor_params = self.skill_discoverer.actor_update_parameters()
        if self.low_level_compact_extractor is not None:
            discoverer_actor_params = discoverer_actor_params + list(self.low_level_compact_extractor.parameters())
        discoverer_critic_params = self.skill_discoverer.critic_update_parameters()

        self.discoverer_actor_optimizer = Adam(
            discoverer_actor_params,
            lr=config.lr_discoverer_actor,  # 使用独立的actor学习率
            weight_decay=config.weight_decay
        )
        self.discoverer_critic_optimizer = Adam(
            discoverer_critic_params,
            lr=config.lr_discoverer_critic, # 使用独立的critic学习率
            weight_decay=config.weight_decay
        )
        self.team_discriminator_optimizer = (
            Adam(
                self.team_discriminator.parameters(),
                lr=config.lr_discriminator,
                weight_decay=config.weight_decay
            )
            if self.use_discriminator_path
            else None
        )
        self.individual_discriminator_optimizer = (
            Adam(
                self.individual_discriminator.parameters(),
                lr=config.lr_discriminator,
                weight_decay=config.weight_decay
            )
            if self.use_discriminator_path
            else None
        )
        process_params = []
        for module in (self.process_encoder, self.process_outcome_predictor, self.process_contrastive_head):
            if module is not None:
                process_params.extend(module.parameters())
        self.process_optimizer = (
            Adam(
                process_params,
                lr=getattr(config, 'lr_process_encoder', 1e-4),
                weight_decay=config.weight_decay,
            )
            if process_params
            else None
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
                self.discoverer_actor_scheduler = LinearLR(
                    self.discoverer_actor_optimizer,
                    start_factor=1.0,
                    end_factor=config.discoverer_lr_decay_factor, 
                    total_iters=config.lr_decay_steps
                )
                self.discoverer_critic_scheduler = LinearLR(
                    self.discoverer_critic_optimizer,
                    start_factor=1.0,
                    end_factor=config.discoverer_lr_decay_factor, 
                    total_iters=config.lr_decay_steps
                )
                self.discoverer_scheduler = None # 兼容性设置
                self.team_discriminator_scheduler = (
                    LinearLR(
                        self.team_discriminator_optimizer,
                        start_factor=1.0,
                        end_factor=config.discriminator_lr_decay_factor,
                        total_iters=config.lr_decay_steps
                    )
                    if self.team_discriminator_optimizer is not None
                    else None
                )
                self.individual_discriminator_scheduler = (
                    LinearLR(
                        self.individual_discriminator_optimizer,
                        start_factor=1.0,
                        end_factor=config.discriminator_lr_decay_factor,
                        total_iters=config.lr_decay_steps
                    )
                    if self.individual_discriminator_optimizer is not None
                    else None
                )
            elif config.lr_decay_schedule == 'cosine':
                self.coordinator_scheduler = CosineAnnealingLR(
                    self.coordinator_optimizer, T_max=config.lr_decay_steps
                )
                self.discoverer_actor_scheduler = CosineAnnealingLR(
                    self.discoverer_actor_optimizer, T_max=config.lr_decay_steps
                )
                self.discoverer_critic_scheduler = CosineAnnealingLR(
                    self.discoverer_critic_optimizer, T_max=config.lr_decay_steps
                )
                self.discoverer_scheduler = None # 兼容性设置
                self.team_discriminator_scheduler = (
                    CosineAnnealingLR(
                        self.team_discriminator_optimizer, T_max=config.lr_decay_steps
                    )
                    if self.team_discriminator_optimizer is not None
                    else None
                )
                self.individual_discriminator_scheduler = (
                    CosineAnnealingLR(
                        self.individual_discriminator_optimizer,
                        T_max=config.lr_decay_steps
                    )
                    if self.individual_discriminator_optimizer is not None
                    else None
                )
            
            main_logger.info(f"已启用学习率衰减: {config.lr_decay_schedule}, 衰减步数: {config.lr_decay_steps}")
        else:
            self.coordinator_scheduler = None
            self.discoverer_scheduler = None  
            self.team_discriminator_scheduler = None
            self.individual_discriminator_scheduler = None
            main_logger.info("未启用学习率衰减")
        
        # 判别器只使用当前rollout数据，update后在clear_buffers中清空。
        discriminator_buffer_size = getattr(config, 'discriminator_buffer_size', 100000)
        self.discriminator_buffer = DiscriminatorBuffer(capacity=discriminator_buffer_size)
        
        # 统一的Rollout缓冲区，同时存储高层和低层策略数据
        rollout_length = getattr(config, 'rollout_length', 2048)  # 默认rollout长度
        num_envs = getattr(config, 'num_envs', 1)  # 并行环境数量
        gru_hidden_size = getattr(config, 'gru_hidden_size', 128)  # GRU隐状态大小
        action_space_type = getattr(config, 'action_space_type', 'continuous')  # 动作空间类型
        rollout_sampler_seed = _rollout_sampler_seed_from_config(
            config,
            stream=0,
        )
        self.rollout_sampler_seed = rollout_sampler_seed
        
        self.rollout_buffer = RolloutBuffer(
            num_steps=rollout_length,
            num_envs=num_envs,
            n_agents=config.n_agents,
            obs_dim=config.obs_dim,
            action_dim=config.action_dim,
            gru_hidden_size=gru_hidden_size,
            n_Z=config.n_Z,
            n_z=config.n_z,
            state_dim=config.state_dim,
            action_space_type=action_space_type,
            compact_dim=getattr(config, 'opt_compact_dim', 0) if (self.use_ha_ctse or self.use_low_level_compact) else 0,
            sampler_seed=rollout_sampler_seed,
            d2_enabled=self.d2_enabled,
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
        
        # 使用新的环境状态管理器替代原有的字典
        max_envs = max(64, getattr(config, 'num_envs', 1) * 2)  # 预留更多空间
        self.env_state_manager = EnvironmentStateManager(max_envs=max_envs)
        
        # 初始化数值稳定性工具
        if SB3_INTEGRATION_AVAILABLE:
            self.numerical_stabilizer = AdvancedNumericalStabilizer()
            main_logger.info("使用SB3增强的数值稳定性工具")
        else:
            self.numerical_stabilizer = NumericalStabilizer()
            main_logger.info("使用内置的数值稳定性工具")
        
        # 创建线程安全的指标收集器
        if SB3_INTEGRATION_AVAILABLE:
            self.metrics_collector = SB3ThreadSafeMetricsCollector(max_size=10000)
            main_logger.info("使用SB3增强的线程安全指标收集器")
        else:
            self.metrics_collector = ThreadSafeMetricsCollector(max_size=10000)
            main_logger.info("使用内置的线程安全指标收集器")
        
        # 保留兼容性接口（将逐步迁移到新的管理器）
        self.env_team_skills = {}  # 将逐步迁移到env_state_manager
        self.env_agent_skills = {}  # 将逐步迁移到env_state_manager
        self.env_log_probs = {}  # 将逐步迁移到env_state_manager
        self.env_hidden_states = {}  # 将逐步迁移到env_state_manager
        self.env_prev_hidden_states = {} # 用于存储上一步的隐藏状态，解决Off-by-One问题
        self.env_pending_high_level = {}  # 保存技能决策时刻的高层PPO样本，周期结束时只补累计奖励
        self.env_skill_ages = {}
        self.env_skill_duration_remaining = {}
        self.env_skill_duration_target = {}
        # D2 per-env bookkeeping (ADR 01). Allocated in both modes as empty dicts so
        # that `clear_buffers`/`reset_env_state` have a uniform surface, but only
        # written by the `d2` branches.
        self.env_team_ages = {}
        self.env_d2_last_decision = {}
        self._d2_last_step = None
        self.d2_open_agent_segments = {}
        self.d2_open_team_segments = {}
        self.d2_metrics = self._new_d2_metrics() if self.d2_enabled else None
        self.process_outcome_extractor = (
            SkillProcessOutcomeExtractor(
                normalize=getattr(config, 'normalize_process_outcomes', True),
            )
            if self.use_process_exploration
            else None
        )
        self.process_segment_buffer = (
            SkillProcessSegmentBuffer(
                capacity=getattr(config, 'process_segment_buffer_size', 20000),
                max_segment_len=getattr(config, 'process_max_segment_len', 250),
                outcome_extractor=self.process_outcome_extractor,
            )
            if self.use_process_exploration
            else None
        )

        self._hidden_batch_capacity = 0
        self.actor_hidden_np = None
        self.critic_hidden_np = None
        self.prev_actor_hidden_np = None
        self.prev_critic_hidden_np = None
        self._hidden_state_array_valid = None
        
        # 动态初始化环境状态字典 - 将在实际使用时按需初始化
        # 不再预分配固定数量的环境槽位
        self.accumulated_rewards = 0.0  # 用于测试的累积奖励属性
        self.episode_rewards = []  # 记录每个完整episode的奖励
        
        main_logger.info(f"已初始化环境状态管理器，最大环境数: {max_envs}")
        main_logger.info("已初始化线程安全指标收集器")

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
        self.last_discriminator_metrics = {
            'total_loss': 0.0,
            'team_loss': 0.0,
            'individual_loss': 0.0,
            'team_accuracy': 0.0,
            'individual_accuracy': 0.0,
        }
        self.last_process_metrics = {
            'process_encoder_loss': 0.0,
            'process_outcome_loss': 0.0,
            'process_contrastive_loss': 0.0,
            'process_contrastive_accuracy': 0.0,
            'process_duration_only_accuracy': 0.0,
            'process_reward_mean': 0.0,
            'process_reward_abs_mean': 0.0,
            'process_reward_applied_steps': 0.0,
            'process_segments_trained': 0.0,
        }
        self.last_action_entropy = 0.0
        self.high_replay_likelihood_metrics = {
            'latest_team_max_abs_error': 0.0,
            'latest_agent_max_abs_error': 0.0,
            'latest_max_abs_error': 0.0,
            'latest_sample_count': 0,
            'global_team_max_abs_error': 0.0,
            'global_agent_max_abs_error': 0.0,
            'global_max_abs_error': 0.0,
            'global_sample_count': 0,
        }
        self.native_toy_optimizer_updates = {
            'high': 0,
            'low_actor': 0,
            'low_critic': 0,
            'discriminator': 0,
        }
        
        # 用于减少高层缓冲区警告日志的计数器
        self.high_level_buffer_warning_counter = 0
        self.last_high_level_buffer_size = 0
        
        # 高层经验统计
        self.high_level_samples_total = 0        # 总收集高层样本数
        self.high_level_samples_by_env = {}      # 各环境贡献的样本数
        self.high_level_samples_by_reason = {'技能周期结束': 0, '环境终止': 0, '强制收集': 0}  # 收集原因统计
        
        # 高层经验收集增强
        self.env_last_contribution = {}          # 跟踪每个环境上次贡献高层样本的时间步
        self.force_high_level_collection = {}    # 强制采集标志，用于确保所有环境都能贡献样本
        self.env_reward_thresholds = {}          # 环境特定的奖励阈值
        self.strict_hmasd_alignment = bool(getattr(config, 'strict_hmasd_alignment', True))
        if self.use_ha_ctse and self.use_discrete_skill_lifetimes and self.strict_hmasd_alignment:
            main_logger.warning(
                "HA-CTSE process/discrete-lifetime模式与strict_hmasd_alignment不兼容；"
                "已关闭固定k周期高层闭合逻辑，改用duration-aware闭合。"
            )
            self.strict_hmasd_alignment = False
            self.config.strict_hmasd_alignment = False
        if self.strict_hmasd_alignment:
            main_logger.info("已启用严格HMASD论文对齐模式：高层样本仅在技能周期边界闭合")
        if getattr(config, 'rollout_length', 0) % getattr(config, 'k', 1) != 0:
            main_logger.warning(
                f"rollout_length={getattr(config, 'rollout_length', None)} 不能被 k={getattr(config, 'k', None)} 整除，"
                "严格HMASD对齐模式下可能丢弃未闭合的高层技能段"
            )
        
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

        # [新增] 熵系数退火初始化
        self.use_entropy_annealing = getattr(config, 'use_entropy_annealing', False)
        if self.use_entropy_annealing:
            self.lambda_h_initial = getattr(config, 'lambda_h_initial', 0.2)
            self.lambda_h_final = getattr(config, 'lambda_h_final', 0.01)
            self.lambda_l_initial = getattr(config, 'lambda_l_initial', 0.1)
            self.lambda_l_final = getattr(config, 'lambda_l_final', 0.01)
            self.entropy_anneal_steps = getattr(config, 'entropy_anneal_steps', config.total_timesteps)
            self.entropy_anneal_schedule = getattr(config, 'entropy_anneal_schedule', 'linear')
            
            # 立即更新 config 的 lambda 值以反映初始状态
            self.config.lambda_h = self.lambda_h_initial
            self.config.lambda_l = self.lambda_l_initial
            
            main_logger.info(f"已启用熵系数退火机制: "
                           f"高层熵系数 {self.lambda_h_initial}→{self.lambda_h_final}, "
                           f"低层熵系数 {self.lambda_l_initial}→{self.lambda_l_final}, "
                           f"退火步数: {self.entropy_anneal_steps}, 退火计划: {self.entropy_anneal_schedule}")
        else:
            main_logger.info("未启用熵系数退火机制")

        self._init_entropy_target_state()
        
        # 初始化Value Normalization - 使用SB3的RunningMeanStd
        if config.use_valuenorm:
            self.value_norm_coordinator = RunningMeanStd(shape=())
            self.value_norm_discoverer = RunningMeanStd(shape=())
            # 添加更新频率控制
            self.value_norm_update_freq = getattr(config, 'value_norm_update_freq', 10)  # 每10步更新一次
            self.value_norm_update_counter = 0
            main_logger.info(f"已启用Value Normalization (使用SB3 RunningMeanStd), 更新频率: {self.value_norm_update_freq}")
        else:
            self.value_norm_coordinator = None
            self.value_norm_discoverer = None
            self.value_norm_update_freq = 0
            self.value_norm_update_counter = 0
            main_logger.info("未启用Value Normalization")
        
        # 初始化Observation Normalization - 使用SB3的RunningMeanStd
        if getattr(config, 'use_obsnorm', False):
            self.obs_norm = RunningMeanStd(shape=(config.obs_dim,))
            main_logger.info("已启用Observation Normalization (使用SB3 RunningMeanStd)")
        else:
            self.obs_norm = None
            main_logger.info("未启用Observation Normalization")
        
        # 初始化State Normalization - 使用SB3的RunningMeanStd (新增)
        if getattr(config, 'use_statenorm', True):  # 默认启用状态标准化
            self.state_norm = RunningMeanStd(shape=(config.state_dim,))
            main_logger.info("已启用State Normalization (使用SB3 RunningMeanStd) - 用于Critic输入标准化")
        else:
            self.state_norm = None
            main_logger.info("未启用State Normalization")
        
        self.training = True # 训练/评估模式标志

    def apply_reward_weighting(self, env_indices, weight):
        """
        对指定环境的回报应用一个权重。
        用于最差表现优化，放大表现不佳的episode的奖励信号。
        """
        if not env_indices:
            return
        
        main_logger.info(f"正在为环境 {env_indices} 的回报应用权重 {weight}...")
        try:
            # 直接修改rollout buffer中的rewards
            # 注意：这里修改的是原始的内在奖励，GAE计算会基于此进行
            self.rollout_buffer.rewards[:, env_indices] *= weight
            main_logger.info(f"已成功对环境 {env_indices} 的奖励应用权重。")
        except IndexError:
            main_logger.error(f"在应用奖励权重时发生索引错误。请求的环境索引: {env_indices}, "
                            f"缓冲区环境数量: {self.rollout_buffer.num_envs}")
        except Exception as e:
            main_logger.error(f"应用奖励权重时发生未知错误: {e}")
    
    def train(self, mode=True):
        """设置智能体为训练或评估模式"""
        self.training = mode
        self.skill_coordinator.train(mode)
        if self.ha_ctse_editor is not None:
            self.ha_ctse_editor.train(mode)
        for module in (self.process_encoder, self.process_outcome_predictor, self.process_contrastive_head):
            if module is not None:
                module.train(mode)
        self.skill_discoverer.train(mode)
        if self.team_discriminator is not None:
            self.team_discriminator.train(mode)
        if self.individual_discriminator is not None:
            self.individual_discriminator.train(mode)
        main_logger.info(f"智能体模式设置为: {'训练' if mode else '评估'}")

    def eval(self):
        """设置智能体为评估模式"""
        self.train(False)

    def _init_entropy_target_state(self):
        self.use_entropy_targets = bool(getattr(self.config, 'use_entropy_targets', False))
        self.entropy_target_update_rate = float(getattr(self.config, 'entropy_target_update_rate', 0.02))
        self.entropy_coef_min = float(getattr(self.config, 'entropy_coef_min', 1e-4))
        self.entropy_coef_max = float(getattr(self.config, 'entropy_coef_max', 0.2))
        self.ha_team_entropy_coef = float(getattr(self.config, 'lambda_h', 0.0))
        self.ha_term_entropy_coef = float(getattr(self.config, 'term_entropy_coef', 0.0))
        self.ha_skill_entropy_coef = float(getattr(self.config, 'skill_entropy_coef', 0.0))
        self.low_level_entropy_coef = float(getattr(self.config, 'lambda_l', 0.0))

    def _auto_entropy_target(self, action_count, fraction, fallback=0.0):
        action_count = max(int(action_count), 1)
        if action_count <= 1:
            return float(fallback)
        return float(fraction) * float(np.log(action_count))

    def _low_level_entropy_target(self):
        configured = float(getattr(self.config, 'target_low_level_entropy', -1.0))
        if configured >= 0.0:
            return configured
        if getattr(self.config, 'action_space_type', 'continuous') == 'continuous':
            per_dim = float(getattr(self.config, 'low_level_entropy_target_per_dim', 0.30))
            return per_dim * float(max(int(getattr(self.config, 'action_dim', 1)), 1))
        frac = float(getattr(self.config, 'target_skill_entropy_frac', 0.75))
        return self._auto_entropy_target(getattr(self.config, 'action_dim', 1), frac)

    def _adapt_entropy_coef(self, attr_name, observed_entropy, target_entropy):
        if not self.use_entropy_targets:
            return float(getattr(self, attr_name))
        observed = float(observed_entropy)
        target = float(target_entropy)
        current = max(float(getattr(self, attr_name)), self.entropy_coef_min)
        # If observed entropy is below target, increase the coefficient; if it
        # is above target, relax it. This keeps exploration pressure adaptive
        # without adding another optimizer to the PPO update.
        updated = current * float(np.exp(self.entropy_target_update_rate * (target - observed)))
        updated = float(np.clip(updated, self.entropy_coef_min, self.entropy_coef_max))
        setattr(self, attr_name, updated)
        return updated

    def _effective_training_steps(self):
        direct_steps = int(getattr(self, 'num_timesteps', 0) or 0)
        update_steps = int(getattr(self, 'global_step', 0)) * int(getattr(self.config, 'num_envs', 1)) * int(getattr(self.config, 'rollout_length', 1))
        return max(direct_steps, update_steps)

    def _warmup_scale(self, warmup_steps):
        warmup_steps = int(max(0, warmup_steps or 0))
        if warmup_steps <= 0:
            return 1.0
        return float(np.clip(self._effective_training_steps() / float(warmup_steps), 0.0, 1.0))

    def _discriminator_mi_reward(self, log_prob_values, num_classes):
        rewards = log_prob_values
        if bool(getattr(self.config, 'use_prior_corrected_intrinsic', False)):
            rewards = rewards + np.log(max(int(num_classes), 1))
        if bool(getattr(self.config, 'normalize_intrinsic_mi', False)):
            denom = np.log(max(int(num_classes), 2))
            rewards = rewards / max(float(denom), 1e-8)
        clip_value = float(getattr(self.config, 'intrinsic_mi_clip', 10.0))
        return np.clip(rewards, -clip_value, clip_value)

    def set_runtime_profiling(self, enabled: bool):
        self.enable_runtime_profiling = bool(enabled)

    def reset_step_profile(self):
        for key in self._step_profile:
            self._step_profile[key] = 0 if key == 'calls' else 0.0

    def get_step_profile(self, reset=False):
        profile = dict(self._step_profile)
        if reset:
            self.reset_step_profile()
        return profile

    def reset_transition_profile(self):
        for key in self._transition_profile:
            self._transition_profile[key] = 0 if key == 'store_calls' else 0.0
        if hasattr(self, 'rollout_buffer') and hasattr(self.rollout_buffer, 'get_profile'):
            self.rollout_buffer.get_profile(reset=True)

    def get_transition_profile(self, reset=False):
        profile = dict(self._transition_profile)
        if hasattr(self, 'rollout_buffer') and hasattr(self.rollout_buffer, 'get_profile'):
            profile.update(self.rollout_buffer.get_profile(reset=reset))
        if reset:
            self.reset_transition_profile()
        return profile

    def _add_transition_profile(self, key, elapsed):
        if self.enable_runtime_profiling:
            self._transition_profile[key] = self._transition_profile.get(key, 0.0) + float(elapsed)

    def reset_update_profile(self):
        for key in self._update_profile:
            self._update_profile[key] = 0.0

    def get_update_profile(self, reset=False):
        profile = dict(self._update_profile)
        if reset:
            self.reset_update_profile()
        return profile

    def _add_update_profile(self, key, elapsed):
        if self.enable_runtime_profiling:
            self._update_profile[key] = self._update_profile.get(key, 0.0) + float(elapsed)

    def _sync_cuda_for_profile(self):
        if self.enable_runtime_profiling and self.device.type == 'cuda':
            torch.cuda.synchronize(self.device)

    def _ensure_hidden_state_arrays(self, num_envs):
        """Ensure contiguous CPU hidden-state arrays cover the active vector env batch."""
        required = int(max(num_envs, 1))
        if self.actor_hidden_np is not None and self._hidden_batch_capacity >= required:
            return

        old_capacity = self._hidden_batch_capacity
        new_capacity = max(required, old_capacity * 2 if old_capacity else getattr(self.config, 'num_envs', required))
        new_capacity = max(new_capacity, required)
        shape = (new_capacity, self.config.n_agents, self.config.gru_hidden_size)

        actor_hidden = np.zeros(shape, dtype=np.float32)
        critic_hidden = np.zeros(shape, dtype=np.float32)
        prev_actor_hidden = np.zeros(shape, dtype=np.float32)
        prev_critic_hidden = np.zeros(shape, dtype=np.float32)
        valid = np.zeros(new_capacity, dtype=np.bool_)

        if old_capacity > 0:
            actor_hidden[:old_capacity] = self.actor_hidden_np[:old_capacity]
            critic_hidden[:old_capacity] = self.critic_hidden_np[:old_capacity]
            prev_actor_hidden[:old_capacity] = self.prev_actor_hidden_np[:old_capacity]
            prev_critic_hidden[:old_capacity] = self.prev_critic_hidden_np[:old_capacity]
            valid[:old_capacity] = self._hidden_state_array_valid[:old_capacity]

        self.actor_hidden_np = actor_hidden
        self.critic_hidden_np = critic_hidden
        self.prev_actor_hidden_np = prev_actor_hidden
        self.prev_critic_hidden_np = prev_critic_hidden
        self._hidden_state_array_valid = valid
        self._hidden_batch_capacity = new_capacity

    def _hidden_to_numpy(self, hidden_state, n_agents=None):
        if hidden_state is None:
            return None
        n_agents = self.config.n_agents if n_agents is None else int(n_agents)
        if isinstance(hidden_state, torch.Tensor):
            hidden_np = hidden_state.detach().cpu().numpy()
        else:
            hidden_np = np.asarray(hidden_state, dtype=np.float32)

        hidden_np = np.asarray(hidden_np, dtype=np.float32)
        if hidden_np.ndim > 2:
            hidden_np = np.squeeze(hidden_np, axis=0) if hidden_np.shape[0] == 1 else hidden_np.reshape(-1, hidden_np.shape[-1])
        if hidden_np.ndim == 1:
            hidden_np = np.broadcast_to(hidden_np, (n_agents, hidden_np.shape[0]))
        if hidden_np.shape[0] == 1 and n_agents > 1:
            hidden_np = np.repeat(hidden_np, n_agents, axis=0)

        expected_shape = (n_agents, self.config.gru_hidden_size)
        if hidden_np.shape != expected_shape:
            main_logger.debug(f"忽略维度不匹配的hidden_state: expected={expected_shape}, actual={hidden_np.shape}")
            return None
        return np.ascontiguousarray(hidden_np, dtype=np.float32)

    def _sync_legacy_hidden_to_arrays(self, num_envs):
        self._ensure_hidden_state_arrays(num_envs)
        if np.all(self._hidden_state_array_valid[:num_envs]):
            return
        for env_id in range(num_envs):
            if self._hidden_state_array_valid[env_id]:
                continue
            actor_hidden = self._hidden_to_numpy(self.env_hidden_states.get(env_id))
            if actor_hidden is not None:
                self.actor_hidden_np[env_id] = actor_hidden

            critic_key = f"{env_id}_critic"
            critic_hidden = self._hidden_to_numpy(self.env_hidden_states.get(critic_key))
            if critic_hidden is not None:
                self.critic_hidden_np[env_id] = critic_hidden
            self._hidden_state_array_valid[env_id] = True

    def _reset_hidden_state_arrays_for_env(self, env_id):
        if self.actor_hidden_np is None or env_id >= self._hidden_batch_capacity:
            return
        self.actor_hidden_np[env_id].fill(0.0)
        self.critic_hidden_np[env_id].fill(0.0)
        self.prev_actor_hidden_np[env_id].fill(0.0)
        self.prev_critic_hidden_np[env_id].fill(0.0)
        self._hidden_state_array_valid[env_id] = True

    def get_prev_actor_hidden_np(self, env_id, n_agents=None):
        if self.prev_actor_hidden_np is not None and env_id < self._hidden_batch_capacity and self._hidden_state_array_valid[env_id]:
            return self.prev_actor_hidden_np[env_id].copy()
        hidden = self._hidden_to_numpy(self.env_prev_hidden_states.get(env_id), n_agents=n_agents)
        if hidden is not None:
            return hidden.copy()
        n_agents = self.config.n_agents if n_agents is None else int(n_agents)
        return np.zeros((n_agents, self.config.gru_hidden_size), dtype=np.float32)

    def get_prev_critic_hidden_np(self, env_id, n_agents=None):
        if self.prev_critic_hidden_np is not None and env_id < self._hidden_batch_capacity and self._hidden_state_array_valid[env_id]:
            return self.prev_critic_hidden_np[env_id].copy()
        critic_key = f"{env_id}_critic"
        hidden = self._hidden_to_numpy(self.env_prev_hidden_states.get(critic_key), n_agents=n_agents)
        if hidden is not None:
            return hidden.copy()
        n_agents = self.config.n_agents if n_agents is None else int(n_agents)
        return np.zeros((n_agents, self.config.gru_hidden_size), dtype=np.float32)

    def get_current_critic_hidden_np(self, env_id, agent_index=None):
        if self.critic_hidden_np is not None and env_id < self._hidden_batch_capacity and self._hidden_state_array_valid[env_id]:
            hidden = self.critic_hidden_np[env_id]
        else:
            hidden = self._hidden_to_numpy(self.env_hidden_states.get(f"{env_id}_critic"))
            if hidden is None:
                hidden = np.zeros((self.config.n_agents, self.config.gru_hidden_size), dtype=np.float32)
        if agent_index is None:
            return hidden.copy()
        return np.asarray(hidden[int(agent_index)], dtype=np.float32).copy()

    def _update_autocast(self):
        if self.update_amp_enabled:
            return torch.amp.autocast(device_type=self.device.type, enabled=True)
        return nullcontext()

    def _value_norm_tensors(self, running_mean_std):
        if not self.config.use_valuenorm or running_mean_std is None:
            return None
        mean = torch.as_tensor(running_mean_std.mean, device=self.device, dtype=torch.float32)
        var = torch.as_tensor(running_mean_std.var, device=self.device, dtype=torch.float32)
        return mean, var, torch.sqrt(var + 1e-8)

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

    def _normalize_observations(self, observations, update=True):
        """
        归一化观测数据，解决输入尺度问题
        
        参数:
            observations: 观测数据，可以是numpy数组或torch张量
            update: 是否更新运行均值和方差（RunningMeanStd）
            
        返回:
            normalized_observations: 归一化后的观测数据
        """
        if not getattr(self.config, 'use_obsnorm', False) or self.obs_norm is None:
            return observations
        
        # 转换为numpy数组进行处理
        if isinstance(observations, torch.Tensor):
            obs_np = observations.cpu().numpy()
            return_tensor = True
        else:
            obs_np = observations
            return_tensor = False
        
        # 仅在训练模式下且update=True时更新观测统计量
        if self.training and update:
            if obs_np.ndim == 1:
                # 单个观测
                self.obs_norm.update(obs_np)
            elif obs_np.ndim == 2:
                # 多个智能体的观测 [n_agents, obs_dim]
                for i in range(obs_np.shape[0]):
                    self.obs_norm.update(obs_np[i])
            elif obs_np.ndim == 3:
                # 批量观测 [batch_size, n_agents, obs_dim]
                for i in range(obs_np.shape[0]):
                    for j in range(obs_np.shape[1]):
                        self.obs_norm.update(obs_np[i, j])
        
        # 归一化
        current_mean = self.obs_norm.mean
        current_var = self.obs_norm.var
        
        normalized_obs = (obs_np - current_mean) / np.sqrt(current_var + 1e-8)
        
        # 裁剪到合理范围
        normalized_obs = np.clip(normalized_obs, -10.0, 10.0)
        
        # 如果输入是张量，返回张量
        if return_tensor:
            return torch.FloatTensor(normalized_obs).to(self.device)
        else:
            return normalized_obs

    def _normalize_states(self, states, update=True):
        """
        归一化全局状态数据，解决Critic输入尺度问题
        
        参数:
            states: 全局状态数据，可以是numpy数组或torch张量
            update: 是否更新运行均值和方差（RunningMeanStd）
            
        返回:
            normalized_states: 归一化后的状态数据
        """
        if not getattr(self.config, 'use_statenorm', True) or self.state_norm is None:
            return states
        
        # 转换为numpy数组进行处理
        if isinstance(states, torch.Tensor):
            states_np = states.cpu().numpy()
            return_tensor = True
        else:
            states_np = states
            return_tensor = False
        
        # 仅在训练模式下且update=True时更新状态统计量
        if self.training and update:
            if states_np.ndim == 1:
                # 单个状态
                self.state_norm.update(states_np)
            elif states_np.ndim == 2:
                # 批量状态 [batch_size, state_dim]
                for i in range(states_np.shape[0]):
                    self.state_norm.update(states_np[i])
        
        # 归一化
        current_mean = self.state_norm.mean
        current_var = self.state_norm.var
        
        normalized_states = (states_np - current_mean) / np.sqrt(current_var + 1e-8)
        
        # 裁剪到合理范围
        normalized_states = np.clip(normalized_states, -10.0, 10.0)
        
        # 如果输入是张量，返回张量
        if return_tensor:
            return torch.FloatTensor(normalized_states).to(self.device)
        else:
            return normalized_states

    def clear_buffers(self):
        """清空on-policy的经验缓冲区，以及判别器Buffer (On-Policy模式)"""
        main_logger.info("清空统一的on-policy经验缓冲区 (RolloutBuffer)...")
        self.rollout_buffer.reset()
        
        # Discriminator 现在采用 On-Policy 模式，更新后清空缓冲区
        self.discriminator_buffer.clear()
        main_logger.info("已清空判别器Buffer (On-Policy模式)")
        
        # 重置计数器和累积值
        self.current_high_level_reward_sum = 0.0
        self.accumulated_rewards = 0.0
        self.skill_change_timer = 0
        self.high_level_buffer_warning_counter = 0
        self.last_high_level_buffer_size = 0
        
        # 重置环境特定的奖励累积字典和计时器字典
        self.env_reward_sums = {}
        self.env_timers = {}
        self.env_pending_high_level = {}
        self.env_skill_ages = {}
        self.env_skill_duration_remaining = {}
        self.env_skill_duration_target = {}
        if self.d2_enabled:
            # D2 per-rollout state: ages, replay metadata and open segment
            # bookkeeping are all rollout-scoped, exactly like the buffer.
            self.env_team_ages = {}
            self.env_d2_last_decision = {}
            self._d2_reset_open_segments()
            self.d2_metrics = self._new_d2_metrics()
        if self.process_segment_buffer is not None:
            self.process_segment_buffer.reset()
        if self._uses_process_high_level_flow():
            invalid_agent_skills = np.full(self.config.n_agents, -1, dtype=np.int64)
            for env_id in range(getattr(self.config, 'num_envs', 0)):
                self.env_team_skills[env_id] = -1
                self.env_agent_skills[env_id] = invalid_agent_skills.copy()
            self.env_log_probs = {}
            self.env_hidden_states = {}
            self.env_prev_hidden_states = {}
            for attr in (
                'actor_hidden_np',
                'critic_hidden_np',
                'prev_actor_hidden_np',
                'prev_critic_hidden_np',
            ):
                array = getattr(self, attr, None)
                if array is not None:
                    array[...] = 0.0
            if getattr(self, '_hidden_state_array_valid', None) is not None:
                self._hidden_state_array_valid[...] = False
            main_logger.info(
                "HA-CTSE过程模式已在update边界重置高层技能与RNN隐状态，"
                "避免跨策略版本延续旧高层决策"
            )
        
        # 重置奖励组成部分的累积值
        self.cumulative_env_reward = 0.0
        self.cumulative_team_disc_reward = 0.0
        self.cumulative_ind_disc_reward = 0.0
        self.reward_component_counts = 0
        
        # 重置技能使用计数
        self.episode_team_skill_counts = {}
        self.episode_agent_skill_counts = []
        
        # 定期清理环境状态管理器中的超时状态
        if hasattr(self, 'env_state_manager'):
            self.env_state_manager.cleanup_inactive()
            stats = self.env_state_manager.get_stats()
            main_logger.debug(f"环境状态管理器统计: {stats}")
        
        # 清理指标收集器中的旧数据
        if hasattr(self, 'metrics_collector'):
            # 只保留最近的指标
            self.metrics_collector.clear_metrics()
            main_logger.debug("已清理指标收集器中的旧数据")
        
        # 注意：不重置Value Normalization统计量
        # ValueNorm的running_mean和running_std应该在整个训练过程中累积
        # 这符合MAPPO的标准实现，确保价值函数标准化的稳定性
        # 只有在模型初始化或显式要求时才重置ValueNorm统计量
        if self.config.use_valuenorm:
            main_logger.debug("保持Value Normalization统计量不变，继续累积训练数据")
    
    def get_env_state_stats(self):
        """获取环境状态管理器的统计信息"""
        if hasattr(self, 'env_state_manager'):
            return self.env_state_manager.get_stats()
        return {'active_envs': 0, 'max_envs': 0}
    
    def cleanup_inactive_envs(self, timeout=3600):
        """手动清理超时的环境状态"""
        if hasattr(self, 'env_state_manager'):
            self.env_state_manager.cleanup_inactive(timeout)
    
    def add_training_metric(self, key, value):
        """添加训练指标到线程安全收集器"""
        if hasattr(self, 'metrics_collector'):
            self.metrics_collector.add_metric(key, value)
    
    def get_recent_metric_mean(self, key, n=100):
        """获取最近n个指标的平均值"""
        if hasattr(self, 'metrics_collector'):
            return self.metrics_collector.get_recent_mean(key, n)
        return None
    
    def reset_env_state(self, env_id):
        """
        【关键修复】重置特定环境的内部状态。
        
        当Episode结束时调用此函数，确保：
        1. 重置所有隐藏状态（Actor和Critic）
        2. 将技能标记为无效(-1)，强制下一步重新分配
        3. 重置计时器和累积奖励
        
        这是解决"新Episode第一步技能未重新分配"Bug的关键修复。
        """
        # 重置Actor隐藏状态
        if env_id in self.env_hidden_states:
            self.env_hidden_states[env_id] = None
            main_logger.debug(f"已重置环境 {env_id} 的Actor隐藏状态")
            
        if env_id in self.env_prev_hidden_states:
            self.env_prev_hidden_states[env_id] = None

        # 【关键修复】重置Critic隐藏状态
        critic_hidden_key = f"{env_id}_critic"
        if critic_hidden_key in self.env_hidden_states:
            self.env_hidden_states[critic_hidden_key] = None
            main_logger.debug(f"已重置环境 {env_id} 的Critic隐藏状态")
            
        if critic_hidden_key in self.env_prev_hidden_states:
            self.env_prev_hidden_states[critic_hidden_key] = None

        self._reset_hidden_state_arrays_for_env(env_id)
        
        # 【关键修复】将技能标记为无效值(-1)，强制在下一个step中重新分配
        # 这确保了新Episode的第一步会触发技能重新分配
        if env_id in self.env_team_skills:
            self.env_team_skills[env_id] = -1
            main_logger.debug(f"已重置环境 {env_id} 的团队技能为-1（无效，待重新分配）")
        
        if env_id in self.env_agent_skills:
            self.env_agent_skills[env_id] = np.full(self.config.n_agents, -1, dtype=int)
            main_logger.debug(f"已重置环境 {env_id} 的个体技能为-1（无效，待重新分配）")
        
        # 【关键修复】重置技能计时器，确保新Episode从0开始
        if env_id in self.env_timers:
            self.env_timers[env_id] = 0
            main_logger.debug(f"已重置环境 {env_id} 的技能计时器为0")
        self.env_skill_ages[env_id] = np.zeros(self.config.n_agents, dtype=np.int64)
        if self.d2_enabled:
            self.env_team_ages[env_id] = 0
        self.env_skill_duration_remaining[env_id] = np.zeros(self.config.n_agents, dtype=np.int64)
        self.env_skill_duration_target[env_id] = np.zeros(self.config.n_agents, dtype=np.int64)
        if self.process_segment_buffer is not None:
            self.process_segment_buffer.close_env_segments(env_id, reason="env_reset")
        
        # 重置累积奖励
        if env_id in self.env_reward_sums:
            self.env_reward_sums[env_id] = 0.0
            main_logger.debug(f"已重置环境 {env_id} 的累积奖励")
        
        # 重置log_probs
        if env_id in self.env_log_probs:
            self.env_log_probs[env_id] = {}

        if env_id in self.env_pending_high_level:
            self.env_pending_high_level.pop(env_id, None)

    def _uses_process_high_level_flow(self):
        return bool(self.use_process_exploration and self.use_discrete_skill_lifetimes)

    def _should_use_legacy_high_level_contribution_monitor(self):
        return not self._uses_process_high_level_flow()

    def _process_segments_enabled(self):
        return self.use_process_exploration and self.process_segment_buffer is not None

    def _open_or_replace_process_segments(self, env_idx, step, log_probs):
        if not self._process_segments_enabled() or not log_probs:
            return
        executed = np.asarray(
            log_probs.get('executed_edit_mask', np.zeros(self.config.n_agents, dtype=np.float32)),
            dtype=np.float32,
        ) > 0.5
        initial = np.asarray(
            log_probs.get('initial_assignment_mask', np.zeros(self.config.n_agents, dtype=np.float32)),
            dtype=np.float32,
        ) > 0.5
        active_prev = np.asarray(
            log_probs.get('active_skill_prev', np.full(self.config.n_agents, -1, dtype=np.int64)),
            dtype=np.int64,
        )
        active = np.asarray(
            log_probs.get('active_skill', self.env_agent_skills.get(env_idx, np.full(self.config.n_agents, -1))),
            dtype=np.int64,
        )
        duration_target = np.asarray(
            log_probs.get('duration_target', np.ones(self.config.n_agents, dtype=np.int64)),
            dtype=np.int64,
        )
        team_code = int(log_probs.get('team_code', self.env_team_skills.get(env_idx, -1)))
        compact = log_probs.get('compact')
        for agent_idx in range(self.config.n_agents):
            if not executed[agent_idx]:
                continue
            if (not initial[agent_idx]) and active_prev[agent_idx] >= 0:
                self.process_segment_buffer.close_segment(
                    env_idx,
                    agent_idx,
                    reason="skill_edit",
                    end_step=step,
                )
            if active[agent_idx] >= 0:
                self.process_segment_buffer.open_segment(
                    env_idx,
                    agent_idx,
                    skill=int(active[agent_idx]),
                    team_code=team_code,
                    compact=compact,
                    start_step=step,
                    duration_target=int(duration_target[agent_idx]),
                )

    @staticmethod
    def _extract_reward_info(info):
        if not isinstance(info, dict):
            return {}
        reward_info = info.get('reward_info')
        if isinstance(reward_info, dict):
            return reward_info
        infos_dict = info.get('infos_dict')
        if isinstance(infos_dict, dict):
            for agent_info in infos_dict.values():
                if isinstance(agent_info, dict) and isinstance(agent_info.get('reward_info'), dict):
                    return agent_info['reward_info']
        for value in info.values():
            if isinstance(value, dict) and isinstance(value.get('reward_info'), dict):
                return value['reward_info']
        return {}

    def _append_process_segment_transitions(self, env_id, observations, next_observations,
                                            actions, rewards, dones, rollout_step_idx=None,
                                            reward_info=None):
        if not self._process_segments_enabled():
            return
        reward_arr = np.asarray(rewards, dtype=np.float32)
        if reward_arr.ndim == 0:
            reward_arr = np.full(self.config.n_agents, float(reward_arr), dtype=np.float32)
        else:
            reward_arr = reward_arr.reshape(-1)
            if reward_arr.size == 1:
                reward_arr = np.full(self.config.n_agents, float(reward_arr[0]), dtype=np.float32)
        done_arr = np.asarray(dones, dtype=np.bool_).reshape(-1)
        if done_arr.size == 1:
            done_arr = np.full(self.config.n_agents, bool(done_arr[0]), dtype=np.bool_)
        for agent_idx in range(self.config.n_agents):
            reward_val = reward_arr[agent_idx] if agent_idx < reward_arr.size else float(np.mean(reward_arr))
            done_val = done_arr[agent_idx] if agent_idx < done_arr.size else bool(np.any(done_arr))
            self.process_segment_buffer.append_transition(
                env_id,
                agent_idx,
                observations[agent_idx],
                actions[agent_idx],
                reward_val,
                done_val,
                next_obs=next_observations[agent_idx],
                step=rollout_step_idx,
                reward_info=reward_info,
            )
        if np.any(done_arr):
            self.process_segment_buffer.close_env_segments(
                env_id,
                reason="env_done",
                end_step=rollout_step_idx,
            )
    
    
    def select_action(self, observations, agent_skills=None, deterministic=False, env_id=0, state=None):
        """
        【论文一致性修复】选择动作，并为每个环境管理 Actor 和 Critic 的隐藏状态
        
        【重要修复】现在每个智能体都有独立的Critic隐状态，与on-policy-main保持一致
        """
        if agent_skills is None:
            agent_skills = self.env_agent_skills.get(env_id, self.current_agent_skills)
            
        # 【关键修复】确保agent_skills有效，如果无效则分配随机技能
        n_agents = observations.shape[0]
        if agent_skills is None or len(agent_skills) != n_agents or np.any(np.array(agent_skills) < 0):
            main_logger.warning(f"环境{env_id}的agent_skills无效: {agent_skills}，分配随机技能")
            agent_skills = np.random.randint(0, self.config.n_z, size=n_agents)
            # 更新环境状态
            self.env_agent_skills[env_id] = agent_skills
            
        # 根据动作空间类型初始化动作张量
        action_space_type = getattr(self.config, 'action_space_type', 'continuous')
        if action_space_type == 'discrete':
            actions = torch.zeros(n_agents, dtype=torch.long, device=self.device)
        else:
            actions = torch.zeros((n_agents, self.config.action_dim), device=self.device)
        action_logprobs = torch.zeros(n_agents, device=self.device)
        values = torch.zeros(n_agents, device=self.device)
        
        # === 管理 Actor 和 Critic 的隐藏状态 ===
        gru_hidden_size = self.config.gru_hidden_size
        
        # Actor 隐藏状态
        if self.actor_hidden_np is not None and env_id < self._hidden_batch_capacity and self._hidden_state_array_valid[env_id]:
            actor_hidden_state = torch.as_tensor(self.actor_hidden_np[env_id], dtype=torch.float32, device=self.device)
        else:
            actor_hidden_state = self.env_hidden_states.get(env_id)
        if actor_hidden_state is None:
            actor_hidden_state = torch.zeros(n_agents, gru_hidden_size, device=self.device)
        
        # 【关键修复】Critic 隐藏状态 - 每个智能体独立
        critic_hidden_key = f"{env_id}_critic"
        if self.critic_hidden_np is not None and env_id < self._hidden_batch_capacity and self._hidden_state_array_valid[env_id]:
            critic_hidden_state = torch.as_tensor(self.critic_hidden_np[env_id], dtype=torch.float32, device=self.device)
        else:
            critic_hidden_state = self.env_hidden_states.get(critic_hidden_key)
        if critic_hidden_state is None:
            critic_hidden_state = torch.zeros(n_agents, gru_hidden_size, device=self.device)

        # 【关键修复】保存当前步的输入隐藏状态，用于store_transition（解决Off-by-One问题）
        self.env_prev_hidden_states[env_id] = actor_hidden_state
        self.env_prev_hidden_states[critic_hidden_key] = critic_hidden_state
        self._ensure_hidden_state_arrays(env_id + 1)
        self.prev_actor_hidden_np[env_id] = self._hidden_to_numpy(actor_hidden_state, n_agents=n_agents)
        self.prev_critic_hidden_np[env_id] = self._hidden_to_numpy(critic_hidden_state, n_agents=n_agents)
        self._hidden_state_array_valid[env_id] = True

        with torch.no_grad():
            low_level_compact_context = None
            if self.use_low_level_compact and self.low_level_compact_extractor is not None and state is not None:
                state_norm_for_context = self._normalize_states(state, update=False)
                obs_norm_for_context = self._normalize_observations(observations, update=False)
                compact_env = self._compute_low_level_compact_context(
                    torch.as_tensor(state_norm_for_context, dtype=torch.float32, device=self.device).unsqueeze(0),
                    torch.as_tensor(obs_norm_for_context, dtype=torch.float32, device=self.device).unsqueeze(0),
                )
                low_level_compact_context = compact_env.expand(n_agents, -1)
            # 【关键修复】为每个智能体独立计算价值，使用各自的Critic隐状态
            current_team_skill = self.env_team_skills.get(env_id, self.current_team_skill)
            if current_team_skill is not None and state is not None:
                # 【关键修复】应用状态标准化，解决Critic输入尺度问题
                normalized_state = self._normalize_states(state)
                
                # 为每个智能体分别计算价值
                new_critic_hidden_states = []
                for i in range(n_agents):
                    global_state_tensor = torch.FloatTensor(normalized_state).unsqueeze(0).to(self.device)
                    team_skill_tensor = torch.tensor(current_team_skill, device=self.device).unsqueeze(0)
                    
                    # 【关键修复】使用每个智能体独立的Critic隐状态
                    agent_value, new_critic_hidden = self.skill_discoverer.get_value(
                        global_state_tensor, team_skill_tensor, 
                        critic_hidden_state[i:i+1],  # 使用第i个智能体的隐状态
                        compact_context=(
                            low_level_compact_context[i:i+1]
                            if low_level_compact_context is not None
                            else None
                        )
                    )
                    
                    # 【关键修复】在此处反归一化，确保传出的是真实价值
                    if self.config.use_valuenorm and self.value_norm_discoverer is not None:
                        real_value = self._denormalize_values(agent_value, self.value_norm_discoverer)
                        values[i] = real_value.item()
                    else:
                        values[i] = agent_value.item()
                        
                    new_critic_hidden_states.append(new_critic_hidden.squeeze(0))
                
                # 更新所有智能体的Critic隐状态
                critic_hidden_state = torch.stack(new_critic_hidden_states)
                self.env_hidden_states[critic_hidden_key] = critic_hidden_state
                self.critic_hidden_np[env_id] = self._hidden_to_numpy(critic_hidden_state, n_agents=n_agents)
            else:
                values.fill_(0.0)

            # 【关键修复】应用观测归一化，解决输入尺度问题
            observations_normalized = self._normalize_observations(observations)
            
            # 将所有智能体作为单个批次处理
            obs_batch = torch.FloatTensor(observations_normalized).to(self.device)
            skill_batch = torch.tensor(agent_skills, device=self.device)

            # 将环境的 Actor hidden_state 传入网络
            actions_batch, logprobs_batch, _, new_actor_hidden_state = self.skill_discoverer.forward(
                obs_batch,
                skill_batch,
                actor_hidden_state,
                deterministic,
                compact_context=low_level_compact_context,
            )
            
            # 存储更新后的 Actor hidden_state
            self.env_hidden_states[env_id] = new_actor_hidden_state
            self.actor_hidden_np[env_id] = self._hidden_to_numpy(new_actor_hidden_state, n_agents=n_agents)
            self._hidden_state_array_valid[env_id] = True

        return actions_batch.cpu().numpy(), logprobs_batch.cpu().numpy(), values.cpu().numpy()
    
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
        # Keep Coordinator sampling inputs on the same scale used during PPO re-evaluation.
        state_normalized = self._normalize_states(state)
        state_tensor = torch.FloatTensor(state_normalized).unsqueeze(0).to(self.device)
        # 修复：先转换为numpy数组再创建tensor，避免从列表创建tensor的警告
        obs_array = np.array(observations) if not isinstance(observations, np.ndarray) else observations
        
        # 【关键修复】应用观测归一化，解决输入尺度问题
        obs_array_normalized = self._normalize_observations(obs_array)
        
        obs_tensor = torch.FloatTensor(obs_array_normalized).unsqueeze(0).to(self.device)
        
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
            state_val, agent_vals, _ = self.skill_coordinator.get_value(state_tensor, obs_tensor)
            if not agent_vals:
                agent_vals = [
                    torch.zeros_like(state_val)
                    for _ in range(self.config.n_agents)
                ]
            if self.config.use_valuenorm and self.value_norm_coordinator is not None:
                state_val = self._denormalize_values(state_val, self.value_norm_coordinator)
                agent_vals = [self._denormalize_values(v, self.value_norm_coordinator) for v in agent_vals]
            log_probs['state_value'] = float(state_val.squeeze().cpu().numpy())
            log_probs['agent_values'] = [float(v.squeeze().cpu().numpy()) for v in agent_vals]
        
        return team_skill.item(), agent_skills.squeeze(0).cpu().numpy(), log_probs
    
    def _batched_assign_skills(self, states_batch, observations_batch, env_steps_batch, dones_batch, deterministic=False):
        """
        【关键修复】为一批环境分配技能。
        只为需要更新的环境运行神经网络。
        
        【Bug修复】现在会检查技能是否为无效值(-1)，确保：
        1. 技能周期结束时重新分配
        2. 环境刚重置时重新分配  
        3. 技能为无效值(-1)时强制重新分配
        """
        if self.use_ha_ctse:
            return self._batched_assign_skills_ha_ctse(
                states_batch,
                observations_batch,
                env_steps_batch,
                dones_batch,
                deterministic=deterministic,
            )
        if self.d2_enabled:
            return self._batched_assign_skills_d2(
                states_batch,
                observations_batch,
                env_steps_batch,
                dones_batch,
                deterministic=deterministic,
            )

        num_envs = states_batch.shape[0]
        
        # 【关键修复】检查当前技能是否无效（-1表示需要重新分配）
        has_invalid_team_skill = np.array([
            self.env_team_skills.get(i, -1) == -1 for i in range(num_envs)
        ])
        has_invalid_agent_skills = np.array([
            np.any(self.env_agent_skills.get(i, np.full(self.config.n_agents, -1)) == -1) 
            for i in range(num_envs)
        ])
        invalid_skills_mask = has_invalid_team_skill | has_invalid_agent_skills
        
        # 找出哪些环境需要重新分配技能 (技能周期结束 或 环境刚重置 或 技能无效)
        needs_reassignment_mask = (env_steps_batch % self.config.k == 0) | dones_batch | invalid_skills_mask
        indices_to_update = np.where(needs_reassignment_mask)[0]
        
        # 日志记录无效技能触发的重分配
        if np.any(invalid_skills_mask):
            invalid_envs = np.where(invalid_skills_mask)[0]
            main_logger.info(f"检测到 {len(invalid_envs)} 个环境技能无效，将强制重新分配: {invalid_envs.tolist()}")

        # 准备最终的技能批次，默认为当前技能
        new_team_skills_batch = np.array([self.env_team_skills.get(i, -1) for i in range(num_envs)], dtype=int)
        new_agent_skills_batch = np.array([self.env_agent_skills.get(i, np.full(self.config.n_agents, -1)) for i in range(num_envs)], dtype=int)
        new_log_probs_batch = [self.env_log_probs.get(i, {}) for i in range(num_envs)]

        if len(indices_to_update) > 0:
            # 提取需要更新的状态和观测，并保持与 update_coordinator 的输入尺度一致
            states_to_process_normalized = self._normalize_states(states_batch[indices_to_update])
            states_to_process = torch.as_tensor(states_to_process_normalized, dtype=torch.float32, device=self.device)
            
            # 【关键修复】应用观测归一化，解决输入尺度问题
            obs_to_process_normalized = self._normalize_observations(observations_batch[indices_to_update])
            obs_to_process = torch.as_tensor(obs_to_process_normalized, dtype=torch.float32, device=self.device)

            # 批量运行 SkillCoordinator
            with torch.no_grad():
                assignment = self.skill_coordinator.assign_and_value_batch(
                    states_to_process,
                    obs_to_process,
                    deterministic=deterministic,
                )
                team_skills = assignment['team_skills']
                agent_skills = assignment['agent_skills']
                state_values = assignment['state_values']
                agent_values_tensor = assignment['agent_values']

                if self.config.use_valuenorm and self.value_norm_coordinator is not None:
                    state_values = self._denormalize_values(state_values, self.value_norm_coordinator)
                    agent_value_columns = [
                        self._denormalize_values(
                            agent_values_tensor[:, agent_idx:agent_idx + 1],
                            self.value_norm_coordinator,
                        ).squeeze(-1)
                        for agent_idx in range(agent_values_tensor.size(1))
                    ]
                    agent_values_tensor = torch.stack(agent_value_columns, dim=1) if agent_value_columns else agent_values_tensor

                team_log_probs_np = assignment['team_log_probs'].detach().cpu().numpy()
                agent_log_probs_np = assignment['agent_log_probs'].detach().cpu().numpy()
                team_skills_np = team_skills.detach().cpu().numpy()
                agent_skills_np = agent_skills.detach().cpu().numpy()
                state_values_np = state_values.squeeze(-1).detach().cpu().numpy()
                agent_values_np = agent_values_tensor.detach().cpu().numpy()
            
            # 将新技能放回正确的位置
            for i, env_idx in enumerate(indices_to_update):
                log_probs = {
                    'team_log_prob': float(team_log_probs_np[i]),
                    'agent_log_probs': agent_log_probs_np[i].astype(np.float32, copy=False).tolist(),
                    # 论文对齐：old value 必须来自技能决策时刻，而不是技能周期结束时重算。
                    'state_value': float(state_values_np[i]),
                    'agent_values': agent_values_np[i].astype(np.float32, copy=False).tolist(),
                }

                # 更新该环境的状态
                new_team_skills_batch[env_idx] = int(team_skills_np[i])
                new_agent_skills_batch[env_idx] = agent_skills_np[i]
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

    # ------------------------------------------------------------------
    # D2 policy-based interruption (ADR 01 revision 3).  Everything below is
    # reachable only when `policy_interruption_mode == "d2"`.
    # ------------------------------------------------------------------

    D2_CAUSE_NONE = 0
    D2_CAUSE_RESET = 1
    D2_CAUSE_TEAM_GAP = 2
    D2_CAUSE_TEAM_CAP = 3
    D2_CAUSE_GAP = 4
    D2_CAUSE_CAP = 5
    D2_CAUSE_NAMES = {
        0: 'none',
        1: 'reset',
        2: 'team_gap',
        3: 'team_cap',
        4: 'gap',
        5: 'cap',
    }

    @staticmethod
    def _new_d2_metrics():
        """Fresh D2 metric accumulators (ADR 01 "Metrics to log", plan section 5)."""
        return {
            'steps': 0,
            'decision_steps': 0,
            'team_decisions': 0,
            'sampled_total': 0,
            'forced_total': 0,
            'S_t_sizes': [],
            'gap_agent': [],
            'gap_team': [],
            'switch_count_by_agent': [],
            'segment_lengths_agent': [],
            'segment_lengths_team': [],
            'cause_counts': {name: 0 for name in ('reset', 'team_gap', 'team_cap', 'gap', 'cap')},
            'coordinator_inference_seconds': 0.0,
            'coordinator_inference_calls': 0,
            'rows_M_agent': 0,
            'rows_M_team': 0,
            'rows_M': 0,
            'optimizer_steps': 0,
            'param_displacement': 0.0,
            'target_scale_team': 0.0,
            'target_scale_agent': 0.0,
            'target_var_team': 0.0,
            'target_var_agent': 0.0,
        }

    def reset_d2_metrics(self):
        """Reset the D2 metric accumulators (called at rollout boundaries)."""
        if self.d2_enabled:
            self.d2_metrics = self._new_d2_metrics()

    def _d2_reset_open_segments(self):
        """Drop all open D2 segment bookkeeping (rollout boundary)."""
        self.d2_open_agent_segments = {}
        self.d2_open_team_segments = {}

    def _d2_open_agent(self, env_id):
        seg = self.d2_open_agent_segments.get(env_id)
        if seg is None:
            seg = {
                'start': np.full(self.config.n_agents, -1, dtype=np.int64),
                'disc': np.zeros(self.config.n_agents, dtype=np.float64),
            }
            self.d2_open_agent_segments[env_id] = seg
        return seg

    def _d2_open_team(self, env_id):
        seg = self.d2_open_team_segments.get(env_id)
        if seg is None:
            seg = {'start': -1, 'disc': 0.0}
            self.d2_open_team_segments[env_id] = seg
        return seg

    def _d2_store_transition(self, env_id, rollout_step_idx, reward, done, d2_step):
        """
        D2 storage (plan section 6): maintain the open per-agent and team
        segments, write a closed row at the segment's start index, and
        accumulate the discounted within-segment reward `sum_u gamma^u r`.

        Close rules: an agent segment closes when the agent is sampled again,
        at episode end (`terminal`), or at rollout end (bootstrap, written by
        `_d2_flush_open_segments`).  The team segment closes on a team
        decision, episode end, or rollout end.  A team decision samples every
        agent, so it closes every agent segment (invariant 7).
        """
        if rollout_step_idx is None:
            main_logger.error("D2 storage requires rollout_step_idx")
            return False

        t = int(rollout_step_idx)
        gamma = float(self.config.gamma)
        n_agents = self.config.n_agents
        seg = self._d2_open_agent(env_id)
        team = self._d2_open_team(env_id)

        sampled = np.asarray(d2_step['sampled_mask'], dtype=np.bool_)
        sample_Z = bool(d2_step['sample_Z'])
        decision = bool(d2_step['decision'])

        # 1. Close the segments that this step's decision ends.
        for i in range(n_agents):
            if sampled[i] and seg['start'][i] >= 0:
                start = int(seg['start'][i])
                elapsed = t - start
                self.rollout_buffer.close_d2_agent_segment(
                    env_id, i, start, float(seg['disc'][i]), elapsed, False
                )
                self.d2_metrics['segment_lengths_agent'].append(int(max(1, elapsed)))
                seg['start'][i] = -1
                seg['disc'][i] = 0.0
        if sample_Z and team['start'] >= 0:
            start = int(team['start'])
            elapsed = t - start
            self.rollout_buffer.close_d2_team_segment(
                env_id, start, float(team['disc']), elapsed, False
            )
            self.d2_metrics['segment_lengths_team'].append(int(max(1, elapsed)))
            team['start'] = -1
            team['disc'] = 0.0

        # 2. Open the segments this step's decision starts, and record the
        #    replay metadata / ages of the step.
        for i in range(n_agents):
            if sampled[i]:
                seg['start'][i] = t
                seg['disc'][i] = 0.0
        if sample_Z:
            team['start'] = t
            team['disc'] = 0.0

        log_probs = self.env_log_probs.get(env_id, {})
        self.rollout_buffer.add_d2_step(
            env_idx=env_id,
            time_step=t,
            agent_age=d2_step['agent_ages'],
            team_age=d2_step['team_age'],
            decision=decision,
            team_skill=int(self.env_team_skills.get(env_id, -1)),
            agent_skills=np.asarray(
                self.env_agent_skills.get(env_id, np.full(n_agents, -1, dtype=np.int64)),
                dtype=np.int64,
            ),
            sampled_mask=sampled,
            sample_Z=sample_Z,
            order=d2_step['order'],
            team_log_prob=float(log_probs.get('team_log_prob', 0.0)),
            agent_log_probs=np.asarray(
                log_probs.get('agent_log_probs', [0.0] * n_agents), dtype=np.float32
            ),
            team_value=float(log_probs.get('state_value', 0.0)),
            agent_values=np.asarray(
                log_probs.get('agent_values', [0.0] * n_agents), dtype=np.float32
            ),
            agent_cause=d2_step['agent_cause'],
            team_cause=d2_step['team_cause'],
        )

        # 3. Accumulate the discounted within-segment reward for this step.
        r = float(reward)
        for i in range(n_agents):
            start = int(seg['start'][i])
            if start >= 0:
                seg['disc'][i] += (gamma ** (t - start)) * r
        if team['start'] >= 0:
            team['disc'] += (gamma ** (t - int(team['start']))) * r

        # 4. Episode end closes every open segment as terminal.
        any_done = bool(np.any(done)) if hasattr(done, '__iter__') else bool(done)
        if any_done:
            for i in range(n_agents):
                start = int(seg['start'][i])
                if start >= 0:
                    self.rollout_buffer.close_d2_agent_segment(
                        env_id, i, start, float(seg['disc'][i]), t - start + 1, True
                    )
                    self.d2_metrics['segment_lengths_agent'].append(int(t - start + 1))
                    seg['start'][i] = -1
                    seg['disc'][i] = 0.0
            if team['start'] >= 0:
                start = int(team['start'])
                self.rollout_buffer.close_d2_team_segment(
                    env_id, start, float(team['disc']), t - start + 1, True
                )
                self.d2_metrics['segment_lengths_team'].append(int(t - start + 1))
                team['start'] = -1
                team['disc'] = 0.0
        return True

    def _d2_flush_open_segments(self, num_steps):
        """
        Close every still-open D2 segment at the rollout boundary with
        `terminal = False`, so the GAE bootstraps it with the value of the next
        state (plan section 6, mirroring `high_level_last_values` in `off`).
        """
        if not self.d2_enabled:
            return 0
        last_t = int(num_steps) - 1
        if last_t < 0:
            return 0
        closed = 0
        for env_id, seg in self.d2_open_agent_segments.items():
            for i in range(self.config.n_agents):
                start = int(seg['start'][i])
                if start >= 0:
                    self.rollout_buffer.close_d2_agent_segment(
                        env_id, i, start, float(seg['disc'][i]), last_t - start + 1, False
                    )
                    self.d2_metrics['segment_lengths_agent'].append(int(last_t - start + 1))
                    seg['start'][i] = -1
                    seg['disc'][i] = 0.0
                    closed += 1
        for env_id, team in self.d2_open_team_segments.items():
            start = int(team['start'])
            if start >= 0:
                self.rollout_buffer.close_d2_team_segment(
                    env_id, start, float(team['disc']), last_t - start + 1, False
                )
                self.d2_metrics['segment_lengths_team'].append(int(last_t - start + 1))
                team['start'] = -1
                team['disc'] = 0.0
                closed += 1
        tables = self.rollout_buffer.get_d2_tables(num_steps)
        if tables is not None:
            self.d2_metrics['rows_M_agent'] = int(tables['agent_valid'].sum())
            self.d2_metrics['rows_M_team'] = int(tables['team_valid'].sum())
            self.d2_metrics['rows_M'] = int(
                (tables['agent_valid'].any(axis=-1) | tables['team_valid']).sum()
            )
        return closed

    def get_d2_metrics(self):
        """Return a JSON-friendly summary of the accumulated D2 metrics."""
        if not self.d2_enabled or self.d2_metrics is None:
            return None
        m = self.d2_metrics
        n_agents = int(self.config.n_agents)
        switch_by_agent = np.zeros(n_agents, dtype=np.int64)
        for row in m['switch_count_by_agent']:
            switch_by_agent += np.asarray(row, dtype=np.int64)
        gap_agent = np.asarray(m['gap_agent'], dtype=np.float64) if m['gap_agent'] else np.zeros(0)
        gap_team = np.asarray(m['gap_team'], dtype=np.float64) if m['gap_team'] else np.zeros(0)

        def _hist(values):
            if values.size == 0:
                return {'count': 0}
            return {
                'count': int(values.size),
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'quantiles': [float(q) for q in np.quantile(values, [0.1, 0.5, 0.9])],
            }

        steps = max(1, int(m['steps']))
        return {
            'steps': int(m['steps']),
            'decision_steps': int(m['decision_steps']),
            'team_decisions': int(m['team_decisions']),
            'sampled_total': int(m['sampled_total']),
            'forced_total': int(m['forced_total']),
            'mean_S_t': float(np.mean(m['S_t_sizes'])) if m['S_t_sizes'] else 0.0,
            'S_t_fraction': (
                float(np.mean(m['S_t_sizes'])) / float(n_agents) if m['S_t_sizes'] else 0.0
            ),
            'switch_rate_by_agent': [float(c) / steps for c in switch_by_agent.tolist()],
            'switch_count_by_agent': switch_by_agent.tolist(),
            'gap_agent_hist': _hist(gap_agent),
            'gap_team_hist': _hist(gap_team),
            'cause_counts': dict(m['cause_counts']),
            'coordinator_inference_seconds': float(m['coordinator_inference_seconds']),
            'coordinator_inference_calls': int(m['coordinator_inference_calls']),
            'segment_length_agent_mean': (
                float(np.mean(m['segment_lengths_agent'])) if m['segment_lengths_agent'] else 0.0
            ),
            'segment_length_team_mean': (
                float(np.mean(m['segment_lengths_team'])) if m['segment_lengths_team'] else 0.0
            ),
            'rows_M_agent': int(m['rows_M_agent']),
            'rows_M_team': int(m['rows_M_team']),
            'rows_M': int(m['rows_M']),
            'optimizer_steps': int(m['optimizer_steps']),
            'param_displacement': float(m['param_displacement']),
            'target_scale_team': float(m['target_scale_team']),
            'target_scale_agent': float(m['target_scale_agent']),
            'target_var_team': float(m['target_var_team']),
            'target_var_agent': float(m['target_var_agent']),
        }

    def _batched_assign_skills_d2(self, states_batch, observations_batch, env_steps_batch,
                                  dones_batch, deterministic=False):
        """
        D2 rollout logic (plan section 5, ADR 01 "Decision").

        Per env and step: reset/done/invalid forces a team decision with every
        agent sampled; otherwise one teacher-forced pass over the held joint
        action gives the gaps `g_Z`, `g_i`, a team decision fires on
        `g_Z >= c_Z` or `a_Z >= k_Z`, and otherwise agent `i` is sampled on
        `g_i >= c` or `a_i >= k_max`.  The teacher-forced pass draws no RNG;
        sampling happens only in `assign_partial_batch` and only for `S_t`.

        Age convention: `a_x` is the number of steps elapsed since the decision
        that produced the currently held skill, evaluated *before* this step's
        decision.  A skill decided at step `t` has age 0 while it executes at
        step `t` and age `k_max` at step `t + k_max`, so `a_i >= k_max`
        reproduces the `env_steps % k == 0` boundaries of `off` when
        `k_max = k_Z = k`.
        """
        num_envs = states_batch.shape[0]
        n_agents = self.config.n_agents
        dones_mask = np.asarray(dones_batch, dtype=np.bool_).reshape(num_envs)
        env_steps = np.asarray(env_steps_batch, dtype=np.int64).reshape(num_envs)

        has_invalid_team_skill = np.array([
            self.env_team_skills.get(i, -1) == -1 for i in range(num_envs)
        ])
        has_invalid_agent_skills = np.array([
            np.any(np.asarray(
                self.env_agent_skills.get(i, np.full(n_agents, -1, dtype=np.int64)),
                dtype=np.int64,
            ) == -1)
            for i in range(num_envs)
        ])
        invalid_skills_mask = has_invalid_team_skill | has_invalid_agent_skills
        # `env_steps == 0` is the first step of an episode; `reset_env_state`
        # additionally invalidates the held skills, so the two agree on the base
        # route.  Both are kept so a collector that omits one still resets.
        reset_mask = (env_steps == 0) | dones_mask | invalid_skills_mask

        for i in range(num_envs):
            if i not in self.env_skill_ages:
                self.env_skill_ages[i] = np.zeros(n_agents, dtype=np.int64)
            if i not in self.env_team_ages:
                self.env_team_ages[i] = 0
        agent_ages = np.stack(
            [np.asarray(self.env_skill_ages[i], dtype=np.int64) for i in range(num_envs)]
        ).astype(np.int64, copy=False)
        team_ages = np.array([int(self.env_team_ages[i]) for i in range(num_envs)], dtype=np.int64)

        held_team = np.array(
            [self.env_team_skills.get(i, -1) for i in range(num_envs)], dtype=np.int64
        )
        held_agents = np.array(
            [np.asarray(
                self.env_agent_skills.get(i, np.full(n_agents, -1, dtype=np.int64)),
                dtype=np.int64,
            ) for i in range(num_envs)],
            dtype=np.int64,
        )

        sampled_mask = np.zeros((num_envs, n_agents), dtype=np.bool_)
        sample_Z_mask = np.zeros(num_envs, dtype=np.bool_)
        team_decision_mask = np.zeros(num_envs, dtype=np.bool_)
        agent_cause = np.zeros((num_envs, n_agents), dtype=np.int64)
        team_cause = np.zeros(num_envs, dtype=np.int64)
        g_agents = np.full((num_envs, n_agents), np.nan, dtype=np.float64)
        g_team = np.full(num_envs, np.nan, dtype=np.float64)

        # 1. Reset / done / invalid: team decision, every agent sampled.
        if np.any(reset_mask):
            sampled_mask[reset_mask] = True
            sample_Z_mask[reset_mask] = True
            team_decision_mask[reset_mask] = True
            agent_cause[reset_mask] = self.D2_CAUSE_RESET
            team_cause[reset_mask] = self.D2_CAUSE_RESET

        # 2. Otherwise: the teacher-forced gap pass, then the cap/gap tests.
        eval_indices = np.where(~reset_mask)[0]
        if eval_indices.size > 0:
            inference_start = time.perf_counter()
            eval_states = torch.as_tensor(
                self._normalize_states(states_batch[eval_indices], update=False),
                dtype=torch.float32,
                device=self.device,
            )
            eval_obs = torch.as_tensor(
                self._normalize_observations(observations_batch[eval_indices], update=False),
                dtype=torch.float32,
                device=self.device,
            )
            held_Z_t = torch.as_tensor(held_team[eval_indices], dtype=torch.long, device=self.device)
            held_z_t = torch.as_tensor(held_agents[eval_indices], dtype=torch.long, device=self.device)
            with torch.no_grad():
                held_eval = self.skill_coordinator.evaluate_held_batch(
                    eval_states, eval_obs, held_Z_t, held_z_t
                )
                Z_logits = held_eval['Z_logits']
                z_logits = held_eval['z_logits']
                gap_Z = (
                    Z_logits.max(dim=-1).values
                    - Z_logits.gather(1, held_Z_t.unsqueeze(1)).squeeze(1)
                ).detach().cpu().numpy()
                gap_z = (
                    z_logits.max(dim=-1).values
                    - z_logits.gather(2, held_z_t.unsqueeze(-1)).squeeze(-1)
                ).detach().cpu().numpy()
            elapsed = time.perf_counter() - inference_start
            self.d2_metrics['coordinator_inference_seconds'] += float(elapsed)
            self.d2_metrics['coordinator_inference_calls'] += 1
            self._add_transition_profile('d2_trigger_inference', elapsed)

            g_team[eval_indices] = gap_Z.astype(np.float64, copy=False)
            g_agents[eval_indices] = gap_z.astype(np.float64, copy=False)

            team_gap_fire = gap_Z >= self.d2_cost_c_Z
            team_cap_fire = team_ages[eval_indices] >= self.d2_k_Z
            team_fire = team_gap_fire | team_cap_fire
            fire_idx = eval_indices[team_fire]
            if fire_idx.size > 0:
                sampled_mask[fire_idx] = True
                sample_Z_mask[fire_idx] = True
                team_decision_mask[fire_idx] = True
                causes = np.where(
                    team_gap_fire[team_fire], self.D2_CAUSE_TEAM_GAP, self.D2_CAUSE_TEAM_CAP
                )
                team_cause[fire_idx] = causes
                agent_cause[fire_idx] = causes[:, None]

            hold_local = ~team_fire
            hold_idx = eval_indices[hold_local]
            if hold_idx.size > 0:
                agent_gap_fire = gap_z[hold_local] >= self.d2_cost_c
                agent_cap_fire = agent_ages[hold_idx] >= self.d2_k_max
                fire = agent_gap_fire | agent_cap_fire
                sampled_mask[hold_idx] = fire
                cause_here = np.where(
                    agent_gap_fire, self.D2_CAUSE_GAP, self.D2_CAUSE_CAP
                )
                agent_cause[hold_idx] = np.where(fire, cause_here, self.D2_CAUSE_NONE)

        # Cheap D2-only invariant asserts (plan section 5).
        if not np.isfinite(self.d2_cost_c):
            assert not np.any(agent_cause == self.D2_CAUSE_GAP), \
                "D2: c = inf produced a `gap` boundary cause"
        if not np.isfinite(self.d2_cost_c_Z):
            assert not np.any(team_cause == self.D2_CAUSE_TEAM_GAP), \
                "D2: c_Z = inf produced a `team_gap` boundary cause"
        assert np.all(sampled_mask[team_decision_mask]), \
            "D2: a team decision did not force every agent into S_t (invariant 7)"

        decision_mask = sampled_mask.any(axis=1)

        new_team_skills_batch = held_team.copy()
        new_agent_skills_batch = held_agents.copy()
        new_log_probs_batch = [self.env_log_probs.get(i, {}) for i in range(num_envs)]

        decision_indices = np.where(decision_mask)[0]
        if decision_indices.size > 0:
            inference_start = time.perf_counter()
            # `update=True` on the decision subset only, exactly as `off` does,
            # so the running normalisers see the same states at D0.
            assign_states = torch.as_tensor(
                self._normalize_states(states_batch[decision_indices]),
                dtype=torch.float32,
                device=self.device,
            )
            assign_obs = torch.as_tensor(
                self._normalize_observations(observations_batch[decision_indices]),
                dtype=torch.float32,
                device=self.device,
            )
            with torch.no_grad():
                assignment = self.skill_coordinator.assign_partial_batch(
                    assign_states,
                    assign_obs,
                    torch.as_tensor(held_team[decision_indices], dtype=torch.long, device=self.device),
                    torch.as_tensor(held_agents[decision_indices], dtype=torch.long, device=self.device),
                    torch.as_tensor(sample_Z_mask[decision_indices], dtype=torch.bool, device=self.device),
                    torch.as_tensor(sampled_mask[decision_indices], dtype=torch.bool, device=self.device),
                    deterministic=deterministic,
                )
                state_values = assignment['state_values']
                agent_values_tensor = assignment['agent_values']
                if self.config.use_valuenorm and self.value_norm_coordinator is not None:
                    state_values = self._denormalize_values(state_values, self.value_norm_coordinator)
                    agent_value_columns = [
                        self._denormalize_values(
                            agent_values_tensor[:, agent_idx:agent_idx + 1],
                            self.value_norm_coordinator,
                        ).squeeze(-1)
                        for agent_idx in range(agent_values_tensor.size(1))
                    ]
                    if agent_value_columns:
                        agent_values_tensor = torch.stack(agent_value_columns, dim=1)

                team_skills_np = assignment['team_skills'].detach().cpu().numpy()
                agent_skills_np = assignment['agent_skills'].detach().cpu().numpy()
                team_log_probs_np = assignment['team_log_probs'].detach().cpu().numpy()
                agent_log_probs_np = assignment['agent_log_probs'].detach().cpu().numpy()
                order_np = assignment['order'].detach().cpu().numpy()
                state_values_np = state_values.squeeze(-1).detach().cpu().numpy()
                agent_values_np = agent_values_tensor.detach().cpu().numpy()
            elapsed = time.perf_counter() - inference_start
            self.d2_metrics['coordinator_inference_seconds'] += float(elapsed)
            self.d2_metrics['coordinator_inference_calls'] += 1
            self._add_transition_profile('d2_assign_inference', elapsed)
        else:
            order_np = np.zeros((0, n_agents), dtype=np.int64)

        order_batch = np.tile(np.arange(n_agents, dtype=np.int64), (num_envs, 1))
        for local_idx, env_idx in enumerate(decision_indices):
            env_idx = int(env_idx)
            new_team_skills_batch[env_idx] = int(team_skills_np[local_idx])
            new_agent_skills_batch[env_idx] = agent_skills_np[local_idx]
            order_batch[env_idx] = order_np[local_idx]
            new_log_probs_batch[env_idx] = {
                'team_log_prob': float(team_log_probs_np[local_idx]),
                'agent_log_probs': agent_log_probs_np[local_idx].astype(np.float32, copy=False).tolist(),
                'state_value': float(state_values_np[local_idx]),
                'agent_values': agent_values_np[local_idx].astype(np.float32, copy=False).tolist(),
            }
            self.env_timers[env_idx] = 0

        for env_idx in np.where(~decision_mask)[0]:
            self.env_timers[int(env_idx)] = self.env_timers.get(int(env_idx), 0) + 1

        # Ages of the skills that actually execute at this step: 0 where the
        # skill was just decided, the pre-decision age otherwise.
        exec_agent_ages = np.where(sampled_mask, 0, agent_ages).astype(np.int64, copy=False)
        exec_team_ages = np.where(sample_Z_mask, 0, team_ages).astype(np.int64, copy=False)

        switched = (new_agent_skills_batch != held_agents) & sampled_mask & (held_agents >= 0)

        for i in range(num_envs):
            self.env_team_skills[i] = int(new_team_skills_batch[i])
            self.env_agent_skills[i] = new_agent_skills_batch[i]
            self.env_log_probs[i] = new_log_probs_batch[i]
            self.env_skill_ages[i] = exec_agent_ages[i] + 1
            self.env_team_ages[i] = int(exec_team_ages[i]) + 1

        self._d2_last_step = {
            'decision': decision_mask.copy(),
            'team_decision': team_decision_mask.copy(),
            'sampled_mask': sampled_mask.copy(),
            'sample_Z': sample_Z_mask.copy(),
            'order': order_batch,
            'agent_ages': exec_agent_ages,
            'team_ages': exec_team_ages,
            'agent_cause': agent_cause,
            'team_cause': team_cause,
            'g_agents': g_agents,
            'g_team': g_team,
        }
        for env_idx in range(num_envs):
            self.env_d2_last_decision[env_idx] = {
                'decision': bool(decision_mask[env_idx]),
                'team_decision': bool(team_decision_mask[env_idx]),
                'sampled_mask': sampled_mask[env_idx].copy(),
                'sample_Z': bool(sample_Z_mask[env_idx]),
                'order': order_batch[env_idx].copy(),
                'agent_ages': exec_agent_ages[env_idx].copy(),
                'team_age': int(exec_team_ages[env_idx]),
                'agent_cause': agent_cause[env_idx].copy(),
                'team_cause': int(team_cause[env_idx]),
            }

        metrics = self.d2_metrics
        metrics['steps'] += num_envs
        metrics['decision_steps'] += int(decision_mask.sum())
        metrics['team_decisions'] += int(team_decision_mask.sum())
        metrics['sampled_total'] += int(sampled_mask.sum())
        metrics['forced_total'] += int((~sampled_mask).sum())
        metrics['S_t_sizes'].extend(sampled_mask.sum(axis=1).astype(np.int64).tolist())
        metrics['switch_count_by_agent'].append(switched.sum(axis=0).astype(np.int64))
        finite_agent_gaps = g_agents[np.isfinite(g_agents)]
        if finite_agent_gaps.size:
            metrics['gap_agent'].extend(finite_agent_gaps.tolist())
        finite_team_gaps = g_team[np.isfinite(g_team)]
        if finite_team_gaps.size:
            metrics['gap_team'].extend(finite_team_gaps.tolist())
        # Team-level causes are counted once per env; per-agent causes are counted
        # per sampled (env, agent) position.
        metrics['cause_counts']['reset'] += int(np.sum(team_cause == self.D2_CAUSE_RESET))
        metrics['cause_counts']['team_gap'] += int(np.sum(team_cause == self.D2_CAUSE_TEAM_GAP))
        metrics['cause_counts']['team_cap'] += int(np.sum(team_cause == self.D2_CAUSE_TEAM_CAP))
        metrics['cause_counts']['gap'] += int(np.sum(agent_cause == self.D2_CAUSE_GAP))
        metrics['cause_counts']['cap'] += int(np.sum(agent_cause == self.D2_CAUSE_CAP))

        return new_team_skills_batch, new_agent_skills_batch, new_log_probs_batch

    def _batched_assign_skills_ha_ctse(self, states_batch, observations_batch, env_steps_batch, dones_batch, deterministic=False):
        """
        HA-CTSE high-level assignment.

        The global interval k still determines when compact/team-code/editor
        decisions are considered. At those boundaries each agent either keeps
        its active skill or edits it according to the bounded termination mask.
        """
        num_envs = states_batch.shape[0]
        n_agents = self.config.n_agents
        dones_mask = np.asarray(dones_batch, dtype=np.bool_).reshape(num_envs)

        has_invalid_team_skill = np.array([
            self.env_team_skills.get(i, -1) == -1 for i in range(num_envs)
        ])
        has_invalid_agent_skills = np.array([
            np.any(self.env_agent_skills.get(i, np.full(n_agents, -1, dtype=np.int64)) == -1)
            for i in range(num_envs)
        ])
        invalid_skills_mask = has_invalid_team_skill | has_invalid_agent_skills
        boundary_mask = (env_steps_batch % self.config.k == 0)
        duration_remaining_batch = np.asarray(
            [
                self.env_skill_duration_remaining.get(
                    i,
                    np.zeros(n_agents, dtype=np.int64),
                )
                for i in range(num_envs)
            ],
            dtype=np.int64,
        )
        if self.use_discrete_skill_lifetimes:
            duration_expired_agents = duration_remaining_batch <= 1
            duration_expired_env = np.any(duration_expired_agents, axis=1)
            needs_reassignment_mask = (
                invalid_skills_mask
                | dones_mask
                | (boundary_mask & duration_expired_env)
            )
            keep_countdown_mask = boundary_mask & ~needs_reassignment_mask & ~invalid_skills_mask & ~dones_mask
            for keep_env_idx in np.where(keep_countdown_mask)[0]:
                keep_env_idx = int(keep_env_idx)
                self.env_skill_duration_remaining[keep_env_idx] = np.maximum(
                    self.env_skill_duration_remaining.get(
                        keep_env_idx,
                        np.zeros(n_agents, dtype=np.int64),
                    ) - 1,
                    0,
                ).astype(np.int64, copy=False)
                self.env_skill_ages[keep_env_idx] = (
                    self.env_skill_ages.get(keep_env_idx, np.zeros(n_agents, dtype=np.int64)) + 1
                ).astype(np.int64, copy=False)
        else:
            duration_expired_agents = np.zeros((num_envs, n_agents), dtype=np.bool_)
            needs_reassignment_mask = boundary_mask | dones_mask | invalid_skills_mask
        indices_to_update = np.where(needs_reassignment_mask)[0]

        new_team_skills_batch = np.array(
            [self.env_team_skills.get(i, -1) for i in range(num_envs)],
            dtype=np.int64,
        )
        new_agent_skills_batch = np.array(
            [self.env_agent_skills.get(i, np.full(n_agents, -1, dtype=np.int64)) for i in range(num_envs)],
            dtype=np.int64,
        )
        new_log_probs_batch = [self.env_log_probs.get(i, {}) for i in range(num_envs)]

        if len(indices_to_update) > 0:
            states_to_process = torch.as_tensor(
                self._normalize_states(states_batch[indices_to_update]),
                dtype=torch.float32,
                device=self.device,
            )
            obs_to_process = torch.as_tensor(
                self._normalize_observations(observations_batch[indices_to_update]),
                dtype=torch.float32,
                device=self.device,
            )
            prev_skills_np = np.asarray(
                [self.env_agent_skills.get(int(env_idx), np.full(n_agents, -1, dtype=np.int64))
                 for env_idx in indices_to_update],
                dtype=np.int64,
            )
            skill_ages_np = np.asarray(
                [self.env_skill_ages.get(int(env_idx), np.zeros(n_agents, dtype=np.int64))
                 for env_idx in indices_to_update],
                dtype=np.int64,
            )
            initial_assignment_np = np.asarray(
                [
                    np.full(
                        n_agents,
                        bool(invalid_skills_mask[int(env_idx)] or dones_mask[int(env_idx)]),
                        dtype=np.float32,
                    )
                    for env_idx in indices_to_update
                ],
                dtype=np.float32,
            )
            forced_edit_np = np.zeros_like(initial_assignment_np, dtype=np.float32)
            forced_keep_np = np.zeros_like(initial_assignment_np, dtype=np.float32)
            if self.use_discrete_skill_lifetimes:
                forced_edit_np = duration_expired_agents[indices_to_update].astype(np.float32)
                forced_edit_np = np.maximum(forced_edit_np, initial_assignment_np)
                forced_keep_np = (
                    (1.0 - forced_edit_np)
                    * (1.0 - initial_assignment_np)
                ).astype(np.float32, copy=False)

            with torch.no_grad():
                assignment = self.ha_ctse_editor.assign_and_value_batch(
                    states_to_process,
                    obs_to_process,
                    torch.as_tensor(prev_skills_np, dtype=torch.long, device=self.device),
                    torch.as_tensor(skill_ages_np, dtype=torch.long, device=self.device),
                    torch.as_tensor(initial_assignment_np, dtype=torch.bool, device=self.device),
                    deterministic=deterministic,
                    forced_keep_mask=torch.as_tensor(forced_keep_np, dtype=torch.bool, device=self.device),
                    forced_edit_mask=torch.as_tensor(forced_edit_np, dtype=torch.bool, device=self.device),
                )

                state_values = assignment['state_values']
                agent_values_tensor = assignment['agent_values']
                if self.config.use_valuenorm and self.value_norm_coordinator is not None:
                    state_values = self._denormalize_values(state_values, self.value_norm_coordinator)
                    agent_value_columns = [
                        self._denormalize_values(
                            agent_values_tensor[:, agent_idx:agent_idx + 1],
                            self.value_norm_coordinator,
                        ).squeeze(-1)
                        for agent_idx in range(agent_values_tensor.size(1))
                    ]
                    agent_values_tensor = torch.stack(agent_value_columns, dim=1) if agent_value_columns else agent_values_tensor

                assignment_np = {
                    key: value.detach().cpu().numpy()
                    for key, value in assignment.items()
                    if isinstance(value, torch.Tensor)
                }
                state_values_np = state_values.squeeze(-1).detach().cpu().numpy()
                agent_values_np = agent_values_tensor.detach().cpu().numpy()

            for local_idx, env_idx in enumerate(indices_to_update):
                env_idx = int(env_idx)
                agent_skills = assignment_np['active_skill'][local_idx].astype(np.int64, copy=False)
                team_code = int(assignment_np['team_code'][local_idx])
                team_code = int(np.clip(team_code, 0, self.config.n_Z - 1))

                log_probs = {
                    'new_high_level_decision': True,
                    'team_log_prob': float(assignment_np['log_prob_team_code'][local_idx]),
                    'agent_log_probs': (
                        assignment_np['log_prob_term'][local_idx]
                        + assignment_np['log_prob_skill'][local_idx]
                        + assignment_np.get('log_prob_duration', np.zeros(n_agents, dtype=np.float32))[local_idx]
                    ).astype(np.float32, copy=False).tolist(),
                    'state_value': float(state_values_np[local_idx]),
                    'agent_values': agent_values_np[local_idx].astype(np.float32, copy=False).tolist(),
                    'compact': assignment_np['compact'][local_idx].astype(np.float32, copy=False),
                    'team_code': team_code,
                    'log_prob_team_code': float(assignment_np['log_prob_team_code'][local_idx]),
                    'entropy_team_code': float(assignment_np['entropy_team_code'][local_idx]),
                    'opt_aggregation_entropy': float(assignment_np['aggregation_entropy'][local_idx]),
                    'active_skill_prev': assignment_np['active_skill_prev'][local_idx].astype(np.int64, copy=False),
                    'active_skill': agent_skills,
                    'candidate_skill': assignment_np['candidate_skill'][local_idx].astype(np.int64, copy=False),
                    'skill_age_prev': assignment_np['skill_age_prev'][local_idx].astype(np.int64, copy=False),
                    'skill_age': assignment_np['skill_age'][local_idx].astype(np.int64, copy=False),
                    'duration_candidate': assignment_np.get('duration_candidate', np.zeros((len(indices_to_update), n_agents), dtype=np.int64))[local_idx].astype(np.int64, copy=False),
                    'duration_target': assignment_np.get('duration_target', np.ones((len(indices_to_update), n_agents), dtype=np.int64))[local_idx].astype(np.int64, copy=False),
                    'duration_remaining': assignment_np.get('duration_remaining', np.zeros((len(indices_to_update), n_agents), dtype=np.int64))[local_idx].astype(np.int64, copy=False),
                    'requested_edit_mask': assignment_np['requested_edit_mask'][local_idx].astype(np.float32, copy=False),
                    'executed_edit_mask': assignment_np['executed_edit_mask'][local_idx].astype(np.float32, copy=False),
                    'log_prob_term': assignment_np['log_prob_term'][local_idx].astype(np.float32, copy=False),
                    'log_prob_skill': assignment_np['log_prob_skill'][local_idx].astype(np.float32, copy=False),
                    'log_prob_duration': assignment_np.get('log_prob_duration', np.zeros((len(indices_to_update), n_agents), dtype=np.float32))[local_idx].astype(np.float32, copy=False),
                    'entropy_term': assignment_np['entropy_term'][local_idx].astype(np.float32, copy=False),
                    'entropy_skill': assignment_np['entropy_skill'][local_idx].astype(np.float32, copy=False),
                    'entropy_duration': assignment_np.get('entropy_duration', np.zeros((len(indices_to_update), n_agents), dtype=np.float32))[local_idx].astype(np.float32, copy=False),
                    'initial_assignment_mask': assignment_np['initial_assignment_mask'][local_idx].astype(np.float32, copy=False),
                }

                new_team_skills_batch[env_idx] = team_code
                new_agent_skills_batch[env_idx] = agent_skills
                new_log_probs_batch[env_idx] = log_probs
                self.env_skill_ages[env_idx] = assignment_np['skill_age'][local_idx].astype(np.int64, copy=False)
                if self.use_discrete_skill_lifetimes:
                    old_remaining = self.env_skill_duration_remaining.get(
                        env_idx,
                        np.zeros(n_agents, dtype=np.int64),
                    )
                    decremented = np.maximum(old_remaining - int(boundary_mask[env_idx]), 0)
                    executed = log_probs['executed_edit_mask'] > 0.5
                    target = log_probs['duration_target'].astype(np.int64, copy=False)
                    remaining = decremented.astype(np.int64, copy=True)
                    remaining[executed] = target[executed]
                    self.env_skill_duration_remaining[env_idx] = remaining
                    prev_target = self.env_skill_duration_target.get(
                        env_idx,
                        np.zeros(n_agents, dtype=np.int64),
                    )
                    next_target = prev_target.astype(np.int64, copy=True)
                    next_target[executed] = target[executed]
                    self.env_skill_duration_target[env_idx] = next_target
                    log_probs['duration_remaining'] = remaining.astype(np.int64, copy=False)
                self._open_or_replace_process_segments(env_idx, int(env_steps_batch[env_idx]), log_probs)
                self.env_timers[env_idx] = 0

        for env_idx in np.where(~needs_reassignment_mask)[0]:
            env_idx = int(env_idx)
            if (
                self.use_discrete_skill_lifetimes
                and bool(boundary_mask[env_idx])
                and not bool(invalid_skills_mask[env_idx])
                and not bool(dones_mask[env_idx])
            ):
                # A high-level check boundary happened, but no new decision was
                # sampled because the active duration has not expired. Keep the
                # old pending PPO sample open and restart the k-local timer.
                self.env_timers[env_idx] = 0
            else:
                self.env_timers[env_idx] = self.env_timers.get(env_idx, 0) + 1

        for i in range(num_envs):
            self.env_team_skills[i] = int(new_team_skills_batch[i])
            self.env_agent_skills[i] = new_agent_skills_batch[i]
            stored_log_probs = dict(new_log_probs_batch[i]) if isinstance(new_log_probs_batch[i], dict) else {}
            if i not in set(int(idx) for idx in indices_to_update):
                stored_log_probs['new_high_level_decision'] = False
            self.env_log_probs[i] = stored_log_probs
            new_log_probs_batch[i] = stored_log_probs
            if i not in self.env_skill_ages:
                self.env_skill_ages[i] = np.zeros(n_agents, dtype=np.int64)

        return new_team_skills_batch, new_agent_skills_batch, new_log_probs_batch

    def _batched_select_action(self, states_batch, observations_batch, agent_skills_batch, team_skills_batch, dones_batch, deterministic=False):
        """
        【论文一致性修复】为一批环境选择动作，正确管理 Actor 和 Critic 的 GRU 隐藏状态
        
        【重要修复】现在每个智能体都有独立的Critic隐状态，与on-policy-main保持一致
        """
        profile_enabled = self.enable_runtime_profiling
        input_start = time.perf_counter() if profile_enabled else 0.0
        num_envs, n_agents, _ = observations_batch.shape
        dones_mask = np.asarray(dones_batch, dtype=np.bool_).reshape(num_envs)

        if self.r39_native_toy_fixed_primitives:
            self._sync_legacy_hidden_to_arrays(num_envs)
            self.actor_hidden_np[:num_envs].fill(0.0)
            self.critic_hidden_np[:num_envs].fill(0.0)
            self.prev_actor_hidden_np[:num_envs].fill(0.0)
            self.prev_critic_hidden_np[:num_envs].fill(0.0)
            self._hidden_state_array_valid[:num_envs] = True
            skills_tensor = torch.as_tensor(
                agent_skills_batch,
                dtype=torch.long,
                device=self.device,
            )
            if skills_tensor.shape != (num_envs, n_agents):
                raise ValueError(
                    f'native toy skills must have shape {(num_envs, n_agents)}, got {tuple(skills_tensor.shape)}'
                )
            with torch.no_grad():
                actions_tensor, logprobs_tensor, values_tensor = self.native_toy_fixed_primitive_executor(
                    skills_tensor
                )
            self._step_profile['calls'] += 1
            return (
                actions_tensor.detach().cpu().numpy(),
                logprobs_tensor.detach().cpu().numpy(),
                values_tensor.detach().cpu().numpy(),
            )
        
        # === 1. 管理 Actor 和 Critic 的隐藏状态 ===
        hidden_extract_start = time.perf_counter() if profile_enabled else 0.0
        self._sync_legacy_hidden_to_arrays(num_envs)
        actor_hidden_states_batch = self.actor_hidden_np[:num_envs].copy()
        critic_hidden_states_batch = self.critic_hidden_np[:num_envs].copy()

        # 重置已完成环境的隐藏状态
        if np.any(dones_mask):
            actor_hidden_states_batch[dones_mask] = 0.0
            critic_hidden_states_batch[dones_mask] = 0.0
        if profile_enabled:
            self._step_profile['hidden_extract'] += time.perf_counter() - hidden_extract_start

        # === 2. 准备批量输入 ===
        obs_flat = observations_batch.reshape(-1, self.config.obs_dim)
        
        # 【关键修复】应用观测归一化，解决输入尺度问题
        obs_flat_normalized = self._normalize_observations(obs_flat)
        
        skills_flat = agent_skills_batch.reshape(-1)
        actor_hidden_flat = np.ascontiguousarray(
            actor_hidden_states_batch.reshape(-1, self.config.gru_hidden_size)
        )

        # 为每个智能体提供对应的全局状态和团队技能
        states_expanded = np.repeat(states_batch, n_agents, axis=0)
        team_skills_expanded = np.repeat(team_skills_batch, n_agents, axis=0)

        # 【关键修复】应用状态标准化，解决Critic输入尺度问题
        states_expanded_normalized = self._normalize_states(states_expanded)
        critic_hidden_flat = np.ascontiguousarray(
            critic_hidden_states_batch.reshape(-1, self.config.gru_hidden_size)
        )

        tensor_upload_start = time.perf_counter() if profile_enabled else 0.0
        obs_tensor = torch.as_tensor(obs_flat_normalized, dtype=torch.float32, device=self.device)
        skills_tensor = torch.as_tensor(skills_flat, dtype=torch.long, device=self.device)
        actor_hidden_tensor = torch.as_tensor(actor_hidden_flat, dtype=torch.float32, device=self.device)
        states_tensor = torch.as_tensor(states_expanded_normalized, dtype=torch.float32, device=self.device)
        team_skills_tensor = torch.as_tensor(team_skills_expanded, dtype=torch.long, device=self.device)
        critic_hidden_tensor = torch.as_tensor(critic_hidden_flat, dtype=torch.float32, device=self.device)
        low_level_compact_flat = None

        if profile_enabled:
            self._sync_cuda_for_profile()
            self._step_profile['tensor_upload'] += time.perf_counter() - tensor_upload_start
            self._step_profile['input_prepare'] += time.perf_counter() - input_start
            forward_start = time.perf_counter()
        
        with torch.no_grad():
            if self.use_low_level_compact and self.low_level_compact_extractor is not None:
                states_env_normalized = states_expanded_normalized.reshape(num_envs, n_agents, self.config.state_dim)[:, 0, :]
                observations_env_normalized = obs_flat_normalized.reshape(num_envs, n_agents, self.config.obs_dim)
                compact_env = self._compute_low_level_compact_context(
                    torch.as_tensor(states_env_normalized, dtype=torch.float32, device=self.device),
                    torch.as_tensor(observations_env_normalized, dtype=torch.float32, device=self.device),
                )
                low_level_compact_flat = compact_env.unsqueeze(1).expand(-1, n_agents, -1).reshape(
                    num_envs * n_agents,
                    -1,
                )
            # === 3. 批量运行 Actor 网络获取动作 ===
            policy_start = time.perf_counter() if profile_enabled else 0.0
            actions_flat, logprobs_flat, _, new_actor_hidden_flat = self.skill_discoverer(
                obs_tensor,
                skills_tensor,
                actor_hidden_tensor,
                deterministic,
                compact_context=low_level_compact_flat,
            )
            if profile_enabled:
                self._sync_cuda_for_profile()
                self._step_profile['policy_forward'] += time.perf_counter() - policy_start

            # === 4. 批量运行 Critic 网络获取价值估计 (使用独立的Critic隐状态) ===
            # 【关键修复】使用新的 get_value 方法，传入每个智能体独立的Critic隐状态
            critic_start = time.perf_counter() if profile_enabled else 0.0
            values_flat, new_critic_hidden_flat = self.skill_discoverer.get_value(
                states_tensor,
                team_skills_tensor,
                critic_hidden_tensor,
                compact_context=low_level_compact_flat,
            )
            
            # 【关键修复】在此处反归一化，确保传出的是真实价值
            if self.config.use_valuenorm and self.value_norm_discoverer is not None:
                values_flat = self._denormalize_values(values_flat, self.value_norm_discoverer)
            if profile_enabled:
                self._sync_cuda_for_profile()
                self._step_profile['critic_forward'] += time.perf_counter() - critic_start

        if profile_enabled:
            self._sync_cuda_for_profile()
            self._step_profile['gpu_forward'] += time.perf_counter() - forward_start
            output_start = time.perf_counter()
            
        # === 5. Reshape 输出 ===
        # 根据动作空间类型正确reshape动作
        action_space_type = getattr(self.config, 'action_space_type', 'continuous')
        action_sync_start = time.perf_counter() if profile_enabled else 0.0
        actions_np = actions_flat.detach().cpu().numpy()
        if profile_enabled:
            self._step_profile['action_sync'] += time.perf_counter() - action_sync_start

        value_logprob_sync_start = time.perf_counter() if profile_enabled else 0.0
        logprobs_np = logprobs_flat.detach().cpu().numpy()
        values_np = values_flat.detach().cpu().numpy()
        if profile_enabled:
            self._step_profile['value_logprob_sync'] += time.perf_counter() - value_logprob_sync_start

        hidden_sync_start = time.perf_counter() if profile_enabled else 0.0
        new_actor_hidden_np = new_actor_hidden_flat.detach().cpu().numpy()
        new_critic_hidden_np = new_critic_hidden_flat.detach().cpu().numpy()
        if profile_enabled:
            self._step_profile['hidden_sync'] += time.perf_counter() - hidden_sync_start

        if action_space_type == 'discrete':
            actions_batch = actions_np.reshape(num_envs, n_agents)
        else:
            actions_batch = actions_np.reshape(num_envs, n_agents, self.config.action_dim)
        logprobs_batch = logprobs_np.reshape(num_envs, n_agents)
        values_batch = values_np.reshape(num_envs, n_agents)
        
        new_actor_hidden_batch = new_actor_hidden_np.reshape(num_envs, n_agents, self.config.gru_hidden_size)
        new_critic_hidden_batch = new_critic_hidden_np.reshape(num_envs, n_agents, self.config.gru_hidden_size)

        if profile_enabled:
            self._step_profile['output_sync'] += time.perf_counter() - output_start
            hidden_update_start = time.perf_counter()
        
        # === 6. 更新内部隐藏状态 ===
        # 【关键修复】保存当前步的输入隐藏状态到 prev，用于store_transition。
        # 训练热路径保持为预分配数组，避免每步按环境写dict和重新分配GPU Tensor。
        self.prev_actor_hidden_np[:num_envs] = actor_hidden_states_batch
        self.prev_critic_hidden_np[:num_envs] = critic_hidden_states_batch
        self.actor_hidden_np[:num_envs] = new_actor_hidden_batch
        self.critic_hidden_np[:num_envs] = new_critic_hidden_batch
        self._hidden_state_array_valid[:num_envs] = True

        if profile_enabled:
            hidden_store_elapsed = time.perf_counter() - hidden_update_start
            self._step_profile['hidden_state_update'] += hidden_store_elapsed
            self._step_profile['hidden_store'] += hidden_store_elapsed
            self._step_profile['calls'] += 1
            
        return actions_batch, logprobs_batch, values_batch

    def step(self, states_batch, observations_batch, env_steps_batch, dones_batch, deterministic=False,
             return_step_data=False, build_infos=True):
        """
        [重构后的核心方法] 为所有并行环境执行一个完整的、批量的步骤。
        这个方法将由训练循环在每一步调用一次。
        """
        num_envs = states_batch.shape[0]
        
        # 初始化环境状态（如果需要）
        for i in range(num_envs):
            if i not in self.env_timers:
                self.env_timers[i] = 0
                if self.use_ha_ctse:
                    self.env_team_skills[i] = -1
                    self.env_agent_skills[i] = np.full(self.config.n_agents, -1, dtype=np.int64)
                    self.env_skill_ages[i] = np.zeros(self.config.n_agents, dtype=np.int64)
                    self.env_skill_duration_remaining[i] = np.zeros(self.config.n_agents, dtype=np.int64)
                    self.env_skill_duration_target[i] = np.zeros(self.config.n_agents, dtype=np.int64)
                    self.env_log_probs[i] = {}
                else:
                    # 【关键修复】立即为新环境分配随机技能，而不是使用-1占位符
                    with torch.no_grad():
                        # 随机分配团队技能
                        random_team_skill = np.random.randint(0, self.config.n_Z)
                        # 随机分配个体技能
                        random_agent_skills = np.random.randint(0, self.config.n_z, size=self.config.n_agents)

                        self.env_team_skills[i] = random_team_skill
                        self.env_agent_skills[i] = random_agent_skills

                        # 创建对应的log_probs（使用均匀分布的log概率）
                        uniform_team_log_prob = -np.log(self.config.n_Z)
                        uniform_agent_log_probs = [-np.log(self.config.n_z)] * self.config.n_agents

                        self.env_log_probs[i] = {
                            'team_log_prob': uniform_team_log_prob,
                            'agent_log_probs': uniform_agent_log_probs
                        }

                        main_logger.info(f"环境{i}初始化: 团队技能={random_team_skill}, "
                                       f"个体技能={random_agent_skills}")

                self.env_hidden_states[i] = None
                self._reset_hidden_state_arrays_for_env(i)

        # 1. 批量分配技能
        profile_enabled = self.enable_runtime_profiling
        profile_start = time.perf_counter() if profile_enabled else 0.0
        team_skills, agent_skills, log_probs_list = self._batched_assign_skills(
            states_batch, observations_batch, env_steps_batch, dones_batch, deterministic
        )
        if profile_enabled:
            self._sync_cuda_for_profile()
            self._step_profile['skill_assign'] += time.perf_counter() - profile_start

        # 2. 批量选择动作
        profile_start = time.perf_counter() if profile_enabled else 0.0
        actions, action_logprobs, values = self._batched_select_action(
            states_batch, observations_batch, agent_skills, team_skills, dones_batch, deterministic
        )
        if profile_enabled:
            self._sync_cuda_for_profile()
            self._step_profile['action_select'] += time.perf_counter() - profile_start

        if self.use_ha_ctse:
            skill_changed = np.asarray(
                [self._is_new_high_level_decision(log_probs) for log_probs in log_probs_list],
                dtype=bool,
            ) | np.asarray(dones_batch, dtype=bool)
        elif self.d2_enabled:
            # A D2 boundary is any step where at least one agent is re-decided;
            # a team decision implies every agent is sampled (invariant 7).
            skill_changed = np.asarray(self._d2_last_step['decision'], dtype=bool)
        else:
            skill_changed = ((env_steps_batch % self.config.k) == 0) | np.asarray(dones_batch, dtype=bool)
        skill_timers = np.asarray([self.env_timers[i] for i in range(num_envs)], dtype=np.int64)
        step_data = {
            'team_skills': team_skills,
            'agent_skills': agent_skills,
            'action_logprobs': action_logprobs,
            'values': values,
            'skill_changed': skill_changed,
            'skill_timer': skill_timers,
            'log_probs': log_probs_list,
            'env_id': np.arange(num_envs, dtype=np.int64),
        }
        if self.d2_enabled:
            # Replay metadata and ages for the D2 storage path (plan sections 6, 9).
            step_data['d2_decision'] = self._d2_last_step['decision']
            step_data['d2_team_decision'] = self._d2_last_step['team_decision']
            step_data['d2_sampled_mask'] = self._d2_last_step['sampled_mask']
            step_data['d2_sample_Z'] = self._d2_last_step['sample_Z']
            step_data['d2_order'] = self._d2_last_step['order']
            step_data['d2_agent_ages'] = self._d2_last_step['agent_ages']
            step_data['d2_team_ages'] = self._d2_last_step['team_ages']
            step_data['d2_agent_cause'] = self._d2_last_step['agent_cause']
            step_data['d2_team_cause'] = self._d2_last_step['team_cause']
        # 3. 准备info字典列表
        profile_start = time.perf_counter() if profile_enabled else 0.0
        infos_list = None
        if build_infos:
            infos_list = []
            for i in range(num_envs):
                infos_list.append({
                    'team_skill': team_skills[i],
                    'agent_skills': agent_skills[i],
                    'action_logprobs': action_logprobs[i],
                    'values': values[i],
                    'skill_changed': bool(skill_changed[i]),
                    'skill_timer': int(skill_timers[i]),
                    'log_probs': log_probs_list[i],
                    'env_id': i
                })
        if profile_enabled:
            self._step_profile['info_build'] += time.perf_counter() - profile_start

        if return_step_data:
            return actions, infos_list, step_data
        return actions, infos_list
    

    
    def store_rollout_step(self, t, state, observations, actions, rewards, dones, values, log_probs, 
                          gru_hidden_states, critic_gru_hidden_states, env_id, team_skill=None, agent_skills=None, 
                          buffer_type='discoverer', reward_components=None):
        """
        将一个时间步的所有智能体数据存储到统一rollout缓冲区
        
        ⚠️ 【重要】此函数现在只能存储低层策略数据！
        ⚠️ 高层策略数据必须通过 add_high_level_data 存储！
        
        参数:
            t: 时间步索引 (必须是连续且一致的)
            state: 全局状态 [state_dim]
            observations: 所有智能体观测 [n_agents, obs_dim]
            actions: 所有智能体动作 [n_agents, action_dim]
            rewards: 奖励数据 [n_agents] 或单个值
            dones: 完成标志 [n_agents] 或单个值
            values: 价值估计 [n_agents]
            log_probs: 对数概率 [n_agents]
            gru_hidden_states: Actor GRU隐状态 [n_agents, hidden_size]
            critic_gru_hidden_states: Critic GRU隐状态 [n_agents, hidden_size] (新增)
            env_id: 环境索引
            team_skill: 团队技能索引
            agent_skills: 个体技能索引 [n_agents]
            buffer_type: 'coordinator' 或 'discoverer' （已适配统一缓冲区）
            reward_components: 包含奖励组成的字典 (必须提供！)
        """
        if reward_components is None:
            main_logger.error(f"store_rollout_step: reward_components cannot be None. env={env_id}, t={t}")
            return False
        
        # 【修复】验证时间步索引的有效性
        if t < 0 or t >= self.rollout_buffer.num_steps:
            main_logger.error(f"时间步索引越界: t={t}, 有效范围[0, {self.rollout_buffer.num_steps-1}], env={env_id}")
            return False
        
        # 提取真实的奖励组成部分
        reward_env = reward_components.get('env', np.zeros_like(rewards, dtype=np.float32))
        reward_team_disc = reward_components.get('team_disc', np.zeros_like(rewards, dtype=np.float32))
        reward_ind_disc = reward_components.get('ind_disc', np.zeros_like(rewards, dtype=np.float32))
        reward_process = reward_components.get('process', np.zeros_like(rewards, dtype=np.float32))

        # 存储数据到统一rollout缓冲区，传递时间步索引 t 和 state
        # 增加 critic_gru_hidden_state
        profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
        success = self.rollout_buffer.add(
            t=t,
            state=state,
            obs=observations,
            action=actions,
            reward=rewards,
            done=dones,
            value=values,
            log_prob=log_probs,
            gru_hidden_state=gru_hidden_states,  # Actor hidden state
            critic_gru_hidden_state=critic_gru_hidden_states, # Critic hidden state
            env_idx=env_id,
            team_skill=team_skill,
            agent_skills=agent_skills,
            reward_env=reward_env,
            reward_team_disc=reward_team_disc,
            reward_ind_disc=reward_ind_disc,
            reward_process=reward_process,
        )
        if self.enable_runtime_profiling:
            self._add_transition_profile('rollout_buffer_write', time.perf_counter() - profile_start)
        
        # 检查存储是否成功
        if not success:
            main_logger.warning(f"低层数据存储失败，环境{env_id}，时间步: {t}")
            return False
        
        main_logger.debug(f"数据已存储到统一rollout缓冲区（{buffer_type}类型），环境{env_id}，"
                         f"时间步: {t}，奖励组成：env={np.mean(reward_env):.4f}, "
                         f"team_disc={np.mean(reward_team_disc):.4f}, ind_disc={np.mean(reward_ind_disc):.4f}")
        
        return True


    def _store_discoverer_experience(self, state, next_state, observations, next_observations, actions, rewards, dones, values, 
                                   action_logprobs, team_skill, agent_skills, env_id, rollout_step_idx=None,
                                   precomputed_reward_components=None):
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
        
        # 准备内在奖励数组。批量路径会提前完成判别器前向；单环境路径保留旧逻辑。
        if precomputed_reward_components is not None:
            intrinsic_rewards_array = np.asarray(precomputed_reward_components['intrinsic'], dtype=np.float32)
            env_rewards_array = np.asarray(precomputed_reward_components['env'], dtype=np.float32)
            team_disc_rewards_array = np.asarray(precomputed_reward_components['team_disc'], dtype=np.float32)
            ind_disc_rewards_array = np.asarray(precomputed_reward_components['ind_disc'], dtype=np.float32)
        else:
            intrinsic_rewards_array = np.zeros(n_agents, dtype=np.float32)
            env_rewards_array = np.zeros(n_agents, dtype=np.float32)
            team_disc_rewards_array = np.zeros(n_agents, dtype=np.float32)
            ind_disc_rewards_array = np.zeros(n_agents, dtype=np.float32)
        
        # 确保dones可以索引且格式正确
        # 处理 numpy bool 标量被误判为可索引对象的问题
        dones_np = np.array(dones)
        if dones_np.ndim == 0:
            dones_array = np.repeat(dones_np, n_agents)
        else:
            dones_array = dones_np

        if precomputed_reward_components is None:
            profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
            for i in range(n_agents):
                # 论文 Eq. 4 使用 s_{t+1}/o_{t+1} 计算判别器内在奖励。
                # 训练循环负责在 done 时传入 terminal_observation/terminal_state，避免使用 reset 后状态。
                idx = i if i < len(dones_array) else 0
                is_done = bool(dones_array[idx])

                calc_next_state = next_state
                calc_next_obs = next_observations[i]

                intrinsic_reward, env_comp, team_disc_comp, ind_disc_comp, _ = self._compute_intrinsic_reward(
                    calc_next_state, rewards, calc_next_obs, team_skill, agent_skills[i]
                )
                final_intrinsic_reward = intrinsic_reward
                if is_done:
                    main_logger.debug(
                        f"终止transition使用terminal s/o计算内在奖励: env={env_id}, agent={i}"
                    )

                main_logger.debug(f"Reward components for agent {i}: env={env_comp:.6f}, team_disc={team_disc_comp:.6f}, ind_disc={ind_disc_comp:.6f}")

                intrinsic_rewards_array[i] = final_intrinsic_reward

                # 存储奖励组成
                env_rewards_array[i] = env_comp
                team_disc_rewards_array[i] = team_disc_comp
                ind_disc_rewards_array[i] = ind_disc_comp

                main_logger.debug(f"Reward components stored for agent {i}: env={env_rewards_array[i]:.6f}, team_disc={team_disc_rewards_array[i]:.6f}, ind_disc={ind_disc_rewards_array[i]:.6f}")
            if self.enable_runtime_profiling:
                self._add_transition_profile('intrinsic_reward_compute', time.perf_counter() - profile_start)

        # 准备奖励组成字典
        reward_components = {
            'env': env_rewards_array,
            'team_disc': team_disc_rewards_array,
            'ind_disc': ind_disc_rewards_array,
            'process': np.zeros(n_agents, dtype=np.float32),
        }
        
        # 获取或创建环境特定的GRU隐藏状态 (Actor)
        # 【关键修复】使用 prev_hidden_states 获取当前步的输入隐状态 (t)，而非输出隐状态 (t+1)
        gru_hidden_states = self.get_prev_actor_hidden_np(env_id, n_agents=n_agents)

        # 获取或创建环境特定的GRU隐藏状态 (Critic)
        # 【关键修复】使用 prev_hidden_states 获取当前步的输入隐状态 (t)
        critic_gru_hidden_states = self.get_prev_critic_hidden_np(env_id, n_agents=n_agents)
        
        # 【修复】确保时间步索引的一致性和有效性
        if rollout_step_idx is not None:
            t = rollout_step_idx
            # 验证时间步索引的有效性
            if t < 0 or t >= self.rollout_buffer.num_steps:
                main_logger.error(f"_store_discoverer_experience: 无效的rollout_step_idx={t}, "
                                f"有效范围[0, {self.rollout_buffer.num_steps-1}], env={env_id}")
                return None
        else:
            # 【修复】不再使用模运算，而是要求明确提供时间步索引
            main_logger.error(f"_store_discoverer_experience: rollout_step_idx is required but not provided, env={env_id}")
            return None

        # 【修复】调用store_rollout_step并检查返回值
        success = self.store_rollout_step(
            t=t,
            state=state,  # 【重要修复】存储当前状态而非下一状态
            observations=observations,  # 【重要修复】存储当前观测而非下一观测
            actions=actions,
            rewards=intrinsic_rewards_array,
            dones=dones,
            values=values,
            log_probs=action_logprobs,
            gru_hidden_states=gru_hidden_states,
            critic_gru_hidden_states=critic_gru_hidden_states, # 传入 Critic Hidden State
            env_id=env_id,
            team_skill=team_skill,
            agent_skills=agent_skills,
            buffer_type='discoverer',
            reward_components=reward_components
        )
        
        if not success:
            main_logger.warning(f"_store_discoverer_experience: 数据存储失败, env={env_id}, t={t}")
            return None

        return reward_components

    def _is_new_high_level_decision(self, log_probs):
        if not isinstance(log_probs, dict) or not log_probs:
            return False
        if self.use_ha_ctse:
            return bool(log_probs.get('new_high_level_decision', False))
        return True

    def _should_close_high_level_sample(self, env_id, skill_timer, any_done, force_collection):
        if any_done or force_collection:
            return True
        if self.use_ha_ctse and self.use_discrete_skill_lifetimes:
            if skill_timer != self.config.k - 1:
                return False
            remaining = np.asarray(
                self.env_skill_duration_remaining.get(
                    env_id,
                    np.ones(self.config.n_agents, dtype=np.int64),
                ),
                dtype=np.int64,
            )
            # RolloutBuffer stores one high-level sample per environment.
            # Close before the next boundary that can renew any agent; exact
            # per-agent process lifetimes are tracked by SkillProcessSegmentBuffer.
            return bool(np.any(remaining <= 1))
        return skill_timer == self.config.k - 1

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
        if self.strict_hmasd_alignment:
            should_store_high_level = (skill_timer == self.config.k - 1)
        else:
            should_store_high_level = self._should_close_high_level_sample(
                env_id,
                skill_timer,
                any_done,
                force_collection,
            )
        
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
        
        # Use the dedicated add_high_level_data to prevent overwriting low-level rewards.
        if rollout_step_idx is None:
            main_logger.error("rollout_step_idx is None! Cannot store high-level experience correctly.")
            return False

        pending = self.env_pending_high_level.get(env_id)
        if pending is None:
            main_logger.debug(
                f"环境{env_id}在高层样本闭合点没有待闭合的技能决策样本，"
                f"rollout_step={rollout_step_idx}, skill_timer={skill_timer}，跳过"
            )
            if any_done or force_collection:
                self.env_reward_sums[env_id] = 0.0
                self.env_timers[env_id] = 0
            return False

        t = int(pending['time_step'])
        elapsed_steps = max(1, int(rollout_step_idx) - t + 1)
        close_reason_code = {
            "技能周期结束": 1,
            "环境终止": 2,
            "强制收集": 3,
        }.get(reason, 0)
        if self.use_ha_ctse:
            executed = np.asarray(
                pending.get('executed_edit_mask', np.zeros(self.config.n_agents, dtype=np.float32)),
                dtype=np.float32,
            )
            initial = np.asarray(
                pending.get('initial_assignment_mask', np.zeros(self.config.n_agents, dtype=np.float32)),
                dtype=np.float32,
            )
            active_prev = np.asarray(
                pending.get('active_skill_prev', np.full(self.config.n_agents, -1, dtype=np.int64)),
                dtype=np.int64,
            )
            active = np.asarray(
                pending.get('active_skill', np.full(self.config.n_agents, -1, dtype=np.int64)),
                dtype=np.int64,
            )
            age_prev = np.asarray(
                pending.get('skill_age_prev', np.zeros(self.config.n_agents, dtype=np.int64)),
                dtype=np.float32,
            )
            penalty_mask = (initial < 0.5).astype(np.float32)
            switch_mask = ((active != active_prev) & (active_prev >= 0)).astype(np.float32)
            horizon_scale = self._warmup_scale(getattr(self.config, 'horizon_penalty_warmup_steps', 0))
            switch_scale = self._warmup_scale(getattr(self.config, 'switch_penalty_warmup_steps', 0))
            edit_penalty = (
                horizon_scale
                * float(getattr(self.config, 'edit_penalty_alpha', 0.0))
                * float(np.sum(executed * penalty_mask))
            )
            switch_penalty = (
                switch_scale
                * float(getattr(self.config, 'switch_penalty_beta', 0.0))
                * float(np.sum(switch_mask * penalty_mask))
            )
            early_coef = float(getattr(self.config, 'early_switch_penalty_eta', 0.0))
            age_power = float(getattr(self.config, 'age_penalty_power', 1.0))
            early_penalty = horizon_scale * early_coef * float(
                np.sum((executed * penalty_mask) / np.power(age_prev + 1.0, age_power))
            )
            env_accumulated_reward = env_accumulated_reward - edit_penalty - switch_penalty - early_penalty
        
        # 【修复】调用add_high_level_data并传递分离的log_probs和values
        # 不再计算和存储联合log_prob，以支持解耦的策略损失
        success = self.rollout_buffer.add_high_level_data(
            env_idx=env_id,
            time_step=t,
            state_value=pending.get('state_value', 0.0),
            agent_values=pending.get('agent_values', np.zeros(self.config.n_agents, dtype=np.float32)),
            team_log_prob=pending.get('team_log_prob', 0.0),
            agent_log_probs=pending.get('agent_log_probs', [0.0] * self.config.n_agents),
            accumulated_reward=env_accumulated_reward,
            value=pending.get('state_value', 0.0),
            elapsed_steps=elapsed_steps,
            terminal=any_done,
            close_reason_code=close_reason_code,
            compact=pending.get('compact'),
            team_code=pending.get('team_code', -1),
            log_prob_team_code=pending.get('log_prob_team_code', 0.0),
            entropy_team_code=pending.get('entropy_team_code', 0.0),
            opt_aggregation_entropy=pending.get('opt_aggregation_entropy', 0.0),
            active_skill_prev=pending.get('active_skill_prev'),
            active_skill=pending.get('active_skill'),
            candidate_skill=pending.get('candidate_skill'),
            skill_age_prev=pending.get('skill_age_prev'),
            skill_age=pending.get('skill_age'),
            duration_candidate=pending.get('duration_candidate'),
            duration_target=pending.get('duration_target'),
            duration_remaining=pending.get('duration_remaining'),
            requested_edit_mask=pending.get('requested_edit_mask'),
            executed_edit_mask=pending.get('executed_edit_mask'),
            log_prob_term=pending.get('log_prob_term'),
            log_prob_skill=pending.get('log_prob_skill'),
            log_prob_duration=pending.get('log_prob_duration'),
            entropy_term=pending.get('entropy_term'),
            entropy_skill=pending.get('entropy_skill'),
            entropy_duration=pending.get('entropy_duration'),
            initial_assignment_mask=pending.get('initial_assignment_mask'),
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
        self.env_pending_high_level.pop(env_id, None)
        
        # 重置该环境的奖励累积和计时器 (这部分逻辑保持不变)
        self.env_reward_sums[env_id] = 0.0
        self.env_timers[env_id] = 0
        
        return True

    def _store_discriminator_data(self, next_state, team_skill, next_observations, agent_skills):
        """
        将状态-技能对存储到当前rollout的判别器缓存中。
        
        【归一化修复】确保存储到判别器Buffer的数据与策略网络使用相同的归一化，
        解决"归一化地狱"问题。
        """
        # 【关键修复】归一化状态和观测，确保与策略网络输入一致
        # 【重要】update=False，防止重复更新 RunningMeanStd
        normalized_state = self._normalize_states(next_state, update=False)
        normalized_observations = self._normalize_observations(next_observations, update=False)
        compact_np = None
        if self.use_compact_team_discriminator or self.use_compact_individual_discriminator:
            with torch.no_grad():
                state_tensor = torch.as_tensor(normalized_state, dtype=torch.float32, device=self.device).unsqueeze(0)
                obs_tensor = torch.as_tensor(normalized_observations, dtype=torch.float32, device=self.device).unsqueeze(0)
                compact_np = self._compute_ha_discriminator_compact_tensor(state_tensor, obs_tensor)
                compact_np = compact_np.squeeze(0).detach().cpu().numpy().astype(np.float32, copy=False)
        
        # 存储团队技能数据（使用归一化状态）
        team_experience = {'type': 'team', 'state': normalized_state, 'skill': team_skill}
        if compact_np is not None:
            team_experience['compact'] = compact_np
        self.discriminator_buffer.push(team_experience)
        
        # 存储每个智能体的个体技能数据（使用归一化观测）
        for i in range(self.config.n_agents):
            ind_experience = {
                'type': 'individual',
                'obs': normalized_observations[i],  # 归一化后的观测
                'team_skill': team_skill,  # 个体技能判别器需要团队技能作为条件
                'skill': agent_skills[i]
            }
            if compact_np is not None:
                ind_experience['compact'] = compact_np
            self.discriminator_buffer.push(ind_experience)

    def _store_discriminator_data_batch(self, normalized_states, team_skills, normalized_observations, agent_skills):
        """
        批量存储判别器训练数据。输入必须已经归一化，避免与批量内在奖励路径重复归一化。
        """
        normalized_states = np.asarray(normalized_states, dtype=np.float32)
        normalized_observations = np.asarray(normalized_observations, dtype=np.float32)
        team_skills = np.asarray(team_skills, dtype=np.int64)
        agent_skills = np.asarray(agent_skills, dtype=np.int64)

        if normalized_states.ndim == 1:
            normalized_states = normalized_states[None, :]
        if normalized_observations.ndim == 2:
            normalized_observations = normalized_observations[None, :, :]

        num_envs = normalized_states.shape[0]
        n_agents = normalized_observations.shape[1]
        team_skills = team_skills.reshape(num_envs)
        agent_skills = agent_skills.reshape(num_envs, n_agents)
        compact_np = None
        if self.use_compact_team_discriminator or self.use_compact_individual_discriminator:
            with torch.no_grad():
                compact_tensor = self._compute_ha_discriminator_compact_tensor(
                    torch.as_tensor(normalized_states, dtype=torch.float32, device=self.device),
                    torch.as_tensor(normalized_observations, dtype=torch.float32, device=self.device),
                )
                if compact_tensor is not None:
                    compact_np = compact_tensor.detach().cpu().numpy().astype(np.float32, copy=False)

        experiences = []
        for env_idx in range(num_envs):
            team_experience = {
                'type': 'team',
                'state': normalized_states[env_idx],
                'skill': int(team_skills[env_idx])
            }
            if compact_np is not None:
                team_experience['compact'] = compact_np[env_idx]
            experiences.append(team_experience)
            for agent_idx in range(n_agents):
                ind_experience = {
                    'type': 'individual',
                    'obs': normalized_observations[env_idx, agent_idx],
                    'team_skill': int(team_skills[env_idx]),
                    'skill': int(agent_skills[env_idx, agent_idx])
                }
                if compact_np is not None:
                    ind_experience['compact'] = compact_np[env_idx]
                experiences.append(ind_experience)

        self.discriminator_buffer.extend(experiences)

    def store_transition(self, state, next_state, observations, next_observations, 
                         actions, rewards, dones, team_skill, agent_skills, action_logprobs, log_probs=None, 
                         skill_timer_for_env=None, env_id=0, values=None, rollout_step_idx=None,
                         reward_info=None, _precomputed_reward_components=None, _skip_discriminator_store=False,
                         d2_step=None):
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
        if self.enable_runtime_profiling:
            self._transition_profile['store_calls'] += 1

        # 确保rewards是数值类型 (更稳健的处理)
        if isinstance(rewards, np.ndarray):
            current_reward = np.mean(rewards) # 如果是数组，取平均值（因为是共享奖励）
        else:
            current_reward = rewards # 如果是标量，直接使用
        
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
            action_logprobs, team_skill, agent_skills, env_id, rollout_step_idx,
            precomputed_reward_components=_precomputed_reward_components
        )
        self._append_process_segment_transitions(
            env_id,
            observations,
            next_observations,
            actions,
            rewards,
            dones,
            rollout_step_idx=rollout_step_idx,
            reward_info=reward_info,
        )
        
        # 新增：将 (下一状态, 技能) 对存储到判别器Buffer
        # 根据论文，我们使用 t+1 时刻的状态/观测
        if (not _skip_discriminator_store) and not getattr(self.config, 'disable_discriminator_training', False):
            profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
            self._store_discriminator_data(next_state, team_skill, next_observations, agent_skills)
            if self.enable_runtime_profiling:
                self._add_transition_profile('discriminator_buffer_write', time.perf_counter() - profile_start)

        # 论文对齐：高层PPO样本的 old log_prob/value 必须固定在技能决策时刻。
        # In HA-CTSE process mode, a k-boundary can be only a check boundary
        # without a new high-level action. Keep the existing pending sample
        # open across such boundaries.
        profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
        if self.d2_enabled:
            # D2 owns its own segment tables; the `off` pending/close mechanism
            # (which assumes one global k-boundary per env) is bypassed entirely.
            if d2_step is None:
                d2_step = self.env_d2_last_decision.get(env_id)
            if d2_step is None:
                main_logger.error(f"D2 storage: no decision metadata for env {env_id}")
            else:
                self._d2_store_transition(
                    env_id, rollout_step_idx, current_reward, dones, d2_step
                )
            if self.enable_runtime_profiling:
                self._add_transition_profile('high_level_bookkeeping', time.perf_counter() - profile_start)
            return returned_reward_components
        if (
            rollout_step_idx is not None
            and skill_timer_for_env == 0
            and log_probs
            and self._is_new_high_level_decision(log_probs)
        ):
            if 'state_value' in log_probs and 'agent_values' in log_probs:
                pending_sample = {
                    'time_step': int(rollout_step_idx),
                    'team_skill': int(team_skill),
                    'agent_skills': np.asarray(agent_skills, dtype=np.int64),
                    'team_log_prob': float(log_probs.get('team_log_prob', 0.0)),
                    'agent_log_probs': np.asarray(
                        log_probs.get('agent_log_probs', [0.0] * self.config.n_agents),
                        dtype=np.float32
                    ),
                    'state_value': float(log_probs.get('state_value', 0.0)),
                    'agent_values': np.asarray(log_probs.get('agent_values'), dtype=np.float32),
                }
                for key in (
                    'compact',
                    'team_code',
                    'log_prob_team_code',
                    'entropy_team_code',
                    'opt_aggregation_entropy',
                    'active_skill_prev',
                    'active_skill',
                    'candidate_skill',
                    'skill_age_prev',
                    'skill_age',
                    'duration_candidate',
                    'duration_target',
                    'duration_remaining',
                    'requested_edit_mask',
                    'executed_edit_mask',
                    'log_prob_term',
                    'log_prob_skill',
                    'log_prob_duration',
                    'entropy_term',
                    'entropy_skill',
                    'entropy_duration',
                    'initial_assignment_mask',
                ):
                    if key in log_probs:
                        pending_sample[key] = log_probs[key]
                self.env_pending_high_level[env_id] = pending_sample
            else:
                main_logger.warning(
                    f"环境{env_id}在技能决策步缺少高层value字段，无法创建严格对齐的高层pending样本"
                )
        
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
        force_collection = (
            False
            if self._uses_process_high_level_flow()
            else self.force_high_level_collection.get(env_id, False)
        )
        
        # 对长时间未贡献的环境强制收集
        force_collection_threshold = getattr(self.config, 'force_collection_threshold', 10**12)
        if (
            self._should_use_legacy_high_level_contribution_monitor()
            and (not self.strict_hmasd_alignment)
            and steps_since_contribution > force_collection_threshold
        ):
            self.force_high_level_collection[env_id] = True
            if steps_since_contribution % force_collection_threshold == 0:  # 避免日志过多
                main_logger.info(f"环境ID={env_id}已{steps_since_contribution}步未贡献高层样本，将强制收集")
        
        # 存储高层策略经验（如果满足条件）
        # 【注意】高层策略数据继续使用当前状态和观测，这是正确的
        if not getattr(self.config, 'disable_high_level_training', False):
            self._store_coordinator_experience(
                state, observations, env_id, team_skill, agent_skills, 
                log_probs, dones, skill_timer, steps_since_contribution, force_collection,
                rollout_step_idx=rollout_step_idx
            )
        if self.enable_runtime_profiling:
            self._add_transition_profile('high_level_bookkeeping', time.perf_counter() - profile_start)
        
        # 返回奖励组成部分给训练循环
        return returned_reward_components

    def store_transition_batch(self, states, next_states, observations, next_observations,
                               actions, rewards, dones, infos_batch=None, rollout_step_idx=None,
                               step_data=None):
        """
        Batch facade for storing one vectorized environment step.

        The rollout buffer still stores per-environment entries, but keeping this
        loop inside the agent gives collectors a single stable call surface.
        """
        reward_components = []
        num_envs = len(rewards)

        if step_data is not None:
            team_skills = np.asarray(step_data['team_skills'], dtype=np.int64)
            agent_skills_batch = np.asarray(step_data['agent_skills'], dtype=np.int64)
            action_logprobs_batch = np.asarray(step_data['action_logprobs'], dtype=np.float32)
            values_batch = np.asarray(step_data['values'], dtype=np.float32)
            log_probs_batch = step_data['log_probs']
            skill_timers = np.asarray(step_data['skill_timer'], dtype=np.int64)
        else:
            if infos_batch is None:
                raise ValueError("store_transition_batch requires infos_batch or step_data")
            team_skills = np.asarray([info['team_skill'] for info in infos_batch], dtype=np.int64)
            agent_skills_batch = np.asarray([info['agent_skills'] for info in infos_batch], dtype=np.int64)
            action_logprobs_batch = np.asarray([info['action_logprobs'] for info in infos_batch], dtype=np.float32)
            values_batch = np.asarray([info['values'] for info in infos_batch], dtype=np.float32)
            log_probs_batch = [info['log_probs'] for info in infos_batch]
            skill_timers = np.asarray([info['skill_timer'] for info in infos_batch], dtype=np.int64)

        d2_steps = None
        if self.d2_enabled:
            if step_data is not None and 'd2_sampled_mask' in step_data:
                d2_steps = [
                    {
                        'decision': bool(step_data['d2_decision'][env_id]),
                        'team_decision': bool(step_data['d2_team_decision'][env_id]),
                        'sampled_mask': np.asarray(step_data['d2_sampled_mask'][env_id], dtype=np.bool_),
                        'sample_Z': bool(step_data['d2_sample_Z'][env_id]),
                        'order': np.asarray(step_data['d2_order'][env_id], dtype=np.int64),
                        'agent_ages': np.asarray(step_data['d2_agent_ages'][env_id], dtype=np.int64),
                        'team_age': int(step_data['d2_team_ages'][env_id]),
                        'agent_cause': np.asarray(step_data['d2_agent_cause'][env_id], dtype=np.int64),
                        'team_cause': int(step_data['d2_team_cause'][env_id]),
                    }
                    for env_id in range(num_envs)
                ]
            else:
                d2_steps = [self.env_d2_last_decision.get(env_id) for env_id in range(num_envs)]

        intrinsic_batch = self._compute_intrinsic_rewards_batch(
            next_states=next_states,
            rewards=rewards,
            next_observations=next_observations,
            team_skills=team_skills,
            agent_skills=agent_skills_batch
        )

        if not getattr(self.config, 'disable_discriminator_training', False):
            profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
            self._store_discriminator_data_batch(
                intrinsic_batch['normalized_states'],
                team_skills,
                intrinsic_batch['normalized_observations'],
                agent_skills_batch
            )
            if self.enable_runtime_profiling:
                self._add_transition_profile('discriminator_buffer_write', time.perf_counter() - profile_start)

        for env_id in range(num_envs):
            reward_info = {}
            if infos_batch is not None and env_id < len(infos_batch):
                reward_info = self._extract_reward_info(infos_batch[env_id])
            env_reward_components = {
                'intrinsic': intrinsic_batch['intrinsic'][env_id],
                'env': intrinsic_batch['env'][env_id],
                'team_disc': intrinsic_batch['team_disc'][env_id],
                'ind_disc': intrinsic_batch['ind_disc'][env_id],
            }
            reward_components.append(
                self.store_transition(
                    state=states[env_id],
                    next_state=next_states[env_id],
                    observations=observations[env_id],
                    next_observations=next_observations[env_id],
                    actions=actions[env_id],
                    rewards=rewards[env_id],
                    dones=dones[env_id],
                    team_skill=team_skills[env_id],
                    agent_skills=agent_skills_batch[env_id],
                    action_logprobs=action_logprobs_batch[env_id],
                    values=values_batch[env_id],
                    log_probs=log_probs_batch[env_id],
                    skill_timer_for_env=int(skill_timers[env_id]),
                    env_id=env_id,
                    rollout_step_idx=rollout_step_idx,
                    reward_info=reward_info,
                    _precomputed_reward_components=env_reward_components,
                    _skip_discriminator_store=True,
                    d2_step=(d2_steps[env_id] if d2_steps is not None else None),
                )
            )
        return reward_components
    
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

    def _format_reward_matrix(self, rewards, num_envs, n_agents):
        reward_np = np.asarray(rewards, dtype=np.float32)

        if reward_np.ndim == 0:
            return np.full((num_envs, n_agents), float(reward_np), dtype=np.float32)

        if reward_np.ndim == 1:
            if reward_np.shape[0] == num_envs:
                return np.repeat(reward_np[:, None], n_agents, axis=1).astype(np.float32, copy=False)
            if num_envs == 1 and reward_np.shape[0] == n_agents:
                return reward_np.reshape(1, n_agents).astype(np.float32, copy=False)
            raise ValueError(
                f"rewards shape {reward_np.shape} cannot be broadcast to ({num_envs}, {n_agents})"
            )

        if reward_np.ndim == 2:
            if reward_np.shape == (num_envs, n_agents):
                return reward_np.astype(np.float32, copy=False)
            if reward_np.shape == (num_envs, 1):
                return np.repeat(reward_np, n_agents, axis=1).astype(np.float32, copy=False)
            raise ValueError(
                f"rewards shape {reward_np.shape} cannot be broadcast to ({num_envs}, {n_agents})"
            )

        raise ValueError(f"Unsupported rewards ndim={reward_np.ndim}")

    def _empty_intrinsic_batch_result(self, next_states, next_observations, reward_matrix):
        env_component = self.config.lambda_e * reward_matrix if hasattr(self.config, 'lambda_e') else reward_matrix
        zeros = np.zeros_like(env_component, dtype=np.float32)
        return {
            'intrinsic': env_component.astype(np.float32, copy=False),
            'env': env_component.astype(np.float32, copy=False),
            'team_disc': zeros.copy(),
            'ind_disc': zeros.copy(),
            'uncertainty': zeros.copy(),
            'normalized_states': np.asarray(next_states, dtype=np.float32),
            'normalized_observations': np.asarray(next_observations, dtype=np.float32),
        }

    def _zero_compact_tensor(self, batch_size):
        compact_dim = int(getattr(self.config, 'opt_compact_dim', getattr(self.config, 'embedding_dim', 128)))
        return torch.zeros(batch_size, compact_dim, dtype=torch.float32, device=self.device)

    def _compute_ha_discriminator_compact_tensor(self, states_tensor, observations_tensor):
        if not (self.use_compact_team_discriminator or self.use_compact_individual_discriminator):
            return None
        if self.ha_ctse_editor is None:
            return self._zero_compact_tensor(states_tensor.shape[0])
        compact, _, _, _, _ = self.ha_ctse_editor.compact_extractor(states_tensor, observations_tensor)
        return compact

    def _compute_low_level_compact_context(self, states_tensor, joint_observations_tensor):
        if self.low_level_compact_extractor is None:
            return None
        compact, _, _, _, _ = self.low_level_compact_extractor(states_tensor, joint_observations_tensor)
        return compact

    def _team_discriminator_logits(self, states_tensor, compact_tensor=None):
        if self.use_compact_team_discriminator:
            if compact_tensor is None:
                compact_tensor = self._zero_compact_tensor(states_tensor.shape[0])
            return self.team_discriminator(states_tensor, compact_tensor)
        return self.team_discriminator(states_tensor)

    def _individual_discriminator_logits(self, obs_tensor, team_skill_tensor, compact_tensor=None):
        if team_skill_tensor.dim() == 0:
            team_skill_tensor = team_skill_tensor.unsqueeze(0)
        if self.use_compact_individual_discriminator:
            if compact_tensor is None:
                compact_tensor = self._zero_compact_tensor(obs_tensor.shape[0])
            return self.individual_discriminator(obs_tensor, team_skill_tensor, compact_tensor)
        return self.individual_discriminator(obs_tensor, team_skill_tensor)

    def _compute_intrinsic_rewards_batch(self, next_states, rewards, next_observations, team_skills, agent_skills):
        """
        Vectorized discriminator reward computation for one VecEnv step.

        Returns reward component arrays with shape [num_envs, n_agents] and the
        normalized next state/observation arrays used by the discriminator path.
        """
        total_start = time.perf_counter() if self.enable_runtime_profiling else 0.0

        next_states_np = np.asarray(next_states, dtype=np.float32)
        next_observations_np = np.asarray(next_observations, dtype=np.float32)
        if next_states_np.ndim == 1:
            next_states_np = next_states_np[None, :]
        if next_observations_np.ndim == 2:
            next_observations_np = next_observations_np[None, :, :]

        num_envs = next_states_np.shape[0]
        n_agents = next_observations_np.shape[1]
        reward_matrix = self._format_reward_matrix(rewards, num_envs, n_agents)

        team_skills_np = np.asarray(team_skills, dtype=np.int64).reshape(num_envs)
        agent_skills_np = np.asarray(agent_skills, dtype=np.int64).reshape(num_envs, n_agents)

        normalized_states = next_states_np
        normalized_observations = next_observations_np

        try:
            normalize_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
            normalized_states = np.asarray(self._normalize_states(next_states_np, update=False), dtype=np.float32)
            normalized_observations = np.asarray(
                self._normalize_observations(next_observations_np, update=False),
                dtype=np.float32
            )
            if self.enable_runtime_profiling:
                self._add_transition_profile('intrinsic_normalize', time.perf_counter() - normalize_start)

            if getattr(self.config, 'disable_discriminator_rewards', False):
                result = self._empty_intrinsic_batch_result(
                    normalized_states, normalized_observations, reward_matrix
                )
                result['normalized_states'] = normalized_states
                result['normalized_observations'] = normalized_observations
                return result

            with torch.no_grad():
                state_tensor = torch.as_tensor(normalized_states, dtype=torch.float32, device=self.device)
                state_tensor = self.numerical_stabilizer.check_and_fix_tensor(
                    state_tensor, "next_state_tensor_batch"
                )
                joint_obs_tensor = torch.as_tensor(normalized_observations, dtype=torch.float32, device=self.device)
                compact_tensor = self._compute_ha_discriminator_compact_tensor(state_tensor, joint_obs_tensor)

                self._sync_cuda_for_profile()
                team_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
                team_disc_logits = self._team_discriminator_logits(state_tensor, compact_tensor)
                team_disc_logits = self.numerical_stabilizer.check_and_fix_tensor(
                    team_disc_logits, "team_disc_logits_batch"
                )
                team_disc_log_probs = F.log_softmax(team_disc_logits, dim=-1)
                team_log_probs_np = team_disc_log_probs.detach().cpu().numpy()
                self._sync_cuda_for_profile()
                if self.enable_runtime_profiling:
                    self._add_transition_profile('intrinsic_team_forward', time.perf_counter() - team_start)

                flat_obs = normalized_observations.reshape(num_envs * n_agents, -1)
                flat_team_skills = np.repeat(team_skills_np, n_agents)
                obs_tensor = torch.as_tensor(flat_obs, dtype=torch.float32, device=self.device)
                obs_tensor = self.numerical_stabilizer.check_and_fix_tensor(
                    obs_tensor, "agent_obs_tensor_batch"
                )
                team_skill_tensor = torch.as_tensor(flat_team_skills, dtype=torch.long, device=self.device)
                flat_compact_tensor = None
                if compact_tensor is not None:
                    flat_compact_tensor = compact_tensor.unsqueeze(1).expand(-1, n_agents, -1).reshape(
                        num_envs * n_agents,
                        -1,
                    )

                self._sync_cuda_for_profile()
                ind_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
                agent_disc_logits = self._individual_discriminator_logits(
                    obs_tensor,
                    team_skill_tensor,
                    flat_compact_tensor,
                )
                agent_disc_logits = self.numerical_stabilizer.check_and_fix_tensor(
                    agent_disc_logits, "agent_disc_logits_batch"
                )
                agent_disc_log_probs = F.log_softmax(agent_disc_logits, dim=-1)
                agent_log_probs_np = agent_disc_log_probs.detach().cpu().numpy()
                self._sync_cuda_for_profile()
                if self.enable_runtime_profiling:
                    self._add_transition_profile('intrinsic_ind_forward', time.perf_counter() - ind_start)

            post_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
            env_indices = np.arange(num_envs)
            team_log_prob_env = team_log_probs_np[env_indices, team_skills_np]
            team_mutual_info_env = self._discriminator_mi_reward(
                team_log_prob_env,
                team_log_probs_np.shape[-1],
            )
            team_mutual_info = np.repeat(team_mutual_info_env[:, None], n_agents, axis=1)

            flat_agent_skills = agent_skills_np.reshape(-1)
            flat_indices = np.arange(num_envs * n_agents)
            ind_log_prob = agent_log_probs_np[flat_indices, flat_agent_skills]
            ind_mutual_info = self._discriminator_mi_reward(
                ind_log_prob,
                agent_log_probs_np.shape[-1],
            ).reshape(num_envs, n_agents)

            if not hasattr(self, 'team_disc_baseline'):
                self.team_disc_baseline = 0.0
                self.ind_disc_baseline = 0.0
                self.baseline_update_rate = 0.01

            for env_idx in range(num_envs):
                for agent_idx in range(n_agents):
                    self.team_disc_baseline = (
                        (1 - self.baseline_update_rate) * self.team_disc_baseline
                        + self.baseline_update_rate * float(team_mutual_info[env_idx, agent_idx])
                    )
                    self.ind_disc_baseline = (
                        (1 - self.baseline_update_rate) * self.ind_disc_baseline
                        + self.baseline_update_rate * float(ind_mutual_info[env_idx, agent_idx])
                    )

            uncertainty = np.zeros((num_envs, n_agents), dtype=np.float32)
            if getattr(self.config, 'enhanced_state', False) and getattr(self.config, 'w_entropy', 0) > 0:
                dims = self.config.state_component_dims
                start_idx = dims['current_state_dim'] + dims['predicted_state_dim']
                uncertainty_env = np.zeros(num_envs, dtype=np.float32)
                for env_idx in range(num_envs):
                    uncertainty_map_flat = next_states_np[env_idx, start_idx:]
                    avg_entropy = np.mean(uncertainty_map_flat) if uncertainty_map_flat.size > 0 else 0.0
                    uncertainty_env[env_idx] = -self.config.w_entropy * avg_entropy
                uncertainty = np.repeat(uncertainty_env[:, None], n_agents, axis=1)

            team_disc_reward_clipped = team_mutual_info
            ind_disc_reward_clipped = ind_mutual_info
            env_component = self.config.lambda_e * reward_matrix
            legacy_mi_coef = float(getattr(self.config, 'legacy_mi_reward_coef', 1.0))
            team_disc_component = legacy_mi_coef * self.config.lambda_D * team_disc_reward_clipped
            ind_disc_component = legacy_mi_coef * self.config.lambda_d * ind_disc_reward_clipped
            intrinsic_reward = env_component + team_disc_component + ind_disc_component + uncertainty

            bad_team = ~np.isfinite(team_disc_component)
            if np.any(bad_team):
                team_disc_component[bad_team] = 0.0
            bad_ind = ~np.isfinite(ind_disc_component)
            if np.any(bad_ind):
                ind_disc_component[bad_ind] = 0.0
            bad_uncertainty = ~np.isfinite(uncertainty)
            if np.any(bad_uncertainty):
                uncertainty[bad_uncertainty] = 0.0
            bad_intrinsic = ~np.isfinite(intrinsic_reward)
            if np.any(bad_intrinsic):
                intrinsic_reward[bad_intrinsic] = env_component[bad_intrinsic]
                team_disc_component[bad_intrinsic] = 0.0
                ind_disc_component[bad_intrinsic] = 0.0
                uncertainty[bad_intrinsic] = 0.0

            if self.enable_runtime_profiling:
                self._add_transition_profile('intrinsic_postprocess', time.perf_counter() - post_start)

            return {
                'intrinsic': intrinsic_reward.astype(np.float32, copy=False),
                'env': env_component.astype(np.float32, copy=False),
                'team_disc': team_disc_component.astype(np.float32, copy=False),
                'ind_disc': ind_disc_component.astype(np.float32, copy=False),
                'uncertainty': uncertainty.astype(np.float32, copy=False),
                'normalized_states': normalized_states,
                'normalized_observations': normalized_observations,
            }

        except Exception as e:
            main_logger.error(f"Error in batched intrinsic reward computation: {e}")
            return self._empty_intrinsic_batch_result(normalized_states, normalized_observations, reward_matrix)
        finally:
            if self.enable_runtime_profiling:
                self._add_transition_profile('intrinsic_reward_compute', time.perf_counter() - total_start)

    def compute_adaptive_advantage_normalization(self, advantages, sparse_reward_threshold=0.01):
        """
        自适应优势标准化：根据奖励稀疏程度调整标准化强度
        
        参数:
            advantages: 优势值张量
            sparse_reward_threshold: 判断稀疏奖励的阈值
            
        返回:
            normalized_advantages: 标准化后的优势值
        """
        # 计算非零优势的比例（作为奖励稀疏度的代理指标）
        non_zero_ratio = (advantages.abs() > sparse_reward_threshold).float().mean()
        
        if non_zero_ratio < 0.1:  # 非常稀疏的奖励
            # 使用更温和的标准化或不标准化
            if advantages.std() > 1e-8:
                # 只进行部分标准化，保留更多原始信号
                normalization_strength = 0.1  # 10%的标准化强度
                mean = advantages.mean()
                std = advantages.std()
                normalized = (advantages - mean) / (std + 1e-8)
                advantages = advantages * (1 - normalization_strength) + normalized * normalization_strength
                main_logger.debug(f"使用轻度优势标准化 (稀疏度: {non_zero_ratio:.3f}, 强度: {normalization_strength})")
        elif non_zero_ratio < 0.3:  # 中等稀疏
            # 使用软标准化
            if advantages.std() > 1e-8:
                # 使用更大的epsilon避免过度放大小信号
                advantages = (advantages - advantages.mean()) / (advantages.std() + 0.1)
                main_logger.debug(f"使用软优势标准化 (稀疏度: {non_zero_ratio:.3f})")
        else:  # 密集奖励
            # 使用标准的优势标准化
            if advantages.std() > 1e-8:
                advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
                main_logger.debug(f"使用标准优势标准化 (稀疏度: {non_zero_ratio:.3f})")
        
        # 裁剪极值，避免数值问题
        advantages = torch.clamp(advantages, -10, 10)
        
        return advantages

    def _compute_high_level_bootstrap_values(self, num_steps):
        """
        【GAE引导价值修复】计算高层策略的bootstrap values
        
        从rollout buffer的最后有效数据计算更准确的引导价值，
        而不是简单假设last_value为0，这将显著减少GAE估计的偏差。
        
        参数:
            num_steps: 当前rollout中的有效步数
            
        返回:
            high_level_last_values: 包含state和agents价值的字典
        """
        try:
            # 获取rollout数据
            rollout_data = self.rollout_buffer._get_full_rollout_data()
            if rollout_data is None:
                main_logger.warning("无法获取rollout数据，使用零值作为bootstrap")
                return {
                    'state': np.zeros(self.rollout_buffer.num_envs),
                    'agents': np.zeros((self.rollout_buffer.num_envs, self.config.n_agents))
                }
            
            # 寻找每个环境的最后有效状态和观测
            last_states = np.zeros((self.rollout_buffer.num_envs, self.config.state_dim))
            last_observations = np.zeros((self.rollout_buffer.num_envs, self.config.n_agents, self.config.obs_dim))
            found_last_data = np.zeros(self.rollout_buffer.num_envs, dtype=bool)
            
            # 从后往前搜索每个环境的最后有效数据
            for env_idx in range(self.rollout_buffer.num_envs):
                for t in range(num_steps - 1, -1, -1):  # 从最新到最旧
                    if t < rollout_data["states"].shape[0] and env_idx < rollout_data["states"].shape[1]:
                        # 检查是否有有效的状态数据
                        state_data = rollout_data["states"][t, env_idx]
                        obs_data = rollout_data["obs"][t, env_idx]
                        
                        # 简单的有效性检查：非全零且非NaN
                        if not np.all(state_data == 0) and not np.isnan(state_data).any():
                            last_states[env_idx] = state_data
                            last_observations[env_idx] = obs_data
                            found_last_data[env_idx] = True
                            break
            
            # 使用找到的最后状态计算bootstrap values
            bootstrap_state_values = np.zeros(self.rollout_buffer.num_envs)
            bootstrap_agent_values = np.zeros((self.rollout_buffer.num_envs, self.config.n_agents))
            
            # 批量计算有效环境的价值
            valid_env_indices = np.where(found_last_data)[0]
            if len(valid_env_indices) > 0:
                # 提取有效环境的状态和观测
                valid_states = last_states[valid_env_indices]
                valid_observations = last_observations[valid_env_indices]
                
                # 应用状态和观测标准化
                valid_states_normalized = self._normalize_states(valid_states)
                valid_observations_normalized = self._normalize_observations(valid_observations)
                
                # 转换为tensors
                states_tensor = torch.FloatTensor(valid_states_normalized).to(self.device)
                observations_tensor = torch.FloatTensor(valid_observations_normalized).to(self.device)
                
                with torch.no_grad():
                    # 使用skill coordinator计算价值
                    state_values, agent_values_list, _ = self.skill_coordinator.get_value(
                        states_tensor, observations_tensor
                    )
                    
                    # 提取价值
                    if state_values is not None:
                        bootstrap_state_values[valid_env_indices] = state_values.cpu().numpy().flatten()
                    
                    if agent_values_list is not None and len(agent_values_list) > 0:
                        # 将agent values列表转换为numpy数组
                        for i, agent_value in enumerate(agent_values_list):
                            if i < self.config.n_agents:
                                agent_vals = agent_value.cpu().numpy().flatten()
                                if len(agent_vals) == len(valid_env_indices):
                                    bootstrap_agent_values[valid_env_indices, i] = agent_vals
                
                main_logger.info(f"成功为{len(valid_env_indices)}个环境计算bootstrap values, "
                               f"状态价值范围: [{bootstrap_state_values.min():.4f}, {bootstrap_state_values.max():.4f}], "
                               f"智能体价值范围: [{bootstrap_agent_values.min():.4f}, {bootstrap_agent_values.max():.4f}]")
            else:
                main_logger.warning("未找到任何有效的最后状态数据，使用零值作为bootstrap")
            
            return {
                'state': bootstrap_state_values,
                'agents': bootstrap_agent_values
            }
            
        except Exception as e:
            main_logger.error(f"计算bootstrap values时发生错误: {e}")
            main_logger.warning("使用零值作为fallback bootstrap values")
            return {
                'state': np.zeros(self.rollout_buffer.num_envs),
                'agents': np.zeros((self.rollout_buffer.num_envs, self.config.n_agents))
            }

    def _compute_high_level_bootstrap_values_ha_ctse(self, num_steps):
        try:
            rollout_data = self.rollout_buffer._get_full_rollout_data()
            if rollout_data is None:
                return {
                    'state': np.zeros(self.rollout_buffer.num_envs),
                    'agents': np.zeros((self.rollout_buffer.num_envs, self.config.n_agents))
                }

            last_states = np.zeros((self.rollout_buffer.num_envs, self.config.state_dim), dtype=np.float32)
            last_observations = np.zeros((self.rollout_buffer.num_envs, self.config.n_agents, self.config.obs_dim), dtype=np.float32)
            found_last_data = np.zeros(self.rollout_buffer.num_envs, dtype=bool)

            for env_idx in range(self.rollout_buffer.num_envs):
                for t in range(num_steps - 1, -1, -1):
                    if t < rollout_data["states"].shape[0] and env_idx < rollout_data["states"].shape[1]:
                        state_data = rollout_data["states"][t, env_idx]
                        obs_data = rollout_data["obs"][t, env_idx]
                        if not np.all(state_data == 0) and not np.isnan(state_data).any():
                            last_states[env_idx] = state_data
                            last_observations[env_idx] = obs_data
                            found_last_data[env_idx] = True
                            break

            bootstrap_state_values = np.zeros(self.rollout_buffer.num_envs)
            bootstrap_agent_values = np.zeros((self.rollout_buffer.num_envs, self.config.n_agents))
            valid_env_indices = np.where(found_last_data)[0]
            if len(valid_env_indices) == 0:
                return {'state': bootstrap_state_values, 'agents': bootstrap_agent_values}

            prev_skills_np = np.asarray(
                [self.env_agent_skills.get(int(env_idx), np.zeros(self.config.n_agents, dtype=np.int64))
                 for env_idx in valid_env_indices],
                dtype=np.int64,
            )
            ages_np = np.asarray(
                [self.env_skill_ages.get(int(env_idx), np.zeros(self.config.n_agents, dtype=np.int64))
                 for env_idx in valid_env_indices],
                dtype=np.int64,
            )
            initial_np = prev_skills_np < 0

            with torch.no_grad():
                result = self.ha_ctse_editor.assign_and_value_batch(
                    torch.as_tensor(self._normalize_states(last_states[valid_env_indices]), dtype=torch.float32, device=self.device),
                    torch.as_tensor(self._normalize_observations(last_observations[valid_env_indices]), dtype=torch.float32, device=self.device),
                    torch.as_tensor(prev_skills_np, dtype=torch.long, device=self.device),
                    torch.as_tensor(ages_np, dtype=torch.long, device=self.device),
                    torch.as_tensor(initial_np, dtype=torch.bool, device=self.device),
                    deterministic=True,
                )
                state_values = result['state_values']
                agent_values = result['agent_values']
                if self.config.use_valuenorm and self.value_norm_coordinator is not None:
                    state_values = self._denormalize_values(state_values, self.value_norm_coordinator)
                    agent_values = torch.stack([
                        self._denormalize_values(
                            agent_values[:, agent_idx:agent_idx + 1],
                            self.value_norm_coordinator,
                        ).squeeze(-1)
                        for agent_idx in range(agent_values.size(1))
                    ], dim=1)

            bootstrap_state_values[valid_env_indices] = state_values.detach().cpu().numpy().flatten()
            bootstrap_agent_values[valid_env_indices] = agent_values.detach().cpu().numpy()
            return {'state': bootstrap_state_values, 'agents': bootstrap_agent_values}
        except Exception as e:
            main_logger.error(f"计算HA-CTSE bootstrap values时发生错误: {e}")
            return {
                'state': np.zeros(self.rollout_buffer.num_envs),
                'agents': np.zeros((self.rollout_buffer.num_envs, self.config.n_agents))
            }

    def _compute_intrinsic_reward(self, next_state, reward, next_obs, team_skill, agent_skill):
        """
        【SB3集成版本】计算内在奖励，集成数值稳定性检查
        
        关键特性:
        1. 使用互信息: I(s;z) = log q(z|s) - log p(z) 而不是原始的 log q(z|s)
        2. 基线减法（baseline subtraction）用于方差减少
        3. 奖励标准化和裁剪防止极值
        4. 运行统计量维护确保训练稳定性
        5. 集成SB3数值稳定性检查
        
        【归一化修复】确保判别器输入与策略网络使用相同的归一化，
        解决"归一化地狱"问题。
        """
        if getattr(self.config, 'disable_discriminator_rewards', False):
            env_component = self.config.lambda_e * reward if hasattr(self.config, 'lambda_e') else reward
            return env_component, env_component, 0.0, 0.0, 0.0

        with torch.no_grad():
            try:
                # === 【关键修复】归一化输入，确保与策略网络和判别器训练数据一致 ===
                # 【重要】update=False，防止重复更新 RunningMeanStd
                normalized_state = self._normalize_states(next_state, update=False)
                normalized_obs = self._normalize_observations(next_obs, update=False)
                
                # === Team Discriminator Reward (Fixed) ===
                next_state_tensor = torch.FloatTensor(normalized_state).unsqueeze(0).to(self.device)
                
                # 数值稳定性检查
                next_state_tensor = self.numerical_stabilizer.check_and_fix_tensor(
                    next_state_tensor, "next_state_tensor"
                )
                
                team_disc_logits = self._team_discriminator_logits(next_state_tensor)
                
                # 数值稳定性检查
                team_disc_logits = self.numerical_stabilizer.check_and_fix_tensor(
                    team_disc_logits, "team_disc_logits"
                )
                
                # Use log_softmax for numerical stability
                team_disc_log_probs = F.log_softmax(team_disc_logits, dim=-1)
                team_skill_log_prob = team_disc_log_probs[0, team_skill]
                
                # CRITICAL FIX: Use mutual information instead of raw log probability
                # I(s;Z) = log q_D(Z|s) - log p(Z)
                # Assume uniform prior: log p(Z) = -log(n_Z)
                team_mutual_info = float(
                    self._discriminator_mi_reward(
                        np.asarray([team_skill_log_prob.item()], dtype=np.float32),
                        team_disc_log_probs.shape[-1],
                    )[0]
                )
                
                # === Individual Discriminator Reward (Fixed) ===
                # 【关键修复】使用归一化后的观测
                agent_obs_tensor = torch.FloatTensor(normalized_obs).unsqueeze(0).to(self.device)
                
                # 数值稳定性检查
                agent_obs_tensor = self.numerical_stabilizer.check_and_fix_tensor(
                    agent_obs_tensor, "agent_obs_tensor"
                )
                
                team_skill_tensor = torch.tensor(team_skill, device=self.device)
                agent_disc_logits = self._individual_discriminator_logits(agent_obs_tensor, team_skill_tensor)
                
                # 数值稳定性检查
                agent_disc_logits = self.numerical_stabilizer.check_and_fix_tensor(
                    agent_disc_logits, "agent_disc_logits"
                )
                
                agent_disc_log_probs = F.log_softmax(agent_disc_logits, dim=-1)
                agent_skill_log_prob = agent_disc_log_probs[0, agent_skill]
                
                # CRITICAL FIX: Use mutual information for individual skills too
                # I(o;z|Z) = log q_d(z|o,Z) - log p(z|Z)
                # Assume uniform conditional prior: log p(z|Z) = -log(n_z)
                agent_mutual_info = float(
                    self._discriminator_mi_reward(
                        np.asarray([agent_skill_log_prob.item()], dtype=np.float32),
                        agent_disc_log_probs.shape[-1],
                    )[0]
                )
                
                # === Baseline Subtraction for Variance Reduction ===
                # Initialize running baselines if not exists
                if not hasattr(self, 'team_disc_baseline'):
                    self.team_disc_baseline = 0.0
                    self.ind_disc_baseline = 0.0
                    self.baseline_update_rate = 0.01
                
                # Update baselines with exponential moving average
                self.team_disc_baseline = (1 - self.baseline_update_rate) * self.team_disc_baseline + \
                                        self.baseline_update_rate * team_mutual_info
                self.ind_disc_baseline = (1 - self.baseline_update_rate) * self.ind_disc_baseline + \
                                       self.baseline_update_rate * agent_mutual_info
                
                # using raw cross entropy seems perform better
                team_disc_reward = team_mutual_info# - self.team_disc_baseline
                ind_disc_reward = agent_mutual_info# - self.ind_disc_baseline
                
                # === 新增：不确定性奖励（熵惩罚） ===
                # 从状态中提取不确定性图（熵图）
                uncertainty_reward = 0.0
                if self.config.enhanced_state and getattr(self.config, 'w_entropy', 0) > 0:
                    dims = self.config.state_component_dims
                    current_dim = dims['current_state_dim']
                    predicted_dim = dims['predicted_state_dim']
                    
                    # 提取不确定性部分
                    uncertainty_map_flat = next_state[current_dim + predicted_dim:]
                    # 计算当前智能体观测位置对应的不确定性
                    # 注意：这里我们只有一个扁平化的观测，需要一种方式来映射回不确定性图
                    # 简化处理：我们使用整个不确定性图的平均熵作为惩罚
                    # 一个更优的实现需要将智能体位置映射到不确定性图的特定区域
                    avg_entropy = np.mean(uncertainty_map_flat) if uncertainty_map_flat.size > 0 else 0
                    
                    # 熵越高，惩罚越大，激励智能体去降低不确定性
                    uncertainty_reward = -self.config.w_entropy * avg_entropy

                # === Reward Normalization and Clipping ===
                # 【临时禁用标准化】直接使用原始奖励值
                team_disc_reward_clipped = team_disc_reward
                ind_disc_reward_clipped = ind_disc_reward
                
                # === Final Reward Computation ===
                env_component = self.config.lambda_e * reward
                legacy_mi_coef = float(getattr(self.config, 'legacy_mi_reward_coef', 1.0))
                team_disc_component = legacy_mi_coef * self.config.lambda_D * team_disc_reward_clipped
                ind_disc_component = legacy_mi_coef * self.config.lambda_d * ind_disc_reward_clipped
                
                intrinsic_reward = env_component + team_disc_component + ind_disc_component + uncertainty_reward
                
                # 使用SB3数值稳定性工具进行最终检查
                if SB3_INTEGRATION_AVAILABLE:
                    # 检查所有组件的数值稳定性
                    components = {
                        'env_component': env_component,
                        'team_disc_component': team_disc_component,
                        'ind_disc_component': ind_disc_component,
                        'uncertainty_reward': uncertainty_reward, # 新增
                        'intrinsic_reward': intrinsic_reward
                    }
                    
                    for name, value in components.items():
                        if not np.isfinite(value):
                            main_logger.warning(f"数值异常检测到在 {name}: {value}")
                            if name == 'intrinsic_reward':
                                intrinsic_reward = env_component
                                team_disc_component = 0.0
                                ind_disc_component = 0.0
                                uncertainty_reward = 0.0
                            elif name == 'team_disc_component':
                                team_disc_component = 0.0
                            elif name == 'ind_disc_component':
                                ind_disc_component = 0.0
                            elif name == 'uncertainty_reward':
                                uncertainty_reward = 0.0
                else:
                    # 使用内置的数值检查
                    if not np.isfinite(intrinsic_reward):
                        intrinsic_reward = env_component
                        team_disc_component = 0.0
                        ind_disc_component = 0.0
                        uncertainty_reward = 0.0
                
                # 在返回值中包含不确定性奖励
                return intrinsic_reward, env_component, team_disc_component, ind_disc_component, uncertainty_reward
                
            except Exception as e:
                main_logger.error(f"Error in SB3-integrated intrinsic reward computation: {e}")
                env_component = self.config.lambda_e * reward if hasattr(self.config, 'lambda_e') else 0.0
                return env_component, env_component, 0.0, 0.0, 0.0

    def update_coordinator_ha_ctse(self, num_steps, bootstrap_values=None):
        rollout_data = self.rollout_buffer._get_full_rollout_data()
        if rollout_data is None:
            main_logger.warning("没有有效的Rollout数据，跳过HA-CTSE Coordinator更新")
            return 0, 0, 0, 0, 0, 0, 0, 0, 0

        high_level_valid_mask = rollout_data["high_level_valid_mask"]
        high_level_data_count = np.sum(high_level_valid_mask[:num_steps])
        if high_level_data_count == 0:
            main_logger.warning("没有有效的HA-CTSE高层策略数据，跳过Coordinator更新")
            return 0, 0, 0, 0, 0, 0, 0, 0, 0

        if bootstrap_values is not None:
            high_level_last_values = bootstrap_values
        else:
            high_level_last_values = self._compute_high_level_bootstrap_values_ha_ctse(num_steps)

        self.rollout_buffer.compute_high_level_advantages(
            high_level_last_values,
            gamma=self.config.gamma,
            value_normalizer=None,
        )

        coordinator_batch_size = getattr(self.config, 'coordinator_batch_size', 128)
        high_level_sampler = self.rollout_buffer.get_coordinator_sampler(
            num_steps,
            getattr(self.config, 'ppo_epochs', 10),
            coordinator_batch_size,
            device=self.device,
            cache_tensors=getattr(self.config, 'cache_update_tensors', False)
        )
        if high_level_sampler is None:
            return 0, 0, 0, 0, 0, 0, 0, 0, 0

        if self.config.use_valuenorm and self.value_norm_coordinator is not None:
            all_returns = self.rollout_buffer.get_all_high_level_returns(num_steps)
            if all_returns.size > 0:
                self.value_norm_coordinator.update(all_returns)

        obs_norm_mean = obs_norm_var = None
        if getattr(self.config, 'use_obsnorm', False) and self.obs_norm is not None:
            obs_norm_mean = torch.as_tensor(self.obs_norm.mean, device=self.device, dtype=torch.float32)
            obs_norm_var = torch.as_tensor(self.obs_norm.var, device=self.device, dtype=torch.float32)

        state_norm_mean = state_norm_var = None
        if getattr(self.config, 'use_statenorm', True) and self.state_norm is not None:
            state_norm_mean = torch.as_tensor(self.state_norm.mean, device=self.device, dtype=torch.float32)
            state_norm_var = torch.as_tensor(self.state_norm.var, device=self.device, dtype=torch.float32)

        coord_value_norm_tensors = self._value_norm_tensors(self.value_norm_coordinator)

        total_policy_loss = torch.zeros((), device=self.device)
        total_value_loss = torch.zeros((), device=self.device)
        total_entropy_loss = torch.zeros((), device=self.device)
        total_loss = torch.zeros((), device=self.device)
        total_cd_loss = torch.zeros((), device=self.device)
        total_cmi_loss = torch.zeros((), device=self.device)
        total_team_entropy = torch.zeros((), device=self.device)
        total_agent_entropy = torch.zeros((), device=self.device)
        total_term_entropy = torch.zeros((), device=self.device)
        total_skill_entropy = torch.zeros((), device=self.device)
        total_duration_entropy = torch.zeros((), device=self.device)
        total_aggregation_entropy = torch.zeros((), device=self.device)
        update_count = 0

        def masked_ppo_loss(new_log_prob, old_log_prob, advantage, mask):
            mask = mask.bool()
            if not mask.any().item():
                return torch.zeros((), device=self.device)
            ratio = torch.exp(new_log_prob[mask] - old_log_prob[mask].detach())
            adv = advantage[mask]
            surr1 = ratio * adv
            surr2 = torch.clamp(ratio, 1.0 - self.config.clip_epsilon, 1.0 + self.config.clip_epsilon) * adv
            return -torch.min(surr1, surr2).mean()

        for batch in high_level_sampler:
            observations_batch = batch['observations'].to(self.device)
            states_batch = batch['states'].to(self.device)
            if obs_norm_mean is not None:
                observations_batch = (observations_batch - obs_norm_mean) / torch.sqrt(obs_norm_var + 1e-8)
                observations_batch = torch.clamp(observations_batch, -10.0, 10.0)
            if state_norm_mean is not None:
                states_batch = (states_batch - state_norm_mean) / torch.sqrt(state_norm_var + 1e-8)
                states_batch = torch.clamp(states_batch, -10.0, 10.0)

            team_advantages_batch = batch['team_advantages'].to(self.device)
            agent_advantages_batch = batch['agent_advantages'].to(self.device)
            all_advantages = torch.cat([team_advantages_batch, agent_advantages_batch.reshape(-1)], dim=0)
            adv_std = all_advantages.std()
            if torch.isfinite(adv_std) and adv_std > 1e-8:
                adv_mean = all_advantages.mean()
                team_advantages_batch = (team_advantages_batch - adv_mean) / (adv_std + 1e-8)
                agent_advantages_batch = (agent_advantages_batch - adv_mean) / (adv_std + 1e-8)

            team_returns_tensor = batch['team_returns'].to(self.device)
            agent_returns_tensor = batch['agent_returns'].to(self.device)
            executed_edit_mask = batch['executed_edit_mask'].to(self.device)
            initial_assignment_mask = batch['initial_assignment_mask'].to(self.device)

            with self._update_autocast():
                coord_eval = self.ha_ctse_editor.evaluate_training_batch(
                    states_batch,
                    observations_batch,
                    batch['team_code'].to(self.device),
                    batch['active_skill_prev'].to(self.device),
                    batch['candidate_skill'].to(self.device),
                    batch['skill_age_prev'].to(self.device),
                    executed_edit_mask,
                    initial_assignment_mask,
                    deterministic=False,
                    duration_candidate=batch.get('duration_candidate', torch.zeros_like(executed_edit_mask, dtype=torch.long)).to(self.device),
                )

                bridge_type = str(getattr(self.config, 'team_bridge_type', 'deterministic'))
                if bridge_type == 'stochastic':
                    team_policy_loss = masked_ppo_loss(
                        coord_eval['log_prob_team_code'],
                        batch['log_prob_team_code'].to(self.device),
                        team_advantages_batch,
                        torch.ones_like(team_advantages_batch, dtype=torch.bool),
                    )
                else:
                    team_policy_loss = torch.zeros((), device=self.device)

                term_policy_loss = masked_ppo_loss(
                    coord_eval['log_prob_term'],
                    batch['log_prob_term'].to(self.device),
                    agent_advantages_batch,
                    initial_assignment_mask < 0.5,
                )
                skill_policy_loss = masked_ppo_loss(
                    coord_eval['log_prob_skill'],
                    batch['log_prob_skill'].to(self.device),
                    agent_advantages_batch,
                    executed_edit_mask > 0.5,
                )
                duration_policy_loss = masked_ppo_loss(
                    coord_eval.get('log_prob_duration', torch.zeros_like(coord_eval['log_prob_skill'])),
                    batch.get('log_prob_duration', torch.zeros_like(executed_edit_mask)).to(self.device),
                    agent_advantages_batch,
                    executed_edit_mask > 0.5,
                )
                policy_loss = team_policy_loss + term_policy_loss + skill_policy_loss + duration_policy_loss

                state_values = coord_eval['state_values'].squeeze(-1)
                agent_values_tensor = coord_eval['agent_values']
                if coord_value_norm_tensors is not None:
                    mean, var, std = coord_value_norm_tensors
                    team_returns_norm = (team_returns_tensor - mean) / std
                    if hasattr(self.config, "value_clip"):
                        team_returns_norm = torch.clamp(team_returns_norm, -self.config.value_clip, self.config.value_clip)
                    team_value_loss = F.mse_loss(state_values, team_returns_norm.detach())
                    agent_value_loss = 0.0
                    for i in range(self.config.n_agents):
                        agent_returns_norm = (agent_returns_tensor[:, i] - mean) / std
                        if hasattr(self.config, "value_clip"):
                            agent_returns_norm = torch.clamp(agent_returns_norm, -self.config.value_clip, self.config.value_clip)
                        agent_value_loss = agent_value_loss + F.mse_loss(agent_values_tensor[:, i], agent_returns_norm.detach())
                    agent_value_loss = agent_value_loss / self.config.n_agents
                else:
                    team_value_loss = F.mse_loss(state_values, team_returns_tensor.detach())
                    agent_value_loss = F.mse_loss(agent_values_tensor, agent_returns_tensor.detach())
                value_loss = team_value_loss + agent_value_loss

                term_entropy = coord_eval['entropy_term']
                skill_entropy = coord_eval['entropy_skill']
                duration_entropy = coord_eval.get('entropy_duration', torch.zeros_like(skill_entropy))
                term_entropy_mean = term_entropy[initial_assignment_mask < 0.5].mean() if (initial_assignment_mask < 0.5).any().item() else torch.zeros((), device=self.device)
                skill_entropy_mean = skill_entropy.mean()
                duration_entropy_mean = duration_entropy[executed_edit_mask > 0.5].mean() if (executed_edit_mask > 0.5).any().item() else torch.zeros((), device=self.device)
                team_entropy_mean = coord_eval['entropy_team_code'].mean()
                team_entropy_coef = (
                    self.ha_team_entropy_coef
                    if self.use_entropy_targets
                    else getattr(self.config, 'lambda_h', 0.0)
                )
                term_entropy_coef = (
                    self.ha_term_entropy_coef
                    if self.use_entropy_targets
                    else getattr(self.config, 'term_entropy_coef', 0.0)
                )
                skill_entropy_coef = (
                    self.ha_skill_entropy_coef
                    if self.use_entropy_targets
                    else getattr(self.config, 'skill_entropy_coef', 0.0)
                )
                entropy_loss = -(
                    team_entropy_coef * team_entropy_mean
                    + term_entropy_coef * term_entropy_mean
                    + skill_entropy_coef * skill_entropy_mean
                    + getattr(self.config, 'duration_entropy_coef', 0.0) * duration_entropy_mean
                )

                cd_loss = coord_eval.get('cd_loss', torch.zeros((), device=self.device))
                cmi_loss = coord_eval.get('cmi_loss', torch.zeros((), device=self.device))
                aggregation_entropy_mean = coord_eval.get(
                    'aggregation_entropy',
                    torch.zeros((), device=self.device),
                ).mean()
                aggregation_entropy_loss = (
                    -getattr(self.config, 'opt_aggregation_entropy_coef', 0.0)
                    * aggregation_entropy_mean
                )
                loss = (
                    policy_loss
                    + self.config.value_loss_coef * value_loss
                    + entropy_loss
                    + getattr(self.config, 'opt_cd_coef', 0.0) * cd_loss
                    + getattr(self.config, 'opt_cmi_coef', 0.0) * cmi_loss
                    + aggregation_entropy_loss
                )

            if torch.isnan(loss).any() or torch.isinf(loss).any():
                main_logger.error("HA-CTSE loss contains NaN or Inf; skipping update.")
                continue

            self.coordinator_optimizer.zero_grad()
            if self.update_amp_enabled:
                self.update_grad_scaler.scale(loss).backward()
                self.update_grad_scaler.unscale_(self.coordinator_optimizer)
            else:
                loss.backward()
            torch.nn.utils.clip_grad_norm_(self.ha_ctse_editor.parameters(), self.config.max_grad_norm)
            if self.update_amp_enabled:
                self.update_grad_scaler.step(self.coordinator_optimizer)
                self.update_grad_scaler.update()
            else:
                self.coordinator_optimizer.step()

            total_policy_loss = total_policy_loss + policy_loss.detach()
            total_value_loss = total_value_loss + value_loss.detach()
            total_entropy_loss = total_entropy_loss + entropy_loss.detach()
            total_loss = total_loss + loss.detach()
            total_cd_loss = total_cd_loss + cd_loss.detach()
            total_cmi_loss = total_cmi_loss + cmi_loss.detach()
            total_team_entropy = total_team_entropy + team_entropy_mean.detach()
            total_agent_entropy = total_agent_entropy + (term_entropy_mean + skill_entropy_mean).detach()
            total_term_entropy = total_term_entropy + term_entropy_mean.detach()
            total_skill_entropy = total_skill_entropy + skill_entropy_mean.detach()
            total_duration_entropy = total_duration_entropy + duration_entropy_mean.detach()
            total_aggregation_entropy = total_aggregation_entropy + aggregation_entropy_mean.detach()
            update_count += 1

        if update_count == 0:
            return 0, 0, 0, 0, 0, 0, 0, 0, 0

        valid_mask = high_level_valid_mask[:num_steps]
        valid_rewards = rollout_data["high_level_rewards"][:num_steps][valid_mask]
        mean_high_level_reward = float(np.mean(valid_rewards)) if valid_rewards.size > 0 else 0.0
        valid_time_steps, valid_env_indices = np.where(valid_mask)
        state_value_mean = float(np.mean(rollout_data["high_level_state_values"][valid_time_steps, valid_env_indices])) if len(valid_time_steps) > 0 else 0.0
        agent_value_mean = float(np.mean(rollout_data["high_level_agent_values"][valid_time_steps, valid_env_indices])) if len(valid_time_steps) > 0 else 0.0

        avg_team_entropy = (total_team_entropy / update_count).item()
        avg_term_entropy = (total_term_entropy / update_count).item()
        avg_skill_entropy = (total_skill_entropy / update_count).item()
        avg_duration_entropy = (total_duration_entropy / update_count).item()
        avg_aggregation_entropy = (total_aggregation_entropy / update_count).item()
        if self.use_entropy_targets:
            self._adapt_entropy_coef(
                'ha_team_entropy_coef',
                avg_team_entropy,
                self._auto_entropy_target(
                    getattr(self.config, 'num_team_codes', getattr(self.config, 'n_Z', 1)),
                    getattr(self.config, 'target_team_code_entropy_frac', 0.75),
                ),
            )
            self._adapt_entropy_coef(
                'ha_term_entropy_coef',
                avg_term_entropy,
                self._auto_entropy_target(2, getattr(self.config, 'target_term_entropy_frac', 0.65)),
            )
            self._adapt_entropy_coef(
                'ha_skill_entropy_coef',
                avg_skill_entropy,
                self._auto_entropy_target(getattr(self.config, 'n_z', 1), getattr(self.config, 'target_skill_entropy_frac', 0.75)),
            )
            self.config.lambda_h = self.ha_team_entropy_coef
            self.config.term_entropy_coef = self.ha_term_entropy_coef
            self.config.skill_entropy_coef = self.ha_skill_entropy_coef

        self.last_ha_ctse_metrics = self._collect_ha_ctse_rollout_metrics(rollout_data, num_steps)
        self.last_ha_ctse_metrics.update({
            'opt_cd_loss': (total_cd_loss / update_count).item(),
            'opt_cmi_loss': (total_cmi_loss / update_count).item(),
            'opt_aggregation_entropy_update': avg_aggregation_entropy,
            'entropy_coef_team_code': float(self.ha_team_entropy_coef),
            'entropy_coef_term': float(self.ha_term_entropy_coef),
            'entropy_coef_skill': float(self.ha_skill_entropy_coef),
            'duration_policy_entropy': avg_duration_entropy,
        })

        return (
            (total_loss / update_count).item(),
            (total_policy_loss / update_count).item(),
            (total_value_loss / update_count).item(),
            (total_team_entropy / update_count).item(),
            (total_agent_entropy / update_count).item(),
            state_value_mean,
            agent_value_mean,
            mean_high_level_reward,
            (total_cd_loss / update_count).item(),
        )

    def _collect_ha_ctse_rollout_metrics(self, rollout_data, num_steps):
        valid_mask = rollout_data["high_level_valid_mask"][:num_steps]
        if not np.any(valid_mask):
            return {}

        executed = rollout_data["executed_edit_mask"][:num_steps][valid_mask]
        requested = rollout_data["requested_edit_mask"][:num_steps][valid_mask]
        initial = rollout_data["initial_assignment_mask"][:num_steps][valid_mask]
        ages = rollout_data["skill_age"][:num_steps][valid_mask]
        age_prev = rollout_data["skill_age_prev"][:num_steps][valid_mask]
        active = rollout_data["active_skill"][:num_steps][valid_mask]
        prev = rollout_data["active_skill_prev"][:num_steps][valid_mask]
        compact = rollout_data["compact"][:num_steps][valid_mask]
        team_code = rollout_data["team_code"][:num_steps][valid_mask]
        term_entropy = rollout_data["entropy_term"][:num_steps][valid_mask]
        skill_entropy = rollout_data["entropy_skill"][:num_steps][valid_mask]
        duration_entropy = rollout_data["entropy_duration"][:num_steps][valid_mask]
        duration_target = rollout_data["duration_target"][:num_steps][valid_mask]
        duration_remaining = rollout_data["duration_remaining"][:num_steps][valid_mask]
        aggregation_entropy = rollout_data["opt_aggregation_entropy"][:num_steps][valid_mask]
        high_level_elapsed_steps = rollout_data.get(
            "high_level_elapsed_steps",
            np.ones_like(rollout_data["high_level_rewards"], dtype=np.int32),
        )[:num_steps][valid_mask]
        high_level_terminal = rollout_data.get(
            "high_level_terminal",
            np.zeros_like(rollout_data["high_level_valid_mask"], dtype=np.bool_),
        )[:num_steps][valid_mask]
        high_level_close_reason = rollout_data.get(
            "high_level_close_reason",
            np.zeros_like(rollout_data["high_level_rewards"], dtype=np.int64),
        )[:num_steps][valid_mask]

        normal_mask = (initial < 0.5).astype(np.float32)
        num_samples = max(1, executed.shape[0])
        num_agents = max(1, executed.shape[1])
        executed_counts = executed.sum(axis=1)
        requested_counts = requested.sum(axis=1)
        switched = ((active != prev) & (prev >= 0)).astype(np.float32) * normal_mask
        full_sync = executed_counts >= num_agents
        no_edit = executed_counts <= 0
        suppressed = np.maximum(requested - executed, 0.0)
        h_min_mask = ((age_prev < int(getattr(self.config, 'H_min', 0))) & (initial < 0.5)).astype(np.float32)
        h_max_forced = (
            (age_prev >= int(getattr(self.config, 'H_max', 10**9)))
            & (initial < 0.5)
            & bool(getattr(self.config, 'force_termination_after_H_max', True))
        ).astype(np.float32)

        team_code_hist = {}
        for code in team_code.reshape(-1):
            if code >= 0:
                team_code_hist[int(code)] = team_code_hist.get(int(code), 0) + 1

        if team_code_hist:
            counts = np.asarray(list(team_code_hist.values()), dtype=np.float32)
            probs = counts / max(float(counts.sum()), 1.0)
            team_code_entropy = float(-(probs * np.log(probs + 1e-8)).sum())
        else:
            team_code_entropy = 0.0

        duration_hist = {}
        executed_duration_targets = duration_target[executed > 0.5]
        for duration in executed_duration_targets.reshape(-1):
            duration_hist[int(duration)] = duration_hist.get(int(duration), 0) + 1

        close_reason_hist = {}
        for reason_code in high_level_close_reason.reshape(-1):
            close_reason_hist[int(reason_code)] = close_reason_hist.get(int(reason_code), 0) + 1

        per_agent_lifetime = ages.astype(np.float32)
        metrics = {
            'avg_requested_edits': float(np.mean(requested_counts)),
            'avg_executed_edits': float(np.mean(executed_counts)),
            'avg_switched_agents': float(np.mean(switched.sum(axis=1))),
            'no_edit_rate': float(np.mean(no_edit)),
            'full_sync_rate': float(np.mean(full_sync)),
            'suppressed_edit_rate': float(np.sum(suppressed) / max(float(np.sum(requested)), 1.0)),
            'initial_assignment_rate': float(np.mean(initial)),
            'skill_age_mean': float(np.mean(ages)),
            'skill_persistence_cycles_mean': float(np.mean(ages + 1)),
            'H_min_masked_edit_rate': float(np.mean(h_min_mask)),
            'H_max_forced_termination_rate': float(np.mean(h_max_forced)),
            'termination_rate': float(np.mean(executed)),
            'lifetime_heterogeneity': float(np.mean(np.std(per_agent_lifetime, axis=1))) if per_agent_lifetime.ndim == 2 else 0.0,
            'compact_norm_mean': float(np.mean(np.linalg.norm(compact, axis=-1))) if compact.size > 0 else 0.0,
            'compact_norm_std': float(np.std(np.linalg.norm(compact, axis=-1))) if compact.size > 0 else 0.0,
            'opt_aggregation_entropy': float(np.mean(aggregation_entropy)) if aggregation_entropy.size > 0 else 0.0,
            'team_code_entropy': team_code_entropy,
            'team_code_usage_histogram': team_code_hist,
            'term_policy_entropy': float(np.mean(term_entropy)),
            'skill_policy_entropy': float(np.mean(skill_entropy)),
            'duration_policy_entropy': float(np.mean(duration_entropy)) if duration_entropy.size > 0 else 0.0,
            'duration_remaining_mean': float(np.mean(duration_remaining)) if duration_remaining.size > 0 else 0.0,
            'duration_target_mean': float(np.mean(executed_duration_targets)) if executed_duration_targets.size > 0 else 0.0,
            'duration_target_histogram': duration_hist,
            'high_level_elapsed_steps_mean': float(np.mean(high_level_elapsed_steps)) if high_level_elapsed_steps.size > 0 else 0.0,
            'high_level_elapsed_steps_max': float(np.max(high_level_elapsed_steps)) if high_level_elapsed_steps.size > 0 else 0.0,
            'high_level_terminal_rate': float(np.mean(high_level_terminal)) if high_level_terminal.size > 0 else 0.0,
            'high_level_close_reason_histogram': close_reason_hist,
            'horizon_penalty_scale': self._warmup_scale(getattr(self.config, 'horizon_penalty_warmup_steps', 0)),
            'switch_penalty_scale': self._warmup_scale(getattr(self.config, 'switch_penalty_warmup_steps', 0)),
            'entropy_coef_team_code': float(getattr(self, 'ha_team_entropy_coef', getattr(self.config, 'lambda_h', 0.0))),
            'entropy_coef_term': float(getattr(self, 'ha_term_entropy_coef', getattr(self.config, 'term_entropy_coef', 0.0))),
            'entropy_coef_skill': float(getattr(self, 'ha_skill_entropy_coef', getattr(self.config, 'skill_entropy_coef', 0.0))),
            'entropy_coef_low_level': float(getattr(self, 'low_level_entropy_coef', getattr(self.config, 'lambda_l', 0.0))),
        }
        if self.process_segment_buffer is not None:
            metrics.update(self.process_segment_buffer.stats())
        return metrics

    def _build_process_segment_batch(self, segments):
        valid_segments = [
            seg for seg in segments
            if int(seg.get("length", 0)) > 0 and 0 <= int(seg.get("skill", -1)) < int(self.config.n_z)
        ]
        if not valid_segments:
            return None, []

        batch_size = len(valid_segments)
        max_len = max(int(seg.get("length", 0)) for seg in valid_segments)
        obs = np.zeros((batch_size, max_len, self.config.obs_dim), dtype=np.float32)
        next_obs = np.zeros_like(obs)
        action_dim = 1 if getattr(self.config, 'action_space_type', 'continuous') == 'discrete' else int(self.config.action_dim)
        actions = np.zeros((batch_size, max_len, action_dim), dtype=np.float32)
        rewards = np.zeros((batch_size, max_len), dtype=np.float32)
        masks = np.zeros((batch_size, max_len), dtype=np.float32)
        outcomes = np.zeros((batch_size, len(SkillProcessOutcomeExtractor.FIELD_NAMES)), dtype=np.float32)
        outcome_masks = np.zeros_like(outcomes)
        labels = np.zeros(batch_size, dtype=np.int64)
        durations = np.zeros(batch_size, dtype=np.int64)

        for batch_idx, segment in enumerate(valid_segments):
            length = int(segment.get("length", 0))
            labels[batch_idx] = int(segment.get("skill", 0))
            durations[batch_idx] = int(segment.get("duration_target", 0))
            obs_seq = segment.get("obs_seq", [])
            next_obs_seq = segment.get("next_obs_seq", [])
            action_seq = segment.get("action_seq", [])
            reward_seq = segment.get("reward_seq", [])
            for step_idx in range(length):
                if step_idx < len(obs_seq):
                    obs_arr = np.asarray(obs_seq[step_idx], dtype=np.float32).reshape(-1)
                    obs[batch_idx, step_idx, :min(obs_arr.size, self.config.obs_dim)] = obs_arr[:self.config.obs_dim]
                if step_idx < len(next_obs_seq):
                    next_obs_arr = np.asarray(next_obs_seq[step_idx], dtype=np.float32).reshape(-1)
                    next_obs[batch_idx, step_idx, :min(next_obs_arr.size, self.config.obs_dim)] = next_obs_arr[:self.config.obs_dim]
                else:
                    next_obs[batch_idx, step_idx] = obs[batch_idx, step_idx]
                if step_idx < len(action_seq):
                    action_arr = np.asarray(action_seq[step_idx], dtype=np.float32).reshape(-1)
                    actions[batch_idx, step_idx, :min(action_arr.size, action_dim)] = action_arr[:action_dim]
                if step_idx < len(reward_seq):
                    rewards[batch_idx, step_idx] = float(reward_seq[step_idx])
                masks[batch_idx, step_idx] = 1.0
            if "outcome_normalized" in segment:
                outcomes[batch_idx] = np.asarray(segment["outcome_normalized"], dtype=np.float32)
            elif "outcome_vector" in segment:
                outcomes[batch_idx] = np.asarray(segment["outcome_vector"], dtype=np.float32)
            if "outcome_mask" in segment:
                outcome_masks[batch_idx] = np.asarray(segment["outcome_mask"], dtype=np.float32)

        batch = {
            "obs": torch.as_tensor(obs, dtype=torch.float32, device=self.device),
            "next_obs": torch.as_tensor(next_obs, dtype=torch.float32, device=self.device),
            "actions": torch.as_tensor(actions, dtype=torch.float32, device=self.device),
            "rewards": torch.as_tensor(rewards, dtype=torch.float32, device=self.device),
            "masks": torch.as_tensor(masks, dtype=torch.float32, device=self.device),
            "outcomes": torch.as_tensor(outcomes, dtype=torch.float32, device=self.device),
            "outcome_masks": torch.as_tensor(outcome_masks, dtype=torch.float32, device=self.device),
            "labels": torch.as_tensor(labels, dtype=torch.long, device=self.device),
            "durations": durations,
        }
        return batch, valid_segments

    def update_process_exploration_from_segments(self):
        metrics = {
            'process_encoder_loss': 0.0,
            'process_outcome_loss': 0.0,
            'process_contrastive_loss': 0.0,
            'process_contrastive_accuracy': 0.0,
            'process_duration_only_accuracy': 0.0,
            'process_reward_mean': 0.0,
            'process_reward_abs_mean': 0.0,
            'process_reward_applied_steps': 0.0,
            'process_segments_trained': 0.0,
        }
        if (
            not self.use_process_exploration
            or self.process_segment_buffer is None
            or self.process_encoder is None
            or self.process_outcome_predictor is None
            or self.process_contrastive_head is None
            or self.process_optimizer is None
        ):
            self.last_process_metrics = metrics
            return metrics

        segments = self.process_segment_buffer.get_completed_segments()
        batch, valid_segments = self._build_process_segment_batch(segments)
        if batch is None:
            self.last_process_metrics = metrics
            return metrics

        num_segments = len(valid_segments)
        metrics['process_segments_trained'] = float(num_segments)
        metrics['process_duration_only_accuracy'] = duration_only_baseline_accuracy(
            batch["durations"],
            process_positive_skill_labels(valid_segments),
        )

        epochs = max(1, int(getattr(self.config, 'process_encoder_epochs', 1)))
        batch_size = max(1, int(getattr(self.config, 'process_encoder_batch_size', 128)))
        outcome_coef = float(getattr(self.config, 'process_outcome_coef', 0.0))
        contrastive_coef = float(getattr(self.config, 'process_contrastive_coef', 0.0))
        total_loss = total_outcome_loss = total_contrastive_loss = total_acc = 0.0
        updates = 0

        for _ in range(epochs):
            perm = torch.randperm(num_segments, device=self.device)
            for start in range(0, num_segments, batch_size):
                idx = perm[start:start + batch_size]
                embeddings = self.process_encoder(
                    batch["obs"][idx],
                    batch["actions"][idx],
                    batch["next_obs"][idx],
                    batch["rewards"][idx],
                    batch["masks"][idx],
                )
                predicted = self.process_outcome_predictor(embeddings)
                outcome_loss = self.process_outcome_predictor.masked_mse_loss(
                    predicted,
                    batch["outcomes"][idx],
                    batch["outcome_masks"][idx],
                )
                contrastive = self.process_contrastive_head(embeddings, batch["labels"][idx])
                contrastive_loss = contrastive["loss"]
                loss = outcome_coef * outcome_loss + contrastive_coef * contrastive_loss

                self.process_optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(
                    list(self.process_encoder.parameters())
                    + list(self.process_outcome_predictor.parameters())
                    + list(self.process_contrastive_head.parameters()),
                    self.config.max_grad_norm,
                )
                self.process_optimizer.step()

                total_loss += float(loss.detach().item())
                total_outcome_loss += float(outcome_loss.detach().item())
                total_contrastive_loss += float(contrastive_loss.detach().item())
                total_acc += float(contrastive["accuracy"].detach().item())
                updates += 1

        if updates > 0:
            metrics['process_encoder_loss'] = total_loss / updates
            metrics['process_outcome_loss'] = total_outcome_loss / updates
            metrics['process_contrastive_loss'] = total_contrastive_loss / updates
            metrics['process_contrastive_accuracy'] = total_acc / updates

        reward_values = []
        applied_steps = 0
        if bool(getattr(self.config, 'use_process_reward_for_discoverer', False)):
            with torch.no_grad():
                embeddings = self.process_encoder(
                    batch["obs"],
                    batch["actions"],
                    batch["next_obs"],
                    batch["rewards"],
                    batch["masks"],
                )
                predicted = self.process_outcome_predictor(embeddings)
                outcome_mask = batch["outcome_masks"]
                outcome_error = ((predicted - batch["outcomes"]).pow(2) * outcome_mask).sum(dim=-1) / outcome_mask.sum(dim=-1).clamp_min(1.0)
                logits = self.process_contrastive_head.logits(embeddings)
                log_probs = F.log_softmax(logits, dim=-1)
                labels = batch["labels"]
                contrastive_mi = log_probs[torch.arange(num_segments, device=self.device), labels] + np.log(max(int(self.config.n_z), 1))
                signal = contrastive_coef * contrastive_mi - outcome_coef * outcome_error
                warmup_steps = int(getattr(self.config, 'process_reward_warmup_steps', 0) or 0)
                reward_scale = self._warmup_scale(warmup_steps)
                process_rewards = (
                    float(getattr(self.config, 'process_reward_coef', 0.0))
                    * reward_scale
                    * signal
                )
                clip_value = float(getattr(self.config, 'process_reward_clip', 2.0))
                process_rewards = torch.clamp(process_rewards, -clip_value, clip_value).detach().cpu().numpy()

            for segment, reward_value in zip(valid_segments, process_rewards):
                steps = np.asarray(segment.get("step_seq", []), dtype=np.int64)
                if steps.size == 0:
                    continue
                if getattr(self.config, 'process_reward_distribution', 'mean_over_segment') == 'terminal':
                    rewards_to_apply = np.zeros(steps.size, dtype=np.float32)
                    rewards_to_apply[-1] = float(reward_value)
                else:
                    rewards_to_apply = np.full(
                        steps.size,
                        float(reward_value) / max(int(steps.size), 1),
                        dtype=np.float32,
                    )
                applied_steps += self.rollout_buffer.add_process_rewards(
                    int(segment.get("env_id", 0)),
                    int(segment.get("agent_id", 0)),
                    steps,
                    rewards_to_apply,
                )
                reward_values.append(float(reward_value))

        if reward_values:
            reward_arr = np.asarray(reward_values, dtype=np.float32)
            metrics['process_reward_mean'] = float(np.mean(reward_arr))
            metrics['process_reward_abs_mean'] = float(np.mean(np.abs(reward_arr)))
        metrics['process_reward_applied_steps'] = float(applied_steps)
        self.last_process_metrics = metrics
        main_logger.info(
            "Process探索更新完成: "
            f"segments={num_segments}, loss={metrics['process_encoder_loss']:.4f}, "
            f"outcome={metrics['process_outcome_loss']:.4f}, "
            f"nce={metrics['process_contrastive_loss']:.4f}, "
            f"acc={metrics['process_contrastive_accuracy']:.3f}, "
            f"reward_mean={metrics['process_reward_mean']:.4f}"
        )
        return metrics

    def _audit_high_replay_likelihood(self, rollout_data, num_steps):
        """Replay stored native-HMASD high actions without changing RNG or policy state."""
        if not bool(getattr(self.config, 'audit_high_replay_likelihood', False)):
            return

        valid_time_steps, valid_env_indices = np.where(
            rollout_data['high_level_valid_mask'][:num_steps]
        )
        sample_count = int(valid_time_steps.size)
        if sample_count == 0:
            self.high_replay_likelihood_metrics.update({
                'latest_team_max_abs_error': 0.0,
                'latest_agent_max_abs_error': 0.0,
                'latest_max_abs_error': 0.0,
                'latest_sample_count': 0,
            })
            return

        batch_size = max(1, int(getattr(self.config, 'coordinator_batch_size', 128)))
        team_max_abs_error = 0.0
        agent_max_abs_error = 0.0
        torch_cpu_rng_state = torch.random.get_rng_state()
        torch_cuda_rng_states = (
            torch.cuda.get_rng_state_all()
            if torch.cuda.is_available()
            else None
        )
        numpy_rng_state = np.random.get_state()
        python_rng_state = random.getstate()

        try:
            with torch.no_grad():
                for start in range(0, sample_count, batch_size):
                    end = min(start + batch_size, sample_count)
                    time_batch = valid_time_steps[start:end]
                    env_batch = valid_env_indices[start:end]

                    states = torch.as_tensor(
                        rollout_data['states'][time_batch, env_batch],
                        dtype=torch.float32,
                        device=self.device,
                    )
                    observations = torch.as_tensor(
                        rollout_data['obs'][time_batch, env_batch],
                        dtype=torch.float32,
                        device=self.device,
                    )
                    if getattr(self.config, 'use_obsnorm', False) and self.obs_norm is not None:
                        obs_mean = torch.as_tensor(
                            self.obs_norm.mean, dtype=torch.float32, device=self.device
                        )
                        obs_var = torch.as_tensor(
                            self.obs_norm.var, dtype=torch.float32, device=self.device
                        )
                        observations = torch.clamp(
                            (observations - obs_mean) / torch.sqrt(obs_var + 1e-8),
                            -10.0,
                            10.0,
                        )
                    if getattr(self.config, 'use_statenorm', True) and self.state_norm is not None:
                        state_mean = torch.as_tensor(
                            self.state_norm.mean, dtype=torch.float32, device=self.device
                        )
                        state_var = torch.as_tensor(
                            self.state_norm.var, dtype=torch.float32, device=self.device
                        )
                        states = torch.clamp(
                            (states - state_mean) / torch.sqrt(state_var + 1e-8),
                            -10.0,
                            10.0,
                        )

                    team_skills = torch.as_tensor(
                        rollout_data['team_skills'][time_batch, env_batch],
                        dtype=torch.long,
                        device=self.device,
                    )
                    agent_skills = torch.as_tensor(
                        rollout_data['agent_skills'][time_batch, env_batch],
                        dtype=torch.long,
                        device=self.device,
                    )
                    replay = self.skill_coordinator.evaluate_training_batch(
                        states,
                        observations,
                        team_skills,
                        agent_skills,
                    )
                    old_team_log_probs = torch.as_tensor(
                        rollout_data['high_level_team_log_probs'][time_batch, env_batch],
                        dtype=torch.float32,
                        device=self.device,
                    )
                    old_agent_log_probs = torch.as_tensor(
                        rollout_data['high_level_agent_log_probs'][time_batch, env_batch],
                        dtype=torch.float32,
                        device=self.device,
                    )
                    team_errors = torch.abs(replay['team_log_probs'] - old_team_log_probs)
                    agent_errors = torch.abs(replay['agent_log_probs'] - old_agent_log_probs)
                    batch_team_max = (
                        float(team_errors.max().item())
                        if torch.isfinite(team_errors).all()
                        else float('inf')
                    )
                    batch_agent_max = (
                        float(agent_errors.max().item())
                        if torch.isfinite(agent_errors).all()
                        else float('inf')
                    )
                    team_max_abs_error = max(team_max_abs_error, batch_team_max)
                    agent_max_abs_error = max(agent_max_abs_error, batch_agent_max)
        finally:
            torch.random.set_rng_state(torch_cpu_rng_state)
            if torch_cuda_rng_states is not None:
                torch.cuda.set_rng_state_all(torch_cuda_rng_states)
            np.random.set_state(numpy_rng_state)
            random.setstate(python_rng_state)

        latest_max_abs_error = max(team_max_abs_error, agent_max_abs_error)
        metrics = self.high_replay_likelihood_metrics
        metrics.update({
            'latest_team_max_abs_error': team_max_abs_error,
            'latest_agent_max_abs_error': agent_max_abs_error,
            'latest_max_abs_error': latest_max_abs_error,
            'latest_sample_count': sample_count,
            'global_team_max_abs_error': max(
                float(metrics['global_team_max_abs_error']), team_max_abs_error
            ),
            'global_agent_max_abs_error': max(
                float(metrics['global_agent_max_abs_error']), agent_max_abs_error
            ),
            'global_max_abs_error': max(
                float(metrics['global_max_abs_error']), latest_max_abs_error
            ),
            'global_sample_count': int(metrics['global_sample_count']) + sample_count,
        })

    def update_coordinator(self, num_steps, bootstrap_values=None):
        """更新高层技能协调器网络（使用标准PPO更新，而非错误的序列化更新）"""
        if self.use_ha_ctse:
            return self.update_coordinator_ha_ctse(num_steps, bootstrap_values=bootstrap_values)

        if self.d2_enabled:
            # Close every still-open segment at the rollout boundary before the
            # tables are read (plan section 6).
            self._d2_flush_open_segments(num_steps)

        # num_steps 现在是实际在缓冲区中的有效数据量
        
        # 【修复】首先从缓冲区获取数据以检查有效样本数
        rollout_data = self.rollout_buffer._get_full_rollout_data()
        if rollout_data is None:
            main_logger.warning("没有有效的Rollout数据，跳过Coordinator更新")
            return 0, 0, 0, 0, 0, 0, 0, 0, 0
            
        # 检查是否有有效的高层数据
        high_level_valid_mask = rollout_data["high_level_valid_mask"]
        high_level_data_count = np.sum(high_level_valid_mask[:num_steps])
        self._audit_high_replay_likelihood(rollout_data, num_steps)
        if (
            bool(getattr(self.config, 'r39a_strict_contract', False))
            and int(self.high_replay_likelihood_metrics['latest_sample_count']) <= 0
        ):
            raise ValueError("R39A collected no replayable high-policy samples")
        if (
            bool(getattr(self.config, 'r39a_strict_contract', False))
            and float(self.high_replay_likelihood_metrics['latest_max_abs_error']) > 1e-6
        ):
            raise ValueError(
                "R39A high-policy replay likelihood mismatch: "
                f"{self.high_replay_likelihood_metrics['latest_max_abs_error']:.9g} > 1e-6"
            )
        if high_level_data_count == 0:
            main_logger.warning("没有有效的高层策略数据，跳过Coordinator更新")
            return 0, 0, 0, 0, 0, 0, 0, 0, 0
        
        main_logger.info(f"开始使用统一缓冲区更新Coordinator，有效高层数据: {high_level_data_count}个")
        
        # 【GAE引导价值修复】优先使用传入的准确 bootstrap_values
        if bootstrap_values is not None:
            high_level_last_values = bootstrap_values
            main_logger.debug("使用传入的Bootstrap Values进行GAE计算")
        else:
            # Fallback: 获取buffer中最后的有效状态和观测来计算bootstrap值
            main_logger.warning("未提供Bootstrap Values，回退到从Buffer搜索（可能存在偏差）")
            high_level_last_values = self._compute_high_level_bootstrap_values(num_steps)
        
        
        gamma_high = self.config.gamma #** self.config.k
        
        # 【关键修复】Buffer中已是真实值，不再需要value_normalizer进行反归一化
        profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
        self.rollout_buffer.compute_high_level_advantages(
            high_level_last_values, 
            gamma=gamma_high, 
            value_normalizer=None
        )
        if self.enable_runtime_profiling:
            self._add_update_profile('coord_advantage', time.perf_counter() - profile_start)
        
        # 累积损失统计
        total_policy_loss = torch.zeros((), device=self.device)
        total_value_loss = torch.zeros((), device=self.device)
        total_entropy_loss = torch.zeros((), device=self.device)
        total_loss = torch.zeros((), device=self.device)
        total_cd_loss = torch.zeros((), device=self.device)
        total_team_entropy = torch.zeros((), device=self.device)
        total_agent_entropy = torch.zeros((), device=self.device)
        update_count = 0
        
        # 【关键修改】使用标准的batch_size而不是序列长度
        coordinator_batch_size = getattr(self.config, 'coordinator_batch_size', 128)
        
        # 【修复】使用专门的Coordinator采样器进行标准PPO更新
        high_level_sampler = self.rollout_buffer.get_coordinator_sampler(
            num_steps,
            getattr(self.config, 'ppo_epochs', 10),
            coordinator_batch_size,
            device=self.device,
            cache_tensors=getattr(self.config, 'cache_update_tensors', False)
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

        obs_norm_mean = obs_norm_var = None
        if getattr(self.config, 'use_obsnorm', False) and self.obs_norm is not None:
            obs_norm_mean = torch.as_tensor(self.obs_norm.mean, device=self.device, dtype=torch.float32)
            obs_norm_var = torch.as_tensor(self.obs_norm.var, device=self.device, dtype=torch.float32)

        state_norm_mean = state_norm_var = None
        if getattr(self.config, 'use_statenorm', True) and self.state_norm is not None:
            state_norm_mean = torch.as_tensor(self.state_norm.mean, device=self.device, dtype=torch.float32)
            state_norm_var = torch.as_tensor(self.state_norm.var, device=self.device, dtype=torch.float32)

        coord_value_norm_tensors = self._value_norm_tensors(self.value_norm_coordinator)

        high_level_sampler_iter = iter(high_level_sampler)
        while True:
            profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
            try:
                batch = next(high_level_sampler_iter)
            except StopIteration:
                break
            if self.enable_runtime_profiling:
                self._add_update_profile('coord_sampler', time.perf_counter() - profile_start)

            batch_profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
            # 提取离散批次数据（注意没有时间维度T）
            observations_batch = batch['observations'].to(self.device)  # Shape: (B, n_agents, obs_dim)
            states_batch = batch['states'].to(self.device)             # Shape: (B, state_dim)
            
            # 手动应用归一化
            if obs_norm_mean is not None:
                observations_batch = (observations_batch - obs_norm_mean) / torch.sqrt(obs_norm_var + 1e-8)
                observations_batch = torch.clamp(observations_batch, -10.0, 10.0)

            if state_norm_mean is not None:
                states_batch = (states_batch - state_norm_mean) / torch.sqrt(state_norm_var + 1e-8)
                states_batch = torch.clamp(states_batch, -10.0, 10.0)

            team_skills_batch = batch['team_skills'].to(self.device)    # Shape: (B,)
            agent_skills_batch = batch['agent_skills'].to(self.device) # Shape: (B, n_agents)
            
            # 【关键修复】使用分离的旧log_probs
            old_team_log_probs_batch = batch['old_team_log_probs'].to(self.device)
            old_agent_log_probs_batch = batch['old_agent_log_probs'].to(self.device)
            
            # 【关键修复】使用分离的优势和回报数据
            team_advantages_batch = batch['team_advantages'].to(self.device)
            agent_advantages_batch = batch['agent_advantages'].to(self.device)
            team_returns_tensor = batch['team_returns'].to(self.device)
            agent_returns_tensor = batch['agent_returns'].to(self.device)
            
            # --- 核心改动：一次Transformer编码同时评估策略和价值 ---
            with self._update_autocast():
                coord_eval = self.skill_coordinator.evaluate_training_batch(
                    states_batch,
                    observations_batch,
                    team_skills_batch,
                    agent_skills_batch,
                    collect_profile=self.enable_runtime_profiling,
                    sync_fn=self._sync_cuda_for_profile if self.enable_runtime_profiling else None,
                )
            if self.enable_runtime_profiling:
                for profile_key, elapsed in coord_eval.get('profile', {}).items():
                    self._add_update_profile(profile_key, elapsed)

            team_log_probs = coord_eval['team_log_probs']
            team_entropy = coord_eval['team_entropy']
            agent_log_probs = coord_eval['agent_log_probs']
            agent_entropies_tensor = coord_eval['agent_entropies']

            # 【修复】按照论文公式计算总熵：E[H(π_h(Z|...)) + Σ H(π_h(z_i|...))]
            # 先计算每个批次样本的总熵（团队熵 + 所有个体熵之和），然后取期望（均值）
            total_entropy_per_sample = team_entropy + agent_entropies_tensor.sum(dim=1)  # Shape: (B,)
            entropy = total_entropy_per_sample.mean()  # 对批次取均值，得到标量

            # 【论文一致性修复】按照论文公式(6)分别处理团队技能和个体技能的价值
            # 不再合并价值函数，而是分别计算损失
            state_values = coord_eval['state_values']
            state_values = state_values.squeeze(-1)  # Shape: (B,) - 用于团队技能
            
            # 将智能体价值列表转换为张量，用于个体技能
            agent_values_tensor = coord_eval['agent_values'].transpose(0, 1)  # Shape: (n_agents, B)

            # 【逻辑修复】统一优势归一化
            # 1. 拼接所有优势 (Batch * (1 + N_Agents))
            # team: [B], agent: [B, N] -> flatten agent -> cat
            all_advantages = torch.cat([team_advantages_batch, agent_advantages_batch.reshape(-1)], dim=0)

            # 2. 计算全局统计量
            global_mean = all_advantages.mean()
            global_std = all_advantages.std() + 1e-8

            # 3. 统一归一化
            team_advantages_batch = (team_advantages_batch - global_mean) / global_std
            agent_advantages_batch = (agent_advantages_batch - global_mean) / global_std

            # --- 【修复】计算解耦的PPO策略损失 ---
            # 1. 团队策略损失
            team_ratios = torch.exp(team_log_probs - old_team_log_probs_batch.detach())
            team_surr1 = team_ratios * team_advantages_batch
            team_surr2 = torch.clamp(team_ratios, 1.0 - self.config.clip_epsilon, 1.0 + self.config.clip_epsilon) * team_advantages_batch
            team_policy_loss = -torch.min(team_surr1, team_surr2).mean()

            # 2. 个体策略损失
            # agent_log_probs shape: [B, n_agents]
            # old_agent_log_probs_batch shape: [B, n_agents]
            # agent_advantages_batch shape: [B, n_agents]
            agent_ratios = torch.exp(agent_log_probs - old_agent_log_probs_batch.detach())
            
            agent_surr1 = agent_ratios * agent_advantages_batch
            agent_surr2 = torch.clamp(agent_ratios, 1.0 - self.config.clip_epsilon, 1.0 + self.config.clip_epsilon) * agent_advantages_batch
            agent_policy_loss = -torch.min(agent_surr1, agent_surr2).mean()

            # 组合策略损失
            policy_loss = team_policy_loss + agent_policy_loss

            # 【内部 ValueNorm】按照论文公式(6)分别计算团队技能和个体技能的价值损失（MAPPO 风格）
            # 假设网络输出 state_values / agent_values_tensor 为归一化后的 value（V_norm），
            # 使用 RunningMeanStd 对真实尺度的 team_returns_tensor / agent_returns_tensor 进行归一化后作为目标。
            if coord_value_norm_tensors is not None:
                mean, var, std = coord_value_norm_tensors
                # 1) 团队技能 value：用归一化后的团队回报作为目标
                team_returns_norm = (team_returns_tensor - mean) / std
                if hasattr(self.config, "value_clip"):
                    team_returns_norm = torch.clamp(
                        team_returns_norm,
                        -self.config.value_clip,
                        self.config.value_clip,
                    )
                # state_values 被视为 V_norm
                team_value_loss = F.mse_loss(state_values, team_returns_norm.detach())

                # 2) 个体技能 value：同样归一化对应的个体回报
                agent_value_loss = 0.0
                for i in range(self.config.n_agents):
                    agent_returns_norm = (agent_returns_tensor[:, i] - mean) / std
                    if hasattr(self.config, "value_clip"):
                        agent_returns_norm = torch.clamp(
                            agent_returns_norm,
                            -self.config.value_clip,
                            self.config.value_clip,
                        )
                    # agent_values_tensor[i] 被视为 V_norm
                    agent_value_loss += F.mse_loss(agent_values_tensor[i], agent_returns_norm.detach())
                agent_value_loss /= self.config.n_agents
            else:
                team_value_loss = F.mse_loss(state_values, team_returns_tensor.detach())
                agent_value_loss = 0.0
                for i in range(self.config.n_agents):
                    agent_value_loss += F.mse_loss(agent_values_tensor[i], agent_returns_tensor[:, i].detach())
                agent_value_loss /= self.config.n_agents
            
            # 【论文公式(6)】组合团队和个体价值损失
            value_loss = team_value_loss + agent_value_loss
            
            # 熵损失
            # 【修复】使用config中定义的统一熵系数，严格按照论文公式
            entropy_loss = -self.config.lambda_h * entropy
            
            # CD损失（如果启用OPT）
            cd_loss = coord_eval.get('cd_loss', torch.tensor(0.0, device=self.device))
            if getattr(self.config, 'use_opt_coordinator', False):
                # evaluate_training_batch 与当前 get_value 一样返回已计算的 cd_loss 占位值；
                # 避免为了默认0值再走一次Transformer编码。
                cd_loss = coord_eval.get('cd_loss', torch.tensor(0.0, device=self.device))
            
            # 总损失
            if getattr(self.config, 'use_opt_coordinator', False):
                loss = policy_loss + self.config.value_loss_coef * value_loss + entropy_loss + getattr(self.config, 'lambda_cd', 0.1) * cd_loss
            else:
                loss = policy_loss + self.config.value_loss_coef * value_loss + entropy_loss
            
            # 更新网络
            if torch.isnan(loss).any() or torch.isinf(loss).any():
                main_logger.error("Loss contains NaN or Inf! Skipping update.")
                continue # 跳过此次更新

            profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
            self.coordinator_optimizer.zero_grad()
            if self.update_amp_enabled:
                self.update_grad_scaler.scale(loss).backward()
                self.update_grad_scaler.unscale_(self.coordinator_optimizer)
            else:
                loss.backward()  # 标准的PPO反向传播
            torch.nn.utils.clip_grad_norm_(self.skill_coordinator.parameters(), self.config.max_grad_norm)
            if self.enable_runtime_profiling:
                self._sync_cuda_for_profile()
                self._add_update_profile('coord_backward', time.perf_counter() - profile_start)

            profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
            if self.update_amp_enabled:
                self.update_grad_scaler.step(self.coordinator_optimizer)
                self.update_grad_scaler.update()
            else:
                self.coordinator_optimizer.step()
            if self.enable_runtime_profiling:
                self._sync_cuda_for_profile()
                self._add_update_profile('coord_optimizer', time.perf_counter() - profile_start)
            
            # 累积统计
            total_policy_loss = total_policy_loss + policy_loss.detach()
            total_value_loss = total_value_loss + value_loss.detach()
            total_entropy_loss = total_entropy_loss + entropy_loss.detach()
            total_loss = total_loss + loss.detach()
            total_cd_loss = total_cd_loss + cd_loss.detach()
            
            # 分别统计团队技能和个体技能的熵（用于TensorBoard记录）
            total_team_entropy = total_team_entropy + team_entropy.mean().detach()
            total_agent_entropy = total_agent_entropy + agent_entropies_tensor.mean().detach()
            
            update_count += 1
            
            if main_logger.isEnabledFor(10):
                main_logger.debug(f"Coordinator 标准更新 #{update_count}: "
                                f"Loss={loss.item():.6f}, Policy={policy_loss.item():.6f}, "
                                f"Value={value_loss.item():.6f}, Entropy={entropy.item():.6f}")
            if self.enable_runtime_profiling:
                self._sync_cuda_for_profile()
                self._add_update_profile('coord_forward_backward', time.perf_counter() - batch_profile_start)
        
        if self.r39_native_hmasd_toy:
            self.native_toy_optimizer_updates['high'] += int(update_count)

        # 计算平均损失
        avg_policy_loss = (total_policy_loss / update_count).item() if update_count > 0 else 0.0
        avg_value_loss = (total_value_loss / update_count).item() if update_count > 0 else 0.0
        avg_entropy_loss = (total_entropy_loss / update_count).item() if update_count > 0 else 0.0
        avg_total_loss = (total_loss / update_count).item() if update_count > 0 else 0.0
        avg_cd_loss = (total_cd_loss / update_count).item() if update_count > 0 else 0.0
        avg_team_entropy = (total_team_entropy / update_count).item() if update_count > 0 else 0.0
        avg_agent_entropy = (total_agent_entropy / update_count).item() if update_count > 0 else 0.0
        profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
        # 计算其他统计信息（从统一缓冲区获取高层数据）
        valid_mask = high_level_valid_mask[:num_steps]
        valid_high_level_rewards = rollout_data["high_level_rewards"][:num_steps][valid_mask]
        if valid_high_level_rewards.size > 0:
            avg_high_level_reward = float(np.mean(valid_high_level_rewards))
            valid_time_steps, valid_env_indices = np.where(valid_mask)
            sample_size = min(50, valid_time_steps.size)
            if sample_size > 0:
                sample_t = valid_time_steps[:sample_size]
                sample_e = valid_env_indices[:sample_size]
                with torch.no_grad():
                    sample_states = torch.as_tensor(
                        rollout_data["states"][sample_t, sample_e],
                        dtype=torch.float32,
                        device=self.device
                    )
                    sample_observations = torch.as_tensor(
                        rollout_data["obs"][sample_t, sample_e],
                        dtype=torch.float32,
                        device=self.device
                    )
                    state_val, agent_vals, _ = self.skill_coordinator.get_value(sample_states, sample_observations)
                    mean_state_value = float(state_val.mean().item())
                    if agent_vals is not None and len(agent_vals) > 0:
                        mean_agent_value = float(torch.stack(agent_vals).mean().item())
                    else:
                        mean_agent_value = 0.0
            else:
                mean_state_value = 0.0
                mean_agent_value = 0.0
        else:
            avg_high_level_reward = 0.0
            mean_state_value = 0.0
            mean_agent_value = 0.0
        if self.enable_runtime_profiling:
            self._add_update_profile('coord_stats', time.perf_counter() - profile_start)
        
        main_logger.info(f"Coordinator 标准更新完成: {update_count}次更新, "
                        f"平均损失={avg_total_loss:.6f}, 平均策略损失={avg_policy_loss:.6f}, "
                        f"平均价值损失={avg_value_loss:.6f}")
        
        return avg_total_loss, avg_policy_loss, avg_value_loss, \
               avg_team_entropy, avg_agent_entropy, \
               mean_state_value, mean_agent_value, avg_high_level_reward, avg_cd_loss
    
    def update_discoverer_from_rollout(self, last_values, dones):
        """
        使用重构后的RolloutBuffer更新低层技能发现器网络。
        """
        if self.r39_native_toy_fixed_primitives:
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        main_logger.info("开始使用重构后的RolloutBuffer更新Discoverer...")
        
        # 1. 计算GAE
        # 【关键修复】Buffer中已是真实值，不再需要value_normalizer进行反归一化
        profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
        self.rollout_buffer.compute_advantages(
            last_values, 
            dones, 
            gamma=self.config.gamma, 
            gae_lambda=self.config.gae_lambda, 
            value_normalizer=None
        )
        if self.enable_runtime_profiling:
            self._add_update_profile('discoverer_advantage', time.perf_counter() - profile_start)
        
        # 累积损失统计
        total_policy_loss = torch.zeros((), device=self.device)
        total_value_loss = torch.zeros((), device=self.device)
        total_entropy_loss = torch.zeros((), device=self.device)
        total_loss = torch.zeros((), device=self.device)
        update_count = 0
        
        ppo_epochs = getattr(self.config, 'ppo_epochs', 10)  # 统一默认值为10
        num_sequences_per_batch = getattr(self.config, 'sequence_batch_size', 32)
        
        # 2. 获取采样器
        # 【关键修复】启用基于 Chunk 的序列切分，使用技能步长 k 作为切分长度
        # 这解决了只使用完整 rollout 进行训练导致的显存爆炸和梯度问题
        sequence_sampler = self.rollout_buffer.get_discoverer_sampler(
            ppo_epochs, 
            num_sequences_per_batch, 
            chunk_length=self.config.k,
            device=self.device,
            cache_tensors=getattr(self.config, 'cache_update_tensors', False)
        )
        
        if sequence_sampler is None:
            main_logger.error("无法获取Discoverer采样器，跳过更新。")
            return 0, 0, 0, 0, 0, 0, 0, 0, 0

        # --- 在所有PPO Epochs开始前，一次性更新统计量 ---
        if self.config.use_valuenorm and self.value_norm_discoverer is not None:
            all_returns = self.rollout_buffer.returns.reshape(-1)
            self.value_norm_discoverer.update(all_returns)
            main_logger.info(f"Discoverer ValueNorm已更新. 新均值: {self.value_norm_discoverer.mean:.4f}, 新标准差: {np.sqrt(self.value_norm_discoverer.var):.4f}")

        obs_norm_mean = obs_norm_var = None
        if getattr(self.config, 'use_obsnorm', False) and self.obs_norm is not None:
            obs_norm_mean = torch.as_tensor(self.obs_norm.mean, device=self.device, dtype=torch.float32)
            obs_norm_var = torch.as_tensor(self.obs_norm.var, device=self.device, dtype=torch.float32)

        state_norm_mean = state_norm_var = None
        if getattr(self.config, 'use_statenorm', True) and self.state_norm is not None:
            state_norm_mean = torch.as_tensor(self.state_norm.mean, device=self.device, dtype=torch.float32)
            state_norm_var = torch.as_tensor(self.state_norm.var, device=self.device, dtype=torch.float32)

        discoverer_value_norm_tensors = self._value_norm_tensors(self.value_norm_discoverer)

        sequence_sampler_iter = iter(sequence_sampler)
        while True:
            profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
            try:
                batch = next(sequence_sampler_iter)
            except StopIteration:
                break
            if self.enable_runtime_profiling:
                self._add_update_profile('discoverer_sampler', time.perf_counter() - profile_start)

            # ... (与旧版本类似的PPO更新逻辑) ...
            # 此处省略了详细的PPO更新代码，因为它与旧版本非常相似，
            # 关键区别在于现在的数据来自一个干净的、无污染的采样器。
            # 核心是使用 batch 中的 'advantages' 和 'returns'
            
            # 提取并转换数据
            observations_seq = batch['observations'].to(self.device)
            agent_skills_seq = batch['agent_skills'].to(self.device)
            actions_seq = batch['actions'].to(self.device)
            global_states_seq = batch['global_states'].to(self.device)
            joint_observations_seq = batch.get('joint_observations')
            if joint_observations_seq is not None:
                joint_observations_seq = joint_observations_seq.to(self.device)

            # 手动应用归一化 (使用当前统计量，不更新统计量，且保持在GPU上)
            if obs_norm_mean is not None:
                observations_seq = (observations_seq - obs_norm_mean) / torch.sqrt(obs_norm_var + 1e-8)
                observations_seq = torch.clamp(observations_seq, -10.0, 10.0)
                if joint_observations_seq is not None:
                    joint_observations_seq = (joint_observations_seq - obs_norm_mean) / torch.sqrt(obs_norm_var + 1e-8)
                    joint_observations_seq = torch.clamp(joint_observations_seq, -10.0, 10.0)

            if state_norm_mean is not None:
                global_states_seq = (global_states_seq - state_norm_mean) / torch.sqrt(state_norm_var + 1e-8)
                global_states_seq = torch.clamp(global_states_seq, -10.0, 10.0)
            team_skills_seq = batch['team_skills'].to(self.device)
            initial_hxs = batch['initial_hxs'].to(self.device)
            dones_seq = batch['dones'].to(self.device)
            initial_critic_hxs = batch['initial_critic_hxs'].to(self.device)
            
            old_log_probs_seq = batch['log_probs'].to(self.device)
            advantages_seq = batch['advantages'].to(self.device)
            returns_seq = batch['returns'].to(self.device)
            value_preds_seq = batch['value_preds'].to(self.device)
            masks_seq = batch['masks'].to(self.device)

            # 重新评估序列。保持 evaluate_sequence 的外部行为不变，但在热路径拆开
            # actor/critic 计时，方便确认 update 内部真实瓶颈。
            eval_total_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
            if dones_seq.dim() > 2:
                dones_for_masks = dones_seq.squeeze(-1)
            else:
                dones_for_masks = dones_seq
            masks_for_eval = (1 - dones_for_masks.float())
            compact_context_seq = None
            if self.use_low_level_compact and self.low_level_compact_extractor is not None:
                if joint_observations_seq is None:
                    raise RuntimeError("use_compact_in_low_level_actor=True requires joint_observations in rollout sampler")
                T_ctx, B_ctx = global_states_seq.shape[:2]
                compact_context_flat = self._compute_low_level_compact_context(
                    global_states_seq.reshape(T_ctx * B_ctx, self.config.state_dim),
                    joint_observations_seq.reshape(T_ctx * B_ctx, self.config.n_agents, self.config.obs_dim),
                )
                compact_context_seq = compact_context_flat.reshape(T_ctx, B_ctx, -1)

            profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
            with self._update_autocast():
                actor_observations_seq = self.skill_discoverer._apply_compact_context(
                    observations_seq,
                    compact_context_seq,
                    self.skill_discoverer.actor_context_adapter,
                )
                new_log_probs, entropy = self.skill_discoverer.actor.evaluate_actions(
                    actor_observations_seq,
                    initial_hxs,
                    actions_seq,
                    masks_for_eval,
                    agent_skills_seq
                )
            if self.enable_runtime_profiling:
                self._sync_cuda_for_profile()
                self._add_update_profile('discoverer_actor_eval', time.perf_counter() - profile_start)

            profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
            with self._update_autocast():
                critic_states_seq = self.skill_discoverer._apply_compact_context(
                    global_states_seq,
                    compact_context_seq,
                    self.skill_discoverer.critic_context_adapter,
                )
                new_values, _ = self.skill_discoverer.critic(
                    critic_states_seq,
                    initial_critic_hxs,
                    masks_for_eval,
                    team_skills_seq
                )
            if self.enable_runtime_profiling:
                self._sync_cuda_for_profile()
                self._add_update_profile('discoverer_critic_eval', time.perf_counter() - profile_start)
                self._add_update_profile('discoverer_eval', time.perf_counter() - eval_total_start)

            profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
            # 展平数据
            advantages_flat = advantages_seq.reshape(-1)
            returns_flat = returns_seq.reshape(-1)
            value_preds_flat = value_preds_seq.reshape(-1)
            old_log_probs_flat = old_log_probs_seq.reshape(-1)
            new_log_probs_flat = new_log_probs.reshape(-1)
            new_values_flat = new_values.reshape(-1)
            masks_flat = masks_seq.reshape(-1)

            # 在计算损失前，使用掩码过滤无效数据
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

            # 【内部 ValueNorm】价值损失计算（MAPPO 风格）
            # 假设网络输出 new_values_flat 为归一化后的 value，
            # 使用 RunningMeanStd 对真实尺度的 returns_flat 进行归一化后作为目标。
            if discoverer_value_norm_tensors is not None:
                mean, var, std = discoverer_value_norm_tensors
                # 将真实尺度 returns 归一化为 target
                returns_norm = (returns_flat - mean) / std
                if hasattr(self.config, "value_clip"):
                    returns_norm = torch.clamp(
                        returns_norm,
                        -self.config.value_clip,
                        self.config.value_clip,
                    )

                # new_values_flat 被视为 V_norm，直接拟合归一化后的 target
                value_loss = F.mse_loss(new_values_flat, returns_norm.detach())
            else:
                # 未启用 ValueNorm 时，直接在真实尺度上拟合
                value_loss = F.mse_loss(new_values_flat, returns_flat.detach())
            
            # Entropy pressure can be adaptive for HA-CTSE exploration. The
            # old HMASD path keeps using the fixed config value unless the
            # config explicitly enables entropy targets.
            low_level_entropy_coef = (
                self.low_level_entropy_coef
                if self.use_entropy_targets
                else self.config.lambda_l
            )
            entropy_loss = -entropy * low_level_entropy_coef

            # 解耦更新
            actor_loss = policy_loss + entropy_loss
            critic_loss = self.config.value_loss_coef * value_loss

            if self.enable_runtime_profiling:
                self._sync_cuda_for_profile()
                self._add_update_profile('discoverer_loss', time.perf_counter() - profile_start)

            profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
            self.discoverer_actor_optimizer.zero_grad()
            self.discoverer_critic_optimizer.zero_grad()
            combined_loss = actor_loss + critic_loss
            if self.update_amp_enabled:
                self.update_grad_scaler.scale(combined_loss).backward()
                self.update_grad_scaler.unscale_(self.discoverer_actor_optimizer)
                self.update_grad_scaler.unscale_(self.discoverer_critic_optimizer)
            else:
                combined_loss.backward()
            actor_clip_params = self.skill_discoverer.actor_update_parameters()
            if self.low_level_compact_extractor is not None:
                actor_clip_params = actor_clip_params + list(self.low_level_compact_extractor.parameters())
            torch.nn.utils.clip_grad_norm_(actor_clip_params, self.config.max_grad_norm)
            torch.nn.utils.clip_grad_norm_(self.skill_discoverer.critic_update_parameters(), self.config.max_grad_norm)
            if self.enable_runtime_profiling:
                self._sync_cuda_for_profile()
                self._add_update_profile('discoverer_backward', time.perf_counter() - profile_start)

            profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
            if self.update_amp_enabled:
                self.update_grad_scaler.step(self.discoverer_actor_optimizer)
                self.update_grad_scaler.step(self.discoverer_critic_optimizer)
                self.update_grad_scaler.update()
            else:
                self.discoverer_actor_optimizer.step()
                self.discoverer_critic_optimizer.step()
            if self.r39_native_hmasd_toy:
                self.native_toy_optimizer_updates['low_actor'] += 1
                self.native_toy_optimizer_updates['low_critic'] += 1
            if self.enable_runtime_profiling:
                self._sync_cuda_for_profile()
                self._add_update_profile('discoverer_optimizer', time.perf_counter() - profile_start)

            total_loss = total_loss + (actor_loss + critic_loss).detach()
            total_policy_loss = total_policy_loss + policy_loss.detach()
            total_value_loss = total_value_loss + value_loss.detach()
            total_entropy_loss = total_entropy_loss + entropy_loss.detach()
            update_count += 1

        # 计算平均值
        avg_loss = (total_loss / update_count).item() if update_count > 0 else 0
        avg_policy_loss = (total_policy_loss / update_count).item() if update_count > 0 else 0
        avg_value_loss = (total_value_loss / update_count).item() if update_count > 0 else 0
        avg_entropy_loss = (total_entropy_loss / update_count).item() if update_count > 0 else 0
        
        profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
        # 其他统计信息
        data = self.rollout_buffer._get_full_rollout_data()
        if data and "masks" in data:
            valid_mask = data["masks"].astype(bool)
            if np.any(valid_mask):
                avg_intrinsic_reward = float(np.mean(data["rewards"][valid_mask]))
                avg_env_comp = float(np.mean(data["reward_env"][valid_mask]))
                avg_team_disc_comp = float(np.mean(data["reward_team_disc"][valid_mask]))
                avg_ind_disc_comp = float(np.mean(data["reward_ind_disc"][valid_mask]))
                avg_discoverer_val = float(np.mean(data["values"][valid_mask]))
            else:
                avg_intrinsic_reward = avg_env_comp = avg_team_disc_comp = avg_ind_disc_comp = avg_discoverer_val = 0.0
        else:
            avg_intrinsic_reward = avg_env_comp = avg_team_disc_comp = avg_ind_disc_comp = avg_discoverer_val = 0.0
        low_level_entropy_coef = (
            self.low_level_entropy_coef
            if self.use_entropy_targets
            else self.config.lambda_l
        )
        action_entropy_val = -avg_entropy_loss / low_level_entropy_coef if low_level_entropy_coef > 0 else 0
        if update_count > 0 and self.use_entropy_targets:
            self._adapt_entropy_coef(
                'low_level_entropy_coef',
                action_entropy_val,
                self._low_level_entropy_target(),
            )
            self.config.lambda_l = self.low_level_entropy_coef
        if self.enable_runtime_profiling:
            self._add_update_profile('discoverer_stats', time.perf_counter() - profile_start)

        main_logger.info(f"Discoverer更新完成: 平均损失={avg_loss:.4f}")
        
        return avg_loss, avg_policy_loss, avg_value_loss, action_entropy_val, \
               avg_intrinsic_reward, avg_env_comp, avg_team_disc_comp, avg_ind_disc_comp, avg_discoverer_val

    def _update_discriminators_fused(
        self,
        team_states,
        team_skills_tensor,
        team_compacts,
        ind_observations,
        ind_team_skills_cond,
        ind_agent_skills,
        ind_compacts,
        update_epochs,
        batch_size,
        noise_std,
    ):
        num_team_samples = int(team_states.size(0)) if team_states is not None else 0
        num_ind_samples = int(ind_observations.size(0)) if ind_observations is not None else 0

        team_loss_accumulated, team_update_count = 0.0, 0
        ind_loss_accumulated, ind_update_count = 0.0, 0

        profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
        for _ in range(update_epochs):
            team_indices = torch.randperm(num_team_samples, device=self.device) if num_team_samples > 0 else None
            ind_indices = torch.randperm(num_ind_samples, device=self.device) if num_ind_samples > 0 else None
            max_samples = max(num_team_samples, num_ind_samples)

            for start_idx in range(0, max_samples, batch_size):
                loss_terms = []
                update_team = False
                update_individual = False

                if team_indices is not None and start_idx < num_team_samples:
                    end_idx = min(start_idx + batch_size, num_team_samples)
                    batch_indices = team_indices[start_idx:end_idx]
                    batch_states = team_states[batch_indices]
                    batch_skills = team_skills_tensor[batch_indices]
                    batch_compacts = team_compacts[batch_indices] if team_compacts is not None else None
                    with torch.no_grad():
                        state_noise = torch.randn_like(batch_states) * noise_std
                    team_disc_logits = self._team_discriminator_logits(batch_states + state_noise, batch_compacts)
                    team_disc_loss = F.cross_entropy(team_disc_logits, batch_skills)
                    loss_terms.append(team_disc_loss)
                    update_team = True
                    team_loss_accumulated += team_disc_loss.item()
                    team_update_count += 1

                if ind_indices is not None and start_idx < num_ind_samples:
                    end_idx = min(start_idx + batch_size, num_ind_samples)
                    batch_indices = ind_indices[start_idx:end_idx]
                    batch_obs = ind_observations[batch_indices]
                    batch_team_skills = ind_team_skills_cond[batch_indices]
                    batch_agent_skills = ind_agent_skills[batch_indices]
                    batch_compacts = ind_compacts[batch_indices] if ind_compacts is not None else None
                    with torch.no_grad():
                        obs_noise = torch.randn_like(batch_obs) * noise_std
                    agent_disc_logits = self._individual_discriminator_logits(
                        batch_obs + obs_noise,
                        batch_team_skills,
                        batch_compacts,
                    )
                    agent_disc_loss = F.cross_entropy(agent_disc_logits, batch_agent_skills)
                    loss_terms.append(agent_disc_loss)
                    update_individual = True
                    ind_loss_accumulated += agent_disc_loss.item()
                    ind_update_count += 1

                if not loss_terms:
                    continue

                fused_loss = torch.stack(loss_terms).sum()
                if update_team:
                    self.team_discriminator_optimizer.zero_grad()
                if update_individual:
                    self.individual_discriminator_optimizer.zero_grad()
                fused_loss.backward()
                # The legacy combined Adam held independent per-parameter
                # moments but clipped the fused parameter inventory together.
                # Retain that clipping contract while separating optimizer state.
                active_parameters = []
                if update_team:
                    active_parameters.extend(self.team_discriminator.parameters())
                if update_individual:
                    active_parameters.extend(self.individual_discriminator.parameters())
                torch.nn.utils.clip_grad_norm_(active_parameters, self.config.max_grad_norm)
                if update_team:
                    self.team_discriminator_optimizer.step()
                if update_individual:
                    self.individual_discriminator_optimizer.step()
                if self.r39_native_hmasd_toy:
                    self.native_toy_optimizer_updates['discriminator'] += 1

        if self.enable_runtime_profiling:
            self._add_update_profile('disc_train', time.perf_counter() - profile_start)

        team_avg_loss = team_loss_accumulated / max(1, team_update_count)
        ind_avg_loss = ind_loss_accumulated / max(1, ind_update_count)
        total_loss = team_avg_loss + ind_avg_loss

        profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
        with torch.no_grad():
            team_acc = (
                (self._team_discriminator_logits(team_states, team_compacts).argmax(-1) == team_skills_tensor).float().mean().item()
                if team_states is not None else 0.0
            )
            ind_acc = (
                (self._individual_discriminator_logits(ind_observations, ind_team_skills_cond, ind_compacts).argmax(-1) == ind_agent_skills).float().mean().item()
                if ind_observations is not None else 0.0
            )
        if self.enable_runtime_profiling:
            self._add_update_profile('disc_accuracy', time.perf_counter() - profile_start)

        main_logger.info(
            f"判别器更新完成(fused): Team Loss={team_avg_loss:.4f}, Ind Loss={ind_avg_loss:.4f}, "
            f"Total={total_loss:.4f}, Team Acc={team_acc:.4f}, Ind Acc={ind_acc:.4f}"
        )
        self.last_discriminator_metrics = {
            'total_loss': float(total_loss),
            'team_loss': float(team_avg_loss),
            'individual_loss': float(ind_avg_loss),
            'team_accuracy': float(team_acc),
            'individual_accuracy': float(ind_acc),
        }

        return total_loss

    
    def update_discriminators(self, num_steps, noise_std=None):
        """
        【论文一致性修复】更新技能判别器网络
        
        严格按照论文 Algorithm 1 的伪代码逻辑：
        - 使用当前 rollout 收集的**全部数据**进行更新（On-Policy）
        - 在 Policy 更新之后执行（由 update() 方法保证调用顺序）
        - 更新完成后，discriminator_buffer 将在 clear_buffers() 中被清空
        
        【噪声注入】在训练判别器时为输入添加高斯噪声，提高鲁棒性：
        - 平滑流形，防止判别器过拟合
        - 只在更新参数时添加噪声，计算奖励时不加
        - 不给离散的技能标签添加噪声
        
        参数:
            num_steps: 当前 rollout 的有效步数
            noise_std: 噪声标准差，默认从 config.discriminator_noise_std 获取，若无则为 0.05
        
        返回值：team_disc_avg_loss + ind_disc_avg_loss（两个判别器损失之和）
        """
        
        # 获取噪声标准差，优先使用参数，其次使用配置，默认0.05
        if noise_std is None:
            noise_std = getattr(self.config, 'discriminator_noise_std', 0.05)
        
        update_epochs = getattr(self.config, 'ppo_epochs', 10)
        profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
        all_data = self.discriminator_buffer.get_all()
        
        if len(all_data) == 0:
            main_logger.warning("判别器Buffer为空，跳过判别器更新")
            return 0
        
        team_data = [d for d in all_data if d['type'] == 'team']
        ind_data = [d for d in all_data if d['type'] == 'individual']
        
        main_logger.info(f"判别器On-Policy更新: 团队数据={len(team_data)}个, 个体数据={len(ind_data)}个")
        
        # 预处理数据为张量
        team_states, team_skills_tensor, team_compacts = None, None, None
        if len(team_data) > 0:
            team_states = torch.FloatTensor(np.array([d['state'] for d in team_data])).to(self.device)
            team_skills_tensor = torch.LongTensor([d['skill'] for d in team_data]).to(self.device)
            if self.use_compact_team_discriminator:
                team_compacts = torch.FloatTensor(
                    np.array([
                        d.get('compact', np.zeros(int(getattr(self.config, 'opt_compact_dim', 1)), dtype=np.float32))
                        for d in team_data
                    ])
                ).to(self.device)

        ind_observations, ind_team_skills_cond, ind_agent_skills, ind_compacts = None, None, None, None
        if len(ind_data) > 0:
            ind_observations = torch.FloatTensor(np.array([d['obs'] for d in ind_data])).to(self.device)
            ind_team_skills_cond = torch.LongTensor([d['team_skill'] for d in ind_data]).to(self.device)
            ind_agent_skills = torch.LongTensor([d['skill'] for d in ind_data]).to(self.device)
            if self.use_compact_individual_discriminator:
                ind_compacts = torch.FloatTensor(
                    np.array([
                        d.get('compact', np.zeros(int(getattr(self.config, 'opt_compact_dim', 1)), dtype=np.float32))
                        for d in ind_data
                    ])
                ).to(self.device)
        if self.enable_runtime_profiling:
            self._add_update_profile('disc_pack', time.perf_counter() - profile_start)

        if getattr(self.config, 'discriminator_update_mode', 'fused') == 'fused':
            return self._update_discriminators_fused(
                team_states,
                team_skills_tensor,
                team_compacts,
                ind_observations,
                ind_team_skills_cond,
                ind_agent_skills,
                ind_compacts,
                update_epochs,
                getattr(self.config, 'discriminator_batch_size', self.config.batch_size),
                noise_std,
            )
        
        # 【修复】分别追踪两个判别器的损失
        team_loss_accumulated, team_update_count = 0.0, 0
        ind_loss_accumulated, ind_update_count = 0.0, 0
        
        batch_size = getattr(self.config, 'discriminator_batch_size', self.config.batch_size)

        profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
        for epoch in range(update_epochs):
            # 团队技能判别器更新
            if team_states is not None:
                num_team_samples = len(team_data)
                indices = torch.randperm(num_team_samples)
                for start_idx in range(0, num_team_samples, batch_size):
                    end_idx = min(start_idx + batch_size, num_team_samples)
                    batch_indices = indices[start_idx:end_idx]
                    batch_states = team_states[batch_indices]
                    batch_skills = team_skills_tensor[batch_indices]
                    batch_compacts = team_compacts[batch_indices] if team_compacts is not None else None
                    
                    # ================= [噪声注入 - 团队判别器] =================
                    # 为状态输入添加高斯噪声，提高判别器鲁棒性
                    # 注意：不给离散的 batch_skills (Z) 加噪声！
                    with torch.no_grad():
                        state_noise = torch.randn_like(batch_states) * noise_std
                    noisy_batch_states = batch_states + state_noise
                    # ================= [噪声注入结束] =================
                    
                    team_disc_logits = self._team_discriminator_logits(noisy_batch_states, batch_compacts)
                    team_disc_loss = F.cross_entropy(team_disc_logits, batch_skills)
                    
                    self.team_discriminator_optimizer.zero_grad()
                    team_disc_loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.team_discriminator.parameters(), self.config.max_grad_norm)
                    self.team_discriminator_optimizer.step()
                    if self.r39_native_hmasd_toy:
                        self.native_toy_optimizer_updates['discriminator'] += 1
                    
                    team_loss_accumulated += team_disc_loss.item()
                    team_update_count += 1
            
            # 个体技能判别器更新
            if ind_observations is not None:
                num_ind_samples = len(ind_data)
                indices = torch.randperm(num_ind_samples)
                for start_idx in range(0, num_ind_samples, batch_size):
                    end_idx = min(start_idx + batch_size, num_ind_samples)
                    batch_indices = indices[start_idx:end_idx]
                    batch_obs = ind_observations[batch_indices]
                    batch_team_skills = ind_team_skills_cond[batch_indices]
                    batch_agent_skills = ind_agent_skills[batch_indices]
                    batch_compacts = ind_compacts[batch_indices] if ind_compacts is not None else None
                    
                    # ================= [噪声注入 - 个体判别器] =================
                    # 为观测输入添加高斯噪声，提高判别器鲁棒性
                    # 注意：不给离散的 batch_team_skills (Z) 和 batch_agent_skills (z) 加噪声！
                    with torch.no_grad():
                        obs_noise = torch.randn_like(batch_obs) * noise_std
                    noisy_batch_obs = batch_obs + obs_noise
                    # ================= [噪声注入结束] =================
                    
                    agent_disc_logits = self._individual_discriminator_logits(
                        noisy_batch_obs,
                        batch_team_skills,
                        batch_compacts,
                    )
                    agent_disc_loss = F.cross_entropy(agent_disc_logits, batch_agent_skills)
                    
                    self.individual_discriminator_optimizer.zero_grad()
                    agent_disc_loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.individual_discriminator.parameters(), self.config.max_grad_norm)
                    self.individual_discriminator_optimizer.step()
                    if self.r39_native_hmasd_toy:
                        self.native_toy_optimizer_updates['discriminator'] += 1
                    
                    ind_loss_accumulated += agent_disc_loss.item()
                    ind_update_count += 1
        if self.enable_runtime_profiling:
            self._add_update_profile('disc_train', time.perf_counter() - profile_start)
        
        # 【修复】分别计算两个判别器的平均损失，然后求和
        team_avg_loss = team_loss_accumulated / max(1, team_update_count)
        ind_avg_loss = ind_loss_accumulated / max(1, ind_update_count)
        total_loss = team_avg_loss + ind_avg_loss
        
        # 计算准确率
        profile_start = time.perf_counter() if self.enable_runtime_profiling else 0.0
        with torch.no_grad():
            team_acc = (
                (self._team_discriminator_logits(team_states, team_compacts).argmax(-1) == team_skills_tensor).float().mean().item()
                if team_states is not None else 0.0
            )
            ind_acc = (
                (self._individual_discriminator_logits(ind_observations, ind_team_skills_cond, ind_compacts).argmax(-1) == ind_agent_skills).float().mean().item()
                if ind_observations is not None else 0.0
            )
        if self.enable_runtime_profiling:
            self._add_update_profile('disc_accuracy', time.perf_counter() - profile_start)
        
        main_logger.info(f"判别器更新完成: Team Loss={team_avg_loss:.4f}, Ind Loss={ind_avg_loss:.4f}, "
                        f"Total={total_loss:.4f}, Team Acc={team_acc:.4f}, Ind Acc={ind_acc:.4f}")
        self.last_discriminator_metrics = {
            'total_loss': float(total_loss),
            'team_loss': float(team_avg_loss),
            'individual_loss': float(ind_avg_loss),
            'team_accuracy': float(team_acc),
            'individual_accuracy': float(ind_acc),
        }
        
        return total_loss

    def get_policy_diagnostics(self):
        """Return bounded-policy exploration diagnostics for experiment comparison."""
        diagnostics = {}
        action_out = getattr(
            getattr(getattr(self.skill_discoverer, 'actor', None), 'act', None),
            'action_out',
            None,
        )
        logstd_module = getattr(action_out, 'logstd', None)
        logstd_bias = getattr(logstd_module, '_bias', None)
        if logstd_bias is not None:
            values = logstd_bias.detach().float().cpu().numpy().reshape(-1)
            lower = float(getattr(action_out, 'logstd_min', -np.inf))
            upper = float(getattr(action_out, 'logstd_max', np.inf))
            values = np.clip(values, lower, upper)
            diagnostics.update({
                'action_logstd_mean': float(np.mean(values)),
                'action_logstd_min': float(np.min(values)),
                'action_logstd_max': float(np.max(values)),
                'action_logstd_values': values.tolist(),
            })
        if self.training_info.get('action_entropy'):
            diagnostics['action_entropy'] = float(self.training_info['action_entropy'][-1])
        else:
            diagnostics['action_entropy'] = float(self.last_action_entropy)
        diagnostics.update({
            f'discriminator_{key}': value
            for key, value in self.last_discriminator_metrics.items()
        })
        return diagnostics
    
    def update(self, last_values, dones, steps_in_buffer, last_state=None, last_observations=None):
        """
        【论文一致性修复】更新所有网络
        
        参数:
            last_values: 最后一步的价值估计（低层）
            dones: 最后一步的终止标志
            steps_in_buffer: 缓冲区中的步数
            last_state: 最后一步的全局状态（新增，用于Coordinator Bootstrap）
            last_observations: 最后一步的观测（新增，用于Coordinator Bootstrap）

        严格按照论文 Algorithm 1 的 Training Phase 顺序：
        1. 先更新 Coordinator (高层策略) - 使用"旧" Discriminator 计算的内在奖励
        2. 再更新 Discoverer (低层策略) - 使用"旧" Discriminator 计算的内在奖励
        3. 最后更新 Discriminator - 使用当前 rollout 的全部数据进行 On-Policy 更新
        
        这确保了：
        - Policy 的更新依赖于 Discriminator 更新前输出的 Reward 值
        - Discriminator 更新后，下一轮采样的内在奖励会基于新的 Discriminator
        - 形成完整的逻辑闭环
        """
        # 更新全局步数
        self.global_step += 1
        main_logger.debug(f"HMASDAgent.update (step {self.global_step}): 开始更新所有网络，有效步数: {steps_in_buffer}")

        # [新增] 熵系数退火逻辑
        if self.use_entropy_annealing:
            # 计算当前环境总步数 (估算)
            steps_per_update = self.config.num_envs * self.config.rollout_length
            current_env_steps = self.global_step * steps_per_update
            
            # 计算进度 (0.0 -> 1.0)
            progress = min(current_env_steps / self.entropy_anneal_steps, 1.0)
            
            if self.entropy_anneal_schedule == 'cosine':
                progress_adjusted = 0.5 * (1 - np.cos(np.pi * progress))
            else: # linear
                progress_adjusted = progress
            
            # 更新 config 中的熵系数
            self.config.lambda_h = self.lambda_h_initial + (self.lambda_h_final - self.lambda_h_initial) * progress_adjusted
            self.config.lambda_l = self.lambda_l_initial + (self.lambda_l_final - self.lambda_l_initial) * progress_adjusted
            
            # 记录退火状态 (Debug级别)
            if self.global_step % 100 == 0:
                main_logger.debug(f"熵系数退火 [进度: {progress_adjusted:.4f}]: lambda_h={self.config.lambda_h:.6f}, lambda_l={self.config.lambda_l:.6f}")

        # 【Coordinator Bootstrap 修复】计算高层策略的 Bootstrap Values
        coord_bootstrap_values = None
        if last_state is not None and last_observations is not None:
            try:
                with torch.no_grad():
                    # 标准化输入
                    last_state_norm = self._normalize_states(last_state)
                    last_obs_norm = self._normalize_observations(last_observations)
                    
                    # 转换为 Tensor
                    state_tensor = torch.FloatTensor(last_state_norm).to(self.device)
                    obs_tensor = torch.FloatTensor(last_obs_norm).to(self.device)
                    
                    if self.use_ha_ctse:
                        num_envs = state_tensor.shape[0]
                        prev_skills_np = np.asarray([
                            self.env_agent_skills.get(i, np.zeros(self.config.n_agents, dtype=np.int64))
                            for i in range(num_envs)
                        ], dtype=np.int64)
                        ages_np = np.asarray([
                            self.env_skill_ages.get(i, np.zeros(self.config.n_agents, dtype=np.int64))
                            for i in range(num_envs)
                        ], dtype=np.int64)
                        result = self.ha_ctse_editor.assign_and_value_batch(
                            state_tensor,
                            obs_tensor,
                            torch.as_tensor(prev_skills_np, dtype=torch.long, device=self.device),
                            torch.as_tensor(ages_np, dtype=torch.long, device=self.device),
                            torch.as_tensor(prev_skills_np < 0, dtype=torch.bool, device=self.device),
                            deterministic=True,
                        )
                        state_val = result['state_values']
                        agent_values_tensor = result['agent_values']
                        if self.config.use_valuenorm and self.value_norm_coordinator is not None:
                            state_val = self._denormalize_values(state_val, self.value_norm_coordinator)
                            agent_values_tensor = torch.stack([
                                self._denormalize_values(
                                    agent_values_tensor[:, agent_idx:agent_idx + 1],
                                    self.value_norm_coordinator,
                                ).squeeze(-1)
                                for agent_idx in range(agent_values_tensor.size(1))
                            ], dim=1)
                        agent_vals_np = agent_values_tensor.cpu().numpy()
                    else:
                        # 计算价值
                        state_val, agent_vals, _ = self.skill_coordinator.get_value(state_tensor, obs_tensor)

                        # 【反归一化修复】确保Bootstrap Value是真实尺度
                        if self.config.use_valuenorm and self.value_norm_coordinator is not None:
                            state_val = self._denormalize_values(state_val, self.value_norm_coordinator)
                            agent_vals = [self._denormalize_values(v, self.value_norm_coordinator) for v in agent_vals]

                        # 转换为 Numpy 格式
                        # state_val: [num_envs, 1] -> [num_envs]
                        # agent_vals: list of [num_envs, 1] -> [num_envs, n_agents]
                        if agent_vals is not None and len(agent_vals) > 0:
                            agent_vals_np = np.array([v.cpu().numpy().flatten() for v in agent_vals]).T
                        else:
                            agent_vals_np = np.zeros((self.config.num_envs, self.config.n_agents))
                        
                    coord_bootstrap_values = {
                        'state': state_val.cpu().numpy().flatten(),
                        'agents': agent_vals_np
                    }
                    main_logger.info("已使用最新的next_state计算Coordinator Bootstrap Values")
            except Exception as e:
                main_logger.error(f"计算Coordinator Bootstrap Values时出错: {e}")
        else:
            main_logger.warning("未提供last_state或last_observations，Coordinator Bootstrap将使用回退机制")

        # 更频繁地检查环境贡献情况（从1000步降至200步）
        if self.global_step % 200 == 0:
            use_legacy_contribution_monitor = self._should_use_legacy_high_level_contribution_monitor()
            # 获取所有环境的贡献情况
            env_contributions = {}
            for env_id in range(self.config.num_envs):
                env_contributions[env_id] = self.high_level_samples_by_env.get(env_id, 0)
            
            if use_legacy_contribution_monitor:
                # 旧HMASD fixed-k路径才允许按环境贡献数强制闭合高层样本。
                low_contribution_envs = {env_id: count for env_id, count in env_contributions.items() if count < 3}
                if low_contribution_envs:
                    main_logger.info(f"以下环境贡献样本较少，将强制其在下一个技能周期结束时贡献: {low_contribution_envs}")
                    for env_id in low_contribution_envs:
                        self.force_high_level_collection[env_id] = True
                        self.env_reward_thresholds[env_id] = 0.0
            else:
                process_stats = (
                    self.process_segment_buffer.stats()
                    if self.process_segment_buffer is not None
                    else {}
                )
                remaining_values = []
                for value in self.env_skill_duration_remaining.values():
                    remaining_values.extend(np.asarray(value, dtype=np.float32).reshape(-1).tolist())
                remaining_mean = float(np.mean(remaining_values)) if remaining_values else 0.0
                remaining_max = float(np.max(remaining_values)) if remaining_values else 0.0
                main_logger.debug(
                    "HA-CTSE过程高层贡献诊断: "
                    f"累计高层样本={self.high_level_samples_total}, "
                    f"贡献环境数={sum(1 for count in env_contributions.values() if count > 0)}/{self.config.num_envs}, "
                    f"duration_remaining_mean={remaining_mean:.2f}, "
                    f"duration_remaining_max={remaining_max:.2f}, "
                    f"process_stats={process_stats}"
                )
            
            # 记录rollout缓冲区状态（统一缓冲区）
            rollout_buffer_pos = self.global_step % self.rollout_buffer.num_steps
            rollout_buffer_full = rollout_buffer_pos == self.rollout_buffer.num_steps - 1
            main_logger.debug(f"当前rollout缓冲区状态: {rollout_buffer_pos}/{self.rollout_buffer.num_steps} (当前/总容量), 完整: {rollout_buffer_full}")
            
            # 检查高层策略数据是否足够
            rollout_data_for_check = self.rollout_buffer._get_full_rollout_data()
            if rollout_data_for_check:
                high_level_data_count = np.sum(rollout_data_for_check['high_level_valid_mask'][:rollout_buffer_pos])
            else:
                high_level_data_count = 0
            
            # 如果高层数据增长过慢，强制所有环境进行贡献
            if (
                use_legacy_contribution_monitor
                and high_level_data_count < 10
                and self.global_step > 5000
            ):  # 至少需要10个高层决策样本
                main_logger.warning(f"高层策略数据增长过慢 (有效高层样本: {high_level_data_count})，强制所有环境贡献样本")
                for env_id in range(self.config.num_envs):
                    self.force_high_level_collection[env_id] = True
                    self.env_reward_thresholds[env_id] = 0.0
            elif not use_legacy_contribution_monitor:
                main_logger.debug(
                    "HA-CTSE过程高层replay诊断: "
                    f"rollout有效闭合样本={high_level_data_count}, "
                    "未按HMASD fixed-k阈值触发强制采样"
                )
            
            # 计算环境贡献分布统计（供训练脚本记录）
            contrib_data = np.zeros(self.config.num_envs)
            for env_id, count in env_contributions.items():
                contrib_data[env_id] = count
            # 计算贡献标准差，衡量是否平衡
            contrib_std = np.std(contrib_data)
            # 计算有效贡献环境数量
            contrib_envs = np.sum(contrib_data > 0)
        
        # ============================================================
        # 【论文一致性修复】Training Phase 执行顺序
        # ============================================================

        process_metrics = self.update_process_exploration_from_segments()
        
        # 步骤 1: 更新高层技能协调器 (Coordinator)
        # 使用基于"旧" Discriminator 计算的内在奖励进行 PPO 更新
        # 【Bootstrap修复】传入计算好的 bootstrap_values
        if getattr(self.config, 'disable_high_level_training', False):
            coordinator_loss = coordinator_policy_loss = coordinator_value_loss = 0.0
            team_skill_entropy = agent_skill_entropy = 0.0
            mean_coord_state_val = mean_coord_agent_val = mean_high_level_reward = cd_loss_val = 0.0
        else:
            coordinator_loss, coordinator_policy_loss, coordinator_value_loss, team_skill_entropy, agent_skill_entropy, \
            mean_coord_state_val, mean_coord_agent_val, mean_high_level_reward, cd_loss_val = self.update_coordinator(
                steps_in_buffer, bootstrap_values=coord_bootstrap_values
            )
        
        # 步骤 2: 更新低层技能发现器 (Discoverer)
        # 同样使用基于"旧" Discriminator 计算的内在奖励进行 PPO 更新
        discoverer_loss, discoverer_policy_loss, discoverer_value_loss, action_entropy, \
        avg_intrinsic_reward, avg_env_comp, avg_team_disc_comp, avg_ind_disc_comp, \
        avg_discoverer_val = self.update_discoverer_from_rollout(last_values, dones)
        
        # 步骤 3: 更新技能判别器 (Discriminator)
        # 【关键】在 Policy 更新完成后，使用当前 rollout 的全部数据进行 On-Policy 更新
        # 这确保了：
        # - 当前 rollout 的内在奖励是基于"旧" Discriminator 计算的（已在上面使用）
        # - 更新后的 Discriminator 将用于下一轮采样时计算新的内在奖励
        if getattr(self.config, 'disable_discriminator_training', False):
            discriminator_loss = 0.0
        else:
            discriminator_loss = self.update_discriminators(steps_in_buffer)
        
        # 更新学习率调度器
        if getattr(self.config, 'use_lr_decay', False) and self.global_step <= self.config.lr_decay_steps:
            if self.coordinator_scheduler is not None:
                self.coordinator_scheduler.step()
            # 【关键修复】更新解耦后的Discoverer调度器
            if hasattr(self, 'discoverer_actor_scheduler') and self.discoverer_actor_scheduler is not None:
                self.discoverer_actor_scheduler.step()
            if hasattr(self, 'discoverer_critic_scheduler') and self.discoverer_critic_scheduler is not None:
                self.discoverer_critic_scheduler.step()
            if self.team_discriminator_scheduler is not None:
                self.team_discriminator_scheduler.step()
            if self.individual_discriminator_scheduler is not None:
                self.individual_discriminator_scheduler.step()

        # 更新训练信息
        self.training_info['high_level_loss'].append(coordinator_loss)
        self.training_info['low_level_loss'].append(discoverer_loss)
        self.training_info['discriminator_loss'].append(discriminator_loss)
        self.training_info['team_skill_entropy'].append(team_skill_entropy) # 真正的团队技能熵
        self.training_info['agent_skill_entropy'].append(agent_skill_entropy) # 个体技能熵，不再是占位符
        self.training_info['action_entropy'].append(action_entropy)
        self.last_action_entropy = float(action_entropy)
        
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
        current_disc_actor_lr = self.discoverer_actor_optimizer.param_groups[0]['lr']
        current_disc_critic_lr = self.discoverer_critic_optimizer.param_groups[0]['lr']
        current_team_discriminator_lr = (
            self.team_discriminator_optimizer.param_groups[0]['lr']
            if self.team_discriminator_optimizer is not None
            else 0.0
        )
        current_individual_discriminator_lr = (
            self.individual_discriminator_optimizer.param_groups[0]['lr']
            if self.individual_discriminator_optimizer is not None
            else 0.0
        )
        if current_team_discriminator_lr != current_individual_discriminator_lr:
            raise RuntimeError('split discriminator learning rates diverged')
        current_process_lr = (
            self.process_optimizer.param_groups[0]['lr']
            if self.process_optimizer is not None
            else 0.0
        )
        
        learning_rates = {
            'coordinator_lr': current_coord_lr,
            'discoverer_actor_lr': current_disc_actor_lr,
            'discoverer_critic_lr': current_disc_critic_lr,
            'discriminator_lr': current_team_discriminator_lr,
            'team_discriminator_lr': current_team_discriminator_lr,
            'individual_discriminator_lr': current_individual_discriminator_lr,
            'process_encoder_lr': current_process_lr,
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
        update_result = {
            'discriminator_loss': discriminator_loss,
            'discriminator_team_loss': self.last_discriminator_metrics.get('team_loss', 0.0),
            'discriminator_individual_loss': self.last_discriminator_metrics.get('individual_loss', 0.0),
            'discriminator_team_accuracy': self.last_discriminator_metrics.get('team_accuracy', 0.0),
            'discriminator_individual_accuracy': self.last_discriminator_metrics.get('individual_accuracy', 0.0),
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
        update_result.update(learning_rates)
        update_result.update(process_metrics)
        if bool(getattr(self.config, 'audit_high_replay_likelihood', False)):
            update_result.update({
                f'high_replay_likelihood_{key}': value
                for key, value in self.high_replay_likelihood_metrics.items()
            })
        if self.use_ha_ctse and hasattr(self, 'last_ha_ctse_metrics'):
            update_result.update(self.last_ha_ctse_metrics)
            update_result['entropy_coef_low_level'] = float(
                getattr(self, 'low_level_entropy_coef', getattr(self.config, 'lambda_l', 0.0))
            )
        return update_result
    
    def save_model(self, path):
        """保存模型"""
        checkpoint = {
            'skill_coordinator': self.skill_coordinator.state_dict(),
            'ha_ctse_editor': self.ha_ctse_editor.state_dict() if self.ha_ctse_editor is not None else None,
            'low_level_compact_extractor': (
                self.low_level_compact_extractor.state_dict()
                if self.low_level_compact_extractor is not None
                else None
            ),
            'process_encoder': self.process_encoder.state_dict() if self.process_encoder is not None else None,
            'process_outcome_predictor': (
                self.process_outcome_predictor.state_dict()
                if self.process_outcome_predictor is not None
                else None
            ),
            'process_contrastive_head': (
                self.process_contrastive_head.state_dict()
                if self.process_contrastive_head is not None
                else None
            ),
            'skill_discoverer': self.skill_discoverer.state_dict(),
            'team_discriminator': (
                self.team_discriminator.state_dict()
                if self.team_discriminator is not None
                else None
            ),
            'individual_discriminator': (
                self.individual_discriminator.state_dict()
                if self.individual_discriminator is not None
                else None
            ),
            'coordinator_optimizer': self.coordinator_optimizer.state_dict(),
            'discoverer_actor_optimizer': self.discoverer_actor_optimizer.state_dict(),
            'discoverer_critic_optimizer': self.discoverer_critic_optimizer.state_dict(),
            'discriminator_optimizer_schema': 'split_team_individual_adam_v1',
            'team_discriminator_optimizer': (
                self.team_discriminator_optimizer.state_dict()
                if self.team_discriminator_optimizer is not None
                else None
            ),
            'individual_discriminator_optimizer': (
                self.individual_discriminator_optimizer.state_dict()
                if self.individual_discriminator_optimizer is not None
                else None
            ),
            'team_discriminator_scheduler': (
                self.team_discriminator_scheduler.state_dict()
                if self.team_discriminator_scheduler is not None
                else None
            ),
            'individual_discriminator_scheduler': (
                self.individual_discriminator_scheduler.state_dict()
                if self.individual_discriminator_scheduler is not None
                else None
            ),
            'process_optimizer': self.process_optimizer.state_dict() if self.process_optimizer is not None else None,
            'config': self.config,
            'policy_interface': {
                'action_dim': int(getattr(self.config, 'action_dim', 0)),
                'action_space_type': getattr(self.config, 'action_space_type', None),
                'continuous_action_distribution': getattr(
                    self.config, 'continuous_action_distribution', 'gaussian'
                ),
                'scenario7_interface_version': getattr(
                    self.config, 'scenario7_interface_version', None
                ),
                'scenario7_reward_model': getattr(
                    self.config, 'scenario7_reward_model', None
                ),
                'scenario7_reward_variant': getattr(
                    self.config, 'scenario7_reward_variant', None
                ),
                'scenario7_experiment_arm': getattr(
                    self.config, 'scenario7_experiment_arm', None
                ),
                'battery_capacity_wh': getattr(
                    self.config, 'battery_capacity_wh', None
                ),
                'return_cost_cap': getattr(
                    self.config, 'return_cost_cap', None
                ),
            },
            'training_interface': {
                'skill_interval': int(getattr(self.config, 'k', 0)),
                'rollout_length': int(getattr(self.config, 'rollout_length', 0)),
                'episode_length': int(getattr(self.config, 'episode_length', 0)),
            },
            'training_diagnostics': {
                'last_discriminator_metrics': dict(self.last_discriminator_metrics),
                'last_process_metrics': dict(getattr(self, 'last_process_metrics', {})),
                'last_action_entropy': float(self.last_action_entropy),
            },
            'training_progress': dict(getattr(self, 'training_progress', {})),
            'rollout_sampler_rng': {
                'schema': 'hmasd_rollout_sampler_rng_v1',
                'streams': {
                    'main_rollout': {
                        'seed': int(self.rollout_sampler_seed),
                        'state': self.rollout_buffer.get_sampler_rng_state(),
                    },
                },
            },
            'scenario7_safety_dual_state': dict(
                getattr(self, 'scenario7_safety_dual_state', {})
            ),
            # 注意：不再保存discriminator_buffer，因为Discriminator现在是On-Policy模式
        }
        if bool(getattr(self.config, 'audit_high_replay_likelihood', False)):
            checkpoint['training_diagnostics']['high_replay_likelihood'] = dict(
                self.high_replay_likelihood_metrics
            )
        
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
        
        # 保存观测和状态标准化统计信息（新增）
        normalization_state = {}
        if getattr(self.config, 'use_obsnorm', False) and self.obs_norm is not None:
            normalization_state['obs_norm'] = {
                'mean': self.obs_norm.mean,
                'var': self.obs_norm.var,
                'count': self.obs_norm.count
            }
        if getattr(self.config, 'use_statenorm', True) and self.state_norm is not None:
            normalization_state['state_norm'] = {
                'mean': self.state_norm.mean,
                'var': self.state_norm.var,
                'count': self.state_norm.count
            }
        if normalization_state:
            checkpoint['normalization_state'] = normalization_state
            main_logger.info("已保存观测和状态标准化统计信息")
        
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
        saved_training_progress = checkpoint.get('training_progress', {})
        if isinstance(saved_training_progress, dict):
            self.training_progress = dict(saved_training_progress)
            saved_optimizer_updates = saved_training_progress.get(
                'native_toy_optimizer_updates', {}
            )
            if not isinstance(saved_optimizer_updates, dict):
                raise ValueError('native toy optimizer progress must be a dictionary')
            if saved_optimizer_updates:
                native_toy_optimizer_updates = getattr(
                    self, 'native_toy_optimizer_updates', None
                )
                if not isinstance(native_toy_optimizer_updates, dict):
                    raise ValueError(
                        'checkpoint contains native toy optimizer progress but '
                        'the current agent has no matching counter inventory'
                    )
                native_toy_optimizer_updates.update(
                    {
                        key: int(value)
                        for key, value in saved_optimizer_updates.items()
                        if key in native_toy_optimizer_updates
                    }
                )

        is_scenario7 = (
            getattr(self.config, 'scenario', None) == 7
            or bool(getattr(self.config, 'energy_stage', None))
        )
        if is_scenario7:
            interface = checkpoint.get('policy_interface')
            expected = {
                'action_dim': int(getattr(self.config, 'action_dim', 4)),
                'action_space_type': getattr(self.config, 'action_space_type', 'continuous'),
                'continuous_action_distribution': getattr(
                    self.config, 'continuous_action_distribution', 'tanh_gaussian'
                ),
                'scenario7_interface_version': getattr(
                    self.config, 'scenario7_interface_version', 3
                ),
                'scenario7_reward_model': getattr(
                    self.config,
                    'scenario7_reward_model',
                    'constrained_qos_safety_pbrs_v2',
                ),
                'scenario7_reward_variant': getattr(
                    self.config,
                    'scenario7_reward_variant',
                    'qos_fixed_safety_graph_pbrs',
                ),
                'scenario7_experiment_arm': getattr(
                    self.config, 'scenario7_experiment_arm', 'C'
                ),
                'battery_capacity_wh': getattr(
                    self.config, 'battery_capacity_wh', 160.0
                ),
                'return_cost_cap': getattr(
                    self.config, 'return_cost_cap', 1.0
                ),
            }
            if interface is None:
                raise ValueError(
                    "拒绝加载旧版 Scenario 7 检查点：缺少 policy_interface 元数据，"
                    "该检查点通常使用旧的三维动作接口。请使用修复后的四维接口重新训练。"
                )
            mismatches = {
                key: (interface.get(key), expected_value)
                for key, expected_value in expected.items()
                if interface.get(key) != expected_value
            }
            if mismatches:
                details = ", ".join(
                    f"{key}: checkpoint={actual!r}, expected={expected_value!r}"
                    for key, (actual, expected_value) in mismatches.items()
                )
                raise ValueError(
                    f"Scenario 7 检查点接口不兼容（{details}）。"
                    "旧版动作、reward模型或电池参数不能加载到当前Scenario 7 V5接口。"
                )

            training_interface = checkpoint.get('training_interface', {})
            checkpoint_config = checkpoint.get('config')
            checkpoint_k = training_interface.get(
                'skill_interval',
                getattr(checkpoint_config, 'k', None),
            )
            expected_k = int(getattr(self.config, 'k', 0))
            if checkpoint_k is None:
                raise ValueError(
                    "拒绝加载 Scenario 7 检查点：无法确定其技能间隔 k。"
                    "请从头训练当前技能间隔实验。"
                )
            if int(checkpoint_k) != expected_k:
                raise ValueError(
                    f"Scenario 7 技能间隔不兼容：checkpoint k={checkpoint_k}，"
                    f"当前实验 k={expected_k}。修改 k 后高层奖励时间尺度变化，禁止续训。"
                )

            saved_diagnostics = checkpoint.get('training_diagnostics', {})
            if saved_diagnostics:
                self.last_discriminator_metrics = dict(
                    saved_diagnostics.get(
                        'last_discriminator_metrics',
                        self.last_discriminator_metrics,
                    )
                )
                self.last_action_entropy = float(
                    saved_diagnostics.get('last_action_entropy', self.last_action_entropy)
                )
                saved_high_replay = saved_diagnostics.get('high_replay_likelihood', {})
                if isinstance(saved_high_replay, dict):
                    for key in self.high_replay_likelihood_metrics:
                        if key in saved_high_replay:
                            self.high_replay_likelihood_metrics[key] = saved_high_replay[key]
            self.scenario7_safety_dual_state = dict(
                checkpoint.get('scenario7_safety_dual_state', {})
            )

        sampler_rng = checkpoint.get('rollout_sampler_rng')
        if sampler_rng is not None:
            if (
                not isinstance(sampler_rng, dict)
                or set(sampler_rng) != {'schema', 'streams'}
                or sampler_rng['schema'] != 'hmasd_rollout_sampler_rng_v1'
                or not isinstance(sampler_rng['streams'], dict)
                or set(sampler_rng['streams']) != {'main_rollout'}
            ):
                raise ValueError('rollout sampler RNG checkpoint metadata is invalid')
            main_rollout_rng = sampler_rng['streams']['main_rollout']
            if (
                not isinstance(main_rollout_rng, dict)
                or set(main_rollout_rng) != {'seed', 'state'}
                or isinstance(main_rollout_rng['seed'], bool)
                or not isinstance(main_rollout_rng['seed'], int)
                or main_rollout_rng['seed'] < 0
            ):
                raise ValueError('main rollout sampler RNG checkpoint is invalid')
            self.rollout_buffer.set_sampler_rng_state(main_rollout_rng['state'])
            self.rollout_sampler_seed = int(main_rollout_rng['seed'])
        else:
            main_logger.warning(
                '旧检查点没有Rollout sampler RNG状态；仅可视为显式warm-start，'
                '不得宣称严格轨迹续训。'
            )
        
        # 使用 strict=False 来处理模型架构不匹配的问题
        # 这允许加载匹配的层，同时忽略不匹配的层（如旧的transformer vs 新的opt，或变化的智能体数量）
        self.skill_coordinator.load_state_dict(checkpoint['skill_coordinator'], strict=False)
        if self.ha_ctse_editor is not None and checkpoint.get('ha_ctse_editor') is not None:
            self.ha_ctse_editor.load_state_dict(checkpoint['ha_ctse_editor'], strict=False)
        if self.low_level_compact_extractor is not None and checkpoint.get('low_level_compact_extractor') is not None:
            self.low_level_compact_extractor.load_state_dict(
                checkpoint['low_level_compact_extractor'],
                strict=False,
            )
        if self.process_encoder is not None and checkpoint.get('process_encoder') is not None:
            self.process_encoder.load_state_dict(checkpoint['process_encoder'], strict=False)
        if self.process_outcome_predictor is not None and checkpoint.get('process_outcome_predictor') is not None:
            self.process_outcome_predictor.load_state_dict(checkpoint['process_outcome_predictor'], strict=False)
        if self.process_contrastive_head is not None and checkpoint.get('process_contrastive_head') is not None:
            self.process_contrastive_head.load_state_dict(checkpoint['process_contrastive_head'], strict=False)
        self.skill_discoverer.load_state_dict(checkpoint['skill_discoverer'], strict=False)
        if self.team_discriminator is not None and checkpoint.get('team_discriminator') is not None:
            self.team_discriminator.load_state_dict(checkpoint['team_discriminator'], strict=False)
        if self.individual_discriminator is not None and checkpoint.get('individual_discriminator') is not None:
            self.individual_discriminator.load_state_dict(checkpoint['individual_discriminator'], strict=False)
        
        # 加载优化器状态（如果存在）
        if 'coordinator_optimizer' in checkpoint:
            self.coordinator_optimizer.load_state_dict(checkpoint['coordinator_optimizer'])
            main_logger.info("已恢复Coordinator优化器状态")
        if 'discoverer_actor_optimizer' in checkpoint and 'discoverer_critic_optimizer' in checkpoint:
            try:
                self.discoverer_actor_optimizer.load_state_dict(checkpoint['discoverer_actor_optimizer'])
                self.discoverer_critic_optimizer.load_state_dict(checkpoint['discoverer_critic_optimizer'])
                main_logger.info("已恢复Discoverer Actor和Critic优化器状态")
            except ValueError as e:
                main_logger.warning(f"Discoverer优化器状态与当前参数组不兼容，跳过恢复: {e}")
        elif 'discoverer_optimizer' in checkpoint: # 兼容旧模型
            try:
                self.discoverer_actor_optimizer.load_state_dict(checkpoint['discoverer_optimizer'])
                self.discoverer_critic_optimizer.load_state_dict(checkpoint['discoverer_optimizer'])
                main_logger.warning("从旧的组合优化器状态恢复Discoverer Actor和Critic优化器")
            except ValueError as e:
                main_logger.warning(f"旧Discoverer优化器状态与当前参数组不兼容，跳过恢复: {e}")
        if self.team_discriminator_optimizer is not None:
            split_optimizer_fields = (
                'team_discriminator_optimizer',
                'individual_discriminator_optimizer',
            )
            has_split_optimizer = any(
                field in checkpoint for field in split_optimizer_fields
            )
            if has_split_optimizer:
                if (
                    checkpoint.get('discriminator_optimizer_schema')
                    != 'split_team_individual_adam_v1'
                    or any(checkpoint.get(field) is None for field in split_optimizer_fields)
                ):
                    raise ValueError('split discriminator optimizer checkpoint is incomplete')
                self.team_discriminator_optimizer.load_state_dict(
                    checkpoint['team_discriminator_optimizer']
                )
                self.individual_discriminator_optimizer.load_state_dict(
                    checkpoint['individual_discriminator_optimizer']
                )
                main_logger.info("已恢复拆分的Team和Individual Discriminator优化器状态")
            elif checkpoint.get('discriminator_optimizer') is not None:
                team_state, individual_state = (
                    _split_legacy_discriminator_adam_state_dict(
                        checkpoint['discriminator_optimizer'],
                        self.team_discriminator.parameters(),
                        self.individual_discriminator.parameters(),
                    )
                )
                self.team_discriminator_optimizer.load_state_dict(team_state)
                self.individual_discriminator_optimizer.load_state_dict(
                    individual_state
                )
                main_logger.info("已严格拆分并恢复旧版Discriminator Adam状态")

            split_scheduler_fields = (
                'team_discriminator_scheduler',
                'individual_discriminator_scheduler',
            )
            has_split_scheduler = any(
                checkpoint.get(field) is not None for field in split_scheduler_fields
            )
            if has_split_scheduler:
                if (
                    self.team_discriminator_scheduler is None
                    or self.individual_discriminator_scheduler is None
                    or any(checkpoint.get(field) is None for field in split_scheduler_fields)
                ):
                    raise ValueError('split discriminator scheduler checkpoint is incompatible')
                self.team_discriminator_scheduler.load_state_dict(
                    checkpoint['team_discriminator_scheduler']
                )
                self.individual_discriminator_scheduler.load_state_dict(
                    checkpoint['individual_discriminator_scheduler']
                )
            elif (
                checkpoint.get('discriminator_scheduler') is not None
                and self.team_discriminator_scheduler is not None
                and self.individual_discriminator_scheduler is not None
            ):
                self.team_discriminator_scheduler.load_state_dict(
                    checkpoint['discriminator_scheduler']
                )
                self.individual_discriminator_scheduler.load_state_dict(
                    checkpoint['discriminator_scheduler']
                )
        if self.process_optimizer is not None and checkpoint.get('process_optimizer') is not None:
            try:
                self.process_optimizer.load_state_dict(checkpoint['process_optimizer'])
                main_logger.info("已恢复Process Encoder优化器状态")
            except ValueError as e:
                main_logger.warning(f"Process Encoder优化器状态与当前参数组不兼容，跳过恢复: {e}")
        
        # 恢复判别器缓冲区
        if 'discriminator_buffer' in checkpoint:
            self.discriminator_buffer = checkpoint['discriminator_buffer']
            main_logger.info(f"已恢复Discriminator缓冲区，当前大小: {len(self.discriminator_buffer)}")
        else:
            main_logger.warning("在checkpoint中未找到Discriminator缓冲区，将使用新的空缓冲区")
        
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
        
        # 加载观测和状态标准化统计信息（新增）
        if 'normalization_state' in checkpoint:
            normalization_state = checkpoint['normalization_state']
            
            if 'obs_norm' in normalization_state and getattr(self.config, 'use_obsnorm', False) and self.obs_norm is not None:
                obs_state = normalization_state['obs_norm']
                self.obs_norm.mean = obs_state['mean']
                self.obs_norm.var = obs_state['var']
                self.obs_norm.count = obs_state['count']
                main_logger.info("已恢复观测标准化统计信息")
                
            if 'state_norm' in normalization_state and getattr(self.config, 'use_statenorm', True) and self.state_norm is not None:
                state_state = normalization_state['state_norm']
                self.state_norm.mean = state_state['mean']
                self.state_norm.var = state_state['var']
                self.state_norm.count = state_state['count']
                main_logger.info("已恢复状态标准化统计信息")
        else:
            if getattr(self.config, 'use_obsnorm', False):
                main_logger.warning("观测标准化已启用，但checkpoint中未找到标准化状态，将使用初始化值")
            if getattr(self.config, 'use_statenorm', True):
                main_logger.warning("状态标准化已启用，但checkpoint中未找到标准化状态，将使用初始化值")
        
        main_logger.info(f"模型已从 {path} 加载 (使用非严格模式)")
