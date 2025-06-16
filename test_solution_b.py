#!/usr/bin/env python3
"""
测试方案B：基于计数器的验证机制
验证修改后的should_update()方法是否能正确工作
"""

import sys
import os
import time
import numpy as np
import torch
from unittest.mock import Mock, MagicMock

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from train_rollout_based_threaded import AgentProxy, RolloutWorker

def test_solution_b():
    """测试方案B的核心功能"""
    print("🧪 测试方案B：基于计数器的验证机制")
    print("=" * 50)
    
    # 创建配置
    config = Config()
    config.rollout_length = 128  # 每个worker的目标步数
    config.k = 32  # 技能周期长度
    config.batch_size = 4096  # 目标总步数
    
    # 创建模拟的logger
    logger = Mock()
    logger.info = lambda x: print(f"[INFO] {x}")
    logger.warning = lambda x: print(f"[WARNING] {x}")
    logger.debug = lambda x: print(f"[DEBUG] {x}")
    logger.error = lambda x: print(f"[ERROR] {x}")
    
    # 创建模拟的agent
    mock_agent = Mock()
    mock_agent.low_level_buffer = []
    mock_agent.high_level_buffer = []
    mock_agent.steps_collected = 0
    
    # 创建AgentProxy
    agent_proxy = AgentProxy(mock_agent, config, logger)
    
    # 创建模拟的rollout workers
    num_workers = 32
    rollout_workers = []
    
    for i in range(num_workers):
        worker = Mock()
        worker.worker_id = i
        worker.samples_collected = 0
        worker.rollout_completed = False
        worker.target_rollout_steps = config.rollout_length
        worker.high_level_experiences_generated = 0
        rollout_workers.append(worker)
    
    # 设置AgentProxy的rollout_workers引用
    agent_proxy.rollout_workers = rollout_workers
    
    print(f"✅ 初始化完成: {num_workers} 个workers, 目标步数={config.rollout_length * num_workers}")
    
    # 测试场景1：数据收集未完成
    print("\n📊 测试场景1：数据收集未完成")
    for i, worker in enumerate(rollout_workers):
        worker.samples_collected = 100  # 未达到目标128
        worker.rollout_completed = False
        worker.high_level_experiences_generated = 100 // config.k  # 3个高层经验
    
    should_update = agent_proxy.should_update()
    print(f"结果: should_update = {should_update} (期望: False)")
    assert not should_update, "数据收集未完成时不应该更新"
    
    # 测试场景2：部分workers完成
    print("\n📊 测试场景2：部分workers完成")
    for i, worker in enumerate(rollout_workers):
        if i < 16:  # 前16个worker完成
            worker.samples_collected = config.rollout_length
            worker.rollout_completed = True
            worker.high_level_experiences_generated = config.rollout_length // config.k
        else:  # 后16个worker未完成
            worker.samples_collected = 100
            worker.rollout_completed = False
            worker.high_level_experiences_generated = 100 // config.k
    
    should_update = agent_proxy.should_update()
    print(f"结果: should_update = {should_update} (期望: False)")
    assert not should_update, "部分workers未完成时不应该更新"
    
    # 测试场景3：所有workers完成，数据充足
    print("\n📊 测试场景3：所有workers完成，数据充足")
    for i, worker in enumerate(rollout_workers):
        worker.samples_collected = config.rollout_length  # 128步
        worker.rollout_completed = True
        worker.high_level_experiences_generated = config.rollout_length // config.k  # 4个高层经验
    
    should_update = agent_proxy.should_update()
    print(f"结果: should_update = {should_update} (期望: True)")
    assert should_update, "所有workers完成且数据充足时应该更新"
    
    # 测试场景4：缓冲区溢出保护
    print("\n📊 测试场景4：缓冲区溢出保护")
    # 重置workers为未完成状态
    for i, worker in enumerate(rollout_workers):
        worker.samples_collected = 100
        worker.rollout_completed = False
        worker.high_level_experiences_generated = 100 // config.k
    
    # 模拟缓冲区溢出
    mock_agent.low_level_buffer = [None] * int(config.batch_size * 2)  # 超过阈值
    
    should_update = agent_proxy.should_update()
    print(f"结果: should_update = {should_update} (期望: True)")
    assert should_update, "缓冲区溢出时应该触发保护机制"
    
    # 测试场景5：验证计数器同步
    print("\n📊 测试场景5：验证计数器同步")
    # 重置缓冲区
    mock_agent.low_level_buffer = []
    
    # 设置完成状态
    total_collected = 0
    for i, worker in enumerate(rollout_workers):
        worker.samples_collected = config.rollout_length
        worker.rollout_completed = True
        worker.high_level_experiences_generated = config.rollout_length // config.k
        total_collected += worker.samples_collected
    
    # 调用同步方法
    agent_proxy._sync_step_counters(total_collected)
    
    print(f"同步后: agent.steps_collected = {mock_agent.steps_collected}")
    print(f"同步后: global_rollout_steps = {agent_proxy.global_rollout_steps}")
    assert mock_agent.steps_collected == total_collected, "agent步数计数器同步失败"
    assert agent_proxy.global_rollout_steps == total_collected, "全局步数计数器同步失败"
    
    print("\n✅ 所有测试通过！方案B实现正确。")
    
    # 性能测试
    print("\n⚡ 性能测试：验证方案B的效率")
    start_time = time.time()
    
    # 执行1000次should_update检查
    for _ in range(1000):
        agent_proxy.should_update()
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 1000 * 1000  # 转换为毫秒
    
    print(f"平均检查时间: {avg_time:.3f} 毫秒")
    print(f"每秒可检查次数: {1000 / (end_time - start_time):.0f}")
    
    if avg_time < 1.0:  # 小于1毫秒
        print("✅ 性能测试通过：检查速度足够快")
    else:
        print("⚠️ 性能警告：检查速度可能需要优化")
    
    print("\n🎉 方案B测试完成！")

if __name__ == "__main__":
    test_solution_b()
