import torch
import numpy as np
import matplotlib.pyplot as plt
from config_continuous_alice_bob import Config
from hmasd.agent import HMASDAgent
from envs.pettingzoo.continuous_alice_bob import ContinuousAliceBobEnv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def diagnose_hmasd_learning():
    """Comprehensive diagnosis of HMASD learning issues"""
    
    # Initialize config and environment
    config = Config()
    env = ContinuousAliceBobEnv()
    
    # Set environment dimensions
    config.state_dim = env.get_state_dim()
    config.obs_dim = env.get_obs_dim()
    config.action_dim = env.action_space('alice').shape[0]
    
    # Initialize agent
    agent = HMASDAgent(config, debug=True)
    
    print("=== HMASD Learning Diagnosis ===\n")
    
    # 1. Test discriminator initialization and outputs
    print("1. Testing Discriminator Initialization:")
    test_discriminators(agent, env)
    
    # 2. Test intrinsic reward computation
    print("\n2. Testing Intrinsic Reward Computation:")
    test_intrinsic_rewards(agent, env, config)
    
    # 3. Test skill assignment
    print("\n3. Testing Skill Assignment:")
    test_skill_assignment(agent, env)
    
    # 4. Test value function learning
    print("\n4. Testing Value Function Learning:")
    test_value_functions(agent, env)
    
    # 5. Test policy gradients
    print("\n5. Testing Policy Gradients:")
    test_policy_gradients(agent, env, config)

def test_discriminators(agent, env):
    """Test discriminator networks"""
    # Reset environment and get initial state
    observations, _ = env.reset()
    state = env._get_state()
    
    # Test team discriminator
    state_tensor = torch.FloatTensor(state).unsqueeze(0).to(agent.device)
    team_logits = agent.team_discriminator(state_tensor)
    team_probs = torch.softmax(team_logits, dim=-1)
    
    print(f"Team Discriminator Output Shape: {team_logits.shape}")
    print(f"Team Discriminator Logits: {team_logits.squeeze().detach().cpu().numpy()}")
    print(f"Team Discriminator Probs: {team_probs.squeeze().detach().cpu().numpy()}")
    print(f"Team Discriminator Entropy: {-(team_probs * torch.log(team_probs + 1e-8)).sum().item():.4f}")
    
    # Test individual discriminator
    obs_alice = torch.FloatTensor(observations['alice']).unsqueeze(0).to(agent.device)
    team_skill = torch.tensor(0, device=agent.device)  # Use team skill 0
    ind_logits = agent.individual_discriminator(obs_alice, team_skill)
    ind_probs = torch.softmax(ind_logits, dim=-1)
    
    print(f"\nIndividual Discriminator Output Shape: {ind_logits.shape}")
    print(f"Individual Discriminator Logits: {ind_logits.squeeze().detach().cpu().numpy()}")
    print(f"Individual Discriminator Probs: {ind_probs.squeeze().detach().cpu().numpy()}")
    print(f"Individual Discriminator Entropy: {-(ind_probs * torch.log(ind_probs + 1e-8)).sum().item():.4f}")

def test_intrinsic_rewards(agent, env, config):
    """Test intrinsic reward computation"""
    # Reset environment
    observations, _ = env.reset()
    state = env._get_state()
    
    # Take a random action
    actions = {
        'alice': env.action_space('alice').sample(),
        'bob': env.action_space('bob').sample()
    }
    
    next_observations, rewards, terminations, truncations, infos = env.step(actions)
    next_state = env._get_state()
    
    # Test intrinsic reward computation for different skill combinations
    print("Testing intrinsic rewards for different skill combinations:")
    
    for team_skill in range(config.n_Z):
        for agent_skill in range(config.n_z):
            intrinsic_reward, env_comp, team_disc_comp, ind_disc_comp = agent._compute_intrinsic_reward(
                next_state, rewards['alice'], next_observations['alice'], team_skill, agent_skill
            )
            
            print(f"Team Skill {team_skill}, Agent Skill {agent_skill}:")
            print(f"  Total Intrinsic: {intrinsic_reward:.6f}")
            print(f"  Env Component: {env_comp:.6f}")
            print(f"  Team Disc Component: {team_disc_comp:.6f}")
            print(f"  Ind Disc Component: {ind_disc_comp:.6f}")
            
            # Check for problematic values
            if abs(intrinsic_reward) > 100:
                print(f"  WARNING: Very large intrinsic reward!")
            if abs(team_disc_comp) < 1e-6 and abs(ind_disc_comp) < 1e-6:
                print(f"  WARNING: Discriminator components are near zero!")

def test_skill_assignment(agent, env):
    """Test skill assignment mechanism"""
    observations, _ = env.reset()
    state = env._get_state()
    
    print("Testing skill assignment consistency:")
    
    # Test multiple skill assignments with same input
    assignments = []
    for i in range(10):
        team_skill, agent_skills, log_probs = agent.assign_skills(
            state, [observations['alice'], observations['bob']], deterministic=False
        )
        assignments.append((team_skill, tuple(agent_skills)))
        print(f"Assignment {i}: Team={team_skill}, Agents={agent_skills}")
    
    # Check diversity
    unique_assignments = set(assignments)
    print(f"\nUnique assignments out of 10: {len(unique_assignments)}")
    
    if len(unique_assignments) == 1:
        print("WARNING: No diversity in skill assignments!")
    elif len(unique_assignments) == 10:
        print("WARNING: Too much randomness, no learning convergence!")
    
    # Test deterministic assignment
    team_skill_det, agent_skills_det, _ = agent.assign_skills(
        state, [observations['alice'], observations['bob']], deterministic=True
    )
    print(f"Deterministic assignment: Team={team_skill_det}, Agents={agent_skills_det}")

def test_value_functions(agent, env):
    """Test value function outputs"""
    observations, _ = env.reset()
    state = env._get_state()
    
    # Test coordinator value function
    state_tensor = torch.FloatTensor(state).unsqueeze(0).to(agent.device)
    obs_tensor = torch.FloatTensor([observations['alice'], observations['bob']]).unsqueeze(0).to(agent.device)
    
    with torch.no_grad():
        state_val, agent_vals, _ = agent.skill_coordinator.get_value(state_tensor, obs_tensor)
        
    print(f"Coordinator State Value: {state_val.item():.6f}")
    if agent_vals:
        for i, val in enumerate(agent_vals):
            print(f"Coordinator Agent {i} Value: {val.item():.6f}")
    
    # Test discoverer value function
    team_skill_tensor = torch.tensor(0, device=agent.device).unsqueeze(0)
    with torch.no_grad():
        global_val, _ = agent.skill_discoverer.get_value(state_tensor, team_skill_tensor)
        
    print(f"Discoverer Global Value: {global_val.item():.6f}")
    
    # Check if values are reasonable
    if abs(state_val.item()) > 100:
        print("WARNING: Very large coordinator state value!")
    if abs(global_val.item()) > 100:
        print("WARNING: Very large discoverer value!")

def test_policy_gradients(agent, env, config):
    """Test if policy gradients are flowing properly"""
    observations, _ = env.reset()
    state = env._get_state()
    
    # Get initial parameters
    coord_params_before = [p.clone() for p in agent.skill_coordinator.parameters()]
    disc_params_before = [p.clone() for p in agent.skill_discoverer.parameters()]
    
    # Simulate a small training step
    print("Simulating training step...")
    
    # Create dummy data
    batch_size = 32
    dummy_states = torch.randn(batch_size, config.state_dim).to(agent.device)
    dummy_obs = torch.randn(batch_size, config.n_agents, config.obs_dim).to(agent.device)
    dummy_advantages = torch.randn(batch_size).to(agent.device)
    dummy_returns = torch.randn(batch_size).to(agent.device)
    
    # Test coordinator gradient flow
    agent.coordinator_optimizer.zero_grad()
    
    # Forward pass
    team_skills, agent_skills, Z_logits, z_logits, _, _ = agent.skill_coordinator(dummy_states, dummy_obs)
    state_vals, agent_vals, _ = agent.skill_coordinator.get_value(dummy_states, dummy_obs)
    
    # Compute simple loss
    policy_loss = -torch.mean(dummy_advantages)
    value_loss = torch.mean((state_vals.squeeze() - dummy_returns) ** 2)
    total_loss = policy_loss + value_loss
    
    total_loss.backward()
    
    # Check gradients
    coord_grad_norm = torch.nn.utils.clip_grad_norm_(agent.skill_coordinator.parameters(), float('inf'))
    print(f"Coordinator gradient norm: {coord_grad_norm:.6f}")
    
    if coord_grad_norm < 1e-8:
        print("WARNING: Very small coordinator gradients!")
    elif coord_grad_norm > 100:
        print("WARNING: Very large coordinator gradients!")
    
    agent.coordinator_optimizer.step()
    
    # Check parameter updates
    coord_param_changes = []
    for p_before, p_after in zip(coord_params_before, agent.skill_coordinator.parameters()):
        change = torch.norm(p_after - p_before).item()
        coord_param_changes.append(change)
    
    avg_coord_change = np.mean(coord_param_changes)
    print(f"Average coordinator parameter change: {avg_coord_change:.8f}")
    
    if avg_coord_change < 1e-10:
        print("WARNING: Parameters not updating!")

if __name__ == "__main__":
    diagnose_hmasd_learning()
