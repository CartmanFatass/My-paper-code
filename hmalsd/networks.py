import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torch.distributions import Normal, Categorical
import logging
from logger import main_logger

def sparsemax(logits, dim=-1):
    """
    Sparsemax激活函数实现
    基于论文: "From Softmax to Sparsemax: A Sparse Model of Attention and Multi-Label Classification"
    
    参数:
        logits: 输入张量 [..., d]
        dim: 应用sparsemax的维度
        
    返回:
        稀疏概率分布 [..., d]
    """
    # 获取输入的形状和设备
    original_shape = logits.shape
    device = logits.device
    
    # 重塑为二维张量以便处理
    if dim != -1 and dim != len(original_shape) - 1:
        # 将指定维度移动到最后
        logits = logits.transpose(dim, -1)
    
    # 展平除最后一维外的所有维度
    batch_size = logits.shape[:-1].numel()
    d = logits.shape[-1]
    logits_2d = logits.reshape(batch_size, d)
    
    # 对每个样本应用sparsemax
    output = torch.zeros_like(logits_2d)
    
    for i in range(batch_size):
        z = logits_2d[i]
        
        # 按降序排序
        z_sorted, _ = torch.sort(z, descending=True)
        
        # 计算累积和
        cumsum = torch.cumsum(z_sorted, dim=0)
        
        # 找到支持集大小
        k_vals = torch.arange(1, d + 1, device=device, dtype=torch.float32)
        support_condition = 1 + k_vals * z_sorted > cumsum
        
        if support_condition.any():
            k = support_condition.nonzero()[-1].item() + 1
        else:
            k = 1
        
        # 计算阈值
        tau = (cumsum[k-1] - 1) / k
        
        # 应用阈值
        output[i] = torch.clamp(z - tau, min=0.0)
    
    # 重塑回原始形状
    output = output.reshape(original_shape)
    
    # 如果之前移动了维度，现在移回去
    if dim != -1 and dim != len(original_shape) - 1:
        output = output.transpose(dim, -1)
    
    return output

def initialize_weights(module, gain=1.0, last_layer_gain=None):
    """
    初始化网络权重，防止数值不稳定。
    参考论文: "Understanding the difficulty of training deep feedforward neural networks"
    
    参数:
        module: 需要初始化的模块
        gain: 权重初始化的增益因子（默认为1.0）
        last_layer_gain: 最后一层的特殊增益因子（如果为None则使用gain值）
    """
    if not last_layer_gain:
        last_layer_gain = gain
    
    if isinstance(module, nn.Sequential):
        # 如果是Sequential容器，找到最后一个线性层
        last_linear_idx = -1
        for i, m in enumerate(module):
            if isinstance(m, nn.Linear):
                last_linear_idx = i
        
        # 初始化每一层
        for i, m in enumerate(module):
            if isinstance(m, nn.Linear):
                if i == last_linear_idx:
                    # 最后一层使用不同的增益因子
                    nn.init.orthogonal_(m.weight.data, last_layer_gain)
                else:
                    nn.init.orthogonal_(m.weight.data, gain)
                if m.bias is not None:
                    nn.init.zeros_(m.bias.data)
    
    elif isinstance(module, nn.Linear):
        # 单个线性层
        nn.init.orthogonal_(module.weight.data, gain)
        if module.bias is not None:
            nn.init.zeros_(module.bias.data)
    
    elif isinstance(module, nn.GRU) or isinstance(module, nn.LSTM):
        # RNN层
        for name, param in module.named_parameters():
            if 'weight' in name:
                nn.init.orthogonal_(param.data, gain)
            elif 'bias' in name:
                nn.init.zeros_(param.data)
                
    elif hasattr(module, 'weight') and hasattr(module, 'bias'):
        # 其他有weight和bias的层
        nn.init.orthogonal_(module.weight.data, gain)
        if module.bias is not None:
            nn.init.zeros_(module.bias.data)

class MLP(nn.Module):
    """多层感知机"""
    def __init__(self, input_dim, hidden_dim, output_dim, n_layers=2):
        super(MLP, self).__init__()
        
        layers = []
        dims = [input_dim] + [hidden_dim] * n_layers + [output_dim]
        
        for i in range(len(dims) - 1):
            layers.append(nn.Linear(dims[i], dims[i+1]))
            if i < len(dims) - 2:  # 不在最后一层应用激活函数
                layers.append(nn.ReLU())
        
        self.model = nn.Sequential(*layers)
        
        # 初始化权重，使用较小的增益因子以避免大梯度
        initialize_weights(self.model, gain=1.0, last_layer_gain=0.01)
    
    def forward(self, x):
        # 确保输入是float32类型
        x = x.float()
        return self.model(x)

class PositionalEncoding(nn.Module):
    """位置编码"""
    def __init__(self, d_model, max_len=100):
        super(PositionalEncoding, self).__init__()
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        
        self.register_buffer('pe', pe)
        self.d_model = d_model
    
    def forward(self, x):
        # 确保输入是float32类型
        x = x.float()
        x = x + self.pe[:, :x.size(1)]
        return x

class OPT(nn.Module):
    """
    OPT (Interaction Pattern Disentangling) 模块
    基于论文: "Interaction Pattern Disentangling for Multi-Agent Reinforcement Learning"
    """
    def __init__(self, input_dim, num_prototypes, prototype_dim, num_layers=1):
        super(OPT, self).__init__()
        
        self.input_dim = input_dim
        self.num_prototypes = num_prototypes  # N
        self.prototype_dim = prototype_dim    # d_x
        self.num_layers = num_layers
        
        # 输入嵌入层
        self.input_embedding = nn.Linear(input_dim, prototype_dim)
        
        # N个交互原型的参数矩阵（每个原型有独立的Q, K, V）
        self.prototype_projections = nn.ModuleList([
            nn.ModuleDict({
                'W_Q': nn.Linear(prototype_dim, prototype_dim, bias=False),
                'W_K': nn.Linear(prototype_dim, prototype_dim, bias=False),
                'W_V': nn.Linear(prototype_dim, prototype_dim, bias=False)
            }) for _ in range(num_prototypes)
        ])
        
        # 原型聚合器 (Prototype Aggregator)
        self.prototype_aggregator = nn.Sequential(
            nn.Linear(prototype_dim, prototype_dim // 2),
            nn.ReLU(),
            nn.Linear(prototype_dim // 2, num_prototypes),
            nn.Softmax(dim=-1)
        )
        
        # 变分近似器 (用于CMI损失)
        self.variational_approximator = nn.Sequential(
            nn.Linear(prototype_dim, prototype_dim // 2),
            nn.ReLU(),
            nn.Linear(prototype_dim // 2, num_prototypes),
            nn.Softmax(dim=-1)
        )
        
        # 历史编码器 (GRU for history encoding)
        self.history_encoder = nn.GRU(
            input_size=prototype_dim,
            hidden_size=prototype_dim,
            batch_first=True
        )
        
        # 初始化权重
        self._init_weights()
    
    def _init_weights(self):
        """初始化网络权重"""
        initialize_weights(self.input_embedding, gain=1.0)
        
        # 初始化原型投影层
        for prototype_proj in self.prototype_projections:
            for layer in prototype_proj.values():
                initialize_weights(layer, gain=1.0)
        
        # 初始化聚合器
        for layer in self.prototype_aggregator:
            if isinstance(layer, nn.Linear):
                initialize_weights(layer, gain=1.0)
        
        # 初始化变分近似器
        for layer in self.variational_approximator:
            if isinstance(layer, nn.Linear):
                initialize_weights(layer, gain=1.0)
        
        # 初始化GRU
        initialize_weights(self.history_encoder, gain=1.0)
    
    def disentangling_step(self, X):
        """
        解耦步骤：生成N个稀疏交互原型
        
        参数:
            X: 输入嵌入 [batch_size, M, prototype_dim]
            
        返回:
            prototypes: 交互原型列表 [N个 [batch_size, M, M]]
            prototype_values: 对应的值矩阵列表 [N个 [batch_size, M, prototype_dim]]
        """
        batch_size, M, _ = X.shape
        device = X.device
        
        prototypes = []
        prototype_values = []
        
        for n in range(self.num_prototypes):
            # 获取第n个原型的投影矩阵
            W_Q = self.prototype_projections[n]['W_Q']
            W_K = self.prototype_projections[n]['W_K']
            W_V = self.prototype_projections[n]['W_V']
            
            # 计算Q, K, V
            Q = W_Q(X)  # [batch_size, M, prototype_dim]
            K = W_K(X)  # [batch_size, M, prototype_dim]
            V = W_V(X)  # [batch_size, M, prototype_dim]
            
            # 计算注意力权重
            attention_scores = torch.bmm(Q, K.transpose(1, 2)) / np.sqrt(self.prototype_dim)  # [batch_size, M, M]
            
            # 应用sparsemax而不是softmax
            P_n = sparsemax(attention_scores, dim=-1)  # [batch_size, M, M]
            
            # 计算原型值
            prototype_value = torch.bmm(P_n, V)  # [batch_size, M, prototype_dim]
            
            prototypes.append(P_n)
            prototype_values.append(prototype_value)
        
        return prototypes, prototype_values
    
    def compute_cd_loss(self, prototype_values):
        """
        计算对比散度损失 (Contrastive Disagreement Loss)
        
        参数:
            prototype_values: 原型值列表 [N个 [batch_size, M, prototype_dim]]
            
        返回:
            cd_loss: 对比散度损失
        """
        if len(prototype_values) < 2:
            return torch.tensor(0.0, device=prototype_values[0].device, requires_grad=True)
        
        batch_size, M, prototype_dim = prototype_values[0].shape
        device = prototype_values[0].device
        
        # 对每个实体计算对比损失
        total_loss = 0.0
        
        # 将原型值堆叠成一个张量 [N, batch_size, M, prototype_dim]
        stacked_prototypes = torch.stack(prototype_values, dim=0)
        
        # 归一化原型向量以提高稳定性
        stacked_prototypes = F.normalize(stacked_prototypes, p=2, dim=-1)
        
        for e in range(M):  # 对每个实体
            # 获取实体e在所有原型下的表示 [N, batch_size, prototype_dim]
            entity_prototypes = stacked_prototypes[:, :, e, :]
            
            # 计算所有原型之间的相似度矩阵 [N, N, batch_size]
            # (N, batch_size, dim) x (N, batch_size, dim) -> (N, N, batch_size)
            similarity_matrix = torch.einsum('nbd,mbd->nmb', entity_prototypes, entity_prototypes)
            
            # 使用 log-sum-exp 技巧来稳定计算
            # log(exp(pos_sim) / sum(exp(neg_sim))) = pos_sim - log(sum(exp(neg_sim)))
            
            # 正样本相似度是对角线元素
            positive_sim = torch.diagonal(similarity_matrix, dim1=0, dim2=1) # [batch_size, N]
            
            # 负样本是所有非对角线元素
            # 创建一个掩码以排除对角线元素
            mask = ~torch.eye(len(prototype_values), dtype=torch.bool, device=device)
            
            # 对每个原型计算损失
            for n in range(len(prototype_values)):
                pos_sim = positive_sim[:, n] # [batch_size]
                
                # 获取第n个原型的负样本相似度
                neg_sims = similarity_matrix[n, mask[n], :] # [N-1, batch_size]
                
                # 使用 logsumexp 计算负样本部分
                log_sum_exp_neg = torch.logsumexp(neg_sims, dim=0) # [batch_size]
                
                # 计算最终的对比损失
                # loss = -log(exp(pos) / (exp(pos) + sum(exp(neg))))
                #      = - (pos - log(exp(pos) + sum(exp(neg))))
                #      = - (pos - logsumexp([pos] + neg))
                all_sims = torch.cat([pos_sim.unsqueeze(0), neg_sims], dim=0)
                log_sum_exp_all = torch.logsumexp(all_sims, dim=0)
                
                loss = -(pos_sim - log_sum_exp_all)
                total_loss += loss.mean()

        # 返回平均损失
        return total_loss / (M * len(prototype_values)) if (M * len(prototype_values)) > 0 else torch.tensor(0.0, device=device)
    
    def restructuring_step(self, prototype_values, global_context, history_context=None):
        """
        重构步骤：根据全局上下文聚合交互原型
        
        参数:
            prototype_values: 原型值列表 [N个 [batch_size, M, prototype_dim]]
            global_context: 全局上下文 [batch_size, prototype_dim]
            history_context: 历史上下文 [batch_size, prototype_dim] (用于CMI损失)
            
        返回:
            final_output: 最终输出 [batch_size, M, prototype_dim]
            aggregation_weights: 聚合权重 [batch_size, num_prototypes]
            cmi_loss: 条件互信息损失
        """
        batch_size = global_context.shape[0]
        device = global_context.device
        
        # 计算聚合权重
        aggregation_weights = self.prototype_aggregator(global_context)  # [batch_size, num_prototypes]
        
        # 加权聚合原型值
        final_output = torch.zeros_like(prototype_values[0])  # [batch_size, M, prototype_dim]
        
        for n, prototype_value in enumerate(prototype_values):
            weight = aggregation_weights[:, n:n+1].unsqueeze(2)  # [batch_size, 1, 1]
            final_output += weight * prototype_value
        
        # 计算CMI损失
        cmi_loss = torch.tensor(0.0, device=device, requires_grad=True)
        if history_context is not None:
            # 变分近似器估计后验分布
            q_posterior = self.variational_approximator(history_context)  # [batch_size, num_prototypes]
            p_prior = aggregation_weights  # [batch_size, num_prototypes]
            
            # 计算KL散度
            kl_div = F.kl_div(
                q_posterior.log(),
                p_prior,
                reduction='batchmean'
            )
            cmi_loss = kl_div
        
        return final_output, aggregation_weights, cmi_loss
    
    def forward(self, X, history_context=None):
        """
        前向传播
        
        参数:
            X: 输入序列 [batch_size, M, input_dim]
            history_context: 历史上下文 [batch_size, prototype_dim] (可选)
            
        返回:
            output: 输出 [batch_size, M, prototype_dim]
            cd_loss: 对比散度损失
            cmi_loss: 条件互信息损失
            aggregation_weights: 聚合权重
        """
        # 输入嵌入
        X_embedded = self.input_embedding(X)  # [batch_size, M, prototype_dim]
        
        # 解耦步骤
        prototypes, prototype_values = self.disentangling_step(X_embedded)
        
        # 计算对比散度损失
        cd_loss = self.compute_cd_loss(prototype_values)
        
        # 计算全局上下文（均值池化）
        global_context = X_embedded.mean(dim=1)  # [batch_size, prototype_dim]
        
        # 重构步骤
        output, aggregation_weights, cmi_loss = self.restructuring_step(
            prototype_values, global_context, history_context
        )
        
        return output, cd_loss, cmi_loss, aggregation_weights


class StateEncoder(nn.Module):
    """状态编码器"""
    def __init__(self, state_dim, obs_dim, embedding_dim, n_layers, n_heads, config=None):
        super(StateEncoder, self).__init__()
        
        self.config = config
        self.use_opt = config.use_opt if config is not None else False
        
        # 及早初始化嵌入层，而不是延迟初始化
        self.state_embedding = nn.Linear(state_dim, embedding_dim)
        self.obs_embedding = nn.Linear(obs_dim, embedding_dim)
        self.embedding_dim = embedding_dim
        self.positional_encoding = PositionalEncoding(embedding_dim)
        
        if self.use_opt:
            # 使用OPT模块
            self.opt_module = OPT(
                input_dim=embedding_dim,
                num_prototypes=config.opt_num_prototypes,
                prototype_dim=config.opt_prototype_dim,
                num_layers=config.opt_layers
            )
            # 投影层将OPT输出映射回embedding_dim
            if config.opt_prototype_dim != embedding_dim:
                self.output_projection = nn.Linear(config.opt_prototype_dim, embedding_dim)
            else:
                self.output_projection = nn.Identity()
        else:
            # 使用标准的Transformer编码器
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=embedding_dim,
                nhead=n_heads,
                dim_feedforward=embedding_dim * 4,
                batch_first=True
            )
            self.transformer_encoder = nn.TransformerEncoder(encoder_layer, n_layers)
        
        # 初始化权重
        self._init_weights()
    
    def _init_weights(self):
        """初始化网络权重"""
        initialize_weights(self.state_embedding, gain=1.0)
        initialize_weights(self.obs_embedding, gain=1.0)
        
        if self.use_opt and hasattr(self, 'output_projection'):
            initialize_weights(self.output_projection, gain=1.0)
    
    def forward(self, state, observations, history_context=None):
        """
        参数:
            state: 全局状态 [batch_size, state_dim]
            observations: 所有智能体观测 [batch_size, n_agents, obs_dim]
            history_context: 历史上下文 [batch_size, prototype_dim] (仅在使用OPT时需要)
            
        返回:
            encoded_state: 编码后的状态 [batch_size, 1, embedding_dim]
            encoded_observations: 编码后的观测 [batch_size, n_agents, embedding_dim]
            cd_loss: 对比散度损失 (仅在使用OPT时)
            cmi_loss: 条件互信息损失 (仅在使用OPT时)
        """
        batch_size, n_agents, obs_dim = observations.size()
        state_dim = state.size(-1)
        
        # 确保输入是float32类型
        state = state.float()
        observations = observations.float()
        
        # 嵌入全局状态和局部观测
        embedded_state = self.state_embedding(state).unsqueeze(1)  # [batch_size, 1, embedding_dim]
        embedded_obs = self.obs_embedding(observations.reshape(-1, obs_dim))
        embedded_obs = embedded_obs.reshape(batch_size, n_agents, -1)  # [batch_size, n_agents, embedding_dim]
        
        # 将状态和观测拼接作为序列
        sequence = torch.cat([embedded_state, embedded_obs], dim=1)  # [batch_size, 1+n_agents, embedding_dim]
        
        # 位置编码
        sequence = self.positional_encoding(sequence)
        
        if self.use_opt:
            # 使用OPT模块
            opt_output, cd_loss, cmi_loss, aggregation_weights = self.opt_module(sequence, history_context)
            
            # 投影回原始维度
            encoded_sequence = self.output_projection(opt_output)
            
            # 拆分回状态和观测
            encoded_state = encoded_sequence[:, 0:1, :]
            encoded_observations = encoded_sequence[:, 1:, :]
            
            return encoded_state, encoded_observations, cd_loss, cmi_loss
        else:
            # 使用标准的Transformer编码器
            encoded_sequence = self.transformer_encoder(sequence)
            
            # 拆分回状态和观测
            encoded_state = encoded_sequence[:, 0:1, :]
            encoded_observations = encoded_sequence[:, 1:, :]
            
            # 返回零损失以保持接口一致性
            device = sequence.device
            cd_loss = torch.tensor(0.0, device=device, requires_grad=True)
            cmi_loss = torch.tensor(0.0, device=device, requires_grad=True)
            
            return encoded_state, encoded_observations, cd_loss, cmi_loss

class SkillDecoder(nn.Module):
    """
    技能解码器 (HMALS版本)
    支持分层解码Louvain技能和个体技能。
    """
    def __init__(self, embedding_dim, n_layers, n_heads, n_louvain_skills, n_z, config):
        super(SkillDecoder, self).__init__()
        
        self.embedding_dim = embedding_dim
        self.config = config
        
        # 通用嵌入层
        self.start_token_embedding = nn.Embedding(1, embedding_dim) # 用于所有解码过程的起始
        self.louvain_skill_embedding = nn.Embedding(n_louvain_skills, embedding_dim)
        self.agent_skill_embedding = nn.Embedding(n_z, embedding_dim)
        self.positional_encoding = PositionalEncoding(embedding_dim)
        
        # Transformer解码器层
        decoder_layer = nn.TransformerDecoderLayer(
            d_model=embedding_dim,
            nhead=n_heads,
            dim_feedforward=embedding_dim * 4,
            batch_first=True
        )
        self.transformer_decoder = nn.TransformerDecoder(decoder_layer, n_layers)
        
        # 输出头
        # 假设Louvain技能数量是固定的，后续可以改为动态输出
        self.louvain_skill_head = nn.Linear(embedding_dim, n_louvain_skills)
        self.agent_skill_head = nn.Linear(embedding_dim, n_z)

    def forward(self, context, memory):
        """
        通用解码器前向传播。

        参数:
            context (Tensor): 解码器的输入序列 (例如, [start_token, parent_skill, ...])
            memory (Tensor): 编码器的输出，用作Transformer的memory

        返回:
            Tensor: 解码后序列的logits
        """
        context = self.positional_encoding(context)
        decoded = self.transformer_decoder(context, memory)
        return decoded

class SkillCoordinator(nn.Module):
    """技能协调器（高层策略, HMALS版本）"""
    def __init__(self, config):
        super(SkillCoordinator, self).__init__()
        
        self.config = config
        self.n_z = config.n_z
        self.n_louvain_skills = config.n_louvain_skills # 新增：Louvain技能数量
        
        # 状态编码器
        self.state_encoder = StateEncoder(
            config.state_dim,
            config.obs_dim,
            config.embedding_dim,
            config.n_encoder_layers,
            config.n_heads,
            config
        )
        
        # 技能解码器
        self.skill_decoder = SkillDecoder(
            config.embedding_dim,
            config.n_decoder_layers,
            config.n_heads,
            config.n_louvain_skills,
            config.n_z,
            config
        )
        
        # 高层价值函数
        self.value_head_state = nn.Linear(config.embedding_dim, 1)
        self.value_heads_obs = nn.ModuleList([
            nn.Linear(config.embedding_dim, 1) for _ in range(config.n_agents)
        ])
        
        # 初始化网络权重
        self._init_weights()
    
    def _init_weights(self):
        """初始化网络权重，提高训练稳定性"""
        initialize_weights(self.value_head_state, gain=0.01)
        for value_head in self.value_heads_obs:
            initialize_weights(value_head, gain=0.01)
    
    def get_value(self, state, observations):
        """获取高层价值函数值"""
        encoded_state, encoded_observations, cd_loss, _ = self.state_encoder(state, observations)
        state_value = self.value_head_state(encoded_state.squeeze(1))
        
        agent_values = []
        for i in range(min(self.config.n_agents, encoded_observations.size(1))):
            agent_value = self.value_heads_obs[i](encoded_observations[:, i, :])
            agent_values.append(agent_value)
            
        return state_value, agent_values, cd_loss
    
    def forward(self, state, observations, louvain_hierarchy, deterministic=False, history_context=None):
        """
        HMALS的分层技能解码过程。
        """
        batch_size = state.size(0)
        n_agents = observations.size(1)
        device = state.device
        
        # 1. 编码状态和观测
        encoded_state, encoded_observations, cd_loss, cmi_loss = self.state_encoder(state, observations, history_context)
        memory = torch.cat([encoded_state, encoded_observations], dim=1)

        # 2. 逐层选择Louvain技能
        active_skill_path = []
        louvain_skills_logits = []
        parent_skill_embedding = self.skill_decoder.start_token_embedding(torch.zeros(batch_size, 1, dtype=torch.long, device=device))

        num_levels = len(louvain_hierarchy.partitions)
        for level in range(num_levels, 0, -1):
            # 构建当前层的解码器输入
            # 这里简化：仅使用父技能作为上下文
            # 实际应用中可能需要更复杂的上下文，如当前社区的嵌入
            context = parent_skill_embedding
            
            # 解码
            decoded_output = self.skill_decoder(context, memory)
            level_logits = self.skill_decoder.louvain_skill_head(decoded_output[:, -1, :])
            
            # 应用掩码，只选择有效的邻居社区技能
            masked_logits = level_logits
            if louvain_hierarchy.skill_tree:
                mask = torch.ones_like(level_logits, dtype=torch.bool) # 默认允许所有技能
                for i in range(batch_size):
                    current_state_np = state[i].cpu().numpy()
                    available_skills = louvain_hierarchy.get_available_skills(current_state_np, level)
                    
                    # 如果找到了当前状态的可用技能，则应用掩码
                    if available_skills:
                        valid_skill_indices = [idx for idx in available_skills.keys() if idx < self.n_louvain_skills]
                        # 创建一个全为False的掩码
                        current_mask = torch.zeros_like(level_logits[i], dtype=torch.bool)
                        if valid_skill_indices:
                            current_mask[valid_skill_indices] = True
                            mask[i] = current_mask
                        else:
                            # 如果有邻居但都不在范围内，或没有邻居，则允许所有
                            mask[i] = torch.ones_like(level_logits[i], dtype=torch.bool)
                
                masked_logits = level_logits.masked_fill(~mask, -1e9)

            louvain_skills_logits.append(masked_logits)
            
            # 采样技能
            dist = Categorical(logits=masked_logits)
            if deterministic:
                skill_choice = level_logits.argmax(dim=-1)
            else:
                skill_choice = dist.sample()
            
            active_skill_path.append(skill_choice)
            
            # 更新父技能嵌入以用于下一层
            parent_skill_embedding = self.skill_decoder.louvain_skill_embedding(skill_choice.unsqueeze(1))

        # 3. 分配个体技能 z
        if not active_skill_path:
            # 如果没有Louvain技能，则使用一个默认的团队技能上下文
            lowest_level_skill = torch.zeros(batch_size, dtype=torch.long, device=device)
        else:
            lowest_level_skill = active_skill_path[-1]
        
        z = torch.zeros(batch_size, n_agents, dtype=torch.long, device=device)
        z_logits = []
        
        # 解码个体技能的上下文：[start_token, lowest_level_skill]
        start_token_emb = self.skill_decoder.start_token_embedding(torch.zeros(batch_size, 1, dtype=torch.long, device=device))
        lowest_skill_emb = self.skill_decoder.louvain_skill_embedding(lowest_level_skill.unsqueeze(1))
        
        for i in range(n_agents):
            # 构建上下文序列
            context_list = [start_token_emb, lowest_skill_emb]
            if i > 0:
                # 添加之前已解码的个体技能
                z_i_emb = self.skill_decoder.agent_skill_embedding(z[:, :i])
                context_list.append(z_i_emb)
            
            context = torch.cat(context_list, dim=1)
            
            # 解码
            decoded_output = self.skill_decoder(context, memory)
            zi_logits = self.skill_decoder.agent_skill_head(decoded_output[:, -1, :])
            z_logits.append(zi_logits)
            
            # 采样
            dist = Categorical(logits=zi_logits)
            if deterministic:
                zi = zi_logits.argmax(dim=-1)
            else:
                zi = dist.sample()
            z[:, i] = zi
            
        # 返回路径，个体技能，以及对应的logits
        return active_skill_path, z, louvain_skills_logits, z_logits, cd_loss, cmi_loss

class SkillDiscoverer(nn.Module):
    """技能发现器（低层策略）"""
    def __init__(self, config, logger=None): # Add logger parameter
        super(SkillDiscoverer, self).__init__()
        
        self.config = config
        # 保存logger参数，如果为None则使用main_logger
        self.logger = logger if logger is not None else main_logger
        self.obs_dim = config.obs_dim
        self.n_z = config.n_z
        self.action_dim = config.action_dim
        self.hidden_dim = config.hidden_size
        self.gru_hidden_dim = config.gru_hidden_size
        
        # Actor网络（每个智能体共享）
        # 及早初始化网络层，避免延迟初始化导致的模型加载问题
        self.actor_mlp = MLP(config.obs_dim + config.n_z, config.hidden_size, config.hidden_size)
        self.actor_gru = nn.GRU(config.hidden_size, config.gru_hidden_size, batch_first=True)
        
        # 动作均值和标准差
        self.action_mean = nn.Linear(config.gru_hidden_size, config.action_dim)
        self.action_log_std = nn.Linear(config.gru_hidden_size, config.action_dim)
        # 将log_std初始化为较小的值，这样训练开始时标准差接近1
        self.action_log_std.weight.data.fill_(0.0)
        self.action_log_std.bias.data.fill_(-1.0)  # exp(-1) ≈ 0.37
        
        # 重置参数
        self.actor_hidden = None
        
        # Critic网络（中心化价值函数）
        self.critic_mlp = MLP(config.state_dim + config.n_louvain_skills, config.hidden_size, config.hidden_size)
        self.critic_gru = nn.GRU(config.hidden_size, config.gru_hidden_size, batch_first=True)
        self.value_head = nn.Linear(config.gru_hidden_size, 1)
        
        # 重置参数
        self.critic_hidden = None
        
        # 初始化网络权重
        self._init_weights()
    
    def _init_weights(self):
        """初始化网络权重，提高训练稳定性"""
        # 初始化MLP层权重 (已在MLP构造函数中完成，这里无需重复)
        # self.actor_mlp 和 self.critic_mlp 在构造时已经初始化了权重
        
        # 初始化GRU权重
        initialize_weights(self.actor_gru, gain=1.0)
        initialize_weights(self.critic_gru, gain=1.0)
        
        # 初始化动作均值输出层
        initialize_weights(self.action_mean, gain=0.01)
        
        # 初始化价值头
        initialize_weights(self.value_head, gain=0.01)  # 价值函数输出层使用较小的初始化
    
    def init_hidden(self, batch_size=1):
        """初始化GRU隐藏状态"""
        device = next(self.parameters()).device
        self.actor_hidden = torch.zeros(1, batch_size, self.gru_hidden_dim, device=device)
        self.critic_hidden = torch.zeros(1, batch_size, self.gru_hidden_dim, device=device)
    
    def reset_hidden_periodic(self, episode_step, reset_interval=100):
        """
        周期性重置GRU隐藏状态，防止长时间积累导致数值不稳定
        
        参数:
            episode_step: 当前回合步数
            reset_interval: 重置间隔步数，默认每100步重置一次
        """
        if episode_step % reset_interval == 0 and episode_step > 0:
            if self.actor_hidden is not None and self.critic_hidden is not None:
                batch_size = self.actor_hidden.size(1)
                self.logger.debug(f"在步骤 {episode_step} 周期性重置隐藏状态")
                self.init_hidden(batch_size)
    
    def get_value(self, state, team_skill, batch_first=True):
        """获取价值函数值"""
        batch_size = state.size(0)
        
        # 确保state是float32类型
        state = state.float()
        
        if isinstance(team_skill, int) or isinstance(team_skill, torch.Tensor):
            # 将技能索引转换为独热编码
            if isinstance(team_skill, int):
                team_skill = torch.tensor([team_skill], device=state.device)
            elif team_skill.dim() == 0:  # 处理标量张量
                team_skill = team_skill.unsqueeze(0)
            
            if team_skill.dim() == 1:
                team_skill_onehot = F.one_hot(team_skill.long(), self.config.n_louvain_skills).float()
            else:
                team_skill_onehot = team_skill.float()
        else:
            team_skill_onehot = team_skill.float()

        # 拼接全局状态和团队技能
        critic_input = torch.cat([state, team_skill_onehot], dim=-1)
        
        # 前向传播
        critic_features = self.critic_mlp(critic_input)
        
        # 确保critic_features是3D的 [batch_size, seq_len, hidden_dim]
        if critic_features.dim() == 2:
            critic_features = critic_features.unsqueeze(1)  # 添加时序维度
        
        # 初始化隐藏状态（如果需要）
        if self.critic_hidden is None or self.critic_hidden.size(1) != batch_size:
            device = critic_features.device
            self.critic_hidden = torch.zeros(1, batch_size, self.gru_hidden_dim, device=device)
            
        critic_output, self.critic_hidden = self.critic_gru(critic_features, self.critic_hidden)
        
        # 移除时序维度
        critic_output = critic_output.squeeze(1)
            
        value = self.value_head(critic_output)
        
        # 确保返回的值是float32类型
        return value.float()
    
    def forward(self, observation, agent_skill, deterministic=False):
        """
        前向传播，生成动作
        
        参数:
            observation: 智能体观测 [batch_size, obs_dim]
            agent_skill: 个体技能索引 [batch_size] 或独热编码 [batch_size, n_z]
            deterministic: 是否使用确定性策略
            
        返回:
            action: 动作 [batch_size, action_dim]
            action_logprob: 动作对数概率 [batch_size]
            action_distribution: 动作分布
        """
        batch_size = observation.size(0)
        
        # 确保observation是float32类型
        observation = observation.float()
        
        if isinstance(agent_skill, int) or isinstance(agent_skill, torch.Tensor):
            # 将技能索引转换为独热编码
            if isinstance(agent_skill, int):
                agent_skill = torch.tensor([agent_skill], device=observation.device)
            elif agent_skill.dim() == 0:  # 处理标量张量
                agent_skill = agent_skill.unsqueeze(0)  # 转换为一维张量
            
            # 确保是一维张量后进行独热编码
            if agent_skill.dim() == 1:
                agent_skill_onehot = F.one_hot(agent_skill.long(), self.n_z).float()
            else:
                agent_skill_onehot = agent_skill.float()  # 已经是独热编码，确保是float32
        else:
            agent_skill_onehot = agent_skill.float()
        
        # 拼接观测和个体技能
        actor_input = torch.cat([observation, agent_skill_onehot], dim=-1)
        self.logger.debug(f"SkillDiscoverer.forward: actor_input shape: {actor_input.shape}, dtype: {actor_input.dtype}")
        
        # 前向传播
        actor_features = self.actor_mlp(actor_input).unsqueeze(1)  # 添加时序维度
        
        # 初始化隐藏状态（如果需要）
        if self.actor_hidden is None or self.actor_hidden.size(1) != batch_size:
            device = actor_features.device
            self.actor_hidden = torch.zeros(1, batch_size, self.gru_hidden_dim, device=device)
            
        actor_output, self.actor_hidden = self.actor_gru(actor_features, self.actor_hidden)
        actor_output = actor_output.squeeze(1)  # 移除时序维度
        
        # 生成动作分布参数并进行数值稳定性处理
        # 1. 使用tanh限制action_mean的范围在[-1,1]之间，然后可以根据需要进行缩放
        action_mean_raw = self.action_mean(actor_output)
        action_mean = torch.tanh(action_mean_raw) * 3.0  # 限制在[-3,3]范围内
        
        # 2. 限制action_log_std的范围，防止exp后溢出
        action_log_std = torch.clamp(self.action_log_std(actor_output), min=-10.0, max=2.0)
        
        # 3. 确保std不为0，避免除零错误
        action_std = torch.exp(action_log_std) + 1e-6
        
        # 检查NaN或Inf并记录日志
        if torch.isnan(action_mean).any() or torch.isinf(action_mean).any():
            self.logger.warning("警告: action_mean中检测到NaN或Inf值!")
            self.logger.warning(f"action_mean统计: 形状={action_mean.shape}, 均值={action_mean.mean().item() if not torch.isnan(action_mean).all() else 'NaN'}, 标准差={action_mean.std().item() if not torch.isnan(action_mean).all() else 'NaN'}")
            # 替换NaN和Inf值
            action_mean = torch.nan_to_num(action_mean, nan=0.0, posinf=1.0, neginf=-1.0)
            self.logger.info("已将action_mean中的NaN和Inf值替换为有限值")
            
        if torch.isnan(action_std).any() or torch.isinf(action_std).any() or (action_std <= 1e-6).any():
            self.logger.warning(f"警告: action_std中检测到NaN、Inf或非常小的值!")
            self.logger.warning(f"action_std统计: 形状={action_std.shape}, 均值={action_std.mean().item() if not torch.isnan(action_std).all() else 'NaN'}, 标准差={action_std.std().item() if not torch.isnan(action_std).all() else 'NaN'}")
            # 替换NaN和Inf值
            action_std = torch.nan_to_num(action_std, nan=1.0, posinf=1.0, neginf=1.0)
            self.logger.info("已将action_std中的NaN和Inf值替换为有限值")
            
        # 添加数值稳定性处理
        # 确保action_std不会太小，避免数值问题
        action_std = torch.clamp(action_std, min=1e-6)
        
        # 创建正态分布前再次确保参数有效
        action_mean = torch.nan_to_num(action_mean, nan=0.0, posinf=3.0, neginf=-3.0)
        action_std = torch.clamp(torch.nan_to_num(action_std, nan=1.0, posinf=1.0), min=1e-6)
        
        try:
            # 创建正态分布
            action_distribution = Normal(action_mean, action_std)
            
            # 采样或选择最佳动作
            if deterministic:
                action = action_mean
            else:
                try:
                    # 使用重参数化技巧采样，可能更稳定
                    # reparameterization trick: 先从标准正态分布采样，再缩放平移
                    epsilon = torch.randn_like(action_mean)
                    action = action_mean + action_std * epsilon
                except Exception as e:
                    self.logger.error(f"采样动作时发生错误: {e}")
                    # 安全回退到确定性动作
                    action = action_mean
                    self.logger.info("采样失败，回退到确定性动作")
            
            # 计算动作对数概率
            try:
                action_logprob = action_distribution.log_prob(action).sum(dim=-1)
                # 检查并处理无穷大/NaN的log_prob
                if torch.isnan(action_logprob).any() or torch.isinf(action_logprob).any():
                    self.logger.warning("检测到action_logprob中有NaN或Inf值")
                    action_logprob = torch.nan_to_num(action_logprob, nan=0.0, posinf=-1e3, neginf=-1e3)
            except Exception as e:
                self.logger.error(f"计算动作对数概率时发生错误: {e}")
                action_logprob = torch.zeros(batch_size, device=action_mean.device)
                self.logger.info("已使用零对数概率作为回退值")
                
        except Exception as e:
            # 完全回退方案：使用标准正态分布
            self.logger.error(f"创建Normal分布时发生错误: {e}")
            self.logger.error(f"action_mean: {action_mean}")
            self.logger.error(f"action_std: {action_std}")
            
            # 使用安全的默认值
            action_mean = torch.zeros_like(action_mean)
            action_std = torch.ones_like(action_std)
            action_distribution = Normal(action_mean, action_std)
            action = action_mean if deterministic else action_mean + action_std * torch.randn_like(action_mean)
            action_logprob = torch.zeros(batch_size, device=action_mean.device)
            self.logger.info("使用安全的默认分布和动作")
        
        return action, action_logprob, action_distribution

class IndividualDiscriminator(nn.Module):
    """
    个体技能判别器
    在HMALS中，它的作用是判断在当前最低层团队任务 Z_1 的背景下，
    个体技能 z_i 的可区分性。
    """
    def __init__(self, config):
        super(IndividualDiscriminator, self).__init__()
        
        self.config = config
        self.n_louvain_skills = config.n_louvain_skills
        
        self.model = MLP(
            input_dim=config.obs_dim + config.n_louvain_skills,  # 观测 + 团队技能
            hidden_dim=config.hidden_size,
            output_dim=config.n_z,
            n_layers=2
        )
    
    def forward(self, observation, team_skill):
        """
        参数:
            observation: 智能体观测 [batch_size, obs_dim]
            team_skill: 团队技能索引 [batch_size] 或独热编码 [batch_size, n_Z]。
                        在HMALS中，这应该是最低层的团队技能 Z_1。
            
        返回:
            logits: 个体技能logits [batch_size, n_z]
        """
        # 确保observation是float32类型
        observation = observation.float()
        
        if isinstance(team_skill, int) or isinstance(team_skill, torch.Tensor):
            # 将技能索引转换为独热编码
            if isinstance(team_skill, int):
                team_skill = torch.tensor([team_skill], device=observation.device)
            elif team_skill.dim() == 0:  # 处理标量张量
                team_skill = team_skill.unsqueeze(0)  # 转换为一维张量
            
            # 确保是一维张量后进行独热编码
            if team_skill.dim() == 1:
                team_skill_onehot = F.one_hot(team_skill.long(), self.config.n_louvain_skills).float()
            else:
                team_skill_onehot = team_skill.float()  # 已经是独热编码，确保是float32
        else:
            team_skill_onehot = team_skill.float()
        
        # 拼接观测和团队技能
        discriminator_input = torch.cat([observation, team_skill_onehot], dim=-1)
        
        return self.model(discriminator_input)
