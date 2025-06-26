#!/usr/bin/env python3
"""
Test script for debugging user connection issues in Scenario 3.

This script is used to analyze why some UAVs (e.g., UAV3) do not connect to
nearby users, by inspecting SINR and interference calculations.
"""

import numpy as np
import matplotlib.pyplot as plt
from envs.pettingzoo.scenario3 import UAVMultiHopEnv

def debug_sinr_calculation():
    """
    Debug SINR calculation process.
    """
    print("=" * 60)
    print("Scenario 3 SINR Calculation Debug")
    print("=" * 60)
    
    # Create environment instance
    env = UAVMultiHopEnv(
        n_uavs=5,
        n_users=30,
        area_size=1000,
        height_range=(50, 200),
        max_speed=30,
        time_step=1.0,
        max_steps=5000,
        user_distribution="multi_cluster",
        channel_model="probabilistic",
        render_mode=None,
        seed=42,  # Fixed seed for reproducibility
        min_sinr=0,  # Minimum SINR threshold (dB)
        max_connections=15,
        max_hops=5,
        n_ground_bs=4,
        n_clusters=7,
        cluster_std=150,
        central_area_ratio=0.5,
        num_channels=5,
    )
    
    # Reset environment
    observations, infos = env.reset(seed=42)
    
    print(f"Environment Parameters:")
    print(f"  - UAVs: {env.n_uavs}")
    print(f"  - Users: {env.n_users}")
    print(f"  - Min SINR Threshold: {env.min_sinr} dB")
    print(f"  - Tx Power: {env.tx_power} dBm")
    print(f"  - Noise Power: {env.noise_power} dBm")
    print(f"  - Carrier Frequency: {env.carrier_frequency / 1e9:.1f} GHz")
    print(f"  - Bandwidth: {env.bandwidth / 1e6:.1f} MHz")
    print()
    
    # Print UAV positions
    print("UAV Positions:")
    for i in range(env.n_uavs):
        pos = env.uav_positions[i]
        print(f"  UAV{i}: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})")
    print()
    
    # Print Ground BS positions
    print("Ground BS Positions:")
    for i in range(env.n_ground_bs):
        pos = env.ground_bs_positions[i]
        print(f"  BS{i}: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})")
    print()
    
    # Calculate and display connection matrix
    print("User Connections:")
    total_connected = 0
    for i in range(env.n_uavs):
        connected_users = np.where(env.connections[i])[0]
        total_connected += len(connected_users)
        print(f"  UAV{i}: connected to {len(connected_users)} users {list(connected_users)}")
    
    unconnected_users = []
    for j in range(env.n_users):
        if not np.any(env.connections[:, j]):
            unconnected_users.append(j)
    
    print(f"  Total connected users: {total_connected}/{env.n_users}")
    print(f"  Unconnected users: {len(unconnected_users)} {unconnected_users}")
    print()
    
    # Find and report idle UAVs
    idle_uavs = []
    for i in range(env.n_uavs):
        if np.sum(env.connections[i]) == 0:
            idle_uavs.append(i)
    
    if idle_uavs:
        print(f"Found {len(idle_uavs)} idle UAVs: {idle_uavs}")
        for uav_idx in idle_uavs:
            print(f"\nAnalyzing idle UAV{uav_idx}:")
            uav_pos = env.uav_positions[uav_idx]
            print(f"    Position: ({uav_pos[0]:.1f}, {uav_pos[1]:.1f}, {uav_pos[2]:.1f})")
            has_backhaul = uav_idx in env.routing_paths
            print(f"    Has backhaul path: {has_backhaul}")
            if has_backhaul:
                path = env.routing_paths[uav_idx]
                path_str = " -> ".join([f"{node_type}_{node_idx}" for node_type, node_idx in path])
                print(f"    Backhaul Path: {path_str}")
    else:
        print("No idle UAVs found.")
    
    # Analyze unconnected users regardless of idle UAVs
    if unconnected_users:
        print(f"\n--- Analyzing Unconnected Users ---")
        # Limit analysis to a few users to avoid excessive output
        users_to_analyze = unconnected_users[:min(3, len(unconnected_users))]
        print(f"Analyzing first {len(users_to_analyze)} unconnected users: {users_to_analyze}")
        
        for user_idx in users_to_analyze:
            print(f"\n[Analysis for Unconnected User {user_idx}]")
            user_pos = env.user_positions[user_idx]
            print(f"  Position: ({user_pos[0]:.1f}, {user_pos[1]:.1f})")
            
            # Analyze SINR from all UAVs to this user
            for uav_idx in range(env.n_uavs):
                analyze_sinr_detailed(env, uav_idx, user_idx)
    else:
        print("\nAll users are connected.")

    # Analyze routing paths
    print(f"\n--- Routing Path Analysis ---")
    print(f"  UAVs with paths: {len(env.routing_paths)}/{env.n_uavs}")
    for uav_idx, path in env.routing_paths.items():
        path_str = " -> ".join([f"{node_type}_{node_idx}" for node_type, node_idx in path])
        print(f"  UAV{uav_idx}: {path_str} (Hops: {len(path)-1})")
    
    # Calculate average hops
    if env.routing_paths:
        total_hops = sum(len(path) - 1 for path in env.routing_paths.values())
        avg_hops = total_hops / len(env.routing_paths)
        print(f"  Average Hops: {avg_hops:.1f}")
    else:
        print("  Average Hops: No paths")

def analyze_sinr_detailed(env, uav_idx, user_idx):
    """
    Perform a detailed analysis of the SINR calculation.
    
    Args:
        env: The environment instance.
        uav_idx: The index of the UAV.
        user_idx: The index of the user.
    """
    print(f"    Analysis for link UAV{uav_idx} -> User{user_idx}:")
    
    uav_pos = env.uav_positions[uav_idx]
    user_pos = env.user_positions[user_idx]
    user_pos_3d = np.append(user_pos, 0)
    
    # 1. Calculate Path Loss
    path_loss = env._compute_path_loss(uav_pos, user_pos)
    distance = np.linalg.norm(uav_pos - user_pos_3d)
    print(f"      - Distance: {distance:.1f}m")
    print(f"      - Path Loss: {path_loss:.2f} dB")
    
    # 2. Calculate Received Power
    rx_power = env.tx_power - path_loss
    print(f"      - Received Power: {env.tx_power} - {path_loss:.2f} = {rx_power:.2f} dBm")
    
    # 3. Calculate Interference Power
    print(f"      - Interference Analysis:")
    total_interference_linear = 0
    
    for i in range(env.n_uavs):
        if i != uav_idx:
            interferer_pos = env.uav_positions[i]
            interferer_path_loss = env._compute_path_loss(interferer_pos, user_pos)
            interferer_power_dbm = env.tx_power - interferer_path_loss
            interferer_power_linear = 10 ** (interferer_power_dbm / 10)
            
            total_interference_linear += interferer_power_linear
            
            interferer_distance = np.linalg.norm(interferer_pos - user_pos_3d)
            
            print(f"        - From UAV{i}: dist {interferer_distance:.1f}m, "
                  f"path loss {interferer_path_loss:.2f}dB, "
                  f"pwr {interferer_power_dbm:.2f}dBm")
    
    # 4. Calculate Total Interference Power
    total_interference_dbm = 10 * np.log10(total_interference_linear) if total_interference_linear > 0 else -float('inf')
    print(f"      - Total Interference: {total_interference_dbm:.2f} dBm")
    
    # 5. Calculate Interference + Noise Power
    noise_power_linear = 10 ** (env.noise_power / 10)
    interference_plus_noise_linear = noise_power_linear + total_interference_linear
    interference_plus_noise_dbm = 10 * np.log10(interference_plus_noise_linear)
    print(f"      - Noise Power: {env.noise_power:.2f} dBm")
    print(f"      - Interference + Noise: {interference_plus_noise_dbm:.2f} dBm")
    
    # 6. Calculate Final SINR
    sinr = rx_power - interference_plus_noise_dbm
    print(f"      - Final SINR: {rx_power:.2f} - {interference_plus_noise_dbm:.2f} = {sinr:.2f} dB")
    print(f"      - SINR Threshold: {env.min_sinr} dB")
    print(f"      - Connection Met: {sinr >= env.min_sinr}")
    
    # 7. Verify with internal environment calculation
    env_sinr = env._compute_sinr(uav_idx, user_idx)
    print(f"      - Env-calculated SINR: {env_sinr:.2f} dB")
    if abs(sinr - env_sinr) > 1e-5:
        print(f"      - WARNING: Calculation Difference: {abs(sinr - env_sinr):.6f} dB")


def visualize_scenario(env):
    """
    Visualize the current scenario.
    """
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111)
    
    # Plot users
    connected_users = []
    unconnected_users = []
    
    for j in range(env.n_users):
        if np.any(env.connections[:, j]):
            connected_users.append(j)
        else:
            unconnected_users.append(j)
    
    # Plot connected users (blue)
    if connected_users:
        connected_pos = env.user_positions[connected_users]
        ax.scatter(connected_pos[:, 0], connected_pos[:, 1], 
                   c='blue', marker='o', s=30, alpha=0.7, label=f'Connected Users ({len(connected_users)})')
    
    # Plot unconnected users (red)
    if unconnected_users:
        unconnected_pos = env.user_positions[unconnected_users]
        ax.scatter(unconnected_pos[:, 0], unconnected_pos[:, 1], 
                   c='red', marker='x', s=50, alpha=0.8, label=f'Unconnected Users ({len(unconnected_users)})')
    
    # Separate UAVs for cleaner plotting and labeling
    serving_uav_indices = [i for i in range(env.n_uavs) if np.sum(env.connections[i]) > 0]
    idle_uav_indices = [i for i in range(env.n_uavs) if np.sum(env.connections[i]) == 0]

    # Plot serving UAVs (green triangles)
    if serving_uav_indices:
        pos = env.uav_positions[serving_uav_indices]
        ax.scatter(pos[:, 0], pos[:, 1], c='green', marker='^', s=200, 
                   edgecolors='black', linewidth=1.5, label='Serving UAV')

    # Plot idle UAVs (orange triangles)
    if idle_uav_indices:
        pos = env.uav_positions[idle_uav_indices]
        ax.scatter(pos[:, 0], pos[:, 1], c='orange', marker='^', s=200, 
                   edgecolors='black', linewidth=1.5, label='Idle UAV')

    # Annotate all UAVs
    for i in range(env.n_uavs):
        uav_pos = env.uav_positions[i]
        ax.annotate(f'UAV{i}', (uav_pos[0], uav_pos[1]), 
                    xytext=(8, 8), textcoords='offset points', fontsize=10, fontweight='bold')

    # Plot Ground BS
    if env.n_ground_bs > 0:
        bs_pos = env.ground_bs_positions
        ax.scatter(bs_pos[:, 0], bs_pos[:, 1], c='black', marker='s', s=150, 
                   label='Ground BS')
    
    # Plot connection lines
    for i in range(env.n_uavs):
        uav_pos = env.uav_positions[i]
        for j in range(env.n_users):
            if env.connections[i, j]:
                user_pos = env.user_positions[j]
                ax.plot([uav_pos[0], user_pos[0]], [uav_pos[1], user_pos[1]], 
                        'g-', alpha=0.3, linewidth=1)
    
    ax.set_xlim(0, env.area_size)
    ax.set_ylim(0, env.area_size)
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_title('Scenario 3 User Connectivity')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig('debug_scenario3_visualization.png', dpi=150, bbox_inches='tight')
    print(f"\nVisualization saved to: debug_scenario3_visualization.png")
    plt.show()

if __name__ == "__main__":
    # Run the debugging process
    debug_sinr_calculation()
    
    # Create a new environment instance for visualization
    # This ensures the visualization reflects the initial state defined in the debug function
    env_vis = UAVMultiHopEnv(
        n_uavs=5,
        n_users=30,
        area_size=1000,
        seed=42,
        min_sinr=0,
    )
    env_vis.reset(seed=42)
    
    # Visualize the scenario
    try:
        visualize_scenario(env_vis)
    except ImportError:
        print("\nNote: matplotlib is not installed, skipping visualization.")
    except Exception as e:
        print(f"\nAn error occurred during visualization: {e}")
    
    print("\nDebug script finished!")
