import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torch.distributions import Normal, Categorical
import logging
from logger import main_logger
from hmasd.r_mappo_utils import CNNBase, MLPBase, RNNLayer, ACTLayer, PopArt, check, get_shape_from_obs_space, init

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


class ResBlock(nn.Module):
    """残差块 - 用于构建更深的网络"""
    def __init__(self, hidden_dim):
        super(ResBlock, self).__init__()
        self.block = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim)
        )
        self.activation = nn.GELU()
        
        # 初始化权重
        for layer in self.block:
            if isinstance(layer, nn.Linear):
                initialize_weights(layer, gain=1.0)

    def forward(self, x):
        return self.activation(x + self.block(x))  # 残差连接

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
    """技能解码器"""
    def __init__(self, embedding_dim, n_layers, n_heads, n_Z, n_z):
        super(SkillDecoder, self).__init__()
        
        self.embedding_dim = embedding_dim
        self.Z0_embedding = nn.Embedding(1, embedding_dim)
        self.team_skill_embedding = nn.Embedding(n_Z, embedding_dim)
        self.agent_skill_embedding = nn.Embedding(n_z, embedding_dim)
        self.positional_encoding = PositionalEncoding(embedding_dim)
        
        decoder_layer = nn.TransformerDecoderLayer(
            d_model=embedding_dim,
            nhead=n_heads,
            dim_feedforward=embedding_dim * 4,
            batch_first=True
        )
        self.transformer_decoder = nn.TransformerDecoder(decoder_layer, n_layers)
        
        # 【数值稳定性修复】添加LayerNorm层防止exploding logits
        self.output_norm = nn.LayerNorm(embedding_dim)
        
        # 输出头
        self.team_skill_head = nn.Linear(embedding_dim, n_Z)
        self.agent_skill_head = nn.Linear(embedding_dim, n_z)
    
    def forward(self, encoded_state, encoded_observations, Z=None, z=None, step=0):
        """
        参数:
            encoded_state: 编码后的状态 [batch_size, 1, embedding_dim]
            encoded_observations: 编码后的观测 [batch_size, n_agents, embedding_dim]
            Z: 已选择的团队技能索引 [batch_size]，可选
            z: 已选择的个体技能索引列表 [batch_size, step]，可选
            step: 当前解码步骤
            
        返回:
            output: 技能分布 [batch_size, n_Z/n_z]
        """
        batch_size = encoded_state.size(0)
        device = encoded_state.device
        
        if step == 0:  # 生成团队技能Z
            # 使用特殊起始符Z0
            Z0_idx = torch.zeros(batch_size, 1, dtype=torch.long, device=device)
            decoder_input = self.Z0_embedding(Z0_idx)
            decoder_input = self.positional_encoding(decoder_input)
            
            # Transformer解码
            memory = torch.cat([encoded_state, encoded_observations], dim=1)
            decoded = self.transformer_decoder(decoder_input, memory)
            
            # 【数值稳定性修复】应用LayerNorm防止exploding logits
            normalized_decoded = self.output_norm(decoded)
            
            # 输出团队技能分布
            team_skill_logits = self.team_skill_head(normalized_decoded).squeeze(1)
            
            # 记录团队技能logits的统计信息
            with torch.no_grad():
                is_nan = torch.isnan(team_skill_logits).any().item()
                is_inf = torch.isinf(team_skill_logits).any().item()
                logits_mean = team_skill_logits.mean().item()
                logits_std = team_skill_logits.std().item()
                logits_min = team_skill_logits.min().item()
                logits_max = team_skill_logits.max().item()
                main_logger.debug(f"团队技能logits统计: 均值={logits_mean:.4f}, 标准差={logits_std:.4f}, "
                      f"最小值={logits_min:.4f}, 最大值={logits_max:.4f}, "
                      f"含NaN={is_nan}, 含Inf={is_inf}")
                
                # 如果检测到NaN或Inf，输出更详细的信息
                if is_nan or is_inf:
                    main_logger.warning("警告: 团队技能logits包含NaN或Inf值！")
                    main_logger.warning(f"logits形状: {team_skill_logits.shape}")
                    main_logger.warning(f"NaN位置: {torch.isnan(team_skill_logits).nonzero()}")
                    main_logger.warning(f"Inf位置: {torch.isinf(team_skill_logits).nonzero()}")
                    
                # 检测是否有极端值，可能导致数值不稳定
                extreme_threshold = 50.0  # 定义极端值阈值
                has_extreme = (torch.abs(team_skill_logits) > extreme_threshold).any().item()
                if has_extreme:
                    main_logger.warning(f"警告: 团队技能logits存在绝对值大于{extreme_threshold}的极端值!")
                    extreme_indices = (torch.abs(team_skill_logits) > extreme_threshold).nonzero()
                    extreme_values = team_skill_logits[extreme_indices[:, 0], extreme_indices[:, 1]]
                    main_logger.warning(f"极端值示例 (最多10个): {extreme_values[:10].tolist()}")
                    
            # 应用数值稳定性措施，裁剪极端值
            clip_threshold = 50.0  # 定义裁剪阈值
            team_skill_logits = torch.clamp(team_skill_logits, min=-clip_threshold, max=clip_threshold)
            
            return team_skill_logits
        else:  # 生成第step个智能体的个体技能zi
            # 构建已解码序列
            seq_len = step + 1  # Z0 + Z + z1 + ... + z_{step-1}
            decoder_inputs = []
            
            # 添加Z0
            Z0_idx = torch.zeros(batch_size, 1, dtype=torch.long, device=device)
            decoder_inputs.append(self.Z0_embedding(Z0_idx))
            
            # 【关键修复】移除detach()操作，保持自回归序列的梯度连续性
            # 这确保了技能解码器能够通过整个序列进行端到端的梯度传播
            Z_embedded = self.team_skill_embedding(Z.unsqueeze(1))
            decoder_inputs.append(Z_embedded)
            
            # 添加z1到z_{step-1}，保持梯度流
            for i in range(step - 1):
                zi_embedded = self.agent_skill_embedding(z[:, i].unsqueeze(1))
                decoder_inputs.append(zi_embedded)
            
            # 拼接所有嵌入
            decoder_input = torch.cat(decoder_inputs, dim=1)
            decoder_input = self.positional_encoding(decoder_input)
            
            # Transformer解码
            memory = torch.cat([encoded_state, encoded_observations], dim=1)
            decoded = self.transformer_decoder(decoder_input, memory)
            
            # 输出个体技能分布（仅取最后一步）
            agent_skill_logits = self.agent_skill_head(decoded[:, -1, :])
            
            # 记录个体技能logits的统计信息
            with torch.no_grad():
                is_nan = torch.isnan(agent_skill_logits).any().item()
                is_inf = torch.isinf(agent_skill_logits).any().item()
                logits_mean = agent_skill_logits.mean().item()
                logits_std = agent_skill_logits.std().item()
                logits_min = agent_skill_logits.min().item()
                logits_max = agent_skill_logits.max().item()
                main_logger.debug(f"智能体{step-1}技能logits统计: 均值={logits_mean:.4f}, 标准差={logits_std:.4f}, "
                      f"最小值={logits_min:.4f}, 最大值={logits_max:.4f}, "
                      f"含NaN={is_nan}, 含Inf={is_inf}")
                
                # 如果检测到NaN或Inf，输出更详细的信息
                if is_nan or is_inf:
                    main_logger.warning("警告: 个体技能logits包含NaN或Inf值！")
                    main_logger.warning(f"logits形状: {agent_skill_logits.shape}")
                    main_logger.warning(f"NaN位置: {torch.isnan(agent_skill_logits).nonzero()}")
                    main_logger.warning(f"Inf位置: {torch.isinf(agent_skill_logits).nonzero()}")
                    
                # 检测是否有极端值，可能导致数值不稳定
                extreme_threshold = 50.0  # 定义极端值阈值
                has_extreme = (torch.abs(agent_skill_logits) > extreme_threshold).any().item()
                if has_extreme:
                    main_logger.warning(f"警告: 个体技能logits存在绝对值大于{extreme_threshold}的极端值!")
                    extreme_indices = (torch.abs(agent_skill_logits) > extreme_threshold).nonzero()
                    extreme_values = agent_skill_logits[extreme_indices[:, 0], extreme_indices[:, 1]]
                    main_logger.warning(f"极端值示例 (最多10个): {extreme_values[:10].tolist()}")
            
            # 应用数值稳定性措施，裁剪极端值
            clip_threshold = 50.0  # 定义裁剪阈值
            agent_skill_logits = torch.clamp(agent_skill_logits, min=-clip_threshold, max=clip_threshold)
            
            return agent_skill_logits

class SkillCoordinator(nn.Module):
    """技能协调器（高层策略）- 简化版"""
    def __init__(self, config):
        super(SkillCoordinator, self).__init__()
        
        self.config = config
        self.n_Z = config.n_Z
        self.n_z = config.n_z
        
        self.state_embedding = nn.Linear(config.state_dim, config.embedding_dim)
        self.obs_embedding = nn.Linear(config.obs_dim, config.embedding_dim)
        self.positional_encoding = PositionalEncoding(config.embedding_dim)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config.embedding_dim,
            nhead=config.n_heads,
            dim_feedforward=config.embedding_dim * 4,
            batch_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, config.n_encoder_layers)
        
        self.skill_decoder = SkillDecoder(
            config.embedding_dim,
            config.n_decoder_layers,
            config.n_heads,
            config.n_Z,
            config.n_z
        )
        
        self.value_head_state = nn.Linear(config.embedding_dim, 1)
        self.value_heads_obs = nn.ModuleList([
            nn.Linear(config.embedding_dim, 1) for _ in range(config.n_agents)
        ])
        
        self._init_weights()
    
    def _init_weights(self):
        """初始化网络权重，提高训练稳定性"""
        initialize_weights(self.state_embedding, gain=1.0)
        initialize_weights(self.obs_embedding, gain=1.0)
        initialize_weights(self.value_head_state, gain=0.01)
        for value_head in self.value_heads_obs:
            initialize_weights(value_head, gain=0.01)
    
    def _build_entity_sequence(self, state, observations):
        batch_size, n_agents, _ = observations.size()
        embedded_state = self.state_embedding(state).unsqueeze(1)
        embedded_obs = self.obs_embedding(observations.view(-1, self.config.obs_dim)).view(batch_size, n_agents, -1)
        entity_features = torch.cat([embedded_state, embedded_obs], dim=1)
        return self.positional_encoding(entity_features)
    
    def get_value(self, state, observations):
        """
        【论文一致性修复】获取高层价值函数值
        
        根据论文Figure 3和公式(6)，高层策略有分别的价值函数：
        - V^h(ŝ): 基于编码状态的价值函数，用于团队技能
        - V^h(ô_i): 基于每个智能体编码观测的价值函数，用于个体技能
        
        返回分离的价值函数，而不是合并的单一价值
        """
        batch_size, n_agents, obs_dim = observations.size()
        device = state.device
        
        # 确保输入是float32类型
        state = state.float()
        observations = observations.float()
        
        # 构造实体特征序列
        entity_features = self._build_entity_sequence(state, observations)
        
        processed_features = self.encoder(entity_features)
        cd_loss = torch.tensor(0.0, device=device, requires_grad=True)
        
        # 【论文一致性修复】按照Figure 3实现分别的价值函数
        # 1. 基于编码状态的价值函数 V^h(ŝ) - 用于团队技能
        encoded_state = processed_features[:, 0:1, :]  # [batch_size, 1, embedding_dim]
        state_value = self.value_head_state(encoded_state.squeeze(1))  # [batch_size, 1]
        
        # 2. 基于每个智能体编码观测的价值函数 V^h(ô_i) - 用于个体技能
        encoded_observations = processed_features[:, 1:, :]  # [batch_size, n_agents, embedding_dim]
        agent_values = []
        for i in range(n_agents):
            agent_value = self.value_heads_obs[i](encoded_observations[:, i, :])  # [batch_size, 1]
            agent_values.append(agent_value)
        
        # 【关键修复】返回分离的价值函数，严格按照论文Figure 3的设计
        # 不再合并状态价值和智能体价值，而是分别返回
        return state_value, agent_values, cd_loss
    
    def forward(self, state, observations, deterministic=False, history_context=None):
        """
        前向传播，按顺序生成技能
        
        参数:
            state: 全局状态 [batch_size, state_dim]
            observations: 所有智能体观测 [batch_size, n_agents, obs_dim]
            deterministic: 是否使用确定性策略
            history_context: 历史上下文 [batch_size, prototype_dim] (仅在使用OPT时需要)
            
        返回:
            Z: 团队技能索引 [batch_size]
            z: 个体技能索引 [batch_size, n_agents]
            Z_logits: 团队技能logits [batch_size, n_Z]
            z_logits: 个体技能logits列表 [n_agents个 [batch_size, n_z]]
            cd_loss: 对比散度损失 (仅在使用OPT时)
            cmi_loss: 条件互信息损失 (仅在使用OPT时)
        """
        batch_size = state.size(0)
        n_agents = observations.size(1)
        device = state.device
        
        # 确保输入是float32类型
        state = state.float()
        observations = observations.float()
        
        # 构造实体特征序列
        entity_features = self._build_entity_sequence(state, observations)
        
        processed_features = self.encoder(entity_features)
        cd_loss = torch.tensor(0.0, device=device, requires_grad=True)
        cmi_loss = torch.tensor(0.0, device=device, requires_grad=True)
        
        # 拆分处理后的特征
        encoded_state = processed_features[:, 0:1, :]  # [batch_size, 1, embedding_dim]
        encoded_observations = processed_features[:, 1:, :]  # [batch_size, n_agents, embedding_dim]
        
        # 生成团队技能Z
        Z_logits = self.skill_decoder(encoded_state, encoded_observations)
        
        # 在创建分布前检查Z_logits是否包含NaN或Inf，并进行更强的数值稳定性处理
        with torch.no_grad():
            is_nan = torch.isnan(Z_logits).any().item()
            is_inf = torch.isinf(Z_logits).any().item()
            if is_nan or is_inf:
                main_logger.warning("警告: 在创建Categorical分布前，Z_logits包含NaN或Inf值！")
                main_logger.warning(f"Z_logits统计: 均值={Z_logits.mean().item() if not torch.isnan(Z_logits).all() else 'NaN'}, "
                              f"标准差={Z_logits.std().item() if not torch.isnan(Z_logits).all() else 'NaN'}, "
                              f"最小值={Z_logits.min().item() if not torch.isnan(Z_logits).all() else 'NaN'}, "
                              f"最大值={Z_logits.max().item() if not torch.isnan(Z_logits).all() else 'NaN'}")
                
                # 记录问题位置的详细信息
                nan_indices = torch.isnan(Z_logits).nonzero()
                inf_indices = torch.isinf(Z_logits).nonzero()
                if len(nan_indices) > 0:
                    main_logger.warning(f"NaN位置示例 (最多5个): {nan_indices[:5].tolist()}")
                if len(inf_indices) > 0:
                    main_logger.warning(f"Inf位置示例 (最多5个): {inf_indices[:5].tolist()}")
                
                # 更强的修复措施
                Z_logits = torch.nan_to_num(Z_logits, nan=0.0, posinf=50.0, neginf=-50.0)
                main_logger.warning("已将Z_logits中的NaN和Inf值替换为有限值")
            
            # 检查极端值
            extreme_threshold = 50.0
            has_extreme = (torch.abs(Z_logits) > extreme_threshold).any().item()
            if has_extreme:
                main_logger.warning(f"警告: Z_logits存在绝对值大于{extreme_threshold}的极端值")
                # 对所有值应用裁剪，确保稳定性
                Z_logits = torch.clamp(Z_logits, min=-extreme_threshold, max=extreme_threshold)
                main_logger.warning(f"已将所有Z_logits值裁剪到[-{extreme_threshold}, {extreme_threshold}]范围内")
        
        try:
            Z_dist = Categorical(logits=Z_logits)
            
            if deterministic:
                Z = Z_logits.argmax(dim=-1)
            else:
                Z = Z_dist.sample()
            
            # 依次为每个智能体生成个体技能zi
            z = torch.zeros(batch_size, n_agents, dtype=torch.long, device=device)
            z_logits = []
            
            for i in range(n_agents):
                # 【关键修复】在前向传播中保持梯度连续性
                # 梯度切断应该只在损失计算时进行，而不是在前向传播中
                # 这确保了技能间的依赖关系能够正确学习
                Z_for_decoder = Z  # 保持梯度流，允许技能间依赖学习
                z_for_decoder = z[:, :i] if i > 0 else None  # 保持梯度流，允许技能间依赖学习
                
                try:
                    zi_logits = self.skill_decoder(encoded_state, encoded_observations, Z_for_decoder, z_for_decoder, step=i+1)
                    
                    # 在创建分布前检查zi_logits是否包含NaN或Inf，并进行更强的数值稳定性处理
                    with torch.no_grad():
                        is_nan = torch.isnan(zi_logits).any().item()
                        is_inf = torch.isinf(zi_logits).any().item()
                        if is_nan or is_inf:
                            main_logger.warning(f"警告: 在创建Categorical分布前，第{i}个智能体的zi_logits包含NaN或Inf值！")
                            main_logger.warning(f"zi_logits统计: 均值={zi_logits.mean().item() if not torch.isnan(zi_logits).all() else 'NaN'}, "
                                  f"标准差={zi_logits.std().item() if not torch.isnan(zi_logits).all() else 'NaN'}, "
                                  f"最小值={zi_logits.min().item() if not torch.isnan(zi_logits).all() else 'NaN'}, "
                                  f"最大值={zi_logits.max().item() if not torch.isnan(zi_logits).all() else 'NaN'}")
                            
                            # 记录问题位置的详细信息
                            nan_indices = torch.isnan(zi_logits).nonzero()
                            inf_indices = torch.isinf(zi_logits).nonzero()
                            if len(nan_indices) > 0:
                                main_logger.warning(f"第{i}个智能体NaN位置示例(最多5个): {nan_indices[:5].tolist()}")
                            if len(inf_indices) > 0:
                                main_logger.warning(f"第{i}个智能体Inf位置示例(最多5个): {inf_indices[:5].tolist()}")
                            
                            # 更强的修复措施
                            zi_logits = torch.nan_to_num(zi_logits, nan=0.0, posinf=50.0, neginf=-50.0)
                            main_logger.warning(f"已将第{i}个智能体的zi_logits中的NaN和Inf值替换为有限值")
                        
                        # 检查极端值
                        extreme_threshold = 50.0
                        has_extreme = (torch.abs(zi_logits) > extreme_threshold).any().item()
                        if has_extreme:
                            main_logger.warning(f"警告: 第{i}个智能体的zi_logits存在绝对值大于{extreme_threshold}的极端值")
                            # 对所有值应用裁剪，确保稳定性
                            zi_logits = torch.clamp(zi_logits, min=-extreme_threshold, max=extreme_threshold)
                            main_logger.warning(f"已将第{i}个智能体的所有zi_logits值裁剪到[-{extreme_threshold}, {extreme_threshold}]范围内")
                    
                    z_logits.append(zi_logits)
                    zi_dist = Categorical(logits=zi_logits)
                    
                    if deterministic:
                        zi = zi_logits.argmax(dim=-1)
                    else:
                        zi = zi_dist.sample()
                    
                    # 【保持原地操作修复】避免原地操作，使用索引赋值的安全方式
                    # 创建新的张量而不是原地修改，确保数值稳定性
                    new_z = z.clone()
                    new_z[:, i] = zi
                    z = new_z  # 重新赋值而不是原地修改
                    
                except Exception as e:
                    main_logger.error(f"在处理第{i}个智能体的zi_logits时发生错误: {e}")
                    # 如果发生错误，使用一个安全的默认值
                    safe_logits = torch.zeros((batch_size, self.n_z), device=device)
                    z_logits.append(safe_logits)
                    z[:, i] = 0  # 使用0作为默认技能索引
                    main_logger.warning(f"已为第{i}个智能体使用默认技能索引0")
                
            return Z, z, Z_logits, z_logits, cd_loss, cmi_loss
            
        except Exception as e:
            main_logger.error(f"在SkillCoordinator.forward中创建Categorical分布时发生错误: {e}")
            # 返回安全的默认值
            default_Z = torch.zeros(batch_size, dtype=torch.long, device=device)
            default_z = torch.zeros(batch_size, n_agents, dtype=torch.long, device=device)
            default_Z_logits = torch.zeros((batch_size, self.n_Z), device=device)
            default_z_logits = [torch.zeros((batch_size, self.n_z), device=device) for _ in range(n_agents)]
            main_logger.warning("由于错误，返回默认值")
            return default_Z, default_z, default_Z_logits, default_z_logits, cd_loss, cmi_loss

class R_Actor(nn.Module):
    def __init__(self, args, obs_space, action_space, n_z, device=torch.device("cpu")):
        super(R_Actor, self).__init__()
        self.hidden_size = args.hidden_size
        self._gain = args.gain
        self._use_orthogonal = args.use_orthogonal
        self._use_policy_active_masks = args.use_policy_active_masks
        self._use_naive_recurrent_policy = args.use_naive_recurrent_policy
        self._use_recurrent_policy = args.use_recurrent_policy
        self._recurrent_N = args.recurrent_N
        self.tpdv = dict(dtype=torch.float32, device=device)

        obs_shape = get_shape_from_obs_space(obs_space)
        base = CNNBase if len(obs_shape) == 3 else MLPBase
        self.base = base(args, obs_shape)
        
        self.film_generator = nn.Linear(n_z, 2 * self.hidden_size)

        if self._use_naive_recurrent_policy or self._use_recurrent_policy:
            self.rnn = RNNLayer(self.hidden_size, self.hidden_size, self._recurrent_N, self._use_orthogonal)

        self.act = ACTLayer(action_space, self.hidden_size, self._use_orthogonal, self._gain, args)

        self.to(device)

    def forward(self, obs, rnn_states, masks, agent_skill, available_actions=None, deterministic=False):
        obs = check(obs).to(**self.tpdv)
        rnn_states = check(rnn_states).to(**self.tpdv)
        masks = check(masks).to(**self.tpdv)
        agent_skill = check(agent_skill).to(**self.tpdv)
        if available_actions is not None:
            available_actions = check(available_actions).to(**self.tpdv)

        actor_features = self.base(obs)
        
        agent_skill_onehot = F.one_hot(agent_skill.long(), num_classes=self.film_generator.in_features).float()
        film_params = self.film_generator(agent_skill_onehot)
        gamma, beta = torch.chunk(film_params, 2, dim=-1)
        actor_features = gamma * actor_features + beta

        if self._use_naive_recurrent_policy or self._use_recurrent_policy:
            actor_features, rnn_states = self.rnn(actor_features, rnn_states, masks)

        actions, action_log_probs = self.act(actor_features, available_actions, deterministic)

        return actions, action_log_probs, rnn_states

    def evaluate_actions(self, obs, rnn_states, action, masks, agent_skill, available_actions=None, active_masks=None):
        is_sequence = len(obs.shape) > 2
        if is_sequence:
            T, B, _ = obs.shape
        
        obs = check(obs).to(**self.tpdv)
        rnn_states = check(rnn_states).to(**self.tpdv)
        action = check(action).to(**self.tpdv)
        masks = check(masks).to(**self.tpdv)
        agent_skill = check(agent_skill).to(**self.tpdv)
        if available_actions is not None:
            available_actions = check(available_actions).to(**self.tpdv)
        if active_masks is not None:
            active_masks = check(active_masks).to(**self.tpdv)

        actor_features = self.base(obs)
        
        agent_skill_onehot = F.one_hot(agent_skill.long(), num_classes=self.film_generator.in_features).float()
        film_params = self.film_generator(agent_skill_onehot)
        gamma, beta = torch.chunk(film_params, 2, dim=-1)
        actor_features = gamma * actor_features + beta

        if self._use_naive_recurrent_policy or self._use_recurrent_policy:
            actor_features, rnn_states = self.rnn(actor_features, rnn_states, masks)
        else:
            if is_sequence:
                # If not using RNN, flatten the features for the action layer
                actor_features = actor_features.view(T * B, -1)
                action = action.view(T * B, -1)
                if available_actions is not None:
                    available_actions = available_actions.view(T * B, -1)
                if active_masks is not None:
                    active_masks = active_masks.view(T * B, -1)

        action_log_probs, dist_entropy = self.act.evaluate_actions(actor_features, action, available_actions, active_masks=active_masks if self._use_policy_active_masks else None)
        
        if is_sequence:
            action_log_probs = action_log_probs.view(T, B, -1)

        return action_log_probs, dist_entropy

class R_Critic(nn.Module):
    def __init__(self, args, cent_obs_space, n_Z, device=torch.device("cpu")):
        super(R_Critic, self).__init__()
        self.hidden_size = args.hidden_size
        self._use_orthogonal = args.use_orthogonal
        self._use_naive_recurrent_policy = args.use_naive_recurrent_policy
        self._use_recurrent_policy = args.use_recurrent_policy
        self._recurrent_N = args.recurrent_N
        self._use_popart = args.use_popart
        self.tpdv = dict(dtype=torch.float32, device=device)
        init_method = [nn.init.xavier_uniform_, nn.init.orthogonal_][self._use_orthogonal]

        cent_obs_shape = get_shape_from_obs_space(cent_obs_space)
        base = CNNBase if len(cent_obs_shape) == 3 else MLPBase
        self.base = base(args, cent_obs_shape)
        
        self.film_generator = nn.Linear(n_Z, 2 * self.hidden_size)

        if self._use_naive_recurrent_policy or self._use_recurrent_policy:
            self.rnn = RNNLayer(self.hidden_size, self.hidden_size, self._recurrent_N, self._use_orthogonal)

        def init_(m):
            return init(m, init_method, lambda x: nn.init.constant_(x, 0))

        if self._use_popart:
            self.v_out = init_(PopArt(self.hidden_size, 1, device=device))
        else:
            self.v_out = init_(nn.Linear(self.hidden_size, 1))

        self.to(device)

    def forward(self, cent_obs, rnn_states, masks, team_skill):
        is_sequence = len(cent_obs.shape) > 2
        if is_sequence:
            T, B, _ = cent_obs.shape

        cent_obs = check(cent_obs).to(**self.tpdv)
        rnn_states = check(rnn_states).to(**self.tpdv)
        masks = check(masks).to(**self.tpdv)
        team_skill = check(team_skill).to(**self.tpdv)

        critic_features = self.base(cent_obs)
        
        team_skill_onehot = F.one_hot(team_skill.long(), num_classes=self.film_generator.in_features).float()
        film_params = self.film_generator(team_skill_onehot)
        gamma, beta = torch.chunk(film_params, 2, dim=-1)
        critic_features = gamma * critic_features + beta

        if self._use_naive_recurrent_policy or self._use_recurrent_policy:
            critic_features, rnn_states = self.rnn(critic_features, rnn_states, masks)
        else:
            if is_sequence:
                critic_features = critic_features.view(T * B, -1)

        values = self.v_out(critic_features)

        if is_sequence:
            values = values.view(T, B, -1)

        return values, rnn_states

class SkillDiscoverer(nn.Module):
    def __init__(self, config, logger=None):
        super(SkillDiscoverer, self).__init__()
        self.config = config
        self.logger = logger if logger is not None else main_logger
        
        # Adapt hmasd config to r_mappo's args format
        class Args:
            def __init__(self, config):
                self.hidden_size = config.hidden_size
                self.gain = 0.01
                self.use_orthogonal = True
                self.use_policy_active_masks = True
                self.use_naive_recurrent_policy = False
                self.use_recurrent_policy = True
                self.recurrent_N = 1
                self.use_feature_normalization = False
                self.use_popart = False
        
        args = Args(config)
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        # Create dummy spaces for initialization
        from gymnasium import spaces
        obs_space = spaces.Box(low=-np.inf, high=np.inf, shape=(config.obs_dim,))
        if getattr(config, 'action_space_type', 'continuous') == 'discrete':
            action_space = spaces.Discrete(config.action_dim)
        else:
            action_space = spaces.Box(low=-config.action_bound, high=config.action_bound, shape=(config.action_dim,))
        
        cent_obs_space = (config.state_dim,)

        self.actor = R_Actor(args, obs_space, action_space, config.n_z, device)
        self.critic = R_Critic(args, cent_obs_space, config.n_Z, device)

    def forward(self, observation, agent_skill, hidden_state, deterministic=False):
        # The new R_Actor expects masks. We can pass ones.
        masks = torch.ones(observation.size(0), 1, device=observation.device)
        actions, log_probs, new_hidden = self.actor(observation, hidden_state, masks, agent_skill, deterministic=deterministic)
        # The original forward returned a dummy distribution, we return None for that.
        return actions, log_probs, None, new_hidden

    def get_value(self, state, team_skill, critic_hidden_state=None):
        # The new R_Critic expects masks. We can pass ones.
        masks = torch.ones(state.size(0), 1, device=state.device)
        return self.critic(state, critic_hidden_state, masks, team_skill)

    def evaluate_sequence(self, observations_seq, agent_skills_seq, actions_seq, global_states_seq, team_skills_seq, initial_hxs=None, dones_seq=None, initial_critic_hxs=None):
        T, B, _ = observations_seq.shape
        # The dones_seq from buffer might be (T, B, 1), ensure it's (T, B) for mask creation
        if dones_seq.dim() > 2:
            dones_seq = dones_seq.squeeze(-1)
        masks = (1 - dones_seq.float())
        
        # Pass sequences without flattening
        log_probs, entropy = self.actor.evaluate_actions(
            observations_seq,
            initial_hxs,
            actions_seq,
            masks,
            agent_skills_seq
        )
        
        values, _ = self.critic(
            global_states_seq,
            initial_critic_hxs,
            masks,
            team_skills_seq
        )
        
        return log_probs, values, entropy

class TeamDiscriminator(nn.Module):
    """团队技能判别器 - 增强版（解决"弱判别器"问题）+ 残差连接"""
    def __init__(self, config):
        super(TeamDiscriminator, self).__init__()
        
        # 【弱判别器修复】使用残差连接的深度网络架构
        # 输入投影层：将状态维度映射到隐藏维度
        self.input_projection = nn.Linear(config.state_dim, config.hidden_size)
        
        # 【关键增强】添加残差块以提升学习能力和梯度流
        self.res_blocks = nn.ModuleList([
            ResBlock(config.hidden_size) for _ in range(2)  # 2个残差块
        ])
        
        # 最终处理层
        self.final_layers = nn.Sequential(
            nn.LayerNorm(config.hidden_size),
            nn.GELU(),
            nn.Tanh(),
            nn.Linear(config.hidden_size, config.n_Z)
        )
        
        # 初始化所有权重
        initialize_weights(self.input_projection, gain=1.0)
        for layer in self.final_layers:
            if isinstance(layer, nn.Linear):
                initialize_weights(layer, gain=1.0)
    
    def forward(self, state):
        """
        参数:
            state: 全局状态 [batch_size, state_dim]
            
        返回:
            logits: 团队技能logits [batch_size, n_Z]
        """
        # 确保state是float32类型
        state = state.float()
        
        # 输入投影
        x = self.input_projection(state)
        
        # 通过残差块
        for res_block in self.res_blocks:
            x = res_block(x)
        
        # 最终处理层
        return self.final_layers(x)

class IndividualDiscriminator(nn.Module):
    """个体技能判别器 - 增强版（解决"弱判别器"问题）+ 残差连接"""
    def __init__(self, config):
        super(IndividualDiscriminator, self).__init__()
        self.config = config
        
        # 1. 观测编码器 - 使用残差连接的深度架构
        self.obs_input_projection = nn.Linear(config.obs_dim, config.hidden_size)
        
        # 【关键增强】为观测编码器添加残差块
        self.obs_res_blocks = nn.ModuleList([
            ResBlock(config.hidden_size) for _ in range(1)  # 1个残差块用于观测编码
        ])
        
        # 2. FiLM参数生成器 (从团队技能Z生成)
        # 使用Embedding层处理离散的团队技能，然后映射到FiLM参数
        self.team_skill_embedding = nn.Embedding(config.n_Z, config.embedding_dim)
        self.film_generator = nn.Linear(config.embedding_dim, 2 * config.hidden_size)
        
        # 3. 【弱判别器修复】后续处理网络 - 使用残差连接
        # 预处理层
        self.post_film_pre = nn.Sequential(
            nn.LayerNorm(config.hidden_size),
            nn.GELU()
        )
        
        # 【关键增强】为后续处理添加残差块
        self.post_film_res_blocks = nn.ModuleList([
            ResBlock(config.hidden_size) for _ in range(1)  # 1个残差块用于后续处理
        ])
        
        # 最终输出层
        self.final_output = nn.Sequential(
            nn.LayerNorm(config.hidden_size),
            nn.GELU(),
            nn.Tanh(),
            nn.Linear(config.hidden_size, config.n_z)
        )
        
        # 初始化权重 - 确保所有层都正确初始化
        initialize_weights(self.obs_input_projection, gain=1.0)
        initialize_weights(self.team_skill_embedding, gain=1.0)
        initialize_weights(self.film_generator, gain=1.0)
        
        for layer in self.post_film_pre:
            if isinstance(layer, nn.Linear):
                initialize_weights(layer, gain=1.0)
        
        for layer in self.final_output:
            if isinstance(layer, nn.Linear):
                initialize_weights(layer, gain=1.0)

    def forward(self, observation, team_skill):
        # 确保 team_skill 是长整型的索引
        if team_skill.dtype != torch.long:
            team_skill = team_skill.long()

        # --- 增强版 Discriminator FiLM 架构实现（使用残差连接）---
        # 1. 观测编码 - 使用残差连接
        # 输入投影
        x = self.obs_input_projection(observation)
        
        # 通过观测残差块
        for res_block in self.obs_res_blocks:
            x = res_block(x)
        
        encoded_obs = x
        
        # 2. 从团队技能生成FiLM参数
        team_skill_embedded = self.team_skill_embedding(team_skill)
        if team_skill_embedded.dim() == 1:
            team_skill_embedded = team_skill_embedded.unsqueeze(0)
            
        film_params = self.film_generator(team_skill_embedded)
        gamma, beta = torch.chunk(film_params, 2, dim=-1)
        
        # 3. 应用FiLM调制
        # 确保gamma和beta可以广播到encoded_obs的形状
        if gamma.dim() < encoded_obs.dim():
            gamma = gamma.unsqueeze(1)
            beta = beta.unsqueeze(1)
            
        modulated_obs = gamma * encoded_obs + beta
        
        # 4. 后续处理 - 使用残差连接
        # 预处理
        x = self.post_film_pre(modulated_obs)
        
        # 通过后续处理残差块
        for res_block in self.post_film_res_blocks:
            x = res_block(x)
        
        # 最终输出
        return self.final_output(x)
