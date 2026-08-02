import torch
import numpy as np
import time
import os
from collections import deque
import matplotlib.pyplot as plt
from torch.utils.tensorboard import SummaryWriter
from envs.pettingzoo.continuous_alice_bob import ContinuousAliceBobEnv
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from hmasd.agent import HMASDAgent
from config_continuous_alice_bob import Config
from hmasd.logging import init_multiproc_logging, main_logger

def plot_trajectories_with_skills(log_dir, episode, trajectories, button_pos, diamond_pos, 
                                 button_colors, diamond_colors, team_skills, agent_skills_history, k, 
                                 diamond_collected=None):
    """Plots and saves the agent trajectories with skill annotations for an episode."""
    # Create figure with more space for legends
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 8)
    
    # Calculate task completion statistics
    total_diamonds = len(diamond_pos) if diamond_pos is not None else 0
    collected_diamonds = sum(diamond_collected) if diamond_collected is not None else 0
    completion_rate = (collected_diamonds / total_diamonds * 100) if total_diamonds > 0 else 0
    
    # Enhanced title with task completion info
    ax.set_title(f"Episode {episode} Trajectories with Skills\n"
                f"Task Completion: {collected_diamonds}/{total_diamonds} Diamonds Collected ({completion_rate:.1f}%)")
    ax.set_aspect('equal')
    
    # Color mapping for items: 0=blue, 1=red
    color_map = {0: 'blue', 1: 'red'}
    
    # Plot buttons with correct colors (avoid duplicate labels)
    button_labels_added = set()
    for i, pos in enumerate(button_pos):
        color = color_map[button_colors[i]]
        button_type = "Blue" if button_colors[i]==0 else "Red"
        label = f'{button_type} Button' if button_type not in button_labels_added else ""
        if label:
            button_labels_added.add(button_type)
        ax.scatter(pos[0], pos[1], c=color, marker='s', s=150, label=label)
    
    # Plot diamonds with correct colors and collection status (avoid duplicate labels)
    diamond_labels_added = set()
    for i, pos in enumerate(diamond_pos):
        color = color_map[diamond_colors[i]]
        diamond_name = "Blue" if diamond_colors[i]==0 else "Red"
        
        if diamond_collected is not None and diamond_collected[i]:
            # Show collected diamonds as faded with an 'X' overlay
            label_key = f'{diamond_name}_collected'
            label = f'{diamond_name} Diamond (Collected)' if label_key not in diamond_labels_added else ""
            if label:
                diamond_labels_added.add(label_key)
            ax.scatter(pos[0], pos[1], c=color, marker='D', s=150, alpha=0.3, label=label)
            # Add 'X' mark to show it's collected
            ax.scatter(pos[0], pos[1], c='black', marker='x', s=100, linewidth=3)
        else:
            # Show uncollected diamonds normally
            label_key = f'{diamond_name}_uncollected'
            label = f'{diamond_name} Diamond' if label_key not in diamond_labels_added else ""
            if label:
                diamond_labels_added.add(label_key)
            ax.scatter(pos[0], pos[1], c=color, marker='D', s=150, label=label)

    # Collect all unique skills used by each agent
    all_agent_skills = {0: set(), 1: set()}  # Alice: 0, Bob: 1
    for skill_segment in agent_skills_history:
        for agent_idx, skill in enumerate(skill_segment):
            all_agent_skills[agent_idx].add(skill)

    # Plot trajectories with skill segments
    agent_colors = ['darkred', 'darkorange']
    agent_labels = ['Alice', 'Bob']
    skill_styles = ['-', '--', '-.', ':']
    
    # Track which skill labels have been added to avoid duplicates
    skill_labels_added = set()
    
    for agent_idx, traj in enumerate(trajectories):
        if len(traj) == 0:
            continue
            
        traj_np = np.array(traj)
        
        # Plot full trajectory as thin line
        ax.plot(traj_np[:, 0], traj_np[:, 1], color=agent_colors[agent_idx], 
               alpha=0.3, linewidth=1, label=f'{agent_labels[agent_idx]} Path')
        
        # Plot skill segments with different line styles
        for skill_idx in range(len(agent_skills_history)):
            start_step = skill_idx * k
            end_step = min((skill_idx + 1) * k, len(traj))
            
            if start_step >= len(traj):
                break
                
            segment = traj_np[start_step:end_step]
            if len(segment) > 1:
                agent_skill = agent_skills_history[skill_idx][agent_idx]
                style = skill_styles[agent_skill % len(skill_styles)]
                
                # Create unique label for this agent-skill combination
                skill_label_key = f'{agent_labels[agent_idx]}_Skill_{agent_skill}'
                label = f'{agent_labels[agent_idx]} Skill {agent_skill}' if skill_label_key not in skill_labels_added else ""
                if label:
                    skill_labels_added.add(skill_label_key)
                
                ax.plot(segment[:, 0], segment[:, 1], 
                       color=agent_colors[agent_idx], linestyle=style, linewidth=2, label=label)
        
        # Mark start and end points
        ax.scatter(traj_np[0, 0], traj_np[0, 1], color=agent_colors[agent_idx], 
                  marker='o', s=100, edgecolor='black', linewidth=2, 
                  label=f'{agent_labels[agent_idx]} Start' if agent_idx == 0 else "")
        ax.scatter(traj_np[-1, 0], traj_np[-1, 1], color=agent_colors[agent_idx], 
                  marker='x', s=100, linewidth=3,
                  label=f'{agent_labels[agent_idx]} End' if agent_idx == 0 else "")

    # Create a more compact team skills legend positioned to avoid overlap
    skill_legend_text = "Team Skills by Segment:\n"
    for i, team_skill in enumerate(team_skills):
        skill_legend_text += f"Seg {i}: Team Skill {team_skill}\n"
    
    # Position the text box in upper right area of the plot, but within the axes
    ax.text(0.98, 0.98, skill_legend_text, transform=ax.transAxes, 
           verticalalignment='top', horizontalalignment='right',
           bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    # Add explanation text about task completion
    explanation_text = ("Task: Collect diamonds by pressing matching color buttons\n"
                       "✓ = Collected diamond, ○ = Start point, × = End point")
    ax.text(0.02, 0.98, explanation_text, transform=ax.transAxes, 
           verticalalignment='top', horizontalalignment='left',
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    # Position main legend outside the plot area
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # Save figure with tight layout
    save_path = os.path.join(log_dir, f"trajectory_skills_episode_{episode}.png")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)

def plot_trajectories(log_dir, episode, trajectories, button_pos, diamond_pos):
    """Plots and saves the agent trajectories for an episode (legacy function)."""
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 8)
    ax.set_title(f"Episode {episode} Trajectories")
    ax.set_aspect('equal')
    
    # Plot items
    ax.scatter(button_pos[:, 0], button_pos[:, 1], c='gray', marker='s', s=100, label='Buttons')
    ax.scatter(diamond_pos[:, 0], diamond_pos[:, 1], c='blue', marker='D', s=100, label='Diamonds')

    # Plot trajectories
    colors = ['red', 'orange']
    labels = ['Alice', 'Bob']
    for i, traj in enumerate(trajectories):
        traj_np = np.array(traj)
        ax.plot(traj_np[:, 0], traj_np[:, 1], color=colors[i], label=labels[i])
        ax.scatter(traj_np[0, 0], traj_np[0, 1], color=colors[i], marker='o', s=50) # Start point
        ax.scatter(traj_np[-1, 0], traj_np[-1, 1], color=colors[i], marker='x', s=50) # End point

    ax.legend()
    ax.grid(True)
    
    # Save figure
    save_path = os.path.join(log_dir, f"trajectory_episode_{episode}.png")
    plt.savefig(save_path)
    plt.close(fig)

def main():
    # Initialize configuration
    config = Config()

    # Setup logging
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_dir = f"logs/alice_bob_{timestamp}"
    init_multiproc_logging(log_dir)
    writer = SummaryWriter(log_dir)
    main_logger.info("Starting Continuous Alice and Bob Litmus Test")

    # Create and wrap the environment
    def env_creator():
        return ParallelToArrayAdapter(ContinuousAliceBobEnv())

    # For simplicity, we use a single environment for this test
    # In a real scenario, you would use a vectorized environment
    env = env_creator()

    # Update config with environment dimensions
    config.update_env_dims(
        state_dim=env.state_dim,
        obs_dim=env.obs_dim,
        n_agents=env.n_uavs
    )
    main_logger.info(f"Env dimensions: state={config.state_dim}, obs={config.obs_dim}, n_agents={config.n_agents}")

    # Initialize agent
    agent = HMASDAgent(config, log_dir=log_dir)

    # Training loop
    main_logger.info("Starting training loop...")
    global_step = 0
    episode_rewards = deque(maxlen=100)
    rollout_step = 0  # Track rollout steps within buffer
    
    for episode in range(int(config.total_timesteps / config.episode_length)):
        obs_array, info = env.reset()
        state = info['state']
        obs = {agent: obs_array[i] for i, agent in enumerate(env.agents)}
        episode_reward = 0
        done = {agent_name: False for agent_name in env.agents}
        
        trajectories = [[], []] # To store positions for Alice and Bob
        episode_team_skills = []  # Track team skills for this episode
        episode_agent_skills = []  # Track agent skills for this episode

        for step in range(config.episode_length):
            # Record positions for trajectory
            trajectories[0].append(env.env.agent_pos[0].copy())
            trajectories[1].append(env.env.agent_pos[1].copy())
            
            # Assign skills if it's the start of a skill cycle
            if rollout_step % config.k == 0:
                team_skill, agent_skills, log_probs = agent.assign_skills(state, list(obs.values()))
                # Record skills for this episode
                episode_team_skills.append(team_skill)
                episode_agent_skills.append(agent_skills.copy())
            
            # Select actions based on current skills
            actions_np, log_probs_np, values_np = agent.select_action(np.array(list(obs.values())), agent_skills, state=state)
            
            actions_dict = {agent_name: actions_np[i] for i, agent_name in enumerate(env.agents)}

            # Step the environment
            next_obs_array, reward, terminated, truncated, info = env.step(actions_np)
            next_state = info['next_state']
            next_obs = {agent: next_obs_array[i] for i, agent in enumerate(env.agents)}
            rewards = {agent: reward for agent in env.agents}
            terminations = info['terminations_dict']
            truncations = info['truncations_dict']

            # Store transition
            # Note: This is a simplified storage for a single env.
            # The HMASDAgent is designed for parallel envs, so we adapt.
            
            # Create dones dict for agent
            dones = {an: terminations[an] or truncations[an] for an in env.agents}

            # Check buffer bounds before storing
            if rollout_step >= agent.rollout_buffer.num_steps:
                main_logger.warning(f"Rollout step {rollout_step} exceeds buffer size {agent.rollout_buffer.num_steps}, resetting buffer")
                agent.update(rollout_step)
                agent.rollout_buffer.reset()
                rollout_step = 0

            # Store experience with correct rollout step index
            agent.store_transition(
                state=state,
                next_state=next_state,
                observations=np.array(list(obs.values())),
                next_observations=np.array(list(next_obs.values())),
                actions=actions_np,
                rewards=list(rewards.values())[0], # Global reward
                dones=np.array(list(dones.values())),
                team_skill=team_skill,
                agent_skills=agent_skills,
                action_logprobs=log_probs_np,
                log_probs=log_probs,
                skill_timer_for_env=rollout_step % config.k,
                env_id=0, # Single environment
                values=values_np,
                rollout_step_idx=rollout_step  # Use rollout_step instead of step
            )

            state = next_state
            obs = next_obs
            episode_reward += list(rewards.values())[0]
            global_step += 1
            rollout_step += 1  # Increment rollout step counter

            # Update networks if buffer is full
            if rollout_step >= agent.rollout_buffer.num_steps:
                main_logger.info(f"Rollout buffer full at global step {global_step}. Computing GAE and updating networks...")
                
                # **关键修复**: 计算最后一步的价值估计用于GAE
                last_values = np.zeros((1, config.n_agents))  # Single environment
                if not any(dones.values()):
                    # 如果没有终止，计算下一状态的价值
                    
                    # **CRITICAL FIX #1**: 确定在 next_state 将使用什么技能
                    # 因为 rollout_step == num_steps, 下一步的 rollout_step 将是 0, 这是一个技能更换点。
                    # 因此，我们必须为 next_state 分配新技能。
                    next_team_skill, next_agent_skills, _ = agent.assign_skills(
                        next_state, np.array(list(next_obs.values()))
                    )

                    # 使用这些"新"技能来计算正确的自举价值
                    _, _, last_values_np = agent.select_action(
                        np.array(list(next_obs.values())),
                        next_agent_skills,  # <--- 使用正确的、未来的技能
                        state=next_state
                    )
                    last_values[0] = last_values_np
                
                # **CRITICAL FIX #2**: 传递每个智能体的终止状态
                final_dones_per_agent = np.array(list(dones.values())).reshape(1, -1)  # Shape: (1, n_agents)
                
                # **关键修复**: 计算GAE advantages
                agent.rollout_buffer.compute_advantages(
                    last_values=last_values,
                    dones=final_dones_per_agent,  # <--- 使用每个智能体的终止标志
                    gamma=config.gamma,
                    gae_lambda=config.gae_lambda
                )
                
                # 更新网络
                agent.update(rollout_step)
                agent.rollout_buffer.reset()
                rollout_step = 0  # Reset rollout step counter

            if any(dones.values()):
                # If episode ends early, still update if we have data
                if rollout_step > 0:
                    main_logger.info(f"Episode ended early at rollout step {rollout_step}. Computing GAE and updating networks...")
                    
                    # **关键修复**: 终止时的价值估计为0
                    last_values = np.zeros((1, config.n_agents))
                    
                    # **CRITICAL FIX #2**: 传递每个智能体的终止状态
                    final_dones_per_agent = np.array(list(dones.values())).reshape(1, -1)  # Shape: (1, n_agents)
                    
                    # **关键修复**: 计算GAE advantages
                    agent.rollout_buffer.compute_advantages(
                        last_values=last_values,
                        dones=final_dones_per_agent,  # <--- 使用每个智能体的终止标志
                        gamma=config.gamma,
                        gae_lambda=config.gae_lambda
                    )
                    
                    agent.update(rollout_step)
                    agent.rollout_buffer.reset()
                    rollout_step = 0
                break
        
        episode_rewards.append(episode_reward)
        avg_reward = np.mean(episode_rewards)
        
        writer.add_scalar("charts/avg_episode_reward", avg_reward, global_step)
        writer.add_scalar("charts/episode_reward", episode_reward, global_step)
        main_logger.info(f"Episode {episode}: Total Reward: {episode_reward:.2f}, Avg Reward (last 100): {avg_reward:.2f}")

        # Plot trajectories every 100 episodes
        if episode % 100 == 0:
            # Use enhanced plotting with skill annotations
            if len(episode_team_skills) > 0 and len(episode_agent_skills) > 0:
                plot_trajectories_with_skills(
                    log_dir=log_dir,
                    episode=episode,
                    trajectories=trajectories,
                    button_pos=env.env.button_pos,
                    diamond_pos=env.env.diamond_pos,
                    button_colors=env.env.button_colors,
                    diamond_colors=env.env.diamond_colors,
                    team_skills=episode_team_skills,
                    agent_skills_history=episode_agent_skills,
                    k=config.k,
                    diamond_collected=env.env.diamond_collected
                )
                main_logger.info(f"Saved enhanced trajectory plot with skills for episode {episode} to {log_dir}")
            else:
                # Fallback to basic plotting if no skills recorded
                plot_trajectories(log_dir, episode, trajectories, env.env.button_pos, env.env.diamond_pos)
                main_logger.info(f"Saved basic trajectory plot for episode {episode} to {log_dir}")

    writer.close()
    env.close()
    main_logger.info("Training finished.")

if __name__ == "__main__":
    main()
