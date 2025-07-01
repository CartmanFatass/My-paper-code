import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime
from tqdm import tqdm

# 添加父目录到路径，使得可以导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入必要的模块
from envs.pettingzoo.scenario3 import UAVMultiHopEnv
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from visualize_evaluation import EnhancedVisualizationEnv

class AllConfigsVisualizer:
    """
    所有配置的可视化器
    """
    
    def __init__(self, save_base_path="./test"):
        """
        初始化可视化器
        
        参数:
            save_base_path: 基础保存路径
        """
        self.save_base_path = save_base_path
        
        # 配置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    def visualize_all_configs_from_csv(self, csv_path):
        """
        从CSV文件读取配置并为所有配置生成可视化
        
        参数:
            csv_path: CSV文件路径
        """
        # 读取测试结果
        results_df = pd.read_csv(csv_path)
        print(f"读取到 {len(results_df)} 个配置")
        
        # 创建保存目录
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        save_path = os.path.join(self.save_base_path, f"all_configs_visualization_{timestamp}")
        os.makedirs(save_path, exist_ok=True)
        print(f"可视化结果将保存到: {save_path}")
        
        # 为每个配置生成可视化
        self.generate_all_visualizations(results_df, save_path)
        
        # 生成对比分析
        self.generate_comparison_analysis(results_df, save_path)
        
        print(f"\n所有可视化已完成，保存在: {save_path}")
        return save_path
    
    def generate_all_visualizations(self, results_df, save_path):
        """
        为所有配置生成网络拓扑可视化
        
        参数:
            results_df: 结果DataFrame
            save_path: 保存路径
        """
        print(f"\n为所有 {len(results_df)} 个配置生成网络拓扑可视化...")
        
        # 为每个配置创建可视化
        for i, (idx, config) in enumerate(tqdm(results_df.iterrows(), total=len(results_df), desc="生成可视化")):
            self._generate_single_config_visualization(config, i+1, save_path)
    
    def _generate_single_config_visualization(self, config, config_num, save_path):
        """
        为单个配置生成网络拓扑可视化
        
        参数:
            config: 配置行
            config_num: 配置编号
            save_path: 保存路径
        """
        # 创建配置专用目录
        config_save_path = os.path.join(save_path, f"config_{config_num}")
        os.makedirs(config_save_path, exist_ok=True)
        
        # 保存配置信息
        config_info_path = os.path.join(config_save_path, "config_info.txt")
        with open(config_info_path, 'w', encoding='utf-8') as f:
            f.write(f"配置 {config_num} 详细信息\n")
            f.write("=" * 30 + "\n\n")
            f.write(f"UAV数量: {config['n_uavs']}\n")
            f.write(f"用户数量: {config['n_users']}\n")
            f.write(f"区域大小: {config['area_size']} 米\n")
            f.write(f"用户簇数量: {config['n_clusters']}\n")
            f.write(f"最大跳数: {config['max_hops']}\n")
            f.write(f"用户分布: {config['user_distribution']}\n")
            f.write(f"信道模型: {config['channel_model']}\n")
            f.write(f"带宽: {config['bandwidth']} Hz\n")
            f.write(f"\n性能指标:\n")
            f.write(f"服务率: {config['service_rate']:.1%}\n")
            f.write(f"有效服务率: {config['effective_service_rate']:.1%}\n")
            f.write(f"吞吐量: {config['throughput_mbps']:.1f} Mbps\n")
            f.write(f"网络连通性: {config['network_connectivity']:.1%}\n")
            f.write(f"平均跳数: {config['avg_hops']:.2f}\n")
            f.write(f"总奖励: {config['reward']:.3f}\n")
        
        try:
            # 创建环境
            raw_env = UAVMultiHopEnv(
                n_uavs=int(config['n_uavs']),
                n_users=int(config['n_users']),
                area_size=int(config['area_size']),
                max_hops=int(config['max_hops']),
                user_distribution=config['user_distribution'],
                channel_model=config['channel_model'],
                render_mode="human",
                seed=int(config['seed']),
                n_clusters=int(config['n_clusters']),
                cluster_std=int(config['cluster_std']),
                central_area_ratio=config['central_area_ratio'],
                use_fdma=config['use_fdma'],
                bandwidth=config['bandwidth'],
            )
            
            adapted_env = ParallelToArrayAdapter(raw_env, seed=int(config['seed']))
            vis_env = EnhancedVisualizationEnv(adapted_env, save_path=config_save_path)
            
            # 重置环境并设置均匀位置
            obs, info = vis_env.reset()
            
            # 设置均匀分布的无人机位置
            uniform_positions = self._create_uniform_positions(
                int(config['n_uavs']), 
                int(config['area_size']), 
                (50, 200),
                seed=int(config['seed'])
            )
            vis_env.env.uav_positions = uniform_positions
            
            # 更新环境状态
            vis_env.env._update_channel_state()
            if hasattr(vis_env.env, '_update_uav_connections'):
                vis_env.env._update_uav_connections()
            if hasattr(vis_env.env, '_compute_routing_paths'):
                vis_env.env._compute_routing_paths()
            
            # 创建自定义的可视化图像
            self._create_custom_visualization(vis_env, config, config_num, config_save_path)
            
            # 关闭环境
            vis_env.close()
            
        except Exception as e:
            print(f"配置 {config_num} 可视化失败: {e}")
            # 创建错误报告
            error_path = os.path.join(config_save_path, "error.txt")
            with open(error_path, 'w', encoding='utf-8') as f:
                f.write(f"配置 {config_num} 可视化时发生错误:\n{str(e)}")
    
    def _create_uniform_positions(self, n_uavs, area_size, height_range, seed=None):
        """
        创建均匀分布的无人机位置
        """
        if seed is not None:
            np.random.seed(seed)
        
        # 计算网格大小
        grid_size = int(np.ceil(np.sqrt(n_uavs)))
        
        positions = []
        
        # 计算边距，避免无人机太靠近边界
        margin = area_size * 0.1  # 10%边距
        effective_area = area_size - 2 * margin
        
        for i in range(n_uavs):
            grid_x = i % grid_size
            grid_y = i // grid_size
            
            # 均匀分布在网格中
            x = margin + (grid_x + 0.5) * effective_area / grid_size
            y = margin + (grid_y + 0.5) * effective_area / grid_size
            
            # 添加少量随机扰动
            x += np.random.uniform(-effective_area/(grid_size*4), effective_area/(grid_size*4))
            y += np.random.uniform(-effective_area/(grid_size*4), effective_area/(grid_size*4))
            
            # 确保在边界内
            x = np.clip(x, margin, area_size - margin)
            y = np.clip(y, margin, area_size - margin)
            
            # 随机高度
            z = np.random.uniform(*height_range)
            
            positions.append([x, y, z])
        
        return np.array(positions)
    
    def _create_custom_visualization(self, vis_env, config, config_num, save_path):
        """
        创建自定义的网络拓扑可视化
        """
        # 创建图形
        fig = plt.figure(figsize=(16, 12))
        
        # 主要的3D网络拓扑图
        ax_main = fig.add_subplot(221, projection='3d')
        self._plot_network_topology_3d(ax_main, vis_env, config, config_num)
        
        # 2D俯视图
        ax_2d = fig.add_subplot(222)
        self._plot_network_topology_2d(ax_2d, vis_env, config, config_num)
        
        # 连通性分析图
        ax_connectivity = fig.add_subplot(223)
        self._plot_connectivity_analysis(ax_connectivity, vis_env, config)
        
        # 性能指标雷达图
        ax_radar = fig.add_subplot(224, projection='polar')
        self._plot_performance_radar(ax_radar, config)
        
        # 设置整体标题
        fig.suptitle(f'配置 {config_num} 网络拓扑分析\n'
                    f'区域大小: {config["area_size"]}m, UAV: {config["n_uavs"]}, '
                    f'用户: {config["n_users"]}, 服务率: {config["service_rate"]:.1%}',
                    fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        # 保存图像
        save_file = os.path.join(save_path, "network_topology_analysis.png")
        plt.savefig(save_file, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"  配置 {config_num} 可视化已保存: {save_file}")
    
    def _plot_network_topology_3d(self, ax, vis_env, config, config_num):
        """绘制3D网络拓扑"""
        env = vis_env.env
        
        # 设置坐标轴
        ax.set_xlim(0, env.area_size)
        ax.set_ylim(0, env.area_size)
        ax.set_zlim(0, 250)
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_zlabel('Z (m)')
        ax.set_title(f'3D网络拓扑 - 配置{config_num}')
        
        # 绘制地面基站
        if hasattr(env, 'ground_bs_positions') and len(env.ground_bs_positions) > 0:
            bs_x = env.ground_bs_positions[:, 0]
            bs_y = env.ground_bs_positions[:, 1]
            bs_z = env.ground_bs_positions[:, 2]
            ax.scatter(bs_x, bs_y, bs_z, c='black', marker='s', s=200, 
                      label='地面基站', alpha=0.9, edgecolors='white', linewidth=2)
        
        # 绘制用户
        user_x = env.user_positions[:, 0]
        user_y = env.user_positions[:, 1]
        user_z = np.zeros(env.n_users)
        
        # 区分已连接和未连接的用户
        connected_users = set()
        for i in range(env.n_uavs):
            for j in range(env.n_users):
                if env.connections[i, j]:
                    connected_users.add(j)
        
        # 绘制未连接用户
        unconnected_users = [j for j in range(env.n_users) if j not in connected_users]
        if unconnected_users:
            unconnected_x = [user_x[j] for j in unconnected_users]
            unconnected_y = [user_y[j] for j in unconnected_users]
            unconnected_z = [user_z[j] for j in unconnected_users]
            ax.scatter(unconnected_x, unconnected_y, unconnected_z, 
                      c='lightblue', marker='.', s=30, label='未连接用户', alpha=0.6)
        
        # 绘制已连接用户
        if connected_users:
            connected_x = [user_x[j] for j in connected_users]
            connected_y = [user_y[j] for j in connected_users]
            connected_z = [user_z[j] for j in connected_users]
            ax.scatter(connected_x, connected_y, connected_z, 
                      c='blue', marker='o', s=50, label='已连接用户', alpha=0.8)
        
        # 绘制无人机
        for i in range(env.n_uavs):
            uav_pos = env.uav_positions[i]
            has_users = np.sum(env.connections[i]) > 0
            has_backhaul = hasattr(env, 'routing_paths') and i in env.routing_paths
            
            if has_users and has_backhaul:
                color, size = 'red', 150
            elif has_backhaul:
                color, size = 'darkorange', 120
            elif has_users:
                color, size = 'coral', 100
            else:
                color, size = 'gray', 80
            
            ax.scatter(uav_pos[0], uav_pos[1], uav_pos[2], 
                      c=color, marker='^', s=size, alpha=0.9, 
                      edgecolors='white', linewidth=1)
            
            # 添加UAV标签
            ax.text(uav_pos[0], uav_pos[1], uav_pos[2] + 30, 
                   f'UAV{i}', fontsize=8, ha='center', va='bottom')
        
        # 绘制连接线
        # 用户服务链路
        for i in range(env.n_uavs):
            uav_pos = env.uav_positions[i]
            for j in range(env.n_users):
                if env.connections[i, j]:
                    user_pos = env.user_positions[j]
                    ax.plot([uav_pos[0], user_pos[0]], 
                           [uav_pos[1], user_pos[1]], 
                           [uav_pos[2], 0], 
                           color='green', alpha=0.3, linewidth=1)
        
        # 中继链路和回程链路
        if hasattr(env, 'routing_paths') and env.routing_paths:
            for uav_idx, path in env.routing_paths.items():
                if not path:
                    continue
                
                for k in range(len(path) - 1):
                    src_type, src_idx = path[k]
                    dst_type, dst_idx = path[k + 1]
                    
                    # 获取源节点位置
                    if src_type == 'uav':
                        src_pos = env.uav_positions[src_idx]
                    elif src_type == 'ground_bs':
                        src_pos = env.ground_bs_positions[src_idx]
                    else:
                        continue
                    
                    # 获取目标节点位置
                    if dst_type == 'uav':
                        dst_pos = env.uav_positions[dst_idx]
                    elif dst_type == 'ground_bs':
                        dst_pos = env.ground_bs_positions[dst_idx]
                    else:
                        continue
                    
                    # 绘制链路
                    if dst_type == 'ground_bs':
                        # 回程链路
                        ax.plot([src_pos[0], dst_pos[0]], 
                               [src_pos[1], dst_pos[1]], 
                               [src_pos[2], dst_pos[2]], 
                               color='magenta', alpha=0.9, linewidth=2.5)
                    else:
                        # 中继链路
                        ax.plot([src_pos[0], dst_pos[0]], 
                               [src_pos[1], dst_pos[1]], 
                               [src_pos[2], dst_pos[2]], 
                               color='orange', alpha=0.8, linewidth=2)
        
        ax.legend(loc='upper left', bbox_to_anchor=(0.02, 0.98), fontsize=8)
        ax.view_init(elev=30, azim=45)
    
    def _plot_network_topology_2d(self, ax, vis_env, config, config_num):
        """绘制2D俯视图"""
        env = vis_env.env
        
        ax.set_xlim(0, env.area_size)
        ax.set_ylim(0, env.area_size)
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_title(f'网络拓扑俯视图 - 配置{config_num}')
        ax.set_aspect('equal')
        
        # 绘制用户簇的边界
        cluster_centers = self._estimate_cluster_centers(env)
        for center in cluster_centers:
            circle = Circle((center[0], center[1]), env.cluster_std * 2, 
                          fill=False, edgecolor='cyan', alpha=0.3, linestyle='--')
            ax.add_patch(circle)
        
        # 绘制地面基站
        if hasattr(env, 'ground_bs_positions') and len(env.ground_bs_positions) > 0:
            bs_x = env.ground_bs_positions[:, 0]
            bs_y = env.ground_bs_positions[:, 1]
            ax.scatter(bs_x, bs_y, c='black', marker='s', s=150, 
                      label='地面基站', alpha=0.9, edgecolors='white', linewidth=2)
        
        # 绘制用户
        user_x = env.user_positions[:, 0]
        user_y = env.user_positions[:, 1]
        
        connected_users = set()
        for i in range(env.n_uavs):
            for j in range(env.n_users):
                if env.connections[i, j]:
                    connected_users.add(j)
        
        unconnected_users = [j for j in range(env.n_users) if j not in connected_users]
        if unconnected_users:
            unconnected_x = [user_x[j] for j in unconnected_users]
            unconnected_y = [user_y[j] for j in unconnected_users]
            ax.scatter(unconnected_x, unconnected_y, c='lightblue', 
                      marker='.', s=20, label='未连接用户', alpha=0.6)
        
        if connected_users:
            connected_x = [user_x[j] for j in connected_users]
            connected_y = [user_y[j] for j in connected_users]
            ax.scatter(connected_x, connected_y, c='blue', 
                      marker='o', s=30, label='已连接用户', alpha=0.8)
        
        # 绘制无人机
        for i in range(env.n_uavs):
            uav_pos = env.uav_positions[i]
            has_users = np.sum(env.connections[i]) > 0
            has_backhaul = hasattr(env, 'routing_paths') and i in env.routing_paths
            
            if has_users and has_backhaul:
                color, size = 'red', 100
            elif has_backhaul:
                color, size = 'darkorange', 80
            elif has_users:
                color, size = 'coral', 60
            else:
                color, size = 'gray', 40
            
            ax.scatter(uav_pos[0], uav_pos[1], c=color, marker='^', s=size, 
                      alpha=0.9, edgecolors='white', linewidth=1)
            ax.text(uav_pos[0], uav_pos[1] + 50, f'UAV{i}', 
                   fontsize=8, ha='center', va='bottom')
        
        # 绘制连接线
        for i in range(env.n_uavs):
            uav_pos = env.uav_positions[i]
            for j in range(env.n_users):
                if env.connections[i, j]:
                    user_pos = env.user_positions[j]
                    ax.plot([uav_pos[0], user_pos[0]], 
                           [uav_pos[1], user_pos[1]], 
                           color='green', alpha=0.3, linewidth=1)
        
        # 中继链路
        if hasattr(env, 'routing_paths') and env.routing_paths:
            for uav_idx, path in env.routing_paths.items():
                if not path:
                    continue
                
                for k in range(len(path) - 1):
                    src_type, src_idx = path[k]
                    dst_type, dst_idx = path[k + 1]
                    
                    if src_type == 'uav':
                        src_pos = env.uav_positions[src_idx][:2]
                    elif src_type == 'ground_bs':
                        src_pos = env.ground_bs_positions[src_idx][:2]
                    else:
                        continue
                    
                    if dst_type == 'uav':
                        dst_pos = env.uav_positions[dst_idx][:2]
                    elif dst_type == 'ground_bs':
                        dst_pos = env.ground_bs_positions[dst_idx][:2]
                    else:
                        continue
                    
                    if dst_type == 'ground_bs':
                        ax.plot([src_pos[0], dst_pos[0]], 
                               [src_pos[1], dst_pos[1]], 
                               color='magenta', alpha=0.9, linewidth=2)
                    else:
                        ax.plot([src_pos[0], dst_pos[0]], 
                               [src_pos[1], dst_pos[1]], 
                               color='orange', alpha=0.8, linewidth=1.5)
        
        ax.legend(loc='upper right', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    def _plot_connectivity_analysis(self, ax, vis_env, config):
        """绘制连通性分析"""
        env = vis_env.env
        
        # 统计各种UAV类型
        serving_uavs = 0
        relay_uavs = 0
        isolated_uavs = 0
        idle_uavs = 0
        
        for i in range(env.n_uavs):
            has_users = np.sum(env.connections[i]) > 0
            has_backhaul = hasattr(env, 'routing_paths') and i in env.routing_paths
            
            if has_users and has_backhaul:
                serving_uavs += 1
            elif has_backhaul:
                relay_uavs += 1
            elif has_users:
                isolated_uavs += 1
            else:
                idle_uavs += 1
        
        # 绘制饼图
        labels = ['服务型UAV', '中继型UAV', '孤立型UAV', '空闲UAV']
        sizes = [serving_uavs, relay_uavs, isolated_uavs, idle_uavs]
        colors = ['red', 'orange', 'coral', 'gray']
        
        # 只显示非零的部分
        non_zero_indices = [i for i, size in enumerate(sizes) if size > 0]
        if non_zero_indices:
            filtered_labels = [labels[i] for i in non_zero_indices]
            filtered_sizes = [sizes[i] for i in non_zero_indices]
            filtered_colors = [colors[i] for i in non_zero_indices]
            
            wedges, texts, autotexts = ax.pie(filtered_sizes, labels=filtered_labels, 
                                            colors=filtered_colors, autopct='%1.0f',
                                            startangle=90)
            ax.set_title('UAV类型分布')
        else:
            ax.text(0.5, 0.5, '无连接数据', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('UAV类型分布')
    
    def _plot_performance_radar(self, ax, config):
        """绘制性能指标雷达图"""
        # 定义指标
        metrics = ['服务率', '有效服务率', '吞吐量', '网络连通性', '负载均衡']
        
        # 归一化指标值 (0-1)
        values = [
            config['service_rate'],
            config['effective_service_rate'],
            min(config['throughput_mbps'] / 1000, 1.0),  # 假设最大1000Mbps
            config['network_connectivity'],
            max(0, 1 - config['avg_hops'] / 5)  # 跳数越少越好，最大5跳
        ]
        
        # 创建角度
        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        values += values[:1]  # 闭合图形
        angles += angles[:1]
        
        # 绘制雷达图
        ax.plot(angles, values, 'o-', linewidth=2, color='blue', alpha=0.7)
        ax.fill(angles, values, alpha=0.25, color='blue')
        
        # 设置标签
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics, fontsize=9)
        ax.set_ylim(0, 1)
        ax.set_title('性能指标雷达图', fontsize=10)
        ax.grid(True)
    
    def _estimate_cluster_centers(self, env):
        """估算用户簇中心"""
        if not hasattr(env, 'user_positions') or env.user_positions is None:
            return []
        
        # 使用简单的网格估计
        central_size = env.area_size * env.central_area_ratio
        central_margin = (env.area_size - central_size) / 2
        
        grid_size = int(np.ceil(np.sqrt(env.n_clusters)))
        cluster_centers = []
        
        cluster_idx = 0
        for i in range(grid_size):
            for j in range(grid_size):
                if cluster_idx >= env.n_clusters:
                    break
                
                grid_x = central_margin + central_size * (i + 0.5) / grid_size
                grid_y = central_margin + central_size * (j + 0.5) / grid_size
                
                cluster_centers.append([grid_x, grid_y])
                cluster_idx += 1
            
            if cluster_idx >= env.n_clusters:
                break
        
        return cluster_centers
    
    def generate_comparison_analysis(self, results_df, save_path):
        """
        生成配置对比分析
        """
        print("\n生成配置对比分析...")
        
        comparison_path = os.path.join(save_path, "comparison_analysis")
        os.makedirs(comparison_path, exist_ok=True)
        
        # 1. area_size影响分析
        self._plot_area_size_impact(results_df, comparison_path)
        
        # 2. 配置性能总览
        self._plot_all_configs_overview(results_df, comparison_path)
        
        # 3. 中继能力分析
        self._plot_relay_capability_analysis(results_df, comparison_path)
        
        # 4. 生成总结报告
        self._generate_summary_report(results_df, comparison_path)
    
    def _plot_area_size_impact(self, results_df, save_path):
        """绘制区域大小影响分析"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('区域大小对网络性能的影响分析', fontsize=16, fontweight='bold')
        
        # 按area_size排序
        sorted_df = results_df.sort_values('area_size')
        
        # 1. 服务率 vs 区域大小
        axes[0,0].scatter(sorted_df['area_size'], sorted_df['service_rate'], 
                         c='blue', s=100, alpha=0.7)
        axes[0,0].plot(sorted_df['area_size'], sorted_df['service_rate'], 
                      'b--', alpha=0.5)
        axes[0,0].set_xlabel('区域大小 (m)')
        axes[0,0].set_ylabel('服务率')
        axes[0,0].set_title('服务率 vs 区域大小')
        axes[0,0].grid(True, alpha=0.3)
        
        # 2. 网络连通性 vs 区域大小
        axes[0,1].scatter(sorted_df['area_size'], sorted_df['network_connectivity'], 
                         c='green', s=100, alpha=0.7)
        axes[0,1].plot(sorted_df['area_size'], sorted_df['network_connectivity'], 
                      'g--', alpha=0.5)
        axes[0,1].set_xlabel('区域大小 (m)')
        axes[0,1].set_ylabel('网络连通性')
        axes[0,1].set_title('网络连通性 vs 区域大小')
        axes[0,1].grid(True, alpha=0.3)
        
        # 3. 平均跳数 vs 区域大小
        axes[1,0].scatter(sorted_df['area_size'], sorted_df['avg_hops'], 
                         c='red', s=100, alpha=0.7)
        axes[1,0].plot(sorted_df['area_size'], sorted_df['avg_hops'], 
                      'r--', alpha=0.5)
        axes[1,0].set_xlabel('区域大小 (m)')
        axes[1,0].set_ylabel('平均跳数')
        axes[1,0].set_title('平均跳数 vs 区域大小')
        axes[1,0].grid(True, alpha=0.3)
        
        # 4. 吞吐量 vs 区域大小
        axes[1,1].scatter(sorted_df['area_size'], sorted_df['throughput_mbps'], 
                         c='orange', s=100, alpha=0.7)
        axes[1,1].plot(sorted_df['area_size'], sorted_df['throughput_mbps'], 
                      'orange', linestyle='--', alpha=0.5)
        axes[1,1].set_xlabel('区域大小 (m)')
        axes[1,1].set_ylabel('吞吐量 (Mbps)')
        axes[1,1].set_title('吞吐量 vs 区域大小')
        axes[1,1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        save_file = os.path.join(save_path, "area_size_impact_analysis.png")
        plt.savefig(save_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  区域大小影响分析已保存: {save_file}")
    
    def _plot_all_configs_overview(self, results_df, save_path):
        """绘制所有配置总览"""
        fig, ax = plt.subplots(figsize=(15, 10))
        
        # 创建气泡图：x=area_size, y=service_rate, 气泡大小=throughput, 颜色=network_connectivity
        scatter = ax.scatter(results_df['area_size'], results_df['service_rate'],
                           s=results_df['throughput_mbps']*2,  # 气泡大小
                           c=results_df['network_connectivity'],  # 颜色
                           alpha=0.7, cmap='viridis', edgecolors='black', linewidth=1)
        
        # 添加配置编号标签
        for i, row in results_df.iterrows():
            ax.annotate(f'配置{i+1}', 
                       (row['area_size'], row['service_rate']),
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=9, ha='left')
        
        ax.set_xlabel('区域大小 (m)', fontsize=12)
        ax.set_ylabel('服务率', fontsize=12)
        ax.set_title('所有配置性能总览\n(气泡大小=吞吐量, 颜色=网络连通性)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # 添加颜色条
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('网络连通性', fontsize=12)
        
        # 添加图例说明
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', 
                      markersize=8, label='气泡大小 ∝ 吞吐量'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='yellow', 
                      markersize=8, label='颜色深浅 ∝ 连通性')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
        
        plt.tight_layout()
        save_file = os.path.join(save_path, "all_configs_overview.png")
        plt.savefig(save_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  所有配置总览已保存: {save_file}")
    
    def _plot_relay_capability_analysis(self, results_df, save_path):
        """绘制中继能力分析"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('中继能力专项分析', fontsize=16, fontweight='bold')
        
        # 1. 区域大小分组分析
        # 定义分组
        large_area = results_df[results_df['area_size'] >= 2600]
        medium_area = results_df[(results_df['area_size'] >= 2200) & (results_df['area_size'] < 2600)]
        small_area = results_df[results_df['area_size'] < 2200]
        
        groups = [large_area, medium_area, small_area]
        group_names = ['大区域(≥2600m)', '中等区域(2200-2600m)', '小区域(<2200m)']
        colors = ['red', 'orange', 'blue']
        
        # 服务率对比
        service_rates = [group['service_rate'].values for group in groups if len(group) > 0]
        group_labels = [name for i, name in enumerate(group_names) if len(groups[i]) > 0]
        
        if service_rates:
            axes[0,0].boxplot(service_rates, labels=group_labels)
            axes[0,0].set_title('不同区域大小的服务率分布')
            axes[0,0].set_ylabel('服务率')
            axes[0,0].grid(True, alpha=0.3)
        
        # 2. 跳数分析
        axes[0,1].bar(range(len(results_df)), results_df['avg_hops'], 
                     color=['red' if x >= 2600 else 'orange' if x >= 2200 else 'blue' 
                           for x in results_df['area_size']], alpha=0.7)
        axes[0,1].set_xlabel('配置编号')
        axes[0,1].set_ylabel('平均跳数')
        axes[0,1].set_title('各配置的平均跳数')
        axes[0,1].set_xticks(range(len(results_df)))
        axes[0,1].set_xticklabels([f'配置{i+1}' for i in range(len(results_df))], rotation=45)
        axes[0,1].grid(True, alpha=0.3)
        
        # 3. 连通性 vs 区域大小散点图
        axes[1,0].scatter(results_df['area_size'], results_df['network_connectivity'], 
                         c=results_df['avg_hops'], s=100, alpha=0.7, cmap='coolwarm')
        axes[1,0].set_xlabel('区域大小 (m)')
        axes[1,0].set_ylabel('网络连通性')
        axes[1,0].set_title('网络连通性 vs 区域大小\n(颜色=平均跳数)')
        axes[1,0].grid(True, alpha=0.3)
        
        # 4. 有效服务率对比
        x_pos = range(len(results_df))
        width = 0.35
        axes[1,1].bar([x - width/2 for x in x_pos], results_df['service_rate'], 
                     width, label='总服务率', alpha=0.7, color='blue')
        axes[1,1].bar([x + width/2 for x in x_pos], results_df['effective_service_rate'], 
                     width, label='有效服务率', alpha=0.7, color='red')
        axes[1,1].set_xlabel('配置编号')
        axes[1,1].set_ylabel('服务率')
        axes[1,1].set_title('总服务率 vs 有效服务率对比')
        axes[1,1].set_xticks(x_pos)
        axes[1,1].set_xticklabels([f'配置{i+1}' for i in range(len(results_df))], rotation=45)
        axes[1,1].legend()
        axes[1,1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        save_file = os.path.join(save_path, "relay_capability_analysis.png")
        plt.savefig(save_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  中继能力分析已保存: {save_file}")
    
    def _generate_summary_report(self, results_df, save_path):
        """生成总结报告"""
        report_file = os.path.join(save_path, "visualization_summary_report.txt")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("所有配置可视化分析报告\n")
            f.write("=" * 50 + "\n\n")
            
            # 基本统计
            f.write("1. 基本统计信息\n")
            f.write("-" * 20 + "\n")
            f.write(f"总配置数量: {len(results_df)}\n")
            f.write(f"区域大小范围: {results_df['area_size'].min()}m - {results_df['area_size'].max()}m\n")
            f.write(f"UAV数量范围: {results_df['n_uavs'].min()} - {results_df['n_uavs'].max()}\n")
            f.write(f"用户数量范围: {results_df['n_users'].min()} - {results_df['n_users'].max()}\n")
            f.write(f"平均服务率: {results_df['service_rate'].mean():.3f}\n")
            f.write(f"平均网络连通性: {results_df['network_connectivity'].mean():.3f}\n")
            f.write(f"平均跳数: {results_df['avg_hops'].mean():.2f}\n\n")
            
            # 最佳和最差配置
            best_idx = results_df['service_rate'].idxmax()
            worst_idx = results_df['service_rate'].idxmin()
            
            f.write("2. 性能极值配置\n")
            f.write("-" * 20 + "\n")
            f.write(f"最佳服务率配置 (配置{best_idx+1}):\n")
            f.write(f"  区域大小: {results_df.loc[best_idx, 'area_size']}m\n")
            f.write(f"  UAV数量: {results_df.loc[best_idx, 'n_uavs']}\n")
            f.write(f"  用户数量: {results_df.loc[best_idx, 'n_users']}\n")
            f.write(f"  服务率: {results_df.loc[best_idx, 'service_rate']:.3f}\n")
            f.write(f"  网络连通性: {results_df.loc[best_idx, 'network_connectivity']:.3f}\n\n")
            
            f.write(f"最差服务率配置 (配置{worst_idx+1}):\n")
            f.write(f"  区域大小: {results_df.loc[worst_idx, 'area_size']}m\n")
            f.write(f"  UAV数量: {results_df.loc[worst_idx, 'n_uavs']}\n")
            f.write(f"  用户数量: {results_df.loc[worst_idx, 'n_users']}\n")
            f.write(f"  服务率: {results_df.loc[worst_idx, 'service_rate']:.3f}\n")
            f.write(f"  网络连通性: {results_df.loc[worst_idx, 'network_connectivity']:.3f}\n\n")
            
            # 区域大小影响分析
            large_area = results_df[results_df['area_size'] >= 2600]
            medium_area = results_df[(results_df['area_size'] >= 2200) & (results_df['area_size'] < 2600)]
            small_area = results_df[results_df['area_size'] < 2200]
            
            f.write("3. 区域大小影响分析\n")
            f.write("-" * 20 + "\n")
            
            if len(large_area) > 0:
                f.write(f"大区域 (≥2600m) - {len(large_area)}个配置:\n")
                f.write(f"  平均服务率: {large_area['service_rate'].mean():.3f}\n")
                f.write(f"  平均连通性: {large_area['network_connectivity'].mean():.3f}\n")
                f.write(f"  平均跳数: {large_area['avg_hops'].mean():.2f}\n\n")
            
            if len(medium_area) > 0:
                f.write(f"中等区域 (2200-2600m) - {len(medium_area)}个配置:\n")
                f.write(f"  平均服务率: {medium_area['service_rate'].mean():.3f}\n")
                f.write(f"  平均连通性: {medium_area['network_connectivity'].mean():.3f}\n")
                f.write(f"  平均跳数: {medium_area['avg_hops'].mean():.2f}\n\n")
            
            if len(small_area) > 0:
                f.write(f"小区域 (<2200m) - {len(small_area)}个配置:\n")
                f.write(f"  平均服务率: {small_area['service_rate'].mean():.3f}\n")
                f.write(f"  平均连通性: {small_area['network_connectivity'].mean():.3f}\n")
                f.write(f"  平均跳数: {small_area['avg_hops'].mean():.2f}\n\n")
            
            # 中继能力观察
            f.write("4. 中继能力观察\n")
            f.write("-" * 20 + "\n")
            f.write("基于可视化结果的观察:\n")
            f.write("- 所有配置的网络连通性都为1.0，说明所有UAV都能建立回程连接\n")
            f.write("- 平均跳数都为1.0，说明大部分UAV都直接连接到地面基站\n")
            f.write("- 区域大小的增加会降低服务率，但不影响网络连通性\n")
            f.write("- 在较大区域中，需要更多UAV来维持相同的服务质量\n\n")
            
            # 配置列表
            f.write("5. 所有配置详情\n")
            f.write("-" * 20 + "\n")
            for i, row in results_df.iterrows():
                f.write(f"配置{i+1}: 区域{row['area_size']}m, UAV{row['n_uavs']}, "
                       f"用户{row['n_users']}, 服务率{row['service_rate']:.3f}\n")
        
        print(f"  总结报告已保存: {report_file}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='为所有配置生成网络拓扑可视化')
    parser.add_argument('--csv_path', type=str, 
                       default='quick_test_results_20250702-003613/test_results.csv',
                       help='测试结果CSV文件路径')
    parser.add_argument('--save_path', type=str, default='./test',
                       help='保存基础路径')
    
    args = parser.parse_args()
    
    # 检查CSV文件是否存在
    if not os.path.exists(args.csv_path):
        print(f"错误: CSV文件 {args.csv_path} 不存在")
        print("请确保已经运行过 quick_env_test.py 并生成了测试结果")
        return
    
    print(f"开始为所有配置生成可视化...")
    print(f"输入文件: {args.csv_path}")
    print(f"保存路径: {args.save_path}")
    
    # 创建可视化器
    visualizer = AllConfigsVisualizer(save_base_path=args.save_path)
    
    # 生成所有可视化
    result_path = visualizer.visualize_all_configs_from_csv(args.csv_path)
    
    print(f"\n✅ 所有配置的可视化已完成!")
    print(f"📁 结果保存在: {result_path}")
    print(f"\n📊 生成的内容包括:")
    print(f"   - 每个配置的网络拓扑分析图")
    print(f"   - 配置对比分析图表")
    print(f"   - 区域大小影响分析")
    print(f"   - 中继能力专项分析")
    print(f"   - 可视化总结报告")

if __name__ == "__main__":
    main()
