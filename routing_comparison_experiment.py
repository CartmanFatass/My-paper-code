#!/usr/bin/env python3
"""
路由协议比较实验脚本

该脚本实现了一个完整的基准测试框架，用于比较HGGR算法与经典路由协议（AODV、DSDV、GPSR）的性能。

主要功能：
1. 配置多种路由协议的实验参数
2. 运行多次仿真以获得统计显著的结果
3. 收集并分析性能指标（PDR、延迟、跳数、能耗、开销）
4. 生成对比图表和统计报告

使用方法：
python routing_comparison_experiment.py
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 设置后端以避免GUI依赖
import time
import json
import os
from typing import Dict, List, Any

# 导入环境
try:
    from envs.pettingzoo.scenario4_discrete import UAVForcedRelayEnv
    ENV_AVAILABLE = True
except ImportError as e:
    print(f"环境导入失败: {e}")
    ENV_AVAILABLE = False

def create_config(routing_protocol: str, seed: int = 42) -> object:
    """
    创建实验配置对象
    
    参数:
        routing_protocol: 路由协议名称
        seed: 随机种子
    
    返回:
        config: 配置对象
    """
    class ExperimentConfig:
        def __init__(self):
            # 基础环境参数
            self.n_agents = 12  # 对应n_uavs
            self.n_users = 80
            self.area_size = 2500
            self.max_steps = 500  # 减少步数以加快实验
            self.height_range = (50, 200)
            self.discrete_speed = 15.0
            self.time_step = 1.0
            
            # 场景特定参数
            self.n_clusters = 4
            self.cluster_std = 80
            self.central_area_ratio = 0.6
            self.base_station_distance_factor = 0.8
            self.observation_radius = 600
            self.uav_init_mode = "start_area"
            self.uav_start_area_size = 500
            self.n_ground_bs = 1
            self.max_hops = 4
            self.min_sinr = 3
            self.max_connections = 25
            
            # 用户移动
            self.user_distribution = "forced_relay_cluster"
            self.user_max_speed = 5.0
            self.user_movement_model = "random_walk"
            
            # 随机化控制
            self.randomize_bs = True
            self.randomize_users = True
            self.randomize_uav_start = True
            
            # 奖励设置
            self.reward_type = "health"
            self.w_connectivity = 0.5
            self.w_diversity = 1.0
            self.w_coverage = 1.0
            self.w_dispersion = 0.05
            
            # 通信参数
            self.carrier_frequency = 2e9
            self.tx_power = 23
            self.noise_power = -94
            self.bandwidth = 20e6
            self.ground_bs_tx_power = 30
            self.use_fdma = False
            
            # 路由协议设置
            self.routing_protocol = routing_protocol
            self.k = 10  # HGGR更新间隔
            
            # 种子
            self.seed = seed
    
    return ExperimentConfig()

def run_single_simulation(config: object) -> Dict[str, Any]:
    """
    运行单次仿真实验
    
    参数:
        config: 实验配置
    
    返回:
        results: 实验结果字典
    """
    if not ENV_AVAILABLE:
        return {"error": "环境不可用"}
    
    # 创建环境
    env = UAVForcedRelayEnv(config=config)
    
    # 重置环境
    obs, infos = env.reset()
    
    # 跟踪指标
    total_overhead = 0
    step_rewards = []
    coverage_history = []
    throughput_history = []
    
    # 运行仿真
    for step in range(config.max_steps):
        # 使用随机动作（可以替换为训练好的策略）
        actions = {}
        for agent in env.agents:
            actions[agent] = env.np_random.randint(0, env.n_discrete_actions)
        
        # 执行步骤
        obs, rewards, terminations, truncations, infos = env.step(actions)
        
        # 收集指标
        if "uav_0" in infos:
            agent_info = infos["uav_0"]
            total_overhead += agent_info.get("routing_overhead", 0)
            step_rewards.append(rewards.get("uav_0", 0))
            coverage_history.append(agent_info.get("coverage_ratio", 0))
            throughput_history.append(agent_info.get("reward_info", {}).get("system_throughput_mbps", 0))
        
        # 检查终止条件
        if any(terminations.values()) or any(truncations.values()):
            break
    
    # 计算最终指标
    final_metrics = env.metrics
    
    # 数据包级指标
    if final_metrics["packets_sent"] > 0:
        pdr = final_metrics["packets_arrived"] / final_metrics["packets_sent"]
        avg_delay = final_metrics["total_end_to_end_delay"] / final_metrics["packets_arrived"] if final_metrics["packets_arrived"] > 0 else float('inf')
        avg_hops = final_metrics["total_hop_count"] / final_metrics["packets_arrived"] if final_metrics["packets_arrived"] > 0 else float('inf')
    else:
        pdr = 0.0
        avg_delay = float('inf')
        avg_hops = float('inf')
    
    # 关闭环境
    env.close()
    
    return {
        "Protocol": config.routing_protocol,
        "Seed": config.seed,
        "PDR": pdr,
        "Avg_Delay_Steps": avg_delay,
        "Avg_Hops": avg_hops,
        "Total_Routing_Overhead": total_overhead,
        "Total_Energy_mJ": final_metrics["total_energy_consumed_mj"],
        "Route_Disconnections": final_metrics["route_disconnections"],
        "Packets_Sent": final_metrics["packets_sent"],
        "Packets_Arrived": final_metrics["packets_arrived"],
        "Final_Coverage": coverage_history[-1] if coverage_history else 0,
        "Avg_Coverage": np.mean(coverage_history) if coverage_history else 0,
        "Final_Throughput_Mbps": throughput_history[-1] if throughput_history else 0,
        "Avg_Throughput_Mbps": np.mean(throughput_history) if throughput_history else 0,
        "Avg_Reward": np.mean(step_rewards) if step_rewards else 0,
        "Simulation_Steps": step + 1
    }

def run_comparative_experiments(protocols_to_test: List[str], num_seeds: int = 5) -> pd.DataFrame:
    """
    运行比较实验
    
    参数:
        protocols_to_test: 要测试的协议列表
        num_seeds: 每个协议运行的种子数量
    
    返回:
        results_df: 包含所有实验结果的DataFrame
    """
    print("=== 开始路由协议比较实验 ===")
    
    results_list = []
    
    for protocol in protocols_to_test:
        print(f"\n--- 运行 {protocol.upper()} 协议仿真 ---")
        
        # 为每个协议运行多个种子
        for seed in range(num_seeds):
            print(f"  种子 {seed+1}/{num_seeds}...", end=" ", flush=True)
            
            # 创建配置
            config = create_config(protocol, seed)
            
            # 运行仿真
            start_time = time.time()
            run_results = run_single_simulation(config)
            end_time = time.time()
            
            # 添加运行时间
            run_results["Runtime_Seconds"] = end_time - start_time
            results_list.append(run_results)
            
            print(f"完成 (PDR: {run_results['PDR']:.2%}, 覆盖率: {run_results['Final_Coverage']:.2%})")
    
    # 转换为DataFrame
    results_df = pd.DataFrame(results_list)
    
    print(f"\n=== 实验完成，共收集 {len(results_df)} 个数据点 ===")
    
    return results_df

def analyze_and_visualize_results(results_df: pd.DataFrame, save_dir: str = "routing_comparison_results"):
    """
    分析并可视化实验结果
    
    参数:
        results_df: 实验结果DataFrame
        save_dir: 保存目录
    """
    # 创建保存目录
    os.makedirs(save_dir, exist_ok=True)
    
    # 1. 计算统计摘要
    print("\n=== 性能统计摘要 ===")
    summary_stats = results_df.groupby('Protocol').agg({
        'PDR': ['mean', 'std'],
        'Avg_Delay_Steps': ['mean', 'std'],
        'Avg_Hops': ['mean', 'std'],
        'Total_Routing_Overhead': ['mean', 'std'],
        'Total_Energy_mJ': ['mean', 'std'],
        'Route_Disconnections': ['mean', 'std'],
        'Final_Coverage': ['mean', 'std'],
        'Avg_Throughput_Mbps': ['mean', 'std'],
        'Runtime_Seconds': ['mean', 'std']
    }).round(4)
    
    print(summary_stats)
    
    # 保存统计摘要
    summary_stats.to_csv(os.path.join(save_dir, "performance_summary.csv"))
    
    # 2. 创建比较图表
    protocols = results_df['Protocol'].unique()
    n_protocols = len(protocols)
    
    # 设置图表样式
    plt.style.use('default')
    colors = plt.cm.tab10(np.linspace(0, 1, n_protocols))
    
    # 创建多子图
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    # 关键性能指标
    metrics_to_plot = [
        ('PDR', '数据包传输成功率'),
        ('Avg_Delay_Steps', '平均端到端延迟 (步数)'),
        ('Avg_Hops', '平均跳数'),
        ('Total_Routing_Overhead', '总路由开销 (数据包数)'),
        ('Final_Coverage', '最终覆盖率'),
        ('Avg_Throughput_Mbps', '平均系统吞吐量 (Mbps)')
    ]
    
    for i, (metric, title) in enumerate(metrics_to_plot):
        ax = axes[i]
        
        # 箱形图显示分布
        data_for_boxplot = []
        labels_for_boxplot = []
        
        for j, protocol in enumerate(protocols):
            protocol_data = results_df[results_df['Protocol'] == protocol][metric]
            # 处理无穷值
            if metric in ['Avg_Delay_Steps', 'Avg_Hops']:
                protocol_data = protocol_data.replace([float('inf'), -float('inf')], np.nan).dropna()
            data_for_boxplot.append(protocol_data)
            labels_for_boxplot.append(protocol)
        
        # 绘制箱形图
        box_plot = ax.boxplot(data_for_boxplot, labels=labels_for_boxplot, patch_artist=True)
        
        # 设置颜色
        for patch, color in zip(box_plot['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)
        
        # 特殊处理某些指标
        if metric == 'PDR' or metric == 'Final_Coverage':
            ax.set_ylim(0, 1)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0%}'))
        elif metric == 'Total_Routing_Overhead':
            ax.set_yscale('log')  # 对数尺度，因为开销可能差异很大
    
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, "performance_comparison.png"), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. 创建详细的协议比较表
    detailed_comparison = results_df.groupby('Protocol').agg({
        'PDR': ['mean', 'std', 'min', 'max'],
        'Avg_Delay_Steps': ['mean', 'std', 'min', 'max'],
        'Avg_Hops': ['mean', 'std', 'min', 'max'],
        'Total_Routing_Overhead': ['mean', 'std', 'min', 'max'],
        'Total_Energy_mJ': ['mean', 'std', 'min', 'max'],
        'Final_Coverage': ['mean', 'std', 'min', 'max'],
        'Avg_Throughput_Mbps': ['mean', 'std', 'min', 'max']
    }).round(4)
    
    detailed_comparison.to_csv(os.path.join(save_dir, "detailed_comparison.csv"))
    
    # 4. 生成性能排名
    ranking_metrics = ['PDR', 'Final_Coverage', 'Avg_Throughput_Mbps']  # 越高越好
    overhead_metrics = ['Avg_Delay_Steps', 'Avg_Hops', 'Total_Routing_Overhead']  # 越低越好
    
    protocol_scores = {}
    for protocol in protocols:
        protocol_data = results_df[results_df['Protocol'] == protocol]
        score = 0
        
        # 正向指标（越高越好）
        for metric in ranking_metrics:
            mean_value = protocol_data[metric].mean()
            max_possible = results_df[metric].max()
            if max_possible > 0:
                normalized_score = mean_value / max_possible
                score += normalized_score
        
        # 反向指标（越低越好）
        for metric in overhead_metrics:
            mean_value = protocol_data[metric].mean()
            # 处理无穷值
            if np.isinf(mean_value):
                normalized_penalty = 1.0  # 最大惩罚
            else:
                min_possible = results_df[metric].min()
                max_possible = results_df[metric].max()
                if max_possible > min_possible:
                    normalized_penalty = (mean_value - min_possible) / (max_possible - min_possible)
                else:
                    normalized_penalty = 0
            score -= normalized_penalty * 0.5  # 降低惩罚权重
        
        protocol_scores[protocol] = score
    
    # 按分数排序
    ranked_protocols = sorted(protocol_scores.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n=== 协议性能排名 ===")
    for i, (protocol, score) in enumerate(ranked_protocols):
        print(f"{i+1}. {protocol}: {score:.3f}")
    
    # 保存排名
    ranking_df = pd.DataFrame(ranked_protocols, columns=['Protocol', 'Overall_Score'])
    ranking_df.to_csv(os.path.join(save_dir, "protocol_ranking.csv"), index=False)
    
    # 5. 保存原始数据
    results_df.to_csv(os.path.join(save_dir, "raw_results.csv"), index=False)
    
    # 6. 生成文本报告
    report_lines = [
        "# 路由协议比较实验报告",
        f"",
        f"实验时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"测试协议: {', '.join(protocols)}",
        f"每协议种子数: {results_df['Seed'].max() + 1}",
        f"总仿真次数: {len(results_df)}",
        f"",
        f"## 关键发现",
        f"",
        f"### 1. 最佳数据包传输率 (PDR):"
    ]
    
    # PDR排名
    pdr_ranking = results_df.groupby('Protocol')['PDR'].mean().sort_values(ascending=False)
    for i, (protocol, pdr) in enumerate(pdr_ranking.items()):
        report_lines.append(f"{i+1}. {protocol}: {pdr:.2%}")
    
    report_lines.extend([
        f"",
        f"### 2. 最低路由开销:",
    ])
    
    # 开销排名（越低越好）
    overhead_ranking = results_df.groupby('Protocol')['Total_Routing_Overhead'].mean().sort_values()
    for i, (protocol, overhead) in enumerate(overhead_ranking.items()):
        report_lines.append(f"{i+1}. {protocol}: {overhead:.0f} 数据包")
    
    report_lines.extend([
        f"",
        f"### 3. 总体性能排名:",
    ])
    
    for i, (protocol, score) in enumerate(ranked_protocols):
        report_lines.append(f"{i+1}. {protocol}: {score:.3f}")
    
    # 保存报告
    with open(os.path.join(save_dir, "experiment_report.md"), 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"\n实验结果已保存到目录: {save_dir}")
    
    return ranking_df

def main():
    """主实验函数"""
    if not ENV_AVAILABLE:
        print("错误：无法导入实验环境，请检查路径和依赖。")
        return
    
    # 实验参数
    protocols_to_test = ['hggr', 'aodv', 'dsdv', 'geographic', 'widest_path']
    num_seeds = 3  # 每个协议测试3个种子
    
    print(f"开始路由协议比较实验")
    print(f"测试协议: {protocols_to_test}")
    print(f"每协议种子数: {num_seeds}")
    print(f"预计总仿真次数: {len(protocols_to_test) * num_seeds}")
    
    # 运行实验
    start_time = time.time()
    
    try:
        results_df = run_comparative_experiments(protocols_to_test, num_seeds)
        
        # 分析结果
        ranking_df = analyze_and_visualize_results(results_df)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n=== 实验总结 ===")
        print(f"总运行时间: {total_time:.2f} 秒")
        print(f"平均每次仿真: {total_time / len(results_df):.2f} 秒")
        
        # 显示最佳协议
        if not ranking_df.empty:
            best_protocol = ranking_df.iloc[0]['Protocol']
            best_score = ranking_df.iloc[0]['Overall_Score']
            print(f"最佳协议: {best_protocol} (综合得分: {best_score:.3f})")
            
            # 显示HGGR的性能表现
            hggr_results = results_df[results_df['Protocol'] == 'hggr']
            if not hggr_results.empty:
                hggr_pdr = hggr_results['PDR'].mean()
                hggr_coverage = hggr_results['Final_Coverage'].mean()
                hggr_overhead = hggr_results['Total_Routing_Overhead'].mean()
                
                print(f"\nHGGR协议性能:")
                print(f"  平均PDR: {hggr_pdr:.2%}")
                print(f"  平均覆盖率: {hggr_coverage:.2%}")
                print(f"  平均路由开销: {hggr_overhead:.0f} 数据包")
    
    except Exception as e:
        print(f"实验过程中发生错误: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
