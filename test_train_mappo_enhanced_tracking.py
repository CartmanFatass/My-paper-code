#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_train_mappo_enhanced_tracking.py

针对 train_mappo_enhanced_tracking.py 的全面测试文件
包含单元测试、集成测试、模拟测试和端到端测试

作者: AI Assistant
日期: 2025年6月19日
"""

import unittest
import pytest
import numpy as np
import torch
import torch.nn as nn
import tempfile
import shutil
import os
import sys
import time
import logging
import multiprocessing as mp
from unittest.mock import Mock, patch, MagicMock
from collections import deque
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 使用非GUI后端
import matplotlib.pyplot as plt

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入被测试的模块
try:
    from train_mappo_enhanced_tracking import (
        check_tensor_health, safe_divide, safe_log, safe_exp,
        monitor_gradients, log_memory_usage, safe_tensor_ops_wrapper,
        EnhancedRewardTracker, MAPPOActor, MAPPOCritic, MAPPOAgent,
        get_device, make_env, parse_args, train, evaluate,
        main_logger
    )
    from config_1 import Config
    from hmasd.utils import ReplayBuffer, compute_gae, compute_ppo_loss
    from logger import init_multiproc_logging, get_logger, shutdown_logging
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有必要的模块都可用")
    sys.exit(1)


class TestNumericalStabilityFunctions(unittest.TestCase):
    """测试数值稳定性函数"""
    
    def setUp(self):
        """测试前设置"""
        self.logger = get_logger("test_numerical")
        
    def test_check_tensor_health_valid_tensor(self):
        """测试健康张量的检查"""
        tensor = torch.randn(5, 3)
        result = check_tensor_health(tensor, "test_tensor", self.logger)
        self.assertTrue(result)
        
    def test_check_tensor_health_nan_tensor(self):
        """测试包含NaN的张量"""
        tensor = torch.tensor([1.0, float('nan'), 3.0])
        result = check_tensor_health(tensor, "nan_tensor", self.logger)
        self.assertFalse(result)
        
    def test_check_tensor_health_inf_tensor(self):
        """测试包含Inf的张量"""
        tensor = torch.tensor([1.0, float('inf'), 3.0])
        result = check_tensor_health(tensor, "inf_tensor", self.logger)
        self.assertFalse(result)
        
    def test_check_tensor_health_boolean_tensor(self):
        """测试布尔张量"""
        tensor = torch.tensor([True, False, True])
        result = check_tensor_health(tensor, "bool_tensor", self.logger)
        self.assertTrue(result)
        
    def test_check_tensor_health_none_input(self):
        """测试None输入"""
        result = check_tensor_health(None, "none_tensor", self.logger)
        self.assertFalse(result)
        
    def test_check_tensor_health_empty_tensor(self):
        """测试空张量"""
        tensor = torch.tensor([])
        result = check_tensor_health(tensor, "empty_tensor", self.logger)
        self.assertFalse(result)
        
    def test_safe_divide_normal_case(self):
        """测试正常除法"""
        numerator = torch.tensor([4.0, 6.0, 8.0])
        denominator = torch.tensor([2.0, 3.0, 4.0])
        result = safe_divide(numerator, denominator, logger=self.logger)
        expected = torch.tensor([2.0, 2.0, 2.0])
        torch.testing.assert_close(result, expected)
        
    def test_safe_divide_zero_denominator(self):
        """测试除零情况"""
        numerator = torch.tensor([4.0, 6.0, 8.0])
        denominator = torch.tensor([2.0, 0.0, 4.0])
        result = safe_divide(numerator, denominator, epsilon=1e-8, logger=self.logger)
        # 应该能够处理零分母而不报错
        self.assertTrue(torch.isfinite(result).all())
        
    def test_safe_divide_scalar_inputs(self):
        """测试标量输入"""
        result = safe_divide(10.0, 2.0, logger=self.logger)
        self.assertEqual(result, 5.0)
        
        # 测试标量零分母
        result = safe_divide(10.0, 0.0, logger=self.logger)
        self.assertTrue(torch.isfinite(result))
        
    def test_safe_log_normal_case(self):
        """测试正常对数运算"""
        tensor = torch.tensor([1.0, 2.0, np.e])
        result = safe_log(tensor, logger=self.logger)
        expected = torch.log(tensor)
        torch.testing.assert_close(result, expected)
        
    def test_safe_log_zero_input(self):
        """测试零输入对数"""
        tensor = torch.tensor([0.0, 1.0, 2.0])
        result = safe_log(tensor, epsilon=1e-8, logger=self.logger)
        # 应该能够处理零输入而不产生-inf
        self.assertTrue(torch.isfinite(result).all())
        
    def test_safe_log_negative_input(self):
        """测试负数输入对数"""
        tensor = torch.tensor([-1.0, 0.0, 1.0])
        result = safe_log(tensor, epsilon=1e-8, logger=self.logger)
        self.assertTrue(torch.isfinite(result).all())
        
    def test_safe_exp_normal_case(self):
        """测试正常指数运算"""
        tensor = torch.tensor([0.0, 1.0, 2.0])
        result = safe_exp(tensor, logger=self.logger)
        expected = torch.exp(tensor)
        torch.testing.assert_close(result, expected)
        
    def test_safe_exp_large_input(self):
        """测试大数输入指数"""
        tensor = torch.tensor([0.0, 50.0, 100.0])  # 100会被截断到50
        result = safe_exp(tensor, max_value=50.0, logger=self.logger)
        # 应该限制最大值避免溢出
        self.assertTrue(torch.isfinite(result).all())
        
    def test_safe_tensor_ops_wrapper(self):
        """测试安全张量操作装饰器"""
        @safe_tensor_ops_wrapper
        def test_function(a, b):
            return a + b
            
        # 正常情况
        a = torch.tensor([1.0, 2.0])
        b = torch.tensor([3.0, 4.0])
        result = test_function(a, b)
        expected = torch.tensor([4.0, 6.0])
        torch.testing.assert_close(result, expected)


class TestNetworkComponents(unittest.TestCase):
    """测试网络组件"""
    
    def setUp(self):
        """测试前设置"""
        self.obs_dim = 10
        self.action_dim = 3
        self.state_dim = 20
        self.hidden_size = 64
        self.device = 'cpu'
        
    def test_mappo_actor_initialization(self):
        """测试MAPPO Actor初始化"""
        actor = MAPPOActor(self.obs_dim, self.action_dim, self.hidden_size)
        self.assertEqual(actor.obs_dim, self.obs_dim)
        self.assertEqual(actor.action_dim, self.action_dim)
        
    def test_mappo_actor_forward(self):
        """测试MAPPO Actor前向传播"""
        actor = MAPPOActor(self.obs_dim, self.action_dim, self.hidden_size)
        obs = torch.randn(5, self.obs_dim)
        
        mean, std = actor(obs)
        
        self.assertEqual(mean.shape, (5, self.action_dim))
        self.assertEqual(std.shape, (self.action_dim,))
        self.assertTrue(torch.all(std > 0))  # 标准差应该为正
        
    def test_mappo_actor_get_action_and_log_prob(self):
        """测试动作采样和对数概率计算"""
        actor = MAPPOActor(self.obs_dim, self.action_dim, self.hidden_size)
        obs = torch.randn(5, self.obs_dim)
        
        actions, log_probs = actor.get_action_and_log_prob(obs)
        
        self.assertEqual(actions.shape, (5, self.action_dim))
        self.assertEqual(log_probs.shape, (5,))
        self.assertTrue(torch.isfinite(actions).all())
        self.assertTrue(torch.isfinite(log_probs).all())
        
    def test_mappo_actor_evaluate_actions(self):
        """测试动作评估"""
        actor = MAPPOActor(self.obs_dim, self.action_dim, self.hidden_size)
        obs = torch.randn(5, self.obs_dim)
        actions = torch.randn(5, self.action_dim)
        
        log_probs, entropy = actor.evaluate_actions(obs, actions)
        
        self.assertEqual(log_probs.shape, (5,))
        self.assertEqual(entropy.shape, (5,))
        self.assertTrue(torch.isfinite(log_probs).all())
        self.assertTrue(torch.isfinite(entropy).all())
        self.assertTrue(torch.all(entropy >= 0))  # 熵应该非负
        
    def test_mappo_critic_initialization(self):
        """测试MAPPO Critic初始化"""
        critic = MAPPOCritic(self.state_dim, self.hidden_size)
        self.assertEqual(critic.state_dim, self.state_dim)
        
    def test_mappo_critic_forward(self):
        """测试MAPPO Critic前向传播"""
        critic = MAPPOCritic(self.state_dim, self.hidden_size)
        state = torch.randn(5, self.state_dim)
        
        values = critic(state)
        
        self.assertEqual(values.shape, (5, 1))
        self.assertTrue(torch.isfinite(values).all())
        
    def test_mappo_actor_with_extreme_inputs(self):
        """测试极端输入下的Actor行为"""
        actor = MAPPOActor(self.obs_dim, self.action_dim, self.hidden_size)
        
        # 测试零输入
        obs_zero = torch.zeros(3, self.obs_dim)
        mean, std = actor(obs_zero)
        self.assertTrue(torch.isfinite(mean).all())
        self.assertTrue(torch.all(std > 0))
        
        # 测试大数输入
        obs_large = torch.ones(3, self.obs_dim) * 1000
        mean, std = actor(obs_large)
        self.assertTrue(torch.isfinite(mean).all())
        self.assertTrue(torch.all(std > 0))


class TestEnhancedRewardTracker(unittest.TestCase):
    """测试增强奖励追踪器"""
    
    def setUp(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config()
        self.tracker = EnhancedRewardTracker(self.temp_dir, self.config)
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.tracker.log_dir, self.temp_dir)
        self.assertEqual(self.tracker.config, self.config)
        self.assertEqual(len(self.tracker.training_rewards['episode_rewards']), 0)
        self.assertEqual(self.tracker.training_rewards['episodes_completed'], 0)
        
    def test_log_training_step(self):
        """测试训练步骤记录"""
        step = 100
        env_id = 0
        reward = 10.5
        agent_rewards = [5.0, 5.5]
        info = {'served_users': 15, 'total_users': 20}
        
        self.tracker.log_training_step(step, env_id, reward, agent_rewards, info)
        
        self.assertEqual(self.tracker.training_rewards['total_steps'], 1)
        self.assertEqual(len(self.tracker.training_rewards['step_rewards']), 1)
        self.assertEqual(len(self.tracker.training_rewards['agent_rewards']), 1)
        self.assertEqual(len(self.tracker.performance_metrics['served_users']), 1)
        
        step_record = self.tracker.training_rewards['step_rewards'][0]
        self.assertEqual(step_record['step'], step)
        self.assertEqual(step_record['reward'], reward)
        
    def test_log_episode_completion(self):
        """测试episode完成记录"""
        episode_num = 1
        env_id = 0
        total_reward = 100.0
        episode_length = 200
        agent_rewards = [50.0, 50.0]
        info = {'coverage_ratio': 0.8}
        
        self.tracker.log_episode_completion(
            episode_num, env_id, total_reward, episode_length, agent_rewards, info
        )
        
        self.assertEqual(self.tracker.training_rewards['episodes_completed'], 1)
        self.assertEqual(len(self.tracker.training_rewards['episode_rewards']), 1)
        self.assertEqual(len(self.tracker.performance_metrics['agent_coordination']), 1)
        
        episode_record = self.tracker.training_rewards['episode_rewards'][0]
        self.assertEqual(episode_record['total_reward'], total_reward)
        self.assertEqual(episode_record['episode_length'], episode_length)
        
    def test_get_summary_statistics(self):
        """测试摘要统计信息"""
        # 添加一些数据
        for i in range(5):
            self.tracker.log_episode_completion(
                i+1, 0, float(i*10), 100, [float(i*5), float(i*5)], {}
            )
            
        summary = self.tracker.get_summary_statistics()
        
        self.assertEqual(summary['total_episodes'], 5)
        self.assertIn('reward_mean', summary)
        self.assertIn('reward_std', summary)
        self.assertIn('avg_coordination', summary)
        
    def test_export_training_data(self):
        """测试训练数据导出"""
        # 添加一些数据
        for i in range(3):
            self.tracker.log_episode_completion(
                i+1, 0, float(i*10), 100, [float(i*5), float(i*5)], {}
            )
            
        # 设置导出间隔为0以强制导出
        self.tracker.export_interval = 0
        self.tracker.export_training_data(1000)
        
        export_dir = os.path.join(self.temp_dir, 'paper_data')
        self.assertTrue(os.path.exists(export_dir))
        
        # 检查CSV文件是否创建
        reward_csv = os.path.join(export_dir, 'episode_rewards_step_1000.csv')
        coord_csv = os.path.join(export_dir, 'agent_coordination_step_1000.csv')
        
        if os.path.exists(reward_csv):
            df = pd.read_csv(reward_csv)
            self.assertEqual(len(df), 3)
            
    def test_generate_training_plots(self):
        """测试训练图表生成"""
        # 添加足够的数据来生成图表
        for i in range(10):
            self.tracker.log_episode_completion(
                i+1, 0, float(i*10 + np.random.randn()), 
                100 + i*5, [float(i*5), float(i*5)], {}
            )
            
        export_dir = os.path.join(self.temp_dir, 'plots')
        os.makedirs(export_dir, exist_ok=True)
        
        # 测试图表生成不会抛出异常
        try:
            self.tracker.generate_training_plots(export_dir, 1000)
            plot_file = os.path.join(export_dir, 'mappo_training_progress_step_1000.png')
            # 图表文件可能存在也可能不存在，取决于matplotlib配置
        except Exception as e:
            self.fail(f"图表生成失败: {e}")


class TestMAPPOAgent(unittest.TestCase):
    """测试MAPPO智能体"""
    
    def setUp(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config()
        self.config.obs_dim = 10
        self.config.state_dim = 20
        self.config.action_dim = 3
        self.config.hidden_size = 32  # 使用较小的网络加速测试
        self.config.lr_coordinator = 1e-3
        self.config.buffer_size = 100
        self.config.gamma = 0.99
        self.config.gae_lambda = 0.95
        self.config.clip_epsilon = 0.2
        self.config.entropy_coef = 0.01
        self.config.max_grad_norm = 0.5
        self.config.ppo_epochs = 2  # 减少epoch数加速测试
        
        self.device = 'cpu'
        self.agent = MAPPOAgent(self.config, self.temp_dir, self.device)
        
    def tearDown(self):
        """测试后清理"""
        self.agent.writer.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_initialization(self):
        """测试智能体初始化"""
        self.assertEqual(self.agent.config, self.config)
        self.assertEqual(self.agent.device, self.device)
        self.assertIsInstance(self.agent.actor, MAPPOActor)
        self.assertIsInstance(self.agent.critic, MAPPOCritic)
        self.assertIsInstance(self.agent.buffer, ReplayBuffer)
        
    def test_select_actions(self):
        """测试动作选择"""
        batch_size = 3
        obs = np.random.randn(batch_size, self.config.obs_dim)
        states = np.random.randn(batch_size, self.config.state_dim)
        
        # 测试随机动作选择
        actions, log_probs, values = self.agent.select_actions(obs, states, deterministic=False)
        
        self.assertEqual(actions.shape, (batch_size, self.config.action_dim))
        self.assertEqual(log_probs.shape, (batch_size,))
        self.assertEqual(values.shape, (batch_size,))
        
        # 测试确定性动作选择
        det_actions, det_log_probs, det_values = self.agent.select_actions(obs, states, deterministic=True)
        
        self.assertEqual(det_actions.shape, (batch_size, self.config.action_dim))
        self.assertEqual(det_log_probs.shape, (batch_size,))
        self.assertEqual(det_values.shape, (batch_size,))
        
    def test_store_transition(self):
        """测试经验存储"""
        obs = np.random.randn(self.config.obs_dim)
        next_obs = np.random.randn(self.config.obs_dim)
        states = np.random.randn(self.config.state_dim)
        next_states = np.random.randn(self.config.state_dim)
        actions = np.random.randn(self.config.action_dim)
        rewards = 10.0
        dones = False
        log_probs = np.random.randn()
        values = np.random.randn()
        
        initial_buffer_size = len(self.agent.buffer)
        
        self.agent.store_transition(
            obs, next_obs, states, next_states, 
            actions, rewards, dones, log_probs, values
        )
        
        self.assertEqual(len(self.agent.buffer), initial_buffer_size + 1)
        
    def test_store_transition_with_different_types(self):
        """测试不同数据类型的经验存储"""
        # 测试不同的rewards类型
        obs = np.random.randn(self.config.obs_dim)
        next_obs = np.random.randn(self.config.obs_dim)
        states = np.random.randn(self.config.state_dim)
        next_states = np.random.randn(self.config.state_dim)
        actions = np.random.randn(self.config.action_dim)
        log_probs = np.random.randn()
        values = np.random.randn()
        
        # 测试不同的奖励类型
        reward_types = [
            10.0,  # float
            [10.0],  # list
            np.array([10.0]),  # numpy array
            torch.tensor(10.0),  # torch tensor
        ]
        
        for reward in reward_types:
            self.agent.store_transition(
                obs, next_obs, states, next_states, 
                actions, reward, False, log_probs, values
            )
            
        # 测试不同的done类型
        done_types = [True, False, [True], np.array([False]), torch.tensor(True)]
        
        for done in done_types:
            self.agent.store_transition(
                obs, next_obs, states, next_states, 
                actions, 5.0, done, log_probs, values
            )
            
    def test_update_insufficient_data(self):
        """测试数据不足时的更新"""
        # 缓冲区为空时应返回空字典
        update_info = self.agent.update()
        self.assertEqual(update_info, {})
        
    def test_update_with_sufficient_data(self):
        """测试有足够数据时的更新"""
        # 添加足够的经验数据
        for i in range(self.config.buffer_size // 2):
            obs = np.random.randn(self.config.obs_dim)
            next_obs = np.random.randn(self.config.obs_dim)
            states = np.random.randn(self.config.state_dim)
            next_states = np.random.randn(self.config.state_dim)
            actions = np.random.randn(self.config.action_dim)
            rewards = np.random.randn()
            dones = i % 10 == 0  # 每10步结束一次
            log_probs = np.random.randn()
            values = np.random.randn()
            
            self.agent.store_transition(
                obs, next_obs, states, next_states, 
                actions, rewards, dones, log_probs, values
            )
            
        # 执行更新
        update_info = self.agent.update()
        
        # 检查更新信息
        self.assertIn('actor_loss', update_info)
        self.assertIn('critic_loss', update_info)
        self.assertIn('update_step', update_info)
        
        # 检查损失值是否合理
        self.assertTrue(np.isfinite(update_info['actor_loss']))
        self.assertTrue(np.isfinite(update_info['critic_loss']))
        
    def test_save_and_load_model(self):
        """测试模型保存和加载"""
        model_path = os.path.join(self.temp_dir, 'test_model.pt')
        
        # 保存模型
        self.agent.save_model(model_path)
        self.assertTrue(os.path.exists(model_path))
        
        # 创建新智能体并加载模型
        new_agent = MAPPOAgent(self.config, self.temp_dir, self.device)
        new_agent.load_model(model_path)
        
        # 比较参数
        for (name1, param1), (name2, param2) in zip(
            self.agent.actor.named_parameters(), 
            new_agent.actor.named_parameters()
        ):
            self.assertEqual(name1, name2)
            torch.testing.assert_close(param1, param2)


class TestUtilityFunctions(unittest.TestCase):
    """测试工具函数"""
    
    def test_get_device_auto(self):
        """测试自动设备选择"""
        device = get_device('auto')
        self.assertIn(device, ['cuda', 'cpu'])
        
    def test_get_device_cpu(self):
        """测试CPU设备选择"""
        device = get_device('cpu')
        self.assertEqual(device, 'cpu')
        
    def test_get_device_cuda(self):
        """测试CUDA设备选择"""
        device = get_device('cuda')
        # 如果CUDA不可用，应该回退到CPU
        self.assertIn(device, ['cuda', 'cpu'])
        
    def test_monitor_gradients(self):
        """测试梯度监控"""
        # 创建一个简单的模型
        model = nn.Linear(10, 5)
        
        # 创建一些假数据并计算梯度
        x = torch.randn(3, 10)
        y = torch.randn(3, 5)
        loss = nn.MSELoss()(model(x), y)
        loss.backward()
        
        # 监控梯度
        logger = get_logger("test_grad")
        total_norm, grad_norms = monitor_gradients(model, "test_model", logger)
        
        self.assertIsInstance(total_norm, float)
        self.assertIsInstance(grad_norms, list)
        self.assertTrue(total_norm >= 0)
        self.assertTrue(all(norm >= 0 for norm in grad_norms))
        
    def test_log_memory_usage(self):
        """测试内存使用记录"""
        logger = get_logger("test_memory")
        memory_stats = log_memory_usage(logger, step=100)
        
        self.assertIsInstance(memory_stats, dict)
        self.assertIn('cpu_memory', memory_stats)
        self.assertIn('cpu_memory_percent', memory_stats)
        self.assertIn('system_memory_percent', memory_stats)
        
        # 检查内存值是否合理
        self.assertTrue(memory_stats['cpu_memory'] >= 0)
        self.assertTrue(0 <= memory_stats['cpu_memory_percent'] <= 100)
        self.assertTrue(0 <= memory_stats['system_memory_percent'] <= 100)


class TestMockEnvironmentIntegration(unittest.TestCase):
    """使用模拟环境测试集成功能"""
    
    def setUp(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_mock_env(self):
        """创建模拟环境"""
        mock_env = Mock()
        mock_env.n_uavs = 3
        mock_env.obs_dim = 8
        mock_env.state_dim = 15
        mock_env.action_dim = 3
        
        # 模拟reset方法
        def mock_reset():
            obs = np.random.randn(mock_env.obs_dim)
            info = {
                'state': np.random.randn(mock_env.state_dim),
                'scenario': 'test_scenario'
            }
            return obs, info
            
        mock_env.reset = mock_reset
        
        # 模拟step方法
        def mock_step(action):
            next_obs = np.random.randn(mock_env.obs_dim)
            reward = np.random.randn()
            terminated = False
            truncated = False
            info = {
                'next_state': np.random.randn(mock_env.state_dim),
                'reward_info': {'total_throughput_mbps': 100.0},
                'served_users': 10
            }
            return next_obs, reward, terminated, truncated, info
            
        mock_env.step = mock_step
        mock_env.close = Mock()
        
        return mock_env
        
    def test_mock_environment_interaction(self):
        """测试与模拟环境的交互"""
        env = self.create_mock_env()
        
        # 测试重置
        obs, info = env.reset()
        self.assertEqual(obs.shape, (env.obs_dim,))
        self.assertIn('state', info)
        
        # 测试步骤
        action = np.random.randn(env.action_dim)
        next_obs, reward, terminated, truncated, info = env.step(action)
        
        self.assertEqual(next_obs.shape, (env.obs_dim,))
        self.assertIsInstance(reward, (int, float, np.number))
        self.assertIsInstance(terminated, bool)
        self.assertIsInstance(truncated, bool)
        self.assertIsInstance(info, dict)
        
    def test_mappo_agent_with_mock_env(self):
        """测试MAPPO智能体与模拟环境的集成"""
        # 创建配置
        config = Config()
        config.obs_dim = 8
        config.state_dim = 15
        config.action_dim = 3
        config.hidden_size = 16  # 小网络加速测试
        config.lr_coordinator = 1e-3
        config.buffer_size = 50
        config.gamma = 0.99
        config.gae_lambda = 0.95
        config.clip_epsilon = 0.2
        config.entropy_coef = 0.01
        config.max_grad_norm = 0.5
        config.ppo_epochs = 1
        
        # 创建智能体
        agent = MAPPOAgent(config, self.temp_dir, 'cpu')
        
        # 模拟训练循环
        env = self.create_mock_env()
        obs, info = env.reset()
        state = info['state']
        
        total_reward = 0
        for step in range(20):  # 短循环用于测试
            # 选择动作
            actions, log_probs, values = agent.select_actions(
                obs.reshape(1, -1), state.reshape(1, -1)
            )
            
            # 执行动作
            next_obs, reward, terminated, truncated, info = env.step(actions[0])
            next_state = info['next_state']
            
            # 存储经验
            agent.store_transition(
                obs, next_obs, state, next_state,
                actions[0], reward, terminated, log_probs[0], values[0]
            )
            
            total_reward += reward
            obs = next_obs
            state = next_state
            
            if terminated or truncated:
                obs, info = env.reset()
                state = info['state']
                total_reward = 0
                
        # 测试更新（如果有足够数据）
        if len(agent.buffer) >= config.buffer_size // 4:
            update_info = agent.update()
            self.assertIsInstance(update_info, dict)
            
        agent.writer.close()


class TestErrorHandlingAndEdgeCases(unittest.TestCase):
    """测试错误处理和边界情况"""
    
    def setUp(self):
        """测试前设置"""
        self.logger = get_logger("test_error")
        
    def test_check_tensor_health_with_malformed_input(self):
        """测试畸形输入的张量健康检查"""
        # 测试非张量输入
        result = check_tensor_health("not_a_tensor", "string_input", self.logger)
        self.assertFalse(result)
        
        # 测试整数输入
        result = check_tensor_health(42, "int_input", self.logger)
        self.assertFalse(result)
        
        # 测试列表输入
        result = check_tensor_health([1, 2, 3], "list_input", self.logger)
        self.assertFalse(result)
        
    def test_safe_divide_edge_cases(self):
        """测试安全除法的边界情况"""
        # 测试NaN输入
        numerator = torch.tensor([1.0, float('nan'), 3.0])
        denominator = torch.tensor([2.0, 2.0, 2.0])
        result = safe_divide(numerator, denominator, logger=self.logger)
        # 应该返回一个安全的结果
        self.assertTrue(result.shape == numerator.shape)
        
        # 测试Inf输入
        numerator = torch.tensor([float('inf'), 2.0, 3.0])
        result = safe_divide(numerator, denominator, logger=self.logger)
        self.assertTrue(result.shape == numerator.shape)
        
    def test_mappo_actor_with_corrupted_input(self):
        """测试损坏输入下的MAPPO Actor行为"""
        actor = MAPPOActor(10, 3, 32)
        
        # 测试NaN输入
        obs_nan = torch.tensor([[1.0, float('nan'), 3.0] + [0.0] * 7])
        try:
            mean, std = actor(obs_nan)
            # 应该能够处理而不崩溃
            self.assertTrue(torch.isfinite(mean).any() or torch.isfinite(std).any())
        except Exception as e:
            # 如果抛出异常，确保是可控的
            self.assertIsInstance(e, (ValueError, RuntimeError))
            
    def test_enhanced_reward_tracker_with_empty_data(self):
        """测试空数据下的奖励追踪器"""
        temp_dir = tempfile.mkdtemp()
        try:
            config = Config()
            tracker = EnhancedRewardTracker(temp_dir, config)
            
            # 测试空数据导出
            tracker.export_training_data(1000)
            
            # 测试空数据统计
            summary = tracker.get_summary_statistics()
            self.assertEqual(summary['total_episodes'], 0)
            self.assertEqual(summary['total_steps'], 0)
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    def test_mappo_agent_buffer_overflow(self):
        """测试缓冲区溢出情况"""
        temp_dir = tempfile.mkdtemp()
        try:
            config = Config()
            config.obs_dim = 5
            config.state_dim = 10
            config.action_dim = 2
            config.hidden_size = 16
            config.buffer_size = 10  # 小缓冲区
            config.lr_coordinator = 1e-3
            
            agent = MAPPOAgent(config, temp_dir, 'cpu')
            
            # 添加超过缓冲区容量的数据
            for i in range(15):  # 超过buffer_size
                obs = np.random.randn(config.obs_dim)
                next_obs = np.random.randn(config.obs_dim)
                states = np.random.randn(config.state_dim)
                next_states = np.random.randn(config.state_dim)
                actions = np.random.randn(config.action_dim)
                rewards = np.random.randn()
                dones = False
                log_probs = np.random.randn()
                values = np.random.randn()
                
                agent.store_transition(
                    obs, next_obs, states, next_states,
                    actions, rewards, dones, log_probs, values
                )
                
            # 缓冲区大小应该被限制
            self.assertLessEqual(len(agent.buffer), config.buffer_size)
            
            agent.writer.close()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestEndToEndScenarios(unittest.TestCase):
    """端到端场景测试"""
    
    def setUp(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    @patch('train_mappo_enhanced_tracking.make_env')
    def test_mini_training_loop(self, mock_make_env):
        """测试迷你训练循环"""
        # 创建模拟环境工厂
        def create_mock_env_factory():
            def env_factory():
                mock_env = Mock()
                mock_env.n_uavs = 2
                mock_env.obs_dim = 6
                mock_env.state_dim = 12
                mock_env.action_dim = 3
                
                def reset():
                    return (np.random.randn(mock_env.obs_dim), 
                           {'state': np.random.randn(mock_env.state_dim)})
                           
                def step(action):
                    return (np.random.randn(mock_env.obs_dim),
                           np.random.randn(),
                           False,  # terminated
                           False,  # truncated
                           {'next_state': np.random.randn(mock_env.state_dim)})
                           
                mock_env.reset = reset
                mock_env.step = step
                mock_env.close = Mock()
                return mock_env
            return env_factory
            
        mock_make_env.return_value = create_mock_env_factory()
        
        # 创建最小配置
        config = Config()
        config.obs_dim = 6
        config.state_dim = 12
        config.action_dim = 3
        config.n_agents = 2
        config.hidden_size = 16
        config.lr_coordinator = 1e-3
        config.buffer_size = 20
        config.total_timesteps = 100  # 非常短的训练
        config.gamma = 0.99
        config.gae_lambda = 0.95
        config.clip_epsilon = 0.2
        config.entropy_coef = 0.01
        config.max_grad_norm = 0.5
        config.ppo_epochs = 1
        
        # 模拟命令行参数
        class MockArgs:
            def __init__(self):
                self.num_envs = 2
                self.log_dir = self.temp_dir
                self.model_path = os.path.join(self.temp_dir, 'test_model.pt')
                self.scenario = 2
                self.n_uavs = 2
                self.n_users = 10
                self.user_distribution = 'uniform'
                self.channel_model = 'free_space'
                self.max_hops = 3
                self.export_interval = 50
                
        MockArgs.temp_dir = self.temp_dir
        args = MockArgs()
        
        try:
            # 这里我们不能直接调用train函数，因为它依赖于真实的环境
            # 相反，我们测试训练的核心组件
            
            # 创建智能体
            agent = MAPPOAgent(config, self.temp_dir, 'cpu')
            
            # 创建奖励追踪器
            tracker = EnhancedRewardTracker(self.temp_dir, config)
            
            # 模拟简单的训练循环
            envs = [mock_make_env().return_value() for _ in range(args.num_envs)]
            
            observations = []
            states = []
            for env in envs:
                obs, info = env.reset()
                observations.append(obs)
                states.append(info['state'])
                
            observations = np.array(observations)
            states = np.array(states)
            
            total_steps = 0
            episode_count = 0
            
            # 运行几步
            for _ in range(10):
                # 选择动作
                actions, log_probs, values = agent.select_actions(observations, states)
                
                # 执行动作
                next_observations = []
                next_states = []
                rewards = []
                dones = []
                
                for i, env in enumerate(envs):
                    next_obs, reward, terminated, truncated, info = env.step(actions[i])
                    next_observations.append(next_obs)
                    next_states.append(info['next_state'])
                    rewards.append(reward)
                    dones.append(terminated or truncated)
                    
                next_observations = np.array(next_observations)
                next_states = np.array(next_states)
                rewards = np.array(rewards)
                dones = np.array(dones)
                
                # 存储经验
                for i in range(args.num_envs):
                    agent.store_transition(
                        observations[i], next_observations[i],
                        states[i], next_states[i],
                        actions[i], rewards[i], dones[i],
                        log_probs[i], values[i]
                    )
                    
                    if dones[i]:
                        episode_count += 1
                        tracker.log_episode_completion(
                            episode_count, i, rewards[i], 10, [rewards[i]], {}
                        )
                        
                observations = next_observations
                states = next_states
                total_steps += args.num_envs
                
            # 测试更新
            if len(agent.buffer) >= config.buffer_size // 4:
                update_info = agent.update()
                self.assertIsInstance(update_info, dict)
                
            # 测试保存
            agent.save_model(args.model_path)
            self.assertTrue(os.path.exists(args.model_path))
            
            # 测试数据导出
            tracker.export_training_data(total_steps)
            
            agent.writer.close()
            
        except Exception as e:
            self.fail(f"迷你训练循环失败: {e}")


class TestPerformanceAndStress(unittest.TestCase):
    """性能和压力测试"""
    
    def test_tensor_health_performance(self):
        """测试张量健康检查的性能"""
        logger = get_logger("test_perf")
        
        # 创建大张量
        large_tensor = torch.randn(1000, 1000)
        
        start_time = time.time()
        for _ in range(100):
            check_tensor_health(large_tensor, "large_tensor", logger)
        end_time = time.time()
        
        # 检查性能是否合理（应该在几秒内完成）
        elapsed = end_time - start_time
        self.assertLess(elapsed, 10.0, "张量健康检查性能过慢")
        
    def test_memory_tracking_overhead(self):
        """测试内存跟踪的开销"""
        logger = get_logger("test_memory_perf")
        
        start_time = time.time()
        for i in range(50):
            log_memory_usage(logger, step=i)
        end_time = time.time()
        
        elapsed = end_time - start_time
        self.assertLess(elapsed, 5.0, "内存跟踪开销过大")
        
    def test_reward_tracker_scalability(self):
        """测试奖励追踪器的扩展性"""
        temp_dir = tempfile.mkdtemp()
        try:
            config = Config()
            tracker = EnhancedRewardTracker(temp_dir, config)
            
            start_time = time.time()
            
            # 添加大量数据
            for i in range(1000):
                tracker.log_episode_completion(
                    i+1, 0, float(i), 100, [float(i/2), float(i/2)], {}
                )
                
            end_time = time.time()
            elapsed = end_time - start_time
            
            self.assertLess(elapsed, 10.0, "奖励追踪器扩展性不足")
            
            # 测试摘要生成性能
            start_time = time.time()
            summary = tracker.get_summary_statistics()
            end_time = time.time()
            
            summary_elapsed = end_time - start_time
            self.assertLess(summary_elapsed, 1.0, "摘要生成过慢")
            self.assertEqual(summary['total_episodes'], 1000)
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


# 自定义测试运行器
class VerboseTestResult(unittest.TextTestResult):
    """详细的测试结果显示"""
    
    def addSuccess(self, test):
        super().addSuccess(test)
        if self.showAll:
            self.stream.writeln(f"✓ {test.id()}")
            
    def addError(self, test, err):
        super().addError(test, err)
        if self.showAll:
            self.stream.writeln(f"✗ {test.id()} - ERROR")
            
    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.showAll:
            self.stream.writeln(f"✗ {test.id()} - FAIL")


def run_test_suite():
    """运行测试套件"""
    # 初始化日志系统
    temp_log_dir = tempfile.mkdtemp()
    try:
        init_multiproc_logging(
            log_dir=temp_log_dir,
            log_file="test_mappo.log",
            file_level=logging.INFO,
            console_level=logging.WARNING
        )
        
        # 创建测试套件
        test_classes = [
            TestNumericalStabilityFunctions,
            TestNetworkComponents,
            TestEnhancedRewardTracker,
            TestMAPPOAgent,
            TestUtilityFunctions,
            TestMockEnvironmentIntegration,
            TestErrorHandlingAndEdgeCases,
            TestEndToEndScenarios,
            TestPerformanceAndStress,
        ]
        
        suite = unittest.TestSuite()
        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)
            
        # 运行测试
        runner = unittest.TextTestRunner(
            verbosity=2,
            resultclass=VerboseTestResult,
            stream=sys.stdout
        )
        
        print("=" * 70)
        print("运行 train_mappo_enhanced_tracking.py 测试套件")
        print("=" * 70)
        
        result = runner.run(suite)
        
        # 输出总结
        print("\n" + "=" * 70)
        print("测试总结:")
        print(f"运行测试: {result.testsRun}")
        print(f"失败: {len(result.failures)}")
        print(f"错误: {len(result.errors)}")
        print(f"跳过: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
        
        if result.failures:
            print("\n失败的测试:")
            for test, traceback in result.failures:
                print(f"  - {test.id()}")
                
        if result.errors:
            print("\n错误的测试:")
            for test, traceback in result.errors:
                print(f"  - {test.id()}")
                
        success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
        print(f"\n成功率: {success_rate:.1f}%")
        print("=" * 70)
        
        return result.wasSuccessful()
        
    finally:
        try:
            shutdown_logging()
        except:
            pass
        shutil.rmtree(temp_log_dir, ignore_errors=True)


if __name__ == "__main__":
    # 设置测试环境
    os.environ['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
    
    # 运行测试
    success = run_test_suite()
    
    # 退出代码
    sys.exit(0 if success else 1)
