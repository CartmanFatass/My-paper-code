#!/usr/bin/env python3
"""
线程安全测试脚本
测试HMASD Agent在多线程环境下的线程安全性
"""

import threading
import time
import numpy as np
import torch
from concurrent.futures import ThreadPoolExecutor
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入必要的模块
from config import Config
from hmasd.agent import HMASDAgent

class ThreadSafetyTester:
    """线程安全测试器"""
    
    def __init__(self):
        self.config = Config()
        self.config.state_dim = 10
        self.config.obs_dim = 8
        self.config.action_dim = 4
        self.config.n_agents = 3
        self.config.n_Z = 5
        self.config.n_z = 4
        self.config.k = 8
        self.config.rollout_based_training = True
        self.config.rollout_length = 32
        self.config.num_parallel_envs = 8
        
        # 创建Agent
        self.agent = HMASDAgent(self.config, log_dir='logs/thread_safety_test')
        
        # 测试结果
        self.test_results = {
            'concurrent_step_calls': {'success': 0, 'error': 0},
            'concurrent_buffer_operations': {'success': 0, 'error': 0},
            'concurrent_counter_updates': {'success': 0, 'error': 0},
            'state_consistency': {'success': 0, 'error': 0}
        }
        
        self.lock = threading.Lock()
    
    def simulate_environment_step(self, env_id, num_steps=10):
        """模拟环境步骤"""
        try:
            for step in range(num_steps):
                # 生成随机状态和观测
                state = np.random.randn(self.config.state_dim)
                observations = np.random.randn(self.config.n_agents, self.config.obs_dim)
                
                # 执行step
                actions, info = self.agent.step(state, observations, step, env_id=env_id)
                
                # 模拟环境反馈
                next_state = np.random.randn(self.config.state_dim)
                next_observations = np.random.randn(self.config.n_agents, self.config.obs_dim)
                rewards = np.random.randn()
                dones = False
                
                # 存储经验
                success = self.agent.store_transition(
                    state, next_state, observations, next_observations,
                    actions, rewards, dones, info['team_skill'], info['agent_skills'],
                    info['action_logprobs'], info['log_probs'], info['skill_timer'], env_id
                )
                
                if success:
                    # 更新rollout计数器
                    self.agent.step_rollout_counter()
                
                # 短暂休眠模拟真实环境延迟
                time.sleep(0.001)
            
            with self.lock:
                self.test_results['concurrent_step_calls']['success'] += 1
                
        except Exception as e:
            logger.error(f"环境{env_id}步骤执行失败: {e}")
            with self.lock:
                self.test_results['concurrent_step_calls']['error'] += 1
    
    def test_concurrent_buffer_operations(self, num_operations=50):
        """测试并发缓冲区操作"""
        try:
            for _ in range(num_operations):
                # 随机选择操作类型
                operation = np.random.choice(['high_level', 'low_level', 'state_skill'])
                
                if operation == 'high_level':
                    # 模拟高层经验存储
                    state = torch.randn(self.config.state_dim)
                    team_skill = np.random.randint(0, self.config.n_Z)
                    observations = torch.randn(self.config.n_agents, self.config.obs_dim)
                    agent_skills = np.random.randint(0, self.config.n_z, self.config.n_agents)
                    reward = np.random.randn()
                    
                    self.agent.store_high_level_transition(
                        state.numpy(), team_skill, observations.numpy(), 
                        agent_skills, reward, worker_id=0
                    )
                
                elif operation == 'low_level':
                    # 模拟低层经验存储
                    state = torch.randn(self.config.state_dim)
                    next_state = torch.randn(self.config.state_dim)
                    observations = torch.randn(self.config.n_agents, self.config.obs_dim)
                    next_observations = torch.randn(self.config.n_agents, self.config.obs_dim)
                    actions = torch.randn(self.config.n_agents, self.config.action_dim)
                    rewards = np.random.randn()
                    dones = False
                    team_skill = np.random.randint(0, self.config.n_Z)
                    agent_skills = np.random.randint(0, self.config.n_z, self.config.n_agents)
                    action_logprobs = torch.randn(self.config.n_agents)
                    
                    self.agent.store_low_level_transition(
                        state.numpy(), next_state.numpy(), 
                        observations.numpy(), next_observations.numpy(),
                        actions.numpy(), rewards, dones, team_skill, agent_skills,
                        action_logprobs.numpy(), worker_id=0
                    )
                
                time.sleep(0.001)
            
            with self.lock:
                self.test_results['concurrent_buffer_operations']['success'] += 1
                
        except Exception as e:
            logger.error(f"缓冲区操作失败: {e}")
            with self.lock:
                self.test_results['concurrent_buffer_operations']['error'] += 1
    
    def test_concurrent_counter_updates(self, num_updates=100):
        """测试并发计数器更新"""
        try:
            for _ in range(num_updates):
                # 测试rollout计数器
                self.agent.step_rollout_counter()
                
                # 测试全局步数更新
                with self.agent.step_lock:
                    self.agent.global_step += 1
                
                time.sleep(0.0001)
            
            with self.lock:
                self.test_results['concurrent_counter_updates']['success'] += 1
                
        except Exception as e:
            logger.error(f"计数器更新失败: {e}")
            with self.lock:
                self.test_results['concurrent_counter_updates']['error'] += 1
    
    def test_state_consistency(self, env_id, num_checks=20):
        """测试状态一致性"""
        try:
            for _ in range(num_checks):
                # 检查环境状态的一致性
                with self.agent.state_lock:
                    team_skill = self.agent.env_team_skills.get(env_id)
                    agent_skills = self.agent.env_agent_skills.get(env_id)
                    timer = self.agent.env_timers.get(env_id, 0)
                    reward_sum = self.agent.env_reward_sums.get(env_id, 0.0)
                
                # 验证状态的合理性
                if team_skill is not None:
                    assert 0 <= team_skill < self.config.n_Z, f"无效的团队技能: {team_skill}"
                
                if agent_skills is not None:
                    for skill in agent_skills:
                        assert 0 <= skill < self.config.n_z, f"无效的个体技能: {skill}"
                
                assert timer >= 0, f"无效的计时器值: {timer}"
                assert isinstance(reward_sum, (int, float)), f"无效的奖励累积: {reward_sum}"
                
                time.sleep(0.001)
            
            with self.lock:
                self.test_results['state_consistency']['success'] += 1
                
        except Exception as e:
            logger.error(f"状态一致性检查失败: {e}")
            with self.lock:
                self.test_results['state_consistency']['error'] += 1
    
    def run_concurrent_tests(self, num_threads=8, duration=10):
        """运行并发测试"""
        logger.info(f"开始线程安全测试，使用{num_threads}个线程，持续{duration}秒")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            
            # 提交不同类型的测试任务
            for i in range(num_threads // 4):
                # 环境步骤测试
                futures.append(executor.submit(self.simulate_environment_step, i, 20))
                
                # 缓冲区操作测试
                futures.append(executor.submit(self.test_concurrent_buffer_operations, 30))
                
                # 计数器更新测试
                futures.append(executor.submit(self.test_concurrent_counter_updates, 50))
                
                # 状态一致性测试
                futures.append(executor.submit(self.test_state_consistency, i, 15))
            
            # 等待所有任务完成或超时
            for future in futures:
                try:
                    future.result(timeout=duration)
                except Exception as e:
                    logger.error(f"任务执行失败: {e}")
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        logger.info(f"测试完成，耗时: {test_duration:.2f}秒")
        
        return self.test_results
    
    def print_test_results(self):
        """打印测试结果"""
        logger.info("=" * 60)
        logger.info("线程安全测试结果")
        logger.info("=" * 60)
        
        total_success = 0
        total_error = 0
        
        for test_name, results in self.test_results.items():
            success = results['success']
            error = results['error']
            total = success + error
            
            if total > 0:
                success_rate = (success / total) * 100
                logger.info(f"{test_name}:")
                logger.info(f"  成功: {success}, 失败: {error}, 成功率: {success_rate:.1f}%")
            else:
                logger.info(f"{test_name}: 未执行")
            
            total_success += success
            total_error += error
        
        logger.info("-" * 60)
        overall_total = total_success + total_error
        if overall_total > 0:
            overall_success_rate = (total_success / overall_total) * 100
            logger.info(f"总体结果: 成功: {total_success}, 失败: {total_error}, 成功率: {overall_success_rate:.1f}%")
        
        # 检查缓冲区状态
        logger.info("-" * 60)
        logger.info("缓冲区状态:")
        logger.info(f"  高层缓冲区大小: {len(self.agent.high_level_buffer)}")
        logger.info(f"  低层缓冲区大小: {len(self.agent.low_level_buffer)}")
        logger.info(f"  状态技能数据集大小: {len(self.agent.state_skill_dataset)}")
        logger.info(f"  Rollout步数: {self.agent.steps_collected}")
        logger.info(f"  全局步数: {self.agent.global_step}")
        
        logger.info("=" * 60)

def main():
    """主函数"""
    logger.info("开始HMASD Agent线程安全测试")
    
    # 创建测试器
    tester = ThreadSafetyTester()
    
    # 运行测试
    results = tester.run_concurrent_tests(num_threads=16, duration=15)
    
    # 打印结果
    tester.print_test_results()
    
    # 检查是否有严重错误
    total_errors = sum(result['error'] for result in results.values())
    if total_errors == 0:
        logger.info("✅ 所有线程安全测试通过！")
        return 0
    else:
        logger.error(f"❌ 发现 {total_errors} 个线程安全问题")
        return 1

if __name__ == "__main__":
    exit(main())
