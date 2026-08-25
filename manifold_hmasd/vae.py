import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from hmasd.logging import main_logger

class VAEEncoder(nn.Module):
    """
    VAE编码器：将高维状态编码为低维潜变量分布
    """
    def __init__(self, state_dim, latent_dim, hidden_dims=[128, 64]):
        super(VAEEncoder, self).__init__()
        
        self.state_dim = state_dim
        self.latent_dim = latent_dim
        
        # 构建编码器网络
        layers = []
        input_dim = state_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.1)  # 防止过拟合
            ])
            input_dim = hidden_dim
        
        self.encoder = nn.Sequential(*layers)
        
        # 均值和方差分支
        self.fc_mu = nn.Linear(hidden_dims[-1], latent_dim)
        self.fc_logvar = nn.Linear(hidden_dims[-1], latent_dim)
        
        # 权重初始化
        self._init_weights()
    
    def _init_weights(self):
        """Xavier初始化"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.zeros_(m.bias)
    
    def forward(self, state):
        """
        前向传播
        
        参数:
            state: 状态 [batch_size, state_dim]
            
        返回:
            mu: 均值 [batch_size, latent_dim]
            logvar: 对数方差 [batch_size, latent_dim]
        """
        # 确保输入是float32类型
        state = state.float()
        
        # 编码
        h = self.encoder(state)
        
        # 计算均值和对数方差
        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)
        
        # 限制logvar范围，防止数值不稳定
        logvar = torch.clamp(logvar, min=-20, max=2)
        
        return mu, logvar

class VAEDecoder(nn.Module):
    """
    VAE解码器：从潜变量重构状态
    """
    def __init__(self, latent_dim, state_dim, hidden_dims=[64, 128]):
        super(VAEDecoder, self).__init__()
        
        self.latent_dim = latent_dim
        self.state_dim = state_dim
        
        # 构建解码器网络
        layers = []
        input_dim = latent_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.1)
            ])
            input_dim = hidden_dim
        
        # 最后一层不使用激活函数
        layers.append(nn.Linear(hidden_dims[-1], state_dim))
        
        self.decoder = nn.Sequential(*layers)
        
        # 权重初始化
        self._init_weights()
    
    def _init_weights(self):
        """Xavier初始化"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.zeros_(m.bias)
    
    def forward(self, z):
        """
        前向传播
        
        参数:
            z: 潜变量 [batch_size, latent_dim]
            
        返回:
            reconstructed_state: 重构状态 [batch_size, state_dim]
        """
        # 确保输入是float32类型
        z = z.float()
        
        # 解码
        reconstructed_state = self.decoder(z)
        
        return reconstructed_state

class StateManifoldVAE(nn.Module):
    """
    状态流形VAE：用于学习"好状态"的低维流形表示
    """
    def __init__(self, state_dim, latent_dim=5, hidden_dims=[128, 64]):
        super(StateManifoldVAE, self).__init__()
        
        self.state_dim = state_dim
        self.latent_dim = latent_dim
        
        # 编码器和解码器
        self.encoder = VAEEncoder(state_dim, latent_dim, hidden_dims)
        self.decoder = VAEDecoder(latent_dim, state_dim, hidden_dims[::-1])
        
        main_logger.info(f"创建StateManifoldVAE: state_dim={state_dim}, latent_dim={latent_dim}")
    
    def encode(self, state):
        """编码状态为潜变量分布参数"""
        return self.encoder(state)
    
    def decode(self, z):
        """从潜变量解码状态"""
        return self.decoder(z)
    
    def reparameterize(self, mu, logvar):
        """
        重参数化技巧：从分布中采样
        
        参数:
            mu: 均值 [batch_size, latent_dim]
            logvar: 对数方差 [batch_size, latent_dim]
            
        返回:
            z: 采样的潜变量 [batch_size, latent_dim]
        """
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        z = mu + eps * std
        return z
    
    def forward(self, state):
        """
        前向传播
        
        参数:
            state: 状态 [batch_size, state_dim]
            
        返回:
            reconstructed_state: 重构状态 [batch_size, state_dim]
            mu: 潜变量均值 [batch_size, latent_dim]
            logvar: 潜变量对数方差 [batch_size, latent_dim]
            z: 采样的潜变量 [batch_size, latent_dim]
        """
        # 编码
        mu, logvar = self.encode(state)
        
        # 重参数化采样
        z = self.reparameterize(mu, logvar)
        
        # 解码
        reconstructed_state = self.decode(z)
        
        return reconstructed_state, mu, logvar, z
    
    def sample_from_latent(self, batch_size, device):
        """
        从先验分布（标准正态分布）中采样潜变量并解码为状态
        
        参数:
            batch_size: 批大小
            device: 设备
            
        返回:
            sampled_states: 采样的状态 [batch_size, state_dim]
            z: 采样的潜变量 [batch_size, latent_dim]
        """
        # 从标准正态分布采样
        z = torch.randn(batch_size, self.latent_dim, device=device)
        
        # 解码为状态
        sampled_states = self.decode(z)
        
        return sampled_states, z
    
    def get_reconstruction_error(self, state):
        """
        计算重构误差，用于衡量状态到流形的距离
        
        参数:
            state: 状态 [batch_size, state_dim]
            
        返回:
            reconstruction_error: 重构误差 [batch_size]
        """
        with torch.no_grad():
            reconstructed_state, _, _, _ = self.forward(state)
            error = torch.mean((state - reconstructed_state) ** 2, dim=1)
        return error

def vae_loss_function(reconstructed_state, state, mu, logvar, beta=1.0):
    """
    VAE损失函数：重构损失 + KL散度损失
    
    参数:
        reconstructed_state: 重构状态 [batch_size, state_dim]
        state: 原始状态 [batch_size, state_dim]
        mu: 潜变量均值 [batch_size, latent_dim]
        logvar: 潜变量对数方差 [batch_size, latent_dim]
        beta: KL损失权重（β-VAE）
        
    返回:
        loss: 总损失
        reconstruction_loss: 重构损失
        kl_loss: KL散度损失
    """
    # 重构损失（均方误差）
    reconstruction_loss = F.mse_loss(reconstructed_state, state, reduction='mean')
    
    # KL散度损失
    # KL(N(μ,σ²) || N(0,1)) = 0.5 * Σ(1 + log(σ²) - μ² - σ²)
    kl_loss = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())
    
    # 总损失
    loss = reconstruction_loss + beta * kl_loss
    
    return loss, reconstruction_loss, kl_loss

class ManifoldQualityMetrics:
    """
    流形质量评估指标
    """
    @staticmethod
    def compute_reconstruction_quality(vae, states):
        """
        计算重构质量指标
        
        参数:
            vae: 训练好的VAE模型
            states: 测试状态 [n_samples, state_dim]
            
        返回:
            metrics: 质量指标字典
        """
        vae.eval()
        with torch.no_grad():
            reconstructed_states, mu, logvar, z = vae(states)
            
            # 重构误差
            reconstruction_errors = torch.mean((states - reconstructed_states) ** 2, dim=1)
            
            # 潜空间分布质量
            # 检查潜变量是否接近标准正态分布
            z_mean = torch.mean(z, dim=0)
            z_std = torch.std(z, dim=0)
            
            metrics = {
                'mean_reconstruction_error': reconstruction_errors.mean().item(),
                'std_reconstruction_error': reconstruction_errors.std().item(),
                'max_reconstruction_error': reconstruction_errors.max().item(),
                'latent_mean_deviation': torch.mean(torch.abs(z_mean)).item(),
                'latent_std_deviation': torch.mean(torch.abs(z_std - 1.0)).item(),
                'latent_space_coverage': ManifoldQualityMetrics._compute_coverage(z),
            }
        
        vae.train()
        return metrics
    
    @staticmethod
    def _compute_coverage(z, n_bins=10):
        """
        计算潜空间覆盖率（简化版本）
        
        参数:
            z: 潜变量 [n_samples, latent_dim]
            n_bins: 每个维度的分箱数
            
        返回:
            coverage: 覆盖率 [0, 1]
        """
        # 将每个维度分箱，计算非空箱子的比例
        latent_dim = z.shape[1]
        total_coverage = 0
        
        for dim in range(latent_dim):
            z_dim = z[:, dim]
            z_min, z_max = z_dim.min().item(), z_dim.max().item()
            
            if z_max > z_min:
                bins = torch.linspace(z_min, z_max, n_bins + 1)
                hist = torch.histc(z_dim, bins=n_bins, min=z_min, max=z_max)
                non_empty_bins = (hist > 0).sum().item()
                coverage = non_empty_bins / n_bins
            else:
                coverage = 1.0  # 所有值相同，认为完全覆盖
            
            total_coverage += coverage
        
        return total_coverage / latent_dim
