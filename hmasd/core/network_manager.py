"""
网络管理器 - 统一管理所有神经网络和优化器
"""

import torch
import torch.nn as nn
from torch.optim import Adam
from torch.optim.lr_scheduler import LinearLR, CosineAnnealingLR, ExponentialLR

from logger import main_logger
from hmasd.networks import SkillCoordinator, SkillDiscoverer, TeamDiscriminator, IndividualDiscriminator


class NetworkManager:
    """统一的网络管理器，负责所有神经网络的创建、初始化和管理"""
    
    def __init__(self, config, device):
        self.config = config
        self.device = device
        
        # 创建网络
        self._create_networks()
        
        # 创建优化器
        self._create_optimizers()
        
        # 创建学习率调度器
        self._create_schedulers()
        
        main_logger.info("网络管理器初始化完成")
    
    def _create_networks(self):
        """创建所有神经网络"""
        self.skill_coordinator = SkillCoordinator(self.config).to(self.device)
        self.skill_discoverer = SkillDiscoverer(self.config, logger=main_logger).to(self.device)
        self.team_discriminator = TeamDiscriminator(self.config).to(self.device)
        self.individual_discriminator = IndividualDiscriminator(self.config).to(self.device)
        
        main_logger.info("所有神经网络已创建并移至设备")
    
    def _create_optimizers(self):
        """创建所有优化器"""
        self.coordinator_optimizer = Adam(
            self.skill_coordinator.parameters(),
            lr=self.config.lr_coordinator,
            weight_decay=self.config.weight_decay
        )
        
        # 为SkillDiscoverer创建解耦的Actor和Critic优化器
        self.discoverer_actor_optimizer = Adam(
            self.skill_discoverer.actor.parameters(),
            lr=self.config.lr_discoverer_actor,
            weight_decay=self.config.weight_decay
        )
        
        self.discoverer_critic_optimizer = Adam(
            self.skill_discoverer.critic.parameters(),
            lr=self.config.lr_discoverer_critic,
            weight_decay=self.config.weight_decay
        )
        
        self.discriminator_optimizer = Adam(
            list(self.team_discriminator.parameters()) + 
            list(self.individual_discriminator.parameters()),
            lr=self.config.lr_discriminator,
            weight_decay=self.config.weight_decay
        )
        
        main_logger.info("所有优化器已创建")
    
    def _create_schedulers(self):
        """创建学习率调度器"""
        if not getattr(self.config, 'use_lr_decay', False):
            self.coordinator_scheduler = None
            self.discoverer_actor_scheduler = None
            self.discoverer_critic_scheduler = None
            self.discriminator_scheduler = None
            main_logger.info("未启用学习率衰减")
            return
        
        scheduler_type = self.config.lr_decay_schedule
        total_iters = self.config.lr_decay_steps
        
        if scheduler_type == 'linear':
            self.coordinator_scheduler = LinearLR(
                self.coordinator_optimizer,
                start_factor=1.0,
                end_factor=self.config.coordinator_lr_decay_factor,
                total_iters=total_iters
            )
            self.discoverer_actor_scheduler = LinearLR(
                self.discoverer_actor_optimizer,
                start_factor=1.0,
                end_factor=self.config.discoverer_lr_decay_factor,
                total_iters=total_iters
            )
            self.discoverer_critic_scheduler = LinearLR(
                self.discoverer_critic_optimizer,
                start_factor=1.0,
                end_factor=self.config.discoverer_lr_decay_factor,
                total_iters=total_iters
            )
            self.discriminator_scheduler = LinearLR(
                self.discriminator_optimizer,
                start_factor=1.0,
                end_factor=self.config.discriminator_lr_decay_factor,
                total_iters=total_iters
            )
        elif scheduler_type == 'cosine':
            self.coordinator_scheduler = CosineAnnealingLR(
                self.coordinator_optimizer, T_max=total_iters
            )
            self.discoverer_actor_scheduler = CosineAnnealingLR(
                self.discoverer_actor_optimizer, T_max=total_iters
            )
            self.discoverer_critic_scheduler = CosineAnnealingLR(
                self.discoverer_critic_optimizer, T_max=total_iters
            )
            self.discriminator_scheduler = CosineAnnealingLR(
                self.discriminator_optimizer, T_max=total_iters
            )
        
        main_logger.info(f"已启用学习率衰减: {scheduler_type}, 衰减步数: {total_iters}")
    
    def train(self, mode=True):
        """设置所有网络为训练或评估模式"""
        self.skill_coordinator.train(mode)
        self.skill_discoverer.train(mode)
        self.team_discriminator.train(mode)
        self.individual_discriminator.train(mode)
    
    def eval(self):
        """设置所有网络为评估模式"""
        self.train(False)
    
    def step_schedulers(self, global_step):
        """更新学习率调度器"""
        if not getattr(self.config, 'use_lr_decay', False) or global_step > self.config.lr_decay_steps:
            return
        
        if self.coordinator_scheduler is not None:
            self.coordinator_scheduler.step()
        if self.discoverer_actor_scheduler is not None:
            self.discoverer_actor_scheduler.step()
        if self.discoverer_critic_scheduler is not None:
            self.discoverer_critic_scheduler.step()
        if self.discriminator_scheduler is not None:
            self.discriminator_scheduler.step()
    
    def get_learning_rates(self):
        """获取当前学习率"""
        return {
            'coordinator_lr': self.coordinator_optimizer.param_groups[0]['lr'],
            'discoverer_actor_lr': self.discoverer_actor_optimizer.param_groups[0]['lr'],
            'discoverer_critic_lr': self.discoverer_critic_optimizer.param_groups[0]['lr'],
            'discriminator_lr': self.discriminator_optimizer.param_groups[0]['lr']
        }
    
    def save_state_dict(self):
        """保存所有网络和优化器的状态字典"""
        return {
            'skill_coordinator': self.skill_coordinator.state_dict(),
            'skill_discoverer': self.skill_discoverer.state_dict(),
            'team_discriminator': self.team_discriminator.state_dict(),
            'individual_discriminator': self.individual_discriminator.state_dict(),
            'coordinator_optimizer': self.coordinator_optimizer.state_dict(),
            'discoverer_actor_optimizer': self.discoverer_actor_optimizer.state_dict(),
            'discoverer_critic_optimizer': self.discoverer_critic_optimizer.state_dict(),
            'discriminator_optimizer': self.discriminator_optimizer.state_dict()
        }
    
    def load_state_dict(self, checkpoint, strict=False):
        """加载网络和优化器状态"""
        # 加载网络状态
        self.skill_coordinator.load_state_dict(checkpoint['skill_coordinator'], strict=strict)
        self.skill_discoverer.load_state_dict(checkpoint['skill_discoverer'], strict=strict)
        self.team_discriminator.load_state_dict(checkpoint['team_discriminator'], strict=strict)
        self.individual_discriminator.load_state_dict(checkpoint['individual_discriminator'], strict=strict)
        
        # 加载优化器状态
        if 'coordinator_optimizer' in checkpoint:
            self.coordinator_optimizer.load_state_dict(checkpoint['coordinator_optimizer'])
        if 'discoverer_actor_optimizer' in checkpoint:
            self.discoverer_actor_optimizer.load_state_dict(checkpoint['discoverer_actor_optimizer'])
        if 'discoverer_critic_optimizer' in checkpoint:
            self.discoverer_critic_optimizer.load_state_dict(checkpoint['discoverer_critic_optimizer'])
        elif 'discoverer_optimizer' in checkpoint:  # 兼容旧模型
            self.discoverer_actor_optimizer.load_state_dict(checkpoint['discoverer_optimizer'])
            self.discoverer_critic_optimizer.load_state_dict(checkpoint['discoverer_optimizer'])
        if 'discriminator_optimizer' in checkpoint:
            self.discriminator_optimizer.load_state_dict(checkpoint['discriminator_optimizer'])
        
        main_logger.info("网络和优化器状态已加载")
