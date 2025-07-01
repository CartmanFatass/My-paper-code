#!/usr/bin/env python3
"""
多种子环境参数验证工具

允许用户指定特定的环境参数，在多个不同的随机种子下运行测试，
以验证参数配置的稳定性和合理性。
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
from datetime import datetime
from tqdm import tqdm
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import Circle

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from envs.pettingzoo.scenario3 import UAVMultiHopEnv
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from visualize_all_configs import AllConfigsVisualizer

class UniformUAVInitializer:
    """均匀分布的无人机初始化器"""
    
    @staticmethod
    def create_uniform_positions(n_uavs, area_size, height_range, seed=None):
        if seed is not None:
            np.random.seed(seed)
        
        grid_size = int(np.ceil(np.sqrt(n_uavs)))
        positions = []
        margin = area_size * 0.1
        effective_area = area_size - 2 * margin
        
        for i in range(n_uavs):
            grid_x = i % grid_size
            grid_y = i // grid_size
            
            x = margin + (grid_x + 0.5) * effective_area / grid_size
            y = margin + (grid_y + 0.5) * effective_area / grid_size
            
            x += np.random.uniform(-effective_area/(grid_size*4), effective_area/(grid_size*4))
            y += np.random.uniform(-effective_area/(grid_size*4), effective_area/(grid_size*4))
            
            x = np.clip(x, margin, area_size - margin)
            y = np.clip(y, margin, area_size - margin)
            z = np.random.uniform(*height_range)
            
            positions.append([x, y, z])
        
        return np.array(positions)

class EnhancedConnectionVisualizer:
    """
    增强的连接可视化器
    
    参考 visualize_evaluation.py 的可视化方法
    """
    
    def __init__(self, save_path=None):
        """
        初始化可视化器
        
        参数:
            save_path: 图像保存路径
        """
        self.save_path = save_path
        
        # 可视化配置
        self.link_colors = {
            'user_service': 'green',      # 用户服务链路
            'uav_relay': 'orange',        # 无人机中继链路
            'backhaul': 'magenta',        # 回程链路
            'ground_bs': 'black'          # 地面基站
        }
        
        self.link_styles = {
            'user_service': {'alpha': 0.3, 'linewidth': 1},
            'uav_relay': {'alpha': 0.8, 'linewidth': 2},
            'backhaul': {'alpha': 0.9, 'linewidth': 2.5}
        }
        
        # 配置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
    
    def create_connection_snapshot(self, env, seed, step, config_params, metrics=None):
        """
        创建连接状态快照
        
        参数:
            env: 环境实例
            seed: 当前种子
            step: 当前步数
            config_params: 配置参数
            metrics: 性能指标
        
        返回:
            figure: matplotlib图形对象
        """
        try:
            fig = plt.figure(figsize=(16, 12))
            ax = fig.add_subplot(111, projection='3d')
            
            # 设置坐标轴
            ax.set_xlim(0, env.env.area_size)
            ax.set_ylim(0, env.env.area_size)
            ax.set_zlim(0, 250)
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            ax.set_zlabel('Z (m)')
            
            # 设置标题
            title = f'多种子分析 - 连接状态快照\n'
            title += f'种子: {seed} | 步数: {step} | '
            title += f'UAV: {config_params["n_uavs"]} | 用户: {config_params["n_users"]}'
            
            if metrics:
                title += f'\n服务率: {metrics.get("service_rate", 0):.3f} | '
                title += f'连通性: {metrics.get("network_connectivity", 0):.3f} | '
                title += f'吞吐量: {metrics.get("throughput_mbps", 0):.1f} Mbps'
            
            ax.set_title(title, fontsize=14, pad=20)
            
            # 1. 绘制地面基站
            if hasattr(env.env, 'ground_bs_positions') and len(env.env.ground_bs_positions) > 0:
                bs_x = env.env.ground_bs_positions[:, 0]
                bs_y = env.env.ground_bs_positions[:, 1]
                bs_z = env.env.ground_bs_positions[:, 2]
                ax.scatter(bs_x, bs_y, bs_z, 
                          c=self.link_colors['ground_bs'], 
                          marker='s', s=200, 
                          label='地面基站', alpha=0.9, edgecolors='white', linewidth=2)
            
            # 2. 绘制用户
            user_x = env.env.user_positions[:, 0]
            user_y = env.env.user_positions[:, 1]
            user_z = np.zeros(env.env.n_users)  # 用户在地面
            
            # 区分已连接和未连接的用户
            connected_users = set()
            for i in range(env.env.n_uavs):
                for j in range(env.env.n_users):
                    if env.env.connections[i, j]:
                        connected_users.add(j)
            
            # 绘制未连接用户
            unconnected_users = [j for j in range(env.env.n_users) if j not in connected_users]
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
            
            # 3. 绘制无人机
            uav_colors = []
            uav_sizes = []
            uav_labels = []
            
            for i in range(env.env.n_uavs):
                # 根据无人机的连接状态确定颜色和大小
                has_users = np.sum(env.env.connections[i]) > 0
                has_backhaul = hasattr(env.env, 'routing_paths') and i in env.env.routing_paths
                
                if has_users and has_backhaul:
                    # 既有用户连接又有回程路径
                    uav_colors.append('red')
                    uav_sizes.append(150)
                    uav_labels.append('服务型UAV')
                elif has_backhaul:
                    # 只有回程路径，作为中继
                    uav_colors.append('darkorange')
                    uav_sizes.append(120)
                    uav_labels.append('中继型UAV')
                elif has_users:
                    # 只有用户连接，没有回程
                    uav_colors.append('coral')
                    uav_sizes.append(100)
                    uav_labels.append('孤立型UAV')
                else:
                    # 既没有用户也没有回程
                    uav_colors.append('gray')
                    uav_sizes.append(80)
                    uav_labels.append('空闲UAV')
            
            for i in range(env.env.n_uavs):
                uav_pos = env.env.uav_positions[i]
                ax.scatter(uav_pos[0], uav_pos[1], uav_pos[2], 
                          c=uav_colors[i], marker='^', s=uav_sizes[i], 
                          alpha=0.9, edgecolors='white', linewidth=1)
                
                # 添加无人机编号标签
                ax.text(uav_pos[0], uav_pos[1], uav_pos[2] + 20, 
                        f'UAV{i}', fontsize=8, ha='center', va='bottom',
                        bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8, edgecolor='gray'))
            
            # 4. 绘制用户服务链路
            for i in range(env.env.n_uavs):
                uav_pos = env.env.uav_positions[i]
                for j in range(env.env.n_users):
                    if env.env.connections[i, j]:
                        user_pos = env.env.user_positions[j]
                        ax.plot([uav_pos[0], user_pos[0]], 
                               [uav_pos[1], user_pos[1]], 
                               [uav_pos[2], 0], 
                               color=self.link_colors['user_service'],
                               **self.link_styles['user_service'])
            
            # 5. 绘制无人机中继链路和回程链路
            if hasattr(env.env, 'routing_paths'):
                self._draw_routing_paths(ax, env)
            
            # 6. 添加图例
            handles, labels = ax.get_legend_handles_labels()
            
            # 添加UAV类型的图例
            uav_legend_elements = []
            unique_labels = list(set(uav_labels))
            for label in unique_labels:
                idx = uav_labels.index(label)
                color = uav_colors[idx]
                handle = plt.Line2D([0], [0], marker='^', color='w', 
                                  markerfacecolor=color, markersize=8, 
                                  markeredgecolor='white', markeredgewidth=1)
                uav_legend_elements.append((handle, label))
            
            # 添加链路类型的图例
            link_legend_elements = [
                (plt.Line2D([0], [0], color=self.link_colors['user_service'], 
                           linewidth=2, alpha=0.7), '用户服务链路'),
                (plt.Line2D([0], [0], color=self.link_colors['uav_relay'], 
                           linewidth=3, alpha=0.8), '无人机中继链路'),
                (plt.Line2D([0], [0], color=self.link_colors['backhaul'], 
                           linewidth=3, alpha=0.9), '回程链路')
            ]
            
            # 合并所有图例元素
            all_handles = handles + [h for h, l in uav_legend_elements] + [h for h, l in link_legend_elements]
            all_labels = labels + [l for h, l in uav_legend_elements] + [l for h, l in link_legend_elements]
            
            # 创建图例
            legend = ax.legend(all_handles, all_labels, 
                               loc='upper left', bbox_to_anchor=(0.02, 0.98),
                               ncol=1, fontsize=9, framealpha=0.9)
            
            # 7. 添加详细统计信息
            self._add_statistics_text(ax, env, metrics)
            
            # 8. 设置视角
            ax.view_init(elev=30, azim=45)
            
            plt.tight_layout()
            
            # 保存图像到文件（如果设置了保存路径）
            if self.save_path is not None:
                filename = f"connection_snapshot_seed{seed}_step{step}.png"
                save_file_path = os.path.join(self.save_path, filename)
                fig.savefig(save_file_path, dpi=150, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
                print(f"    连接快照已保存: {filename}")
            
            return fig
            
        except Exception as e:
            print(f"    创建连接快照失败: {e}")
            return None
    
    def _draw_routing_paths(self, ax, env):
        """
        绘制路由路径（中继链路和回程链路）
        """
        if not hasattr(env.env, 'routing_paths'):
            return
        
        routing_paths = env.env.routing_paths
        
        if not routing_paths:
            return
        
        for uav_idx, path in routing_paths.items():
            if not path:
                continue
            
            # 绘制路径中的每一段链路
            for i in range(len(path) - 1):
                src_type, src_idx = path[i]
                dst_type, dst_idx = path[i + 1]
                
                # 获取源节点位置
                if src_type == 'uav':
                    src_pos = env.env.uav_positions[src_idx]
                elif src_type == 'ground_bs':
                    src_pos = env.env.ground_bs_positions[src_idx]
                else:
                    continue
                
                # 获取目标节点位置
                if dst_type == 'uav':
                    dst_pos = env.env.uav_positions[dst_idx]
                elif dst_type == 'ground_bs':
                    dst_pos = env.env.ground_bs_positions[dst_idx]
                else:
                    continue
                
                # 确定链路类型和样式
                if dst_type == 'ground_bs':
                    # 到地面基站的链路 - 回程链路
                    link_color = self.link_colors['backhaul']
                    link_style = self.link_styles['backhaul']
                else:
                    # UAV到UAV的链路 - 中继链路
                    link_color = self.link_colors['uav_relay']
                    link_style = self.link_styles['uav_relay']
                
                # 绘制链路
                ax.plot([src_pos[0], dst_pos[0]], 
                       [src_pos[1], dst_pos[1]], 
                       [src_pos[2], dst_pos[2]], 
                       color=link_color, **link_style)
    
    def _add_statistics_text(self, ax, env, metrics):
        """
        添加详细的统计信息文本
        """
        if not metrics:
            return
        
        # 计算统计信息
        total_connections = np.sum(env.env.connections)
        coverage_ratio = total_connections / env.env.n_users
        
        # 统计UAV类型
        serving_uavs = 0
        relay_uavs = 0
        isolated_uavs = 0
        idle_uavs = 0
        
        for i in range(env.env.n_uavs):
            has_users = np.sum(env.env.connections[i]) > 0
            has_backhaul = hasattr(env.env, 'routing_paths') and i in env.env.routing_paths
            
            if has_users and has_backhaul:
                serving_uavs += 1
            elif has_backhaul:
                relay_uavs += 1
            elif has_users:
                isolated_uavs += 1
            else:
                idle_uavs += 1
        
        # 构建统计文本
        stats_text = f"""连接统计:
总连接数: {total_connections}/{env.env.n_users} ({coverage_ratio:.1%})
有效连接数: {int(metrics.get('effective_service_rate', 0) * env.env.n_users)}
服务型UAV: {serving_uavs}
中继型UAV: {relay_uavs}
孤立型UAV: {isolated_uavs}
空闲UAV: {idle_uavs}
平均跳数: {metrics.get('avg_hops', 0):.2f}
系统吞吐量: {metrics.get('throughput_mbps', 0):.1f} Mbps"""
        
        # 添加文本到图中
        ax.text2D(0.75, 0.95, stats_text, transform=ax.transAxes,
                  fontsize=10, verticalalignment='top',
                  bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8))
    
    def generate_multi_seed_comparison(self, all_seed_data, config_params):
        """
        生成多种子连接状态对比图
        
        参数:
            all_seed_data: 所有种子的数据列表
            config_params: 配置参数
        """
        if not all_seed_data or not self.save_path:
            return
        
        # 选择几个代表性的种子进行对比
        n_seeds = min(6, len(all_seed_data))
        selected_seeds = np.linspace(0, len(all_seed_data)-1, n_seeds, dtype=int)
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12), subplot_kw={'projection': '3d'})
        axes = axes.flatten()
        
        fig.suptitle(f'多种子连接状态对比\n'
                    f'UAV:{config_params["n_uavs"]}, 用户:{config_params["n_users"]}, '
                    f'区域:{config_params["area_size"]}m', 
                    fontsize=16, fontweight='bold')
        
        for i, seed_idx in enumerate(selected_seeds):
            seed_data = all_seed_data[seed_idx]
            ax = axes[i]
            
            # 设置坐标轴
            ax.set_xlim(0, config_params['area_size'])
            ax.set_ylim(0, config_params['area_size'])
            ax.set_zlim(0, 250)
            ax.set_xlabel('X (m)', fontsize=8)
            ax.set_ylabel('Y (m)', fontsize=8)
            ax.set_zlabel('Z (m)', fontsize=8)
            
            # 设置标题
            seed = seed_data['seed']
            service_rate = seed_data['service_rate']
            connectivity = seed_data['network_connectivity']
            
            ax.set_title(f'种子: {seed}\n服务率: {service_rate:.3f}\n连通性: {connectivity:.3f}', 
                        fontsize=10)
            
            # 简化的可视化 - 只显示基本的连接状态
            # 这里需要重新创建环境来获取位置信息，或者事先保存位置数据
            # 为了示例，我们创建一个简化版本
            
            ax.text(0.5, 0.5, 0.5, f'种子 {seed}\n性能数据可视化\n待完善', 
                   transform=ax.transAxes, ha='center', va='center',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))
        
        plt.tight_layout()
        
        # 保存对比图
        comparison_file = os.path.join(self.save_path, "multi_seed_connection_comparison.png")
        plt.savefig(comparison_file, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"  多种子连接对比图已保存: {comparison_file}")

class MultiSeedAnalyzer:
    """多种子参数分析器"""
    
    def __init__(self, max_steps=200, stabilization_steps=50, enable_visualization=True):
        self.max_steps = max_steps
        self.stabilization_steps = stabilization_steps
        self.enable_visualization = enable_visualization
        
        # 配置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 可视化器
        self.visualizer = None
        
        # 存储所有种子的数据用于对比
        self.all_seed_results = []
    
    def analyze_config_multi_seed(self, config_params, seeds, save_path=None):
        """
        在多个种子下分析单个配置的性能
        
        参数:
            config_params: 配置参数字典
            seeds: 种子列表
            save_path: 保存路径
            
        返回:
            results_df: 结果DataFrame
            stats: 统计信息
        """
        print(f"\n开始多种子分析配置:")
        print(f"  UAV数量: {config_params['n_uavs']}")
        print(f"  用户数量: {config_params['n_users']}")
        print(f"  区域大小: {config_params['area_size']}m")
        print(f"  用户簇数量: {config_params['n_clusters']}")
        print(f"  测试种子: {len(seeds)}个")
        
        results = []
        
        for i, seed in enumerate(tqdm(seeds, desc="种子测试进度")):
            print(f"\n[{i+1}/{len(seeds)}] 测试种子: {seed}")
            
            # 设置当前种子
            test_config = config_params.copy()
            test_config['seed'] = seed
            
            # 评估当前种子下的性能
            result = self._evaluate_single_seed(test_config, save_path)
            if result:
                result['seed'] = seed
                result['run_id'] = i + 1
                results.append(result)
        
        if not results:
            print("错误: 没有成功完成任何测试")
            return None, None
        
        # 转换为DataFrame
        results_df = pd.DataFrame(results)
        
        # 计算统计信息
        stats = self._calculate_statistics(results_df)
        
        # 生成分析报告和图表
        if save_path:
            self._generate_multi_seed_report(config_params, results_df, stats, save_path)
            self._generate_multi_seed_plots(config_params, results_df, stats, save_path)
            
            # 生成多种子连接状态对比可视化
            if self.enable_visualization and self.visualizer:
                print("  生成多种子连接状态对比图...")
                self.visualizer.generate_multi_seed_comparison(self.all_seed_results, config_params)
        
        return results_df, stats
    
    def _evaluate_single_seed(self, config_params, save_path=None):
        """评估单个种子下的配置性能"""
        try:
            # 创建环境
            raw_env = UAVMultiHopEnv(
                n_uavs=config_params['n_uavs'],
                n_users=config_params['n_users'],
                area_size=config_params['area_size'],
                max_hops=config_params.get('max_hops', 5),
                user_distribution=config_params.get('user_distribution', 'multi_cluster'),
                channel_model=config_params.get('channel_model', 'probabilistic'),
                render_mode=None,
                seed=config_params['seed'],
                n_clusters=config_params.get('n_clusters', 4),
                cluster_std=config_params.get('cluster_std', 120),
                central_area_ratio=config_params.get('central_area_ratio', 0.6),
                use_fdma=config_params.get('use_fdma', True),
                bandwidth=config_params.get('bandwidth', 20e6),
            )
            
            adapted_env = ParallelToArrayAdapter(raw_env, seed=config_params['seed'])
            
            # 初始化可视化器（如果启用）
            if self.enable_visualization and save_path:
                if not self.visualizer:
                    self.visualizer = EnhancedConnectionVisualizer(save_path)
            
            # 初始化性能记录
            performance_history = {
                'service_rate': [],
                'effective_service_rate': [],
                'throughput_mbps': [],
                'network_connectivity': [],
                'avg_hops': [],
                'reward': []
            }
            
            # 重置环境
            obs, info = adapted_env.reset()
            
            # 设置均匀分布的无人机位置
            uniform_positions = UniformUAVInitializer.create_uniform_positions(
                config_params['n_uavs'], 
                config_params['area_size'], 
                (50, 200),
                seed=config_params['seed']
            )
            adapted_env.env.uav_positions = uniform_positions
            
            # 更新初始状态
            adapted_env.env._update_channel_state()
            if hasattr(adapted_env.env, '_update_uav_connections'):
                adapted_env.env._update_uav_connections()
            if hasattr(adapted_env.env, '_compute_routing_paths'):
                adapted_env.env._compute_routing_paths()
            
            # 生成初始状态快照
            if self.enable_visualization and self.visualizer:
                initial_metrics = self._extract_metrics(adapted_env)
                print(f"    生成初始状态快照...")
                fig = self.visualizer.create_connection_snapshot(
                    adapted_env, config_params['seed'], 0, config_params, initial_metrics
                )
                if fig:
                    plt.close(fig)  # 关闭图形以释放内存
            
            # 运行评估
            snapshot_steps = [self.max_steps // 4, self.max_steps // 2, 3 * self.max_steps // 4, self.max_steps - 1]
            
            for step in range(self.max_steps):
                # 使用简单的随机动作
                actions = self._generate_simple_actions(adapted_env, config_params['n_uavs'])
                
                # 执行步骤
                next_obs, reward, done, truncated, info = adapted_env.step(actions)
                
                # 记录性能指标
                metrics = self._extract_metrics(adapted_env)
                for key, value in metrics.items():
                    performance_history[key].append(value)
                
                # 在关键步骤生成快照
                if self.enable_visualization and self.visualizer and step in snapshot_steps:
                    print(f"    生成步骤 {step} 快照...")
                    fig = self.visualizer.create_connection_snapshot(
                        adapted_env, config_params['seed'], step, config_params, metrics
                    )
                    if fig:
                        plt.close(fig)  # 关闭图形以释放内存
                
                obs = next_obs
                
                if done or truncated:
                    break
            
            # 计算稳态性能
            stable_metrics = self._compute_stable_metrics(performance_history)
            
            # 存储用于对比的数据
            seed_result_data = stable_metrics.copy()
            seed_result_data['seed'] = config_params['seed']
            self.all_seed_results.append(seed_result_data)
            
            # 清理环境
            adapted_env.close()
            
            return stable_metrics
            
        except Exception as e:
            print(f"种子 {config_params['seed']} 评估失败: {e}")
            return None
    
    def _generate_simple_actions(self, env, n_uavs):
        """生成简单的动作"""
        actions = []
        for i in range(n_uavs):
            action = np.random.uniform(-0.2, 0.2, 3)
            actions.append(action)
        return np.array(actions)
    
    def _extract_metrics(self, env):
        """提取性能指标"""
        metrics = {}
        
        # 基本连接信息
        total_connections = np.sum(env.env.connections)
        metrics['service_rate'] = total_connections / env.env.n_users
        
        # 有效连接
        effective_connections = 0
        if hasattr(env.env, 'routing_paths'):
            for i in range(env.env.n_uavs):
                if i in env.env.routing_paths:
                    effective_connections += np.sum(env.env.connections[i])
        
        metrics['effective_service_rate'] = effective_connections / env.env.n_users
        
        # 网络连通性
        if hasattr(env.env, 'routing_paths'):
            connected_uavs = len(env.env.routing_paths)
            metrics['network_connectivity'] = connected_uavs / env.env.n_uavs
        else:
            metrics['network_connectivity'] = 0
        
        # 平均跳数
        if hasattr(env.env, 'routing_paths') and env.env.routing_paths:
            total_hops = sum(len(path) - 1 for path in env.env.routing_paths.values())
            metrics['avg_hops'] = total_hops / len(env.env.routing_paths)
        else:
            metrics['avg_hops'] = 0
        
        # 系统吞吐量
        system_throughput = 0
        for i in range(env.env.n_uavs):
            if i in getattr(env.env, 'routing_paths', {}):
                connected_users = np.sum(env.env.connections[i])
                if connected_users > 0:
                    avg_sinr = np.mean([env.env.sinr_matrix[i, j] for j in range(env.env.n_users) 
                                      if env.env.connections[i, j]])
                    sinr_linear = 10 ** (avg_sinr / 10)
                    capacity_per_user = (env.env.bandwidth / connected_users) * np.log2(1 + sinr_linear)
                    system_throughput += capacity_per_user * connected_users
        
        metrics['throughput_mbps'] = system_throughput / 1e6
        
        # 奖励
        if hasattr(env.env, 'reward_info') and env.env.reward_info:
            metrics['reward'] = env.env.reward_info.get('final_reward', 0)
        else:
            metrics['reward'] = 0
        
        return metrics
    
    def _compute_stable_metrics(self, performance_history):
        """计算稳态性能指标"""
        stable_metrics = {}
        start_idx = max(0, len(performance_history['service_rate']) // 2)
        
        for key, values in performance_history.items():
            if len(values) > start_idx:
                stable_values = values[start_idx:]
                stable_metrics[key] = np.mean(stable_values)
                stable_metrics[f'{key}_std'] = np.std(stable_values)
            else:
                stable_metrics[key] = 0
                stable_metrics[f'{key}_std'] = 0
        
        return stable_metrics
    
    def _calculate_statistics(self, results_df):
        """计算多种子统计信息"""
        key_metrics = ['service_rate', 'effective_service_rate', 'throughput_mbps', 
                      'network_connectivity', 'avg_hops', 'reward']
        
        stats = {}
        for metric in key_metrics:
            if metric in results_df.columns:
                stats[metric] = {
                    'mean': results_df[metric].mean(),
                    'std': results_df[metric].std(),
                    'min': results_df[metric].min(),
                    'max': results_df[metric].max(),
                    'cv': results_df[metric].std() / results_df[metric].mean() if results_df[metric].mean() > 0 else float('inf')
                }
        
        return stats
    
    def _generate_multi_seed_report(self, config_params, results_df, stats, save_path):
        """生成多种子分析报告"""
        report_file = os.path.join(save_path, "multi_seed_analysis_report.txt")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("多种子环境参数验证报告\n")
            f.write("=" * 50 + "\n\n")
            
            # 配置信息
            f.write("1. 测试配置\n")
            f.write("-" * 20 + "\n")
            f.write(f"UAV数量: {config_params['n_uavs']}\n")
            f.write(f"用户数量: {config_params['n_users']}\n")
            f.write(f"区域大小: {config_params['area_size']}m\n")
            f.write(f"用户簇数量: {config_params['n_clusters']}\n")
            f.write(f"最大跳数: {config_params.get('max_hops', 5)}\n")
            f.write(f"用户分布: {config_params.get('user_distribution', 'multi_cluster')}\n")
            f.write(f"信道模型: {config_params.get('channel_model', 'probabilistic')}\n")
            f.write(f"测试种子数量: {len(results_df)}\n\n")
            
            # 性能统计
            f.write("2. 性能统计 (所有种子)\n")
            f.write("-" * 20 + "\n")
            key_metrics = ['service_rate', 'effective_service_rate', 'throughput_mbps', 
                          'network_connectivity', 'avg_hops', 'reward']
            
            for metric in key_metrics:
                if metric in stats:
                    stat = stats[metric]
                    f.write(f"{metric}:\n")
                    f.write(f"  平均值: {stat['mean']:.4f}\n")
                    f.write(f"  标准差: {stat['std']:.4f}\n")
                    f.write(f"  最小值: {stat['min']:.4f}\n")
                    f.write(f"  最大值: {stat['max']:.4f}\n")
                    f.write(f"  变异系数: {stat['cv']:.4f}\n\n")
            
            # 稳定性分析
            f.write("3. 稳定性分析\n")
            f.write("-" * 20 + "\n")
            
            # 变异系数分析
            cv_thresholds = {'低': 0.1, '中': 0.2, '高': float('inf')}
            for metric in ['service_rate', 'effective_service_rate', 'network_connectivity']:
                if metric in stats:
                    cv = stats[metric]['cv']
                    stability = next(level for level, thresh in cv_thresholds.items() if cv <= thresh)
                    f.write(f"{metric} 稳定性: {stability} (CV={cv:.4f})\n")
            
            f.write(f"\n")
            
            # 异常值检测
            f.write("4. 异常值检测\n")
            f.write("-" * 20 + "\n")
            for metric in ['service_rate', 'effective_service_rate']:
                if metric in results_df.columns:
                    mean_val = results_df[metric].mean()
                    std_val = results_df[metric].std()
                    outliers = results_df[(results_df[metric] < mean_val - 2*std_val) | 
                                        (results_df[metric] > mean_val + 2*std_val)]
                    if len(outliers) > 0:
                        f.write(f"{metric} 异常种子: {list(outliers['seed'].values)}\n")
                    else:
                        f.write(f"{metric} 无异常值\n")
            
            f.write(f"\n")
            
            # 推荐建议
            f.write("5. 推荐建议\n")
            f.write("-" * 20 + "\n")
            
            service_rate_cv = stats.get('service_rate', {}).get('cv', float('inf'))
            connectivity_cv = stats.get('network_connectivity', {}).get('cv', float('inf'))
            
            if service_rate_cv < 0.1 and connectivity_cv < 0.1:
                f.write("✅ 参数配置非常稳定，推荐使用\n")
            elif service_rate_cv < 0.2 and connectivity_cv < 0.2:
                f.write("✅ 参数配置相对稳定，可以使用\n")
            else:
                f.write("⚠️  参数配置稳定性较差，建议调整以下方面:\n")
                if service_rate_cv > 0.2:
                    f.write("   - 增加UAV数量或优化分布\n")
                if connectivity_cv > 0.2:
                    f.write("   - 调整区域大小或UAV密度\n")
        
        print(f"  多种子分析报告已保存: {report_file}")
    
    def _generate_multi_seed_plots(self, config_params, results_df, stats, save_path):
        """生成多种子分析图表"""
        # 创建图表
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(f'多种子参数验证分析\n'
                    f'UAV:{config_params["n_uavs"]}, 用户:{config_params["n_users"]}, '
                    f'区域:{config_params["area_size"]}m', 
                    fontsize=16, fontweight='bold')
        
        # 1. 服务率分布
        axes[0,0].hist(results_df['service_rate'], bins=10, alpha=0.7, color='blue', edgecolor='black')
        axes[0,0].axvline(results_df['service_rate'].mean(), color='red', linestyle='--', 
                         label=f'均值: {results_df["service_rate"].mean():.3f}')
        axes[0,0].set_xlabel('服务率')
        axes[0,0].set_ylabel('频次')
        axes[0,0].set_title('服务率分布')
        axes[0,0].legend()
        axes[0,0].grid(True, alpha=0.3)
        
        # 2. 网络连通性分布
        axes[0,1].hist(results_df['network_connectivity'], bins=10, alpha=0.7, color='green', edgecolor='black')
        axes[0,1].axvline(results_df['network_connectivity'].mean(), color='red', linestyle='--',
                         label=f'均值: {results_df["network_connectivity"].mean():.3f}')
        axes[0,1].set_xlabel('网络连通性')
        axes[0,1].set_ylabel('频次')
        axes[0,1].set_title('网络连通性分布')
        axes[0,1].legend()
        axes[0,1].grid(True, alpha=0.3)
        
        # 3. 吞吐量分布
        axes[0,2].hist(results_df['throughput_mbps'], bins=10, alpha=0.7, color='orange', edgecolor='black')
        axes[0,2].axvline(results_df['throughput_mbps'].mean(), color='red', linestyle='--',
                         label=f'均值: {results_df["throughput_mbps"].mean():.1f}Mbps')
        axes[0,2].set_xlabel('吞吐量 (Mbps)')
        axes[0,2].set_ylabel('频次')
        axes[0,2].set_title('吞吐量分布')
        axes[0,2].legend()
        axes[0,2].grid(True, alpha=0.3)
        
        # 4. 种子vs性能散点图
        axes[1,0].scatter(results_df['seed'], results_df['service_rate'], alpha=0.7, color='blue')
        axes[1,0].set_xlabel('随机种子')
        axes[1,0].set_ylabel('服务率')
        axes[1,0].set_title('种子 vs 服务率')
        axes[1,0].grid(True, alpha=0.3)
        
        # 5. 性能指标箱线图
        metrics_for_box = ['service_rate', 'effective_service_rate', 'network_connectivity']
        box_data = [results_df[metric].values for metric in metrics_for_box if metric in results_df.columns]
        box_labels = [metric.replace('_', '\n') for metric in metrics_for_box if metric in results_df.columns]
        
        if box_data:
            axes[1,1].boxplot(box_data, labels=box_labels)
            axes[1,1].set_ylabel('性能值')
            axes[1,1].set_title('关键指标箱线图')
            axes[1,1].grid(True, alpha=0.3)
        
        # 6. 变异系数对比
        cv_metrics = []
        cv_values = []
        for metric in ['service_rate', 'effective_service_rate', 'throughput_mbps', 'network_connectivity']:
            if metric in stats:
                cv_metrics.append(metric.replace('_', '\n'))
                cv_values.append(stats[metric]['cv'])
        
        if cv_values:
            bars = axes[1,2].bar(cv_metrics, cv_values, alpha=0.7, 
                               color=['red' if cv > 0.2 else 'orange' if cv > 0.1 else 'green' for cv in cv_values])
            axes[1,2].axhline(y=0.1, color='green', linestyle='--', alpha=0.7, label='稳定阈值(0.1)')
            axes[1,2].axhline(y=0.2, color='orange', linestyle='--', alpha=0.7, label='中等阈值(0.2)')
            axes[1,2].set_ylabel('变异系数')
            axes[1,2].set_title('指标稳定性 (变异系数)')
            axes[1,2].legend()
            axes[1,2].grid(True, alpha=0.3)
            
            # 添加数值标签
            for bar, cv in zip(bars, cv_values):
                height = bar.get_height()
                axes[1,2].text(bar.get_x() + bar.get_width()/2., height + 0.01,
                              f'{cv:.3f}', ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        
        # 保存图表
        plot_file = os.path.join(save_path, "multi_seed_analysis_plots.png")
        plt.savefig(plot_file, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"  多种子分析图表已保存: {plot_file}")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='多种子环境参数验证工具')
    
    # 环境参数
    parser.add_argument('--n_uavs', type=int, default=10, help='无人机数量')
    parser.add_argument('--n_users', type=int, default=50, help='用户数量')
    parser.add_argument('--area_size', type=int, default=2400, help='区域大小 (米)')
    parser.add_argument('--n_clusters', type=int, default=4, help='用户簇数量')
    parser.add_argument('--max_hops', type=int, default=5, help='最大跳数')
    parser.add_argument('--user_distribution', type=str, default='multi_cluster',
                       choices=['uniform', 'cluster', 'hotspot', 'multi_cluster'],
                       help='用户分布类型')
    parser.add_argument('--channel_model', type=str, default='probabilistic',
                       choices=['free_space', 'urban', 'suburban', '3gpp-36777', 'probabilistic'],
                       help='信道模型')
    parser.add_argument('--cluster_std', type=int, default=120, help='簇内用户分布标准差 (米)')
    parser.add_argument('--central_area_ratio', type=float, default=0.6, help='中心用户区域比例')
    parser.add_argument('--use_fdma', action='store_true', default=True, help='是否使用FDMA')
    parser.add_argument('--bandwidth', type=float, default=20e6, help='带宽 (Hz)')
    
    # 测试参数
    parser.add_argument('--seeds', type=int, nargs='+', default=None,
                       help='指定测试种子列表，例如: --seeds 42 123 456')
    parser.add_argument('--num_seeds', type=int, default=10, help='随机生成的种子数量')
    parser.add_argument('--seed_start', type=int, default=1, help='种子起始值')
    parser.add_argument('--max_steps', type=int, default=200, help='每次运行的最大步数')
    
    # 输出参数
    parser.add_argument('--save_path', type=str, default='./test', help='结果保存路径')
    parser.add_argument('--experiment_name', type=str, default=None, help='实验名称')
    
    # 可视化参数
    parser.add_argument('--enable_visualization', action='store_true', default=True, 
                       help='启用连接状态可视化快照')
    parser.add_argument('--disable_visualization', action='store_true', 
                       help='禁用连接状态可视化快照')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    print("🔬 多种子环境参数验证工具")
    print("=" * 60)
    
    # 生成或使用指定的种子
    if args.seeds:
        seeds = args.seeds
        print(f"📌 使用指定种子: {seeds}")
    else:
        seeds = list(range(args.seed_start, args.seed_start + args.num_seeds))
        print(f"🎲 生成随机种子: {seeds}")
    
    # 构建配置参数
    config_params = {
        'n_uavs': args.n_uavs,
        'n_users': args.n_users,
        'area_size': args.area_size,
        'n_clusters': args.n_clusters,
        'max_hops': args.max_hops,
        'user_distribution': args.user_distribution,
        'channel_model': args.channel_model,
        'cluster_std': args.cluster_std,
        'central_area_ratio': args.central_area_ratio,
        'use_fdma': args.use_fdma,
        'bandwidth': args.bandwidth,
    }
    
    # 创建保存目录
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if args.experiment_name:
        folder_name = f"multi_seed_{args.experiment_name}_{timestamp}"
    else:
        folder_name = f"multi_seed_uav{args.n_uavs}_usr{args.n_users}_area{args.area_size}_{timestamp}"
    
    save_path = os.path.join(args.save_path, folder_name)
    os.makedirs(save_path, exist_ok=True)
    print(f"💾 结果将保存到: {save_path}")
    
    # 处理可视化参数
    enable_visualization = args.enable_visualization and not args.disable_visualization
    print(f"📸 可视化功能: {'启用' if enable_visualization else '禁用'}")
    
    # 创建分析器
    analyzer = MultiSeedAnalyzer(max_steps=args.max_steps, enable_visualization=enable_visualization)
    
    try:
        # 运行多种子分析
        results_df, stats = analyzer.analyze_config_multi_seed(config_params, seeds, save_path)
        
        if results_df is not None:
            # 保存原始结果
            results_file = os.path.join(save_path, "multi_seed_results.csv")
            results_df.to_csv(results_file, index=False, encoding='utf-8-sig')
            print(f"📊 原始结果已保存: {results_file}")
            
            # 打印摘要
            print("\n" + "=" * 60)
            print("📈 分析结果摘要")
            print("-" * 30)
            print(f"测试种子数量: {len(results_df)}")
            print(f"平均服务率: {stats['service_rate']['mean']:.3f} ± {stats['service_rate']['std']:.3f}")
            print(f"平均网络连通性: {stats['network_connectivity']['mean']:.3f} ± {stats['network_connectivity']['std']:.3f}")
            print(f"平均吞吐量: {stats['throughput_mbps']['mean']:.1f} ± {stats['throughput_mbps']['std']:.1f} Mbps")
            
            # 稳定性评估
            service_cv = stats['service_rate']['cv']
            connectivity_cv = stats['network_connectivity']['cv']
            
            print(f"\n🎯 稳定性评估:")
            print(f"服务率变异系数: {service_cv:.4f}")
            print(f"连通性变异系数: {connectivity_cv:.4f}")
            
            if service_cv < 0.1 and connectivity_cv < 0.1:
                print("✅ 参数配置非常稳定，推荐使用")
            elif service_cv < 0.2 and connectivity_cv < 0.2:
                print("✅ 参数配置相对稳定，可以使用")
            else:
                print("⚠️  参数配置稳定性需要改进")
            
            print(f"\n📁 详细分析结果请查看: {save_path}")
            
        else:
            print("❌ 分析失败，请检查参数设置")
    
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {e}")
        return

if __name__ == "__main__":
    main()
