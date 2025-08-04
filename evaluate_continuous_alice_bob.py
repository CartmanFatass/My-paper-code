import torch
import numpy as np
import time
import os
import json
from collections import defaultdict
import matplotlib.pyplot as plt
from envs.pettingzoo.continuous_alice_bob import ContinuousAliceBobEnv
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from hmasd.agent import HMASDAgent
from config_continuous_alice_bob import Config
from logger import init_multiproc_logging, main_logger

def save_trajectory_data(log_dir, episode, trajectories, team_skills, agent_skills_history, 
                        button_pos, diamond_pos, button_colors, diamond_colors, 
                        rewards_history, episode_reward, k):
    """Save detailed trajectory data with skill annotations to JSON file."""
    
    # Prepare data for JSON serialization
    trajectory_data = {
        'episode': episode,
        'total_reward': float(episode_reward),
        'episode_length': len(trajectories[0]) if trajectories[0] else 0,
        'skill_duration': k,
        'environment_setup': {
            'button_positions': button_pos.tolist(),
            'diamond_positions': diamond_pos.tolist(),
            'button_colors': button_colors.tolist(),  # 0=blue, 1=red
            'diamond_colors': diamond_colors.tolist(),  # 0=blue, 1=red
            'color_mapping': {0: 'blue', 1: 'red'}
        },
        'team_skills': [int(skill) for skill in team_skills],
        'agent_skills_by_segment': [
            {
                'segment': i,
                'team_skill': int(team_skills[i]) if i < len(team_skills) else None,
                'alice_skill': int(agent_skills_history[i][0]) if i < len(agent_skills_history) else None,
                'bob_skill': int(agent_skills_history[i][1]) if i < len(agent_skills_history) else None,
                'start_step': i * k,
                'end_step': min((i + 1) * k, len(trajectories[0]))
            }
            for i in range(max(len(team_skills), len(agent_skills_history)))
        ],
        'trajectories': {
            'alice': [pos.tolist() for pos in trajectories[0]],
            'bob': [pos.tolist() for pos in trajectories[1]]
        },
        'rewards_history': [float(r) for r in rewards_history]
    }
    
    # Save to JSON file
    json_path = os.path.join(log_dir, f"trajectory_data_episode_{episode}.json")
    with open(json_path, 'w') as f:
        json.dump(trajectory_data, f, indent=2)
    
    return json_path

def plot_detailed_trajectory_analysis(log_dir, episode, trajectories, team_skills, agent_skills_history,
                                    button_pos, diamond_pos, button_colors, diamond_colors, k):
    """Create detailed trajectory analysis plots."""
    
    # Create a figure with multiple subplots
    fig = plt.figure(figsize=(16, 12))
    
    # Main trajectory plot
    ax1 = plt.subplot(2, 2, 1)
    ax1.set_xlim(0, 8)
    ax1.set_ylim(0, 8)
    ax1.set_title(f"Episode {episode}: Agent Trajectories with Skills")
    ax1.set_aspect('equal')
    
    # Color mapping for items: 0=blue, 1=red
    color_map = {0: 'blue', 1: 'red'}
    
    # Plot environment items
    for i, pos in enumerate(button_pos):
        color = color_map[button_colors[i]]
        ax1.scatter(pos[0], pos[1], c=color, marker='s', s=200, 
                   label=f'{"Blue" if button_colors[i]==0 else "Red"} Button' if i == button_colors[i] else "",
                   edgecolor='black', linewidth=2)
    
    for i, pos in enumerate(diamond_pos):
        color = color_map[diamond_colors[i]]
        ax1.scatter(pos[0], pos[1], c=color, marker='D', s=200,
                   label=f'{"Blue" if diamond_colors[i]==0 else "Red"} Diamond' if i == diamond_colors[i] else "",
                   edgecolor='black', linewidth=2)
    
    # Plot agent trajectories with skill segments
    agent_colors = ['darkred', 'darkorange']
    agent_labels = ['Alice', 'Bob']
    skill_styles = ['-', '--', '-.', ':']
    
    for agent_idx, traj in enumerate(trajectories):
        if len(traj) == 0:
            continue
            
        traj_np = np.array(traj)
        
        # Plot skill segments
        for skill_idx in range(len(agent_skills_history)):
            start_step = skill_idx * k
            end_step = min((skill_idx + 1) * k, len(traj))
            
            if start_step >= len(traj):
                break
                
            segment = traj_np[start_step:end_step]
            if len(segment) > 1:
                agent_skill = agent_skills_history[skill_idx][agent_idx]
                style = skill_styles[agent_skill % len(skill_styles)]
                ax1.plot(segment[:, 0], segment[:, 1], 
                        color=agent_colors[agent_idx], linestyle=style, linewidth=3,
                        alpha=0.8)
        
        # Mark start and end points
        ax1.scatter(traj_np[0, 0], traj_np[0, 1], color=agent_colors[agent_idx], 
                   marker='o', s=150, edgecolor='white', linewidth=3, label=f'{agent_labels[agent_idx]} Start')
        ax1.scatter(traj_np[-1, 0], traj_np[-1, 1], color=agent_colors[agent_idx], 
                   marker='X', s=150, edgecolor='white', linewidth=3, label=f'{agent_labels[agent_idx]} End')
    
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Skill timeline plot
    ax2 = plt.subplot(2, 2, 2)
    segments = list(range(len(team_skills)))
    ax2.bar(segments, team_skills, alpha=0.7, color='lightblue', edgecolor='black')
    ax2.set_xlabel('Skill Segment')
    ax2.set_ylabel('Team Skill ID')
    ax2.set_title('Team Skills Over Time')
    ax2.set_xticks(segments)
    
    # Individual agent skills plot
    ax3 = plt.subplot(2, 2, 3)
    if len(agent_skills_history) > 0:
        alice_skills = [skills[0] for skills in agent_skills_history]
        bob_skills = [skills[1] for skills in agent_skills_history]
        
        x = np.arange(len(alice_skills))
        width = 0.35
        
        ax3.bar(x - width/2, alice_skills, width, label='Alice', color='darkred', alpha=0.7)
        ax3.bar(x + width/2, bob_skills, width, label='Bob', color='darkorange', alpha=0.7)
        
        ax3.set_xlabel('Skill Segment')
        ax3.set_ylabel('Individual Skill ID')
        ax3.set_title('Individual Agent Skills Over Time')
        ax3.set_xticks(x)
        ax3.legend()
    
    # Skill analysis text
    ax4 = plt.subplot(2, 2, 4)
    ax4.axis('off')
    
    # Create skill analysis text
    analysis_text = f"Episode {episode} Skill Analysis:\n\n"
    analysis_text += f"Total Segments: {len(team_skills)}\n"
    analysis_text += f"Skill Duration: {k} steps\n\n"
    
    analysis_text += "Team Skills by Segment:\n"
    for i, team_skill in enumerate(team_skills):
        if i < len(agent_skills_history):
            alice_skill = agent_skills_history[i][0]
            bob_skill = agent_skills_history[i][1]
            analysis_text += f"  Seg {i}: Team={team_skill}, Alice={alice_skill}, Bob={bob_skill}\n"
    
    analysis_text += "\nEnvironment Setup:\n"
    analysis_text += f"Blue Button: ({button_pos[0][0]:.1f}, {button_pos[0][1]:.1f})\n"
    analysis_text += f"Red Button: ({button_pos[1][0]:.1f}, {button_pos[1][1]:.1f})\n"
    analysis_text += f"Red Diamond: ({diamond_pos[0][0]:.1f}, {diamond_pos[0][1]:.1f})\n"
    analysis_text += f"Blue Diamond: ({diamond_pos[1][0]:.1f}, {diamond_pos[1][1]:.1f})\n"
    
    ax4.text(0.05, 0.95, analysis_text, transform=ax4.transAxes, 
            verticalalignment='top', fontfamily='monospace', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
    
    plt.tight_layout()
    
    # Save the detailed analysis plot
    save_path = os.path.join(log_dir, f"detailed_analysis_episode_{episode}.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    return save_path

def evaluate_agent(model_path, num_episodes=10, render=False):
    """Evaluate a trained agent and generate detailed trajectory analysis."""
    
    # Initialize configuration
    config = Config()
    
    # Setup logging
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_dir = f"evaluation/alice_bob_eval_{timestamp}"
    os.makedirs(log_dir, exist_ok=True)
    init_multiproc_logging(log_dir)
    
    main_logger.info(f"Starting evaluation with {num_episodes} episodes")
    main_logger.info(f"Results will be saved to: {log_dir}")
    
    # Create environment
    def env_creator():
        return ParallelToArrayAdapter(ContinuousAliceBobEnv(render_mode="human" if render else None))
    
    env = env_creator()
    
    # Update config with environment dimensions
    config.update_env_dims(
        state_dim=env.state_dim,
        obs_dim=env.obs_dim,
        n_agents=env.n_uavs
    )
    
    # Initialize agent
    agent = HMASDAgent(config, log_dir=log_dir)
    
    # Load trained model if provided
    if model_path and os.path.exists(model_path):
        main_logger.info(f"Loading model from {model_path}")
        agent.load_models(model_path)
    else:
        main_logger.warning("No model path provided or model not found. Using randomly initialized agent.")
    
    # Evaluation loop
    episode_rewards = []
    all_trajectory_data = []
    
    for episode in range(num_episodes):
        obs_array, info = env.reset()
        state = info['state']
        obs = {agent_name: obs_array[i] for i, agent_name in enumerate(env.agents)}
        
        episode_reward = 0
        trajectories = [[], []]
        episode_team_skills = []
        episode_agent_skills = []
        rewards_history = []
        step = 0
        
        main_logger.info(f"Starting evaluation episode {episode + 1}/{num_episodes}")
        
        while step < config.episode_length:
            # Record positions
            trajectories[0].append(env.env.agent_pos[0].copy())
            trajectories[1].append(env.env.agent_pos[1].copy())
            
            # Assign skills at the start of each skill cycle
            if step % config.k == 0:
                team_skill, agent_skills, log_probs = agent.assign_skills(state, list(obs.values()))
                episode_team_skills.append(team_skill)
                episode_agent_skills.append(agent_skills.copy())
            
            # Select actions
            actions_np, _, _ = agent.select_action(np.array(list(obs.values())), agent_skills, state=state)
            
            # Step environment
            next_obs_array, reward, terminated, truncated, info = env.step(actions_np)
            next_state = info['next_state']
            next_obs = {agent_name: next_obs_array[i] for i, agent_name in enumerate(env.agents)}
            
            episode_reward += reward
            rewards_history.append(reward)
            
            # Check for episode termination
            terminations = info['terminations_dict']
            truncations = info['truncations_dict']
            if any(terminations.values()) or any(truncations.values()):
                main_logger.info(f"Episode {episode} terminated at step {step}")
                break
            
            state = next_state
            obs = next_obs
            step += 1
        
        episode_rewards.append(episode_reward)
        
        # Save detailed trajectory data
        json_path = save_trajectory_data(
            log_dir, episode, trajectories, episode_team_skills, episode_agent_skills,
            env.env.button_pos, env.env.diamond_pos, env.env.button_colors, env.env.diamond_colors,
            rewards_history, episode_reward, config.k
        )
        
        # Create detailed analysis plot
        plot_path = plot_detailed_trajectory_analysis(
            log_dir, episode, trajectories, episode_team_skills, episode_agent_skills,
            env.env.button_pos, env.env.diamond_pos, env.env.button_colors, env.env.diamond_colors, config.k
        )
        
        main_logger.info(f"Episode {episode}: Reward={episode_reward:.2f}, "
                        f"Steps={len(trajectories[0])}, Skills={len(episode_team_skills)}")
        main_logger.info(f"Saved data: {json_path}")
        main_logger.info(f"Saved plot: {plot_path}")
    
    # Summary statistics
    avg_reward = np.mean(episode_rewards)
    std_reward = np.std(episode_rewards)
    
    summary = {
        'num_episodes': num_episodes,
        'average_reward': float(avg_reward),
        'std_reward': float(std_reward),
        'min_reward': float(np.min(episode_rewards)),
        'max_reward': float(np.max(episode_rewards)),
        'episode_rewards': [float(r) for r in episode_rewards]
    }
    
    # Save summary
    summary_path = os.path.join(log_dir, 'evaluation_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    main_logger.info(f"Evaluation completed!")
    main_logger.info(f"Average reward: {avg_reward:.2f} ± {std_reward:.2f}")
    main_logger.info(f"Results saved to: {log_dir}")
    
    env.close()
    return log_dir, summary

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate Continuous Alice and Bob Agent')
    parser.add_argument('--model_path', type=str, default=None,
                       help='Path to trained model directory')
    parser.add_argument('--num_episodes', type=int, default=10,
                       help='Number of episodes to evaluate')
    parser.add_argument('--render', action='store_true',
                       help='Render the environment during evaluation')
    
    args = parser.parse_args()
    
    evaluate_agent(args.model_path, args.num_episodes, args.render)
