import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

class VisualizationManager:
    """
    统一管理评估过程中的数据收集和可视化绘图。
    """
    def __init__(self, episode_num, log_dir, config):
        """
        初始化可视化管理器。

        参数:
            episode_num (int): 当前评估的 episode 编号。
            log_dir (str): 保存绘图的目录。
            config: 训练配置对象。
        """
        self.episode_num = episode_num
        self.log_dir = os.path.join(log_dir, 'evaluation_plots')
        os.makedirs(self.log_dir, exist_ok=True)
        self.config = config
        
        # 数据存储
        self.history = {
            'steps': [],
            'uav_positions': [],
            'team_skills': [],
            'agent_skills': [],
            'connectivity': [],
            'throughput': [],
            'coverage_ratios': [],
            'static_info': None
        }

    def record_step(self, step_count, uav_positions, team_skill, agent_skills, reward_info, static_info=None):
        """
        记录评估过程中每一步的数据。

        参数:
            step_count (int): 当前步数。
            uav_positions (np.array): 所有无人机的位置。
            team_skill (int): 当前的团队技能。
            agent_skills (list): 每个智能体的个体技能。
            reward_info (dict): 包含性能指标的字典。
            static_info (dict, optional): 静态环境信息，如用户位置。
        """
        # 检查数据记录的顺序是否正确，防止多进程/线程导致的数据错乱
        if self.history['steps'] and step_count <= self.history['steps'][-1]:
            print(f"警告: 检测到乱序或重复的步数记录 (当前: {step_count}, 上一步: {self.history['steps'][-1]})。"
                  f"这可能由多进程环境下的竞态条件导致。为保证图像正确，将清空当前实例的历史数据。")
            # 清空历史数据，开始新的记录序列
            for key in self.history:
                if isinstance(self.history[key], list):
                    self.history[key] = []
            self.history['static_info'] = None

        self.history['steps'].append(step_count)
        self.history['uav_positions'].append(uav_positions.copy())
        self.history['team_skills'].append(team_skill)
        self.history['agent_skills'].append(agent_skills)
        
        # 记录性能指标
        self.history['connectivity'].append(reward_info.get('effective_connected_users', 0))
        self.history['throughput'].append(reward_info.get('system_throughput_mbps', 0))
        
        # 计算并记录覆盖率
        n_users = self.config.n_users
        served_users = reward_info.get('effective_connected_users', 0)
        coverage_ratio = served_users / n_users if n_users > 0 else 0
        self.history['coverage_ratios'].append(coverage_ratio)

        # 仅记录一次静态信息
        if self.history['static_info'] is None and static_info:
            self.history['static_info'] = static_info

    def generate_plots(self, prefix='', eval_step=None):
        """
        在 episode 结束后生成所有相关的图表。
        
        参数:
            prefix (str, optional): 添加到文件名开头的前缀。
            eval_step (int, optional): 当前的训练总步数，用于唯一标识评估图像。
        """
        if not self.history['steps']:
            print("没有数据可用于生成绘图。")
            return

        self._create_topology_plot(prefix=prefix, eval_step=eval_step)
        self._create_performance_plot(prefix=prefix, eval_step=eval_step)

    def _create_topology_plot(self, prefix='', eval_step=None):
        """
        生成并保存2D拓扑图，根据个体技能使用不同线型绘制无人机轨迹。
        """
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'Microsoft YaHei']
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, ax = plt.subplots(figsize=(12, 10))
            
            positions_history = np.array(self.history['uav_positions'])
            skills_history = np.array(self.history['agent_skills'])
            
            if positions_history.ndim != 3:
                print(f"错误的轨迹数据维度: {positions_history.shape}")
                return
            if skills_history.ndim != 2:
                print(f"错误的技能数据维度: {skills_history.shape}")
                return

            # 定义技能到线型的映射
            skill_linestyles = {
                0: '-',  # 实线
                1: '--', # 虚线
                2: ':',  # 点线
                3: '-.'  # 点划线
            }
            # 备用线型，以防技能超过预定义
            fallback_linestyles = ['-', '--', ':', '-.']

            # 绘制轨迹
            for i in range(self.config.n_agents):
                color = plt.cm.jet(i / self.config.n_agents)
                trajectory = positions_history[:, i, :2]
                agent_skills = skills_history[:, i]

                # 起点标记
                ax.scatter(trajectory[0, 0], trajectory[0, 1], marker='o', color=color, s=80, edgecolors='black', zorder=6, label=f'UAV {i} 起点')
                
                # 终点标记
                ax.scatter(trajectory[-1, 0], trajectory[-1, 1], marker='^', color=color, s=120, edgecolors='black', zorder=6, label=f'UAV {i} 终点')
                ax.text(trajectory[-1, 0] + 10, trajectory[-1, 1] + 10, f'UAV{i}', fontsize=9)

                # 根据技能变化分段绘制轨迹
                start_idx = 0
                for step_idx in range(1, len(trajectory)):
                    if agent_skills[step_idx] != agent_skills[start_idx]:
                        # 技能变化，绘制上一段轨迹
                        segment = trajectory[start_idx:step_idx+1]
                        skill = agent_skills[start_idx]
                        linestyle = skill_linestyles.get(skill, fallback_linestyles[skill % len(fallback_linestyles)])
                        ax.plot(segment[:, 0], segment[:, 1], color=color, linestyle=linestyle, linewidth=2, alpha=0.8, zorder=4)
                        start_idx = step_idx
                
                # 绘制最后一段轨迹
                if start_idx < len(trajectory) - 1:
                    segment = trajectory[start_idx:]
                    skill = agent_skills[start_idx]
                    linestyle = skill_linestyles.get(skill, fallback_linestyles[skill % len(fallback_linestyles)])
                    ax.plot(segment[:, 0], segment[:, 1], color=color, linestyle=linestyle, linewidth=2, alpha=0.8, zorder=4)

            # 绘制静态实体
            static_info = self.history['static_info']
            if static_info:
                if 'ground_bs_positions' in static_info and static_info.get('ground_bs_positions') is not None:
                    bs_pos = static_info['ground_bs_positions']
                    ax.scatter(bs_pos[:, 0], bs_pos[:, 1], c='black', marker='s', s=200, label='地面基站', zorder=5)
                if 'user_positions' in static_info and static_info.get('user_positions') is not None:
                    user_pos = static_info['user_positions']
                    ax.scatter(user_pos[:, 0], user_pos[:, 1], c='blue', marker='.', s=50, label='用户', zorder=5)

            # --- 构建图例 ---
            # 1. UAV 颜色图例
            uav_handles = [Line2D([0], [0], color=plt.cm.jet(i / self.config.n_agents), lw=4, label=f'UAV {i}') for i in range(self.config.n_agents)]
            
            # 2. 技能线型图例
            unique_skills = np.unique(skills_history)
            skill_handles = []
            for skill in sorted(unique_skills):
                linestyle = skill_linestyles.get(skill, fallback_linestyles[skill % len(fallback_linestyles)])
                skill_handles.append(Line2D([0], [0], color='gray', linestyle=linestyle, lw=2, label=f'个体技能 {skill}'))

            # 3. 静态实体和信息图例
            other_handles, _ = ax.get_legend_handles_labels()
            final_coverage = self.history['coverage_ratios'][-1]
            team_skill_at_end = self.history['team_skills'][-1]
            info_elements = [
                Line2D([0], [0], color='w', label=f'最终覆盖率: {final_coverage:.2%}'),
                Line2D([0], [0], color='w', label=f'团队技能 (Z): {team_skill_at_end}')
            ]
            
            # 合并所有图例元素
            all_handles = uav_handles + skill_handles + other_handles + info_elements
            
            ax.set_title(f'评估 Episode {self.episode_num}: 2D拓扑与无人机轨迹 (按技能分段)')
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            
            area_size = static_info.get('area_size', 1000) if static_info else 1000
            ax.set_xlim(0, area_size)
            ax.set_ylim(0, area_size)
            ax.set_aspect('equal', adjustable='box')
            ax.legend(handles=all_handles, title="图例与信息", loc='upper right', bbox_to_anchor=(1.4, 1.0))
            ax.grid(True, linestyle='--', alpha=0.5)
            
            plt.tight_layout(rect=[0, 0, 0.8, 1]) # 为图例留出更多空间
            
            # 使用 eval_step 和 PID 创建唯一的文件名以避免竞态条件
            pid = os.getpid()
            if eval_step is not None:
                filename = f'topology_eval_step_{eval_step}_episode_{self.episode_num}_pid_{pid}.png'
            else:
                filename = f'topology_episode_{self.episode_num}_pid_{pid}.png'
                
            if prefix:
                filename = f'{prefix}_{filename}'
            save_path = os.path.join(self.log_dir, filename)
            fig.savefig(save_path, dpi=200, bbox_inches='tight')
            plt.close(fig)
            print(f"拓扑图已保存: {save_path}")

        except Exception as e:
            print(f"生成拓扑图时出错: {e}")

    def _create_performance_plot(self, prefix='', eval_step=None):
        """
        生成并保存性能指标随时间变化的图表。
        
        参数:
            prefix (str, optional): 添加到文件名开头的前缀。
            eval_step (int, optional): 当前的训练总步数，用于唯一标识评估图像。
        """
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'Microsoft YaHei']
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
            
            steps = self.history['steps']
            connectivity = self.history['connectivity']
            throughput = self.history['throughput']
            
            # 连通性图
            ax1.plot(steps, connectivity, color='b', marker='.', linestyle='-', markersize=4, label='有效连接用户数')
            ax1.set_title(f'评估 Episode {self.episode_num}: 网络性能变化')
            ax1.set_ylabel('有效连接用户数')
            ax1.grid(True, linestyle='--', alpha=0.6)
            ax1.legend()
            
            # 吞吐量图
            ax2.plot(steps, throughput, color='g', marker='.', linestyle='-', markersize=4, label='系统吞吐量')
            ax2.set_ylabel('系统吞吐量 (Mbps)')
            ax2.set_xlabel('时间步 (Step)')
            ax2.grid(True, linestyle='--', alpha=0.6)
            ax2.legend()
            
            fig.tight_layout()
            
            # 使用 eval_step 和 PID 创建唯一的文件名以避免竞态条件
            pid = os.getpid()
            if eval_step is not None:
                filename = f'performance_eval_step_{eval_step}_episode_{self.episode_num}_pid_{pid}.png'
            else:
                filename = f'performance_episode_{self.episode_num}_pid_{pid}.png'

            if prefix:
                filename = f'{prefix}_{filename}'
            save_path = os.path.join(self.log_dir, filename)
            fig.savefig(save_path, dpi=200, bbox_inches='tight')
            plt.close(fig)
            print(f"性能图表已保存: {save_path}")

        except Exception as e:
            print(f"生成性能图表时出错: {e}")
