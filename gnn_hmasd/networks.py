import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torch.distributions import Categorical

# 尝试导入PyTorch Geometric，如果失败则发出警告
try:
    from torch_geometric.nn import GCNConv, GATConv, MessagePassing
    from torch_geometric.data import Data
except ImportError:
    GCNConv = None
    GATConv = None
    MessagePassing = None
    Data = None
    print("警告: PyTorch Geometric 未安装。GNN相关功能将不可用。请运行 'pip install torch_geometric' 进行安装。")

from hmasd.logging import main_logger

def initialize_weights(module, gain=1.0, last_layer_gain=None):
    """
    初始化网络权重，防止数值不稳定。
    """
    if not last_layer_gain:
        last_layer_gain = gain
    
    if isinstance(module, nn.Sequential):
        last_linear_idx = -1
        for i, m in enumerate(module):
            if isinstance(m, nn.Linear):
                last_linear_idx = i
        
        for i, m in enumerate(module):
            if isinstance(m, nn.Linear):
                if i == last_linear_idx:
                    nn.init.orthogonal_(m.weight.data, last_layer_gain)
                else:
                    nn.init.orthogonal_(m.weight.data, gain)
                if m.bias is not None:
                    nn.init.zeros_(m.bias.data)
    
    elif isinstance(module, nn.Linear):
        nn.init.orthogonal_(module.weight.data, gain)
        if module.bias is not None:
            nn.init.zeros_(module.bias.data)
            
    elif isinstance(module, nn.GRU) or isinstance(module, nn.LSTM):
        for name, param in module.named_parameters():
            if 'weight' in name:
                nn.init.orthogonal_(param.data, gain)
            elif 'bias' in name:
                nn.init.zeros_(param.data)

class MLP(nn.Module):
    """多层感知机"""
    def __init__(self, input_dim, hidden_dim, output_dim, n_layers=2):
        super(MLP, self).__init__()
        
        layers = []
        dims = [input_dim] + [hidden_dim] * n_layers + [output_dim]
        
        for i in range(len(dims) - 1):
            layers.append(nn.Linear(dims[i], dims[i+1]))
            if i < len(dims) - 2:
                layers.append(nn.ReLU())
        
        self.model = nn.Sequential(*layers)
        initialize_weights(self.model, gain=1.0, last_layer_gain=0.01)
    
    def forward(self, x):
        return self.model(x.float())

class GNNRoleAssigner(nn.Module):
    """
    高层策略：使用GNN为智能体分配角色
    """
    def __init__(self, config):
        super(GNNRoleAssigner, self).__init__()
        if GCNConv is None:
            raise ImportError("PyTorch Geometric 未安装，无法创建GNNRoleAssigner。")
            
        self.config = config
        self.node_feature_dim = config.node_feature_dim
        self.gnn_hidden_dim = config.gnn_hidden_dim
        self.num_roles = config.num_roles # 例如, 2 for {'SERVER', 'RELAY'}

        # GNN层
        self.conv1 = GCNConv(self.node_feature_dim, self.gnn_hidden_dim)
        self.conv2 = GCNConv(self.gnn_hidden_dim, self.gnn_hidden_dim)

        # 角色分配头 (为每个节点输出一个角色分类)
        self.role_head = nn.Linear(self.gnn_hidden_dim, self.num_roles)
        
        # 价值函数头
        self.value_head = nn.Sequential(
            nn.Linear(self.gnn_hidden_dim, self.gnn_hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(self.gnn_hidden_dim // 2, 1)
        )

    def _policy_value(self, graph_data):
        """Return per-UAV role logits and one pooled value per input graph."""
        x, edge_index = graph_data.x, graph_data.edge_index
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.conv2(x, edge_index)

        uav_nodes_mask = graph_data.uav_mask
        uav_features = x[uav_nodes_mask]
        role_logits = self.role_head(uav_features)

        node_batch = getattr(graph_data, "batch", None)
        if node_batch is None:
            graph_features = x.mean(dim=0, keepdim=True)
            uav_batch = torch.zeros(
                uav_features.shape[0], dtype=torch.long, device=x.device
            )
        else:
            node_batch = node_batch.to(device=x.device, dtype=torch.long)
            num_graphs = int(node_batch.max().item()) + 1 if node_batch.numel() else 0
            if num_graphs <= 0:
                raise ValueError("batched graph input contains no graphs")
            graph_sums = torch.zeros(
                (num_graphs, x.shape[-1]), dtype=x.dtype, device=x.device
            )
            graph_sums.index_add_(0, node_batch, x)
            graph_counts = torch.bincount(node_batch, minlength=num_graphs).to(x.dtype)
            if bool(torch.any(graph_counts <= 0).item()):
                raise ValueError("batched graph input contains an empty graph")
            graph_features = graph_sums / graph_counts.unsqueeze(-1)
            uav_batch = node_batch[uav_nodes_mask]

        values = self.value_head(graph_features).squeeze(-1)
        return role_logits, values, uav_batch

    def forward(self, graph_data, deterministic=False):
        """
        参数:
            graph_data: PyG的Data对象, 包含 x, edge_index
            deterministic: 是否使用确定性策略
        返回:
            roles: 分配给每个无人机节点的角色 [num_uav_nodes]
            role_log_probs: 角色选择的对数概率 [num_uav_nodes]
            role_logits: 角色分类的logits [num_uav_nodes, num_roles]
            value: 状态价值估计
        """
        role_logits, values, _uav_batch = self._policy_value(graph_data)
        role_dist = Categorical(logits=role_logits)

        if deterministic:
            roles = role_logits.argmax(dim=-1)
        else:
            roles = role_dist.sample()

        role_log_probs = role_dist.log_prob(roles)

        return roles, role_log_probs, role_logits, values

    def evaluate_roles(self, graph_data, roles):
        """Evaluate stored roles without sampling a replacement action."""
        role_logits, values, uav_batch = self._policy_value(graph_data)
        roles = torch.as_tensor(roles, dtype=torch.long, device=role_logits.device).reshape(-1)
        if roles.numel() != role_logits.shape[0]:
            raise ValueError("stored role count does not match batched UAV count")
        distribution = Categorical(logits=role_logits)
        return distribution.log_prob(roles), distribution.entropy(), values, uav_batch

class TaskExecutor(nn.Module):
    """
    低层策略：执行由高层分配的特定任务
    """
    def __init__(self, config):
        super(TaskExecutor, self).__init__()
        self.config = config
        self.obs_dim = config.obs_dim
        self.action_dim = config.action_dim
        self.hidden_dim = config.hidden_size
        self.num_roles = config.num_roles
        
        # 任务嵌入
        self.role_embedding = nn.Embedding(self.num_roles, config.role_embedding_dim)

        # 策略网络 (Actor)
        self.actor_net = MLP(
            input_dim=self.obs_dim + config.role_embedding_dim,
            hidden_dim=self.hidden_dim,
            output_dim=self.hidden_dim
        )
        self.action_mean = nn.Linear(self.hidden_dim, self.action_dim)
        self.action_log_std = nn.Parameter(torch.zeros(1, self.action_dim))

        # 价值网络 (Critic)
        self.critic_net = MLP(
            input_dim=self.obs_dim + config.role_embedding_dim,
            hidden_dim=self.hidden_dim,
            output_dim=1
        )
        
        initialize_weights(self.action_mean, gain=0.01)

    def _distribution_value(self, obs, role):
        obs = obs.float()
        role = role.long()
        role_emb = self.role_embedding(role)
        actor_input = torch.cat([obs, role_emb], dim=-1)
        critic_input = torch.cat([obs, role_emb], dim=-1)
        actor_features = self.actor_net(actor_input)
        mean = self.action_mean(actor_features)
        action_log_std = self.action_log_std.expand_as(mean)
        distribution = torch.distributions.Normal(mean, torch.exp(action_log_std))
        value = self.critic_net(critic_input).squeeze(-1)
        return distribution, value

    def get_value(self, obs, role):
        return self._distribution_value(obs, role)[1]

    def evaluate_actions(self, obs, role, actions):
        distribution, value = self._distribution_value(obs, role)
        actions = torch.as_tensor(actions, dtype=obs.dtype, device=obs.device)
        if actions.shape != distribution.loc.shape:
            raise ValueError(
                f"stored action shape {tuple(actions.shape)} does not match "
                f"policy shape {tuple(distribution.loc.shape)}"
            )
        return (
            distribution.log_prob(actions).sum(dim=-1),
            distribution.entropy().sum(dim=-1),
            value,
        )

    def forward(self, obs, role, deterministic=False):
        """
        参数:
            obs: 局部观测 [batch_size, obs_dim]
            role: 分配的角色 [batch_size]
            deterministic: 是否使用确定性策略
        返回:
            action: 动作
            log_prob: 动作对数概率
            value: 价值估计
        """
        action_dist, value = self._distribution_value(obs, role)

        if deterministic:
            action = action_dist.mean
        else:
            action = action_dist.sample()
        
        log_prob = action_dist.log_prob(action).sum(dim=-1)

        return action, log_prob, value

# --- 从 hmasd/networks.py 迁移过来的判别器 ---

class TeamDiscriminator(nn.Module):
    """团队技能判别器 (在此GNN方案中，可能需要判别角色组合)"""
    def __init__(self, config):
        super(TeamDiscriminator, self).__init__()
        # 输入可以是全局状态，或者GNN编码后的全局图特征
        self.model = MLP(
            input_dim=config.state_dim, # 或者 gnn_hidden_dim
            hidden_dim=config.hidden_size,
            output_dim=config.n_Z, # n_Z 在此方案中可能代表角色组合的ID
            n_layers=2
        )
    
    def forward(self, state):
        return self.model(state.float())

class IndividualDiscriminator(nn.Module):
    """个体技能判别器 (在此GNN方案中，判别的是角色)"""
    def __init__(self, config):
        super(IndividualDiscriminator, self).__init__()
        self.config = config
        # 输入是局部观测和全局上下文（如团队角色组合ID）
        self.model = MLP(
            input_dim=config.obs_dim + config.n_Z,
            hidden_dim=config.hidden_size,
            output_dim=config.num_roles, # 输出是角色分类
            n_layers=2
        )
    
    def forward(self, observation, team_context):
        # team_context 可以是 one-hot 编码的团队技能/角色组合ID
        team_context_onehot = F.one_hot(team_context, self.config.n_Z).float()
        discriminator_input = torch.cat([observation.float(), team_context_onehot], dim=-1)
        return self.model(discriminator_input)
