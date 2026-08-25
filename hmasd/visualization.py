import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle

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

            # Energy-aware scenario metrics
            'battery_mean_ratio': [],
            'battery_min_ratio': [],
            'low_battery_uav_count': [],
            'depleted_uav_count': [],
            'charging_uav_count': [],
            'charging_queue_len': [],
            'uav_failed_count': [],
            'energy_penalty': [],
            'low_battery_distance_penalty': [],
            'depleted_battery_penalty': [],
            'charge_progress_reward': [],
            'charging_queue_penalty': [],
            'energy_reward_delta': [],
            'base_load_balance_reward': [],
            'energy_reward_delta_raw': [],
            'energy_reward_delta_clipped': [],
            'station_approach_reward': [],
            'charging_arrival_reward': [],
            'uav_battery_ratios': [],
            'uav_charging': [],
            'uav_failed': [],
            'charging_station_positions': [],
            'charging_station_capacity': [],
            'charging_station_occupancy': [],
            'charging_station_queue_lengths': [],
            'charging_radius_m': [],
            
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
        reward_info = reward_info or {}

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

        # === Record energy-aware metrics ===
        self.history['battery_mean_ratio'].append(reward_info.get('battery_mean_ratio', np.nan))
        self.history['battery_min_ratio'].append(reward_info.get('battery_min_ratio', np.nan))
        self.history['low_battery_uav_count'].append(reward_info.get('low_battery_uav_count', 0))
        self.history['depleted_uav_count'].append(reward_info.get('depleted_uav_count', 0))
        self.history['charging_uav_count'].append(reward_info.get('charging_uav_count', 0))
        self.history['charging_queue_len'].append(reward_info.get('charging_queue_len', 0))
        self.history['uav_failed_count'].append(reward_info.get('uav_failed_count', 0))
        self.history['energy_penalty'].append(reward_info.get('energy_penalty', 0))
        self.history['low_battery_distance_penalty'].append(reward_info.get('low_battery_distance_penalty', 0))
        self.history['depleted_battery_penalty'].append(reward_info.get('depleted_battery_penalty', 0))
        self.history['charge_progress_reward'].append(reward_info.get('charge_progress_reward', 0))
        self.history['charging_queue_penalty'].append(reward_info.get('charging_queue_penalty', 0))
        self.history['energy_reward_delta'].append(reward_info.get('energy_reward_delta', 0))
        self.history['base_load_balance_reward'].append(reward_info.get('base_load_balance_reward', 0))
        self.history['energy_reward_delta_raw'].append(reward_info.get('energy_reward_delta_raw', 0))
        self.history['energy_reward_delta_clipped'].append(reward_info.get('energy_reward_delta_clipped', reward_info.get('energy_reward_delta', 0)))
        self.history['station_approach_reward'].append(reward_info.get('station_approach_reward', 0))
        self.history['charging_arrival_reward'].append(reward_info.get('charging_arrival_reward', 0))
        self.history['uav_battery_ratios'].append(self._as_array(reward_info.get('uav_battery_ratios')))
        self.history['uav_charging'].append(self._as_array(reward_info.get('uav_charging')))
        self.history['uav_failed'].append(self._as_array(reward_info.get('uav_failed')))
        self.history['charging_station_positions'].append(self._as_array(reward_info.get('charging_station_positions')))
        self.history['charging_station_capacity'].append(self._as_array(reward_info.get('charging_station_capacity')))
        self.history['charging_station_occupancy'].append(self._as_array(reward_info.get('charging_station_occupancy')))
        self.history['charging_station_queue_lengths'].append(self._as_array(reward_info.get('charging_station_queue_lengths')))
        self.history['charging_radius_m'].append(reward_info.get('charging_radius_m', np.nan))

        # 仅记录一次静态信息
        if self.history['static_info'] is None and static_info:
            self.history['static_info'] = dict(static_info)
        elif self.history['static_info'] is not None and static_info:
            for key, value in static_info.items():
                if key not in self.history['static_info'] or self.history['static_info'][key] is None:
                    self.history['static_info'][key] = value

        if self.history['static_info'] is not None:
            station_positions = reward_info.get('charging_station_positions')
            if station_positions is not None:
                self.history['static_info']['charging_station_positions'] = np.array(station_positions).copy()
            station_capacity = reward_info.get('charging_station_capacity')
            if station_capacity is not None:
                self.history['static_info']['charging_station_capacity'] = np.array(station_capacity).copy()
            if 'charging_radius_m' in reward_info:
                self.history['static_info']['charging_radius_m'] = reward_info.get('charging_radius_m')
            if 'n_charging_stations' in reward_info:
                self.history['static_info']['n_charging_stations'] = reward_info.get('n_charging_stations')

    @staticmethod
    def _as_array(value):
        if value is None:
            return np.array([])
        return np.array(value).copy()

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
            if self._has_energy_data():
                self._create_energy_dashboard(prefix=prefix, eval_step=eval_step)
            self._create_skill_usage_dashboard(prefix=prefix, eval_step=eval_step)
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
            area_size = static_info.get('area_size', 1000) if static_info else 1000
            if static_info:
                if 'ground_bs_positions' in static_info and static_info.get('ground_bs_positions') is not None:
                    bs_pos = static_info['ground_bs_positions']
                    ax.scatter(bs_pos[:, 0], bs_pos[:, 1], c='black', marker='s', s=200, label='Ground Base Stations', zorder=5)

            station_positions, station_capacity, station_occupancy, station_queue, charging_radius = self._get_charging_station_plot_data(static_info)
            if station_positions.size > 0:
                active_station_count = self._get_active_station_count(static_info, station_positions)
                active_station_count = min(active_station_count, len(station_positions))
                for station_idx in range(active_station_count):
                    station_pos = station_positions[station_idx]
                    label = 'Charging Stations' if station_idx == 0 else None
                    ax.scatter(
                        station_pos[0],
                        station_pos[1],
                        c='orange',
                        marker='h',
                        s=190,
                        edgecolors='black',
                        linewidths=1.2,
                        zorder=6,
                        label=label,
                    )
                    if np.isfinite(charging_radius) and charging_radius > 0:
                        radius_patch = Circle(
                            (station_pos[0], station_pos[1]),
                            charging_radius,
                            fill=False,
                            linestyle='--',
                            linewidth=1.2,
                            edgecolor='orange',
                            alpha=0.45,
                            zorder=2,
                        )
                        ax.add_patch(radius_patch)
                    cap_text = self._format_station_capacity(station_capacity, station_idx)
                    occ_text = self._safe_index(station_occupancy, station_idx, default=0)
                    queue_text = self._safe_index(station_queue, station_idx, default=0)
                    ax.text(
                        station_pos[0] + 12,
                        station_pos[1] - 18,
                        f'CS{station_idx} cap={cap_text} occ={int(occ_text)} q={int(queue_text)}',
                        fontsize=8,
                        color='darkorange',
                        zorder=7,
                    )

            # Plot users at their final positions
            if user_positions is not None and user_positions.ndim == 2 and user_positions.shape[0] > 0:
                ax.scatter(user_positions[:, 0], user_positions[:, 1], c='blue', marker='.', s=50, label='Users', zorder=5)

            # Plot UAVs at their final positions. Energy scenarios color the final
            # marker by battery state and use overlays for charging/failure.
            final_batteries = self._last_array('uav_battery_ratios')
            final_charging = self._last_array('uav_charging')
            final_failed = self._last_array('uav_failed')
            use_energy_markers = final_batteries.size >= self.config.n_agents
            for i in range(self.config.n_agents):
                route_color = plt.cm.jet(i / self.config.n_agents)
                pos = uav_positions[i, :2]
                if use_energy_markers:
                    battery_ratio = float(final_batteries[i])
                    marker_color = self._battery_color(battery_ratio)
                    edge_color = 'dimgray' if bool(self._safe_index(final_failed, i, default=False)) else 'black'
                    ax.scatter(
                        pos[0],
                        pos[1],
                        marker='^',
                        color=marker_color,
                        s=135,
                        edgecolors=edge_color,
                        linewidths=1.4,
                        zorder=7,
                        label='UAV Final Position' if i == 0 else None,
                    )
                    if bool(self._safe_index(final_charging, i, default=False)):
                        ax.scatter(
                            pos[0],
                            pos[1],
                            marker='o',
                            facecolors='none',
                            edgecolors='deepskyblue',
                            s=260,
                            linewidths=2.0,
                            zorder=8,
                            label='Charging UAV' if i == 0 else None,
                        )
                    if bool(self._safe_index(final_failed, i, default=False)) or battery_ratio <= 0.02:
                        ax.scatter(
                            pos[0],
                            pos[1],
                            marker='x',
                            color='dimgray',
                            s=170,
                            linewidths=2.2,
                            zorder=9,
                            label='Failed/Depleted UAV' if i == 0 else None,
                        )
                    self._annotate_uav(ax, pos, f'UAV{i}', i, area_size)
                else:
                    ax.scatter(pos[0], pos[1], marker='^', color=route_color, s=120, edgecolors='black', zorder=6, label=f'UAV {i}')
                    self._annotate_uav(ax, pos, f'UAV{i}', i, area_size)

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

                self._plot_charging_event_points(ax)

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
            info_elements = [
                Line2D([0], [0], color='w', label=f'Final Coverage: {final_coverage:.2%}'),
            ]
            if use_energy_markers:
                battery_mean = self.history['battery_mean_ratio'][-1]
                battery_min = self.history['battery_min_ratio'][-1]
                info_elements.extend([
                    Line2D([0], [0], marker='^', color='w', markerfacecolor='#2ca02c', markeredgecolor='black', label='Battery High', markersize=9),
                    Line2D([0], [0], marker='^', color='w', markerfacecolor='#f2c94c', markeredgecolor='black', label='Battery Medium', markersize=9),
                    Line2D([0], [0], marker='^', color='w', markerfacecolor='#d62728', markeredgecolor='black', label='Battery Low', markersize=9),
                    Line2D([0], [0], marker='o', color='deepskyblue', markerfacecolor='none', linestyle='None', label='Charging Overlay', markersize=9),
                    Line2D([0], [0], marker='x', color='dimgray', linestyle='None', label='Failed/Depleted', markersize=9),
                    Line2D([0], [0], color='w', label=f'Battery Mean/Min: {battery_mean:.0%}/{battery_min:.0%}'),
                ])
            
            all_handles = list(by_label.values()) + info_elements
            
            current_step = self.history['steps'][-1]
            ax.set_title(f'Evaluation Episode {self.episode_num}: Network Topology Snapshot at Step {current_step}')
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            
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

    def _has_energy_data(self):
        if getattr(self.config, 'energy_stage', None):
            return True
        static_info = self.history.get('static_info') or {}
        if static_info.get('charging_station_positions') is not None:
            return True
        return any(np.asarray(v).size > 0 for v in self.history.get('uav_battery_ratios', []))

    def _history_series(self, key, default=0.0):
        values = []
        for value in self.history.get(key, []):
            try:
                scalar = float(value)
            except (TypeError, ValueError):
                scalar = default
            if np.isnan(scalar):
                scalar = default
            values.append(scalar)
        return np.asarray(values, dtype=float)

    def _last_array(self, key):
        for value in reversed(self.history.get(key, [])):
            array = np.asarray(value)
            if array.size > 0:
                return array
        return np.array([])

    @staticmethod
    def _safe_index(values, index, default=0):
        array = np.asarray(values).flatten()
        if 0 <= index < array.size:
            return array[index]
        return default

    @staticmethod
    def _battery_color(ratio):
        if not np.isfinite(ratio):
            return '#bdbdbd'
        if ratio > 0.50:
            return '#2ca02c'
        if ratio > 0.25:
            return '#f2c94c'
        return '#d62728'

    @staticmethod
    def _annotate_uav(ax, position, text, index, area_size):
        y_sign = -1 if position[1] > area_size * 0.85 else 1
        x_offset = 7 + (index % 2) * 22
        y_offset = y_sign * (8 + (index % 6) * 9)
        ax.annotate(
            text,
            xy=(position[0], position[1]),
            xytext=(x_offset, y_offset),
            textcoords='offset points',
            fontsize=8,
            zorder=10,
            bbox=dict(boxstyle='round,pad=0.18', facecolor='white', edgecolor='none', alpha=0.65),
        )

    def _get_active_station_count(self, static_info, station_positions):
        if static_info and static_info.get('n_charging_stations') is not None:
            try:
                return int(static_info.get('n_charging_stations'))
            except (TypeError, ValueError):
                pass
        if getattr(self.config, 'n_charging_stations', None) is not None:
            try:
                return int(getattr(self.config, 'n_charging_stations'))
            except (TypeError, ValueError):
                pass
        return len(station_positions)

    def _get_charging_station_plot_data(self, static_info):
        static_info = static_info or {}
        positions = static_info.get('charging_station_positions')
        if positions is None:
            positions = self._last_array('charging_station_positions')
        positions = np.asarray(positions)
        if positions.size == 0:
            return np.array([]), np.array([]), np.array([]), np.array([]), np.nan
        if positions.ndim == 1:
            positions = positions.reshape(1, -1)

        capacity = static_info.get('charging_station_capacity')
        if capacity is None:
            capacity = self._last_array('charging_station_capacity')
        capacity = np.asarray(capacity, dtype=float) if np.asarray(capacity).size > 0 else np.array([])

        occupancy = self._last_array('charging_station_occupancy')
        queue = self._last_array('charging_station_queue_lengths')

        radius = static_info.get('charging_radius_m')
        if radius is None:
            for value in reversed(self.history.get('charging_radius_m', [])):
                try:
                    radius = float(value)
                except (TypeError, ValueError):
                    radius = np.nan
                if np.isfinite(radius):
                    break
        try:
            radius = float(radius)
        except (TypeError, ValueError):
            radius = np.nan

        return positions, capacity, np.asarray(occupancy), np.asarray(queue), radius

    @staticmethod
    def _format_station_capacity(capacity_values, station_idx):
        capacity = VisualizationManager._safe_index(capacity_values, station_idx, default=np.nan)
        if np.isinf(capacity):
            return 'inf'
        if not np.isfinite(capacity):
            return 'N/A'
        return str(int(capacity))

    def _plot_charging_event_points(self, ax):
        label_added = False
        for step_idx, charging_flags in enumerate(self.history.get('uav_charging', [])):
            charging = np.asarray(charging_flags).astype(bool).flatten()
            if charging.size == 0 or step_idx >= len(self.history['uav_positions']):
                continue
            positions = self.history['uav_positions'][step_idx]
            for uav_idx in np.where(charging)[0]:
                if uav_idx >= len(positions):
                    continue
                ax.scatter(
                    positions[uav_idx, 0],
                    positions[uav_idx, 1],
                    marker='o',
                    s=32,
                    facecolors='deepskyblue',
                    edgecolors='white',
                    linewidths=0.4,
                    alpha=0.65,
                    zorder=4,
                    label='Charging Events' if not label_added else None,
                )
                label_added = True

    def _create_energy_dashboard(self, prefix='', eval_step=None):
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial', 'Liberation Sans']
            plt.rcParams['axes.unicode_minus'] = False

            steps = self.history['steps']
            fig, axes = plt.subplots(3, 3, figsize=(20, 15))
            fig.suptitle(f'Evaluation Episode {self.episode_num}: Energy Scheduling Dashboard', fontsize=16, fontweight='bold')

            battery_mean = self._history_series('battery_mean_ratio', default=1.0)
            battery_min = self._history_series('battery_min_ratio', default=1.0)
            low_count = self._history_series('low_battery_uav_count')
            depleted_count = self._history_series('depleted_uav_count')
            charging_count = self._history_series('charging_uav_count')
            queue_len = self._history_series('charging_queue_len')
            failed_count = self._history_series('uav_failed_count')

            ax1 = axes[0, 0]
            ax1.plot(steps, battery_mean, color='#2ca02c', linewidth=2, label='Mean Battery')
            ax1.plot(steps, battery_min, color='#d62728', linewidth=2, label='Min Battery')
            ax1.set_ylim(-0.02, 1.02)
            ax1.set_ylabel('Battery Ratio')
            ax1.set_title('Battery Level')
            ax1.grid(True, alpha=0.3)
            ax1.legend()

            ax2 = axes[0, 1]
            ax2.plot(steps, low_count, color='#f2c94c', linewidth=2, label='Low Battery UAVs')
            ax2.plot(steps, depleted_count, color='#d62728', linewidth=2, label='Depleted UAVs')
            ax2.set_ylabel('UAV Count')
            ax2.set_title('Low and Depleted Battery Count')
            ax2.grid(True, alpha=0.3)
            ax2.legend()

            ax3 = axes[0, 2]
            ax3.plot(steps, charging_count, color='deepskyblue', linewidth=2, label='Charging UAVs')
            ax3.plot(steps, queue_len, color='darkorange', linewidth=2, label='Total Queue Length')
            ax3.set_ylabel('Count')
            ax3.set_title('Charging and Queue')
            ax3.grid(True, alpha=0.3)
            ax3.legend()

            ax4 = axes[1, 0]
            occupancy_history = self.history.get('charging_station_occupancy', [])
            max_stations = max((np.asarray(v).size for v in occupancy_history), default=0)
            for station_idx in range(max_stations):
                station_occ = [self._safe_index(v, station_idx, default=0) for v in occupancy_history]
                ax4.plot(steps, station_occ, linewidth=2, label=f'CS{station_idx} Occupancy')
            ax4.set_ylabel('Occupied Slots')
            ax4.set_title('Station Occupancy')
            ax4.grid(True, alpha=0.3)
            if max_stations > 0:
                ax4.legend()

            ax5 = axes[1, 1]
            ax5.plot(steps, self._history_series('energy_penalty'), color='red', linewidth=2, label='Motion Energy Penalty')
            ax5.plot(steps, self._history_series('low_battery_distance_penalty'), color='darkorange', linewidth=2, label='Low Battery Distance')
            ax5.plot(steps, self._history_series('depleted_battery_penalty'), color='black', linewidth=2, label='Depleted Penalty')
            ax5.plot(steps, self._history_series('charging_queue_penalty'), color='purple', linewidth=2, label='Queue Penalty')
            ax5.plot(steps, self._history_series('station_approach_reward'), color='seagreen', linewidth=2, label='Station Approach')
            ax5.plot(steps, self._history_series('charging_arrival_reward'), color='royalblue', linewidth=2, label='Arrival Slowdown')
            ax5.set_ylabel('Normalized Value')
            ax5.set_title('Energy Reward Components')
            ax5.grid(True, alpha=0.3)
            ax5.legend(fontsize=8)

            ax6 = axes[1, 2]
            ax6.plot(steps, self._history_series('charge_progress_reward'), color='deepskyblue', linewidth=2, label='Charge Progress')
            ax6.plot(steps, self._history_series('base_load_balance_reward'), color='seagreen', linewidth=2, label='Base Load Balance')
            ax6_twin = ax6.twinx()
            ax6_twin.plot(steps, self._history_series('energy_reward_delta_raw'), color='mediumpurple', linewidth=1.5, linestyle='--', label='Energy Delta Raw')
            ax6_twin.plot(steps, self._history_series('energy_reward_delta_clipped'), color='purple', linewidth=2, label='Energy Delta Clipped')
            ax6.set_ylabel('Base / Charging', color='seagreen')
            ax6_twin.set_ylabel('Reward Delta', color='purple')
            ax6.set_title('Base Reward and Energy Shaping')
            ax6.grid(True, alpha=0.3)
            ax6.legend(loc='upper left', fontsize=8)
            ax6_twin.legend(loc='upper right', fontsize=8)

            ax7 = axes[2, 0]
            ax7.plot(steps, failed_count, color='dimgray', linewidth=2, label='Failed UAVs')
            ax7_twin = ax7.twinx()
            ax7_twin.plot(steps, self.history['service_drop_ratio'], color='red', linewidth=2, label='Service Drop Ratio')
            ax7.set_ylabel('Failed UAV Count', color='dimgray')
            ax7_twin.set_ylabel('Service Drop Ratio', color='red')
            ax7.set_title('Failure and Service Drop')
            ax7.grid(True, alpha=0.3)
            ax7.legend(loc='upper left')
            ax7_twin.legend(loc='upper right')

            ax8 = axes[2, 1]
            ax8.plot(steps, self.history['coverage_ratios'], color='blue', linewidth=2, label='Coverage')
            ax8.plot(steps, self.history['backhaul_outage_ratio'], color='red', linewidth=2, label='Backhaul Outage')
            ax8_twin = ax8.twinx()
            ax8_twin.plot(steps, self.history['throughput'], color='green', linewidth=2, label='Throughput')
            ax8.set_ylabel('Ratio', color='blue')
            ax8_twin.set_ylabel('Throughput (Mbps)', color='green')
            ax8.set_title('Coverage, Backhaul, Throughput')
            ax8.grid(True, alpha=0.3)
            ax8.legend(loc='upper left')
            ax8_twin.legend(loc='upper right')

            ax9 = axes[2, 2]
            ax9.axis('off')
            final_mean = battery_mean[-1] if len(battery_mean) else 1.0
            final_min = battery_min[-1] if len(battery_min) else 1.0
            final_low = int(low_count[-1]) if len(low_count) else 0
            final_depleted = int(depleted_count[-1]) if len(depleted_count) else 0
            final_charging = int(charging_count[-1]) if len(charging_count) else 0
            final_queue = int(queue_len[-1]) if len(queue_len) else 0
            final_failed = int(failed_count[-1]) if len(failed_count) else 0
            summary_text = f"""
Energy Summary

Stage: {getattr(self.config, 'energy_stage', 'N/A')}
Battery mean/min: {final_mean:.1%} / {final_min:.1%}
Low/depleted UAVs: {final_low} / {final_depleted}
Charging UAVs: {final_charging}
Queue length: {final_queue}
Failed UAVs: {final_failed}
Final coverage: {self.history['coverage_ratios'][-1]:.1%}
Final throughput: {self.history['throughput'][-1]:.1f} Mbps
            """
            ax9.text(0.05, 0.95, summary_text, transform=ax9.transAxes, fontsize=11,
                     verticalalignment='top', fontfamily='monospace',
                     bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.8))
            ax9.set_title('Energy Summary', fontweight='bold')

            for row in range(3):
                for col in range(3):
                    if not (row == 2 and col == 2):
                        axes[row, col].set_xlabel('Time Step')

            plt.tight_layout()

            pid = os.getpid()
            if eval_step is not None:
                filename = f'energy_dashboard_eval_step_{eval_step}_episode_{self.episode_num}_pid_{pid}.png'
            else:
                filename = f'energy_dashboard_episode_{self.episode_num}_pid_{pid}.png'
            if prefix:
                filename = f'{prefix}_{filename}'
            save_path = os.path.join(self.log_dir, filename)
            fig.savefig(save_path, dpi=200, bbox_inches='tight')
            plt.close(fig)
            print(f"Energy dashboard saved: {save_path}")

        except Exception as e:
            print(f"Error generating energy dashboard: {e}")
            import traceback
            traceback.print_exc()

    def _compute_skill_stats(self):
        team_skills = np.asarray(self.history.get('team_skills', []), dtype=float)
        valid = team_skills[team_skills >= 0].astype(int)
        n_z = int(max(getattr(self.config, 'n_Z', 1), (int(valid.max()) + 1) if valid.size else 1))

        counts = np.zeros(n_z, dtype=float)
        for skill in valid:
            if 0 <= skill < n_z:
                counts[skill] += 1
        ratios = counts / max(float(valid.size), 1.0)
        dominant_skill = int(np.argmax(counts)) if valid.size else -1
        dominant_ratio = float(ratios[dominant_skill]) if dominant_skill >= 0 else 0.0

        switch_count = 0
        dwell_lengths = []
        transitions = np.zeros((n_z, n_z), dtype=float)
        if valid.size:
            current_skill = valid[0]
            current_len = 1
            for prev, cur in zip(valid[:-1], valid[1:]):
                if 0 <= prev < n_z and 0 <= cur < n_z:
                    transitions[prev, cur] += 1
                if cur == prev:
                    current_len += 1
                else:
                    switch_count += 1
                    dwell_lengths.append(current_len)
                    current_skill = cur
                    current_len = 1
            dwell_lengths.append(current_len)

        switches_per_100 = switch_count / max(valid.size - 1, 1) * 100.0 if valid.size > 1 else 0.0
        avg_dwell = float(np.mean(dwell_lengths)) if dwell_lengths else 0.0

        agent_matrix = np.full((getattr(self.config, 'n_agents', 0), len(self.history.get('agent_skills', []))), np.nan)
        for time_idx, skills in enumerate(self.history.get('agent_skills', [])):
            try:
                skill_array = np.asarray(skills, dtype=float).flatten()
            except (TypeError, ValueError):
                continue
            count = min(agent_matrix.shape[0], skill_array.size)
            if count > 0:
                agent_matrix[:count, time_idx] = skill_array[:count]

        return {
            'team_skills': team_skills,
            'valid': valid,
            'n_z': n_z,
            'counts': counts,
            'ratios': ratios,
            'dominant_skill': dominant_skill,
            'dominant_ratio': dominant_ratio,
            'switch_count': switch_count,
            'switches_per_100': switches_per_100,
            'dwell_lengths': dwell_lengths,
            'avg_dwell': avg_dwell,
            'transitions': transitions,
            'agent_matrix': agent_matrix,
        }

    def _create_skill_usage_dashboard(self, prefix='', eval_step=None):
        if not self.history.get('team_skills'):
            return

        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial', 'Liberation Sans']
            plt.rcParams['axes.unicode_minus'] = False

            steps = self.history['steps']
            stats = self._compute_skill_stats()
            fig, axes = plt.subplots(2, 3, figsize=(20, 11))
            fig.suptitle(f'Evaluation Episode {self.episode_num}: Skill Usage Dashboard', fontsize=16, fontweight='bold')

            ax1 = axes[0, 0]
            ax1.step(steps, stats['team_skills'], where='post', color='navy', linewidth=1.8)
            ax1.set_title('Team Skill Timeline')
            ax1.set_xlabel('Time Step')
            ax1.set_ylabel('Team Skill')
            ax1.set_yticks(range(stats['n_z']))
            ax1.grid(True, alpha=0.3)

            ax2 = axes[0, 1]
            x = np.arange(stats['n_z'])
            ax2.bar(x, stats['ratios'], color='steelblue')
            ax2.set_title('Team Skill Usage Ratio')
            ax2.set_xlabel('Skill')
            ax2.set_ylabel('Episode Ratio')
            ax2.set_xticks(x)
            ax2.set_ylim(0, max(1.0, np.max(stats['ratios']) * 1.15 if stats['ratios'].size else 1.0))
            ax2.grid(True, axis='y', alpha=0.3)

            ax3 = axes[0, 2]
            transition_sum = np.sum(stats['transitions'], axis=1, keepdims=True)
            transition_rates = np.divide(
                stats['transitions'],
                np.maximum(transition_sum, 1.0),
                out=np.zeros_like(stats['transitions']),
                where=transition_sum > 0,
            )
            im3 = ax3.imshow(transition_rates, cmap='Blues', vmin=0, vmax=1)
            ax3.set_title('Team Skill Transition Matrix')
            ax3.set_xlabel('Next Skill')
            ax3.set_ylabel('Current Skill')
            ax3.set_xticks(x)
            ax3.set_yticks(x)
            fig.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)
            if stats['n_z'] <= 10:
                for row in range(stats['n_z']):
                    for col in range(stats['n_z']):
                        value = transition_rates[row, col]
                        if value > 0:
                            ax3.text(col, row, f'{value:.2f}', ha='center', va='center', fontsize=8)

            ax4 = axes[1, 0]
            agent_matrix = stats['agent_matrix']
            if agent_matrix.size > 0:
                im4 = ax4.imshow(agent_matrix, aspect='auto', interpolation='nearest', cmap='viridis', vmin=0, vmax=max(stats['n_z'] - 1, 1))
                ax4.set_title('Agent Skill Heatmap')
                ax4.set_xlabel('Recorded Step Index')
                ax4.set_ylabel('Agent')
                ax4.set_yticks(range(agent_matrix.shape[0]))
                fig.colorbar(im4, ax=ax4, fraction=0.046, pad=0.04)
            else:
                ax4.axis('off')
                ax4.text(0.5, 0.5, 'No agent skill data', ha='center', va='center')

            ax5 = axes[1, 1]
            if stats['dwell_lengths']:
                bins = range(1, max(stats['dwell_lengths']) + 2)
                ax5.hist(stats['dwell_lengths'], bins=bins, color='darkorange', edgecolor='black', alpha=0.8)
            ax5.set_title('Team Skill Dwell Lengths')
            ax5.set_xlabel('Consecutive Steps')
            ax5.set_ylabel('Segment Count')
            ax5.grid(True, axis='y', alpha=0.3)

            ax6 = axes[1, 2]
            ax6.axis('off')
            summary_text = f"""
Skill Usage Summary

Dominant skill: {stats['dominant_skill']}
Dominant ratio: {stats['dominant_ratio']:.1%}
Switch count: {stats['switch_count']}
Switches per 100 steps: {stats['switches_per_100']:.1f}
Average dwell length: {stats['avg_dwell']:.1f} steps
Recorded steps: {len(steps)}
            """
            ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes, fontsize=11,
                     verticalalignment='top', fontfamily='monospace',
                     bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.8))
            ax6.set_title('Skill Summary', fontweight='bold')

            plt.tight_layout()

            pid = os.getpid()
            if eval_step is not None:
                filename = f'skill_usage_dashboard_eval_step_{eval_step}_episode_{self.episode_num}_pid_{pid}.png'
            else:
                filename = f'skill_usage_dashboard_episode_{self.episode_num}_pid_{pid}.png'
            if prefix:
                filename = f'{prefix}_{filename}'
            save_path = os.path.join(self.log_dir, filename)
            fig.savefig(save_path, dpi=200, bbox_inches='tight')
            plt.close(fig)
            print(f"Skill usage dashboard saved: {save_path}")

        except Exception as e:
            print(f"Error generating skill usage dashboard: {e}")
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
