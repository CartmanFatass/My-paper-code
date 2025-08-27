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
        
        # 扩展的数据存储 - 包含所有环境提供的丰富信息
        self.history = {
            'steps': [],
            'uav_positions': [],
            'team_skills': [],
            'agent_skills': [],
            
            # 基础性能指标
            'connectivity': [],
            'throughput': [],
            'coverage_ratios': [],
            'avg_throughput_per_user': [],
            
            # 网络健康度指标
            'rt_final_health_score': [],
            'connectivity_score': [],
            'role_diversity_bonus': [],
            'effective_coverage_score': [],
            'dispersion_penalty': [],
            'serving_uavs_count': [],
            'pure_relay_uavs_count': [],
            'weighted_serving_score': [],
            
            # 网络拓扑指标
            'avg_hops': [],
            'connected_uavs': [],
            'uavs_with_backhaul': [],
            'connectivity_ratio': [],
            
            # 用户服务指标
            'total_connected_users': [],
            'served_users': [],
            'service_rate': [],
            
            # 静态信息
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
        
        # === 记录基础性能指标 ===
        self.history['connectivity'].append(reward_info.get('effective_connected_users', 0))
        self.history['throughput'].append(reward_info.get('system_throughput_mbps', 0))
        self.history['avg_throughput_per_user'].append(reward_info.get('avg_throughput_per_user_mbps', 0))
        
        # 计算并记录覆盖率
        n_users = self.config.n_users
        served_users = reward_info.get('effective_connected_users', 0)
        coverage_ratio = served_users / n_users if n_users > 0 else 0
        self.history['coverage_ratios'].append(coverage_ratio)
        
        # === 记录网络健康度指标 ===
        self.history['rt_final_health_score'].append(reward_info.get('rt_final_health_score', 0))
        self.history['connectivity_score'].append(reward_info.get('connectivity_score', 0))
        self.history['role_diversity_bonus'].append(reward_info.get('role_diversity_bonus', 0))
        self.history['effective_coverage_score'].append(reward_info.get('effective_coverage_score', 0))
        self.history['dispersion_penalty'].append(reward_info.get('dispersion_penalty', 0))
        self.history['serving_uavs_count'].append(reward_info.get('serving_uavs_count', 0))
        self.history['pure_relay_uavs_count'].append(reward_info.get('pure_relay_uavs_count', 0))
        self.history['weighted_serving_score'].append(reward_info.get('weighted_serving_score', 0))
        
        # === 记录网络拓扑指标 ===
        self.history['avg_hops'].append(reward_info.get('avg_hops', 0))
        self.history['connected_uavs'].append(reward_info.get('connected_uavs', 0))
        self.history['uavs_with_backhaul'].append(reward_info.get('uavs_with_backhaul', 0))
        self.history['connectivity_ratio'].append(reward_info.get('connectivity_ratio', 0))
        
        # === 记录用户服务指标 ===
        self.history['total_connected_users'].append(reward_info.get('total_connected_users', 0))
        self.history['served_users'].append(reward_info.get('served_users', served_users))
        self.history['service_rate'].append(reward_info.get('service_rate', coverage_ratio))

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
        self._create_health_score_analysis(prefix=prefix, eval_step=eval_step)

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
        生成并保存综合性能指标仪表板，包含所有丰富的性能数据。
        
        参数:
            prefix (str, optional): 添加到文件名开头的前缀。
            eval_step (int, optional): 当前的训练总步数，用于唯一标识评估图像。
        """
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'Microsoft YaHei']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 创建一个3x3的子图网格，展示全面的性能指标
            fig, axes = plt.subplots(3, 3, figsize=(18, 15))
            fig.suptitle(f'评估 Episode {self.episode_num}: 综合性能指标仪表板', fontsize=16, fontweight='bold')
            
            steps = self.history['steps']
            
            # === 第一行：核心性能指标 ===
            # 1. 覆盖率和连接用户数
            ax1 = axes[0, 0]
            ax1.plot(steps, self.history['coverage_ratios'], 'b-', linewidth=2, label='覆盖率')
            ax1_twin = ax1.twinx()
            ax1_twin.plot(steps, self.history['connectivity'], 'r--', linewidth=2, label='有效连接用户数')
            ax1.set_ylabel('覆盖率', color='b')
            ax1_twin.set_ylabel('连接用户数', color='r')
            ax1.set_title('用户覆盖性能')
            ax1.grid(True, alpha=0.3)
            ax1.legend(loc='upper left')
            ax1_twin.legend(loc='upper right')
            
            # 2. 系统吞吐量
            ax2 = axes[0, 1]
            ax2.plot(steps, self.history['throughput'], 'g-', linewidth=2, label='系统总吞吐量')
            ax2.plot(steps, self.history['avg_throughput_per_user'], 'orange', linestyle='--', linewidth=2, label='平均用户吞吐量')
            ax2.set_ylabel('吞吐量 (Mbps)')
            ax2.set_title('系统吞吐量性能')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            # 3. 网络健康度总分
            ax3 = axes[0, 2]
            ax3.plot(steps, self.history['rt_final_health_score'], 'purple', linewidth=3, label='网络健康度总分')
            ax3.set_ylabel('健康度分数')
            ax3.set_title('网络健康度评分')
            ax3.grid(True, alpha=0.3)
            ax3.legend()
            
            # === 第二行：网络健康度组成部分 ===
            # 4. 连接性和角色多样性
            ax4 = axes[1, 0]
            ax4.plot(steps, self.history['connectivity_score'], 'cyan', linewidth=2, label='连接性得分')
            ax4.plot(steps, self.history['role_diversity_bonus'], 'magenta', linewidth=2, label='角色多样性奖励')
            ax4.set_ylabel('得分')
            ax4.set_title('网络连接性与角色多样性')
            ax4.grid(True, alpha=0.3)
            ax4.legend()
            
            # 5. 有效覆盖和分散惩罚
            ax5 = axes[1, 1]
            ax5.plot(steps, self.history['effective_coverage_score'], 'green', linewidth=2, label='有效覆盖得分')
            ax5_twin = ax5.twinx()
            ax5_twin.plot(steps, self.history['dispersion_penalty'], 'red', linewidth=2, label='分散惩罚')
            ax5.set_ylabel('覆盖得分', color='green')
            ax5_twin.set_ylabel('惩罚值', color='red')
            ax5.set_title('覆盖效果与空间分散')
            ax5.grid(True, alpha=0.3)
            ax5.legend(loc='upper left')
            ax5_twin.legend(loc='upper right')
            
            # 6. UAV角色分布
            ax6 = axes[1, 2]
            ax6.plot(steps, self.history['serving_uavs_count'], 'blue', linewidth=2, marker='o', markersize=3, label='服务型UAV数量')
            ax6.plot(steps, self.history['pure_relay_uavs_count'], 'red', linewidth=2, marker='s', markersize=3, label='纯中继UAV数量')
            ax6.plot(steps, self.history['weighted_serving_score'], 'orange', linewidth=2, marker='^', markersize=3, label='加权服务贡献')
            ax6.set_ylabel('数量/得分')
            ax6.set_title('UAV角色分布')
            ax6.grid(True, alpha=0.3)
            ax6.legend()
            
            # === 第三行：网络拓扑和服务质量 ===
            # 7. 网络拓扑指标
            ax7 = axes[2, 0]
            ax7.plot(steps, self.history['avg_hops'], 'brown', linewidth=2, label='平均跳数')
            ax7_twin = ax7.twinx()
            ax7_twin.plot(steps, self.history['connected_uavs'], 'navy', linewidth=2, label='已连接UAV数')
            ax7_twin.plot(steps, self.history['connectivity_ratio'], 'teal', linewidth=2, linestyle='--', label='连接比例')
            ax7.set_ylabel('跳数', color='brown')
            ax7_twin.set_ylabel('UAV数量/比例', color='navy')
            ax7.set_title('网络拓扑结构')
            ax7.grid(True, alpha=0.3)
            ax7.legend(loc='upper left')
            ax7_twin.legend(loc='upper right')
            
            # 8. 用户服务质量对比
            ax8 = axes[2, 1]
            ax8.plot(steps, self.history['total_connected_users'], 'lightblue', linewidth=2, label='总连接用户数')
            ax8.plot(steps, self.history['served_users'], 'darkblue', linewidth=2, label='有效服务用户数')
            ax8.plot(steps, self.history['service_rate'], 'green', linewidth=2, linestyle='--', label='服务率')
            ax8.set_ylabel('用户数/服务率')
            ax8.set_title('用户服务质量')
            ax8.grid(True, alpha=0.3)
            ax8.legend()
            
            # 9. 关键指标汇总（最后一个子图显示最终值）
            ax9 = axes[2, 2]
            ax9.axis('off')  # 关闭坐标轴，用作文本显示
            
            # 计算最终值
            final_coverage = self.history['coverage_ratios'][-1] if self.history['coverage_ratios'] else 0
            final_throughput = self.history['throughput'][-1] if self.history['throughput'] else 0
            final_health = self.history['rt_final_health_score'][-1] if self.history['rt_final_health_score'] else 0
            final_hops = self.history['avg_hops'][-1] if self.history['avg_hops'] else 0
            final_serving_uavs = self.history['serving_uavs_count'][-1] if self.history['serving_uavs_count'] else 0
            final_relay_uavs = self.history['pure_relay_uavs_count'][-1] if self.history['pure_relay_uavs_count'] else 0
            
            # 显示关键指标汇总
            summary_text = f"""
关键指标汇总 (最终值)

📊 覆盖性能:
   • 覆盖率: {final_coverage:.1%}
   • 连接用户: {self.history['connectivity'][-1] if self.history['connectivity'] else 0}/{self.config.n_users}

🚀 网络性能:
   • 系统吞吐量: {final_throughput:.1f} Mbps
   • 网络健康度: {final_health:.3f}
   • 平均跳数: {final_hops:.1f}

🛰️ UAV角色分布:
   • 服务型UAV: {final_serving_uavs}
   • 中继型UAV: {final_relay_uavs}
   • 总UAV数: {self.config.n_agents}

📈 团队技能:
   • 最终团队技能: {self.history['team_skills'][-1] if self.history['team_skills'] else 'N/A'}
            """
            
            ax9.text(0.05, 0.95, summary_text, transform=ax9.transAxes, fontsize=10,
                    verticalalignment='top', fontfamily='monospace',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.8))
            ax9.set_title('性能汇总', fontweight='bold')
            
            # 设置所有子图的x轴标签（除了汇总图）
            for i in range(3):
                for j in range(2):  # 前两列需要x轴标签
                    axes[i, j].set_xlabel('时间步 (Step)')
            
            plt.tight_layout()
            
            # 使用 eval_step 和 PID 创建唯一的文件名以避免竞态条件
            pid = os.getpid()
            if eval_step is not None:
                filename = f'comprehensive_performance_eval_step_{eval_step}_episode_{self.episode_num}_pid_{pid}.png'
            else:
                filename = f'comprehensive_performance_episode_{self.episode_num}_pid_{pid}.png'

            if prefix:
                filename = f'{prefix}_{filename}'
            save_path = os.path.join(self.log_dir, filename)
            fig.savefig(save_path, dpi=200, bbox_inches='tight')
            plt.close(fig)
            print(f"综合性能仪表板已保存: {save_path}")

        except Exception as e:
            print(f"生成综合性能图表时出错: {e}")
            import traceback
            traceback.print_exc()

    def _create_health_score_analysis(self, prefix='', eval_step=None):
        """
        生成网络健康度组成部分的详细分析图表。
        
        参数:
            prefix (str, optional): 添加到文件名开头的前缀。
            eval_step (int, optional): 当前的训练总步数，用于唯一标识评估图像。
        """
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'Microsoft YaHei']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 创建2x2的子图网格，专门分析网络健康度
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle(f'评估 Episode {self.episode_num}: 网络健康度深度分析', fontsize=16, fontweight='bold')
            
            steps = self.history['steps']
            
            # === 左上：健康度总分与组成部分堆叠图 ===
            ax1 = axes[0, 0]
            
            # 从配置中获取权重（如果可用）
            w_connectivity = getattr(self.config, 'w_connectivity', 0.5)
            w_diversity = getattr(self.config, 'w_diversity', 1.0)
            w_coverage = getattr(self.config, 'w_coverage', 1.0)
            w_dispersion = getattr(self.config, 'w_dispersion', 0.05)
            
            # 计算各组成部分的加权贡献
            connectivity_contribution = np.array(self.history['connectivity_score']) * w_connectivity
            diversity_contribution = np.array(self.history['role_diversity_bonus']) * w_diversity
            coverage_contribution = np.array(self.history['effective_coverage_score']) * w_coverage
            dispersion_contribution = np.array(self.history['dispersion_penalty']) * w_dispersion
            
            # 创建堆叠面积图
            ax1.fill_between(steps, 0, connectivity_contribution, alpha=0.7, label=f'连接性贡献 (×{w_connectivity})', color='cyan')
            ax1.fill_between(steps, connectivity_contribution, 
                           connectivity_contribution + diversity_contribution, 
                           alpha=0.7, label=f'角色多样性贡献 (×{w_diversity})', color='magenta')
            ax1.fill_between(steps, connectivity_contribution + diversity_contribution,
                           connectivity_contribution + diversity_contribution + coverage_contribution,
                           alpha=0.7, label=f'覆盖贡献 (×{w_coverage})', color='green')
            
            # 分散惩罚用负值显示
            ax1.fill_between(steps, connectivity_contribution + diversity_contribution + coverage_contribution,
                           connectivity_contribution + diversity_contribution + coverage_contribution - dispersion_contribution,
                           alpha=0.7, label=f'分散惩罚 (×{w_dispersion})', color='red')
            
            # 叠加总健康度分数线
            ax1.plot(steps, self.history['rt_final_health_score'], 'k-', linewidth=3, label='总健康度分数')
            
            ax1.set_ylabel('健康度分数')
            ax1.set_title('健康度组成部分堆叠分析')
            ax1.grid(True, alpha=0.3)
            ax1.legend(loc='upper left', fontsize=9)
            
            # === 右上：UAV角色演化分析 ===
            ax2 = axes[0, 1]
            
            # 计算角色比例
            total_uavs = self.config.n_agents
            serving_ratio = np.array(self.history['serving_uavs_count']) / total_uavs
            relay_ratio = np.array(self.history['pure_relay_uavs_count']) / total_uavs
            disconnected_ratio = 1 - serving_ratio - relay_ratio
            
            # 创建堆叠面积图显示角色分布
            ax2.fill_between(steps, 0, serving_ratio, alpha=0.8, label='服务型UAV比例', color='blue')
            ax2.fill_between(steps, serving_ratio, serving_ratio + relay_ratio, 
                           alpha=0.8, label='中继型UAV比例', color='orange')
            ax2.fill_between(steps, serving_ratio + relay_ratio, 1, 
                           alpha=0.8, label='未连接UAV比例', color='gray')
            
            # 叠加加权服务贡献
            ax2_twin = ax2.twinx()
            ax2_twin.plot(steps, self.history['weighted_serving_score'], 'r-', linewidth=2, label='加权服务贡献')
            ax2_twin.set_ylabel('加权服务贡献', color='r')
            
            ax2.set_ylabel('UAV角色比例')
            ax2.set_title('UAV角色分布演化')
            ax2.set_ylim(0, 1)
            ax2.grid(True, alpha=0.3)
            ax2.legend(loc='upper left', fontsize=9)
            ax2_twin.legend(loc='upper right', fontsize=9)
            
            # === 左下：网络效率分析 ===
            ax3 = axes[1, 0]
            
            # 计算效率指标
            coverage_efficiency = np.array(self.history['coverage_ratios']) / np.maximum(np.array(self.history['connectivity_ratio']), 0.01)
            throughput_per_uav = np.array(self.history['throughput']) / np.maximum(np.array(self.history['connected_uavs']), 1)
            
            ax3.plot(steps, coverage_efficiency, 'g-', linewidth=2, label='覆盖效率 (覆盖率/连接比例)')
            ax3_twin = ax3.twinx()
            ax3_twin.plot(steps, throughput_per_uav, 'b--', linewidth=2, label='单UAV平均吞吐量')
            ax3_twin.plot(steps, self.history['avg_hops'], 'r:', linewidth=2, label='平均跳数')
            
            ax3.set_ylabel('覆盖效率', color='g')
            ax3_twin.set_ylabel('吞吐量(Mbps)/跳数', color='b')
            ax3.set_title('网络效率指标')
            ax3.grid(True, alpha=0.3)
            ax3.legend(loc='upper left', fontsize=9)
            ax3_twin.legend(loc='upper right', fontsize=9)
            
            # === 右下：性能稳定性分析 ===
            ax4 = axes[1, 1]
            
            # 计算滑动窗口标准差（稳定性指标）
            window_size = min(20, len(steps) // 4)  # 动态窗口大小
            if window_size >= 2:
                coverage_stability = []
                health_stability = []
                throughput_stability = []
                
                for i in range(len(steps)):
                    start_idx = max(0, i - window_size + 1)
                    end_idx = i + 1
                    
                    coverage_window = self.history['coverage_ratios'][start_idx:end_idx]
                    health_window = self.history['rt_final_health_score'][start_idx:end_idx]
                    throughput_window = self.history['throughput'][start_idx:end_idx]
                    
                    coverage_stability.append(np.std(coverage_window))
                    health_stability.append(np.std(health_window))
                    throughput_stability.append(np.std(throughput_window))
                
                ax4.plot(steps, coverage_stability, 'g-', linewidth=2, label=f'覆盖率稳定性 (窗口={window_size})')
                ax4.plot(steps, health_stability, 'purple', linewidth=2, label=f'健康度稳定性 (窗口={window_size})')
                ax4.plot(steps, throughput_stability, 'orange', linewidth=2, label=f'吞吐量稳定性 (窗口={window_size})')
                
                ax4.set_ylabel('标准差 (稳定性指标)')
                ax4.set_title('性能稳定性分析 (越低越稳定)')
                ax4.grid(True, alpha=0.3)
                ax4.legend(fontsize=9)
            else:
                ax4.text(0.5, 0.5, '数据点不足\n无法进行稳定性分析', 
                        transform=ax4.transAxes, ha='center', va='center', fontsize=12)
                ax4.set_title('性能稳定性分析')
            
            # 设置所有子图的x轴标签
            for i in range(2):
                for j in range(2):
                    axes[i, j].set_xlabel('时间步 (Step)')
            
            plt.tight_layout()
            
            # 使用 eval_step 和 PID 创建唯一的文件名以避免竞态条件
            pid = os.getpid()
            if eval_step is not None:
                filename = f'health_analysis_eval_step_{eval_step}_episode_{self.episode_num}_pid_{pid}.png'
            else:
                filename = f'health_analysis_episode_{self.episode_num}_pid_{pid}.png'

            if prefix:
                filename = f'{prefix}_{filename}'
            save_path = os.path.join(self.log_dir, filename)
            fig.savefig(save_path, dpi=200, bbox_inches='tight')
            plt.close(fig)
            print(f"网络健康度分析图已保存: {save_path}")

        except Exception as e:
            print(f"生成网络健康度分析图时出错: {e}")
            import traceback
            traceback.print_exc()
