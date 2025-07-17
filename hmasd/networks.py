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
    def __init__(self, input_dim, hidden_dim, output_dim, n_layers=2, last_layer_gain=0.01):
        super(MLP, self).__init__()
        
        layers = []
        dims = [input_dim] + [hidden_dim] * n_layers + [output_dim]
        
        for i in range(len(dims) - 1):
            layers.append(nn.Linear(dims[i], dims[i+1]))
            if i < len(dims) - 2:  # 不在最后一层应用激活函数
                layers.append(nn.ReLU())
        
        self.model = nn.Sequential(*layers)
        
        # 初始化权重，使用较小的增益因子以避免大梯度
        initialize_weights(self.model, gain=1.0, last_layer_gain=last_layer_gain)
    
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
            
            # 输出团队技能分布
            team_skill_logits = self.team_skill_head(decoded).squeeze(1)
            
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
            
            # 添加Z，使用clone()创建新张量，防止原地修改导致自动求导错误
            Z_clone = Z.clone().detach()
            Z_embedded = self.team_skill_embedding(Z_clone.unsqueeze(1))
            decoder_inputs.append(Z_embedded)
            
            # 添加z1到z_{step-1}
            for i in range(step - 1):
                # 使用clone()创建新张量，防止原地修改导致自动求导错误
                z_i_clone = z[:, i].clone().detach()
                zi_embedded = self.agent_skill_embedding(z_i_clone.unsqueeze(1))
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
    """技能协调器（高层策略）"""
    def __init__(self, config):
        super(SkillCoordinator, self).__init__()
        
        self.config = config
        self.n_Z = config.n_Z
        self.n_z = config.n_z
        self.use_opt = config.use_opt
        
        # 实体特征嵌入层
        self.state_embedding = nn.Linear(config.state_dim, config.embedding_dim)
        self.obs_embedding = nn.Linear(config.obs_dim, config.embedding_dim)
        self.positional_encoding = PositionalEncoding(config.embedding_dim)
        
        if self.use_opt:
            # 决策层OPT模块：专门用于技能选择的交互解耦
            self.decision_opt = OPT(
                input_dim=config.embedding_dim,
                num_prototypes=config.opt_num_prototypes,
                prototype_dim=config.opt_prototype_dim,
                num_layers=config.opt_layers
            )
            # 将OPT输出投影到适合技能解码的维度
            if config.opt_prototype_dim != config.embedding_dim:
                self.opt_to_decoder_projection = nn.Linear(config.opt_prototype_dim, config.embedding_dim)
            else:
                self.opt_to_decoder_projection = nn.Identity()
        else:
            # 使用标准的Transformer编码器作为后备
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=config.embedding_dim,
                nhead=config.n_heads,
                dim_feedforward=config.embedding_dim * 4,
                batch_first=True
            )
            self.fallback_encoder = nn.TransformerEncoder(encoder_layer, config.n_encoder_layers)
        
        # 技能解码器
        self.skill_decoder = SkillDecoder(
            config.embedding_dim,
            config.n_decoder_layers,
            config.n_heads,
            config.n_Z,
            config.n_z
        )
        
        # 高层价值函数 - 基于解耦后的特征
        self.value_head_state = nn.Linear(config.embedding_dim, 1)
        self.value_heads_obs = nn.ModuleList([
            nn.Linear(config.embedding_dim, 1) for _ in range(config.n_agents)
        ])
        
        # 初始化网络权重
        self._init_weights()
    
    def _init_weights(self):
        """初始化网络权重，提高训练稳定性"""
        # 初始化嵌入层
        initialize_weights(self.state_embedding, gain=1.0)
        initialize_weights(self.obs_embedding, gain=1.0)
        
        # 初始化价值头权重
        initialize_weights(self.value_head_state, gain=0.01)  # 价值函数输出层使用较小的初始化
        for value_head in self.value_heads_obs:
            initialize_weights(value_head, gain=0.01)
    
    def _build_entity_sequence(self, state, observations):
        """
        构造实体特征序列，用于OPT模块处理
        
        参数:
            state: 全局状态 [batch_size, state_dim]
            observations: 所有智能体观测 [batch_size, n_agents, obs_dim]
            
        返回:
            entity_features: 实体特征序列 [batch_size, 1+n_agents, embedding_dim]
        """
        batch_size, n_agents, obs_dim = observations.size()
        
        # 嵌入全局状态和局部观测
        embedded_state = self.state_embedding(state).unsqueeze(1)  # [batch_size, 1, embedding_dim]
        embedded_obs = self.obs_embedding(observations.reshape(-1, obs_dim))
        embedded_obs = embedded_obs.reshape(batch_size, n_agents, -1)  # [batch_size, n_agents, embedding_dim]
        
        # 将状态和观测拼接作为实体序列
        entity_features = torch.cat([embedded_state, embedded_obs], dim=1)  # [batch_size, 1+n_agents, embedding_dim]
        
        # 应用位置编码
        entity_features = self.positional_encoding(entity_features)
        
        return entity_features
    
    def get_value(self, state, observations):
        """获取高层价值函数值"""
        batch_size, n_agents, obs_dim = observations.size()
        device = state.device
        
        # 确保输入是float32类型
        state = state.float()
        observations = observations.float()
        
        # 构造实体特征序列
        entity_features = self._build_entity_sequence(state, observations)
        
        if self.use_opt:
            # 使用决策层OPT进行交互解耦
            disentangled_features, cd_loss, _, _ = self.decision_opt(entity_features)
            # 投影到解码器维度
            processed_features = self.opt_to_decoder_projection(disentangled_features)
        else:
            # 使用标准编码器
            processed_features = self.fallback_encoder(entity_features)
            cd_loss = torch.tensor(0.0, device=device, requires_grad=True)
        
        # 拆分处理后的特征
        encoded_state = processed_features[:, 0:1, :]  # [batch_size, 1, embedding_dim]
        encoded_observations = processed_features[:, 1:, :]  # [batch_size, n_agents, embedding_dim]
        
        # 全局状态价值
        state_value = self.value_head_state(encoded_state.squeeze(1))
        
        # 每个智能体的观测价值
        agent_values = []
        for i in range(min(self.config.n_agents, encoded_observations.size(1))):
            agent_value = self.value_heads_obs[i](encoded_observations[:, i, :])
            agent_values.append(agent_value)
            
        # 返回价值和CD损失，以便在训练中使用
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
        
        if self.use_opt:
            # 使用决策层OPT进行交互解耦
            disentangled_features, cd_loss, cmi_loss, _ = self.decision_opt(entity_features, history_context)
            # 投影到解码器维度
            processed_features = self.opt_to_decoder_projection(disentangled_features)
        else:
            # 使用标准编码器
            processed_features = self.fallback_encoder(entity_features)
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
                # 使用clone()创建新张量，防止原地修改导致自动求导错误
                Z_clone = Z.clone().detach()
                z_clone = z[:, :i].clone().detach() if i > 0 else None
                
                try:
                    zi_logits = self.skill_decoder(encoded_state, encoded_observations, Z_clone, z_clone, step=i+1)
                    
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
                        
                    z[:, i] = zi
                    
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
        self.use_opt = config.use_opt
        
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
        
        # Critic网络（中心化价值函数）- 使用FiLM进行状态-技能融合
        if self.use_opt:
            # 低层OPT模块：用于处理全局状态的交互解耦
            self.critic_opt = OPT(
                input_dim=config.embedding_dim,
                num_prototypes=config.opt_num_prototypes,
                prototype_dim=config.opt_prototype_dim,
                num_layers=config.opt_layers
            )
            # 状态嵌入层
            self.state_embedding = nn.Linear(config.state_dim, config.embedding_dim)
            # 将OPT输出投影到适合价值计算的维度
            if config.opt_prototype_dim != config.embedding_dim:
                self.opt_to_value_projection = nn.Linear(config.opt_prototype_dim, config.embedding_dim)
            else:
                self.opt_to_value_projection = nn.Identity()
            # 状态编码器：只处理状态特征，不再拼接技能
            self.critic_state_encoder = MLP(config.embedding_dim, config.hidden_size, config.hidden_size)
        else:
            # 状态编码器：只处理状态特征，不再拼接技能
            self.critic_state_encoder = MLP(config.state_dim, config.hidden_size, config.hidden_size)
        
        # FiLM层：团队技能生成调制参数
        self.critic_skill_film_generator = nn.Linear(config.n_Z, config.hidden_size * 2)  # 生成gamma和beta
        
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
        
        # 如果使用OPT，初始化状态嵌入层和投影层
        if self.use_opt:
            initialize_weights(self.state_embedding, gain=1.0)
            if hasattr(self, 'opt_to_value_projection'):
                initialize_weights(self.opt_to_value_projection, gain=1.0)
    
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
        """获取价值函数值 - 使用FiLM进行状态-技能融合"""
        batch_size = state.size(0)
        device = state.device
        
        # 确保state是float32类型
        state = state.float()
        
        if isinstance(team_skill, int) or isinstance(team_skill, torch.Tensor):
            # 将技能索引转换为独热编码
            if isinstance(team_skill, int):
                team_skill = torch.tensor([team_skill], device=state.device)
            elif team_skill.dim() == 0:  # 处理标量张量
                team_skill = team_skill.unsqueeze(0)
            
            if team_skill.dim() == 1:
                team_skill_onehot = F.one_hot(team_skill, self.config.n_Z).float()
            else:
                team_skill_onehot = team_skill.float()
        else:
            team_skill_onehot = team_skill.float()

        if self.use_opt:
            # 使用低层OPT处理全局状态
            # 将状态嵌入到embedding空间
            embedded_state = self.state_embedding(state).unsqueeze(1)  # [batch_size, 1, embedding_dim]
            
            # 通过OPT解耦全局状态中的交互模式
            disentangled_state, cd_loss, _, _ = self.critic_opt(embedded_state)
            
            # 投影回价值计算维度并去除序列维度
            processed_state = self.opt_to_value_projection(disentangled_state).squeeze(1)  # [batch_size, embedding_dim]
        else:
            # 标准方式：直接处理全局状态
            processed_state = state
            cd_loss = torch.tensor(0.0, device=device, requires_grad=True)
        
        # 关键修改：使用FiLM代替简单拼接
        # 1. 状态特征编码（不包含技能信息）
        state_features = self.critic_state_encoder(processed_state)  # [batch_size, hidden_size]
        
        # 2. 技能生成FiLM调制参数
        film_params = self.critic_skill_film_generator(team_skill_onehot)  # [batch_size, hidden_size * 2]
        gamma, beta = torch.chunk(film_params, 2, dim=-1)  # 各自为 [batch_size, hidden_size]
        
        # 3. FiLM调制：gamma * state_features + beta
        # 这种方式让技能信息能够动态调整状态特征，实现强条件依赖
        modulated_features = gamma * state_features + beta  # [batch_size, hidden_size]
        
        # 确保modulated_features是3D的 [batch_size, seq_len, hidden_dim]
        if modulated_features.dim() == 2:
            modulated_features = modulated_features.unsqueeze(1)  # 添加时序维度
        
        # 初始化隐藏状态（如果需要）
        if self.critic_hidden is None or self.critic_hidden.size(1) != batch_size:
            self.critic_hidden = torch.zeros(1, batch_size, self.gru_hidden_dim, device=device)
            
        critic_output, self.critic_hidden = self.critic_gru(modulated_features, self.critic_hidden)
        
        # 移除时序维度
        critic_output = critic_output.squeeze(1)
            
        value = self.value_head(critic_output)
        
        # 确保返回的值是float32类型，同时返回cd_loss
        return value.float(), cd_loss
    
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
                agent_skill_onehot = F.one_hot(agent_skill, self.n_z).float()
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

class TeamDiscriminator(nn.Module):
    """团队技能判别器"""
    def __init__(self, config):
        super(TeamDiscriminator, self).__init__()
        
        self.model = MLP(
            input_dim=config.state_dim,
            hidden_dim=config.hidden_size,
            output_dim=config.n_Z,
            n_layers=2,
            last_layer_gain=1.0  # 为判别器使用更大的初始化增益
        )
    
    def forward(self, state):
        """
        参数:
            state: 全局状态 [batch_size, state_dim]
            
        返回:
            logits: 团队技能logits [batch_size, n_Z]
        """
        # 确保state是float32类型
        state = state.float()
        return self.model(state)

class IndividualDiscriminator(nn.Module):
    """个体技能判别器"""
    def __init__(self, config):
        super(IndividualDiscriminator, self).__init__()
        
        self.config = config
        self.n_Z = config.n_Z
        
        self.model = MLP(
            input_dim=config.obs_dim + config.n_Z,  # 观测 + 团队技能
            hidden_dim=config.hidden_size,
            output_dim=config.n_z,
            n_layers=2,
            last_layer_gain=1.0  # 为判别器使用更大的初始化增益
        )
    
    def forward(self, observation, team_skill):
        """
        参数:
            observation: 智能体观测 [batch_size, obs_dim]
            team_skill: 团队技能索引 [batch_size] 或独热编码 [batch_size, n_Z]
            
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
                team_skill_onehot = F.one_hot(team_skill, self.config.n_Z).float()
            else:
                team_skill_onehot = team_skill.float()  # 已经是独热编码，确保是float32
        else:
            team_skill_onehot = team_skill.float()
        
        # 拼接观测和团队技能
        discriminator_input = torch.cat([observation, team_skill_onehot], dim=-1)
        
        return self.model(discriminator_input)
