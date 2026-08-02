import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
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
from hmasd.utils import ReplayBuffer, compute_gae

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
        self.low_level_buffer = ReplayBuffer(config.buffer_size)

        self.global_step = 0
        
        # 环境状态跟踪
        self.env_roles = {}
        self.env_timers = {}
        self.env_reward_sums = {}
        
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
        graph_data.uav_mask = torch.arange(n_uavs) # 记录哪些是UAV节点

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
        obs_tensor = torch.tensor(observations, dtype=torch.float, device=self.device)
        roles_tensor = torch.tensor(roles, dtype=torch.long, device=self.device)
        
        actions, log_probs, values = self.task_executor(obs_tensor, roles_tensor, deterministic)
        
        return actions.cpu().detach().numpy(), log_probs, values

    def step(self, env, ep_t, env_id=0, deterministic=False):
        """
        执行一个环境步骤
        """
        if env_id not in self.env_timers:
            self.env_timers[env_id] = 0
            self.env_roles[env_id] = None
            self.env_reward_sums[env_id] = 0.0
            self.high_level_obs = None

        if ep_t % self.config.k == 0 or self.env_roles[env_id] is None:
            # 从环境中获取最新的实体位置
            uav_pos = env.uav_positions
            user_pos = env.user_positions
            gbs_pos = env.ground_bs_positions
            
            roles, role_log_probs, high_level_value, graph_data = self.assign_roles(uav_pos, user_pos, gbs_pos, deterministic)
            self.env_roles[env_id] = roles.cpu().numpy()
            self.env_timers[env_id] = 0
            self.env_reward_sums[env_id] = 0.0
            skill_changed = True
            
            # 存储高层决策信息
            self.high_level_obs = {
                "graph_data": graph_data,
                "roles": roles,
                "log_probs": role_log_probs,
                "value": high_level_value
            }
        else:
            self.env_timers[env_id] += 1
            skill_changed = False

        # 从环境中获取最新的局部观测
        observations = [env._get_observation(agent)['obs'] for agent in env.agents]
        actions, action_logprobs, low_level_values = self.select_action(observations, self.env_roles[env_id], deterministic)

        info = {
            'roles': self.env_roles[env_id],
            'action_logprobs': action_logprobs.cpu().detach().numpy(),
            'low_level_values': low_level_values.cpu().detach().numpy(),
            'skill_changed': skill_changed,
            'skill_timer': self.env_timers[env_id],
            'env_id': env_id,
            'high_level_obs': self.high_level_obs if skill_changed else None
        }
        return actions, info

    def _compute_intrinsic_reward(self, obs, reward, role):
        # 占位符，需要根据具体角色定义来实现
        return self.config.lambda_e * reward

    def store_transition(self, obs, next_obs, actions, rewards, dones, info):
        """
        存储经验
        """
        # 累积高层奖励
        self.env_reward_sums[info['env_id']] += np.mean(rewards)

        # 存储低层经验
        for i in range(self.config.n_agents):
            intrinsic_reward = self._compute_intrinsic_reward(obs[i], rewards[i], info['roles'][i])
            self.low_level_buffer.push((
                obs[i], actions[i], intrinsic_reward, dones[i],
                info['action_logprobs'][i], info['roles'][i], info['low_level_values'][i]
            ))

        # 存储高层经验
        if info['skill_timer'] == self.config.k - 1 or any(dones):
            if info['high_level_obs'] is not None:
                high_level_reward = self.env_reward_sums[info['env_id']]
                
                # 将高层经验添加到缓冲区
                self.high_level_buffer.append({
                    'graph_data': info['high_level_obs']['graph_data'],
                    'roles': info['high_level_obs']['roles'],
                    'log_probs': info['high_level_obs']['log_probs'],
                    'value': info['high_level_obs']['value'],
                    'reward': high_level_reward,
                    'done': any(dones)
                })
                self.env_reward_sums[info['env_id']] = 0.0

    def update(self):
        if len(self.low_level_buffer) > self.config.batch_size:
            self.update_executor()
        if len(self.high_level_buffer) > self.config.high_level_batch_size:
            self.update_assigner()
        self.global_step += 1

    def update_executor(self):
        """更新低层TaskExecutor网络"""
        obs, actions, rewards, dones, old_log_probs, roles, old_values = self.low_level_buffer.sample_torch(self.config.batch_size, self.device)

        advantages, returns = compute_gae(rewards, old_values, torch.zeros_like(old_values), dones, self.config.gamma, self.config.gae_lambda)
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        _, new_log_probs, new_values = self.task_executor(obs, roles)
        
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

    def update_assigner(self):
        """更新高层GNNRoleAssigner网络"""
        batch = np.random.choice(self.high_level_buffer, self.config.high_level_batch_size, replace=False)
        
        rewards = torch.tensor([b['reward'] for b in batch], dtype=torch.float, device=self.device)
        dones = torch.tensor([b['done'] for b in batch], dtype=torch.float, device=self.device)
        old_log_probs = torch.stack([b['log_probs'] for b in batch]).to(self.device)
        old_values = torch.stack([b['value'] for b in batch]).to(self.device).squeeze()

        # 计算GAE
        advantages, returns = compute_gae(rewards, old_values, torch.zeros_like(old_values), dones, self.config.gamma, self.config.gae_lambda)
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # 从批处理中重新计算新的log_probs和values
        graph_batch = Batch.from_data_list([b['graph_data'] for b in batch]).to(self.device)
        roles_batch = torch.stack([b['roles'] for b in batch]).to(self.device)
        
        _, new_log_probs, new_values = self.role_assigner(graph_batch, roles_batch)
        new_log_probs = new_log_probs.sum(dim=1) # 对每个图的所有节点的log_prob求和
        new_values = new_values.squeeze()

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

    def save_model(self, path):
        torch.save({
            'role_assigner': self.role_assigner.state_dict(),
            'task_executor': self.task_executor.state_dict(),
        }, path)
        main_logger.info(f"GNN模型已保存到 {path}")

    def load_model(self, path):
        checkpoint = torch.load(path, map_location=self.device)
        self.role_assigner.load_state_dict(checkpoint['role_assigner'])
        self.task_executor.load_state_dict(checkpoint['task_executor'])
        main_logger.info(f"GNN模型已从 {path} 加载")
