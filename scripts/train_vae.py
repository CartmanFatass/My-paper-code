"""
训练VAE模型学习"好状态"的流形
该脚本加载收集的高奖励状态数据，训练VAE模型学习其低维流形表示
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import os
import sys
import argparse
from datetime import datetime
import matplotlib.pyplot as plt
import json

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from manifold_hmasd.vae import StateManifoldVAE, vae_loss_function, ManifoldQualityMetrics
from logger import main_logger

class StateDataset(Dataset):
    """
    状态数据集
    """
    def __init__(self, states, rewards=None, normalize=True):
        """
        初始化数据集
        
        参数:
            states: 状态数组 [n_samples, state_dim]
            rewards: 对应的奖励数组 [n_samples] (可选)
            normalize: 是否标准化
        """
        self.states = torch.tensor(states, dtype=torch.float32)
        self.rewards = torch.tensor(rewards, dtype=torch.float32) if rewards is not None else None
        
        # 标准化
        if normalize:
            self.state_mean = torch.mean(self.states, dim=0)
            self.state_std = torch.std(self.states, dim=0) + 1e-8  # 避免除零
            self.states = (self.states - self.state_mean) / self.state_std
        else:
            self.state_mean = torch.zeros(self.states.shape[1])
            self.state_std = torch.ones(self.states.shape[1])
        
        main_logger.info(f"数据集初始化: {len(self.states)} 个样本, 状态维度: {self.states.shape[1]}")
        main_logger.info(f"标准化参数: mean范围=[{self.state_mean.min():.3f}, {self.state_mean.max():.3f}], "
                        f"std范围=[{self.state_std.min():.3f}, {self.state_std.max():.3f}]")
    
    def __len__(self):
        return len(self.states)
    
    def __getitem__(self, idx):
        if self.rewards is not None:
            return self.states[idx], self.rewards[idx]
        else:
            return self.states[idx]
    
    def denormalize_state(self, normalized_state):
        """反标准化状态"""
        return normalized_state * self.state_std + self.state_mean

class VAETrainer:
    """
    VAE训练器
    """
    def __init__(self, model, train_loader, val_loader=None, device='cpu'):
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.device = device
        
        # 训练记录
        self.train_losses = []
        self.train_recon_losses = []
        self.train_kl_losses = []
        self.val_losses = []
        
        # 最佳模型记录
        self.best_val_loss = float('inf')
        self.best_model_state = None
        
    def train_epoch(self, optimizer, beta=1.0):
        """
        训练一个epoch
        
        参数:
            optimizer: 优化器
            beta: KL损失权重
            
        返回:
            epoch_loss: 平均损失
            epoch_recon_loss: 平均重构损失
            epoch_kl_loss: 平均KL损失
        """
        self.model.train()
        total_loss = 0
        total_recon_loss = 0
        total_kl_loss = 0
        
        for batch_idx, batch_data in enumerate(self.train_loader):
            if isinstance(batch_data, tuple):
                states, rewards = batch_data
                states = states.to(self.device)
            else:
                states = batch_data.to(self.device)
            
            optimizer.zero_grad()
            
            # 前向传播
            reconstructed_states, mu, logvar, z = self.model(states)
            
            # 计算损失
            loss, recon_loss, kl_loss = vae_loss_function(
                reconstructed_states, states, mu, logvar, beta
            )
            
            # 反向传播
            loss.backward()
            
            # 梯度裁剪
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            
            optimizer.step()
            
            # 记录损失
            total_loss += loss.item()
            total_recon_loss += recon_loss.item()
            total_kl_loss += kl_loss.item()
        
        n_batches = len(self.train_loader)
        return total_loss / n_batches, total_recon_loss / n_batches, total_kl_loss / n_batches
    
    def validate_epoch(self, beta=1.0):
        """
        验证一个epoch
        
        参数:
            beta: KL损失权重
            
        返回:
            val_loss: 验证损失
        """
        if self.val_loader is None:
            return 0.0
        
        self.model.eval()
        total_loss = 0
        
        with torch.no_grad():
            for batch_data in self.val_loader:
                if isinstance(batch_data, tuple):
                    states, rewards = batch_data
                    states = states.to(self.device)
                else:
                    states = batch_data.to(self.device)
                
                # 前向传播
                reconstructed_states, mu, logvar, z = self.model(states)
                
                # 计算损失
                loss, _, _ = vae_loss_function(
                    reconstructed_states, states, mu, logvar, beta
                )
                
                total_loss += loss.item()
        
        return total_loss / len(self.val_loader)
    
    def train(self, n_epochs, lr=1e-3, beta_schedule=None, save_dir=None):
        """
        训练VAE
        
        参数:
            n_epochs: 训练轮数
            lr: 学习率
            beta_schedule: beta退火计划 (start_beta, end_beta, anneal_epochs)
            save_dir: 保存目录
        """
        optimizer = optim.Adam(self.model.parameters(), lr=lr, weight_decay=1e-5)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.8, patience=10, verbose=True
        )
        
        main_logger.info(f"开始训练VAE: {n_epochs} epochs, lr={lr}")
        
        for epoch in range(n_epochs):
            # 计算当前beta值
            if beta_schedule is not None:
                start_beta, end_beta, anneal_epochs = beta_schedule
                if epoch < anneal_epochs:
                    beta = start_beta + (end_beta - start_beta) * epoch / anneal_epochs
                else:
                    beta = end_beta
            else:
                beta = 1.0
            
            # 训练和验证
            train_loss, train_recon_loss, train_kl_loss = self.train_epoch(optimizer, beta)
            val_loss = self.validate_epoch(beta)
            
            # 记录损失
            self.train_losses.append(train_loss)
            self.train_recon_losses.append(train_recon_loss)
            self.train_kl_losses.append(train_kl_loss)
            self.val_losses.append(val_loss)
            
            # 学习率调度
            scheduler.step(val_loss if val_loss > 0 else train_loss)
            
            # 保存最佳模型
            current_loss = val_loss if val_loss > 0 else train_loss
            if current_loss < self.best_val_loss:
                self.best_val_loss = current_loss
                self.best_model_state = self.model.state_dict().copy()
            
            # 记录进度
            if (epoch + 1) % 10 == 0:
                main_logger.info(f"Epoch {epoch + 1}/{n_epochs}: "
                               f"train_loss={train_loss:.4f}, "
                               f"recon_loss={train_recon_loss:.4f}, "
                               f"kl_loss={train_kl_loss:.4f}, "
                               f"val_loss={val_loss:.4f}, "
                               f"beta={beta:.3f}")
        
        # 恢复最佳模型
        if self.best_model_state is not None:
            self.model.load_state_dict(self.best_model_state)
            main_logger.info(f"已恢复最佳模型 (验证损失: {self.best_val_loss:.4f})")
    
    def plot_training_curves(self, save_path=None):
        """
        绘制训练曲线
        
        参数:
            save_path: 保存路径
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        epochs = range(1, len(self.train_losses) + 1)
        
        # 总损失
        ax1.plot(epochs, self.train_losses, label='训练损失', color='blue')
        if len(self.val_losses) > 0 and max(self.val_losses) > 0:
            ax1.plot(epochs, self.val_losses, label='验证损失', color='red')
        ax1.set_title('训练/验证损失')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('损失')
        ax1.legend()
        ax1.grid(True)
        
        # 重构损失
        ax2.plot(epochs, self.train_recon_losses, label='重构损失', color='green')
        ax2.set_title('重构损失')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('重构损失')
        ax2.grid(True)
        
        # KL损失
        ax3.plot(epochs, self.train_kl_losses, label='KL损失', color='orange')
        ax3.set_title('KL散度损失')
        ax3.set_xlabel('Epoch')
        ax3.set_ylabel('KL损失')
        ax3.grid(True)
        
        # 损失比例
        total_losses = np.array(self.train_losses)
        recon_ratios = np.array(self.train_recon_losses) / total_losses
        kl_ratios = np.array(self.train_kl_losses) / total_losses
        
        ax4.plot(epochs, recon_ratios, label='重构损失比例', color='green')
        ax4.plot(epochs, kl_ratios, label='KL损失比例', color='orange')
        ax4.set_title('损失组成比例')
        ax4.set_xlabel('Epoch')
        ax4.set_ylabel('比例')
        ax4.legend()
        ax4.grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            main_logger.info(f"训练曲线已保存到 {save_path}")
        
        plt.close()

def visualize_latent_space(model, dataset, device, save_path=None, n_samples=1000):
    """
    可视化潜空间
    
    参数:
        model: 训练好的VAE模型
        dataset: 数据集
        device: 设备
        save_path: 保存路径
        n_samples: 采样数量
    """
    model.eval()
    
    # 采样一部分数据
    indices = np.random.choice(len(dataset), min(n_samples, len(dataset)), replace=False)
    states = torch.stack([dataset[i] for i in indices])
    if isinstance(states, tuple):
        states = states[0]  # 如果包含奖励，只取状态
    
    states = states.to(device)
    
    with torch.no_grad():
        mu, logvar = model.encode(states)
        z = model.reparameterize(mu, logvar)
    
    z_np = z.cpu().numpy()
    
    # 如果潜空间维度>=2，可视化前两个维度
    if z_np.shape[1] >= 2:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 散点图
        ax1.scatter(z_np[:, 0], z_np[:, 1], alpha=0.6, s=20)
        ax1.set_title('潜空间分布 (前两个维度)')
        ax1.set_xlabel('Z1')
        ax1.set_ylabel('Z2')
        ax1.grid(True)
        
        # 各维度的边际分布
        ax2.hist(z_np[:, 0], bins=50, alpha=0.7, density=True, label='Z1')
        ax2.axvline(0, color='red', linestyle='--', label='标准正态分布均值')
        ax2.set_title('Z1维度分布')
        ax2.set_xlabel('Z1')
        ax2.set_ylabel('密度')
        ax2.legend()
        ax2.grid(True)
        
        ax3.hist(z_np[:, 1], bins=50, alpha=0.7, density=True, label='Z2', color='orange')
        ax3.axvline(0, color='red', linestyle='--', label='标准正态分布均值')
        ax3.set_title('Z2维度分布')
        ax3.set_xlabel('Z2')
        ax3.set_ylabel('密度')
        ax3.legend()
        ax3.grid(True)
        
        # 所有维度的统计信息
        z_means = np.mean(z_np, axis=0)
        z_stds = np.std(z_np, axis=0)
        dimensions = range(z_np.shape[1])
        
        ax4.bar(dimensions, z_means, alpha=0.7, label='均值')
        ax4.axhline(0, color='red', linestyle='--', alpha=0.7)
        ax4.set_title('各维度均值')
        ax4.set_xlabel('潜空间维度')
        ax4.set_ylabel('均值')
        ax4.grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            main_logger.info(f"潜空间可视化已保存到 {save_path}")
        
        plt.close()

def visualize_reconstruction(model, dataset, device, save_path=None, n_samples=5):
    """
    可视化重构效果
    
    参数:
        model: 训练好的VAE模型
        dataset: 数据集
        device: 设备
        save_path: 保存路径
        n_samples: 可视化的样本数量
    """
    model.eval()
    
    # 随机选择样本
    indices = np.random.choice(len(dataset), n_samples, replace=False)
    
    original_states = []
    reconstructed_states = []
    reconstruction_errors = []
    
    with torch.no_grad():
        for idx in indices:
            state = dataset[idx]
            if isinstance(state, tuple):
                state = state[0]  # 如果包含奖励，只取状态
            
            state = state.unsqueeze(0).to(device)
            recon_state, _, _, _ = model(state)
            
            original_states.append(state.cpu().numpy().flatten())
            reconstructed_states.append(recon_state.cpu().numpy().flatten())
            
            error = torch.mean((state - recon_state) ** 2).item()
            reconstruction_errors.append(error)
    
    # 绘制重构对比
    fig, axes = plt.subplots(n_samples, 1, figsize=(15, 3 * n_samples))
    if n_samples == 1:
        axes = [axes]
    
    for i in range(n_samples):
        state_dim = len(original_states[i])
        dims = range(state_dim)
        
        axes[i].plot(dims, original_states[i], 'b-', label='原始状态', linewidth=2)
        axes[i].plot(dims, reconstructed_states[i], 'r--', label='重构状态', linewidth=2)
        axes[i].set_title(f'样本 {i+1} - 重构误差: {reconstruction_errors[i]:.4f}')
        axes[i].set_xlabel('状态维度')
        axes[i].set_ylabel('值')
        axes[i].legend()
        axes[i].grid(True)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        main_logger.info(f"重构可视化已保存到 {save_path}")
    
    plt.close()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='训练VAE学习状态流形')
    parser.add_argument('--data_dir', type=str, required=True, help='数据目录')
    parser.add_argument('--latent_dim', type=int, default=5, help='潜空间维度')
    parser.add_argument('--hidden_dims', type=int, nargs='+', default=[128, 64], help='隐藏层维度')
    parser.add_argument('--n_epochs', type=int, default=200, help='训练轮数')
    parser.add_argument('--batch_size', type=int, default=64, help='批大小')
    parser.add_argument('--lr', type=float, default=1e-3, help='学习率')
    parser.add_argument('--beta_start', type=float, default=0.0, help='beta起始值')
    parser.add_argument('--beta_end', type=float, default=1.0, help='beta结束值')
    parser.add_argument('--beta_anneal_epochs', type=int, default=50, help='beta退火轮数')
    parser.add_argument('--val_split', type=float, default=0.2, help='验证集比例')
    parser.add_argument('--save_dir', type=str, default='models/vae', help='保存目录')
    parser.add_argument('--device', type=str, default='auto', help='设备 (auto/cpu/cuda)')
    parser.add_argument('--seed', type=int, default=42, help='随机种子')
    
    args = parser.parse_args()
    
    # 设置随机种子
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    
    # 设置设备
    if args.device == 'auto':
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    else:
        device = torch.device(args.device)
    main_logger.info(f"使用设备: {device}")
    
    # 创建保存目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = f"{args.save_dir}_{timestamp}"
    os.makedirs(save_dir, exist_ok=True)
    
    # 加载数据
    good_states_path = os.path.join(args.data_dir, 'good_states.npy')
    rewards_path = os.path.join(args.data_dir, 'good_states_rewards.npy')
    
    if not os.path.exists(good_states_path):
        raise FileNotFoundError(f"未找到数据文件: {good_states_path}")
    
    states = np.load(good_states_path)
    rewards = np.load(rewards_path) if os.path.exists(rewards_path) else None
    
    main_logger.info(f"加载数据: {states.shape[0]} 个状态, 维度: {states.shape[1]}")
    
    # 创建数据集
    dataset = StateDataset(states, rewards, normalize=True)
    
    # 划分训练集和验证集
    n_samples = len(dataset)
    n_val = int(n_samples * args.val_split)
    n_train = n_samples - n_val
    
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [n_train, n_val], generator=torch.Generator().manual_seed(args.seed)
    )
    
    # 创建数据加载器
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False) if n_val > 0 else None
    
    main_logger.info(f"数据划分: 训练集 {n_train} 个样本, 验证集 {n_val} 个样本")
    
    # 创建模型
    state_dim = states.shape[1]
    model = StateManifoldVAE(
        state_dim=state_dim,
        latent_dim=args.latent_dim,
        hidden_dims=args.hidden_dims
    )
    
    # 创建训练器
    trainer = VAETrainer(model, train_loader, val_loader, device)
    
    # 训练模型
    beta_schedule = (args.beta_start, args.beta_end, args.beta_anneal_epochs)
    trainer.train(
        n_epochs=args.n_epochs,
        lr=args.lr,
        beta_schedule=beta_schedule,
        save_dir=save_dir
    )
    
    # 评估模型质量
    main_logger.info("评估模型质量...")
    test_states = torch.stack([dataset[i] for i in range(min(1000, len(dataset)))])
    if isinstance(test_states, tuple):
        test_states = test_states[0]
    
    metrics = ManifoldQualityMetrics.compute_reconstruction_quality(model, test_states.to(device))
    main_logger.info(f"模型质量指标: {metrics}")
    
    # 保存模型和相关信息
    model_path = os.path.join(save_dir, 'vae_model.pth')
    torch.save({
        'model_state_dict': model.state_dict(),
        'model_config': {
            'state_dim': state_dim,
            'latent_dim': args.latent_dim,
            'hidden_dims': args.hidden_dims
        },
        'normalization': {
            'state_mean': dataset.state_mean,
            'state_std': dataset.state_std
        },
        'training_args': vars(args),
        'quality_metrics': metrics
    }, model_path)
    
    # 保存训练记录
    training_log = {
        'train_losses': trainer.train_losses,
        'train_recon_losses': trainer.train_recon_losses,
        'train_kl_losses': trainer.train_kl_losses,
        'val_losses': trainer.val_losses,
        'best_val_loss': trainer.best_val_loss,
        'quality_metrics': metrics
    }
    
    log_path = os.path.join(save_dir, 'training_log.json')
    with open(log_path, 'w') as f:
        json.dump(training_log, f, indent=2)
    
    # 生成可视化
    main_logger.info("生成可视化...")
    
    # 训练曲线
    trainer.plot_training_curves(os.path.join(save_dir, 'training_curves.png'))
    
    # 潜空间可视化
    visualize_latent_space(model, dataset, device, os.path.join(save_dir, 'latent_space.png'))
    
    # 重构可视化
    visualize_reconstruction(model, dataset, device, os.path.join(save_dir, 'reconstruction.png'))
    
    # 输出最终结果
    main_logger.info("=" * 60)
    main_logger.info("VAE训练完成!")
    main_logger.info(f"保存目录: {save_dir}")
    main_logger.info(f"模型文件: {model_path}")
    main_logger.info(f"最佳验证损失: {trainer.best_val_loss:.4f}")
    main_logger.info(f"重构误差: {metrics['mean_reconstruction_error']:.4f} ± {metrics['std_reconstruction_error']:.4f}")
    main_logger.info(f"潜空间覆盖率: {metrics['latent_space_coverage']:.3f}")
    main_logger.info("=" * 60)

if __name__ == "__main__":
    main()
