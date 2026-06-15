import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

class VisualizationManager:
    """
    Unified management for data collection and visualization during evaluation.
    """
    def __init__(self, episode_num, log_dir, config):
        """
        Initialize visualization manager.

        Args:
            episode_num (int): Current evaluation episode number.
            log_dir (str): Directory to save plots.
            config: Training configuration object.
        """
        self.episode_num = episode_num
        # 为每个并行环境创建独立的子文件夹
        self.log_dir = os.path.join(log_dir, 'evaluation_plots', f'episode_{episode_num}')
        os.makedirs(self.log_dir, exist_ok=True)
        self.config = config
        
        # Extended data storage - includes all rich information provided by environment
        self.history = {
            'steps': [],
            'uav_positions': [],
            'user_positions': [],  # Add user position tracking for mobility visualization
            'team_skills': [],
            'agent_skills': [],
            
            # Basic performance metrics
            'connectivity': [],
            'throughput': [],
            'coverage_ratios': [],
            'avg_throughput_per_user': [],
            
            # Network health metrics
            'rt_final_health_score': [],
            'load_balance_reward': [],
            'load_balance_penalty': [],
            'robustness_penalty': [],
            'backhaul_outage_penalty': [],
            'full_disconnect_penalty': [],
            'coverage_drop_penalty': [],
            'outage_memory_penalty': [],
            'relay_break_penalty': [],
            'backhaul_margin_penalty': [],

            # Backhaul robustness metrics for load_balance mode
            'backhaul_outage_users': [],
            'backhaul_outage_ratio': [],
            'service_drop_users': [],
            'service_drop_ratio': [],
            'backhaul_drop_users': [],
            'backhaul_drop_ratio': [],
            'full_network_disconnect': [],
            'full_disconnect_streak': [],
            'coverage_drop_ratio': [],
            'backhaul_outage_ema': [],
            'instant_outage_intensity': [],
            'relay_route_lost_uavs': [],
            'relay_route_lost_users': [],
            'relay_route_loss_ratio': [],
            'relay_route_loss_prev_served_ratio': [],
            'prev_backhaul_served_users': [],
            'current_backhaul_served_users': [],
            'backhaul_margin_penalty_raw': [],
            'min_serving_backhaul_bottleneck_mbps': [],
            'avg_serving_backhaul_bottleneck_mbps': [],
            'backhaul_guard_checked_actions': [],
            'backhaul_guard_blocked_actions': [],
            
            # Network topology metrics
            'avg_hops': [],
            'connected_uavs': [],
            'uavs_with_backhaul': [],
            'connectivity_ratio': [],
            
            # User service metrics
            'total_connected_users': [],
            'served_users': [],
            'service_rate': [],
            
            # 【新增】连接数据
            'connections': [],
            'routing_paths': [],
            
            # Static information
            'static_info': None
        }

    def record_step(self, step_count, uav_positions, team_skill, agent_skills, reward_info, static_info=None, connections=None, routing_paths=None):
        """
        Record data for each step during evaluation.

        Args:
            step_count (int): Current step number.
            uav_positions (np.array): Positions of all UAVs.
            team_skill (int): Current team skill.
            agent_skills (list): Individual skills of each agent.
            reward_info (dict): Dictionary containing performance metrics.
            static_info (dict, optional): Static environment information, such as user positions.
            connections (np.array, optional): UAV-user connection matrix.
            routing_paths (dict, optional): Backhaul routing paths.
        """
        # Check if data recording order is correct to prevent data corruption from multiprocessing/threading
        if self.history['steps'] and step_count <= self.history['steps'][-1]:
            print(f"Warning: Detected out-of-order or duplicate step recording (current: {step_count}, previous: {self.history['steps'][-1]}). "
                  f"This may be caused by race conditions in multiprocessing environments. Clearing current instance history data to ensure correct visualization.")
            # Clear history data and start new recording sequence
            for key in self.history:
                if isinstance(self.history[key], list):
                    self.history[key] = []
            self.history['static_info'] = None

        self.history['steps'].append(step_count)
        self.history['uav_positions'].append(uav_positions.copy())
        self.history['team_skills'].append(team_skill)
        self.history['agent_skills'].append(agent_skills)
        
        # 【新增】记录连接数据
        self.history['connections'].append(connections)
        self.history['routing_paths'].append(routing_paths)
        
        # Record user positions for mobility visualization
        # Only get current user positions from reward_info (dynamic information)
        # Do NOT use static_info as fallback since it contains only initial positions
        current_user_positions = None
        if reward_info and 'user_positions' in reward_info:
            current_user_positions = reward_info['user_positions']
        
        if current_user_positions is not None:
            self.history['user_positions'].append(np.array(current_user_positions).copy())
        else:
            # If no dynamic user positions available, use empty array to maintain consistency
            # This prevents misleading visualization with static initial positions
            self.history['user_positions'].append(np.array([]))
        
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
        self.history['load_balance_reward'].append(reward_info.get('load_balance_reward', reward_info.get('rt_final_health_score', 0)))
        self.history['load_balance_penalty'].append(reward_info.get('load_balance_penalty', 0))
        self.history['robustness_penalty'].append(reward_info.get('robustness_penalty', 0))
        self.history['backhaul_outage_penalty'].append(reward_info.get('backhaul_outage_penalty', 0))
        self.history['full_disconnect_penalty'].append(reward_info.get('full_disconnect_penalty', 0))
        self.history['coverage_drop_penalty'].append(reward_info.get('coverage_drop_penalty', 0))
        self.history['outage_memory_penalty'].append(reward_info.get('outage_memory_penalty', 0))
        self.history['relay_break_penalty'].append(reward_info.get('relay_break_penalty', 0))
        self.history['backhaul_margin_penalty'].append(reward_info.get('backhaul_margin_penalty', 0))

        # === 记录回程健壮性指标 ===
        self.history['backhaul_outage_users'].append(reward_info.get('backhaul_outage_users', 0))
        self.history['backhaul_outage_ratio'].append(reward_info.get('backhaul_outage_ratio', 0))
        self.history['service_drop_users'].append(reward_info.get('service_drop_users', 0))
        self.history['service_drop_ratio'].append(reward_info.get('service_drop_ratio', 0))
        self.history['backhaul_drop_users'].append(reward_info.get('backhaul_drop_users', 0))
        self.history['backhaul_drop_ratio'].append(reward_info.get('backhaul_drop_ratio', 0))
        self.history['full_network_disconnect'].append(reward_info.get('full_network_disconnect', 0))
        self.history['full_disconnect_streak'].append(reward_info.get('full_disconnect_streak', 0))
        self.history['coverage_drop_ratio'].append(reward_info.get('coverage_drop_ratio', 0))
        self.history['backhaul_outage_ema'].append(reward_info.get('backhaul_outage_ema', 0))
        self.history['instant_outage_intensity'].append(reward_info.get('instant_outage_intensity', 0))
        self.history['relay_route_lost_uavs'].append(reward_info.get('relay_route_lost_uavs', 0))
        self.history['relay_route_lost_users'].append(reward_info.get('relay_route_lost_users', 0))
        self.history['relay_route_loss_ratio'].append(reward_info.get('relay_route_loss_ratio', 0))
        self.history['relay_route_loss_prev_served_ratio'].append(reward_info.get('relay_route_loss_prev_served_ratio', 0))
        self.history['prev_backhaul_served_users'].append(reward_info.get('prev_backhaul_served_users', 0))
        self.history['current_backhaul_served_users'].append(reward_info.get('current_backhaul_served_users', 0))
        self.history['backhaul_margin_penalty_raw'].append(reward_info.get('backhaul_margin_penalty_raw', 0))
        self.history['min_serving_backhaul_bottleneck_mbps'].append(reward_info.get('min_serving_backhaul_bottleneck_mbps', 0))
        self.history['avg_serving_backhaul_bottleneck_mbps'].append(reward_info.get('avg_serving_backhaul_bottleneck_mbps', 0))
        self.history['backhaul_guard_checked_actions'].append(reward_info.get('backhaul_guard_checked_actions', 0))
        self.history['backhaul_guard_blocked_actions'].append(reward_info.get('backhaul_guard_blocked_actions', 0))
        
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

    def generate_plots(self, prefix='', eval_step=None, topology_only=False):
        """
        Generate all relevant charts after episode completion.
        
        Args:
            prefix (str, optional): Prefix to add to the beginning of filename.
            eval_step (int, optional): Current training total steps for unique evaluation image identification.
            topology_only (bool, optional): If True, only generate the topology plot.
        """
        if not self.history['steps']:
            print("No data available for plot generation.")
            return

        if topology_only:
            # Only generate the topology plot for snapshots
            self._create_topology_plot(prefix=prefix, eval_step=eval_step)
        else:
            # For regular episode completion, generate all plots
            self._create_topology_plot(prefix=prefix, eval_step=eval_step)
            self._create_performance_plot(prefix=prefix, eval_step=eval_step)
            self._create_relay_backhaul_analysis(prefix=prefix, eval_step=eval_step)

    def _create_topology_plot(self, prefix='', eval_step=None):
        """
        Generate and save a 2D topology snapshot for the final step of the episode,
        showing node positions and connections.
        """
        try:
            # 设置支持中文和表情符号的字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial', 'Liberation Sans', 'Noto Color Emoji']
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, ax = plt.subplots(figsize=(12, 10))
            
            # Get data for the last recorded step
            last_step_idx = -1
            uav_positions = self.history['uav_positions'][last_step_idx]
            user_positions = self.history['user_positions'][last_step_idx]
            connections = self.history['connections'][last_step_idx]
            routing_paths = self.history['routing_paths'][last_step_idx]
            
            # Plot static entities from the beginning
            static_info = self.history['static_info']
            if static_info:
                if 'ground_bs_positions' in static_info and static_info.get('ground_bs_positions') is not None:
                    bs_pos = static_info['ground_bs_positions']
                    ax.scatter(bs_pos[:, 0], bs_pos[:, 1], c='black', marker='s', s=200, label='Ground Base Stations', zorder=5)

            # Plot users at their final positions
            if user_positions is not None and user_positions.ndim == 2 and user_positions.shape[0] > 0:
                ax.scatter(user_positions[:, 0], user_positions[:, 1], c='blue', marker='.', s=50, label='Users', zorder=5)

            # Plot UAVs at their final positions
            for i in range(self.config.n_agents):
                color = plt.cm.jet(i / self.config.n_agents)
                pos = uav_positions[i, :2]
                ax.scatter(pos[0], pos[1], marker='^', color=color, s=120, edgecolors='black', zorder=6, label=f'UAV {i}')
                ax.text(pos[0] + 10, pos[1] + 10, f'UAV{i}', fontsize=9)

            # Plot connections: User -> UAV with a less obtrusive style
            if connections is not None and user_positions is not None:
                # Add a single legend entry for all user links
                ax.plot([], [], 'g:', alpha=0.5, label='User Links')
                for uav_idx in range(connections.shape[0]):
                    for user_idx in range(connections.shape[1]):
                        if connections[uav_idx, user_idx]:
                            uav_pos = uav_positions[uav_idx]
                            user_pos = user_positions[user_idx]
                            # Use a dotted line to reduce visual clutter
                            ax.plot([uav_pos[0], user_pos[0]], [uav_pos[1], user_pos[1]], 'g:', alpha=0.5, zorder=3)

            # 【新增】绘制无人机飞行轨迹（在背景中）
            if len(self.history['uav_positions']) > 1:  # 确保有足够的历史位置数据
                # 仅为第一个无人机添加起点图例，避免重复
                ax.scatter([], [], color='gray', marker='*', s=80, alpha=0.8, label='UAV Initial Position')
                for i in range(self.config.n_agents):
                    # 提取该无人机的完整飞行轨迹
                    trajectory_x = [positions[i, 0] for positions in self.history['uav_positions']]
                    trajectory_y = [positions[i, 1] for positions in self.history['uav_positions']]
                    
                    # 使用与无人机相同的颜色但更淡的透明度绘制轨迹
                    color = plt.cm.jet(i / self.config.n_agents)
                    ax.plot(trajectory_x, trajectory_y, color=color, alpha=0.3, linewidth=1.5, linestyle='-', zorder=1)
                    
                    # 在起点绘制一个星形标记，以区别于用户
                    ax.scatter(trajectory_x[0], trajectory_y[0], color=color, marker='*', s=80, alpha=0.8, zorder=2, edgecolors='white', linewidths=0.5)

            # Plot routing paths (backhaul) - Reworked for robustness
            if routing_paths and static_info and 'ground_bs_positions' in static_info:
                # --- Pre-build a robust node position lookup dictionary ---
                node_positions = {}
                # Add UAV positions
                for i in range(len(uav_positions)):
                    node_positions[('uav', i)] = uav_positions[i, :2]
                # Add Ground Base Station positions
                bs_positions = static_info['ground_bs_positions']
                for i in range(len(bs_positions)):
                    node_positions[('ground_bs', i)] = bs_positions[i, :2]

                backhaul_legend_added = False
                for uav_idx, (path, capacity) in routing_paths.items():
                    if not path or len(path) < 2:
                        continue
                    
                    for i in range(len(path) - 1):
                        node1_key = tuple(path[i]) # path is list of lists, convert to tuple for dict key
                        node2_key = tuple(path[i+1])
                        
                        pos1 = node_positions.get(node1_key)
                        pos2 = node_positions.get(node2_key)

                        if pos1 is not None and pos2 is not None:
                            label = 'Backhaul Routing Paths' if not backhaul_legend_added else None
                            ax.plot([pos1[0], pos2[0]], [pos1[1], pos2[1]], 
                                    'b--', alpha=0.9, linewidth=2.5, zorder=5, label=label)
                            backhaul_legend_added = True
                        else:
                            print(f"Warning: Could not find position for one or both nodes in path segment: {node1_key} -> {node2_key}")

            # --- Build legend ---
            handles, labels = ax.get_legend_handles_labels()
            by_label = {l: h for h, l in zip(handles, labels)} # remove duplicate labels
            
            final_coverage = self.history['coverage_ratios'][-1]
            team_skill_at_end = self.history['team_skills'][-1]
            info_elements = [
                Line2D([0], [0], color='w', label=f'Final Coverage: {final_coverage:.2%}'),
                Line2D([0], [0], color='w', label=f'Team Skill (Z): {team_skill_at_end}')
            ]
            
            all_handles = list(by_label.values()) + info_elements
            
            current_step = self.history['steps'][-1]
            ax.set_title(f'Evaluation Episode {self.episode_num}: Network Topology Snapshot at Step {current_step}')
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            
            area_size = static_info.get('area_size', 1000) if static_info else 1000
            ax.set_xlim(0, area_size)
            ax.set_ylim(0, area_size)
            ax.set_aspect('equal', adjustable='box')
            ax.legend(handles=all_handles, title="Legend & Information", loc='upper right', bbox_to_anchor=(1.4, 1.0))
            ax.grid(True, linestyle='--', alpha=0.5)
            
            plt.tight_layout(rect=[0, 0, 0.8, 1]) # Leave more space for legend
            
            # Use eval_step and PID to create unique filename to avoid race conditions
            pid = os.getpid()
            if eval_step is not None:
                filename = f'topology_snapshot_eval_step_{eval_step}_episode_{self.episode_num}_step_{current_step}_pid_{pid}.png'
            else:
                filename = f'topology_snapshot_episode_{self.episode_num}_step_{current_step}_pid_{pid}.png'
                
            if prefix:
                filename = f'{prefix}_{filename}'
            save_path = os.path.join(self.log_dir, filename)
            fig.savefig(save_path, dpi=200, bbox_inches='tight')
            plt.close(fig)
            print(f"Topology snapshot saved: {save_path}")

        except Exception as e:
            print(f"Error generating topology plot: {e}")

    def _create_performance_plot(self, prefix='', eval_step=None):
        """
        Generate and save comprehensive performance metrics dashboard with all rich performance data.
        
        Args:
            prefix (str, optional): Prefix to add to the beginning of filename.
            eval_step (int, optional): Current training total steps for unique evaluation image identification.
        """
        try:
            # 设置支持中文和表情符号的字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial', 'Liberation Sans', 'Noto Color Emoji']
            plt.rcParams['axes.unicode_minus'] = False
            
            # Create a 3x3 subplot grid to display comprehensive performance metrics
            fig, axes = plt.subplots(3, 3, figsize=(18, 15))
            fig.suptitle(f'Evaluation Episode {self.episode_num}: Comprehensive Performance Dashboard', fontsize=16, fontweight='bold')
            
            steps = self.history['steps']
            
            # === First Row: Core Performance Metrics ===
            # 1. Coverage Rate and Connected Users
            ax1 = axes[0, 0]
            ax1.plot(steps, self.history['coverage_ratios'], 'b-', linewidth=2, label='Coverage Rate')
            ax1_twin = ax1.twinx()
            ax1_twin.plot(steps, self.history['connectivity'], 'r--', linewidth=2, label='Effective Connected Users')
            ax1.set_ylabel('Coverage Rate', color='b')
            ax1_twin.set_ylabel('Connected Users', color='r')
            ax1.set_title('User Coverage Performance')
            ax1.grid(True, alpha=0.3)
            ax1.legend(loc='upper left')
            ax1_twin.legend(loc='upper right')
            
            # 2. System Throughput
            ax2 = axes[0, 1]
            ax2.plot(steps, self.history['throughput'], 'g-', linewidth=2, label='Total System Throughput')
            ax2.plot(steps, self.history['avg_throughput_per_user'], 'orange', linestyle='--', linewidth=2, label='Average User Throughput')
            ax2.set_ylabel('Throughput (Mbps)')
            ax2.set_title('System Throughput Performance')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            # 3. Load-balance reward and robustness penalty
            ax3 = axes[0, 2]
            ax3.plot(steps, self.history['load_balance_reward'], 'purple', linewidth=2, label='Load Balance Reward')
            ax3.plot(steps, self.history['robustness_penalty'], 'red', linewidth=2, label='Robustness Penalty')
            ax3.plot(steps, self.history['load_balance_penalty'], 'gray', linestyle='--', linewidth=1.5, label='Load Penalty')
            ax3.set_ylabel('Reward / Penalty')
            ax3.set_title('Load Balance Reward & Robustness Cost')
            ax3.grid(True, alpha=0.3)
            ax3.legend()
            
            # === Second Row: Backhaul Robustness ===
            # 4. Relay route breakage
            ax4 = axes[1, 0]
            ax4.plot(steps, self.history['relay_route_loss_ratio'], 'red', linewidth=2, label='Relay Route Loss Ratio')
            ax4.plot(steps, self.history['relay_route_loss_prev_served_ratio'], 'darkred', linestyle='--', linewidth=2, label='Loss / Prev Backhaul Served')
            ax4_twin = ax4.twinx()
            ax4_twin.plot(steps, self.history['relay_route_lost_users'], 'black', linewidth=1.5, alpha=0.7, label='Lost Users')
            ax4.set_ylabel('Ratio', color='red')
            ax4_twin.set_ylabel('Users', color='black')
            ax4.set_title('Relay Backhaul Route Breakage')
            ax4.grid(True, alpha=0.3)
            ax4.legend(loc='upper left')
            ax4_twin.legend(loc='upper right')
            
            # 5. Backhaul bottleneck margin
            ax5 = axes[1, 1]
            ax5.plot(steps, self.history['min_serving_backhaul_bottleneck_mbps'], 'brown', linewidth=2, label='Min Serving Bottleneck')
            ax5.plot(steps, self.history['avg_serving_backhaul_bottleneck_mbps'], 'orange', linewidth=2, label='Avg Serving Bottleneck')
            target_mbps = getattr(self.config, 'backhaul_margin_target_mbps', 10.0)
            ax5.axhline(target_mbps, color='gray', linestyle=':', linewidth=1.5, label=f'Target {target_mbps:.1f} Mbps')
            ax5_twin = ax5.twinx()
            ax5_twin.plot(steps, self.history['backhaul_margin_penalty_raw'], 'red', linewidth=2, label='Margin Penalty')
            ax5.set_ylabel('Bottleneck (Mbps)', color='brown')
            ax5_twin.set_ylabel('Penalty', color='red')
            ax5.set_title('Backhaul Bottleneck Margin')
            ax5.grid(True, alpha=0.3)
            ax5.legend(loc='upper left')
            ax5_twin.legend(loc='upper right')
            
            # 6. Outage and service drop
            ax6 = axes[1, 2]
            ax6.plot(steps, self.history['backhaul_outage_ratio'], 'red', linewidth=2, label='Backhaul Outage Ratio')
            ax6.plot(steps, self.history['service_drop_ratio'], 'purple', linewidth=2, label='Service Drop Ratio')
            ax6.plot(steps, self.history['coverage_drop_ratio'], 'orange', linestyle='--', linewidth=1.5, label='Coverage Drop Ratio')
            ax6.plot(steps, self.history['full_network_disconnect'], 'black', linestyle=':', linewidth=1.5, label='Full Disconnect')
            ax6.set_ylabel('Ratio / Flag')
            ax6.set_title('Outage and Service Drop')
            ax6.grid(True, alpha=0.3)
            ax6.legend()
            
            # === Third Row: Network Topology and Service Quality ===
            # 7. Network Topology Metrics
            ax7 = axes[2, 0]
            ax7.plot(steps, self.history['avg_hops'], 'brown', linewidth=2, label='Average Hops')
            ax7_twin = ax7.twinx()
            ax7_twin.plot(steps, self.history['connected_uavs'], 'navy', linewidth=2, label='Connected UAVs')
            ax7_twin.plot(steps, self.history['connectivity_ratio'], 'teal', linewidth=2, linestyle='--', label='Connectivity Ratio')
            ax7.set_ylabel('Hops', color='brown')
            ax7_twin.set_ylabel('UAV Count/Ratio', color='navy')
            ax7.set_title('Network Topology Structure')
            ax7.grid(True, alpha=0.3)
            ax7.legend(loc='upper left')
            ax7_twin.legend(loc='upper right')
            
            # 8. Guard actions and user service quality
            ax8 = axes[2, 1]
            ax8.plot(steps, self.history['total_connected_users'], 'lightblue', linewidth=2, label='Access Connected Users')
            ax8.plot(steps, self.history['served_users'], 'darkblue', linewidth=2, label='Effectively Served Users')
            ax8_twin = ax8.twinx()
            ax8_twin.plot(steps, self.history['backhaul_guard_checked_actions'], 'gray', linestyle='--', linewidth=1.5, label='Guard Checked')
            ax8_twin.plot(steps, self.history['backhaul_guard_blocked_actions'], 'red', linestyle=':', linewidth=2, label='Guard Blocked')
            ax8.set_ylabel('Users', color='blue')
            ax8_twin.set_ylabel('Guard Actions', color='red')
            ax8.set_title('Service Quality and Backhaul Guard')
            ax8.grid(True, alpha=0.3)
            ax8.legend(loc='upper left')
            ax8_twin.legend(loc='upper right')
            
            # 9. Key Metrics Summary (last subplot shows final values)
            ax9 = axes[2, 2]
            ax9.axis('off')  # Turn off axes for text display
            
            # Calculate final values
            final_coverage = self.history['coverage_ratios'][-1] if self.history['coverage_ratios'] else 0
            final_throughput = self.history['throughput'][-1] if self.history['throughput'] else 0
            final_reward = self.history['load_balance_reward'][-1] if self.history['load_balance_reward'] else 0
            max_relay_loss = max(self.history['relay_route_loss_ratio']) if self.history['relay_route_loss_ratio'] else 0
            max_outage = max(self.history['backhaul_outage_ratio']) if self.history['backhaul_outage_ratio'] else 0
            min_bottleneck = min([v for v in self.history['min_serving_backhaul_bottleneck_mbps'] if v > 0], default=0)
            total_guard_blocked = sum(self.history['backhaul_guard_blocked_actions']) if self.history['backhaul_guard_blocked_actions'] else 0
            final_hops = self.history['avg_hops'][-1] if self.history['avg_hops'] else 0
            final_uavs_with_backhaul = self.history['uavs_with_backhaul'][-1] if self.history['uavs_with_backhaul'] else 0
            
            # Display key metrics summary
            summary_text = f"""
Key Metrics Summary (Final Values)

Coverage Performance:
   • Coverage Rate: {final_coverage:.1%}
   • Connected Users: {self.history['connectivity'][-1] if self.history['connectivity'] else 0}/{self.config.n_users}

Network Performance:
   • System Throughput: {final_throughput:.1f} Mbps
   • Load Balance Reward: {final_reward:.3f}
   • Average Hops: {final_hops:.1f}
   • UAVs With Backhaul: {final_uavs_with_backhaul}/{self.config.n_agents}

Backhaul Robustness:
   • Max Relay Loss Ratio: {max_relay_loss:.3f}
   • Max Backhaul Outage: {max_outage:.3f}
   • Min Serving Bottleneck: {min_bottleneck:.1f} Mbps
   • Guard Blocked Actions: {total_guard_blocked}

Team Skill:
   • Final Team Skill: {self.history['team_skills'][-1] if self.history['team_skills'] else 'N/A'}
            """
            
            ax9.text(0.05, 0.95, summary_text, transform=ax9.transAxes, fontsize=10,
                    verticalalignment='top', fontfamily='monospace',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.8))
            ax9.set_title('Performance Summary', fontweight='bold')
            
            # Set x-axis labels for all subplots (except summary plot)
            for i in range(3):
                for j in range(2):  # First two columns need x-axis labels
                    axes[i, j].set_xlabel('Time Step')
            
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
            print(f"Comprehensive performance dashboard saved: {save_path}")

        except Exception as e:
            print(f"Error generating comprehensive performance chart: {e}")
            import traceback
            traceback.print_exc()

    def _create_relay_backhaul_analysis(self, prefix='', eval_step=None):
        """
        Generate analysis charts for relay-route breakage and backhaul robustness.

        The old health-score component plots are intentionally not generated for
        load_balance mode because those component fields are not part of this reward.
        """
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial', 'Liberation Sans']
            plt.rcParams['axes.unicode_minus'] = False

            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle(f'Evaluation Episode {self.episode_num}: Relay Backhaul Deep Analysis', fontsize=16, fontweight='bold')

            steps = self.history['steps']

            # 1. Reward and penalty decomposition
            ax1 = axes[0, 0]
            ax1.plot(steps, self.history['load_balance_reward'], 'k-', linewidth=2.5, label='Load Balance Reward')
            ax1.plot(steps, self.history['robustness_penalty'], 'red', linewidth=2, label='Total Robustness Penalty')
            ax1.plot(steps, self.history['relay_break_penalty'], 'darkred', linestyle='--', linewidth=2, label='Relay Break Penalty')
            ax1.plot(steps, self.history['backhaul_margin_penalty'], 'orange', linestyle='--', linewidth=2, label='Backhaul Margin Penalty')
            ax1.plot(steps, self.history['backhaul_outage_penalty'], 'purple', linestyle=':', linewidth=2, label='Outage Penalty')
            ax1.set_ylabel('Reward / Penalty')
            ax1.set_title('Load Balance Reward Decomposition')
            ax1.grid(True, alpha=0.3)
            ax1.legend(fontsize=8)

            # 2. Relay breakage and outage events
            ax2 = axes[0, 1]
            ax2.plot(steps, self.history['relay_route_loss_ratio'], 'red', linewidth=2, label='Relay Route Loss Ratio')
            ax2.plot(steps, self.history['backhaul_outage_ratio'], 'purple', linewidth=2, label='Backhaul Outage Ratio')
            ax2.plot(steps, self.history['service_drop_ratio'], 'orange', linewidth=2, label='Service Drop Ratio')
            ax2.plot(steps, self.history['full_network_disconnect'], 'black', linestyle=':', linewidth=1.5, label='Full Disconnect Flag')
            ax2.set_ylabel('Ratio / Flag')
            ax2.set_title('Relay Breakage and Service Outage')
            ax2.grid(True, alpha=0.3)
            ax2.legend(fontsize=8)

            # 3. Bottleneck capacity margin
            ax3 = axes[1, 0]
            ax3.plot(steps, self.history['min_serving_backhaul_bottleneck_mbps'], 'brown', linewidth=2, label='Min Serving Bottleneck')
            ax3.plot(steps, self.history['avg_serving_backhaul_bottleneck_mbps'], 'orange', linewidth=2, label='Avg Serving Bottleneck')
            target_mbps = getattr(self.config, 'backhaul_margin_target_mbps', 10.0)
            guard_mbps = getattr(self.config, 'backhaul_guard_min_capacity_mbps', 5.0)
            ax3.axhline(target_mbps, color='gray', linestyle='--', linewidth=1.5, label=f'Margin Target {target_mbps:.1f} Mbps')
            ax3.axhline(guard_mbps, color='red', linestyle=':', linewidth=1.5, label=f'Guard Min {guard_mbps:.1f} Mbps')
            ax3_twin = ax3.twinx()
            ax3_twin.plot(steps, self.history['backhaul_margin_penalty_raw'], 'red', linewidth=2, alpha=0.7, label='Margin Penalty Raw')
            ax3.set_ylabel('Bottleneck Capacity (Mbps)', color='brown')
            ax3_twin.set_ylabel('Penalty', color='red')
            ax3.set_title('Backhaul Bottleneck Capacity Margin')
            ax3.grid(True, alpha=0.3)
            ax3.legend(loc='upper left', fontsize=8)
            ax3_twin.legend(loc='upper right', fontsize=8)

            # 4. Guard behavior and rolling instability
            ax4 = axes[1, 1]
            ax4.plot(steps, self.history['backhaul_guard_checked_actions'], 'gray', linewidth=1.5, label='Guard Checked Actions')
            ax4.plot(steps, self.history['backhaul_guard_blocked_actions'], 'red', linewidth=2, label='Guard Blocked Actions')

            window_size = min(20, len(steps) // 4)
            if window_size >= 2:
                relay_loss_stability = []
                outage_stability = []
                throughput_stability = []

                for i in range(len(steps)):
                    start_idx = max(0, i - window_size + 1)
                    end_idx = i + 1
                    relay_loss_stability.append(np.std(self.history['relay_route_loss_ratio'][start_idx:end_idx]))
                    outage_stability.append(np.std(self.history['backhaul_outage_ratio'][start_idx:end_idx]))
                    throughput_stability.append(np.std(self.history['throughput'][start_idx:end_idx]))

                ax4_twin = ax4.twinx()
                ax4_twin.plot(steps, relay_loss_stability, 'darkred', linestyle='--', linewidth=1.5, label=f'Relay Loss Std W={window_size}')
                ax4_twin.plot(steps, outage_stability, 'purple', linestyle='--', linewidth=1.5, label=f'Outage Std W={window_size}')
                ax4_twin.plot(steps, throughput_stability, 'orange', linestyle=':', linewidth=1.5, label=f'Throughput Std W={window_size}')
                ax4_twin.set_ylabel('Rolling Std', color='purple')
                ax4_twin.legend(loc='upper right', fontsize=8)

            ax4.set_ylabel('Guard Action Count', color='red')
            ax4.set_title('Backhaul Guard and Instability')
            ax4.grid(True, alpha=0.3)
            ax4.legend(loc='upper left', fontsize=8)

            for i in range(2):
                for j in range(2):
                    axes[i, j].set_xlabel('Time Step')

            plt.tight_layout()

            pid = os.getpid()
            if eval_step is not None:
                filename = f'relay_backhaul_analysis_eval_step_{eval_step}_episode_{self.episode_num}_pid_{pid}.png'
            else:
                filename = f'relay_backhaul_analysis_episode_{self.episode_num}_pid_{pid}.png'

            if prefix:
                filename = f'{prefix}_{filename}'
            save_path = os.path.join(self.log_dir, filename)
            fig.savefig(save_path, dpi=200, bbox_inches='tight')
            plt.close(fig)
            print(f"Relay backhaul analysis chart saved: {save_path}")

        except Exception as e:
            print(f"Error generating relay backhaul analysis chart: {e}")
            import traceback
            traceback.print_exc()
