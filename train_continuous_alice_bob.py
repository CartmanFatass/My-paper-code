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
from logger import init_multiproc_logging, main_logger

def plot_trajectories(log_dir, episode, trajectories, button_pos, diamond_pos):
    """Plots and saves the agent trajectories for an episode."""
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

        for step in range(config.episode_length):
            # Record positions for trajectory
            trajectories[0].append(env.env.agent_pos[0].copy())
            trajectories[1].append(env.env.agent_pos[1].copy())
            # Assign skills if it's the start of a skill cycle
            if rollout_step % config.k == 0:
                team_skill, agent_skills, log_probs = agent.assign_skills(state, list(obs.values()))
            
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
                    last_actions_np, last_log_probs_np, last_values_np = agent.select_action(
                        np.array(list(next_obs.values())), agent_skills, state=next_state
                    )
                    last_values[0] = last_values_np
                
                # **关键修复**: 计算GAE advantages
                agent.rollout_buffer.compute_advantages(
                    last_values=last_values,
                    dones=np.array([any(dones.values())]),  # Single environment done flag
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
                    
                    # **关键修复**: 计算GAE advantages
                    agent.rollout_buffer.compute_advantages(
                        last_values=last_values,
                        dones=np.array([True]),  # Episode terminated
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

        # Plot trajectories every 20 episodes
        if episode % 20 == 0:
            plot_trajectories(log_dir, episode, trajectories, env.env.button_pos, env.env.diamond_pos)
            main_logger.info(f"Saved trajectory plot for episode {episode} to {log_dir}")

    writer.close()
    env.close()
    main_logger.info("Training finished.")

if __name__ == "__main__":
    main()
