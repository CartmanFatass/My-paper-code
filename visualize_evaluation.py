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
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter

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
        """重置环境"""
        return self.base_env.reset(**kwargs)
    
    def step(self, action):
        """执行环境步骤"""
        return self.base_env.step(action)
    
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
        
        if hasattr(self.base_env.env, 'reward_info') and self.base_env.env.reward_info:
            reward_info = self.base_env.env.reward_info
            title = f'无人机网络通信链路可视化 - {step_info} | {team_skill_info}\n'
            title += f'总奖励: {reward_info.get("final_reward", 0):.3f} | '
            title += f'有效用户: {reward_info.get("effective_connected_users", 0)}/{self.base_env.env.n_users} | '
            title += f'平均跳数: {reward_info.get("avg_hops", 0):.1f}'
        else:
            title = f'无人机网络通信链路可视化 - {step_info} | {team_skill_info}'
        
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
    
    def close(self):
        """关闭可视化环境"""
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
            self.ax = None
        
        # 关闭基础环境
        if hasattr(self.base_env, 'close'):
            self.base_env.close()


def create_evaluation_folder(args):
    """
    创建评估结果保存文件夹
    
    参数:
        args: 命令行参数
    
    返回:
        save_path: 保存路径
    """
    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    # 提取模型名称（去掉路径和扩展名）
    model_name = os.path.splitext(os.path.basename(args.model_path))[0]
    
    # 构建实验设置字符串
    experiment_config = f"scen{args.scenario}_uav{args.n_uavs}_usr{args.n_users}_{args.user_distribution}"
    
    # 创建文件夹名称
    folder_name = f"{timestamp}_{experiment_config}_{model_name}"
    
    # 创建完整路径
    evaluation_dir = "evaluation"
    save_path = os.path.join(evaluation_dir, folder_name)
    
    # 创建目录
    os.makedirs(save_path, exist_ok=True)
    
    print(f"评估结果将保存到: {save_path}")
    return save_path


def create_env(scenario, args, save_path=None):
    """
    创建环境实例
    
    参数:
        scenario: 场景编号
        args: 命令行参数
        save_path: 图像保存路径
    
    返回:
        env: 环境实例
    """
    if scenario == 1:
        raw_env = UAVBaseStationEnv(
            n_uavs=args.n_uavs,
            n_users=args.n_users,
            area_size=args.area_size,
            user_distribution=args.user_distribution,
            channel_model=args.channel_model,
            render_mode="human",
            seed=args.seed
        )
    elif scenario == 2:
        raw_env = UAVCooperativeNetworkEnv(
            n_uavs=args.n_uavs,
            n_users=args.n_users,
            area_size=args.area_size,
            max_hops=args.max_hops,
            user_distribution=args.user_distribution,
            channel_model=args.channel_model,
            render_mode="human",
            seed=args.seed
        )
    elif scenario == 3:
        raw_env = UAVMultiHopEnv(
            n_uavs=args.n_uavs,
            n_users=args.n_users,
            area_size=args.area_size,
            max_hops=args.max_hops,
            user_distribution=args.user_distribution,
            channel_model=args.channel_model,
            render_mode="human",
            seed=args.seed,
            n_clusters=args.n_clusters,
            cluster_std=args.cluster_std,
            central_area_ratio=args.central_area_ratio
        )
    else:
        raise ValueError(f"未知的场景: {scenario}")
    
    # 使用适配器包装环境
    adapted_env = ParallelToArrayAdapter(raw_env, seed=args.seed)
    
    # 使用增强可视化包装器
    enhanced_env = EnhancedVisualizationEnv(adapted_env, save_path=save_path)
    
    return enhanced_env


def visualize_evaluation(env, agent, n_episodes=5):
    """
    运行可视化评估
    
    参数:
        env: 环境实例
        agent: 智能体实例
        n_episodes: 评估的episode数量
    """
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
            
            # 渲染当前状态，传入技能信息
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
                break
            
            # 暂停一下以便观察
            time.sleep(0.5)
        
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
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='可视化评估训练好的HMASD模型')
    
    # 模型参数
    parser.add_argument('--model_path', type=str, required=True,
                       help='训练好的模型文件路径')
    parser.add_argument('--scenario', type=int, default=3,
                       help='场景: 1=基站模式, 2=协作组网模式, 3=强制多跳模式')
    parser.add_argument('--n_episodes', type=int, default=5,
                       help='评估的episode数量')
    
    # 环境参数
    parser.add_argument('--n_uavs', type=int, default=10,
                       help='无人机数量')
    parser.add_argument('--n_users', type=int, default=30,
                       help='用户数量')
    parser.add_argument('--area_size', type=int, default=1500,
                       help='区域大小 (米)')
    parser.add_argument('--max_hops', type=int, default=5,
                       help='最大跳数 (场景2和3使用)')
    parser.add_argument('--user_distribution', type=str, default='multi_cluster',
                       choices=['uniform', 'cluster', 'hotspot', 'multi_cluster'],
                       help='用户分布类型')
    parser.add_argument('--channel_model', type=str, default='3gpp-36777',
                       choices=['free_space', 'urban', 'suburban', '3gpp-36777'],
                       help='信道模型')
    parser.add_argument('--seed', type=int, default=42,
                       help='随机种子')
    
    # 场景3特有参数
    parser.add_argument('--n_clusters', type=int, default=3,
                       help='用户簇数量 (仅用于场景3)')
    parser.add_argument('--cluster_std', type=int, default=150,
                       help='簇内用户分布标准差 (米, 仅用于场景3)')
    parser.add_argument('--central_area_ratio', type=float, default=0.5,
                       help='中心用户区域占总区域的比例 (仅用于场景3)')
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 检查模型文件是否存在
    if not os.path.exists(args.model_path):
        print(f"错误: 模型文件 {args.model_path} 不存在")
        return
    
    print(f"加载模型: {args.model_path}")
    print(f"场景: {args.scenario}")
    print(f"无人机数量: {args.n_uavs}")
    print(f"用户数量: {args.n_users}")
    print(f"区域大小: {args.area_size}m")
    
    # 创建评估结果保存文件夹
    save_path = create_evaluation_folder(args)
    
    # 创建配置
    config = Config()
    config.n_agents = args.n_uavs
    
    # 创建环境获取维度信息
    temp_env = create_env(args.scenario, args)
    state_dim = temp_env.state_dim
    obs_dim = temp_env.obs_dim
    config.update_env_dims(state_dim, obs_dim)
    temp_env.close()
    
    print(f"环境维度: state_dim={state_dim}, obs_dim={obs_dim}")
    
    # 创建智能体并加载模型
    agent = HMASDAgent(config, device=torch.device('cpu'))
    agent.load_model(args.model_path)
    print("模型加载成功")
    
    # 创建可视化环境（带保存路径）
    env = create_env(args.scenario, args, save_path=save_path)
    
    try:
        # 运行可视化评估
        visualize_evaluation(env, agent, args.n_episodes)
    finally:
        # 清理资源
        env.close()
        print("可视化评估完成")
        print(f"所有图像已保存到: {save_path}")


if __name__ == "__main__":
    main()
