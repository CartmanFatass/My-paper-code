import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import copy
import random
from torch.optim import Adam
from collections import deque
import os

# 尝试导入PyTorch Geometric
try:
    from torch_geometric.data import Data, Batch
except ImportError:
    Data = None
    Batch = None

# 尝试导入科学计算库
try:
    from sklearn.cluster import KMeans
    from scipy.spatial.distance import cdist
except ImportError:
    KMeans = None
    cdist = None

from hmasd.logging import main_logger
from gnn_hmasd.networks import GNNRoleAssigner, TaskExecutor
from hmasd.utils import ReplayBuffer, clone_replay_data, compute_ordered_trajectory_gae

STRICT_CHECKPOINT_VERSION = 4
GNN_LEGACY_WARM_START_KEYS = frozenset({'role_assigner', 'task_executor'})


def _capture_torch_sampling_rng_state():
    cuda_initialized = bool(torch.cuda.is_initialized())
    cuda_states = torch.cuda.get_rng_state_all() if cuda_initialized else []
    return {
        'cpu': torch.get_rng_state().clone(),
        'cuda_initialized': cuda_initialized,
        'cuda_device_count': len(cuda_states),
        'cuda': [state.clone() for state in cuda_states],
    }


def _validate_torch_sampling_rng_state(state):
    required = {'cpu', 'cuda_initialized', 'cuda_device_count', 'cuda'}
    if not isinstance(state, dict) or set(state) != required:
        raise ValueError("invalid Torch policy-sampling RNG checkpoint schema")
    cpu = state['cpu']
    if not torch.is_tensor(cpu) or cpu.dtype != torch.uint8 or cpu.ndim != 1 or not cpu.numel():
        raise ValueError("invalid Torch CPU policy-sampling RNG state")
    if not isinstance(state['cuda_initialized'], bool):
        raise ValueError("invalid Torch CUDA RNG initialization marker")
    if not isinstance(state['cuda_device_count'], int) or state['cuda_device_count'] < 0:
        raise ValueError("invalid Torch CUDA RNG device count")
    cuda_states = state['cuda']
    if not isinstance(cuda_states, list):
        raise ValueError("invalid Torch CUDA policy-sampling RNG state list")
    if not state['cuda_initialized']:
        if state['cuda_device_count'] != 0 or cuda_states:
            raise ValueError("Torch checkpoint has CUDA RNG states without initialization")
        return
    if not torch.cuda.is_available():
        raise ValueError("Torch checkpoint requires CUDA RNG state but CUDA is unavailable")
    runtime_count = torch.cuda.device_count()
    if runtime_count != state['cuda_device_count'] or len(cuda_states) != runtime_count:
        raise ValueError("Torch CUDA RNG device-count/state mismatch")
    for cuda_state in cuda_states:
        if (
            not torch.is_tensor(cuda_state) or cuda_state.dtype != torch.uint8
            or cuda_state.ndim != 1 or not cuda_state.numel()
        ):
            raise ValueError("invalid Torch CUDA policy-sampling RNG state")


def _restore_torch_sampling_rng_state(state):
    torch.set_rng_state(state['cpu'].cpu())
    if state['cuda_initialized']:
        torch.cuda.set_rng_state_all([item.cpu() for item in state['cuda']])


def _canonical_device_identity(device):
    device = torch.device(device)
    index = device.index
    if device.type == 'cuda' and index is None:
        index = torch.cuda.current_device()
    return {'type': device.type, 'index': index}


def _canonical_module_device(module, label):
    devices = {parameter.device for parameter in module.parameters()}
    devices.update(buffer.device for buffer in module.buffers())
    if len(devices) != 1:
        raise ValueError(f"{label} must have exactly one policy parameter device")
    return _canonical_device_identity(next(iter(devices)))

class GNNHMASDAgent:
    """
    基于GNN的层次化多智能体技能发现（GNN-HMASD）代理
    """
    def __init__(self, config, log_dir='logs', device=None):
        """
        初始化GNN-HMASD代理
        """
        if Data is None or KMeans is None or cdist is None:
            raise ImportError("GNNHMASDAgent 需要 PyTorch Geometric, scikit-learn, 和 scipy。请安装这些库。")

        self.config = config
        self.device = device if device is not None else torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        main_logger.info(f"使用设备: {self.device}")

        # 创建网络
        self.role_assigner = GNNRoleAssigner(config).to(self.device)
        self.task_executor = TaskExecutor(config).to(self.device)

        # 创建优化器
        self.assigner_optimizer = Adam(self.role_assigner.parameters(), lr=config.lr_coordinator)
        self.executor_optimizer = Adam(self.task_executor.parameters(), lr=config.lr_discoverer)

        # 创建经验回放缓冲区
        # 高层缓冲区需要存储图数据，这需要特殊处理
        self.high_level_buffer = [] # 使用一个简单的列表来存储图数据
        base_seed = int(getattr(config, 'seed', 0))
        self.low_level_buffer = ReplayBuffer(
            config.buffer_size,
            rng_seed=int(getattr(config, 'gnn_low_replay_seed', base_seed + 1701)),
        )
        self._high_replay_rng = np.random.default_rng(
            int(getattr(config, 'gnn_high_replay_seed', base_seed + 1702))
        )

        self.global_step = 0
        
        # 环境状态跟踪
        self.env_roles = {}
        self.env_timers = {}
        self.env_reward_sums = {}
        self._pending_high_samples = {}
        self._pending_low_segments = {}
        self._unbootstrapped_low_rows = {}
        self._pending_high_segments = {}
        self._low_episode_ids = {}
        self._low_timesteps = {}
        self._low_segment_ids = {}
        self._high_episode_ids = {}
        self._high_timesteps = {}
        self._high_segment_ids = {}
        self._low_rows_since_update = 0
        self._high_rows_since_update = 0
        self._collection_tokens = {}
        self._collection_frontiers = {}
        self._collection_token_counter = 0
        
        # 初始化用户聚类模型
        if self.config.num_user_clusters > 0:
            self.kmeans = KMeans(n_clusters=self.config.num_user_clusters, random_state=0, n_init=10)

    def _build_graph(self, uav_positions, user_positions, gbs_positions):
        """
        将环境实体位置构建成一个图。

        参数:
            uav_positions: 无人机位置 [n_uavs, 3]
            user_positions: 用户位置 [n_users, 2]
            gbs_positions: 地面基站位置 [n_gbs, 3]

        返回:
            graph_data: PyTorch Geometric的Data对象
        """
        # 1. 节点定义
        n_uavs = uav_positions.shape[0]
        n_gbs = gbs_positions.shape[0]
        
        # 用户聚类
        if self.config.num_user_clusters > 0 and len(user_positions) > self.config.num_user_clusters:
            user_cluster_centers = self.kmeans.fit(user_positions).cluster_centers_
            user_nodes_pos = np.c_[user_cluster_centers, np.zeros(self.config.num_user_clusters)] # 添加z=0
        else: # 如果用户数少于聚类数，直接使用用户作为节点
            user_nodes_pos = np.c_[user_positions, np.zeros(len(user_positions))]
        
        n_user_nodes = user_nodes_pos.shape[0]

        # 合并所有节点位置
        all_positions = np.vstack([uav_positions, user_nodes_pos, gbs_positions])
        num_nodes = all_positions.shape[0]

        # 2. 节点特征 (Node Features)
        # [pos_x, pos_y, pos_z, type_specific_1, type_onehot...]
        node_features = torch.zeros((num_nodes, self.config.node_feature_dim), device=self.device)
        
        # 归一化位置
        norm_positions = torch.tensor(all_positions / self.config.area_size, dtype=torch.float32, device=self.device)
        node_features[:, :3] = norm_positions

        # 类型嵌入 (One-hot)
        uav_type_emb = F.one_hot(torch.tensor(0), num_classes=4).float()
        user_type_emb = F.one_hot(torch.tensor(1), num_classes=4).float()
        gbs_type_emb = F.one_hot(torch.tensor(2), num_classes=4).float()

        # 填充特征
        # UAVs
        node_features[:n_uavs, 4:] = uav_type_emb
        # User Clusters
        node_features[n_uavs:n_uavs+n_user_nodes, 4:] = user_type_emb
        # GBS
        node_features[n_uavs+n_user_nodes:, 4:] = gbs_type_emb

        # 3. 边 (Edges) - 基于距离
        dist_matrix = cdist(all_positions, all_positions)
        adj = dist_matrix < self.config.graph_build_d_max
        np.fill_diagonal(adj, False) # 移除自环
        
        edge_index = torch.tensor(np.array(np.where(adj)), dtype=torch.long, device=self.device)

        # 4. 创建Data对象
        graph_data = Data(x=node_features, edge_index=edge_index)
        graph_data.uav_mask = torch.zeros(num_nodes, dtype=torch.bool, device=self.device)
        graph_data.uav_mask[:n_uavs] = True

        return graph_data

    def assign_roles(self, uav_positions, user_positions, gbs_positions, deterministic=False):
        """
        使用GNN高层策略分配角色
        """
        graph_data = self._build_graph(uav_positions, user_positions, gbs_positions)
        roles, role_log_probs, _, value = self.role_assigner(graph_data, deterministic)
        return roles, role_log_probs, value, graph_data

    def select_action(self, observations, roles, deterministic=False):
        """
        根据分配的角色选择动作
        """
        obs_tensor = torch.as_tensor(
            np.asarray(observations), dtype=torch.float32, device=self.device
        )
        roles_tensor = torch.tensor(roles, dtype=torch.long, device=self.device)
        
        actions, log_probs, values = self.task_executor(obs_tensor, roles_tensor, deterministic)
        
        return actions.cpu().detach().numpy(), log_probs, values

    @staticmethod
    def _collection_values_equal(left, right):
        if torch.is_tensor(left):
            left = left.detach().cpu().numpy()
        if torch.is_tensor(right):
            right = right.detach().cpu().numpy()
        return np.array_equal(np.asarray(left), np.asarray(right))

    def _register_collection_token(
        self, env_id, observations, actions, roles, log_probs, values, skill_timer
    ):
        if env_id in self._collection_frontiers:
            raise ValueError(f"environment {env_id} has an unconsumed GNN collection token")
        token_id = f"gnn-collection:{self._collection_token_counter}"
        self._collection_token_counter += 1
        self._collection_tokens[token_id] = clone_replay_data({
            'env_id': env_id,
            'observations': observations,
            'actions': actions,
            'roles': roles,
            'old_log_probs': log_probs,
            'old_values': values,
            'skill_timer': int(skill_timer),
        })
        self._collection_frontiers[env_id] = token_id
        return token_id

    def _validate_collection_token(self, obs, actions, info):
        token_id = info.get('collection_token')
        if token_id is None or token_id not in self._collection_tokens:
            raise ValueError("missing, stale, or reused GNN collection token")
        token = self._collection_tokens[token_id]
        env_id = info.get('env_id')
        if (
            token['env_id'] != env_id
            or self._collection_frontiers.get(env_id) != token_id
        ):
            raise ValueError("GNN collection token is not the environment frontier")
        comparisons = (
            ('observation', obs, token['observations']),
            ('action', actions, token['actions']),
            ('role', info.get('roles'), token['roles']),
            ('old log-probability', info.get('action_logprobs'), token['old_log_probs']),
            ('old value', info.get('low_level_values'), token['old_values']),
        )
        for name, supplied, collected in comparisons:
            if supplied is None or not self._collection_values_equal(supplied, collected):
                raise ValueError(f"GNN stored {name} does not match exact collection input")
        if int(info.get('skill_timer', -1)) != token['skill_timer']:
            raise ValueError("GNN skill timer does not match collection frontier")
        return token_id, token

    def step(self, env, ep_t, env_id=0, deterministic=False):
        """
        执行一个环境步骤
        """
        if env_id in self._collection_frontiers:
            raise ValueError(f"environment {env_id} has an unconsumed GNN collection token")
        if env_id not in self.env_timers:
            self.env_timers[env_id] = 0
            self.env_roles[env_id] = None
            self.env_reward_sums[env_id] = 0.0
            self.high_level_obs = None
            self._low_episode_ids[env_id] = 0
            self._high_episode_ids[env_id] = 0
            self._high_timesteps[env_id] = 0
            self._high_segment_ids[env_id] = 0
            self._pending_high_segments[env_id] = []

        if ep_t % self.config.k == 0 or self.env_roles[env_id] is None:
            # 从环境中获取最新的实体位置
            uav_pos = env.uav_positions
            user_pos = env.user_positions
            gbs_pos = env.ground_bs_positions
            
            roles, role_log_probs, high_level_value, graph_data = self.assign_roles(uav_pos, user_pos, gbs_pos, deterministic)

            # A non-terminal high-level transition closes at the preceding
            # environment step, but its one-step bootstrap is only available
            # when the next decision graph is evaluated.  Finalize it here so
            # replay rows never depend on their sampled neighbours.
            previous = self._pending_high_samples.get(env_id)
            if previous is not None and previous.get("closed", False):
                previous["next_value"] = float(high_level_value.detach().reshape(-1)[0].item())
                previous.pop("closed", None)
                self._append_completed_high_transition(env_id, previous)

            self.env_roles[env_id] = roles.detach().cpu().numpy().copy()
            self.env_timers[env_id] = 0
            self.env_reward_sums[env_id] = 0.0
            skill_changed = True
            
            # 存储高层决策信息
            self.high_level_obs = clone_replay_data({
                "graph_data": graph_data,
                "roles": roles,
                "log_probs": role_log_probs,
                "value": high_level_value
            })
            self._pending_high_samples[env_id] = clone_replay_data({
                'graph_data': graph_data,
                'roles': roles.detach(),
                'log_probs': role_log_probs.detach(),
                'old_value': float(high_level_value.detach().reshape(-1)[0].item()),
                'trajectory_id': (
                    f"gnn-high:{env_id}:{self._high_episode_ids[env_id]}:"
                    f"{self._high_segment_ids[env_id]}"
                ),
                'timestep': self._high_timesteps[env_id],
            })
            self._high_timesteps[env_id] += 1
        else:
            self.env_timers[env_id] += 1
            skill_changed = False

        # 从环境中获取最新的局部观测
        observations = [env._get_observation(agent)['obs'] for agent in env.agents]

        # Complete the preceding transition with V(s_{t+1}) evaluated under
        # the roles actually active at s_{t+1}.  This is intentionally delayed
        # until the next policy decision so a skill-boundary role change cannot
        # bootstrap through the stale role.
        observation_tensor = torch.as_tensor(
            np.asarray(observations), dtype=torch.float32, device=self.device
        )
        role_tensor = torch.as_tensor(
            self.env_roles[env_id], dtype=torch.long, device=self.device
        )
        with torch.no_grad():
            bootstrap_values = self.task_executor.get_value(observation_tensor, role_tensor)
        self._complete_low_bootstraps(env_id, bootstrap_values)
        self._maybe_update_executor_at_segment_boundary()

        # If a complete segment triggered an update, this action and its stored
        # old value/log-prob are collected under the updated policy.
        actions, action_logprobs, low_level_values = self.select_action(
            observations, self.env_roles[env_id], deterministic
        )
        action_logprob_array = action_logprobs.detach().cpu().numpy().copy()
        low_value_array = low_level_values.detach().cpu().numpy().copy()
        token_id = self._register_collection_token(
            env_id,
            observations,
            actions,
            self.env_roles[env_id],
            action_logprob_array,
            low_value_array,
            self.env_timers[env_id],
        )

        info = {
            'roles': clone_replay_data(self.env_roles[env_id]),
            'action_logprobs': action_logprob_array.copy(),
            'low_level_values': low_value_array.copy(),
            'skill_changed': skill_changed,
            'skill_timer': self.env_timers[env_id],
            'env_id': env_id,
            'high_level_obs': clone_replay_data(self.high_level_obs) if skill_changed else None,
            'collection_token': token_id,
        }
        return clone_replay_data(actions), info

    def _compute_intrinsic_reward(self, obs, reward, role):
        # 占位符，需要根据具体角色定义来实现
        return self.config.lambda_e * reward

    def _complete_low_bootstraps(self, env_id, low_level_values):
        if len(low_level_values) != self.config.n_agents:
            raise ValueError("low-level bootstrap value count does not match n_agents")
        for i in range(self.config.n_agents):
            key = (env_id, i)
            previous_low_row = self._unbootstrapped_low_rows.pop(key, None)
            if previous_low_row is not None:
                previous_low_row['next_value'] = float(low_level_values[i].item())
                rows = self._pending_low_segments.get(key)
                if rows is None or rows[-1] is not previous_low_row:
                    raise ValueError("low-level bootstrap row is not the trajectory frontier")
                if len(rows) >= self._low_segment_length():
                    self._finalize_low_segment(key)

    def _low_segment_length(self):
        return max(1, int(getattr(
            self.config, 'replay_gae_segment_length', self.config.batch_size
        )))

    def _maybe_update_executor_at_segment_boundary(self):
        if (
            len(self.low_level_buffer) >= self.config.batch_size
            and self._low_rows_since_update >= self.config.batch_size
            and not self._unbootstrapped_low_rows
            and not any(bool(rows) for rows in self._pending_low_segments.values())
        ):
            self.update_executor()

    def _freeze_trajectory_rows(self, rows):
        if not rows:
            raise ValueError("cannot finalize an empty GNN trajectory segment")
        rewards = torch.as_tensor(
            [row['reward'] for row in rows], dtype=torch.float32, device=self.device
        )
        values = torch.as_tensor(
            [row['old_value'] for row in rows], dtype=torch.float32, device=self.device
        )
        next_values = torch.as_tensor(
            [row['next_value'] for row in rows], dtype=torch.float32, device=self.device
        )
        dones = torch.as_tensor(
            [row['done'] for row in rows], dtype=torch.float32, device=self.device
        )
        advantages, returns = compute_ordered_trajectory_gae(
            rewards,
            values,
            next_values,
            dones,
            [row['trajectory_id'] for row in rows],
            [row['timestep'] for row in rows],
            self.config.gamma,
            self.config.gae_lambda,
        )
        frozen = []
        for index, row in enumerate(rows):
            frozen_row = clone_replay_data(row)
            frozen_row['advantage'] = float(advantages[index].item())
            frozen_row['return'] = float(returns[index].item())
            frozen_row.pop('next_value', None)
            frozen.append(frozen_row)
        return frozen

    def _high_segment_length(self):
        return max(1, int(getattr(
            self.config,
            'high_level_replay_gae_segment_length',
            self.config.high_level_batch_size,
        )))

    def _finalize_low_segment(self, key):
        rows = self._pending_low_segments.pop(key, None)
        if not rows:
            raise ValueError(f"no pending low-level trajectory segment for {key}")
        frozen = self._freeze_trajectory_rows(rows)
        for row in frozen:
            self.low_level_buffer.push(row)
        self._low_rows_since_update += len(frozen)
        self._low_segment_ids[key] = self._low_segment_ids.get(key, 0) + 1

    def _append_completed_high_transition(self, env_id, row):
        rows = self._pending_high_segments.setdefault(env_id, [])
        rows.append(clone_replay_data(row))
        if row['done'] or len(rows) >= self._high_segment_length():
            frozen = self._freeze_trajectory_rows(rows)
            self.high_level_buffer.extend(clone_replay_data(frozen))
            self._high_rows_since_update += len(frozen)
            self._pending_high_segments[env_id] = []
            self._high_segment_ids[env_id] = self._high_segment_ids.get(env_id, 0) + 1

    def store_transition(self, obs, next_obs, actions, rewards, dones, info):
        """
        存储经验
        """
        token_id, collection = self._validate_collection_token(obs, actions, info)
        if len(rewards) != self.config.n_agents or len(dones) != self.config.n_agents:
            raise ValueError("GNN reward/done count does not match n_agents")
        if len(next_obs) != self.config.n_agents:
            raise ValueError("GNN next observation count does not match n_agents")
        next_obs_shape = tuple(next_obs.shape) if hasattr(next_obs, 'shape') else np.asarray(next_obs).shape
        collected_obs = collection['observations']
        collected_obs_shape = tuple(collected_obs.shape) if hasattr(collected_obs, 'shape') else np.asarray(collected_obs).shape
        if next_obs_shape != collected_obs_shape:
            raise ValueError("GNN next observation shape does not match collection input")
        # Consume only after every caller-supplied collection field validates.
        del self._collection_tokens[token_id]
        del self._collection_frontiers[collection['env_id']]

        obs = collection['observations']
        actions = collection['actions']
        roles = collection['roles']
        old_log_probs = collection['old_log_probs']
        old_values = collection['old_values']
        next_obs = clone_replay_data(next_obs)
        rewards = clone_replay_data(rewards)
        dones = clone_replay_data(dones)

        # 累积高层奖励
        env_id = info['env_id']
        self.env_reward_sums[env_id] += np.mean(rewards)

        episode_done = bool(any(dones))

        # 存储低层经验
        for i in range(self.config.n_agents):
            intrinsic_reward = self._compute_intrinsic_reward(obs[i], rewards[i], roles[i])
            key = (env_id, i)
            episode_id = self._low_episode_ids.setdefault(env_id, 0)
            timestep = self._low_timesteps.get(key, 0)
            segment_id = self._low_segment_ids.get(key, 0)
            rows = self._pending_low_segments.setdefault(key, [])
            if key in self._unbootstrapped_low_rows:
                raise ValueError(f"low-level trajectory {key} has an unresolved bootstrap")
            row = {
                'obs': clone_replay_data(obs[i]),
                'next_obs': clone_replay_data(next_obs[i]),
                'action': clone_replay_data(actions[i]),
                'reward': float(intrinsic_reward),
                'done': bool(dones[i]) or episode_done,
                'old_log_prob': clone_replay_data(old_log_probs[i]),
                'role': clone_replay_data(roles[i]),
                'old_value': float(old_values[i]),
                'trajectory_id': f"gnn-low:{env_id}:{episode_id}:{i}:{segment_id}",
                'timestep': timestep,
            }
            if episode_done:
                row['next_value'] = 0.0
            else:
                self._unbootstrapped_low_rows[key] = row
            rows.append(row)
            self._low_timesteps[key] = timestep + 1
            if episode_done:
                self._finalize_low_segment(key)

        # 存储高层经验
        if info['skill_timer'] == self.config.k - 1 or any(dones):
            pending = self._pending_high_samples.get(env_id)
            if pending is not None:
                high_level_reward = self.env_reward_sums[env_id]
                pending['reward'] = high_level_reward
                pending['done'] = bool(any(dones))
                if pending['done']:
                    pending['next_value'] = 0.0
                    self._append_completed_high_transition(env_id, pending)
                    del self._pending_high_samples[env_id]
                else:
                    pending['closed'] = True
                self.env_reward_sums[env_id] = 0.0

        if episode_done:
            for i in range(self.config.n_agents):
                key = (env_id, i)
                if key in self._pending_low_segments:
                    raise ValueError(
                        f"terminal low-level trajectory for {key} was not finalized"
                    )
                if key in self._unbootstrapped_low_rows:
                    raise ValueError(
                        f"terminal low-level trajectory for {key} has an unresolved bootstrap"
                    )
                self._low_timesteps[key] = 0
                self._low_segment_ids[key] = 0
            self._low_episode_ids[env_id] = self._low_episode_ids.get(env_id, 0) + 1
            self._high_episode_ids[env_id] = self._high_episode_ids.get(env_id, 0) + 1
            self._high_timesteps[env_id] = 0
            self._high_segment_ids[env_id] = 0

    def update(self):
        if (
            len(self.low_level_buffer) >= self.config.batch_size
            and self._low_rows_since_update >= self.config.batch_size
            and not any(bool(rows) for rows in self._pending_low_segments.values())
        ):
            self.update_executor()
        if (
            len(self.high_level_buffer) >= self.config.high_level_batch_size
            and self._high_rows_since_update >= self.config.high_level_batch_size
            and not any(bool(rows) for rows in self._pending_high_segments.values())
            and not self._pending_high_samples
        ):
            self.update_assigner()
        self.global_step += 1

    def update_executor(self):
        """更新低层TaskExecutor网络"""
        sample = self.low_level_buffer.sample_torch(self.config.batch_size, self.device)
        if sample is None:
            return
        (
            obs,
            _next_obs,
            actions,
            _rewards,
            _dones,
            old_log_probs,
            roles,
            _old_values,
            advantages,
            returns,
        ) = sample
        advantages = (advantages - advantages.mean()) / (advantages.std(unbiased=False) + 1e-8)

        new_log_probs, _entropy, new_values = self.task_executor.evaluate_actions(
            obs, roles, actions
        )
        
        ratio = torch.exp(new_log_probs - old_log_probs)
        surr1 = ratio * advantages
        surr2 = torch.clamp(ratio, 1 - self.config.clip_epsilon, 1 + self.config.clip_epsilon) * advantages
        policy_loss = -torch.min(surr1, surr2).mean()
        value_loss = F.mse_loss(new_values, returns)
        loss = policy_loss + self.config.value_loss_coef * value_loss

        self.executor_optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.task_executor.parameters(), self.config.max_grad_norm)
        self.executor_optimizer.step()
        self._low_rows_since_update = 0

    def update_assigner(self):
        """更新高层GNNRoleAssigner网络"""
        indices = self._high_replay_rng.choice(
            len(self.high_level_buffer),
            self.config.high_level_batch_size,
            replace=False,
        )
        batch = [self.high_level_buffer[int(index)] for index in indices]
        
        old_log_probs = torch.stack([b['log_probs'] for b in batch]).to(self.device)
        advantages = torch.as_tensor(
            [b['advantage'] for b in batch], dtype=torch.float32, device=self.device
        )
        returns = torch.as_tensor(
            [b['return'] for b in batch], dtype=torch.float32, device=self.device
        )
        advantages = (advantages - advantages.mean()) / (advantages.std(unbiased=False) + 1e-8)

        # 从批处理中重新计算新的log_probs和values
        graph_batch = Batch.from_data_list([b['graph_data'] for b in batch]).to(self.device)
        roles_batch = torch.stack([b['roles'] for b in batch]).to(self.device)
        role_log_probs, _role_entropy, new_values, uav_batch = (
            self.role_assigner.evaluate_roles(graph_batch, roles_batch)
        )
        new_log_probs = torch.zeros(
            len(batch), dtype=role_log_probs.dtype, device=self.device
        )
        new_log_probs.index_add_(0, uav_batch, role_log_probs)
        new_values = new_values.reshape(-1)

        # PPO损失
        ratio = torch.exp(new_log_probs - old_log_probs.sum(dim=1))
        surr1 = ratio * advantages
        surr2 = torch.clamp(ratio, 1 - self.config.clip_epsilon, 1 + self.config.clip_epsilon) * advantages
        policy_loss = -torch.min(surr1, surr2).mean()
        value_loss = F.mse_loss(new_values, returns)
        loss = policy_loss + self.config.value_loss_coef * value_loss

        self.assigner_optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.role_assigner.parameters(), self.config.max_grad_norm)
        self.assigner_optimizer.step()

        # 清空高层缓冲区
        self.high_level_buffer.clear()
        self._high_rows_since_update = 0

    def _checkpoint_topology(self):
        role_device = _canonical_module_device(self.role_assigner, 'GNN role assigner')
        executor_device = _canonical_module_device(self.task_executor, 'GNN task executor')
        if role_device != executor_device:
            raise ValueError("GNN policies are split across different parameter devices")
        if role_device != _canonical_device_identity(self.device):
            raise ValueError("GNN sampling device does not match policy parameter device")
        return {
            'n_agents': int(self.config.n_agents),
            'obs_dim': getattr(self.config, 'obs_dim', getattr(self.task_executor, 'obs_dim', None)),
            'action_dim': getattr(
                self.config, 'action_dim', getattr(self.task_executor, 'action_dim', None)
            ),
            'num_roles': getattr(
                self.config, 'num_roles', getattr(self.role_assigner, 'num_roles', None)
            ),
            'node_feature_dim': getattr(
                self.config,
                'node_feature_dim',
                getattr(self.role_assigner, 'node_feature_dim', None),
            ),
            'low_buffer_capacity': int(self.low_level_buffer.capacity),
            'low_segment_length': self._low_segment_length(),
            'high_segment_length': self._high_segment_length(),
            'policy_device': role_device,
        }

    def _validate_trajectory_state(self, state):
        required = {
            'high_level_buffer', 'pending_high_samples', 'pending_low_segments',
            'unbootstrapped_low_keys', 'pending_high_segments', 'low_episode_ids',
            'low_timesteps', 'low_segment_ids', 'high_episode_ids',
            'high_timesteps', 'high_segment_ids', 'low_rows_since_update',
            'high_rows_since_update', 'env_roles', 'env_timers',
            'env_reward_sums', 'high_level_obs', 'global_step',
            'collection_tokens', 'collection_frontiers', 'collection_token_counter',
        }
        if not isinstance(state, dict) or not required.issubset(state):
            raise ValueError("GNN checkpoint is missing strict trajectory state")
        pending_low = state['pending_low_segments']
        unresolved = state['unbootstrapped_low_keys']
        if not isinstance(pending_low, dict) or not isinstance(unresolved, list):
            raise ValueError("invalid GNN low-level frontier containers")
        unresolved = set(tuple(key) for key in unresolved)
        n_agents = int(self.config.n_agents)
        low_required = {
            'obs', 'next_obs', 'action', 'reward', 'done', 'old_log_prob',
            'role', 'old_value', 'trajectory_id', 'timestep',
        }
        topology = self._checkpoint_topology()

        def validate_low_row(row, *, frozen):
            if not isinstance(row, dict) or not low_required.issubset(row):
                raise ValueError("GNN checkpoint contains an invalid low-level row")
            if topology['obs_dim'] is not None and (
                np.asarray(row['obs']).reshape(-1).size != int(topology['obs_dim'])
                or np.asarray(row['next_obs']).reshape(-1).size != int(topology['obs_dim'])
            ):
                raise ValueError("GNN checkpoint observation shape does not match topology")
            if topology['action_dim'] is not None and (
                np.asarray(row['action']).reshape(-1).size != int(topology['action_dim'])
            ):
                raise ValueError("GNN checkpoint action shape does not match topology")
            role = int(np.asarray(row['role']).reshape(-1)[0])
            if topology['num_roles'] is not None and not 0 <= role < int(topology['num_roles']):
                raise ValueError("GNN checkpoint role is outside runtime topology")
            if frozen and not {'advantage', 'return'}.issubset(row):
                raise ValueError("GNN low replay checkpoint contains an unfrozen row")

        low_replay_state = state.get('low_replay_state')
        if low_replay_state is not None:
            for row in low_replay_state.get('buffer', []):
                validate_low_row(row, frozen=True)
        for key, rows in pending_low.items():
            if (
                not isinstance(key, tuple) or len(key) != 2
                or not isinstance(key[1], (int, np.integer))
                or not 0 <= int(key[1]) < n_agents
                or not isinstance(rows, list) or not rows
            ):
                raise ValueError("invalid GNN pending low-level trajectory key")
            for row in rows:
                validate_low_row(row, frozen=False)
            trajectory_ids = {row.get('trajectory_id') for row in rows}
            timesteps = [row.get('timestep') for row in rows]
            if (
                len(trajectory_ids) != 1 or len(timesteps) != len(rows)
                or timesteps != list(range(timesteps[0], timesteps[0] + len(rows)))
            ):
                raise ValueError("GNN pending low-level trajectory order is ambiguous")
            if any(bool(row['done']) for row in rows):
                raise ValueError("GNN checkpoint retained a terminal pending low row")
            missing_bootstraps = [i for i, row in enumerate(rows) if 'next_value' not in row]
            if key in unresolved:
                if missing_bootstraps != [len(rows) - 1]:
                    raise ValueError("GNN unresolved bootstrap is not the trajectory frontier")
            elif missing_bootstraps:
                raise ValueError("GNN pending row is missing its bootstrap marker")
        if unresolved.difference(pending_low):
            raise ValueError("GNN unresolved bootstrap has no pending trajectory")
        env_roles = state['env_roles']
        if not isinstance(env_roles, dict):
            raise ValueError("invalid GNN environment-role frontier")
        for roles in env_roles.values():
            if roles is not None and np.asarray(roles).reshape(-1).size != n_agents:
                raise ValueError("GNN checkpoint role shape does not match topology")

        high_frozen_required = {
            'graph_data', 'roles', 'log_probs', 'old_value', 'reward', 'done',
            'trajectory_id', 'timestep', 'advantage', 'return',
        }
        high_completed_required = high_frozen_required.difference({'advantage', 'return'}) | {
            'next_value'
        }

        def validate_high_row(row, required):
            if not isinstance(row, dict) or not required.issubset(row):
                raise ValueError("GNN checkpoint contains an invalid high-level row")
            roles_size = row['roles'].numel() if torch.is_tensor(row['roles']) else np.asarray(row['roles']).size
            if roles_size != n_agents:
                raise ValueError("GNN checkpoint high-level role shape does not match topology")
            logp_size = row['log_probs'].numel() if torch.is_tensor(row['log_probs']) else np.asarray(row['log_probs']).size
            if logp_size != n_agents:
                raise ValueError("GNN checkpoint high-level log-prob shape does not match topology")
            graph = row['graph_data']
            if not hasattr(graph, 'x') or not hasattr(graph, 'uav_mask'):
                raise ValueError("GNN checkpoint high-level row has no graph topology")
            if topology['node_feature_dim'] is not None and graph.x.shape[-1] != int(
                topology['node_feature_dim']
            ):
                raise ValueError("GNN checkpoint graph feature shape does not match topology")
            mask = graph.uav_mask
            uav_count = int(mask.sum().item()) if getattr(mask, 'dtype', None) == torch.bool else int(mask.numel())
            if uav_count != n_agents:
                raise ValueError("GNN checkpoint graph UAV count does not match topology")

        if not isinstance(state['high_level_buffer'], list):
            raise ValueError("invalid GNN high-level replay container")
        for row in state['high_level_buffer']:
            validate_high_row(row, high_frozen_required)
        for rows in state['pending_high_segments'].values():
            if not isinstance(rows, list):
                raise ValueError("invalid GNN pending high-level segment")
            for row in rows:
                validate_high_row(row, high_completed_required)
        for row in state['pending_high_samples'].values():
            if not isinstance(row, dict):
                raise ValueError("invalid GNN pending high-level sample")
            required = {'graph_data', 'roles', 'log_probs', 'old_value', 'trajectory_id', 'timestep'}
            if row.get('closed', False):
                required |= {'reward', 'done'}
            validate_high_row(row, required)
        for name in (
            'pending_high_samples', 'pending_high_segments', 'low_episode_ids',
            'low_timesteps', 'low_segment_ids', 'high_episode_ids',
            'high_timesteps', 'high_segment_ids', 'env_timers', 'env_reward_sums',
        ):
            if not isinstance(state[name], dict):
                raise ValueError(f"invalid GNN checkpoint container {name}")
        for name in ('low_rows_since_update', 'high_rows_since_update', 'global_step'):
            if not isinstance(state[name], (int, np.integer)) or int(state[name]) < 0:
                raise ValueError(f"invalid GNN checkpoint counter {name}")
        tokens = state['collection_tokens']
        frontiers = state['collection_frontiers']
        if not isinstance(tokens, dict) or not isinstance(frontiers, dict):
            raise ValueError("invalid GNN collection-token checkpoint state")
        if set(frontiers.values()) != set(tokens):
            raise ValueError("GNN collection tokens do not match environment frontiers")
        for env_id, token_id in frontiers.items():
            token = tokens[token_id]
            token_required = {
                'env_id', 'observations', 'actions', 'roles', 'old_log_probs',
                'old_values', 'skill_timer',
            }
            if not isinstance(token, dict) or not token_required.issubset(token):
                raise ValueError("GNN collection token is missing strict replay inputs")
            def first_dim(value):
                return int(value.shape[0]) if hasattr(value, 'shape') else len(value)
            def value_size(value):
                return int(value.numel()) if torch.is_tensor(value) else int(np.asarray(value).size)
            if token.get('env_id') != env_id:
                raise ValueError("GNN collection token has the wrong environment owner")
            if (
                first_dim(token.get('observations')) != n_agents
                or first_dim(token.get('actions')) != n_agents
                or value_size(token.get('roles')) != n_agents
                or value_size(token.get('old_log_probs')) != n_agents
                or value_size(token.get('old_values')) != n_agents
            ):
                raise ValueError("GNN collection-token shape does not match topology")
        if (
            not isinstance(state['collection_token_counter'], (int, np.integer))
            or int(state['collection_token_counter']) < len(tokens)
        ):
            raise ValueError("invalid GNN collection-token counter")

    def save_model(self, path):
        trajectory_state = {
            'high_level_buffer': self.high_level_buffer,
            'pending_high_samples': self._pending_high_samples,
            'pending_low_segments': self._pending_low_segments,
            'unbootstrapped_low_keys': list(self._unbootstrapped_low_rows),
            'pending_high_segments': self._pending_high_segments,
            'low_episode_ids': self._low_episode_ids,
            'low_timesteps': self._low_timesteps,
            'low_segment_ids': self._low_segment_ids,
            'high_episode_ids': self._high_episode_ids,
            'high_timesteps': self._high_timesteps,
            'high_segment_ids': self._high_segment_ids,
            'low_rows_since_update': self._low_rows_since_update,
            'high_rows_since_update': self._high_rows_since_update,
            'env_roles': self.env_roles,
            'env_timers': self.env_timers,
            'env_reward_sums': self.env_reward_sums,
            'high_level_obs': getattr(self, 'high_level_obs', None),
            'global_step': self.global_step,
            'collection_tokens': self._collection_tokens,
            'collection_frontiers': self._collection_frontiers,
            'collection_token_counter': self._collection_token_counter,
        }
        torch.save({
            'checkpoint_version': STRICT_CHECKPOINT_VERSION,
            'role_assigner': self.role_assigner.state_dict(),
            'task_executor': self.task_executor.state_dict(),
            'assigner_optimizer': self.assigner_optimizer.state_dict(),
            'executor_optimizer': self.executor_optimizer.state_dict(),
            'topology': self._checkpoint_topology(),
            'low_replay_state': self.low_level_buffer.state_dict(),
            'trajectory_state': trajectory_state,
            'high_replay_rng_state': copy.deepcopy(
                self._high_replay_rng.bit_generator.state
            ),
            'torch_sampling_rng_state': _capture_torch_sampling_rng_state(),
        }, path)
        main_logger.info(f"GNN模型已保存到 {path}")

    def load_model(self, path):
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        required = {
            'checkpoint_version', 'role_assigner', 'task_executor',
            'assigner_optimizer', 'executor_optimizer', 'topology',
            'low_replay_state', 'trajectory_state', 'high_replay_rng_state',
            'torch_sampling_rng_state',
        }
        if not isinstance(checkpoint, dict):
            raise ValueError("GNN strict checkpoint must be a dictionary")
        missing = sorted(required.difference(checkpoint))
        if missing:
            raise ValueError(
                "GNN checkpoint missing strict state; legacy checkpoints are "
                f"warm-start only: {missing}"
            )
        extra = sorted(set(checkpoint).difference(required))
        if extra:
            raise ValueError(f"GNN strict checkpoint has unexpected keys: {extra}")
        if checkpoint['checkpoint_version'] != STRICT_CHECKPOINT_VERSION:
            raise ValueError("unsupported GNN strict checkpoint version")
        runtime_topology = self._checkpoint_topology()
        saved_device = checkpoint['topology'].get('policy_device')
        if saved_device != runtime_topology['policy_device']:
            raise ValueError(
                "GNN checkpoint policy parameter device does not match runtime device"
            )
        if checkpoint['topology'] != runtime_topology:
            raise ValueError("GNN checkpoint topology does not match runtime agent")
        trajectory_for_validation = dict(checkpoint['trajectory_state'])
        trajectory_for_validation['low_replay_state'] = checkpoint['low_replay_state']
        self._validate_trajectory_state(trajectory_for_validation)
        _validate_torch_sampling_rng_state(checkpoint['torch_sampling_rng_state'])
        self.low_level_buffer.load_state_dict(checkpoint['low_replay_state'])
        restored_high_rng = np.random.default_rng()
        try:
            restored_high_rng.bit_generator.state = copy.deepcopy(
                checkpoint['high_replay_rng_state']
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid GNN high replay RNG state") from exc
        self.role_assigner.load_state_dict(checkpoint['role_assigner'])
        self.task_executor.load_state_dict(checkpoint['task_executor'])
        self.assigner_optimizer.load_state_dict(checkpoint['assigner_optimizer'])
        self.executor_optimizer.load_state_dict(checkpoint['executor_optimizer'])
        state = copy.deepcopy(checkpoint['trajectory_state'])
        self.high_level_buffer = state['high_level_buffer']
        self._pending_high_samples = state['pending_high_samples']
        self._pending_low_segments = state['pending_low_segments']
        self._unbootstrapped_low_rows = {
            tuple(key): self._pending_low_segments[tuple(key)][-1]
            for key in state['unbootstrapped_low_keys']
        }
        self._pending_high_segments = state['pending_high_segments']
        self._low_episode_ids = state['low_episode_ids']
        self._low_timesteps = state['low_timesteps']
        self._low_segment_ids = state['low_segment_ids']
        self._high_episode_ids = state['high_episode_ids']
        self._high_timesteps = state['high_timesteps']
        self._high_segment_ids = state['high_segment_ids']
        self._low_rows_since_update = int(state['low_rows_since_update'])
        self._high_rows_since_update = int(state['high_rows_since_update'])
        self.env_roles = state['env_roles']
        self.env_timers = state['env_timers']
        self.env_reward_sums = state['env_reward_sums']
        self.high_level_obs = state['high_level_obs']
        self.global_step = int(state['global_step'])
        self._collection_tokens = state['collection_tokens']
        self._collection_frontiers = state['collection_frontiers']
        self._collection_token_counter = int(state['collection_token_counter'])
        self._high_replay_rng = restored_high_rng
        # Global Torch distribution state is restored last, after every strict
        # payload and model/optimizer/frontier load has succeeded.
        _restore_torch_sampling_rng_state(checkpoint['torch_sampling_rng_state'])
        main_logger.info(f"GNN模型已从 {path} 加载")

    @staticmethod
    def _validate_warm_start_weights(module, state, label):
        if not isinstance(state, dict):
            raise ValueError(f"legacy GNN {label} weights must be a state dictionary")
        expected = module.state_dict()
        if set(state) != set(expected):
            raise ValueError(f"legacy GNN {label} weights have missing or extra keys")
        for name, tensor in state.items():
            if (
                not torch.is_tensor(tensor)
                or tensor.shape != expected[name].shape
                or tensor.dtype != expected[name].dtype
            ):
                raise ValueError(f"legacy GNN {label} weight {name!r} is incompatible")

    def _reset_after_warm_start(self):
        base_seed = int(getattr(self.config, 'seed', 0))
        low_seed = int(getattr(self.config, 'gnn_low_replay_seed', base_seed + 1701))
        high_seed = int(getattr(self.config, 'gnn_high_replay_seed', base_seed + 1702))
        self.low_level_buffer.clear()
        self.low_level_buffer.set_rng_state(random.Random(low_seed).getstate())
        self._high_replay_rng = np.random.default_rng(high_seed)
        self.high_level_buffer = []
        self._pending_high_samples = {}
        self._pending_low_segments = {}
        self._unbootstrapped_low_rows = {}
        self._pending_high_segments = {}
        self._low_episode_ids = {}
        self._low_timesteps = {}
        self._low_segment_ids = {}
        self._high_episode_ids = {}
        self._high_timesteps = {}
        self._high_segment_ids = {}
        self._low_rows_since_update = 0
        self._high_rows_since_update = 0
        self.env_roles = {}
        self.env_timers = {}
        self.env_reward_sums = {}
        self.high_level_obs = None
        self._collection_tokens = {}
        self._collection_frontiers = {}
        self._collection_token_counter = 0
        self.global_step = 0
        self.assigner_optimizer.state.clear()
        self.executor_optimizer.state.clear()
        torch.manual_seed(base_seed)
        if torch.cuda.is_initialized():
            torch.cuda.manual_seed_all(base_seed)

    def load_warm_start(self, path):
        """Load the historical two-key GNN weights-only checkpoint family.

        This API never accepts a strict or mixed payload. Replay, trajectory
        frontiers, optimizer moments, collection tokens, and sampler RNGs are
        deliberately reset after both weight dictionaries validate.
        """
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        if not isinstance(checkpoint, dict) or set(checkpoint) != GNN_LEGACY_WARM_START_KEYS:
            raise ValueError(
                "legacy GNN warm-start payload must contain exactly role_assigner "
                "and task_executor"
            )
        self._validate_warm_start_weights(
            self.role_assigner, checkpoint['role_assigner'], 'role_assigner'
        )
        self._validate_warm_start_weights(
            self.task_executor, checkpoint['task_executor'], 'task_executor'
        )
        self.role_assigner.load_state_dict(checkpoint['role_assigner'], strict=True)
        self.task_executor.load_state_dict(checkpoint['task_executor'], strict=True)
        self._reset_after_warm_start()
        main_logger.info(f"GNN legacy weights warm-started from {path}")
