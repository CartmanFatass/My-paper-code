import os
import time
import numpy as np
import torch
import argparse
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime

# 导入必要的模块
from config_1 import Config
from hmasd.agent import HMASDAgent
from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv
from envs.pettingzoo.scenario3 import UAVMultiHopEnv
from envs.pettingzoo.scenario4 import UAVForcedRelayEnv
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter

class RandomAgent:
    """
    随机策略智能体，用于在没有训练模型时提供基线演示
    
    模拟 HMASDAgent 的接口，但使用随机动作
    """
    
    def __init__(self, config, seed=None):
        """
        初始化随机智能体
        
        参数:
            config: 配置对象，包含智能体数量和技能数量信息
            seed: 随机种子
        """
        self.config = config
        self.action_dim = 3  # 3D速度控制 (x, y, z)
        
        # 设置随机种子
        if seed is not None:
            np.random.seed(seed)
        
        # 模拟技能状态
        self.current_team_skill = 0
        self.current_agent_skills = [0] * config.n_agents
        self.skill_timer = 0
        self.skill_duration = 10  # 每10步切换一次技能
        
        print(f"初始化随机策略智能体: {config.n_agents}个无人机, 动作维度={self.action_dim}")
    
    def step(self, state, obs, step_count, deterministic=True, env_id=0):
        """
        选择随机动作
        
        参数:
            state: 全局状态 (未使用)
            obs: 观测 (未使用)
            step_count: 当前步数
            deterministic: 是否确定性 (对随机策略无影响)
            env_id: 环境ID (未使用)
        
        返回:
            actions: 随机动作数组 [n_agents, action_dim]
            agent_info: 智能体信息字典
        """
        # 生成随机动作：3D速度控制，范围 [-1, 1]
        actions = np.random.uniform(-1, 1, size=(self.config.n_agents, self.action_dim))
        
        # 更新技能状态（模拟技能切换）
        skill_changed = False
        if self.skill_timer >= self.skill_duration:
            # 切换团队技能
            self.current_team_skill = np.random.randint(0, self.config.n_Z)
            
            # 切换个体技能
            self.current_agent_skills = [
                np.random.randint(0, self.config.n_z) 
                for _ in range(self.config.n_agents)
            ]
            
            self.skill_timer = 0
            skill_changed = True
        else:
            self.skill_timer += 1
        
        # 构建智能体信息
        agent_info = {
            'team_skill': self.current_team_skill,
            'agent_skills': self.current_agent_skills.copy(),
            'skill_changed': skill_changed,
            'action_logprobs': np.zeros((self.config.n_agents, self.action_dim)),  # 随机策略无logprobs
            'log_probs': {
                'team_logprob': 0.0,
                'agent_logprobs': [0.0] * self.config.n_agents
            }
        }
        
        return actions, agent_info

class EnhancedVisualizationEnv:
    """
    增强的可视化环境包装器
    
    在原有环境渲染基础上添加通信链路可视化
    """
    
    def __init__(self, base_env, save_path=None):
        """
        初始化增强可视化环境
        
        参数:
            base_env: 基础环境实例
            save_path: 图像保存路径
        """
        self.base_env = base_env
        self.fig = None
        self.ax = None
        self.save_path = save_path
        self.current_episode = 0
        self.current_step = 0
        self.history = {}
        
        # 可视化配置
        self.link_colors = {
            'user_service': 'green',      # 用户服务链路 (已有)
            'uav_relay': 'orange',        # 无人机中继链路
            'backhaul': 'magenta',        # 回程链路 (到地面基站)
            'ground_bs': 'black'          # 地面基站
        }
        
        self.link_styles = {
            'user_service': {'alpha': 0.3, 'linewidth': 1},
            'uav_relay': {'alpha': 0.8, 'linewidth': 2},
            'backhaul': {'alpha': 0.9, 'linewidth': 2.5}
        }
    
    def __getattr__(self, name):
        """委托属性访问到基础环境"""
        return getattr(self.base_env, name)
    
    def reset(self, **kwargs):
        """重置环境并记录初始状态"""
        obs, info = self.base_env.reset(**kwargs)
        
        # 重置历史记录
        self.history = {
            'steps': [],
            'uav_positions': [],
            'connectivity': [],
            'throughput': []
        }
        self._record_history() # 记录初始状态
        
        return obs, info

    def step(self, action):
        """执行环境步骤并记录状态"""
        next_obs, reward, done, truncated, info = self.base_env.step(action)
        self._record_history() # 记录此步之后的状态
        return next_obs, reward, done, truncated, info
    
    def render(self, skill_info=None):
        """增强的渲染方法"""
        # 首先调用基础环境的渲染设置
        if self.base_env.render_mode is None:
            return
        
        return self._render_enhanced_frame(skill_info)
    
    def _render_enhanced_frame(self, skill_info=None):
        """
        渲染增强的可视化帧
        
        包含通信链路、中继路径、技能信息等额外信息
        
        参数:
            skill_info: 智能体技能信息，包含 team_skill 和 agent_skills
        """
        try:
            import matplotlib.pyplot as plt
            from matplotlib.patches import Circle
            from mpl_toolkits.mplot3d import Axes3D
            
            # 配置中文字体支持
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'Microsoft YaHei']
            plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        except ImportError:
            print("渲染需要matplotlib库")
            return None
        
        if self.fig is None:
            self.fig = plt.figure(figsize=(14, 10))
            self.ax = self.fig.add_subplot(111, projection='3d')
        else:
            self.ax.clear()
        
        # 设置坐标轴
        self.ax.set_xlim(0, self.base_env.env.area_size)
        self.ax.set_ylim(0, self.base_env.env.area_size)
        self.ax.set_zlim(0, self.base_env.env.height_range[1] * 1.2)
        self.ax.set_xlabel('X (m)')
        self.ax.set_ylabel('Y (m)')
        self.ax.set_zlabel('Z (m)')
        
        # 设置标题
        step_info = f'步数: {self.base_env.env.current_step}/{self.base_env.env.max_steps}'
        
        # 添加团队技能信息到标题
        if skill_info and 'team_skill' in skill_info:
            team_skill_info = f'团队技能: Z_{skill_info["team_skill"]}'
        else:
            team_skill_info = '团队技能: N/A'
        
        # 检测智能体类型以添加到标题
        agent_type_info = ""
        if skill_info:
            # 通过检查技能信息的特征来判断智能体类型
            if 'action_logprobs' in skill_info:
                # 检查logprobs是否全为0（随机策略的特征）
                logprobs = skill_info['action_logprobs']
                if isinstance(logprobs, np.ndarray) and np.all(logprobs == 0):
                    agent_type_info = " | 🎲 随机策略"
                else:
                    agent_type_info = " | 🤖 训练模型"
        
        if hasattr(self.base_env.env, 'reward_info') and self.base_env.env.reward_info:
            reward_info = self.base_env.env.reward_info
            title = f'无人机网络通信链路可视化 - {step_info} | {team_skill_info}{agent_type_info}\n'
            title += f'总奖励: {reward_info.get("final_reward", 0):.3f} | '
            title += f'有效用户: {reward_info.get("effective_connected_users", 0)}/{self.base_env.env.n_users} | '
            title += f'平均跳数: {reward_info.get("avg_hops", 0):.1f}'
        else:
            title = f'无人机网络通信链路可视化 - {step_info} | {team_skill_info}{agent_type_info}'
        
        self.ax.set_title(title, fontsize=12, pad=20)
        
        # 1. 绘制地面基站
        if hasattr(self.base_env.env, 'ground_bs_positions') and len(self.base_env.env.ground_bs_positions) > 0:
            bs_x = self.base_env.env.ground_bs_positions[:, 0]
            bs_y = self.base_env.env.ground_bs_positions[:, 1]
            bs_z = self.base_env.env.ground_bs_positions[:, 2]
            self.ax.scatter(bs_x, bs_y, bs_z, 
                          c=self.link_colors['ground_bs'], 
                          marker='s', s=200, 
                          label='地面基站', alpha=0.9, edgecolors='white', linewidth=2)
        
        # 2. 绘制用户
        user_x = self.base_env.env.user_positions[:, 0]
        user_y = self.base_env.env.user_positions[:, 1]
        user_z = np.zeros(self.base_env.env.n_users)  # 用户在地面
        
        # 区分已连接和未连接的用户
        connected_users = set()
        for i in range(self.base_env.env.n_uavs):
            for j in range(self.base_env.env.n_users):
                if self.base_env.env.connections[i, j]:
                    connected_users.add(j)
        
        # 绘制未连接用户
        unconnected_users = [j for j in range(self.base_env.env.n_users) if j not in connected_users]
        if unconnected_users:
            unconnected_x = [user_x[j] for j in unconnected_users]
            unconnected_y = [user_y[j] for j in unconnected_users]
            unconnected_z = [user_z[j] for j in unconnected_users]
            self.ax.scatter(unconnected_x, unconnected_y, unconnected_z, 
                          c='lightblue', marker='.', s=30, label='未连接用户', alpha=0.6)
        
        # 绘制已连接用户
        if connected_users:
            connected_x = [user_x[j] for j in connected_users]
            connected_y = [user_y[j] for j in connected_users]
            connected_z = [user_z[j] for j in connected_users]
            self.ax.scatter(connected_x, connected_y, connected_z, 
                          c='blue', marker='o', s=50, label='已连接用户', alpha=0.8)
        
        # 3. 绘制无人机
        uav_colors = []
        uav_sizes = []
        uav_labels = []
        
        for i in range(self.base_env.env.n_uavs):
            # 根据无人机的连接状态确定颜色和大小
            has_users = np.sum(self.base_env.env.connections[i]) > 0
            has_backhaul = hasattr(self.base_env.env, 'routing_paths') and i in self.base_env.env.routing_paths
            
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
        
        for i in range(self.base_env.env.n_uavs):
            uav_pos = self.base_env.env.uav_positions[i]
            self.ax.scatter(uav_pos[0], uav_pos[1], uav_pos[2], 
                          c=uav_colors[i], marker='^', s=uav_sizes[i], 
                          alpha=0.9, edgecolors='white', linewidth=1)
            
            # 添加无人机编号和技能标签
            if skill_info and 'agent_skills' in skill_info:
                agent_skills = skill_info['agent_skills']
                if i < len(agent_skills):
                    skill_id = agent_skills[i]
                    label_text = f'UAV{i}\nz_{skill_id}'
                else:
                    label_text = f'UAV{i}\nz_?'
            else:
                label_text = f'UAV{i}'
            
            self.ax.text(uav_pos[0], uav_pos[1], uav_pos[2] + 30, 
                        label_text, fontsize=8, ha='center', va='bottom',
                        bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8, edgecolor='gray'))
        
        # 4. 绘制用户服务链路 (基础连接)
        for i in range(self.base_env.env.n_uavs):
            uav_pos = self.base_env.env.uav_positions[i]
            for j in range(self.base_env.env.n_users):
                if self.base_env.env.connections[i, j]:
                    user_pos = self.base_env.env.user_positions[j]
                    self.ax.plot([uav_pos[0], user_pos[0]], 
                               [uav_pos[1], user_pos[1]], 
                               [uav_pos[2], 0], 
                               color=self.link_colors['user_service'],
                               **self.link_styles['user_service'])
        
        # 5. 绘制无人机中继链路和回程链路
        if hasattr(self.base_env.env, 'routing_paths'):
            self._draw_routing_paths()
        
        # 6. 添加图例
        handles, labels = self.ax.get_legend_handles_labels()
        
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
        legend = self.ax.legend(all_handles, all_labels, 
                               loc='upper left', bbox_to_anchor=(0.02, 0.98),
                               ncol=1, fontsize=9, framealpha=0.9)
        
        # 7. 添加详细统计信息
        self._add_statistics_text()
        
        # 8. 设置视角
        self.ax.view_init(elev=30, azim=45)
        
        self.fig.canvas.draw()
        
        # 保存图像到文件（如果设置了保存路径）
        if self.save_path is not None:
            filename = f"episode_{self.current_episode + 1}_step_{self.current_step}.png"
            save_file_path = os.path.join(self.save_path, filename)
            self.fig.savefig(save_file_path, dpi=150, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
            print(f"图像已保存: {save_file_path}")
        
        if self.base_env.render_mode == "human":
            plt.pause(0.1)
            return None
        
        # 返回RGB数组
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        canvas = FigureCanvasAgg(self.fig)
        canvas.draw()
        image = np.array(canvas.renderer.buffer_rgba())
        return image
    
    def _draw_routing_paths(self):
        """
        绘制路由路径（中继链路和回程链路）
        """
        if not hasattr(self.base_env.env, 'routing_paths'):
            return
        
        routing_paths = self.base_env.env.routing_paths
        
        if not routing_paths:
            return
        
        for uav_idx, path in routing_paths.items():
            if not path:
                continue
            
            # 路径现在已经包含完整的节点信息，直接使用
            # 绘制路径中的每一段链路
            for i in range(len(path) - 1):
                src_type, src_idx = path[i]
                dst_type, dst_idx = path[i + 1]
                
                # 获取源节点位置
                if src_type == 'uav':
                    src_pos = self.base_env.env.uav_positions[src_idx]
                elif src_type == 'ground_bs':
                    src_pos = self.base_env.env.ground_bs_positions[src_idx]
                else:
                    continue
                
                # 获取目标节点位置
                if dst_type == 'uav':
                    dst_pos = self.base_env.env.uav_positions[dst_idx]
                elif dst_type == 'ground_bs':
                    dst_pos = self.base_env.env.ground_bs_positions[dst_idx]
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
                self.ax.plot([src_pos[0], dst_pos[0]], 
                           [src_pos[1], dst_pos[1]], 
                           [src_pos[2], dst_pos[2]], 
                           color=link_color, **link_style)
    
    def _add_statistics_text(self):
        """
        添加详细的统计信息文本
        """
        if not hasattr(self.base_env.env, 'reward_info') or not self.base_env.env.reward_info:
            return
        
        reward_info = self.base_env.env.reward_info
        
        # 计算统计信息
        total_connections = np.sum(self.base_env.env.connections)
        coverage_ratio = total_connections / self.base_env.env.n_users
        
        # 统计UAV类型
        serving_uavs = 0
        relay_uavs = 0
        isolated_uavs = 0
        idle_uavs = 0
        
        for i in range(self.base_env.env.n_uavs):
            has_users = np.sum(self.base_env.env.connections[i]) > 0
            has_backhaul = hasattr(self.base_env.env, 'routing_paths') and i in self.base_env.env.routing_paths
            
            if has_users and has_backhaul:
                serving_uavs += 1
            elif has_backhaul:
                relay_uavs += 1
            elif has_users:
                isolated_uavs += 1
            else:
                idle_uavs += 1
        
        # 构建统计文本
        stats_text = f"""统计信息:
总连接数: {total_connections}/{self.base_env.env.n_users} ({coverage_ratio:.1%})
有效连接数: {reward_info.get('effective_connected_users', 0)}
服务型UAV: {serving_uavs}
中继型UAV: {relay_uavs}
孤立型UAV: {isolated_uavs}
空闲UAV: {idle_uavs}
网络连通性: {reward_info.get('connected_uavs', 0)}/{self.base_env.env.n_uavs}
系统吞吐量: {reward_info.get('system_throughput_mbps', 0):.1f} Mbps"""
        
        # 添加文本到图中
        self.ax.text2D(0.75, 0.95, stats_text, transform=self.ax.transAxes,
                      fontsize=10, verticalalignment='top',
                      bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8))

    def _record_history(self):
        """记录当前时间步的历史数据"""
        # 记录UAV位置
        self.history['steps'].append(self.base_env.env.current_step)
        self.history['uav_positions'].append(self.base_env.env.uav_positions.copy())
        
        # 记录性能指标
        reward_info = getattr(self.base_env.env, 'reward_info', {})
        self.history['connectivity'].append(reward_info.get('effective_connected_users', 0))
        self.history['throughput'].append(reward_info.get('system_throughput_mbps', 0))

    def save_episode_plots(self, args):
        """在episode结束时，保存所有额外的分析图表"""
        if not self.save_path:
            return
        
        print(f"为 Episode {self.current_episode + 1} 生成额外的分析图表...")
        self._save_2d_topology_plot(args)
        self._save_performance_plots()

    def _save_2d_topology_plot(self, args):
        """生成并保存带轨迹的2D俯瞰拓扑图"""
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # 绘制历史轨迹
        positions_history = np.array(self.history['uav_positions']) # [steps, n_uavs, 3]
        for i in range(self.base_env.env.n_uavs):
            # 使用颜色循环来区分不同无人机
            color = plt.cm.jet(i / self.base_env.env.n_uavs)
            ax.plot(positions_history[:, i, 0], positions_history[:, i, 1], 
                    color=color, alpha=0.6, linewidth=1.5,
                    label=f'UAV {i} 轨迹' if i == 0 else "") # 只为一个UAV添加图例
            
            # 标记轨迹快照点
            if args.trajectory_snapshot_interval > 0 and args.trajectory_snapshot_interval < len(positions_history):
                for step_idx in range(args.trajectory_snapshot_interval, len(positions_history), args.trajectory_snapshot_interval):
                    ax.scatter(positions_history[step_idx, i, 0], positions_history[step_idx, i, 1],
                               marker='x', color=color, s=40, alpha=0.9)
            
            # 标记起点和终点
            ax.scatter(positions_history[0, i, 0], positions_history[0, i, 1],
                       marker='o', color=color, s=50, edgecolors='black') # 起点
            ax.scatter(positions_history[-1, i, 0], positions_history[-1, i, 1],
                       marker='>', color=color, s=100, edgecolors='black') # 终点

        # 绘制最终状态的实体和连接
        # 1. 地面基站
        if hasattr(self.base_env.env, 'ground_bs_positions'):
            bs_pos = self.base_env.env.ground_bs_positions
            ax.scatter(bs_pos[:, 0], bs_pos[:, 1], c='black', marker='s', s=200, label='地面基站', zorder=5)

        # 2. 用户
        user_pos = self.base_env.env.user_positions
        ax.scatter(user_pos[:, 0], user_pos[:, 1], c='blue', marker='.', s=50, label='用户', zorder=5)

        # 3. 无人机 (最终位置)
        uav_pos = self.base_env.env.uav_positions
        ax.scatter(uav_pos[:, 0], uav_pos[:, 1], c='red', marker='^', s=150, label='UAV (最终位置)', zorder=5)
        for i in range(self.base_env.env.n_uavs):
            ax.text(uav_pos[i, 0] + 10, uav_pos[i, 1] + 10, f'UAV{i}', fontsize=9)

        # 4. 连接线 (根据用户反馈已移除)

        ax.set_title(f'Episode {self.current_episode + 1}: 2D拓扑与无人机轨迹')
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_xlim(0, self.base_env.env.area_size)
        ax.set_ylim(0, self.base_env.env.area_size)
        ax.set_aspect('equal', adjustable='box')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.5)
        
        filename = f"episode_{self.current_episode + 1}_topology_2d.png"
        save_file_path = os.path.join(self.save_path, filename)
        fig.savefig(save_file_path, dpi=200, bbox_inches='tight')
        plt.close(fig)
        print(f"2D拓扑图已保存: {save_file_path}")

    def _save_performance_plots(self):
        """生成并保存性能指标（连通性、吞吐量）随时间变化的图表"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        steps = self.history['steps']
        connectivity = self.history['connectivity']
        throughput = self.history['throughput']
        
        # 连通性图
        ax1.plot(steps, connectivity, color='b', marker='.', linestyle='-', label='有效连接用户数')
        ax1.set_title(f'Episode {self.current_episode + 1}: 网络性能变化')
        ax1.set_ylabel('有效连接用户数')
        ax1.grid(True, linestyle='--', alpha=0.6)
        ax1.legend()
        
        # 吞吐量图
        ax2.plot(steps, throughput, color='g', marker='.', linestyle='-', label='系统吞吐量')
        ax2.set_ylabel('系统吞吐量 (Mbps)')
        ax2.set_xlabel('时间步 (Step)')
        ax2.grid(True, linestyle='--', alpha=0.6)
        ax2.legend()
        
        fig.tight_layout()
        filename = f"episode_{self.current_episode + 1}_performance.png"
        save_file_path = os.path.join(self.save_path, filename)
        fig.savefig(save_file_path, dpi=200, bbox_inches='tight')
        plt.close(fig)
        print(f"性能图表已保存: {save_file_path}")

    def close(self):
        """关闭可视化环境"""
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
            self.ax = None
        
        # 关闭基础环境
        if hasattr(self.base_env, 'close'):
            self.base_env.close()


def create_evaluation_folder(config, scenario, model_path):
    """
    创建评估结果保存文件夹
    
    参数:
        config: 配置对象
        scenario: 场景编号
        model_path: 模型路径
    
    返回:
        save_path: 保存路径
    """
    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    # 提取模型名称（去掉路径和扩展名）
    model_name = os.path.splitext(os.path.basename(model_path))[0]
    
    # 构建实验设置字符串 - 从config读取参数
    experiment_config = f"scen{scenario}_uav{config.n_agents}_usr{config.n_users}_{config.user_distribution}"
    
    # 创建文件夹名称
    folder_name = f"{timestamp}_{experiment_config}_{model_name}"
    
    # 创建完整路径
    evaluation_dir = "evaluation"
    save_path = os.path.join(evaluation_dir, folder_name)
    
    # 创建目录
    os.makedirs(save_path, exist_ok=True)
    
    print(f"评估结果将保存到: {save_path}")
    return save_path


def create_env(scenario, config, seed, save_path=None):
    """
    创建环境实例
    
    参数:
        scenario: 场景编号
        config: 配置对象
        seed: 随机种子
        save_path: 图像保存路径
    
    返回:
        env: 环境实例
    """
    # 从配置对象获取通用环境参数
    env_kwargs = {
        'n_uavs': config.n_agents,
        'n_users': config.n_users,
        'user_distribution': config.user_distribution,
        'channel_model': config.channel_model,
        'render_mode': "human",
        'seed': seed,
        'use_fdma': config.use_fdma,
        'bandwidth': config.bandwidth
    }
    
    if scenario == 1:
        raw_env = UAVBaseStationEnv(**env_kwargs)
    elif scenario == 2:
        # 场景2不再需要传递奖励权重参数，奖励已固化为覆盖率+归一化吞吐量
        raw_env = UAVCooperativeNetworkEnv(
            max_hops=config.max_hops,
            **env_kwargs
        )
    elif scenario == 3:
        # 场景3的奖励权重参数（从配置对象获取）
        reward_kwargs = {
            'effective_coverage_weight': config.effective_coverage_weight,
            'throughput_weight': config.throughput_weight,
            'load_balance_weight': config.load_balance_weight,
            'proximity_penalty_weight': config.proximity_penalty_weight
        }
        
        # 场景3特有的参数（从配置对象获取）
        scenario3_kwargs = {
            'n_clusters': config.n_clusters,
            'cluster_std': config.cluster_std,
            'central_area_ratio': config.central_area_ratio,
            'area_size': config.area_size
        }
        
        raw_env = UAVMultiHopEnv(
            max_hops=config.max_hops,
            **env_kwargs, # 传递通用参数
            **reward_kwargs, # 传递场景3的奖励权重参数
            **scenario3_kwargs # 传递场景3特有参数
        )
    elif scenario == 4:
        # 场景4：强制多跳中继环境（从配置对象获取所有参数）
        scenario4_kwargs = {
            'user_distribution': 'forced_relay_cluster',  # 场景4强制使用此分布类型
            'max_hops': config.max_hops,
            'area_size': config.area_size,
            'n_clusters': config.n_clusters,
            'cluster_std': config.cluster_std,
            'central_area_ratio': config.central_area_ratio,
            'min_sinr': config.min_sinr,
            'max_connections': config.max_connections,
            'coverage_weight': config.coverage_weight,
            'connectivity_weight': config.connectivity_weight,
            'efficiency_weight': config.efficiency_weight,
            'uav_init_mode': config.uav_init_mode,
            'uav_start_area_size': config.uav_start_area_size,
            'grid_resolution': config.grid_resolution,
            'potential_reward_weight': config.potential_reward_weight,
            'belief_decay_factor': config.belief_decay_factor,
            'recon_interval': config.recon_interval,
            'recon_strength': config.recon_strength,
            'coverage_overlap_penalty_weight': config.coverage_overlap_penalty_weight
        }
        
        # 将场景4的参数合并到通用参数中
        env_kwargs.update(scenario4_kwargs)
        
        raw_env = UAVForcedRelayEnv(**env_kwargs)
    else:
        raise ValueError(f"未知的场景: {scenario}")
    
    # 使用适配器包装环境
    adapted_env = ParallelToArrayAdapter(raw_env, seed=seed)
    
    # 使用增强可视化包装器
    enhanced_env = EnhancedVisualizationEnv(adapted_env, save_path=save_path)
    
    return enhanced_env


def visualize_evaluation(env, agent, args):
    """
    运行可视化评估
    
    参数:
        env: 环境实例
        agent: 智能体实例
        args: 命令行参数
    """
    n_episodes = args.n_episodes
    print(f"\n开始可视化评估，将运行 {n_episodes} 个episodes...")
    
    episode_rewards = []
    
    for episode in range(n_episodes):
        print(f"\n=== Episode {episode + 1}/{n_episodes} ===")
        
        # 设置当前episode
        env.current_episode = episode
        env.current_step = 0
        
        # 重置环境
        obs, info = env.reset()
        state = info.get('state', np.zeros(agent.config.state_dim))
        
        episode_reward = 0
        step_count = 0
        done = False
        
        # 渲染初始状态
        env.render()
        input("按回车键开始这个episode...")
        
        while not done:
            # 智能体选择动作（确定性模式）
            actions, agent_info = agent.step(state, obs, step_count, deterministic=True)
            
            # 执行动作
            next_obs, reward, done, truncated, info = env.step(actions)
            next_state = info.get('next_state', np.zeros(agent.config.state_dim))
            
            # 更新状态
            state = next_state
            obs = next_obs
            episode_reward += reward
            step_count += 1
            
            # 更新环境的step计数
            env.current_step = step_count
            
            # 根据渲染间隔渲染当前状态
            if step_count % args.render_interval == 0:
                env.render(skill_info=agent_info)
            
            # 打印当前步骤信息（包含技能信息）
            if hasattr(env.base_env.env, 'reward_info') and env.base_env.env.reward_info:
                reward_info = env.base_env.env.reward_info
                print(f"步骤 {step_count}: 奖励={reward:.3f}, "
                      f"有效用户={reward_info.get('effective_connected_users', 0)}/{env.base_env.env.n_users}, "
                      f"平均跳数={reward_info.get('avg_hops', 0):.1f}, "
                      f"团队技能=Z_{agent_info.get('team_skill', 'N/A')}")
                
                # 打印个体技能信息
                agent_skills = agent_info.get('agent_skills', [])
                skills_str = ', '.join([f"UAV{i}:z_{skill}" for i, skill in enumerate(agent_skills)])
                print(f"个体技能: {skills_str}")
            
            # 检查是否结束
            if done or truncated:
                # 强制渲染最终状态
                print("渲染最终状态...")
                env.render(skill_info=agent_info)
                
                # 如果启用了额外绘图，则在episode结束时生成
                if args.save_extra_plots:
                    env.save_episode_plots(args)
                
                break
            
            # 暂停一下以便观察
            #time.sleep(0.1)
        
        episode_rewards.append(episode_reward)
        print(f"Episode {episode + 1} 完成: 总奖励={episode_reward:.3f}, 总步数={step_count}")
        
        if episode < n_episodes - 1:
            input("按回车键继续下一个episode...")
    
    # 打印评估结果
    print(f"\n=== 评估完成 ===")
    print(f"平均奖励: {np.mean(episode_rewards):.3f} ± {np.std(episode_rewards):.3f}")
    print(f"最大奖励: {np.max(episode_rewards):.3f}")
    print(f"最小奖励: {np.min(episode_rewards):.3f}")


def parse_args():
    """解析命令行参数 - 简化版本，大多数参数从config_1.py读取"""
    parser = argparse.ArgumentParser(description='可视化评估训练好的HMASD模型')
    
    # 模型和场景参数
    parser.add_argument('--model_path', type=str, default=None,
                       help='训练好的模型文件路径 (如果未提供或不存在，将使用随机策略)')
    parser.add_argument('--use_random', action='store_true',
                       help='强制使用随机策略 (忽略模型文件)')
    parser.add_argument('--scenario', type=int, default=4,
                       help='场景: 1=基站模式, 2=协作组网模式, 3=强制多跳模式, 4=强制中继模式')
    
    # 评估控制参数
    parser.add_argument('--n_episodes', type=int, default=5,
                       help='评估的episode数量')
    parser.add_argument('--seed', type=int, default=42,
                       help='随机种子')
    
    # 可视化参数
    parser.add_argument('--render_interval', type=int, default=50,
                        help='每隔多少步渲染一次 (默认: 1, 即每步都渲染)')
    parser.add_argument('--save_extra_plots', action='store_true',
                        help='生成并保存额外的分析图表 (2D拓扑图、性能变化图)')
    parser.add_argument('--trajectory_snapshot_interval', type=int, default=500,
                        help='在2D拓扑图上标记轨迹快照的频率 (步数)')
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 判断是否使用随机策略
    use_random_agent = args.use_random or args.model_path is None or not os.path.exists(args.model_path or "")
    
    # 加载配置（基于论文参数）
    config = Config()
    config.use_opt = False
    
    print(f"场景: {args.scenario}")
    print(f"无人机数量: {config.n_agents}")
    print(f"用户数量: {config.n_users}")
    print(f"区域大小: {config.area_size}m")
    print(f"最大跳数: {config.max_hops}")
    print(f"用户分布: {config.user_distribution}")
    print(f"信道模型: {config.channel_model}")
    print(f"FDMA启用状态: {config.use_fdma}")
    if config.use_fdma:
        print(f"无人机带宽: {config.bandwidth/1e6:.0f} MHz")
    
    # 创建环境获取维度信息
    temp_env = create_env(args.scenario, config, args.seed)
    state_dim = temp_env.state_dim
    obs_dim = temp_env.obs_dim
    config.update_env_dims(state_dim, obs_dim)
    temp_env.close()
    
    print(f"环境维度: state_dim={state_dim}, obs_dim={obs_dim}")
    
    # 智能体选择和创建
    if use_random_agent:
        # 使用随机策略
        if args.use_random:
            print("🎲 强制使用随机策略进行演示")
        elif args.model_path is None:
            print("🎲 未提供模型路径，使用随机策略进行演示")
        else:
            print(f"🎲 模型文件 {args.model_path} 不存在，使用随机策略进行演示")
        
        agent = RandomAgent(config, seed=args.seed)
        
        # 创建评估结果保存文件夹 (随机策略)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        experiment_config = f"scen{args.scenario}_uav{config.n_agents}_usr{config.n_users}_{config.user_distribution}"
        folder_name = f"{timestamp}_{experiment_config}_random_agent"
        evaluation_dir = "evaluation"
        save_path = os.path.join(evaluation_dir, folder_name)
        os.makedirs(save_path, exist_ok=True)
        print(f"评估结果将保存到: {save_path}")
        
    else:
        # 使用训练好的模型
        print(f"🤖 加载训练好的模型: {args.model_path}")
        
        try:
            agent = HMASDAgent(config, device=torch.device('cpu'))
            agent.load_model(args.model_path)
            print("✅ 模型加载成功")
            
            # 创建评估结果保存文件夹
            save_path = create_evaluation_folder(config, args.scenario, args.model_path)
            
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            print("🎲 回退到随机策略进行演示")
            
            agent = RandomAgent(config, seed=args.seed)
            
            # 创建评估结果保存文件夹 (回退到随机策略)
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            experiment_config = f"scen{args.scenario}_uav{config.n_agents}_usr{config.n_users}_{config.user_distribution}"
            folder_name = f"{timestamp}_{experiment_config}_random_fallback"
            evaluation_dir = "evaluation"
            save_path = os.path.join(evaluation_dir, folder_name)
            os.makedirs(save_path, exist_ok=True)
            print(f"评估结果将保存到: {save_path}")
    
    # 创建可视化环境（带保存路径）
    env = create_env(args.scenario, config, args.seed, save_path=save_path)
    
    try:
        # 运行可视化评估
        visualize_evaluation(env, agent, args)
    finally:
        # 清理资源
        env.close()
        print("可视化评估完成")
        print(f"所有图像已保存到: {save_path}")


if __name__ == "__main__":
    main()
