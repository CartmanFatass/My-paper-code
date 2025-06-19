import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv
import seaborn as sns

def test_sinr_throughput_analysis():
    """
    测试5UAV 50users环境下的SINR和throughput分析
    """
    print("=" * 60)
    print("5UAV 50Users环境SINR和Throughput分析测试")
    print("=" * 60)
    
    # 测试不同的信道模型
    channel_models = ["free_space", "urban", "suburban", "3gpp-36777"]
    user_distributions = ["uniform", "cluster", "hotspot"]
    
    all_results = []
    
    for channel_model in channel_models:
        for user_dist in user_distributions:
            print(f"\n--- 测试配置: {channel_model} + {user_dist} ---")
            
            # 创建环境
            env = UAVCooperativeNetworkEnv(
                n_uavs=5,
                n_users=50,
                area_size=1000,
                height_range=(50, 150),
                user_distribution=user_dist,
                channel_model=channel_model,
                seed=42
            )
            
            # 重置环境
            observations, infos = env.reset()
            
            # 打印基础通信参数
            print(f"载波频率: {env.carrier_frequency/1e9:.1f} GHz")
            print(f"带宽: {env.bandwidth/1e6:.1f} MHz")
            print(f"UAV发射功率: {env.tx_power} dBm")
            print(f"地面基站发射功率: {env.ground_bs_tx_power} dBm")
            print(f"噪声功率: {env.noise_power} dBm")
            print(f"最小SINR阈值: {env.min_sinr} dB")
            print(f"每UAV最大连接数: {env.max_connections}")
            
            # 运行几个步骤让UAV移动到更好的位置
            for step in range(5):
                # 随机动作
                actions = {}
                for agent in env.agents:
                    actions[agent] = np.random.uniform(-0.5, 0.5, 3)  # 小幅移动
                
                observations, rewards, terminations, truncations, infos = env.step(actions)
            
            # 分析当前状态
            result = analyze_environment_state(env, channel_model, user_dist)
            all_results.append(result)
    
    # 生成综合分析报告
    generate_comprehensive_report(all_results)
    
    # 生成可视化图表
    generate_visualizations(all_results)
    
    print("\n" + "=" * 60)
    print("测试完成！报告已保存到文件。")
    print("=" * 60)

def analyze_environment_state(env, channel_model, user_dist):
    """
    分析环境当前状态的SINR和throughput
    """
    result = {
        'channel_model': channel_model,
        'user_distribution': user_dist,
        'uav_positions': env.uav_positions.copy(),
        'user_positions': env.user_positions.copy(),
        'connections': env.connections.copy(),
        'sinr_matrix': env.sinr_matrix.copy(),
        'detailed_analysis': {}
    }
    
    print(f"\n连接矩阵形状: {env.connections.shape}")
    print(f"总连接数: {np.sum(env.connections)}")
    print(f"连接覆盖率: {np.sum(env.connections)/env.n_users:.2%}")
    
    # SINR分析
    print("\n--- SINR分析 ---")
    
    # 所有UAV-用户对的SINR
    all_sinrs = env.sinr_matrix.flatten()
    connected_sinrs = env.sinr_matrix[env.connections]
    
    print(f"所有SINR统计 (dB):")
    print(f"  均值: {np.mean(all_sinrs):.2f}")
    print(f"  标准差: {np.std(all_sinrs):.2f}")
    print(f"  最小值: {np.min(all_sinrs):.2f}")
    print(f"  最大值: {np.max(all_sinrs):.2f}")
    print(f"  中位数: {np.median(all_sinrs):.2f}")
    
    if len(connected_sinrs) > 0:
        print(f"\n已连接链路的SINR统计 (dB):")
        print(f"  均值: {np.mean(connected_sinrs):.2f}")
        print(f"  标准差: {np.std(connected_sinrs):.2f}")
        print(f"  最小值: {np.min(connected_sinrs):.2f}")
        print(f"  最大值: {np.max(connected_sinrs):.2f}")
        print(f"  中位数: {np.median(connected_sinrs):.2f}")
    
    # 按SINR范围统计连接分布
    sinr_ranges = [(-20, 0), (0, 10), (10, 20), (20, 30), (30, 40), (40, float('inf'))]
    print(f"\n按SINR范围统计已连接链路:")
    for range_min, range_max in sinr_ranges:
        if range_max == float('inf'):
            count = np.sum((connected_sinrs >= range_min))
            print(f"  {range_min}dB+: {count} 个连接")
        else:
            count = np.sum((connected_sinrs >= range_min) & (connected_sinrs < range_max))
            print(f"  {range_min}-{range_max}dB: {count} 个连接")
    
    # Throughput分析
    print("\n--- Throughput分析 ---")
    
    # 计算所有连接的吞吐量
    individual_throughputs = []
    uav_throughputs = []
    uav_effective_throughputs = []
    
    for i in range(env.n_uavs):
        uav_total_throughput = 0
        uav_connected_users = []
        
        for j in range(env.n_users):
            if env.connections[i, j]:
                throughput = env._compute_throughput(i, j)
                throughput_mbps = throughput / 1e6
                individual_throughputs.append(throughput_mbps)
                uav_total_throughput += throughput
                uav_connected_users.append(j)
        
        uav_throughputs.append(uav_total_throughput / 1e6)  # 转换为Mbps
        
        # 计算有效吞吐量（考虑回程瓶颈）
        uav_user_throughput = 0
        for j in range(env.n_users):
            if env.connections[i, j]:
                user_throughput = env._compute_throughput(i, j)
                uav_user_throughput += user_throughput
        
        if i in env.routing_paths:
            backhaul_capacity = env._compute_backhaul_capacity(i)
            path = env.routing_paths[i]
            hop_count = len(path)
            hop_efficiency = 1.0 / hop_count if hop_count > 0 else 0
            effective_backhaul = backhaul_capacity * hop_efficiency
            uav_effective_throughput = min(uav_user_throughput, effective_backhaul)
        else:
            uav_effective_throughput = 0
        
        uav_effective_throughputs.append(uav_effective_throughput / 1e6)  # Mbps
        
        print(f"UAV {i}: {len(uav_connected_users)} 个连接, "
              f"前端总需求: {uav_total_throughput/1e6:.1f} Mbps, "
              f"有效吞吐量: {uav_effective_throughput/1e6:.1f} Mbps")
    
    # 系统总吞吐量
    system_throughput = sum(uav_effective_throughputs)
    max_realistic_throughput = env._compute_realistic_max_throughput() / 1e6
    
    print(f"\n系统吞吐量统计:")
    print(f"  各UAV有效吞吐量: {[f'{t:.1f}' for t in uav_effective_throughputs]} Mbps")
    print(f"  系统总有效吞吐量: {system_throughput:.1f} Mbps")
    print(f"  理论最大吞吐量: {max_realistic_throughput:.1f} Mbps")
    print(f"  吞吐量利用率: {system_throughput/max_realistic_throughput:.2%}")
    
    if individual_throughputs:
        print(f"\n单连接吞吐量统计 (Mbps):")
        print(f"  均值: {np.mean(individual_throughputs):.1f}")
        print(f"  标准差: {np.std(individual_throughputs):.1f}")
        print(f"  最小值: {np.min(individual_throughputs):.1f}")
        print(f"  最大值: {np.max(individual_throughputs):.1f}")
        print(f"  中位数: {np.median(individual_throughputs):.1f}")
        
        # 检查是否有异常高的单连接吞吐量
        high_throughput_threshold = 200  # Mbps
        high_throughput_connections = [t for t in individual_throughputs if t > high_throughput_threshold]
        if high_throughput_connections:
            print(f"  ⚠️  检测到 {len(high_throughput_connections)} 个异常高吞吐量连接 (>{high_throughput_threshold}Mbps)")
            print(f"      异常值: {[f'{t:.1f}' for t in high_throughput_connections]} Mbps")
    
    # 距离和路径损耗分析
    print("\n--- 距离和路径损耗分析 ---")
    connected_distances = []
    connected_path_losses = []
    
    for i in range(env.n_uavs):
        for j in range(env.n_users):
            if env.connections[i, j]:
                # 计算3D距离
                uav_pos = env.uav_positions[i]
                user_pos_3d = np.append(env.user_positions[j], 0)  # 用户在地面
                distance = np.sqrt(np.sum((uav_pos - user_pos_3d) ** 2))
                connected_distances.append(distance)
                
                # 计算路径损耗
                path_loss = env._compute_path_loss(uav_pos, env.user_positions[j])
                connected_path_losses.append(path_loss)
    
    if connected_distances:
        print(f"已连接链路的距离统计 (m):")
        print(f"  均值: {np.mean(connected_distances):.1f}")
        print(f"  最小值: {np.min(connected_distances):.1f}")
        print(f"  最大值: {np.max(connected_distances):.1f}")
        
        print(f"已连接链路的路径损耗统计 (dB):")
        print(f"  均值: {np.mean(connected_path_losses):.1f}")
        print(f"  最小值: {np.min(connected_path_losses):.1f}")
        print(f"  最大值: {np.max(connected_path_losses):.1f}")
    
    # 保存详细分析结果
    result['detailed_analysis'] = {
        'all_sinrs': all_sinrs,
        'connected_sinrs': connected_sinrs,
        'individual_throughputs': individual_throughputs,
        'uav_throughputs': uav_throughputs,
        'uav_effective_throughputs': uav_effective_throughputs,
        'system_throughput': system_throughput,
        'max_realistic_throughput': max_realistic_throughput,
        'connected_distances': connected_distances,
        'connected_path_losses': connected_path_losses,
        'routing_paths': dict(env.routing_paths)
    }
    
    return result

def generate_comprehensive_report(all_results):
    """
    生成综合分析报告
    """
    print("\n" + "=" * 60)
    print("综合分析报告")
    print("=" * 60)
    
    # 创建汇总表格
    summary_data = []
    
    for result in all_results:
        analysis = result['detailed_analysis']
        
        row = {
            '信道模型': result['channel_model'],
            '用户分布': result['user_distribution'],
            '连接数': np.sum(result['connections']),
            '覆盖率(%)': f"{np.sum(result['connections'])/50*100:.1f}",
            '平均SINR(dB)': f"{np.mean(analysis['connected_sinrs']):.1f}" if len(analysis['connected_sinrs']) > 0 else "N/A",
            '最大SINR(dB)': f"{np.max(analysis['connected_sinrs']):.1f}" if len(analysis['connected_sinrs']) > 0 else "N/A",
            '单连接最大吞吐量(Mbps)': f"{np.max(analysis['individual_throughputs']):.1f}" if analysis['individual_throughputs'] else "N/A",
            '系统总吞吐量(Mbps)': f"{analysis['system_throughput']:.1f}",
            '理论最大吞吐量(Mbps)': f"{analysis['max_realistic_throughput']:.1f}",
        }
        summary_data.append(row)
    
    # 打印汇总表格
    df = pd.DataFrame(summary_data)
    print("\n汇总统计表:")
    print(df.to_string(index=False))
    
    # 保存到CSV文件
    df.to_csv('sinr_throughput_summary.csv', index=False, encoding='utf-8-sig')
    print(f"\n汇总表已保存到: sinr_throughput_summary.csv")
    
    # 分析异常情况
    print("\n--- 异常情况分析 ---")
    
    max_single_throughput = 0
    max_system_throughput = 0
    problematic_configs = []
    
    for result in all_results:
        analysis = result['detailed_analysis']
        
        if analysis['individual_throughputs']:
            max_single = np.max(analysis['individual_throughputs'])
            if max_single > max_single_throughput:
                max_single_throughput = max_single
            
            # 检查单连接吞吐量是否异常
            if max_single > 300:  # 超过300Mbps认为异常
                problematic_configs.append({
                    'config': f"{result['channel_model']}+{result['user_distribution']}",
                    'issue': f"单连接吞吐量过高: {max_single:.1f} Mbps",
                    'type': 'single_throughput'
                })
        
        system_throughput = analysis['system_throughput']
        if system_throughput > max_system_throughput:
            max_system_throughput = system_throughput
        
        # 检查系统总吞吐量是否异常
        if system_throughput > 1000:  # 超过1000Mbps认为异常
            problematic_configs.append({
                'config': f"{result['channel_model']}+{result['user_distribution']}",
                'issue': f"系统吞吐量过高: {system_throughput:.1f} Mbps",
                'type': 'system_throughput'
            })
    
    print(f"发现的最大单连接吞吐量: {max_single_throughput:.1f} Mbps")
    print(f"发现的最大系统吞吐量: {max_system_throughput:.1f} Mbps")
    
    if problematic_configs:
        print(f"\n检测到 {len(problematic_configs)} 个潜在问题:")
        for i, config in enumerate(problematic_configs, 1):
            print(f"  {i}. {config['config']}: {config['issue']}")
    else:
        print("\n未检测到明显的异常吞吐量问题。")
    
    # 理论分析
    print("\n--- 理论验证 ---")
    bandwidth_mhz = 20  # MHz
    print(f"系统带宽: {bandwidth_mhz} MHz")
    print(f"香农公式理论最大值 (30dB SINR): C = B × log₂(1 + 10^(30/10)) ≈ {bandwidth_mhz * np.log2(1 + 1000):.1f} Mbps")
    print(f"单UAV理论最大前端容量: ~{bandwidth_mhz * np.log2(1 + 1000):.1f} Mbps")
    print(f"5UAV理论最大系统容量: ~{5 * bandwidth_mhz * np.log2(1 + 1000):.1f} Mbps (假设完美频谱复用)")
    
    # 合理期望值
    print(f"\n--- 合理期望值 ---")
    print(f"单连接吞吐量: 1-200 Mbps (取决于SINR和距离)")
    print(f"单UAV总吞吐量: 20-400 Mbps (受带宽和连接数限制)")
    print(f"系统总吞吐量: 100-1000 Mbps (考虑回程瓶颈和多跳损失)")

def generate_visualizations(all_results):
    """
    生成可视化图表
    """
    print("\n生成可视化图表...")
    
    # 设置图表样式
    plt.style.use('default')
    sns.set_palette("husl")
    
    # 创建多个子图
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('5UAV 50Users SINR and Throughput Analysis Report', fontsize=16, fontweight='bold')
    
    # 收集所有数据
    all_sinrs = []
    all_throughputs = []
    system_throughputs = []
    config_labels = []
    
    for result in all_results:
        analysis = result['detailed_analysis']
        config_label = f"{result['channel_model']}\n{result['user_distribution']}"
        config_labels.append(config_label)
        
        if analysis['connected_sinrs'] is not None and len(analysis['connected_sinrs']) > 0:
            all_sinrs.extend(analysis['connected_sinrs'])
        
        if analysis['individual_throughputs']:
            all_throughputs.extend(analysis['individual_throughputs'])
        
        system_throughputs.append(analysis['system_throughput'])
    
    # 1. SINR分布直方图
    if all_sinrs:
        axes[0, 0].hist(all_sinrs, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, 0].set_xlabel('SINR (dB)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].set_title('SINR Distribution of Connected Links')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].axvline(np.mean(all_sinrs), color='red', linestyle='--', 
                           label=f'Mean: {np.mean(all_sinrs):.1f} dB')
        axes[0, 0].legend()
    
    # 2. 单连接吞吐量分布
    if all_throughputs:
        axes[0, 1].hist(all_throughputs, bins=30, alpha=0.7, color='lightgreen', edgecolor='black')
        axes[0, 1].set_xlabel('Single Connection Throughput (Mbps)')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].set_title('Single Connection Throughput Distribution')
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].axvline(np.mean(all_throughputs), color='red', linestyle='--',
                           label=f'Mean: {np.mean(all_throughputs):.1f} Mbps')
        # 标记异常值
        if np.max(all_throughputs) > 200:
            axes[0, 1].axvline(200, color='orange', linestyle='-', 
                               label='Anomaly Threshold: 200 Mbps')
        axes[0, 1].legend()
    
    # 3. 系统总吞吐量对比
    x_pos = range(len(config_labels))
    bars = axes[0, 2].bar(x_pos, system_throughputs, alpha=0.7, color='coral')
    axes[0, 2].set_xlabel('Configuration')
    axes[0, 2].set_ylabel('System Total Throughput (Mbps)')
    axes[0, 2].set_title('System Total Throughput under Different Configurations')
    axes[0, 2].set_xticks(x_pos)
    axes[0, 2].set_xticklabels(config_labels, rotation=45, ha='right')
    axes[0, 2].grid(True, alpha=0.3)
    
    # 在柱状图上添加数值标签
    for bar, value in zip(bars, system_throughputs):
        axes[0, 2].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
                        f'{value:.0f}', ha='center', va='bottom')
    
    # 标记异常阈值
    axes[0, 2].axhline(1000, color='red', linestyle='--', label='Anomaly Threshold: 1000 Mbps')
    axes[0, 2].legend()
    
    # 4. SINR vs 吞吐量散点图
    if all_sinrs and all_throughputs and len(all_sinrs) == len(all_throughputs):
        scatter = axes[1, 0].scatter(all_sinrs, all_throughputs, alpha=0.6, c=all_throughputs, 
                                     cmap='viridis', s=50)
        axes[1, 0].set_xlabel('SINR (dB)')
        axes[1, 0].set_ylabel('Single Connection Throughput (Mbps)')
        axes[1, 0].set_title('SINR vs Single Connection Throughput')
        axes[1, 0].grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=axes[1, 0], label='Throughput (Mbps)')
    
    # 5. 不同信道模型的吞吐量箱线图
    channel_models = list(set([r['channel_model'] for r in all_results]))
    throughput_by_channel = {model: [] for model in channel_models}
    
    for result in all_results:
        channel = result['channel_model']
        analysis = result['detailed_analysis']
        if analysis['individual_throughputs']:
            throughput_by_channel[channel].extend(analysis['individual_throughputs'])
    
    # 只绘制有数据的信道模型
    valid_channels = [ch for ch in channel_models if throughput_by_channel[ch]]
    if valid_channels:
        box_data = [throughput_by_channel[ch] for ch in valid_channels]
        box_plot = axes[1, 1].boxplot(box_data, labels=valid_channels, patch_artist=True)
        
        # 美化箱线图
        colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow']
        for patch, color in zip(box_plot['boxes'], colors[:len(box_plot['boxes'])]):
            patch.set_facecolor(color)
        
        axes[1, 1].set_xlabel('Channel Model')
        axes[1, 1].set_ylabel('Single Connection Throughput (Mbps)')
        axes[1, 1].set_title('Throughput Distribution by Channel Model')
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].tick_params(axis='x', rotation=45)
    
    # 6. 理论值对比
    theoretical_max = 20 * np.log2(1 + 1000)  # 20MHz * log2(1+30dB)
    actual_max = np.max(all_throughputs) if all_throughputs else 0
    
    categories = ['Theoretical Single\nConnection Max', 'Actual Single\nConnection Max', 'Actual System Max']
    values = [theoretical_max, actual_max, np.max(system_throughputs)]
    colors = ['blue', 'orange', 'red']
    
    bars = axes[1, 2].bar(categories, values, color=colors, alpha=0.7)
    axes[1, 2].set_ylabel('Throughput (Mbps)')
    axes[1, 2].set_title('Theoretical vs Actual Values Comparison')
    axes[1, 2].tick_params(axis='x', rotation=45)
    
    # 添加数值标签
    for bar, value in zip(bars, values):
        axes[1, 2].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 20,
                        f'{value:.0f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('sinr_throughput_analysis.png', dpi=300, bbox_inches='tight')
    print("可视化图表已保存到: sinr_throughput_analysis.png")
    
    # 显示图表（如果在交互环境中）
    try:
        plt.show()
    except:
        pass
    
    plt.close()

if __name__ == "__main__":
    test_sinr_throughput_analysis()
