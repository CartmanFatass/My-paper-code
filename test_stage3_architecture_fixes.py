#!/usr/bin/env python3
"""
阶段3架构修复和根本性解决方案测试脚本
用于验证确定性步数计数、高层经验收集和数据传输完整性的修复效果
"""

import time
import numpy as np
import threading
import queue
from collections import defaultdict, Counter
from train_rollout_based_threaded import RolloutWorker, AgentProxy, DataBuffer, ThreadSafeCounter
from config import Config
import logging

# 设置简单的日志配置
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockAgent:
    """模拟HMASD Agent，用于测试"""
    def __init__(self, config):
        self.config = config
        self.device = 'cpu'
        self.high_level_buffer = []
        self.low_level_buffer = []
        self.state_skill_dataset = []
        self.steps_collected = 0
        
        # 用于统计的字典
        self.high_level_samples_by_env = defaultdict(int)
        self.high_level_samples_by_reason = defaultdict(int)
        
        # 【阶段3修复】确保配置维度有效 - 更严格的初始化
        self._ensure_config_dimensions(config)
    
    def _ensure_config_dimensions(self, config):
        """确保配置维度有效"""
        # 设置默认维度
        if not hasattr(config, 'state_dim') or config.state_dim is None:
            config.state_dim = 10
        if not hasattr(config, 'obs_dim') or config.obs_dim is None:
            config.obs_dim = 8
        if not hasattr(config, 'action_dim') or config.action_dim is None:
            config.action_dim = 3
        if not hasattr(config, 'n_agents') or config.n_agents is None:
            config.n_agents = 5
        
        # 确保所有维度都是正整数
        config.state_dim = max(1, int(config.state_dim))
        config.obs_dim = max(1, int(config.obs_dim))
        config.action_dim = max(1, int(config.action_dim))
        config.n_agents = max(1, int(config.n_agents))
        
        print(f"MockAgent配置维度: state_dim={config.state_dim}, obs_dim={config.obs_dim}, "
              f"action_dim={config.action_dim}, n_agents={config.n_agents}")
    
    def assign_skills(self, state, observations, deterministic=False):
        """模拟技能分配"""
        team_skill = np.random.randint(0, 3)
        agent_skills = [np.random.randint(0, 3) for _ in range(self.config.n_agents)]
        log_probs = {
            'team_log_prob': -0.5,
            'agent_log_probs': [-0.3] * self.config.n_agents
        }
        return team_skill, agent_skills, log_probs
    
    def select_action(self, observations, agent_skills, deterministic=False, env_id=0):
        """模拟动作选择"""
        n_agents = observations.shape[0] if hasattr(observations, 'shape') else self.config.n_agents
        actions = np.random.randn(n_agents, self.config.action_dim)
        action_logprobs = np.random.randn(n_agents)
        return actions, action_logprobs
    
    def store_high_level_transition(self, state, team_skill, observations, agent_skills, 
                                  accumulated_reward, skill_log_probs, worker_id):
        """【阶段3修复】模拟高层经验存储 - 添加空值检查和安全处理"""
        try:
            # 【阶段3修复】确保所有参数都有有效值 - 更安全的处理
            state = self._safe_copy_or_create(state, (self.config.state_dim,))
            observations = self._safe_copy_or_create(observations, (self.config.n_agents, self.config.obs_dim))
            agent_skills = self._safe_copy_or_create(agent_skills, (self.config.n_agents,), default_value=0, as_list=True)
            
            # 确保数值参数有效
            team_skill = int(team_skill) if team_skill is not None else 0
            accumulated_reward = float(accumulated_reward) if accumulated_reward is not None else 0.0
            worker_id = int(worker_id) if worker_id is not None else 0
            
            # 处理skill_log_probs
            if skill_log_probs is None:
                skill_log_probs = {'reason': '默认'}
            elif not isinstance(skill_log_probs, dict):
                skill_log_probs = {'reason': '转换'}
            else:
                # 安全复制字典
                skill_log_probs = dict(skill_log_probs)
            
            experience = {
                'state': state,
                'team_skill': team_skill,
                'observations': observations,
                'agent_skills': agent_skills,
                'accumulated_reward': accumulated_reward,
                'skill_log_probs': skill_log_probs,
                'worker_id': worker_id
            }
            self.high_level_buffer.append(experience)
            
            # 更新统计
            self.high_level_samples_by_env[worker_id] += 1
            reason = skill_log_probs.get('reason', '未知')
            self.high_level_samples_by_reason[reason] += 1
            
            return True
            
        except Exception as e:
            print(f"MockAgent.store_high_level_transition 错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _safe_copy_or_create(self, data, shape, default_value=0.0, as_list=False):
        """安全地复制或创建数据"""
        try:
            if data is None:
                if as_list:
                    return [default_value] * shape[0]
                else:
                    return np.full(shape, default_value)
            
            # 如果是numpy数组
            if isinstance(data, np.ndarray):
                return data.copy()
            
            # 如果是列表
            if isinstance(data, (list, tuple)):
                if as_list:
                    return list(data)
                else:
                    return np.array(data)
            
            # 如果是标量，扩展为所需形状
            if np.isscalar(data):
                if as_list:
                    return [data] * shape[0]
                else:
                    return np.full(shape, data)
            
            # 尝试转换为numpy数组
            return np.array(data)
            
        except Exception as e:
            print(f"_safe_copy_or_create 错误: {e}, 使用默认值")
            if as_list:
                return [default_value] * shape[0]
            else:
                return np.full(shape, default_value)
    
    def store_low_level_transition(self, state, next_state, observations, next_observations,
                                 actions, rewards, dones, team_skill, agent_skills,
                                 action_logprobs, skill_log_probs, worker_id):
        """模拟低层经验存储"""
        experience = {
            'state': state,
            'next_state': next_state,
            'observations': observations,
            'next_observations': next_observations,
            'actions': actions,
            'rewards': rewards,
            'dones': dones,
            'team_skill': team_skill,
            'agent_skills': agent_skills,
            'action_logprobs': action_logprobs,
            'skill_log_probs': skill_log_probs,
            'worker_id': worker_id
        }
        self.low_level_buffer.append(experience)
        return True
    
    def rollout_update(self):
        """模拟模型更新"""
        time.sleep(0.1)  # 模拟更新耗时
        
        update_info = {
            'coordinator': {'coordinator_loss': 0.01},
            'discoverer': {'discoverer_loss': 0.02}
        }
        
        # 清空缓冲区（模拟PPO on-policy特性）
        self.high_level_buffer.clear()
        self.low_level_buffer.clear()
        
        return update_info

class MockEnvironment:
    """【阶段3修复】模拟环境，用于测试 - 确保维度有效"""
    def __init__(self, config):
        self.config = config
        
        # 【阶段3修复】确保所有维度都有有效值 - 更严格的检查
        self.state_dim = self._safe_get_dim(config, 'state_dim', 10)
        self.obs_dim = self._safe_get_dim(config, 'obs_dim', 8)
        self.n_uavs = self._safe_get_dim(config, 'n_agents', 5)
        self.action_dim = self._safe_get_dim(config, 'action_dim', 3)
        
        self.step_count = 0
        self.max_episode_length = 100
        
        # 【阶段3修复】更新配置以确保一致性
        config.state_dim = self.state_dim
        config.obs_dim = self.obs_dim
        config.n_agents = self.n_uavs
        config.action_dim = self.action_dim
        
        print(f"MockEnvironment初始化: state_dim={self.state_dim}, obs_dim={self.obs_dim}, "
              f"n_uavs={self.n_uavs}, action_dim={self.action_dim}")
    
    def _safe_get_dim(self, config, attr_name, default_value):
        """安全获取维度参数"""
        try:
            if hasattr(config, attr_name):
                value = getattr(config, attr_name)
                if value is not None and value > 0:
                    return int(value)
            return default_value
        except Exception:
            return default_value
    
    def reset(self):
        """【阶段3修复】重置环境 - 确保返回有效数据"""
        self.step_count = 0
        try:
            # 确保维度都是有效的正整数
            if self.n_uavs <= 0 or self.obs_dim <= 0 or self.state_dim <= 0:
                raise ValueError(f"无效维度: n_uavs={self.n_uavs}, obs_dim={self.obs_dim}, state_dim={self.state_dim}")
            
            observations = np.random.randn(self.n_uavs, self.obs_dim)
            info = {'state': np.random.randn(self.state_dim)}
            return observations, info
        except Exception as e:
            print(f"MockEnvironment.reset 错误: {e}, state_dim={self.state_dim}, obs_dim={self.obs_dim}")
            # 返回安全的默认值
            safe_n_uavs = max(1, self.n_uavs)
            safe_obs_dim = max(1, self.obs_dim)
            safe_state_dim = max(1, self.state_dim)
            
            observations = np.zeros((safe_n_uavs, safe_obs_dim))
            info = {'state': np.zeros(safe_state_dim)}
            return observations, info
    
    def step(self, actions):
        """【阶段3修复】环境步骤 - 确保返回有效数据"""
        self.step_count += 1
        
        try:
            # 确保维度都是有效的正整数
            if self.n_uavs <= 0 or self.obs_dim <= 0 or self.state_dim <= 0:
                raise ValueError(f"无效维度: n_uavs={self.n_uavs}, obs_dim={self.obs_dim}, state_dim={self.state_dim}")
            
            next_observations = np.random.randn(self.n_uavs, self.obs_dim)
            rewards = np.random.randn()  # 标量奖励
            terminated = self.step_count >= self.max_episode_length
            truncated = False
            info = {'next_state': np.random.randn(self.state_dim)}
            
            return next_observations, rewards, terminated, truncated, info
            
        except Exception as e:
            print(f"MockEnvironment.step 错误: {e}, state_dim={self.state_dim}, obs_dim={self.obs_dim}")
            # 返回安全的默认值
            safe_n_uavs = max(1, self.n_uavs)
            safe_obs_dim = max(1, self.obs_dim)
            safe_state_dim = max(1, self.state_dim)
            
            next_observations = np.zeros((safe_n_uavs, safe_obs_dim))
            rewards = 0.0
            terminated = True  # 出错时终止episode
            truncated = False
            info = {'next_state': np.zeros(safe_state_dim)}
            
            return next_observations, rewards, terminated, truncated, info
    
    def close(self):
        pass

def test_deterministic_step_counting():
    """测试确定性步数计数"""
    print("🔍 测试阶段3确定性步数计数...")
    
    config = Config()
    config.rollout_length = 128
    config.k = 32
    
    # 创建模拟环境工厂
    def env_factory():
        return MockEnvironment(config)
    
    # 创建数据缓冲区和控制事件
    data_buffer = DataBuffer(maxsize=1000)
    control_events = {'stop': threading.Event(), 'pause': threading.Event()}
    
    # 创建单个worker
    worker = RolloutWorker(
        worker_id=0,
        env_factory=env_factory,
        config=config,
        data_buffer=data_buffer,
        control_events=control_events,
        logger=logger
    )
    
    # 创建模拟代理和代理代理
    mock_agent = MockAgent(config)
    agent_proxy = AgentProxy(mock_agent, config, logger, data_buffer)
    
    # 手动执行128步
    success_count = 0
    for step in range(128):
        success = worker.run_step(agent_proxy)
        if success:
            success_count += 1
    
    # 验证步数计数
    expected_steps = 128
    actual_steps = worker.samples_collected
    expected_high_level = expected_steps // config.k  # 128 // 32 = 4
    actual_high_level = worker.high_level_experiences_generated
    
    print(f"  步数验证: 期望={expected_steps}, 实际={actual_steps}, 匹配={'✅' if actual_steps == expected_steps else '❌'}")
    print(f"  高层经验验证: 期望={expected_high_level}, 实际={actual_high_level}, 匹配={'✅' if actual_high_level == expected_high_level else '❌'}")
    print(f"  成功步数: {success_count}/{128}")
    
    # 测试complete_rollout方法
    worker.complete_rollout()
    
    final_high_level = worker.high_level_experiences_generated
    print(f"  Rollout完成后高层经验: {final_high_level}, 期望={expected_high_level}")
    
    # 验证确定性补齐
    if final_high_level == expected_high_level:
        print("  ✅ 确定性步数计数和高层经验收集正常")
        return True
    else:
        print("  ❌ 确定性步数计数或高层经验收集有问题")
        return False

def test_data_transmission_integrity():
    """测试数据传输完整性"""
    print("\n🔍 测试阶段3数据传输完整性...")
    
    config = Config()
    
    # 【阶段3修复】确保配置维度有效 - 模拟train_rollout_based_threaded.py中的维度获取过程
    if not hasattr(config, 'state_dim') or config.state_dim is None:
        config.state_dim = 10
    if not hasattr(config, 'obs_dim') or config.obs_dim is None:
        config.obs_dim = 8
    if not hasattr(config, 'action_dim') or config.action_dim is None:
        config.action_dim = 3
    if not hasattr(config, 'n_agents') or config.n_agents is None:
        config.n_agents = 5
    
    # 确保所有维度都是正整数
    config.state_dim = max(1, int(config.state_dim))
    config.obs_dim = max(1, int(config.obs_dim))
    config.action_dim = max(1, int(config.action_dim))
    config.n_agents = max(1, int(config.n_agents))
    
    print(f"数据传输测试配置维度: state_dim={config.state_dim}, obs_dim={config.obs_dim}, "
          f"action_dim={config.action_dim}, n_agents={config.n_agents}")
    
    # 创建数据缓冲区
    data_buffer = DataBuffer(maxsize=500)
    
    # 模拟多个worker并发添加数据
    def worker_thread(worker_id, data_count):
        for i in range(data_count):
            try:
                low_level_exp = {
                    'experience_type': 'low_level',
                    'worker_id': worker_id,
                    'state': np.random.randn(config.state_dim),
                    'actions': np.random.randn(config.n_agents, config.action_dim),
                    'rewards': np.random.randn(),
                    'next_state': np.random.randn(config.state_dim),
                    'step_number': i
                }
                
                high_level_exp = {
                    'experience_type': 'high_level',
                    'worker_id': worker_id,
                    'state': np.random.randn(config.state_dim),
                    'team_skill': np.random.randint(0, 3),
                    'accumulated_reward': np.random.randn(),
                    'step_number': i
                }
                
                # 添加数据
                data_buffer.put(low_level_exp, block=True, timeout=5.0)
                if i % 4 == 0:  # 每4步添加一个高层经验
                    data_buffer.put(high_level_exp, block=True, timeout=5.0)
                
                time.sleep(0.001)  # 模拟处理延迟
                
            except Exception as e:
                print(f"Worker {worker_id} 数据生成错误: {e}")
                break
    
    # 启动4个worker线程
    threads = []
    worker_count = 4
    data_per_worker = 32
    
    for worker_id in range(worker_count):
        thread = threading.Thread(target=worker_thread, args=(worker_id, data_per_worker))
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    # 验证数据完整性
    stats = data_buffer.get_stats()
    expected_total = worker_count * data_per_worker + worker_count * (data_per_worker // 4)  # 低层 + 高层
    
    print(f"  数据缓冲区统计:")
    print(f"    总添加: {stats['total_added']}")
    print(f"    高优先级添加: {stats['high_priority_added']}")
    print(f"    普通优先级添加: {stats['normal_priority_added']}")
    print(f"    队列大小: {stats['queue_size']}")
    print(f"    处理速度: {stats['processing_speed']:.2f} 项/秒")
    print(f"    拥塞检测: {stats['congestion_detected']}")
    print(f"    校验错误: {stats['checksum_errors']}")
    
    # 消费所有数据
    consumed_high = 0
    consumed_normal = 0
    consumed_total = 0
    
    while not data_buffer.empty():
        item = data_buffer.get(timeout=1.0)
        if item:
            consumed_total += 1
            if item.get('experience_type') == 'high_level':
                consumed_high += 1
            else:
                consumed_normal += 1
    
    print(f"  消费统计:")
    print(f"    总消费: {consumed_total}")
    print(f"    高层消费: {consumed_high}")
    print(f"    普通消费: {consumed_normal}")
    
    # 验证优先级处理
    expected_high = worker_count * (data_per_worker // 4)
    expected_normal = worker_count * data_per_worker
    
    high_priority_correct = consumed_high == expected_high
    normal_priority_correct = consumed_normal == expected_normal
    
    print(f"  验证结果:")
    print(f"    高层经验: {consumed_high}/{expected_high} {'✅' if high_priority_correct else '❌'}")
    print(f"    低层经验: {consumed_normal}/{expected_normal} {'✅' if normal_priority_correct else '❌'}")
    
    return high_priority_correct and normal_priority_correct

def test_multi_worker_coordination():
    """测试多worker协调"""
    print("\n🔍 测试阶段3多worker协调...")
    
    config = Config()
    config.rollout_length = 64  # 减小测试规模
    config.k = 16
    
    # 创建多个worker模拟
    worker_count = 4
    workers = []
    data_buffer = DataBuffer(maxsize=2000)
    control_events = {'stop': threading.Event(), 'pause': threading.Event()}
    
    def env_factory():
        return MockEnvironment(config)
    
    for i in range(worker_count):
        worker = RolloutWorker(
            worker_id=i,
            env_factory=env_factory,
            config=config,
            data_buffer=data_buffer,
            control_events=control_events,
            logger=logger
        )
        workers.append(worker)
    
    # 创建模拟代理
    mock_agent = MockAgent(config)
    agent_proxy = AgentProxy(mock_agent, config, logger, data_buffer)
    agent_proxy.rollout_workers = workers  # 设置引用
    
    # 模拟每个worker执行rollout
    def worker_rollout(worker, agent_proxy):
        for step in range(config.rollout_length):
            worker.run_step(agent_proxy)
        worker.complete_rollout()
    
    # 启动所有worker线程
    threads = []
    for worker in workers:
        thread = threading.Thread(target=worker_rollout, args=(worker, agent_proxy))
        threads.append(thread)
        thread.start()
    
    # 等待所有worker完成
    for thread in threads:
        thread.join()
    
    # 验证结果
    total_steps = sum(worker.samples_collected for worker in workers)
    total_high_level = sum(worker.high_level_experiences_generated for worker in workers)
    expected_total_steps = worker_count * config.rollout_length
    expected_total_high_level = worker_count * (config.rollout_length // config.k)
    
    print(f"  多worker协调结果:")
    print(f"    总步数: {total_steps}/{expected_total_steps} {'✅' if total_steps == expected_total_steps else '❌'}")
    print(f"    总高层经验: {total_high_level}/{expected_total_high_level} {'✅' if total_high_level == expected_total_high_level else '❌'}")
    
    # 检查每个worker的贡献
    worker_stats = []
    for worker in workers:
        expected_worker_high_level = config.rollout_length // config.k
        worker_stats.append({
            'worker_id': worker.worker_id,
            'steps': worker.samples_collected,
            'high_level': worker.high_level_experiences_generated,
            'expected_steps': config.rollout_length,
            'expected_high_level': expected_worker_high_level,
            'steps_correct': worker.samples_collected == config.rollout_length,
            'high_level_correct': worker.high_level_experiences_generated == expected_worker_high_level
        })
    
    print(f"  单个worker详情:")
    all_correct = True
    for stats in worker_stats:
        steps_status = '✅' if stats['steps_correct'] else '❌'
        high_level_status = '✅' if stats['high_level_correct'] else '❌'
        print(f"    Worker {stats['worker_id']}: 步数={stats['steps']}/{stats['expected_steps']} {steps_status}, "
              f"高层={stats['high_level']}/{stats['expected_high_level']} {high_level_status}")
        all_correct = all_correct and stats['steps_correct'] and stats['high_level_correct']
    
    return all_correct and total_steps == expected_total_steps and total_high_level == expected_total_high_level

def test_edge_cases():
    """测试边界情况"""
    print("\n🔍 测试阶段3边界情况...")
    
    config = Config()
    
    # 测试1: 非整除的步数和k值
    config.rollout_length = 100  # 不能被32整除
    config.k = 32
    
    data_buffer = DataBuffer(maxsize=1000)
    control_events = {'stop': threading.Event(), 'pause': threading.Event()}
    
    def env_factory():
        return MockEnvironment(config)
    
    worker = RolloutWorker(
        worker_id=0,
        env_factory=env_factory,
        config=config,
        data_buffer=data_buffer,
        control_events=control_events,
        logger=logger
    )
    
    mock_agent = MockAgent(config)
    agent_proxy = AgentProxy(mock_agent, config, logger, data_buffer)
    
    # 执行100步
    for step in range(100):
        worker.run_step(agent_proxy)
    
    worker.complete_rollout()
    
    expected_high_level = 100 // 32  # 3个高层经验
    actual_high_level = worker.high_level_experiences_generated
    
    print(f"  边界情况1 (100步, k=32):")
    print(f"    期望高层经验: {expected_high_level}")
    print(f"    实际高层经验: {actual_high_level}")
    print(f"    结果: {'✅' if actual_high_level == expected_high_level else '❌'}")
    
    # 测试2: 极小的rollout长度
    config.rollout_length = 16
    config.k = 32  # k > rollout_length
    
    worker2 = RolloutWorker(
        worker_id=1,
        env_factory=env_factory,
        config=config,
        data_buffer=data_buffer,
        control_events=control_events,
        logger=logger
    )
    
    for step in range(16):
        worker2.run_step(agent_proxy)
    
    worker2.complete_rollout()
    
    expected_high_level_2 = 16 // 32  # 0个高层经验
    actual_high_level_2 = worker2.high_level_experiences_generated
    
    print(f"  边界情况2 (16步, k=32):")
    print(f"    期望高层经验: {expected_high_level_2}")
    print(f"    实际高层经验: {actual_high_level_2}")
    print(f"    结果: {'✅' if actual_high_level_2 == expected_high_level_2 else '❌'}")
    
    return (actual_high_level == expected_high_level and 
            actual_high_level_2 == expected_high_level_2)

def test_enhanced_data_transmission_wait():
    """测试增强的数据传输等待功能"""
    print("\n🔍 测试阶段3增强数据传输等待...")
    
    config = Config()
    data_buffer = DataBuffer(maxsize=1000)
    control_events = {'stop': threading.Event(), 'pause': threading.Event()}
    
    def env_factory():
        return MockEnvironment(config)
    
    worker = RolloutWorker(
        worker_id=0,
        env_factory=env_factory,
        config=config,
        data_buffer=data_buffer,
        control_events=control_events,
        logger=logger
    )
    
    # 测试情况1: 空队列等待
    start_time = time.time()
    worker.wait_for_data_transmission_complete()
    wait_time_empty = time.time() - start_time
    
    print(f"  空队列等待时间: {wait_time_empty:.3f}s {'✅' if wait_time_empty < 1.0 else '❌'}")
    
    # 测试情况2: 有数据的队列等待
    # 添加一些数据到队列
    for i in range(50):
        data = {
            'experience_type': 'low_level',
            'worker_id': 0,
            'data': f'test_data_{i}'
        }
        data_buffer.put(data)
    
    # 启动消费者线程
    def consumer():
        time.sleep(0.5)  # 延迟开始消费
        while not data_buffer.empty():
            data_buffer.get(timeout=0.1)
            time.sleep(0.01)  # 模拟处理时间
    
    consumer_thread = threading.Thread(target=consumer)
    consumer_thread.start()
    
    start_time = time.time()
    worker.wait_for_data_transmission_complete()
    wait_time_with_data = time.time() - start_time
    
    consumer_thread.join()
    
    print(f"  有数据队列等待时间: {wait_time_with_data:.3f}s")
    print(f"  队列最终状态: {'空' if data_buffer.empty() else '非空'} {'✅' if data_buffer.empty() else '❌'}")
    
    return wait_time_empty < 1.0 and data_buffer.empty()

def main():
    """运行所有阶段3测试"""
    print("🚀 阶段3架构修复和根本性解决方案测试")
    print("=" * 60)
    
    tests = [
        ("确定性步数计数", test_deterministic_step_counting),
        ("数据传输完整性", test_data_transmission_integrity),
        ("多worker协调", test_multi_worker_coordination),
        ("边界情况处理", test_edge_cases),
        ("增强数据传输等待", test_enhanced_data_transmission_wait),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ 通过" if result else "❌ 失败"
            print(f"\n{test_name}: {status}")
        except Exception as e:
            print(f"\n{test_name}: ❌ 异常 - {e}")
            results[test_name] = False
    
    print("\n" + "="*60)
    print("📊 阶段3测试总结:")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
    
    print(f"\n总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有阶段3修复测试通过！")
        print("\n🎯 阶段3修复效果:")
        print("- ✅ 确定性步数计数: 确保每个worker准确收集目标步数")
        print("- ✅ 高层经验收集: 严格按k步生成，确保数据量准确")
        print("- ✅ 数据传输完整性: 100%确保数据不丢失")
        print("- ✅ 多worker协调: 所有worker同步完成rollout")
        print("- ✅ 边界情况处理: 正确处理各种边界条件")
        print("- ✅ 增强传输等待: 确保数据传输100%完成")
    else:
        print(f"⚠️ 还有 {total - passed} 个测试失败，需要进一步修复")
    
    return passed == total

if __name__ == "__main__":
    main()
