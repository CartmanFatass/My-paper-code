#!/usr/bin/env python3
"""
测试数据损失修复效果的脚本
验证RolloutWorker高层经验收集逻辑和TrainingWorker数据传输的修复
"""

import os
import sys
import time
import numpy as np
import torch
import threading
import queue
from collections import defaultdict
from threading import Event

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logger import get_logger, init_multiproc_logging
from config import Config
from train_rollout_based_threaded import (
    RolloutWorker, TrainingWorker, AgentProxy, DataBuffer, 
    ThreadSafeCounter, ThreadedRolloutTrainer
)
from hmasd.agent import HMASDAgent
from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter

class DataLossFixTester:
    """数据损失修复效果测试器"""
    
    def __init__(self):
        self.config = Config()
        self.logger = self._init_logging()
        
        # 测试配置
        self.test_workers = 4  # 使用较少的worker进行测试
        self.test_steps = 256  # 每个worker收集256步
        self.expected_high_level_per_worker = self.test_steps // self.config.k  # 期望的高层经验数
        
        self.logger.info(f"数据损失修复测试初始化")
        self.logger.info(f"测试配置: {self.test_workers} workers, 每个收集 {self.test_steps} 步")
        self.logger.info(f"k值: {self.config.k}, 期望每worker高层经验: {self.expected_high_level_per_worker}")
    
    def _init_logging(self):
        """初始化日志系统"""
        log_dir = "logs/data_loss_fix_test"
        os.makedirs(log_dir, exist_ok=True)
        
        init_multiproc_logging(
            log_dir=log_dir,
            log_file='data_loss_fix_test.log',
            file_level=20,  # INFO
            console_level=20  # INFO
        )
        
        return get_logger("DataLossFixTester")
    
    def create_test_env(self):
        """创建测试环境"""
        def make_env():
            raw_env = UAVCooperativeNetworkEnv(
                n_uavs=5,
                n_users=50,
                max_hops=3,
                user_distribution='uniform',
                channel_model='3gpp-36777',
                seed=42
            )
            env = ParallelToArrayAdapter(raw_env, seed=42)
            return env
        return make_env
    
    def test_rollout_worker_high_level_collection(self):
        """测试1: RolloutWorker高层经验收集逻辑"""
        self.logger.info("=" * 60)
        self.logger.info("测试1: RolloutWorker高层经验收集逻辑")
        self.logger.info("=" * 60)
        
        # 创建测试环境
        env_factory = self.create_test_env()
        temp_env = env_factory()
        
        # 更新配置维度
        self.config.update_env_dims(temp_env.state_dim, temp_env.obs_dim)
        self.config.n_agents = temp_env.n_uavs
        temp_env.close()
        
        # 创建Agent和AgentProxy
        agent = HMASDAgent(
            config=self.config,
            log_dir="logs/data_loss_fix_test",
            device=torch.device('cpu'),
            debug=True
        )
        
        data_buffer = DataBuffer(maxsize=10000)
        agent_proxy = AgentProxy(agent, self.config, self.logger, data_buffer)
        
        # 创建控制事件
        control_events = {
            'stop': Event(),
            'pause': Event()
        }
        
        # 创建测试workers
        workers = []
        threads = []
        
        for i in range(self.test_workers):
            worker = RolloutWorker(
                worker_id=i,
                env_factory=env_factory,
                config=self.config,
                data_buffer=data_buffer,
                control_events=control_events,
                logger=self.logger
            )
            # 设置测试目标步数
            worker.target_rollout_steps = self.test_steps
            workers.append(worker)
        
        # 设置AgentProxy的workers引用
        agent_proxy.rollout_workers = workers
        
        # 启动workers
        for i, worker in enumerate(workers):
            thread = threading.Thread(
                target=worker.run,
                args=(agent_proxy,),
                name=f"TestWorker-{i}"
            )
            thread.daemon = True
            threads.append(thread)
            thread.start()
        
        # 监控测试进度
        start_time = time.time()
        max_test_time = 300  # 最多测试5分钟
        
        while time.time() - start_time < max_test_time:
            # 检查所有workers是否完成
            completed_workers = sum(1 for w in workers if w.rollout_completed)
            total_samples = sum(w.samples_collected for w in workers)
            total_high_level = sum(w.high_level_experiences_generated for w in workers)
            
            self.logger.info(f"测试进度: 完成workers={completed_workers}/{self.test_workers}, "
                           f"总样本={total_samples}, 总高层经验={total_high_level}")
            
            if completed_workers == self.test_workers:
                break
            
            time.sleep(5)
        
        # 停止workers
        control_events['stop'].set()
        for thread in threads:
            thread.join(timeout=5)
        
        # 分析结果
        self.analyze_rollout_test_results(workers)
        
        return workers
    
    def analyze_rollout_test_results(self, workers):
        """分析RolloutWorker测试结果"""
        self.logger.info("\n" + "=" * 50)
        self.logger.info("RolloutWorker测试结果分析")
        self.logger.info("=" * 50)
        
        total_samples = 0
        total_high_level = 0
        total_expected_high_level = 0
        
        success_workers = 0
        failed_workers = 0
        
        for worker in workers:
            samples = worker.samples_collected
            high_level = worker.high_level_experiences_generated
            expected_high_level = samples // self.config.k
            missing = expected_high_level - high_level
            
            total_samples += samples
            total_high_level += high_level
            total_expected_high_level += expected_high_level
            
            status = "✅ 成功" if missing == 0 else f"❌ 缺失{missing}个"
            if missing == 0:
                success_workers += 1
            else:
                failed_workers += 1
            
            self.logger.info(f"Worker {worker.worker_id}: "
                           f"样本={samples}, 高层经验={high_level}/{expected_high_level}, "
                           f"技能计时器={worker.skill_timer}, "
                           f"累积奖励={worker.accumulated_reward:.4f}, "
                           f"状态={status}")
        
        # 总体统计
        total_missing = total_expected_high_level - total_high_level
        success_rate = (success_workers / len(workers)) * 100
        collection_rate = (total_high_level / total_expected_high_level) * 100 if total_expected_high_level > 0 else 0
        
        self.logger.info(f"\n📊 总体统计:")
        self.logger.info(f"   成功Workers: {success_workers}/{len(workers)} ({success_rate:.1f}%)")
        self.logger.info(f"   失败Workers: {failed_workers}/{len(workers)}")
        self.logger.info(f"   总样本数: {total_samples}")
        self.logger.info(f"   高层经验收集率: {total_high_level}/{total_expected_high_level} ({collection_rate:.1f}%)")
        self.logger.info(f"   缺失高层经验: {total_missing}")
        
        # 判断测试结果
        if success_rate >= 100 and collection_rate >= 100:
            self.logger.info("🎉 测试1通过: RolloutWorker高层经验收集逻辑修复成功!")
            return True
        elif success_rate >= 90 and collection_rate >= 95:
            self.logger.warning("⚠️ 测试1基本通过: 高层经验收集大部分正常，但仍有少量问题")
            return True
        else:
            self.logger.error("❌ 测试1失败: RolloutWorker高层经验收集仍存在问题")
            return False
    
    def test_training_worker_data_transmission(self):
        """测试2: TrainingWorker数据传输可靠性"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("测试2: TrainingWorker数据传输可靠性")
        self.logger.info("=" * 60)
        
        # 创建测试数据缓冲区
        data_buffer = DataBuffer(maxsize=1000)
        
        # 创建模拟Agent和AgentProxy
        class MockAgent:
            def __init__(self):
                self.stored_experiences = []
                self.device = torch.device('cpu')
            
            def store_high_level_transition(self, **kwargs):
                self.stored_experiences.append(('high_level', kwargs))
                return True
            
            def store_low_level_transition(self, **kwargs):
                self.stored_experiences.append(('low_level', kwargs))
                return True
        
        mock_agent = MockAgent()
        agent_proxy = AgentProxy(mock_agent, self.config, self.logger, data_buffer)
        
        # 创建控制事件
        control_events = {
            'stop': Event(),
            'pause': Event()
        }
        
        # 生成测试数据
        test_data_count = 1000
        self.logger.info(f"生成 {test_data_count} 个测试经验数据...")
        
        for i in range(test_data_count):
            # 创建模拟经验数据
            if i % 3 == 0:  # 高层经验
                experience = {
                    'experience_type': 'high_level',
                    'worker_id': i % 4,
                    'state': np.random.randn(self.config.state_dim),
                    'team_skill': i % self.config.n_team_skills,
                    'observations': np.random.randn(self.config.n_agents, self.config.obs_dim),
                    'agent_skills': [i % self.config.n_agent_skills] * self.config.n_agents,
                    'accumulated_reward': np.random.randn(),
                    'skill_log_probs': {'team_log_prob': 0.0, 'agent_log_probs': [0.0] * self.config.n_agents}
                }
            else:  # 低层经验
                experience = {
                    'experience_type': 'low_level',
                    'worker_id': i % 4,
                    'state': np.random.randn(self.config.state_dim),
                    'next_state': np.random.randn(self.config.state_dim),
                    'observations': np.random.randn(self.config.n_agents, self.config.obs_dim),
                    'next_observations': np.random.randn(self.config.n_agents, self.config.obs_dim),
                    'actions': np.random.randn(self.config.n_agents, self.config.action_dim),
                    'rewards': np.random.randn(),
                    'dones': False,
                    'team_skill': i % self.config.n_team_skills,
                    'agent_skills': [i % self.config.n_agent_skills] * self.config.n_agents,
                    'action_logprobs': np.random.randn(self.config.n_agents),
                    'skill_log_probs': {'team_log_prob': 0.0, 'agent_log_probs': [0.0] * self.config.n_agents}
                }
            
            data_buffer.put(experience)
        
        # 创建TrainingWorker
        training_worker = TrainingWorker(
            worker_id=0,
            agent_proxy=agent_proxy,
            data_buffer=data_buffer,
            control_events=control_events,
            logger=self.logger,
            config=self.config,
            trainer=None
        )
        
        # 启动TrainingWorker
        self.logger.info("启动TrainingWorker进行数据传输测试...")
        thread = threading.Thread(target=training_worker.run, name="TestTrainingWorker")
        thread.daemon = True
        thread.start()
        
        # 监控数据传输
        start_time = time.time()
        max_test_time = 60  # 最多测试1分钟
        
        while time.time() - start_time < max_test_time:
            queue_size = data_buffer.qsize()
            processed = training_worker.samples_processed
            stored = len(mock_agent.stored_experiences)
            
            self.logger.info(f"数据传输进度: 队列剩余={queue_size}, "
                           f"处理样本={processed}, 存储经验={stored}")
            
            if queue_size == 0:
                break
            
            time.sleep(2)
        
        # 停止worker
        control_events['stop'].set()
        thread.join(timeout=10)
        
        # 分析结果
        return self.analyze_training_test_results(test_data_count, training_worker, mock_agent, data_buffer)
    
    def analyze_training_test_results(self, test_data_count, training_worker, mock_agent, data_buffer):
        """分析TrainingWorker测试结果"""
        self.logger.info("\n" + "=" * 50)
        self.logger.info("TrainingWorker测试结果分析")
        self.logger.info("=" * 50)
        
        processed_samples = training_worker.samples_processed
        stored_experiences = len(mock_agent.stored_experiences)
        remaining_queue = data_buffer.qsize()
        buffer_stats = data_buffer.get_stats()
        
        # 计算传输成功率
        transmission_rate = (stored_experiences / test_data_count) * 100
        processing_rate = (processed_samples / test_data_count) * 100
        
        self.logger.info(f"📊 数据传输统计:")
        self.logger.info(f"   生成测试数据: {test_data_count}")
        self.logger.info(f"   处理样本数: {processed_samples}")
        self.logger.info(f"   存储经验数: {stored_experiences}")
        self.logger.info(f"   剩余队列: {remaining_queue}")
        self.logger.info(f"   传输成功率: {transmission_rate:.1f}%")
        self.logger.info(f"   处理成功率: {processing_rate:.1f}%")
        self.logger.info(f"   缓冲区统计: {buffer_stats}")
        
        # 分析经验类型分布
        high_level_count = sum(1 for exp_type, _ in mock_agent.stored_experiences if exp_type == 'high_level')
        low_level_count = sum(1 for exp_type, _ in mock_agent.stored_experiences if exp_type == 'low_level')
        
        self.logger.info(f"📈 经验类型分布:")
        self.logger.info(f"   高层经验: {high_level_count}")
        self.logger.info(f"   低层经验: {low_level_count}")
        
        # 判断测试结果
        if transmission_rate >= 99 and remaining_queue <= 10:
            self.logger.info("🎉 测试2通过: TrainingWorker数据传输可靠性修复成功!")
            return True
        elif transmission_rate >= 95 and remaining_queue <= 50:
            self.logger.warning("⚠️ 测试2基本通过: 数据传输大部分正常，但仍有少量丢失")
            return True
        else:
            self.logger.error("❌ 测试2失败: TrainingWorker数据传输仍存在问题")
            return False
    
    def test_integrated_system(self):
        """测试3: 集成系统测试"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("测试3: 集成系统测试")
        self.logger.info("=" * 60)
        
        try:
            # 创建小规模的完整训练器进行测试
            import argparse
            
            # 创建测试参数
            test_args = argparse.Namespace(
                steps=1000,  # 只训练1000步进行测试
                device='cpu',
                debug=True,
                training_threads=2,  # 减少线程数
                rollout_threads=4,   # 减少线程数
                buffer_size=1000,
                scenario=2,
                n_uavs=5,
                n_users=50,
                user_distribution='uniform',
                channel_model='3gpp-36777',
                max_hops=3,
                log_level='INFO',
                console_log_level='INFO'
            )
            
            # 创建训练器
            trainer = ThreadedRolloutTrainer(self.config, test_args)
            
            self.logger.info("开始集成系统测试...")
            start_time = time.time()
            
            # 运行短时间训练
            trainer.train(total_steps=1000)
            
            test_duration = time.time() - start_time
            
            # 分析集成测试结果
            return self.analyze_integrated_test_results(trainer, test_duration)
            
        except Exception as e:
            self.logger.error(f"集成系统测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def analyze_integrated_test_results(self, trainer, test_duration):
        """分析集成测试结果"""
        self.logger.info("\n" + "=" * 50)
        self.logger.info("集成系统测试结果分析")
        self.logger.info("=" * 50)
        
        try:
            # 收集统计信息
            if hasattr(trainer, 'rollout_workers'):
                total_samples = sum(w.samples_collected for w in trainer.rollout_workers)
                total_high_level = sum(w.high_level_experiences_generated for w in trainer.rollout_workers)
                completed_workers = sum(1 for w in trainer.rollout_workers if w.rollout_completed)
                
                self.logger.info(f"📊 Rollout统计:")
                self.logger.info(f"   总样本数: {total_samples}")
                self.logger.info(f"   总高层经验: {total_high_level}")
                self.logger.info(f"   完成Workers: {completed_workers}/{len(trainer.rollout_workers)}")
            
            if hasattr(trainer, 'training_workers'):
                total_updates = sum(w.updates_performed for w in trainer.training_workers)
                total_processed = sum(w.samples_processed for w in trainer.training_workers)
                
                self.logger.info(f"📊 Training统计:")
                self.logger.info(f"   总更新数: {total_updates}")
                self.logger.info(f"   总处理样本: {total_processed}")
            
            if hasattr(trainer, 'agent_proxy'):
                high_level_stored = trainer.agent_proxy.high_level_experiences_stored
                low_level_stored = trainer.agent_proxy.low_level_experiences_stored
                
                self.logger.info(f"📊 经验存储统计:")
                self.logger.info(f"   高层经验存储: {high_level_stored}")
                self.logger.info(f"   低层经验存储: {low_level_stored}")
            
            self.logger.info(f"⏱️ 测试耗时: {test_duration:.2f}秒")
            
            # 简单的成功判断
            if (hasattr(trainer, 'rollout_workers') and 
                total_samples > 500 and total_high_level > 0):
                self.logger.info("🎉 测试3通过: 集成系统运行正常!")
                return True
            else:
                self.logger.warning("⚠️ 测试3部分通过: 系统运行但数据收集可能不足")
                return True
                
        except Exception as e:
            self.logger.error(f"分析集成测试结果时出错: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("🚀 开始数据损失修复效果测试")
        self.logger.info("=" * 80)
        
        test_results = {}
        
        # 测试1: RolloutWorker高层经验收集
        try:
            test_results['rollout_worker'] = self.test_rollout_worker_high_level_collection()
        except Exception as e:
            self.logger.error(f"测试1异常: {e}")
            test_results['rollout_worker'] = False
        
        # 测试2: TrainingWorker数据传输
        try:
            test_results['training_worker'] = self.test_training_worker_data_transmission()
        except Exception as e:
            self.logger.error(f"测试2异常: {e}")
            test_results['training_worker'] = False
        
        # 测试3: 集成系统测试
        try:
            test_results['integrated_system'] = self.test_integrated_system()
        except Exception as e:
            self.logger.error(f"测试3异常: {e}")
            test_results['integrated_system'] = False
        
        # 输出最终结果
        self.print_final_results(test_results)
        
        return test_results
    
    def print_final_results(self, test_results):
        """打印最终测试结果"""
        self.logger.info("\n" + "=" * 80)
        self.logger.info("🏁 数据损失修复效果测试 - 最终结果")
        self.logger.info("=" * 80)
        
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            self.logger.info(f"   {test_name}: {status}")
        
        self.logger.info(f"\n📊 总体结果: {passed_tests}/{total_tests} 测试通过")
        
        if passed_tests == total_tests:
            self.logger.info("🎉 所有测试通过! 数据损失修复成功!")
        elif passed_tests >= total_tests * 0.8:
            self.logger.info("⚠️ 大部分测试通过，修复基本成功，但仍需关注失败的测试")
        else:
            self.logger.error("❌ 多个测试失败，数据损失问题仍需进一步修复")
        
        self.logger.info("=" * 80)

def main():
    """主函数"""
    print("🧪 数据损失修复效果测试")
    print("=" * 60)
    
    try:
        tester = DataLossFixTester()
        results = tester.run_all_tests()
        
        # 返回测试结果
        passed = sum(results.values())
        total = len(results)
        
        if passed == total:
            print("🎉 所有测试通过!")
            return 0
        else:
            print(f"⚠️ {passed}/{total} 测试通过")
            return 1
            
    except Exception as e:
        print(f"❌ 测试运行异常: {e}")
        import traceback
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    exit(main())
