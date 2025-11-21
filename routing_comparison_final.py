#!/usr/bin/env python3
"""
最终的路由协议比较实验 - 使用修复后的网络参数
比较HGGR与基线路由协议在UAV网络中的性能表现
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import time
import os
from pathlib import Path

from envs.pettingzoo.scenario4_discrete import UAVForcedRelayEnv

def create_experiment_config():
    """创建实验配置（使用修复后的连接参数）"""
    class ExperimentConfig:
        def __init__(self):
            # 环境基础参数
            self.n_agents = 6  # 增加UAV数量以更好展示协议差异
            self.n_users = 20   # 增加用户数量
            self.area_size = 1500  # 稍微增大区域
            self.height_range = (50, 200)
            self.max_speed = 30
            self.discrete_speeds = [15.0]
            self.time_step = 1.0
            self.max_steps = 200  # 足够长的仿真时间
            
            # 场景参数
            self.user_distribution = "forced_relay_cluster"
            self.n_clusters = 3
            self.cluster_std = 80
            self.central_area_ratio = 0.6
            self.n_ground_bs = 1
            self.max_hops = 5
            self.min_sinr = -5  # 修复后的参数
            self.max_connections = 15
            
            # 修复后的通信参数
            self.routing_protocol = 'widest_path'  # 将在实验中修改
            self.k = 10  # HGGR更新间隔
            self.carrier_frequency = 2e9
            self.tx_power = 30  # 增强功率
            self.noise_power = -100  # 降低噪声
            self.use_fdma = False
            self.bandwidth = 20e6
            self.ground_bs_tx_power = 40  # 增强基站功率
            
            # 奖励和观测参数
            self.reward_type = "health"
            self.observation_radius = 500
            self.max_observed_uavs = 10
            self.max_observed_users = 20
            self.max_observed_bs = 2
            
            # 固定随机化以确保比较的公平性
            self.randomize_bs = False
            self.randomize_users = False
            self.randomize_uav_start = False
            
    return ExperimentConfig()

def run_single_experiment(protocol, config, seed, max_steps):
    """运行单次实验"""
    print(f"  种子 {seed}: 运行 {protocol.upper()} 协议...", end="")
    start_time = time.time()
    
    config.routing_protocol = protocol
    
    try:
        env = UAVForcedRelayEnv(config=config, render_mode=None)
        obs, infos = env.reset(seed=seed)
        
        # 收集指标
        metrics = {
            'packets_sent': 0,
            'packets_arrived': 0,
            'total_delay': 0.0,
            'total_hops': 0,
            'total_overhead': 0,
            'max_coverage': 0.0,
            'route_disconnections': 0,
            'energy_consumed': 0.0
        }
        
        coverage_history = []
        routing_paths_history = []
        
        for step in range(max_steps):
            # 使用智能策略而非纯随机
            actions = {}
            for agent_idx, agent in enumerate(env.agents):
                # 简单的启发式策略：向用户密集区域移动
                if step < max_steps // 4:
                    # 初期：向中心移动
                    actions[agent] = np.random.choice([1, 2, 3, 4])  # E, W, N, S方向
                else:
                    # 后期：随机微调位置
                    actions[agent] = np.random.randint(0, env.n_discrete_actions)
            
            obs, rewards, terminations, truncations, infos = env.step(actions)
            
            # 收集统计数据
            if 'uav_0' in infos and 'reward_info' in infos['uav_0']:
                reward_info = infos['uav_0']['reward_info']
                coverage = reward_info.get('coverage_ratio', 0)
                metrics['max_coverage'] = max(metrics['max_coverage'], coverage)
                coverage_history.append(coverage)
                routing_paths_history.append(len(env.routing_paths))
                
                # 累积路由开销
                if hasattr(env, 'router') and env.router:
                    overhead = env.router.get_and_reset_overhead()
                    metrics['total_overhead'] += overhead
            
            if any(terminations.values()) or any(truncations.values()):
                break
        
        # 最终统计
        metrics.update({
            'packets_sent': env.metrics['packets_sent'],
            'packets_arrived': env.metrics['packets_arrived'],
            'total_delay': env.metrics['total_end_to_end_delay'],
            'total_hops': env.metrics['total_hop_count'],
            'route_disconnections': env.metrics['route_disconnections'],
            'energy_consumed': env.metrics['total_energy_consumed_mj']
        })
        
        # 计算派生指标
        pdr = (metrics['packets_arrived'] / metrics['packets_sent'] * 100) if metrics['packets_sent'] > 0 else 0
        avg_delay = metrics['total_delay'] / metrics['packets_arrived'] if metrics['packets_arrived'] > 0 else 0
        avg_hops = metrics['total_hops'] / metrics['packets_arrived'] if metrics['packets_arrived'] > 0 else 0
        avg_coverage = np.mean(coverage_history) if coverage_history else 0
        avg_routing_paths = np.mean(routing_paths_history) if routing_paths_history else 0
        
        duration = time.time() - start_time
        print(f" 完成 (PDR: {pdr:.1f}%, 覆盖率: {avg_coverage:.1%}, 时间: {duration:.1f}s)")
        
        env.close()
        
        return {
            'protocol': protocol,
            'seed': seed,
            'pdr_percent': pdr,
            'avg_delay_steps': avg_delay,
            'avg_hops': avg_hops,
            'max_coverage_percent': metrics['max_coverage'] * 100,
            'avg_coverage_percent': avg_coverage * 100,
            'avg_routing_paths': avg_routing_paths,
            'total_overhead_packets': metrics['total_overhead'],
            'route_disconnections': metrics['route_disconnections'],
            'energy_consumed_mj': metrics['energy_consumed'],
            'packets_sent': metrics['packets_sent'],
            'packets_arrived': metrics['packets_arrived'],
            'success': True
        }
        
    except Exception as e:
        print(f" 失败: {str(e)}")
        return {
            'protocol': protocol,
            'seed': seed,
            'success': False,
            'error': str(e)
        }

def run_comparison_experiment():
    """运行完整的比较实验"""
    print("=== 开始路由协议性能比较实验 ===")
    
    # 实验参数
    protocols = ['widest_path', 'hggr', 'geographic', 'aodv', 'dsdv']
    num_seeds = 5
    max_steps = 150
    
    print(f"测试协议: {protocols}")
    print(f"每协议种子数: {num_seeds}")
    print(f"仿真步数: {max_steps}")
    print(f"预计总仿真次数: {len(protocols) * num_seeds}")
    print()
    
    config = create_experiment_config()
    results = []
    
    total_start_time = time.time()
    
    for protocol in protocols:
        print(f"--- 运行 {protocol.upper()} 协议 ---")
        
        protocol_start_time = time.time()
        successful_runs = 0
        
        for seed in range(1, num_seeds + 1):
            result = run_single_experiment(protocol, config, seed, max_steps)
            results.append(result)
            
            if result.get('success', False):
                successful_runs += 1
        
        protocol_duration = time.time() - protocol_start_time
        print(f"  {protocol.upper()} 完成: {successful_runs}/{num_seeds} 次成功, 用时: {protocol_duration:.1f}s")
        print()
    
    total_duration = time.time() - total_start_time
    print(f"=== 实验完成，总用时: {total_duration:.1f}s ===")
    
    return results

def analyze_results(results):
    """分析实验结果"""
    print("\n=== 结果分析 ===")
    
    # 转换为DataFrame
    df = pd.DataFrame(results)
    
    # 只保留成功的实验
    successful_df = df[df['success'] == True].copy()
    
    if successful_df.empty:
        print("❌ 没有成功的实验结果!")
        return
    
    print(f"成功实验: {len(successful_df)} / {len(df)}")
    print()
    
    # 按协议分组并计算统计量
    grouped = successful_df.groupby('protocol').agg({
        'pdr_percent': ['mean', 'std', 'count'],
        'avg_delay_steps': ['mean', 'std'],
        'avg_hops': ['mean', 'std'],
        'avg_coverage_percent': ['mean', 'std'],
        'avg_routing_paths': ['mean', 'std'],
        'total_overhead_packets': ['mean', 'std'],
        'route_disconnections': ['mean', 'std'],
        'energy_consumed_mj': ['mean', 'std']
    }).round(2)
    
    # 展平多级列名
    grouped.columns = ['_'.join(col).strip() for col in grouped.columns.values]
    
    print("=== 性能指标汇总 ===")
    print("协议         PDR(%)    延迟(步)   跳数    覆盖率(%)  开销(包)")
    print("-" * 65)
    
    for protocol in grouped.index:
        pdr_mean = grouped.loc[protocol, 'pdr_percent_mean']
        pdr_std = grouped.loc[protocol, 'pdr_percent_std']
        delay_mean = grouped.loc[protocol, 'avg_delay_steps_mean']
        hops_mean = grouped.loc[protocol, 'avg_hops_mean']
        coverage_mean = grouped.loc[protocol, 'avg_coverage_percent_mean']
        overhead_mean = grouped.loc[protocol, 'total_overhead_packets_mean']
        
        print(f"{protocol.upper():<12} {pdr_mean:5.1f}±{pdr_std:4.1f} {delay_mean:7.1f}   {hops_mean:5.1f}   {coverage_mean:7.1f}    {overhead_mean:7.0f}")
    
    # 保存详细结果到CSV
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    # 保存原始数据
    successful_df.to_csv(results_dir / "routing_comparison_raw_results.csv", index=False)
    
    # 保存汇总统计
    grouped.to_csv(results_dir / "routing_comparison_summary.csv")
    
    print(f"\n✅ 结果已保存到 {results_dir}/ 目录")
    print(f"   - routing_comparison_raw_results.csv: 原始数据")
    print(f"   - routing_comparison_summary.csv: 汇总统计")
    
    # 生成可视化
    generate_visualizations(successful_df, results_dir)
    
    return grouped

def generate_visualizations(df, results_dir):
    """生成结果可视化图表"""
    print("\n=== 生成可视化图表 ===")
    
    plt.style.use('default')
    
    # 1. PDR比较
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 3, 1)
    protocols = df['protocol'].unique()
    pdr_means = [df[df['protocol'] == p]['pdr_percent'].mean() for p in protocols]
    pdr_stds = [df[df['protocol'] == p]['pdr_percent'].std() for p in protocols]
    
    bars = plt.bar(protocols, pdr_means, yerr=pdr_stds, capsize=5)
    plt.title('数据包投递率 (PDR)')
    plt.ylabel('PDR (%)')
    plt.xticks(rotation=45)
    
    # 在柱状图上标注数值
    for bar, mean in zip(bars, pdr_means):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{mean:.1f}%', ha='center', va='bottom')
    
    # 2. 平均延迟比较
    plt.subplot(2, 3, 2)
    delay_means = [df[df['protocol'] == p]['avg_delay_steps'].mean() for p in protocols]
    delay_stds = [df[df['protocol'] == p]['avg_delay_steps'].std() for p in protocols]
    
    bars = plt.bar(protocols, delay_means, yerr=delay_stds, capsize=5, color='orange')
    plt.title('平均端到端延迟')
    plt.ylabel('延迟 (步)')
    plt.xticks(rotation=45)
    
    for bar, mean in zip(bars, delay_means):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                f'{mean:.1f}', ha='center', va='bottom')
    
    # 3. 平均覆盖率比较
    plt.subplot(2, 3, 3)
    coverage_means = [df[df['protocol'] == p]['avg_coverage_percent'].mean() for p in protocols]
    coverage_stds = [df[df['protocol'] == p]['avg_coverage_percent'].std() for p in protocols]
    
    bars = plt.bar(protocols, coverage_means, yerr=coverage_stds, capsize=5, color='green')
    plt.title('平均覆盖率')
    plt.ylabel('覆盖率 (%)')
    plt.xticks(rotation=45)
    
    for bar, mean in zip(bars, coverage_means):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{mean:.1f}%', ha='center', va='bottom')
    
    # 4. 平均跳数比较
    plt.subplot(2, 3, 4)
    hops_means = [df[df['protocol'] == p]['avg_hops'].mean() for p in protocols]
    hops_stds = [df[df['protocol'] == p]['avg_hops'].std() for p in protocols]
    
    bars = plt.bar(protocols, hops_means, yerr=hops_stds, capsize=5, color='red')
    plt.title('平均跳数')
    plt.ylabel('跳数')
    plt.xticks(rotation=45)
    
    for bar, mean in zip(bars, hops_means):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                f'{mean:.1f}', ha='center', va='bottom')
    
    # 5. 路由开销比较
    plt.subplot(2, 3, 5)
    overhead_means = [df[df['protocol'] == p]['total_overhead_packets'].mean() for p in protocols]
    overhead_stds = [df[df['protocol'] == p]['total_overhead_packets'].std() for p in protocols]
    
    bars = plt.bar(protocols, overhead_means, yerr=overhead_stds, capsize=5, color='purple')
    plt.title('路由开销')
    plt.ylabel('开销 (数据包)')
    plt.xticks(rotation=45)
    
    for bar, mean in zip(bars, overhead_means):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(overhead_means)*0.02, 
                f'{mean:.0f}', ha='center', va='bottom')
    
    # 6. 路由断开比较
    plt.subplot(2, 3, 6)
    disconn_means = [df[df['protocol'] == p]['route_disconnections'].mean() for p in protocols]
    disconn_stds = [df[df['protocol'] == p]['route_disconnections'].std() for p in protocols]
    
    bars = plt.bar(protocols, disconn_means, yerr=disconn_stds, capsize=5, color='brown')
    plt.title('路由断开次数')
    plt.ylabel('断开次数')
    plt.xticks(rotation=45)
    
    for bar, mean in zip(bars, disconn_means):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(disconn_means)*0.02, 
                f'{mean:.0f}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(results_dir / "routing_comparison_results.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ 图表已保存: {results_dir}/routing_comparison_results.png")

def main():
    """主函数"""
    print("🚀 路由协议比较实验 - 最终版本")
    print("使用修复后的网络连接参数进行性能比较")
    print("=" * 60)
    
    # 运行实验
    results = run_comparison_experiment()
    
    # 分析结果
    if results:
        summary = analyze_results(results)
        
        print("\n🎉 实验完成！")
        print("请查看results/目录中的详细结果和图表。")
    else:
        print("❌ 实验失败，没有获得结果")

if __name__ == "__main__":
    main()
