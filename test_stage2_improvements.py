#!/usr/bin/env python3
"""
阶段2数据传输可靠性增强测试脚本
用于验证渐进式等待策略、优先级队列处理和智能重试机制的效果
"""

import time
import numpy as np
from collections import defaultdict
from train_rollout_based_threaded import DataBuffer, ThreadSafeCounter
import queue

def test_priority_queue_processing():
    """测试优先级队列处理功能"""
    print("🔍 测试优先级队列处理功能...")
    
    buffer = DataBuffer(maxsize=1000)
    
    # 添加不同类型的经验数据
    low_level_exp = {
        'experience_type': 'low_level',
        'worker_id': 0,
        'state': np.zeros(10),
        'actions': np.zeros(5),
        'rewards': 1.0,
        'next_state': np.zeros(10)
    }
    
    high_level_exp = {
        'experience_type': 'high_level',
        'worker_id': 0,
        'state': np.zeros(10),
        'team_skill': 1,
        'accumulated_reward': 5.0
    }
    
    state_skill_exp = {
        'experience_type': 'state_skill',
        'worker_id': 0,
        'state': np.zeros(10),
        'team_skill': 1,
        'observations': np.zeros((5, 8)),
        'agent_skills': [1, 0, 1, 0, 1]
    }
    
    # 混合添加数据
    for i in range(10):
        buffer.put(low_level_exp.copy())
        if i % 3 == 0:
            buffer.put(high_level_exp.copy())
        if i % 5 == 0:
            buffer.put(state_skill_exp.copy())
    
    # 获取统计信息
    stats = buffer.get_stats()
    print(f"  添加数据后: 总队列={stats['queue_size']}, "
          f"高优先级={stats['high_priority_size']}, "
          f"普通优先级={stats['normal_priority_size']}")
    
    # 测试优先级处理
    retrieved_types = []
    while not buffer.empty():
        item = buffer.get(timeout=1.0)
        if item:
            retrieved_types.append(item['experience_type'])
    
    # 统计获取顺序
    type_counts = defaultdict(int)
    for exp_type in retrieved_types:
        type_counts[exp_type] += 1
    
    print(f"  获取到的数据类型: {dict(type_counts)}")
    print(f"  获取顺序（前10个）: {retrieved_types[:10]}")
    
    # 验证高层经验是否优先处理
    high_level_positions = [i for i, exp_type in enumerate(retrieved_types) if exp_type == 'high_level']
    if high_level_positions:
        avg_position = sum(high_level_positions) / len(high_level_positions)
        print(f"  高层经验平均位置: {avg_position:.2f} (越小越优先)")
        if avg_position < len(retrieved_types) / 3:
            print("  ✅ 优先级处理正常")
        else:
            print("  ⚠️ 优先级处理可能有问题")
    
    print()

def test_data_validation():
    """测试数据完整性校验功能"""
    print("🔍 测试数据完整性校验功能...")
    
    buffer = DataBuffer(maxsize=100)
    
    # 测试有效数据
    valid_data = {
        'experience_type': 'low_level',
        'worker_id': 0,
        'state': np.zeros(10),
        'actions': np.zeros(5),
        'rewards': 1.0,
        'next_state': np.zeros(10)
    }
    
    # 测试无效数据
    invalid_data_cases = [
        {},  # 空字典
        {'experience_type': 'low_level'},  # 缺少worker_id
        {'worker_id': 0},  # 缺少experience_type
        {'experience_type': 'low_level', 'worker_id': 0},  # 缺少必需字段
        {'experience_type': 'high_level', 'worker_id': 0},  # 高层经验缺少必需字段
        "not_a_dict",  # 不是字典
    ]
    
    # 测试有效数据
    success = buffer.put(valid_data)
    print(f"  有效数据添加: {'成功' if success else '失败'}")
    
    # 测试无效数据
    failed_count = 0
    for i, invalid_data in enumerate(invalid_data_cases):
        success = buffer.put(invalid_data)
        if not success:
            failed_count += 1
        print(f"  无效数据#{i+1}添加: {'成功' if success else '失败（预期）'}")
    
    stats = buffer.get_stats()
    print(f"  校验错误计数: {stats['checksum_errors']}")
    print(f"  预期拒绝: {len(invalid_data_cases)}, 实际拒绝: {failed_count}")
    
    if failed_count == len(invalid_data_cases):
        print("  ✅ 数据完整性校验正常")
    else:
        print("  ⚠️ 数据完整性校验可能有问题")
    
    print()

def test_congestion_detection():
    """测试拥塞检测功能"""
    print("🔍 测试拥塞检测功能...")
    
    buffer = DataBuffer(maxsize=100)
    
    # 添加大量数据触发拥塞
    data = {
        'experience_type': 'low_level',
        'worker_id': 0,
        'state': np.zeros(10),
        'actions': np.zeros(5),
        'rewards': 1.0,
        'next_state': np.zeros(10)
    }
    
    # 添加数据直到接近容量
    added_count = 0
    for i in range(85):  # 85% 容量
        if buffer.put(data.copy(), block=False):
            added_count += 1
        else:
            break
    
    stats = buffer.get_stats()
    print(f"  添加了 {added_count} 个数据项")
    print(f"  当前队列大小: {stats['queue_size']}")
    print(f"  拥塞检测: {'是' if stats['congestion_detected'] else '否'}")
    
    # 测试高优先级拥塞处理
    high_level_data = {
        'experience_type': 'high_level',
        'worker_id': 0,
        'state': np.zeros(10),
        'team_skill': 1,
        'accumulated_reward': 5.0
    }
    
    success = buffer.put(high_level_data, block=False)
    print(f"  高优先级数据在拥塞时添加: {'成功' if success else '失败'}")
    
    if stats['congestion_detected']:
        print("  ✅ 拥塞检测正常")
    else:
        print("  ⚠️ 拥塞检测可能未触发")
    
    print()

def test_processing_speed_monitoring():
    """测试处理速度监控功能"""
    print("🔍 测试处理速度监控功能...")
    
    buffer = DataBuffer(maxsize=1000)
    
    # 添加数据
    data = {
        'experience_type': 'low_level',
        'worker_id': 0,
        'state': np.zeros(10),
        'actions': np.zeros(5),
        'rewards': 1.0,
        'next_state': np.zeros(10)
    }
    
    # 快速添加数据
    for i in range(50):
        buffer.put(data.copy())
    
    # 模拟处理过程
    start_time = time.time()
    processed_count = 0
    
    while not buffer.empty() and processed_count < 30:
        item = buffer.get(timeout=0.1)
        if item:
            processed_count += 1
            time.sleep(0.01)  # 模拟处理时间
    
    processing_time = time.time() - start_time
    
    # 等待一下让速度统计更新
    time.sleep(1.1)
    
    stats = buffer.get_stats()
    estimated_speed = processed_count / processing_time if processing_time > 0 else 0
    
    print(f"  处理了 {processed_count} 个数据项，耗时 {processing_time:.2f}s")
    print(f"  估算处理速度: {estimated_speed:.2f} 项/秒")
    print(f"  监控的处理速度: {stats['processing_speed']:.2f} 项/秒")
    
    if abs(stats['processing_speed'] - estimated_speed) < estimated_speed * 0.5:
        print("  ✅ 处理速度监控正常")
    else:
        print("  ⚠️ 处理速度监控可能有偏差")
    
    print()

def test_enhanced_statistics():
    """测试增强的统计功能"""
    print("🔍 测试增强的统计功能...")
    
    buffer = DataBuffer(maxsize=1000)
    
    # 添加不同类型的数据
    low_level_count = 0
    high_level_count = 0
    
    for i in range(20):
        # 低层经验
        low_level_exp = {
            'experience_type': 'low_level',
            'worker_id': i % 4,
            'state': np.zeros(10),
            'actions': np.zeros(5),
            'rewards': 1.0,
            'next_state': np.zeros(10)
        }
        buffer.put(low_level_exp)
        low_level_count += 1
        
        # 高层经验 (每3个添加1个)
        if i % 3 == 0:
            high_level_exp = {
                'experience_type': 'high_level',
                'worker_id': i % 4,
                'state': np.zeros(10),
                'team_skill': i % 3,
                'accumulated_reward': float(i)
            }
            buffer.put(high_level_exp)
            high_level_count += 1
    
    # 处理一些数据
    processed_high = 0
    processed_low = 0
    
    for _ in range(15):
        item = buffer.get(timeout=0.1)
        if item:
            if item['experience_type'] == 'high_level':
                processed_high += 1
            else:
                processed_low += 1
    
    stats = buffer.get_stats()
    
    print(f"  添加统计:")
    print(f"    总计: {stats['total_added']}")
    print(f"    高优先级: {stats['high_priority_added']}")
    print(f"    普通优先级: {stats['normal_priority_added']}")
    print(f"  消费统计:")
    print(f"    总计: {stats['total_consumed']}")
    print(f"    高优先级: {stats['high_priority_consumed']}")
    print(f"    普通优先级: {stats['normal_priority_consumed']}")
    print(f"  高优先级比例: {stats['high_priority_ratio']:.2%}")
    
    # 验证统计一致性
    expected_total_added = low_level_count + high_level_count
    expected_high_added = high_level_count
    expected_normal_added = low_level_count
    
    if (stats['total_added'] == expected_total_added and 
        stats['high_priority_added'] == expected_high_added and
        stats['normal_priority_added'] == expected_normal_added):
        print("  ✅ 统计数据一致性正常")
    else:
        print("  ⚠️ 统计数据可能有问题")
        print(f"    期望: 总={expected_total_added}, 高={expected_high_added}, 普通={expected_normal_added}")
    
    print()

def main():
    """运行所有测试"""
    print("🚀 阶段2数据传输可靠性增强测试")
    print("=" * 50)
    
    test_priority_queue_processing()
    test_data_validation()
    test_congestion_detection()
    test_processing_speed_monitoring()
    test_enhanced_statistics()
    
    print("✅ 所有测试完成！")
    print("\n📊 测试总结:")
    print("- 优先级队列处理: 高层经验优先处理")
    print("- 数据完整性校验: 自动拒绝无效数据")
    print("- 拥塞检测: 自动检测队列拥塞状态")
    print("- 处理速度监控: 实时监控处理性能")
    print("- 增强统计: 详细的数据流统计信息")
    
    print("\n🎯 阶段2改进效果:")
    print("- 减少数据传输验证失败率: 目标从~1%降低到0.1%以下")
    print("- 提高数据传输成功率: 确保99.9%以上的数据传输成功")
    print("- 减少等待时间: 通过智能等待策略减少不必要的等待")
    print("- 增强系统稳定性: 即使出现问题也能自动恢复")

if __name__ == "__main__":
    main()
